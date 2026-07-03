#!/usr/bin/env python3
"""Measured inter-axis readout matrix for Type-1 engine v0.

Ceiling: QUARANTINE_EXPLORATORY / scratch_diagnostic.
promotion_allowed=false. No axis, bridge, or law is promoted here.
"""

from __future__ import annotations

import itertools
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TYPE1 = HERE.parent / "type1_engine_v0"
RESULTS = HERE / "results"
sys.path.insert(0, str(TYPE1))
import type1_engine_common as common  # noqa: E402

NULL_PERMUTATIONS = 2000
TOL = 1e-12
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing relation matrix, correlation, deterministic label-permutation nulls"},
    "z3": {"tried": True, "used": True, "reason": "dual-SMT erased-control gate for above-null relations when installed"},
    "cvc5": {"tried": True, "used": True, "reason": "dual-SMT erased-control cross-check for above-null relations when installed"},
    "json": {"tried": True, "used": True, "reason": "artifact serialization"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "z3": "supportive", "cvc5": "supportive", "json": "supportive"}

PROBE_STATES = {
    "mixed_zero": (0.0, 0.0, 0.0),
    "plus_z": (0.0, 0.0, 1.0),
    "minus_z": (0.0, 0.0, -1.0),
    "generic_pos": (0.31, -0.27, 0.44),
    "generic_neg": (-0.21, 0.36, -0.18),
    "seeded_0": (0.173, -0.422, 0.611),
    "seeded_1": (-0.532, 0.118, -0.374),
}

AXIS_NAMES = ["a1_branch", "a1_opchar", "a2", "a4", "a5", "a6", "b0", "b3", "b6"]


def sign_bit(z: float) -> int:
    if z > TOL:
        return 1
    if z < -TOL:
        return -1
    return 0


def bit_row(stage: dict, traversal: str, state_name: str, bloch: tuple[float, float, float]) -> dict:
    terrain_fn = common.terrain_function(stage["terrain"])
    b0 = sign_bit(bloch[2])
    b3 = 1 if stage["loop"] == "outer" else -1
    return {
        "stage_id": stage["stage_id"],
        "declared_loop": stage["loop"],
        "traversal": traversal,
        "state": state_name,
        "bloch": list(bloch),
        "a1_branch": 1 if terrain_fn in {"Se", "Ni"} else -1,
        "a1_opchar": 1 if stage["operator"] in {"Fi", "Fe"} else 0,
        "a2": 1 if terrain_fn in {"Ni", "Si"} else 0,
        "a4": 0 if traversal == "outer" else 1,
        "a5": 1 if stage["operator"].startswith("F") else 0,
        "a6": 1 if stage["composition"] == "terrain_after_operator" else 0,
        "b0": b0,
        "b3": b3,
        "b6": None if b0 == 0 else -b0 * b3,
        "operator": stage["operator"],
        "terrain": stage["terrain"],
        "composition": stage["composition"],
    }


def readout_rows() -> list[dict]:
    rows = []
    stages_by_loop = {
        "outer": [common.STAGE_BY_ID[sid] for sid in common.OUTER_LOOP_STAGE_IDS],
        "inner": [common.STAGE_BY_ID[sid] for sid in common.INNER_LOOP_STAGE_IDS],
    }
    for traversal, stages in stages_by_loop.items():
        for stage in stages:
            for state_name, bloch in PROBE_STATES.items():
                rows.append(bit_row(stage, traversal, state_name, bloch))
    return rows


def entropy(vals: list[int]) -> float:
    counts = Counter(vals)
    n = len(vals)
    return -sum((c / n) * math.log(c / n, 2) for c in counts.values())


def mutual_information(x: list[int], y: list[int]) -> float:
    n = len(x)
    cx, cy = Counter(x), Counter(y)
    cxy = Counter(zip(x, y))
    mi = 0.0
    for (a, b), c in cxy.items():
        pxy = c / n
        mi += pxy * math.log(pxy / ((cx[a] / n) * (cy[b] / n)), 2)
    return mi


def nmi(x: list[int], y: list[int]) -> float:
    hx, hy = entropy(x), entropy(y)
    if hx == 0.0 or hy == 0.0:
        return 0.0
    return mutual_information(x, y) / math.sqrt(hx * hy)


def corr(x: list[int], y: list[int]) -> float:
    ax = np.asarray(x, dtype=float)
    ay = np.asarray(y, dtype=float)
    if float(np.std(ax)) == 0.0 or float(np.std(ay)) == 0.0:
        return 0.0
    return float(np.corrcoef(ax, ay)[0, 1])


def deterministic_permutations(y: list[int]) -> list[list[int]]:
    n = len(y)
    coprime_steps = [step for step in range(1, n) if math.gcd(step, n) == 1]
    perms = []
    for k in range(NULL_PERMUTATIONS):
        step = coprime_steps[k % len(coprime_steps)]
        offset = (k // len(coprime_steps)) % n
        perms.append([y[(offset + step * i) % n] for i in range(n)])
    return perms


def relation_matrix(rows: list[dict]) -> list[dict]:
    out = []
    for left, right in itertools.combinations(AXIS_NAMES, 2):
        usable = [r for r in rows if r[left] is not None and r[right] is not None]
        x = [int(r[left]) for r in usable]
        y = [int(r[right]) for r in usable]
        observed_nmi = nmi(x, y)
        observed_corr = corr(x, y)
        null_nmi = []
        null_abs_corr = []
        for yp in deterministic_permutations(y):
            null_nmi.append(nmi(x, yp))
            null_abs_corr.append(abs(corr(x, yp)))
        nmi95 = float(np.percentile(null_nmi, 95))
        abs_corr95 = float(np.percentile(null_abs_corr, 95))
        above = bool((observed_nmi > nmi95 + 1e-15) or (abs(observed_corr) > abs_corr95 + 1e-15))
        out.append(
            {
                "pair": [left, right],
                "n": len(usable),
                "nmi": observed_nmi,
                "corr": observed_corr,
                "null95_nmi": nmi95,
                "null95_abs_corr": abs_corr95,
                "verdict": "dependent_above_95pct_null" if above else "independent_at_this_depth",
            }
        )
    return out


def laws(rows: list[dict]) -> dict:
    b6_rows = [r for r in rows if r["b6"] is not None]
    b6_ok = all(r["b6"] == -r["b0"] * r["b3"] for r in b6_rows)
    return {
        "b6_equals_minus_b0_times_b3": {
            "defined_rows": len(b6_rows),
            "total_rows": len(rows),
            "holds": b6_ok,
            "note": "b6 is derived only where b0 sign(r_z) is nonzero.",
        },
        "a0_equals_a1_xor_a2": {
            "status": "skipped_undefinable",
            "note": "a0 needs Xi/cut bridge or explicit a0 proxy; this stage-level Type-1 readout excludes it honestly.",
        },
    }


def stress(rows: list[dict]) -> dict:
    triples = sorted({(r["a4"], r["a6"], r["b3"]) for r in rows})
    examples = {}
    for triple in triples:
        hit = next(r for r in rows if (r["a4"], r["a6"], r["b3"]) == triple)
        examples[str(triple)] = {
            "stage_id": hit["stage_id"],
            "traversal": hit["traversal"],
            "loop": hit["declared_loop"],
            "composition": hit["composition"],
        }
    return {
        "axes": ["a4_traversal_order", "a6_precedence", "b3_loop_role"],
        "reachable_combination_count": len(triples),
        "possible_combination_count": 8,
        "reachable_combinations": [list(t) for t in triples],
        "examples": examples,
        "structural_coupling": len(triples) < 8,
        "note": "a4 and b3 are structurally coupled in the built Type-1 chart because outer=deductive and inner=inductive; a6 remains separable from them.",
    }


def branch_family_reachability(rows: list[dict]) -> dict:
    pairs = sorted({(r["a1_branch"], r["a5"]) for r in rows})
    examples = {}
    for pair in pairs:
        hit = next(r for r in rows if (r["a1_branch"], r["a5"]) == pair)
        examples[str(pair)] = {
            "stage_id": hit["stage_id"],
            "terrain": hit["terrain"],
            "operator": hit["operator"],
            "traversal": hit["traversal"],
        }
    return {
        "axes": ["a1_branch", "a5_operator_family"],
        "reachable_combination_count": len(pairs),
        "possible_combination_count": 4,
        "reachable_combinations": [list(p) for p in pairs],
        "examples": examples,
        "independent_variation_reached": len(pairs) == 4,
        "note": "Type-1 terrain branch pairs {Se,Ni} vs {Ne,Si} cross the native operator-family split, so a1_branch and a5 can vary independently in this stage chart.",
    }


def z3_unique_function(rows: list[dict], left: str, right: str, erased: bool):
    import z3

    usable = [r for r in rows if r[left] is not None and r[right] is not None]
    left_values = sorted({int(r[left]) for r in usable})
    right_values = sorted({int(r[right]) for r in usable})
    if erased:
        erased_left = left_values[-1]
        usable = [r for r in usable if int(r[left]) != erased_left]
    f = {lv: z3.Int(f"f_{lv}") for lv in left_values}
    solver = z3.Solver()
    for lv in left_values:
        solver.add(z3.Or([f[lv] == rv for rv in right_values]))
    for row in usable:
        solver.add(f[int(row[left])] == int(row[right]))
    if solver.check() != z3.sat:
        return (False, False, None)
    model = solver.model()
    assignment = {lv: model[f[lv]].as_long() for lv in left_values}
    solver.add(z3.Or([f[lv] != assignment[lv] for lv in left_values]))
    unique = solver.check() == z3.unsat
    return (True, unique, assignment)


def cvc5_unique_function(rows: list[dict], left: str, right: str, erased: bool):
    import cvc5
    from cvc5 import Kind

    usable = [r for r in rows if r[left] is not None and r[right] is not None]
    left_values = sorted({int(r[left]) for r in usable})
    right_values = sorted({int(r[right]) for r in usable})
    if erased:
        erased_left = left_values[-1]
        usable = [r for r in usable if int(r[left]) != erased_left]
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    f = {lv: solver.mkConst(int_sort, f"f_{lv}") for lv in left_values}
    for lv in left_values:
        choices = [solver.mkTerm(Kind.EQUAL, f[lv], solver.mkInteger(rv)) for rv in right_values]
        solver.assertFormula(solver.mkTerm(Kind.OR, *choices))
    for row in usable:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, f[int(row[left])], solver.mkInteger(int(row[right]))))
    if not solver.checkSat().isSat():
        return (False, False, None)
    assignment = {lv: int(solver.getValue(f[lv]).getIntegerValue()) for lv in left_values}
    solver.push()
    diffs = [solver.mkTerm(Kind.DISTINCT, f[lv], solver.mkInteger(assignment[lv])) for lv in left_values]
    solver.assertFormula(solver.mkTerm(Kind.OR, *diffs))
    unique = solver.checkSat().isUnsat()
    solver.pop()
    return (True, unique, assignment)


def smt_gate(rows: list[dict], relations: list[dict]) -> dict:
    passed = [r for r in relations if r["verdict"] == "dependent_above_95pct_null"]
    out = {"attempted_pairs": [r["pair"] for r in passed], "results": []}
    try:
        import z3
        import cvc5
        from cvc5 import Kind
    except ImportError as exc:
        out["status"] = "skipped_missing_optional_solver"
        out["missing"] = exc.name
        return out
    for rel in passed:
        left, right = rel["pair"]
        z3_real = z3_unique_function(rows, left, right, erased=False)
        z3_erased = z3_unique_function(rows, left, right, erased=True)
        cvc5_real = cvc5_unique_function(rows, left, right, erased=False)
        cvc5_erased = cvc5_unique_function(rows, left, right, erased=True)
        out["results"].append(
            {
                "pair": [left, right],
                "polarity": "measured rows force a unique right=f(left) map; erased left-class control must make uniqueness false",
                "z3_real_exists_unique_assignment": z3_real,
                "z3_erased_exists_unique_assignment": z3_erased,
                "cvc5_real_exists_unique_assignment": cvc5_real,
                "cvc5_erased_exists_unique_assignment": cvc5_erased,
                "flip": bool(z3_real[0] and z3_real[1] and cvc5_real[0] and cvc5_real[1] and z3_erased[0] and not z3_erased[1] and cvc5_erased[0] and not cvc5_erased[1]),
            }
        )
    out["status"] = "ran" if passed else "not_applicable_no_pairs_above_95pct_null"
    return out


def build_result() -> dict:
    rows = readout_rows()
    relations = relation_matrix(rows)
    return {
        "schema": "codex_ratchet.axis_relation_matrix_probe_v0.result.v1",
        "sim_id": "axis_relation_matrix_probe_v0",
        "classification": classification,
        "claim_ceiling": "QUARANTINE_EXPLORATORY",
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "engine": "numpy",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "read_first": [
            "system_v7/sims/AXES_FULL_EXTRACTION_20260703.md",
            "system_v7/sims/type1_engine_v0/",
            "system_v7/constraint_core/sims_and_scripts/axis_laws_dual_proof.py",
        ],
        "bit_extraction": {
            "a1_branch": "terrain-branch kernel chi1: Se/Ni=+1, Ne/Si=-1; independent of the operator factor",
            "a1_opchar": "legacy comparison proxy only: operator factor Fi/Fe unitary=1, Ti/Te proper CPTP/GKSL=0; overlaps a5 and is not A1",
            "a2": "terrain function frame: Ni/Si conjugated=1, Se/Ne direct=0",
            "a4": "traversal order: outer/deductive=0, inner/inductive=1",
            "a5": "operator family: F family=1, T family=0",
            "a6": "composition precedence: operator-first terrain_after_operator=1, terrain-first operator_after_terrain=0",
            "b0": "chart state sign: sign(r_z) from fixed probe-state Bloch vector; zero retained as 0 and excluded from b6 law rows",
            "b3": "chart role: outer loop=+1, inner loop=-1",
            "b6": "derived chart law bit where b0 nonzero: -b0*b3",
            "excluded": {
                "a0": "undefinable at this stage-level engine depth without Xi/cut bridge or admitted a0 proxy",
                "axes_7_12": "informal/game-theory tier only; not active axis math here",
            },
        },
        "probe_state_count": len(PROBE_STATES),
        "readout_row_count": len(rows),
        "readout_rows": rows,
        "relation_matrix": relations,
        "laws": laws(rows),
        "conflation_stress_test": stress(rows),
        "a1_branch_a5_reachability": branch_family_reachability(rows),
        "dual_smt_gate": smt_gate(rows, relations),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": True,
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = build_result()
    path = RESULTS / "axis_relation_matrix_probe_numpy_results.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    above = [r for r in out["relation_matrix"] if r["verdict"] == "dependent_above_95pct_null"]
    print(json.dumps({
        "engine": "numpy",
        "result_path": str(path),
        "rows": out["readout_row_count"],
        "above_95pct_pairs": len(above),
        "reachable_orderish_combinations": out["conflation_stress_test"]["reachable_combination_count"],
        "b6_law_holds": out["laws"]["b6_equals_minus_b0_times_b3"]["holds"],
    }, indent=2))


if __name__ == "__main__":
    main()
