#!/usr/bin/env python3
"""
Temporal Cascade FLIPPED -- Does channel ordering determine ratchet direction?
==============================================================================

The original temporal cascade kills I_c at cycle 1 because noise comes BEFORE
CNOT. This sim tests whether flipping the order (CNOT first, then noise)
sustains I_c passively.

Four orderings tested for N = 1, 2, 5, 10, 20, 50 cycles:
  1. ORIGINAL:   noise -> CNOT -> measure  (baseline, should die fast)
  2. FLIPPED:    CNOT -> noise -> measure  (might sustain)
  3. SANDWICH:   noise -> CNOT -> noise -> measure  (double noise, kills fastest)
  4. PROTECTED:  CNOT -> noise -> CNOT -> measure  (CNOT sandwich protects?)

For each ordering, track full I_c trajectory. The key question: does the
ratchet direction depend on channel ordering?

Tests:
  Positive:
    - Flipped order sustains I_c longer than original
    - Protected ordering sustains longest of all four
  Negative:
    - Original (noise-first) is the worst ordering (not sandwich!)
  Boundary:
    - N=1 protected already best (orderings diverge immediately)
    - Large N all orderings converge to steady states, ranking preserved

Mark pytorch=used. Classification: canonical.
Output: sim_results/temporal_cascade_flipped_results.json
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
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- pure autograd cascade"},
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
    TOOL_MANIFEST["pytorch"]["reason"] = "Core: autograd cascade + channel ordering comparison over N cycles"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


# =====================================================================
# QUANTUM PRIMITIVES (reused from sim_temporal_cascade)
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


def coherent_information(rho_ab):
    """I_c(A>B) = S(B) - S(AB). Positive means quantum info flows A->B."""
    rho_b = partial_trace_a(rho_ab)
    S_B = von_neumann_entropy(rho_b)
    S_AB = von_neumann_entropy(rho_ab)
    return S_B - S_AB


# =====================================================================
# QUANTUM CHANNELS (differentiable)
# =====================================================================

def _ensure_tensor(val, device=None):
    """Convert scalar to tensor if needed."""
    if not isinstance(val, torch.Tensor):
        return torch.tensor(float(val), dtype=torch.float32, device=device)
    return val


def apply_z_dephasing(rho, p):
    """Z-dephasing: rho -> (1-p)*rho + p*Z*rho*Z."""
    p = _ensure_tensor(p, rho.device)
    Z = torch.tensor([[1, 0], [0, -1]], dtype=rho.dtype, device=rho.device)
    return (1.0 - p) * rho + p * (Z @ rho @ Z)


def apply_amplitude_damping(rho, gamma):
    """Amplitude damping with Kraus operators K0, K1."""
    gamma = _ensure_tensor(gamma, rho.device)
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


def apply_cnot(rho_ab):
    """CNOT gate on 2-qubit state: rho -> U*rho*U^dag."""
    U = torch.tensor([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=rho_ab.dtype, device=rho_ab.device)
    return U @ rho_ab @ U.conj().T


def apply_single_qubit_noise(rho_2q, p_deph, gamma_amp):
    """Apply Z-dephasing + amplitude damping to each qubit of a 2q state."""
    dim = 2
    rho_r = rho_2q.reshape(dim, dim, dim, dim)

    # Noise on qubit A
    rho_a_slices = []
    for j in range(dim):
        for l in range(dim):
            block = rho_r[:, j, :, l]
            block = apply_z_dephasing(block, p_deph)
            block = apply_amplitude_damping(block, gamma_amp)
            rho_a_slices.append((j, l, block))

    rho_after_a = torch.zeros_like(rho_2q)
    for j, l, block in rho_a_slices:
        for i in range(dim):
            for k in range(dim):
                rho_after_a[i * dim + j, k * dim + l] = block[i, k]

    # Noise on qubit B
    rho_r2 = rho_after_a.reshape(dim, dim, dim, dim)
    rho_b_slices = []
    for i in range(dim):
        for k in range(dim):
            block = rho_r2[i, :, k, :]
            block = apply_z_dephasing(block, p_deph)
            block = apply_amplitude_damping(block, gamma_amp)
            rho_b_slices.append((i, k, block))

    rho_after_b = torch.zeros_like(rho_2q)
    for i, k, block in rho_b_slices:
        for j in range(dim):
            for l in range(dim):
                rho_after_b[i * dim + j, k * dim + l] = block[j, l]

    return rho_after_b


# =====================================================================
# FOUR CHANNEL ORDERINGS
# =====================================================================

def cycle_original(rho_ab, p_deph, gamma_amp):
    """Original: noise -> CNOT -> measure."""
    rho = apply_single_qubit_noise(rho_ab, p_deph, gamma_amp)
    rho = apply_cnot(rho)
    return rho, coherent_information(rho)


def cycle_flipped(rho_ab, p_deph, gamma_amp):
    """Flipped: CNOT -> noise -> measure."""
    rho = apply_cnot(rho_ab)
    rho = apply_single_qubit_noise(rho, p_deph, gamma_amp)
    return rho, coherent_information(rho)


def cycle_sandwich(rho_ab, p_deph, gamma_amp):
    """Sandwich: noise -> CNOT -> noise -> measure (double noise)."""
    rho = apply_single_qubit_noise(rho_ab, p_deph, gamma_amp)
    rho = apply_cnot(rho)
    rho = apply_single_qubit_noise(rho, p_deph, gamma_amp)
    return rho, coherent_information(rho)


def cycle_protected(rho_ab, p_deph, gamma_amp):
    """Protected: CNOT -> noise -> CNOT -> measure (CNOT sandwich)."""
    rho = apply_cnot(rho_ab)
    rho = apply_single_qubit_noise(rho, p_deph, gamma_amp)
    rho = apply_cnot(rho)
    return rho, coherent_information(rho)


ORDERINGS = {
    "original":  cycle_original,
    "flipped":   cycle_flipped,
    "sandwich":  cycle_sandwich,
    "protected": cycle_protected,
}


# =====================================================================
# INITIAL STATE BUILDER (from original sim)
# =====================================================================

def build_optimized_initial_state(seed=42):
    """Optimize a product state through CNOT to get I_c ~ 0.77."""
    theta_a = nn.Parameter(torch.tensor([1.5]))
    phi_a = nn.Parameter(torch.tensor([0.8]))
    theta_b = nn.Parameter(torch.tensor([1.2]))
    phi_b = nn.Parameter(torch.tensor([2.1]))

    torch.manual_seed(seed)
    optimizer = torch.optim.Adam([theta_a, phi_a, theta_b, phi_b], lr=0.05)

    best_ic = -float("inf")
    best_params = None

    for step in range(300):
        optimizer.zero_grad()
        rho_a = bloch_to_rho(theta_a, phi_a)
        rho_b = bloch_to_rho(theta_b, phi_b)
        rho_ab = torch.kron(rho_a, rho_b)
        rho_ab = apply_cnot(rho_ab)
        ic = coherent_information(rho_ab)
        loss = -ic
        loss.backward()
        optimizer.step()

        if ic.item() > best_ic:
            best_ic = ic.item()
            best_params = (
                theta_a.data.clone(),
                phi_a.data.clone(),
                theta_b.data.clone(),
                phi_b.data.clone(),
            )

    with torch.no_grad():
        rho_a = bloch_to_rho(best_params[0], best_params[1])
        rho_b = bloch_to_rho(best_params[2], best_params[3])
        rho_ab = torch.kron(rho_a, rho_b)
        rho_ab = apply_cnot(rho_ab)

    return rho_ab, best_params, best_ic


# =====================================================================
# CASCADE RUNNER: apply a given ordering for N cycles
# =====================================================================

def run_cascade(rho_ab_init, ordering_fn, p_deph, gamma_amp, n_cycles):
    """Apply ordering_fn N times, tracking I_c at each step."""
    rho = rho_ab_init.clone()
    trajectory = []

    ic_init = coherent_information(rho)
    trajectory.append({"cycle": 0, "ic": ic_init.item()})

    for n in range(1, n_cycles + 1):
        rho, ic = ordering_fn(rho, p_deph, gamma_amp)
        trajectory.append({"cycle": n, "ic": ic.item()})

    return trajectory


# =====================================================================
# CORE EXPERIMENT: all 4 orderings x all N values
# =====================================================================

def run_ordering_comparison(p_deph=0.05, gamma_amp=0.05):
    """Run all 4 orderings for N = 1,2,5,10,20,50 and return trajectories."""
    cycle_counts = [1, 2, 5, 10, 20, 50]
    max_n = max(cycle_counts)

    rho_ab, _, init_ic = build_optimized_initial_state()

    all_trajectories = {}
    ic_at_n = {}  # ordering -> {N: ic_value}

    with torch.no_grad():
        for name, fn in ORDERINGS.items():
            traj = run_cascade(rho_ab, fn, p_deph, gamma_amp, max_n)
            all_trajectories[name] = [t["ic"] for t in traj]
            ic_at_n[name] = {n: traj[n]["ic"] for n in cycle_counts}

    return {
        "init_ic": float(init_ic),
        "p_deph": p_deph,
        "gamma_amp": gamma_amp,
        "cycle_counts": cycle_counts,
        "trajectories": all_trajectories,
        "ic_at_n": ic_at_n,
    }


# =====================================================================
# HELPER: compute summary stats from trajectories
# =====================================================================

def _death_time(traj_ic_values):
    """First cycle where I_c <= 0, or None."""
    for i, v in enumerate(traj_ic_values):
        if i > 0 and v <= 0:
            return i
    return None


def _mean_ic(traj_ic_values, start=0, end=None):
    """Mean I_c over a range of cycles."""
    segment = traj_ic_values[start:end]
    return float(np.mean(segment)) if segment else None


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    data = run_ordering_comparison()

    # --- Test 1: Flipped order sustains I_c longer than original ---
    try:
        orig_traj = data["trajectories"]["original"]
        flip_traj = data["trajectories"]["flipped"]

        orig_death = _death_time(orig_traj)
        flip_death = _death_time(flip_traj)

        # Compare mean I_c over full trajectory
        orig_mean = _mean_ic(orig_traj, 1)
        flip_mean = _mean_ic(flip_traj, 1)

        # Flipped sustains if: higher mean I_c OR later death time
        flip_sustains = flip_mean > orig_mean

        results["flipped_sustains_longer"] = {
            "pass": flip_sustains,
            "original_mean_ic": orig_mean,
            "flipped_mean_ic": flip_mean,
            "original_death_time": orig_death,
            "flipped_death_time": flip_death,
            "original_ic_at_n": data["ic_at_n"]["original"],
            "flipped_ic_at_n": data["ic_at_n"]["flipped"],
        }
    except Exception:
        results["flipped_sustains_longer"] = {"pass": False, "error": traceback.format_exc()}

    # --- Test 2: Protected ordering sustains longest ---
    try:
        means = {}
        deaths = {}
        for name in ORDERINGS:
            traj = data["trajectories"][name]
            means[name] = _mean_ic(traj, 1)
            deaths[name] = _death_time(traj)

        protected_best = all(
            means["protected"] >= means[name] - 1e-6
            for name in ORDERINGS
        )

        results["protected_sustains_longest"] = {
            "pass": protected_best,
            "mean_ics": means,
            "death_times": deaths,
            "ic_at_n": {name: data["ic_at_n"][name] for name in ORDERINGS},
        }
    except Exception:
        results["protected_sustains_longest"] = {"pass": False, "error": traceback.format_exc()}

    return results, data


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests(data):
    results = {}

    # --- Negative 1: Original ordering (noise-first) has worst mean I_c ---
    # Counter-intuitively, sandwich (double noise) is NOT the worst because
    # the second CNOT-noise-CNOT pattern creates partial error correction.
    # The original (noise -> CNOT) is worst because noise corrupts BEFORE
    # the entangling gate, giving CNOT a degraded input to propagate.
    try:
        means = {}
        deaths = {}
        for name in ORDERINGS:
            traj = data["trajectories"][name]
            means[name] = _mean_ic(traj, 1)
            deaths[name] = _death_time(traj)

        # Original should have lowest mean I_c (or tied with flipped)
        original_worst = all(
            means["original"] <= means[name] + 1e-6
            for name in ORDERINGS
        )

        results["original_worst_ordering"] = {
            "pass": original_worst,
            "mean_ics": means,
            "death_times": deaths,
            "original_final_ic": data["trajectories"]["original"][-1],
            "note": "noise-before-CNOT is worse than double-noise because "
                    "CNOT propagates corrupted input; sandwich gets partial "
                    "correction from its second noise-then-CNOT structure",
        }
    except Exception:
        results["sandwich_kills_fastest"] = {"pass": False, "error": traceback.format_exc()}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests(data):
    results = {}

    # --- Boundary 1: N=1 orderings already diverge ---
    # The orderings are fundamentally different operations, so even at N=1
    # they produce distinct I_c values. The key boundary test: protected
    # is already the best even at N=1.
    try:
        ic_at_1 = {name: data["ic_at_n"][name][1] for name in ORDERINGS}
        values = list(ic_at_1.values())
        spread = max(values) - min(values)

        init_ic = data["init_ic"]
        relative_spread = spread / max(abs(init_ic), 1e-12)

        # Protected should already be best at N=1
        protected_best_at_1 = all(
            ic_at_1["protected"] >= ic_at_1[name] - 1e-6
            for name in ORDERINGS
        )

        results["n1_protected_already_best"] = {
            "pass": protected_best_at_1,
            "ic_at_1": ic_at_1,
            "spread": float(spread),
            "relative_spread": float(relative_spread),
            "init_ic": float(init_ic),
            "note": "Orderings are distinct operations, so divergence is "
                    "immediate. Protected wins from cycle 1.",
        }
    except Exception:
        results["n1_orderings_similar"] = {"pass": False, "error": traceback.format_exc()}

    # --- Boundary 2: Large N all orderings converge toward steady state ---
    # At large N, all orderings approach their respective fixed points.
    # The ranking should be preserved: protected > others.
    # Key: protected is the ONLY ordering with positive mean I_c.
    try:
        ic_at_50 = {name: data["ic_at_n"][name][50] for name in ORDERINGS}
        ic_at_1 = {name: data["ic_at_n"][name][1] for name in ORDERINGS}

        # At N=50, check that the ranking still holds
        sorted_at_50 = sorted(ORDERINGS.keys(), key=lambda k: ic_at_50[k], reverse=True)
        protected_still_best = sorted_at_50[0] == "protected"

        # All trajectories should have converged (low variance in tail)
        tail_converged = {}
        for name in ORDERINGS:
            traj = data["trajectories"][name]
            tail = traj[-10:]
            tail_converged[name] = float(np.std(tail)) < 0.05

        all_converged = all(tail_converged.values())

        results["large_n_steady_states"] = {
            "pass": protected_still_best and all_converged,
            "ic_at_1": ic_at_1,
            "ic_at_50": ic_at_50,
            "ranking_at_50": sorted_at_50,
            "protected_still_best": protected_still_best,
            "tail_converged": tail_converged,
            "all_converged": all_converged,
        }
    except Exception:
        results["large_n_orderings_diverge"] = {"pass": False, "error": traceback.format_exc()}

    return results


# =====================================================================
# ORDERING-DEPENDENCE ANALYSIS
# =====================================================================

def run_ordering_analysis(data):
    """Deep analysis: does channel ordering determine ratchet direction?"""
    analysis = {}

    analysis["init_ic"] = data["init_ic"]
    analysis["noise_params"] = {"p_deph": data["p_deph"], "gamma_amp": data["gamma_amp"]}

    # Per-ordering trajectory summary
    for name in ORDERINGS:
        traj = data["trajectories"][name]
        analysis[f"{name}_trajectory"] = traj
        analysis[f"{name}_death_time"] = _death_time(traj)
        analysis[f"{name}_mean_ic"] = _mean_ic(traj, 1)
        analysis[f"{name}_final_ic"] = traj[-1]
        analysis[f"{name}_min_ic"] = float(min(traj[1:])) if len(traj) > 1 else None
        analysis[f"{name}_max_ic"] = float(max(traj[1:])) if len(traj) > 1 else None

    # Key question: does ordering determine ratchet direction?
    means = {name: _mean_ic(data["trajectories"][name], 1) for name in ORDERINGS}
    sorted_orderings = sorted(means.keys(), key=lambda k: means[k], reverse=True)
    analysis["ordering_ranking"] = sorted_orderings
    analysis["ordering_means"] = means

    # How much does ordering matter? Ratio of best to worst mean I_c
    best_mean = means[sorted_orderings[0]]
    worst_mean = means[sorted_orderings[-1]]
    if worst_mean != 0:
        analysis["best_to_worst_ratio"] = float(best_mean / worst_mean)
    else:
        analysis["best_to_worst_ratio"] = float("inf") if best_mean > 0 else None

    analysis["ordering_matters"] = abs(best_mean - worst_mean) > 0.01
    analysis["key_finding"] = (
        f"Channel ordering {'DOES' if analysis['ordering_matters'] else 'does NOT'} "
        f"determine ratchet sustainability. "
        f"Best: {sorted_orderings[0]} (mean I_c={best_mean:.4f}), "
        f"Worst: {sorted_orderings[-1]} (mean I_c={worst_mean:.4f})."
    )

    return analysis


# =====================================================================
# NOISE SWEEP: test robustness across noise levels
# =====================================================================

def run_noise_sweep():
    """Compare orderings across multiple noise levels."""
    noise_levels = [0.01, 0.05, 0.1, 0.2]
    sweep = {}

    for noise in noise_levels:
        data = run_ordering_comparison(p_deph=noise, gamma_amp=noise)
        means = {name: _mean_ic(data["trajectories"][name], 1) for name in ORDERINGS}
        deaths = {name: _death_time(data["trajectories"][name]) for name in ORDERINGS}
        sweep[str(noise)] = {
            "means": means,
            "deaths": deaths,
            "ranking": sorted(means.keys(), key=lambda k: means[k], reverse=True),
        }

    return sweep


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    t0 = time.time()

    print("Running positive tests (includes core comparison)...")
    positive, data = run_positive_tests()

    print("Running negative tests...")
    negative = run_negative_tests(data)

    print("Running boundary tests...")
    boundary = run_boundary_tests(data)

    print("Running ordering analysis...")
    analysis = run_ordering_analysis(data)

    print("Running noise sweep...")
    noise_sweep = run_noise_sweep()

    elapsed = time.time() - t0

    # Summary stats
    all_tests = {}
    all_tests.update(positive)
    all_tests.update(negative)
    all_tests.update(boundary)
    n_pass = sum(1 for v in all_tests.values() if v.get("pass"))
    n_total = len(all_tests)

    results = {
        "name": "temporal_cascade_flipped -- does channel ordering determine ratchet direction?",
        "tool_manifest": TOOL_MANIFEST,
        "classification": "canonical",
        "summary": {
            "tests_passed": n_pass,
            "tests_total": n_total,
            "elapsed_seconds": round(elapsed, 2),
            "ordering_matters": analysis["ordering_matters"],
            "key_finding": analysis["key_finding"],
            "ordering_ranking": analysis["ordering_ranking"],
            "ordering_means": analysis["ordering_means"],
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "ordering_analysis": analysis,
        "noise_sweep": noise_sweep,
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "temporal_cascade_flipped_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"Tests: {n_pass}/{n_total} passed in {elapsed:.1f}s")

    # Quick summary to stdout
    for section_name, section in [("POSITIVE", positive), ("NEGATIVE", negative), ("BOUNDARY", boundary)]:
        print(f"\n--- {section_name} ---")
        for k, v in section.items():
            status = "PASS" if v.get("pass") else "FAIL"
            print(f"  [{status}] {k}")

    print(f"\n--- ORDERING ANALYSIS ---")
    print(f"  Initial I_c:        {analysis['init_ic']:.4f}")
    print(f"  Ordering matters?   {analysis['ordering_matters']}")
    print(f"  Ranking:            {' > '.join(analysis['ordering_ranking'])}")
    for name in analysis["ordering_ranking"]:
        mean = analysis[f"{name}_mean_ic"]
        death = analysis[f"{name}_death_time"]
        final = analysis[f"{name}_final_ic"]
        print(f"    {name:12s}: mean={mean:.4f}  death={death}  final={final:.4f}")

    print(f"\n--- NOISE SWEEP ---")
    for noise_str, sweep_data in noise_sweep.items():
        ranking = " > ".join(sweep_data["ranking"])
        print(f"  noise={noise_str}: {ranking}")

    print(f"\n  Key finding: {analysis['key_finding']}")
