"""EventFlow Pro — API v1 Blueprint"""
from flask import Blueprint

api_v1_bp = Blueprint("api_v1", __name__)

# Import routes to register them
# from app.api.v1 import auth, inventory, projects, proposals
# from app.api.v1 import payments, clients, dispatch, calendar
# from app.api.v1 import reports, website, barcoding
