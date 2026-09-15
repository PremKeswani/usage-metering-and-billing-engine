from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import Base, engine, get_db
from app import models
from app.meter_service import record_usage
from app.quota_service import check_quota

Base.metadata.create_all(bind=engine)

app = FastAPI()

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