#!/usr/bin/env python3
"""Fail-closed code gate for the V8 nonofficial stress campaign."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "campaign_spec.json"
PREREG_PATH = HERE / "preregistration.json"
EXECUTION_PATH = HERE / "results" / "campaign_execution.json"
OUT_PATH = HERE / "results" / "campaign_validation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(raw: str, root: Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else root / path


def find_case(execution: dict[str, Any], case_id: str) -> dict[str, Any]:
    return next((case for case in execution.get("cases", []) if case.get("case_id") == case_id), {})


def find_step(execution: dict[str, Any], case_id: str, step_id: str) -> dict[str, Any]:
    case = find_case(execution, case_id)
    return next((step for step in case.get("steps", []) if step.get("step_id") == step_id), {})


def combined_log(step: dict[str, Any]) -> str:
    return f"{step.get('stdout_tail', '')}\n{step.get('stderr_tail', '')}".lower()


def validate_payload(
    spec: dict[str, Any],
    prereg: dict[str, Any],
    execution: dict[str, Any],
    *,
    verify_live_files: bool,
) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    evidence: dict[str, Any] = {}

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    root = Path(spec["frozen_source_state"]["repo_root"])
    deep_root = Path(spec["frozen_source_state"]["deep_stack_repo_root"])
    first_root = Path(spec["frozen_source_state"]["first_rung_repo_root"])

    require(execution.get("schema") == "codex_ratchet.v8_nonofficial_stress_campaign.execution.v1", "bad execution schema")
    require(execution.get("campaign_id") == spec.get("campaign_id") == prereg.get("campaign_id"), "campaign id mismatch")
    false_fields = (
        "promotion_allowed",
        "formal_admission_allowed",
        "release_eligible",
        "official_launch_allowed",
        "scientific_claim_proven",
    )
    for field in false_fields:
        require(spec.get(field) is False, f"spec {field} must remain false")
        require(prereg.get(field) is False, f"preregistration {field} must remain false")
        require(execution.get(field) is False, f"execution {field} must remain false")
    require(spec.get("llm_gate_allowed") is False, "spec LLM gate fence opened")
    require(prereg.get("llm_gate_allowed") is False, "preregistration LLM gate fence opened")
    require(execution.get("llm_gate_used") is False, "execution used an LLM gate")
    require(execution.get("install_attempted") is False, "execution attempted an install")
    require(execution.get("all_systems_green") is False, "all_systems_green must remain false while preserved reds exist")
    require(execution.get("spec_sha256") == prereg.get("source_state", {}).get("spec_sha256"), "execution spec hash mismatch")
    require(execution.get("preregistration_sha256") == sha256(PREREG_PATH), "execution preregistration hash mismatch")
    require(execution.get("blocked_cases") == spec.get("blocked_cases"), "blocked cases changed or disappeared")

    expected_case_ids = [case["case_id"] for case in spec["cases"]]
    actual_case_ids = [case.get("case_id") for case in execution.get("cases", [])]
    require(actual_case_ids == expected_case_ids, "case order or membership differs from frozen spec")
    spec_by_id = {case["case_id"]: case for case in spec["cases"]}
    for case_id in expected_case_ids:
        declared = spec_by_id[case_id]
        observed = find_case(execution, case_id)
        require(observed.get("cohort") == declared.get("cohort"), f"{case_id}: cohort drift")
        require(observed.get("claim_ceiling") == declared.get("claim_ceiling"), f"{case_id}: claim ceiling drift")
        require(observed.get("all_expected_outcomes_observed") is True, f"{case_id}: expected outcome mismatch")
        require(observed.get("all_required_artifacts_present") is True, f"{case_id}: required artifact missing")
        expected_steps = declared["steps"]
        actual_steps = observed.get("steps", [])
        require([row.get("step_id") for row in actual_steps] == [row["step_id"] for row in expected_steps], f"{case_id}: step ledger drift")
        for wanted, got in zip(expected_steps, actual_steps):
            label = f"{case_id}/{wanted['step_id']}"
            require(got.get("executed") is True, f"{label}: step not executed")
            require(got.get("command") == wanted["command"], f"{label}: command drift")
            require(got.get("receipt_role") == wanted["receipt_role"], f"{label}: receipt role drift")
            require(got.get("expected_exit") == wanted["expected_exit"], f"{label}: expected exit drift")
            require(got.get("expected_exit_observed") is True, f"{label}: expected exit not observed")
            require(got.get("timed_out") is False, f"{label}: command timed out")
            if wanted["expected_exit"] == "zero":
                require(got.get("returncode") == 0, f"{label}: expected zero exit")
            elif wanted["expected_exit"] == "nonzero":
                require(isinstance(got.get("returncode"), int) and got["returncode"] != 0, f"{label}: expected preserved nonzero exit")
            if verify_live_files:
                for stream in ("stdout", "stderr"):
                    state = got.get(stream, {})
                    path = Path(state.get("path", ""))
                    require(path.is_file(), f"{label}: {stream} log missing")
                    if path.is_file():
                        require(sha256(path) == state.get("sha256"), f"{label}: {stream} log hash drift")

        recorded_artifacts = observed.get("artifacts_after", [])
        require(len(recorded_artifacts) == len(declared.get("required_artifacts", [])), f"{case_id}: artifact ledger length drift")
        for raw, state in zip(declared.get("required_artifacts", []), recorded_artifacts):
            path = resolve(raw, root)
            require(state.get("path") == str(path), f"{case_id}: artifact path drift: {raw}")
            require(state.get("exists") is True, f"{case_id}: artifact not recorded as present: {raw}")
            if verify_live_files:
                require(path.is_file(), f"{case_id}: live artifact missing: {path}")
                if path.is_file():
                    require(sha256(path) == state.get("sha256"), f"{case_id}: live artifact hash drift: {path}")

    require(execution.get("all_expected_outcomes_observed") is True, "campaign expected-outcome ledger is red")
    require(execution.get("all_required_artifacts_present") is True, "campaign artifact ledger is red")
    require(execution.get("execution_integrity_pass") is True, "campaign execution integrity is red")

    # Preflight: canonical carrier green and isolated-worktree portability red must both survive.
    preflights: dict[str, Any] = {}
    for binding in prereg.get("source_state", {}).get("preflight_bindings", []):
        path = Path(binding["absolute_path"])
        if not path.is_file():
            require(False, f"preflight receipt missing: {path}")
            continue
        payload = load_json(path)
        counts = payload.get("summary", {}).get("counts")
        require(counts == binding.get("expected_counts"), f"preflight counts changed: {binding['role']}")
        require(payload.get("promotion_allowed") is False and payload.get("formal_admission_allowed") is False, f"preflight ceiling opened: {binding['role']}")
        if verify_live_files:
            require(sha256(path) == binding.get("sha256"), f"preflight hash drift: {binding['role']}")
        preflights[binding["role"]] = {"counts": counts, "ok": payload.get("summary", {}).get("ok")}
    require(preflights.get("preserved_isolated_worktree_red", {}).get("counts", {}).get("fail") == 3, "isolated portability red was erased")
    require(preflights.get("canonical_carrier_control", {}).get("counts", {}).get("fail") == 0, "canonical carrier control is not green")
    evidence["preflight"] = preflights

    # Fresh finite deep-stack estate.
    estate_path = deep_root / "system_v5/ops/tooling/deep_stack_stress_20260714/results/deep_stack_estate_v8_nonofficial_regression_20260715.json"
    validation_path = deep_root / "system_v5/ops/tooling/deep_stack_stress_20260714/results/deep_stack_validation_v8_nonofficial_regression_20260715.json"
    estate = load_json(estate_path) if estate_path.is_file() else {}
    deep_validation = load_json(validation_path) if validation_path.is_file() else {}
    producer = estate.get("producer_summary", {})
    require(estate.get("schema") == "codex-ratchet.deep-stack-estate-receipt.v1", "deep-stack estate schema mismatch")
    require(producer.get("registry_tool_count") == 139, "deep-stack roster is not 139")
    require(producer.get("deep_stress_tool_count") == 95, "deep-stack required roster is not 95")
    require(producer.get("integration_edge_count") == 29, "deep-stack edge roster is not 29")
    require(producer.get("operational_pass_count") == 95 and producer.get("operational_red_count") == 0, "deep-stack operational rows are not 95/95")
    require(producer.get("operational_red_edge_count") == 0, "deep-stack edge red remains")
    require(producer.get("raw_reuse_used") is False and estate.get("raw_reuse_used") is False, "deep-stack raw receipt reuse occurred")
    require(len(estate.get("tool_receipts", [])) == 139, "deep-stack tool receipt cardinality mismatch")
    require(len(estate.get("integration_edge_receipts", [])) == 29, "deep-stack edge receipt cardinality mismatch")
    require(deep_validation.get("receipt_valid") is True and deep_validation.get("operational_pass") is True, "strict deep-stack validator is not green")
    deep_summary = deep_validation.get("summary", {})
    require(deep_summary.get("required_operational_count") == 95, "deep-stack validation required count mismatch")
    require(deep_summary.get("operational_pass_count") == 95 and deep_summary.get("operational_red_count") == 0, "deep-stack validation pass count mismatch")
    require(deep_summary.get("integration_edge_count") == 29 and deep_summary.get("integration_edge_red_count") == 0, "deep-stack validation edge count mismatch")
    require(estate.get("promotion_allowed") is False and estate.get("release_eligible") is False and estate.get("scientific_claim_proven") is False, "deep-stack claim ceiling opened")
    evidence["deep_stack"] = {"producer_summary": producer, "validator_summary": deep_summary}

    # Old regression artifacts.
    qit = load_json(root / "system_v7/sims/qit_projection_battery_v0/results/qit_projection_battery_v0_envelope_results.json")
    require(qit.get("all_pass") is True and qit.get("classification") == "scratch_diagnostic", "QIT projection regression is not scratch green")
    require(qit.get("promotion_allowed") is False and qit.get("formal_admission_allowed") is False, "QIT projection ceiling opened")
    graph_paths = [
        root / "system_v4/probes/a2_state/sim_results/sim_integration_networkx_rustworkx_crosscheck_results.json",
        root / "system_v4/probes/a2_state/sim_results/sim_capability_xgi_isolated_results.json",
        root / "system_v4/probes/a2_state/sim_results/sim_capability_toponetx_isolated_results.json",
        root / "system_v4/probes/a2_state/sim_results/sim_capability_gudhi_isolated_results.json",
    ]
    graph_payloads = [load_json(path) for path in graph_paths]
    require(all(row.get("overall_pass") is True for row in graph_payloads), "graph/topology regression pack is red")
    require(all(row.get("classification") == "classical_baseline" for row in graph_payloads), "graph/topology classification drift")
    tensor = load_json(root / "system_v7/sims/v8_nonofficial_stress_campaign_20260715/results/gap_k_tensor_chain_v2.json")
    require(tensor.get("schema") == "codex-ratchet.gap-k-tensor-chain-result.v2" and tensor.get("all_pass") is True, "cross-tensor regression is red")
    require(tensor.get("check_summary") == {"failed": 0, "passed": 19, "total": 19}, "cross-tensor check count drift")
    require(tensor.get("promotion_allowed") is False and tensor.get("formal_admission_allowed") is False, "cross-tensor ceiling opened")
    dynamics = load_json(root / "system_v7/sims/v8_nonofficial_stress_campaign_20260715/results/basin_chain_d.json")
    require(dynamics.get("schema") == "codex-ratchet.basin-chain-d-result.v2" and dynamics.get("all_pass") is True, "cross-dynamics regression is red")
    require(dynamics.get("promotion_allowed") is False and dynamics.get("formal_admission_allowed") is False, "cross-dynamics ceiling opened")
    evidence["old_regressions"] = {"qit_projection": True, "graph_topology": 4, "cross_tensor_checks": 19, "cross_dynamics": True}

    # Fresh first-tooth G0-G9 replay deliberately stops before Lev G10.
    rung_dir = first_root / "system_v7/sims/tolerance_to_equivalence_ratchet_rung_v0/results"
    envelope = load_json(rung_dir / "controller_envelope.json")
    envelope_validation = load_json(rung_dir / "validation.json")
    mutations = load_json(rung_dir / "mutation_tests.json")
    g0_g9 = load_json(rung_dir / "g0_g9_report.json")
    require(envelope.get("all_pass") is True and all(envelope.get("checks", {}).values()), "first-tooth controller envelope is red")
    require(envelope_validation.get("ok") is True, "first-tooth independent envelope validator is red")
    require(mutations.get("all_pass") is True and mutations.get("case_count") == 5 and all(row.get("rejected") for row in mutations.get("cases", [])), "first-tooth mutation suite is red")
    require(g0_g9.get("candidate_pass") is True, "first-tooth G0-G9 candidate is red")
    require(g0_g9.get("final_decision") == "HOLD_PENDING_LEV" and g0_g9.get("ratchet_state") == "TOOTH_1_CANDIDATE", "first-tooth fresh decision must hold pending Lev")
    require(g0_g9.get("gates", {}).get("G10_deterministic_lev_replay") is False, "fresh campaign falsely reused G10")
    require(all(value is True for key, value in g0_g9.get("gates", {}).items() if key != "G10_deterministic_lev_replay"), "a first-tooth G0-G9 gate is red")
    require(g0_g9.get("promotion_allowed") is False and g0_g9.get("formal_admission_allowed") is False and g0_g9.get("llm_verdict_used") is False, "first-tooth claim or LLM fence opened")
    evidence["first_tooth"] = {"candidate_pass": True, "decision": "HOLD_PENDING_LEV", "mutation_rejections": 5}

    # Later-rung scratch: local mechanics may green while strict contract reds remain mandatory.
    l8_numpy = load_json(root / "system_v7/sims/manifold_L8_cut_lattice_gate2_b/results/manifold_L8_cut_lattice_gate2_b_numpy_results.json")
    l8_julia = load_json(root / "system_v7/sims/manifold_L8_cut_lattice_gate2_b/results/manifold_L8_cut_lattice_gate2_b_julia_results.json")
    l8_parity = load_json(root / "system_v7/sims/manifold_L8_cut_lattice_gate2_b/results/manifold_L8_cut_lattice_gate2_b_parity_results.json")
    require(l8_numpy.get("summary", {}).get("all_pass") is True and l8_julia.get("summary", {}).get("all_pass") is True, "L8 engine control suite is red")
    require(l8_numpy.get("summary", {}).get("controls_passed") == 8 and l8_julia.get("summary", {}).get("controls_passed") == 8, "L8 control count drift")
    require(l8_parity.get("all_pass") is True and l8_parity.get("failure_count") == 0 and l8_parity.get("numeric_fields_compared") == 720 and l8_parity.get("max_abs_delta") == 0.0, "L8 parity is red")
    require(l8_numpy.get("promotion_allowed") is False and l8_julia.get("promotion_allowed") is False, "L8 promotion fence opened")
    tower = load_json(root / "system_v7/sims/tower_g6g7_spinor_hopf_v0/results/tower_g6g7_spinor_hopf_v0_three_engine_results.json")
    tower_red = find_step(execution, "LATER_G6G7_SPINOR_HOPF", "strict_generic_validator")
    require(tower.get("all_pass") is True and tower.get("parity", {}).get("agreement_ok") is True, "tower local mechanical envelope is red")
    require(tower.get("promotion_allowed") is False and tower.get("formal_admission_allowed") is False, "tower promotion fence opened")
    require(tower_red.get("returncode") not in (None, 0), "tower strict contract red disappeared")
    require("reads_peer_result" in combined_log(tower_red) and "source-backed audit failed" in combined_log(tower_red), "tower red is not the preregistered contract failure")
    climb = load_json(root / "system_v7/sims/ratchet_climb_engine_v1_drive/results/ratchet_climb_engine_v1_drive_three_engine_results.json")
    climb_basic = find_step(execution, "LATER_RATCHET_DRIVE_V1", "basic_validator")
    climb_red = find_step(execution, "LATER_RATCHET_DRIVE_V1", "strict_validator")
    require(climb.get("all_pass") is True and climb.get("frontier_reached") == 6, "ratchet-drive local envelope is red")
    require(climb.get("capstone_status") == "DRAFT_UNAUDITED", "ratchet-drive capstone ceiling changed")
    require(climb.get("promotion_allowed") is False and climb.get("formal_admission_allowed") is False, "ratchet-drive promotion fence opened")
    require(climb_basic.get("returncode") == 0, "ratchet-drive basic validator is not green")
    require(climb_red.get("returncode") not in (None, 0), "ratchet-drive strict red disappeared")
    require("declared load-bearing packages not imported in source: z3, cvc5" in combined_log(climb_red), "ratchet-drive red is not the preregistered source-thin failure")
    evidence["later_scratch"] = {"l8_parity_fields": 720, "tower_local_green_strict_red": True, "climb_frontier": 6, "climb_basic_green_strict_red": True}

    # Lev core ProofBundle tests green; monitor-to-proof evidence integration remains red.
    lev_eval = find_step(execution, "LEV_PROOF_BOUNDARY", "eval_suite")
    lev_monitor = find_step(execution, "LEV_PROOF_BOUNDARY", "proof_monitor_suite")
    require(lev_eval.get("returncode") == 0, "Lev core eval/ProofBundle suite is red")
    require("175 passed" in combined_log(lev_eval), "Lev eval suite did not report 175 passed tests")
    require(lev_monitor.get("returncode") not in (None, 0), "Lev monitor-to-proof red disappeared")
    monitor_log = combined_log(lev_monitor)
    require("2 failed" in monitor_log and "monitor-heartbeat-evidence.test.ts" in monitor_log, "Lev red is not the preregistered two-test monitor evidence failure")
    evidence["lev"] = {"eval_tests_passed": 175, "monitor_tests_failed": 2, "admission_state": "HOLD"}

    return failures, evidence


def selftest(spec: dict[str, Any], prereg: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
    mutations: list[tuple[str, dict[str, Any]]] = []
    promoted = copy.deepcopy(execution)
    promoted["official_launch_allowed"] = True
    mutations.append(("open_official_launch_flag", promoted))
    flipped_exit = copy.deepcopy(execution)
    flipped_exit["cases"][0]["steps"][0]["returncode"] = 9
    mutations.append(("flip_expected_zero_exit", flipped_exit))
    missing_artifact = copy.deepcopy(execution)
    target = next(case for case in missing_artifact["cases"] if case.get("artifacts_after"))
    target["artifacts_after"][0]["exists"] = False
    mutations.append(("erase_required_artifact", missing_artifact))
    erased_block = copy.deepcopy(execution)
    erased_block["blocked_cases"] = []
    mutations.append(("erase_blocked_cases", erased_block))
    false_green = copy.deepcopy(execution)
    false_green["all_systems_green"] = True
    mutations.append(("claim_all_systems_green", false_green))
    records = []
    for name, payload in mutations:
        findings, _ = validate_payload(spec, prereg, payload, verify_live_files=False)
        records.append({"case": name, "rejected": bool(findings), "finding_count": len(findings)})
    return {"case_count": len(records), "all_rejected": all(row["rejected"] for row in records), "cases": records}


def main() -> int:
    spec = load_json(SPEC_PATH)
    prereg = load_json(PREREG_PATH)
    execution = load_json(EXECUTION_PATH)
    prereg_proc = subprocess.run(
        [sys.executable, str(HERE / "validate_preregistration.py")],
        cwd=HERE,
        text=True,
        capture_output=True,
        check=False,
    )
    failures, evidence = validate_payload(spec, prereg, execution, verify_live_files=True)
    if prereg_proc.returncode != 0:
        failures.append("preregistration validator is red")
    mutations = selftest(spec, prereg, execution)
    if not mutations["all_rejected"]:
        failures.append("campaign validator mutation self-test is red")

    case_states = {
        case["case_id"]: "EXPECTED_PATTERN_OBSERVED" if case.get("case_execution_pass") else "RED"
        for case in execution.get("cases", [])
    }
    rungs = [
        {"rung_id": "R0_FROZEN_BOUNDARY", "state": "BOUNDARY_FROZEN_NONOFFICIAL" if prereg_proc.returncode == 0 else "HOLD"},
        {"rung_id": "R1_RUNTIME_CARRIER", "state": "CANONICAL_GREEN_PORTABILITY_RED" if evidence.get("preflight") else "HOLD"},
        {"rung_id": "R2_FINITE_STACK", "state": "95_OF_95_TOOLS_AND_29_OF_29_EDGES_OPERATIONAL" if evidence.get("deep_stack") else "HOLD"},
        {"rung_id": "R3_OLD_SIM_REGRESSION", "state": "OLD_FINITE_CONTROLS_REPRODUCED" if evidence.get("old_regressions") else "HOLD"},
        {"rung_id": "R4_FIRST_TOOTH_CANDIDATE", "state": "TOOTH_1_CANDIDATE_HOLD_PENDING_LEV" if evidence.get("first_tooth") else "HOLD"},
        {"rung_id": "R5_LATER_RUNG_SCRATCH", "state": "MECHANICAL_GREENS_WITH_STRICT_REDS_PRESERVED" if evidence.get("later_scratch") else "HOLD"},
        {"rung_id": "R6_PROCESS_ADMISSION", "state": "HOLD_WHILE_MONITOR_TO_PROOF_CHAIN_IS_RED"},
    ]
    result = {
        "schema": "codex_ratchet.v8_nonofficial_stress_campaign.validation.v1",
        "campaign_id": spec["campaign_id"],
        "integrity_pass": not failures,
        "all_systems_green": False,
        "official_launch_allowed": False,
        "release_eligible": False,
        "scientific_claim_proven": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "llm_gate_used": False,
        "install_attempted": False,
        "claim_ceiling": spec["claim_ceiling"],
        "case_states": case_states,
        "rungs": rungs,
        "evidence": evidence,
        "preserved_reds": [
            "isolated worktree lacks the ignored Julia Manifest: 3 preflight failures",
            "tower G6/G7 strict source/peer-result contract gate",
            "ratchet drive v1 strict source-backed gate and DRAFT_UNAUDITED capstone",
            "Lev monitor-to-proof evidence integration: 2 failing tests",
        ],
        "blocked_cases": spec["blocked_cases"],
        "blocked_consumers": spec["blocked_consumers"],
        "validator_mutation_selftest": mutations,
        "failures": failures,
        "preregistration_validator_returncode": prereg_proc.returncode,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(OUT_PATH),
        "integrity_pass": result["integrity_pass"],
        "failure_count": len(failures),
        "all_systems_green": False,
        "official_launch_allowed": False,
    }, indent=2, sort_keys=True))
    return 0 if result["integrity_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
