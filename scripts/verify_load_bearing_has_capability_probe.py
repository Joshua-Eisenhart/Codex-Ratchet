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
}


def canonical(tool: str) -> str:
    key = tool.strip().lower().replace("-", "_")
    return ALIASES.get(key, key)


def extract_tool_integration_depth(path: Path) -> dict | None:
    """Parse-only extraction of TOOL_INTEGRATION_DEPTH dict literal."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "TOOL_INTEGRATION_DEPTH":
                    try:
                        val = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return None
                    if isinstance(val, dict):
                        return val
    return None


def probe_status(tool: str) -> str | None:
    """Return None if OK, else violation status string."""
    probe = PROBES_DIR / f"sim_{tool}_capability.py"
    result = RESULTS_DIR / f"{tool}_capability_results.json"
    if not probe.exists():
        return "missing_probe"
    if not result.exists():
        return "probe_stale"
    try:
        data = json.loads(result.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "probe_stale"
    summary = data.get("summary") or {}
    if summary.get("all_pass") is True:
        return None
    return "probe_failing"


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
            if sim_path.name == f"sim_{canon}_capability.py":
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
