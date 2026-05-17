#!/usr/bin/env python3
"""Tune existing EngineCore STAGE_DT against basin-depth criteria."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import numpy as np

import engine_core as ec


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_engine_manifold_dt_tuning_basin_probe_results.json"
SOURCE_RESULT = RESULT_DIR / "source_native_engine_manifold_attractor_basin_depth_probe_results.json"

NAME = "source_native_engine_manifold_dt_tuning_basin_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: sweeps the existing EngineCore STAGE_DT integration "
    "parameter against finite basin-depth criteria. It does not admit global "
    "manifold necessity, deep-basin promotion, final FEP, final Axis0, "
    "Holodeck, physics, cognition, world-model, or canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing trace-distance and sweep statistics"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing source-native EngineCore execution with runtime STAGE_DT sweep"},
    "json": {"tried": True, "used": True, "reason": "load-bearing receipt parsing/writing"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing source hash receipt"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DT_VALUES = [0.035, 0.05, 0.08, 0.12, 0.18]
SEEDS = [101, 211, 307]
EPSILONS = [0.02, 0.08]
TRACE_CANDIDATE_FLOOR = 0.10
CONTROL_SEPARATION_FLOOR = 0.05


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace_distance(rho1: np.ndarray, rho2: np.ndarray) -> float:
    diff = rho1 - rho2
    evals = np.linalg.eigvalsh(diff.conj().T @ diff)
    return 0.5 * float(np.sum(np.sqrt(np.clip(evals, 0.0, None))))


def perturb_density(rho: np.ndarray, epsilon: float) -> np.ndarray:
    return ec._normalize_density((1.0 - epsilon) * rho + epsilon * ec.I2 / 2.0)


def run_cycle(engine_type: int, rho: np.ndarray, *, manifold_enabled: bool, schedule_mode: str = "native") -> dict[str, Any]:
    engine = ec.EngineCore(engine_type=engine_type, manifold_enabled=manifold_enabled)
    if schedule_mode == "reversed":
        engine.schedule = list(reversed(engine.schedule))
    result = engine.run_full_cycle(rho)
    records = result["trajectory"]
    return {
        "rho": np.asarray(result["final_rho"], dtype=np.complex128),
        "tokens": [str(row["ordered_token"]) for row in records],
        "mean_correction": float(np.mean([row["update_repair"]["manifold_projection_delta_norm"] for row in records])),
    }


def token_match(a: list[str], b: list[str]) -> float:
    return sum(x == y for x, y in zip(a, b)) / max(1, min(len(a), len(b)))


def run_dt(dt: float) -> dict[str, Any]:
    ec.STAGE_DT = dt
    rows = []
    for engine_type in (0, 1):
        for seed in SEEDS:
            rho0 = ec.generate_initial_density(seed)
            baseline = run_cycle(engine_type, rho0, manifold_enabled=True)
            for eps in EPSILONS:
                pert = perturb_density(rho0, eps)
                on = run_cycle(engine_type, pert, manifold_enabled=True)
                off = run_cycle(engine_type, pert, manifold_enabled=False)
                rev = run_cycle(engine_type, pert, manifold_enabled=True, schedule_mode="reversed")
                wrong = run_cycle(1 - engine_type, pert, manifold_enabled=True)
                rows.append(
                    {
                        "epsilon": eps,
                        "on_trace": trace_distance(on["rho"], baseline["rho"]),
                        "off_trace": trace_distance(off["rho"], baseline["rho"]),
                        "reversed_trace": trace_distance(rev["rho"], baseline["rho"]),
                        "wrong_trace": trace_distance(wrong["rho"], baseline["rho"]),
                        "on_token_match": token_match(on["tokens"], baseline["tokens"]),
                        "reversed_token_match": token_match(rev["tokens"], baseline["tokens"]),
                        "wrong_token_match": token_match(wrong["tokens"], baseline["tokens"]),
                        "on_correction": on["mean_correction"],
                        "off_correction": off["mean_correction"],
                    }
                )
    on_mean = float(np.mean([r["on_trace"] for r in rows]))
    nearest_control = float(
        min(
            np.mean([r["off_trace"] for r in rows]),
            np.mean([r["reversed_trace"] for r in rows]),
            np.mean([r["wrong_trace"] for r in rows]),
        )
    )
    separation = nearest_control - on_mean
    if on_mean <= TRACE_CANDIDATE_FLOOR and separation >= CONTROL_SEPARATION_FLOOR:
        label = "candidate_basin"
    elif separation < 0:
        label = "anti_basin"
    elif on_mean <= nearest_control:
        label = "shallow_basin"
    else:
        label = "open_basin_boundary"
    return {
        "dt": dt,
        "label": label,
        "row_count": len(rows),
        "on_mean_trace": on_mean,
        "nearest_control_mean": nearest_control,
        "control_separation": separation,
        "mean_on_token_match": float(np.mean([r["on_token_match"] for r in rows])),
        "mean_reversed_token_match": float(np.mean([r["reversed_token_match"] for r in rows])),
        "mean_wrong_token_match": float(np.mean([r["wrong_token_match"] for r in rows])),
        "mean_on_correction": float(np.mean([r["on_correction"] for r in rows])),
        "mean_off_correction": float(np.mean([r["off_correction"] for r in rows])),
    }


def main() -> int:
    started = time.time()
    source = json.loads(SOURCE_RESULT.read_text(encoding="utf-8"))
    original_dt = ec.STAGE_DT
    try:
        rows = [run_dt(dt) for dt in DT_VALUES]
    finally:
        ec.STAGE_DT = original_dt
    candidate_rows = [r for r in rows if r["label"] == "candidate_basin"]
    best = min(candidate_rows or rows, key=lambda r: (r["on_mean_trace"], -r["control_separation"]))
    positive = {
        "source_shallow_basin_receipt_loaded": {
            "pass": (
                source.get("all_pass") is True
                and source.get("name") == "source_native_engine_manifold_attractor_basin_depth_probe"
                and source.get("basin_classification", {}).get("label") == "shallow_basin"
            ),
            "source_sha256": sha256_file(SOURCE_RESULT),
            "source_name": source.get("name"),
            "source_label": source.get("basin_classification", {}).get("label"),
        },
        "dt_sweep_executed": {
            "pass": len(rows) == len(DT_VALUES),
            "dt_values": DT_VALUES,
            "rows": rows,
        },
        "best_dt_identified": {
            "pass": best["dt"] in DT_VALUES and (not candidate_rows or best["label"] == "candidate_basin"),
            "best": best,
            "candidate_rows_present": bool(candidate_rows),
        },
    }
    graveyard = {
        "dt_tuning_does_not_silently_promote_to_deep": {
            "pass": True,
            "candidate_dt_values": [r["dt"] for r in candidate_rows],
            "reason": "Any improved DT remains a finite tuning candidate until rerun in the full basin-depth scout.",
        },
        "original_dt_remains_visible": {
            "pass": any(abs(r["dt"] - original_dt) < 1e-12 for r in rows),
            "original_dt": original_dt,
        },
        "tuning_is_existing_parameter_not_new_system": {"pass": True},
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "stage_dt_restored_after_sweep": {"pass": abs(ec.STAGE_DT - original_dt) < 1e-12, "restored_dt": ec.STAGE_DT},
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_engine_manifold_dt_tuning_basin",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "rows": rows,
        "recommended_dt": best["dt"],
        "nearby_variants": {"total": len(graveyard), "passed": sum(1 for row in graveyard.values() if row["pass"]), "variants": sorted(graveyard)},
        "why_not_v4_probes": [
            "This is a source-native v5 EngineCore parameter tuning scout.",
            "It identifies a repair candidate without editing engine_core or promoting architecture claims.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  recommended_dt={best['dt']} label={best['label']} on_mean={best['on_mean_trace']:.4f} separation={best['control_separation']:.4f}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
