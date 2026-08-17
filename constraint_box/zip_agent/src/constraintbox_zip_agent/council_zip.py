from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Any
import zipfile

from .failure_wave import _manifest, _task
from .md_agent_roster import build_md_agent_roster_packet
from .protocol import (
    SHA256_RE,
    TaskSpec,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    sha256_bytes,
    strict_json_loads,
    validate_return_zip,
)

MARKER = "CB_COUNCIL_ZIP"
MEMBERS = ("failure", "repair", "strategy")
FAILURE_MEMBERS = ("likely", "dangerous", "assumption")
REPAIR_MEMBERS = ("smallest", "test", "ceiling")
STRATEGY_MEMBERS = ("systems_boundary", "object_preservation", "divergent_futures")
FAILURE_DEEP_MEMBERS = (
    "likely",
    "dangerous",
    "assumption",
    "bypass",
    "fail_open",
    "authority_swap",
)
ROLE_CORE_VOICES: dict[str, tuple[str, ...]] = {
    "failure": ("popper", "hume"),
    "repair": ("feynman", "orwell"),
    "strategy": ("strategy", "systems"),
    "likely": ("popper", "hume"),
    "dangerous": ("pushback", "orwell"),
    "assumption": ("zhuangzi", "hume"),
    "bypass": ("factory", "pushback"),
    "fail_open": ("popper", "systems"),
    "authority_swap": ("orwell", "strategy"),
    "smallest": ("feynman", "orwell"),
    "test": ("feynman", "popper"),
    "ceiling": ("hume", "pushback"),
    "systems_boundary": ("systems", "factory"),
    "object_preservation": ("strategy", "pushback"),
    "divergent_futures": ("zhuangzi", "strategy"),
}
COUNCIL_SLOTS: dict[str, tuple[str, ...]] = {
    "failure": ("support: observed", "falsifier:"),
    "failure-deep": ("support: observed", "falsifier:"),
    "repair": ("keep_or_discard:", "live_patch: false"),
    "strategy": ("disposition:",),
    "failure-repair-strategy": ("support: observed",),
}
COUNCIL_MEMBERS = {
    "failure-repair-strategy": MEMBERS,
    "failure": FAILURE_MEMBERS,
    "failure-deep": FAILURE_DEEP_MEMBERS,
    "repair": REPAIR_MEMBERS,
    "strategy": STRATEGY_MEMBERS,
}
VOICES = (
    "factory",
    "feynman",
    "hume",
    "orwell",
    "popper",
    "pushback",
    "strategy",
    "systems",
    "zhuangzi",
)
CLAIM_CEILING = (
    "local_zip_execution_with_declared_md_agents;"
    "not_host_hook;not_mmm_read;not_skill_exec;not_admission;not_release"
)
LOOP_CEILING = "local_deterministic_zip_execution_only;not_model_execution;not_admission;not_release"
SELECTION_ALGO = "cb-mini-mmm-selection-v2"


def assign_mini_mmm_combos(*, seed: int, members: tuple[str, ...] = MEMBERS, voice_count: int | None = None) -> dict[str, list[str]]:
    assigned: dict[str, list[str]] = {}
    used: set[tuple[str, ...]] = set()
    for member in members:
        core = list(ROLE_CORE_VOICES.get(member, ("hume", "popper")))
        digest = hashlib.sha256(f"{seed}:{member}:extras".encode("utf-8")).digest()
        extra_n = digest[0] % 3 if voice_count is None else max(0, voice_count - len(core))
        extras: list[str] = []
        cursor = 1
        pool = [voice for voice in VOICES if voice not in core]
        while len(extras) < extra_n and pool:
            voice = pool[digest[cursor % len(digest)] % len(pool)]
            cursor += 1
            if voice not in extras:
                extras.append(voice)
            if cursor > 64:
                break
        picks = core + extras
        if voice_count is not None:
            picks = picks[:voice_count]
            while len(picks) < voice_count:
                for voice in VOICES:
                    if voice not in picks:
                        picks.append(voice)
                        break
        key = tuple(picks)
        salt = 0
        while key in used:
            salt += 1
            digest = hashlib.sha256(f"{seed}:{member}:extras:{salt}".encode("utf-8")).digest()
            extras = []
            cursor = 0
            pool = [voice for voice in VOICES if voice not in core]
            while len(extras) < extra_n and pool:
                voice = pool[digest[cursor % len(digest)] % len(pool)]
                cursor += 1
                if voice not in extras:
                    extras.append(voice)
            picks = core + extras
            key = tuple(picks)
            if salt > 32:
                break
        used.add(key)
        assigned[member] = list(key)
    return assigned


def bind_live_agent_fields(agent: dict[str, Any], *, paths: dict[str, str]) -> dict[str, Any]:
    bound = dict(agent)
    provider = bound.get("provider")
    if provider == "fixture-subprocess":
        return bound
    runner = paths.get("runner_path")
    if not runner or not Path(runner).is_file():
        raise ZipJobRefusal("HOLD_LIVE_RUNNER_UNBOUND", str(provider))
    bound["runner_path"] = runner
    if provider == "codex-cli":
        home = paths.get("codex_home")
        if not home or not Path(home).is_dir():
            raise ZipJobRefusal("HOLD_CODEX_HOME_UNBOUND", "CODEX_HOME")
        bound["codex_home"] = home
    if provider == "claude-code":
        bridge = paths.get("bridge_path")
        if not bridge or not Path(bridge).is_file():
            raise ZipJobRefusal("HOLD_CLAUDE_BRIDGE_UNBOUND", "bridge_path")
        bound["bridge_path"] = bridge
    return bound


def compare_shadow_lanes(
    *,
    target_sha256: str,
    internal_accepted: list[str],
    external_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema": "constraintbox.council-shadow-compare.v1",
        "target_sha256": target_sha256,
        "internal_accepted": list(internal_accepted),
        "external_findings": external_findings,
        "winner": None,
        "disagreement_preserved": True,
        "internal_not_superior": True,
        "promotion_allowed": False,
        "claim_ceiling": "shadow comparison only; not a merge; not admission",
    }


def _validated_mmm_files(mmm_files: dict[str, bytes]) -> dict[str, bytes]:
    expected = {f"MMMS/{voice}.md" for voice in VOICES}
    if set(mmm_files) != expected:
        missing = sorted(expected - set(mmm_files))
        extra = sorted(set(mmm_files) - expected)
        raise ZipJobRefusal(
            "REFUSE_COUNCIL_ZIP_MMM_SET",
            f"missing={missing};extra={extra}",
        )
    checked: dict[str, bytes] = {}
    for path, raw in mmm_files.items():
        if not isinstance(raw, bytes) or not raw.strip():
            raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_MMM_BYTES", path)
        checked[path] = raw
    return checked


def _validate_bound_prior(
    *,
    label: str,
    expected_council_ids: set[str],
    expected_owner_sha256: str,
    receipts: dict[str, str],
    files: dict[str, bytes],
) -> None:
    receipt_key = f"{label}_return_sha256"
    expected_digest = receipts.get(receipt_key)
    if not isinstance(expected_digest, str) or len(expected_digest) != 64:
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_RECEIPT", receipt_key)
    packet_path = f"input/prior/{label}/packet.zip"
    return_path = f"input/prior/{label}/return.zip"
    packet_bytes = files.get(packet_path)
    return_bytes = files.get(return_path)
    if not isinstance(packet_bytes, bytes) or not isinstance(return_bytes, bytes):
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_RECEIPT", f"{label}_packet_or_return")
    if sha256_bytes(return_bytes) != expected_digest:
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_RECEIPT", f"{label}_return_sha256")
    try:
        validate_return_zip(return_bytes, input_packet_bytes=packet_bytes)
        with zipfile.ZipFile(io.BytesIO(packet_bytes), "r") as archive:
            manifest = strict_json_loads(
                archive.read("input/council_manifest.json"),
                label=f"{label}.input/council_manifest.json",
            )
    except (KeyError, zipfile.BadZipFile, ZipJobRefusal) as exc:
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_RECEIPT", f"{label}_not_council") from exc
    if not isinstance(manifest, dict):
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_RECEIPT", f"{label}_manifest")
    if manifest.get("schema") != "constraintbox.council-zip.v1":
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_RECEIPT", f"{label}_schema")
    if manifest.get("council_id") not in expected_council_ids:
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_RECEIPT", f"{label}_council_id")
    if manifest.get("owner_prompt_sha256") != expected_owner_sha256:
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_RECEIPT", f"{label}_owner")


def build_named_council_packet(
    *,
    council_id: str,
    owner_prompt: bytes,
    seed: int,
    run_id: str,
    agents: list[dict[str, Any]],
    mmm_files: dict[str, bytes],
    extra_files: dict[str, bytes] | None = None,
    bound_receipts: dict[str, str] | None = None,
) -> bytes:
    members = COUNCIL_MEMBERS.get(council_id)
    if members is None:
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_ROSTER", council_id)
    if list(row.get("agent_id") for row in agents) != list(members):
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_ROSTER", "agent_ids")
    receipts = bound_receipts or {}
    owner_sha = sha256_bytes(owner_prompt)
    if council_id == "repair":
        _validate_bound_prior(
            label="failure",
            expected_council_ids={"failure", "failure-deep"},
            expected_owner_sha256=owner_sha,
            receipts=receipts,
            files=extra_files or {},
        )
    if council_id == "strategy":
        _validate_bound_prior(
            label="failure",
            expected_council_ids={"failure", "failure-deep"},
            expected_owner_sha256=owner_sha,
            receipts=receipts,
            files=extra_files or {},
        )
        _validate_bound_prior(
            label="repair",
            expected_council_ids={"repair"},
            expected_owner_sha256=owner_sha,
            receipts=receipts,
            files=extra_files or {},
        )
    combos = assign_mini_mmm_combos(seed=seed, members=members)
    files: dict[str, bytes] = {
        "input/OWNER_PROMPT.bin": owner_prompt,
        "input/STOP.md": (
            b"Stop if undeclared child launch, extra output, missing token, "
            b"or worker self-promotion.\n"
        ),
        "input/CHILD_ZIP_REQUEST.schema.json": canonical_json_bytes(
            {
                "schema": "constraintbox.child-zip-request.v1",
                "rule": "worker may request; CB must validate and launch; worker may not pack or certify",
                "required": ["child_job_id", "operation", "reason"],
            }
        ),
        "SKILLS/council.md": (
            b"Write only the declared council file. Copy tool-token, skill-token, "
            b"and every assigned mmm-token. Do not promote. Do not launch children.\n"
        ),
    }
    files.update(_validated_mmm_files(mmm_files))
    if extra_files:
        overlap = set(extra_files) & set(files)
        if overlap:
            raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_AGENT", ",".join(sorted(overlap)))
        files.update(extra_files)
    for name in members:
        if f"AGENTS/{name}.md" not in files:
            raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_AGENT", name)
    members_out: list[dict[str, Any]] = []
    built_agents: list[dict[str, Any]] = []
    for row in agents:
        agent_id = row["agent_id"]
        voices = combos[agent_id]
        mmm_paths = [f"MMMS/{voice}.md" for voice in voices]
        mmm_sha256 = {path: sha256_bytes(files[path]) for path in mmm_paths}
        skill_sha256 = sha256_bytes(files["SKILLS/council.md"])
        required = list(row.get("required_fragments") or [])
        required.extend(
            [
                f"finding: {MARKER}",
                f"council: {agent_id}",
                f"skill-token: {skill_sha256}",
            ]
        )
        required.extend(COUNCIL_SLOTS.get(council_id, ()))
        for digest in mmm_sha256.values():
            required.append(f"mmm-token: {digest}")
        core = list(ROLE_CORE_VOICES.get(agent_id, ()))
        extras = [voice for voice in voices if voice not in core]
        agent = dict(row)
        agent["forbidden_fragments"] = list(
            dict.fromkeys(
                list(agent.get("forbidden_fragments") or [])
                + [
                    "promotion_allowed: true",
                    "admission: ADMITTED",
                    "CONTINUE_CANDIDATE",
                ]
            )
        )
        agent["mmm_paths"] = mmm_paths
        agent["skill_paths"] = ["SKILLS/council.md"]
        agent["context_paths"] = sorted(
            set(list(agent.get("context_paths") or []) + ["input/OWNER_PROMPT.bin", "input/STOP.md"])
        )
        agent["required_fragments"] = list(dict.fromkeys(required))
        built_agents.append(agent)
        members_out.append(
            {
                "agent_id": agent_id,
                "output_path": agent["output_path"],
                "provider": agent.get("provider"),
                "model_requested": agent.get("model_requested"),
                "mmm_ids": [f"voice:{voice}:compact" for voice in voices],
                "mmm_core": core,
                "mmm_extras": extras,
                "mmm_paths": mmm_paths,
                "mmm_sha256": mmm_sha256,
                "skill_path": "SKILLS/council.md",
                "skill_sha256": skill_sha256,
                "context_paths": list(agent["context_paths"]),
            }
        )
    manifest = {
        "schema": "constraintbox.council-zip.v1",
        "council_id": council_id,
        "run_id": run_id,
        "parent_id": None,
        "round": 1,
        "depth": 0,
        "seed": seed,
        "owner_prompt_sha256": sha256_bytes(owner_prompt),
        "bound_receipts": receipts,
        "selection": {
            "algorithm": SELECTION_ALGO,
            "voice_count": "role_core_plus_seeded_extras",
            "member_voice_counts": {row["agent_id"]: len(row["mmm_ids"]) for row in members_out},
            "voice_variant_request": "compact",
            "seed": seed,
        },
        "members": members_out,
        "required_outputs": [f"output/{name}.md" for name in members] + ["output/roster_receipt.json"],
        "negative_controls": [
            "undeclared extra markdown output",
            "missing tool/skill/mmm token",
            "worker-launched child ZIP",
            "self-promotion",
        ],
        "stop_conditions": [
            "exhausted member",
            "undeclared child",
            "same blocker twice",
        ],
        "child_zip_request_path": "input/CHILD_ZIP_REQUEST.schema.json",
        "mmm_read_proved": False,
        "skill_executed": False,
        "applies_live_patch": False,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    files["input/council_manifest.json"] = canonical_json_bytes(manifest)
    roster = {
        "schema": "constraintbox.md-agent-roster.v1",
        "run_id": run_id,
        "seed": seed,
        "required_marker": MARKER,
        "max_attempts": int(agents[0].get("max_attempts", 1) or 1),
        "timeout_seconds": int(agents[0].get("timeout_seconds", 30) or 30),
        "max_workers": max(3, len(members)),
        "shared_paths": ["input/council_manifest.json"],
        "agents": [
            {
                key: agent[key]
                for key in agent
                if key not in {"max_attempts", "timeout_seconds"}
            }
            for agent in built_agents
        ],
    }
    return build_md_agent_roster_packet(roster=roster, files=files)


def build_three_member_council_packet(
    *,
    owner_prompt: bytes,
    seed: int,
    run_id: str,
    agents: list[dict[str, Any]],
    mmm_files: dict[str, bytes],
    extra_files: dict[str, bytes] | None = None,
) -> bytes:
    return build_named_council_packet(
        council_id="failure-repair-strategy",
        owner_prompt=owner_prompt,
        seed=seed,
        run_id=run_id,
        agents=agents,
        mmm_files=mmm_files,
        extra_files=extra_files,
    )


def build_council_zip_packet(
    *,
    roster: dict[str, Any],
    files: dict[str, bytes],
) -> bytes:
    if roster.get("required_marker") != MARKER:
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_MARKER", "required_marker")
    ids = [row.get("agent_id") for row in roster.get("agents") or []]
    if list(ids) != list(MEMBERS):
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_ROSTER", "agent_ids")
    for name in MEMBERS:
        if f"AGENTS/{name}.md" not in files:
            raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_AGENT", name)
    return build_md_agent_roster_packet(roster=roster, files=files)


def compile_council_loop_state(intent: dict[str, Any]) -> dict[str, Any]:
    if intent.get("schema") != "constraintbox.council-loop-state.v1":
        raise ZipJobRefusal("REFUSE_COUNCIL_LOOP_SCHEMA", "schema")
    owner = intent.get("owner_prompt_sha256")
    if not isinstance(owner, str) or SHA256_RE.fullmatch(owner) is None:
        raise ZipJobRefusal("REFUSE_COUNCIL_LOOP_SCHEMA", "owner_prompt_sha256")
    bound = {
        "failure": intent.get("failure_return_sha256"),
        "repair": intent.get("repair_return_sha256"),
        "strategy": intent.get("strategy_return_sha256"),
    }
    for name, value in bound.items():
        if value is None:
            continue
        if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
            raise ZipJobRefusal("REFUSE_COUNCIL_LOOP_SCHEMA", f"{name}_return_sha256")
    present = {name: value for name, value in bound.items() if isinstance(value, str)}
    if "failure" not in present:
        next_slice = "failure"
    elif "repair" not in present:
        next_slice = "repair"
    elif "strategy" not in present:
        next_slice = "strategy"
    else:
        next_slice = "stop_or_repeat"
    return {
        "schema": "constraintbox.council-loop-compile.v1",
        "owner_prompt_sha256": owner,
        "bound_receipts": present,
        "missing": [name for name in ("failure", "repair", "strategy") if name not in present],
        "disposition": "REQUEST_CONTEXT",
        "next_slice": next_slice,
        "winner": None,
        "internal_not_superior": True,
        "promotion_allowed": False,
        "claim_ceiling": LOOP_CEILING,
    }


def run_council_loop_compile(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    if len(task.input_paths) != 1 or len(task.output_paths) != 1:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    raw = workspace[task.input_paths[0]]
    intent = strict_json_loads(raw, label=task.input_paths[0])
    if not isinstance(intent, dict):
        raise ZipJobRefusal("REFUSE_COUNCIL_LOOP_SCHEMA", "not_object")
    compiled = compile_council_loop_state(intent)
    return {task.output_paths[0]: canonical_json_bytes(compiled)}


def build_council_loop_packet(*, intent: dict[str, Any]) -> bytes:
    files = {
        "00_RUN_ME_FIRST.md": (
            b"# council loop compile\n\nDoes not fill missing children. Does not promote.\n"
        ),
        "inputs/loop_intent.json": canonical_json_bytes(intent),
        "tasks/00_compile.task.json": _task(
            task_id="compile-loop",
            sequence=0,
            operation="compile_council_loop_v1",
            inputs=["inputs/loop_intent.json"],
            outputs=["output/council_loop.json"],
        ),
    }
    return build_packet(
        _manifest(
            job_id="council-loop",
            task_paths=["tasks/00_compile.task.json"],
            outputs=["output/council_loop.json"],
            operations=["compile_council_loop_v1"],
            claim_ceiling=LOOP_CEILING,
        ),
        files,
    )
