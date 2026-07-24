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
import os
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


def _engine_metrics(r):
    """{engine: {metric_id: value}} from engine_values keys '<engine>_<metric_id>'.

    Keeps the METRIC ID, not just the first number. The prior version took the
    first prefixed key and compared across engines regardless of which observable
    it was -- so `jax_entropy=0.5` and `julia_unrelated=0.5` counted as agreement.
    An external audit (2026-07-24) named this; a hostile fixture confirmed it
    passed. Agreement is only meaningful between the SAME measured quantity.
    """
    ev = _d(r, "engine_values")
    out = {}
    for eng in AUTHORITATIVE:
        for k, v in ev.items():
            kl = str(k).lower()
            if kl.startswith(eng + "_") and isinstance(v, (int, float)) and not isinstance(v, bool):
                out.setdefault(eng, {})[kl[len(eng) + 1:]] = float(v)
    return out


def _engine_values(r):
    """Back-compat shim: {engine: one value} (first metric). Never used for the
    agreement test -- that now goes through _engine_metrics by metric ID."""
    return {e: next(iter(m.values())) for e, m in _engine_metrics(r).items() if m}


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

    # R1b superseded (owner 2026-07-22 new spec): numpy is ALLOWED in a CONTAINED role — the
    # downstream CPU satellite (post-hoc pysindy/sympy/scipy on JAX output), NEVER load_bearing and
    # NEVER the sim engine. The containment is enforced structurally below: a numeric sim must show
    # >=2 authoritative engines (JAX base + Julia authoritative) that AGREE and whose jax leg
    # RE-DERIVES. That requirement makes numpy incapable of being the workhorse-in-disguise — the
    # load-bearing witness must provably come from the engines, so numpy can only sit in the satellite.

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

    # CONSISTENCY: a load_bearing engine cannot be marked engines_ran=False. Contradictory
    # metadata (jax load_bearing but engines_ran.jax=False) is a lie on its face — reject it.
    contradiction = sorted(e for e in load_bearing & set(AUTHORITATIVE)
                           if engines_ran.get(e) is False)
    if contradiction:
        return 1, (f"REJECT — inconsistent metadata: {contradiction} labeled load_bearing but "
                   f"engines_ran says False. A load-bearing engine must record engines_ran=True.")

    # (A) EVIDENCE: >=2 authoritative engines with load_bearing label AND a numeric value.
    values = _engine_values(receipt)
    verified = sorted(e for e in AUTHORITATIVE if e in load_bearing and e in values)
    if len(verified) < 2:
        return 1, (f"REJECT — a numeric sim must show >=2 authoritative engines each load_bearing AND "
                   f"carrying a numeric engine_value; verified={verified or 'none'}. A self-reported "
                   f"engines_ran boolean is NOT evidence — record the engine's computed value.")

    # Values must AGREE on the SAME METRIC ID. Comparing an engine's entropy to
    # another engine's unrelated number is not agreement (audit 2026-07-24).
    metrics = _engine_metrics(receipt)
    shared = set.intersection(*(set(metrics[e]) for e in verified)) if verified else set()
    if not shared:
        per_engine = {e: sorted(metrics.get(e, {})) for e in verified}
        return 1, (f"REJECT — engines share no common metric ID, so 'agreement' is undefined: "
                   f"{per_engine}. Two engines must report the SAME measured quantity "
                   f"(engine_values keys '<engine>_<metric_id>' with matching metric_id).")
    div = 0.0
    worst = None
    for m in sorted(shared):
        vals = [metrics[e][m] for e in verified]
        d = max(abs(a - b) for a in vals for b in vals)
        if d > div:
            div, worst = d, m
    if div > AGREE_TOL:
        return 1, (f"REJECT — authoritative engines DISAGREE on metric '{worst}': "
                   f"max divergence {div} > {AGREE_TOL} across {verified}.")

    # METADATA-ONLY mode (CI, where the sim env / jax leg is not installed): the numpy and
    # engine-count/agreement checks above need no env and fully catch the numpy bullshit;
    # only the jax re-derive is skipped. Local runs (pre-commit, Stop hook) do the re-derive.
    if os.environ.get("SEAL_METADATA_ONLY"):
        return 0, f"pass (metadata-only) — {len(verified)} engines {verified} agree (div {div:.1e}); no numpy"

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
    if not isinstance(receipt, dict):
        print("three_engine_seal: pass — not a sim-receipt object (list/scalar); N/A", file=sys.stderr)
        return 0
    code, message = check(receipt, argv[1])
    print("three_engine_seal: " + message, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
