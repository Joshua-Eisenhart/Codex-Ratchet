#!/usr/bin/env python3
"""Mechanical gate for queue item 1 of the Ratchet Runbook.

Enforces the runbook section 6 discipline on every projection row: one shared
root (constrained distinguishability), and every row MUST report what it
preserves, what it ERASES, at least one control that could kill it, and a
status label from the allowed set. A row that does not say what it erases or
carries no control is a false-separation risk -> fails.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REQUIRED = ["name", "view_type", "preserves", "erases", "weakest_carrier", "stronger_lifts", "controls", "status"]


def main():
    reg = json.load(open(os.path.join(HERE, "registry.json")))
    allowed = set(reg["allowed_status"])
    root = reg["root_object"]
    failures = []

    if root != "constrained distinguishability":
        failures.append(f"root_object is not 'constrained distinguishability': {root!r}")

    seen = set()
    for r in reg["rows"]:
        nm = r.get("name", "<unnamed>")
        if nm in seen:
            failures.append(f"{nm}: duplicate row")
        seen.add(nm)
        for k in REQUIRED:
            if k not in r or r[k] in (None, "", []):
                failures.append(f"{nm}: missing/empty required field '{k}'")
        if r.get("status") not in allowed:
            failures.append(f"{nm}: status {r.get('status')!r} not in allowed set")
        if not isinstance(r.get("controls"), list) or len(r.get("controls", [])) < 1:
            failures.append(f"{nm}: needs >= 1 control (a row with no control that could kill it is ornamental)")
        # erasure discipline: every projection MUST name what it erases
        if isinstance(r.get("erases"), str) and len(r["erases"].strip()) < 3:
            failures.append(f"{nm}: 'erases' is empty -- every quotient must report what it erases")

    report = {
        "registry_id": reg["registry_id"],
        "row_count": len(reg["rows"]),
        "all_rows_one_root": root == "constrained distinguishability",
        "well_formed": len(failures) == 0,
        "failures": failures,
        "status": "SCRATCH_DIAGNOSTIC",
        "note": "MAPPER pass only; forced-vs-installed and load-bearing-vs-ornamental adjudication is the fleet step, not asserted here.",
    }
    out = os.path.join(HERE, "registry_validation.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    if failures:
        print(f"\nREGISTRY GATE FAILED ({len(failures)} issue(s))", file=sys.stderr)
        sys.exit(1)
    print(f"\nREGISTRY GATE OK: {len(reg['rows'])} projections, one root, each reports erasure + control + status.")


if __name__ == "__main__":
    main()
