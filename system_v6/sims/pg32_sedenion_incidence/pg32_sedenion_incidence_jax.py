#!/usr/bin/env python3
"""JAX/z3/cvc5 leg for sedenion-derived PG(3,2) incidence."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "pg32_sedenion_incidence"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = SIM_DIR / "results" / f"{SIM_ID}_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

OCTONION_TRIPLES = (
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.int64)[idx]


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate([jnp.ones((1,), dtype=jnp.int64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.int64)])
    return x * signs


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("kij,i,j->k", table, x, y)


def octonion_table() -> jax.Array:
    table = jnp.zeros((8, 8, 8), dtype=jnp.int64)
    table = table.at[0, 0, 0].set(1)
    for i in range(1, 8):
        table = table.at[i, 0, i].set(1)
        table = table.at[i, i, 0].set(1)
        table = table.at[0, i, i].set(-1)
    for a, b, c in OCTONION_TRIPLES:
        for x, y, z, sign in (
            (a, b, c, 1),
            (b, c, a, 1),
            (c, a, b, 1),
            (b, a, c, -1),
            (c, b, a, -1),
            (a, c, b, -1),
        ):
            table = table.at[z, x, y].set(sign)
    return table


def cd_double(parent: jax.Array) -> jax.Array:
    n = int(parent.shape[0])
    dim = 2 * n
    table = jnp.zeros((dim, dim, dim), dtype=jnp.int64)
    eye = jnp.eye(dim, dtype=jnp.int64)
    for i in range(dim):
        for j in range(dim):
            x = eye[i]
            y = eye[j]
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
            second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
            table = table.at[:, i, j].set(jnp.concatenate([first, second]))
    return table


def sedenion_table() -> jax.Array:
    return cd_double(octonion_table())


def vector_terms(v: jax.Array) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, coeff in enumerate(jax.device_get(v).astype(int).tolist()):
        if coeff:
            out.append({"basis_index": idx, "label": f"e{idx}", "coefficient": int(coeff)})
    return out


def normsq(v: jax.Array) -> int:
    return int(jax.device_get(jnp.sum(v * v)))


def product_index_and_sign(table: jax.Array, a: int, b: int) -> tuple[int, int]:
    prod = multiply(table, basis(int(table.shape[0]), a), basis(int(table.shape[0]), b))
    terms = vector_terms(prod)
    if len(terms) != 1:
        raise ValueError(f"basis product e{a}*e{b} has {len(terms)} terms")
    return int(terms[0]["basis_index"]), int(terms[0]["coefficient"])


def extract_lines(table: jax.Array, points: range) -> tuple[list[tuple[int, int, int]], dict[tuple[int, int], tuple[int, int, int]]]:
    lines = set()
    pair_to_line: dict[tuple[int, int], tuple[int, int, int]] = {}
    for a, b in combinations(points, 2):
        k, sign = product_index_and_sign(table, a, b)
        if k not in points or abs(sign) != 1:
            continue
        line = tuple(sorted((a, b, k)))
        lines.add(line)
        pair_to_line[(a, b)] = line
    return sorted(lines), pair_to_line


def pair_axiom(lines: list[tuple[int, int, int]], points: range) -> dict[str, Any]:
    counts: dict[str, int] = {}
    bad: list[dict[str, Any]] = []
    for a, b in combinations(points, 2):
        count = sum(1 for line in lines if a in line and b in line)
        counts[f"{a}-{b}"] = count
        if count != 1:
            bad.append({"pair": [a, b], "line_count": count})
    return {
        "pair_count": len(counts),
        "all_pairs_exactly_one_line": not bad,
        "violations": bad,
        "counts_by_pair": counts,
    }


def planes_from_pair_map(pair_to_line: dict[tuple[int, int], tuple[int, int, int]], points: range) -> list[tuple[int, ...]]:
    planes: list[tuple[int, ...]] = []
    for subset in combinations(points, 7):
        subset_set = set(subset)
        if all(set(pair_to_line[tuple(sorted((a, b)))]) <= subset_set for a, b in combinations(subset, 2)):
            planes.append(subset)
    return planes


def assoc(table: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> jax.Array:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def is_zero(v: jax.Array) -> bool:
    return normsq(v) == 0


def alternative_witness(table: jax.Array, plane: tuple[int, ...]) -> dict[str, Any] | None:
    vecs = [basis(16, 0)] + [basis(16, p) for p in plane]
    labels = [0, *plane]
    for ix, x in enumerate(vecs):
        for iy, y in enumerate(vecs):
            for iz, z in enumerate(vecs):
                left_alt = assoc(table, x, y, z) + assoc(table, y, x, z)
                right_alt = assoc(table, x, y, z) + assoc(table, x, z, y)
                if not is_zero(left_alt):
                    return {
                        "kind": "left_linearized_alternativity_failure",
                        "x": labels[ix],
                        "y": labels[iy],
                        "z": labels[iz],
                        "associator_xyz": vector_terms(assoc(table, x, y, z)),
                        "associator_yxz": vector_terms(assoc(table, y, x, z)),
                        "sum_terms": vector_terms(left_alt),
                    }
                if not is_zero(right_alt):
                    return {
                        "kind": "right_linearized_alternativity_failure",
                        "x": labels[ix],
                        "y": labels[iy],
                        "z": labels[iz],
                        "associator_xyz": vector_terms(assoc(table, x, y, z)),
                        "associator_xzy": vector_terms(assoc(table, x, z, y)),
                        "sum_terms": vector_terms(right_alt),
                    }
    return None


def plane_classification(table: jax.Array, lines: list[tuple[int, int, int]], pair_to_line: dict[tuple[int, int], tuple[int, int, int]]) -> dict[str, Any]:
    planes = planes_from_pair_map(pair_to_line, range(1, 16))
    records: list[dict[str, Any]] = []
    for plane in planes:
        plane_set = set(plane)
        plane_lines = [line for line in lines if set(line) <= plane_set]
        closed = all(set(pair_to_line[tuple(sorted((a, b)))]) <= plane_set for a, b in combinations(plane, 2))
        witness = alternative_witness(table, plane)
        genuine = closed and witness is None
        records.append(
            {
                "plane": list(plane),
                "line_count_inside": len(plane_lines),
                "closed": closed,
                "alternative": witness is None,
                "classification": "genuine_octonion_subalgebra" if genuine else "closed_non_alternative_sedenion_plane",
                "witness": witness,
            }
        )
    return {
        "plane_count": len(records),
        "genuine_octonion_count": sum(1 for row in records if row["classification"] == "genuine_octonion_subalgebra"),
        "non_alternative_count": sum(1 for row in records if row["classification"] != "genuine_octonion_subalgebra"),
        "records": records,
    }


def two_term(dim: int, a: int, b: int) -> jax.Array:
    out = jnp.zeros((dim,), dtype=jnp.int64)
    return out.at[a].set(1).at[b].set(1)


def support_geometry(
    ab: tuple[int, int],
    cd: tuple[int, int],
    pair_to_line: dict[tuple[int, int], tuple[int, int, int]],
    planes: list[tuple[int, ...]],
) -> dict[str, Any]:
    support = set((*ab, *cd))
    containing_planes = [list(plane) for plane in planes if support <= set(plane)]
    return {
        "left_pair": list(ab),
        "right_pair": list(cd),
        "left_line": list(pair_to_line[tuple(sorted(ab))]),
        "right_line": list(pair_to_line[tuple(sorted(cd))]),
        "support_points": sorted(support),
        "containing_planes": containing_planes,
    }


def zero_divisors(table: jax.Array, pair_to_line: dict[tuple[int, int], tuple[int, int, int]], planes: list[tuple[int, ...]]) -> dict[str, Any]:
    pairs = list(combinations(range(1, 16), 2))
    zero_pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    examples: list[dict[str, Any]] = []
    adjacency: dict[tuple[int, int], set[tuple[int, int]]] = {pair: set() for pair in pairs}
    for ab in pairs:
        x = two_term(16, *ab)
        for cd in pairs:
            y = two_term(16, *cd)
            prod = multiply(table, x, y)
            if is_zero(prod):
                zero_pairs.append((ab, cd))
                adjacency[ab].add(cd)
                adjacency[cd].add(ab)
                if len(examples) < 12:
                    geom = support_geometry(ab, cd, pair_to_line, planes)
                    geom["product_terms"] = vector_terms(prod)
                    examples.append(geom)
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for node in pairs:
        if node in seen:
            continue
        stack = [node]
        seen.add(node)
        comp: list[tuple[int, int]] = []
        while stack:
            item = stack.pop()
            comp.append(item)
            for nxt in adjacency[item]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        if len(comp) > 1:
            components.append(sorted(comp))
    return {
        "candidate_pair_nodes": len(pairs),
        "ordered_zero_divisor_pair_count": len(zero_pairs),
        "undirected_zero_divisor_edge_count": len({tuple(sorted((ab, cd))) for ab, cd in zero_pairs}),
        "component_count": len(components),
        "component_sizes": sorted(len(comp) for comp in components),
        "components": [[list(pair) for pair in comp] for comp in components],
        "examples": examples,
    }


def octonion_control(table: jax.Array) -> dict[str, Any]:
    lines, pair_to_line = extract_lines(table, range(1, 8))
    pairs = list(combinations(range(1, 8), 2))
    zero_count = 0
    for ab in pairs:
        x = two_term(8, *ab)
        for cd in pairs:
            y = two_term(8, *cd)
            zero_count += int(is_zero(multiply(table, x, y)))
    return {
        "line_count": len(lines),
        "lines": [list(line) for line in lines],
        "pair_axiom": pair_axiom(lines, range(1, 8)),
        "ordered_zero_divisor_pair_count": zero_count,
        "all_pass": len(lines) == 7 and pair_axiom(lines, range(1, 8))["all_pairs_exactly_one_line"] and zero_count == 0,
    }


def signed_entry_scramble_control(table: jax.Array) -> dict[str, Any]:
    scrambled = table
    prod_12 = multiply(table, basis(16, 1), basis(16, 2))
    prod_14 = multiply(table, basis(16, 1), basis(16, 4))
    scrambled = scrambled.at[:, 1, 2].set(prod_14)
    scrambled = scrambled.at[:, 2, 1].set(-prod_14)
    scrambled = scrambled.at[:, 1, 4].set(prod_12)
    scrambled = scrambled.at[:, 4, 1].set(-prod_12)
    lines, _ = extract_lines(scrambled, range(1, 16))
    axiom = pair_axiom(lines, range(1, 16))
    sign_flip = table.at[:, 1, 2].set(-prod_12).at[:, 2, 1].set(prod_12)
    sign_lines, _ = extract_lines(sign_flip, range(1, 16))
    return {
        "control_note": "Pure in-place sign flips preserve e_i e_j = +/- e_k incidence; the breaking control scrambles signed product entries across pair slots.",
        "pure_sign_flip_line_count": len(sign_lines),
        "pure_sign_flip_pair_axiom_ok": pair_axiom(sign_lines, range(1, 16))["all_pairs_exactly_one_line"],
        "signed_entry_scramble_line_count": len(lines),
        "signed_entry_scramble_pair_axiom_ok": axiom["all_pairs_exactly_one_line"],
        "first_pair_violations": axiom["violations"][:8],
        "breaks": len(lines) != 35 or not axiom["all_pairs_exactly_one_line"],
    }


def host_table(table: jax.Array) -> list[list[list[int]]]:
    return jax.device_get(table).astype(int).tolist()


def z3_line_claim(table: jax.Array, a: int, b: int, c: int, *, assert_line: bool) -> dict[str, Any]:
    host = host_table(table)
    solver = z3.Solver()
    coeffs = [z3.Int(f"C_{k}_{a}_{b}_{c}_{int(assert_line)}") for k in range(16)]
    for k, var in enumerate(coeffs):
        solver.add(var == host[k][a][b])
    line_expr = z3.And(coeffs[c] * coeffs[c] == 1, *[coeffs[k] == 0 for k in range(16) if k != c])
    solver.add(line_expr if assert_line else z3.Not(line_expr))
    status = solver.check()
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "bound_entry": f"C[*][{a}][{b}]",
        "target": c,
        "asserted": "line_closure" if assert_line else "not_line_closure",
        "verdict": str(status),
    }


def z3_zero_product(table: jax.Array, left_pair: tuple[int, int], right_pair: tuple[int, int]) -> dict[str, Any]:
    host = host_table(table)
    solver = z3.Solver()
    left = [z3.Int(f"L_{i}") for i in range(16)]
    right = [z3.Int(f"R_{i}") for i in range(16)]
    for idx, var in enumerate(left):
        solver.add(var == (1 if idx in left_pair else 0))
    for idx, var in enumerate(right):
        solver.add(var == (1 if idx in right_pair else 0))
    for k in range(16):
        terms = [host[k][i][j] * left[i] * right[j] for i in range(16) for j in range(16) if host[k][i][j]]
        solver.add(sum(terms, z3.IntVal(0)) == 0)
    status = solver.check()
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "product_derived_in_solver": True,
        "left_pair": list(left_pair),
        "right_pair": list(right_pair),
        "verdict": str(status),
    }


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkInteger(0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_mul(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.MULT, *terms)


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_line_claim(table: jax.Array, a: int, b: int, c: int, *, assert_line: bool) -> dict[str, Any]:
    host = host_table(table)
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    coeffs = [solver.mkConst(int_sort, f"C_{k}_{a}_{b}_{c}_{int(assert_line)}") for k in range(16)]
    for k, var in enumerate(coeffs):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(host[k][a][b])))
    target_sq = cvc5_mul(solver, [coeffs[c], coeffs[c]])
    pieces = [solver.mkTerm(Kind.EQUAL, target_sq, solver.mkInteger(1))]
    pieces.extend(solver.mkTerm(Kind.EQUAL, coeffs[k], solver.mkInteger(0)) for k in range(16) if k != c)
    line_expr = solver.mkTerm(Kind.AND, *pieces)
    solver.assertFormula(line_expr if assert_line else solver.mkTerm(Kind.NOT, line_expr))
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "bound_entry": f"C[*][{a}][{b}]",
        "target": c,
        "asserted": "line_closure" if assert_line else "not_line_closure",
        "verdict": cvc5_status(solver.checkSat()),
    }


def cvc5_zero_product(table: jax.Array, left_pair: tuple[int, int], right_pair: tuple[int, int]) -> dict[str, Any]:
    host = host_table(table)
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    int_sort = solver.getIntegerSort()
    left = [solver.mkConst(int_sort, f"L_{i}") for i in range(16)]
    right = [solver.mkConst(int_sort, f"R_{i}") for i in range(16)]
    for idx, var in enumerate(left):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(1 if idx in left_pair else 0)))
    for idx, var in enumerate(right):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(1 if idx in right_pair else 0)))
    for k in range(16):
        terms = [
            cvc5_mul(solver, [solver.mkInteger(host[k][i][j]), left[i], right[j]])
            for i in range(16)
            for j in range(16)
            if host[k][i][j]
        ]
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvc5_sum(solver, terms), solver.mkInteger(0)))
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "product_derived_in_solver": True,
        "left_pair": list(left_pair),
        "right_pair": list(right_pair),
        "verdict": cvc5_status(solver.checkSat()),
    }


def smt_suite(table: jax.Array, zero_example: tuple[tuple[int, int], tuple[int, int]]) -> dict[str, Any]:
    claimed_line = (1, 2, product_index_and_sign(table, 1, 2)[0])
    claimed_non_line = (1, 2, 4)
    z3_claimed_sat = z3_line_claim(table, *claimed_line, assert_line=True)
    z3_claimed_unsat_flip = z3_line_claim(table, *claimed_line, assert_line=False)
    z3_nonline_unsat = z3_line_claim(table, *claimed_non_line, assert_line=True)
    z3_nonline_sat_flip = z3_line_claim(table, *claimed_non_line, assert_line=False)
    cvc5_claimed_sat = cvc5_line_claim(table, *claimed_line, assert_line=True)
    cvc5_claimed_unsat_flip = cvc5_line_claim(table, *claimed_line, assert_line=False)
    cvc5_nonline_unsat = cvc5_line_claim(table, *claimed_non_line, assert_line=True)
    cvc5_nonline_sat_flip = cvc5_line_claim(table, *claimed_non_line, assert_line=False)
    return {
        "claimed_line": list(claimed_line),
        "claimed_non_line": list(claimed_non_line),
        "z3": {
            "claimed_line_sat": z3_claimed_sat,
            "claimed_line_negation_unsat": z3_claimed_unsat_flip,
            "claimed_non_line_unsat": z3_nonline_unsat,
            "claimed_non_line_negation_sat": z3_nonline_sat_flip,
            "zero_product": z3_zero_product(table, *zero_example),
        },
        "cvc5": {
            "claimed_line_sat": cvc5_claimed_sat,
            "claimed_line_negation_unsat": cvc5_claimed_unsat_flip,
            "claimed_non_line_unsat": cvc5_nonline_unsat,
            "claimed_non_line_negation_sat": cvc5_nonline_sat_flip,
            "zero_product": cvc5_zero_product(table, *zero_example),
        },
    }


def main() -> int:
    s_table = sedenion_table()
    o_table = octonion_table()
    lines, pair_to_line = extract_lines(s_table, range(1, 16))
    axiom = pair_axiom(lines, range(1, 16))
    planes = planes_from_pair_map(pair_to_line, range(1, 16))
    plane_summary = plane_classification(s_table, lines, pair_to_line)
    zd = zero_divisors(s_table, pair_to_line, planes)
    first_zero = (tuple(zd["examples"][0]["left_pair"]), tuple(zd["examples"][0]["right_pair"]))
    smt = smt_suite(s_table, first_zero)
    control_oct = octonion_control(o_table)
    control_scramble = signed_entry_scramble_control(s_table)
    shared_scalars = {
        "line_count": len(lines),
        "pair_axiom_ok": int(axiom["all_pairs_exactly_one_line"]),
        "plane_count": plane_summary["plane_count"],
        "genuine_octonion_plane_count": plane_summary["genuine_octonion_count"],
        "non_alternative_plane_count": plane_summary["non_alternative_count"],
        "ordered_zero_divisor_pair_count": zd["ordered_zero_divisor_pair_count"],
        "zero_divisor_component_count": zd["component_count"],
        "octonion_line_count": control_oct["line_count"],
        "octonion_zero_divisor_pair_count": control_oct["ordered_zero_divisor_pair_count"],
        "scrambled_breaks_pair_axiom": int(control_scramble["breaks"]),
    }
    all_pass = (
        len(lines) == 35
        and axiom["all_pairs_exactly_one_line"]
        and plane_summary["plane_count"] == 15
        and plane_summary["genuine_octonion_count"] == 8
        and plane_summary["non_alternative_count"] == 7
        and zd["ordered_zero_divisor_pair_count"] == 84
        and zd["component_count"] == 7
        and control_oct["all_pass"]
        and control_scramble["breaks"]
        and smt["z3"]["claimed_line_sat"]["verdict"] == "sat"
        and smt["z3"]["claimed_line_negation_unsat"]["verdict"] == "unsat"
        and smt["z3"]["claimed_non_line_unsat"]["verdict"] == "unsat"
        and smt["z3"]["claimed_non_line_negation_sat"]["verdict"] == "sat"
        and smt["z3"]["zero_product"]["verdict"] == "sat"
        and smt["cvc5"]["claimed_line_sat"]["verdict"] == "sat"
        and smt["cvc5"]["claimed_line_negation_unsat"]["verdict"] == "unsat"
        and smt["cvc5"]["claimed_non_line_unsat"]["verdict"] == "unsat"
        and smt["cvc5"]["claimed_non_line_negation_sat"]["verdict"] == "sat"
        and smt["cvc5"]["zero_product"]["verdict"] == "sat"
    )
    payload = {
        "schema_version": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_jax",
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "sys_executable": sys.executable,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["jax", "jax.numpy", "z3", "cvc5"],
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "JAX int64 tensor recomputation of Cayley-Dickson products and incidence scans"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing SMT line/non-line and zero-product derivations from bound structure constants"},
            "cvc5": {"tried": True, "used": True, "reason": "independent load-bearing SMT mirror for the same finite structure-constant obligations"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"},
        "construction": {
            "octonion_source": "canonical oriented octonion table",
            "octonion_triples": [list(row) for row in OCTONION_TRIPLES],
            "sedenion_rule": "(a,b)(c,d)=(ac-conj(d)b, da+b conj(c))",
            "line_extraction": "all triples {i,j,k} with e_i e_j = +/- e_k, derived from table products",
        },
        "incidence": {"points": list(range(1, 16)), "line_count": len(lines), "lines": [list(line) for line in lines], "pair_axiom": axiom},
        "planes": plane_summary,
        "zero_divisors": zd,
        "controls": {"octonion_restriction": control_oct, "signed_entry_scramble": control_scramble},
        "smt": smt,
        "shared_scalars": shared_scalars,
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(all_pass).lower()} "
        f"lines={len(lines)} pair_axiom={axiom['all_pairs_exactly_one_line']} "
        f"planes={plane_summary['genuine_octonion_count']}/{plane_summary['non_alternative_count']} "
        f"zero_pairs={zd['ordered_zero_divisor_pair_count']} components={zd['component_count']} "
        f"z3_line_flip={smt['z3']['claimed_line_negation_unsat']['verdict']} "
        f"cvc5_nonline={smt['cvc5']['claimed_non_line_unsat']['verdict']}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
