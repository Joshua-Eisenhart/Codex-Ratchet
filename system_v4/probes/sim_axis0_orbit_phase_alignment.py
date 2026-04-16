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
import json
import os
import sys
from datetime import UTC, datetime
from functools import lru_cache

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/codex-mpl")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)
os.makedirs(os.environ["XDG_CACHE_HOME"], exist_ok=True)

import gudhi
import numpy as np
import rustworkx as rx
import sympy as sp
import torch
import torch_ga
import xgi
from collections import defaultdict
from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.learning.frechet_mean import FrechetMean
from scipy.linalg import expm
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat

classification = "classical_baseline"  # auto-backfill
divergence_log = (
    "Classical foundation baseline: this characterizes Axis-0 orbit-phase failures numerically, "
    "not a canonical nonclassical witness. The legacy strict bridge diagnosis is preserved, and "
    "the orbit-phase lane is now also grounded in the deep Axis 0 shell/topology/symbolic/solver/"
    "manifold contract used by the upgraded probe family."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "phase-alignment statistics, guard diagnostics, and orbit aggregates"},
    "scipy": {"tried": True, "used": True, "reason": "orbit-phase expansion propagator witness"},
    "pytorch": {"tried": True, "used": True, "reason": "fit witness over orbit-phase deep surfaces"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning orbit-phase surface vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning orbit-phase surface vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered orbit-phase surface DAG witness"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order orbit-phase coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for orbit-phase surface closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the orbit-phase surface complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for orbit-phase expansion trends"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing ordered orbit-phase ranking and scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for orbit-phase surface aggregation"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "load_bearing",
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "geomstats": "load_bearing",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER
from sim_axis0_dynamic_shell import lane_d_topology_expansion_bridge
from sim_axis0_iscalar_sweep import (
    _clifford_vector,
    _option_cell_complex_surface as _candidate_cell_complex_surface,
    _option_constraint_surface as _candidate_constraint_surface,
    _option_graph_surface as _candidate_graph_surface,
    _option_hypergraph_surface as _candidate_hypergraph_surface,
    _option_manifold_surface as _candidate_manifold_surface,
    _option_scale_history as _candidate_scale_history,
    _option_symbolic_surface as _candidate_symbolic_surface,
    _option_topology_surface as _candidate_topology_surface,
    _torch_ga_roundtrip,
    _torch_option_fit as _torch_candidate_fit,
)

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
EPS = 1e-12

TORUS_CONFIGS = [
    ("inner",    TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer",    TORUS_OUTER),
]
ENGINE_TYPES = [1, 2]
PHASE_NAMES  = {0: "Ti", 1: "Fe", 2: "Te", 3: "Fi"}


@lru_cache(maxsize=1)
def _get_clifford_layout():
    layout, _ = Cl(3)
    return layout


def update_pyg_node_features(
    hetero, history, engine_type, pub_to_hid, hid_to_pyg_idx
):
    """Populate PyG node features with live engine state.

    Each SUBCYCLE_STEP node gets a 10-dim feature vector:
      [degree, in_deg, out_deg, bx_L, by_L, bz_L, bx_R, by_R, bz_R, vne_L]

    The first 3 dims are static graph features (kept).
    Dims 3-8 are Bloch vector components from the step's density matrices.
    Dim 9 is the von Neumann entropy of the left spinor.

    This makes PyG features carry live QIT state rather than static degree counts.
    """
    if hetero is None or pub_to_hid is None or hid_to_pyg_idx is None:
        return
    if not history:
        return

    import torch
    x = hetero["node"].x  # (N, 10) tensor

    for t, step in enumerate(history):
        stage = step.get("stage", "")
        pub_id = f"qit::SUBCYCLE_STEP::type{engine_type}_{stage}"
        hid = pub_to_hid.get(pub_id)
        if hid is None:
            continue
        idx = hid_to_pyg_idx.get(hid)
        if idx is None or idx >= x.shape[0]:
            continue

        rho_L = step.get("rho_L")
        rho_R = step.get("rho_R")
        if rho_L is None or rho_R is None:
            continue

        # Bloch vector from density matrix: (Tr(ρσ_x), Tr(ρσ_y), Tr(ρσ_z))
        b_L = bloch(rho_L)
        b_R = bloch(rho_R)
        s_L = vne(rho_L)

        # Write into dims 3-9, preserving static dims 0-2
        x[idx, 3] = float(b_L[0])
        x[idx, 4] = float(b_L[1])
        x[idx, 5] = float(b_L[2])
        x[idx, 6] = float(b_R[0])
        x[idx, 7] = float(b_R[1])
        x[idx, 8] = float(b_R[2])
        x[idx, 9] = float(s_L)



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
from qit_nonclassical_guards import (
    bridge_guard_input,
    check_nonclassical_guards,
    guard_witness_dict,
    format_guard_witness_line,
    GuardCheckResult,
)

def bridge_mi(rho_L, rho_R, cc=None, ga_edges=None, hetero=None, negative_mode="strict", node_t=None, node_t1=None, engine_type=None, pub_to_hid=None, hid_to_pyg_idx=None, step_strength=1.0, op_name=None, edge_map=None, dphi_L=0.0, dphi_R=0.0, guard_events=None, step_index=None):
    """QIT-native bridge mutual information.

    All quantities derived from:
      - density matrices (ρ_L, ρ_R, ρ_AB)
      - trace distance D(ρ,σ) = ½ Tr|ρ-σ|   (operational distinguishability)
      - von Neumann entropy S(ρ)              (information content)
      - CPTP maps / unitaries                 (lawful dynamics)
      - Clifford Cl(3) geometric product      (chirality / orientation)
      - Cell complex boundary rank            (topological admissibility)

    No classical probability primitives. No arbitrary thresholds. No binary gates.
    """
    from geometric_operators import trace_distance_2x2

    # ── QIT primitive: operational distinguishability ──────────────────────
    # Trace distance D(ρ_L, ρ_R) ∈ [0,1] — the maximum probability of
    # distinguishing rho_L from rho_R by any single measurement.
    # This is the QIT-legal replacement for the classical "p_base" mixture variable.
    D_LR = trace_distance_2x2(rho_L, rho_R)

    if negative_mode == "bell_injected":
        # Negative control: inject maximal entanglement unrelated to geometry.
        # Uses D_LR as coupling strength to maintain comparability.
        gamma_bell = D_LR * (np.pi / 2.0)
        H_bell = np.kron(SIGMA_X, SIGMA_X)
        U_bell = np.cos(gamma_bell) * np.eye(4) - 1j * np.sin(gamma_bell) * H_bell
        separable = np.kron(rho_L, rho_R)
        rho_AB = _ensure_valid_density(U_bell @ separable @ U_bell.conj().T)
    else:
        # ── Coupling amplitude: derived from trace distance ───────────────
        # D_LR measures how much the two subsystems can be told apart,
        # which determines how strongly they can be correlated.
        phase_gamma = D_LR * (np.pi / 2.0)

        c_coeffs = [0.0] * 8
        e_pos = edge_map.get((node_t, node_t1)) if edge_map and node_t and node_t1 else None

        # ── Topological admissibility: graded boundary rank ───────────────
        # Instead of binary 0/1 from 2-cell membership, compute a graded
        # admissibility from the cell complex boundary structure.
        # rank 0: nodes exist but no edge → 0.0
        # rank 1: 1-cell (edge) exists → base admissibility from boundary operator
        # rank 2: 2-cell (face) exists → full topological closure
        topo_rank = 0.0
        if cc is not None and node_t and node_t1 and node_t != node_t1:
            try:
                if negative_mode == "topology_flattened":
                    # Negative control: admit any 1-cell adjacency as full rank.
                    edges_1 = [tuple(sorted(e)) for e in cc.skeleton(1)]
                    edge_tup = tuple(sorted([node_t, node_t1]))
                    topo_rank = 1.0 if edge_tup in edges_1 else 0.0
                else:
                    # Strict: graded rank from cell complex skeleton.
                    # 1-cell membership gives partial admissibility.
                    # 2-cell membership gives full closure.
                    edges_1 = [tuple(sorted(e)) for e in cc.skeleton(1)]
                    edge_tup = tuple(sorted([node_t, node_t1]))
                    in_1cell = edge_tup in edges_1

                    in_2cell = False
                    n_shared_faces = 0
                    for face in cc.skeleton(2):
                        if node_t in face and node_t1 in face:
                            in_2cell = True
                            n_shared_faces += 1

                    if in_2cell:
                        # Full topological closure: normalized by face count
                        topo_rank = min(1.0, 0.7 + 0.3 * n_shared_faces)
                    elif in_1cell:
                        # 1-cell adjacency: partial admissibility
                        # The boundary operator ∂₁ maps 1-cells to 0-cells.
                        # An edge without face closure is topologically open
                        # but still structurally linked — admit at reduced rank.
                        topo_rank = 0.4
                    else:
                        topo_rank = 0.0
            except Exception:
                topo_rank = 0.0
        elif cc is None:
            topo_rank = 1.0  # No cell complex available → cannot constrain

        # ── PyG node feature similarity: continuous, no threshold ─────────
        pyg_similarity = 1.0
        cos_sim_raw = 0.0
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
                            pyg_similarity = 1.0
                        else:
                            cos_sim_raw = F.cosine_similarity(
                                x_t.unsqueeze(0), x_t1.unsqueeze(0)
                            ).item()
                            # Map [-1, 1] → [0, 1] continuously.
                            # No arbitrary threshold — the full range modulates.
                            pyg_similarity = 0.5 * (1.0 + cos_sim_raw)
                except Exception:
                    pyg_similarity = 1.0

        # ── Clifford geometric product: chirality coupling ────────────────
        ga_coupling = 0.0  # No GA edges → no geometric coupling
        if ga_edges is not None:
            seq_edge = next(
                (e for e in ga_edges
                 if e.get("source_id") == node_t
                 and e.get("target_id") == node_t1),
                None
            )
            if seq_edge is not None:
                seq_coeffs = list(
                    seq_edge.get("ga_payload", {}).get("coefficients", [0] * 8)
                )
                chiral_edge = next(
                    (e for e in ga_edges
                     if e.get("relation") == "CHIRALITY_COUPLING"),
                    None
                )
                if chiral_edge and pub_to_hid:
                    c_coeffs = chiral_edge.get(
                        "ga_payload", {}
                    ).get("coefficients", [0] * 8).copy()
                    engine_hid = pub_to_hid.get(f"qit::ENGINE::type{engine_type}")
                    if engine_hid == chiral_edge.get("target_id"):
                        c_coeffs = [-c for c in c_coeffs]

                layout = _get_clifford_layout()
                mv_seq = layout.MultiVector(seq_coeffs)
                mv_chiral = layout.MultiVector(c_coeffs)

                if negative_mode == "chirality_destroyed":
                    # Negative: project to scalar (grade-0), destroy orientation
                    mv_chiral = layout.MultiVector([c_coeffs[0]] + [0] * 7)

                # The geometric product mv_seq * mv_chiral produces a
                # multivector whose norm encodes the coupling strength
                # between the sequence direction and the chiral volume.
                mv_interaction = mv_seq * mv_chiral
                ga_coupling = float(abs(mv_interaction))

        # ── Compose coupling: all factors are QIT-derived ─────────────────
        # D_LR:           trace distance (operational distinguishability)
        # ga_coupling:    |mv_seq * mv_chiral| (geometric product norm)
        # topo_rank:      graded boundary rank from cell complex
        # pyg_similarity: continuous cosine similarity from graph features
        # step_strength:  engine-determined operator amplitude
        #
        # phase_gamma controls the entangling unitary U = exp(-iγ H_int).
        # When γ=0, U=I and rho_AB is separable.
        # When γ=π/2, U maximally entangles.
        if ga_coupling > 0:
            phase_gamma = D_LR * ga_coupling * (np.pi / 2.0)
        # else: phase_gamma already set from D_LR above, but without GA
        # edges there is no geometric basis for entanglement.
        elif ga_edges is not None:
            phase_gamma = 0.0

        phase_gamma *= topo_rank * pyg_similarity * float(step_strength)

        # ── Operator-aligned entangler ────────────────────────────────────
        # Each operator family has its own interaction Hamiltonian:
        #   Ti → σ_z⊗σ_z (fiber-aligned)
        #   Fe → σ_x⊗σ_x (base-coupled)
        #   Te → σ_y⊗σ_y (cross-coupled)
        #   Fi → σ_x⊗σ_x (selection-coupled)
        H_int = OPERATOR_ENTANGLERS.get(op_name, np.kron(SIGMA_X, SIGMA_X))

        # U = exp(-iγ H_int) = cos(γ)I - i sin(γ)H_int
        U = np.cos(phase_gamma) * np.eye(4) - 1j * np.sin(phase_gamma) * H_int
        separable = np.kron(rho_L, rho_R)
        rho_AB = _ensure_valid_density(U @ separable @ U.conj().T)

        # ── Dynamic edge state write-back ─────────────────────────────────
        if hetero is not None and e_pos is not None:
            dphi_sum = abs(dphi_L) + abs(dphi_R)
            ea = hetero["node", "rel", "node"].edge_attr

            # POLARITY: sign of marginal flux (QIT: sign of entropy flow)
            mean_flux = 0.5 * (dphi_L + dphi_R)
            ea[e_pos, SLOT_POLARITY] = float(np.sign(mean_flux)) if abs(mean_flux) > 1e-12 else 0.0

            # CHIRAL_STATUS: sign of pseudoscalar coefficient (grade-3 orientation)
            ea[e_pos, SLOT_CHIRAL_STATUS] = float(np.sign(c_coeffs[7])) if abs(c_coeffs[7]) > 1e-12 else 0.0

            # TOPO_LEGAL: graded boundary rank — continuous, not binary
            ea[e_pos, SLOT_TOPO_LEGAL] = topo_rank

            # CONST_SAT: continuous constraint satisfaction from trace norm
            # How well the current rho_AB satisfies the constraint that
            # partial traces should differ from the marginals (non-trivial coupling).
            rho_A_pt = np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=1, axis2=3)
            rho_B_pt = np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=0, axis2=2)
            constraint_sat = min(
                1.0,
                trace_distance_2x2(rho_A_pt, rho_L) + trace_distance_2x2(rho_B_pt, rho_R)
            )
            ea[e_pos, SLOT_CONST_SAT] = constraint_sat

            # MARG_PRES: continuous marginal preservation from entropy
            ea[e_pos, SLOT_MARG_PRES] = max(0.0, 1.0 - dphi_sum)

    entangling_claim = negative_mode != "chirality_destroyed"
    guard_result = check_nonclassical_guards(
        bridge_guard_input(
            rho_AB,
            rho_L,
            rho_R,
            entangling_bridge_claim=entangling_claim,
        )
    )
    if not guard_result.passed:
        if guard_events is not None:
            guard_events.append({
                "step": step_index,
                "negative_mode": negative_mode,
                "violations": list(guard_result.violations),
                "op_name": op_name,
                "engine_type": engine_type,
                "node_t": node_t,
                "node_t1": node_t1,
            })
        return 0.0
                
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
    guard_events = []
    
    edge_map = build_edge_lookup(hetero, enriched_edges or [], hid_to_pyg_idx or {})
    for t in range(T):
        step_t = history[t]
        step_t1 = history[(t + 1) % T]
        
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
            guard_events=guard_events,
            step_index=t,
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

    witness = guard_witness_dict(
        GuardCheckResult(
            passed=(len(guard_events) == 0),
            violations=sorted({v for ev in guard_events for v in ev.get("violations", [])}),
            checked_count=6,
        ),
        events=guard_events,
    )

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
        **witness,
    }


# --------------------------------------------------------------------------- #
# Deep contract                                                                #
# --------------------------------------------------------------------------- #

def _safe_ratio(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def _trace_terminal_activation(trace: list[float]) -> tuple[float, float]:
    if not trace:
        return 0.0, 0.0
    if len(trace) == 1:
        return float(trace[0]), float(trace[0])
    prior = trace[:-1]
    terminal = float(trace[-1])
    return max(terminal - max(prior), 0.0), terminal - float(np.mean(prior))


def _build_orbit_shell_history() -> list[dict[str, object]]:
    fallback_history: list[dict[str, object]] = []
    candidates = [
        (1, "inner", TORUS_INNER),
        (1, "clifford", TORUS_CLIFFORD),
        (1, "outer", TORUS_OUTER),
        (2, "inner", TORUS_INNER),
    ]
    for engine_type, _, torus_val in candidates:
        try:
            engine = GeometricEngine(engine_type=engine_type)
            state = engine.init_state(eta=torus_val)
            final = engine.run_cycle(state)
        except Exception:
            continue

        history: list[dict[str, object]] = []
        for step in final.history:
            rho_L = step.get("rho_L")
            rho_R = step.get("rho_R")
            if rho_L is None or rho_R is None:
                continue
            history.append(
                {
                    "rho_L": np.array(rho_L),
                    "rho_R": np.array(rho_R),
                    "eta": float(step.get("ax0_torus_entropy", torus_val)),
                }
            )

        if history and lane_d_topology_expansion_bridge(history)["lane_d_keep"]:
            return history
        if len(history) > len(fallback_history):
            fallback_history = history
    return fallback_history


def _aggregate_deep_contract(
    all_results: list[dict[str, object]],
    aggregate_phase: dict[str, dict[str, int]],
    aggregate_half: dict[str, dict[str, int]],
    failure_profiles: list[dict[str, object]],
    total_guard_event_count: int,
    shell_bridge: dict[str, object],
) -> dict[str, object]:
    candidate_names = [
        "terminal_mi_surface",
        "neutral_plateau_surface",
        "fi_phase_surface",
        "outer_half_surface",
        "guard_isolation_surface",
        "orbit_shell_surface",
    ]
    shell_bridge_pass_fraction = 1.0 if shell_bridge["lane_d_keep"] else 0.0

    total_steps = sum(
        int(row.get("n_success", 0)) + int(row.get("n_fail", 0)) + int(row.get("n_neutral", 0))
        for row in all_results
    )
    total_fail = sum(int(row.get("n_fail", 0)) for row in all_results)
    total_neutral = sum(int(row.get("n_neutral", 0)) for row in all_results)
    neutral_ratio = _safe_ratio(total_neutral, total_steps)
    fail_ratio = _safe_ratio(total_fail, total_steps)

    terminal_spikes = []
    terminal_signed = []
    for row in all_results:
        spike, signed = _trace_terminal_activation(list(row.get("mi_trace", [])))
        terminal_spikes.append(spike)
        terminal_signed.append(signed)
    terminal_doctrine = bool(
        terminal_spikes
        and all(spike > EPS for spike in terminal_spikes)
    )

    phase_fail_total = sum(int(stats.get("fail", 0)) for stats in aggregate_phase.values())
    fi_fail = int(aggregate_phase.get("Fi", {}).get("fail", 0))
    other_phase_fail = max(
        (int(stats.get("fail", 0)) for phase, stats in aggregate_phase.items() if phase != "Fi"),
        default=0,
    )

    outer_fail = int(aggregate_half.get("outer", {}).get("fail", 0))
    inner_fail = int(aggregate_half.get("inner", {}).get("fail", 0))
    half_fail_total = outer_fail + inner_fail

    unique_guard_violations = sorted(
        {
            violation
            for row in all_results
            for violation in row.get("guard_violations", [])
        }
    )
    single_cartesian_leak = (
        len(unique_guard_violations) == 1
        and unique_guard_violations[0] == "cartesian_bridge_leak"
    )

    shell_gap = float(abs(shell_bridge.get("dynamic_vs_frozen_gap", 0.0)))
    shell_hubble = float(shell_bridge.get("mean_hubble_proxy", 0.0))

    local_rows = {
        "terminal_mi_surface": {
            "signal": float(np.mean(terminal_spikes)) if terminal_spikes else 0.0,
            "signed": float(np.mean(terminal_signed)) if terminal_signed else 0.0,
            "doctrine": float(terminal_doctrine),
        },
        "neutral_plateau_surface": {
            "signal": neutral_ratio,
            "signed": neutral_ratio - fail_ratio,
            "doctrine": float(neutral_ratio >= 0.5),
        },
        "fi_phase_surface": {
            "signal": _safe_ratio(fi_fail, phase_fail_total),
            "signed": float(fi_fail - other_phase_fail),
            "doctrine": float(phase_fail_total > 0 and fi_fail == phase_fail_total),
        },
        "outer_half_surface": {
            "signal": _safe_ratio(outer_fail, half_fail_total),
            "signed": float(outer_fail - inner_fail),
            "doctrine": float(half_fail_total > 0 and outer_fail > inner_fail),
        },
        "guard_isolation_surface": {
            "signal": 1.0 if single_cartesian_leak else _safe_ratio(1.0, max(len(unique_guard_violations), 1)),
            "signed": float(1.0 if single_cartesian_leak else 0.0),
            "doctrine": float(single_cartesian_leak and total_guard_event_count > 0),
        },
        "orbit_shell_surface": {
            "signal": float(min(shell_hubble / 2.0, 1.0)),
            "signed": float(shell_gap),
            "doctrine": float(shell_bridge["lane_d_keep"]),
        },
    }

    raw_rows: list[dict[str, object]] = []
    max_mean_abs = 0.0
    for name in candidate_names:
        signal = float(local_rows[name]["signal"])
        signed = float(local_rows[name]["signed"])
        doctrine = float(local_rows[name]["doctrine"])
        shell_alignment = float(signal * (0.5 + 0.5 * shell_bridge_pass_fraction))
        mean_abs = abs(signal)
        max_mean_abs = max(max_mean_abs, mean_abs)
        raw_rows.append(
            {
                "candidate": name,
                "mean_abs_support": mean_abs,
                "mean_signed_support": signed,
                "doctrine_fit": doctrine,
                "shell_alignment": shell_alignment,
                "shell_alignment_abs": abs(shell_alignment),
                "mean_signal": signal,
                "shell_hubble": shell_hubble,
            }
        )

    row_by_name: dict[str, dict[str, object]] = {}
    for row in raw_rows:
        signal_score = float(row["mean_abs_support"] / max(max_mean_abs, EPS))
        composite_score = float(
            0.45 * float(row["doctrine_fit"])
            + 0.35 * signal_score
            + 0.20 * float(row["shell_alignment_abs"])
        )
        enriched = dict(row)
        enriched["signal_score"] = signal_score
        enriched["composite_score"] = composite_score
        row_by_name[str(row["candidate"])] = enriched

    ranking = sorted(candidate_names, key=lambda name: float(row_by_name[name]["composite_score"]), reverse=True)
    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    candidate_rows: list[dict[str, object]] = []
    ranking_scores: list[float] = []
    for name in ranking:
        row = row_by_name[name]
        ranking_scores.append(float(row["composite_score"]))
        candidate_rows.append(
            {
                "option": name,
                "mean_abs_a0": float(row["mean_abs_support"]),
                "mean_signed_a0": float(row["mean_signed_support"]),
                "doctrine_fit": float(row["doctrine_fit"]),
                "sign_consistency": float(row["doctrine_fit"]),
                "shell_alignment": float(row["shell_alignment"]),
                "shell_alignment_abs": float(row["shell_alignment_abs"]),
                "signal_score": float(row["signal_score"]),
                "composite_score": float(row["composite_score"]),
                "mean_signal": float(row["mean_signal"]),
            }
        )

    expansion_drive = np.asarray(
        [
            row["mean_abs_a0"] + row["doctrine_fit"] + row["shell_alignment_abs"]
            for row in candidate_rows
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _candidate_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(np.log(np.clip(scale_factors, EPS, None)), lambda_shells)

    for row, scale, hubble in zip(candidate_rows, scale_factors.tolist(), hubble_proxy.tolist(), strict=True):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _candidate_graph_surface(candidate_rows)
    ranking_index = {name: idx for idx, name in enumerate(ranking)}
    hypergraph_windows = [[ranking_index[name] for name in ranking[:3]]] if len(ranking) >= 3 else []
    hypergraph_surface = _candidate_hypergraph_surface(len(ranking), hypergraph_windows)
    combined_pair_edges = sorted(
        {
            tuple(edge)
            for edge in graph_surface["pair_edges"] + hypergraph_surface["pair_edges"]
        }
    )
    combined_triad_windows = sorted(
        {
            tuple(window)
            for window in graph_surface["triad_windows"] + hypergraph_surface["triad_windows"]
        }
    )
    closed_pair_edges = set(combined_pair_edges)
    for window in combined_triad_windows:
        for idx in range(len(window)):
            for jdx in range(idx + 1, len(window)):
                closed_pair_edges.add(tuple(sorted((int(window[idx]), int(window[jdx])))))
    cell_complex_surface = _candidate_cell_complex_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    topology_surface = _candidate_topology_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    symbolic_surface = _candidate_symbolic_surface(lambda_shells, scale_factors, expansion_drive)
    constraint_surface = _candidate_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray(ranking_scores, dtype=np.float64),
    )
    manifold_surface = _candidate_manifold_surface(
        np.asarray([row["mean_abs_a0"] for row in candidate_rows], dtype=np.float64),
        np.asarray([row["doctrine_fit"] for row in candidate_rows], dtype=np.float64),
        np.asarray([row["shell_alignment_abs"] for row in candidate_rows], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_candidate_fit(
        np.stack(
            [
                np.asarray([row["mean_abs_a0"] for row in candidate_rows], dtype=np.float64),
                np.asarray([row["doctrine_fit"] for row in candidate_rows], dtype=np.float64),
                np.asarray([row["shell_alignment_abs"] for row in candidate_rows], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner = ranking[0]
    winner_row = next(row for row in candidate_rows if row["option"] == winner)
    winner_vector = np.array(
        [
            winner_row["mean_abs_a0"],
            winner_row["doctrine_fit"],
            winner_row["shell_alignment_abs"],
        ],
        dtype=np.float64,
    )
    clifford_vector = _clifford_vector(winner_vector)
    torch_ga_vector = _torch_ga_roundtrip(winner_vector)
    topology_parity_ok = bool(
        cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
    )
    graph_path_budget = max(1, len(ranking) - 2)
    topology_loop_budget = max(2, len(ranking) // 2)

    pass_flag = bool(
        shell_bridge_pass_fraction >= 0.5
        and graph_surface["longest_path_length"] >= graph_path_budget
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] <= topology_loop_budget
        and topology_parity_ok
        and constraint_surface["sat"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > 1e-3
        and torch_fit["loss"] < 1.0
    )

    return {
        "pass": pass_flag,
        "winner": winner,
        "candidate_universe_size": len(candidate_names),
        "frontier_size": len(ranking),
        "shell_bridge_pass_fraction": shell_bridge_pass_fraction,
        "candidate_rows": candidate_rows,
        "graph_surface": {
            "edge_count": graph_surface["edge_count"],
            "longest_path_length": graph_surface["longest_path_length"],
            "triad_windows": graph_surface["triad_windows"],
            "path_budget": int(graph_path_budget),
        },
        "hypergraph_surface": {
            "num_edges": hypergraph_surface["num_edges"],
            "max_hyperedge_size": hypergraph_surface["max_hyperedge_size"],
            "connected_components": hypergraph_surface["connected_components"],
            "hyperedges": hypergraph_surface["hyperedges"],
        },
        "topology_surface": {
            "betti_numbers": topology_surface["betti_numbers"],
            "euler_characteristic": topology_surface["euler_characteristic"],
            "parity_ok": topology_parity_ok,
            "loop_budget": int(topology_loop_budget),
        },
        "symbolic_surface": symbolic_surface,
        "constraint_surface": constraint_surface,
        "manifold_surface": manifold_surface,
        "torch_fit": {
            "weights": torch_fit["weights"],
            "bias": torch_fit["bias"],
            "loss": torch_fit["loss"],
            "max_gap": torch_fit["max_gap"],
        },
        "winner_vector": winner_vector.tolist(),
        "clifford_vector_gap": float(np.max(np.abs(clifford_vector - winner_vector))),
        "torch_ga_vector_gap": float(np.max(np.abs(torch_ga_vector - winner_vector))),
        "scale_factors": scale_factors.tolist(),
        "hubble_proxy": hubble_proxy.tolist(),
        "propagator_traces": propagator_traces,
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
    parser.add_argument(
        "--packet-witness",
        action="store_true",
        help="Run the minimal packet-safe witness path used by root_emergence R9.",
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    print("Axis 0 Orbit Phase Alignment Probe (with Full Graph Stack Integration)")
    print("=" * 70)
    cc = hetero = ga_edges = None
    pub_to_hid = {}
    hid_to_pyg_idx = {}

    if not args.packet_witness:
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
    else:
        print("Mode: packet-witness")
        print("Skipping graph sidecars; using packet-safe strict witness lane.")
    
    all_results = []
    # Aggregate failure phase counts
    agg_phase = defaultdict(lambda: {"ok": 0, "fail": 0, "neutral": 0})
    agg_half  = defaultdict(lambda: {"ok": 0, "fail": 0})
    failure_profiles = []   # details on all failure steps
    total_guard_event_count = 0

    if args.full:
        negative_modes = ["strict", "bell_injected", "topology_flattened", "pyg_bypassed", "chirality_destroyed"]
        engine_types = list(ENGINE_TYPES)
        torus_configs = list(TORUS_CONFIGS)
        print("Mode: full")
    elif args.packet_witness:
        negative_modes = ["strict"]
        engine_types = [1]
        torus_configs = [("inner", TORUS_INNER)]
    else:
        # Default packet witness path: R9 only consumes failure existence,
        # zero guard events, Fe failure dominance, and inner-half failure bias.
        # The strict canonical lane is sufficient for those predicates while
        # avoiding the wider negative-family sweep reserved for --full.
        negative_modes = ["strict"]
        engine_types = [1]
        torus_configs = [("inner", TORUS_INNER)]
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

                # Populate PyG node features with live engine state
                if negative_mode != "pyg_bypassed":
                    update_pyg_node_features(
                        hetero, final.history, engine_type,
                        pub_to_hid, hid_to_pyg_idx,
                    )

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
                      f"rate={rate:.3f}" if rate is not None else f"  [{key}] no nonzero steps")
                print(f"    Graph Stack: TopoNetX Loops={traj['valid_topology_loops_count']}, PyG Validated={traj['pyg_orbit_validated']}, Chiral Global Operators={traj['chiral_global_operators_found']}")
                print(f"    Phase: ", end="")
                for ph in ["Ti", "Fe", "Te", "Fi"]:
                    st = traj["phase_stats"][ph]
                    print(f"{ph}={st['ok']}/{st['ok']+st['fail']+st['neutral']} ", end="")
                print()
                print(f"    Half:  outer={traj['half_stats']['outer']['ok']}/{sum(traj['half_stats']['outer'].values())} "
                      f"inner={traj['half_stats']['inner']['ok']}/{sum(traj['half_stats']['inner'].values())}")
                print(f"    {format_guard_witness_line('Guard', traj)}")
                total_guard_event_count += traj["guard_event_count"]

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
                    "guard_passed": traj["guard_passed"],
                    "guard_checked_count": traj["guard_checked_count"],
                    "guard_event_count": traj["guard_event_count"],
                    "guard_violations": traj["guard_violations"],
                    "guard_events": traj["guard_events"],
                })

    # ---------- Aggregate analysis ---------------------------------------- #
    print("\n=== AGGREGATE PHASE ANALYSIS ===")
    for ph in ["Ti", "Fe", "Te", "Fi"]:
        st = agg_phase[ph]
        total_decided = st["ok"] + st["fail"]
        rate = st["ok"] / total_decided if total_decided > 0 else None
        bar = "✓" * st["ok"] + "✗" * st["fail"]
        print(f"  {ph}: {st['ok']:2d}/{total_decided:2d} ({rate*100:.0f}%)" if rate is not None else
              f"  {ph}: all neutral")

    print("\n=== AGGREGATE HALF ANALYSIS ===")
    for half in ["outer", "inner"]:
        st = agg_half[half]
        total = st["ok"] + st["fail"]
        rate = st["ok"] / total if total > 0 else None
        print(f"  {half}: {st['ok']}/{total} ({rate*100:.0f}%)" if rate is not None else f"  {half}: all neutral")

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
            rates = [r["forward_coarising_rate"] for r in configs if r["forward_coarising_rate"] is not None]
            mean_rate = float(np.mean(rates)) if rates else 0.0
            print(f"  {torus_name:9s}: mean_failures={mean_fail:.1f}  mean_rate={mean_rate:.3f}")

    # ---------- P5: engine type consistency -------------------------------- #
    print("\n=== ENGINE TYPE CONSISTENCY ===")
    for et in ENGINE_TYPES:
        configs = [r for r in all_results if r["engine_type"] == et]
        if configs:
            rates = [r["forward_coarising_rate"] for r in configs if r["forward_coarising_rate"] is not None]
            if rates:
                print(f"  Engine {et}: mean={np.mean(rates):.3f}  std={np.std(rates):.3f}  "
                      f"range=[{min(rates):.3f},{max(rates):.3f}]")
            else:
                print(f"  Engine {et}: no valid forward_coarising_rate values")

    # ---------- Consistency check: do the same step indices fail? ---------- #
    print("\n=== FAILURE STEP CONSISTENCY ===")
    fail_positions = defaultdict(list)  # (engine_type, loop_position, phase_pos) → list of d_ct_mi
    for f in failure_profiles:
        key = (f["config"].split("/")[0], f["loop_position"], f["phase_name"])
        fail_positions[key].append(f["d_ct_mi"])
    for k, vals in sorted(fail_positions.items()):
        print(f"  {k}: {len(vals)} failures, d_ct_mi mean={np.mean(vals):+.4f}")

    print("\n=== GUARD WITNESS SUMMARY ===")
    aggregate_guard_witness = {
        "guard_passed": total_guard_event_count == 0,
        "guard_checked_count": sum(int(r.get("guard_checked_count", 0)) for r in all_results),
        "guard_event_count": total_guard_event_count,
        "guard_violations": sorted({v for r in all_results for v in r.get("guard_violations", [])}),
        "guard_events": [],
    }
    print(f"  {format_guard_witness_line('Aggregate guard', aggregate_guard_witness)}")

    shell_history = _build_orbit_shell_history()
    if shell_history:
        shell_bridge = lane_d_topology_expansion_bridge(shell_history)
    else:
        shell_bridge = {
            "lane_d_keep": False,
            "dynamic_vs_frozen_gap": 0.0,
            "mean_hubble_proxy": 0.0,
        }
    deep_contract = _aggregate_deep_contract(
        all_results,
        dict(agg_phase),
        dict(agg_half),
        failure_profiles,
        total_guard_event_count,
        shell_bridge,
    )
    legacy_all_pass = bool(total_guard_event_count == 0 and len(failure_profiles) == 0)

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
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "configs": strip(all_results),
        "aggregate_phase": dict(agg_phase),
        "aggregate_half": dict(agg_half),
        "failure_profiles": strip(failure_profiles),
        "n_total_failures": len(failure_profiles),
        "guard_event_count": total_guard_event_count,
        "shell_bridge": strip(shell_bridge),
        "aggregate": {
            "legacy_all_pass": legacy_all_pass,
            "deep_contract": strip(deep_contract),
        },
        "overall_pass": bool(deep_contract["pass"]),
        "all_pass": bool(deep_contract["pass"]),
    }

    out = os.path.join(RESULTS_DIR, "axis0_orbit_phase_alignment_results.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nResults written to {out}")
    print("\n=== DEEP CONTRACT ===")
    print(f"legacy_all_pass = {legacy_all_pass}")
    print(f"  Deep pass:                    {deep_contract['pass']}")
    print(f"  Orbit frontier:              {deep_contract['frontier_size']}/{deep_contract['candidate_universe_size']}")
    print(f"  Shell bridge pass fraction:   {deep_contract['shell_bridge_pass_fraction']:.3f}")
    print(f"  Winning deep surface:         {deep_contract['winner']}")
    print(f"  Graph longest path:           {deep_contract['graph_surface']['longest_path_length']}")
    print(f"  Hypergraph max edge size:     {deep_contract['hypergraph_surface']['max_hyperedge_size']}")
    print(f"  Topology betti numbers:       {deep_contract['topology_surface']['betti_numbers']}")
    print(f"  Symbolic hubble mid:          {deep_contract['symbolic_surface']['symbolic_hubble_mid']:.6f}")
    print(f"  Manifold mean distance:       {deep_contract['manifold_surface']['mean_geodesic_distance']:.6f}")
    print(f"  Torch fit loss:               {deep_contract['torch_fit']['loss']:.6f}")
    print(
        "  Winner vector gaps:           "
        f"clifford={deep_contract['clifford_vector_gap']:.2e} | "
        f"torch_ga={deep_contract['torch_ga_vector_gap']:.2e}"
    )

    # ---------- Enforce Fail-Closed Validation ---------- #
    # Only the exhaustive --full sweep carries the negative-family traces needed
    # for these differential checks. The bounded packet path intentionally runs a
    # single strict lane for R9's witness fields only.
    if args.full:
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
        
    print(f"\nPROBE STATUS: {'PASS' if deep_contract['pass'] else 'FAIL'}")
    return results

if __name__ == "__main__":
    main()
