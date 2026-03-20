"""
Evently — Flask Application Factory
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_caching import Cache

from app.config import config_by_name
from app.extensions import db, redis_client, ma


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

    # ── Error Handlers ──
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app
