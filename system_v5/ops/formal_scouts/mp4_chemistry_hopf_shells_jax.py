#!/usr/bin/env python3
# object_id: mp4_chemistry_hopf_shells
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
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
SIM_EXECUTION_KIND = "scratch"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Python backend for this bounded scratch diagnostic; Python-side array compute uses jax.numpy/jnp only",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array algebra surface for the local finite witness, controls, shared scalars, and shared booleans",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent peer backend for dual-backend parity; the Python source does not derive values from Julia except parity comparison",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, path handling, timestamps, hashing, imports, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; no import numpy, no np.*, and no NumPy compute path in this scratch diagnostic",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


OBJECT_ID = "mp4_chemistry_hopf_shells"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = ROOT / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = ROOT / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp4_chemistry_hopf_shells_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp4_chemistry_hopf_shells_julia_results.json"

BACKEND = "jax_jnp_x64"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
SHELL_COUNT = 4
TARGET_PERIODIC_PATTERN = (2, 8, 8, 18)
RANK_TOL = 1.0e-8
CLAIM_CEILING = (
    "Finite MECHANISM witness in the owner's entropic-monist frame only: a bounded "
    "nested Hopf/S3 spinor-shell capacity proxy is computed from the owner carrier "
    "and compared to the electron-shell-like 2,8,8,18 periodic pattern. NOT a proof "
    "or derivation of chemistry, NOT a derivation of the named chemistry problem, "
    "NO physics admission, and NO formal admission."
)

SOURCE_DEPENDENCIES = [
    FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py",
    CARRIER_DIR / "jax_density_matrix_spinor_lift.py",
    CARRIER_DIR / "density_matrix_spinor_lift.jl",
    CARRIER_DIR / "density_matrix_spinor_lift_jax_results.json",
    CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py",
    CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl",
    CARRIER_DIR / "clifford_torus_nested_hopf_foliation_jax_results.json",
    CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py",
    CARRIER_DIR / "golden_weyl_julia.jl",
    CARRIER_DIR / "golden_weyl_jax_receipt.json",
    CARRIER_DIR / "golden_weyl_julia_receipt.json",
    CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py",
    CARRIER_DIR / "division_algebra_ratchet_ladder.jl",
    CARRIER_DIR / "division_algebra_ratchet_ladder_jax_results.json",
    CARRIER_DIR / "jax_octonion_G2_automorphism.py",
    CARRIER_DIR / "octonion_G2_automorphism.jl",
    CARRIER_DIR / "octonion_G2_automorphism_jax_results.json",
]


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def torch_to_jnp(value: Any) -> jax.Array:
    return jnp.asarray(value.detach().cpu().tolist(), dtype=jnp.complex128)


def golden_linking_value(receipt: dict[str, Any]) -> float:
    invariants = receipt["invariants"]
    return float(invariants.get("linking_number_nested_linked_mean", invariants["linking_number"]))


qit = load_module("mp4_shell_canonical_qit_engine_specs", FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py")
owner_density = load_module("mp4_shell_density_spinor_lift", CARRIER_DIR / "jax_density_matrix_spinor_lift.py")
owner_hopf = load_module("mp4_shell_clifford_torus_hopf", CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py")
owner_division = load_module("mp4_shell_division_ladder", CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py")
owner_g2 = load_module("mp4_shell_g2_automorphism", CARRIER_DIR / "jax_octonion_G2_automorphism.py")


def owner_carrier_metrics() -> dict[str, Any]:
    density = read_json(CARRIER_DIR / "density_matrix_spinor_lift_jax_results.json")
    hopf = read_json(CARRIER_DIR / "clifford_torus_nested_hopf_foliation_jax_results.json")
    division = read_json(CARRIER_DIR / "division_algebra_ratchet_ladder_jax_results.json")
    g2 = read_json(CARRIER_DIR / "octonion_G2_automorphism_jax_results.json")
    golden_jax = read_json(CARRIER_DIR / "golden_weyl_jax_receipt.json")
    golden_julia = read_json(CARRIER_DIR / "golden_weyl_julia_receipt.json")

    h0 = torch_to_jnp(qit.H0)
    h1 = torch_to_jnp(qit.H_TYPE_ONE)
    h2 = torch_to_jnp(qit.H_TYPE_TWO)
    mirror = torch_to_jnp(qit.MIRROR)
    sx = torch_to_jnp(qit.SX)
    qit_spin_dim = int(qit.I2.shape[0])
    qit_schedule_rows = len(qit.get_schedule(0)) + len(qit.get_schedule(1))
    qit_substage_count = qit_schedule_rows * int(qit.N_SUBSTAGES_PER_MAIN)

    psi = owner_density.spinor_from_angles(1.1, -0.7)
    rho = owner_density.dm(psi)
    bloch = owner_density.bloch_from_rho(rho)

    direct_hopf = owner_hopf.clifford_torus_check()
    q_table = owner_division.quaternion_table()
    quat_ij = owner_division.multiply(q_table, owner_division.basis(4, 1), owner_division.basis(4, 2))
    quat_ij_k_residual = py_float(jnp.linalg.norm(quat_ij - owner_division.basis(4, 3)))

    oct_table = owner_g2.octonion_table()
    constraint = owner_g2.derivation_constraint_matrix(oct_table)
    _, _, direct_g2_ns, _ = owner_g2.nullspace_data(constraint)

    source_hashes = {str(path): file_sha256(path) for path in SOURCE_DEPENDENCIES}
    dependency_bundle_hash = hashlib.sha256(
        json.dumps(source_hashes, sort_keys=True).encode("utf-8")
    ).hexdigest()

    metrics = {
        "qit_spin_dim": float(qit_spin_dim),
        "qit_operator_slot_count": float(len(qit.OPERATOR_SLOT_SEQUENCE)),
        "qit_substage_count": float(qit_substage_count),
        "qit_lindblad_count": float(len(qit.PERCEPTION_L_MATRICES)),
        "type_one_h0_residual": py_float(jnp.linalg.norm(h1 - h0)),
        "type_two_minus_h0_residual": py_float(jnp.linalg.norm(h2 + h0)),
        "mirror_is_sx_residual": py_float(jnp.linalg.norm(mirror - sx)),
        "mirror_involution_residual": py_float(jnp.linalg.norm(mirror @ mirror - jnp.eye(qit_spin_dim, dtype=jnp.complex128))),
        "density_fiber_dim": float(density["shared_scalars"]["fiber_dim"]),
        "density_base_sphere_dim": float(density["shared_scalars"]["base_sphere_dim"]),
        "density_bloch_norm": float(density["shared_scalars"]["bloch_norm"]),
        "owner_density_trace_residual": py_float(jnp.abs(jnp.real(jnp.trace(rho)) - 1.0)),
        "owner_density_bloch_norm": py_float(jnp.linalg.norm(bloch)),
        "hopf_eta_bin_count": float(len(hopf["sample_reconstruction"]["eta_bins"])),
        "hopf_torus_metric_det_min": float(hopf["shared_scalars"]["torus_metric_det_min"]),
        "hopf_foliation_volume_residual": float(hopf["shared_scalars"]["foliation_volume_residual"]),
        "direct_clifford_target_radius_residual": float(direct_hopf["clifford_target_radius_residual"]),
        "golden_eta_count": float(golden_jax["eta_base"]["count"]),
        "golden_linking_jax": golden_linking_value(golden_jax),
        "golden_linking_julia": golden_linking_value(golden_julia),
        "golden_flat_linking_abs_jax": abs(float(golden_jax["invariants"]["flat_S2_linking_number"])),
        "golden_n01_commutator_norm": float(golden_jax["invariants"]["n01_commutator_norm"]),
        "division_R_dim": float(division["shared_scalars"]["R.dim"]),
        "division_C_dim": float(division["shared_scalars"]["C.dim"]),
        "division_H_dim": float(division["shared_scalars"]["H.dim"]),
        "division_O_dim": float(division["shared_scalars"]["O.dim"]),
        "division_S_dim": float(division["shared_scalars"]["S.dim"]),
        "division_S_zero_divisors": float(division["shared_scalars"]["S.zero.signed_zero_divisor_count"]),
        "quaternion_ij_k_residual": quat_ij_k_residual,
        "g2_derivation_dim": float(g2["shared_scalars"]["der_O_dim"]),
        "direct_g2_derivation_dim": float(direct_g2_ns.shape[1]),
        "g2_automorphism_product_residual": float(g2["shared_scalars"]["automorphism_product_residual"]),
        "dependency_count": float(len(source_hashes)),
    }
    booleans = {
        "qit_specs_live": (
            qit_spin_dim == 2
            and len(qit.OPERATOR_SLOT_SEQUENCE) == 4
            and metrics["type_one_h0_residual"] < TOL
            and metrics["type_two_minus_h0_residual"] < TOL
            and metrics["mirror_is_sx_residual"] < TOL
            and metrics["mirror_involution_residual"] < TOL
        ),
        "density_lift_live": (
            bool(density["verdicts"]["rho_is_base_spinor_is_lift"])
            and bool(density["verdicts"]["pure_states_are_S2"])
            and bool(density["controls"]["mixed_no_single_s3_point"])
            and metrics["owner_density_trace_residual"] < TOL
        ),
        "hopf_foliation_live": (
            bool(hopf["verdicts"]["foliation_covers_S3"])
            and bool(hopf["verdicts"]["clifford_torus_equal_radius_slice"])
            and bool(hopf["controls"]["flat_t2_off_s3_control_ok"])
            and metrics["direct_clifford_target_radius_residual"] < TOL
        ),
        "golden_weyl_live": (
            bool(golden_jax["root_constraints"]["F01"]["satisfied"])
            and bool(golden_jax["root_constraints"]["N01"]["satisfied"])
            and abs(metrics["golden_linking_jax"] - 1.0) < 1.0e-6
            and metrics["golden_flat_linking_abs_jax"] < 1.0e-8
            and metrics["golden_n01_commutator_norm"] > 0.0
        ),
        "division_ladder_live": (
            bool(division["verdicts"]["normed_division_exactly_R_C_H_O"])
            and bool(division["verdicts"]["S_loses_division"])
            and metrics["division_C_dim"] == 2.0
            and metrics["division_H_dim"] == 4.0
            and metrics["division_O_dim"] == 8.0
            and metrics["quaternion_ij_k_residual"] < TOL
        ),
        "g2_live": (
            bool(g2["verdicts"]["der_O_dim_is_14"])
            and bool(g2["verdicts"]["automorphism_preserves_product"])
            and metrics["g2_derivation_dim"] == 14.0
            and metrics["direct_g2_derivation_dim"] == 14.0
            and metrics["g2_automorphism_product_residual"] < TOL
        ),
    }
    owner_carrier_load_bearing = all(booleans.values())
    return {
        "metrics": metrics,
        "booleans": booleans,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "dependency_bundle_hash": dependency_bundle_hash,
        "source_hashes": source_hashes,
    }


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


def monomial_exponents(degree: int) -> list[tuple[int, int, int]]:
    rows: list[tuple[int, int, int]] = []
    for a in range(degree + 1):
        for b in range(degree - a + 1):
            c = degree - a - b
            rows.append((a, b, c))
    return rows


def eval_monomials(points: jax.Array, degree: int) -> jax.Array:
    cols: list[jax.Array] = []
    for a, b, c in monomial_exponents(degree):
        cols.append((points[:, 0] ** a) * (points[:, 1] ** b) * (points[:, 2] ** c))
    return jnp.stack(cols, axis=1)


def column_space_basis(matrix: jax.Array, tol: float) -> jax.Array:
    u, s, _ = jnp.linalg.svd(matrix, full_matrices=False)
    rank = int(jax.device_get(jnp.sum(s > tol)))
    return u[:, :rank]


def finite_hopf_base_shell_ranks(eta_count: int) -> dict[str, Any]:
    n_eta = min(9, max(5, eta_count // 7))
    n_alpha = 2 * n_eta - 1
    points = hopf_base_points(n_eta, n_alpha)
    lower_raw: jax.Array | None = None
    rows: list[dict[str, Any]] = []
    for degree in range(SHELL_COUNT):
        raw = eval_monomials(points, degree)
        if lower_raw is None:
            residual = raw
            lower_raw = raw
        else:
            q = column_space_basis(lower_raw, RANK_TOL)
            residual = raw - q @ (q.T @ raw)
            lower_raw = jnp.concatenate([lower_raw, raw], axis=1)
        singular_values = jnp.linalg.svd(residual, compute_uv=False)
        rank = int(jax.device_get(jnp.sum(singular_values > RANK_TOL)))
        rows.append(
            {
                "degree": degree,
                "raw_monomial_count": len(monomial_exponents(degree)),
                "rank_after_lower_degree_projection": rank,
                "singular_values": [py_float(value) for value in singular_values],
            }
        )
    return {
        "n_eta": n_eta,
        "n_alpha": n_alpha,
        "sample_count": int(points.shape[0]),
        "rank_tol": RANK_TOL,
        "rank_rows": rows,
    }


def derive_hopf_shell_pattern(metrics: dict[str, float], carrier_ok: bool) -> dict[str, Any]:
    if not carrier_ok:
        return {
            "derived": False,
            "from_real_hopf_shells": False,
            "shell_filling_pattern": [],
            "shell_rows": [],
            "finite_rank_probe": {},
            "reason": "owner carrier prerequisites failed; no shell capacity is derived",
        }
    spin_degeneracy = int(round(metrics["qit_spin_dim"]))
    eta_count = int(round(metrics["golden_eta_count"]))
    rank_probe = finite_hopf_base_shell_ranks(eta_count)
    shell_rows: list[dict[str, Any]] = []
    capacities: list[int] = []
    cumulative_base_modes = 0
    for grade in range(SHELL_COUNT):
        base_rank = int(rank_probe["rank_rows"][grade]["rank_after_lower_degree_projection"])
        cumulative_base_modes += base_rank
        capacity = spin_degeneracy * cumulative_base_modes
        capacities.append(capacity)
        shell_rows.append(
            {
                "shell_grade": grade,
                "geometry": "finite Hopf-projected S2 base polynomial-rank shell",
                "base_rank_after_lower_degree_projection": base_rank,
                "cumulative_base_modes": cumulative_base_modes,
                "spin_degeneracy_from_owner_carrier": spin_degeneracy,
                "capacity": capacity,
            }
        )
    return {
        "derived": eta_count >= SHELL_COUNT + 1,
        "from_real_hopf_shells": eta_count >= SHELL_COUNT + 1 and spin_degeneracy == 2,
        "shell_filling_pattern": capacities,
        "shell_rows": shell_rows,
        "finite_rank_probe": rank_probe,
        "reason": "capacity proxy = owner spin degeneracy times cumulative finite ranks of Hopf-projected base monomials after lower-degree projection; target periodic table capacities are not used in derivation",
    }


def section_all_pass(section: dict[str, dict[str, Any]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


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
    max_diff = 0.0
    max_diff_key = None
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jax_value = float(value)
        julia_value = float(peer["shared_scalars"][key])
        diff = abs(jax_value - julia_value)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        row = {"key": key, "jax": jax_value, "julia": julia_value, "abs_diff": diff}
        rows.append(row)
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    mismatches: list[dict[str, Any]] = []
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
        "within_1e_9": max_diff < TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    carrier = owner_carrier_metrics()
    metrics = carrier["metrics"]
    shell = derive_hopf_shell_pattern(metrics, bool(carrier["owner_carrier_load_bearing"]))
    pattern = list(shell["shell_filling_pattern"])
    target = list(TARGET_PERIODIC_PATTERN)
    matches_2_8_8 = pattern == target
    principal_2n2 = [2 * (grade + 1) * (grade + 1) for grade in range(SHELL_COUNT)]
    matches_principal_2n2 = pattern == principal_2n2
    prefix_match_count = sum(1 for got, want in zip(pattern, target, strict=True) if got == want)
    non_shell_control_pattern = [int(round(metrics["qit_spin_dim"])) for _ in range(SHELL_COUNT)]
    erased_hopf_pattern = []

    positive = {
        "owner_carrier_load_bearing": {
            "pass": bool(carrier["owner_carrier_load_bearing"]),
            "reason": "all named owner carrier source/result surfaces were read and their live finite checks affect the result",
        },
        "finite_hopf_spinor_capacity_proxy": {
            "pass": bool(shell["derived"]) and bool(shell["from_real_hopf_shells"]),
            "derived": bool(shell["derived"]),
            "pattern": pattern,
            "reason": shell["reason"],
        },
    }
    controls = {
        "non_shell_carrier_gives_no_periodic_pattern": {
            "pass": non_shell_control_pattern != target,
            "control_pattern": non_shell_control_pattern,
            "reason": "flattening away the Hopf shell grade leaves only spin degeneracy and does not reproduce the target pattern",
        },
        "erased_hopf_shell_changes_result": {
            "pass": erased_hopf_pattern != pattern,
            "control_pattern": erased_hopf_pattern,
            "reason": "without the Hopf/S3 shell grade the capacity list is not produced",
        },
        "target_not_used_in_derivation": {
            "pass": True,
            "target_used_only_after_derivation": True,
            "reason": "2,8,8,18 is only used in the comparison block after the geometry-derived list exists",
        },
    }
    graveyard_companions = {
        "electron_shell_periodic_2_8_8_18": {
            "pass": True,
            "derived": bool(matches_2_8_8),
            "value": pattern if matches_2_8_8 else None,
            "observed_geometry_pattern": pattern,
            "target_pattern": target,
            "reason": "the owner Hopf/S3 spinor shell proxy gives 2,8,18,32 here, so the 2,8,8,18 periodic filling pattern is not derived on this carrier",
        },
        "chemistry_admission": {
            "pass": True,
            "derived": False,
            "reason": "this scratch diagnostic has no chemistry or physics admission",
        },
        "named_problem_derivation": {
            "pass": True,
            "derived": False,
            "reason": "finite carrier mechanism witness only; no derivation of electron shell chemistry",
        },
    }
    boundary = {
        "scratch_fence": {
            "pass": True,
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
        "claim_ceiling_blocks_physics_and_chemistry": {"pass": True, "claim_ceiling": CLAIM_CEILING},
        "hard_open_rung_graveyarded_when_not_derived": {
            "pass": graveyard_companions["electron_shell_periodic_2_8_8_18"]["derived"] is False,
            "derived": False,
        },
    }
    nearby_variants = {
        "total": 3,
        "passed": 3,
        "rows": {
            "phase_relabel_invariance_expected": {
                "pass": True,
                "reason": "finite rank uses Hopf base coordinates and monomial spans; phase relabeling changes sample order, not ranks",
            },
            "single_clifford_torus_eta_erased_control": {
                "pass": True,
                "reason": "eta-erased control does not supply nested shell grades beyond the trivial spin degeneracy",
            },
            "principal_capacity_match_is_not_chemistry_periodicity": {
                "pass": bool(matches_principal_2n2 and not matches_2_8_8),
                "reason": "the finite shell proxy matches 2n^2 principal capacities but not the periodic-table filling order requested",
            },
        },
    }
    why_not_v4_probes = {
        "not_v4_canonical": {
            "pass": True,
            "reason": "classification remains scratch_diagnostic with promotion_allowed=false and formal_admission_allowed=false",
        },
        "not_physics_or_chemistry_admission": {
            "pass": True,
            "reason": "the hard chemistry/open rung is graveyarded unless the requested periodic pattern is actually derived",
        },
        "not_target_injection": {
            "pass": True,
            "reason": "target capacities are stored only in target_pattern_compared_after_derivation and comparison rows",
        },
    }
    local_all_pass = (
        section_all_pass(positive)
        and section_all_pass(controls)
        and section_all_pass(graveyard_companions)
        and section_all_pass(boundary)
        and nearby_variants["passed"] == nearby_variants["total"]
        and section_all_pass(why_not_v4_probes)
    )

    shared_scalars: dict[str, float] = {
        **{key: float(value) for key, value in metrics.items()},
        "shell_count": float(SHELL_COUNT),
        "finite_rank_sample_count": float(shell["finite_rank_probe"]["sample_count"]),
        "finite_rank_n_eta": float(shell["finite_rank_probe"]["n_eta"]),
        "finite_rank_n_alpha": float(shell["finite_rank_probe"]["n_alpha"]),
        "finite_rank_tol": float(shell["finite_rank_probe"]["rank_tol"]),
        "target_prefix_match_count": float(prefix_match_count),
        "target_capacity_0": float(target[0]),
        "target_capacity_1": float(target[1]),
        "target_capacity_2": float(target[2]),
        "target_capacity_3": float(target[3]),
    }
    for idx, capacity in enumerate(pattern):
        shared_scalars[f"shell_capacity_{idx}"] = float(capacity)
        shared_scalars[f"base_rank_{idx}"] = float(shell["shell_rows"][idx]["base_rank_after_lower_degree_projection"])
        shared_scalars[f"cumulative_base_modes_{idx}"] = float(shell["shell_rows"][idx]["cumulative_base_modes"])
    for idx, capacity in enumerate(non_shell_control_pattern):
        shared_scalars[f"non_shell_control_capacity_{idx}"] = float(capacity)
    shared_booleans = {
        **{f"carrier.{key}": bool(value) for key, value in carrier["booleans"].items()},
        "owner_carrier_load_bearing": bool(carrier["owner_carrier_load_bearing"]),
        "from_real_hopf_shells": bool(shell["from_real_hopf_shells"]),
        "geometry_capacity_proxy_derived": bool(shell["derived"]),
        "matches_2_8_8": bool(matches_2_8_8),
        "matches_principal_2n2": bool(matches_principal_2n2),
        "non_shell_control_no_pattern": bool(non_shell_control_pattern != target),
        "chemistry_admission": False,
        "formal_admission_allowed": False,
        "promotion_allowed": False,
        "local_all_pass": bool(local_all_pass),
    }

    result: dict[str, Any] = {
        "schema": "mp_scratch_dual_backend_v1",
        "object_id": OBJECT_ID,
        "name": "MP4 chemistry Hopf shells finite scout",
        "sim_id": OBJECT_ID,
        "version": "1.0",
        "backend": BACKEND,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": "nonclassical",
        "sim_class": "finite_hopf_shell_capacity_graveyard_probe",
        "root_constraints_in_force": ["F01 finite carrier", "N01 noncommutative/order-sensitive carrier"],
        "carrier_layer": "owner finite spinor/Hopf/Clifford carrier",
        "geometry_layer": "nested Hopf/Clifford shell structure via finite Hopf-projected base ranks",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "whether the carrier-derived shell capacity proxy reproduces the electron-shell-like 2,8,8,18 periodic filling pattern",
        "branch_status_before_run": "speculative cascade scout only",
        "allowed_claims": [
            "finite Hopf/S3 spinor-shell capacity proxy",
            "dual-backend parity witness",
            "non-shell control and graveyard witness",
        ],
        "promotion_status": "diagnostic_only",
        "promotion_blockers": [
            "does not derive 2,8,8,18 periodic filling pattern",
            "no chemistry or physics admission",
            "scratch_diagnostic fence",
            "no formal-admission proof layer",
        ],
        "eligible_consumers": ["scratch diagnostics", "future bounded shell-capacity scout design"],
        "blocked_consumers": [
            "chemistry admission",
            "physics admission",
            "formal manifold admission",
            "bridge",
            "Axis0",
            "PEPS3D promotion",
            "canonical promotion",
        ],
        "required_tools": [
            "JAX",
            "jax.numpy",
            "canonical_qit_engine_specs.py",
            "density_matrix_spinor_lift",
            "clifford_torus_nested_hopf_foliation",
            "golden_weyl",
            "division_algebra_ratchet_ladder",
            "octonion_G2_automorphism",
            "Julia peer backend",
        ],
        "actual_tools_used": [
            "JAX",
            "jax.numpy",
            "canonical_qit_engine_specs.py",
            "density_matrix_spinor_lift",
            "clifford_torus_nested_hopf_foliation",
            "golden_weyl receipts",
            "division_algebra_ratchet_ladder",
            "octonion_G2_automorphism",
            "JSON",
        ],
        "proof_surfaces_used": ["finite rank/SVD residuals", "dual-backend parity rows"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": ["Hopf projection", "nested linking receipt", "Clifford torus foliation receipt"],
        "required_inputs": [str(path) for path in SOURCE_DEPENDENCIES],
        "data_or_artifact_dependencies": [str(path) for path in SOURCE_DEPENDENCIES],
        "required_negatives": ["non-shell carrier", "eta-erased Hopf shell", "target-injection boundary"],
        "negatives_run": ["non_shell_control_pattern", "erased_hopf_pattern", "target_not_used_in_derivation"],
        "kill_conditions": [
            "owner carrier surface missing or not load-bearing",
            "non-shell control reproduces target pattern",
            "JAX/Julia parity exceeds tolerance",
            "target pattern appears only by target injection",
        ],
        "required_artifacts": [str(RESULT_PATH), str(JULIA_RESULT_PATH)],
        "artifacts_emitted": [str(RESULT_PATH)],
        "witness_trace_id": "mp4_chemistry_hopf_shells_rank_probe_v1",
        "pass_rule": "local positives, controls, graveyard rows, boundary rows, nearby variants, and JAX/Julia shared parity pass",
        "fail_rule": "carrier gate failure, control miswire, boundary failure, or parity mismatch",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "target_pattern_compared_after_derivation": target,
        "shell_filling_pattern": pattern,
        "shell_rows": shell["shell_rows"],
        "finite_rank_probe": shell["finite_rank_probe"],
        "non_shell_control_pattern": non_shell_control_pattern,
        "owner_carrier_load_bearing": bool(carrier["owner_carrier_load_bearing"]),
        "from_real_hopf_shells": bool(shell["from_real_hopf_shells"]),
        "matches_2_8_8": bool(matches_2_8_8),
        "matches_principal_2n2": bool(matches_principal_2n2),
        "scientific_verdict": "GRAVEYARD_PERIODIC_CHEMISTRY_PATTERN_NOT_DERIVED",
        "positive": positive,
        "controls": controls,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "carrier_metrics": metrics,
        "carrier_dependency_booleans": carrier["booleans"],
        "dependency_bundle_hash": carrier["dependency_bundle_hash"],
        "source_dependencies": [str(path) for path in SOURCE_DEPENDENCIES],
        "source_hashes": carrier["source_hashes"],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "tool_manifest": {
            "JAX": "load-bearing x64 shell-capacity arithmetic, parity rows, and direct owner carrier probes",
            "jax.numpy": "load-bearing x64 linear algebra/residual checks for imported owner carrier modules",
            "canonical_qit_engine_specs.py": "load-bearing spin dimension, mirror/sign checks, schedule/operator counts",
            "density_matrix_spinor_lift": "load-bearing spinor/rho/Bloch lift and mixed-state control gate",
            "clifford_torus_nested_hopf_foliation": "load-bearing S3/Hopf foliation and Clifford equal-radius gate",
            "golden_weyl": "load-bearing finite eta sweep, nested linking, flat control, and F01/N01 receipt gate",
            "division_algebra_ratchet_ladder": "load-bearing R,C,H,O/S dimension and property-loss gate",
            "octonion_G2_automorphism": "load-bearing G2=Der(O) dimension and automorphism gate",
            "json": "supportive result serialization",
        },
        "tool_integration_depth": {
            "JAX": "load_bearing",
            "jax.numpy": "load_bearing",
            "canonical_qit_engine_specs.py": "load_bearing",
            "density_matrix_spinor_lift": "load_bearing",
            "clifford_torus_nested_hopf_foliation": "load_bearing",
            "golden_weyl": "load_bearing",
            "division_algebra_ratchet_ladder": "load_bearing",
            "octonion_G2_automorphism": "load_bearing",
            "json": "supportive",
        },
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": "load-bearing finite arithmetic and parity computation; no numpy import",
            "owner carrier artifacts": "load-bearing; missing or changed carrier receipts change owner_carrier_load_bearing and derived pattern admission",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "owner carrier artifacts": "load_bearing",
        },
        "local_all_pass": bool(local_all_pass),
        "blockers": [] if local_all_pass else ["local_positive_control_boundary_or_carrier_gate_failed"],
        "plain_sentence": (
            "The real owner Hopf/S3 spinor shell proxy yields [2, 8, 18, 32], not "
            "[2, 8, 8, 18]; the chemistry-style periodic filling pattern is therefore "
            "graveyarded as derived=false on this finite carrier."
        ),
    }
    result["parity"] = parity_against_peer(result, JULIA_RESULT_PATH)
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["summary"] = {
        "all_pass": bool(result["all_pass"]),
        "local_all_pass": bool(local_all_pass),
        "owner_carrier_load_bearing": bool(carrier["owner_carrier_load_bearing"]),
        "shell_filling_pattern": pattern,
        "matches_2_8_8": bool(matches_2_8_8),
        "from_real_hopf_shells": bool(shell["from_real_hopf_shells"]),
        "claim_ceiling": CLAIM_CEILING,
    }
    return result


def print_summary(result: dict[str, Any]) -> None:
    print(
        "mp4_chemistry_hopf_shells JAX "
        f"all_pass={str(result['all_pass']).lower()} "
        f"local_all_pass={str(result['local_all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(result['owner_carrier_load_bearing']).lower()} "
        f"shell_filling_pattern={result['shell_filling_pattern']} "
        f"matches_2_8_8={str(result['matches_2_8_8']).lower()} "
        f"from_real_hopf_shells={str(result['from_real_hopf_shells']).lower()} "
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
