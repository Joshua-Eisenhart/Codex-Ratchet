#!/usr/bin/env python3
"""qit_fep_surprise_stream_lev_emitter -- companion emitter that closes the UP-97 emit gap.

UP-97 (qit_fep_surprise_stream_sim.py) computes the per-tick belief/surprise trace of the
running engine but emits only the bare surprise list (stream_bits); the per-tick
{tick, belief_bloch, fe_gradient} records that Lev's stream port
(core/eval/src/qit-bridge-stream.ts, schema constraint_core.lev_bridge_stream.v1) requires
are computed internally and dropped. This companion re-runs UP-97's OWN generator (imported,
not reimplemented) and records what UP-97 discards, wrapped in the v1 header.

Definitions match the spec'd adapter (lev_bridge_sim.py LevBridge.tick):
  surprise_bits = S(obs_t || belief_before_update)   [Umegaki, bits -- UP-97's own S_rel]
  fe_gradient   = surprise_before - S(obs_t || belief_after_update)  [FE reduction by the update]
  belief_bloch  = Bloch vector of the belief AFTER the update

GATE (falsifiable): the recomputed surprise trace must equal UP-97's published stream_bits
(round-to-4 identical, all 30 ticks). If the traces diverge, this is NOT UP-97's engine
trace and the emitter FAILS. The live negative control is UP-97's raw results file itself:
the Lev parser rejects it (stream_schema_mismatch).

scratch_diagnostic, promotion_allowed=false. Evidence-only; no Lev graph/mesh/runtime claim.
"""
import importlib.util
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
UP97 = os.path.join(HERE, "qit_fep_surprise_stream_sim.py")
UP97_RESULTS = os.path.join(HERE, "qit_fep_surprise_stream_sim_results.json")
OUT = os.path.join(HERE, "..", "engines", "qit_fep_surprise_stream_v1.json")

spec = importlib.util.spec_from_file_location("up97", UP97)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def stream_records(switch_at=15, n=30, terr_a=0, terr_b=2, lr=0.5):
    """UP-97's stream() with the learning branch, recording full per-tick records."""
    belief = m.dm([0, 0, 0])
    obs = m.dm([0.6, 0.3, 0.2])
    records = []
    for t in range(n):
        ti = terr_b if t >= switch_at else terr_a
        obs = m.tflow(ti, obs)
        surprise = m.S_rel(obs, belief)
        belief = m.dm((1 - lr) * m.bvec(belief) + lr * m.bvec(obs))
        fe_gradient = surprise - m.S_rel(obs, belief)
        records.append({
            "tick": t,
            "belief_bloch": [round(float(x), 4) for x in m.bvec(belief)],
            "surprise_bits": round(float(surprise), 4),
            "fe_gradient": round(float(fe_gradient), 4),
        })
    return records


def main():
    records = stream_records()

    published = json.load(open(UP97_RESULTS))["stream_bits"]
    recomputed = [r["surprise_bits"] for r in records]
    trace_match = len(published) == len(recomputed) and all(
        abs(a - b) < 5e-5 for a, b in zip(published, recomputed)
    )
    print(f"  recomputed trace == UP-97 published stream_bits (30 ticks): {trace_match}")
    if not trace_match:
        print("FAIL qit_fep_surprise_stream_lev_emitter (trace mismatch -- not UP-97's engine run)")
        return 1

    doc = {
        "schema_version": "constraint_core.lev_bridge_stream.v1",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "claim_ceiling": (
            "per-tick FEP surprise stream of the UP-97 engine run (Umegaki bits); "
            "evidence-only for Lev's stream port -- no graph, mesh, runtime, Axis0, "
            "or FEP admission"
        ),
        "source_sim": "qit_fep_surprise_stream_sim.py (UP-97) via companion emitter",
        "signature": {
            "predictable_phase_mean_bits": round(float(np.mean(recomputed[5:15])), 4),
            "regime_shift_spike_bits": round(float(max(recomputed[15:19])), 4),
            "relearned_phase_mean_bits": round(float(np.mean(recomputed[25:])), 4),
        },
        "stream": records,
    }
    with open(OUT, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    sig = doc["signature"]
    print(f"  signature: predictable {sig['predictable_phase_mean_bits']}, "
          f"spike {sig['regime_shift_spike_bits']}, relearned {sig['relearned_phase_mean_bits']}")
    print("PASS qit_fep_surprise_stream_lev_emitter")
    print(f"ALL_GATES: PASS -> {os.path.normpath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
