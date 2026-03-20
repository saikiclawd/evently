"""
Evently — Payment Processor (Stripe Integration)
"""
import os
import stripe
from app.extensions import db
from app.models import Payment, Project, PaymentMethod, PaymentStatus, ProjectStage
from app.models.core import utcnow

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


def create_stripe_payment_intent(project, amount, method_str):
    """Create a Stripe PaymentIntent for a project."""
    try:
        payment_method_types = {
            "credit_card": ["card"],
            "debit_card": ["card"],
            "ach": ["us_bank_account"],
            "google_pay": ["card"],
            "bnpl": ["klarna", "afterpay_clearpay"],
        }

        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe uses cents
            currency="usd",
            payment_method_types=payment_method_types.get(method_str, ["card"]),
            metadata={
                "project_id": str(project.id),
                "project_number": project.project_number,
                "client_id": str(project.client_id),
            },
        )

        # Create pending payment record
        payment = Payment(
            project_id=project.id,
            client_id=project.client_id,
            amount=amount,
            method=PaymentMethod(method_str),
            status=PaymentStatus.processing,
            stripe_payment_intent_id=intent.id,
        )
        db.session.add(payment)
        db.session.commit()

        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "payment_id": payment.id,
        }

    except stripe.error.StripeError as e:
        return {"error": str(e)}


def handle_stripe_webhook(payload, sig_header):
    """Process incoming Stripe webhook events."""
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return {"error": "Invalid webhook signature"}

    # Handle payment success
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        _handle_payment_success(intent)

    # Handle payment failure
    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        _handle_payment_failure(intent)

    return {"status": "ok"}


def _handle_payment_success(intent):
    """Process a successful payment."""
    payment = Payment.query.filter_by(
        stripe_payment_intent_id=intent["id"]
    ).first()

    if not payment:
        return

    payment.status = PaymentStatus.succeeded
    payment.paid_at = utcnow()
    payment.stripe_charge_id = intent.get("latest_charge")

    # Extract card details if available
    if intent.get("charges", {}).get("data"):
        charge = intent["charges"]["data"][0]
        pm_details = charge.get("payment_method_details", {})
        if "card" in pm_details:
            payment.card_last_four = pm_details["card"].get("last4")
            payment.card_brand = pm_details["card"].get("brand")
        payment.processing_fee = charge.get("balance_transaction", {}).get("fee", 0) / 100
        payment.net_amount = payment.amount - (payment.processing_fee or 0)

    # Update project payment totals
    project = payment.project
    total_paid = db.session.query(
        db.func.coalesce(db.func.sum(Payment.amount), 0)
    ).filter(
        Payment.project_id == project.id,
        Payment.status == PaymentStatus.succeeded,
    ).scalar()

    project.amount_paid = total_paid

    # Auto-advance stage if fully paid
    if project.is_fully_paid and project.stage in (
        ProjectStage.deposit_paid, ProjectStage.confirmed
    ):
        project.stage = ProjectStage.paid_in_full

    # Update client stats
    if project.client:
        project.client.update_stats()

    db.session.commit()

    # Trigger async tasks
    from app.tasks.email_tasks import send_payment_receipt
    send_payment_receipt.delay(payment.id)

    from app.tasks.quickbooks_tasks import sync_payment
    sync_payment.delay(payment.id)


def _handle_payment_failure(intent):
    """Process a failed payment."""
    payment = Payment.query.filter_by(
        stripe_payment_intent_id=intent["id"]
    ).first()

    if payment:
        payment.status = PaymentStatus.failed
        payment.payment_metadata = {
            **(payment.payment_metadata or {}),
            "failure_message": intent.get("last_payment_error", {}).get("message"),
        }
        db.session.commit()
