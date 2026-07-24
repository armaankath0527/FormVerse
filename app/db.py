import sqlite3
from flask import g, current_app


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',       -- user | admin
    status TEXT NOT NULL DEFAULT 'active',   -- active | suspended
    avatar_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS password_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Untitled form',
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',   -- draft | published | archived
    theme_json TEXT DEFAULT '{}',
    share_slug TEXT UNIQUE,
    is_public INTEGER NOT NULL DEFAULT 1,
    expires_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_id INTEGER NOT NULL REFERENCES forms(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    placeholder TEXT DEFAULT '',
    help_text TEXT DEFAULT '',
    required INTEGER NOT NULL DEFAULT 0,
    char_limit INTEGER,
    options_json TEXT DEFAULT '[]',
    order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_id INTEGER NOT NULL REFERENCES forms(id) ON DELETE CASCADE,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    device TEXT DEFAULT 'Desktop',
    status TEXT NOT NULL DEFAULT 'complete'  -- complete | flagged
);

CREATE TABLE IF NOT EXISTS response_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER NOT NULL REFERENCES responses(id) ON DELETE CASCADE,
    field_id INTEGER REFERENCES fields(id) ON DELETE SET NULL,
    value TEXT
);

CREATE TABLE IF NOT EXISTS views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_id INTEGER NOT NULL REFERENCES forms(id) ON DELETE CASCADE,
    viewed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    device TEXT DEFAULT 'Desktop',
    source TEXT DEFAULT 'direct'   -- direct | qr | embed | social
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info',
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db(app):
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        db.commit()
