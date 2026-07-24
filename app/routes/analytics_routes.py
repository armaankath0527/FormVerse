import datetime
from flask import Blueprint, jsonify, g
from ..db import get_db
from ..auth_utils import token_required
from .form_routes import get_owned_form_or_404

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/forms/<int:form_id>/analytics", methods=["GET"])
@token_required
def form_analytics(form_id):
    db = get_db()
    form = get_owned_form_or_404(db, form_id, g.current_user["id"])
    if not form:
        return jsonify({"error": "Form not found."}), 404

    total_views = db.execute("SELECT COUNT(*) AS c FROM views WHERE form_id = ?", (form_id,)).fetchone()["c"]
    total_responses = db.execute("SELECT COUNT(*) AS c FROM responses WHERE form_id = ?", (form_id,)).fetchone()["c"]
    submission_rate = round((total_responses / total_views) * 100, 1) if total_views else 0.0

    device_rows = db.execute(
        "SELECT device, COUNT(*) AS c FROM views WHERE form_id = ? GROUP BY device", (form_id,)
    ).fetchall()
    device_breakdown = {r["device"]: r["c"] for r in device_rows}

    source_rows = db.execute(
        "SELECT source, COUNT(*) AS c FROM views WHERE form_id = ? GROUP BY source", (form_id,)
    ).fetchall()
    source_breakdown = {r["source"]: r["c"] for r in source_rows}

    trend_rows = db.execute(
        """SELECT DATE(submitted_at) AS day, COUNT(*) AS c FROM responses
           WHERE form_id = ? GROUP BY DATE(submitted_at) ORDER BY day ASC""",
        (form_id,),
    ).fetchall()
    trend = [{"date": r["day"], "responses": r["c"]} for r in trend_rows]

    return jsonify({
        "totalViews": total_views,
        "totalResponses": total_responses,
        "submissionRate": submission_rate,
        "deviceBreakdown": device_breakdown,
        "sourceBreakdown": source_breakdown,
        "responseTrend": trend,
    })


@analytics_bp.route("/dashboard/summary", methods=["GET"])
@token_required
def dashboard_summary():
    db = get_db()
    uid = g.current_user["id"]
    total_forms = db.execute("SELECT COUNT(*) AS c FROM forms WHERE user_id = ?", (uid,)).fetchone()["c"]
    active_forms = db.execute(
        "SELECT COUNT(*) AS c FROM forms WHERE user_id = ? AND status = 'published'", (uid,)
    ).fetchone()["c"]
    total_responses = db.execute(
        """SELECT COUNT(*) AS c FROM responses r JOIN forms f ON f.id = r.form_id WHERE f.user_id = ?""", (uid,)
    ).fetchone()["c"]
    trend_rows = db.execute(
        """SELECT DATE(r.submitted_at) AS day, COUNT(*) AS c FROM responses r
           JOIN forms f ON f.id = r.form_id WHERE f.user_id = ?
           GROUP BY DATE(r.submitted_at) ORDER BY day DESC LIMIT 14""",
        (uid,),
    ).fetchall()
    trend = [{"date": r["day"], "responses": r["c"]} for r in reversed(trend_rows)]

    recent_forms = db.execute(
        "SELECT * FROM forms WHERE user_id = ? ORDER BY updated_at DESC LIMIT 5", (uid,)
    ).fetchall()
    from .form_routes import form_public
    recent = [form_public(db, r, with_fields=False) for r in recent_forms]

    return jsonify({
        "totalForms": total_forms,
        "activeForms": active_forms,
        "totalResponses": total_responses,
        "responseTrend": trend,
        "recentForms": recent,
    })
