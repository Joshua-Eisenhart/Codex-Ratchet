#!/usr/bin/env python3
"""Compile the v8 welded packet set: Pack 183's seven source-derived packets
PLUS the two real system_v7 sim-derived packets (contextuality + ring).

This is the repo-native replacement for source_packets.py. Same output schema
(ratchet.pack183.source-packets.v1-compatible), so the downstream engines
(base_mss_engine, nesting_ratchet, whole_feedback_ratchet, verify) consume it
unchanged. Provenance:

  - vendored sources: system_v8/manifold/inputs/ (INPUT_HASHES.sha256)
  - real packets:     system_v8/inputs/receipts/normalized_source_tables.json
                      + system_v8/kernel_tick/receipts/tick_receipt_20260718.json

Claim ceiling: common finite source-derived comparison packets only; no base
structure admitted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from common import digest, file_sha256, write_json
import source_packets as sp

ENGINE = Path(__file__).resolve().parent
MANIFOLD = ENGINE.parent
V8 = MANIFOLD.parent

# repoint the pack's module paths at the vendored copies
sp.QCA_SOURCE = MANIFOLD / "inputs" / "finite_qca_runner_trajectories_v0_exact.py"
sp.ROOT = MANIFOLD
VENDORED_GCM = MANIFOLD / "inputs" / "finite_whole_gcm.py"
VENDORED_ALGEBRA = MANIFOLD / "inputs" / "finite_algebra.py"

TABLES = V8 / "inputs" / "receipts" / "normalized_source_tables.json"
TICK = V8 / "kernel_tick" / "receipts" / "tick_receipt_20260718.json"
VARS = ("h0", "h1", "p", "o")


def real_rows(handle: str) -> set[tuple[int, ...]]:
    tables = json.loads(TABLES.read_text())
    rows = {tuple(int(r[v]) for v in VARS)
            for s in tables["sources"] if s["handle"] == handle
            for r in s["rows"]}
    return rows


def real_packets() -> list[dict[str, Any]]:
    ctx = real_rows("src-1858a5f7dbbb248f")
    tick = json.loads(TICK.read_text())
    for r in tick["new_records"]:
        ctx.add((int(r["history"][0]), int(r["history"][1]),
                 int(r["probe"]), int(r["outcome"])))
    ring = real_rows("src-5cb0baaed60f7057")
    return [
        sp.packet(
            "v7_contextuality_heldout_relation",
            "system_v8/inputs/receipts/normalized_source_tables.json"
            "::src-1858a5f7dbbb248f + kernel_tick heldout rows",
            ["h0_variant", "h1_context_parity", "p_sign", "o_global_infeasible"],
            ctx,
            "source_observation",
        ),
        sp.packet(
            "v7_ring_presentation_relation",
            "system_v8/inputs/receipts/normalized_source_tables.json"
            "::src-5cb0baaed60f7057",
            ["h0", "h1", "p", "o"],
            ring,
            "source_observation",
        ),
    ]


def prior_modules_vendored():
    for p in (str(ENGINE), str(MANIFOLD / "inputs")):
        if p not in sys.path:
            sys.path.append(p)
    algebra = sp.load_module("finite_algebra", VENDORED_ALGEBRA)
    whole = sp.load_module("v8_prior_whole", VENDORED_GCM)
    return whole, algebra


def run() -> dict[str, Any]:
    whole, algebra = prior_modules_vendored()
    packets = sp.qca_packets()
    packets.extend([sp.gcm_packet(whole), sp.spinor_packet(algebra),
                    sp.octonion_packet(algebra)])
    real = real_packets()
    packets.extend(real)
    nesting = [
        sp.nesting_packet(whole, (0, 1), "nested_completion_baseline",
                          "source_observation"),
        sp.nesting_packet(whole, (0, 1, 2), "nested_completion_expanded",
                          "heldout_evolution_reoffer"),
    ]
    baseline = {tuple(tuple(s) for s in t)
                for t in nesting[0]["admissible_triples"]}
    expanded = {tuple(tuple(s) for s in t)
                for t in nesting[1]["admissible_triples"]}
    ctx_pkt = next(p for p in packets
                   if p["packet_id"] == "v7_contextuality_heldout_relation")
    ring_pkt = next(p for p in packets
                    if p["packet_id"] == "v7_ring_presentation_relation")
    checks = {
        "all_base_packets_width_four": all(r["width"] == 4 for r in packets),
        "qca_source_hash_retained": file_sha256(sp.QCA_SOURCE).startswith("sha256:"),
        "baseline_nested_nonempty": bool(baseline),
        "expansion_preserves_baseline": baseline <= expanded,
        "expansion_adds_configuration": bool(expanded - baseline),
        "real_contextuality_packet_nonempty": ctx_pkt["accepted_count"] > 0,
        "real_ring_packet_nonempty": ring_pkt["accepted_count"] > 0,
        "real_ring_has_continuation_conflict": any(
            w[:3] == v[:3] and w[3] != v[3]
            for w in ring_pkt["accepted_words"] for v in ring_pkt["accepted_words"]),
        "vendored_hashes_bound": (MANIFOLD / "inputs" / "INPUT_HASHES.sha256").exists(),
    }
    result = {
        "schema": "ratchet.v8.source-packets.v1",
        "base_packets": packets,
        "nesting_packets": nesting,
        "checks": checks,
        "all_pass": all(checks.values()),
        "selection_disclosure": (
            "seven four-coordinate calibration projections from preserved "
            "executable sources plus two real system_v7 sim-derived packets "
            "(contextuality with executed held-out rows; ring with real "
            "continuation conflicts); not neutral samples of all mathematics"
        ),
        "claim_ceiling": ("common finite source-derived comparison packets "
                          "only; no base structure admitted"),
    }
    result["result_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "base_packets": len(result["base_packets"]),
        "nesting_packets": len(result["nesting_packets"]),
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
