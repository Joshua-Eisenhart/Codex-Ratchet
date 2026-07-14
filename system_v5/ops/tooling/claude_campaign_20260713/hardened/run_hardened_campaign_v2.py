#!/usr/bin/env python3
"""Execute and recompute the hardened Claude-campaign lanes.

This runner launches producers. It does not bless pre-existing child markers.
Execution completion, bounded tool-fit results, and promotion eligibility are
reported as separate fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
RESULTS = HERE / "results"
PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
CANONICAL_REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNTIME_DOCTOR = CANONICAL_REPO / "scripts" / "codex_runtime_env_doctor.py"
DEFAULT_OUTPUT = RESULTS / "hardened_campaign_v2_envelope.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lane_specs(archive: Path) -> list[dict[str, Any]]:
    return [
        {
            "id": "D",
            "name": "active-boundary basin chain",
            "source": HERE / "basin_chain_d.py",
            "result": RESULTS / "basin_chain_d_results.json",
            "command": [PYTHON, str(HERE / "basin_chain_d.py")],
            "environment": {"JAX_ENABLE_X64": "1"},
            "expected_schema": "codex-ratchet.basin-chain-d-result.v2",
            "expected_all_pass": True,
        },
        {
            "id": "F",
            "name": "archive-pinned structured optimal transport",
            "source": HERE / "gap_f_ott_structured_v2.py",
            "result": RESULTS / "gap_f_ott_structured_v2_results.json",
            "command": [PYTHON, str(HERE / "gap_f_ott_structured_v2.py"), "--archive", str(archive), "--output", str(RESULTS / "gap_f_ott_structured_v2_results.json")],
            "environment": {"JAX_ENABLE_X64": "1"},
            "expected_schema": "codex-ratchet.gap-f-structured-ot-result.v2",
            "expected_all_pass": True,
        },
        {
            "id": "J",
            "name": "auto_LiRPA exhaustive activation-region audit",
            "source": HERE / "gap_j_autolirpa_region_oracle_v2.py",
            "result": RESULTS / "gap_j_autolirpa_region_oracle_v2_results.json",
            "command": [PYTHON, str(HERE / "gap_j_autolirpa_region_oracle_v2.py"), "--output", str(RESULTS / "gap_j_autolirpa_region_oracle_v2_results.json")],
            "environment": {},
            "expected_schema": "codex-ratchet.gap-j-autolirpa-region-oracle-result.v2",
            "expected_all_pass": True,
        },
        {
            "id": "K",
            "name": "nontrivial quimb and ITensors tensor chain",
            "source": HERE / "gap_k_tensor_chain_v2.py",
            "result": RESULTS / "gap_k_tensor_chain_v2_results.json",
            "command": [PYTHON, str(HERE / "gap_k_tensor_chain_v2.py"), "--output", str(RESULTS / "gap_k_tensor_chain_v2_results.json")],
            "environment": {"NUMBA_CACHE_DIR": "/private/tmp/codex_numba_cache"},
            "expected_schema": "codex-ratchet.gap-k-tensor-chain-result.v2",
            "expected_all_pass": True,
        },
        {
            "id": "H",
            "name": "variation-cycle contract semantics",
            "source": HERE / "lineage_semantics_audit_v2.py",
            "result": RESULTS / "lineage_semantics_audit_v2_results.json",
            "command": [PYTHON, str(HERE / "lineage_semantics_audit_v2.py"), "--archive", str(archive), "--output", str(RESULTS / "lineage_semantics_audit_v2_results.json")],
            "environment": {},
            "expected_schema": "codex-ratchet.lineage-semantics-audit-result.v2",
            "expected_all_pass": False,
            "expected_audit_completed": True,
        },
    ]


def run_runtime_doctor() -> dict[str, Any]:
    command = [PYTHON, str(RUNTIME_DOCTOR), "--json"]
    completed = subprocess.run(
        command,
        cwd=CANONICAL_REPO,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    report: dict[str, Any] = {}
    parse_error = ""
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        parse_error = str(error)
    gates = {
        "doctor_exit_zero": completed.returncode == 0,
        "doctor_json_parses": not parse_error,
        "doctor_schema_matches": report.get("schema") == "codex_runtime_env_doctor.v1",
        "doctor_summary_ok": report.get("summary", {}).get("ok") is True,
        "install_state_stable": report.get("summary", {}).get("install_state") == "stable_observed",
        "no_active_installers": report.get("active_installers", {}).get("ok") is True and report.get("active_installers", {}).get("matches") == [],
        "no_repo_pollution": report.get("repo_pollution") == [],
        "canonical_python_matches": report.get("python", {}).get("path") == PYTHON,
        "canonical_julia_project_matches": report.get("julia", {}).get("active_project") == "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml",
    }
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stderr": completed.stderr.splitlines(),
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "source_path": str(RUNTIME_DOCTOR.resolve()),
        "source_sha256": sha256_file(RUNTIME_DOCTOR),
        "parse_error": parse_error,
        "gates": gates,
        "all_gates_pass": all(gates.values()),
        "report": report,
    }


def run_lane(spec: dict[str, Any]) -> dict[str, Any]:
    before_mtime = spec["result"].stat().st_mtime_ns if spec["result"].exists() else None
    environment = dict(os.environ)
    environment.update(spec["environment"])
    started_at = utc_now()
    started = time.perf_counter()
    completed = subprocess.run(
        spec["command"],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
    )
    duration = time.perf_counter() - started
    finished_at = utc_now()
    result_exists = spec["result"].is_file()
    after_mtime = spec["result"].stat().st_mtime_ns if result_exists else None
    receipt: dict[str, Any] = {}
    parse_error = ""
    if result_exists:
        try:
            receipt = json.loads(spec["result"].read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            parse_error = str(error)

    required_fields = (
        "schema",
        "sim_id",
        "command",
        "runner_identity",
        "classification",
        "promotion_allowed",
        "source",
        "tool_calls",
        "claim_ceiling",
        "all_pass",
    )
    missing_fields = [field for field in required_fields if field not in receipt]
    expected_claim = receipt.get("all_pass") is spec["expected_all_pass"]
    audit_completed = receipt.get("audit_completed") is True if spec.get("expected_audit_completed") else True
    source_path = spec["source"].resolve()
    gates = {
        "process_exit_zero": completed.returncode == 0,
        "result_exists_and_parses": result_exists and not parse_error,
        "result_was_rewritten_by_this_run": after_mtime is not None and after_mtime != before_mtime,
        "schema_matches": receipt.get("schema") == spec["expected_schema"],
        "required_receipt_fields_present": not missing_fields,
        "promotion_is_blocked": receipt.get("promotion_allowed") is False,
        "tool_calls_are_nonempty": isinstance(receipt.get("tool_calls"), list) and len(receipt.get("tool_calls", [])) > 0,
        "claim_ceiling_is_nonempty": isinstance(receipt.get("claim_ceiling"), str) and bool(receipt.get("claim_ceiling")),
        "source_file_hash_recomputed": source_path.is_file() and sha256_file(source_path) in json.dumps(receipt.get("source", {}), sort_keys=True),
        "claim_polarity_matches_lane_contract": expected_claim,
        "audit_completion_matches_lane_contract": audit_completed,
    }
    execution_ok = all(gates.values())
    return {
        "id": spec["id"],
        "name": spec["name"],
        "command": spec["command"],
        "environment_overrides": spec["environment"],
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.splitlines(),
        "stderr": completed.stderr.splitlines(),
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        "producer_source_path": str(source_path),
        "producer_source_sha256": sha256_file(source_path),
        "result_path": str(spec["result"].resolve()),
        "result_sha256": sha256_file(spec["result"]) if result_exists else None,
        "receipt_schema": receipt.get("schema"),
        "receipt_all_pass": receipt.get("all_pass"),
        "receipt_audit_completed": receipt.get("audit_completed"),
        "receipt_claim_ceiling": receipt.get("claim_ceiling"),
        "missing_required_fields": missing_fields,
        "parse_error": parse_error,
        "gates": gates,
        "execution_and_receipt_ok": execution_ok,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if Path(sys.executable).resolve() != Path(PYTHON).resolve():
        raise RuntimeError(f"wrong Python runtime: {sys.executable}")
    archive = args.archive.resolve()
    if not archive.is_file():
        raise FileNotFoundError(archive)

    RESULTS.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    started = time.perf_counter()
    runtime_doctor = run_runtime_doctor()
    lanes = [run_lane(spec) for spec in lane_specs(archive)]
    finished_at = utc_now()
    by_id = {lane["id"]: lane for lane in lanes}
    runner_all_completed = runtime_doctor["all_gates_pass"] and all(lane["execution_and_receipt_ok"] for lane in lanes)
    capability_fit_all_pass = all(by_id[lane]["receipt_all_pass"] is True for lane in ("D", "F", "J", "K"))
    semantic_blockers = [
        {
            "lane": "H",
            "reason": "cycle observed, but native mutation-lineage integrity accepts it and no ancestry-DAG rule was found",
        }
    ]
    promotion_eligible = False
    all_pass = False
    source_path = Path(__file__).resolve()
    output = args.output.resolve()
    command = [PYTHON, str(source_path), "--archive", str(archive), "--output", str(output)]
    envelope = {
        "schema": "codex-ratchet.hardened-claude-campaign-envelope.v2",
        "campaign_id": "claude_campaign_20260713_hardened_v2",
        "created_at": finished_at,
        "command": command,
        "runner_identity": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "cwd": str(REPO_ROOT),
            "runner_started_at": started_at,
            "runner_finished_at": finished_at,
            "duration_seconds": time.perf_counter() - started,
        },
        "source": {
            "runner_path": str(source_path),
            "runner_sha256": sha256_file(source_path),
            "packet_archive_path": str(archive),
            "packet_archive_sha256": sha256_file(archive),
        },
        "classification": "integration_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "truth_state": "host_recomputed_blocked",
        "runner_all_completed": runner_all_completed,
        "capability_fit_all_pass": capability_fit_all_pass,
        "promotion_eligible": promotion_eligible,
        "all_pass": all_pass,
        "summary": {
            "lanes_executed": len(lanes),
            "lane_receipt_true": sum(lane["receipt_all_pass"] is True for lane in lanes),
            "lane_receipt_false": sum(lane["receipt_all_pass"] is False for lane in lanes),
            "runner_failures": [lane["id"] for lane in lanes if not lane["execution_and_receipt_ok"]],
            "bounded_green_lanes": [lane for lane in ("D", "F", "J", "K") if by_id[lane]["receipt_all_pass"] is True],
            "semantic_blockers": semantic_blockers,
        },
        "runtime_doctor": runtime_doctor,
        "lanes": lanes,
        "tool_calls": [
            {
                "tool": "campaign subprocess orchestrator",
                "api": "subprocess.run per producer with captured exit/stdout/stderr",
                "input": "five source-backed bounded producers and the pinned packet archive",
                "output": "fresh child receipts plus recomputed hashes",
                "negative_control": "H remains false and blocks promotion rather than being tallied as green",
                "gates": ["runner_all_completed", "promotion_eligible", "all_pass"],
            }
        ],
        "claim_ceiling": (
            "Fresh host recomputation of four bounded tool-fit lanes and one lineage-semantics audit. "
            "The campaign is not a composed scientific Ratchet, does not establish a living basin or MSS, "
            "does not admit packet integrity failure H, and is not eligible for canon or graph mutation."
        ),
        "blocked_consumers": [
            "scientific canon",
            "Ratchet rung or manifold admission",
            "living-basin or MSS claim",
            "packet integrity-defect escalation for H",
            "Lev graph or ontology mutation",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "runner_all_completed": runner_all_completed,
        "capability_fit_all_pass": capability_fit_all_pass,
        "promotion_eligible": promotion_eligible,
        "all_pass": all_pass,
        "receipt": str(output),
        "receipt_sha256": sha256_file(output),
    }, sort_keys=True))
    return 0 if runner_all_completed and capability_fit_all_pass and not promotion_eligible and not all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
