#!/usr/bin/env python3
"""Fail-closed validation for Codex Ratchet deep-stack operational receipts."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shlex
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

TOOL_SCHEMA = "codex-ratchet.deep-stack-tool-receipt.v1"
EDGE_SCHEMA = "codex-ratchet.deep-stack-edge-receipt.v1"
ESTATE_SCHEMA = "codex-ratchet.deep-stack-estate-receipt.v1"
VERDICT_SCHEMA = "codex-ratchet.deep-stack-validation-verdict.v1"
REQUIRED_CASES = ("positive", "negative", "boundary", "stress")
REQUIRED_EVIDENCE_BOUNDARY = {
    "promotion_allowed": False,
    "scientific_claim_proven": False,
    "release_eligible": False,
    "lev_projection_only": True,
}
REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_DIR = REPO_ROOT / "system_v5/ops/tooling/deep_stack_stress_20260714/schemas"
SCHEMA_FILES = {
    ESTATE_SCHEMA: SCHEMA_DIR / "deep_stack_estate_receipt_v1.schema.json",
    TOOL_SCHEMA: SCHEMA_DIR / "deep_stack_tool_receipt_v1.schema.json",
    EDGE_SCHEMA: SCHEMA_DIR / "deep_stack_edge_receipt_v1.schema.json",
}
RAW_ROLES = {
    "python_core",
    "julia_core",
    "jl_tensorkit",
    "jl_pepskit",
    "jl_intervalarithmetic",
    "cross_tensor",
    "cross_dynamics",
}
MAPPED_TOOL_CLAIM_CEILING = (
    "One-to-one registry/source/output contract or exact structured artifact identity only; "
    "direct load-bearing API evidence remains in the raw four-case probe."
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalized_evidence_token(value: Any) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum())


def structured_tool_identities(value: Any) -> list[str]:
    identities: set[str] = set()
    scalar_keys = {"tool", "package", "target_tool", "tool_id"}
    list_keys = {"packages_used", "aligned_packages_load_bearing"}
    map_keys = {"TOOL_MANIFEST", "tool_manifest", "package_versions"}
    if isinstance(value, dict):
        for key, item in value.items():
            if key in scalar_keys and isinstance(item, str):
                identities.add(item)
            if key in list_keys and isinstance(item, list):
                identities.update(str(entry) for entry in item if isinstance(entry, str))
            if key in map_keys and isinstance(item, dict):
                identities.update(str(entry) for entry in item)
            identities.update(structured_tool_identities(item))
    elif isinstance(value, list):
        for item in value:
            identities.update(structured_tool_identities(item))
    return sorted(identities)


def raw_case(raw_row: dict[str, Any], name: str) -> dict[str, Any] | None:
    cases = raw_row.get("cases")
    if isinstance(cases, dict) and isinstance(cases.get(name), dict):
        return cases[name]
    value = raw_row.get(name)
    return value if isinstance(value, dict) else None


def raw_passed(value: Any) -> bool:
    return isinstance(value, dict) and value.get("passed", value.get("pass")) is True


def raw_qualified_apis(raw_row: dict[str, Any], fallback: str) -> list[str]:
    value = raw_row.get("qualified_api")
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list):
        result = [str(item) for item in value if str(item)]
        if result:
            return result
    calls = raw_row.get("tool_calls")
    if isinstance(calls, list):
        result = [
            str(item.get("qualified_api"))
            for item in calls
            if isinstance(item, dict) and item.get("qualified_api")
        ]
        if result:
            return result
    return [f"unresolved::{fallback}"]


def normalized_case_from_raw(
    raw: dict[str, Any] | None,
    name: str,
    api: str,
) -> dict[str, Any]:
    if raw is None:
        return {
            "passed": False,
            "qualified_api": api,
            "raw_case_sha256": None,
            "observed": {"missing_case": name},
            "error": "raw probe omitted case",
        }
    observation = raw.get("observed", raw.get("detail", raw.get("results")))
    return {
        "passed": raw_passed(raw),
        "qualified_api": api,
        "raw_case_sha256": canonical_json_sha256(raw),
        "observed": observation,
        "expected": raw.get("expected"),
        "error": raw.get("error"),
        "duration": raw.get("duration_seconds", raw.get("duration_ms")),
    }


def normalized_demotion_from_raw(raw_row: dict[str, Any]) -> dict[str, Any]:
    raw_demotion = raw_row.get("demotion")
    demotion = raw_demotion if isinstance(raw_demotion, dict) else None
    method = demotion.get("method") if demotion else None
    if not method:
        method = raw_row.get("demotion_condition")
    return {
        "passed": raw_passed(demotion),
        "method": method or "raw probe missing or red; operational label is demoted",
        "observed": demotion,
        "raw_demotion_sha256": canonical_json_sha256(demotion) if demotion is not None else None,
    }


def expected_normalized_tool_call(
    raw_call: dict[str, Any],
    *,
    cases: dict[str, Any],
    probe_source_sha256: str,
) -> dict[str, Any]:
    expected = copy.deepcopy(raw_call)
    expected["raw_call_sha256"] = canonical_json_sha256(raw_call)
    expected["executed"] = raw_call.get("executed") is True
    expected["load_bearing"] = raw_call.get("load_bearing") is True
    expected["raw_probe_recorded"] = raw_call.get("raw_probe_recorded") is True
    expected["case_bindings"] = {
        name: {
            "passed": case_passed(cases.get(name)),
            "qualified_api": expected.get("qualified_api"),
        }
        for name in REQUIRED_CASES
    }
    expected["probe_source_sha256"] = probe_source_sha256
    return expected


def parsed_stdout_receipt(command: dict[str, Any]) -> Any:
    stdout = str(command.get("stdout") or "").strip()
    if not stdout:
        return None
    for candidate in [stdout, *reversed(stdout.splitlines())]:
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
    return None


@lru_cache(maxsize=8)
def live_git_state(repo_root: str) -> tuple[str | None, str | None]:
    values: list[str | None] = []
    for revision in ("HEAD", "HEAD^{tree}"):
        try:
            result = subprocess.run(
                ["git", "-C", repo_root, "rev-parse", revision],
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            values.append(None)
            continue
        values.append(result.stdout.strip() if result.returncode == 0 else None)
    return values[0], values[1]


@lru_cache(maxsize=8)
def schema_validator(schema_id: str) -> Draft202012Validator:
    schema_path = SCHEMA_FILES[schema_id]
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def schema_instance_findings(
    instance: dict[str, Any],
    schema_id: str,
    label: str,
) -> list[str]:
    try:
        validator = schema_validator(schema_id)
    except (OSError, ValueError, KeyError) as exc:
        return [f"{label}: schema validator unavailable: {type(exc).__name__}: {exc}"]
    findings: list[str] = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        path = ".".join(str(item) for item in error.absolute_path) or "$"
        findings.append(f"{label}: schema instance violation at {path}: {error.message}")
    return findings


def contains_key_recursive(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(contains_key_recursive(item, key) for item in value.values())
    if isinstance(value, list):
        return any(contains_key_recursive(item, key) for item in value)
    return False


@lru_cache(maxsize=8)
def live_runtime_version(executable: str) -> str | None:
    try:
        result = subprocess.run(
            [executable, "--version"],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return (result.stdout + "\n" + result.stderr).strip()


def case_passed(value: Any) -> bool | None:
    if not isinstance(value, dict):
        return None
    passed = value.get("passed", value.get("pass"))
    return passed if isinstance(passed, bool) else None


def tool_findings(
    receipt: dict[str, Any],
    registry_row: dict[str, Any],
    edge_ids: set[str],
    *,
    repo_root: Path,
    commands: list[dict[str, Any]],
    expected_raw_row: dict[str, Any] | None,
    expected_source_tool_ids: list[str],
    verified_raw_output_paths: set[str],
    live_commit: str | None,
    live_tree: str | None,
    is_selftest: bool,
) -> list[str]:
    findings: list[str] = []
    tool_id = registry_row["tool_id"]
    prefix = f"{tool_id}: "

    if receipt.get("schema") != TOOL_SCHEMA:
        findings.append(prefix + f"schema must be {TOOL_SCHEMA}")
    for key in ("receipt_id", "run_id", "generated_at", "tool_id", "package", "bucket", "family", "runtime_binding", "source_binding", "verdict", "evidence_boundary"):
        if key not in receipt:
            findings.append(prefix + f"missing {key}")

    for key in ("tool_id", "package", "bucket", "family", "runtime_id"):
        observed = receipt.get(key)
        expected = registry_row.get(key)
        if observed != expected:
            findings.append(prefix + f"{key} mismatch: {observed!r} != {expected!r}")

    source = receipt.get("source_binding")
    if not isinstance(source, dict):
        findings.append(prefix + "source_binding must be an object")
        source = {}
    else:
        for key in ("registry_path", "registry_sha256", "runner_path", "runner_sha256", "probe_path", "probe_sha256", "ratchet_commit", "ratchet_tree"):
            if not source.get(key):
                findings.append(prefix + f"source_binding.{key} missing")
        for key in ("registry_sha256", "runner_sha256", "probe_sha256"):
            if source.get(key) and not is_sha256(source[key]):
                findings.append(prefix + f"source_binding.{key} is not sha256")
        for path_key, hash_key in (("registry_path", "registry_sha256"), ("runner_path", "runner_sha256"), ("probe_path", "probe_sha256")):
            raw_path = source.get(path_key)
            expected_hash = source.get(hash_key)
            if isinstance(raw_path, str) and expected_hash:
                path = Path(raw_path)
                path = path if path.is_absolute() else repo_root / path
                if not path.is_file():
                    findings.append(prefix + f"bound source absent: {raw_path}")
                elif sha256_file(path) != expected_hash:
                    findings.append(prefix + f"bound source hash mismatch: {raw_path}")
        if live_commit is not None and source.get("ratchet_commit") != live_commit:
            findings.append(prefix + "source_binding.ratchet_commit must match live git HEAD")
        if live_tree is not None and source.get("ratchet_tree") != live_tree:
            findings.append(prefix + "source_binding.ratchet_tree must match live git HEAD tree")
        support_sources = source.get("support_sources")
        if registry_row.get("runtime_id") == "python_canonical" and registry_row.get("requires_deep_stress") is True:
            if not isinstance(support_sources, list) or not support_sources:
                findings.append(prefix + "source_binding.support_sources must bind the Python probe support source")
        if support_sources is not None:
            if not isinstance(support_sources, list):
                findings.append(prefix + "source_binding.support_sources must be a list")
            else:
                for index, item in enumerate(support_sources):
                    if not isinstance(item, dict):
                        findings.append(prefix + f"source_binding.support_sources[{index}] must be an object")
                        continue
                    raw_path = item.get("path")
                    expected_hash = item.get("sha256")
                    if not isinstance(raw_path, str) or not raw_path:
                        findings.append(prefix + f"source_binding.support_sources[{index}].path missing")
                        continue
                    if not is_sha256(expected_hash):
                        findings.append(prefix + f"source_binding.support_sources[{index}].sha256 is not sha256")
                        continue
                    path = Path(raw_path)
                    path = path if path.is_absolute() else repo_root / path
                    if not path.is_file():
                        findings.append(prefix + f"bound support source absent: {raw_path}")
                    elif sha256_file(path) != expected_hash:
                        findings.append(prefix + f"bound support source hash mismatch: {raw_path}")
                    probe_hash = item.get("probe_sha256")
                    if not is_sha256(probe_hash) or probe_hash != expected_hash:
                        findings.append(prefix + f"source_binding.support_sources[{index}].probe_sha256 must equal live binding")
                    if item.get("hash_matches_probe") is not (probe_hash == expected_hash):
                        findings.append(prefix + f"source_binding.support_sources[{index}].hash_matches_probe is inconsistent")

    runtime = receipt.get("runtime_binding")
    if not isinstance(runtime, dict):
        findings.append(prefix + "runtime_binding must be an object")
    else:
        for key in ("runtime_id", "executable", "runtime_version", "environment_policy"):
            if key not in runtime:
                findings.append(prefix + f"runtime_binding.{key} missing")
        if runtime.get("runtime_id") != registry_row.get("runtime_id"):
            findings.append(prefix + "runtime_binding.runtime_id mismatch")
        if runtime.get("install_allowed") is not False:
            findings.append(prefix + "runtime_binding.install_allowed must be false")
        executable = runtime.get("executable")
        if isinstance(executable, str) and executable and not Path(executable).exists():
            findings.append(prefix + f"runtime executable absent: {executable}")
        elif isinstance(executable, str) and executable:
            resolved = str(Path(executable).resolve())
            if runtime.get("executable_realpath") != resolved:
                findings.append(prefix + "runtime executable_realpath mismatch")
            probe_realpath = runtime.get("probe_executable_realpath")
            if probe_realpath != resolved:
                findings.append(prefix + "probe executable realpath must equal live runtime")
            if runtime.get("executable_matches_probe") is not (probe_realpath == resolved):
                findings.append(prefix + "executable_matches_probe is inconsistent")
            executable_path = Path(executable)
            executable_realpath = Path(resolved)
            if not executable_path.is_file():
                findings.append(prefix + "runtime executable must be a regular file")
            else:
                if runtime.get("executable_sha256") != sha256_file(executable_path):
                    findings.append(prefix + "runtime executable_sha256 must match live launcher bytes")
                if runtime.get("executable_realpath_sha256") != sha256_file(executable_realpath):
                    findings.append(prefix + "runtime executable_realpath_sha256 must match live runtime bytes")
            probe_executable = runtime.get("probe_executable")
            if not isinstance(probe_executable, str) or not Path(probe_executable).is_file():
                findings.append(prefix + "probe executable must be a live regular file")
            else:
                probe_path = Path(probe_executable)
                probe_resolved = probe_path.resolve()
                if runtime.get("probe_executable_realpath") != str(probe_resolved):
                    findings.append(prefix + "probe executable realpath is not live-derived")
                if runtime.get("probe_executable_sha256") != sha256_file(probe_path):
                    findings.append(prefix + "probe executable sha256 mismatch")
                if runtime.get("probe_executable_realpath_sha256") != sha256_file(probe_resolved):
                    findings.append(prefix + "probe executable realpath sha256 mismatch")
                expected_hash_match = (
                    runtime.get("executable_realpath_sha256")
                    == runtime.get("probe_executable_realpath_sha256")
                )
                if runtime.get("executable_hash_matches_probe") is not expected_hash_match:
                    findings.append(prefix + "executable_hash_matches_probe is inconsistent")
            if not is_selftest:
                live_version = live_runtime_version(executable)
                version_token = str(runtime.get("runtime_version", "")).split()[0]
                if not live_version or not version_token or version_token not in live_version:
                    findings.append(prefix + "runtime_version does not match executable --version")
        if runtime.get("probe_runtime_version") != runtime.get("runtime_version"):
            findings.append(prefix + "probe_runtime_version must equal normalized runtime_version")
        if runtime.get("runtime_version_matches_probe") is not True:
            findings.append(prefix + "runtime_version_matches_probe must be true")
        if registry_row.get("requires_deep_stress") is True and str(registry_row.get("runtime_id", "")).startswith("julia_"):
            policy = runtime.get("environment_policy")
            if not isinstance(policy, dict):
                findings.append(prefix + "Julia environment_policy must be an object")
            else:
                for path_key, hash_key in (("project", "project_sha256"), ("manifest", "manifest_sha256")):
                    raw_path = policy.get(path_key)
                    expected_hash = policy.get(hash_key)
                    if not isinstance(raw_path, str) or not raw_path:
                        findings.append(prefix + f"runtime_binding.environment_policy.{path_key} missing")
                        continue
                    if not is_sha256(expected_hash):
                        findings.append(prefix + f"runtime_binding.environment_policy.{hash_key} is not sha256")
                        continue
                    path = Path(raw_path)
                    path = path if path.is_absolute() else repo_root / path
                    if not path.is_file():
                        findings.append(prefix + f"bound Julia runtime artifact absent: {raw_path}")
                    elif sha256_file(path) != expected_hash:
                        findings.append(prefix + f"bound Julia runtime artifact hash mismatch: {raw_path}")
                if policy.get("project_hash_matches_probe") is not True:
                    findings.append(prefix + "Julia project hash must match raw probe")
                if policy.get("manifest_hash_matches_probe") is not True:
                    findings.append(prefix + "Julia manifest hash must match raw probe")
                if policy.get("probe_project_sha256") != policy.get("project_sha256"):
                    findings.append(prefix + "Julia probe_project_sha256 must equal live project hash")
                if policy.get("probe_manifest_sha256") != policy.get("manifest_sha256"):
                    findings.append(prefix + "Julia probe_manifest_sha256 must equal live manifest hash")
                if policy.get("julia_load_path") != "@:@stdlib":
                    findings.append(prefix + "Julia load path must be strict @:@stdlib")
                if policy.get("julia_pkg_offline") is not True:
                    findings.append(prefix + "Julia package manager must be offline during stress execution")
                if policy.get("startup_file") is not False:
                    findings.append(prefix + "Julia startup_file must be false")

    evidence = receipt.get("evidence_boundary")
    if not isinstance(evidence, dict):
        findings.append(prefix + "evidence_boundary must be an object")
    else:
        for key, expected in REQUIRED_EVIDENCE_BOUNDARY.items():
            if evidence.get(key) is not expected:
                findings.append(prefix + f"evidence_boundary.{key} must be {expected!r}")
        if evidence.get("skill_guidance_max") != "L2":
            findings.append(prefix + "skill_guidance_max must be L2")
        if evidence.get("l4_earned") is not False:
            findings.append(prefix + "l4_earned must be false")

    verdict = receipt.get("verdict")
    if not isinstance(verdict, dict):
        findings.append(prefix + "verdict must be an object")
        return findings

    requires = registry_row.get("requires_deep_stress") is True
    if requires:
        cases = receipt.get("cases")
        if not isinstance(cases, dict):
            findings.append(prefix + "cases must be an object")
            cases = {}
        observed_case_passes: list[bool] = []
        for case_name in REQUIRED_CASES:
            value = cases.get(case_name)
            passed = case_passed(value)
            if passed is None:
                findings.append(prefix + f"cases.{case_name}.passed must be boolean")
            else:
                observed_case_passes.append(passed)
            if isinstance(value, dict):
                if not value.get("qualified_api") and not value.get("api"):
                    findings.append(prefix + f"cases.{case_name} missing qualified API")
                if "observed" not in value and "detail" not in value and "results" not in value:
                    findings.append(prefix + f"cases.{case_name} missing observation")

        if expected_raw_row is None and not is_selftest:
            findings.append(prefix + "required tool has no uniquely bound raw probe row")
        if isinstance(expected_raw_row, dict):
            expected_api = raw_qualified_apis(expected_raw_row, tool_id)[0]
            expected_cases = {
                name: normalized_case_from_raw(
                    raw_case(expected_raw_row, name),
                    name,
                    expected_api,
                )
                for name in REQUIRED_CASES
            }
            if cases != expected_cases:
                findings.append(prefix + "cases must exactly equal normalization of the bound raw row")

        demotion = receipt.get("demotion")
        demotion_pass = case_passed(demotion)
        if demotion_pass is None:
            findings.append(prefix + "demotion.passed must be boolean")
        elif not demotion.get("method"):
            findings.append(prefix + "demotion.method missing")
        if isinstance(expected_raw_row, dict):
            expected_demotion = normalized_demotion_from_raw(expected_raw_row)
            if demotion != expected_demotion:
                findings.append(prefix + "demotion must exactly equal normalization of the bound raw row")

        integrations = receipt.get("adjacent_integrations")
        declared = set(registry_row.get("integration_edge_ids", []))
        integration_passes: dict[str, bool] = {}
        if not isinstance(integrations, list) or not integrations:
            findings.append(prefix + "adjacent_integrations must be non-empty")
        else:
            seen: set[str] = set()
            for item in integrations:
                if not isinstance(item, dict):
                    findings.append(prefix + "adjacent integration entry must be an object")
                    continue
                edge_id = item.get("edge_id")
                if edge_id not in edge_ids:
                    findings.append(prefix + f"unknown integration edge {edge_id!r}")
                if edge_id not in declared:
                    findings.append(prefix + f"undeclared integration edge {edge_id!r}")
                if isinstance(edge_id, str):
                    seen.add(edge_id)
                if isinstance(edge_id, str):
                    integration_passes[edge_id] = case_passed(item) is True
            if declared - seen:
                findings.append(prefix + f"missing declared integration edges {sorted(declared - seen)}")
        integration_pass = bool(declared) and all(
            integration_passes.get(edge_id) is True for edge_id in declared
        )

        representative = receipt.get("representative_sim")
        representative_pass = case_passed(representative)
        if representative_pass is None:
            findings.append(prefix + "representative_sim.passed must be boolean")
        elif not isinstance(representative, dict) or not representative.get("source_path"):
            findings.append(prefix + "representative_sim.source_path missing")
        elif isinstance(representative, dict):
            source_path = representative.get("source_path")
            if source_path != registry_row.get("representative_sim", {}).get("path") and not is_selftest:
                findings.append(prefix + "representative_sim.source_path must match registry")
            source_hash = representative.get("source_sha256")
            if not is_sha256(source_hash):
                findings.append(prefix + "representative_sim.source_sha256 is not sha256")
            else:
                path = Path(source_path)
                path = path if path.is_absolute() else repo_root / path
                if not path.is_file():
                    findings.append(prefix + f"representative sim source absent: {source_path}")
                elif sha256_file(path) != source_hash:
                    findings.append(prefix + f"representative sim source hash mismatch: {source_path}")
            execution_modes = {
                "direct_current_probe",
                "controller_invoked_nested_fixture",
                "isolated_disposable_projection",
            }
            if representative.get("execution_mode") not in execution_modes:
                findings.append(prefix + "representative_sim.execution_mode is not an admitted execution mode")
            execution_source = representative.get("execution_source_path")
            execution_hash = representative.get("execution_source_sha256")
            if not isinstance(execution_source, str) or not execution_source:
                findings.append(prefix + "representative_sim.execution_source_path missing")
            elif not is_sha256(execution_hash):
                findings.append(prefix + "representative_sim.execution_source_sha256 is not sha256")
            else:
                path = Path(execution_source)
                path = path if path.is_absolute() else repo_root / path
                if not path.is_file():
                    findings.append(prefix + f"representative execution source absent: {execution_source}")
                elif sha256_file(path) != execution_hash:
                    findings.append(prefix + "representative execution source hash mismatch")
            rewrites = representative.get("source_rewrites")
            if not isinstance(rewrites, list):
                findings.append(prefix + "representative_sim.source_rewrites must be a list")
            elif not rewrites and is_sha256(source_hash) and execution_hash != source_hash:
                findings.append(prefix + "representative execution hash differs without a declared rewrite")
            if representative.get("executed") is not True:
                findings.append(prefix + "representative_sim.executed must be true")
            command = representative.get("command")
            if not isinstance(command, list) or not command:
                findings.append(prefix + "representative_sim.command must be a non-empty list")
            if not isinstance(representative.get("command_line"), str) or not representative.get("command_line"):
                findings.append(prefix + "representative_sim.command_line missing")
            elif isinstance(command, list) and representative.get("command_line") != shlex.join(command):
                findings.append(prefix + "representative_sim.command_line must exactly encode command")
            if representative.get("exit_code") != 0:
                findings.append(prefix + "representative_sim.exit_code must be zero")
            if representative.get("timed_out") is not False:
                findings.append(prefix + "representative_sim.timed_out must be false")
            exact_command_matches = [
                item
                for item in commands
                if (
                isinstance(item, dict)
                and item.get("command") == representative.get("command")
                and item.get("command_line") == representative.get("command_line")
                and item.get("exit_code") == representative.get("exit_code")
                and item.get("timed_out") == representative.get("timed_out")
                )
            ]
            if not is_selftest and not exact_command_matches:
                findings.append(prefix + "representative_sim command is not bound to estate.commands")
            matched_command = exact_command_matches[0] if exact_command_matches else None
            if isinstance(matched_command, dict):
                stdout_nonempty = bool(str(matched_command.get("stdout") or "").strip())
                if representative.get("stdout_nonempty") is not stdout_nonempty:
                    findings.append(prefix + "representative_sim.stdout_nonempty must match command stdout")
                if representative.get("stdout_receipt") != parsed_stdout_receipt(matched_command):
                    findings.append(prefix + "representative_sim.stdout_receipt must be parsed from command stdout")
            api_failures = representative.get("api_failure_signals")
            if not isinstance(api_failures, list):
                findings.append(prefix + "representative_sim.api_failure_signals must be a list")
            elif representative_pass is True and api_failures:
                findings.append(prefix + "passing representative_sim cannot carry API failure signals")
            artifacts = representative.get("emitted_artifacts")
            artifact_payloads: list[dict[str, Any]] = []
            if not isinstance(artifacts, list):
                findings.append(prefix + "representative_sim.emitted_artifacts must be a list")
                artifacts = []
            for index, artifact in enumerate(artifacts):
                if not isinstance(artifact, dict):
                    findings.append(prefix + f"representative_sim.emitted_artifacts[{index}] must be an object")
                    continue
                artifact_path = artifact.get("path")
                artifact_hash = artifact.get("sha256")
                if artifact.get("exists") is not True or artifact.get("changed_or_created") is not True:
                    findings.append(prefix + f"representative_sim.emitted_artifacts[{index}] must be fresh and present")
                if artifact.get("created_after_explicit_unlink") is not True:
                    findings.append(prefix + f"representative_sim.emitted_artifacts[{index}] must be created after explicit unlink")
                if not isinstance(artifact_path, str) or not artifact_path:
                    findings.append(prefix + f"representative_sim.emitted_artifacts[{index}].path missing")
                    continue
                path = Path(artifact_path)
                path = path if path.is_absolute() else repo_root / path
                if not path.is_file():
                    findings.append(prefix + f"representative artifact absent: {artifact_path}")
                elif not is_sha256(artifact_hash) or sha256_file(path) != artifact_hash:
                    findings.append(prefix + f"representative artifact hash mismatch: {artifact_path}")
                else:
                    if artifact.get("size") != path.stat().st_size:
                        findings.append(prefix + f"representative artifact size mismatch: {artifact_path}")
                if path.is_file() and path.suffix.lower() in {".json", ".jsonl"}:
                    try:
                        payload = load_json(path)
                        artifact_payloads.append(payload)
                        if artifact.get("json_object_parsed") is not True:
                            findings.append(prefix + f"representative_sim.emitted_artifacts[{index}].json_object_parsed must be true")
                    except (ValueError, json.JSONDecodeError, OSError):
                        findings.append(prefix + f"representative artifact is not parseable object JSON: {artifact_path}")
            if not isinstance(representative.get("stdout_nonempty"), bool):
                findings.append(prefix + "representative_sim.stdout_nonempty must be boolean")
            if not artifacts and representative.get("stdout_nonempty") is not True:
                findings.append(prefix + "representative_sim requires emitted artifact or stdout receipt")
            execution_mode = representative.get("execution_mode")
            invoked_source = representative.get("invoked_source_path")
            invoked_argument = representative.get("invoked_source_argument")
            invoked_hash = representative.get("invoked_source_sha256")
            if not isinstance(invoked_source, str) or not invoked_source:
                findings.append(prefix + "representative invoked_source_path missing")
            if not isinstance(invoked_argument, str) or invoked_argument not in (command or []):
                findings.append(prefix + "representative invoked source must be an exact command argument")
            if not is_sha256(invoked_hash):
                findings.append(prefix + "representative invoked_source_sha256 is not sha256")
            if representative.get("invoked_source_argument_present") is not True:
                findings.append(prefix + "representative invoked_source_argument_present must be true")
            if execution_mode == "isolated_disposable_projection":
                contracts = representative.get("output_contract_paths")
                emitted_contracts = representative.get("emitted_output_contract_paths")
                if not isinstance(contracts, list) or not contracts or len(contracts) != len(set(contracts)):
                    findings.append(prefix + "projection output_contract_paths must be a unique non-empty list")
                    contracts = []
                if emitted_contracts != sorted(contracts):
                    findings.append(prefix + "projection emitted output contracts must exactly match declaration")
                artifact_contracts = sorted(
                    artifact.get("projection_path")
                    for artifact in artifacts
                    if isinstance(artifact, dict) and isinstance(artifact.get("projection_path"), str)
                )
                if artifact_contracts != sorted(contracts) or len(artifacts) != len(contracts):
                    findings.append(prefix + "projection artifacts must exactly cover output contracts")
                if any(
                    not isinstance(artifact, dict)
                    or artifact.get("created_after_explicit_unlink") is not True
                    for artifact in artifacts
                ):
                    findings.append(prefix + "projection artifacts must be created after explicit unlink")
                if representative.get("output_contract_exact") is not True:
                    findings.append(prefix + "projection output_contract_exact must be true")
                if not isinstance(representative.get("preexisting_outputs_removed"), list):
                    findings.append(prefix + "projection preexisting_outputs_removed must be a list")
                if not is_sha256(invoked_hash) or invoked_hash != execution_hash:
                    findings.append(prefix + "projection invoked source hash must equal preserved execution source")
                if representative.get("invoked_source_matches_preserved") is not True:
                    findings.append(prefix + "projection invoked source must match preserved source")
                if isinstance(matched_command, dict):
                    for key in (
                        "invoked_source_path",
                        "invoked_source_argument",
                        "invoked_source_sha256",
                        "invoked_source_argument_present",
                        "output_contract_paths",
                        "emitted_output_contract_paths",
                        "output_contract_exact",
                        "invoked_source_matches_preserved",
                    ):
                        if matched_command.get(key) != representative.get(key):
                            findings.append(prefix + f"projection command {key} must match representative receipt")
                    if matched_command.get("outputs_created_after_explicit_unlink") is not True:
                        findings.append(prefix + "projection command must confirm fresh output creation")
            elif execution_mode in {"direct_current_probe", "controller_invoked_nested_fixture"}:
                contracts = representative.get("output_contract_paths")
                emitted_contracts = representative.get("emitted_output_contract_paths")
                artifact_paths_list = [
                    str(item.get("path"))
                    for item in artifacts
                    if isinstance(item, dict) and isinstance(item.get("path"), str)
                ]
                if not isinstance(contracts, list) or contracts != artifact_paths_list:
                    findings.append(prefix + "direct representative output contracts must exactly match artifacts")
                if emitted_contracts != artifact_paths_list:
                    findings.append(prefix + "direct representative emitted output contracts must exactly match artifacts")
                if representative.get("output_contract_exact") is not True:
                    findings.append(prefix + "direct representative output_contract_exact must be true")
                artifact_paths = {
                    str(item.get("path"))
                    for item in artifacts
                    if isinstance(item, dict) and isinstance(item.get("path"), str)
                }
                if verified_raw_output_paths and (
                    not artifact_paths or not artifact_paths.issubset(verified_raw_output_paths)
                ):
                    findings.append(prefix + "direct representative artifacts must bind verified fresh raw outputs")
            status = representative.get("reported_scientific_status")
            if not isinstance(status, dict) or status.get("state") not in {"green", "red", "unknown"}:
                findings.append(prefix + "representative_sim.reported_scientific_status.state invalid")
            if representative.get("scientific_status_preserved") is not True:
                findings.append(prefix + "representative_sim.scientific_status_preserved must be true")
            if representative.get("promotion_allowed") is not False:
                findings.append(prefix + "representative_sim.promotion_allowed must be false")
            if representative.get("scientific_claim_proven") is not False:
                findings.append(prefix + "representative_sim.scientific_claim_proven must be false")
            if representative.get("fixture_credit") != "representative_consumer_only_not_seven_case_replacement":
                findings.append(prefix + "representative_sim.fixture_credit must preserve the evidence ceiling")
            if representative.get("operational_execution_pass") is not representative_pass:
                findings.append(prefix + "representative_sim.operational_execution_pass must equal passed")
            mapping = representative.get("mapped_tool_evidence")
            aliases = sorted(
                {
                    str(value)
                    for value in (
                        registry_row.get("package"),
                        registry_row.get("import_name"),
                        str(registry_row.get("tool_id", "")).removeprefix("py_").removeprefix("jl_"),
                    )
                    if isinstance(value, str) and value
                }
            )
            stdout_value = representative.get("stdout_receipt")
            identities = structured_tool_identities(artifact_payloads)
            if stdout_value is not None:
                identities = sorted(set(identities) | set(structured_tool_identities(stdout_value)))
            normalized_aliases = {normalized_evidence_token(alias) for alias in aliases}
            matched_identities = [
                identity
                for identity in identities
                if normalized_evidence_token(identity) in normalized_aliases
            ]
            single_tool_source_contract = len(expected_source_tool_ids) == 1
            expected_mode = (
                "registry_single_tool_source_contract"
                if single_tool_source_contract
                else "structured_artifact_tool_identity"
            )
            mapped_pass = single_tool_source_contract or bool(matched_identities)
            if not isinstance(mapping, dict):
                findings.append(prefix + "representative_sim.mapped_tool_evidence must be an object")
            else:
                if mapping.get("mode") != expected_mode:
                    findings.append(prefix + "representative mapped-tool mode does not match source cardinality")
                if mapping.get("registry_tool_ids_for_source") != expected_source_tool_ids:
                    findings.append(prefix + "representative mapped-tool source IDs do not match registry")
                if mapping.get("registry_aliases") != aliases:
                    findings.append(prefix + "representative mapped-tool aliases do not match registry")
                if mapping.get("structured_artifact_identities") != identities:
                    findings.append(prefix + "representative structured artifact identities are not reproducible")
                if mapping.get("matched_structured_identities") != matched_identities:
                    findings.append(prefix + "representative structured identity matches are not exact")
                if mapping.get("passed") is not mapped_pass:
                    findings.append(prefix + "representative mapped-tool pass is inconsistent")
                if mapping.get("claim_ceiling") != MAPPED_TOOL_CLAIM_CEILING:
                    findings.append(prefix + "representative mapped-tool claim ceiling mismatch")
            mapped_ids = representative.get("mapped_tool_ids")
            if not isinstance(mapped_ids, list) or tool_id not in mapped_ids:
                findings.append(prefix + "representative mapped_tool_ids must include the receipt tool")
            if representative_pass is True and not mapped_pass:
                findings.append(prefix + "passing representative lacks tool-specific emitted evidence")

        calls = receipt.get("tool_calls")
        if not isinstance(calls, list) or not calls:
            findings.append(prefix + "tool_calls must be non-empty")
        else:
            for index, call in enumerate(calls):
                if not isinstance(call, dict) or not call.get("qualified_api"):
                    findings.append(prefix + f"tool_calls[{index}] missing qualified_api")
                if not isinstance(call, dict) or not call.get("input_object"):
                    findings.append(prefix + f"tool_calls[{index}] missing input_object")
                if not isinstance(call, dict) or not call.get("output_object"):
                    findings.append(prefix + f"tool_calls[{index}] missing output_object")
                if not isinstance(call, dict) or not call.get("gates"):
                    findings.append(prefix + f"tool_calls[{index}] missing gates")
                if not isinstance(call, dict) or call.get("executed") is not True:
                    findings.append(prefix + f"tool_calls[{index}].executed must be true")
                if not isinstance(call, dict) or call.get("load_bearing") is not True:
                    findings.append(prefix + f"tool_calls[{index}].load_bearing must be true")
                if not isinstance(call, dict) or call.get("raw_probe_recorded") is not True:
                    findings.append(prefix + f"tool_calls[{index}].raw_probe_recorded must be true")
                raw_call_hash = call.get("raw_call_sha256") if isinstance(call, dict) else None
                if not is_sha256(raw_call_hash):
                    findings.append(prefix + f"tool_calls[{index}].raw_call_sha256 is not sha256")
                if isinstance(call, dict) and call.get("probe_source_sha256") != source.get("probe_sha256"):
                    findings.append(prefix + f"tool_calls[{index}].probe_source_sha256 must match source binding")
                case_bindings = call.get("case_bindings") if isinstance(call, dict) else None
                if not isinstance(case_bindings, dict) or set(case_bindings) != set(REQUIRED_CASES):
                    findings.append(prefix + f"tool_calls[{index}].case_bindings must exactly cover four cases")
                elif any(
                    case_passed(case_bindings[name]) is not case_passed(cases.get(name))
                    for name in REQUIRED_CASES
                ):
                    findings.append(prefix + f"tool_calls[{index}].case_bindings must match normalized case verdicts")
                elif any(
                    case_bindings[name].get("qualified_api") != call.get("qualified_api")
                    for name in REQUIRED_CASES
                ):
                    findings.append(prefix + f"tool_calls[{index}].case_bindings must bind the exact recorded API")
            if isinstance(expected_raw_row, dict):
                raw_calls = expected_raw_row.get("tool_calls")
                if not isinstance(raw_calls, list):
                    raw_calls = []
                expected_calls = [
                    expected_normalized_tool_call(
                        raw_call,
                        cases=cases,
                        probe_source_sha256=str(source.get("probe_sha256")),
                    )
                    for raw_call in raw_calls
                    if isinstance(raw_call, dict)
                ]
                if calls != expected_calls:
                    findings.append(prefix + "tool_calls must exactly equal normalized bound raw calls")

        computed_pass = bool(
            len(observed_case_passes) == len(REQUIRED_CASES)
            and all(observed_case_passes)
            and demotion_pass is True
            and integration_pass
            and representative_pass is True
            and isinstance(calls, list)
            and bool(calls)
        )
        if verdict.get("operational_pass") is not computed_pass:
            findings.append(prefix + f"verdict.operational_pass must equal computed {computed_pass}")
        expected_status = "passed" if computed_pass else "red"
        if verdict.get("operational_status") != expected_status:
            findings.append(prefix + f"verdict.operational_status must be {expected_status}")
    else:
        policy = receipt.get("policy_check")
        policy_pass = case_passed(policy)
        if policy_pass is None:
            findings.append(prefix + "policy_check.passed must be boolean")
        expected_status = "policy_passed" if policy_pass is True else "policy_red"
        if verdict.get("operational_status") != expected_status:
            findings.append(prefix + f"policy verdict must be {expected_status}")
        if verdict.get("operational_pass") is not False:
            findings.append(prefix + "non-operational bucket cannot set operational_pass true")

    if verdict.get("receipt_valid") is not True:
        findings.append(prefix + "producer must mark receipt_valid true before independent validation")
    if receipt.get("classification") != "integration_diagnostic":
        findings.append(prefix + "classification must be integration_diagnostic")
    if receipt.get("promotion_allowed") is not False:
        findings.append(prefix + "promotion_allowed must be false")
    if receipt.get("scientific_claim_proven") is not False:
        findings.append(prefix + "scientific_claim_proven must be false")
    return findings


def edge_findings(receipt: dict[str, Any], edge_row: dict[str, Any], *, repo_root: Path) -> list[str]:
    findings: list[str] = []
    edge_id = edge_row["id"]
    prefix = f"edge {edge_id}: "
    if receipt.get("schema") != EDGE_SCHEMA:
        findings.append(prefix + f"schema must be {EDGE_SCHEMA}")
    if receipt.get("edge_id") != edge_id:
        findings.append(prefix + "edge_id mismatch")
    if receipt.get("family") != edge_row.get("family"):
        findings.append(prefix + "family mismatch")
    if receipt.get("case_id") != edge_row.get("case_id"):
        findings.append(prefix + "case_id mismatch")
    if receipt.get("members") != edge_row.get("members"):
        findings.append(prefix + "members must exactly preserve registry order")
    if receipt.get("declared_exchange") != edge_row.get("exchange"):
        findings.append(prefix + "declared_exchange must exactly preserve registry intent")
    if receipt.get("classification") != "integration_diagnostic":
        findings.append(prefix + "classification must be integration_diagnostic")
    if receipt.get("promotion_allowed") is not False:
        findings.append(prefix + "promotion_allowed must be false")
    if receipt.get("scientific_claim_proven") is not False:
        findings.append(prefix + "scientific_claim_proven must be false")
    if receipt.get("executed") is not True:
        findings.append(prefix + "executed must be true")
    expected_witness_modes = {
        "cross_jax_torch": "direct_value_handoff",
        "cross_proof": "independent_shared_obligation_crosscheck",
        "cross_tensor": "independent_shared_fixture_crosscheck",
        "cross_dynamics": "independent_shared_fixture_crosscheck",
    }
    expected_witness = expected_witness_modes.get(edge_id, "executed_member_case_conjunction")
    if receipt.get("witness_mode") != expected_witness:
        findings.append(prefix + f"witness_mode must be {expected_witness}")
    ceiling = receipt.get("exchange_claim_ceiling")
    if not isinstance(ceiling, str) or not ceiling:
        findings.append(prefix + "exchange_claim_ceiling missing")
    elif expected_witness == "executed_member_case_conjunction" and "does not assert a direct inter-member value handoff" not in ceiling:
        findings.append(prefix + "conjunction witness must explicitly disclaim direct value handoff")
    executed_exchange = receipt.get("exchange")
    if not isinstance(executed_exchange, str) or not executed_exchange:
        findings.append(prefix + "executed exchange description missing")
    elif expected_witness == "executed_member_case_conjunction" and "no direct inter-member value handoff is executed" not in executed_exchange:
        findings.append(prefix + "executed exchange must preserve conjunction-only ceiling")

    source_path = receipt.get("source_path")
    source_hash = receipt.get("source_sha256")
    if not isinstance(source_path, str) or not source_path:
        findings.append(prefix + "source_path missing")
    elif not is_sha256(source_hash):
        findings.append(prefix + "source_sha256 is not sha256")
    else:
        path = Path(source_path)
        path = path if path.is_absolute() else repo_root / path
        if not path.is_file():
            findings.append(prefix + f"source absent: {source_path}")
        elif sha256_file(path) != source_hash:
            findings.append(prefix + f"source hash mismatch: {source_path}")

    calls = receipt.get("qualified_api")
    if not isinstance(calls, list) or not calls or not all(isinstance(item, str) and item for item in calls):
        findings.append(prefix + "qualified_api must be a non-empty string list")
    for key in ("input_objects", "output_objects", "gates"):
        value = receipt.get(key)
        if not isinstance(value, list) or not value:
            findings.append(prefix + f"{key} must be non-empty")

    case_passes: list[bool] = []
    cases = receipt.get("cases")
    if not isinstance(cases, dict):
        findings.append(prefix + "cases must be an object")
        cases = {}
    for case_name in REQUIRED_CASES:
        case = cases.get(case_name)
        passed = case_passed(case)
        if passed is None:
            findings.append(prefix + f"cases.{case_name}.passed must be boolean")
        else:
            case_passes.append(passed)
        if not isinstance(case, dict) or (
            "observed" not in case and "detail" not in case and "results" not in case
        ):
            findings.append(prefix + f"cases.{case_name} missing observation")

    demotion = receipt.get("demotion")
    demotion_pass = case_passed(demotion)
    if demotion_pass is None:
        findings.append(prefix + "demotion.passed must be boolean")
    elif not isinstance(demotion, dict) or not demotion.get("method"):
        findings.append(prefix + "demotion.method missing")

    computed_pass = bool(
        len(case_passes) == len(REQUIRED_CASES)
        and all(case_passes)
        and demotion_pass is True
    )
    verdict = receipt.get("verdict")
    if not isinstance(verdict, dict):
        findings.append(prefix + "verdict must be an object")
    else:
        if verdict.get("operational_pass") is not computed_pass:
            findings.append(prefix + f"verdict.operational_pass must equal computed {computed_pass}")
        expected_status = "passed" if computed_pass else "red"
        if verdict.get("operational_status") != expected_status:
            findings.append(prefix + f"verdict.operational_status must be {expected_status}")
        if verdict.get("receipt_valid") is not True:
            findings.append(prefix + "producer must mark receipt_valid true")
    return findings


def command_findings(command: Any, index: int) -> list[str]:
    prefix = f"commands[{index}]: "
    findings: list[str] = []
    if not isinstance(command, dict):
        return [prefix + "command record must be an object"]
    argv = command.get("command")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
        return [prefix + "command must be a non-empty string list"]
    if command.get("command_line") != shlex.join(argv):
        findings.append(prefix + "command_line must exactly encode command")
    if command.get("exit_code") != 0:
        findings.append(prefix + "exit_code must be zero")
    if command.get("timed_out") is not False:
        findings.append(prefix + "timed_out must be false")
    launcher = Path(argv[0])
    launcher = launcher if launcher.is_absolute() else Path(command.get("process_launcher_path", argv[0]))
    if not launcher.is_file():
        findings.append(prefix + "process launcher is not a live regular file")
        return findings
    realpath = launcher.resolve()
    expected = {
        "process_launcher_path": str(launcher),
        "process_launcher_realpath": str(realpath),
        "process_launcher_sha256": sha256_file(launcher),
        "process_launcher_realpath_sha256": sha256_file(realpath),
    }
    for key, value in expected.items():
        if command.get(key) != value:
            findings.append(prefix + f"{key} does not match live launcher provenance")
    return findings


def raw_binding_and_producer_findings(
    *,
    estate: dict[str, Any],
    commands: list[dict[str, Any]],
    repo_root: Path,
    is_selftest: bool,
) -> tuple[list[str], list[str], set[str]]:
    findings: list[str] = []
    missing_roles: list[str] = []
    verified_paths: set[str] = set()
    if is_selftest:
        return findings, missing_roles, verified_paths

    raw_paths: list[str] = []

    def collect_paths(value: Any) -> None:
        if isinstance(value, str):
            raw_paths.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                collect_paths(item)
        elif isinstance(value, list):
            for item in value:
                collect_paths(item)

    collect_paths(estate.get("raw_receipts"))
    run_id = estate.get("run_id")
    if len(raw_paths) != 7 or len(set(raw_paths)) != 7:
        findings.append(f"raw_receipts must contain exactly seven unique paths, got {len(raw_paths)}")
    for raw_path in raw_paths:
        if f"/raw/{run_id}/" not in "/" + raw_path:
            findings.append(f"raw receipt is not run-scoped: {raw_path}")

    raw_bindings = estate.get("raw_receipt_bindings")
    if not isinstance(raw_bindings, list):
        return findings + ["raw_receipt_bindings must be a list"], sorted(RAW_ROLES), verified_paths
    roles = [item.get("role") for item in raw_bindings if isinstance(item, dict)]
    if len(roles) != len(set(roles)):
        findings.append("raw_receipt_bindings roles are duplicated")
    if set(roles) != RAW_ROLES:
        findings.append("raw_receipt_bindings must exactly cover seven execution roles")
    bindings_by_role = {
        item["role"]: item
        for item in raw_bindings
        if isinstance(item, dict) and item.get("role") in RAW_ROLES
    }
    if {item.get("path") for item in bindings_by_role.values()} != set(raw_paths):
        findings.append("raw receipt bindings must exactly match raw_receipts paths")

    producers_by_role: dict[str, list[dict[str, Any]]] = {role: [] for role in RAW_ROLES}
    for command in commands:
        if isinstance(command, dict) and command.get("role") == "raw_producer":
            role = command.get("raw_role")
            if role in producers_by_role:
                producers_by_role[role].append(command)
            else:
                findings.append(f"raw producer command has unknown role {role!r}")

    for role in sorted(RAW_ROLES):
        binding = bindings_by_role.get(role)
        if not isinstance(binding, dict):
            missing_roles.append(role)
            continue
        raw_path = binding.get("path")
        expected_hash = binding.get("sha256")
        if not isinstance(raw_path, str) or not raw_path:
            findings.append(f"raw receipt binding {role} path missing")
            missing_roles.append(role)
            continue
        path = Path(raw_path)
        path = path if path.is_absolute() else repo_root / path
        if binding.get("exists") is not True or not path.is_file():
            findings.append(f"raw receipt binding {role} is not live")
            missing_roles.append(role)
            continue
        if not is_sha256(expected_hash) or sha256_file(path) != expected_hash:
            findings.append(f"raw receipt binding {role} hash mismatch")
            continue
        producers = producers_by_role[role]
        if len(producers) != 1:
            findings.append(f"raw role {role} must have exactly one producer command")
            continue
        producer = producers[0]
        if producer.get("output_path") != raw_path:
            findings.append(f"raw producer {role} output_path must equal binding path")
        if producer.get("output_exists") is not True:
            findings.append(f"raw producer {role} output_exists must be true")
        if producer.get("output_sha256") != expected_hash:
            findings.append(f"raw producer {role} output hash must equal binding hash")
        if producer.get("output_created_after_explicit_unlink") is not True:
            findings.append(f"raw producer {role} must create output after explicit unlink")
        if producer.get("output_boundary_cleared_before_execution") is not True:
            findings.append(f"raw producer {role} must clear output boundary before execution")
        if "preexisting_output_removed" not in producer:
            findings.append(f"raw producer {role} must report preexisting output disposition")
        invoked_path = producer.get("invoked_source_path")
        invoked_argument = producer.get("invoked_source_argument")
        invoked_hash = producer.get("invoked_source_sha256")
        if not isinstance(invoked_path, str) or not invoked_path:
            findings.append(f"raw producer {role} invoked_source_path missing")
        else:
            source = Path(invoked_path)
            source = source if source.is_absolute() else repo_root / source
            if not source.is_file() or not is_sha256(invoked_hash) or sha256_file(source) != invoked_hash:
                findings.append(f"raw producer {role} invoked source hash mismatch")
        if not isinstance(invoked_argument, str) or invoked_argument not in producer.get("command", []):
            findings.append(f"raw producer {role} invoked source must be an exact command argument")
        if producer.get("invoked_source_argument_present") is not True:
            findings.append(f"raw producer {role} invoked_source_argument_present must be true")
        expected_binding_fields = {
            "producer_command_count": 1,
            "producer_bound": True,
            "producer_exit_code": 0,
            "producer_timed_out": False,
            "producer_output_path": raw_path,
            "producer_output_sha256": expected_hash,
            "producer_output_created_after_explicit_unlink": True,
            "producer_output_boundary_cleared_before_execution": True,
            "producer_invoked_source_path": invoked_path,
            "producer_invoked_source_sha256": invoked_hash,
            "producer_invoked_source_argument_present": True,
        }
        for key, expected in expected_binding_fields.items():
            if binding.get(key) != expected:
                findings.append(f"raw receipt binding {role} {key} mismatch")
        if not any(finding.startswith(f"raw producer {role}") for finding in findings):
            verified_paths.add(raw_path)
    return findings, sorted(set(missing_roles)), verified_paths


def source_state_findings(
    *,
    estate: dict[str, Any],
    repo_root: Path,
    registry_path: Path | None,
    edges_path: Path | None,
    is_selftest: bool,
) -> tuple[list[str], str | None, str | None]:
    if is_selftest:
        return [], None, None
    findings: list[str] = []
    state = estate.get("source_state")
    if not isinstance(state, dict):
        return ["source_state must be an object"], None, None
    live_commit, live_tree = live_git_state(str(repo_root))
    if live_commit is None or live_tree is None:
        findings.append("source_state cannot resolve live git HEAD and tree")
    if state.get("ratchet_commit") != live_commit:
        findings.append("source_state.ratchet_commit must match live git HEAD")
    if state.get("ratchet_tree") != live_tree:
        findings.append("source_state.ratchet_tree must match live git HEAD tree")
    runner_path = state.get("runner_path")
    runner = Path(runner_path) if isinstance(runner_path, str) else Path()
    runner = runner if runner.is_absolute() else repo_root / runner
    if not isinstance(runner_path, str) or not runner.is_file():
        findings.append("source_state.runner_path must be a live file")
    elif state.get("runner_sha256") != sha256_file(runner):
        findings.append("source_state.runner_sha256 mismatch")
    for label, path in (("registry", registry_path), ("edges", edges_path)):
        if path is None or not path.is_file():
            findings.append(f"source_state {label} validation path missing")
        elif state.get(f"{label}_sha256") != sha256_file(path):
            findings.append(f"source_state.{label}_sha256 mismatch")
    julia_root = repo_root / "system_v5/julia_carrier"
    for filename, key in (
        ("Project.toml", "julia_carrier_project_sha256"),
        ("Manifest.toml", "julia_carrier_manifest_sha256"),
    ):
        path = julia_root / filename
        if not path.is_file() or state.get(key) != sha256_file(path):
            findings.append(f"source_state.{key} mismatch")
    return findings, live_commit, live_tree


def validate_estate(
    estate: dict[str, Any],
    registry: dict[str, Any],
    edges: dict[str, Any],
    *,
    repo_root: Path,
    registry_path: Path | None = None,
    edges_path: Path | None = None,
    selftest_mode: bool = False,
) -> dict[str, Any]:
    findings: list[str] = []
    if estate.get("schema") != ESTATE_SCHEMA:
        findings.append(f"schema must be {ESTATE_SCHEMA}")
    if estate.get("classification") != "integration_diagnostic":
        findings.append("classification must be integration_diagnostic")
    if estate.get("promotion_allowed") is not False:
        findings.append("promotion_allowed must be false")
    if estate.get("scientific_claim_proven") is not False:
        findings.append("scientific_claim_proven must be false")
    if estate.get("claude_bridge_used") is not False:
        findings.append("claude_bridge_used must be false")
    if not isinstance(estate.get("run_id"), str) or not estate.get("run_id"):
        findings.append("run_id must be a non-empty string")
    if not isinstance(estate.get("generated_at"), str) or not estate.get("generated_at"):
        findings.append("generated_at must be a non-empty string")
    if estate.get("release_eligible") is not False:
        findings.append("release_eligible must be false")
    if estate.get("install_attempted") is not False:
        findings.append("install_attempted must be false")
    if not isinstance(estate.get("raw_reuse_used"), bool):
        findings.append("raw_reuse_used must be boolean")

    registry_rows = {row["tool_id"]: copy.deepcopy(row) for row in registry.get("tools", [])}
    is_selftest = selftest_mode
    production_checks = not is_selftest or estate.get("_exercise_production_gates") is True
    provenance_findings, live_commit, live_tree = source_state_findings(
        estate=estate,
        repo_root=repo_root,
        registry_path=registry_path,
        edges_path=edges_path,
        is_selftest=is_selftest,
    )
    findings.extend(provenance_findings)
    edge_rows = {row["id"]: row for row in edges.get("edges", [])}
    if not is_selftest:
        findings.extend(schema_instance_findings(estate, ESTATE_SCHEMA, "estate"))
    edge_ids = set(edge_rows)
    for edge_id, edge_row in edge_rows.items():
        for member in edge_row.get("members", []):
            if member not in registry_rows:
                findings.append(f"integration edge {edge_id} names unknown member {member!r}")
                continue
            declared = registry_rows[member].setdefault("integration_edge_ids", [])
            if edge_id not in declared:
                declared.append(edge_id)
    receipts = estate.get("tool_receipts")
    if not isinstance(receipts, list):
        receipts = []
        findings.append("tool_receipts must be a list")

    receipt_rows: dict[str, dict[str, Any]] = {}
    duplicates: set[str] = set()
    for receipt in receipts:
        if not isinstance(receipt, dict):
            findings.append("tool receipt entry must be an object")
            continue
        tool_id = receipt.get("tool_id")
        if not isinstance(tool_id, str):
            findings.append("tool receipt missing tool_id")
            continue
        if tool_id in receipt_rows:
            duplicates.add(tool_id)
        receipt_rows[tool_id] = receipt
        if receipt.get("run_id") != estate.get("run_id"):
            findings.append(f"{tool_id}: run_id must match estate run_id")
        if receipt.get("receipt_id") != f"{estate.get('run_id')}:{tool_id}":
            findings.append(f"{tool_id}: receipt_id must bind estate run_id and tool_id")
    if duplicates:
        findings.append(f"duplicate tool ids: {sorted(duplicates)}")

    missing = sorted(set(registry_rows) - set(receipt_rows))
    extra = sorted(set(receipt_rows) - set(registry_rows))
    if missing:
        findings.append(f"missing registry rows: {missing}")
    if extra:
        findings.append(f"unknown receipt rows: {extra}")

    representative_executions = estate.get("representative_execution_receipts")
    if not isinstance(representative_executions, list):
        representative_executions = []
        if not is_selftest:
            findings.append("representative_execution_receipts must be a list")
    if production_checks:
        expected_sources = {
            row.get("representative_sim", {}).get("path")
            for row in registry_rows.values()
            if row.get("requires_deep_stress") is True
        }
        observed_sources = {
            item.get("source_path")
            for item in representative_executions
            if isinstance(item, dict)
        }
        if observed_sources != expected_sources:
            findings.append("representative_execution_receipts source coverage must exactly match registry")
        for tool_id, row in registry_rows.items():
            if row.get("requires_deep_stress") is not True:
                continue
            source_path = row.get("representative_sim", {}).get("path")
            if not any(
                isinstance(item, dict)
                and item.get("source_path") == source_path
                and (
                    item.get("tool_id") == tool_id
                    or tool_id in item.get("mapped_tool_ids", [])
                )
                for item in representative_executions
            ):
                findings.append(f"{tool_id}: missing representative execution index entry")

    commands = estate.get("commands")
    if not isinstance(commands, list):
        commands = []
        findings.append("commands must be a list")
    for index, command in enumerate(commands):
        findings.extend(command_findings(command, index))

    raw_rows_by_tool: dict[str, dict[str, Any]] = {}
    if production_checks:
        raw_strings: list[str] = []

        def collect_raw_strings(value: Any) -> None:
            if isinstance(value, str):
                raw_strings.append(value)
            elif isinstance(value, dict):
                for item in value.values():
                    collect_raw_strings(item)
            elif isinstance(value, list):
                for item in value:
                    collect_raw_strings(item)

        collect_raw_strings(estate.get("raw_receipts"))
        registry_by_package = {
            row.get("package"): tool_id for tool_id, row in registry_rows.items() if row.get("package")
        }
        registry_by_import = {
            row.get("import_name"): tool_id for tool_id, row in registry_rows.items() if row.get("import_name")
        }
        for raw_string in raw_strings:
            raw_path = Path(raw_string)
            raw_path = raw_path if raw_path.is_absolute() else repo_root / raw_path
            if not raw_path.is_file():
                continue
            try:
                payload = load_json(raw_path)
            except (ValueError, json.JSONDecodeError, OSError):
                continue
            rows: list[dict[str, Any]] = []
            for key in ("rows", "support_rows"):
                value = payload.get(key)
                if isinstance(value, list):
                    rows.extend(item for item in value if isinstance(item, dict))
            for raw_row in rows:
                raw_name = raw_row.get("tool", raw_row.get("package"))
                tool_id = registry_by_package.get(raw_name) or registry_by_import.get(raw_name)
                if not tool_id:
                    continue
                if tool_id in raw_rows_by_tool:
                    findings.append(f"{tool_id}: duplicate raw probe rows")
                    continue
                raw_rows_by_tool[tool_id] = raw_row

    raw_findings, missing_raw_roles, verified_raw_output_paths = raw_binding_and_producer_findings(
        estate=estate,
        commands=commands,
        repo_root=repo_root,
        is_selftest=not production_checks,
    )
    findings.extend(raw_findings)
    source_tool_ids_by_path: dict[str, list[str]] = {}
    for tool_id, row in registry_rows.items():
        if row.get("requires_deep_stress") is not True:
            continue
        source_path = row.get("representative_sim", {}).get("path")
        if isinstance(source_path, str):
            source_tool_ids_by_path.setdefault(source_path, []).append(tool_id)
    for tool_ids in source_tool_ids_by_path.values():
        tool_ids.sort()

    per_tool: dict[str, list[str]] = {}
    for tool_id in sorted(set(registry_rows) & set(receipt_rows)):
        row = registry_rows[tool_id]
        source_path = row.get("representative_sim", {}).get("path")
        row_findings = tool_findings(
            receipt_rows[tool_id],
            row,
            edge_ids,
            repo_root=repo_root,
            commands=commands,
            expected_raw_row=None if not production_checks else raw_rows_by_tool.get(tool_id),
            expected_source_tool_ids=source_tool_ids_by_path.get(source_path, [tool_id]),
            verified_raw_output_paths=verified_raw_output_paths,
            live_commit=live_commit,
            live_tree=live_tree,
            is_selftest=is_selftest,
        )
        if not is_selftest:
            findings.extend(schema_instance_findings(receipt_rows[tool_id], TOOL_SCHEMA, f"{tool_id} tool receipt"))
        if row_findings:
            per_tool[tool_id] = row_findings
            findings.extend(row_findings)

    raw_edge_receipts = estate.get("integration_edge_receipts")
    if not isinstance(raw_edge_receipts, list):
        raw_edge_receipts = []
        findings.append("integration_edge_receipts must be a list")
    edge_receipts: dict[str, dict[str, Any]] = {}
    duplicate_edges: set[str] = set()
    for receipt in raw_edge_receipts:
        if not isinstance(receipt, dict) or not isinstance(receipt.get("edge_id"), str):
            findings.append("integration edge receipt missing edge_id")
            continue
        edge_id = receipt["edge_id"]
        if edge_id in edge_receipts:
            duplicate_edges.add(edge_id)
        edge_receipts[edge_id] = receipt
    if duplicate_edges:
        findings.append(f"duplicate edge ids: {sorted(duplicate_edges)}")
    missing_edges = sorted(edge_ids - set(edge_receipts))
    extra_edges = sorted(set(edge_receipts) - edge_ids)
    if missing_edges:
        findings.append(f"missing integration edge receipts: {missing_edges}")
    if extra_edges:
        findings.append(f"unknown integration edge receipts: {extra_edges}")
    for edge_id in sorted(edge_ids & set(edge_receipts)):
        if not is_selftest:
            findings.extend(schema_instance_findings(edge_receipts[edge_id], EDGE_SCHEMA, f"{edge_id} edge receipt"))
        findings.extend(edge_findings(edge_receipts[edge_id], edge_rows[edge_id], repo_root=repo_root))

    reused_command_count = sum(
        isinstance(command, dict)
        and (
            contains_key_recursive(command, "reused_raw")
            or "--reuse-raw" in json.dumps(command, sort_keys=True)
        )
        for command in commands
    )
    if production_checks and len(commands) < 10:
        findings.append("commands must preserve every parent-runner execution record")
    if estate.get("raw_reuse_used") is False and reused_command_count:
        findings.append("raw_reuse_used=false contradicts reused_raw command records")
    if estate.get("raw_reuse_used") is True and reused_command_count == 0:
        findings.append("raw_reuse_used=true requires reused_raw command records")

    required = [
        row["tool_id"]
        for row in registry_rows.values()
        if row.get("bucket") in set(registry.get("required_operational_buckets", []))
        and row.get("requires_deep_stress") is True
    ]
    operational_red = sorted(
        tool_id for tool_id in required
        if receipt_rows.get(tool_id, {}).get("verdict", {}).get("operational_pass") is not True
    )
    policy_red = sorted(
        tool_id for tool_id, row in registry_rows.items()
        if row.get("requires_deep_stress") is not True
        and receipt_rows.get(tool_id, {}).get("policy_check", {}).get("passed") is not True
    )
    operational_edge_red = sorted(
        edge_id for edge_id in edge_ids
        if edge_receipts.get(edge_id, {}).get("verdict", {}).get("operational_pass") is not True
    )

    raw_reuse_used = estate.get("raw_reuse_used") is True
    def command_signature(value: dict[str, Any]) -> tuple[str, Any, Any, Any]:
        return (
            json.dumps(value.get("command"), sort_keys=True),
            value.get("command_line"),
            value.get("exit_code"),
            value.get("timed_out"),
        )

    representative_by_signature: dict[tuple[str, Any, Any, Any], dict[str, Any]] = {}
    for receipt in receipt_rows.values():
        representative = receipt.get("representative_sim")
        if isinstance(representative, dict) and isinstance(representative.get("command"), list):
            representative_by_signature[command_signature(representative)] = representative
    for command in commands:
        if not isinstance(command, dict) or command.get("role") != "representative_sim":
            continue
        if command_signature(command) not in representative_by_signature:
            findings.append("representative_sim command record is not referenced by any tool receipt")

    failed_command_count = sum(
        1
        for command in commands
        if not isinstance(command, dict)
        or command.get("exit_code") != 0
        or command.get("timed_out") is not False
    )
    accepted_scientific_red_command_count = 0

    valid = not findings
    operational_pass = bool(
        valid
        and not operational_red
        and not operational_edge_red
        and not policy_red
        and not raw_reuse_used
        and not missing_raw_roles
        and failed_command_count == 0
    )
    summary = {
        "registry_tool_count": len(registry_rows),
        "receipt_tool_count": len(receipt_rows),
        "required_operational_count": len(required),
        "operational_pass_count": len(required) - len(operational_red),
        "operational_red_count": len(operational_red),
        "policy_red_count": len(policy_red),
        "integration_edge_count": len(edge_ids),
        "integration_edge_red_count": len(operational_edge_red),
        "finding_count": len(findings),
        "raw_reuse_used": raw_reuse_used,
        "reused_command_count": reused_command_count,
        "missing_raw_receipt_count": len(missing_raw_roles),
        "failed_command_count": failed_command_count,
        "accepted_scientific_red_command_count": accepted_scientific_red_command_count,
    }
    return {
        "schema": VERDICT_SCHEMA,
        "receipt_valid": valid,
        "operational_pass": operational_pass,
        "release_eligible": False,
        "projection_only": True,
        "scientific_claim_proven": False,
        "summary": summary,
        "operational_red_tools": operational_red,
        "policy_red_tools": policy_red,
        "operational_red_edges": operational_edge_red,
        "missing_raw_receipt_roles": sorted(missing_raw_roles),
        "findings": findings,
        "per_tool_findings": per_tool,
    }


def minimal_selftest_fixture() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    registry_row = {
        "tool_id": "fixture",
        "package": "fixture",
        "bucket": "current_core",
        "family": "fixture",
        "runtime_id": "python_canonical",
        "requires_deep_stress": True,
        "integration_edge_ids": ["edge"],
        "_selftest_fixture": True,
    }
    registry = {
        "required_operational_buckets": ["current_core"],
        "tools": [registry_row],
    }
    edges = {
        "edges": [
            {
                "id": "edge",
                "family": "fixture",
                "case_id": "fixture_edge",
                "members": ["fixture"],
                "exchange": "fixture intended exchange",
            }
        ]
    }
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for name in ("registry.json", "runner.py", "probe.py", "support.py", "artifact.json"):
            (root / name).write_text(name + "\n", encoding="utf-8")
        (root / "artifact.json").write_text('{"tool":"fixture"}\n', encoding="utf-8")
        launcher = Path("/usr/bin/true")
        launcher_realpath = launcher.resolve()
        launcher_provenance = {
            "process_launcher_path": str(launcher),
            "process_launcher_realpath": str(launcher_realpath),
            "process_launcher_sha256": sha256_file(launcher),
            "process_launcher_realpath_sha256": sha256_file(launcher_realpath),
        }
        source = {
            "registry_path": "registry.json",
            "registry_sha256": sha256_file(root / "registry.json"),
            "runner_path": "runner.py",
            "runner_sha256": sha256_file(root / "runner.py"),
            "probe_path": "probe.py",
            "probe_sha256": sha256_file(root / "probe.py"),
            "ratchet_commit": "a" * 40,
            "ratchet_tree": "b" * 40,
            "support_sources": [
                {
                    "path": "support.py",
                    "sha256": sha256_file(root / "support.py"),
                    "probe_sha256": sha256_file(root / "support.py"),
                    "hash_matches_probe": True,
                    "role": "fixture support source",
                }
            ],
        }
        case = {"passed": True, "qualified_api": "fixture.api", "observed": "ok"}
        receipt = {
            "schema": TOOL_SCHEMA,
            "receipt_id": "fixture-run:fixture",
            "run_id": "fixture-run",
            "generated_at": "2026-07-14T00:00:00Z",
            "tool_id": "fixture",
            "package": "fixture",
            "bucket": "current_core",
            "family": "fixture",
            "runtime_id": "python_canonical",
            "classification": "integration_diagnostic",
            "promotion_allowed": False,
            "scientific_claim_proven": False,
            "source_binding": source,
            "runtime_binding": {
                "runtime_id": "python_canonical",
                "executable": "/usr/bin/true",
                "executable_realpath": str(launcher_realpath),
                "executable_sha256": sha256_file(launcher),
                "executable_realpath_sha256": sha256_file(launcher_realpath),
                "probe_executable": "/usr/bin/true",
                "probe_executable_realpath": str(launcher_realpath),
                "probe_executable_sha256": sha256_file(launcher),
                "probe_executable_realpath_sha256": sha256_file(launcher_realpath),
                "executable_matches_probe": True,
                "executable_hash_matches_probe": True,
                "runtime_version": "test",
                "probe_runtime_version": "test",
                "runtime_version_matches_probe": True,
                "environment_policy": {},
                "install_allowed": False,
            },
            "cases": {name: copy.deepcopy(case) for name in REQUIRED_CASES},
            "demotion": {"passed": True, "method": "stub"},
            "adjacent_integrations": [{"edge_id": "edge", "passed": True}],
            "representative_sim": {
                "source_path": "probe.py",
                "source_sha256": sha256_file(root / "probe.py"),
                "execution_source_path": "probe.py",
                "execution_source_sha256": sha256_file(root / "probe.py"),
                "invoked_source_path": "probe.py",
                "invoked_source_argument": "/usr/bin/true",
                "invoked_source_sha256": sha256_file(root / "probe.py"),
                "invoked_source_argument_present": True,
                "source_rewrites": [],
                "executed": True,
                "execution_mode": "direct_current_probe",
                "command": ["/usr/bin/true"],
                "command_line": "/usr/bin/true",
                "exit_code": 0,
                "timed_out": False,
                "stdout_nonempty": False,
                "stdout_receipt": None,
                "api_failure_signals": [],
                "emitted_artifacts": [
                    {
                        "path": "artifact.json",
                        "exists": True,
                        "changed_or_created": True,
                        "created_after_explicit_unlink": True,
                        "sha256": sha256_file(root / "artifact.json"),
                        "size": (root / "artifact.json").stat().st_size,
                        "json_object_parsed": True,
                    }
                ],
                "output_contract_paths": ["artifact.json"],
                "emitted_output_contract_paths": ["artifact.json"],
                "output_contract_exact": True,
                "reported_scientific_status": {"state": "unknown"},
                "scientific_status_preserved": True,
                "promotion_allowed": False,
                "scientific_claim_proven": False,
                "operational_execution_pass": True,
                "passed": True,
                "fixture_credit": "representative_consumer_only_not_seven_case_replacement",
                "mapped_tool_ids": ["fixture"],
                "tool_id": "fixture",
                "mapped_tool_evidence": {
                    "mode": "registry_single_tool_source_contract",
                    "registry_tool_ids_for_source": ["fixture"],
                    "registry_aliases": ["fixture"],
                    "structured_artifact_identities": ["fixture"],
                    "matched_structured_identities": ["fixture"],
                    "passed": True,
                    "claim_ceiling": MAPPED_TOOL_CLAIM_CEILING,
                },
            },
            "tool_calls": [
                {
                    "qualified_api": "fixture.api",
                    "input_object": "x",
                    "output_object": "y",
                    "gates": ["positive"],
                    "executed": True,
                    "load_bearing": True,
                    "raw_probe_recorded": True,
                    "raw_call_sha256": "c" * 64,
                    "probe_source_sha256": source["probe_sha256"],
                    "case_bindings": {name: copy.deepcopy(case) for name in REQUIRED_CASES},
                }
            ],
            "verdict": {"receipt_valid": True, "operational_status": "passed", "operational_pass": True},
            "evidence_boundary": {
                "skill_guidance_max": "L2",
                "promotion_allowed": False,
                "scientific_claim_proven": False,
                "release_eligible": False,
                "lev_projection_only": True,
                "l4_earned": False,
            },
        }
        estate = {
            "schema": ESTATE_SCHEMA,
            "run_id": "fixture-run",
            "generated_at": "2026-07-14T00:00:00Z",
            "classification": "integration_diagnostic",
            "promotion_allowed": False,
            "scientific_claim_proven": False,
            "release_eligible": False,
            "claude_bridge_used": False,
            "install_attempted": False,
            "raw_reuse_used": False,
            "commands": [
                {
                    "command": ["/usr/bin/true"],
                    "command_line": "/usr/bin/true",
                    "exit_code": 0,
                    "timed_out": False,
                    **launcher_provenance,
                }
            ],
            "raw_receipts": {},
            "raw_receipt_bindings": [],
            "representative_execution_receipts": [copy.deepcopy(receipt["representative_sim"])],
            "tool_receipts": [receipt],
            "integration_edge_receipts": [
                {
                    "schema": EDGE_SCHEMA,
                    "edge_id": "edge",
                    "family": "fixture",
                    "case_id": "fixture_edge",
                    "members": ["fixture"],
                    "declared_exchange": "fixture intended exchange",
                    "exchange": "Exact members execute fixture cases; no direct inter-member value handoff is executed.",
                    "classification": "integration_diagnostic",
                    "promotion_allowed": False,
                    "scientific_claim_proven": False,
                    "executed": True,
                    "witness_mode": "executed_member_case_conjunction",
                    "exchange_claim_ceiling": "This receipt does not assert a direct inter-member value handoff.",
                    "source_path": "probe.py",
                    "source_sha256": sha256_file(root / "probe.py"),
                    "qualified_api": ["fixture.api"],
                    "input_objects": ["fixture input"],
                    "output_objects": ["fixture output"],
                    "gates": ["positive", "negative", "boundary", "stress", "demotion"],
                    "cases": {name: copy.deepcopy(case) for name in REQUIRED_CASES},
                    "demotion": {"passed": True, "method": "erase edge call"},
                    "verdict": {
                        "receipt_valid": True,
                        "operational_status": "passed",
                        "operational_pass": True,
                    },
                }
            ],
        }
        # Paths must survive the TemporaryDirectory cleanup for the caller.
        estate["_selftest_source_bytes"] = {
            name: (root / name).read_text(encoding="utf-8")
            for name in ("registry.json", "runner.py", "probe.py", "support.py", "artifact.json")
        }
    return estate, registry, edges


def run_selftest() -> dict[str, Any]:
    estate, registry, edges = minimal_selftest_fixture()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for name, value in estate.pop("_selftest_source_bytes").items():
            (root / name).write_text(value, encoding="utf-8")
        cases: list[dict[str, Any]] = []
        baseline = validate_estate(
            copy.deepcopy(estate), registry, edges, repo_root=root, selftest_mode=True
        )
        cases.append({"id": "baseline_valid", "passed": baseline["receipt_valid"] and baseline["operational_pass"]})

        def invent_tool_call(value: dict[str, Any]) -> None:
            invented = copy.deepcopy(value["tool_receipts"][0]["tool_calls"][0])
            invented["qualified_api"] = "invented.module.fabricated_api"
            value["tool_receipts"][0]["tool_calls"].append(invented)

        def erase_representative_execution(value: dict[str, Any]) -> None:
            representative = value["tool_receipts"][0]["representative_sim"]
            for key in ("command", "execution_source_sha256", "emitted_artifacts"):
                representative.pop(key, None)

        mutations = {
            "missing_negative": lambda x: x["tool_receipts"][0]["cases"].pop("negative"),
            "import_only": lambda x: x["tool_receipts"][0].update({"tool_calls": []}),
            "false_demotion": lambda x: x["tool_receipts"][0]["demotion"].update({"passed": False}),
            "unknown_edge": lambda x: x["tool_receipts"][0]["adjacent_integrations"][0].update({"edge_id": "unknown"}),
            "stale_hash": lambda x: x["tool_receipts"][0]["source_binding"].update({"probe_sha256": "0" * 64}),
            "science_promotion": lambda x: x.update({"scientific_claim_proven": True}),
            "claude_bridge": lambda x: x.update({"claude_bridge_used": True}),
            "duplicate_tool": lambda x: x["tool_receipts"].append(copy.deepcopy(x["tool_receipts"][0])),
            "missing_edge_receipt": lambda x: x.update({"integration_edge_receipts": []}),
            "invented_tool_call": invent_tool_call,
            "hidden_raw_reuse": lambda x: x["commands"][0].update({"provenance": {"reused_raw": "hidden.json"}}),
            "representative_without_execution_receipt": erase_representative_execution,
            "raw_tool_call_hash_missing": lambda x: x["tool_receipts"][0]["tool_calls"][0].pop("raw_call_sha256"),
        }
        for case_id, mutate in mutations.items():
            candidate = copy.deepcopy(estate)
            mutate(candidate)
            verdict = validate_estate(
                candidate, registry, edges, repo_root=root, selftest_mode=True
            )
            cases.append({"id": case_id, "passed": verdict["receipt_valid"] is False, "finding_count": len(verdict["findings"])})
        return {
            "schema": "codex-ratchet.deep-stack-validator-selftest.v1",
            "case_count": len(cases),
            "passed_count": sum(1 for case in cases if case["passed"]),
            "all_pass": all(case["passed"] for case in cases),
            "cases": cases,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("estate")
    validate.add_argument("--receipt", required=True, type=Path)
    validate.add_argument("--registry", required=True, type=Path)
    validate.add_argument("--edges", required=True, type=Path)
    validate.add_argument("--repo-root", type=Path, default=Path.cwd())
    validate.add_argument("--out", type=Path)
    validate.add_argument("--require-operational-pass", action="store_true")

    selftest = sub.add_parser("selftest")
    selftest.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "selftest":
        verdict = run_selftest()
        if args.out:
            write_json(args.out, verdict)
        print(json.dumps(verdict, indent=2, sort_keys=True))
        return 0 if verdict["all_pass"] else 2

    estate = load_json(args.receipt)
    registry = load_json(args.registry)
    edges = load_json(args.edges)
    verdict = validate_estate(
        estate,
        registry,
        edges,
        repo_root=args.repo_root.resolve(),
        registry_path=args.registry.resolve(),
        edges_path=args.edges.resolve(),
    )
    if args.out:
        write_json(args.out, verdict)
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if not verdict["receipt_valid"]:
        return 2
    if args.require_operational_pass and not verdict["operational_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
