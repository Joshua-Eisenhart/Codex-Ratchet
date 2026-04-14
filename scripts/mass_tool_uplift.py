#!/usr/bin/env python3
"""mass_tool_uplift.py -- propose tool-layer uplifts across many sims at once.

Given a tool name (e.g. "z3") and a target pattern (e.g. "negation-of-positive-claim
should be UNSAT"), scan candidate sims and emit a proposed patch per candidate.

NO AUTO-APPLY. Proposals only. Humans/next-layer agents review.

Usage:
    python scripts/mass_tool_uplift.py \\
        --tool z3 \\
        --pattern neg_of_positive_unsat \\
        --glob 'classical_baseline_*.py' \\
        --out overnight_logs/mass_uplift_proposals.md
"""
from __future__ import annotations
import argparse, ast, glob, os, re, sys
from dataclasses import dataclass, field
from typing import Optional

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBES = os.path.join(REPO, "system_v4", "probes")


# Heuristic admissibility keywords -- "this X must hold" kinds of claims.
ADMISSIBILITY_KEYWORDS = [
    "admissib", "must", "invariant", "conserved", "orthogon", "unitary",
    "idempotent", "closed under", "commut", "equal", "identity", "preserv",
    "bound", "monotone", "nonneg", "nonnegative", "positive definite",
    "fence", "constraint", "forbidden", "cannot", "never", "always",
]

# Pattern templates keyed by --pattern arg.
PATTERN_TEMPLATES = {
    "neg_of_positive_unsat": {
        "description": "Encode the negation of each positive-test claim as a z3 "
                       "assertion. If the sim's positive claim is truly admissible, "
                       "the solver must return UNSAT. SAT = counterexample found.",
        "z3_skeleton": (
            "from z3 import Solver, Real, Bool, Not, sat, unsat\n"
            "def z3_admissibility_fence():\n"
            "    s = Solver()\n"
            "    # TODO: translate each positive-test claim into z3 terms,\n"
            "    # then assert Not(claim). UNSAT => claim is admissibility-closed.\n"
            "    # SAT   => counterexample exists; sim's 'positive' is not a fence.\n"
            "    return {'z3_unsat': s.check() == unsat}\n"
        ),
    },
}


@dataclass
class SimInfo:
    path: str
    name: str
    classification: Optional[str] = None
    scope_note: Optional[str] = None
    admissibility_hits: list = field(default_factory=list)
    has_positive: bool = False
    has_z3_already: bool = False
    uplift_score: int = 0


def _extract_string_assignment(tree: ast.AST, varname: str) -> Optional[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == varname:
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        return node.value.value
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == varname and isinstance(v, ast.Constant):
                    if isinstance(v.value, str):
                        return v.value
    return None


def parse_sim(path: str) -> Optional[SimInfo]:
    try:
        with open(path, "r") as f:
            src = f.read()
    except OSError:
        return None
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None

    info = SimInfo(path=path, name=os.path.basename(path))

    # classification: look in results dict or module-level var
    cls = _extract_string_assignment(tree, "classification")
    # also search dict literal like {"classification": "classical_baseline"}
    if cls is None:
        m = re.search(r"""["']classification["']\s*:\s*["']([^"']+)["']""", src)
        if m:
            cls = m.group(1)
    info.classification = cls

    info.scope_note = _extract_string_assignment(tree, "scope_note")

    # Find positive-test function and extract a claim-ish blob
    pos_blob = ""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("run_positive"):
            info.has_positive = True
            pos_blob = ast.get_source_segment(src, node) or ""

    # Admissibility keyword hits in docstring/scope_note/positive-test block
    search_text = " ".join([
        ast.get_docstring(tree) or "",
        info.scope_note or "",
        pos_blob,
    ]).lower()
    for kw in ADMISSIBILITY_KEYWORDS:
        if kw in search_text:
            info.admissibility_hits.append(kw)

    # Already using z3?
    info.has_z3_already = bool(
        re.search(r"TOOL_INTEGRATION_DEPTH.*z3.*load_bearing", src, re.DOTALL)
        or re.search(r"from\s+z3\s+import", src)
    )

    info.uplift_score = (
        (2 if info.classification == "classical_baseline" else 0)
        + len(info.admissibility_hits)
        + (1 if info.has_positive else 0)
        - (5 if info.has_z3_already else 0)
    )
    return info


def extract_positive_claim_summary(path: str) -> str:
    """Grab the `return {...}` dict inside run_positive_tests as a claim sketch."""
    try:
        src = open(path).read()
    except OSError:
        return ""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("run_positive"):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and sub.value is not None:
                    seg = ast.get_source_segment(src, sub.value) or ""
                    return seg.strip().replace("\n", " ")[:220]
    return ""


def build_proposal(info: SimInfo, tool: str, pattern: str) -> str:
    tmpl = PATTERN_TEMPLATES[pattern]
    claim = extract_positive_claim_summary(info.path)
    reason = (
        f"positive-test dict asserts: `{claim}`. Under pattern "
        f"`{pattern}`, assert Not(<claim>) in {tool}. Expected UNSAT "
        f"if the claim is an admissibility fence; SAT exposes a "
        f"counterexample that falsifies the fence."
    )
    return (
        f"### {info.name}\n\n"
        f"- path: `{os.path.relpath(info.path, REPO)}`\n"
        f"- classification: `{info.classification}`\n"
        f"- uplift_score: {info.uplift_score}\n"
        f"- admissibility_hits: {info.admissibility_hits}\n"
        f"- positive_claim: `{claim or '(none extracted)'}`\n"
        f"- proposed tool: `{tool}`\n"
        f"- proposed assertion: `Not({claim or '<positive_claim>'})`\n"
        f"- expected UNSAT reason: {reason}\n"
        f"- patch skeleton:\n\n"
        f"```python\n{tmpl['z3_skeleton']}```\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", default="z3")
    ap.add_argument("--pattern", default="neg_of_positive_unsat",
                    choices=list(PATTERN_TEMPLATES.keys()))
    ap.add_argument("--glob", default="classical_baseline_*.py")
    ap.add_argument("--probes-dir", default=PROBES)
    ap.add_argument("--out", default=os.path.join(REPO, "overnight_logs", "mass_uplift_proposals.md"))
    ap.add_argument("--limit", type=int, default=0, help="0 = no limit")
    args = ap.parse_args()

    candidates = sorted(glob.glob(os.path.join(args.probes_dir, args.glob)))
    infos = []
    for p in candidates:
        info = parse_sim(p)
        if info is None:
            continue
        if info.classification != "classical_baseline":
            continue
        if info.has_z3_already:
            continue
        if not info.admissibility_hits:
            continue
        infos.append(info)

    infos.sort(key=lambda i: -i.uplift_score)
    if args.limit:
        infos = infos[: args.limit]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    tmpl = PATTERN_TEMPLATES[args.pattern]
    with open(args.out, "w") as f:
        f.write(f"# Mass Tool Uplift Proposals\n\n")
        f.write(f"- tool: `{args.tool}`\n")
        f.write(f"- pattern: `{args.pattern}` — {tmpl['description']}\n")
        f.write(f"- glob: `{args.glob}`\n")
        f.write(f"- eligible sims: {len(infos)}\n")
        f.write(f"- scanned: {len(candidates)}\n\n")
        f.write("STATUS: proposals only. No sims modified. Review then apply.\n\n")
        f.write("## Top candidates (by uplift_score)\n\n")
        for i in infos[:5]:
            f.write(f"- **{i.name}** (score {i.uplift_score}, hits={i.admissibility_hits})\n")
        f.write("\n---\n\n## Proposals\n\n")
        for info in infos:
            f.write(build_proposal(info, args.tool, args.pattern))
            f.write("\n---\n\n")
    print(f"wrote {args.out}  eligible={len(infos)}  scanned={len(candidates)}")
    for i in infos[:5]:
        print(f"  top: {i.name}  score={i.uplift_score}  hits={i.admissibility_hits}")


if __name__ == "__main__":
    main()
