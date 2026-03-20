"""
EventFlow Pro — Dispatch & Operations Models
"""
import enum
from app.extensions import db
from app.models.core import gen_uuid, utcnow
from sqlalchemy.dialects.postgresql import UUID, JSONB


class RouteStatus(enum.Enum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"


class StopType(enum.Enum):
    delivery = "delivery"
    pickup = "pickup"
    setup = "setup"
    teardown = "teardown"
    custom = "custom"


class StopStatus(enum.Enum):
    scheduled = "scheduled"
    en_route = "en_route"
    arrived = "arrived"
    completed = "completed"
    skipped = "skipped"


class CrewRole(enum.Enum):
    driver = "driver"
    helper = "helper"
    installer = "installer"


class PullSheetStatus(enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class MessageDirection(enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class MessageChannel(enum.Enum):
    email = "email"
    internal = "internal"
    system = "system"


# ── Vehicle ──

class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=False), db.ForeignKey("companies.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    vehicle_type = db.Column(db.String(50))  # truck, van, trailer
    license_plate = db.Column(db.String(20))
    capacity_cubic_ft = db.Column(db.Integer)
    max_weight_lbs = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    routes = db.relationship("Route", backref="vehicle", lazy="dynamic")


# ── Route ──

class Route(db.Model):
    __tablename__ = "routes"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=False), db.ForeignKey("companies.id"), nullable=False, index=True)
    vehicle_id = db.Column(UUID(as_uuid=False), db.ForeignKey("vehicles.id"), nullable=True)

    route_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.Enum(RouteStatus, name="route_status"), default=RouteStatus.planned)

    total_stops = db.Column(db.Integer, default=0)
    total_drive_minutes = db.Column(db.Integer, default=0)
    total_distance_miles = db.Column(db.Float, default=0)
    optimized_order = db.Column(JSONB, default=list)

    # Default dispatch settings
    warehouse_start_time = db.Column(db.Time)
    warehouse_duration_minutes = db.Column(db.Integer, default=30)
    shift_max_hours = db.Column(db.Float, default=10)

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    stops = db.relationship("RouteStop", backref="route", lazy="dynamic",
                           cascade="all, delete-orphan", order_by="RouteStop.stop_order")
    crew = db.relationship("RouteAssignment", backref="route", lazy="dynamic",
                          cascade="all, delete-orphan")


# ── Route Stop ──

class RouteStop(db.Model):
    __tablename__ = "route_stops"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    route_id = db.Column(UUID(as_uuid=False), db.ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    project_id = db.Column(UUID(as_uuid=False), db.ForeignKey("projects.id"), nullable=True)

    stop_order = db.Column(db.Integer, nullable=False, default=0)
    stop_type = db.Column(db.Enum(StopType, name="stop_type"), nullable=False)
    status = db.Column(db.Enum(StopStatus, name="stop_status"), default=StopStatus.scheduled)

    venue_name = db.Column(db.String(300))
    address = db.Column(db.Text)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

    arrival_time = db.Column(db.Time)
    duration_minutes = db.Column(db.Integer, default=30)
    drive_minutes_from_prev = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)

    completed_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        db.Index("ix_route_stop_order", "route_id", "stop_order"),
    )


# ── Route Crew Assignment ──

class RouteAssignment(db.Model):
    __tablename__ = "route_assignments"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    route_id = db.Column(UUID(as_uuid=False), db.ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.Enum(CrewRole, name="crew_role"), nullable=False)
    notified = db.Column(db.Boolean, default=False)
    notified_at = db.Column(db.DateTime(timezone=True))


# ── Pull Sheet ──

class PullSheet(db.Model):
    __tablename__ = "pull_sheets"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = db.Column(UUID(as_uuid=False), db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(db.Enum(PullSheetStatus, name="pull_sheet_status"), default=PullSheetStatus.pending)
    items_checklist = db.Column(JSONB, default=list)
    pdf_url = db.Column(db.String(500))
    xlsx_url = db.Column(db.String(500))
    completed_by = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id"), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)


# ── Message Center ──

class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = db.Column(UUID(as_uuid=False), db.ForeignKey("projects.id"), nullable=True)
    client_id = db.Column(UUID(as_uuid=False), db.ForeignKey("clients.id"), nullable=False)
    user_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id"), nullable=True)

    direction = db.Column(db.Enum(MessageDirection, name="message_direction"), nullable=False)
    channel = db.Column(db.Enum(MessageChannel, name="message_channel"), default=MessageChannel.email)
    subject = db.Column(db.String(500))
    body = db.Column(db.Text, nullable=False)
    attachments = db.Column(JSONB, default=list)

    is_read = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        db.Index("ix_message_client_project", "client_id", "project_id"),
    )


# ── Email Template ──

class EmailTemplate(db.Model):
    __tablename__ = "email_templates"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=False), db.ForeignKey("companies.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    subject_template = db.Column(db.String(500), nullable=False)
    body_template = db.Column(db.Text, nullable=False)
    trigger_type = db.Column(db.String(50))  # manual, payment_reminder, proposal_sent, etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)


# ── Activity Log ──

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=False), db.ForeignKey("companies.id"), nullable=False)
    user_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id"), nullable=True)
    project_id = db.Column(UUID(as_uuid=False), db.ForeignKey("projects.id"), nullable=True)

    entity_type = db.Column(db.String(50), nullable=False)  # project, inventory, payment, etc.
    entity_id = db.Column(UUID(as_uuid=False), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # created, updated, stage_changed, etc.
    changes = db.Column(JSONB, default=dict)
    ip_address = db.Column(db.String(45))

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, index=True)

    __table_args__ = (
        db.Index("ix_activity_entity", "entity_type", "entity_id"),
    )


# ── Website Wishlist ──

class WebsiteWishlist(db.Model):
    __tablename__ = "website_wishlists"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=False), db.ForeignKey("companies.id"), nullable=False)

    visitor_name = db.Column(db.String(200), nullable=False)
    visitor_email = db.Column(db.String(255), nullable=False)
    visitor_phone = db.Column(db.String(30))
    event_date = db.Column(db.Date)
    event_type = db.Column(db.String(100))
    venue = db.Column(db.String(300))
    notes = db.Column(db.Text)

    items = db.Column(JSONB, default=list)  # [{item_id, quantity}]
    status = db.Column(db.String(20), default="new")  # new, reviewed, converted, rejected
    converted_project_id = db.Column(UUID(as_uuid=False), db.ForeignKey("projects.id"), nullable=True)

    submitted_at = db.Column(db.DateTime(timezone=True), default=utcnow)
