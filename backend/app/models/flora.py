"""
FloraFlow — Floral Intelligence Models
All table names prefixed `flora_` to avoid conflicts with existing Evently tables.
Uses standard SQLAlchemy types (String/JSON) for SQLite + PostgreSQL compatibility.
"""
import uuid
import math
from datetime import datetime, timezone
from app.extensions import db
import enum


def gen_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


# ── Enums ──────────────────────────────────────────────────

class RecipeCategory(enum.Enum):
    centerpiece      = "centerpiece"
    head_table       = "head_table"
    ceremony         = "ceremony"
    chuppah          = "chuppah"
    runner           = "runner"
    arch_full        = "arch_full"
    arch_half        = "arch_half"
    bouquet_bridal   = "bouquet_bridal"
    bouquet_bm       = "bouquet_bm"
    boutonniere      = "boutonniere"
    hanging          = "hanging"
    stage            = "stage"
    backdrop         = "backdrop"
    ceiling          = "ceiling"
    aisle            = "aisle"
    sweetheart       = "sweetheart"
    cake             = "cake"
    welcome          = "welcome"
    other            = "other"


class RecipeStatus(enum.Enum):
    draft     = "draft"
    published = "published"
    archived  = "archived"


class EventType(enum.Enum):
    wedding      = "wedding"
    corporate    = "corporate"
    gala         = "gala"
    bar_mitzvah  = "bar_mitzvah"
    birthday     = "birthday"
    other        = "other"


class EventStatus(enum.Enum):
    inquiry        = "inquiry"
    proposal_sent  = "proposal_sent"
    confirmed      = "confirmed"
    in_production  = "in_production"
    completed      = "completed"
    cancelled      = "cancelled"


class POStatus(enum.Enum):
    draft     = "draft"
    sent      = "sent"
    confirmed = "confirmed"
    received  = "received"
    partial   = "partial"
    cancelled = "cancelled"


class TransactionType(enum.Enum):
    received = "received"
    consumed = "consumed"
    adjusted = "adjusted"
    wasted   = "wasted"


class PaymentType(enum.Enum):
    deposit = "deposit"
    balance = "balance"
    refund  = "refund"


# Category → default buffer percentage (replaces flat 10%)
CATEGORY_BUFFER_DEFAULTS = {
    RecipeCategory.chuppah:       15.0,
    RecipeCategory.arch_full:     15.0,
    RecipeCategory.arch_half:     15.0,
    RecipeCategory.ceiling:       15.0,
    RecipeCategory.hanging:       15.0,
    RecipeCategory.backdrop:      12.0,
    RecipeCategory.stage:         12.0,
    RecipeCategory.centerpiece:   10.0,
    RecipeCategory.head_table:    10.0,
    RecipeCategory.runner:        10.0,
    RecipeCategory.sweetheart:    10.0,
    RecipeCategory.ceremony:      10.0,
    RecipeCategory.bouquet_bridal: 8.0,
    RecipeCategory.bouquet_bm:     8.0,
    RecipeCategory.aisle:          8.0,
    RecipeCategory.welcome:        8.0,
    RecipeCategory.boutonniere:    5.0,
    RecipeCategory.cake:           5.0,
    RecipeCategory.other:         10.0,
}


# ── Flower Catalog ──────────────────────────────────────────

class Flower(db.Model):
    __tablename__ = "flora_flowers"

    id                 = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    company_id         = db.Column(db.String(36), db.ForeignKey("companies.id"), nullable=False, index=True)
    common_name        = db.Column(db.String(150), nullable=False)
    variety            = db.Column(db.String(150))
    color              = db.Column(db.String(100))
    default_buffer_pct = db.Column(db.Numeric(5, 2), default=10.0)
    bunch_size         = db.Column(db.Integer, default=10)
    cost_per_stem      = db.Column(db.Numeric(8, 4), default=0)
    season_notes       = db.Column(db.Text)
    season_months      = db.Column(db.JSON, default=list)  # [1,2,3,...12]
    photo_url          = db.Column(db.String(500))
    is_active          = db.Column(db.Boolean, default=True)
    created_at         = db.Column(db.DateTime, default=utcnow)
    updated_at         = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    vendor_preferences = db.relationship("VendorFlowerPreference", backref="flower", lazy="dynamic")
    recipe_stems       = db.relationship("RecipeStem", backref="flower", lazy="dynamic")

    def to_dict(self):
        return {
            "id":                 self.id,
            "common_name":        self.common_name,
            "variety":            self.variety,
            "color":              self.color,
            "default_buffer_pct": float(self.default_buffer_pct or 10),
            "bunch_size":         self.bunch_size,
            "cost_per_stem":      float(self.cost_per_stem or 0),
            "season_notes":       self.season_notes,
            "season_months":      self.season_months or [],
            "photo_url":          self.photo_url,
            "is_active":          self.is_active,
            "display_name":       f"{self.common_name}{' – ' + self.variety if self.variety else ''}{' (' + self.color + ')' if self.color else ''}",
        }


# ── Vendors ─────────────────────────────────────────────────

class Vendor(db.Model):
    __tablename__ = "flora_vendors"

    id              = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    company_id      = db.Column(db.String(36), db.ForeignKey("companies.id"), nullable=False, index=True)
    name            = db.Column(db.String(200), nullable=False)
    contact_name    = db.Column(db.String(200))
    email           = db.Column(db.String(255))
    phone           = db.Column(db.String(30))
    min_order_value = db.Column(db.Numeric(10, 2), default=0)
    lead_days       = db.Column(db.Integer, default=3)
    notes           = db.Column(db.Text)
    is_active       = db.Column(db.Boolean, default=True)
    created_at      = db.Column(db.DateTime, default=utcnow)

    flower_prefs    = db.relationship("VendorFlowerPreference", backref="vendor", lazy="dynamic", cascade="all, delete-orphan")
    purchase_orders = db.relationship("PurchaseOrder", backref="vendor", lazy="dynamic")

    def to_dict(self):
        return {
            "id":              self.id,
            "name":            self.name,
            "contact_name":    self.contact_name,
            "email":           self.email,
            "phone":           self.phone,
            "min_order_value": float(self.min_order_value or 0),
            "lead_days":       self.lead_days,
            "notes":           self.notes,
            "is_active":       self.is_active,
        }


class VendorFlowerPreference(db.Model):
    __tablename__ = "flora_vendor_flower_prefs"

    id                   = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    vendor_id            = db.Column(db.String(36), db.ForeignKey("flora_vendors.id"), nullable=False)
    flower_id            = db.Column(db.String(36), db.ForeignKey("flora_flowers.id"), nullable=False)
    priority_rank        = db.Column(db.Integer, default=1)  # 1=primary, 2=backup
    typical_unit_price   = db.Column(db.Numeric(8, 4))
    bunch_size_override  = db.Column(db.Integer)
    min_fill_rate        = db.Column(db.Numeric(5, 2), default=80.0)

    def to_dict(self):
        return {
            "id":                  self.id,
            "vendor_id":           self.vendor_id,
            "flower_id":           self.flower_id,
            "flower_name":         self.flower.display_name if self.flower else None,
            "priority_rank":       self.priority_rank,
            "typical_unit_price":  float(self.typical_unit_price or 0),
            "bunch_size_override": self.bunch_size_override,
            "min_fill_rate":       float(self.min_fill_rate or 80),
        }


# ── Recipes ─────────────────────────────────────────────────

class Recipe(db.Model):
    __tablename__ = "flora_recipes"

    id                 = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    company_id         = db.Column(db.String(36), db.ForeignKey("companies.id"), nullable=False, index=True)
    name               = db.Column(db.String(255), nullable=False)
    category           = db.Column(db.String(50), default="other")
    status             = db.Column(db.String(20), default="draft")
    current_version_id = db.Column(db.String(36), nullable=True)
    photo_url          = db.Column(db.String(500))
    tags               = db.Column(db.JSON, default=list)
    labor_minutes      = db.Column(db.Integer, default=0)
    markup_pct         = db.Column(db.Numeric(5, 2), default=20.0)
    is_public          = db.Column(db.Boolean, default=True)
    created_by         = db.Column(db.String(36), db.ForeignKey("users.id"))
    created_at         = db.Column(db.DateTime, default=utcnow)
    updated_at         = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    versions = db.relationship("RecipeVersion", backref="recipe", lazy="dynamic",
                               foreign_keys="RecipeVersion.recipe_id",
                               cascade="all, delete-orphan")

    @property
    def current_version(self):
        if self.current_version_id:
            return RecipeVersion.query.get(self.current_version_id)
        return self.versions.order_by(RecipeVersion.version_number.desc()).first()

    @property
    def category_buffer_pct(self):
        try:
            cat = RecipeCategory(self.category)
            return CATEGORY_BUFFER_DEFAULTS.get(cat, 10.0)
        except ValueError:
            return 10.0

    def to_dict(self, include_stems=False):
        cv = self.current_version
        d = {
            "id":                  self.id,
            "name":                self.name,
            "category":            self.category,
            "status":              self.status,
            "tags":                self.tags or [],
            "labor_minutes":       self.labor_minutes,
            "markup_pct":          float(self.markup_pct or 20),
            "is_public":           self.is_public,
            "photo_url":           self.photo_url,
            "category_buffer_pct": self.category_buffer_pct,
            "current_version_id":  self.current_version_id,
            "total_stems":         cv.total_stems if cv else 0,
            "cost_per_unit":       float(cv.cost_per_unit) if cv else 0,
            "version_number":      cv.version_number if cv else 0,
            "created_at":          self.created_at.isoformat() if self.created_at else None,
            "updated_at":          self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_stems and cv:
            d["stems"] = [s.to_dict() for s in cv.stems]
        return d


class RecipeVersion(db.Model):
    __tablename__ = "flora_recipe_versions"

    id             = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    recipe_id      = db.Column(db.String(36), db.ForeignKey("flora_recipes.id"), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False, default=1)
    change_summary = db.Column(db.Text)
    total_stems    = db.Column(db.Integer, default=0)
    cost_per_unit  = db.Column(db.Numeric(10, 2), default=0)
    created_by     = db.Column(db.String(36), db.ForeignKey("users.id"))
    created_at     = db.Column(db.DateTime, default=utcnow)

    stems = db.relationship("RecipeStem", backref="version", lazy="select",
                            cascade="all, delete-orphan",
                            foreign_keys="RecipeStem.recipe_version_id")

    def recalculate_totals(self):
        self.total_stems = sum(s.quantity for s in self.stems)
        self.cost_per_unit = sum(
            s.quantity * float(s.unit_cost_override or s.flower.cost_per_stem or 0)
            for s in self.stems
        )

    def to_dict(self):
        return {
            "id":             self.id,
            "recipe_id":      self.recipe_id,
            "version_number": self.version_number,
            "change_summary": self.change_summary,
            "total_stems":    self.total_stems,
            "cost_per_unit":  float(self.cost_per_unit or 0),
            "created_at":     self.created_at.isoformat() if self.created_at else None,
            "stems":          [s.to_dict() for s in self.stems],
        }


class RecipeStem(db.Model):
    __tablename__ = "flora_recipe_stems"

    id                  = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    recipe_version_id   = db.Column(db.String(36), db.ForeignKey("flora_recipe_versions.id"), nullable=False, index=True)
    flower_id           = db.Column(db.String(36), db.ForeignKey("flora_flowers.id"), nullable=False)
    quantity            = db.Column(db.Integer, nullable=False, default=1)
    unit_cost_override  = db.Column(db.Numeric(8, 4))
    buffer_pct_override = db.Column(db.Numeric(5, 2))
    notes               = db.Column(db.Text)
    sort_order          = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id":                  self.id,
            "recipe_version_id":   self.recipe_version_id,
            "flower_id":           self.flower_id,
            "flower_name":         self.flower.common_name if self.flower else None,
            "flower_variety":      self.flower.variety if self.flower else None,
            "flower_color":        self.flower.color if self.flower else None,
            "flower_display":      self.flower.to_dict()["display_name"] if self.flower else None,
            "bunch_size":          self.flower.bunch_size if self.flower else 10,
            "quantity":            self.quantity,
            "unit_cost":           float(self.unit_cost_override or (self.flower.cost_per_stem if self.flower else 0) or 0),
            "unit_cost_override":  float(self.unit_cost_override) if self.unit_cost_override else None,
            "buffer_pct_override": float(self.buffer_pct_override) if self.buffer_pct_override else None,
            "notes":               self.notes,
            "sort_order":          self.sort_order,
            "line_cost":           self.quantity * float(self.unit_cost_override or (self.flower.cost_per_stem if self.flower else 0) or 0),
        }


# ── Events ──────────────────────────────────────────────────

class FloraEvent(db.Model):
    __tablename__ = "flora_events"

    id                 = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    company_id         = db.Column(db.String(36), db.ForeignKey("companies.id"), nullable=False, index=True)
    name               = db.Column(db.String(255), nullable=False)
    event_date         = db.Column(db.Date)
    event_type         = db.Column(db.String(30), default="wedding")
    status             = db.Column(db.String(30), default="inquiry")
    venue              = db.Column(db.String(255))
    quoted_budget      = db.Column(db.Numeric(10, 2), default=0)
    guest_count        = db.Column(db.Integer)
    lead_designer_id   = db.Column(db.String(36), db.ForeignKey("users.id"))
    account_manager_id = db.Column(db.String(36), db.ForeignKey("users.id"))
    style_tags         = db.Column(db.JSON, default=list)
    brief_notes        = db.Column(db.Text)
    locked_at          = db.Column(db.DateTime)
    created_by         = db.Column(db.String(36), db.ForeignKey("users.id"))
    created_at         = db.Column(db.DateTime, default=utcnow)
    updated_at         = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    arrangements = db.relationship("EventArrangement", backref="event", lazy="select",
                                   order_by="EventArrangement.sort_order",
                                   cascade="all, delete-orphan")
    purchase_orders = db.relationship("PurchaseOrder", backref="event", lazy="dynamic")
    payments = db.relationship("EventPayment", backref="event", lazy="dynamic",
                               cascade="all, delete-orphan")

    @property
    def total_paid(self):
        return sum(float(p.amount) for p in self.payments if p.payment_type != "refund") \
             - sum(float(p.amount) for p in self.payments if p.payment_type == "refund")

    def to_dict(self, include_arrangements=False):
        d = {
            "id":                self.id,
            "name":              self.name,
            "event_date":        self.event_date.isoformat() if self.event_date else None,
            "event_type":        self.event_type,
            "status":            self.status,
            "venue":             self.venue,
            "quoted_budget":     float(self.quoted_budget or 0),
            "guest_count":       self.guest_count,
            "lead_designer_id":  self.lead_designer_id,
            "style_tags":        self.style_tags or [],
            "brief_notes":       self.brief_notes,
            "total_paid":        self.total_paid,
            "created_at":        self.created_at.isoformat() if self.created_at else None,
        }
        if include_arrangements:
            d["arrangements"] = [a.to_dict() for a in self.arrangements]
        return d


class EventArrangement(db.Model):
    __tablename__ = "flora_event_arrangements"

    id                = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    event_id          = db.Column(db.String(36), db.ForeignKey("flora_events.id"), nullable=False, index=True)
    recipe_id         = db.Column(db.String(36), db.ForeignKey("flora_recipes.id"), nullable=False)
    recipe_version_id = db.Column(db.String(36), db.ForeignKey("flora_recipe_versions.id"))
    quantity          = db.Column(db.Integer, nullable=False, default=1)
    location_note     = db.Column(db.Text)
    is_custom         = db.Column(db.Boolean, default=False)
    sort_order        = db.Column(db.Integer, default=0)

    recipe  = db.relationship("Recipe")
    version = db.relationship("RecipeVersion")
    overrides = db.relationship("EventStemOverride", backref="arrangement",
                                lazy="select", cascade="all, delete-orphan")

    def to_dict(self):
        recipe = self.recipe
        version = self.version or (recipe.current_version if recipe else None)
        return {
            "id":                self.id,
            "event_id":          self.event_id,
            "recipe_id":         self.recipe_id,
            "recipe_version_id": self.recipe_version_id,
            "recipe_name":       recipe.name if recipe else None,
            "recipe_category":   recipe.category if recipe else None,
            "quantity":          self.quantity,
            "location_note":     self.location_note,
            "is_custom":         self.is_custom,
            "sort_order":        self.sort_order,
            "stems_per_unit":    version.total_stems if version else 0,
            "cost_per_unit":     float(version.cost_per_unit) if version else 0,
            "total_stems":       (version.total_stems if version else 0) * self.quantity,
            "total_cost":        float(version.cost_per_unit or 0) * self.quantity if version else 0,
        }


class EventStemOverride(db.Model):
    __tablename__ = "flora_event_stem_overrides"

    id                   = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    event_arrangement_id = db.Column(db.String(36), db.ForeignKey("flora_event_arrangements.id"), nullable=False)
    flower_id            = db.Column(db.String(36), db.ForeignKey("flora_flowers.id"), nullable=False)
    override_quantity    = db.Column(db.Integer, nullable=False)
    reason               = db.Column(db.Text)


class EventPayment(db.Model):
    __tablename__ = "flora_event_payments"

    id           = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    event_id     = db.Column(db.String(36), db.ForeignKey("flora_events.id"), nullable=False, index=True)
    amount       = db.Column(db.Numeric(10, 2), nullable=False)
    payment_type = db.Column(db.String(20), default="deposit")
    payment_date = db.Column(db.Date)
    method       = db.Column(db.String(50))
    notes        = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id":           self.id,
            "event_id":     self.event_id,
            "amount":       float(self.amount),
            "payment_type": self.payment_type,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "method":       self.method,
            "notes":        self.notes,
        }


# ── Purchase Orders ─────────────────────────────────────────

class PurchaseOrder(db.Model):
    __tablename__ = "flora_purchase_orders"

    id               = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    company_id       = db.Column(db.String(36), db.ForeignKey("companies.id"), nullable=False, index=True)
    event_id         = db.Column(db.String(36), db.ForeignKey("flora_events.id"), nullable=False)
    vendor_id        = db.Column(db.String(36), db.ForeignKey("flora_vendors.id"), nullable=False)
    po_number        = db.Column(db.String(50), unique=True)
    status           = db.Column(db.String(20), default="draft")
    required_by_date = db.Column(db.Date)
    total_amount     = db.Column(db.Numeric(10, 2), default=0)
    sent_at          = db.Column(db.DateTime)
    notes            = db.Column(db.Text)
    created_by       = db.Column(db.String(36), db.ForeignKey("users.id"))
    created_at       = db.Column(db.DateTime, default=utcnow)
    updated_at       = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    line_items = db.relationship("POLineItem", backref="purchase_order", lazy="select",
                                 cascade="all, delete-orphan")

    def recalculate_total(self):
        self.total_amount = sum(float(li.line_total or 0) for li in self.line_items)

    def to_dict(self, include_lines=False):
        d = {
            "id":               self.id,
            "event_id":         self.event_id,
            "event_name":       self.event.name if self.event else None,
            "vendor_id":        self.vendor_id,
            "vendor_name":      self.vendor.name if self.vendor else None,
            "po_number":        self.po_number,
            "status":           self.status,
            "required_by_date": self.required_by_date.isoformat() if self.required_by_date else None,
            "total_amount":     float(self.total_amount or 0),
            "sent_at":          self.sent_at.isoformat() if self.sent_at else None,
            "notes":            self.notes,
            "created_at":       self.created_at.isoformat() if self.created_at else None,
            "line_count":       len(self.line_items),
        }
        if include_lines:
            d["line_items"] = [li.to_dict() for li in self.line_items]
        return d


class POLineItem(db.Model):
    __tablename__ = "flora_po_line_items"

    id                   = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    po_id                = db.Column(db.String(36), db.ForeignKey("flora_purchase_orders.id"), nullable=False, index=True)
    flower_id            = db.Column(db.String(36), db.ForeignKey("flora_flowers.id"), nullable=False)
    stems_required       = db.Column(db.Integer, default=0)
    bunches_required     = db.Column(db.Integer, default=0)
    bunch_size           = db.Column(db.Integer, default=10)
    unit_price           = db.Column(db.Numeric(8, 4), default=0)
    line_total           = db.Column(db.Numeric(10, 2), default=0)
    substitution_note    = db.Column(db.Text)
    substitution_status  = db.Column(db.String(20))  # null/pending/approved/rejected

    flower = db.relationship("Flower")

    def to_dict(self):
        return {
            "id":                  self.id,
            "po_id":               self.po_id,
            "flower_id":           self.flower_id,
            "flower_name":         self.flower.to_dict()["display_name"] if self.flower else None,
            "stems_required":      self.stems_required,
            "bunches_required":    self.bunches_required,
            "bunch_size":          self.bunch_size,
            "unit_price":          float(self.unit_price or 0),
            "line_total":          float(self.line_total or 0),
            "substitution_note":   self.substitution_note,
            "substitution_status": self.substitution_status,
        }


# ── Inventory Ledger ─────────────────────────────────────────

class InventoryLedger(db.Model):
    __tablename__ = "flora_inventory_ledger"

    id               = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    company_id       = db.Column(db.String(36), db.ForeignKey("companies.id"), nullable=False, index=True)
    flower_id        = db.Column(db.String(36), db.ForeignKey("flora_flowers.id"), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    quantity_delta   = db.Column(db.Integer, nullable=False)
    reference_id     = db.Column(db.String(36))
    notes            = db.Column(db.Text)
    balance_after    = db.Column(db.Integer, default=0)
    created_by       = db.Column(db.String(36), db.ForeignKey("users.id"))
    created_at       = db.Column(db.DateTime, default=utcnow)

    flower = db.relationship("Flower")

    def to_dict(self):
        return {
            "id":               self.id,
            "flower_id":        self.flower_id,
            "flower_name":      self.flower.to_dict()["display_name"] if self.flower else None,
            "transaction_type": self.transaction_type,
            "quantity_delta":   self.quantity_delta,
            "reference_id":     self.reference_id,
            "notes":            self.notes,
            "balance_after":    self.balance_after,
            "created_at":       self.created_at.isoformat() if self.created_at else None,
        }
