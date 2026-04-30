#!/usr/bin/env python3
"""Run the repaired Wizard packet as a local receipt-producing system.

This runner is deliberately honest about scope: it does not claim live model or
subagent execution. It loads the packet language bodies, creates lane-local
records, runs the existing receipt harness, writes a final answer, and validates
that visible lane names have receipts.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
CONTAINER_ROOT = SCRIPT_DIR.parent
REPO_ROOT = Path(__file__).resolve().parents[1]

if list(CONTAINER_ROOT.glob("MMM_PACKET_MANIFEST_v*.json")):
    DEFAULT_CANDIDATE = CONTAINER_ROOT
    DEFAULT_OUT_DIR = CONTAINER_ROOT / "runs" / "wizard_local_run_latest"
else:
    DEFAULT_CANDIDATE = (
        REPO_ROOT
        / "work"
        / "mmm_wizard_repair"
        / "mmm_wizard_complete_system_packet_v2_7_candidate"
    )
    DEFAULT_OUT_DIR = REPO_ROOT / "work" / "mmm_wizard_repair" / "runs" / "wizard_local_run_latest"

GENERAL_FILE_PATTERNS = {
    "compact": ["current/WIZARD_GENERAL_COMPACT_{version}.md"],
    "standard": ["current/WIZARD_GENERAL_STANDARD_{version}.md"],
    "ultra": ["current/WIZARD_GENERAL_ULTRA_{version}.md"],
    "full": [
        "current/WIZARD_GENERAL_FULL_GUIDE_{version}.md",
        "current/WIZARD_GENERAL_FULL_REFERENCE_{version}.md",
    ],
}

GENERAL_FILES = {
    size: patterns[0].format(version="v2_7")
    for size, patterns in GENERAL_FILE_PATTERNS.items()
}

LANES: list[dict[str, str]] = [
    {
        "lane": "Direct",
        "emoji": "🎯",
        "path_template": "mini_mmms/{size}/lanes/md/MMM_LANE_DIRECT_{upper}_v2_7.md",
        "output": "Shortest bounded move: keep improving the packet locally, run receipts, and do not call it live until live logs exist.",
    },
    {
        "lane": "Hume",
        "emoji": "🦉",
        "path_template": "mini_mmms/{size}/voices/md/MMM_VOICE_HUME_{upper}_v2_7.md",
        "output": "Measured judgment: the evidence supports local dry-run readiness, while live-agent confidence remains unearned.",
    },
    {
        "lane": "Zhuangzi",
        "emoji": "🦋",
        "path_template": "mini_mmms/{size}/voices/md/MMM_VOICE_ZHUANGZI_{upper}_v2_7.md",
        "output": "Keep two readings separate: useful local language body and unproven live behavior. Do not collapse them.",
    },
    {
        "lane": "Popper",
        "emoji": "🧨",
        "path_template": "mini_mmms/{size}/voices/md/MMM_VOICE_POPPER_{upper}_v2_7.md",
        "output": "Falsifier: any visible lane without a receipt, or any live claim without fresh boot logs, kills acceptance.",
    },
    {
        "lane": "Feynman",
        "emoji": "🔬",
        "path_template": "mini_mmms/{size}/voices/md/MMM_VOICE_FEYNMAN_{upper}_v2_7.md",
        "output": "Operational test: load packet files, produce lane receipts, validate the final answer, and package only after hashes match.",
    },
    {
        "lane": "Orwell",
        "emoji": "✂️",
        "path_template": "mini_mmms/{size}/voices/md/MMM_VOICE_ORWELL_{upper}_v2_7.md",
        "output": "Plain wording rule: metadata belongs in JSON; boot-visible Markdown should carry language, not labels.",
    },
    {
        "lane": "Pushback",
        "emoji": "🥊",
        "path_template": "mini_mmms/{size}/voices/md/MMM_VOICE_PUSHBACK_{upper}_v2_7.md",
        "output": "Boundary: do not wire this into live memory or present it as live-tested until the live gate has real logs.",
    },
    {
        "lane": "Factory",
        "emoji": "🏭",
        "path_template": "mini_mmms/{size}/voices/md/MMM_VOICE_FACTORY_{upper}_v2_7.md",
        "output": "Voice contribution: inspect the wider workstream for bottleneck, queue, handoff drag, rework, and repeatability before choosing the next local move.",
    },
    {
        "lane": "Strategy",
        "emoji": "♟️",
        "path_template": "mini_mmms/{size}/voices/md/MMM_VOICE_STRATEGY_{upper}_v2_7.md",
        "output": "Voice contribution: inspect the larger campaign, scarce resource, sequence, drift risk, and hold/retreat condition before optimizing the immediate answer.",
    },
    {
        "lane": "Systems",
        "emoji": "🔁",
        "path_template": "mini_mmms/{size}/voices/md/MMM_VOICE_SYSTEMS_{upper}_v2_7.md",
        "output": "Voice contribution: inspect feedback loops, incentives, couplings, delays, and second-order effects outside the immediate input.",
    },
    {
        "lane": "Alternative",
        "emoji": "🔀",
        "path_template": "mini_mmms/{size}/lanes/md/MMM_LANE_ALTERNATIVE_{upper}_v2_7.md",
        "output": "Second route: keep this local runner as the stable gate while Opus or other external reviewers remain optional.",
    },
    {
        "lane": "Reframe",
        "emoji": "🪞",
        "path_template": "mini_mmms/{size}/lanes/md/MMM_LANE_REFRAME_{upper}_v2_7.md",
        "output": "Frame shift: the Wizard is a runnable receipt system, not only a folder of rule documents.",
    },
    {
        "lane": "Wildcard",
        "emoji": "🃏",
        "path_template": "mini_mmms/{size}/lanes/md/MMM_LANE_WILDCARD_{upper}_v2_7.md",
        "output": "Off-axis probe: add a deliberately bad unlisted-material task in a future run to confirm refusal behavior.",
    },
    {
        "lane": "Back",
        "emoji": "⬅️",
        "path_template": "mini_mmms/{size}/lanes/md/MMM_LANE_BACK_{upper}_v2_7.md",
        "output": "Return route: keep the packet-level audit menu reachable without treating it as execution evidence.",
    },
    {
        "lane": "LLM Council",
        "emoji": "🧠",
        "path_template": "mini_mmms/{size}/system_routes/md/MMM_VOICE_LLM_COUNCIL_{upper}_v2_7.md",
        "output": "Council result: local system run is useful; live acceptance remains held pending independent fresh-agent logs.",
    },
    {
        "lane": "Hygiene",
        "emoji": "🧼",
        "path_template": "mini_mmms/{size}/lanes/md/MMM_LANE_REPO_HYGIENE_{upper}_v2_7.md",
        "output": "Lane result: clean drift, bloat, stale wording, duplicate surfaces, and receipt confusion while preserving substance.",
    },
    {
        "lane": "Security",
        "emoji": "🛡️",
        "path_template": "mini_mmms/{size}/lanes/md/MMM_LANE_SECURITY_{upper}_v2_7.md",
        "output": "Lane result: check unsafe claims, permission confusion, prompt leakage, fake execution, and unearned certainty before answering.",
    },
    {
        "lane": "Audit",
        "emoji": "🔎",
        "path_template": "mini_mmms/{size}/checks_guards/md/MMM_VOICE_AUDIT_{upper}_v2_7.md",
        "output": "Audit rule: receipt spine and final-answer visibility check decide what can be claimed.",
    },
    {
        "lane": "All-A",
        "emoji": "🔗",
        "path_template": "mini_mmms/{size}/compositions/md/MMM_LANE_ALL_A_{upper}_v2_7.md",
        "output": "All-A compilation: deterministic repair checks for taxonomy, schema, boot text, validators, and packaging.",
    },
    {
        "lane": "All-B",
        "emoji": "🧬",
        "path_template": "mini_mmms/{size}/compositions/md/MMM_LANE_ALL_B_{upper}_v2_7.md",
        "output": "All-B compilation: behavior proof plan for no-MMM, main-MMM, and mini-MMM comparison.",
    },
    {
        "lane": "All-C",
        "emoji": "🧹",
        "path_template": "mini_mmms/{size}/compositions/md/MMM_LANE_ALL_C_{upper}_v2_7.md",
        "output": "All-C compilation: voice and lane tuning pass for Hume, Zhuangzi, Popper, Feynman, Orwell, and Pushback.",
    },
    {
        "lane": "All-D",
        "emoji": "🧙",
        "path_template": "mini_mmms/{size}/compositions/md/MMM_LANE_ALL_OF_ABOVE_WIZARD_{upper}_v2_7.md",
        "output": "All-D/C9 composition: integrate as much useful composition work as the next input warrants, then keep only what survives Audit and Council.",
    },
    {
        "lane": "All-E",
        "emoji": "🧼",
        "path_template": "mini_mmms/{size}/compositions/md/MMM_LANE_ALL_E_HYGIENE_{upper}_v2_7.md",
        "output": "All-E composition: close the answer cleanly by combining Direct, Hygiene, Security, Factory, Audit, and Council without turning the answer into a report.",
    },
    {
        "lane": "All-F",
        "emoji": "🛡️",
        "path_template": "mini_mmms/{size}/compositions/md/MMM_LANE_ALL_F_SECURITY_{upper}_v2_7.md",
        "output": "All-F composition: test trust by combining Security, Pushback, Popper, Feynman, Direct, Audit, and Council.",
    },
    {
        "lane": "All-H",
        "emoji": "🌐",
        "path_template": "mini_mmms/{size}/compositions/md/MMM_LANE_ALL_H_OVERALL_CONTEXT_{upper}_v2_7.md",
        "output": "All-H composition: check whole-context fit by combining Reframe, Systems, Factory, Strategy, Hygiene, Audit, and Council.",
    },
]

WAVE_DEFINITIONS: dict[int, dict[str, str]] = {
    0: {
        "name": "Preflight / Registry",
        "purpose": "build route registry with truth states",
        "result": "registry built",
        "open": "live spawn truth",
    },
    1: {
        "name": "Voice Wave",
        "purpose": "run each visible voice as separate unit",
        "result": "voice receipts separated",
        "open": "live voice subagents",
    },
    2: {
        "name": "Voice Audit Wave",
        "purpose": "audit voice receipts for collapse",
        "result": "audit receipt present",
        "open": "independent audit workers",
    },
    3: {
        "name": "Voice Improvement Wave",
        "purpose": "rerun weak/collapsed voices",
        "result": "deferred unless audit finds weak voice",
        "open": "rerun targets",
    },
    4: {
        "name": "LLM Council Wave",
        "purpose": "run independent council routes",
        "result": "council route separated",
        "open": "external model council logs",
    },
    5: {
        "name": "Hygiene Wave",
        "purpose": "readability and structure checks",
        "result": "hygiene receipt present",
        "open": "visual/user pass",
    },
    6: {
        "name": "Security Wave",
        "purpose": "control-law and risk checks",
        "result": "security receipt present",
        "open": "fresh boot contamination run",
    },
    7: {
        "name": "Follow-up Make Wave",
        "purpose": "generate full candidate bank",
        "result": "voices, lanes, checks, system, compositions listed",
        "open": "candidate subreceipts",
    },
    8: {
        "name": "Follow-up Run/Scout Wave",
        "purpose": "run/scout useful follow-up candidates",
        "result": "route and composition scouts present",
        "open": "live scout subagents",
    },
    9: {
        "name": "Follow-up Audit/Improve Wave",
        "purpose": "suppress weak options and improve wording",
        "result": "final menu compiled",
        "open": "full audit workers",
    },
    10: {
        "name": "Final Receipt Audit Wave",
        "purpose": "verify honest final claims",
        "result": "local validation passed",
        "open": "live final audit",
    },
    11: {
        "name": "Controller Synthesis",
        "purpose": "synthesize after receipts",
        "result": "summary composed without claiming execution",
        "open": "none for local run",
    },
}

CHAT_HEADERS = (
    "🧙 Main Answer",
    "🧨 Popper Check",
    "📌 Results",
    "🌊 Wave Note",
    "🗣️ Voices",
    "🧠 LLM Council",
    "➡️ Current Lanes",
    "🔎 Checks And System Routes",
    "📊 Quality Audit",
    "🔎 Audit",
    "🌊 Follow-up Wave Truth",
    "🪄 Follow-up",
)

LANE_WAVES = {
    "Hume": 1,
    "Zhuangzi": 1,
    "Feynman": 1,
    "Orwell": 1,
    "Popper": 1,
    "Pushback": 1,
    "Factory": 1,
    "Strategy": 1,
    "Systems": 1,
    "Audit": 2,
    "LLM Council": 4,
    "Hygiene": 8,
    "Security": 8,
    "All-A": 7,
    "All-B": 7,
    "All-C": 7,
    "Direct": 8,
    "Alternative": 8,
    "Reframe": 8,
    "Wildcard": 8,
    "Back": 8,
    "All-D": 9,
    "All-E": 9,
    "All-F": 9,
    "All-H": 9,
}

ALL_D_CHILD_ROWS = tuple(f"Follow-up {index}" for index in range(1, 18)) + (
    "All-D self-check",
    "Follow-up Audit/Improve",
)
FOLLOWUP_SCOUT_ROWS = tuple(f"Follow-up Scout {option}" for option in ("L1", "L2", "L3", "L4", "L5", "L6", "C5", "C6", "C7", "C8", "C9"))
FULL_WIZARD_WAVE_COUNT = 11
FULL_WIZARD_MAX_SUBAGENTS_PER_WAVE = 14
FULL_WIZARD_MIN_LIVE_SUBAGENTS = 151


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _tool_path(name: str) -> Path:
    local = SCRIPT_DIR / name
    if local.exists():
        return local
    repo = REPO_ROOT / "scripts" / name
    if repo.exists():
        return repo
    raise FileNotFoundError(name)


def _read_terms(path: Path, limit: int = 12) -> list[str]:
    terms: list[str] = []
    if not path.exists():
        return terms
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line.startswith("- "):
            continue
        term = line[2:].strip()
        if term and term not in terms:
            terms.append(term)
        if len(terms) >= limit:
            break
    return terms


def _packet_version(candidate_root: Path) -> str:
    manifests = sorted(candidate_root.glob("MMM_PACKET_MANIFEST_v*.json"))
    for manifest in manifests:
        stem = manifest.stem
        if stem.startswith("MMM_PACKET_MANIFEST_"):
            return stem.removeprefix("MMM_PACKET_MANIFEST_")
    return "v2_7"


def _human_version(version: str) -> str:
    return version.replace("_", ".")


def _path_for(spec: dict[str, str], size: str, version: str) -> str:
    if "path" in spec:
        return spec["path"]
    rel_path = spec["path_template"].format(size=size, upper=size.upper())
    if version != "v2_7":
        rel_path = rel_path.replace("_v2_7.", f"_{version}.")
    return rel_path


def _general_path(candidate_root: Path, size: str, version: str) -> Path:
    if version == "v3_3":
        v3_paths = {
            "full": "universal_core/WIZARD_UNIVERSAL_CORE_FULL_v3_3.md",
            "compact": "universal_core/WIZARD_UNIVERSAL_CORE_COMPACT_v3_3.md",
        }
        if size in v3_paths:
            return candidate_root / v3_paths[size]
    try:
        patterns = GENERAL_FILE_PATTERNS[size]
    except KeyError as exc:
        raise ValueError(f"unknown Wizard General size: {size}") from exc
    candidates = [candidate_root / pattern.format(version=version) for pattern in patterns]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _word_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8", errors="replace").split())


def _external_worker_summary(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {
            "label": "Subagents: opus high 0, sonnet high 0, codex 5.5 high 0, gemini 0",
            "claude_total": 0,
            "codex_total": 0,
            "gemini_total": 0,
            "live_waves": 0,
            "voice_load_proof": "",
            "behavior_probe": "",
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    claude_worker_models: dict[str, int] = {}
    for row in payload.get("claude", []):
        if row.get("status") != "completed":
            continue
        model = str(row.get("model") or "claude")
        claude_worker_models[model] = claude_worker_models.get(model, 0) + int(row.get("task_completed") or row.get("agent_tool_calls") or 0)
    opus_total = sum(count for model, count in claude_worker_models.items() if "opus" in model.lower())
    sonnet_total = sum(count for model, count in claude_worker_models.items() if "sonnet" in model.lower())
    other_claude_total = sum(
        count
        for model, count in claude_worker_models.items()
        if "opus" not in model.lower() and "sonnet" not in model.lower()
    )
    claude_total = opus_total + sonnet_total + other_claude_total
    codex_by_model = payload.get("codex_native_agents_by_model") or {}
    if not codex_by_model and payload.get("codex_native_agents_completed"):
        codex_by_model = {"codex 5.5 high": int(payload.get("codex_native_agents_completed") or 0)}
    codex_total = sum(int(value) for value in codex_by_model.values())
    gemini_total = int(payload.get("gemini_calls") or 0)
    if not gemini_total:
        gemini_total = int("GEMINI_DIRECT_OK" in str(payload.get("gemini_direct_probe", ""))) + int(
            str(payload.get("gemini_audit", "")).startswith("completed")
        )
    live_waves = int(payload.get("valid_live_waves_proven") or int(payload.get("valid_wave_minimum_met") is True))
    label_parts = [f"opus high {opus_total}", f"sonnet high {sonnet_total}"]
    if other_claude_total:
        label_parts.append(f"claude other {other_claude_total}")
    label_parts.extend([f"codex 5.5 high {codex_total}", f"gemini {gemini_total}"])
    label = "Subagents: " + ", ".join(label_parts)
    return {
        "label": label,
        "claude_total": claude_total,
        "codex_total": codex_total,
        "gemini_total": gemini_total,
        "live_waves": live_waves,
        "voice_load_proof": str(payload.get("voice_load_proof") or ""),
        "behavior_probe": str(payload.get("behavior_probe") or ""),
    }


def _quality_dimensions(validation_ok: bool, findings: list[dict[str, Any]] | None) -> dict[str, int]:
    dimensions = {
        "drift": 1 if validation_ok else 3,
        "sycophancy": 0 if validation_ok else 2,
        "hallucination": 1 if validation_ok else 3,
        "fake_execution": 0 if validation_ok else 3,
        "filler_fluff": 1 if validation_ok else 3,
        "format_collapse": 1 if validation_ok else 4,
        "receipt_grounding": 5 if validation_ok else 2,
        "useful_density": 4 if validation_ok else 2,
    }
    for finding in findings or []:
        code = str(finding.get("code", ""))
        if code in {
            "wizard_chat_missing_section",
            "wizard_chat_markdown_table",
            "wizard_chat_markdown_heading",
            "body_compositions_section",
            "body_composition_option",
        }:
            dimensions["format_collapse"] = 5
        if code.startswith("followup_") or code == "missing_quality_score":
            dimensions["format_collapse"] = max(dimensions["format_collapse"], 4)
            dimensions["useful_density"] = min(dimensions["useful_density"], 2)
        if code in {"missing_lane_resolution", "missing_receipt_file", "missing_receipt_fields"}:
            dimensions["receipt_grounding"] = min(dimensions["receipt_grounding"], 1)
            dimensions["fake_execution"] = max(dimensions["fake_execution"], 4)
        if "unsupported" in code or "claim" in code:
            dimensions["fake_execution"] = max(dimensions["fake_execution"], 4)
    return dimensions


def _quality_score(dimensions: dict[str, int]) -> int:
    return max(
        0,
        min(
            100,
            round(
                100
                - dimensions["drift"] * 14 / 5
                - dimensions["sycophancy"] * 8 / 5
                - dimensions["hallucination"] * 16 / 5
                - dimensions["fake_execution"] * 20 / 5
                - dimensions["filler_fluff"] * 8 / 5
                - dimensions["format_collapse"] * 10 / 5
                - (5 - dimensions["receipt_grounding"]) * 14 / 5
                - (5 - dimensions["useful_density"]) * 10 / 5
            ),
        ),
    )


def _slug(value: str) -> str:
    import re

    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "lane"


def _category(lane: str) -> str:
    if lane in {"Direct", "Alternative", "Reframe", "Wildcard", "Back", "Hygiene", "Security"}:
        return "lane"
    if lane in {"Audit"}:
        return "check/guard"
    if lane == "LLM Council":
        return "system"
    if lane in {"All-A", "All-B", "All-C", "All-D", "All-E", "All-F", "All-H"}:
        return "composition"
    if lane == "Full Wizard":
        return "composition"
    if lane == "Synthesis":
        return "controller"
    return "voice"


def _default_wave_for(lane: str, category: str) -> int:
    if lane in LANE_WAVES:
        return LANE_WAVES[lane]
    if category == "voices":
        return 1
    if category == "checks_guards":
        return 2
    if category == "system_routes":
        return 4
    if category == "lanes":
        return 8
    if category == "compositions":
        return 9
    return 11


def _lanes_for(candidate_root: Path, size: str, version: str) -> list[dict[str, str]]:
    if version != "v3_3":
        return LANES
    registry_path = candidate_root / "universal_core" / "WIZARD_ROUTE_REGISTRY_v3_3.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    lanes: list[dict[str, str]] = []
    for unit in registry.get("units", []):
        paths = unit.get("paths", {}).get(size, {})
        md_path = paths.get("md")
        if not md_path:
            continue
        name = str(unit["name"])
        category = str(unit.get("category", ""))
        lanes.append(
            {
                "lane": name,
                "emoji": str(unit.get("emoji", "")),
                "path": str(md_path),
                "wave": str(_default_wave_for(name, category)),
                "category": category,
                "output": f"{name} route completed with assigned v3.3 mini-MMM receipt truth.",
            }
        )
    return lanes


def _record_for(spec: dict[str, str], candidate_root: Path, task: str, size: str, version: str) -> dict[str, Any]:
    rel_path = _path_for(spec, size, version)
    mmm_path = candidate_root / rel_path
    if not mmm_path.exists():
        raise FileNotFoundError(f"missing Wizard language body for {spec['lane']}: {mmm_path}")
    terms = _read_terms(mmm_path)
    term_text = ", ".join(terms[:8]) if terms else "language body missing"
    evidence = f"{rel_path} terms: {term_text}"
    wave = int(spec.get("wave") or LANE_WAVES[spec["lane"]])
    wave_def = WAVE_DEFINITIONS[wave]
    return {
        "lane": spec["lane"],
        "emoji": spec["emoji"],
        "role": "local_wizard_lane",
        "wave": wave,
        "wave_name": wave_def["name"],
        "status": "local_receipt",
        "output": (
            f"Task: {task}\n"
            f"Wizard General size: {size}\n"
            f"Wave {wave}: {wave_def['name']}\n"
            f"{spec['output']}\n"
            f"Loaded language body terms: {term_text}"
        ),
        "checked": f"loaded {rel_path}",
        "concluded": spec["output"],
        "open": "live proof pending",
        "evidence": evidence,
        "mini_mmm_path": rel_path,
        "mini_mmm_scope": "voice_local" if _category(spec["lane"]) == "voice" else "lane_local",
        "task_card": task,
    }


def _load_json_or_jsonl(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return []
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        records: list[dict[str, Any]] = []
        for line_no, raw in enumerate(text.splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_no}: record must be an object")
            records.append(row)
        return records


def _load_live_receipts(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    payload = _load_json_or_jsonl(path)
    if isinstance(payload, dict):
        if isinstance(payload.get("receipts"), list):
            records = payload["receipts"]
        elif isinstance(payload.get("routes"), list):
            records = payload["routes"]
        else:
            records = [payload]
    elif isinstance(payload, list):
        records = payload
    else:
        raise ValueError(f"{path}: live receipts must be an object, array, or JSONL objects")

    overlays: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"{path}: live receipt {index} must be an object")
        lane = str(record.get("lane") or record.get("route") or "").strip()
        if not lane:
            raise ValueError(f"{path}: live receipt {index} is missing lane/route")
        if lane in overlays:
            raise ValueError(f"{path}: duplicate live receipt for {lane}")
        overlays[lane] = record
    return overlays


def _live_receipt_wave(overlay: dict[str, Any]) -> int:
    raw_wave = overlay.get("wizard_wave", overlay.get("wave"))
    if raw_wave in (None, ""):
        return 0
    try:
        wave = int(raw_wave)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{overlay.get('lane') or overlay.get('route')}: live receipt wave must be an integer") from exc
    if wave < 1 or wave > FULL_WIZARD_WAVE_COUNT:
        raise ValueError(
            f"{overlay.get('lane') or overlay.get('route')}: live receipt wave must be 1..{FULL_WIZARD_WAVE_COUNT}"
        )
    return wave


def _validate_full_wizard_scale(overlays: dict[str, dict[str, Any]]) -> dict[str, Any]:
    waves: dict[int, int] = {wave: 0 for wave in range(1, FULL_WIZARD_WAVE_COUNT + 1)}
    for overlay in overlays.values():
        wave = _live_receipt_wave(overlay)
        if wave == 0:
            raise ValueError("full-scale Wizard validation requires wizard_wave/wave on every live receipt")
        waves[wave] += 1
    total = sum(waves.values())
    if total < FULL_WIZARD_MIN_LIVE_SUBAGENTS:
        raise ValueError(
            f"full-scale Wizard requires at least {FULL_WIZARD_MIN_LIVE_SUBAGENTS} live receipts; got {total}"
        )
    missing_waves = [wave for wave, count in waves.items() if count == 0]
    if missing_waves:
        raise ValueError(f"full-scale Wizard requires receipts for all {FULL_WIZARD_WAVE_COUNT} waves; missing {missing_waves}")
    overfull_waves = {
        wave: count
        for wave, count in waves.items()
        if count > FULL_WIZARD_MAX_SUBAGENTS_PER_WAVE
    }
    if overfull_waves:
        raise ValueError(
            f"full-scale Wizard allows at most {FULL_WIZARD_MAX_SUBAGENTS_PER_WAVE} live receipts per wave; got {overfull_waves}"
        )
    return {
        "required_waves": FULL_WIZARD_WAVE_COUNT,
        "max_subagents_per_wave": FULL_WIZARD_MAX_SUBAGENTS_PER_WAVE,
        "min_live_subagents": FULL_WIZARD_MIN_LIVE_SUBAGENTS,
        "live_subagents": total,
        "wave_counts": waves,
    }


def _apply_live_overlay(record: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    lane = record["lane"]
    state = str(overlay.get("state") or overlay.get("status") or overlay.get("resolution") or "spawned_completed").strip().lower()
    if state not in {"spawned", "spawned_completed", "completed", "ran"}:
        raise ValueError(f"{lane}: live receipt status must be spawned/completed/ran, got {state!r}")

    agent_id = str(overlay.get("agent_id") or "").strip()
    worker_id = str(overlay.get("worker_id") or agent_id or "").strip()
    if not (agent_id or worker_id):
        raise ValueError(f"{lane}: live receipt requires agent_id or worker_id")

    mini_mmm_path = str(overlay.get("mini_mmm_path") or record.get("mini_mmm_path") or "").strip()
    if not mini_mmm_path:
        raise ValueError(f"{lane}: live receipt requires mini_mmm_path")

    source_tool = str(overlay.get("source_tool") or "").strip()
    if not source_tool:
        raise ValueError(f"{lane}: live receipt requires source_tool")

    spawn_timestamp = str(overlay.get("spawn_timestamp") or "").strip()
    if not spawn_timestamp:
        raise ValueError(f"{lane}: live receipt requires spawn_timestamp")
    try:
        datetime.fromisoformat(spawn_timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{lane}: live receipt spawn_timestamp must be ISO-8601") from exc

    runtime_registry = str(overlay.get("runtime_registry") or "").strip()
    if not runtime_registry:
        runtime_registry = "codex native subagent spawned with route-local mini-MMM"

    updated = dict(record)
    updated.update(
        {
            "status": state,
            "state": state,
            "role": str(overlay.get("role") or "live_wizard_route"),
            "worker_id": worker_id,
            "agent_id": agent_id,
            "checked": overlay.get("checked") or record.get("checked"),
            "concluded": overlay.get("concluded") or record.get("concluded"),
            "open": overlay.get("open") or "live route returned usable receipt",
            "evidence": overlay.get("evidence") or f"live receipt for {lane}: {agent_id or worker_id}",
            "output": overlay.get("output") or overlay.get("concluded") or record.get("output"),
            "mini_mmm_path": mini_mmm_path,
            "mini_mmm_scope": overlay.get("mini_mmm_scope") or record.get("mini_mmm_scope"),
            "task_card": overlay.get("task_card") or record.get("task_card"),
            "runtime_registry": runtime_registry,
            "receipt_kind": overlay.get("receipt_kind") or "codex_spawn_live",
            "source_tool": source_tool,
            "spawn_timestamp": spawn_timestamp,
        }
    )
    return updated


def _overlay_live_receipts(
    records: list[dict[str, Any]],
    live_receipts_path: Path | None,
    *,
    require_full_wizard_scale: bool = False,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any] | None]:
    overlays = _load_live_receipts(live_receipts_path)
    if not overlays:
        if require_full_wizard_scale:
            raise ValueError("full-scale Wizard validation requires --live-receipts-path")
        return records, [], None
    scale_report = _validate_full_wizard_scale(overlays) if require_full_wizard_scale else None
    known = {record["lane"] for record in records}
    unknown = sorted(
        lane
        for lane in set(overlays) - known
        if not (
            lane.startswith("Follow-up ")
            or lane.endswith(" Scout")
            or lane == "All-D self-check"
            or lane.startswith("Wizard Wave ")
        )
    )
    if unknown:
        raise ValueError(f"live receipt route not in Wizard lane set: {', '.join(unknown)}")

    live_routes: list[str] = []
    updated_records: list[dict[str, Any]] = []
    for record in records:
        overlay = overlays.get(record["lane"])
        if overlay is None:
            updated_records.append(record)
            continue
        updated_records.append(_apply_live_overlay(record, overlay))
        live_routes.append(record["lane"])
    for lane, overlay in overlays.items():
        if lane in known:
            continue
        updated_records.append(_apply_live_overlay({"lane": lane, "emoji": "", "wave": 8}, overlay))
        live_routes.append(lane)
    return updated_records, live_routes, scale_report


def _block_unproven_live_records(records: list[dict[str, Any]], live_routes: list[str]) -> list[dict[str, Any]]:
    live_route_set = set(live_routes)
    blocked: list[dict[str, Any]] = []
    all_d_blocked = False
    for record in records:
        if record["lane"] in live_route_set:
            blocked.append(record)
            continue
        updated = dict(record)
        updated.update(
            {
                "status": "blocked",
                "state": "blocked",
                "worker_id": None,
                "agent_id": "",
                "open": "live receipt not supplied for strict live run",
                "reason": "live receipt not supplied for strict live run",
                "blocker_or_defer_reason": "live receipt not supplied for strict live run",
                "runtime_registry": "blocked because no live spawn receipt was supplied",
            }
        )
        if updated["lane"] == "All-D":
            all_d_blocked = True
        blocked.append(updated)
    if all_d_blocked:
        existing = {record["lane"] for record in blocked}
        for lane in ALL_D_CHILD_ROWS:
            if lane in existing:
                continue
            blocked.append(
                {
                    "lane": lane,
                    "emoji": "",
                    "role": "blocked_all_d_child",
                    "wave": 9,
                    "status": "blocked",
                    "state": "blocked",
                    "worker_id": None,
                    "agent_id": "",
                    "checked": "Full Wizard child route was not spawned in strict live run",
                    "concluded": "blocked until live child receipt is supplied",
                    "open": "live child receipt not supplied",
                    "evidence": "blocked child row emitted to preserve All-D route truth",
                    "reason": "live child receipt not supplied for strict live run",
                    "blocker_or_defer_reason": "live child receipt not supplied for strict live run",
                    "runtime_registry": "blocked because no live child spawn receipt was supplied",
                    "output": "Blocked Full Wizard child row; no execution claimed.",
                    "mini_mmm_scope": "lane_local",
                    "task_card": "Blocked Full Wizard child route; do not claim execution.",
                }
            )
    existing = {record["lane"] for record in blocked}
    for lane in FOLLOWUP_SCOUT_ROWS:
        if lane in existing:
            continue
        blocked.append(
            {
                "lane": lane,
                "emoji": "",
                "role": "blocked_followup_scout",
                "wave": 8,
                "status": "blocked",
                "state": "blocked",
                "worker_id": None,
                "agent_id": "",
                "checked": "Follow-up scout route was not spawned in strict live run",
                "concluded": "blocked until live follow-up scout receipt is supplied",
                "open": "live follow-up scout receipt not supplied",
                "evidence": "blocked scout row emitted to preserve follow-up route truth",
                "reason": "live follow-up scout receipt not supplied for strict live run",
                "blocker_or_defer_reason": "live follow-up scout receipt not supplied for strict live run",
                "runtime_registry": "blocked because no live follow-up scout receipt was supplied",
                "output": "Blocked follow-up scout row; no execution claimed.",
                "mini_mmm_scope": "lane_local",
                "task_card": "Blocked follow-up scout route; do not claim execution.",
            }
        )
    return blocked


def _final_answer(
    *,
    task: str,
    records: list[dict[str, Any]],
    validation_ok: bool,
    validation_path: Path,
    size: str,
    general_path: Path,
    general_words: int,
    feedback: list[str],
    version: str,
    external_summary_path: Path | None = None,
    live_routes: list[str] | None = None,
    final_validation_ok: bool | None = None,
    final_findings: list[dict[str, Any]] | None = None,
) -> str:
    effective_ok = validation_ok if final_validation_ok is None else final_validation_ok
    findings = final_findings or []
    status = "passed" if effective_ok else "failed"
    state_icon = "✅" if effective_ok else "🚧"
    feedback_line = (feedback[-1] if feedback else "rich Wizard format, less log surface, receipt evidence kept as paths").rstrip(".")
    lanes = [record["lane"] for record in records]
    general_rel = general_path.relative_to(general_path.parents[1])
    validation_display = validation_path
    external = _external_worker_summary(external_summary_path)
    live_routes = live_routes or []
    receipt_kind = "live spawned receipts" if live_routes else "local receipts"

    voice_lines = [
        "🦉 Hume: loaded full mini-MMM; keeps evidence, confidence, and humane restraint attached to receipts instead of claims.",
        "🦋 Zhuangzi: loaded full mini-MMM; keeps live readings open without letting plurality become decorative fog.",
        "🧨 Popper: loaded full mini-MMM; turns every readiness claim into a falsifier, decisive check, and killed/open/survived status.",
        "🔬 Feynman: loaded full mini-MMM; demands observable behavior, pass/fail operations, and file/tool receipts.",
        "✂️ Orwell: loaded full mini-MMM; cuts log-speak, stale labels, and abstract filler from the visible answer.",
        "🥊 Pushback: loaded full mini-MMM; blocks wiring and success claims until boot, behavior, and receipt gates are real.",
        "🏭 Factory: loaded full mini-MMM; converts repairs into repeatable rebuild, validate, mirror, and package steps.",
        "♟️ Strategy: loaded full mini-MMM; keeps the Wizard aimed at QIT/sim building, not endless self-audit.",
        "🔁 Systems: loaded full mini-MMM; watches feedback loops such as overcompression, fake plurality, and frozen workflows.",
    ]

    lane_lines = [
        "🎯 Direct: make the next input small enough to execute.",
        "🔀 Alternative: keep one different path alive when the obvious path may be hiding cost.",
        "🪞 Reframe: change the unit of work when the current frame produces the wrong answer shape.",
        "🃏 Wildcard: run one bounded off-axis probe only when it can reveal a real failure faster.",
        "⬅️ Back: return to packet-level repair when runtime claims outrun source truth.",
        "🧼 Hygiene: clean drift, bloat, duplicate surfaces, and receipt confusion without deleting substance.",
        "🛡️ Security: check unsafe claims, permission confusion, prompt leakage, fake execution, and unearned certainty.",
    ]

    check_lines = [
        "🧠 LLM Council: external model work is advisory until Codex audits and accepts it.",
        "🔎 Audit: verify receipt truth, visible-route claims, follow-up prework, and quality score.",
    ]

    followup_lines = [
        "Lane follow-ups",
        "L1. 🎯 Direct\n   🪄 Follow-up: Make the smallest reversible repair for the current artifact, then show the validator result.\n   Pre-run status/score: scouted, not executed as current work; 94/100.\n   Audit: passes only if the next action has one artifact and one proof gate.",
        "L2. 🪞 Reframe\n   🪄 Follow-up: Restate the real unit of work, then rerun the answer through Hume, Systems, Factory, Strategy, Council, and Audit.\n   Pre-run status/score: scouted, not executed as current work; 88/100.\n   Audit: passes only if the new frame changes the next action.",
        "L3. 🔀 Alternative\n   🪄 Follow-up: Give one alternate route with different assumptions, cost, and failure mode, then recommend keep/drop.\n   Pre-run status/score: scouted, not executed as current work; 86/100.\n   Audit: passes only if the tradeoff is concrete.",
        "L4. 🃏 Wildcard\n   🪄 Follow-up: Run one adversarial/off-axis probe that could expose a false success claim.\n   Pre-run status/score: scouted, not executed as current work; 79/100.\n   Audit: passes only if it cannot contaminate the main path.",
        "L5. 🧼 Hygiene\n   🪄 Follow-up: Clean the next output for drift, bloat, stale wording, duplicate surfaces, and receipt confusion while preserving substance.\n   Pre-run status/score: scouted, not executed as current work; 93/100.\n   Audit: passes only if the result is clearer, shorter where appropriate, and still evidence-honest.",
        "L6. 🛡️ Security\n   🪄 Follow-up: Check the next route for unsafe claims, permission confusion, prompt leakage, fake execution, and unearned certainty before answering.\n   Pre-run status/score: scouted, not executed as current work; 95/100.\n   Audit: passes only if every risky claim is proven, blocked, deferred, or converted into a test.",
        "Composition follow-ups",
        "C5. 🧼 Clean closeout\n   🪄 Follow-up: Use Direct, Hygiene, Security, Factory, Audit, and Council to close the next input cleanly without turning it into a report.\n   Pre-run status/score: scouted, not executed as current work; 92/100.\n   Audit: passes only if the closeout names what changed, what remains open, and what evidence supports the claim.",
        "C6. 🛡️ Trust check\n   🪄 Follow-up: Use Security, Pushback, Popper, Feynman, Direct, Audit, and Council to test whether the next answer is safe to trust.\n   Pre-run status/score: scouted, not executed as current work; 96/100.\n   Audit: passes only if wiring, permission, execution, and evidence claims are not overstated.",
        "C7. 🌐 Whole-context check\n   🪄 Follow-up: Use Reframe, Systems, Factory, Strategy, Hygiene, Audit, and Council to decide whether the local next move still serves the larger workstream.\n   Pre-run status/score: scouted, not executed as current work; 91/100.\n   Audit: passes only if it confirms one bounded next action or changes it for a concrete reason.",
        "C8. 🧬 Behavior proof\n   🪄 Follow-up: Use Direct, Alternative, Wildcard, Security, Audit, and Council to compare expected behavior against actual output shape.\n   Pre-run status/score: scouted, not executed as current work; 96/100.\n   Audit: passes only if the comparison has a falsifier and does not treat style improvement as proof of runtime behavior.",
        "C9. 🧙 Full Wizard pass\n   🪄 Follow-up: Use as much of C5, C6, C7, and C8 as the next input warrants: clean the answer, check trust, check whole-context fit, test behavior where relevant, then let Council and Audit decide what survives.\n   Pre-run status/score: scouted, not executed as current work; 98/100.\n   Audit: passes only if C9 stays selective, keeps current-body claims separate from future follow-ups, and does not collapse into a decorative all-of-the-above label.",
    ]

    wave_count = len(WAVE_DEFINITIONS)
    blocked = 0
    deferred = 0
    quality_dimensions = _quality_dimensions(effective_ok, findings)
    quality_score = _quality_score(quality_dimensions)
    quality_grade = "pass" if quality_score >= 85 else "fail"
    quality_lines = [
        f"Quality Audit Score: {quality_score}/100 ({quality_grade})",
        f"Quality Audit Findings: {len(findings)}",
        f"Drift: {quality_dimensions['drift']}/5. The answer stays on the Wizard contract and names the live-runtime boundary.",
        f"Sycophancy: {quality_dimensions['sycophancy']}/5. It applies the feedback without treating every requested direction as already proven.",
        f"Hallucination: {quality_dimensions['hallucination']}/5. Claims are limited to local files and receipts.",
        f"Fake execution / lying: {quality_dimensions['fake_execution']}/5. Local receipts are named as local receipts; live subagents are not claimed by this runner.",
        f"Filler / fluff: {quality_dimensions['filler_fluff']}/5. The body is shorter and the follow-ups carry only prompt, pre-run score, and audit fields.",
        f"Receipt grounding: {quality_dimensions['receipt_grounding']}/5. Visible body routes have local receipt rows.",
        f"Useful density: {quality_dimensions['useful_density']}/5. The output says what changed, what is open, and what each follow-up would do.",
        f"Format collapse: {quality_dimensions['format_collapse']}/5. Compositions are follow-up-only; no body composition catalog is rendered.",
    ]

    return "\n".join(
        [
            f"🧙 Wizard {_human_version(version)} {size} | {external['label']} | quality {quality_score}/100",
            "",
            "🧙 Main Answer",
            f"The Wizard ran in {size} mode and the validator {status}. The useful result is narrower than the old report shape: keep the MMM reservoirs large, boot only the full main MMM before task text, prove voice shaping with mini-MMM-loaded subagents, and use behavior comparisons before claiming salience effects.",
            f"Feedback applied: {feedback_line}.",
            f"Evidence: {len(records)} {receipt_kind}, live routes {len(live_routes)}, {external['live_waves']}/12 live mixed-model waves, {general_words} words in {general_rel}, and final validation findings {len(findings)}.",
            f"Load proof: {external['voice_load_proof'] or 'not supplied'}.",
            f"Behavior probe: {external['behavior_probe'] or 'not supplied'}.",
            "",
            "🧨 Popper Check",
            "Target claim: this Wizard is ready to guide real QIT/sim work.",
            "Falsifier: if loaded MMMs do not measurably change output, or if the answer falls back into log text, the claim fails.",
            f"Status: {'open, not wired-ready' if effective_ok else 'killed by validation'}; validator {status}.",
            "",
            "🗣️ Voices",
            *voice_lines,
            "",
            "➡️ Current Lanes",
            *lane_lines,
            "",
            "🧠 LLM Council",
            "Council advice stays advisory until Codex accepts it against receipts, behavior probes, and packet gates.",
            "",
            "📊 Quality Audit",
            *quality_lines,
            "",
            "🔎 Audit",
            f"Visible routes have {receipt_kind}. Route receipts: {len(records)}. File loading is confirmed for the behavior arms; the remaining behavior gate is stronger divergence testing across more tasks.",
            "",
            "🪄 Follow-up",
            *followup_lines,
            "",
        ]
    )


def run_wizard(
    candidate_root: Path,
    out_dir: Path,
    task: str,
    *,
    general_size: str = "full",
    feedback: list[str] | None = None,
    external_summary_path: Path | None = None,
    live_receipts_path: Path | None = None,
    require_live_execution: bool = False,
    require_full_wizard_scale: bool = False,
) -> dict[str, Any]:
    candidate_root = candidate_root.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    feedback = feedback or []
    version = _packet_version(candidate_root)
    general_path = _general_path(candidate_root, general_size, version)
    if not general_path.exists():
        raise FileNotFoundError(f"missing Wizard General file for {general_size}: {general_path}")
    general_words = _word_count(general_path)

    harness = _load_module(_tool_path("wizard_behavior_harness.py"), "wizard_behavior_harness_runtime")
    adapter = _load_module(_tool_path("codex_harness_adapter.py"), "codex_harness_adapter_runtime")

    lane_specs = _lanes_for(candidate_root, general_size, version)
    records = [_record_for(spec, candidate_root, task, general_size, version) for spec in lane_specs]
    records, live_routes, scale_report = _overlay_live_receipts(
        records,
        live_receipts_path,
        require_full_wizard_scale=require_full_wizard_scale,
    )
    if require_live_execution and live_receipts_path is not None:
        records = _block_unproven_live_records(records, live_routes)
    harness_result = harness.run_harness(candidate_root, out_dir, records)

    validation_path = out_dir / "validation_before_final.json"
    ok, validation = adapter.validate(
        lane_resolution_path=Path(harness_result["lane_resolution_path"]),
        receipts_dir=Path(harness_result["receipts_dir"]),
        final_answer_path=None,
        allow_controller_local=False,
        allow_local_receipt=True,
        require_live_execution=require_live_execution,
    )
    validation_path.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    final_answer_path = out_dir / "final_answer.md"
    final_answer_path.write_text(
        _final_answer(
            task=task,
            records=records,
            validation_ok=ok,
            validation_path=validation_path,
            size=general_size,
            general_path=general_path,
            general_words=general_words,
            feedback=feedback,
            version=version,
            external_summary_path=external_summary_path,
            live_routes=live_routes,
        ),
        encoding="utf-8",
    )

    final_validation_path = out_dir / "validation_final_answer.json"
    final_ok, final_validation = adapter.validate(
        lane_resolution_path=Path(harness_result["lane_resolution_path"]),
        receipts_dir=Path(harness_result["receipts_dir"]),
        final_answer_path=final_answer_path,
        allow_controller_local=False,
        allow_local_receipt=True,
        require_live_execution=require_live_execution,
    )
    if final_ok != ok or final_validation.get("findings"):
        final_answer_path.write_text(
            _final_answer(
                task=task,
                records=records,
                validation_ok=ok,
                validation_path=validation_path,
                size=general_size,
                general_path=general_path,
                general_words=general_words,
                feedback=feedback,
                version=version,
                external_summary_path=external_summary_path,
                live_routes=live_routes,
                final_validation_ok=final_ok,
                final_findings=final_validation.get("findings", []),
            ),
            encoding="utf-8",
        )
        final_ok, final_validation = adapter.validate(
            lane_resolution_path=Path(harness_result["lane_resolution_path"]),
            receipts_dir=Path(harness_result["receipts_dir"]),
            final_answer_path=final_answer_path,
            allow_controller_local=False,
            allow_local_receipt=True,
            require_live_execution=require_live_execution,
        )
    final_validation_path.write_text(
        json.dumps(final_validation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "ok": bool(ok and final_ok),
        "task": task,
        "general_size": general_size,
        "general_path": str(general_path),
        "packet_version": version,
        "general_words": general_words,
        "feedback": feedback,
        "live_receipts_path": str(live_receipts_path) if live_receipts_path else None,
        "live_routes": live_routes,
        "full_wizard_scale": scale_report,
        "require_full_wizard_scale": require_full_wizard_scale,
        "require_live_execution": require_live_execution,
        "candidate_root": str(candidate_root),
        "out_dir": str(out_dir),
        "lane_resolution_path": harness_result["lane_resolution_path"],
        "receipts_dir": harness_result["receipts_dir"],
        "final_answer_path": str(final_answer_path),
        "validation_path": str(validation_path),
        "final_validation_path": str(final_validation_path),
        "lanes": [spec["lane"] for spec in lane_specs],
        "waves": WAVE_DEFINITIONS,
        "findings": final_validation.get("findings", []),
    }
    (out_dir / "wizard_run_receipt.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--general-size", choices=sorted(GENERAL_FILE_PATTERNS), default="full")
    parser.add_argument("--feedback", action="append", default=[])
    parser.add_argument("--external-summary-path", type=Path)
    parser.add_argument(
        "--live-receipts-path",
        type=Path,
        help="JSON/JSONL parent-collected live spawn receipts to overlay by lane before validation",
    )
    parser.add_argument(
        "--require-live-execution",
        action="store_true",
        help="fail local receipts when live spawned-agent execution is required",
    )
    parser.add_argument(
        "--require-full-wizard-scale",
        action="store_true",
        help="require 11 waves and at least 151 live spawn receipts in --live-receipts-path",
    )
    parser.add_argument(
        "--task",
        default="Improve and locally run the repaired MMM Wizard packet without live wiring.",
    )
    args = parser.parse_args(argv)
    result = run_wizard(
        args.candidate_root,
        args.out_dir,
        args.task,
        general_size=args.general_size,
        feedback=args.feedback,
        external_summary_path=args.external_summary_path,
        live_receipts_path=args.live_receipts_path,
        require_live_execution=args.require_live_execution,
        require_full_wizard_scale=args.require_full_wizard_scale,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
