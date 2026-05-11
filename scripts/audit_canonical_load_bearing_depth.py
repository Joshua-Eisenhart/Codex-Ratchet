#!/usr/bin/env python3
"""Audit canonical sims that declare no load-bearing tools.

This is intentionally separate from verify_load_bearing_has_capability_probe.py:
that verifier checks whether declared load-bearing tools have passing capability
receipts. This audit checks the complementary contract surface: canonical sims
should not have zero load-bearing tools.
"""

from __future__ import annotations

import argparse
import ast
import json
import runpy
import sys
from pathlib import Path


REPO = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")
PROBES_DIR = REPO / "system_v4" / "probes"
VERIFY_SCRIPT = REPO / "scripts" / "verify_load_bearing_has_capability_probe.py"


def module_literal(tree: ast.AST, name: str):
    vals = []
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                try:
                    vals.append(ast.literal_eval(node.value))
                except (ValueError, SyntaxError):
                    pass
    return vals[-1] if vals else None


def sim_paths(scope_files: list[str] | None) -> list[Path]:
    if scope_files:
        paths = []
        for item in scope_files:
            path = Path(item)
            if not path.is_absolute():
                path = REPO / path
            paths.append(path)
        return sorted(paths)
    return sorted(
        path for path in PROBES_DIR.glob("sim_*.py")
        if not path.name.endswith(" 2.py")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope-file", action="append", dest="scope_files")
    parser.add_argument("--fail-on-violations", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()

    verify = runpy.run_path(str(VERIFY_SCRIPT))
    extract_tool_integration_depth = verify["extract_tool_integration_depth"]

    rows = []
    parse_errors = []
    for path in sim_paths(args.scope_files):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError) as exc:
            parse_errors.append({"path": str(path.relative_to(REPO)), "error": str(exc)})
            continue
        classification = module_literal(tree, "CLASSIFICATION") or module_literal(tree, "classification")
        if classification != "canonical":
            continue
        depth = extract_tool_integration_depth(path) or {}
        load_bearing_tools = sorted(
            str(tool) for tool, level in depth.items()
            if level == "load_bearing"
        )
        if not load_bearing_tools:
            rows.append({
                "path": str(path.relative_to(REPO)),
                "classification": classification,
                "load_bearing_tools": [],
                "status": "canonical_zero_load_bearing",
            })

    report = {
        "schema": "canonical_load_bearing_depth_audit_v1",
        "scope": "explicit_files" if args.scope_files else "all_sim_sources",
        "checked_path_count": len(sim_paths(args.scope_files)),
        "parse_error_count": len(parse_errors),
        "canonical_zero_load_bearing_count": len(rows),
        "violations": rows,
        "parse_errors": parse_errors,
        "claim_boundary": (
            "This audit checks canonical/no-load-bearing source declarations only; "
            "it does not rerun sims or promote coupling, QIT, GStack, axis, or "
            "nonclassical claims."
        ),
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = REPO / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")

    if args.fail_on_violations and rows:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
