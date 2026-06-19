#!/usr/bin/env python3
"""Bounded diffrax capability probe.

This is tool capability evidence only. It does not promote any dynamics lego or
scientific packet.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import diffrax
import jax.numpy as jnp


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v4/probes/sim_diffrax_capability.py"
RESULT_DIR = ROOT / "system_v4/probes/a2_state/sim_results"
RESULT_PATH = RESULT_DIR / "diffrax_capability_results.json"

TOOL_MANIFEST = {
    "diffrax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing capability probe for diffrax.ODETerm and diffrax.diffeqsolve on a bounded ODE fixture",
    }
}
TOOL_INTEGRATION_DEPTH = {"diffrax": "load_bearing"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve_decay(rate: float, y0: float, t1: float) -> float:
    term = diffrax.ODETerm(lambda _t, y, args: -args["rate"] * y)
    sol = diffrax.diffeqsolve(
        term,
        diffrax.Tsit5(),
        t0=0.0,
        t1=t1,
        dt0=0.05,
        y0=jnp.asarray([y0], dtype=jnp.float64),
        args={"rate": rate},
        saveat=diffrax.SaveAt(t1=True),
        stepsize_controller=diffrax.PIDController(rtol=1.0e-10, atol=1.0e-10),
        max_steps=4096,
    )
    return float(sol.ys[-1][0])


def build_result() -> dict:
    positive_value = solve_decay(1.0, 1.0, 1.0)
    positive_expected = math.exp(-1.0)
    erased_value = solve_decay(0.0, 0.75, 1.0)
    boundary_value = solve_decay(3.0, 0.25, 0.0)
    positive_error = abs(positive_value - positive_expected)
    erased_error = abs(erased_value - 0.75)
    boundary_error = abs(boundary_value - 0.25)
    checks = {
        "positive_decay_matches_analytic": positive_error <= 1.0e-8,
        "erased_rate_keeps_initial_value": erased_error <= 1.0e-10,
        "zero_duration_boundary_returns_initial_value": boundary_error <= 1.0e-12,
    }
    all_pass = all(checks.values())
    return {
        "schema": "tool_capability_probe_v1",
        "name": "sim_diffrax_capability",
        "classification": "capability_probe",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": "system_v4/probes/sim_diffrax_capability.py",
        "source_sha256": sha256_file(SOURCE_PATH),
        "packages_used": ["diffrax", "jax.numpy"],
        "aligned_packages_load_bearing": ["diffrax"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "diffrax",
                "qualified_api/function": "diffrax.ODETerm / diffrax.diffeqsolve / diffrax.Tsit5",
                "input_object": "scalar exponential-decay ODE y'=-rate*y",
                "output_object": "terminal y(t)",
                "positive_case": "rate=1, y0=1, t=1 matches exp(-1)",
                "negative/erased_control": "rate=0 keeps y0 fixed",
                "boundary_case": "t1=0 returns y0",
                "demotion_condition": "demote diffrax if solve call, erased control, or zero-duration boundary fails",
                "gates": ["summary.all_pass"],
            }
        ],
        "positive": {
            "value": positive_value,
            "expected": positive_expected,
            "abs_error": positive_error,
            "pass": checks["positive_decay_matches_analytic"],
        },
        "negative": {
            "erased_rate_value": erased_value,
            "expected": 0.75,
            "abs_error": erased_error,
            "pass": checks["erased_rate_keeps_initial_value"],
        },
        "boundary": {
            "zero_duration_value": boundary_value,
            "expected": 0.25,
            "abs_error": boundary_error,
            "pass": checks["zero_duration_boundary_returns_initial_value"],
        },
        "summary": {"all_pass": all_pass, **checks},
        "all_pass": all_pass,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH.relative_to(ROOT))}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
