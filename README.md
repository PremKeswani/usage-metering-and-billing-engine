# Usage Metering & Billing Engine

A backend service that meters usage (API calls, AI tokens), enforces plan quotas,
calculates costs with real-world token pricing rules, and syncs subscription state
with Stripe via signature-verified, idempotent webhooks.

## Architecture

Client -> POST /generate -> MeterService (idempotent record) -> QuotaService (check limit)
                                                               -> allowed / 429 / 402

GET /usage -> rollup(usage_events) -> { used, limit, cost }

Stripe Checkout -> subscription created
Stripe -> signed webhook -> /webhooks/stripe
  -> verify signature (forged -> 400)
  -> deduplicate event (replay -> ignored)
  -> update tenant plan/status

Layers: routes (HTTP) -> services (business logic) -> db (models/queries)

## Plans

| Plan | API calls/month | AI tokens/month |
|------|-----------------|------------------|
| Free | 1,000           | 100,000          |
| Pro  | 20,000          | 5,000,000        |

## Setup

1. Clone the repo
2. Create a virtual environment and install dependencies:
   pip install -r requirements.txt
3. Copy .env.example to .env and fill in values
4. Start Postgres: docker compose up -d
5. Run the app: uvicorn app.main:app --reload --port 8000
6. Seed initial data: python -m app.seed

## Endpoints

- POST /generate - record a billable usage event (idempotent)
- GET /usage?tenant_id=X - usage, limits, and cost for a tenant
- POST /checkout - create a Stripe Checkout session
- POST /webhooks/stripe - Stripe webhook handler

## Limitations

- Stripe account creation is not available in Pakistan. Webhook handling was built
  and tested using the real Stripe SDK verification logic against locally-generated,
  correctly-signed test events, rather than a live Stripe test account. See BUILDLOG.md.
- Token cost breakdown (cached vs fresh input, reasoning vs standard output) is
  supported in the pricing engine (app/pricing.py) but the current /generate endpoint
  only records a flat token quantity; full category-level metering is a natural next step.
- No invoicing, proration, or overage billing in core (see stretch goals in the brief).