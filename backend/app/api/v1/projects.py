"""
EventFlow Pro — Projects API
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.extensions import db
from app.models import Project, ProjectLineItem, Proposal, ProjectStage, User, InventoryItem
from app.schemas import (
    ProjectSchema, ProjectCreateSchema, AddLineItemSchema,
    ProjectLineItemSchema, ProposalSchema,
)
from app.api.v1.inventory import get_current_company_id


@api_v1_bp.route("/projects", methods=["GET"])
@jwt_required()
def list_projects():
    company_id = get_current_company_id()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)
    stage = request.args.get("stage")
    search = request.args.get("search", "").strip()

    query = Project.query.filter_by(company_id=company_id)

    if stage:
        query = query.filter_by(stage=ProjectStage(stage))
    if search:
        query = query.filter(
            db.or_(
                Project.event_name.ilike(f"%{search}%"),
                Project.project_number.ilike(f"%{search}%"),
                Project.venue_name.ilike(f"%{search}%"),
            )
        )

    query = query.order_by(Project.event_start.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "projects": ProjectSchema(many=True).dump(pagination.items),
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    })


@api_v1_bp.route("/projects/<project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    company_id = get_current_company_id()
    project = Project.query.filter_by(id=project_id, company_id=company_id).first_or_404()
    return jsonify(ProjectSchema().dump(project))


@api_v1_bp.route("/projects", methods=["POST"])
@jwt_required()
def create_project():
    schema = ProjectCreateSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    user_id = get_jwt_identity()
    company_id = get_current_company_id()
    data = request.json

    project = Project(
        company_id=company_id,
        client_id=data["client_id"],
        created_by=user_id,
        event_name=data["event_name"],
        event_type=data.get("event_type"),
        venue_name=data.get("venue_name"),
        venue_address=data.get("venue_address"),
        event_start=data["event_start"],
        event_end=data["event_end"],
        tax_rate=data.get("tax_rate", 0),
        delivery_fee=data.get("delivery_fee", 0),
        internal_notes=data.get("internal_notes"),
    )
    db.session.add(project)
    db.session.commit()
    return jsonify(ProjectSchema().dump(project)), 201


@api_v1_bp.route("/projects/<project_id>", methods=["PATCH"])
@jwt_required()
def update_project(project_id):
    company_id = get_current_company_id()
    project = Project.query.filter_by(id=project_id, company_id=company_id).first_or_404()
    data = request.json

    updatable = [
        "event_name", "event_type", "venue_name", "venue_address",
        "venue_lat", "venue_lng", "event_start", "event_end",
        "tax_rate", "delivery_fee", "discount_amount", "internal_notes",
        "custom_terms", "quote_expires_at",
    ]
    for key in updatable:
        if key in data:
            setattr(project, key, data[key])

    project.recalculate_totals()
    db.session.commit()
    return jsonify(ProjectSchema().dump(project))


# ── Stage Management ──

@api_v1_bp.route("/projects/<project_id>/stage", methods=["POST"])
@jwt_required()
def change_stage(project_id):
    company_id = get_current_company_id()
    project = Project.query.filter_by(id=project_id, company_id=company_id).first_or_404()
    new_stage = request.json.get("stage")

    if not new_stage:
        return jsonify({"error": "stage is required"}), 400

    try:
        project.advance_stage(ProjectStage(new_stage))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    db.session.commit()
    return jsonify(ProjectSchema().dump(project))


# ── Line Items ──

@api_v1_bp.route("/projects/<project_id>/items", methods=["POST"])
@jwt_required()
def add_line_item(project_id):
    company_id = get_current_company_id()
    project = Project.query.filter_by(id=project_id, company_id=company_id).first_or_404()

    schema = AddLineItemSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    data = request.json

    # If linking to inventory, check availability
    if data.get("item_id"):
        from app.services.conflict_engine import check_item_availability
        item = InventoryItem.query.get(data["item_id"])
        if item:
            avail = check_item_availability(
                item,
                str(project.event_start),
                str(project.event_end),
                data["quantity"],
            )
            if not avail["available"]:
                return jsonify({
                    "error": "Inventory conflict detected",
                    "conflict": avail,
                }), 409

    max_order = db.session.query(db.func.max(ProjectLineItem.sort_order)).filter_by(
        project_id=project.id
    ).scalar() or 0

    line_item = ProjectLineItem(
        project_id=project.id,
        item_id=data.get("item_id"),
        name=data["name"],
        description=data.get("description"),
        quantity=data["quantity"],
        unit_price=data["unit_price"],
        subtotal=data["quantity"] * data["unit_price"],
        sort_order=max_order + 1,
        is_taxable=data.get("is_taxable", True),
    )
    db.session.add(line_item)
    project.recalculate_totals()
    db.session.commit()

    return jsonify(ProjectLineItemSchema().dump(line_item)), 201


@api_v1_bp.route("/projects/<project_id>/items/<item_id>", methods=["DELETE"])
@jwt_required()
def remove_line_item(project_id, item_id):
    company_id = get_current_company_id()
    project = Project.query.filter_by(id=project_id, company_id=company_id).first_or_404()
    line_item = ProjectLineItem.query.filter_by(id=item_id, project_id=project.id).first_or_404()

    db.session.delete(line_item)
    project.recalculate_totals()
    db.session.commit()
    return jsonify({"message": "Line item removed"})


# ── Reorder Line Items ──

@api_v1_bp.route("/projects/<project_id>/items/reorder", methods=["POST"])
@jwt_required()
def reorder_line_items(project_id):
    company_id = get_current_company_id()
    project = Project.query.filter_by(id=project_id, company_id=company_id).first_or_404()
    item_ids = request.json.get("item_ids", [])

    for i, lid in enumerate(item_ids):
        li = ProjectLineItem.query.filter_by(id=lid, project_id=project.id).first()
        if li:
            li.sort_order = i

    db.session.commit()
    return jsonify({"message": "Reordered"})


# ── Public Live Link (no auth) ──

@api_v1_bp.route("/proposals/live/<token>", methods=["GET"])
def get_live_proposal(token):
    """Public endpoint for clients to view their proposal via live link."""
    project = Project.query.filter_by(live_link_token=token).first_or_404()

    # Mark as viewed
    if project.proposal and not project.proposal.viewed_at:
        from app.models.core import utcnow
        project.proposal.viewed_at = utcnow()
        db.session.commit()

    return jsonify({
        "event_name": project.event_name,
        "venue_name": project.venue_name,
        "event_start": project.event_start.isoformat() if project.event_start else None,
        "event_end": project.event_end.isoformat() if project.event_end else None,
        "line_items": ProjectLineItemSchema(many=True).dump(project.line_items.all()),
        "subtotal": float(project.subtotal or 0),
        "tax_amount": float(project.tax_amount or 0),
        "delivery_fee": float(project.delivery_fee or 0),
        "total": float(project.total or 0),
        "amount_paid": float(project.amount_paid or 0),
        "balance_due": project.balance_due,
        "stage": project.stage.value,
        "custom_terms": project.custom_terms,
    })
