# YouTube Video Summarizer

A Python app that turns a YouTube video's available English captions into an extractive summary, keywords, reading statistics, optional sentiment scores, and quiz questions. Use the Streamlit web app to manage saved reports, or use the command-line interface for one-off summaries and batch jobs.

The app does not execute generated code or download the video itself. It analyzes captions returned by `yt-dlp`; it does not use an LLM. Summaries use Sumy's extractive methods or a built-in frequency-based fallback.

## Features

- Generate summaries with LSA, Luhn, LexRank, or the built-in naive method.
- Extract keywords and calculate readability and text statistics.
- Create fill-in-the-blank and multiple-choice quiz questions.
- Export reports as text, Markdown, or JSON.
- Create a local account and sign in to the Streamlit app.
- Save reports in a personal history; one account cannot open another account's saved reports.
- Use an admin dashboard to review account/report counts and disable or reactivate accounts.
- Store accounts and reports in SQLite. Passwords are stored as salted PBKDF2 hashes, not plain text.

## Run locally

You need Python 3.8 or newer and a video with usable English captions.

```powershell
git clone https://github.com/HariomSThakur/youtube-video-summarizer.git
cd youtube-video-summarizer
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create the first admin account before starting the app. In PowerShell, set a username and a unique password of at least 12 characters:

```powershell
$env:SUMMARIZER_ADMIN_USERNAME = "your_admin_name"
$env:SUMMARIZER_ADMIN_PASSWORD = "use-a-long-unique-password"
streamlit run summarizer.py
```

The app creates the admin account on its first run. It never uses a built-in default password. Keep the password private and do not commit it. These environment variables only seed the first admin; changing them later does not change an existing account's password.

After opening the local address printed by Streamlit, sign in as the admin or create a regular user account. Regular accounts can create summaries and see their own history. Admins also see the Admin page.

On macOS or Linux, create and activate the virtual environment with `python3 -m venv .venv` and `source .venv/bin/activate`, then set the two variables with `export SUMMARIZER_ADMIN_USERNAME=your_admin_name` and `export SUMMARIZER_ADMIN_PASSWORD='use-a-long-unique-password'` before running Streamlit.

## Database and admin settings

By default, the SQLite database is created at `data/summarizer.sqlite3`. The `data/` folder and SQLite files are ignored by Git so account details and saved reports are not uploaded with the source code.

To store the database somewhere else, set `SUMMARIZER_DB_PATH` before starting the app. For example:

```powershell
$env:SUMMARIZER_DB_PATH = "D:\app-data\summarizer.sqlite3"
```

For Streamlit hosting, put `SUMMARIZER_ADMIN_USERNAME` and `SUMMARIZER_ADMIN_PASSWORD` in the host's private secrets/settings rather than in the repository. The app can read Streamlit secrets with those names. SQLite data on a hosted app is only durable if the host provides persistent storage and the database path points to it; otherwise account and report data may disappear when the app's filesystem is replaced.

There is no self-service password reset yet. Back up the SQLite database before moving or replacing it. Deleting the database removes all accounts and report history.

## Use the command line

The CLI does not require an account or use the web app's database.

```powershell
python summarizer.py --input "https://youtu.be/VIDEO_ID" --format markdown --output summary.md
```

Choose `text`, `markdown`, or `json` for `--format`; choose `lsa`, `luhn`, `lexrank`, or `naive` for `--backend`. For a batch, put one video URL per line in a text file and run:

```powershell
python summarizer.py --batch urls.txt --output-dir reports --format json
```

Run `python summarizer.py --help` for all options. Without `--input`, the CLI starts interactive mode.

## Limitations

- A video needs usable English captions. Videos without captions cannot be summarized.
- The first run may download NLTK tokenizer data.
- Subtitle files are cached in the system temporary directory; batch reports go to `reports/`.
- Extractive summaries and automatically generated quiz questions can be imperfect. Review them before relying on them.
- This SQLite login is suitable for a small demo. It does not include email verification, password recovery, or login rate limiting. Use persistent storage when hosting the app if you need to keep user data between deployments.
