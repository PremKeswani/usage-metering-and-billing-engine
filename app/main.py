from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.webhooks import router as webhook_router
from app.database import Base, engine, get_db
from app import models
from app.meter_service import record_usage
from app.quota_service import check_quota, get_current_plan, get_usage_this_month

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(webhook_router)

@app.get("/health")
def health():
    return {"status": "ok"}


class GenerateRequest(BaseModel):
    tenant_id: int
    idempotency_key: str
    type: str          # "api_call" or "ai_tokens"
    quantity: int


@app.post("/generate")
def generate(payload: GenerateRequest, db: Session = Depends(get_db)):
    # Step A: record usage idempotently
    event, is_new = record_usage(
        db,
        tenant_id=payload.tenant_id,
        type=payload.type,
        quantity=payload.quantity,
        idempotency_key=payload.idempotency_key
    )

    if not is_new:
        # This is a retry -- return the same result as before, no new quota check
        return {
            "status": "ok",
            "retry": True,
            "event_id": event.id,
            "message": "Duplicate request -- returning original result"
        }

    # Step B: check quota (only for genuinely new events)
    allowed, reason, limit, current_usage = check_quota(
        db,
        tenant_id=payload.tenant_id,
        usage_type=payload.type,
        quantity=payload.quantity
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "reason": reason,
                "limit": limit,
                "current_usage": current_usage,
                "message": f"Quota exceeded for {payload.type}. Limit is {limit}, current usage is {current_usage}."
            }
        )

    return {
        "status": "ok",
        "retry": False,
        "event_id": event.id,
        "current_usage": current_usage + payload.quantity,
        "limit": limit
    }

@app.get("/usage")
def get_usage(tenant_id: int, db: Session = Depends(get_db)):
    plan = get_current_plan(db, tenant_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Tenant or plan not found")

    api_used = get_usage_this_month(db, tenant_id, "api_call")
    tokens_used = get_usage_this_month(db, tenant_id, "ai_tokens")

    return {
        "tenant_id": tenant_id,
        "plan": plan.name,
        "api_calls": {
            "used": api_used,
            "limit": plan.api_call_limit,
            "remaining": max(plan.api_call_limit - api_used, 0)
        },
        "ai_tokens": {
            "used": tokens_used,
            "limit": plan.token_limit,
            "remaining": max(plan.token_limit - tokens_used, 0)
        }
    }