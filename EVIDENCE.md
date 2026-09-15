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