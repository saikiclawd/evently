"""Evently — Extension Instances"""
import os
import redis
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
