"""
Evently — Flask Application Factory
"""
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_caching import Cache

from app.config import config_by_name
from app.extensions import db, redis_client, ma

# Absolute path to the built React frontend (../frontend/dist relative to this file)
_FRONTEND_DIST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
)


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "production")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # ── Initialize Extensions ──
    db.init_app(app)
    ma.init_app(app)
    Migrate(app, db)
    JWTManager(app)
    Cache(app)
    CORS(app, origins=app.config.get("CORS_ORIGINS", "*"))

    # ── Register Blueprints ──
    from app.api.v1 import api_v1_bp
    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")

    # ── Health Check ──
    @app.route("/api/v1/health")
    def health():
        return jsonify({
            "status": "healthy",
            "service": "evently-api",
            "version": app.config.get("APP_VERSION", "1.0.0"),
        }), 200

    # ── SPA Static File Serving (monolithic mode) ──
    # Activated by SERVE_STATIC=1 env var. Flask serves the built React
    # app for all non-API routes so a single process handles everything.
    if os.environ.get("SERVE_STATIC") == "1":
        if os.path.isdir(_FRONTEND_DIST):
            @app.route("/", defaults={"path": ""})
            @app.route("/<path:path>")
            def serve_spa(path):
                full_path = os.path.join(_FRONTEND_DIST, path)
                if path and os.path.isfile(full_path):
                    return send_from_directory(_FRONTEND_DIST, path)
                return send_from_directory(_FRONTEND_DIST, "index.html")
        else:
            app.logger.warning(
                "SERVE_STATIC=1 but frontend/dist not found. "
                "Run 'npm run build' inside the frontend/ directory first."
            )

    # ── Error Handlers ──
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app
