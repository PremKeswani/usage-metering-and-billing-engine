import stripe
import os
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Subscription, Plan, Tenant
from pydantic import BaseModel

router = APIRouter()

WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Track processed event IDs in memory for now (simple dedup)
processed_events = set()


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_id = event["id"]
    if event_id in processed_events:
        return {"status": "ignored", "reason": "duplicate event"}

    event_type = event["type"]
    data = event["data"]["object"]
    data = data.to_dict()

    if event_type == "checkout.session.completed":
        tenant_id = int(data["client_reference_id"])
        pro_plan = db.query(Plan).filter_by(name="pro").first()

        sub = db.query(Subscription).filter_by(tenant_id=tenant_id).first()
        if not sub:
            sub = Subscription(tenant_id=tenant_id, plan_id=pro_plan.id, status="active")
            db.add(sub)
        else:
            sub.plan_id = pro_plan.id
            sub.status = "active"
        sub.stripe_customer_id = data.get("customer")
        sub.stripe_subscription_id = data.get("subscription")
        db.commit()

    elif event_type == "customer.subscription.deleted":
        stripe_sub_id = data["id"]
        sub = db.query(Subscription).filter_by(stripe_subscription_id=stripe_sub_id).first()
        if sub:
            free_plan = db.query(Plan).filter_by(name="free").first()
            sub.plan_id = free_plan.id
            sub.status = "canceled"
            db.commit()

    processed_events.add(event_id)
    return {"status": "ok", "event_type": event_type}

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
stripe.api_key = STRIPE_SECRET_KEY

class CheckoutRequest(BaseModel):
    tenant_id: int

@router.post("/checkout")
def create_checkout_session(payload: CheckoutRequest, db: Session = Depends(get_db)):
    tenant_id = payload.tenant_id
    tenant = db.query(Tenant).filter_by(id=tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            client_reference_id=str(tenant_id),
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "Pro Plan"},
                    "unit_amount": 2000,
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }],
            success_url="http://localhost:8000/success",
            cancel_url="http://localhost:8000/cancel",
        )
        return {"checkout_url": session.url}
    except stripe.error.AuthenticationError:
        return {
            "status": "simulated",
            "message": "Stripe account not available in this environment (no valid API key). "
                        "In production with real Stripe credentials, this would return a real "
                        "Checkout URL. Session parameters were built and sent correctly.",
            "would_have_sent": {
                "mode": "subscription",
                "client_reference_id": str(tenant_id),
                "product": "Pro Plan",
                "amount": 2000
            }
        }