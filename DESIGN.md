# Design Doc — Usage Metering & Billing Engine

## Problem
This service meters billable usage (API calls and AI tokens) per tenant, enforces
plan quotas before allowing usage, calculates cost from usage with token-specific
pricing rules, and keeps subscription status in sync with Stripe via webhooks.

## Non-goal
This capstone does not implement proration, invoicing, or overage billing in core —
these are stretch goals only. Stripe account creation is unavailable in Pakistan;
Stripe integration is built and tested using the Stripe SDK with mocked/signed test
fixtures rather than a live test account (confirmed acceptable by program staff).

## Data Model

### tenants
- id (primary key)
- name
- created_at

### plans
- id (primary key)
- name            -- 'free' or 'pro'
- api_call_limit
- token_limit

### subscriptions
- id (primary key)
- tenant_id (foreign key → tenants.id)
- plan_id (foreign key → plans.id)
- status                  -- 'active', 'canceled', etc.
- stripe_customer_id
- stripe_subscription_id
- updated_at

### usage_events
- id (primary key)
- tenant_id (foreign key → tenants.id)
- type            -- 'api_call' or 'ai_tokens'
- quantity
- idempotency_key
- created_at
- UNIQUE constraint on (tenant_id, idempotency_key)

## Boundary Rule

A request is allowed if: current_usage + requested_quantity <= plan_limit

Example: limit = 1000
- current usage 999, request 1 more -> total 1000 -> ALLOWED (exactly at limit is OK)
- current usage 1000, request 1 more -> total 1001 -> REJECTED (429 Too Many Requests)

If a tenant is on the Free plan and tries an action that requires a paid feature entirely,
respond with 402 Payment Required instead of 429.

## API Surface

### POST /generate
The one dummy billable endpoint. Simulates a customer doing something billable
(e.g. an AI call or an API call).
Request body: { tenant_id, idempotency_key, type, quantity }
- type: "api_call" or "ai_tokens"
Behavior: records a usage event (idempotently), checks quota, returns
allowed/rejected with clear message.

### GET /usage?tenant_id=...
Returns the tenant's current usage, limits, and cost for the month.
Response: { used: {...}, limit: {...}, cost: ... }

### POST /checkout
Creates a Stripe Checkout session so a tenant can upgrade to Pro.
(Built in Phase 3)

### POST /webhooks/stripe
Receives events from Stripe (checkout completed, subscription updated/deleted).
Verifies signature, deduplicates, updates tenant's plan/status.
(Built in Phase 3)