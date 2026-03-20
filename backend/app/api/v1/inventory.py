"""
EventFlow Pro — Inventory API
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.extensions import db
from app.models import InventoryItem, ItemPhoto, User, ItemStatus
from app.schemas import (
    InventoryItemSchema, InventoryItemCreateSchema, InventoryItemUpdateSchema,
)


def get_current_company_id():
    user = User.query.get(get_jwt_identity())
    return user.company_id


# ── List / Search Inventory ──

@api_v1_bp.route("/inventory", methods=["GET"])
@jwt_required()
def list_inventory():
    company_id = get_current_company_id()

    # Query params
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)
    search = request.args.get("search", "").strip()
    category = request.args.get("category")
    status = request.args.get("status")
    tag = request.args.get("tag")
    sort_by = request.args.get("sort_by", "name")
    sort_dir = request.args.get("sort_dir", "asc")
    low_stock = request.args.get("low_stock", type=bool)

    query = InventoryItem.query.filter_by(company_id=company_id)

    # Filters
    if search:
        query = query.filter(
            db.or_(
                InventoryItem.name.ilike(f"%{search}%"),
                InventoryItem.category.ilike(f"%{search}%"),
                InventoryItem.tags.any(search.lower()),
            )
        )
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=ItemStatus(status))
    if tag:
        query = query.filter(InventoryItem.tags.any(tag))
    if low_stock:
        query = query.filter(
            InventoryItem.available_quantity < InventoryItem.total_quantity * 0.2
        )

    # Sorting
    sort_column = getattr(InventoryItem, sort_by, InventoryItem.name)
    if sort_dir == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": InventoryItemSchema(many=True).dump(pagination.items),
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    })


# ── Get Single Item ──

@api_v1_bp.route("/inventory/<item_id>", methods=["GET"])
@jwt_required()
def get_inventory_item(item_id):
    company_id = get_current_company_id()
    item = InventoryItem.query.filter_by(id=item_id, company_id=company_id).first_or_404()
    return jsonify(InventoryItemSchema().dump(item))


# ── Create Item ──

@api_v1_bp.route("/inventory", methods=["POST"])
@jwt_required()
def create_inventory_item():
    schema = InventoryItemCreateSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    company_id = get_current_company_id()
    data = request.json

    item = InventoryItem(
        company_id=company_id,
        name=data["name"],
        description=data.get("description"),
        category=data["category"],
        price=data["price"],
        total_quantity=data["total_quantity"],
        available_quantity=data["total_quantity"],
        tags=data.get("tags", []),
        attributes=data.get("attributes", {}),
        buffer_minutes=data.get("buffer_minutes", 0),
    )
    db.session.add(item)
    db.session.commit()

    return jsonify(InventoryItemSchema().dump(item)), 201


# ── Update Item ──

@api_v1_bp.route("/inventory/<item_id>", methods=["PATCH"])
@jwt_required()
def update_inventory_item(item_id):
    company_id = get_current_company_id()
    item = InventoryItem.query.filter_by(id=item_id, company_id=company_id).first_or_404()

    schema = InventoryItemUpdateSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    data = request.json
    for key, value in data.items():
        if key == "status":
            value = ItemStatus(value)
        if hasattr(item, key):
            setattr(item, key, value)

    if "total_quantity" in data:
        item.recalculate_availability()

    db.session.commit()
    return jsonify(InventoryItemSchema().dump(item))


# ── Delete Item ──

@api_v1_bp.route("/inventory/<item_id>", methods=["DELETE"])
@jwt_required()
def delete_inventory_item(item_id):
    company_id = get_current_company_id()
    item = InventoryItem.query.filter_by(id=item_id, company_id=company_id).first_or_404()

    # Soft delete: mark as retired instead of hard delete
    item.status = ItemStatus.retired
    db.session.commit()
    return jsonify({"message": "Item retired"}), 200


# ── Get Categories ──

@api_v1_bp.route("/inventory/categories", methods=["GET"])
@jwt_required()
def list_categories():
    company_id = get_current_company_id()
    categories = db.session.query(InventoryItem.category).filter_by(
        company_id=company_id
    ).distinct().order_by(InventoryItem.category).all()
    return jsonify([c[0] for c in categories if c[0]])


# ── Check Availability ──

@api_v1_bp.route("/inventory/<item_id>/availability", methods=["GET"])
@jwt_required()
def check_availability(item_id):
    """Check item availability for a date range."""
    company_id = get_current_company_id()
    item = InventoryItem.query.filter_by(id=item_id, company_id=company_id).first_or_404()

    start = request.args.get("start")
    end = request.args.get("end")
    quantity = request.args.get("quantity", 1, type=int)

    if not start or not end:
        return jsonify({"error": "start and end date params required"}), 400

    from app.services.conflict_engine import check_item_availability
    result = check_item_availability(item, start, end, quantity)

    return jsonify(result)
