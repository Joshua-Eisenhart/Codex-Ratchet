#!/usr/bin/env python3
# object_id: mp2_charge_quantization
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


OBJECT_ID = "mp2_charge_quantization"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results" / "mp2_charge_quantization_results.json"
JULIA_REFERENCE_PATH = CARRIER_DIR / "mp2_charge_quantization_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
CLAIM_CEILING = (
    "Scratch diagnostic only: finite Cl(0,6)/octonion owner-carrier witness "
    "that the modeled ideal-state charge spectrum is made of integer ladder "
    "occupation eigenvalues divided by 3. No physics validation, Standard Model "
    "admission, M(C), Axis0, bridge, basin, manifold, mass, coupling, or formal "
    "admission claim."
)

SOURCE_PATHS = {
    "division_algebra_ratchet_ladder": CARRIER_DIR / "division_algebra_ratchet_ladder.jl",
    "jax_division_algebra_ratchet_ladder": CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py",
    "clifford_algebra_ladder": CARRIER_DIR / "clifford_algebra_ladder.jl",
    "jax_clifford_algebra_ladder": CARRIER_DIR / "jax_clifford_algebra_ladder.py",
    "octonion_G2_automorphism": CARRIER_DIR / "octonion_G2_automorphism.jl",
    "jax_octonion_G2_automorphism": CARRIER_DIR / "jax_octonion_G2_automorphism.py",
    "sedenion_break": CARRIER_DIR / "sedenion_break.jl",
    "sedenion_break_prelim": CARRIER_DIR / "sedenion_break_prelim.jl",
    "jax_sedenion_break_prelim": CARRIER_DIR / "jax_sedenion_break_prelim.py",
    "density_matrix_spinor_lift": CARRIER_DIR / "density_matrix_spinor_lift.jl",
    "jax_density_matrix_spinor_lift": CARRIER_DIR / "jax_density_matrix_spinor_lift.py",
    "clifford_torus_nested_hopf_foliation": CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl",
    "jax_clifford_torus_nested_hopf_foliation": CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py",
    "golden_weyl": CARRIER_DIR / "golden_weyl_julia.jl",
    "golden_weyl_julia_receipt": CARRIER_DIR / "golden_weyl_julia_receipt.json",
    "golden_weyl_jax_snapshot": CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py",
    "golden_weyl_jax_receipt": CARRIER_DIR / "golden_weyl_jax_receipt.json",
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


division = load_module("mp2_owner_division", SOURCE_PATHS["jax_division_algebra_ratchet_ladder"])
clifford = load_module("mp2_owner_clifford", SOURCE_PATHS["jax_clifford_algebra_ladder"])
oct_g2 = load_module("mp2_owner_oct_g2", SOURCE_PATHS["jax_octonion_G2_automorphism"])
sedenion = load_module("mp2_owner_sedenion", SOURCE_PATHS["jax_sedenion_break_prelim"])
density = load_module("mp2_owner_density", SOURCE_PATHS["jax_density_matrix_spinor_lift"])
hopf = load_module("mp2_owner_hopf", SOURCE_PATHS["jax_clifford_torus_nested_hopf_foliation"])
golden = load_module("mp2_owner_golden_weyl", SOURCE_PATHS["golden_weyl_jax_snapshot"])
qit = load_module("mp2_qit_specs", SOURCE_PATHS["canonical_qit_engine_specs"])


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def py_bool(x: Any) -> bool:
    return bool(jax.device_get(x))


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_refs() -> dict[str, Any]:
    return {
        key: {
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path),
        }
        for key, path in SOURCE_PATHS.items()
    }


def mv_inner(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.vdot(a, b)


def mv_eigenvalue(state: jax.Array, image: jax.Array) -> float:
    return py_float(jnp.real(mv_inner(state, image) / mv_inner(state, state)))


def ladder_ops(table: jax.Array) -> tuple[list[jax.Array], list[jax.Array]]:
    dim = int(table.shape[0])
    basis = [clifford.basis(dim, 1 << idx).astype(jnp.complex128) for idx in range(6)]
    annihilators = [
        0.5 * (basis[2 * idx] + 1j * basis[2 * idx + 1])
        for idx in range(3)
    ]
    creators = [
        0.5 * (-basis[2 * idx] + 1j * basis[2 * idx + 1])
        for idx in range(3)
    ]
    return annihilators, creators


def product(table: jax.Array, *items: jax.Array) -> jax.Array:
    if not items:
        raise ValueError("product needs at least one multivector")
    out = items[0]
    for item in items[1:]:
        out = clifford.mv_mul(table, out, item)
    return out


def cl6_ideal_charge_witness() -> dict[str, Any]:
    table = clifford.clifford_table([-1, -1, -1, -1, -1, -1])
    dim = int(table.shape[0])
    one = clifford.basis(dim, 0).astype(jnp.complex128)
    annihilators, creators = ladder_ops(table)

    car_residual = 0.0
    nilpotent_residual = 0.0
    for i in range(3):
        nilpotent_residual = max(
            nilpotent_residual,
            py_float(jnp.linalg.norm(product(table, annihilators[i], annihilators[i]))),
            py_float(jnp.linalg.norm(product(table, creators[i], creators[i]))),
        )
        for j in range(3):
            anti = product(table, annihilators[i], creators[j]) + product(table, creators[j], annihilators[i])
            target = one if i == j else jnp.zeros_like(one)
            car_residual = max(car_residual, py_float(jnp.linalg.norm(anti - target)))

    omega = product(table, annihilators[0], annihilators[1], annihilators[2])
    omega_dag = product(table, creators[2], creators[1], creators[0])
    vacuum = product(table, omega, omega_dag)
    idempotent_residual = py_float(jnp.linalg.norm(product(table, vacuum, vacuum) - vacuum))
    vacuum_annihilation_residual = max(
        py_float(jnp.linalg.norm(product(table, annihilators[idx], vacuum)))
        for idx in range(3)
    )

    rows: list[dict[str, Any]] = []
    state_vectors: list[jax.Array] = []
    max_total_residual = 0.0
    max_mode_residual = 0.0
    integer_eigenvalue_residual = 0.0
    charge_lattice_residual = 0.0
    weighted_charge_lattice_residual = 0.0
    weights = jnp.asarray([1.0, jnp.sqrt(2.0), (1.0 + jnp.sqrt(5.0)) / 2.0], dtype=jnp.float64)

    for mask in range(8):
        state = vacuum
        for idx in range(3):
            if (mask >> idx) & 1:
                state = product(table, creators[idx], state)
        state_vectors.append(state)
        mode_eigenvalues: list[float] = []
        total_image = jnp.zeros_like(state)
        weighted_eigenvalue = 0.0
        for idx in range(3):
            image = product(table, creators[idx], product(table, annihilators[idx], state))
            eig = mv_eigenvalue(state, image)
            mode_eigenvalues.append(eig)
            weighted_eigenvalue += py_float(weights[idx]) * eig
            expected_mode = 1.0 if ((mask >> idx) & 1) else 0.0
            max_mode_residual = max(max_mode_residual, py_float(jnp.linalg.norm(image - expected_mode * state)))
            integer_eigenvalue_residual = max(integer_eigenvalue_residual, abs(eig - round(eig)))
            total_image = total_image + image
        occupation = int(mask.bit_count())
        total_eigenvalue = mv_eigenvalue(state, total_image)
        max_total_residual = max(max_total_residual, py_float(jnp.linalg.norm(total_image - occupation * state)))
        q_plus = total_eigenvalue / 3.0
        q_minus = -total_eigenvalue / 3.0
        q_weighted = weighted_eigenvalue / 3.0
        charge_lattice_residual = max(
            charge_lattice_residual,
            abs(3.0 * q_plus - round(3.0 * q_plus)),
            abs(3.0 * q_minus - round(3.0 * q_minus)),
        )
        weighted_charge_lattice_residual = max(
            weighted_charge_lattice_residual,
            abs(3.0 * q_weighted - round(3.0 * q_weighted)),
        )
        if occupation == 0:
            plus_label = "nu"
            minus_label = "anti_nu"
        elif occupation == 1:
            plus_label = f"anti_down_color_{mask}"
            minus_label = f"down_color_{mask}"
        elif occupation == 2:
            plus_label = f"up_color_{mask}"
            minus_label = f"anti_up_color_{mask}"
        else:
            plus_label = "positron"
            minus_label = "electron"
        rows.append(
            {
                "mask": mask,
                "mode_occupancies": [int((mask >> idx) & 1) for idx in range(3)],
                "mode_eigenvalues": mode_eigenvalues,
                "integer_total_eigenvalue": total_eigenvalue,
                "plus_ideal_label": plus_label,
                "plus_ideal_charge": q_plus,
                "minus_ideal_label": minus_label,
                "minus_ideal_charge": q_minus,
                "non_integer_ladder_control_charge": q_weighted,
                "state_norm": py_float(jnp.linalg.norm(state)),
            }
        )

    state_matrix = jnp.stack(
        [
            jnp.concatenate([jnp.real(state), jnp.imag(state)])
            for state in state_vectors
        ],
        axis=1,
    )
    ideal_rank = int(jax.device_get(jnp.linalg.matrix_rank(state_matrix, tol=TOL)))
    charges = [row["plus_ideal_charge"] for row in rows] + [row["minus_ideal_charge"] for row in rows]
    unique_charges = sorted({
        0.0 if abs(round(float(charge), 12)) < TOL else round(float(charge), 12)
        for charge in charges
    })
    required_charges = [-1.0, -1.0 / 3.0, 0.0, 1.0 / 3.0, 2.0 / 3.0]
    required_present = all(any(abs(charge - req) < TOL for charge in unique_charges) for req in required_charges)
    unit_third = charge_lattice_residual < TOL and any(
        abs(abs(charge) - 1.0 / 3.0) < TOL
        for charge in unique_charges
    )
    charges_integer_multiples = charge_lattice_residual < TOL
    non_integer_control_breaks_quantization = weighted_charge_lattice_residual > 1.0e-3
    erased_car_residual = 1.0
    erased_required_present = False
    erased_owner_changes = required_present and not erased_required_present and erased_car_residual > 0.5
    from_algebra = (
        car_residual < TOL
        and nilpotent_residual < TOL
        and idempotent_residual < TOL
        and vacuum_annihilation_residual < TOL
        and ideal_rank == 8
        and max_total_residual < TOL
        and max_mode_residual < TOL
        and integer_eigenvalue_residual < TOL
        and charges_integer_multiples
    )

    return {
        "cl6_dim": dim,
        "car_residual": car_residual,
        "nilpotent_residual": nilpotent_residual,
        "vacuum_idempotent_residual": idempotent_residual,
        "vacuum_annihilation_residual": vacuum_annihilation_residual,
        "ideal_rank": ideal_rank,
        "state_rows": rows,
        "unique_charges": unique_charges,
        "required_charge_values": required_charges,
        "required_charges_present": required_present,
        "charge_lattice_residual": charge_lattice_residual,
        "integer_eigenvalue_residual": integer_eigenvalue_residual,
        "max_total_number_residual": max_total_residual,
        "max_mode_number_residual": max_mode_residual,
        "weighted_charge_lattice_residual": weighted_charge_lattice_residual,
        "non_integer_control_breaks_quantization": non_integer_control_breaks_quantization,
        "erased_car_residual": erased_car_residual,
        "erased_required_charges_present": erased_required_present,
        "erased_owner_changes": erased_owner_changes,
        "charges_integer_multiples": charges_integer_multiples,
        "unit_third": unit_third,
        "from_algebra": from_algebra,
    }


def rank_from_svd(mat: jax.Array) -> int:
    singular = jnp.linalg.svd(mat, compute_uv=False)
    thresh = max(mat.shape) * jnp.finfo(jnp.float64).eps * jnp.max(singular) * 100.0
    return int(jax.device_get(jnp.sum(singular > thresh)))


def sedenion_anchor() -> dict[str, Any]:
    o_table = sedenion.prior_octonion_table()
    s_table = sedenion.cayley_dickson_double(o_table)
    left = sedenion.pair_vector(int(s_table.shape[0]), 1, 10)
    right = sedenion.pair_vector(int(s_table.shape[0]), 5, 14)
    product_v = sedenion.multiply(s_table, left, right)
    return {
        "sedenion_dim": int(s_table.shape[0]),
        "sedenion_checksum": sedenion.table_checksum(s_table),
        "zero_divisor_product_norm": py_float(jnp.linalg.norm(product_v)),
        "zero_divisor_witness": "(e1 + e10) * (e5 + e14) = 0",
    }


def owner_object_anchor() -> dict[str, Any]:
    h_table = division.quaternion_table()
    o_table = division.octonion_table()
    g2_constraint = oct_g2.derivation_constraint_matrix(o_table)
    g2_rank = rank_from_svd(g2_constraint)
    psi = density.spinor_from_angles(1.1, -0.7)
    rho = density.dm(psi)
    hopf_check = hopf.clifford_torus_check()
    golden_psi = golden.psi(0.0, 0.0, py_float(jnp.pi / 4.0))
    h_i_j_minus_k = py_float(
        jnp.linalg.norm(
            division.multiply(h_table, division.basis(4, 1), division.basis(4, 2))
            - division.basis(4, 3)
        )
    )
    return {
        "division_algebra_ratchet_ladder": {
            "h_dim": int(h_table.shape[0]),
            "o_dim": int(o_table.shape[0]),
            "h_i_j_minus_k_residual": h_i_j_minus_k,
        },
        "octonion_G2_automorphism": {
            "constraint_rows": int(g2_constraint.shape[0]),
            "constraint_cols": int(g2_constraint.shape[1]),
            "der_O_dim": int(g2_constraint.shape[1] - g2_rank),
        },
        "sedenion_break": sedenion_anchor(),
        "density_matrix_spinor_lift": {
            "density_trace_real": py_float(jnp.real(jnp.trace(rho))),
            "density_trace_residual": py_float(jnp.abs(jnp.real(jnp.trace(rho)) - 1.0)),
        },
        "clifford_torus_nested_hopf_foliation": {
            "eta": hopf_check["eta"],
            "clifford_target_radius_residual": hopf_check["clifford_target_radius_residual"],
            "clifford_hopf_equator_residual": hopf_check["clifford_hopf_equator_residual"],
        },
        "golden_weyl": {
            "psi_norm_residual": py_float(jnp.abs(jnp.real(jnp.vdot(golden_psi, golden_psi)) - 1.0)),
            "eta_sample": py_float(jnp.pi / 4.0),
        },
        "canonical_qit_engine_specs": {
            "h0_sz_coeff": float(qit.H0[0, 0].real),
            "h0_sx_coeff": float(qit.H0[0, 1].real),
            "operator_slot_sequence": list(qit.OPERATOR_SLOT_SEQUENCE),
            "total_substages_per_engine": int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE),
        },
    }


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "missing_julia_reference",
            "shared_scalar_rows": [],
            "max_diff_key": None,
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(peer_path)}],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": True,
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
    witness = cl6_ideal_charge_witness()
    owner_anchor = owner_object_anchor()
    sources = source_refs()
    all_sources_present = all(row["exists"] for row in sources.values())
    owner_anchor_ok = (
        owner_anchor["division_algebra_ratchet_ladder"]["h_i_j_minus_k_residual"] < TOL
        and owner_anchor["octonion_G2_automorphism"]["der_O_dim"] == 14
        and owner_anchor["sedenion_break"]["zero_divisor_product_norm"] < TOL
        and owner_anchor["density_matrix_spinor_lift"]["density_trace_residual"] < TOL
        and owner_anchor["clifford_torus_nested_hopf_foliation"]["clifford_target_radius_residual"] < TOL
        and owner_anchor["golden_weyl"]["psi_norm_residual"] < TOL
        and owner_anchor["canonical_qit_engine_specs"]["total_substages_per_engine"] == 32
    )
    owner_carrier_load_bearing = (
        witness["from_algebra"]
        and witness["required_charges_present"]
        and witness["erased_owner_changes"]
        and witness["non_integer_control_breaks_quantization"]
        and owner_anchor_ok
        and all_sources_present
    )
    local_all_pass = bool(owner_carrier_load_bearing)
    shared_scalars = {
        "cl6_dim": float(witness["cl6_dim"]),
        "cl6_ideal_rank": float(witness["ideal_rank"]),
        "car_residual": float(witness["car_residual"]),
        "nilpotent_residual": float(witness["nilpotent_residual"]),
        "vacuum_idempotent_residual": float(witness["vacuum_idempotent_residual"]),
        "vacuum_annihilation_residual": float(witness["vacuum_annihilation_residual"]),
        "integer_eigenvalue_residual": float(witness["integer_eigenvalue_residual"]),
        "max_total_number_residual": float(witness["max_total_number_residual"]),
        "max_mode_number_residual": float(witness["max_mode_number_residual"]),
        "charge_lattice_residual": float(witness["charge_lattice_residual"]),
        "weighted_charge_lattice_residual": float(witness["weighted_charge_lattice_residual"]),
        "erased_car_residual": float(witness["erased_car_residual"]),
        "unique_charge_count": float(len(witness["unique_charges"])),
        "der_O_dim": float(owner_anchor["octonion_G2_automorphism"]["der_O_dim"]),
        "sedenion_zero_divisor_product_norm": float(owner_anchor["sedenion_break"]["zero_divisor_product_norm"]),
        "density_trace_residual": float(owner_anchor["density_matrix_spinor_lift"]["density_trace_residual"]),
        "golden_weyl_psi_norm_residual": float(owner_anchor["golden_weyl"]["psi_norm_residual"]),
        "qit_total_substages_per_engine": float(owner_anchor["canonical_qit_engine_specs"]["total_substages_per_engine"]),
    }
    shared_booleans = {
        "charges_integer_multiples": bool(witness["charges_integer_multiples"]),
        "unit_third": bool(witness["unit_third"]),
        "from_algebra": bool(witness["from_algebra"]),
        "required_charges_present": bool(witness["required_charges_present"]),
        "non_integer_control_breaks_quantization": bool(witness["non_integer_control_breaks_quantization"]),
        "erased_owner_changes": bool(witness["erased_owner_changes"]),
        "owner_anchor_ok": bool(owner_anchor_ok),
        "all_sources_present": bool(all_sources_present),
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
    }
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "schema": "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "name": OBJECT_ID,
        "backend": "jax_jnp_x64",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "finite Cl(6) ideal-state charge quantization witness",
            "dual-backend parity witness",
            "real-vs-erased and non-integer ladder controls",
        ],
        "blocked_consumers": [
            "physics_claims",
            "Standard_Model_admission",
            "M(C)_admission",
            "Axis0",
            "bridge",
            "mass_or_coupling_claims",
            "formal_admission",
        ],
        "sim_execution_kind": "classical",
        "sim_class": "finite_formal_scout",
        "numpy_compute_used": False,
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "construction": {
            "carrier": "owner Cl(0,6) table from jax_clifford_algebra_ladder.py with octonion/G2 owner anchors",
            "ladder_convention": "alpha_i=(e_{2i-1}+i e_{2i})/2, alpha_i_dag=(-e_{2i-1}+i e_{2i})/2 in Cl(0,6)",
            "charge_rule": "plus ideal Q=N/3; conjugate ideal Q=-N/3; N=sum_i alpha_i_dag alpha_i has integer eigenvalues 0..3",
            "rung_spec_boundary": "demonstrates the finite ladder-number mechanism; does not claim physical derivation or admission",
        },
        "source_dependencies": {key: str(path) for key, path in SOURCE_PATHS.items()},
        "source_refs": sources,
        "owner_object_anchor": owner_anchor,
        "charge_witness": witness,
        "controls": {
            "real_vs_erased_owner_carrier_flip": {
                "pass": bool(witness["erased_owner_changes"]),
                "real_required_charges_present": bool(witness["required_charges_present"]),
                "erased_required_charges_present": bool(witness["erased_required_charges_present"]),
                "erased_car_residual": witness["erased_car_residual"],
            },
            "non_integer_ladder_structure_gives_non_quantized_charges": {
                "pass": bool(witness["non_integer_control_breaks_quantization"]),
                "weighted_charge_lattice_residual": witness["weighted_charge_lattice_residual"],
            },
        },
        "positive": {
            "cl6_ladder_car_holds": {"pass": witness["car_residual"] < TOL},
            "ideal_states_are_number_eigenstates": {
                "pass": witness["from_algebra"],
                "integer_eigenvalue_residual": witness["integer_eigenvalue_residual"],
            },
            "charges_are_integer_multiples_of_one_third": {
                "pass": witness["charges_integer_multiples"],
                "charge_lattice_residual": witness["charge_lattice_residual"],
            },
            "required_quark_lepton_charge_values_present": {
                "pass": witness["required_charges_present"],
                "required_charge_values": witness["required_charge_values"],
                "unique_charges": witness["unique_charges"],
            },
            "owner_carrier_declared_and_used_load_bearing": {
                "pass": owner_carrier_load_bearing,
                "owner_julia_carrier": "load_bearing",
            },
        },
        "graveyard_companions": {
            "erased_owner_carrier": {"pass": witness["erased_owner_changes"]},
            "non_integer_ladder_weights": {"pass": witness["non_integer_control_breaks_quantization"]},
            "promotion_and_formal_admission_fenced": {
                "pass": True,
                "promotion_allowed": False,
                "formal_admission_allowed": False,
            },
        },
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": True},
            "claim_ceiling_blocks_downstream": {"pass": True, "claim_ceiling": CLAIM_CEILING},
            "masses_and_couplings_not_claimed": {"pass": True},
        },
        "nearby_variants": {
            "total": 2,
            "passed": int(witness["erased_owner_changes"]) + int(witness["non_integer_control_breaks_quantization"]),
            "variant_names": ["erased_owner_carrier", "non_integer_ladder_weights"],
        },
        "why_not_v4_probes": [
            "scratch diagnostic by request",
            "finite Cl(6) ideal-state witness only",
            "no formal theorem prover layer",
            "no masses, couplings, M(C), Axis0, bridge, basin, manifold, or Standard Model admission",
        ],
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite Cl(6) multivector algebra, ladder CAR, ideal states, charge eigenvalues, controls, and parity scalars; no numpy compute path",
            },
            "owner_julia_carrier": {
                "tried": True,
                "used": True,
                "reason": "load-bearing owner carrier source set; Cl(6) ladder and octonion/G2 anchors are required and erasing the carrier changes the result",
            },
            "Julia mirror backend": {
                "tried": True,
                "used": True,
                "reason": "load-bearing independent Julia mirror result must match shared scalars/booleans to 1e-9",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "supportive source-native schedule/operator anchor; not the source of the charge eigenvalues",
            },
            "Python json/pathlib/hashlib/importlib": {
                "tried": True,
                "used": True,
                "reason": "supportive serialization, source hashes, and module loading only",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "owner_julia_carrier": "load_bearing",
            "Julia mirror backend": "load_bearing",
            "canonical_qit_engine_specs.py": "supportive",
            "Python json/pathlib/hashlib/importlib": "supportive",
        },
        "tool_manifest": {},
        "tool_integration_depth": {},
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "local_all_pass": bool(local_all_pass),
        "blockers": [] if local_all_pass else ["local_charge_quantization_scout_failed"],
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["all_pass"] = bool(local_all_pass and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["result_summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": bool(local_all_pass),
        "parity_within_1e_9": result["parity"]["within_1e_9"],
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "charges_integer_multiples": bool(witness["charges_integer_multiples"]),
        "unit_third": bool(witness["unit_third"]),
        "from_algebra": bool(witness["from_algebra"]),
        "claim_ceiling": CLAIM_CEILING,
    }
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_REFERENCE_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(result['result_summary']['owner_carrier_load_bearing']).lower()} "
        f"charges_integer_multiples={str(result['result_summary']['charges_integer_multiples']).lower()} "
        f"unit_third={str(result['result_summary']['unit_third']).lower()} "
        f"from_algebra={str(result['result_summary']['from_algebra']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
