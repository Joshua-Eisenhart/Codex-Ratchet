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


REPO = Path(__file__).resolve().parents[1]
PROBES_DIR = REPO / "system_v4" / "probes"
RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"
VERIFY_SCRIPT = REPO / "scripts" / "verify_load_bearing_has_capability_probe.py"


def module_literal(tree: ast.AST, name: str):
    vals = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    try:
                        vals.append(ast.literal_eval(node.value))
                    except (ValueError, SyntaxError):
                        pass
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name and node.value is not None:
                try:
                    vals.append(ast.literal_eval(node.value))
                except (ValueError, SyntaxError):
                    pass
    return vals[-1] if vals else None


def literal_key(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Str):
        return node.s
    return None


def manifest_used_tools(tree: ast.AST) -> list[str]:
    """Fallback for dynamic depth maps derived from TOOL_MANIFEST.

    Several older canonical sims define ``TOOL_INTEGRATION_DEPTH`` with a
    comprehension such as ``tool: ("load_bearing" if entry["used"] else None)``.
    The parse-only verifier cannot evaluate that expression, but the literal
    manifest still records whether any tool is used. For this audit's narrow
    purpose, any used tool is enough to prove the row is not zero-load-bearing.
    """

    used_tools = []
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id not in {"TOOL_MANIFEST", "tool_manifest"}:
                continue
            if not isinstance(node.value, ast.Dict):
                continue
            for key_node, value_node in zip(node.value.keys, node.value.values):
                tool = literal_key(key_node)
                if tool is None or not isinstance(value_node, ast.Dict):
                    continue
                used = None
                for spec_key, spec_value in zip(value_node.keys, value_node.values):
                    if literal_key(spec_key) == "used":
                        try:
                            used = ast.literal_eval(spec_value)
                        except (ValueError, SyntaxError):
                            used = None
                        break
                if used is True:
                    used_tools.append(str(tool))
    return sorted(used_tools)


def subscript_load_bearing_tools(tree: ast.AST) -> list[str]:
    """Find ``TOOL_INTEGRATION_DEPTH["tool"] = "load_bearing"`` assignments.

    Older sims often set tool depth inside top-level try blocks or inside
    functions after a tool succeeds. Those assignments are still parse-visible
    contract evidence even when they are not in the initial literal dict.
    """

    depth_aliases = {"TOOL_INTEGRATION_DEPTH", "tool_integration_depth"}
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if isinstance(node.value, ast.Name) and node.value.id in depth_aliases:
                depth_aliases.add(target.id)

    tools = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Subscript):
                continue
            if not isinstance(target.value, ast.Name):
                continue
            if target.value.id not in depth_aliases:
                continue
            tool = literal_key(target.slice)
            if tool is None:
                continue
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                continue
            if value == "load_bearing":
                tools.append(str(tool))
    return sorted(set(tools))


def result_load_bearing_tools(path: Path) -> list[str]:
    """Read existing result receipts when source declarations are dynamic."""
    stems = [path.stem]
    if path.stem.startswith("sim_"):
        stems.append(path.stem[4:])
    candidates = [RESULTS_DIR / f"{stem}_results.json" for stem in stems]
    for result_path in candidates:
        if not result_path.exists():
            continue
        try:
            data = json.loads(result_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        depth = (
            data.get("tool_integration_depth")
            or data.get("TOOL_INTEGRATION_DEPTH")
            or data.get("summary", {}).get("tool_integration_depth")
        )
        if not isinstance(depth, dict):
            continue
        tools = sorted(str(tool) for tool, level in depth.items() if level == "load_bearing")
        if tools:
            return tools
    return []


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
        depth = extract_tool_integration_depth(path) or module_literal(tree, "TOOL_INTEGRATION_DEPTH") or {}
        load_bearing_tools = sorted(
            str(tool) for tool, level in depth.items()
            if level == "load_bearing"
        )
        if not load_bearing_tools:
            load_bearing_tools = subscript_load_bearing_tools(tree)
        if not load_bearing_tools:
            load_bearing_tools = result_load_bearing_tools(path)
        fallback_used_tools = []
        if not load_bearing_tools:
            fallback_used_tools = manifest_used_tools(tree)
            load_bearing_tools = fallback_used_tools
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
