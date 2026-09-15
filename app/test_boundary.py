import requests

url = "http://127.0.0.1:8000/generate"

# We already have 1 usage event from earlier, so send 999 more to hit exactly 1000
for i in range(999):
    key = f"boundary-test-{i}"
    resp = requests.post(url, json={
        "tenant_id": 1,
        "idempotency_key": key,
        "type": "api_call",
        "quantity": 1
    })
    if resp.status_code != 200:
        print(f"Unexpected failure at i={i}: {resp.status_code} {resp.text}")
        break
else:
    print("Sent 999 requests successfully. Now at exactly 1000 usage.")

# This next one should be REJECTED with 429
final = requests.post(url, json={
    "tenant_id": 1,
    "idempotency_key": "boundary-test-final",
    "type": "api_call",
    "quantity": 1
})
print("Final request status:", final.status_code)
print("Final request body:", final.text)