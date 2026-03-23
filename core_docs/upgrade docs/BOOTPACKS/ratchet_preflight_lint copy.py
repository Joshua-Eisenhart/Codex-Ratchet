#!/usr/bin/env python3
"""
ratchet_preflight_lint.py

Purpose:
  Quick offline linting for Thread-B paste payloads (EXPORT_BLOCK / SIM_EVIDENCE blocks).

This is intentionally conservative:
  - flags obvious "will HALT the kernel" issues (wrong markers, multiple containers in one message,
    stray prose, comment lines, markdown fences, REQUIRES MATH_TOKEN, etc.)
  - does NOT attempt to fully validate the kernel schema (Thread-B is the source of truth).

Usage:
  python ratchet_preflight_lint.py path/to/file.txt
  python ratchet_preflight_lint.py --split path/to/tape.txt out_dir

Notes:
  - A *Thread-B message* must contain exactly one EXPORT_BLOCK OR one SAVE_SNAPSHOT OR a SIM_EVIDENCE pack.
  - A *tape file* may contain multiple EXPORT_BLOCKs; you must paste them one at a time.
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


EXPORT_BEGIN = "BEGIN EXPORT_BLOCK v1"
EXPORT_END   = "END EXPORT_BLOCK v1"

EVID_BEGIN   = "BEGIN SIM_EVIDENCE v1"
EVID_END     = "END SIM_EVIDENCE v1"

SAVE_BEGIN   = "BEGIN SAVE_SNAPSHOT v1"
SAVE_END     = "END SAVE_SNAPSHOT v1"

FORBIDDEN_SUBSTRINGS = [
    "```",          # markdown fences
    "<<<", ">>>",    # old markers
    "->", "<-", "=>", "=<", ">=", "<=", "≠", "≈", "∴", "∵",
]

# Very common kernel-halters
REQUIRES_MATH_TOKEN_RE = re.compile(r"^\s*REQUIRES\b.*\bMATH_TOKEN\b", re.IGNORECASE)
COMMENT_LINE_RE = re.compile(r"^\s*#")  # comments are NOT allowed inside EXPORT_BLOCK

ALLOWED_LINE_PREFIXES = (
    "BEGIN", "END",
    "EXPORT_ID:", "GENERATOR:", "SCOPE:", "DATE:", "BRANCH_ID:",
    "AXIOM_HYP", "PROBE_HYP", "SPEC_HYP", "MATH_DEF", "SIM_SPEC", "CANON_PERMIT", "BAN",
    "SPEC_KIND", "REQUIRES", "DEF_FIELD", "ASSERT", "NEGATIVE_TEST",
)

@dataclass
class Block:
    kind: str  # EXPORT / EVID / SAVE
    start_line: int
    end_line: int
    lines: List[str]


def find_blocks(lines: List[str]) -> List[Block]:
    blocks: List[Block] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].rstrip("\n")

        if line.strip() == EXPORT_BEGIN:
            start = i
            i += 1
            while i < n and lines[i].rstrip("\n").strip() != EXPORT_END:
                i += 1
            if i >= n:
                blocks.append(Block("EXPORT_UNCLOSED", start+1, n, lines[start:]))
                break
            end = i
            blocks.append(Block("EXPORT", start+1, end+1, lines[start:end+1]))
            i += 1
            continue

        if line.strip() == EVID_BEGIN:
            start = i
            i += 1
            while i < n and lines[i].rstrip("\n").strip() != EVID_END:
                i += 1
            if i >= n:
                blocks.append(Block("EVID_UNCLOSED", start+1, n, lines[start:]))
                break
            end = i
            blocks.append(Block("EVID", start+1, end+1, lines[start:end+1]))
            i += 1
            continue

        if line.strip() == SAVE_BEGIN:
            start = i
            i += 1
            while i < n and lines[i].rstrip("\n").strip() != SAVE_END:
                i += 1
            if i >= n:
                blocks.append(Block("SAVE_UNCLOSED", start+1, n, lines[start:]))
                break
            end = i
            blocks.append(Block("SAVE", start+1, end+1, lines[start:end+1]))
            i += 1
            continue

        i += 1

    return blocks


def lint(lines: List[str]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    # quick forbidden substring scan
    for idx, raw in enumerate(lines, start=1):
        s = raw.rstrip("\n")
        for bad in FORBIDDEN_SUBSTRINGS:
            if bad in s:
                errors.append(f"L{idx}: forbidden substring {bad!r} found")
                break

    blocks = find_blocks(lines)

    export_blocks = [b for b in blocks if b.kind.startswith("EXPORT")]
    evid_blocks   = [b for b in blocks if b.kind.startswith("EVID")]
    save_blocks   = [b for b in blocks if b.kind.startswith("SAVE")]

    if any(b.kind.endswith("UNCLOSED") for b in blocks):
        for b in blocks:
            if b.kind.endswith("UNCLOSED"):
                errors.append(f"{b.kind}: starts at L{b.start_line} but has no matching END")
        return errors, warnings

    # message-level sanity
    if export_blocks and (evid_blocks or save_blocks):
        errors.append("File mixes EXPORT_BLOCK with SIM_EVIDENCE and/or SAVE_SNAPSHOT. Thread-B will HALT.")
    if save_blocks and (export_blocks or evid_blocks):
        errors.append("File mixes SAVE_SNAPSHOT with EXPORT_BLOCK and/or SIM_EVIDENCE. Thread-B will HALT.")

    # if it's meant to be a single message, multiple EXPORT_BLOCKs are a problem
    if len(export_blocks) > 1:
        warnings.append(f"Found {len(export_blocks)} EXPORT_BLOCKs. Paste one per Thread-B message (tape file is OK).")

    # line-level schema-ish checks within export blocks
    for b in export_blocks:
        for j, raw in enumerate(b.lines, start=b.start_line):
            s = raw.rstrip("\n")
            if s.strip() in (EXPORT_BEGIN, EXPORT_END) or s.strip() == "":
                continue

            if COMMENT_LINE_RE.match(s):
                errors.append(f"L{j}: comment line found inside EXPORT_BLOCK (not allowed by schema)")

            if REQUIRES_MATH_TOKEN_RE.match(s):
                errors.append(f"L{j}: REQUIRES references MATH_TOKEN (should reference a MATH_DEF ID)")

            if not s.startswith(ALLOWED_LINE_PREFIXES):
                # Some kernels accept extra headers, but most don't. Flag as warning first.
                warnings.append(f"L{j}: unrecognized line prefix (may HALT): {s[:40]!r}")

    # line-level checks within evidence packs
    for b in evid_blocks:
        for j, raw in enumerate(b.lines, start=b.start_line):
            s = raw.rstrip("\n")
            if s.strip() in (EVID_BEGIN, EVID_END) or s.strip() == "":
                continue
            if s.lstrip().startswith("#"):
                errors.append(f"L{j}: comment line found inside SIM_EVIDENCE (not allowed)")
            if s.startswith(("BEGIN", "END")) and s.strip() not in (EVID_BEGIN, EVID_END):
                warnings.append(f"L{j}: nested container marker inside SIM_EVIDENCE? {s!r}")

    # if file contains no recognized containers, it is probably stray prose
    if not blocks:
        errors.append("No BEGIN/END containers found. Thread-B will treat this as contamination.")

    return errors, warnings


def split_tape(lines: List[str], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    blocks = find_blocks(lines)

    count = 0
    for b in blocks:
        if b.kind != "EXPORT":
            continue
        count += 1
        p = out_dir / f"export_block_{count:03d}.txt"
        p.write_text("".join(b.lines), encoding="utf-8")

    print(f"Wrote {count} export blocks to: {out_dir}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="text file to lint")
    ap.add_argument("--split", action="store_true", help="split EXPORT_BLOCK tape into separate files")
    ap.add_argument("out_dir", nargs="?", help="output directory for --split")
    args = ap.parse_args()

    if not args.path:
        ap.error("missing path")

    path = Path(args.path)
    if not path.exists():
        raise SystemExit(f"file not found: {path}")

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

    if args.split:
        if not args.out_dir:
            ap.error("--split requires out_dir")
        split_tape(lines, Path(args.out_dir))
        return

    errors, warnings = lint(lines)

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print("  -", w)

    if errors:
        print("\nERRORS:")
        for e in errors:
            print("  -", e)
        raise SystemExit(2)

    print("OK: no blocking issues found (still not a full schema validation).")


if __name__ == "__main__":
    main()
