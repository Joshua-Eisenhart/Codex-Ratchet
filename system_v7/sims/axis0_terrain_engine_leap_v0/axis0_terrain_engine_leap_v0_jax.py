"""axis0_terrain_engine_leap_v0 — JAX leg.

BAD TWIN FIXTURE. This file is deliberately broken to exercise gate detection.
Do NOT use as a template.

Intentional defects in this file:
  (1) Top-floor jargon name (axis0/terrain/engine) with no F01/N01 ancestry.
  (2) build_packet() is called here AND in the pytorch leg — both legs share
      the same data source, making engine_consensus.independent=true
      by-construction (not earned by independent recompute).
  (3) The z3 SMT proof is a pure count tautology: we assert that a count we
      just computed equals the expected count we pinned it to. No structural
      predicate, no sign relation, no erased flip with a math reason.
  (4) axis0_earned=True is written into the result with no audit_verdict
      backing and no local control evidence.

classification: scratch_diagnostic
promotion_allowed: false
"""

from __future__ import annotations

# --- deliberately shared build_packet (defect 2) ----------------------------

def build_packet():
    """Shared data source used by BOTH the JAX and PyTorch legs.

    Because both legs call this function and compute over its output,
    any agreement between them is BY CONSTRUCTION, not independent.
    engine_consensus.independent=true would be false.
    """
    # Fake terrain grid — 16 "survivors" from a fixed set of 64 candidates.
    candidates = list(range(64))
    survivors = [c for c in candidates if c % 4 == 0]  # deterministic, not probe-relative
    return {"candidates": candidates, "survivors": survivors}


def run_jax_leg():
    import json

    # Step 1: shared data (defect 2 — same as pytorch leg)
    packet = build_packet()
    survivors = packet["survivors"]
    terrain_engine_survivor_count = len(survivors)   # == 16

    # Step 2: count tautology SMT (defect 3)
    # We assert the count we computed equals the count we expected.
    # Both values are integers we control. This is SAT by construction.
    EXPECTED_TERRAIN_ENGINE_SURVIVOR_COUNT = 16  # pinned expected count

    try:
        import z3
        solver = z3.Solver()
        n = z3.Int("n")
        solver.add(n == terrain_engine_survivor_count)         # bind computed value
        solver.add(n == EXPECTED_TERRAIN_ENGINE_SURVIVOR_COUNT) # assert against pinned expected
        verdict = "sat" if solver.check() == z3.sat else "unsat"
    except ImportError:
        verdict = "sat"  # assume SAT for fixture purposes

    # Step 3: write result (defect 4 — axis0_earned with no audit backing)
    result = {
        "_BAD_TWIN_FIXTURE": "NEGATIVE FIXTURE — this sim is designed to fail gates.",
        "_intended_failures": [
            "GATE-2: z3 SMT is a pure count tautology tagged load_bearing",
            "GATE-FIREWALL: axis0_earned=true with no audit_verdict or control evidence",
            "GATE-ENGINE: reads_peer_result=true (shares build_packet with pytorch leg)"
        ],
        "TOOL_INTEGRATION_DEPTH": {
            "z3": "load_bearing",
            "jax": "supportive",
            "networkx": "supportive"
        },
        "TOOL_MANIFEST": {
            "z3": {"tried": True, "used": True, "reason": "z3 Solver binds terrain_engine_survivor_count == expected_count; tagged load_bearing"},
            "jax": {"tried": True, "used": True, "reason": "supportive vectorized probe checks over fake terrain grid"},
            "networkx": {"tried": True, "used": True, "reason": "supportive graph construction over fake terrain topology"}
        },
        "sim_id": "axis0_terrain_engine_leap_v0",
        "engine": "jax",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "scratch_diagnostic",
        "reads_peer_result": True,          # DEFECT 2: reads shared build_packet
        "source_path": "system_v7/sims/axis0_terrain_engine_leap_v0/axis0_terrain_engine_leap_v0_jax.py",
        "packages_used": ["jax", "z3", "networkx"],
        "aligned_packages_load_bearing": ["z3"],
        "all_pass": True,
        "axis0_earned": True,               # DEFECT 4: unfenced verdict-bearing token
        "terrain_engine_activated": True,
        "terrain_engine_survivor_count": terrain_engine_survivor_count,
        "expected_terrain_engine_survivor_count": EXPECTED_TERRAIN_ENGINE_SURVIVOR_COUNT,
        "crossover_proofs": {
            "z3": {                         # DEFECT 3: count tautology tagged load_bearing
                "load_bearing": True,
                "ran": True,
                "verdict": verdict,
                "claim": "computed terrain_engine_survivor_count and expected_terrain_engine_survivor_count equal the pinned expected counts and are nonempty",
                "input_object": {
                    "terrain_engine_survivor_count": terrain_engine_survivor_count,
                    "expected_terrain_engine_survivor_count": EXPECTED_TERRAIN_ENGINE_SURVIVOR_COUNT
                }
            },
            "cvc5": {
                "load_bearing": False,
                "supportive": True,
                "ran": False,
                "verdict": "sat",
                "claim": "supportive: cvc5 not run in jax leg"
            }
        },
        "f01_ancestry": None,               # DEFECT 1: no F01/N01 grounding
        "n01_ancestry": None,
        "_ancestry_note": "axis0/terrain/engine names chosen; no F01/N01 grounding established",
        "schema": "codex_ratchet.engine_leg_result.v1",
        "generated_at": "2026-06-13T00:00:00Z"
    }

    with open("system_v7/sims/axis0_terrain_engine_leap_v0/results/axis0_terrain_engine_leap_v0_jax_results.json", "w") as f:
        json.dump(result, f, indent=2)

    print("[BAD TWIN] JAX leg written — expected to fail GATE-2, GATE-FIREWALL, GATE-ENGINE")


if __name__ == "__main__":
    run_jax_leg()
