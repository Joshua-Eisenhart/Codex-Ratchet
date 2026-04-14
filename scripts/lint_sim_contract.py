#!/usr/bin/env python3
"""lint_sim_contract.py -- Static contract linter for system_v4/probes/sim_*.py.

Checks, by AST parse only (no import side-effects):
  C1: module-level `classification` in {"classical_baseline","canonical"}
  C2: module-level `TOOL_MANIFEST` dict with non-empty `reason` per tool
  C3: module-level `TOOL_INTEGRATION_DEPTH` dict present, values in allowed set
  C4: if classification == "classical_baseline", non-empty `divergence_log`
  C5: if any tool in TOOL_INTEGRATION_DEPTH == "load_bearing",
      `sim_<canonical>_capability.py` exists AND
      a2_state/sim_results/<canonical>_capability_results.json has summary.all_pass == True
      (self-probe exception: a capability probe is trivially its own evidence)

Emits a JSON report to stdout with:
  - checked
  - violations_by_type: counts per rule
  - violations: flat list (each: {sim, rule, detail})
  - top_offenders: up to 10 sims with the most distinct rule violations

Exit 1 if any violation; 0 otherwise.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROBES_DIR = REPO / "system_v4" / "probes"
RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"

VALID_CLASSIFICATIONS = {"classical_baseline", "canonical"}
VALID_DEPTHS = {"load_bearing", "supportive", "decorative", None}

ALIASES = {
    "pytorch": "pytorch", "torch": "pytorch",
    "pyg": "pyg", "torch_geometric": "pyg", "torch-geometric": "pyg",
    "z3": "z3", "z3-solver": "z3", "z3_solver": "z3",
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
    return ALIASES.get(tool.strip().lower().replace("-", "_"),
                       tool.strip().lower().replace("-", "_"))


def _module_level_assignments(tree: ast.Module) -> dict:
    """Collect literal-evaluable module-level assignments by name."""
    out: dict = {}
    for node in tree.body:
        targets = []
        value = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        else:
            continue
        for t in targets:
            if isinstance(t, ast.Name):
                try:
                    out[t.id] = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    # Re-attempt for dict-of-dicts whose inner strings are literals:
                    # literal_eval handles those. A failure means non-literal; skip.
                    pass
    return out


def _capability_ok(tool_canon: str) -> tuple[bool, str]:
    probe = PROBES_DIR / f"sim_{tool_canon}_capability.py"
    result = RESULTS_DIR / f"{tool_canon}_capability_results.json"
    if not probe.exists():
        return False, "missing_probe"
    if not result.exists():
        return False, "probe_stale"
    try:
        data = json.loads(result.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False, "probe_stale"
    if (data.get("summary") or {}).get("all_pass") is True:
        return True, "ok"
    return False, "probe_failing"


def lint_sim(path: Path) -> list[dict]:
    violations: list[dict] = []
    rel = str(path.relative_to(REPO))
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        violations.append({"sim": rel, "rule": "parse_error", "detail": str(exc)})
        return violations

    assigns = _module_level_assignments(tree)

    # C1: classification
    cls = assigns.get("classification", "__MISSING__")
    if cls == "__MISSING__":
        violations.append({"sim": rel, "rule": "C1_classification_missing", "detail": None})
    elif cls not in VALID_CLASSIFICATIONS:
        violations.append({"sim": rel, "rule": "C1_classification_invalid",
                           "detail": repr(cls)})

    # C2: TOOL_MANIFEST
    manifest = assigns.get("TOOL_MANIFEST", "__MISSING__")
    if manifest == "__MISSING__":
        violations.append({"sim": rel, "rule": "C2_manifest_missing", "detail": None})
    elif not isinstance(manifest, dict) or not manifest:
        violations.append({"sim": rel, "rule": "C2_manifest_malformed",
                           "detail": type(manifest).__name__})
    else:
        for tool, entry in manifest.items():
            if not isinstance(entry, dict):
                violations.append({"sim": rel, "rule": "C2_manifest_entry_malformed",
                                   "detail": f"{tool}: {type(entry).__name__}"})
                continue
            reason = entry.get("reason")
            # empty reason acceptable when used=False (honest non-use)
            if entry.get("used") is True and (not isinstance(reason, str) or not reason.strip()):
                violations.append({"sim": rel, "rule": "C2_reason_empty",
                                   "detail": str(tool)})

    # C3: TOOL_INTEGRATION_DEPTH
    depth = assigns.get("TOOL_INTEGRATION_DEPTH", "__MISSING__")
    if depth == "__MISSING__":
        violations.append({"sim": rel, "rule": "C3_depth_missing", "detail": None})
    elif not isinstance(depth, dict) or not depth:
        violations.append({"sim": rel, "rule": "C3_depth_malformed",
                           "detail": type(depth).__name__})
    else:
        for tool, lvl in depth.items():
            if lvl not in VALID_DEPTHS:
                violations.append({"sim": rel, "rule": "C3_depth_invalid_value",
                                   "detail": f"{tool}={lvl!r}"})

    # C4: divergence_log required when classical_baseline
    if cls == "classical_baseline":
        dl = assigns.get("divergence_log", "__MISSING__")
        if dl == "__MISSING__":
            violations.append({"sim": rel, "rule": "C4_divergence_log_missing", "detail": None})
        elif not (isinstance(dl, str) and dl.strip()):
            violations.append({"sim": rel, "rule": "C4_divergence_log_empty",
                               "detail": repr(dl)})

    # C5: load_bearing tools need passing capability probe
    if isinstance(depth, dict):
        for tool, lvl in depth.items():
            if lvl != "load_bearing":
                continue
            canon = canonical(str(tool))
            # Self-probe exception
            if path.name == f"sim_{canon}_capability.py":
                continue
            ok, detail = _capability_ok(canon)
            if not ok:
                violations.append({"sim": rel, "rule": f"C5_{detail}",
                                   "detail": f"{tool}->{canon}"})

    # C6: classical_baseline sims may not carry load_bearing tools (Lane B doctrine)
    if cls == "classical_baseline" and isinstance(depth, dict):
        for tool, lvl in depth.items():
            if lvl == "load_bearing":
                violations.append({"sim": rel, "rule": "C6_classical_has_load_bearing",
                                   "detail": str(tool)})

    return violations


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-archive", action="store_true",
                    help="Include _archive_lane_c sims (default: excluded).")
    args = ap.parse_args()

    sims = sorted(PROBES_DIR.glob("sim_*.py"))
    if not args.include_archive:
        sims = [s for s in sims if "_archive_lane_c" not in s.parts]

    all_violations: list[dict] = []
    for sim in sims:
        all_violations.extend(lint_sim(sim))

    by_type = Counter(v["rule"] for v in all_violations)
    per_sim: dict = defaultdict(set)
    for v in all_violations:
        per_sim[v["sim"]].add(v["rule"])
    top_offenders = sorted(
        ({"sim": s, "distinct_rules": len(rs),
          "rules": sorted(rs)} for s, rs in per_sim.items()),
        key=lambda x: (-x["distinct_rules"], x["sim"]),
    )[:10]

    report = {
        "checked": len(sims),
        "violation_total": len(all_violations),
        "sims_with_violations": len(per_sim),
        "violations_by_type": dict(by_type.most_common()),
        "top_offenders": top_offenders,
        "violations": all_violations,
    }
    print(json.dumps(report, indent=2))
    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
