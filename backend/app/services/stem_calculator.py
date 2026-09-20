"""
FloraFlow — Stem Calculation Engine

Core business logic for scaling recipes, aggregating event stems,
and generating purchase order line items.
All functions are pure where possible — no DB side effects.
"""
import math
from collections import defaultdict


def apply_buffer(stems: int, buffer_pct: float) -> int:
    """Add buffer percentage and always round up."""
    return math.ceil(stems * (1 + buffer_pct / 100.0))


def round_to_bunch(stems: int, bunch_size: int) -> int:
    """Round up to the nearest full bunch."""
    if bunch_size <= 0:
        return stems
    return math.ceil(stems / bunch_size) * bunch_size


def scale_recipe_version(version, quantity: int, category_buffer_pct: float = 10.0) -> list:
    """
    Scale a RecipeVersion by quantity.
    Returns a list of stem line items with buffered + rounded quantities.

    Each item: {
        flower_id, flower_name, variety, color, display_name,
        base_stems, buffer_pct, buffered_stems, bunch_size, bunches,
        unit_cost, line_cost
    }
    """
    result = []
    if not version or not version.stems:
        return result

    for stem in version.stems:
        flower = stem.flower
        if not flower:
            continue

        # Buffer: stem override → category default → flower default → 10%
        buffer_pct = float(
            stem.buffer_pct_override
            or flower.default_buffer_pct
            or category_buffer_pct
            or 10.0
        )

        base_stems  = stem.quantity * quantity
        buffered    = apply_buffer(base_stems, buffer_pct)
        bunch_size  = flower.bunch_size or 10
        bunches     = math.ceil(buffered / bunch_size)
        unit_cost   = float(stem.unit_cost_override or flower.cost_per_stem or 0)

        result.append({
            "flower_id":      flower.id,
            "flower_name":    flower.common_name,
            "variety":        flower.variety or "",
            "color":          flower.color or "",
            "display_name":   flower.to_dict()["display_name"],
            "base_stems":     base_stems,
            "buffer_pct":     buffer_pct,
            "buffered_stems": buffered,
            "bunch_size":     bunch_size,
            "bunches":        bunches,
            "unit_cost":      unit_cost,
            "line_cost":      unit_cost * buffered,
        })

    return result


def aggregate_event_stems(event) -> list:
    """
    Aggregate stems across all arrangements in an event.
    Merges same flower_id entries, recalculates bunches on merged total.

    Returns sorted list of aggregated stem items.
    """
    aggregated = defaultdict(lambda: {
        "flower_id":   None,
        "display_name": "",
        "flower_name":  "",
        "variety":      "",
        "color":        "",
        "buffered_stems": 0,
        "bunches":      0,
        "bunch_size":   10,
        "unit_cost":    0,
        "line_cost":    0,
    })

    for arrangement in event.arrangements:
        recipe  = arrangement.recipe
        version = arrangement.version or (recipe.current_version if recipe else None)
        if not version:
            continue

        category_buffer = recipe.category_buffer_pct if recipe else 10.0
        scaled = scale_recipe_version(version, arrangement.quantity, category_buffer)

        for item in scaled:
            fid = item["flower_id"]
            agg = aggregated[fid]
            agg["flower_id"]    = fid
            agg["display_name"] = item["display_name"]
            agg["flower_name"]  = item["flower_name"]
            agg["variety"]      = item["variety"]
            agg["color"]        = item["color"]
            agg["bunch_size"]   = item["bunch_size"]
            agg["unit_cost"]    = item["unit_cost"]
            agg["buffered_stems"] += item["buffered_stems"]
            agg["line_cost"]    += item["line_cost"]

    # Recalculate bunches on merged total
    for fid, item in aggregated.items():
        item["bunches"] = math.ceil(item["buffered_stems"] / (item["bunch_size"] or 10))

    return sorted(aggregated.values(), key=lambda x: x["flower_name"])


def calculate_event_summary(event) -> dict:
    """
    Full summary for an event: per-flower stem list + totals + margin.
    """
    stems = aggregate_event_stems(event)
    total_stems  = sum(s["buffered_stems"] for s in stems)
    total_cost   = sum(s["line_cost"] for s in stems)
    quoted       = float(event.quoted_budget or 0)
    margin_pct   = ((quoted - total_cost) / quoted * 100) if quoted > 0 else 0

    arrangements_summary = []
    for arr in event.arrangements:
        recipe  = arr.recipe
        version = arr.version or (recipe.current_version if recipe else None)
        arrangements_summary.append({
            "id":            arr.id,
            "recipe_name":   recipe.name if recipe else "Unknown",
            "category":      recipe.category if recipe else "",
            "quantity":      arr.quantity,
            "location_note": arr.location_note,
            "stems_per_unit": version.total_stems if version else 0,
            "total_stems":   (version.total_stems if version else 0) * arr.quantity,
            "cost_per_unit": float(version.cost_per_unit or 0) if version else 0,
            "total_cost":    float(version.cost_per_unit or 0) * arr.quantity if version else 0,
        })

    return {
        "event_id":            event.id,
        "event_name":          event.name,
        "quoted_budget":       quoted,
        "total_stems":         total_stems,
        "estimated_cost":      round(total_cost, 2),
        "margin_pct":          round(margin_pct, 1),
        "margin_amount":       round(quoted - total_cost, 2),
        "stems_by_flower":     stems,
        "arrangements":        arrangements_summary,
    }


def build_po_line_items(stems_list: list, vendor_prefs: dict) -> dict:
    """
    Given aggregated stems and a vendor preference map,
    assign each flower to its preferred vendor and return
    a dict of {vendor_id: [line_items]}.

    vendor_prefs: {flower_id: [{vendor_id, priority_rank, typical_unit_price, bunch_size_override}]}
    """
    vendor_lines = defaultdict(list)
    unassigned   = []

    for stem in stems_list:
        fid   = stem["flower_id"]
        prefs = sorted(vendor_prefs.get(fid, []), key=lambda p: p["priority_rank"])

        if prefs:
            pref        = prefs[0]
            vendor_id   = pref["vendor_id"]
            unit_price  = pref.get("typical_unit_price") or stem["unit_cost"]
            bunch_size  = pref.get("bunch_size_override") or stem["bunch_size"] or 10
            bunches     = math.ceil(stem["buffered_stems"] / bunch_size)
            line_total  = unit_price * stem["buffered_stems"]

            vendor_lines[vendor_id].append({
                "flower_id":      fid,
                "display_name":   stem["display_name"],
                "stems_required": stem["buffered_stems"],
                "bunches_required": bunches,
                "bunch_size":     bunch_size,
                "unit_price":     unit_price,
                "line_total":     round(line_total, 2),
            })
        else:
            unassigned.append(stem)

    return dict(vendor_lines), unassigned
