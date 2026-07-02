#!/usr/bin/env python3
"""CF-24 finite-epsilon/step vs limit-smuggling gate."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf24_finite_epsilon_step_vs_limit_smuggling_gate_results.json"


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    return value


def iterate_contraction(x0: float, ratio: float, epsilon: float, max_steps: int) -> dict[str, Any]:
    x = x0
    history = [x]
    reached = abs(x) <= epsilon
    reached_step = 0 if reached else None
    for step in range(1, max_steps + 1):
        x = ratio * x
        history.append(x)
        if reached_step is None and abs(x) <= epsilon:
            reached = True
            reached_step = step
            break
    return {
        "x0": x0,
        "ratio": ratio,
        "epsilon": epsilon,
        "max_steps": max_steps,
        "reached": reached,
        "reached_step": reached_step,
        "last_value": history[-1],
        "history": history,
    }


def positive_finite_epsilon_gate() -> dict[str, Any]:
    run = iterate_contraction(x0=1.0, ratio=0.72, epsilon=0.05, max_steps=12)
    return {
        "pass": run["reached"] is True and run["reached_step"] is not None and run["reached_step"] <= 12,
        "epsilon_declared": run["epsilon"],
        "step_budget_declared": run["max_steps"],
        "stopping_rule": "abs(x) <= epsilon",
        "finite_run": run,
    }


def primitive_limit_negative_gate() -> dict[str, Any]:
    finite_failure = iterate_contraction(x0=1.0, ratio=0.72, epsilon=0.05, max_steps=4)
    rejected = finite_failure["reached"] is False
    return {
        "pass": False,
        "expected": "fail",
        "negative_case_type": "executable_rejection",
        "negative_rejected": rejected,
        "attempted_claim": {
            "claim": "this converges eventually, so the finite claim is admitted",
            "epsilon_declared": False,
            "step_budget_declared": False,
            "finite_failure_case_available": True,
        },
        "finite_failure_case": finite_failure,
    }


def asymptotic_explanation_boundary_gate() -> dict[str, Any]:
    finite_open = iterate_contraction(x0=1.0, ratio=0.92, epsilon=0.05, max_steps=8)
    return {
        "pass": finite_open["reached"] is False,
        "asymptotic_intuition_allowed": True,
        "load_bearing_claim": "open_until_finite_threshold_reached",
        "finite_open_case": finite_open,
        "interpretation": "asymptotic convergence can guide a hypothesis, but cannot replace the finite threshold and step budget",
    }


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    positive = positive_finite_epsilon_gate()
    negative = primitive_limit_negative_gate()
    boundary = asymptotic_explanation_boundary_gate()
    result = {
        "schema": "cf24_finite_epsilon_step_vs_limit_smuggling_gate_result_v1",
        "name": "cf24_finite_epsilon_step_vs_limit_smuggling_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-24",
        "gate": "EG-CF24-finite-epsilon-step-vs-limit-smuggling",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-24 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "python_float": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite recurrence, epsilon threshold, step budget, and finite failure case",
            },
            "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
        },
        "TOOL_INTEGRATION_DEPTH": {"python_float": "load_bearing", "python_json": "supportive"},
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": positive["pass"] and negative["pass"] is False and negative["negative_rejected"] and boundary["pass"],
    }
    OUT.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
