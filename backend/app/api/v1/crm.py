"""
Evently — CRM API (Contacts, Notes, Tasks, Pipeline)

Twenty-CRM-inspired additions on top of the existing Client model:
contacts (people belonging to a client), a notes timeline, tasks with
due dates, and a lifecycle pipeline for the client relationship itself.
"""
from datetime import datetime, timezone
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.extensions import db
from app.models import Client, Contact, Note, Task, ActivityLog, TaskStatus, TaskPriority
from app.schemas import (
    ClientSchema,
    ContactSchema, ContactCreateSchema,
    NoteSchema, NoteCreateSchema,
    TaskSchema, TaskCreateSchema, TaskUpdateSchema,
)
from app.api.v1.inventory import get_current_company_id


def _err(message, status=400):
    return jsonify({"error": message}), status


def _get_client_or_404(client_id, company_id):
    return Client.query.filter_by(id=client_id, company_id=company_id).first_or_404()


def _log(company_id, entity_type, entity_id, action, changes=None):
    db.session.add(ActivityLog(
        company_id=company_id, user_id=get_jwt_identity(),
        entity_type=entity_type, entity_id=entity_id, action=action, changes=changes or {},
    ))


# ════════════════════════════════════════
# PIPELINE — lifecycle stage board
# ════════════════════════════════════════

@api_v1_bp.route("/clients/pipeline", methods=["GET"])
@jwt_required()
def crm_pipeline():
    """Clients grouped by lifecycle stage, for the CRM kanban view."""
    company_id = get_current_company_id()
    stages = ["lead", "qualified", "active", "past_client", "lost"]
    clients = Client.query.filter_by(company_id=company_id).order_by(Client.updated_at.desc()).all()

    board = {stage: [] for stage in stages}
    for c in clients:
        stage = c.lifecycle_stage if c.lifecycle_stage in board else "lead"
        board[stage].append(ClientSchema().dump(c))

    return jsonify({"stages": stages, "board": board})


@api_v1_bp.route("/clients/<client_id>/stage", methods=["POST"])
@jwt_required()
def move_client_stage(client_id):
    company_id = get_current_company_id()
    client = _get_client_or_404(client_id, company_id)
    stage = (request.json or {}).get("lifecycle_stage")
    valid = ["lead", "qualified", "active", "past_client", "lost"]
    if stage not in valid:
        return _err(f"lifecycle_stage must be one of {valid}")

    old_stage = client.lifecycle_stage
    client.lifecycle_stage = stage
    _log(company_id, "client", client.id, "stage_changed", {"from": old_stage, "to": stage})
    db.session.commit()
    return jsonify(ClientSchema().dump(client))


# ════════════════════════════════════════
# CONTACTS
# ════════════════════════════════════════

@api_v1_bp.route("/clients/<client_id>/contacts", methods=["GET"])
@jwt_required()
def list_contacts(client_id):
    company_id = get_current_company_id()
    client = _get_client_or_404(client_id, company_id)
    return jsonify(ContactSchema(many=True).dump(client.contacts.all()))


@api_v1_bp.route("/clients/<client_id>/contacts", methods=["POST"])
@jwt_required()
def create_contact(client_id):
    company_id = get_current_company_id()
    client = _get_client_or_404(client_id, company_id)

    errors = ContactCreateSchema().validate(request.json or {})
    if errors:
        return jsonify({"errors": errors}), 400

    data = request.json
    if data.get("is_primary"):
        Contact.query.filter_by(client_id=client.id).update({"is_primary": False})

    contact = Contact(company_id=company_id, client_id=client.id,
                       **{k: data[k] for k in data if hasattr(Contact, k)})
    db.session.add(contact)
    _log(company_id, "client", client.id, "contact_added", {"name": contact.name})
    db.session.commit()
    return jsonify(ContactSchema().dump(contact)), 201


@api_v1_bp.route("/contacts/<contact_id>", methods=["PATCH"])
@jwt_required()
def update_contact(contact_id):
    company_id = get_current_company_id()
    contact = Contact.query.filter_by(id=contact_id, company_id=company_id).first_or_404()
    data = request.json or {}
    if data.get("is_primary"):
        Contact.query.filter_by(client_id=contact.client_id).update({"is_primary": False})
    for key in ["name", "role", "email", "phone", "is_primary"]:
        if key in data:
            setattr(contact, key, data[key])
    db.session.commit()
    return jsonify(ContactSchema().dump(contact))


@api_v1_bp.route("/contacts/<contact_id>", methods=["DELETE"])
@jwt_required()
def delete_contact(contact_id):
    company_id = get_current_company_id()
    contact = Contact.query.filter_by(id=contact_id, company_id=company_id).first_or_404()
    db.session.delete(contact)
    db.session.commit()
    return "", 204


# ════════════════════════════════════════
# NOTES
# ════════════════════════════════════════

@api_v1_bp.route("/clients/<client_id>/notes", methods=["GET"])
@jwt_required()
def list_notes(client_id):
    company_id = get_current_company_id()
    client = _get_client_or_404(client_id, company_id)
    notes = client.crm_notes.order_by(Note.is_pinned.desc(), Note.created_at.desc()).all()
    return jsonify(NoteSchema(many=True).dump(notes))


@api_v1_bp.route("/clients/<client_id>/notes", methods=["POST"])
@jwt_required()
def create_note(client_id):
    company_id = get_current_company_id()
    client = _get_client_or_404(client_id, company_id)

    errors = NoteCreateSchema().validate(request.json or {})
    if errors:
        return jsonify({"errors": errors}), 400

    data = request.json
    note = Note(company_id=company_id, client_id=client.id, author_id=get_jwt_identity(),
                body=data["body"], project_id=data.get("project_id"),
                is_pinned=data.get("is_pinned", False))
    db.session.add(note)
    _log(company_id, "client", client.id, "note_added")
    db.session.commit()
    return jsonify(NoteSchema().dump(note)), 201


@api_v1_bp.route("/notes/<note_id>", methods=["DELETE"])
@jwt_required()
def delete_note(note_id):
    company_id = get_current_company_id()
    note = Note.query.filter_by(id=note_id, company_id=company_id).first_or_404()
    db.session.delete(note)
    db.session.commit()
    return "", 204


# ════════════════════════════════════════
# TASKS
# ════════════════════════════════════════

@api_v1_bp.route("/tasks", methods=["GET"])
@jwt_required()
def list_my_tasks():
    """Cross-client task list — e.g. 'My Tasks' view."""
    company_id = get_current_company_id()
    query = Task.query.filter_by(company_id=company_id)

    assignee_id = request.args.get("assignee_id")
    if assignee_id:
        query = query.filter_by(assignee_id=assignee_id)
    status = request.args.get("status")
    if status:
        query = query.filter_by(status=TaskStatus(status))

    tasks = query.order_by(Task.due_date.is_(None), Task.due_date).all()
    return jsonify(TaskSchema(many=True).dump(tasks))


@api_v1_bp.route("/clients/<client_id>/tasks", methods=["GET"])
@jwt_required()
def list_client_tasks(client_id):
    company_id = get_current_company_id()
    client = _get_client_or_404(client_id, company_id)
    tasks = client.crm_tasks.all()
    return jsonify(TaskSchema(many=True).dump(tasks))


@api_v1_bp.route("/clients/<client_id>/tasks", methods=["POST"])
@jwt_required()
def create_task(client_id):
    company_id = get_current_company_id()
    client = _get_client_or_404(client_id, company_id)

    errors = TaskCreateSchema().validate(request.json or {})
    if errors:
        return jsonify({"errors": errors}), 400

    data = TaskCreateSchema().load(request.json)  # deserializes due_date to a datetime
    task = Task(
        company_id=company_id, client_id=client.id,
        title=data["title"], description=data.get("description"),
        due_date=data.get("due_date"), project_id=data.get("project_id"),
        assignee_id=data.get("assignee_id"),
        priority=TaskPriority(data.get("priority", "medium")),
    )
    db.session.add(task)
    _log(company_id, "client", client.id, "task_added", {"title": task.title})
    db.session.commit()
    return jsonify(TaskSchema().dump(task)), 201


@api_v1_bp.route("/tasks/<task_id>", methods=["PATCH"])
@jwt_required()
def update_task(task_id):
    company_id = get_current_company_id()
    task = Task.query.filter_by(id=task_id, company_id=company_id).first_or_404()

    errors = TaskUpdateSchema().validate(request.json or {})
    if errors:
        return jsonify({"errors": errors}), 400

    data = TaskUpdateSchema().load(request.json)  # deserializes due_date to a datetime
    for key in ["title", "description", "due_date", "assignee_id"]:
        if key in data:
            setattr(task, key, data[key])
    if "priority" in data:
        task.priority = TaskPriority(data["priority"])
    if "status" in data:
        task.status = TaskStatus(data["status"])
        if data["status"] == "done":
            task.completed_at = datetime.now(timezone.utc)
        else:
            task.completed_at = None
    db.session.commit()
    return jsonify(TaskSchema().dump(task))


@api_v1_bp.route("/tasks/<task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    company_id = get_current_company_id()
    task = Task.query.filter_by(id=task_id, company_id=company_id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return "", 204


# ════════════════════════════════════════
# TIMELINE — unified activity feed for a client
# ════════════════════════════════════════

@api_v1_bp.route("/clients/<client_id>/timeline", methods=["GET"])
@jwt_required()
def client_timeline(client_id):
    """Merge notes + activity log into one chronological feed, Twenty-style."""
    company_id = get_current_company_id()
    client = _get_client_or_404(client_id, company_id)

    events = []
    for note in client.crm_notes.all():
        events.append({
            "type": "note", "id": note.id, "created_at": note.created_at.isoformat(),
            "body": note.body, "is_pinned": note.is_pinned,
            "author": note.author.name if note.author else None,
        })
    for log in ActivityLog.query.filter_by(entity_type="client", entity_id=client.id).all():
        events.append({
            "type": "activity", "id": log.id, "created_at": log.created_at.isoformat(),
            "action": log.action, "changes": log.changes,
        })

    events.sort(key=lambda e: e["created_at"], reverse=True)
    return jsonify({"events": events})
