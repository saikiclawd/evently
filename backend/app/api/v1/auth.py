"""
Evently — Auth API (Local + Google OAuth)
"""
import os
import requests as http_requests
from flask import request, jsonify, redirect, url_for, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity,
)
import bcrypt
from app.api.v1 import api_v1_bp
from app.extensions import db
from app.models import Company, User, UserRole
from app.schemas import UserSchema, UserCreateSchema, LoginSchema
from app.models.core import utcnow


# ════════════════════════════════════════
# Local Auth
# ════════════════════════════════════════

@api_v1_bp.route("/auth/register", methods=["POST"])
def register():
    """Register a new company + admin user."""
    schema = UserCreateSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    data = request.json

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    company = Company(name=data.get("company_name", f"{data['name']}'s Company"))
    db.session.add(company)
    db.session.flush()

    hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
    user = User(
        company_id=company.id,
        email=data["email"],
        password_hash=hashed,
        name=data["name"],
        role=UserRole.admin,
        auth_provider="local",
    )
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "user": UserSchema().dump(user),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }), 201


@api_v1_bp.route("/auth/login", methods=["POST"])
def login():
    """Login with email + password."""
    schema = LoginSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    data = request.json
    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    # If user signed up via Google, tell them to use Google login
    if user.auth_provider == "google" and not user.password_hash:
        return jsonify({"error": "This account uses Google sign-in. Please use the Google button to log in."}), 401

    if not user.password_hash or not bcrypt.checkpw(data["password"].encode(), user.password_hash.encode()):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is disabled"}), 403

    user.last_login = utcnow()
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "user": UserSchema().dump(user),
        "access_token": access_token,
        "refresh_token": refresh_token,
    })


# ════════════════════════════════════════
# Google OAuth
# ════════════════════════════════════════

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@api_v1_bp.route("/auth/google/config", methods=["GET"])
def google_config():
    """Return the Google OAuth client ID for the frontend."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    # Only enable if it's a real client ID (not a placeholder)
    is_valid = (
        bool(client_id)
        and client_id.endswith(".apps.googleusercontent.com")
        and "XXXX" not in client_id
        and len(client_id) > 40
    )
    return jsonify({
        "client_id": client_id if is_valid else "",
        "enabled": is_valid,
    })


@api_v1_bp.route("/auth/google", methods=["POST"])
def google_auth():
    """
    Exchange a Google OAuth authorization code for user tokens.
    Frontend sends: { "code": "...", "redirect_uri": "..." }
    OR sends: { "credential": "..." } for one-tap / ID token flow
    """
    data = request.json or {}

    # ── Flow 1: Google One Tap (ID token / credential) ──
    if "credential" in data:
        google_user = _verify_google_id_token(data["credential"])
        if not google_user:
            return jsonify({"error": "Invalid Google credential"}), 401

    # ── Flow 2: Authorization Code exchange ──
    elif "code" in data:
        google_user = _exchange_google_code(data["code"], data.get("redirect_uri", ""))
        if not google_user:
            return jsonify({"error": "Failed to authenticate with Google"}), 401

    else:
        return jsonify({"error": "Missing 'credential' or 'code' parameter"}), 400

    # ── Find or create user ──
    user = User.query.filter_by(email=google_user["email"]).first()

    if user:
        # Existing user — update Google fields
        if not user.google_id:
            user.google_id = google_user["id"]
            user.auth_provider = "google"
        if google_user.get("picture") and not user.avatar_url:
            user.avatar_url = google_user["picture"]
        user.last_login = utcnow()
        db.session.commit()
    else:
        # New user — create account + company
        company = Company(name=f"{google_user['name']}'s Company")
        db.session.add(company)
        db.session.flush()

        user = User(
            company_id=company.id,
            email=google_user["email"],
            name=google_user.get("name", google_user["email"].split("@")[0]),
            avatar_url=google_user.get("picture"),
            google_id=google_user["id"],
            auth_provider="google",
            role=UserRole.admin,
        )
        db.session.add(user)
        db.session.commit()

    if not user.is_active:
        return jsonify({"error": "Account is disabled"}), 403

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "user": UserSchema().dump(user),
        "access_token": access_token,
        "refresh_token": refresh_token,
    })


def _verify_google_id_token(credential):
    """Verify a Google ID token (from One Tap or Sign In With Google)."""
    try:
        # Method 1: Use Google's tokeninfo endpoint (most reliable)
        resp = http_requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        )
        if resp.status_code != 200:
            return None

        idinfo = resp.json()

        # Verify the token was meant for our app
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        if idinfo.get("aud") != client_id:
            return None

        # Verify email is verified
        if idinfo.get("email_verified") != "true":
            return None

        return {
            "id": idinfo["sub"],
            "email": idinfo["email"],
            "name": idinfo.get("name", idinfo.get("email", "").split("@")[0]),
            "picture": idinfo.get("picture", ""),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None


def _exchange_google_code(code, redirect_uri):
    """Exchange an authorization code for user info."""
    try:
        # Exchange code for tokens
        token_resp = http_requests.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        if token_resp.status_code != 200:
            return None

        access_token = token_resp.json().get("access_token")
        if not access_token:
            return None

        # Get user info
        user_resp = http_requests.get(GOOGLE_USERINFO_URL, headers={
            "Authorization": f"Bearer {access_token}"
        })
        if user_resp.status_code != 200:
            return None

        data = user_resp.json()
        return {
            "id": data["id"],
            "email": data["email"],
            "name": data.get("name", ""),
            "picture": data.get("picture", ""),
        }
    except Exception:
        return None


# ════════════════════════════════════════
# Common
# ════════════════════════════════════════

@api_v1_bp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token})


@api_v1_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def me():
    """Get current user profile."""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(UserSchema().dump(user))
