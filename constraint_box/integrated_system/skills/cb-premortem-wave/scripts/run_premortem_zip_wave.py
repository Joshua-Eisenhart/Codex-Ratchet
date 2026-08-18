#!/usr/bin/env python3
"""Build, execute, and verify one ZIP-native premortem wave.

This module is deliberately a candidate runner.  It composes the existing
ZIP_JOB and Markdown-agent roster operations; it does not fan out provider
adapters itself.  Provider/model rows, route paths, and budgets are run data.
The runner's only semantic work is structural validation and preservation of
disagreement.  It never votes for a finding or grants authority.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from constraintbox_zip_agent.failure_wave import _task
from constraintbox_zip_agent.md_agent_roster import (
    CLAIM_CEILING as ROSTER_MANIFEST_CLAIM_CEILING,
    PREMORTEM_CELL_FIELDS,
    RECEIPT_SCHEMA,
    ROSTER_RECEIPT_FIELDS,
    _roster_receipt_field_set,
    build_md_agent_roster_packet,
)
from constraintbox_zip_agent.operation_ids import KNOWN_OPERATION_IDS
from constraintbox_zip_agent.protocol import (
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    deterministic_zip,
    sha256_bytes,
    strict_json_loads,
    validate_packet,
    validate_return_zip,
)
from constraintbox_zip_agent.runtime import execute_packet


CONFIG_SCHEMA = "constraintbox.premortem-zip-wave-run.v1"
WAVE_SCHEMA = "constraintbox.premortem-zip-wave.v1"
CELL_SCHEMA = "constraintbox.premortem-cell-result.v1"
ROSTER_SCHEMA = "constraintbox.md-agent-roster.v1"
OUTPUT_DELIVERY = "provider_response"
LENSES = ("likely_failure", "dangerous_failure", "hidden_assumption")
STOP_REASONS = (
    "no_material_delta",
    "repair_callback_absent",
    "falsifiers_settled",
    "cancelled",
    "max_rounds",
    "provider_refused",
    "repair_callback_refused",
)
CLAIM_CEILING = (
    "bounded ZIP premortem observations with exact target, route, MMM, skill, "
    "ancestry, retry, and return bindings; not semantic consensus, authority, "
    "promotion, release, or proof of model comprehension"
)
_SAFE_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
_MAX_MODEL_OBSERVED_ALLOWLIST = 32
SKILL_ECHO_PREFIX = "skill_bytes_delivered_echo:"
MMM_ECHO_PREFIX = "mmm_bytes_delivered_echo:"
TOOL_ECHO_PREFIX = "tool_bytes_delivered_echo:"


def _skill_echo(path: str, digest: str) -> str:
    return f"{SKILL_ECHO_PREFIX}path={path};sha256={digest}"


def _mmm_echo(voice: str, path: str, digest: str) -> str:
    return f"{MMM_ECHO_PREFIX}voice={voice};path={path};sha256={digest}"


def _tool_echo(path: str, digest: str) -> str:
    return f"{TOOL_ECHO_PREFIX}path={path};canonical_sha256={digest}"


def _delivery_echo_status(
    cell: Mapping[str, Any],
    *,
    skill_path: str,
    skill_digest: str,
    mmm_digests: Mapping[str, str],
    tool_digest: str,
) -> dict[str, bool]:
    """Require exact labeled delivery echoes in the cell ``evidence`` array."""

    evidence = cell.get("evidence")
    if not isinstance(evidence, list) or any(
        not isinstance(item, str) for item in evidence
    ):
        raise ZipJobRefusal("REFUSE_PREMORTEM_DELIVERY_ECHO", "evidence")
    expected = {
        _skill_echo(skill_path, skill_digest),
        _tool_echo("output/tool_evidence.json", tool_digest),
        *{
            _mmm_echo(voice, f"MMMS/{voice}.md", digest)
            for voice, digest in mmm_digests.items()
        },
    }
    counts = {item: evidence.count(item) for item in expected}
    if any(count != 1 for count in counts.values()):
        raise ZipJobRefusal("REFUSE_PREMORTEM_DELIVERY_ECHO", "missing_or_duplicate")
    prefixes = (SKILL_ECHO_PREFIX, MMM_ECHO_PREFIX, TOOL_ECHO_PREFIX)
    if any(
        any(item.startswith(prefix) for prefix in prefixes) and item not in expected
        for item in evidence
    ):
        raise ZipJobRefusal("REFUSE_PREMORTEM_DELIVERY_ECHO", "unexpected_label")
    # An echo copied into another strict cell field is not an evidence entry.
    outside = {key: value for key, value in cell.items() if key != "evidence"}
    outside_text = _canonical(outside).decode("utf-8")
    if any(item in outside_text for item in expected):
        raise ZipJobRefusal("REFUSE_PREMORTEM_DELIVERY_ECHO", "echo_outside_evidence")
    return {
        "skill_echo_proved": True,
        "mmm_echo_proved": True,
        "tool_echo_proved": True,
    }


@dataclass(frozen=True)
class PremortemZipPacket:
    packet_bytes: bytes
    target_sha256: str
    child_job_ids: tuple[str, ...]
    mmm_combos: dict[str, tuple[str, ...]]

    @property
    def packet_sha256(self) -> str:
        return sha256_bytes(self.packet_bytes)


class PremortemConfigError(ZipJobRefusal):
    """Configuration was not admissible as run data."""


def _canonical(value: Any) -> bytes:
    return canonical_json_bytes(value)


def _object(raw: bytes, label: str) -> dict[str, Any]:
    value = strict_json_loads(raw, label=label)
    if not isinstance(value, dict):
        raise ZipJobRefusal("REFUSE_PREMORTEM_SCHEMA", label)
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ZipJobRefusal("REFUSE_PREMORTEM_SCHEMA", label)
    return value


def _bounded_int(value: object, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ZipJobRefusal("REFUSE_PREMORTEM_SCHEMA", label)
    return value


def _model_observed_allowlist(value: object, label: str) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not value or len(value) > _MAX_MODEL_OBSERVED_ALLOWLIST:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_SCHEMA", label)
    if any(not isinstance(item, str) or _SAFE_MODEL.fullmatch(item) is None for item in value):
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_SCHEMA", label)
    if len(value) != len(set(value)):
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_SCHEMA", label)
    return list(value)


def _bytes(value: object, label: str, *, maximum: int = 2 * 1024 * 1024) -> bytes:
    if not isinstance(value, (bytes, bytearray)):
        raise ZipJobRefusal("REFUSE_PREMORTEM_BYTES", label)
    raw = bytes(value)
    if not raw or len(raw) > maximum:
        raise ZipJobRefusal("REFUSE_PREMORTEM_BYTES", label)
    return raw


def _entries(data: bytes, *, label: str) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
            result: dict[str, bytes] = {}
            for info in archive.infolist():
                if info.is_dir() or info.filename in result:
                    raise ZipJobRefusal("REFUSE_PREMORTEM_ZIP_SHAPE", info.filename)
                result[info.filename] = archive.read(info)
            return result
    except ZipJobRefusal:
        raise
    except (OSError, RuntimeError, zipfile.BadZipFile, KeyError) as exc:
        raise ZipJobRefusal("REFUSE_PREMORTEM_ZIP_SHAPE", label) from exc


def _task_bytes(task_id: str, sequence: int, operation: str, inputs: list[str], outputs: list[str], depends_on: list[str] | None = None) -> bytes:
    return _canonical(
        {
            "schema": "constraintbox.zip_task.v1",
            "task_id": task_id,
            "sequence": sequence,
            "operation": operation,
            "input_paths": inputs,
            "output_paths": outputs,
            "depends_on": depends_on or [],
            "parameters": {},
            "preload_files": [],
        }
    )


def _validate_config(config: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(config)
    if value.get("schema") != CONFIG_SCHEMA:
        raise ZipJobRefusal("REFUSE_PREMORTEM_CONFIG", "schema")
    for field in ("parent_job_id", "run_id", "wave_id"):
        _text(value.get(field), field)
    _bounded_int(value.get("round"), "round", 0, 1_000_000)
    _bounded_int(value.get("seed"), "seed", 0, 2**63 - 1)
    max_rounds = _bounded_int(value.get("max_rounds", 1), "max_rounds", 1, 4)
    max_attempts = _bounded_int(value.get("max_attempts", 2), "max_attempts", 1, 5)
    # Normalize defaults into the checked run data so every downstream
    # manifest and validator binds the same retry ceiling.
    value["max_rounds"] = max_rounds
    value["max_attempts"] = max_attempts
    members = value.get("members")
    if not isinstance(members, dict) or set(members) != set(LENSES):
        raise ZipJobRefusal("REFUSE_PREMORTEM_LENS_ROSTER", "lenses")
    seen: set[str] = set()
    for lens in LENSES:
        rows = members[lens]
        if not isinstance(rows, list) or not 2 <= len(rows) <= 4:
            raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_COUNT", lens)
        for row in rows:
            if not isinstance(row, dict):
                raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_SCHEMA", lens)
            member_id = _text(row.get("member_id"), f"{lens}.member_id")
            if member_id in seen:
                raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_IDENTITY", member_id)
            seen.add(member_id)
            _text(row.get("provider"), f"{member_id}.provider")
            _text(row.get("model_requested"), f"{member_id}.model_requested")
            if "model_observed_allowlist" in row:
                row["model_observed_allowlist"] = _model_observed_allowlist(
                    row["model_observed_allowlist"], f"{member_id}.model_observed_allowlist"
                )
            if row.get("output_delivery") != OUTPUT_DELIVERY:
                raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", member_id)
            provider = row["provider"]
            if provider == "fixture-subprocess":
                _text(row.get("fixture_script"), f"{member_id}.fixture_script")
            elif provider not in {"codex-cli", "grok-cli", "claude-code"}:
                raise ZipJobRefusal("REFUSE_PREMORTEM_PROVIDER", str(provider))
    if not seen:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_COUNT", "empty")
    return value


def _select_combo(seed: int, lens: str, member_id: str, voices: list[str], salt: int = 0) -> tuple[str, ...]:
    if len(voices) < 2:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MMM_ASSIGNMENT", "fewer_than_two_sources")
    seed_bytes = f"{seed}:{lens}:{member_id}:mmm:{salt}".encode("utf-8")
    digest = hashlib.sha256(seed_bytes).digest()
    count = min(len(voices), 2 + digest[0] % 3)
    ordered = sorted(
        voices,
        key=lambda voice: hashlib.sha256(
            seed_bytes + b":" + voice.encode("utf-8")
        ).digest(),
    )
    return tuple(ordered[:count])


def _assign_combos(config: Mapping[str, Any], mmm_sources: Mapping[str, bytes]) -> dict[str, tuple[str, ...]]:
    voices = sorted(_text(key, "mmm_voice") for key in mmm_sources)
    if len(voices) > 9:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MMM_ASSIGNMENT", "more_than_nine_sources")
    used: set[tuple[str, ...]] = set()
    assigned: dict[str, tuple[str, ...]] = {}
    seed = int(config["seed"])
    for lens in LENSES:
        for row in config["members"][lens]:
            member_id = str(row["member_id"])
            combo: tuple[str, ...] = ()
            for salt in range(65):
                combo = _select_combo(seed, lens, member_id, voices, salt)
                if combo not in used:
                    break
            if not combo or combo in used:
                raise ZipJobRefusal("REFUSE_PREMORTEM_MMM_ASSIGNMENT", member_id)
            used.add(combo)
            assigned[f"{lens}:{member_id}"] = combo
    return assigned


def _agent_instruction(
    lens: str,
    member_id: str,
    target_digest: str,
    combo: tuple[str, ...],
    *,
    skill_path: str,
    skill_digest: str,
    mmm_digests: Mapping[str, str],
    tool_digest: str,
) -> bytes:
    echo_lines = [
        f"- {_skill_echo(skill_path, skill_digest)}",
        *[
            f"- {_mmm_echo(voice, f'MMMS/{voice}.md', digest)}"
            for voice, digest in mmm_digests.items()
        ],
        f"- {_tool_echo('output/tool_evidence.json', tool_digest)}",
    ]
    return (
        f"You are premortem member {member_id}. Assigned lens: {lens}.\n"
        "Read input/target.bin, input/lens_manifest.json, every assigned MMMS file, "
        "and SKILLS/cb-premortem-cell/SKILL.md before responding.\n"
        f"The target_sha256 must be exactly {target_digest}.\n"
        f"Your compact MMM combo is exactly: {', '.join(combo)}.\n"
        "Return ONLY one strict JSON object in the declared output channel. No "
        "markdown fence, preface, vote, promotion, or authority claim.\n"
        f"Required keys exactly: {', '.join(PREMORTEM_CELL_FIELDS)}.\n"
        "Use arrays of strings for failure_mechanisms, evidence, and limits. "
        "Keep rival findings separate; the parent preserves disagreement.\n"
        "The evidence array must contain each of these exact strings once; do "
        "not substitute unlabeled digests, put these strings in another field, "
        "duplicate them, or add any other *_echo label:\n"
        + "\n".join(echo_lines)
        + "\nThese are delivery echoes only; they do not prove reading, execution, "
        "comprehension, or semantic agreement.\n"
    ).encode("utf-8")


def _route_for_roster(row: Mapping[str, Any], *, output_path: str, agent_path: str, mmm_paths: list[str], skill_path: str, context_paths: list[str], required_fragments: list[str], config: Mapping[str, Any]) -> dict[str, Any]:
    """Translate candidate run data to the existing roster's run-data shape."""

    member = dict(row)
    member_id = _text(member.pop("member_id", None), "member_id")
    # This field is part of the roster's provider-response contract.  It must
    # survive into the child packet; silently dropping it would route the
    # worker through the legacy workspace-file path.
    member.pop("require_model_binding", None)
    member.update(
        {
            "agent_id": member_id,
            "agent_path": agent_path,
            "output_path": output_path,
            "mmm_paths": mmm_paths,
            "skill_paths": [skill_path],
            "context_paths": context_paths,
            "required_fragments": required_fragments,
            "forbidden_fragments": ["promotion_allowed: true", '"promotion_allowed":true'],
            "max_output_bytes": int(row.get("max_output_bytes") or 131072),
        }
    )
    member["output_delivery"] = OUTPUT_DELIVERY
    member["output_format"] = "strict_json_object"
    # These are deliberately not passed as provider policy.  The route and
    # output mode remain recorded in input/lens_manifest.json and verified
    # against the resulting receipt.
    return member


def _rename_packet_job(packet_bytes: bytes, job_id: str) -> bytes:
    entries = _entries(packet_bytes, label="child_packet")
    manifest = _object(entries.pop("ZIP_JOB_MANIFEST.json"), "ZIP_JOB_MANIFEST.json")
    manifest["job_id"] = job_id
    return build_packet(manifest, entries)


def _build_lens_packet(*, config: Mapping[str, Any], lens: str, target: bytes, skill: bytes, mmm_sources: Mapping[str, bytes], combos: Mapping[str, tuple[str, ...]]) -> tuple[bytes, dict[str, Any]]:
    target_digest = sha256_bytes(target)
    parent_id = str(config["parent_job_id"])
    wave_id = str(config["wave_id"])
    round_value = int(config["round"])
    max_attempts = int(config["max_attempts"])
    child_id = f"{parent_id}-{lens}"
    skill_path = "SKILLS/cb-premortem-cell/SKILL.md"
    delivery_path = "input/output_delivery.json"
    context_paths = ["input/target.bin", "input/lens_manifest.json", delivery_path]
    members_manifest: list[dict[str, Any]] = []
    files: dict[str, bytes] = {
        "input/target.bin": target,
        skill_path: skill,
        delivery_path: _canonical(
            {
                "schema": "constraintbox.output-delivery.v1",
                "output_delivery": OUTPUT_DELIVERY,
                "provider_response_required": True,
            }
        ),
    }
    agents: list[dict[str, Any]] = []
    for row in config["members"][lens]:
        member_id = str(row["member_id"])
        combo = combos[f"{lens}:{member_id}"]
        mmm_paths = [f"MMMS/{voice}.md" for voice in combo]
        mmm_digests: dict[str, str] = {}
        for voice in combo:
            path = f"MMMS/{voice}.md"
            raw = _bytes(mmm_sources[voice], path)
            files[path] = raw
            mmm_digests[voice] = sha256_bytes(raw)
        agent_path = f"AGENTS/{member_id}.md"
        output_path = f"output/{member_id}.md"
        files[agent_path] = _agent_instruction(
            lens,
            member_id,
            target_digest,
            combo,
            skill_path=skill_path,
            skill_digest=sha256_bytes(skill),
            mmm_digests=mmm_digests,
            tool_digest="<canonical_sha256 from output/tool_evidence.json>",
        )
        required = [
            '"schema"',
            f'"lens"',
            f'"target_sha256"',
            '"failure_mechanisms"',
            '"falsifier"',
            target_digest,
        ]
        agent = _route_for_roster(
            row,
            output_path=output_path,
            agent_path=agent_path,
            mmm_paths=mmm_paths,
            skill_path=skill_path,
            context_paths=context_paths,
            required_fragments=required,
            config=config,
        )
        agents.append(agent)
        members_manifest.append(
            {
                "member_id": member_id,
                "agent_path": agent_path,
                "output_path": output_path,
                "provider": row["provider"],
                "model_requested": row["model_requested"],
                "model_observed_allowlist": list(row["model_observed_allowlist"])
                if row.get("model_observed_allowlist") is not None
                else None,
                "model_binding_required": bool(row.get("require_model_binding", row["provider"] != "fixture-subprocess")),
                "output_delivery": OUTPUT_DELIVERY,
                "output_format": "strict_json_object",
                "mmm_ids": list(combo),
                "mmm_paths": mmm_paths,
                "mmm_sha256": mmm_digests,
                "skill_path": skill_path,
                "skill_sha256": sha256_bytes(skill),
            }
        )
    lens_manifest = {
        "schema": "constraintbox.premortem-lens-manifest.v1",
        "parent_id": parent_id,
        "parent_job_id": parent_id,
        "job_id": child_id,
        "wave_id": wave_id,
        "round": round_value,
        "depth": 1,
        "max_attempts": max_attempts,
        "lens": lens,
        "target_sha256": target_digest,
        "target_bytes": len(target),
        "output_delivery": OUTPUT_DELIVERY,
        "output_delivery_required": True,
        "output_delivery_binding": "run-data-and-return-verifier",
        "skill_sha256": sha256_bytes(skill),
        "members": members_manifest,
        "selection": {
            "algorithm": "cb-premortem-distinct-compact-combos-v1",
            "seed": int(config["seed"]),
            "distinct_within_wave": True,
        },
        "claim_ceiling": CLAIM_CEILING,
    }
    files["input/lens_manifest.json"] = _canonical(lens_manifest)
    roster = {
        "schema": ROSTER_SCHEMA,
        "run_id": f"{config['run_id']}-{lens}",
        "seed": int(config["seed"]),
        "required_marker": CELL_SCHEMA,
        "max_attempts": max_attempts,
        "timeout_seconds": int(config.get("timeout_seconds", 120)),
        "max_workers": len(agents),
        "shared_paths": context_paths,
        "agents": agents,
        "parent_id": parent_id,
        "wave_id": wave_id,
        "round": round_value,
        "depth": 1,
    }
    child = build_md_agent_roster_packet(roster=roster, files=files)
    child = _rename_packet_job(child, child_id)
    return child, lens_manifest


def build_premortem_zip_wave_packet(*, config: Mapping[str, Any], target: bytes, skill: bytes, mmm_sources: Mapping[str, bytes]) -> PremortemZipPacket:
    """Build a root ZIP_JOB containing one md-agent child per premortem lens."""

    checked = _validate_config(config)
    target_raw = _bytes(target, "target")
    skill_raw = _bytes(skill, "skill")
    if not isinstance(mmm_sources, Mapping) or not mmm_sources:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MMM_ASSIGNMENT", "empty_sources")
    source_bytes = {str(key): _bytes(raw, str(key)) for key, raw in mmm_sources.items()}
    combos = _assign_combos(checked, source_bytes)
    child_packets: dict[str, bytes] = {}
    child_manifests: dict[str, dict[str, Any]] = {}
    for lens in LENSES:
        child, lens_manifest = _build_lens_packet(
            config=checked,
            lens=lens,
            target=target_raw,
            skill=skill_raw,
            mmm_sources=source_bytes,
            combos=combos,
        )
        child_packets[lens] = child
        child_manifests[lens] = lens_manifest
    parent_id = str(checked["parent_job_id"])
    child_ids = tuple(f"{parent_id}-{lens}" for lens in LENSES)
    child_records = [
        {
            "job_id": child_ids[index],
            "lens": lens,
            "packet_path": f"children/{lens}.zip",
            "return_path": f"output/{lens}.return.zip",
            "packet_sha256": sha256_bytes(child_packets[lens]),
            "target_sha256": sha256_bytes(target_raw),
            "target_bytes": len(target_raw),
            "member_ids": [row["member_id"] for row in checked["members"][lens]],
            "depth": 1,
            "max_attempts": int(checked["max_attempts"]),
        }
        for index, lens in enumerate(LENSES)
    ]
    wave_manifest = {
        "schema": WAVE_SCHEMA,
        "parent_id": parent_id,
        "parent_job_id": parent_id,
        "run_id": checked["run_id"],
        "wave_id": checked["wave_id"],
        "round": checked["round"],
        "depth": 0,
        "max_attempts": int(checked["max_attempts"]),
        "target_sha256": sha256_bytes(target_raw),
        "target_bytes": len(target_raw),
        "output_delivery": OUTPUT_DELIVERY,
        "output_delivery_required": True,
        "lenses": child_records,
        "selection_algorithm": "cb-premortem-distinct-compact-combos-v1",
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    task_paths: list[str] = []
    files: dict[str, bytes] = {
        "00_RUN_ME_FIRST.md": (
            b"# ConstraintBox ZIP premortem wave\n\n"
            b"CB runs one declared child ZIP for each lens. The parent preserves "
            b"all child returns and never selects a semantic winner.\n"
        ),
        "inputs/target.bin": target_raw,
        "inputs/wave_manifest.json": _canonical(wave_manifest),
    }
    for index, lens in enumerate(LENSES):
        child_path = f"children/{lens}.zip"
        return_path = f"output/{lens}.return.zip"
        task_path = f"tasks/{index:02d}_{lens}.task.json"
        files[child_path] = child_packets[lens]
        files[task_path] = _task_bytes(
            f"run-{lens}", index, "run_child_zip_v1", [child_path], [return_path]
        )
        task_paths.append(task_path)
    parent_manifest = {
        "schema": "constraintbox.zip_job.v1",
        "job_id": parent_id,
        "task_execution_order": task_paths,
        "required_output_file_list": [f"output/{lens}.return.zip" for lens in LENSES],
        "allowed_operations": ["run_child_zip_v1"],
        "allowed_child_job_ids": list(child_ids),
        "max_child_depth": 1,
        "claim_ceiling": ROSTER_MANIFEST_CLAIM_CEILING,
    }
    packet = build_packet(parent_manifest, files)
    validate_packet(packet, known_operations=set(KNOWN_OPERATION_IDS))
    return PremortemZipPacket(
        packet_bytes=packet,
        target_sha256=sha256_bytes(target_raw),
        child_job_ids=child_ids,
        mmm_combos=combos,
    )


def _cell_fields(
    value: Mapping[str, Any],
    *,
    lens: str,
    target_digest: str,
    member_id: str | None = None,
    output_path: str | None = None,
) -> None:
    required = set(PREMORTEM_CELL_FIELDS)
    actual = set(value)
    if actual != required:
        detail = _canonical(
            {
                "schema": "constraintbox.premortem-cell-schema-refusal.v1",
                "reason": "field_set",
                "lens": lens,
                "member_id": member_id,
                "output_path": output_path,
                "missing_fields": sorted(required - actual),
                "extra_fields": sorted(actual - required),
                "allowed_fields": sorted(required),
            }
        ).decode("ascii")
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_SCHEMA", detail)
    if value.get("schema") != CELL_SCHEMA or value.get("lens") != lens or value.get("target_sha256") != target_digest:
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_BINDING", lens)
    for key in ("failure_mechanisms", "evidence", "limits"):
        values = value.get(key)
        if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item.strip() for item in values):
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_SCHEMA", key)
    for key in ("falsifier", "warning", "finite_repair", "rerun_operation", "claim_ceiling"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_SCHEMA", key)
    ceiling = value["claim_ceiling"].lower()
    if any(term in ceiling for term in ("promotion_allowed: true", "authority granted", "release approved")):
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_CLAIM_CEILING", lens)


def _attempt_history_summary(
    *, member_id: str, attempts: list[Mapping[str, Any]], accepted_attempt: int
) -> dict[str, Any]:
    """Copy retry facts into the parent surface without semantic flattening."""

    refusal_reasons = [
        str(attempt["refusal_reason"])
        for attempt in attempts
        if isinstance(attempt.get("refusal_reason"), str)
        and attempt.get("refusal_reason")
    ]
    reason_counts: dict[str, int] = {}
    for reason in refusal_reasons:
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    return {
        "member_id": member_id,
        "attempt_count": len(attempts),
        # This is the one-based number of attempts consumed before the
        # accepted output, not a claim that every attempt was accepted.
        "accepted_attempt_count": accepted_attempt,
        "attempts_until_acceptance": accepted_attempt,
        "accepted_attempts": 1,
        "refusal_reasons": refusal_reasons,
        "attempt_refusal_reasons": refusal_reasons,
        "refusal_reason_summary": reason_counts,
        "attempt_refusal_reason_summary": reason_counts,
    }


def _bounded_refusal_detail(
    reason_code: str, detail: str, *, config: Mapping[str, Any]
) -> str:
    """Retain only bounded identity/digest/schema facts across the wrapper."""

    try:
        value = strict_json_loads(detail.encode("utf-8"), label="refusal_detail")
    except (UnicodeEncodeError, ZipJobRefusal):
        value = None
    if not isinstance(value, dict):
        return _canonical(
            {"reason_code": reason_code, "detail": None}
        ).decode("ascii")
    if value.get("schema") == "constraintbox.premortem-cell-schema-refusal.v1":
        return _canonical(
            {
                "schema": value.get("schema"),
                "reason": value.get("reason"),
                "lens": value.get("lens"),
                "member_id": value.get("member_id"),
                "output_path": value.get("output_path"),
                "missing_fields": sorted(value.get("missing_fields") or []),
                "extra_fields": sorted(value.get("extra_fields") or []),
                "allowed_fields": sorted(value.get("allowed_fields") or []),
            }
        ).decode("ascii")
    if value.get("schema") == "constraintbox.md-agent-roster-refusal.v1":
        member_lenses = {
            str(row.get("member_id")): lens
            for lens, rows in dict(config.get("members") or {}).items()
            for row in rows
            if isinstance(row, dict)
        }
        exhausted: list[dict[str, Any]] = []
        for agent in value.get("exhausted_agents") or []:
            if not isinstance(agent, dict):
                continue
            agent_id = agent.get("agent_id")
            lens = member_lenses.get(str(agent_id))
            attempts: list[dict[str, Any]] = []
            for attempt in agent.get("attempts") or []:
                if not isinstance(attempt, dict):
                    continue
                attempts.append(
                    {
                        key: attempt.get(key)
                        for key in (
                            "attempt",
                            "provider_request_id",
                            "output_sha256",
                            "refusal_reason",
                            "cell_missing_fields",
                            "cell_extra_fields",
                        )
                        if key in attempt
                    }
                )
            exhausted.append(
                {
                    "agent_id": agent_id,
                    "lens": lens,
                    "child_job_id": (
                        f"{config.get('parent_job_id')}-{lens}" if lens else None
                    ),
                    "output_path": agent.get("output_path"),
                    "terminal_refusal": agent.get("terminal_refusal"),
                    "attempts": attempts,
                }
            )
        return _canonical(
            {
                "schema": value.get("schema"),
                "run_id": value.get("run_id"),
                "max_attempts": value.get("max_attempts"),
                "accepted_agent_ids": value.get("accepted_agent_ids") or [],
                "refusal_reason_summary": value.get("refusal_reason_summary") or {},
                "exhausted_agents": exhausted,
            }
        ).decode("ascii")
    return _canonical(
        {
            "reason_code": reason_code,
            "schema": value.get("schema"),
            "lens": value.get("lens"),
            "member_id": value.get("member_id"),
            "output_path": value.get("output_path"),
            "missing_fields": sorted(value.get("missing_fields") or []),
            "extra_fields": sorted(value.get("extra_fields") or []),
        }
    ).decode("ascii")


def _validate_lens_return(*, lens: str, target: bytes, child_packet: bytes, child_return: bytes, expected: Mapping[str, Any], wave: Mapping[str, Any]) -> dict[str, Any]:
    max_attempts = wave.get("max_attempts")
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 5:
        raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", lens)
    if expected.get("max_attempts") != max_attempts:
        raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", lens)
    child = validate_packet(child_packet, known_operations=set(KNOWN_OPERATION_IDS))
    child_entries = _entries(child_packet, label=f"{lens}.packet")
    child_return_manifest = validate_return_zip(
        child_return,
        expected_input_sha256=sha256_bytes(child_packet),
        input_packet_bytes=child_packet,
    )
    return_entries = _entries(child_return, label=f"{lens}.return")
    lens_manifest = _object(child_entries.get("input/lens_manifest.json", b""), f"{lens}.lens_manifest")
    if lens_manifest.get("lens") != lens or lens_manifest.get("target_sha256") != sha256_bytes(target):
        raise ZipJobRefusal("REFUSE_PREMORTEM_TARGET_BINDING", lens)
    if lens_manifest.get("output_delivery") != OUTPUT_DELIVERY:
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", lens)
    if lens_manifest.get("max_attempts") != max_attempts:
        raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", lens)
    if child.manifest.job_id != expected.get("job_id"):
        raise ZipJobRefusal("REFUSE_PREMORTEM_ANCESTRY", lens)
    if lens_manifest.get("parent_id") != wave.get("parent_id") or lens_manifest.get("wave_id") != wave.get("wave_id") or lens_manifest.get("round") != wave.get("round") or lens_manifest.get("depth") != 1:
        raise ZipJobRefusal("REFUSE_PREMORTEM_ANCESTRY", lens)
    if child_entries.get("input/target.bin") != target:
        raise ZipJobRefusal("REFUSE_PREMORTEM_TARGET_BINDING", lens)
    if sha256_bytes(child_entries.get("input/target.bin", b"")) != wave.get("target_sha256"):
        raise ZipJobRefusal("REFUSE_PREMORTEM_TARGET_BINDING", lens)
    delivery = _object(child_entries.get("input/output_delivery.json", b""), f"{lens}.output_delivery")
    if delivery.get("output_delivery") != OUTPUT_DELIVERY or delivery.get("provider_response_required") is not True:
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", lens)
    roster = _object(return_entries.get("output/roster_receipt.json", b""), f"{lens}.roster_receipt")
    expected_members = list(expected.get("member_ids") or [])
    if roster.get("schema") != RECEIPT_SCHEMA:
        expected_output_paths = sorted(
            str(member.get("output_path"))
            for member in lens_manifest.get("members", [])
            if isinstance(member, dict) and member.get("output_path")
        )
        detail = _canonical(
            {
                "schema": "constraintbox.md-agent-roster-schema-refusal.v1",
                "reason": "schema",
                "lens": lens,
                "child_job_id": child.manifest.job_id,
                "expected_member_ids": expected_members,
                "expected_output_paths": expected_output_paths,
                "expected_schema": RECEIPT_SCHEMA,
                "observed_schema": roster.get("schema"),
                "missing_fields": [],
                "extra_fields": [],
            }
        ).decode("ascii")
        raise ZipJobRefusal("REFUSE_PREMORTEM_ROSTER_SCHEMA", detail)
    roster_ok, roster_missing, roster_extra = _roster_receipt_field_set(roster)
    if not roster_ok:
        variant = "bound" if roster.get("hierarchy_bound") is True else "unbound"
        expected_output_paths = sorted(
            str(member.get("output_path"))
            for member in lens_manifest.get("members", [])
            if isinstance(member, dict) and member.get("output_path")
        )
        detail = _canonical(
            {
                "schema": "constraintbox.md-agent-roster-schema-refusal.v1",
                "reason": "field_set",
                "lens": lens,
                "child_job_id": child.manifest.job_id,
                "expected_member_ids": expected_members,
                "expected_output_paths": expected_output_paths,
                "missing_fields": roster_missing,
                "extra_fields": roster_extra,
                "allowed_fields": sorted(ROSTER_RECEIPT_FIELDS[variant]),
            }
        ).decode("ascii")
        raise ZipJobRefusal("REFUSE_PREMORTEM_ROSTER_SCHEMA", detail)
    if roster.get("max_attempts") != max_attempts:
        raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", lens)
    if roster.get("accepted_agent_ids") != expected_members:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_MISSING", lens)
    rows = roster.get("agents")
    if not isinstance(rows, list) or len(rows) != len(expected_members):
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_MISSING", lens)
    expected_by_id = {str(row["member_id"]): row for row in lens_manifest.get("members", [])}
    records: list[dict[str, Any]] = []
    attempt_summaries: list[dict[str, Any]] = []
    refusal_reason_summary: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ZipJobRefusal("REFUSE_PREMORTEM_ROSTER_RECEIPT", lens)
        member_id = _text(row.get("agent_id"), "agent_id")
        expected_member = expected_by_id.get(member_id)
        if expected_member is None or row.get("accepted") is not True:
            raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_MISSING", member_id)
        if row.get("output_delivery") != OUTPUT_DELIVERY:
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", member_id)
        if row.get("controller_materialized_output") is not True:
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", member_id)
        if row.get("provider") != expected_member.get("provider") or row.get("model_requested") != expected_member.get("model_requested"):
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_MISMATCH", member_id)
        if row.get("model_observed_allowlist") != expected_member.get(
            "model_observed_allowlist"
        ):
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        attempts = row.get("attempts")
        if not isinstance(attempts, list) or not 1 <= len(attempts) <= max_attempts:
            raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", member_id)
        if not isinstance(row.get("accepted_attempt"), int) or not 1 <= row["accepted_attempt"] <= len(attempts):
            raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", member_id)
        accepted_attempt = attempts[row["accepted_attempt"] - 1]
        for attempt_index, attempt in enumerate(attempts, start=1):
            if not isinstance(attempt, dict) or not attempt.get("provider_request_id"):
                raise ZipJobRefusal("REFUSE_PREMORTEM_REQUEST_BINDING", member_id)
            if attempt.get("attempt") != attempt_index:
                raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", member_id)
            if "output_delivery" in attempt and attempt.get("output_delivery") != OUTPUT_DELIVERY:
                raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", member_id)
        attempt_summary = _attempt_history_summary(
            member_id=member_id, attempts=attempts, accepted_attempt=row["accepted_attempt"]
        )
        # Delivery is derived from the child packet bytes below, not from a
        # member's echoed digest or a copied receipt flag.
        attempt_summary["skill_bytes_delivered"] = True
        attempt_summary["skill_read_proved"] = False
        attempt_summary["skill_executed"] = False
        attempt_summary["max_attempts"] = max_attempts
        attempt_summaries.append(attempt_summary)
        for reason, count in attempt_summary["refusal_reason_summary"].items():
            refusal_reason_summary[reason] = refusal_reason_summary.get(reason, 0) + int(count)
        if accepted_attempt.get("controller_materialized_output") is not True:
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", member_id)
        require_binding = bool(expected_member.get("model_binding_required"))
        match_kind = row.get(
            "model_identity_match_kind",
            row.get("model_match_kind", "unverified"),
        )
        if match_kind not in {"exact", "declared_alias", "unverified"}:
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_MISMATCH", member_id)
        if require_binding and match_kind not in {"exact", "declared_alias"}:
            # A provider receipt's boolean binding flag is not enough: an
            # unverified route must never satisfy a required identity bind.
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        if require_binding and (row.get("model_binding_confirmed") is not True or not row.get("models_observed")):
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        if require_binding and (
            not row.get("composed_prompt_sha256")
            or not row.get("provider_source_receipt_sha256")
        ):
            raise ZipJobRefusal("REFUSE_PREMORTEM_REQUEST_BINDING", member_id)
        observed_values = row.get(
            "model_observed_values", row.get("models_observed", [])
        )
        if not isinstance(observed_values, list) or any(
            not isinstance(value, str) or not value for value in observed_values
        ):
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        if len(observed_values) != 1:
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        if match_kind == "declared_alias" and row.get(
            "alias_resolution_source"
        ) != "invocation.model_observed_allowlist":
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        if match_kind == "exact":
            if observed_values != [expected_member.get("model_requested")]:
                raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        elif match_kind == "declared_alias":
            allowlist = expected_member.get("model_observed_allowlist")
            if not isinstance(allowlist, list) or observed_values[0] not in allowlist:
                raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        attempt_summary["model_identity_match_kind"] = match_kind
        attempt_summary["model_match_kind"] = match_kind
        attempt_summary["model_alias_admitted"] = match_kind == "declared_alias"
        attempt_summary["alias_resolution_source"] = row.get("alias_resolution_source")
        attempt_summary["model_observed_values"] = list(observed_values)
        output_path = str(expected_member["output_path"])
        body = return_entries.get(output_path)
        if body is None:
            raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_MISSING", output_path)
        cell = _object(body, output_path)
        _cell_fields(
            cell,
            lens=lens,
            target_digest=sha256_bytes(target),
            member_id=member_id,
            output_path=output_path,
        )
        if row.get("output_sha256") != sha256_bytes(body):
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_BINDING", member_id)
        if accepted_attempt.get("output_sha256") != sha256_bytes(body):
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_BINDING", member_id)
        if row.get("output_path") != output_path:
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_BINDING", member_id)
        skill_digest = str(expected_member["skill_sha256"])
        if sha256_bytes(child_entries.get(str(expected_member["skill_path"]), b"")) != skill_digest:
            raise ZipJobRefusal("REFUSE_PREMORTEM_SKILL_BINDING", member_id)
        mmm_digests = dict(expected_member.get("mmm_sha256") or {})
        for digest in dict(expected_member.get("mmm_sha256") or {}).values():
            voice = next(
                name for name, value in dict(expected_member.get("mmm_sha256") or {}).items()
                if value == digest
            )
            if sha256_bytes(child_entries.get(f"MMMS/{voice}.md", b"")) != digest:
                raise ZipJobRefusal("REFUSE_PREMORTEM_MMM_BINDING", member_id)
        tool_raw = return_entries.get("output/tool_evidence.json")
        if not tool_raw:
            raise ZipJobRefusal("REFUSE_PREMORTEM_TOOL_RECEIPT", lens)
        tool = _object(tool_raw, "output/tool_evidence.json")
        tool_digest = _text(tool.get("canonical_sha256"), "tool.canonical_sha256")
        echo_status = _delivery_echo_status(
            cell,
            skill_path=str(expected_member["skill_path"]),
            skill_digest=skill_digest,
            mmm_digests=mmm_digests,
            tool_digest=tool_digest,
        )
        attempt_summary.update(echo_status)
        records.append(cell)
    return {
        "lens": lens,
        "max_attempts": max_attempts,
        "packet_sha256": sha256_bytes(child_packet),
        "return_sha256": sha256_bytes(child_return),
        "return_runtime_source_sha256": child_return_manifest.runtime_source_sha256,
        "target_sha256": sha256_bytes(target),
        "member_records": records,
        "attempt_summaries": attempt_summaries,
        "member_attempt_receipts": attempt_summaries,
        "accepted_attempt_count": sum(
            int(summary["accepted_attempts"]) for summary in attempt_summaries
        ),
        "accepted_attempts_consumed": sum(
            int(summary["accepted_attempt_count"]) for summary in attempt_summaries
        ),
        "refusal_reason_summary": refusal_reason_summary,
        "mmm_read_proved": False,
        "skill_bytes_delivered": all(
            bool(summary.get("skill_bytes_delivered")) for summary in attempt_summaries
        ),
        "skill_echo_proved": all(
            bool(summary.get("skill_echo_proved")) for summary in attempt_summaries
        ),
        "mmm_echo_proved": all(
            bool(summary.get("mmm_echo_proved")) for summary in attempt_summaries
        ),
        "tool_echo_proved": all(
            bool(summary.get("tool_echo_proved")) for summary in attempt_summaries
        ),
        "skill_read_proved": False,
        "skill_executed": False,
        "accepted_member_ids": expected_members,
        "output_delivery": OUTPUT_DELIVERY,
        "claim_ceiling": CLAIM_CEILING,
    }


def validate_premortem_zip_wave_return(packet_bytes: bytes, return_bytes: bytes) -> dict[str, Any]:
    """Validate root/child ZIPs and return only a disagreement-preserving receipt."""

    packet = validate_packet(packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    if packet.manifest.allowed_operations != ["run_child_zip_v1"] or packet.manifest.max_child_depth != 1:
        raise ZipJobRefusal("REFUSE_PREMORTEM_PACKET_SHAPE", packet.manifest.job_id)
    validate_return_zip(return_bytes, expected_input_sha256=sha256_bytes(packet_bytes), input_packet_bytes=packet_bytes)
    root_entries = _entries(return_bytes, label="premortem.root_return")
    packet_entries = _entries(packet_bytes, label="premortem.root_packet")
    wave = _object(packet_entries.get("inputs/wave_manifest.json", b""), "inputs/wave_manifest.json")
    target = packet_entries.get("inputs/target.bin")
    if target is None or wave.get("target_sha256") != sha256_bytes(target):
        raise ZipJobRefusal("REFUSE_PREMORTEM_TARGET_BINDING", "root")
    if wave.get("output_delivery") != OUTPUT_DELIVERY or wave.get("lenses") is None:
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", "root")
    child_rows = {str(row.get("lens")): row for row in wave["lenses"] if isinstance(row, dict)}
    if set(child_rows) != set(LENSES):
        raise ZipJobRefusal("REFUSE_PREMORTEM_LENS_ROSTER", "return")
    lens_receipts: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []
    all_attempt_summaries: list[dict[str, Any]] = []
    for lens in LENSES:
        child_path = f"children/{lens}.zip"
        return_path = f"output/{lens}.return.zip"
        child_packet = packet_entries.get(child_path)
        child_return = root_entries.get(return_path)
        if child_packet is None or child_return is None:
            raise ZipJobRefusal("REFUSE_PREMORTEM_CHILD_RETURN_MISSING", lens)
        row = child_rows[lens]
        if sha256_bytes(child_packet) != row.get("packet_sha256") or row.get("target_sha256") != sha256_bytes(target):
            raise ZipJobRefusal("REFUSE_PREMORTEM_CHILD_REBOUND", lens)
        receipt = _validate_lens_return(
            lens=lens,
            target=target,
            child_packet=child_packet,
            child_return=child_return,
            expected=row,
            wave=wave,
        )
        lens_receipts.append(receipt)
        all_records.extend(receipt["member_records"])
        all_attempt_summaries.extend(receipt["attempt_summaries"])
    compiled = compile_disagreement_receipt(
        all_records, attempt_summaries=all_attempt_summaries
    )
    return {
        "schema": WAVE_SCHEMA,
        "disposition": "PREMORTEM_ZIP_WAVE_COMPLETED",
        "parent_job_id": packet.manifest.job_id,
        "wave_id": wave.get("wave_id"),
        "run_id": wave.get("run_id"),
        "round": wave.get("round"),
        "target_sha256": sha256_bytes(target),
        "packet_sha256": sha256_bytes(packet_bytes),
        "return_sha256": sha256_bytes(return_bytes),
        "max_attempts": wave.get("max_attempts"),
        "lens_receipts": lens_receipts,
        "attempt_summaries": all_attempt_summaries,
        "compiled": compiled,
        # These are copied from the freshly compiled, validated receipt.  No
        # member text can raise a read/execution claim at this surface.
        "mmm_read_proved": bool(compiled.get("mmm_read_proved", False)),
        "skill_read_proved": bool(compiled.get("skill_read_proved", False)),
        "skill_executed": bool(compiled.get("skill_executed", False)),
        "skill_echo_proved": bool(compiled.get("skill_echo_proved", False)),
        "mmm_echo_proved": bool(compiled.get("mmm_echo_proved", False)),
        "tool_echo_proved": bool(compiled.get("tool_echo_proved", False)),
        "accepted_attempt_count": int(compiled.get("accepted_attempt_count", 0)),
        "accepted_attempts_consumed": int(
            compiled.get("accepted_attempts_consumed", 0)
        ),
        "refusal_reason_summary": dict(
            compiled.get("refusal_reason_summary") or {}
        ),
        "semantic_vote": None,
        "authority_disposition": None,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def compile_disagreement_receipt(
    records: list[Mapping[str, Any]],
    *,
    attempt_summaries: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Group exact records and expose contradictions without choosing a winner."""

    fingerprints: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        value = dict(record)
        digest = sha256_bytes(_canonical(value))
        fingerprints.setdefault(digest, []).append(value)
    groups = [
        {"fingerprint": digest, "count": len(values), "records": values}
        for digest, values in sorted(fingerprints.items())
    ]
    mechanisms = {str(item) for record in records for item in record.get("failure_mechanisms", [])}
    contradictions = []
    if len(mechanisms) > 1:
        contradictions.append(
            {
                "field": "failure_mechanisms",
                "distinct_values": sorted(mechanisms),
                "semantic_resolution": None,
            }
        )
    max_count = max((len(values) for values in fingerprints.values()), default=0)
    minority = [group for group in groups if group["count"] < max_count]
    attempt_rows = [dict(summary) for summary in (attempt_summaries or [])]
    refusal_reason_summary: dict[str, int] = {}
    for summary in attempt_rows:
        for reason, count in dict(summary.get("refusal_reason_summary") or {}).items():
            refusal_reason_summary[str(reason)] = refusal_reason_summary.get(str(reason), 0) + int(count)
    return {
        "schema": "constraintbox.premortem-disagreement.v1",
        "max_attempts": max(
            (int(summary.get("max_attempts", 0)) for summary in attempt_rows),
            default=0,
        ),
        "member_count": len(records),
        "exact_groups": groups,
        "contradictions": contradictions,
        "minority_findings": minority,
        "attempt_summaries": attempt_rows,
        "accepted_attempt_count": sum(
            int(summary.get("accepted_attempts", 0)) for summary in attempt_rows
        ),
        "accepted_attempts_consumed": sum(
            int(summary.get("accepted_attempt_count", 0)) for summary in attempt_rows
        ),
        "refusal_reason_summary": refusal_reason_summary,
        "mmm_read_proved": False,
        "skill_bytes_delivered": bool(attempt_rows)
        and all(bool(summary.get("skill_bytes_delivered", True)) for summary in attempt_rows),
        "skill_echo_proved": bool(attempt_rows)
        and all(bool(summary.get("skill_echo_proved")) for summary in attempt_rows),
        "mmm_echo_proved": bool(attempt_rows)
        and all(bool(summary.get("mmm_echo_proved")) for summary in attempt_rows),
        "tool_echo_proved": bool(attempt_rows)
        and all(bool(summary.get("tool_echo_proved")) for summary in attempt_rows),
        "skill_read_proved": False,
        "skill_executed": False,
        "winner": None,
        "semantic_vote": None,
        "preserved_without_collapse": True,
        "claim_ceiling": "disagreement inventory only; not semantic consensus or authority",
    }


def run_premortem_zip_wave(*, config: Mapping[str, Any], target: bytes, skill: bytes, mmm_sources: Mapping[str, bytes], repair_workspace: Path | None = None, repair_callback: Callable[[dict[str, Any], Path], bytes | None] | None = None, cancel: bool = False) -> dict[str, Any]:
    """Run bounded rounds; callback receives a temporary repair workspace only."""

    checked = _validate_config(config)
    original_target = _bytes(target, "target")
    if cancel:
        return {
            "schema": WAVE_SCHEMA,
            "disposition": "CANCELLED",
            "stop_reason": "cancelled",
            "max_attempts": int(checked["max_attempts"]),
            "target_sha256": sha256_bytes(original_target),
            "rounds": [],
            "mmm_read_proved": False,
            "skill_echo_proved": False,
            "mmm_echo_proved": False,
            "tool_echo_proved": False,
            "skill_read_proved": False,
            "skill_executed": False,
            "accepted_attempt_count": 0,
            "accepted_attempts_consumed": 0,
            "refusal_reason_summary": {},
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
    if repair_callback is not None and repair_workspace is None:
        raise ZipJobRefusal("REFUSE_PREMORTEM_REPAIR_WORKSPACE", "required_for_callback")
    current = original_target
    rounds: list[dict[str, Any]] = []
    max_rounds = int(checked.get("max_rounds", 1))
    start_round = int(checked["round"])
    stop_reason = "max_rounds"
    for offset in range(max_rounds):
        round_config = dict(checked)
        round_config["round"] = start_round + offset
        packet = build_premortem_zip_wave_packet(
            config=round_config, target=current, skill=skill, mmm_sources=mmm_sources
        )
        try:
            result = execute_packet(packet.packet_bytes)
            receipt = validate_premortem_zip_wave_return(packet.packet_bytes, result.return_zip_bytes)
        except ZipJobRefusal as exc:
            rounds.append(
                {
                    "round": round_config["round"],
                    "packet_sha256": packet.packet_sha256,
                    "target_sha256": packet.target_sha256,
                    "disposition": "REFUSED",
                    "reason_code": exc.reason_code,
                    "detail": _bounded_refusal_detail(
                        exc.reason_code, exc.detail, config=checked
                    ),
                }
            )
            stop_reason = "provider_refused"
            break
        rounds.append(receipt)
        if repair_callback is None:
            # No probe ran, so no observation supports a material-delta
            # conclusion.  Keep no_material_delta for a callback that ran and
            # returned an unchanged/no candidate target.
            stop_reason = "repair_callback_absent"
            break
        if offset + 1 >= max_rounds:
            stop_reason = "max_rounds"
            break
        workspace_root = Path(repair_workspace).expanduser().resolve()
        workspace_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f"premortem-r{round_config['round']}-", dir=workspace_root) as tmp:
            work = Path(tmp)
            (work / "target.bin").write_bytes(current)
            (work / "receipt.json").write_bytes(_canonical(receipt))
            candidate = repair_callback(receipt, work)
        if candidate is None:
            stop_reason = "no_material_delta"
            break
        try:
            candidate_bytes = _bytes(candidate, "repair_candidate")
        except ZipJobRefusal:
            stop_reason = "repair_callback_refused"
            break
        if candidate_bytes == current:
            stop_reason = "no_material_delta"
            break
        current = candidate_bytes
    latest_valid = next(
        (
            round_receipt
            for round_receipt in reversed(rounds)
            if isinstance(round_receipt, dict)
            and isinstance(round_receipt.get("compiled"), dict)
        ),
        {},
    )
    compiled = latest_valid.get("compiled", {})
    return {
        "schema": WAVE_SCHEMA,
        "disposition": "PREMORTEM_ZIP_WAVE_COMPLETED" if rounds and rounds[-1].get("disposition") != "REFUSED" else "REFUSED",
        "stop_reason": stop_reason,
        "max_attempts": int(checked["max_attempts"]),
        "target_sha256": sha256_bytes(original_target),
        "final_target_sha256": sha256_bytes(current),
        "rounds": rounds,
        "mmm_read_proved": bool(compiled.get("mmm_read_proved", False)),
        "skill_echo_proved": bool(compiled.get("skill_echo_proved", False)),
        "mmm_echo_proved": bool(compiled.get("mmm_echo_proved", False)),
        "tool_echo_proved": bool(compiled.get("tool_echo_proved", False)),
        "skill_read_proved": bool(compiled.get("skill_read_proved", False)),
        "skill_executed": bool(compiled.get("skill_executed", False)),
        "accepted_attempt_count": int(compiled.get("accepted_attempt_count", 0)),
        "accepted_attempts_consumed": int(
            compiled.get("accepted_attempts_consumed", 0)
        ),
        "refusal_reason_summary": dict(
            compiled.get("refusal_reason_summary") or {}
        ),
        "semantic_vote": None,
        "authority_disposition": None,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def _read_mmm_args(values: list[str]) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("MMM must be VOICE=PATH")
        voice, raw_path = value.split("=", 1)
        result[_text(voice, "mmm_voice")] = Path(raw_path).read_bytes()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_premortem_zip_wave")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--mmm", action="append", default=[], help="VOICE=PATH (repeat)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cancel", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = _object(args.config.read_bytes(), str(args.config))
        receipt = run_premortem_zip_wave(
            config=config,
            target=args.target.read_bytes(),
            skill=args.skill.read_bytes(),
            mmm_sources=_read_mmm_args(args.mmm),
            cancel=args.cancel,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(_canonical(receipt) + b"\n")
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        return 0 if receipt.get("disposition") != "REFUSED" else 2
    except (OSError, ValueError, ZipJobRefusal) as exc:
        reason = exc.reason_code if isinstance(exc, ZipJobRefusal) else "REFUSE_PREMORTEM_IO"
        detail = exc.detail if isinstance(exc, ZipJobRefusal) else str(exc)
        print(json.dumps({"schema": WAVE_SCHEMA, "disposition": "REFUSE", "reason_code": reason, "detail": detail, "promotion_allowed": False}, sort_keys=True, separators=(",", ":")))
        return 2


__all__ = [
    "CELL_SCHEMA",
    "CONFIG_SCHEMA",
    "LENSES",
    "OUTPUT_DELIVERY",
    "PremortemZipPacket",
    "build_premortem_zip_wave_packet",
    "compile_disagreement_receipt",
    "run_premortem_zip_wave",
    "validate_premortem_zip_wave_return",
]


if __name__ == "__main__":
    raise SystemExit(main())
