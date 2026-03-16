# WorkBoard

Personal intranet dashboard for managing my work life during internship/apprenticeship.

## Features

- 📅 Planning / agenda (weekly view)
- ✅ Task tracking with built-in timer
- 📁 Document storage (bulletins, contracts...)
- 📝 Markdown notes with live preview
- 🎯 Goals & KPIs with progress tracking

## Stack

Flask 3.x · SQLAlchemy · SQLite · Jinja2 · TailwindCSS · Chart.js

## Setup

```bash
git clone https://github.com/Kiwi6212/workboard
cd workboard
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in your token
python run.py
```

## Deploy

Served via Gunicorn on port 8080, managed by systemd. No domain required — direct IP access.

## License

MIT
