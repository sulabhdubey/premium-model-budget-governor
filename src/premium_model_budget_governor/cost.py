"""Credit and Sol-parity math."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


RATES = {
    "gpt-5.6-sol": {"input": 100.0, "cached_input": 10.0, "output": 500.0},
    "gpt-6-astra": {"input": 250.0, "cached_input": 25.0, "output": 1250.0},
}


@dataclass(frozen=True)
class TokenPlan:
    input: int = 0
    cached_input: int = 0
    output: int = 0

    @classmethod
    def from_mapping(cls, value: Mapping[str, object] | None) -> "TokenPlan":
        value = value or {}
        return cls(
            input=_token(value.get("input", value.get("input_tokens", 0)), "input"),
            cached_input=_token(value.get("cached_input", value.get("cached_tokens", 0)), "cached_input"),
            output=_token(value.get("output", value.get("output_tokens", 0)), "output"),
        )

    @property
    def billable_volume(self) -> int:
        return self.input + self.cached_input + self.output


def _token(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{name} must be a non-negative number")
    return int(value)


def model_credits(model: str, tokens: TokenPlan | Mapping[str, object], *, fast_mode: bool = False) -> float:
    if model not in RATES:
        raise ValueError(f"unsupported model: {model}")
    plan = tokens if isinstance(tokens, TokenPlan) else TokenPlan.from_mapping(tokens)
    rates = RATES[model]
    credits = (
        plan.input * rates["input"]
        + plan.cached_input * rates["cached_input"]
        + plan.output * rates["output"]
    ) / 1_000_000
    return credits * (2.5 if fast_mode else 1.0)


def estimate_parity(
    *,
    sol_baseline: TokenPlan | Mapping[str, object],
    premium_plan: TokenPlan | Mapping[str, object],
    premium_model: str = "gpt-6-astra",
    baseline_model: str = "gpt-5.6-sol",
    fast_mode: bool = False,
) -> dict[str, object]:
    sol = sol_baseline if isinstance(sol_baseline, TokenPlan) else TokenPlan.from_mapping(sol_baseline)
    premium = premium_plan if isinstance(premium_plan, TokenPlan) else TokenPlan.from_mapping(premium_plan)
    sol_credits = model_credits(baseline_model, sol)
    premium_credits = model_credits(premium_model, premium, fast_mode=fast_mode)
    ceiling = int(sol.billable_volume * (0.4 / (2.5 if fast_mode else 1.0)))
    return {
        "baseline_model": baseline_model,
        "premium_model": premium_model,
        "sol_baseline_credits": round(sol_credits, 6),
        "premium_plan_credits": round(premium_credits, 6),
        "premium_to_sol_ratio": None if sol_credits == 0 else round(premium_credits / sol_credits, 4),
        "sol_parity_met": sol_credits > 0 and premium_credits <= sol_credits and premium.billable_volume <= ceiling,
        "premium_billable_tokens": premium.billable_volume,
        "sol_billable_tokens": sol.billable_volume,
        "premium_billable_token_ceiling": ceiling,
        "fast_mode": fast_mode,
    }
