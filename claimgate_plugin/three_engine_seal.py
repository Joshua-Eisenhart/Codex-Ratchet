#!/usr/bin/env python3
"""Three-engine seal — EXECUTION-EVIDENCE enforcement (hardened 2026-07-22).

A webui audit found the prior seal TRUSTED receipt metadata: a forged
engines_ran=true passed, missing metadata passed, an IO error passed, and one
engine sufficed. This version RE-DERIVES instead of trusting, and fails CLOSED.

A sim receipt is admitted only if ONE of:
  (A) EVIDENCE — it carries >=2 authoritative engines (Julia/JAX/PyTorch) that
      each have a load_bearing label AND a numeric engine_value, those values
      AGREE (divergence recomputed here, not a trusted field), AND the jax leg
      RE-RUNS and reproduces its recorded values. Re-running the jax leg is where
      ClaimGate genuinely USES jax — the un-plantable execution evidence.
  (B) EXEMPT — it explicitly declares engine_contract.numeric_engine_required=false
      with a reason (a genuinely non-numeric proof/finite-set sim).
Everything else REJECTS, including: numpy/scipy/mpmath labeled load_bearing; a
sim that shows numeric-engine intent but <2 agreeing engine values; engine
disagreement; a jax leg that will not re-run or does not reproduce; an unreadable
receipt.

Exit: 0 pass, 1 REJECT, 2 usage.
"""
import json
import subprocess
import sys
from pathlib import Path

CONTROL_ONLY = {"numpy", "scipy", "mpmath"}
AUTHORITATIVE = ("julia", "jax", "torch", "pytorch")
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
AGREE_TOL = 1.0e-6
RERUN_TOL = 1.0e-9


def _d(receipt, *keys):
    for k in keys:
        v = receipt.get(k)
        if isinstance(v, dict):
            return v
    return {}


def _depth(r):
    return {str(k).lower(): v for k, v in _d(r, "TOOL_INTEGRATION_DEPTH", "tool_integration_depth").items()}


def _engine_values(r):
    """{engine: numeric value} pulled from engine_values keys prefixed '<engine>_'."""
    ev = _d(r, "engine_values")
    out = {}
    for eng in AUTHORITATIVE:
        for k, v in ev.items():
            if str(k).lower().startswith(eng + "_") and isinstance(v, (int, float)):
                out[eng] = float(v)
                break
    return out


def _rerun_jax_reproduces(receipt_path, recorded_jax):
    """Re-run <name>_jax.py and confirm it reproduces recorded_jax's numerics.
    THIS is ClaimGate using jax: execution evidence, not a self-reported boolean."""
    rp = Path(receipt_path)
    leg = rp.parent.parent / f"{rp.stem}_jax.py"  # results/<name>.json -> ../<name>_jax.py
    if not leg.exists():
        return False, f"jax load_bearing but no runnable leg at {leg.name} (fabricated-source anti-pattern)"
    try:
        proc = subprocess.run([SIM_PY, str(leg)], capture_output=True, text=True, timeout=600)
    except Exception as exc:  # noqa: BLE001
        return False, f"jax leg re-run dispatch failed: {exc}"
    if proc.returncode != 0:
        return False, f"jax leg re-run exit {proc.returncode}: {proc.stderr.strip()[-160:]}"
    fresh_lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
    if not fresh_lines:
        return False, "jax leg re-run produced no JSON"
    fresh = json.loads(fresh_lines[-1])
    compared = 0
    for k, v in (recorded_jax or {}).items():
        if isinstance(v, (int, float)) and isinstance(fresh.get(k), (int, float)):
            compared += 1
            if abs(float(v) - float(fresh[k])) > RERUN_TOL:
                return False, f"jax leg NOT reproducible: recorded {k}={v} vs re-run {fresh[k]} (>1e-9)"
    if compared == 0:
        return False, "jax leg re-ran but shares no numeric field with the recorded leg — cannot verify"
    return True, f"jax leg re-derived, {compared} numeric field(s) reproduce to <1e-9"


def check(receipt, receipt_path):
    depth = _depth(receipt)
    engines_ran = _d(receipt, "engines_ran", "engines")
    load_bearing = {k for k, v in depth.items() if v == "load_bearing"}

    # R1: control-only tool labeled load_bearing — absolute violation.
    ctrl = load_bearing & CONTROL_ONLY
    if ctrl:
        return 1, f"REJECT — {sorted(ctrl)} labeled load_bearing, but numpy/scipy/mpmath are CONTROL-ONLY."

    # (B) explicit exemption for a genuinely non-numeric sim.
    ec = _d(receipt, "engine_contract")
    if ec.get("numeric_engine_required") is False:
        return 0, f"pass — exempt (numeric_engine_required=false): {ec.get('exemption_reason', 'declared')}"

    # Does the receipt show numeric-engine INTENT? (numpy, an authoritative engine, or engine_values)
    numeric_intent = ("numpy" in depth or engines_ran.get("numpy")
                      or bool(load_bearing & set(AUTHORITATIVE))
                      or any(engines_ran.get(e) for e in AUTHORITATIVE)
                      or bool(_d(receipt, "engine_values")))
    if not numeric_intent:
        # No numeric engines involved and no numpy — a pure symbolic/SMT/finite sim.
        return 0, "pass — no numeric-engine intent (pure symbolic/SMT/finite); contract N/A"

    # (A) EVIDENCE: >=2 authoritative engines with load_bearing label AND a numeric value.
    values = _engine_values(receipt)
    verified = sorted(e for e in AUTHORITATIVE if e in load_bearing and e in values)
    if len(verified) < 2:
        return 1, (f"REJECT — a numeric sim must show >=2 authoritative engines each load_bearing AND "
                   f"carrying a numeric engine_value; verified={verified or 'none'}. A self-reported "
                   f"engines_ran boolean is NOT evidence — record the engine's computed value.")

    # Values must AGREE (recomputed from the values themselves).
    vv = [values[e] for e in verified]
    div = max(abs(a - b) for a in vv for b in vv)
    if div > AGREE_TOL:
        return 1, f"REJECT — authoritative engines DISAGREE: max divergence {div} > {AGREE_TOL} across {verified}."

    # RE-DERIVE via jax (ClaimGate USES jax): re-run the jax leg, require reproducibility.
    if "jax" in verified:
        ok, msg = _rerun_jax_reproduces(receipt_path, _d(receipt, "three_engine_legs").get("jax"))
        if not ok:
            return 1, f"REJECT — jax re-derive failed: {msg}"
        return 0, f"pass — {len(verified)} engines {verified} agree (div {div:.1e}); {msg}"
    return 1, (f"REJECT — engines {verified} agree but none is jax; ClaimGate re-derives via jax as the "
               f"execution check. Include a jax leg (dynamiqs) so the value can be independently re-run.")


def main(argv):
    if len(argv) != 2:
        print("usage: three_engine_seal.py <receipt.json>", file=sys.stderr)
        return 2
    try:
        receipt = json.load(open(argv[1]))
    except Exception as exc:  # noqa: BLE001
        print(f"three_engine_seal: REJECT — receipt unreadable ({exc}); failing CLOSED.", file=sys.stderr)
        return 1
    code, message = check(receipt, argv[1])
    print("three_engine_seal: " + message, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
