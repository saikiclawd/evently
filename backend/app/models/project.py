"""
Evently — Project & Proposal Models
"""
import enum
import secrets
from app.extensions import db
from app.models.core import gen_uuid, utcnow
from sqlalchemy.dialects.postgresql import UUID, JSONB


class ProjectStage(enum.Enum):
    draft = "draft"
    proposal_sent = "proposal_sent"
    signed = "signed"
    deposit_paid = "deposit_paid"
    confirmed = "confirmed"
    paid_in_full = "paid_in_full"
    completed = "completed"
    cancelled = "cancelled"


def gen_project_number():
    return f"PRJ-{secrets.token_hex(3).upper()}"


def gen_live_link_token():
    return secrets.token_urlsafe(32)


# ── Project ──

class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=False), db.ForeignKey("companies.id"), nullable=False, index=True)
    client_id = db.Column(UUID(as_uuid=False), db.ForeignKey("clients.id"), nullable=False, index=True)
    created_by = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id"), nullable=False)

    project_number = db.Column(db.String(20), unique=True, default=gen_project_number)
    event_name = db.Column(db.String(300), nullable=False)
    event_type = db.Column(db.String(100))  # wedding, corporate, birthday, etc.
    venue_name = db.Column(db.String(300))
    venue_address = db.Column(db.Text)
    venue_lat = db.Column(db.Float)
    venue_lng = db.Column(db.Float)
    venue_notes = db.Column(db.Text)

    event_start = db.Column(db.DateTime(timezone=True), nullable=False)
    event_end = db.Column(db.DateTime(timezone=True), nullable=False)
    setup_start = db.Column(db.DateTime(timezone=True))
    teardown_end = db.Column(db.DateTime(timezone=True))
    buffer_minutes = db.Column(db.Integer, default=60)

    stage = db.Column(db.Enum(ProjectStage, name="project_stage"), default=ProjectStage.draft, index=True)

    # Financials
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    tax_rate = db.Column(db.Numeric(5, 4), default=0)  # e.g., 0.085 for 8.5%
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    delivery_fee = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    amount_paid = db.Column(db.Numeric(12, 2), default=0)

    # Proposal settings
    custom_terms = db.Column(JSONB, default=dict)
    internal_notes = db.Column(db.Text)
    live_link_token = db.Column(db.String(64), unique=True, default=gen_live_link_token)
    quote_expires_at = db.Column(db.DateTime(timezone=True))

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    line_items = db.relationship("ProjectLineItem", backref="project", lazy="dynamic",
                                cascade="all, delete-orphan", order_by="ProjectLineItem.sort_order")
    proposal = db.relationship("Proposal", backref="project", uselist=False, cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="project", lazy="dynamic")
    payment_schedules = db.relationship("PaymentSchedule", backref="project", lazy="dynamic",
                                        order_by="PaymentSchedule.due_date")
    messages = db.relationship("Message", backref="project", lazy="dynamic")
    pull_sheets = db.relationship("PullSheet", backref="project", lazy="dynamic")
    route_stops = db.relationship("RouteStop", backref="project", lazy="dynamic")
    activity_logs = db.relationship("ActivityLog", backref="project", lazy="dynamic")

    __table_args__ = (
        db.Index("ix_project_company_stage", "company_id", "stage"),
        db.Index("ix_project_dates", "event_start", "event_end"),
    )

    def __repr__(self):
        return f"<Project {self.project_number}: {self.event_name}>"

    @property
    def balance_due(self):
        return max(0, float(self.total or 0) - float(self.amount_paid or 0))

    @property
    def is_fully_paid(self):
        return self.amount_paid >= self.total

    @property
    def item_count(self):
        return self.line_items.count()

    def recalculate_totals(self):
        """Recalculate subtotal, tax, and total from line items."""
        items = self.line_items.all()
        self.subtotal = sum(li.subtotal for li in items)
        self.tax_amount = self.subtotal * (self.tax_rate or 0)
        self.total = self.subtotal + self.tax_amount + (self.delivery_fee or 0) - (self.discount_amount or 0)

    def advance_stage(self, new_stage):
        """Advance project to a new stage with validation."""
        valid_transitions = {
            ProjectStage.draft: [ProjectStage.proposal_sent, ProjectStage.cancelled],
            ProjectStage.proposal_sent: [ProjectStage.signed, ProjectStage.draft, ProjectStage.cancelled],
            ProjectStage.signed: [ProjectStage.deposit_paid, ProjectStage.cancelled],
            ProjectStage.deposit_paid: [ProjectStage.confirmed, ProjectStage.cancelled],
            ProjectStage.confirmed: [ProjectStage.paid_in_full, ProjectStage.cancelled],
            ProjectStage.paid_in_full: [ProjectStage.completed],
            ProjectStage.completed: [],
            ProjectStage.cancelled: [ProjectStage.draft],
        }
        if new_stage not in valid_transitions.get(self.stage, []):
            raise ValueError(f"Cannot transition from {self.stage.value} to {new_stage.value}")
        self.stage = new_stage


# ── Project Line Item ──

class ProjectLineItem(db.Model):
    __tablename__ = "project_line_items"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = db.Column(UUID(as_uuid=False), db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    item_id = db.Column(UUID(as_uuid=False), db.ForeignKey("inventory_items.id"), nullable=True)  # null for custom

    name = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    sort_order = db.Column(db.Integer, default=0)

    is_package = db.Column(db.Boolean, default=False)
    package_id = db.Column(UUID(as_uuid=False), nullable=True)  # Group items in a package
    is_taxable = db.Column(db.Boolean, default=True)
    custom_fields = db.Column(JSONB, default=dict)

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def __repr__(self):
        return f"<LineItem {self.name} x{self.quantity}>"

    def calculate_subtotal(self):
        self.subtotal = self.quantity * self.unit_price


# ── Proposal ──

class Proposal(db.Model):
    __tablename__ = "proposals"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = db.Column(UUID(as_uuid=False), db.ForeignKey("projects.id", ondelete="CASCADE"),
                           nullable=False, unique=True)

    pdf_url = db.Column(db.String(500))
    branding_override = db.Column(JSONB, default=dict)
    payment_schedule_config = db.Column(JSONB, default=dict)  # deposit %, balance timing
    signature_required = db.Column(db.Boolean, default=True)
    custom_message = db.Column(db.Text)

    sent_at = db.Column(db.DateTime(timezone=True))
    viewed_at = db.Column(db.DateTime(timezone=True))
    signed_at = db.Column(db.DateTime(timezone=True))
    expires_at = db.Column(db.DateTime(timezone=True))

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    # Relationships
    signatures = db.relationship("Signature", backref="proposal", lazy="dynamic")


# ── Signature ──

class Signature(db.Model):
    __tablename__ = "signatures"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    proposal_id = db.Column(UUID(as_uuid=False), db.ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False)
    signer_name = db.Column(db.String(200), nullable=False)
    signer_email = db.Column(db.String(255), nullable=False)
    signature_image_url = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    provider = db.Column(db.String(50), default="internal")  # docusign, hellosign, internal
    external_id = db.Column(db.String(200))
    signed_at = db.Column(db.DateTime(timezone=True), default=utcnow)
