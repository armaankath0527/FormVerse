import datetime
from flask import Blueprint, render_template, request, redirect, session, g
from werkzeug.security import generate_password_hash
from ..db import get_db
from ..auth_utils import page_login_required, load_user_from_session, generate_reset_token
from ..auth_service import create_user, authenticate, AuthError, user_initials

pages_bp = Blueprint("pages", __name__)


def _user_ctx():
    """Small dict handed to every app-shell template for the sidebar user chip."""
    u = g.current_user
    return {"name": u["name"], "email": u["email"], "initials": user_initials(u["name"])}


@pages_bp.route("/")
def landing():
    if load_user_from_session() is not None:
        return redirect("/app/dashboard")
    return render_template("landing.html")


@pages_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if load_user_from_session() is not None:
        return redirect("/app/dashboard")
    next_url = request.values.get("next") or "/app/dashboard"
    if request.method == "GET":
        return render_template("login.html", next=next_url)

    email = request.form.get("email", "")
    password = request.form.get("password", "")
    try:
        user = authenticate(email, password)
    except AuthError as e:
        return render_template("login.html", error=str(e), email=email, next=next_url), 401

    session["user_id"] = user["id"]
    return redirect(next_url if next_url.startswith("/") else "/app/dashboard")


@pages_bp.route("/signup", methods=["GET", "POST"])
def signup_page():
    if load_user_from_session() is not None:
        return redirect("/app/dashboard")
    if request.method == "GET":
        return render_template("signup.html")

    name = request.form.get("name", "")
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    try:
        user = create_user(name, email, password)
    except AuthError as e:
        return render_template("signup.html", error=str(e), name=name, email=email), 400

    session["user_id"] = user["id"]
    return redirect("/app/dashboard")


@pages_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password_page():
    if request.method == "GET":
        return render_template("forgot_password.html")

    email = (request.form.get("email") or "").strip().lower()
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    dev_token = None
    if user:
        from flask import current_app
        token = generate_reset_token()
        expires = (datetime.datetime.utcnow() + datetime.timedelta(
            minutes=current_app.config["RESET_TOKEN_EXPIRY_MINUTES"])).isoformat()
        db.execute("INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)",
                   (user["id"], token, expires))
        db.commit()
        dev_token = token  # no email provider configured yet — surfaced directly instead
    return render_template("forgot_password.html", sent=True, dev_token=dev_token)


@pages_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password_page():
    token = request.values.get("token", "")
    if request.method == "GET":
        return render_template("reset_password.html", token=token)

    new_password = request.form.get("password", "")
    if len(new_password) < 8:
        return render_template("reset_password.html", token=token, error="Password must be at least 8 characters."), 400

    db = get_db()
    reset = db.execute("SELECT * FROM password_resets WHERE token = ? AND used = 0", (token,)).fetchone()
    if not reset:
        return render_template("reset_password.html", token=token, error="This reset link is invalid or has already been used."), 400
    if datetime.datetime.fromisoformat(reset["expires_at"]) < datetime.datetime.utcnow():
        return render_template("reset_password.html", token=token, error="This reset link has expired. Request a new one."), 400

    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(new_password), reset["user_id"]))
    db.execute("UPDATE password_resets SET used = 1 WHERE id = ?", (reset["id"],))
    db.commit()
    return render_template("reset_password.html", token=token, done=True)


@pages_bp.route("/logout", methods=["POST"])
def logout_page():
    session.pop("user_id", None)
    return redirect("/")


@pages_bp.route("/f/<slug>")
def public_form_page(slug):
    return render_template("public_form.html", slug=slug)


# ---------------- app shell pages (require login) ----------------

@pages_bp.route("/app/dashboard")
@page_login_required
def dashboard_page():
    return render_template("dashboard.html", user=_user_ctx())


@pages_bp.route("/app/forms")
@page_login_required
def forms_page():
    return render_template("forms.html", user=_user_ctx())


@pages_bp.route("/app/builder")
@page_login_required
def builder_new_page():
    return render_template("builder.html", user=_user_ctx(), form_id=None)


@pages_bp.route("/app/builder/<int:form_id>")
@page_login_required
def builder_edit_page(form_id):
    return render_template("builder.html", user=_user_ctx(), form_id=form_id)


@pages_bp.route("/app/responses")
@page_login_required
def responses_page():
    return render_template("responses.html", user=_user_ctx())


@pages_bp.route("/app/analytics")
@page_login_required
def analytics_page():
    return render_template("analytics.html", user=_user_ctx())


@pages_bp.route("/app/settings")
@page_login_required
def settings_page():
    return render_template("settings.html", user=_user_ctx())
