import jwt
import datetime
import secrets
from functools import wraps
from flask import request, jsonify, current_app, g, session, redirect
from .db import get_db


def generate_token(user_id, role):
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=current_app.config["JWT_EXPIRY_HOURS"]),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])


def generate_reset_token():
    return secrets.token_urlsafe(32)


def get_bearer_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header.split(" ", 1)[1]
    return None


def load_user_from_session():
    """Returns the sqlite3.Row for the session-cookie-authenticated user, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None or user["status"] == "suspended":
        return None
    return user


def token_required(f):
    """Protects an /api/* route. Accepts EITHER the Flask session cookie (set at
    login/signup for browser page requests) OR an Authorization: Bearer <JWT> header
    (for external API clients). Attaches g.current_user either way."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = load_user_from_session()
        if user is not None:
            g.current_user = user
            return f(*args, **kwargs)

        token = get_bearer_token()
        if not token:
            return jsonify({"error": "Authentication required. Log in, or include an Authorization: Bearer <token> header."}), 401
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid authentication token."}), 401

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = ?", (payload["sub"],)).fetchone()
        if user is None:
            return jsonify({"error": "User no longer exists."}), 401
        if user["status"] == "suspended":
            return jsonify({"error": "This account has been suspended."}), 403

        g.current_user = user
        return f(*args, **kwargs)
    return wrapper


def page_login_required(f):
    """Protects a page (non-API) route. Redirects to /login instead of returning JSON."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = load_user_from_session()
        if user is None:
            return redirect("/login?next=" + request.path)
        g.current_user = user
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Protects a route: requires the authenticated user to have the admin role."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "current_user" not in g or g.current_user["role"] != "admin":
            return jsonify({"error": "Admin access required."}), 403
        return f(*args, **kwargs)
    return wrapper
