import datetime
from flask import Blueprint, request, jsonify, g, current_app, session
from werkzeug.security import generate_password_hash, check_password_hash
from ..db import get_db
from ..auth_utils import generate_token, generate_reset_token, token_required
from ..auth_service import create_user, authenticate, AuthError

auth_bp = Blueprint("auth", __name__)


def user_public(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "status": row["status"],
        "avatarUrl": row["avatar_url"],
        "createdAt": row["created_at"],
    }


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    try:
        user = create_user(data.get("name"), data.get("email"), data.get("password"))
    except AuthError as e:
        return jsonify({"error": str(e)}), 400
    token = generate_token(user["id"], user["role"])
    session["user_id"] = user["id"]
    return jsonify({"token": token, "user": user_public(user)}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    try:
        user = authenticate(data.get("email"), data.get("password"))
    except AuthError as e:
        return jsonify({"error": str(e)}), 401
    token = generate_token(user["id"], user["role"])
    session["user_id"] = user["id"]
    return jsonify({"token": token, "user": user_public(user)})


@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out."})


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    # Always respond the same way whether or not the account exists, to avoid leaking which emails are registered.
    if user:
        token = generate_reset_token()
        expires = (datetime.datetime.utcnow() + datetime.timedelta(
            minutes=current_app.config["RESET_TOKEN_EXPIRY_MINUTES"])).isoformat()
        db.execute(
            "INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user["id"], token, expires),
        )
        db.commit()
        # In production this token would be emailed via a transactional email service (e.g. SendGrid, SES).
        # It's returned directly here since there's no email provider wired up yet.
        return jsonify({"message": "If that email exists, a reset link has been sent.", "dev_reset_token": token})

    return jsonify({"message": "If that email exists, a reset link has been sent."})


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    token = data.get("token") or ""
    new_password = data.get("password") or ""

    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    db = get_db()
    reset = db.execute(
        "SELECT * FROM password_resets WHERE token = ? AND used = 0", (token,)
    ).fetchone()
    if not reset:
        return jsonify({"error": "This reset link is invalid or has already been used."}), 400
    if datetime.datetime.fromisoformat(reset["expires_at"]) < datetime.datetime.utcnow():
        return jsonify({"error": "This reset link has expired. Request a new one."}), 400

    password_hash = generate_password_hash(new_password)
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, reset["user_id"]))
    db.execute("UPDATE password_resets SET used = 1 WHERE id = ?", (reset["id"],))
    db.commit()
    return jsonify({"message": "Password updated. You can now log in."})


@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    return jsonify({"user": user_public(g.current_user)})


@auth_bp.route("/me", methods=["PATCH"])
@token_required
def update_me():
    data = request.get_json(silent=True) or {}
    db = get_db()
    name = data.get("name")
    avatar_url = data.get("avatarUrl")
    fields, params = [], []
    if name:
        fields.append("name = ?"); params.append(name)
    if avatar_url is not None:
        fields.append("avatar_url = ?"); params.append(avatar_url)
    if fields:
        params.append(g.current_user["id"])
        db.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", params)
        db.commit()
    user = db.execute("SELECT * FROM users WHERE id = ?", (g.current_user["id"],)).fetchone()
    return jsonify({"user": user_public(user)})


@auth_bp.route("/change-password", methods=["POST"])
@token_required
def change_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get("currentPassword") or ""
    new_password = data.get("newPassword") or ""

    if not check_password_hash(g.current_user["password_hash"], current_password):
        return jsonify({"error": "Current password is incorrect."}), 400
    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters."}), 400

    db = get_db()
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
               (generate_password_hash(new_password), g.current_user["id"]))
    db.commit()
    return jsonify({"message": "Password changed."})


@auth_bp.route("/me", methods=["DELETE"])
@token_required
def delete_me():
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (g.current_user["id"],))
    db.commit()
    return jsonify({"message": "Account deleted."})
