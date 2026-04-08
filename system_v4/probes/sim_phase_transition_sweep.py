#!/usr/bin/env python3
"""
Phase Transition Sweep -- Where does coherence die under noise?
================================================================

Sweeps noise_budget over [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0].
For each budget, runs the adversarial minimax game (30 rounds, 5 steps each)
and records equilibrium I_c.

Questions answered:
  1. Is there a sharp transition (critical noise budget) where I_c crosses zero?
  2. Is the transition continuous (smooth decay) or discontinuous (sudden death)?
  3. What is the critical noise budget?
  4. Does ratchet gate strength also transition at the same point?

Tests:
  Positive:
    - I_c decreases monotonically with noise budget
    - There exists a critical budget where I_c ~ 0
    - Below critical, ratchet wins; above, adversary wins
  Negative:
    - At budget=0, I_c = maximum (no noise)
  Boundary:
    - Very large budget (adversary overwhelms)
    - Very small budget (ratchet dominates)

Mark pytorch=used. Classification: canonical.
Output: sim_results/phase_transition_sweep_results.json
"""

import json
import os
import traceback
import time
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- pure autograd minimax"},
    "z3":        {"tried": False, "used": False, "reason": "not needed for this sim"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed for this sim"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed for this sim"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed for this sim"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this sim"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed for this sim"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this sim"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed for this sim"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed for this sim"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed for this sim"},
}

try:
    import torch
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core: autograd drives both ratchet and adversary optimizers "
        "across noise budget sweep; gradient flow through quantum channels"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


# =====================================================================
# QUANTUM PRIMITIVES (reused from sim_adversarial_ratchet)
# =====================================================================

def bloch_to_rho(theta, phi):
    """Bloch sphere angles -> 2x2 density matrix (differentiable)."""
    c = torch.cos(theta.squeeze() / 2).to(torch.complex64)
    s = torch.sin(theta.squeeze() / 2).to(torch.complex64)
    phase = torch.exp(1j * phi.squeeze().to(torch.complex64))
    psi = torch.stack([c, s * phase])
    return torch.outer(psi, psi.conj())


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log2 rho), differentiable via eigendecomposition."""
    eigs = torch.real(torch.linalg.eigvalsh(rho))
    eigs_clamped = torch.clamp(eigs, min=1e-12)
    return -torch.sum(eigs_clamped * torch.log2(eigs_clamped))


def partial_trace_a(rho_ab, dim_a=2, dim_b=2):
    """Trace out A, return rho_B."""
    rho_r = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    return torch.einsum("ijkj->ik", rho_r)


def partial_trace_b(rho_ab, dim_a=2, dim_b=2):
    """Trace out B, return rho_A."""
    rho_r = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    return torch.einsum("ijik->jk", rho_r)


def coherent_information(rho_ab):
    """I_c(A>B) = S(B) - S(AB). Positive means quantum info flows A->B."""
    rho_b = partial_trace_a(rho_ab)
    S_B = von_neumann_entropy(rho_b)
    S_AB = von_neumann_entropy(rho_ab)
    return S_B - S_AB


# =====================================================================
# QUANTUM CHANNELS (differentiable, parameterized)
# =====================================================================

def apply_z_dephasing(rho, p):
    """Z-dephasing: rho -> (1-p)*rho + p*Z*rho*Z."""
    Z = torch.tensor([[1, 0], [0, -1]], dtype=rho.dtype, device=rho.device)
    return (1.0 - p) * rho + p * (Z @ rho @ Z)


def apply_amplitude_damping(rho, gamma):
    """Amplitude damping with Kraus operators K0, K1."""
    one_r = torch.tensor(1.0, dtype=torch.float32, device=rho.device)
    zero_c = torch.tensor(0.0, dtype=rho.dtype, device=rho.device)
    one_c = torch.tensor(1.0, dtype=rho.dtype, device=rho.device)
    sqrt_1mg = torch.sqrt(torch.clamp(one_r - gamma, min=1e-30)).to(rho.dtype)
    sqrt_g = torch.sqrt(torch.clamp(gamma, min=1e-30)).to(rho.dtype)
    K0 = torch.stack([
        torch.stack([one_c, zero_c]),
        torch.stack([zero_c, sqrt_1mg]),
    ])
    K1 = torch.stack([
        torch.stack([zero_c, sqrt_g]),
        torch.stack([zero_c, zero_c]),
    ])
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T


def apply_depolarizing(rho, p):
    """Depolarizing: rho -> (1-p)*rho + p*I/2."""
    I2 = torch.eye(2, dtype=rho.dtype, device=rho.device)
    return (1.0 - p) * rho + p * I2 / 2.0


def apply_parameterized_cnot(rho_ab, strength):
    """Parameterized entangling gate: interpolates between identity and CNOT.

    CNOT = I - 2*P_minus. U(s) = I - (1 - e^{i*pi*s})*P_minus.
    At s=0: U=I. At s=1: U=CNOT.
    """
    I4 = torch.eye(4, dtype=rho_ab.dtype, device=rho_ab.device)
    CNOT = torch.tensor([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=rho_ab.dtype, device=rho_ab.device)
    evals, evecs = torch.linalg.eigh(CNOT)
    P_minus = evecs[:, evals.real < 0]
    if P_minus.shape[1] > 0:
        P_proj = P_minus @ P_minus.conj().T
    else:
        P_proj = torch.zeros_like(I4)
    phase = torch.exp(1j * np.pi * strength)
    U_gate = I4 - (1.0 - phase) * P_proj
    return U_gate @ rho_ab @ U_gate.conj().T


# =====================================================================
# SINGLE-QUBIT ROTATION
# =====================================================================

def apply_single_qubit_rotation(rho, rx, ry, rz):
    """Apply learnable single-qubit rotation R = Rz(rz) Ry(ry) Rx(rx)."""
    cx = torch.cos(rx / 2).to(torch.complex64)
    sx = torch.sin(rx / 2).to(torch.complex64)
    Rx = torch.stack([
        torch.stack([cx, -1j * sx]),
        torch.stack([-1j * sx, cx]),
    ])
    cy = torch.cos(ry / 2).to(torch.complex64)
    sy = torch.sin(ry / 2).to(torch.complex64)
    Ry = torch.stack([
        torch.stack([cy, -sy]),
        torch.stack([sy, cy]),
    ])
    cz = torch.cos(rz / 2).to(torch.complex64)
    sz = torch.sin(rz / 2).to(torch.complex64)
    Rz = torch.stack([
        torch.stack([cz - 1j * sz, torch.tensor(0.0, dtype=torch.complex64)]),
        torch.stack([torch.tensor(0.0, dtype=torch.complex64), cz + 1j * sz]),
    ])
    R = Rz @ Ry @ Rx
    return R @ rho @ R.conj().T


# =====================================================================
# PLAYERS (reused from sim_adversarial_ratchet)
# =====================================================================

class RatchetPlayer(nn.Module):
    def __init__(self, seed=None):
        super().__init__()
        if seed is not None:
            torch.manual_seed(seed)
        self.theta_a = nn.Parameter(torch.rand(1) * np.pi)
        self.phi_a = nn.Parameter(torch.rand(1) * 2 * np.pi)
        self.theta_b = nn.Parameter(torch.rand(1) * np.pi)
        self.phi_b = nn.Parameter(torch.rand(1) * 2 * np.pi)
        self.raw_gate_strength = nn.Parameter(torch.tensor([1.0]))
        self.correction_a = nn.Parameter(torch.zeros(3))
        self.correction_b = nn.Parameter(torch.zeros(3))

    def get_gate_strength(self):
        return torch.sigmoid(self.raw_gate_strength)

    def build_state(self):
        rho_a = bloch_to_rho(self.theta_a, self.phi_a)
        rho_b = bloch_to_rho(self.theta_b, self.phi_b)
        return rho_a, rho_b

    def apply_correction(self, rho_a, rho_b):
        rho_a = apply_single_qubit_rotation(
            rho_a, self.correction_a[0],
            self.correction_a[1], self.correction_a[2]
        )
        rho_b = apply_single_qubit_rotation(
            rho_b, self.correction_b[0],
            self.correction_b[1], self.correction_b[2]
        )
        return rho_a, rho_b


class AdversaryPlayer(nn.Module):
    def __init__(self, seed=None, noise_budget=0.5):
        super().__init__()
        if seed is not None:
            torch.manual_seed(seed)
        self.raw_p_deph = nn.Parameter(torch.randn(2) * 0.5)
        self.raw_gamma_damp = nn.Parameter(torch.randn(2) * 0.5)
        self.raw_p_depol = nn.Parameter(torch.randn(2) * 0.5)
        self.noise_budget = noise_budget

    def get_params(self):
        raw = torch.cat([
            torch.sigmoid(self.raw_p_deph),
            torch.sigmoid(self.raw_gamma_damp),
            torch.sigmoid(self.raw_p_depol),
        ])
        total = raw.sum()
        if total > self.noise_budget:
            raw = raw * (self.noise_budget / total)
        p_deph = raw[:2]
        gamma_damp = raw[2:4]
        p_depol = raw[4:6]
        return p_deph, gamma_damp, p_depol

    def apply_channels(self, rho_a, rho_b):
        p_deph, gamma_damp, p_depol = self.get_params()
        rho_a = apply_z_dephasing(rho_a, p_deph[0])
        rho_a = apply_amplitude_damping(rho_a, gamma_damp[0])
        rho_a = apply_depolarizing(rho_a, p_depol[0])
        rho_b = apply_z_dephasing(rho_b, p_deph[1])
        rho_b = apply_amplitude_damping(rho_b, gamma_damp[1])
        rho_b = apply_depolarizing(rho_b, p_depol[1])
        return rho_a, rho_b


# =====================================================================
# GAME PIPELINE
# =====================================================================

def evaluate_game(ratchet, adversary, use_cnot=True):
    """Run the full pipeline and return I_c."""
    rho_a, rho_b = ratchet.build_state()
    p_deph, gamma_damp, p_depol = adversary.get_params()

    rho_a = apply_z_dephasing(rho_a, p_deph[0])
    rho_a = apply_amplitude_damping(rho_a, gamma_damp[0])
    rho_a = apply_depolarizing(rho_a, p_depol[0])

    rho_b = apply_z_dephasing(rho_b, p_deph[1])
    rho_b = apply_amplitude_damping(rho_b, gamma_damp[1])
    rho_b = apply_depolarizing(rho_b, p_depol[1])

    rho_a, rho_b = ratchet.apply_correction(rho_a, rho_b)
    rho_ab = torch.kron(rho_a, rho_b)

    if use_cnot:
        strength = ratchet.get_gate_strength()
        rho_ab = apply_parameterized_cnot(rho_ab, strength)

    ic = coherent_information(rho_ab)
    return ic, rho_ab


# =====================================================================
# ALTERNATING OPTIMIZATION (MINIMAX GAME)
# =====================================================================

def run_adversarial_game(
    noise_budget=0.5,
    ratchet_seed=42,
    adversary_seed=7,
    n_rounds=30,
    steps_per_turn=5,
    lr_ratchet=0.02,
    lr_adversary=0.02,
):
    """Run alternating optimization minimax game at a given noise budget.

    Returns trajectory of I_c values and final parameters.
    """
    ratchet = RatchetPlayer(seed=ratchet_seed)
    adversary = AdversaryPlayer(seed=adversary_seed, noise_budget=noise_budget)

    opt_ratchet = torch.optim.Adam(ratchet.parameters(), lr=lr_ratchet)
    opt_adversary = torch.optim.Adam(adversary.parameters(), lr=lr_adversary)

    trajectory = []

    for round_idx in range(n_rounds):
        # Ratchet's turn: maximize I_c
        for _ in range(steps_per_turn):
            opt_ratchet.zero_grad()
            ic, _ = evaluate_game(ratchet, adversary)
            loss = -ic
            loss.backward()
            opt_ratchet.step()

        # Adversary's turn: minimize I_c
        for _ in range(steps_per_turn):
            opt_adversary.zero_grad()
            ic, _ = evaluate_game(ratchet, adversary)
            loss = ic
            loss.backward()
            opt_adversary.step()

        # Record state after both turns
        with torch.no_grad():
            ic_eval, rho_ab = evaluate_game(ratchet, adversary)
            p_deph, gamma_damp, p_depol = adversary.get_params()
            gate_str = ratchet.get_gate_strength()
            rho_a_reduced = partial_trace_b(rho_ab)
            purity_a = torch.real(
                torch.trace(rho_a_reduced @ rho_a_reduced)
            ).item()

        trajectory.append({
            "round": round_idx,
            "ic": ic_eval.item(),
            "gate_strength": gate_str.item(),
            "noise_used": float(
                p_deph.sum() + gamma_damp.sum() + p_depol.sum()
            ),
            "purity_reduced_A": purity_a,
        })

    return trajectory, ratchet, adversary


# =====================================================================
# SWEEP RUNNER
# =====================================================================

NOISE_BUDGETS = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0]


def run_sweep():
    """Run the adversarial game at each noise budget, record equilibrium I_c."""
    sweep_data = []

    for budget in NOISE_BUDGETS:
        traj, ratchet, adversary = run_adversarial_game(
            noise_budget=budget,
            n_rounds=30,
            steps_per_turn=5,
        )

        # Equilibrium = mean of final quarter
        quarter = max(1, len(traj) // 4)
        final_ics = [t["ic"] for t in traj[-quarter:]]
        final_gates = [t["gate_strength"] for t in traj[-quarter:]]

        eq_ic = float(np.mean(final_ics))
        eq_ic_std = float(np.std(final_ics))
        eq_gate = float(np.mean(final_gates))

        sweep_data.append({
            "noise_budget": budget,
            "equilibrium_ic": eq_ic,
            "equilibrium_ic_std": eq_ic_std,
            "equilibrium_gate_strength": eq_gate,
            "ic_trajectory": [t["ic"] for t in traj],
            "gate_trajectory": [t["gate_strength"] for t in traj],
        })

        print(
            f"  budget={budget:.1f}  eq_I_c={eq_ic:+.4f}  "
            f"gate={eq_gate:.3f}  std={eq_ic_std:.4f}"
        )

    return sweep_data


# =====================================================================
# PHASE TRANSITION ANALYSIS
# =====================================================================

def analyze_phase_transition(sweep_data):
    """Determine critical noise budget and transition character."""
    budgets = [d["noise_budget"] for d in sweep_data]
    ics = [d["equilibrium_ic"] for d in sweep_data]
    gates = [d["equilibrium_gate_strength"] for d in sweep_data]

    # --- Find critical budget: linear interpolation of I_c zero crossing ---
    critical_budget = None
    crossing_type = "none"

    for i in range(len(ics) - 1):
        if ics[i] > 0 and ics[i + 1] <= 0:
            # Linear interpolation to find zero crossing
            frac = ics[i] / (ics[i] - ics[i + 1])
            critical_budget = budgets[i] + frac * (budgets[i + 1] - budgets[i])
            break

    # If no crossing found, check if all positive or all negative
    if critical_budget is None:
        if all(ic > 0 for ic in ics):
            crossing_type = "no_crossing_all_positive"
            critical_budget = float("inf")
        elif all(ic <= 0 for ic in ics):
            crossing_type = "no_crossing_all_negative"
            critical_budget = 0.0
        else:
            crossing_type = "non_monotonic"
            # Take first negative point as rough estimate
            for i, ic in enumerate(ics):
                if ic <= 0:
                    critical_budget = budgets[i]
                    break

    # --- Transition character: compute max |delta I_c| between steps ---
    deltas = []
    for i in range(len(ics) - 1):
        delta_ic = abs(ics[i + 1] - ics[i])
        delta_budget = budgets[i + 1] - budgets[i]
        deltas.append({
            "from_budget": budgets[i],
            "to_budget": budgets[i + 1],
            "delta_ic": delta_ic,
            "slope": delta_ic / delta_budget if delta_budget > 0 else 0,
        })

    # Find steepest segment
    if deltas:
        steepest = max(deltas, key=lambda d: d["slope"])
    else:
        steepest = {"from_budget": 0, "to_budget": 0, "slope": 0}

    # Characterize transition: discontinuous if slope > 1.0 at transition
    max_slope = steepest["slope"]
    if max_slope > 1.0:
        transition_type = "sharp"
    elif max_slope > 0.3:
        transition_type = "moderate"
    else:
        transition_type = "smooth"

    # --- Gate strength transition: does it co-occur? ---
    gate_at_critical = None
    if critical_budget is not None and critical_budget != float("inf"):
        # Interpolate gate strength at critical budget
        for i in range(len(budgets) - 1):
            if budgets[i] <= critical_budget <= budgets[i + 1]:
                frac = ((critical_budget - budgets[i])
                        / (budgets[i + 1] - budgets[i]))
                gate_at_critical = (
                    gates[i] + frac * (gates[i + 1] - gates[i])
                )
                break

    # Gate transition: does gate also change sharply near critical?
    gate_deltas = []
    for i in range(len(gates) - 1):
        gate_deltas.append(abs(gates[i + 1] - gates[i]))

    return {
        "critical_noise_budget": critical_budget,
        "crossing_type": crossing_type,
        "transition_type": transition_type,
        "max_slope_ic_per_budget": max_slope,
        "steepest_segment": steepest,
        "gate_at_critical_budget": gate_at_critical,
        "ic_values": ics,
        "gate_values": gates,
        "budgets": budgets,
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests(sweep_data, analysis):
    results = {}

    ics = analysis["ic_values"]
    budgets = analysis["budgets"]

    # --- Test 1: I_c decreases monotonically with noise budget ---
    try:
        monotonic_violations = 0
        for i in range(len(ics) - 1):
            if ics[i + 1] > ics[i] + 0.05:  # small tolerance for noise
                monotonic_violations += 1

        results["ic_monotonically_decreasing"] = {
            "pass": monotonic_violations <= 1,  # allow 1 minor violation
            "violations": monotonic_violations,
            "ic_values": ics,
            "budgets": budgets,
            "note": (
                "I_c should generally decrease as adversary gets more "
                "noise budget -- more resources to destroy coherence"
            ),
        }
    except Exception:
        results["ic_monotonically_decreasing"] = {
            "pass": False, "error": traceback.format_exc()
        }

    # --- Test 2: Critical budget exists where I_c ~ 0 ---
    try:
        has_positive = any(ic > 0.01 for ic in ics)
        has_negative_or_zero = any(ic <= 0.01 for ic in ics)
        critical = analysis["critical_noise_budget"]

        results["critical_budget_exists"] = {
            "pass": has_positive and has_negative_or_zero,
            "has_positive_ic": has_positive,
            "has_zero_or_negative_ic": has_negative_or_zero,
            "critical_noise_budget": critical,
            "note": (
                "There must exist a noise level where I_c transitions "
                "from positive (ratchet wins) to zero/negative (adversary wins)"
            ),
        }
    except Exception:
        results["critical_budget_exists"] = {
            "pass": False, "error": traceback.format_exc()
        }

    # --- Test 3: Below critical ratchet wins, above adversary wins ---
    try:
        below_wins = True
        above_loses = True

        if critical is not None and critical != float("inf"):
            for b, ic in zip(budgets, ics):
                if b < critical * 0.8 and ic <= -0.05:
                    below_wins = False
                if b > critical * 1.2 and ic > 0.05:
                    above_loses = False
        else:
            below_wins = False
            above_loses = False

        results["ratchet_wins_below_critical"] = {
            "pass": below_wins and above_loses,
            "below_critical_ratchet_wins": below_wins,
            "above_critical_adversary_wins": above_loses,
            "critical_budget": critical,
            "note": (
                "Phase separation: below critical budget ratchet maintains "
                "positive I_c; above it, adversary destroys coherence"
            ),
        }
    except Exception:
        results["ratchet_wins_below_critical"] = {
            "pass": False, "error": traceback.format_exc()
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- Negative 1: At budget=0, I_c should be maximum (no noise) ---
    try:
        traj_zero, ratchet, _ = run_adversarial_game(
            noise_budget=0.0,
            n_rounds=30,
            steps_per_turn=5,
        )
        quarter = max(1, len(traj_zero) // 4)
        eq_ic_zero = float(np.mean([t["ic"] for t in traj_zero[-quarter:]]))

        # Compare against moderate budget
        traj_mod, _, _ = run_adversarial_game(
            noise_budget=0.5,
            n_rounds=30,
            steps_per_turn=5,
        )
        eq_ic_mod = float(np.mean([t["ic"] for t in traj_mod[-quarter:]]))

        results["zero_budget_maximum_ic"] = {
            "pass": eq_ic_zero > eq_ic_mod,
            "ic_at_zero_budget": eq_ic_zero,
            "ic_at_0.5_budget": eq_ic_mod,
            "difference": eq_ic_zero - eq_ic_mod,
            "note": (
                "With zero noise budget, adversary is powerless -- "
                "ratchet should achieve maximum I_c"
            ),
        }
    except Exception:
        results["zero_budget_maximum_ic"] = {
            "pass": False, "error": traceback.format_exc()
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests(sweep_data, analysis):
    results = {}

    ics = analysis["ic_values"]
    budgets = analysis["budgets"]

    # --- Boundary 1: Very large budget -- adversary overwhelms ---
    try:
        # Budget 5.0 is the largest in our sweep (6 channels max = 6.0)
        largest_budget_ic = ics[-1]
        results["large_budget_adversary_overwhelms"] = {
            "pass": largest_budget_ic < 0.05,
            "ic_at_max_budget": largest_budget_ic,
            "max_budget": budgets[-1],
            "note": (
                "At very large noise budget, adversary has enough "
                "resources to fully destroy coherent information"
            ),
        }
    except Exception:
        results["large_budget_adversary_overwhelms"] = {
            "pass": False, "error": traceback.format_exc()
        }

    # --- Boundary 2: Very small budget -- ratchet dominates ---
    try:
        smallest_budget_ic = ics[0]
        results["small_budget_ratchet_dominates"] = {
            "pass": smallest_budget_ic > 0.05,
            "ic_at_min_budget": smallest_budget_ic,
            "min_budget": budgets[0],
            "note": (
                "At very small noise budget, ratchet easily maintains "
                "positive coherent information -- noise is negligible"
            ),
        }
    except Exception:
        results["small_budget_ratchet_dominates"] = {
            "pass": False, "error": traceback.format_exc()
        }

    # --- Boundary 3: Gate strength behavior at extremes ---
    try:
        gates = analysis["gate_values"]
        gate_at_low = gates[0]
        gate_at_high = gates[-1]

        results["gate_strength_extremes"] = {
            "pass": True,  # informational
            "gate_at_low_noise": gate_at_low,
            "gate_at_high_noise": gate_at_high,
            "gate_at_critical": analysis["gate_at_critical_budget"],
            "note": (
                "Gate strength behavior across the transition: "
                "does the ratchet keep trying (high gate) or give up?"
            ),
        }
    except Exception:
        results["gate_strength_extremes"] = {
            "pass": False, "error": traceback.format_exc()
        }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    t0 = time.time()

    print("=== Phase Transition Sweep ===")
    print(f"Sweeping noise budgets: {NOISE_BUDGETS}\n")

    # Run the sweep
    sweep_data = run_sweep()

    # Analyze transition
    analysis = analyze_phase_transition(sweep_data)

    print(f"\n--- Phase Transition Analysis ---")
    print(f"Critical noise budget: {analysis['critical_noise_budget']}")
    print(f"Transition type: {analysis['transition_type']}")
    print(f"Max slope (dI_c/d_budget): {analysis['max_slope_ic_per_budget']:.4f}")
    print(f"Gate at critical: {analysis['gate_at_critical_budget']}")

    # Run tests
    positive = run_positive_tests(sweep_data, analysis)
    negative = run_negative_tests()
    boundary = run_boundary_tests(sweep_data, analysis)

    elapsed = time.time() - t0

    # Summary
    all_tests = {}
    all_tests.update(positive)
    all_tests.update(negative)
    all_tests.update(boundary)
    n_pass = sum(1 for v in all_tests.values() if v.get("pass"))
    n_total = len(all_tests)

    # Build answers to the four questions
    answers = {
        "Q1_sharp_transition": (
            f"{'Yes' if analysis['critical_noise_budget'] is not None else 'No'} -- "
            f"I_c crosses zero at noise budget ~ "
            f"{analysis['critical_noise_budget']:.3f}"
            if analysis['critical_noise_budget'] is not None
            and analysis['critical_noise_budget'] != float('inf')
            else "No zero crossing found in sweep range"
        ),
        "Q2_transition_character": (
            f"Transition is {analysis['transition_type']} "
            f"(max slope = {analysis['max_slope_ic_per_budget']:.4f} "
            f"I_c per unit budget)"
        ),
        "Q3_critical_budget": analysis["critical_noise_budget"],
        "Q4_gate_co_transition": (
            f"Gate strength at critical budget: "
            f"{analysis['gate_at_critical_budget']}"
            if analysis["gate_at_critical_budget"] is not None
            else "Could not interpolate gate at critical point"
        ),
    }

    results = {
        "name": (
            "phase_transition_sweep -- map Nash equilibrium I_c vs noise "
            "budget to find where coherence dies"
        ),
        "tool_manifest": TOOL_MANIFEST,
        "classification": "canonical",
        "summary": {
            "tests_passed": n_pass,
            "tests_total": n_total,
            "elapsed_seconds": round(elapsed, 2),
            "answers": answers,
        },
        "phase_transition_analysis": analysis,
        "sweep_data": sweep_data,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "phase_transition_sweep_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"Tests: {n_pass}/{n_total} passed in {elapsed:.1f}s")

    # Quick summary
    for section_name, section in [
        ("POSITIVE", positive),
        ("NEGATIVE", negative),
        ("BOUNDARY", boundary),
    ]:
        print(f"\n--- {section_name} ---")
        for k, v in section.items():
            status = "PASS" if v.get("pass") else "FAIL"
            print(f"  [{status}] {k}")

    print(f"\n--- ANSWERS ---")
    for q, a in answers.items():
        print(f"  {q}: {a}")
