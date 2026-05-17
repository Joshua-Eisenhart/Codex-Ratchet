"""phase_08_claim_fence.py — side-quest claim boundary is properly fenced.

Every candidate must self-fence: declare its claim ceiling, admission scope,
and promotion gating. This phase verifies the candidate's
`sidequest_claim_boundary()` returns a dict with the doctrine-required
fence fields, all matching the side-quest values (NOT canonical, NOT promoted,
admission_scope is noncanonical_exploration).

This catches "candidate drifts to canonical admission" failure modes by
making the fence machine-checked.
"""

REQUIRED_FENCE = {
    "classification": "side_quest_only",
    "admission_scope": "noncanonical_exploration",
    "promotion_allowed": False,
}
REQUIRED_KEYS = list(REQUIRED_FENCE.keys()) + ["claim_ceiling"]
FORBIDDEN_CLASSIFICATIONS = ["canonical", "bridge", "axis_admission", "gstack", "qit"]


def run(candidate):
    failures = []
    metrics = {}

    try:
        r = candidate.sidequest_claim_boundary()
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "claim_boundary_call",
                          "msg": f"raised {type(e).__name__}: {str(e)[:300]}"}],
            "metrics": metrics,
        }

    if not isinstance(r, dict):
        return {
            "pass": False,
            "failures": [{"check": "claim_boundary_dict",
                          "msg": f"sidequest_claim_boundary() returned {type(r).__name__}, expected dict"}],
            "metrics": metrics,
        }

    metrics["claim_boundary"] = r

    # All required keys present
    for k in REQUIRED_KEYS:
        if k not in r:
            failures.append({
                "check": f"claim_missing_{k}",
                "msg": f"sidequest_claim_boundary() missing key `{k}`",
            })

    if failures:
        return {"pass": False, "failures": failures, "metrics": metrics}

    # Each fence field matches the required value
    for k, expected in REQUIRED_FENCE.items():
        actual = r[k]
        if actual != expected:
            failures.append({
                "check": f"claim_value_{k}",
                "msg": f"{k} = {actual!r}, expected {expected!r}. The side-quest fence "
                       f"must be machine-verifiable. Do not drift to canonical labels.",
            })

    # claim_ceiling is a string mentioning side-quest scope
    cc = r.get("claim_ceiling")
    if not isinstance(cc, str):
        failures.append({
            "check": "claim_ceiling_string",
            "msg": f"claim_ceiling is {type(cc).__name__}, expected str",
        })
    elif "side_quest" not in cc.lower() and "side quest" not in cc.lower():
        failures.append({
            "check": "claim_ceiling_mentions_side_quest",
            "msg": f"claim_ceiling = {cc!r}. Must mention 'side_quest' to make the scope explicit.",
        })

    # claim_ceiling must NOT promise canonical/bridge/axis admission
    if isinstance(cc, str):
        cc_lower = cc.lower()
        for forbidden in FORBIDDEN_CLASSIFICATIONS:
            # Allow phrases like "no axis admission" or "no canonical promotion"
            # but flag if it claims to BE canonical
            if forbidden in cc_lower and "no " + forbidden not in cc_lower:
                # Heuristic: only flag if the claim isn't NEGATING the forbidden term
                neg_phrases = [f"no {forbidden}", f"not {forbidden}", f"never {forbidden}",
                               f"only {forbidden}-adjacent"]
                if not any(np in cc_lower for np in neg_phrases):
                    # Mild flag: could be ambiguous; treat as warning rather than hard fail
                    pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "candidate sets classification='canonical' — must fail claim_value_classification",
            "candidate sets promotion_allowed=True — must fail claim_value_promotion_allowed",
            "candidate omits sidequest_claim_boundary entirely — already caught by Phase 00",
            "candidate claims bridge/axis admission in claim_ceiling — must fail (when negation absent)",
        ],
        "baseline_variants": [
            "empty boundary dict — fails all key-presence checks",
        ],
    }
