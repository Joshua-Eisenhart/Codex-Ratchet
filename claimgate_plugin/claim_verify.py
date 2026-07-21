#!/usr/bin/env python3
"""
claim_verify — the higher-level claimgate: a TIER-DISPATCHING verifier.

The gap the inventory found: every verification TIER already exists in this repo
as a separate tool, and Lev already fires shell commands as un-skippable hooks
(`lev exec --verifier`). What was missing is the ONE thing that, given a receipt,
runs the applicable tiers and emits a composite verdict. This is that thing.

It does NOT reimplement any checker. It dispatches the existing ones and records
what it verified AND what it could not — a skipped tier is NEVER counted as passed.

    claim_verify <receipt.json> [--require tier0,tier2,...] [--json]
        exit 0 = every applicable/required tier passed
        exit 1 = a tier failed, or a --require tier was not verifiable
        exit 2 = usage/IO error

Tiers (cheapest -> deepest), each wired to a tool that ALREADY EXISTS here:
  tier0  field-consistency   claimgate/claimgate.py (R1-R6) | fallback claimgate.mjs
  tier1  recompute           claimgate.mjs R5 (runs when the receipt has a `recompute` block)
  tier2  smt-recheck+flip    the receipt's declared verification.tier2 cmd (e.g. proof_order_lane.py)
  tier3  referee-agreement   the receipt's declared verification.tier3 cmd (e.g. tools_qit_referee.py)
  tier4  fresh-audit affirm  sibling AUDIT_VERDICT.md must be CLEAN (not TAINTED/FATAL)

A receipt opts into tiers 2/3 by declaring them:
  "verification": { "tier2": {"cmd": ["python3","system_v8/manifold/engine/proof_order_lane.py"],
                              "expect": {"all_pass": true}} }

Designed to be the <cmd> in:  lev exec --verifier 'python3 claimgate_plugin/claim_verify.py <receipt>'
Emits a Lev-shaped claim_verdicts array so `lev gate validate` can consume it.

No third-party deps. Python 3.
"""
import json, os, subprocess, sys

def repo_root(start):
    d = os.path.abspath(start)
    while d != "/":
        if os.path.isdir(os.path.join(d, ".git")) or os.path.isdir(os.path.join(d, "system_v8")):
            return d
        d = os.path.dirname(d)
    return os.getcwd()

def run(cmd, cwd):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=900)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return None, "", str(e)

def load(path):
    with open(path) as f:
        return json.load(f)

# ---- tier implementations: each returns (status, evidence_ref, detail) ----
# status in {PASS, FAIL, SKIP, ERROR}. SKIP carries a reason and NEVER counts as passed.

def tier0(receipt_path, receipt, root):
    py = os.path.join(root, "claimgate", "claimgate.py")
    if os.path.exists(py):
        rc, out, err = run(["python3", py, receipt_path], root)
        tool = "claimgate/claimgate.py"
    else:
        mjs = os.path.join(root, "claimgate_plugin", "claimgate.mjs")
        rc, out, err = run(["node", mjs, "lint-receipt", receipt_path, "--rules",
                            os.path.join(root, "claimgate_plugin", "rules_ratchet.json")], root)
        tool = "claimgate_plugin/claimgate.mjs"
    if rc is None:
        return "ERROR", tool, err[:200]
    return ("PASS" if rc == 0 else "FAIL"), tool, f"{tool} exit {rc}"

def tier1(receipt_path, receipt, root):
    if "recompute" not in receipt:
        return "SKIP", None, "no recompute contract declared in receipt"
    mjs = os.path.join(root, "claimgate_plugin", "claimgate.mjs")
    rc, out, err = run(["node", mjs, "lint-receipt", receipt_path], root)
    if rc is None:
        return "ERROR", "claimgate.mjs", err[:200]
    # R5 mismatch surfaces as a violation -> nonzero exit
    return ("PASS" if rc == 0 else "FAIL"), "claimgate.mjs R5", f"recompute exit {rc}"

def _declared_tier(receipt, key, receipt_path, root):
    v = (receipt.get("verification") or {}).get(key)
    if not v or "cmd" not in v:
        return "SKIP", None, f"receipt declares no verification.{key}"
    rc, out, err = run(v["cmd"], root)
    if rc is None:
        return "ERROR", " ".join(v["cmd"][:2]), err[:200]
    expect = v.get("expect", {})
    # the declared cmd should have written its own receipt; if expect names fields,
    # re-open the produced json and check them (re-derive, don't trust stdout)
    ok = rc == 0
    ev = v.get("result_path")
    if expect and ev and os.path.exists(os.path.join(root, ev)):
        try:
            produced = load(os.path.join(root, ev))
            for k, want in expect.items():
                if produced.get(k) != want:
                    return "FAIL", ev, f"{k}={produced.get(k)} != expected {want}"
        except Exception as e:
            return "ERROR", ev, str(e)[:120]
    return ("PASS" if ok else "FAIL"), (ev or " ".join(v["cmd"][:2])), f"exit {rc}"

def tier2(receipt_path, receipt, root):
    return _declared_tier(receipt, "tier2", receipt_path, root)

def tier3(receipt_path, receipt, root):
    return _declared_tier(receipt, "tier3", receipt_path, root)

def tier4(receipt_path, receipt, root):
    d = os.path.dirname(receipt_path)
    cand = [os.path.join(d, n) for n in ("AUDIT_VERDICT.md", "audit_verdict.md")]
    found = next((c for c in cand if os.path.exists(c)), None)
    if not found:
        return "SKIP", None, "no sibling AUDIT_VERDICT.md (unaudited)"
    head = open(found).read(600).upper()
    if "TAINTED" in head or "FATAL" in head:
        return "FAIL", os.path.relpath(found, root), "fresh audit headline is TAINTED/FATAL"
    if "CLEAN" in head:
        return "PASS", os.path.relpath(found, root), "fresh audit affirms CLEAN"
    return "SKIP", os.path.relpath(found, root), "audit present but headline not machine-readable"

TIERS = [("tier0", tier0), ("tier1", tier1), ("tier2", tier2), ("tier3", tier3), ("tier4", tier4)]

def main():
    args = sys.argv[1:]
    receipt_path = next((a for a in args if not a.startswith("--")), None)
    if not receipt_path or not os.path.exists(receipt_path):
        sys.stderr.write("usage: claim_verify <receipt.json> [--require tier0,tier2] [--json]\n")
        sys.exit(2)
    require = set()
    if "--require" in args:
        require = set(args[args.index("--require") + 1].split(","))
    root = repo_root(receipt_path)
    try:
        receipt = load(receipt_path)
    except Exception as e:
        sys.stderr.write(f"claim_verify: bad receipt: {e}\n"); sys.exit(2)

    results, claim_verdicts = [], []
    for name, fn in TIERS:
        status, ev, detail = fn(receipt_path, receipt, root)
        results.append({"tier": name, "status": status, "evidence_ref": ev, "detail": detail})
        if status in ("PASS", "FAIL"):
            claim_verdicts.append({"claim": name, "verdict": "pass" if status == "PASS" else "fail",
                                   "evidence_ref": ev})

    failed = [r for r in results if r["status"] in ("FAIL", "ERROR")]
    # a --require tier that did not actually PASS is itself a failure
    req_unmet = [t for t in require if not any(r["tier"] == t and r["status"] == "PASS" for r in results)]
    verified = [r["tier"] for r in results if r["status"] == "PASS"]
    unverified = [r["tier"] for r in results if r["status"] == "SKIP"]

    if failed or req_unmet:
        verdict = "REJECTED"
    elif require:
        verdict = "VERIFIED"           # all required tiers passed
    else:
        verdict = "VERIFIED_PARTIAL"    # nothing failed, but depth was not required

    report = {
        "tool": "claim_verify",
        "receipt": os.path.relpath(receipt_path, root),
        "verdict": verdict,
        "verified_tiers": verified,
        "unverified_tiers": unverified,           # SKIPPED — explicitly NOT passed
        "required": sorted(require),
        "required_unmet": req_unmet,
        "tier_results": results,
        "claim_verdicts": claim_verdicts,          # Lev-shaped, for `lev gate validate`
    }
    print(json.dumps(report, indent=1))
    sys.exit(0 if verdict.startswith("VERIFIED") else 1)

if __name__ == "__main__":
    main()
