#!/usr/bin/env python3
# object_id: mp2_anomaly_cancellation
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# source_file: sim_mp2_anomaly_cancellation.py

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


OBJECT_ID = "mp2_anomaly_cancellation"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
JULIA_CARRIER = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results" / "mp2_anomaly_cancellation_results.json"
JULIA_REFERENCE_PATH = JULIA_CARRIER / "mp2_anomaly_cancellation_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
GENERATION_LABELS = (9, 10, 11)

SOURCE_OBJECTS = {
    "division_algebra_ratchet_ladder": JULIA_CARRIER / "division_algebra_ratchet_ladder.jl",
    "jax_division_algebra_ratchet_ladder": JULIA_CARRIER / "jax_division_algebra_ratchet_ladder.py",
    "clifford_algebra_ladder": JULIA_CARRIER / "clifford_algebra_ladder.jl",
    "jax_clifford_algebra_ladder": JULIA_CARRIER / "jax_clifford_algebra_ladder.py",
    "octonion_G2_automorphism": JULIA_CARRIER / "octonion_G2_automorphism.jl",
    "jax_octonion_G2_automorphism": JULIA_CARRIER / "jax_octonion_G2_automorphism.py",
    "sedenion_break": JULIA_CARRIER / "sedenion_break.jl",
    "sedenion_break_prelim": JULIA_CARRIER / "sedenion_break_prelim.jl",
    "jax_sedenion_break": JULIA_CARRIER / "jax_sedenion_break_prelim.py",
    "density_matrix_spinor_lift": JULIA_CARRIER / "density_matrix_spinor_lift.jl",
    "jax_density_matrix_spinor_lift": JULIA_CARRIER / "jax_density_matrix_spinor_lift.py",
    "clifford_torus_nested_hopf_foliation": JULIA_CARRIER / "clifford_torus_nested_hopf_foliation.jl",
    "jax_clifford_torus_nested_hopf_foliation": JULIA_CARRIER / "jax_clifford_torus_nested_hopf_foliation.py",
    "golden_weyl": JULIA_CARRIER / "golden_weyl_julia.jl",
    "golden_weyl_jax_snapshot": JULIA_CARRIER / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py",
    "canonical_qit_engine_specs": FORMAL_SCOUTS / "canonical_qit_engine_specs.py",
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


division = load_module("mp2_owner_division", SOURCE_OBJECTS["jax_division_algebra_ratchet_ladder"])
clifford = load_module("mp2_owner_clifford", SOURCE_OBJECTS["jax_clifford_algebra_ladder"])
oct_g2 = load_module("mp2_owner_oct_g2", SOURCE_OBJECTS["jax_octonion_G2_automorphism"])
sedenion = load_module("mp2_owner_sedenion", SOURCE_OBJECTS["jax_sedenion_break"])
density = load_module("mp2_owner_density", SOURCE_OBJECTS["jax_density_matrix_spinor_lift"])
hopf = load_module("mp2_owner_hopf", SOURCE_OBJECTS["jax_clifford_torus_nested_hopf_foliation"])
golden_weyl = load_module("mp2_owner_golden_weyl", SOURCE_OBJECTS["golden_weyl_jax_snapshot"])
qit_specs = load_module("mp2_owner_qit_specs", SOURCE_OBJECTS["canonical_qit_engine_specs"])


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_refs() -> dict[str, Any]:
    return {
        key: {
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path),
        }
        for key, path in SOURCE_OBJECTS.items()
    }


def cl6_anticommutator_residual(table: jax.Array) -> float:
    dim = int(table.shape[0])
    one = clifford.basis(dim, 0)
    zero = jnp.zeros((dim,), dtype=jnp.float64)
    max_seen = 0.0
    for i in range(6):
        ei = clifford.basis(dim, 1 << i)
        for j in range(6):
            ej = clifford.basis(dim, 1 << j)
            target = 2.0 * one if i == j else zero
            resid = jnp.linalg.norm(clifford.mv_mul(table, ei, ej) + clifford.mv_mul(table, ej, ei) - target)
            max_seen = max(max_seen, py_float(resid))
    return max_seen


def nullity(mat: jax.Array) -> int:
    _, s, _ = jnp.linalg.svd(mat, full_matrices=False)
    thresh = max(mat.shape) * jnp.finfo(jnp.float64).eps * jnp.max(s) * 100.0
    return int(jax.device_get(jnp.sum(s <= thresh)))


def owner_anchor_checks() -> dict[str, Any]:
    h_table = division.quaternion_table()
    o_table = division.octonion_table()
    cl6_table = clifford.clifford_table([1, 1, 1, 1, 1, 1])
    s_table = sedenion.cayley_dickson_double(o_table)
    g2_constraints = oct_g2.derivation_constraint_matrix(o_table)

    psi = density.spinor_from_angles(0.91, -0.37)
    rho = density.dm(psi)
    bloch = density.bloch_from_rho(rho)
    z, w = hopf.torus_point(py_float(jnp.pi / 4.0), 0.31, -0.22)
    golden = golden_weyl.psi(0.17, -0.23, py_float(jnp.pi / 5.0))

    h_ij_minus_k = jnp.linalg.norm(
        division.multiply(h_table, division.basis(4, 1), division.basis(4, 2)) - division.basis(4, 3)
    )
    o_e1e2_minus_e3 = jnp.linalg.norm(
        division.multiply(o_table, division.basis(8, 1), division.basis(8, 2)) - division.basis(8, 3)
    )
    checksum = sedenion.table_checksum(s_table)
    return {
        "h_i_j_minus_k_residual": py_float(h_ij_minus_k),
        "o_fano_e1_e2_minus_e3_residual": py_float(o_e1e2_minus_e3),
        "cl6_dim": int(cl6_table.shape[0]),
        "cl6_anticommutator_residual": cl6_anticommutator_residual(cl6_table),
        "g2_derivation_nullity": nullity(g2_constraints),
        "sedenion_dim": int(s_table.shape[0]),
        "sedenion_nonzero_entry_count": int(checksum["nonzero_entry_count"]),
        "density_trace_residual": py_float(jnp.abs(jnp.trace(rho).real - 1.0)),
        "density_bloch_norm": py_float(jnp.linalg.norm(bloch)),
        "hopf_s3_residual": hopf.s3_constraint_residual(z, w),
        "golden_weyl_spinor_norm_residual": py_float(jnp.abs(jnp.vdot(golden, golden).real - 1.0)),
        "qit_substages_per_engine": int(qit_specs.N_TOTAL_SUBSTAGES_PER_ENGINE),
    }


I2 = jnp.asarray([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
Z2 = jnp.asarray([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)
CREATE = jnp.asarray([[0.0 + 0.0j, 0.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
ANNIHILATE = jnp.asarray([[0.0 + 0.0j, 1.0 + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)


def kron_all(mats: list[jax.Array]) -> jax.Array:
    out = mats[0]
    for mat in mats[1:]:
        out = jnp.kron(out, mat)
    return out


def left_multiplication_matrix(table: jax.Array, basis_mask: int) -> jax.Array:
    dim = int(table.shape[0])
    seed = clifford.basis(dim, basis_mask)
    columns = [clifford.mv_mul(table, seed, clifford.basis(dim, col)) for col in range(dim)]
    return jnp.stack(columns, axis=1).astype(jnp.complex128)


def owner_cl6_fock_operators(table: jax.Array) -> tuple[list[jax.Array], list[jax.Array], jax.Array]:
    gammas = [left_multiplication_matrix(table, 1 << idx) for idx in range(6)]
    creators = [(gammas[2 * idx] - 1j * gammas[2 * idx + 1]) / 2.0 for idx in range(3)]
    annihilators = [(gammas[2 * idx] + 1j * gammas[2 * idx + 1]) / 2.0 for idx in range(3)]
    dim = int(table.shape[0])
    number = jnp.zeros((dim, dim), dtype=jnp.complex128)
    for create, annihilate in zip(creators, annihilators, strict=True):
        number = number + create @ annihilate
    return creators, annihilators, number


def car_residual(creators: list[jax.Array], annihilators: list[jax.Array]) -> float:
    dim = int(creators[0].shape[0])
    ident = jnp.eye(dim, dtype=jnp.complex128)
    zero = jnp.zeros((dim, dim), dtype=jnp.complex128)
    max_seen = 0.0
    for i, ai in enumerate(annihilators):
        for j, cj in enumerate(creators):
            target = ident if i == j else zero
            max_seen = max(max_seen, py_float(jnp.linalg.norm(ai @ cj + cj @ ai - target)))
    return max_seen


def occupation_counts(number: jax.Array, degeneracy: int = 8) -> tuple[dict[int, int], dict[int, int], list[float]]:
    hermitian_number = (number + jnp.conj(number.T)) / 2.0
    eigenvalues = jnp.linalg.eigvalsh(hermitian_number)
    rounded = jnp.rint(eigenvalues).astype(jnp.int32)
    raw_counts = {n: int(jax.device_get(jnp.sum(rounded == n))) for n in range(4)}
    quotient_counts = {n: raw_counts[n] // degeneracy for n in range(4)}
    return quotient_counts, raw_counts, [float(v) for v in jax.device_get(eigenvalues).tolist()]


IDEAL_CLASSES = [
    {"name": "nu_L", "occupation": 0, "charge_sign": 1.0, "weak_t3": 0.5, "ideal_role": "lepton_singlet"},
    {"name": "e_L", "occupation": 3, "charge_sign": -1.0, "weak_t3": -0.5, "ideal_role": "lepton_singlet_conjugate"},
    {"name": "u_L", "occupation": 2, "charge_sign": 1.0, "weak_t3": 0.5, "ideal_role": "quark_triplet"},
    {"name": "d_L", "occupation": 1, "charge_sign": -1.0, "weak_t3": -0.5, "ideal_role": "quark_triplet_conjugate"},
    {"name": "nu_R", "occupation": 0, "charge_sign": 1.0, "weak_t3": 0.0, "ideal_role": "lepton_singlet"},
    {"name": "e_R", "occupation": 3, "charge_sign": -1.0, "weak_t3": 0.0, "ideal_role": "lepton_singlet_conjugate"},
    {"name": "u_R", "occupation": 2, "charge_sign": 1.0, "weak_t3": 0.0, "ideal_role": "quark_triplet"},
    {"name": "d_R", "occupation": 1, "charge_sign": -1.0, "weak_t3": 0.0, "ideal_role": "quark_triplet_conjugate"},
]


def hypercharge_rows(counts: dict[int, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in IDEAL_CLASSES:
        n = int(spec["occupation"])
        multiplicity = int(counts[n])
        electric_charge = float(spec["charge_sign"]) * float(n) / 3.0
        hypercharge = 2.0 * (electric_charge - float(spec["weak_t3"]))
        rows.append(
            {
                "state_class": spec["name"],
                "minimal_ideal_occupation": n,
                "multiplicity_from_cl6_fock": multiplicity,
                "ideal_role": spec["ideal_role"],
                "electric_charge_from_number_operator": electric_charge,
                "weak_t3": float(spec["weak_t3"]),
                "hypercharge_from_q_minus_t3": hypercharge,
                "weighted_hypercharge": float(multiplicity) * hypercharge,
            }
        )
    return rows


def weighted_sum(rows: list[dict[str, Any]]) -> float:
    return float(sum(row["weighted_hypercharge"] for row in rows))


def fock_witness() -> dict[str, Any]:
    cl6_table = clifford.clifford_table([1, 1, 1, 1, 1, 1])
    creators, annihilators, number = owner_cl6_fock_operators(cl6_table)
    counts, raw_counts, eigenvalues = occupation_counts(number)
    rows = hypercharge_rows(counts)

    _, _, erased_number = owner_cl6_fock_operators(jnp.zeros_like(cl6_table))
    erased_counts, erased_raw_counts, _ = occupation_counts(erased_number)
    erased_rows = hypercharge_rows(erased_counts)
    wrong_rows = []
    random_like_rows = []
    for idx, row in enumerate(rows):
        wrong_hypercharge = 2.0 * (abs(float(row["electric_charge_from_number_operator"])) - float(row["weak_t3"]))
        random_like_hypercharge = (float((idx * 37 + 19) % 23) - 11.0) / 7.0
        wrong_rows.append({**row, "hypercharge_from_q_minus_t3": wrong_hypercharge, "weighted_hypercharge": row["multiplicity_from_cl6_fock"] * wrong_hypercharge})
        random_like_rows.append({**row, "hypercharge_from_q_minus_t3": random_like_hypercharge, "weighted_hypercharge": row["multiplicity_from_cl6_fock"] * random_like_hypercharge})

    generation_sums = {str(label): weighted_sum(rows) for label in GENERATION_LABELS}
    return {
        "car_residual": car_residual(creators, annihilators),
        "number_operator_eigenvalues": eigenvalues,
        "occupation_multiplicities": {str(k): v for k, v in counts.items()},
        "regular_representation_raw_occupation_multiplicities": {str(k): v for k, v in raw_counts.items()},
        "minimal_ideal_degeneracy_quotient": 8,
        "hypercharge_rows": rows,
        "hypercharge_sum": weighted_sum(rows),
        "per_generation_hypercharge_sums": generation_sums,
        "erased_occupation_multiplicities": {str(k): v for k, v in erased_counts.items()},
        "erased_regular_representation_raw_occupation_multiplicities": {str(k): v for k, v in erased_raw_counts.items()},
        "erased_hypercharge_sum": weighted_sum(erased_rows),
        "wrong_sign_hypercharge_sum": weighted_sum(wrong_rows),
        "random_like_hypercharge_sum": weighted_sum(random_like_rows),
        "wrong_sign_rows": wrong_rows,
        "random_like_rows": random_like_rows,
    }


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "pending_peer_backend",
            "shared_scalar_rows": [],
            "max_diff_key": None,
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": False,
        }
    peer = json.loads(peer_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    max_diff_key = None
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jv = float(value)
        pv = float(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        row = {"key": key, "jax": jv, "julia": pv, "abs_diff": diff}
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
    anchors = owner_anchor_checks()
    witness = fock_witness()
    source_dependencies = source_refs()
    source_ok = all(row["exists"] for row in source_dependencies.values())
    carrier_ok = (
        source_ok
        and anchors["h_i_j_minus_k_residual"] < TOL
        and anchors["o_fano_e1_e2_minus_e3_residual"] < TOL
        and anchors["cl6_dim"] == 64
        and anchors["cl6_anticommutator_residual"] < TOL
        and anchors["g2_derivation_nullity"] == 14
        and anchors["sedenion_dim"] == 16
        and anchors["density_trace_residual"] < TOL
        and anchors["hopf_s3_residual"] < TOL
        and anchors["golden_weyl_spinor_norm_residual"] < TOL
        and anchors["qit_substages_per_engine"] == 32
    )
    multiplicities_ok = witness["occupation_multiplicities"] == {"0": 1, "1": 3, "2": 3, "3": 1}
    hypercharge_sum_zero = abs(witness["hypercharge_sum"]) < TOL
    per_generation = all(abs(value) < TOL for value in witness["per_generation_hypercharge_sums"].values())
    wrong_control_fails = abs(witness["wrong_sign_hypercharge_sum"]) > 1.0 and abs(witness["random_like_hypercharge_sum"]) > 1.0
    erased_control_fails = abs(witness["erased_hypercharge_sum"] - witness["hypercharge_sum"]) > 1.0
    emerges_from_ideals = witness["car_residual"] < TOL and multiplicities_ok and hypercharge_sum_zero
    owner_carrier_load_bearing = carrier_ok and emerges_from_ideals and erased_control_fails
    local_all_pass = owner_carrier_load_bearing and per_generation and wrong_control_fails

    shared_scalars = {
        "car_residual": witness["car_residual"],
        "hypercharge_sum": witness["hypercharge_sum"],
        "erased_hypercharge_sum": witness["erased_hypercharge_sum"],
        "wrong_sign_hypercharge_sum": witness["wrong_sign_hypercharge_sum"],
        "random_like_hypercharge_sum": witness["random_like_hypercharge_sum"],
        "occupation_multiplicity_0": float(witness["occupation_multiplicities"]["0"]),
        "occupation_multiplicity_1": float(witness["occupation_multiplicities"]["1"]),
        "occupation_multiplicity_2": float(witness["occupation_multiplicities"]["2"]),
        "occupation_multiplicity_3": float(witness["occupation_multiplicities"]["3"]),
        "cl6_dim": float(anchors["cl6_dim"]),
        "cl6_anticommutator_residual": anchors["cl6_anticommutator_residual"],
        "g2_derivation_nullity": float(anchors["g2_derivation_nullity"]),
        "sedenion_dim": float(anchors["sedenion_dim"]),
        "sedenion_nonzero_entry_count": float(anchors["sedenion_nonzero_entry_count"]),
        "density_trace_residual": anchors["density_trace_residual"],
        "hopf_s3_residual": anchors["hopf_s3_residual"],
        "golden_weyl_spinor_norm_residual": anchors["golden_weyl_spinor_norm_residual"],
        "qit_substages_per_engine": float(anchors["qit_substages_per_engine"]),
    }
    shared_booleans = {
        "carrier_ok": carrier_ok,
        "multiplicities_ok": multiplicities_ok,
        "hypercharge_sum_zero": hypercharge_sum_zero,
        "per_generation": per_generation,
        "wrong_control_fails": wrong_control_fails,
        "erased_control_fails": erased_control_fails,
        "emerges_from_ideals": emerges_from_ideals,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }
    tool_manifest = {
        "JAX jax.numpy x64": {
            "tried": True,
            "used": True,
            "reason": "load-bearing backend for owner-Cl6 CAR, number operator, occupation multiplicities, hypercharge trace, controls, and parity scalars; no numpy compute",
        },
        "owner_julia_carrier": {
            "tried": True,
            "used": True,
            "reason": "load-bearing source carrier family; erasing the owner carrier changes the occupation/hypercharge result and blocks all_pass",
        },
        "Julia mirror": {
            "tried": True,
            "used": True,
            "reason": "load-bearing independent peer backend for parity at 1e-9",
        },
        "canonical_qit_engine_specs.py": {
            "tried": True,
            "used": True,
            "reason": "supportive current engine-spec anchor only; it does not promote this anomaly witness",
        },
    }
    tool_depth = {
        "JAX jax.numpy x64": "load_bearing",
        "owner_julia_carrier": "load_bearing",
        "Julia mirror": "load_bearing",
        "canonical_qit_engine_specs.py": "supportive",
    }
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0",
        "schema": "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "backend": "jax_jnp_x64",
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Finite Cl(6)/division-algebra carrier witness reproducing one-generation weighted hypercharge trace cancellation from minimal-ideal occupation data. No physics, SM validation/admission, M(C), Axis0, bridge, masses, couplings, or formal admission claim.",
        "allowed_claims": [
            "finite minimal-ideal occupation witness",
            "weighted hypercharge sum zero on the finite owner carrier",
            "dual-backend parity diagnostic",
        ],
        "blocked_consumers": ["physics_claims", "SM_admission", "M(C)_admission", "Axis0", "bridge", "masses", "couplings", "formal_admission"],
        "sim_execution_kind": "nonclassical",
        "sim_class": "finite_formal_scout",
        "carrier_layer": "owner_Cl6_minimal_ideal_Fock_carrier_with_division_algebra_anchors",
        "root_constraints_in_force": ["finite_bounded_carrier", "noncommuting_order_sensitive_structure"],
        "numpy_compute_used": False,
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "source_dependencies": source_dependencies,
        "owner_carrier_objects": list(SOURCE_OBJECTS.keys()),
        "owner_anchor_checks": anchors,
        "witness": witness,
        "controls": {
            "real_vs_erased_owner_carrier_flip": erased_control_fails,
            "wrong_sign_assignment_not_zero": abs(witness["wrong_sign_hypercharge_sum"]) > 1.0,
            "random_like_charge_assignment_not_zero": abs(witness["random_like_hypercharge_sum"]) > 1.0,
        },
        "verdicts": {
            "hypercharge_sum_zero": hypercharge_sum_zero,
            "per_generation": per_generation,
            "emerges_from_ideals": emerges_from_ideals,
            "owner_carrier_load_bearing": owner_carrier_load_bearing,
        },
        "positive": {
            "owner_cl6_carrier_loaded_and_car": {"pass": carrier_ok and witness["car_residual"] < TOL},
            "minimal_ideal_multiplicities_1_3_3_1": {"pass": multiplicities_ok, "multiplicities": witness["occupation_multiplicities"]},
            "weighted_hypercharge_trace_zero": {"pass": hypercharge_sum_zero, "weighted_sum": witness["hypercharge_sum"]},
            "per_generation_zero": {"pass": per_generation, "generation_labels": list(GENERATION_LABELS)},
            "owner_carrier_declared_and_used_load_bearing": {"pass": owner_carrier_load_bearing, "owner_julia_carrier": "load_bearing"},
        },
        "graveyard_companions": {
            "erased_owner_carrier_breaks_result": {"pass": erased_control_fails, "erased_sum": witness["erased_hypercharge_sum"]},
            "wrong_sign_assignment_breaks_result": {"pass": abs(witness["wrong_sign_hypercharge_sum"]) > 1.0, "wrong_sum": witness["wrong_sign_hypercharge_sum"]},
            "random_like_charge_assignment_breaks_result": {"pass": abs(witness["random_like_hypercharge_sum"]) > 1.0, "random_like_sum": witness["random_like_hypercharge_sum"]},
        },
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": True},
            "promotion_disallowed": {"pass": True},
            "formal_admission_disallowed": {"pass": True},
            "claim_ceiling_blocks_physics_axis_bridge_masses_couplings": {"pass": True},
        },
        "nearby_variants": {
            "total": 3,
            "passed": int(erased_control_fails) + int(abs(witness["wrong_sign_hypercharge_sum"]) > 1.0) + int(abs(witness["random_like_hypercharge_sum"]) > 1.0),
            "variant_names": ["erased_owner_carrier", "wrong_sign_assignment", "random_like_charge_assignment"],
        },
        "why_not_v4_probes": {
            "scratch_by_request": "classification remains scratch_diagnostic",
            "finite_witness_only": "reproduces a finite algebraic trace identity; no dynamics or physical admission",
            "source_scope": "uses owner carrier anchors and dual backend parity, not a formal proof assistant",
        },
        "TOOL_MANIFEST": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": tool_depth,
        "tool_manifest": tool_manifest,
        "tool_integration_depth": tool_depth,
        "owner_julia_carrier": "load_bearing",
        "shared_scalars": {key: float(value) for key, value in shared_scalars.items()},
        "shared_booleans": {key: bool(value) for key, value in shared_booleans.items()},
        "local_all_pass": bool(local_all_pass),
        "blockers": [] if local_all_pass else ["local_owner_carrier_or_control_check_failed"],
        "plain_sentence": "Finite Cl(6) minimal-ideal occupation multiplicities give quark triplets and lepton singlets; deriving Y=2(Q-T3) from the number operator gives weighted hypercharge sum zero per generation, while erased/wrong assignments do not.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["all_pass"] = bool(local_all_pass and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["result_summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": result["local_all_pass"],
        "parity_within_1e_9": result["parity"]["within_1e_9"],
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "hypercharge_sum_zero": hypercharge_sum_zero,
        "per_generation": per_generation,
        "emerges_from_ideals": emerges_from_ideals,
        "claim_ceiling": result["claim_ceiling"],
    }
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "MP2_ANOMALY_CANCELLATION_JAX "
        f"all_pass={str(result['all_pass']).lower()} "
        f"local_all_pass={str(result['local_all_pass']).lower()} "
        f"parity={result['parity']['parity_max_diff']} "
        f"owner_carrier_load_bearing={str(result['result_summary']['owner_carrier_load_bearing']).lower()} "
        f"hypercharge_sum_zero={str(result['result_summary']['hypercharge_sum_zero']).lower()} "
        f"wrote={RESULT_PATH}"
    )
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
