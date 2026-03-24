"""
Gain Calibration Fix SIM — Pro Thread 1 (v2)
============================================
Fixes the all-negative ΔΦ failure in the 64-stage engine.

Changes vs v1:
1. Fe is now ENERGY-SELECTIVE, not all-to-all symmetric damping.
   It preferentially moves population from excited levels toward the
   low-energy / high-structure basin instead of driving rho -> I/d.
2. Operators are applied SEQUENTIALLY within each microstep, dominant first,
   instead of all 4 being summed simultaneously at every stage.
3. Ti is CONTEXT-SENSITIVE:
   - Axis6 up  (+Ti / adiabatic): eigenbasis-adaptive projection
   - Axis6 down(-Ti / isothermal): computational basis dephasing
4. Fi is a spectral sharpening/flattening step:
   - sink / convergent stages sharpen the eigen-spectrum
   - source / exploratory stages flatten it slightly
5. Type-1 keeps damping dominant over coherent rotation by weakening Te
   relative to dissipative stages, consistent with γ >= 2ω.

Outputs:
- Console sweep report
- JSON results under a2_state/sim_results/gain_calibration_v2_results.json
"""

import json
import os
from datetime import datetime, UTC

import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    von_neumann_entropy,
    trace_distance,
    EvidenceToken,
)


TYPE1_STAGES = [
    (1, "Ne", "Ti", "SG", False, "A-outer"),
    (2, "Si", "Fe", "SG", True,  "A-outer"),
    (3, "Se", "Ti", "EE", True,  "A-outer"),
    (4, "Ni", "Fe", "EE", False, "A-outer"),
    (5, "Se", "Fi", "sg", False, "B-inner"),
    (6, "Si", "Te", "sg", False, "B-inner"),
    (7, "Ne", "Fi", "ee", True,  "B-inner"),
    (8, "Ni", "Te", "ee", True,  "B-inner"),
]


def negentropy(rho: np.ndarray, d: int) -> float:
    s_nat = von_neumann_entropy(rho) * np.log(2.0)
    return float(np.log(d) - s_nat)


def ensure_valid(rho: np.ndarray) -> np.ndarray:
    rho = (rho + rho.conj().T) / 2
    eigvals, eigvecs = np.linalg.eigh(rho)
    eigvals = np.maximum(np.real(eigvals), 0.0)
    if eigvals.sum() <= 0:
        d = rho.shape[0]
        return np.eye(d, dtype=complex) / d
    rho = eigvecs @ np.diag(eigvals.astype(complex)) @ eigvecs.conj().T
    rho = rho / np.trace(rho)
    return rho


def build_te_hamiltonian(d: int, seed: int = 77) -> np.ndarray:
    np.random.seed(seed)
    h = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    return (h + h.conj().T) / 2


def build_ti_ops_eigenbasis(rho: np.ndarray, d: int):
    eigvals, eigvecs = np.linalg.eigh(rho)
    return [eigvecs[:, k:k+1] @ eigvecs[:, k:k+1].conj().T for k in range(d)]


def build_ti_ops_computational(d: int):
    ops = []
    for k in range(d):
        l = np.zeros((d, d), dtype=complex)
        l[k, k] = 1.0
        ops.append(l)
    return ops


def build_fe_ops_energy_selective(d: int):
    """
    Cooling-style Fe:
    only excited -> ground transitions, instead of all d(d-1) transitions.
    This makes Fe structure-building rather than maximally mixing.
    """
    ops = []
    for k in range(1, d):
        l = np.zeros((d, d), dtype=complex)
        l[0, k] = 1.0
        ops.append(l)
    return ops


def lindblad_update(rho: np.ndarray, ops, gamma: float, dt: float, scale: float = 1.0) -> np.ndarray:
    drho = np.zeros_like(rho, dtype=complex)
    for l in ops:
        ldl = l.conj().T @ l
        drho += gamma * scale * (l @ rho @ l.conj().T - 0.5 * (ldl @ rho + rho @ ldl))
    return rho + dt * drho


def hamiltonian_update(rho: np.ndarray, h: np.ndarray, omega: float, sign: float, dt: float) -> np.ndarray:
    comm = h @ rho - rho @ h
    return rho + dt * (-1j * sign * omega * comm)


def fi_spectral_step(rho: np.ndarray, axis6_up: bool, strength: float) -> np.ndarray:
    """
    Sink / convergent mode: sharpen spectrum (more ordered)
    Source / exploratory mode: flatten spectrum slightly (more exploratory)
    """
    vals, vecs = np.linalg.eigh((rho + rho.conj().T) / 2)
    vals = np.maximum(np.real(vals), 1e-12)
    vals = vals / vals.sum()

    power = 0.85 if axis6_up else 1.25
    vals2 = vals ** power
    vals2 = vals2 / vals2.sum()

    rho2 = vecs @ np.diag(vals2.astype(complex)) @ vecs.conj().T
    return (1.0 - strength) * rho + strength * rho2


def apply_stage(
    rho: np.ndarray,
    d: int,
    dominant_op: str,
    axis6_up: bool,
    gamma_sub: float,
    gamma_dom: float,
    dt: float,
    n_steps: int,
    h: np.ndarray,
) -> np.ndarray:
    """
    Sequential dominant-first application.

    Context-sensitive Ti:
    - Axis6 up   => eigenbasis adaptive (+Ti / insulated / coherent)
    - Axis6 down => computational basis (-Ti / environment-selected pointer basis)
    """
    sign = 1.0 if axis6_up else -1.0

    for _ in range(n_steps):
        ti_ops = build_ti_ops_eigenbasis(rho, d) if axis6_up else build_ti_ops_computational(d)
        fe_ops = build_fe_ops_energy_selective(d)

        order = [dominant_op] + [op for op in ("Ti", "Fe", "Fi", "Te") if op != dominant_op]

        for op in order:
            gamma = gamma_dom if op == dominant_op else gamma_sub

            if op == "Ti":
                scale = 0.2 if axis6_up else 1.0
                rho = lindblad_update(rho, ti_ops, gamma, dt, scale=scale)

            elif op == "Fe":
                # Stronger on sink/convergent strokes, very weak on source strokes
                scale = 0.8 if not axis6_up else 0.05
                rho = lindblad_update(rho, fe_ops, gamma, dt, scale=scale)

            elif op == "Fi":
                strength = min(0.3, gamma * dt)
                rho = fi_spectral_step(rho, axis6_up=axis6_up, strength=strength)

            elif op == "Te":
                # Keep Type-1 damping dominant: Te is intentionally weakened.
                omega = min(gamma, gamma_dom / 2.0) if dominant_op == "Te" else gamma
                rho = hamiltonian_update(rho, h, omega, sign, dt)

            rho = ensure_valid(rho)

    return rho


def run_type1_cycle(
    d: int,
    n_cycles: int,
    gamma_dom: float,
    gamma_sub: float,
    dt: float = 0.01,
    n_steps: int = 5,
    seed: int = 42,
    verbose: bool = False,
):
    np.random.seed(seed)
    rho = make_random_density_matrix(d)
    h = build_te_hamiltonian(d)

    phi_start = negentropy(rho, d)
    cycle_deltas = []

    for cycle in range(n_cycles):
        phi_cycle_start = negentropy(rho, d)

        for stage_num, topo, dominant, label, axis6_up, loop in TYPE1_STAGES:
            phi_before = negentropy(rho, d)
            rho = apply_stage(
                rho=rho,
                d=d,
                dominant_op=dominant,
                axis6_up=axis6_up,
                gamma_sub=gamma_sub,
                gamma_dom=gamma_dom,
                dt=dt,
                n_steps=n_steps,
                h=h,
            )
            phi_after = negentropy(rho, d)
            dphi = phi_after - phi_before

            if verbose and cycle == 0:
                pol = "Up" if axis6_up else "Down"
                print(
                    f"  S{stage_num} {topo:2s} {loop:7s} {dominant:2s} {label:2s} {pol:4s} "
                    f"ΔΦ={dphi:+.6f}"
                )

        phi_cycle_end = negentropy(rho, d)
        cycle_deltas.append(phi_cycle_end - phi_cycle_start)

    total_dphi = negentropy(rho, d) - phi_start
    return rho, total_dphi, cycle_deltas


def sim_gain_calibration_v2(d: int = 4, n_cycles: int = 5):
    print("\n" + "=" * 72)
    print("GAIN CALIBRATION FIX — V2")
    print(f"  d={d}, cycles={n_cycles}, gamma_dom=5.0")
    print("  sequential dominant-first, energy-selective Fe, context-sensitive Ti")
    print("=" * 72)

    gamma_dom = 5.0
    gamma_values = [0.01, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.00]
    sweep_results = []

    best = None

    for gamma_sub in gamma_values:
        rho_final, total_dphi, cycle_deltas = run_type1_cycle(
            d=d,
            n_cycles=n_cycles,
            gamma_dom=gamma_dom,
            gamma_sub=gamma_sub,
            dt=0.01,
            n_steps=5,
            seed=42,
            verbose=False,
        )
        ratio = gamma_dom / gamma_sub
        mean_cycle = float(np.mean(cycle_deltas))

        record = {
            "gamma_sub": float(gamma_sub),
            "gamma_dom_over_gamma_sub": float(ratio),
            "total_dphi": float(total_dphi),
            "mean_cycle_dphi": mean_cycle,
            "cycle_deltas": [float(x) for x in cycle_deltas],
            "rho_trace": float(np.real(np.trace(rho_final))),
            "rho_entropy_bits": float(von_neumann_entropy(rho_final)),
            "note": "PASS" if total_dphi > 0 else "KILL",
        }
        sweep_results.append(record)

        if best is None or total_dphi > best["total_dphi"]:
            best = record

        marker = "PASS" if total_dphi > 0 else "KILL"
        print(
            f"  {marker:4s} gamma_sub={gamma_sub:>4.2f} "
            f"(ratio={ratio:>6.2f}:1) total ΔΦ={total_dphi:+.6f} "
            f"mean/cycle={mean_cycle:+.6f}"
        )

    positive = [r for r in sweep_results if r["total_dphi"] > 0.0]
    threshold = max(r["gamma_sub"] for r in positive) if positive else None

    print("\n" + "-" * 72)
    if threshold is not None:
        print(f"  Positive regime exists through gamma_sub <= {threshold:.2f}")
    else:
        print("  No positive regime found.")
    print(
        f"  Best setting: gamma_sub={best['gamma_sub']:.2f} "
        f"(ratio={best['gamma_dom_over_gamma_sub']:.2f}:1) "
        f"with total ΔΦ={best['total_dphi']:+.6f}"
    )
    print("-" * 72)

    evidence = []

    if positive:
        evidence.append(EvidenceToken(
            token_id="E_SIM_GAIN_PHASE_DIAGRAM_V2_OK",
            sim_spec_id="S_SIM_GAIN_CALIBRATION_V2",
            status="PASS",
            measured_value=float(best["total_dphi"]),
        ))
    else:
        evidence.append(EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_GAIN_CALIBRATION_V2",
            status="KILL",
            measured_value=float(best["total_dphi"]),
            kill_reason="NO_POSITIVE_DPHI_FOUND",
        ))

    if best["total_dphi"] > 0:
        evidence.append(EvidenceToken(
            token_id="E_SIM_CALIBRATED_RATCHET_V2_OK",
            sim_spec_id="S_SIM_TYPE1_RATCHET_V2",
            status="PASS",
            measured_value=float(best["total_dphi"]),
        ))
    else:
        evidence.append(EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_TYPE1_RATCHET_V2",
            status="KILL",
            measured_value=float(best["total_dphi"]),
            kill_reason="BEST_CONFIGURATION_STILL_NEGATIVE",
        ))

    print("\nBEST-CONFIG FIRST-CYCLE STAGE DETAIL")
    _, _, _ = run_type1_cycle(
        d=d,
        n_cycles=n_cycles,
        gamma_dom=gamma_dom,
        gamma_sub=best["gamma_sub"],
        dt=0.01,
        n_steps=5,
        seed=42,
        verbose=True,
    )

    return evidence, sweep_results, best, threshold


if __name__ == "__main__":
    evidence, sweep_results, best, threshold = sim_gain_calibration_v2(d=4, n_cycles=5)

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "gain_calibration_v2_results.json")

    with open(outpath, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "best_configuration": best,
                "positive_threshold_gamma_sub": threshold,
                "sweep_results": sweep_results,
                "evidence_ledger": [
                    {
                        "token_id": e.token_id,
                        "sim_spec_id": e.sim_spec_id,
                        "status": e.status,
                        "measured_value": e.measured_value,
                        "kill_reason": e.kill_reason,
                    }
                    for e in evidence
                ],
            },
            f,
            indent=2,
        )

    print("\n" + "=" * 72)
    print("GAIN CALIBRATION V2 RESULTS")
    print("=" * 72)
    for e in evidence:
        icon = "PASS" if e.status == "PASS" else "KILL"
        print(f"  {icon:4s} {e.sim_spec_id}: value={e.measured_value:+.6f}")
    print(f"  Results saved to: {outpath}")
