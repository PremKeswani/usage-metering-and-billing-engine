from app.database import SessionLocal
from app.models import Plan , Tenant

db = SessionLocal()

existing = db.query(Plan).count()
if existing == 0:
    free = Plan(name="free", api_call_limit=1000, token_limit=100_000)
    pro = Plan(name="pro", api_call_limit=20_000, token_limit=5_000_000)
    db.add_all([free, pro])
    db.commit()
    print("Seeded plans: free, pro")
else:
    print("Plans already exists, skipping seed")

db.close()

existing_tenant = db.query(Tenant).count()
if existing_tenant == 0:
    tenant = Tenant(name="Test Tenant")
    db.add(tenant)
    db.commit()
    print("Seeded test tenant")
else:
    print("Tenant already exists, skipping")