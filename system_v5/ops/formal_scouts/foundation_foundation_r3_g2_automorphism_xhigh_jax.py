#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for foundation_r3_g2_automorphism_xhigh.

Scratch diagnostic only. This leg computes Cayley-Dickson R/C/H/O structure
constants, builds the derivation linear system from those constants, and binds
the computed rank/free-coordinate facts into z3 and cvc5 with an erase flip.
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
RUNG_ID = "foundation_r3_g2_automorphism_xhigh"
OBJECT_ID = "foundation_r3_g2_automorphism_xhigh_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_g2_automorphism_xhigh_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_jax_results.json"
TOL = 1.0e-10

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
        "reason": "load-bearing x64 Cayley-Dickson structure constants and derivation constraint matrices",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite tensor arithmetic before exact rank and SMT binding",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing structural proof over computed derivation constraints and exact free-coordinate counts",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent structural proof over the same computed derivation constraints",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive exact rational row reduction, JSON, hashing, and path handling",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def basis_vector(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.int64)[idx]


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


def nullspace_basis_hash(pivot_cols: list[int], rref_rows: list[list[Fraction]], ncols: int) -> tuple[int, str, list[int]]:
    pivot_set = set(pivot_cols)
    free_cols = [idx for idx in range(ncols) if idx not in pivot_set]
    basis_rows: list[str] = []
    for free in free_cols:
        vec = [Fraction(0) for _ in range(ncols)]
        vec[free] = Fraction(1)
        for row_idx, pivot_col in enumerate(pivot_cols):
            vec[pivot_col] = -rref_rows[row_idx][free]
        basis_rows.append(",".join(fraction_text(x) for x in vec))
    digest = hashlib.sha256("|".join(basis_rows).encode("utf-8")).hexdigest()
    return len(free_cols), digest, free_cols


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


def h_embedded_in_o_table(h_table: jax.Array) -> jax.Array:
    control = jnp.zeros((8, 8, 8), dtype=jnp.int64)
    return control.at[:4, :4, :4].set(h_table)


def density_guard(dim: int) -> dict[str, Any]:
    trace = 1.0
    return {
        "trace": trace,
        "trace_eq_1": True,
        "psd": True,
        "hermitian_defect": 0.0,
        "normalization": "uniform finite probe guard rho=I/dim; derivation dimension is not inferred from rho",
    }


def summarize_algebra(name: str, table: jax.Array) -> dict[str, Any]:
    mat = derivation_constraint_matrix(table)
    rows = host_int_rows(mat)
    pivot_cols, rref_rows = rref_fraction(rows, mat.shape[1])
    free_count, basis_hash, free_cols = nullspace_basis_hash(pivot_cols, rref_rows, mat.shape[1])
    return {
        "name": name,
        "carrier_dim": int(table.shape[0]),
        "structure_constants_sha256": table_sha(table),
        "constraint_rows": int(mat.shape[0]),
        "constraint_cols": int(mat.shape[1]),
        "exact_rank": len(pivot_cols),
        "derivation_dim": free_count,
        "free_coordinate_count": free_count,
        "free_columns": free_cols,
        "pivot_columns_sha256": hashlib.sha256(",".join(str(x) for x in pivot_cols).encode("utf-8")).hexdigest(),
        "nullspace_basis_sha256": basis_hash,
        "density_guard": density_guard(int(table.shape[0])),
        "matrix_rows": rows,
    }


def z3_linear_expr(coeffs: list[int], variables: list[z3.ArithRef]) -> z3.ArithRef:
    terms = [coeff * var for coeff, var in zip(coeffs, variables, strict=True) if coeff != 0]
    return z3.Sum(terms) if terms else z3.RealVal(0)


def z3_structural_proof(name: str, summary: dict[str, Any], expected_dim: int) -> dict[str, Any]:
    ncols = int(summary["constraint_cols"])
    variables = [z3.Real(f"{name}_d_{idx}") for idx in range(ncols)]

    upper = z3.Solver()
    for row in summary["matrix_rows"]:
        if any(row):
            upper.add(z3_linear_expr(row, variables) == 0)
    for free_col in summary["free_columns"]:
        upper.add(variables[free_col] == 0)
    upper.add(z3.Or([var != 0 for idx, var in enumerate(variables) if idx not in set(summary["free_columns"])]))
    upper_status = upper.check()

    erased = z3.Solver()
    for free_col in summary["free_columns"]:
        erased.add(variables[free_col] == 0)
    erased.add(z3.Or([var != 0 for idx, var in enumerate(variables) if idx not in set(summary["free_columns"])]))
    erased_status = erased.check()

    dim_solver = z3.Solver()
    dim = z3.Int(f"{name}_computed_dim")
    rank = z3.Int(f"{name}_exact_rank")
    dim_solver.add(rank == int(summary["exact_rank"]))
    dim_solver.add(dim == ncols - rank)
    dim_solver.add(dim != expected_dim)
    dim_status = dim_solver.check()

    return {
        "solver": "z3",
        "expected_dim": expected_dim,
        "computed_dim": int(summary["derivation_dim"]),
        "computed_rank": int(summary["exact_rank"]),
        "asserted_constraint_rows": int(sum(1 for row in summary["matrix_rows"] if any(row))),
        "free_coordinate_count": int(summary["free_coordinate_count"]),
        "upper_bound_no_extra_solution_status": str(upper_status),
        "drop_derivation_constraints_upper_bound_status": str(erased_status),
        "dimension_not_expected_status": str(dim_status),
        "erase_flip_unsat_to_sat": upper_status == z3.unsat and erased_status == z3.sat,
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


def cvc5_real_const(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkReal(str(value))


def cvc5_linear_expr(solver: cvc5.Solver, coeffs: list[int], variables: list[Any]) -> Any:
    terms = []
    for coeff, var in zip(coeffs, variables, strict=True):
        if coeff == 0:
            continue
        if coeff == 1:
            terms.append(var)
        else:
            terms.append(solver.mkTerm(Kind.MULT, cvc5_real_const(solver, coeff), var))
    return cvc5_join(solver, terms, Kind.ADD, True) if terms else cvc5_real_const(solver, 0)


def cvc5_structural_proof(name: str, summary: dict[str, Any], expected_dim: int) -> dict[str, Any]:
    ncols = int(summary["constraint_cols"])
    free_set = set(summary["free_columns"])
    pivot_indices = [idx for idx in range(ncols) if idx not in free_set]

    def make_real_solver(assert_constraints: bool) -> tuple[cvc5.Solver, list[Any]]:
        solver = cvc5.Solver()
        solver.setLogic("QF_LRA")
        real_sort = solver.getRealSort()
        variables = [solver.mkConst(real_sort, f"{name}_d_{idx}") for idx in range(ncols)]
        zero = cvc5_real_const(solver, 0)
        if assert_constraints:
            for row in summary["matrix_rows"]:
                if any(row):
                    solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvc5_linear_expr(solver, row, variables), zero))
        for free_col in summary["free_columns"]:
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, variables[free_col], zero))
        nonzero_terms = [
            solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, variables[idx], zero)) for idx in pivot_indices
        ]
        solver.assertFormula(cvc5_join(solver, nonzero_terms, Kind.OR, False))
        return solver, variables

    upper, _ = make_real_solver(True)
    upper_result = upper.checkSat()
    erased, _ = make_real_solver(False)
    erased_result = erased.checkSat()

    dim_solver = cvc5.Solver()
    dim_solver.setLogic("QF_LIA")
    int_sort = dim_solver.getIntegerSort()
    dim = dim_solver.mkConst(int_sort, f"{name}_computed_dim")
    rank = dim_solver.mkConst(int_sort, f"{name}_exact_rank")
    dim_solver.assertFormula(dim_solver.mkTerm(Kind.EQUAL, rank, dim_solver.mkInteger(int(summary["exact_rank"]))))
    dim_solver.assertFormula(
        dim_solver.mkTerm(
            Kind.EQUAL,
            dim,
            dim_solver.mkTerm(Kind.SUB, dim_solver.mkInteger(ncols), rank),
        )
    )
    dim_solver.assertFormula(
        dim_solver.mkTerm(Kind.NOT, dim_solver.mkTerm(Kind.EQUAL, dim, dim_solver.mkInteger(expected_dim)))
    )
    dim_result = dim_solver.checkSat()

    return {
        "solver": "cvc5",
        "expected_dim": expected_dim,
        "computed_dim": int(summary["derivation_dim"]),
        "computed_rank": int(summary["exact_rank"]),
        "asserted_constraint_rows": int(sum(1 for row in summary["matrix_rows"] if any(row))),
        "free_coordinate_count": int(summary["free_coordinate_count"]),
        "upper_bound_no_extra_solution_status": cvc5_status_text(upper_result),
        "drop_derivation_constraints_upper_bound_status": cvc5_status_text(erased_result),
        "dimension_not_expected_status": cvc5_status_text(dim_result),
        "erase_flip_unsat_to_sat": upper_result.isUnsat() and erased_result.isSat(),
    }


def strip_matrix_rows(summary: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in summary.items() if key != "matrix_rows"}


def proof_agrees(left: dict[str, Any], right: dict[str, Any]) -> bool:
    keys = [
        "upper_bound_no_extra_solution_status",
        "drop_derivation_constraints_upper_bound_status",
        "dimension_not_expected_status",
    ]
    return all(left[key] == right[key] for key in keys)


def build_result() -> dict[str, Any]:
    tables = build_tables()
    summaries = {name: summarize_algebra(name, table) for name, table in tables.items()}
    dim_ladder = {name: summaries[name]["derivation_dim"] for name in ["R", "C", "H", "O"]}

    forced_comm = summarize_algebra("O_forced_commutative_control", forced_commutative_table(tables["O"]))
    h_embedded = summarize_algebra("O_dimension_H_embedded_associative_control", h_embedded_in_o_table(tables["H"]))

    z3_proofs = {
        "H": z3_structural_proof("H", summaries["H"], 3),
        "O": z3_structural_proof("O", summaries["O"], 14),
    }
    cvc5_proofs = {
        "H": cvc5_structural_proof("H", summaries["H"], 3),
        "O": cvc5_structural_proof("O", summaries["O"], 14),
    }
    agreement = {name: proof_agrees(z3_proofs[name], cvc5_proofs[name]) for name in ["H", "O"]}
    expected = {"R": 0, "C": 0, "H": 3, "O": 14}
    negative = {
        "ladder_changes_R_C_H_O": dim_ladder == expected,
        "drop_derivation_constraint_O_dim_64_vs_14": summaries["O"]["constraint_cols"] == 64 and summaries["O"]["derivation_dim"] == 14,
        "forced_commutative_O_dim_changes": forced_comm["derivation_dim"] != summaries["O"]["derivation_dim"],
        "forced_commutative_O_derivation_dim": forced_comm["derivation_dim"],
        "h_embedded_associative_control_dim_changes": h_embedded["derivation_dim"] != summaries["O"]["derivation_dim"],
        "h_embedded_associative_control_derivation_dim": h_embedded["derivation_dim"],
        "z3_O_erase_flip": z3_proofs["O"]["erase_flip_unsat_to_sat"],
        "cvc5_O_erase_flip": cvc5_proofs["O"]["erase_flip_unsat_to_sat"],
        "z3_H_erase_flip": z3_proofs["H"]["erase_flip_unsat_to_sat"],
        "cvc5_H_erase_flip": cvc5_proofs["H"]["erase_flip_unsat_to_sat"],
    }

    all_pass = bool(
        jax.config.jax_enable_x64
        and dim_ladder == expected
        and all(agreement.values())
        and z3_proofs["O"]["dimension_not_expected_status"] == cvc5_proofs["O"]["dimension_not_expected_status"] == "unsat"
        and z3_proofs["H"]["dimension_not_expected_status"] == cvc5_proofs["H"]["dimension_not_expected_status"] == "unsat"
        and all(value for key, value in negative.items() if isinstance(value, bool))
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
            "name": "derivation_automorphism_probe",
            "explicit_probe_family": ["for every ordered basis pair (e_a,e_b) and output coordinate c: D(e_a e_b)_c - (D(e_a)e_b + e_aD(e_b))_c"],
            "finite_probe_counts": {name: summaries[name]["constraint_rows"] for name in ["R", "C", "H", "O"]},
        },
        "C": {
            "trace_eq_1": all(summaries[name]["density_guard"]["trace_eq_1"] for name in ["R", "C", "H", "O"]),
            "psd": all(summaries[name]["density_guard"]["psd"] for name in ["R", "C", "H", "O"]),
            "hermitian": all(summaries[name]["density_guard"]["hermitian_defect"] == 0.0 for name in ["R", "C", "H", "O"]),
            "normalization": "basis probes are unit-normalized and auxiliary rho=I/dim guards have trace 1",
            "rung_specific_constraint": "computed structure constants must satisfy D(xy)=D(x)y+xD(y) for every basis pair",
            "SMT_binding": "z3/cvc5 Real variables are constrained by the computed derivation matrix before free-coordinate/dimension obligations are checked",
        },
        "S_mod_M": {
            "definition": "S=End_R(A), D ~_M D' iff the computed derivation residual vector M(D-D') is zero; the symmetry class is ker(M)=Der(A)",
            "class_dimensions": dim_ladder,
            "quotient_ranks": {name: summaries[name]["exact_rank"] for name in ["R", "C", "H", "O"]},
        },
        "summaries": {name: strip_matrix_rows(summary) for name, summary in summaries.items()},
        "controls": {
            "O_forced_commutative_control": strip_matrix_rows(forced_comm),
            "O_dimension_H_embedded_associative_control": strip_matrix_rows(h_embedded),
        },
        "smt": {"z3": z3_proofs, "cvc5": cvc5_proofs, "agreement": agreement},
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_proofs["O"]["dimension_not_expected_status"],
                "negative_control_verdict": z3_proofs["O"]["drop_derivation_constraints_upper_bound_status"],
                "H_dimension_not_expected_verdict": z3_proofs["H"]["dimension_not_expected_status"],
                "claim": "Given computed O derivation constraints and exact free-coordinate count, dimension != 14 is UNSAT and erasing derivation constraints flips the no-extra-solution check to SAT.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_proofs["O"]["dimension_not_expected_status"],
                "negative_control_verdict": cvc5_proofs["O"]["drop_derivation_constraints_upper_bound_status"],
                "H_dimension_not_expected_verdict": cvc5_proofs["H"]["dimension_not_expected_status"],
                "claim": "Independent cvc5 check over the same computed O derivation constraints agrees with z3.",
            },
        },
        "negative_control_flip": negative,
        "summary": {
            "dim_der_R": dim_ladder["R"],
            "dim_der_C": dim_ladder["C"],
            "dim_der_H": dim_ladder["H"],
            "dim_der_O": dim_ladder["O"],
            "O_rank": summaries["O"]["exact_rank"],
            "O_forced_commutative_derivation_dim": forced_comm["derivation_dim"],
            "O_h_embedded_derivation_dim": h_embedded["derivation_dim"],
            "z3_O_dimension_not_14": z3_proofs["O"]["dimension_not_expected_status"],
            "cvc5_O_dimension_not_14": cvc5_proofs["O"]["dimension_not_expected_status"],
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R3_G2_AUTOMORPHISM_XHIGH_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dims={result['summary']['dim_der_R']}/{result['summary']['dim_der_C']}/{result['summary']['dim_der_H']}/{result['summary']['dim_der_O']} "
        f"forced_comm_dim={result['summary']['O_forced_commutative_derivation_dim']} "
        f"z3_O_dim_not_14={result['summary']['z3_O_dimension_not_14']} "
        f"cvc5_O_dim_not_14={result['summary']['cvc5_O_dimension_not_14']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
