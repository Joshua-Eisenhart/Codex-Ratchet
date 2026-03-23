#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER", "A2_CONTROLLER"}
ALLOWED_NEXT_STEPS = {"STOP", "ONE_MORE_BOUNDED_A1_PASS_NEEDED", "ONE_MORE_BOUNDED_A2_PASS_NEEDED", "ONE_MORE_BOUNDED_PASS_NEEDED"}

HEADING_RE = re.compile(r"^\s*(?:\d+\.\s*)?`?([A-Z0-9_]+)`?\s*$", re.MULTILINE)
KNOWN_HEADINGS = {
    "ROLE_AND_SCOPE",
    "WHAT_YOU_READ",
    "WHAT_YOU_UPDATED",
    "FAMILY_RESULT",
    "NEGATIVE_AND_RESCUE_RESULT",
    "NEXT_STEP",
    "IF_ONE_MORE_PASS",
    "CLOSED_STATEMENT",
}


def _fail(msg: str) -> None:
    raise SystemExit(msg)


def _parse_sections(text: str) -> dict[str, str]:
    matches = [match for match in HEADING_RE.finditer(text) if match.group(1) in KNOWN_HEADINGS]
    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        name = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()
    return sections


def _clean_bullet(line: str) -> str:
    return re.sub(r"^\s*[-*]\s*", "", line).strip()


def _nonempty_lines(block: str) -> list[str]:
    return [line.strip() for line in block.splitlines() if line.strip()]


def _extract_simple_list(block: str) -> list[str]:
    return [_clean_bullet(line).strip("`") for line in _nonempty_lines(block)]


def _extract_role_and_scope(block: str, fallback_role: str, fallback_scope: str) -> dict[str, str]:
    lines = _extract_simple_list(block)
    role = lines[0] if lines else fallback_role
    scope = lines[1] if len(lines) > 1 else fallback_scope
    return {"role": role, "scope": scope}


def _extract_next_step(block: str) -> str:
    for line in _extract_simple_list(block):
        token = line.strip("`")
        if token in ALLOWED_NEXT_STEPS:
            if token == "ONE_MORE_BOUNDED_A1_PASS_NEEDED" or token == "ONE_MORE_BOUNDED_A2_PASS_NEEDED":
                return "ONE_MORE_BOUNDED_PASS_NEEDED"
            return token
    _fail("missing_or_invalid_next_step")


def _extract_if_one_more_pass(block: str) -> dict:
    lines = _extract_simple_list(block)
    result = {"next_step": "", "touches": [], "stop_condition": ""}
    if not lines:
        return result
    labeled: dict[str, str] = {}
    unlabeled: list[str] = []
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            labeled[key.strip().lower()] = value.strip()
        else:
            unlabeled.append(line)
    result["next_step"] = labeled.get("one exact next bounded a1 step") or labeled.get("one exact next bounded a2 step") or labeled.get("exact next bounded step") or labeled.get("next step") or (unlabeled[0] if unlabeled else "")
    touches = labeled.get("exact touched files or artifact families") or labeled.get("exact files/artifacts it touches") or labeled.get("touches") or ""
    if touches:
        result["touches"] = [part.strip() for part in touches.split(",") if part.strip()]
    result["stop_condition"] = labeled.get("exact stop condition after that step") or labeled.get("stop condition") or (unlabeled[1] if len(unlabeled) > 1 else "")
    return result


def _extract_updated(block: str) -> tuple[list[str], bool]:
    lines = _extract_simple_list(block)
    if len(lines) == 1 and lines[0].upper() == "NONE":
        return [], True
    if len(lines) == 1 and "no repo artifact was updated" in lines[0].lower():
        return [], True
    return lines, False


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_packet(
    text: str,
    target_thread_id: str,
    thread_class: str,
    boot_surface: str,
    source_decision_record: str,
    expected_return_shape: str,
    fallback_role: str,
    fallback_scope: str,
    continuation_count: int,
) -> dict:
    if thread_class not in ALLOWED_THREAD_CLASSES:
        _fail("invalid_thread_class")

    sections = _parse_sections(text)
    role_and_scope = _extract_role_and_scope(sections.get("ROLE_AND_SCOPE", ""), fallback_role, fallback_scope)
    what_you_read = _extract_simple_list(sections.get("WHAT_YOU_READ", ""))
    if not what_you_read:
        _fail("missing_what_you_read")
    what_you_updated, bounded_no_change = _extract_updated(sections.get("WHAT_YOU_UPDATED", ""))
    next_step = _extract_next_step(sections.get("NEXT_STEP", ""))
    if_one_more = _extract_if_one_more_pass(sections.get("IF_ONE_MORE_PASS", ""))
    result_summary = (sections.get("FAMILY_RESULT", "") + "\n\n" + sections.get("NEGATIVE_AND_RESCUE_RESULT", "")).strip()
    return {
        "schema": "AUTO_GO_ON_THREAD_RESULT_v1",
        "target_thread_id": target_thread_id,
        "thread_class": thread_class,
        "role_and_scope": role_and_scope,
        "what_you_read": what_you_read,
        "what_you_updated": what_you_updated,
        "what_you_updated_is_bounded_no_change": bounded_no_change,
        "next_step": next_step,
        "if_one_more_pass": if_one_more,
        "continuation_count": continuation_count,
        "source_decision_record": source_decision_record,
        "boot_surface": boot_surface,
        "expected_return_shape": expected_return_shape,
        "blocked_case_flags": [],
        "result_summary": result_summary,
        "thread_platform": "CODEX",
        "captured_utc": _now_utc(),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Normalize one returned thread prose result into AUTO_GO_ON_THREAD_RESULT_v1.")
    parser.add_argument("--reply-text", required=True, help="Path to the raw thread result text.")
    parser.add_argument("--out-json", required=True, help="Output path for normalized JSON.")
    parser.add_argument("--target-thread-id", required=True, help="Exact target thread id.")
    parser.add_argument("--thread-class", required=True, choices=sorted(ALLOWED_THREAD_CLASSES), help="Thread class.")
    parser.add_argument("--boot-surface", required=True, help="Exact boot surface path.")
    parser.add_argument("--source-decision-record", required=True, help="Exact repo path to decision/summary record.")
    parser.add_argument("--expected-return-shape", required=True, help="Expected minimum return shape after one more pass.")
    parser.add_argument("--fallback-role", default="", help="Fallback role if ROLE_AND_SCOPE is missing.")
    parser.add_argument("--fallback-scope", default="", help="Fallback scope if ROLE_AND_SCOPE is missing.")
    parser.add_argument("--continuation-count", type=int, default=0, help="Continuation count since last manual review.")
    args = parser.parse_args(argv)

    reply_path = Path(args.reply_text)
    if not reply_path.exists():
        _fail(f"missing_reply_text:{reply_path}")

    packet = _build_packet(
        reply_path.read_text(encoding="utf-8"),
        args.target_thread_id,
        args.thread_class,
        args.boot_surface,
        args.source_decision_record,
        args.expected_return_shape,
        args.fallback_role,
        args.fallback_scope,
        args.continuation_count,
    )
    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "schema": "AUTO_GO_ON_THREAD_RESULT_EXTRACT_RESULT_v1",
                "reply_text": str(reply_path),
                "out_json": str(out_path),
                "target_thread_id": args.target_thread_id,
                "thread_class": args.thread_class,
                "status": "EXTRACTED",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
