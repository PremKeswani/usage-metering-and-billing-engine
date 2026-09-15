import stripe
import os
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Subscription, Plan, Tenant

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