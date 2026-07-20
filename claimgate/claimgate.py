#!/usr/bin/env python3
"""
claimgate.py -- deterministic receipt validator (CODE, never LLM judgment).

Usage:
    python3 claimgate.py <path/to/receipt.json>

Exit codes (the only interface -- do not parse prose):
    0 = admitted   (no reasons printed)
    1 = rejected   (machine-readable reasons JSON printed to stdout)

Checks (all run every time; every failing check is reported, not just the first):
  R1  classification_missing / classification_not_allowed
  R2  promotion_without_canonical_evidence
  R3  verdict_inflation           (INTEGRATED/GREEN-type verdict beside pass:false)
  R4  controls_missing            (no controls section present at all)
  R4b controls_copy_of_main_run   (a control's numeric leaves exactly match the
                                    main-run numeric leaves -- copy-detection)
  R5  negative_mutual_information (any *mutual_info* key with a negative value)
  R6  preregistration_missing     (no preregistration header reference anywhere)

This is a GENERAL validator. It must not special-case any receipt path.
"""
import json
import sys
import re
from pathlib import Path

ALLOWED_CLASSIFICATIONS = {
    "canonical",
    "classical_baseline",
    "scratch_diagnostic",
    "diagnostic_only",
    "tool_integration_battery",
    "tournament_lane_working_sim",
    "tournament_lane_receipt",
    "tournament_control_lane_receipt",
    "tool_lego_fit_probe",
    "world_engine_object_source",
    "working_sim",
}

CANONICAL_EVIDENCE_LABELS = {
    "canonical by process",
    "canonical_by_process",
}

VERDICT_INFLATION_PATTERN = re.compile(r"\b(INTEGRATED|GREEN)\b", re.IGNORECASE)
MUTUAL_INFO_KEY_PATTERN = re.compile(r"mutual_info", re.IGNORECASE)
PREREGISTRATION_KEY_PATTERN = re.compile(r"preregist", re.IGNORECASE)


def walk(obj, path=""):
    """Yield (path, key, value) for every scalar leaf and every dict encountered."""
    if isinstance(obj, dict):
        yield ("__dict__", path, obj)
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield ("__leaf__", path, obj)


def find_key_matches(obj, pattern):
    """Return list of (path, key, value) where the leaf key matches pattern."""
    hits = []

    def _rec(o, path, last_key):
        if isinstance(o, dict):
            for k, v in o.items():
                _rec(v, f"{path}.{k}" if path else str(k), k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                _rec(v, f"{path}[{i}]", last_key)
        else:
            if last_key is not None and pattern.search(str(last_key)):
                hits.append((path, last_key, o))

    _rec(obj, "", None)
    return hits


def any_string_matches(obj, pattern):
    """True if any string leaf in obj matches pattern."""
    for kind, path, val in walk(obj):
        if kind == "__leaf__" and isinstance(val, str) and pattern.search(val):
            return True
        if kind != "__leaf__" and isinstance(val, str):
            pass
    return False


def collect_numeric_leaves(obj):
    """Collect all numeric leaves (floats/ints, excluding bools) as a sorted list."""
    out = []
    for kind, path, val in walk(obj):
        if kind == "__leaf__" and isinstance(val, (int, float)) and not isinstance(val, bool):
            out.append(round(float(val), 12))
    return sorted(out)


# ---------------------------------------------------------------------------
# R1: classification
# ---------------------------------------------------------------------------
def check_classification(receipt):
    reasons = []
    c = receipt.get("classification")
    if c is None:
        reasons.append({
            "code": "classification_missing",
            "detail": "top-level 'classification' field is absent",
        })
    elif c not in ALLOWED_CLASSIFICATIONS:
        reasons.append({
            "code": "classification_not_allowed",
            "detail": f"classification={c!r} is not in the allowed set",
        })
    return reasons


# ---------------------------------------------------------------------------
# R2: promotion_allowed
# ---------------------------------------------------------------------------
def check_promotion(receipt):
    reasons = []
    promo = receipt.get("promotion_allowed", None)
    if promo is True:
        label = str(receipt.get("accepted_status_label", "")).strip().lower()
        has_canonical_evidence = label in CANONICAL_EVIDENCE_LABELS
        if not has_canonical_evidence:
            reasons.append({
                "code": "promotion_without_canonical_evidence",
                "detail": (
                    "promotion_allowed=true but no canonical-by-process evidence "
                    f"(accepted_status_label={receipt.get('accepted_status_label')!r})"
                ),
            })
    return reasons


# ---------------------------------------------------------------------------
# R3: verdict inflation -- a dict with pass:false but a sibling string field
# reading INTEGRATED / GREEN (or similar "looks good" verdict language)
# ---------------------------------------------------------------------------
def check_verdict_inflation(receipt):
    reasons = []
    for kind, path, val in walk(receipt):
        if kind != "__dict__":
            continue
        d = val
        if d.get("pass") is False:
            for k, v in d.items():
                if k == "pass":
                    continue
                if isinstance(v, str) and VERDICT_INFLATION_PATTERN.search(v):
                    reasons.append({
                        "code": "verdict_inflation",
                        "detail": f"at {path or '<root>'}: pass=false but {k}={v!r}",
                    })
        # also catch all_pass True with any nested pass:false anywhere below this dict
        if d.get("all_pass") is True:
            for kind2, path2, val2 in walk(d):
                if kind2 == "__dict__" and val2 is not d and val2.get("pass") is False:
                    reasons.append({
                        "code": "verdict_inflation",
                        "detail": f"at {path or '<root>'}: all_pass=true but nested pass=false at {path2}",
                    })
    return reasons


# ---------------------------------------------------------------------------
# R4 / R4b: controls
# ---------------------------------------------------------------------------
HIGH_TIER_STATUS_LABELS = {"passes local rerun", "canonical by process"}


def requires_control_rigor(receipt):
    """Only receipts claiming a status above bare 'exists/runs' owe controls +
    a preregistration reference. Bare scratch/tool-fit probes do not."""
    label = str(receipt.get("accepted_status_label", "")).strip().lower()
    return label in HIGH_TIER_STATUS_LABELS or receipt.get("promotion_allowed") is True


def check_controls(receipt):
    reasons = []
    if not requires_control_rigor(receipt):
        return reasons
    control_hits = find_key_matches(receipt, re.compile(r"^controls$"))
    # also accept a top-level "controls" dict directly
    controls_blocks = []
    if isinstance(receipt.get("controls"), dict):
        controls_blocks.append(("controls", receipt["controls"]))
    for path, key, val in control_hits:
        if isinstance(val, dict) and (path, val) not in controls_blocks:
            controls_blocks.append((path, val))

    if not controls_blocks:
        reasons.append({
            "code": "controls_missing",
            "detail": "no 'controls' section found anywhere in the receipt",
        })
        return reasons

    # main-run numeric fingerprint: everything in the receipt EXCEPT the controls subtree(s)
    receipt_sans_controls = json.loads(json.dumps(receipt))
    if isinstance(receipt_sans_controls.get("controls"), dict):
        del receipt_sans_controls["controls"]
    main_numbers = collect_numeric_leaves(receipt_sans_controls)

    for path, block in controls_blocks:
        # a control block may itself contain several named sub-controls
        subblocks = block.items() if isinstance(block, dict) else []
        any_subblock_checked = False
        for name, sub in subblocks:
            if not isinstance(sub, (dict, list)):
                continue
            any_subblock_checked = True
            sub_numbers = collect_numeric_leaves(sub)
            if sub_numbers and main_numbers and sub_numbers == main_numbers:
                reasons.append({
                    "code": "controls_copy_of_main_run",
                    "detail": (
                        f"control '{path}.{name}' has numeric leaves identical "
                        "to the main run -- looks copy-pasted, not independently computed"
                    ),
                })
        if not any_subblock_checked and isinstance(block, dict):
            block_numbers = collect_numeric_leaves(block)
            if block_numbers and main_numbers and block_numbers == main_numbers:
                reasons.append({
                    "code": "controls_copy_of_main_run",
                    "detail": f"control block '{path}' numerically identical to main run",
                })
    return reasons


# ---------------------------------------------------------------------------
# R5: negative mutual information
# ---------------------------------------------------------------------------
NEGATIVE_MI_EPSILON = -1e-9  # floating-point noise around 0 is not a pathology


def check_negative_mutual_info(receipt):
    reasons = []
    for path, key, val in find_key_matches(receipt, MUTUAL_INFO_KEY_PATTERN):
        if isinstance(val, (int, float)) and not isinstance(val, bool) and val < NEGATIVE_MI_EPSILON:
            reasons.append({
                "code": "negative_mutual_information",
                "detail": f"{path} = {val} (mutual information cannot be negative)",
            })
    return reasons


# ---------------------------------------------------------------------------
# R6: preregistration header reference
# ---------------------------------------------------------------------------
def check_preregistration(receipt):
    reasons = []
    if not requires_control_rigor(receipt):
        return reasons
    hits = find_key_matches(receipt, PREREGISTRATION_KEY_PATTERN)
    if not hits:
        reasons.append({
            "code": "preregistration_missing",
            "detail": "no key matching 'preregist*' found anywhere in the receipt",
        })
    return reasons


CHECKS = [
    check_classification,
    check_promotion,
    check_verdict_inflation,
    check_controls,
    check_negative_mutual_info,
    check_preregistration,
]


def evaluate(receipt):
    reasons = []
    for check in CHECKS:
        reasons.extend(check(receipt))
    return reasons


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "usage: claimgate.py <receipt.json>"}))
        sys.exit(1)
    path = Path(sys.argv[1])
    try:
        receipt = json.loads(path.read_text())
    except Exception as e:
        print(json.dumps({"admitted": False, "path": str(path), "reasons": [
            {"code": "unreadable_receipt", "detail": str(e)}
        ]}))
        sys.exit(1)

    reasons = evaluate(receipt)
    if reasons:
        print(json.dumps({"admitted": False, "path": str(path), "reasons": reasons}, indent=2))
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
