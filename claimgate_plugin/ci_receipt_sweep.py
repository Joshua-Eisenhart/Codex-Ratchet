#!/usr/bin/env python3
"""CI RECEIPT SWEEP — run one lean-tier checker over the claim-bearing receipt set.

WHY THIS EXISTS (server-side placement is the whole point). The local pre-commit
gate is skippable: `git commit --no-verify` bypasses it entirely, measured. Only
.github/workflows/ runs where the committer has no --no-verify. So the lean tier
(intake_supervisor + recompute_veto) has to fire from CI, not only from the hook.

This script is the SHARED receipt-set definition so the intake job, the recompute
job, and the legacy ratchet job cannot drift apart into three different ideas of
what a receipt is.

CLAIM-BEARING = the UNION of the two definitions already live in this repo:
  (a) parses as a JSON object with a top-level "classification"
      -- the rule claimgate_plugin/orphan_receipt_detector.py uses
  (b) filename contains "receipt", or the body carries "claim_under_test" or
      "claim_ceiling", or it declares a schema naming "receipt"
      -- the rule .github/workflows/three-engine-seal.yml already used
Union, not intersection: neither job may lose coverage relative to today.

HOSTILE FIXTURES ARE INPUTS, NOT EXCLUSIONS (corrected 2026-07-25). The first
version skipped any path under a prefix list. That was the CHEAPEST bypass in the
whole layer and needed no edit to any checker: move a poisoned real receipt under
claimgate_plugin/fixtures/ and the sweep never looks at it. A path prefix cannot
distinguish "poison we wrote on purpose" from "poison someone parked here".

Every hostile fixture is now an EXPLICIT REGRESSION INPUT pinned by DIGEST in
claimgate_plugin/fixtures/sweep_fixture_manifest.json: path -> sha256 + the exit
code that checker must return. The sweep runs them and asserts the recorded exit.
Three ways to fail, all closed:
  - a pinned fixture stops producing its recorded exit  -> the checker regressed
  - a pinned fixture's bytes no longer match its digest -> the fixture was edited
  - an UNPINNED file appears under a fixture root       -> laundering; swept as a
    normal receipt, so parking poison there now makes the job RED, not quiet.

Exit: 0 = failures <= budget and every pinned fixture held | 1 = over budget, a
      fixture regressed//was edited, or the sweep found no receipts | 2 = usage.
Nonzero is a policy/infrastructure disposition, never a scientific verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Roots that MAY hold poison-by-design fixtures. Being under one of these buys a
# file NOTHING on its own -- it only means an entry in the digest-pinned manifest
# is permitted here. Anything under a fixture root that is NOT pinned is swept as
# an ordinary receipt.
FIXTURE_ROOTS = (
    "claimgate_plugin/fixtures/",
    "claimgate_plugin/rf_fixtures/",
    "system_v8/harness_patch/results/fixtures/",
    "claimgate_plugin/stress/",
)
FIXTURE_MANIFEST = REPO / "claimgate_plugin" / "fixtures" / "sweep_fixture_manifest.json"


def load_fixture_manifest() -> dict[str, dict]:
    """path -> {sha256, expect_exit: {checker_name: code}}. Absent manifest is
    FAIL-CLOSED at the call site, never an empty allowlist."""
    entries = json.loads(FIXTURE_MANIFEST.read_bytes())["fixtures"]
    return {e["path"]: e for e in entries}

# Live surfaces per CLAUDE.md ("the live surfaces are system_v8/, MODEL_DOSSIER/,
# ROOT/, and current receipts"); system_v4..v7 are historical archives read as a
# mine. --scope live is these roots; --scope all is the whole repo.
# MODEL_DOSSIER and ROOT were MISSING here while CLAUDE.md named both as live, so
# a receipt written to the current-era docs home was never swept at live scope.
LIVE_ROOTS = ("system_v8", "claimgate_plugin", "ratchet_contract",
              "MODEL_DOSSIER", "ROOT")

SKIP_DIR_PARTS = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def under_fixture_root(rel: str) -> bool:
    return rel.startswith(FIXTURE_ROOTS)


def _keys_anywhere(obj, out=None):
    out = set() if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(k)
            _keys_anywhere(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _keys_anywhere(v, out)
    return out


def claim_bearing(path: Path) -> bool:
    """Raw-byte markers are a FAST PATH ONLY, never the decision.

    The byte scan alone missed `{"claim\\u005funder\\u005ftest": ...}`: valid JSON
    that decodes to the real key, so the file carries a claim while no literal
    substring matches. Anything that parses is therefore also judged on its PARSED
    keys, at any depth, and a file that does not parse is treated as claim-bearing
    so the checkers get to say why rather than the sweep dropping it silently.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return False
    low = raw.lower()
    if ("receipt" in path.name.lower()
            or b'"claim_under_test"' in low
            or b'"claim_ceiling"' in low
            or (b'"schema"' in low and b"receipt" in low)):
        return True
    try:
        obj = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        # Unparseable JSON is not evidence of innocence. Hand it to the checker,
        # which fails closed with a reason; dropping it here fails open.
        return True
    if isinstance(obj, dict) and "classification" in obj:
        return True
    return bool(_keys_anywhere(obj)
                & {"claim_under_test", "claim_ceiling", "classification"})


def discover(scope: str, pinned: dict[str, dict]) -> list[Path]:
    """Ordinary receipts to sweep. A file under a fixture root is skipped ONLY if
    it is pinned in the manifest; unpinned files there are swept normally, so
    parking poison in a fixture directory no longer hides it."""
    roots = [REPO / r for r in LIVE_ROOTS] if scope == "live" else [REPO]
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            if not path.is_file():
                continue
            if SKIP_DIR_PARTS & set(path.parts):
                continue
            rel = path.relative_to(REPO).as_posix()
            if rel in pinned:
                continue
            if claim_bearing(path):
                seen.add(path)
    return sorted(seen)


# Isolated-module trampoline. `-I` alone cannot be combined with `-m` here because
# -I implies -P, so neither cwd nor the script dir is on sys.path and the package
# is unimportable; and PYTHONPATH is ignored by design (-I implies -E), which is
# the point -- no environment variable may steer resolution. So the parent injects
# the repo root it computed itself, as a literal, and nothing else.
#
# APPEND, never insert(0). Prepending the repo root puts it AHEAD of the stdlib,
# so a file at the REPO ROOT named json.py or hashlib.py shadows the real module
# and the whole defence is undone one directory up. Appended, the stdlib wins
# every top-level name while claimgate_plugin still resolves, because nothing
# else provides that name. Measured against a NaN-poisoned receipt with a
# repo-root json.py planted: insert(0) admits it (exit 0), append rejects it (1).
_TRAMPOLINE = (
    "import sys, runpy\n"
    "sys.path.append({root!r})\n"
    "sys.argv = [{name!r}, sys.argv[1]]\n"
    "runpy.run_module({mod!r}, run_name='__main__', alter_sys=False)\n"
)


def _checker_argv(checker: Path, target: str) -> list[str]:
    """Run the checker as an ISOLATED MODULE, never as a bare script path.

    `[sys.executable, str(checker), ...]` puts the checker's OWN directory on
    sys.path[0], so an attacker-authored claimgate_plugin/hashlib.py shadows the
    stdlib and forges every digest the checker computes. Importing the same file
    as claimgate_plugin.<name> with only the REPO ROOT on sys.path makes that file
    a submodule (claimgate_plugin.hashlib) instead of top-level hashlib, so it
    cannot shadow. -I additionally drops PYTHONPATH and user site-packages.
    """
    code = _TRAMPOLINE.format(root=str(REPO), name=checker.name,
                              mod=f"claimgate_plugin.{checker.stem}")
    return [sys.executable, "-I", "-c", code, target]


def run_one(checker: Path, path: Path) -> tuple[Path, int, str]:
    proc = subprocess.run(
        _checker_argv(checker, str(path)),
        capture_output=True, text=True, cwd=str(REPO),
    )
    tail = (proc.stderr or proc.stdout or "").strip().splitlines()
    return path, proc.returncode, tail[-1] if tail else ""


def check_pinned_fixtures(checker: Path, pinned: dict[str, dict]) -> list[str]:
    """Hostile fixtures as REGRESSION INPUTS. Each pinned fixture must still hash
    to its recorded digest AND still produce its recorded exit for this checker.
    Returns failure lines; empty means every pin held."""
    name, fails = checker.stem, []
    for rel, entry in sorted(pinned.items()):
        p = REPO / rel
        if not p.exists():
            fails.append(f"{rel}: PINNED FIXTURE MISSING — a regression input was deleted")
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != entry["sha256"]:
            fails.append(f"{rel}: DIGEST MISMATCH — fixture edited "
                         f"(pinned {entry['sha256'][:12]}, found {got[:12]})")
            continue
        want = entry.get("expect_exit", {}).get(name)
        if want is None:
            continue          # this fixture makes no claim about this checker
        _, got_exit, msg = run_one(checker, p)
        if got_exit != want:
            fails.append(f"{rel}: {name} exit {got_exit}, recorded {want} — "
                         f"the checker REGRESSED on a known-hostile input ({msg[:80]})")
    return fails


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checker", required=True,
                    help="repo-relative checker script; run as <python> <checker> <receipt>")
    ap.add_argument("--scope", choices=("live", "all"), default="live")
    ap.add_argument("--max-failures", type=int, default=0,
                    help="COUNT budget. DEPRECATED and fungible — see --frozen-failures. "
                         "0 = zero tolerance. Retained only for callers not yet migrated.")
    ap.add_argument("--frozen-failures", metavar="JSON",
                    help="Path+digest freeze of known-failing receipts, replacing the "
                         "fungible --max-failures count. A failure outside the frozen set, "
                         "or a frozen receipt whose bytes changed, fails the job.")
    ap.add_argument("--write-frozen-failures", metavar="JSON",
                    help="Record the current failure set as a frozen baseline (reviewed act).")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args(argv)

    checker = REPO / args.checker
    if not checker.exists():
        print(f"ci_receipt_sweep: usage — checker absent: {args.checker}", file=sys.stderr)
        return 2
    if args.max_failures < 0:
        print("ci_receipt_sweep: usage — --max-failures must be >= 0", file=sys.stderr)
        return 2

    # Absent/unreadable manifest FAILS CLOSED. An empty allowlist would silently
    # turn every pinned fixture into an ordinary receipt and paint the job red for
    # the wrong reason; a missing manifest is infrastructure breakage, not a pass.
    try:
        pinned = load_fixture_manifest()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ci_receipt_sweep: FAIL — cannot read the pinned fixture manifest "
              f"{FIXTURE_MANIFEST.name} ({exc}); failing CLOSED", file=sys.stderr)
        return 1

    fixture_fails = check_pinned_fixtures(checker, pinned)

    receipts = discover(args.scope, pinned)
    if not receipts:
        print(f"ci_receipt_sweep: FAIL — scope {args.scope} found no claim-bearing receipts; "
              f"an empty sweep is a broken sweep, not a pass", file=sys.stderr)
        return 1
    # Poison parked under a fixture root but never pinned is LAUNDERING. It stays
    # in the ordinary sweep (above), and is named here so it cannot pass quietly.
    stray = [p.relative_to(REPO).as_posix() for p in receipts
             if under_fixture_root(p.relative_to(REPO).as_posix())]

    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for row in pool.map(lambda p: run_one(checker, p), receipts):
            results.append(row)

    failures = [r for r in results if r[1] != 0]
    print(f"ci_receipt_sweep: checker={args.checker} scope={args.scope} "
          f"swept={len(receipts)} failed={len(failures)} budget={args.max_failures}")
    for path, code, line in failures:
        print(f"  FAIL exit {code}  {path.relative_to(REPO).as_posix()}")
        if line:
            print(f"       {line}")
    print(f"  pinned hostile fixtures: {len(pinned)} (digest + expected exit enforced)")
    for line in fixture_fails:
        print(f"  FIXTURE-REGRESSION {line}")
    for rel in stray:
        print(f"  UNPINNED-UNDER-FIXTURE-ROOT {rel} — swept as an ordinary receipt")

    # A fixture regression is never inside the legacy debt budget: the budget
    # records known-bad RECEIPTS, while this says a CHECKER stopped catching a
    # known attack, or a regression input was edited or deleted.
    if fixture_fails:
        print(f"\nci_receipt_sweep: FAIL — {len(fixture_fails)} pinned hostile fixture(s) "
              f"regressed. These are mandatory regression inputs and are NOT covered by "
              f"--max-failures. Fix the checker; do not re-pin to whatever it now returns.",
              file=sys.stderr)
        return 1

    # ---------------------------------------------------------------- E9 REPAIR
    # A COUNT budget is fungible in exactly the way the orphan ceiling was: repair
    # one old failing receipt and a free slot opens for one new poisoned one, with
    # CI still green. The frozen set removes the slot — identity, not arithmetic.
    cur_fail = {p.relative_to(REPO).as_posix():
                {"exit": code, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                 "msg": line[:200]}
                for p, code, line in failures}
    if args.write_frozen_failures:
        # TRACKED-ONLY, matching the other freeze tools. discover() deliberately
        # sweeps everything present so a developer's uncommitted receipt is still
        # checked, but a BASELINE must describe what CI will see. Freezing the
        # sweep's raw result would bake untracked working-tree files into the set
        # and then report them as phantom failures in CI.
        sys.path.insert(0, str(REPO))
        from claimgate_plugin.tracked_set import tracked_files
        tracked = tracked_files(REPO)
        dropped = sorted(set(cur_fail) - tracked)
        cur_fail = {k: v for k, v in cur_fail.items() if k in tracked}
        for d in dropped:
            print(f"  not frozen (untracked): {d}")
        Path(args.write_frozen_failures).write_text(json.dumps({
            "_what": f"FROZEN failure set for {args.checker} at scope={args.scope}: every "
                     f"known-failing receipt by path + sha256 + exit. Replaces the fungible "
                     f"--max-failures count.",
            "_rule": "May only ever SHRINK, and only by a reviewed edit. A NEW failing path, "
                     "or a frozen path whose bytes changed, fails the job — repairing one old "
                     "failure no longer buys a slot for a new one.",
            "checker": args.checker, "scope": args.scope,
            "count_at_freeze": len(cur_fail), "failures": dict(sorted(cur_fail.items())),
        }, indent=1) + "\n")
        print(f"\nci_receipt_sweep: froze {len(cur_fail)} failure(s) into "
              f"{args.write_frozen_failures}")
        return 0

    if args.frozen_failures:
        try:
            frozen_f = json.loads(Path(args.frozen_failures).read_bytes())["failures"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f"ci_receipt_sweep: FAIL — cannot read the frozen failure set "
                  f"{args.frozen_failures} ({exc}); failing CLOSED", file=sys.stderr)
            return 1
        new_f = sorted(set(cur_fail) - set(frozen_f))
        gone_f = sorted(set(frozen_f) - set(cur_fail))
        mutated_f = sorted(p for p in set(cur_fail) & set(frozen_f)
                           if cur_fail[p]["sha256"] != frozen_f[p].get("sha256"))
        print(f"  frozen-failure set: now={len(cur_fail)} frozen={len(frozen_f)} "
              f"new={len(new_f)} mutated={len(mutated_f)} repaired={len(gone_f)}")
        for p in gone_f[:20]:
            print(f"  REPAIRED {p} — prune it from the frozen set")
        for p in new_f:
            print(f"  NEW FAILURE {p} — {cur_fail[p]['msg'][:110]}")
        for p in mutated_f:
            print(f"  MUTATED {p} — a known-failing receipt was edited while still failing")
        if new_f or mutated_f:
            print(f"\nci_receipt_sweep: FAIL — {len(new_f)} new and {len(mutated_f)} mutated "
                  f"failing receipt(s) outside the frozen set. Do not re-freeze to make this "
                  f"green; that erases the finding.", file=sys.stderr)
            return 1
        print("ci_receipt_sweep: within the frozen failure set — DEBT, not a pass.")
        return 0

    if len(failures) > args.max_failures:
        print(f"\nci_receipt_sweep: FAIL — {len(failures)} failure(s) exceeds budget "
              f"{args.max_failures}. Do not raise the budget to make this green; fix the "
              f"receipt or record the exclusion consciously.", file=sys.stderr)
        return 1
    if failures:
        print(f"\nci_receipt_sweep: within recorded ratchet ceiling "
              f"({len(failures)}/{args.max_failures}) — this is DEBT, not a pass. "
              f"Lower the ceiling as receipts are fixed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
