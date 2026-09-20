"""
Evently — Configuration
"""
import os
from datetime import timedelta


class BaseConfig:
    APP_VERSION = "1.0.0"
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 20,
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "max_overflow": 10,
    }

    # JWT
    JWT_SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Redis / Cache
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

    # SendGrid
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@evently.com")

    # S3 / Linode Object Storage
    S3_ENDPOINT = os.getenv("S3_ENDPOINT")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
    S3_BUCKET = os.getenv("S3_BUCKET", "evently-uploads")

    # CORS
    CORS_ORIGINS = os.getenv("FRONTEND_URL", "http://localhost:3000")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://evently:devpassword@postgres:5432/evently"
    )


class ProductionConfig(BaseConfig):
    DEBUG = False

    # PostgreSQL on same host (set DATABASE_URL in .env)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "max_overflow": 5,
    }

    # No Redis — use simple in-process cache for production monolith
    CACHE_TYPE = "SimpleCache"
    CACHE_REDIS_URL = None

    # Monolith: Flask serves React dist/ when SERVE_STATIC=1 (set in .env)
    SERVE_STATIC = os.getenv("SERVE_STATIC", "1") == "1"

    # Cookie security
    JWT_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # CORS — same origin in production (nginx handles everything on one domain)
    CORS_ORIGINS = os.getenv("FRONTEND_URL", "")


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class LocalConfig(BaseConfig):
    """SQLite-based config for local FloraFlow development — no PostgreSQL or Redis needed."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///floraflow_local.db"
    SQLALCHEMY_ENGINE_OPTIONS = {}  # SQLite doesn't use connection pooling
    CACHE_TYPE = "SimpleCache"
    CACHE_REDIS_URL = None
    # Dev mode origins (Vite dev server); ignored when serving as monolith (same origin)
    CORS_ORIGINS = ["http://localhost:5173", "http://localhost:5001"]


config_by_name = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
    "local":       LocalConfig,
}
