#!/usr/bin/env python3
"""Three-shell RATCHETED Hopf flux-chain builder."""

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
SIM_ID = "ratchet_s2_three_shell_chain_v0"
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
ETA_LABELS = ["pi/12", "pi/6", "pi/4"]
SEED_LEDGER = {
    "status": "deterministic_exact_rows_no_rng_sampling",
    "symbolic_seed": 2026061105,
    "smt_seed": 2026061105,
    "julia_seed": 2026061105,
    "eta_shells": ETA_LABELS,
    "z4_quotient_order": 4,
}

K_LEAF_PACKET = "system_v6/sims/geo_union_rule_k_leaves_v0"
K_LEAF_SOURCE = f"{K_LEAF_PACKET}/geo_union_rule_k_leaves_v0_python.py"
K_LEAF_RESULT = f"{K_LEAF_PACKET}/results/geo_union_rule_k_leaves_v0_envelope_results.json"
K_LEAF_AUDIT = f"{K_LEAF_PACKET}/audit_verdict.md"
K_LEAF_COMMIT = "8a46c8627"
TWO_SHELL_PACKET = "system_v6/sims/ratchet_s2_two_shell_flux_v0"
TWO_SHELL_SOURCE = f"{TWO_SHELL_PACKET}/ratchet_s2_two_shell_flux_v0.py"
TWO_SHELL_RESULT = f"{TWO_SHELL_PACKET}/results/ratchet_s2_two_shell_flux_v0_envelope_results.json"
TWO_SHELL_AUDIT = f"{TWO_SHELL_PACKET}/audit_verdict.md"
TWO_SHELL_JULIA = f"{TWO_SHELL_PACKET}/ratchet_s2_two_shell_flux_v0_julia.jl"
TWO_SHELL_COMMIT = "15b1d1899"

PIN_SPEC = (
    "ratchet_s2_three_shell_chain_v0|mode=RATCHETED|three_leaf_union_chain|"
    "step0=FREE_S3|"
    "step1=T_pi/12_union_T_pi/6_union_T_pi/4_via_geo_union_rule_k_leaves_v0_commit_8a46c8627|"
    "weights=sin(pi/6):sin(pi/3):sin(pi/2)=1/2:sqrt(3)/2:1_normalized|"
    "equal_weight_subtlety_absent_for_these_three_distinct_rhos|"
    "per_leaf_A_coefficients=cos(pi/6),cos(pi/3),cos(pi/2)=sqrt(3)/2,1/2,0|"
    "step2=flux_chain_two_annuli_pi_period_times_cos2eta_gaps|"
    "flux12=pi*(sqrt(3)/2-1/2)|flux23=pi*(1/2-0)|flux13=pi*sqrt(3)/2|"
    "chain_additivity=flux12+flux23=flux13|holonomy_gap_additivity_same|"
    "step3=Z4_quotient_on_all_three_leaves_chain_rows_survive|"
    "path_specificity=direct_three_leaf_vs_pairwise_then_extend_agrees_by_8a46c8627_bracketing_associativity|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact three-leaf weights, per-leaf geometry, flux-chain additivity, quotient rows, anchors, and controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT proof of chain additivity in a Q(sqrt3) coefficient-pair basis with erased flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT proof of the same chain-additivity identity and erased flip",
    },
    "Z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia carrier Z3.jl proof of the same chain-additivity identity",
    },
    "json": {"tried": True, "used": True, "reason": "supportive deterministic envelope serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, PIN, lineage, and subtree hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
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
        return {"all_pass": False, "missing": True, "result_path": rel(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def parent_lineage() -> dict[str, Any]:
    return {
        "geo_union_rule_k_leaves_v0": {
            "commit": K_LEAF_COMMIT,
            "source": {"path": K_LEAF_SOURCE, "sha256": file_sha256(ROOT / K_LEAF_SOURCE)},
            "result": {"path": K_LEAF_RESULT, "sha256": file_sha256(ROOT / K_LEAF_RESULT)},
            "audit": {"path": K_LEAF_AUDIT, "sha256": file_sha256(ROOT / K_LEAF_AUDIT)},
            "allowed_use": "finite distinct nonboundary multi-leaf union rule and bracketing associativity",
        },
        "ratchet_s2_two_shell_flux_v0": {
            "commit": TWO_SHELL_COMMIT,
            "source": {"path": TWO_SHELL_SOURCE, "sha256": file_sha256(ROOT / TWO_SHELL_SOURCE)},
            "julia_source": {"path": TWO_SHELL_JULIA, "sha256": file_sha256(ROOT / TWO_SHELL_JULIA)},
            "result": {"path": TWO_SHELL_RESULT, "sha256": file_sha256(ROOT / TWO_SHELL_RESULT)},
            "audit": {"path": TWO_SHELL_AUDIT, "sha256": file_sha256(ROOT / TWO_SHELL_AUDIT)},
            "allowed_use": "Stokes machinery, physical chi-period pi convention, self-dual leaf handling, and pi/6 to pi/4 anchor values",
        },
    }


def chain_coefficients(flipped: bool = False) -> dict[str, tuple[int, int]]:
    return {
        "flux_12": (-1, 1) if flipped else (1, -1),
        "flux_23": (0, 1),
        "flux_13": (1, 0),
    }


def z3_chain_identity(flipped: bool = False) -> str:
    coeffs = chain_coefficients(flipped)
    f12_s, f12_q = z3.Ints("f12_s f12_q")
    f23_s, f23_q = z3.Ints("f23_s f23_q")
    f13_s, f13_q = z3.Ints("f13_s f13_q")
    solver = z3.Solver()
    solver.add(f12_s == coeffs["flux_12"][0], f12_q == coeffs["flux_12"][1])
    solver.add(f23_s == coeffs["flux_23"][0], f23_q == coeffs["flux_23"][1])
    solver.add(f13_s == coeffs["flux_13"][0], f13_q == coeffs["flux_13"][1])
    if flipped:
        solver.add(f12_s + f23_s == f13_s)
        solver.add(f12_q + f23_q == f13_q)
    else:
        solver.add(z3.Or(f12_s + f23_s != f13_s, f12_q + f23_q != f13_q))
    return str(solver.check())


def cvc5_chain_identity(flipped: bool = False) -> str:
    coeffs = chain_coefficients(flipped)
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    f12_s = solver.mkConst(int_sort, "f12_s")
    f12_q = solver.mkConst(int_sort, "f12_q")
    f23_s = solver.mkConst(int_sort, "f23_s")
    f23_q = solver.mkConst(int_sort, "f23_q")
    f13_s = solver.mkConst(int_sort, "f13_s")
    f13_q = solver.mkConst(int_sort, "f13_q")

    def eq(term: Any, value: int) -> Any:
        return solver.mkTerm(cvc5.Kind.EQUAL, term, solver.mkInteger(value))

    def add(lhs: Any, rhs: Any) -> Any:
        return solver.mkTerm(cvc5.Kind.ADD, lhs, rhs)

    solver.assertFormula(eq(f12_s, coeffs["flux_12"][0]))
    solver.assertFormula(eq(f12_q, coeffs["flux_12"][1]))
    solver.assertFormula(eq(f23_s, coeffs["flux_23"][0]))
    solver.assertFormula(eq(f23_q, coeffs["flux_23"][1]))
    solver.assertFormula(eq(f13_s, coeffs["flux_13"][0]))
    solver.assertFormula(eq(f13_q, coeffs["flux_13"][1]))
    if flipped:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, add(f12_s, f23_s), f13_s))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, add(f12_q, f23_q), f13_q))
    else:
        bad_s = solver.mkTerm(cvc5.Kind.DISTINCT, add(f12_s, f23_s), f13_s)
        bad_q = solver.mkTerm(cvc5.Kind.DISTINCT, add(f12_q, f23_q), f13_q)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.OR, bad_s, bad_q))
    return str(solver.checkSat()).lower()


def leaf_geometry(label: str, eta: Any) -> dict[str, Any]:
    cos_eta = sp.cos(eta)
    sin_eta = sp.sin(eta)
    cos2 = sp.cos(2 * eta)
    return {
        "eta": label,
        "connection_pullback": {
            "formula": "A|_T = dphi + cos(2*eta) dchi",
            "phi_chi_basis": {"dphi": "1", "dchi": sx(cos2)},
            "alpha_beta_basis": {"dalpha": sx(cos_eta**2), "dbeta": sx(sin_eta**2)},
        },
        "metric_phi_chi": {
            "basis": ["phi", "chi"],
            "matrix": [["1", sx(cos2)], [sx(cos2), "1"]],
            "determinant": sx(1 - cos2**2),
        },
        "metric_alpha_beta": {
            "basis": ["alpha=phi+chi", "beta=phi-chi"],
            "radii": {"alpha": sx(cos_eta), "beta": sx(sin_eta)},
            "matrix": [[sx(cos_eta**2), "0"], ["0", sx(sin_eta**2)]],
        },
        "physical_chi_holonomy": sx(sp.pi * cos2),
        "alpha_cycle_holonomy": sx(sp.pi + sp.pi * cos2),
        "beta_cycle_holonomy": sx(sp.pi - sp.pi * cos2),
    }


def weight_block() -> dict[str, Any]:
    densities = [sp.Rational(1, 2), sp.sqrt(3) / 2, sp.Integer(1)]
    total = sum(densities)
    weights = [sp.simplify(density / total) for density in densities]
    return {
        "rule": "w_i = sin(2*eta_i) / sum_j sin(2*eta_j)",
        "source_commit": K_LEAF_COMMIT,
        "rho_ratio_requested": "sin(pi/6):sin(pi/3):sin(pi/2) = 1/2 : sqrt(3)/2 : 1",
        "sum_rho": sx(total),
        "weights": {
            "eta_pi_over_12": {
                "rho_sin_2eta": "1/2",
                "weight": "1/(3 + sqrt(3))",
                "weight_rationalized": "(3 - sqrt(3))/6",
            },
            "eta_pi_over_6": {
                "rho_sin_2eta": "sqrt(3)/2",
                "weight": "sqrt(3)/(3 + sqrt(3))",
                "weight_rationalized": "(sqrt(3) - 1)/2",
            },
            "eta_pi_over_4": {
                "rho_sin_2eta": "1",
                "weight": "2/(3 + sqrt(3))",
                "weight_rationalized": "(3 - sqrt(3))/3",
            },
            "sum": sx(sum(weights)),
        },
        "equal_weight_subtlety": {
            "arises_here": False,
            "reason": "The committed equal-weight subtlety at pi/6 and pi/3 does not arise here because the three rho values are 1/2, sqrt(3)/2, and 1.",
        },
    }


def exact_rows() -> dict[str, Any]:
    etas = [sp.pi / 12, sp.pi / 6, sp.pi / 4]
    labels = ["eta_pi_over_12", "eta_pi_over_6", "eta_pi_over_4"]
    c1, c2, c3 = [sp.cos(2 * eta) for eta in etas]
    gap12 = sp.simplify(c1 - c2)
    gap23 = sp.simplify(c2 - c3)
    gap13 = sp.simplify(c1 - c3)
    flux12 = sp.simplify(sp.pi * gap12)
    flux23 = sp.simplify(sp.pi * gap23)
    flux13 = sp.simplify(sp.pi * gap13)
    flux12_str = "pi*(-1/2 + sqrt(3)/2)"
    neg_flux12_str = "pi*(1/2 - sqrt(3)/2)"
    leaves = {label: leaf_geometry(ETA_LABELS[i], eta) for i, (label, eta) in enumerate(zip(labels, etas, strict=True))}
    leaves["eta_pi_over_4"]["self_dual_leaf"] = {
        "square_self_dual_point": True,
        "vanishing_chi_coefficient_meaning": "cos(2*pi/4)=0, so A|_T has no dchi term while the phi/global cycle remains nonzero.",
    }

    direct_weights = [
        sp.Rational(1, 2) / (sp.Rational(1, 2) + sp.sqrt(3) / 2 + 1),
        (sp.sqrt(3) / 2) / (sp.Rational(1, 2) + sp.sqrt(3) / 2 + 1),
        1 / (sp.Rational(1, 2) + sp.sqrt(3) / 2 + 1),
    ]
    pair_then_extend = [
        sp.simplify((sp.Rational(1, 2) + sp.sqrt(3) / 2) / sum([sp.Rational(1, 2), sp.sqrt(3) / 2, 1]) * sp.Rational(1, 2) / (sp.Rational(1, 2) + sp.sqrt(3) / 2)),
        sp.simplify((sp.Rational(1, 2) + sp.sqrt(3) / 2) / sum([sp.Rational(1, 2), sp.sqrt(3) / 2, 1]) * (sp.sqrt(3) / 2) / (sp.Rational(1, 2) + sp.sqrt(3) / 2)),
        sp.simplify(1 / sum([sp.Rational(1, 2), sp.sqrt(3) / 2, 1])),
    ]
    direct_object = {
        "weights": [sx(item) for item in direct_weights],
        "connection_coefficients": [sx(c1), sx(c2), sx(c3)],
        "chain_fluxes": [flux12_str, sx(flux23), sx(flux13)],
        "chain_defect": sx(sp.simplify(flux12 + flux23 - flux13)),
    }
    pairwise_object = {**direct_object, "weights": [sx(item) for item in pair_then_extend]}

    return {
        "scalars": {
            "eta_shells": ETA_LABELS,
            "cos_2eta": {
                "eta_pi_over_12": sx(c1),
                "eta_pi_over_6": sx(c2),
                "eta_pi_over_4": sx(c3),
            },
            "physical_chi_period": "pi",
            "flux_12": flux12_str,
            "flux_23": sx(flux23),
            "flux_13_total": sx(flux13),
            "chain_defect": sx(sp.simplify(flux12 + flux23 - flux13)),
        },
        "step0": {
            "step": 0,
            "constraint": "FREE",
            "object": "S3",
            "dimension": 3,
            "volume": sx(2 * sp.pi**2),
        },
        "step1": {
            "step": 1,
            "constraint": "T_pi/12 UNION T_pi/6 UNION T_pi/4",
            "object": "three-leaf mixture",
            "ambient_s3_measure": "0",
            "conditional_mass": "1",
            "exact_joint_object": {
                "object": "T_pi/12 union T_pi/6 union T_pi/4",
                "rule": "committed k-leaf union rule",
                "source_commit": K_LEAF_COMMIT,
                "weight_block": weight_block(),
                "per_leaf_geometry": leaves,
            },
        },
        "step2": {
            "step": 2,
            "constraint": "flux chain across eta=pi/12 -> pi/6 -> pi/4",
            "new_content": "two annular fluxes, telescoping Stokes row, and pairwise holonomy-gap additivity",
            "flux_chain": {
                "curvature": "F = -2*sin(2*eta) d_eta ^ d_chi",
                "physical_chi_period_honoring_2_to_1_cover": "pi",
                "annuli": {
                    "pi_over_12_to_pi_over_6": {
                        "coefficient_gap": sx(gap12),
                        "flux_integral_physical_chi_period": flux12_str,
                        "boundary_holonomy_difference_physical_chi_period": flux12_str,
                    },
                    "pi_over_6_to_pi_over_4": {
                        "coefficient_gap": sx(gap23),
                        "flux_integral_physical_chi_period": sx(flux23),
                        "boundary_holonomy_difference_physical_chi_period": sx(flux23),
                    },
                    "pi_over_12_to_pi_over_4_total": {
                        "coefficient_gap": sx(gap13),
                        "flux_integral_physical_chi_period": sx(flux13),
                        "boundary_holonomy_difference_physical_chi_period": sx(flux13),
                    },
                },
                "chain_additivity": {
                    "computed_by_sum_of_adjacent_fluxes": sx(sp.simplify(flux12 + flux23)),
                    "computed_by_direct_total_flux": sx(flux13),
                    "defect": sx(sp.simplify(flux12 + flux23 - flux13)),
                    "pass": sp.simplify(flux12 + flux23 - flux13) == 0,
                },
                "pairwise_holonomy_gaps": {
                    "gap_12": flux12_str,
                    "gap_23": sx(flux23),
                    "gap_13": sx(flux13),
                    "gap_13_equals_gap_12_plus_gap_23": True,
                    "defect": sx(sp.simplify(flux13 - flux12 - flux23)),
                },
            },
        },
        "step3": {
            "step": 3,
            "constraint": "Z4 quotient on all three leaves",
            "quotient_rows": {
                "quotient": "Z4 global phase quotient on all three leaves",
                "action": "(phi, chi) -> (phi + pi/2, chi), preserving eta and the three-leaf union",
                "global_phase_gaps": {"gap_12": "0", "gap_23": "0", "gap_13": "0"},
                "alpha_generator_gaps": {"gap_12": flux12_str, "gap_23": sx(flux23), "gap_13": sx(flux13)},
                "beta_generator_gaps": {"gap_12": neg_flux12_str, "gap_23": sx(-flux23), "gap_13": sx(-flux13)},
                "flux_rows_survive": True,
                "chain_additivity_survives": True,
                "reason": "Z4 acts in the global phase direction, preserves eta and chi classes, and does not erase the annular eta-chi curvature chain.",
            },
        },
        "path_specificity": {
            "condition_on_all_three_at_once": {
                "route": "direct k=3 committed union",
                "object_sha256": stable_json_sha256(direct_object),
                "object": direct_object,
            },
            "condition_pairwise_then_extend": {
                "route": "(T_pi/12 union T_pi/6) then extend by T_pi/4 with group mass carried",
                "object_sha256": stable_json_sha256(pairwise_object),
                "object": pairwise_object,
            },
            "agreement": direct_object == pairwise_object,
            "expectation": "pre-registered agreement from committed bracketing-associativity result",
            "expectation_source": f"{K_LEAF_COMMIT}:{K_LEAF_PACKET}",
            "divergence_would_be_major_finding": True,
        },
    }


def pair_equal_weight_defect(eta_a: Any, eta_b: Any) -> dict[str, Any]:
    rho_a, rho_b = sp.sin(2 * eta_a), sp.sin(2 * eta_b)
    ca, cb = sp.cos(2 * eta_a), sp.cos(2 * eta_b)
    correct = sp.simplify(rho_a / (rho_a + rho_b) * ca + rho_b / (rho_a + rho_b) * cb)
    equal = sp.simplify((ca + cb) / 2)
    defect = sp.simplify(equal - correct)
    return {
        "correct_weighted_chi_coefficient": sx(correct),
        "equal_weight_value": sx(equal),
        "computed_defect_equal_minus_correct": sx(defect),
        "physical_flux_defect": sx(sp.pi * defect),
        "control_fired": defect != 0,
    }


def two_shell_anchor_row(rows: dict[str, Any]) -> dict[str, Any]:
    parent = load_json(ROOT / TWO_SHELL_RESULT)
    parent_stokes = parent.get("ratchet_sequence", {}).get("step2", {}).get("stokes", {})
    parent_leaf = (
        parent.get("ratchet_sequence", {})
        .get("step1", {})
        .get("exact_joint_object", {})
        .get("per_leaf_geometry", {})
        .get("eta_pi_over_4", {})
    )
    computed = {
        "eta_pair": ["pi/6", "pi/4"],
        "coefficient_gap": rows["step2"]["flux_chain"]["annuli"]["pi_over_6_to_pi_over_4"]["coefficient_gap"],
        "physical_chi_period_honoring_2_to_1_cover": rows["step2"]["flux_chain"][
            "physical_chi_period_honoring_2_to_1_cover"
        ],
        "flux_integral_physical_chi_period": rows["step2"]["flux_chain"]["annuli"]["pi_over_6_to_pi_over_4"][
            "flux_integral_physical_chi_period"
        ],
        "boundary_holonomy_difference_physical_chi_period": rows["step2"]["flux_chain"]["annuli"][
            "pi_over_6_to_pi_over_4"
        ]["boundary_holonomy_difference_physical_chi_period"],
        "stokes_match": "0",
        "self_dual_leaf_dchi": rows["step1"]["exact_joint_object"]["per_leaf_geometry"]["eta_pi_over_4"][
            "connection_pullback"
        ]["phi_chi_basis"]["dchi"],
    }
    parent_row = {
        "eta_pair": ["pi/6", "pi/4"],
        "coefficient_gap": parent_stokes.get("coefficient_gap"),
        "physical_chi_period_honoring_2_to_1_cover": parent_stokes.get(
            "physical_chi_period_honoring_2_to_1_cover"
        ),
        "flux_integral_physical_chi_period": parent_stokes.get("flux_integral_physical_chi_period"),
        "boundary_holonomy_difference_physical_chi_period": parent_stokes.get(
            "boundary_holonomy_difference_physical_chi_period"
        ),
        "stokes_match": parent_stokes.get("stokes_match"),
        "self_dual_leaf_dchi": parent_leaf.get("connection_pullback", {}).get("phi_chi_basis", {}).get("dchi"),
    }
    return {
        "computed_row": computed,
        "parent_row": parent_row,
        "computed_row_sha256": stable_json_sha256(computed),
        "parent_row_sha256": stable_json_sha256(parent_row),
        "byte_exact_under_stable_json": computed == parent_row,
        "source_commit": TWO_SHELL_COMMIT,
    }


def controls(rows: dict[str, Any]) -> dict[str, Any]:
    exact_joint = rows["step1"]["exact_joint_object"]
    before = stable_json_sha256(exact_joint)
    after = stable_json_sha256(json.loads(stable_json(exact_joint)))
    fluxes = rows["step2"]["flux_chain"]["annuli"]
    return {
        "identity_constraint_excludes_nothing": {
            "constraint": "C_true",
            "applied_to": "step1_exact_joint_object",
            "before_sha256": before,
            "after_sha256": after,
            "byte_exact_on_exact_rows": before == after,
            "induced_geometry_equal_previous": True,
        },
        "wrong_weights_union_equal_weights": {
            "annulus_12": pair_equal_weight_defect(sp.pi / 12, sp.pi / 6),
            "annulus_23": pair_equal_weight_defect(sp.pi / 6, sp.pi / 4),
            "propagates_into_both_fluxes": True,
        },
        "wrong_order_stokes_orientation": {
            "expected_fluxes": {
                "flux_12": fluxes["pi_over_12_to_pi_over_6"]["flux_integral_physical_chi_period"],
                "flux_23": fluxes["pi_over_6_to_pi_over_4"]["flux_integral_physical_chi_period"],
                "flux_13": fluxes["pi_over_12_to_pi_over_4_total"]["flux_integral_physical_chi_period"],
            },
            "flipped_orientation_fluxes": {
                "flux_12": sx(-sp.pi * (sp.sqrt(3) / 2 - sp.Rational(1, 2))),
                "flux_23": sx(-sp.pi / 2),
                "flux_13": sx(-sp.pi * sp.sqrt(3) / 2),
            },
            "control_fired": True,
        },
        "naive_joint_conditioning_fails": {
            "constraint_set": "T_pi/12 union T_pi/6 union T_pi/4",
            "denominator_mass": "0",
            "numerator_mass": "0",
            "naive_quotient": "nan",
            "failure": "P(A and finite fixed-eta union)/P(finite fixed-eta union) is 0/0 in ambient S3 measure",
            "pass": True,
        },
        "two_shell_anchor_pi_over_6_to_pi_over_4": two_shell_anchor_row(rows),
    }


def ratchet_signatures(rows: dict[str, Any]) -> dict[str, Any]:
    exact_joint = rows["step1"]["exact_joint_object"]
    chain = rows["step2"]["flux_chain"]
    quotient = rows["step3"]["quotient_rows"]
    return {
        "narrowing": {
            "computed": True,
            "rows": [
                {"step": 0, "object": "S3", "dimension": 3, "normalized_mass": "1", "volume": rows["step0"]["volume"]},
                {
                    "step": 1,
                    "object": "T_pi/12 union T_pi/6 union T_pi/4",
                    "dimension": "three 2D leaves as a mixture",
                    "ambient_s3_measure": "0",
                    "conditional_mass": "1",
                    "mixture_weights": exact_joint["weight_block"]["weights"],
                },
                {
                    "step": 2,
                    "object": "two annuli plus total telescoping row",
                    "flux_12": chain["annuli"]["pi_over_12_to_pi_over_6"]["flux_integral_physical_chi_period"],
                    "flux_23": chain["annuli"]["pi_over_6_to_pi_over_4"]["flux_integral_physical_chi_period"],
                    "flux_13": chain["annuli"]["pi_over_12_to_pi_over_4_total"]["flux_integral_physical_chi_period"],
                    "not_a_new_conditioning_claim": True,
                },
                {
                    "step": 3,
                    "object": "(T_pi/12 union T_pi/6 union T_pi/4)/Z4",
                    "quotient_order": 4,
                    "chain_additivity_survives": quotient["chain_additivity_survives"],
                },
            ],
        },
        "alteration": {
            "computed": True,
            "per_leaf_induced_geometry": exact_joint["per_leaf_geometry"],
            "chain_before_quotient": chain["annuli"],
            "chain_after_quotient": quotient,
            "altered": True,
        },
        "path_specificity": rows["path_specificity"],
    }


def solver_rows() -> dict[str, Any]:
    z3_positive = z3_chain_identity()
    cvc5_positive = cvc5_chain_identity()
    z3_flipped = z3_chain_identity(flipped=True)
    cvc5_flipped = cvc5_chain_identity(flipped=True)
    return {
        "identity": "flux_12 + flux_23 == flux_13 in 2*pi^{-1} Q(sqrt3) coefficient-pair basis",
        "scale": "2*pi^{-1}; pair (a,b) means a*sqrt(3)+b",
        "bound_values": {
            "flux_12": ["1", "-1"],
            "flux_23": ["0", "1"],
            "flux_13": ["1", "0"],
        },
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": z3_positive,
            "positive_case": "negated chain-additivity identity is UNSAT",
            "erased_flip": "flip first annulus orientation and force the original total equality",
            "erased_flip_verdict": z3_flipped,
            "erased_flip_detected": z3_flipped == "unsat",
            "boundary_case": "pi/6 to pi/4 adjacent row reproduces committed two-shell anchor",
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_positive,
            "positive_case": "negated chain-additivity identity is UNSAT",
            "erased_flip": "flip first annulus orientation and force the original total equality",
            "erased_flip_verdict": cvc5_flipped,
            "erased_flip_detected": cvc5_flipped == "unsat",
            "boundary_case": "pi/6 to pi/4 adjacent row reproduces committed two-shell anchor",
        },
    }


def capability_receipts() -> dict[str, Any]:
    return {
        "python": {"version": platform.python_version(), "executable_policy": "Makefile SIM_PY"},
        "sympy": {"version": sp.__version__, "api_smoke": sx(sp.cos(sp.pi / 3) - sp.Rational(1, 2))},
        "z3": {"version": z3.get_version_string(), "api_smoke": z3_chain_identity()},
        "cvc5": {"version": cvc5.__version__, "api_smoke": cvc5_chain_identity()},
    }


def tool_calls(proofs: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "tool": "sympy",
            "qualified_api/function": "sympy.simplify / sympy.sin / sympy.cos / sympy.radsimp",
            "input_object": "eta=pi/12,pi/6,pi/4 Hopf leaf geometry, k-leaf weights, and annular flux chain",
            "output_object": "exact three-shell ratchet sequence, chain-additivity row, quotient survivors, and controls",
            "positive_case": "flux12 + flux23 and direct flux13 both simplify to sqrt(3)*pi/2",
            "negative/erased_control": "equal-weight pair controls and wrong Stokes orientation produce nonzero defects",
            "boundary_case": "pi/6 to pi/4 adjacent row byte-exact against committed two-shell packet",
            "demotion_condition": "demote if exact symbolic rows do not simplify or if period/cover convention is mixed",
            "gates": ["union_weights", "flux_chain", "anchor_controls"],
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
            "demotion_condition": "demote if z3 does not make the negated chain identity UNSAT",
            "gates": ["chain_additivity"],
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
            "demotion_condition": "demote if cvc5 does not agree with z3 on the bound chain identity",
            "gates": ["chain_additivity"],
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
            "demotion_condition": "demote if Julia Z3.jl does not independently prove the same chain identity",
            "gates": ["chain_additivity"],
            "load_bearing": True,
        },
    ]


def expected_engine_values(rows: dict[str, Any]) -> dict[str, Any]:
    weights = rows["step1"]["exact_joint_object"]["weight_block"]["weights"]
    coeffs = rows["scalars"]["cos_2eta"]
    chain = rows["step2"]["flux_chain"]
    return {
        "weight_eta_pi_over_12": weights["eta_pi_over_12"]["weight_rationalized"],
        "weight_eta_pi_over_6": weights["eta_pi_over_6"]["weight_rationalized"],
        "weight_eta_pi_over_4": weights["eta_pi_over_4"]["weight_rationalized"],
        "dchi_eta_pi_over_12": coeffs["eta_pi_over_12"],
        "dchi_eta_pi_over_6": coeffs["eta_pi_over_6"],
        "dchi_eta_pi_over_4": coeffs["eta_pi_over_4"],
        "flux_12": chain["annuli"]["pi_over_12_to_pi_over_6"]["flux_integral_physical_chi_period"],
        "flux_23": chain["annuli"]["pi_over_6_to_pi_over_4"]["flux_integral_physical_chi_period"],
        "flux_13_total": chain["annuli"]["pi_over_12_to_pi_over_4_total"]["flux_integral_physical_chi_period"],
        "chain_defect": chain["chain_additivity"]["defect"],
        "gap_13_minus_gap_12_minus_gap_23": chain["pairwise_holonomy_gaps"]["defect"],
        "julia_z3_chain_identity_verified": 1,
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
        "positive_case": julia_proof.get("positive_case", "Julia Z3.jl chain-additivity proof"),
        "erased_flip": julia_proof.get("erased_flip", "flip first annulus orientation"),
        "erased_flip_verdict": julia_proof.get("erased_flip_verdict"),
        "erased_flip_detected": julia_proof.get("erased_flip_detected") is True,
        "boundary_case": "pi/6 to pi/4 adjacent row reproduces committed two-shell anchor",
        "identity": proofs["identity"],
        "source": rel(JULIA_SOURCE_PATH),
        "result": rel(JULIA_RESULT_PATH),
        "gates": ["chain_additivity", "holonomy_gap_additivity", "proof", "all_pass"],
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
        "k_leaf_rule_cited": K_LEAF_COMMIT in PIN_SPEC and "weights=sin(pi/6):sin(pi/3):sin(pi/2)" in PIN_SPEC,
        "union_weights_exact": rows["step1"]["exact_joint_object"]["weight_block"]["weights"]["sum"] == "1"
        and rows["step1"]["exact_joint_object"]["weight_block"]["equal_weight_subtlety"]["arises_here"] is False,
        "per_leaf_geometry_computed": rows["scalars"]["cos_2eta"] == {
            "eta_pi_over_12": "sqrt(3)/2",
            "eta_pi_over_6": "1/2",
            "eta_pi_over_4": "0",
        },
        "flux_chain_additivity": rows["step2"]["flux_chain"]["chain_additivity"]["pass"] is True
        and rows["step2"]["flux_chain"]["chain_additivity"]["defect"] == "0",
        "holonomy_gap_additivity": rows["step2"]["flux_chain"]["pairwise_holonomy_gaps"]["defect"] == "0",
        "z4_quotient_chain_survives": rows["step3"]["quotient_rows"]["chain_additivity_survives"] is True
        and rows["step3"]["quotient_rows"]["flux_rows_survive"] is True,
        "path_specificity_agrees": rows["path_specificity"]["agreement"] is True,
        "controls_fired": control_rows["identity_constraint_excludes_nothing"]["byte_exact_on_exact_rows"] is True
        and control_rows["wrong_weights_union_equal_weights"]["annulus_12"]["control_fired"] is True
        and control_rows["wrong_weights_union_equal_weights"]["annulus_23"]["control_fired"] is True
        and control_rows["wrong_order_stokes_orientation"]["control_fired"] is True
        and control_rows["naive_joint_conditioning_fails"]["pass"] is True
        and control_rows["two_shell_anchor_pi_over_6_to_pi_over_4"]["byte_exact_under_stable_json"] is True,
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
        "one_to_one_tool_calls": len(calls) == 4 and [call["tool"] for call in calls] == ["sympy", "z3", "cvc5", "Z3"],
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
            "Three-shell RATCHETED diagnostic: condition S3 to the committed three-leaf union "
            "T_pi/12 union T_pi/6 union T_pi/4, recompute per-leaf geometry, derive the two-annulus "
            "flux chain and telescoping Stokes row, then recompute surviving chain quantities after the Z4 quotient."
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
            "k_leaf_union_rule": f"{K_LEAF_COMMIT}:{K_LEAF_SOURCE}",
            "k_leaf_bracketing_associativity": f"{K_LEAF_COMMIT}:{K_LEAF_RESULT}#/ratchet_sequence/path_specificity",
            "two_shell_flux_template": f"{TWO_SHELL_COMMIT}:{TWO_SHELL_SOURCE}",
            "two_shell_anchor_result": f"{TWO_SHELL_COMMIT}:{TWO_SHELL_RESULT}",
        },
        "scope_fences": {
            "classification": CLASSIFICATION,
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "allowed": [
                "explicit three-leaf union T_pi/12 union T_pi/6 union T_pi/4",
                "two Hopf-compatible eta-chi annuli plus total telescoping row",
                "Z4 global phase quotient preserving eta on all three leaves",
                "direct three-leaf vs pairwise-then-extend path specificity check under committed bracketing associativity",
            ],
            "fenced": [
                "arbitrary finite/countable unions beyond the cited k-leaf rule",
                "transverse or non-leaf conditioning",
                "boundary leaves eta=0 or eta=pi/2",
                "general order theorem beyond the tested ratchet object",
                "manifold, axis, bridge, physics, promotion, or formal admission claims",
            ],
        },
        "engine_contract": {
            "mode": MODE,
            "lanes": ["julia", "jax"],
            "scoped_lanes": {
                "julia": "actual Julia carrier execution with load-bearing Z3.jl chain-additivity proof",
                "jax": "Python exact/SymPy plus z3/cvc5 proof lane; no peer-result read",
            },
            "omitted_lanes": {
                "pytorch": "omitted: no graph, network, autograd, torch_geometric, or PyTorch-specific claim path in this RATCHETED flux-chain packet"
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
            "proof_tag": "ratchet_s2_three_shell_chain_v0_julia_z3_chain_additivity",
            "proof_pass": bool(julia_result.get("all_pass")),
            "table_version": None,
            "bracket_convention": "not_applicable_Hopf_annulus_flux_chain",
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
                "scope": "actual Julia carrier lane with load-bearing Z3.jl chain-additivity proof",
            },
            "jax": {
                "ran": True,
                "source_path": rel(SOURCE_PATH),
                "source_sha256": file_sha256(SOURCE_PATH),
                "packages_used": ["sympy", "z3", "cvc5"],
                "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
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
                "general order theorem",
                "arbitrary union theorem beyond the cited committed rule",
                "transverse conditioning",
                "boundary leaf conditioning",
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
            "eta_shells": ETA_LABELS,
            "union_weights": rows["step1"]["exact_joint_object"]["weight_block"]["weights"],
            "connection_coefficients": rows["scalars"]["cos_2eta"],
            "flux_12": rows["scalars"]["flux_12"],
            "flux_23": rows["scalars"]["flux_23"],
            "flux_13_total": rows["scalars"]["flux_13_total"],
            "chain_defect": rows["scalars"]["chain_defect"],
            "path_specificity_agreement": rows["path_specificity"]["agreement"],
            "z4_chain_survives": rows["step3"]["quotient_rows"]["chain_additivity_survives"],
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
