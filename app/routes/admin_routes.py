from flask import Blueprint, jsonify, request, g
from ..db import get_db
from ..auth_utils import token_required, admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@token_required
@admin_required
def list_users():
    db = get_db()
    rows = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    users = []
    for r in rows:
        form_count = db.execute("SELECT COUNT(*) AS c FROM forms WHERE user_id = ?", (r["id"],)).fetchone()["c"]
        users.append({
            "id": r["id"], "name": r["name"], "email": r["email"], "role": r["role"],
            "status": r["status"], "createdAt": r["created_at"], "formCount": form_count,
        })
    return jsonify({"users": users})


@admin_bp.route("/users/<int:user_id>", methods=["PATCH"])
@token_required
@admin_required
def update_user_status(user_id):
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in ("active", "suspended"):
        return jsonify({"error": "Status must be 'active' or 'suspended'."}), 400
    db = get_db()
    db.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    db.commit()
    return jsonify({"message": f"User set to {new_status}."})


@admin_bp.route("/forms", methods=["GET"])
@token_required
@admin_required
def list_all_forms():
    db = get_db()
    rows = db.execute(
        """SELECT f.*, u.name AS owner_name, u.email AS owner_email FROM forms f
           JOIN users u ON u.id = f.user_id ORDER BY f.created_at DESC"""
    ).fetchall()
    forms = []
    for r in rows:
        resp_count = db.execute("SELECT COUNT(*) AS c FROM responses WHERE form_id = ?", (r["id"],)).fetchone()["c"]
        forms.append({
            "id": r["id"], "title": r["title"], "status": r["status"],
            "ownerName": r["owner_name"], "ownerEmail": r["owner_email"],
            "responseCount": resp_count, "createdAt": r["created_at"],
        })
    return jsonify({"forms": forms})


@admin_bp.route("/stats", methods=["GET"])
@token_required
@admin_required
def platform_stats():
    db = get_db()
    total_users = db.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    total_forms = db.execute("SELECT COUNT(*) AS c FROM forms").fetchone()["c"]
    total_responses = db.execute("SELECT COUNT(*) AS c FROM responses").fetchone()["c"]
    published_forms = db.execute("SELECT COUNT(*) AS c FROM forms WHERE status = 'published'").fetchone()["c"]
    suspended_users = db.execute("SELECT COUNT(*) AS c FROM users WHERE status = 'suspended'").fetchone()["c"]
    return jsonify({
        "totalUsers": total_users, "totalForms": total_forms, "totalResponses": total_responses,
        "publishedForms": published_forms, "suspendedUsers": suspended_users,
    })
