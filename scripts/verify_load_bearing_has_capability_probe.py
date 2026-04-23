#!/usr/bin/env python3
"""Audit: every tool declared load_bearing must have a passing capability probe.

Rule (owner+Hermes 2026-04-13):
  A sim may set TOOL_INTEGRATION_DEPTH[tool] = "load_bearing" only if
    - sim_<canonical_tool>_capability.py exists in probes/
    - a2_state/sim_results/<canonical_tool>_capability_results.json exists
      and has summary.all_pass == True
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")
PROBES_DIR = REPO / "system_v4" / "probes"
RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"
REPORT_PATH = RESULTS_DIR / "load_bearing_capability_audit.json"

# Canonical probe-name normalization.
ALIASES = {
    "pytorch": "pytorch",
    "torch": "pytorch",
    "pyg": "pyg",
    "torch_geometric": "pyg",
    "torch-geometric": "pyg",
    "z3": "z3",
    "z3-solver": "z3",
    "z3_solver": "z3",
    "cvc5": "cvc5",
    "sympy": "sympy",
    "clifford": "clifford",
    "geomstats": "geomstats",
    "e3nn": "e3nn",
    "xgi": "xgi",
    "toponetx": "toponetx",
    "gudhi": "gudhi",
    "rustworkx": "rustworkx",
    "hypothesis": "hypothesis",
    "optuna": "optuna",
    "evotorch": "evotorch",
    "datasketch": "datasketch",
    "pymoo": "pymoo",
    "ribs": "ribs",
    "deap": "deap",
    "networkx": "networkx",
    "igraph": "igraph",
    "scipy": "scipy",
    "sklearn": "sklearn",
    "hdbscan": "hdbscan",
    "umap": "umap",
    "pynndescent": "pynndescent",
    "cma": "cma",
}


def canonical(tool: str) -> str:
    key = tool.strip().lower().replace("-", "_")
    return ALIASES.get(key, key)


def _is_ignored_sim_path(path: Path) -> bool:
    return path.name.endswith(" 2.py")


def _find_module_literal(tree: ast.AST, name: str):
    """Return the literal Python value of a top-level `name = <literal>` assign, or None.

    Also resolves single-generator dict-comprehensions whose iter is itself a
    literal (or a Name referencing another sibling literal) — this is enough to
    cover the `TOOL_MANIFEST = {k: {...} for k in [<list>]}` pattern. In that
    case we only need the *keys*, so we return a dict mapping keys to None.
    """
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    try:
                        return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        pass
                    if isinstance(node.value, ast.DictComp) and len(node.value.generators) == 1:
                        gen = node.value.generators[0]
                        if gen.ifs or gen.is_async:
                            return None
                        if not isinstance(gen.target, ast.Name):
                            return None
                        iter_node = gen.iter
                        iterable = None
                        try:
                            iterable = ast.literal_eval(iter_node)
                        except (ValueError, SyntaxError):
                            if isinstance(iter_node, ast.Name):
                                iterable = _find_module_literal(tree, iter_node.id)
                        if isinstance(iterable, dict):
                            keys = list(iterable.keys())
                        elif isinstance(iterable, (list, tuple, set)):
                            keys = list(iterable)
                        else:
                            return None
                        if isinstance(node.value.key, ast.Name) and node.value.key.id == gen.target.id:
                            return {k: None for k in keys}
                    return None
    return None


def _eval_dictcomp_from_manifest(node: ast.DictComp, tree: ast.AST) -> dict | None:
    """Handle `{k: <expr> for k in TOOL_MANIFEST}` — single generator over a sibling literal.

    Returns a dict mapping manifest keys to the comprehension's value expression
    evaluated as a literal if possible, else None. Returns None if the pattern
    doesn't match or the iterator can't be resolved.
    """
    if len(node.generators) != 1:
        return None
    gen = node.generators[0]
    if gen.ifs or gen.is_async:
        return None
    if not isinstance(gen.target, ast.Name):
        return None
    loop_var = gen.target.id
    if not isinstance(gen.iter, ast.Name):
        return None
    manifest = _find_module_literal(tree, gen.iter.id)
    if manifest is None:
        return None
    # Keys are the iterated elements; for a dict iteration this is dict keys.
    if isinstance(manifest, dict):
        keys = list(manifest.keys())
    elif isinstance(manifest, (list, tuple, set)):
        keys = list(manifest)
    else:
        return None

    # Only accept a key expression that is just the loop variable (common case).
    if not (isinstance(node.key, ast.Name) and node.key.id == loop_var):
        return None

    # Try to evaluate the value as a literal independent of the loop var.
    try:
        value = ast.literal_eval(node.value)
    except (ValueError, SyntaxError):
        value = None
    return {k: value for k in keys}


def extract_tool_integration_depth(path: Path) -> dict | None:
    """Parse-only extraction of TOOL_INTEGRATION_DEPTH.

    Primary: `ast.literal_eval` of a dict literal.
    Fallback: dict-comprehension `{k: <literal> for k in TOOL_MANIFEST}` where
    `TOOL_MANIFEST` is a sibling literal dict/list/tuple/set at module scope.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "TOOL_INTEGRATION_DEPTH":
                    try:
                        val = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        val = None
                    if isinstance(val, dict):
                        return val
                    if isinstance(node.value, ast.DictComp):
                        comp_val = _eval_dictcomp_from_manifest(node.value, tree)
                        if isinstance(comp_val, dict):
                            return comp_val
                    return None
    return None


def probe_status(tool: str) -> str | None:
    """Return None if OK, else violation status string."""
    candidates = [
        (
            PROBES_DIR / f"sim_{tool}_capability.py",
            RESULTS_DIR / f"{tool}_capability_results.json",
        ),
        (
            PROBES_DIR / f"sim_capability_{tool}_isolated.py",
            RESULTS_DIR / f"sim_capability_{tool}_isolated_results.json",
        ),
    ]

    existing_probe = False
    saw_result = False
    for probe, result in candidates:
        if not probe.exists():
            continue
        existing_probe = True
        if not result.exists():
            continue
        saw_result = True
        try:
            data = json.loads(result.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        summary = data.get("summary") or {}
        if (
            summary.get("all_pass") is True
            or data.get("overall_pass") is True
            or data.get("passed") is True
        ):
            return None

    if existing_probe and not saw_result:
        return "probe_stale"
    if existing_probe:
        return "probe_failing"
    return "missing_probe"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-json", action="store_true",
                    help=f"Write JSON summary to {REPORT_PATH}")
    ap.add_argument("--sim", type=str, default=None,
                    help="Gate a single sim path; print JSON report; exit 0 if all "
                         "load-bearing tools have passing capability probes.")
    args = ap.parse_args()

    if args.sim is not None:
        sim_path = Path(args.sim)
        if not sim_path.is_absolute():
            sim_path = (REPO / sim_path).resolve()
        report: dict = {
            "sim_file": sim_path.name,
            "sim_path": str(sim_path),
            "load_bearing_tools": [],
            "violations": [],
        }
        if not sim_path.exists():
            report["error"] = "sim_not_found"
            print(json.dumps(report, indent=2))
            return 1
        depth = extract_tool_integration_depth(sim_path)
        if depth is None:
            report["error"] = "no_tool_integration_depth"
            print(json.dumps(report, indent=2))
            return 1
        for tool, level in depth.items():
            if not isinstance(level, str) or level != "load_bearing":
                continue
            canon = canonical(str(tool))
            entry = {"tool_declared": str(tool), "tool_canonical": canon}
            report["load_bearing_tools"].append(entry)
            # Self-probe: a capability sim is load-bearing on its own tool.
            if sim_path.name in {
                f"sim_{canon}_capability.py",
                f"sim_capability_{canon}_isolated.py",
            }:
                entry["status"] = "self_probe_ok"
                continue
            status = probe_status(canon)
            if status is None:
                entry["status"] = "ok"
            else:
                entry["status"] = status
                report["violations"].append({
                    "sim_file": sim_path.name,
                    "tool_declared": str(tool),
                    "tool_canonical": canon,
                    "status": status,
                })
        print(json.dumps(report, indent=2))
        return 1 if report["violations"] else 0

    sims = sorted(
        p for p in PROBES_DIR.glob("sim_*.py")
        if not _is_ignored_sim_path(p)
        if "_archive_lane_c" not in p.parts
    )

    violations: list[dict] = []
    audited = 0
    for sim in sims:
        depth = extract_tool_integration_depth(sim)
        if not depth:
            continue
        audited += 1
        for tool, level in depth.items():
            if not isinstance(level, str) or level != "load_bearing":
                continue
            canon = canonical(str(tool))
            # Don't audit a capability probe against itself.
            if sim.name == f"sim_{canon}_capability.py":
                continue
            status = probe_status(canon)
            if status is not None:
                violations.append({
                    "sim_file": sim.name,
                    "tool_declared": str(tool),
                    "tool_canonical": canon,
                    "status": status,
                })

    print(f"Audited {audited} sims with TOOL_INTEGRATION_DEPTH, "
          f"found {len(violations)} violations.")
    if violations:
        w_sim = max(len(v["sim_file"]) for v in violations)
        w_tool = max(len(v["tool_canonical"]) for v in violations)
        header = f"{'sim_file'.ljust(w_sim)}  {'tool'.ljust(w_tool)}  status"
        print(header)
        print("-" * len(header))
        for v in violations:
            print(f"{v['sim_file'].ljust(w_sim)}  "
                  f"{v['tool_canonical'].ljust(w_tool)}  {v['status']}")

    if args.report_json:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps({
            "audited": audited,
            "violation_count": len(violations),
            "violations": violations,
        }, indent=2))
        print(f"Wrote report: {REPORT_PATH}")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
