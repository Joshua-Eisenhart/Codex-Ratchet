#!/usr/bin/env python3
"""lev_qit_bridge_stream_host_adapter -- lift engines/lev_bridge_stream.json
(the per-tick {tick, belief_bloch, surprise_bits, fe_gradient} signal stream
from lev_bridge_sim.py) into the document shape the live Lev ingester requires
(core/eval/src/qit-bridge-stream.ts: schema_version
constraint_core.lev_bridge_stream.v1 + classification + promotion_allowed +
claim_ceiling + contiguous ticks). Additive; the producer sim and the Lev
ingester are both left untouched.

Header fields only -- tick payloads pass through verbatim. The live negative
control is the raw file itself: the Lev parser rejects it with
stream_schema_mismatch.

classification="scratch_diagnostic". promotion_allowed=False.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "..", "engines", "lev_bridge_stream.json")
OUT = os.path.join(HERE, "..", "engines", "lev_bridge_stream_host_adapted.json")

LEV_SCHEMA = "constraint_core.lev_bridge_stream.v1"


def contiguous_from_zero(stream):
    ticks = sorted(t["tick"] for t in stream)
    return ticks == list(range(len(ticks)))


def main():
    source = json.load(open(SOURCE))
    stream = source["stream"]

    ok_shape = (
        len(stream) > 0
        and contiguous_from_zero(stream)
        and all(
            isinstance(t["tick"], int)
            and len(t["belief_bloch"]) == 3
            and all(isinstance(v, (int, float)) for v in t["belief_bloch"])
            and isinstance(t["surprise_bits"], (int, float))
            and isinstance(t["fe_gradient"], (int, float))
            for t in stream
        )
    )
    print(f"  source ticks: {len(stream)}, contiguous-from-zero + finite fields: {ok_shape}")
    if not ok_shape:
        print("FAIL lev_qit_bridge_stream_host_adapter (source stream malformed)")
        return 1

    adapted = {
        "schema_version": LEV_SCHEMA,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "claim_ceiling": (
            "per-tick signal stream measurement from the QIT bridge demo world; "
            "evidence for Lev attention/novelty wiring only -- no graph, mesh, "
            "runtime, Axis0, or FEP admission"
        ),
        "source_sim": "lev_bridge_sim.py",
        "source_demo_world": source.get("demo_world"),
        "source_schema_note": source.get("schema"),
        "stream": stream,
    }
    with open(OUT, "w") as fh:
        json.dump(adapted, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("PASS lev_qit_bridge_stream_host_adapter")
    print(f"ALL_GATES: PASS -> {os.path.normpath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
