"""
EventFlow Pro — Payment Models
"""
import enum
from app.extensions import db
from app.models.core import gen_uuid, utcnow
from sqlalchemy.dialects.postgresql import UUID, JSONB


class PaymentMethod(enum.Enum):
    credit_card = "credit_card"
    debit_card = "debit_card"
    ach = "ach"
    google_pay = "google_pay"
    bnpl = "bnpl"
    cash = "cash"
    check = "check"


class PaymentStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"
    refunded = "refunded"
    partially_refunded = "partially_refunded"


class SyncStatus(enum.Enum):
    synced = "synced"
    pending = "pending"
    error = "error"


# ── Payment ──

class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = db.Column(UUID(as_uuid=False), db.ForeignKey("projects.id"), nullable=False, index=True)
    client_id = db.Column(UUID(as_uuid=False), db.ForeignKey("clients.id"), nullable=False)
    schedule_id = db.Column(UUID(as_uuid=False), db.ForeignKey("payment_schedules.id"), nullable=True)

    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(db.Enum(PaymentMethod, name="payment_method"), nullable=False)
    status = db.Column(db.Enum(PaymentStatus, name="payment_status"), default=PaymentStatus.pending)

    # Stripe fields
    stripe_payment_intent_id = db.Column(db.String(200), index=True)
    stripe_charge_id = db.Column(db.String(200))
    stripe_refund_id = db.Column(db.String(200))

    # Processing details
    card_last_four = db.Column(db.String(4))
    card_brand = db.Column(db.String(20))
    processing_fee = db.Column(db.Numeric(10, 2), default=0)
    net_amount = db.Column(db.Numeric(12, 2))
    payment_metadata = db.Column(JSONB, default=dict)

    due_date = db.Column(db.DateTime(timezone=True))
    paid_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def __repr__(self):
        return f"<Payment ${self.amount} ({self.status.value})>"


# ── Payment Schedule ──

class PaymentSchedule(db.Model):
    __tablename__ = "payment_schedules"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = db.Column(UUID(as_uuid=False), db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    label = db.Column(db.String(100), nullable=False)  # "Deposit 50%", "Balance"
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    due_date = db.Column(db.DateTime(timezone=True), nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_sent_at = db.Column(db.DateTime(timezone=True))
    payment_id = db.Column(UUID(as_uuid=False), nullable=True)  # Linked when paid

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)


# ── QuickBooks Sync ──

class QuickBooksSync(db.Model):
    __tablename__ = "quickbooks_syncs"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=False), db.ForeignKey("companies.id"), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)  # invoice, payment, customer
    entity_id = db.Column(UUID(as_uuid=False), nullable=False)
    qb_id = db.Column(db.String(100))
    status = db.Column(db.Enum(SyncStatus, name="sync_status"), default=SyncStatus.pending)
    error_details = db.Column(JSONB, default=dict)
    last_synced_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        db.Index("ix_qb_sync_entity", "entity_type", "entity_id"),
    )
