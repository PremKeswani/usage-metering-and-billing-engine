# Pricing constants, pinned here for auditability (values in cents per 1,000 tokens/calls)
# These are illustrative rates loosely modeled on real-world AI token pricing tiers.

PRICING = {
    "api_call": {
        "rate_per_1000": 50,       # 50 cents per 1000 API calls
    },
    "ai_tokens": {
        "input_rate_per_1000": 15,          # fresh input tokens
        "cached_input_rate_per_1000": 3,    # cached input tokens are cheaper
        "output_rate_per_1000": 60,         # output tokens (includes reasoning tokens)
    }
}


def calculate_api_call_cost(quantity: int) -> int:
    """Returns cost in cents."""
    return round(quantity * PRICING["api_call"]["rate_per_1000"] / 1000)


def calculate_token_cost(input_tokens: int, cached_input_tokens: int,
                          output_tokens: int, reasoning_tokens: int) -> int:
    """
    Returns cost in cents.
    Rules:
    - cached input tokens are billed at the cheaper cached rate
    - reasoning tokens are billed as output tokens (not a separate category)
    - categories are priced separately, never simply summed together at one rate
    """
    fresh_input_cost = input_tokens * PRICING["ai_tokens"]["input_rate_per_1000"] / 1000
    cached_input_cost = cached_input_tokens * PRICING["ai_tokens"]["cached_input_rate_per_1000"] / 1000
    # reasoning tokens count as output tokens for pricing purposes
    total_output_tokens = output_tokens + reasoning_tokens
    output_cost = total_output_tokens * PRICING["ai_tokens"]["output_rate_per_1000"] / 1000

    return round(fresh_input_cost + cached_input_cost + output_cost)