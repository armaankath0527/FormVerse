import json
import datetime
from flask import Blueprint, request, jsonify
from ..db import get_db
from .form_routes import field_public

public_bp = Blueprint("public", __name__)


@public_bp.route("/forms/<share_slug>", methods=["GET"])
def get_public_form(share_slug):
    db = get_db()
    row = db.execute(
        "SELECT * FROM forms WHERE share_slug = ? AND status = 'published' AND is_public = 1", (share_slug,)
    ).fetchone()
    if not row:
        return jsonify({"error": "This form isn't available."}), 404
    if row["expires_at"] and row["expires_at"] < datetime.datetime.utcnow().isoformat():
        return jsonify({"error": "This form is no longer accepting responses."}), 410

    source = request.args.get("source", "direct")
    device = request.args.get("device", "Desktop")
    db.execute("INSERT INTO views (form_id, device, source) VALUES (?, ?, ?)", (row["id"], device, source))
    db.commit()

    fields = db.execute("SELECT * FROM fields WHERE form_id = ? ORDER BY order_index", (row["id"],)).fetchall()
    return jsonify({
        "form": {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "theme": json.loads(row["theme_json"] or "{}"),
            "fields": [field_public(f) for f in fields],
        }
    })


@public_bp.route("/forms/<share_slug>/submit", methods=["POST"])
def submit_response(share_slug):
    db = get_db()
    row = db.execute(
        "SELECT * FROM forms WHERE share_slug = ? AND status = 'published' AND is_public = 1", (share_slug,)
    ).fetchone()
    if not row:
        return jsonify({"error": "This form isn't available."}), 404

    data = request.get_json(silent=True) or {}
    answers = data.get("answers", {})  # { field_id: value }
    device = data.get("device", "Desktop")

    required_fields = db.execute(
        "SELECT id, label FROM fields WHERE form_id = ? AND required = 1", (row["id"],)
    ).fetchall()
    missing = [f["label"] for f in required_fields if not str(answers.get(str(f["id"]), "")).strip()]
    if missing:
        return jsonify({"error": "Please fill in all required fields.", "missing": missing}), 400

    cur = db.execute("INSERT INTO responses (form_id, device) VALUES (?, ?)", (row["id"], device))
    response_id = cur.lastrowid
    for field_id, value in answers.items():
        db.execute(
            "INSERT INTO response_answers (response_id, field_id, value) VALUES (?, ?, ?)",
            (response_id, field_id, json.dumps(value) if isinstance(value, (list, dict)) else str(value)),
        )
    db.execute(
        "INSERT INTO notifications (user_id, message, type) VALUES (?, ?, 'info')",
        (row["user_id"], f'"{row["title"]}" received a new response.'),
    )
    db.commit()
    return jsonify({"message": "Response submitted.", "responseId": response_id}), 201
