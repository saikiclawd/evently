"""
EventFlow Pro — Model Registry
Import all models here so Alembic can auto-detect them.
"""
from app.models.core import Company, User, Client, UserRole
from app.models.inventory import (
    InventoryItem, InventoryPool, ItemPhoto, Barcode,
    SetAside, ScanLog, ItemStatus, SetAsideReason, ScanAction,
)
from app.models.project import (
    Project, ProjectLineItem, Proposal, Signature, ProjectStage,
)
from app.models.payment import (
    Payment, PaymentSchedule, QuickBooksSync,
    PaymentMethod, PaymentStatus,
)
from app.models.operations import (
    Vehicle, Route, RouteStop, RouteAssignment, PullSheet,
    Message, EmailTemplate, ActivityLog, WebsiteWishlist,
    RouteStatus, StopType, StopStatus, CrewRole, PullSheetStatus,
)

__all__ = [
    "Company", "User", "Client", "UserRole",
    "InventoryItem", "InventoryPool", "ItemPhoto", "Barcode",
    "SetAside", "ScanLog", "ItemStatus", "SetAsideReason", "ScanAction",
    "Project", "ProjectLineItem", "Proposal", "Signature", "ProjectStage",
    "Payment", "PaymentSchedule", "QuickBooksSync", "PaymentMethod", "PaymentStatus",
    "Vehicle", "Route", "RouteStop", "RouteAssignment", "PullSheet",
    "Message", "EmailTemplate", "ActivityLog", "WebsiteWishlist",
    "RouteStatus", "StopType", "StopStatus", "CrewRole", "PullSheetStatus",
]
