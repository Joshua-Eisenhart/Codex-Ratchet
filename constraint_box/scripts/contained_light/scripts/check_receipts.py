#!/usr/bin/env python3
"""Shape-check the contained Light receipts after verify."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    root = Path(argv[1])
    seed_check = json.loads((root / "SEED_CHECK.json").read_text(encoding="utf-8"))
    seed = json.loads((root / "seed.json").read_text(encoding="utf-8"))
    collapsed = json.loads((root / "seed_collapsed.json").read_text(encoding="utf-8"))
    feas = json.loads((root / "feasibility.json").read_text(encoding="utf-8"))
    quotient = json.loads((root / "quotient.json").read_text(encoding="utf-8"))
    unbound = json.loads((root / "quotient_unbound.json").read_text(encoding="utf-8"))
    surface = json.loads((root / "surface.json").read_text(encoding="utf-8"))
    if seed_check.get("disposition") != "ADMIT":
        raise SystemExit(f"seed-check {seed_check.get('disposition')} {seed_check.get('refuses')}")
    if seed.get("status") != "PASS":
        raise SystemExit(f"seed status {seed.get('status')}")
    if seed.get("operation") != "finite_time_first_seed_validation.v1":
        raise SystemExit("seed operation mismatch")
    if seed.get("checks", {}).get("capacity_bits_recomputed") != [1.0, 2.0, 3.0]:
        raise SystemExit("seed capacity recompute mismatch")
    if collapsed.get("status") != "REFUSE":
        raise SystemExit("collapsed seed did not refuse")
    if "REFUSE_ORDER_GAP_COLLAPSED" not in str(collapsed.get("reason")):
        raise SystemExit("collapsed reason mismatch")
    if feas.get("status") != "BOUNDED_SAT":
        raise SystemExit(f"feasibility status {feas.get('status')}")
    if feas.get("operation") != "finite_probe_assignment_feasibility.v1":
        raise SystemExit("feasibility operation mismatch")
    if feas.get("claim_ceiling") != "exists":
        raise SystemExit("feasibility ceiling mismatch")
    if feas.get("witness_kind") != "solver_chosen":
        raise SystemExit("feasibility must mark solver-chosen witnesses")
    if feas.get("quotient_admitted") is not False:
        raise SystemExit("feasibility must not admit a quotient")
    if quotient.get("status") != "PASS" or quotient.get("quotient_admitted") is not True:
        raise SystemExit("bound quotient did not admit")
    if unbound.get("status") != "HOLD" or unbound.get("reason") != "REFUSE_UNBOUND_OBSERVATION":
        raise SystemExit("unbound quotient did not hold")
    if surface.get("status") != "PASS":
        raise SystemExit("surface status mismatch")
    if surface.get("seed", {}).get("surface", {}).get("kind") != "static_finite_supports":
        raise SystemExit("surface kind mismatch")
    summary = {
        "schema": "constraintbox.contained-light-verify.v1",
        "promotion_allowed": False,
        "claim_ceiling": (
            "contained source overlay; seed-check + feasibility + bound quotient; "
            "solver-chosen obs are not measured distinguishability; not Light-wheel admission"
        ),
        "isolated_import_failed_as_expected": True,
        "seed_check_disposition": seed_check["disposition"],
        "seed_status": seed["status"],
        "feasibility_status": feas["status"],
        "quotient_admitted": quotient.get("quotient_admitted"),
        "surface_packets": len(surface["packets"]),
    }
    (root / "VERIFY_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("verify ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
