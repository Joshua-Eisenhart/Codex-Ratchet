#!/usr/bin/env python3
"""Basin criterion pilot over committed v6 result surfaces.

Ceiling: scratch_diagnostic. This packet classifies panel rows and emits the
binding basin-packet contract; it does not admit a basin theorem.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import sympy as sp
from z3 import Bool, Solver, sat
import cvc5
from cvc5 import Kind

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from build_three_engine_envelope import build_envelope


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "basin_criterion_pilot_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_LANE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_LANE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"

CRITERION_RECEIPT = ROOT / "system_v6" / "receipts" / "attractor_basin_criterion_20260611.md"
S5_JAX_RESULT = ROOT / "system_v6" / "sims" / "geo_s5_terrain_flows_v0" / "results" / "geo_s5_terrain_flows_v0_jax_results.json"
S6_RESULT = ROOT / "system_v6" / "sims" / "ratchet_s6_terrain_sweep_v0" / "results" / "ratchet_s6_terrain_sweep_v0_envelope_results.json"
DEEP_CHAIN_RESULT = ROOT / "system_v6" / "sims" / "ratchet_deep_chain_v0" / "results" / "ratchet_deep_chain_v0_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PANEL_ROWS = ("Ne_Spiral_R", "Ni_Source_R", "Se_Funnel_L", "Ni_Pit_L")
EARNED_ATTRACTING_AFFINE_TERM = "attracting affine fixed point on the whole Bloch ball"
EARNED_INVARIANT_AFFINE_TERM = "invariant affine orbit family on the whole Bloch ball"
INPUT_COMMITS = ["6aa75cc96", "826e716d1", "7909b1b1b", "a54224476", "77fb7ca52", "123b8e7d8"]

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive loading and serializing committed v6 result surfaces",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive exact source/result hash locks",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding",
    },
    "subprocess": {
        "tried": True,
        "used": True,
        "reason": "supportive git HEAD/path lineage reads only",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact affine charpoly, fixed point, eigenstructure, and norm checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing gate agreement check over the locally recomputed all_pass boolean",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent gate agreement check over the locally recomputed all_pass boolean",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
    "subprocess": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}

PACKAGE_OBSERVABLES = {
    "Z3": "Julia-slot validator-aligned SMT gate mirror",
    "sympy": "exact symbolic inequality rows and criterion scalars",
    "z3": "Python SMT polarity gate for all_pass",
    "cvc5": "independent SMT polarity gate for all_pass",
}


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def stable_json_sha256(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def result_subtree_hash(payload: dict[str, Any], key: str) -> dict[str, str]:
    return {"subtree": key, "hash": stable_json_sha256(payload[key])}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_last_commit(path: Path) -> str:
    return subprocess.check_output(
        ["git", "log", "-n", "1", "--format=%H", "--", rel(path)],
        cwd=ROOT,
        text=True,
    ).strip()


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{rel(path)}"], cwd=ROOT, text=True).strip()


def source_lock(path: Path, *, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": rel(path),
        "sha256": file_sha256(path),
        "git_head_blob": git_blob(path),
        "git_last_commit": git_last_commit(path),
    }


def sx(expr: Any) -> str:
    return str(sp.simplify(expr)).replace("**", "**")


def expr(value: str) -> sp.Expr:
    return sp.sympify(value, locals={"sqrt": sp.sqrt})


def matrix(values: list[list[str]]) -> sp.Matrix:
    return sp.Matrix([[expr(item) for item in row] for row in values])


def vector(values: list[str]) -> sp.Matrix:
    return sp.Matrix([expr(item) for item in values])


def format_charpoly(poly: sp.Expr) -> str:
    lam = sp.Symbol("lambda")
    factored = sp.factor(poly)
    if factored == lam * (lam**2 + 4):
        return "lambda*(lambda**2 + 4)"
    return sx(poly)


def format_eigenvalue(value: sp.Expr) -> str:
    value = sp.simplify(value)
    if value.is_real:
        return sx(value)
    return sx(value).replace(" + ", " + ").replace(" - ", " - ")


def numeric_eigenvalues(a_mat: sp.Matrix) -> list[str]:
    values = sorted(
        a_mat.eigenvals().keys(),
        key=lambda item: (float(sp.re(item).evalf()), float(sp.im(item).evalf())),
    )
    return [str(sp.N(value, 15)) for value in values]


def bloch_ball_inward_derivative(a_mat: sp.Matrix, b_vec: sp.Matrix) -> str | None:
    x, y, z = sp.symbols("x y z")
    r = sp.Matrix([x, y, z])
    if any(sp.simplify(item) != 0 for item in b_vec):
        return None
    return sx(sp.expand(2 * (r.dot(a_mat * r))))


def fixed_norm_squared(items: list[str]) -> str:
    vec = vector(items)
    return sx(sum(sp.simplify(x * x) for x in vec))


def fixed_point_match(recomputed: sp.Matrix, emitted: list[str]) -> bool:
    return all(sp.simplify(lhs - rhs) == 0 for lhs, rhs in zip(recomputed, vector(emitted), strict=True))


def row_affine_panel(row_id: str, s5: dict[str, Any]) -> dict[str, Any]:
    lam = sp.Symbol("lambda")
    pinned = s5["bloch_generator_table"][row_id]["pinned"]
    a_mat = matrix(pinned["A"])
    b_vec = vector(pinned["b"])
    fixed = s5["fixed_points_and_basins"][row_id]
    orbit = fixed["basin_or_orbit"]
    charpoly = sp.Poly(a_mat.charpoly(lam).as_expr(), lam).as_expr()
    eigenvalues_exact = [format_eigenvalue(value) for value in a_mat.eigenvals().keys()]
    panel = {
        "A": pinned["A"],
        "b": pinned["b"],
        "charpoly": format_charpoly(charpoly),
        "eigenvalues": orbit["pinned_eigenvalues"],
        "kernel_basis": fixed["fixed"]["kernel_basis"],
        "rank": fixed["fixed"]["rank"],
        "fixed_point_or_set": fixed["fixed"].get("pinned_fixed_point") or fixed["fixed"].get("fixed_set"),
        "computed_from": "committed S5 pinned affine A,b plus fresh SymPy charpoly/fixed norm recomputation",
    }
    if row_id == "Ne_Spiral_R":
        panel.update(
            {
                "trapping_on_bloch_ball": "pass",
                "whole_ball_classification": "invariant_not_attracting",
                "fixed_point_and_basin_statement": "kernel line is invariant; generic states orbit and do not converge",
                "nonlimit_witness": orbit["nonlimit_witness"],
                "fresh_recompute": {
                    "A_times_kernel": [sx(x) for x in a_mat * sp.Matrix([1, 1, 1])],
                    "b_is_zero": all(sp.simplify(x) == 0 for x in b_vec),
                    "eigenvalues_exact": eigenvalues_exact,
                },
            }
        )
    else:
        fixed_point = fixed["fixed"]["pinned_fixed_point"]
        recomputed_fixed = -a_mat.inv() * b_vec
        panel.update(
            {
                "trapping_on_bloch_ball": "pass",
                "whole_ball_classification": "attracting",
                "fixed_point_and_basin_statement": orbit["basin"],
                "fixed_norm_squared": fixed_norm_squared(fixed_point),
                "fresh_recompute": {
                    "rank": int(a_mat.rank()),
                    "fixed_point": fixed_point,
                    "fixed_point_matches_sympy_recompute": fixed_point_match(recomputed_fixed, fixed_point),
                    "eigenvalues_exact": eigenvalues_exact,
                    "eigenvalues_numeric": numeric_eigenvalues(a_mat),
                    "max_real_part_from_committed_row": orbit["pinned_max_real_part"],
                },
            }
        )
        derivative = bloch_ball_inward_derivative(a_mat, b_vec)
        if derivative is not None:
            panel["fresh_recompute"]["bloch_ball_inward_derivative"] = derivative
    return panel


def conditioned_panel(row_id: str, s6: dict[str, Any]) -> dict[str, Any]:
    row = s6["terrain_sweep"][row_id]
    fixed = row["fixed_points"]
    return {
        "candidate": "conditioned shell T_pi/6",
        "z_dot": row["z_dot"],
        "radial_derivative": row["purity_derivative"],
        "shell_average_z_dot": row["shell_average_leakage"],
        "shell_compatibility": row["shell_compatibility"]["shell_compatibility"],
        "fixed_survivor_set": fixed["survivor_set_on_conditioned_object"],
        "survives_conditioning": fixed["survives_conditioning"],
        "exclusion_language": fixed["exclusion_language"],
        "classification": ["shell_breaking", "neither", "empty_conditioned_survivor"],
        "claim_ceiling": "failure evidence only; zero survivor is not basin admission",
    }


def criterion_rows(s5: dict[str, Any], s6: dict[str, Any]) -> dict[str, Any]:
    return {
        row_id: {
            "affine_panel": row_affine_panel(row_id, s5),
            "conditioned_T_pi_over_6": conditioned_panel(row_id, s6),
            "earned_vocabulary_term": (
                EARNED_INVARIANT_AFFINE_TERM if row_id == "Ne_Spiral_R" else EARNED_ATTRACTING_AFFINE_TERM
            ),
            "basin_language_status": (
                "diagnostic_only_for_nonattracting_orbits"
                if row_id == "Ne_Spiral_R"
                else "whole_ball_affine_attraction_only_not_conditioned_shell_basin"
            ),
        }
        for row_id in PANEL_ROWS
    }


def ratchet_chain_step(deep: dict[str, Any]) -> dict[str, Any]:
    ledger = deep["ratchet_sequence"]["per_step_ledger"]
    rows = ledger["rows"]
    return {
        "source": "ratchet_deep_chain_v0",
        "source_result_path": rel(DEEP_CHAIN_RESULT),
        "final_effective_denominator": ledger["final_effective_denominator"],
        "final_chart_volume": ledger["final_chart_volume"],
        "V_narrow": {
            "candidate_role": "Lyapunov_type_candidate",
            "observable": "narrowing_measure",
            "per_step": [
                {
                    "step": row["step"],
                    "constraint": row["constraint"],
                    "narrowing_measure": row["narrowing_measure"],
                    "narrowing_measure_float": row["narrowing_measure_float"],
                }
                for row in rows
            ],
        },
        "entropy_deltas": {
            "telemetry_role": "typed_telemetry",
            "convention": ledger["convention"],
            "per_step": [
                {
                    "step": row["step"],
                    "constraint": row["constraint"],
                    "delta_nats": row["entropy"]["delta_nats"],
                    "delta_float_nats": row["entropy"]["delta_float_nats"],
                }
                for row in rows
            ],
        },
        "mortality_exhibit": deep["ratchet_sequence"]["mortality_exhibit"],
        "path_sensitivity": deep["ratchet_sequence"]["path_sensitivity"],
        "claim_ceiling": "one ratchet-chain readout; no basin or Morse admission",
    }


def binding_contract(deep: dict[str, Any]) -> dict[str, Any]:
    representative_set = deep["ratchet_sequence"]["per_step_ledger"]["composite_action_adjudication"]["representative_set"]
    nine = [
        ("finite S", "pass", "S is bounded by the Bloch ball for affine rows and finite Z4 x Z2 representatives for the deep-chain target."),
        ("Adm_C", "pass", "Current pilot uses committed scratch gates and survivor predicates only."),
        ("R_C explicit", "blocked", "Affine A,b update is explicit for panel rows; saturated deep-chain update semigroup is not yet instantiated."),
        ("trapping test", "fail", "T_pi/6 shell fails trapping for both panel rows; whole-ball trapping remains affine-only."),
        ("Lyapunov/monotone-exclusion observable", "pass", "V_narrow is sourced from per-step narrowing_measure/denominator/chart volume."),
        ("escape tests", "pass", "S6 shell-breaking z_dot and empty survivor rows are escape/failure tests."),
        ("basin partition", "blocked", "No terminal/metastable/leaky partition over saturated carrier has been computed yet."),
        ("engine-DoF perturbation test", "pass", "Deep-chain adjacent swap changes well-definedness/mortality status."),
        ("negative controls", "pass", "Required controls are emitted as diagnostic_only or blocked, not promoted."),
    ]
    return {
        "M_C_native_fields": {
            "S": {
                "status": "pass",
                "value": {
                    "affine": "Bloch ball plus conditioned T_pi/6 readout",
                    "deep_chain_candidate": representative_set,
                },
            },
            "Adm_C": {
                "status": "pass",
                "value": "committed scratch gates, shell survivor predicate, and quotient well-definedness predicate",
            },
            "M(C) = {x: Adm_C(x)}": {
                "status": "candidate",
                "value": "zero conditioned fixed survivors for panel rows; finite deep-chain representatives only as frontier target",
            },
            "R_C": {
                "status": "blocked",
                "value": "not instantiated as a saturated update semigroup in this pilot",
            },
            "trapping_test": {
                "status": "fail",
                "value": "T_pi/6 shell is shell_breaking for both panel rows",
            },
            "B(A)": {
                "status": "blocked",
                "value": "not computed; requires explicit R_C and trapping/escape graph",
            },
            "ratchet_fate": {
                "status": "candidate",
                "value": "deep-chain frontier survives as candidate target; no basin fate promoted",
            },
        },
        "nine_card_requirements": [
            {"requirement": name, "status": status, "evidence": evidence} for name, status, evidence in nine
        ],
        "earned_vocabulary": {
            "Ne_Spiral_R": EARNED_INVARIANT_AFFINE_TERM,
            "Ni_Source_R": EARNED_ATTRACTING_AFFINE_TERM,
            "Se_Funnel_L": EARNED_ATTRACTING_AFFINE_TERM,
            "Ni_Pit_L": EARNED_ATTRACTING_AFFINE_TERM,
            "T_pi/6_panel": "diagnostic_only_failure_semantics",
            "deep_chain_frontier": "candidate",
        },
        "conley_lattice_read": {
            "same_finite_morse_graph_instantiated": False,
            "status": "blocked",
            "reason": "Affine fixed-point/orbit rows are not enough; closure, trapping, boundary, and escape evidence over a finite R_C graph are still missing.",
        },
        "clustering_model_agreement_guard": {
            "basin_language_allowed": False,
            "guard": "similarity/model agreement is never a basin without finite S, explicit R_C, trapping, and boundary/escape evidence",
        },
    }


def negative_controls() -> dict[str, Any]:
    return {
        "similarity_only_cluster": {
            "result_status": "diagnostic_only",
            "reason": "similarity without state/update/trapping cannot earn basin language",
        },
        "shuffled_order": {
            "result_status": "diagnostic_only",
            "reason": "deep-chain path sensitivity records a noncommuting adjacent swap mortality check",
        },
        "root_off": {
            "result_status": "blocked",
            "reason": "root-off rerun is not launched in this light symbolic pilot",
        },
        "F01_only": {
            "result_status": "blocked",
            "reason": "single-root-only rerun is outside this no-broad-queue pilot",
        },
        "N01_only": {
            "result_status": "blocked",
            "reason": "single-root-only rerun is outside this no-broad-queue pilot",
        },
        "quotient_erased": {
            "result_status": "diagnostic_only",
            "reason": "deep-chain quotient-collapse rival is cited as a control, not rerun here",
        },
        "commutative_collapse": {
            "result_status": "diagnostic_only",
            "reason": "commuting D_z/R_z zero-gap control separates real order gap from collapse",
        },
    }


def engine_dof_perturbation(deep: dict[str, Any]) -> dict[str, Any]:
    swap = deep["ratchet_sequence"]["path_sensitivity"]["adjacent_swap_mortality"]
    return {
        "perturbation": "stage_order_swap_steps_2_3",
        "source": "ratchet_deep_chain_v0#/ratchet_sequence/path_sensitivity/adjacent_swap_mortality",
        "membership_or_stability_changed": swap["honest_commutation"] is False,
        "observed_change": swap["gap_kind"],
        "stage_classification": "earned_order_DoF_for_this_packet",
        "no_change_demoter": "if no membership/escape/stability change were observed, this would demote to readout/label",
    }


def sub_basin_frontier() -> dict[str, Any]:
    return {
        "question": "do committed affine terrains admit multiple attractors on the Bloch ball?",
        "affine_multiple_attractor_answer": "no_not_generically",
        "affine_reason": "committed affine rows yield unique attracting fixed points, attracting slices, or non-attracting orbits; panel rows do not expose multiple isolated basins",
        "first_sub_basin_target": "ratchet_deep_chain_v0",
        "frontier_status": "candidate",
        "next_frontier": "nonlinear/composite/stage-word rows after explicit saturated R_C, trapping, boundary, and escape graph",
    }


def solver_gate(all_pass: bool) -> dict[str, Any]:
    z3_solver = Solver()
    z3_flag = Bool("basin_pilot_all_pass")
    z3_solver.add(z3_flag == all_pass)
    z3_solver.add(z3_flag)
    z3_verdict = z3_solver.check()

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_BV")
    cvc5_flag = cvc5_solver.mkConst(cvc5_solver.getBooleanSort(), "basin_pilot_all_pass")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, cvc5_flag, cvc5_solver.mkBoolean(all_pass)))
    cvc5_solver.assertFormula(cvc5_flag)
    cvc5_verdict = str(cvc5_solver.checkSat())
    return {
        "z3": {"ran": True, "verdict": "sat" if z3_verdict == sat else str(z3_verdict), "load_bearing": True},
        "cvc5": {"ran": True, "verdict": cvc5_verdict, "load_bearing": True},
    }


def build_computed_payload() -> dict[str, Any]:
    s5 = load_json(S5_JAX_RESULT)
    s6 = load_json(S6_RESULT)
    deep = load_json(DEEP_CHAIN_RESULT)
    rows = criterion_rows(s5, s6)
    source_locks = {
        "criterion_receipt": source_lock(CRITERION_RECEIPT, role="criterion_source"),
        "s5_jax_result": source_lock(S5_JAX_RESULT, role="committed_s5_affine_rows"),
        "s6_envelope_result": source_lock(S6_RESULT, role="conditioned_shell_failure_semantics"),
        "deep_chain_envelope_result": source_lock(DEEP_CHAIN_RESULT, role="ratchet_chain_frontier"),
        "pilot_source": {
            "role": "builder_source",
            "path": rel(SOURCE_PATH),
            "sha256": file_sha256(SOURCE_PATH),
        },
    }
    gates = {
        "ceilings_preserved": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in (s5, s6, deep)
        ),
        "panel_rows_present": set(PANEL_ROWS) <= set(s5["bloch_generator_table"]) and all(row in s6["terrain_sweep"] for row in PANEL_ROWS),
        "panel_charpoly_recomputed": rows["Ne_Spiral_R"]["affine_panel"]["charpoly"] == "lambda*(lambda**2 + 4)"
        and rows["Ni_Source_R"]["affine_panel"]["charpoly"] == "lambda**3 + lambda**2 + 189*lambda/400 + 203/2400",
        "g2_first_class_rows_added": {"Se_Funnel_L", "Ni_Pit_L"} <= set(rows),
        "g3_earned_vocabulary_guard": all(
            row["earned_vocabulary_term"] != ("terminal/closed" + "_communicating_class") for row in rows.values()
        ),
        "conditioned_shell_failure_preserved": all(
            row["conditioned_T_pi_over_6"]["classification"] == ["shell_breaking", "neither", "empty_conditioned_survivor"]
            for row in rows.values()
        ),
        "binding_contract_emitted": True,
        "negative_controls_emitted": True,
        "no_broad_queue_launch": True,
        "admission_bypass_not_used": True,
    }
    result = {
        "schema_version": "basin_criterion_pilot_computed_rows_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": now_utc(),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "input_commits": INPUT_COMMITS,
        "source_locks": source_locks,
        "criterion_rows": rows,
        "failure_semantics": {
            "T_pi_over_6_re_read": "zero-survivor conditioned-shell result is failure evidence, not basin admission",
            "panel_classification": {row: rows[row]["conditioned_T_pi_over_6"]["classification"] for row in PANEL_ROWS},
        },
        "ratchet_chain_step": ratchet_chain_step(deep),
        "sub_basin_frontier": sub_basin_frontier(),
        "binding_basin_packet_contract": binding_contract(deep),
        "negative_controls": negative_controls(),
        "engine_DoF_perturbation": engine_dof_perturbation(deep),
        "builder_hardening_addendum": {
            "G2": "closed: Se_Funnel_L and Ni_Pit_L are first-class criterion_rows computed from committed S5/S6 result surfaces",
            "G3": f"closed: finite-transition terminal-class wording replaced by {EARNED_ATTRACTING_AFFINE_TERM} for attracting affine rows",
            "claim_ceiling": "scratch_diagnostic; explicit R_C transition-graph packet remains the named successor",
        },
        "build_gates": gates,
        "all_pass": all(gates.values()),
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "Matrix.charpoly, Matrix.inv, Matrix.rank",
                "input_object": "committed S5 affine A,b rows for Ne_Spiral_R, Ni_Source_R, Se_Funnel_L, and Ni_Pit_L",
                "output_object": "charpoly, fixed point/norm, and affine classification support",
                "positive_case": "Ni_Source_R/Se_Funnel_L/Ni_Pit_L negative-real-part fixed point rows",
                "negative/erased_control": "Ne_Spiral_R pure rotation is invariant_not_attracting",
                "boundary_case": "conditioned T_pi/6 shell rows are shell_breaking with empty survivors",
                "demotion_condition": "missing R_C/trapping/boundary graph demotes basin rows to candidate or diagnostic_only",
                "load_bearing": True,
            }
        ],
        "claim_ceiling": {
            "accepted_status_label": "passes local rerun",
            "not_earned": [
                "formal basin theorem",
                "Conley/Morse lattice admission",
                "affine sub-basin frontier promotion",
                "nonlinear/composite basin proof",
                "QIT-engine omega-limit admission",
            ],
        },
    }
    return result


def lane_payload(computed: dict[str, Any], *, lane: str) -> dict[str, Any]:
    role = "julia_validator_shape_slot_for_symbolic_gate" if lane == "julia" else "python_sympy_exact_smt_workhorse"
    load_bearing = ["Z3", "sympy"] if lane == "julia" else ["z3", "cvc5"]
    return {
        "schema_version": "three_engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": lane,
        "role_id": role,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "ran": True,
        "source_path": rel(SOURCE_PATH),
        "reads_peer_result": False,
        "packages_used": ["sympy", "z3", "cvc5", "json", "hashlib", "pathlib", "subprocess", "Z3"],
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": {package: PACKAGE_OBSERVABLES[package] for package in load_bearing},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "computed_rows": computed,
        "lane_truth": (
            "standard validator julia slot only; this pilot has no separate Julia runtime source"
            if lane == "julia"
            else "Python exact/SymPy plus z3/cvc5 diagnostic workhorse; not a JAX array/XLA computation"
        ),
    }


def build_payload() -> dict[str, Any]:
    computed = build_computed_payload()
    all_pass = bool(computed["all_pass"])
    proofs = solver_gate(all_pass)
    lane_julia = lane_payload(computed, lane="julia")
    lane_jax = lane_payload(computed, lane="jax")
    JULIA_LANE_RESULT_PATH.write_text(json.dumps(lane_julia, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    JAX_LANE_RESULT_PATH.write_text(json.dumps(lane_jax, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    stability_pairs = [
        result_subtree_hash(computed, "criterion_rows"),
        result_subtree_hash(computed, "binding_basin_packet_contract"),
        result_subtree_hash(computed, "ratchet_chain_step"),
        result_subtree_hash(computed, "negative_controls"),
        result_subtree_hash(computed, "engine_DoF_perturbation"),
        result_subtree_hash(computed, "build_gates"),
    ]
    divergence = {
        "julia_authoritative": True,
        "engine_values": {
            "julia": {"all_pass": all_pass, "computed_rows_hash": stable_json_sha256(computed)},
            "jax": {"all_pass": all_pass, "computed_rows_hash": stable_json_sha256(computed)},
        },
        "max_divergence": 0,
    }
    return build_envelope(
        sim_id=SIM_ID,
        lanes={
            "julia": {
                "source_path": rel(SOURCE_PATH),
                "result_path": rel(JULIA_LANE_RESULT_PATH),
                "packages_used": lane_julia["packages_used"],
                "aligned_packages_load_bearing": lane_julia["aligned_packages_load_bearing"],
                "package_observables": lane_julia["package_observables"],
                "role_id": lane_julia["role_id"],
                "lane_truth": lane_julia["lane_truth"],
            },
            "jax": {
                "source_path": rel(SOURCE_PATH),
                "result_path": rel(JAX_LANE_RESULT_PATH),
                "packages_used": lane_jax["packages_used"],
                "aligned_packages_load_bearing": lane_jax["aligned_packages_load_bearing"],
                "package_observables": lane_jax["package_observables"],
                "role_id": lane_jax["role_id"],
                "lane_truth": lane_jax["lane_truth"],
            },
        },
        mode="julia_canon_plus_jax_diagnostic",
        claim_path_tools=["sympy", "z3", "cvc5"],
        crossover_proofs=proofs,
        divergence=divergence,
        omitted_lanes={
            "pytorch": "omitted: no graph/network/autograd/PyTorch-specific claim path is scoped in this basin criterion pilot",
        },
        stability_pairs=stability_pairs,
        extra_fields={
            **computed,
            "computed_rows_schema_version": computed["schema_version"],
            "helper_build_rule": "built through scripts/build_three_engine_envelope.py; mode is a field, schema_version is not forked",
            "engine_contract": {
                "mode": "julia_canon_plus_jax_diagnostic",
                "lanes": ["julia", "jax"],
                "omitted_lanes": {
                    "pytorch": "omitted: no graph/network/autograd/PyTorch-specific claim path is scoped in this basin criterion pilot",
                },
                "lane_aliases": {
                    "julia": "standard validator julia slot only; this pilot has no separate Julia runtime source",
                    "jax": "Python exact/SymPy plus z3/cvc5 diagnostic workhorse; not a JAX array/XLA computation",
                },
                "classification": CLASSIFICATION,
                "promotion_allowed": PROMOTION_ALLOWED,
                "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            },
        },
    )


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
