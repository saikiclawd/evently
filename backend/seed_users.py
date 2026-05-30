#!/usr/bin/env python3
"""
Seed script — creates test company + two UAT users.
Run from /opt/evently/backend:
  set -a; source /opt/evently/.env; set +a
  python3 seed_users.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from app.models.core import Company, User, UserRole
import bcrypt, uuid

app = create_app()

COMPANY_NAME = "Luxel Decor & Flowers"

USERS = [
    {
        "email": "admin@floraflow.test",
        "password": "Flora2026!",
        "name": "Admin User",
        "role": UserRole.admin,
    },
    {
        "email": "staff@floraflow.test",
        "password": "Flora2026!",
        "name": "Staff User",
        "role": UserRole.full,
    },
]

with app.app_context():
    # Find or create the company
    company = Company.query.filter_by(name=COMPANY_NAME).first()
    if not company:
        company = Company(
            id=str(uuid.uuid4()),
            name=COMPANY_NAME,
            timezone="UTC",
        )
        db.session.add(company)
        db.session.flush()
        print(f"Created company: {COMPANY_NAME}")
    else:
        print(f"Using existing company: {COMPANY_NAME}")

    for u in USERS:
        existing = User.query.filter_by(email=u["email"]).first()
        if existing:
            print(f"User already exists: {u['email']} — skipping")
            continue

        pw_hash = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt()).decode()
        user = User(
            id=str(uuid.uuid4()),
            company_id=company.id,
            email=u["email"],
            password_hash=pw_hash,
            name=u["name"],
            role=u["role"],
            is_active=True,
            auth_provider="local",
        )
        db.session.add(user)
        print(f"Created user: {u['email']}  password: {u['password']}  role: {u['role'].value}")

    db.session.commit()
    print("\nDone.")
