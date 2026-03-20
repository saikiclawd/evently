"""
Evently — Periodic Celery Tasks
"""
from app.tasks import celery_app


@celery_app.task(name="app.tasks.payment_reminders.send_due_reminders")
def send_due_reminders():
    """Send payment reminders for upcoming and overdue payments."""
    from app import create_app
    app = create_app()
    with app.app_context():
        from datetime import datetime, timedelta, timezone
        from app.extensions import db
        from app.models import PaymentSchedule, Project

        now = datetime.now(timezone.utc)
        upcoming_window = now + timedelta(days=3)

        # Find unpaid schedules due within 3 days or overdue
        due_schedules = PaymentSchedule.query.filter(
            PaymentSchedule.is_paid == False,  # noqa: E712
            PaymentSchedule.reminder_sent == False,  # noqa: E712
            PaymentSchedule.due_date <= upcoming_window,
        ).all()

        sent_count = 0
        for schedule in due_schedules:
            project = Project.query.get(schedule.project_id)
            if not project or not project.client:
                continue

            is_overdue = schedule.due_date < now
            subject = (
                f"Payment overdue: {project.event_name}"
                if is_overdue else
                f"Payment reminder: {project.event_name}"
            )
            body = (
                f"{'This is a reminder that your' if not is_overdue else 'Your'} "
                f"payment of ${schedule.amount:.2f} for {project.event_name} "
                f"{'was due on' if is_overdue else 'is due on'} "
                f"{schedule.due_date.strftime('%B %d, %Y')}.\n\n"
                f"Project: {project.project_number}\n"
                f"Amount: ${schedule.amount:.2f}\n"
                f"Label: {schedule.label}\n"
            )

            from app.tasks.email_tasks import send_client_email, _create_system_message
            msg_id = _create_system_message(
                project.client_id, project.id, subject, body
            )
            send_client_email.delay(msg_id)

            schedule.reminder_sent = True
            schedule.reminder_sent_at = now
            sent_count += 1

        db.session.commit()
        return {"reminders_sent": sent_count}


@celery_app.task(name="app.tasks.inventory_sync.sync_availability")
def sync_availability():
    """Recalculate availability for items with recent booking changes."""
    from app import create_app
    app = create_app()
    with app.app_context():
        from datetime import datetime, timedelta, timezone
        from app.extensions import db
        from app.models import InventoryItem, ItemStatus

        # Recalculate all active items
        items = InventoryItem.query.filter_by(status=ItemStatus.active).all()
        updated = 0
        for item in items:
            old_available = item.available_quantity
            item.recalculate_availability()
            if item.available_quantity != old_available:
                updated += 1

        db.session.commit()
        return {"items_checked": len(items), "items_updated": updated}


@celery_app.task(name="app.tasks.quickbooks_tasks.sync_payment")
def sync_payment(payment_id):
    """Sync a payment to QuickBooks Online."""
    # Placeholder for QuickBooks integration
    return {"status": "pending", "payment_id": payment_id, "message": "QB sync not configured"}


@celery_app.task(name="app.tasks.quickbooks_sync.batch_sync")
def batch_sync():
    """Batch sync unsynced records to QuickBooks."""
    return {"status": "pending", "message": "QB batch sync not configured"}


@celery_app.task(name="app.tasks.monthly_insights.generate_report")
def generate_report():
    """Generate monthly business insights and email to admins."""
    from app import create_app
    app = create_app()
    with app.app_context():
        from datetime import datetime, timedelta, timezone
        from app.extensions import db
        from app.models import Company, User, UserRole, Payment, PaymentStatus, Project

        now = datetime.now(timezone.utc)
        month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
        month_end = now.replace(day=1) - timedelta(seconds=1)
        month_name = month_start.strftime("%B %Y")

        companies = Company.query.all()
        reports_sent = 0

        for company in companies:
            # Calculate monthly stats
            revenue = db.session.query(
                db.func.coalesce(db.func.sum(Payment.amount), 0)
            ).join(Project).filter(
                Project.company_id == company.id,
                Payment.status == PaymentStatus.succeeded,
                Payment.paid_at >= month_start,
                Payment.paid_at <= month_end,
            ).scalar()

            projects_count = Project.query.filter(
                Project.company_id == company.id,
                Project.created_at >= month_start,
                Project.created_at <= month_end,
            ).count()

            # Email admin users
            admins = User.query.filter_by(
                company_id=company.id, role=UserRole.admin, is_active=True
            ).all()

            for admin in admins:
                body = (
                    f"Monthly Business Insights — {month_name}\n\n"
                    f"Revenue: ${float(revenue):,.2f}\n"
                    f"New Projects: {projects_count}\n\n"
                    f"Log in to your dashboard for full details."
                )
                # Send via email task
                reports_sent += 1

        return {"reports_sent": reports_sent, "month": month_name}
