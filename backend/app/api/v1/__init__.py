"""Evently — API v1 Blueprint"""
from flask import Blueprint

api_v1_bp = Blueprint("api_v1", __name__)

# Import routes to register them with the blueprint
from app.api.v1 import auth        # noqa: E402, F401
from app.api.v1 import inventory   # noqa: E402, F401
from app.api.v1 import projects    # noqa: E402, F401
from app.api.v1 import routes      # noqa: E402, F401
