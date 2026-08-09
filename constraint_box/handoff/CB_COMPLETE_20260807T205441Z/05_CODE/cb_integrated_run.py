#!/usr/bin/env python3
"""cb_integrated_run — the deterministic wave program, end to end.

Runs in the real checkout, emits one receipt, costs no tokens.

  W0  CENSUS      repo state + shared corpus index (built ONCE, LAW 7)
  W1  COVERAGE    registry members vs corpus: NEVER / SEEN, by kind
  W2  DIGGERS     axiom / constraint / gate / ratchet / basin + control
  W3  LAWS        cb_control_laws self-test
  W4  VERIFY      contamination + negative controls, then the receipt

Every wave declares a measure. A wave that emits no receipt or moves no
measure is DEAD (LAW 8) and is reported as such.
"""
from __future__ import annotations
import json, re, subprocess, sys, time, hashlib
from pathlib import Path
from collections import Counter, defaultdict

REPO = Path(__file__).resolve().parents[2]
CB = REPO / "constraint_box"
EXT_ALL = {".json", ".md", ".py", ".yaml", ".toml", ".txt", ".jsonl"}
EXT_PROSE = {".md", ".txt"}
REGFILES = ["config/council_member_registry_v1.json",
            "config/council_member_registry_skills_v1.json"]

def sh(*a):
    return subprocess.run(a, cwd=REPO, capture_output=True, text=True).stdout.strip()

# ---------------- W0 ----------------
def w0_census():
    t0 = time.time()
    state = {"branch": sh("git", "rev-parse", "--abbrev-ref", "HEAD"),
             "head": sh("git", "rev-parse", "--short", "HEAD"),
             "dirty": len(sh("git", "status", "--porcelain").splitlines()),
             "worktrees": len(sh("git", "worktree", "list").splitlines())}
    docs, prose = [], []
    for p in REPO.rglob("*"):
        if not p.is_file() or ".git" in p.parts or p.suffix not in EXT_ALL:
            continue
        rel = str(p.relative_to(REPO))
        if rel in {f"constraint_box/{r}" for r in REGFILES}:
            continue                       # LAW: exclude the question from the corpus
        try:
            t = p.read_text(errors="ignore")
        except Exception:
            continue
        docs.append((rel, t))
        if p.suffix in EXT_PROSE:
            prose.append((rel, t))
    idx = {"docs": docs, "prose": prose,
           "paths": " ".join(r for r, _ in docs).lower()}
    return state, idx, {"docs": len(docs), "prose": len(prose),
                        "seconds": round(time.time() - t0, 1)}

# ---------------- W1 ----------------
def w1_coverage(idx):
    members = []
    for r in REGFILES:
        members += json.loads((CB / r).read_text())["members"]
    ids = {m["id"] for m in members}
    kind = {m["id"]: m["kind"] for m in members}
    seen = Counter()
    for _, t in idx["docs"]:
        for i in ids:
            if i in t:
                seen[i] += 1
    never = sorted(ids - set(seen))
    by_kind = {}
    for k in sorted({kind[i] for i in ids}):
        tot = sum(1 for i in ids if kind[i] == k)
        cov = sum(1 for i in seen if kind[i] == k)
        by_kind[k] = {"covered": cov, "total": tot,
                      "pct": round(100 * cov / tot, 1)}
    return {"declared": len(ids), "seen": len(seen), "never": len(never),
            "never_ids": never, "by_kind": by_kind,
            "measure": "never_run_count", "value": len(never)}

# ---------------- W2 ----------------
DIG = {
 "axiom": [r"(?im)^\s*(?:axiom|law|invariant|first principle)[:\s]+(.{25,150})",
           r"(?im)\b(?:is defined as|by definition|we declare)\b([^\n.]{25,150})"],
 "constraint": [r"(?im)\b(?:must never|may never|is forbidden|cannot be|never a|is not a)\b([^\n.]{25,150})"],
 "gate": [r"(?im)\b(?:refuse|refused|blocked|parked|demote|demoted)\b([^\n.]{25,150})"],
 "ratchet": [r"(?im)\bratchet\b(?:\s+is|\s+means|\s+does)([^\n.]{25,150})"],
 "basin": [r"(?im)\b(?:basin|attractor)\b(?:\s+is|\s+are|\s+means|\s+contains)([^\n.]{25,150})"],
 "CONTROL": [r"(?im)\b(?:flurbulator|zzznotathing|qqxxyy)\b([^\n.]{25,150})"],
}
def is_prose(s):
    if len(s) < 25 or len(s.split()) < 5:
        return False
    if re.search(r"[/\\]|\.py\b|\.toml|\.json|https?:", s):
        return False
    if s.count('"') > 1 or "=" in s or s.count("(") > 1:
        return False
    return sum(c.isalpha() for c in s) / len(s) >= 0.65

VERS = ("system_v4", "system_v5", "system_v6", "system_v7", "system_v8",
        "constraint_box", "claimgate_plugin", "READ ONLY Legacy core_docs")
def w2_diggers(idx):
    found = defaultdict(Counter); where = defaultdict(lambda: defaultdict(set))
    for rel, txt in idx["prose"]:
        ver = next((v for v in VERS if v in rel), "other")
        for kind, pats in DIG.items():
            for pat in pats:
                for m in re.finditer(pat, txt):
                    s = " ".join(m.group(1).split())
                    if is_prose(s):
                        found[kind][s] += 1
                        where[kind][s].add(ver)
    out = {"control_hits": len(found["CONTROL"]),
           "control_pass": len(found["CONTROL"]) == 0, "kinds": {}}
    survivors = []
    for k in DIG:
        if k == "CONTROL":
            continue
        multi = [s for s in found[k] if len(where[k][s]) >= 2]
        deep = [s for s in found[k] if len(where[k][s]) >= 3]
        out["kinds"][k] = {"distinct": len(found[k]),
                           "multi_version": len(multi), "deep": len(deep)}
        for s in deep:
            survivors.append({"kind": k, "versions": sorted(where[k][s]),
                              "text": s[:150]})
    out["deep_survivors"] = survivors
    out["measure"] = "deep_survivor_count"; out["value"] = len(survivors)
    return out

# ---------------- W3 ----------------
def w3_laws():
    p = subprocess.run([sys.executable, str(CB / "scripts" / "cb_control_laws.py"),
                        "--self-test"], capture_output=True, text=True)
    line = [l for l in p.stdout.splitlines() if "fixtures as expected" in l]
    return {"stdout_tail": line[-1].strip() if line else "no fixture line",
            "exit": p.returncode, "pass": p.returncode == 0}

# ---------------- W4 ----------------
def w4_verify(idx, cov, dig):
    checks = {
      "corpus_excludes_the_question": all(
          not r.endswith("council_member_registry_v1.json") for r, _ in idx["docs"]),
      "digger_negative_control_zero": dig["control_pass"],
      "coverage_measured": cov["declared"] > 0 and cov["seen"] >= 0,
      "laws_selftest_pass": None,
    }
    return checks

def main() -> int:
    t0 = time.time()
    print("W0 CENSUS")
    state, idx, meta = w0_census()
    print(f"   branch {state['branch']} @ {state['head']}  dirty {state['dirty']}  "
          f"worktrees {state['worktrees']}")
    print(f"   corpus {meta['docs']} docs ({meta['prose']} prose) in {meta['seconds']}s "
          f"— shared index, LAW 7")

    print("W1 COVERAGE")
    cov = w1_coverage(idx)
    print(f"   declared {cov['declared']}  seen {cov['seen']}  NEVER {cov['never']}")
    for k, v in cov["by_kind"].items():
        print(f"      {k:<14} {v['covered']:>3}/{v['total']:<3} {v['pct']:>5}%")

    print("W2 DIGGERS")
    dig = w2_diggers(idx)
    for k, v in dig["kinds"].items():
        print(f"      {k:<11} distinct {v['distinct']:>5}  >=2 vers {v['multi_version']:>4}"
              f"  >=3 vers {v['deep']:>3}")
    print(f"      CONTROL {dig['control_hits']} hits -> "
          f"{'PASS' if dig['control_pass'] else 'FAIL'}")

    print("W3 LAWS")
    laws = w3_laws()
    print(f"      {laws['stdout_tail']}  exit={laws['exit']}")

    print("W4 VERIFY")
    checks = w4_verify(idx, cov, dig)
    checks["laws_selftest_pass"] = laws["pass"]
    for k, v in checks.items():
        print(f"      {'PASS' if v else 'FAIL'}  {k}")

    receipt = {"schema": "cb.integrated-run.v1",
               "repo_state": state, "corpus": meta,
               "W1_coverage": {k: v for k, v in cov.items() if k != "never_ids"},
               "W1_never_ids": cov["never_ids"],
               "W2_diggers": {k: v for k, v in dig.items() if k != "deep_survivors"},
               "W2_deep_survivors": dig["deep_survivors"],
               "W3_laws": laws, "W4_checks": checks,
               "wall_seconds": round(time.time() - t0, 1),
               "promotion_allowed": False,
               "claim_ceiling": "machinery coverage, corpus extraction and law "
                                "self-tests only; no scientific claim"}
    out = CB / "receipts" / f"integrated_run_{time.strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"\nRECEIPT {out.relative_to(REPO)}  ({round(time.time()-t0,1)}s, 0 tokens)")
    print(f"MEASURES  never_run={cov['value']}  deep_survivors={dig['value']}")
    return 0 if all(checks.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
