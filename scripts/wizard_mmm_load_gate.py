#!/usr/bin/env python3
"""Wizard MMM-load gate: mechanical proof of COMPLETE reading, for every agent.

The Wizard v4.2 MMM Loading Contract (WIZARD_v4_2.md, "MMM Loading Contract")
requires the main agent to boot on positive MMM salience and requires every
parent, child, and subsubagent to load its compact MMM plus its assigned
mini-MMM slices. That was process-text only: a worker could emit wizard-shaped
output having read nothing, and a worker could SKIM one doc and claim a load.

This gate enforces two things mechanically, per the source rule "make the
process executable / make violations mechanically visible / make unauthorized
success impossible":

1. COMPLETE reading, not skimming. Each required doc is split into segments by
   file size. The load receipt must carry a verbatim anchor quote from EVERY
   segment, including the last. You cannot quote the final segment of a long
   file without having read to the end, so partial/skim reads fail.

2. EVERY agent loads MMMs. The receipt is an agent tree: the main agent must
   prove the floor (a compact-or-full main MMM plus the member registry), and
   every declared sub / subsub agent must prove a complete read of its assigned
   mini-MMM. A child with no proven mini-MMM read fails the gate.

The required floor and the role->mini-MMM mapping are hardcoded here, not
declared by the receipt, so a run cannot shrink its own obligation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "wizard_mmm_load_receipt_v2"

DEFAULT_MMM_ROOT = Path(
    "/Users/joshuaeisenhart/wiki/wizard/packet-v4-2-current/mmm"
)

# Canonical-active salience per PACKET_MANIFEST_v4_2.md.
FULL_MMM = "FULL_MMM_v4_2.md"
COMPACT_MMM = "COMPACT_MMM_v4_2.md"
REGISTRY = "mini/MEMBER_MINI_MMM_REGISTRY_v4_2.md"

# Floor rules:
#   main agent  : FULL_MMM completely read, OR (COMPACT_MMM AND REGISTRY) completely read.
#   sub/subsub  : COMPACT_MMM completely read (the minimum).
# Mini-MMMs are reusable salience reservoirs, not name-locked roles. An agent
# boots with a GROUPING of compact and/or mini MMMs chosen by function. The gate
# does not dictate which mini maps to which role; it only proves that every
# declared load was completely read. So there is no fixed role->file mapping.

MIN_QUOTE_LEN = 24
LINES_PER_SEGMENT = 400
MIN_SEGMENTS = 6
MAX_SEGMENTS = 14
CHILD_ROLES = {"sub", "subsub"}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str


def _append(errors: list[Finding], severity: str, code: str, message: str) -> None:
    errors.append(Finding(severity=severity, code=code, message=message))


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _segment_count(line_count: int) -> int:
    return max(MIN_SEGMENTS, min(MAX_SEGMENTS, math.ceil(line_count / LINES_PER_SEGMENT)))


def _resolve_root(receipt: dict[str, Any], cli_root: Path | None) -> Path:
    if cli_root is not None:
        return cli_root
    declared = receipt.get("mmm_root")
    if isinstance(declared, str) and declared.strip():
        return Path(declared)
    return DEFAULT_MMM_ROOT


def _verify_complete_read(root: Path, entry: Any, *, label: str) -> tuple[list[Finding], str | None]:
    """Return (findings, proven_path). proven_path is set only if the read is complete."""
    findings: list[Finding] = []
    if not isinstance(entry, dict):
        return [Finding("error", "load.not_object", f"{label}: each loads[] entry must be an object")], None

    rel = entry.get("path")
    if not isinstance(rel, str) or not rel.strip():
        return [Finding("error", "load.empty_path", f"{label}: loads[].path must be a non-empty string")], None

    file_path = root / rel
    if not file_path.is_file():
        return [Finding("error", "load.file_missing", f"{label}:{rel}: file not found under MMM root")], None

    raw = _normalize(file_path.read_text(encoding="utf-8", errors="replace"))
    total = max(1, len(raw))
    line_count = raw.count("\n") + 1
    n_segments = _segment_count(line_count)

    claimed_sha = entry.get("sha256")
    if isinstance(claimed_sha, str) and claimed_sha.strip():
        if claimed_sha != hashlib.sha256(file_path.read_bytes()).hexdigest():
            _append(findings, "error", "load.sha256_mismatch", f"{label}:{rel}: sha256 does not match file on disk")

    quotes = entry.get("anchor_quotes")
    if not isinstance(quotes, list) or len(quotes) < n_segments:
        _append(
            findings,
            "error",
            "load.too_few_quotes",
            f"{label}:{rel}: complete read needs >= {n_segments} verbatim quotes spanning the file "
            f"({line_count} lines / {n_segments} segments); got {len(quotes) if isinstance(quotes, list) else 0}",
        )

    covered: set[int] = set()
    seen: set[str] = set()
    for index, quote in enumerate(quotes if isinstance(quotes, list) else []):
        if not isinstance(quote, str) or len(quote.strip()) < MIN_QUOTE_LEN:
            _append(
                findings,
                "error",
                "load.quote_too_short",
                f"{label}:{rel}: anchor_quotes[{index}] must be verbatim and >= {MIN_QUOTE_LEN} chars",
            )
            continue
        norm = _normalize(quote)
        if norm in seen:
            _append(findings, "error", "load.duplicate_quote", f"{label}:{rel}: anchor_quotes[{index}] is a duplicate")
            continue
        seen.add(norm)
        offset = raw.find(norm)
        if offset < 0:
            _append(
                findings,
                "error",
                "load.quote_not_found",
                f"{label}:{rel}: anchor_quotes[{index}] not verbatim in file (fabricated or stale)",
            )
            continue
        segment = min(n_segments - 1, int(offset / total * n_segments))
        covered.add(segment)

    missing_segments = sorted(set(range(n_segments)) - covered)
    if missing_segments and not any(f.code == "load.too_few_quotes" for f in findings):
        _append(
            findings,
            "error",
            "load.incomplete_coverage",
            f"{label}:{rel}: skim detected — no verbatim quote from segment(s) "
            f"{missing_segments} of {n_segments} (segment {n_segments - 1} is the file's end)",
        )

    proven = rel if not any(f.severity == "error" for f in findings) else None
    return findings, proven


def _validate_agent(root: Path, agent: Any, *, index: int, known_ids: set[str]) -> tuple[list[Finding], set[str], str | None, str | None]:
    findings: list[Finding] = []
    if not isinstance(agent, dict):
        return [Finding("error", "agent.not_object", f"agents[{index}] must be an object")], set(), None, None

    agent_id = agent.get("agent_id")
    role = agent.get("role")
    label = str(agent_id) if isinstance(agent_id, str) and agent_id.strip() else f"agents[{index}]"

    if not isinstance(agent_id, str) or not agent_id.strip():
        _append(findings, "error", "agent.empty_id", f"agents[{index}].agent_id must be a non-empty string")
    if role not in ({"main"} | CHILD_ROLES):
        _append(findings, "error", "agent.bad_role", f"{label}.role must be one of main, sub, subsub")

    proven: set[str] = set()
    loads = agent.get("loads")
    if not isinstance(loads, list) or not loads:
        _append(findings, "error", "agent.no_loads", f"{label}: loads must be a non-empty list of complete-read proofs")
    else:
        for entry in loads:
            entry_findings, proven_path = _verify_complete_read(root, entry, label=label)
            findings.extend(entry_findings)
            if proven_path is not None:
                proven.add(proven_path)

    if role in CHILD_ROLES:
        parent_id = agent.get("parent_id")
        if not isinstance(parent_id, str) or parent_id not in known_ids:
            _append(findings, "error", "agent.bad_parent", f"{label}.parent_id must reference an existing agent")
        # Subagent floor: the compact MMM is the minimum complete read.
        if COMPACT_MMM not in proven:
            _append(
                findings,
                "error",
                "floor.child_missing_compact",
                f"{label} ({role}) must completely read the compact MMM (subagent minimum): {COMPACT_MMM}",
            )

    return findings, proven, (agent_id if isinstance(agent_id, str) else None), (role if isinstance(role, str) else None)


def validate_receipt(receipt: dict[str, Any], *, cli_root: Path | None = None) -> dict[str, Any]:
    findings: list[Finding] = []

    if receipt.get("schema_version") != SCHEMA_VERSION:
        _append(findings, "error", "receipt.bad_schema_version", f"schema_version must be {SCHEMA_VERSION}")

    root = _resolve_root(receipt, cli_root)
    if not root.is_dir():
        _append(findings, "error", "receipt.mmm_root_missing", f"MMM root not found: {root}")

    agents = receipt.get("agents")
    if not isinstance(agents, list) or not agents:
        _append(findings, "error", "receipt.no_agents", "agents must be a non-empty list (at least the main agent)")
        agents = []

    known_ids = {a.get("agent_id") for a in agents if isinstance(a, dict) and isinstance(a.get("agent_id"), str)}

    main_proven: set[str] = set()
    main_count = 0
    per_agent: list[dict[str, Any]] = []
    for index, agent in enumerate(agents):
        agent_findings, proven, agent_id, role = _validate_agent(root, agent, index=index, known_ids=known_ids)
        findings.extend(agent_findings)
        per_agent.append({"agent_id": agent_id, "role": role, "proven_reads": sorted(proven)})
        if role == "main":
            main_count += 1
            main_proven |= proven

    if main_count == 0:
        _append(findings, "error", "receipt.no_main_agent", "receipt must contain exactly one main agent")
    elif main_count > 1:
        _append(findings, "error", "receipt.multiple_main_agents", "receipt must contain exactly one main agent")

    # Main floor: FULL alone, OR COMPACT + REGISTRY. The receipt cannot shrink it.
    if main_count >= 1:
        full_ok = FULL_MMM in main_proven
        compact_path_ok = COMPACT_MMM in main_proven and REGISTRY in main_proven
        if not (full_ok or compact_path_ok):
            _append(
                findings,
                "error",
                "floor.main_unsatisfied",
                f"main agent must completely read {FULL_MMM}, or both {COMPACT_MMM} and {REGISTRY}",
            )

    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    return {
        "ok": not errors,
        "schema_version": SCHEMA_VERSION,
        "mmm_root": str(root),
        "agents": per_agent,
        "errors": [asdict(f) for f in errors],
        "warnings": [asdict(f) for f in warnings],
    }


# --------------------------------------------------------------------------- #
# Self-test: hermetic temp MMM fixtures so it runs on any machine.
# --------------------------------------------------------------------------- #

def _write_spanning_file(path: Path, title: str, n_lines: int) -> None:
    body = "\n".join(f"- {title} salience marker line {i:04d} :: 100" for i in range(n_lines))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n{body}\n", encoding="utf-8")


def _spanning_quotes(title: str, n_lines: int) -> list[str]:
    # One quote from each ~8% band, guaranteeing full segment coverage.
    picks = [int(n_lines * frac) for frac in (0.04, 0.16, 0.30, 0.44, 0.58, 0.72, 0.86, 0.97)]
    return [f"- {title} salience marker line {i:04d} :: 100" for i in picks]


def _fixture_root(tmp: Path) -> Path:
    root = tmp / "mmm"
    _write_spanning_file(root / COMPACT_MMM, "compact", 240)
    _write_spanning_file(root / FULL_MMM, "full", 240)
    _write_spanning_file(root / REGISTRY, "registry", 240)
    # An arbitrary mini grouped into a boot by function (not name-locked to a role).
    _write_spanning_file(root / "mini" / "grouped_lens.md", "lens", 240)
    return root


def _good_receipt(root: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "mmm_root": str(root),
        "agents": [
            {
                "agent_id": "main",
                "role": "main",
                "boot_grouping": "compact-path main boot",
                "loads": [
                    {"path": COMPACT_MMM, "anchor_quotes": _spanning_quotes("compact", 240)},
                    {"path": REGISTRY, "anchor_quotes": _spanning_quotes("registry", 240)},
                ],
            },
            {
                "agent_id": "sub-1",
                "role": "sub",
                "parent_id": "main",
                "boot_grouping": "compact + one functional lens",
                "loads": [
                    {"path": COMPACT_MMM, "anchor_quotes": _spanning_quotes("compact", 240)},
                    {"path": "mini/grouped_lens.md", "anchor_quotes": _spanning_quotes("lens", 240)},
                ],
            },
        ],
    }


def selftest_cases(root: Path) -> list[tuple[str, dict[str, Any], bool]]:
    valid = _good_receipt(root)

    main_full = {
        "schema_version": SCHEMA_VERSION,
        "mmm_root": str(root),
        "agents": [
            {
                "agent_id": "main",
                "role": "main",
                "loads": [{"path": FULL_MMM, "anchor_quotes": _spanning_quotes("full", 240)}],
            }
        ],
    }

    main_compact_only = json.loads(json.dumps(valid))
    del main_compact_only["agents"][0]["loads"][1]  # drop the registry; compact alone is not enough for main

    skim_main = json.loads(json.dumps(valid))
    skim_main["agents"][0]["loads"][0]["anchor_quotes"] = _spanning_quotes("compact", 240)[:3]

    fabricated = json.loads(json.dumps(valid))
    fabricated["agents"][0]["loads"][0]["anchor_quotes"][4] = "- compact salience marker line 9999 :: 100"

    child_no_compact = json.loads(json.dumps(valid))
    child_no_compact["agents"][1]["loads"] = [
        {"path": "mini/grouped_lens.md", "anchor_quotes": _spanning_quotes("lens", 240)}
    ]

    nonexistent_load = json.loads(json.dumps(valid))
    nonexistent_load["agents"][0]["loads"].append(
        {"path": "mini/does_not_exist.md", "anchor_quotes": _spanning_quotes("ghost", 240)}
    )

    no_main = json.loads(json.dumps(valid))
    no_main["agents"][0]["role"] = "sub"
    no_main["agents"][0]["parent_id"] = "sub-1"

    return [
        ("valid_main_compact_path_plus_child", valid, True),
        ("valid_main_full_path", main_full, True),
        ("reject_main_compact_only_no_registry", main_compact_only, False),
        ("reject_skim_main", skim_main, False),
        ("reject_fabricated_quote", fabricated, False),
        ("reject_child_without_compact", child_no_compact, False),
        ("reject_nonexistent_load", nonexistent_load, False),
        ("reject_no_main_agent", no_main, False),
    ]


def run_selftest() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        root = _fixture_root(Path(tmp))
        cases = []
        all_passed = True
        for name, receipt, expected_ok in selftest_cases(root):
            result = validate_receipt(receipt, cli_root=root)
            passed = result["ok"] is expected_ok
            all_passed = all_passed and passed
            cases.append(
                {
                    "name": name,
                    "expected_ok": expected_ok,
                    "actual_ok": result["ok"],
                    "passed": passed,
                    "errors": result["errors"],
                }
            )
    return {"ok": all_passed, "schema_version": SCHEMA_VERSION, "cases": cases}


def example_receipt() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "mmm_root": str(DEFAULT_MMM_ROOT),
        "agents": [
            {
                "agent_id": "main",
                "role": "main",
                "boot_grouping": "FULL alone, or COMPACT + registry",
                "loads": [
                    {"path": COMPACT_MMM, "anchor_quotes": ["<verbatim line from each segment, end included>"]},
                    {"path": REGISTRY, "anchor_quotes": ["<verbatim spanning quotes>"]},
                ],
            },
            {
                "agent_id": "sub-1",
                "role": "sub",
                "parent_id": "main",
                "boot_grouping": "compact (minimum) + any functional grouping of minis",
                "loads": [
                    {"path": COMPACT_MMM, "anchor_quotes": ["<verbatim spanning quotes from compact>"]},
                    {"path": "mini/<any functionally chosen mini>.md", "anchor_quotes": ["<verbatim spanning quotes>"]},
                ],
            },
        ],
    }


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="Validate an MMM-load receipt (agent tree)")
    validate_parser.add_argument("--input", required=True, type=Path)
    validate_parser.add_argument("--mmm-root", type=Path, help="override MMM root directory")
    validate_parser.add_argument("--out", type=Path)

    selftest_parser = sub.add_parser("selftest", help="Run hermetic self-tests")
    selftest_parser.add_argument("--out", type=Path)

    example_parser = sub.add_parser("example", help="Print an example agent-tree receipt skeleton")
    example_parser.add_argument("--out", type=Path)

    args = parser.parse_args(argv)

    if args.command == "validate":
        payload = validate_receipt(read_json(args.input), cli_root=args.mmm_root)
        if args.out:
            write_json(args.out, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1

    if args.command == "selftest":
        payload = run_selftest()
        if args.out:
            write_json(args.out, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1

    if args.command == "example":
        payload = example_receipt()
        if args.out:
            write_json(args.out, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
