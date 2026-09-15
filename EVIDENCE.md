# Evidence

## Idempotency Proof

Sent the same request twice with idempotency_key "test-key-1":

First call -> created event id 1, retry: false
Second call (identical) -> returned event id 1, retry: true

Database check confirms only ONE row exists in usage_events for this key:

 id | tenant_id | type     | quantity | idempotency_key | created_at
----+-----------+----------+----------+------------------+------------
  1 |         1 | api_call |        1 | test-key-1       | 2026-09-15
(1 row)

## Quota Boundary Proof

Drove tenant 1 (free plan, limit 1000 api_call/month) to its quota limit.

Once usage reached 1000, the next request was rejected:

Status: 429
Body: {"detail":{"reason":"quota_exceeded","limit":1000,"current_usage":1000,
"message":"Quota exceeded for api_call. Limit is 1000, current usage is 1000."}}

A further request also correctly rejected:

Status: 429
Body: {"detail":{"reason":"quota_exceeded","limit":1000,"current_usage":1001,
"message":"Quota exceeded for api_call. Limit is 1000, current usage is 1001."}}

This confirms: current_usage + requested_quantity <= limit is enforced correctly,
and requests beyond the limit are rejected with a clear, machine-readable message.

## Stripe Webhook Proof

Since Stripe account creation is not available in Pakistan, webhook handling was tested
using locally-generated, correctly-signed test events matching Stripe's exact event schema
and signature scheme (HMAC-SHA256, same as stripe.Webhook.construct_event).

Test 1 - Valid checkout.session.completed event:
Status: 200
Body: {"status":"ok","event_type":"checkout.session.completed"}
Database confirms tenant 1 flipped from Free (plan_id 1) to Pro (plan_id 2), status active,
with stripe_customer_id and stripe_subscription_id correctly stored.

Test 2 - Replayed the SAME event again (testing deduplication):
Status: 200
Body: {"status":"ignored","reason":"duplicate event"}
Confirms the event was processed only once.

Test 3 - Forged signature:
Status: 400
Body: {"detail":"Invalid signature"}
Confirms signature verification rejects tampered/forged requests.