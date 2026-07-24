"""
Populates the database with a demo account, sample forms, fields, and responses —
so the frontend has real data to display immediately after connecting.

Run with:  python seed.py
"""
import random
import datetime
from app import create_app
from app.db import get_db
from werkzeug.security import generate_password_hash

app = create_app()

DEMO_EMAIL = "demo@formverse.io"
DEMO_PASSWORD = "password123"

SAMPLE_FORMS = [
    {
        "title": "Customer Feedback Survey",
        "description": "Tell us how we're doing.",
        "status": "published",
        "fields": [
            {"type": "short", "label": "Your name", "required": True},
            {"type": "email", "label": "Email address", "required": True},
            {"type": "rating", "label": "How satisfied are you?", "required": True},
            {"type": "long", "label": "Anything we can improve?", "required": False},
        ],
        "responses": 42,
    },
    {
        "title": "Event Registration",
        "description": "Register for the FormVerse summer meetup.",
        "status": "published",
        "fields": [
            {"type": "short", "label": "Full name", "required": True},
            {"type": "email", "label": "Email address", "required": True},
            {"type": "dropdown", "label": "Ticket type", "required": True,
             "options": ["General", "VIP", "Student"]},
        ],
        "responses": 29,
    },
    {
        "title": "Job Application — Backend Engineer",
        "description": "",
        "status": "draft",
        "fields": [
            {"type": "short", "label": "Full name", "required": True},
            {"type": "file", "label": "Resume", "required": True},
        ],
        "responses": 0,
    },
]


def run():
    with app.app_context():
        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (DEMO_EMAIL,)).fetchone()
        if existing:
            print("Demo account already exists — skipping seed.")
            return

        cur = db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Jordan Blake", DEMO_EMAIL, generate_password_hash(DEMO_PASSWORD), "admin"),
        )
        user_id = cur.lastrowid

        for form_def in SAMPLE_FORMS:
            import secrets
            fcur = db.execute(
                "INSERT INTO forms (user_id, title, description, status, share_slug) VALUES (?, ?, ?, ?, ?)",
                (user_id, form_def["title"], form_def["description"], form_def["status"], secrets.token_urlsafe(6)),
            )
            form_id = fcur.lastrowid
            field_ids = []
            for idx, f in enumerate(form_def["fields"]):
                import json
                fldcur = db.execute(
                    """INSERT INTO fields (form_id, type, label, required, options_json, order_index)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (form_id, f["type"], f["label"], 1 if f["required"] else 0,
                     json.dumps(f.get("options", [])), idx),
                )
                field_ids.append(fldcur.lastrowid)

            for i in range(form_def["responses"]):
                days_ago = random.randint(0, 13)
                submitted = (datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)).isoformat()
                device = random.choice(["Desktop", "Mobile", "Tablet"])
                rcur = db.execute(
                    "INSERT INTO responses (form_id, submitted_at, device) VALUES (?, ?, ?)",
                    (form_id, submitted, device),
                )
                response_id = rcur.lastrowid
                for fid in field_ids:
                    db.execute(
                        "INSERT INTO response_answers (response_id, field_id, value) VALUES (?, ?, ?)",
                        (response_id, fid, "Sample answer"),
                    )

            for i in range(form_def["responses"] * 3 + 10):
                days_ago = random.randint(0, 13)
                viewed = (datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)).isoformat()
                db.execute(
                    "INSERT INTO views (form_id, viewed_at, device, source) VALUES (?, ?, ?, ?)",
                    (form_id, viewed, random.choice(["Desktop", "Mobile", "Tablet"]),
                     random.choice(["direct", "qr", "embed", "social"])),
                )

        db.commit()
        print(f"Seeded demo account: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    run()
