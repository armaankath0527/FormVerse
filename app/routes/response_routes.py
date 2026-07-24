import csv
import io
import json
from flask import Blueprint, request, jsonify, g, Response
from ..db import get_db
from ..auth_utils import token_required
from .form_routes import get_owned_form_or_404

response_bp = Blueprint("responses", __name__)


def _answers_for(db, response_id):
    rows = db.execute(
        """SELECT ra.field_id, ra.value, f.label FROM response_answers ra
           LEFT JOIN fields f ON f.id = ra.field_id WHERE ra.response_id = ?""",
        (response_id,),
    ).fetchall()
    return {r["label"] or f"field_{r['field_id']}": r["value"] for r in rows}


@response_bp.route("/forms/<int:form_id>/responses", methods=["GET"])
@token_required
def list_responses(form_id):
    db = get_db()
    form = get_owned_form_or_404(db, form_id, g.current_user["id"])
    if not form:
        return jsonify({"error": "Form not found."}), 404

    status = request.args.get("status", "")
    sort = request.args.get("sort", "recent")
    query = "SELECT * FROM responses WHERE form_id = ?"
    params = [form_id]
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY submitted_at " + ("ASC" if sort == "oldest" else "DESC")

    rows = db.execute(query, params).fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "formId": r["form_id"],
            "submittedAt": r["submitted_at"],
            "device": r["device"],
            "status": r["status"],
            "answers": _answers_for(db, r["id"]),
        })
    return jsonify({"responses": results, "count": len(results)})


@response_bp.route("/responses/<int:response_id>", methods=["GET"])
@token_required
def get_response(response_id):
    db = get_db()
    row = db.execute(
        """SELECT r.* FROM responses r JOIN forms f ON f.id = r.form_id
           WHERE r.id = ? AND f.user_id = ?""",
        (response_id, g.current_user["id"]),
    ).fetchone()
    if not row:
        return jsonify({"error": "Response not found."}), 404
    return jsonify({
        "response": {
            "id": row["id"], "formId": row["form_id"], "submittedAt": row["submitted_at"],
            "device": row["device"], "status": row["status"], "answers": _answers_for(db, row["id"]),
        }
    })


@response_bp.route("/responses/<int:response_id>", methods=["DELETE"])
@token_required
def delete_response(response_id):
    db = get_db()
    row = db.execute(
        """SELECT r.id FROM responses r JOIN forms f ON f.id = r.form_id
           WHERE r.id = ? AND f.user_id = ?""",
        (response_id, g.current_user["id"]),
    ).fetchone()
    if not row:
        return jsonify({"error": "Response not found."}), 404
    db.execute("DELETE FROM responses WHERE id = ?", (response_id,))
    db.commit()
    return jsonify({"message": "Response deleted."})


@response_bp.route("/forms/<int:form_id>/responses/bulk-delete", methods=["POST"])
@token_required
def bulk_delete_responses(form_id):
    db = get_db()
    form = get_owned_form_or_404(db, form_id, g.current_user["id"])
    if not form:
        return jsonify({"error": "Form not found."}), 404
    ids = (request.get_json(silent=True) or {}).get("ids", [])
    if not ids:
        return jsonify({"error": "No response ids provided."}), 400
    placeholders = ",".join("?" * len(ids))
    db.execute(f"DELETE FROM responses WHERE form_id = ? AND id IN ({placeholders})", [form_id] + ids)
    db.commit()
    return jsonify({"message": f"Deleted {len(ids)} response(s)."})


@response_bp.route("/forms/<int:form_id>/responses/export", methods=["GET"])
@token_required
def export_responses(form_id):
    db = get_db()
    form = get_owned_form_or_404(db, form_id, g.current_user["id"])
    if not form:
        return jsonify({"error": "Form not found."}), 404

    fmt = request.args.get("format", "csv").lower()
    rows = db.execute("SELECT * FROM responses WHERE form_id = ? ORDER BY submitted_at DESC", (form_id,)).fetchall()
    fields = db.execute("SELECT label FROM fields WHERE form_id = ? ORDER BY order_index", (form_id,)).fetchall()
    field_labels = [f["label"] for f in fields]

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Response ID", "Submitted At", "Device", "Status"] + field_labels)
    for r in rows:
        answers = _answers_for(db, r["id"])
        writer.writerow([r["id"], r["submitted_at"], r["device"], r["status"]] + [answers.get(l, "") for l in field_labels])

    csv_data = buf.getvalue()
    filename = f"{form['title'].replace(' ', '_')}_responses.csv"
    # Note: true .xlsx generation needs an Excel-writing library (e.g. openpyxl) which isn't
    # installed in this environment yet — CSV opens cleanly in Excel/Sheets as a stand-in for now.
    mimetype = "text/csv"
    return Response(
        csv_data, mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
