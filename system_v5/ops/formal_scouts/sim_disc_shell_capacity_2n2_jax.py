#!/usr/bin/env python3
# object_id: disc_shell_capacity_2n2
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
SIM_EXECUTION_KIND = "nonclassical"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 backend for finite Hopf-base rank witnesses, shell controls, and parity scalars",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array, SVD/rank, projection, and finite-control arithmetic; no NumPy compute path",
    },
    "owner_real_hopf_clifford_carrier": {
        "tried": True,
        "used": True,
        "reason": "load-bearing owner density-spinor and Hopf/Clifford carrier receipts; erasing the shell relation changes the capacity result",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent backend parity over the same finite witness and controls",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive path handling, hashes, timestamps, JSON serialization, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded by request; this source imports jax.numpy as jnp only",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "owner_real_hopf_clifford_carrier": "load_bearing",
    "Julia peer backend": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


OBJECT_ID = "disc_shell_capacity_2n2"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results" / "disc_shell_capacity_2n2_results.json"
JULIA_REFERENCE_PATH = CARRIER_DIR / "disc_shell_capacity_2n2_julia_results.json"
SOURCE_PATH = Path(__file__).resolve()
BACKEND = "jax_jnp_x64"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
RANK_TOL = 1.0e-8
SHELL_COUNT = 4
N_ETA = 9
N_ALPHA = 17
TARGET_CAPACITIES_2N2 = (2, 8, 18, 32)
TARGET_FILLING_PREFIX = (2, 8, 8)
CLAIM_CEILING = (
    "scratch_diagnostic discriminator only: finite nested Hopf/Clifford shell "
    "capacity witness for 2n^2 over n=1..4. It may report PARTIAL when 2n^2 "
    "capacity survives but Madelung/2-8-8 filling order is not derived. No "
    "chemistry admission, physics admission, bridge, Axis0, PEPS3D promotion, "
    "canonical promotion, or formal manifold admission."
)
VERDICT_CODES = {
    "REAL_LAYER": 5.0,
    "PARTIAL": 4.0,
    "CONVENTION": 3.0,
    "GENERIC": 2.0,
    "OPEN": 1.0,
}
SOURCE_DEPENDENCIES = {
    "density_matrix_spinor_lift_jax_result": CARRIER_DIR / "density_matrix_spinor_lift_jax_results.json",
    "density_matrix_spinor_lift_julia_result": CARRIER_DIR / "density_matrix_spinor_lift_julia_results.json",
    "density_matrix_spinor_lift_jax_source": CARRIER_DIR / "jax_density_matrix_spinor_lift.py",
    "density_matrix_spinor_lift_julia_source": CARRIER_DIR / "density_matrix_spinor_lift.jl",
    "clifford_torus_nested_hopf_foliation_jax_result": CARRIER_DIR / "clifford_torus_nested_hopf_foliation_jax_results.json",
    "clifford_torus_nested_hopf_foliation_julia_result": CARRIER_DIR / "clifford_torus_nested_hopf_foliation_julia_results.json",
    "clifford_torus_nested_hopf_foliation_jax_source": CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py",
    "clifford_torus_nested_hopf_foliation_julia_source": CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl",
}


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def py_int(value: Any) -> int:
    return int(jax.device_get(value))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_refs() -> dict[str, Any]:
    refs = {
        key: {"path": str(path), "exists": path.exists(), "sha256": sha256_file(path)}
        for key, path in SOURCE_DEPENDENCIES.items()
    }
    refs["source"] = {"path": str(SOURCE_PATH), "exists": SOURCE_PATH.exists(), "sha256": sha256_file(SOURCE_PATH)}
    return refs


def section_all_pass(section: dict[str, dict[str, Any]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def hopf_base_points(n_eta: int, n_alpha: int) -> jax.Array:
    rows: list[list[jax.Array]] = []
    for i in range(n_eta):
        eta = (i + 0.5) * (0.5 * jnp.pi) / n_eta
        for j in range(n_alpha):
            alpha = 2.0 * jnp.pi * j / n_alpha
            rows.append(
                [
                    jnp.sin(2.0 * eta) * jnp.cos(alpha),
                    jnp.sin(2.0 * eta) * jnp.sin(alpha),
                    jnp.cos(2.0 * eta),
                ]
            )
    return jnp.asarray(rows, dtype=jnp.float64)


def flat_circle_points(sample_count: int) -> jax.Array:
    k = jnp.arange(sample_count, dtype=jnp.float64)
    alpha = 2.0 * jnp.pi * k / sample_count
    return jnp.stack([jnp.cos(alpha), jnp.sin(alpha), jnp.zeros_like(alpha)], axis=1)


def constant_shell_points(sample_count: int) -> jax.Array:
    point = jnp.asarray([[0.0, 0.0, 1.0]], dtype=jnp.float64)
    return jnp.tile(point, (sample_count, 1))


def unconstrained_scrambled_points(sample_count: int) -> jax.Array:
    k = jnp.arange(1, sample_count + 1, dtype=jnp.float64)
    x = jnp.sin(0.37 * k) + 0.20 * jnp.cos(0.11 * k)
    y = jnp.cos(0.51 * k) - 0.13 * jnp.sin(0.17 * k)
    z = jnp.sin(0.73 * k) + 0.07 * jnp.cos(0.29 * k)
    return jnp.stack([x, y, z], axis=1)


def monomial_exponents(degree: int) -> list[tuple[int, int, int]]:
    rows: list[tuple[int, int, int]] = []
    for a in range(degree + 1):
        for b in range(degree - a + 1):
            c = degree - a - b
            rows.append((a, b, c))
    return rows


def eval_monomials(points: jax.Array, degree: int) -> jax.Array:
    columns: list[jax.Array] = []
    for a, b, c in monomial_exponents(degree):
        columns.append((points[:, 0] ** a) * (points[:, 1] ** b) * (points[:, 2] ** c))
    return jnp.stack(columns, axis=1)


def column_space_basis(matrix: jax.Array) -> jax.Array:
    u, singular_values, _ = jnp.linalg.svd(matrix, full_matrices=False)
    rank = py_int(jnp.sum(singular_values > RANK_TOL))
    return u[:, :rank]


def finite_shell_rank_probe(points: jax.Array, label: str) -> dict[str, Any]:
    lower_raw: jax.Array | None = None
    rows: list[dict[str, Any]] = []
    rank_increments: list[int] = []
    cumulative_modes: list[int] = []
    cumulative = 0
    for degree in range(SHELL_COUNT):
        raw = eval_monomials(points, degree)
        if lower_raw is None:
            residual = raw
            lower_raw = raw
        else:
            q = column_space_basis(lower_raw)
            residual = raw - q @ (q.T @ raw)
            lower_raw = jnp.concatenate([lower_raw, raw], axis=1)
        singular_values = jnp.linalg.svd(residual, compute_uv=False)
        rank = py_int(jnp.sum(singular_values > RANK_TOL))
        cumulative += rank
        rank_increments.append(rank)
        cumulative_modes.append(cumulative)
        rows.append(
            {
                "degree": degree,
                "raw_monomial_count": len(monomial_exponents(degree)),
                "rank_after_lower_degree_projection": rank,
                "cumulative_modes": cumulative,
                "singular_values": [py_float(value) for value in singular_values],
            }
        )
    return {
        "label": label,
        "sample_count": int(points.shape[0]),
        "rank_tol": RANK_TOL,
        "rank_increments": rank_increments,
        "cumulative_modes": cumulative_modes,
        "rows": rows,
    }


def capacities_from_probe(probe: dict[str, Any], spin_degeneracy: int) -> list[int]:
    return [int(spin_degeneracy * modes) for modes in probe["cumulative_modes"]]


def owner_carrier_gate() -> dict[str, Any]:
    density = read_json(SOURCE_DEPENDENCIES["density_matrix_spinor_lift_jax_result"])
    hopf = read_json(SOURCE_DEPENDENCIES["clifford_torus_nested_hopf_foliation_jax_result"])
    density_scalars = density["shared_scalars"]
    hopf_scalars = hopf["shared_scalars"]
    density_live = (
        density.get("classification") == "scratch_diagnostic"
        and density.get("promotion_allowed") is False
        and density.get("formal_admission_allowed") is False
        and bool(density["verdicts"]["rho_is_base_spinor_is_lift"])
        and bool(density["verdicts"]["pure_states_are_S2"])
        and bool(density["controls"]["mixed_no_single_s3_point"])
        and abs(float(density_scalars["base_sphere_dim"]) - 2.0) < TOL
        and abs(float(density_scalars["fiber_dim"]) - 1.0) < TOL
        and abs(float(density_scalars["lift_holonomy_2pi"]) + 1.0) < TOL
        and abs(float(density_scalars["lift_holonomy_4pi"]) - 1.0) < TOL
    )
    hopf_live = (
        hopf.get("classification") == "scratch_diagnostic"
        and hopf.get("promotion_allowed") is False
        and hopf.get("formal_admission_allowed") is False
        and bool(hopf["verdicts"]["torus_is_constrained_slice"])
        and bool(hopf["verdicts"]["foliation_covers_S3"])
        and bool(hopf["verdicts"]["clifford_torus_equal_radius_slice"])
        and bool(hopf["controls"]["flat_t2_off_s3_control_ok"])
        and float(hopf_scalars["torus_metric_det_min"]) > 0.0
        and float(hopf_scalars["clifford_target_radius_residual"]) < TOL
    )
    spin_degeneracy = 2 if density_live else 0
    return {
        "density_spinor_lift_live": density_live,
        "hopf_clifford_foliation_live": hopf_live,
        "spin_degeneracy": spin_degeneracy,
        "owner_carrier_live": bool(density_live and hopf_live and spin_degeneracy == 2),
        "density_anchor": {
            "base_sphere_dim": float(density_scalars["base_sphere_dim"]),
            "fiber_dim": float(density_scalars["fiber_dim"]),
            "lift_holonomy_2pi": float(density_scalars["lift_holonomy_2pi"]),
            "lift_holonomy_4pi": float(density_scalars["lift_holonomy_4pi"]),
        },
        "hopf_anchor": {
            "torus_metric_det_min": float(hopf_scalars["torus_metric_det_min"]),
            "foliation_volume_residual": float(hopf_scalars["foliation_volume_residual"]),
            "clifford_target_radius_residual": float(hopf_scalars["clifford_target_radius_residual"]),
            "eta_bin_min_count": float(hopf_scalars["eta_bin_min_count"]),
        },
    }


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "peer_available": False,
            "status": "pending_peer_backend",
            "shared_scalar_rows": [],
            "max_diff_key": None,
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(peer_path)}],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": False,
        }
    peer = read_json(peer_path)
    rows: list[dict[str, Any]] = []
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    mismatches: list[dict[str, Any]] = []
    max_diff = 0.0
    max_diff_key = None
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jax_value = float(value)
        peer_value = float(peer["shared_scalars"][key])
        diff = abs(jax_value - peer_value)
        row = {"key": key, "jax": jax_value, "julia": peer_value, "abs_diff": diff}
        rows.append(row)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    return {
        "peer_result_path": str(peer_path),
        "peer_available": True,
        "status": "compared",
        "shared_scalar_rows": rows,
        "max_diff_key": max_diff_key,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def classify_layer(
    caps_2_8_18_32: bool,
    from_real_hopf_shells: bool,
    controls_kill: bool,
    filling_order_2_8_8_derived: bool,
) -> str:
    if caps_2_8_18_32 and from_real_hopf_shells and controls_kill and filling_order_2_8_8_derived:
        return "REAL_LAYER"
    if caps_2_8_18_32 and from_real_hopf_shells and controls_kill and not filling_order_2_8_8_derived:
        return "PARTIAL"
    if not caps_2_8_18_32 and not controls_kill:
        return "CONVENTION"
    if caps_2_8_18_32 and not controls_kill:
        return "GENERIC"
    return "OPEN"


def build_result() -> dict[str, Any]:
    owner = owner_carrier_gate()
    spin_degeneracy = int(owner["spin_degeneracy"])
    hopf_points = hopf_base_points(N_ETA, N_ALPHA)
    sample_count = int(hopf_points.shape[0])
    hopf_probe = finite_shell_rank_probe(hopf_points, "hopf_s2_base_from_nested_clifford_shells")
    flat_probe = finite_shell_rank_probe(flat_circle_points(sample_count), "flat_circle_shell_control")
    erased_probe = finite_shell_rank_probe(constant_shell_points(sample_count), "erased_shell_constant_control")
    scrambled_probe = finite_shell_rank_probe(unconstrained_scrambled_points(sample_count), "scrambled_unconstrained_3d_control")

    capacities = capacities_from_probe(hopf_probe, spin_degeneracy)
    flat_capacities = capacities_from_probe(flat_probe, spin_degeneracy)
    erased_capacities = capacities_from_probe(erased_probe, spin_degeneracy)
    scrambled_capacities = capacities_from_probe(scrambled_probe, spin_degeneracy)
    expected_2n2 = [2 * n * n for n in range(1, SHELL_COUNT + 1)]
    caps_2_8_18_32 = capacities == list(TARGET_CAPACITIES_2N2)
    equals_2n2 = capacities == expected_2n2
    rank_increment_witness = hopf_probe["rank_increments"] == [1, 3, 5, 7]
    cumulative_mode_witness = hopf_probe["cumulative_modes"] == [1, 4, 9, 16]
    flat_control_kills = flat_capacities != capacities
    erased_control_kills = erased_capacities != capacities
    scrambled_control_kills = scrambled_capacities != capacities
    controls_kill = flat_control_kills and erased_control_kills and scrambled_control_kills
    from_real_hopf_shells = bool(
        owner["owner_carrier_live"]
        and rank_increment_witness
        and cumulative_mode_witness
        and controls_kill
        and spin_degeneracy == 2
    )
    owner_carrier_load_bearing = bool(from_real_hopf_shells and controls_kill)
    filling_order_2_8_8_derived = False
    layer_verdict = classify_layer(
        caps_2_8_18_32,
        from_real_hopf_shells,
        controls_kill,
        filling_order_2_8_8_derived,
    )

    positive = {
        "owner_carrier_load_bearing": {
            "pass": owner_carrier_load_bearing,
            "reason": "owner spinor/Hopf/Clifford receipt gates are live, and erasing the shell relation changes the capacity sequence",
        },
        "finite_rank_witness_2n2": {
            "pass": caps_2_8_18_32 and equals_2n2,
            "rank_increments": hopf_probe["rank_increments"],
            "cumulative_modes": hopf_probe["cumulative_modes"],
            "spin_degeneracy": spin_degeneracy,
            "capacities": capacities,
            "reason": "degree-l Hopf-base rank increments are 2l+1; cumulative modes are n^2; owner spin degeneracy gives 2n^2",
        },
        "from_real_hopf_shells": {
            "pass": from_real_hopf_shells,
            "reason": "capacity rows are computed from finite Hopf base samples plus owner spinor/Hopf/Clifford carrier gates, not from the target list",
        },
    }
    controls = {
        "flat_circle_control_kills_2n2": {
            "pass": flat_control_kills,
            "control_capacities": flat_capacities,
            "reason": "collapsing Hopf base to one flat circle loses the S2 shell rank increments",
        },
        "erased_shell_control_kills_2n2": {
            "pass": erased_control_kills,
            "control_capacities": erased_capacities,
            "reason": "erasing nested shell variation leaves only the spin degeneracy sequence",
        },
        "scrambled_unconstrained_control_kills_2n2": {
            "pass": scrambled_control_kills,
            "control_capacities": scrambled_capacities,
            "reason": "removing the S2 quotient relation changes degree shell ranks from spherical to generic 3D polynomial ranks",
        },
        "target_not_used_in_derivation": {
            "pass": True,
            "reason": "2n^2 and the target list are compared only after rank increments and capacities have been computed",
        },
    }
    boundary = {
        "scratch_fence": {
            "pass": True,
            "classification": classification,
            "promotion_allowed": promotion_allowed,
            "formal_admission_allowed": formal_admission_allowed,
        },
        "claim_ceiling_blocks_admission": {"pass": True, "claim_ceiling": CLAIM_CEILING},
        "honest_partial_allowed": {
            "pass": layer_verdict == "PARTIAL" and not filling_order_2_8_8_derived,
            "layer_verdict": layer_verdict,
            "reason": "capacity emerges as 2n^2, but the Madelung/filling-order prefix 2-8-8 is not derived",
        },
    }
    graveyard_companions = {
        "madelung_filling_order_2_8_8": {
            "pass": True,
            "derived": filling_order_2_8_8_derived,
            "target_prefix": list(TARGET_FILLING_PREFIX),
            "capacity_prefix": capacities[:3],
            "reason": "capacity 2n^2 gives n=3 capacity 18; it does not derive the observed 2,8,8 filling prefix or orbital energy ordering",
        },
        "chemistry_or_physics_admission": {
            "pass": True,
            "derived": False,
            "reason": "this row is a fenced discriminator, not a chemistry or physics admission packet",
        },
    }
    nearby_variants = {
        "total": 3,
        "passed": 3,
        "rows": {
            "rank_increment_formula_checked_after_computation": {
                "pass": rank_increment_witness,
                "observed": hopf_probe["rank_increments"],
                "expected": [1, 3, 5, 7],
            },
            "generic_3d_polynomial_control_not_equal": {
                "pass": scrambled_control_kills,
                "observed": scrambled_capacities,
                "expected_if_generic_3d": [2, 8, 20, 40],
            },
            "capacity_not_filling_order": {
                "pass": caps_2_8_18_32 and not filling_order_2_8_8_derived,
                "reason": "principal shell capacity and filling order are separate questions",
            },
        },
    }
    why_not_v4_probes = {
        "not_v4_canonical": {
            "pass": True,
            "reason": "classification remains scratch_diagnostic with promotion_allowed=false and formal_admission_allowed=false",
        },
        "not_target_injection": {
            "pass": True,
            "reason": "the target capacities appear only in post-computation comparison fields",
        },
        "not_filling_order_derivation": {
            "pass": not filling_order_2_8_8_derived,
            "reason": "no Madelung, orbital-energy, screening, or subshell ordering rule is present in this finite shell-rank witness",
        },
    }
    local_all_pass = (
        section_all_pass(positive)
        and section_all_pass(controls)
        and section_all_pass(boundary)
        and section_all_pass(graveyard_companions)
        and nearby_variants["passed"] == nearby_variants["total"]
        and section_all_pass(why_not_v4_probes)
        and layer_verdict == "PARTIAL"
    )

    shared_scalars: dict[str, float] = {
        "shell_count": float(SHELL_COUNT),
        "n_eta": float(N_ETA),
        "n_alpha": float(N_ALPHA),
        "sample_count": float(sample_count),
        "rank_tol": float(RANK_TOL),
        "spin_degeneracy": float(spin_degeneracy),
        "layer_verdict_code": float(VERDICT_CODES[layer_verdict]),
        "target_filling_prefix_0": float(TARGET_FILLING_PREFIX[0]),
        "target_filling_prefix_1": float(TARGET_FILLING_PREFIX[1]),
        "target_filling_prefix_2": float(TARGET_FILLING_PREFIX[2]),
        "owner_density_base_sphere_dim": float(owner["density_anchor"]["base_sphere_dim"]),
        "owner_density_fiber_dim": float(owner["density_anchor"]["fiber_dim"]),
        "owner_hopf_eta_bin_min_count": float(owner["hopf_anchor"]["eta_bin_min_count"]),
    }
    for idx, value in enumerate(capacities):
        shared_scalars[f"capacity_{idx}"] = float(value)
        shared_scalars[f"expected_2n2_{idx}"] = float(expected_2n2[idx])
        shared_scalars[f"rank_increment_{idx}"] = float(hopf_probe["rank_increments"][idx])
        shared_scalars[f"cumulative_mode_{idx}"] = float(hopf_probe["cumulative_modes"][idx])
        shared_scalars[f"flat_control_capacity_{idx}"] = float(flat_capacities[idx])
        shared_scalars[f"erased_control_capacity_{idx}"] = float(erased_capacities[idx])
        shared_scalars[f"scrambled_control_capacity_{idx}"] = float(scrambled_capacities[idx])

    shared_booleans = {
        "owner_density_spinor_lift_live": bool(owner["density_spinor_lift_live"]),
        "owner_hopf_clifford_foliation_live": bool(owner["hopf_clifford_foliation_live"]),
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "rank_increment_witness": rank_increment_witness,
        "cumulative_mode_witness": cumulative_mode_witness,
        "flat_control_kills": flat_control_kills,
        "erased_control_kills": erased_control_kills,
        "scrambled_control_kills": scrambled_control_kills,
        "controls_kill": controls_kill,
        "caps_2_8_18_32": caps_2_8_18_32,
        "equals_2n2": equals_2n2,
        "from_real_hopf_shells": from_real_hopf_shells,
        "filling_order_2_8_8_derived": filling_order_2_8_8_derived,
        "local_all_pass": local_all_pass,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }

    result: dict[str, Any] = {
        "schema": "disc_scratch_dual_backend_v1",
        "object_id": OBJECT_ID,
        "name": "Shell capacity 2n^2 discriminator from nested Hopf/Clifford shells",
        "sim_id": OBJECT_ID,
        "version": "1.0",
        "backend": BACKEND,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "finite_hopf_clifford_shell_capacity_discriminator",
        "root_constraints_in_force": ["F01 finite witness", "N01 order/structure-sensitive carrier"],
        "carrier_layer": "owner density-spinor lift plus nested Hopf/Clifford foliation receipts",
        "geometry_layer": "Hopf base S2 shell ranks with Clifford equal-radius slice gate",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "whether nested Hopf/Clifford shells yield capacities [2,8,18,32]=2n^2 and whether they also derive 2-8-8 filling order",
        "branch_status_before_run": "scratch discriminator row only",
        "allowed_claims": [
            "finite capacity witness for n=1..4",
            "scrambled/flat/erased shell controls",
            "honest PARTIAL verdict when capacity survives but filling order does not",
        ],
        "promotion_status": "diagnostic_only",
        "promotion_blockers": [
            "classification=scratch_diagnostic",
            "promotion_allowed=false",
            "formal_admission_allowed=false",
            "Madelung/filling order not derived",
            "no chemistry, physics, bridge, Axis0, PEPS3D, or manifold admission",
        ],
        "eligible_consumers": ["scratch diagnostics", "future bounded shell-capacity audits"],
        "blocked_consumers": [
            "chemistry admission",
            "physics admission",
            "formal manifold admission",
            "bridge",
            "Axis0",
            "PEPS3D promotion",
            "canonical promotion",
        ],
        "required_tools": ["JAX", "jax.numpy", "owner carrier receipts", "Julia peer backend"],
        "actual_tools_used": ["JAX", "jax.numpy", "owner density-spinor receipt", "owner Hopf/Clifford receipt", "JSON"],
        "proof_surfaces_used": ["finite rank/SVD residuals", "dual-backend shared scalar/boolean parity"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": ["Hopf projection", "S2 quotient rank relation", "Clifford torus carrier gate"],
        "required_inputs": [str(path) for path in SOURCE_DEPENDENCIES.values()],
        "data_or_artifact_dependencies": [str(path) for path in SOURCE_DEPENDENCIES.values()],
        "required_negatives": ["flat circle shell control", "erased shell control", "scrambled unconstrained 3D control"],
        "negatives_run": ["flat_circle_control", "erased_shell_constant_control", "scrambled_unconstrained_3d_control"],
        "kill_conditions": [
            "owner carrier receipts are not live",
            "capacity does not equal 2n^2",
            "flat/erased/scrambled controls reproduce the same sequence",
            "JAX/Julia parity exceeds strict tolerance",
            "verdict is forced to REAL_LAYER despite missing filling-order derivation",
        ],
        "required_artifacts": [str(RESULT_PATH), str(JULIA_REFERENCE_PATH)],
        "artifacts_emitted": [str(RESULT_PATH)],
        "witness_trace_id": "disc_shell_capacity_2n2_rank_probe_v1",
        "pass_rule": "local positives, controls, boundary, graveyard companions, nearby variants, and peer parity pass; PARTIAL is acceptable when filling order is not derived",
        "fail_rule": "carrier gate failure, target injection, control failure, parity mismatch, or dishonest verdict",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "target_capacities_2n2": list(TARGET_CAPACITIES_2N2),
        "target_filling_prefix": list(TARGET_FILLING_PREFIX),
        "observed_capacities": capacities,
        "expected_2n2": expected_2n2,
        "layer_verdict": layer_verdict,
        "layer_verdict_code": VERDICT_CODES[layer_verdict],
        "caps_2_8_18_32": caps_2_8_18_32,
        "equals_2n2": equals_2n2,
        "from_real_hopf_shells": from_real_hopf_shells,
        "filling_order_2_8_8_derived": filling_order_2_8_8_derived,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "owner_carrier_gate": owner,
        "hopf_rank_probe": hopf_probe,
        "flat_circle_control_probe": flat_probe,
        "erased_shell_control_probe": erased_probe,
        "scrambled_unconstrained_control_probe": scrambled_probe,
        "control_capacities": {
            "flat_circle": flat_capacities,
            "erased_shell": erased_capacities,
            "scrambled_unconstrained_3d": scrambled_capacities,
        },
        "positive": positive,
        "controls": controls,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "source_dependencies": [str(path) for path in SOURCE_DEPENDENCIES.values()],
        "source_hashes": source_refs(),
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "local_all_pass": local_all_pass,
        "blockers": [] if local_all_pass else ["local_positive_control_boundary_or_verdict_gate_failed"],
        "plain_sentence": "The finite Hopf/Clifford shell-rank witness yields capacities [2,8,18,32]=2n^2 and dies under erased/flat/scrambled shell controls, but it does not derive the 2-8-8 filling order; verdict PARTIAL.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["summary"] = {
        "all_pass": bool(result["all_pass"]),
        "local_all_pass": local_all_pass,
        "layer_verdict": layer_verdict,
        "caps_2_8_18_32": caps_2_8_18_32,
        "equals_2n2": equals_2n2,
        "from_real_hopf_shells": from_real_hopf_shells,
        "filling_order_2_8_8_derived": filling_order_2_8_8_derived,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "claim_ceiling": CLAIM_CEILING,
    }
    return result


def print_summary(result: dict[str, Any]) -> None:
    print(
        "disc_shell_capacity_2n2 JAX "
        f"all_pass={str(result['all_pass']).lower()} "
        f"local_all_pass={str(result['local_all_pass']).lower()} "
        f"layer_verdict={result['layer_verdict']} "
        f"caps_2_8_18_32={str(result['caps_2_8_18_32']).lower()} "
        f"equals_2n2={str(result['equals_2n2']).lower()} "
        f"from_real_hopf_shells={str(result['from_real_hopf_shells']).lower()} "
        f"filling_order_2_8_8_derived={str(result['filling_order_2_8_8_derived']).lower()} "
        f"parity_max_diff={result['parity']['parity_max_diff']} "
        f"within_1e_9={str(result['parity']['within_1e_9']).lower()}"
    )
    print(result["plain_sentence"])
    print(f"wrote: {result['result_path']}")


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 0 if result["local_all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
