"""Bounded provider-backed parent -> council -> worker ZIP composition.

The public ZIP runtime already owns packet validation and ``run_child_zip_v1``
execution.  This module only builds the two-child topology, binds a small
lineage/leaf inventory beside each council packet, and compiles a parent-side
inventory after the runtime has returned the child ZIPs.  The inventory is a
receipt index and a synthesis *request*; it is deliberately not a consensus
or admission result.

Provider/model policy stays in caller-supplied agent rows.  Fixture rows use
the existing ``fixture-subprocess`` route; live rows are passed through to the
existing council/roster adapter unchanged.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .council_zip import MARKER, VOICES, assign_mini_mmm_combos, build_named_council_packet
from .md_agent_roster import build_md_agent_roster_packet
from .operation_ids import KNOWN_OPERATION_IDS
from .protocol import (
    MANIFEST_PATH,
    TaskSpec,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    deterministic_zip,
    sha256_bytes,
    strict_json_loads,
    validate_packet,
    validate_return_zip,
)
from .runtime import ExecutionResult, execute_packet


MAX_DEPTH = 2
CHILD_COUNT = 2
MAX_RETRIES = 2
DEFAULT_PARENT_JOB_ID = "provider-nested-parent"
DEFAULT_WAVE_ID = "provider-nested-council"
LINEAGE_PATH = "inputs/lineage.json"
LEAF_MANIFEST_PATH = "inputs/provider_leaf_manifest.json"
SYNTHESIS_REQUEST_PATH = "inputs/parent_synthesis_request.json"
PARENT_INVENTORY_PATH = "output/parent_inventory.json"

LINEAGE_SCHEMA = "constraintbox.provider-nested-lineage.v1"
LEAF_SCHEMA = "constraintbox.provider-nested-leaves.v1"
REQUEST_SCHEMA = "constraintbox.provider-nested-synthesis-request.v1"
INVENTORY_SCHEMA = "constraintbox.provider-nested-inventory.v1"
CLAIM_CEILING = (
    "local_zip_execution_with_declared_md_agents;"
    "not_host_hook;not_mmm_read;not_skill_exec;not_admission;not_release"
)
INVENTORY_CLAIM_CEILING = (
    "deterministic_receipt_inventory_and_synthesis_request_only;"
    "not_semantic_consensus;not_admission;not_release"
)


def _refuse(reason: str, detail: str = "") -> None:
    raise ZipJobRefusal(reason, detail)


def _task(
    *,
    task_id: str,
    sequence: int,
    operation: str,
    inputs: list[str],
    outputs: list[str],
    depends_on: list[str] | None = None,
) -> bytes:
    return canonical_json_bytes(
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


def _entries(data: bytes, *, reason: str = "REFUSE_PROVIDER_NESTED_MALFORMED_ZIP") -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
            result: dict[str, bytes] = {}
            for info in archive.infolist():
                if info.is_dir() or info.filename in result:
                    _refuse(reason, info.filename)
                result[info.filename] = archive.read(info)
            return result
    except ZipJobRefusal:
        raise
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise ZipJobRefusal(reason, str(exc)) from exc


def _object(raw: bytes, label: str, *, reason: str = "REFUSE_PROVIDER_NESTED_SCHEMA") -> dict[str, Any]:
    try:
        value = strict_json_loads(raw, label=label)
    except ZipJobRefusal as exc:
        raise ZipJobRefusal(reason, label) from exc
    if not isinstance(value, dict):
        _refuse(reason, label)
    return value


def _bytes(value: object, label: str) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    _refuse("REFUSE_PROVIDER_NESTED_BYTES", label)
    return b""


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _refuse("REFUSE_PROVIDER_NESTED_SCHEMA", label)
    return value


def _owner_prompt(value: object, label: str) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    return _bytes(value, label)


def _lineage(
    *,
    job_id: str,
    parent_job_id: str | None,
    wave_id: str,
    round_value: int,
    depth: int,
    child_ids: list[str],
    leaf_ids: list[str],
) -> bytes:
    return canonical_json_bytes(
        {
            "schema": LINEAGE_SCHEMA,
            "job_id": job_id,
            "parent_id": parent_job_id,
            "parent_job_id": parent_job_id,
            "wave_id": wave_id,
            "round": round_value,
            "depth": depth,
            "allowed_child_job_ids": child_ids,
            "leaf_ids": leaf_ids,
        }
    )


def _normalise_agents(
    rows: object,
    *,
    child_job_id: str,
    max_attempts: int,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    if not isinstance(rows, list) or not rows:
        _refuse("REFUSE_PROVIDER_NESTED_ROUTES", f"{child_job_id}:agents")
    cleaned: list[dict[str, Any]] = []
    leaf_options: dict[str, dict[str, Any]] = {}
    retry_values: set[int] = set()
    for raw in rows:
        if not isinstance(raw, Mapping):
            _refuse("REFUSE_PROVIDER_NESTED_ROUTES", f"{child_job_id}:agent")
        row = dict(raw)
        agent_id = _text(row.get("agent_id"), "agent_id")
        provider = _text(row.get("provider"), f"{agent_id}.provider")
        model = _text(row.get("model_requested"), f"{agent_id}.model_requested")
        output_path = _text(row.get("output_path"), f"{agent_id}.output_path")
        retries = row.get("max_attempts", max_attempts)
        if isinstance(retries, bool) or not isinstance(retries, int) or not 1 <= retries <= MAX_RETRIES:
            _refuse("REFUSE_PROVIDER_NESTED_RETRY_LIMIT", f"{agent_id}:{retries!r}")
        retry_values.add(retries)
        leaf_id = row.pop("leaf_id", f"{child_job_id}:{agent_id}")
        if leaf_id != f"{child_job_id}:{agent_id}":
            _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", str(leaf_id))
        require_binding = row.pop(
            "require_model_binding", provider != "fixture-subprocess"
        )
        if not isinstance(require_binding, bool):
            _refuse("REFUSE_PROVIDER_NESTED_SCHEMA", f"{agent_id}.require_model_binding")
        # These fields belong to this module's leaf manifest, not the roster
        # schema.  Hierarchy is added to the roster as a separate pass below.
        for field in ("depth", "parent_id", "wave_id", "round"):
            row.pop(field, None)
        row["max_attempts"] = retries
        cleaned.append(row)
        leaf_options[agent_id] = {
            "leaf_id": leaf_id,
            "provider": provider,
            "model_requested": model,
            "output_path": output_path,
            "model_binding_required": require_binding,
            "max_attempts": retries,
        }
    if len(leaf_options) != len(cleaned):
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", child_job_id)
    if len(retry_values) != 1:
        _refuse("REFUSE_PROVIDER_NESTED_RETRY_LIMIT", f"{child_job_id}:mixed")
    return cleaned, leaf_options


def _update_child_packet(
    packet_bytes: bytes,
    *,
    child_job_id: str,
    parent_job_id: str,
    wave_id: str,
    round_value: int,
    child_spec: Mapping[str, Any],
    leaf_options: Mapping[str, Mapping[str, Any]],
) -> tuple[bytes, dict[str, Any]]:
    packet = validate_packet(packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    entries = _entries(packet_bytes)
    manifest = _object(entries.pop(MANIFEST_PATH), MANIFEST_PATH)
    if manifest.get("job_id") != "md-agent-roster":
        _refuse("REFUSE_PROVIDER_NESTED_CHILD_JOB", str(manifest.get("job_id")))
    if manifest.get("max_child_depth") != 0 or manifest.get("allowed_child_job_ids") != []:
        _refuse("REFUSE_PROVIDER_NESTED_DEPTH", child_job_id)
    roster = _object(entries.get("inputs/roster.json", b""), "inputs/roster.json")
    # The hierarchy-aware roster path is optional in older checkouts, but this
    # packet always binds it when the current roster accepts the four fields.
    # The roster launches the actual provider leaves.  Its hierarchy therefore
    # binds those leaves to this child council at depth 2, while the council
    # packet's own lineage remains depth 1 under the root parent.
    roster["parent_id"] = child_job_id
    roster["wave_id"] = wave_id
    roster["round"] = round_value
    roster["depth"] = MAX_DEPTH
    entries["inputs/roster.json"] = canonical_json_bytes(roster)

    council_manifest = _object(
        entries.get("input/council_manifest.json", b""), "input/council_manifest.json"
    )
    members = council_manifest.get("members")
    if not isinstance(members, list) or not members:
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", child_job_id)
    member_ids = [row.get("agent_id") for row in members if isinstance(row, dict)]
    if len(member_ids) != len(members) or len(member_ids) != len(set(member_ids)):
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", child_job_id)
    if set(member_ids) != set(leaf_options):
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", child_job_id)
    leaves: list[dict[str, Any]] = []
    for member in members:
        if not isinstance(member, dict):
            _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", child_job_id)
        agent_id = _text(member.get("agent_id"), "member.agent_id")
        option = leaf_options[agent_id]
        if member.get("provider") != option["provider"] or member.get("model_requested") != option["model_requested"]:
            _refuse("REFUSE_PROVIDER_NESTED_LEAF_REBOUND", agent_id)
        if member.get("output_path") != option["output_path"]:
            _refuse("REFUSE_PROVIDER_NESTED_LEAF_REBOUND", agent_id)
        leaves.append(
            {
                "leaf_id": option["leaf_id"],
                "parent_id": child_job_id,
                "parent_job_id": child_job_id,
                "root_job_id": parent_job_id,
                "council_job_id": child_job_id,
                "agent_id": agent_id,
                "depth": MAX_DEPTH,
                "provider": member.get("provider"),
                "model_requested": member.get("model_requested"),
                "model_binding_required": option["model_binding_required"],
                "output_path": member.get("output_path"),
                "mmm_ids": list(member.get("mmm_ids") or []),
                "mmm_paths": list(member.get("mmm_paths") or []),
                "mmm_sha256": dict(member.get("mmm_sha256") or {}),
                "required_fragments": list(
                    next(
                        row.get("required_fragments", [])
                        for row in roster.get("agents", [])
                        if isinstance(row, dict) and row.get("agent_id") == agent_id
                    )
                ),
                "request_receipt_path": "output/roster_receipt.json",
                "output_receipt_path": member.get("output_path"),
            }
        )
    leaf_ids = [row["leaf_id"] for row in leaves]
    if len(leaf_ids) != len(set(leaf_ids)):
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", child_job_id)
    council_manifest.update(
        {
            "parent_id": parent_job_id,
            "parent_job_id": parent_job_id,
            "wave_id": wave_id,
            "round": round_value,
            "depth": 1,
        }
    )
    entries["input/council_manifest.json"] = canonical_json_bytes(council_manifest)
    entries[LINEAGE_PATH] = _lineage(
        job_id=child_job_id,
        parent_job_id=parent_job_id,
        wave_id=wave_id,
        round_value=round_value,
        depth=1,
        child_ids=[],
        leaf_ids=leaf_ids,
    )
    entries[LEAF_MANIFEST_PATH] = canonical_json_bytes(
        {
            "schema": LEAF_SCHEMA,
            "parent_id": parent_job_id,
            "parent_job_id": parent_job_id,
            "council_job_id": child_job_id,
            "wave_id": wave_id,
            "round": round_value,
            "depth": 1,
            "leaf_depth": MAX_DEPTH,
            "leaves": leaves,
        }
    )
    manifest.update(
        {
            "job_id": child_job_id,
            "allowed_child_job_ids": [],
            "max_child_depth": 0,
        }
    )
    child = build_packet(manifest, entries)
    # Re-validate after adding hierarchy and leaves so callers never receive a
    # packet that the normal runtime cannot consume.
    validate_packet(child, known_operations=set(KNOWN_OPERATION_IDS))
    return child, {
        "job_id": child_job_id,
        "packet_sha256": sha256_bytes(child),
        "depth": 1,
        "leaf_ids": leaf_ids,
        "leaves": leaves,
        "council_id": council_manifest.get("council_id"),
        "run_id": roster.get("run_id"),
        "seed": roster.get("seed"),
    }


def _build_roster_child_packet(
    *,
    council_id: str,
    owner_prompt: bytes,
    seed: int,
    run_id: str,
    agents: list[dict[str, Any]],
    mmm_files: Mapping[str, bytes],
    extra_files: Mapping[str, bytes],
    parent_job_id: str,
    wave_id: str,
    round_value: int,
) -> bytes:
    """Build a generic child with the public roster builder.

    ``build_named_council_packet`` is still supported by the caller's named
    council IDs, but named failure/repair councils may require prior receipts.
    This generic route keeps provider policy caller-owned and makes a fresh
    two-child fixture possible without manufacturing prior council evidence.
    """

    names = tuple(_text(row.get("agent_id"), "agent_id") for row in agents)
    combos = assign_mini_mmm_combos(seed=seed, members=names, voice_count=3)
    files = {str(path): _bytes(raw, str(path)) for path, raw in mmm_files.items()}
    files.update({str(path): _bytes(raw, str(path)) for path, raw in extra_files.items()})
    files.setdefault("SKILLS/council.md", b"Write only the declared council finding.\n")
    files.setdefault("input/OWNER_PROMPT.bin", owner_prompt)
    files.setdefault(
        "input/STOP.md",
        b"Stop on undeclared output, missing token, exhausted worker, or promotion.\n",
    )
    members: list[dict[str, Any]] = []
    roster_agents: list[dict[str, Any]] = []
    for row in agents:
        agent = {
            key: value
            for key, value in row.items()
            if key not in {"max_attempts", "timeout_seconds"}
        }
        agent_id = _text(agent.get("agent_id"), "agent_id")
        agent_path = _text(agent.get("agent_path"), f"{agent_id}.agent_path")
        files.setdefault(agent_path, f"role: {agent_id}\n".encode())
        voices = combos[agent_id]
        mmm_paths = [f"MMMS/{voice}.md" for voice in voices]
        if any(path not in files for path in mmm_paths):
            _refuse("REFUSE_PROVIDER_NESTED_MMM", agent_id)
        skill_path = "SKILLS/council.md"
        context_paths = list(agent.get("context_paths") or [])
        context_paths.extend(["input/OWNER_PROMPT.bin", "input/STOP.md"])
        required = list(agent.get("required_fragments") or [])
        required.extend(
            [
                f"finding: {MARKER}",
                f"council: {agent_id}",
                "support: observed",
                f"skill-token: {sha256_bytes(files[skill_path])}",
            ]
        )
        mmm_sha = {path: sha256_bytes(files[path]) for path in mmm_paths}
        required.extend(f"mmm-token: {digest}" for digest in mmm_sha.values())
        agent.update(
            {
                "mmm_paths": mmm_paths,
                "skill_paths": [skill_path],
                "context_paths": sorted(set(context_paths)),
                "required_fragments": list(dict.fromkeys(required)),
                "forbidden_fragments": list(
                    dict.fromkeys(
                        list(agent.get("forbidden_fragments") or [])
                        + ["promotion_allowed: true", "admission: ADMITTED"]
                    )
                ),
            }
        )
        roster_agents.append(agent)
        members.append(
            {
                "agent_id": agent_id,
                "output_path": agent["output_path"],
                "provider": agent["provider"],
                "model_requested": agent["model_requested"],
                "mmm_ids": [f"voice:{voice}:compact" for voice in voices],
                "mmm_paths": mmm_paths,
                "mmm_sha256": mmm_sha,
                "required_fragments": list(agent["required_fragments"]),
            }
        )
    files["input/council_manifest.json"] = canonical_json_bytes(
        {
            "schema": "constraintbox.council-zip.v1",
            "council_id": council_id,
            "run_id": run_id,
            "parent_id": parent_job_id,
            "parent_job_id": parent_job_id,
            "wave_id": wave_id,
            "round": round_value,
            "depth": 1,
            "seed": seed,
            "owner_prompt_sha256": sha256_bytes(owner_prompt),
            "members": members,
            "promotion_allowed": False,
            "mmm_read_proved": False,
            "skill_executed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
    )
    roster = {
        "schema": "constraintbox.md-agent-roster.v1",
        "run_id": run_id,
        "seed": seed,
        "required_marker": MARKER,
        "max_attempts": int(agents[0].get("max_attempts", 1) or 1),
        "timeout_seconds": int(agents[0].get("timeout_seconds", 30) or 30),
        "max_workers": max(3, len(roster_agents)),
        "shared_paths": ["input/council_manifest.json"],
        "parent_id": parent_job_id,
        "wave_id": wave_id,
        "round": round_value,
        "depth": 1,
        "agents": roster_agents,
    }
    return build_md_agent_roster_packet(roster=roster, files=files)


def build_provider_nested_council_packet(
    *,
    owner_prompt: bytes | str,
    seed: int,
    run_id: str,
    children: Sequence[Mapping[str, Any]] | None = None,
    child_specs: Sequence[Mapping[str, Any]] | None = None,
    child_councils: Sequence[Mapping[str, Any]] | None = None,
    mmm_files: Mapping[str, bytes] | None = None,
    parent_job_id: str = DEFAULT_PARENT_JOB_ID,
    wave_id: str = DEFAULT_WAVE_ID,
    round_value: int = 1,
    max_attempts: int = MAX_RETRIES,
) -> bytes:
    """Build a depth-2 parent packet from exactly two caller-supplied councils.

    Each child specification is the normal ``build_named_council_packet``
    input plus optional ``job_id``, ``owner_prompt``, ``agent_files`` and
    ``require_model_binding`` route metadata.  No provider or model is chosen
    here.  The resulting parent packet has only ``run_child_zip_v1`` and a
    deterministic local compile task.
    """

    if isinstance(max_attempts, bool) or not 1 <= max_attempts <= MAX_RETRIES:
        _refuse("REFUSE_PROVIDER_NESTED_RETRY_LIMIT", str(max_attempts))
    if isinstance(round_value, bool) or not isinstance(round_value, int) or round_value < 0:
        _refuse("REFUSE_PROVIDER_NESTED_SCHEMA", "round")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        _refuse("REFUSE_PROVIDER_NESTED_SCHEMA", "seed")
    parent_prompt = _owner_prompt(owner_prompt, "owner_prompt")
    parent_id = _text(parent_job_id, "parent_job_id")
    wave = _text(wave_id, "wave_id")
    run = _text(run_id, "run_id")
    chosen = children if children is not None else child_specs
    if chosen is None:
        chosen = child_councils
    if chosen is None or len(chosen) != CHILD_COUNT:
        _refuse("REFUSE_PROVIDER_NESTED_CHILD_COUNT", str(len(chosen or [])))
    specs = list(chosen)
    child_ids: list[str] = []
    child_packets: dict[str, bytes] = {}
    child_meta: list[dict[str, Any]] = []
    all_leaf_ids: list[str] = []
    all_mmm_combos: set[tuple[str, ...]] = set()
    for index, raw_spec in enumerate(specs):
        if not isinstance(raw_spec, Mapping):
            _refuse("REFUSE_PROVIDER_NESTED_SCHEMA", f"children[{index}]")
        spec = dict(raw_spec)
        council_id = _text(spec.get("council_id"), f"children[{index}].council_id")
        child_id = _text(
            spec.get("job_id", f"{parent_id}-{council_id}-{index}"),
            f"children[{index}].job_id",
        )
        if child_id in child_ids:
            _refuse("REFUSE_PROVIDER_NESTED_CHILD_IDENTITY", child_id)
        child_ids.append(child_id)
        child_seed = spec.get("seed", seed + index + 1)
        if isinstance(child_seed, bool) or not isinstance(child_seed, int) or child_seed < 0:
            _refuse("REFUSE_PROVIDER_NESTED_SCHEMA", f"{child_id}.seed")
        agents, leaf_options = _normalise_agents(
            spec.get("agents"), child_job_id=child_id, max_attempts=max_attempts
        )
        top_mmm = spec.get("mmm_files", mmm_files)
        if not isinstance(top_mmm, Mapping):
            _refuse("REFUSE_PROVIDER_NESTED_MMM", child_id)
        mmm_source: dict[str, bytes] = {
            str(path): _bytes(raw, str(path)) for path, raw in top_mmm.items()
        }
        extra = spec.get("extra_files") or {}
        if not isinstance(extra, Mapping):
            _refuse("REFUSE_PROVIDER_NESTED_SCHEMA", f"{child_id}.extra_files")
        child_extra: dict[str, bytes] = {
            str(path): _bytes(raw, str(path)) for path, raw in extra.items()
        }
        agent_files = spec.get("agent_files") or {}
        if not isinstance(agent_files, Mapping):
            _refuse("REFUSE_PROVIDER_NESTED_SCHEMA", f"{child_id}.agent_files")
        child_extra.update({str(path): _bytes(raw, str(path)) for path, raw in agent_files.items()})
        child_owner = _owner_prompt(spec.get("owner_prompt", parent_prompt), f"{child_id}.owner_prompt")
        child_run_id = _text(spec.get("run_id", f"{run}-{child_id}"), f"{child_id}.run_id")
        try:
            # A named council is the richest existing public builder.  Its
            # failure/repair variants intentionally require prior receipts,
            # however, so a fresh nested council falls back to the public
            # roster builder while retaining the same member/receipt surface.
            try:
                base_child = build_named_council_packet(
                    council_id=council_id,
                    owner_prompt=child_owner,
                    seed=child_seed,
                    run_id=child_run_id,
                    agents=agents,
                    mmm_files=mmm_source,
                    extra_files=child_extra,
                )
            except ZipJobRefusal as named_error:
                if named_error.reason_code not in {
                    "REFUSE_COUNCIL_ZIP_RECEIPT",
                    "REFUSE_COUNCIL_ZIP_ROSTER",
                    "REFUSE_COUNCIL_ZIP_AGENT",
                }:
                    raise
                base_child = _build_roster_child_packet(
                    council_id=council_id,
                    owner_prompt=child_owner,
                    seed=child_seed,
                    run_id=child_run_id,
                    agents=agents,
                    mmm_files=mmm_source,
                    extra_files=child_extra,
                    parent_job_id=parent_id,
                    wave_id=wave,
                    round_value=round_value,
                )
        except ZipJobRefusal:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise ZipJobRefusal("REFUSE_PROVIDER_NESTED_CHILD_BUILD", child_id) from exc
        child, meta = _update_child_packet(
            base_child,
            child_job_id=child_id,
            parent_job_id=parent_id,
            wave_id=wave,
            round_value=round_value,
            child_spec=spec,
            leaf_options=leaf_options,
        )
        for leaf in meta["leaves"]:
            combo = tuple(leaf.get("mmm_ids") or [])
            if combo in all_mmm_combos:
                _refuse("REFUSE_PROVIDER_NESTED_MMM_ASSIGNMENT", leaf["leaf_id"])
            all_mmm_combos.add(combo)
            all_leaf_ids.append(leaf["leaf_id"])
        child_packets[child_id] = child
        child_meta.append(meta)
    if len(all_leaf_ids) != len(set(all_leaf_ids)):
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", "duplicate")

    parent_lineage = _lineage(
        job_id=parent_id,
        parent_job_id=None,
        wave_id=wave,
        round_value=round_value,
        depth=0,
        child_ids=child_ids,
        leaf_ids=sorted(all_leaf_ids),
    )
    return_paths = [f"output/{child_id}.return.zip" for child_id in child_ids]
    child_records = [
        {
            "job_id": meta["job_id"],
            "packet_sha256": meta["packet_sha256"],
            "return_path": return_paths[index],
            "parent_id": parent_id,
            "parent_job_id": parent_id,
            "depth": 1,
            "leaf_ids": list(meta["leaf_ids"]),
            "council_id": meta["council_id"],
            "run_id": meta["run_id"],
            "seed": meta["seed"],
        }
        for index, meta in enumerate(child_meta)
    ]
    synthesis_request = {
        "schema": REQUEST_SCHEMA,
        "parent_id": parent_id,
        "parent_job_id": parent_id,
        "wave_id": wave,
        "round": round_value,
        "depth": 0,
        "owner_prompt_sha256": sha256_bytes(parent_prompt),
        "children": child_records,
        "required_receipts": [
            "provider",
            "model_requested",
            "model_observed",
            "request_id",
            "output_path",
            "output_sha256",
            "model_binding_confirmed",
        ],
        "semantic_consensus": False,
        "instruction": (
            "Inventory child return ZIP bytes and declared provider/model/request/output "
            "receipts; issue a synthesis request only. Do not infer semantic consensus."
        ),
        "claim_ceiling": INVENTORY_CLAIM_CEILING,
    }
    files: dict[str, bytes] = {
        "00_RUN_ME_FIRST.md": (
            b"# Provider nested council parent ZIP\n\n"
            b"The runtime launches exactly two declared child council ZIPs. "
            b"Provider workers remain child-return records; the parent compiler "
            b"does not flatten or promote them.\n"
        ),
        LINEAGE_PATH: parent_lineage,
        SYNTHESIS_REQUEST_PATH: canonical_json_bytes(synthesis_request),
    }
    task_paths: list[str] = []
    tasks: list[bytes] = []
    child_task_ids: list[str] = []
    for sequence, child_id in enumerate(child_ids):
        child_path = f"children/{child_id}.zip"
        task_id = f"run-{child_id}"
        task_path = f"tasks/{sequence:02d}_{task_id}.task.json"
        output_path = return_paths[sequence]
        files[child_path] = child_packets[child_id]
        files[task_path] = _task(
            task_id=task_id,
            sequence=sequence,
            operation="run_child_zip_v1",
            inputs=[child_path],
            outputs=[output_path],
        )
        task_paths.append(task_path)
        tasks.append(files[task_path])
        child_task_ids.append(task_id)
    compile_task_path = "tasks/02_compile_parent.task.json"
    files[compile_task_path] = _task(
        task_id="compile-parent",
        sequence=2,
        operation="compile_provider_nested_inventory_v1",
        inputs=[
            LINEAGE_PATH,
            SYNTHESIS_REQUEST_PATH,
            "inputs/parent_child_records.json",
            *[f"children/{child_id}.zip" for child_id in child_ids],
            *return_paths,
        ],
        outputs=[PARENT_INVENTORY_PATH],
        depends_on=child_task_ids,
    )
    task_paths.append(compile_task_path)
    files["inputs/parent_child_records.json"] = canonical_json_bytes(child_records)
    manifest = {
        "schema": "constraintbox.zip_job.v1",
        "job_id": parent_id,
        "task_execution_order": task_paths,
        "required_output_file_list": [*return_paths, PARENT_INVENTORY_PATH],
        "allowed_operations": ["compile_provider_nested_inventory_v1", "run_child_zip_v1"],
        "allowed_child_job_ids": child_ids,
        "max_child_depth": MAX_DEPTH,
        "claim_ceiling": CLAIM_CEILING,
    }
    packet = build_packet(manifest, files)
    validate_provider_nested_packet(packet)
    return packet


def _lineage_from(entries: Mapping[str, bytes], *, packet_id: str) -> dict[str, Any]:
    raw = _object(entries.get(LINEAGE_PATH, b""), LINEAGE_PATH)
    if raw.get("schema") != LINEAGE_SCHEMA or raw.get("job_id") != packet_id:
        _refuse("REFUSE_PROVIDER_NESTED_LINEAGE", packet_id)
    return raw


def _validate_child_packet(
    child_bytes: bytes,
    *,
    parent_id: str,
    child_id: str,
    wave_id: str,
    round_value: int,
    expected_packet_sha256: str | None = None,
) -> tuple[Any, dict[str, bytes], dict[str, Any], dict[str, Any]]:
    try:
        packet = validate_packet(child_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    except ZipJobRefusal as exc:
        raise ZipJobRefusal("REFUSE_PROVIDER_NESTED_CHILD_MALFORMED", child_id) from exc
    if expected_packet_sha256 is not None and sha256_bytes(child_bytes) != expected_packet_sha256:
        _refuse("REFUSE_PROVIDER_NESTED_CHILD_REBOUND", child_id)
    if packet.manifest.job_id != child_id:
        _refuse("REFUSE_PROVIDER_NESTED_CHILD_REBOUND", child_id)
    if packet.manifest.max_child_depth != 0 or packet.manifest.allowed_child_job_ids:
        _refuse("REFUSE_PROVIDER_NESTED_DEPTH", child_id)
    if any(task.operation == "run_child_zip_v1" for task in packet.tasks):
        _refuse("REFUSE_PROVIDER_NESTED_DEPTH", child_id)
    entries = _entries(child_bytes)
    lineage = _lineage_from(entries, packet_id=child_id)
    if lineage.get("parent_id") != parent_id or lineage.get("parent_job_id") != parent_id:
        _refuse("REFUSE_PROVIDER_NESTED_LINEAGE", child_id)
    if lineage.get("wave_id") != wave_id or lineage.get("round") != round_value or lineage.get("depth") != 1:
        _refuse("REFUSE_PROVIDER_NESTED_LINEAGE", child_id)
    if lineage.get("allowed_child_job_ids") != []:
        _refuse("REFUSE_PROVIDER_NESTED_DEPTH", child_id)
    leaves = _object(entries.get(LEAF_MANIFEST_PATH, b""), LEAF_MANIFEST_PATH)
    if leaves.get("schema") != LEAF_SCHEMA:
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", child_id)
    if leaves.get("parent_id") != parent_id or leaves.get("parent_job_id") != parent_id:
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_REBOUND", child_id)
    if leaves.get("council_job_id") != child_id or leaves.get("depth") != 1 or leaves.get("leaf_depth") != MAX_DEPTH:
        _refuse("REFUSE_PROVIDER_NESTED_DEPTH", child_id)
    if leaves.get("wave_id") != wave_id or leaves.get("round") != round_value:
        _refuse("REFUSE_PROVIDER_NESTED_LINEAGE", child_id)
    rows = leaves.get("leaves")
    if not isinstance(rows, list) or not rows:
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", child_id)
    ids = [row.get("leaf_id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or len(ids) != len(set(ids)):
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", child_id)
    if lineage.get("leaf_ids") != ids:
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_REBOUND", child_id)
    return packet, entries, leaves, lineage


def validate_provider_nested_packet(packet_bytes: bytes) -> ProviderNestedCouncil:
    """Validate exact depth-2 topology and caller-bound child/leaf identities."""

    try:
        packet = validate_packet(packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    except ZipJobRefusal as exc:
        raise ZipJobRefusal("REFUSE_PROVIDER_NESTED_PARENT_MALFORMED", "packet") from exc
    if packet.manifest.max_child_depth != MAX_DEPTH:
        _refuse("REFUSE_PROVIDER_NESTED_DEPTH", str(packet.manifest.max_child_depth))
    parent_id = packet.manifest.job_id
    entries = _entries(packet_bytes)
    lineage = _lineage_from(entries, packet_id=parent_id)
    if lineage.get("parent_id") is not None or lineage.get("parent_job_id") is not None:
        _refuse("REFUSE_PROVIDER_NESTED_LINEAGE", parent_id)
    if lineage.get("depth") != 0:
        _refuse("REFUSE_PROVIDER_NESTED_DEPTH", parent_id)
    wave_id = _text(lineage.get("wave_id"), "wave_id")
    round_value = lineage.get("round")
    if isinstance(round_value, bool) or not isinstance(round_value, int) or round_value < 0:
        _refuse("REFUSE_PROVIDER_NESTED_LINEAGE", parent_id)
    child_ids = packet.manifest.allowed_child_job_ids
    if len(child_ids) != CHILD_COUNT or len(set(child_ids)) != CHILD_COUNT:
        _refuse("REFUSE_PROVIDER_NESTED_CHILD_COUNT", parent_id)
    if lineage.get("allowed_child_job_ids") != child_ids:
        _refuse("REFUSE_PROVIDER_NESTED_LINEAGE", parent_id)
    if not isinstance(lineage.get("leaf_ids"), list) or len(lineage["leaf_ids"]) != len(set(lineage["leaf_ids"])):
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", parent_id)
    child_tasks = [task for task in packet.tasks if task.operation == "run_child_zip_v1"]
    if len(child_tasks) != CHILD_COUNT:
        _refuse("REFUSE_PROVIDER_NESTED_CHILD_COUNT", parent_id)
    if packet.tasks[-1].operation != "compile_provider_nested_inventory_v1":
        _refuse("REFUSE_PROVIDER_NESTED_COMPILE", parent_id)
    if packet.tasks[-1].output_paths != [PARENT_INVENTORY_PATH]:
        _refuse("REFUSE_PROVIDER_NESTED_COMPILE", parent_id)
    if set(packet.manifest.allowed_operations) != {
        "run_child_zip_v1",
        "compile_provider_nested_inventory_v1",
    }:
        _refuse("REFUSE_PROVIDER_NESTED_COMPILE", parent_id)
    expected_outputs = {PARENT_INVENTORY_PATH}
    observed_child_ids: list[str] = []
    all_leaf_ids: list[str] = []
    for task in child_tasks:
        if len(task.input_paths) != 1 or len(task.output_paths) != 1:
            _refuse("REFUSE_PROVIDER_NESTED_TASK", task.task_id)
        path = task.input_paths[0]
        child_bytes = entries.get(path)
        if child_bytes is None:
            _refuse("REFUSE_PROVIDER_NESTED_CHILD_MISSING", path)
        child_id = path.removeprefix("children/").removesuffix(".zip")
        if path != f"children/{child_id}.zip" or child_id not in child_ids:
            _refuse("REFUSE_PROVIDER_NESTED_CHILD_REBOUND", path)
        if task.output_paths != [f"output/{child_id}.return.zip"]:
            _refuse("REFUSE_PROVIDER_NESTED_TASK", child_id)
        observed_child_ids.append(child_id)
        expected_outputs.add(task.output_paths[0])
        _child_packet, child_entries, child_leaves, _child_lineage = _validate_child_packet(
            child_bytes,
            parent_id=parent_id,
            child_id=child_id,
            wave_id=wave_id,
            round_value=round_value,
        )
        child_rows = child_leaves["leaves"]
        all_leaf_ids.extend(row["leaf_id"] for row in child_rows)
        if child_id in observed_child_ids[:-1]:
            _refuse("REFUSE_PROVIDER_NESTED_CHILD_IDENTITY", child_id)
        # A child must have exactly one roster task and the normal required
        # output set.  This keeps the worker leaves isolated inside the child.
        if not any(task.operation == "run_md_agent_roster_v1" for task in _child_packet.tasks):
            _refuse("REFUSE_PROVIDER_NESTED_CHILD_BUILD", child_id)
        if any(path.startswith("children/") for path in child_entries):
            _refuse("REFUSE_PROVIDER_NESTED_DEPTH", child_id)
    if observed_child_ids != child_ids:
        _refuse("REFUSE_PROVIDER_NESTED_CHILD_REBOUND", parent_id)
    if sorted(all_leaf_ids) != lineage.get("leaf_ids") or len(all_leaf_ids) != len(set(all_leaf_ids)):
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", parent_id)
    expected_required_outputs = {
        PARENT_INVENTORY_PATH,
        *(f"output/{child_id}.return.zip" for child_id in child_ids),
    }
    if set(packet.manifest.required_output_file_list) != expected_required_outputs:
        _refuse("REFUSE_PROVIDER_NESTED_OUTPUT", parent_id)
    if PARENT_INVENTORY_PATH not in packet.manifest.required_output_file_list:
        _refuse("REFUSE_PROVIDER_NESTED_OUTPUT", parent_id)
    request = _object(entries.get(SYNTHESIS_REQUEST_PATH, b""), SYNTHESIS_REQUEST_PATH)
    if request.get("schema") != REQUEST_SCHEMA or request.get("parent_job_id") != parent_id:
        _refuse("REFUSE_PROVIDER_NESTED_COMPILE", parent_id)
    if request.get("semantic_consensus") is not False:
        _refuse("REFUSE_PROVIDER_NESTED_COMPILE", "semantic_consensus")
    records = request.get("children")
    if not isinstance(records, list) or [row.get("job_id") for row in records if isinstance(row, dict)] != child_ids:
        _refuse("REFUSE_PROVIDER_NESTED_CHILD_REBOUND", parent_id)
    for child_id, record in zip(child_ids, records, strict=True):
        if not isinstance(record, dict) or record.get("job_id") != child_id:
            _refuse("REFUSE_PROVIDER_NESTED_CHILD_REBOUND", child_id)
        child_packet = entries[f"children/{child_id}.zip"]
        if record.get("packet_sha256") != sha256_bytes(child_packet):
            _refuse("REFUSE_PROVIDER_NESTED_CHILD_REBOUND", child_id)
        child_leaves = _object(
            _entries(child_packet)[LEAF_MANIFEST_PATH], LEAF_MANIFEST_PATH
        )
        if record.get("leaf_ids") != [row["leaf_id"] for row in child_leaves["leaves"]]:
            _refuse("REFUSE_PROVIDER_NESTED_LEAF_REBOUND", child_id)
    return ProviderNestedCouncil(
        packet_bytes=packet_bytes,
        parent_job_id=parent_id,
        child_job_ids=tuple(child_ids),
        leaf_ids=tuple(all_leaf_ids),
    )


def _receipt_row_for_leaf(
    *,
    child_id: str,
    child_packet: bytes,
    child_entries: Mapping[str, bytes],
    child_leaves: Mapping[str, Any],
    child_return: bytes,
) -> list[dict[str, Any]]:
    try:
        validate_return_zip(
            child_return,
            expected_input_sha256=sha256_bytes(child_packet),
            input_packet_bytes=child_packet,
        )
    except ZipJobRefusal as exc:
        raise ZipJobRefusal("REFUSE_PROVIDER_NESTED_CHILD_RETURN", child_id) from exc
    returned = _entries(child_return, reason="REFUSE_PROVIDER_NESTED_CHILD_RETURN")
    roster = _object(returned.get("output/roster_receipt.json", b""), "output/roster_receipt.json", reason="REFUSE_PROVIDER_NESTED_OUTPUT")
    if roster.get("schema") != "constraintbox.md-agent-roster-receipt.v1":
        _refuse("REFUSE_PROVIDER_NESTED_OUTPUT", child_id)
    expected = child_leaves.get("leaves")
    rows = roster.get("agents")
    if not isinstance(expected, list) or not isinstance(rows, list) or len(expected) != len(rows):
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", child_id)
    expected_by_id = {row["agent_id"]: row for row in expected}
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            _refuse("REFUSE_PROVIDER_NESTED_OUTPUT", child_id)
        agent_id = row.get("agent_id")
        if agent_id not in expected_by_id or agent_id in seen:
            _refuse("REFUSE_PROVIDER_NESTED_LEAF_REBOUND", str(agent_id))
        seen.add(agent_id)
        expected_leaf = expected_by_id[agent_id]
        if row.get("provider") != expected_leaf.get("provider") or row.get("model_requested") != expected_leaf.get("model_requested"):
            _refuse("REFUSE_PROVIDER_NESTED_LEAF_REBOUND", agent_id)
        if row.get("output_path") != expected_leaf.get("output_path"):
            _refuse("REFUSE_PROVIDER_NESTED_LEAF_REBOUND", agent_id)
        for key, expected_value in (
            ("parent_id", child_id),
            ("wave_id", child_leaves.get("wave_id")),
            ("round", child_leaves.get("round")),
            ("depth", MAX_DEPTH),
        ):
            if row.get(key) != expected_value:
                _refuse("REFUSE_PROVIDER_NESTED_LEAF_REBOUND", f"{agent_id}:{key}")
        if row.get("accepted") is not True or not isinstance(row.get("accepted_attempt"), int):
            _refuse("REFUSE_PROVIDER_NESTED_LEAF_EXHAUSTED", agent_id)
        attempts = row.get("attempts")
        if not isinstance(attempts, list) or not 1 <= len(attempts) <= MAX_RETRIES:
            _refuse("REFUSE_PROVIDER_NESTED_RETRY_LIMIT", agent_id)
        accepted_attempt = row["accepted_attempt"]
        if not 1 <= accepted_attempt <= len(attempts):
            _refuse("REFUSE_PROVIDER_NESTED_OUTPUT", agent_id)
        # Every request identity and output digest is receipt-bound and
        # deterministic for the existing roster runner.
        request_ids: set[str] = set()
        for attempt_index, attempt in enumerate(attempts, start=1):
            if not isinstance(attempt, dict):
                _refuse("REFUSE_PROVIDER_NESTED_OUTPUT", agent_id)
            if attempt.get("attempt") != attempt_index:
                _refuse("REFUSE_PROVIDER_NESTED_OUTPUT", agent_id)
            request_id = attempt.get("provider_request_id")
            if not isinstance(request_id, str) or not request_id or request_id in request_ids:
                _refuse("REFUSE_PROVIDER_NESTED_LEAF_REBOUND", agent_id)
            request_ids.add(request_id)
        body = returned.get(str(expected_leaf.get("output_path")), b"")
        if not body:
            _refuse("REFUSE_PROVIDER_NESTED_OUTPUT", agent_id)
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ZipJobRefusal("REFUSE_PROVIDER_NESTED_OUTPUT", agent_id) from exc
        for fragment in expected_leaf.get("required_fragments") or []:
            if fragment not in text:
                _refuse("REFUSE_PROVIDER_NESTED_OUTPUT", agent_id)
        request_row = attempts[accepted_attempt - 1]
        if request_row.get("output_sha256") != sha256_bytes(body):
            _refuse("REFUSE_PROVIDER_NESTED_OUTPUT", agent_id)
        model_observed = row.get("models_observed")
        if not isinstance(model_observed, list) or not model_observed or any(not isinstance(v, str) or not v for v in model_observed):
            _refuse("REFUSE_PROVIDER_NESTED_MODEL_BINDING", agent_id)
        binding_required = bool(expected_leaf.get("model_binding_required"))
        if binding_required:
            if row.get("model_binding_confirmed") is not True:
                _refuse("REFUSE_PROVIDER_NESTED_MODEL_BINDING", agent_id)
            if not isinstance(row.get("provider_request_id"), str) or not row.get("provider_request_id"):
                _refuse("REFUSE_PROVIDER_NESTED_MODEL_BINDING", agent_id)
            source_digest = row.get("provider_source_receipt_sha256")
            if not isinstance(source_digest, str) or len(source_digest) != 64:
                _refuse("REFUSE_PROVIDER_NESTED_MODEL_BINDING", agent_id)
        out.append(
            {
                "leaf_id": expected_leaf["leaf_id"],
                "parent_id": expected_leaf["parent_id"],
                "parent_job_id": expected_leaf["parent_job_id"],
                "council_job_id": child_id,
                "agent_id": agent_id,
                "depth": MAX_DEPTH,
                "provider": row["provider"],
                "model_requested": row["model_requested"],
                "model_observed": list(model_observed),
                "model_binding_confirmed": bool(row.get("model_binding_confirmed")),
                "request": {
                    "request_id": request_row.get("provider_request_id"),
                    "attempt": accepted_attempt,
                    "attempt_receipt_sha256": sha256_bytes(canonical_json_bytes(request_row)),
                    "composed_prompt_sha256": request_row.get("composed_prompt_sha256"),
                },
                "provider_receipt": {
                    "provider_source_receipt_sha256": row.get("provider_source_receipt_sha256"),
                    "identity_source": row.get("identity_source"),
                    "model_binding_confirmed": bool(row.get("model_binding_confirmed")),
                },
                "output": {
                    "path": expected_leaf["output_path"],
                    "sha256": sha256_bytes(body),
                    "bytes": len(body),
                },
                "mmm": {
                    "ids": list(expected_leaf.get("mmm_ids") or []),
                    "paths": list(expected_leaf.get("mmm_paths") or []),
                    "sha256": dict(expected_leaf.get("mmm_sha256") or {}),
                },
            }
        )
    if seen != set(expected_by_id) or roster.get("accepted_agent_ids") != [row["agent_id"] for row in rows]:
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", child_id)
    max_attempts = roster.get("max_attempts")
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= MAX_RETRIES:
        _refuse("REFUSE_PROVIDER_NESTED_RETRY_LIMIT", child_id)
    return out


def compile_provider_nested_inventory(
    packet_bytes: bytes,
    child_returns: Mapping[str, bytes],
) -> bytes:
    """Compile a canonical inventory from exact child return ZIP bytes."""

    council = validate_provider_nested_packet(packet_bytes)
    parent_packet = validate_packet(packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    parent_entries = _entries(packet_bytes)
    parent_lineage = _lineage_from(parent_entries, packet_id=council.parent_job_id)
    request = _object(parent_entries[SYNTHESIS_REQUEST_PATH], SYNTHESIS_REQUEST_PATH)
    by_id: dict[str, Any] = {}
    all_leaves: list[dict[str, Any]] = []
    for record in request["children"]:
        child_id = record["job_id"]
        if child_id not in child_returns:
            _refuse("REFUSE_PROVIDER_NESTED_CHILD_RETURN_MISSING", child_id)
        child_packet = parent_entries[f"children/{child_id}.zip"]
        _child, child_entries, child_leaves, _lineage_value = _validate_child_packet(
            child_packet,
            parent_id=council.parent_job_id,
            child_id=child_id,
            wave_id=parent_lineage["wave_id"],
            round_value=parent_lineage["round"],
            expected_packet_sha256=record["packet_sha256"],
        )
        child_return = _bytes(child_returns[child_id], child_id)
        leaf_receipts = _receipt_row_for_leaf(
            child_id=child_id,
            child_packet=child_packet,
            child_entries=child_entries,
            child_leaves=child_leaves,
            child_return=child_return,
        )
        child_return_digest = sha256_bytes(child_return)
        by_id[child_id] = {
            "job_id": child_id,
            "parent_id": council.parent_job_id,
            "parent_job_id": council.parent_job_id,
            "depth": 1,
            "packet_sha256": sha256_bytes(child_packet),
            "return_path": record["return_path"],
            "return_sha256": child_return_digest,
            "return_bytes": len(child_return),
            "council_id": record.get("council_id"),
            "leaf_ids": list(record["leaf_ids"]),
            "leaves": leaf_receipts,
        }
        all_leaves.extend(leaf_receipts)
    if [by_id[child_id]["job_id"] for child_id in council.child_job_ids] != list(council.child_job_ids):
        _refuse("REFUSE_PROVIDER_NESTED_CHILD_REBOUND", council.parent_job_id)
    if len({leaf["leaf_id"] for leaf in all_leaves}) != len(all_leaves):
        _refuse("REFUSE_PROVIDER_NESTED_LEAF_IDENTITY", council.parent_job_id)
    inventory = {
        "schema": INVENTORY_SCHEMA,
        "claim_ceiling": INVENTORY_CLAIM_CEILING,
        "parent": {
            "job_id": council.parent_job_id,
            "parent_id": None,
            "parent_job_id": None,
            "depth": 0,
            "packet_sha256": parent_packet.packet_sha256,
            "wave_id": parent_lineage["wave_id"],
            "round": parent_lineage["round"],
        },
        "children": [by_id[child_id] for child_id in council.child_job_ids],
        "leaf_count": len(all_leaves),
        "leaf_ids": [leaf["leaf_id"] for leaf in all_leaves],
        "synthesis_request": {
            "schema": REQUEST_SCHEMA,
            "semantic_consensus": False,
            "instruction": request["instruction"],
            "child_return_paths": [by_id[child_id]["return_path"] for child_id in council.child_job_ids],
            "required_receipts": list(request["required_receipts"]),
            "next_action": "compare_declared_receipts_and_outputs_only",
        },
        "promotion_allowed": False,
    }
    return canonical_json_bytes(inventory)


def run_compile_provider_nested_inventory(
    task: TaskSpec,
    workspace: dict[str, bytes],
) -> dict[str, bytes]:
    """Compile the parent inventory as an ordinary deterministic ZIP operation.

    The runtime manifest is an implicit authority input.  Reconstructing the
    original packet from its registered members lets the existing validator
    bind the exact parent packet while excluding task outputs added later.
    """

    if len(task.output_paths) != 1 or len(task.input_paths) < 7:
        _refuse("REFUSE_OPERATION_ARITY", task.task_id)
    if task.input_paths[:3] != [
        LINEAGE_PATH,
        SYNTHESIS_REQUEST_PATH,
        "inputs/parent_child_records.json",
    ]:
        _refuse("REFUSE_PROVIDER_NESTED_COMPILE_INPUTS", task.task_id)
    if MANIFEST_PATH not in workspace:
        _refuse("REFUSE_MANIFEST_MISSING", task.task_id)
    manifest = _object(workspace[MANIFEST_PATH], MANIFEST_PATH)
    registry = manifest.get("file_sha256_registry")
    if not isinstance(registry, dict) or not registry:
        _refuse("REFUSE_PROVIDER_NESTED_COMPILE_INPUTS", "registry")
    missing = [path for path in registry if path not in workspace]
    if missing:
        _refuse("REFUSE_PROVIDER_NESTED_COMPILE_INPUTS", missing[0])
    packet_bytes = deterministic_zip(
        {
            MANIFEST_PATH: workspace[MANIFEST_PATH],
            **{path: workspace[path] for path in registry},
        }
    )
    request = _object(workspace[SYNTHESIS_REQUEST_PATH], SYNTHESIS_REQUEST_PATH)
    records = request.get("children")
    if not isinstance(records, list) or len(records) != CHILD_COUNT:
        _refuse("REFUSE_PROVIDER_NESTED_CHILD_COUNT", "compile")
    child_returns: dict[str, bytes] = {}
    expected_inputs = {
        LINEAGE_PATH,
        SYNTHESIS_REQUEST_PATH,
        "inputs/parent_child_records.json",
    }
    for record in records:
        if not isinstance(record, dict):
            _refuse("REFUSE_PROVIDER_NESTED_SCHEMA", "compile_child")
        child_id = _text(record.get("job_id"), "compile_child.job_id")
        child_path = f"children/{child_id}.zip"
        return_path = _text(record.get("return_path"), "compile_child.return_path")
        expected_inputs.update({child_path, return_path})
        if child_path not in workspace or return_path not in workspace:
            _refuse("REFUSE_PROVIDER_NESTED_CHILD_RETURN_MISSING", child_id)
        child_returns[child_id] = workspace[return_path]
    if set(task.input_paths) != expected_inputs:
        _refuse("REFUSE_PROVIDER_NESTED_COMPILE_INPUTS", "input_set")
    return {
        task.output_paths[0]: compile_provider_nested_inventory(packet_bytes, child_returns)
    }


@dataclass(frozen=True)
class ProviderNestedCouncil:
    packet_bytes: bytes
    parent_job_id: str
    child_job_ids: tuple[str, ...]
    leaf_ids: tuple[str, ...]
    parent_depth: int = 0

    @property
    def packet_sha256(self) -> str:
        return sha256_bytes(self.packet_bytes)


@dataclass(frozen=True)
class ProviderNestedExecution:
    council: ProviderNestedCouncil
    result: ExecutionResult
    inventory_bytes: bytes
    retained_child_return_sha256: dict[str, str]


def execute_provider_nested_council(
    packet_bytes: bytes,
    *,
    child_returns: Mapping[str, bytes] | None = None,
) -> ProviderNestedExecution:
    """Execute the parent, validate each child return, then compile inventory."""

    council = validate_provider_nested_packet(packet_bytes)
    parent_packet = validate_packet(packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    if child_returns is None:
        try:
            intermediate_result = execute_packet(packet_bytes)
        except ZipJobRefusal:
            # A child failure/exhaustion intentionally emits no parent return.
            raise
        entries = _entries(intermediate_result.return_zip_bytes)
        child_returns = {}
        for child_id in council.child_job_ids:
            path = f"output/{child_id}.return.zip"
            if path not in entries:
                _refuse("REFUSE_PROVIDER_NESTED_CHILD_RETURN_MISSING", child_id)
            child_returns[child_id] = entries[path]
    inventory = compile_provider_nested_inventory(packet_bytes, child_returns)
    if child_returns is not None and len(child_returns) != CHILD_COUNT:
        _refuse("REFUSE_PROVIDER_NESTED_CHILD_RETURN_MISSING", council.parent_job_id)
    if "intermediate_result" not in locals():
        # Caller-supplied returns are for compiler/refusal probes.  Execute the
        # parent only after validating those exact bytes, so no return ZIP is
        # ever minted from an invalid child set.
        intermediate_result = execute_packet(packet_bytes)
    returned_entries = _entries(intermediate_result.return_zip_bytes)
    if returned_entries.get(PARENT_INVENTORY_PATH) != inventory:
        _refuse("REFUSE_PROVIDER_NESTED_INVENTORY_MISMATCH", council.parent_job_id)
    final_result = intermediate_result
    return ProviderNestedExecution(
        council=council,
        result=final_result,
        inventory_bytes=inventory,
        retained_child_return_sha256={
            child_id: sha256_bytes(child_returns[child_id]) for child_id in council.child_job_ids
        },
    )


def build_and_execute_provider_nested_council(**kwargs: Any) -> ProviderNestedExecution:
    packet = build_provider_nested_council_packet(**kwargs)
    return execute_provider_nested_council(packet)


# Short aliases make the module easy to discover without changing the public
# APIs it composes.
build_nested_provider_council = build_provider_nested_council_packet
build_provider_nested_council = build_provider_nested_council_packet
execute_nested_provider_council = execute_provider_nested_council
compile_parent_inventory = compile_provider_nested_inventory


__all__ = [
    "CHILD_COUNT",
    "CLAIM_CEILING",
    "DEFAULT_PARENT_JOB_ID",
    "DEFAULT_WAVE_ID",
    "INVENTORY_SCHEMA",
    "LEAF_MANIFEST_PATH",
    "LINEAGE_PATH",
    "MAX_DEPTH",
    "MAX_RETRIES",
    "PARENT_INVENTORY_PATH",
    "ProviderNestedCouncil",
    "ProviderNestedExecution",
    "SYNTHESIS_REQUEST_PATH",
    "build_and_execute_provider_nested_council",
    "build_nested_provider_council",
    "build_provider_nested_council",
    "build_provider_nested_council_packet",
    "compile_parent_inventory",
    "compile_provider_nested_inventory",
    "execute_nested_provider_council",
    "execute_provider_nested_council",
    "validate_provider_nested_packet",
]
