"""
Evently — Inventory Models
"""
import enum
from app.extensions import db
from app.models.core import gen_uuid, utcnow
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


class ItemStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    retired = "retired"


class SetAsideReason(enum.Enum):
    damaged = "damaged"
    missing = "missing"
    maintenance = "maintenance"
    dirty = "dirty"
    hold = "hold"


class ScanAction(enum.Enum):
    check_out = "check_out"
    check_in = "check_in"
    audit = "audit"
    damage_report = "damage_report"


# ── Inventory Pool (for alternates) ──

class InventoryPool(db.Model):
    __tablename__ = "inventory_pools"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=False), db.ForeignKey("companies.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    items = db.relationship("InventoryItem", backref="pool", lazy="dynamic")


# ── Inventory Item ──

class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=False), db.ForeignKey("companies.id"), nullable=False, index=True)
    pool_id = db.Column(UUID(as_uuid=False), db.ForeignKey("inventory_pools.id"), nullable=True)

    name = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    description_ecommerce = db.Column(db.Text)
    category = db.Column(db.String(100), index=True)
    subcategory = db.Column(db.String(100))

    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_quantity = db.Column(db.Integer, nullable=False, default=1)
    available_quantity = db.Column(db.Integer, nullable=False, default=1)

    tags = db.Column(ARRAY(db.String), default=list)
    attributes = db.Column(JSONB, default=dict)  # color, size, material, etc.
    custom_columns = db.Column(JSONB, default=dict)

    purchase_price = db.Column(db.Numeric(10, 2))
    purchase_location = db.Column(db.String(200))
    purchase_date = db.Column(db.Date)

    status = db.Column(db.Enum(ItemStatus, name="item_status"), default=ItemStatus.active)
    buffer_minutes = db.Column(db.Integer, default=0)  # Conflict buffer time

    # Stats (denormalized for performance)
    total_revenue = db.Column(db.Numeric(12, 2), default=0)
    total_bookings = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    photos = db.relationship("ItemPhoto", backref="item", lazy="dynamic", order_by="ItemPhoto.sort_order")
    barcodes = db.relationship("Barcode", backref="item", lazy="dynamic")
    set_asides = db.relationship("SetAside", backref="item", lazy="dynamic")
    line_items = db.relationship("ProjectLineItem", backref="inventory_item", lazy="dynamic")

    # Indexes for conflict detection
    __table_args__ = (
        db.Index("ix_inventory_company_category", "company_id", "category"),
        db.Index("ix_inventory_company_status", "company_id", "status"),
    )

    def __repr__(self):
        return f"<InventoryItem {self.name} (qty:{self.total_quantity})>"

    @property
    def utilization_pct(self):
        if self.total_quantity == 0:
            return 0
        return round((self.total_quantity - self.available_quantity) / self.total_quantity * 100, 1)

    @property
    def is_low_stock(self):
        if self.total_quantity == 0:
            return True
        return (self.available_quantity / self.total_quantity) < 0.2

    @property
    def primary_photo_url(self):
        photo = self.photos.filter_by(is_primary=True).first()
        return photo.url if photo else None

    def recalculate_availability(self):
        """Recalculate available quantity from active reservations and set-asides."""
        from app.models.project import ProjectLineItem, Project, ProjectStage
        active_stages = [
            ProjectStage.signed, ProjectStage.deposit_paid,
            ProjectStage.confirmed, ProjectStage.paid_in_full,
        ]
        reserved = db.session.query(
            db.func.coalesce(db.func.sum(ProjectLineItem.quantity), 0)
        ).join(Project).filter(
            ProjectLineItem.item_id == self.id,
            Project.stage.in_(active_stages),
        ).scalar()

        set_aside_qty = db.session.query(
            db.func.coalesce(db.func.sum(SetAside.quantity), 0)
        ).filter(
            SetAside.item_id == self.id,
            SetAside.resolved_at.is_(None),
        ).scalar()

        self.available_quantity = max(0, self.total_quantity - int(reserved) - int(set_aside_qty))


# ── Item Photo ──

class ItemPhoto(db.Model):
    __tablename__ = "item_photos"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    item_id = db.Column(UUID(as_uuid=False), db.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)


# ── Barcode ──

class Barcode(db.Model):
    __tablename__ = "barcodes"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    item_id = db.Column(UUID(as_uuid=False), db.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    barcode_type = db.Column(db.String(20), default="code128")  # code128, qr
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)


# ── Set Aside ──

class SetAside(db.Model):
    __tablename__ = "set_asides"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    item_id = db.Column(UUID(as_uuid=False), db.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    reason = db.Column(db.Enum(SetAsideReason, name="set_aside_reason"), nullable=False)
    notes = db.Column(db.Text)
    resolved_by = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id"), nullable=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)


# ── Scan Log ──

class ScanLog(db.Model):
    __tablename__ = "scan_logs"

    id = db.Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    barcode_id = db.Column(UUID(as_uuid=False), db.ForeignKey("barcodes.id"), nullable=False)
    user_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(UUID(as_uuid=False), db.ForeignKey("projects.id"), nullable=True)
    action = db.Column(db.Enum(ScanAction, name="scan_action"), nullable=False)
    condition_notes = db.Column(db.Text)
    scanned_at = db.Column(db.DateTime(timezone=True), default=utcnow)
