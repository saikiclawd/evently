"""
FloraFlow — API Routes
All routes prefixed /api/v1/flora/
"""
import os
import json
import base64
from datetime import date, datetime, timedelta
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1 import api_v1_bp
from app.extensions import db
from app.models.core import User
from app.models.flora import (
    Flower, Vendor, VendorFlowerPreference,
    Recipe, RecipeVersion, RecipeStem,
    FloraEvent, EventArrangement, EventStemOverride, EventPayment,
    PurchaseOrder, POLineItem, InventoryLedger,
)
from app.services.stem_calculator import (
    calculate_event_summary, aggregate_event_stems, build_po_line_items
)


def get_company_id():
    uid = get_jwt_identity()
    user = User.query.get(uid)
    return user.company_id if user else None


def _next_po_number(company_id):
    year = datetime.now().year
    count = PurchaseOrder.query.filter_by(company_id=company_id).count()
    return f"FLW-{year}-{str(count + 1).zfill(4)}"


def _err(msg, code=400):
    return jsonify({"error": msg}), code


# ══════════════════════════════════════════════
# FLOWER CATALOG
# ══════════════════════════════════════════════

@api_v1_bp.route("/flora/flowers", methods=["GET"])
@jwt_required()
def list_flowers():
    company_id = get_company_id()
    q = Flower.query.filter_by(company_id=company_id)
    if request.args.get("active_only") == "true":
        q = q.filter_by(is_active=True)
    search = request.args.get("q")
    if search:
        q = q.filter(
            db.or_(
                Flower.common_name.ilike(f"%{search}%"),
                Flower.variety.ilike(f"%{search}%"),
            )
        )
    flowers = q.order_by(Flower.common_name).all()
    return jsonify([f.to_dict() for f in flowers])


@api_v1_bp.route("/flora/flowers", methods=["POST"])
@jwt_required()
def create_flower():
    company_id = get_company_id()
    data = request.get_json()
    if not data.get("common_name"):
        return _err("common_name is required")
    flower = Flower(
        company_id         = company_id,
        common_name        = data["common_name"],
        variety            = data.get("variety"),
        color              = data.get("color"),
        default_buffer_pct = data.get("default_buffer_pct", 10.0),
        bunch_size         = data.get("bunch_size", 10),
        cost_per_stem      = data.get("cost_per_stem", 0),
        season_notes       = data.get("season_notes"),
        season_months      = data.get("season_months", []),
    )
    db.session.add(flower)
    db.session.commit()
    return jsonify(flower.to_dict()), 201


@api_v1_bp.route("/flora/flowers/<fid>", methods=["GET"])
@jwt_required()
def get_flower(fid):
    company_id = get_company_id()
    flower = Flower.query.filter_by(id=fid, company_id=company_id).first_or_404()
    return jsonify(flower.to_dict())


@api_v1_bp.route("/flora/flowers/<fid>", methods=["PUT"])
@jwt_required()
def update_flower(fid):
    company_id = get_company_id()
    flower = Flower.query.filter_by(id=fid, company_id=company_id).first_or_404()
    data = request.get_json()
    for field in ["common_name", "variety", "color", "default_buffer_pct",
                  "bunch_size", "cost_per_stem", "season_notes", "season_months", "is_active"]:
        if field in data:
            setattr(flower, field, data[field])
    db.session.commit()
    return jsonify(flower.to_dict())


@api_v1_bp.route("/flora/flowers/<fid>", methods=["DELETE"])
@jwt_required()
def delete_flower(fid):
    company_id = get_company_id()
    flower = Flower.query.filter_by(id=fid, company_id=company_id).first_or_404()
    flower.is_active = False
    db.session.commit()
    return jsonify({"deleted": True})


# ══════════════════════════════════════════════
# VENDORS
# ══════════════════════════════════════════════

@api_v1_bp.route("/flora/vendors", methods=["GET"])
@jwt_required()
def list_vendors():
    company_id = get_company_id()
    vendors = Vendor.query.filter_by(company_id=company_id, is_active=True)\
                          .order_by(Vendor.name).all()
    return jsonify([v.to_dict() for v in vendors])


@api_v1_bp.route("/flora/vendors", methods=["POST"])
@jwt_required()
def create_vendor():
    company_id = get_company_id()
    data = request.get_json()
    if not data.get("name"):
        return _err("name is required")
    vendor = Vendor(
        company_id      = company_id,
        name            = data["name"],
        contact_name    = data.get("contact_name"),
        email           = data.get("email"),
        phone           = data.get("phone"),
        min_order_value = data.get("min_order_value", 0),
        lead_days       = data.get("lead_days", 3),
        notes           = data.get("notes"),
    )
    db.session.add(vendor)
    db.session.commit()
    return jsonify(vendor.to_dict()), 201


@api_v1_bp.route("/flora/vendors/<vid>", methods=["GET"])
@jwt_required()
def get_vendor(vid):
    company_id = get_company_id()
    vendor = Vendor.query.filter_by(id=vid, company_id=company_id).first_or_404()
    d = vendor.to_dict()
    d["flower_prefs"] = [p.to_dict() for p in vendor.flower_prefs]
    return jsonify(d)


@api_v1_bp.route("/flora/vendors/<vid>", methods=["PUT"])
@jwt_required()
def update_vendor(vid):
    company_id = get_company_id()
    vendor = Vendor.query.filter_by(id=vid, company_id=company_id).first_or_404()
    data = request.get_json()
    for field in ["name", "contact_name", "email", "phone",
                  "min_order_value", "lead_days", "notes", "is_active"]:
        if field in data:
            setattr(vendor, field, data[field])
    db.session.commit()
    return jsonify(vendor.to_dict())


@api_v1_bp.route("/flora/vendors/<vid>/preferences", methods=["POST"])
@jwt_required()
def add_vendor_preference(vid):
    company_id = get_company_id()
    Vendor.query.filter_by(id=vid, company_id=company_id).first_or_404()
    data = request.get_json()
    pref = VendorFlowerPreference(
        vendor_id           = vid,
        flower_id           = data["flower_id"],
        priority_rank       = data.get("priority_rank", 1),
        typical_unit_price  = data.get("typical_unit_price"),
        bunch_size_override = data.get("bunch_size_override"),
        min_fill_rate       = data.get("min_fill_rate", 80.0),
    )
    db.session.add(pref)
    db.session.commit()
    return jsonify(pref.to_dict()), 201


@api_v1_bp.route("/flora/vendors/<vid>/preferences/<pid>", methods=["DELETE"])
@jwt_required()
def delete_vendor_preference(vid, pid):
    pref = VendorFlowerPreference.query.filter_by(id=pid, vendor_id=vid).first_or_404()
    db.session.delete(pref)
    db.session.commit()
    return jsonify({"deleted": True})


# ══════════════════════════════════════════════
# RECIPES
# ══════════════════════════════════════════════

@api_v1_bp.route("/flora/recipes", methods=["GET"])
@jwt_required()
def list_recipes():
    company_id = get_company_id()
    q = Recipe.query.filter_by(company_id=company_id)
    status = request.args.get("status")
    if status:
        q = q.filter_by(status=status)
    category = request.args.get("category")
    if category:
        q = q.filter_by(category=category)
    search = request.args.get("q")
    if search:
        q = q.filter(Recipe.name.ilike(f"%{search}%"))
    recipes = q.order_by(Recipe.name).all()
    return jsonify([r.to_dict() for r in recipes])


@api_v1_bp.route("/flora/recipes", methods=["POST"])
@jwt_required()
def create_recipe():
    company_id = get_company_id()
    uid = get_jwt_identity()
    data = request.get_json()
    if not data.get("name"):
        return _err("name is required")

    recipe = Recipe(
        company_id    = company_id,
        name          = data["name"],
        category      = data.get("category", "other"),
        status        = "draft",
        tags          = data.get("tags", []),
        labor_minutes = data.get("labor_minutes", 0),
        markup_pct    = data.get("markup_pct", 20.0),
        is_public     = data.get("is_public", True),
        created_by    = uid,
    )
    db.session.add(recipe)
    db.session.flush()

    # Create initial version
    version = RecipeVersion(
        recipe_id      = recipe.id,
        version_number = 1,
        change_summary = "Initial version",
        created_by     = uid,
    )
    db.session.add(version)
    db.session.flush()

    # Add stems if provided
    stems_data = data.get("stems", [])
    for i, s in enumerate(stems_data):
        stem = RecipeStem(
            recipe_version_id   = version.id,
            flower_id           = s["flower_id"],
            quantity            = s.get("quantity", 1),
            unit_cost_override  = s.get("unit_cost_override"),
            buffer_pct_override = s.get("buffer_pct_override"),
            notes               = s.get("notes"),
            sort_order          = i,
        )
        db.session.add(stem)

    db.session.flush()
    version.recalculate_totals()
    recipe.current_version_id = version.id
    db.session.commit()
    return jsonify(recipe.to_dict(include_stems=True)), 201


@api_v1_bp.route("/flora/recipes/<rid>", methods=["GET"])
@jwt_required()
def get_recipe(rid):
    company_id = get_company_id()
    recipe = Recipe.query.filter_by(id=rid, company_id=company_id).first_or_404()
    return jsonify(recipe.to_dict(include_stems=True))


@api_v1_bp.route("/flora/recipes/<rid>", methods=["PUT"])
@jwt_required()
def update_recipe(rid):
    """Update recipe — always creates a new version when stems change."""
    company_id = get_company_id()
    uid = get_jwt_identity()
    recipe = Recipe.query.filter_by(id=rid, company_id=company_id).first_or_404()
    data = request.get_json()

    # Update recipe metadata
    for field in ["name", "category", "tags", "labor_minutes", "markup_pct",
                  "is_public", "photo_url"]:
        if field in data:
            setattr(recipe, field, data[field])

    # If stems are included, create a new version
    if "stems" in data:
        current = recipe.current_version
        next_num = (current.version_number + 1) if current else 1

        version = RecipeVersion(
            recipe_id      = recipe.id,
            version_number = next_num,
            change_summary = data.get("change_summary", f"Version {next_num}"),
            created_by     = uid,
        )
        db.session.add(version)
        db.session.flush()

        for i, s in enumerate(data["stems"]):
            stem = RecipeStem(
                recipe_version_id   = version.id,
                flower_id           = s["flower_id"],
                quantity            = s.get("quantity", 1),
                unit_cost_override  = s.get("unit_cost_override"),
                buffer_pct_override = s.get("buffer_pct_override"),
                notes               = s.get("notes"),
                sort_order          = i,
            )
            db.session.add(stem)

        db.session.flush()
        version.recalculate_totals()
        recipe.current_version_id = version.id

    db.session.commit()
    return jsonify(recipe.to_dict(include_stems=True))


@api_v1_bp.route("/flora/recipes/<rid>/publish", methods=["POST"])
@jwt_required()
def publish_recipe(rid):
    company_id = get_company_id()
    recipe = Recipe.query.filter_by(id=rid, company_id=company_id).first_or_404()
    recipe.status = "published"
    db.session.commit()
    return jsonify(recipe.to_dict())


@api_v1_bp.route("/flora/recipes/<rid>/versions", methods=["GET"])
@jwt_required()
def list_recipe_versions(rid):
    company_id = get_company_id()
    Recipe.query.filter_by(id=rid, company_id=company_id).first_or_404()
    versions = RecipeVersion.query.filter_by(recipe_id=rid)\
                                  .order_by(RecipeVersion.version_number.desc()).all()
    return jsonify([v.to_dict() for v in versions])


@api_v1_bp.route("/flora/recipes/<rid>/duplicate", methods=["POST"])
@jwt_required()
def duplicate_recipe(rid):
    company_id = get_company_id()
    uid = get_jwt_identity()
    source = Recipe.query.filter_by(id=rid, company_id=company_id).first_or_404()
    source_v = source.current_version

    new_recipe = Recipe(
        company_id    = company_id,
        name          = f"{source.name} (copy)",
        category      = source.category,
        status        = "draft",
        tags          = list(source.tags or []),
        labor_minutes = source.labor_minutes,
        markup_pct    = source.markup_pct,
        is_public     = source.is_public,
        created_by    = uid,
    )
    db.session.add(new_recipe)
    db.session.flush()

    version = RecipeVersion(
        recipe_id      = new_recipe.id,
        version_number = 1,
        change_summary = f"Copied from {source.name}",
        created_by     = uid,
    )
    db.session.add(version)
    db.session.flush()

    if source_v:
        for s in source_v.stems:
            db.session.add(RecipeStem(
                recipe_version_id   = version.id,
                flower_id           = s.flower_id,
                quantity            = s.quantity,
                unit_cost_override  = s.unit_cost_override,
                buffer_pct_override = s.buffer_pct_override,
                notes               = s.notes,
                sort_order          = s.sort_order,
            ))

    db.session.flush()
    version.recalculate_totals()
    new_recipe.current_version_id = version.id
    db.session.commit()
    return jsonify(new_recipe.to_dict(include_stems=True)), 201


# ══════════════════════════════════════════════
# EVENTS
# ══════════════════════════════════════════════

@api_v1_bp.route("/flora/events", methods=["GET"])
@jwt_required()
def list_flora_events():
    company_id = get_company_id()
    q = FloraEvent.query.filter_by(company_id=company_id)
    status = request.args.get("status")
    if status:
        q = q.filter_by(status=status)
    events = q.order_by(FloraEvent.event_date.asc()).all()
    return jsonify([e.to_dict() for e in events])


@api_v1_bp.route("/flora/events", methods=["POST"])
@jwt_required()
def create_flora_event():
    company_id = get_company_id()
    uid = get_jwt_identity()
    data = request.get_json()
    if not data.get("name"):
        return _err("name is required")

    event_date = None
    if data.get("event_date"):
        try:
            event_date = date.fromisoformat(data["event_date"])
        except ValueError:
            return _err("Invalid event_date format. Use YYYY-MM-DD")

    event = FloraEvent(
        company_id       = company_id,
        name             = data["name"],
        event_date       = event_date,
        event_type       = data.get("event_type", "wedding"),
        status           = data.get("status", "inquiry"),
        venue            = data.get("venue"),
        quoted_budget    = data.get("quoted_budget", 0),
        guest_count      = data.get("guest_count"),
        style_tags       = data.get("style_tags", []),
        brief_notes      = data.get("brief_notes"),
        created_by       = uid,
        lead_designer_id = uid,
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict(include_arrangements=True)), 201


@api_v1_bp.route("/flora/events/<eid>", methods=["GET"])
@jwt_required()
def get_flora_event(eid):
    company_id = get_company_id()
    event = FloraEvent.query.filter_by(id=eid, company_id=company_id).first_or_404()
    return jsonify(event.to_dict(include_arrangements=True))


@api_v1_bp.route("/flora/events/<eid>", methods=["PUT"])
@jwt_required()
def update_flora_event(eid):
    company_id = get_company_id()
    event = FloraEvent.query.filter_by(id=eid, company_id=company_id).first_or_404()
    data = request.get_json()

    if "event_date" in data and data["event_date"]:
        try:
            event.event_date = date.fromisoformat(data["event_date"])
        except ValueError:
            return _err("Invalid event_date format")

    for field in ["name", "event_type", "status", "venue", "quoted_budget",
                  "guest_count", "style_tags", "brief_notes", "lead_designer_id"]:
        if field in data:
            setattr(event, field, data[field])

    db.session.commit()
    return jsonify(event.to_dict(include_arrangements=True))


@api_v1_bp.route("/flora/events/<eid>/confirm", methods=["POST"])
@jwt_required()
def confirm_event(eid):
    company_id = get_company_id()
    event = FloraEvent.query.filter_by(id=eid, company_id=company_id).first_or_404()
    event.status = "confirmed"
    db.session.commit()
    return jsonify(event.to_dict())


# ── Event Arrangements ──────────────────────────────────────

@api_v1_bp.route("/flora/events/<eid>/arrangements", methods=["POST"])
@jwt_required()
def add_arrangement(eid):
    company_id = get_company_id()
    event = FloraEvent.query.filter_by(id=eid, company_id=company_id).first_or_404()
    data = request.get_json()

    recipe = Recipe.query.filter_by(id=data["recipe_id"], company_id=company_id).first_or_404()
    version = recipe.current_version
    if not version:
        return _err("Recipe has no published version")

    sort_order = len(list(event.arrangements))
    arr = EventArrangement(
        event_id          = eid,
        recipe_id         = recipe.id,
        recipe_version_id = version.id,
        quantity          = data.get("quantity", 1),
        location_note     = data.get("location_note"),
        sort_order        = sort_order,
    )
    db.session.add(arr)
    db.session.commit()
    return jsonify(arr.to_dict()), 201


@api_v1_bp.route("/flora/events/<eid>/arrangements/<aid>", methods=["PUT"])
@jwt_required()
def update_arrangement(eid, aid):
    company_id = get_company_id()
    FloraEvent.query.filter_by(id=eid, company_id=company_id).first_or_404()
    arr = EventArrangement.query.filter_by(id=aid, event_id=eid).first_or_404()
    data = request.get_json()
    if "quantity" in data:
        arr.quantity = max(1, int(data["quantity"]))
    if "location_note" in data:
        arr.location_note = data["location_note"]
    db.session.commit()
    return jsonify(arr.to_dict())


@api_v1_bp.route("/flora/events/<eid>/arrangements/<aid>", methods=["DELETE"])
@jwt_required()
def delete_arrangement(eid, aid):
    company_id = get_company_id()
    FloraEvent.query.filter_by(id=eid, company_id=company_id).first_or_404()
    arr = EventArrangement.query.filter_by(id=aid, event_id=eid).first_or_404()
    db.session.delete(arr)
    db.session.commit()
    return jsonify({"deleted": True})


# ── Event Stem Summary ──────────────────────────────────────

@api_v1_bp.route("/flora/events/<eid>/stem-summary", methods=["GET"])
@jwt_required()
def event_stem_summary(eid):
    company_id = get_company_id()
    event = FloraEvent.query.filter_by(id=eid, company_id=company_id).first_or_404()
    summary = calculate_event_summary(event)
    return jsonify(summary)


# ── Event Payments ──────────────────────────────────────────

@api_v1_bp.route("/flora/events/<eid>/payments", methods=["GET"])
@jwt_required()
def list_event_payments(eid):
    company_id = get_company_id()
    FloraEvent.query.filter_by(id=eid, company_id=company_id).first_or_404()
    payments = EventPayment.query.filter_by(event_id=eid)\
                                 .order_by(EventPayment.payment_date).all()
    return jsonify([p.to_dict() for p in payments])


@api_v1_bp.route("/flora/events/<eid>/payments", methods=["POST"])
@jwt_required()
def add_event_payment(eid):
    company_id = get_company_id()
    FloraEvent.query.filter_by(id=eid, company_id=company_id).first_or_404()
    data = request.get_json()
    payment = EventPayment(
        event_id     = eid,
        amount       = data["amount"],
        payment_type = data.get("payment_type", "deposit"),
        payment_date = date.fromisoformat(data["payment_date"]) if data.get("payment_date") else date.today(),
        method       = data.get("method"),
        notes        = data.get("notes"),
    )
    db.session.add(payment)
    db.session.commit()
    return jsonify(payment.to_dict()), 201


# ══════════════════════════════════════════════
# PURCHASE ORDERS
# ══════════════════════════════════════════════

@api_v1_bp.route("/flora/events/<eid>/generate-po", methods=["POST"])
@jwt_required()
def generate_po(eid):
    company_id = get_company_id()
    uid = get_jwt_identity()
    event = FloraEvent.query.filter_by(id=eid, company_id=company_id).first_or_404()

    if not event.arrangements:
        return _err("Event has no arrangements")

    # Aggregate stems
    stems = aggregate_event_stems(event)

    # Build vendor preference map
    vendor_prefs = {}
    for stem in stems:
        fid = stem["flower_id"]
        prefs = VendorFlowerPreference.query\
            .filter_by(flower_id=fid)\
            .join(Vendor)\
            .filter(Vendor.company_id == company_id, Vendor.is_active == True)\
            .all()
        vendor_prefs[fid] = [
            {
                "vendor_id":           p.vendor_id,
                "priority_rank":       p.priority_rank,
                "typical_unit_price":  float(p.typical_unit_price or 0),
                "bunch_size_override": p.bunch_size_override,
            }
            for p in prefs
        ]

    vendor_lines, unassigned = build_po_line_items(stems, vendor_prefs)

    # If nothing assigned to vendors, create one PO with all stems
    if not vendor_lines:
        default_vendor = Vendor.query.filter_by(company_id=company_id, is_active=True).first()
        if not default_vendor:
            return _err("No vendors configured. Add at least one vendor first.")
        vendor_lines = {default_vendor.id: [
            {**s, "unit_price": s["unit_cost"], "line_total": s["line_cost"]}
            for s in stems
        ]}

    # Required by date = event date - vendor lead days
    created_pos = []
    for vendor_id, lines in vendor_lines.items():
        vendor = Vendor.query.get(vendor_id)
        req_date = None
        if event.event_date and vendor:
            req_date = event.event_date - timedelta(days=vendor.lead_days or 3)

        po = PurchaseOrder(
            company_id       = company_id,
            event_id         = eid,
            vendor_id        = vendor_id,
            po_number        = _next_po_number(company_id),
            status           = "draft",
            required_by_date = req_date,
            created_by       = uid,
        )
        db.session.add(po)
        db.session.flush()

        for line in lines:
            li = POLineItem(
                po_id            = po.id,
                flower_id        = line["flower_id"],
                stems_required   = line["stems_required"],
                bunches_required = line["bunches_required"],
                bunch_size       = line["bunch_size"],
                unit_price       = line["unit_price"],
                line_total       = line["line_total"],
            )
            db.session.add(li)

        db.session.flush()
        po.recalculate_total()
        created_pos.append(po)

    db.session.commit()
    return jsonify([po.to_dict(include_lines=True) for po in created_pos]), 201


@api_v1_bp.route("/flora/orders", methods=["GET"])
@jwt_required()
def list_orders():
    company_id = get_company_id()
    q = PurchaseOrder.query.filter_by(company_id=company_id)
    status = request.args.get("status")
    if status:
        q = q.filter_by(status=status)
    event_id = request.args.get("event_id")
    if event_id:
        q = q.filter_by(event_id=event_id)
    orders = q.order_by(PurchaseOrder.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders])


@api_v1_bp.route("/flora/orders/<oid>", methods=["GET"])
@jwt_required()
def get_order(oid):
    company_id = get_company_id()
    order = PurchaseOrder.query.filter_by(id=oid, company_id=company_id).first_or_404()
    return jsonify(order.to_dict(include_lines=True))


@api_v1_bp.route("/flora/orders/<oid>/send", methods=["POST"])
@jwt_required()
def send_order(oid):
    company_id = get_company_id()
    order = PurchaseOrder.query.filter_by(id=oid, company_id=company_id).first_or_404()
    order.status  = "sent"
    order.sent_at = datetime.utcnow()
    db.session.commit()
    return jsonify(order.to_dict())


@api_v1_bp.route("/flora/orders/<oid>", methods=["PUT"])
@jwt_required()
def update_order(oid):
    company_id = get_company_id()
    order = PurchaseOrder.query.filter_by(id=oid, company_id=company_id).first_or_404()
    data = request.get_json()
    for field in ["status", "notes", "required_by_date"]:
        if field in data:
            setattr(order, field, data[field])
    db.session.commit()
    return jsonify(order.to_dict(include_lines=True))


# ══════════════════════════════════════════════
# INVENTORY
# ══════════════════════════════════════════════

@api_v1_bp.route("/flora/inventory", methods=["GET"])
@jwt_required()
def get_inventory():
    company_id = get_company_id()
    flowers = Flower.query.filter_by(company_id=company_id, is_active=True).all()
    result = []
    for flower in flowers:
        last_entry = InventoryLedger.query\
            .filter_by(company_id=company_id, flower_id=flower.id)\
            .order_by(InventoryLedger.created_at.desc()).first()
        balance = last_entry.balance_after if last_entry else 0
        result.append({**flower.to_dict(), "current_balance": balance})
    return jsonify(result)


@api_v1_bp.route("/flora/inventory/adjust", methods=["POST"])
@jwt_required()
def adjust_inventory():
    company_id = get_company_id()
    uid = get_jwt_identity()
    data = request.get_json()

    flower = Flower.query.filter_by(id=data["flower_id"], company_id=company_id).first_or_404()
    last = InventoryLedger.query\
        .filter_by(company_id=company_id, flower_id=flower.id)\
        .order_by(InventoryLedger.created_at.desc()).first()
    current_balance = last.balance_after if last else 0
    delta = int(data["quantity_delta"])
    new_balance = current_balance + delta

    entry = InventoryLedger(
        company_id       = company_id,
        flower_id        = flower.id,
        transaction_type = data.get("transaction_type", "adjusted"),
        quantity_delta   = delta,
        reference_id     = data.get("reference_id"),
        notes            = data.get("notes"),
        balance_after    = new_balance,
        created_by       = uid,
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201


# ══════════════════════════════════════════════
# FLORAFLOW DASHBOARD
# ══════════════════════════════════════════════

@api_v1_bp.route("/flora/dashboard", methods=["GET"])
@jwt_required()
def flora_dashboard():
    company_id = get_company_id()
    from sqlalchemy import func

    active_events = FloraEvent.query.filter(
        FloraEvent.company_id == company_id,
        FloraEvent.status.in_(["confirmed", "in_production"])
    ).count()

    pending_pos = PurchaseOrder.query.filter_by(
        company_id=company_id, status="draft"
    ).count()

    total_recipes = Recipe.query.filter(
        Recipe.company_id == company_id,
        Recipe.status == "published"
    ).count()

    upcoming = FloraEvent.query.filter(
        FloraEvent.company_id == company_id,
        FloraEvent.status.in_(["confirmed", "in_production"]),
        FloraEvent.event_date >= date.today()
    ).order_by(FloraEvent.event_date).limit(5).all()

    recent_pos = PurchaseOrder.query.filter_by(company_id=company_id)\
        .order_by(PurchaseOrder.created_at.desc()).limit(5).all()

    return jsonify({
        "active_events":   active_events,
        "pending_pos":     pending_pos,
        "total_recipes":   total_recipes,
        "upcoming_events": [e.to_dict() for e in upcoming],
        "recent_pos":      [po.to_dict() for po in recent_pos],
    })


# ══════════════════════════════════════════════
# AI STEM ANALYZER
# ══════════════════════════════════════════════

_GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

_ANALYZE_PROMPT = """You are an expert floral designer helping calculate stem orders.

Carefully examine this floral image and identify every flower, foliage, and greenery type visible.

Return ONLY valid JSON — no markdown fences, no explanation — in this exact shape:
{
  "arrangement_type": "centerpiece",
  "total_stems_estimate": 45,
  "flowers": [
    {
      "common_name": "Garden Rose",
      "variety": "White Ohara",
      "color": "White",
      "estimated_stems": 12,
      "confidence": "high"
    }
  ],
  "notes": "Lush garden-style centerpiece with layered textures."
}

Rules:
- arrangement_type: one of bouquet, centerpiece, arch, boutonniere, ceremony, installation, other
- estimated_stems: count of individual stems (not flower heads in compound stems)
- confidence: "high" (clearly identifiable), "medium" (likely), "low" (best guess)
- Include foliage and greenery as separate line items
- Be conservative — only count what you can see or reasonably infer
- If you truly cannot identify a type, use "Unknown Flower" as common_name"""


@api_v1_bp.route("/flora/ai/analyze-image", methods=["POST"])
@jwt_required()
def ai_analyze_image():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return _err("GROQ_API_KEY is not set. Add it to your environment and restart.", 503)

    if "image" not in request.files:
        return _err("No image file provided. Send as multipart/form-data with field name 'image'.")

    file = request.files["image"]
    image_bytes = file.read()

    if len(image_bytes) > 10 * 1024 * 1024:
        return _err("Image too large — maximum size is 10 MB.")

    mime = file.content_type or "image/jpeg"
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    try:
        import requests as _requests
        resp = _requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": _GROQ_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        {"type": "text", "text": _ANALYZE_PROMPT},
                    ],
                }],
                "temperature": 0.1,
                "max_tokens": 1024,
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if the model wraps the output
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw.strip())
        return jsonify(result)

    except json.JSONDecodeError:
        return _err("AI returned an unparseable response. Please try again.", 502)
    except Exception as e:
        return _err(f"Analysis failed: {str(e)}", 503)
