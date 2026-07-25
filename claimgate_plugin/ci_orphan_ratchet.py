#!/usr/bin/env python3
"""CI ORPHAN RATCHET — the historical orphan set may shrink, never grow.

An ORPHAN is a claim-bearing receipt with no durable gate-ledger record: nothing
distinguishes it from a receipt that never went near the gate. The measured
baseline is that essentially every receipt in this repo is one, so wiring the
detector's raw exit code into CI would paint the build red on a known baseline
and teach everyone to ignore it. Failing on a baseline enforces nothing.

FROZEN BY PATH AND DIGEST, NOT BY COUNT (corrected 2026-07-25).
    The first version compared a COUNT against orphan_receipts_max. A count is
    fungible: delete one historical orphan, add one brand-new ungated receipt,
    and the total is unchanged while a fresh unverified claim has just landed.
    The baseline now freezes the exact SET — every orphan's path and the sha256
    of its bytes — so the three cases are distinct and the bad two are closed:

      NEW ORPHAN    a path not in the frozen set -> an ungated receipt landed
      MUTATED       a frozen path whose bytes changed -> a grandfathered receipt
                    was edited while still carrying no gate record, so its
                    grandfathering no longer covers the content it now holds
      RESOLVED      a frozen path that is gone or now gated -> fine, and reported
                    so the baseline can be pruned deliberately

    Shrinking is the only allowed direction, and it is never automatic: pruning
    the set is a reviewed edit, exactly like lowering a ratchet ceiling.

The detector itself is not modified and not weakened.

Exit: 0 = within the frozen set | 1 = new or mutated orphan, or the detector
      could not be read | 2 = usage.
Nonzero is a policy/infrastructure disposition, never a scientific verdict.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASELINE = REPO / "claimgate_plugin" / "ci_orphan_baseline.json"

sys.path.insert(0, str(REPO))


def current_orphans() -> dict[str, str]:
    """{repo-relative path: sha256}. Imported, not stdout-scraped: a regex over
    the detector's prose would silently read zero orphans the day the wording
    changes, and that failure is OPEN."""
    from claimgate_plugin.orphan_receipt_detector import find_orphans
    from claimgate_plugin.tracked_set import tracked_files

    tracked = tracked_files(REPO)

    report = find_orphans(REPO)
    out: dict[str, str] = {}
    for entry in report["orphans"]:
        p = Path(entry)
        rel = (p.relative_to(REPO) if p.is_absolute() else p).as_posix()
        # TRACKED-ONLY: the first freeze took 2851 from the working tree while CI
        # measured 2202, producing 651 phantom "resolved" entries. A baseline must
        # describe the committed set.
        if rel not in tracked:
            continue
        try:
            out[rel] = hashlib.sha256((REPO / rel).read_bytes()).hexdigest()
        except OSError:
            out[rel] = "UNREADABLE"
    return out


def main(argv: list[str]) -> int:
    try:
        current = current_orphans()
    except Exception as exc:  # noqa: BLE001
        print(f"ci_orphan_ratchet: FAIL — the detector did not run ({exc!r}); failing "
              f"CLOSED rather than assuming zero orphans", file=sys.stderr)
        return 1

    if "--write-baseline" in argv:
        BASELINE.write_text(json.dumps({
            "_what": "The FROZEN historical orphan set: claim-bearing receipts carrying no "
                     "durable gate-ledger record. Path + sha256, never a count, so one "
                     "orphan cannot be silently swapped for another.",
            "_rule": "This set may only ever SHRINK, and only by a reviewed edit. Adding a "
                     "path here grandfathers an unverified claim — do that consciously or "
                     "not at all.",
            "_regenerate": "python3 claimgate_plugin/ci_orphan_ratchet.py --write-baseline",
            "count_at_freeze": len(current),
            "orphans": dict(sorted(current.items())),
        }, indent=1) + "\n")
        print(f"ci_orphan_ratchet: froze {len(current)} orphan(s) into {BASELINE.name}")
        return 0

    try:
        frozen = json.loads(BASELINE.read_bytes())["orphans"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ci_orphan_ratchet: usage — cannot read the frozen orphan set from "
              f"{BASELINE.name}: {exc}", file=sys.stderr)
        return 2

    new = sorted(set(current) - set(frozen))
    gone = sorted(set(frozen) - set(current))
    mutated = sorted(p for p in set(current) & set(frozen) if current[p] != frozen[p])

    print(f"ci_orphan_ratchet: orphans now={len(current)} frozen={len(frozen)} "
          f"new={len(new)} mutated={len(mutated)} resolved={len(gone)}")
    for p in gone[:20]:
        print(f"  RESOLVED {p} — gated or removed; prune it from the baseline")
    for p in new:
        print(f"  NEW ORPHAN {p}")
    for p in mutated:
        print(f"  MUTATED {p} (frozen {frozen[p][:12]} -> now {current[p][:12]})")

    if new:
        print(f"\nci_orphan_ratchet: FAIL — {len(new)} claim-bearing receipt(s) landed with no "
              f"durable gate-ledger record. Run them through "
              f"claimgate_plugin/hooks/post_receipt_gate.sh, which appends the chained line. "
              f"Do NOT add them to the frozen set to make this green.", file=sys.stderr)
        return 1
    if mutated:
        print(f"\nci_orphan_ratchet: FAIL — {len(mutated)} grandfathered orphan(s) were EDITED "
              f"while still ungated. Grandfathering covered the bytes that were measured, not "
              f"whatever they now hold. Gate them, or revert the edit.", file=sys.stderr)
        return 1
    print(f"ci_orphan_ratchet: within the frozen set. This is DEBT, not enforcement: "
          f"{len(current)} receipt(s) still have no durable gate-run record.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
