"""Build and verify one provider-backed worker as a nested ZIP_JOB.

The builder is deliberately model agnostic.  Provider, model, runner, MMMs,
and task material are caller-supplied run data.  CB turns those exact bytes
into a child roster packet, nests it under one parent packet, and later
verifies both return layers. The worker never writes an authoritative CB
receipt. Output delivery is explicit run data: legacy workers may write the
declared temporary file, while read-only providers may return response bytes
that CB materializes into that same declared file before applying its gates.
"""

from __future__ import annotations

import argparse
import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .failure_wave import _task
from .md_agent_roster import build_md_agent_roster_packet
from .operation_ids import KNOWN_OPERATION_IDS
from .protocol import (
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    sha256_bytes,
    strict_json_loads,
    validate_packet,
    validate_return_zip,
)

BUILD_SCHEMA = "constraintbox.single-provider-child-build.v1"
RESULT_SCHEMA = "constraintbox.single-provider-child-result.v1"
MARKER = "CB_SINGLE_PROVIDER_CHILD_RESULT_V1"
CHILD_JOB_ID = "md-agent-roster"
CHILD_PACKET_PATH = "children/md-agent-roster.zip"
CHILD_RETURN_PATH = "output/child.return.zip"
WORKER_OUTPUT_PATH = "output/worker.md"
ROSTER_RECEIPT_PATH = "output/roster_receipt.json"
CLAIM_CEILING = (
    "one local provider observation through one nested ZIP; exact delivered bytes, "
    "provider-adapter receipt, declared output, and return bindings only; not semantic "
    "correctness, MMM comprehension, host-wide enforcement, promotion, or portability"
)
MANIFEST_CLAIM_CEILING = (
    "local_zip_execution_with_declared_md_agents;not_host_hook;not_mmm_read;"
    "not_skill_exec;not_admission;not_release"
)


class ProviderRoute(BaseModel):
    """Run-data fields understood by the existing Markdown roster adapter."""

    model_config = ConfigDict(extra="forbid", strict=True)

    provider: str = Field(min_length=1, max_length=64)
    model_requested: str | None = Field(default=None, max_length=160)
    fixture_script: str | None = None
    reasoning_effort: str | None = Field(default=None, max_length=32)
    budget_usd: float | None = Field(default=None, ge=0.01, le=5.0)
    max_turns: int | None = Field(default=None, ge=1, le=64)
    runner_path: str | None = Field(default=None, max_length=4096)
    bridge_path: str | None = Field(default=None, max_length=4096)
    codex_home: str | None = Field(default=None, max_length=4096)
    controller_src: str | None = Field(default=None, max_length=4096)
    output_delivery: Literal["workspace_file", "provider_response"] = "workspace_file"


class SingleProviderChildBuild(BaseModel):
    """Strict file-backed build request; source paths are not authority claims."""

    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    schema_: Literal[BUILD_SCHEMA] = Field(alias="schema")
    parent_job_id: str
    run_id: str
    wave_id: str
    round: int = Field(ge=0, le=1_000_000)
    seed: int = Field(ge=0, le=2**63 - 1)
    timeout_seconds: int = Field(default=180, ge=1, le=600)
    max_attempts: int = Field(default=2, ge=1, le=5)
    owner_prompt_path: str = Field(min_length=1, max_length=4096)
    agent_instruction_path: str = Field(min_length=1, max_length=4096)
    skill_path: str = Field(min_length=1, max_length=4096)
    mmm_paths: list[str] = Field(min_length=1, max_length=9)
    route: ProviderRoute
    required_fragments: list[str] = Field(default_factory=list, max_length=16)
    forbidden_fragments: list[str] = Field(default_factory=list, max_length=16)

    @field_validator("parent_job_id", "run_id", "wave_id")
    @classmethod
    def nonempty_identity(cls, value: str) -> str:
        if not value.strip() or len(value) > 96:
            raise ValueError("invalid identity")
        return value

    @field_validator("mmm_paths")
    @classmethod
    def distinct_mmm_paths(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)) or any(not value for value in values):
            raise ValueError("duplicate or empty MMM path")
        return values

    @field_validator("required_fragments", "forbidden_fragments")
    @classmethod
    def bounded_fragments(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate fragment")
        if any(not value or len(value.encode("utf-8")) > 4096 for value in values):
            raise ValueError("invalid fragment")
        return values


@dataclass(frozen=True)
class SingleProviderChildPacket:
    packet_bytes: bytes
    child_packet_bytes: bytes
    parent_job_id: str
    run_id: str
    provider: str
    model_requested: str | None

    @property
    def packet_sha256(self) -> str:
        return sha256_bytes(self.packet_bytes)

    @property
    def child_packet_sha256(self) -> str:
        return sha256_bytes(self.child_packet_bytes)


@dataclass(frozen=True)
class SingleProviderChildResult:
    summary: dict[str, Any]
    worker_output: bytes
    roster_receipt: dict[str, Any]
    child_return_bytes: bytes


def _read_source(path_value: str, *, label: str) -> bytes:
    path = Path(path_value).expanduser()
    if not path.is_absolute() or not path.is_file():
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_SOURCE", label)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_SOURCE", label) from exc
    if not data or len(data) > 2 * 1024 * 1024:
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_SOURCE", label)
    return data


def _zip_entries(data: bytes) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
            return {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_RETURN_ZIP") from exc


def _route_row(route: ProviderRoute) -> dict[str, Any]:
    return {
        key: value
        for key, value in route.model_dump(mode="python").items()
        if value is not None
    }


def build_single_provider_child_packet(
    request: SingleProviderChildBuild,
) -> SingleProviderChildPacket:
    """Build a deterministic parent -> one provider-backed child ZIP tree."""

    owner_prompt = _read_source(request.owner_prompt_path, label="owner_prompt_path")
    agent_instruction = _read_source(
        request.agent_instruction_path, label="agent_instruction_path"
    )
    skill = _read_source(request.skill_path, label="skill_path")
    mmm_bytes = [
        _read_source(path, label=f"mmm_paths[{index}]")
        for index, path in enumerate(request.mmm_paths)
    ]

    mmm_packet_paths = [f"MMMS/{index:02d}.md" for index in range(len(mmm_bytes))]
    mmm_sha256 = [sha256_bytes(data) for data in mmm_bytes]
    skill_sha256 = sha256_bytes(skill)
    required = [
        "status: OBSERVATION",
        "evidence:",
        "limits:",
        "next:",
        f"skill-token: {skill_sha256}",
        *(f"mmm-token: {digest}" for digest in mmm_sha256),
        *request.required_fragments,
    ]
    if len(set(required)) != len(required):
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_BUILD", "duplicate_required_fragment")

    source_rows = [
        {
            "kind": "owner_prompt",
            "packet_path": "input/OWNER_PROMPT.bin",
            "sha256": sha256_bytes(owner_prompt),
            "bytes": len(owner_prompt),
        },
        {
            "kind": "agent_instruction",
            "packet_path": "AGENTS/worker.md",
            "sha256": sha256_bytes(agent_instruction),
            "bytes": len(agent_instruction),
        },
        {
            "kind": "skill",
            "packet_path": "SKILLS/task.md",
            "sha256": skill_sha256,
            "bytes": len(skill),
        },
        *(
            {
                "kind": "mini_mmm",
                "packet_path": packet_path,
                "sha256": digest,
                "bytes": len(data),
            }
            for packet_path, digest, data in zip(
                mmm_packet_paths, mmm_sha256, mmm_bytes, strict=True
            )
        ),
    ]
    build_record = {
        "schema": "constraintbox.single-provider-child-build-record.v1",
        "parent_job_id": request.parent_job_id,
        "child_job_id": CHILD_JOB_ID,
        "run_id": request.run_id,
        "wave_id": request.wave_id,
        "round": request.round,
        "seed": request.seed,
        "provider": request.route.provider,
        "model_requested": request.route.model_requested,
        "output_delivery": request.route.output_delivery,
        "source_rows": source_rows,
        "required_fragments": required,
        "forbidden_fragments": request.forbidden_fragments,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    child_files = {
        "AGENTS/worker.md": agent_instruction,
        "SKILLS/task.md": skill,
        "input/OWNER_PROMPT.bin": owner_prompt,
        "input/SINGLE_PROVIDER_BUILD_RECORD.json": canonical_json_bytes(build_record),
        **{
            path: data
            for path, data in zip(mmm_packet_paths, mmm_bytes, strict=True)
        },
    }
    agent = {
        "agent_id": "worker",
        "agent_path": "AGENTS/worker.md",
        "output_path": WORKER_OUTPUT_PATH,
        "mmm_paths": mmm_packet_paths,
        "skill_paths": ["SKILLS/task.md"],
        "context_paths": ["input/OWNER_PROMPT.bin"],
        "required_fragments": required,
        "forbidden_fragments": request.forbidden_fragments,
        "max_output_bytes": 262_144,
        **_route_row(request.route),
    }
    roster = {
        "schema": "constraintbox.md-agent-roster.v1",
        "run_id": request.run_id,
        "seed": request.seed,
        "required_marker": MARKER,
        "max_attempts": request.max_attempts,
        "timeout_seconds": request.timeout_seconds,
        "max_workers": 1,
        # Route/model data stays in the packet's build record for CB custody,
        # but is not delivered to the model. This keeps paired-provider prompt
        # bytes identical when task, MMM, skill, identity, and attempt match.
        "shared_paths": [],
        "agents": [agent],
        "parent_id": request.parent_job_id,
        "wave_id": request.wave_id,
        "round": request.round,
        "depth": 1,
    }
    child_packet = build_md_agent_roster_packet(roster=roster, files=child_files)

    task_path = "tasks/00_run_child.task.json"
    parent_packet = build_packet(
        {
            "schema": "constraintbox.zip_job.v1",
            "job_id": request.parent_job_id,
            "task_execution_order": [task_path],
            "required_output_file_list": [CHILD_RETURN_PATH],
            "allowed_operations": ["run_child_zip_v1"],
            "allowed_child_job_ids": [CHILD_JOB_ID],
            "max_child_depth": 1,
            "claim_ceiling": MANIFEST_CLAIM_CEILING,
        },
        {
            "00_RUN_ME_FIRST.md": (
                b"CB validates and runs the declared child packet. "
                b"Only the nested return ZIP is authoritative.\n"
            ),
            "input/SINGLE_PROVIDER_BUILD_RECORD.json": canonical_json_bytes(build_record),
            CHILD_PACKET_PATH: child_packet,
            task_path: _task(
                task_id="run-provider-child",
                sequence=0,
                operation="run_child_zip_v1",
                inputs=[CHILD_PACKET_PATH],
                outputs=[CHILD_RETURN_PATH],
            ),
        },
    )
    return SingleProviderChildPacket(
        packet_bytes=parent_packet,
        child_packet_bytes=child_packet,
        parent_job_id=request.parent_job_id,
        run_id=request.run_id,
        provider=request.route.provider,
        model_requested=request.route.model_requested,
    )


def validate_single_provider_child_return(
    packet_bytes: bytes,
    return_bytes: bytes,
) -> SingleProviderChildResult:
    """Verify parent and child returns, then expose the declared worker file."""

    parent = validate_packet(packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    if (
        parent.manifest.allowed_child_job_ids != [CHILD_JOB_ID]
        or parent.manifest.required_output_file_list != [CHILD_RETURN_PATH]
        or parent.manifest.allowed_operations != ["run_child_zip_v1"]
    ):
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_PARENT_SHAPE")
    validate_return_zip(return_bytes, input_packet_bytes=packet_bytes)
    parent_entries = _zip_entries(return_bytes)
    child_return = parent_entries.get(CHILD_RETURN_PATH)
    child_packet = parent.members.get(CHILD_PACKET_PATH)
    if child_return is None or child_packet is None:
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_CHILD_MISSING")
    validate_return_zip(child_return, input_packet_bytes=child_packet)
    child_entries = _zip_entries(child_return)
    worker_output = child_entries.get(WORKER_OUTPUT_PATH)
    roster_raw = child_entries.get(ROSTER_RECEIPT_PATH)
    if worker_output is None or roster_raw is None:
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_OUTPUT_MISSING")
    roster_value = strict_json_loads(roster_raw, label=ROSTER_RECEIPT_PATH)
    if not isinstance(roster_value, dict):
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_ROSTER_RECEIPT")
    agents = roster_value.get("agents")
    if (
        roster_value.get("accepted_agent_ids") != ["worker"]
        or not isinstance(agents, list)
        or len(agents) != 1
        or not isinstance(agents[0], dict)
        or agents[0].get("accepted") is not True
    ):
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_ROSTER_RECEIPT")
    agent = agents[0]
    summary = {
        "schema": RESULT_SCHEMA,
        "parent_job_id": parent.manifest.job_id,
        "parent_packet_sha256": parent.packet_sha256,
        "parent_return_sha256": sha256_bytes(return_bytes),
        "child_packet_sha256": sha256_bytes(child_packet),
        "child_return_sha256": sha256_bytes(child_return),
        "provider": agent.get("provider"),
        "model_requested": agent.get("model_requested"),
        "model_observed": agent.get("models_observed"),
        "model_binding_confirmed": agent.get("model_binding_confirmed"),
        "accepted_attempt": agent.get("accepted_attempt"),
        "worker_output_sha256": sha256_bytes(worker_output),
        "worker_output_bytes": len(worker_output),
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    return SingleProviderChildResult(
        summary=summary,
        worker_output=worker_output,
        roster_receipt=roster_value,
        child_return_bytes=child_return,
    )


def load_build_request(path: Path) -> SingleProviderChildBuild:
    try:
        raw = strict_json_loads(path.read_bytes(), label=str(path))
        return SingleProviderChildBuild.model_validate(raw)
    except OSError as exc:
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_BUILD", str(path)) from exc
    except ValidationError as exc:
        raise ZipJobRefusal("REFUSE_SINGLE_PROVIDER_BUILD", str(exc)) from exc


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cb-single-provider-child")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--contract", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("--packet", required=True, type=Path)
    verify.add_argument("--return-zip", required=True, type=Path)
    verify.add_argument("--summary", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            built = build_single_provider_child_packet(load_build_request(args.contract))
            _atomic_write(args.output, built.packet_bytes)
            result = {
                "schema": "constraintbox.single-provider-child-build-result.v1",
                "packet": str(args.output.resolve()),
                "packet_sha256": built.packet_sha256,
                "child_packet_sha256": built.child_packet_sha256,
                "provider": built.provider,
                "model_requested": built.model_requested,
                "claim_ceiling": CLAIM_CEILING,
                "promotion_allowed": False,
            }
        else:
            packet_bytes = args.packet.read_bytes()
            return_bytes = args.return_zip.read_bytes()
            verified = validate_single_provider_child_return(packet_bytes, return_bytes)
            result = verified.summary
            if args.summary is not None:
                _atomic_write(args.summary, canonical_json_bytes(result) + b"\n")
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, ZipJobRefusal) as exc:
        reason = exc.reason_code if isinstance(exc, ZipJobRefusal) else "REFUSE_SINGLE_PROVIDER_IO"
        detail = exc.detail if isinstance(exc, ZipJobRefusal) else str(exc)
        print(
            json.dumps(
                {
                    "schema": "constraintbox.single-provider-child-refusal.v1",
                    "disposition": "REFUSE",
                    "reason_code": reason,
                    "detail": detail,
                    "promotion_allowed": False,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "BUILD_SCHEMA",
    "CLAIM_CEILING",
    "MARKER",
    "SingleProviderChildBuild",
    "SingleProviderChildPacket",
    "SingleProviderChildResult",
    "build_single_provider_child_packet",
    "load_build_request",
    "validate_single_provider_child_return",
]
