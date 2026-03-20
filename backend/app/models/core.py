"""
Evently — Core Models: Company, User, Client
"""
import uuid
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy import String, Enum as PgEnum
import enum


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


# ── Enums ──

class UserRole(enum.Enum):
    admin = "admin"
    full = "full"
    limited = "limited"
    readonly = "readonly"


# ── Company ──

class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = db.Column(db.String(200), nullable=False)
    logo_url = db.Column(db.String(500))
    website_url = db.Column(db.String(500))
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    timezone = db.Column(db.String(50), default="UTC")
    branding_config = db.Column(JSONB, default=dict)
    stripe_account_id = db.Column(db.String(100))
    quickbooks_realm_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    # Relationships
    users = db.relationship("User", backref="company", lazy="dynamic")
    clients = db.relationship("Client", backref="company", lazy="dynamic")
    inventory_items = db.relationship("InventoryItem", backref="company", lazy="dynamic")
    projects = db.relationship("Project", backref="company", lazy="dynamic")
    vehicles = db.relationship("Vehicle", backref="company", lazy="dynamic")

    def __repr__(self):
        return f"<Company {self.name}>"


# ── User ──

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=False), db.ForeignKey("companies.id"), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    role = db.Column(PgEnum(UserRole, name="user_role"), default=UserRole.full)
    phone = db.Column(db.String(30))
    avatar_url = db.Column(db.String(500))
    permissions = db.Column(JSONB, default=dict)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    # Relationships
    created_projects = db.relationship("Project", backref="created_by_user", foreign_keys="Project.created_by")
    activity_logs = db.relationship("ActivityLog", backref="user", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def is_admin(self):
        return self.role == UserRole.admin

    @property
    def can_create_proposals(self):
        return self.role in (UserRole.admin, UserRole.full)


# ── Client ──

class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=False), db.ForeignKey("companies.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), index=True)
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    tags = db.Column(ARRAY(db.String), default=list)
    preferences = db.Column(JSONB, default=dict)
    saved_terms = db.Column(JSONB, default=dict)
    notes = db.Column(db.Text)
    total_spent = db.Column(db.Numeric(12, 2), default=0)
    event_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    projects = db.relationship("Project", backref="client", lazy="dynamic")
    payments = db.relationship("Payment", backref="client", lazy="dynamic")
    messages = db.relationship("Message", backref="client", lazy="dynamic")

    def __repr__(self):
        return f"<Client {self.name}>"

    def update_stats(self):
        """Recalculate total_spent and event_count from projects."""
        from app.models.project import Project, ProjectStage
        completed = self.projects.filter(
            Project.stage.in_([ProjectStage.completed, ProjectStage.paid_in_full])
        ).all()
        self.event_count = len(completed)
        self.total_spent = sum(p.total for p in completed)
