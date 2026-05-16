# 🎬 YouTube Video Summarizer

> Turn any YouTube video into a summary, keyword report, readability analysis, and quiz — via CLI or Streamlit web UI.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-ff4b4b?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 📖 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Demo](#-demo)
- [Installation](#-installation)
- [Usage](#-usage)
  - [Streamlit Web UI](#streamlit-web-ui)
  - [CLI — Single Video](#cli--single-video)
  - [CLI — Batch Mode](#cli--batch-mode)
  - [CLI — Interactive Mode](#cli--interactive-mode)
- [Output Formats](#-output-formats)
- [Project Structure](#-project-structure)
- [Dependencies](#-dependencies)
- [Configuration](#-configuration)
- [How It Works](#-how-it-works)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📌 About

**YouTube Video Summarizer** is a Python tool that downloads a video's subtitles (auto-generated or manual) via `yt-dlp`, then runs a full NLP pipeline on the transcript to produce:

- A concise summary (multiple algorithm choices)
- Top keywords with frequency and TF-IDF scores
- Readability and lexical statistics
- Sentiment analysis
- A fill-in-the-blank **and** multiple-choice quiz

It works entirely offline after subtitle download — no OpenAI key, no paid API.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📥 Subtitle download | Auto-generated & manual subtitles via `yt-dlp` |
| ✍️ Summarization | LSA, Luhn, LexRank (Sumy), or built-in naive fallback |
| 📄 Long video support | Map-reduce chunking for lengthy transcripts |
| 🔎 Keyword extraction | Raw frequency + TF-IDF scoring |
| 📊 Text statistics | Word count, sentence count, lexical diversity, avg. word/sentence length |
| 📖 Readability | Flesch Reading Ease & Flesch-Kincaid Grade Level |
| 💬 Sentiment analysis | Polarity & subjectivity scores via TextBlob (optional) |
| 🧠 Quiz generation | Fill-in-the-blank AND multiple-choice questions |
| 🗂️ Batch processing | Process a list of URLs from a `.txt` file |
| 💾 Export formats | Plain text, Markdown, JSON |
| 🌐 Streamlit UI | Tabbed web interface with one-click download |
| 🖥️ CLI | Full-featured command-line interface with flags |
| ⚡ Caching | Skips re-downloading already fetched subtitles |

---

## 🎥 Demo

### Web UI (Streamlit)
```
streamlit run summarizer.py
```
The app opens at `http://localhost:8501`. Paste a YouTube URL, pick your options, and click **Generate Report**.

### CLI
```bash
python summarizer.py --input https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/youtube-summarizer.git
cd youtube-summarizer
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download NLTK data
The script handles this automatically on first run. If you prefer to do it manually:
```python
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
```

---

## 🚀 Usage

### Streamlit Web UI
```bash
streamlit run summarizer.py
```

Opens a browser tab with:
- **Summary** tab — the generated summary
- **Keywords** tab — keyword frequency table
- **Stats & Sentiment** tab — all metrics as JSON
- **Quiz** tab — expandable FITB and MC questions
- **Raw Output** tab — full report + download button

---

### CLI — Single Video

```bash
python summarizer.py --input <YouTube_URL> [OPTIONS]
```

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--input` | `-i` | — | YouTube video URL *(required)* |
| `--output` | `-o` | `summary.txt` | Output file path |
| `--sentences` | `-s` | `8` | Number of sentences in summary |
| `--quiz` | `-q` | `5` | Quiz questions per type |
| `--keywords` | `-k` | `10` | Top N keywords to extract |
| `--backend` | `-b` | `lsa` | Summarizer: `lsa`, `luhn`, `lexrank`, `naive` |
| `--format` | `-f` | `text` | Export format: `text`, `markdown`, `json` |
| `--no-cache` | | off | Disable subtitle caching |
| `--verbose` | | off | Enable debug logging |

**Examples:**
```bash
# Basic usage
python summarizer.py -i https://youtu.be/xyz

# 12-sentence summary using LexRank, saved as Markdown
python summarizer.py -i https://youtu.be/xyz -s 12 -b lexrank -f markdown -o report.md

# Export as JSON, no cache
python summarizer.py -i https://youtu.be/xyz -f json --no-cache
```

---

### CLI — Batch Mode

Create a text file with one URL per line (lines starting with `#` are ignored):

```
# urls.txt
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
# https://www.youtube.com/watch?v=skipped
https://www.youtube.com/watch?v=video3
```

Then run:
```bash
python summarizer.py --batch urls.txt --output-dir ./reports --format markdown
```

Each video gets its own file inside `./reports/`, named after the video title.

---

### CLI — Interactive Mode

Prompts you for all options at runtime — no flags needed:
```bash
python summarizer.py --interactive
```

---

## 📤 Output Formats

### Plain Text (default)
```
============================================================
🎬  VIDEO SUMMARY REPORT
============================================================
Title     : My Video Title
URL       : https://...
Generated : 2025-05-16T14:30:00
============================================================

📘  SUMMARY
------------------------------------------------------------
The video discusses ...

🔎  KEYWORDS (frequency)
------------------------------------------------------------
python (42), machine (31), learning (28) ...

📊  STATISTICS
------------------------------------------------------------
  Sentences: 312
  Words: 4821
  ...

🧠  FILL-IN-THE-BLANK QUIZ
------------------------------------------------------------
Q1. The model was trained on a large _____
   ✅ Answer: dataset
...
```

### Markdown (`--format markdown`)
Produces a fully formatted `.md` file with tables, headings, and blockquotes — ready to paste into a GitHub wiki or Notion.

### JSON (`--format json`)
Structured output with all fields (title, summary, keywords, stats, readability, sentiment, quizzes) as a JSON object — ideal for piping into other tools.

---

## 📁 Project Structure

```
youtube-summarizer/
│
├── summarizer.py          # Main script (all logic + UI + CLI)
├── requirements.txt       # Python dependencies
├── README.md              # This file
│
├── reports/               # Default batch output directory (auto-created)
└── /tmp/yt_summarizer_cache/  # Subtitle cache (system temp dir)
```

> The project is intentionally single-file for portability. All sections are clearly numbered and separated by comments.

---

## 📦 Dependencies

### Required
| Package | Purpose |
|---------|---------|
| `yt-dlp` | Download YouTube subtitles |
| `nltk` | Sentence tokenization |
| `sumy` | LSA, Luhn, LexRank summarizers |

### Optional (gracefully skipped if missing)
| Package | Purpose |
|---------|---------|
| `textblob` | Sentiment analysis |
| `colorama` | Colored CLI output |
| `tqdm` | Progress bars |
| `streamlit` | Web UI |

### Install all at once
```bash
pip install yt-dlp nltk sumy textblob colorama tqdm streamlit
```

Or use the provided file:
```bash
pip install -r requirements.txt
```

**`requirements.txt`:**
```
yt-dlp
nltk
sumy
textblob
colorama
tqdm
streamlit
```

---

## 🔧 Configuration

All tuneable constants live at the top of `summarizer.py`:

```python
DEFAULT_SENTENCES = 8       # Default summary length
DEFAULT_QUIZ_QS   = 5       # Default quiz questions per type
DEFAULT_KEYWORDS  = 10      # Default keywords to extract
CACHE_DIR         = ...     # Subtitle cache location (system temp)
STOPWORDS         = {...}   # Customizable set of ignored words
```

To add more stopwords or change defaults, edit these values directly.

---

## 🔍 How It Works

```
YouTube URL
    │
    ▼
yt-dlp → downloads .vtt subtitle file
    │
    ▼
VTT Parser → strips timestamps, tags, cues, speaker labels → plain text
    │
    ▼
Cleaner → normalizes unicode, whitespace
    │
    ├──► Chunker (if long) → map-reduce summarization
    │
    ▼
Summarizer (LSA / Luhn / LexRank / Naive)
    │
    ├──► Keyword Extractor (frequency + TF-IDF)
    ├──► Text Statistics (words, sentences, diversity)
    ├──► Readability (Flesch scores)
    ├──► Sentiment (TextBlob polarity & subjectivity)
    └──► Quiz Generator (FITB + Multiple Choice)
         │
         ▼
    VideoReport dataclass
         │
         ▼
    Export: Text / Markdown / JSON
```

---

## 🤝 Contributing

Contributions are welcome! To get started:

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes and commit: `git commit -m "Add: your feature"`
4. Push to your fork: `git push origin feature/your-feature-name`
5. Open a Pull Request

### Ideas for contributions
- Add support for more languages (currently English only)
- GPU-accelerated summarization via Transformers / BART
- Chapter-aware summarization using YouTube chapter markers
- Database storage for report history
- Docker image

---

## 📄 License

This project is licensed under the **MIT License**.  
Feel free to use, modify, and distribute it.

---

<p align="center">Made with ❤️ by Hariom</p>
