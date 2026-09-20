"""
Evently — Marshmallow Schemas
"""
from app.extensions import ma
from app.models import (
    Company, User, Client, InventoryItem, ItemPhoto,
    Project, ProjectLineItem, Proposal,
    Payment, PaymentSchedule,
    Vehicle, Route, RouteStop, RouteAssignment, PullSheet,
    Message, ActivityLog, WebsiteWishlist,
    Contact, Note, Task, TaskStatus,
)
from marshmallow import fields, validate, pre_load, post_dump


# ════════════════════════════════════════
# Core Schemas
# ════════════════════════════════════════

class CompanySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Company
        load_instance = True
        exclude = ("stripe_account_id", "quickbooks_realm_id")


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = ("password_hash", "google_id")

    role = fields.String()
    auth_provider = fields.String(dump_only=True)
    company = ma.Nested(CompanySchema, dump_only=True, only=("id", "name"))


class UserCreateSchema(ma.Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))
    name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    role = fields.String(validate=validate.OneOf(["admin", "full", "limited", "readonly"]))


class LoginSchema(ma.Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)


class ContactSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Contact
        load_instance = True
        include_fk = True


class ContactCreateSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    role = fields.String()
    email = fields.Email(allow_none=True)
    phone = fields.String()
    is_primary = fields.Boolean()


class NoteSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Note
        load_instance = True
        include_fk = True

    author = ma.Nested(lambda: UserSchema, dump_only=True, only=("id", "name"))


class NoteCreateSchema(ma.Schema):
    body = fields.String(required=True, validate=validate.Length(min=1))
    project_id = fields.String(allow_none=True)
    is_pinned = fields.Boolean()


class TaskSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        load_instance = True
        include_fk = True

    status = fields.Method("_get_status", dump_only=True)
    priority = fields.Method("_get_priority", dump_only=True)
    assignee = ma.Nested(lambda: UserSchema, dump_only=True, only=("id", "name"))

    def _get_status(self, obj):
        return obj.status.value if obj.status else None

    def _get_priority(self, obj):
        return obj.priority.value if obj.priority else None


class TaskCreateSchema(ma.Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=300))
    description = fields.String()
    due_date = fields.DateTime(allow_none=True)
    priority = fields.String(validate=validate.OneOf(["low", "medium", "high"]))
    assignee_id = fields.String(allow_none=True)
    project_id = fields.String(allow_none=True)


class TaskUpdateSchema(ma.Schema):
    title = fields.String(validate=validate.Length(min=1, max=300))
    description = fields.String()
    due_date = fields.DateTime(allow_none=True)
    status = fields.String(validate=validate.OneOf(["todo", "in_progress", "done"]))
    priority = fields.String(validate=validate.OneOf(["low", "medium", "high"]))
    assignee_id = fields.String(allow_none=True)


class ClientSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Client
        load_instance = True
        include_fk = True

    event_count = fields.Integer(dump_only=True)
    total_spent = fields.Float(dump_only=True)
    lifecycle_stage = fields.String()
    owner = ma.Nested(lambda: UserSchema, dump_only=True, only=("id", "name"))
    contact_count = fields.Method("_get_contact_count", dump_only=True)
    open_task_count = fields.Method("_get_open_task_count", dump_only=True)

    def _get_contact_count(self, obj):
        return obj.contacts.count()

    def _get_open_task_count(self, obj):
        return obj.crm_tasks.filter(Task.status != TaskStatus.done).count()


class ClientCreateSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    email = fields.Email()
    phone = fields.String()
    address = fields.String()
    website = fields.String()
    tags = fields.List(fields.String())
    notes = fields.String()
    lifecycle_stage = fields.String(validate=validate.OneOf(
        ["lead", "qualified", "active", "past_client", "lost"]))
    lead_source = fields.String()
    owner_id = fields.String(allow_none=True)


# ════════════════════════════════════════
# Inventory Schemas
# ════════════════════════════════════════

class ItemPhotoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ItemPhoto
        load_instance = True


class InventoryItemSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = InventoryItem
        load_instance = True
        include_fk = True

    photos = ma.Nested(ItemPhotoSchema, many=True, dump_only=True)
    utilization_pct = fields.Float(dump_only=True)
    is_low_stock = fields.Boolean(dump_only=True)
    primary_photo_url = fields.String(dump_only=True)


class InventoryItemCreateSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=300))
    description = fields.String()
    category = fields.String(required=True)
    price = fields.Float(required=True, validate=validate.Range(min=0))
    total_quantity = fields.Integer(required=True, validate=validate.Range(min=0))
    tags = fields.List(fields.String())
    attributes = fields.Dict()
    buffer_minutes = fields.Integer(validate=validate.Range(min=0))


class InventoryItemUpdateSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=1, max=300))
    description = fields.String()
    category = fields.String()
    price = fields.Float(validate=validate.Range(min=0))
    total_quantity = fields.Integer(validate=validate.Range(min=0))
    tags = fields.List(fields.String())
    attributes = fields.Dict()
    status = fields.String(validate=validate.OneOf(["active", "inactive", "retired"]))
    buffer_minutes = fields.Integer(validate=validate.Range(min=0))


# ════════════════════════════════════════
# Project Schemas
# ════════════════════════════════════════

class ProjectLineItemSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ProjectLineItem
        load_instance = True
        include_fk = True


class ProjectSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Project
        load_instance = True
        include_fk = True
        exclude = ("live_link_token",)

    line_items = ma.Nested(ProjectLineItemSchema, many=True, dump_only=True)
    client = ma.Nested(ClientSchema, dump_only=True, only=("id", "name", "email"))
    balance_due = fields.Float(dump_only=True)
    is_fully_paid = fields.Boolean(dump_only=True)
    item_count = fields.Integer(dump_only=True)
    stage = fields.String()


class ProjectCreateSchema(ma.Schema):
    client_id = fields.String(required=True)
    event_name = fields.String(required=True, validate=validate.Length(min=1, max=300))
    event_type = fields.String()
    venue_name = fields.String()
    venue_address = fields.String()
    event_start = fields.DateTime(required=True)
    event_end = fields.DateTime(required=True)
    tax_rate = fields.Float(validate=validate.Range(min=0, max=1))
    delivery_fee = fields.Float(validate=validate.Range(min=0))
    internal_notes = fields.String()


class AddLineItemSchema(ma.Schema):
    item_id = fields.String()  # Null for custom line items
    name = fields.String(required=True)
    description = fields.String()
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    unit_price = fields.Float(required=True, validate=validate.Range(min=0))
    is_taxable = fields.Boolean(load_default=True)


class ProposalSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Proposal
        load_instance = True
        include_fk = True


# ════════════════════════════════════════
# Payment Schemas
# ════════════════════════════════════════

class PaymentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Payment
        load_instance = True
        include_fk = True
        exclude = ("stripe_payment_intent_id", "stripe_charge_id", "stripe_refund_id")

    method = fields.String()
    status = fields.String()


class PaymentScheduleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PaymentSchedule
        load_instance = True
        include_fk = True


class CreatePaymentIntentSchema(ma.Schema):
    project_id = fields.String(required=True)
    amount = fields.Float(required=True, validate=validate.Range(min=0.50))
    method = fields.String(required=True, validate=validate.OneOf([
        "credit_card", "debit_card", "ach", "google_pay", "bnpl",
    ]))


# ════════════════════════════════════════
# Dispatch Schemas
# ════════════════════════════════════════

class VehicleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Vehicle
        load_instance = True
        include_fk = True


class RouteStopSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = RouteStop
        load_instance = True
        include_fk = True

    stop_type = fields.String()
    status = fields.String()


class RouteAssignmentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = RouteAssignment
        load_instance = True
        include_fk = True

    user = ma.Nested(UserSchema, dump_only=True, only=("id", "name"))
    role = fields.String()


class RouteSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Route
        load_instance = True
        include_fk = True

    stops = ma.Nested(RouteStopSchema, many=True, dump_only=True)
    crew = ma.Nested(RouteAssignmentSchema, many=True, dump_only=True)
    vehicle = ma.Nested(VehicleSchema, dump_only=True, only=("id", "name", "vehicle_type"))
    status = fields.String()


class CreateRouteSchema(ma.Schema):
    vehicle_id = fields.String()
    route_date = fields.Date(required=True)
    stops = fields.List(fields.Dict(), required=True)


class PullSheetSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PullSheet
        load_instance = True
        include_fk = True

    status = fields.String()


# ════════════════════════════════════════
# Communication Schemas
# ════════════════════════════════════════

class MessageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Message
        load_instance = True
        include_fk = True

    direction = fields.String()
    channel = fields.String()


class SendMessageSchema(ma.Schema):
    client_id = fields.String(required=True)
    project_id = fields.String()
    subject = fields.String()
    body = fields.String(required=True)


class ActivityLogSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ActivityLog
        load_instance = True
        include_fk = True

    user = ma.Nested(UserSchema, dump_only=True, only=("id", "name"))


class WebsiteWishlistSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WebsiteWishlist
        load_instance = True
        include_fk = True


class WishlistSubmitSchema(ma.Schema):
    visitor_name = fields.String(required=True)
    visitor_email = fields.Email(required=True)
    visitor_phone = fields.String()
    event_date = fields.Date()
    event_type = fields.String()
    venue = fields.String()
    notes = fields.String()
    items = fields.List(fields.Dict(), required=True)  # [{item_id, quantity}]


# ════════════════════════════════════════
# Dashboard / Report Schemas
# ════════════════════════════════════════

class DashboardStatsSchema(ma.Schema):
    monthly_revenue = fields.Float()
    active_projects = fields.Integer()
    items_rented = fields.Integer()
    proposals_sent = fields.Integer()
    revenue_change_pct = fields.Float()
    upcoming_events = fields.List(fields.Dict())
    inventory_alerts = fields.List(fields.Dict())
    payment_status = fields.List(fields.Dict())
    top_performers = fields.List(fields.Dict())


class ReportFiltersSchema(ma.Schema):
    start_date = fields.Date()
    end_date = fields.Date()
    category = fields.String()
    stage = fields.String()
