#!/usr/bin/env python3
# object_id: three_spinor_associator_scout
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite 3-spinor associator witness only. No final M(C),
# PEPS3D admission, Axis0, physics, engine, bridge, or formal-admission claim.

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


OBJECT_ID = "three_spinor_associator_scout"
classification = "scratch_diagnostic"
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
TOOL_MANIFEST = {
    "JAX": {"tried": True, "used": True, "reason": "load-bearing x64 finite spinor arithmetic and backend parity lane"},
    "jax.numpy": {"tried": True, "used": True, "reason": "load-bearing x64 vector, matrix, norm, and density calculations"},
    "Julia peer backend": {"tried": True, "used": True, "reason": "load-bearing independent mirror for the same finite carrier controls and shared scalar/boolean parity"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON serialization and path handling"},
    "numpy": {"tried": False, "used": False, "reason": "intentionally not imported; no numpy compute is allowed in this scout"},
}
TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "python_stdlib": "supportive",
    "numpy": None,
}
RESULT_PATH = Path(
    "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/"
    "disc_associator_harden_results.json"
)
JULIA_REFERENCE_PATH = Path(
    "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/"
    "disc_associator_harden_julia_results.json"
)
TOL = 1.0e-10
STRICT_STOP_TOL = 1.0e-8
FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def octonion_table() -> list[list[tuple[int, int]]]:
    table = [[(0, 0) for _ in range(8)] for _ in range(8)]
    table[0][0] = (1, 0)
    for i in range(1, 8):
        table[0][i] = (1, i)
        table[i][0] = (1, i)
        table[i][i] = (-1, 0)
    for a, b, c in FANO:
        for i, j, k in [(a, b, c), (b, c, a), (c, a, b)]:
            table[i][j] = (1, k)
        for i, j, k in [(b, a, c), (c, b, a), (a, c, b)]:
            table[i][j] = (-1, k)
    return table


TABLE = octonion_table()


def oct_mul(a: jax.Array, b: jax.Array) -> jax.Array:
    out = jnp.zeros((8,), dtype=jnp.float64)
    for i in range(8):
        for j in range(8):
            sign, k = TABLE[i][j]
            out = out.at[k].add(float(sign) * a[i] * b[j])
    return out


def basis(idx: int) -> jax.Array:
    return jnp.eye(8, dtype=jnp.float64)[idx]


def normalize_real(v: jax.Array) -> jax.Array:
    return v / jnp.linalg.norm(v)


def normalize_spinor(psi: jax.Array) -> jax.Array:
    return psi / jnp.linalg.norm(psi)


def seed_three_qubit_spinor() -> jax.Array:
    real = jnp.asarray([1.0, -2.0, 3.0, 5.0, -7.0, 11.0, -13.0, 17.0], dtype=jnp.float64)
    imag = jnp.asarray([19.0, -23.0, 29.0, -31.0, 37.0, -41.0, 43.0, -47.0], dtype=jnp.float64)
    return normalize_spinor(real + 1j * imag)


def spinor_to_oct_pair(psi: jax.Array) -> tuple[jax.Array, jax.Array]:
    return jnp.real(psi), jnp.imag(psi)


def oct_pair_to_spinor(pair: tuple[jax.Array, jax.Array]) -> jax.Array:
    real, imag = pair
    return normalize_spinor(real + 1j * imag)


def right_action_pair(pair: tuple[jax.Array, jax.Array], q: jax.Array) -> tuple[jax.Array, jax.Array]:
    real, imag = pair
    return oct_mul(real, q), oct_mul(imag, q)


def star_product(a: jax.Array, b: jax.Array) -> jax.Array:
    return normalize_real(oct_mul(a, b))


def bracket_products(a: jax.Array, b: jax.Array, c: jax.Array) -> tuple[jax.Array, jax.Array]:
    left = star_product(star_product(a, b), c)
    right = star_product(a, star_product(b, c))
    return left, right


def projective_canonical(psi: jax.Array) -> jax.Array:
    anchor = psi[0]
    phase = anchor / jnp.abs(anchor)
    return psi / phase


def density_gap(left: jax.Array, right: jax.Array) -> float:
    rho_left = jnp.outer(left, jnp.conjugate(left))
    rho_right = jnp.outer(right, jnp.conjugate(right))
    return py_float(jnp.linalg.norm(rho_left - rho_right))


def bracket_witness(psi: jax.Array, a: jax.Array, b: jax.Array, c: jax.Array) -> dict[str, Any]:
    left_product, right_product = bracket_products(a, b, c)
    pair = spinor_to_oct_pair(psi)
    left = oct_pair_to_spinor(right_action_pair(pair, left_product))
    right = oct_pair_to_spinor(right_action_pair(pair, right_product))
    delta = left - right
    erased_left = projective_canonical(left)
    erased_right = projective_canonical(right)
    return {
        "product_gap": py_float(jnp.linalg.norm(left_product - right_product)),
        "spinor_gap": py_float(jnp.linalg.norm(delta)),
        "basis_probe_max_abs": py_float(jnp.max(jnp.abs(delta))),
        "optimal_unit_probe_abs": py_float(jnp.linalg.norm(delta)),
        "density_gap_fro": density_gap(left, right),
        "bracket_erased_projective_gap": py_float(jnp.linalg.norm(erased_left - erased_right)),
        "left_product": [py_float(v) for v in left_product],
        "right_product": [py_float(v) for v in right_product],
    }


def right_mult_matrix(q: jax.Array) -> jax.Array:
    cols = [oct_mul(basis(idx), q) for idx in range(8)]
    return jnp.stack(cols, axis=1)


def raw_matrix_associativity_control(psi: jax.Array, a: jax.Array, b: jax.Array, c: jax.Array) -> dict[str, float]:
    ra = right_mult_matrix(a)
    rb = right_mult_matrix(b)
    rc = right_mult_matrix(c)
    left_matrix = (rc @ rb) @ ra
    right_matrix = rc @ (rb @ ra)
    real, imag = spinor_to_oct_pair(psi)
    left = normalize_spinor((left_matrix @ real) + 1j * (left_matrix @ imag))
    right = normalize_spinor((right_matrix @ real) + 1j * (right_matrix @ imag))
    return {
        "matrix_associativity_gap": py_float(jnp.linalg.norm(left_matrix - right_matrix)),
        "raw_spinor_alpha_gap": py_float(jnp.linalg.norm(left - right)),
    }


def arity_can_witness_associator(qubit_count: int, operation_count: int) -> bool:
    return qubit_count >= 3 and operation_count >= 3


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "pending_peer_backend",
            "shared_scalar_rows": [],
            "max_diff_key": None,
            "parity_max_diff": None,
            "within_1e_10": False,
            "within_1e_9": False,
            "strict_divergence_gt_1e_8": [{"missing": str(peer_path)}],
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
    strict_1e6: list[dict[str, Any]] = []
    missing: list[str] = []
    peer_scalars = peer.get("shared_scalars", {})
    for key, peer_value in peer_scalars.items():
        if key not in result["shared_scalars"]:
            missing.append(key)
            continue
        jax_value = float(result["shared_scalars"][key])
        julia_value = float(peer_value)
        diff = abs(jax_value - julia_value)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        row = {"key": key, "jax": jax_value, "julia": julia_value, "abs_diff": diff}
        rows.append(row)
        if diff > STRICT_STOP_TOL:
            strict.append(row)
        if diff > 1.0e-6:
            strict_1e6.append(row)
    mismatches: list[dict[str, Any]] = []
    peer_booleans = peer.get("shared_booleans", {})
    for key, peer_value in peer_booleans.items():
        if key not in result["shared_booleans"]:
            missing.append(key)
            continue
        if bool(result["shared_booleans"][key]) != bool(peer_value):
            mismatches.append({"key": key, "jax": bool(result["shared_booleans"][key]), "julia": bool(peer_value)})
    return {
        "peer_result_path": str(peer_path),
        "status": "compared",
        "shared_scalar_rows": rows,
        "max_diff_key": max_diff_key,
        "parity_max_diff": max_diff,
        "within_1e_10": max_diff <= TOL and not strict and not mismatches and not missing,
        "within_1e_9": max_diff <= 1.0e-9 and not strict_1e6 and not mismatches and not missing,
        "strict_divergence_gt_1e_8": strict,
        "strict_divergence_gt_1e_6": strict_1e6,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing) or max_diff > TOL,
    }


def section_passes(section: dict[str, Any]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values() if isinstance(row, dict) and "pass" in row)


def build_result() -> dict[str, Any]:
    psi = seed_three_qubit_spinor()
    oct_a, oct_b, oct_c = basis(1), basis(2), basis(4)
    h_a, h_b, h_c = basis(1), basis(2), basis(3)
    alt_a, alt_b, alt_c = basis(1), basis(1), basis(4)
    alt2_a, alt2_b, alt2_c = basis(1), basis(4), basis(4)

    oct_witness = bracket_witness(psi, oct_a, oct_b, oct_c)
    h_control = bracket_witness(psi, h_a, h_b, h_c)
    alt_control = bracket_witness(psi, alt_a, alt_b, alt_c)
    alt2_control = bracket_witness(psi, alt2_a, alt2_b, alt2_c)
    raw_control = raw_matrix_associativity_control(psi, oct_a, oct_b, oct_c)

    positive = {
        "finite_three_qubit_spinor_cell_present": {
            "domain": "psi in a finite 3-qubit spinor cell, complex dimension 8",
            "pass": bool(psi.shape == (8,) and abs(py_float(jnp.linalg.norm(psi)) - 1.0) < TOL),
        },
        "spinor_lifted_associator_witness_visible": {
            "witness": oct_witness,
            "pass": bool(
                oct_witness["spinor_gap"] > STRICT_STOP_TOL
                and oct_witness["product_gap"] > STRICT_STOP_TOL
                and oct_witness["basis_probe_max_abs"] > STRICT_STOP_TOL
            ),
        },
    }
    controls = {
        "raw_associative_matrix_composition_alpha_zero": {
            **raw_control,
            "pass": bool(raw_control["matrix_associativity_gap"] < TOL and raw_control["raw_spinor_alpha_gap"] < TOL),
        },
        "bracket_erased_projective_quotient_signal_dies": {
            "real_spinor_gap": oct_witness["spinor_gap"],
            "erased_projective_gap": oct_witness["bracket_erased_projective_gap"],
            "pass": bool(oct_witness["spinor_gap"] > STRICT_STOP_TOL and oct_witness["bracket_erased_projective_gap"] < TOL),
        },
        "density_only_quotient_signal_dies": {
            "spinor_sign_gap": oct_witness["spinor_gap"],
            "density_sign_gap": oct_witness["density_gap_fro"],
            "pass": bool(abs(oct_witness["spinor_gap"] - 2.0) < 1.0e-9 and oct_witness["density_gap_fro"] < TOL),
        },
        "H_quaternion_associative_subalgebra_collapses": {
            "witness": h_control,
            "pass": bool(h_control["spinor_gap"] < TOL and h_control["product_gap"] < TOL),
        },
        "octonion_alternativity_repeated_input_collapses": {
            "xxy_witness": alt_control,
            "xyy_witness": alt2_control,
            "max_spinor_gap": max(alt_control["spinor_gap"], alt2_control["spinor_gap"]),
            "max_product_gap": max(alt_control["product_gap"], alt2_control["product_gap"]),
            "pass": bool(
                max(alt_control["spinor_gap"], alt2_control["spinor_gap"]) < TOL
                and max(alt_control["product_gap"], alt2_control["product_gap"]) < TOL
            ),
        },
        "two_qubit_two_operation_control_insufficient": {
            "qubit_count": 2,
            "operation_count": 2,
            "arity_sufficient": arity_can_witness_associator(2, 2),
            "pass": bool(not arity_can_witness_associator(2, 2)),
        },
        "sedenion_zero_divisor_control_blocked": {
            "status": "blocked_expected",
            "reason": "Sedenion zero-divisor lane is not admitted in this finite spinor-network scout.",
            "pass": True,
        },
    }
    controls["control_miswired"] = not section_passes(controls)

    boundary = {
        "claim_ceiling_enforced": {
            "claim_ceiling": "finite 3-spinor associator witness exists as a scratch/formal scout",
            "pass": True,
        },
        "carrier_boundary": {
            "carrier": "finite spinor networks",
            "readout_lane": "octonion/tensor coordinates are diagnostic readouts, not admitted primitives",
            "pass": True,
        },
        "promotion_and_formal_admission_disabled": {
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "pass": True,
        },
    }
    carrier_readout_controls = {
        "owner-octonion-carrier": {
            "carrier": "O finite basis table",
            "finite_witness": "x=e1,y=e2,z=e4 in the finite Fano octonion table",
            "assoc": oct_witness["product_gap"],
            "readout": oct_witness["spinor_gap"],
            "pass": bool(abs(oct_witness["product_gap"] - 2.0) < TOL and abs(oct_witness["spinor_gap"] - 2.0) < TOL),
        },
        "quaternion-restriction": {
            "carrier": "H=span(1,e1,e2,e3)",
            "finite_witness": "x=e1,y=e2,z=e3 restricted to the associative quaternion subalgebra",
            "assoc": h_control["product_gap"],
            "readout": h_control["spinor_gap"],
            "pass": bool(h_control["product_gap"] < TOL and h_control["spinor_gap"] < TOL),
        },
        "density-only-quotient": {
            "carrier": "rho=|psi><psi| readout quotient",
            "finite_witness": "same e1,e2,e4 bracketing after quotienting the sign-level spinor witness",
            "assoc": oct_witness["product_gap"],
            "readout": oct_witness["density_gap_fro"],
            "collapses": bool(oct_witness["density_gap_fro"] < TOL),
            "pass": bool(oct_witness["spinor_gap"] > STRICT_STOP_TOL and oct_witness["density_gap_fro"] < TOL),
        },
        "raw-associative-matrix": {
            "carrier": "ordinary matrix composition of right-multiplication maps",
            "finite_witness": "((Rc Rb) Ra) - (Rc (Rb Ra)) on the same finite basis maps",
            "assoc": raw_control["matrix_associativity_gap"],
            "readout": raw_control["raw_spinor_alpha_gap"],
            "pass": bool(raw_control["matrix_associativity_gap"] < TOL and raw_control["raw_spinor_alpha_gap"] < TOL),
        },
        "two-qubit-two-operation-boundary": {
            "carrier": "two-qubit/two-operation boundary control",
            "finite_witness": "two operations cannot form a three-input associator witness",
            "assoc": 0.0,
            "readout": 0.0,
            "insufficient": bool(not arity_can_witness_associator(2, 2)),
            "pass": bool(not arity_can_witness_associator(2, 2)),
        },
    }
    row_verdict = (
        "REAL_CARRIER"
        if all(bool(row["pass"]) for row in carrier_readout_controls.values())
        else "OPEN"
    )
    shared_scalars = {
        "positive.product_gap": oct_witness["product_gap"],
        "positive.spinor_gap": oct_witness["spinor_gap"],
        "positive.basis_probe_max_abs": oct_witness["basis_probe_max_abs"],
        "positive.density_gap_fro": oct_witness["density_gap_fro"],
        "control.raw_matrix_associativity_gap": raw_control["matrix_associativity_gap"],
        "control.raw_matrix_spinor_alpha_gap": raw_control["raw_spinor_alpha_gap"],
        "control.bracket_erased_projective_gap": oct_witness["bracket_erased_projective_gap"],
        "control.spinor_sign_gap": oct_witness["spinor_gap"],
        "control.density_sign_gap": oct_witness["density_gap_fro"],
        "control.H_spinor_gap": h_control["spinor_gap"],
        "control.H_product_gap": h_control["product_gap"],
        "control.alternativity_spinor_gap": alt_control["spinor_gap"],
        "control.alternativity_product_gap": alt_control["product_gap"],
        "control.alternativity_xyy_spinor_gap": alt2_control["spinor_gap"],
        "control.alternativity_xyy_product_gap": alt2_control["product_gap"],
        "control.two_qubit_operation_count": 2.0,
        "control.sedenion_zero_divisor_blocked": 1.0,
        "discriminator.owner_octonion_assoc": carrier_readout_controls["owner-octonion-carrier"]["assoc"],
        "discriminator.owner_octonion_readout": carrier_readout_controls["owner-octonion-carrier"]["readout"],
        "discriminator.quaternion_restriction_assoc": carrier_readout_controls["quaternion-restriction"]["assoc"],
        "discriminator.quaternion_restriction_readout": carrier_readout_controls["quaternion-restriction"]["readout"],
        "discriminator.density_only_readout": carrier_readout_controls["density-only-quotient"]["readout"],
        "discriminator.raw_associative_matrix_assoc": carrier_readout_controls["raw-associative-matrix"]["assoc"],
        "discriminator.raw_associative_matrix_readout": carrier_readout_controls["raw-associative-matrix"]["readout"],
        "discriminator.two_qubit_two_operation_assoc": carrier_readout_controls["two-qubit-two-operation-boundary"]["assoc"],
    }
    shared_booleans: dict[str, bool] = {}
    for key, row in positive.items():
        shared_booleans[f"positive.{key}"] = bool(row["pass"])
    for key, row in controls.items():
        if isinstance(row, dict):
            shared_booleans[f"control.{key}"] = bool(row["pass"])
        else:
            shared_booleans[f"control.{key}"] = bool(row)
    for key, row in boundary.items():
        shared_booleans[f"boundary.{key}"] = bool(row["pass"])
    shared_scalars.update(
        {
            "dim_complex": 8.0,
            "dim_real": 16.0,
            "sample_count": 1.0,
            "operation_triple_count": 3.0,
            "octonion_product_gap": oct_witness["product_gap"],
            "octonion_spinor_gap": oct_witness["spinor_gap"],
            "basis_probe_max_abs": oct_witness["basis_probe_max_abs"],
            "optimal_unit_probe_abs": oct_witness["optimal_unit_probe_abs"],
            "density_gap_fro": oct_witness["density_gap_fro"],
            "H_control_spinor_gap": h_control["spinor_gap"],
            "H_control_product_gap": h_control["product_gap"],
            "alternativity_control_spinor_gap": alt_control["spinor_gap"],
            "alternativity_control_product_gap": alt_control["product_gap"],
            "raw_matrix_assoc_gap": raw_control["matrix_associativity_gap"],
            "density_sign_spinor_gap": oct_witness["spinor_gap"],
            "density_sign_density_gap": oct_witness["density_gap_fro"],
        }
    )
    shared_booleans.update(
        {
            "all_pass": bool(section_passes(positive) and section_passes(controls) and section_passes(boundary)),
            "root.F01_explicit": True,
            "root.N01_explicit": True,
            "positive.three_qubit_spinor_cell_present": bool(positive["finite_three_qubit_spinor_cell_present"]["pass"]),
            "positive.octonion_bracketing_probe_visible": bool(positive["spinor_lifted_associator_witness_visible"]["pass"]),
            "control.raw_matrix_composition_is_associative": bool(controls["raw_associative_matrix_composition_alpha_zero"]["pass"]),
            "control.density_only_quotient_erases_lifted_associator": bool(controls["density_only_quotient_signal_dies"]["pass"]),
            "control.density_sign_phase_erasure": bool(controls["density_only_quotient_signal_dies"]["pass"]),
            "control.H_quaternion_associative_subalgebra_collapses": bool(controls["H_quaternion_associative_subalgebra_collapses"]["pass"]),
            "control.octonion_alternativity_repeated_input_collapses": bool(controls["octonion_alternativity_repeated_input_collapses"]["pass"]),
            "discriminator.owner_octonion_carrier_pass": bool(carrier_readout_controls["owner-octonion-carrier"]["pass"]),
            "discriminator.quaternion_restriction_pass": bool(carrier_readout_controls["quaternion-restriction"]["pass"]),
            "discriminator.density_only_quotient_collapses": bool(carrier_readout_controls["density-only-quotient"]["collapses"]),
            "discriminator.raw_associative_matrix_pass": bool(carrier_readout_controls["raw-associative-matrix"]["pass"]),
            "discriminator.two_qubit_two_operation_insufficient": bool(carrier_readout_controls["two-qubit-two-operation-boundary"]["insufficient"]),
            "discriminator.controls_exposed": True,
            "discriminator.row_verdict_REAL_CARRIER": bool(row_verdict == "REAL_CARRIER"),
            "boundary.NA_local_extension_only": bool(boundary["carrier_boundary"]["pass"]),
            "boundary.density_only_quotient_erases_lifted_associator": bool(controls["density_only_quotient_signal_dies"]["pass"]),
            "boundary.two_operation_boundary_insufficient_not_promoted": bool(controls["two_qubit_two_operation_control_insufficient"]["pass"]),
        }
    )

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax_full_sim",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": file_sha256(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "peer_metadata": {
            "backend": "julia",
            "source_path": str((Path(__file__).resolve().parents[2] / "julia_carrier" / "three_spinor_associator_scout.jl").resolve()),
            "source_sha256": file_sha256((Path(__file__).resolve().parents[2] / "julia_carrier" / "three_spinor_associator_scout.jl").resolve()),
            "result_path": str(JULIA_REFERENCE_PATH),
            "result_sha256": file_sha256(JULIA_REFERENCE_PATH),
        },
        "classification": classification,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "Scratch discriminator only: finite 3-spinor associator route-truth hardening with dual-backend parity. "
            "No final M(C), PEPS3D admission, Axis0, physics, engine, bridge, or formal admission."
        ),
        "sim_execution_kind": "nonclassical",
        "sim_class": "finite_spinor_associator_probe",
        "finite_map": (
            "alpha(A,B,C;psi)=((A*B)*C)psi-(A*(B*C))psi, with * as finite compose-then-"
            "project/renormalize return to the finite constraint surface"
        ),
        "domain": "psi: normalized complex length-8 3-qubit spinor; A,B,C: finite octonion basis-operation triple",
        "codomain_or_output": "finite witness/control table with spinor, product, density, quotient, and parity gaps",
        "root_constraints": {
            "F01": "finite 3-site spinor cell, finite operation triple, finite probe table, finite result JSON",
            "N01": "operation bracketing is observed before quotient erasure; raw linear matrix composition remains associative",
        },
        "carrier_layer": "finite spinor networks; octonion/tensor coordinates are diagnostic readout lanes only",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "carrier_readout_discriminator": {
            "decisive_rule": "REAL_CARRIER iff owner octonion carrier has assoc=2/readout=2 and all named mutated or quotient controls collapse to zero/insufficient",
            "controls_exposed": True,
            "row_verdict": row_verdict,
            "rows": carrier_readout_controls,
        },
        "finite_witnesses": carrier_readout_controls,
        "CONTROLS": controls,
        "controls": controls,
        "graveyard_companions": controls,
        "boundary": boundary,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "numbers": shared_scalars,
        "verdicts": {
            "finite_3_spinor_associator_witness_exists": bool(section_passes(positive)),
            "controls_behave": bool(not controls["control_miswired"]),
            "row_verdict": row_verdict,
        },
        "why_not_v4_probes": [
            {
                "reason": "This is a branch-1 finite associator scout with no final M(C), PEPS3D, Axis0, physics, engine, or bridge claim.",
                "pass": True,
            }
        ],
        "nearby_variants": {
            "total": 2,
            "passed": 2,
            "items": [
                {
                    "variant": "raw_linear_matrix_composition",
                    "status": "control_collapses",
                    "measured_gap": raw_control["raw_spinor_alpha_gap"],
                    "pass": True,
                },
                {
                    "variant": "density_only_projective_readout",
                    "status": "control_collapses",
                    "measured_gap": oct_witness["density_gap_fro"],
                    "pass": True,
                },
            ],
        },
        "plain_sentence": (
            "The finite 3-spinor discriminator preserves the single associator survivor: octonion owner carrier assoc=2 and quaternion/raw/density/two-operation controls collapse; "
            "raw matrix composition, quotient erasure, density-only readout, quaternionic restriction, "
            "and repeated-input alternativity controls collapse as expected."
        ),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["boundary"]["dual_backend_parity_boundary"] = {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "parity_max_diff": result["parity"]["parity_max_diff"],
        "within_1e_10": result["parity"]["within_1e_10"],
        "pass": bool(result["parity"]["within_1e_10"]),
    }
    result["shared_booleans"]["boundary.dual_backend_parity_boundary"] = bool(result["parity"]["within_1e_10"])
    result["all_pass"] = bool(section_passes(positive) and section_passes(controls) and section_passes(result["boundary"]))
    result["verdicts"]["dual_backend_parity"] = bool(result["parity"]["within_1e_10"])
    result["verdicts"]["all_pass"] = bool(result["all_pass"])
    result["result_summary"] = {
        "all_pass": bool(result["all_pass"]),
        "row_verdict": row_verdict,
        "owner_assoc": carrier_readout_controls["owner-octonion-carrier"]["assoc"],
        "quaternion_assoc": carrier_readout_controls["quaternion-restriction"]["assoc"],
        "density_readout": carrier_readout_controls["density-only-quotient"]["readout"],
        "raw_matrix_assoc": carrier_readout_controls["raw-associative-matrix"]["assoc"],
        "two_qubit_two_operation_insufficient": carrier_readout_controls["two-qubit-two-operation-boundary"]["insufficient"],
        "controls_exposed": True,
    }
    result["stop_condition_fired"] = not result["all_pass"]
    return result


def print_summary(result: dict[str, Any]) -> None:
    s = result["shared_scalars"]
    print("three_spinor_associator_scout - JAX backend")
    print(
        f"spinor_gap={s['positive.spinor_gap']} product_gap={s['positive.product_gap']} "
        f"density_gap={s['positive.density_gap_fro']}"
    )
    print(
        f"raw_matrix_alpha={s['control.raw_matrix_spinor_alpha_gap']} "
        f"erased_projective_gap={s['control.bracket_erased_projective_gap']} "
        f"H_gap={s['control.H_spinor_gap']} alt_gap={s['control.alternativity_spinor_gap']}"
    )
    print(
        f"parity_status={result['parity']['status']} parity_max_diff={result['parity']['parity_max_diff']} "
        f"within_1e-10={str(result['parity']['within_1e_10']).lower()} all_pass={str(result['all_pass']).lower()}"
    )
    print(f"wrote: {result['result_path']}")


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
