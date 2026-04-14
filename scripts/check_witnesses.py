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
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            if isinstance(node.target, ast.Name) and node.target.id == name:
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


def _literal_string_list(value: ast.AST, mod_consts: dict[str, str]) -> list[str]:
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return [value.value]
    if isinstance(value, ast.Name) and value.id in mod_consts:
        return [mod_consts[value.id]]
    if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        items: list[str] = []
        for elt in value.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                items.append(elt.value)
            elif isinstance(elt, ast.Name) and elt.id in mod_consts:
                items.append(mod_consts[elt.id])
        return items
    return []


def _extract_witness_sim_paths(cap_path: Path) -> list[str]:
    """Find declared witness sim paths across recent capability-probe schemas."""
    try:
        tree = ast.parse(cap_path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    mod_consts = _collect_module_str_constants(tree)
    witness_paths: list[str] = []

    def add_candidates(value: ast.AST) -> None:
        for candidate in _literal_string_list(value, mod_consts):
            if candidate not in witness_paths:
                witness_paths.append(candidate)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run_witness_replay":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Dict):
                    for k, v in zip(sub.keys, sub.values):
                        if not (isinstance(k, ast.Constant) and k.value == "sim"):
                            continue
                        add_candidates(v)
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if not isinstance(k, ast.Constant):
                    continue
                if k.value in {
                    "witness_file",
                    "witness_loadbearing_use",
                    "witness_use_cases",
                    "witness_load_bearing_uses",
                }:
                    add_candidates(v)
    return witness_paths


def main() -> int:
    cap_probes = sorted(PROBES_DIR.glob("sim_*_capability.py"))
    per_probe: list[dict] = []
    violations: list[dict] = []

    for cap in cap_probes:
        tool = _tool_name_from_capability(cap)
        witness_rel_paths = _extract_witness_sim_paths(cap)
        entry: dict = {
            "capability_probe": cap.name,
            "tool": tool,
            "witness_sims": witness_rel_paths,
            "status": "ok",
        }

        if not witness_rel_paths:
            entry["status"] = "no_witness_declared"
            violations.append(entry)
            per_probe.append(entry)
            continue

        witness_details: list[dict] = []
        accepted = False
        for witness_rel in witness_rel_paths:
            witness_path = (REPO / witness_rel).resolve()
            detail: dict = {
                "witness_sim": witness_rel,
                "resolved_path": str(witness_path),
            }
            if not witness_path.exists():
                detail["status"] = "witness_file_missing"
                witness_details.append(detail)
                continue

            try:
                tree = ast.parse(witness_path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError) as exc:
                detail["status"] = "witness_parse_error"
                detail["detail"] = str(exc)
                witness_details.append(detail)
                continue

            depth = _extract_dict_assign(tree, "TOOL_INTEGRATION_DEPTH")
            if depth is None:
                detail["status"] = "witness_no_tool_integration_depth"
                witness_details.append(detail)
                continue

            level = depth.get(tool)
            detail["declared_level"] = level
            if level == "load_bearing":
                detail["status"] = "ok"
                witness_details.append(detail)
                accepted = True
                break

            detail["status"] = "witness_not_load_bearing"
            witness_details.append(detail)

        entry["witness_details"] = witness_details
        if not accepted:
            entry["status"] = witness_details[-1]["status"]
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
