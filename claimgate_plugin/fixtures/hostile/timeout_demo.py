#!/usr/bin/env python3
"""HOSTILE CONTROL FIXTURE HARNESS — class: timeout_hang.

Demonstrates claim_verify's timeout path WITHOUT waiting 900 s.

claim_verify.py run() (lines 39-44) wraps every gate invocation in
subprocess.run(..., timeout=900); subprocess.TimeoutExpired is caught by
`except Exception`, the hung child is killed, and run() returns rc=None.
_registered_tier (lines 98-99) maps rc=None to tier status ERROR; main()
counts ERROR among `failed` (line 240) so the verdict is REJECTED, exit 1
(lines 246-248). A hanging gate is therefore killed and BLOCKED — it can
never reach VERIFIED.

This harness mirrors run() byte-for-byte in shape, with the timeout scaled
900 -> 5 so the whole demonstration finishes in ~5 s. It then applies the
same rc->status->verdict mapping claim_verify applies, and reports TIMEOUT.

Exit code: 1 = timeout engaged, hang killed, mapped verdict REJECTED
               (the EXPECTED fail-closed outcome for this hostile class);
           0 = the hang gate somehow completed and passed (a GAP).
"""
import json, os, subprocess, sys, time

FIXTURE_MARKER = {
    "classification": "hostile_control_fixture",
    "promotion_allowed": False,
    "class": "timeout_hang",
}

HERE = os.path.dirname(os.path.abspath(__file__))
HANG_GATE = os.path.join(HERE, "hang_gate.py")
DEMO_TIMEOUT_S = 5       # stand-in for claim_verify's 900 s
PRODUCTION_TIMEOUT_S = 900


def run(cmd, cwd, timeout_s):
    """Same shape as claim_verify.run(); only the timeout constant differs."""
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout_s)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return None, "", str(e)


def main():
    t0 = time.monotonic()
    rc, out, err = run([sys.executable, HANG_GATE], HERE, DEMO_TIMEOUT_S)
    elapsed_s = round(time.monotonic() - t0, 2)

    timed_out = rc is None and "timed out" in err.lower()
    # claim_verify._registered_tier: rc is None -> ERROR; main(): ERROR -> REJECTED exit 1
    tier_status = "ERROR" if rc is None else ("PASS" if rc == 0 else "FAIL")
    verdict = "REJECTED" if tier_status in ("ERROR", "FAIL") else "VERIFIED"

    report = {
        "classification": "hostile_control_fixture",
        "promotion_allowed": False,
        "class": "timeout_hang",
        "gate_under_test": "claimgate_plugin/fixtures/hostile/hang_gate.py",
        "demo_timeout_s": DEMO_TIMEOUT_S,
        "production_timeout_s": PRODUCTION_TIMEOUT_S,
        "elapsed_s": elapsed_s,
        "harness_result": "TIMEOUT" if timed_out else ("EXIT_%s" % rc),
        "hang_killed": timed_out,
        "gate_stdout": out[:200],
        "gate_error": err[:200],
        "mapped_tier_status": tier_status,
        "mapped_claim_verify_verdict": verdict,
        "mapped_claim_verify_exit": 1 if verdict == "REJECTED" else 0,
        "note": "timeout scaled 900->5 for demonstration only; the rc->ERROR->REJECTED mapping is claim_verify's, unmodified",
    }
    print(json.dumps(report, indent=1))
    sys.exit(1 if verdict == "REJECTED" else 0)


if __name__ == "__main__":
    main()
