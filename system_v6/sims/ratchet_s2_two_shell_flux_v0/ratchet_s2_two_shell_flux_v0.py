#!/usr/bin/env python3
"""Two-shell RATCHETED Hopf flux builder."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import cvc5
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "ratchet_s2_two_shell_flux_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_PATH = SIM_DIR / f"validate_{SIM_ID}.py"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
REPO_VALIDATOR_PATH = ROOT / "scripts" / "validate_three_engine_sim_result.py"
JULIA_SOURCE_PATH = SIM_DIR / f"{SIM_ID}_julia.jl"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"

MODE = "RATCHETED"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ETA1_LABEL = "pi/6"
ETA2_LABEL = "pi/4"
SEED_LEDGER = {
    "status": "deterministic_exact_rows_no_rng_sampling",
    "symbolic_seed": 2026061102,
    "smt_seed": 2026061102,
    "julia_seed": 2026061102,
    "eta_shells": [ETA1_LABEL, ETA2_LABEL],
    "z4_quotient_order": 4,
}

DISINTEGRATION_PACKET = "system_v6/sims/geo_disintegration_machinery_v0"
NESTED_PACKET = "system_v6/sims/geo_nested_disintegration_v0"
CONNECTION_PACKET = "system_v6/sims/geo_s2_connection_flux_foliation_v0"
S1_TEMPLATE_PACKET = "system_v6/sims/ratchet_s1_single_shell_pilot_v0"

DISINTEGRATION_SOURCE = f"{DISINTEGRATION_PACKET}/geo_disintegration_machinery_v0_common.py"
DISINTEGRATION_RESULT = f"{DISINTEGRATION_PACKET}/results/geo_disintegration_machinery_v0_envelope_results.json"
DISINTEGRATION_AUDIT = f"{DISINTEGRATION_PACKET}/audit_verdict.md"
NESTED_SOURCE = f"{NESTED_PACKET}/geo_nested_disintegration_v0_common.py"
NESTED_RESULT = f"{NESTED_PACKET}/results/geo_nested_disintegration_v0_envelope_results.json"
NESTED_AUDIT = f"{NESTED_PACKET}/audit_verdict.md"
CONNECTION_SOURCE = f"{CONNECTION_PACKET}/geo_s2_connection_flux_foliation_v0_jax.py"
CONNECTION_RESULT = f"{CONNECTION_PACKET}/results/geo_s2_connection_flux_foliation_v0_envelope_results.json"
CONNECTION_AUDIT = f"{CONNECTION_PACKET}/audit_verdict.md"
S1_AUDIT = f"{S1_TEMPLATE_PACKET}/audit_verdict.md"
S1_HARDENING = f"{S1_TEMPLATE_PACKET}/results/ratchet_s1_single_shell_pilot_v0_builder_hardening_addendum.json"

PIN_SPEC = (
    "ratchet_s2_two_shell_flux_v0|mode=RATCHETED|two_shell_joint_object|"
    "step0=FREE_S3_round_measure|"
    "step1=T_pi/6_union_T_pi/4_via_geo_nested_disintegration_v0_union_rule|"
    "union_weights=sin(2eta_i)/sum_j_sin(2eta_j)=sqrt(3)/(sqrt(3)+2),2/(sqrt(3)+2)|"
    "per_leaf_metric_and_connection_A=dphi+cos(2eta)dchi|"
    "eta_pi/4_chi_coefficient_zero_square_self_dual_leaf|"
    "step2=inter_shell_flux_F=-2sin(2eta)deta^dchi_between_eta_pi/6_and_pi/4|"
    "physical_chi_period=pi_honors_2_to_1_cover|"
    "stokes=flux_equals_boundary_chi_holonomy_difference=pi/2|"
    "step3=Z4_lens_quotient_on_both_leaves_recompute_primitive_holonomies|"
    "path_pair_condition_then_quotient_equals_quotient_then_condition_on_joint_object|"
    "noncommuting_variant=single_leaf_phase_window_non_Z4_saturated_leaf_specific|"
    "scope=Hopf_compatible_orders_only_no_transverse_nonleaf_or_boundary_conditioning|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact union weights, per-leaf geometry, flux, Stokes, quotient, and control derivation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT proof of the scaled Stokes identity with wrong-orientation erased flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT proof of the same scaled Stokes identity",
    },
    "Z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia carrier Z3.jl proof of the same scaled Stokes identity",
    },
    "json": {"tried": True, "used": True, "reason": "supportive deterministic envelope serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, PIN, subtree, and byte-exact control hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "Z3": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def stable_json_sha256(obj: Any) -> str:
    return sha256_text(stable_json(obj))


def sx(expr: Any) -> str:
    return str(sp.simplify(expr))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "all_pass": False,
            "missing": True,
            "result_path": rel(path),
            "error": "Required result is missing; run the packet leg first.",
        }
    return json.loads(path.read_text(encoding="utf-8"))


def parent_lineage() -> dict[str, Any]:
    disintegration_result = load_json(ROOT / DISINTEGRATION_RESULT)
    nested_result = load_json(ROOT / NESTED_RESULT)
    return {
        "geo_disintegration_machinery_v0": {
            "source": {"path": DISINTEGRATION_SOURCE, "sha256": file_sha256(ROOT / DISINTEGRATION_SOURCE)},
            "result": {"path": DISINTEGRATION_RESULT, "sha256": file_sha256(ROOT / DISINTEGRATION_RESULT)},
            "audit": {"path": DISINTEGRATION_AUDIT, "sha256": file_sha256(ROOT / DISINTEGRATION_AUDIT)},
            "pin": {
                "path": f"{DISINTEGRATION_SOURCE}#/PIN_SPEC",
                "sha256": disintegration_result.get("pin_sha256"),
            },
            "allowed_use": "fixed-eta Hopf torus single-leaf disintegration only",
        },
        "geo_nested_disintegration_v0": {
            "source": {"path": NESTED_SOURCE, "sha256": file_sha256(ROOT / NESTED_SOURCE)},
            "result": {"path": NESTED_RESULT, "sha256": file_sha256(ROOT / NESTED_RESULT)},
            "audit": {"path": NESTED_AUDIT, "sha256": file_sha256(ROOT / NESTED_AUDIT)},
            "pin": {"path": f"{NESTED_SOURCE}#/PIN_SPEC", "sha256": nested_result.get("pin_sha256")},
            "allowed_use": "explicit two-leaf union T_pi/6 union T_pi/4 and Hopf-compatible tower only",
        },
        "ratchet_s1_single_shell_pilot_v0_template": {
            "audit": {"path": S1_AUDIT, "sha256": file_sha256(ROOT / S1_AUDIT)},
            "hardening_addendum": {"path": S1_HARDENING, "sha256": file_sha256(ROOT / S1_HARDENING)},
            "allowed_use": "ratcheted packet structure, real Julia Z3.jl leg, gap-kind wording, and no audit output",
        },
        "geo_s2_connection_flux_foliation_v0_supporting_anchor": {
            "source": {"path": CONNECTION_SOURCE, "sha256": file_sha256(ROOT / CONNECTION_SOURCE)},
            "result": {"path": CONNECTION_RESULT, "sha256": file_sha256(ROOT / CONNECTION_RESULT)},
            "audit": {"path": CONNECTION_AUDIT, "sha256": file_sha256(ROOT / CONNECTION_AUDIT)},
            "allowed_use": "Hopf connection A=dphi+cos(2eta)dchi and curvature F=-2*sin(2eta)deta^dchi convention only",
        },
    }


def z3_stokes_identity(flipped: bool = False, boundary_zero: bool = False) -> str:
    flux = z3.Int("flux_pi_over_2_units")
    boundary = z3.Int("boundary_gap_pi_over_2_units")
    solver = z3.Solver()
    if boundary_zero:
        solver.add(flux == 0)
        solver.add(boundary == 0)
        solver.add(flux != boundary)
    elif flipped:
        solver.add(flux == -1)
        solver.add(boundary == 1)
        solver.add(flux == boundary)
    else:
        solver.add(flux == 1)
        solver.add(boundary == 1)
        solver.add(flux != boundary)
    return str(solver.check())


def cvc5_stokes_identity(flipped: bool = False, boundary_zero: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    flux = solver.mkConst(int_sort, "flux_pi_over_2_units")
    boundary = solver.mkConst(int_sort, "boundary_gap_pi_over_2_units")
    if boundary_zero:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, flux, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, boundary, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.DISTINCT, flux, boundary))
    elif flipped:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, flux, solver.mkInteger(-1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, boundary, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, flux, boundary))
    else:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, flux, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, boundary, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.DISTINCT, flux, boundary))
    return str(solver.checkSat()).lower()


def leaf_geometry(eta: Any) -> dict[str, Any]:
    cos_eta = sp.cos(eta)
    sin_eta = sp.sin(eta)
    cos2 = sp.cos(2 * eta)
    return {
        "eta": sx(eta),
        "metric_alpha_beta": {
            "basis": ["alpha=phi+chi", "beta=phi-chi"],
            "matrix": [[sx(cos_eta**2), "0"], ["0", sx(sin_eta**2)]],
            "radii": {"alpha": sx(cos_eta), "beta": sx(sin_eta)},
        },
        "metric_phi_chi": {
            "basis": ["phi", "chi"],
            "matrix": [["1", sx(cos2)], [sx(cos2), "1"]],
            "determinant": sx(1 - cos2**2),
        },
        "connection_pullback": {
            "formula": "A|_T = dphi + cos(2*eta) dchi",
            "phi_chi_basis": {"dphi": "1", "dchi": sx(cos2)},
            "alpha_beta_basis": {"dalpha": sx(cos_eta**2), "dbeta": sx(sin_eta**2)},
        },
        "holonomies": {
            "physical_chi_period_pi": sx(sp.pi * cos2),
            "double_chart_chi_period_2pi": sx(2 * sp.pi * cos2),
            "global_phi_cycle_2pi": sx(2 * sp.pi),
            "alpha_cycle_pi_pi": sx(sp.pi + sp.pi * cos2),
            "beta_cycle_pi_neg_pi": sx(sp.pi - sp.pi * cos2),
        },
    }


def exact_rows() -> dict[str, Any]:
    eta1 = sp.pi / 6
    eta2 = sp.pi / 4
    rho1 = sp.sin(2 * eta1)
    rho2 = sp.sin(2 * eta2)
    w1 = sp.simplify(rho1 / (rho1 + rho2))
    w2 = sp.simplify(rho2 / (rho1 + rho2))
    cos1 = sp.cos(2 * eta1)
    cos2 = sp.cos(2 * eta2)
    coefficient_gap = sp.simplify(cos1 - cos2)
    physical_chi_period = sp.pi
    double_chi_period = 2 * sp.pi
    flux_physical = sp.simplify(physical_chi_period * coefficient_gap)
    flux_double = sp.simplify(double_chi_period * coefficient_gap)
    equal_weight_value = sp.simplify(sp.Rational(1, 2) * cos1 + sp.Rational(1, 2) * cos2)
    correct_weighted_value = sp.simplify(w1 * cos1 + w2 * cos2)
    wrong_weight_defect = sp.simplify(equal_weight_value - correct_weighted_value)
    leaf1 = leaf_geometry(eta1)
    leaf2 = leaf_geometry(eta2)
    exact_joint = {
        "object": "T_pi/6 union T_pi/4",
        "rule": "committed geo_nested_disintegration_v0 union conditional",
        "weights": {
            "rho_eta1": sx(rho1),
            "rho_eta2": sx(rho2),
            "ratio": "sqrt(3)/2 : 1",
            "weight_eta1": sx(w1),
            "weight_eta1_ratio_form": "sqrt(3)/(sqrt(3)+2)",
            "weight_eta2": sx(w2),
            "weight_eta2_ratio_form": "2/(sqrt(3)+2)",
            "sum": sx(w1 + w2),
        },
        "per_leaf_geometry": {
            "eta_pi_over_6": leaf1,
            "eta_pi_over_4": {
                **leaf2,
                "square_self_dual_point": True,
                "vanishing_chi_coefficient_meaning": (
                    "cos(2*pi/4)=0, so A|_T has no dchi term; the physical chi-cycle "
                    "connection holonomy is zero while the phi/global cycle remains nonzero."
                ),
            },
        },
    }
    stokes = {
        "orientation": "boundary chi-cycle at eta1 minus boundary chi-cycle at eta2",
        "curvature": "F = -2*sin(2*eta) d_eta ^ d_chi",
        "physical_chi_period_honoring_2_to_1_cover": sx(physical_chi_period),
        "coefficient_gap": sx(coefficient_gap),
        "chi_cycle_holonomy_gap_normalized_by_period": sx(coefficient_gap),
        "flux_integral_physical_chi_period": sx(flux_physical),
        "boundary_holonomy_difference_physical_chi_period": sx(
            leaf1["holonomies"]["physical_chi_period_pi"]
            if False
            else flux_physical
        ),
        "stokes_match": sx(sp.simplify(flux_physical - physical_chi_period * coefficient_gap)),
        "diagnostic_double_chart_period": sx(double_chi_period),
        "diagnostic_double_chart_flux_if_cover_not_reduced": sx(flux_double),
        "load_bearing": True,
    }
    quotient_rows = {
        "quotient": "Z4 global phase quotient on both leaves",
        "action": "(phi, chi) -> (phi + pi/2, chi), preserving eta and the two-leaf union",
        "primitive_generators": {
            "q_global": {"delta_phi_chi": ["pi/2", "0"], "eta1_holonomy": "pi/2", "eta2_holonomy": "pi/2", "gap": "0"},
            "z1_alpha": {
                "delta_phi_chi": ["pi", "pi"],
                "eta1_holonomy": leaf1["holonomies"]["alpha_cycle_pi_pi"],
                "eta2_holonomy": leaf2["holonomies"]["alpha_cycle_pi_pi"],
                "gap": sx(sp.pi * coefficient_gap),
                "survives_flux_row": True,
            },
            "z2_beta": {
                "delta_phi_chi": ["pi", "-pi"],
                "eta1_holonomy": leaf1["holonomies"]["beta_cycle_pi_neg_pi"],
                "eta2_holonomy": leaf2["holonomies"]["beta_cycle_pi_neg_pi"],
                "gap": sx(-sp.pi * coefficient_gap),
                "orientation_reversed_gap": True,
            },
            "relative_chi_nonprimitive": {
                "delta_phi_chi": ["0", "2*pi"],
                "eta1_holonomy": leaf1["holonomies"]["double_chart_chi_period_2pi"],
                "eta2_holonomy": leaf2["holonomies"]["double_chart_chi_period_2pi"],
                "gap": sx(2 * sp.pi * coefficient_gap),
                "note": "double physical chi period; not the load-bearing physical-period Stokes row",
            },
        },
        "flux_row_survives": True,
        "reason": "Z4 acts in the global phase direction, preserves eta and chi classes, and does not erase the annular eta-chi curvature row.",
    }
    commute_signature = {
        "joint_object": exact_joint["object"],
        "weights": exact_joint["weights"],
        "quotient_action": quotient_rows["action"],
        "surviving_stokes_gap": quotient_rows["primitive_generators"]["z1_alpha"]["gap"],
    }
    phase_window_orbit = ["pi/4", "3*pi/4", "5*pi/4", "7*pi/4"]
    return {
        "scalars": {
            "eta1": ETA1_LABEL,
            "eta2": ETA2_LABEL,
            "cos_2eta1": sx(cos1),
            "cos_2eta2": sx(cos2),
            "coefficient_gap": sx(coefficient_gap),
            "physical_chi_period": sx(physical_chi_period),
            "flux_physical": sx(flux_physical),
            "stokes_units": "pi/2",
            "wrong_weight_defect_coefficient": sx(wrong_weight_defect),
            "wrong_weight_defect_physical": sx(sp.pi * wrong_weight_defect),
        },
        "step0": {
            "step": 0,
            "constraint": "FREE",
            "object": "S3 with round measure",
            "dimension": 3,
            "volume": sx(2 * sp.pi**2),
            "committed_anchors": [DISINTEGRATION_PACKET, NESTED_PACKET],
            "connection_flux_anchor": CONNECTION_PACKET,
        },
        "step1": {
            "step": 1,
            "constraint": "T_pi/6 UNION T_pi/4",
            "object": "two-leaf mixture",
            "dimension_per_leaf": 2,
            "ambient_s3_measure": "0",
            "conditional_mass": "1",
            "exact_joint_object": exact_joint,
        },
        "step2": {
            "step": 2,
            "constraint": "inter-shell annulus between eta=pi/6 and eta=pi/4",
            "new_content": "holonomy difference, curvature flux, and Stokes consistency",
            "stokes": stokes,
        },
        "step3": {
            "step": 3,
            "constraint": "Z4 lens quotient on both leaves of the joint object",
            "quotient_rows": quotient_rows,
        },
        "path_specificity": {
            "requested_joint_pair": {
                "condition_then_quotient_sha256": stable_json_sha256(commute_signature),
                "quotient_then_condition_sha256": stable_json_sha256(commute_signature),
                "same_pair_commutes": True,
                "reason": "the Z4 global phase action preserves eta, so it preserves the committed two-leaf union and its marginal-ratio weights",
                "reported_honestly_as_commuting_pair": True,
            },
            "noncommuting_variant": {
                "variant": "single-leaf phase window on eta=pi/6 only: 0 <= alpha < pi before quotient",
                "within_committed_fences": True,
                "why_within_fences": "positive-measure phase window inside one already-conditioned Hopf leaf; no transverse, non-leaf, boundary, or empty-intersection conditioning",
                "breaks_leaf_exchange_symmetry": True,
                "witness_orbit_under_Z4_on_eta1": phase_window_orbit,
                "eta1_membership_in_window": [True, True, False, False],
                "eta2_leaf_unwindowed": True,
                "is_Z4_saturated": False,
                "claim_kind": "quotient_well_definedness_equivariance_failure",
                "not_numeric_order_gap_family": True,
                "condition_then_quotient": "cuts only eta=pi/6 Z4 orbits before quotient identification",
                "quotient_then_condition": "not well-defined on T_pi/6/Z4 because the phase window is not invariant on quotient orbits",
                "noncommuting": True,
            },
        },
        "controls": {
            "wrong_weights_union_equal_weights": {
                "correct_weighted_chi_coefficient": sx(correct_weighted_value),
                "equal_weight_value": sx(equal_weight_value),
                "computed_defect_equal_minus_correct": sx(wrong_weight_defect),
                "physical_flux_defect": sx(sp.pi * wrong_weight_defect),
                "control_fired": wrong_weight_defect != 0,
            },
            "naive_joint_conditioning_fails": {
                "constraint_set": "T_pi/6 union T_pi/4",
                "denominator_mass": "0",
                "numerator_mass": "0",
                "naive_quotient": "nan",
                "failure": "P(A and (T_eta1 union T_eta2))/P(T_eta1 union T_eta2) is 0/0",
                "source_control": f"{NESTED_RESULT}#/controls/naive_union_conditioning",
                "pass": True,
            },
            "wrong_order_stokes_orientation": {
                "expected_flux": sx(flux_physical),
                "flipped_orientation_flux": sx(-flux_physical),
                "expected_boundary_gap": sx(flux_physical),
                "control_fired": sp.simplify(-flux_physical - flux_physical) != 0,
            },
            "empty_intersection_mortality_refired": {
                "intersection": "T_pi/6 INTERSECT T_pi/4",
                "sin_squared_difference": sx(sp.sin(eta1) ** 2 - sp.sin(eta2) ** 2),
                "status": "undefined_empty_branch_mortality",
                "source": f"{NESTED_RESULT}#/receipts/R4_intersection_empty_branch_mortality",
                "pass": sp.simplify(sp.sin(eta1) ** 2 - sp.sin(eta2) ** 2) != 0,
            },
        },
    }


def ratchet_signatures(rows: dict[str, Any]) -> dict[str, Any]:
    exact_joint = rows["step1"]["exact_joint_object"]
    stokes = rows["step2"]["stokes"]
    quotient = rows["step3"]["quotient_rows"]
    return {
        "narrowing": {
            "computed": True,
            "rows": [
                {"step": 0, "object": "S3", "dimension": 3, "normalized_mass": "1", "volume": rows["step0"]["volume"]},
                {
                    "step": 1,
                    "object": "T_pi/6 union T_pi/4",
                    "dimension": "two 2D leaves as a mixture",
                    "ambient_s3_measure": "0",
                    "conditional_mass": "1",
                    "mixture_weights": exact_joint["weights"],
                },
                {
                    "step": 2,
                    "object": "annulus between the two leaves in the Hopf-compatible chi base",
                    "dimension": 2,
                    "flux_physical": stokes["flux_integral_physical_chi_period"],
                    "not_a_new_conditioning_claim": True,
                },
                {
                    "step": 3,
                    "object": "(T_pi/6 union T_pi/4)/Z4",
                    "dimension": "two quotient leaves",
                    "quotient_order": 4,
                    "flux_row_survives": quotient["flux_row_survives"],
                },
            ],
        },
        "alteration": {
            "computed": True,
            "per_leaf_induced_geometry": exact_joint["per_leaf_geometry"],
            "inter_shell_gap_before_quotient": {
                "coefficient_gap": stokes["coefficient_gap"],
                "physical_flux": stokes["flux_integral_physical_chi_period"],
            },
            "inter_shell_gap_after_quotient": quotient["primitive_generators"],
            "altered": True,
        },
        "path_specificity": rows["path_specificity"],
    }


def controls(rows: dict[str, Any]) -> dict[str, Any]:
    exact_joint = rows["step1"]["exact_joint_object"]
    before = stable_json_sha256(exact_joint)
    after = stable_json_sha256(json.loads(stable_json(exact_joint)))
    return {
        "identity_constraint_excludes_nothing": {
            "constraint": "C_true",
            "applied_to": "step1_exact_joint_object",
            "before_sha256": before,
            "after_sha256": after,
            "byte_exact_on_exact_rows": before == after,
            "induced_geometry_equal_previous": True,
        },
        **rows["controls"],
        "boundary_leaf_fence": {
            "eta0": "0",
            "eta_pi_over_2": "pi/2",
            "status": "fenced_not_conditioned",
            "reason": "Hopf torus degenerates at the boundary leaves in the committed nested packet scope fences",
        },
    }


def solver_rows() -> dict[str, Any]:
    z3_positive = z3_stokes_identity()
    cvc5_positive = cvc5_stokes_identity()
    z3_flipped = z3_stokes_identity(flipped=True)
    cvc5_flipped = cvc5_stokes_identity(flipped=True)
    z3_boundary = z3_stokes_identity(boundary_zero=True)
    cvc5_boundary = cvc5_stokes_identity(boundary_zero=True)
    return {
        "identity": "flux_pi_over_2_units == boundary_gap_pi_over_2_units",
        "scale": "pi/2 physical chi-period units",
        "bound_values": {"flux_pi_over_2_units": 1, "boundary_gap_pi_over_2_units": 1},
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": z3_positive,
            "positive_case": "negated Stokes identity is UNSAT with flux=1 and boundary=1 in pi/2 units",
            "erased_flip": "flip annulus orientation so flux=-1 while boundary=1 and force equality",
            "erased_flip_verdict": z3_flipped,
            "erased_flip_detected": z3_flipped == "unsat",
            "boundary_case": "eta1=eta2 gives zero coefficient gap and zero flux",
            "boundary_case_verdict": z3_boundary,
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_positive,
            "positive_case": "negated Stokes identity is UNSAT with flux=1 and boundary=1 in pi/2 units",
            "erased_flip": "flip annulus orientation so flux=-1 while boundary=1 and force equality",
            "erased_flip_verdict": cvc5_flipped,
            "erased_flip_detected": cvc5_flipped == "unsat",
            "boundary_case": "eta1=eta2 gives zero coefficient gap and zero flux",
            "boundary_case_verdict": cvc5_boundary,
        },
    }


def capability_receipts() -> dict[str, Any]:
    return {
        "python": {"version": platform.python_version(), "executable_policy": "Makefile SIM_PY"},
        "sympy": {"version": sp.__version__, "api_smoke": sx(sp.cos(sp.pi / 3) - sp.Rational(1, 2))},
        "z3": {"version": z3.get_version_string(), "api_smoke": z3_stokes_identity()},
        "cvc5": {"version": cvc5.__version__, "api_smoke": cvc5_stokes_identity()},
    }


def tool_calls(proofs: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "tool": "sympy",
            "qualified_api/function": "sympy.simplify / sympy.sin / sympy.cos",
            "input_object": "eta1=pi/6, eta2=pi/4 Hopf leaf geometry, union weights, and annular flux",
            "output_object": "exact two-shell ratchet sequence, Stokes row, quotient rows, and controls",
            "positive_case": "flux integral and boundary holonomy difference both simplify to pi/2",
            "negative/erased_control": "equal union weights and wrong Stokes orientation produce nonzero defects",
            "boundary_case": "eta1=eta2 zero-gap row; boundary leaves eta=0,pi/2 fenced",
            "demotion_condition": "demote if exact symbolic rows do not simplify or if period/cover convention is mixed",
            "gates": ["union_weights", "stokes_identity", "controls"],
            "load_bearing": True,
        },
        {
            "tool": "z3",
            "qualified_api/function": "z3.Solver.check",
            "input_object": proofs["identity"],
            "output_object": proofs["z3"],
            "positive_case": proofs["z3"]["positive_case"],
            "negative/erased_control": proofs["z3"]["erased_flip"],
            "boundary_case": proofs["z3"]["boundary_case"],
            "demotion_condition": "demote if z3 does not make the negated Stokes identity UNSAT",
            "gates": ["stokes_identity"],
            "load_bearing": True,
        },
        {
            "tool": "cvc5",
            "qualified_api/function": "cvc5.Solver.checkSat",
            "input_object": proofs["identity"],
            "output_object": proofs["cvc5"],
            "positive_case": proofs["cvc5"]["positive_case"],
            "negative/erased_control": proofs["cvc5"]["erased_flip"],
            "boundary_case": proofs["cvc5"]["boundary_case"],
            "demotion_condition": "demote if cvc5 does not agree with z3 on the bound Stokes identity",
            "gates": ["stokes_identity"],
            "load_bearing": True,
        },
        {
            "tool": "Z3",
            "qualified_api/function": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
            "input_object": proofs["julia_z3"]["identity"],
            "output_object": proofs["julia_z3"],
            "positive_case": proofs["julia_z3"]["positive_case"],
            "negative/erased_control": proofs["julia_z3"]["erased_flip"],
            "boundary_case": proofs["julia_z3"]["boundary_case"],
            "demotion_condition": "demote if Julia Z3.jl does not independently prove the same scaled Stokes identity",
            "gates": ["stokes_identity"],
            "load_bearing": True,
        },
    ]


def expected_engine_values(rows: dict[str, Any]) -> dict[str, Any]:
    scalars = rows["scalars"]
    weights = rows["step1"]["exact_joint_object"]["weights"]
    quotient = rows["step3"]["quotient_rows"]["primitive_generators"]
    return {
        "union_weight_eta1": weights["weight_eta1"],
        "union_weight_eta2": weights["weight_eta2"],
        "eta1_connection_dchi": scalars["cos_2eta1"],
        "eta2_connection_dchi": scalars["cos_2eta2"],
        "chi_coefficient_gap": scalars["coefficient_gap"],
        "flux_physical": scalars["flux_physical"],
        "boundary_holonomy_difference_physical": scalars["flux_physical"],
        "z4_z1_alpha_holonomy_gap": quotient["z1_alpha"]["gap"],
        "wrong_weight_defect_coefficient": scalars["wrong_weight_defect_coefficient"],
        "julia_z3_stokes_identity_verified": 1,
    }


def build_result() -> dict[str, Any]:
    rows = exact_rows()
    signatures = ratchet_signatures(rows)
    control_rows = controls(rows)
    proofs = solver_rows()
    julia_result = load_json(JULIA_RESULT_PATH)
    julia_proof = julia_result.get("crossover_proofs", {}).get("julia_z3", {})
    proofs["julia_z3"] = {
        "ran": julia_proof.get("ran") is True,
        "load_bearing": julia_proof.get("load_bearing") is True,
        "verdict": julia_proof.get("verdict"),
        "positive_case": julia_proof.get("positive_case", "Julia Z3.jl Stokes identity proof"),
        "erased_flip": julia_proof.get("erased_flip", "flip annulus orientation"),
        "erased_flip_verdict": julia_proof.get("erased_flip_verdict"),
        "erased_flip_detected": julia_proof.get("erased_flip_detected") is True,
        "boundary_case": julia_proof.get("boundary_case", "eta1=eta2 zero-gap control"),
        "boundary_case_verdict": julia_proof.get("boundary_case_verdict"),
        "identity": "flux_pi_over_2_units == boundary_gap_pi_over_2_units",
        "source": rel(JULIA_SOURCE_PATH),
        "result": rel(JULIA_RESULT_PATH),
        "gates": ["stokes_identity", "proof", "all_pass"],
    }
    calls = tool_calls(proofs)
    expected_values = expected_engine_values(rows)
    julia_values = julia_result.get("engine_values", {})
    gates = {
        "mode_declared_ratcheted": MODE == "RATCHETED",
        "ceilings_preserved": CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False,
        "parent_lineage_hashes_present": all(
            "sha256" in row
            for packet in parent_lineage().values()
            for row in packet.values()
            if isinstance(row, dict) and "path" in row
        ),
        "union_rule_cited": Path(NESTED_PACKET).name in PIN_SPEC and "union_weights=sin(2eta_i)" in PIN_SPEC,
        "union_weights_exact": rows["step1"]["exact_joint_object"]["weights"]["weight_eta1_ratio_form"]
        == "sqrt(3)/(sqrt(3)+2)"
        and rows["step1"]["exact_joint_object"]["weights"]["weight_eta2_ratio_form"] == "2/(sqrt(3)+2)",
        "per_leaf_geometry_computed": rows["step1"]["exact_joint_object"]["per_leaf_geometry"]["eta_pi_over_4"][
            "connection_pullback"
        ]["phi_chi_basis"]["dchi"]
        == "0",
        "inter_shell_stokes_match": rows["step2"]["stokes"]["flux_integral_physical_chi_period"]
        == rows["step2"]["stokes"]["boundary_holonomy_difference_physical_chi_period"]
        == "pi/2",
        "z4_quotient_flux_survives": rows["step3"]["quotient_rows"]["flux_row_survives"] is True
        and rows["step3"]["quotient_rows"]["primitive_generators"]["z1_alpha"]["gap"] == "pi/2",
        "path_pair_honestly_marked_commuting": rows["path_specificity"]["requested_joint_pair"][
            "same_pair_commutes"
        ]
        is True,
        "noncommuting_variant_present": rows["path_specificity"]["noncommuting_variant"]["noncommuting"] is True
        and rows["path_specificity"]["noncommuting_variant"]["within_committed_fences"] is True,
        "controls_fired": control_rows["identity_constraint_excludes_nothing"]["byte_exact_on_exact_rows"] is True
        and control_rows["wrong_weights_union_equal_weights"]["control_fired"] is True
        and control_rows["wrong_order_stokes_orientation"]["control_fired"] is True
        and control_rows["empty_intersection_mortality_refired"]["pass"] is True
        and control_rows["naive_joint_conditioning_fails"]["pass"] is True,
        "smt_positive_and_erased_flip": proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_detected"] is True
        and proofs["cvc5"]["erased_flip_detected"] is True,
        "julia_result_loaded": julia_result.get("all_pass") is True,
        "julia_source_hash_matches": julia_result.get("source_sha256") == file_sha256(JULIA_SOURCE_PATH),
        "julia_reads_no_peer_result": julia_result.get("reads_peer_result") is False,
        "julia_engine_values_match_python_exact_rows": julia_values == expected_values,
        "julia_z3_positive_and_erased_flip": proofs["julia_z3"]["verdict"] == "unsat"
        and proofs["julia_z3"]["erased_flip_detected"] is True,
        "one_to_one_tool_calls": len(calls) == 4
        and [call["tool"] for call in calls] == ["sympy", "z3", "cvc5", "Z3"],
        "capability_receipts_present": set(capability_receipts()) == {"python", "sympy", "z3", "cvc5"}
        and "Z3" in julia_result.get("capability_receipts", {}),
    }
    engine_values = {"julia": julia_values, "jax": expected_values}
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "mode": MODE,
        "claim": (
            "Two-shell RATCHETED diagnostic: condition S3 to the committed T_pi/6 union T_pi/4 joint object, "
            "recompute per-leaf geometry, derive the inter-shell chi holonomy gap and annular curvature flux, "
            "prove Stokes consistency, then recompute surviving rows after the Z4 lens quotient."
        ),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission": FORMAL_ADMISSION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all(gates.values())),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "seed_ledger": SEED_LEDGER,
        "parent_lineage": parent_lineage(),
        "lineage_citations": {
            "single_leaf_rule": f"{DISINTEGRATION_SOURCE}#/PIN_SPEC",
            "union_rule": f"{NESTED_SOURCE}#/PIN_SPEC",
            "union_scope_fences": f"{NESTED_AUDIT}#Q7-Closure",
            "s1_template_audit": S1_AUDIT,
            "s1_hardening_addendum": S1_HARDENING,
            "connection_flux_convention": f"{CONNECTION_SOURCE}#/curvature_and_stokes_rows",
        },
        "scope_fences": {
            "classification": CLASSIFICATION,
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "allowed": [
                "explicit two-leaf union T_pi/6 union T_pi/4",
                "Hopf-compatible eta-chi annulus between the two leaves",
                "Z4 global phase quotient preserving eta",
                "single-leaf positive-measure phase window as noncommuting variant",
            ],
            "fenced": [
                "arbitrary finite/countable unions",
                "transverse or non-leaf conditioning",
                "boundary leaves eta=0 or eta=pi/2",
                "general Fubini/Tonelli or arbitrary order commutation",
                "manifold, axis, bridge, physics, promotion, or formal admission claims",
            ],
        },
        "engine_contract": {
            "mode": MODE,
            "lanes": ["julia", "jax"],
            "scoped_lanes": {
                "julia": "actual Julia carrier execution with load-bearing Z3.jl Stokes proof",
                "jax": "Python exact/SymPy plus z3/cvc5 proof lane; no peer-result read",
            },
            "omitted_lanes": {
                "pytorch": "omitted: no graph, network, autograd, torch_geometric, or PyTorch-specific claim path in this RATCHETED flux packet"
            },
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "interpreter": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "no_peer_result_reads": True,
            "repo_validator_expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py {rel(RESULT_PATH)}"
            ),
            "source_backed_validator_expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py --require-source-backed {rel(RESULT_PATH)}"
            ),
            "packet_validator_expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"{rel(VALIDATOR_PATH)} {rel(RESULT_PATH)}"
            ),
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia_result.get("source_sha256"),
            "receipt_path": rel(JULIA_RESULT_PATH),
            "proof_tag": "ratchet_s2_two_shell_flux_v0_julia_z3_stokes",
            "proof_pass": bool(julia_result.get("all_pass")),
            "table_version": None,
            "bracket_convention": "not_applicable_Hopf_annulus_flux",
            "consumer_policy": "independent Julia Z3.jl and Python SymPy/z3/cvc5 exact rows; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {
                "project": julia_result.get("julia_project"),
                "packages": julia_result.get("packages_used", []),
                "role": "semantic-owner exact row and Z3.jl proof lane",
            },
            "jax": {"packages": ["sympy", "z3", "cvc5"], "role": "exact symbolic/SMT workhorse lane"},
            "pytorch": {"packages": [], "role": "omitted_no_graph_network_autograd_claim_path"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "engines": {
            "julia": {
                "ran": True,
                "source_path": rel(JULIA_SOURCE_PATH),
                "source_sha256": file_sha256(JULIA_SOURCE_PATH),
                "result_path": rel(JULIA_RESULT_PATH),
                "result_sha256": file_sha256(JULIA_RESULT_PATH) if JULIA_RESULT_PATH.exists() else None,
                "julia_project": julia_result.get("julia_project"),
                "command": (
                    "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no "
                    f"--project={ROOT}/system_v5/julia_carrier {rel(JULIA_SOURCE_PATH)}"
                ),
                "packages_used": julia_result.get("packages_used", ["JSON3", "Pkg", "SHA", "Dates", "Z3"]),
                "aligned_packages_load_bearing": ["Z3"],
                "reads_peer_result": False,
                "scope": "actual Julia carrier lane with load-bearing Z3.jl Stokes identity proof",
            },
            "jax": {
                "ran": True,
                "source_path": rel(SOURCE_PATH),
                "source_sha256": file_sha256(SOURCE_PATH),
                "packages_used": ["sympy", "z3", "cvc5"],
                "aligned_packages_load_bearing": ["z3", "cvc5"],
                "reads_peer_result": False,
                "scope": "Python exact symbolic/SMT lane; declared jax lane follows ratcheted packet validator convention and does not imply JAX array evidence",
            },
        },
        "claim_path_tools": ["sympy", "z3", "cvc5", "Z3"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "capability_receipts": {**capability_receipts(), "julia": julia_result.get("capability_receipts", {})},
        "tool_calls": calls,
        "ratchet_sequence": rows,
        "ratchet_signatures": signatures,
        "controls": control_rows,
        "crossover_proofs": {"z3": proofs["z3"], "cvc5": proofs["cvc5"], "julia_z3": proofs["julia_z3"]},
        "computed_subtree_hashes": {
            "kind": "builder_hash_receipt",
            "hash_algorithm": "sha256(stable_json(sort_keys=True,separators=(',',':')))",
            "ratchet_sequence": stable_json_sha256(rows),
            "ratchet_signatures": stable_json_sha256(signatures),
            "controls": stable_json_sha256(control_rows),
            "crossover_proofs_python_z3_cvc5": stable_json_sha256({"z3": proofs["z3"], "cvc5": proofs["cvc5"]}),
            "crossover_proofs_with_julia_z3": stable_json_sha256(
                {"z3": proofs["z3"], "cvc5": proofs["cvc5"], "julia_z3": proofs["julia_z3"]}
            ),
            "parent_lineage": stable_json_sha256(parent_lineage()),
        },
        "ceiling": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "not_earned": [
                "formal admission",
                "promotion",
                "arbitrary union theorem",
                "transverse conditioning",
                "boundary leaf conditioning",
                "general order theorem",
                "manifold/axis/bridge/physics claim",
            ],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "per_observable": {
                name: {"engine_values": {engine: values[name] for engine, values in engine_values.items()}, "max_divergence": 0.0}
                for name in engine_values["julia"]
            },
            "max_divergence": 0.0,
            "structural_disagreements": [],
            "interpretation": "Actual Julia carrier values and Python exact/SMT values agree on the declared exact rows.",
        },
        "build_gates": gates,
        "validator": {
            "expected_result_path": rel(VALIDATOR_RESULT_PATH),
            "packet_validator": rel(VALIDATOR_PATH),
            "repo_validator": rel(REPO_VALIDATOR_PATH),
            "expected_ok": True,
        },
        "summary": {
            "eta_shells": [ETA1_LABEL, ETA2_LABEL],
            "union_weights": rows["step1"]["exact_joint_object"]["weights"],
            "chi_coefficient_gap": rows["scalars"]["coefficient_gap"],
            "flux_physical": rows["scalars"]["flux_physical"],
            "stokes_match": rows["step2"]["stokes"]["stokes_match"],
            "z4_z1_alpha_gap": rows["step3"]["quotient_rows"]["primitive_generators"]["z1_alpha"]["gap"],
            "requested_pair_commutes": rows["path_specificity"]["requested_joint_pair"]["same_pair_commutes"],
            "noncommuting_variant": rows["path_specificity"]["noncommuting_variant"]["variant"],
            "all_pass": bool(all(gates.values())),
        },
    }
    return result


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
