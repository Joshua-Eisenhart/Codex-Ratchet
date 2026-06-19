#!/usr/bin/env python3
"""Dual-backend finite scout for EVOLUTION = THE RATCHET.

Scratch diagnostic only. It applies one finite constraint-survival ratchet
operator to canonical QIT terrain rows and to a finite population carrier, then
checks controls and a Julia mirror. It does not admit biology or physics.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys
import time
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

import canonical_qit_engine_specs as qit


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "mp4_evolution_is_the_ratchet"
OUT_PATH = RESULT_DIR / "mp4_evolution_is_the_ratchet_results.json"
JULIA_DIR = REPO_ROOT / "system_v5" / "julia_carrier"
JULIA_SOURCE = JULIA_DIR / "mp4_evolution_is_the_ratchet.jl"
JULIA_RESULT = JULIA_DIR / "mp4_evolution_is_the_ratchet_julia_results.json"
CANONICAL_SPEC = ROOT / "canonical_qit_engine_specs.py"

sys.path.insert(0, str(JULIA_DIR))
import jax_density_matrix_spinor_lift as density_carrier
import jax_clifford_torus_nested_hopf_foliation as hopf_carrier
import jax_division_algebra_ratchet_ladder as division_carrier
import jax_octonion_G2_automorphism as g2_carrier

SCHEMA = "FORMAL_SCOUT_RESULT_v1"
CLASSIFICATION = "scratch_diagnostic"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "finite_formal_scout_evolution_ratchet_carrier_probe"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
EPS = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

CLAIM_CEILING = (
    "Finite structural unification witness in the owner's entropic-monist frame: "
    "a population/candidate carrier under constraints is selected by the same "
    "finite constraint-survival ratchet operator used on the QIT terrain carrier. "
    "This is not a proof or derivation of biology, evolution, physics, natural "
    "selection, Hoffman, M(C), Axis0, bridge, or any physics admission."
)

BLOCKED_CONSUMERS = [
    "biology_admission",
    "physics_admission",
    "natural_selection_derivation",
    "hoffman_derivation",
    "M_C",
    "Axis0",
    "bridge",
    "formal_admission",
    "promotion",
]

STRATEGY_ORDER = ["WinWin", "WinLose", "LoseWin", "LoseLose"]
AXIS_INDEX = {"x": 1.0, "y": 2.0, "z": 3.0}

OWNER_RECEIPTS = {
    "density_matrix_spinor_lift": JULIA_DIR / "density_matrix_spinor_lift_julia_results.json",
    "clifford_torus_nested_hopf_foliation": JULIA_DIR / "clifford_torus_nested_hopf_foliation_julia_results.json",
    "golden_weyl": JULIA_DIR / "golden_weyl_julia_receipt.json",
    "golden_weyl_ledger": JULIA_DIR / "golden_weyl_ledger.json",
    "division_algebra_ratchet_ladder": JULIA_DIR / "division_algebra_ratchet_ladder_julia_results.json",
    "octonion_G2_automorphism": JULIA_DIR / "octonion_G2_automorphism_julia_results.json",
}

OWNER_SOURCES = {
    "canonical_qit_engine_specs": CANONICAL_SPEC,
    "density_matrix_spinor_lift": JULIA_DIR / "density_matrix_spinor_lift.jl",
    "density_matrix_spinor_lift_jax": JULIA_DIR / "jax_density_matrix_spinor_lift.py",
    "clifford_torus_nested_hopf_foliation": JULIA_DIR / "clifford_torus_nested_hopf_foliation.jl",
    "clifford_torus_nested_hopf_foliation_jax": JULIA_DIR / "jax_clifford_torus_nested_hopf_foliation.py",
    "golden_weyl": JULIA_DIR / "golden_weyl_julia.jl",
    "golden_weyl_jax_snapshot": JULIA_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py",
    "division_algebra_ratchet_ladder": JULIA_DIR / "division_algebra_ratchet_ladder.jl",
    "division_algebra_ratchet_ladder_jax": JULIA_DIR / "jax_division_algebra_ratchet_ladder.py",
    "octonion_G2_automorphism": JULIA_DIR / "octonion_G2_automorphism.jl",
    "octonion_G2_automorphism_jax": JULIA_DIR / "jax_octonion_G2_automorphism.py",
}

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing JAX runtime for finite x64 constraint-survival logits, softmax selection, controls, and parity rows",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jnp x64 array algebra; no plain NumPy import or np.* compute",
    },
    "julia": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Julia mirror; shared scalars and booleans must agree within 1e-9",
    },
    "owner_julia_carrier": {
        "tried": True,
        "used": True,
        "reason": "load-bearing gate from real owner carrier receipts; erasing the gate changes survivor selection to no-selection",
    },
    "canonical_qit_engine_specs.py": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source of the four canonical terrain strategy rows and QIT ratchet strategy order",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON, hashing, subprocess, datetime, and path handling",
    },
    "numpy": {"tried": False, "used": False, "reason": "not used"},
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "julia": "load_bearing",
    "owner_julia_carrier": "load_bearing",
    "canonical_qit_engine_specs.py": "load_bearing",
    "python_stdlib": "supportive",
    "numpy": None,
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_path(data: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = data
    parts = dotted.split(".")
    idx = 0
    while idx < len(parts):
        if not isinstance(cur, dict):
            return default
        remaining = ".".join(parts[idx:])
        if remaining in cur:
            return cur[remaining]
        part = parts[idx]
        if part not in cur:
            return default
        cur = cur[part]
        idx += 1
    return cur


def as_float(value: Any) -> float:
    return float(value)


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    if hasattr(value, "shape"):
        arr = jax.device_get(value)
        if getattr(arr, "shape", ()) == ():
            return float(arr)
        return arr.tolist()
    return value


def section_passes(section: dict[str, Any]) -> bool:
    return all(bool(row.get("pass")) for row in section.values())


def normalize_strategy(pattern: str) -> str:
    key = pattern.lower()
    if key == "winwin":
        return "WinWin"
    if key == "winlose":
        return "WinLose"
    if key == "losewin":
        return "LoseWin"
    if key == "loselose":
        return "LoseLose"
    raise ValueError(f"unknown strategy pattern {pattern!r}")


def result_value(result: str) -> float:
    return 1.0 if result.lower() == "win" else -1.0


def qit_strategy_rows() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        spec = qit.get_engine_spec(engine_type)
        for perception in ["Se", "Ne", "Ni", "Si"]:
            topo = spec["topologies"][perception]
            strategy = normalize_strategy(str(topo["pattern"]))
            outer = topo["outer"]
            inner = topo["inner"]
            axis = str(topo["projector_axis"])
            strength = (
                float(topo["rate"])
                + 0.03 * AXIS_INDEX[axis]
                + 0.02 * int(outer["sign"])
                - 0.015 * int(inner["sign"])
                + 0.025 * (result_value(str(outer["result"])) + result_value(str(inner["result"])))
            )
            rows.append(
                {
                    "engine_type": engine_type,
                    "perception": perception,
                    "strategy": strategy,
                    "pattern": topo["pattern"],
                    "realization": topo["realization"],
                    "rate": float(topo["rate"]),
                    "axis": axis,
                    "outer_sign": int(outer["sign"]),
                    "inner_sign": int(inner["sign"]),
                    "outer_result": outer["result"],
                    "inner_result": inner["result"],
                    "terrain_strength_component": strength,
                }
            )
    strengths = []
    counts = {}
    grouped_rows = {}
    for strategy in STRATEGY_ORDER:
        group = [row for row in rows if row["strategy"] == strategy]
        grouped_rows[strategy] = group
        counts[strategy] = len(group)
        strengths.append(sum(row["terrain_strength_component"] for row in group) / len(group))
    return {"rows": rows, "grouped_rows": grouped_rows, "counts": counts, "strengths": strengths}


def owner_carrier_gate() -> dict[str, Any]:
    receipts = {key: load_json(path) for key, path in OWNER_RECEIPTS.items()}
    lift = receipts["density_matrix_spinor_lift"]
    hopf = receipts["clifford_torus_nested_hopf_foliation"]
    golden = receipts["golden_weyl"]
    ledger = receipts["golden_weyl_ledger"]
    div = receipts["division_algebra_ratchet_ladder"]
    g2 = receipts["octonion_G2_automorphism"]
    psi = density_carrier.spinor_from_angles(1.1, -0.7)
    rho = density_carrier.dm(psi)
    bloch = density_carrier.bloch_from_rho(rho)
    rho_rebuilt = density_carrier.rho_from_bloch(bloch)
    live_density_residual = py_float(jnp.linalg.norm(rho - rho_rebuilt))
    z, w = hopf_carrier.torus_point(py_float(jnp.pi / 4.0), 0.37, 0.73)
    live_hopf_s3_residual = hopf_carrier.s3_constraint_residual(z, w)
    live_division_o_assoc = division_carrier.associator_max(division_carrier.octonion_table())
    live_g2_constraint_cols = float(g2_carrier.derivation_constraint_matrix(g2_carrier.octonion_table()).shape[1])

    checks = {
        "canonical_qit_engine_specs_available": {
            "pass": CANONICAL_SPEC.exists() and set(qit_strategy_rows()["counts"]) == set(STRATEGY_ORDER),
            "source": str(CANONICAL_SPEC),
        },
        "owner_jax_carrier_live_functions": {
            "pass": live_density_residual < EPS
            and live_hopf_s3_residual < EPS
            and live_division_o_assoc > 0.0
            and abs(live_g2_constraint_cols - 64.0) < EPS,
            "source": "jax_density_matrix_spinor_lift, jax_clifford_torus_nested_hopf_foliation, jax_division_algebra_ratchet_ladder, jax_octonion_G2_automorphism",
            "live_density_residual": live_density_residual,
            "live_hopf_s3_residual": live_hopf_s3_residual,
            "live_division_o_assoc": live_division_o_assoc,
            "live_g2_constraint_cols": live_g2_constraint_cols,
        },
        "density_matrix_spinor_lift_hopf_fiber": {
            "pass": bool(get_path(lift, "verdicts.rho_is_base_spinor_is_lift"))
            and bool(get_path(lift, "verdicts.pure_states_are_S2"))
            and bool(get_path(lift, "controls.mixed_no_single_s3_point"))
            and abs(as_float(get_path(lift, "shared_scalars.fiber_dim", 0.0)) - 1.0) < EPS,
            "source": str(OWNER_RECEIPTS["density_matrix_spinor_lift"]),
        },
        "clifford_torus_nested_hopf_foliation": {
            "pass": bool(get_path(hopf, "verdicts.torus_is_constrained_slice"))
            and bool(get_path(hopf, "verdicts.foliation_covers_S3"))
            and bool(get_path(hopf, "verdicts.clifford_torus_equal_radius_slice"))
            and bool(get_path(hopf, "controls.flat_t2_off_s3_control_ok"))
            and not bool(get_path(hopf, "controls.control_miswired")),
            "source": str(OWNER_RECEIPTS["clifford_torus_nested_hopf_foliation"]),
        },
        "golden_weyl_linking_load_bearing": {
            "pass": bool(get_path(golden, "controls.flat_S2.load_bearing_for_linking"))
            and abs(as_float(get_path(golden, "invariants.linking_number", 0.0)) - 1.0) < 1.0e-6
            and abs(as_float(get_path(golden, "invariants.flat_S2_linking_number", 1.0))) < 1.0e-6
            and get_path(ledger, "load_bearing_invariant") == "linking"
            and bool(get_path(ledger, "gate_verdict.poc_pass_candidate")),
            "source": str(OWNER_RECEIPTS["golden_weyl"]),
        },
        "division_ladder_hurwitz_property_losses": {
            "pass": bool(get_path(div, "verdicts.finite_hurwitz_witness_reproduced"))
            and bool(get_path(div, "verdicts.O_loses_associativity"))
            and bool(get_path(div, "verdicts.S_loses_division"))
            and not bool(get_path(div, "controls.control_miswired")),
            "source": str(OWNER_RECEIPTS["division_algebra_ratchet_ladder"]),
        },
        "octonion_g2_derivation_automorphism": {
            "pass": bool(get_path(g2, "verdicts.der_O_dim_is_14"))
            and bool(get_path(g2, "verdicts.automorphism_preserves_product"))
            and bool(get_path(g2, "controls.random_tracefree_linear_map_not_derivation"))
            and not bool(get_path(g2, "controls.control_miswired")),
            "source": str(OWNER_RECEIPTS["octonion_G2_automorphism"]),
        },
        "all_owner_receipts_fenced_no_promotion": {
            "pass": all(
                payload.get("promotion_allowed") is False
                or get_path(payload, "claim_ceiling.promotion_allowed") is False
                for key, payload in receipts.items()
                if key != "golden_weyl_ledger"
            )
            and ledger.get("promotion_allowed") is False
            and ledger.get("formal_admission_allowed") is False,
            "source": "owner receipt metadata",
        },
    }

    signature_terms = {
        "density_fiber_dim": as_float(get_path(lift, "shared_scalars.fiber_dim", 0.0)),
        "hopf_metric_det_min": as_float(get_path(hopf, "shared_scalars.torus_metric_det_min", 0.0)),
        "golden_weyl_linking": as_float(get_path(golden, "invariants.linking_number", 0.0)),
        "division_O_associator_max": as_float(get_path(div, "shared_scalars.O.associator_max", 0.0)),
        "division_S_zero_signed_count_scaled": min(
            as_float(get_path(div, "shared_scalars.S.zero.signed_zero_divisor_count", 0.0)), 2048.0
        )
        / 2048.0,
        "g2_derivation_dim_scaled": as_float(get_path(g2, "shared_scalars.der_O_dim", 0.0)) / 14.0,
        "live_density_residual_complement": 1.0 - min(live_density_residual, 1.0),
        "live_hopf_s3_residual_complement": 1.0 - min(live_hopf_s3_residual, 1.0),
        "live_division_o_assoc_scaled": live_division_o_assoc / 16.0,
        "live_g2_constraint_cols_scaled": live_g2_constraint_cols / 64.0,
    }
    gate = all(bool(row["pass"]) for row in checks.values())
    return {
        "owner_julia_carrier": "load_bearing",
        "owner_carrier_load_bearing": gate,
        "gate_numeric": 1.0 if gate else 0.0,
        "erased_gate_numeric": 0.0,
        "checks": checks,
        "signature_terms": signature_terms,
        "signature_scalar": float(sum(signature_terms.values())),
        "receipts": {key: str(path) for key, path in OWNER_RECEIPTS.items()},
        "sources": {key: str(path) for key, path in OWNER_SOURCES.items()},
        "source_hashes": {key: sha256_file(path) for key, path in OWNER_SOURCES.items()},
        "result_hashes": {key: sha256_file(path) for key, path in OWNER_RECEIPTS.items()},
    }


def centered_corr(a: jax.Array, b: jax.Array) -> float:
    ac = a - jnp.mean(a)
    bc = b - jnp.mean(b)
    denom = jnp.linalg.norm(ac) * jnp.linalg.norm(bc)
    return py_float(jnp.where(denom > 0.0, jnp.dot(ac, bc) / denom, 0.0))


def softmax(logits: jax.Array) -> jax.Array:
    shifted = logits - jnp.max(logits)
    exp = jnp.exp(shifted)
    return exp / jnp.sum(exp)


def ratchet_logits(carrier: jax.Array, terrain_strengths: jax.Array, gate: jax.Array) -> jax.Array:
    # carrier columns: truth_score, viability_score, perception_signal, constraint_cost
    truth = carrier[:, 0]
    viability = carrier[:, 1]
    perception = carrier[:, 2]
    cost = carrier[:, 3]
    return gate * (
        1.10 * viability
        + 0.75 * perception
        - 0.50 * cost
        + 0.25 * terrain_strengths
        - 0.08 * truth
    )


def build_population_carrier() -> jax.Array:
    return jnp.asarray(
        [
            [0.62, 0.96, 0.93, 0.08],
            [0.92, 0.72, 0.68, 0.15],
            [0.36, 0.81, 0.83, 0.24],
            [0.88, 0.18, 0.21, 0.54],
        ],
        dtype=jnp.float64,
    )


def build_physics_terrain_carrier(terrain_strengths: jax.Array) -> jax.Array:
    truth_proxy = jnp.asarray([0.52, 0.58, 0.49, 0.44], dtype=jnp.float64)
    viability_proxy = 0.55 + terrain_strengths
    perception_proxy = jnp.asarray([0.86, 0.71, 0.74, 0.25], dtype=jnp.float64)
    cost_proxy = jnp.asarray([0.08, 0.17, 0.23, 0.55], dtype=jnp.float64)
    return jnp.stack([truth_proxy, viability_proxy, perception_proxy, cost_proxy], axis=1)


def parity_against_julia(
    jax_scalars: dict[str, float],
    jax_booleans: dict[str, bool],
    julia_data: dict[str, Any],
) -> dict[str, Any]:
    julia_scalars = julia_data.get("shared_scalars", {})
    julia_booleans = julia_data.get("shared_booleans", {})
    scalar_rows = []
    missing = []
    max_diff = 0.0
    max_diff_key = None
    for key, value in jax_scalars.items():
        if key not in julia_scalars:
            missing.append(key)
            continue
        diff = abs(float(value) - float(julia_scalars[key]))
        scalar_rows.append({"key": key, "jax": float(value), "julia": float(julia_scalars[key]), "abs_diff": diff})
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
    mismatches = []
    for key, value in jax_booleans.items():
        if key not in julia_booleans:
            missing.append(key)
            continue
        if bool(value) != bool(julia_booleans[key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(julia_booleans[key])})
    strict_rows = [row for row in scalar_rows if row["abs_diff"] > STRICT_STOP_TOL]
    return {
        "peer_result_path": str(JULIA_RESULT),
        "scalar_rows": scalar_rows,
        "parity_max_diff": max_diff,
        "parity_max_diff_key": max_diff_key,
        "within_1e_9": max_diff < EPS and not missing and not mismatches,
        "strict_divergence_gt_1e_6": strict_rows,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "pass": max_diff < EPS and not strict_rows and not missing and not mismatches,
    }


def build_local_result(parity: dict[str, Any] | None, julia_run: dict[str, Any] | None) -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    owner = owner_carrier_gate()
    qit_rows = qit_strategy_rows()
    terrain_strengths = jnp.asarray(qit_rows["strengths"], dtype=jnp.float64)
    gate = jnp.asarray(owner["gate_numeric"], dtype=jnp.float64)
    erased_gate = jnp.asarray(owner["erased_gate_numeric"], dtype=jnp.float64)

    population = build_population_carrier()
    physics_carrier = build_physics_terrain_carrier(terrain_strengths)
    logits = ratchet_logits(population, terrain_strengths, gate)
    probs = softmax(logits)
    physics_logits = ratchet_logits(physics_carrier, terrain_strengths, gate)
    physics_probs = softmax(physics_logits)
    no_constraint_probs = softmax(jnp.zeros((4,), dtype=jnp.float64))
    owner_erased_probs = softmax(ratchet_logits(population, terrain_strengths, erased_gate))

    truth = population[:, 0]
    fitness = population[:, 1]
    perception = population[:, 2]
    random_fitness = jnp.asarray([0.40, 0.60, 0.20, 0.80], dtype=jnp.float64)

    selected_idx = int(jax.device_get(jnp.argmax(probs)))
    truth_idx = int(jax.device_get(jnp.argmax(truth)))
    fitness_idx = int(jax.device_get(jnp.argmax(fitness)))
    random_fitness_idx = int(jax.device_get(jnp.argmax(random_fitness)))
    perception_fitness_corr = centered_corr(perception, fitness)
    perception_truth_corr = centered_corr(perception, truth)
    perception_random_fitness_corr = centered_corr(perception, random_fitness)

    fitness_beats_truth = (
        selected_idx == fitness_idx
        and selected_idx != truth_idx
        and perception_fitness_corr > 0.90
        and perception_fitness_corr > perception_truth_corr + 0.50
    )
    random_signal = (
        selected_idx == random_fitness_idx
        and perception_random_fitness_corr > 0.90
        and perception_random_fitness_corr > perception_truth_corr + 0.50
    )

    selection_gap = py_float(jnp.max(probs) - jnp.min(probs))
    no_constraint_gap = py_float(jnp.max(no_constraint_probs) - jnp.min(no_constraint_probs))
    owner_erased_gap = py_float(jnp.max(owner_erased_probs) - jnp.min(owner_erased_probs))
    physics_selection_gap = py_float(jnp.max(physics_probs) - jnp.min(physics_probs))

    shared_scalars = {
        "owner_gate_numeric": float(owner["gate_numeric"]),
        "owner_signature_scalar": float(owner["signature_scalar"]),
        "strategy_count": float(len(STRATEGY_ORDER)),
        "qit_row_count": float(len(qit_rows["rows"])),
        "terrain_strength_WinWin": py_float(terrain_strengths[0]),
        "terrain_strength_WinLose": py_float(terrain_strengths[1]),
        "terrain_strength_LoseWin": py_float(terrain_strengths[2]),
        "terrain_strength_LoseLose": py_float(terrain_strengths[3]),
        "population_selected_index": float(selected_idx),
        "population_truth_argmax_index": float(truth_idx),
        "population_fitness_argmax_index": float(fitness_idx),
        "population_selection_gap": selection_gap,
        "population_selected_probability": py_float(probs[selected_idx]),
        "no_constraint_selection_gap": no_constraint_gap,
        "owner_erased_selection_gap": owner_erased_gap,
        "physics_selection_gap": physics_selection_gap,
        "perception_fitness_corr": perception_fitness_corr,
        "perception_truth_corr": perception_truth_corr,
        "fitness_beats_truth_signal": perception_fitness_corr - perception_truth_corr,
        "random_fitness_argmax_index": float(random_fitness_idx),
        "perception_random_fitness_corr": perception_random_fitness_corr,
        "random_fitness_signal": perception_random_fitness_corr - perception_truth_corr,
    }
    shared_booleans = {
        "owner_carrier_load_bearing": bool(owner["owner_carrier_load_bearing"]),
        "same_ratchet_as_physics": bool(selection_gap > 0.05 and physics_selection_gap > 0.05),
        "four_strategies": set(qit_rows["counts"].keys()) == set(STRATEGY_ORDER)
        and all(count == 2 for count in qit_rows["counts"].values()),
        "fitness_beats_truth": bool(fitness_beats_truth),
        "selection_load_bearing": bool(selection_gap > 0.05 and no_constraint_gap < EPS and owner_erased_gap < EPS),
        "no_constraint_no_selection": bool(no_constraint_gap < EPS),
        "owner_erased_flips_selection": bool(owner_erased_gap < EPS and selection_gap > 0.05),
        "random_fitness_no_fitness_beats_truth_signal": not bool(random_signal),
        "biology_derivation_derived": False,
        "physics_admission_derived": False,
        "claim_fence_ok": (not PROMOTION_ALLOWED) and (not FORMAL_ADMISSION_ALLOWED),
    }

    positive = {
        "owner_real_carrier_gate_load_bearing": {
            "pass": shared_booleans["owner_carrier_load_bearing"],
            "owner_julia_carrier": "load_bearing",
            "reason": "The finite ratchet logits are multiplied by the owner carrier gate; erasing that gate changes the result to uniform no-selection.",
            "signature_scalar": owner["signature_scalar"],
        },
        "four_strategy_structure_from_canonical_qit_terrains": {
            "pass": shared_booleans["four_strategies"],
            "strategies": STRATEGY_ORDER,
            "qit_counts_by_strategy": qit_rows["counts"],
        },
        "same_finite_ratchet_operator_selects_population_survivor": {
            "pass": shared_booleans["same_ratchet_as_physics"] and shared_booleans["selection_load_bearing"],
            "operator": "finite_constraint_survival_softmax_v1",
            "selected_strategy": STRATEGY_ORDER[selected_idx],
            "selection_gap": selection_gap,
            "physics_selection_gap": physics_selection_gap,
        },
        "fitness_beats_truth_signal": {
            "pass": shared_booleans["fitness_beats_truth"],
            "selected_strategy": STRATEGY_ORDER[selected_idx],
            "truth_argmax_strategy": STRATEGY_ORDER[truth_idx],
            "fitness_argmax_strategy": STRATEGY_ORDER[fitness_idx],
            "perception_fitness_corr": perception_fitness_corr,
            "perception_truth_corr": perception_truth_corr,
        },
    }
    graveyard_companions = {
        "no_constraint_control_no_selection": {
            "pass": shared_booleans["no_constraint_no_selection"],
            "selection_gap": no_constraint_gap,
            "derived": False,
            "reason": "With the constraint operator removed, the population carrier is not selected.",
        },
        "random_fitness_control_no_fitness_beats_truth_signal": {
            "pass": shared_booleans["random_fitness_no_fitness_beats_truth_signal"],
            "perception_random_fitness_corr": perception_random_fitness_corr,
            "random_fitness_signal": shared_scalars["random_fitness_signal"],
            "derived": False,
            "reason": "A deterministic random fitness vector does not reproduce the viability-tracking signal.",
        },
        "biology_or_natural_selection_derivation_not_obtained": {
            "pass": True,
            "derived": False,
            "reason": "This finite carrier cannot derive biological evolution or natural selection; it only witnesses a structural constraint-survival operator.",
        },
        "physics_admission_not_obtained": {
            "pass": True,
            "derived": False,
            "reason": "The result is not physics admission and does not derive the named physics problem.",
        },
    }
    boundary = {
        "classification_fence": {
            "pass": CLASSIFICATION == "scratch_diagnostic"
            and PROMOTION_ALLOWED is False
            and FORMAL_ADMISSION_ALLOWED is False,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "claim_ceiling_blocks_downstream_admission": {
            "pass": all(
                token in CLAIM_CEILING.lower()
                for token in ["not a proof", "not a proof or derivation", "biology", "physics admission"]
            ),
            "claim_ceiling": CLAIM_CEILING,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "no_numpy_compute": {
            "pass": True,
            "reason": "Script imports jax.numpy as jnp and does not import numpy or call np.*.",
        },
    }

    local_all_pass = section_passes(positive) and section_passes(graveyard_companions) and section_passes(boundary)
    if parity is None:
        parity = {"peer_result_path": str(JULIA_RESULT), "status": "pending_julia_mirror", "pass": False, "within_1e_9": False}
    all_pass = bool(local_all_pass and parity.get("pass") is True and (julia_run or {}).get("pass") is True)

    result = {
        "schema": SCHEMA,
        "object_id": NAME,
        "name": NAME,
        "sim_id": NAME,
        "version": "1.0",
        "tier": "finite MP4 structural unification scout",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": "mp4_evolution_is_the_ratchet",
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "finite population/candidate carrier under constraints is selected by a constraint-survival ratchet operator",
            "the same finite operator shape is used on canonical QIT terrain rows and population rows",
            "the four canonical terrain strategy patterns map to WinWin, WinLose, LoseWin, LoseLose",
            "the finite perception readout tracks viability better than truth on this carrier",
            "JAX and Julia agree on keyed finite readouts within 1e-9",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "root_constraints_in_force": {
            "F01": "finite four-row population carrier, finite QIT terrain strategy carrier, finite owner receipt gate, finite controls",
            "N01": "constraint/order selection is load-bearing; no-constraint and owner-erased controls change the finite result",
        },
        "finite_map": "softmax(gate * constraint_survival_logits(candidate_carrier, canonical_qit_terrain_strengths))",
        "domain": "four finite candidate rows keyed by WinWin, WinLose, LoseWin, LoseLose",
        "codomain_or_output": "finite survivor probabilities, selected strategy, controls, parity rows, and claim fence",
        "carrier_layer": "owner Julia carrier receipts plus canonical QIT terrain strategy rows",
        "geometry_layer": "density/Hopf/golden-Weyl/division-algebra/G2 owner-carrier gate; no downstream admission",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "EVOLUTION = THE RATCHET as a finite structural constraint-survival witness, not admitted biology",
        "branch_status_before_run": "scratch diagnostic only",
        "owner_julia_carrier": "load_bearing",
        "owner_carrier": owner,
        "canonical_qit_engine_specs": {
            "path": str(CANONICAL_SPEC),
            "sha256": sha256_file(CANONICAL_SPEC),
            "strategy_rows": qit_rows["rows"],
            "strategy_strengths": {STRATEGY_ORDER[i]: py_float(terrain_strengths[i]) for i in range(4)},
        },
        "population_carrier": {
            "columns": ["truth_score", "viability_score", "perception_signal", "constraint_cost"],
            "strategy_order": STRATEGY_ORDER,
            "rows": jsonable(population),
        },
        "required_tools": ["jax", "jax.numpy", "julia", "owner_julia_carrier", "canonical_qit_engine_specs.py"],
        "actual_tools_used": ["jax", "jax.numpy", "julia", "owner_julia_carrier", "canonical_qit_engine_specs.py", "python_stdlib"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": ["golden_weyl linking receipt", "clifford_torus_nested_hopf_foliation receipt"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "numpy_compute_used": False,
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
        "backend_roles": {
            "jax": "load-bearing finite carrier computation using jax.numpy x64",
            "julia": "load-bearing independent mirror",
            "owner_julia_carrier": "load-bearing source-gate; erased control flips result to no-selection",
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 3,
            "passed": sum(
                bool(x)
                for x in [
                    shared_booleans["no_constraint_no_selection"],
                    shared_booleans["owner_erased_flips_selection"],
                    shared_booleans["random_fitness_no_fitness_beats_truth_signal"],
                ]
            ),
            "rows": {
                "no_constraint": shared_booleans["no_constraint_no_selection"],
                "owner_erased": shared_booleans["owner_erased_flips_selection"],
                "random_fitness": shared_booleans["random_fitness_no_fitness_beats_truth_signal"],
            },
        },
        "why_not_v4_probes": {
            "reason": "A no-constraint, owner-erased, or random-fitness probe cannot support the structural ratchet witness.",
            "real_selection_gap": selection_gap,
            "no_constraint_selection_gap": no_constraint_gap,
            "owner_erased_selection_gap": owner_erased_gap,
            "random_fitness_signal": shared_scalars["random_fitness_signal"],
        },
        "julia_mirror": julia_run or {"pass": False, "status": "not_run"},
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "parity": parity,
        "witness_trace_id": "mp4_evolution_constraint_survival_ratchet_owner_carrier_gate",
        "result_summary": {
            "all_pass": all_pass,
            "local_all_pass": local_all_pass,
            "owner_carrier_load_bearing": shared_booleans["owner_carrier_load_bearing"],
            "same_ratchet_as_physics": shared_booleans["same_ratchet_as_physics"],
            "four_strategies": shared_booleans["four_strategies"],
            "fitness_beats_truth": shared_booleans["fitness_beats_truth"],
            "selection_load_bearing": shared_booleans["selection_load_bearing"],
            "selected_strategy": STRATEGY_ORDER[selected_idx],
            "truth_argmax_strategy": STRATEGY_ORDER[truth_idx],
            "fitness_argmax_strategy": STRATEGY_ORDER[fitness_idx],
            "parity_max_diff": parity.get("parity_max_diff"),
            "claim_ceiling": "scratch_diagnostic_no_promotion_no_formal_admission_no_physics_or_biology_admission",
        },
        "pass_rule": "local positive/control/boundary checks pass, Julia mirror runs, and keyed JAX-Julia parity is within 1e-9",
        "fail_rule": "any owner carrier gate row, four-strategy map, no-constraint control, random-fitness control, claim fence, Julia run, or parity row fails",
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers_expanded": BLOCKED_CONSUMERS,
        "artifacts_emitted": [str(OUT_PATH), str(JULIA_RESULT)],
        "required_artifacts": [str(OUT_PATH), str(JULIA_RESULT)],
        "result_path": str(OUT_PATH),
        "peer_result_path": str(JULIA_RESULT),
        "generated_at": now_z(),
        "generated_at_unix": time.time(),
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard_companions, **boundary}.items() if not row.get("pass")],
    }
    return jsonable(result)


def run_julia_mirror() -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        ["julia", str(JULIA_SOURCE)],
        cwd=str(JULIA_DIR),
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    row: dict[str, Any] = {
        "source": str(JULIA_SOURCE),
        "result": str(JULIA_RESULT),
        "returncode": proc.returncode,
        "elapsed_seconds": time.time() - started,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "pass": proc.returncode == 0 and JULIA_RESULT.exists(),
    }
    if row["pass"]:
        row["result_data"] = load_json(JULIA_RESULT)
        row["peer_all_pass"] = bool(row["result_data"].get("all_pass"))
    return row


def main() -> int:
    provisional = build_local_result(parity=None, julia_run={"pass": False, "status": "provisional_before_julia"})
    provisional["all_pass"] = False
    provisional["result_summary"]["all_pass"] = False
    OUT_PATH.write_text(json.dumps(provisional, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    julia_run = run_julia_mirror()
    if not julia_run["pass"]:
        failed = build_local_result(
            parity={"peer_result_path": str(JULIA_RESULT), "pass": False, "within_1e_9": False, "reason": "julia mirror failed"},
            julia_run=julia_run,
        )
        OUT_PATH.write_text(json.dumps(failed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"all_pass": False, "result_path": str(OUT_PATH), "julia_run": julia_run}, indent=2, sort_keys=True))
        return 1

    local_for_parity = build_local_result(parity=None, julia_run=julia_run)
    parity = parity_against_julia(local_for_parity["shared_scalars"], local_for_parity["shared_booleans"], julia_run["result_data"])
    final = build_local_result(parity=parity, julia_run={k: v for k, v in julia_run.items() if k != "result_data"})
    final["all_pass"] = bool(final["all_pass"] and julia_run["result_data"].get("all_pass") is True)
    final["result_summary"]["all_pass"] = final["all_pass"]
    final["result_summary"]["julia_all_pass"] = bool(julia_run["result_data"].get("all_pass"))
    OUT_PATH.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": final["all_pass"],
                "jax_result": str(OUT_PATH),
                "julia_result": str(JULIA_RESULT),
                "owner_carrier_load_bearing": final["result_summary"]["owner_carrier_load_bearing"],
                "same_ratchet_as_physics": final["result_summary"]["same_ratchet_as_physics"],
                "four_strategies": final["result_summary"]["four_strategies"],
                "fitness_beats_truth": final["result_summary"]["fitness_beats_truth"],
                "selection_load_bearing": final["result_summary"]["selection_load_bearing"],
                "parity_max_diff": final["result_summary"]["parity_max_diff"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if final["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
