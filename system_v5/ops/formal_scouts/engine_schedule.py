#!/usr/bin/env python3
"""
engine_schedule.py — Schedule class for composing operational QIT engines.

Composes engines across N iterations with two compose rules:
  - "outer_then_inner": apply engine 0 full cycle, then engine 1 full cycle, repeat
  - "inner_then_outer": apply engine 1 full cycle, then engine 0 full cycle, repeat

For paired-engine runs, both engines share the same 2-dim density state and the
state evolves through one engine's full cycle, then the next engine's full cycle.
This produces a composed map Φ_schedule = Φ_engine_N ∘ ... ∘ Φ_engine_1.

For independent paired runs (run_paired_engines), each engine starts from the
same initial density but evolves independently — the manifold context is shared
but state is not.

Source alignment:
  - engine_core.py (EngineCore class)
  - canonical_qit_engine_specs.py (spec accessors)
  - claude_integrated_manifold_modules/two_engine_thirty_two_stage_execution.py
    (reference for paired-engine independence semantics)
"""

from __future__ import annotations

import os
import pathlib
import sys
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import numpy as np

_ROOT = pathlib.Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from canonical_qit_engine_specs import DTYPE, I2
from engine_core import (
    EngineCore,
    N_TOTAL_SUBSTAGES_PER_ENGINE,
    _bloch_vector,
    _is_valid_density,
    _normalize_density,
    _purity,
    _von_neumann_entropy,
    generate_initial_density,
)


# ---------------------------------------------------------------------------
# Compose rules
# ---------------------------------------------------------------------------

COMPOSE_RULES = ("outer_then_inner", "inner_then_outer")


# ---------------------------------------------------------------------------
# Schedule class
# ---------------------------------------------------------------------------

class Schedule:
    """
    Compose multiple engine cycles across N iterations.

    engines: ordered list of EngineCore objects.
      For paired execution: [engine_type_one, engine_type_two].
    compose_rule:
      "outer_then_inner": engines applied in list order each iteration
      "inner_then_outer": engines applied in reverse list order each iteration
    n_iter: number of full schedule iterations.

    Each iteration applies every engine in the chosen order to the current state
    (state is passed through, not reset).
    """

    def __init__(
        self,
        engines: list[EngineCore],
        compose_rule: str = "outer_then_inner",
        n_iter: int = 1,
    ):
        if not engines:
            raise ValueError("Schedule requires at least one engine")
        if compose_rule not in COMPOSE_RULES:
            raise ValueError(f"compose_rule must be in {COMPOSE_RULES}, got {compose_rule}")
        if n_iter < 1:
            raise ValueError(f"n_iter must be >= 1, got {n_iter}")
        self.engines = engines
        self.compose_rule = compose_rule
        self.n_iter = n_iter

    def _resolve_engine_order(self) -> list[EngineCore]:
        """Return the engine order per iteration based on compose_rule."""
        if self.compose_rule == "outer_then_inner":
            return list(self.engines)
        else:
            return list(reversed(self.engines))

    def run(
        self,
        initial_state: np.ndarray,
    ) -> dict[str, Any]:
        """
        Run the schedule: apply each engine in compose order, repeat n_iter times.

        State is passed through: engine i's output is engine (i+1)'s input.

        Returns:
          dict with keys:
            final_state, full_trajectory, schedule_record
        """
        rho = _normalize_density(initial_state.copy())
        full_trajectory: list[dict[str, Any]] = []
        per_iteration_records: list[dict[str, Any]] = []
        engine_order = self._resolve_engine_order()

        for iter_idx in range(self.n_iter):
            iter_record = {"iter_idx": iter_idx, "engine_outputs": []}
            for eng in engine_order:
                cycle_result = eng.run_full_cycle(rho)
                # Update state for next engine
                rho = np.array(cycle_result["final_rho"], dtype=DTYPE)
                # Tag trajectory records with iter_idx
                for record in cycle_result["trajectory"]:
                    record["iter_idx"] = iter_idx
                    full_trajectory.append(record)
                iter_record["engine_outputs"].append({
                    "engine_type": cycle_result["engine_type"],
                    "type_label": cycle_result["type_label"],
                    "final_bloch": cycle_result["final_bloch"],
                    "final_entropy": cycle_result["final_entropy"],
                    "final_purity": cycle_result["final_purity"],
                    "final_valid_density": cycle_result["final_valid_density"],
                    "n_substages": cycle_result["n_substages"],
                })
            per_iteration_records.append(iter_record)

        schedule_record = {
            "compose_rule": self.compose_rule,
            "n_iter": self.n_iter,
            "n_engines": len(self.engines),
            "engine_types_in_order": [eng.engine_type for eng in engine_order],
            "per_iteration": per_iteration_records,
            "total_substages": len(full_trajectory),
            "expected_substages": self.n_iter * len(self.engines) * N_TOTAL_SUBSTAGES_PER_ENGINE,
        }
        return {
            "final_state": rho.tolist(),
            "final_bloch": _bloch_vector(rho).tolist(),
            "final_entropy": _von_neumann_entropy(rho),
            "final_purity": _purity(rho),
            "final_valid_density": _is_valid_density(rho),
            "trajectory": full_trajectory,
            "schedule_record": schedule_record,
        }

    def run_paired_engines(
        self,
        initial_state: np.ndarray,
        n_pairs: int = 4,
    ) -> dict[str, Any]:
        """
        Run engines as a pair: both engines start from the same initial density
        but evolve independently (no state cross-reference between engines).

        n_pairs: number of independent runs to perform (each starts from the same
                 initial_state but uses a fresh manifold context for each engine).

        Returns:
          dict with keys:
            paired_runs: list of n_pairs dicts, each containing both engines' results
            divergence_summary: per-pair Frobenius distance between engines' finals
        """
        paired_runs: list[dict[str, Any]] = []
        divergences = []
        rho_init = _normalize_density(initial_state.copy())

        for pair_idx in range(n_pairs):
            pair_record = {"pair_idx": pair_idx, "engine_results": []}
            engine_finals = []
            for eng in self.engines:
                # Fresh manifold context per pair (independence)
                eng.manifold_context = {}
                eng.global_step = 0
                cycle_result = eng.run_full_cycle(rho_init)
                pair_record["engine_results"].append(cycle_result)
                engine_finals.append(np.array(cycle_result["final_rho"], dtype=DTYPE))

            # Compute pair-wise divergence (max over all engine pairs in this pair)
            divs = []
            for i in range(len(engine_finals)):
                for j in range(i + 1, len(engine_finals)):
                    d = float(np.linalg.norm(engine_finals[i] - engine_finals[j], "fro"))
                    divs.append(d)
            pair_max_div = max(divs) if divs else 0.0
            divergences.append(pair_max_div)
            pair_record["max_pairwise_divergence"] = pair_max_div
            paired_runs.append(pair_record)

        return {
            "n_pairs": n_pairs,
            "paired_runs": paired_runs,
            "divergence_summary": {
                "per_pair_max_divergence": divergences,
                "mean": float(np.mean(divergences)) if divergences else 0.0,
                "min": float(np.min(divergences)) if divergences else 0.0,
                "max": float(np.max(divergences)) if divergences else 0.0,
            },
        }


# ---------------------------------------------------------------------------
# Composition-order utility
# ---------------------------------------------------------------------------

def order_dependence_check(
    rho_init: np.ndarray,
    engine_a: EngineCore,
    engine_b: EngineCore,
) -> dict[str, Any]:
    """
    Compare Φ_B ∘ Φ_A vs Φ_A ∘ Φ_B applied to the same initial density.
    If the composition is non-commutative, the two outputs differ.

    Returns dict with:
      ab_final, ba_final, frobenius_distance
    """
    rho_init_n = _normalize_density(rho_init.copy())

    # Reset engines to fresh state for clean comparison
    engine_a.manifold_context = {}
    engine_a.global_step = 0
    engine_b.manifold_context = {}
    engine_b.global_step = 0

    # A then B
    out_a = engine_a.run_full_cycle(rho_init_n)
    rho_after_a = np.array(out_a["final_rho"], dtype=DTYPE)
    engine_b.manifold_context = {}
    engine_b.global_step = 0
    out_ba = engine_b.run_full_cycle(rho_after_a)
    rho_ab = np.array(out_ba["final_rho"], dtype=DTYPE)

    # Reset and run B then A
    engine_a.manifold_context = {}
    engine_a.global_step = 0
    engine_b.manifold_context = {}
    engine_b.global_step = 0
    out_b = engine_b.run_full_cycle(rho_init_n)
    rho_after_b = np.array(out_b["final_rho"], dtype=DTYPE)
    engine_a.manifold_context = {}
    engine_a.global_step = 0
    out_ab = engine_a.run_full_cycle(rho_after_b)
    rho_ba = np.array(out_ab["final_rho"], dtype=DTYPE)

    # Compose order: AB = engine A first then engine B; BA = engine B first then engine A
    distance = float(np.linalg.norm(rho_ab - rho_ba, "fro"))
    return {
        "ab_final": rho_ab.tolist(),
        "ba_final": rho_ba.tolist(),
        "frobenius_distance": distance,
        "non_commutative": distance > 1e-6,
    }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("engine_schedule.py — smoke test")
    print("=" * 70)

    rho0 = generate_initial_density(11)
    eng_t1 = EngineCore(engine_type=0)
    eng_t2 = EngineCore(engine_type=1)

    # 1. Single-iteration paired schedule
    print("\n1. Single-iter outer_then_inner schedule")
    sched = Schedule(engines=[eng_t1, eng_t2], compose_rule="outer_then_inner", n_iter=1)
    out1 = sched.run(rho0)
    print(f"   total_substages: {out1['schedule_record']['total_substages']}  "
          f"(expected {out1['schedule_record']['expected_substages']})")
    print(f"   final_bloch: {[round(x, 4) for x in out1['final_bloch']]}")
    print(f"   final_valid: {out1['final_valid_density']}")
    assert out1["schedule_record"]["total_substages"] == 64, "Expected 64 substages"

    # 2. Inner-then-outer compose rule
    print("\n2. Single-iter inner_then_outer schedule")
    eng_t1.manifold_context = {}; eng_t1.global_step = 0
    eng_t2.manifold_context = {}; eng_t2.global_step = 0
    sched2 = Schedule(engines=[eng_t1, eng_t2], compose_rule="inner_then_outer", n_iter=1)
    out2 = sched2.run(rho0)
    print(f"   total_substages: {out2['schedule_record']['total_substages']}")
    print(f"   final_bloch: {[round(x, 4) for x in out2['final_bloch']]}")

    # 3. Compose orders differ
    final_otc = np.array(out1["final_state"], dtype=DTYPE)
    final_ito = np.array(out2["final_state"], dtype=DTYPE)
    diff = float(np.linalg.norm(final_otc - final_ito, "fro"))
    print(f"\n3. outer_then_inner vs inner_then_outer Frobenius distance: {diff:.6f}")
    assert diff > 1e-6, "Compose orders should produce different outputs (non-commutative)"

    # 4. Multi-iter schedule (n_pairs equivalent via .run with n_iter)
    print("\n4. Multi-iter (n_iter=4) outer_then_inner schedule")
    eng_t1.manifold_context = {}; eng_t1.global_step = 0
    eng_t2.manifold_context = {}; eng_t2.global_step = 0
    sched4 = Schedule(engines=[eng_t1, eng_t2], compose_rule="outer_then_inner", n_iter=4)
    out4 = sched4.run(rho0)
    print(f"   total_substages: {out4['schedule_record']['total_substages']}  "
          f"(expected {out4['schedule_record']['expected_substages']})")
    print(f"   final_bloch: {[round(x, 4) for x in out4['final_bloch']]}")
    assert out4["schedule_record"]["total_substages"] == 256, "Expected 256 substages (64 × 4)"

    # 5. Paired engines (independent)
    print("\n5. Paired-engine independent runs (n_pairs=4)")
    eng_t1.manifold_context = {}; eng_t1.global_step = 0
    eng_t2.manifold_context = {}; eng_t2.global_step = 0
    sched_paired = Schedule(engines=[eng_t1, eng_t2], compose_rule="outer_then_inner", n_iter=1)
    paired = sched_paired.run_paired_engines(rho0, n_pairs=4)
    print(f"   n_pairs run: {paired['n_pairs']}")
    print(f"   divergence per pair: {[round(d, 4) for d in paired['divergence_summary']['per_pair_max_divergence']]}")
    print(f"   mean divergence: {paired['divergence_summary']['mean']:.4f}")
    assert paired["divergence_summary"]["mean"] > 1e-6, "Paired engines should diverge"

    # 6. Order-dependence check
    print("\n6. Order-dependence (non-commutativity)")
    order = order_dependence_check(rho0, eng_t1, eng_t2)
    print(f"   Frobenius distance (AB vs BA): {order['frobenius_distance']:.6f}")
    print(f"   non_commutative: {order['non_commutative']}")
    assert order["non_commutative"], "Engine composition should be non-commutative"

    print("\n" + "=" * 70)
    print("engine_schedule.py SMOKE TEST PASS")
    print("=" * 70)
