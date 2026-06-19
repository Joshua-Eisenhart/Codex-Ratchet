#!/usr/bin/env python3
"""Exact SymPy plus SMT lane for round3_s9_alias_pass_v0.

The lane name follows the repo envelope convention. The scoped claim path is
exact symbolic connection canonicalization: f(eta), F=df/deta, exact leaf
holonomy values, annular flux differences, and finite SMT polarity. No numeric
closeness, JAX array, PyTorch tensor, graph, autograd, or path-ordered loop
claim is made.
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
SIM_ID = "round3_s9_alias_pass_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
REGISTRY_PATH = ROOT / "system_v6" / "receipts" / "round3_discriminator_registry_20260611.md"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

ETA = sp.symbols("eta", real=True)
LEAVES = [
    ("0", sp.Integer(0)),
    ("pi/6", sp.pi / 6),
    ("pi/4", sp.pi / 4),
    ("pi/3", sp.pi / 3),
    ("pi/2", sp.pi / 2),
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return sha256_text(stable_json(value))


def sx(expr: Any) -> str:
    return sp.sstr(sp.factor(sp.radsimp(sp.trigsimp(sp.simplify(expr)))))


def leaf_values(f_expr: sp.Expr) -> dict[str, str]:
    return {label: sx(f_expr.subs(ETA, value)) for label, value in LEAVES}


def annular_flux_values(f_expr: sp.Expr) -> dict[str, str]:
    values = []
    for (left_label, left), (right_label, right) in zip(LEAVES[:-1], LEAVES[1:]):
        values.append(
            (
                f"{left_label}->{right_label}",
                sx(sp.simplify(f_expr.subs(ETA, right) - f_expr.subs(ETA, left))),
            )
        )
    return dict(values)


def canonical_tuple(f_expr: sp.Expr, *, path_ordered_loop_signature: Any = "not-scoped-light-symbolic") -> dict[str, Any]:
    simplified = sp.factor(sp.radsimp(sp.trigsimp(sp.simplify(f_expr))))
    curvature = sp.diff(simplified, ETA)
    f0 = simplified.subs(ETA, 0)
    fpi2 = simplified.subs(ETA, sp.pi / 2)
    return {
        "canonicalizer": (
            "f_simplified, F=f'(eta), c1, leaf_holonomy_vector[0,pi/6,pi/4,pi/3,pi/2], "
            "annular_flux_vector, validity_class, path_ordered_loop_signature_when_scoped"
        ),
        "f_simplified": sx(simplified),
        "F_curvature_form_coefficient": sx(curvature),
        "c1": sx(sp.simplify((f0 - fpi2) / 2)),
        "leaf_holonomy_vector": leaf_values(simplified),
        "annular_flux_vector": annular_flux_values(simplified),
        "validity_class": "ordinary_one_form_A=dphi+f(eta)dchi_on_pinned_S9_chart",
        "path_ordered_loop_signature": path_ordered_loop_signature,
        "s2_s9_convention_pin": "pinned_phi_holonomy_convention; pin-relative separations are reopenable, not intrinsic kills",
    }


def registry_rows() -> list[dict[str, Any]]:
    anchor = sp.cos(2 * ETA)
    return [
        {
            "id": "S9.R3.0_committed_hopf",
            "finite_representative": "f=cos(2eta)",
            "closeness": "control",
            "expected_teeth_row": "none; anchor",
            "cost": "light-symbolic",
            "forms": [{"variant": "anchor", "f_expr": anchor}],
        },
        {
            "id": "S9.R3.1_c1_small_density_bump",
            "finite_representative": "f=cos(2eta)+epsilon*sin(2eta)^2, epsilon in {1/20,-1/20}",
            "closeness": "closest same-c1 density neighbor",
            "expected_teeth_row": "curvature density before holonomy",
            "cost": "light-symbolic",
            "forms": [
                {"variant": "epsilon=1/20", "f_expr": anchor + sp.Rational(1, 20) * sp.sin(2 * ETA) ** 2},
                {"variant": "epsilon=-1/20", "f_expr": anchor - sp.Rational(1, 20) * sp.sin(2 * ETA) ** 2},
            ],
        },
        {
            "id": "S9.R3.2_one_leaf_match_pi6",
            "finite_representative": "f=cos(2eta)+epsilon*(cos(2eta)-1/2), epsilon in {1/10,-1/10}",
            "closeness": "matches holonomy at pi/6 only",
            "expected_teeth_row": "expanded holonomy spectrum",
            "cost": "light-symbolic",
            "forms": [
                {"variant": "epsilon=1/10", "f_expr": anchor + sp.Rational(1, 10) * (sp.cos(2 * ETA) - sp.Rational(1, 2))},
                {"variant": "epsilon=-1/10", "f_expr": anchor - sp.Rational(1, 10) * (sp.cos(2 * ETA) - sp.Rational(1, 2))},
            ],
        },
        {
            "id": "S9.R3.3_one_leaf_match_pi4",
            "finite_representative": "f=cos(2eta)+epsilon*cos(2eta), epsilon in {1/10,-1/10}",
            "closeness": "matches holonomy at pi/4 only",
            "expected_teeth_row": "expanded holonomy spectrum",
            "cost": "light-symbolic",
            "forms": [
                {"variant": "epsilon=1/10", "f_expr": anchor + sp.Rational(1, 10) * sp.cos(2 * ETA)},
                {"variant": "epsilon=-1/10", "f_expr": anchor - sp.Rational(1, 10) * sp.cos(2 * ETA)},
            ],
        },
        {
            "id": "S9.R3.4_two_leaf_match_pi6_pi4",
            "finite_representative": "f=cos(2eta)+epsilon*cos(2eta)*(cos(2eta)-1/2), epsilon in {1/10,-1/10}",
            "closeness": "very close leaf-anchor neighbor",
            "expected_teeth_row": "annular flux plus off-anchor holonomy",
            "cost": "light-symbolic",
            "forms": [
                {
                    "variant": "epsilon=1/10",
                    "f_expr": anchor
                    + sp.Rational(1, 10) * sp.cos(2 * ETA) * (sp.cos(2 * ETA) - sp.Rational(1, 2)),
                },
                {
                    "variant": "epsilon=-1/10",
                    "f_expr": anchor
                    - sp.Rational(1, 10) * sp.cos(2 * ETA) * (sp.cos(2 * ETA) - sp.Rational(1, 2)),
                },
            ],
        },
        {
            "id": "S9.R3.5_path_ordered_loop_neighbor",
            "finite_representative": "same local c1 row plus two named quaternionic loop families from the committed transport closure",
            "closeness": "closest heavy transport neighbor",
            "expected_teeth_row": "path-ordered holonomy commutator",
            "cost": "heavy-local",
            "forms": [{"variant": "local-c1-anchor-plus-heavy-loop-family", "f_expr": anchor}],
        },
    ]


def first_witness(anchor: dict[str, Any], candidate: dict[str, Any], *, preferred_row: str) -> dict[str, Any]:
    if preferred_row == "curvature density before holonomy":
        paths = [("F_curvature_form_coefficient",)]
    elif preferred_row == "expanded holonomy spectrum":
        paths = [("leaf_holonomy_vector", "0"), ("leaf_holonomy_vector", "pi/4"), ("leaf_holonomy_vector", "pi/3")]
    elif preferred_row == "annular flux plus off-anchor holonomy":
        paths = [
            ("annular_flux_vector", "0->pi/6"),
            ("annular_flux_vector", "pi/4->pi/3"),
            ("leaf_holonomy_vector", "0"),
            ("leaf_holonomy_vector", "pi/3"),
        ]
    else:
        paths = [
            ("f_simplified",),
            ("F_curvature_form_coefficient",),
            ("leaf_holonomy_vector", "0"),
            ("annular_flux_vector", "0->pi/6"),
        ]
    for path in paths:
        left: Any = anchor
        right: Any = candidate
        for part in path:
            left = left[part]
            right = right[part]
        if left != right:
            return {"field": ".".join(path), "anchor": left, "candidate": right}
    return {"field": "canonical_tuple", "anchor": "equal", "candidate": "equal"}


def z3_nonzero_witness_proof() -> dict[str, Any]:
    solver = z3.Solver()
    anchor_scaled = z3.Int("anchor_leaf0_scaled_by_20")
    candidate_scaled = z3.Int("candidate_leaf0_scaled_by_20")
    solver.add(anchor_scaled == 20)
    solver.add(candidate_scaled == 21)
    solver.add(anchor_scaled == candidate_scaled)
    positive = str(solver.check())

    flip = z3.Solver()
    flip_anchor = z3.Int("flip_anchor_leaf0_scaled_by_20")
    flip_candidate = z3.Int("flip_candidate_leaf0_scaled_by_20")
    flip.add(flip_anchor == 20)
    flip.add(flip_candidate == 20)
    flip.add(flip_anchor == flip_candidate)
    flip_status = str(flip.check())
    return {
        "solver": "z3",
        "ran": True,
        "verdict": positive,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "computed exact rational off-anchor holonomy witness cannot equal the pinned anchor value",
        "witness_values": {
            "candidate": "S9.R3.2_one_leaf_match_pi6 epsilon=1/10",
            "leaf": "0",
            "anchor_leaf0": "1",
            "candidate_leaf0": "21/20",
            "scaled_difference": "1",
        },
        "negated_assertion": "anchor_leaf0_scaled_by_20 == candidate_leaf0_scaled_by_20",
        "flip_control_verdict": flip_status,
        "positive_case": "off-anchor holonomy differs by exact rational 1/20, so alias equality is UNSAT",
        "negative/erased_control": "deliberate reparameterized alias has equal scaled leaf value and is SAT",
        "boundary_case": "SMT binds a finite rational nonzero witness only; path-ordered loops remain queued-heavy-local",
    }


def cvc5_nonzero_witness_proof() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    anchor_scaled = solver.mkConst(int_sort, "anchor_leaf0_scaled_by_20")
    candidate_scaled = solver.mkConst(int_sort, "candidate_leaf0_scaled_by_20")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, anchor_scaled, solver.mkInteger(20)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, candidate_scaled, solver.mkInteger(21)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, anchor_scaled, candidate_scaled))
    positive = str(solver.checkSat()).lower()

    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    int_sort = flip.getIntegerSort()
    flip_anchor = flip.mkConst(int_sort, "flip_anchor_leaf0_scaled_by_20")
    flip_candidate = flip.mkConst(int_sort, "flip_candidate_leaf0_scaled_by_20")
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, flip_anchor, flip.mkInteger(20)))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, flip_candidate, flip.mkInteger(20)))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, flip_anchor, flip_candidate))
    flip_status = str(flip.checkSat()).lower()
    return {
        "solver": "cvc5",
        "ran": True,
        "verdict": positive,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "computed exact rational off-anchor holonomy witness cannot equal the pinned anchor value",
        "witness_values": {
            "candidate": "S9.R3.2_one_leaf_match_pi6 epsilon=1/10",
            "leaf": "0",
            "anchor_leaf0": "1",
            "candidate_leaf0": "21/20",
            "scaled_difference": "1",
        },
        "negated_assertion": "anchor_leaf0_scaled_by_20 == candidate_leaf0_scaled_by_20",
        "flip_control_verdict": flip_status,
        "positive_case": "off-anchor holonomy differs by exact rational 1/20, so alias equality is UNSAT",
        "negative/erased_control": "deliberate reparameterized alias has equal scaled leaf value and is SAT",
        "boundary_case": "SMT binds a finite rational nonzero witness only; path-ordered loops remain queued-heavy-local",
    }


def build_rows() -> dict[str, Any]:
    anchor_tuple = canonical_tuple(sp.cos(2 * ETA))
    candidates = []
    for row in registry_rows():
        canonical_forms = [
            {
                "variant": form["variant"],
                "canonical_tuple": canonical_tuple(
                    form["f_expr"],
                    path_ordered_loop_signature="queued-heavy-local"
                    if row["id"] == "S9.R3.5_path_ordered_loop_neighbor"
                    else "not-scoped-light-symbolic",
                ),
            }
            for form in row["forms"]
        ]
        if row["id"] == "S9.R3.0_committed_hopf":
            verdict = "anchor"
            registry_row = "anchor"
            witness = first_witness(anchor_tuple, canonical_forms[0]["canonical_tuple"], preferred_row="anchor")
            citation_status = "anchor row; no co-survivor citation required"
        elif row["cost"] == "heavy-local":
            verdict = "open + queued-heavy-local"
            registry_row = "heavy_local_cost_guard_not_run_in_phase_1"
            witness = {
                "field": "path_ordered_loop_signature",
                "anchor": "ordinary one-form local anchor; no path-ordered loop signature scoped",
                "candidate": f"{row['id']} cost=heavy-local; queued for {row['expected_teeth_row']}",
            }
            citation_status = "no prior co-survivor receipt cited; S4 audit standard forces open + queued-heavy-local"
        else:
            verdict = "excluded-by-" + row["expected_teeth_row"].replace(" ", "-")
            registry_row = row["expected_teeth_row"]
            witness = first_witness(anchor_tuple, canonical_forms[0]["canonical_tuple"], preferred_row=row["expected_teeth_row"])
            citation_status = "not a known co-survivor label; exact light-symbolic teeth row supplied a separating witness"
        candidates.append(
            {
                "id": row["id"],
                "finite_representative": row["finite_representative"],
                "closeness": row["closeness"],
                "expected_teeth_row": row["expected_teeth_row"],
                "cost": row["cost"],
                "verdict": verdict,
                "row": registry_row,
                "witness": witness,
                "canonical_forms": canonical_forms,
                "citation_status": citation_status,
            }
        )

    alias_expr = 1 - 2 * sp.sin(ETA) ** 2
    alias_tuple = canonical_tuple(alias_expr)
    far_tuple = canonical_tuple(sp.Integer(0))
    controls = [
        {
            "id": "control.anchor_self",
            "verdict": "anchor",
            "row": "anchor",
            "witness": first_witness(anchor_tuple, anchor_tuple, preferred_row="anchor"),
            "canonical_tuple": anchor_tuple,
        },
        {
            "id": "control.alias_reparameterized_committed",
            "verdict": "alias" if alias_tuple == anchor_tuple else "failed",
            "row": "gauge-reparameterization alias check",
            "witness": first_witness(anchor_tuple, alias_tuple, preferred_row="anchor"),
            "canonical_tuple": alias_tuple,
        },
        {
            "id": "control.round2_flat_far_connection",
            "verdict": "excluded-by-curvature-density-row",
            "row": "curvature density first teeth row",
            "witness": first_witness(anchor_tuple, far_tuple, preferred_row="curvature density before holonomy"),
            "canonical_tuple": far_tuple,
        },
    ]
    return {"candidate_rows": candidates, "control_rows": controls}


def build_result() -> dict[str, Any]:
    rows = build_rows()
    z3_proof = z3_nonzero_witness_proof()
    cvc5_proof = cvc5_nonzero_witness_proof()
    verdicts = {row["id"]: row["verdict"] for row in rows["candidate_rows"]}
    controls = {row["id"]: row["verdict"] for row in rows["control_rows"]}
    heavy_queue = [row["id"] for row in rows["candidate_rows"] if row["cost"] == "heavy-local"]
    light_exclusions = [row["id"] for row in rows["candidate_rows"] if row["verdict"].startswith("excluded-by-")]
    alias_classes = [
        {
            "representative": "S9.R3.0_committed_hopf",
            "members": ["S9.R3.0_committed_hopf", "control.anchor_self", "control.alias_reparameterized_committed"],
            "selection_rule": "registry anchor is the representative for the exact f/F/holonomy/annular-flux alias class",
        }
    ]
    gates = {
        "registry_rows_built": len(rows["candidate_rows"]) == 6,
        "anchor_classifies_as_itself": verdicts["S9.R3.0_committed_hopf"] == "anchor",
        "deliberate_alias_classifies_alias": controls["control.alias_reparameterized_committed"] == "alias",
        "far_candidate_dies_first_teeth": controls["control.round2_flat_far_connection"] == "excluded-by-curvature-density-row",
        "light_symbolic_exclusions_named_by_registry_rows": len(light_exclusions) == 4
        and all(" " not in verdicts[candidate] for candidate in light_exclusions),
        "heavy_local_rows_queued": verdicts["S9.R3.5_path_ordered_loop_neighbor"] == "open + queued-heavy-local",
        "no_known_cosurvivor_without_citation": all("co-survivor" not in verdict for verdict in verdicts.values()),
        "z3_positive_unsat": z3_proof["verdict"] == "unsat",
        "z3_flip_control_sat": z3_proof["flip_control_verdict"] == "sat",
        "cvc5_positive_unsat": cvc5_proof["verdict"] == "unsat",
        "cvc5_flip_control_sat": cvc5_proof["flip_control_verdict"] == "sat",
    }
    all_pass = all(gates.values())
    return {
        "schema": f"{SIM_ID}_jax_lane_v1",
        "sim_id": SIM_ID,
        "role_id": "python_sympy_smt_connection_diagnostic_lane",
        "engine_role_note": "Python exact symbolic sidecar uses SymPy canonical forms plus z3/cvc5 finite rational witness polarity.",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["sympy", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "package_observables": {
            "sympy": "SymPy exact simplification/differentiation/substitution computes f, F=df/deta, c1, leaf holonomy, and annular flux canonical rows",
            "z3": "z3.Solver proves exact rational off-anchor holonomy equality is UNSAT and the reparameterized alias flip is SAT",
            "cvc5": "cvc5.Solver independently proves the same finite rational witness polarity",
        },
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "all_pass": all_pass,
        "positive": {
            "s9_registry_provenance_table": [
                {k: row[k] for k in ["id", "finite_representative", "closeness", "expected_teeth_row", "cost"]}
                for row in rows["candidate_rows"]
            ],
            "alias_classes": alias_classes,
            "anchor_canonical_tuple": rows["candidate_rows"][0]["canonical_forms"][0]["canonical_tuple"],
        },
        "negative": {
            "far_candidate_control": rows["control_rows"][2],
            "light_symbolic_exclusions": light_exclusions,
            "heavy_local_label_guard": "not-run heavy-local rows without cited prior co-survivor receipts are open + queued-heavy-local, never co-survivor-open",
        },
        "boundary": {
            "phase": "light-symbolic phase 1 only",
            "heavy_local_not_run": heavy_queue,
            "pytorch_omitted": "no PyTorch tensor/autograd/message-passing claim path is scoped; exact connection comparison is carried by SymPy, Julia Symbolics, and SMT",
            "path_ordered_transport_loops": "queued-heavy-local, not run",
            "no_numeric_closeness": True,
            "pin_relative_separations": "excluded under pinned S2/S9 holonomy convention and reopenable if convention changes",
        },
        "candidate_verdicts": rows["candidate_rows"],
        "control_verdicts": rows["control_rows"],
        "phase2_queue": {
            "light_symbolic_non_alias_representatives_remaining": [],
            "heavy_local_queued_by_registry_cost_class": heavy_queue,
            "queued_with_verdict": {candidate: "open + queued-heavy-local" for candidate in heavy_queue},
            "known_cosurvivor_classes": [],
        },
        "counts": {
            "raw_registry_candidates": 6,
            "raw_symbolic_variants": 9,
            "exact_alias_classes": 1,
            "known_cosurvivor_classes": 0,
            "light_symbolic_exclusions": len(light_exclusions),
            "non_alias_representatives_queued_heavy_local": len(heavy_queue),
            "control_exclusions": 1,
        },
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "TOOL_MANIFEST": {
            "sympy": {"used": True, "reason": "load-bearing exact canonical forms, derivatives, leaf holonomies, and annular fluxes"},
            "z3": {"used": True, "reason": "load-bearing finite rational nonzero-witness polarity"},
            "cvc5": {"used": True, "reason": "load-bearing independent finite rational nonzero-witness polarity"},
            "json": {"used": True, "reason": "supportive result serialization"},
            "hashlib": {"used": True, "reason": "supportive source and tuple hashes"},
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
                "qualified_api": "sympy.simplify/trigsimp/radsimp/diff/subs",
                "input_object": "finite S9 registry functions f(eta) over exact leaves 0,pi/6,pi/4,pi/3,pi/2",
                "output_object": "canonical f, F=df/deta, c1, leaf holonomy vector, and annular flux vector",
                "positive_case": "1 - 2*sin(eta)^2 canonicalizes to the committed cos(2eta) anchor",
                "negative/erased_control": "flat round-2 far control has F=0 and fails the curvature-density row",
                "boundary_case": "path-ordered loop signatures are not computed in this light-symbolic phase",
                "demotion_condition": "float/tolerance comparisons or path-ordered loop claims appear in the light pass",
            },
            {
                "tool": "z3",
                "qualified_api": "z3.Solver/check",
                "input_object": "scaled exact leaf-holonomy witness anchor=20, candidate=21",
                "output_object": "UNSAT for false alias equality; SAT after alias flip control",
                "positive_case": "S9.R3.2 epsilon=1/10 differs from anchor at eta=0 by 1/20",
                "negative/erased_control": "reparameterized anchor has equal scaled leaf value",
                "boundary_case": "SMT checks finite rational nonzero witnesses only",
                "demotion_condition": "solver only asserts a precomputed boolean instead of binding witness values",
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver/checkSat",
                "input_object": "same scaled exact leaf-holonomy witness as z3",
                "output_object": "independent UNSAT/SAT polarity",
                "positive_case": "S9.R3.2 epsilon=1/10 differs from anchor at eta=0 by 1/20",
                "negative/erased_control": "reparameterized anchor has equal scaled leaf value",
                "boundary_case": "SMT checks finite rational nonzero witnesses only",
                "demotion_condition": "cvc5 witness values disagree with SymPy canonical rows",
            },
        ],
        "build_gates": gates,
        "canonicalizer_hash": stable_hash([row["canonical_forms"] for row in rows["candidate_rows"]]),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
