"""SQLite persistence and account management for the YouTube summarizer."""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / "data" / "summarizer.sqlite3"
DATABASE_PATH = Path(os.environ.get("SUMMARIZER_DB_PATH", str(DEFAULT_DATABASE_PATH)))
PASSWORD_ITERATIONS = 600_000
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DATABASE_PATH), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hash_password(password: str, salt: Optional[bytes] = None) -> tuple:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return salt.hex(), digest.hex()


def _validate_credentials(username: str, password: str) -> str:
    username = username.strip().lower()
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username must be 3–32 characters: letters, numbers, dots, dashes, or underscores.")
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters long.")
    if len(password) > 1024:
        raise ValueError("Password is too long.")
    return username


def _setting(name: str) -> str:
    """Read a setting from the process environment or Streamlit secrets."""
    value = os.environ.get(name, "")
    if value:
        return value
    try:
        import streamlit as streamlit_app
        return str(streamlit_app.secrets.get(name, ""))
    except Exception:
        # Streamlit secrets are unavailable during CLI use and local runs
        # without a secrets.toml file.
        return ""


def initialize_database() -> Optional[str]:
    """Create the schema and seed an admin once when environment values are set."""
    with _connection() as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                video_url TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS reports_user_created ON reports(user_id, created_at DESC)"
        )

        admin_username = _setting("SUMMARIZER_ADMIN_USERNAME").strip()
        admin_password = _setting("SUMMARIZER_ADMIN_PASSWORD")
        admin_exists = connection.execute(
            "SELECT 1 FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()
        if admin_exists:
            return None
        if not admin_username and not admin_password:
            return "No admin account exists yet. Set SUMMARIZER_ADMIN_USERNAME and SUMMARIZER_ADMIN_PASSWORD, then restart the app to create one."
        if not admin_username or not admin_password:
            return "To create the first admin, set both SUMMARIZER_ADMIN_USERNAME and SUMMARIZER_ADMIN_PASSWORD."
        try:
            normalized = _validate_credentials(admin_username, admin_password)
        except ValueError as exc:
            return "Admin setup was skipped: " + str(exc)

        existing = connection.execute(
            "SELECT 1 FROM users WHERE username = ?", (normalized,)
        ).fetchone()
        if existing:
            return "Admin setup could not use that username because it already belongs to a regular account. Set a different SUMMARIZER_ADMIN_USERNAME and restart."

        salt, digest = _hash_password(admin_password)
        connection.execute(
            "INSERT INTO users (username, password_salt, password_hash, role, created_at) VALUES (?, ?, ?, 'admin', ?)",
            (normalized, salt, digest, _now()),
        )
    return None


def create_user(username: str, password: str) -> Dict[str, Any]:
    normalized = _validate_credentials(username, password)
    salt, digest = _hash_password(password)
    try:
        with _connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users (username, password_salt, password_hash, role, created_at) VALUES (?, ?, ?, 'user', ?)",
                (normalized, salt, digest, _now()),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError("That username is already in use.") from exc
    return get_user_by_id(user_id)


def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
    normalized = (username or "").strip().lower()
    with _connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE username = ?", (normalized,)
        ).fetchone()
    if not row or not row["is_active"]:
        return None
    try:
        salt = bytes.fromhex(row["password_salt"])
    except ValueError:
        return None
    _, candidate = _hash_password(password or "", salt)
    if not hmac.compare_digest(candidate, row["password_hash"]):
        return None
    return dict(row)


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with _connection() as connection:
        row = connection.execute(
            "SELECT id, username, role, is_active, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def save_report(user_id: int, report: Any) -> int:
    with _connection() as connection:
        user = connection.execute(
            "SELECT is_active FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not user or not user["is_active"]:
            raise PermissionError("This account is not active.")
        cursor = connection.execute(
            "INSERT INTO reports (user_id, video_url, title, summary, report_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                user_id,
                report.url,
                report.title,
                report.summary,
                report.to_json(),
                _now(),
            ),
        )
        return int(cursor.lastrowid)


def list_user_reports(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    with _connection() as connection:
        rows = connection.execute(
            "SELECT id, video_url, title, summary, created_at FROM reports WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
            (user_id, max(1, min(limit, 500))),
        ).fetchall()
    return [dict(row) for row in rows]


def get_user_report(report_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    with _connection() as connection:
        row = connection.execute(
            "SELECT id, video_url, title, summary, report_json, created_at FROM reports WHERE id = ? AND user_id = ?",
            (report_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def admin_overview() -> Dict[str, Any]:
    with _connection() as connection:
        counts = connection.execute(
            "SELECT COUNT(*) AS total_users, SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active_users, SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) AS admins FROM users"
        ).fetchone()
        report_count = connection.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        users = connection.execute(
            """SELECT users.id, users.username, users.role, users.is_active, users.created_at,
                      COUNT(reports.id) AS report_count
               FROM users LEFT JOIN reports ON reports.user_id = users.id
               GROUP BY users.id ORDER BY users.created_at DESC"""
        ).fetchall()
        recent_reports = connection.execute(
            """SELECT reports.id, reports.title, reports.video_url, reports.created_at,
                      users.username
               FROM reports JOIN users ON users.id = reports.user_id
               ORDER BY reports.created_at DESC, reports.id DESC LIMIT 30"""
        ).fetchall()
    return {
        "total_users": counts["total_users"] or 0,
        "active_users": counts["active_users"] or 0,
        "admins": counts["admins"] or 0,
        "total_reports": report_count,
        "users": [dict(row) for row in users],
        "recent_reports": [dict(row) for row in recent_reports],
    }


def set_user_active(user_id: int, is_active: bool, actor_id: int) -> None:
    with _connection() as connection:
        actor = connection.execute(
            "SELECT role, is_active FROM users WHERE id = ?", (actor_id,)
        ).fetchone()
        target = connection.execute(
            "SELECT role, is_active FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not actor or actor["role"] != "admin" or not actor["is_active"]:
            raise PermissionError("An active admin account is required.")
        if not target:
            raise ValueError("Account not found.")
        if not is_active and user_id == actor_id:
            raise ValueError("You cannot deactivate your own account.")
        if not is_active and target["role"] == "admin" and target["is_active"]:
            active_admins = connection.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1"
            ).fetchone()[0]
            if active_admins <= 1:
                raise ValueError("The last active admin account cannot be deactivated.")
        connection.execute(
            "UPDATE users SET is_active = ? WHERE id = ?", (int(is_active), user_id)
        )
