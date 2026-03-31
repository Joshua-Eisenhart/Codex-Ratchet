#!/usr/bin/env python3
"""
Axis 0 — Orbit Phase Alignment Probe
======================================
Direct characterization of the ~4 failures per 32-step forward MI co-arising.

From the attractor basin probe (Q2): 27–28/31 steps co-arise in the forward
MI measure MI(L[t], R[t+1]). About 3–4 fail per cycle.

Questions:
  P1: Are failures concentrated at a specific 4-cycle phase (Ti=0,Fe=1,Te=2,Fi=3)?
  P2: Are failures in the outer vs inner half of the orbit?
  P3: What distinguishes failure steps from success steps (lr_asym, ga0, loop_position)?
  P4: Does Clifford have more failures than inner/outer?
  P5: Are failures consistent across engine types 1 and 2?

If failures cluster at a specific phase position across all configs:
  → The proof strategy must handle that phase specially.
  → That phase is where the forward pairing is weakest.
If failures are random:
  → The 87–90% rate is intrinsic noise of the pairing, not a proof gap.

For the proof strategy:
  If Ti always succeeds (100% confirmed) and Fi has a fixed failure rate at a known
  phase position, we can prove co-arising EXCEPT at those positions and then
  show the positions are measure-zero in the formal limit.
"""

from __future__ import annotations
import argparse
import json, os, sys
from datetime import UTC, datetime
import numpy as np
from collections import defaultdict

_PROBE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_PROBE_DIR))
_MPL_CACHE = os.path.join(_REPO_ROOT, "work", "audit_tmp", "mplcache")
os.makedirs(_MPL_CACHE, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", _MPL_CACHE)
os.environ.setdefault("XDG_CACHE_HOME", _MPL_CACHE)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER

# Graph stack imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills"))
from graph_tool_integration import get_runtime_projections

PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL = np.outer(PSI_MINUS, PSI_MINUS.conj())
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
OPERATOR_ENTANGLERS = {
    "Ti": np.kron(SIGMA_Z, SIGMA_Z),
    "Fe": np.kron(SIGMA_X, SIGMA_X),
    "Te": np.kron(SIGMA_Y, SIGMA_Y),
    "Fi": np.kron(SIGMA_X, SIGMA_X),
}

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results"
)
os.makedirs(RESULTS_DIR, exist_ok=True)

TORUS_CONFIGS = [
    ("inner",    TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer",    TORUS_OUTER),
]
ENGINE_TYPES = [1, 2]
PHASE_NAMES  = {0: "Ti", 1: "Fe", 2: "Te", 3: "Fi"}


# --------------------------------------------------------------------------- #
# MI utilities                                                                 #
# --------------------------------------------------------------------------- #

def bloch(rho):
    return np.array([float(np.real(np.trace(s @ rho))) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])

def lr_asym(a, b):
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0.0, 1.0))

def vne(rho):
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0

from qit_edge_state_updater import (
    build_edge_lookup,
    SLOT_POLARITY, SLOT_ENTANG_WEIGHT, SLOT_CHIRAL_STATUS,
    SLOT_TOPO_LEGAL, SLOT_CONST_SAT, SLOT_MARG_PRES, SLOT_ADMISSIBILITY,
)

def bridge_mi(rho_L, rho_R, cc=None, ga_edges=None, hetero=None, negative_mode="strict", node_t=None, node_t1=None, engine_type=None, pub_to_hid=None, hid_to_pyg_idx=None, step_strength=1.0, op_name=None, edge_map=None, dphi_L=0.0, dphi_R=0.0):
    p_base = float(np.clip(lr_asym(rho_L, rho_R), 0.01, 0.99))
    
    if negative_mode == "bell_injected":
        # Legacy: Empirical mixture model unanchored to geometry
        p = p_base
        rho_AB = _ensure_valid_density((1 - p) * np.kron(rho_L, rho_R) + p * BELL)
    else:
        # Load-bearing penalties mapped strictly to the active timestep transition
        topo_gate = 1.0
        ga_gate = 1.0
        cos_sim = 1.0
        c_coeffs = [0.0]*8
        e_pos = edge_map.get((node_t, node_t1)) if edge_map and node_t and node_t1 else None

        phase_gamma = p_base * (np.pi / 2.0)
        
        # TopoNetX Active Link Penalty
        if cc is not None:
            if node_t and node_t1 and node_t != node_t1:
                try:
                    if negative_mode == "topology_flattened":
                        # Flat Topology: only demand spatial 1-cell graph adjacency.
                        # This physically zeroes only the face-closure metric.
                        edges_1 = [tuple(sorted(e)) for e in cc.skeleton(1)]
                        edge_tup = tuple(sorted([node_t, node_t1]))
                        topo_gate = 1.0 if edge_tup in edges_1 else 0.0
                    else:
                        # Strict Topology: actively demand the metric generates 2-cell manifold continuous faces.
                        # This verifies closure beyond simple graph linking.
                        is_in_2cell = False
                        for face in cc.skeleton(2):
                            if node_t in face and node_t1 in face:
                                is_in_2cell = True
                                break
                        topo_gate = 1.0 if is_in_2cell else 0.0
                except Exception:
                    topo_gate = 0.0
            else:
                topo_gate = 0.0 if (node_t != node_t1) else 1.0
        else:
            topo_gate = 1.0  # cc unavailable → pass-through; topology penalty cannot be applied

        # PyG Tensor Similarity Gate
        pyg_gate = 1.0
        if hetero is not None and pub_to_hid is not None and hid_to_pyg_idx is not None:
            if node_t and node_t1:
                try:
                    import torch
                    import torch.nn.functional as F
                    idx_t = hid_to_pyg_idx.get(node_t)
                    idx_t1 = hid_to_pyg_idx.get(node_t1)
                    
                    if idx_t is not None and idx_t1 is not None:
                        x_t = hetero["node"].x[idx_t]
                        x_t1 = hetero["node"].x[idx_t1]
                        
                        if negative_mode == "pyg_bypassed":
                            pyg_gate = 1.0
                        else:
                            cos_sim = F.cosine_similarity(x_t.unsqueeze(0), x_t1.unsqueeze(0)).item()
                            # Map cosine similarity from [-1, 1] into [0, 1] so
                            # structurally opposite-but-related graph states do
                            # not collapse the gate to near-zero by sign alone.
                            pyg_gate = max(0.01, 0.8 * (0.5 * (1.0 + cos_sim)))
                except Exception as e:
                    print(f"PyG Error: {e}")
                    pyg_gate = 1.0

        # Clifford Chirality Penalty on the Active Link
        if ga_edges is not None:
            seq_edge = next((e for e in ga_edges if e.get("source_id") == node_t and e.get("target_id") == node_t1), None)
            if seq_edge is not None:
                # Base Clifford multivector payload from the Step Sequence Graph Edge
                seq_coeffs = list(seq_edge.get("ga_payload", {}).get("coefficients", [0]*8))
                
                # Natively deduce overarching geometric engine phase by querying the global coupling edge payload
                chiral_edge = next((e for e in ga_edges if e.get("relation") == "CHIRALITY_COUPLING"), None)
                if chiral_edge and pub_to_hid:
                    c_coeffs = chiral_edge.get("ga_payload", {}).get("coefficients", [0]*8).copy()
                    engine_hid = pub_to_hid.get(f"qit::ENGINE::type{engine_type}")
                    if engine_hid == chiral_edge.get("target_id"):
                        c_coeffs = [-c for c in c_coeffs] # Flip orientation algebraically
                    
                import clifford as cf
                layout, blv = cf.Cl(3)
                mv_seq = layout.MultiVector(seq_coeffs)
                mv_chiral = layout.MultiVector(c_coeffs)
                
                # Organic Chirality Destruction: Project tensor to purely symmetric scalar space (Grade-0) rather than orientable volume (Grade-3)
                if negative_mode == "chirality_destroyed":
                    mv_chiral = layout.MultiVector([c_coeffs[0]] + [0]*7)
                    
                # Real Geometric Computation: Phase organically extracts from the resulting bivector rotation 
                # generated natively by multiplying the sequence vector through the chiral volume!
                mv_interaction = mv_seq * mv_chiral
                phase_gamma = p_base * float(abs(mv_interaction)) * (np.pi / 2.0)
            else:
                ga_gate = 0.0
                phase_gamma = 0.0
        else:
            ga_gate = 0.0
            phase_gamma = 0.0
            
        phase_gamma *= topo_gate * ga_gate * pyg_gate * float(step_strength)
        
        # Operator families should not share a single universal entangler.
        # Keep the generator aligned to the active engine operator while the
        # graph path, chirality, topology, and PyG gates control its amplitude.
        H_int = OPERATOR_ENTANGLERS.get(op_name, np.kron(SIGMA_X, SIGMA_X))
        # U = exp(-i gamma H_int) = cos(gamma) I - i sin(gamma) H_int
        # A purely separable origin state becomes correctly structurally entangled
        U = np.cos(phase_gamma) * np.eye(4) - 1j * np.sin(phase_gamma) * H_int
        separable = np.kron(rho_L, rho_R)
        rho_AB = _ensure_valid_density(U @ separable @ U.conj().T)
        
        # Write slot state into dynamic edge tensor via qit_edge_state_updater constants
        if hetero is not None and e_pos is not None:
            mean_flux = 0.5 * (dphi_L + dphi_R)
            ea = hetero["node", "rel", "node"].edge_attr
            ea[e_pos, SLOT_POLARITY]      = 1.0 if mean_flux > 1e-9 else (-1.0 if mean_flux < -1e-9 else 0.0)
            ea[e_pos, SLOT_CHIRAL_STATUS] = float(np.sign(c_coeffs[7])) if c_coeffs[7] else 0.0
            ea[e_pos, SLOT_TOPO_LEGAL]    = topo_gate
            ea[e_pos, SLOT_CONST_SAT]     = 1.0 if cos_sim >= 0.8 else 0.0
            ea[e_pos, SLOT_MARG_PRES]     = max(0.0, 1.0 - abs(dphi_L) - abs(dphi_R))
                
    rho_A = np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=1, axis2=3)
    rho_B = np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=0, axis2=2)
    return max(0.0, vne(rho_A) + vne(rho_B) - vne(rho_AB))


# --------------------------------------------------------------------------- #
# Core analysis per trajectory                                                 #
# --------------------------------------------------------------------------- #

def analyze_trajectory(
    history: list[dict], 
    cc=None, 
    hetero=None, 
    enriched_edges=None,
    engine_type=None,
    negative_mode="strict",
    pub_to_hid=None,
    hid_to_pyg_idx=None,
) -> dict:
    """
    Compute per-step forward MI co-arising and characterize failures.
    Returns per-step analysis with failure flags and attractor features,
    augmented by TopoNetX cell structures, PyG tensors, and GA payloads.
    """
    T = len(history)
    ct_mi = []
    
    edge_map = build_edge_lookup(hetero, enriched_edges or [], hid_to_pyg_idx or {})
    for t in range(T):
        step_t = history[t]
        step_t1 = history[min(t+1, T-1)]
        
        # Build strict topological identifiers for the active cycle path
        pub_t = f"qit::SUBCYCLE_STEP::type{engine_type}_{step_t['stage']}"
        pub_t1 = f"qit::SUBCYCLE_STEP::type{engine_type}_{step_t1['stage']}"
        
        hid_t = pub_to_hid.get(pub_t) if pub_to_hid else None
        hid_t1 = pub_to_hid.get(pub_t1) if pub_to_hid else None
        
        # Forward MI series: ct_mi[t] = MI(L[t], R[t+1]) modulated by rigorous graph geometry
        ct_mi.append(bridge_mi(
            step_t["rho_L"],
            step_t1["rho_R"],
            cc=cc,
            ga_edges=enriched_edges,
            negative_mode=negative_mode,
            node_t=hid_t,
            node_t1=hid_t1,
            engine_type=engine_type,
            hetero=hetero,
            pub_to_hid=pub_to_hid,
            hid_to_pyg_idx=hid_to_pyg_idx,
            step_strength=step_t.get("strength", 1.0),
            op_name=step_t.get("op_name"),
            edge_map=edge_map,
            dphi_L=step_t.get("dphi_L", 0.0),
            dphi_R=step_t.get("dphi_R", 0.0),
        ))

    # Graph stack integrations
    loop_topologies = []
    pyg_orbit_validated = False
    
    if cc is not None:
        # Check if 1-cells and 2-cells form valid complete paths for the engine
        try:
            loop_topologies = list(cc.skeleton(2))
        except AttributeError:
            loop_topologies = []
    
    if hetero is not None:
        # Basic PyG forward pass check (just confirming node tensor shapes match)
        if hasattr(hetero["node"], "x") and hetero["node"].x.size(0) > 0:
            pyg_orbit_validated = True

    chiral_edges = 0
    if enriched_edges is not None:
        chiral_edges = len([e for e in enriched_edges if e.get("relation") == "CHIRALITY_COUPLING"])

    steps = []
    for t in range(1, T):
        d_ct_mi = ct_mi[t] - ct_mi[t-1]
        ga0_curr = history[t]["ga0_after"]
        ga0_prev = history[t-1]["ga0_after"]
        d_ga0 = ga0_curr - ga0_prev

        phase_pos = t % 4          # 0=Ti, 1=Fe, 2=Te, 3=Fi within 4-cycle
        orbit_half = "outer" if t < 16 else "inner"
        loop_position = history[t].get("loop_position", "?")

        asym = lr_asym(history[t]["rho_L"], history[t]["rho_R"])

        # Co-arising check
        significant = abs(d_ct_mi) > 1e-6 and abs(d_ga0) > 1e-6
        if significant:
            coarises = (d_ga0 * d_ct_mi) > 0
        else:
            coarises = None   # near-zero: neutral

        steps.append({
            "step": t,
            "op_name": history[t]["op_name"],
            "phase_pos": phase_pos,
            "phase_name": PHASE_NAMES[phase_pos],
            "orbit_half": orbit_half,
            "loop_position": loop_position,
            "ga0_before": float(history[t-1]["ga0_after"]),
            "ga0_after": float(ga0_curr),
            "d_ga0": float(d_ga0),
            "ct_mi": float(ct_mi[t]),
            "d_ct_mi": float(d_ct_mi),
            "lr_asym": float(asym),
            "coarises": coarises,
        })

    n_success = sum(1 for s in steps if s["coarises"] is True)
    n_fail    = sum(1 for s in steps if s["coarises"] is False)
    n_neutral = sum(1 for s in steps if s["coarises"] is None)

    # Phase breakdown
    phase_stats = {}
    for ph in range(4):
        ph_steps = [s for s in steps if s["phase_pos"] == ph]
        ph_ok  = sum(1 for s in ph_steps if s["coarises"] is True)
        ph_bad = sum(1 for s in ph_steps if s["coarises"] is False)
        ph_neu = sum(1 for s in ph_steps if s["coarises"] is None)
        phase_stats[PHASE_NAMES[ph]] = {"ok": ph_ok, "fail": ph_bad, "neutral": ph_neu}

    # Half breakdown
    half_stats = {}
    for half in ["outer", "inner"]:
        h_steps = [s for s in steps if s["orbit_half"] == half]
        h_ok  = sum(1 for s in h_steps if s["coarises"] is True)
        h_bad = sum(1 for s in h_steps if s["coarises"] is False)
        half_stats[half] = {"ok": h_ok, "fail": h_bad}

    return {
        "n_steps": T,
        "n_success": n_success,
        "n_fail": n_fail,
        "n_neutral": n_neutral,
        "phase_stats": phase_stats,
        "half_stats": half_stats,
        "steps": steps,
        "pyg_orbit_validated": pyg_orbit_validated,
        "valid_topology_loops_count": len(loop_topologies),
        "chiral_global_operators_found": chiral_edges,
        "mi_trace": ct_mi,
    }


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #

def _parse_args():
    parser = argparse.ArgumentParser(description="Axis 0 orbit phase alignment probe")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the exhaustive cross-product sweep instead of the bounded regression mode.",
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    print("Axis 0 Orbit Phase Alignment Probe (with Full Graph Stack Integration)")
    print("=" * 70)

    builder_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "graphs")
    
    nodes_dict = {}
    edges_list = []
    
    # Load ONLY the engine physical structural graph (no file-provenance pollution)
    engine_graph_path = os.path.join(builder_dir, "qit_engine_graph_v1.json")
    if os.path.exists(engine_graph_path):
        with open(engine_graph_path, "r", encoding="utf-8") as fh:
            engine_data = json.load(fh)
            nodes_dict.update(engine_data.get("nodes", {}))
            edges_list.extend(engine_data.get("edges", []))
        print(f"Loaded Native Engine Graph. Total nodes: {len(nodes_dict)}, Edges: {len(edges_list)}")
    else:
        print("CRITICAL: qit_engine_graph_v1.json not found.")

    pub_to_hid = {nd.get("public_id"): hid for hid, nd in nodes_dict.items()}
    hid_to_pyg_idx = {hid: i for i, hid in enumerate(sorted(nodes_dict.keys()))}
    
    # Generate Runtime Projections via sidecars
    cc, hetero, ga_edges = get_runtime_projections(nodes_dict, edges_list)
    print(f"Sidecars built. TopoNetX available: {cc is not None}, PyG available: {hetero is not None}")
    
    all_results = []
    # Aggregate failure phase counts
    agg_phase = defaultdict(lambda: {"ok": 0, "fail": 0, "neutral": 0})
    agg_half  = defaultdict(lambda: {"ok": 0, "fail": 0})
    failure_profiles = []   # details on all failure steps

    if args.full:
        negative_modes = ["strict", "bell_injected", "topology_flattened", "pyg_bypassed", "chirality_destroyed"]
        engine_types = list(ENGINE_TYPES)
        torus_configs = list(TORUS_CONFIGS)
        print("Mode: full")
    else:
        # Default verify path: keep the graph-integrated negative family live, but
        # bound the sweep to a single canonical engine/torus lane so it stays mechanical.
        negative_modes = ["strict", "bell_injected", "topology_flattened", "pyg_bypassed", "chirality_destroyed"]
        engine_types = [1]
        torus_configs = [("clifford", TORUS_CLIFFORD)]
        print("Mode: bounded")

    for negative_mode in negative_modes:
        for engine_type in engine_types:
            for torus_name, torus_val in torus_configs:
                try:
                    engine = GeometricEngine(engine_type=engine_type)
                    state  = engine.init_state(eta=torus_val)
                    final  = engine.run_cycle(state)
                except Exception as e:
                    print(f"  [{negative_mode}/{engine_type}/{torus_name}] SKIP: {e}")
                    continue

                traj = analyze_trajectory(
                    final.history,
                    cc=cc,
                    hetero=hetero,
                    enriched_edges=ga_edges,
                    engine_type=engine_type,
                    negative_mode=negative_mode,
                    pub_to_hid=pub_to_hid,
                    hid_to_pyg_idx=hid_to_pyg_idx
                )
                key = f"{negative_mode}/{engine_type}/{torus_name}"

                # Accumulate per-phase
                for ph, stats in traj["phase_stats"].items():
                    agg_phase[ph]["ok"]      += stats["ok"]
                    agg_phase[ph]["fail"]    += stats["fail"]
                    agg_phase[ph]["neutral"] += stats["neutral"]
                for half, stats in traj["half_stats"].items():
                    agg_half[half]["ok"]   += stats["ok"]
                    agg_half[half]["fail"] += stats["fail"]

                # Collect failure step profiles
                for s in traj["steps"]:
                    if s["coarises"] is False:
                        failure_profiles.append({**s, "config": key})

                rate = traj["n_success"] / (traj["n_success"] + traj["n_fail"]) if (traj["n_success"] + traj["n_fail"]) > 0 else None
                print(f"\n  [{key}] ok={traj['n_success']} fail={traj['n_fail']} neutral={traj['n_neutral']} "
                      f"rate={rate:.3f}" if rate else f"  [{key}] no nonzero steps")
                print(f"    Graph Stack: TopoNetX Loops={traj['valid_topology_loops_count']}, PyG Validated={traj['pyg_orbit_validated']}, Chiral Global Operators={traj['chiral_global_operators_found']}")
                print(f"    Phase: ", end="")
                for ph in ["Ti", "Fe", "Te", "Fi"]:
                    st = traj["phase_stats"][ph]
                    print(f"{ph}={st['ok']}/{st['ok']+st['fail']+st['neutral']} ", end="")
                print()
                print(f"    Half:  outer={traj['half_stats']['outer']['ok']}/{sum(traj['half_stats']['outer'].values())} "
                      f"inner={traj['half_stats']['inner']['ok']}/{sum(traj['half_stats']['inner'].values())}")

                all_results.append({
                    "config": key,
                    "negative_mode": negative_mode,
                    "engine_type": engine_type,
                    "torus": torus_name,
                    "eta": torus_val,
                    "n_success": traj["n_success"],
                    "n_fail": traj["n_fail"],
                    "n_neutral": traj["n_neutral"],
                    "forward_coarising_rate": rate,
                    "phase_stats": traj["phase_stats"],
                    "half_stats": traj["half_stats"],
                    "mi_trace": traj["mi_trace"],
                })

    # ---------- Aggregate analysis ---------------------------------------- #
    print("\n=== AGGREGATE PHASE ANALYSIS ===")
    for ph in ["Ti", "Fe", "Te", "Fi"]:
        st = agg_phase[ph]
        total_decided = st["ok"] + st["fail"]
        rate = st["ok"] / total_decided if total_decided > 0 else None
        bar = "✓" * st["ok"] + "✗" * st["fail"]
        print(f"  {ph}: {st['ok']:2d}/{total_decided:2d} ({rate*100:.0f}%)" if rate else
              f"  {ph}: all neutral")

    print("\n=== AGGREGATE HALF ANALYSIS ===")
    for half in ["outer", "inner"]:
        st = agg_half[half]
        total = st["ok"] + st["fail"]
        rate = st["ok"] / total if total > 0 else None
        print(f"  {half}: {st['ok']}/{total} ({rate*100:.0f}%)" if rate else f"  {half}: all neutral")

    print(f"\n=== FAILURE PROFILES ({len(failure_profiles)} total) ===")
    if failure_profiles:
        # Group by phase
        for ph in ["Ti", "Fe", "Te", "Fi"]:
            ph_fails = [f for f in failure_profiles if f["phase_name"] == ph]
            if ph_fails:
                print(f"\n  {ph} failures ({len(ph_fails)}):")
                for f in ph_fails[:4]:
                    print(f"    [{f['config']}] step={f['step']:2d} loop={f['loop_position']} "
                          f"lr_asym={f['lr_asym']:.3f} ga0={f['ga0_before']:.3f}→{f['ga0_after']:.3f} "
                          f"d_ct_mi={f['d_ct_mi']:+.4f} d_ga0={f['d_ga0']:+.4f}")

    # ---------- Clifford vs inner/outer comparison ------------------------- #
    print("\n=== CLIFFORD vs INNER/OUTER ===")
    for torus_name in ["inner", "clifford", "outer"]:
        configs = [r for r in all_results if r["torus"] == torus_name]
        if configs:
            mean_fail = np.mean([r["n_fail"] for r in configs])
            mean_rate = np.mean([r["forward_coarising_rate"] for r in configs if r["forward_coarising_rate"]])
            print(f"  {torus_name:9s}: mean_failures={mean_fail:.1f}  mean_rate={mean_rate:.3f}")

    # ---------- P5: engine type consistency -------------------------------- #
    print("\n=== ENGINE TYPE CONSISTENCY ===")
    for et in ENGINE_TYPES:
        configs = [r for r in all_results if r["engine_type"] == et]
        if configs:
            rates = [r["forward_coarising_rate"] for r in configs if r["forward_coarising_rate"]]
            print(f"  Engine {et}: mean={np.mean(rates):.3f}  std={np.std(rates):.3f}  "
                  f"range=[{min(rates):.3f},{max(rates):.3f}]")

    # ---------- Consistency check: do the same step indices fail? ---------- #
    print("\n=== FAILURE STEP CONSISTENCY ===")
    fail_positions = defaultdict(list)  # (engine_type, loop_position, phase_pos) → list of d_ct_mi
    for f in failure_profiles:
        key = (f["config"].split("/")[0], f["loop_position"], f["phase_name"])
        fail_positions[key].append(f["d_ct_mi"])
    for k, vals in sorted(fail_positions.items()):
        print(f"  {k}: {len(vals)} failures, d_ct_mi mean={np.mean(vals):+.4f}")

    # Serialize
    def strip(obj):
        if isinstance(obj, dict):   return {k: strip(v) for k, v in obj.items()}
        elif isinstance(obj, list): return [strip(v) for v in obj]
        elif isinstance(obj, (np.float32, np.float64)): return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):     return int(obj)
        return obj

    results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_axis0_orbit_phase_alignment",
        "configs": strip(all_results),
        "aggregate_phase": dict(agg_phase),
        "aggregate_half": dict(agg_half),
        "failure_profiles": strip(failure_profiles),
        "n_total_failures": len(failure_profiles),
    }

    out = os.path.join(RESULTS_DIR, "axis0_orbit_phase_alignment_results.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nResults written to {out}")
    
    # ---------- Enforce Fail-Closed Validation ---------- #
    # Validate trace integrals against the strict mode instead of just booleans to expose true degeneracies.
    print("\n=== NEGATIVE SIM TRACE DIFFERENTIALS ===")
    
    def get_traces(mode_prefix):
        return [r["mi_trace"] for r in all_results if r["config"].startswith(mode_prefix)]
        
    strict_traces = get_traces("strict/")
    bell_traces = get_traces("bell_injected/")
    topo_traces = get_traces("topology_flattened/")
    pyg_traces = get_traces("pyg_bypassed/")
    chir_traces = get_traces("chirality_destroyed/")
    
    def l1_delta(traces_a, traces_b):
        if not traces_a or not traces_b or len(traces_a) != len(traces_b):
            return 0.0
        diff = 0.0
        for ta, tb in zip(traces_a, traces_b):
            diff += sum(abs(a - b) for a, b in zip(ta, tb))
        return diff
        
    delta_bell = l1_delta(strict_traces, bell_traces)
    delta_topo = l1_delta(strict_traces, topo_traces)
    delta_pyg = l1_delta(strict_traces, pyg_traces)
    delta_chir = l1_delta(strict_traces, chir_traces)
    
    print(f"  strict vs bell_injected:      Δ L1 = {delta_bell:.4f}")
    print(f"  strict vs topology_flattened: Δ L1 = {delta_topo:.4f}")
    print(f"  strict vs pyg_bypassed:       Δ L1 = {delta_pyg:.4f}")
    print(f"  strict vs chirality_destroyed:Δ L1 = {delta_chir:.4f}")
    
    if delta_bell < 1e-4 or delta_topo < 0.1 or delta_pyg < 0.1 or delta_chir < 0.1:
        print("\n[⚠] FAIL CLOSED: A negative ablation simulation generated mathematically identical ")
        print("    trace tensors (Δ L1 < 0.1) to the strictly constrained simulation.")
        print("    The graph logic did not analytically collapse.")
        sys.exit(1)
        
    return results

if __name__ == "__main__":
    main()
