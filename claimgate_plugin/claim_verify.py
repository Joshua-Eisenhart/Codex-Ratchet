#!/usr/bin/env python3
"""
claim_verify v2 — the higher-level claimgate: a TIER-DISPATCHER whose pass-policy
lives OUTSIDE the producing agent's write-control.

v1 was red-teamed (2026-07-20) and had 4 confirmed holes: the receipt declared its
own tier2/3 command (["true"] passed), a builder-written AUDIT_VERDICT.md passed
tier4, a substring bug let "NOT CLEAN" pass, and a tier2 command could manufacture
the tier4 audit file. All four share one root: the agent authored its own
pass-criteria. v2 closes that root, following the Lev dev's approved design
(observation -> deterministic measurement -> decision; operator/agent never
assembles methodology; external evaluator policy).

    claim_verify <receipt.json> [--registry gate_registry.json] [--json]
        exit 0 = VERIFIED           (every required tier passed)
        exit 1 = REJECTED           (a required tier failed / producer authored policy)
        exit 3 = INSUFFICIENT_DEPTH (nothing failed but required depth not met)
        exit 2 = usage / IO error

Policy source (all EXTERNAL to the receipt):
  - which tiers a claim needs           -> gate_registry.claim_kinds[receipt.claim_kind]
  - the argv for tier2/tier3            -> gate_registry.gates[...] (NEVER receipt-declared)
  - tier4 audit admissibility           -> exact verdict token + auditor identity != producer
                                           + a current evalcheck calibration receipt
A receipt that tries to declare its own verification.*.cmd is REJECTED outright.

No third-party deps. Python 3.
"""
import json, os, subprocess, sys, hashlib, glob

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

def sha(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except Exception:
        return None

# ---- tiers. status in {PASS, FAIL, SKIP, ERROR}; SKIP never counts as passed ----

def tier0(receipt_path, receipt, root, reg):
    py = os.path.join(root, "claimgate", "claimgate.py")
    if os.path.exists(py):
        rc, out, err = run(["python3", py, receipt_path], root)
        tool = "claimgate/claimgate.py"
    else:
        mjs = os.path.join(root, "claimgate_plugin", "claimgate.mjs")
        rc, out, err = run(["node", mjs, "lint-receipt", receipt_path, "--rules",
                            os.path.join(root, "claimgate_plugin", "rules_ratchet.json")], root)
        tool = "claimgate.mjs"
    if rc is None:
        return "ERROR", tool, err[:200]
    return ("PASS" if rc == 0 else "FAIL"), tool, f"{tool} exit {rc}"

def tier1(receipt_path, receipt, root, reg):
    if "recompute" not in receipt:
        return "SKIP", None, "no recompute contract declared"
    mjs = os.path.join(root, "claimgate_plugin", "claimgate.mjs")
    rc, out, err = run(["node", mjs, "lint-receipt", receipt_path], root)
    if rc is None:
        return "ERROR", "claimgate.mjs", err[:200]
    # honest caveat: recompute proves internal consistency of claim-vs-own-raw,
    # NOT that the raw itself is genuine (that needs the replay tier / controlled run)
    return ("PASS" if rc == 0 else "FAIL"), "claimgate.mjs R5", f"recompute (internal-consistency) exit {rc}"

def _registered_tier(tier_key, receipt, root, reg):
    # HARD FAIL if the producer tried to author its own verification policy.
    v = (receipt.get("verification") or {}).get(tier_key)
    if isinstance(v, dict) and "cmd" in v:
        return "FAIL", None, f"receipt declared its own {tier_key}.cmd — producer-authored verification is forbidden (policy must be external)"
    kind = reg["claim_kinds"].get(receipt.get("claim_kind"))
    if not kind:
        return "SKIP", None, f"claim_kind '{receipt.get('claim_kind')}' names no {tier_key} gate"
    gate_name = kind.get(f"{tier_key}_gate")
    if not gate_name:
        return "SKIP", None, f"claim_kind declares no {tier_key} gate"
    gate = reg["gates"].get(gate_name)
    if not gate:
        return "ERROR", gate_name, "registry gate missing"
    rc, out, err = run(gate["cmd"], root)          # argv from REGISTRY, not receipt
    if rc is None:
        return "ERROR", gate_name, err[:200]
    # re-derive from the produced result file (do not trust stdout/exit alone)
    rp = gate.get("result_path")
    expect = gate.get("expect", {})
    if rp and expect:
        full = os.path.join(root, rp)
        if not os.path.exists(full):
            return "FAIL", gate_name, f"gate produced no result at {rp}"
        try:
            produced = load(full)
        except Exception as e:
            return "ERROR", rp, str(e)[:120]
        for k, want in expect.items():
            if produced.get(k) != want:
                return "FAIL", rp, f"{k}={produced.get(k)} != {want}"
        return "PASS", rp, f"{gate_name}: {', '.join(f'{k}={want}' for k, want in expect.items())}"
    return ("PASS" if rc == 0 else "FAIL"), gate_name, f"{gate_name} exit {rc}"

def tier2(receipt_path, receipt, root, reg):
    return _registered_tier("tier2", receipt, root, reg)

def tier3(receipt_path, receipt, root, reg):
    return _registered_tier("tier3", receipt, root, reg)

def _read_audit_verdict(path):
    """Exact machine-readable token only. A fenced/keyed 'verdict: CLEAN|TAINTED|FATAL'
    or a bare first-line token. Substring matching ('NOT CLEAN' contains 'CLEAN') is banned."""
    txt = open(path).read()
    for line in txt.splitlines():
        s = line.strip().lower()
        for key in ("verdict:", "audit verdict:", "audit_verdict:"):
            if s.startswith(key):
                tok = s[len(key):].strip().strip("`*_ ").split()[0].upper() if s[len(key):].strip() else ""
                if tok in ("CLEAN", "TAINTED", "FATAL"):
                    return tok
    return None  # no machine-readable verdict token -> not admissible

def _auditor_identity(path):
    for line in open(path).read().splitlines():
        s = line.strip().lower()
        if s.startswith("auditor:"):
            return line.split(":", 1)[1].strip()
    return None

def tier4(receipt_path, receipt, root, reg):
    pol = reg.get("audit_policy", {})
    d = os.path.dirname(receipt_path)
    found = next((os.path.join(d, n) for n in ("AUDIT_VERDICT.md", "audit_verdict.md")
                  if os.path.exists(os.path.join(d, n))), None)
    if not found:
        return "SKIP", None, "no sibling audit (unaudited)"
    verdict = _read_audit_verdict(found)
    if verdict is None:
        return "FAIL", os.path.relpath(found, root), "audit has no exact 'verdict: CLEAN|TAINTED|FATAL' token (prose headline not admissible)"
    if verdict in ("TAINTED", "FATAL"):
        return "FAIL", os.path.relpath(found, root), f"audit verdict {verdict}"
    # verdict == CLEAN: now prove the audit is not self-authored and its auditor is calibrated
    if pol.get("require_auditor_identity"):
        auditor = _auditor_identity(found)
        producer = receipt.get("produced_by") or receipt.get("builder") or receipt.get("author")
        if not auditor:
            return "FAIL", os.path.relpath(found, root), "audit CLEAN but names no 'auditor:' identity — cannot prove it isn't self-authored"
        if producer and auditor.lower() == str(producer).lower():
            return "FAIL", os.path.relpath(found, root), f"auditor '{auditor}' == producer — self-audit forbidden"
    if pol.get("require_calibration"):
        ok, why = _auditor_calibrated(auditor, root, reg)
        if not ok:
            return "FAIL", os.path.relpath(found, root), f"audit CLEAN but auditor not freshly calibrated: {why}"
    return "PASS", os.path.relpath(found, root), f"audit CLEAN, auditor '{auditor}' fresh-calibrated"

def _auditor_calibrated(auditor, root, reg):
    # NO static file trust (a checked-in *.calibration.json is forgeable — the
    # workflow proved it FATAL). Calibration is RE-DERIVED per run: evalcheck is
    # executed fresh against a REGISTRY-FIXED sealed deck for this auditor. An
    # auditor with no registered calibration gate is, by definition, not calibrated.
    pol = reg.get("audit_policy", {})
    gate = (pol.get("calibration_gates") or {}).get(auditor)
    if not gate or "deck" not in gate:
        return (False, f"auditor '{auditor}' has no registered calibration gate (unregistered auditors cannot self-certify)")
    deck = os.path.join(root, gate["deck"])
    if not os.path.exists(deck):
        return (False, f"registered deck missing: {gate['deck']}")
    rc, out, err = run(["node", os.path.join(root, "claimgate_plugin", "evalcheck.mjs"), deck], root)
    if rc is None:
        return (False, f"evalcheck did not run: {err[:80]}")
    try:
        rep = json.loads(out)
    except Exception:
        return (False, "evalcheck output unparseable")
    return (rep.get("verdict") == "EVALUATOR_CALIBRATED",
            f"fresh evalcheck on {gate['deck']}: {rep.get('verdict')}")

TIERS = [("tier0", tier0), ("tier1", tier1), ("tier2", tier2), ("tier3", tier3), ("tier4", tier4)]

def main():
    args = sys.argv[1:]
    receipt_path = next((a for a in args if not a.startswith("--")), None)
    if not receipt_path or not os.path.exists(receipt_path):
        sys.stderr.write("usage: claim_verify <receipt.json> [--registry gate_registry.json]\n"); sys.exit(2)
    receipt_path = os.path.abspath(receipt_path)  # subprocesses run with cwd=root; the path must be absolute
    # root = the SCRIPT's repo (fixed), NOT the receipt's — a receipt can live
    # anywhere (a /tmp fixture, a Lev-supplied path); the tools/registry/decks are
    # fixed relative to this file.
    here = os.path.dirname(os.path.abspath(__file__))
    root = repo_root(here)
    reg_path = args[args.index("--registry") + 1] if "--registry" in args else \
        os.path.join(here, "gate_registry.json")
    try:
        receipt = load(receipt_path)
        reg = load(reg_path)
    except Exception as e:
        sys.stderr.write(f"claim_verify: {e}\n"); sys.exit(2)

    kind = reg["claim_kinds"].get(receipt.get("claim_kind"))
    # an unclassified receipt cannot resolve its required depth -> never VERIFIED
    unclassified = kind is None
    required = set(kind["required_tiers"]) if kind else {"tier0"}

    # cross-tier bootstrap guard: pin the sibling AUDIT file(s) by hash BEFORE any
    # tier runs; a registered gate writing its OWN result_path is expected, but no
    # tier may create/modify the tier4 audit evidence.
    d = os.path.dirname(receipt_path)
    pinned = {}
    for n in ("AUDIT_VERDICT.md", "audit_verdict.md"):
        p = os.path.join(d, n)
        pinned[p] = sha(p)

    results, claim_verdicts, tamper = [], [], []
    for name, fn in TIERS:
        status, ev, detail = fn(receipt_path, receipt, root, reg)
        # after each tier, detect if it manufactured/altered a pinned evidence file
        for p, h0 in list(pinned.items()):
            h1 = sha(p)
            if h1 != h0:
                tamper.append({"tier": name, "path": os.path.relpath(p, root),
                               "change": "created" if h0 is None else "modified"})
                pinned[p] = h1  # re-pin so we attribute once
        results.append({"tier": name, "status": status, "evidence_ref": ev, "detail": detail})
        if status in ("PASS", "FAIL"):
            claim_verdicts.append({"claim": name, "verdict": "pass" if status == "PASS" else "fail", "evidence_ref": ev})

    failed = [r for r in results if r["status"] in ("FAIL", "ERROR")]
    req_unmet = [t for t in required if not any(r["tier"] == t and r["status"] == "PASS" for r in results)]
    verified = [r["tier"] for r in results if r["status"] == "PASS"]
    unverified = [r["tier"] for r in results if r["status"] == "SKIP"]

    if tamper:
        verdict, code = "REJECTED", 1           # cross-tier evidence bootstrap = fatal
    elif failed:
        verdict, code = "REJECTED", 1
    elif unclassified or req_unmet:
        verdict, code = "INSUFFICIENT_DEPTH", 3  # unclassified, or required depth not met
    else:
        verdict, code = "VERIFIED", 0

    report = {
        "tool": "claim_verify", "version": 2,
        "receipt": os.path.relpath(receipt_path, root),
        "claim_kind": receipt.get("claim_kind"),
        "verdict": verdict,
        "required_tiers": sorted(required),
        "verified_tiers": verified,
        "unverified_tiers": unverified,          # SKIPPED — explicitly NOT passed
        "required_unmet": req_unmet,
        "tamper_events": tamper,                 # a tier that manufactured another tier's evidence
        "tier_results": results,
        "claim_verdicts": claim_verdicts,
    }
    print(json.dumps(report, indent=1))
    sys.exit(code)

if __name__ == "__main__":
    main()
