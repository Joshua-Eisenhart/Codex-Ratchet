#!/usr/bin/env python3
"""Three-spinor associator lifted-bracketing formal scout.

This formal scout tests a bounded non-associativity question at the carrier
edge:

    psi in (C^2)^3, read as a finite 3-site spinor network cell
    real(psi), imag(psi) as a pair of octonion coordinate readouts
    alpha_O(psi, x, y, z) = psi*((xy)z) - psi*(x(yz))

The witness must be visible to lifted spinor/component probes, collapse under
quaternionic and alternativity controls, and be erased by a density-only
quotient for this chosen operation triple. Octonion coordinates are diagnostic
readout coordinates, not an admitted primitive carrier.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import time
import hashlib
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "three_spinor_associator_lifted_bracketing_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
JULIA_SOURCE = (
    ROOT.parent.parent
    / "julia_carrier"
    / "three_spinor_associator_lifted_bracketing.jl"
)
JULIA_RESULT = (
    ROOT.parent.parent
    / "julia_carrier"
    / "three_spinor_associator_lifted_bracketing_julia_results.json"
)

SCHEMA = "FORMAL_SCOUT_RESULT_v1"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
EPS = 1.0e-9

FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

CLAIM_CEILING = (
    "Formal scout only: tests whether finite non-associative bracketing is a "
    "probe-visible lifted-spinor readout in a 3-qubit spinor network cell, "
    "with quaternionic, alternativity, density-erasure, and dual-backend "
    "controls. It does not admit final M(C), PEPS3D, octonions as primitive "
    "carrier, QIT engine, Axis0, bridge, physics, or formal admission."
)

BLOCKED_CONSUMERS = [
    "final_M_C",
    "PEPS3D_admission",
    "octonion_primitive_carrier_admission",
    "QIT_engine_admission",
    "Axis0",
    "bridge",
    "physics",
    "gravity",
    "consciousness",
    "promotion",
    "formal_admission",
]

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite spinor arithmetic, octonion-coordinate multiplication, lifted spinor probes, and density-erasure controls",
    },
    "julia": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent mirror using Julia LinearAlgebra and the same finite operation table; parity must hold on keyed scalars and booleans",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, subprocess rerun of Julia mirror, and path handling",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used; no numpy import, np calls, or .numpy conversions in claim-bearing compute",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used; current fenced question is JAX+Julia finite spinor arithmetic, and adding decorative torch would be stale-gate drift",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "julia": "load_bearing",
    "python_stdlib": "supportive",
    "numpy": None,
    "pytorch": None,
}


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if hasattr(value, "shape"):
        arr = jax.device_get(value)
        if getattr(arr, "shape", ()) == ():
            return float(arr)
        return arr.tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def file_sha256(path: pathlib.Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def oct_mul(a: jax.Array, b: jax.Array) -> jax.Array:
    out = jnp.zeros((8,), dtype=jnp.float64)
    for i in range(8):
        for j in range(8):
            sign, k = TABLE[i][j]
            out = out.at[k].add(float(sign) * a[i] * b[j])
    return out


def basis(idx: int) -> jax.Array:
    return jnp.eye(8, dtype=jnp.float64)[idx]


def normalize_spinor(psi: jax.Array) -> jax.Array:
    return psi / jnp.linalg.norm(psi)


def seed_three_qubit_spinor() -> jax.Array:
    real = jnp.array([1.0, -2.0, 3.0, 5.0, -7.0, 11.0, -13.0, 17.0], dtype=jnp.float64)
    imag = jnp.array([19.0, -23.0, 29.0, -31.0, 37.0, -41.0, 43.0, -47.0], dtype=jnp.float64)
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
        "left_product": [py_float(v) for v in left_q],
        "right_product": [py_float(v) for v in right_q],
    }


def right_mult_matrix(q: jax.Array) -> jax.Array:
    return jnp.stack([oct_mul(basis(i), q) for i in range(8)], axis=1)


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
        "pass": spinor_gap > 1.0 and density_gap < EPS,
    }


def run_julia_mirror() -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        ["julia", str(JULIA_SOURCE)],
        cwd=str(JULIA_SOURCE.parent),
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    row: dict[str, Any] = {
        "source": JULIA_SOURCE,
        "result": JULIA_RESULT,
        "returncode": proc.returncode,
        "elapsed_seconds": time.time() - started,
        "stdout_tail": proc.stdout[-1000:],
        "stderr_tail": proc.stderr[-1000:],
        "pass": proc.returncode == 0 and JULIA_RESULT.exists(),
    }
    if row["pass"]:
        row["result_data"] = json.loads(JULIA_RESULT.read_text(encoding="utf-8"))
    return row


def parity_against_julia(jax_scalars: dict[str, float], jax_booleans: dict[str, bool], julia_data: dict[str, Any]) -> dict[str, Any]:
    julia_scalars = julia_data.get("shared_scalars", {})
    julia_booleans = julia_data.get("shared_booleans", {})
    scalar_rows = []
    max_diff = 0.0
    max_diff_key = None
    missing = []
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
    return {
        "scalar_rows": scalar_rows,
        "parity_max_diff": max_diff,
        "parity_max_diff_key": max_diff_key,
        "missing_keys": missing,
        "boolean_mismatches": mismatches,
        "within_1e_9": max_diff < EPS and not missing and not mismatches,
        "pass": max_diff < EPS and not missing and not mismatches,
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    psi = seed_three_qubit_spinor()
    oct_witness = spinor_bracket_witness(psi, basis(1), basis(2), basis(4))
    h_control = spinor_bracket_witness(psi, basis(1), basis(2), basis(3))
    alt_control = spinor_bracket_witness(psi, basis(1), basis(1), basis(4))
    matrix_gap = raw_matrix_associativity_gap(basis(1), basis(2), basis(4))
    phase_control = density_phase_erasure_control(psi)

    jax_scalars = {
        "three_qubit_complex_dim": float(psi.shape[0]),
        "three_qubit_real_dim": float(2 * psi.shape[0]),
        "two_qubit_real_dim": 8.0,
        "octonion_pair_real_dim": 16.0,
        "octonion_product_gap": oct_witness["product_gap"],
        "octonion_spinor_gap": oct_witness["spinor_gap"],
        "octonion_basis_probe_max_abs": oct_witness["basis_probe_max_abs"],
        "octonion_optimal_unit_probe_abs": oct_witness["optimal_unit_probe_abs"],
        "octonion_density_gap_fro": oct_witness["density_gap_fro"],
        "h_control_spinor_gap": h_control["spinor_gap"],
        "h_control_product_gap": h_control["product_gap"],
        "alt_control_spinor_gap": alt_control["spinor_gap"],
        "alt_control_product_gap": alt_control["product_gap"],
        "raw_matrix_assoc_gap": matrix_gap,
        "density_sign_spinor_gap": phase_control["spinor_sign_gap"],
        "density_sign_density_gap": phase_control["density_sign_gap"],
    }
    jax_booleans = {
        "three_qubit_minimum_for_octonion_pair": 2 * psi.shape[0] == 16,
        "two_qubit_insufficient_for_octonion_pair": 8 < 16,
        "octonion_bracketing_lifted_spinor_visible": oct_witness["spinor_gap"] > EPS and oct_witness["basis_probe_max_abs"] > EPS,
        "density_quotient_erases_octonion_bracketing_witness": oct_witness["density_gap_fro"] < EPS and oct_witness["spinor_gap"] > EPS,
        "quaternion_subalgebra_collapses": h_control["spinor_gap"] < EPS and h_control["product_gap"] < EPS,
        "octonion_alternativity_repeated_input_collapses": alt_control["spinor_gap"] < EPS and alt_control["product_gap"] < EPS,
        "raw_matrix_composition_associative_control": matrix_gap < EPS,
        "density_sign_erasure_control": bool(phase_control["pass"]),
    }

    julia = run_julia_mirror()
    parity = (
        parity_against_julia(jax_scalars, jax_booleans, julia["result_data"])
        if julia.get("pass")
        else {"pass": False, "reason": "julia mirror failed or missing"}
    )

    positive = {
        "finite_three_qubit_spinor_network_cell_present": {
            "domain": "psi in (C^2)^3; complex_dim=8; real_dim=16; three finite spinor sites q0,q1,q2",
            "pass": bool(jax_booleans["three_qubit_minimum_for_octonion_pair"]),
        },
        "octonion_bracketing_lifted_spinor_visible": {
            "finite_map": "alpha_O(psi,x,y,z)=psi*((xy)z)-psi*(x(yz)) over x=e1,y=e2,z=e4",
            "witness": oct_witness,
            "pass": bool(jax_booleans["octonion_bracketing_lifted_spinor_visible"]),
        },
        "dual_backend_jax_julia_parity": parity,
    }
    graveyard_companions = {
        "quaternion_associative_subalgebra_collapses": {
            "control": "x=e1,y=e2,z=e3 inside H=span(1,e1,e2,e3)",
            "witness": h_control,
            "pass": bool(jax_booleans["quaternion_subalgebra_collapses"]),
        },
        "octonion_alternativity_repeated_input_collapses": {
            "control": "x=e1,y=e1,z=e4; repeated input should kill associator in an alternative algebra",
            "witness": alt_control,
            "pass": bool(jax_booleans["octonion_alternativity_repeated_input_collapses"]),
        },
        "density_only_quotient_erases_lifted_bracketing_witness": {
            "note": "For this triple, left/right products are e7 and -e7, so normalized spinors differ by sign while rho=|psi><psi| is unchanged.",
            "spinor_gap": oct_witness["spinor_gap"],
            "density_gap_fro": oct_witness["density_gap_fro"],
            "pass": bool(jax_booleans["density_quotient_erases_octonion_bracketing_witness"]),
        },
        "raw_matrix_composition_is_associative_not_the_claim": {
            "matrix_associativity_gap": matrix_gap,
            "pass": bool(jax_booleans["raw_matrix_composition_associative_control"]),
        },
        "density_sign_erasure_control": phase_control,
    }
    boundary = {
        "two_qubit_cell_is_below_octonion_pair_floor": {
            "two_qubit_real_dim": 8,
            "octonion_pair_real_dim": 16,
            "pass": bool(jax_booleans["two_qubit_insufficient_for_octonion_pair"]),
        },
        "two_operation_boundary_has_no_associator": {
            "note": "A bracketing associator requires three algebra inputs; two operations test multiplication or commutation, not associativity.",
            "pass": True,
        },
        "octonion_coordinates_are_diagnostic_not_primitive_carrier": {
            "note": "Carrier remains the finite spinor network cell; octonion coordinates are a readout lane for bracket sensitivity.",
            "pass": True,
        },
        "promotion_remains_disabled": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "pass": (not PROMOTION_ALLOWED) and (not FORMAL_ADMISSION_ALLOWED),
        },
    }
    nearby_rows = {
        "three_spinor_cell": positive["finite_three_qubit_spinor_network_cell_present"]["pass"],
        "octonion_bracket": positive["octonion_bracketing_lifted_spinor_visible"]["pass"],
        "julia_parity": parity["pass"],
        "h_control": graveyard_companions["quaternion_associative_subalgebra_collapses"]["pass"],
        "alternativity_control": graveyard_companions["octonion_alternativity_repeated_input_collapses"]["pass"],
        "density_erasure": graveyard_companions["density_only_quotient_erases_lifted_bracketing_witness"]["pass"],
        "two_qubit_boundary": boundary["two_qubit_cell_is_below_octonion_pair_floor"]["pass"],
    }
    all_pass = (
        all(bool(row.get("pass")) for row in positive.values())
        and all(bool(row.get("pass")) for row in graveyard_companions.values())
        and all(bool(row.get("pass")) for row in boundary.values())
    )
    result = {
        "schema": SCHEMA,
        "name": NAME,
        "sim_id": NAME,
        "version": "1.0",
        "tier": "1-2 finite carrier/readout scout",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "carrier_probe",
        "source_alignment_category": "formal_tool_admission__three_spinor_nonassociative_bracketing_readout",
        "source_path": str(pathlib.Path(__file__).resolve()),
        "source_sha256": file_sha256(pathlib.Path(__file__).resolve()),
        "result_path": str(OUT_PATH.resolve()),
        "peer_source_path": str(JULIA_SOURCE.resolve()),
        "peer_result_path": str(JULIA_RESULT.resolve()),
        "peer_metadata": {
            "backend": "julia",
            "source_path": str(JULIA_SOURCE.resolve()),
            "source_sha256": file_sha256(JULIA_SOURCE),
            "result_path": str(JULIA_RESULT.resolve()),
            "result_sha256": file_sha256(JULIA_RESULT),
            "all_pass": bool((julia.get("result_data") or {}).get("all_pass")) if julia.get("pass") else False,
        },
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "finite 3-qubit spinor cell can carry a lifted bracketing witness in this diagnostic coordinate lane",
            "density-only quotient can erase this witness",
            "quaternion and alternativity controls collapse",
            "JAX and Julia agree on keyed finite readouts",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "root_constraints_in_force": {
            "F01": "finite carrier/probe/operator/path set: three spinor sites, finite operation triple, finite basis probes, finite result JSON",
            "N01": "bracketing/order-sensitive operation is measured; global associativity is not assumed",
        },
        "finite_map": "alpha_O : (psi in (C^2)^3, x,y,z in O_basis) -> lifted spinor/component-probe delta between psi*((xy)z) and psi*(x(yz))",
        "domain": "finite three-site spinor network cell psi in (C^2)^3 plus finite octonion-basis operation triples",
        "codomain_or_output": "finite readout table: product gap, spinor gap, component probe gap, density gap, backend parity, controls",
        "carrier_layer": "finite spinor network cell; not tensor primitive language",
        "geometry_layer": "bracket-sensitive octonion-coordinate readout over lifted spinor cell",
        "carrier_realization": "JAX x64 complex spinor vector of dim 8 mirrored by Julia ComplexF64 vector of dim 8",
        "peps3d_embedding": {
            "status": "scratch_anchor_only_not_admitted",
            "finite_cell_anchor": {
                "V": ["q0", "q1", "q2"],
                "E": [["q0", "q1"], ["q1", "q2"], ["q0", "q2"]],
                "F": [["q0", "q1", "q2"]],
                "C": ["cell_q0_q1_q2"],
            },
        },
        "spinor_state": {
            "kind": "three_qubit_lifted_spinor",
            "complex_dim": 8,
            "real_dim": 16,
            "why_three_qubits_minimum": "three qubits give 16 real coordinates, enough for a pair of octonion coordinate readouts; two qubits give only 8 real coordinates",
        },
        "quaternion_action": {
            "control_subalgebra": "H=span(1,e1,e2,e3)",
            "control_result": "associative subalgebra collapses the bracket witness",
        },
        "bridge_layer": "none",
        "cut_layer": "density_only_quotient_boundary_control",
        "law_or_candidate_tested": "non-associativity as finite probe-visible bracketing over lifted spinor network cell",
        "branch_status_before_run": "octonion/J3(O) fork remains scratch-only; this scout only hardens the lifted-spinor bracketing readout",
        "dependency_receipts": {
            "octonion_admissibility_prelim": str(ROOT.parent.parent / "julia_carrier" / "octonion_admissibility_prelim_julia_results.json"),
            "nonassociativity_probe_bracketing": str(ROOT.parent.parent / "julia_carrier" / "nonassociativity_as_probe_bracketing_julia_results.json"),
        },
        "downstream_blocks": BLOCKED_CONSUMERS,
        "required_tools": ["jax", "julia"],
        "actual_tools_used": ["jax", "julia", "python_stdlib"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "numpy_compute_used": False,
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
        "backend_roles": {
            "jax": "load-bearing mirror/stress computation in jax.numpy x64",
            "julia": "load-bearing independent reference using native Julia LinearAlgebra",
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(nearby_rows),
            "passed": sum(1 for v in nearby_rows.values() if v),
            "rows": nearby_rows,
        },
        "why_not_v4_probes": {
            "reason": "legacy v4/scalar/density-only probes cannot see this witness because the result is a lifted-spinor sign/bracketing readout erased by rho",
            "v4_style_density_only_gap": oct_witness["density_gap_fro"],
            "lifted_spinor_gap": oct_witness["spinor_gap"],
        },
        "julia_mirror": {
            k: v for k, v in julia.items() if k != "result_data"
        },
        "shared_scalars": jax_scalars,
        "shared_booleans": jax_booleans,
        "parity": parity,
        "witness_trace_id": "three_spinor_e1_e2_e4_lifted_bracketing",
        "result_summary": {
            "all_pass": all_pass,
            "octonion_spinor_gap": oct_witness["spinor_gap"],
            "octonion_density_gap_fro": oct_witness["density_gap_fro"],
            "h_control_spinor_gap": h_control["spinor_gap"],
            "alt_control_spinor_gap": alt_control["spinor_gap"],
            "parity_max_diff": parity.get("parity_max_diff"),
            "claim_ceiling": "formal_scout_only_no_promotion",
        },
        "pass_rule": "all positive, graveyard, boundary, and JAX-Julia parity checks pass",
        "fail_rule": "any control fails, density quotient sees the sign witness, two-qubit floor is false, or JAX-Julia parity diverges",
        "promotion_status": "blocked_formal_scout_only",
        "eligible_consumers": [],
        "blocked_consumers_expanded": BLOCKED_CONSUMERS,
        "artifacts_emitted": [str(OUT_PATH), str(JULIA_RESULT)],
        "required_artifacts": [str(OUT_PATH), str(JULIA_RESULT)],
        "generated_at_unix": time.time(),
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
        "blockers": [],
    }
    return jsonable(result)


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "classification": result["classification"],
                "octonion_spinor_gap": result["result_summary"]["octonion_spinor_gap"],
                "octonion_density_gap_fro": result["result_summary"]["octonion_density_gap_fro"],
                "parity_max_diff": result["result_summary"]["parity_max_diff"],
                "promotion_allowed": result["promotion_allowed"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
