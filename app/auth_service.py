"""Shared auth logic so both the JSON API routes and the server-rendered page
routes (login/signup forms) can create/authenticate users without duplicating code."""
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db


class AuthError(Exception):
    """Raised with a user-facing message when register/login fails validation."""
    pass


def create_user(name, email, password):
    name = (name or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    if not name or not email or len(password) < 8:
        raise AuthError("Name, a valid email, and a password of at least 8 characters are required.")

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        raise AuthError("An account with that email already exists.")

    password_hash = generate_password_hash(password)
    user_count = db.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    role = "admin" if user_count == 0 else "user"  # first-ever user becomes admin

    cur = db.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, role),
    )
    db.commit()
    return db.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()


def authenticate(email, password):
    email = (email or "").strip().lower()
    password = password or ""
    if not email or not password:
        raise AuthError("Email and password are required.")

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        raise AuthError("Incorrect email or password.")
    if user["status"] == "suspended":
        raise AuthError("This account has been suspended.")
    return user


def user_initials(name):
    parts = (name or "").split()
    return "".join(p[0] for p in parts[:2]).upper() or "?"
