"""Evently — Extension Instances"""
import os
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()

# Redis is optional — not needed for local FloraFlow development
try:
    import redis as _redis
    redis_client = _redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"),
                                   socket_connect_timeout=2)
    redis_client.ping()
except Exception:
    redis_client = None
