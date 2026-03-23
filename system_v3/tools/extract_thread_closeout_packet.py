#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


DIAGNOSES = {
    "healthy_but_ready_to_stop",
    "healthy_but_needs_one_bounded_final_step",
    "stalled",
    "duplicate",
    "drifted_off_scope",
    "metadata_polish_only",
    "waiting_on_external_input",
}

DECISIONS = {
    "STOP",
    "CONTINUE_ONE_BOUNDED_STEP",
    "CORRECT_LANE_LATER",
}

OUTPUT_STATUSES = {
    "complete": "complete",
    "usable but partial": "usable_but_partial",
    "usable_but_partial": "usable_but_partial",
    "not actually reusable": "not_actually_reusable",
    "not_actually_reusable": "not_actually_reusable",
}

HEADING_RE = re.compile(r"^\s*(?:\d+\.\s*)?`?([A-Z0-9_]+)`?:?\s*$", re.MULTILINE)

SECTION_ALIASES = {
    "THREAD": "THREAD",
    "ROLE_LABEL": "ROLE_LABEL",
    "ROLE_AND_SCOPE": "ROLE_AND_SCOPE",
    "ROLE_SCOPE": "ROLE_SCOPE",
    "CURRENT_PHASE": "CURRENT_PHASE",
    "PHASE": "CURRENT_PHASE",
    "BOUNDED_PASS": "BOUNDED_PASS",
    "BOUNDED_PASS_RUN": "BOUNDED_PASS",
    "BOUNDED_RESULT": "RESULT",
    "RESULT": "RESULT",
    "AUDIT_RESULT": "RESULT",
    "EXACT_APPLICATION_PLAN": "RESULT",
    "EXACT_OPERATIONAL_USE_PLAN": "RESULT",
    "PRESERVED_TENSION_NON_SMOOTHED_FINDING": "RESULT",
    "PRESERVED_TENSION": "RESULT",
    "WHAT_I_READ": "WHAT_I_READ",
    "ARTIFACTS_READ": "WHAT_I_READ",
    "FILES_READ": "WHAT_I_READ",
    "WHAT_WAS_READ": "WHAT_I_READ",
    "WHAT_I_UPDATED": "WHAT_I_UPDATED",
    "TOUCHED_FILES": "FILES_TOUCHED",
    "FILES_TOUCHED": "FILES_TOUCHED",
    "INTENTIONALLY_KEPT_REFERENCES": "KEEPERS",
    "WHAT_CAN_BE_DEMOTED_FROM_WARM_VISIBILITY": "KEEPERS",
    "WHAT_MUST_REMAIN_BLOCKED": "RISKS",
    "MODEL_CHOICE": "MODEL_CHOICE",
    "GO_ON_COUNTS": "GO_ON_COUNTS",
    "EXACT_NEXT_GO_ON": "NEXT_STEP",
    "NEXT_GO_ON": "NEXT_STEP",
    "FINAL_STATUS": "FINAL_STATUS",
    "FINAL_DECISION": "FINAL_DECISION",
    "STOP_CONTINUE_CORRECT_DECISION": "FINAL_DECISION",
    "THREAD_DIAGNOSIS": "THREAD_DIAGNOSIS",
    "STRONGEST_OUTPUTS": "STRONGEST_OUTPUTS",
    "STRONGEST_BOUNDED_OUTPUTS": "STRONGEST_OUTPUTS",
    "KEEPERS": "KEEPERS",
    "UNFINISHED_BUT_KEEPING": "KEEPERS",
    "UNFINISHED_BUT_WORTH_KEEPING": "KEEPERS",
    "RISKS": "RISKS",
    "OPEN_RISKS_AND_DRIFT_FLAGS": "RISKS",
    "IF_ONE_MORE_STEP": "IF_ONE_MORE_STEP",
    "HANDOFF_PACKET": "HANDOFF_PACKET",
    "CLOSED_STATEMENT": "CLOSED_STATEMENT",
    "NO_MORE_WORK_STATEMENT": "CLOSED_STATEMENT",
    "SELF_SAVED_RETURN_PATHS": "SELF_SAVED_RETURN_PATHS",
    "WHAT_YOU_UPDATED": "WHAT_YOU_UPDATED",
    "WHAT_YOU_READ": "WHAT_YOU_READ",
}


def _fail(msg: str) -> None:
    raise SystemExit(msg)


def _parse_sections(text: str) -> dict[str, str]:
    matches = list(HEADING_RE.finditer(text))
    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        raw_name = match.group(1)
        name = SECTION_ALIASES.get(_normalize_heading_token(raw_name), raw_name)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()

    current_name: str | None = None
    current_lines: list[str] = []
    for raw_line in text.splitlines():
        heading = _normalize_section_heading(raw_line)
        if heading:
            if current_name is not None:
                existing = sections.get(current_name, "")
                current_text = "\n".join(current_lines).strip()
                sections[current_name] = current_text or existing
            current_name, inline_value = heading
            current_lines = [inline_value] if inline_value else []
            continue
        if current_name is not None:
            current_lines.append(raw_line)
    if current_name is not None:
        existing = sections.get(current_name, "")
        current_text = "\n".join(current_lines).strip()
        sections[current_name] = current_text or existing
    return sections


def _normalize_heading_token(text: str) -> str:
    token = text.strip().strip("`")
    token = re.sub(r"[^A-Za-z0-9]+", "_", token).strip("_")
    return token.upper()


def _normalize_section_heading(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith(("-", "*")):
        return None
    if ":" in stripped:
        left, right = stripped.split(":", 1)
        normalized = SECTION_ALIASES.get(_normalize_heading_token(left))
        if normalized:
            return normalized, right.strip()
    normalized = SECTION_ALIASES.get(_normalize_heading_token(stripped))
    if normalized:
        return normalized, ""
    return None


def _clean_bullet(line: str) -> str:
    return re.sub(r"^\s*[-*]\s*", "", line).strip()


def _nonempty_lines(block: str) -> list[str]:
    return [line.strip() for line in block.splitlines() if line.strip()]


def _strip_leading_field_label(text: str, *labels: str) -> str:
    cleaned = text.strip().strip("`")
    lowered = cleaned.lower()
    for label in labels:
        prefix = f"{label.lower()}:"
        if lowered.startswith(prefix):
            return cleaned[len(prefix):].strip()
    return cleaned


def _extract_choice(block: str, allowed: set[str]) -> str:
    for line in _nonempty_lines(block):
        token = _clean_bullet(line).strip("`")
        if token in allowed:
            return token
    _fail(f"could_not_extract_choice_from:{sorted(allowed)}")


def _extract_decision_from_next_step(block: str) -> str:
    for line in _nonempty_lines(block):
        token = _clean_bullet(line).strip("`")
        if token in DECISIONS:
            return token
    _fail(f"could_not_extract_choice_from:{sorted(DECISIONS)}")


def _extract_role_and_scope(block: str, fallback_label: str) -> dict[str, str]:
    lines = [_clean_bullet(line).strip("`") for line in _nonempty_lines(block)]
    if not lines:
        return {"role_label": fallback_label, "scope": ""}
    normalized_lines = [
        _strip_leading_field_label(
            re.sub(r"\s+", " ", line.replace("`", "")).strip(),
            "current role label",
            "role label",
            "actual scope",
            "scope",
        )
        for line in lines
    ]
    first = normalized_lines[0]
    match = re.match(
        r"^(?P<label>.+?)(?:\s+\([^)]*\))?\s+(?P<scope>(?:one bounded|ran one bounded|run as one bounded).+)$",
        first,
        re.IGNORECASE,
    )
    if match:
        role_label = match.group("label").strip()
        scope = re.sub(r"^(?:ran|run as)\s+", "", match.group("scope").strip(), flags=re.IGNORECASE)
        scope = scope[0].upper() + scope[1:] if scope else ""
        return {"role_label": role_label or fallback_label, "scope": scope}
    role_label = re.sub(r"\s+\([^)]*\)", "", first).strip()
    scope = normalized_lines[1] if len(normalized_lines) > 1 else ""
    return {"role_label": role_label or fallback_label, "scope": scope}


def _extract_paths(block: str) -> list[str]:
    paths: list[str] = []
    for line in _nonempty_lines(block):
        cleaned = _clean_bullet(line).strip("`")
        if cleaned.startswith("/Users/") and cleaned not in paths:
            paths.append(cleaned)
    return paths


def _extract_result_summary(block: str) -> str:
    text = re.sub(r"\s+", " ", " ".join(_nonempty_lines(block))).strip()
    if not text:
        return ""
    match = re.search(r"(.+?[.!?])(?:\s|$)", text)
    return match.group(1).strip() if match else text


def _infer_diagnosis(decision: str) -> str:
    return {
        "STOP": "healthy_but_ready_to_stop",
        "CONTINUE_ONE_BOUNDED_STEP": "healthy_but_needs_one_bounded_final_step",
        "CORRECT_LANE_LATER": "drifted_off_scope",
    }[decision]


def _extract_boot_files(block: str) -> list[str]:
    return [path for path in _extract_paths(block) if path.endswith("system_v3/specs/28_A2_THREAD_BOOT__v1.md")]


def _extract_unresolved_question(result_block: str, decision: str) -> str:
    text = re.sub(r"\s+", " ", result_block).strip()
    if not text:
        return ""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    keyword_sentences = [
        s for s in sentences if re.search(r"\b(still needed|separate|next move|until|before any|requires prep)\b", s, re.IGNORECASE)
    ]
    if keyword_sentences:
        return keyword_sentences[-1]
    if decision == "STOP":
        return "None inside this bounded lane; the worker marked this pass STOP."
    return ""


def _extract_outputs_from_current_shape(
    updated_block: str,
    self_saved_block: str,
    result_block: str,
) -> tuple[list[dict], list[str]]:
    updated_paths = _extract_paths(updated_block)
    self_saved_paths = _extract_paths(self_saved_block)
    summary = _extract_result_summary(result_block) or "Captures the bounded pass result for controller review."
    strongest_outputs: list[dict] = []
    meaningful_updated_paths = [path for path in updated_paths if not path.endswith(".txt")]
    if meaningful_updated_paths:
        for path in meaningful_updated_paths:
            strongest_outputs.append(
                {
                    "artifact_path": path,
                    "why_it_matters": summary,
                    "status": "complete",
                }
            )
    elif self_saved_paths:
        preferred = next((path for path in self_saved_paths if "parallel_codex_worker_returns" in path), self_saved_paths[0])
        strongest_outputs.append(
            {
                "artifact_path": preferred,
                "why_it_matters": summary,
                "status": "complete",
            }
        )

    handoff_paths = list(updated_paths)
    staging_path = next((path for path in self_saved_paths if "thread_closeout_packets" in path), "")
    if staging_path and staging_path not in handoff_paths:
        handoff_paths.append(staging_path)
    if not handoff_paths:
        handoff_paths = list(self_saved_paths)
    return strongest_outputs, handoff_paths


def _extract_outputs(block: str) -> list[dict]:
    outputs: list[dict] = []
    current: dict[str, str] | None = None
    for raw in _nonempty_lines(block):
        line = _clean_bullet(raw).strip("`")
        lowered = line.lower()
        if lowered.startswith("status:"):
            if current is None:
                continue
            status_raw = line.split(":", 1)[1].strip().lower()
            current["status"] = OUTPUT_STATUSES.get(status_raw, status_raw)
            continue
        if " - " in line:
            left, right = line.split(" - ", 1)
            current = {
                "artifact_path": left.strip(),
                "why_it_matters": right.strip(),
                "status": "usable_but_partial",
            }
            outputs.append(current)
            continue
        if current is None:
            current = {
                "artifact_path": line,
                "why_it_matters": "",
                "status": "usable_but_partial",
            }
            outputs.append(current)
        elif not current["why_it_matters"]:
            current["why_it_matters"] = _strip_leading_field_label(line, "why it matters")
    return outputs


def _extract_simple_list(block: str) -> list[str]:
    lines = [_clean_bullet(line).strip("`") for line in _nonempty_lines(block)]
    if len(lines) == 1 and lines[0].strip().lower().startswith("none"):
        return []
    return lines


def _extract_go_on_counts(block: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in _nonempty_lines(block):
        cleaned = _clean_bullet(line).strip("`")
        if ":" not in cleaned:
            continue
        key, value = cleaned.split(":", 1)
        match = re.search(r"-?\d+", value)
        if match:
            counts[_normalize_heading_token(key).lower()] = int(match.group(0))
    return counts


def _extract_mixed_decision(sections: dict[str, str]) -> str:
    final_status = sections.get("FINAL_STATUS", "")
    if final_status:
        for line in _nonempty_lines(final_status):
            token = _clean_bullet(line).strip("`")
            if token in DECISIONS:
                return token

    explicit = sections.get("FINAL_DECISION", "")
    if explicit:
        return _extract_choice(explicit, DECISIONS)

    phase_block = " ".join(
        block for block in (sections.get("CURRENT_PHASE", ""), sections.get("BOUNDED_PASS", "")) if block
    )
    if re.search(r"\bSTOP\b", phase_block, re.IGNORECASE):
        return "STOP"

    next_step = sections.get("NEXT_STEP", "")
    if next_step:
        normalized = re.sub(r"\s+", " ", next_step).strip()
        if re.search(r"\bnone\b", normalized, re.IGNORECASE) or re.search(r"\bstop after\b", normalized, re.IGNORECASE):
            return "STOP"

    counts = _extract_go_on_counts(sections.get("GO_ON_COUNTS", ""))
    if counts.get("thread_action", 0) > 0:
        return "CONTINUE_ONE_BOUNDED_STEP"
    if counts.get("thread_action", 0) == 0 and counts.get("local_scaffolding", 0) == 0:
        return "STOP"

    if next_step:
        return "CONTINUE_ONE_BOUNDED_STEP"
    return "STOP"


def _extract_outputs_from_paths(paths: list[str], summary: str) -> list[dict]:
    if not paths:
        return []
    preferred_paths = [path for path in paths if not path.endswith(".txt")] or paths
    outputs: list[dict] = []
    for path in preferred_paths:
        outputs.append(
            {
                "artifact_path": path,
                "why_it_matters": summary or "Captures the bounded pass result for controller review.",
                "status": "complete",
            }
        )
    return outputs


def _extract_outputs_from_mixed_shape(sections: dict[str, str]) -> tuple[list[dict], list[str]]:
    summary = (
        _extract_result_summary(sections.get("RESULT", ""))
        or _extract_result_summary(sections.get("CURRENT_PHASE", ""))
        or "Captures the bounded pass result for controller review."
    )
    updated_paths = _extract_paths(sections.get("WHAT_I_UPDATED", ""))
    touched_paths = _extract_paths(sections.get("FILES_TOUCHED", ""))
    outputs = _extract_outputs_from_paths(updated_paths or touched_paths, summary)
    handoff_paths = list(updated_paths)
    for path in touched_paths:
        if path not in handoff_paths:
            handoff_paths.append(path)
    return outputs, handoff_paths


def _extract_mixed_if_one_more_step(sections: dict[str, str], decision: str) -> dict:
    if decision != "CONTINUE_ONE_BOUNDED_STEP":
        return {"next_step": "", "touches": [], "stop_condition": ""}
    next_step = re.sub(r"\s+", " ", sections.get("NEXT_STEP", "")).strip()
    return {"next_step": next_step, "touches": [], "stop_condition": ""}


def _extract_mixed_handoff(sections: dict[str, str], decision: str, handoff_paths: list[str]) -> dict:
    next_step = re.sub(r"\s+", " ", sections.get("NEXT_STEP", "")).strip()
    unresolved = ""
    if decision == "STOP":
        unresolved = "None inside this bounded lane; the worker marked this pass STOP."
    elif next_step:
        unresolved = next_step
    return {
        "boot_files": _extract_boot_files(sections.get("WHAT_I_READ", "")),
        "artifact_paths": handoff_paths,
        "unresolved_question": unresolved,
    }


def _derive_closed_statement(sections: dict[str, str], decision: str) -> str:
    explicit = (sections.get("CLOSED_STATEMENT") or "").strip()
    if explicit:
        return explicit

    current_phase = re.sub(r"\s+", " ", sections.get("CURRENT_PHASE", "")).strip()
    if current_phase:
        current_phase = current_phase.rstrip(".")
        if decision == "STOP":
            return f"{current_phase} and should now be considered closed."
        return f"{current_phase} and remains ready for one bounded follow-on step."

    final_status_lines = [line for line in _nonempty_lines(sections.get("FINAL_STATUS", "")) if ":" not in line]
    if final_status_lines:
        return " ".join(_clean_bullet(line) for line in final_status_lines)

    if decision == "STOP":
        return "This bounded pass is complete and should now be considered closed."
    return "This bounded pass is complete and remains ready for one bounded follow-on step."


def _extract_if_one_more_step(block: str) -> dict:
    lines = [_clean_bullet(line).strip("`") for line in _nonempty_lines(block)]
    result = {"next_step": "", "touches": [], "stop_condition": ""}
    if not lines:
        return result
    labeled = {}
    unlabeled = []
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            labeled[key.strip().lower()] = value.strip()
        else:
            unlabeled.append(line)
    result["next_step"] = labeled.get("exact next bounded step") or labeled.get("next step") or (unlabeled[0] if unlabeled else "")
    touches = labeled.get("exact files/artifacts it touches") or labeled.get("touches") or ""
    result["touches"] = [part.strip() for part in touches.split(",") if part.strip()]
    result["stop_condition"] = labeled.get("exact stop condition after that step") or labeled.get("stop condition") or (unlabeled[1] if len(unlabeled) > 1 else "")
    return result


def _extract_handoff(block: str) -> dict:
    lines = [_clean_bullet(line).strip("`") for line in _nonempty_lines(block)]
    boot_files: list[str] = []
    artifact_paths: list[str] = []
    unresolved_question = ""
    mode = None
    for line in lines:
        lower = line.lower().rstrip(":")
        if lower == "boot files":
            mode = "boot"
            continue
        if lower == "artifact paths":
            mode = "artifacts"
            continue
        if lower == "unresolved question":
            mode = "question"
            continue
        if line.lower().startswith("boot files:"):
            mode = None
            value = line.split(":", 1)[1].strip()
            if value:
                boot_files.extend([part.strip() for part in value.split(",") if part.strip()])
            continue
        if line.lower().startswith("artifact paths:"):
            mode = None
            value = line.split(":", 1)[1].strip()
            if value:
                artifact_paths.extend([part.strip() for part in value.split(",") if part.strip()])
            continue
        if line.lower().startswith("unresolved question:"):
            mode = None
            unresolved_question = line.split(":", 1)[1].strip()
            continue
        if mode == "boot":
            boot_files.append(line)
        elif mode == "artifacts":
            artifact_paths.append(line)
        elif mode == "question":
            unresolved_question = line if not unresolved_question else f"{unresolved_question} {line}"
        elif not unresolved_question:
            unresolved_question = line
    return {
        "boot_files": boot_files,
        "artifact_paths": artifact_paths,
        "unresolved_question": unresolved_question,
    }


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_packet(text: str, source_thread_label: str) -> dict:
    sections = _parse_sections(text)
    current_shape = (
        ("NEXT_STEP" in sections or "EXACT_NEXT_GO_ON" in sections)
        and "CLOSED_STATEMENT" in sections
        and "ROLE_AND_SCOPE" in sections
    )
    if current_shape:
        decision = _extract_decision_from_next_step(sections.get("NEXT_STEP") or sections.get("EXACT_NEXT_GO_ON", ""))
        diagnosis = _infer_diagnosis(decision)
    elif any(name in sections for name in ("CURRENT_PHASE", "WHAT_I_READ", "GO_ON_COUNTS", "FINAL_STATUS")):
        decision = _extract_mixed_decision(sections)
        diagnosis = _infer_diagnosis(decision)
    else:
        decision = _extract_choice(sections.get("FINAL_DECISION") or sections.get("STOP_CONTINUE_CORRECT_DECISION", ""), DECISIONS)
        diagnosis = _extract_choice(sections.get("THREAD_DIAGNOSIS", ""), DIAGNOSES)
    if current_shape:
        role_block = sections.get("ROLE_LABEL") or sections.get("ROLE_AND_SCOPE", "")
        role_and_scope = _extract_role_and_scope(role_block, source_thread_label)
        outputs, handoff_paths = _extract_outputs_from_current_shape(
            sections.get("WHAT_YOU_UPDATED", ""),
            sections.get("SELF_SAVED_RETURN_PATHS", ""),
            sections.get("RESULT", ""),
        )
        keepers = []
        risks = []
        one_more = {"next_step": "", "touches": [], "stop_condition": ""}
        handoff = {
            "boot_files": _extract_boot_files(sections.get("WHAT_YOU_READ", "")),
            "artifact_paths": handoff_paths,
            "unresolved_question": _extract_unresolved_question(sections.get("RESULT", ""), decision),
        }
        closed_statement = (sections.get("CLOSED_STATEMENT") or sections.get("NO_MORE_WORK_STATEMENT", "")).strip()
    elif any(name in sections for name in ("CURRENT_PHASE", "WHAT_I_READ", "GO_ON_COUNTS", "FINAL_STATUS")):
        role_label = (sections.get("ROLE_LABEL") or "").strip() or source_thread_label
        role_scope = (
            (sections.get("ROLE_SCOPE") or "").strip()
            or re.sub(r"\s+", " ", sections.get("CURRENT_PHASE", "")).strip()
            or "One bounded pass captured from a mixed-format worker closeout."
        )
        role_and_scope = {"role_label": role_label, "scope": role_scope}
        outputs, handoff_paths = _extract_outputs_from_mixed_shape(sections)
        keepers = _extract_simple_list(sections.get("KEEPERS", ""))
        risks = _extract_simple_list(sections.get("RISKS", ""))
        one_more = _extract_mixed_if_one_more_step(sections, decision)
        handoff = _extract_mixed_handoff(sections, decision, handoff_paths)
        closed_statement = _derive_closed_statement(sections, decision)
    else:
        role_block = sections.get("ROLE_LABEL") or sections.get("ROLE_AND_SCOPE", "")
        role_and_scope = _extract_role_and_scope(role_block, source_thread_label)
        outputs = _extract_outputs(sections.get("STRONGEST_OUTPUTS") or sections.get("STRONGEST_BOUNDED_OUTPUTS", ""))
        if not outputs:
            outputs = []
        keepers = _extract_simple_list(sections.get("KEEPERS") or sections.get("UNFINISHED_BUT_WORTH_KEEPING", ""))
        risks = _extract_simple_list(sections.get("RISKS") or sections.get("OPEN_RISKS_AND_DRIFT_FLAGS", ""))
        one_more = _extract_if_one_more_step(sections.get("IF_ONE_MORE_STEP", ""))
        handoff = _extract_handoff(sections.get("HANDOFF_PACKET", ""))
        closed_statement = (sections.get("CLOSED_STATEMENT") or sections.get("NO_MORE_WORK_STATEMENT", "")).strip()
    if not closed_statement:
        _fail("missing_closed_statement")
    return {
        "schema": "THREAD_CLOSEOUT_PACKET_v1",
        "captured_utc": _now_utc(),
        "source_thread_label": source_thread_label,
        "final_decision": decision,
        "thread_diagnosis": diagnosis,
        "role_and_scope": role_and_scope,
        "strongest_outputs": outputs,
        "keepers": keepers,
        "if_one_more_step": one_more,
        "risks": risks,
        "handoff_packet": handoff,
        "closed_statement": closed_statement,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Extract a THREAD_CLOSEOUT_PACKET_v1 JSON object from a raw thread closeout reply.")
    parser.add_argument("--reply-text", required=True, help="Path to the raw thread closeout reply text file.")
    parser.add_argument("--source-thread-label", required=True, help="Thread label to stamp onto the packet.")
    parser.add_argument("--out-json", required=True, help="Output path for the extracted packet JSON.")
    args = parser.parse_args(argv)

    reply_path = Path(args.reply_text)
    if not reply_path.exists():
        _fail(f"missing_reply_text:{reply_path}")
    packet = _build_packet(reply_path.read_text(encoding="utf-8"), args.source_thread_label)
    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"schema": "THREAD_CLOSEOUT_PACKET_EXTRACT_RESULT_v1", "reply_text": str(reply_path), "out_json": str(out_path), "source_thread_label": args.source_thread_label, "status": "EXTRACTED"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
