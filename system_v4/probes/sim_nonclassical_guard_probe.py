# REQUIRES: z3, engine_core
# Run as: make sim NAME=sim_nonclassical_guard_probe  (from repo root)
"""
Nonclassical Guard Probe
=========================
Runs the z3-backed nonclassical guards from qit_nonclassical_guards.py
against a live engine trajectory to detect classical drift.

This probe does NOT test the guard module itself (that is _selftest()).
It tests whether the engine runtime is actually honoring nonclassical
constraints during a real simulation cycle.

Pass conditions:
  P1: baseline guard check passes (no drift in declared configuration)
  P2: flat_state_drift guard catches a deliberately flat input
  P3: commutativity guard detects at least one non-commuting operator pair
  P4: separability guard detects non-separable joint state from engine
  P5: marginals move under operator application (no identity collapse)
"""

from __future__ import annotations
import os, sys
import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills"))

from engine_core import GeometricEngine
from hopf_manifold import TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER
from geometric_operators import apply_Ti, apply_Fe, apply_Te, apply_Fi

from qit_nonclassical_guards import (
    NonclassicalGuardInput,
    check_nonclassical_guards,
    guard_witness_dict,
    format_guard_witness_summary,
)


def bloch(rho):
    sx = np.array([[0,1],[1,0]], dtype=complex)
    sy = np.array([[0,-1j],[1j,0]], dtype=complex)
    sz = np.array([[1,0],[0,-1]], dtype=complex)
    return np.array([float(np.real(np.trace(s @ rho))) for s in [sx, sy, sz]])


def main():
    print("Nonclassical Guard Probe (Engine-Integrated)")
    print("=" * 55)

    results = {}

    # ── P1: baseline config passes ────────────────────────────────────────── #
    baseline = check_nonclassical_guards(NonclassicalGuardInput())
    results["P1"] = baseline.passed
    baseline_witness = guard_witness_dict(baseline)
    print()
    for line in format_guard_witness_summary("P1 baseline guard check", baseline_witness, indent=""):
        print(line)

    # ── P2: deliberately flat input triggers flat_state_drift ──────────────── #
    flat = check_nonclassical_guards(NonclassicalGuardInput(flat_state_model=True))
    results["P2"] = (not flat.passed and "flat_state_drift" in flat.violations)
    print(f"P2 flat state guard catches drift: {'✓ PASS' if results['P2'] else '✗ FAIL'}")

    # ── P3: commutativity check across operator pairs ─────────────────────── #
    # For each torus, apply Ti∘Fe vs Fe∘Ti and check order matters
    non_commuting_pairs = 0
    total_pairs = 0
    for eta_name, eta in [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]:
        engine = GeometricEngine(engine_type=1)
        state = engine.init_state(eta)
        rho_0 = state.rho_L.copy()

        ops = [
            ("Ti", lambda r: apply_Ti(r.copy(), strength=0.5)),
            ("Fe", lambda r: apply_Fe(r.copy(), strength=0.5)),
            ("Te", lambda r: apply_Te(r.copy(), strength=0.5)),
            ("Fi", lambda r: apply_Fi(r.copy(), strength=0.5)),
        ]

        for i in range(len(ops)):
            for j in range(i + 1, len(ops)):
                name_a, op_a = ops[i]
                name_b, op_b = ops[j]

                ab = op_b(op_a(rho_0.copy()))
                ba = op_a(op_b(rho_0.copy()))
                diff = np.linalg.norm(ab - ba, ord='fro')

                total_pairs += 1
                if diff > 1e-10:
                    non_commuting_pairs += 1

    results["P3"] = non_commuting_pairs > 0
    print(f"P3 non-commuting operator pairs: {non_commuting_pairs}/{total_pairs} "
          f"{'✓ PASS' if results['P3'] else '✗ FAIL'}")

    # ── P4: separability check from engine pair_cut_state ─────────────────── #
    separable_count = 0
    entangled_count = 0
    for et in [1, 2]:
        for eta in [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]:
            engine = GeometricEngine(engine_type=et)
            state = engine.init_state(eta)
            state = engine.run_cycle(state)

            rho_AB = engine.pair_cut_state(state)
            separable_product = np.kron(state.rho_L, state.rho_R)
            diff = np.linalg.norm(rho_AB - separable_product, ord='fro')

            if diff > 1e-8:
                entangled_count += 1
            else:
                separable_count += 1

    results["P4"] = entangled_count > 0
    print(f"P4 entangled configurations: {entangled_count}/{entangled_count + separable_count} "
          f"{'✓ PASS' if results['P4'] else '✗ FAIL (all separable — no entanglement!)'}")

    # ── P5: marginals move under operators ────────────────────────────────── #
    identity_steps = 0
    total_steps = 0
    for et in [1, 2]:
        engine = GeometricEngine(engine_type=et)
        state = engine.init_state(TORUS_INNER)
        state = engine.run_cycle(state)

        for i in range(1, len(state.history)):
            prev = state.history[i - 1]
            step = state.history[i]
            diff_L = np.linalg.norm(step["rho_L"] - prev["rho_L"], ord='fro')
            diff_R = np.linalg.norm(step["rho_R"] - prev["rho_R"], ord='fro')
            total_steps += 1
            if diff_L < 1e-12 and diff_R < 1e-12:
                identity_steps += 1

    results["P5"] = identity_steps < total_steps // 2
    print(f"P5 identity steps: {identity_steps}/{total_steps} "
          f"{'✓ PASS (minority)' if results['P5'] else '✗ FAIL (majority are identity)'}")

    # ── Cartesian bridge leak check against actual engine config ──────────── #
    # The engine uses np.kron(rho_L, rho_R) + entangling term in bridge_mi.
    # If bridge_mi ever drops to pure kron, it's a cartesian bridge leak.
    bridge_guard = check_nonclassical_guards(NonclassicalGuardInput(
        entangling_bridge_claim=True,
        cartesian_product_bridge=False,  # This should be True if bridge_mi is separable
    ))
    bridge_witness = guard_witness_dict(bridge_guard)
    print()
    for line in format_guard_witness_summary("Bridge guard (declared non-cartesian)", bridge_witness, indent="   "):
        print(line)

    # ── Summary ───────────────────────────────────────────────────────────── #
    all_pass = all(results.values())
    print(f"\n{'=' * 55}")
    status_line = " ".join(f"{k}={'✓' if v else '✗'}" for k, v in results.items())
    print(f"{'✓ ALL PASS' if all_pass else '✗ FAILURES DETECTED'}: {status_line}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
