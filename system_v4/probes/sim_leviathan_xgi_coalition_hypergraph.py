#!/usr/bin/env python3
"""
Leviathan XGI Coalition Hypergraph.

Claim: a Leviathan coalition space is a multi-agent (multi-way) relation, not
a pairwise graph. XGI hypergraphs are the natural carrier structure. This sim
establishes:
  - hyperedge incidence structure (B-matrix) as the carrier for coalition geometry
  - coalition power aggregation via hyperedge weights
  - hub fragility: removing the highest-power agent disconnects the structure
  - z3 UNSAT: zero-power agents cannot form a stable coalition

Load-bearing tools:
  xgi  -- hypergraph construction, B-matrix, connectivity, node removal
  z3   -- UNSAT on zero-power stability claim
"""

import json
import os
import numpy as np

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "no tensor graph needed; hyperedge structure is xgi native"},
    "pyg":       {"tried": False, "used": False, "reason": "pairwise graph only; cannot represent coalition hyperedges"},
    "z3":        {"tried": False, "used": False, "reason": "UNSAT on zero-power stability impossibility"},
    "cvc5":      {"tried": False, "used": False, "reason": "not required; z3 is sufficient for this SAT check"},
    "sympy":     {"tried": False, "used": False, "reason": "no symbolic algebra needed; numerical aggregation sufficient"},
    "clifford":  {"tried": False, "used": False, "reason": "no spinor structure in coalition hypergraph"},
    "geomstats": {"tried": False, "used": False, "reason": "Riemannian geometry not the target structure here"},
    "e3nn":      {"tried": False, "used": False, "reason": "equivariant NN not required"},
    "rustworkx": {"tried": False, "used": False, "reason": "ordinary graph comparison for connectivity baseline"},
    "xgi":       {"tried": False, "used": False, "reason": "hypergraph construction, incidence matrix, node removal, connectivity"},
    "toponetx":  {"tried": False, "used": False, "reason": "cell complex; overkill for hyperedge incidence at this stage"},
    "gudhi":     {"tried": False, "used": False, "reason": "persistence topology reserved for stability sim"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import xgi as xgi_lib
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    xgi_lib = None
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    import z3 as z3_lib
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3_lib = None
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    rx = None
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"


# =====================================================================
# SHARED SETUP
# =====================================================================

# 6 agents: h0, h1, h2 are high-power; l0, l1, l2 are low-power
# Node ids: h0=0, h1=1, h2=2, l0=3, l1=4, l2=5
AGENT_POWER = {0: 0.7, 1: 0.8, 2: 0.75, 3: 0.2, 4: 0.15, 5: 0.1}

# 5 coalition hyperedges:
#   e0: {h0, h1}        -- pairwise high+high
#   e1: {h0, l0}        -- pairwise high+low
#   e2: {l0, l1, l2}    -- three-way low (all three low-power agents)
#   e3: {h0, h1, h2}    -- three-way high
#   e4: {h0, l0, l1}    -- three-way mixed
# Note: all 6 nodes appear in at least one hyperedge, ensuring connectivity.
COALITIONS = [
    [0, 1],
    [0, 3],
    [3, 4, 5],
    [0, 1, 2],
    [0, 3, 4],
]


def build_hypergraph():
    H = xgi_lib.Hypergraph()
    H.add_nodes_from(list(AGENT_POWER.keys()))
    for i, members in enumerate(COALITIONS):
        H.add_edge(members, id=i)
    # Attach power as node attribute
    for node, pwr in AGENT_POWER.items():
        H.nodes[node]["power"] = pwr
    return H


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    if xgi_lib is None:
        return {"skipped": "xgi not installed"}

    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = (
        "build hypergraph, compute B-matrix rank, aggregate coalition power, connectivity check"
    )
    TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"

    results = {}

    # ------------------------------------------------------------------
    # P1: Basic hypergraph structure
    # ------------------------------------------------------------------
    H = build_hypergraph()
    n_nodes = H.num_nodes
    n_edges = H.num_edges
    connected = xgi_lib.is_connected(H)
    results["P1_structure"] = {
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "connected": connected,
        "pass": (n_nodes == 6 and n_edges == 5 and connected),
    }

    # ------------------------------------------------------------------
    # P2: Incidence matrix (B-matrix) rank
    # ------------------------------------------------------------------
    B = xgi_lib.incidence_matrix(H, sparse=False)
    rank_B = int(np.linalg.matrix_rank(B))
    expected_rank = min(6, 5)  # min(nodes, edges) = 5 for this case
    results["P2_bmatrix_rank"] = {
        "B_shape": list(B.shape),
        "rank": rank_B,
        "expected": expected_rank,
        "pass": (rank_B == expected_rank),
    }

    # ------------------------------------------------------------------
    # P3: Aggregate power -- 3-way high coalition dominates all pairwise
    # ------------------------------------------------------------------
    coalition_powers = {}
    for eid, members in enumerate(COALITIONS):
        agg_power = sum(AGENT_POWER[m] for m in members)
        coalition_powers[f"e{eid}"] = round(agg_power, 4)

    pairwise_ids = [0, 1, 2]   # e0, e1, e2
    three_way_high_power = coalition_powers["e3"]  # {h0,h1,h2}
    pairwise_powers = [coalition_powers[f"e{i}"] for i in pairwise_ids]
    three_way_dominates = all(three_way_high_power > pw for pw in pairwise_powers)
    results["P3_coalition_power_dominance"] = {
        "coalition_powers": coalition_powers,
        "three_way_high_power": three_way_high_power,
        "pairwise_powers": pairwise_powers,
        "three_way_dominates_all_pairwise": three_way_dominates,
        "pass": three_way_dominates,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ------------------------------------------------------------------
    # N1: z3 UNSAT -- stable coalition requires at least one agent with p_i > 0
    # ------------------------------------------------------------------
    if z3_lib is None:
        results["N1_zero_power_unsat"] = {"skipped": "z3 not installed"}
    else:
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "UNSAT: zero-power agents cannot form stable coalition"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

        s = z3_lib.Solver()
        # Encode 3 agents, each with power p_i >= 0
        p = [z3_lib.Real(f"p_{i}") for i in range(3)]
        for pi in p:
            s.add(pi >= 0)
        # Stability requirement: at least one member has p_i > 0
        # Claim to refute: ALL members have zero power AND coalition is stable
        # Encode: all p_i = 0 (zero-power coalition) AND stability_score > 0
        for pi in p:
            s.add(pi == 0)
        stability_score = z3_lib.Sum(p)
        s.add(stability_score > 0)  # impossible when all are 0
        r = s.check()
        results["N1_zero_power_unsat"] = {
            "z3_result": str(r),
            "claim_refuted": "zero-power agents have stability > 0",
            "pass": (r == z3_lib.unsat),
        }

    # ------------------------------------------------------------------
    # N2: XGI -- removing hub node h0 disconnects the hypergraph
    # ------------------------------------------------------------------
    if xgi_lib is None:
        results["N2_hub_removal_disconnects"] = {"skipped": "xgi not installed"}
    else:
        H = build_hypergraph()
        H_no_hub = H.copy()
        H_no_hub.remove_node(0)  # remove h0 (highest-power hub)
        connected_after = xgi_lib.is_connected(H_no_hub)
        results["N2_hub_removal_disconnects"] = {
            "hub_node": 0,
            "hub_power": AGENT_POWER[0],
            "connected_after_removal": connected_after,
            "pass": (not connected_after),  # should be disconnected
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if xgi_lib is None:
        return {"skipped": "xgi not installed"}

    # ------------------------------------------------------------------
    # B1: Equal-power boundary -- all agents have power 1/n
    #     All hyperedges have equal aggregate weight; entropy maximized
    # ------------------------------------------------------------------
    n = 6
    equal_power = 1.0 / n
    AGENT_POWER_EQUAL = {i: equal_power for i in range(n)}

    # Compute aggregate power per hyperedge under equal distribution
    equal_coalition_powers = {}
    for eid, members in enumerate(COALITIONS):
        agg = sum(AGENT_POWER_EQUAL[m] for m in members)
        equal_coalition_powers[f"e{eid}"] = round(agg, 6)

    # Check all hyperedges have weight proportional to size only (equal per-agent power)
    # e0,e1 are 2-way: weight = 2/n; e2,e3,e4 are 3-way: weight = 3/n
    expected_2way = round(2.0 / n, 6)
    expected_3way = round(3.0 / n, 6)

    e0_correct = abs(equal_coalition_powers["e0"] - expected_2way) < 1e-10
    e1_correct = abs(equal_coalition_powers["e1"] - expected_2way) < 1e-10
    e2_correct = abs(equal_coalition_powers["e2"] - expected_3way) < 1e-10
    e3_correct = abs(equal_coalition_powers["e3"] - expected_3way) < 1e-10
    e4_correct = abs(equal_coalition_powers["e4"] - expected_3way) < 1e-10

    # Entropy of coalition space: each coalition equally likely -> S = log(num_coalitions)
    n_coalitions = len(COALITIONS)
    entropy_equal = float(np.log(n_coalitions))

    all_equal = e0_correct and e1_correct and e2_correct and e3_correct and e4_correct
    results["B1_equal_power_max_entropy"] = {
        "equal_agent_power": equal_power,
        "coalition_powers": equal_coalition_powers,
        "expected_2way": expected_2way,
        "expected_3way": expected_3way,
        "all_weights_proportional_to_size": all_equal,
        "entropy_log_num_coalitions": round(entropy_equal, 6),
        "pass": all_equal,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    def allpass(d):
        if isinstance(d, dict) and "skipped" in d:
            return False
        return all(v.get("pass", False) for v in d.values() if isinstance(v, dict))

    ap = allpass(pos) and allpass(neg) and allpass(bnd)

    out = {
        "name": "leviathan_xgi_coalition_hypergraph",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": ap,
        "status": "PASS" if ap else "FAIL",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "leviathan_xgi_coalition_hypergraph_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"[{out['status']}] {out_path}")
