"""
FloraFlow — Local Development Server
Run with: python run_local.py

Uses SQLite (no PostgreSQL or Redis needed).
Creates tables automatically on first run and seeds sample data.
"""
import os
os.environ["FLASK_ENV"] = "local"

from app import create_app
from app.extensions import db
from app.models.core import Company, User
from app.models.flora import (
    Flower, Vendor, Recipe, RecipeVersion, RecipeStem
)
import bcrypt, uuid

app = create_app("local")


def seed_data():
    """Seed sample flowers, a vendor, and a starter recipe if DB is empty."""
    if Flower.query.count() > 0:
        return

    # Get or create a demo company
    company = Company.query.first()
    if not company:
        company = Company(id=str(uuid.uuid4()), name="Luxel Decor & Flowers")
        db.session.add(company)
        db.session.flush()

    # Get or create a demo user
    user = User.query.first()
    if not user:
        pw_hash = bcrypt.hashpw(b"floraflow", bcrypt.gensalt()).decode()
        user = User(
            id=str(uuid.uuid4()),
            company_id=company.id,
            email="owner@luxel.com",
            password_hash=pw_hash,
            name="Studio Owner",
            role="admin",
        )
        db.session.add(user)
        db.session.flush()

    cid = company.id

    # ── Sample Flowers ──────────────────────────────────────
    flowers_data = [
        {"common_name": "Garden Rose",    "variety": "White Ohara",    "color": "White",       "cost_per_stem": 2.40, "bunch_size": 12, "default_buffer_pct": 10},
        {"common_name": "Garden Rose",    "variety": "Blush Juliet",   "color": "Blush",       "cost_per_stem": 2.60, "bunch_size": 12, "default_buffer_pct": 10},
        {"common_name": "Ranunculus",     "variety": "Blush",          "color": "Blush",       "cost_per_stem": 1.80, "bunch_size": 10, "default_buffer_pct": 10},
        {"common_name": "Peony",          "variety": "Sarah Bernhardt", "color": "Blush Pink", "cost_per_stem": 3.50, "bunch_size": 10, "default_buffer_pct": 15, "season_months": [4,5,6]},
        {"common_name": "Lisianthus",     "variety": "White",          "color": "White",       "cost_per_stem": 1.40, "bunch_size":  9, "default_buffer_pct": 10},
        {"common_name": "Stock",          "variety": "Blush",          "color": "Blush",       "cost_per_stem": 1.10, "bunch_size": 10, "default_buffer_pct": 10},
        {"common_name": "Eucalyptus",     "variety": "Silver Dollar",  "color": "Green",       "cost_per_stem": 0.95, "bunch_size": 12, "default_buffer_pct":  8},
        {"common_name": "Eucalyptus",     "variety": "Seeded",         "color": "Green",       "cost_per_stem": 0.85, "bunch_size": 10, "default_buffer_pct":  8},
        {"common_name": "Baby's Breath",  "variety": "Gypsophila",     "color": "White",       "cost_per_stem": 0.60, "bunch_size": 25, "default_buffer_pct":  8},
        {"common_name": "Italian Ruscus", "variety": None,             "color": "Green",       "cost_per_stem": 0.70, "bunch_size": 25, "default_buffer_pct":  8},
        {"common_name": "Spray Rose",     "variety": "Creme de la Creme", "color": "Cream",   "cost_per_stem": 1.60, "bunch_size": 12, "default_buffer_pct": 10},
        {"common_name": "Anemone",        "variety": "White",          "color": "White",       "cost_per_stem": 1.90, "bunch_size": 10, "default_buffer_pct": 12},
        {"common_name": "Wax Flower",     "variety": "White",          "color": "White",       "cost_per_stem": 0.55, "bunch_size": 10, "default_buffer_pct":  8},
        {"common_name": "Dahlia",         "variety": "Café au Lait",   "color": "Blush Tan",   "cost_per_stem": 3.20, "bunch_size":  5, "default_buffer_pct": 15},
        {"common_name": "Sweet Pea",      "variety": "Blush",          "color": "Blush",       "cost_per_stem": 1.50, "bunch_size": 10, "default_buffer_pct": 12},
    ]

    created_flowers = {}
    for fd in flowers_data:
        f = Flower(
            company_id         = cid,
            common_name        = fd["common_name"],
            variety            = fd.get("variety"),
            color              = fd.get("color"),
            cost_per_stem      = fd.get("cost_per_stem", 0),
            bunch_size         = fd.get("bunch_size", 10),
            default_buffer_pct = fd.get("default_buffer_pct", 10),
            season_months      = fd.get("season_months", list(range(1, 13))),
        )
        db.session.add(f)
        db.session.flush()
        key = f"{fd['common_name']}_{fd.get('variety', '')}"
        created_flowers[key] = f

    # ── Sample Vendor ────────────────────────────────────────
    vendor = Vendor(
        company_id   = cid,
        name         = "Mayesh Wholesale",
        contact_name = "Sales Team",
        email        = "orders@mayesh.com",
        phone        = "800-555-0100",
        lead_days    = 3,
        notes        = "Primary wholesale vendor",
    )
    db.session.add(vendor)
    db.session.flush()

    # ── Starter Recipe — Garden Romance Centerpiece ──────────
    recipe = Recipe(
        company_id    = cid,
        name          = "Garden Romance Centerpiece",
        category      = "centerpiece",
        status        = "published",
        tags          = ["garden", "romantic", "blush"],
        labor_minutes = 45,
        markup_pct    = 20.0,
        created_by    = user.id,
    )
    db.session.add(recipe)
    db.session.flush()

    version = RecipeVersion(
        recipe_id      = recipe.id,
        version_number = 1,
        change_summary = "Initial version",
        created_by     = user.id,
    )
    db.session.add(version)
    db.session.flush()

    stems_spec = [
        ("Garden Rose_White Ohara",   12),
        ("Ranunculus_Blush",           8),
        ("Eucalyptus_Silver Dollar",   6),
        ("Lisianthus_White",           5),
        ("Stock_Blush",                6),
        ("Baby's Breath_Gypsophila",   8),
    ]
    for i, (key, qty) in enumerate(stems_spec):
        flower = created_flowers.get(key)
        if flower:
            db.session.add(RecipeStem(
                recipe_version_id = version.id,
                flower_id         = flower.id,
                quantity          = qty,
                sort_order        = i,
            ))

    db.session.flush()
    version.recalculate_totals()
    recipe.current_version_id = version.id

    db.session.commit()
    print("✓ Sample data seeded: 15 flowers, 1 vendor, 1 recipe")
    print(f"  Login: owner@luxel.com / floraflow")


if __name__ == "__main__":
    with app.app_context():
        # Import all models so SQLAlchemy knows about them
        from app.models import core, flora  # noqa
        db.create_all()
        print("✓ Database tables created (floraflow_local.db)")
        seed_data()

    print("\n🌸 FloraFlow local server starting...")
    print("   API:      http://localhost:5001/api/v1")
    print("   Frontend: http://localhost:5173 (run: cd frontend && npm run dev)\n")
    app.run(host="0.0.0.0", port=5001, debug=True)
