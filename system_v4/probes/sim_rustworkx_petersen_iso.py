#!/usr/bin/env python3
"""
Isomorphism check: Petersen graph vs random 3-regular graphs on 10 nodes.
rustworkx is_isomorphic (VF2) — load-bearing (strict typing + Rust backend).
Petersen is uniquely determined by girth 5 + 3-regular + 10 nodes, so all non-Petersen
3-regular 10-node graphs must be non-isomorphic.
Ablation: numpy eigenvalue-spectrum comparison (necessary but not sufficient).
"""
import json, os, time, random
import numpy as np
import rustworkx as rx

TOOL_MANIFEST = {
    "rustworkx": {"tried": True, "used": True,
                  "reason": "VF2 is_isomorphic is load-bearing; eigen-spectrum is only a necessary filter, not a decision procedure"},
    "numpy": {"tried": True, "used": True, "reason": "spectral ablation (cospectral false positives possible)"},
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing", "numpy": "supportive"}

def petersen():
    g = rx.PyGraph()
    for _ in range(10): g.add_node(None)
    # outer 5-cycle
    for i in range(5): g.add_edge(i, (i+1)%5, 1)
    # inner pentagram
    for i in range(5): g.add_edge(5+i, 5+((i+2)%5), 1)
    # spokes
    for i in range(5): g.add_edge(i, 5+i, 1)
    return g

def random_3reg_10(seed):
    """Construct a 3-regular graph on 10 nodes via configuration model with rejection."""
    rng = random.Random(seed)
    for _ in range(500):
        stubs = []
        for v in range(10): stubs += [v,v,v]
        rng.shuffle(stubs)
        edges = set(); ok = True
        for i in range(0, 30, 2):
            a,b = stubs[i], stubs[i+1]
            if a == b: ok = False; break
            k = (min(a,b), max(a,b))
            if k in edges: ok = False; break
            edges.add(k)
        if ok and len(edges) == 15:
            g = rx.PyGraph()
            for _ in range(10): g.add_node(None)
            for (u,v) in edges: g.add_edge(u,v,1)
            # verify 3-regular
            if all(len(list(g.neighbors(v))) == 3 for v in range(10)):
                return g
    return None

def spectrum(g):
    n = len(g)
    A = np.zeros((n,n))
    for (u,v) in g.edge_list(): A[u,v]=1; A[v,u]=1
    return np.sort(np.linalg.eigvalsh(A))

def relabel(g, perm):
    h = rx.PyGraph()
    for _ in range(len(g)): h.add_node(None)
    for (u,v) in g.edge_list():
        h.add_edge(perm[u], perm[v], 1)
    return h

def run_positive_tests():
    p = petersen()
    # Petersen vs Petersen-relabeled => isomorphic
    perm = list(range(10)); random.Random(42).shuffle(perm)
    p2 = relabel(p, perm)
    iso_same = rx.is_isomorphic(p, p2)
    return {
        "petersen_n_nodes": len(p),
        "petersen_n_edges": len(p.edge_list()),
        "three_regular": all(len(list(p.neighbors(v)))==3 for v in range(10)),
        "iso_with_relabel": iso_same,
        "pass": iso_same and len(p.edge_list()) == 15,
    }

def run_negative_tests():
    p = petersen()
    results = []
    attempts = 0; nonpetersen_found = 0
    for seed in range(1, 40):
        r = random_3reg_10(seed)
        if r is None: continue
        attempts += 1
        iso = rx.is_isomorphic(p, r)
        # Petersen has girth 5; if random graph has triangle or 4-cycle, can't be iso.
        if not iso:
            nonpetersen_found += 1
        results.append({"seed": seed, "iso_to_petersen": iso})
        if nonpetersen_found >= 3: break
    return {
        "attempts": attempts,
        "nonpetersen_confirmed": nonpetersen_found,
        "sample": results[:5],
        "pass": nonpetersen_found >= 1,
    }

def run_boundary_tests():
    p = petersen()
    spec_p = spectrum(p)
    # Petersen spectrum: {3, 1 (×5), -2 (×4)}
    expected = sorted([3.0] + [1.0]*5 + [-2.0]*4)
    spec_match = np.allclose(spec_p, expected, atol=1e-9)
    # Construct a random 3-reg, compare spectra (cospectral filter)
    r = random_3reg_10(7)
    spec_r = spectrum(r) if r is not None else None
    cospectral = bool(spec_r is not None and np.allclose(spec_p, spec_r, atol=1e-9))
    t0 = time.time()
    _ = rx.is_isomorphic(p, r) if r is not None else None
    t_rx = time.time()-t0
    return {
        "petersen_spectrum": spec_p.tolist(),
        "spectrum_matches_theory": spec_match,
        "cospectral_with_random": cospectral,
        "t_rx_vf2_s": t_rx,
    }

if __name__ == "__main__":
    results = {
        "name": "rustworkx_petersen_iso",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "rustworkx_petersen_iso_results.json")
    with open(out,"w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
    print(json.dumps(results["positive"], indent=2))
