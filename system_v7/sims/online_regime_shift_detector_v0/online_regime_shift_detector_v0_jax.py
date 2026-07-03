#!/usr/bin/env python3
"""JAX leg for online_regime_shift_detector_v0."""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import jax
import jax.numpy as jnp
import numpy as np

SIM_ID = "online_regime_shift_detector_v0"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
RESULT = RESULTS / f"{SIM_ID}_jax_results.json"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_spec() -> dict[str, Any]:
    return json.loads((HERE / "spec.json").read_text(encoding="utf-8"))


def rank_index(count: int, alpha: float) -> int:
    return min(count - 1, max(0, int(math.ceil((1.0 - alpha) * count)) - 1))


def stationary_values(n: int, period: int) -> jax.Array:
    idx = jnp.arange(n, dtype=jnp.float64) % period
    square = jnp.where((idx % 16) < 8, 1.0, -1.0)
    return (
        0.026
        + 0.004 * jnp.sin(2.0 * jnp.pi * idx / period)
        + 0.002 * jnp.cos(4.0 * jnp.pi * idx / period)
        + 0.0005 * square
    ).astype(jnp.float64)


def step_shift(values: jax.Array, shift_tick: int, shift_size: float) -> jax.Array:
    return values + jnp.where(jnp.arange(values.shape[0]) >= shift_tick, shift_size, 0.0)


def slow_drift(values: jax.Array, shift_tick: int, shift_size: float, horizon: int) -> jax.Array:
    ticks = jnp.arange(values.shape[0], dtype=jnp.float64)
    ramp = jnp.clip((ticks - shift_tick) / max(1, horizon), 0.0, 1.0)
    return values + shift_size * ramp


def page_hinkley_stats(monitored: jax.Array, mean0: float, delta: float, initial_count: int) -> jax.Array:
    def step(carry: tuple[jax.Array, jax.Array, jax.Array, jax.Array], x: jax.Array) -> tuple[tuple[jax.Array, jax.Array, jax.Array, jax.Array], jax.Array]:
        mean, count, cumulative, min_cumulative = carry
        count = count + 1.0
        mean = mean + (x - mean) / count
        cumulative = cumulative + x - mean - delta
        min_cumulative = jnp.minimum(min_cumulative, cumulative)
        stat = cumulative - min_cumulative
        return (mean, count, cumulative, min_cumulative), stat

    _, stats = jax.lax.scan(
        step,
        (
            jnp.asarray(mean0, dtype=jnp.float64),
            jnp.asarray(float(initial_count), dtype=jnp.float64),
            jnp.asarray(0.0, dtype=jnp.float64),
            jnp.asarray(0.0, dtype=jnp.float64),
        ),
        monitored,
    )
    return stats


def cusum_stats(monitored: jax.Array, mean0: float, delta: float) -> jax.Array:
    def step(state: jax.Array, x: jax.Array) -> tuple[jax.Array, jax.Array]:
        state = jnp.maximum(0.0, state + x - mean0 - delta)
        return state, state

    _, stats = jax.lax.scan(step, jnp.asarray(0.0, dtype=jnp.float64), monitored)
    return stats


def first_crossing(stats: jax.Array, threshold: float, calibration_window: int) -> int | None:
    hits = np.flatnonzero(np.asarray(stats > threshold))
    if hits.size == 0:
        return None
    return int(calibration_window + int(hits[0]))


def derive_parameters(calibration: jax.Array, spec: dict[str, Any]) -> dict[str, Any]:
    alpha = float(spec["declared_false_positive_rate"])
    calibration_window = int(spec["calibration_window"])
    horizon = int(spec["bootstrap_horizon"])
    mean0 = float(jnp.mean(calibration))
    positive_residuals = jnp.maximum(calibration - mean0, 0.0)
    delta_rank = rank_index(int(positive_residuals.shape[0]), alpha)
    delta = float(jnp.sort(positive_residuals)[delta_rank])
    ph_maxima = []
    cusum_maxima = []
    base_indices = jnp.arange(horizon)
    for offset in range(int(calibration.shape[0])):
        seq = calibration[(base_indices + offset) % calibration.shape[0]]
        ph_maxima.append(float(jnp.max(page_hinkley_stats(seq, mean0, delta, calibration_window))))
        cusum_maxima.append(float(jnp.max(cusum_stats(seq, mean0, delta))))
    threshold_rank = rank_index(len(ph_maxima), alpha)
    tie_guard = 1.0e-12
    return {
        "declared_false_positive_rate": alpha,
        "calibration_window": calibration_window,
        "bootstrap_horizon": horizon,
        "empirical_quantile_rank": threshold_rank,
        "baseline_mean": mean0,
        "page_hinkley": {
            "delta": delta,
            "lambda_threshold": float(jnp.sort(jnp.asarray(ph_maxima, dtype=jnp.float64))[threshold_rank] + tie_guard),
            "derivation": "delta and lambda are empirical calibration cyclic-bootstrap quantiles at 1-alpha, plus numerical tie guard",
        },
        "cusum": {
            "delta": delta,
            "lambda_threshold": float(jnp.sort(jnp.asarray(cusum_maxima, dtype=jnp.float64))[threshold_rank] + tie_guard),
            "derivation": "delta and lambda are empirical calibration cyclic-bootstrap quantiles at 1-alpha, plus numerical tie guard",
        },
    }


def detect(values: jax.Array, params: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    calibration_window = int(spec["calibration_window"])
    monitored = values[calibration_window:]
    mean0 = float(params["baseline_mean"])
    ph_params = params["page_hinkley"]
    cusum_params = params["cusum"]
    ph_stats = page_hinkley_stats(monitored, mean0, float(ph_params["delta"]), calibration_window)
    cu_stats = cusum_stats(monitored, mean0, float(cusum_params["delta"]))
    ph_tick = first_crossing(ph_stats, float(ph_params["lambda_threshold"]), calibration_window)
    cu_tick = first_crossing(cu_stats, float(cusum_params["lambda_threshold"]), calibration_window)
    agree = ph_tick is not None and cu_tick is not None and abs(ph_tick - cu_tick) <= int(spec["agreement_window"])
    dual_tick = max(ph_tick, cu_tick) if agree and ph_tick is not None and cu_tick is not None else None
    return {
        "page_hinkley_detection_tick": ph_tick,
        "cusum_detection_tick": cu_tick,
        "dual_detection_tick": dual_tick,
        "detectors_agree_within_w": agree,
        "statistics": {
            "page_hinkley_max": float(jnp.max(ph_stats)) if ph_stats.shape[0] else 0.0,
            "cusum_max": float(jnp.max(cu_stats)) if cu_stats.shape[0] else 0.0,
            "page_hinkley_final": float(ph_stats[-1]) if ph_stats.shape[0] else 0.0,
            "cusum_final": float(cu_stats[-1]) if cu_stats.shape[0] else 0.0,
        },
    }


def values_from_ticks(ticks: list[dict[str, Any]]) -> jax.Array:
    return jnp.asarray([float(row["surprise_bits"]) for row in ticks], dtype=jnp.float64)


def ticks_for(values: jax.Array, stream_id: str) -> list[dict[str, Any]]:
    return [{"tick": int(i), "stream_id": stream_id, "surprise_bits": float(v)} for i, v in enumerate(np.asarray(values))]


def main() -> int:
    spec = load_spec()
    RESULTS.mkdir(exist_ok=True)
    stationary = stationary_values(int(spec["stationary_ticks"]), int(spec["stream_period"]))
    calibration = stationary[: int(spec["calibration_window"])]
    params = derive_parameters(calibration, spec)

    positive = step_shift(stationary_values(int(spec["positive_ticks"]), int(spec["stream_period"])), int(spec["positive_shift_tick"]), float(spec["positive_shift_size"]))
    positive_result = detect(positive, params, spec)
    positive_delay = None if positive_result["dual_detection_tick"] is None else positive_result["dual_detection_tick"] - int(spec["positive_shift_tick"])

    stationary_result = detect(stationary, params, spec)
    stationary_trigger_count = 0 if stationary_result["dual_detection_tick"] is None else 1
    monitored_ticks = int(spec["stationary_ticks"]) - int(spec["calibration_window"])
    empirical_fpr = stationary_trigger_count / monitored_ticks

    boundary_shift = max(
        float(params["page_hinkley"]["delta"]) + float(params["page_hinkley"]["lambda_threshold"]) / (int(spec["agreement_window"]) + 1),
        float(params["cusum"]["delta"]) + float(params["cusum"]["lambda_threshold"]) / (int(spec["agreement_window"]) + 1),
    )
    boundary = step_shift(stationary_values(int(spec["positive_ticks"]), int(spec["stream_period"])), int(spec["positive_shift_tick"]), boundary_shift)
    boundary_result = detect(boundary, params, spec)

    drift = slow_drift(stationary_values(int(spec["stationary_ticks"]), int(spec["stream_period"])), int(spec["positive_shift_tick"]), float(spec["positive_shift_size"]), horizon=1000)
    drift_result = detect(drift, params, spec)
    drift_delay = None if drift_result["dual_detection_tick"] is None else drift_result["dual_detection_tick"] - int(spec["positive_shift_tick"])

    relabeled_a = detect(values_from_ticks(ticks_for(positive, "stream-A")), params, spec)
    relabeled_b = detect(values_from_ticks(ticks_for(positive, "stream-B")), params, spec)
    label_invariant = relabeled_a["dual_detection_tick"] == relabeled_b["dual_detection_tick"]

    positive_pass = positive_delay is not None and 0 <= positive_delay <= int(spec["agreement_window"])
    stationary_pass = stationary_trigger_count == 0
    label_pass = label_invariant
    all_pass = positive_pass and stationary_pass and label_pass

    scenarios = {
        "positive_known_shift": {
            **positive_result,
            "known_shift_tick": int(spec["positive_shift_tick"]),
            "shift_detected_within": positive_delay,
            "pass": positive_pass,
        },
        "stationary_10k": {
            **stationary_result,
            "dual_trigger_count": stationary_trigger_count,
            "declared_fpr": float(spec["declared_false_positive_rate"]),
            "empirical_fpr": empirical_fpr,
            "pass": stationary_pass,
        },
        "boundary_small_shift_at_threshold": {
            **boundary_result,
            "shift_size": boundary_shift,
            "behavior": "near-threshold shifts are detected only if cumulative evidence crosses both calibration-derived thresholds inside the agreement window",
        },
        "adversarial_slow_drift": {
            **drift_result,
            "drift_horizon": 1000,
            "shift_detected_after": drift_delay,
            "behavior": "slow monotone drift is the known hard case; detectors may trigger late because evidence is spread across many ticks",
        },
        "label_erased": {
            "stream_a_detection_tick": relabeled_a["dual_detection_tick"],
            "stream_b_detection_tick": relabeled_b["dual_detection_tick"],
            "invariant_to_stream_id_relabeling": label_invariant,
            "pass": label_pass,
        },
    }

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "engine_leg_completeness": "FULL",
        "classification": spec["classification"],
        "promotion_allowed": spec["promotion_allowed"],
        "formal_admission_allowed": spec["formal_admission_allowed"],
        "battery_eligible": spec["battery_eligible"],
        "reads_peer_result": False,
        "written_at": now_iso(),
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha256_of(Path(__file__).resolve()),
        "spec_sha256": sha256_of(HERE / "spec.json"),
        "package_versions": {"jax": jax.__version__},
        "detectors": ["page_hinkley", "cusum"],
        "detector_parameters": params,
        "trigger_rule": f"dual trigger requires Page-Hinkley and CUSUM detection ticks within w={spec['agreement_window']}",
        "scenarios": scenarios,
        "positive_tests": {
            "known_shift_detected_within_w": positive_pass,
            "page_hinkley_and_cusum_agree": positive_result["detectors_agree_within_w"],
        },
        "negative_tests": {
            "stationary_10k_zero_dual_triggers": stationary_pass,
            "label_erased_stream_id_invariant": label_pass,
        },
        "boundary_tests": {
            "small_shift_at_threshold_reported": True,
            "slow_drift_behavior_reported_without_promotion": True,
        },
        "facts": {
            "declared_false_positive_rate": float(spec["declared_false_positive_rate"]),
            "empirical_stationary_fpr": empirical_fpr,
            "positive_shift_detected_within": positive_delay,
            "drift_behavior": scenarios["adversarial_slow_drift"]["behavior"],
        },
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "load-bearing x64 stream generation, calibration bootstrap, Page-Hinkley/CUSUM scans"},
            "jax.numpy": {"tried": True, "used": True, "reason": "load-bearing vectorized deterministic surprise stream and threshold derivation arrays"},
            "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON/timestamp/hash result emission"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "jax.numpy": "load_bearing", "python_stdlib": "supportive"},
        "claim_ceiling": spec["claim_ceiling"],
        "all_pass": all_pass,
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": str(RESULT), "positive_delay": positive_delay, "stationary_fpr": empirical_fpr}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
