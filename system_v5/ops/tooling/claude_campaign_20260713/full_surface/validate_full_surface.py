#!/usr/bin/env python3
"""Closed-schema, hash-bound validator for the full-surface campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA = "codex-ratchet.full-surface-campaign-envelope.v1"
EXPECTED_ARCHIVE_MEMBERS = {
    "julia_canon/src/ExceptionalAlgebraCanon.jl",
    "sims_and_scripts/living_purgatory_ledger_r2_results.json",
    "sims_and_scripts/ontological_finitude_cosmogenesis_ratchet_sim.py",
}
TOP_KEYS = {
    "schema",
    "campaign_id",
    "created_at",
    "started_at",
    "duration_seconds",
    "command",
    "runner_identity",
    "lev_executor",
    "source",
    "archive",
    "artifact_root",
    "classification",
    "promotion_allowed",
    "partial_promotion_allowed",
    "formal_admission_allowed",
    "provider_advisory_is_evidence",
    "projection_only",
    "runner_all_completed",
    "scientific_all_pass",
    "all_pass",
    "truth_state",
    "summary",
    "groups",
    "set_coverage",
    "blocked_inventory",
    "tool_calls",
    "claim_ceiling",
    "blocked_consumers",
}
GROUP_KEYS = {
    "id",
    "kind",
    "classification",
    "sources",
    "commands",
    "artifacts",
    "required_artifact_count",
    "execution_completed",
    "scientific_pass",
    "science_evidence",
    "status",
    "claim_ceiling",
    "blockers",
    "blocked_consumers",
    "red_preservation_required",
}
COMMAND_KEYS = {
    "command",
    "cwd",
    "environment_overrides",
    "started_at",
    "finished_at",
    "duration_seconds",
    "exit_code",
    "timed_out",
    "stdout_path",
    "stdout_sha256",
    "stderr_path",
    "stderr_sha256",
}
ARTIFACT_KEYS = {"path", "sha256"}
FILE_SOURCE_KEYS = {"kind", "path", "sha256", "provenance"}
ARCHIVE_SOURCE_KEYS = {"kind", "path", "member", "sha256", "provenance"}
EVIDENCE_KEYS = {
    "kind",
    "artifact_path",
    "json_pointer",
    "command_index",
    "observed",
    "pass_value",
}
SUMMARY_KEYS = {
    "group_count",
    "command_count",
    "executed_command_count",
    "execution_failed_count",
    "scientific_green_count",
    "scientific_red_count",
    "scientific_not_assessed_count",
    "blocked_inventory_count",
    "set_count",
    "set_full_count",
    "set_partial_count",
    "set_blocked_count",
}
SET_KEYS = {"set_id", "group_ids", "status", "blockers", "promotion_allowed"}
INVENTORY_KEYS = {"id", "status", "source_count", "sources", "reason"}
INVENTORY_SOURCE_KEYS = {"path", "sha256", "reason"}
TOOL_CALL_KEYS = {"tool", "function", "observable"}
RUNNER_IDENTITY_KEYS = {
    "python_executable",
    "python_version",
    "platform",
    "pid",
}
LEV_EXECUTOR_KEYS = {
    "worktree",
    "git_commit",
    "expected_status",
    "expected_suite_status",
    "projection_only",
    "release_eligible",
}
FORBIDDEN_AUTHORITY_KEYS = {
    "provider_as_evidence",
    "provider_evidence",
    "provider_gate_pass",
    "provider_authority",
    "advisory_gate_pass",
    "provisional_promotion",
    "partial_promotion",
    "partial_promotion_status",
    "projection_pass",
    "projection_authority",
    "replay_allowed",
    "authority_override",
    "candidate_hash_override",
}
GROUP_CONTRACTS = {
    "hardened_d_f_j_k_h": ("hardened_stress_chain", 1, "artifact_json", "/all_pass", None, True, True),
    "imported_python_battery": ("imported_candidate_battery", 1, "artifact_json", "/fail", None, 0, True),
    "imported_fit_sweep": ("imported_candidate_battery", 1, "artifact_json", "/fail", None, 0, True),
    "imported_julia_battery": ("imported_candidate_battery", 1, "artifact_json", "/fail", None, 0, True),
    "foundation_entropy_gradient": ("foundation_scratch_diagnostic", 1, "artifact_json", "/FOLLOWS_RATCHET_RULES", None, True, True),
    "foundation_forcing_robustness": ("foundation_scratch_diagnostic", 1, "artifact_json", "/policy_eval/FOUNDATIONS_EARNED_FORCED_ROBUST_LOADBEARING", None, True, True),
    "foundation_drive_mss_tiebreak": ("foundation_scratch_diagnostic", 1, "artifact_json", "/policy_eval/ROOT_DRIVE_AND_TIEBREAK_AUDITED", None, True, True),
    "manifold_dual_ratchet_foundations_v0": ("cross_runtime_foundation_diagnostic", 1, "artifact_json", "/parity_passed", None, True, True),
    "manifold_dual_ratchet_foundations_v0_1": ("cross_runtime_foundation_diagnostic", 1, "artifact_json", "/parity_passed", None, True, True),
    "legacy_engine_1q": ("legacy_cross_substrate_engine_diagnostic", 4, "command_exit", None, 4, 0, True),
    "legacy_engine_3q": ("legacy_cross_substrate_engine_diagnostic", 4, "command_exit", None, 4, 0, True),
    "ratchet_process_v1_tests": ("process_gate_test", 0, "command_exit", None, 0, 0, True),
    "qics_entropy_dpi_oracle": ("pinned_external_oracle_diagnostic", 1, "artifact_json", "/all_tests_pass", None, True, True),
    "lean_formal_surface": ("formal_build", 0, "command_exit", None, 0, 0, True),
    "grok45_advisory_validation": ("provider_advisory_validation", 0, "command_exit", None, 0, 0, False),
}
BASE_GROUP_IDS = set(GROUP_CONTRACTS) - {"grok45_advisory_validation"}
SET_CONTRACTS = {
    "A": (["imported_python_battery"], []),
    "B": (["imported_julia_battery"], ["Julia battery result may remain red"]),
    "C": (["imported_python_battery", "legacy_engine_1q", "legacy_engine_3q"], []),
    "D": (["hardened_d_f_j_k_h"], []),
    "E": (["imported_python_battery"], ["fixture-level Maude only"]),
    "F": (["hardened_d_f_j_k_h"], []),
    "G": (["imported_python_battery", "imported_julia_battery", "hardened_d_f_j_k_h"], []),
    "H": (["hardened_d_f_j_k_h"], ["expected semantic red"]),
    "I": (["imported_python_battery", "imported_julia_battery"], ["Flux/Lux consumer chain not executed"]),
    "J": (["hardened_d_f_j_k_h", "imported_fit_sweep"], ["Julia IntervalArithmetic leg not executed"]),
    "K": (["hardened_d_f_j_k_h", "imported_python_battery", "imported_julia_battery"], []),
    "L": (["lean_formal_surface", "qics_entropy_dpi_oracle"], ["ALCO and physlib legs blocked"]),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def closed(errors: list[str], value: Any, keys: set[str], label: str) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    extra = sorted(set(value) - keys)
    missing = sorted(keys - set(value))
    if extra:
        errors.append(f"{label} unknown fields: {', '.join(extra)}")
    if missing:
        errors.append(f"{label} missing fields: {', '.join(missing)}")
    return not extra and not missing


def timestamp_ok(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def pointer(payload: Any, path: str) -> Any:
    value = payload
    for token in path.strip("/").split("/") if path != "/" else []:
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def scan_forbidden(value: Any, errors: list[str], prefix: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in FORBIDDEN_AUTHORITY_KEYS:
                errors.append(f"forbidden authority alias at {prefix}.{key}")
            if lowered.startswith("partial_promotion") and lowered != "partial_promotion_allowed":
                errors.append(f"forbidden partial-promotion alias at {prefix}.{key}")
            scan_forbidden(child, errors, f"{prefix}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_forbidden(child, errors, f"{prefix}[{index}]")


def validate_source(
    record: Any,
    errors: list[str],
    label: str,
    *,
    source_commit: str,
    repo_root: Path,
    provider_advisory: bool,
) -> None:
    if not isinstance(record, dict):
        errors.append(f"{label} must be an object")
        return
    kind = record.get("kind")
    expected = FILE_SOURCE_KEYS if kind == "file" else ARCHIVE_SOURCE_KEYS if kind == "archive_member" else set()
    if not expected:
        errors.append(f"{label}.kind invalid")
        return
    closed(errors, record, expected, label)
    path = Path(str(record.get("path", "")))
    if kind == "file":
        add(errors, path.is_file(), f"{label} file missing")
        if path.is_file():
            add(errors, sha256_file(path) == record.get("sha256"), f"{label} file hash mismatch")
        if not provider_advisory:
            try:
                relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                relative = ""
            add(errors, bool(relative), f"{label} non-advisory file must be repo-bound")
            if relative:
                result = subprocess.run(
                    ["git", "show", f"{source_commit}:{relative}"],
                    cwd=repo_root,
                    capture_output=True,
                    check=False,
                )
                add(errors, result.returncode == 0, f"{label} absent from source commit")
                if result.returncode == 0:
                    add(
                        errors,
                        hashlib.sha256(result.stdout).hexdigest() == record.get("sha256"),
                        f"{label} commit hash mismatch or replayed source",
                    )
    else:
        member = record.get("member")
        add(errors, path.is_file(), f"{label} archive missing")
        try:
            with zipfile.ZipFile(path) as bundle:
                data = bundle.read(str(member))
            add(errors, hashlib.sha256(data).hexdigest() == record.get("sha256"), f"{label} archive member hash mismatch")
        except (OSError, KeyError, zipfile.BadZipFile):
            errors.append(f"{label} archive member unreadable")


def validate_artifact(
    record: Any,
    errors: list[str],
    label: str,
    *,
    artifact_root: Path,
) -> None:
    if not closed(errors, record, ARTIFACT_KEYS, label):
        return
    path = Path(str(record["path"]))
    try:
        path.resolve().relative_to(artifact_root.resolve())
        contained = True
    except ValueError:
        contained = False
    add(errors, contained, f"{label} outside artifact root")
    add(errors, path.is_file(), f"{label} missing")
    if path.is_file():
        add(errors, sha256_file(path) == record["sha256"], f"{label} hash mismatch")


def validate_command(
    record: Any,
    errors: list[str],
    label: str,
    *,
    artifact_root: Path,
) -> None:
    if not closed(errors, record, COMMAND_KEYS, label):
        return
    add(errors, isinstance(record["command"], list) and bool(record["command"]), f"{label}.command invalid")
    add(errors, isinstance(record["environment_overrides"], dict), f"{label}.environment_overrides invalid")
    add(errors, timestamp_ok(record["started_at"]), f"{label}.started_at invalid")
    add(errors, timestamp_ok(record["finished_at"]), f"{label}.finished_at invalid")
    add(errors, isinstance(record["duration_seconds"], (int, float)) and record["duration_seconds"] >= 0, f"{label}.duration invalid")
    add(errors, isinstance(record["timed_out"], bool), f"{label}.timed_out invalid")
    add(errors, record["exit_code"] is None or isinstance(record["exit_code"], int), f"{label}.exit_code invalid")
    for stream in ("stdout", "stderr"):
        path = Path(str(record[f"{stream}_path"]))
        try:
            path.resolve().relative_to(artifact_root.resolve())
            contained = True
        except ValueError:
            contained = False
        add(errors, contained, f"{label}.{stream} outside artifact root")
        add(errors, path.is_file(), f"{label}.{stream} missing")
        if path.is_file():
            add(errors, sha256_file(path) == record[f"{stream}_sha256"], f"{label}.{stream} hash mismatch")


def validate_group(
    row: Any,
    errors: list[str],
    index: int,
    *,
    source_commit: str,
    repo_root: Path,
    artifact_root: Path,
) -> None:
    label = f"groups[{index}]"
    if not closed(errors, row, GROUP_KEYS, label):
        return
    add(errors, row["classification"] == "integration_diagnostic", f"{label} classification mismatch")
    add(errors, isinstance(row["id"], str) and bool(row["id"]), f"{label}.id invalid")
    add(errors, isinstance(row["commands"], list) and bool(row["commands"]), f"{label}.commands invalid")
    add(errors, isinstance(row["sources"], list) and bool(row["sources"]), f"{label}.sources invalid")
    add(errors, isinstance(row["artifacts"], list), f"{label}.artifacts invalid")
    add(
        errors,
        isinstance(row["required_artifact_count"], int)
        and not isinstance(row["required_artifact_count"], bool)
        and row["required_artifact_count"] >= 0,
        f"{label}.required_artifact_count invalid",
    )
    add(errors, isinstance(row["blockers"], list), f"{label}.blockers invalid")
    add(errors, isinstance(row["blocked_consumers"], list) and bool(row["blocked_consumers"]), f"{label}.blocked_consumers invalid")
    add(errors, isinstance(row["claim_ceiling"], str) and bool(row["claim_ceiling"]), f"{label}.claim_ceiling invalid")
    add(
        errors,
        isinstance(row["red_preservation_required"], bool),
        f"{label}.red_preservation_required invalid",
    )
    contract = GROUP_CONTRACTS.get(row["id"])
    add(errors, contract is not None, f"{label} unexpected group id")
    if contract is not None:
        (
            expected_kind,
            required_count,
            evidence_kind,
            evidence_pointer,
            command_index,
            pass_value,
            preserve_red,
        ) = contract
        add(errors, row["kind"] == expected_kind, f"{label}.kind contract mismatch")
        add(
            errors,
            row["required_artifact_count"] == required_count,
            f"{label}.required_artifact_count contract mismatch",
        )
        add(
            errors,
            row["red_preservation_required"] is preserve_red,
            f"{label}.red preservation contract mismatch",
        )
    provider_advisory = row["kind"] == "provider_advisory_validation"
    for source_index, source in enumerate(row["sources"]):
        validate_source(
            source,
            errors,
            f"{label}.sources[{source_index}]",
            source_commit=source_commit,
            repo_root=repo_root,
            provider_advisory=provider_advisory,
        )
    for command_index, command in enumerate(row["commands"]):
        validate_command(
            command,
            errors,
            f"{label}.commands[{command_index}]",
            artifact_root=artifact_root,
        )
    for artifact_index, artifact in enumerate(row["artifacts"]):
        validate_artifact(
            artifact,
            errors,
            f"{label}.artifacts[{artifact_index}]",
            artifact_root=artifact_root,
        )
    derived_execution = all(
        command.get("timed_out") is False and command.get("exit_code") is not None
        for command in row["commands"]
    ) and len(row["artifacts"]) >= row["required_artifact_count"]
    add(errors, row["execution_completed"] is derived_execution, f"{label}.execution_completed mismatch")
    evidence = row["science_evidence"]
    if not closed(errors, evidence, EVIDENCE_KEYS, f"{label}.science_evidence"):
        return
    if contract is not None:
        add(errors, evidence["kind"] == evidence_kind, f"{label} evidence kind contract mismatch")
        add(
            errors,
            evidence["json_pointer"] == evidence_pointer,
            f"{label} evidence pointer contract mismatch",
        )
        add(
            errors,
            evidence["command_index"] == command_index,
            f"{label} evidence command contract mismatch",
        )
        add(
            errors,
            evidence["pass_value"] == pass_value,
            f"{label} evidence pass value contract mismatch",
        )
    observed = None
    if evidence["kind"] == "artifact_json":
        artifact_paths = {artifact["path"] for artifact in row["artifacts"] if isinstance(artifact, dict)}
        add(errors, evidence["artifact_path"] in artifact_paths, f"{label} evidence artifact not declared")
        try:
            payload = json.loads(Path(evidence["artifact_path"]).read_text(encoding="utf-8"))
            observed = pointer(payload, evidence["json_pointer"])
        except (OSError, json.JSONDecodeError, KeyError, IndexError, TypeError):
            errors.append(f"{label} evidence JSON/pointer unreadable")
        add(errors, evidence["command_index"] is None, f"{label} artifact evidence command_index must be null")
    elif evidence["kind"] == "command_exit":
        command_index = evidence["command_index"]
        add(errors, isinstance(command_index, int) and 0 <= command_index < len(row["commands"]), f"{label} evidence command_index invalid")
        if isinstance(command_index, int) and 0 <= command_index < len(row["commands"]):
            observed = row["commands"][command_index]["exit_code"]
        add(errors, evidence["artifact_path"] is None and evidence["json_pointer"] is None, f"{label} command evidence paths must be null")
    else:
        errors.append(f"{label} science evidence kind invalid")
    add(errors, observed == evidence["observed"], f"{label} evidence observed value mismatch")
    if provider_advisory:
        add(errors, row["scientific_pass"] is None, f"{label} provider advisory cannot be a scientific pass")
        expected_status = "scientific_not_assessed" if derived_execution else "execution_failed"
    else:
        derived_scientific = observed == evidence["pass_value"]
        add(errors, row["scientific_pass"] is derived_scientific, f"{label} scientific pass mismatch")
        expected_status = (
            "execution_failed"
            if not derived_execution
            else "scientific_green"
            if derived_scientific
            else "scientific_red"
        )
    add(errors, row["status"] == expected_status, f"{label} status mismatch")


def validate(raw: dict[str, Any], *, envelope_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    if not closed(errors, raw, TOP_KEYS, "$"):
        return errors
    scan_forbidden(raw, errors)
    add(errors, raw["schema"] == EXPECTED_SCHEMA, "schema mismatch")
    add(errors, raw["campaign_id"] == "claude_campaign_20260713_full_surface_v1", "campaign id mismatch")
    add(errors, raw["classification"] == "integration_diagnostic", "classification mismatch")
    add(errors, raw["promotion_allowed"] is False, "promotion must remain false")
    add(errors, raw["partial_promotion_allowed"] is False, "partial promotion must remain false")
    add(errors, raw["formal_admission_allowed"] is False, "formal admission must remain false")
    add(errors, raw["provider_advisory_is_evidence"] is False, "provider advice must not be evidence")
    add(errors, raw["projection_only"] is False, "projection-only state cannot satisfy execution")
    add(errors, raw["all_pass"] is False, "campaign all_pass must remain false")
    add(errors, raw["truth_state"] == "host_recomputed_blocked", "truth_state mismatch")
    add(errors, timestamp_ok(raw["created_at"]) and timestamp_ok(raw["started_at"]), "timestamps invalid")
    add(errors, isinstance(raw["duration_seconds"], (int, float)) and raw["duration_seconds"] >= 0, "duration invalid")
    add(errors, isinstance(raw["claim_ceiling"], str) and bool(raw["claim_ceiling"]), "claim ceiling missing")
    add(errors, isinstance(raw["blocked_consumers"], list) and bool(raw["blocked_consumers"]), "blocked consumers missing")
    add(errors, isinstance(raw["tool_calls"], list) and bool(raw["tool_calls"]), "tool calls missing")
    for index, tool_call in enumerate(raw["tool_calls"]):
        closed(errors, tool_call, TOOL_CALL_KEYS, f"tool_calls[{index}]")

    runner_identity = raw["runner_identity"]
    if closed(errors, runner_identity, RUNNER_IDENTITY_KEYS, "runner_identity"):
        add(errors, isinstance(runner_identity["python_executable"], str), "runner python executable invalid")
        add(errors, isinstance(runner_identity["python_version"], str), "runner python version invalid")
        add(errors, isinstance(runner_identity["platform"], str), "runner platform invalid")
        add(errors, isinstance(runner_identity["pid"], int) and runner_identity["pid"] > 0, "runner pid invalid")

    lev_executor = raw["lev_executor"]
    if closed(errors, lev_executor, LEV_EXECUTOR_KEYS, "lev_executor"):
        lev_worktree = Path(str(lev_executor["worktree"]))
        add(errors, lev_worktree.is_dir(), "Lev executor worktree missing")
        lev_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=lev_worktree if lev_worktree.is_dir() else Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )
        add(errors, lev_head.returncode == 0, "Lev executor commit unreadable")
        if lev_head.returncode == 0:
            add(errors, lev_head.stdout.strip() == lev_executor["git_commit"], "Lev executor commit mismatch")
        add(errors, lev_executor["expected_status"] == "projected", "Lev expected status mismatch")
        add(errors, lev_executor["expected_suite_status"] == "passed", "Lev expected suite status mismatch")
        add(errors, lev_executor["projection_only"] is True, "Lev projection fence missing")
        add(errors, lev_executor["release_eligible"] is False, "Lev release fence missing")

    artifact_root = Path(str(raw["artifact_root"]))
    add(errors, artifact_root.is_dir(), "artifact root missing")

    source = raw["source"]
    if closed(errors, source, {"path", "sha256", "git_commit"}, "source"):
        runner = Path(str(source["path"]))
        add(errors, runner.is_file(), "runner source missing")
        add(errors, bool(re.fullmatch(r"[0-9a-f]{40}", str(source["git_commit"]))), "source commit invalid")
        if runner.is_file():
            add(errors, sha256_file(runner) == source["sha256"], "runner source hash mismatch")
        root_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=runner.parent if runner.is_file() else Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )
        repo_root = Path(root_result.stdout.strip()) if root_result.returncode == 0 else Path.cwd()
        try:
            runner_relative = runner.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            runner_relative = ""
        add(errors, bool(runner_relative), "runner source is outside repository")
        result = subprocess.run(
            ["git", "show", f"{source['git_commit']}:{runner_relative}"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        ) if runner.is_file() and runner_relative else None
        add(errors, result is not None and result.returncode == 0, "runner absent from source commit")
        if result is not None and result.returncode == 0:
            add(errors, hashlib.sha256(result.stdout).hexdigest() == source["sha256"], "runner/source commit hash mismatch")
    else:
        repo_root = Path.cwd()

    archive = raw["archive"]
    if closed(errors, archive, {"path", "sha256", "members"}, "archive"):
        archive_path = Path(str(archive["path"]))
        add(errors, archive_path.is_file(), "archive missing")
        if archive_path.is_file():
            add(errors, sha256_file(archive_path) == archive["sha256"], "archive hash mismatch")
        add(errors, isinstance(archive["members"], list) and len(archive["members"]) == 3, "archive members mismatch")
        add(
            errors,
            {
                member.get("member")
                for member in archive["members"]
                if isinstance(member, dict)
            }
            == EXPECTED_ARCHIVE_MEMBERS,
            "archive member identities mismatch",
        )
        for index, member in enumerate(archive["members"] if isinstance(archive["members"], list) else []):
            validate_source(member, errors, f"archive.members[{index}]", source_commit=source.get("git_commit", ""), repo_root=repo_root, provider_advisory=False)

    command = raw["command"]
    add(errors, isinstance(command, list) and len(command) == 8, "top-level command shape invalid")
    if isinstance(command, list) and len(command) == 8:
        add(errors, command[0] == runner_identity.get("python_executable"), "command/runtime mismatch")
        add(errors, Path(str(command[1])).resolve() == Path(str(source.get("path", ""))).resolve(), "command/runner mismatch")
        add(errors, command[2:7:2] == ["--archive", "--output", "--artifact-dir"], "command option order mismatch")
        add(errors, Path(str(command[3])).resolve() == Path(str(archive.get("path", ""))).resolve(), "command/archive mismatch")
        add(errors, Path(str(command[7])).resolve() == artifact_root.resolve(), "command/artifact-root mismatch")

    groups = raw["groups"]
    add(errors, isinstance(groups, list) and bool(groups), "groups missing")
    if not isinstance(groups, list):
        return errors
    ids = [row.get("id") for row in groups if isinstance(row, dict)]
    add(errors, len(ids) == len(set(ids)), "duplicate group ids")
    observed_ids = set(ids)
    add(
        errors,
        frozenset(observed_ids)
        in {frozenset(BASE_GROUP_IDS), frozenset(GROUP_CONTRACTS)},
        "group inventory does not match the bounded campaign contract",
    )
    for index, row in enumerate(groups):
        validate_group(
            row,
            errors,
            index,
            source_commit=source.get("git_commit", ""),
            repo_root=repo_root,
            artifact_root=artifact_root,
        )

    sets = raw["set_coverage"]
    add(errors, isinstance(sets, list) and len(sets) == 12, "set coverage must contain A-L")
    group_ids = set(ids)
    if isinstance(sets, list):
        add(errors, {row.get("set_id") for row in sets if isinstance(row, dict)} == set("ABCDEFGHIJKL"), "set ids mismatch")
        for index, row in enumerate(sets):
            if not closed(errors, row, SET_KEYS, f"set_coverage[{index}]"):
                continue
            add(errors, row["promotion_allowed"] is False, f"set {row['set_id']} promotion must be false")
            add(errors, isinstance(row["group_ids"], list) and all(group_id in group_ids for group_id in row["group_ids"]), f"set {row['set_id']} group ids invalid")
            add(errors, row["status"] in {"execution_blocked", "partial", "red", "bounded_green", "not_assessed"}, f"set {row['set_id']} status invalid")
            add(errors, isinstance(row["blockers"], list), f"set {row['set_id']} blockers invalid")
            expected_set = SET_CONTRACTS.get(row["set_id"])
            add(errors, expected_set is not None, f"set {row['set_id']} is outside the contract")
            if expected_set is not None:
                add(errors, row["group_ids"] == expected_set[0], f"set {row['set_id']} group contract mismatch")
                add(errors, row["blockers"] == expected_set[1], f"set {row['set_id']} blocker contract mismatch")
            selected = [
                group
                for group in groups
                if group.get("id") in row["group_ids"]
            ]
            execution = (
                len(selected) == len(row["group_ids"])
                and all(group.get("execution_completed") is True for group in selected)
            )
            scientific_values = [group.get("scientific_pass") for group in selected]
            expected_status = (
                "execution_blocked"
                if not execution
                else "partial"
                if row["blockers"]
                else "red"
                if any(value is False for value in scientific_values)
                else "bounded_green"
                if scientific_values and all(value is True for value in scientific_values)
                else "not_assessed"
            )
            add(errors, row["status"] == expected_status, f"set {row['set_id']} status mismatch")

    inventory = raw["blocked_inventory"]
    add(errors, isinstance(inventory, list), "blocked inventory invalid")
    if isinstance(inventory, list):
        for index, row in enumerate(inventory):
            if not closed(errors, row, INVENTORY_KEYS, f"blocked_inventory[{index}]"):
                continue
            add(errors, row["status"] == "blocked", f"blocked_inventory[{index}] status invalid")
            add(errors, row["source_count"] == len(row["sources"]), f"blocked_inventory[{index}] source count mismatch")
            for source_index, record in enumerate(row["sources"]):
                source_label = f"blocked_inventory[{index}].sources[{source_index}]"
                if not closed(errors, record, INVENTORY_SOURCE_KEYS, source_label):
                    continue
                inventory_path = Path(str(record["path"]))
                add(errors, inventory_path.is_file(), f"{source_label} missing")
                if inventory_path.is_file():
                    add(errors, sha256_file(inventory_path) == record["sha256"], f"{source_label} hash mismatch")
                    try:
                        relative = inventory_path.resolve().relative_to(repo_root.resolve()).as_posix()
                    except ValueError:
                        relative = ""
                    add(errors, bool(relative), f"{source_label} outside repository")
                    if relative:
                        committed = subprocess.run(
                            ["git", "show", f"{source.get('git_commit', '')}:{relative}"],
                            cwd=repo_root,
                            capture_output=True,
                            check=False,
                        )
                        add(errors, committed.returncode == 0, f"{source_label} absent from source commit")
                        if committed.returncode == 0:
                            add(
                                errors,
                                hashlib.sha256(committed.stdout).hexdigest() == record["sha256"],
                                f"{source_label} commit hash mismatch",
                            )

    summary = raw["summary"]
    if closed(errors, summary, SUMMARY_KEYS, "summary"):
        scientific = [row["scientific_pass"] for row in groups if row.get("scientific_pass") is not None]
        derived = {
            "group_count": len(groups),
            "command_count": sum(len(row["commands"]) for row in groups),
            "executed_command_count": sum(
                1
                for row in groups
                for command in row["commands"]
                if command["timed_out"] is False and command["exit_code"] is not None
            ),
            "execution_failed_count": sum(row["execution_completed"] is not True for row in groups),
            "scientific_green_count": sum(value is True for value in scientific),
            "scientific_red_count": sum(value is False for value in scientific),
            "scientific_not_assessed_count": sum(row["scientific_pass"] is None for row in groups),
            "blocked_inventory_count": len(inventory),
            "set_count": len(sets),
            "set_full_count": sum(row["status"] in {"bounded_green", "red"} for row in sets),
            "set_partial_count": sum(row["status"] == "partial" for row in sets),
            "set_blocked_count": sum(row["status"] == "execution_blocked" for row in sets),
        }
        add(errors, summary == derived, "summary does not recompute from children")
        runner_completed = derived["execution_failed_count"] == 0 and derived["executed_command_count"] == derived["command_count"]
        science_all = bool(scientific) and all(scientific) and derived["set_partial_count"] == 0 and derived["set_blocked_count"] == 0
        add(errors, raw["runner_all_completed"] is runner_completed, "runner_all_completed mismatch")
        add(errors, raw["scientific_all_pass"] is science_all, "scientific_all_pass mismatch")
        add(errors, derived["executed_command_count"] > 0, "zero execution is not acceptable")
    if envelope_path is not None:
        add(errors, Path(raw["command"][raw["command"].index("--output") + 1]).resolve() == envelope_path.resolve(), "command/output envelope path mismatch")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("envelope", type=Path)
    args = parser.parse_args()
    try:
        raw = json.loads(args.envelope.read_text(encoding="utf-8"))
        errors = validate(raw, envelope_path=args.envelope)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        errors = [f"parse failure: {error}"]
    print(json.dumps({"ok": not errors, "errors": errors, "envelope": str(args.envelope.resolve())}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
