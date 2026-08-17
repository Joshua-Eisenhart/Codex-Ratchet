from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import stat
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

MANIFEST_PATH = "ZIP_JOB_MANIFEST.json"
FIXED_ZIP_DATETIME = (1980, 1, 1, 0, 0, 0)
MAX_MEMBERS = 1024
MAX_MEMBER_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")


class ZipJobRefusal(RuntimeError):
    def __init__(self, reason_code: str, detail: str = "") -> None:
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)
        self.reason_code = reason_code
        self.detail = detail


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ZipJobRefusal("REFUSE_NON_CANONICAL_JSON", str(exc)) from exc


def strict_json_loads(data: bytes, *, label: str) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non_finite_number:{value}")

    try:
        return json.loads(data.decode("utf-8"), parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ZipJobRefusal("REFUSE_INVALID_JSON", f"{label}:{exc}") from exc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def runtime_source_sha256() -> str:
    package_root = Path(__file__).resolve().parent
    registry = {
        f"constraintbox_zip_agent/{path.name}": sha256_bytes(path.read_bytes())
        for path in sorted(package_root.glob("*.py"), key=lambda item: item.name)
    }
    adapter_root = package_root.parents[3] / "src" / "constraintbox"
    for name in (
        "claude_bridge_adapter.py",
        "codex_cli_adapter.py",
        "grok_cli_adapter.py",
    ):
        origin = adapter_root / name
        if origin.is_file():
            registry[f"constraintbox/{name}"] = sha256_bytes(origin.read_bytes())
    return sha256_bytes(canonical_json_bytes(registry))


def validate_member_path(path: str, *, output: bool = False) -> str:
    if not isinstance(path, str) or not path:
        raise ZipJobRefusal("REFUSE_UNSAFE_PATH", repr(path))
    if "\\" in path or "\x00" in path or path.startswith("/"):
        raise ZipJobRefusal("REFUSE_UNSAFE_PATH", path)
    pure = PurePosixPath(path)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ZipJobRefusal("REFUSE_UNSAFE_PATH", path)
    if ":" in pure.parts[0] or pure.as_posix() != path:
        raise ZipJobRefusal("REFUSE_UNSAFE_PATH", path)
    if output and not path.startswith("output/"):
        raise ZipJobRefusal("REFUSE_OUTPUT_OUTSIDE_OUTPUT_ROOT", path)
    return path


class TaskSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    schema_: Literal["constraintbox.zip_task.v1"] = Field(alias="schema")
    task_id: str
    sequence: int = Field(ge=0, le=31)
    operation: str
    input_paths: list[str] = Field(min_length=1, max_length=512)
    output_paths: list[str] = Field(min_length=1, max_length=512)
    depends_on: list[str] = Field(default_factory=list, max_length=31)
    parameters: dict[str, Any] = Field(default_factory=dict)
    preload_files: list[str] = Field(default_factory=list, max_length=9)

    @field_validator("task_id", "operation")
    @classmethod
    def valid_id(cls, value: str) -> str:
        if not ID_RE.fullmatch(value):
            raise ValueError("invalid identifier")
        return value

    @field_validator("input_paths", "preload_files")
    @classmethod
    def valid_inputs(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate path")
        return [validate_member_path(value) for value in values]

    @field_validator("output_paths")
    @classmethod
    def valid_outputs(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate path")
        return [validate_member_path(value, output=True) for value in values]

    @field_validator("depends_on")
    @classmethod
    def valid_dependencies(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate dependency")
        if any(not ID_RE.fullmatch(value) for value in values):
            raise ValueError("invalid dependency")
        return values


class ZipJobManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    schema_: Literal["constraintbox.zip_job.v1"] = Field(alias="schema")
    job_id: str
    task_execution_order: list[str] = Field(min_length=1, max_length=32)
    required_output_file_list: list[str] = Field(min_length=1, max_length=512)
    file_sha256_registry: dict[str, str] = Field(min_length=2, max_length=1023)
    allowed_operations: list[str] = Field(min_length=1, max_length=16)
    allowed_child_job_ids: list[str] = Field(default_factory=list, max_length=256)
    max_child_depth: int = Field(default=0, ge=0, le=4)
    claim_ceiling: Literal[
        "local_deterministic_zip_execution_only;not_model_execution;not_admission;not_release",
        "local_zip_execution_with_one_provider_subprocess;not_admission;not_release",
        "local_zip_execution_with_declared_md_agents;not_admission;not_release",
        "local_zip_execution_with_declared_md_agents;not_host_hook;not_mmm_read;not_skill_exec;not_admission;not_release",
        "local_prompt_confirm_only;not_execution;not_admission;not_release",
        "local_separate_execute_only;not_confirm;not_admission;not_release",
        "append_only_project_memory;not_admission;not_release",
        "local_append_only_map_observation;not_producer_authenticity;not_tool_rank;not_admission;not_release",
        "contained-Light Mini-Lev polynomial operation and bounded role/order observations only;not core;not admission;not provider;not portability;not release;not semantic truth",
    ]

    @field_validator("job_id")
    @classmethod
    def valid_job_id(cls, value: str) -> str:
        if not ID_RE.fullmatch(value):
            raise ValueError("invalid job_id")
        return value

    @field_validator("task_execution_order")
    @classmethod
    def valid_task_paths(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate task path")
        checked = [validate_member_path(value) for value in values]
        if any(not value.startswith("tasks/") or not value.endswith(".task.json") for value in checked):
            raise ValueError("task path must be tasks/*.task.json")
        return checked

    @field_validator("required_output_file_list")
    @classmethod
    def valid_required_outputs(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate required output")
        return [validate_member_path(value, output=True) for value in values]

    @field_validator("file_sha256_registry")
    @classmethod
    def valid_registry(cls, values: dict[str, str]) -> dict[str, str]:
        checked: dict[str, str] = {}
        for path, digest in values.items():
            checked[validate_member_path(path)] = digest
            if not SHA256_RE.fullmatch(digest):
                raise ValueError(f"invalid sha256:{path}")
        return checked

    @field_validator("allowed_operations", "allowed_child_job_ids")
    @classmethod
    def valid_ids(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate identifier")
        if any(not ID_RE.fullmatch(value) for value in values):
            raise ValueError("invalid identifier")
        return values


class ZipReturnManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    schema_: Literal["constraintbox.zip_return.v1"] = Field(alias="schema")
    job_id: str
    input_packet_sha256: str
    runtime_source_sha256: str
    task_execution_order: list[str] = Field(min_length=1, max_length=32)
    required_output_file_list: list[str] = Field(min_length=1, max_length=512)
    file_sha256_registry: dict[str, str] = Field(min_length=2, max_length=1023)
    disposition: Literal["ZIP_JOB_EXECUTED_LOCAL"]
    claim_ceiling: str

    @field_validator("job_id")
    @classmethod
    def valid_return_job_id(cls, value: str) -> str:
        if not ID_RE.fullmatch(value):
            raise ValueError("invalid job_id")
        return value

    @field_validator("input_packet_sha256", "runtime_source_sha256")
    @classmethod
    def valid_input_digest(cls, value: str) -> str:
        if not SHA256_RE.fullmatch(value):
            raise ValueError("invalid input digest")
        return value

    @field_validator("required_output_file_list")
    @classmethod
    def valid_return_outputs(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate required output")
        return [validate_member_path(value, output=True) for value in values]

    @field_validator("file_sha256_registry")
    @classmethod
    def valid_return_registry(cls, values: dict[str, str]) -> dict[str, str]:
        for path, digest in values.items():
            validate_member_path(path)
            if not SHA256_RE.fullmatch(digest):
                raise ValueError(f"invalid sha256:{path}")
        return values


class ZipTaskReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    schema_: Literal["constraintbox.zip_task_receipt.v1"] = Field(alias="schema")
    task_id: str
    sequence: int = Field(ge=0, le=31)
    operation: str
    depends_on: list[str]
    input_sha256: dict[str, str]
    preload_sha256: dict[str, str]
    output_sha256: dict[str, str]
    disposition: Literal["TASK_EXECUTED_LOCAL"]
    claim_ceiling: str


@dataclass(frozen=True)
class ValidatedPacket:
    packet_sha256: str
    manifest: ZipJobManifest
    members: dict[str, bytes]
    tasks: tuple[TaskSpec, ...]


def _read_zip(packet_bytes: bytes) -> dict[str, bytes]:
    if not packet_bytes:
        raise ZipJobRefusal("REFUSE_EMPTY_PACKET")
    members: dict[str, bytes] = {}
    total = 0
    try:
        with zipfile.ZipFile(io.BytesIO(packet_bytes), "r") as archive:
            infos = archive.infolist()
            if len(infos) > MAX_MEMBERS:
                raise ZipJobRefusal("REFUSE_MEMBER_LIMIT", str(len(infos)))
            for info in infos:
                path = validate_member_path(info.filename)
                if info.is_dir():
                    raise ZipJobRefusal("REFUSE_DIRECTORY_MEMBER", path)
                if path in members:
                    raise ZipJobRefusal("REFUSE_DUPLICATE_MEMBER", path)
                if info.flag_bits & 0x1:
                    raise ZipJobRefusal("REFUSE_ENCRYPTED_MEMBER", path)
                mode = (info.external_attr >> 16) & 0o170000
                if mode not in {0, stat.S_IFREG}:
                    raise ZipJobRefusal("REFUSE_NON_REGULAR_MEMBER", path)
                if info.file_size > MAX_MEMBER_BYTES:
                    raise ZipJobRefusal("REFUSE_MEMBER_SIZE_LIMIT", path)
                total += info.file_size
                if total > MAX_TOTAL_BYTES:
                    raise ZipJobRefusal("REFUSE_TOTAL_SIZE_LIMIT", str(total))
                if info.file_size > 65536 and info.compress_size and info.file_size / info.compress_size > 100:
                    raise ZipJobRefusal("REFUSE_COMPRESSION_RATIO", path)
                members[path] = archive.read(info)
        if deterministic_zip(members) != packet_bytes:
            raise ZipJobRefusal("REFUSE_NON_CANONICAL_ZIP")
    except ZipJobRefusal:
        raise
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise ZipJobRefusal("REFUSE_INVALID_ZIP", str(exc)) from exc
    return members


def _parse_model(model: type[BaseModel], raw: Any, *, label: str) -> BaseModel:
    schema = model.model_json_schema()
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(raw), key=lambda error: list(error.path))
    if errors:
        detail = f"{label}:{errors[0].json_path}:{errors[0].message}"
        raise ZipJobRefusal("REFUSE_SCHEMA_INVALID", detail)
    try:
        return model.model_validate(raw, strict=True)
    except ValidationError as exc:
        raise ZipJobRefusal("REFUSE_TYPED_MODEL_INVALID", f"{label}:{exc.errors()[0]}") from exc


def validate_packet(packet_bytes: bytes, *, known_operations: set[str] | None = None) -> ValidatedPacket:
    members = _read_zip(packet_bytes)
    if MANIFEST_PATH not in members:
        raise ZipJobRefusal("REFUSE_MANIFEST_MISSING")
    raw_manifest = strict_json_loads(members[MANIFEST_PATH], label=MANIFEST_PATH)
    if not isinstance(raw_manifest, dict):
        raise ZipJobRefusal("REFUSE_SCHEMA_INVALID", "manifest_not_object")
    manifest = _parse_model(ZipJobManifest, raw_manifest, label=MANIFEST_PATH)
    assert isinstance(manifest, ZipJobManifest)

    actual_paths = set(members) - {MANIFEST_PATH}
    registered_paths = set(manifest.file_sha256_registry)
    if actual_paths != registered_paths:
        missing = sorted(actual_paths - registered_paths)
        extra = sorted(registered_paths - actual_paths)
        raise ZipJobRefusal("REFUSE_FILE_REGISTRY_SET_MISMATCH", f"unregistered={missing};missing={extra}")
    for path in sorted(actual_paths):
        if sha256_bytes(members[path]) != manifest.file_sha256_registry[path]:
            raise ZipJobRefusal("REFUSE_FILE_DIGEST_MISMATCH", path)

    if not set(manifest.task_execution_order).issubset(actual_paths):
        raise ZipJobRefusal("REFUSE_TASK_FILE_MISSING")
    tasks: list[TaskSpec] = []
    seen_ids: set[str] = set()
    produced: set[str] = set()
    task_outputs: set[str] = set()
    used_operations: set[str] = set()
    for sequence, path in enumerate(manifest.task_execution_order):
        raw_task = strict_json_loads(members[path], label=path)
        task = _parse_model(TaskSpec, raw_task, label=path)
        assert isinstance(task, TaskSpec)
        if task.sequence != sequence:
            raise ZipJobRefusal("REFUSE_TASK_SEQUENCE_MISMATCH", path)
        if task.task_id in seen_ids:
            raise ZipJobRefusal("REFUSE_DUPLICATE_TASK_ID", task.task_id)
        if not set(task.depends_on).issubset(seen_ids):
            raise ZipJobRefusal("REFUSE_FORWARD_OR_UNKNOWN_DEPENDENCY", task.task_id)
        available = actual_paths | produced
        for input_path in task.input_paths + task.preload_files:
            if input_path not in available:
                raise ZipJobRefusal("REFUSE_TASK_INPUT_UNAVAILABLE", f"{task.task_id}:{input_path}")
        if set(task.output_paths) & (actual_paths | produced):
            raise ZipJobRefusal("REFUSE_OUTPUT_ALIAS", task.task_id)
        seen_ids.add(task.task_id)
        produced.update(task.output_paths)
        task_outputs.update(task.output_paths)
        used_operations.add(task.operation)
        tasks.append(task)

    if task_outputs != set(manifest.required_output_file_list):
        raise ZipJobRefusal("REFUSE_REQUIRED_OUTPUT_SET_MISMATCH")
    if used_operations != set(manifest.allowed_operations):
        raise ZipJobRefusal("REFUSE_OPERATION_DECLARATION_MISMATCH")
    if known_operations is not None:
        unknown = sorted(used_operations - known_operations)
        if unknown:
            raise ZipJobRefusal("REFUSE_OPERATION_NOT_IMPLEMENTED", ",".join(unknown))

    return ValidatedPacket(
        packet_sha256=sha256_bytes(packet_bytes),
        manifest=manifest,
        members=members,
        tasks=tuple(tasks),
    )


def deterministic_zip(entries: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(entries):
            validate_member_path(path)
            info = zipfile.ZipInfo(path, date_time=FIXED_ZIP_DATETIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.create_system = 3
            archive.writestr(info, entries[path])
    return out.getvalue()


def build_packet(manifest_fields: dict[str, Any], files: dict[str, bytes]) -> bytes:
    if MANIFEST_PATH in files:
        raise ValueError("manifest is generated")
    registry = {path: sha256_bytes(data) for path, data in sorted(files.items())}
    manifest = dict(manifest_fields)
    manifest["file_sha256_registry"] = registry
    _parse_model(ZipJobManifest, manifest, label=MANIFEST_PATH)
    entries = dict(files)
    entries[MANIFEST_PATH] = canonical_json_bytes(manifest)
    return deterministic_zip(entries)


def validate_return_zip(
    return_bytes: bytes,
    *,
    expected_input_sha256: str | None = None,
    input_packet_bytes: bytes | None = None,
    require_current_runtime: bool = True,
) -> ZipReturnManifest:
    members = _read_zip(return_bytes)
    manifest_path = "RETURN_MANIFEST.json"
    if manifest_path not in members:
        raise ZipJobRefusal("REFUSE_RETURN_MANIFEST_MISSING")
    raw = strict_json_loads(members[manifest_path], label=manifest_path)
    manifest = _parse_model(ZipReturnManifest, raw, label=manifest_path)
    assert isinstance(manifest, ZipReturnManifest)
    actual = set(members) - {manifest_path}
    registered = set(manifest.file_sha256_registry)
    if actual != registered:
        raise ZipJobRefusal("REFUSE_RETURN_REGISTRY_SET_MISMATCH")
    for path in sorted(actual):
        if sha256_bytes(members[path]) != manifest.file_sha256_registry[path]:
            raise ZipJobRefusal("REFUSE_RETURN_DIGEST_MISMATCH", path)
    outputs = {path for path in actual if path.startswith("output/")}
    if outputs != set(manifest.required_output_file_list):
        raise ZipJobRefusal("REFUSE_RETURN_OUTPUT_SET_MISMATCH")
    expected_receipts = {
        f"receipts/{sequence:02d}_{task_id}.json"
        for sequence, task_id in enumerate(manifest.task_execution_order)
    }
    receipts = {path for path in actual if path.startswith("receipts/")}
    if receipts != expected_receipts or actual != outputs | receipts:
        raise ZipJobRefusal("REFUSE_RETURN_RECEIPT_SET_MISMATCH")
    parsed_receipts: list[ZipTaskReceipt] = []
    for path in sorted(receipts):
        raw_receipt = strict_json_loads(members[path], label=path)
        receipt = _parse_model(ZipTaskReceipt, raw_receipt, label=path)
        assert isinstance(receipt, ZipTaskReceipt)
        parsed_receipts.append(receipt)
    for sequence, receipt in enumerate(parsed_receipts):
        if receipt.sequence != sequence or receipt.task_id != manifest.task_execution_order[sequence]:
            raise ZipJobRefusal("REFUSE_RETURN_TASK_RECEIPT_ORDER_MISMATCH")
    if expected_input_sha256 is not None and manifest.input_packet_sha256 != expected_input_sha256:
        raise ZipJobRefusal("REFUSE_RETURN_INPUT_BINDING_MISMATCH")
    if require_current_runtime and manifest.runtime_source_sha256 != runtime_source_sha256():
        raise ZipJobRefusal("HOLD_RETURN_RUNTIME_SOURCE_DRIFT")
    if input_packet_bytes is not None:
        from .operation_ids import KNOWN_OPERATION_IDS

        packet = validate_packet(input_packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
        if packet.packet_sha256 != manifest.input_packet_sha256 or packet.manifest.job_id != manifest.job_id:
            raise ZipJobRefusal("REFUSE_RETURN_INPUT_BINDING_MISMATCH")
        if [task.task_id for task in packet.tasks] != manifest.task_execution_order:
            raise ZipJobRefusal("REFUSE_RETURN_TASK_ORDER_MISMATCH")
        available_digests = dict(packet.manifest.file_sha256_registry)
        for task, receipt in zip(packet.tasks, parsed_receipts, strict=True):
            if receipt.operation != task.operation or receipt.depends_on != task.depends_on:
                raise ZipJobRefusal("REFUSE_RETURN_TASK_RECEIPT_BINDING_MISMATCH", task.task_id)
            if set(receipt.input_sha256) != set(task.input_paths):
                raise ZipJobRefusal("REFUSE_RETURN_TASK_RECEIPT_BINDING_MISMATCH", task.task_id)
            if set(receipt.preload_sha256) != set(task.preload_files):
                raise ZipJobRefusal("REFUSE_RETURN_TASK_RECEIPT_BINDING_MISMATCH", task.task_id)
            for path in task.input_paths + task.preload_files:
                observed = receipt.input_sha256.get(path) or receipt.preload_sha256.get(path)
                if observed != available_digests.get(path):
                    raise ZipJobRefusal("REFUSE_RETURN_TASK_RECEIPT_BINDING_MISMATCH", task.task_id)
            if set(receipt.output_sha256) != set(task.output_paths):
                raise ZipJobRefusal("REFUSE_RETURN_TASK_RECEIPT_BINDING_MISMATCH", task.task_id)
            for path in task.output_paths:
                if receipt.output_sha256[path] != manifest.file_sha256_registry[path]:
                    raise ZipJobRefusal("REFUSE_RETURN_TASK_RECEIPT_BINDING_MISMATCH", task.task_id)
                available_digests[path] = receipt.output_sha256[path]
    return manifest
