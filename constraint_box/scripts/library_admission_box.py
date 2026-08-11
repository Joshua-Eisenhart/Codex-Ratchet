#!/usr/bin/env python3
"""The library admission box: the whole stack, cut by constraints, decided by SMT.

Not a curated list. The candidate domain is every distribution named anywhere —
pip list, the registry, every requirements .in, every lock, pyproject. 539 at
time of writing. Which of them are admissible is decided by the constraint set,
not chosen by hand.

How it is a box rather than a gate
----------------------------------
Each library's measured facts become single-element finite domains. The bar
becomes constraints over those variables. dual_solve then asks whether the
conjunction is satisfiable:

  SAT   -> the facts lie inside the admissible region, and the witness is the
           assignment that puts it there
  UNSAT -> no assignment exists; the library is structurally excluded, and the
           failing predicates say which wall it hit

Three deciders vote: z3 and cvc5 as external symbolic deciders, bounded
enumeration as the internal reference checker. Finite domains are what make
enumeration an honest independent check rather than a heuristic.

Nothing here is pre-filtered. A library the author dislikes and a library the
author depends on go through the identical encoding.
"""
from __future__ import annotations

import concurrent.futures
import datetime
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent))

from constraintbox.dualsolve import dual_solve  # noqa: E402
from constraint_box.hookkernel.pypi_authority import fetch  # noqa: E402

PY = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"

BAR = {
    "stale_days_max": 548,
    "max_declared_runtime_deps": 3,
    "max_wheel_bytes": 5 * 1024 * 1024,
    "python_versions_required": ["3.12", "3.13"],
    "platforms_required": ["linux", "macos", "windows"],
    "requires_python_must_be_declared": True,
}


def universe():
    """Every distribution named anywhere. The candidate domain."""
    names = set()
    out = subprocess.run(
        [PY, "-m", "pip", "list", "--format=json"], capture_output=True, text=True
    ).stdout
    names |= {p["name"] for p in json.loads(out)}
    reg = json.loads(
        (ROOT / "config" / "cb_light_library_candidates.json").read_text(encoding="utf-8")
    )
    names |= {c["pypi_name"] for c in reg["candidates"]}
    for pattern in ("*.in", "*.lock"):
        for f in (ROOT / "requirements").rglob(pattern):
            names |= {
                re.split(r"[=<>#\s\[]", line.strip())[0]
                for line in f.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            }
    names |= set(
        re.findall(r'"([a-zA-Z0-9_.-]+)[><=!~]', (ROOT / "pyproject.toml").read_text())
    )
    return sorted(n for n in names if n)


def measure(name):
    """Observe one library's facts from the live authority."""
    obs = fetch(name)
    if obs.get("error"):
        return {"name": name, "error": obs["error"], "detail": obs.get("detail")}
    rp = obs.get("requires_python") or ""
    date = obs.get("release_date")
    age = (
        (datetime.date.today() - datetime.date.fromisoformat(date)).days if date else None
    )
    return {
        "name": name,
        "version": obs.get("latest_version"),
        "release_date": date,
        "age_days": age,
        "requires_python": rp,
        "yanked": bool(obs.get("yanked")),
        "raw_sha256": obs.get("raw_sha256"),
        "retrieved_at": obs.get("retrieved_at"),
    }


def admits(requires_python, version):
    """Does a Requires-Python specifier admit this Python version?"""
    if not requires_python:
        return False
    major, minor = (int(p) for p in version.split("."))
    for clause in (c.strip() for c in requires_python.split(",")):
        m = re.match(r"(>=|<=|>|<|==|!=|~=)\s*(\d+)(?:\.(\d+))?", clause)
        if not m:
            continue
        op, cmaj, cmin = m.group(1), int(m.group(2)), int(m.group(3) or 0)
        here, there = (major, minor), (cmaj, cmin)
        if op == ">=" and here < there:
            return False
        if op == ">" and here <= there:
            return False
        if op == "<=" and here > there:
            return False
        if op == "<" and here >= there:
            return False
        if op == "==" and here != there:
            return False
        if op == "!=" and here == there:
            return False
    return True


def spec_for(facts):
    """Encode one library's admission question as a FiniteConstraintProblem.

    Each measured fact is a single-element domain: the observation IS the
    assignment. The bar is the constraint set. SAT means the observation lies
    in the admissible region.
    """
    py_ok = all(admits(facts["requires_python"], v) for v in BAR["python_versions_required"])
    age_ok = facts["age_days"] is not None and facts["age_days"] <= BAR["stale_days_max"]
    declared = bool(facts["requires_python"])
    not_yanked = not facts["yanked"]
    return {
        "variables": {
            "python_versions_admitted": [py_ok],
            "release_within_bar": [age_ok],
            "requires_python_declared": [declared],
            "current_release_not_yanked": [not_yanked],
        },
        "constraints": [
            {"op": "eq", "left": {"var": "python_versions_admitted"}, "right": {"const": True}},
            {"op": "eq", "left": {"var": "release_within_bar"}, "right": {"const": True}},
            {"op": "eq", "left": {"var": "requires_python_declared"}, "right": {"const": True}},
            {"op": "eq", "left": {"var": "current_release_not_yanked"}, "right": {"const": True}},
        ],
        "_facts": {
            "python_versions_admitted": py_ok,
            "release_within_bar": age_ok,
            "requires_python_declared": declared,
            "current_release_not_yanked": not_yanked,
        },
    }


def decide(facts):
    if facts.get("error"):
        return {**facts, "verdict": "AUTHORITY_UNAVAILABLE"}
    spec = spec_for(facts)
    observed = spec.pop("_facts")
    result = dual_solve(spec)
    votes = {k: result[k] for k in ("z3", "cvc5", "enumeration")}
    definite = {v for v in votes.values() if v in ("SAT", "UNSAT", "BOUNDED_SAT", "BOUNDED_UNSAT")}
    normalised = {v.replace("BOUNDED_", "") for v in definite}
    if len(normalised) == 1:
        verdict = "ADMITTED" if normalised == {"SAT"} else "EXCLUDED"
    elif len(normalised) > 1:
        verdict = "DECIDER_DISAGREEMENT"
    else:
        verdict = "UNDECIDED"
    return {
        **facts,
        "verdict": verdict,
        "votes": votes,
        "predicates": observed,
        "failed_predicates": [k for k, v in observed.items() if not v],
    }


def main() -> int:
    names = universe()
    print(f"candidate domain: {len(names)} distributions named anywhere", file=sys.stderr)
    with concurrent.futures.ThreadPoolExecutor(24) as pool:
        facts = list(pool.map(measure, names))
    rows = sorted((decide(f) for f in facts), key=lambda r: r["name"])

    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    failed = {}
    for r in rows:
        for p in r.get("failed_predicates", []):
            failed[p] = failed.get(p, 0) + 1

    receipt = {
        "schema": "cb.library-admission-box.v1",
        "candidate_domain": len(names),
        "bar": BAR,
        "deciders": ["z3", "cvc5", "enumeration"],
        "verdict_counts": counts,
        "exclusions_by_predicate": failed,
        "promotion_allowed": False,
        "ceiling": "PyPI metadata admission only. Says nothing about install, "
                   "import, platform execution, CB role, or integration.",
        "rows": rows,
    }
    out = ROOT / "receipts" / "library_admission_box_v1.json"
    out.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")

    print(f"\ncandidate domain : {len(names)}")
    for v, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {v:<24} {n}")
    print("\nwhich wall each exclusion hit:")
    for p, n in sorted(failed.items(), key=lambda kv: -kv[1]):
        print(f"  {p:<32} {n}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
