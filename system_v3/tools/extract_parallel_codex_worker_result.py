#!/usr/bin/env python3
"""Normalize one raw parallel Codex worker return into JSON for C0 evaluation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER"}
ALLOWED_NEXT_STEPS = {
    "STOP",
    "ONE_MORE_BOUNDED_A2_PASS_NEEDED",
    "ONE_MORE_BOUNDED_A1_PASS_NEEDED",
}


def extract_section(text: str, heading: str) -> str:
    pattern = rf"(?m)^\s*(?:\d+\.\s*)?{re.escape(heading)}\s*$"
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"Missing section: {heading}")
    start = match.end()
    next_match = re.search(r"(?m)^\s*\d+\.\s+[A-Z0-9_]+(?:\s|$)", text[start:])
    if next_match:
        end = start + next_match.start()
        return text[start:end].strip()
    return text[start:].strip()


def parse_next_step(section: str) -> tuple[str, str]:
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    if not lines:
        raise ValueError("NEXT_STEP section is empty")
    next_step = lines[0]
    if next_step not in ALLOWED_NEXT_STEPS:
        raise ValueError(f"Invalid NEXT_STEP: {next_step}")
    remainder = "\n".join(lines[1:]).strip()
    return next_step, remainder


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract one parallel Codex worker raw return into normalized JSON."
    )
    parser.add_argument("--reply-text", required=True, help="Path to raw worker return text")
    parser.add_argument("--dispatch-id", required=True, help="Dispatch id for this worker result")
    parser.add_argument(
        "--thread-class",
        required=True,
        choices=sorted(ALLOWED_THREAD_CLASSES),
        help="Worker class",
    )
    parser.add_argument("--out-json", required=True, help="Output JSON path")
    args = parser.parse_args()

    raw_path = Path(args.reply_text)
    out_path = Path(args.out_json)
    text = raw_path.read_text(encoding="utf-8")

    role_and_scope = extract_section(text, "ROLE_AND_SCOPE")
    what_you_read = extract_section(text, "WHAT_YOU_READ")
    what_you_updated = extract_section(text, "WHAT_YOU_UPDATED")
    next_step_section = extract_section(text, "NEXT_STEP")
    closed_statement = extract_section(text, "CLOSED_STATEMENT")

    known_headings = {
        "ROLE_AND_SCOPE",
        "WHAT_YOU_READ",
        "WHAT_YOU_UPDATED",
        "NEXT_STEP",
        "IF_ONE_MORE_PASS",
        "CLOSED_STATEMENT",
    }
    result_heading_match = re.search(
        r"(?m)^\s*\d+\.\s+([A-Z0-9_]+)\s*$", text
    )
    # Find first non-control numbered heading after WHAT_YOU_UPDATED.
    result_heading = None
    for match in re.finditer(r"(?m)^\s*\d+\.\s+([A-Z0-9_]+)\s*$", text):
        candidate = match.group(1)
        if candidate not in known_headings:
            result_heading = candidate
            break
    if result_heading is None:
        raise ValueError("Missing worker result section")
    result_section_body = extract_section(text, result_heading)

    next_step, trailing = parse_next_step(next_step_section)
    if_one_more_pass = ""
    if next_step != "STOP":
        try:
            if_one_more_pass = extract_section(text, "IF_ONE_MORE_PASS")
        except ValueError:
            if trailing:
                if_one_more_pass = trailing
            else:
                raise ValueError("Missing IF_ONE_MORE_PASS for continuation result")

    packet = {
        "packet_type": "PARALLEL_CODEX_WORKER_RESULT_v1",
        "dispatch_id": args.dispatch_id,
        "thread_class": args.thread_class,
        "role_and_scope": role_and_scope,
        "what_you_read": what_you_read,
        "what_you_updated": what_you_updated,
        "result_section_name": result_heading,
        "result_section_body": result_section_body,
        "next_step": next_step,
        "if_one_more_pass": if_one_more_pass,
        "closed_statement": closed_statement,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
