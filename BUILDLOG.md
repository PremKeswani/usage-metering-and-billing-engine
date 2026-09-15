# Build Log

## Stripe limitation
Stripe account creation is not available in Pakistan, so a live test account could not
be obtained. Implemented webhook handling using the real Stripe SDK verification logic
(stripe.Webhook.construct_event), tested against locally-generated events signed with
the same HMAC-SHA256 scheme Stripe uses in production.

## Issues debugged
- stripe.Webhook.construct_event() returns a StripeObject, not a plain dict — accessing
  fields with .get() or converting with dict() both failed; fixed using the SDK's own
  .to_dict() method.
- Initial event-deduplication logic marked an event as "processed" before its handler
  actually completed, meaning a crash mid-processing would incorrectly mark a real event
  as already handled. Fixed by moving the dedup marker to after successful processing.

## AI assistance
Used Claude AI as a coding assistant for parts of the implementation and debugging.
Reviewed and tested all generated code before accepting it.