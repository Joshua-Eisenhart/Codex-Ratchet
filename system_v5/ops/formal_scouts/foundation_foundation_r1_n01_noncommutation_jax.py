#!/usr/bin/env python3
from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SRC_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r1_n01_noncommutation_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r1_n01_noncommutation_jax_result.json"
RUNG_ID = "foundation_r1_n01_noncommutation"
TOL = 1.0e-12

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite operator/probe-state construction for the N01 order-gap and quotient signatures",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 Pauli operator arithmetic and expectation signatures",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT proof over JAX-computed Z/X entries: zero commutator is UNSAT; erased probe constraint flips SAT",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT proof matching z3 over the same computed integer operator entries",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive timestamp, paths, and JSON receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "Python stdlib": "supportive",
}


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "shape"):
        return jsonable(jax.device_get(value).tolist())
    if isinstance(value, (jnp.bool_,)):
        return bool(value)
    return value


def pauli_operators() -> tuple[jax.Array, jax.Array, jax.Array]:
    z_probe = jnp.array([[1, 0], [0, -1]], dtype=jnp.int64)
    x_probe = jnp.array([[0, 1], [1, 0]], dtype=jnp.int64)
    # Informative commuting partner in the Z eigenbasis: D = diag(2, 3).
    # D commutes with Z (both diagonal) but is not the identity and not a
    # scalar multiple of it, so <D> carries state-dependent information.
    # This isolates non-commutation instead of information loss.
    d_probe = jnp.array([[2, 0], [0, 3]], dtype=jnp.int64)
    return z_probe, x_probe, d_probe


def fixture_states() -> list[tuple[str, jax.Array]]:
    inv = 1.0 / jnp.sqrt(jnp.asarray(2.0, dtype=jnp.float64))
    return [
        ("ket_0", jnp.array([1.0 + 0.0j, 0.0 + 0.0j], dtype=jnp.complex128)),
        ("ket_1", jnp.array([0.0 + 0.0j, 1.0 + 0.0j], dtype=jnp.complex128)),
        ("ket_plus", jnp.array([inv + 0.0j, inv + 0.0j], dtype=jnp.complex128)),
        ("ket_minus", jnp.array([inv + 0.0j, -inv + 0.0j], dtype=jnp.complex128)),
        ("ket_y_plus", jnp.array([inv + 0.0j, 1.0j * inv], dtype=jnp.complex128)),
        ("ket_y_minus", jnp.array([inv + 0.0j, -1.0j * inv], dtype=jnp.complex128)),
    ]


def expectation_signature(probes: list[jax.Array], ket: jax.Array) -> list[float]:
    signature: list[float] = []
    for probe in probes:
        probe_c = probe.astype(jnp.complex128)
        value = jnp.vdot(ket, probe_c @ ket)
        signature.append(round(float(jax.device_get(jnp.real(value))), 12))
    return signature


def quotient_classes(probes: list[jax.Array], states: list[tuple[str, jax.Array]]) -> list[dict[str, Any]]:
    classes: dict[tuple[float, ...], list[str]] = {}
    for name, ket in states:
        key = tuple(expectation_signature(probes, ket))
        classes.setdefault(key, []).append(name)
    return [
        {"signature": list(key), "members": classes[key]}
        for key in sorted(classes)
    ]


def int_matrix(matrix: jax.Array) -> list[list[int]]:
    return [[int(x) for x in row] for row in jax.device_get(matrix).tolist()]


def z3_matrix(name: str) -> list[list[z3.ArithRef]]:
    return [[z3.Int(f"{name}_{i}_{j}") for j in range(2)] for i in range(2)]


def z3_bind_matrix(solver: z3.Solver, matrix: list[list[z3.ArithRef]], values: list[list[int]]) -> None:
    for i in range(2):
        for j in range(2):
            solver.add(matrix[i][j] == values[i][j])


def z3_commutator_entries(a: list[list[z3.ArithRef]], b: list[list[z3.ArithRef]]) -> list[z3.ArithRef]:
    entries = []
    for i in range(2):
        for j in range(2):
            ab = sum(a[i][k] * b[k][j] for k in range(2))
            ba = sum(b[i][k] * a[k][j] for k in range(2))
            entries.append(ab - ba)
    return entries


def z3_order_gap_proof(z_values: list[list[int]], x_values: list[list[int]], d_values: list[list[int]]) -> dict[str, Any]:
    a = z3_matrix("A")
    b = z3_matrix("B")
    entries = z3_commutator_entries(a, b)

    main = z3.Solver()
    z3_bind_matrix(main, a, z_values)
    z3_bind_matrix(main, b, x_values)
    main.add([entry == 0 for entry in entries])
    main_status = main.check()

    erased = z3.Solver()
    z3_bind_matrix(erased, a, z_values)
    erased.add([entry == 0 for entry in entries])
    erased_status = erased.check()

    control = z3.Solver()
    z3_bind_matrix(control, a, z_values)
    z3_bind_matrix(control, b, d_values)
    control.add([entry == 0 for entry in entries])
    control_status = control.check()

    return {
        "solver": "z3",
        "version": z3.get_version_string(),
        "claim": "For the JAX-computed Z and X integer matrices, the asserted zero commutator equations are unsatisfiable",
        "main_status": str(main_status),
        "main_unsat": main_status == z3.unsat,
        "erase_x_probe_constraint_status": str(erased_status),
        "erase_flip_sat": erased_status == z3.sat,
        "commuting_control_status": str(control_status),
        "commuting_control_sat": control_status == z3.sat,
        "pass": main_status == z3.unsat and erased_status == z3.sat and control_status == z3.sat,
    }


def cvc5_int(solver: cvc5.Solver, n: int) -> cvc5.Term:
    return solver.mkInteger(n)


def cvc5_add(solver: cvc5.Solver, terms: list[cvc5.Term]) -> cvc5.Term:
    if not terms:
        return cvc5_int(solver, 0)
    total = terms[0]
    for term in terms[1:]:
        total = solver.mkTerm(Kind.ADD, total, term)
    return total


def cvc5_matrix(solver: cvc5.Solver, name: str) -> list[list[cvc5.Term]]:
    int_sort = solver.getIntegerSort()
    return [[solver.mkConst(int_sort, f"{name}_{i}_{j}") for j in range(2)] for i in range(2)]


def cvc5_bind_matrix(solver: cvc5.Solver, matrix: list[list[cvc5.Term]], values: list[list[int]]) -> None:
    for i in range(2):
        for j in range(2):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, matrix[i][j], cvc5_int(solver, values[i][j])))


def cvc5_commutator_entries(
    solver: cvc5.Solver,
    a: list[list[cvc5.Term]],
    b: list[list[cvc5.Term]],
) -> list[cvc5.Term]:
    entries = []
    for i in range(2):
        for j in range(2):
            ab_terms = [solver.mkTerm(Kind.MULT, a[i][k], b[k][j]) for k in range(2)]
            ba_terms = [solver.mkTerm(Kind.MULT, b[i][k], a[k][j]) for k in range(2)]
            entries.append(solver.mkTerm(Kind.SUB, cvc5_add(solver, ab_terms), cvc5_add(solver, ba_terms)))
    return entries


def cvc5_zero_comm_status(
    z_values: list[list[int]],
    b_values: list[list[int]] | None,
) -> str:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    a = cvc5_matrix(solver, "A")
    b = cvc5_matrix(solver, "B")
    cvc5_bind_matrix(solver, a, z_values)
    if b_values is not None:
        cvc5_bind_matrix(solver, b, b_values)
    for entry in cvc5_commutator_entries(solver, a, b):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, entry, cvc5_int(solver, 0)))
    return str(solver.checkSat())


def cvc5_order_gap_proof(z_values: list[list[int]], x_values: list[list[int]], d_values: list[list[int]]) -> dict[str, Any]:
    main_status = cvc5_zero_comm_status(z_values, x_values)
    erased_status = cvc5_zero_comm_status(z_values, None)
    control_status = cvc5_zero_comm_status(z_values, d_values)
    return {
        "solver": "cvc5",
        "version": cvc5.__version__,
        "claim": "For the JAX-computed Z and X integer matrices, the asserted zero commutator equations are unsatisfiable",
        "main_status": main_status,
        "main_unsat": main_status == "unsat",
        "erase_x_probe_constraint_status": erased_status,
        "erase_flip_sat": erased_status == "sat",
        "commuting_control_status": control_status,
        "commuting_control_sat": control_status == "sat",
        "pass": main_status == "unsat" and erased_status == "sat" and control_status == "sat",
    }


def build_result() -> dict[str, Any]:
    z_probe, x_probe, d_probe = pauli_operators()
    states = fixture_states()
    noncommutator = z_probe @ x_probe - x_probe @ z_probe
    commuting_commutator = z_probe @ d_probe - d_probe @ z_probe
    ket_0 = states[0][1]
    order_gap_noncommuting = float(jax.device_get(jnp.linalg.norm(noncommutator.astype(jnp.complex128) @ ket_0)))
    order_gap_commuting = float(jax.device_get(jnp.linalg.norm(commuting_commutator.astype(jnp.complex128) @ ket_0)))
    noncommuting_classes = quotient_classes([z_probe, x_probe], states)
    commuting_classes = quotient_classes([z_probe, d_probe], states)

    z_values = int_matrix(z_probe)
    x_values = int_matrix(x_probe)
    d_values = int_matrix(d_probe)
    z3_proof = z3_order_gap_proof(z_values, x_values, d_values)
    cvc5_proof = cvc5_order_gap_proof(z_values, x_values, d_values)

    class_count_noncommuting = len(noncommuting_classes)
    class_count_commuting = len(commuting_classes)
    all_pass = bool(
        order_gap_noncommuting > TOL
        and order_gap_commuting <= TOL
        and class_count_commuting < class_count_noncommuting
        and z3_proof["pass"]
        and cvc5_proof["pass"]
        and z3_proof["main_status"] == cvc5_proof["main_status"]
    )
    return {
        "schema": "codex_ratchet.foundation_rung_leg.v1",
        "object_id": "foundation_foundation_r1_n01_noncommutation_jax",
        "rung_id": RUNG_ID,
        "engine": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SRC_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "jax_enable_x64": jax.config.read("jax_enable_x64"),
        "python_executable": str(Path(__import__("sys").executable)),
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "Python stdlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "M": {
            "noncommuting_probe_family": ["Pauli_Z", "Pauli_X"],
            "commuting_control_family": ["Pauli_Z", "Diag_2_3"],
            "fixture_states": [name for name, _ in states],
        },
        "C": {
            "admissibility": ["Hermitian density operator", "trace=1", "PSD", "normalized ket fixtures"],
            "rung_specific_constraint": "[Z, X] != 0 encoded as UNSAT of zero-commutator equations over computed entries",
            "erase_control": "Drop the X probe constraint while keeping zero-commutator equations",
            "commuting_control_constraint": "[Z, D] = 0 for the informative commuting observable D = diag(2, 3); the control is not information-free (D is not I and not a scalar multiple of I)",
        },
        "quotient_summary": {
            "definition": "rho ~_M sigma iff Tr(rho O)=Tr(sigma O) for every O in M",
            "noncommuting_coordinates": ["<Z>", "<X>"],
            "commuting_control_coordinates": ["<Z>", "<D>"],
            "fixture_class_count_noncommuting": class_count_noncommuting,
            "fixture_class_count_commuting": class_count_commuting,
            "noncommuting_classes": noncommuting_classes,
            "commuting_control_classes": commuting_classes,
            "strictly_finer_than_commuting_control": class_count_noncommuting > class_count_commuting,
        },
        "computed_operators": {
            "Z": z_values,
            "X": x_values,
            "D": d_values,
            "commutator_ZX_minus_XZ": int_matrix(noncommutator),
            "commutator_ZD_minus_DZ": int_matrix(commuting_commutator),
        },
        "smt": {
            "z3": z3_proof,
            "cvc5": cvc5_proof,
            "solvers_agree": z3_proof["main_status"] == cvc5_proof["main_status"],
        },
        "values": {
            "commutator_frobenius_norm": float(jax.device_get(jnp.linalg.norm(noncommutator.astype(jnp.float64)))),
            "commuting_control_commutator_frobenius_norm": float(jax.device_get(jnp.linalg.norm(commuting_commutator.astype(jnp.float64)))),
            "order_gap_noncommuting": order_gap_noncommuting,
            "order_gap_commuting": order_gap_commuting,
            "class_count_noncommuting": class_count_noncommuting,
            "class_count_commuting": class_count_commuting,
        },
        "negative_control_flip": {
            "noncommuting_order_gap_positive": order_gap_noncommuting > TOL,
            "commuting_order_gap_zero": order_gap_commuting <= TOL,
            "commuting_control_coarser_quotient": class_count_commuting < class_count_noncommuting,
            "erase_x_probe_constraint_z3": z3_proof["erase_x_probe_constraint_status"],
            "erase_x_probe_constraint_cvc5": cvc5_proof["erase_x_probe_constraint_status"],
            "flipped": order_gap_noncommuting > TOL and order_gap_commuting <= TOL and class_count_commuting < class_count_noncommuting,
        },
        "all_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = jsonable(build_result())
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    vals = result["values"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "JAX_N01_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"order_gap_noncommuting={vals['order_gap_noncommuting']} "
        f"order_gap_commuting={vals['order_gap_commuting']} "
        f"z3={result['smt']['z3']['main_status']} "
        f"cvc5={result['smt']['cvc5']['main_status']} "
        f"erase_z3={result['smt']['z3']['erase_x_probe_constraint_status']} "
        f"erase_cvc5={result['smt']['cvc5']['erase_x_probe_constraint_status']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
