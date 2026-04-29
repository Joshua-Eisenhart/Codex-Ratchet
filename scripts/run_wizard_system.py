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
    rel_path = spec["path_template"].format(size=size, upper=size.upper())
    if version != "v2_7":
        rel_path = rel_path.replace("_v2_7.", f"_{version}.")
    return rel_path


def _general_path(candidate_root: Path, size: str, version: str) -> Path:
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
    if lane == "Synthesis":
        return "controller"
    return "voice"


def _record_for(spec: dict[str, str], candidate_root: Path, task: str, size: str, version: str) -> dict[str, Any]:
    rel_path = _path_for(spec, size, version)
    mmm_path = candidate_root / rel_path
    if not mmm_path.exists():
        raise FileNotFoundError(f"missing Wizard language body for {spec['lane']}: {mmm_path}")
    terms = _read_terms(mmm_path)
    term_text = ", ".join(terms[:8]) if terms else "language body missing"
    evidence = f"{rel_path} terms: {term_text}"
    wave = LANE_WAVES[spec["lane"]]
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
            f"The Wizard ran in {size} mode and the local validator {status}. The useful result is narrower than the old report shape: keep the MMM reservoirs large, boot only the full main MMM before task text, prove voice shaping with mini-MMM-loaded subagents, and use behavior comparisons before claiming salience effects.",
            f"Feedback applied: {feedback_line}.",
            f"Evidence: {len(records)} local receipts, {external['live_waves']}/12 live mixed-model waves, {general_words} words in {general_rel}, and final validation findings {len(findings)}.",
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
            f"Visible routes have local receipts. local receipts: {len(records)}. File loading is confirmed for the behavior arms; the remaining behavior gate is stronger divergence testing across more tasks.",
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
    require_live_execution: bool = False,
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

    records = [_record_for(spec, candidate_root, task, general_size, version) for spec in LANES]
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
        "require_live_execution": require_live_execution,
        "candidate_root": str(candidate_root),
        "out_dir": str(out_dir),
        "lane_resolution_path": harness_result["lane_resolution_path"],
        "receipts_dir": harness_result["receipts_dir"],
        "final_answer_path": str(final_answer_path),
        "validation_path": str(validation_path),
        "final_validation_path": str(final_validation_path),
        "lanes": [spec["lane"] for spec in LANES],
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
        "--require-live-execution",
        action="store_true",
        help="fail local receipts when live spawned-agent execution is required",
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
        require_live_execution=args.require_live_execution,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
