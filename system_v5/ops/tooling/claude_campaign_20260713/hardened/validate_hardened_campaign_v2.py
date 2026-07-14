#!/usr/bin/env python3
"""Fail-closed validator for the hardened campaign v2 envelope.

This validates the identities and contents of the expected campaign artifacts,
not arbitrary self-reported path/hash pairs. A valid stored envelope is still a
record of an execution; live freshness requires running the campaign command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
RESULTS = HERE / "results"
PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
CANONICAL_REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNTIME_DOCTOR = CANONICAL_REPO / "scripts" / "codex_runtime_env_doctor.py"
ARCHIVE = Path("/Users/joshuaeisenhart/Desktop/166_reconciled_ratchet_v0_11_7_cold_verified (1).zip")
ARCHIVE_SHA256 = "42fc2629e076b4cd5b8015514fb1c9027aa7c751702ebc7a719a6b808141b9da"
RUNNER = HERE / "run_hardened_campaign_v2.py"
ENVELOPE = RESULTS / "hardened_campaign_v2_envelope.json"
EXPECTED_SCHEMA = "codex-ratchet.hardened-claude-campaign-envelope.v2"

EXPECTED_CLAIM_CEILING = (
    "Fresh host recomputation of four bounded tool-fit lanes and one lineage-semantics audit. "
    "The campaign is not a composed scientific Ratchet, does not establish a living basin or MSS, "
    "does not admit packet integrity failure H, and is not eligible for canon or graph mutation."
)
EXPECTED_BLOCKED_CONSUMERS = [
    "scientific canon",
    "Ratchet rung or manifold admission",
    "living-basin or MSS claim",
    "packet integrity-defect escalation for H",
    "Lev graph or ontology mutation",
]
EXPECTED_SEMANTIC_BLOCKERS = [
    {
        "lane": "H",
        "reason": "cycle observed, but native mutation-lineage integrity accepts it and no ancestry-DAG rule was found",
    }
]

TOP_KEYS = {
    "all_pass", "blocked_consumers", "campaign_id", "capability_fit_all_pass",
    "claim_ceiling", "classification", "command", "created_at",
    "formal_admission_allowed", "lanes", "promotion_allowed",
    "promotion_eligible", "runner_all_completed", "runner_identity",
    "runtime_doctor", "schema", "source", "summary", "tool_calls", "truth_state",
}
RUNNER_IDENTITY_KEYS = {
    "cwd", "duration_seconds", "platform", "python_executable", "python_version",
    "runner_finished_at", "runner_started_at",
}
SOURCE_KEYS = {"packet_archive_path", "packet_archive_sha256", "runner_path", "runner_sha256"}
SUMMARY_KEYS = {
    "bounded_green_lanes", "lane_receipt_false", "lane_receipt_true",
    "lanes_executed", "runner_failures", "semantic_blockers",
}
LANE_KEYS = {
    "command", "duration_seconds", "environment_overrides", "execution_and_receipt_ok",
    "exit_code", "finished_at", "gates", "id", "missing_required_fields", "name",
    "parse_error", "producer_source_path", "producer_source_sha256", "receipt_all_pass",
    "receipt_audit_completed", "receipt_claim_ceiling", "receipt_schema", "result_path",
    "result_sha256", "started_at", "stderr", "stderr_sha256", "stdout", "stdout_sha256",
}
LANE_GATE_KEYS = {
    "audit_completion_matches_lane_contract", "claim_ceiling_is_nonempty",
    "claim_polarity_matches_lane_contract", "process_exit_zero", "promotion_is_blocked",
    "required_receipt_fields_present", "result_exists_and_parses",
    "result_was_rewritten_by_this_run", "schema_matches", "source_file_hash_recomputed",
    "tool_calls_are_nonempty",
}
RUNTIME_KEYS = {
    "all_gates_pass", "command", "exit_code", "gates", "parse_error", "report",
    "source_path", "source_sha256", "stderr", "stdout_sha256",
}
RUNTIME_GATE_KEYS = {
    "canonical_julia_project_matches", "canonical_python_matches", "doctor_exit_zero",
    "doctor_json_parses", "doctor_schema_matches", "doctor_summary_ok",
    "install_state_stable", "no_active_installers", "no_repo_pollution",
}
TOOL_CALL_KEYS = {"api", "gates", "input", "negative_control", "output", "tool"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def same_path(value: Any, expected: Path) -> bool:
    try:
        return Path(str(value)).resolve() == expected.resolve()
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def parse_time(value: Any, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{label} must be an ISO timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} must be an ISO timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{label} must include a timezone")
        return None
    return parsed


def require_exact_keys(value: Any, expected: set[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    actual = set(value)
    if actual != expected:
        errors.append(
            f"{label} keys mismatch: missing={sorted(expected - actual)} unknown={sorted(actual - expected)}"
        )
        return False
    return True


def hash_lines(value: Any) -> str | None:
    if not isinstance(value, list) or not all(isinstance(row, str) for row in value):
        return None
    text = "\n".join(value)
    if value:
        text += "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def lane_specs() -> dict[str, dict[str, Any]]:
    claims = {
        "D": "tool-lego fit evidence for one supplied active-boundary basin and its controls; cross-engine agreement is diagnostic, Z3 is active-branch-only, and no lego, scientific basin, manifold, bridge, axis, or formal admission is promoted",
        "F": "Archive-pinned function-level evidence that OTT agrees with a finite SciPy LP oracle under one nontrivial structured ground metric on two named packet profile pairs. This does not admit the packet, a scientific transport law, QIT, a manifold, or a Ratchet rung.",
        "J": "Finite numerical containment evidence for CROWN and IBP on one pinned, fixed-seed 2-4-1 ReLU network and three nested boxes, checked by exhaustive activation-region LP. This is not a general auto_LiRPA soundness proof and admits no scientific Ratchet claim.",
        "K": "Fixed-fixture function-level tensor-tool fit diagnostic only. This result does not prove general quimb/ITensors equivalence, numerical soundness for arbitrary states, Julia Canon admission, tensor-network science, ratchet dynamics, cosmogenesis, a bridge, an Axis, a basin, a manifold, or any physics claim.",
        "H": "Packet-local observation that the variation transition graph contains a cycle while the packet's native integrity verifier accepts it. No ledger defect is admitted without an authoritative ancestry-DAG rule.",
    }
    rows: dict[str, dict[str, Any]] = {
        "D": {
            "name": "active-boundary basin chain",
            "source": HERE / "basin_chain_d.py",
            "result": RESULTS / "basin_chain_d_results.json",
            "environment": {"JAX_ENABLE_X64": "1"},
            "schema": "codex-ratchet.basin-chain-d-result.v2",
            "all_pass": True,
            "audit_completed": None,
            "classification": "tool_lego_fit_probe",
        },
        "F": {
            "name": "archive-pinned structured optimal transport",
            "source": HERE / "gap_f_ott_structured_v2.py",
            "result": RESULTS / "gap_f_ott_structured_v2_results.json",
            "environment": {"JAX_ENABLE_X64": "1"},
            "schema": "codex-ratchet.gap-f-structured-ot-result.v2",
            "all_pass": True,
            "audit_completed": None,
            "classification": "tool_lego_fit_probe",
        },
        "J": {
            "name": "auto_LiRPA exhaustive activation-region audit",
            "source": HERE / "gap_j_autolirpa_region_oracle_v2.py",
            "result": RESULTS / "gap_j_autolirpa_region_oracle_v2_results.json",
            "environment": {},
            "schema": "codex-ratchet.gap-j-autolirpa-region-oracle-result.v2",
            "all_pass": True,
            "audit_completed": None,
            "classification": "tool_lego_fit_probe",
        },
        "K": {
            "name": "nontrivial quimb and ITensors tensor chain",
            "source": HERE / "gap_k_tensor_chain_v2.py",
            "result": RESULTS / "gap_k_tensor_chain_v2_results.json",
            "environment": {"NUMBA_CACHE_DIR": "/private/tmp/codex_numba_cache"},
            "schema": "codex-ratchet.gap-k-tensor-chain-result.v2",
            "all_pass": True,
            "audit_completed": None,
            "classification": "tool_lego_fit_probe",
        },
        "H": {
            "name": "variation-cycle contract semantics",
            "source": HERE / "lineage_semantics_audit_v2.py",
            "result": RESULTS / "lineage_semantics_audit_v2_results.json",
            "environment": {},
            "schema": "codex-ratchet.lineage-semantics-audit-result.v2",
            "all_pass": False,
            "audit_completed": True,
            "classification": "contract_semantics_audit",
        },
    }
    for lane_id, spec in rows.items():
        command = [str(PYTHON), str(spec["source"])]
        if lane_id in {"F", "H"}:
            command.extend(["--archive", str(ARCHIVE), "--output", str(spec["result"])])
        elif lane_id in {"J", "K"}:
            command.extend(["--output", str(spec["result"])])
        spec["command"] = command
        spec["receipt_command"] = command if lane_id != "D" else ["env", "JAX_ENABLE_X64=1", *command]
        spec["claim_ceiling"] = claims[lane_id]
    return rows


def validate_child_receipt(
    lane_id: str,
    lane: dict[str, Any],
    spec: dict[str, Any],
    lane_start: datetime | None,
    lane_finish: datetime | None,
    errors: list[str],
) -> None:
    result_path = spec["result"]
    if not result_path.is_file():
        errors.append(f"lane {lane_id} expected result is missing")
        return
    try:
        receipt = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError) as error:
        errors.append(f"lane {lane_id} result parse failure: {error}")
        return

    if receipt.get("schema") != spec["schema"]:
        errors.append(f"lane {lane_id} child schema mismatch")
    if receipt.get("all_pass") is not spec["all_pass"]:
        errors.append(f"lane {lane_id} child all_pass mismatch")
    if receipt.get("audit_completed") is not spec["audit_completed"]:
        errors.append(f"lane {lane_id} child audit_completed mismatch")
    if receipt.get("classification") != spec["classification"]:
        errors.append(f"lane {lane_id} child classification mismatch")
    if receipt.get("promotion_allowed") is not False or receipt.get("formal_admission_allowed") is not False:
        errors.append(f"lane {lane_id} child promotion/admission must remain blocked")
    if receipt.get("claim_ceiling") != spec["claim_ceiling"]:
        errors.append(f"lane {lane_id} child claim ceiling mismatch")
    if receipt.get("command") != spec["receipt_command"]:
        errors.append(f"lane {lane_id} child command mismatch")
    if not isinstance(receipt.get("runner_identity"), dict) or not receipt["runner_identity"]:
        errors.append(f"lane {lane_id} child runner identity missing")
    if not isinstance(receipt.get("tool_calls"), list) or not receipt["tool_calls"]:
        errors.append(f"lane {lane_id} child tool calls missing")
    if not isinstance(receipt.get("blocked_consumers"), list) or not receipt["blocked_consumers"]:
        errors.append(f"lane {lane_id} child blocked consumers missing")

    source_text = json.dumps(receipt.get("source"), sort_keys=True)
    expected_source = str(spec["source"].resolve())
    expected_hash = sha256_file(spec["source"])
    if expected_source not in source_text or expected_hash not in source_text:
        errors.append(f"lane {lane_id} child source identity mismatch")
    if lane_id in {"F", "H"} and (str(ARCHIVE) not in source_text or ARCHIVE_SHA256 not in source_text):
        errors.append(f"lane {lane_id} child archive identity mismatch")

    created = parse_time(receipt.get("created_at"), f"lane {lane_id} child created_at", errors)
    if created and lane_start and lane_finish and not (lane_start <= created <= lane_finish):
        errors.append(f"lane {lane_id} child timestamp is outside its execution interval")

    if lane_id == "D":
        per_leg = receipt.get("per_leg")
        if not isinstance(per_leg, dict) or not per_leg or not all(value == "PASS" for value in per_leg.values()):
            errors.append("lane D child per-leg verdicts are not all PASS")
        if receipt.get("divergence", {}).get("julia_authoritative") is not True:
            errors.append("lane D Julia authority marker missing")
    elif lane_id in {"F", "J"}:
        checks = receipt.get("checks")
        if not isinstance(checks, dict) or not checks or not all(value is True for value in checks.values()):
            errors.append(f"lane {lane_id} child checks are not all true")
    elif lane_id == "K":
        checks = receipt.get("checks")
        if not isinstance(checks, dict) or not checks or not all(
            isinstance(value, dict) and value.get("pass") is True for value in checks.values()
        ):
            errors.append("lane K child checks are not all passing")
        if receipt.get("check_summary") != {"failed": 0, "passed": 19, "total": 19}:
            errors.append("lane K child check summary mismatch")
    elif lane_id == "H":
        audit_checks = receipt.get("audit_checks")
        if not isinstance(audit_checks, dict) or not audit_checks or not all(value is True for value in audit_checks.values()):
            errors.append("lane H audit checks are not all true")
        verdict = receipt.get("semantic_verdict", {})
        expected = {
            "append_only_ancestry_contract_found": False,
            "cycle_observed": True,
            "integrity_defect_admitted": False,
            "native_integrity_pass": True,
            "required_decision": "Either retain mutation-transition semantics with cycles allowed, or explicitly add ancestry-DAG semantics to the authoritative contract and native verifier tests.",
            "status": "cycle_observed_but_native_contract_does_not_forbid_it",
        }
        if verdict != expected or receipt.get("ancestry_dag_claim_pass") is not False:
            errors.append("lane H semantic verdict mismatch")


def validate(raw: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require_exact_keys(raw, TOP_KEYS, "envelope", errors)

    if raw.get("schema") != EXPECTED_SCHEMA:
        errors.append("schema mismatch")
    if raw.get("campaign_id") != "claude_campaign_20260713_hardened_v2":
        errors.append("campaign id mismatch")
    if raw.get("classification") != "integration_diagnostic":
        errors.append("classification must remain integration_diagnostic")
    if raw.get("promotion_allowed") is not False or raw.get("promotion_eligible") is not False:
        errors.append("promotion must remain blocked")
    if raw.get("formal_admission_allowed") is not False:
        errors.append("formal admission must remain blocked")
    if raw.get("runner_all_completed") is not True:
        errors.append("runner_all_completed must be true")
    if raw.get("capability_fit_all_pass") is not True:
        errors.append("bounded capability lanes must pass")
    if raw.get("all_pass") is not False:
        errors.append("campaign all_pass must remain false")
    if raw.get("truth_state") != "host_recomputed_blocked":
        errors.append("truth_state must remain host_recomputed_blocked")
    if raw.get("claim_ceiling") != EXPECTED_CLAIM_CEILING:
        errors.append("campaign claim ceiling mismatch")
    if raw.get("blocked_consumers") != EXPECTED_BLOCKED_CONSUMERS:
        errors.append("campaign blocked consumers mismatch")

    expected_top_command = [
        str(PYTHON), str(RUNNER), "--archive", str(ARCHIVE), "--output", str(ENVELOPE)
    ]
    if raw.get("command") != expected_top_command:
        errors.append("campaign command mismatch")

    source = raw.get("source")
    if require_exact_keys(source, SOURCE_KEYS, "source", errors):
        if not same_path(source.get("runner_path"), RUNNER):
            errors.append("runner path identity mismatch")
        elif source.get("runner_sha256") != sha256_file(RUNNER):
            errors.append("runner source hash mismatch")
        if not same_path(source.get("packet_archive_path"), ARCHIVE):
            errors.append("packet archive path identity mismatch")
        elif not ARCHIVE.is_file() or source.get("packet_archive_sha256") != ARCHIVE_SHA256 or sha256_file(ARCHIVE) != ARCHIVE_SHA256:
            errors.append("packet archive hash mismatch")

    runner = raw.get("runner_identity")
    runner_start = runner_finish = None
    if require_exact_keys(runner, RUNNER_IDENTITY_KEYS, "runner_identity", errors):
        if not same_path(runner.get("python_executable"), PYTHON):
            errors.append("runner Python identity mismatch")
        if runner.get("cwd") != str(REPO_ROOT):
            errors.append("runner cwd mismatch")
        if not isinstance(runner.get("python_version"), str) or not runner["python_version"]:
            errors.append("runner Python version missing")
        if not isinstance(runner.get("platform"), str) or not runner["platform"]:
            errors.append("runner platform missing")
        if not isinstance(runner.get("duration_seconds"), (int, float)) or runner["duration_seconds"] < 0:
            errors.append("runner duration invalid")
        runner_start = parse_time(runner.get("runner_started_at"), "runner_started_at", errors)
        runner_finish = parse_time(runner.get("runner_finished_at"), "runner_finished_at", errors)
        if runner_start and runner_finish and runner_start > runner_finish:
            errors.append("runner timestamp order invalid")
    created = parse_time(raw.get("created_at"), "created_at", errors)
    if created and runner_finish and created != runner_finish:
        errors.append("created_at must equal runner_finished_at")

    runtime = raw.get("runtime_doctor")
    if require_exact_keys(runtime, RUNTIME_KEYS, "runtime_doctor", errors):
        expected_command = [str(PYTHON), str(RUNTIME_DOCTOR), "--json"]
        if runtime.get("command") != expected_command or runtime.get("exit_code") != 0:
            errors.append("runtime doctor command/exit mismatch")
        if runtime.get("parse_error") != "" or runtime.get("all_gates_pass") is not True:
            errors.append("runtime doctor parse/gate mismatch")
        if not same_path(runtime.get("source_path"), RUNTIME_DOCTOR):
            errors.append("runtime doctor source identity mismatch")
        elif runtime.get("source_sha256") != sha256_file(RUNTIME_DOCTOR):
            errors.append("runtime doctor source hash mismatch")
        gates = runtime.get("gates")
        if not require_exact_keys(gates, RUNTIME_GATE_KEYS, "runtime_doctor.gates", errors) or not all(value is True for value in gates.values()):
            errors.append("runtime doctor gates must be exactly the known green gates")
        report = runtime.get("report")
        if not isinstance(report, dict):
            errors.append("runtime doctor report missing")
        else:
            if report.get("schema") != "codex_runtime_env_doctor.v1":
                errors.append("runtime doctor report schema mismatch")
            if report.get("summary", {}).get("ok") is not True or report.get("summary", {}).get("install_state") != "stable_observed":
                errors.append("runtime doctor report summary mismatch")
            if report.get("active_installers", {}).get("ok") is not True or report.get("active_installers", {}).get("matches") != []:
                errors.append("runtime doctor active installers mismatch")
            if report.get("repo_pollution") != []:
                errors.append("runtime doctor repo pollution is not empty")
            if report.get("python", {}).get("path") != str(PYTHON):
                errors.append("runtime doctor canonical Python mismatch")
            if report.get("julia", {}).get("active_project") != "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml":
                errors.append("runtime doctor Julia project mismatch")

    specs = lane_specs()
    lanes = raw.get("lanes")
    if not isinstance(lanes, list) or len(lanes) != len(specs):
        return [*errors, "lanes must be an exact five-row array"]
    by_id = {lane.get("id"): lane for lane in lanes if isinstance(lane, dict)}
    if set(by_id) != set(specs):
        return [*errors, "lane ids must be exactly D,F,J,K,H"]

    for lane_id, spec in specs.items():
        lane = by_id[lane_id]
        require_exact_keys(lane, LANE_KEYS, f"lane {lane_id}", errors)
        if lane.get("name") != spec["name"]:
            errors.append(f"lane {lane_id} name mismatch")
        if lane.get("command") != spec["command"]:
            errors.append(f"lane {lane_id} command mismatch")
        if lane.get("environment_overrides") != spec["environment"]:
            errors.append(f"lane {lane_id} environment mismatch")
        if lane.get("exit_code") != 0 or lane.get("execution_and_receipt_ok") is not True:
            errors.append(f"lane {lane_id} execution/receipt gates are not green")
        if lane.get("missing_required_fields") != [] or lane.get("parse_error") != "":
            errors.append(f"lane {lane_id} parse/provenance fields are not clean")
        gates = lane.get("gates")
        if not require_exact_keys(gates, LANE_GATE_KEYS, f"lane {lane_id}.gates", errors) or not all(value is True for value in gates.values()):
            errors.append(f"lane {lane_id} gates must be exactly the known green gates")
        if not same_path(lane.get("producer_source_path"), spec["source"]):
            errors.append(f"lane {lane_id} producer source identity mismatch")
        elif lane.get("producer_source_sha256") != sha256_file(spec["source"]):
            errors.append(f"lane {lane_id} producer source hash mismatch")
        if not same_path(lane.get("result_path"), spec["result"]):
            errors.append(f"lane {lane_id} result identity mismatch")
        elif not spec["result"].is_file() or lane.get("result_sha256") != sha256_file(spec["result"]):
            errors.append(f"lane {lane_id} result hash mismatch")
        if lane.get("receipt_schema") != spec["schema"]:
            errors.append(f"lane {lane_id} receipt schema mismatch")
        if lane.get("receipt_all_pass") is not spec["all_pass"]:
            errors.append(f"lane {lane_id} receipt polarity mismatch")
        if lane.get("receipt_audit_completed") is not spec["audit_completed"]:
            errors.append(f"lane {lane_id} audit-completion mismatch")
        if lane.get("receipt_claim_ceiling") != spec["claim_ceiling"]:
            errors.append(f"lane {lane_id} receipt claim ceiling mismatch")
        if hash_lines(lane.get("stdout")) != lane.get("stdout_sha256"):
            errors.append(f"lane {lane_id} stdout hash mismatch")
        if hash_lines(lane.get("stderr")) != lane.get("stderr_sha256"):
            errors.append(f"lane {lane_id} stderr hash mismatch")
        lane_start = parse_time(lane.get("started_at"), f"lane {lane_id} started_at", errors)
        lane_finish = parse_time(lane.get("finished_at"), f"lane {lane_id} finished_at", errors)
        if lane_start and lane_finish and lane_start > lane_finish:
            errors.append(f"lane {lane_id} timestamp order invalid")
        if runner_start and lane_start and lane_start < runner_start:
            errors.append(f"lane {lane_id} starts before runner")
        if runner_finish and lane_finish and lane_finish > runner_finish:
            errors.append(f"lane {lane_id} finishes after runner")
        if not isinstance(lane.get("duration_seconds"), (int, float)) or lane["duration_seconds"] < 0:
            errors.append(f"lane {lane_id} duration invalid")
        validate_child_receipt(lane_id, lane, spec, lane_start, lane_finish, errors)

    summary = raw.get("summary")
    expected_summary = {
        "lanes_executed": 5,
        "lane_receipt_true": 4,
        "lane_receipt_false": 1,
        "runner_failures": [],
        "bounded_green_lanes": ["D", "F", "J", "K"],
        "semantic_blockers": EXPECTED_SEMANTIC_BLOCKERS,
    }
    if not require_exact_keys(summary, SUMMARY_KEYS, "summary", errors) or summary != expected_summary:
        errors.append("campaign summary mismatch")

    tool_calls = raw.get("tool_calls")
    expected_tool_calls = [
        {
            "tool": "campaign subprocess orchestrator",
            "api": "subprocess.run per producer with captured exit/stdout/stderr",
            "input": "five source-backed bounded producers and the pinned packet archive",
            "output": "fresh child receipts plus recomputed hashes",
            "negative_control": "H remains false and blocks promotion rather than being tallied as green",
            "gates": ["runner_all_completed", "promotion_eligible", "all_pass"],
        }
    ]
    if not isinstance(tool_calls, list) or tool_calls != expected_tool_calls:
        errors.append("campaign tool-call contract mismatch")
    elif not require_exact_keys(tool_calls[0], TOOL_CALL_KEYS, "tool_calls[0]", errors):
        errors.append("campaign tool-call keys mismatch")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelope", type=Path)
    args = parser.parse_args()
    try:
        raw = json.loads(args.envelope.read_text(encoding="utf-8"))
        errors = validate(raw)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        errors = [f"parse failure: {error}"]
    print(json.dumps({"ok": not errors, "errors": errors, "envelope": str(args.envelope.resolve())}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
