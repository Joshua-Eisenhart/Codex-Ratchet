#!/usr/bin/env python3
"""
Grammar Invariant Test for engine_core.py dual-loop rebuild.

Tests the 8 invariants from ENGINE_GRAMMAR_DISCRETE.md against the live engine.
Exits 0 if all pass, non-zero if any fail.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, LOOP_GRAMMAR, EngineOwnership,
    _TERRAIN_TO_LOOP, TERRAINS,
)
import numpy as np

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
print("Engine Grammar Invariant Tests")
print("=" * 60)

# --- Loop role tests ---
print("\n[Loop roles]")
t1 = LOOP_GRAMMAR[1]
t2 = LOOP_GRAMMAR[2]

check("Type-1 outer role == cooling",
      t1["outer"].role == "cooling",
      f"got {t1['outer'].role}")
check("Type-1 inner role == heating",
      t1["inner"].role == "heating",
      f"got {t1['inner'].role}")
check("Type-2 outer role == heating  [inverted]",
      t2["outer"].role == "heating",
      f"got {t2['outer'].role}")
check("Type-2 inner role == cooling  [inverted]",
      t2["inner"].role == "cooling",
      f"got {t2['inner'].role}")

# --- Terrain index non-overlap ---
print("\n[Terrain ownership]")
t1_outer_i = set(t1["outer"].terrain_indices)
t1_inner_i = set(t1["inner"].terrain_indices)
check("Type-1 outer/inner terrain indices non-overlapping",
      len(t1_outer_i & t1_inner_i) == 0,
      f"overlap: {t1_outer_i & t1_inner_i}")
check("Type-1 loops cover all 8 terrains",
      t1_outer_i | t1_inner_i == set(range(8)))

# --- Ownership counts ---
print("\n[Ownership 32/32/64]")
own1 = EngineOwnership(engine_type=1)
own2 = EngineOwnership(engine_type=2)
check("Type-1 owned_microstates == 32", own1.owned_microstates == 32,
      f"got {own1.owned_microstates}")
check("Type-2 owned_microstates == 32", own2.owned_microstates == 32,
      f"got {own2.owned_microstates}")
try:
    own1.assert_non_overlapping(own2)
    check("assert_non_overlapping passes", True)
except AssertionError as e:
    check("assert_non_overlapping passes", False, str(e))

# --- EngineState has psi_L, psi_R ---
print("\n[EngineState spinor fields]")
engine1 = GeometricEngine(engine_type=1)
engine2 = GeometricEngine(engine_type=2)
state1 = engine1.init_state()
state2 = engine2.init_state()

check("state.psi_L exists and is ndarray",
      isinstance(state1.psi_L, np.ndarray),
      f"type: {type(state1.psi_L)}")
check("state.psi_R exists and is ndarray",
      isinstance(state1.psi_R, np.ndarray),
      f"type: {type(state1.psi_R)}")
check("psi_L shape == (2,) complex",
      state1.psi_L.shape == (2,) and np.iscomplexobj(state1.psi_L),
      f"shape={state1.psi_L.shape} dtype={state1.psi_L.dtype}")
check("psi_R shape == (2,) complex",
      state1.psi_R.shape == (2,) and np.iscomplexobj(state1.psi_R),
      f"shape={state1.psi_R.shape} dtype={state1.psi_R.dtype}")

# --- Loop context annotation ---
print("\n[Loop context in state and history]")
check("state.loop_position is set after init",
      state1.loop_position in ("outer", "inner"),
      f"got {state1.loop_position!r}")
check("state.loop_role is set after init",
      state1.loop_role in ("heating", "cooling"),
      f"got {state1.loop_role!r}")

state1_stepped = engine1.step(state1, stage_idx=0)
check("history entries have loop_position",
      "loop_position" in state1_stepped.history[0],
      f"keys: {list(state1_stepped.history[0].keys())}")
check("history entries have loop_role",
      "loop_role" in state1_stepped.history[0],
      f"keys: {list(state1_stepped.history[0].keys())}")

# --- Role inversion check in history ---
print("\n[Role inversion across engine types]")
# Stage 4 = terrain index 4 = first base terrain
# Type-1 maps terrain 4 -> outer (cooling); Type-2 maps terrain 4 -> inner (cooling)
# Stage 0 = terrain index 0 = first fiber terrain
# Type-1 maps terrain 0 -> inner (heating); Type-2 maps terrain 0 -> outer (heating)
# So to see a difference: compare Type-1 stage-4 role (cooling) vs Type-2 stage-0 role (heating)
state1_s4 = engine1.step(engine1.init_state(), stage_idx=4)
state2_s0 = engine2.step(engine2.init_state(), stage_idx=0)
role_t1_stage4 = state1_s4.history[0]["loop_role"]
role_t2_stage0 = state2_s0.history[0]["loop_role"]
check("Type-1 stage-4 role (cooling) != Type-2 stage-0 role (heating)",
      role_t1_stage4 != role_t2_stage0,
      f"Type-1/stage4: {role_t1_stage4}, Type-2/stage0: {role_t2_stage0}")
# Also directly verify the terrain-to-loop map inverts between types
check("Terrain 0 is inner for T1 (heating) but outer for T2 (heating) — same role here",
      _TERRAIN_TO_LOOP[1][0][0] == "inner" and _TERRAIN_TO_LOOP[2][0][0] == "outer")
check("Terrain 4 is outer for T1 (cooling) and inner for T2 (cooling) — same role, different loop name",
      _TERRAIN_TO_LOOP[1][4][0] == "outer" and _TERRAIN_TO_LOOP[2][4][0] == "inner")

# --- read_axes backward compat ---
print("\n[read_axes backward compatibility]")
axes = engine1.read_axes(state1)
expected_keys = {"GA0_entropy", "GA1_boundary", "GA2_scale",
                 "GA3_chirality", "GA4_variance", "GA5_coupling"}
check("read_axes returns all 6 axis keys",
      set(axes.keys()) == expected_keys,
      f"got: {set(axes.keys())}")

# --- run_cycle still produces 32 history entries ---
print("\n[run_cycle output]")
full_state = engine1.run_cycle(engine1.init_state())
check("run_cycle produces 32 history entries (4 ops × 8 stages)",
      len(full_state.history) == 32,
      f"got {len(full_state.history)}")

# --- Summary ---
print("\n" + "=" * 60)
total = len(PASS) + len(FAIL)
print(f"RESULT: {len(PASS)}/{total} PASS")
if FAIL:
    print(f"FAILED: {', '.join(FAIL)}")
    sys.exit(1)
else:
    print("All grammar invariants satisfied.")
    sys.exit(0)
