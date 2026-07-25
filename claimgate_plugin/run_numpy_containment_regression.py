#!/usr/bin/env python3
"""NUMPY CONTAINMENT REGRESSION — the owner's restored numpy rule, both sides.

THE RULE (owner, 2026-07-22; claimgate_plugin/claim_policy.json
engine_requirement.control_only and its _control_only_note):

    numpy in a CONTAINED downstream-satellite role is ALLOWED.
    numpy labelled or evidenced as LOAD-BEARING is REJECTED.

A one-sided test cannot prove that. "numpy load_bearing is rejected" is also
satisfied by a gate that rejects everything, and "a numpy receipt is admitted"
is also satisfied by a gate that admits everything. Only the PAIR pins the rule
down, so both directions are measured here and both must land.

ISOLATION. The two fixtures differ in EXACTLY ONE field:

    TOOL_INTEGRATION_DEPTH.numpy   "supportive"  ->  "load_bearing"

Same receipt otherwise, byte for byte. Same three leg files, byte for byte —
a real JAX leg, a real PyTorch leg, and the numpy satellite. This runner asserts
that single-field property before it runs anything, so the result cannot later be
explained by some other drift between the fixtures.

WHY THE REASON IS ASSERTED, NOT JUST THE EXIT CODE. A regression that checks only
"n1 exits 0, n2 exits nonzero" turns green for any breakage that happens to fail
n2 first — a missing leg, an unreadable file, an import error. So the FAIL side
additionally requires that:

  - the blocking stage is the SEAL (not intake, not tier0, not the policy gate)
  - the seal's own message names numpy as control-only
  - the claim-policy stage exited 0 on BOTH sides

That last one is the load-bearing clause. It records that n2's JAX and PyTorch
legs were WITNESSED by execution — presence, dispatch, poison, mutation all
passed — so n2 is not rejected for having weak engines. It has the same real
engines as n1. It is rejected for the label alone, which is precisely the
containment rule and nothing else.

Exit: 0 rule proven in both directions | 1 not proven | 2 usage.
Nonzero is a policy/infra disposition, never a scientific verdict.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BYPASS = REPO / "claimgate_plugin" / "fixtures" / "bypass"
HOOK = REPO / "claimgate_plugin" / "hooks" / "post_receipt_gate.sh"
LEDGER = REPO / "claimgate_plugin" / "results" / "gate_ledger.jsonl"

PASS_DIR = BYPASS / "n1_contained_numpy_satellite"
FAIL_DIR = BYPASS / "n2_load_bearing_numpy"
RECEIPT = "results/probe.json"
LEGS = ("probe_jax.py", "probe_torch.py", "probe_numpy_satellite.py")

ADMITTING = {"PASS", "ADMITTED_PENDING_DEPTH", "ADMITTED_FLOOR_PARKED"}
THE_FIELD = ("TOOL_INTEGRATION_DEPTH", "numpy")


def isolation_check():
    """The pair must differ in exactly one field, over identical legs."""
    problems = []
    a = json.loads((PASS_DIR / RECEIPT).read_bytes())
    b = json.loads((FAIL_DIR / RECEIPT).read_bytes())
    differing = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    if differing != [THE_FIELD[0]]:
        problems.append(f"receipts differ in {differing}, expected only ['{THE_FIELD[0]}']")
    da, db = a.get(THE_FIELD[0], {}), b.get(THE_FIELD[0], {})
    inner = sorted(k for k in set(da) | set(db) if da.get(k) != db.get(k))
    if inner != [THE_FIELD[1]]:
        problems.append(f"{THE_FIELD[0]} differs in {inner}, expected only ['{THE_FIELD[1]}']")
    if da.get("numpy") != "supportive":
        problems.append(f"n1 numpy label is {da.get('numpy')!r}, expected 'supportive'")
    if db.get("numpy") != "load_bearing":
        problems.append(f"n2 numpy label is {db.get('numpy')!r}, expected 'load_bearing'")
    for leg in LEGS:
        pa, pb = PASS_DIR / leg, FAIL_DIR / leg
        if not pa.exists() or not pb.exists():
            problems.append(f"leg {leg} missing from one side of the pair")
        elif pa.read_bytes() != pb.read_bytes():
            problems.append(f"leg {leg} is not byte-identical across the pair")
    return {"one_field_difference": not problems, "differing_top_level_keys": differing,
            "differing_depth_labels": inner, "problems": problems}


def chain(receipt: Path):
    """Run the fired chain; read the exit, the durable ledger line, and stderr."""
    before = len(LEDGER.read_bytes().splitlines()) if LEDGER.exists() else 0
    proc = subprocess.run(["sh", str(HOOK), str(receipt)],
                          capture_output=True, text=True, cwd=str(REPO))
    row = {}
    if LEDGER.exists():
        want = str(receipt.relative_to(REPO)) if receipt.is_relative_to(REPO) else str(receipt)
        for ln in LEDGER.read_bytes().splitlines()[before:]:
            try:
                cand = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if cand.get("receipt_path") == want:
                row = cand
    stages = {s["stage"]: s["exit"] for s in row.get("stages", [])}
    return {"exit": proc.returncode, "disposition": row.get("disposition"),
            "blocking_stage": row.get("blocking_stage"), "stages": stages,
            "seal_message": next((l for l in proc.stderr.splitlines()
                                  if l.startswith("three_engine_seal:")), None)}


def main(argv):
    if not HOOK.exists():
        print(f"run_numpy_containment_regression: usage — hook absent: {HOOK}", file=sys.stderr)
        return 2
    for d in (PASS_DIR, FAIL_DIR):
        if not (d / RECEIPT).exists():
            print(f"run_numpy_containment_regression: usage — fixture absent: {d / RECEIPT}",
                  file=sys.stderr)
            return 2

    iso = isolation_check()
    print(f"  isolation  one-field difference: {iso['one_field_difference']}  "
          f"(top-level {iso['differing_top_level_keys']}, label {iso['differing_depth_labels']})")
    for p in iso["problems"]:
        print(f"      PROBLEM {p}")

    allowed = chain(PASS_DIR / RECEIPT)
    rejected = chain(FAIL_DIR / RECEIPT)

    failures = list(iso["problems"])

    # ---- ALLOWED side: contained numpy satellite must be ADMITTED.
    if allowed["exit"] != 0:
        failures.append(f"contained-numpy receipt exited {allowed['exit']}, expected 0")
    if allowed["disposition"] not in ADMITTING:
        failures.append(f"contained-numpy disposition {allowed['disposition']!r} does not admit")
    if allowed["stages"].get("seal") != 0:
        failures.append(f"seal exited {allowed['stages'].get('seal')} on the contained side; "
                        f"the rule must ALLOW a satellite, not merely fail it late")

    # ---- REJECTED side: numpy labelled load_bearing must be BLOCKED, at the seal,
    # for the numpy reason, with its engines witnessed exactly as on the allowed side.
    if rejected["exit"] == 0:
        failures.append("numpy labelled load_bearing was ADMITTED — the containment rule is open")
    if rejected["disposition"] != "BLOCKED":
        failures.append(f"load-bearing-numpy disposition {rejected['disposition']!r}, "
                        f"expected BLOCKED")
    if rejected["blocking_stage"] != "seal":
        failures.append(f"load-bearing-numpy blocked at {rejected['blocking_stage']!r}, not the "
                        f"seal — the right verdict for the wrong reason is not the rule holding")
    msg = rejected["seal_message"] or ""
    if "numpy" not in msg or "CONTROL-ONLY" not in msg:
        failures.append(f"seal message does not name numpy as control-only: {msg!r}")
    for side, res in (("contained", allowed), ("load_bearing", rejected)):
        if res["stages"].get("claim_policy") != 0:
            failures.append(f"{side} side: claim_policy exited "
                            f"{res['stages'].get('claim_policy')}, so its JAX and PyTorch legs "
                            f"were not both witnessed. Without that, the pair proves nothing "
                            f"about numpy — only that one side had weaker engines.")

    for label, res in (("ALLOW  contained numpy satellite", allowed),
                       ("REJECT numpy labelled load_bearing", rejected)):
        print(f"  {label}\n      exit={res['exit']}  disposition={res['disposition']}  "
              f"blocking_stage={res['blocking_stage']}  stages={res['stages']}")
        if res["seal_message"]:
            print(f"      {res['seal_message']}")

    out = {"probe": "claimgate_numpy_containment_regression_v1",
           "classification": "tool_lego_fit_probe", "promotion_allowed": False,
           "rule": "owner 2026-07-22 — CONTAINED numpy as a downstream satellite is ALLOWED; "
                   "numpy labelled or evidenced as LOAD-BEARING is REJECTED",
           "rule_source": ["claimgate_plugin/claim_policy.json engine_requirement.control_only",
                           "claimgate_plugin/three_engine_seal.py R1"],
           "acceptance": "both directions must land: the contained satellite ADMITTED, the "
                         "load-bearing label BLOCKED at the seal for the numpy reason, with the "
                         "claim-policy engine witness passing on BOTH sides",
           "isolation": iso,
           "allowed_case": {"fixture": str((PASS_DIR / RECEIPT).relative_to(REPO)), **allowed},
           "rejected_case": {"fixture": str((FAIL_DIR / RECEIPT).relative_to(REPO)), **rejected},
           "rule_proven": not failures, "failures": failures}
    d = REPO / "claimgate_plugin" / "results"
    d.mkdir(exist_ok=True)
    (d / "numpy_containment_regression_v1.json").write_text(json.dumps(out, indent=1) + "\n")

    if failures:
        print(f"\nrun_numpy_containment_regression: FAIL — {len(failures)} unmet clause(s)")
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("\nrun_numpy_containment_regression: rule proven in BOTH directions — a contained "
          "numpy satellite is admitted, the same receipt with numpy labelled load_bearing is "
          "blocked at the seal, and the one field between them is the label.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
