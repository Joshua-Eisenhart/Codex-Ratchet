#!/usr/bin/env python3
"""LEGACY UNWITNESSED RATCHET — the historical unwitnessed set may shrink, never grow.

WHY THIS EXISTS. The typed receipt grammar (claimgate_plugin/receipt_grammar.py +
claimgate_plugin/receipt_schema.json) refuses everything it cannot resolve to an
evaluator-owned role, and it has NO admitted witness procedure today, so on the
committed tree it refuses essentially everything. Measured 2026-07-25 over
`git ls-files '*.json'`, 3856 tracked files:

    PARK    3843    3832 of them UNBOUND — no family covers the path yet
    BLOCK      13    6 adversarial fixtures + 7 tracked files that are not JSON
    pass        0    by construction: the only witness procedure in the schema is
                     engine_witness_v0, status `purgatory`, and a non-admitted
                     procedure cannot discharge an obligation

Wiring that raw exit code into CI would paint the build red on a known baseline
and teach everyone to ignore it. Failing on a baseline enforces nothing. This
ratchet makes the historical set QUIET AND FROZEN so the grammar can enter CI
while the only thing it actually enforces is DIRECTION.

    PARKED_LEGACY_UNWITNESSED   a frozen path whose bytes are unchanged. Not
                                invalid science, not a passing baseline, not a
                                false positive: an unmigrated or unwitnessed
                                receipt, carried as named debt.
    FROZEN_LEGACY_BLOCKING      a frozen path the grammar DECIDES against. Kept
                                as a SEPARATE set, never folded into the parked
                                count. Six are poison-by-design fixtures whose
                                BLOCK is the wanted behaviour; seven are tracked
                                files that do not parse as JSON. Lumping the two
                                dispositions would hide both.
    BLOCK (this ratchet's own)  a path not in the frozen set, or a frozen path
                                whose bytes changed while still not passing.

FROZEN BY PATH AND DIGEST, NOT BY COUNT — the same correction that
claimgate_plugin/ci_orphan_ratchet.py records. A count is fungible: delete one
historical receipt, add one brand-new unwitnessed claim, and the total is
unchanged while a fresh unverified claim has just landed.

THE CLASSIFIER IS PINNED TOO, which is the one thing this file adds to the
pattern it copies. A frozen SET is only meaningful relative to the classifier
that produced it: edit the schema, and the same 3856 files partition differently
while the baseline still claims to describe them. So the baseline records the
sha256 of receipt_grammar.py and of receipt_schema.json, and a mismatch is exit 2
— re-freeze required — instead of a silently stale green.

FREEZE FROM THE COMMITTED BYTES, CHECK THE WORKING TREE. Every baseline in this
layer was first frozen from the working tree and every one then failed in CI,
which checks out committed files only (see claimgate_plugin/tracked_set.py: 651
phantom "resolved" entries on the first push, then 327 phantom NEW ORPHANs from a
temp clone that re-applied .gitignore). Freezing reads `git cat-file blob
HEAD:<path>`, so a dirty tree cannot bake an uncommitted digest into the
baseline, and no temp clone is involved. Checking reads what is on disk, so a
developer's edit to a frozen receipt is caught BEFORE it is committed. In a clean
tree the two agree; where they differ the check is right to be loud.

ONE NAMED EXCLUSION, with the alternative verifier named:
claimgate_plugin/results/gate_ledger.head.json is append-only runtime state
rewritten by every gate run, and its integrity is established by content, not by
bytes — orphan_receipt_detector.verify_chain re-derives its count and
last_line_sha256 from the ledger it anchors. Byte-freezing it here would fire on
every legitimate gate run and enforce nothing. The exclusion is printed on every
run so it can never be an invisible hole, and it is a NAME, not a path glob: a
new receipt cannot be laundered by being dropped near it.

Exit: 0 within the frozen set | 1 new or mutated, or the classifier did not run
      | 2 usage, or the baseline was frozen under a different classifier.
Nonzero is a policy/infrastructure disposition, never a scientific verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASELINE = REPO / "claimgate_plugin" / "legacy_unwitnessed_baseline.json"

sys.path.insert(0, str(REPO))

# Append-only runtime state whose integrity is checked by the ledger chain
# verifier, not by its bytes. A NAME, not a shape: see the module docstring.
LEDGER_ANCHORS = {"claimgate_plugin/results/gate_ledger.head.json"}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _committed_bytes(rel: str) -> bytes | None:
    """The bytes CI will see. None when the path is not in HEAD (newly staged)."""
    p = subprocess.run(["git", "-C", str(REPO), "cat-file", "blob", f"HEAD:{rel}"],
                       capture_output=True)
    return p.stdout if p.returncode == 0 else None


def classifier_identity(schema_path: Path) -> dict:
    """A frozen set describes the world as ONE classifier saw it. Pin both halves."""
    from claimgate_plugin import receipt_grammar

    module = Path(receipt_grammar.__file__).resolve()
    schema = json.loads(schema_path.read_bytes())
    return {
        "module": module.relative_to(REPO).as_posix(),
        "module_sha256": _sha256(module.read_bytes()),
        "schema": schema_path.relative_to(REPO).as_posix(),
        "schema_sha256": _sha256(schema_path.read_bytes()),
        "grammar_id": schema.get("grammar_id"),
    }


def pass_path(schema: dict) -> dict:
    """Is ANY receipt able to pass this grammar today? COMPUTED from the schema,
    because the answer decides what a green run of this ratchet means.

    The grammar has exactly two doors, and both are currently shut:

      an obligation discharged by a witness procedure whose status is `admitted`
        — engine_witness_v0 is `purgatory`, smt_unsat_core_recheck is `absent`
      a family declaring `x-asserts-nothing`, which lets a receipt that measures
        nothing pass without witnessing anything — no family declares it

    With both shut, EVERY new tracked JSON is refused, so "new -> BLOCK" cannot be
    distinguished from "anything new blocks". That makes this ratchet a FREEZE
    rather than a FILTER, and a freeze must say so out loud: a check whose block
    arm is indiscriminate teaches people to route around it. Reported on every
    run, and re-computed rather than remembered, so the day a witness procedure is
    admitted the message changes by itself.
    """
    procs = {k: v.get("status") for k, v in (schema.get("witness_procedures") or {}).items()
             if isinstance(v, dict)}
    admitted = sorted(k for k, s in procs.items() if s == "admitted")
    asserts_nothing = sorted(f for f, fam in (schema.get("families") or {}).items()
                             if isinstance(fam, dict) and fam.get("x-asserts-nothing"))
    return {"exists": bool(admitted or asserts_nothing),
            "admitted_witness_procedures": admitted,
            "witness_procedure_status": procs,
            "families_declaring_x-asserts-nothing": asserts_nothing}


def dispositions(source: str) -> tuple[dict[str, dict], dict[str, int]]:
    """{rel: {sha256, disposition, why}} for every tracked JSON the grammar does
    NOT pass, plus a reason-code histogram.

    source="committed"  bytes from HEAD — what CI sees; used for freezing
    source="worktree"   bytes on disk — used for checking

    Imported, not stdout-scraped: a regex over the grammar's prose would silently
    read zero refusals the day the wording changes, and that failure is OPEN.
    """
    from claimgate_plugin.receipt_grammar import evaluate, load_schema
    from claimgate_plugin.tracked_set import tracked_files

    schema = load_schema()
    out: dict[str, dict] = {}
    hist: dict[str, int] = {}

    def bump(code: str) -> None:
        hist[code] = hist.get(code, 0) + 1

    for rel in sorted(tracked_files(REPO)):
        if rel in LEDGER_ANCHORS:
            continue
        if source == "committed":
            raw = _committed_bytes(rel)
            if raw is None:                     # staged but not yet committed
                continue
        else:
            path = REPO / rel
            if not path.exists():               # deleted locally: carries no claim
                continue
            try:
                raw = path.read_bytes()
            except OSError as exc:
                out[rel] = {"sha256": "UNREADABLE", "disposition": "BLOCK",
                            "why": f"UNREADABLE_FILE:{exc.errno}"}
                bump("UNREADABLE_FILE")
                continue

        digest = _sha256(raw)
        try:
            doc = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            # receipt_grammar.py's own entry point BLOCKs on an unparseable
            # artifact and says so ("cannot evaluate; failing CLOSED"). Recording
            # it as PARK here would be a softer disposition than the grammar's.
            out[rel] = {"sha256": digest, "disposition": "BLOCK", "why": "UNPARSEABLE_JSON"}
            bump("UNPARSEABLE_JSON")
            continue
        try:
            code, label, msg, det = evaluate(doc, REPO / rel, schema)
        except Exception as exc:  # noqa: BLE001
            out[rel] = {"sha256": digest, "disposition": "BLOCK",
                        "why": f"EVALUATOR_ERROR:{type(exc).__name__}"}
            bump("EVALUATOR_ERROR")
            continue

        if code == 0:
            continue                            # passes the grammar: not debt

        codes = det.get("reason_codes") or {}
        if not codes and "no evaluator-owned binding" in msg:
            codes = {"UNBOUND": 1}
        why = ",".join(sorted(codes)[:4]) or label
        out[rel] = {"sha256": digest, "disposition": "BLOCK" if code == 1 else "PARK",
                    "why": why}
        for c in codes or {label: 1}:
            bump(c)
    return out, hist


def _write_baseline(current: dict[str, dict], hist: dict[str, int], ident: dict) -> None:
    parked = {k: v for k, v in current.items() if v["disposition"] == "PARK"}
    blocking = {k: v for k, v in current.items() if v["disposition"] == "BLOCK"}
    BASELINE.write_text(json.dumps({
        "_what": "The FROZEN historical set the typed receipt grammar refuses: every tracked "
                 "JSON path it does not pass, with the sha256 of its COMMITTED bytes and the "
                 "reason codes measured at freeze time. Path + digest, never a count, so one "
                 "unwitnessed receipt cannot be silently swapped for another.",
        "_rule": "This set may only ever SHRINK, and only by a reviewed edit. Adding a path here "
                 "grandfathers an unwitnessed claim — do that consciously or not at all. "
                 "Re-running the freeze to make CI green is the same mistake as raising a "
                 "ratchet ceiling.",
        "_two_sets_not_one": "parked = PARKED_LEGACY_UNWITNESSED (unmigrated or unwitnessed debt). "
                             "blocking = FROZEN_LEGACY_BLOCKING (the grammar DECIDES against these "
                             "bytes). They are counted separately because one is pending evidence "
                             "and the other is a decided refusal, and a single number would hide "
                             "both. Most of `blocking` is poison-by-design fixtures, pinned by "
                             "digest in claimgate_plugin/fixtures/sweep_fixture_manifest.json, "
                             "plus tracked files that are not parseable JSON.",
        "_not_a_pass": "Nothing in this file is verified science. A frozen entry means only that "
                       "these exact bytes were already here when the grammar landed.",
        "_classifier_pin": "A frozen SET is meaningful only relative to the classifier that "
                           "produced it. Both digests below are re-checked on every run; a "
                           "mismatch is exit 2, re-freeze required, never a stale green.",
        "_frozen_from": "git cat-file blob HEAD:<path> — the COMMITTED bytes, which is all CI can "
                        "see. Never the working tree, and never a temp clone: both produced wrong "
                        "baselines earlier in this work (claimgate_plugin/tracked_set.py).",
        "_excluded_by_name": sorted(LEDGER_ANCHORS),
        "_excluded_why": "append-only runtime state whose integrity is established by content "
                         "(orphan_receipt_detector.verify_chain re-derives count and "
                         "last_line_sha256 from the ledger it anchors), not by its bytes",
        "_regenerate": "python3 claimgate_plugin/legacy_unwitnessed_baseline.py --write-baseline",
        "classifier": ident,
        "count_at_freeze": {"parked": len(parked), "blocking": len(blocking)},
        "reason_codes_at_freeze": dict(sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))),
        "parked": dict(sorted(parked.items())),
        "blocking": dict(sorted(blocking.items())),
    }, indent=1) + "\n")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write-baseline", action="store_true",
                    help="freeze the current refused set from the COMMITTED bytes")
    ap.add_argument("--max-resolved", type=int, default=20,
                    help="resolved entries to print (0 = all)")
    args = ap.parse_args(argv)

    from claimgate_plugin.receipt_grammar import SCHEMA_PATH, load_schema

    try:
        ident = classifier_identity(SCHEMA_PATH)
        pp = pass_path(load_schema())
        current, hist = dispositions("committed" if args.write_baseline else "worktree")
    except Exception as exc:  # noqa: BLE001
        print(f"legacy_unwitnessed_baseline: FAIL — the typed grammar did not run ({exc!r}); "
              f"failing CLOSED rather than assuming an empty refused set", file=sys.stderr)
        return 1

    if args.write_baseline:
        _write_baseline(current, hist, ident)
        p = sum(1 for v in current.values() if v["disposition"] == "PARK")
        b = len(current) - p
        print(f"legacy_unwitnessed_baseline: froze {p} parked + {b} blocking path(s) from the "
              f"COMMITTED bytes into {BASELINE.name}")
        print(f"  classifier {ident['module']}@{ident['module_sha256'][:12]} "
              f"schema {ident['schema']}@{ident['schema_sha256'][:12]}")
        return 0

    try:
        doc = json.loads(BASELINE.read_bytes())
        frozen = dict(doc["parked"])
        frozen.update(doc["blocking"])
        frozen_ident = doc["classifier"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"legacy_unwitnessed_baseline: usage — cannot read the frozen set from "
              f"{BASELINE.name}: {exc}", file=sys.stderr)
        return 2

    drift = [k for k in ("module_sha256", "schema_sha256")
             if frozen_ident.get(k) != ident.get(k)]
    if drift:
        for k in drift:
            print(f"  CLASSIFIER DRIFT {k}: frozen {str(frozen_ident.get(k))[:12]} -> now "
                  f"{str(ident.get(k))[:12]}")
        print(f"\nlegacy_unwitnessed_baseline: usage — the frozen set was measured under a "
              f"DIFFERENT classifier ({', '.join(drift)}). The same tracked files partition "
              f"differently under a changed grammar, so this baseline no longer describes them. "
              f"Re-measure: python3 claimgate_plugin/legacy_unwitnessed_baseline.py "
              f"--write-baseline", file=sys.stderr)
        return 2

    new = sorted(set(current) - set(frozen))
    gone = sorted(set(frozen) - set(current))
    shared = set(current) & set(frozen)
    mutated = sorted(p for p in shared if current[p]["sha256"] != frozen[p]["sha256"])
    worsened = sorted(p for p in shared
                      if current[p]["sha256"] == frozen[p]["sha256"]
                      and current[p]["disposition"] != frozen[p]["disposition"])

    parked_now = sum(1 for v in current.values() if v["disposition"] == "PARK")
    blocking_now = len(current) - parked_now
    print(f"legacy_unwitnessed_baseline: refused now={len(current)} "
          f"(parked={parked_now} blocking={blocking_now}) frozen={len(frozen)} "
          f"new={len(new)} mutated={len(mutated)} resolved={len(gone)}")
    print(f"  classifier {ident['module']}@{ident['module_sha256'][:12]} "
          f"schema {ident['schema']}@{ident['schema_sha256'][:12]} "
          f"grammar_id={ident['grammar_id']}")
    print(f"  excluded by name (integrity checked by the ledger chain verifier, not by bytes): "
          f"{sorted(LEDGER_ANCHORS)}")
    if pp["exists"]:
        print(f"  pass path OPEN — admitted witness procedure(s) {pp['admitted_witness_procedures']}, "
              f"family/families asserting nothing {pp['families_declaring_x-asserts-nothing']}. "
              f"A new receipt that satisfies the grammar does NOT fail this ratchet.")
    else:
        print(f"  PASS PATH: NONE. witness procedures {pp['witness_procedure_status']}, no family "
              f"declares x-asserts-nothing. So EVERY new tracked JSON is refused and this ratchet "
              f"is currently a FREEZE, not a filter: its block arm cannot distinguish an "
              f"unwitnessed claim from any other new file. Do not read a green run as evidence "
              f"that new claims are being filtered.")

    shown = gone if args.max_resolved == 0 else gone[:args.max_resolved]
    for p in shown:
        state = "now passes the grammar" if (REPO / p).exists() else "removed from the tree"
        print(f"  RESOLVED {p} — {state}; prune it from the baseline")
    if len(gone) > len(shown):
        print(f"  ... and {len(gone) - len(shown)} more resolved (--max-resolved 0 for all)")
    for p in new:
        print(f"  NEW {current[p]['disposition']} {p} [{current[p]['why']}]")
    for p in mutated:
        print(f"  MUTATED {p} (frozen {frozen[p]['sha256'][:12]} -> now "
              f"{current[p]['sha256'][:12]}) [{current[p]['why']}]")
    for p in worsened:
        print(f"  DISPOSITION DRIFT {p}: {frozen[p]['disposition']} -> "
              f"{current[p]['disposition']} on IDENTICAL bytes")

    if worsened:
        print(f"\nlegacy_unwitnessed_baseline: usage — {len(worsened)} path(s) changed disposition "
              f"on identical bytes while both classifier digests matched. That is not possible for "
              f"a deterministic grammar, so the classifier pin is not covering everything the "
              f"verdict depends on. Do not re-freeze past this; find the input that is not "
              f"pinned.", file=sys.stderr)
        return 2
    if new:
        print(f"\nlegacy_unwitnessed_baseline: FAIL — {len(new)} tracked receipt(s) the typed "
              f"grammar refuses are NOT in the frozen set. A new unwitnessed numerical claim is "
              f"exactly what this ratchet exists to stop. Give it witnessed provenance the grammar "
              f"can re-check, or migrate its family in "
              f"claimgate_plugin/receipt_schema.json. Do NOT add it to the frozen set to make this "
              f"green.", file=sys.stderr)
        return 1
    if mutated:
        print(f"\nlegacy_unwitnessed_baseline: FAIL — {len(mutated)} grandfathered receipt(s) were "
              f"EDITED and are still refused by the grammar. Grandfathering covered the bytes that "
              f"were measured, not whatever they now hold. Fix the receipt so the grammar passes "
              f"it, or revert the edit.", file=sys.stderr)
        return 1
    print(f"legacy_unwitnessed_baseline: within the frozen set. This is DEBT, not enforcement: "
          f"{parked_now} receipt(s) PARKED_LEGACY_UNWITNESSED and {blocking_now} "
          f"FROZEN_LEGACY_BLOCKING. No witness procedure is admitted in "
          f"{ident['schema']}, so no numeric receipt has a pass path today.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
