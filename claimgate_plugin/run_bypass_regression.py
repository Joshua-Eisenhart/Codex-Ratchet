#!/usr/bin/env python3
"""BYPASS REGRESSION — six end-to-end cases that must never be admitted.

Every case below was RUN against the reviewed gate and observed to be admitted.
Two of them return exit 0 / VERIFIED / ledger PASS through the full
post_receipt_gate.sh chain. This file is the standing proof that they stop doing
so, and it is deliberately end-to-end: a unit test on one checker would have
missed all six, because each survives by taking a path around a checker rather
than by defeating one.

ACCEPTANCE (all three clauses, per external review):
  - every case must PARK or BLOCK
  - no case may produce VERIFIED, PASS, or ADMITTED_PENDING_DEPTH
  - claim kind and the numeric-engine requirement must be resolved from an
    EVALUATOR-OWNED registry, never from the receipt

ADMITTED_PENDING_DEPTH counts as a failure here on purpose. It is an ADMITTING
disposition — post_receipt_gate.sh sets gate_admits=1 on it — so allowing it
would let a forged receipt through wearing an "audit owed" label.

Why the earlier diagnosis was wrong, recorded so it is not repeated: a receipt
with classification `canonical` was rejected, and I generalised that to "no
claim_kind defines a tier0_gate, so every kind rejects". Wrong. Receipts with
classification `tool_lego_fit_probe` take a different path and reach VERIFIED.
One rejection is not a proof of closure, and the end-to-end verdict is the only
thing that settles it.

Exit: 0 all six blocked | 1 one or more admitted | 2 usage.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BYPASS = REPO / "claimgate_plugin" / "fixtures" / "bypass"
HOOK = REPO / "claimgate_plugin" / "hooks" / "post_receipt_gate.sh"
LEDGER = REPO / "claimgate_plugin" / "results" / "gate_ledger.jsonl"

ADMITTING = {"PASS", "ADMITTED_PENDING_DEPTH", "ADMITTED_FLOOR_PARKED"}
ADMITTING_VERDICTS = {"VERIFIED"}

CASES = [
    ("b1", "field_only + producer numeric_engine_required=false",
     "b1_field_only_self_exempt.json",
     "the receipt declares its own exemption; three_engine_seal.py:120 honours it"),
    ("b2", "field_only + asserted numeric value, no engine metadata",
     "b2_field_only_asserted_number.json",
     "omission reads as 'no numeric-engine intent (pure symbolic/SMT/finite)'; "
     "recompute says the number is merely asserted; claim_verify still returns VERIFIED"),
    ("b3", "forged matching JAX/Julia numeric fields",
     "b3_forged_two_engine_agreement.json",
     "two copied numbers in one file; Julia is never executed by any gate"),
    ("b4", "fake JAX leg that prints JSON without JAX",
     "b4_fake_jax_leg/results/probe.json",
     "the old re-derive checked none of import jax / jaxpr / devices / __version__"),
    ("b5", "decorative JAX import with no dispatched operation",
     "b5_decorative_jax/results/probe.json",
     "import present, zero engine operations invoked"),
    ("b6", "NaN matching engine values via the metadata-only path",
     "b6_nan_matching_engine_values.json",
     "NaN == NaN comparisons are false, so a NaN pair reads as perfect agreement"),
    # --------------------------------------------------------------------------
    # b7-b10 defeat the FIX for b1-b6. Found by attacking my own gate rather than
    # by waiting for review. All four are OPEN.
    ("b7", "claim hidden under a key name on the ignored-metadata list",
     "b7_claim_hidden_under_ignored_key.json",
     "metadata_keys_ignored skips 'count' at ANY depth, so the claim rides in a key "
     "the detector refuses to look at"),
    ("b8", "integer claim outside any claim-bearing container",
     "b8_integer_outside_container.json",
     "integers count only inside a claim_bearing_container, so a bare integer claim evades"),
    ("b9", "number encoded as a JSON string",
     "b9_number_as_string.json",
     "content detection walks for int/float; a stringified number is invisible to it"),
    ("b10", "one token engine op, then print fabricated constants",
     "b10_token_dispatch/results/probe.json",
     "dispatch counting proves AN operation ran, not that the OUTPUT came from it — the "
     "deepest of the four, and the one the design does not currently address"),
    # b11-b12 defeated the INVERSION that fixed b7-b9. Found by an independent
    # workflow lane, then reproduced against the inverted function.
    ("b11", "whole payload one level down under a key on the exempt-path list",
     "b11_subtree_under_exempt_path.json",
     "the exemption skipped the SUBTREE, not the leaf, so {\"digest\": {...everything...}} "
     "was never walked; measured exit 0 / PASS / VERIFIED with no engine leg on disk"),
    ("b12", "receipt wrapped in a top-level JSON array",
     "b12_toplevel_array_wrapper.json",
     "a non-dict document returned 0 without evaluating, so an array wrapper skipped "
     "the whole policy"),
]


def chain(receipt: Path):
    """Run the fired chain and read the disposition it durably recorded."""
    before = len(LEDGER.read_bytes().splitlines()) if LEDGER.exists() else 0
    env = dict(os.environ)
    proc = subprocess.run(["sh", str(HOOK), str(receipt)],
                          capture_output=True, text=True, cwd=str(REPO), env=env)
    disp = None
    if LEDGER.exists():
        lines = LEDGER.read_bytes().splitlines()
        if len(lines) > before:
            try:
                disp = json.loads(lines[-1]).get("disposition")
            except json.JSONDecodeError:
                disp = "UNPARSEABLE_LEDGER_LINE"
    return proc.returncode, disp


def verdict_of(receipt: Path):
    p = subprocess.run([sys.executable, str(REPO / "claimgate_plugin" / "claim_verify.py"),
                        str(receipt)], capture_output=True, text=True, cwd=str(REPO))
    txt = p.stdout or ""
    i = txt.find("{")
    if i < 0:
        return None
    try:
        return json.loads(txt[i:]).get("verdict")
    except json.JSONDecodeError:
        return None


def main(argv):
    if not HOOK.exists():
        print(f"run_bypass_regression: usage — hook absent: {HOOK}", file=sys.stderr)
        return 2
    rows, admitted = [], []
    for cid, name, rel, why in CASES:
        p = BYPASS / rel
        if not p.exists():
            rows.append((cid, name, "MISSING_FIXTURE", None, None))
            admitted.append(cid)          # a deleted regression input is a failure
            continue
        rc, disp = chain(p)
        verd = verdict_of(p)
        bad = (disp in ADMITTING) or (verd in ADMITTING_VERDICTS) or rc == 0
        rows.append((cid, name, disp or "NO_LEDGER_LINE", verd, rc))
        if bad:
            admitted.append(cid)
        print(f"  {cid}  exit={rc}  disposition={disp}  claim_verify={verd}")
        print(f"      {name}")
        print(f"      {'ADMITTED — BYPASS OPEN' if bad else 'blocked'}   ({why[:96]})")

    print(f"\nrun_bypass_regression: {len(CASES) - len(admitted)}/{len(CASES)} blocked")
    out = {"probe": "claimgate_bypass_regression_v1",
           "classification": "tool_lego_fit_probe", "promotion_allowed": False,
           "acceptance": "every case must PARK or BLOCK; none may yield VERIFIED, PASS, or "
                         "ADMITTED_PENDING_DEPTH (that disposition ADMITS)",
           "blocked": len(CASES) - len(admitted), "total": len(CASES),
           "still_admitted": admitted,
           "results": [{"id": c, "case": n, "disposition": d, "claim_verify": v, "exit": e}
                       for c, n, d, v, e in rows]}
    d = REPO / "claimgate_plugin" / "results"
    d.mkdir(exist_ok=True)
    (d / "bypass_regression_v1.json").write_text(json.dumps(out, indent=1) + "\n")
    if admitted:
        print(f"run_bypass_regression: FAIL — {admitted} still admitted. The gate rewards a "
              f"convincing receipt over a real computation.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
