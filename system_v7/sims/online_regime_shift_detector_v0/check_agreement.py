#!/usr/bin/env python3
"""Agreement check for online_regime_shift_detector_v0 exact and JAX legs."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

SIM_ID = "online_regime_shift_detector_v0"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
EXACT = RESULTS / f"{SIM_ID}_exact_results.json"
JAX = RESULTS / f"{SIM_ID}_jax_results.json"
OUT = RESULTS / f"{SIM_ID}_agreement_results.json"
TOL = 1.0e-10


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def numeric_paths(obj: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    params = obj["detector_parameters"]
    out["baseline_mean"] = float(params["baseline_mean"])
    for detector in ("page_hinkley", "cusum"):
        out[f"{detector}.delta"] = float(params[detector]["delta"])
        out[f"{detector}.lambda_threshold"] = float(params[detector]["lambda_threshold"])
    for scenario, payload in obj["scenarios"].items():
        if "statistics" not in payload:
            continue
        for key, value in payload["statistics"].items():
            out[f"{scenario}.{key}"] = float(value)
        if "empirical_fpr" in payload:
            out[f"{scenario}.empirical_fpr"] = float(payload["empirical_fpr"])
        if "shift_size" in payload:
            out[f"{scenario}.shift_size"] = float(payload["shift_size"])
    return out


def tick_paths(obj: dict[str, Any]) -> dict[str, int | None]:
    out: dict[str, int | None] = {}
    for scenario, payload in obj["scenarios"].items():
        for key in ("page_hinkley_detection_tick", "cusum_detection_tick", "dual_detection_tick"):
            if key in payload:
                out[f"{scenario}.{key}"] = payload[key]
        if scenario == "label_erased":
            out["label_erased.stream_a_detection_tick"] = payload["stream_a_detection_tick"]
            out["label_erased.stream_b_detection_tick"] = payload["stream_b_detection_tick"]
    return out


def main() -> int:
    exact = load(EXACT)
    jax = load(JAX)
    failures: list[str] = []
    for name, result in (("exact", exact), ("jax", jax)):
        if result.get("schema") != "codex_ratchet.engine_leg_result.v1":
            failures.append(f"{name}: schema mismatch")
        if result.get("engine_leg_completeness") != "FULL":
            failures.append(f"{name}: engine_leg_completeness not FULL")
        if result.get("reads_peer_result") is not False:
            failures.append(f"{name}: reads_peer_result not false")
        if result.get("all_pass") is not True:
            failures.append(f"{name}: all_pass not true")
        if not result.get("written_at"):
            failures.append(f"{name}: missing written_at")
        if not result.get("negative_tests"):
            failures.append(f"{name}: missing negative_tests")
        if not result.get("facts"):
            failures.append(f"{name}: missing facts")

    exact_ticks = tick_paths(exact)
    jax_ticks = tick_paths(jax)
    for key, exact_value in exact_ticks.items():
        if jax_ticks.get(key) != exact_value:
            failures.append(f"tick mismatch {key}: exact={exact_value} jax={jax_ticks.get(key)}")

    exact_nums = numeric_paths(exact)
    jax_nums = numeric_paths(jax)
    max_abs_diff = 0.0
    max_abs_key = None
    for key, exact_value in exact_nums.items():
        jax_value = jax_nums.get(key)
        if jax_value is None:
            failures.append(f"missing numeric key in jax: {key}")
            continue
        diff = abs(exact_value - jax_value)
        if diff > max_abs_diff:
            max_abs_diff = diff
            max_abs_key = key
        if diff > TOL:
            failures.append(f"numeric parity {key}: exact={exact_value} jax={jax_value} diff={diff}")

    agreement_ok = not failures
    result = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "written_at": now_iso(),
        "agreement_ok": agreement_ok,
        "parity_tolerance": TOL,
        "max_abs_diff": max_abs_diff,
        "max_abs_diff_key": max_abs_key,
        "legs": ["exact", "jax"],
        "detection_ticks": exact_ticks,
        "stationary_fpr": {
            "declared": exact["facts"]["declared_false_positive_rate"],
            "empirical": exact["facts"]["empirical_stationary_fpr"],
        },
        "positive_shift_detected_within": exact["facts"]["positive_shift_detected_within"],
        "drift_behavior": exact["facts"]["drift_behavior"],
        "failures": failures,
        "claim_ceiling": "agreement check only; parity is diagnostic and does not promote QIT, Lev, bridge, or drift-robustness claims",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if agreement_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
