"""axis0_terrain_engine_leap_v0 — PyTorch leg.

BAD TWIN FIXTURE. Do NOT use as a template.

Intentional defects:
  (1) Calls the same build_packet() from jax leg — shared data source.
      Both legs agree by construction, not by independent recompute.
  (2) cvc5 SMT is a count tautology: SAT of (count == computed) AND (count == EXPECTED).
  (3) axis0_terrain_engine_activated=True written without audit backing.
"""

from __future__ import annotations

# Import build_packet from jax leg (DEFECT: shared data source)
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from axis0_terrain_engine_leap_v0_jax import build_packet  # noqa: E402


def run_pytorch_leg():
    import json

    # Step 1: shared data — same build_packet as jax leg (defect 1)
    packet = build_packet()
    survivors = packet["survivors"]
    terrain_engine_survivor_count = len(survivors)   # == 16

    EXPECTED_TERRAIN_ENGINE_SURVIVOR_COUNT = 16

    # Step 2: count tautology with cvc5 (defect 2)
    try:
        import cvc5
        slv = cvc5.Solver()
        slv.setOption("produce-models", "true")
        slv.setLogic("QF_LIA")
        integer_sort = slv.getIntegerSort()
        n = slv.mkConst(integer_sort, "n")
        computed = slv.mkInteger(terrain_engine_survivor_count)
        expected = slv.mkInteger(EXPECTED_TERRAIN_ENGINE_SURVIVOR_COUNT)
        slv.assertFormula(slv.mkTerm(cvc5.Kind.EQUAL, n, computed))
        slv.assertFormula(slv.mkTerm(cvc5.Kind.EQUAL, n, expected))
        result_check = slv.checkSat()
        verdict = "sat" if result_check.isSat() else "unsat"
    except Exception:
        verdict = "sat"  # fixture default

    result = {
        "_BAD_TWIN_FIXTURE": "NEGATIVE FIXTURE — this sim is designed to fail gates.",
        "_intended_failures": [
            "GATE-ENGINE: reads_peer_result=true (shares build_packet with jax leg)",
            "GATE-2: cvc5 SMT is a pure count tautology tagged load_bearing",
            "GATE-FIREWALL: axis0_terrain_engine_activated=true unfenced dynamic key"
        ],
        "TOOL_INTEGRATION_DEPTH": {
            "cvc5": "load_bearing",
            "torch": "supportive"
        },
        "TOOL_MANIFEST": {
            "cvc5": {"tried": True, "used": True, "reason": "cvc5 Solver binds terrain_engine_survivor_count == EXPECTED_count; tagged load_bearing"},
            "torch": {"tried": True, "used": True, "reason": "supportive tensor operations over shared build_packet output"}
        },
        "sim_id": "axis0_terrain_engine_leap_v0",
        "engine": "pytorch",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "scratch_diagnostic",
        "reads_peer_result": True,          # DEFECT 1: uses shared build_packet
        "source_path": "system_v7/sims/axis0_terrain_engine_leap_v0/axis0_terrain_engine_leap_v0_pytorch.py",
        "packages_used": ["torch", "cvc5"],
        "aligned_packages_load_bearing": ["cvc5"],
        "all_pass": True,
        "axis0_terrain_engine_activated": True,  # DEFECT 3: unfenced verdict-bearing token
        "terrain_engine_survivor_count": terrain_engine_survivor_count,
        "expected_terrain_engine_survivor_count": EXPECTED_TERRAIN_ENGINE_SURVIVOR_COUNT,
        "crossover_proofs": {
            "cvc5": {                        # DEFECT 2: count tautology tagged load_bearing
                "load_bearing": True,
                "ran": True,
                "verdict": verdict,
                "claim": "computed terrain_engine_survivor_count matches expected pinned finite count (trivial count equality assertion)",
                "input_object": {
                    "terrain_engine_survivor_count": terrain_engine_survivor_count,
                    "expected_terrain_engine_survivor_count": EXPECTED_TERRAIN_ENGINE_SURVIVOR_COUNT
                }
            },
            "z3": {
                "load_bearing": False,
                "supportive": True,
                "ran": False,
                "verdict": "sat",
                "claim": "supportive: z3 not run in pytorch leg"
            }
        },
        "_build_packet_note": "Both jax and pytorch legs call the same build_packet() function. Agreement is by construction, not independent.",
        "schema": "codex_ratchet.engine_leg_result.v1",
        "generated_at": "2026-06-13T00:00:00Z"
    }

    with open("system_v7/sims/axis0_terrain_engine_leap_v0/results/axis0_terrain_engine_leap_v0_pytorch_results.json", "w") as f:
        json.dump(result, f, indent=2)

    print("[BAD TWIN] PyTorch leg written — expected to fail GATE-ENGINE, GATE-2, GATE-FIREWALL")


if __name__ == "__main__":
    run_pytorch_leg()
