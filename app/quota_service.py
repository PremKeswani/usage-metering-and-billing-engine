from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import UsageEvent, Subscription, Plan
from datetime import datetime, timezone
from typing import Optional

def get_current_plan(db: Session, tenant_id: int) -> Optional[Plan]:
    sub = db.query(Subscription).filter_by(tenant_id=tenant_id).first()
    if sub:
        return db.query(Plan).filter_by(id=sub.plan_id).first()
    return db.query(Plan).filter_by(name="free").first()

def get_usage_this_month(db: Session, tenant_id: int, usage_type: str) -> int:
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total = db.query(func.coalesce(func.sum(UsageEvent.quantity), 0)).filter(
        UsageEvent.tenant_id == tenant_id,
        UsageEvent.type == usage_type,
        UsageEvent.created_at >= start_of_month
    ).scalar()
    return total or 0

def check_quota(db: Session, tenant_id: int, usage_type: str, quantity: int):
    """
    Returns (allowed: bool, reason: str or None, limit: int, current_usage: int)
    """
    plan = get_current_plan(db, tenant_id)
    limit = plan.api_call_limit if usage_type == "api_call" else plan.token_limit

    current_usage = get_usage_this_month(db, tenant_id, usage_type)

    if current_usage + quantity <= limit:
        return True, None, limit, current_usage
    else:
        return False, "quota_exceeded", limit, current_usage