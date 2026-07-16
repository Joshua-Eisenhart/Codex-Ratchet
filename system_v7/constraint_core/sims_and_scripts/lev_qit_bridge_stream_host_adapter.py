#!/usr/bin/env python3
"""lev_qit_bridge_stream_host_adapter -- lift engines/lev_bridge_stream.json
(the per-tick {tick, belief_bloch, surprise_bits, fe_gradient} signal stream
from lev_bridge_sim.py) into the document shape the live Lev ingester requires
(plugins/sim-witness/src/qit-bridge-stream.ts: schema_version
constraint_core.lev_bridge_stream.v1 + classification + promotion_allowed +
claim_ceiling + contiguous ticks). Additive; the producer sim and the Lev
ingester are both left untouched.

Header fields only -- tick payloads pass through verbatim. The live negative
control is the raw file itself: the Lev parser rejects it with
stream_schema_mismatch.

classification="scratch_diagnostic". promotion_allowed=False.
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "..", "engines", "lev_bridge_stream.json")
OUT = os.path.join(HERE, "..", "engines", "lev_bridge_stream_host_adapted.json")

LEV_SCHEMA = "constraint_core.lev_bridge_stream.v1"


def contiguous_from_zero(stream):
    ticks = sorted(t["tick"] for t in stream)
    return ticks == list(range(len(ticks)))


def finite_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def adapt(source_path, out_path):
    with open(source_path, encoding="utf-8") as handle:
        source = json.load(handle)
    stream = source["stream"]

    ok_shape = (
        len(stream) > 0
        and contiguous_from_zero(stream)
        and all(
            isinstance(t["tick"], int)
            and not isinstance(t["tick"], bool)
            and len(t["belief_bloch"]) == 3
            and all(finite_number(v) for v in t["belief_bloch"])
            and finite_number(t["surprise_bits"])
            and finite_number(t["fe_gradient"])
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
    target = Path(out_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        json.dump(adapted, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("PASS lev_qit_bridge_stream_host_adapter")
    print(f"ALL_GATES: PASS -> {target}")
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Adapt a Codex QIT stream for the Lev sim-witness ingester")
    parser.add_argument("--source", default=SOURCE, help="Raw Codex bridge-stream JSON")
    parser.add_argument("--out", default=OUT, help="Adapted Lev bridge-stream JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    return adapt(args.source, args.out)


if __name__ == "__main__":
    sys.exit(main())
