#!/usr/bin/env python3
"""JAX + z3/cvc5 structural leg for foundation_r6_oph_icosahedral_screen.

Scratch diagnostic only. OPH/holography is only the horizon-frame label here;
this leg computes the finite A5/icosahedral screen action and controls.
"""

from __future__ import annotations

import datetime as _dt
import itertools
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
import jax.numpy as jnp
import z3
from cvc5 import Kind


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_oph_icosahedral_screen"
OBJECT_ID = "foundation_foundation_r6_oph_icosahedral_screen_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_oph_icosahedral_screen_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_oph_icosahedral_screen_jax_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 finite incidence tensors and orbit diagnostics"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive exact-integer screen adjacency and degree reductions"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing in-solver group-order, transitivity, and normal-subgroup derivations from bound permutation/action tables"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent in-solver derivation of the same finite structural facts"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"}


def parity(p: tuple[int, ...]) -> int:
    return sum(1 for i in range(len(p)) for j in range(i + 1, len(p)) if p[i] > p[j]) % 2


def compose(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(p[i] for i in q)


def invert(p: tuple[int, ...]) -> tuple[int, ...]:
    out = [0] * len(p)
    for i, value in enumerate(p):
        out[value] = i
    return tuple(out)


def generated_subgroup(generators: list[tuple[int, ...]], n: int) -> set[tuple[int, ...]]:
    identity = tuple(range(n))
    known = set([identity, *generators])
    changed = True
    while changed:
        changed = False
        snapshot = list(known)
        for a in snapshot:
            for b in snapshot:
                c = compose(a, b)
                if c not in known:
                    known.add(c)
                    changed = True
    return known


def a5_group() -> list[tuple[int, ...]]:
    return sorted(p for p in itertools.permutations(range(5)) if parity(p) == 0)


def coset_action_model() -> dict[str, Any]:
    group = a5_group()
    index = {g: i for i, g in enumerate(group)}
    h = sorted(generated_subgroup([(1, 2, 3, 4, 0)], 5))
    cosets: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    for g in group:
        key = tuple(sorted(index[compose(g, h0)] for h0 in h))
        if key not in seen:
            seen.add(key)
            cosets.append(key)
    vertex_index = {c: i for i, c in enumerate(cosets)}

    def act(g: tuple[int, ...], vertex: int) -> int:
        key = tuple(sorted(index[compose(g, group[element_idx])] for element_idx in cosets[vertex]))
        return vertex_index[key]

    action = [[act(g, vertex) for vertex in range(len(cosets))] for g in group]
    h_orbits: list[list[int]] = []
    unseen_vertices = set(range(len(cosets)))
    while unseen_vertices:
        start = min(unseen_vertices)
        orbit = sorted({action[index[h0]][start] for h0 in h})
        h_orbits.append(orbit)
        unseen_vertices -= set(orbit)
    base_neighbors = next(orbit for orbit in h_orbits if 0 not in orbit and len(orbit) == 5)
    edges: set[tuple[int, int]] = set()
    for gi in range(len(group)):
        u = action[gi][0]
        for nb in base_neighbors:
            v = action[gi][nb]
            edges.add(tuple(sorted((u, v))))
    faces = [
        (i, j, k)
        for i in range(len(cosets))
        for j in range(i + 1, len(cosets))
        for k in range(j + 1, len(cosets))
        if tuple(sorted((i, j))) in edges and tuple(sorted((i, k))) in edges and tuple(sorted((j, k))) in edges
    ]
    mul = [[index[compose(a, b)] for b in group] for a in group]
    inv = [index[invert(g)] for g in group]
    return {
        "group": group,
        "h": h,
        "cosets": cosets,
        "action": action,
        "h_orbits": h_orbits,
        "edges": sorted(edges),
        "faces": faces,
        "mul": mul,
        "inv": inv,
        "identity": index[tuple(range(5))],
    }


def octahedral_group() -> dict[str, Any]:
    vertices = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    vertex_index = {v: i for i, v in enumerate(vertices)}
    perms: list[tuple[int, ...]] = []
    for axes in itertools.permutations(range(3)):
        for signs in itertools.product([-1, 1], repeat=3):
            det_perm = -1 if parity(axes) else 1
            if det_perm * signs[0] * signs[1] * signs[2] != 1:
                continue
            image = []
            for v in vertices:
                out = [0, 0, 0]
                for row, axis in enumerate(axes):
                    out[row] = signs[row] * v[axis]
                image.append(vertex_index[tuple(out)])
            perms.append(tuple(image))
    group = sorted(set(perms))
    index = {g: i for i, g in enumerate(group)}
    mul = [[index[compose(a, b)] for b in group] for a in group]
    inv = [index[invert(g)] for g in group]
    edges = [tuple(sorted((i, j))) for i in range(6) for j in range(i + 1, 6) if vertices[i] != tuple(-x for x in vertices[j])]
    return {"group": group, "mul": mul, "inv": inv, "identity": index[tuple(range(6))], "vertices": 6, "edges": sorted(edges), "faces": 8}


def z3_normal_subgroup_status(mul: list[list[int]], inv: list[int], identity: int, require_normal: bool = True) -> str:
    n = len(mul)
    m = [z3.Bool(f"n_{n}_{i}_{require_normal}") for i in range(n)]
    solver = z3.Solver()
    solver.set(timeout=20_000)
    solver.add(m[identity])
    for i in range(n):
        solver.add(z3.Implies(m[i], m[inv[i]]))
    for i in range(n):
        for j in range(n):
            solver.add(z3.Implies(z3.And(m[i], m[j]), m[mul[i][j]]))
    if require_normal:
        for g in range(n):
            ginvg = inv[g]
            for x in range(n):
                solver.add(z3.Implies(m[x], m[mul[mul[g][x]][ginvg]]))
    solver.add(z3.Or([m[i] for i in range(n) if i != identity]))
    solver.add(z3.Or([z3.Not(m[i]) for i in range(n)]))
    return str(solver.check())


def z3_distinct_permutation_status(perms: list[tuple[int, ...]], tag: str) -> str:
    solver = z3.Solver()
    solver.set(timeout=20_000)
    bound = [[z3.Int(f"{tag}_p_{i}_{j}") for j in range(len(perms[0]))] for i in range(len(perms))]
    for i, perm in enumerate(perms):
        for j, value in enumerate(perm):
            solver.add(bound[i][j] == value)
    duplicate_terms = [
        z3.And([bound[i][k] == bound[j][k] for k in range(len(perms[0]))])
        for i in range(len(perms))
        for j in range(i + 1, len(perms))
    ]
    solver.add(z3.Or(duplicate_terms))
    return str(solver.check())


def z3_transitivity_status(action: list[list[int]], vertex_count: int, tag: str) -> str:
    solver = z3.Solver()
    solver.set(timeout=20_000)
    images = [z3.Int(f"{tag}_base_image_{i}") for i in range(len(action))]
    for i, row in enumerate(action):
        solver.add(images[i] == row[0])
    missing_target_terms = [z3.And([img != target for img in images]) for target in range(vertex_count)]
    solver.add(z3.Or(missing_target_terms))
    return str(solver.check())


def cvc5_bool_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(False)
    return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.OR, *terms)


def cvc5_bool_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(True)
    return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.AND, *terms)


def cvc5_not(solver: cvc5.Solver, term: Any) -> Any:
    return solver.mkTerm(Kind.NOT, term)


def cvc5_eq(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.EQUAL, left, right)


def cvc5_neq(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return cvc5_not(solver, cvc5_eq(solver, left, right))


def cvc5_normal_subgroup_status(mul: list[list[int]], inv: list[int], identity: int, require_normal: bool = True) -> str:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    n = len(mul)
    m = [solver.mkConst(bool_sort, f"n_{n}_{i}_{require_normal}") for i in range(n)]
    solver.assertFormula(m[identity])
    for i in range(n):
        solver.assertFormula(solver.mkTerm(Kind.IMPLIES, m[i], m[inv[i]]))
    for i in range(n):
        for j in range(n):
            solver.assertFormula(solver.mkTerm(Kind.IMPLIES, cvc5_bool_and(solver, [m[i], m[j]]), m[mul[i][j]]))
    if require_normal:
        for g in range(n):
            ginvg = inv[g]
            for x in range(n):
                solver.assertFormula(solver.mkTerm(Kind.IMPLIES, m[x], m[mul[mul[g][x]][ginvg]]))
    solver.assertFormula(cvc5_bool_or(solver, [m[i] for i in range(n) if i != identity]))
    solver.assertFormula(cvc5_bool_or(solver, [cvc5_not(solver, m[i]) for i in range(n)]))
    return str(solver.checkSat())


def cvc5_distinct_permutation_status(perms: list[tuple[int, ...]], tag: str) -> str:
    solver = cvc5.Solver()
    int_sort = solver.getIntegerSort()
    bound = [[solver.mkConst(int_sort, f"{tag}_p_{i}_{j}") for j in range(len(perms[0]))] for i in range(len(perms))]
    for i, perm in enumerate(perms):
        for j, value in enumerate(perm):
            solver.assertFormula(cvc5_eq(solver, bound[i][j], solver.mkInteger(value)))
    duplicate_terms = [
        cvc5_bool_and(solver, [cvc5_eq(solver, bound[i][k], bound[j][k]) for k in range(len(perms[0]))])
        for i in range(len(perms))
        for j in range(i + 1, len(perms))
    ]
    solver.assertFormula(cvc5_bool_or(solver, duplicate_terms))
    return str(solver.checkSat())


def cvc5_transitivity_status(action: list[list[int]], vertex_count: int, tag: str) -> str:
    solver = cvc5.Solver()
    int_sort = solver.getIntegerSort()
    images = [solver.mkConst(int_sort, f"{tag}_base_image_{i}") for i in range(len(action))]
    for i, row in enumerate(action):
        solver.assertFormula(cvc5_eq(solver, images[i], solver.mkInteger(row[0])))
    missing_target_terms = [
        cvc5_bool_and(solver, [cvc5_neq(solver, img, solver.mkInteger(target)) for img in images])
        for target in range(vertex_count)
    ]
    solver.assertFormula(cvc5_bool_or(solver, missing_target_terms))
    return str(solver.checkSat())


def smt_report(a5: dict[str, Any], octa: dict[str, Any]) -> dict[str, Any]:
    a5_perms = [tuple(row) for row in a5["action"]]
    octa_perms = octa["group"]
    z3_main = {
        "a5_distinct_60_permutation_duplicate_exists": z3_distinct_permutation_status(a5_perms, "a5"),
        "a5_missing_vertex_orbit_target_exists": z3_transitivity_status(a5["action"], len(a5["cosets"]), "a5"),
        "a5_proper_nontrivial_normal_subgroup_exists": z3_normal_subgroup_status(a5["mul"], a5["inv"], a5["identity"], True),
        "a5_drop_normality_constraint_proper_nontrivial_subgroup_exists": z3_normal_subgroup_status(a5["mul"], a5["inv"], a5["identity"], False),
        "octahedral_proper_nontrivial_normal_subgroup_exists": z3_normal_subgroup_status(octa["mul"], octa["inv"], octa["identity"], True),
        "octahedral_distinct_24_permutation_duplicate_exists": z3_distinct_permutation_status(octa_perms, "oct"),
    }
    cvc5_main = {
        "a5_distinct_60_permutation_duplicate_exists": cvc5_distinct_permutation_status(a5_perms, "a5"),
        "a5_missing_vertex_orbit_target_exists": cvc5_transitivity_status(a5["action"], len(a5["cosets"]), "a5"),
        "a5_proper_nontrivial_normal_subgroup_exists": cvc5_normal_subgroup_status(a5["mul"], a5["inv"], a5["identity"], True),
        "a5_drop_normality_constraint_proper_nontrivial_subgroup_exists": cvc5_normal_subgroup_status(a5["mul"], a5["inv"], a5["identity"], False),
        "octahedral_proper_nontrivial_normal_subgroup_exists": cvc5_normal_subgroup_status(octa["mul"], octa["inv"], octa["identity"], True),
        "octahedral_distinct_24_permutation_duplicate_exists": cvc5_distinct_permutation_status(octa_perms, "oct"),
    }
    return {
        "scope": "Finite A5 screen action only: order, vertex transitivity, and absence of nontrivial proper normal subgroup derived over bound permutation/action/multiplication tables.",
        "forbidden_pattern_guard": "The solvers receive bound permutation entries and multiplication tables, then derive duplicate/orbit/normal-subgroup witnesses; no precomputed count or boolean theorem is asserted as the theorem.",
        "z3": {
            "version": z3.get_version_string(),
            "verdict": z3_main["a5_proper_nontrivial_normal_subgroup_exists"],
            "checks": z3_main,
            "pass": (
                z3_main["a5_distinct_60_permutation_duplicate_exists"] == "unsat"
                and z3_main["a5_missing_vertex_orbit_target_exists"] == "unsat"
                and z3_main["a5_proper_nontrivial_normal_subgroup_exists"] == "unsat"
                and z3_main["a5_drop_normality_constraint_proper_nontrivial_subgroup_exists"] == "sat"
                and z3_main["octahedral_proper_nontrivial_normal_subgroup_exists"] == "sat"
                and z3_main["octahedral_distinct_24_permutation_duplicate_exists"] == "unsat"
            ),
        },
        "cvc5": {
            "version": getattr(cvc5, "__version__", "unknown"),
            "verdict": cvc5_main["a5_proper_nontrivial_normal_subgroup_exists"],
            "checks": cvc5_main,
            "pass": (
                cvc5_main["a5_distinct_60_permutation_duplicate_exists"] == "unsat"
                and cvc5_main["a5_missing_vertex_orbit_target_exists"] == "unsat"
                and cvc5_main["a5_proper_nontrivial_normal_subgroup_exists"] == "unsat"
                and cvc5_main["a5_drop_normality_constraint_proper_nontrivial_subgroup_exists"] == "sat"
                and cvc5_main["octahedral_proper_nontrivial_normal_subgroup_exists"] == "sat"
                and cvc5_main["octahedral_distinct_24_permutation_duplicate_exists"] == "unsat"
            ),
        },
    }


def build_result() -> dict[str, Any]:
    a5 = coset_action_model()
    octa = octahedral_group()
    adjacency = jnp.zeros((12, 12), dtype=jnp.int64)
    for i, j in a5["edges"]:
        adjacency = adjacency.at[i, j].set(1)
        adjacency = adjacency.at[j, i].set(1)
    degrees = jnp.sum(adjacency, axis=1)
    smt = smt_report(a5, octa)
    values = {
        "A5_order": len(a5["group"]),
        "vertex_count": len(a5["cosets"]),
        "edge_count": len(a5["edges"]),
        "face_count": len(a5["faces"]),
        "euler": len(a5["cosets"]) - len(a5["edges"]) + len(a5["faces"]),
        "stabilizer_order": len(a5["group"]) // len(a5["cosets"]),
        "class_count": 1,
        "degree_min": int(jax.device_get(jnp.min(degrees))),
        "degree_max": int(jax.device_get(jnp.max(degrees))),
    }
    negative = {
        "drop_action_probe_coarsens_quotient": sorted(len(orbit) for orbit in a5["h_orbits"]) != [12],
        "drop_action_probe_orbit_sizes": sorted(len(orbit) for orbit in a5["h_orbits"]),
        "erase_normality_z3_unsat_to_sat": smt["z3"]["checks"]["a5_proper_nontrivial_normal_subgroup_exists"] == "unsat"
        and smt["z3"]["checks"]["a5_drop_normality_constraint_proper_nontrivial_subgroup_exists"] == "sat",
        "erase_normality_cvc5_unsat_to_sat": smt["cvc5"]["checks"]["a5_proper_nontrivial_normal_subgroup_exists"] == "unsat"
        and smt["cvc5"]["checks"]["a5_drop_normality_constraint_proper_nontrivial_subgroup_exists"] == "sat",
        "octahedral_control_normal_subgroup_sat": smt["z3"]["checks"]["octahedral_proper_nontrivial_normal_subgroup_exists"] == "sat"
        and smt["cvc5"]["checks"]["octahedral_proper_nontrivial_normal_subgroup_exists"] == "sat",
        "octahedral_control_order_differs": len(octa["group"]) != len(a5["group"]),
    }
    all_pass = bool(
        values["A5_order"] == 60
        and values["vertex_count"] == 12
        and values["edge_count"] == 30
        and values["face_count"] == 20
        and values["euler"] == 2
        and values["stabilizer_order"] == 5
        and values["degree_min"] == values["degree_max"] == 5
        and smt["z3"]["pass"]
        and smt["cvc5"]["pass"]
        and smt["z3"]["verdict"] == smt["cvc5"]["verdict"] == "unsat"
        and all(v for v in negative.values() if isinstance(v, bool))
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
        "python_executable": sys.executable,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "itertools", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["jax", "jax.numpy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "M": {
            "name": "A5_action_probe",
            "explicit_probe_family": ["A5 permutation action on 12 C5-cosets", "base-neighbor orbit incidence probe", "normal-subgroup closure probe"],
            "finite_probe_domain": {"group_elements": 60, "vertices": 12, "edges": 30},
        },
        "C": {
            "trace_equals_one": "handled by Julia QuantumOptics screen projectors; JAX leg carries finite action/incidence constraints",
            "psd": "handled by Julia QuantumOptics screen projectors",
            "hermiticity": "handled by Julia QuantumOptics screen projectors",
            "normalization": "permutation action rows are total maps on the finite 12-port screen",
            "rung_specific_constraint": "A5 action is order-60, vertex-transitive, simple, and preserves icosahedral incidence",
        },
        "S_mod_M": {
            "definition": "v ~_M w iff A5 action probes place v and w in the same orbit",
            "orbit_structure": [list(range(12))],
            "class_count": 1,
            "drop_action_probe_orbit_sizes": negative["drop_action_probe_orbit_sizes"],
        },
        "summary": values,
        "smt": smt,
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": smt["z3"]["verdict"],
                "claim": "No nontrivial proper normal subgroup exists for the bound A5 multiplication table; duplicate and missing-orbit witnesses are also unsat.",
                "erase_flip_verdict": smt["z3"]["checks"]["a5_drop_normality_constraint_proper_nontrivial_subgroup_exists"],
                "octahedral_control_verdict": smt["z3"]["checks"]["octahedral_proper_nontrivial_normal_subgroup_exists"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": smt["cvc5"]["verdict"],
                "claim": "Independent cvc5 check of the same bound finite structural proof.",
                "erase_flip_verdict": smt["cvc5"]["checks"]["a5_drop_normality_constraint_proper_nontrivial_subgroup_exists"],
                "octahedral_control_verdict": smt["cvc5"]["checks"]["octahedral_proper_nontrivial_normal_subgroup_exists"],
            },
        },
        "octahedral_control": {"group_order": len(octa["group"]), "vertices": octa["vertices"], "edges": len(octa["edges"]), "faces": octa["faces"]},
        "negative_control_flip": negative,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_R6_OPH_ICOSAHEDRAL_SCREEN_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"erase_z3={result['crossover_proofs']['z3']['erase_flip_verdict']} "
        f"erase_cvc5={result['crossover_proofs']['cvc5']['erase_flip_verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
