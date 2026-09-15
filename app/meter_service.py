from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import UsageEvent

def record_usage(db: Session, tenant_id: int, type: str, quantity: int, idempotency_key: str):
    """
    Records a usage event idempotently.
    Returns (event, is_new) where is_new is False if this was a retry.
    """
    event = UsageEvent(
        tenant_id=tenant_id,
        type=type,
        quantity=quantity,
        idempotency_key=idempotency_key
    )
    db.add(event)
    try:
        db.commit()
        db.refresh(event)
        return event, True
    except IntegrityError:
        db.rollback()
        existing = db.query(UsageEvent).filter_by(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key
        ).first()
        return existing, False