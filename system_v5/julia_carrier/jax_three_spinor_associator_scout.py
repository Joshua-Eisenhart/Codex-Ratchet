#!/usr/bin/env python3
# object_id: three_spinor_associator_scout
# classification: formal_scout
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import json
import sys
import time
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "three_spinor_associator_scout"
BASE_DIR = Path(__file__).resolve().parent
RESULT_PATH = BASE_DIR / "three_spinor_associator_scout_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "three_spinor_associator_scout_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def py_list(value: Any) -> list[float]:
    return [float(v) for v in jax.device_get(value)]


def octonion_table() -> list[list[tuple[float, int]]]:
    table = [[(0.0, 0) for _ in range(8)] for _ in range(8)]
    table[0][0] = (1.0, 0)
    for i in range(1, 8):
        table[0][i] = (1.0, i)
        table[i][0] = (1.0, i)
        table[i][i] = (-1.0, 0)
    for a, b, c in FANO:
        for i, j, k in [(a, b, c), (b, c, a), (c, a, b)]:
            table[i][j] = (1.0, k)
        for i, j, k in [(b, a, c), (c, b, a), (a, c, b)]:
            table[i][j] = (-1.0, k)
    return table


TABLE = octonion_table()


def basis(idx: int) -> jax.Array:
    return jnp.eye(8, dtype=jnp.float64)[idx]


def oct_mul(a: jax.Array, b: jax.Array) -> jax.Array:
    out = jnp.zeros((8,), dtype=jnp.float64)
    for i in range(8):
        for j in range(8):
            sign, k = TABLE[i][j]
            out = out.at[k].add(sign * a[i] * b[j])
    return out


def normalize_spinor(psi: jax.Array) -> jax.Array:
    return psi / jnp.linalg.norm(psi)


def seed_three_qubit_spinor() -> jax.Array:
    real = jnp.asarray([1.0, -2.0, 3.0, 5.0, -7.0, 11.0, -13.0, 17.0], dtype=jnp.float64)
    imag = jnp.asarray([19.0, -23.0, 29.0, -31.0, 37.0, -41.0, 43.0, -47.0], dtype=jnp.float64)
    return normalize_spinor(real + 1j * imag)


def spinor_to_oct_pair(psi: jax.Array) -> tuple[jax.Array, jax.Array]:
    return jnp.real(psi), jnp.imag(psi)


def oct_pair_to_spinor(pair: tuple[jax.Array, jax.Array]) -> jax.Array:
    a, b = pair
    return normalize_spinor(a + 1j * b)


def right_action_pair(pair: tuple[jax.Array, jax.Array], q: jax.Array) -> tuple[jax.Array, jax.Array]:
    a, b = pair
    return oct_mul(a, q), oct_mul(b, q)


def bracket_products(x: jax.Array, y: jax.Array, z: jax.Array) -> tuple[jax.Array, jax.Array]:
    return oct_mul(oct_mul(x, y), z), oct_mul(x, oct_mul(y, z))


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conjugate(psi))


def spinor_bracket_witness(psi: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> dict[str, Any]:
    pair = spinor_to_oct_pair(psi)
    left_q, right_q = bracket_products(x, y, z)
    left = oct_pair_to_spinor(right_action_pair(pair, left_q))
    right = oct_pair_to_spinor(right_action_pair(pair, right_q))
    delta = left - right
    return {
        "product_gap": py_float(jnp.linalg.norm(left_q - right_q)),
        "spinor_gap": py_float(jnp.linalg.norm(delta)),
        "basis_probe_max_abs": py_float(jnp.max(jnp.abs(delta))),
        "optimal_unit_probe_abs": py_float(jnp.linalg.norm(delta)),
        "density_gap_fro": py_float(jnp.linalg.norm(density(left) - density(right))),
        "left_product": py_list(left_q),
        "right_product": py_list(right_q),
    }


def right_mult_matrix(q: jax.Array) -> jax.Array:
    cols = [oct_mul(basis(i), q) for i in range(8)]
    return jnp.stack(cols, axis=1)


def raw_matrix_associativity_gap(x: jax.Array, y: jax.Array, z: jax.Array) -> float:
    rx = right_mult_matrix(x)
    ry = right_mult_matrix(y)
    rz = right_mult_matrix(z)
    return py_float(jnp.linalg.norm((rz @ ry) @ rx - rz @ (ry @ rx)))


def density_phase_erasure_control(psi: jax.Array) -> dict[str, Any]:
    minus = -psi
    spinor_gap = py_float(jnp.linalg.norm(psi - minus))
    density_gap = py_float(jnp.linalg.norm(density(psi) - density(minus)))
    return {
        "spinor_sign_gap": spinor_gap,
        "density_sign_gap": density_gap,
        "pass": bool(spinor_gap > 1.0 and density_gap < TOL),
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
            "strict_divergence_gt_1e_6": [],
            "boolean_mismatches": [],
            "missing_keys": [{"missing_peer_result": str(peer_path)}],
            "stop_condition_fired": True,
        }

    peer = json.loads(peer_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    max_diff_key = None
    strict: list[dict[str, Any]] = []
    missing: list[Any] = []

    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append({"missing_scalar": key})
            continue
        jax_value = float(value)
        julia_value = float(peer["shared_scalars"][key])
        diff = abs(jax_value - julia_value)
        row = {"key": key, "jax": jax_value, "julia": julia_value, "abs_diff": diff}
        rows.append(row)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        if diff > STRICT_STOP_TOL:
            strict.append(row)

    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append({"missing_boolean": key})
            continue
        jax_value = bool(value)
        julia_value = bool(peer["shared_booleans"][key])
        if jax_value != julia_value:
            mismatches.append({"key": key, "jax": jax_value, "julia": julia_value})

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
    started = time.time()
    psi = seed_three_qubit_spinor()

    oct_x, oct_y, oct_z = basis(1), basis(2), basis(4)
    h_x, h_y, h_z = basis(1), basis(2), basis(3)
    alt_x, alt_y, alt_z = basis(1), basis(1), basis(4)

    oct_witness = spinor_bracket_witness(psi, oct_x, oct_y, oct_z)
    h_control = spinor_bracket_witness(psi, h_x, h_y, h_z)
    alt_control = spinor_bracket_witness(psi, alt_x, alt_y, alt_z)
    matrix_gap = raw_matrix_associativity_gap(oct_x, oct_y, oct_z)
    phase_control = density_phase_erasure_control(psi)

    positive = {
        "three_qubit_spinor_cell_present": {
            "domain": "psi in (C^2)^tensor3, dim_complex=8, finite 3-qubit spinor cell",
            "pass": bool(psi.shape == (8,)),
        },
        "octonion_bracketing_probe_visible": {
            "witness": oct_witness,
            "pass": bool(oct_witness["spinor_gap"] > TOL and oct_witness["basis_probe_max_abs"] > TOL),
        },
    }
    controls = {
        "H_quaternion_associative_subalgebra_collapses": {
            "triple": ["e1", "e2", "e3"],
            "witness": h_control,
            "pass": bool(h_control["spinor_gap"] < TOL and h_control["product_gap"] < TOL),
        },
        "octonion_alternativity_repeated_input_collapses": {
            "triple": ["e1", "e1", "e4"],
            "witness": alt_control,
            "pass": bool(alt_control["spinor_gap"] < TOL and alt_control["product_gap"] < TOL),
        },
        "raw_matrix_composition_is_associative_control": {
            "matrix_associativity_gap": matrix_gap,
            "pass": bool(matrix_gap < TOL),
        },
        "density_only_quotient_erases_lifted_associator_signal": {
            "density_gap_fro": oct_witness["density_gap_fro"],
            "spinor_gap": oct_witness["spinor_gap"],
            "pass": bool(oct_witness["density_gap_fro"] < TOL and oct_witness["spinor_gap"] > TOL),
            "note": "The density-only readout erases the sign-level lifted associator witness.",
        },
        "density_sign_phase_erasure_control": phase_control,
    }
    boundary = {
        "density_only_quotient_erases_this_lifted_associator": {
            "density_gap_fro": oct_witness["density_gap_fro"],
            "spinor_gap": oct_witness["spinor_gap"],
            "pass": bool(oct_witness["density_gap_fro"] < TOL and oct_witness["spinor_gap"] > TOL),
            "note": "For this triple, the two normalized bracketed spinors differ by sign, so rho=|psi><psi| erases the lifted witness.",
        },
        "two_operation_boundary_insufficient_not_promoted": {
            "pass": True,
            "note": "Associator evidence requires three algebra inputs; two-operation checks are insufficient and are not promoted.",
        },
        "NA_local_bracket_sensitive_probe_extension_only": {
            "pass": True,
            "note": "NA is recorded only as a local bracket-sensitive probe extension on this finite carrier, not as a new global foundation.",
        },
        "promotion_and_formal_admission_disabled": {
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "pass": True,
        },
    }

    check_rows = [row["pass"] for row in positive.values()]
    check_rows += [row["pass"] for row in controls.values()]
    check_rows += [row["pass"] for row in boundary.values()]
    all_pass = bool(all(check_rows))

    shared_scalars = {
        "dim_complex": 8,
        "dim_real": 16,
        "sample_count": 1,
        "operation_triple_count": 3,
        "octonion_product_gap": oct_witness["product_gap"],
        "octonion_spinor_gap": oct_witness["spinor_gap"],
        "basis_probe_max_abs": oct_witness["basis_probe_max_abs"],
        "optimal_unit_probe_abs": oct_witness["optimal_unit_probe_abs"],
        "density_gap_fro": oct_witness["density_gap_fro"],
        "H_control_spinor_gap": h_control["spinor_gap"],
        "H_control_product_gap": h_control["product_gap"],
        "alternativity_control_spinor_gap": alt_control["spinor_gap"],
        "alternativity_control_product_gap": alt_control["product_gap"],
        "raw_matrix_assoc_gap": matrix_gap,
        "density_sign_spinor_gap": phase_control["spinor_sign_gap"],
        "density_sign_density_gap": phase_control["density_sign_gap"],
    }
    shared_booleans = {
        "all_pass": all_pass,
        "positive.three_qubit_spinor_cell_present": positive["three_qubit_spinor_cell_present"]["pass"],
        "positive.octonion_bracketing_probe_visible": positive["octonion_bracketing_probe_visible"]["pass"],
        "control.H_quaternion_associative_subalgebra_collapses": controls[
            "H_quaternion_associative_subalgebra_collapses"
        ]["pass"],
        "control.octonion_alternativity_repeated_input_collapses": controls[
            "octonion_alternativity_repeated_input_collapses"
        ]["pass"],
        "control.raw_matrix_composition_is_associative": controls[
            "raw_matrix_composition_is_associative_control"
        ]["pass"],
        "control.density_only_quotient_erases_lifted_associator": controls[
            "density_only_quotient_erases_lifted_associator_signal"
        ]["pass"],
        "control.density_sign_phase_erasure": controls["density_sign_phase_erasure_control"]["pass"],
        "boundary.density_only_quotient_erases_lifted_associator": boundary[
            "density_only_quotient_erases_this_lifted_associator"
        ]["pass"],
        "boundary.two_operation_boundary_insufficient_not_promoted": boundary[
            "two_operation_boundary_insufficient_not_promoted"
        ]["pass"],
        "boundary.NA_local_extension_only": boundary["NA_local_bracket_sensitive_probe_extension_only"]["pass"],
        "boundary.promotion_and_formal_admission_disabled": boundary[
            "promotion_and_formal_admission_disabled"
        ]["pass"],
        "root.F01_explicit": True,
        "root.N01_explicit": True,
    }

    tool_manifest = {
        "jax": {"used": True, "reason": "load-bearing x64 finite spinor and octonion-coordinate arithmetic"},
        "jax.numpy": {"used": True, "reason": "load-bearing vector norms, density matrices, and matrix associativity control"},
        "json": {"used": True, "reason": "supportive result and parity serialization"},
        "numpy": {"used": False, "reason": "not imported; no NumPy computation is used"},
    }
    tool_depth = {
        "jax": "load_bearing",
        "jax.numpy": "load_bearing",
        "json": "supportive",
        "numpy": "None",
    }

    result: dict[str, Any] = {
        "schema": "three_spinor_associator_scout_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "classification": "formal_scout",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "promotion_status": "diagnostic_only",
        "claim_ceiling": (
            "Bounded formal_scout only: finite 3-qubit spinor cell bracket-sensitive associator probe with controls. "
            "No final M(C), no M(C+NA) admission, no PEPS3D admission, no Axis0, no physics/gravity, "
            "no QIT-engine, no bridge, and no global octonionic manifold claim."
        ),
        "root_constraints": {
            "F01": "finite carrier/probe/operator/result: one normalized psi in (C^2)^tensor3, finite octonion basis triples, finite witnesses, finite JSON",
            "N01": "noncommutation plus bracket-sensitivity are measured objects; the witness compares ((xy)z) against (x(yz)) on the same finite spinor cell",
            "NA": "local bracket-sensitive probe extension only; not an admitted global foundation",
        },
        "finite_map": "alpha_O(psi,x,y,z) = psi*((xy)z) - psi*(x(yz)) after octonion-coordinate right action and normalization",
        "domain": "finite 3-qubit spinor cell psi in (C^2)^tensor3, dim_complex=8",
        "codomain_or_output": "finite witness/control table: product gap, spinor gap, basis probe gap, density readout gap, parity rows",
        "carrier_layer": "finite spinor network scout cell; octonion coordinates are diagnostic readout/action coordinates, not an admitted primitive carrier",
        "operation_registry": {
            "octonion_nonassociative_witness": {"algebra": "O", "triple": ["e1", "e2", "e4"]},
            "H_quaternion_associative_control": {"algebra": "H subset O", "triple": ["e1", "e2", "e3"]},
            "octonion_alternativity_control": {"algebra": "O", "triple": ["e1", "e1", "e4"]},
        },
        "peps3d_embedding": {"status": "not_admitted", "note": "No PEPS3D admission or downstream carrier promotion is made."},
        "blocked_consumers": [
            "final_M(C)",
            "M(C+NA)",
            "PEPS3D",
            "Axis0",
            "physics_gravity",
            "QIT_engine",
            "bridge",
            "global_octonionic_manifold",
        ],
        "positive": positive,
        "graveyard_companions": controls,
        "boundary": boundary,
        "numbers": shared_scalars,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "witnesses": {
            "octonion": oct_witness,
            "H_quaternion_control": h_control,
            "alternativity_control": alt_control,
            "density_phase_erasure_control": phase_control,
        },
        "TOOL_MANIFEST": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": tool_depth,
        "tool_manifest": tool_manifest,
        "tool_integration_depth": tool_depth,
        "divergence_log": ["Not a classical baseline; bounded formal_scout with positive/control/boundary rows only."],
        "jax_x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = bool(not all_pass or result["parity"]["stop_condition_fired"])
    return result


def print_summary(result: dict[str, Any]) -> None:
    n = result["shared_scalars"]
    parity = result["parity"]
    print("three_spinor_associator_scout - JAX formal scout")
    print(
        "all_pass={all_pass} octonion_product_gap={product} octonion_spinor_gap={spinor} "
        "basis_probe_max_abs={basis} density_gap_fro={density}".format(
            all_pass=str(result["all_pass"]).lower(),
            product=n["octonion_product_gap"],
            spinor=n["octonion_spinor_gap"],
            basis=n["basis_probe_max_abs"],
            density=n["density_gap_fro"],
        )
    )
    print(
        "H_control_spinor_gap={h_gap} alternativity_control_spinor_gap={alt_gap} "
        "raw_matrix_assoc_gap={matrix_gap}".format(
            h_gap=n["H_control_spinor_gap"],
            alt_gap=n["alternativity_control_spinor_gap"],
            matrix_gap=n["raw_matrix_assoc_gap"],
        )
    )
    print(
        "parity_status={status} parity_max_diff={max_diff} within_1e-9={within} stop_condition_fired={stop}".format(
            status=parity["status"],
            max_diff=parity["parity_max_diff"],
            within=str(parity["within_1e_9"]).lower(),
            stop=str(result["stop_condition_fired"]).lower(),
        )
    )
    if result["stop_condition_fired"]:
        print("STOP: local check or backend parity condition is not fully accepted.")
        print(
            json.dumps(
                {
                    "strict_divergence_gt_1e_6": parity["strict_divergence_gt_1e_6"],
                    "boolean_mismatches": parity["boolean_mismatches"],
                    "missing_keys": parity["missing_keys"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    print(result["claim_ceiling"])
    print(f"wrote: {result['result_path']}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
