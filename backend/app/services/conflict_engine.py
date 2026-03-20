"""
EventFlow Pro — Inventory Conflict Detection Engine

The most critical business service. Checks item availability across
overlapping date ranges with buffer times using efficient SQL queries.
"""
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse as parse_date
from app.extensions import db
from app.models import (
    InventoryItem, Project, ProjectLineItem, ProjectStage, SetAside,
)


def check_item_availability(item, start, end, requested_qty=1):
    """
    Check if an inventory item is available for a given date range.

    Returns:
        {
            "available": bool,
            "requested": int,
            "available_quantity": int,
            "conflicts": [...],
            "alternates": [...],
        }
    """
    if isinstance(start, str):
        start = parse_date(start)
    if isinstance(end, str):
        end = parse_date(end)

    # Apply buffer time
    buffer = timedelta(minutes=item.buffer_minutes or 0)
    buffered_start = start - buffer
    buffered_end = end + buffer

    # Active project stages that reserve inventory
    active_stages = [
        ProjectStage.signed,
        ProjectStage.deposit_paid,
        ProjectStage.confirmed,
        ProjectStage.paid_in_full,
    ]

    # Find conflicting projects (date range overlap)
    conflicts = db.session.query(
        Project.id,
        Project.project_number,
        Project.event_name,
        Project.event_start,
        Project.event_end,
        ProjectLineItem.quantity,
    ).join(ProjectLineItem).filter(
        ProjectLineItem.item_id == item.id,
        Project.stage.in_(active_stages),
        # Overlap condition: NOT (end < project_start OR start > project_end)
        db.not_(
            db.or_(
                buffered_end <= Project.event_start,
                buffered_start >= Project.event_end,
            )
        ),
    ).all()

    # Calculate reserved quantity during this period
    reserved_qty = sum(c.quantity for c in conflicts)

    # Get set-aside quantity (damaged, missing, etc.)
    set_aside_qty = db.session.query(
        db.func.coalesce(db.func.sum(SetAside.quantity), 0)
    ).filter(
        SetAside.item_id == item.id,
        SetAside.resolved_at.is_(None),
    ).scalar()

    total_unavailable = reserved_qty + int(set_aside_qty)
    currently_available = max(0, item.total_quantity - total_unavailable)
    is_available = currently_available >= requested_qty

    result = {
        "available": is_available,
        "requested": requested_qty,
        "total_quantity": item.total_quantity,
        "available_quantity": currently_available,
        "reserved_quantity": reserved_qty,
        "set_aside_quantity": int(set_aside_qty),
        "conflicts": [{
            "project_id": str(c.id),
            "project_number": c.project_number,
            "event_name": c.event_name,
            "event_start": c.event_start.isoformat(),
            "event_end": c.event_end.isoformat(),
            "quantity_reserved": c.quantity,
        } for c in conflicts],
        "alternates": [],
    }

    # If not available, suggest alternates from the same pool
    if not is_available and item.pool_id:
        alternates = InventoryItem.query.filter(
            InventoryItem.pool_id == item.pool_id,
            InventoryItem.id != item.id,
            InventoryItem.status == InventoryItem.status.default.arg,
        ).all()

        for alt in alternates:
            alt_result = check_item_availability(alt, start, end, requested_qty)
            if alt_result["available"]:
                result["alternates"].append({
                    "item_id": str(alt.id),
                    "name": alt.name,
                    "available_quantity": alt_result["available_quantity"],
                    "price": float(alt.price),
                })

    return result


def get_availability_calendar(item, year, month):
    """
    Get daily availability for an item across a month.
    Returns a dict of {date_str: available_qty}.
    """
    from calendar import monthrange

    _, days_in_month = monthrange(year, month)
    calendar = {}

    active_stages = [
        ProjectStage.signed, ProjectStage.deposit_paid,
        ProjectStage.confirmed, ProjectStage.paid_in_full,
    ]

    # Get all reservations that overlap this month
    month_start = datetime(year, month, 1, tzinfo=timezone.utc)
    month_end = datetime(year, month, days_in_month, 23, 59, 59, tzinfo=timezone.utc)

    reservations = db.session.query(
        Project.event_start,
        Project.event_end,
        ProjectLineItem.quantity,
    ).join(ProjectLineItem).filter(
        ProjectLineItem.item_id == item.id,
        Project.stage.in_(active_stages),
        db.not_(
            db.or_(
                month_end <= Project.event_start,
                month_start >= Project.event_end,
            )
        ),
    ).all()

    # Set aside quantity (constant across all days)
    set_aside_qty = db.session.query(
        db.func.coalesce(db.func.sum(SetAside.quantity), 0)
    ).filter(
        SetAside.item_id == item.id,
        SetAside.resolved_at.is_(None),
    ).scalar()

    for day in range(1, days_in_month + 1):
        date = datetime(year, month, day, tzinfo=timezone.utc)
        date_str = date.strftime("%Y-%m-%d")

        reserved_today = sum(
            r.quantity for r in reservations
            if r.event_start.date() <= date.date() <= r.event_end.date()
        )

        available = max(0, item.total_quantity - reserved_today - int(set_aside_qty))
        calendar[date_str] = available

    return calendar


def bulk_check_availability(items_with_qty, start, end):
    """
    Check availability for multiple items at once.
    items_with_qty: [(item_id, quantity), ...]
    Returns: {item_id: {available, conflicts, ...}}
    """
    results = {}
    for item_id, qty in items_with_qty:
        item = InventoryItem.query.get(item_id)
        if item:
            results[item_id] = check_item_availability(item, start, end, qty)
        else:
            results[item_id] = {"available": False, "error": "Item not found"}
    return results
