#!/usr/bin/env python3
"""Independent fail-closed validator for the V8 readiness HOLD receipt."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Sequence


HERE = Path(__file__).resolve().parent
DEFAULT_RECEIPT = HERE / "results/readiness_receipt.json"
DEFAULT_OUT = HERE / "results/readiness_validation.json"

SCHEMA = "codex_ratchet.v8_launch_readiness.receipt.v1"
CLASSIFICATION = "controller_audit"
AUDIT_KIND = "v8_launch_readiness"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Validates bound JSON, hashes, negative mutations, and deterministic receipt structure.",
    },
    "git": {
        "used": True,
        "reason": "Rechecks the exact clean Lev repair commit and changed-path identity.",
    },
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive", "git": "supportive"}
EXPECTED_CHECKS = {
    "qit_integration_receipt_green_and_nongating",
    "qit_integration_bindings_current",
    "qit_independent_validation_green",
    "v0_mechanical_g0_g9_green",
    "v0_semantic_forcing_red_and_state_open",
    "v0_authority_fences_closed",
    "v1_preregistration_sealed",
    "v1_engine_builders_absent",
    "provider_catalogs_valid_nongating",
    "provider_quota_preflights_hold_unknown",
    "claude_bridge_tests_green",
    "claude_fable5_dry_receipt_valid_nongating",
    "frozen_campaign_red_nonofficial",
    "frozen_postrun_diagnostic_preserves_red",
    "lev_repair_branch_identity_bound",
    "lev_narrow_evidence_valid_but_transitional",
    "lev_process_admission_remains_unproven",
    "all_runtime_steps_green",
}
EXPECTED_HOLD_REASONS = {
    "V0_SEMANTIC_FORCING_FAILED",
    "V1_BUILDERS_ABSENT",
    "FROZEN_CAMPAIGN_RED_NONOFFICIAL",
    "NVIDIA_QUOTA_UNKNOWN",
    "XAI_QUOTA_UNKNOWN",
    "CLAUDE_BRIDGE_ADVISORY_ONLY",
    "LEV_REPAIR_SOURCE_BOUND_NOT_PROCESS_ADMISSION",
}
EXPECTED_STEPS = {
    "v0_g0_g9_validator",
    "v0_final_validator",
    "v1_preregistration_validator",
    "provider_validator_nvidia_catalog",
    "provider_validator_nvidia_preflight",
    "provider_validator_xai_catalog",
    "provider_validator_xai_preflight",
    "claude_bridge_unit_tests",
    "claude_bridge_fable5_dry_run",
    "claude_bridge_dry_receipt_validator",
}
REQUIRED_INPUTS = {
    "qit_receipt",
    "qit_validation",
    "v0_g0_g9",
    "v0_final",
    "v0_semantic_audit",
    "v1_seal",
    "v1_spec",
    "nvidia_catalog",
    "nvidia_preflight",
    "xai_catalog",
    "xai_preflight",
    "frozen_execution",
    "frozen_validation",
    "frozen_diagnostics",
    "lev_evidence",
    "lev_evidence_validation",
    "claude_dry_receipt",
}


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
        raise ValueError(f"JSON input is not an object: {path}")
    return value


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def closed(payload: dict[str, Any]) -> bool:
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


def bound_payloads(
    receipt: dict[str, Any], errors: list[str], *, verify_files: bool
) -> dict[str, dict[str, Any]]:
    inputs = receipt.get("inputs")
    require(errors, isinstance(inputs, dict), "input binding table missing")
    if not isinstance(inputs, dict):
        return {}
    require(errors, set(inputs) == REQUIRED_INPUTS, "input binding key set drift")
    payloads: dict[str, dict[str, Any]] = {}
    for name, record in inputs.items():
        if not isinstance(record, dict):
            errors.append(f"input binding is not an object: {name}")
            continue
        raw_path = record.get("path")
        expected_hash = record.get("sha256")
        expected_size = record.get("size_bytes")
        if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
            errors.append(f"input binding path is not absolute: {name}")
            continue
        path = Path(raw_path)
        if not verify_files:
            continue
        if not path.is_file():
            errors.append(f"bound input missing: {name}")
            continue
        if sha256_file(path) != expected_hash:
            errors.append(f"bound input hash drift: {name}")
            continue
        if path.stat().st_size != expected_size:
            errors.append(f"bound input size drift: {name}")
            continue
        try:
            payloads[name] = load_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            errors.append(f"bound input parse failed: {name}: {type(error).__name__}")
    return payloads


def validate_qit(payloads: dict[str, dict[str, Any]], errors: list[str]) -> None:
    receipt = payloads.get("qit_receipt", {})
    validation = payloads.get("qit_validation", {})
    steps = receipt.get("steps")
    checks = receipt.get("content_checks")
    require(
        errors,
        receipt.get("schema") == "codex_ratchet.v8_integration_repair.gate_receipt.v1",
        "QIT integration receipt schema drift",
    )
    require(errors, receipt.get("integration_gate_pass") is True, "QIT integration gate red")
    require(errors, receipt.get("all_steps_pass") is True, "QIT step aggregate red")
    require(errors, receipt.get("all_content_checks_pass") is True, "QIT content aggregate red")
    require(
        errors,
        isinstance(steps, list)
        and len(steps) == 11
        and all(
            row.get("pass") is True
            and row.get("returncode") == 0
            and row.get("timed_out") is False
            for row in steps
        ),
        "QIT step ledger drift",
    )
    require(
        errors,
        isinstance(checks, dict) and bool(checks) and all(value is True for value in checks.values()),
        "QIT content checks are not all green",
    )
    require(errors, closed(receipt), "QIT receipt authority fence opened")
    require(errors, receipt.get("llm_gate_used") is False, "QIT receipt used LLM gate")
    require(
        errors,
        validation.get("schema")
        == "codex_ratchet.v8_integration_repair.gate_validation.v1"
        and validation.get("ok") is True
        and validation.get("failures") == []
        and validation.get("mutation_selftest", {}).get("all_rejected") is True,
        "QIT independent validation is not green",
    )
    require(errors, closed(validation), "QIT validation authority fence opened")


def validate_v0(payloads: dict[str, dict[str, Any]], errors: list[str]) -> None:
    g0 = payloads.get("v0_g0_g9", {})
    final = payloads.get("v0_final", {})
    semantic = payloads.get("v0_semantic_audit", {})
    require(
        errors,
        g0.get("schema") == "codex_ratchet.tolerance_to_equivalence.g0_g9_report.v1",
        "V0 G0-G9 schema drift",
    )
    require(errors, g0.get("mechanical_pass") is True, "V0 mechanical pass absent")
    require(errors, g0.get("semantic_forcing_pass") is False, "V0 semantic forcing opened")
    require(errors, g0.get("candidate_pass") is False, "V0 candidate falsely passed")
    require(
        errors,
        g0.get("final_decision") == "HOLD_SEMANTIC_FORCING",
        "V0 G0-G9 HOLD decision drift",
    )
    require(
        errors,
        g0.get("gates", {}).get("G10_deterministic_lev_replay") is False,
        "V0 G10 falsely opened",
    )
    require(
        errors,
        final.get("schema") == "codex_ratchet.tolerance_to_equivalence.final_report.v2",
        "V0 final schema drift",
    )
    require(errors, final.get("mechanical_code_gates_pass") is True, "V0 final lost mechanical green")
    require(errors, final.get("semantic_forcing_pass") is False, "V0 final semantic forcing opened")
    require(errors, final.get("all_code_gates_pass") is False, "V0 all-code gate falsely opened")
    require(errors, final.get("decision") == "HOLD_DESIGNED_SURROGATE", "V0 final HOLD drift")
    require(errors, final.get("ratchet_state_after") == "OPEN", "V0 state falsely ratcheted")
    require(errors, final.get("llm_verdict_used") is False, "V0 final used LLM verdict")
    require(errors, closed(final), "V0 final authority fence opened")
    require(
        errors,
        semantic.get("schema") == "codex_ratchet.tolerance_to_equivalence.semantic_audit.v1",
        "V0 semantic audit schema drift",
    )
    require(errors, semantic.get("semantic_forcing_pass") is False, "V0 semantic audit opened")
    require(errors, semantic.get("found_fabrication") is True, "V0 fabrication finding disappeared")
    require(
        errors,
        semantic.get("decision") == "HOLD_DESIGNED_SURROGATE",
        "V0 semantic audit HOLD drift",
    )
    require(errors, closed(semantic), "V0 semantic authority fence opened")
    for name, record in final.get("artifacts", {}).items():
        if not isinstance(record, dict):
            errors.append(f"V0 final artifact binding malformed: {name}")
            continue
        path = Path(str(record.get("path", "")))
        if not path.is_absolute():
            repo_root = Path(str(payloads.get("_paths", {}).get("repo_root", "")))
            path = repo_root / path
        require(
            errors,
            path.is_file() and sha256_file(path) == record.get("sha256"),
            f"V0 final artifact binding drift: {name}",
        )


def validate_v1(payloads: dict[str, dict[str, Any]], errors: list[str]) -> None:
    seal = payloads.get("v1_seal", {})
    spec = payloads.get("v1_spec", {})
    require(
        errors,
        seal.get("schema")
        == "codex_ratchet.tolerance_to_equivalence_v1.preregistration_receipt.v1",
        "V1 seal schema drift",
    )
    require(
        errors,
        seal.get("status") == "SEALED_PREREGISTRATION_BUILDERS_ABSENT",
        "V1 seal status drift",
    )
    require(errors, seal.get("classification") == "scratch_diagnostic", "V1 classification drift")
    require(errors, seal.get("llm_verdict_used") is False, "V1 used LLM verdict")
    require(errors, seal.get("promotion_allowed") is False, "V1 promotion fence opened")
    require(errors, seal.get("formal_admission_allowed") is False, "V1 admission fence opened")
    require(errors, seal.get("official_launch_allowed") is False, "V1 launch fence opened")
    require(
        errors,
        seal.get("builder_paths")
        == {"run_jax.py": False, "run_julia.jl": False, "run_pytorch.py": False},
        "V1 seal builder absence map drift",
    )
    require(
        errors,
        spec.get("status") == "PREREGISTRATION_ONLY_BUILDERS_ABSENT",
        "V1 spec status drift",
    )
    require(errors, spec.get("llm_verdict_allowed") is False, "V1 spec permits LLM verdict")
    require(errors, spec.get("promotion_allowed") is False, "V1 spec promotion fence opened")
    require(errors, spec.get("formal_admission_allowed") is False, "V1 spec admission fence opened")
    require(errors, spec.get("official_launch_allowed") is False, "V1 spec launch fence opened")
    require(
        errors,
        isinstance(spec.get("code_gates"), list) and len(spec["code_gates"]) == 13,
        "V1 P0-P12 vector drift",
    )
    seal_path = Path(str(payloads.get("_input_paths", {}).get("v1_seal", "")))
    v1_dir = seal_path.parent if seal_path else Path("/")
    builders = spec.get("builder_paths")
    require(
        errors,
        isinstance(builders, list)
        and len(builders) == 3
        and all(not (v1_dir / str(relative)).exists() for relative in builders),
        "V1 engine builder appeared after seal",
    )
    for name, expected_hash in seal.get("inputs", {}).items():
        path = v1_dir / name
        require(
            errors,
            path.is_file() and sha256_file(path) == expected_hash,
            f"V1 sealed input hash drift: {name}",
        )


def validate_providers(payloads: dict[str, dict[str, Any]], errors: list[str]) -> None:
    for provider, catalog_name, preflight_name, model in (
        ("nvidia", "nvidia_catalog", "nvidia_preflight", "deepseek-ai/deepseek-v4-pro"),
        ("xai", "xai_catalog", "xai_preflight", "grok-4.5"),
    ):
        catalog = payloads.get(catalog_name, {})
        models = catalog.get("models")
        require(
            errors,
            catalog.get("schema") == "codex_ratchet.provider_catalog_receipt.v1",
            f"{provider} catalog schema drift",
        )
        require(errors, catalog.get("provider") == provider, f"{provider} catalog provider drift")
        require(errors, catalog.get("status") == "completed", f"{provider} catalog incomplete")
        require(errors, catalog.get("fixture_used") is False, f"{provider} catalog used fixture")
        require(errors, catalog.get("advisory_only") is True, f"{provider} advisory fence drift")
        require(errors, catalog.get("gate_authority") is False, f"{provider} gained gate authority")
        require(errors, catalog.get("evidence_allowed") is False, f"{provider} evidence fence opened")
        require(errors, closed(catalog), f"{provider} catalog authority fence opened")
        require(
            errors,
            isinstance(models, list)
            and bool(models)
            and models == sorted(set(models))
            and catalog.get("model_count") == len(models)
            and model in models,
            f"{provider} catalog model set invalid",
        )
        preflight = payloads.get(preflight_name, {})
        require(
            errors,
            preflight.get("schema") == "codex_ratchet.provider_advisory_preflight.v1",
            f"{provider} preflight schema drift",
        )
        require(errors, preflight.get("provider") == provider, f"{provider} preflight provider drift")
        require(errors, preflight.get("model") == model, f"{provider} preflight model drift")
        require(errors, preflight.get("decision") == "HOLD", f"{provider} preflight dispatch opened")
        require(errors, preflight.get("reason") == "quota_unknown", f"{provider} quota reason drift")
        require(errors, preflight.get("max_requests") is None, f"{provider} invented request limit")
        require(errors, preflight.get("window_seconds") is None, f"{provider} invented quota window")
        require(errors, preflight.get("remaining_requests") is None, f"{provider} invented remaining quota")
        require(errors, preflight.get("advisory_only") is True, f"{provider} preflight advisory drift")
        require(errors, preflight.get("gate_authority") is False, f"{provider} preflight gate authority opened")
        require(errors, preflight.get("evidence_allowed") is False, f"{provider} preflight evidence opened")
        require(errors, closed(preflight), f"{provider} preflight authority fence opened")


def validate_claude(payloads: dict[str, dict[str, Any]], errors: list[str]) -> None:
    receipt = payloads.get("claude_dry_receipt", {})
    route = receipt.get("route", {})
    require(
        errors,
        receipt.get("schema") == "codex-ratchet.claude-bridge-receipt.v1",
        "Claude dry receipt schema drift",
    )
    require(errors, receipt.get("execution_mode") == "dry_run", "Claude receipt is not dry run")
    require(errors, receipt.get("provider_invoked") is False, "Claude provider was invoked")
    require(errors, receipt.get("provider_returncode") is None, "Claude provider returncode appeared")
    require(errors, receipt.get("wrapper_returncode") == 0, "Claude dry wrapper red")
    require(errors, receipt.get("timed_out") is False, "Claude dry wrapper timed out")
    require(errors, receipt.get("advisory_only") is True, "Claude advisory fence drift")
    require(errors, receipt.get("gate_authority") is False, "Claude gained gate authority")
    require(errors, receipt.get("evidence_allowed") is False, "Claude evidence fence opened")
    require(errors, closed(receipt), "Claude authority fence opened")
    require(errors, receipt.get("gate_decision") == "not_applicable", "Claude emitted gate decision")
    require(errors, route.get("requested_model") == "fable5", "Claude requested alias drift")
    require(errors, route.get("routed_model") == "fable", "Claude fable5 route drift")
    require(errors, route.get("resolution_kind") == "moving_alias", "Claude alias is not moving")
    require(errors, receipt.get("backend_models") == [], "Claude dry run invented backend model")
    require(
        errors,
        receipt.get("backend_model_truth_source") == "output.modelUsage",
        "Claude backend truth source drift",
    )
    for key in ("prompt", "output"):
        path = Path(str(receipt.get(f"{key}_path", "")))
        require(
            errors,
            path.is_file() and sha256_file(path) == receipt.get(f"{key}_sha256"),
            f"Claude {key} binding drift",
        )


def validate_frozen(payloads: dict[str, dict[str, Any]], errors: list[str]) -> None:
    execution = payloads.get("frozen_execution", {})
    validation = payloads.get("frozen_validation", {})
    diagnostics = payloads.get("frozen_diagnostics", {})
    require(
        errors,
        execution.get("schema")
        == "codex_ratchet.v8_nonofficial_stress_campaign.execution.v1",
        "frozen execution schema drift",
    )
    require(
        errors,
        execution.get("campaign_id") == "v8_nonofficial_stress_campaign_20260715",
        "frozen campaign id drift",
    )
    require(errors, execution.get("all_expected_outcomes_observed") is False, "frozen execution red disappeared")
    require(errors, execution.get("all_systems_green") is False, "frozen execution falsely all-green")
    require(errors, execution.get("execution_integrity_pass") is False, "frozen execution integrity falsely green")
    require(errors, len(execution.get("cases", [])) == 10, "frozen campaign case count drift")
    require(errors, closed(execution), "frozen execution authority fence opened")
    require(errors, execution.get("llm_gate_used") is False, "frozen campaign used LLM gate")
    require(
        errors,
        validation.get("schema")
        == "codex_ratchet.v8_nonofficial_stress_campaign.validation.v1",
        "frozen validation schema drift",
    )
    require(errors, validation.get("integrity_pass") is False, "frozen validation falsely green")
    require(errors, validation.get("all_systems_green") is False, "frozen validation falsely all-green")
    require(errors, closed(validation), "frozen validation authority fence opened")
    require(errors, validation.get("llm_gate_used") is False, "frozen validation used LLM gate")
    require(
        errors,
        diagnostics.get("schema")
        == "codex_ratchet.v8_nonofficial_stress_campaign.postrun_diagnostics.v1",
        "frozen diagnostics schema drift",
    )
    require(errors, diagnostics.get("diagnostic_integrity_pass") is True, "postrun diagnosis red")
    require(errors, diagnostics.get("campaign_integrity_pass") is False, "postrun rewrote frozen red")
    require(errors, diagnostics.get("all_systems_green") is False, "postrun falsely all-green")
    require(
        errors,
        diagnostics.get("unexpected_red", {}).get("case_id") == "OLD_QIT_PROJECTION_BATTERY",
        "frozen unexpected red identity drift",
    )
    require(
        errors,
        diagnostics.get("checks", {}).get("frozen_campaign_is_red") is True
        and diagnostics.get("checks", {}).get("official_launch_remains_closed") is True,
        "postrun red/launch checks drift",
    )
    require(errors, closed(diagnostics), "postrun diagnostics authority fence opened")
    require(errors, diagnostics.get("llm_gate_used") is False, "postrun diagnostics used LLM gate")


def validate_lev(receipt: dict[str, Any], errors: list[str]) -> None:
    lev = receipt.get("lev")
    require(errors, isinstance(lev, dict), "Lev binding missing")
    if not isinstance(lev, dict):
        return
    raw_path = lev.get("path")
    expected = lev.get("expected_commit")
    observed = lev.get("observed_head")
    require(errors, isinstance(raw_path, str) and Path(raw_path).is_absolute(), "Lev path invalid")
    require(
        errors,
        isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{40}", expected) is not None,
        "Lev expected commit invalid",
    )
    require(errors, observed == expected, "Lev recorded HEAD mismatch")
    require(errors, lev.get("worktree_clean") is True, "Lev worktree was not clean")
    require(errors, lev.get("identity_bound") is True, "Lev identity binding red")
    require(errors, lev.get("process_admission_proven") is False, "Lev process admission falsely proven")
    require(errors, lev.get("gate_authority") is False, "Lev source branch gained gate authority")
    if not isinstance(raw_path, str) or not Path(raw_path).is_dir() or not isinstance(expected, str):
        return
    path = Path(raw_path)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    changed = subprocess.run(
        ["git", "show", "--format=", "--name-only", expected],
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    required_paths = {
        "core/eval/src/proof-bundle.ts",
        "core/exec/src/run/evidence.ts",
        "core/exec/src/run/monitor-heartbeat-evidence.test.ts",
    }
    require(errors, head.returncode == 0 and head.stdout.strip() == expected, "live Lev HEAD drift")
    require(errors, status.returncode == 0 and status.stdout == "", "live Lev worktree drift")
    require(
        errors,
        changed.returncode == 0 and required_paths <= set(changed.stdout.splitlines()),
        "live Lev repair path set drift",
    )
    bindings = lev.get("required_source_bindings")
    require(errors, isinstance(bindings, list) and len(bindings) == 3, "Lev source bindings incomplete")
    if isinstance(bindings, list):
        for record in bindings:
            source = Path(str(record.get("path", "")))
            require(
                errors,
                source.is_file()
                and sha256_file(source) == record.get("sha256")
                and source.stat().st_size == record.get("size_bytes"),
                f"Lev source binding drift: {source}",
            )


def validate_lev_evidence(
    payloads: dict[str, dict[str, Any]],
    receipt: dict[str, Any],
    errors: list[str],
) -> None:
    evidence = payloads.get("lev_evidence", {})
    validation = payloads.get("lev_evidence_validation", {})
    lev = receipt.get("lev", {})
    expected_commit = lev.get("expected_commit")
    lev_path = Path(str(lev.get("path", "")))
    repository = evidence.get("repository", {})
    commands = {
        row.get("id"): row
        for row in evidence.get("commands", [])
        if isinstance(row, dict)
    }
    require(
        errors,
        evidence.get("schema") == "lev.v8_monitor_proof_evidence_repair_receipt.v1",
        "Lev evidence snapshot schema drift",
    )
    require(
        errors,
        evidence.get("gate_implementation") == "python_stdlib_deterministic"
        and evidence.get("llm_gate_authority") is False,
        "Lev evidence gate authority drift",
    )
    require(errors, repository.get("commit") == expected_commit, "Lev evidence commit drift")
    require(
        errors,
        Path(str(repository.get("cwd", ""))).resolve() == lev_path.resolve(),
        "Lev evidence cwd drift",
    )
    expected_ids = {
        "exec_monitor_heartbeat_evidence_test",
        "eval_proof_bundle_test",
        "eval_typecheck",
        "exec_typecheck",
    }
    require(errors, set(commands) == expected_ids, "Lev evidence command set drift")
    monitor = commands.get("exec_monitor_heartbeat_evidence_test", {})
    proof = commands.get("eval_proof_bundle_test", {})
    eval_typecheck = commands.get("eval_typecheck", {})
    exec_typecheck = commands.get("exec_typecheck", {})
    require(
        errors,
        monitor.get("exit_code") == 0
        and monitor.get("result", {}).get("tests_passed") == 4
        and monitor.get("result", {}).get("tests_total") == 4,
        "Lev monitor narrow result drift",
    )
    require(
        errors,
        proof.get("exit_code") == 0
        and proof.get("result", {}).get("tests_passed") == 6
        and proof.get("result", {}).get("tests_total") == 6,
        "Lev legacy proof-bundle narrow result drift",
    )
    require(
        errors,
        eval_typecheck.get("exit_code") == 0
        and eval_typecheck.get("result", {}).get("typecheck_passed") is True,
        "Lev eval typecheck result drift",
    )
    require(
        errors,
        exec_typecheck.get("exit_code") == 2
        and exec_typecheck.get("result", {}).get("typecheck_passed") is False
        and exec_typecheck.get("result", {}).get("expected_red_preserved") is True,
        "Lev exec typecheck expected red drift",
    )
    require(
        errors,
        evidence.get("full_suites", {}).get("core_exec")
        == {"run_in_this_receipt": False, "current_counts": None}
        and evidence.get("full_suites", {}).get("core_eval")
        == {"run_in_this_receipt": False, "current_counts": None},
        "Lev evidence invented full-suite counts",
    )
    authority = evidence.get("authority", {})
    readiness = evidence.get("readiness", {})
    require(
        errors,
        authority.get("canonical_promotion_verdict") == "EvalDecision"
        and authority.get("legacy_objects_have_active_promotion_authority") is False
        and authority.get("transitional_repair") is True
        and authority.get("final_proof_readiness") is False,
        "Lev evidence authority ceiling drift",
    )
    require(
        errors,
        readiness.get("state") == "HOLD_TRANSITIONAL"
        and readiness.get("final_proof_readiness") is False
        and readiness.get("exec_typecheck_passed") is False,
        "Lev evidence HOLD state drift",
    )
    source_hashes = evidence.get("source_hashes_sha256", {})
    require(errors, isinstance(source_hashes, dict) and len(source_hashes) == 3, "Lev evidence source hash set drift")
    if isinstance(source_hashes, dict):
        for relative, expected_hash in source_hashes.items():
            path = lev_path / str(relative)
            require(
                errors,
                path.is_file() and sha256_file(path) == expected_hash,
                f"Lev evidence source hash drift: {relative}",
            )
    require(
        errors,
        validation.get("schema")
        == "lev.v8_monitor_proof_evidence_repair_validation.v1"
        and validation.get("ok") is True
        and validation.get("checks_total") == 30
        and validation.get("checks_passed") == 30
        and validation.get("failed") == []
        and validation.get("rerun_exit_codes")
        == {
            "eval_proof_bundle_test": 0,
            "eval_typecheck": 0,
            "exec_monitor_heartbeat_evidence_test": 0,
            "exec_typecheck": 2,
        }
        and validation.get("decision") == "HOLD_TRANSITIONAL"
        and validation.get("final_proof_readiness") is False,
        "Lev evidence independent validation drift",
    )


def validate_source_bindings(receipt: dict[str, Any], errors: list[str]) -> None:
    records = receipt.get("source_bindings")
    require(errors, isinstance(records, list) and len(records) >= 9, "source bindings incomplete")
    if not isinstance(records, list):
        return
    for record in records:
        path = Path(str(record.get("path", "")))
        require(
            errors,
            path.is_absolute()
            and path.is_file()
            and sha256_file(path) == record.get("sha256")
            and path.stat().st_size == record.get("size_bytes"),
            f"source binding drift: {path}",
        )


def validate_steps(receipt: dict[str, Any], errors: list[str]) -> None:
    steps = receipt.get("steps")
    require(errors, isinstance(steps, list), "runtime step ledger missing")
    if not isinstance(steps, list):
        return
    ids = [row.get("step_id") for row in steps]
    require(errors, set(ids) == EXPECTED_STEPS and len(ids) == len(EXPECTED_STEPS), "runtime step id set drift")
    for row in steps:
        step_id = row.get("step_id")
        stdout = row.get("stdout")
        stderr = row.get("stderr")
        require(errors, row.get("returncode") == 0, f"runtime step red: {step_id}")
        require(errors, row.get("timed_out") is False, f"runtime step timed out: {step_id}")
        require(errors, isinstance(stdout, str), f"runtime stdout missing: {step_id}")
        require(errors, isinstance(stderr, str), f"runtime stderr missing: {step_id}")
        if isinstance(stdout, str):
            require(
                errors,
                sha256_text(stdout) == row.get("stdout_sha256"),
                f"runtime stdout hash drift: {step_id}",
            )
        if isinstance(stderr, str):
            require(
                errors,
                sha256_text(stderr) == row.get("stderr_sha256"),
                f"runtime stderr hash drift: {step_id}",
            )
    by_id = {row.get("step_id"): row for row in steps}
    claude_tests = by_id.get("claude_bridge_unit_tests", {})
    require(
        errors,
        re.search(r"Ran\s+20\s+tests", str(claude_tests.get("stderr", ""))) is not None
        and "OK" in str(claude_tests.get("stderr", "")),
        "Claude unit-test count/status drift",
    )
    for step_id in (
        "v0_g0_g9_validator",
        "v0_final_validator",
        "v1_preregistration_validator",
    ):
        try:
            parsed = json.loads(by_id.get(step_id, {}).get("stdout", ""))
        except json.JSONDecodeError:
            parsed = {}
        require(errors, parsed.get("ok") is True, f"validator output is not green: {step_id}")
    for step_id in (
        "provider_validator_nvidia_catalog",
        "provider_validator_nvidia_preflight",
        "provider_validator_xai_catalog",
        "provider_validator_xai_preflight",
    ):
        try:
            parsed = json.loads(by_id.get(step_id, {}).get("stdout", ""))
        except json.JSONDecodeError:
            parsed = {}
        require(errors, parsed.get("valid") is True, f"provider validator output red: {step_id}")


def validate(
    receipt: dict[str, Any], *, verify_files: bool = True
) -> list[str]:
    errors: list[str] = []
    require(errors, receipt.get("schema") == SCHEMA, "readiness receipt schema drift")
    require(errors, receipt.get("classification") == CLASSIFICATION, "classification drift")
    require(errors, receipt.get("audit_kind") == AUDIT_KIND, "audit kind drift")
    require(errors, receipt.get("decision") == "HOLD_NOT_READY", "readiness decision drift")
    require(errors, receipt.get("launch_ready") is False, "launch_ready opened")
    require(errors, receipt.get("audit_integrity_pass") is True, "audit integrity is red")
    require(errors, receipt.get("all_systems_green") is False, "all_systems_green falsely opened")
    for field in (
        "official_launch_allowed",
        "promotion_allowed",
        "formal_admission_allowed",
        "release_eligible",
        "scientific_claim_proven",
        "llm_gate_used",
        "provider_call_attempted",
        "install_attempted",
    ):
        require(errors, receipt.get(field) is False, f"{field} must remain false")
    require(errors, receipt.get("errors") == [], "runner recorded readiness errors")
    checks = receipt.get("checks")
    require(errors, isinstance(checks, dict), "check vector missing")
    if isinstance(checks, dict):
        require(errors, set(checks) == EXPECTED_CHECKS, "check vector key set drift")
        require(errors, all(value is True for value in checks.values()), "one or more expected-state checks are red")
    hold_reasons = receipt.get("hold_reasons")
    require(
        errors,
        isinstance(hold_reasons, list)
        and len(hold_reasons) == len(EXPECTED_HOLD_REASONS)
        and set(hold_reasons) == EXPECTED_HOLD_REASONS,
        "HOLD reason set drift",
    )
    authority = receipt.get("authority_model", {})
    require(
        errors,
        authority.get("gate_type") == "deterministic_local_code_only"
        and authority.get("llm_or_provider_output_can_gate") is False,
        "authority model drift",
    )
    tool_manifest = receipt.get("TOOL_MANIFEST")
    depth = receipt.get("TOOL_INTEGRATION_DEPTH")
    require(
        errors,
        isinstance(tool_manifest, dict)
        and set(tool_manifest) == {"python_stdlib", "git"}
        and all(isinstance(value.get("reason"), str) and value["reason"] for value in tool_manifest.values()),
        "tool manifest drift",
    )
    require(
        errors,
        depth == {"git": "supportive", "python_stdlib": "supportive"},
        "tool integration depth drift",
    )
    payloads = bound_payloads(receipt, errors, verify_files=verify_files)
    paths = receipt.get("paths", {})
    payloads["_paths"] = paths if isinstance(paths, dict) else {}
    payloads["_input_paths"] = {
        name: record.get("path")
        for name, record in receipt.get("inputs", {}).items()
        if isinstance(record, dict)
    }
    if verify_files:
        validate_qit(payloads, errors)
        validate_v0(payloads, errors)
        validate_v1(payloads, errors)
        validate_providers(payloads, errors)
        validate_claude(payloads, errors)
        validate_frozen(payloads, errors)
        validate_lev(receipt, errors)
        validate_lev_evidence(payloads, receipt, errors)
        validate_source_bindings(receipt, errors)
    validate_steps(receipt, errors)
    return errors


def mutation_selftest(receipt: dict[str, Any]) -> dict[str, Any]:
    mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("open_launch_ready", lambda value: value.__setitem__("launch_ready", True)),
        ("open_official_launch", lambda value: value.__setitem__("official_launch_allowed", True)),
        ("allow_llm_gate", lambda value: value.__setitem__("llm_gate_used", True)),
        ("erase_hold_reason", lambda value: value["hold_reasons"].pop()),
        (
            "flip_semantic_hold_check",
            lambda value: value["checks"].__setitem__(
                "v0_semantic_forcing_red_and_state_open", False
            ),
        ),
        (
            "erase_input_hash",
            lambda value: value["inputs"]["v0_final"].__setitem__("sha256", "0" * 64),
        ),
        (
            "rewrite_lev_commit",
            lambda value: value["lev"].__setitem__("expected_commit", "0" * 40),
        ),
        (
            "provider_call_claim",
            lambda value: value.__setitem__("provider_call_attempted", True),
        ),
    ]
    cases = []
    for name, mutate in mutations:
        candidate = copy.deepcopy(receipt)
        mutate(candidate)
        cases.append({"case": name, "rejected": bool(validate(candidate, verify_files=True))})
    return {"all_rejected": all(row["rejected"] for row in cases), "cases": cases}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path, nargs="?", default=DEFAULT_RECEIPT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    failures: list[str]
    try:
        receipt = load_json(args.receipt)
        failures = validate(receipt, verify_files=True)
        mutations = mutation_selftest(receipt)
        if not mutations["all_rejected"]:
            failures.append("validator mutation self-test is red")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        receipt = {}
        failures = [f"receipt parse failure: {type(error).__name__}"]
        mutations = {"all_rejected": False, "cases": []}
    result = {
        "schema": "codex_ratchet.v8_launch_readiness.validation.v1",
        "ok": not failures,
        "decision": "HOLD_NOT_READY",
        "launch_ready": False,
        "failures": failures,
        "mutation_selftest": mutations,
        "official_launch_allowed": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "release_eligible": False,
        "scientific_claim_proven": False,
        "llm_gate_used": False,
        "claim_ceiling": "independent validation of a deterministic HOLD receipt only",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "out": str(args.out.resolve())}, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
