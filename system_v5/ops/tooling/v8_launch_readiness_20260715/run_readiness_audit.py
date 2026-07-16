#!/usr/bin/env python3
"""Build a code-only V8 launch-readiness HOLD receipt.

This controller reads and independently exercises local deterministic artifacts.
It never calls an LLM provider, never installs packages, and never treats a
provider or model output as gate evidence.  A successful audit means that the
expected fail-closed state was observed; it does not mean launch is ready.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parents[3]
DEFAULT_OUT = HERE / "results/readiness_receipt.json"

SCHEMA = "codex_ratchet.v8_launch_readiness.receipt.v1"
CLASSIFICATION = "controller_audit"
AUDIT_KIND = "v8_launch_readiness"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Hashes local evidence, invokes deterministic validators, and binds git state."
    },
    "git": {
        "used": True,
        "reason": "Binds the supplied Lev repair path to the exact expected commit and clean worktree."
    },
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive", "git": "supportive"}

EXPECTED_HOLD_REASONS = [
    "V0_SEMANTIC_FORCING_FAILED",
    "V1_BUILDERS_ABSENT",
    "FROZEN_CAMPAIGN_RED_NONOFFICIAL",
    "NVIDIA_QUOTA_UNKNOWN",
    "XAI_QUOTA_UNKNOWN",
    "CLAUDE_BRIDGE_ADVISORY_ONLY",
    "LEV_REPAIR_SOURCE_BOUND_NOT_PROCESS_ADMISSION",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact is not an object: {path}")
    return value


def binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def run_step(
    step_id: str,
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_seconds,
        )
        return {
            "step_id": step_id,
            "command": list(command),
            "cwd": str(cwd.resolve()),
            "returncode": completed.returncode,
            "timed_out": False,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "stdout_sha256": sha256_text(completed.stdout),
            "stderr_sha256": sha256_text(completed.stderr),
        }
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return {
            "step_id": step_id,
            "command": list(command),
            "cwd": str(cwd.resolve()),
            "returncode": 124,
            "timed_out": True,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_sha256": sha256_text(stdout),
            "stderr_sha256": sha256_text(stderr),
        }


def parse_json_stdout(step: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(step.get("stdout", ""))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def is_closed(payload: dict[str, Any]) -> bool:
    return all(
        payload.get(field) is False
        for field in (
            "promotion_allowed",
            "formal_admission_allowed",
            "official_launch_allowed",
            "release_eligible",
            "scientific_claim_proven",
        )
        if field in payload
    )


def integration_receipt_green(payload: dict[str, Any]) -> bool:
    expected_false = (
        "install_attempted",
        "llm_gate_used",
        "promotion_allowed",
        "formal_admission_allowed",
        "official_launch_allowed",
        "release_eligible",
        "scientific_claim_proven",
    )
    steps = payload.get("steps")
    checks = payload.get("content_checks")
    return (
        payload.get("schema") == "codex_ratchet.v8_integration_repair.gate_receipt.v1"
        and payload.get("integration_gate_pass") is True
        and payload.get("all_steps_pass") is True
        and payload.get("all_content_checks_pass") is True
        and all(payload.get(key) is False for key in expected_false)
        and isinstance(steps, list)
        and len(steps) == 11
        and all(
            row.get("pass") is True
            and row.get("returncode") == 0
            and row.get("timed_out") is False
            for row in steps
        )
        and isinstance(checks, dict)
        and bool(checks)
        and all(value is True for value in checks.values())
    )


def integration_bindings_green(root: Path, payload: dict[str, Any]) -> bool:
    records = payload.get("source_bindings", []) + payload.get("artifact_bindings", [])
    if not records:
        return False
    for record in records:
        relative = record.get("path")
        expected = record.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            return False
        path = root / relative
        if not path.is_file() or sha256_file(path) != expected:
            return False
    source_head = payload.get("source_head")
    if not isinstance(source_head, str) or not re.fullmatch(r"[0-9a-f]{40}", source_head):
        return False
    check = subprocess.run(
        ["git", "cat-file", "-e", f"{source_head}^{{commit}}"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return check.returncode == 0


def provider_catalog_valid(payload: dict[str, Any], provider: str) -> bool:
    models = payload.get("models")
    return (
        payload.get("schema") == "codex_ratchet.provider_catalog_receipt.v1"
        and payload.get("provider") == provider
        and payload.get("status") == "completed"
        and payload.get("http_status") == 200
        and payload.get("fixture_used") is False
        and payload.get("advisory_only") is True
        and payload.get("gate_authority") is False
        and payload.get("evidence_allowed") is False
        and payload.get("promotion_allowed") is False
        and payload.get("formal_admission_allowed") is False
        and payload.get("scientific_claim_proven") is False
        and isinstance(models, list)
        and bool(models)
        and models == sorted(set(models))
        and payload.get("model_count") == len(models)
    )


def provider_preflight_hold(
    payload: dict[str, Any], provider: str, model: str
) -> bool:
    return (
        payload.get("schema") == "codex_ratchet.provider_advisory_preflight.v1"
        and payload.get("provider") == provider
        and payload.get("model") == model
        and payload.get("decision") == "HOLD"
        and payload.get("reason") == "quota_unknown"
        and payload.get("max_requests") is None
        and payload.get("window_seconds") is None
        and payload.get("remaining_requests") is None
        and payload.get("advisory_only") is True
        and payload.get("gate_authority") is False
        and payload.get("evidence_allowed") is False
        and payload.get("promotion_allowed") is False
        and payload.get("formal_admission_allowed") is False
        and payload.get("scientific_claim_proven") is False
    )


def claude_receipt_valid(payload: dict[str, Any]) -> bool:
    route = payload.get("route", {})
    parsed = payload.get("parsed", {})
    prompt_path = Path(str(payload.get("prompt_path", "")))
    output_path = Path(str(payload.get("output_path", "")))
    return (
        payload.get("schema") == "codex-ratchet.claude-bridge-receipt.v1"
        and payload.get("execution_mode") == "dry_run"
        and payload.get("provider_invoked") is False
        and payload.get("provider_returncode") is None
        and payload.get("wrapper_returncode") == 0
        and payload.get("timed_out") is False
        and payload.get("advisory_only") is True
        and payload.get("gate_authority") is False
        and payload.get("evidence_allowed") is False
        and payload.get("gate_decision") == "not_applicable"
        and payload.get("promotion_allowed") is False
        and payload.get("formal_admission_allowed") is False
        and payload.get("release_eligible") is False
        and payload.get("official_launch_allowed") is False
        and payload.get("scientific_claim_proven") is False
        and route.get("requested_model") == "fable5"
        and route.get("routed_model") == "fable"
        and route.get("resolution_kind") == "moving_alias"
        and payload.get("backend_models") == []
        and payload.get("backend_model_truth_source") == "output.modelUsage"
        and parsed.get("dry_run") is True
        and prompt_path.is_file()
        and output_path.is_file()
        and sha256_file(prompt_path) == payload.get("prompt_sha256")
        and sha256_file(output_path) == payload.get("output_sha256")
    )


def git_metadata(lev_worktree: Path, expected_commit: str) -> dict[str, Any]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=lev_worktree,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=lev_worktree,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    changed = subprocess.run(
        ["git", "show", "--format=", "--name-only", expected_commit],
        cwd=lev_worktree,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    changed_paths = sorted(line for line in changed.stdout.splitlines() if line)
    required_paths = [
        "core/eval/src/proof-bundle.ts",
        "core/exec/src/run/evidence.ts",
        "core/exec/src/run/monitor-heartbeat-evidence.test.ts",
    ]
    observed_head = head.stdout.strip()
    clean = status.returncode == 0 and status.stdout == ""
    identity_bound = (
        head.returncode == 0
        and status.returncode == 0
        and changed.returncode == 0
        and observed_head == expected_commit
        and clean
        and all(path in changed_paths for path in required_paths)
    )
    source_bindings = []
    for relative in required_paths:
        path = lev_worktree / relative
        if path.is_file():
            source_bindings.append(binding(path))
    return {
        "path": str(lev_worktree.resolve()),
        "expected_commit": expected_commit,
        "observed_head": observed_head,
        "worktree_clean": clean,
        "changed_paths": changed_paths,
        "required_paths": required_paths,
        "required_source_bindings": source_bindings,
        "identity_bound": identity_bound,
        "test_claim": "not made by this auditor; source branch identity only",
        "process_admission_proven": False,
        "gate_authority": False,
    }


def build_paths(root: Path, frozen_campaign_root: Path) -> dict[str, Path]:
    return {
        "qit_receipt": root
        / "system_v5/ops/tooling/v8_integration_repair_20260715/results/integration_gate_receipt.json",
        "qit_validation": root
        / "system_v5/ops/tooling/v8_integration_repair_20260715/results/integration_gate_validation.json",
        "v0_g0_g9": root
        / "system_v7/sims/tolerance_to_equivalence_ratchet_rung_v0/results/g0_g9_report.json",
        "v0_final": root
        / "system_v7/sims/tolerance_to_equivalence_ratchet_rung_v0/results/final_report.json",
        "v0_semantic_audit": root
        / "system_v7/sims/tolerance_to_equivalence_ratchet_rung_v0/results/semantic_audit.json",
        "v1_seal": root
        / "system_v7/sims/tolerance_to_equivalence_ratchet_rung_v1_semantic_forcing/preregistration_receipt.json",
        "v1_spec": root
        / "system_v7/sims/tolerance_to_equivalence_ratchet_rung_v1_semantic_forcing/spec.json",
        "nvidia_catalog": root
        / "system_v5/ops/tooling/provider_advisory_control_v1/results/nvidia_catalog_20260715.json",
        "nvidia_preflight": root
        / "system_v5/ops/tooling/provider_advisory_control_v1/results/nvidia_deepseek_v4_pro_preflight_20260715.json",
        "xai_catalog": root
        / "system_v5/ops/tooling/provider_advisory_control_v1/results/xai_catalog_20260715.json",
        "xai_preflight": root
        / "system_v5/ops/tooling/provider_advisory_control_v1/results/xai_grok45_preflight_20260715.json",
        "frozen_execution": frozen_campaign_root / "results/campaign_execution.json",
        "frozen_validation": frozen_campaign_root / "results/campaign_validation.json",
        "frozen_diagnostics": frozen_campaign_root / "results/postrun_diagnostics.json",
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--frozen-campaign-root", type=Path, required=True)
    parser.add_argument("--lev-worktree", type=Path, required=True)
    parser.add_argument("--expected-lev-commit", required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.repo_root.resolve()
    frozen_campaign_root = args.frozen_campaign_root.resolve()
    lev_worktree = args.lev_worktree.resolve()
    out = args.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    if not re.fullmatch(r"[0-9a-f]{40}", args.expected_lev_commit):
        errors.append("expected Lev commit must be a full lowercase 40-character SHA")

    paths = build_paths(root, frozen_campaign_root)
    payloads: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        try:
            payloads[name] = load_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            errors.append(f"{name} unavailable or invalid: {type(error).__name__}")

    python = str(Path(args.python).resolve())
    v0_dir = root / "system_v7/sims/tolerance_to_equivalence_ratchet_rung_v0"
    v1_dir = root / "system_v7/sims/tolerance_to_equivalence_ratchet_rung_v1_semantic_forcing"
    provider_dir = root / "system_v5/ops/tooling/provider_advisory_control_v1"
    claude_dir = root / "system_v5/codex_skills/claude-bridge"
    claude_out = out.parent / "claude_dry_run"

    steps = [
        run_step(
            "v0_g0_g9_validator",
            [python, "-B", str(v0_dir / "validate_g0_g9_report.py")],
            cwd=root,
        ),
        run_step(
            "v0_final_validator",
            [python, "-B", str(v0_dir / "validate_final_report.py")],
            cwd=root,
        ),
        run_step(
            "v1_preregistration_validator",
            [python, "-B", str(v1_dir / "validate_preregistration.py")],
            cwd=v1_dir,
        ),
    ]
    for provider_name in ("nvidia_catalog", "nvidia_preflight", "xai_catalog", "xai_preflight"):
        steps.append(
            run_step(
                f"provider_validator_{provider_name}",
                [
                    python,
                    "-B",
                    str(provider_dir / "validate_provider_advisory.py"),
                    str(paths[provider_name]),
                ],
                cwd=root,
            )
        )
    steps.append(
        run_step(
            "claude_bridge_unit_tests",
            [
                python,
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                str(claude_dir / "tests"),
                "-p",
                "test_claude_bridge.py",
                "-v",
            ],
            cwd=root,
        )
    )
    claude_dry_step = run_step(
        "claude_bridge_fable5_dry_run",
        [
            python,
            "-B",
            str(claude_dir / "scripts/claude_bridge.py"),
            "--dry-run",
            "--model",
            "fable5",
            "--budget",
            "1",
            "--cwd",
            "/tmp",
            "--out-dir",
            str(claude_out),
            "--name",
            "v8-readiness-audit",
            "--prompt",
            "deterministic advisory route inspection only",
        ],
        cwd=root,
    )
    steps.append(claude_dry_step)
    claude_receipt = parse_json_stdout(claude_dry_step)
    claude_receipt_path = Path(str(claude_receipt.get("receipt_path", "")))
    if claude_receipt_path.is_file():
        paths["claude_dry_receipt"] = claude_receipt_path
        payloads["claude_dry_receipt"] = claude_receipt
        steps.append(
            run_step(
                "claude_bridge_dry_receipt_validator",
                [
                    python,
                    "-B",
                    str(claude_dir / "scripts/validate_receipt.py"),
                    str(claude_receipt_path),
                ],
                cwd=root,
            )
        )
    else:
        errors.append("Claude dry-run receipt was not created")

    step_by_id = {row["step_id"]: row for row in steps}
    v0_validation = parse_json_stdout(step_by_id["v0_g0_g9_validator"])
    v0_final_validation = parse_json_stdout(step_by_id["v0_final_validator"])
    v1_validation = parse_json_stdout(step_by_id["v1_preregistration_validator"])

    qit_receipt = payloads.get("qit_receipt", {})
    qit_validation = payloads.get("qit_validation", {})
    v0_g0_g9 = payloads.get("v0_g0_g9", {})
    v0_final = payloads.get("v0_final", {})
    v0_semantic = payloads.get("v0_semantic_audit", {})
    v1_seal = payloads.get("v1_seal", {})
    v1_spec = payloads.get("v1_spec", {})
    nvidia_catalog = payloads.get("nvidia_catalog", {})
    nvidia_preflight = payloads.get("nvidia_preflight", {})
    xai_catalog = payloads.get("xai_catalog", {})
    xai_preflight = payloads.get("xai_preflight", {})
    frozen_execution = payloads.get("frozen_execution", {})
    frozen_validation = payloads.get("frozen_validation", {})
    frozen_diagnostics = payloads.get("frozen_diagnostics", {})

    v1_builder_paths = v1_spec.get("builder_paths", [])
    v1_builders_absent = (
        isinstance(v1_builder_paths, list)
        and len(v1_builder_paths) == 3
        and all(not (v1_dir / str(relative)).exists() for relative in v1_builder_paths)
        and v1_seal.get("builder_paths")
        == {"run_jax.py": False, "run_julia.jl": False, "run_pytorch.py": False}
    )

    lev = git_metadata(lev_worktree, args.expected_lev_commit)
    provider_step_ids = [
        "provider_validator_nvidia_catalog",
        "provider_validator_nvidia_preflight",
        "provider_validator_xai_catalog",
        "provider_validator_xai_preflight",
    ]
    provider_validators_green = all(
        step_by_id[step_id]["returncode"] == 0
        and parse_json_stdout(step_by_id[step_id]).get("valid") is True
        for step_id in provider_step_ids
    )
    claude_validator_green = (
        "claude_bridge_dry_receipt_validator" in step_by_id
        and step_by_id["claude_bridge_dry_receipt_validator"]["returncode"] == 0
    )
    claude_tests_green = (
        step_by_id["claude_bridge_unit_tests"]["returncode"] == 0
        and re.search(r"Ran\s+20\s+tests", step_by_id["claude_bridge_unit_tests"]["stderr"])
        is not None
        and "OK" in step_by_id["claude_bridge_unit_tests"]["stderr"]
    )

    checks = {
        "qit_integration_receipt_green_and_nongating": integration_receipt_green(qit_receipt),
        "qit_integration_bindings_current": integration_bindings_green(root, qit_receipt),
        "qit_independent_validation_green": (
            qit_validation.get("schema")
            == "codex_ratchet.v8_integration_repair.gate_validation.v1"
            and qit_validation.get("ok") is True
            and qit_validation.get("failures") == []
            and qit_validation.get("mutation_selftest", {}).get("all_rejected") is True
            and is_closed(qit_validation)
        ),
        "v0_mechanical_g0_g9_green": (
            v0_g0_g9.get("mechanical_pass") is True
            and v0_g0_g9.get("candidate_pass") is False
            and v0_g0_g9.get("final_decision") == "HOLD_SEMANTIC_FORCING"
            and v0_g0_g9.get("gates", {}).get("G10_deterministic_lev_replay") is False
            and v0_validation.get("ok") is True
            and step_by_id["v0_g0_g9_validator"]["returncode"] == 0
        ),
        "v0_semantic_forcing_red_and_state_open": (
            v0_g0_g9.get("semantic_forcing_pass") is False
            and v0_final.get("semantic_forcing_pass") is False
            and v0_final.get("all_code_gates_pass") is False
            and v0_final.get("decision") == "HOLD_DESIGNED_SURROGATE"
            and v0_final.get("ratchet_state_after") == "OPEN"
            and v0_semantic.get("semantic_forcing_pass") is False
            and v0_semantic.get("found_fabrication") is True
            and v0_semantic.get("decision") == "HOLD_DESIGNED_SURROGATE"
            and v0_final_validation.get("ok") is True
            and step_by_id["v0_final_validator"]["returncode"] == 0
        ),
        "v0_authority_fences_closed": (
            is_closed(v0_final)
            and is_closed(v0_semantic)
            and v0_g0_g9.get("promotion_allowed") is False
            and v0_g0_g9.get("formal_admission_allowed") is False
            and v0_g0_g9.get("llm_verdict_used") is False
            and v0_final.get("llm_verdict_used") is False
        ),
        "v1_preregistration_sealed": (
            v1_seal.get("schema")
            == "codex_ratchet.tolerance_to_equivalence_v1.preregistration_receipt.v1"
            and v1_seal.get("status") == "SEALED_PREREGISTRATION_BUILDERS_ABSENT"
            and v1_seal.get("classification") == "scratch_diagnostic"
            and v1_seal.get("llm_verdict_used") is False
            and v1_seal.get("promotion_allowed") is False
            and v1_seal.get("formal_admission_allowed") is False
            and v1_seal.get("official_launch_allowed") is False
            and v1_validation.get("ok") is True
            and v1_validation.get("builder_paths_absent") is True
            and step_by_id["v1_preregistration_validator"]["returncode"] == 0
        ),
        "v1_engine_builders_absent": v1_builders_absent,
        "provider_catalogs_valid_nongating": (
            provider_validators_green
            and provider_catalog_valid(nvidia_catalog, "nvidia")
            and provider_catalog_valid(xai_catalog, "xai")
            and "deepseek-ai/deepseek-v4-pro" in nvidia_catalog.get("models", [])
            and "grok-4.5" in xai_catalog.get("models", [])
        ),
        "provider_quota_preflights_hold_unknown": (
            provider_preflight_hold(
                nvidia_preflight, "nvidia", "deepseek-ai/deepseek-v4-pro"
            )
            and provider_preflight_hold(xai_preflight, "xai", "grok-4.5")
        ),
        "claude_bridge_tests_green": claude_tests_green,
        "claude_fable5_dry_receipt_valid_nongating": (
            claude_validator_green and claude_receipt_valid(claude_receipt)
        ),
        "frozen_campaign_red_nonofficial": (
            frozen_execution.get("schema")
            == "codex_ratchet.v8_nonofficial_stress_campaign.execution.v1"
            and frozen_execution.get("campaign_id")
            == "v8_nonofficial_stress_campaign_20260715"
            and frozen_execution.get("all_expected_outcomes_observed") is False
            and frozen_execution.get("all_systems_green") is False
            and frozen_execution.get("execution_integrity_pass") is False
            and len(frozen_execution.get("cases", [])) == 10
            and frozen_validation.get("all_systems_green") is False
            and frozen_validation.get("integrity_pass") is False
            and frozen_validation.get("official_launch_allowed") is False
            and frozen_validation.get("promotion_allowed") is False
            and frozen_validation.get("formal_admission_allowed") is False
            and frozen_validation.get("scientific_claim_proven") is False
            and frozen_validation.get("llm_gate_used") is False
        ),
        "frozen_postrun_diagnostic_preserves_red": (
            frozen_diagnostics.get("schema")
            == "codex_ratchet.v8_nonofficial_stress_campaign.postrun_diagnostics.v1"
            and frozen_diagnostics.get("diagnostic_integrity_pass") is True
            and frozen_diagnostics.get("campaign_integrity_pass") is False
            and frozen_diagnostics.get("all_systems_green") is False
            and frozen_diagnostics.get("unexpected_red", {}).get("case_id")
            == "OLD_QIT_PROJECTION_BATTERY"
            and frozen_diagnostics.get("checks", {}).get("frozen_campaign_is_red") is True
            and frozen_diagnostics.get("checks", {}).get("official_launch_remains_closed")
            is True
            and is_closed(frozen_diagnostics)
        ),
        "lev_repair_branch_identity_bound": lev["identity_bound"],
        "lev_process_admission_remains_unproven": (
            lev["process_admission_proven"] is False and lev["gate_authority"] is False
        ),
        "all_runtime_steps_green": all(
            row.get("returncode") == 0 and row.get("timed_out") is False for row in steps
        ),
    }

    for name, result in checks.items():
        if result is not True:
            errors.append(f"required expected-state check failed: {name}")

    input_bindings: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        if path.is_file():
            input_bindings[name] = binding(path)

    source_paths = [
        HERE / "run_readiness_audit.py",
        HERE / "validate_readiness_receipt.py",
        v0_dir / "validate_g0_g9_report.py",
        v0_dir / "validate_final_report.py",
        v1_dir / "validate_preregistration.py",
        provider_dir / "validate_provider_advisory.py",
        claude_dir / "scripts/claude_bridge.py",
        claude_dir / "scripts/validate_receipt.py",
        claude_dir / "tests/test_claude_bridge.py",
    ]
    source_bindings = [binding(path) for path in source_paths if path.is_file()]

    audit_integrity_pass = not errors and all(checks.values())
    receipt = {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": CLASSIFICATION,
        "audit_kind": AUDIT_KIND,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "decision": "HOLD_NOT_READY",
        "launch_ready": False,
        "audit_integrity_pass": audit_integrity_pass,
        "all_systems_green": False,
        "official_launch_allowed": False,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "release_eligible": False,
        "scientific_claim_proven": False,
        "llm_gate_used": False,
        "provider_call_attempted": False,
        "install_attempted": False,
        "hold_reasons": EXPECTED_HOLD_REASONS,
        "checks": checks,
        "errors": errors,
        "claim_ceiling": (
            "code-only cross-system readiness diagnosis; QIT integration repair is green, "
            "but no Ratchet tooth, process admission, promotion, science claim, release, or "
            "official V8 launch is authorized"
        ),
        "authority_model": {
            "gate_type": "deterministic_local_code_only",
            "llm_or_provider_output_can_gate": False,
            "lev_role": "source-bound repair evidence only; no process-admission claim",
        },
        "paths": {
            "repo_root": str(root),
            "frozen_campaign_root": str(frozen_campaign_root),
            "lev_worktree": str(lev_worktree),
        },
        "lev": lev,
        "steps": steps,
        "inputs": input_bindings,
        "source_bindings": source_bindings,
    }
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "audit_integrity_pass": audit_integrity_pass,
                "decision": receipt["decision"],
                "launch_ready": receipt["launch_ready"],
                "out": str(out),
            },
            sort_keys=True,
        )
    )
    return 0 if audit_integrity_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
