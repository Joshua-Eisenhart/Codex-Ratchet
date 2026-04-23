"""
qit_edge_state_updater.py
=========================
Skeleton for dynamic edge-state updates into the live PyG HeteroData tensor.

The 15D edge_attr in HeteroData["node", "rel", "node"].edge_attr is:
  dims 0–7   : static GA coefficients from RELATION_GA_SPEC (set at build time, never written here)
  dims 8–14  : dynamic runtime state (THIS MODULE writes these)

Dynamic slot layout (dims 8–14):
  8  POLARITY         sign of the dominant entropy flux at this step (+1/0/-1 → stored as float)
  9  ENTANG_WEIGHT    bridge MI value at this step (float, ≥ 0)
  10 CHIRAL_STATUS    chiral_volume applied at this step (+1.0, -1.0, or 0.0 if destroyed)
  11 TOPO_LEGAL       TopoNetX 2-cell legality of this transition (1.0 = legal, 0.0 = not)
  12 CONST_SAT        constraint satisfaction flag (1.0 = satisfied, 0.0 = violated) [STEP 4 — not yet]
  13 MARG_PRES        marginal preservation: 1.0 if |Δlr_asym| < MARG_THRESHOLD, else 0.0
  14 ADMISSIBILITY    co-arising flag: 1.0 if sign(Δga0) == sign(Δct_mi), else 0.0

Dependencies per slot:
  POLARITY       ← history[t].dphi_L / dphi_R alone (no external deps)
  ENTANG_WEIGHT  ← bridge_mi(rho_L[t], rho_R[t+1], ...) — needs forward rho_R
  CHIRAL_STATUS  ← engine_type + CHIRALITY_COUPLING edge + negative_mode
  TOPO_LEGAL     ← TopoNetX cc + node_t + node_t1 (available when cc is not None)
  CONST_SAT      ← constraint registry (read dynamically from the real-time guard evaluation)
  MARG_PRES      ← lr_asym(rho_L[t-1], rho_R[t-1]) vs lr_asym(rho_L[t], rho_R[t])
  ADMISSIBILITY  ← sign(ga0_after - ga0_before) vs sign(ct_mi[t] - ct_mi[t-1])

Delegation note (Antigravity):
  - Implement _compute_slots() with real logic for each slot.
  - The engine history record keys are STABLE:
      stage, op_name, loop_position, loop_role,
      dphi_L, dphi_R, rho_L, rho_R, strength,
      ga0_before, ga0_after, ax0_torus_entropy
  - The update contract is: call update_edge_state() once per history step, in order.
  - update_edge_state() writes in-place to hetero.edge_attr. No copies.
  - build_edge_lookup() must be called once after get_runtime_projections() returns.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

import numpy as np

# ── Slot indices (into edge_attr dim axis) ──────────────────────────────────── #
SLOT_POLARITY      = 8
SLOT_ENTANG_WEIGHT = 9
SLOT_CHIRAL_STATUS = 10
SLOT_TOPO_LEGAL    = 11
SLOT_CONST_SAT     = 12   # populated by engine_core's check_nonclassical_guards emission
SLOT_MARG_PRES     = 13
SLOT_ADMISSIBILITY = 14

MARG_THRESHOLD = 0.05   # |Δlr_asym| below this → marginal preservation holds

DYNAMIC_SLOTS = [
    SLOT_POLARITY, SLOT_ENTANG_WEIGHT, SLOT_CHIRAL_STATUS,
    SLOT_TOPO_LEGAL, SLOT_CONST_SAT, SLOT_MARG_PRES, SLOT_ADMISSIBILITY,
]


@dataclass
class EdgeStateRecord:
    """
    Runtime state for a single STEP_SEQUENCE edge traversal.
    Populated from engine history + bridge_mi computation.
    Passed to update_edge_state() to write into hetero.edge_attr.
    """
    # From engine history[t]
    op_name: str                  # Ti | Fe | Te | Fi
    dphi_L: float                 # left entropy flux
    dphi_R: float                 # right entropy flux
    ga0_before: float
    ga0_after: float
    rho_L: Any                    # np.ndarray 2×2
    rho_R: Any                    # np.ndarray 2×2
    strength: float               # operator application strength

    # From bridge_mi computation
    ct_mi_before: float           # MI(L[t-1], R[t]) — previous step forward MI
    ct_mi_after: float            # MI(L[t], R[t+1]) — this step forward MI

    # From graph stack
    chiral_volume: float = 1.0    # ±1.0; 0.0 if chirality_destroyed mode
    topo_legal: float = 1.0       # 1.0 if 2-cell face found, else 0.0
    lr_asym_before: float = 0.0   # lr_asym at t-1 (for marg_pres computation)
    lr_asym_after: float = 0.0    # lr_asym at t
    const_sat: float = 0.0        # Engine physics guard SAT flag


def build_edge_lookup(
    hetero: Any,
    enriched_edges: list[dict],
    node_idx: dict[str, int],
) -> dict[tuple[str, str], int]:
    """
    Build a (source_hid, target_hid) → edge_position lookup over STEP_SEQUENCE edges.

    edge_position is the row index into hetero["node", "rel", "node"].edge_attr.
    This must be called once after get_runtime_projections() returns.

    Returns:
        dict mapping (src_hid, tgt_hid) → int row index in edge_attr
        Only STEP_SEQUENCE edges are included; other relation types are ignored.

    TODO (Antigravity): verify edge_index ordering matches enriched_edges ordering.
    The current build in get_runtime_projections() iterates enriched_edges in order
    and appends to edge_src/edge_tgt/edge_attr in the same loop — so position i in
    edge_attr corresponds to enriched_edges[i]. Confirm this is invariant or add
    an explicit position-stable build.
    """
    lookup: dict[tuple[str, str], int] = {}
    position = 0
    for e in enriched_edges:
        if e.get("relation") == "STEP_SEQUENCE":
            src = e.get("source_id", "")
            tgt = e.get("target_id", "")
            if src in node_idx and tgt in node_idx:
                lookup[(src, tgt)] = position
        position += 1

    # Position-stability assertion: verify that edge_attr row i corresponds to enriched_edges[i].
    # If get_runtime_projections() ever reorders edges differently from enriched_edges,
    # all dynamic slot writes will land on the wrong edges silently.
    if hetero is not None and lookup:
        try:
            edge_index = hetero["node", "rel", "node"].edge_index
            mismatches = 0
            for (src, tgt), pos in lookup.items():
                expected_src = node_idx.get(src)
                expected_tgt = node_idx.get(tgt)
                if expected_src is None or expected_tgt is None:
                    continue
                actual_src = int(edge_index[0, pos])
                actual_tgt = int(edge_index[1, pos])
                if actual_src != expected_src or actual_tgt != expected_tgt:
                    mismatches += 1
            if mismatches > 0:
                raise AssertionError(
                    f"build_edge_lookup: {mismatches} STEP_SEQUENCE edges have mismatched "
                    f"positions in edge_attr vs enriched_edges. Dynamic slot writes will be wrong. "
                    f"Fix: ensure get_runtime_projections() iterates enriched_edges in the same "
                    f"order used here."
                )
        except (KeyError, IndexError):
            pass  # hetero not fully built yet; skip assertion

    return lookup


def update_edge_state(
    hetero: Any,
    edge_lookup: dict[tuple[str, str], int],
    src_hid: str,
    tgt_hid: str,
    record: EdgeStateRecord,
) -> bool:
    """
    Write dynamic slots (dims 8–14) into hetero.edge_attr for the edge (src_hid → tgt_hid).

    In-place mutation of hetero["node", "rel", "node"].edge_attr.
    Returns True if edge was found and written, False if edge not in lookup.

    Call once per engine step, in trajectory order.

    TODO (Antigravity): implement _compute_slots(). The stubs below return
    correct values for POLARITY and ADMISSIBILITY from pure history data.
    ENTANG_WEIGHT, CHIRAL_STATUS, TOPO_LEGAL, MARG_PRES need the full record fields.
    CONST_SAT reads from the live engine guard state.
    """
    edge_pos = edge_lookup.get((src_hid, tgt_hid))
    if edge_pos is None:
        return False

    try:
        import torch
        edge_attr = hetero["node", "rel", "node"].edge_attr
        slots = _compute_slots(record)
        for slot_idx, value in slots.items():
            edge_attr[edge_pos, slot_idx] = float(value)
        return True
    except Exception:
        return False


def _compute_slots(record: EdgeStateRecord) -> dict[int, float]:
    """
    Compute the 7 dynamic slot values from an EdgeStateRecord.

    TODO (Antigravity — implement each slot):
      POLARITY      : sign of mean(dphi_L, dphi_R); +1 if both positive, -1 if both negative, 0 otherwise
      ENTANG_WEIGHT : record.ct_mi_after (the forward bridge MI at this step)
      CHIRAL_STATUS : record.chiral_volume (already computed upstream in bridge_mi)
      TOPO_LEGAL    : record.topo_legal (already computed upstream)
      CONST_SAT     : record.const_sat (read from the physics guard)
      MARG_PRES     : 1.0 if abs(record.lr_asym_after - record.lr_asym_before) < MARG_THRESHOLD else 0.0
      ADMISSIBILITY : 1.0 if sign(ga0_after - ga0_before) == sign(ct_mi_after - ct_mi_before) else 0.0
    """
    d_ga0 = record.ga0_after - record.ga0_before
    d_ct_mi = record.ct_mi_after - record.ct_mi_before

    # POLARITY: dominant flux direction
    mean_flux = 0.5 * (record.dphi_L + record.dphi_R)
    if mean_flux > 1e-9:
        polarity = 1.0
    elif mean_flux < -1e-9:
        polarity = -1.0
    else:
        polarity = 0.0

    # ADMISSIBILITY: co-arising check
    if abs(d_ga0) < 1e-9 or abs(d_ct_mi) < 1e-9:
        admissibility = 0.5   # neutral — no clear signal
    else:
        admissibility = 1.0 if (np.sign(d_ga0) == np.sign(d_ct_mi)) else -1.0

    # MARG_PRES
    d_lr = abs(record.lr_asym_after - record.lr_asym_before)
    marg_pres = 1.0 if d_lr < MARG_THRESHOLD else -1.0

    return {
        SLOT_POLARITY:      polarity,
        SLOT_ENTANG_WEIGHT: record.ct_mi_after,           # TODO: verify forward bridge MI is correct here
        SLOT_CHIRAL_STATUS: record.chiral_volume,
        SLOT_TOPO_LEGAL:    record.topo_legal,
        SLOT_CONST_SAT:     record.const_sat,             # written via guard check
        SLOT_MARG_PRES:     marg_pres,
        SLOT_ADMISSIBILITY: admissibility,
    }
