#!/usr/bin/env python3
"""Classical baseline: I Ching hexagram trigram decomposition.

Every 6-bit hexagram decomposes into an upper trigram (bits 3-5) and
lower trigram (bits 0-2). The 6-dimensional hypercube Q6 is isomorphic
to the Cartesian graph product Q3 □ Q3.

Tests cover:
  - Q6 ≅ Q3 □ Q3 via degree sequence, edge count (192), bipartiteness
  - Upper and lower trigrams are independent DOFs
  - All 64 hexagrams span exactly 8x8 upper×lower pairs
  - z3 UNSAT: a single Hamming-1 flip cannot change both trigrams simultaneously
  - Boundary: the 8 hexagrams with upper == lower form an independent set in Q6
"""

import json
import os

classification = "classical_baseline"
divergence_log = [
    "Classical comparator/control surface only: this runner does not promote a nonclassical, formal-scout, bridge, axis-level, or canonical proof claim.",
]

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False,
                   "reason": "not applicable to combinatorial graph sim"},
    "pyg":        {"tried": False, "used": False,
                   "reason": "not applicable to combinatorial graph sim"},
    "z3":         {"tried": True,  "used": True,
                   "reason": "UNSAT proof that single Hamming-1 flip cannot change both upper and lower trigram simultaneously"},
    "cvc5":       {"tried": False, "used": False,
                   "reason": "z3 sufficient for this Boolean UNSAT; cvc5 not needed"},
    "sympy":      {"tried": True,  "used": True,
                   "reason": "verify Cartesian product edge-count formula |V_G|*|E_H| + |E_G|*|V_H| = 8*12 + 12*8 = 192"},
    "clifford":   {"tried": False, "used": False,
                   "reason": "not applicable to combinatorial graph sim"},
    "geomstats":  {"tried": False, "used": False,
                   "reason": "not applicable to combinatorial graph sim"},
    "e3nn":       {"tried": False, "used": False,
                   "reason": "not applicable to combinatorial graph sim"},
    "rustworkx":  {"tried": True,  "used": True,
                   "reason": "construct Q6 and Q3□Q3 as explicit graphs; verify isomorphism via degree sequence and edge count"},
    "xgi":        {"tried": False, "used": False,
                   "reason": "not applicable; no hyperedges in this sim"},
    "toponetx":   {"tried": False, "used": False,
                   "reason": "not applicable; no cell complex structure needed"},
    "gudhi":      {"tried": False, "used": False,
                   "reason": "not applicable; no persistent homology needed"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":    None,
    "pyg":        None,
    "z3":         "load_bearing",
    "cvc5":       None,
    "sympy":      "supportive",
    "clifford":   None,
    "geomstats":  None,
    "e3nn":       None,
    "rustworkx":  "load_bearing",
    "xgi":        None,
    "toponetx":   None,
    "gudhi":      None,
}

# --- tool imports -----------------------------------------------------------
try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    _HAS_RX = True
except ImportError:
    _HAS_RX = False
    TOOL_MANIFEST["rustworkx"]["reason"] += " [IMPORT FAILED]"

try:
    from z3 import Solver, BitVec, BitVecVal, Not, And, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    _HAS_Z3 = True
except ImportError:
    _HAS_Z3 = False
    TOOL_MANIFEST["z3"]["reason"] += " [IMPORT FAILED]"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    _HAS_SP = True
except ImportError:
    _HAS_SP = False
    TOOL_MANIFEST["sympy"]["reason"] += " [IMPORT FAILED]"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hamming_weight(x: int) -> int:
    return bin(x).count("1")


def upper_trigram(h: int) -> int:
    """Bits 3-5 (shift right 3)."""
    return (h >> 3) & 0b111


def lower_trigram(h: int) -> int:
    """Bits 0-2."""
    return h & 0b111


def build_q6_rustworkx():
    """Build Q6 as a rustworkx undirected graph: nodes 0-63, edges = Hamming-1 pairs."""
    g = rx.PyGraph()
    g.add_nodes_from(range(64))
    for i in range(64):
        for bit in range(6):
            j = i ^ (1 << bit)
            if j > i:
                g.add_edge(i, j, None)
    return g


def build_cartesian_product_q3_q3_rustworkx():
    """Build Q3 □ Q3 explicitly: vertex = (u, v) for u,v in 0..7.
    Encoded as u*8 + v so node index matches hexagram decimal value."""
    g = rx.PyGraph()
    g.add_nodes_from(range(64))  # node i = upper*8 + lower
    for u in range(8):
        for v in range(8):
            node = u * 8 + v
            # edges from u-side: fix v, flip one bit of u
            for bit in range(3):
                u2 = u ^ (1 << bit)
                if u2 > u:
                    node2 = u2 * 8 + v
                    g.add_edge(node, node2, None)
            # edges from v-side: fix u, flip one bit of v
            for bit in range(3):
                v2 = v ^ (1 << bit)
                if v2 > v:
                    node2 = u * 8 + v2
                    g.add_edge(node, node2, None)
    return g


# ---------------------------------------------------------------------------
# POSITIVE TESTS
# ---------------------------------------------------------------------------

def run_positive_tests():
    r = {}

    # --- P1: Q6 ≅ Q3 □ Q3 structural equivalence ---
    if _HAS_RX:
        q6 = build_q6_rustworkx()
        cp = build_cartesian_product_q3_q3_rustworkx()

        q6_edge_count = q6.num_edges()
        cp_edge_count = cp.num_edges()
        r["p1_q6_edge_count"] = q6_edge_count
        r["p1_cp_edge_count"] = cp_edge_count
        r["p1_edge_counts_match"] = bool(q6_edge_count == cp_edge_count == 192)

        # Degree sequences must match
        q6_degrees = sorted([q6.degree(i) for i in range(64)])
        cp_degrees = sorted([cp.degree(i) for i in range(64)])
        r["p1_degree_sequences_match"] = bool(q6_degrees == cp_degrees)
        r["p1_all_degree_6"] = bool(all(d == 6 for d in q6_degrees))

        # Both must be bipartite (hypercubes are bipartite)
        # Check via 2-colorability: parity of number of 1-bits
        def is_bipartite_by_parity(graph, n):
            for i in range(n):
                for j in graph.neighbors(i):
                    if hamming_weight(i) % 2 == hamming_weight(j) % 2:
                        return False
            return True

        r["p1_q6_bipartite"] = is_bipartite_by_parity(q6, 64)
        r["p1_cp_bipartite"] = is_bipartite_by_parity(cp, 64)

        r["p1_pass"] = bool(
            r["p1_edge_counts_match"]
            and r["p1_degree_sequences_match"]
            and r["p1_all_degree_6"]
            and r["p1_q6_bipartite"]
            and r["p1_cp_bipartite"]
        )
    else:
        r["p1_pass"] = "SKIP: rustworkx unavailable"

    # --- P2: Upper and lower trigrams are independent ---
    # Flipping a bit in the lower three bits never changes the upper trigram,
    # and vice versa — verified exhaustively over all 64 hexagrams.
    independence_violations = []
    for h in range(64):
        u_orig = upper_trigram(h)
        l_orig = lower_trigram(h)
        # flip each lower bit: upper trigram must not change
        for bit in range(3):
            h2 = h ^ (1 << bit)
            if upper_trigram(h2) != u_orig:
                independence_violations.append(("lower_flip_changed_upper", h, bit))
        # flip each upper bit: lower trigram must not change
        for bit in range(3, 6):
            h2 = h ^ (1 << bit)
            if lower_trigram(h2) != l_orig:
                independence_violations.append(("upper_flip_changed_lower", h, bit))

    r["p2_independence_violations"] = len(independence_violations)
    r["p2_pass"] = bool(len(independence_violations) == 0)

    # --- P3: All 64 upper×lower pairs present exactly once ---
    pair_counts: dict = {}
    for h in range(64):
        key = (upper_trigram(h), lower_trigram(h))
        pair_counts[key] = pair_counts.get(key, 0) + 1

    r["p3_unique_pairs"] = len(pair_counts)
    r["p3_all_counts_one"] = bool(all(v == 1 for v in pair_counts.values()))
    r["p3_pass"] = bool(r["p3_unique_pairs"] == 64 and r["p3_all_counts_one"])

    return r


# ---------------------------------------------------------------------------
# NEGATIVE TESTS
# ---------------------------------------------------------------------------

def run_negative_tests():
    r = {}

    # --- N1: z3 UNSAT — a Hamming-1 flip cannot change both upper AND lower trigram ---
    # A Hamming-1 flip flips exactly one bit. A bit is in exactly one of
    # {bits 0-2} (lower) or {bits 3-5} (upper). So it is structurally
    # impossible for one flip to affect both. We encode this as a z3 query
    # and expect UNSAT.
    if _HAS_Z3:
        slv = Solver()
        # h is the original hexagram (6-bit)
        h = BitVec("h", 6)
        # flip_bit selects which bit to flip (0-5); encoded as one-hot via 6 Booleans
        # We model the flipped hexagram h2 = h XOR (1 << flip_bit)
        # Use a concrete bit position enumeration for clarity
        from z3 import Or as Z3Or, BV2Int
        results_unsat = []
        for flip_pos in range(6):
            mask = BitVecVal(1 << flip_pos, 6)
            h2 = h ^ mask

            # upper trigram: bits 3-5 → h >> 3 (take low 3 bits)
            upper_mask = BitVecVal(0b111000, 6)
            lower_mask = BitVecVal(0b000111, 6)

            upper_changed = Not((h & upper_mask) == (h2 & upper_mask))
            lower_changed = Not((h & lower_mask) == (h2 & lower_mask))

            slv2 = Solver()
            slv2.add(upper_changed)
            slv2.add(lower_changed)
            result = slv2.check()
            results_unsat.append(result == unsat)

        r["n1_all_flip_positions_unsat"] = all(results_unsat)
        r["n1_unsat_count"] = sum(results_unsat)
        r["n1_pass"] = bool(r["n1_all_flip_positions_unsat"])
    else:
        r["n1_pass"] = "SKIP: z3 unavailable"

    return r


# ---------------------------------------------------------------------------
# BOUNDARY TESTS
# ---------------------------------------------------------------------------

def run_boundary_tests():
    r = {}

    # --- B1: 8 hexagrams with upper == lower form an independent set in Q6 ---
    # upper == lower means bits 0-2 == bits 3-5, i.e. h = t | (t << 3) for t in 0..7
    palindromes = [t | (t << 3) for t in range(8)]
    r["b1_palindromes"] = palindromes
    r["b1_palindrome_count"] = len(palindromes)

    # Check: no two palindromes are adjacent in Q6 (Hamming distance 1)
    adjacent_pairs = []
    for i, a in enumerate(palindromes):
        for b in palindromes[i + 1:]:
            if hamming_weight(a ^ b) == 1:
                adjacent_pairs.append((a, b))

    r["b1_adjacent_pairs"] = adjacent_pairs
    r["b1_is_independent_set"] = bool(len(adjacent_pairs) == 0)

    # Verify the palindromes: for h = t|(t<<3), upper(h)=t and lower(h)=t
    all_upper_eq_lower = all(upper_trigram(h) == lower_trigram(h) for h in palindromes)
    r["b1_all_upper_eq_lower"] = all_upper_eq_lower

    # Also verify no non-palindrome is adjacent to two palindromes with the same trigram
    # (sanity: confirm 8 palindromes cover all 8 trigrams exactly once)
    trigrams_covered = sorted([lower_trigram(h) for h in palindromes])
    r["b1_trigrams_covered"] = trigrams_covered
    r["b1_all_8_trigrams"] = bool(trigrams_covered == list(range(8)))

    r["b1_pass"] = bool(
        r["b1_is_independent_set"]
        and r["b1_all_upper_eq_lower"]
        and r["b1_all_8_trigrams"]
        and r["b1_palindrome_count"] == 8
    )

    # --- B2: sympy formula verification for Cartesian product edge count ---
    if _HAS_SP:
        # Q3 has 8 vertices and 12 edges; Q3 □ Q3 edge count = |V_Q3|*|E_Q3| + |E_Q3|*|V_Q3|
        V_Q3 = sp.Integer(8)
        E_Q3 = sp.Integer(12)
        formula_count = V_Q3 * E_Q3 + E_Q3 * V_Q3
        r["b2_sympy_formula_edge_count"] = int(formula_count)
        r["b2_formula_matches_192"] = bool(formula_count == 192)
        r["b2_pass"] = bool(r["b2_formula_matches_192"])
    else:
        r["b2_pass"] = "SKIP: sympy unavailable"

    return r


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Collect pass/fail
    all_results = {}
    all_results.update(pos)
    all_results.update(neg)
    all_results.update(bnd)

    pass_keys = [k for k in all_results if k.endswith("_pass")]
    passed = [k for k in pass_keys if all_results[k] is True]
    failed = [k for k in pass_keys if all_results[k] is not True]
    all_pass = len(failed) == 0 and len(passed) > 0

    results = {
        "name": "sim_iching_hexagram_trigram_decomposition",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "pass_summary": {
            "passed": passed,
            "failed": failed,
            "total_pass_keys": len(pass_keys),
            "all_pass": all_pass,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir, "sim_iching_hexagram_trigram_decomposition_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Pass summary: {len(passed)}/{len(pass_keys)} pass keys green | all_pass={all_pass}")
    if failed:
        print(f"FAILED: {failed}")
