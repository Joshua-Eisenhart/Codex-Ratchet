#!/usr/bin/env python3
"""LEGACY RATCHET REGRESSION — six cases that fix what the ratchet actually enforces.

WHY THIS IS NOT OPTIONAL. claimgate_plugin/legacy_unwitnessed_baseline.py freezes
3855 refused paths and exits 0 on them. A freeze that large is indistinguishable,
from its exit code alone, from a check that has been switched off. Worse, the
typed grammar currently passes NOTHING on the committed tree (no witness
procedure is admitted), so "a new file BLOCKS" could just as easily mean "every
new file blocks", which would make the ratchet a freeze-the-repo check wearing a
ratchet's name. These cases separate those readings by RUNNING them.

    R1  frozen set, untouched                     CONDITIONAL — see below
    R2  NEW refused receipt, unbound family        expect 1   (a new claim landed)
    R3  NEW refused receipt INSIDE a bound family, expect 1   (the literal case:
        numeric measurement, no witness                        a new unwitnessed
                                                               numerical claim)
    R4  NEW receipt with no obligation at all      CONDITIONAL — see below
    R5  MUTATED frozen receipt, still refused      expect 1
    R6  baseline frozen under another classifier   expect 2   (no stale green)

R4 IS THE CASE THAT MAKES THE OTHER FIVE MEAN SOMETHING, and today it cannot be
satisfied. Measured against the landed grammar: no witness procedure has status
`admitted` (engine_witness_v0 is `purgatory`, smt_unsat_core_recheck is `absent`)
and no family declares `x-asserts-nothing`, so NOTHING passes — a metadata-only
receipt PARKs on NO_DISCHARGED_OBLIGATION. So R4's expectation is COMPUTED from
the schema by legacy_unwitnessed_baseline.pass_path():

    pass path OPEN   expect 0, and the discrimination is MEASURED
    pass path SHUT   expect 1, and the discrimination is recorded as
                     UNTESTED_NO_PASS_PATH — the ratchet is a freeze, not a
                     filter, and this runner says so instead of quietly counting
                     an expect-1 row as a success

Hard-coding expect=0 here would have made this runner fail for the right reason
and then be "fixed" by relaxing it. Hard-coding expect=1 would have laundered a
degenerate state into a green row. The expectation therefore tracks the schema.

R1 IS CONDITIONAL FOR THE SAME REASON, on a different fact. The ratchet checks
what is ON DISK, so any tracked receipt already edited before this runner starts
is a real MUTATED finding that R1 did not cause. Measured while writing this: a
concurrent lane regenerated claimgate_plugin/results/numpy_containment_regression_
v1.json, and R1 measured 1. Rather than exempting result receipts (which would
re-open exactly the hole this ratchet closes) or calling it a flake, R1 reads
`git diff --name-only HEAD -- '*.json'` first and then requires the ratchet's
MUTATED set to equal that dirty set EXACTLY — no more, no fewer. A dirty tree
turns R1 into a stronger check than a clean one, and either way the precondition
is recorded in the receipt instead of being assumed.

THE INDEX IS TOUCHED, and that is unavoidable: `git ls-files` is the committed
set, so a case about a NEW tracked receipt cannot be staged any other way. Every
case restores what it changed in a finally block, the pre-run `git status
--porcelain` is captured and re-compared at the end, and a mismatch FAILS this
runner rather than being reported as a pass. Nothing is committed.

Exit: 0 all six measured as expected | 1 a case measured differently | 2 usage.
Nonzero is a policy/infra disposition, never a scientific verdict.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RATCHET = REPO / "claimgate_plugin" / "legacy_unwitnessed_baseline.py"
BASELINE = REPO / "claimgate_plugin" / "legacy_unwitnessed_baseline.json"
# The only path glob receipt_schema.json binds today, so it is the only place a
# receipt reaches a TYPED disposition rather than UNBOUND.
BOUND_DIR = REPO / "claimgate_plugin" / "fixtures" / "bypass"
UNBOUND_DIR = REPO / "claimgate_plugin" / "fixtures" / "legacy_ratchet"

# Dot-prefixed so shell `*.json` globs in other lanes skip these while `git
# ls-files '*.json'` still sees them — the window in which they exist is seconds.
NEW_UNBOUND = UNBOUND_DIR / ".zz_ratchet_new_unbound.json"
NEW_BOUND = BOUND_DIR / ".zz_ratchet_new_unwitnessed.json"
NEW_PASSING = BOUND_DIR / ".zz_ratchet_new_passing.json"

# A numeric claim with no engine evidence of any kind.
UNWITNESSED = {
    "classification": "canonical",
    "claim": "spectral gap of the 3x3 test operator",
    "metrics": {"spectral_gap": 1.7807764064044151},
    "all_pass": True,
}
# Metadata only: no measurement, no result, no claim object, so no obligation is
# raised and none has to be discharged by the purgatory witness procedure.
PASSING = {
    "classification": "tool_lego_fit_probe",
    "name": "legacy_ratchet_discrimination_control",
    "timestamp": "2026-07-25T09:30:00Z",
    "seed": 7,
    "promotion_allowed": False,
    "digest": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
}


def sh(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(REPO), *argv], capture_output=True, text=True)


def status() -> str:
    return sh("status", "--porcelain").stdout


def ratchet() -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(RATCHET)], capture_output=True, text=True,
                       cwd=str(REPO))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def write_and_stage(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1) + "\n")
    r = sh("add", "--", str(path.relative_to(REPO)))
    if r.returncode != 0:
        raise RuntimeError(f"git add failed for {path}: {r.stderr.strip()}")


def unstage_and_remove(path: Path) -> None:
    rel = path.relative_to(REPO).as_posix()
    sh("rm", "--cached", "--quiet", "--", rel)
    path.unlink(missing_ok=True)
    try:
        if path.parent.is_dir() and not any(path.parent.iterdir()):
            path.parent.rmdir()
    except OSError:
        pass


def dirty_tracked_json() -> list[str]:
    """Tracked JSON already differing from HEAD, staged or not — the paths the
    ratchet is RIGHT to report as MUTATED and that this runner did not cause."""
    from claimgate_plugin.legacy_unwitnessed_baseline import LEDGER_ANCHORS

    out = sh("diff", "--name-only", "HEAD", "--", "*.json").stdout.split()
    return sorted(p for p in out if p and p not in LEDGER_ANCHORS)


def mutated_in(out: str) -> list[str]:
    return sorted(line.split()[1] for line in out.splitlines()
                  if line.strip().startswith("MUTATED "))


def a_frozen_parked_path() -> str:
    """A path from the frozen PARKED set, chosen deterministically. Deliberately a
    real historical receipt: mutating a synthetic file would not test that
    grandfathering is byte-bound."""
    doc = json.loads(BASELINE.read_bytes())
    for rel in sorted(doc["parked"]):
        p = REPO / rel
        if p.is_file() and rel.startswith("system_v8/"):
            return rel
    return sorted(doc["parked"])[0]


def main(argv: list[str]) -> int:
    if not BASELINE.exists():
        print(f"run_legacy_ratchet_regression: usage — no frozen baseline at {BASELINE.name}; "
              f"run --write-baseline first", file=sys.stderr)
        return 2
    before = status()
    rows: list[dict] = []

    def record(cid: str, name: str, expect: int, measured: int, out: str, marker: str = "",
               **extra) -> None:
        ok = measured == expect and (marker in out if marker else True)
        rows.append({"id": cid, "case": name, "expect_exit": expect,
                     "measured_exit": measured, "marker": marker or None,
                     "marker_seen": (marker in out) if marker else None, "as_expected": ok,
                     **extra})
        print(f"  {cid}  expect={expect} measured={measured}  {'ok' if ok else 'MISMATCH'}")
        print(f"      {name}")
        for line in out.splitlines():
            if line.strip().startswith(("NEW ", "MUTATED ", "RESOLVED ", "CLASSIFIER DRIFT",
                                        "DISPOSITION DRIFT")):
                print(f"      | {line.strip()[:150]}")

    sys.path.insert(0, str(REPO))
    dirty = dirty_tracked_json()
    rc, out = ratchet()
    if dirty:
        reported = mutated_in(out)
        exact = reported == dirty
        record("R1", f"the frozen set with {len(dirty)} tracked receipt(s) already edited before "
                     f"this run — the ratchet's MUTATED set must equal that dirty set exactly",
               1, rc, out, "", precondition="DIRTY_TRACKED_JSON",
               dirty_before_run=dirty, mutated_reported=reported,
               mutated_set_equals_dirty_set=exact)
        if not exact:
            rows[-1]["as_expected"] = False
            print(f"      | dirty={dirty}\n      | reported={reported}")
    else:
        record("R1", "the frozen set, untouched", 0, rc, out, "new=0 mutated=0",
               precondition="CLEAN_TRACKED_JSON")

    try:
        write_and_stage(NEW_UNBOUND, UNWITNESSED)
        rc, out = ratchet()
        record("R2", "NEW refused receipt outside every bound family (numeric claim, UNBOUND)",
               1, rc, out, NEW_UNBOUND.relative_to(REPO).as_posix())
    finally:
        unstage_and_remove(NEW_UNBOUND)

    try:
        write_and_stage(NEW_BOUND, UNWITNESSED)
        rc, out = ratchet()
        record("R3", "NEW unwitnessed NUMERICAL claim inside the bound family probe.v1",
               1, rc, out, NEW_BOUND.relative_to(REPO).as_posix())
    finally:
        unstage_and_remove(NEW_BOUND)

    sys.path.insert(0, str(REPO))
    from claimgate_plugin.legacy_unwitnessed_baseline import pass_path
    from claimgate_plugin.receipt_grammar import load_schema

    pp = pass_path(load_schema())
    try:
        write_and_stage(NEW_PASSING, PASSING)
        rc, out = ratchet()
        record("R4",
               "NEW receipt raising no obligation — DISCRIMINATION control: does the ratchet "
               "block on the grammar's disposition, or merely on the file being new?",
               0 if pp["exists"] else 1, rc, out,
               "new=0" if pp["exists"] else "PASS PATH: NONE",
               pass_path_exists=pp["exists"],
               discrimination="MEASURED" if pp["exists"] else "UNTESTED_NO_PASS_PATH",
               pass_path_detail=pp)
    finally:
        unstage_and_remove(NEW_PASSING)

    victim = a_frozen_parked_path()
    vpath = REPO / victim
    original = vpath.read_bytes()
    try:
        doc = json.loads(original)
        if isinstance(doc, dict):
            doc["_zz_ratchet_regression_edit"] = "one added field, still no witnessed provenance"
            mutated = (json.dumps(doc, indent=1) + "\n").encode()
        else:
            mutated = original + b"\n"
        vpath.write_bytes(mutated)
        rc, out = ratchet()
        record("R5", f"MUTATED frozen receipt still refused ({victim})", 1, rc, out, victim)
    finally:
        vpath.write_bytes(original)
        if hashlib.sha256(vpath.read_bytes()).hexdigest() != hashlib.sha256(original).hexdigest():
            print("run_legacy_ratchet_regression: FAIL — could not restore the mutated receipt",
                  file=sys.stderr)
            return 1

    baseline_bytes = BASELINE.read_bytes()
    try:
        doc = json.loads(baseline_bytes)
        doc["classifier"]["schema_sha256"] = "0" * 64
        BASELINE.write_text(json.dumps(doc, indent=1) + "\n")
        rc, out = ratchet()
        record("R6", "baseline frozen under a different classifier digest", 2, rc, out,
               "CLASSIFIER DRIFT")
    finally:
        BASELINE.write_bytes(baseline_bytes)

    after = status()
    clean = after == before
    if not clean:
        print("run_legacy_ratchet_regression: WORKING TREE / INDEX RESIDUE", file=sys.stderr)
        print(f"  before:\n{before}\n  after:\n{after}", file=sys.stderr)

    failed = [r["id"] for r in rows if not r["as_expected"]]
    print(f"\nrun_legacy_ratchet_regression: {len(rows) - len(failed)}/{len(rows)} as expected; "
          f"tree/index restored={clean}")
    out_doc = {
        "probe": "claimgate_legacy_ratchet_regression_v1",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "claim_ceiling": "measures the RATCHET's direction only — that a new or mutated refused "
                         "receipt fails and a grammar-passing one does not. It says nothing about "
                         "whether any receipt's science is verified, and the grammar admits no "
                         "witness procedure today.",
        "acceptance": "every case must measure the exit its schema-computed expectation names. R4 "
                      "is the discrimination control: while no pass path exists the expect-1 rows "
                      "are ALSO satisfied by a check that fails on any new tracked JSON, so R4 is "
                      "recorded as UNTESTED_NO_PASS_PATH rather than counted as enforcement.",
        "discrimination": next((r.get("discrimination") for r in rows if r["id"] == "R4"), None),
        "pass_path": pp,
        "index_touched": "R2/R3/R4 stage a file because git ls-files IS the committed set; each "
                         "unstages in a finally block and git status is re-compared",
        "tree_and_index_restored": clean,
        "as_expected": len(rows) - len(failed),
        "total": len(rows),
        "failed": failed,
        "results": rows,
    }
    d = REPO / "claimgate_plugin" / "results"
    d.mkdir(exist_ok=True)
    (d / "legacy_ratchet_regression_v1.json").write_text(json.dumps(out_doc, indent=1) + "\n")
    if failed or not clean:
        print(f"run_legacy_ratchet_regression: FAIL — {failed or 'index residue'}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
