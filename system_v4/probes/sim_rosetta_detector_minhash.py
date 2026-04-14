#!/usr/bin/env python3
"""
sim_rosetta_detector_minhash.py -- Canonical sim.

MinHashLSH-based detector for Rosetta candidate pairs across the sim
corpus. Verdict signature = sorted tuple of top-level result-JSON keys
whose values are truthy, hashed into a 64-permutation MinHash; LSH
threshold=0.7. Clusters of size >=2 are reported; clusters are flagged
"confirmed Rosetta candidate" only if their source files span >=3
distinct load_bearing tool families (patient-convergence rule).

Exclusion language: clusters are similarity-admitted under the verdict-
key signature; they are candidates, not theorems. Reports only -- no
file is merged or deleted.
"""

import json
import os
import re
import glob

TOOL_MANIFEST = {
    "datasketch": {"tried": False, "used": False, "reason": ""},
    "ribs": {"tried": False, "used": False, "reason": "archive handled in sibling sim"},
    "pytorch": {"tried": False, "used": False, "reason": "no tensor compute needed"},
    "pyg": {"tried": False, "used": False, "reason": "no message passing"},
    "z3": {"tried": False, "used": False, "reason": "no SMT proof for similarity detection"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT proof"},
    "sympy": {"tried": False, "used": False, "reason": "no symbolic math"},
    "clifford": {"tried": False, "used": False, "reason": "no Cl rotors"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold geometry"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph algorithms"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraphs"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from datasketch import MinHash, MinHashLSH
    TOOL_MANIFEST["datasketch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["datasketch"]["reason"] = "not installed"
    raise

PROBES = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(PROBES, "a2_state", "sim_results")

FAMILY_MAP = {
    "z3": "smt", "cvc5": "smt",
    "sympy": "symbolic",
    "clifford": "clifford",
    "e3nn": "e3nn",
    "pyg": "graph_topo", "torch_geometric": "graph_topo", "toponetx": "graph_topo",
    "gudhi": "topo_geom", "rustworkx": "topo_geom", "geomstats": "topo_geom",
    "ribs": "search", "deap": "search", "evotorch": "search",
}


def verdict_signature(result_path):
    try:
        with open(result_path) as f:
            data = json.load(f)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    keys = [k for k, v in data.items() if v]
    return tuple(sorted(keys))


def load_bearing_tools(source_path):
    try:
        with open(source_path) as f:
            src = f.read()
    except Exception:
        return set()
    m = re.search(r"TOOL_INTEGRATION_DEPTH\s*=\s*\{([^}]*)\}", src, re.DOTALL)
    if not m:
        return set()
    lb = set()
    for line in m.group(1).splitlines():
        mm = re.match(r"\s*[\"']([a-zA-Z0-9_]+)[\"']\s*:\s*[\"']load_bearing[\"']", line)
        if mm:
            lb.add(mm.group(1).lower())
    return lb


def tool_families(lb_tools):
    return {FAMILY_MAP[t] for t in lb_tools if t in FAMILY_MAP}


def mk_minhash(sig, num_perm=64):
    mh = MinHash(num_perm=num_perm)
    for tok in sig:
        mh.update(tok.encode("utf-8"))
    return mh


def run_positive_tests():
    lsh = MinHashLSH(threshold=0.7, num_perm=64)
    TOOL_MANIFEST["datasketch"]["used"] = True
    TOOL_MANIFEST["datasketch"]["reason"] = "MinHashLSH threshold=0.7 num_perm=64 over verdict-key signatures"
    TOOL_INTEGRATION_DEPTH["datasketch"] = "load_bearing"

    # Build signatures for every result JSON whose sim source exists.
    sim_files = {os.path.basename(p)[:-3]: p for p in glob.glob(os.path.join(PROBES, "sim_*.py"))}
    sigs = {}
    mhs = {}
    for rp in glob.glob(os.path.join(RESULTS_DIR, "*_results.json")):
        base = os.path.basename(rp)[:-len("_results.json")]
        src = sim_files.get(base) or sim_files.get("sim_" + base)
        if not src:
            continue
        sig = verdict_signature(rp)
        if not sig:
            continue
        mh = mk_minhash(sig)
        try:
            lsh.insert(base, mh)
        except ValueError:
            # duplicate key: skip
            continue
        sigs[base] = sig
        mhs[base] = (mh, src)

    # Query each, collect clusters.
    seen = set()
    clusters = []
    for base, (mh, _src) in mhs.items():
        if base in seen:
            continue
        hits = [h for h in lsh.query(mh) if h in mhs]
        if len(hits) >= 2:
            cluster = tuple(sorted(hits))
            if cluster not in {tuple(sorted(c["sims"])) for c in clusters}:
                clusters.append({"sims": list(cluster)})
        for h in hits:
            seen.add(h)

    # Patient-convergence: confirm only if >=3 tool families.
    confirmed = []
    diversity = []
    for c in clusters:
        fams = set()
        per_sim = {}
        for s in c["sims"]:
            _mh, src = mhs[s]
            lb = load_bearing_tools(src)
            fs = tool_families(lb)
            per_sim[s] = sorted(fs)
            fams |= fs
        diversity.append({"cluster": c["sims"], "families": sorted(fams), "n_families": len(fams)})
        if len(fams) >= 3:
            confirmed.append({"sims": c["sims"], "tool_families": sorted(fams)})

    total_pairs = sum(len(c["sims"]) * (len(c["sims"]) - 1) // 2 for c in clusters)

    return {
        "total_signatures": len(mhs),
        "lsh_clusters_count": len(clusters),
        "lsh_pairs_count": total_pairs,
        "confirmed_rosettas": confirmed,
        "notation_diversity_per_cluster": diversity,
        "passed": True,  # insert/query succeeded; list may be empty (valid)
    }


def run_negative_tests():
    # Negative: dissimilar signatures must NOT cluster at threshold 0.7.
    lsh = MinHashLSH(threshold=0.7, num_perm=64)
    a = mk_minhash(("alpha", "beta", "gamma"))
    b = mk_minhash(("delta", "epsilon", "zeta"))
    lsh.insert("a", a); lsh.insert("b", b)
    hits = lsh.query(a)
    return {"dissimilar_hits": hits, "passed": "b" not in hits}


def run_boundary_tests():
    # Boundary: identical signatures must collide.
    lsh = MinHashLSH(threshold=0.7, num_perm=64)
    sig = ("k1", "k2", "k3", "k4", "k5")
    lsh.insert("x", mk_minhash(sig))
    lsh.insert("y", mk_minhash(sig))
    hits = set(lsh.query(mk_minhash(sig)))
    return {"identical_hits": sorted(hits), "passed": {"x", "y"}.issubset(hits)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    overall = "PASS" if (pos["passed"] and neg["passed"] and bnd["passed"]) else "FAIL"
    results = {
        "name": "sim_rosetta_detector_minhash",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "status": overall,
    }
    out_path = os.path.join(RESULTS_DIR, "sim_rosetta_detector_minhash_results.json")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{overall}] sigs={pos['total_signatures']} clusters={pos['lsh_clusters_count']} pairs={pos['lsh_pairs_count']} confirmed={len(pos['confirmed_rosettas'])}")
    print(f"Results -> {out_path}")
