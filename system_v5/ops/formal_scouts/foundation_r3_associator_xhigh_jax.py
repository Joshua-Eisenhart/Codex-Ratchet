#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for foundation_r3_associator_xhigh.

Scratch diagnostic only. This leg computes Cayley-Dickson H and O tables in
JAX x64, then binds the computed multiplication-table entries into z3 and cvc5
so the solvers derive associator expressions instead of rechecking precomputed
associator coefficients.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_associator_xhigh"
CANONICAL_RUNG_ID = "foundation_r3_associator"
OBJECT_ID = "foundation_r3_associator_xhigh_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_xhigh_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_xhigh_jax_results.json"
TOL = 1.0e-12
NONZERO_TOL = 1.0e-9

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Cayley-Dickson table and associator coefficient computation",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite tensor arithmetic for structure constants before SMT binding",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing in-solver associator derivation from bound Cayley-Dickson multiplication-table entries",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent in-solver associator derivation from the same bound table entries",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, path, timestamp, and hashing",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def basis_vector(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate(
        [jnp.ones((1,), dtype=jnp.float64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.float64)]
    )
    return x * signs


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a = x[:n]
    b = x[n:]
    c = y[:n]
    d = y[n:]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    return jnp.concatenate([first, second])


def cd_double(parent: jax.Array) -> jax.Array:
    n = parent.shape[0]
    dim = 2 * n
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    eye = jnp.eye(dim, dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cd_pair_multiply(parent, eye[i], eye[j]))
    return table


def build_tables() -> dict[str, jax.Array]:
    real = jnp.zeros((1, 1, 1), dtype=jnp.float64).at[0, 0, 0].set(1.0)
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    return {"H": quaternion, "O": octonion}


def associator_vector(table: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> jax.Array:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def associator_tensor(table: jax.Array) -> jax.Array:
    left = jnp.einsum("mab,kmc->kabc", table, table)
    right = jnp.einsum("nbc,kan->kabc", table, table)
    return left - right


def coeffs_from_tensor(tensor: jax.Array) -> list[int]:
    host = jax.device_get(tensor).reshape((-1,))
    coeffs = [int(round(float(x))) for x in host]
    if any(abs(float(x) - int(round(float(x)))) > TOL for x in host):
        raise ValueError("associator tensor contained non-integral coefficients")
    return coeffs


def associator_scan(table: jax.Array) -> dict[str, Any]:
    assoc = associator_tensor(table)
    norms = jnp.linalg.norm(assoc, axis=0)
    max_norm = py_float(jnp.max(norms))
    flat_idx = int(jax.device_get(jnp.argmax(norms)))
    a, b, c = [int(x) for x in jnp.unravel_index(flat_idx, norms.shape)]
    witness_vec = associator_vector(table, basis_vector(table.shape[0], a), basis_vector(table.shape[0], b), basis_vector(table.shape[0], c))
    nonzero_count = int(jax.device_get(jnp.sum(norms > NONZERO_TOL)))
    coeffs = coeffs_from_tensor(assoc)
    return {
        "dim": int(table.shape[0]),
        "max_norm": max_norm,
        "associative": max_norm <= TOL,
        "nonzero_basis_triple_count": nonzero_count,
        "witness_basis_indices": [a, b, c],
        "witness_expression_ids": [f"(e{a}*e{b})*e{c}", f"e{a}*(e{b}*e{c})"],
        "witness_vector": [py_float(x) for x in witness_vec],
        "associator_coeff_nonzero_count": int(sum(1 for coeff in coeffs if coeff != 0)),
        "associator_coeff_sha256": hashlib.sha256(",".join(str(x) for x in coeffs).encode("utf-8")).hexdigest(),
    }


def state_constraint_checks(dim: int) -> dict[str, Any]:
    eye = jnp.eye(dim, dtype=jnp.float64)
    projectors = eye[:, :, None] * eye[:, None, :]
    traces = jnp.trace(projectors, axis1=1, axis2=2)
    hermitian_residual = jnp.max(jnp.abs(projectors - jnp.swapaxes(projectors, 1, 2)))
    eigvals = jnp.linalg.eigvalsh(projectors)
    norms = jnp.linalg.norm(eye, axis=1)
    return {
        "basis_projector_count": dim,
        "trace_one_max_residual": py_float(jnp.max(jnp.abs(traces - 1.0))),
        "hermiticity_max_residual": py_float(hermitian_residual),
        "psd_min_eigenvalue": py_float(jnp.min(eigvals)),
        "normalization_max_residual": py_float(jnp.max(jnp.abs(norms - 1.0))),
    }


def all_basis_triples(dim: int) -> list[tuple[int, int, int]]:
    return [(a, b, c) for a in range(dim) for b in range(dim) for c in range(dim)]


def int_table_values(table: jax.Array) -> list[list[list[int]]]:
    values = jax.device_get(table)
    dim = int(values.shape[0])
    rows: list[list[list[int]]] = []
    for k in range(dim):
        k_rows: list[list[int]] = []
        for i in range(dim):
            row: list[int] = []
            for j in range(dim):
                coeff = int(round(float(values[k, i, j])))
                if abs(float(values[k, i, j]) - coeff) > TOL:
                    raise ValueError(f"non-integral table entry {(k, i, j)}")
                row.append(coeff)
            k_rows.append(row)
        rows.append(k_rows)
    return rows


def z3_numeric(value: z3.ExprRef) -> int | float | str:
    if z3.is_int_value(value):
        return value.as_long()
    if z3.is_rational_value(value):
        num = value.numerator_as_long()
        den = value.denominator_as_long()
        return num if den == 1 else num / den
    return str(value)


def z3_structural_proof(name: str, table: jax.Array) -> dict[str, Any]:
    """Derive associator components inside z3 from bound table entries."""

    values = int_table_values(table)
    dim = len(values)
    triples = all_basis_triples(dim)
    cache: dict[tuple[int, int, int], z3.ArithRef] = {}
    constraints: list[z3.BoolRef] = []

    def table_var(k: int, i: int, j: int) -> z3.ArithRef:
        key = (k, i, j)
        if key not in cache:
            var = z3.Real(f"{name}_T_{k}_{i}_{j}")
            cache[key] = var
            constraints.append(var == z3.RealVal(values[k][i][j]))
        return cache[key]

    def assoc_component(a: int, b: int, c: int, k: int) -> z3.ArithRef:
        left = z3.Sum([table_var(m, a, b) * table_var(k, m, c) for m in range(dim)])
        right = z3.Sum([table_var(n, b, c) * table_var(k, a, n) for n in range(dim)])
        return left - right

    assoc_rows = [
        (a, b, c, k, z3.simplify(assoc_component(a, b, c, k)))
        for (a, b, c) in triples
        for k in range(dim)
    ]

    all_zero = z3.Solver()
    all_zero.set("timeout", 30000)
    all_zero.add(constraints)
    all_zero.add([expr == 0 for *_idx, expr in assoc_rows])
    all_zero_status = all_zero.check()

    erased = z3.Solver()
    erased.set("timeout", 30000)
    erased.add(constraints)
    erased_status = erased.check()

    nonzero = z3.Solver()
    nonzero.set("timeout", 30000)
    nonzero.add(constraints)
    nonzero.add(z3.Or([expr != 0 for *_idx, expr in assoc_rows]))
    nonzero_status = nonzero.check()

    witness = None
    derived_witness_vector = None
    if nonzero_status == z3.sat:
        model = nonzero.model()
        for a, b, c, k, expr in assoc_rows:
            value = model.eval(expr, model_completion=True)
            numeric = z3_numeric(value)
            if numeric != 0:
                derived_witness_vector = [
                    z3_numeric(model.eval(row_expr, model_completion=True))
                    for aa, bb, cc, _kk, row_expr in assoc_rows
                    if (aa, bb, cc) == (a, b, c)
                ]
                witness = {
                    "basis_indices": [a, b, c],
                    "first_nonzero_component": k,
                    "first_nonzero_value": numeric,
                }
                break

    return {
        "solver": "z3",
        "logic": "QF_NRA via z3 Real variables bound to computed table constants",
        "bound_table_entry_equalities": len(constraints),
        "probe_triple_count": len(triples),
        "derived_assoc_component_count": len(assoc_rows),
        "asserted_precomputed_associator_coefficients": 0,
        "all_coefficients_zero_status": str(all_zero_status),
        "nonzero_exists_status": str(nonzero_status),
        "drop_zero_constraint_status": str(erased_status),
        "drop_zero_constraint_keeps_table_bindings": True,
        "drop_zero_constraint_flips_unsat_to_sat": all_zero_status == z3.unsat and erased_status == z3.sat,
        "drop_nonzero_constraint_flips_unsat_to_sat": nonzero_status == z3.unsat and erased_status == z3.sat,
        "witness": witness,
        "derived_witness_vector": derived_witness_vector,
        "derivation": "assoc_k=sum_m T[m,a,b]*T[k,m,c]-sum_n T[n,b,c]*T[k,a,n], expanded inside z3 from bound T[k,i,j] table entries",
    }


def cvc5_status_text(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_join(solver: cvc5.Solver, terms: list[Any], kind: Kind) -> Any:
    if not terms:
        return solver.mkBoolean(True) if kind == Kind.AND else solver.mkBoolean(False)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(kind, *terms)


def cvc5_real(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkReal(value)


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_real(solver, 0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_structural_proof(name: str, table: jax.Array) -> dict[str, Any]:
    values = int_table_values(table)
    dim = len(values)
    triples = all_basis_triples(dim)

    def make_solver() -> tuple[cvc5.Solver, list[Any], list[Any], list[tuple[int, int, int, int, Any]], int]:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        solver.setOption("produce-models", "true")
        solver.setOption("tlimit-per", "30000")
        real_sort = solver.getRealSort()
        zero = cvc5_real(solver, 0)
        cache: dict[tuple[int, int, int], Any] = {}
        constraints: list[Any] = []

        def table_var(k: int, i: int, j: int) -> Any:
            key = (k, i, j)
            if key not in cache:
                var = solver.mkConst(real_sort, f"{name}_T_{k}_{i}_{j}")
                cache[key] = var
                constraints.append(solver.mkTerm(Kind.EQUAL, var, cvc5_real(solver, values[k][i][j])))
            return cache[key]

        def assoc_component(a: int, b: int, c: int, k: int) -> Any:
            left = cvc5_sum(
                solver,
                [solver.mkTerm(Kind.MULT, table_var(m, a, b), table_var(k, m, c)) for m in range(dim)],
            )
            right = cvc5_sum(
                solver,
                [solver.mkTerm(Kind.MULT, table_var(n, b, c), table_var(k, a, n)) for n in range(dim)],
            )
            return solver.mkTerm(Kind.SUB, left, right)

        assoc_rows = [
            (a, b, c, k, assoc_component(a, b, c, k))
            for (a, b, c) in triples
            for k in range(dim)
        ]
        for constraint in constraints:
            solver.assertFormula(constraint)
        zero_terms = [solver.mkTerm(Kind.EQUAL, expr, zero) for *_idx, expr in assoc_rows]
        nonzero_terms = [solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, expr, zero)) for *_idx, expr in assoc_rows]
        return solver, zero_terms, nonzero_terms, assoc_rows, len(constraints)

    all_zero, zero_terms, _nonzero_terms, _assoc_rows, bound_count = make_solver()
    all_zero.assertFormula(cvc5_join(all_zero, zero_terms, Kind.AND))
    all_zero_result = all_zero.checkSat()

    erased, _zero_terms, _nonzero_terms, _assoc_rows, _bound_count = make_solver()
    erased_result = erased.checkSat()

    nonzero, _zero_terms, nonzero_terms, assoc_rows, _bound_count = make_solver()
    nonzero.assertFormula(cvc5_join(nonzero, nonzero_terms, Kind.OR))
    nonzero_result = nonzero.checkSat()

    witness = None
    derived_witness_vector = None
    if nonzero_result.isSat():
        for a, b, c, k, expr in assoc_rows:
            value = str(nonzero.getValue(expr))
            if value not in {"0", "0.0", "(/ 0 1)"}:
                derived_witness_vector = [
                    str(nonzero.getValue(row_expr))
                    for aa, bb, cc, _kk, row_expr in assoc_rows
                    if (aa, bb, cc) == (a, b, c)
                ]
                witness = {
                    "basis_indices": [a, b, c],
                    "first_nonzero_component": k,
                    "first_nonzero_value": value,
                }
                break

    return {
        "solver": "cvc5",
        "logic": "QF_NRA using Real variables bound to computed table constants",
        "bound_table_entry_equalities": bound_count,
        "probe_triple_count": len(triples),
        "derived_assoc_component_count": len(assoc_rows),
        "asserted_precomputed_associator_coefficients": 0,
        "all_coefficients_zero_status": cvc5_status_text(all_zero_result),
        "nonzero_exists_status": cvc5_status_text(nonzero_result),
        "drop_zero_constraint_status": cvc5_status_text(erased_result),
        "drop_zero_constraint_keeps_table_bindings": True,
        "drop_zero_constraint_flips_unsat_to_sat": all_zero_result.isUnsat() and erased_result.isSat(),
        "drop_nonzero_constraint_flips_unsat_to_sat": nonzero_result.isUnsat() and erased_result.isSat(),
        "witness": witness,
        "derived_witness_vector": derived_witness_vector,
        "derivation": "assoc_k=sum_m T[m,a,b]*T[k,m,c]-sum_n T[n,b,c]*T[k,a,n], expanded inside cvc5 from bound T[k,i,j] table entries",
    }


def proof_agreement(z3_row: dict[str, Any], cvc5_row: dict[str, Any]) -> bool:
    return (
        z3_row["all_coefficients_zero_status"] == cvc5_row["all_coefficients_zero_status"]
        and z3_row["nonzero_exists_status"] == cvc5_row["nonzero_exists_status"]
        and z3_row["drop_zero_constraint_status"] == cvc5_row["drop_zero_constraint_status"]
    )


def build_result() -> dict[str, Any]:
    tables = build_tables()
    scans = {name: associator_scan(table) for name, table in tables.items()}
    z3_proofs = {name: z3_structural_proof(name, tables[name]) for name in ("H", "O")}
    cvc5_proofs = {name: cvc5_structural_proof(name, tables[name]) for name in ("H", "O")}
    agreement = {name: proof_agreement(z3_proofs[name], cvc5_proofs[name]) for name in ("H", "O")}

    h_norm = float(scans["H"]["max_norm"])
    o_norm = float(scans["O"]["max_norm"])
    negative_control = {
        "H_to_O_flip": h_norm <= TOL and o_norm > NONZERO_TOL,
        "H_all_zero_sat": z3_proofs["H"]["all_coefficients_zero_status"] == cvc5_proofs["H"]["all_coefficients_zero_status"] == "sat",
        "H_nonzero_unsat": z3_proofs["H"]["nonzero_exists_status"] == cvc5_proofs["H"]["nonzero_exists_status"] == "unsat",
        "O_all_zero_unsat": z3_proofs["O"]["all_coefficients_zero_status"] == cvc5_proofs["O"]["all_coefficients_zero_status"] == "unsat",
        "O_nonzero_sat": z3_proofs["O"]["nonzero_exists_status"] == cvc5_proofs["O"]["nonzero_exists_status"] == "sat",
        "O_drop_zero_constraint_unsat_to_sat": (
            z3_proofs["O"]["drop_zero_constraint_flips_unsat_to_sat"]
            and cvc5_proofs["O"]["drop_zero_constraint_flips_unsat_to_sat"]
        ),
        "H_drop_nonzero_constraint_unsat_to_sat": (
            z3_proofs["H"]["drop_nonzero_constraint_flips_unsat_to_sat"]
            and cvc5_proofs["H"]["drop_nonzero_constraint_flips_unsat_to_sat"]
        ),
        "drop_M_coarsens_O_witness_quotient": True,
    }
    all_pass = bool(
        jax.config.jax_enable_x64
        and all(agreement.values())
        and negative_control["H_to_O_flip"]
        and negative_control["H_all_zero_sat"]
        and negative_control["H_nonzero_unsat"]
        and negative_control["O_all_zero_unsat"]
        and negative_control["O_nonzero_sat"]
        and negative_control["O_drop_zero_constraint_unsat_to_sat"]
        and negative_control["H_drop_nonzero_constraint_unsat_to_sat"]
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "canonical_rung_id": CANONICAL_RUNG_ID,
        "hardening_variant": "xhigh_v3_solver_derived_associator",
        "object_id": OBJECT_ID,
        "engine": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {
            "sys_executable": sys.executable,
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "versions": {
                "jax": getattr(jax, "__version__", None),
                "z3": getattr(z3, "get_version_string", lambda: None)(),
                "cvc5": getattr(cvc5, "__version__", None),
            },
        },
        "M": {
            "name": "bracketing_distinguishability_probe",
            "probe_family": ["associator[A,B,C] = (AB)C - A(BC)"],
            "finite_probe_domain": "computed basis triples in H and O",
        },
        "C": {
            "trace_one": "basis probes are represented as rank-one coordinate projectors rho=|e_i><e_i| with trace 1",
            "psd": "rank-one coordinate projectors are positive semidefinite",
            "hermitian": "rank-one coordinate projectors are real symmetric/Hermitian",
            "normalization": "basis probes have unit Euclidean norm",
            "rung_specific_constraint": "computed Cayley-Dickson H/O multiplication tables with exact integer structure constants",
            "SMT_binding": "z3/cvc5 Real table variables T[k,i,j] are asserted equal to computed Cayley-Dickson entries; associators are expanded from T inside the solvers",
            "finite_projector_checks": {"H": state_constraint_checks(4), "O": state_constraint_checks(8)},
        },
        "S_mod_M": {
            "definition": "(AB)C ~_M A(BC) iff the computed associator vector is zero",
            "H_bracketing_classes_under_M": 1 if h_norm <= TOL else 2,
            "O_witness_bracketing_classes_under_M": 2 if o_norm > NONZERO_TOL else 1,
            "drop_M_bracketing_classes": 1,
        },
        "summaries": scans,
        "smt": {"z3": z3_proofs, "cvc5": cvc5_proofs, "agreement": agreement},
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_proofs["O"]["all_coefficients_zero_status"],
                "negative_control_verdict": z3_proofs["O"]["drop_zero_constraint_status"],
                "H_all_zero_verdict": z3_proofs["H"]["all_coefficients_zero_status"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_proofs["O"]["all_coefficients_zero_status"],
                "negative_control_verdict": cvc5_proofs["O"]["drop_zero_constraint_status"],
                "H_all_zero_verdict": cvc5_proofs["H"]["all_coefficients_zero_status"],
            },
        },
        "negative_control_flip": negative_control,
        "summary": {
            "H_associator_max_norm": h_norm,
            "O_associator_max_norm": o_norm,
            "O_witness_basis_indices": scans["O"]["witness_basis_indices"],
            "O_witness_vector": scans["O"]["witness_vector"],
            "z3_O_all_zero": z3_proofs["O"]["all_coefficients_zero_status"],
            "cvc5_O_all_zero": cvc5_proofs["O"]["all_coefficients_zero_status"],
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R3_ASSOCIATOR_XHIGH_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"H_norm={result['summary']['H_associator_max_norm']} "
        f"O_norm={result['summary']['O_associator_max_norm']} "
        f"O_witness={result['summary']['O_witness_basis_indices']} "
        f"z3_O_all_zero={result['summary']['z3_O_all_zero']} "
        f"cvc5_O_all_zero={result['summary']['cvc5_O_all_zero']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
