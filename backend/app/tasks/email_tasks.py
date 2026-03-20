"""
EventFlow Pro — Celery Email Tasks
"""
from app.tasks import celery_app


@celery_app.task(name="app.tasks.email_tasks.send_client_email")
def send_client_email(message_id):
    """Send an email to a client via SendGrid."""
    import os
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        return {"status": "skipped", "reason": "No SendGrid API key"}

    # Import inside task to avoid circular imports
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models import Message
        message = Message.query.get(message_id)
        if not message or not message.client:
            return {"status": "error", "reason": "Message or client not found"}

        mail = Mail(
            from_email=os.getenv("FROM_EMAIL", "noreply@eventflow.pro"),
            to_emails=message.client.email,
            subject=message.subject or "Message from your event team",
            plain_text_content=message.body,
        )

        try:
            sg = SendGridAPIClient(api_key)
            sg.send(mail)
            return {"status": "sent", "message_id": message_id}
        except Exception as e:
            return {"status": "error", "reason": str(e)}


@celery_app.task(name="app.tasks.email_tasks.send_payment_receipt")
def send_payment_receipt(payment_id):
    """Send a payment receipt email."""
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models import Payment
        payment = Payment.query.get(payment_id)
        if not payment:
            return

        # Build receipt content
        project = payment.project
        client = payment.client
        body = (
            f"Payment received: ${payment.amount:.2f}\n"
            f"Project: {project.event_name} ({project.project_number})\n"
            f"Method: {payment.method.value}\n"
            f"Balance remaining: ${project.balance_due:.2f}\n\n"
            f"Thank you for your payment!"
        )

        send_client_email.delay(
            _create_system_message(client.id, project.id, "Payment Receipt", body)
        )


def _create_system_message(client_id, project_id, subject, body):
    from app.models.operations import Message, MessageDirection, MessageChannel
    from app.extensions import db
    msg = Message(
        client_id=client_id, project_id=project_id,
        direction=MessageDirection.outbound,
        channel=MessageChannel.system,
        subject=subject, body=body,
    )
    db.session.add(msg)
    db.session.commit()
    return msg.id
