from app.pricing import calculate_api_call_cost, calculate_token_cost

# Test 1: API calls
cost1 = calculate_api_call_cost(1000)
print(f"1000 API calls -> {cost1} cents (expected 50)")
assert cost1 == 50

# Test 2: Simple token cost, no caching, no reasoning
cost2 = calculate_token_cost(input_tokens=1000, cached_input_tokens=0, output_tokens=1000, reasoning_tokens=0)
expected2 = round(1000 * 15 / 1000 + 0 + 1000 * 60 / 1000)
print(f"1000 fresh input + 1000 output -> {cost2} cents (expected {expected2})")
assert cost2 == expected2

# Test 3: Cached input tokens should be cheaper than fresh
cost_fresh = calculate_token_cost(input_tokens=1000, cached_input_tokens=0, output_tokens=0, reasoning_tokens=0)
cost_cached = calculate_token_cost(input_tokens=0, cached_input_tokens=1000, output_tokens=0, reasoning_tokens=0)
print(f"1000 fresh input -> {cost_fresh} cents, 1000 cached input -> {cost_cached} cents")
assert cost_cached < cost_fresh

# Test 4: Reasoning tokens should be priced the same as output tokens
cost_output = calculate_token_cost(input_tokens=0, cached_input_tokens=0, output_tokens=1000, reasoning_tokens=0)
cost_reasoning = calculate_token_cost(input_tokens=0, cached_input_tokens=0, output_tokens=0, reasoning_tokens=1000)
print(f"1000 output -> {cost_output} cents, 1000 reasoning -> {cost_reasoning} cents (should be equal)")
assert cost_output == cost_reasoning

print("\nAll pricing tests passed.")