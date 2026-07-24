from flask import Blueprint, jsonify, g
from ..db import get_db
from ..auth_utils import token_required

notification_bp = Blueprint("notifications", __name__)


@notification_bp.route("", methods=["GET"])
@token_required
def list_notifications():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
        (g.current_user["id"],),
    ).fetchall()
    notifications = [
        {"id": r["id"], "message": r["message"], "type": r["type"],
         "isRead": bool(r["is_read"]), "createdAt": r["created_at"]}
        for r in rows
    ]
    unread = sum(1 for n in notifications if not n["isRead"])
    return jsonify({"notifications": notifications, "unreadCount": unread})


@notification_bp.route("/<int:notif_id>/read", methods=["POST"])
@token_required
def mark_read(notif_id):
    db = get_db()
    db.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
        (notif_id, g.current_user["id"]),
    )
    db.commit()
    return jsonify({"message": "Marked as read."})
