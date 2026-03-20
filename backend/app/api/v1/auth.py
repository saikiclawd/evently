"""
EventFlow Pro — Auth API
"""
from flask import request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, current_user,
)
import bcrypt
from app.api.v1 import api_v1_bp
from app.extensions import db
from app.models import Company, User, UserRole
from app.schemas import UserSchema, UserCreateSchema, LoginSchema


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

    # Create company
    company = Company(name=data.get("company_name", f"{data['name']}'s Company"))
    db.session.add(company)
    db.session.flush()

    # Create admin user
    hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
    user = User(
        company_id=company.id,
        email=data["email"],
        password_hash=hashed,
        name=data["name"],
        role=UserRole.admin,
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
    """Login and get JWT tokens."""
    schema = LoginSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    data = request.json
    user = User.query.filter_by(email=data["email"]).first()

    if not user or not bcrypt.checkpw(data["password"].encode(), user.password_hash.encode()):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is disabled"}), 403

    from app.models.core import utcnow
    user.last_login = utcnow()
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "user": UserSchema().dump(user),
        "access_token": access_token,
        "refresh_token": refresh_token,
    })


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
