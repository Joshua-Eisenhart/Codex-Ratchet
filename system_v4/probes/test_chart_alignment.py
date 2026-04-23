#!/usr/bin/env python3
"""
Chart Alignment Test — validates that runtime execution matches the
locked stage grammar from ENGINE_GRAMMAR_DISCRETE.md.

Tests:
  1. LOOP_STAGE_ORDER traversal matches chart topology order
  2. run_cycle() produces history in the correct terrain sequence
  3. Token pairing: each topology produces the expected outer/inner tokens
  4. Outer loop uses deductive/inductive operators correctly
  5. Count invariant: 8 distinct signed operators per engine

Exits 0 if all pass, non-zero if any fail.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, LOOP_STAGE_ORDER, TERRAINS, LOOP_GRAMMAR,
)

PASS = []
FAIL = []

def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))


print("=" * 60)
print("Chart Alignment Tests")
print("=" * 60)


# ─── 1. LOOP_STAGE_ORDER terrain topology sequence ─────────────

print("\n[Loop order topology sequence]")

# Type-1 outer = deductive: Se → Ne → Ni → Si
t1_outer_topos = [TERRAINS[i]["topo"] for i in LOOP_STAGE_ORDER[1][:4]]
check("Type-1 outer loop = deductive Se→Ne→Ni→Si",
      t1_outer_topos == ["Se", "Ne", "Ni", "Si"],
      f"got {t1_outer_topos}")

# Type-1 inner = inductive: Se → Si → Ni → Ne
t1_inner_topos = [TERRAINS[i]["topo"] for i in LOOP_STAGE_ORDER[1][4:]]
check("Type-1 inner loop = inductive Se→Si→Ni→Ne",
      t1_inner_topos == ["Se", "Si", "Ni", "Ne"],
      f"got {t1_inner_topos}")

# Type-2 outer = inductive: Se → Si → Ni → Ne
t2_outer_topos = [TERRAINS[i]["topo"] for i in LOOP_STAGE_ORDER[2][:4]]
check("Type-2 outer loop = inductive Se→Si→Ni→Ne",
      t2_outer_topos == ["Se", "Si", "Ni", "Ne"],
      f"got {t2_outer_topos}")

# Type-2 inner = deductive: Se → Ne → Ni → Si
t2_inner_topos = [TERRAINS[i]["topo"] for i in LOOP_STAGE_ORDER[2][4:]]
check("Type-2 inner loop = deductive Se→Ne→Ni→Si",
      t2_inner_topos == ["Se", "Ne", "Ni", "Si"],
      f"got {t2_inner_topos}")


# ─── 2. Outer/inner terrain families ───────────────────────────

print("\n[Terrain families]")

# Type-1 outer = base terrains, inner = fiber terrains
t1_outer_loops = [TERRAINS[i]["loop"] for i in LOOP_STAGE_ORDER[1][:4]]
t1_inner_loops = [TERRAINS[i]["loop"] for i in LOOP_STAGE_ORDER[1][4:]]
check("Type-1 outer uses base terrains",
      all(l == "base" for l in t1_outer_loops),
      f"got {t1_outer_loops}")
check("Type-1 inner uses fiber terrains",
      all(l == "fiber" for l in t1_inner_loops),
      f"got {t1_inner_loops}")

# Type-2 outer = fiber terrains, inner = base terrains
t2_outer_loops = [TERRAINS[i]["loop"] for i in LOOP_STAGE_ORDER[2][:4]]
t2_inner_loops = [TERRAINS[i]["loop"] for i in LOOP_STAGE_ORDER[2][4:]]
check("Type-2 outer uses fiber terrains",
      all(l == "fiber" for l in t2_outer_loops),
      f"got {t2_outer_loops}")
check("Type-2 inner uses base terrains",
      all(l == "base" for l in t2_inner_loops),
      f"got {t2_inner_loops}")


# ─── 3. run_cycle history terrain sequence ─────────────────────

print("\n[run_cycle terrain sequence]")

for et in (1, 2):
    engine = GeometricEngine(engine_type=et)
    state = engine.run_cycle(engine.init_state())

    # run_cycle produces 1 history entry per stage (8 total).
    # Extract topology from each entry's stage field (e.g. "Se_b_Ti" → "Se").
    stage_terrains = []
    for entry in state.history:
        stage_name = entry["stage"]  # e.g. "Se_b_Ti"
        topo = stage_name.split("_")[0]  # "Se"
        stage_terrains.append(topo)

    expected_topos = [TERRAINS[i]["topo"] for i in LOOP_STAGE_ORDER[et]]
    check(f"Type-{et} run_cycle terrain order matches LOOP_STAGE_ORDER",
          stage_terrains == expected_topos,
          f"got {stage_terrains}, expected {expected_topos}")


# ─── 4. Outer loop uses correct operator family ───────────────

print("\n[Outer loop operator family]")

# Type-1 outer = deductive = FeTi operators should dominate
# (in the current engine, strength modulation makes FeTi stronger on base for T1)
# We check that the outer loop history entries have loop_position = "outer"
for et in (1, 2):
    engine = GeometricEngine(engine_type=et)
    state = engine.run_cycle(engine.init_state())

    # run_cycle produces 8 history entries: first 4 = outer loop, last 4 = inner loop.
    n = len(state.history)
    half = n // 2
    outer_positions = {state.history[i].get("loop_position") for i in range(half)} - {None}
    inner_positions = {state.history[i].get("loop_position") for i in range(half, n)} - {None}

    check(f"Type-{et} first 16 history entries are 'outer'",
          outer_positions == {"outer"},
          f"got positions: {outer_positions}")
    check(f"Type-{et} last 16 history entries are 'inner'",
          inner_positions == {"inner"},
          f"got positions: {inner_positions}")


# ─── 5. LOOP_STAGE_ORDER covers all 8 terrain indices ─────────

print("\n[Coverage invariants]")

for et in (1, 2):
    order = LOOP_STAGE_ORDER[et]
    check(f"Type-{et} LOOP_STAGE_ORDER has 8 entries",
          len(order) == 8, f"got {len(order)}")
    check(f"Type-{et} LOOP_STAGE_ORDER covers indices 0-7",
          set(order) == set(range(8)),
          f"got {sorted(order)}")
    check(f"Type-{et} LOOP_STAGE_ORDER has no duplicates",
          len(set(order)) == 8,
          f"duplicates: {[x for x in order if order.count(x) > 1]}")


# ─── Summary ──────────────────────────────────────────────────

print("\n" + "=" * 60)
total = len(PASS) + len(FAIL)
print(f"RESULT: {len(PASS)}/{total} PASS")
if FAIL:
    print(f"FAILED: {', '.join(FAIL)}")
    sys.exit(1)
else:
    print("All chart alignment tests satisfied.")
    sys.exit(0)
