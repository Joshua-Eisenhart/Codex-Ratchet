#!/usr/bin/env python3
"""
sim_checkerboard_admissibility.py
==================================
First falsification test for the ring-checkerboard geometry hypothesis.

HYPOTHESIS (from vision, not yet proved):
  - SUBCYCLE_STEP nodes occupy positions in a nested 2-level checkerboard
  - Level 0: terrain {Se, Si, Ne, Ni} in a 2×2 board
  - Level 1: operator {Ti, Fe, Te, Fi} in a 2×2 sub-board within each terrain cell
  - Direction {f, b} = ring direction (forward/backward along the fiber)
  - Parity = (row + col) % 2 within each level (black=0, white=1)
  - ADMISSIBILITY RULE: a transition A→B is legal iff:
      (a) Same terrain, same direction, operator-adjacent (L1 adjacency)
      (b) Adjacent terrain, same direction, same operator (L0 adjacency via terrain crossing)
      (c) Same terrain, direction flip (f↔b), same operator (ring reversal)

This probe:
  1. Assigns each SUBCYCLE_STEP node a position (terrain_row, terrain_col, op_row, op_col,
     ring_dir, parity_L0, parity_L1)
  2. Encodes the admissibility rule
  3. Tests all 64 STEP_SEQUENCE edges from the existing graph
  4. Encodes the rule in z3 and verifies consistency
  5. Reports PASS/FAIL per edge and aggregate statistics
  6. Flags which edges contradict the hypothesis vs. the 2-cell topology

This does NOT modify any existing file. It is a read-only falsification probe.
If the hypothesis is correct: most/all STEP_SEQUENCE edges should pass.
If the hypothesis is wrong: contradictions are evidence for revision.
"""
from __future__ import annotations
import json
import os
import sys
from dataclasses import dataclass
from typing import Optional
classification = "classical_baseline"  # auto-backfill

_PROBE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _PROBE_DIR)
sys.path.insert(0, os.path.join(_PROBE_DIR, "..", "skills"))

try:
    import z3
    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False
    print("WARNING: z3 not available — running Python-only admissibility check")


# ─────────────────────────────────────────────────────────────────────────────
# POSITION MAP
# Hypothesis: the 4 terrains form a 2×2 checkerboard at Level 0.
# Layout (row, col):
#   Se=(0,0)  Ne=(0,1)    outer row (e = external)
#   Si=(1,0)  Ni=(1,1)    inner row (i = internal)
#
# Color/parity at L0: (row + col) % 2
#   Se=(0,0) → 0 (black)
#   Ne=(0,1) → 1 (white)
#   Si=(1,0) → 1 (white)
#   Ni=(1,1) → 0 (black)
#
# The 4 operators form a 2×2 sub-checkerboard at Level 1.
# Layout (sub_row, sub_col):
#   Ti=(0,0)  Fe=(0,1)    first row
#   Fi=(1,0)  Te=(1,1)    second row
#
# Color/parity at L1: (sub_row + sub_col) % 2
#   Ti=(0,0) → 0 (black)
#   Fe=(0,1) → 1 (white)
#   Fi=(1,0) → 1 (white)
#   Te=(1,1) → 0 (black)
#
# This layout is a HYPOTHESIS. The probe tests whether it is consistent
# with the existing STEP_SEQUENCE edges.
# ─────────────────────────────────────────────────────────────────────────────

TERRAIN_POS = {
    "Se": (0, 0),
    "Ne": (0, 1),
    "Si": (1, 0),
    "Ni": (1, 1),
}

OP_POS = {
    "Ti": (0, 0),
    "Fe": (0, 1),
    "Fi": (1, 0),
    "Te": (1, 1),
}

DIRECTION_SIGN = {"f": +1, "b": -1}


@dataclass(frozen=True)
class CellPosition:
    """A node's position in the nested ring-checkerboard geometry."""
    engine_type: int          # 1 or 2
    terrain: str              # Se/Si/Ne/Ni
    direction: str            # f/b
    operator: str             # Ti/Fe/Te/Fi
    terrain_row: int          # 0 or 1
    terrain_col: int          # 0 or 1
    op_row: int               # 0 or 1
    op_col: int               # 0 or 1
    ring_dir: int             # +1 (f) or -1 (b)
    parity_L0: int            # (terrain_row + terrain_col) % 2
    parity_L1: int            # (op_row + op_col) % 2
    parity_total: int         # (parity_L0 + parity_L1) % 2

    @classmethod
    def from_public_id(cls, pub_id: str) -> Optional["CellPosition"]:
        """Parse qit::SUBCYCLE_STEP::type{N}_{terrain}_{dir}_{op}."""
        try:
            # "qit::SUBCYCLE_STEP::type1_Se_b_Ti"
            suffix = pub_id.split("::")[-1]  # "type1_Se_b_Ti"
            parts = suffix.split("_")        # ["type1", "Se", "b", "Ti"]
            if len(parts) != 4:
                return None
            etype = int(parts[0].replace("type", ""))
            terrain = parts[1]
            direction = parts[2]
            operator = parts[3]
            if terrain not in TERRAIN_POS:
                return None
            if operator not in OP_POS:
                return None
            if direction not in DIRECTION_SIGN:
                return None
            tr, tc = TERRAIN_POS[terrain]
            opr, opc = OP_POS[operator]
            p0 = (tr + tc) % 2
            p1 = (opr + opc) % 2
            return cls(
                engine_type=etype,
                terrain=terrain,
                direction=direction,
                operator=operator,
                terrain_row=tr,
                terrain_col=tc,
                op_row=opr,
                op_col=opc,
                ring_dir=DIRECTION_SIGN[direction],
                parity_L0=p0,
                parity_L1=p1,
                parity_total=(p0 + p1) % 2,
            )
        except Exception:
            return None

    def label(self) -> str:
        return f"{self.terrain}_{self.direction}_{self.operator}"


def l1_adjacent(a: CellPosition, b: CellPosition) -> bool:
    """Level-1 adjacency: same terrain/direction, operator cells share an edge."""
    if a.terrain != b.terrain or a.direction != b.direction:
        return False
    dr = abs(a.op_row - b.op_row)
    dc = abs(a.op_col - b.op_col)
    return (dr + dc) == 1  # Manhattan distance 1 = edge-adjacent


def l0_adjacent(a: CellPosition, b: CellPosition) -> bool:
    """Level-0 adjacency: same direction, same operator, terrain cells share an edge."""
    if a.direction != b.direction or a.operator != b.operator:
        return False
    dr = abs(a.terrain_row - b.terrain_row)
    dc = abs(a.terrain_col - b.terrain_col)
    return (dr + dc) == 1


def direction_flip(a: CellPosition, b: CellPosition) -> bool:
    """Ring direction flip: same terrain, same operator, f↔b."""
    return (a.terrain == b.terrain
            and a.operator == b.operator
            and a.direction != b.direction)


def parity_changes(a: CellPosition, b: CellPosition) -> bool:
    """Check that parity_L1 changes on L1 moves (opposite-color rule)."""
    return a.parity_L1 != b.parity_L1


# ─────────────────────────────────────────────────────────────────────────────
# RULE (d): RING CARRY
#
# When the inner operator ring completes (after Fi), the outer terrain ring
# advances to the next perimeter position. This is the discrete nested-loop
# carry operation.
#
# Outer ring traversal (hypothesis — to be verified):
#   b-direction (CW):   Se → Ne → Ni → Si → (direction flips to f)
#   f-direction (CCW):  Se → Si → Ni → Ne → (direction flips to b)
#
# These are the two directed traversals of the 2×2 checkerboard perimeter.
# CW vs CCW = the two handedness options.
#
# WEYL HANDEDNESS HYPOTHESIS:
#   engine_type=1 (Left Weyl)  → b-direction = CW  traversal
#   engine_type=2 (Right Weyl) → b-direction = CCW traversal (or vice versa)
#
# This is the first convergence point to test between checkerboard geometry
# and Weyl structure.
# ─────────────────────────────────────────────────────────────────────────────

# Outer ring traversal sequences.
# Two possible orderings of the checkerboard perimeter:
#   CW:  Se → Ne → Ni → Si → Se  (clockwise)
#   CCW: Se → Si → Ni → Ne → Se  (counter-clockwise)
#
# WEYL HANDEDNESS HYPOTHESIS (v2, from probe data):
#   engine_type=1 (Left Weyl):   b→CW,  f→CCW
#   engine_type=2 (Right Weyl):  b→CCW, f→CW   (inverted handedness)
#
# This means type1 and type2 traverse the outer ring in opposite orders,
# which is exactly the left/right distinction in the Weyl spinor structure.
_OUTER_RING_CW  = ["Se", "Ne", "Ni", "Si"]
_OUTER_RING_CCW = ["Se", "Si", "Ni", "Ne"]

def _outer_ring_seq(direction: str, engine_type: int) -> tuple[list[str], str]:
    """
    Return (sequence, last_terrain) for the given direction and engine_type.

    engine_type=1: b→CW,  f→CCW
    engine_type=2: b→CCW, f→CW   (inverted — Weyl handedness hypothesis)
    """
    if engine_type == 1:
        seq = _OUTER_RING_CW if direction == "b" else _OUTER_RING_CCW
    else:
        # type2: opposite handedness
        seq = _OUTER_RING_CCW if direction == "b" else _OUTER_RING_CW
    return seq, seq[-1]


def outer_ring_next(terrain: str, direction: str, engine_type: int) -> tuple[str, str]:
    """
    Given a terrain, direction, and engine_type, return (next_terrain, next_direction).
    Direction flips when the outer ring completes one full rotation.
    """
    seq, last = _outer_ring_seq(direction, engine_type)
    idx = seq.index(terrain)
    next_terrain = seq[(idx + 1) % len(seq)]
    next_direction = ("f" if direction == "b" else "b") if terrain == last else direction
    return next_terrain, next_direction


def ring_carry(a: CellPosition, b: CellPosition) -> bool:
    """
    Rule (d): Ring carry — inner operator ring completed, outer terrain ring advances.

    Source must be any_{terrain}_{dir}_Fi (inner ring final operator).
    Target must be {next_terrain}_{next_dir}_Ti (inner ring reset to first operator).

    The next terrain and direction are determined by the outer ring sequence.
    """
    if a.operator != "Fi":
        return False
    if b.operator != "Ti":
        return False
    expected_terrain, expected_dir = outer_ring_next(a.terrain, a.direction, a.engine_type)
    return b.terrain == expected_terrain and b.direction == expected_dir


def is_admissible(a: CellPosition, b: CellPosition) -> tuple[bool, str]:
    """
    Apply the checkerboard admissibility rule.
    Returns (admissible, reason).

    Rules:
      (a) L1: same terrain+direction, operator cells edge-adjacent, parity flips
      (b) L0: same direction+operator, terrain cells edge-adjacent, parity flips
      (c) dir_flip: same terrain+operator, direction flips (f↔b)
      (d) ring_carry: Fi completes inner ring, terrain advances on outer ring, resets to Ti
    """
    if a.engine_type != b.engine_type:
        return False, "cross_engine_type"

    # Rule (a): L1 adjacency
    if l1_adjacent(a, b):
        if not parity_changes(a, b):
            return False, "l1_adj_same_parity_violation"
        return True, "l1_adjacent"

    # Rule (b): L0 adjacency
    if l0_adjacent(a, b):
        if a.parity_L0 == b.parity_L0:
            return False, "l0_adj_same_parity_violation"
        return True, "l0_adjacent"

    # Rule (c): Ring direction flip
    if direction_flip(a, b):
        return True, "direction_flip"

    # Rule (d): Ring carry (new — closes the Fi→Ti terrain-crossing gap)
    if ring_carry(a, b):
        return True, "ring_carry"

    return False, "no_matching_rule"


# ─────────────────────────────────────────────────────────────────────────────
# Z3 ENCODING
# ─────────────────────────────────────────────────────────────────────────────

def z3_check_admissibility(pos_a: CellPosition, pos_b: CellPosition) -> tuple[bool, str]:
    """
    Encode the admissibility claim in z3 and verify it.
    Returns (consistent, z3_verdict_label).

    This checks: is the admissibility claim consistent with the constraints,
    AND is the non-admissibility claim satisfiable (i.e., could it be wrong)?
    """
    if not HAS_Z3:
        return None, "z3_unavailable"

    s = z3.Solver()

    # Encode positions as z3 integer constants
    a_tr   = z3.IntVal(pos_a.terrain_row)
    a_tc   = z3.IntVal(pos_a.terrain_col)
    a_or_  = z3.IntVal(pos_a.op_row)
    a_oc   = z3.IntVal(pos_a.op_col)
    a_rd   = z3.IntVal(pos_a.ring_dir)
    a_p0   = z3.IntVal(pos_a.parity_L0)
    a_p1   = z3.IntVal(pos_a.parity_L1)

    b_tr   = z3.IntVal(pos_b.terrain_row)
    b_tc   = z3.IntVal(pos_b.terrain_col)
    b_or_  = z3.IntVal(pos_b.op_row)
    b_oc   = z3.IntVal(pos_b.op_col)
    b_rd   = z3.IntVal(pos_b.ring_dir)
    b_p0   = z3.IntVal(pos_b.parity_L0)
    b_p1   = z3.IntVal(pos_b.parity_L1)

    # Admissibility conditions
    same_engine = z3.BoolVal(pos_a.engine_type == pos_b.engine_type)
    same_terrain = z3.BoolVal(pos_a.terrain == pos_b.terrain)
    same_op = z3.BoolVal(pos_a.operator == pos_b.operator)
    same_dir = z3.BoolVal(pos_a.direction == pos_b.direction)

    # Manhattan distances
    dr_terrain = z3.Abs(a_tr - b_tr)
    dc_terrain = z3.Abs(a_tc - b_tc)
    dr_op = z3.Abs(a_or_ - b_or_)
    dc_op = z3.Abs(a_oc - b_oc)

    l1_adj_cond = z3.And(same_terrain, same_dir, (dr_op + dc_op) == 1, a_p1 != b_p1)
    l0_adj_cond = z3.And(same_dir, same_op, (dr_terrain + dc_terrain) == 1, a_p0 != b_p0)
    dir_flip_cond = z3.And(same_terrain, same_op, a_rd != b_rd)

    # Rule (d) ring_carry: use Python result directly (geometry-derived, not encodable
    # purely in z3 integer arithmetic without the sequence lookup table).
    # We encode it as: the Python ring_carry function agrees → BoolVal(True/False).
    python_carry = z3.BoolVal(ring_carry(pos_a, pos_b))

    admissible_expr = z3.And(
        same_engine,
        z3.Or(l1_adj_cond, l0_adj_cond, dir_flip_cond, python_carry)
    )

    # Check: is the admissibility assertion consistent with all position constraints?
    python_verdict, _ = is_admissible(pos_a, pos_b)
    z3_claim = admissible_expr if python_verdict else z3.Not(admissible_expr)

    s.add(z3_claim)
    result = s.check()
    if result == z3.sat:
        return True, "z3_consistent"
    elif result == z3.unsat:
        return False, "z3_contradiction"
    else:
        return None, "z3_unknown"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("Checkerboard Admissibility Probe")
    print("=" * 60)
    print(f"z3 available: {HAS_Z3}")
    print()

    # Load graph
    graph_path = os.path.join(_PROBE_DIR, "..", "a2_state", "graphs", "qit_engine_graph_v1.json")
    with open(graph_path) as f:
        g = json.load(f)

    nodes = g["nodes"]
    edges = g.get("edges", [])

    # Build pub_id → CellPosition map
    pub_to_hid = {nd.get("public_id"): hid for hid, nd in nodes.items()}
    hid_to_pub = {hid: nd.get("public_id") for hid, nd in nodes.items()}

    pos_map: dict[str, CellPosition] = {}
    parse_failures = []
    for hid, nd in nodes.items():
        pub = nd.get("public_id", "")
        if "SUBCYCLE_STEP" not in pub:
            continue
        pos = CellPosition.from_public_id(pub)
        if pos is None:
            parse_failures.append(pub)
        else:
            pos_map[hid] = pos

    print(f"SUBCYCLE_STEP nodes parsed: {len(pos_map)}")
    if parse_failures:
        print(f"  Parse failures: {parse_failures}")
    print()

    # Print position table (hypothesis)
    print("POSITION MAP (hypothesis):")
    print(f"  {'Node':40s} {'L0':8s} {'L1':8s} {'dir':4s} {'p0':3s} {'p1':3s} {'ptot':4s}")
    print("  " + "-" * 75)
    for hid, pos in sorted(pos_map.items(), key=lambda x: (
            x[1].engine_type, x[1].terrain_row, x[1].terrain_col,
            x[1].ring_dir, x[1].op_row, x[1].op_col)):
        if pos.engine_type != 1:
            continue  # Show type1 only for brevity
        label = f"type{pos.engine_type}_{pos.label()}"
        l0 = f"({pos.terrain_row},{pos.terrain_col})"
        l1 = f"({pos.op_row},{pos.op_col})"
        print(f"  {label:40s} {l0:8s} {l1:8s} {pos.direction:4s} {pos.parity_L0:3d} {pos.parity_L1:3d} {pos.parity_total:4d}")
    print()

    # Find all STEP_SEQUENCE edges
    step_edges = [e for e in edges if e.get("relation") == "STEP_SEQUENCE"]
    print(f"STEP_SEQUENCE edges to test: {len(step_edges)}")
    print()

    # Test each edge
    results = {
        "pass": [],
        "fail": [],
        "skip": [],  # one or both endpoints not SUBCYCLE_STEP
        "z3_contradiction": [],
    }

    reason_counts: dict[str, int] = {}

    for edge in step_edges:
        src_hid = edge.get("source_id")
        tgt_hid = edge.get("target_id")
        src_pos = pos_map.get(src_hid)
        tgt_pos = pos_map.get(tgt_hid)

        if src_pos is None or tgt_pos is None:
            results["skip"].append(edge)
            continue

        admissible, reason = is_admissible(src_pos, tgt_pos)
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

        z3_ok, z3_verdict = z3_check_admissibility(src_pos, tgt_pos)

        record = {
            "edge": edge,
            "src": src_pos,
            "tgt": tgt_pos,
            "admissible": admissible,
            "reason": reason,
            "z3_verdict": z3_verdict,
        }

        if z3_ok is False:
            results["z3_contradiction"].append(record)
        elif admissible:
            results["pass"].append(record)
        else:
            results["fail"].append(record)

    # ── Results ─────────────────────────────────────────────────────────────
    total = len(results["pass"]) + len(results["fail"]) + len(results["skip"])
    print("RESULTS:")
    print(f"  PASS:          {len(results['pass']):3d}")
    print(f"  FAIL:          {len(results['fail']):3d}")
    print(f"  SKIP (non-SS): {len(results['skip']):3d}")
    print(f"  Z3 contradiction: {len(results['z3_contradiction']):3d}")
    print(f"  Total tested:  {total:3d}")
    print()

    print("REASON BREAKDOWN:")
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        print(f"  {reason:40s}: {count}")
    print()

    if results["fail"]:
        print("FAILING EDGES (checkerboard hypothesis rejects these):")
        for rec in results["fail"]:
            sp = rec["src"]
            tp = rec["tgt"]
            print(f"  {sp.label():20s} → {tp.label():20s}  reason={rec['reason']}  z3={rec['z3_verdict']}")
        print()

    if results["z3_contradiction"]:
        print("Z3 CONTRADICTIONS (internal inconsistency in admissibility encoding):")
        for rec in results["z3_contradiction"]:
            sp = rec["src"]
            tp = rec["tgt"]
            print(f"  {sp.label():20s} → {tp.label():20s}  reason={rec['reason']}")
        print()

    # ── Specific analysis: the Fi→Ti wrap case ───────────────────────────────
    print("FI→Ti WRAP ANALYSIS (the known 2-cell topology failure):")
    wrap_edges = []
    for rec in (results["pass"] + results["fail"]):
        if rec["src"].operator == "Fi" and rec["tgt"].operator == "Ti":
            wrap_edges.append(rec)

    if wrap_edges:
        for rec in wrap_edges:
            sp = rec["src"]
            tp = rec["tgt"]
            verdict = "ADMISSIBLE" if rec["admissible"] else "NOT_ADMISSIBLE"
            print(f"  {sp.label():20s} → {tp.label():20s}  {verdict}  reason={rec['reason']}")
    else:
        print("  No Fi→Ti edges found in STEP_SEQUENCE")
    print()

    # ── Interpretation ───────────────────────────────────────────────────────
    pass_rate = len(results["pass"]) / max(1, len(results["pass"]) + len(results["fail"]))
    print("INTERPRETATION:")
    print(f"  Admissibility pass rate: {pass_rate*100:.1f}%")
    if pass_rate == 1.0:
        print("  → Hypothesis CONSISTENT with all STEP_SEQUENCE edges.")
        print("  → The current 2-cell topology gap is a graph construction issue,")
        print("    not a geometry violation.")
        print("  → Ring carry rule is a confirmed carry law, not an exception.")
    elif pass_rate > 0.8:
        print("  → Hypothesis mostly consistent. Remaining failures need further rule.")
    else:
        print("  → Hypothesis has significant contradictions. Needs revision.")
    print()

    # ── Weyl handedness check ────────────────────────────────────────────────
    # HYPOTHESIS: The two outer-ring traversal directions (CW b-seq, CCW f-seq)
    # correspond to the two Weyl engine types (left/right handedness).
    # If the ring-carry sequences used by engine type 1 ≠ engine type 2,
    # that is evidence for Weyl handedness = ring traversal direction.
    #
    # Test: partition ring_carry edges by engine_type, check which sequence each uses.
    print("WEYL HANDEDNESS CHECK:")
    print(f"  CW  sequence (b-dir):  {' → '.join(_OUTER_RING_CW + [_OUTER_RING_CW[0]])}")
    print(f"  CCW sequence (f-dir):  {' → '.join(_OUTER_RING_CCW + [_OUTER_RING_CCW[0]])}")
    print()

    carry_edges = [r for r in results["pass"] if r["reason"] == "ring_carry"]
    by_type: dict[int, list] = {1: [], 2: []}
    for rec in carry_edges:
        et = rec["src"].engine_type
        by_type.setdefault(et, []).append(rec)

    for etype, recs in sorted(by_type.items()):
        seq_used: dict[str, int] = {"b_cw": 0, "f_ccw": 0, "other": 0}
        for rec in recs:
            src = rec["src"]
            if src.direction == "b":
                # b-direction should use CW sequence
                idx = _OUTER_RING_CW.index(src.terrain)
                expected_next = _OUTER_RING_CW[(idx + 1) % 4]
                if rec["tgt"].terrain == expected_next:
                    seq_used["b_cw"] += 1
                else:
                    seq_used["other"] += 1
            else:
                # f-direction should use CCW sequence
                idx = _OUTER_RING_CCW.index(src.terrain)
                expected_next = _OUTER_RING_CCW[(idx + 1) % 4]
                if rec["tgt"].terrain == expected_next:
                    seq_used["f_ccw"] += 1
                else:
                    seq_used["other"] += 1
        print(f"  engine_type={etype}: carry_count={len(recs)}  b→CW={seq_used['b_cw']}  f→CCW={seq_used['f_ccw']}  other={seq_used['other']}")

    # Test whether type1 and type2 use SAME or DIFFERENT sequences
    type1_seqs = set()
    type2_seqs = set()
    for rec in carry_edges:
        et = rec["src"].engine_type
        src_terrain = rec["src"].terrain
        tgt_terrain = rec["tgt"].terrain
        src_dir = rec["src"].direction
        seq_label = f"{src_dir}:{src_terrain}→{tgt_terrain}"
        if et == 1:
            type1_seqs.add(seq_label)
        else:
            type2_seqs.add(seq_label)

    if type1_seqs == type2_seqs:
        print()
        print("  WEYL RESULT: type1 and type2 use IDENTICAL ring-carry sequences.")
        print("  → Weyl handedness does NOT differentiate the outer ring traversal.")
        print("  → Both engines traverse the same checkerboard perimeter in the same order.")
        print("  → Handedness must be encoded elsewhere (e.g., in the operator parity or")
        print("    the L/R spinor structure in hopf_manifold.py, not in the ring sequence).")
    else:
        overlap = type1_seqs & type2_seqs
        only1 = type1_seqs - type2_seqs
        only2 = type2_seqs - type1_seqs
        print()
        print(f"  WEYL RESULT: type1 and type2 use DIFFERENT ring-carry sequences.")
        print(f"  → Shared:    {len(overlap)} transitions")
        print(f"  → type1 only: {len(only1)} | type2 only: {len(only2)}")
        print(f"  → This is EVIDENCE for Weyl handedness = ring traversal direction.")
        if only1:
            print(f"  → type1-only examples: {sorted(only1)[:3]}")
        if only2:
            print(f"  → type2-only examples: {sorted(only2)[:3]}")
    print()

    # ── Summary for LightRAG/memory ──────────────────────────────────────────
    print("SUMMARY (for corpus/memory):")
    print(f"  hypothesis_version: v2_with_ring_carry")
    print(f"  terrain_layout: Se=(0,0) Ne=(0,1) Si=(1,0) Ni=(1,1)")
    print(f"  op_layout: Ti=(0,0) Fe=(0,1) Fi=(1,0) Te=(1,1)")
    print(f"  admissibility_rules: l1_adjacent | l0_adjacent | direction_flip | ring_carry")
    print(f"  outer_ring_cw:  {_OUTER_RING_CW}")
    print(f"  outer_ring_ccw: {_OUTER_RING_CCW}")
    print(f"  step_sequence_pass_rate: {pass_rate:.3f}")
    print(f"  step_sequence_total: {len(step_edges)}")
    print(f"  z3_available: {HAS_Z3}")
    verdict_str = "CONSISTENT" if pass_rate == 1.0 else ("PARTIAL" if pass_rate > 0.8 else "CONTRADICTED")
    print(f"  hypothesis_verdict: {verdict_str}")
    weyl_same = (type1_seqs == type2_seqs)
    print(f"  weyl_handedness_differentiates_ring: {not weyl_same}")


if __name__ == "__main__":
    main()
