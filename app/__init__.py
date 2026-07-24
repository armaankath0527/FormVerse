from flask import Flask, jsonify
from .config import Config
from .db import close_db, init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config["SECRET_KEY"]  # powers the session cookie used for page auth

    app.teardown_appcontext(close_db)
    init_db(app)

    # --- CORS (hand-rolled, no flask-cors dependency needed) ---
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = app.config.get("CORS_ORIGINS", "*")
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

    @app.route("/api/<path:_any>", methods=["OPTIONS"])
    def cors_preflight(_any):
        return "", 204

    # --- Blueprints ---
    from .routes.auth_routes import auth_bp
    from .routes.form_routes import form_bp
    from .routes.public_routes import public_bp
    from .routes.response_routes import response_bp
    from .routes.analytics_routes import analytics_bp
    from .routes.notification_routes import notification_bp
    from .routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(form_bp, url_prefix="/api/forms")
    app.register_blueprint(public_bp, url_prefix="/api/public")
    app.register_blueprint(response_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")
    app.register_blueprint(notification_bp, url_prefix="/api/notifications")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    from .pages.page_routes import pages_bp
    app.register_blueprint(pages_bp)

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "FormVerse API"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app
