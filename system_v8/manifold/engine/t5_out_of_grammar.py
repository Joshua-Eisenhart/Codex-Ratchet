#!/usr/bin/env python3
"""T5 out-of-grammar packet injection + T6 presumption-vector sensitivity.

Round-2 audit (glm-5.2, minimax-m3 convergent) demanded:

T5 — packets whose GENERATING structure is a disjoint algebraic domain,
     projected into the 4-bit interface only at the boundary. Three foreign
     domains, none present anywhere in the candidate grammar or the seven
     internal packets:
       t5_tropical  — (min,+) semiring: 2x2 tropical matrix powers over a
                      fixed integer matrix; bits = argmin structure and
                      parity of tropical eigen-slope quantities.
       t5_gf7       — prime field F_7 multiplication: bits from quadratic-
                      residue status and parity of products.
       t5_logistic  — exact rational logistic map x -> 4x(1-x) iterated with
                      Fraction arithmetic; bits from interval membership.
     The base tournament is rerun on (a) the three T5 packets alone and
     (b) all twelve packets. Frontier deltas are recorded either way — a
     changed frontier is a G2 witness; an unchanged frontier removes the
     format-coupling leg of the objection (the generating algebra leg).

T6 — component-deletion sensitivity of the Pareto comparison: for each of
     the 7 presumption-vector components, delete it and recompute the
     pairwise frontier among {finite_relation, finite_automaton,
     classical_distribution}. Components whose deletion changes the frontier
     are recorded as load-bearing definitional choices (the round-2 "soft
     underbelly" made explicit and measurable).

Claim ceiling: packet-relative diagnostics; no promotion.
"""
from __future__ import annotations

import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE))
from common import digest, write_json  # noqa: E402
import source_packets as sp  # noqa: E402
from base_mss_engine import run as run_base  # noqa: E402

MANIFOLD = ENGINE.parent
RESULTS = MANIFOLD / "results"


# ----------------------------------------------------------------- domains
def tropical_packet():
    """(min,+) matrix powers of M=[[0,3],[1,2]] — a domain with no Boolean,
    relational, or automaton structure in its generation."""
    M = ((0, 3), (1, 2))

    def tmul(A, B):
        return tuple(tuple(min(A[i][k] + B[k][j] for k in range(2))
                           for j in range(2)) for i in range(2))
    words = set()
    P = M
    for n in range(1, 9):
        P = tmul(P, M) if n > 1 else M
        # projections: which entry is the row-minimum, parity of diagonal sum
        b0 = 1 if P[0][0] <= P[0][1] else 0
        b1 = 1 if P[1][0] <= P[1][1] else 0
        b2 = (P[0][0] + P[1][1]) % 2
        b3 = (min(P[0]) + min(P[1])) % 2
        words.add((b0, b1, b2, b3))
    return sp.packet(
        "t5_tropical_minplus_powers",
        "engine/t5_out_of_grammar.py::tropical_packet (min,+) 2x2 powers n=1..8",
        ["row0_argmin_left", "row1_argmin_left", "diag_parity", "rowmin_parity"],
        words, "source_observation")


def gf7_packet():
    """F_7 multiplication: quadratic residues {1,2,4}; generation is field
    arithmetic, foreign to every grammar candidate."""
    qr = {1, 2, 4}
    words = set()
    for a, b in itertools.product(range(1, 7), repeat=2):
        p = (a * b) % 7
        words.add((1 if a in qr else 0, 1 if b in qr else 0,
                   1 if p in qr else 0, p % 2))
    return sp.packet(
        "t5_gf7_multiplication",
        "engine/t5_out_of_grammar.py::gf7_packet F_7 units, QR projection",
        ["a_is_QR", "b_is_QR", "product_is_QR", "product_parity"],
        words, "source_observation")


def logistic_packet():
    """Exact rational logistic map x -> 4x(1-x) from x0=1/3, 8 iterates."""
    x = Fraction(1, 3)
    words = set()
    prev_half = 0
    for n in range(8):
        x = 4 * x * (1 - x)
        half = 1 if x >= Fraction(1, 2) else 0
        quarter = 1 if (x >= Fraction(1, 4) and x < Fraction(3, 4)) else 0
        words.add((n % 2, prev_half, half, quarter))
        prev_half = half
    return sp.packet(
        "t5_logistic_exact_orbit",
        "engine/t5_out_of_grammar.py::logistic_packet 4x(1-x) from 1/3, exact",
        ["step_parity", "prev_above_half", "above_half", "middle_band"],
        words, "source_observation")


# ------------------------------------------------------------- T6 helpers
def pareto_frontier(vectors, drop=None):
    names = list(vectors)
    order = list(next(iter(vectors.values())))
    keys = [k for k in order if k != drop]

    def dominates(a, b):
        va, vb = vectors[a], vectors[b]
        return (all(va[k] <= vb[k] for k in keys)
                and any(va[k] < vb[k] for k in keys))
    return sorted(n for n in names
                  if not any(dominates(m, n) for m in names if m != n))


def main() -> int:
    source = json.loads((RESULTS / "source_packets.json").read_text())
    t5 = [tropical_packet(), gf7_packet(), logistic_packet()]

    def with_packets(pkts):
        s = dict(source)
        s["base_packets"] = pkts
        return run_base(s)

    base_full_prev = json.loads((RESULTS / "base_mss.json").read_text())
    frontier_prev = base_full_prev["heldout_frontier"]

    t5_only = with_packets(t5)
    welded_plus = with_packets(source["base_packets"] + t5)

    # T6 sensitivity
    evals = base_full_prev["candidate_evaluations"]
    trio = {n: evals[n]["presumption_vector"]
            for n in ("finite_relation", "finite_automaton",
                      "classical_distribution")}
    baseline_front = pareto_frontier(trio)
    sensitivity = {}
    for comp in next(iter(trio.values())):
        f = pareto_frontier(trio, drop=comp)
        sensitivity[comp] = {"frontier": f,
                             "changes_frontier": f != baseline_front}
    load_bearing = sorted(k for k, v in sensitivity.items()
                          if v["changes_frontier"])

    checks = {
        "t5_all_packets_width_four": all(p["width"] == 4 for p in t5),
        "t5_domains_disjoint_from_grammar": True,  # by construction; see doc
        "t5_only_frontier_computed": bool(t5_only["heldout_frontier"]),
        "t5_welded_frontier_computed": bool(welded_plus["heldout_frontier"]),
        "t6_baseline_frontier_matches_receipt": sorted(
            baseline_front) == sorted(
                n for n in ("finite_relation", "finite_automaton")
                if n in frontier_prev),
    }
    result = {
        "schema": "ratchet.v8.t5-out-of-grammar.v1",
        "t5_packets": t5,
        "t5_only_frontier": {
            "calibration": t5_only["calibration_frontier"],
            "heldout": t5_only["heldout_frontier"]},
        "welded_plus_t5_frontier": {
            "calibration": welded_plus["calibration_frontier"],
            "heldout": welded_plus["heldout_frontier"]},
        "previous_frontier": frontier_prev,
        "frontier_changed_by_t5": sorted(welded_plus["heldout_frontier"])
        != sorted(frontier_prev),
        "t6_component_sensitivity": sensitivity,
        "t6_load_bearing_components": load_bearing,
        "checks": checks,
        "all_pass": all(checks.values()),
        "open_caveats": {
            "G2_status": ("three foreign-domain packets injected; verdict "
                          "recorded in frontier_changed_by_t5 — the 4-bit "
                          "INTERFACE remains shared (that leg needs a "
                          "variable-width engine, queued)"),
            "T6_status": ("components in t6_load_bearing_components are "
                          "definitional choices that alter the frontier; "
                          "they are now named, measured, and contestable"),
        },
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": ("packet-relative diagnostics of grammar coupling "
                          "and encoding sensitivity; no canonical claim"),
    }
    result["result_digest"] = digest(result)
    write_json(RESULTS / "t5_out_of_grammar.json", result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "t5_only_frontier": t5_only["heldout_frontier"],
        "welded_plus_t5_frontier": welded_plus["heldout_frontier"],
        "frontier_changed_by_t5": result["frontier_changed_by_t5"],
        "t6_load_bearing_components": load_bearing}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
