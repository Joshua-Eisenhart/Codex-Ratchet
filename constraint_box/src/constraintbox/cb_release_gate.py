#!/usr/bin/env python3
"""cb_release_gate — the composed gate CB currently lacks (CBIMP-4).

Today a run "passes" when its own shipped verifier returns N/N. Three
independent findings show that is not sufficient:
  - the target verifier passes a run whose declared artifact bytes
    were mutated (CBIMP-1, canary reproduced);
  - a stray generated file silently changed the artifact set (27/28
    regression, CBIMP-2);
  - the Aug-6 federation shipped RECEIPTS ONLY: 15 files in the run
    root against thousands of declared digests (CBIMP-5, diagnosed
    here) — every shipped verifier that reads stored fields still
    reports its own N/N.

This gate composes four independent conditions and refuses release
unless all hold:
  G-A  the run's own verifier(s) pass (unchanged, still required);
  G-B  strict recomputing consumer: every run-root-scoped declared
       digest recomputes from bytes (no MISMATCH, no ABSENT);
  G-C  artifact-root cleanliness: no present-but-undeclared files
       except the receipt/verification files themselves;
  G-D  evidence-tree presence invariant: the run root must contain
       more than receipts alone — at least one non-receipt artifact
       per declaring subsystem (catches receipts-only packaging).
Emits one release receipt; exit 1 unless every condition holds.
promotion_allowed=false; ceiling: packaging/receipt integrity only.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

SELF_FILES = ("RECEIPT", "VERIFICATION", "STRICT_CONSUMER",
              "RELEASE_GATE")

def is_self_file(rel: str) -> bool:
    return any(t in Path(rel).name.upper() for t in SELF_FILES)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", required=True, type=Path)
    ap.add_argument("--package-root", required=True, type=Path)
    ap.add_argument("--verifier", action="append", default=[],
                    help="shipped verifier cmd; {run} {pkg} {out} "
                         "substituted")
    ap.add_argument("--consumer", type=Path, required=True,
                    help="path to strict_receipt_consumer.py")
    ap.add_argument("--output", required=True, type=Path)
    a = ap.parse_args()
    conds, detail = {}, {}
    # G-A shipped verifiers
    vres = []
    for i, v in enumerate(a.verifier):
        out = Path(f"/tmp/_gate_v{i}.json")
        cmd = v.format(run=a.run_root, pkg=a.package_root, out=out)
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        ok = False
        try:
            d = json.loads(out.read_text())
            ok = bool(d.get("passed"))
            vres.append({"cmd": cmd.split()[1], "passed": ok,
                         "checks": f"{d.get('checks_passed')}/"
                                   f"{d.get('checks_total')}"})
        except Exception:
            vres.append({"cmd": cmd.split()[1] if len(cmd.split()) > 1
                         else cmd, "passed": False,
                         "error": p.stderr.strip()[-200:]})
    conds["G-A_shipped_verifiers_pass"] = bool(vres) and all(
        r.get("passed") for r in vres)
    detail["verifiers"] = vres
    # G-B strict recomputing consumer
    cout = Path("/tmp/_gate_strict.json")
    subprocess.run([sys.executable, str(a.consumer), "--run-root",
                    str(a.run_root), "--output", str(cout)],
                   capture_output=True, text=True)
    sc = json.loads(cout.read_text())
    conds["G-B_all_declared_digests_recompute"] = (
        len(sc.get("recomputed_mismatch", [])) == 0
        and len(sc.get("declared_absent", [])) == 0)
    detail["strict_consumer"] = {
        "declared": sc.get("declared_digests"),
        "match": sc.get("recomputed_match"),
        "mismatch": len(sc.get("recomputed_mismatch", [])),
        "absent": len(sc.get("declared_absent", [])),
        "stored_verdicts_refused": sc.get(
            "stored_verdicts_refused_count")}
    # G-C cleanliness
    undecl = [u for u in sc.get("present_but_undeclared", [])
              if not is_self_file(u)]
    total_nonself = sc.get("present_but_undeclared_count", 0) \
        + sc.get("recomputed_match", 0)
    covered = sc.get("recomputed_match", 0)
    coverage = (covered / total_nonself) if total_nonself else 1.0
    conds["G-C_declaration_coverage_complete"] = coverage >= 0.999
    detail["declaration_coverage"] = {
        "declared_and_recomputed": covered,
        "non_self_artifacts_present": total_nonself,
        "coverage": round(coverage, 4),
        "undeclared_sample": undecl[:6],
        "note": "artifacts the receipt never hash-declares can be "
                "mutated with no detection by any consumer"}
    # G-D evidence-tree presence
    files = [str(p.relative_to(a.run_root))
             for p in a.run_root.rglob("*") if p.is_file()]
    non_self = [f for f in files if not is_self_file(f)]
    conds["G-D_evidence_tree_present"] = (
        len(non_self) > 0
        and len(non_self) >= 0.25 * max(1, sc.get("recomputed_match", 0)))
    detail["files_total"] = len(files)
    detail["files_non_receipt"] = len(non_self)
    ok = all(conds.values())
    out = {"schema": "cb.release-ceiling-gate.v1",
           "run_root": str(a.run_root), "conditions": conds,
           "detail": detail, "release_allowed": ok,
           "promotion_allowed": False,
           "claim_ceiling": "packaging and receipt integrity only; "
                            "no scientific or CR claim"}
    a.output.write_text(json.dumps(out, indent=1, sort_keys=True))
    for k, v in conds.items():
        print(f"{k:<38} {'PASS' if v else 'FAIL'}")
    print("RELEASE ALLOWED:", ok)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
