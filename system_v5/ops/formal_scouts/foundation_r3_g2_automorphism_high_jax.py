#!/usr/bin/env python3
"""JAX + z3/cvc5 hardened leg for foundation_r3_g2_automorphism_high.

The SMT check deliberately does not assert precomputed kernel or RREF
relations. RREF is used only to select 14 candidate derivation matrices. The
solvers then expand the Leibniz defect from bound octonion structure constants
and bound candidate D entries.
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
RUNG_ID = "foundation_r3_g2_automorphism"
OBJECT_ID = "foundation_r3_g2_automorphism_high"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_g2_automorphism_high_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_g2_automorphism_high_jax_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False


def basis_vector(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.int64)[idx]


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate([jnp.ones((1,), dtype=jnp.int64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.int64)])
    return x * signs


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    return jnp.concatenate([first, second])


def cd_double(parent: jax.Array) -> jax.Array:
    dim = int(parent.shape[0] * 2)
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
    commutative_projection = jnp.asarray(0.5 * (octonion + jnp.swapaxes(octonion, 1, 2)), dtype=jnp.float64)
    return {
        "R": real,
        "C": complex_table,
        "H": quaternion,
        "O": octonion,
        "O_commutative_projection_control": commutative_projection,
    }


def derivation_rows(table: jax.Array, *, imaginary_only: bool = False, unit_only: bool = False) -> tuple[list[list[Fraction]], list[tuple[int, int, int]]]:
    dim = int(table.shape[0])
    host = jax.device_get(table).tolist()
    rows: list[list[Fraction]] = []
    labels: list[tuple[int, int, int]] = []
    for i in range(dim):
        for j in range(dim):
            for k in range(dim):
                if imaginary_only and (i == 0 or j == 0 or k == 0):
                    continue
                if unit_only and i != 0 and j != 0:
                    continue
                coeffs = [Fraction(0) for _ in range(dim * dim)]
                for m in range(dim):
                    # Variable index is D[row, col] = D[row + col * dim].
                    coeffs[k + m * dim] += Fraction(host[m][i][j])
                    coeffs[m + i * dim] -= Fraction(host[k][m][j])
                    coeffs[m + j * dim] -= Fraction(host[k][i][m])
                rows.append(coeffs)
                labels.append((i, j, k))
    return rows, labels


def rref(rows_in: list[list[Fraction]], ncols: int) -> tuple[list[int], list[list[Fraction]]]:
    rows = [[Fraction(x) for x in row] for row in rows_in if any(row)]
    pivot_cols: list[int] = []
    r = 0
    for c in range(ncols):
        pivot = next((idx for idx in range(r, len(rows)) if rows[idx][c] != 0), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        scale = rows[r][c]
        rows[r] = [x / scale for x in rows[r]]
        for idx in range(len(rows)):
            if idx != r and rows[idx][c] != 0:
                factor = rows[idx][c]
                rows[idx] = [x - factor * y for x, y in zip(rows[idx], rows[r], strict=True)]
        pivot_cols.append(c)
        r += 1
        if r == len(rows):
            break
    return pivot_cols, rows[: len(pivot_cols)]


def nullspace_basis(rows: list[list[Fraction]], ncols: int) -> tuple[list[list[Fraction]], list[int], list[list[Fraction]]]:
    pivots, reduced = rref(rows, ncols)
    pivot_set = set(pivots)
    free_cols = [idx for idx in range(ncols) if idx not in pivot_set]
    basis: list[list[Fraction]] = []
    for free in free_cols:
        vec = [Fraction(0) for _ in range(ncols)]
        vec[free] = Fraction(1)
        for row_idx, pivot_col in enumerate(pivots):
            vec[pivot_col] = -reduced[row_idx][free]
        basis.append(vec)
    return basis, pivots, reduced


def rank_of_rows(rows: list[list[Fraction]], ncols: int) -> int:
    pivots, _ = rref(rows, ncols)
    return len(pivots)


def frac_str(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def matrix_from_vec(vec: list[Fraction], dim: int) -> list[list[Fraction]]:
    return [[vec[row + col * dim] for col in range(dim)] for row in range(dim)]


def sha_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def summarize_table(name: str, table: jax.Array) -> dict[str, Any]:
    dim = int(table.shape[0])
    rows, _ = derivation_rows(table)
    rank = rank_of_rows(rows, dim * dim)
    unit_rows, _ = derivation_rows(table, unit_only=True)
    unit_rank = rank_of_rows(unit_rows, dim * dim)
    imaginary_rows, _ = derivation_rows(table, imaginary_only=True)
    imaginary_rank = rank_of_rows(imaginary_rows, dim * dim)
    return {
        "name": name,
        "algebra_dim": dim,
        "probe_count": len(rows),
        "variable_count": dim * dim,
        "constraint_rank": rank,
        "derivation_dimension": dim * dim - rank,
        "unit_pair_constraint_rank": unit_rank,
        "imaginary_only_probe_count": len(imaginary_rows),
        "imaginary_only_constraint_rank": imaginary_rank,
        "imaginary_only_derivation_dimension": dim * dim - imaginary_rank,
        "structure_constants_sha256": sha_json(jax.device_get(table).tolist()),
    }


def z3_real(value: Fraction | int) -> z3.RatNumRef:
    return z3.RealVal(frac_str(value if isinstance(value, Fraction) else Fraction(value)))


def z3_sum(terms: list[z3.ArithRef]) -> z3.ArithRef:
    return z3.Sum(terms) if terms else z3.RealVal(0)


def z3_leibniz_query(
    *,
    name: str,
    table: jax.Array,
    d_matrix: list[list[Fraction]],
    omit_d_binding: tuple[int, int] | None = None,
) -> dict[str, Any]:
    dim = int(table.shape[0])
    host = jax.device_get(table).tolist()
    solver = z3.Solver()
    t_vars = [[[z3.Real(f"{name}_T_{k}_{i}_{j}") for j in range(dim)] for i in range(dim)] for k in range(dim)]
    d_vars = [[z3.Real(f"{name}_D_{row}_{col}") for col in range(dim)] for row in range(dim)]
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                solver.add(t_vars[k][i][j] == z3_real(Fraction(host[k][i][j])))
    bound_d = 0
    for row in range(dim):
        for col in range(dim):
            if omit_d_binding == (row, col):
                continue
            solver.add(d_vars[row][col] == z3_real(d_matrix[row][col]))
            bound_d += 1

    defects: list[z3.ArithRef] = []
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                left = z3_sum([d_vars[k][m] * t_vars[m][i][j] for m in range(dim)])
                right_a = z3_sum([t_vars[k][m][j] * d_vars[m][i] for m in range(dim)])
                right_b = z3_sum([t_vars[k][i][m] * d_vars[m][j] for m in range(dim)])
                defects.append(left - right_a - right_b)
    solver.add(z3.Or([defect != 0 for defect in defects]))
    status = solver.check()
    return {
        "solver": "z3",
        "status": str(status),
        "verdict": str(status),
        "sat": status == z3.sat,
        "unsat": status == z3.unsat,
        "structure_constants_bound": dim**3,
        "D_entries_bound": bound_d,
        "leibniz_defect_coordinates": len(defects),
        "omitted_D_binding": list(omit_d_binding) if omit_d_binding is not None else None,
    }


def cvc5_real(solver: cvc5.Solver, value: Fraction | int) -> Any:
    return solver.mkReal(frac_str(value if isinstance(value, Fraction) else Fraction(value)))


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_real(solver, 0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_status_text(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_leibniz_query(
    *,
    name: str,
    table: jax.Array,
    d_matrix: list[list[Fraction]],
    omit_d_binding: tuple[int, int] | None = None,
) -> dict[str, Any]:
    dim = int(table.shape[0])
    host = jax.device_get(table).tolist()
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    real_sort = solver.getRealSort()
    zero = cvc5_real(solver, 0)
    t_vars = [
        [[solver.mkConst(real_sort, f"{name}_T_{k}_{i}_{j}") for j in range(dim)] for i in range(dim)]
        for k in range(dim)
    ]
    d_vars = [[solver.mkConst(real_sort, f"{name}_D_{row}_{col}") for col in range(dim)] for row in range(dim)]
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, t_vars[k][i][j], cvc5_real(solver, Fraction(host[k][i][j]))))
    bound_d = 0
    for row in range(dim):
        for col in range(dim):
            if omit_d_binding == (row, col):
                continue
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, d_vars[row][col], cvc5_real(solver, d_matrix[row][col])))
            bound_d += 1

    violations: list[Any] = []
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                left = cvc5_sum(solver, [solver.mkTerm(Kind.MULT, d_vars[k][m], t_vars[m][i][j]) for m in range(dim)])
                right_a = cvc5_sum(solver, [solver.mkTerm(Kind.MULT, t_vars[k][m][j], d_vars[m][i]) for m in range(dim)])
                right_b = cvc5_sum(solver, [solver.mkTerm(Kind.MULT, t_vars[k][i][m], d_vars[m][j]) for m in range(dim)])
                defect = solver.mkTerm(Kind.SUB, left, right_a, right_b)
                violations.append(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, defect, zero)))
    solver.assertFormula(solver.mkTerm(Kind.OR, *violations))
    result = solver.checkSat()
    status = cvc5_status_text(result)
    return {
        "solver": "cvc5",
        "status": status,
        "verdict": status,
        "sat": result.isSat(),
        "unsat": result.isUnsat(),
        "structure_constants_bound": dim**3,
        "D_entries_bound": bound_d,
        "leibniz_defect_coordinates": len(violations),
        "omitted_D_binding": list(omit_d_binding) if omit_d_binding is not None else None,
    }


def prove_generators(table: jax.Array, generators: list[list[list[Fraction]]]) -> tuple[dict[str, Any], dict[str, Any]]:
    z3_rows = []
    cvc5_rows = []
    for idx, matrix in enumerate(generators):
        z3_rows.append(z3_leibniz_query(name=f"g2_gen_{idx}", table=table, d_matrix=matrix))
        cvc5_rows.append(cvc5_leibniz_query(name=f"g2_gen_{idx}", table=table, d_matrix=matrix))
    z3_statuses = [row["status"] for row in z3_rows]
    cvc5_statuses = [row["status"] for row in cvc5_rows]
    return (
        {
            "solver": "z3",
            "status": "unsat" if all(status == "unsat" for status in z3_statuses) else "mixed",
            "verdict": "unsat" if all(status == "unsat" for status in z3_statuses) else "mixed",
            "per_generator": z3_rows,
        },
        {
            "solver": "cvc5",
            "status": "unsat" if all(status == "unsat" for status in cvc5_statuses) else "mixed",
            "verdict": "unsat" if all(status == "unsat" for status in cvc5_statuses) else "mixed",
            "per_generator": cvc5_rows,
        },
    )


def build_result() -> dict[str, Any]:
    tables = build_tables()
    summaries = {name: summarize_table(name, table) for name, table in tables.items()}
    o_rows, _ = derivation_rows(tables["O"])
    basis, pivots, _ = nullspace_basis(o_rows, 64)
    generators = [matrix_from_vec(vec, 8) for vec in basis]
    generator_hash = sha_json([[[frac_str(value) for value in row] for row in matrix] for matrix in generators])

    z3_generators, cvc5_generators = prove_generators(tables["O"], generators)
    identity_control = [[Fraction(1 if row == col else 0) for col in range(8)] for row in range(8)]
    z3_control = z3_leibniz_query(name="g2_nonderivation_identity_control", table=tables["O"], d_matrix=identity_control)
    cvc5_control = cvc5_leibniz_query(name="g2_nonderivation_identity_control", table=tables["O"], d_matrix=identity_control)
    z3_erased = z3_leibniz_query(name="g2_drop_D00_binding_flip", table=tables["O"], d_matrix=generators[0], omit_d_binding=(0, 0))
    cvc5_erased = cvc5_leibniz_query(name="g2_drop_D00_binding_flip", table=tables["O"], d_matrix=generators[0], omit_d_binding=(0, 0))

    dim_ladder = {name: summaries[name]["derivation_dimension"] for name in ("R", "C", "H", "O")}
    expected_ladder = {"R": 0, "C": 0, "H": 3, "O": 14}
    solver_agreement = (
        z3_generators["status"] == cvc5_generators["status"] == "unsat"
        and z3_control["status"] == cvc5_control["status"] == "sat"
        and z3_erased["status"] == cvc5_erased["status"] == "sat"
    )
    all_pass = bool(
        jax.config.jax_enable_x64
        and dim_ladder == expected_ladder
        and len(generators) == 14
        and summaries["O"]["unit_pair_constraint_rank"] == 8
        and summaries["O"]["imaginary_only_derivation_dimension"] == 15
        and solver_agreement
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
        and READS_PEER_RESULT is False
    )

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "runtime_preflight": {
            "sys_executable": sys.executable,
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "versions": {
                "jax": getattr(jax, "__version__", None),
                "z3": getattr(z3, "get_version_string", lambda: None)(),
                "cvc5": getattr(cvc5, "__version__", None),
            },
        },
        "M_probe_family": {
            "id": "basis_pair_derivation_defect_coordinates",
            "observable": "L_k(i,j)=D(e_i e_j)_k-(D(e_i)e_j)_k-(e_iD(e_j))_k",
            "finite_family": {name: summaries[name]["probe_count"] for name in ("R", "C", "H", "O")},
            "indistinguishability_rule": "D1 ~_M D2 iff every Leibniz-defect coordinate agrees on D1-D2",
        },
        "C_constraints": {
            "trace": "finite probe weights are normalized to trace one in the envelope measurement guard",
            "PSD": "squared defect readout is a positive semidefinite Gram norm",
            "Hermiticity": "real coordinate observables are self-adjoint",
            "normalization": "Cayley-Dickson basis has e0 identity and norm-one basis units",
            "rung_specific": "Leibniz derivation condition D(xy)=D(x)y+xD(y) for every ordered basis pair",
        },
        "quotient": {
            "S": "End_R(A), represented by algebra_dim^2 real coefficients",
            "equivalence": "D1 ~_M D2 iff the finite Leibniz-defect probe family vanishes on D1-D2",
            "class_dimensions": dim_ladder,
            "dimension_honesty": "JAX computes a candidate basis for SMT checking; Julia is the authoritative dim=14 nullspace source.",
        },
        "values": summaries,
        "candidate_generators": {
            "source": "exact rational nullspace basis of the computed O Leibniz matrix; used only to bind candidate D entries",
            "generator_count": len(generators),
            "pivot_count": len(pivots),
            "generator_matrix_sha256": generator_hash,
        },
        "smt_structural_proof": {
            "encoding": "z3/cvc5 bind T[k,i,j] and D[k,m] as SMT Reals, expand L_k(i,j) in solver, and assert some defect is nonzero.",
            "asserted_precomputed_kernel_relations": 0,
            "derived_leibniz_defect_count": 14 * summaries["O"]["probe_count"],
            "z3": {
                "all_g2_generators_leibniz_negation": z3_generators,
                "nonderivation_control_has_defect": z3_control,
                "drop_D00_binding_flip": z3_erased,
            },
            "cvc5": {
                "all_g2_generators_leibniz_negation": cvc5_generators,
                "nonderivation_control_has_defect": cvc5_control,
                "drop_D00_binding_flip": cvc5_erased,
            },
            "solver_agreement": solver_agreement,
        },
        "negative_control": {
            "division_algebra_ladder_flip": {"pass": dim_ladder == expected_ladder, "dimensions": dim_ladder},
            "unit_fixing_rank": {"pass": summaries["O"]["unit_pair_constraint_rank"] == 8, "rank": summaries["O"]["unit_pair_constraint_rank"]},
            "imaginary_only_probe_quotient_widens_to_15": {
                "pass": summaries["O"]["imaginary_only_derivation_dimension"] == 15,
                "full_O_derivation_dimension": summaries["O"]["derivation_dimension"],
                "imaginary_only_derivation_dimension": summaries["O"]["imaginary_only_derivation_dimension"],
            },
            "force_commutativity_flip": {
                "pass": summaries["O_commutative_projection_control"]["derivation_dimension"] != summaries["O"]["derivation_dimension"],
                "O_derivation_dimension": summaries["O"]["derivation_dimension"],
                "commutative_projection_derivation_dimension": summaries["O_commutative_projection_control"]["derivation_dimension"],
            },
            "nonderivation_control_flip": {"pass": z3_control["status"] == cvc5_control["status"] == "sat", "z3": z3_control["status"], "cvc5": cvc5_control["status"]},
            "drop_D00_binding_flip": {"pass": z3_erased["status"] == cvc5_erased["status"] == "sat", "z3": z3_erased["status"], "cvc5": cvc5_erased["status"]},
        },
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "fractions", "hashlib", "json", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "supportive x64 Cayley-Dickson table construction"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive finite tensor arithmetic for candidate generation"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing in-solver Leibniz-defect derivation over bound structure constants"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent in-solver Leibniz-defect derivation over the same bindings"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"},
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    dims = result["quotient"]["class_dimensions"]
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dims_R_C_H_O={dims['R']}/{dims['C']}/{dims['H']}/{dims['O']} "
        f"unit_rank={result['negative_control']['unit_fixing_rank']['rank']} "
        f"imaginary_only_dim={result['negative_control']['imaginary_only_probe_quotient_widens_to_15']['imaginary_only_derivation_dimension']} "
        f"z3={result['smt_structural_proof']['z3']['all_g2_generators_leibniz_negation']['status']} "
        f"cvc5={result['smt_structural_proof']['cvc5']['all_g2_generators_leibniz_negation']['status']} "
        f"drop_D00={result['negative_control']['drop_D00_binding_flip']['z3']}/{result['negative_control']['drop_D00_binding_flip']['cvc5']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
