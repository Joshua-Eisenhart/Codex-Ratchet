#!/usr/bin/env python3
"""Detect fabrication tells in capstone-class sim probes.

Based on two confirmed fabrication incidents 2026-04-17 (Agent C + Haiku capstone).
Both shipped probes claiming engine schedule applied, axis integration, tool
load-bearing — but every signal was randomized or vacuous.

Run: python3 ops/detect_capstone_fabrication.py <probe.py>
Exit 0 = clean. Exit 1 = fabrication tells detected.

Scope: sim probes claiming to apply a named schedule, import from existing axis
probes, or use tools as load-bearing. Does NOT apply to tool-capability probes
or shell-local probes where random states are legitimate.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path


FABRICATION_PATTERNS = [
    # Pattern 1: random density per stage = schedule never applied
    (r'rho\s*=\s*.*random', "density matrix re-randomized — schedule never applied to state"),
    (r'make_random_density_matrix', "random-density-per-stage = fabricated schedule"),

    # Pattern 2: random unitary labelled as schedule
    (r'random_unitary.*seed', "random_unitary with hardcoded seed masquerading as named schedule"),
    (r'haar.*random', "Haar-random unitary used as 'schedule'"),

    # Pattern 3: torch imported but numpy used for math
    # (bad: `import torch` plus `np.linalg.` or `np.dot` in evolution code)
    # flagged separately below with numpy-dominant check

    # Pattern 4: vacuous z3/cvc5 assertions
    (r'z3\.BitVec.*!=\s*0', "z3 vacuous 'variable != 0' constraint — not tied to schedule"),
    (r'Int.*>=?\s*-?\d+.*<=?\s*\d+', "generic integer range constraint — not load-bearing proof"),
    (r'sat.*\|.*trivial.*bound', "SMT assertion on trivial bounds"),

    # Pattern 5: sympy tautology check
    (r'sp\.satisfiable\(True\)', "sympy.satisfiable(True) — vacuous tautology check"),
    (r'simplify\(True\)', "sympy simplify(True) — vacuous"),
    (r'Eq\(\s*0\s*,\s*0\s*\)', "sympy Eq(0, 0) — vacuous"),

    # Pattern 6: Clifford constructed but unused
    (r'e1\s*\*\s*e2.*#.*(never used|unused|not applied)', "Clifford blade constructed but never applied"),

    # Pattern 7: PyG message never fed back
    (r'aggr\s*=\s*["\']mean["\'].*\n.*return.*x\s*$', "PyG aggr=mean with identity message — output not fed back"),
]


def analyze(probe_path: Path) -> list[tuple[str, int, str]]:
    """Return list of (pattern_desc, line_no, excerpt) for fabrication tells."""
    try:
        txt = probe_path.read_text()
    except Exception as e:
        return [("unreadable", 0, str(e))]

    findings: list[tuple[str, int, str]] = []
    lines = txt.splitlines()

    for pat, desc in FABRICATION_PATTERNS:
        for i, line in enumerate(lines, 1):
            if re.search(pat, line):
                findings.append((desc, i, line.strip()[:120]))

    # Numpy-dominant heuristic: if import torch exists but torch.XX usage < numpy usage
    if "import torch" in txt:
        torch_uses = len(re.findall(r'\btorch\.\w', txt))
        numpy_uses = len(re.findall(r'\bnp\.\w|\bnumpy\.\w', txt))
        if numpy_uses > 0 and torch_uses < numpy_uses / 3:
            findings.append((
                f"torch imported but numpy-dominant ({numpy_uses} np uses vs {torch_uses} torch) — likely fabricated 'torch load-bearing' claim",
                0,
                f"torch_uses={torch_uses}, numpy_uses={numpy_uses}",
            ))

    # Stage/schedule application check: if probe claims schedule and has "stage" variable,
    # check that rho (or state) appears to be evolved (not reassigned) between stages
    if re.search(r'stage[_\s]*(\d|one|two|three|four)', txt, re.I):
        # Look for stage loops that reassign rho from scratch
        if re.search(r'for.*stage.*:\s*\n\s*rho\s*=\s*(np\.random|make_random|random_unitary)', txt):
            findings.append((
                "stage loop reassigns rho to random — state not evolved across stages",
                0,
                "schedule claim inconsistent with stage-wise reassignment",
            ))

    return findings


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 detect_capstone_fabrication.py <probe.py>")
        return 2

    probe = Path(sys.argv[1])
    if not probe.exists():
        print(f"NOT FOUND: {probe}")
        return 2

    findings = analyze(probe)
    if not findings:
        print(f"CLEAN: {probe.name} — no fabrication tells detected")
        return 0

    print(f"FABRICATION TELLS DETECTED: {probe.name}")
    for desc, line, excerpt in findings:
        loc = f"line {line}" if line else "whole file"
        print(f"  [{loc}] {desc}")
        if excerpt:
            print(f"    → {excerpt}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
