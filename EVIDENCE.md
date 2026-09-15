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