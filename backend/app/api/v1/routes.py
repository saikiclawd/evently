"""
Evently — Clients, Payments, Dispatch & Reports APIs
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.extensions import db
from app.models import (
    Client, Payment, PaymentSchedule, PaymentMethod, PaymentStatus,
    Vehicle, Route, RouteStop, RouteAssignment, PullSheet,
    Project, ProjectStage, InventoryItem, WebsiteWishlist, Message,
    User, ActivityLog,
)
from app.schemas import (
    ClientSchema, ClientCreateSchema, PaymentSchema, PaymentScheduleSchema,
    VehicleSchema, RouteSchema, CreateRouteSchema, PullSheetSchema,
    MessageSchema, SendMessageSchema, ActivityLogSchema,
    WebsiteWishlistSchema, WishlistSubmitSchema,
    DashboardStatsSchema, CreatePaymentIntentSchema,
)
from app.api.v1.inventory import get_current_company_id


# ════════════════════════════════════════
# CLIENTS (CRM)
# ════════════════════════════════════════

@api_v1_bp.route("/clients", methods=["GET"])
@jwt_required()
def list_clients():
    company_id = get_current_company_id()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)
    search = request.args.get("search", "").strip()
    tag = request.args.get("tag")

    query = Client.query.filter_by(company_id=company_id)
    if search:
        query = query.filter(
            db.or_(Client.name.ilike(f"%{search}%"), Client.email.ilike(f"%{search}%"))
        )
    if tag:
        query = query.filter(Client.tags.any(tag))

    query = query.order_by(Client.name)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "clients": ClientSchema(many=True).dump(pagination.items),
        "total": pagination.total, "page": page, "pages": pagination.pages,
    })


@api_v1_bp.route("/clients/<client_id>", methods=["GET"])
@jwt_required()
def get_client(client_id):
    company_id = get_current_company_id()
    client = Client.query.filter_by(id=client_id, company_id=company_id).first_or_404()
    return jsonify(ClientSchema().dump(client))


@api_v1_bp.route("/clients", methods=["POST"])
@jwt_required()
def create_client():
    errors = ClientCreateSchema().validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    company_id = get_current_company_id()
    data = request.json
    client = Client(company_id=company_id, **{k: data[k] for k in data if hasattr(Client, k)})
    db.session.add(client)
    db.session.commit()
    return jsonify(ClientSchema().dump(client)), 201


@api_v1_bp.route("/clients/<client_id>", methods=["PATCH"])
@jwt_required()
def update_client(client_id):
    company_id = get_current_company_id()
    client = Client.query.filter_by(id=client_id, company_id=company_id).first_or_404()
    data = request.json
    for key in ["name", "email", "phone", "address", "tags", "preferences", "saved_terms", "notes"]:
        if key in data:
            setattr(client, key, data[key])
    db.session.commit()
    return jsonify(ClientSchema().dump(client))


# ════════════════════════════════════════
# PAYMENTS
# ════════════════════════════════════════

@api_v1_bp.route("/payments", methods=["GET"])
@jwt_required()
def list_payments():
    company_id = get_current_company_id()
    project_id = request.args.get("project_id")
    status = request.args.get("status")

    query = Payment.query.join(Project).filter(Project.company_id == company_id)
    if project_id:
        query = query.filter(Payment.project_id == project_id)
    if status:
        query = query.filter(Payment.status == PaymentStatus(status))

    payments = query.order_by(Payment.created_at.desc()).all()
    return jsonify(PaymentSchema(many=True).dump(payments))


@api_v1_bp.route("/payments/create-intent", methods=["POST"])
@jwt_required()
def create_payment_intent():
    """Create a Stripe payment intent for a project."""
    errors = CreatePaymentIntentSchema().validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    data = request.json
    company_id = get_current_company_id()
    project = Project.query.filter_by(id=data["project_id"], company_id=company_id).first_or_404()

    from app.services.payment_processor import create_stripe_payment_intent
    result = create_stripe_payment_intent(project, data["amount"], data["method"])

    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@api_v1_bp.route("/webhooks/stripe", methods=["POST"])
def stripe_webhook():
    """Handle Stripe webhook events."""
    from app.services.payment_processor import handle_stripe_webhook
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")
    result = handle_stripe_webhook(payload, sig_header)

    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@api_v1_bp.route("/projects/<project_id>/payment-schedule", methods=["GET"])
@jwt_required()
def get_payment_schedule(project_id):
    company_id = get_current_company_id()
    project = Project.query.filter_by(id=project_id, company_id=company_id).first_or_404()
    schedules = project.payment_schedules.all()
    return jsonify(PaymentScheduleSchema(many=True).dump(schedules))


# ════════════════════════════════════════
# DISPATCH
# ════════════════════════════════════════

@api_v1_bp.route("/vehicles", methods=["GET"])
@jwt_required()
def list_vehicles():
    company_id = get_current_company_id()
    vehicles = Vehicle.query.filter_by(company_id=company_id, is_active=True).all()
    return jsonify(VehicleSchema(many=True).dump(vehicles))


@api_v1_bp.route("/vehicles", methods=["POST"])
@jwt_required()
def create_vehicle():
    company_id = get_current_company_id()
    data = request.json
    vehicle = Vehicle(company_id=company_id, **{k: data[k] for k in data if hasattr(Vehicle, k)})
    db.session.add(vehicle)
    db.session.commit()
    return jsonify(VehicleSchema().dump(vehicle)), 201


@api_v1_bp.route("/routes", methods=["GET"])
@jwt_required()
def list_routes():
    company_id = get_current_company_id()
    date = request.args.get("date")
    query = Route.query.filter_by(company_id=company_id)
    if date:
        query = query.filter_by(route_date=date)
    routes = query.order_by(Route.route_date.asc()).all()
    return jsonify(RouteSchema(many=True).dump(routes))


@api_v1_bp.route("/routes", methods=["POST"])
@jwt_required()
def create_route():
    company_id = get_current_company_id()
    data = request.json

    route = Route(
        company_id=company_id,
        vehicle_id=data.get("vehicle_id"),
        route_date=data["route_date"],
    )
    db.session.add(route)
    db.session.flush()

    for i, stop_data in enumerate(data.get("stops", [])):
        stop = RouteStop(
            route_id=route.id,
            project_id=stop_data.get("project_id"),
            stop_order=i,
            stop_type=stop_data.get("stop_type", "delivery"),
            venue_name=stop_data.get("venue_name"),
            address=stop_data.get("address"),
            lat=stop_data.get("lat"),
            lng=stop_data.get("lng"),
            arrival_time=stop_data.get("arrival_time"),
            duration_minutes=stop_data.get("duration_minutes", 30),
            notes=stop_data.get("notes"),
        )
        db.session.add(stop)

    route.total_stops = len(data.get("stops", []))
    db.session.commit()
    return jsonify(RouteSchema().dump(route)), 201


@api_v1_bp.route("/routes/<route_id>/auto-route", methods=["POST"])
@jwt_required()
def auto_route(route_id):
    """AI-powered route optimization."""
    company_id = get_current_company_id()
    route = Route.query.filter_by(id=route_id, company_id=company_id).first_or_404()

    from app.services.route_optimizer import optimize_route
    result = optimize_route(route)
    db.session.commit()
    return jsonify(result)


@api_v1_bp.route("/routes/<route_id>/stops/<stop_id>/complete", methods=["POST"])
@jwt_required()
def complete_stop(route_id, stop_id):
    company_id = get_current_company_id()
    route = Route.query.filter_by(id=route_id, company_id=company_id).first_or_404()
    stop = RouteStop.query.filter_by(id=stop_id, route_id=route.id).first_or_404()

    from app.models.core import utcnow
    from app.models.operations import StopStatus
    stop.status = StopStatus.completed
    stop.completed_at = utcnow()
    db.session.commit()
    return jsonify({"message": "Stop marked complete"})


# ════════════════════════════════════════
# MESSAGES
# ════════════════════════════════════════

@api_v1_bp.route("/messages", methods=["GET"])
@jwt_required()
def list_messages():
    company_id = get_current_company_id()
    client_id = request.args.get("client_id")
    project_id = request.args.get("project_id")

    query = Message.query.join(Client).filter(Client.company_id == company_id)
    if client_id:
        query = query.filter(Message.client_id == client_id)
    if project_id:
        query = query.filter(Message.project_id == project_id)

    messages = query.order_by(Message.sent_at.desc()).limit(50).all()
    return jsonify(MessageSchema(many=True).dump(messages))


@api_v1_bp.route("/messages", methods=["POST"])
@jwt_required()
def send_message():
    errors = SendMessageSchema().validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    user_id = get_jwt_identity()
    data = request.json
    from app.models.operations import MessageDirection, MessageChannel

    message = Message(
        client_id=data["client_id"],
        project_id=data.get("project_id"),
        user_id=user_id,
        direction=MessageDirection.outbound,
        channel=MessageChannel.email,
        subject=data.get("subject"),
        body=data["body"],
    )
    db.session.add(message)
    db.session.commit()

    # Send via email asynchronously
    from app.tasks.email_tasks import send_client_email
    send_client_email.delay(message.id)

    return jsonify(MessageSchema().dump(message)), 201


# ════════════════════════════════════════
# WEBSITE INTEGRATION
# ════════════════════════════════════════

@api_v1_bp.route("/website/<company_id>/inventory", methods=["GET"])
def public_inventory(company_id):
    """Public endpoint: inventory feed for website integration."""
    items = InventoryItem.query.filter_by(
        company_id=company_id, status=InventoryItem.status.default.arg
    ).order_by(InventoryItem.category, InventoryItem.name).all()

    return jsonify([{
        "id": i.id, "name": i.name, "description": i.description_ecommerce or i.description,
        "category": i.category, "price": float(i.price),
        "available": i.available_quantity > 0, "tags": i.tags,
        "photo_url": i.primary_photo_url,
    } for i in items])


@api_v1_bp.route("/website/<company_id>/wishlist", methods=["POST"])
def submit_wishlist(company_id):
    """Public endpoint: wishlist submission from website widget."""
    errors = WishlistSubmitSchema().validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    data = request.json
    wishlist = WebsiteWishlist(company_id=company_id, **{k: data[k] for k in data})
    db.session.add(wishlist)
    db.session.commit()
    return jsonify({"message": "Wishlist submitted", "id": wishlist.id}), 201


@api_v1_bp.route("/wishlists", methods=["GET"])
@jwt_required()
def list_wishlists():
    company_id = get_current_company_id()
    status = request.args.get("status")
    query = WebsiteWishlist.query.filter_by(company_id=company_id)
    if status:
        query = query.filter_by(status=status)
    wishlists = query.order_by(WebsiteWishlist.submitted_at.desc()).all()
    return jsonify(WebsiteWishlistSchema(many=True).dump(wishlists))


# ════════════════════════════════════════
# DASHBOARD & REPORTS
# ════════════════════════════════════════

@api_v1_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    company_id = get_current_company_id()
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Monthly revenue
    monthly_revenue = db.session.query(
        db.func.coalesce(db.func.sum(Payment.amount), 0)
    ).join(Project).filter(
        Project.company_id == company_id,
        Payment.status == PaymentStatus.succeeded,
        Payment.paid_at >= month_start,
    ).scalar()

    # Active projects
    active_projects = Project.query.filter(
        Project.company_id == company_id,
        Project.stage.in_([
            ProjectStage.signed, ProjectStage.deposit_paid,
            ProjectStage.confirmed, ProjectStage.paid_in_full,
        ]),
    ).count()

    # Items rented (reserved across active projects)
    from app.models import ProjectLineItem
    items_rented = db.session.query(
        db.func.coalesce(db.func.sum(ProjectLineItem.quantity), 0)
    ).join(Project).filter(
        Project.company_id == company_id,
        Project.stage.in_([ProjectStage.confirmed, ProjectStage.paid_in_full]),
    ).scalar()

    # Proposals sent this month
    proposals_sent = Project.query.filter(
        Project.company_id == company_id,
        Project.stage != ProjectStage.draft,
        Project.created_at >= month_start,
    ).count()

    # Upcoming events (next 30 days)
    upcoming = Project.query.filter(
        Project.company_id == company_id,
        Project.stage.in_([ProjectStage.confirmed, ProjectStage.deposit_paid, ProjectStage.signed]),
        Project.event_start >= now,
        Project.event_start <= now + timedelta(days=30),
    ).order_by(Project.event_start).limit(5).all()

    # Low stock items
    low_stock = InventoryItem.query.filter(
        InventoryItem.company_id == company_id,
        InventoryItem.available_quantity < InventoryItem.total_quantity * 0.2,
        InventoryItem.total_quantity > 0,
    ).limit(5).all()

    # Top revenue items
    top_items = InventoryItem.query.filter_by(company_id=company_id).order_by(
        InventoryItem.total_revenue.desc()
    ).limit(5).all()

    return jsonify({
        "monthly_revenue": float(monthly_revenue),
        "active_projects": active_projects,
        "items_rented": int(items_rented),
        "proposals_sent": proposals_sent,
        "upcoming_events": [{
            "id": p.id, "event_name": p.event_name, "client": p.client.name if p.client else "",
            "venue": p.venue_name, "date": p.event_start.isoformat(),
            "stage": p.stage.value, "total": float(p.total or 0),
        } for p in upcoming],
        "inventory_alerts": [{
            "id": i.id, "name": i.name, "available": i.available_quantity,
            "total": i.total_quantity, "category": i.category,
        } for i in low_stock],
        "top_performers": [{
            "id": i.id, "name": i.name, "revenue": float(i.total_revenue or 0),
            "bookings": i.total_bookings, "category": i.category,
        } for i in top_items],
    })


@api_v1_bp.route("/reports/revenue", methods=["GET"])
@jwt_required()
def revenue_report():
    company_id = get_current_company_id()
    from datetime import datetime, timezone
    year = request.args.get("year", datetime.now(timezone.utc).year, type=int)

    monthly = db.session.query(
        db.func.extract("month", Payment.paid_at).label("month"),
        db.func.sum(Payment.amount).label("revenue"),
    ).join(Project).filter(
        Project.company_id == company_id,
        Payment.status == PaymentStatus.succeeded,
        db.func.extract("year", Payment.paid_at) == year,
    ).group_by("month").order_by("month").all()

    return jsonify({
        "year": year,
        "monthly": [{"month": int(m.month), "revenue": float(m.revenue)} for m in monthly],
    })


@api_v1_bp.route("/reports/pipeline", methods=["GET"])
@jwt_required()
def pipeline_report():
    company_id = get_current_company_id()
    stages = db.session.query(
        Project.stage,
        db.func.count(Project.id).label("count"),
        db.func.sum(Project.total).label("value"),
    ).filter_by(company_id=company_id).group_by(Project.stage).all()

    return jsonify([{
        "stage": s.stage.value,
        "count": s.count,
        "value": float(s.value or 0),
    } for s in stages])


@api_v1_bp.route("/activity", methods=["GET"])
@jwt_required()
def list_activity():
    company_id = get_current_company_id()
    project_id = request.args.get("project_id")
    query = ActivityLog.query.filter_by(company_id=company_id)
    if project_id:
        query = query.filter_by(project_id=project_id)
    logs = query.order_by(ActivityLog.created_at.desc()).limit(50).all()
    return jsonify(ActivityLogSchema(many=True).dump(logs))
