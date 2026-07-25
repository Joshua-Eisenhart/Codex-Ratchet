#!/usr/bin/env python3
"""Does this file report a verdict it never computed?

The generic form of a defect measured in Codex-Ratchet:
  system_v7/sims/tower_g5_density_floor_v0/check_agreement.py — 132 lines,
  0 imports of z3/cvc5/subprocess, writes {"ran": true, "verdict": "unsat",
  "load_bearing": true} three times, for z3, cvc5 and julia_z3.

Nothing scientific about it. The same shape is "tests passed" in a file that
never ran the test runner, or "lint clean" in one that never invoked the linter.
A receipt-shape gate cannot catch it, because the shape is impeccable.

RULE: a file asserting a tool's verdict as a LITERAL must also invoke something
capable of producing that verdict — the tool, or a subprocess launcher.

Exit: 0 clean | 1 violation(s) | 2 usage.
Nonzero is a policy disposition, never a scientific verdict.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

# A literal verdict: a key naming a tool outcome, assigned a constant.
# NARROWED after measurement. The first version flagged any literal verdict and
# hit 1119 sites in 7879 files, including honest code where all_pass = all(checks)
# is computed in-process and needs no external tool at all. A gate that fires on
# honest work is the worse failure — people route around it.
#
# The actual defect is narrower: the file NAMES AN EXTERNAL TOOL and reports THAT
# TOOL's outcome. tower_g5 writes "z3": {"ran": true, "verdict": "unsat"}. Only a
# tool name adjacent to a literal outcome can be an uncomputed verdict, because
# only then is the file speaking for a process it did not start.
TOOLS = r'z3|cvc5|julia|jax|torch|pytorch|solver|smt|tlc|apalache|pytest|mypy|eslint'
VERDICT = re.compile(
    r'["\'](?:' + TOOLS + r')[_a-z]*["\']\s*:\s*\{[^}]{0,200}?'
    r'["\'](?:ran|verdict|load_bearing|passed)["\']\s*:\s*'
    r'(?:True|true|"unsat"|"sat"|"pass")',
    re.I | re.S)

# Evidence the file can actually produce a verdict.
INVOKES = re.compile(
    r'^\s*(?:import|from)\s+(subprocess|z3|cvc5|pytest|unittest)\b'
    r'|subprocess\.(run|Popen|check_output)'
    r'|child_process|execSync|spawnSync'
    r'|\.check\(\)|\.solve\(\)|checkSat', re.M)

SKIP = ("/fixtures/", "/test", "_test.", ".test.", "/node_modules/", "/.git/")


def scan(path: Path) -> list[str]:
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    hits = list(VERDICT.finditer(src))
    if not hits:
        return []
    if INVOKES.search(src):
        return []                      # it can genuinely produce a verdict
    # Only count literals that are actually constants in the AST, so a variable
    # named `verdict` holding a computed value is not a violation.
    out = []
    for m in hits:
        line = src[:m.start()].count("\n") + 1
        out.append(f"{path}:{line}: literal {m.group(0)} with no tool or "
                   f"subprocess invocation in this file")
    return out


def main(argv):
    roots = [Path(a) for a in argv] or [Path(".")]
    violations = []
    for root in roots:
        files = [root] if root.is_file() else [
            p for p in root.rglob("*")
            if p.suffix in (".py", ".ts", ".js", ".mjs") and p.is_file()
            and not any(s in p.as_posix() for s in SKIP)]
        for f in files:
            violations += scan(f)
    for v in violations:
        print(f"  UNCOMPUTED VERDICT {v}")
    if violations:
        print(f"\ncheck_no_uncomputed_verdict: {len(violations)} literal verdict(s) "
              f"in files that invoke nothing able to produce them. Either invoke the "
              f"tool and derive the field, or remove the field.", file=sys.stderr)
        return 1
    print("check_no_uncomputed_verdict: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
