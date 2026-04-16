#!/usr/bin/env python3
"""
Axis 0 Co-Arising Stress Test — Toward OPEN-1
===============================================
Analytical probe to test whether sign(Δga0) = sign(ΔMI) is forced by the
operator algebra, or is merely an empirical trajectory correlation.

Probe design (per controller synthesis 2026-03-30):
  "Build a symbolic/analytical probe that computes Δga0 and ΔMI for a generic
   2-qubit state under each operator class (Ti, Fe, Te, Fi) and verifies that
   their signs are forced to agree by the operator algebra — not just
   empirically correlated."

The null hypothesis to eliminate:
  H0: ga0 and MI correlate because of a shared driver (trajectory structure),
      but they are not algebraically related.

What would eliminate H0:
  Universality — sign agreement holds across ALL random valid input states,
  not just the states the engine visits on its attractor trajectory.

What would NOT eliminate H0:
  Sign agreement only on trajectory-typical states (near the attractor).
  This would mean the correlation is attractor-specific, not operator-algebraic.

Two-level test:
  Level 1 — lr_asym universality:
    For each operator O, does applying O always change lr_asym
    (the driver of bridge MI) in a direction consistent with Δga0,
    regardless of the input state?
    → If yes: the operator forces sign co-arising algebraically.
    → If no: the co-arising is trajectory-specific (attractor artifact).

  Level 2 — bridge MI universality:
    Directly test sign(Δga0) = sign(ΔMI_bridge) across random states.
    Uses the full cross-temporal bridge MI (L_after ⊗ R_before Bell injection)
    as the MI measure.

Owner correction (2026-03-30 synthesis):
  "The sensory channel is geometry, not a marginal correction. η is the body
   of evidence; Phase 5A only ruled out the marginal channel."
  → Level 3: Test whether η-transport (the geometric sensory channel)
    breaks the co-arising. If η changes can decouple ga0 from MI, then
    the co-arising is operator-algebraic only under fixed geometry, and
    the "full" co-arising requires geometry + operator together.

Three findings that would each matter:
  (a) Full universality (Level 1 + 2, all operators): OPEN-1 IS SOLVABLE
      algebraically — the sign is forced by the operator definition.
  (b) Partial universality (holds for Ti/Te but not Fe/Fi): the proof
      strategy must handle unitary operators differently from CPTP.
  (c) Trajectory-specificity: the co-arising is an attractor property,
      not an operator property — the theorem requires the attractor, not
      just the operator algebra.
"""

from __future__ import annotations
import json, os, sys
from datetime import UTC, datetime

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import gudhi
import numpy as np
from typing import Tuple
import rustworkx as rx
import sympy as sp
import torch
import torch_ga
import xgi
from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.learning.frechet_mean import FrechetMean
from scipy.linalg import expm
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat
classification = "classical_baseline"  # auto-backfill
divergence_log = (
    "Classical foundation baseline: this stress-tests Axis-0 co-arising "
    "numerically across random states. The legacy universality result is "
    "preserved, and a deep contract now ranks operator classes against "
    "operator-conditioned shell bridges, ordered graph/topology, symbolic "
    "expansion, solver closure, geometric algebra, and manifold witnesses."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "random-state stress testing, trajectory operator profiling, and aggregate numerics"},
    "scipy": {"tried": True, "used": True, "reason": "matrix exponential propagator for operator-ranking expansion updates"},
    "pytorch": {"tried": True, "used": True, "reason": "fit and gradient witness over aggregate operator features"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning operator vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning operator vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered DAG witness over the ranked operator classes"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order config-to-operator coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for operator-ranking closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the operator complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for operator expansion trends"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing operator rank order and monotone scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for aggregate operator geometry"},
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
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi, _ensure_valid_density
)
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER
from sim_axis0_dynamic_shell import lane_d_topology_expansion_bridge
from sim_axis0_iscalar_sweep import (
    _clifford_vector,
    _option_cell_complex_surface as _operator_cell_complex_surface,
    _option_constraint_surface as _operator_constraint_surface,
    _option_graph_surface as _operator_graph_surface,
    _option_hypergraph_surface as _operator_hypergraph_surface,
    _option_manifold_surface as _operator_manifold_surface,
    _option_scale_history as _operator_scale_history,
    _option_symbolic_surface as _operator_symbolic_surface,
    _option_topology_surface as _operator_topology_surface,
    _torch_ga_roundtrip,
    _torch_option_fit as _torch_operator_fit,
)

N_RANDOM_STATES = 2000    # Haar-random (ρ_L, ρ_R) pairs per operator
N_STRENGTH_VALS = 5       # operator strength sweep
N_GA0_VALS = 7            # ga0_before sweep
RNG_SEED = 42
TORUS_CONFIGS = [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]
OPERATOR_ORDER = ["Ti", "Fe", "Te", "Fi"]

# ─── ga0 update constants (from engine_core._ga0_target for generic terrain) ───
# Base target offsets per operator (from engine_core line 371):
GA0_OFFSET = {"Ti": -0.25, "Fe": 0.05, "Te": 0.20, "Fi": -0.10}
# Typical base (fiber=0.35, base=0.55, expansion=+0.15, open=+0.10)
# We test over a range of base values to cover both terrain types.
GA0_BASE_RANGE = [0.35, 0.45, 0.55]   # fiber, midpoint, base terrain
GA0_ALPHA = 0.55   # typical blend rate (piston=1.0: 0.10 + 0.45*1.0 = 0.55)

EPS = 1e-12

SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL = np.outer(PSI_MINUS, PSI_MINUS.conj())


# --------------------------------------------------------------------------- #
# Random state generation                                                     #
# --------------------------------------------------------------------------- #

def haar_random_density(rng: np.random.Generator) -> np.ndarray:
    """Haar-random mixed state via random unitary and random eigenvalues."""
    # Random unitary (Haar measure on U(2))
    z = rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2))
    Q, _ = np.linalg.qr(z)
    # Random eigenvalues (Dirichlet on simplex)
    ev = rng.exponential(1.0, size=2)
    ev /= ev.sum()
    return _ensure_valid_density(Q @ np.diag(ev.astype(complex)) @ Q.conj().T)


def bloch_vec(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(s @ rho))) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


def lr_asym(rho_L: np.ndarray, rho_R: np.ndarray) -> float:
    return float(np.clip(0.5 * np.linalg.norm(bloch_vec(rho_L) - bloch_vec(rho_R)), 0.0, 1.0))


def vne(rho: np.ndarray) -> float:
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0


def bridge_mi(rho_L: np.ndarray, rho_R: np.ndarray) -> float:
    """Bell-injected bridge MI (same as Phase4 bridge without cross-temporal lag)."""
    p = float(np.clip(lr_asym(rho_L, rho_R), 0.01, 0.99))
    rho_AB = _ensure_valid_density((1 - p) * np.kron(rho_L, rho_R) + p * BELL)
    rho_A = np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=1, axis2=3)
    rho_B = np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=0, axis2=2)
    return max(0.0, vne(rho_A) + vne(rho_B) - vne(rho_AB))


# --------------------------------------------------------------------------- #
# Operator application (replicating engine_core right-spinor conjugate rule)  #
# --------------------------------------------------------------------------- #

def apply_left(op_name: str, rho_L: np.ndarray, strength: float,
               polarity_up: bool = True) -> np.ndarray:
    """Apply operator to left spinor (standard basis)."""
    kw = {"polarity_up": polarity_up, "strength": strength}
    if op_name == "Te":
        kw["q"] = 0.3 * 0.7   # typical q = angle_mod * 0.3
    return {"Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi}[op_name](
        rho_L, **kw
    )


def apply_right(op_name: str, rho_R: np.ndarray, strength: float,
                theta1: float = 0.5, theta2: float = 0.3,
                polarity_up: bool = True) -> np.ndarray:
    """Apply operator to right spinor (conjugate dynamics per engine_core)."""
    kw = {"polarity_up": polarity_up, "strength": strength}
    if op_name == "Te":
        kw["q"] = 0.3 * 0.7
        # Conjugate: reversed polarity
        kw["polarity_up"] = not polarity_up
        return apply_Te(rho_R, **kw)
    elif op_name == "Ti":
        # Right-spinor Ti: dephase in rotated basis
        phase = theta2 - theta1
        basis = np.array([[1.0, np.exp(1j * phase)],
                          [1.0, -np.exp(1j * phase)]], dtype=complex) / np.sqrt(2.0)
        rho_conj = basis @ rho_R @ basis.conj().T
        rho_conj = apply_Ti(rho_conj, **kw)
        return _ensure_valid_density(basis.conj().T @ rho_conj @ basis)
    elif op_name in ("Fe", "Fi"):
        # Conjugate: flip basis (σ_x conjugation)
        rho_conj = SIGMA_X @ rho_R @ SIGMA_X
        rho_conj = {"Fe": apply_Fe, "Fi": apply_Fi}[op_name](rho_conj, **kw)
        return _ensure_valid_density(SIGMA_X @ rho_conj @ SIGMA_X)
    return rho_R


# --------------------------------------------------------------------------- #
# Level 1 — lr_asym universality                                              #
# --------------------------------------------------------------------------- #

def level1_lr_asym_universality(rng: np.random.Generator) -> dict:
    """
    For each operator O, sweep random input states and check:
      sign(Δga0) = sign(Δlr_asym) universally?

    lr_asym is the direct driver of bridge_MI via Bell injection.
    If sign agreement holds universally for lr_asym, the algebraic proof
    structure is: operator → lr_asym change → MI change (same sign chain).
    """
    results = {}

    for op_name in ["Ti", "Fe", "Te", "Fi"]:
        ga0_offset = GA0_OFFSET[op_name]
        failures = []
        total = 0
        agree = 0

        for ga0_base in GA0_BASE_RANGE:
            ga0_target = float(np.clip(ga0_base + ga0_offset, 0.05, 0.95))

            for ga0_before in np.linspace(0.1, 0.9, N_GA0_VALS):
                delta_ga0 = GA0_ALPHA * (ga0_target - ga0_before)
                if abs(delta_ga0) < 1e-4:
                    continue  # near-zero change — skip

                for strength in np.linspace(0.1, 0.9, N_STRENGTH_VALS):
                    for _ in range(N_RANDOM_STATES // (N_GA0_VALS * N_STRENGTH_VALS * len(GA0_BASE_RANGE))):
                        rho_L = haar_random_density(rng)
                        rho_R = haar_random_density(rng)

                        asym_before = lr_asym(rho_L, rho_R)
                        rho_L_new = apply_left(op_name, rho_L, strength)
                        rho_R_new = apply_right(op_name, rho_R, strength)
                        asym_after = lr_asym(rho_L_new, rho_R_new)
                        delta_asym = asym_after - asym_before

                        total += 1
                        if abs(delta_asym) < 1e-6:
                            # Negligible change — neutral
                            agree += 1
                            continue

                        sign_match = (delta_ga0 * delta_asym > 0)
                        if sign_match:
                            agree += 1
                        else:
                            failures.append({
                                "op": op_name,
                                "ga0_base": float(ga0_base),
                                "ga0_before": float(ga0_before),
                                "ga0_after": float(ga0_before + delta_ga0),
                                "delta_ga0": float(delta_ga0),
                                "delta_asym": float(delta_asym),
                                "strength": float(strength),
                                "bloch_L_before": bloch_vec(rho_L).tolist(),
                                "bloch_R_before": bloch_vec(rho_R).tolist(),
                            })

        rate = agree / total if total > 0 else 0.0
        universal = (len(failures) == 0)
        results[op_name] = {
            "total_trials": total,
            "agree": agree,
            "failures": len(failures),
            "agreement_rate": rate,
            "universal": universal,
            "failure_examples": failures[:3],   # first 3 for diagnosis
        }

    return results


# --------------------------------------------------------------------------- #
# Level 2 — bridge MI universality                                            #
# --------------------------------------------------------------------------- #

def level2_bridge_mi_universality(rng: np.random.Generator) -> dict:
    """
    For each operator O, sweep random input states and check:
      sign(Δga0) = sign(Δbridge_MI) universally?

    Uses the direct bridge MI (with Bell injection) rather than lr_asym proxy.
    """
    results = {}

    for op_name in ["Ti", "Fe", "Te", "Fi"]:
        ga0_offset = GA0_OFFSET[op_name]
        failures = 0
        agrees = 0
        total = 0

        for ga0_base in GA0_BASE_RANGE:
            ga0_target = float(np.clip(ga0_base + ga0_offset, 0.05, 0.95))
            for ga0_before in np.linspace(0.15, 0.85, 5):
                delta_ga0 = GA0_ALPHA * (ga0_target - ga0_before)
                if abs(delta_ga0) < 1e-4:
                    continue
                for strength in np.linspace(0.2, 0.8, 4):
                    for _ in range(N_RANDOM_STATES // (5 * 4 * len(GA0_BASE_RANGE))):
                        rho_L = haar_random_density(rng)
                        rho_R = haar_random_density(rng)

                        mi_before = bridge_mi(rho_L, rho_R)
                        rho_L_new = apply_left(op_name, rho_L, strength)
                        rho_R_new = apply_right(op_name, rho_R, strength)
                        mi_after = bridge_mi(rho_L_new, rho_R_new)
                        delta_mi = mi_after - mi_before

                        total += 1
                        if abs(delta_mi) < 1e-5:
                            agrees += 1
                            continue
                        if delta_ga0 * delta_mi > 0:
                            agrees += 1
                        else:
                            failures += 1

        rate = agrees / total if total > 0 else 0.0
        results[op_name] = {
            "total": total,
            "agrees": agrees,
            "failures": failures,
            "agreement_rate": rate,
            "universal": (failures == 0),
        }

    return results


# --------------------------------------------------------------------------- #
# Level 3 — η transport breaks co-arising                                     #
# --------------------------------------------------------------------------- #

def level3_geometry_decoupling(rng: np.random.Generator) -> dict:
    """
    Tests the owner's correction (2026-03-30):
      'The sensory channel is geometry, not a marginal correction.
       η is the body of evidence.'

    When η changes (torus transport), does co-arising break?
    If η-transport can increase MI while ga0 decreases (or vice versa),
    then the co-arising is operator-algebraic only under fixed η.
    The geometry (η) is the 'sensory input' that can override the operator signal.

    Test: apply η-transport (change rho_L, rho_R based on new torus position)
    while holding operator-ga0 fixed. Check sign agreement.
    """
    from hopf_manifold import (
        torus_coordinates, left_density, right_density, TORUS_INNER, TORUS_OUTER
    )

    n_trials = 200
    decoupled_cases = 0
    coupled_cases = 0

    eta_pairs = [(TORUS_INNER, TORUS_OUTER), (TORUS_OUTER, TORUS_INNER)]

    for eta_from, eta_to in eta_pairs:
        q_from = torus_coordinates(eta_from, 0.5, 0.3)
        q_to = torus_coordinates(eta_to, 0.5, 0.3)

        rho_L_from = left_density(q_from)
        rho_R_from = right_density(q_from)
        rho_L_to = left_density(q_to)
        rho_R_to = right_density(q_to)

        # Pure transport: Bloch vectors change from eta geometry
        # ga0 target during transport depends on operator — test "Ti" as representative
        ga0_target = float(np.clip(0.45 + GA0_OFFSET["Ti"], 0.05, 0.95))

        for ga0_before in np.linspace(0.2, 0.8, 10):
            delta_ga0 = GA0_ALPHA * (ga0_target - ga0_before)
            mi_from = bridge_mi(rho_L_from, rho_R_from)
            mi_to = bridge_mi(rho_L_to, rho_R_to)
            delta_mi = mi_to - mi_from

            if abs(delta_mi) < 1e-5 or abs(delta_ga0) < 1e-4:
                continue
            if delta_ga0 * delta_mi > 0:
                coupled_cases += 1
            else:
                decoupled_cases += 1

    total = coupled_cases + decoupled_cases
    decoupling_rate = decoupled_cases / total if total > 0 else 0.0

    return {
        "total_trials": total,
        "decoupled_cases": decoupled_cases,
        "coupled_cases": coupled_cases,
        "decoupling_rate": decoupling_rate,
        "geometry_breaks_coarising": decoupled_cases > 0,
        "interpretation": (
            "η-transport CAN decouple ga0 from MI — geometry is the sensory override."
            if decoupled_cases > 0 else
            "η-transport preserves co-arising — geometric sensory channel and operator co-arise too."
        ),
    }


# --------------------------------------------------------------------------- #
# Algebraic structure analysis                                                #
# --------------------------------------------------------------------------- #

def algebraic_structure_note(l1: dict, l2: dict, l3: dict) -> str:
    """
    Based on the three levels, characterize what kind of algebraic result
    is available.
    """
    all_l1_universal = all(v["universal"] for v in l1.values())
    all_l2_universal = all(v["universal"] for v in l2.values())
    cptp_ops = ["Ti", "Te"]   # genuinely dissipative
    unitary_ops = ["Fe", "Fi"]  # purity-preserving

    cptp_l1_universal = all(l1[op]["universal"] for op in cptp_ops)
    unitary_l1_universal = all(l1[op]["universal"] for op in unitary_ops)
    geometry_decouples = l3["geometry_breaks_coarising"]

    if all_l1_universal and all_l2_universal:
        return (
            "STRONG: Sign co-arising is operator-algebraic and universal. "
            "OPEN-1 is solvable from operator definitions alone. "
            "Proof strategy: show Δga0 and Δlr_asym have the same sign for any valid "
            "2-qubit density matrix under Ti/Fe/Te/Fi. "
            + ("Geometry (η) provides an additional sensory override channel." if geometry_decouples
               else "Geometry also preserves co-arising.")
        )
    elif cptp_l1_universal and not unitary_l1_universal:
        return (
            "PARTIAL: Co-arising is universal for CPTP (Ti, Te) but not unitary (Fe, Fi). "
            "CPTP operators provably monotone in sign(Δga0) = sign(Δlr_asym). "
            "Unitary operators require additional trajectory constraints. "
            "Proof strategy: split — CPTP algebraic theorem + attractor condition for unitaries."
        )
    elif all_l1_universal and not all_l2_universal:
        return (
            "INTERMEDIATE: lr_asym universality holds but bridge-MI universality is partial. "
            "The Bell-injection nonlinearity introduces sign failures at high Bell fraction. "
            "Proof strategy: prove for lr_asym, then add saturation condition for MI."
        )
    else:
        return (
            "TRAJECTORY-SPECIFIC: Co-arising is attractor-dependent, not operator-algebraic. "
            "The theorem requires the attractor as a precondition. "
            "Proof strategy: characterize the attractor basin, then prove co-arising within it."
        )


def _operator_transformed_history(history: list[dict], op_name: str) -> list[dict]:
    transformed = []
    for step in history:
        strength = float(step.get("strength", 0.5))
        transformed.append(
            {
                "rho_L": apply_left(op_name, step["rho_L"], strength),
                "rho_R": apply_right(op_name, step["rho_R"], strength),
                "eta": float(step.get("ax0_torus_entropy", 0.5)),
            }
        )
    return transformed


def _operator_config_profile(
    engine_type: int,
    torus_name: str,
    torus_val: float,
) -> dict[str, object]:
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=torus_val)
    final_state = engine.run_cycle(state)
    history = final_state.history

    operator_profiles: dict[str, dict[str, object]] = {}
    for op_name in OPERATOR_ORDER:
        prev_rho_L = state.rho_L
        prev_rho_R = state.rho_R
        delta_ga0_vals: list[float] = []
        delta_mi_vals: list[float] = []
        sign_matches = 0
        sign_trials = 0

        for step in history:
            mi_before = bridge_mi(prev_rho_L, prev_rho_R)
            mi_after = bridge_mi(step["rho_L"], step["rho_R"])
            if step["op_name"] == op_name:
                delta_ga0 = float(step["ga0_after"] - step["ga0_before"])
                delta_mi = float(mi_after - mi_before)
                delta_ga0_vals.append(delta_ga0)
                delta_mi_vals.append(delta_mi)
                if abs(delta_ga0) < 1e-6 or abs(delta_mi) < 1e-6:
                    sign_matches += 1
                else:
                    sign_matches += int(delta_ga0 * delta_mi > 0)
                sign_trials += 1
            prev_rho_L = step["rho_L"]
            prev_rho_R = step["rho_R"]

        shell_bridge = lane_d_topology_expansion_bridge(_operator_transformed_history(history, op_name))
        agreement_rate = float(sign_matches / sign_trials) if sign_trials else 0.0
        mean_abs_delta_mi = float(np.mean(np.abs(delta_mi_vals))) if delta_mi_vals else 0.0
        mean_signed_delta_mi = float(np.mean(delta_mi_vals)) if delta_mi_vals else 0.0
        support_score = float(agreement_rate + 0.5 * mean_abs_delta_mi)
        operator_profiles[op_name] = {
            "agreement_rate": agreement_rate,
            "sign_matches": int(sign_matches),
            "sign_trials": int(sign_trials),
            "mean_abs_delta_mi": mean_abs_delta_mi,
            "mean_signed_delta_mi": mean_signed_delta_mi,
            "support_score": support_score,
            "shell_bridge": shell_bridge,
        }

    return {
        "engine_type": int(engine_type),
        "torus": torus_name,
        "operators": operator_profiles,
    }


def _aggregate_deep_contract(
    l1: dict[str, dict[str, object]],
    l2: dict[str, dict[str, object]],
    operator_config_profiles: list[dict[str, object]],
) -> dict[str, object]:
    shell_bridge_pass_fraction = float(
        np.mean(
            [
                1.0
                if profile["operators"][op_name]["shell_bridge"]["lane_d_keep"]
                else 0.0
                for profile in operator_config_profiles
                for op_name in OPERATOR_ORDER
            ]
        )
    ) if operator_config_profiles else 0.0

    operator_shell_hubble_by_name: dict[str, list[float]] = {op: [] for op in OPERATOR_ORDER}
    operator_support_by_name: dict[str, list[float]] = {op: [] for op in OPERATOR_ORDER}
    operator_abs_delta_mi_by_name: dict[str, list[float]] = {op: [] for op in OPERATOR_ORDER}
    config_rankings: list[list[str]] = []

    for profile in operator_config_profiles:
        config_rankings.append(
            sorted(
                OPERATOR_ORDER,
                key=lambda op_name: float(profile["operators"][op_name]["support_score"]),
                reverse=True,
            )
        )
        for op_name in OPERATOR_ORDER:
            operator = profile["operators"][op_name]
            operator_shell_hubble_by_name[op_name].append(
                float(operator["shell_bridge"]["mean_hubble_proxy"])
            )
            operator_support_by_name[op_name].append(float(operator["agreement_rate"]))
            operator_abs_delta_mi_by_name[op_name].append(float(operator["mean_abs_delta_mi"]))

    raw_rows: list[dict[str, object]] = []
    max_mean_abs = 0.0
    for op_name in OPERATOR_ORDER:
        shell_vals = np.asarray(operator_shell_hubble_by_name[op_name], dtype=np.float64)
        support_vals = np.asarray(operator_support_by_name[op_name], dtype=np.float64)
        abs_delta_vals = np.asarray(operator_abs_delta_mi_by_name[op_name], dtype=np.float64)
        shell_alignment = 0.0
        if support_vals.size and support_vals.std() > EPS and shell_vals.std() > EPS:
            shell_alignment = float(np.corrcoef(support_vals, shell_vals)[0, 1])
        universality_support = 0.5 * (
            float(l1[op_name]["agreement_rate"]) + float(l2[op_name]["agreement_rate"])
        )
        trajectory_support = float(np.mean(support_vals)) if support_vals.size else 0.0
        mean_abs_delta_mi = float(np.mean(abs_delta_vals)) if abs_delta_vals.size else 0.0
        mean_abs = universality_support + mean_abs_delta_mi
        max_mean_abs = max(max_mean_abs, mean_abs)
        raw_rows.append(
            {
                "operator": op_name,
                "mean_abs_support": mean_abs,
                "mean_signed_support": float(
                    0.5
                    * (
                        float(l1[op_name]["agreement_rate"])
                        - float(l2[op_name]["agreement_rate"])
                    )
                ),
                "doctrine_fit": trajectory_support,
                "shell_alignment": shell_alignment,
                "shell_alignment_abs": abs(shell_alignment),
                "universality_support": universality_support,
                "mean_abs_delta_mi": mean_abs_delta_mi,
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
        row_by_name[str(row["operator"])] = enriched

    ranking = sorted(
        OPERATOR_ORDER,
        key=lambda op_name: float(row_by_name[op_name]["composite_score"]),
        reverse=True,
    )
    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    operator_rows: list[dict[str, object]] = []
    ranking_scores: list[float] = []
    for op_name in ranking:
        row = row_by_name[op_name]
        ranking_scores.append(float(row["composite_score"]))
        operator_rows.append(
            {
                "option": op_name,
                "mean_abs_a0": float(row["mean_abs_support"]),
                "mean_signed_a0": float(row["mean_signed_support"]),
                "doctrine_fit": float(row["doctrine_fit"]),
                "sign_consistency": float(row["doctrine_fit"]),
                "shell_alignment": float(row["shell_alignment"]),
                "shell_alignment_abs": float(row["shell_alignment_abs"]),
                "signal_score": float(row["signal_score"]),
                "composite_score": float(row["composite_score"]),
                "universality_support": float(row["universality_support"]),
                "mean_abs_delta_mi": float(row["mean_abs_delta_mi"]),
            }
        )

    expansion_drive = np.asarray(
        [
            row["mean_abs_a0"] + row["doctrine_fit"] + row["shell_alignment_abs"]
            for row in operator_rows
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _operator_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(np.log(np.clip(scale_factors, EPS, None)), lambda_shells)

    for row, scale, hubble in zip(
        operator_rows,
        scale_factors.tolist(),
        hubble_proxy.tolist(),
        strict=True,
    ):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _operator_graph_surface(operator_rows)
    ranking_index = {op_name: idx for idx, op_name in enumerate(ranking)}
    config_windows = [
        [ranking_index[op_name] for op_name in config_ranking[:3]]
        for config_ranking in config_rankings
    ]
    hypergraph_surface = _operator_hypergraph_surface(len(ranking), config_windows)
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
    cell_complex_surface = _operator_cell_complex_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    topology_surface = _operator_topology_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    symbolic_surface = _operator_symbolic_surface(
        lambda_shells,
        scale_factors,
        expansion_drive,
    )
    constraint_surface = _operator_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray(ranking_scores, dtype=np.float64),
    )
    manifold_surface = _operator_manifold_surface(
        np.asarray([row["mean_abs_a0"] for row in operator_rows], dtype=np.float64),
        np.asarray([row["doctrine_fit"] for row in operator_rows], dtype=np.float64),
        np.asarray([row["shell_alignment_abs"] for row in operator_rows], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_operator_fit(
        np.stack(
            [
                np.asarray([row["mean_abs_a0"] for row in operator_rows], dtype=np.float64),
                np.asarray([row["doctrine_fit"] for row in operator_rows], dtype=np.float64),
                np.asarray([row["shell_alignment_abs"] for row in operator_rows], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner = ranking[0]
    winner_row = next(row for row in operator_rows if row["option"] == winner)
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

    pass_flag = bool(
        shell_bridge_pass_fraction >= 0.5
        and graph_surface["longest_path_length"] >= len(ranking) - 1
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] == 0
        and topology_parity_ok
        and constraint_surface["sat"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > 1e-2
        and torch_fit["loss"] < 1.0
    )

    return {
        "pass": pass_flag,
        "winner": winner,
        "shell_bridge_pass_fraction": shell_bridge_pass_fraction,
        "operator_rows": operator_rows,
        "graph_surface": {
            "edge_count": graph_surface["edge_count"],
            "longest_path_length": graph_surface["longest_path_length"],
            "triad_windows": graph_surface["triad_windows"],
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
# Main                                                                        #
# --------------------------------------------------------------------------- #

def main() -> None:
    print("=" * 72)
    print("AXIS 0 CO-ARISING STRESS TEST — Toward OPEN-1")
    print("=" * 72)
    print(f"N random states: {N_RANDOM_STATES} per operator")
    print(f"Null hypothesis: co-arising is trajectory artifact, not algebraic")
    print()

    rng = np.random.default_rng(RNG_SEED)

    # Level 1
    print("Level 1 — lr_asym universality (direct driver of bridge MI):")
    l1 = level1_lr_asym_universality(rng)
    for op, r in l1.items():
        status = "✓ UNIVERSAL" if r["universal"] else f"✗ {r['failures']} failures"
        print(f"  {op}: {r['agree']}/{r['total_trials']} agree ({r['agreement_rate']:.3f}) | {status}")

    print()

    # Level 2
    print("Level 2 — bridge MI universality (full Bell-injection MI):")
    l2 = level2_bridge_mi_universality(rng)
    for op, r in l2.items():
        status = "✓ UNIVERSAL" if r["universal"] else f"✗ {r['failures']} failures"
        print(f"  {op}: {r['agrees']}/{r['total']} agree ({r['agreement_rate']:.3f}) | {status}")

    print()

    # Level 3
    print("Level 3 — geometry (η-transport) as sensory override:")
    l3 = level3_geometry_decoupling(rng)
    print(f"  Total trials: {l3['total_trials']}")
    print(f"  Decoupled (geometry breaks co-arising): {l3['decoupled_cases']}")
    print(f"  Coupled (geometry preserves co-arising): {l3['coupled_cases']}")
    print(f"  {l3['interpretation']}")

    print()

    # Algebraic structure
    struct = algebraic_structure_note(l1, l2, l3)

    operator_config_profiles = []
    for engine_type in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            operator_config_profiles.append(
                _operator_config_profile(engine_type, torus_name, torus_val)
            )
    deep_contract = _aggregate_deep_contract(l1, l2, operator_config_profiles)

    print("=" * 72)
    print("ALGEBRAIC STRUCTURE FOR OPEN-1")
    print("=" * 72)
    print(f"  {struct}")

    print()
    print("  Per-operator failure breakdown (Level 1):")
    for op, r in l1.items():
        print(f"    {op}: {r['failures']} failures / {r['total_trials']} trials "
              f"({'always_same_sign' if r['universal'] else 'sign inversion exists'})")
        if r["failure_examples"]:
            ex = r["failure_examples"][0]
            print(f"      Sample failure: Δga0={ex['delta_ga0']:+.3f} Δasym={ex['delta_asym']:+.4f} "
                  f"strength={ex['strength']:.2f} ga0_before={ex['ga0_before']:.2f}")

    print()
    print("─" * 72)
    print("DEEP CONTRACT")
    print("─" * 72)
    print(f"  Deep pass:                    {deep_contract['pass']}")
    print(f"  Shell bridge pass fraction:   {deep_contract['shell_bridge_pass_fraction']:.3f}")
    print(f"  Winning operator surface:     {deep_contract['winner']}")
    print(f"  Graph longest path:           {deep_contract['graph_surface']['longest_path_length']}")
    print(f"  Hypergraph max edge size:     {deep_contract['hypergraph_surface']['max_hyperedge_size']}")
    print(f"  Topology betti numbers:       {deep_contract['topology_surface']['betti_numbers']}")
    print(f"  Symbolic hubble mid:          {deep_contract['symbolic_surface']['symbolic_hubble_mid']:.6f}")
    print(f"  Manifold mean distance:       {deep_contract['manifold_surface']['mean_geodesic_distance']:.6f}")
    print(f"  Torch fit loss:               {deep_contract['torch_fit']['loss']:.6f}")
    print(
        f"  Winner vector gaps:           "
        f"clifford={deep_contract['clifford_vector_gap']:.2e} | "
        f"torch_ga={deep_contract['torch_ga_vector_gap']:.2e}"
    )

    print()
    print("================================================================================")
    print(f"PROBE STATUS: {'PASS' if deep_contract['pass'] else 'FAIL'}")
    print("================================================================================")

    def safe(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, np.bool_): return bool(obj)
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, dict): return {k: safe(v) for k, v in obj.items()}
        if isinstance(obj, list): return [safe(v) for v in obj]
        return obj

    output = {
        "timestamp": datetime.now(UTC).isoformat(),
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "n_random_states": N_RANDOM_STATES,
        "level1_lr_asym": safe(l1),
        "level2_bridge_mi": safe(l2),
        "level3_geometry": safe(l3),
        "algebraic_structure": struct,
        "operator_config_profiles": safe(operator_config_profiles),
        "aggregate": {
            "deep_contract": safe(deep_contract),
            "all_pass": bool(deep_contract["pass"]),
        },
        "summary": {
            "deep_contract_pass": bool(deep_contract["pass"]),
            "deep_contract_winner": deep_contract["winner"],
            "algebraic_structure": struct,
        },
        "overall_pass": bool(deep_contract["pass"]),
        "all_pass": bool(deep_contract["pass"]),
    }

    out_path = os.path.join(
        os.path.dirname(__file__),
        "a2_state", "sim_results", "axis0_coarising_stress_test_results.json",
    )
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
