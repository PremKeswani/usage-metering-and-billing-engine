import json
import time
import hmac
import hashlib
import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
URL = "http://127.0.0.1:8000/webhooks/stripe"


def sign_payload(payload: str, secret: str) -> str:
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


def send_event(event_dict, sig_header=None):
    payload = json.dumps(event_dict)
    if sig_header is None:
        sig_header = sign_payload(payload, WEBHOOK_SECRET)

    resp = requests.post(
        URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": sig_header
        }
    )
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
    return resp


# Test 1: valid checkout.session.completed event
checkout_event = {
    "id": "evt_test_1",
    "type": "checkout.session.completed",
    "data": {
        "object": {
            "client_reference_id": "1",   # our test tenant id
            "customer": "cus_test_123",
            "subscription": "sub_test_123"
        }
    }
}

print("=== Test 1: Valid checkout.session.completed ===")
send_event(checkout_event)

print("\n=== Test 2: Replay the SAME event (should be ignored as duplicate) ===")
send_event(checkout_event)

print("\n=== Test 3: Forged signature (should be rejected with 400) ===")
send_event(checkout_event, sig_header="t=123,v1=forgedsignature")