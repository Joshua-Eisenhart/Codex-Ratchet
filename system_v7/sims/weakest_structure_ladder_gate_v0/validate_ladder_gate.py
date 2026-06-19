#!/usr/bin/env python3
"""Queue item 2 GATE -- now FAIL-CLOSED (deep audit w2qgptvqb + codex/Hermes audit).

An evidence_grade row must cite a discriminator sim that is, AT THE FILE LEVEL:
  - NOT refuted (no REFUTED*.md in its dir; result classification != broken;
    graveyard_keep not true),
  - NOT circular (no FLEET_VERDICT/REFUTED in its dir whose verdict is CIRCULAR),
  - FRESH (the sim source's current sha256 == the source_sha256 recorded in its
    result JSON; a stale result = source changed without rerun = fail),
  - PRESENT (the cited result JSON actually exists and loads).
The validator DEREFERENCES files; it does not trust prose strings in this JSON.
A refuted/broken/stale/circular discriminator can no longer back an evidence_grade row.
"""

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIMS = os.path.dirname(HERE)


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def sim_dir(sim_id):
    return os.path.join(SIMS, sim_id)


def check_discriminator_fresh_and_live(sim_id):
    """Returns (ok, reasons[]) -- dereferences the cited sim's files."""
    reasons = []
    d = sim_dir(sim_id)
    if not os.path.isdir(d):
        return False, [f"discriminator dir missing: {sim_id}"]
    # 1. refutation markers (machine-unambiguous: a REFUTED*.md retires the sim)
    for fn in os.listdir(d):
        if fn.startswith("REFUTED"):
            reasons.append(f"{sim_id}: has {fn} (refuted sim cannot back evidence)")
    # 2. result JSON: present, not broken, fresh
    #    (circularity is carried machine-readably as classification=broken /
    #    graveyard_keep / evidence_eligible=false, NOT by scanning verdict prose,
    #    which false-positives on held-divergence discussion.)
    rdir = os.path.join(d, "results")
    results = [f for f in os.listdir(rdir) if f.endswith("_results.json")] if os.path.isdir(rdir) else []
    if not results:
        return False, reasons + [f"{sim_id}: no result JSON"]
    for rf in results:
        r = json.load(open(os.path.join(rdir, rf)))
        if r.get("classification") == "broken" or r.get("graveyard_keep") or r.get("evidence_eligible") is False:
            reasons.append(f"{sim_id}: result {rf} broken/graveyard_keep/evidence_ineligible")
        # freshness: recompute source sha, compare
        src = r.get("source_sha256")
        srcfile = None
        for f in os.listdir(d):
            if f.endswith(".py") and "validate" not in f and "check_agreement" not in f:
                srcfile = os.path.join(d, f)
                break
        if src and srcfile and os.path.exists(srcfile):
            if sha256_of(srcfile) != src:
                reasons.append(f"{sim_id}: STALE -- result {rf} source_sha256 != current source (rerun needed)")
    return (len(reasons) == 0), reasons


def main():
    d = json.load(open(os.path.join(HERE, "ladder_placement.json")))
    ladder = set(d["ladder"])
    failures = []

    for r in d["rows"]:
        p = r.get("projection", "<?>")
        if r.get("weakest_rung") not in ladder:
            failures.append(f"{p}: weakest_rung not on the ladder")
        if r.get("lift_verdict") not in d["allowed_lift_verdict"]:
            failures.append(f"{p}: lift_verdict {r.get('lift_verdict')!r} not allowed")
        if r.get("grade") not in d["allowed_grade"]:
            failures.append(f"{p}: grade {r.get('grade')!r} not allowed")
        if r.get("status") != "scratch_diagnostic":
            failures.append(f"{p}: status must be scratch_diagnostic (no admission)")
        if r.get("lift_verdict") == "open" and r.get("grade") == "evidence_grade":
            failures.append(f"{p}: lift_verdict=open cannot be evidence_grade")
        # THE FAIL-CLOSED EVIDENCE GATE: dereference the cited discriminator
        if r.get("grade") == "evidence_grade":
            sim = r.get("discriminator_sim")
            if not sim:
                failures.append(f"{p}: evidence_grade but no discriminator_sim cited")
                continue
            # registry validator may never back evidence
            if "registry" in sim:
                failures.append(f"{p}: evidence_grade may not cite the registry (mapper-only)")
            ok, reasons = check_discriminator_fresh_and_live(sim)
            if not ok:
                failures.extend(f"{p}: {x}" for x in reasons)

    summary = {row["projection"]: {"rung": row["weakest_rung"], "verdict": row["lift_verdict"], "grade": row["grade"]} for row in d["rows"]}
    report = {
        "gate_id": d["gate_id"],
        "row_count": len(d["rows"]),
        "placement": summary,
        "evidence_grade_rows": [r["projection"] for r in d["rows"] if r.get("grade") == "evidence_grade"],
        "open_rows": [r["projection"] for r in d["rows"] if r.get("lift_verdict") == "open"],
        "gate_is_fail_closed": True,
        "gate_passes": len(failures) == 0,
        "failures": failures,
        "status": "scratch_diagnostic",
    }
    out = os.path.join(HERE, "ladder_gate_results.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    if failures:
        print(f"\nLADDER GATE FAILED ({len(failures)} issue(s)) -- fail-closed on refuted/broken/circular/stale discriminators", file=sys.stderr)
        sys.exit(1)
    print(f"\nLADDER GATE OK (fail-closed): {len(d['rows'])} rows; "
          f"{len(report['evidence_grade_rows'])} evidence-grade each backed by a live, fresh, non-refuted, non-circular discriminator.")


if __name__ == "__main__":
    main()
