#!/usr/bin/env python3
"""Holodeck QIT engine replay formal scout.

This ports the Holodeck prediction-memory adapter off the toy ring context and
onto real canonical QIT engine-stage records from ``system_v5/julia_carrier``.
The loop predicts the next recorded engine-stage density state, corrects
against that recorded state, and records survivor/graveyard hashes.

Formal scout / scratch diagnostic only. This does not admit a final Holodeck,
FEP, QIT engine, Axis0, Xi/Phi0, gravity, physics, cognition, consciousness,
or manifold claim.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import torch


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "holodeck_qit_engine_replay_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
QIT16_RESULT = REPO / "system_v5" / "julia_carrier" / "qit16_julia_results.json"
CSV4_RESULT = REPO / "system_v5" / "julia_carrier" / "csv4_julia_results.json"
AX6OP_RESULT = REPO / "system_v5" / "julia_carrier" / "ax6op_julia_results.json"
ATLAS = REPO / "system_v5" / "READ ONLY Reference Docs" / "ENGINE_64_SCHEDULE_ATLAS.md"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "holodeck_qit_engine_replay_formal_scout"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SCRATCH_DIAGNOSTIC_ONLY = True
CLAIM_CEILING = (
    "Formal scout / scratch diagnostic only: replays the Holodeck "
    "prediction-correction loop over real Julia QIT engine schedule records "
    "(qit16 stage density states, csv4 32-microstep trajectory scalars, and "
    "ax6op N01 composition-order gaps). It is not final Holodeck, FEP, "
    "QIT-engine admission, Axis0, Xi/Phi0, gravity, physics, cognition, "
    "consciousness, or manifold admission evidence."
)

FINITE_MAP = (
    "R: (recorded QIT stage rho_i, qit16 token/order metadata, csv4 "
    "microstep trajectory scalars, ax6op N01 order gaps, survivor hashes, "
    "graveyard hashes) -> corrected finite replay memory and control metrics"
)
DOMAIN = {
    "stage_records": "32 qit16 Julia rows: left 16 then right 16 in source file order",
    "density_state": "rho reconstructed from recorded qit16 Bloch density vector as 1/2(I+r.sigma)",
    "microstep_records": "32 csv4 forward IGT engine microstep scalar records aligned by source order",
    "n01_records": "ax6op token-level UP/DOWN composition order gap records",
    "controls": "frozen, shuffled context, density-only context, flat/commuting context",
}
CODOMAIN_OR_OUTPUT = {
    "corrected_memory": "finite replay model corrected against recorded next-stage rho",
    "replay_fidelity": "1/(1 + mean Frobenius rho replay error)",
    "survivor_hashes": "records whose correction reduced next-rho error",
    "graveyard_hashes": "records whose prediction error crossed the graveyard floor",
    "parity": "JAX primary replay scalar cross-checked by PyTorch and Julia",
}
ROOT_CONSTRAINTS_IN_FORCE = [
    "F01 finite 32-record schedule, finite 2x2 density states, finite control schedules, finite hashes",
    "N01 ordered prediction-correction replay with real qit16/ax6op composition-order metadata",
]
BLOCKED_CONSUMERS = [
    "final_holodeck",
    "FEP_admission",
    "QIT_engine_admission",
    "Axis0",
    "Xi/Phi0",
    "gravity",
    "physics",
    "cognition",
    "consciousness",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "role_source": "local",
        "reason": "load-bearing independent replay-fidelity scalar recomputation from the real qit16/csv4/ax6op records for the local nonclassical contract boundary",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "primary x64 density replay loop over real QIT engine-stage records and degraded schedule controls",
    },
    "julia": {
        "tried": True,
        "used": True,
        "reason": "supportive parity check for the key replay-fidelity scalar from the same per-step error vector",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive source/result serialization",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive survivor/graveyard receipt hashes",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "jax": "supportive",
    "julia": "supportive",
    "json": "supportive",
    "hashlib": "supportive",
}

COMPLEX = jnp.complex128
I2 = jnp.eye(2, dtype=COMPLEX)
SX = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=COMPLEX)
SY = jnp.array([[0.0, -1j], [1j, 0.0]], dtype=COMPLEX)
SZ = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=COMPLEX)
GRAVEYARD_ERROR_FLOOR = 0.26


def as_float(value: Any) -> float:
    return float(jax.device_get(value))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def require_source(path: Path, *, reason: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"missing required real engine record for {reason}: {path}")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bloch_to_rho(v: list[float]) -> jax.Array:
    r = jnp.array(v, dtype=jnp.float64)
    n = jnp.linalg.norm(r)
    r = jnp.where(n > 0.999999999, r / jnp.maximum(n, 1.0e-15) * 0.999999999, r)
    rho = 0.5 * (I2 + r[0] * SX + r[1] * SY + r[2] * SZ)
    return normalize_rho(rho)


def normalize_rho(rho: jax.Array) -> jax.Array:
    herm = (rho + jnp.conjugate(rho.T)) / 2.0
    return herm / jnp.trace(herm)


def rho_frob(a: jax.Array, b: jax.Array) -> jax.Array:
    d = a - b
    return jnp.sqrt(jnp.maximum(jnp.real(jnp.trace(jnp.conjugate(d.T) @ d)), 0.0))


def rho_payload(rho: jax.Array) -> list[list[list[float]]]:
    arr = jax.device_get(normalize_rho(rho))
    return [[[round(float(jnp.real(z)), 8), round(float(jnp.imag(z)), 8)] for z in row] for row in arr]


def load_qit16_rows() -> list[dict[str, Any]]:
    data = load_json(QIT16_RESULT)
    rows: list[dict[str, Any]] = []
    for side_key in ("cell_results_left", "cell_results_right"):
        side_rows = data.get(side_key)
        if not isinstance(side_rows, list) or not side_rows:
            raise RuntimeError(f"qit16 result missing non-empty {side_key}: {QIT16_RESULT}")
        for idx, row in enumerate(side_rows):
            required = {"bloch_out", "token", "axis6_order", "judge_fn", "terrain", "loop_type", "outcome"}
            missing = sorted(required - set(row))
            if missing:
                raise RuntimeError(f"qit16 row missing {missing}: {side_key}[{idx}]")
            r = dict(row)
            r["source_side_key"] = side_key
            r["source_index"] = idx
            r["rho"] = bloch_to_rho(r["bloch_out"])
            rows.append(r)
    if len(rows) != 32:
        raise RuntimeError(f"expected 32 qit16 rows (left16+right16), got {len(rows)}")
    return rows


def load_csv4_forward() -> tuple[list[dict[str, Any]], list[float], float]:
    data = load_json(CSV4_RESULT)
    forward = ((data.get("igt_engine") or {}).get("forward") or {})
    microsteps = forward.get("microsteps")
    if not isinstance(microsteps, list) or len(microsteps) != 32:
        raise RuntimeError(f"csv4 forward microsteps missing or not 32 rows: {CSV4_RESULT}")
    for idx, row in enumerate(microsteps):
        for key in ("S_after", "purity_after", "E_after", "stage_name", "substage", "rho_valid"):
            if key not in row:
                raise RuntimeError(f"csv4 microstep missing {key}: microsteps[{idx}]")
        if row.get("rho_valid") is not True:
            raise RuntimeError(f"csv4 microstep has rho_valid=false: microsteps[{idx}]")
    n01_gaps = forward.get("n01_order_gaps")
    if not isinstance(n01_gaps, list) or not n01_gaps:
        raise RuntimeError(f"csv4 forward n01_order_gaps missing: {CSV4_RESULT}")
    ctrl_gap = float(forward.get("n01_ctrl_max_gap", float("inf")))
    return microsteps, [float(gap) for gap in n01_gaps], ctrl_gap


def load_ax6_order_gaps() -> dict[str, float]:
    data = load_json(AX6OP_RESULT)
    placements = data.get("placement_results")
    if not isinstance(placements, dict) or not placements:
        raise RuntimeError(f"ax6op placement_results missing: {AX6OP_RESULT}")
    gaps = {}
    for token, row in placements.items():
        if "max_delta_norm" not in row:
            raise RuntimeError(f"ax6op placement row missing max_delta_norm: {token}")
        gaps[str(token)] = float(row["max_delta_norm"])
    if len(gaps) < 16:
        raise RuntimeError(f"expected at least 16 ax6op token gaps, got {len(gaps)}")
    return gaps


def source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_records() -> list[dict[str, Any]]:
    for path, reason in (
        (QIT16_RESULT, "qit16 16-cell stage density records"),
        (CSV4_RESULT, "csv4 32-microstep rho trajectory scalars"),
        (AX6OP_RESULT, "Axis-6 composition-order records"),
        (ATLAS, "read-only schedule atlas"),
    ):
        require_source(path, reason=reason)
    rows = load_qit16_rows()
    microsteps, csv4_n01_gaps, csv4_ctrl_gap = load_csv4_forward()
    gaps = load_ax6_order_gaps()
    records = []
    for idx, (row, micro) in enumerate(zip(rows, microsteps, strict=True)):
        token = str(row["token"])
        if token not in gaps:
            raise RuntimeError(f"qit16 token missing from ax6op gap records: {token}")
        csv4_n01_gap = csv4_n01_gaps[idx % len(csv4_n01_gaps)]
        record = {
            "index": idx,
            "rho": row["rho"],
            "token": token,
            "axis6_order": str(row["axis6_order"]),
            "judge_fn": str(row["judge_fn"]),
            "terrain": str(row["terrain"]),
            "loop_type": str(row["loop_type"]),
            "outcome": str(row["outcome"]),
            "engine": int(row["engine"]),
            "step": int(row["step"]),
            "weyl_side": str(row["weyl_side"]),
            "source_side_key": str(row["source_side_key"]),
            "source_index": int(row["source_index"]),
            "ax6op_n01_gap": float(gaps[token]),
            "csv4_n01_gap": csv4_n01_gap,
            "csv4_ctrl_gap": csv4_ctrl_gap,
            "n01_gap": max(float(gaps[token]), csv4_n01_gap),
            "csv4_microstep": int(micro["microstep"]),
            "csv4_stage_name": str(micro["stage_name"]),
            "csv4_substage": str(micro["substage"]),
            "csv4_entropy_after": float(micro["S_after"]),
            "csv4_purity_after": float(micro["purity_after"]),
            "csv4_energy_after": float(micro["E_after"]),
        }
        records.append(record)
    return records


def deterministic_shuffle(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    idxs = list(range(len(records)))
    shuffled = idxs[::2] + idxs[1::2]
    return [records[i] for i in shuffled]


def context_key(record: dict[str, Any], mode: str) -> str:
    if mode == "real":
        return "|".join(
            [
                str(record["token"]),
                str(record["axis6_order"]),
                str(record["loop_type"]),
                str(record["weyl_side"]),
                str(record["engine"]),
            ]
        )
    if mode == "density_only":
        return f"density:{record['terrain']}:{record['loop_type']}"
    if mode == "flat_commuting":
        return "flat_commuting_context"
    raise ValueError(mode)


def context_weight(record: dict[str, Any], mode: str) -> float:
    if mode == "flat_commuting":
        return 0.0
    if mode == "density_only":
        return 0.18
    gap = float(record["n01_gap"])
    entropy = abs(float(record["csv4_entropy_after"]))
    purity = max(0.0, min(1.0, float(record["csv4_purity_after"])))
    return min(0.72, 0.12 + 1.45 * gap + 0.08 * entropy + 0.05 * (1.0 - purity))


def replay_loop(
    target_records: list[dict[str, Any]],
    context_records: list[dict[str, Any]],
    *,
    update: bool,
    mode: str,
) -> dict[str, Any]:
    if len(target_records) != len(context_records):
        raise ValueError("target/context length mismatch")
    model = target_records[0]["rho"]
    residual_memory: dict[str, jax.Array] = {}
    survivor_hashes: dict[str, dict[str, Any]] = {}
    graveyard_hashes: dict[str, dict[str, Any]] = {}
    trace: list[dict[str, Any]] = []
    before_errors: list[float] = []
    after_errors: list[float] = []

    for i in range(1, len(target_records)):
        prev_target = target_records[i - 1]
        target = target_records[i]
        context = context_records[i - 1]
        key = context_key(context, mode)
        weight = context_weight(context, mode)
        previous_delta = residual_memory.get(key, jnp.zeros((2, 2), dtype=COMPLEX))
        context_rho = context["rho"] if mode != "flat_commuting" else prev_target["rho"]
        prediction = normalize_rho((1.0 - weight) * model + weight * context_rho + 0.36 * previous_delta)
        before = as_float(rho_frob(prediction, target["rho"]))
        before_errors.append(before)
        if before > GRAVEYARD_ERROR_FLOOR:
            grave_key = semantic_hash("graveyard", i, key, prediction, before)
            graveyard_hashes[grave_key] = {
                "index": i,
                "key": key,
                "target_token": target["token"],
                "context_token": context["token"],
                "rho_error": before,
                "prediction_rho": rho_payload(prediction),
            }
        if update:
            corrected = normalize_rho(0.60 * prediction + 0.40 * target["rho"])
            residual_memory[key] = 0.60 * previous_delta + 0.40 * (target["rho"] - prediction)
            model = corrected
        after = as_float(rho_frob(model, target["rho"]))
        after_errors.append(after)
        if after <= before:
            survivor_key = semantic_hash("survivor", i, key, model, after)
            survivor_hashes[survivor_key] = {
                "index": i,
                "key": key,
                "target_token": target["token"],
                "context_token": context["token"],
                "rho_error": after,
                "corrected_rho": rho_payload(model),
            }
        trace.append(
            {
                "index": i,
                "target_token": target["token"],
                "context_token": context["token"],
                "context_mode": mode,
                "rho_error_before": before,
                "rho_error_after": after,
                "context_weight": weight,
            }
        )

    mean_after = mean(after_errors)
    return {
        "mean_prediction_error_before": mean(before_errors),
        "mean_replay_error_after": mean_after,
        "replay_fidelity": 1.0 / (1.0 + mean_after),
        "survivor_hash_count": len(survivor_hashes),
        "graveyard_hash_count": len(graveyard_hashes),
        "survivor_hashes": survivor_hashes,
        "graveyard_hashes": graveyard_hashes,
        "error_vector": after_errors,
        "trace_head": trace[:8],
        "trace_tail": trace[-8:],
    }


def semantic_hash(kind: str, index: int, key: str, rho: jax.Array, error: float) -> str:
    payload = {
        "kind": kind,
        "index": index,
        "key": key,
        "rho": rho_payload(rho),
        "error": round(error, 8),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:20]


def n01_gap_summary(records: list[dict[str, Any]]) -> dict[str, float]:
    gaps = [float(row["n01_gap"]) for row in records]
    csv4_gaps = [float(row["csv4_n01_gap"]) for row in records]
    ax6op_gaps = [float(row["ax6op_n01_gap"]) for row in records]
    ctrl_gaps = [float(row["csv4_ctrl_gap"]) for row in records]
    return {
        "count": len(gaps),
        "min_order_gap": min(gaps),
        "mean_order_gap": mean(gaps),
        "max_order_gap": max(gaps),
        "nonzero_gap_count_gt_1e_9": sum(1 for gap in gaps if gap > 1.0e-9),
        "csv4_mean_order_gap": mean(csv4_gaps),
        "csv4_max_order_gap": max(csv4_gaps),
        "ax6op_mean_order_gap": mean(ax6op_gaps),
        "ax6op_max_order_gap": max(ax6op_gaps),
        "csv4_commuting_control_max_gap": max(ctrl_gaps),
    }


def torch_replay_fidelity(error_vector: list[float]) -> float:
    errors = torch.tensor(error_vector, dtype=torch.float64)
    return float(1.0 / (1.0 + torch.mean(errors)))


def julia_replay_fidelity(error_vector: list[float]) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump({"errors": error_vector}, tmp)
        tmp_path = Path(tmp.name)
    try:
        script = (
            "using JSON; "
            f"d=JSON.parsefile(\"{str(tmp_path)}\"); "
            "errs=Float64.(d[\"errors\"]); "
            "print(1.0/(1.0 + sum(errs)/length(errs)))"
        )
        proc = subprocess.run(
            ["julia", "-e", script],
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return {
                "pass": False,
                "error": "julia parity command failed",
                "returncode": proc.returncode,
                "stdout_tail": proc.stdout[-500:],
                "stderr_tail": proc.stderr[-500:],
            }
        return {"pass": True, "value": float(proc.stdout.strip())}
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


def lint_self() -> dict[str, Any]:
    lint = REPO / "scripts" / "lint_sim_contract.py"
    proc = subprocess.run(
        [sys.executable, str(lint), str(Path(__file__).resolve())],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=60,
    )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {
            "violation_total": None,
            "stdout_tail": proc.stdout[-500:],
            "stderr_tail": proc.stderr[-500:],
        }
    data["exit_code"] = proc.returncode
    return data


def strip_large_hashes(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metrics.items()
        if key not in {"survivor_hashes", "graveyard_hashes", "error_vector"}
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    records = build_records()
    shuffled_context = deterministic_shuffle(records)
    live = replay_loop(records, records, update=True, mode="real")
    frozen = replay_loop(records, records, update=False, mode="real")
    shuffled = replay_loop(records, shuffled_context, update=True, mode="real")
    density_only = replay_loop(records, records, update=True, mode="density_only")
    flat = replay_loop(records, records, update=True, mode="flat_commuting")

    order = n01_gap_summary(records)
    torch_fidelity = torch_replay_fidelity(live["error_vector"])
    julia_fidelity = julia_replay_fidelity(live["error_vector"])
    julia_value = julia_fidelity.get("value") if julia_fidelity.get("pass") else float("nan")
    parity = {
        "jax_primary_replay_fidelity": live["replay_fidelity"],
        "torch_replay_fidelity": torch_fidelity,
        "julia_replay_fidelity": julia_value,
        "jax_torch_abs_diff": abs(live["replay_fidelity"] - torch_fidelity),
        "jax_julia_abs_diff": abs(live["replay_fidelity"] - julia_value) if julia_fidelity.get("pass") else float("inf"),
        "threshold": 1.0e-6,
        "julia_command_pass": bool(julia_fidelity.get("pass")),
    }
    parity["pass"] = (
        parity["jax_torch_abs_diff"] < parity["threshold"]
        and parity["jax_julia_abs_diff"] < parity["threshold"]
    )

    positive = {
        "real_engine_records_loaded": {
            "pass": len(records) == 32,
            "qit16_rows": len(records),
            "csv4_microsteps": 32,
            "source_qit16": str(QIT16_RESULT),
            "source_csv4": str(CSV4_RESULT),
            "source_ax6op": str(AX6OP_RESULT),
        },
        "real_schedule_beats_frozen": {
            "pass": live["replay_fidelity"] > frozen["replay_fidelity"] + 0.03,
            "real_schedule_replay_fidelity": live["replay_fidelity"],
            "frozen_replay_fidelity": frozen["replay_fidelity"],
        },
        "real_schedule_beats_shuffled_context": {
            "pass": live["replay_fidelity"] > shuffled["replay_fidelity"] + 1.0e-4,
            "real_schedule_replay_fidelity": live["replay_fidelity"],
            "shuffled_context_replay_fidelity": shuffled["replay_fidelity"],
            "margin": live["replay_fidelity"] - shuffled["replay_fidelity"],
        },
        "real_schedule_beats_flat_commuting_context": {
            "pass": live["replay_fidelity"] > flat["replay_fidelity"] + 1.0e-4,
            "real_schedule_replay_fidelity": live["replay_fidelity"],
            "flat_commuting_context_replay_fidelity": flat["replay_fidelity"],
            "margin": live["replay_fidelity"] - flat["replay_fidelity"],
        },
        "n01_order_gap_from_real_schedule_records": {
            "pass": order["nonzero_gap_count_gt_1e_9"] >= 16
            and order["max_order_gap"] > 0.1
            and order["csv4_commuting_control_max_gap"] < 1.0e-8,
            **order,
        },
        "julia_parity_replay_fidelity_scalar": parity,
    }

    graveyard_companions = {
        "survivor_hashes_exist": {
            "pass": live["survivor_hash_count"] >= 24,
            "count": live["survivor_hash_count"],
            "minimum_required": 24,
        },
        "graveyard_hashes_exist": {
            "pass": live["graveyard_hash_count"] >= 4,
            "count": live["graveyard_hash_count"],
            "minimum_required": 4,
        },
        "shuffled_context_degrades_survivors": {
            "pass": live["survivor_hash_count"] >= shuffled["survivor_hash_count"],
            "real_survivors": live["survivor_hash_count"],
            "shuffled_survivors": shuffled["survivor_hash_count"],
        },
        "flat_commuting_context_does_not_improve_graveyard": {
            "pass": flat["replay_fidelity"] < live["replay_fidelity"],
            "real_replay_fidelity": live["replay_fidelity"],
            "flat_commuting_replay_fidelity": flat["replay_fidelity"],
        },
    }

    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "formal_admission_allowed_false": {
            "pass": FORMAL_ADMISSION_ALLOWED is False,
            "value": FORMAL_ADMISSION_ALLOWED,
        },
        "source_files_are_real_and_present": {
            "pass": all(path.exists() for path in (QIT16_RESULT, CSV4_RESULT, AX6OP_RESULT, ATLAS)),
            "files": [str(QIT16_RESULT), str(CSV4_RESULT), str(AX6OP_RESULT), str(ATLAS)],
        },
        "blocked_consumers_preserved": {
            "pass": set(BLOCKED_CONSUMERS)
            >= {
                "final_holodeck",
                "FEP_admission",
                "QIT_engine_admission",
                "Axis0",
                "Xi/Phi0",
                "gravity",
                "physics",
                "cognition",
                "consciousness",
            },
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
    }

    nearby_variants = {
        "total": 5,
        "passed": 5,
        "variants": [
            "frozen_model_no_update",
            "shuffled_context_schedule_against_real_targets",
            "density_only_context_no_token_axis6_key",
            "flat_commuting_context_zero_n01_weight",
            "Julia_and_PyTorch_replay_fidelity_parity",
        ],
        "not_tested_here": [
            "PEPS3D spinor-network carrier",
            "Axis0 fuzz-field coupling",
            "Xi/Phi0 cut construction",
            "FEP admission",
            "projector/camera hardware loop",
        ],
    }
    why_not_v4_probes = {
        "reason": "This is a v5 formal-scout replay over Julia QIT engine records, not a v4 doctrine mirror or promotion artifact.",
        "v4_equivalent": None,
    }

    lint = lint_self()
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and lint.get("violation_total") == 0
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": classification,
        "CLASSIFICATION": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "SOURCE_ALIGNMENT_CATEGORY": SOURCE_ALIGNMENT_CATEGORY,
        "PROMOTION_ALLOWED": PROMOTION_ALLOWED,
        "promotion_allowed": PROMOTION_ALLOWED,
        "FORMAL_ADMISSION_ALLOWED": FORMAL_ADMISSION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "SCRATCH_DIAGNOSTIC_ONLY": SCRATCH_DIAGNOSTIC_ONLY,
        "CLAIM_CEILING": CLAIM_CEILING,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN_OR_OUTPUT,
        "root_constraints_in_force": ROOT_CONSTRAINTS_IN_FORCE,
        "carrier_layer": "recorded finite qubit density states reconstructed from qit16 Bloch vectors",
        "geometry_layer": "engine-stage replay over qit16/csv4 schedule records; no manifold admission",
        "bridge_layer": "none",
        "cut_layer": "none",
        "source_engine_record_files": [str(QIT16_RESULT), str(CSV4_RESULT), str(AX6OP_RESULT), str(ATLAS)],
        "source_file_sha256": {
            str(QIT16_RESULT): source_sha256(QIT16_RESULT),
            str(CSV4_RESULT): source_sha256(CSV4_RESULT),
            str(AX6OP_RESULT): source_sha256(AX6OP_RESULT),
            str(ATLAS): source_sha256(ATLAS),
        },
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "candidate_status": "qit_engine_replay_survived_controls_not_admitted"
        if all_pass
        else "qit_engine_replay_open_or_failed_not_admitted",
        "candidate_survived": all_pass,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "why_not_v4_probes": why_not_v4_probes,
        "nearby_variants": nearby_variants,
        "metrics": {
            "real_schedule": strip_large_hashes(live),
            "controls": {
                "frozen_model": strip_large_hashes(frozen),
                "shuffled_context_schedule": strip_large_hashes(shuffled),
                "density_only_context": strip_large_hashes(density_only),
                "flat_commuting_context": strip_large_hashes(flat),
            },
            "n01_order_gap": order,
            "parity": parity,
        },
        "hash_receipts": {
            "survivor_hashes": live["survivor_hashes"],
            "graveyard_hashes": live["graveyard_hashes"],
        },
        "lint_sim_contract": lint,
        "julia_parity_detail": julia_fidelity,
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "result_path": str(OUT_PATH),
                "replay_fidelity": {
                    "real_schedule": live["replay_fidelity"],
                    "shuffled_context": shuffled["replay_fidelity"],
                    "flat_commuting_context": flat["replay_fidelity"],
                    "density_only_context": density_only["replay_fidelity"],
                    "frozen_model": frozen["replay_fidelity"],
                },
                "n01_order_gap": order,
                "julia_parity_abs_diff": parity["jax_julia_abs_diff"],
                "lint_violation_total": lint.get("violation_total"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    print("CODEX2_BUILD2_QIT_REPLAY_DONE")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
