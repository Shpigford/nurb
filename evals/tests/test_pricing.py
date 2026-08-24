"""The cost proxy: API-equivalent dollars at list prices, never a guess.

A harness that computed its own cache-aware cost is believed verbatim; a harness
that only counted tokens is priced from the committed table; a row that carries
neither stays blank rather than pretending.
"""

from nurb_evals import pricing

PRICES = {
    "grok": {"grok-4.6": {"input": 2.0, "output": 6.0, "cache_read": 0.5}},
    "claude": {
        "sonnet": {
            "input": 3.0,
            "output": 15.0,
            "cache_read": 0.3,
            "cache_write_5m": 3.75,
        }
    },
}


def test_a_harness_reported_cost_is_believed_verbatim():
    row = {
        "harness": "claude",
        "model": "sonnet",
        "usage": {"total_cost_usd": 0.4321, "input_tokens": 1, "output_tokens": 1},
    }
    assert pricing.trial_cost(row, PRICES) == 0.4321


def test_token_counts_price_from_the_table():
    row = {
        "harness": "grok",
        "model": "grok-4.6",
        "usage": {"input_tokens": 1_000_000, "output_tokens": 500_000},
    }
    assert pricing.trial_cost(row, PRICES) == 2.0 + 3.0


def test_cache_fields_price_at_their_own_rates_when_present():
    row = {
        "harness": "claude",
        "model": "sonnet",
        "usage": {
            "input_tokens": 1_000_000,
            "output_tokens": 0,
            "cache_read_input_tokens": 1_000_000,
            "cache_creation_input_tokens": 1_000_000,
        },
    }
    assert pricing.trial_cost(row, PRICES) == 3.0 + 0.3 + 3.75


def test_an_unpriced_model_or_empty_usage_stays_blank():
    assert pricing.trial_cost({"harness": "codex", "model": "mystery", "usage": {"input_tokens": 1, "output_tokens": 1}}, PRICES) is None
    assert pricing.trial_cost({"harness": "grok", "model": "grok-4.6", "usage": {}}, PRICES) is None
    assert pricing.trial_cost({"harness": "grok", "model": "grok-4.6"}, PRICES) is None


def test_the_committed_table_prices_every_menu_model():
    """Every model the wizard offers must be priceable, so a codex or grok row is
    never blank by accident. claude entries exist too, as the fallback for rows
    whose CLI ever stops reporting its own figure."""
    import tomllib

    prices = pricing.load()
    menu = tomllib.loads((pricing.EVALS / "models.toml").read_text(encoding="utf-8"))
    for harness, entries in menu.items():
        for entry in entries:
            table = prices.get(harness, {}).get(entry["id"])
            assert table, f"prices.toml is missing [{harness}.{entry['id']}]"
            assert table["input"] > 0 and table["output"] > 0
