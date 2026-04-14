#!/usr/bin/env python3
"""check_witnesses.py -- guard: capability probes must witness a real load-bearing sim.

For every system_v4/probes/sim_*_capability.py:
  1. Extract the witness sim path from run_witness_replay() (the "sim" key string).
  2. Verify that file exists.
  3. Verify the witness sim declares the capability tool as "load_bearing" in its
     TOOL_INTEGRATION_DEPTH.

Exit 1 with a JSON report if any capability probe has a missing or non-load-bearing
witness. Intended to be usable as a pre-commit hook. No external dependencies.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROBES_DIR = REPO / "system_v4" / "probes"


def _tool_name_from_capability(path: Path) -> str:
    # sim_<tool>_capability.py  ->  <tool>
    stem = path.stem  # sim_z3_capability
    assert stem.startswith("sim_") and stem.endswith("_capability")
    return stem[len("sim_"):-len("_capability")]


def _extract_dict_assign(tree: ast.AST, name: str) -> dict | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    try:
                        val = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return None
                    if isinstance(val, dict):
                        return val
    return None


def _collect_module_str_constants(tree: ast.AST) -> dict[str, str]:
    """Collect module-level `NAME = "..."` string constant assignments."""
    consts: dict[str, str] = {}
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    try:
                        val = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        continue
                    if isinstance(val, str):
                        consts[t.id] = val
    return consts


def _extract_witness_sim_path(cap_path: Path) -> str | None:
    """Find the witness sim path referenced inside run_witness_replay().

    Accepts either:
      - a literal string at the 'sim' key, or
      - a Name reference that resolves to a module-level string constant.
    """
    try:
        tree = ast.parse(cap_path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None
    mod_consts = _collect_module_str_constants(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run_witness_replay":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Dict):
                    for k, v in zip(sub.keys, sub.values):
                        if not (isinstance(k, ast.Constant) and k.value == "sim"):
                            continue
                        if isinstance(v, ast.Constant) and isinstance(v.value, str):
                            return v.value
                        if isinstance(v, ast.Name) and v.id in mod_consts:
                            return mod_consts[v.id]
    return None


def main() -> int:
    cap_probes = sorted(PROBES_DIR.glob("sim_*_capability.py"))
    per_probe: list[dict] = []
    violations: list[dict] = []

    for cap in cap_probes:
        tool = _tool_name_from_capability(cap)
        witness_rel = _extract_witness_sim_path(cap)
        entry: dict = {
            "capability_probe": cap.name,
            "tool": tool,
            "witness_sim": witness_rel,
            "status": "ok",
        }

        if witness_rel is None:
            entry["status"] = "no_witness_declared"
            violations.append(entry)
            per_probe.append(entry)
            continue

        witness_path = (REPO / witness_rel).resolve()
        if not witness_path.exists():
            entry["status"] = "witness_file_missing"
            entry["resolved_path"] = str(witness_path)
            violations.append(entry)
            per_probe.append(entry)
            continue

        try:
            tree = ast.parse(witness_path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError) as exc:
            entry["status"] = "witness_parse_error"
            entry["detail"] = str(exc)
            violations.append(entry)
            per_probe.append(entry)
            continue

        depth = _extract_dict_assign(tree, "TOOL_INTEGRATION_DEPTH")
        if depth is None:
            entry["status"] = "witness_no_tool_integration_depth"
            violations.append(entry)
            per_probe.append(entry)
            continue

        level = depth.get(tool)
        entry["declared_level"] = level
        if level != "load_bearing":
            entry["status"] = "witness_not_load_bearing"
            violations.append(entry)
            per_probe.append(entry)
            continue

        per_probe.append(entry)

    report = {
        "checked": len(cap_probes),
        "violation_count": len(violations),
        "probes": per_probe,
        "violations": violations,
    }
    print(json.dumps(report, indent=2))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
