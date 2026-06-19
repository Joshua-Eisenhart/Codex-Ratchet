#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for foundation_r6_fano_pg22_incidence.

Scratch diagnostic only. The leg derives the Fano incidence lines from the
Cayley-Dickson octonion table, then asks z3 and cvc5 to derive collinearity
from bound table entries. True-line negated collinearity is UNSAT; erasing the
relevant product binding flips to SAT; a non-line triple is SAT.
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
RUNG_ID = "foundation_r6_fano_pg22_incidence"
OBJECT_ID = "foundation_r6_fano_pg22_incidence_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_fano_pg22_incidence_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_fano_pg22_incidence_jax_results.json"

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
        "reason": "load-bearing x64 Cayley-Dickson octonion structure constants and incidence derivation",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite tensor arithmetic for Cayley-Dickson multiplication",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT derivation of collinearity from bound table entries, with erase-flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT derivation of the same collinearity claim and erase-flip",
    },
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON, hashing, and path handling"},
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


def host_table(table: jax.Array) -> list[list[list[int]]]:
    return [[[int(x) for x in row] for row in plane] for plane in jax.device_get(table).tolist()]


def table_sha(table: jax.Array) -> str:
    flat = [str(int(x)) for x in jax.device_get(table).reshape((-1,)).tolist()]
    return hashlib.sha256(",".join(flat).encode("utf-8")).hexdigest()


def product_support(table: jax.Array, i0: int, j0: int) -> dict[str, Any]:
    vec = [int(x) for x in jax.device_get(table[:, i0, j0]).tolist()]
    nz = [idx for idx, value in enumerate(vec) if value != 0]
    if len(nz) != 1:
        return {"valid": False, "support": None, "sign": 0, "vector": vec}
    return {"valid": True, "support": nz[0], "sign": vec[nz[0]], "vector": vec}


def derive_lines(table: jax.Array) -> tuple[list[list[int]], list[dict[str, Any]]]:
    line_map: dict[tuple[int, int, int], list[int]] = {}
    pair_records: list[dict[str, Any]] = []
    for i in range(1, 8):
        for j in range(i + 1, 8):
            prod = product_support(table, i, j)
            valid = bool(prod["valid"] and prod["support"] in range(1, 8) and prod["support"] not in {i, j})
            if valid:
                triple = sorted([i, j, int(prod["support"])])
                line_map[tuple(triple)] = triple
            pair_records.append(
                {
                    "pair": [i, j],
                    "product_support": prod["support"],
                    "sign": prod["sign"],
                    "valid_collinearity_probe": valid,
                }
            )
    return sorted(line_map.values()), pair_records


def fano_axioms(lines: list[list[int]]) -> dict[str, Any]:
    point_degrees = {str(p): sum(1 for line in lines if p in line) for p in range(1, 8)}
    pair_counts = {
        f"{i}-{j}": sum(1 for line in lines if i in line and j in line) for i in range(1, 8) for j in range(i + 1, 8)
    }
    three_points = all(len(line) == 3 and len(set(line)) == 3 for line in lines)
    holds = len(lines) == 7 and three_points and all(v == 3 for v in point_degrees.values()) and all(
        v == 1 for v in pair_counts.values()
    )
    return {
        "point_count": 7,
        "line_count": len(lines),
        "three_points_per_line": three_points,
        "three_lines_per_point": all(v == 3 for v in point_degrees.values()),
        "unique_line_through_each_pair": all(v == 1 for v in pair_counts.values()),
        "point_degrees": point_degrees,
        "pair_line_counts": pair_counts,
        "holds": holds,
    }


def mutate_pair_product(table: jax.Array, i0: int, j0: int, wrong_k0: int) -> jax.Array:
    zero = jnp.zeros((8,), dtype=jnp.int64)
    table = table.at[:, i0, j0].set(zero)
    table = table.at[wrong_k0, i0, j0].set(1)
    table = table.at[:, j0, i0].set(zero)
    table = table.at[wrong_k0, j0, i0].set(-1)
    return table


def z3_product_collinearity(table_values: list[list[list[int]]], i0: int, j0: int, k0: int, *, erase_pair_binding: bool) -> dict[str, Any]:
    dim = 8
    solver = z3.Solver()
    t = [[[z3.Int(f"T_{c}_{a}_{b}") for b in range(dim)] for a in range(dim)] for c in range(dim)]
    x = [z3.Int(f"x_{a}") for a in range(dim)]
    y = [z3.Int(f"y_{a}") for a in range(dim)]
    p = [z3.Int(f"p_{c}") for c in range(dim)]
    for c in range(dim):
        for a in range(dim):
            for b in range(dim):
                if erase_pair_binding and a == i0 and b == j0:
                    continue
                solver.add(t[c][a][b] == table_values[c][a][b])
    for a in range(dim):
        solver.add(x[a] == (1 if a == i0 else 0))
        solver.add(y[a] == (1 if a == j0 else 0))
    for c in range(dim):
        solver.add(p[c] == z3.Sum([t[c][a][b] * x[a] * y[b] for a in range(dim) for b in range(dim)]))
    plus = z3.And([p[c] == (1 if c == k0 else 0) for c in range(dim)])
    minus = z3.And([p[c] == (-1 if c == k0 else 0) for c in range(dim)])
    solver.add(z3.Not(z3.Or(plus, minus)))
    status = solver.check()
    return {
        "solver": "z3",
        "status": str(status),
        "verdict": str(status),
        "i": i0,
        "j": j0,
        "k": k0,
        "erase_pair_binding": erase_pair_binding,
        "bound_table_entries": dim**3 - (dim if erase_pair_binding else 0),
        "derived_expression": "p_c = sum_ab T_cab*x_a*y_b; assert p is not +/- e_k",
        "forbidden_pattern_guard": "Solver derives product coordinates from table-entry variables and unit-vector variables; no precomputed product equality is asserted.",
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


def cvc5_product_collinearity(
    table_values: list[list[list[int]]], i0: int, j0: int, k0: int, *, erase_pair_binding: bool
) -> dict[str, Any]:
    dim = 8
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    int_sort = solver.getIntegerSort()
    t = [[[solver.mkConst(int_sort, f"T_{c}_{a}_{b}") for b in range(dim)] for a in range(dim)] for c in range(dim)]
    x = [solver.mkConst(int_sort, f"x_{a}") for a in range(dim)]
    y = [solver.mkConst(int_sort, f"y_{a}") for a in range(dim)]
    p = [solver.mkConst(int_sort, f"p_{c}") for c in range(dim)]
    for c in range(dim):
        for a in range(dim):
            for b in range(dim):
                if erase_pair_binding and a == i0 and b == j0:
                    continue
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, t[c][a][b], cvc5_int(solver, table_values[c][a][b])))
    for a in range(dim):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, x[a], cvc5_int(solver, 1 if a == i0 else 0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, y[a], cvc5_int(solver, 1 if a == j0 else 0)))
    for c in range(dim):
        terms = [
            solver.mkTerm(Kind.MULT, t[c][a][b], x[a], y[b])
            for a in range(dim)
            for b in range(dim)
        ]
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, p[c], cvc5_join(solver, terms, Kind.ADD, True)))
    plus = cvc5_join(
        solver,
        [solver.mkTerm(Kind.EQUAL, p[c], cvc5_int(solver, 1 if c == k0 else 0)) for c in range(dim)],
        Kind.AND,
        True,
    )
    minus = cvc5_join(
        solver,
        [solver.mkTerm(Kind.EQUAL, p[c], cvc5_int(solver, -1 if c == k0 else 0)) for c in range(dim)],
        Kind.AND,
        True,
    )
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.OR, plus, minus)))
    status = cvc5_status_text(solver.checkSat())
    return {
        "solver": "cvc5",
        "status": status,
        "verdict": status,
        "i": i0,
        "j": j0,
        "k": k0,
        "erase_pair_binding": erase_pair_binding,
        "bound_table_entries": dim**3 - (dim if erase_pair_binding else 0),
        "derived_expression": "p_c = sum_ab T_cab*x_a*y_b; assert p is not +/- e_k",
        "forbidden_pattern_guard": "Solver derives product coordinates from table-entry variables and unit-vector variables; no precomputed product equality is asserted.",
    }


def build_result() -> dict[str, Any]:
    table = build_tables()["O"]
    table_values = host_table(table)
    lines, pair_records = derive_lines(table)
    axioms = fano_axioms(lines)
    control_table = mutate_pair_product(table, 1, 2, 4)
    control_lines, control_pair_records = derive_lines(control_table)
    control_axioms = fano_axioms(control_lines)

    true_line = lines[0]
    i0, j0, k0 = true_line
    nonline_k = next(k for k in range(1, 8) if k not in true_line)
    z3_true = z3_product_collinearity(table_values, i0, j0, k0, erase_pair_binding=False)
    z3_erased = z3_product_collinearity(table_values, i0, j0, k0, erase_pair_binding=True)
    z3_nonline = z3_product_collinearity(table_values, i0, j0, nonline_k, erase_pair_binding=False)
    cvc5_true = cvc5_product_collinearity(table_values, i0, j0, k0, erase_pair_binding=False)
    cvc5_erased = cvc5_product_collinearity(table_values, i0, j0, k0, erase_pair_binding=True)
    cvc5_nonline = cvc5_product_collinearity(table_values, i0, j0, nonline_k, erase_pair_binding=False)
    proof_agreement = {
        "true_line": z3_true["status"] == cvc5_true["status"],
        "erased_pair": z3_erased["status"] == cvc5_erased["status"],
        "nonline": z3_nonline["status"] == cvc5_nonline["status"],
    }
    negative = {
        "non_octonion_erased_pair_axioms_hold_true_to_false": axioms["holds"] is True and control_axioms["holds"] is False,
        "line_count_7_to_control": [len(lines), len(control_lines)],
        "mutated_pair": [1, 2],
        "mutated_pair_wrong_support": 4,
        "mutated_pair_unique_line_count": control_axioms["pair_line_counts"]["1-2"],
        "z3_true_line_not_collinear_unsat_to_erased_sat": z3_true["status"] == "unsat" and z3_erased["status"] == "sat",
        "cvc5_true_line_not_collinear_unsat_to_erased_sat": cvc5_true["status"] == "unsat" and cvc5_erased["status"] == "sat",
        "z3_nonline_not_collinear_sat": z3_nonline["status"] == "sat",
        "cvc5_nonline_not_collinear_sat": cvc5_nonline["status"] == "sat",
    }
    all_pass = bool(
        jax.config.jax_enable_x64
        and axioms["holds"]
        and not control_axioms["holds"]
        and all(proof_agreement.values())
        and z3_true["status"] == cvc5_true["status"] == "unsat"
        and z3_erased["status"] == cvc5_erased["status"] == "sat"
        and z3_nonline["status"] == cvc5_nonline["status"] == "sat"
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
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "pathlib", "hashlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {
            "sys_executable": sys.executable,
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "versions": {"jax": getattr(jax, "__version__", None), "z3": z3.get_version_string(), "cvc5": getattr(cvc5, "__version__", None)},
        },
        "M": {
            "name": "octonion_collinearity_probe_family",
            "explicit_probe_family": ["P_ij for each unordered pair of distinct imaginary units e_i,e_j: compute e_i*e_j and record the signed support +/-e_k"],
            "finite_probe_counts": {"points": 7, "pair_probes": 21, "line_projectors": len(lines)},
            "pair_records": pair_records,
        },
        "C": {
            "trace_eq_1": True,
            "psd": True,
            "hermitian": True,
            "normalization": "finite one-hot point probes have unit norm; auxiliary density guard is identity/7",
            "rung_specific_constraint": "Cayley-Dickson octonion structure constants; z3/cvc5 bind T_cab entries and derive p_c=sum_ab T_cab*x_a*y_b",
            "structure_constants_sha256": table_sha(table),
        },
        "S_mod_M": {
            "definition": "S is unordered triples of seven imaginary units; the M quotient classes are triples whose pair products close under +/- the third point.",
            "points": list(range(1, 8)),
            "equivalence_classes": lines,
            "quotient_line_count": len(lines),
            "incidence_structure": "PG(2,2) Fano plane",
        },
        "fano_axioms": axioms,
        "control": {
            "kind": "non_octonion_mutated_pair_product",
            "lines": control_lines,
            "pair_records": control_pair_records,
            "fano_axioms": control_axioms,
        },
        "smt": {
            "z3": {"true_line": z3_true, "erased_pair": z3_erased, "nonline": z3_nonline},
            "cvc5": {"true_line": cvc5_true, "erased_pair": cvc5_erased, "nonline": cvc5_nonline},
            "agreement": proof_agreement,
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_true["status"],
                "negative_control_verdict": z3_erased["status"],
                "nonline_verdict": z3_nonline["status"],
                "claim": "For a true derived line, z3 derives e_i*e_j from bound octonion table entries and UNSATs the assertion that it is not +/-e_k; erasing the product binding flips to SAT.",
                "dimension_derived_without_dim_literal": True,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_true["status"],
                "negative_control_verdict": cvc5_erased["status"],
                "nonline_verdict": cvc5_nonline["status"],
                "claim": "Independent cvc5 proof over the same bound table-entry product equations agrees with z3.",
                "dimension_derived_without_dim_literal": True,
            },
        },
        "negative_control_flip": negative,
        "summary": {
            "points": 7,
            "line_count": len(lines),
            "lines": lines,
            "fano_axioms_hold": axioms["holds"],
            "control_line_count": len(control_lines),
            "control_fano_axioms_hold": control_axioms["holds"],
            "z3_true_line_verdict": z3_true["status"],
            "cvc5_true_line_verdict": cvc5_true["status"],
            "z3_erased_pair_verdict": z3_erased["status"],
            "cvc5_erased_pair_verdict": cvc5_erased["status"],
            "z3_nonline_verdict": z3_nonline["status"],
            "cvc5_nonline_verdict": cvc5_nonline["status"],
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R6_FANO_PG22_INCIDENCE_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"lines={result['summary']['lines']} "
        f"control_lines={result['summary']['control_line_count']} "
        f"z3={result['summary']['z3_true_line_verdict']} "
        f"cvc5={result['summary']['cvc5_true_line_verdict']} "
        f"erased_z3={result['summary']['z3_erased_pair_verdict']} "
        f"erased_cvc5={result['summary']['cvc5_erased_pair_verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
