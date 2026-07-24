# FormVerse

A full-stack **multi-page** web app — Flask serves both the pages and the API, so there's
one server, one URL, and real browser navigation (every sidebar link and button is an actual
page load with its own URL, not a JS view-toggle). SQLite (Python's built-in `sqlite3`) is
the database — no separate database server to install.

This replaces the earlier single-file HTML prototype: the frontend and backend are now one
app, which also removes the "do these need to be in the same folder / running together"
confusion — there's only one thing to run.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Seed demo data (recommended)

```bash
python seed.py
```

Creates a demo account with sample forms and responses already in place:

```
Email:    demo@formverse.io
Password: password123
```

## Run it

```bash
python run.py
```

Open **http://127.0.0.1:5000** in your browser. That's it — one process, one port, pages and
API both served from there.


