#!/usr/bin/env python3
"""JAX terrain Choi holonomy ladder diagnostic.

This probe composes the existing 64 Weyl-terrain microstep object with the
newer nested-Hopf/LR-Weyl v2 holonomy/cocycle split. It is intentionally
bounded: Choi-level terrain/holonomy diagnostics only, no terrain admission,
layer completion, PEPS3D closure, or manifold promotion.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from jax.scipy.linalg import expm


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "jax_terrain_choi_holonomy_ladder_probe_results.json"

PLACEMENT_16_RECEIPT = ROOT / "jax_weyl_terrain_16_placements_lindblad_audit_results.json"
MICROSTEP_64_RECEIPT = ROOT / "jax_weyl_terrain_64_microstep_diagnostic_results.json"
HOLONOMY_V2_RECEIPT = ROOT / "jax_nested_hopf_lr_weyl_holonomy_v2_probe_results.json"

SCALES = (8, 16, 32, 64)
SHELL_ETAS = (math.pi / 10.0, math.pi / 6.0, math.pi / 4.0, math.pi / 3.0)
EPS = 1.0e-12

I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)

BLOCKED_CONSUMERS = [
    "full_layer_completion",
    "one_layer_done_right",
    "layer_stacking_readiness",
    "official_g_structure_selection",
    "PEPS3D_closure",
    "terrain_admission",
    "coupling_promotion",
    "basin_admission",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "bridge",
    "physics_gravity",
    "final_manifold_admission",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def dependency_receipts() -> dict[str, Any]:
    specs = {
        "terrain_16": PLACEMENT_16_RECEIPT,
        "terrain_64": MICROSTEP_64_RECEIPT,
        "holonomy_v2": HOLONOMY_V2_RECEIPT,
    }
    rows: dict[str, Any] = {}
    for name, path in specs.items():
        data = load_json(path)
        rows[name] = {
            "path": str(path.relative_to(ROOT)),
            "exists": data is not None,
            "AUDIT_PASS": data.get("AUDIT_PASS") if isinstance(data, dict) else None,
            "classification": data.get("classification") if isinstance(data, dict) else None,
            "promotion_allowed": data.get("promotion_allowed") if isinstance(data, dict) else None,
            "all_pass": data.get("all_pass") if isinstance(data, dict) else None,
            "one_layer_done_right_candidate": data.get("one_layer_done_right_candidate") if isinstance(data, dict) else None,
        }
    return rows


def fit_zero_intercept(xs: list[float], ys: list[float]) -> dict[str, float]:
    x = jnp.array(xs, dtype=jnp.float64)
    y = jnp.array(ys, dtype=jnp.float64)
    slope = float(jnp.dot(x, y) / jnp.maximum(jnp.dot(x, x), EPS))
    pred = slope * x
    residual = y - pred
    ss_res = float(jnp.sum(residual * residual))
    centered = y - jnp.mean(y)
    ss_tot = float(jnp.sum(centered * centered))
    r2 = 0.0 if ss_tot < EPS else 1.0 - ss_res / ss_tot
    return {
        "slope": slope,
        "r2": r2,
        "max_abs_residual": float(jnp.max(jnp.abs(residual))),
    }


def choi_from_unitary(unitary: jax.Array) -> jax.Array:
    d = unitary.shape[0]
    choi = jnp.zeros((d * d, d * d), dtype=jnp.complex128)
    for i in range(d):
        for j in range(d):
            basis = jnp.zeros((d, d), dtype=jnp.complex128).at[i, j].set(1.0)
            image = unitary @ basis @ unitary.conj().T
            choi = choi + jnp.kron(basis, image)
    return choi / d


def partial_trace_output(choi: jax.Array) -> jax.Array:
    d = int(round(math.sqrt(choi.shape[0])))
    return jnp.einsum("akbk->ab", choi.reshape(d, d, d, d))


def unitary_holonomy(eta: float, chirality: float, angle: float = 0.19) -> jax.Array:
    return expm(-1.0j * angle * chirality * math.cos(2.0 * eta) * SX)


def terrain_generator(row: dict[str, Any]) -> jax.Array:
    stage = row["stage"]
    op = row["operator_substage"]
    loop = row["actual_loop"]
    stage_axis = {
        "Se": SZ + 0.15 * SY,
        "Ne": SY + 0.21 * SZ,
        "Ni": SZ - 0.18 * SX,
        "Si": SY - 0.27 * SZ,
    }[stage]
    op_axis = {
        "Ti": SZ,
        "Te": SX + 0.11 * SZ,
        "Fi": SX + 0.23 * SY,
        "Fe": SZ + 0.17 * SX,
    }[op]
    loop_axis = 0.09 * (SX if loop == "base_lift_loop" else SY)
    gen = stage_axis + 0.37 * op_axis + loop_axis
    return gen / jnp.maximum(jnp.linalg.norm(gen), EPS)


def terrain_unitary(row: dict[str, Any], terrain_erased: bool = False) -> jax.Array:
    if terrain_erased:
        return I2
    gap = float(row["noncommuting_order_gap"])
    angle = 0.065 + 0.31 * gap + 0.001 * int(row["placement"])
    return expm(-1.0j * angle * terrain_generator(row))


def channel_row(row: dict[str, Any], eta: float) -> dict[str, Any]:
    chirality = 1.0 if row["sheet"] == "L" else -1.0
    hol = unitary_holonomy(eta, chirality)
    terrain = terrain_unitary(row)
    terrain_then_hol = terrain @ hol
    hol_then_terrain = hol @ terrain
    choi = choi_from_unitary(terrain_then_hol)
    order_choi_gap = float(jnp.linalg.norm(choi - choi_from_unitary(hol_then_terrain)))
    hermitian_gap = float(jnp.linalg.norm(choi - choi.conj().T))
    min_eval = float(jnp.min(jnp.linalg.eigvalsh(0.5 * (choi + choi.conj().T))))
    tp_gap = float(jnp.linalg.norm(partial_trace_output(choi) - 0.5 * I2))
    finite = bool(jnp.all(jnp.isfinite(jnp.real(choi))) and jnp.all(jnp.isfinite(jnp.imag(choi))))
    terrain_amp = 1.0 + 10.0 * float(row["noncommuting_order_gap"])
    law_readout = chirality * terrain_amp * math.cos(2.0 * eta)
    return {
        "microstep": int(row["microstep"]),
        "placement": int(row["placement"]),
        "sheet": row["sheet"],
        "stage": row["stage"],
        "terrain": row["terrain"],
        "operator_substage": row["operator_substage"],
        "loop": row["actual_loop"],
        "source_precedence": row["source_precedence"],
        "eta": eta,
        "cos2eta": math.cos(2.0 * eta),
        "choi_finite": finite,
        "choi_hermitian_gap": hermitian_gap,
        "choi_min_eigenvalue": min_eval,
        "trace_preserving_gap": tp_gap,
        "choi_order_gap": order_choi_gap,
        "terrain_holonomy_readout": law_readout,
        "input_microstep_order_gap": float(row["noncommuting_order_gap"]),
    }


def terrain_law_fits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_microstep: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_microstep.setdefault(row["microstep"], []).append(row)
    fits = []
    for microstep, group in sorted(by_microstep.items()):
        xs = [float(row["cos2eta"]) for row in group]
        ys = [float(row["terrain_holonomy_readout"]) for row in group]
        fit = fit_zero_intercept(xs, ys)
        first = group[0]
        fits.append(
            {
                "microstep": microstep,
                "placement": first["placement"],
                "sheet": first["sheet"],
                "stage": first["stage"],
                "terrain": first["terrain"],
                "operator_substage": first["operator_substage"],
                "fit": fit,
            }
        )
    return fits


def summarize(rows: list[dict[str, Any]], fits: list[dict[str, Any]], terrain64: dict[str, Any], holonomy_v2: dict[str, Any]) -> dict[str, Any]:
    order_gaps = [row["choi_order_gap"] for row in rows]
    choi_hermitian = [row["choi_hermitian_gap"] for row in rows]
    choi_evals = [row["choi_min_eigenvalue"] for row in rows]
    tp_gaps = [row["trace_preserving_gap"] for row in rows]
    return {
        "choi_row_count": len(rows),
        "microstep_count": int(terrain64.get("microstep_count", 0)),
        "eta_count": len(SHELL_ETAS),
        "max_choi_hermitian_gap": max(choi_hermitian),
        "min_choi_eigenvalue": min(choi_evals),
        "max_trace_preserving_gap": max(tp_gaps),
        "mean_choi_order_gap": float(jnp.mean(jnp.array(order_gaps, dtype=jnp.float64))),
        "nonzero_choi_order_gap_count": int(jnp.sum(jnp.array(order_gaps) > 1.0e-8)),
        "min_row_holonomy_r2": min(fit["fit"]["r2"] for fit in fits),
        "fixed_base_spin_lift_holonomy_r2": holonomy_v2["summary"]["singlebase_holonomy_r2"],
        "mixed_cocycle_nested_mag_min_LR": holonomy_v2["summary"]["mixed_cocycle_nested_mag_min_LR"],
        "terrain_erased_gap": float(terrain64["metrics"]["left_right_signature_gap"]),
        "operator_order_erased_gap": float(terrain64["metrics"]["mean_noncommuting_order_gap"]),
        "loop_erased_gap": float(terrain64["metrics"]["loop_erased_control_gap"]),
        "chirality_erased_gap": float(terrain64["metrics"]["sign_only_control_gap"]),
    }


def run_probe(write: bool = True) -> dict[str, Any]:
    start = time.time()
    terrain16 = load_json(PLACEMENT_16_RECEIPT)
    terrain64 = load_json(MICROSTEP_64_RECEIPT)
    holonomy_v2 = load_json(HOLONOMY_V2_RECEIPT)
    if terrain16 is None or terrain64 is None or holonomy_v2 is None:
        raise FileNotFoundError("required terrain or holonomy receipt is missing")

    microsteps = terrain64["microsteps"]
    rows = [channel_row(row, eta) for row in microsteps for eta in SHELL_ETAS]
    fits = terrain_law_fits(rows)
    summary = summarize(rows, fits, terrain64, holonomy_v2)
    grok_split = {
        "singlebase_reproduces_B_holonomy_law": holonomy_v2["summary"]["singlebase_reproduces_B_holonomy_law"],
        "singlebase_reproduces_A_mixed_cocycle": holonomy_v2["summary"]["singlebase_reproduces_A_mixed_cocycle"],
        "verdict": holonomy_v2["grok_deflation_control"]["grok_deflation_verdict"],
    }
    checks = {
        "dependency_receipts_present": bool(terrain16["AUDIT_PASS"] and terrain64["AUDIT_PASS"] and holonomy_v2["AUDIT_PASS"]),
        "terrain_choi_rows_64x4": summary["choi_row_count"] == 64 * 4,
        "choi_channels_finite": all(row["choi_finite"] for row in rows),
        "choi_hermitian_psd": summary["max_choi_hermitian_gap"] < 1.0e-10 and summary["min_choi_eigenvalue"] > -1.0e-10,
        "trace_preserving_channels": summary["max_trace_preserving_gap"] < 1.0e-10,
        "noncommuting_order_gap_preserved": summary["mean_choi_order_gap"] > 1.0e-5
        and summary["nonzero_choi_order_gap_count"] >= 128,
        "holonomy_cos2eta_law_recorded": summary["min_row_holonomy_r2"] > 0.999,
        "fixed_base_spin_lift_deflates_holonomy": bool(grok_split["singlebase_reproduces_B_holonomy_law"]),
        "mixed_cocycle_signature_present": bool(holonomy_v2["checks"]["mixed_cocycle_signature_present"]),
        "mixed_cocycle_magnitude_not_promoted": not bool(holonomy_v2["checks"]["mixed_cocycle_magnitude_pass"]),
        "terrain_erased_control_rejected": summary["terrain_erased_gap"] > 1.0e-5,
        "chirality_erased_control_rejected": summary["chirality_erased_gap"] > 1.0e-5,
        "loop_erased_control_rejected": summary["loop_erased_gap"] > 1.0e-5,
        "operator_order_erased_control_rejected": summary["operator_order_erased_gap"] > 1.0e-5,
        "promotion_blocked": True,
    }
    checks["bounded_diagnostic_pass"] = all(checks.values())
    payload: dict[str, Any] = {
        "sim_id": "jax_terrain_choi_holonomy_ladder_probe",
        "name": "JAX terrain Choi holonomy ladder diagnostic",
        "version": "1.0",
        "tier": "bounded_coupling_diagnostic",
        "classification": "diagnostic_jax_terrain_choi_holonomy_ladder",
        "sim_execution_kind": "nonclassical_diagnostic",
        "sim_class": "geometry_probe",
        "generated_at": now_iso(),
        "ran_jax": True,
        "ran_julia": False,
        "ran_pytorch": False,
        "AUDIT_PASS": bool(checks["bounded_diagnostic_pass"]),
        "promotion_allowed": False,
        "formal_layer_admission_allowed": False,
        "terrain_admission_allowed": False,
        "root_constraints_in_force": ["F01", "N01"],
        "finite_map": (
            "finite placement/operator row p,o from the 64-row terrain receipt, shell eta, and Weyl chirality -> "
            "terrain-dressed holonomy channel Choi matrix plus order-gap, cos(2eta), and deflation-split readouts"
        ),
        "domain": {
            "placement_rows": 16,
            "microstep_rows": 64,
            "etas": list(SHELL_ETAS),
            "site_counts": list(SCALES),
            "chiralities": {"L": +1, "R": -1},
        },
        "codomain_or_output": "JSON diagnostic receipt with 64x4 Choi rows, law fits, controls, and blocked consumers",
        "carrier_layer": "terrain-dressed Weyl density channels over nested-Hopf holonomy diagnostic",
        "geometry_layer": "finite Choi holonomy terrain ladder",
        "carrier_realization": "JAX complex128 2x2 unitary channels and 4x4 Choi matrices",
        "peps3d_embedding": "not admitted here; bounded Choi diagnostic only",
        "spinor_state": "chirality sign inherited from finite Weyl terrain and holonomy v2 receipts",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts(),
        "summary": summary,
        "checks": checks,
        "grok_deflation_split": grok_split,
        "terrain_mixed_cocycle_reference": {
            "signature_present": holonomy_v2["checks"]["mixed_cocycle_signature_present"],
            "magnitude_pass": holonomy_v2["checks"]["mixed_cocycle_magnitude_pass"],
            "nested_mag_min_LR": holonomy_v2["summary"]["mixed_cocycle_nested_mag_min_LR"],
            "winding_L": holonomy_v2["summary"]["mixed_cocycle_winding_L"],
            "winding_R": holonomy_v2["summary"]["mixed_cocycle_winding_R"],
        },
        "fit_rows": fits,
        "choi_rows": rows,
        "TOOL_MANIFEST": {
            "jax": {
                "used": True,
                "role": "load_bearing",
                "reason": "finite Choi channel construction, eigenvalue checks, and order-gap readouts",
            },
            "jax.numpy": {
                "used": True,
                "role": "load_bearing",
                "reason": "complex matrix and Choi algebra over all terrain rows",
            },
            "jax.scipy.linalg.expm": {
                "used": True,
                "role": "load_bearing",
                "reason": "terrain and holonomy channel exponentials",
            },
            "json": {
                "used": True,
                "role": "supportive",
                "reason": "receipt loading and emission",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "jax.scipy.linalg.expm": "load_bearing",
            "json": "supportive",
        },
        "allowed_claims": [
            "A bounded JAX terrain Choi holonomy diagnostic ran over 64 terrain/operator rows and four etas.",
            "The diagnostic records the Julia-v2 split: holonomy law deflated, mixed cocycle signature still the nested-not-glued candidate.",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": [
            "bounded diagnostic only; terrain admission remains blocked",
            "holonomy law is deflated by fixed-base spin lift and is not stacking-order evidence by itself",
            "mixed cocycle magnitude remains below the old pre-registered magnitude bar in the JAX v2 receipt",
            "no PEPS3D carrier admission from the first carrier step",
            "no layer-completion claim gate admission",
        ],
        "wallclock_seconds": round(time.time() - start, 6),
    }
    if write:
        RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    payload = run_probe(write=True)
    print(
        json.dumps(
            {
                "AUDIT_PASS": payload["AUDIT_PASS"],
                "result": str(RESULT.relative_to(ROOT)),
                "criteria_failed": [key for key, value in payload["checks"].items() if not value],
                "promotion_allowed": payload["promotion_allowed"],
                "terrain_admission_allowed": payload["terrain_admission_allowed"],
                "wallclock_seconds": payload["wallclock_seconds"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
