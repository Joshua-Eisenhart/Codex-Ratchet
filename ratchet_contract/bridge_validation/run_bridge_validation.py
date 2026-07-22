#!/usr/bin/env python3
"""
run_bridge_validation.py -- run the 9 controls + 3 bridge self-tests, write
ratchet_contract/bridge_validation/results/bridge_validation.json.

BRIDGE_VALIDATION tests whether a proposed trace->partition bridge honestly
lets the FIXED ratchet (ratchet_contract/gates.py, mss.py) see competing
candidates. It does NOT ratchet the axioms and does NOT admit any real
carrier -- see README.md. `promotion_allowed: false`.

Exit codes (matches ratchet_contract/run_contract_selfcheck.py's discipline
-- the interface is the exit code, not printed prose):
    0 = every one of the 9 controls fired its expected verdict, all 3
        bridge self-tests fired as expected, the two bridges agreed on
        every exact toy case gathered (C9), and the forbidden-surface-
        token scan is clean.
    1 = at least one of those checks did not hold -- the JSON `findings`
        list names exactly which, honestly, rather than forcing green.

KNOWN ISSUE (diagnosed, worked around, not hidden): the cvc5 Python binding
(`cvc5.cvc5_python_base`) segfaults during normal CPython interpreter
shutdown when many Solver/TermManager objects are garbage-collected in this
process (confirmed via `python3 -X faulthandler`: the crash is inside
"Garbage-collecting" with zero Python frames on the stack, AFTER main()
already returned its correct exit code and every result was written and
printed -- i.e. the bug is in cvc5's native destructor/finalizer ordering
on interpreter teardown, not in any computation this file performs). The
`__main__` block below calls `os._exit()` after flushing stdout, which
skips CPython's normal GC-driven shutdown sequence entirely and bypasses
the crash without touching program logic or results.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
RESULTS_PATH = THIS_DIR / "results" / "bridge_validation.json"

from controls import run_all_controls, action_category_coverage  # noqa: E402
from bridge_self_tests import run_all_self_tests  # noqa: E402

# Files whose ACTUAL vocabulary must avoid the forbidden shared-surface
# tokens. bridge_interface.py is deliberately EXCLUDED: it is where
# FORBIDDEN_SURFACE_TOKENS is itself defined and documented, so scanning it
# would trivially self-flag (its own policy list contains the tokens as
# data, not as candidate/bridge vocabulary).
_SCANNED_FILES = (
    "bridge_action_predictive.py",
    "bridge_smt_relational.py",
    "controls.py",
    "bridge_self_tests.py",
    "run_bridge_validation.py",
)


def _confirm_no_forbidden_surface_tokens() -> dict:
    """Mechanical (substring) scan, mirroring
    ratchet_contract/run_contract_selfcheck.py's _confirm_no_llm_or_network_calls:
    every check is code, nothing is asserted in prose."""
    from bridge_interface import FORBIDDEN_SURFACE_TOKENS

    hits = {}
    for fname in _SCANNED_FILES:
        text = (THIS_DIR / fname).read_text(encoding="utf-8").lower()
        found = [tok for tok in FORBIDDEN_SURFACE_TOKENS if tok in text]
        if found:
            hits[fname] = found
    return {
        "scanned_files": list(_SCANNED_FILES),
        "excluded_file": "bridge_interface.py (defines/documents the forbidden-token list itself)",
        "forbidden_tokens_checked": list(FORBIDDEN_SURFACE_TOKENS),
        "hits": hits,
        "clean": len(hits) == 0,
    }


def _build_agreement_matrix(control_results: dict) -> dict:
    """Top-level roll-up of every control's bridge_agreement note -- the
    same data C9 consumes, surfaced directly per the task's request for
    'the two-bridge agreement matrix' as its own reportable section."""
    matrix = {}
    for cid, res in control_results.items():
        note = res.reasons.get("bridge_agreement")
        if note is not None:
            matrix[cid] = note
    all_agree = all(v.get("agree") for v in matrix.values()) if matrix else False
    return {"per_control": matrix, "all_controls_agree": all_agree}


def main() -> int:
    control_results = run_all_controls()
    self_test_results = run_all_self_tests()
    coverage = action_category_coverage()
    forbidden_scan = _confirm_no_forbidden_surface_tokens()
    agreement_matrix = _build_agreement_matrix(control_results)

    findings = []
    for cid, res in control_results.items():
        if not res.fired_as_expected:
            findings.append({
                "kind": "control_did_not_fire_as_expected", "id": cid,
                "expected_label": res.expected_label, "observed_label": res.label,
            })
    for sid, res in self_test_results.items():
        if not res.fired_as_expected:
            findings.append({
                "kind": "self_test_did_not_fire_as_expected", "id": sid,
                "expected_label": res.expected_label, "observed_label": res.label,
            })
    if not forbidden_scan["clean"]:
        findings.append({"kind": "forbidden_surface_token_found", "detail": forbidden_scan["hits"]})
    if not coverage["all_categories_covered"]:
        findings.append({
            "kind": "manifold_action_category_not_exercised",
            "missing_categories": coverage["missing_categories"],
        })

    all_controls_fired = all(r.fired_as_expected for r in control_results.values())
    all_self_tests_fired = all(r.fired_as_expected for r in self_test_results.values())
    bridge_semantic_concordance = control_results["C9"].fired_as_expected

    overall_ok = (
        all_controls_fired and all_self_tests_fired and forbidden_scan["clean"]
        and bridge_semantic_concordance and coverage["all_categories_covered"]
    )

    result = {
        "schema_version": "bridge-validation/0.1",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "ceiling": (
            "input_interface_validation_only; this campaign tests whether a proposed trace->partition "
            "bridge honestly lets the FIXED ratchet (ratchet_contract/gates.py, mss.py) see competing "
            "candidates. it does NOT ratchet the axioms, does NOT admit any real carrier, and passing it "
            "is the PRECONDITION to adapting real carriers (not done here). promotion_allowed=false; "
            "formal_admission_allowed=false"
        ),
        "control_verdicts": {cid: res.to_json() for cid, res in control_results.items()},
        "bridge_self_tests": {sid: res.to_json() for sid, res in self_test_results.items()},
        "agreement_matrix": agreement_matrix,
        "action_category_coverage": coverage,
        "forbidden_surface_token_scan": forbidden_scan,
        "findings": findings,
        "confirmations": {
            "all_9_controls_fired_as_expected": all_controls_fired,
            "all_3_self_tests_fired_as_expected": all_self_tests_fired,
            "bridges_agree_on_every_exact_toy_case_C9": bridge_semantic_concordance,
            "forbidden_surface_token_scan_clean": forbidden_scan["clean"],
            "all_manifold_action_categories_exercised": coverage["all_categories_covered"],
            "overall_ok": overall_ok,
        },
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    print(json.dumps(result["confirmations"], indent=2))
    print(f"\nfull receipt written to {RESULTS_PATH}")
    print("\ncontrol verdict matrix:")
    for cid, res in control_results.items():
        print(f"  {cid}: {'OK  ' if res.fired_as_expected else 'FIND'}  {res.label}")
    print("\nself-test matrix:")
    for sid, res in self_test_results.items():
        print(f"  {sid}: {'OK  ' if res.fired_as_expected else 'FIND'}  {res.label}")
    if findings:
        print(f"\n{len(findings)} FINDING(S) -- reported, not forced:")
        for f in findings:
            print(f"  - {f}")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    _rc = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(_rc)  # see module docstring's KNOWN ISSUE -- skips cvc5's buggy GC-shutdown path
