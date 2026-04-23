#!/usr/bin/env python3
"""
sim_c2_entropy_structure_search.py
==================================

Entropy Structure [Band C2]
----------------------------
1. Positive Witness: Tying the informational entropy readout explicitly to 
   the admitted 4x4 joint-state carrier (rho_AB).
2. Negative Controls (Shortcut Ablation):
   - Classical Shannon Shortcut: Proving that Shannon entropy of populations 
     fails to capture the non-classical coherent information signal.
   - Purity-Only Proxy: Testing if state purity (Tr(rho^2)) is an insufficient 
     proxy for the full entropic gradient.

Math Source: Improved Dependency Chain (Order 8)
"""

import json
import os
from collections import defaultdict
from datetime import datetime, UTC
import numpy as np
from typing import Dict, List, Tuple

import sys
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical bridge baseline: this searches C2 entropy-structure witnesses numerically on the admitted carrier, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "joint-state entropy family and control-ablation numerics"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, EngineState, StageControls, TERRAINS
from geometric_operators import (
    apply_Ti_4x4, apply_Fe_4x4, apply_Te_4x4, apply_Fi_4x4,
    partial_trace_A, partial_trace_B, _ensure_valid_density
)
from stage_matrix_neg_lib import (
    all_stage_rows, init_stage, baseline_controls
)

# ═══════════════════════════════════════════════════════════════════
# FULL ENTROPY FAMILY (NO SHORTHAND)
# ═══════════════════════════════════════════════════════════════════

def get_entropy_family(rho_AB: np.ndarray) -> Dict[str, float]:
    """
    Computes the full Von Neumann entropy family for the 4x4 joint state.
    """
    def s_vn(rho: np.ndarray) -> float:
        """S(rho) = -Tr(rho log2 rho)"""
        evals = np.linalg.eigvalsh(rho)
        evals = evals[evals > 1e-15]
        return float(-np.sum(evals * np.log2(evals)))

    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    
    s_AB = s_vn(rho_AB)
    s_A = s_vn(rho_A)
    s_B = s_vn(rho_B)
    
    # Mutual Information: I(A:B) = S(A) + S(B) - S(AB)
    mi = s_A + s_B - s_AB
    # Conditional Entropy: S(A|B) = S(AB) - S(B)
    cond_ent = s_AB - s_B
    # Coherent Information: Ic(A>B) = S(B) - S(AB)
    coh_info = s_B - s_AB
    
    return {
        "S_AB": s_AB,
        "S_A": s_A,
        "S_B": s_B,
        "I_AB": mi,
        "S_A_given_B": cond_ent,
        "Ic_A_to_B": coh_info
    }

# ═══════════════════════════════════════════════════════════════════
# NEGATIVE: CLASSICAL SHANNON SHORTCUT
# ═══════════════════════════════════════════════════════════════════

def get_shannon_shortcut(rho_AB: np.ndarray) -> Dict[str, float]:
    """
    H(p) = -sum(pi log2 pi) using ONLY the diagonal populations.
    This simulates a 'classical' observer who ignores coherence.
    """
    pops = np.real(np.diag(rho_AB))
    pops = pops[pops > 1e-15]
    h_AB = float(-np.sum(pops * np.log2(pops)))
    
    # Marginal Shannon entropies
    pops_A = np.real(np.diag(_ensure_valid_density(partial_trace_B(rho_AB))))
    pops_A = pops_A[pops_A > 1e-15]
    h_A = float(-np.sum(pops_A * np.log2(pops_A)))
    
    pops_B = np.real(np.diag(_ensure_valid_density(partial_trace_A(rho_AB))))
    pops_B = pops_B[pops_B > 1e-15]
    h_B = float(-np.sum(pops_B * np.log2(pops_B)))
    
    return {
        "H_AB": h_AB,
        "Ic_shannon": h_B - h_AB # The "fake" coherent info
    }

# ═══════════════════════════════════════════════════════════════════
# NEGATIVE: PURITY-ONLY PROXY
# ═══════════════════════════════════════════════════════════════════

def get_purity_proxy(rho_AB: np.ndarray) -> Dict[str, float]:
    """
    Purity-only proxy control: uses Tr(rho^2) on joint and marginal states.
    Does NOT use eigenvalues or logarithms — deliberately surface-limited.

    Purity-proxy Ic analogous to Ic(A>B) = S(B) - S(AB):
      purity_Ic = Tr(rho_B^2) - Tr(rho_AB^2)

    If purity_Ic > 0 wherever vn_Ic > 0, purity is a sufficient proxy
    and the VN coherent information signal is not doing unique work.
    If purity_Ic <= 0 when vn_Ic > 0, the proxy is killed — VN is necessary.
    """
    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))

    purity_AB = float(np.real(np.trace(rho_AB @ rho_AB)))
    purity_A  = float(np.real(np.trace(rho_A  @ rho_A)))
    purity_B  = float(np.real(np.trace(rho_B  @ rho_B)))

    # Direct purity-difference analog of S(B) - S(AB)
    purity_Ic = purity_B - purity_AB

    return {
        "purity_AB": purity_AB,
        "purity_A":  purity_A,
        "purity_B":  purity_B,
        "purity_Ic": purity_Ic,
    }

# ═══════════════════════════════════════════════════════════════════
# GRAPH ARTIFACT
# ═══════════════════════════════════════════════════════════════════

def build_c2_graph_artifact(results: List[Dict]) -> Dict:
    """
    Build a minimal entropy-polarity contrast graph from C2 stage results.

    Nodes: one per stage result (16 nodes), labelled by stage+op.
    Edges: directed from vn_Ic-positive nodes to vn_Ic-negative nodes
           within the same terrain label (WIN, LOSE, win, lose).

    Edge weight = vn_Ic_gap (positive.vn_Ic - negative.vn_Ic).
    Captures the Fe/Fi vs Ti/Te entropy polarity contrast structure.
    Each edge also records whether shortcut and purity controls fired at
    each endpoint — so the graph carries the discrimination audit trail.
    """
    nodes = []
    for r in results:
        nodes.append({
            "id": f"{r['stage']}_{r['op']}",
            "stage": r["stage"],
            "op": r["op"],
            "vn_Ic": round(r["vn_Ic"], 6),
            "purity_Ic": round(r["purity_Ic"], 6),
            "is_vn_positive": r["vn_Ic"] > 0,
            "is_shortcut_killed": r["is_shortcut_killed"],
            "is_purity_proxy_killed": r["is_purity_proxy_killed"],
        })

    by_terrain = defaultdict(list)
    for n in nodes:
        by_terrain[n["stage"]].append(n)

    edges = []
    for terrain, tnodes in sorted(by_terrain.items()):
        pos = [n for n in tnodes if n["is_vn_positive"]]
        neg = [n for n in tnodes if not n["is_vn_positive"]]
        for p in pos:
            for n in neg:
                edges.append({
                    "src": p["id"],
                    "dst": n["id"],
                    "terrain": terrain,
                    "edge_type": "entropy_polarity_contrast",
                    "vn_Ic_gap": round(p["vn_Ic"] - n["vn_Ic"], 6),
                    "src_shortcut_killed": p["is_shortcut_killed"],
                    "src_purity_killed": p["is_purity_proxy_killed"],
                    "dst_shortcut_killed": n["is_shortcut_killed"],
                    "dst_purity_killed": n["is_purity_proxy_killed"],
                })

    return {
        "artifact_type": "c2_entropy_polarity_contrast_graph",
        "description": (
            "Bipartite-within-terrain entropy polarity contrast graph. "
            "Directed edges from vn_Ic-positive nodes to vn_Ic-negative nodes "
            "within each terrain label. Edge weight = vn_Ic gap. "
            "Captures Fe/Fi (positive) vs Ti/Te (negative) operator entropy "
            "contrast structure. Discrimination audit trail on each edge."
        ),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


# ═══════════════════════════════════════════════════════════════════
# SIMULATION CORE
# ═══════════════════════════════════════════════════════════════════

def run_c2_search():
    results = []
    joint_ops = {"Ti": apply_Ti_4x4, "Fe": apply_Fe_4x4, "Te": apply_Te_4x4, "Fi": apply_Fi_4x4}
    
    for engine_type, row in all_stage_rows():
        seed = 12000 + engine_type * 10 + row[0]
        engine, state, meta = init_stage(engine_type, row, seed)
        
        rho_AB_init = state.rho_AB.copy()
        op_name = meta["native_operator"]
        op_fn = joint_ops[op_name]
        
        # Evolve the structure
        rho_AB_final = op_fn(rho_AB_init, polarity_up=meta["axis6_up"], strength=0.8)
        
        # 1. HONEST READOUT (VN)
        vn_family = get_entropy_family(rho_AB_final)
        
        # 2. CLASSICAL SHORTCUT (Shannon)
        shannon_family = get_shannon_shortcut(rho_AB_final)

        # 3. PURITY-ONLY PROXY (Tr(rho^2))
        purity_family = get_purity_proxy(rho_AB_final)

        # Analysis:
        # Classical Shannon Ic cannot be positive for a product state or
        # classical mixture (H_AB >= H_B).
        # Only Non-classical Coherent Information can be > 0.
        shortcut_fails = vn_family["Ic_A_to_B"] > 0 and shannon_family["Ic_shannon"] <= 0

        # Purity proxy kill: VN sees positive Ic but purity-difference does not.
        # If purity_Ic > 0 alongside vn_Ic > 0, the proxy survives — report honestly.
        vn_positive = vn_family["Ic_A_to_B"] > 0
        purity_proxy_killed = vn_positive and purity_family["purity_Ic"] <= 0

        results.append({
            "stage": row[3],
            "op": op_name,
            "vn_Ic": vn_family["Ic_A_to_B"],
            "shannon_Ic": shannon_family["Ic_shannon"],
            "shortcut_gap": vn_family["Ic_A_to_B"] - shannon_family["Ic_shannon"],
            "is_shortcut_killed": shortcut_fails,
            "purity_AB": purity_family["purity_AB"],
            "purity_B": purity_family["purity_B"],
            "purity_Ic": purity_family["purity_Ic"],
            "is_purity_proxy_killed": purity_proxy_killed,
        })

    # Admission Verdict
    shortcut_kill_count = sum(1 for r in results if r["is_shortcut_killed"])
    purity_kill_count   = sum(1 for r in results if r["is_purity_proxy_killed"])
    vn_positive_count   = sum(1 for r in results if r["vn_Ic"] > 0)

    # Purity proxy verdict: killed means VN does unique work the proxy misses.
    # Survived means purity tracks VN — which is an honest failure of this control.
    if vn_positive_count == 0:
        purity_verdict = "NO_VN_POSITIVE_STAGES (proxy comparison not exercised)"
    elif purity_kill_count == vn_positive_count:
        purity_verdict = "KILLED (purity proxy fails on all VN-positive stages — VN is necessary)"
    elif purity_kill_count > 0:
        purity_verdict = f"PARTIAL ({purity_kill_count}/{vn_positive_count} VN-positive stages kill the proxy)"
    else:
        purity_verdict = "SURVIVED (purity proxy tracks VN on all positive stages — VN may not be necessary)"

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "C2_status": "PASS (Entropy Structure Admitted)" if shortcut_kill_count > 0 else "FAIL (Classical Shortcut Admitted)",
        "summary": {
            "classical_shortcut_kills": shortcut_kill_count,
            "purity_proxy_kills": purity_kill_count,
            "vn_positive_stages": vn_positive_count,
            "purity_proxy_verdict": purity_verdict,
            "total_stages": 16,
            "reason": "Shannon shortcut fails to capture positive coherent information.",
        },
        "results": results
    }
    
    # Graph artifact
    graph_artifact = build_c2_graph_artifact(results)
    graph_artifact_filename = "c2_entropy_polarity_graph.json"

    out_dir = "a2_state/sim_results"
    os.makedirs(out_dir, exist_ok=True)

    graph_path = os.path.join(out_dir, graph_artifact_filename)
    with open(graph_path, "w") as f:
        json.dump(graph_artifact, f, indent=2)
    print(f"Wrote {graph_path}")

    payload["graph_artifact"] = {
        "file": graph_artifact_filename,
        "node_count": graph_artifact["node_count"],
        "edge_count": graph_artifact["edge_count"],
        "artifact_type": graph_artifact["artifact_type"],
    }

    out_path = os.path.join(out_dir, "c2_entropy_structure_search_results.json")
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    run_c2_search()
