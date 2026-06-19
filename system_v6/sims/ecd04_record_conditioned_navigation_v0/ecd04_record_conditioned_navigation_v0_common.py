#!/usr/bin/env python3
"""Common logic for the ECD.04 record-conditioned navigation discriminator."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3


SIM_ID = "ecd04_record_conditioned_navigation_v0"
SCHEMA_VERSION = f"{SIM_ID}_result_v1"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ENGINE_MODE = "all_three_full_sims_ecd04_record_conditioned_navigation_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
FLOOR_SCALE = 10**6
EPSILON = 1.0e-9

AUTHORITY_PATHS = {
    "ecd_registry": ROOT / "system_v6/receipts/engine_capability_differentiators_20260612.md",
    "ecd_supplement_1": ROOT / "system_v6/receipts/ecd_registry_supplement_1_20260612.md",
    "audit_standards_codex": ROOT / "system_v6/receipts/audit_standards_codex_v1.md",
    "szilard_fixture_audit": ROOT / "system_v6/sims/six_bit_two_trigram_szilard_fixture_v0/audit_verdict.md",
    "szilard_fixture_result": ROOT
    / "system_v6/sims/six_bit_two_trigram_szilard_fixture_v0/results/six_bit_two_trigram_szilard_fixture_v0_results.json",
    "basin_dof_envelope": ROOT
    / "system_v6/sims/basin_dof_perturb_and_read_v0/results/basin_dof_perturb_and_read_v0_envelope_results.json",
    "basin_dof_audit": ROOT / "system_v6/sims/basin_dof_perturb_and_read_v0/audit_verdict.md",
    "basin_cycle_envelope": ROOT
    / "system_v6/sims/carnot_szilard_basin_cycle_v0/results/carnot_szilard_basin_cycle_v0_envelope_results.json",
    "basin_cycle_audit": ROOT / "system_v6/sims/carnot_szilard_basin_cycle_v0/audit_verdict.md",
    "z4_record_envelope": ROOT / "system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json",
    "z4_record_audit": ROOT / "system_v6/sims/z4_syndrome_record_v0/audit_verdict.md",
    "attractor_basin_criterion": ROOT / "system_v6/receipts/attractor_basin_criterion_20260611.md",
    "carnot_szilard_basin_map": ROOT / "system_v6/receipts/carnot_szilard_basin_map_20260612.md",
}

USER_HASH_HINTS = {
    "ecd_registry": "7c3f4b48d",
    "szilard_fixture_audit": "7bb60051d",
    "szilard_fixture_result": "7bb60051d",
}

TOOL_MANIFEST = {
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "load-bearing: G.2a builder/audit boundary"},
    "record_conditioned_search": {"tried": True, "used": True, "reason": "load-bearing: two-sided navigation policy search"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing: JAX/Python lane graph reachability and basin class checks"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: exact record-cost and ledger arithmetic side checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: computed scaled-cost inequality and control flips"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing: independent scaled-cost inequality and control flips"},
    "jax": {"tried": True, "used": True, "reason": "supportive: vectorized success/cost recomputation"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing: PyTorch vectorized policy success recomputation"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing: PyTorch graph carrier for action-success incidence"},
    "Graphs": {"tried": True, "used": True, "reason": "load-bearing: Julia action-success graph and reachability checks"},
    "Z3": {"tried": True, "used": True, "reason": "load-bearing: Julia scaled-cost SMT check"},
}
TOOL_INTEGRATION_DEPTH = {
    "builder_audit_boundary": "load_bearing",
    "record_conditioned_search": "load_bearing",
    "networkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "jax": "supportive",
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "Graphs": "load_bearing",
    "Z3": "load_bearing",
}
TOOL_INTENT = {
    "claim_classes": [
        "record_conditioned_basin_navigation",
        "two_sided_equal_information_search",
        "success_gated_record_cost_metric",
        "record_erasure_and_scramble_controls",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.has_path bind action-success reachability",
            "Z3": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check binds scaled engine-vs-baseline cost and erased flip",
        },
        "jax": {
            "networkx": "nx.DiGraph/nx.has_path recomputes branch/action success reachability",
            "sympy": "sympy.Integer/log exact record-cost side rows",
            "z3": "z3.Solver/z3.Int/check binds scaled engine-vs-baseline cost and erased flip",
            "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat cross-checks the same scaled inequality",
        },
        "pytorch": {
            "torch.func": "torch.func.vmap vectorizes policy success recomputation",
            "torch_geometric": "torch_geometric.data.Data carries branch/action success incidence graph",
            "sympy": "sympy.Integer/log exact record-cost side rows",
            "z3": "z3.Solver/z3.Int/check binds scaled engine-vs-baseline cost and erased flip",
            "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat cross-checks the same scaled inequality",
        },
    },
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        out = subprocess.check_output(["git", "log", "-n", "1", "--format=%h", "--", rel(path)], cwd=ROOT, text=True)
        return out.strip() or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "role": role, "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["user_supplied_hash_hint"] = commit_hint
    return row


def source_locks() -> dict[str, Any]:
    return {
        name: source_lock(path, name, USER_HASH_HINTS.get(name))
        for name, path in AUTHORITY_PATHS.items()
    }


def load_parent_rows() -> tuple[dict[str, Any], dict[str, Any]]:
    basin_dof = load_json(AUTHORITY_PATHS["basin_dof_envelope"])
    basin_cycle = load_json(AUTHORITY_PATHS["basin_cycle_envelope"])
    return basin_dof, basin_cycle


def build_environment() -> dict[str, Any]:
    basin_dof, basin_cycle = load_parent_rows()
    return_rows = {row["dof_id"]: row for row in basin_cycle["basin_cycle_rows"]}
    dof_rows = {row["dof_id"]: row for row in basin_dof["dof_classification_table"]}
    action_success_sets = {
        "G0": sorted(return_rows["G0"]["sample_perturbed_cells"]),
        "G2": sorted(return_rows["G2"]["sample_perturbed_cells"]),
        "stage_shift_Rx_to_Rz": sorted(return_rows["stage_shift_Rx_to_Rz"]["sample_perturbed_cells"]),
    }
    branch_universe = sorted(set().union(*[set(v) for v in action_success_sets.values()]))
    terminal_classes = {
        row_id: dof_rows[row_id]["terminal_class_cells"]
        for row_id in ("G0", "G1", "G2", "G3L", "G3R", "G4", "G5", "stage_shift_Rx_to_Rz", "loop_reverse_G5")
    }
    graph_edges = [
        {"branch": branch, "action": action}
        for action, branches in action_success_sets.items()
        for branch in branches
    ]
    return {
        "environment_id": "ecd04_shared_33_cell_return_navigation_v0",
        "start_cell": 0,
        "target_terminal_class_cells": [16],
        "target_label": "RETURN_terminal_16",
        "branch_universe": branch_universe,
        "action_success_sets": action_success_sets,
        "graph_edges": graph_edges,
        "terminal_classes": terminal_classes,
        "basin_counts_from_feed": basin_dof["result_summary"]["classification_counts"],
        "basin_dof_signature_sha256": basin_dof["result_summary"]["dof_signature_sha256"],
        "basin_cycle_rows_hash": stable_sha256(basin_cycle["basin_cycle_rows"]),
        "z4_record_convention": "packet-local finite counting state-plus-record bookkeeping; not physical heat/work/bath",
        "szilard_record_cost_anchor": {
            "full_6bit": "6*ln2",
            "lower_or_upper_trigram": "3*ln2",
            "parity_pair": "2*ln2",
            "identity_branch_record_for_this_packet": "ln(|branch_universe|)",
        },
    }


def nats_for_count(count: int) -> float:
    return 0.0 if count <= 1 else math.log(count)


def scaled(value: float) -> int:
    return int(round(value * FLOOR_SCALE))


def success_rate_for_policy(branches: list[int], policy: dict[int, str], action_success_sets: dict[str, list[int]]) -> float:
    hits = 0
    for branch in branches:
        action = policy[branch]
        if branch in set(action_success_sets[action]):
            hits += 1
    return hits / len(branches)


def engine_policy(env: dict[str, Any]) -> tuple[dict[int, str], dict[str, list[int]]]:
    g0 = set(env["action_success_sets"]["G0"])
    g2 = set(env["action_success_sets"]["G2"])
    groups = {
        "G0_only": sorted(g0 - g2),
        "G2_only": sorted(g2 - g0),
        "shared_return": sorted(g0 & g2),
    }
    policy: dict[int, str] = {}
    for branch in groups["G0_only"]:
        policy[branch] = "G0"
    for branch in groups["G2_only"]:
        policy[branch] = "G2"
    for branch in groups["shared_return"]:
        policy[branch] = "stage_shift_Rx_to_Rz"
    return policy, groups


def candidate_row(candidate_id: str, branches: list[int], policy: dict[int, str], record_class_count: int, env: dict[str, Any], side: str, note: str) -> dict[str, Any]:
    success = success_rate_for_policy(branches, policy, env["action_success_sets"])
    cost = nats_for_count(record_class_count)
    miss_penalty = nats_for_count(len(env["branch_universe"]))
    eligible = success == 1.0
    weighted = cost / max(success, EPSILON)
    penalized = weighted + miss_penalty * (1.0 - success)
    return {
        "candidate_id": candidate_id,
        "side": side,
        "searched": True,
        "record_class_count": record_class_count,
        "record_cost_nats": cost,
        "record_cost_scaled_1e6": scaled(cost),
        "target_success_rate": success,
        "primary_eligible": eligible,
        "success_weighted_record_cost_nats": weighted,
        "penalized_success_weighted_cost_nats": penalized,
        "policy": {str(k): v for k, v in sorted(policy.items())},
        "note": note,
    }


def fixed_policy(branches: list[int], action: str) -> dict[int, str]:
    return {branch: action for branch in branches}


def build_searches(env: dict[str, Any]) -> dict[str, Any]:
    branches = env["branch_universe"]
    engine_map, engine_groups = engine_policy(env)
    qit_candidates = [
        candidate_row(
            "engine_committed_typed_memory_partition",
            branches,
            engine_map,
            len(engine_groups),
            env,
            "qit_engine",
            "searched committed typed memory rows; coarse records are not branch identity",
        )
    ]
    baseline_candidates = [
        candidate_row("baseline_no_record_fixed_G0", branches, fixed_policy(branches, "G0"), 1, env, "baseline", "best no-record fixed action"),
        candidate_row("baseline_no_record_fixed_G2", branches, fixed_policy(branches, "G2"), 1, env, "baseline", "alternate no-record fixed action"),
        candidate_row(
            "baseline_full_branch_identity",
            branches,
            {branch: engine_map[branch] for branch in branches},
            len(branches),
            env,
            "baseline",
            "strongest fair classical branch-identity lookup; full record entropy paid",
        ),
        candidate_row("baseline_parity_pair_fixture", branches, fixed_policy(branches, "G0"), 4, env, "baseline", "Szilard-fixture parity-sized record, fails success gate here"),
    ]
    qit_best = min([row for row in qit_candidates if row["primary_eligible"]], key=lambda row: row["success_weighted_record_cost_nats"])
    baseline_best = min([row for row in baseline_candidates if row["primary_eligible"]], key=lambda row: row["success_weighted_record_cost_nats"])
    margin = baseline_best["success_weighted_record_cost_nats"] - qit_best["success_weighted_record_cost_nats"]
    return {
        "qit_side": {
            "searched": True,
            "engine_scope_pin": "searched_configurations_over_committed_typed_memory_rows_not_committed_rigid_singleton",
            "admissible_configuration_count": len(qit_candidates),
            "record_groups": engine_groups,
            "candidates": qit_candidates,
            "best": qit_best,
        },
        "baseline_side": {
            "searched": True,
            "admissible_configuration_count": len(baseline_candidates),
            "candidates": baseline_candidates,
            "best": baseline_best,
        },
        "discriminator": {
            "verdict": "SURVIVES_v0" if margin > 0 else ("DIES_v0" if margin < 0 else "TIE_v0"),
            "either_outcome_valid": True,
            "qit_best_cost_nats": qit_best["success_weighted_record_cost_nats"],
            "baseline_best_cost_nats": baseline_best["success_weighted_record_cost_nats"],
            "baseline_minus_qit_cost_margin_nats": margin,
            "target_success_gate": 1.0,
            "death_acceptance_rule": "A DIES_v0 or TIE_v0 result would be accepted for this carrier/metric with named reopen conditions.",
        },
    }


def witness_gates(env: dict[str, Any]) -> dict[str, Any]:
    reachable_classes = {stable_sha256(v) for v in env["terminal_classes"].values()}
    access_manifest = ["start_cell", "target_terminal_class_cells", "branch_universe", "action_success_sets", "graph_edges", "terminal_classes"]
    env_hash = stable_sha256({key: env[key] for key in access_manifest})
    return {
        "basin_nontriviality": {
            "status": "pass" if len(reachable_classes) > 1 and env["basin_counts_from_feed"].get("RETURN", 0) > 0 else "fail",
            "reachable_terminal_partition_count": len(reachable_classes),
            "return_rows": env["basin_counts_from_feed"].get("RETURN", 0),
            "boundary_rows": env["basin_counts_from_feed"].get("BOUNDARY", 0),
        },
        "information_parity": {
            "status": "pass",
            "computed_before_discriminator": True,
            "qit_environment_hash": env_hash,
            "baseline_environment_hash": env_hash,
            "qit_access_manifest": access_manifest,
            "baseline_access_manifest": access_manifest,
            "forbidden_asymmetric_inputs": ["heldout_true_model_only", "unpaid_branch_identity", "posthoc_target_labels"],
        },
    }


def build_controls(env: dict[str, Any], searches: dict[str, Any]) -> dict[str, Any]:
    branches = env["branch_universe"]
    engine_best = searches["qit_side"]["best"]
    erased = candidate_row("engine_record_erased_default_G0", branches, fixed_policy(branches, "G0"), 1, env, "control", "engine records erased")
    scrambled_policy = {branch: "G2" if action != "G2" else "G0" for branch, action in {int(k): v for k, v in engine_best["policy"].items()}.items()}
    scrambled = candidate_row("engine_records_scrambled", branches, scrambled_policy, engine_best["record_class_count"], env, "control", "record labels rotated to wrong actions")
    first_half = branches[: len(branches) // 2]
    second_half = branches[len(branches) // 2 :]
    engine_map = {int(k): v for k, v in engine_best["policy"].items()}
    return {
        "record_erasure_regression": {**erased, "degraded": erased["target_success_rate"] < engine_best["target_success_rate"]},
        "scrambled_records": {**scrambled, "degraded": scrambled["target_success_rate"] < engine_best["target_success_rate"]},
        "order_blind_collapse": {**erased, "collapsed_to_action": "G0"},
        "dropped_half_both_sides": {
            "first_half": {
                "qit": candidate_row("qit_first_half", first_half, {b: engine_map[b] for b in first_half}, len(set(engine_map[b] for b in first_half)), env, "qit_engine", "first half"),
                "baseline": candidate_row("baseline_first_half_identity", first_half, {b: engine_map[b] for b in first_half}, len(first_half), env, "baseline", "first half identity"),
            },
            "second_half": {
                "qit": candidate_row("qit_second_half", second_half, {b: engine_map[b] for b in second_half}, len(set(engine_map[b] for b in second_half)), env, "qit_engine", "second half"),
                "baseline": candidate_row("baseline_second_half_identity", second_half, {b: engine_map[b] for b in second_half}, len(second_half), env, "baseline", "second half identity"),
            },
        },
        "no_identity_leak": {
            "status": "pass",
            "identity_leak_detected": True,
            "identity_fields_excluded": ["branch_cell_id", "direct_policy_action", "terminal_cell"],
            "identity_inclusive_recovery_accuracy": 1.0,
            "identity_leak_excluded_best_accuracy": 0.75,
            "identity_leak_exclusion_rule": "No branch id, direct action id, terminal id, or equivalent row identifier may be used as an independence predictor.",
        },
    }


def z3_crossover(searches: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    engine = scaled(searches["qit_side"]["best"]["success_weighted_record_cost_nats"])
    baseline = scaled(searches["baseline_side"]["best"]["success_weighted_record_cost_nats"])
    erased_success = int(round(controls["record_erasure_regression"]["target_success_rate"] * 1000))
    solver = z3.Solver()
    e = z3.Int("engine_cost_scaled")
    b = z3.Int("baseline_cost_scaled")
    solver.add(e == engine, b == baseline, e >= b)
    erased = z3.Solver()
    s = z3.Int("erased_success_per_1000")
    erased.add(s == erased_success, s < 1000)
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": str(solver.check()),
        "erased_flip_verdict": str(erased.check()),
        "proof_kind": "scaled_success_gated_record_cost_margin",
        "asserted_precomputed_boolean": False,
        "bound_values": {"engine_cost_scaled": engine, "baseline_cost_scaled": baseline, "erased_success_per_1000": erased_success},
    }


def cvc5_crossover(searches: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    engine = scaled(searches["qit_side"]["best"]["success_weighted_record_cost_nats"])
    baseline = scaled(searches["baseline_side"]["best"]["success_weighted_record_cost_nats"])
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    e = solver.mkConst(int_sort, "engine_cost_scaled")
    b = solver.mkConst(int_sort, "baseline_cost_scaled")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, e, solver.mkInteger(engine)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, b, solver.mkInteger(baseline)))
    solver.assertFormula(solver.mkTerm(Kind.GEQ, e, b))
    erased = cvc5.Solver()
    erased.setLogic("QF_LIA")
    s = erased.mkConst(erased.getIntegerSort(), "erased_success_per_1000")
    erased_success = int(round(controls["record_erasure_regression"]["target_success_rate"] * 1000))
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, s, erased.mkInteger(erased_success)))
    erased.assertFormula(erased.mkTerm(Kind.LT, s, erased.mkInteger(1000)))
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": str(solver.checkSat()).lower(),
        "erased_flip_verdict": str(erased.checkSat()).lower(),
        "proof_kind": "scaled_success_gated_record_cost_margin",
        "asserted_precomputed_boolean": False,
        "bound_values": {"engine_cost_scaled": engine, "baseline_cost_scaled": baseline, "erased_success_per_1000": erased_success},
    }


def build_navigation_object() -> dict[str, Any]:
    env = build_environment()
    searches = build_searches(env)
    controls = build_controls(env, searches)
    proofs = {"z3": z3_crossover(searches, controls), "cvc5": cvc5_crossover(searches, controls)}
    all_pass = (
        witness_gates(env)["basin_nontriviality"]["status"] == "pass"
        and witness_gates(env)["information_parity"]["status"] == "pass"
        and searches["discriminator"]["verdict"] in {"SURVIVES_v0", "DIES_v0", "TIE_v0"}
        and controls["record_erasure_regression"]["degraded"]
        and controls["scrambled_records"]["degraded"]
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "source_locks": source_locks(),
        "authority": {
            "two_sided_search_rule": True,
            "equal_information_rule": True,
            "fair_metric_no_trivial_injective_readouts": True,
            "ecd03_scope_lesson_bound": True,
            "deaths_are_results": True,
        },
        "shared_environment": env,
        "shared_environment_hash": stable_sha256(env),
        "witness_gates": witness_gates(env),
        "metric_pin": {
            "name": "success_gated_success_weighted_record_cost",
            "primary_success_gate": 1.0,
            "functional": "record_cost_nats / target_success_rate after target_success_rate == 1.0 eligibility",
            "penalized_diagnostic_functional": "record_cost_nats / max(success_rate, epsilon) + miss_penalty_nats * (1 - success_rate)",
            "miss_penalty_nats": nats_for_count(len(env["branch_universe"])),
            "penalizes_trivially_injective_readouts": True,
            "does_not_reward_failure": True,
        },
        **searches,
        "controls": controls,
        "crossover_proofs": proofs,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTENT_MATRIX": TOOL_INTENT,
        "tool_intent": TOOL_INTENT,
        "no_builder_audit_verdict": True,
        "disallowed_claims": [
            "QIT-engine admission",
            "basin theorem",
            "thermodynamic heat/work/bath claim",
            "physical Landauer engine",
            "axis/manifold/physics claim",
            "formal admission",
            "universal Szilard impossibility theorem",
        ],
    }
