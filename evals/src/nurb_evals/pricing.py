"""API-equivalent cost of a trial, at list prices.

Subscription trials have no invoice, so the leaderboard reports what the same
tokens would have cost through the API at list prices, the convention every usage
tool (Claude Code's own cost line, ccusage, aider's leaderboard) converged on.

Two paths, in order of trust. A row whose harness computed its own cost keeps it:
claude's total_cost_usd is cache-aware, priced with the CLI's own multipliers, and
recorded at run time, so it never drifts with this file. Everything else derives
from the row's token counts and prices.toml, which is read at report time only:
cost lives outside the benchmark revision on purpose, because a price change must
never orphan a submitted row.
"""

import pathlib
import tomllib

EVALS = pathlib.Path(__file__).parents[2]


def load():
    path = EVALS / "prices.toml"
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def trial_cost(row, prices):
    """Dollars for one trial, or None when the row carries too little to price."""
    usage = row.get("usage") or {}
    reported = usage.get("total_cost_usd")
    if isinstance(reported, (int, float)):
        return float(reported)
    table = (prices.get(row.get("harness")) or {}).get(row.get("model"))
    if not table or "input_tokens" not in usage or "output_tokens" not in usage:
        return None
    per_million = (
        usage["input_tokens"] * table["input"]
        + usage["output_tokens"] * table["output"]
        + usage.get("cache_read_input_tokens", 0) * table.get("cache_read", 0.0)
        + usage.get("cache_creation_input_tokens", 0) * table.get("cache_write_5m", 0.0)
    )
    return per_million / 1e6
