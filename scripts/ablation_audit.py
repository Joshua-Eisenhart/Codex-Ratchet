#!/usr/bin/env python3
"""Static ablation risk scanner.

Scans system_v4/probes/sim_*.py for sims declaring a non-numpy tool as
load_bearing in TOOL_INTEGRATION_DEPTH, and heuristically classifies the risk
that the tool is decorative (could be swapped for numpy without invalidating
the claim).

This does NOT run ablations. It is a triage harness to guide human review.

Heuristics per tool call site:
  - HIGH risk   : tool imported but appears <=1 times in body, or only in
                  expressions whose result is compared for numeric equality
                  without branching / assertion gating.
  - MEDIUM risk : tool appears >1 times but never gates control flow
                  (no if/assert/raise on its result).
  - LOW risk    : tool result feeds an if/assert/while/branch condition, or
                  a .check()/.prove()/.is_sat style gating call is present.
"""
from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROBES = REPO / "system_v4" / "probes"
OUT = REPO / "overnight_logs" / "ablation_audit.json"

NUMPY_NAMES = {"numpy", "np"}

# Tool-specific gating call signatures that strongly indicate load-bearing use.
GATING_CALLS = {
    "z3": {"check", "prove", "solve", "is_unsat", "is_sat"},
    "cvc5": {"checkSat", "check_sat", "check"},
    "sympy": {"simplify", "solve", "satisfiable", "Eq"},
    "torch": {"backward", "autograd"},
    "networkx": {"is_isomorphic", "is_connected"},
    "toponetx": {},
    "torch_geometric": {},
    "clifford": {},
}


def _literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def parse_manifest(tree: ast.AST):
    manifest = None
    depth = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    if t.id == "TOOL_MANIFEST":
                        manifest = _literal(node.value)
                    elif t.id == "TOOL_INTEGRATION_DEPTH":
                        depth = _literal(node.value)
    return manifest, depth


def tool_risk(tool: str, source: str) -> str:
    # Count attribute/call uses of the module.
    pat_use = re.compile(rf"\b{re.escape(tool)}\b\s*[.(]")
    uses = pat_use.findall(source)
    n_uses = len(uses)

    # Import-only detector: imported but zero attribute access on the module.
    imported = bool(
        re.search(rf"^\s*import\s+{re.escape(tool)}\b", source, re.MULTILINE)
        or re.search(rf"^\s*from\s+{re.escape(tool)}\b", source, re.MULTILINE)
    )
    if imported and n_uses == 0:
        return "HIGH"

    # Tightened gating for z3/cvc5: require a solver-like object to be bound
    # (e.g. `s = z3.Solver()` or `slv = cvc5.Solver(...)`) AND a `.check(`
    # call on any name to count as load-bearing.
    if tool in ("z3", "cvc5"):
        solver_bind = re.search(
            rf"(\w+)\s*=\s*{re.escape(tool)}\s*\.\s*Solver\s*\(",
            source,
        )
        has_check = bool(re.search(r"\.\s*check\s*\(", source)) or bool(
            re.search(r"\.\s*checkSat\s*\(", source)
        )
        if solver_bind and has_check:
            # Extra: the bound solver's name must appear before a .check
            name = solver_bind.group(1)
            if re.search(rf"\b{re.escape(name)}\b\s*\.\s*check", source):
                return "LOW"
        # If z3/cvc5 imported but no bound-solver+.check pattern, HIGH.
        return "HIGH" if n_uses <= 2 else "MEDIUM"

    # Gating: does a known gating call appear?
    gate_names = GATING_CALLS.get(tool, set())
    gated = False
    for g in gate_names:
        if re.search(rf"\b{re.escape(tool)}\b[^\n]*\.{re.escape(g)}\s*\(", source):
            gated = True
            break
    if not gated and gate_names:
        for g in gate_names:
            if re.search(rf"\.{re.escape(g)}\s*\(", source):
                gated = True
                break

    branch_gated = bool(
        re.search(
            rf"\b{re.escape(tool)}\b[^\n]{{0,200}}\n[^\n]*?(?:if |assert |while |raise )",
            source,
        )
    ) or bool(
        re.search(
            rf"(?:if |assert |while )[^\n]*\b{re.escape(tool)}\b",
            source,
        )
    )

    if gated or branch_gated:
        return "LOW"
    if n_uses <= 1:
        return "HIGH"
    return "MEDIUM"


def scan_file(path: Path):
    try:
        source = path.read_text()
    except Exception as e:
        return {"error": f"read_failed: {e}"}
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"parse_failed: {e}"}

    manifest, depth = parse_manifest(tree)
    if not isinstance(depth, dict):
        return None

    rows = []
    for tool, level in depth.items():
        if level != "load_bearing":
            continue
        if tool in NUMPY_NAMES:
            continue
        risk = tool_risk(tool, source)
        rows.append(
            {
                "sim_path": str(path.relative_to(REPO)),
                "tool": tool,
                "heuristic_risk": risk,
                "manifest_reason": (
                    (manifest or {}).get(tool, {}).get("reason")
                    if isinstance(manifest, dict)
                    else None
                ),
            }
        )
    return rows


def main():
    rows_all = []
    errors = []
    skipped = 0
    scanned = 0
    for p in sorted(PROBES.glob("sim_*.py")):
        name = p.name
        if name.endswith(" 2.py") or " 2.py" in name:
            skipped += 1
            continue
        scanned += 1
        result = scan_file(p)
        if result is None:
            continue
        if isinstance(result, dict) and "error" in result:
            errors.append({"sim_path": str(p.relative_to(REPO)), **result})
            continue
        rows_all.extend(result)

    summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in rows_all:
        summary[r["heuristic_risk"]] = summary.get(r["heuristic_risk"], 0) + 1

    out = {
        "scanned": scanned,
        "skipped_duplicates": skipped,
        "load_bearing_claims": len(rows_all),
        "summary_by_risk": summary,
        "rows": rows_all,
        "parse_errors": errors,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True))
    print(f"wrote {OUT}")
    print(f"scanned={scanned} skipped={skipped} claims={len(rows_all)} summary={summary}")


if __name__ == "__main__":
    main()
