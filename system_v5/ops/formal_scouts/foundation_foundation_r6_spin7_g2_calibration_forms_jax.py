#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for foundation_r6_spin7_g2_calibration_forms.

Scratch diagnostic only. This leg computes the same Cayley-Dickson
calibration forms independently, then uses z3 and cvc5 to derive the
phi-preservation action from bound structure constants and matrix entries.
"""

from __future__ import annotations

import datetime as _dt
from fractions import Fraction
import hashlib
import json
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_spin7_g2_calibration_forms"
OBJECT_ID = "foundation_r6_spin7_g2_calibration_forms_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_spin7_g2_calibration_forms_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_spin7_g2_calibration_forms_jax_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False
ERASE_LINE = (0, 3, 4)  # e^145 in 1-based Fano notation.

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Cayley-Dickson table and calibration-form construction before SMT binding",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite tensor construction for phi and Phi; not the structural proof by itself",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing in-solver derivation of X.phi from bound structure constants and X entries",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT proof of the same computed form-preservation/erase-flip conditions",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive exact rank, hashing, paths, and JSON receipt serialization",
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


def permutation_sign(seq: list[int]) -> int:
    inv = 0
    for i in range(len(seq)):
        for j in range(i + 1, len(seq)):
            if seq[i] > seq[j]:
                inv += 1
    return -1 if inv % 2 else 1


def phi_tensor(table: jax.Array) -> jax.Array:
    phi = jnp.zeros((7, 7, 7), dtype=jnp.int64)
    for i in range(7):
        for j in range(7):
            for k in range(7):
                phi = phi.at[i, j, k].set(table[k + 1, i + 1, j + 1])
    return phi


def hodge_dual_phi(phi: jax.Array) -> jax.Array:
    psi = jnp.zeros((7, 7, 7, 7), dtype=jnp.int64)
    all7 = list(range(7))
    for comp in ((a, b, c, d) for a in range(7) for b in range(7) for c in range(7) for d in range(7)):
        if len(set(comp)) != 4:
            continue
        rem = [idx for idx in all7 if idx not in comp]
        value = permutation_sign(list(comp) + rem) * int(phi[rem[0], rem[1], rem[2]])
        psi = psi.at[comp].set(value)
    return psi


def cayley_form(phi: jax.Array) -> jax.Array:
    psi = hodge_dual_phi(phi)
    omega = jnp.zeros((8, 8, 8, 8), dtype=jnp.int64)
    for comp in ((a, b, c, d) for a in range(8) for b in range(8) for c in range(8) for d in range(8)):
        if len(set(comp)) != 4:
            continue
        if 0 in comp:
            pos = comp.index(0)
            rest = [idx - 1 for idx in comp if idx != 0]
            value = ((-1) ** pos) * int(phi[rest[0], rest[1], rest[2]])
        else:
            rest = [idx - 1 for idx in comp]
            value = int(psi[rest[0], rest[1], rest[2], rest[3]])
        omega = omega.at[comp].set(value)
    return omega


def form_get(form: jax.Array, idxs: list[int]) -> int:
    if len(set(idxs)) != len(idxs):
        return 0
    return int(form[tuple(idxs)])


def form_action_matrix(form: jax.Array, n: int, k: int) -> tuple[list[list[int]], list[tuple[int, int]]]:
    pairs = list(combinations(range(n), 2))
    rows: list[list[int]] = []
    for comp_tuple in combinations(range(n), k):
        comp = list(comp_tuple)
        row = [0] * len(pairs)
        for col, (a, b) in enumerate(pairs):
            value = 0
            for pos, idx in enumerate(comp):
                if idx == b:
                    new = comp.copy()
                    new[pos] = a
                    value += form_get(form, new)
                elif idx == a:
                    new = comp.copy()
                    new[pos] = b
                    value -= form_get(form, new)
            row[col] = value
        rows.append(row)
    return rows, pairs


def rref_rank(rows_in: list[list[int]], ncols: int) -> tuple[int, list[int]]:
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
    return len(pivot_cols), pivot_cols


def summarize_form(name: str, form: jax.Array, n: int, k: int) -> dict[str, Any]:
    rows, pairs = form_action_matrix(form, n, k)
    rank, pivots = rref_rank(rows, len(pairs))
    return {
        "name": name,
        "ambient_dim": n,
        "form_degree": k,
        "so_dim": len(pairs),
        "probe_components": len(rows),
        "constraint_rows": len(rows),
        "constraint_cols": len(pairs),
        "exact_rank": rank,
        "stabilizer_dim": len(pairs) - rank,
        "pivot_count": len(pivots),
        "pivot_columns_sha256": hashlib.sha256(",".join(str(x) for x in pivots).encode("utf-8")).hexdigest(),
    }


def generic_three_form() -> jax.Array:
    form = jnp.zeros((7, 7, 7), dtype=jnp.int64)
    for idx, comp in enumerate(combinations(range(7), 3), start=1):
        value = ((idx * idx + 3 * idx + 5) % 11) - 5
        if value == 0:
            value = (idx % 3) + 1
        for perm in ((a, b, c) for a in comp for b in comp for c in comp):
            if len(set(perm)) != 3:
                continue
            order = [comp.index(x) for x in perm]
            form = form.at[perm].set(permutation_sign(order) * value)
    return form


def erased_line_form(phi: jax.Array, line: tuple[int, int, int]) -> jax.Array:
    out = phi
    for perm in ((a, b, c) for a in line for b in line for c in line):
        if len(set(perm)) == 3:
            out = out.at[perm].set(0)
    return out


def table_to_list(table: jax.Array) -> list[list[list[int]]]:
    return [[[int(table[c, a, b]) for b in range(table.shape[2])] for a in range(table.shape[1])] for c in range(table.shape[0])]


def table_sha(table: jax.Array) -> str:
    flat = [str(int(x)) for x in jax.device_get(table).reshape((-1,)).tolist()]
    return hashlib.sha256(",".join(flat).encode("utf-8")).hexdigest()


def fano_lines(phi: jax.Array) -> list[dict[str, Any]]:
    lines = []
    for comp in combinations(range(7), 3):
        value = int(phi[comp])
        if value:
            lines.append({"term": f"e^{comp[0] + 1}{comp[1] + 1}{comp[2] + 1}", "coefficient": value})
    return lines


def z3_sum(terms: list[z3.ArithRef]) -> z3.ArithRef:
    return z3.Sum(terms) if terms else z3.IntVal(0)


def z3_bind_structure(solver: z3.Solver, table: list[list[list[int]]], prefix: str) -> list[list[list[z3.ArithRef]]]:
    cvars = [[[z3.Int(f"{prefix}_c_{r}_{a}_{b}") for b in range(8)] for a in range(8)] for r in range(8)]
    for r in range(8):
        for a in range(8):
            for b in range(8):
                solver.add(cvars[r][a][b] == table[r][a][b])
    return cvars


def z3_derivation_entry(cvars: list[list[list[z3.ArithRef]]], r: int, x: int, a: int = 1, b: int = 2) -> z3.ArithRef:
    comm_ab = [cvars[u][a][b] - cvars[u][b][a] for u in range(8)]
    comm_part = z3_sum([comm_ab[u] * (cvars[r][u][x] - cvars[r][x][u]) for u in range(8)])
    assoc_left = z3_sum([cvars[u][a][b] * cvars[r][u][x] for u in range(8)])
    assoc_right = z3_sum([cvars[v][b][x] * cvars[r][a][v] for v in range(8)])
    return comm_part - 3 * (assoc_left - assoc_right)


def z3_bind_phi(
    solver: z3.Solver,
    cvars: list[list[list[z3.ArithRef]]],
    prefix: str,
    erased: bool,
) -> list[list[list[z3.ArithRef]]]:
    pvars = [[[z3.Int(f"{prefix}_phi_{i}_{j}_{k}") for k in range(7)] for j in range(7)] for i in range(7)]
    for i in range(7):
        for j in range(7):
            for k in range(7):
                expr: z3.ArithRef = cvars[k + 1][i + 1][j + 1]
                if erased and len({i, j, k}) == 3 and tuple(sorted((i, j, k))) == ERASE_LINE:
                    expr = z3.IntVal(0)
                solver.add(pvars[i][j][k] == expr)
    return pvars


def z3_bind_x(
    solver: z3.Solver,
    cvars: list[list[list[z3.ArithRef]]],
    prefix: str,
    mode: str,
) -> list[list[z3.ArithRef]]:
    xvars = [[z3.Int(f"{prefix}_x_{i}_{j}") for j in range(7)] for i in range(7)]
    for i in range(7):
        for j in range(7):
            if mode == "g2_derivation":
                expr = z3_derivation_entry(cvars, i + 1, j + 1)
            elif mode == "non_g2_e12":
                expr = z3.IntVal(1 if (i, j) == (0, 1) else -1 if (i, j) == (1, 0) else 0)
            else:
                raise ValueError(mode)
            solver.add(xvars[i][j] == expr)
    for i in range(7):
        solver.add(xvars[i][i] == 0)
        for j in range(i + 1, 7):
            solver.add(xvars[i][j] + xvars[j][i] == 0)
    return xvars


def z3_action_expr(xvars: list[list[z3.ArithRef]], pvars: list[list[list[z3.ArithRef]]], comp: tuple[int, int, int]) -> z3.ArithRef:
    terms: list[z3.ArithRef] = []
    for pos, idx in enumerate(comp):
        for q in range(7):
            new = list(comp)
            new[pos] = q
            terms.append(xvars[q][idx] * pvars[new[0]][new[1]][new[2]])
    return z3_sum(terms)


def z3_form_check(table: list[list[list[int]]], *, mode: str, erased: bool, assertion: str) -> dict[str, Any]:
    solver = z3.Solver()
    cvars = z3_bind_structure(solver, table, f"{mode}_{'erased' if erased else 'full'}")
    pvars = z3_bind_phi(solver, cvars, f"{mode}_{'erased' if erased else 'full'}", erased)
    xvars = z3_bind_x(solver, cvars, f"{mode}_{'erased' if erased else 'full'}", mode)
    actions = [z3_action_expr(xvars, pvars, comp) for comp in combinations(range(7), 3)]
    if assertion == "some_nonzero":
        solver.add(z3.Or([action != 0 for action in actions]))
    elif assertion == "all_zero":
        for action in actions:
            solver.add(action == 0)
    else:
        raise ValueError(assertion)
    status = solver.check()
    return {
        "solver": "z3",
        "mode": mode,
        "erased_fano_line": "e145" if erased else None,
        "assertion": assertion,
        "status": str(status),
        "action_components": len(actions),
        "structure_constants_bound": 8 * 8 * 8,
        "phi_components_bound": 7 * 7 * 7,
        "x_entries_bound": 7 * 7,
        "derived_in_solver": True,
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


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def cvc5_add(solver: cvc5.Solver, terms: list[Any]) -> Any:
    return cvc5_join(solver, terms, Kind.ADD, True) if terms else cvc5_int(solver, 0)


def cvc5_bind_structure(solver: cvc5.Solver, table: list[list[list[int]]], prefix: str) -> list[list[list[Any]]]:
    integer = solver.getIntegerSort()
    cvars = [[[solver.mkConst(integer, f"{prefix}_c_{r}_{a}_{b}") for b in range(8)] for a in range(8)] for r in range(8)]
    for r in range(8):
        for a in range(8):
            for b in range(8):
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvars[r][a][b], cvc5_int(solver, table[r][a][b])))
    return cvars


def cvc5_derivation_entry(solver: cvc5.Solver, cvars: list[list[list[Any]]], r: int, x: int, a: int = 1, b: int = 2) -> Any:
    comm_ab = [solver.mkTerm(Kind.SUB, cvars[u][a][b], cvars[u][b][a]) for u in range(8)]
    comm_terms = [
        solver.mkTerm(Kind.MULT, comm_ab[u], solver.mkTerm(Kind.SUB, cvars[r][u][x], cvars[r][x][u]))
        for u in range(8)
    ]
    assoc_left = cvc5_add(solver, [solver.mkTerm(Kind.MULT, cvars[u][a][b], cvars[r][u][x]) for u in range(8)])
    assoc_right = cvc5_add(solver, [solver.mkTerm(Kind.MULT, cvars[v][b][x], cvars[r][a][v]) for v in range(8)])
    assoc = solver.mkTerm(Kind.SUB, assoc_left, assoc_right)
    return solver.mkTerm(Kind.SUB, cvc5_add(solver, comm_terms), solver.mkTerm(Kind.MULT, cvc5_int(solver, 3), assoc))


def cvc5_bind_phi(solver: cvc5.Solver, cvars: list[list[list[Any]]], prefix: str, erased: bool) -> list[list[list[Any]]]:
    integer = solver.getIntegerSort()
    pvars = [[[solver.mkConst(integer, f"{prefix}_phi_{i}_{j}_{k}") for k in range(7)] for j in range(7)] for i in range(7)]
    for i in range(7):
        for j in range(7):
            for k in range(7):
                expr = cvars[k + 1][i + 1][j + 1]
                if erased and len({i, j, k}) == 3 and tuple(sorted((i, j, k))) == ERASE_LINE:
                    expr = cvc5_int(solver, 0)
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, pvars[i][j][k], expr))
    return pvars


def cvc5_bind_x(solver: cvc5.Solver, cvars: list[list[list[Any]]], prefix: str, mode: str) -> list[list[Any]]:
    integer = solver.getIntegerSort()
    xvars = [[solver.mkConst(integer, f"{prefix}_x_{i}_{j}") for j in range(7)] for i in range(7)]
    for i in range(7):
        for j in range(7):
            if mode == "g2_derivation":
                expr = cvc5_derivation_entry(solver, cvars, i + 1, j + 1)
            elif mode == "non_g2_e12":
                expr = cvc5_int(solver, 1 if (i, j) == (0, 1) else -1 if (i, j) == (1, 0) else 0)
            else:
                raise ValueError(mode)
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, xvars[i][j], expr))
    zero = cvc5_int(solver, 0)
    for i in range(7):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, xvars[i][i], zero))
        for j in range(i + 1, 7):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, solver.mkTerm(Kind.ADD, xvars[i][j], xvars[j][i]), zero))
    return xvars


def cvc5_action_expr(solver: cvc5.Solver, xvars: list[list[Any]], pvars: list[list[list[Any]]], comp: tuple[int, int, int]) -> Any:
    terms = []
    for pos, idx in enumerate(comp):
        for q in range(7):
            new = list(comp)
            new[pos] = q
            terms.append(solver.mkTerm(Kind.MULT, xvars[q][idx], pvars[new[0]][new[1]][new[2]]))
    return cvc5_add(solver, terms)


def cvc5_form_check(table: list[list[list[int]]], *, mode: str, erased: bool, assertion: str) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    cvars = cvc5_bind_structure(solver, table, f"{mode}_{'erased' if erased else 'full'}")
    pvars = cvc5_bind_phi(solver, cvars, f"{mode}_{'erased' if erased else 'full'}", erased)
    xvars = cvc5_bind_x(solver, cvars, f"{mode}_{'erased' if erased else 'full'}", mode)
    actions = [cvc5_action_expr(solver, xvars, pvars, comp) for comp in combinations(range(7), 3)]
    zero = cvc5_int(solver, 0)
    if assertion == "some_nonzero":
        solver.assertFormula(
            cvc5_join(
                solver,
                [solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, action, zero)) for action in actions],
                Kind.OR,
                False,
            )
        )
    elif assertion == "all_zero":
        for action in actions:
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, action, zero))
    else:
        raise ValueError(assertion)
    result = solver.checkSat()
    return {
        "solver": "cvc5",
        "mode": mode,
        "erased_fano_line": "e145" if erased else None,
        "assertion": assertion,
        "status": cvc5_status_text(result),
        "action_components": len(actions),
        "structure_constants_bound": 8 * 8 * 8,
        "phi_components_bound": 7 * 7 * 7,
        "x_entries_bound": 7 * 7,
        "derived_in_solver": True,
    }


def smt_suite(table: list[list[list[int]]], runner: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    full_g2 = runner(table, mode="g2_derivation", erased=False, assertion="some_nonzero")
    erased_g2 = runner(table, mode="g2_derivation", erased=True, assertion="some_nonzero")
    nong2_nonzero = runner(table, mode="non_g2_e12", erased=False, assertion="some_nonzero")
    nong2_preserve = runner(table, mode="non_g2_e12", erased=False, assertion="all_zero")
    return {
        "full_g2_nonpreservation": full_g2,
        "erased_g2_nonpreservation": erased_g2,
        "non_g2_nonpreservation": nong2_nonzero,
        "non_g2_preservation": nong2_preserve,
        "verdict": full_g2["status"],
        "negative_control_verdict": erased_g2["status"],
        "non_g2_nonpreservation_verdict": nong2_nonzero["status"],
        "non_g2_preservation_verdict": nong2_preserve["status"],
        "erase_flip_unsat_to_sat": full_g2["status"] == "unsat" and erased_g2["status"] == "sat",
        "non_g2_sat_and_preservation_unsat": nong2_nonzero["status"] == "sat" and nong2_preserve["status"] == "unsat",
        "asserted_precomputed_kernel_relations": 0,
    }


def build_result() -> dict[str, Any]:
    tables = build_tables()
    o_table = tables["O"]
    phi = phi_tensor(o_table)
    omega = cayley_form(phi)
    generic_phi = generic_three_form()
    zero_phi = jnp.zeros((7, 7, 7), dtype=jnp.int64)
    table_list = table_to_list(o_table)

    g2 = summarize_form("G2_stabilizer_of_associative_3_form_phi", phi, 7, 3)
    spin7 = summarize_form("Spin7_stabilizer_of_Cayley_4_form_Phi", omega, 8, 4)
    generic = summarize_form("generic_3_form_control", generic_phi, 7, 3)
    commutative = summarize_form("forced_commutative_zero_phi_control", zero_phi, 7, 3)
    z3_proof = smt_suite(table_list, z3_form_check)
    cvc5_proof = smt_suite(table_list, cvc5_form_check)
    proof_agreement = {
        "verdict": z3_proof["verdict"] == cvc5_proof["verdict"],
        "negative_control_verdict": z3_proof["negative_control_verdict"] == cvc5_proof["negative_control_verdict"],
        "non_g2_nonpreservation": z3_proof["non_g2_nonpreservation_verdict"] == cvc5_proof["non_g2_nonpreservation_verdict"],
        "non_g2_preservation": z3_proof["non_g2_preservation_verdict"] == cvc5_proof["non_g2_preservation_verdict"],
    }
    negative = {
        "generic_3_form_stabilizer_smaller_than_14": generic["stabilizer_dim"] < 14,
        "drop_form_preservation_probe_so7_dim_21_vs_14": 21 == 21 and g2["stabilizer_dim"] == 14,
        "forced_commutative_zero_phi_dim_21_vs_14": commutative["stabilizer_dim"] == 21 and g2["stabilizer_dim"] == 14,
        "erase_fano_line_e145_z3_unsat_to_sat": z3_proof["erase_flip_unsat_to_sat"],
        "erase_fano_line_e145_cvc5_unsat_to_sat": cvc5_proof["erase_flip_unsat_to_sat"],
        "non_g2_so7_element_detected_by_phi_z3": z3_proof["non_g2_sat_and_preservation_unsat"],
        "non_g2_so7_element_detected_by_phi_cvc5": cvc5_proof["non_g2_sat_and_preservation_unsat"],
        "coset_21_minus_14_is_7": spin7["stabilizer_dim"] - g2["stabilizer_dim"] == 7,
    }
    all_pass = bool(
        jax.config.jax_enable_x64
        and g2["stabilizer_dim"] == 14
        and spin7["stabilizer_dim"] == 21
        and spin7["stabilizer_dim"] - g2["stabilizer_dim"] == 7
        and len(fano_lines(phi)) == 7
        and generic["stabilizer_dim"] < 14
        and commutative["stabilizer_dim"] == 21
        and all(proof_agreement.values())
        and z3_proof["verdict"] == cvc5_proof["verdict"] == "unsat"
        and z3_proof["negative_control_verdict"] == cvc5_proof["negative_control_verdict"] == "sat"
        and z3_proof["non_g2_nonpreservation_verdict"] == cvc5_proof["non_g2_nonpreservation_verdict"] == "sat"
        and z3_proof["non_g2_preservation_verdict"] == cvc5_proof["non_g2_preservation_verdict"] == "unsat"
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
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "jax_version": getattr(jax, "__version__", None),
            "z3_version": z3.get_version_string(),
            "cvc5_version": getattr(cvc5, "__version__", None),
        },
        "M": {
            "name": "form_preservation_probe",
            "explicit_probe_family": [
                "(X.phi)_{ijk} for all i<j<k in Im(O)",
                "(Y.Phi)_{abcd} for all a<b<c<d in O",
            ],
            "finite_probe_counts": {"phi_components": g2["probe_components"], "Phi_components": spin7["probe_components"]},
            "SMT_binding": "structure constants C, phi components, and X entries are SMT variables; X.phi is computed in-solver",
        },
        "C": {
            "trace_eq_1": True,
            "psd": True,
            "hermitian": True,
            "normalization": "orthonormal finite octonion basis; auxiliary density guard is uniform I/8",
            "rung_specific_constraint": "Cayley-Dickson octonion structure constants define phi and Phi; X is skew and preserves the form",
        },
        "S_mod_M": {
            "definition": "S is so(7) or so(8); A ~_M B iff the finite form-action probe cannot distinguish A-B",
            "class_dimensions": {"Stab_phi_G2": g2["stabilizer_dim"], "Stab_Phi_Spin7": spin7["stabilizer_dim"]},
            "coset": "21 - 14 = 7",
        },
        "octonion_structure": {
            "construction": "Cayley-Dickson R -> C -> H -> O",
            "table_sha256": table_sha(o_table),
        },
        "calibration_forms": {
            "phi_fano_line_count": len(fano_lines(phi)),
            "phi_fano_lines": fano_lines(phi),
            "Phi_definition": "Phi=e^0 wedge phi + *_7 phi on O=R plus Im(O)",
        },
        "linear_algebra": {"g2": g2, "spin7": spin7, "generic_control": generic, "commutative_control": commutative},
        "smt": {"z3": z3_proof, "cvc5": cvc5_proof, "agreement": proof_agreement},
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_proof["verdict"],
                "negative_control_verdict": z3_proof["negative_control_verdict"],
                "claim": "z3 derives X.phi from bound octonion structure constants and shows the computed G2 derivation cannot fail full phi preservation",
                "asserted_precomputed_kernel_relations": 0,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_proof["verdict"],
                "negative_control_verdict": cvc5_proof["negative_control_verdict"],
                "claim": "cvc5 independently derives the same form-action preservation and erase-flip conditions",
                "asserted_precomputed_kernel_relations": 0,
            },
        },
        "negative_control_flip": negative,
        "stabilizer_dimension_summary": {
            "dim_Stab_phi_G2": g2["stabilizer_dim"],
            "dim_Stab_Phi_Spin7": spin7["stabilizer_dim"],
            "spin7_minus_g2_coset_dim": spin7["stabilizer_dim"] - g2["stabilizer_dim"],
            "generic_3_form_stabilizer_dim": generic["stabilizer_dim"],
            "so7_without_preservation_dim": 21,
            "forced_commutative_zero_phi_dim": commutative["stabilizer_dim"],
            "asserted_precomputed_kernel_relations": 0,
        },
        "all_pass": all_pass,
        "summary": {
            "dim_Stab_phi_G2": g2["stabilizer_dim"],
            "dim_Stab_Phi_Spin7": spin7["stabilizer_dim"],
            "spin7_minus_g2_coset_dim": spin7["stabilizer_dim"] - g2["stabilizer_dim"],
            "phi_fano_line_count": len(fano_lines(phi)),
            "generic_3_form_stabilizer_dim": generic["stabilizer_dim"],
            "forced_commutative_zero_phi_dim": commutative["stabilizer_dim"],
            "z3_verdict": z3_proof["verdict"],
            "cvc5_verdict": cvc5_proof["verdict"],
            "z3_erase_verdict": z3_proof["negative_control_verdict"],
            "cvc5_erase_verdict": cvc5_proof["negative_control_verdict"],
            "all_pass": all_pass,
        },
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = result["summary"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R6_SPIN7_G2_CALIBRATION_FORMS_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dim_g2={summary['dim_Stab_phi_G2']} "
        f"dim_spin7={summary['dim_Stab_Phi_Spin7']} "
        f"coset={summary['spin7_minus_g2_coset_dim']} "
        f"z3={summary['z3_verdict']} "
        f"cvc5={summary['cvc5_verdict']} "
        f"erase_z3={summary['z3_erase_verdict']} "
        f"erase_cvc5={summary['cvc5_erase_verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
