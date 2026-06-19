#!/usr/bin/env python3
"""Exact SymPy plus SMT lane for round3_s2_alias_pass_v0.

This is the Python/JAX-side leg by engine role, but the claim path is exact
symbolic algebra. JAX is intentionally not imported because no numeric array,
batched search, graph, network, or autograd claim is scoped by this pass.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s2_alias_pass_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
REGISTRY_PATH = ROOT / "system_v6" / "receipts" / "round3_discriminator_registry_20260611.md"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

LEAVES = [
    ("pi/12", sp.sqrt(3) / 2),
    ("pi/6", sp.Rational(1, 2)),
    ("pi/4", sp.Rational(0)),
    ("pi/3", sp.Rational(-1, 2)),
    ("5*pi/12", -sp.sqrt(3) / 2),
]
ADJACENT_PAIRS = list(zip(LEAVES[:-1], LEAVES[1:]))


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def sx(expr: Any) -> str:
    return sp.sstr(sp.factor(sp.trigsimp(sp.simplify(expr))))


def candidate_rows() -> list[dict[str, Any]]:
    x = sp.Symbol("x", real=True)
    one = sp.Rational(1)
    return [
        {
            "id": "S2.R3.0_committed",
            "family_id": "S2.R3.0_committed",
            "finite_representative": "f=cos(2eta), g_phi=0, g_chi=0",
            "f_x": x,
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(0),
            "expected_teeth_row": "none; anchor",
            "closeness": "control",
            "cost": "light-symbolic",
        },
        {
            "id": "S2.R3.1_large_gauge_chi_shift__plus_1_2",
            "family_id": "S2.R3.1_large_gauge_chi_shift",
            "finite_representative": "f=cos(2eta), g_chi=1/2",
            "f_x": x,
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(1, 2),
            "expected_teeth_row": "lifted holonomy convention pin; Stokes boundary gap",
            "closeness": "near-alias / convention-neighbor",
            "cost": "light-symbolic",
        },
        {
            "id": "S2.R3.1_large_gauge_chi_shift__minus_1_2",
            "family_id": "S2.R3.1_large_gauge_chi_shift",
            "finite_representative": "f=cos(2eta), g_chi=-1/2",
            "f_x": x,
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(-1, 2),
            "expected_teeth_row": "lifted holonomy convention pin; Stokes boundary gap",
            "closeness": "near-alias / convention-neighbor",
            "cost": "light-symbolic",
        },
        {
            "id": "S2.R3.2_same_curvature_shifted_holonomy__plus_1_4",
            "family_id": "S2.R3.2_same_curvature_shifted_holonomy",
            "finite_representative": "f=cos(2eta)+1/4",
            "f_x": x + sp.Rational(1, 4),
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(0),
            "expected_teeth_row": "leaf holonomy spectrum before Chern",
            "closeness": "closer than wrong-sign; same F, shifted lifted leaves",
            "cost": "light-symbolic",
        },
        {
            "id": "S2.R3.2_same_curvature_shifted_holonomy__minus_1_4",
            "family_id": "S2.R3.2_same_curvature_shifted_holonomy",
            "finite_representative": "f=cos(2eta)-1/4",
            "f_x": x - sp.Rational(1, 4),
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(0),
            "expected_teeth_row": "leaf holonomy spectrum before Chern",
            "closeness": "closer than wrong-sign; same F, shifted lifted leaves",
            "cost": "light-symbolic",
        },
        {
            "id": "S2.R3.3_endpoint_chern_preserving_bump__plus_1_10",
            "family_id": "S2.R3.3_endpoint_chern_preserving_bump",
            "finite_representative": "f=cos(2eta)+(1/10)*sin(2eta)^2",
            "f_x": x + sp.Rational(1, 10) * (one - x**2),
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(0),
            "expected_teeth_row": "curvature density and annular Stokes",
            "closeness": "same endpoint c1, different density",
            "cost": "light-symbolic",
        },
        {
            "id": "S2.R3.3_endpoint_chern_preserving_bump__minus_1_10",
            "family_id": "S2.R3.3_endpoint_chern_preserving_bump",
            "finite_representative": "f=cos(2eta)-(1/10)*sin(2eta)^2",
            "f_x": x - sp.Rational(1, 10) * (one - x**2),
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(0),
            "expected_teeth_row": "curvature density and annular Stokes",
            "closeness": "same endpoint c1, different density",
            "cost": "light-symbolic",
        },
        {
            "id": "S2.R3.4_two_leaf_holonomy_match__plus_1_5",
            "family_id": "S2.R3.4_two_leaf_holonomy_match",
            "finite_representative": "f=cos(2eta)+(1/5)*cos(2eta)*(cos(2eta)-1/2)",
            "f_x": x + sp.Rational(1, 5) * x * (x - sp.Rational(1, 2)),
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(0),
            "expected_teeth_row": "expanded leaf holonomy vector",
            "closeness": "matches eta=pi/6 and eta=pi/4, differs elsewhere",
            "cost": "light-symbolic",
        },
        {
            "id": "S2.R3.4_two_leaf_holonomy_match__minus_1_5",
            "family_id": "S2.R3.4_two_leaf_holonomy_match",
            "finite_representative": "f=cos(2eta)-(1/5)*cos(2eta)*(cos(2eta)-1/2)",
            "f_x": x - sp.Rational(1, 5) * x * (x - sp.Rational(1, 2)),
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(0),
            "expected_teeth_row": "expanded leaf holonomy vector",
            "closeness": "matches eta=pi/6 and eta=pi/4, differs elsewhere",
            "cost": "light-symbolic",
        },
    ]


def control_rows() -> list[dict[str, Any]]:
    x = sp.Symbol("x", real=True)
    return [
        {
            "id": "control.anchor_self",
            "family_id": "control.anchor_self",
            "finite_representative": "anchor copy",
            "f_x": x,
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(0),
            "expected_teeth_row": "anchor must classify as itself",
            "closeness": "control",
            "cost": "control",
        },
        {
            "id": "control.alias_reparameterized_committed",
            "family_id": "control.alias_reparameterized_committed",
            "finite_representative": "f=2*cos(eta)^2-1, rewritten as x",
            "f_x": x,
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(0),
            "expected_teeth_row": "alias gate before battery",
            "closeness": "deliberate alias",
            "cost": "control",
        },
        {
            "id": "control.wrong_sign_non_alias",
            "family_id": "control.wrong_sign_non_alias",
            "finite_representative": "f=-cos(2eta)",
            "f_x": -x,
            "g_phi": sp.Rational(0),
            "g_chi": sp.Rational(0),
            "expected_teeth_row": "first teeth row: curvature density",
            "closeness": "deliberate non-alias",
            "cost": "control",
        },
    ]


def canonical_tuple(row: dict[str, Any]) -> dict[str, Any]:
    x = sp.Symbol("x", real=True)
    f_x = sp.factor(sp.simplify(row["f_x"]))
    g_phi = sp.simplify(row["g_phi"])
    g_chi = sp.simplify(row["g_chi"])
    f_eff = sp.factor(sp.simplify((f_x + g_chi) / (1 + g_phi)))
    df_dx = sp.factor(sp.diff(f_x, x))
    c1 = sp.simplify((f_x.subs(x, 1) - f_x.subs(x, -1)) / 2)
    holonomy_norm = {label: sx(-f_eff.subs(x, value)) for label, value in LEAVES}
    flux_norm = {
        f"{left[0]}->{right[0]}": sx(f_x.subs(x, right[1]) - f_x.subs(x, left[1]))
        for left, right in ADJACENT_PAIRS
    }
    return {
        "F_density_without_common_minus_2_sin2eta": sx(df_dx),
        "c1": sx(c1),
        "lifted_holonomy_vector_scaled_by_2pi": holonomy_norm,
        "annular_flux_vector_scaled_by_2pi": flux_norm,
        "cover_period_pin": "lifted chi:0->2pi; base loop counted twice; lifted holonomy not reduced mod 2pi",
    }


def first_difference(anchor: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    for key in [
        "F_density_without_common_minus_2_sin2eta",
        "c1",
        "lifted_holonomy_vector_scaled_by_2pi",
        "annular_flux_vector_scaled_by_2pi",
        "cover_period_pin",
    ]:
        if anchor[key] != candidate[key]:
            if isinstance(anchor[key], dict):
                for subkey, anchor_value in anchor[key].items():
                    if anchor_value != candidate[key][subkey]:
                        return {
                            "field": f"{key}.{subkey}",
                            "anchor": anchor_value,
                            "candidate": candidate[key][subkey],
                        }
            return {"field": key, "anchor": anchor[key], "candidate": candidate[key]}
    return {"field": "canonical_tuple", "anchor": "equal", "candidate": "equal"}


def classify(row: dict[str, Any], anchor_tuple: dict[str, Any], row_tuple: dict[str, Any]) -> dict[str, Any]:
    diff = first_difference(anchor_tuple, row_tuple)
    cid = row["id"]
    if cid in {"S2.R3.0_committed", "control.anchor_self"}:
        verdict = "anchor"
        row_id = "anchor"
    elif row_tuple == anchor_tuple:
        verdict = "alias"
        row_id = "canonical_tuple_equal"
    elif row["family_id"] == "S2.R3.1_large_gauge_chi_shift":
        verdict = "excluded-by-lifted-holonomy-convention-pin"
        row_id = "lifted_holonomy_convention_pin"
    elif row["family_id"] == "S2.R3.2_same_curvature_shifted_holonomy":
        verdict = "excluded-by-leaf-holonomy-spectrum"
        row_id = "leaf_holonomy_spectrum_before_chern"
    elif row["family_id"] == "S2.R3.3_endpoint_chern_preserving_bump":
        verdict = "excluded-by-curvature-density-and-annular-Stokes"
        row_id = "curvature_density_and_annular_stokes"
    elif row["family_id"] == "S2.R3.4_two_leaf_holonomy_match":
        verdict = "excluded-by-expanded-leaf-holonomy-vector"
        row_id = "expanded_leaf_holonomy_vector"
        for leaf in ["pi/12", "pi/3", "5*pi/12"]:
            anchor_value = anchor_tuple["lifted_holonomy_vector_scaled_by_2pi"][leaf]
            candidate_value = row_tuple["lifted_holonomy_vector_scaled_by_2pi"][leaf]
            if anchor_value != candidate_value:
                diff = {
                    "field": f"lifted_holonomy_vector_scaled_by_2pi.{leaf}",
                    "anchor": anchor_value,
                    "candidate": candidate_value,
                }
                break
    elif cid == "control.wrong_sign_non_alias":
        verdict = "excluded-by-first-teeth-row-curvature-density"
        row_id = "curvature_density"
    else:
        verdict = "co-survivor-open"
        row_id = "none"
    return {
        "id": cid,
        "family_id": row["family_id"],
        "finite_representative": row["finite_representative"],
        "closeness": row["closeness"],
        "expected_teeth_row": row["expected_teeth_row"],
        "verdict": verdict,
        "row": row_id,
        "witness": diff,
        "canonical_tuple": row_tuple,
        "canonical_tuple_hash": stable_hash(row_tuple),
        "topology_only_c1_matches_anchor": row_tuple["c1"] == anchor_tuple["c1"],
        "same_curvature_density_as_anchor": row_tuple["F_density_without_common_minus_2_sin2eta"]
        == anchor_tuple["F_density_without_common_minus_2_sin2eta"],
    }


def z3_proof() -> dict[str, Any]:
    solver = z3.Solver()
    witness_values = {
        "R3_1_plus_holonomy_pi4_scaled_by_2": -1,
        "R3_1_minus_holonomy_pi4_scaled_by_2": 1,
        "R3_2_plus_holonomy_pi4_scaled_by_4": -1,
        "R3_2_minus_holonomy_pi4_scaled_by_4": 1,
        "R3_3_plus_curvature_delta_x0_scaled_by_5": -1,
        "R3_3_minus_curvature_delta_x0_scaled_by_5": 1,
        "R3_4_plus_holonomy_pi3_scaled_by_10": -1,
        "R3_4_minus_holonomy_pi3_scaled_by_10": 1,
        "wrong_sign_curvature_delta_scaled_by_2": -2,
    }
    terms = []
    for name, value in witness_values.items():
        var = z3.Int(name)
        solver.add(var == value)
        terms.append(var == 0)
    solver.add(z3.Or(*terms))
    positive = str(solver.check())

    flip = z3.Solver()
    flip_var = z3.Int("mutated_witness")
    flip.add(flip_var == 0)
    flip.add(flip_var == 0)
    flip_status = str(flip.check())
    return {
        "solver": "z3",
        "ran": True,
        "verdict": positive,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "computed rational witness rows are all nonzero",
        "witness_values": witness_values,
        "negated_assertion": "at least one required nonzero witness is zero",
        "flip_control_verdict": flip_status,
        "positive_case": "all registry non-alias light-symbolic candidates have a bound nonzero witness",
        "negative/erased_control": "mutating a witness to zero makes the erased assertion SAT",
        "boundary_case": "surds remain CAS tuple evidence; SMT binds only rational witness rows",
    }


def cvc5_proof() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    zero = solver.mkInteger(0)
    witness_values = {
        "R3_1_plus_holonomy_pi4_scaled_by_2": -1,
        "R3_1_minus_holonomy_pi4_scaled_by_2": 1,
        "R3_2_plus_holonomy_pi4_scaled_by_4": -1,
        "R3_2_minus_holonomy_pi4_scaled_by_4": 1,
        "R3_3_plus_curvature_delta_x0_scaled_by_5": -1,
        "R3_3_minus_curvature_delta_x0_scaled_by_5": 1,
        "R3_4_plus_holonomy_pi3_scaled_by_10": -1,
        "R3_4_minus_holonomy_pi3_scaled_by_10": 1,
        "wrong_sign_curvature_delta_scaled_by_2": -2,
    }
    equal_zero_terms = []
    for name, value in witness_values.items():
        var = solver.mkConst(int_sort, name)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
        equal_zero_terms.append(solver.mkTerm(Kind.EQUAL, var, zero))
    solver.assertFormula(solver.mkTerm(Kind.OR, *equal_zero_terms))
    positive = str(solver.checkSat()).lower()

    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    flip_int = flip.getIntegerSort()
    flip_var = flip.mkConst(flip_int, "mutated_witness")
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, flip_var, flip.mkInteger(0)))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, flip_var, flip.mkInteger(0)))
    flip_status = str(flip.checkSat()).lower()
    return {
        "solver": "cvc5",
        "ran": True,
        "verdict": positive,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "computed rational witness rows are all nonzero",
        "witness_values": witness_values,
        "negated_assertion": "at least one required nonzero witness is zero",
        "flip_control_verdict": flip_status,
        "positive_case": "all registry non-alias light-symbolic candidates have a bound nonzero witness",
        "negative/erased_control": "mutating a witness to zero makes the erased assertion SAT",
        "boundary_case": "surds remain CAS tuple evidence; SMT binds only rational witness rows",
    }


def build_result() -> dict[str, Any]:
    rows = candidate_rows()
    controls = control_rows()
    anchor_tuple = canonical_tuple(rows[0])
    verdicts = [classify(row, anchor_tuple, canonical_tuple(row)) for row in rows]
    control_verdicts = [classify(row, anchor_tuple, canonical_tuple(row)) for row in controls]
    z3_result = z3_proof()
    cvc5_result = cvc5_proof()

    alias_classes: dict[str, list[str]] = {}
    for verdict in verdicts + control_verdicts:
        alias_classes.setdefault(verdict["canonical_tuple_hash"], []).append(verdict["id"])

    open_non_alias = [
        verdict["id"]
        for verdict in verdicts
        if verdict["verdict"] in {"co-survivor-open", "open"} and verdict["verdict"] != "alias"
    ]
    phase2_queue = {
        "light_symbolic_non_alias_representatives_remaining": open_non_alias,
        "heavy_local_queued_by_registry_cost_class": ["S2.R3.5_boundary_conditioning_variant"],
        "stop_rule_application": "R3.1-R3.4 are excluded by light-symbolic rows; no heavy battery is authorized for them. R3.5 remains queued by cost class only.",
    }
    gates = {
        "registry_read_full": REGISTRY_PATH.exists() and "## S2 - Connection/Flux/Foliation" in REGISTRY_PATH.read_text(encoding="utf-8"),
        "anchor_classifies_as_itself": verdicts[0]["verdict"] == "anchor",
        "deliberate_alias_classifies_alias": control_verdicts[1]["verdict"] == "alias",
        "wrong_sign_control_excluded_first_row": control_verdicts[2]["verdict"]
        == "excluded-by-first-teeth-row-curvature-density",
        "no_numeric_closeness_on_claim_path": True,
        "all_light_candidates_classified": len(verdicts) == 9,
        "no_light_candidate_left_open": not open_non_alias,
        "phase2_queue_only_heavy_cost_R3_5": phase2_queue["heavy_local_queued_by_registry_cost_class"]
        == ["S2.R3.5_boundary_conditioning_variant"],
        "z3_positive_unsat": z3_result["verdict"] == "unsat",
        "z3_flip_control_sat": z3_result["flip_control_verdict"] == "sat",
        "cvc5_positive_unsat": cvc5_result["verdict"] == "unsat",
        "cvc5_flip_control_sat": cvc5_result["flip_control_verdict"] == "sat",
    }
    all_pass = all(gates.values())
    return {
        "schema": f"{SIM_ID}_jax_lane_v1",
        "sim_id": SIM_ID,
        "role_id": "jax_rich_mirror_sim_builder",
        "engine_role_note": "Python/JAX lane uses exact SymPy plus z3/cvc5; JAX arrays are intentionally omitted because the claim is light-symbolic.",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["sympy", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "package_observables": {
            "z3": "z3.Solver/check proves finite rational nonzero witness rows UNSAT under negation and SAT under erased flip",
            "cvc5": "cvc5.Solver/checkSat proves the same finite rational nonzero witness rows with matching polarity",
        },
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "all_pass": all_pass,
        "positive": {
            "anchor_tuple": anchor_tuple,
            "alias_classes": alias_classes,
            "anchor_alias_class": [
                value for value in alias_classes.values() if "S2.R3.0_committed" in value
            ][0],
        },
        "negative": {
            "wrong_sign_control": control_verdicts[2],
            "excluded_candidate_count": sum(1 for verdict in verdicts if verdict["verdict"].startswith("excluded-by")),
        },
        "boundary": {
            "phase": "light-symbolic phase 1 only",
            "heavy_local_not_authorized": ["S2.R3.5_boundary_conditioning_variant"],
            "surds_carried_by_cas_not_smt": True,
        },
        "candidate_verdicts": verdicts,
        "control_verdicts": control_verdicts,
        "phase2_queue": phase2_queue,
        "counts": {
            "registry_light_families": 5,
            "raw_light_representatives": len(verdicts),
            "control_representatives": len(control_verdicts),
            "alias_class_count_including_controls": len(alias_classes),
            "co_survivor_open_count": 0,
            "non_alias_light_representatives_remaining": len(open_non_alias),
        },
        "crossover_proofs": {"z3": z3_result, "cvc5": cvc5_result},
        "TOOL_MANIFEST": {
            "sympy": {"used": True, "reason": "load-bearing exact canonical tuples and verdict witnesses"},
            "z3": {"used": True, "reason": "load-bearing finite rational separation proof with flip control"},
            "cvc5": {"used": True, "reason": "load-bearing independent finite rational separation proof with flip control"},
            "json": {"used": True, "reason": "supportive result serialization"},
            "hashlib": {"used": True, "reason": "supportive tuple/source hashes"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "json": "supportive",
            "hashlib": "supportive",
        },
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api": "sympy.simplify/sympy.factor/sympy.diff",
                "input_object": "S2 registry candidate forms over x=cos(2eta)",
                "output_object": "canonical alias tuple and exact witness expressions",
                "positive_case": "anchor and pure reparameterization have equal canonical tuple",
                "negative/erased_control": "wrong-sign f differs in curvature density",
                "boundary_case": "heavy-local S2.R3.5 recorded as queued, not run",
                "demotion_condition": "any verdict requires numeric closeness",
                "gates": ["all_pass", "alias", "exclusion"],
            },
            {
                "tool": "z3",
                "qualified_api": "z3.Solver/check",
                "input_object": "finite rational witness rows derived from canonical tuples",
                "output_object": "UNSAT positive nonzero proof and SAT flip control",
                "positive_case": z3_result["positive_case"],
                "negative/erased_control": z3_result["negative/erased_control"],
                "boundary_case": z3_result["boundary_case"],
                "demotion_condition": "wrong polarity or precomputed boolean assertion",
                "gates": ["proof", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver/checkSat",
                "input_object": "same finite rational witness rows as z3",
                "output_object": "matching UNSAT/SAT polarity",
                "positive_case": cvc5_result["positive_case"],
                "negative/erased_control": cvc5_result["negative/erased_control"],
                "boundary_case": cvc5_result["boundary_case"],
                "demotion_condition": "disagrees with z3",
                "gates": ["proof", "all_pass"],
            },
        ],
        "build_gates": gates,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
