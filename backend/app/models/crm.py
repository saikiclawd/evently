"""
Evently — CRM Models (Contacts, Notes, Tasks)

Inspired by Twenty CRM's data model: a Client (≈ Twenty's Company) can have
multiple Contacts (≈ Twenty's People), and any record can carry a timeline
of Notes and Tasks.
"""
import enum
from app.extensions import db
from app.models.core import gen_uuid, utcnow


class LifecycleStage(enum.Enum):
    lead = "lead"
    qualified = "qualified"
    active = "active"
    past_client = "past_client"
    lost = "lost"


class TaskStatus(enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskPriority(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


# ── Contact ──
# A person associated with a Client record — e.g. the bride, groom,
# wedding planner, or corporate event coordinator. Mirrors Twenty's
# Person-belongs-to-Company relationship.

class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    company_id = db.Column(db.String(36), db.ForeignKey("companies.id"), nullable=False, index=True)
    client_id = db.Column(db.String(36), db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)

    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100))  # Bride, Groom, Planner, Coordinator, etc.
    email = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    is_primary = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def __repr__(self):
        return f"<Contact {self.name} ({self.role})>"


# ── Note ──
# A freeform, timestamped note attached to a Client and/or Project.
# Mirrors Twenty's Notes — a structured timeline entry, not a single
# freeform text field.

class Note(db.Model):
    __tablename__ = "crm_notes"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    company_id = db.Column(db.String(36), db.ForeignKey("companies.id"), nullable=False, index=True)
    client_id = db.Column(db.String(36), db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=True)
    author_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    body = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, index=True)

    author = db.relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        return f"<Note {self.id} on client {self.client_id}>"


# ── Task ──
# A to-do attached to a Client and/or Project with a due date and
# assignee. Mirrors Twenty's Tasks.

class Task(db.Model):
    __tablename__ = "crm_tasks"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    company_id = db.Column(db.String(36), db.ForeignKey("companies.id"), nullable=False, index=True)
    client_id = db.Column(db.String(36), db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=True)
    assignee_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.Enum(TaskStatus, name="task_status"), default=TaskStatus.todo, index=True)
    priority = db.Column(db.Enum(TaskPriority, name="task_priority"), default=TaskPriority.medium)
    completed_at = db.Column(db.DateTime(timezone=True))

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    assignee = db.relationship("User", foreign_keys=[assignee_id])

    def __repr__(self):
        return f"<Task {self.title} ({self.status.value})>"

    def mark_done(self):
        self.status = TaskStatus.done
        self.completed_at = utcnow()
