#!/usr/bin/env python3
"""Audit-response ticks for the welded v8 manifold.

Executes the four refinements demanded by the 2026-07-18 external cross-audit
(deepseek-v4-pro / grok-4.5 / kimi-k2.5 convergent findings):

  T1 circularity ablation — recompute the base frontier on (a) the two REAL
     v7 packets alone, (b) the seven internal packets alone, (c) all nine.
     If the frontier from reality alone differs, the circularity charge has
     a computed witness; if it agrees, the charge loses its packet-selection
     leg (grammar-level circularity remains open).
  T2 provenance binding — recompute both real packets from the hash-bound
     upstream receipts and require digest equality with the archived source
     packet set; verify vendored input hashes.
  T3 plurality probe — for each pair of final-frontier bases, print the
     presumption vectors and the exact component trade-off that keeps them
     incomparable; a pair with no trade-off is decorative and is flagged.
  T4 geometry tally + revival scope — count whole-manifold candidates per
     geometry profile (silent-filter check) and list ALL bases revived by a
     later layer, testing whether the revival law fired only for
     classical_distribution (ad-hoc concern recorded as open caveat G1).

Claim ceiling: packet-relative diagnostics of the welded lane; no promotion.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE))

from common import digest, write_json  # noqa: E402
import source_packets_v8 as spv8  # noqa: E402
from base_mss_engine import run as run_base  # noqa: E402

MANIFOLD = ENGINE.parent
RESULTS = MANIFOLD / "results"

REAL_IDS = {"v7_contextuality_heldout_relation", "v7_ring_presentation_relation"}


def filtered_source(source: dict, keep) -> dict:
    out = dict(source)
    out["base_packets"] = [p for p in source["base_packets"] if keep(p)]
    return out


def main() -> int:
    source = json.loads((RESULTS / "source_packets.json").read_text())
    whole = json.loads((RESULTS / "whole_manifold.json").read_text())

    # T1 ablation
    frontiers = {}
    for name, keep in [
        ("real_only", lambda p: p["packet_id"] in REAL_IDS),
        ("internal_only", lambda p: p["packet_id"] not in REAL_IDS),
        ("all_nine", lambda p: True),
    ]:
        sub = filtered_source(source, keep)
        base = run_base(sub)
        frontiers[name] = {
            "packets": len(sub["base_packets"]),
            "calibration_frontier": base["calibration_frontier"],
            "heldout_frontier": base["heldout_frontier"],
        }
    t1_agree = (frontiers["real_only"]["heldout_frontier"]
                == frontiers["all_nine"]["heldout_frontier"])

    # T2 provenance
    recomputed = {p["packet_id"]: p["packet_digest"] for p in spv8.real_packets()}
    archived = {p["packet_id"]: p["packet_digest"]
                for p in source["base_packets"] if p["packet_id"] in REAL_IDS}
    t2_digests_match = recomputed == archived
    hash_lines = (MANIFOLD / "inputs" / "INPUT_HASHES.sha256").read_text().split()
    t2_vendored_ok = True
    for h, rel in zip(hash_lines[0::2], hash_lines[1::2]):
        t2_vendored_ok &= hashlib.sha256(
            (MANIFOLD / "inputs" / rel).read_bytes()).hexdigest() == h
    tick = json.loads((MANIFOLD.parent / "kernel_tick" / "receipts"
                       / "tick_receipt_20260718.json").read_text())
    t2_chain = tick["predecessor_bindings"]["source_sha256"].startswith("sha256:5cc45b90")

    # T3 plurality probe on base evaluations (all nine packets)
    base_full = json.loads((RESULTS / "base_mss.json").read_text())
    evals = base_full["candidate_evaluations"]
    order = None
    vectors = {}
    for name in ("finite_relation", "finite_automaton", "classical_distribution"):
        row = evals.get(name)
        if row and "presumption_vector" in row:
            order = order or row["presumption_vector_order"]
            vectors[name] = [row["presumption_vector"][k] for k in order]
    tradeoffs = {}
    names = [n for n in vectors]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            va, vb = vectors[a], vectors[b]
            a_better = [k for k, (x, y) in enumerate(zip(va, vb)) if x < y]
            b_better = [k for k, (x, y) in enumerate(zip(va, vb)) if x > y]
            tradeoffs[f"{a}_vs_{b}"] = {
                "a_strictly_better_components": a_better,
                "b_strictly_better_components": b_better,
                "incomparable": bool(a_better) and bool(b_better),
                "decorative_tie": not a_better and not b_better,
            }

    # T4 geometry tally + revival scope
    profiles = {}
    revived = sorted({c.rsplit("__", 2)[0] for c in whole["final_frontier"]}
                     - set(json.loads((RESULTS / "base_mss.json").read_text())
                           ["heldout_frontier"]))
    for cid in whole["candidate_evaluations"]:
        key = cid.rsplit("__", 1)[-1]
        profiles[key] = profiles.get(key, 0) + 1
    t4_counts_uniform = len(set(profiles.values())) <= 1 if profiles else None

    checks = {
        "T1_real_only_frontier_matches_full": t1_agree,
        "T2_real_packet_digests_bound_to_upstream": t2_digests_match,
        "T2_vendored_hashes_verified": t2_vendored_ok,
        "T2_tick_chain_to_live_sim_lock": t2_chain,
        # only pairs that BOTH sit on the base frontier must be incomparable;
        # a dominated pair is a witness (why it lost), not a failure
        "T3_frontier_pair_incomparable_with_witness": tradeoffs[
            "finite_relation_vs_finite_automaton"]["incomparable"],
        "T3_classical_distribution_base_domination_witnessed": not tradeoffs[
            "finite_relation_vs_classical_distribution"]["incomparable"],
        "T4_no_silent_geometry_filter": bool(t4_counts_uniform) if profiles else False,
    }
    result = {
        "schema": "ratchet.v8.audit-response-ticks.v1",
        "T1_ablation_frontiers": frontiers,
        "T2_provenance": {
            "recomputed_digests": recomputed,
            "archived_digests": archived,
        },
        "T3_presumption_vectors": vectors,
        "T3_vector_order": order,
        "T3_tradeoffs": tradeoffs,
        "T4_geometry_profile_counts": profiles,
        "T4_revived_candidates": revived,
        "open_caveats": {
            "G1_revival_rule_scope": (
                "revival law observed firing for classical_distribution only; "
                "whether it is candidate-agnostic is untested until a second "
                "geometry-native candidate exists"),
            "G2_grammar_level_circularity": (
                "packet-selection circularity is answered by T1; circularity "
                "between the candidate grammar and the shared 4-bit word "
                "format remains open and needs an out-of-grammar packet"),
        },
        "checks": checks,
        "all_pass": all(v for v in checks.values() if v is not None),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": ("packet-relative diagnostics of the welded manifold "
                          "lane; no scientific, physical, or canonical claim"),
    }
    result["result_digest"] = digest(result)
    out = RESULTS / "audit_response_ticks.json"
    write_json(out, result)
    print(json.dumps({"all_pass": result["all_pass"], "checks": checks,
                      "real_only_frontier": frontiers["real_only"]["heldout_frontier"],
                      "full_frontier": frontiers["all_nine"]["heldout_frontier"]},
                     sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
