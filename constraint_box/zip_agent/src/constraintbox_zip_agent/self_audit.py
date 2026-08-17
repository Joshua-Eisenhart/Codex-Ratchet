from __future__ import annotations

import io
import stat
import warnings
import zipfile
from typing import Any

from .operation_ids import KNOWN_OPERATION_IDS
from .protocol import (
    FIXED_ZIP_DATETIME,
    MANIFEST_PATH,
    TaskSpec,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    deterministic_zip,
    runtime_source_sha256,
    sha256_bytes,
    strict_json_loads,
    validate_packet,
    validate_return_zip,
)


MODEL_LAUNCH_OPERATIONS = frozenset(
    {
        "run_md_agent_roster_v1",
        "run_provider_call_v1",
    }
)


def _packet_launches_models(packet: bytes) -> bool:
    validated = validate_packet(packet, known_operations=set(KNOWN_OPERATION_IDS))
    return bool(set(validated.manifest.allowed_operations) & MODEL_LAUNCH_OPERATIONS)


def _one_in_one_out(task: TaskSpec) -> tuple[str, str]:
    if len(task.input_paths) != 1 or len(task.output_paths) != 1:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    return task.input_paths[0], task.output_paths[0]


def _entries(packet: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(packet), "r") as archive:
        return {info.filename: archive.read(info) for info in archive.infolist() if not info.is_dir()}


def _manual_zip(items: list[tuple[str, bytes]]) -> bytes:
    out = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path, data in items:
                info = zipfile.ZipInfo(path, date_time=FIXED_ZIP_DATETIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.create_system = 3
                archive.writestr(info, data)
    return out.getvalue()


def _manifest_and_files(packet: bytes) -> tuple[dict[str, Any], dict[str, bytes]]:
    entries = _entries(packet)
    manifest = strict_json_loads(entries.pop(MANIFEST_PATH), label=MANIFEST_PATH)
    assert isinstance(manifest, dict)
    manifest.pop("file_sha256_registry", None)
    return manifest, entries


def _unknown_operation_packet(packet: bytes) -> bytes:
    manifest, files = _manifest_and_files(packet)
    first_task_path = manifest["task_execution_order"][0]
    task = strict_json_loads(files[first_task_path], label=first_task_path)
    assert isinstance(task, dict)
    task["operation"] = "unknown_operation_v1"
    files[first_task_path] = canonical_json_bytes(task)
    operations: set[str] = set()
    for path in manifest["task_execution_order"]:
        raw = strict_json_loads(files[path], label=path)
        assert isinstance(raw, dict)
        operations.add(raw["operation"])
    manifest["allowed_operations"] = sorted(operations)
    return build_packet(manifest, files)


def _missing_output_packet(packet: bytes) -> bytes:
    manifest, files = _manifest_and_files(packet)
    manifest["required_output_file_list"] = sorted(
        set(manifest["required_output_file_list"]) | {"output/never-produced.json"}
    )
    return build_packet(manifest, files)


def mutation_cases(packet: bytes) -> dict[str, tuple[bytes, str]]:
    entries = _entries(packet)
    ordinary = next(path for path in sorted(entries) if path != MANIFEST_PATH and not path.startswith("tasks/"))
    tampered = dict(entries)
    tampered[ordinary] += b"tamper"
    undeclared = dict(entries)
    undeclared["inputs/undeclared.txt"] = b"not in manifest"
    first_path = sorted(entries)[0]
    duplicate_items = [(path, entries[path]) for path in sorted(entries)]
    duplicate_items.append((first_path, entries[first_path]))
    traversal_items = [(path, entries[path]) for path in sorted(entries)]
    traversal_items.append(("../escape.txt", b"escape"))
    return {
        "payload_digest_tamper": (deterministic_zip(tampered), "REFUSE_FILE_DIGEST_MISMATCH"),
        "undeclared_member": (deterministic_zip(undeclared), "REFUSE_FILE_REGISTRY_SET_MISMATCH"),
        "duplicate_member": (_manual_zip(duplicate_items), "REFUSE_DUPLICATE_MEMBER"),
        "path_traversal": (_manual_zip(traversal_items), "REFUSE_UNSAFE_PATH"),
        "unknown_operation": (_unknown_operation_packet(packet), "REFUSE_OPERATION_NOT_IMPLEMENTED"),
        "unproduced_required_output": (
            _missing_output_packet(packet),
            "REFUSE_REQUIRED_OUTPUT_SET_MISMATCH",
        ),
    }


def _audit_structure(packet: bytes) -> dict[str, Any]:
    first = validate_packet(packet, known_operations=set(KNOWN_OPERATION_IDS))
    second = validate_packet(packet, known_operations=set(KNOWN_OPERATION_IDS))
    checks = {
        "packet_digest_replay": first.packet_sha256 == second.packet_sha256,
        "task_order_replay": first.tasks == second.tasks,
        "registry_exact": set(first.members) - {MANIFEST_PATH} == set(first.manifest.file_sha256_registry),
        "required_outputs_exact": {
            path for task in first.tasks for path in task.output_paths
        } == set(first.manifest.required_output_file_list),
    }
    return {
        "schema": "constraintbox.zip_failure_member.v1",
        "member": "structure",
        "status": "PASS" if all(checks.values()) else "REVISE",
        "target_sha256": first.packet_sha256,
        "checks": checks,
    }


def _audit_mutations(packet: bytes) -> dict[str, Any]:
    observations: dict[str, dict[str, Any]] = {}
    for name, (mutant, expected) in mutation_cases(packet).items():
        observed = "ACCEPTED"
        try:
            validate_packet(mutant, known_operations=set(KNOWN_OPERATION_IDS))
        except ZipJobRefusal as exc:
            observed = exc.reason_code
        observations[name] = {
            "mutant_sha256": sha256_bytes(mutant),
            "expected": expected,
            "observed": observed,
            "pass": observed == expected,
        }
    status = "PASS" if all(row["pass"] for row in observations.values()) else "REVISE"
    return {
        "schema": "constraintbox.zip_failure_member.v1",
        "member": "counterexample",
        "status": status,
        "target_sha256": sha256_bytes(packet),
        "observations": observations,
    }


def _audit_authority(packet: bytes, return_zip: bytes | None = None) -> dict[str, Any]:
    from .runtime import execute_packet

    unknown_reason = "ACCEPTED"
    try:
        validate_packet(_unknown_operation_packet(packet), known_operations=set(KNOWN_OPERATION_IDS))
    except ZipJobRefusal as exc:
        unknown_reason = exc.reason_code
    if return_zip is None:
        if _packet_launches_models(packet):
            raise ZipJobRefusal(
                "REFUSE_FAILURE_WAVE_REEXECUTES_MODELS",
                "target_return_required",
            )
        first = execute_packet(packet)
        second = execute_packet(packet)
        checks = {
            "unknown_operation_refused": unknown_reason == "REFUSE_OPERATION_NOT_IMPLEMENTED",
            "byte_identical_replay": first.return_zip_bytes == second.return_zip_bytes,
            "input_identity_bound": first.input_packet_sha256 == sha256_bytes(packet),
        }
        mode = "execute_and_replay"
        manifest = None
    else:
        manifest = validate_return_zip(
            return_zip,
            expected_input_sha256=sha256_bytes(packet),
            input_packet_bytes=packet,
            require_current_runtime=False,
        )
        runtime_current = manifest.runtime_source_sha256 == runtime_source_sha256()
        checks = {
            "unknown_operation_refused": unknown_reason == "REFUSE_OPERATION_NOT_IMPLEMENTED",
            "return_integrity_bound": True,
            "input_identity_bound": manifest.input_packet_sha256 == sha256_bytes(packet),
            "runtime_source_current": runtime_current,
        }
        mode = "verify_existing_return_without_execution"
    return {
        "schema": "constraintbox.zip_failure_member.v1",
        "member": "authority-collapse",
        "status": "PASS" if all(checks.values()) else "REVISE",
        "target_sha256": sha256_bytes(packet),
        "target_return_sha256": sha256_bytes(return_zip) if return_zip is not None else None,
        "target_runtime_source_sha256": (
            manifest.runtime_source_sha256 if manifest is not None else None
        ),
        "existing_return_consumed": return_zip is not None,
        "mode": mode,
        "checks": checks,
    }


def _return_report(return_zip: bytes) -> dict[str, Any]:
    entries = _entries(return_zip)
    outputs = [path for path in entries if path.startswith("output/") and path.endswith(".json")]
    if len(outputs) != 1:
        raise ZipJobRefusal("REFUSE_FAILURE_MEMBER_OUTPUT_SHAPE", repr(outputs))
    report = strict_json_loads(entries[outputs[0]], label=outputs[0])
    if not isinstance(report, dict):
        raise ZipJobRefusal("REFUSE_FAILURE_MEMBER_OUTPUT_SHAPE", outputs[0])
    return report


def _compile_failure_wave(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    if len(task.input_paths) != 3 or len(task.output_paths) != 1:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    reports = [_return_report(workspace[path]) for path in task.input_paths]
    members = {report.get("member"): report for report in reports}
    expected = {"structure", "counterexample", "authority-collapse"}
    complete = set(members) == expected
    passing = complete and all(members[name].get("status") == "PASS" for name in expected)
    result = {
        "schema": "constraintbox.zip_failure_wave.v1",
        "verdict": "PASS" if passing else "REVISE",
        "members_complete": complete,
        "member_status": {name: members.get(name, {}).get("status", "MISSING") for name in sorted(expected)},
        "member_report_sha256": {
            name: sha256_bytes(canonical_json_bytes(members[name])) for name in sorted(members)
        },
        "claim_ceiling": "prototype_self_falsification_only;not_independent_proof;not_model_council;not_release",
    }
    return {task.output_paths[0]: canonical_json_bytes(result)}


def run_audit_operation(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    if task.operation == "compile_failure_wave_v1":
        return _compile_failure_wave(task, workspace)
    if len(task.output_paths) != 1:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    output_path = task.output_paths[0]
    if task.operation == "audit_runtime_authority_v1":
        if len(task.input_paths) not in {1, 2}:
            raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
        packet = workspace[task.input_paths[0]]
        target_return = workspace[task.input_paths[1]] if len(task.input_paths) == 2 else None
        report = _audit_authority(packet, target_return)
        return {output_path: canonical_json_bytes(report)}
    source_path, output_path = _one_in_one_out(task)
    packet = workspace[source_path]
    if task.operation == "audit_packet_structure_v1":
        report = _audit_structure(packet)
    elif task.operation == "audit_packet_mutations_v1":
        report = _audit_mutations(packet)
    else:
        raise ZipJobRefusal("REFUSE_AUDIT_OPERATION_UNKNOWN", task.operation)
    return {output_path: canonical_json_bytes(report)}
