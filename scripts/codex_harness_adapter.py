#!/usr/bin/env python3
"""Codex anti-collapse receipt adapter.

Validates the small runtime spine needed for plurality-sensitive Codex turns:

    wiki_harness_boot -> mini_mmm_language_body -> task_card -> lane_resolution
    -> runtime_registry -> worker_receipt -> audit -> final answer

The adapter is intentionally stdlib-only and file-shape focused. It does not
spawn workers; it verifies that a user-visible answer only names lanes that
have a real resolution record and, when spawned, a readable receipt.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "runtime_registry.json"

VISIBLE_UNIT_NAMES = (
    "Direct",
    "Hume",
    "Popper",
    "Systems",
    "Factory",
    "Strategy",
    "Feynman",
    "Orwell",
    "Audit",
    "Hygiene",
    "Security",
    "Alternative",
    "Reframe",
    "Wildcard",
    "Back",
    "Zhuangzi",
    "Pushback",
    "LLM Council",
    "All-A",
    "All-B",
    "All-C",
    "All-D",
    "Option 18",
)

VISIBLE_UNIT_ALIASES = {
    "Option 18": "All-D",
}

ALL_D_CHILD_ROWS = tuple(f"Follow-up {index}" for index in range(1, 18)) + (
    "All-D self-check",
    "Follow-up Audit/Improve",
)

SPAWNED_STATES = {"spawned", "spawned_completed", "completed", "ran"}
BLOCKED_STATES = {"blocked", "deferred", "shutdown", "queued", "batched", "reset_pending", "deferred_by_ceiling"}
OPTIONAL_LOCAL_STATES = {"controller_local", "not_spawned"}
LOCAL_RECEIPT_STATES = {"local_receipt"}
CODEX_VISIBLE_STATES = SPAWNED_STATES | BLOCKED_STATES
LIVE_RUNTIME_LOCAL_MARKERS = (
    "local_receipt",
    "local receipt",
    "not spawned",
    "normalization only",
    "scaffold",
    "offline",
)
LIVE_PROVENANCE_PATH_FIELDS = (
    "spawn_receipt_path",
    "agent_receipt_path",
    "live_receipt_path",
)
LIVE_PROVENANCE_SOURCES = {
    "spawn_agent",
    "codex_app_spawn_agent",
    "codex_spawn_agent",
    "spawn_agent_tool",
    "codex_native_spawn_agent",
}

REQUIRED_REGISTRY_FIELDS = {
    "lane",
    "emoji",
    "role",
    "wave",
    "status",
    "worker_id",
    "checked",
    "concluded",
    "open",
    "evidence",
    "blocker_or_defer_reason",
}

REQUIRED_RECEIPT_FIELDS = {
    "lane",
    "checked",
    "concluded",
    "open",
    "evidence",
}

SOURCE_LIFT_GATE_REQUIRED_FIELDS = {
    "gate_id",
    "route_id",
    "source_bundle_ref",
    "source_slice_used",
    "loaded_salience_surfaces",
    "claim_tested",
    "claim_scope",
    "execution_evidence",
    "terminal_status",
    "not_run_or_simulated_accounting",
    "evidence_boundary",
    "lift_probe",
    "counter_probe_seed",
    "label_strip_result",
    "counter_probe_result",
    "strongest_omitted_falsifier",
    "salience_status",
    "gate_verdict",
    "expansion_permission",
}

SOURCE_LIFT_GATE_REQUIRED_KEYS = {
    "raw_launch_receipt_refs",
    "raw_completion_receipt_refs",
}

SOURCE_LIFT_STATUS_AXES = {
    "load_axis",
    "salience_axis",
    "counter_probe_axis",
    "corpus_axis",
}

SOURCE_LIFT_TERMINAL_STATUSES = {
    "completed",
    "blocked",
    "timed_out",
    "rerouted",
    "superseded",
    "simulated",
    "deferred",
}

SOURCE_LIFT_GATE_VERDICTS = {"pass", "harden", "quarantine", "kill"}

REQUIRED_SPAWNED_SPINE_FIELDS = {
    "wiki_harness_boot",
    "mini_mmm_language_body",
    "task_card",
    "lane_resolution",
    "runtime_registry",
    "worker_receipt",
    "audit",
    "final_output_check",
}

LANE_LOCAL_SCOPES = {"lane_local", "voice_local", "unit_local", "overall_context_lane", "overall_context"}

EXCLUDED_AGENCY_TERMS = (
    "cause",
    "causes",
    "create",
    "creates",
    "drive",
    "drives",
    "produce",
    "produces",
    "generate",
    "generates",
    "make",
    "makes",
    "force",
    "forces",
    "determine",
    "determines",
)

HUME_JARGON_TERMS = (
    "impression",
    "idea",
    "custom",
    "constant conjunction",
    "contiguity",
    "experimental reasoning",
    "enquiry",
    "matter of fact",
    "relation of ideas",
    "habit",
)

UNSUPPORTED_STATUS_CLAIMS = (
    "lower engine path is back to passing",
    "owner graph aligns",
    "axis 0 control bridge exists",
    "red maintenance surfaces",
)

REQUIRED_SALIENCE_ROW_FIELDS = {"id", "term", "weight", "row_type", "gloss", "provenance"}

BOOT_CRITICAL_NAME_MARKERS = (
    "POSITIVE_MMM_BOOT_PROMPT",
    "POSITIVE_MINI_MMM_BOOT_PROMPT",
    "README_BOOT_ORDER",
)

BOOT_CRITICAL_BANNED_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9_])contrast(?![A-Za-z0-9_])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])reference(?![A-Za-z0-9_])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])audit(?![A-Za-z0-9_])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])council(?![A-Za-z0-9_])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])synthesis(?![A-Za-z0-9_])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])security(?![A-Za-z0-9_])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])hygiene(?![A-Za-z0-9_])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])bridge(?![A-Za-z0-9_])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])all[-_\s]?(?:[abcd]|of[-_\s]?above)(?![A-Za-z0-9_])", re.IGNORECASE),
)

TAXONOMY_SURFACE_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9])AUDIT(?![A-Za-z0-9])"),
    re.compile(r"(?<![A-Za-z0-9])COUNCIL(?![A-Za-z0-9])"),
    re.compile(r"(?<![A-Za-z0-9])SYNTHESIS(?![A-Za-z0-9])"),
    re.compile(r"(?<![A-Za-z0-9])ALL(?:_[A-Z0-9]+|_OF_ABOVE|-[A-Z0-9]+)?(?![A-Za-z0-9])"),
)

TEXT_SURFACE_SUFFIXES = {".json", ".md", ".txt", ".csv"}


@dataclass(frozen=True)
class Finding:
    code: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "detail": self.detail}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_no}: record must be an object")
            records.append(record)
    return records


def _normalize_state(record: dict[str, Any]) -> str:
    value = record.get("state", record.get("resolution", record.get("status", "")))
    return str(value).strip().lower()


def _normalize_lane(record: dict[str, Any]) -> str:
    return str(record.get("lane", "")).strip()


def _execution_text(text: str) -> str:
    """Ignore proposed follow-up menus when detecting executed visible units."""
    match = re.search(r"(?im)^\s*(?:\*\*)?\s*(?:🪄\s*)?Follow-up\b.*(?:\*\*)?\s*$", text)
    if match:
        return text[: match.start()]
    return text


def _visible_units(text: str) -> set[str]:
    visible: set[str] = set()
    scan_text = _execution_text(text)
    for lane in VISIBLE_UNIT_NAMES:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(lane)}(?![A-Za-z0-9_])", scan_text):
            visible.add(VISIBLE_UNIT_ALIASES.get(lane, lane))
    return visible


def _output_contract_findings(text: str) -> list[Finding]:
    findings: list[Finding] = []
    first_nonblank = next((line.strip() for line in text.splitlines() if line.strip()), "")
    is_wizard_chat = (
        first_nonblank.startswith("🧙 Wizard ")
        or first_nonblank.startswith("Wizard ")
        or first_nonblank.startswith("Wizard:")
    )
    execution_text = _execution_text(text)
    if is_wizard_chat:
        for expected in ("🧙 Main Answer", "📌 Results", "🪄 Follow-up"):
            if expected not in text:
                findings.append(Finding("wizard_chat_missing_section", expected))
        if re.search(r"(?m)^\s*\|.*\|\s*$", execution_text):
            findings.append(Finding("wizard_chat_markdown_table", "chat output should not render wave/route tables"))
        if re.search(r"(?m)^\s*\*\*.+\*\*\s*$", execution_text):
            findings.append(Finding("wizard_chat_markdown_heading", "chat output should not use markdown report headings"))
        if re.search(r"(?im)^\s*(?:\*\*)?\s*(?:🔗\s*)?Compositions\b", execution_text):
            findings.append(Finding("body_compositions_section", "compositions belong in Follow-up only"))
        if re.search(r"(?m)^\s*C(?:[5-9]|1[0-9]|2[0-5])\.", execution_text):
            findings.append(Finding("body_composition_option", "composition IDs belong in Follow-up only"))
        if re.search(r"(?m)^(?:📊\s*)?Quality Audit\b|^🔎\s*Audit\b", execution_text):
            findings.append(Finding("audit_section_default_output", "Audit/Quality Audit should fix the answer; score belongs in footer"))
        if not re.search(r"(?m)^🧙🏽‍♂️ .+ \| .+ \| q:(?:100|[1-9]?\d)/100 \| 🪄 .+$", text):
            findings.append(Finding("missing_footer_quality_score", "footer q:{score}/100"))
    if re.search(r"(?m)^\s*19\.\s", text):
        findings.append(
            Finding(
                "bare_composition_offset_numbering",
                "body uses bare 19./20./21./22. numbering; use C19-C22 IDs or visible 1-18",
            )
        )
    followup_match = re.search(r"(?ims)^\s*(?:\*\*)?🪄 Follow-up\b.*", text)
    if followup_match:
        followup_text = followup_match.group(0)
        if re.search(r"(?m)^\s*V[1-9]\.", followup_text):
            findings.append(
                Finding(
                    "voice_menu_in_followup",
                    "default Follow-up repeats voice menu; use lanes/compositions only unless voice rerun was explicitly requested",
                )
            )
        selection_fields = ("🪄 Follow-up:", "Pre-run status/score:", "Audit:") if is_wizard_chat else ("Outcome:", "Use when:", "Stop/gate:")
        for expected in selection_fields:
            if expected not in followup_text:
                findings.append(Finding("followup_missing_selection_field", expected))
        if is_wizard_chat:
            option_matches = list(re.finditer(r"(?m)^\s*([LC]\d+)\.\s+(.+)$", followup_text))
            expected_options = {"L1", "L2", "L3", "L4", "L5", "L6", "C5", "C6", "C7", "C8", "C9"}
            seen_options = {match.group(1) for match in option_matches}
            for option_id in sorted(seen_options - expected_options):
                findings.append(Finding("followup_unexpected_chat_option", option_id))
            for option_id in sorted(expected_options - seen_options):
                findings.append(Finding("followup_missing_chat_option", f"{option_id}."))
            for index, option_match in enumerate(option_matches):
                start = option_match.end()
                end = option_matches[index + 1].start() if index + 1 < len(option_matches) else len(followup_text)
                block = followup_text[start:end]
                option_id = option_match.group(1)
                for expected in selection_fields:
                    if expected not in block:
                        findings.append(Finding("followup_option_missing_selection_field", f"{option_id}: {expected}"))
                status_match = re.search(r"Pre-run status/score:\s*([^\n]+)", block)
                if status_match:
                    status_line = status_match.group(1).strip()
                    if not re.fullmatch(
                        r"scouted, not executed as current work; (?:100|[1-9]?\d)/100\.",
                        status_line,
                    ):
                        findings.append(Finding("followup_option_bad_status_score", f"{option_id}: {status_line}"))
            for expected in ("Lane follow-ups", "Composition follow-ups"):
                if expected not in followup_text:
                    findings.append(Finding("followup_missing_family_section", expected))
        else:
            for expected in ("Prompt-local", "Context-scale", "Guard compositions", "All-of-above"):
                if expected not in followup_text:
                    findings.append(Finding("followup_missing_scale_section", expected))
            for expected in ("P1.", "S7.", "G10.", "A16."):
                if expected not in followup_text:
                    findings.append(Finding("followup_missing_scale_option", expected))
            for composition in ("C19", "C20", "C21", "C22", "C23", "C24", "C25"):
                match = re.search(rf"(?ms)^{composition}\..*?(?=^C\d+\.|\n\*\*|\Z)", text)
                if match:
                    block = match.group(0)
                    for expected in ("Members:", "Integrated result:", "Tension handled:", "Next gate:"):
                        if expected not in block:
                            findings.append(Finding("composition_missing_integration_field", f"{composition}: {expected}"))
    return findings


def _followup_scout_claims(text: str) -> set[str]:
    followup_match = re.search(r"(?ims)^\s*(?:\*\*)?🪄 Follow-up\b.*", text)
    if not followup_match:
        return set()
    followup_text = followup_match.group(0)
    claims: set[str] = set()
    option_matches = list(re.finditer(r"(?m)^\s*([LC]\d+)\.\s+(.+)$", followup_text))
    for index, option_match in enumerate(option_matches):
        start = option_match.end()
        end = option_matches[index + 1].start() if index + 1 < len(option_matches) else len(followup_text)
        block = followup_text[start:end]
        if re.search(r"(?im)Pre-run status/score:\s*scouted\b", block):
            claims.add(option_match.group(1))
    return claims


def _term_hits(text: str, terms: tuple[str, ...]) -> dict[str, int]:
    lowered = text.lower()
    hits: dict[str, int] = {}
    for term in terms:
        if " " in term:
            count = lowered.count(term)
        else:
            count = len(re.findall(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", lowered))
        if count:
            hits[term] = count
    return hits


def audit_behavior_text(
    text: str,
    *,
    label: str = "text",
    source_kind: str = "output",
    check_hume_jargon: bool = False,
    check_unsupported_status: bool = True,
) -> list[Finding]:
    """Audit MMM source/output text for deterministic leakage signatures."""
    findings: list[Finding] = []
    excluded_hits = _term_hits(text, EXCLUDED_AGENCY_TERMS)
    if excluded_hits:
        rendered = ", ".join(f"{term}={count}" for term, count in sorted(excluded_hits.items()))
        findings.append(Finding("excluded_agency_terms", f"{label}: {rendered}"))

    if check_hume_jargon:
        hume_hits = _term_hits(text, HUME_JARGON_TERMS)
        if hume_hits:
            rendered = ", ".join(f"{term}={count}" for term, count in sorted(hume_hits.items()))
            findings.append(Finding("hume_jargon_terms", f"{label}: {rendered}"))

    if source_kind == "output" and check_unsupported_status:
        unsupported_hits = _term_hits(text, UNSUPPORTED_STATUS_CLAIMS)
        if unsupported_hits:
            rendered = ", ".join(sorted(unsupported_hits))
            findings.append(Finding("unsupported_status_claims", f"{label}: {rendered}"))

    return findings


def audit_behavior_file(
    path: Path,
    *,
    label: str | None = None,
    source_kind: str = "source",
    check_hume_jargon: bool = False,
) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    return audit_behavior_text(
        text,
        label=label or str(path),
        source_kind=source_kind,
        check_hume_jargon=check_hume_jargon,
        check_unsupported_status=False,
    )


def _looks_like_hume_path(path: Path) -> bool:
    return "HUME" in path.name.upper() or "hume" in str(path).lower()


def _looks_like_main_mmm_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return "main_mmm" in parts or path.name.upper().startswith("MMM_MAIN_")


def audit_packet_dir(packet_dir: Path) -> tuple[bool, dict[str, Any]]:
    findings: list[Finding] = []
    scanned: list[str] = []
    for path in sorted(packet_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".json"}:
            continue
        is_main = _looks_like_main_mmm_path(path)
        is_hume = _looks_like_hume_path(path)
        if not is_main and not is_hume:
            continue
        scanned.append(str(path))
        findings.extend(
            audit_behavior_file(
                path,
                source_kind="source",
                check_hume_jargon=is_hume,
            )
        )
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "ok": not findings,
        "packet_dir": str(packet_dir),
        "scanned": scanned,
        "findings": [finding.to_dict() for finding in findings],
    }
    return not findings, report


def _text_surface_paths(packet_dir: Path) -> list[Path]:
    return [
        path
        for path in sorted(packet_dir.rglob("*"))
        if path.is_file() and path.suffix.lower() in TEXT_SURFACE_SUFFIXES
    ]


def _is_boot_critical_path(packet_dir: Path, path: Path) -> bool:
    relative = path.relative_to(packet_dir)
    parts = relative.parts
    if parts and parts[0] == "boot_rules":
        return True
    return any(marker in path.name for marker in BOOT_CRITICAL_NAME_MARKERS)


def _boot_critical_findings(packet_dir: Path, path: Path, text: str) -> list[Finding]:
    if not _is_boot_critical_path(packet_dir, path):
        return []
    hits: list[str] = []
    for pattern in BOOT_CRITICAL_BANNED_PATTERNS:
        for match in pattern.finditer(text):
            hit = match.group(0)
            if hit.lower() not in {item.lower() for item in hits}:
                hits.append(hit)
    if not hits:
        return []
    relative = path.relative_to(packet_dir)
    return [Finding("boot_critical_banned_terms", f"{relative}: {', '.join(sorted(hits, key=str.lower))}")]


def _json_structure_findings(packet_dir: Path, path: Path) -> tuple[Any | None, list[Finding]]:
    relative = path.relative_to(packet_dir)
    try:
        payload = _load_json(path)
    except Exception as exc:  # noqa: BLE001
        return None, [Finding("invalid_json", f"{relative}: {exc}")]
    return payload, []


def _salience_row_findings(packet_dir: Path, path: Path, payload: Any) -> list[Finding]:
    if not isinstance(payload, dict) or "words" not in payload:
        return []
    relative = path.relative_to(packet_dir)
    words = payload.get("words")
    if not isinstance(words, list):
        return [Finding("invalid_salience_words", f"{relative}: words must be a list")]

    findings: list[Finding] = []
    for index, row in enumerate(words, start=1):
        if isinstance(row, list):
            if len(row) != 3:
                findings.append(
                    Finding("invalid_salience_row", f"{relative}: row {index} triplet must be [id, term, weight]")
                )
            continue
        if not isinstance(row, dict):
            findings.append(
                Finding("invalid_salience_row", f"{relative}: row {index} must be an object or [id, term, weight] triplet")
            )
            continue
        missing = sorted(field for field in REQUIRED_SALIENCE_ROW_FIELDS if field not in row)
        if missing:
            findings.append(
                Finding("missing_salience_row_fields", f"{relative}: row {index}: {', '.join(missing)}")
            )
    return findings


def _taxonomy_misplacement_findings(packet_dir: Path, path: Path) -> list[Finding]:
    try:
        relative = path.relative_to(packet_dir)
    except ValueError:
        return []
    parts = relative.parts
    if len(parts) < 4 or parts[0] != "mini_mmms" or parts[2] not in {"voices", "lanes"}:
        return []

    matched = [pattern.search(path.name).group(0) for pattern in TAXONOMY_SURFACE_PATTERNS if pattern.search(path.name)]
    if not matched:
        return []
    return [Finding("taxonomy_misplacement", f"{relative}: {', '.join(sorted(set(matched)))}")]


def audit_structure_dir(packet_dir: Path) -> tuple[bool, dict[str, Any]]:
    findings: list[Finding] = []
    scanned_json: list[str] = []
    scanned_text: list[str] = []
    scanned_salience: list[str] = []

    for path in _text_surface_paths(packet_dir):
        relative = path.relative_to(packet_dir)
        scanned_text.append(str(relative))
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            findings.append(Finding("invalid_text_encoding", f"{relative}: {exc}"))
            continue
        if "\u200d" in text:
            findings.append(Finding("zero_width_joiner", str(relative)))
        findings.extend(_boot_critical_findings(packet_dir, path, text))
        findings.extend(_taxonomy_misplacement_findings(packet_dir, path))

        if path.suffix.lower() != ".json":
            continue
        scanned_json.append(str(relative))
        payload, json_findings = _json_structure_findings(packet_dir, path)
        findings.extend(json_findings)
        if json_findings:
            continue
        salience_findings = _salience_row_findings(packet_dir, path, payload)
        if isinstance(payload, dict) and "words" in payload:
            scanned_salience.append(str(relative))
        findings.extend(salience_findings)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "ok": not findings,
        "packet_dir": str(packet_dir),
        "scanned_json": scanned_json,
        "scanned_salience": scanned_salience,
        "scanned_text": scanned_text,
        "findings": [finding.to_dict() for finding in findings],
    }
    return not findings, report


def _resolve_receipt_path(base_dir: Path, raw_path: Any) -> Path | None:
    if raw_path in (None, ""):
        return None
    path = Path(str(raw_path))
    if not path.is_absolute():
        path = base_dir / path
    return path


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _source_lift_gate_findings(lane: str, receipt: dict[str, Any], *, row_state: str = "") -> list[Finding]:
    gate = receipt.get("source_and_lift_receipt_gate")
    if gate is None:
        return [Finding("missing_source_and_lift_gate", lane)]
    if not isinstance(gate, dict):
        return [Finding("invalid_source_and_lift_gate_shape", lane)]

    findings: list[Finding] = []
    missing = sorted(field for field in SOURCE_LIFT_GATE_REQUIRED_FIELDS if not _present(gate.get(field)))
    if missing:
        findings.append(Finding("missing_source_and_lift_gate_fields", f"{lane}: {', '.join(missing)}"))
    missing_keys = sorted(field for field in SOURCE_LIFT_GATE_REQUIRED_KEYS if field not in gate)
    if missing_keys:
        findings.append(Finding("missing_source_and_lift_gate_keys", f"{lane}: {', '.join(missing_keys)}"))

    terminal_status = str(gate.get("terminal_status", "")).strip().lower()
    if terminal_status and terminal_status not in SOURCE_LIFT_TERMINAL_STATUSES:
        findings.append(Finding("invalid_source_lift_terminal_status", f"{lane}: {terminal_status}"))
    if row_state in SPAWNED_STATES and terminal_status != "completed":
        findings.append(Finding("source_lift_terminal_status_mismatch", f"{lane}: row={row_state} gate={terminal_status or '<empty>'}"))

    gate_verdict = str(gate.get("gate_verdict", "")).strip().lower()
    if gate_verdict and gate_verdict not in SOURCE_LIFT_GATE_VERDICTS:
        findings.append(Finding("invalid_source_lift_gate_verdict", f"{lane}: {gate_verdict}"))

    if not isinstance(gate.get("expansion_permission"), bool):
        findings.append(Finding("invalid_source_lift_expansion_permission", lane))

    salience_status = gate.get("salience_status")
    if not isinstance(salience_status, dict):
        findings.append(Finding("invalid_source_lift_salience_status", lane))
    else:
        missing_axes = sorted(axis for axis in SOURCE_LIFT_STATUS_AXES if not _present(salience_status.get(axis)))
        if missing_axes:
            findings.append(Finding("missing_source_lift_salience_axes", f"{lane}: {', '.join(missing_axes)}"))

    if terminal_status == "completed":
        if not _present(gate.get("raw_launch_receipt_refs")):
            findings.append(Finding("source_lift_missing_launch_refs_for_completed", lane))
        if not _present(gate.get("raw_completion_receipt_refs")):
            findings.append(Finding("source_lift_missing_completion_refs_for_completed", lane))

    if gate_verdict == "pass" and gate.get("expansion_permission") is True:
        boundary = str(gate.get("evidence_boundary", "")).lower()
        if "expand" not in boundary and "expansion" not in boundary:
            findings.append(Finding("source_lift_expansion_without_boundary", lane))

    return findings


def _receipt_findings(
    lane: str,
    receipt_path: Path,
    *,
    require_source_and_lift_gate: bool = False,
    row_state: str = "",
) -> list[Finding]:
    findings: list[Finding] = []
    if not receipt_path.exists():
        return [Finding("missing_receipt_file", f"{lane}: {receipt_path}")]
    try:
        receipt = _load_json(receipt_path)
    except Exception as exc:  # noqa: BLE001
        return [Finding("invalid_receipt_json", f"{lane}: {receipt_path}: {exc}")]
    if not isinstance(receipt, dict):
        return [Finding("invalid_receipt_shape", f"{lane}: receipt must be an object")]

    missing = sorted(field for field in REQUIRED_RECEIPT_FIELDS if not receipt.get(field))
    if missing:
        findings.append(Finding("missing_receipt_fields", f"{lane}: {', '.join(missing)}"))

    receipt_lane = str(receipt.get("lane", "")).strip()
    if receipt_lane and receipt_lane != lane:
        findings.append(Finding("receipt_lane_mismatch", f"{lane}: receipt says {receipt_lane}"))

    if require_source_and_lift_gate:
        findings.extend(_source_lift_gate_findings(lane, receipt, row_state=row_state))

    return findings


def _mini_mmm_findings(lane: str, base_dir: Path, raw_path: Any) -> list[Finding]:
    path = _resolve_receipt_path(base_dir, raw_path)
    if path is None:
        return [Finding("missing_mini_mmm_path", lane)]
    if not path.exists():
        return [Finding("missing_mini_mmm_file", f"{lane}: {path}")]
    try:
        text = path.read_text(encoding="utf-8").strip()
    except Exception as exc:  # noqa: BLE001
        return [Finding("invalid_mini_mmm_file", f"{lane}: {path}: {exc}")]
    if len(text.split()) < 100:
        return [Finding("thin_mini_mmm_language_body", f"{lane}: {path}")]
    return []


def _registry_field_findings(lane: str, record: dict[str, Any]) -> list[Finding]:
    missing = sorted(field for field in REQUIRED_REGISTRY_FIELDS if field not in record)
    if missing:
        return [Finding("missing_registry_fields", f"{lane}: {', '.join(missing)}")]
    return []


def _spine_findings(lane: str, record: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    missing = sorted(field for field in REQUIRED_SPAWNED_SPINE_FIELDS if not record.get(field))
    if missing:
        findings.append(Finding("missing_receipt_spine_fields", f"{lane}: {', '.join(missing)}"))

    scope = str(record.get("mini_mmm_scope", "")).strip()
    if scope not in LANE_LOCAL_SCOPES:
        findings.append(Finding("missing_lane_local_mini_mmm", lane))

    if not record.get("task_card_after_mini_mmm"):
        findings.append(Finding("missing_task_card_after_mini_mmm", lane))

    return findings


def _live_provenance_path(record: dict[str, Any]) -> Any:
    for field in LIVE_PROVENANCE_PATH_FIELDS:
        if record.get(field):
            return record[field]
    return None


def _inline_live_provenance_findings(lane: str, record: dict[str, Any]) -> list[Finding]:
    source = str(record.get("source_tool", record.get("source", ""))).strip().lower()
    timestamp = str(record.get("spawn_timestamp", "")).strip()
    if not source and not timestamp:
        return [Finding("missing_live_provenance_receipt", lane)]

    findings: list[Finding] = []
    if source not in LIVE_PROVENANCE_SOURCES:
        findings.append(Finding("missing_live_provenance_source", lane))
    if not timestamp:
        findings.append(Finding("missing_live_spawn_timestamp", lane))
    else:
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            findings.append(Finding("invalid_live_spawn_timestamp", lane))
    return findings


def _live_provenance_findings(lane: str, record: dict[str, Any], base_dir: Path) -> list[Finding]:
    agent_id = str(record.get("agent_id", "")).strip()
    raw_path = _live_provenance_path(record)
    if raw_path in (None, ""):
        return _inline_live_provenance_findings(lane, record)

    path = _resolve_receipt_path(base_dir, raw_path)
    if path is None:
        return [Finding("missing_live_provenance_receipt", lane)]
    if not path.exists():
        return [Finding("missing_live_provenance_file", f"{lane}: {path}")]

    try:
        payload = _load_json(path)
    except Exception as exc:  # noqa: BLE001
        return [Finding("invalid_live_provenance_json", f"{lane}: {path}: {exc}")]
    if not isinstance(payload, dict):
        return [Finding("invalid_live_provenance_shape", f"{lane}: receipt must be an object")]

    findings: list[Finding] = []
    source = str(payload.get("source", payload.get("receipt_source", payload.get("tool", "")))).strip().lower()
    if source not in LIVE_PROVENANCE_SOURCES:
        findings.append(Finding("missing_live_provenance_source", lane))

    receipt_agent_id = str(payload.get("agent_id", payload.get("agent_path", payload.get("id", "")))).strip()
    if agent_id and receipt_agent_id != agent_id:
        findings.append(Finding("live_agent_id_mismatch", f"{lane}: row={agent_id} receipt={receipt_agent_id or '<empty>'}"))

    status = str(payload.get("status", payload.get("state", ""))).strip().lower()
    if status and status not in SPAWNED_STATES:
        findings.append(Finding("live_provenance_not_spawned", f"{lane}: {status}"))

    return findings


def _live_execution_findings(lane: str, record: dict[str, Any], base_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    state = _normalize_state(record)
    if state in LOCAL_RECEIPT_STATES:
        findings.append(Finding("live_execution_requires_spawned", lane))
        return findings
    if state not in SPAWNED_STATES:
        return findings

    if not str(record.get("agent_id", "")).strip():
        findings.append(Finding("missing_live_agent_id", lane))

    runtime_registry = str(record.get("runtime_registry", "")).strip().lower()
    if not runtime_registry:
        findings.append(Finding("missing_live_runtime_registry", lane))
    elif any(marker in runtime_registry for marker in LIVE_RUNTIME_LOCAL_MARKERS):
        findings.append(Finding("live_execution_contradicts_runtime_registry", lane))

    findings.extend(_live_provenance_findings(lane, record, base_dir))

    return findings


def _followup_scout_findings(claims: set[str], by_lane: dict[str, dict[str, Any]], base_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for option_id in sorted(claims):
        candidate_names = (
            f"Follow-up Scout {option_id}",
            f"Follow-up {option_id}",
            f"{option_id} Scout",
        )
        record = next((by_lane[name] for name in candidate_names if name in by_lane), None)
        if record is None:
            findings.append(Finding("missing_followup_scout_receipt", option_id))
            continue
        state = _normalize_state(record)
        if state in BLOCKED_STATES:
            continue
        if state not in SPAWNED_STATES:
            findings.append(Finding("followup_scout_not_live", f"{option_id}: {state or '<empty>'}"))
            continue
        findings.extend(_live_execution_findings(option_id, record, base_dir))
    return findings


def _all_d_child_findings(by_lane: dict[str, dict[str, Any]]) -> list[Finding]:
    record = by_lane.get("All-D")
    if record is None or _normalize_state(record) not in CODEX_VISIBLE_STATES:
        return []
    missing = [lane for lane in ALL_D_CHILD_ROWS if lane not in by_lane]
    if missing:
        return [Finding("missing_all_d_child_rows", ", ".join(missing))]
    return []


def validate(
    *,
    lane_resolution_path: Path,
    receipts_dir: Path,
    final_answer_path: Path | None,
    allow_controller_local: bool,
    allow_local_receipt: bool = False,
    require_live_execution: bool = False,
    require_source_and_lift_gate: bool = False,
) -> tuple[bool, dict[str, Any]]:
    records = _load_jsonl(lane_resolution_path)
    findings: list[Finding] = []
    by_lane: dict[str, dict[str, Any]] = {}

    for index, record in enumerate(records, start=1):
        lane = _normalize_lane(record)
        state = _normalize_state(record)
        if not lane:
            findings.append(Finding("missing_lane", f"record {index} has no lane"))
            continue
        if lane in by_lane:
            findings.append(Finding("duplicate_lane_resolution", lane))
            continue
        by_lane[lane] = record
        findings.extend(_registry_field_findings(lane, record))

        allowed = (
            CODEX_VISIBLE_STATES
            | LOCAL_RECEIPT_STATES
            | (OPTIONAL_LOCAL_STATES if allow_controller_local else set())
        )
        if state not in allowed:
            findings.append(Finding("invalid_lane_state", f"{lane}: {state or '<empty>'}"))

        if state in SPAWNED_STATES:
            runtime_registry = str(record.get("runtime_registry", "")).lower()
            if "not spawned" in runtime_registry or "normalization only" in runtime_registry:
                findings.append(Finding("spawned_state_contradicts_runtime_registry", lane))
            if not record.get("agent_id") and not record.get("worker_id"):
                findings.append(Finding("missing_worker_id", lane))
            findings.extend(_spine_findings(lane, record))
            findings.extend(
                _mini_mmm_findings(
                    lane,
                    lane_resolution_path.parent,
                    record.get("mini_mmm_path", record.get("mini_mmm_language_body")),
                )
            )
            receipt_path = _resolve_receipt_path(receipts_dir, record.get("receipt_path"))
            if receipt_path is None:
                findings.append(Finding("missing_receipt_path", lane))
            else:
                findings.extend(
                    _receipt_findings(
                        lane,
                        receipt_path,
                        require_source_and_lift_gate=require_source_and_lift_gate,
                        row_state=state,
                    )
                )
            if require_live_execution:
                findings.extend(_live_execution_findings(lane, record, lane_resolution_path.parent))

        if state in BLOCKED_STATES and not (record.get("reason") or record.get("blocker_or_defer_reason")):
            findings.append(Finding("missing_block_or_defer_reason", lane))

        if state in OPTIONAL_LOCAL_STATES and not allow_controller_local:
            findings.append(Finding("controller_local_visible", lane))

        if state in LOCAL_RECEIPT_STATES:
            if not allow_local_receipt:
                findings.append(Finding("local_receipt_not_allowed", lane))
            if require_live_execution:
                findings.append(Finding("live_execution_requires_spawned", lane))
            findings.extend(_spine_findings(lane, record))
            findings.extend(
                _mini_mmm_findings(
                    lane,
                    lane_resolution_path.parent,
                    record.get("mini_mmm_path", record.get("mini_mmm_language_body")),
                )
            )
            receipt_path = _resolve_receipt_path(receipts_dir, record.get("receipt_path"))
            if receipt_path is None:
                findings.append(Finding("missing_receipt_path", lane))
            else:
                findings.extend(
                    _receipt_findings(
                        lane,
                        receipt_path,
                        require_source_and_lift_gate=require_source_and_lift_gate,
                        row_state=state,
                    )
                )

    findings.extend(_all_d_child_findings(by_lane))

    visible: set[str] = set()
    followup_scout_claims: set[str] = set()
    if final_answer_path is not None:
        text = final_answer_path.read_text(encoding="utf-8")
        findings.extend(_output_contract_findings(text))
        visible = _visible_units(text)
        followup_scout_claims = _followup_scout_claims(text)
        for lane in sorted(visible):
            if lane not in by_lane:
                findings.append(Finding("missing_lane_resolution", lane))
                continue
            state = _normalize_state(by_lane[lane])
            if state in OPTIONAL_LOCAL_STATES and not allow_controller_local:
                findings.append(Finding("visible_lane_not_spawned", f"{lane}: {state}"))
            if state in LOCAL_RECEIPT_STATES and not allow_local_receipt:
                findings.append(Finding("visible_lane_local_receipt_not_allowed", f"{lane}: {state}"))
            if require_live_execution and state in LOCAL_RECEIPT_STATES:
                findings.append(Finding("visible_lane_not_live", f"{lane}: {state}"))
            if require_live_execution and state in SPAWNED_STATES:
                findings.extend(_live_execution_findings(lane, by_lane[lane], lane_resolution_path.parent))
        if require_live_execution:
            findings.extend(_followup_scout_findings(followup_scout_claims, by_lane, lane_resolution_path.parent))

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "ok": not findings,
        "lane_resolution_path": str(lane_resolution_path),
        "receipts_dir": str(receipts_dir),
        "final_answer_path": str(final_answer_path) if final_answer_path else None,
        "lanes_seen": sorted(by_lane),
        "visible_lanes": sorted(visible),
        "followup_scout_claims": sorted(followup_scout_claims),
        "require_live_execution": require_live_execution,
        "require_source_and_lift_gate": require_source_and_lift_gate,
        "findings": [finding.to_dict() for finding in findings],
    }
    return not findings, report


def write_registry(path: Path) -> dict[str, Any]:
    registry = {
        "generated_at": datetime.now(UTC).isoformat(),
        "runtime": "codex",
        "model_family": "gpt-5.5",
        "configured": {
            "config_path": "/Users/joshuaeisenhart/.codex/config.toml",
            "mmm_index_path": "/Users/joshuaeisenhart/.codex/mmm/mmm_index.json",
            "mmm_manifest_path": "/Users/joshuaeisenhart/.codex/mmm/manifest.json",
            "mmm_seed_dir": "/Users/joshuaeisenhart/.codex/mmm",
            "model": "gpt-5.5",
            "max_threads": 14,
            "max_depth": 4,
            "multi_agent": True,
            "child_agents_md": True,
        },
        "observed": {
            "top_level_lane_workers_spawned_this_session": 13,
            "stale_completed_agents_count_against_thread_limit": True,
            "subsubagent_depth_tested": False,
        },
        "control_law": {
            "path": "/Users/joshuaeisenhart/.codex/AGENTS.md",
            "documents_configured_max_threads": 14,
            "documents_configured_max_depth": 4,
            "requires_receipt_spine": True,
            "requires_mini_mmm_language_body_per_spawned_lane": True,
            "status": "patched_to_match_config_with_depth_caveat_and_mini_mmm_language_body_gate",
        },
        "claim_ceiling": "top-level worker fanout observed; depth untested; anti-collapse not fixed until mini-MMM receipt spine validates final output",
    }
    path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="validate lane receipts against a final answer")
    validate_parser.add_argument("--lane-resolution", required=True, type=Path)
    validate_parser.add_argument("--receipts-dir", required=True, type=Path)
    validate_parser.add_argument("--final-answer", type=Path)
    validate_parser.add_argument("--allow-controller-local", action="store_true")
    validate_parser.add_argument("--allow-local-receipt", action="store_true")
    validate_parser.add_argument("--require-live-execution", action="store_true")
    validate_parser.add_argument("--require-source-and-lift-gate", action="store_true")
    validate_parser.add_argument("--out", type=Path)

    registry_parser = sub.add_parser("write-registry", help="write current Codex runtime registry facts")
    registry_parser.add_argument("--out", default=DEFAULT_REGISTRY, type=Path)

    behavior_parser = sub.add_parser("audit-behavior", help="audit MMM source or output text leakage")
    behavior_parser.add_argument("paths", nargs="*", type=Path)
    behavior_parser.add_argument("--text", action="append", default=[])
    behavior_parser.add_argument("--source-kind", choices=["source", "output"], default="source")
    behavior_parser.add_argument("--hume", action="store_true", help="also check Hume academic-jargon terms")
    behavior_parser.add_argument("--out", type=Path)

    packet_parser = sub.add_parser("audit-packet", help="audit an MMM packet directory for v2.7 blockers")
    packet_parser.add_argument("packet_dir", type=Path)
    packet_parser.add_argument("--out", type=Path)

    structure_parser = sub.add_parser("audit-structure", help="audit a v2.7 Wizard packet structure")
    structure_parser.add_argument("packet_dir", type=Path)
    structure_parser.add_argument("--out", type=Path)

    args = parser.parse_args(argv)
    if args.command == "validate":
        ok, report = validate(
            lane_resolution_path=args.lane_resolution,
            receipts_dir=args.receipts_dir,
            final_answer_path=args.final_answer,
            allow_controller_local=args.allow_controller_local,
            allow_local_receipt=args.allow_local_receipt,
            require_live_execution=args.require_live_execution,
            require_source_and_lift_gate=args.require_source_and_lift_gate,
        )
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)
        return 0 if ok else 1

    if args.command == "write-registry":
        registry = write_registry(args.out)
        sys.stdout.write(json.dumps(registry, indent=2, sort_keys=True) + "\n")
        return 0

    if args.command == "audit-behavior":
        findings: list[Finding] = []
        for path in args.paths:
            findings.extend(
                audit_behavior_file(
                    path,
                    source_kind=args.source_kind,
                    check_hume_jargon=args.hume,
                )
            )
        for index, text in enumerate(args.text, start=1):
            findings.extend(
                audit_behavior_text(
                    text,
                    label=f"text:{index}",
                    source_kind=args.source_kind,
                    check_hume_jargon=args.hume,
                    check_unsupported_status=args.source_kind == "output",
                )
            )
        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "ok": not findings,
            "findings": [finding.to_dict() for finding in findings],
        }
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)
        return 0 if not findings else 1

    if args.command == "audit-packet":
        ok, report = audit_packet_dir(args.packet_dir)
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)
        return 0 if ok else 1

    if args.command == "audit-structure":
        ok, report = audit_structure_dir(args.packet_dir)
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)
        return 0 if ok else 1

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
