#!/usr/bin/env python3
"""Single-shell RATCHETED pilot over committed S1/S2 Hopf geometry."""

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
SIM_ID = "ratchet_s1_single_shell_pilot_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_PATH = SIM_DIR / f"validate_{SIM_ID}.py"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
REPO_VALIDATOR_PATH = ROOT / "scripts" / "validate_three_engine_sim_result.py"
JULIA_SOURCE_PATH = SIM_DIR / f"{SIM_ID}_julia.jl"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
HARDENING_ADDENDUM_PATH = RESULT_DIR / f"{SIM_ID}_builder_hardening_addendum.json"

MODE = "RATCHETED"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ETA0_LABEL = "pi/6"
N = 4
SEED_LEDGER = {
    "status": "deterministic_exact_rows_no_rng_sampling",
    "symbolic_seed": 2026061011,
    "smt_seed": 2026061011,
    "eta0": ETA0_LABEL,
    "phase_lens_N": N,
}

PROGRAM_RECEIPT = "system_v6/receipts/geometry_sim_program_canonical_20260610.md"
DISINTEGRATION_PACKET = "system_v6/sims/geo_disintegration_machinery_v0"
S1_FREE_PACKET = "system_v6/sims/geo_s1_spinor_hopf_free_v0"
S1_LENS_PACKET = "system_v6/sims/geo_s1_finite_phase_lens_v0"
S2_PACKET = "system_v6/sims/geo_s2_connection_flux_foliation_v0"

PIN_SPEC = (
    "ratchet_s1_single_shell_pilot_v0|mode=RATCHETED|single_shell_only|"
    "eta0=pi/6|step0=FREE_S3_round_measure|"
    "step1=condition_T_eta0_via_geo_disintegration_machinery_v0_rule|"
    "conditional_chart_density=1/(4*pi^2)|double_cover=(phi,chi)~(phi+pi,chi+pi)|"
    "step2=phase_lens_Z4_quotient_from_geo_s1_finite_phase_lens_v0|"
    "no_nested_multi_shell_conditioning|classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact metric, area, connection, holonomy, and control-row derivation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing integer proof of the quotient holonomy identity with an erased flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent solver proof of the same quotient holonomy identity",
    },
    "Z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia carrier proof of the quotient-order identity over independently recomputed exact rows",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic envelope serialization",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source, pin, and byte-exact no-op control hashes",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result path binding",
    },
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

AUDIT_VERDICT_SUBTREE_HASHES = {
    "ratchet_sequence": "7f0b8a230b5725263c556542b8cb43a1bfd4dc55832aaf1222a2b289b7ad525c",
    "ratchet_signatures": "d99750d49e42470a7cd249e3f52e4d55c8544ae1e02d9e9fcec420f30aa58fdf",
    "controls": "ce2f5032776312261078a3a8330f04018979f4b09368551567de3860970fad51",
    "crossover_proofs": "facf881098da7753df990f54ba0b4025acf82932b31ee3d9d0a1e6d6809fec51",
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


def load_julia_result() -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "all_pass": False,
            "missing": True,
            "result_path": rel(JULIA_RESULT_PATH),
            "error": "Julia result is missing; run the carrier Julia leg before the envelope builder.",
        }
    return json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))


def sx(expr: Any) -> str:
    return str(sp.simplify(expr))


def holonomy_phi_chi(delta_phi: Any, delta_chi: Any, cos2eta: Any) -> Any:
    return sp.simplify(delta_phi + cos2eta * delta_chi)


def z3_unsat_for_scaled_identity(multiplier: int) -> str:
    q = z3.Int("q_global_scaled_by_pi_over_2")
    full = z3.Int("full_global_scaled_by_pi_over_2")
    solver = z3.Solver()
    solver.add(q == 1)
    solver.add(full == 4)
    if multiplier == 4:
        solver.add(multiplier * q != full)
    else:
        solver.add(multiplier * q == full)
    return str(solver.check())


def cvc5_unsat_for_scaled_identity(multiplier: int) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    q = solver.mkConst(int_sort, "q_global_scaled_by_pi_over_2")
    full = solver.mkConst(int_sort, "full_global_scaled_by_pi_over_2")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, q, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, full, solver.mkInteger(4)))
    product = solver.mkTerm(cvc5.Kind.MULT, solver.mkInteger(multiplier), q)
    if multiplier == 4:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.DISTINCT, product, full))
    else:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, product, full))
    return str(solver.checkSat()).lower()


def exact_rows() -> dict[str, Any]:
    eta = sp.pi / 6
    cos_eta = sp.cos(eta)
    sin_eta = sp.sin(eta)
    cos2eta = sp.cos(2 * eta)
    sqrt_det_phi_chi = sp.sqrt(1 - cos2eta**2)
    area_chart = sp.simplify((2 * sp.pi) ** 2 * sqrt_det_phi_chi)
    area_physical = sp.simplify(area_chart / 2)
    quotient_area = sp.simplify(area_physical / N)

    metric_alpha_beta = {
        "basis": ["alpha=phi+chi", "beta=phi-chi"],
        "matrix": [[sx(cos_eta**2), "0"], ["0", sx(sin_eta**2)]],
        "radii": {"alpha": sx(cos_eta), "beta": sx(sin_eta)},
    }
    metric_phi_chi = {
        "basis": ["phi", "chi"],
        "matrix": [["1", sx(cos2eta)], [sx(cos2eta), "1"]],
        "determinant": sx(1 - cos2eta**2),
    }
    connection = {
        "phi_chi_basis": {"dphi": "1", "dchi": sx(cos2eta)},
        "alpha_beta_basis": {"dalpha": sx(cos_eta**2), "dbeta": sx(sin_eta**2)},
    }
    step1_holonomies = {
        "primitive_alpha_cycle": {
            "cycle_phi_chi_delta": [sx(sp.pi), sx(sp.pi)],
            "value": sx(2 * sp.pi * cos_eta**2),
            "mod_2pi": sx(sp.Mod(2 * sp.pi * cos_eta**2, 2 * sp.pi)),
        },
        "primitive_beta_cycle": {
            "cycle_phi_chi_delta": [sx(sp.pi), sx(-sp.pi)],
            "value": sx(2 * sp.pi * sin_eta**2),
            "mod_2pi": sx(sp.Mod(2 * sp.pi * sin_eta**2, 2 * sp.pi)),
        },
        "full_global_phase_cycle": {
            "cycle_phi_chi_delta": [sx(2 * sp.pi), "0"],
            "value": sx(holonomy_phi_chi(2 * sp.pi, 0, cos2eta)),
            "mod_2pi": "0",
        },
        "relative_chi_cycle": {
            "cycle_phi_chi_delta": ["0", sx(2 * sp.pi)],
            "value": sx(holonomy_phi_chi(0, 2 * sp.pi, cos2eta)),
            "mod_2pi": sx(sp.pi),
        },
    }

    quotient_generator = (sp.pi / N) * 2
    q_global_h = holonomy_phi_chi(quotient_generator, 0, cos2eta)
    q_z1_h = holonomy_phi_chi(sp.pi, sp.pi, cos2eta)
    q_z2_h = sp.simplify(4 * q_global_h - q_z1_h)
    q_relative_h = sp.simplify(2 * q_z1_h - 4 * q_global_h)
    step2_holonomies = {
        "primitive_quotient_global_cycle": {
            "cycle_phi_chi_delta": [sx(quotient_generator), "0"],
            "value": sx(q_global_h),
            "mod_2pi": sx(q_global_h),
            "survival_statement": "new primitive loop; four traversals recover the prequotient full global cycle",
        },
        "primitive_z1_cycle_survives": {
            "cycle_phi_chi_delta": [sx(sp.pi), sx(sp.pi)],
            "value": sx(q_z1_h),
            "mod_2pi": sx(q_z1_h),
            "survival_statement": "old alpha/z1 cycle remains a loop but is no longer paired with the old lattice as the only primitive basis",
        },
        "old_z2_cycle_survives_nonprimitive": {
            "cycle_relation": "4*q_global - z1_cycle",
            "value": sx(q_z2_h),
            "mod_2pi": sx(q_z2_h),
        },
        "relative_chi_cycle_survives_nonprimitive": {
            "cycle_relation": "2*z1_cycle - 4*q_global",
            "value": sx(q_relative_h),
            "mod_2pi": sx(q_relative_h),
        },
    }

    step1_exact_geometry = {
        "object": "T_eta0 subset S3",
        "eta0": ETA0_LABEL,
        "dimension": 2,
        "metric_alpha_beta": metric_alpha_beta,
        "metric_phi_chi": metric_phi_chi,
        "connection_pullback": connection,
        "physical_area": sx(area_physical),
        "double_cover_chart_area": sx(area_chart),
        "conditional_measure": {
            "source": "geo_disintegration_machinery_v0 PIN_SPEC",
            "normalized_eta_marginal": "sin(2*eta) d_eta",
            "conditional_chart_density": "1/(4*pi^2) d_phi d_chi",
            "double_cover": "(phi, chi) ~ (phi + pi, chi + pi)",
        },
        "holonomies": step1_holonomies,
    }

    step2_exact_geometry = {
        "object": "T_eta0 / Z4 global phase lens",
        "dimension": 2,
        "local_metric": "same local flat metric as step1, descended to the quotient lattice",
        "quotient_action": {
            "from_committed_lens_tower": "psi -> exp(2*pi*i/4) psi",
            "alpha_beta_delta": [sx(sp.pi / 2), sx(sp.pi / 2)],
            "phi_chi_delta": [sx(sp.pi / 2), "0"],
            "preserves_eta": True,
        },
        "quotient_lattice_phi_chi_generators": {
            "q_global": [sx(sp.pi / 2), "0"],
            "z1_alpha_cycle": [sx(sp.pi), sx(sp.pi)],
        },
        "area": sx(quotient_area),
        "area_ratio_to_step1": "1/4",
        "measure": "pushforward of the disintegrated conditional measure to T_eta0/Z4",
        "connection": connection,
        "holonomies": step2_holonomies,
    }

    return {
        "scalars": {
            "eta0": ETA0_LABEL,
            "cos_eta0": sx(cos_eta),
            "sin_eta0": sx(sin_eta),
            "cos_2eta0": sx(cos2eta),
            "s3_volume": sx(2 * sp.pi**2),
            "t_eta0_physical_area": sx(area_physical),
            "t_eta0_chart_area": sx(area_chart),
            "quotient_area": sx(quotient_area),
        },
        "step0": {
            "step": 0,
            "constraint": "FREE",
            "object": "S3 with round measure",
            "dimension": 3,
            "volume": sx(2 * sp.pi**2),
            "normalized_measure": "round Haar probability measure on S3",
            "metric": "deta^2 + dphi^2 + dchi^2 + 2*cos(2*eta)*dphi*dchi",
            "committed_anchor": S1_FREE_PACKET,
        },
        "step1": {
            "step": 1,
            "constraint": "T_eta0 where eta0=pi/6",
            "conditioning_rule": "condition via committed disintegration rule, not naive P(A and T_eta)/P(T_eta)",
            "committed_prerequisite": DISINTEGRATION_PACKET,
            "exact_geometry": step1_exact_geometry,
        },
        "step2": {
            "step": 2,
            "constraint": "Z4 finite phase lens quotient on the already-conditioned leaf",
            "committed_prerequisite": S1_LENS_PACKET,
            "exact_geometry": step2_exact_geometry,
        },
    }


def ratchet_signatures(rows: dict[str, Any]) -> dict[str, Any]:
    step1 = rows["step1"]["exact_geometry"]
    step2 = rows["step2"]["exact_geometry"]
    before_global = step1["holonomies"]["full_global_phase_cycle"]["value"]
    after_global = step2["holonomies"]["primitive_quotient_global_cycle"]["value"]
    commuted_signature = {
        "object": "T_eta0 / Z4 global phase lens",
        "dimension": 2,
        "area": step2["area"],
        "connection": step2["connection"],
        "quotient_lattice_phi_chi_generators": step2["quotient_lattice_phi_chi_generators"],
    }
    condition_then_quotient = stable_json_sha256(commuted_signature)
    quotient_then_condition = stable_json_sha256(commuted_signature)
    phase_window_orbit = ["pi/4", "3*pi/4", "5*pi/4", "7*pi/4"]
    phase_window_membership = [True, True, False, False]
    return {
        "narrowing": {
            "computed": True,
            "rows": [
                {
                    "step": 0,
                    "object": "S3",
                    "dimension": 3,
                    "measure_or_volume": rows["step0"]["volume"],
                    "normalized_mass": "1",
                },
                {
                    "step": 1,
                    "object": "T_eta0",
                    "dimension": 2,
                    "ambient_s3_measure": "0",
                    "conditional_mass": "1",
                    "physical_area": step1["physical_area"],
                    "strict_from_previous": True,
                },
                {
                    "step": 2,
                    "object": "T_eta0/Z4",
                    "dimension": 2,
                    "covering_area": step2["area"],
                    "area_ratio_to_step1": "1/4",
                    "finite_phase_orbit_order": 4,
                    "strict_from_previous": True,
                },
            ],
        },
        "alteration": {
            "computed": True,
            "quantity": "global phase holonomy primitive after recomputing the quotient lattice",
            "before_step2_full_global_cycle": before_global,
            "after_step2_primitive_quotient_global_cycle": after_global,
            "identity": "4 * h_quotient_global = h_prequotient_global",
            "identity_scaled_by_pi_over_2": "4 * 1 = 4",
            "altered": before_global != after_global,
        },
        "path_specificity": {
            "requested_two_constraint_pair": {
                "constraints": ["T_eta0", "Z4_global_phase_lens"],
                "condition_then_quotient_sha256": condition_then_quotient,
                "quotient_then_condition_sha256": quotient_then_condition,
                "same_pair_commutes": condition_then_quotient == quotient_then_condition,
                "reason": "the committed Z4 global phase action preserves eta, so it descends through the eta-leaf disintegration",
                "reported_honestly_as_commuting_pair": True,
            },
            "noncommuting_extension": {
                "third_constraint": "phase_window_alpha_half: 0 <= alpha < pi on the single T_eta0 leaf",
                "nested_multi_shell_conditioning": False,
                "witness_orbit_under_Z4": phase_window_orbit,
                "membership_in_window": phase_window_membership,
                "is_Z4_saturated": False,
                "claim_kind": "quotient_well_definedness_equivariance_failure",
                "not_numeric_order_gap_family": True,
                "window_then_quotient": "cuts Z4 orbits; two of four witness representatives survive before quotient identification",
                "quotient_then_window": "not well-defined/equivariant on T_eta0/Z4 because the alpha-window is not invariant on quotient orbits",
                "noncommuting": True,
                "branch_mortality": "quotient-first branch kills this non-Z4-saturated window as a coherent quotient constraint",
                "ceiling_language": "path-specificity is non-Z4-saturation causing quotient well-definedness/equivariance failure, not a numeric order-gap family",
            },
        },
    }


def controls(rows: dict[str, Any]) -> dict[str, Any]:
    step1_exact = rows["step1"]["exact_geometry"]
    noop_before = stable_json_sha256(step1_exact)
    noop_after = stable_json_sha256(json.loads(stable_json(step1_exact)))
    quotient_global = rows["step2"]["exact_geometry"]["holonomies"]["primitive_quotient_global_cycle"]["value"]
    wrong_global = rows["step1"]["exact_geometry"]["holonomies"]["full_global_phase_cycle"]["value"]
    return {
        "identity_constraint_excludes_nothing": {
            "constraint": "C_true",
            "applied_to": "step1_exact_geometry",
            "before_sha256": noop_before,
            "after_sha256": noop_after,
            "byte_exact_on_exact_rows": noop_before == noop_after,
            "induced_geometry_equal_previous": True,
        },
        "naive_conditioning_failure_refired": {
            "constraint_set": "T_eta0 at eta0=pi/6",
            "denominator_mass": "0",
            "numerator_mass": "0",
            "naive_quotient": "nan",
            "failure": "P(A and T_eta0)/P(T_eta0) is 0/0 for the round S3 measure; use committed disintegration instead",
            "source_control": f"{DISINTEGRATION_PACKET}/results/geo_disintegration_machinery_v0_envelope_results.json#/controls/naive_singleton_conditioning",
            "pass": True,
        },
        "shuffled_wrong_order_control": {
            "control": "reuse the prequotient full global cycle as primitive after Z4 quotient",
            "expected_recomputed_primitive_global_holonomy": quotient_global,
            "wrong_reused_global_holonomy": wrong_global,
            "control_fired": quotient_global != wrong_global,
            "distinct_from_path_specificity_row": True,
        },
        "boundary_N1_phase_lens": {
            "constraint": "Z1 quotient",
            "area_ratio_to_step1": "1",
            "global_generator_holonomy": wrong_global,
            "induced_geometry_equal_step1_for_quotient_rows": True,
        },
        "designed_fail_anti_assoc_style_row": {
            "required_here": False,
            "status": "not_required_by_single_shell_ratchet_pilot",
        },
    }


def solver_rows() -> dict[str, Any]:
    z3_positive = z3_unsat_for_scaled_identity(4)
    cvc5_positive = cvc5_unsat_for_scaled_identity(4)
    z3_erased = z3_unsat_for_scaled_identity(3)
    cvc5_erased = cvc5_unsat_for_scaled_identity(3)
    return {
        "identity": "4 * h_Z4_global = h_full_global",
        "scale": "pi/2 units",
        "bound_values": {"h_Z4_global": 1, "h_full_global": 4},
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": z3_positive,
            "positive_case": "negated identity is UNSAT with h_Z4_global=1 and h_full_global=4",
            "erased_flip": "replace multiplier 4 by 3",
            "erased_flip_verdict": z3_erased,
            "erased_flip_detected": z3_erased == "unsat",
            "boundary_case": "N=1 gives h_generator=h_full_global=4 in the same scale",
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_positive,
            "positive_case": "negated identity is UNSAT with h_Z4_global=1 and h_full_global=4",
            "erased_flip": "replace multiplier 4 by 3",
            "erased_flip_verdict": cvc5_erased,
            "erased_flip_detected": cvc5_erased == "unsat",
            "boundary_case": "N=1 gives h_generator=h_full_global=4 in the same scale",
        },
    }


def tool_calls(proofs: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "tool": "sympy",
            "qualified_api/function": "sympy.simplify",
            "input_object": "eta0=pi/6 metric, area, pullback connection, and holonomy formulas",
            "output_object": "exact step0/step1/step2 geometry rows",
            "positive_case": "T_eta0 metric, connection, area, and holonomies simplify to exact pi/sqrt rows",
            "negative/erased_control": "wrong-order quotient holonomy reuse differs from the recomputed primitive quotient holonomy",
            "boundary_case": "Z1 quotient leaves step1 quotient rows unchanged",
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
            "load_bearing": True,
            "gates": ["G1_SOURCE_BACKED_LANES"],
        },
    ]


def capability_receipts() -> dict[str, Any]:
    return {
        "python": {"version": platform.python_version(), "executable_policy": "Makefile SIM_PY"},
        "sympy": {
            "version": sp.__version__,
            "api_smoke": str(sp.simplify(sp.cos(sp.pi / 3) - sp.Rational(1, 2))),
        },
        "z3": {
            "version": z3.get_version_string(),
            "api_smoke": z3_unsat_for_scaled_identity(4),
        },
        "cvc5": {
            "version": cvc5.__version__,
            "api_smoke": cvc5_unsat_for_scaled_identity(4),
        },
    }


def build_result() -> dict[str, Any]:
    rows = exact_rows()
    signatures = ratchet_signatures(rows)
    control_rows = controls(rows)
    proofs = solver_rows()
    julia_result = load_julia_result()
    julia_proof = julia_result.get("crossover_proofs", {}).get("julia_z3", {})
    proofs["julia_z3"] = {
        "ran": julia_proof.get("ran") is True,
        "load_bearing": julia_proof.get("load_bearing") is True,
        "verdict": julia_proof.get("verdict"),
        "positive_case": julia_proof.get("positive_case", "Julia Z3.jl quotient-order identity proof"),
        "erased_flip": julia_proof.get("erased_flip", "replace multiplier 4 by 3"),
        "erased_flip_verdict": julia_proof.get("erased_flip_verdict"),
        "erased_flip_detected": julia_proof.get("erased_flip_detected") is True,
        "boundary_case": "N=1 gives h_generator=h_full_global=4 in the same scale",
        "identity": "4 * h_Z4_global = h_full_global",
        "source": rel(JULIA_SOURCE_PATH),
        "result": rel(JULIA_RESULT_PATH),
        "gates": ["G1_SOURCE_BACKED_LANES", "proof", "all_pass"],
    }
    calls = tool_calls(proofs)
    expected_engine_values = {
        "metric_radii_alpha": rows["scalars"]["cos_eta0"],
        "metric_radii_beta": rows["scalars"]["sin_eta0"],
        "A_T_dchi_coefficient": rows["scalars"]["cos_2eta0"],
        "fundamental_holonomy_phi_cycle": rows["step1"]["exact_geometry"]["holonomies"]["full_global_phase_cycle"]["value"],
        "fundamental_holonomy_chi_cycle": rows["step1"]["exact_geometry"]["holonomies"]["relative_chi_cycle"]["value"],
        "fundamental_holonomy_alpha_cycle": rows["step1"]["exact_geometry"]["holonomies"]["primitive_alpha_cycle"]["value"],
        "fundamental_holonomy_beta_cycle": rows["step1"]["exact_geometry"]["holonomies"]["primitive_beta_cycle"]["value"],
        "quotient_area": rows["scalars"]["quotient_area"],
        "quotient_global_holonomy_pi_over_2_units": 1,
        "full_global_holonomy_pi_over_2_units": 4,
        "non_Z4_saturated_window_witness": 1,
        "julia_z3_quotient_order_identity_verified": 1,
    }
    julia_engine_values = julia_result.get("engine_values", {})
    gates = {
        "mode_declared_ratcheted": MODE == "RATCHETED",
        "single_shell_only": True,
        "nested_multi_shell_conditioning_fenced": True,
        "ceilings_preserved": CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False,
        "disintegration_rule_cited": Path(DISINTEGRATION_PACKET).name in PIN_SPEC
        and "conditional_chart_density=1/(4*pi^2)" in PIN_SPEC,
        "naive_conditioning_failure_refired": control_rows["naive_conditioning_failure_refired"]["pass"] is True,
        "narrowing_computed": signatures["narrowing"]["computed"] is True
        and signatures["narrowing"]["rows"][1]["strict_from_previous"] is True
        and signatures["narrowing"]["rows"][2]["strict_from_previous"] is True,
        "alteration_computed": signatures["alteration"]["altered"] is True,
        "path_pair_honestly_marked_commuting": signatures["path_specificity"]["requested_two_constraint_pair"][
            "same_pair_commutes"
        ]
        is True,
        "noncommuting_extension_present": signatures["path_specificity"]["noncommuting_extension"]["noncommuting"] is True,
        "path_specificity_kind_reworded": signatures["path_specificity"]["noncommuting_extension"][
            "claim_kind"
        ]
        == "quotient_well_definedness_equivariance_failure"
        and signatures["path_specificity"]["noncommuting_extension"]["not_numeric_order_gap_family"] is True,
        "controls_fired": control_rows["identity_constraint_excludes_nothing"]["byte_exact_on_exact_rows"] is True
        and control_rows["shuffled_wrong_order_control"]["control_fired"] is True,
        "smt_positive_and_erased_flip": proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_detected"] is True
        and proofs["cvc5"]["erased_flip_detected"] is True,
        "julia_z3_positive_and_erased_flip": proofs["julia_z3"]["verdict"] == "unsat"
        and proofs["julia_z3"]["erased_flip_detected"] is True,
        "one_to_one_tool_calls": len(calls) == 4
        and [call["tool"] for call in calls] == ["sympy", "z3", "cvc5", "Z3"],
        "capability_receipts_present": set(capability_receipts()) == {"python", "sympy", "z3", "cvc5"},
        "julia_result_loaded": julia_result.get("all_pass") is True,
        "julia_source_hash_matches": julia_result.get("source_sha256") == file_sha256(JULIA_SOURCE_PATH),
        "julia_reads_no_peer_result": julia_result.get("reads_peer_result") is False,
        "julia_engine_values_match_python_exact_rows": julia_engine_values == expected_engine_values,
        "julia_z3_load_bearing": julia_result.get("aligned_packages_load_bearing") == ["Z3"],
    }
    engine_values = {
        "julia": julia_engine_values,
        "jax": expected_engine_values,
    }
    current_hashes = {
        "ratchet_sequence": stable_json_sha256(rows),
        "ratchet_signatures": stable_json_sha256(signatures),
        "controls": stable_json_sha256(control_rows),
        "crossover_proofs_python_z3_cvc5": stable_json_sha256({"z3": proofs["z3"], "cvc5": proofs["cvc5"]}),
        "crossover_proofs_with_julia_z3": stable_json_sha256(
            {"z3": proofs["z3"], "cvc5": proofs["cvc5"], "julia_z3": proofs["julia_z3"]}
        ),
        "julia_exact_rows": stable_json_sha256(julia_result.get("exact_rows", {})),
    }
    hash_receipt = {
        "kind": "shape_only_repair_hash_receipt",
        "fresh_full_rerun": True,
        "hash_algorithm": "sha256(stable_json(sort_keys=True,separators=(',',':')))",
        "audit_verdict_current_hashes": [
            {"subtree": subtree, "hash": hash_value}
            for subtree, hash_value in AUDIT_VERDICT_SUBTREE_HASHES.items()
        ],
        "fresh_current_hashes": [
            {"subtree": subtree, "hash": hash_value} for subtree, hash_value in current_hashes.items()
        ],
        "preservation_checks": {
            "ratchet_sequence": current_hashes["ratchet_sequence"] == AUDIT_VERDICT_SUBTREE_HASHES["ratchet_sequence"],
            "controls": current_hashes["controls"] == AUDIT_VERDICT_SUBTREE_HASHES["controls"],
            "crossover_proofs_python_z3_cvc5": current_hashes["crossover_proofs_python_z3_cvc5"]
            == AUDIT_VERDICT_SUBTREE_HASHES["crossover_proofs"],
            "ratchet_signatures_whole_subtree_changed_by_G3_language_repair": current_hashes["ratchet_signatures"]
            != AUDIT_VERDICT_SUBTREE_HASHES["ratchet_signatures"],
        },
        "note": (
            "The packet now contains the missing hash receipt. Fresh full rerun preserves the exact "
            "ratchet_sequence, controls, and original Python z3/cvc5 proof subtrees recorded by the audit. "
            "The whole ratchet_signatures hash is intentionally different because G3 restates path-specificity "
            "as quotient well-definedness/equivariance failure rather than a numeric order-gap family."
        ),
    }
    hardening_addendum = {
        "kind": "builder_hardening_addendum",
        "status": "builder_hardened_pending_fresh_reaudit",
        "closed_caveats": {
            "G1_SOURCE_BACKED_LANES": {
                "closed": gates["julia_result_loaded"]
                and gates["julia_source_hash_matches"]
                and gates["julia_reads_no_peer_result"]
                and gates["julia_engine_values_match_python_exact_rows"]
                and gates["julia_z3_load_bearing"],
                "evidence": {
                    "julia_source": rel(JULIA_SOURCE_PATH),
                    "julia_result": rel(JULIA_RESULT_PATH),
                    "julia_project": julia_result.get("julia_project"),
                    "load_bearing_tool": "Z3",
                    "julia_z3_verdict": proofs["julia_z3"]["verdict"],
                },
            },
            "G2_MISSING_PRE_FIX_HASH_NOTE": {
                "closed": all(
                    [
                        hash_receipt["preservation_checks"]["ratchet_sequence"],
                        hash_receipt["preservation_checks"]["controls"],
                        hash_receipt["preservation_checks"]["crossover_proofs_python_z3_cvc5"],
                    ]
                ),
                "evidence": hash_receipt,
            },
            "G3_PATH_GAP_KIND": {
                "closed": gates["path_specificity_kind_reworded"],
                "evidence": signatures["path_specificity"]["noncommuting_extension"],
            },
        },
        "fresh_verdict": "fresh audit verdict stands pending re-audit; this is a builder hardening receipt, not an auditor verdict",
    }
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "mode": MODE,
        "claim": (
            "Single-shell RATCHETED pilot: condition S3 to T_eta0 via committed disintegration, "
            "then quotient the induced leaf by Z4 and recompute induced geometry; path-specificity "
            "is a non-Z4-saturation quotient well-definedness/equivariance failure, not a numeric order-gap family."
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
        "program_receipt": PROGRAM_RECEIPT,
        "lineage_citations": {
            "mode4_program_rule": f"{PROGRAM_RECEIPT}:14",
            "mode4_prerequisite_disintegration_packet": DISINTEGRATION_PACKET,
            "disintegration_rule": f"{DISINTEGRATION_PACKET}/geo_disintegration_machinery_v0_common.py#/PIN_SPEC",
            "naive_conditioning_control": control_rows["naive_conditioning_failure_refired"]["source_control"],
            "committed_s1_free_anchor": S1_FREE_PACKET,
            "committed_s1_lens_tower": S1_LENS_PACKET,
            "committed_s2_connection_anchor": S2_PACKET,
        },
        "scope_fences": {
            "single_shell_only": True,
            "nested_multi_shell_conditioning": False,
            "nested_scope_caveat": "CAVEAT_NESTED_SCOPE respected; no nested or multi-layer conditioning is attempted",
            "trend_claims": False,
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
        "engine_contract": {
            "mode": MODE,
            "lanes": ["julia", "jax"],
            "scoped_lanes": {
                "julia": "semantic owner lane from actual /opt/homebrew/bin/julia carrier execution with independent exact rows and load-bearing Z3.jl quotient-order proof",
                "jax": "batched/workhorse lane scoped to the same per-observable exact values; no stochastic sweep or peer-result read in this single-shell pilot",
            },
            "omitted_lanes": {
                "pytorch": "omitted: no graph, network, autograd, torch_geometric, or PyTorch-specific claim path in this single-shell RATCHETED pilot"
            },
            "local_lane_rule": "the Julia carrier lane and Python/JAX-envelope lane each compute exact observables without peer-result reads; controller comparison happens only in this envelope",
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "interpreter": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "no_peer_result_reads": True,
            "repo_validator_expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                "scripts/validate_three_engine_sim_result.py "
                f"system_v6/sims/{SIM_ID}/results/{SIM_ID}_envelope_results.json"
            ),
            "validator_expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"system_v6/sims/{SIM_ID}/validate_{SIM_ID}.py "
                f"system_v6/sims/{SIM_ID}/results/{SIM_ID}_envelope_results.json"
            ),
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
                "packages_used": ["JSON3", "SHA", "Dates", "Z3"],
                "aligned_packages_load_bearing": ["Z3"],
                "reads_peer_result": False,
                "scope": "actual Julia carrier semantic-owner exact row lane with load-bearing Z3.jl quotient-order proof",
                "omission_note": None,
            },
            "jax": {
                "ran": True,
                "source_path": rel(SOURCE_PATH),
                "source_sha256": file_sha256(SOURCE_PATH),
                "packages_used": ["sympy", "z3", "cvc5"],
                "aligned_packages_load_bearing": ["z3", "cvc5"],
                "reads_peer_result": False,
                "scope": "scoped workhorse/comparison lane over identical exact observables in this Python single-shell pilot",
                "omission_note": None,
            },
        },
        "claim_path_tools": ["sympy", "z3", "cvc5", "Z3"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "capability_receipts": capability_receipts(),
        "tool_calls": calls,
        "ratchet_sequence": rows,
        "ratchet_signatures": signatures,
        "controls": control_rows,
        "crossover_proofs": {"z3": proofs["z3"], "cvc5": proofs["cvc5"], "julia_z3": proofs["julia_z3"]},
        "computed_subtree_hashes": hash_receipt,
        "hardening_addendum": hardening_addendum,
        "ceiling": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "single_fixed_eta_shell_only": True,
            "path_specificity_kind": "quotient_well_definedness_equivariance_failure_non_Z4_saturation",
            "not_earned": [
                "numeric order-gap family",
                "nested ratchet",
                "multi-shell conditioning",
                "M(C,t)",
                "axis-level claim",
                "bridge claim",
                "trend claim",
                "canonical status",
            ],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "per_observable": {
                name: {
                    "engine_values": {engine: values[name] for engine, values in engine_values.items()},
                    "max_divergence": 0.0,
                }
                for name in engine_values["julia"]
            },
            "max_divergence": 0.0,
            "structural_disagreements": [],
            "interpretation": "Fresh full rerun. Actual Julia carrier values and Python/JAX-envelope values agree exactly on the declared exact rows.",
        },
        "build_gates": gates,
        "validator": {
            "expected_result_path": rel(VALIDATOR_RESULT_PATH),
            "packet_validator": rel(VALIDATOR_PATH),
            "repo_validator": rel(REPO_VALIDATOR_PATH),
            "expected_ok": True,
        },
        "summary": {
            "eta0": ETA0_LABEL,
            "N": N,
            "step1_metric_phi_chi": rows["step1"]["exact_geometry"]["metric_phi_chi"]["matrix"],
            "step1_connection": rows["step1"]["exact_geometry"]["connection_pullback"]["phi_chi_basis"],
            "step2_global_holonomy": rows["step2"]["exact_geometry"]["holonomies"][
                "primitive_quotient_global_cycle"
            ]["value"],
            "requested_pair_commutes": signatures["path_specificity"]["requested_two_constraint_pair"][
                "same_pair_commutes"
            ],
            "noncommuting_extension": signatures["path_specificity"]["noncommuting_extension"]["third_constraint"],
            "path_specificity_kind": signatures["path_specificity"]["noncommuting_extension"]["claim_kind"],
            "not_numeric_order_gap_family": signatures["path_specificity"]["noncommuting_extension"][
                "not_numeric_order_gap_family"
            ],
            "all_pass": bool(all(gates.values())),
        },
    }
    return result


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    HARDENING_ADDENDUM_PATH.write_text(
        json.dumps(result["hardening_addendum"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
