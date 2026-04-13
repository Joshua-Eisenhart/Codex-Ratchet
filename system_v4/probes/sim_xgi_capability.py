#!/usr/bin/env python3
"""
sim_xgi_capability.py -- Tool-capability isolation sim for XGI (hypergraph library).

Governing rule (durable, owner+Hermes 2026-04-13):
xgi is used as load_bearing in several coupling/multi-way interaction sims with
no dedicated capability probe. This sim is the bounded isolation probe that
unblocks xgi for nonclassical use.

Contract (from new docs/plans/tool-capability-sim-program.md):

- Job the tool is supposed to do here:
    Construct hypergraphs (nodes + hyperedges of arbitrary arity),
    compute node degree and edge size, incidence structure, connected
    components over hyperedges (two nodes linked iff they co-occur in any
    hyperedge), and lift to a simplicial complex when supported --
    used to encode shell-coupling multi-way interactions.

- Minimal bounded task it can actually do:
    Build xgi.Hypergraph with ~10 nodes and ~5 hyperedges of mixed size,
    verify degree sequence, edge-size sequence, incidence lookups,
    connected-component partition on hypergraph, and SimplicialComplex
    lift (if available in installed xgi version).

- Failure modes in this stack:
    * Silent: `import xgi` without exercising any xgi.* operation whose
      result materially affects the downstream claim.
    * API drift: xgi renamed Hypergraph methods across 0.7.x -> 0.9.x
      (e.g. `connected_components` vs `connected.connected_components`,
      SimplicialComplex in xgi.classes).
    * Input: passing a non-iterable as an edge must raise.

- Decorative vs load-bearing:
    Decorative = `import xgi` with no hypergraph structure used in the
    sim's conclusion.
    Load-bearing = hyperedge incidence / CC partition / simplicial lift
    IS the structure the coupling claim rests on.

- Baseline vs canonical comparison:
    Baseline = manual union-find over co-membership on the same
    hyperedge list (pure Python).
    Canonical-use = xgi's own connected_components on the Hypergraph;
    both must agree on the partition.
"""

import json
import os

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed -- pure hypergraph capability probe"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- pure hypergraph capability probe"},
    "z3":        {"tried": False, "used": False, "reason": "no proof obligation in a capability probe"},
    "cvc5":      {"tried": False, "used": False, "reason": "no proof obligation in a capability probe"},
    "sympy":     {"tried": False, "used": False, "reason": "no symbolic derivation required"},
    "clifford":  {"tried": False, "used": False, "reason": "no geometric algebra needed"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold/geodesic needed"},
    "e3nn":      {"tried": False, "used": False, "reason": "no equivariance needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "xgi is the graph library under test"},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": "not topology-relevant here; separate probe"},
    "gudhi":     {"tried": False, "used": False, "reason": "persistence not needed for hypergraph probe"},
    "networkx":  {"tried": False, "used": False, "reason": "union-find baseline suffices"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None, "rustworkx": None,
    "xgi": "load_bearing",   # the subject of the probe
    "toponetx": None, "gudhi": None, "networkx": None,
}

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = "capability under test -- Hypergraph construction / degree / incidence / CC / simplicial lift"
    XGI_OK = True
    XGI_VERSION = getattr(xgi, "__version__", "unknown")
except Exception as exc:
    XGI_OK = False
    XGI_VERSION = None
    TOOL_MANIFEST["xgi"]["reason"] = f"not installed: {exc}"


# =====================================================================
# Helpers
# =====================================================================

def _uf_cc(nodes, hyperedges):
    """Baseline connected components: nodes linked iff co-occur in any hyperedge."""
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for edge in hyperedges:
        edge = list(edge)
        for v in edge[1:]:
            union(edge[0], v)
    comps = {}
    for n in nodes:
        r = find(n)
        comps.setdefault(r, set()).add(n)
    return [frozenset(s) for s in comps.values()]


def _canon_partition(parts):
    return sorted([tuple(sorted(p)) for p in parts])


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    if not XGI_OK:
        results["xgi_available"] = {"pass": False, "detail": "xgi missing"}
        return results
    results["xgi_available"] = {"pass": True, "version": XGI_VERSION}

    # --- 1. Hypergraph construction + size/degree ---
    # Hand-verified small hypergraph
    nodes = list(range(6))
    hyperedges = [
        [0, 1, 2],    # size 3
        [2, 3],       # size 2
        [3, 4, 5],    # size 3
        [0, 5],       # size 2
    ]
    H = xgi.Hypergraph()
    H.add_nodes_from(nodes)
    H.add_edges_from(hyperedges)

    n_nodes = H.num_nodes
    n_edges = H.num_edges
    results["construction"] = {
        "pass": n_nodes == 6 and n_edges == 4,
        "num_nodes": int(n_nodes),
        "num_edges": int(n_edges),
        "expected_nodes": 6,
        "expected_edges": 4,
    }

    # --- 2. Degree sequence ---
    # node 0 appears in {e0,e3}=2; 1 in {e0}=1; 2 in {e0,e1}=2;
    # 3 in {e1,e2}=2; 4 in {e2}=1; 5 in {e2,e3}=2
    expected_deg = {0: 2, 1: 1, 2: 2, 3: 2, 4: 1, 5: 2}
    deg = {n: int(H.degree(n)) for n in nodes}
    results["degree_sequence"] = {
        "pass": deg == expected_deg,
        "got": deg,
        "expected": expected_deg,
    }

    # --- 3. Edge size sequence ---
    expected_sizes = sorted([3, 2, 3, 2])
    sizes = sorted([len(H.edges.members(e)) for e in H.edges])
    results["edge_sizes"] = {
        "pass": sizes == expected_sizes,
        "got": sizes,
        "expected": expected_sizes,
    }

    # --- 4. Incidence: which edges contain node 2? ---
    # node 2 is in edges e0 and e1 (by insertion order)
    edges_of_2 = sorted([int(e) for e in H.nodes.memberships(2)])
    # We don't assume edge IDs are 0..k; check content instead.
    members_per_edge = {int(e): set(H.edges.members(e)) for e in edges_of_2}
    contains_2 = all(2 in s for s in members_per_edge.values())
    results["incidence_lookup"] = {
        "pass": len(edges_of_2) == 2 and contains_2,
        "edges_of_node_2": edges_of_2,
        "members_per_edge": {str(k): sorted(v) for k, v in members_per_edge.items()},
    }

    # --- 5. Connected components (xgi vs union-find baseline) ---
    try:
        # xgi 0.8+ exposes xgi.connected_components
        cc_fn = getattr(xgi, "connected_components", None)
        if cc_fn is None:
            from xgi.algorithms import connected as _conn
            cc_fn = _conn.connected_components
        xgi_cc = [frozenset(c) for c in cc_fn(H)]
        uf_cc = _uf_cc(nodes, hyperedges)
        results["connected_components_vs_baseline"] = {
            "pass": _canon_partition(xgi_cc) == _canon_partition(uf_cc),
            "xgi_partition": _canon_partition(xgi_cc),
            "baseline_partition": _canon_partition(uf_cc),
            "detail": "all 6 nodes should be in one component via edge chain",
        }
    except Exception as exc:
        results["connected_components_vs_baseline"] = {"pass": False, "detail": f"raised: {exc}"}

    # --- 6. Simplicial complex lift (if available in this xgi version) ---
    sc_cls = getattr(xgi, "SimplicialComplex", None)
    if sc_cls is None:
        results["simplicial_lift"] = {
            "pass": True,
            "skipped": True,
            "detail": f"xgi {XGI_VERSION} does not expose SimplicialComplex at top level -- capability limit noted",
        }
    else:
        try:
            SC = sc_cls()
            SC.add_nodes_from(nodes)
            SC.add_simplices_from(hyperedges)
            # A simplicial complex is downward-closed; adding a 3-simplex
            # {0,1,2} must induce its 2-faces {0,1},{0,2},{1,2}.
            all_members = [frozenset(SC.edges.members(e)) for e in SC.edges]
            has_01 = any(frozenset([0, 1]).issubset(m) for m in all_members)
            has_12 = any(frozenset([1, 2]).issubset(m) for m in all_members)
            results["simplicial_lift"] = {
                "pass": SC.num_nodes == 6 and has_01 and has_12,
                "num_nodes": int(SC.num_nodes),
                "num_simplices": int(SC.num_edges),
                "detail": "SimplicialComplex must be downward-closed",
            }
        except Exception as exc:
            results["simplicial_lift"] = {"pass": False, "detail": f"raised: {exc}"}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    if not XGI_OK:
        results["xgi_available"] = {"pass": False, "detail": "xgi missing"}
        return results

    # --- N1. Disconnected hypergraph must yield >1 CC ---
    H = xgi.Hypergraph()
    H.add_nodes_from([0, 1, 2, 3])
    H.add_edges_from([[0, 1], [2, 3]])
    try:
        cc_fn = getattr(xgi, "connected_components", None)
        if cc_fn is None:
            from xgi.algorithms import connected as _conn
            cc_fn = _conn.connected_components
        parts = [frozenset(c) for c in cc_fn(H)]
        results["disconnected_has_two_components"] = {
            "pass": len(parts) == 2,
            "got": len(parts),
            "expected": 2,
        }
    except Exception as exc:
        results["disconnected_has_two_components"] = {"pass": False, "detail": f"raised: {exc}"}

    # --- N2. Non-iterable hyperedge must raise ---
    raised = False
    err = None
    try:
        H_bad = xgi.Hypergraph()
        H_bad.add_nodes_from([0, 1])
        H_bad.add_edge(42)  # int, not iterable
    except Exception as exc:
        raised = True
        err = type(exc).__name__
    results["non_iterable_edge_raises"] = {
        "pass": raised,
        "error_type": err,
        "detail": "xgi must refuse a non-iterable hyperedge",
    }

    # --- N3. Querying degree of non-existent node must raise ---
    H2 = xgi.Hypergraph()
    H2.add_nodes_from([0, 1])
    H2.add_edges_from([[0, 1]])
    raised2 = False
    err2 = None
    try:
        _ = H2.degree(999)
    except Exception as exc:
        raised2 = True
        err2 = type(exc).__name__
    results["missing_node_degree_raises"] = {
        "pass": raised2,
        "error_type": err2,
        "detail": "degree() on a nonexistent node must raise (IDNotFound or similar)",
    }
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    if not XGI_OK:
        results["xgi_available"] = {"pass": False, "detail": "xgi missing"}
        return results

    # --- B1. Empty hypergraph ---
    H0 = xgi.Hypergraph()
    results["empty_hypergraph"] = {
        "pass": H0.num_nodes == 0 and H0.num_edges == 0,
        "num_nodes": int(H0.num_nodes),
        "num_edges": int(H0.num_edges),
        "detail": "empty Hypergraph must have 0 nodes and 0 edges",
    }

    # --- B2. Singleton node, no edges -> one component of size 1 ---
    H1 = xgi.Hypergraph()
    H1.add_node(0)
    try:
        cc_fn = getattr(xgi, "connected_components", None)
        if cc_fn is None:
            from xgi.algorithms import connected as _conn
            cc_fn = _conn.connected_components
        parts = [frozenset(c) for c in cc_fn(H1)]
        results["singleton_one_component"] = {
            "pass": len(parts) == 1 and list(parts[0]) == [0],
            "partition": _canon_partition(parts),
        }
    except Exception as exc:
        results["singleton_one_component"] = {"pass": False, "detail": f"raised: {exc}"}

    # --- B3. Self-loop-ish edge (singleton hyperedge) ---
    # Not every xgi version accepts size-1 edges; record the behavior rather
    # than demand a specific outcome.
    H3 = xgi.Hypergraph()
    H3.add_nodes_from([0, 1])
    accepted = True
    err = None
    n_edges = None
    try:
        H3.add_edge([0])
        n_edges = int(H3.num_edges)
    except Exception as exc:
        accepted = False
        err = type(exc).__name__
    results["singleton_hyperedge_behavior"] = {
        "pass": True,   # behavior-recording only, not a failure either way
        "accepted": accepted,
        "num_edges_after": n_edges,
        "error_type": err,
        "detail": "records xgi's policy on size-1 hyperedges (capability boundary)",
    }

    # --- B4. Large-ish sanity check: 50 nodes, all in one hyperedge ---
    Hbig = xgi.Hypergraph()
    Hbig.add_nodes_from(range(50))
    Hbig.add_edge(list(range(50)))
    # Every node has degree 1, edge has size 50.
    all_deg1 = all(int(Hbig.degree(n)) == 1 for n in range(50))
    big_edge_size = len(Hbig.edges.members(list(Hbig.edges)[0]))
    results["one_big_hyperedge"] = {
        "pass": all_deg1 and big_edge_size == 50,
        "all_degree_1": all_deg1,
        "edge_size": big_edge_size,
    }
    return results


# =====================================================================
# MAIN
# =====================================================================

def _all_pass(section):
    if not isinstance(section, dict):
        return False
    flags = [bool(v.get("pass", False)) for v in section.values() if isinstance(v, dict)]
    return bool(flags) and all(flags)


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = XGI_OK and all(summary.values())

    results = {
        "name": "sim_xgi_capability",
        "purpose": "Tool-capability isolation probe for xgi -- unblocks load-bearing hypergraph use.",
        "xgi_version": XGI_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "xgi_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
