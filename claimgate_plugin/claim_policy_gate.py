#!/usr/bin/env python3
"""CLAIM POLICY GATE — the evaluator decides what a receipt must satisfy.

THE HOLE THIS CLOSES, measured end-to-end on the reviewed branch:

    {"classification":"tool_lego_fit_probe","claim_kind":"field_only",
     "engine_contract":{"numeric_engine_required":false,
                        "exemption_reason":"producer says so"}}
      -> post_receipt_gate.sh exit 0, claim_verify VERIFIED, ledger PASS

    {"classification":"tool_lego_fit_probe","claim_kind":"field_only",
     "claim":"numeric result","value":123.0}
      -> post_receipt_gate.sh exit 0, claim_verify VERIFIED, ledger PASS

Both self-certified. The first declared its own exemption; the second said nothing
and was read as "pure symbolic/SMT/finite by default". claim_verify returned
VERIFIED for all six forged cases in the regression set without once consulting
engine evidence.

THE RULE. A receipt may DESCRIBE itself. It may not DECIDE what it must satisfy.
  - numeric-ness is derived from CONTENT (claimgate_plugin/claim_policy.json),
    so it cannot be switched off by a boolean or by omission
  - the engine requirement comes from the policy file, never the receipt
  - `numeric_engine_required` is recorded as a producer ASSERTION and ignored
  - omission of engine metadata on a numeric claim is PARK, never exemption
  - each declared load-bearing engine must be WITNESSED by execution
    (claimgate_plugin/engine_witness.py: presence, dispatch, poison, mutation)
  - non-finite engine values are rejected: NaN == NaN is false, so a NaN pair
    reads as perfect agreement under a naive difference test

HONEST CEILING. claim_policy.json is a strong default, not yet a trust root: it
lives in the repo it governs, so a producer who can commit can edit it. Making it
authoritative needs CODEOWNERS on that path plus branch protection, which is not
in force. This gate says so in its own output rather than implying otherwise.

Exit: 0 policy satisfied | 1 BLOCK | 3 PARK/PENDING_EVIDENCE | 2 usage.
Nonzero is a policy/infra disposition, never a scientific verdict.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
POLICY_PATH = REPO / "claimgate_plugin" / "claim_policy.json"
sys.path.insert(0, str(REPO))


def load_policy():
    return json.loads(POLICY_PATH.read_bytes())


_NUMERIC_STRING = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def _numbers_in_claim_positions(obj, pol, container=None, path="", hits=None):
    """CONTENT-DERIVED numeric detection. EVERY number is a claim by default.

    INVERTED 2026-07-25 after three fixtures (b7, b8, b9) walked through the
    previous design, which was a key-name denylist plus a container allowlist:

      b7  {"count": 1.7807764}        'count' is on metadata_keys_ignored, at ANY depth
      b8  {"survivors": 42}           an integer outside claim_bearing_containers
      b9  {"metrics":{"gap":"1.78"}}  the number encoded as a string

    That is the same shape as the path-prefix exclusion which was the cheapest
    bypass earlier in this work: a NAME cannot establish that a number is not a
    claim, exactly as a path prefix could not establish that a file was not
    poison. So the polarity is flipped — numbers are claims, and exemption must
    be EARNED by an exact full-path match on a short reviewed list, never by a
    key name that happens to appear somewhere in the document.

    Numeric-looking STRINGS count too: encoding a float as text does not make it
    a different claim.
    """
    hits = [] if hits is None else hits
    nc = pol["numeric_content_detection"]
    exempt_paths = set(nc.get("metadata_paths_exempt", []))
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else f".{k}"
            if p.lstrip(".") in exempt_paths:
                continue                     # EXACT full path, not a bare name
            _numbers_in_claim_positions(v, pol, container, p, hits)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _numbers_in_claim_positions(v, pol, container, f"{path}[{i}]", hits)
    elif isinstance(obj, bool):
        return hits                          # a flag is not a measurement
    elif isinstance(obj, (int, float)):
        hits.append((path, obj))
    elif isinstance(obj, str) and _NUMERIC_STRING.match(obj.strip()):
        hits.append((path, obj))
    return hits


def _engine_blocks(receipt):
    """{engine: {metric: value}} from whichever container the receipt used."""
    out = {}
    for key in ("engines_ran", "engines"):
        blk = receipt.get(key)
        if not isinstance(blk, dict):
            continue
        for eng, ev in blk.items():
            if isinstance(ev, dict):
                out.setdefault(str(eng).lower(), {}).update(ev)
    return out


def _declared_load_bearing(receipt, pol):
    depth = receipt.get("TOOL_INTEGRATION_DEPTH") or receipt.get("tool_integration_depth") or {}
    lb = {k.lower() for k, v in depth.items() if v == "load_bearing"}
    ec = receipt.get("engine_contract") or {}
    for e in (ec.get("engines") or []):
        lb.add(str(e).lower())
    lb |= set(_engine_blocks(receipt))
    return lb & set(pol["engine_requirement"]["authoritative_engines"])


def _non_finite_engine_values(receipt):
    bad = []
    for eng, ev in _engine_blocks(receipt).items():
        for k, v in ev.items():
            if isinstance(v, str) and v.strip().lower() in {"nan", "inf", "-inf", "infinity", "-infinity"}:
                bad.append(f"{eng}.{k}={v!r}")
            elif isinstance(v, float) and not math.isfinite(v):
                bad.append(f"{eng}.{k}={v!r}")
    return bad


def _witness(receipt_path: Path, eng: str):
    """Locate <name>_<eng>.py beside results/<name>.json and witness it."""
    from claimgate_plugin.engine_witness import witness_leg

    rp = Path(receipt_path)
    leg = rp.parent.parent / f"{rp.stem}_{eng}.py"
    return witness_leg(leg, eng)


def evaluate(receipt: dict, receipt_path: Path, pol: dict):
    """-> (exit, label, message, detail)"""
    nums = _numbers_in_claim_positions(receipt, pol)
    assertion = (receipt.get("engine_contract") or {}).get("numeric_engine_required")
    det = {"producer_assertion_numeric_engine_required": assertion,
           "producer_assertion_honoured": False,
           "numeric_evidence_found": [f"{p}={v}" for p, v in nums[:6]],
           "numeric_evidence_count": len(nums),
           "policy_ownership": pol["_ownership"][:140]}

    if not nums:
        return 0, "pass", ("no numbers in any claim-bearing container, so the evaluator "
                           "establishes exemption from CONTENT (not from a declaration)"), det

    # From here the claim IS numeric, whatever it declared.
    nf = _non_finite_engine_values(receipt)
    if nf:
        det["non_finite_engine_values"] = nf
        return 1, "BLOCK", (f"non-finite engine value(s) {nf}: NaN == NaN is false, so a NaN "
                            f"pair reads as perfect agreement under a difference test"), det

    declared = sorted(_declared_load_bearing(receipt, pol))
    det["declared_authoritative_engines"] = declared
    need = pol["engine_requirement"]["min_witnessed_engines"]

    if not declared:
        return 3, "PARK", (f"numeric claim ({len(nums)} value(s) in claim-bearing containers, "
                           f"e.g. {det['numeric_evidence_found'][:2]}) carries NO engine "
                           f"metadata. Omission is PENDING EVIDENCE, never 'pure symbolic by "
                           f"default'"
                           + (f". The receipt asserted numeric_engine_required={assertion}, "
                              f"which is recorded and NOT honoured — policy is the evaluator's"
                              if assertion is not None else "")), det

    witnessed, failures = [], []
    for eng in declared:
        ok, rep = _witness(receipt_path, eng)
        det.setdefault("witness", {})[eng] = {"verdict": rep.get("verdict"),
                                              "error": rep.get("error")}
        (witnessed if ok else failures).append(eng)
    det["witnessed"] = witnessed
    det["witness_failures"] = failures

    if failures:
        v = "; ".join(f"{e}: {det['witness'][e]['verdict']}" for e in failures)
        return 1, "BLOCK", (f"declared load-bearing engine(s) not witnessed by execution — {v}. "
                            f"A recorded number is not evidence that an engine produced it"), det
    if len(witnessed) < need:
        return 3, "PARK", (f"only {len(witnessed)} engine(s) witnessed ({witnessed}), policy "
                           f"requires {need}. Two copied numeric fields are one assertion, "
                           f"not two engines"), det
    return 0, "pass", f"{len(witnessed)} engine(s) witnessed by execution: {witnessed}", det


def main(argv):
    if len(argv) != 2:
        print("usage: claim_policy_gate.py <receipt.json>", file=sys.stderr)
        return 2
    p = Path(argv[1])
    if not p.exists():
        print(f"claim_policy_gate: BLOCK — artifact absent: {p}", file=sys.stderr)
        return 1
    try:
        receipt = json.loads(p.read_bytes())
        pol = load_policy()
    except Exception as exc:  # noqa: BLE001
        print(f"claim_policy_gate: BLOCK — cannot evaluate ({exc}); failing CLOSED",
              file=sys.stderr)
        return 1
    if not isinstance(receipt, dict):
        print("claim_policy_gate: pass — non-object document, no claim to police", file=sys.stderr)
        return 0
    code, label, msg, det = evaluate(receipt, p, pol)
    print(json.dumps({"tool": "claimgate.claim_policy_gate", "receipt": str(p),
                      "disposition": label, "message": msg, "detail": det,
                      "ceiling": "claim_policy.json lives in the repo it governs, so it is a "
                                 "strong default, not a trust root, until CODEOWNERS + branch "
                                 "protection cover it"}, indent=1))
    print(f"claim_policy_gate: {label} — {msg}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
