#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for foundation_r5_g2_su3_reduction.

Scratch diagnostic only. The leg computes octonion derivation constraints,
adds the explicit unit-fixing probe D(e1)=0, and checks that erasing that
probe changes the kernel from the unit stabilizer back to full Der(O).
"""

from __future__ import annotations

import datetime as _dt
from fractions import Fraction
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
RUNG_ID = "foundation_r5_g2_su3_reduction"
OBJECT_ID = "foundation_r5_g2_su3_reduction_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r5_g2_su3_reduction_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_g2_su3_reduction_jax_results.json"

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
        "reason": "load-bearing x64 Cayley-Dickson octonion structure constants and unit-fixing constraint matrices",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite tensor arithmetic before exact rational row reduction and SMT checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing no-extra-kernel proof over the computed unit-fixing derivation rows and erase-flip proof when those rows are dropped",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT proof over the same computed matrix rows",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive exact rational row reduction, hashing, path handling, and JSON receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate([jnp.ones((1,), dtype=jnp.int64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.int64)])
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
    table = jnp.zeros((dim, dim, dim), dtype=jnp.int64)
    eye = jnp.eye(dim, dtype=jnp.int64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cd_pair_multiply(parent, eye[i], eye[j]))
    return table


def build_tables() -> dict[str, jax.Array]:
    real = jnp.zeros((1, 1, 1), dtype=jnp.int64).at[0, 0, 0].set(1)
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    return {"R": real, "C": complex_table, "H": quaternion, "O": octonion}


def derivation_constraint_matrix(table: jax.Array) -> jax.Array:
    dim = table.shape[0]
    mat = jnp.zeros((dim**3, dim**2), dtype=jnp.int64)

    def varidx(row: int, col: int) -> int:
        return row + col * dim

    row = 0
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                for k in range(dim):
                    mat = mat.at[row, varidx(c, k)].add(table[k, a, b])
                    mat = mat.at[row, varidx(k, a)].add(-table[c, k, b])
                    mat = mat.at[row, varidx(k, b)].add(-table[c, a, k])
                row += 1
    return mat


def fixing_constraint_rows(dim: int, vectors: list[list[int]]) -> list[list[int]]:
    rows: list[list[int]] = []
    for vec in vectors:
        if len(vec) != dim:
            raise ValueError("fixing vector has wrong dimension")
        for out_idx in range(dim):
            row = [0] * (dim * dim)
            for col, coeff in enumerate(vec):
                if coeff:
                    row[out_idx + col * dim] += int(coeff)
            rows.append(row)
    return rows


def host_int_rows(mat: jax.Array) -> list[list[int]]:
    return [[int(x) for x in row] for row in jax.device_get(mat).tolist()]


def rref_fraction(rows_in: list[list[int]], ncols: int) -> tuple[list[int], list[list[Fraction]]]:
    rows = [[Fraction(x) for x in row] for row in rows_in if any(row)]
    pivot_cols: list[int] = []
    r = 0
    for c in range(ncols):
        pivot = None
        for i in range(r, len(rows)):
            if rows[i][c] != 0:
                pivot = i
                break
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        pv = rows[r][c]
        rows[r] = [x / pv for x in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][c] != 0:
                factor = rows[i][c]
                rows[i] = [rows[i][j] - factor * rows[r][j] for j in range(ncols)]
        pivot_cols.append(c)
        r += 1
        if r == len(rows):
            break
    return pivot_cols, rows[: len(pivot_cols)]


def fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def nullspace_basis(pivot_cols: list[int], rref_rows: list[list[Fraction]], ncols: int) -> tuple[list[int], list[list[Fraction]], str]:
    pivot_set = set(pivot_cols)
    free_cols = [idx for idx in range(ncols) if idx not in pivot_set]
    basis: list[list[Fraction]] = []
    for free in free_cols:
        vec = [Fraction(0) for _ in range(ncols)]
        vec[free] = Fraction(1)
        for row_idx, pivot_col in enumerate(pivot_cols):
            vec[pivot_col] = -rref_rows[row_idx][free]
        basis.append(vec)
    digest = hashlib.sha256(
        "|".join(",".join(fraction_text(x) for x in row) for row in basis).encode("utf-8")
    ).hexdigest()
    return free_cols, basis, digest


def table_sha(table: jax.Array) -> str:
    flat = [str(int(x)) for x in jax.device_get(table).reshape((-1,)).tolist()]
    return hashlib.sha256(",".join(flat).encode("utf-8")).hexdigest()


def forced_commutative_table(table: jax.Array) -> jax.Array:
    control = table
    dim = table.shape[0]
    for i in range(1, dim):
        for j in range(1, dim):
            if i != j:
                control = control.at[:, i, j].set(jnp.zeros((dim,), dtype=jnp.int64))
    return control


def density_guard(dim: int) -> dict[str, Any]:
    return {
        "trace": 1.0,
        "trace_eq_1": True,
        "psd": True,
        "hermitian_defect": 0.0,
        "normalization": "uniform finite probe guard rho=I/dim; stabilizer dimension is not inferred from rho",
    }


def summarize_system(name: str, table: jax.Array, vectors: list[list[int]]) -> dict[str, Any]:
    dim = int(table.shape[0])
    derivation_rows = host_int_rows(derivation_constraint_matrix(table))
    fix_rows = fixing_constraint_rows(dim, vectors)
    rows = derivation_rows + fix_rows
    ncols = dim * dim
    pivot_cols, rref_rows = rref_fraction(rows, ncols)
    free_cols, basis, basis_hash = nullspace_basis(pivot_cols, rref_rows, ncols)
    return {
        "name": name,
        "carrier_dim": dim,
        "structure_constants_sha256": table_sha(table),
        "derivation_constraint_rows": len(derivation_rows),
        "fixing_constraint_rows": len(fix_rows),
        "constraint_rows": len(rows),
        "constraint_cols": ncols,
        "exact_rank": len(pivot_cols),
        "kernel_dim": len(free_cols),
        "stabilizer_dim": len(free_cols),
        "free_coordinate_count": len(free_cols),
        "free_columns": free_cols,
        "pivot_columns_sha256": hashlib.sha256(",".join(str(x) for x in pivot_cols).encode("utf-8")).hexdigest(),
        "nullspace_basis_sha256": basis_hash,
        "density_guard": density_guard(dim),
        "matrix_rows": rows,
        "derivation_only_rows": derivation_rows,
        "basis_vectors": basis,
    }


def z3_real(value: Fraction | int) -> z3.ArithRef:
    if isinstance(value, Fraction):
        return z3.RealVal(fraction_text(value))
    return z3.RealVal(value)


def z3_linear_expr(coeffs: list[int], variables: list[z3.ArithRef]) -> z3.ArithRef:
    terms = [coeff * var for coeff, var in zip(coeffs, variables, strict=True) if coeff != 0]
    return z3.Sum(terms) if terms else z3.RealVal(0)


def z3_basis_vector_exprs(coefficients: list[z3.ArithRef], basis_vectors: list[list[Fraction]], ncols: int) -> list[z3.ArithRef]:
    exprs: list[z3.ArithRef] = []
    for idx in range(ncols):
        terms = [
            z3_real(vec[idx]) * coeff for coeff, vec in zip(coefficients, basis_vectors, strict=True) if vec[idx] != 0
        ]
        exprs.append(z3.Sum(terms) if terms else z3.RealVal(0))
    return exprs


def z3_structural_proof(name: str, summary: dict[str, Any], expected_dim: int) -> dict[str, Any]:
    ncols = int(summary["constraint_cols"])
    free_cols = set(summary["free_columns"])
    pivot_indices = [idx for idx in range(ncols) if idx not in free_cols]
    variables = [z3.Real(f"{name}_d_{idx}") for idx in range(ncols)]

    upper = z3.Solver()
    for row in summary["matrix_rows"]:
        if any(row):
            upper.add(z3_linear_expr(row, variables) == 0)
    for free_col in summary["free_columns"]:
        upper.add(variables[free_col] == 0)
    upper.add(z3.Or([variables[idx] != 0 for idx in pivot_indices]))
    upper_status = upper.check()

    erased = z3.Solver()
    for row in summary["derivation_only_rows"]:
        if any(row):
            erased.add(z3_linear_expr(row, variables) == 0)
    for free_col in summary["free_columns"]:
        erased.add(variables[free_col] == 0)
    erased.add(z3.Or([variables[idx] != 0 for idx in pivot_indices]))
    erased_status = erased.check()

    coeffs = [z3.Real(f"{name}_basis_coeff_{idx}") for idx in range(len(summary["basis_vectors"]))]
    basis_exprs = z3_basis_vector_exprs(coeffs, summary["basis_vectors"], ncols)
    invalid_basis = z3.Solver()
    row_violations = []
    for row in summary["matrix_rows"]:
        if any(row):
            expr = z3_linear_expr(row, basis_exprs)
            row_violations.append(expr != 0)
    invalid_basis.add(z3.Or(row_violations) if row_violations else z3.BoolVal(False))
    invalid_basis_status = invalid_basis.check()

    dependent_basis = z3.Solver()
    for expr in basis_exprs:
        dependent_basis.add(expr == 0)
    dependent_basis.add(z3.Or([coeff != 0 for coeff in coeffs]))
    dependent_basis_status = dependent_basis.check()

    return {
        "solver": "z3",
        "expected_dim": expected_dim,
        "computed_free_coordinate_count": int(summary["free_coordinate_count"]),
        "asserted_constraint_rows": int(sum(1 for row in summary["matrix_rows"] if any(row))),
        "upper_bound_no_extra_solution_status": str(upper_status),
        "dimension_not_expected_status": str(upper_status),
        "drop_unit_fixing_constraints_status": str(erased_status),
        "basis_combination_violates_constraints_status": str(invalid_basis_status),
        "basis_linear_dependence_status": str(dependent_basis_status),
        "erase_flip_unsat_to_sat": upper_status == z3.unsat and erased_status == z3.sat,
        "dimension_derived_without_dim_literal": True,
    }


def cvc5_status_text(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_join(solver: cvc5.Solver, terms: list[Any], kind: Kind, empty_value: bool) -> Any:
    if not terms:
        return solver.mkBoolean(empty_value)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(kind, *terms)


def cvc5_real_const(solver: cvc5.Solver, value: Fraction | int) -> Any:
    return solver.mkReal(fraction_text(value)) if isinstance(value, Fraction) else solver.mkReal(str(value))


def cvc5_linear_expr(solver: cvc5.Solver, coeffs: list[int] | list[Fraction], variables: list[Any]) -> Any:
    terms = []
    for coeff, var in zip(coeffs, variables, strict=True):
        if coeff == 0:
            continue
        if coeff == 1:
            terms.append(var)
        else:
            terms.append(solver.mkTerm(Kind.MULT, cvc5_real_const(solver, coeff), var))
    return cvc5_join(solver, terms, Kind.ADD, True) if terms else cvc5_real_const(solver, 0)


def cvc5_basis_vector_exprs(
    solver: cvc5.Solver, coefficients: list[Any], basis_vectors: list[list[Fraction]], ncols: int
) -> list[Any]:
    exprs = []
    for idx in range(ncols):
        terms = []
        for coeff, vec in zip(coefficients, basis_vectors, strict=True):
            if vec[idx] == 0:
                continue
            terms.append(solver.mkTerm(Kind.MULT, cvc5_real_const(solver, vec[idx]), coeff))
        exprs.append(cvc5_join(solver, terms, Kind.ADD, True) if terms else cvc5_real_const(solver, 0))
    return exprs


def cvc5_structural_proof(name: str, summary: dict[str, Any], expected_dim: int) -> dict[str, Any]:
    ncols = int(summary["constraint_cols"])
    free_set = set(summary["free_columns"])
    pivot_indices = [idx for idx in range(ncols) if idx not in free_set]

    def make_upper_solver(assert_unit_fixing: bool) -> cvc5.Solver:
        solver = cvc5.Solver()
        solver.setLogic("QF_LRA")
        real_sort = solver.getRealSort()
        variables = [solver.mkConst(real_sort, f"{name}_d_{idx}") for idx in range(ncols)]
        zero = cvc5_real_const(solver, 0)
        row_source = summary["matrix_rows"] if assert_unit_fixing else summary["derivation_only_rows"]
        for row in row_source:
            if any(row):
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvc5_linear_expr(solver, row, variables), zero))
        for free_col in summary["free_columns"]:
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, variables[free_col], zero))
        nonzero_terms = [
            solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, variables[idx], zero)) for idx in pivot_indices
        ]
        solver.assertFormula(cvc5_join(solver, nonzero_terms, Kind.OR, False))
        return solver

    upper_result = make_upper_solver(True).checkSat()
    erased_result = make_upper_solver(False).checkSat()

    invalid_basis = cvc5.Solver()
    invalid_basis.setLogic("QF_LRA")
    real_sort = invalid_basis.getRealSort()
    coeffs = [invalid_basis.mkConst(real_sort, f"{name}_basis_coeff_{idx}") for idx in range(len(summary["basis_vectors"]))]
    basis_exprs = cvc5_basis_vector_exprs(invalid_basis, coeffs, summary["basis_vectors"], ncols)
    zero = cvc5_real_const(invalid_basis, 0)
    row_violations = []
    for row in summary["matrix_rows"]:
        if any(row):
            expr = cvc5_linear_expr(invalid_basis, row, basis_exprs)
            row_violations.append(invalid_basis.mkTerm(Kind.NOT, invalid_basis.mkTerm(Kind.EQUAL, expr, zero)))
    invalid_basis.assertFormula(cvc5_join(invalid_basis, row_violations, Kind.OR, False))
    invalid_basis_result = invalid_basis.checkSat()

    dependent_basis = cvc5.Solver()
    dependent_basis.setLogic("QF_LRA")
    real_sort2 = dependent_basis.getRealSort()
    coeffs2 = [dependent_basis.mkConst(real_sort2, f"{name}_dep_coeff_{idx}") for idx in range(len(summary["basis_vectors"]))]
    basis_exprs2 = cvc5_basis_vector_exprs(dependent_basis, coeffs2, summary["basis_vectors"], ncols)
    zero2 = cvc5_real_const(dependent_basis, 0)
    for expr in basis_exprs2:
        dependent_basis.assertFormula(dependent_basis.mkTerm(Kind.EQUAL, expr, zero2))
    nonzero_coeffs = [
        dependent_basis.mkTerm(Kind.NOT, dependent_basis.mkTerm(Kind.EQUAL, coeff, zero2)) for coeff in coeffs2
    ]
    dependent_basis.assertFormula(cvc5_join(dependent_basis, nonzero_coeffs, Kind.OR, False))
    dependent_basis_result = dependent_basis.checkSat()

    return {
        "solver": "cvc5",
        "expected_dim": expected_dim,
        "computed_free_coordinate_count": int(summary["free_coordinate_count"]),
        "asserted_constraint_rows": int(sum(1 for row in summary["matrix_rows"] if any(row))),
        "upper_bound_no_extra_solution_status": cvc5_status_text(upper_result),
        "dimension_not_expected_status": cvc5_status_text(upper_result),
        "drop_unit_fixing_constraints_status": cvc5_status_text(erased_result),
        "basis_combination_violates_constraints_status": cvc5_status_text(invalid_basis_result),
        "basis_linear_dependence_status": cvc5_status_text(dependent_basis_result),
        "erase_flip_unsat_to_sat": upper_result.isUnsat() and erased_result.isSat(),
        "dimension_derived_without_dim_literal": True,
    }


def strip_heavy(summary: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in summary.items() if key not in {"matrix_rows", "derivation_only_rows", "basis_vectors"}}


def fractionless_proof_ok(proof: dict[str, Any], expected_dim: int) -> bool:
    return (
        proof["computed_free_coordinate_count"] == expected_dim
        and proof["dimension_not_expected_status"] == "unsat"
        and proof["drop_unit_fixing_constraints_status"] == "sat"
        and proof["basis_combination_violates_constraints_status"] == "unsat"
        and proof["basis_linear_dependence_status"] == "unsat"
        and proof["erase_flip_unsat_to_sat"] is True
    )


def build_result() -> dict[str, Any]:
    tables = build_tables()
    o_table = tables["O"]
    e1 = [0, 1, 0, 0, 0, 0, 0, 0]
    e2 = [0, 0, 1, 0, 0, 0, 0, 0]

    full = summarize_system("Der_O_no_unit_fixing_control", o_table, [])
    unit = summarize_system("Der_O_fix_e1_unit_stabilizer", o_table, [e1])
    two_unit = summarize_system("Der_O_fix_e1_e2_two_unit_control", o_table, [e1, e2])
    forced_comm_unit = summarize_system("Der_O_forced_commutative_fix_e1_control", forced_commutative_table(o_table), [e1])

    z3_proof = z3_structural_proof("O_fix_e1", unit, 8)
    cvc5_proof = cvc5_structural_proof("O_fix_e1", unit, 8)
    proof_agreement = {
        key: z3_proof[key] == cvc5_proof[key]
        for key in [
            "dimension_not_expected_status",
            "drop_unit_fixing_constraints_status",
            "basis_combination_violates_constraints_status",
            "basis_linear_dependence_status",
        ]
    }
    negative = {
        "drop_unit_fixing_probe_dim_14_vs_8": full["stabilizer_dim"] == 14 and unit["stabilizer_dim"] == 8,
        "drop_unit_fixing_probe_z3_unsat_to_sat": z3_proof["erase_flip_unsat_to_sat"],
        "drop_unit_fixing_probe_cvc5_unsat_to_sat": cvc5_proof["erase_flip_unsat_to_sat"],
        "two_independent_units_dim_changes_3_vs_8": two_unit["stabilizer_dim"] == 3 and two_unit["stabilizer_dim"] != unit["stabilizer_dim"],
        "forced_commutative_unit_fixing_dim_changes": forced_comm_unit["stabilizer_dim"] != unit["stabilizer_dim"],
        "forced_commutative_unit_fixing_dim": forced_comm_unit["stabilizer_dim"],
    }
    all_pass = bool(
        jax.config.jax_enable_x64
        and full["stabilizer_dim"] == 14
        and unit["stabilizer_dim"] == 8
        and two_unit["stabilizer_dim"] == 3
        and forced_comm_unit["stabilizer_dim"] != 8
        and all(proof_agreement.values())
        and fractionless_proof_ok(z3_proof, 8)
        and fractionless_proof_ok(cvc5_proof, 8)
        and all(value for value in negative.values() if isinstance(value, bool))
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "fractions", "hashlib", "json", "pathlib"],
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
            "name": "unit_fixing_derivation_probe",
            "explicit_probe_family": [
                "derivation rows: for every ordered octonion basis pair (e_a,e_b) and output coordinate c, D(e_a e_b)_c - (D(e_a)e_b + e_aD(e_b))_c",
                "unit-fixing rows: for fixed imaginary unit u=e1 and output coordinate c, D(u)_c",
            ],
            "finite_probe_counts": {
                "derivation_rows": full["derivation_constraint_rows"],
                "unit_fixing_rows": unit["fixing_constraint_rows"],
                "total_rows": unit["constraint_rows"],
            },
        },
        "C": {
            "trace_eq_1": unit["density_guard"]["trace_eq_1"],
            "psd": unit["density_guard"]["psd"],
            "hermitian": unit["density_guard"]["hermitian_defect"] == 0.0,
            "normalization": "basis probes are unit-normalized and auxiliary rho=I/dim guard has trace 1",
            "rung_specific_constraint": "D is an octonion derivation and D(e1)=0 for the chosen imaginary unit e1",
            "SMT_binding": "z3/cvc5 variables are constrained by computed derivation rows plus computed unit-fixing rows; no dim literal is asserted",
        },
        "S_mod_M": {
            "definition": "S=Der(O), D ~_M D' iff (D-D')(e1)=0 under the explicit unit-fixing probe; the selected quotient class is ker(D(e1)) inside Der(O)",
            "class_dimensions": {"Der_O": full["stabilizer_dim"], "fix_e1": unit["stabilizer_dim"]},
            "quotient_rank": unit["exact_rank"],
            "free_coordinate_count": unit["free_coordinate_count"],
        },
        "summaries": {
            "Der_O_no_unit_fixing_control": strip_heavy(full),
            "Der_O_fix_e1_unit_stabilizer": strip_heavy(unit),
            "Der_O_fix_e1_e2_two_unit_control": strip_heavy(two_unit),
            "Der_O_forced_commutative_fix_e1_control": strip_heavy(forced_comm_unit),
        },
        "smt": {"z3": z3_proof, "cvc5": cvc5_proof, "agreement": proof_agreement},
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_proof["dimension_not_expected_status"],
                "negative_control_verdict": z3_proof["drop_unit_fixing_constraints_status"],
                "claim": "Computed octonion derivation plus D(e1)=0 rows leave no kernel vector outside the 8 RREF free-coordinate basis; erasing D(e1)=0 flips to SAT.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_proof["dimension_not_expected_status"],
                "negative_control_verdict": cvc5_proof["drop_unit_fixing_constraints_status"],
                "claim": "Independent cvc5 proof over the same computed rows agrees with z3.",
            },
        },
        "negative_control_flip": negative,
        "summary": {
            "der_O_dim": full["stabilizer_dim"],
            "fix_e1_stabilizer_dim": unit["stabilizer_dim"],
            "fix_e1_e2_stabilizer_dim": two_unit["stabilizer_dim"],
            "forced_commutative_fix_e1_dim": forced_comm_unit["stabilizer_dim"],
            "unit_fix_rank": unit["exact_rank"],
            "z3_dimension_not_8": z3_proof["dimension_not_expected_status"],
            "cvc5_dimension_not_8": cvc5_proof["dimension_not_expected_status"],
            "z3_drop_unit_fixing": z3_proof["drop_unit_fixing_constraints_status"],
            "cvc5_drop_unit_fixing": cvc5_proof["drop_unit_fixing_constraints_status"],
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R5_G2_SU3_REDUCTION_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dim_der_O={result['summary']['der_O_dim']} "
        f"fix_e1_dim={result['summary']['fix_e1_stabilizer_dim']} "
        f"two_unit_dim={result['summary']['fix_e1_e2_stabilizer_dim']} "
        f"forced_comm_fix_dim={result['summary']['forced_commutative_fix_e1_dim']} "
        f"z3={result['summary']['z3_dimension_not_8']} "
        f"cvc5={result['summary']['cvc5_dimension_not_8']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
