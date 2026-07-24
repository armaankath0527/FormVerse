import json
import secrets
from flask import Blueprint, request, jsonify, g
from ..db import get_db
from ..auth_utils import token_required

form_bp = Blueprint("forms", __name__)


def field_public(row):
    return {
        "id": row["id"],
        "type": row["type"],
        "label": row["label"],
        "placeholder": row["placeholder"],
        "helpText": row["help_text"],
        "required": bool(row["required"]),
        "charLimit": row["char_limit"],
        "options": json.loads(row["options_json"] or "[]"),
        "order": row["order_index"],
    }


def form_public(db, row, with_fields=True):
    data = {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "theme": json.loads(row["theme_json"] or "{}"),
        "shareSlug": row["share_slug"],
        "isPublic": bool(row["is_public"]),
        "expiresAt": row["expires_at"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }
    resp_count = db.execute("SELECT COUNT(*) AS c FROM responses WHERE form_id = ?", (row["id"],)).fetchone()["c"]
    view_count = db.execute("SELECT COUNT(*) AS c FROM views WHERE form_id = ?", (row["id"],)).fetchone()["c"]
    data["responseCount"] = resp_count
    data["viewCount"] = view_count
    if with_fields:
        fields = db.execute(
            "SELECT * FROM fields WHERE form_id = ? ORDER BY order_index ASC", (row["id"],)
        ).fetchall()
        data["fields"] = [field_public(f) for f in fields]
    return data


def get_owned_form_or_404(db, form_id, user_id):
    row = db.execute("SELECT * FROM forms WHERE id = ? AND user_id = ?", (form_id, user_id)).fetchone()
    return row


@form_bp.route("", methods=["GET"])
@token_required
def list_forms():
    db = get_db()
    q = request.args.get("q", "").strip().lower()
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "recent")

    query = "SELECT * FROM forms WHERE user_id = ?"
    params = [g.current_user["id"]]
    if status:
        query += " AND status = ?"
        params.append(status)
    if q:
        query += " AND LOWER(title) LIKE ?"
        params.append(f"%{q}%")

    order_map = {
        "recent": "updated_at DESC",
        "name": "title ASC",
        "responses": "id DESC",  # response count sorted after fetch (needs join); handled below for correctness
    }
    query += f" ORDER BY {order_map.get(sort, 'updated_at DESC')}"

    rows = db.execute(query, params).fetchall()
    forms = [form_public(db, r, with_fields=False) for r in rows]
    if sort == "responses":
        forms.sort(key=lambda f: f["responseCount"], reverse=True)
    return jsonify({"forms": forms})


@form_bp.route("", methods=["POST"])
@token_required
def create_form():
    data = request.get_json(silent=True) or {}
    title = data.get("title") or "Untitled form"
    description = data.get("description") or ""
    db = get_db()
    cur = db.execute(
        "INSERT INTO forms (user_id, title, description, share_slug) VALUES (?, ?, ?, ?)",
        (g.current_user["id"], title, description, secrets.token_urlsafe(6)),
    )
    db.commit()
    row = db.execute("SELECT * FROM forms WHERE id = ?", (cur.lastrowid,)).fetchone()
    _sync_fields(db, cur.lastrowid, data.get("fields", []))
    db.commit()
    row = db.execute("SELECT * FROM forms WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify({"form": form_public(db, row)}), 201


@form_bp.route("/<int:form_id>", methods=["GET"])
@token_required
def get_form(form_id):
    db = get_db()
    row = get_owned_form_or_404(db, form_id, g.current_user["id"])
    if not row:
        return jsonify({"error": "Form not found."}), 404
    return jsonify({"form": form_public(db, row)})


def _sync_fields(db, form_id, fields):
    """Replace all fields for a form with the given ordered list."""
    db.execute("DELETE FROM fields WHERE form_id = ?", (form_id,))
    for idx, f in enumerate(fields):
        db.execute(
            """INSERT INTO fields (form_id, type, label, placeholder, help_text, required, char_limit, options_json, order_index)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                form_id,
                f.get("type", "short"),
                f.get("label", ""),
                f.get("placeholder", ""),
                f.get("helpText", ""),
                1 if f.get("required") else 0,
                f.get("charLimit"),
                json.dumps(f.get("options", [])),
                idx,
            ),
        )


@form_bp.route("/<int:form_id>", methods=["PUT"])
@token_required
def update_form(form_id):
    db = get_db()
    row = get_owned_form_or_404(db, form_id, g.current_user["id"])
    if not row:
        return jsonify({"error": "Form not found."}), 404

    data = request.get_json(silent=True) or {}
    title = data.get("title", row["title"])
    description = data.get("description", row["description"])
    theme = json.dumps(data.get("theme", json.loads(row["theme_json"] or "{}")))

    db.execute(
        "UPDATE forms SET title = ?, description = ?, theme_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (title, description, theme, form_id),
    )
    if "fields" in data:
        _sync_fields(db, form_id, data["fields"])
    db.commit()
    row = db.execute("SELECT * FROM forms WHERE id = ?", (form_id,)).fetchone()
    return jsonify({"form": form_public(db, row)})


@form_bp.route("/<int:form_id>", methods=["DELETE"])
@token_required
def delete_form(form_id):
    db = get_db()
    row = get_owned_form_or_404(db, form_id, g.current_user["id"])
    if not row:
        return jsonify({"error": "Form not found."}), 404
    db.execute("DELETE FROM forms WHERE id = ?", (form_id,))
    db.commit()
    return jsonify({"message": "Form deleted."})


@form_bp.route("/<int:form_id>/duplicate", methods=["POST"])
@token_required
def duplicate_form(form_id):
    db = get_db()
    row = get_owned_form_or_404(db, form_id, g.current_user["id"])
    if not row:
        return jsonify({"error": "Form not found."}), 404

    cur = db.execute(
        "INSERT INTO forms (user_id, title, description, status, theme_json, share_slug) VALUES (?, ?, ?, 'draft', ?, ?)",
        (g.current_user["id"], row["title"] + " (copy)", row["description"], row["theme_json"], secrets.token_urlsafe(6)),
    )
    new_id = cur.lastrowid
    fields = db.execute("SELECT * FROM fields WHERE form_id = ? ORDER BY order_index", (form_id,)).fetchall()
    for f in fields:
        db.execute(
            """INSERT INTO fields (form_id, type, label, placeholder, help_text, required, char_limit, options_json, order_index)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (new_id, f["type"], f["label"], f["placeholder"], f["help_text"], f["required"],
             f["char_limit"], f["options_json"], f["order_index"]),
        )
    db.commit()
    new_row = db.execute("SELECT * FROM forms WHERE id = ?", (new_id,)).fetchone()
    return jsonify({"form": form_public(db, new_row)}), 201


@form_bp.route("/<int:form_id>/publish", methods=["POST"])
@token_required
def publish_form(form_id):
    db = get_db()
    row = get_owned_form_or_404(db, form_id, g.current_user["id"])
    if not row:
        return jsonify({"error": "Form not found."}), 404
    db.execute("UPDATE forms SET status = 'published', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (form_id,))
    db.execute(
        "INSERT INTO notifications (user_id, message, type) VALUES (?, ?, 'success')",
        (g.current_user["id"], f'"{row["title"]}" was published.'),
    )
    db.commit()
    row = db.execute("SELECT * FROM forms WHERE id = ?", (form_id,)).fetchone()
    return jsonify({"form": form_public(db, row)})


@form_bp.route("/<int:form_id>/archive", methods=["POST"])
@token_required
def archive_form(form_id):
    db = get_db()
    row = get_owned_form_or_404(db, form_id, g.current_user["id"])
    if not row:
        return jsonify({"error": "Form not found."}), 404
    db.execute("UPDATE forms SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (form_id,))
    db.commit()
    row = db.execute("SELECT * FROM forms WHERE id = ?", (form_id,)).fetchone()
    return jsonify({"form": form_public(db, row)})
