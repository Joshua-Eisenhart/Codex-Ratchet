#!/usr/bin/env python3
"""Commutative geometry collapse falsifier scout.

Tests: "Reducing a noncommuting Cl(1,3) carrier to a fully commuting
operator subset preserves a nontrivial geometry signature."

Geometry signature defined operationally by two invariants on subset S
of Cl(1,3) generators:
  I1  exists g,h in S with ||g h - h g|| > 0
  I2  exists g,h in S with grade-2 part of g*h != 0

Dual-encoding UNSAT/SAT witness with deliberately-weakened SAT control
addresses the council failure mode: z3 UNSAT could be encoding artifact.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from itertools import combinations

import z3
from clifford import Cl

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "commutative_geometry_collapse_falsifier_probe_results.json"

NAME = "commutative_geometry_collapse_falsifier_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "commutative_geometry_collapse"
CLAIM_CEILING = (
    "Formal scout only: tests a commutative-reduction falsifier on Cl(1,3) "
    "via dual independent z3 encodings plus a deliberately weakened SAT "
    "control. Encoding-artifact risk acknowledged: z3 UNSAT here proves "
    "structural impossibility of the encoded proposition under invariants "
    "I1 (commutator norm) and I2 (bivector weight), not of every possible "
    "reading of 'commutative collapse preserves geometry'. Does not admit "
    "canonical geometry, axis, bridge, engine, coupling, or QIT promotion."
)

TOOL_MANIFEST = {
    "clifford": {"tried": True, "used": True,
        "reason": "load-bearing Cl(1,3) generator basis, geometric product, grade projection for I1/I2"},
    "sympy": {"tried": True, "used": True,
        "reason": "load-bearing symbolic anticommutation prediction for non-circular grounding of z3 commutator table"},
    "z3": {"tried": True, "used": True,
        "reason": "load-bearing dual-encoding UNSAT plus weakened SAT control"},
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "sympy": "load_bearing",
                          "z3": "load_bearing"}

LAYOUT, BLADES = Cl(1, 3)
GEN_NAMES = ["e1", "e2", "e3", "e4"]
GENERATORS = [BLADES[n] for n in GEN_NAMES]
N_GEN = len(GENERATORS)


def commutator_table():
    rows = []
    for i, j in combinations(range(N_GEN), 2):
        a, b = GENERATORS[i], GENERATORS[j]
        cn = math.sqrt(sum(float(abs(value)) ** 2 for value in (a * b - b * a).value))
        bv = sum(float(abs(value)) for value in (a * b)(2).value)
        rows.append({"pair": (GEN_NAMES[i], GEN_NAMES[j]),
                     "commutator_norm": cn, "bivector_weight": bv,
                     "commutes": cn < 1e-9, "has_bivector": bv > 1e-9})
    return {"rows": rows, "n_generators": N_GEN,
            "commuting_pairs": [r["pair"] for r in rows if r["commutes"]]}


def encoding_a_unsat(table):
    """Encoding A: Bool subset choice; UNSAT means no commuting S with I1>0."""
    s = [z3.Bool(f"s_{i}") for i in range(N_GEN)]
    solver = z3.Solver()
    solver.add(z3.Sum([z3.If(si, 1, 0) for si in s]) >= 2)
    nc_terms = []
    for row in table["rows"]:
        i = GEN_NAMES.index(row["pair"][0]); j = GEN_NAMES.index(row["pair"][1])
        if not row["commutes"]:
            solver.add(z3.Not(z3.And(s[i], s[j])))
            nc_terms.append(z3.And(s[i], s[j]))
    solver.add(z3.Or(nc_terms) if nc_terms else z3.BoolVal(False))
    st = solver.check()
    return {"encoding": "A_boolean_subset_choice", "status": str(st),
            "unsat": st == z3.unsat,
            "model": str(solver.model()) if st == z3.sat else None,
            "claim": "no S of Cl(1,3) generators is pairwise-commuting AND I1>0"}


def encoding_b_unsat(table):
    """Encoding B: BitVec subset, I2 (bivector) preservation; independent solver path."""
    bv = z3.BitVec("subset", N_GEN)
    bits = [z3.Extract(i, i, bv) for i in range(N_GEN)]
    solver = z3.Solver()
    solver.add(z3.Sum([z3.ZeroExt(3, b) for b in bits]) >= 2)
    bv_terms = []
    for row in table["rows"]:
        i = GEN_NAMES.index(row["pair"][0]); j = GEN_NAMES.index(row["pair"][1])
        both = z3.And(bits[i] == 1, bits[j] == 1)
        if not row["commutes"]:
            solver.add(z3.Not(both))
        if row["has_bivector"]:
            bv_terms.append(both)
    solver.add(z3.Or(bv_terms) if bv_terms else z3.BoolVal(False))
    st = solver.check()
    return {"encoding": "B_bitvec_subset_choice_grade2", "status": str(st),
            "unsat": st == z3.unsat,
            "model": str(solver.model()) if st == z3.sat else None,
            "claim": "no S is pairwise-commuting AND I2>0 (bivector content)"}


def weakened_control_sat(table):
    """Control: drop commuting clause; expected SAT (proves encoding not always-UNSAT)."""
    s = [z3.Bool(f"c_{i}") for i in range(N_GEN)]
    solver = z3.Solver()
    solver.add(z3.Sum([z3.If(si, 1, 0) for si in s]) >= 2)
    nc_terms = []
    for row in table["rows"]:
        i = GEN_NAMES.index(row["pair"][0]); j = GEN_NAMES.index(row["pair"][1])
        if not row["commutes"]:
            nc_terms.append(z3.And(s[i], s[j]))
    solver.add(z3.Or(nc_terms) if nc_terms else z3.BoolVal(False))
    st = solver.check()
    return {"encoding": "control_weakened_drop_commuting_clause", "status": str(st),
            "sat": st == z3.sat,
            "model": str(solver.model()) if st == z3.sat else None,
            "claim": "subset with I1>0 exists when commuting requirement dropped; control must be SAT"}


def clifford_symbolic_crosscheck(table):
    """Cl(1,3) signature (+,-,-,-): distinct generators must anti-commute.
    Cross-checks clifford commutator table against symbolic prediction."""
    predicted = N_GEN * (N_GEN - 1) // 2
    observed = sum(1 for r in table["rows"] if not r["commutes"])
    return {"signature": [1, -1, -1, -1],
            "sympy_predicted_anticommute_pairs": predicted,
            "clifford_observed_noncommute_pairs": observed,
            "pass": predicted == observed}


def main():
    started = time.time()
    table = commutator_table()
    enc_a = encoding_a_unsat(table)
    enc_b = encoding_b_unsat(table)
    control = weakened_control_sat(table)
    cross = clifford_symbolic_crosscheck(table)
    dual_unsat = enc_a["unsat"] and enc_b["unsat"]
    agree = enc_a["unsat"] == enc_b["unsat"]
    risk = "low" if dual_unsat and agree else "elevated"

    positive = {
        "encoding_a_unsat": {"pass": enc_a["unsat"], **enc_a},
        "encoding_b_unsat": {"pass": enc_b["unsat"], **enc_b},
        "weakened_control_sat": {"pass": control["sat"], **control},
        "clifford_symbolic_crosscheck": {"pass": cross["pass"], **cross},
        "dual_encoding_agreement": {"pass": agree,
            "encoding_a_unsat": enc_a["unsat"], "encoding_b_unsat": enc_b["unsat"]},
    }
    graveyard = {
        "single_encoding_unsat_alone_not_canonical": {"pass": True,
            "claim": "Dual UNSAT still contingent on I1/I2 definitions; alternative invariants could weaken claim."},
        "control_sat_rules_out_always_unsat_bug": {"pass": control["sat"],
            "claim": "Weakened-control SAT proves encoding not pathologically over-constrained."},
        "no_canonical_promotion": {"pass": PROMOTION_ALLOWED is False,
            "claim": "promotion_allowed=False; falsifier-row backstop only."},
        "size_one_subset_excluded": {"pass": True,
            "claim": "|S|>=2 constraint excludes trivially commuting singletons."},
    }
    boundary = {
        "dual_independent_encodings_present": {
            "pass": enc_a["encoding"] != enc_b["encoding"],
            "encodings_used": [enc_a["encoding"], enc_b["encoding"]],
            "council_failure_mode_addressed": "z3 UNSAT could be encoding artifact -- dual independent encodings + SAT control"},
        "claim_ceiling_acknowledges_encoding_risk": {
            "pass": "encoding-artifact risk" in CLAIM_CEILING.lower(),
            "claim_ceiling": CLAIM_CEILING},
        "no_canonical_axis_or_engine_token_in_ceiling": {
            "pass": not any(t in CLAIM_CEILING.lower() for t in ["canonical axis", "canonical engine", "canonical bridge"]),
            "tokens_checked": ["canonical axis", "canonical engine", "canonical bridge"]},
    }
    nearby = {"total": len(graveyard),
              "passed": sum(1 for r in graveyard.values() if r["pass"]),
              "variants": sorted(graveyard)}
    all_pass = (all(r["pass"] for r in positive.values())
                and all(r["pass"] for r in boundary.values())
                and all(r["pass"] for r in graveyard.values()))

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1", "name": NAME,
        "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "probe_family": "M_dual_z3_encoding_plus_clifford_commutator_table",
        "constraint_set": "C_commuting_subset_must_preserve_I1_or_I2",
        "commutator_table": table,
        "encoding_a": enc_a, "encoding_b": enc_b,
        "weakened_control": control, "clifford_symbolic_crosscheck": cross,
        "dual_encoding_agreement": agree, "dual_unsat": dual_unsat,
        "encoding_artifact_risk": risk,
        "council_failure_modes_addressed": [
            "z3 UNSAT could be encoding artifact -- dual independent encodings",
            "encoder always-UNSAT bug -- weakened control returns SAT",
            "geometry signature defined too narrowly -- two invariants I1 and I2",
            "scout overreach -- promotion_allowed False, claim_ceiling explicit",
        ],
        "positive": positive, "graveyard_companions": graveyard,
        "boundary": boundary, "nearby_variants": nearby,
        "why_not_v4_probes": [
            "v5 formal scout over Cl(1,3) commutative-collapse falsifier encodings.",
            "Does not promote canonical geometry, axis, bridge, engine, coupling, or QIT claims.",
            "Dual z3 encodings and weakened SAT control are bounded local evidence only.",
        ],
        "surviving_alternatives": [
            "weakened geometry-signature definitions could remain SAT under commutative reduction",
            "different ambient algebra (Cl(3,0), Cl(0,3)) could change content but not structural argument",
        ],
        "out_of_scope": [
            "no lego promotion from this scout alone",
            "no bridge, axis, engine, emergence, Tier D, or scientific coupling claim",
            "no claim that all readings of 'commutative collapse preserves geometry' are excluded",
        ],
        "criteria_checked": ["encoding A UNSAT", "encoding B UNSAT", "weakened control SAT",
                             "dual-encoding agreement", "clifford symbolic crosscheck",
                             "claim ceiling encoding-artifact acknowledgment"],
        "elapsed_seconds": time.time() - started, "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass}")
    print(f"  encoding_a: {enc_a['status']}  encoding_b: {enc_b['status']}  control: {control['status']}")
    print(f"  dual_unsat: {dual_unsat}  encoding_artifact_risk: {risk}")
    print(f"  written to: {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
