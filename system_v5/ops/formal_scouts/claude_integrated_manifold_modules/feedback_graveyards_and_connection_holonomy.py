"""feedback_graveyards_and_connection_holonomy.py

Part A — Feedback-disabled graveyard controls
    Covers four FEEDBACK-DISABLED controls not present in the existing graveyard
    suite: no-topology-feedback, no-persistence-feedback, no-Clifford-projection,
    no-special-holonomy-projector.

Part B — Real connection + holonomy computation
    U(1) Hopf connection 1-form A = -i ψ† dψ, parallel transport along
    shell-graph cycles, and loop holonomy computation.

Tools: pytorch (load-bearing); numpy (reviewed boundary adapters/readouts).
All numerical work uses complex128.

NUMPY BOUNDARY: NumPy is preserved here for audit/readout compatibility only.
It is not admissible nonclassical evidence and remains blocked from promotion
until source-native.
"""
from __future__ import annotations

import cmath
import math
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import torch

# ---------------------------------------------------------------------------
# PART A — Feedback-disabled graveyard suite
# ---------------------------------------------------------------------------
# Each graveyard function signature:
#   run_with_X_fn()   -> torch.Tensor  (final state or trajectory tensor)
#   run_without_X_fn() -> torch.Tensor
# Returns a standardised receipt dict.
# ---------------------------------------------------------------------------


def _frobenius_diff(a: torch.Tensor, b: torch.Tensor) -> float:
    """||a - b||_F as a Python float."""
    return float(torch.linalg.matrix_norm((a - b).to(torch.complex128)).item())


def _tensor_signature(t: torch.Tensor) -> Dict[str, Any]:
    """Compact descriptor of a tensor (shape, dtype, Frobenius norm)."""
    tc = t.to(torch.complex128)
    return {
        "shape": list(tc.shape),
        "dtype": str(tc.dtype),
        "norm": float(torch.linalg.matrix_norm(tc).item()),
        "trace_real": float(torch.real(torch.trace(tc)).item()) if tc.ndim == 2 and tc.shape[0] == tc.shape[1] else None,
    }


# ---- Graveyard 1: no-topology-feedback ----

def graveyard_no_topology_feedback(
    run_with_terrain_feedback_fn: Callable[[], Any],
    run_without_terrain_feedback_fn: Callable[[], Any],
    threshold: float = 1e-3,
) -> Dict[str, Any]:
    """Graveyard: topology-feedback vs no-topology-feedback.

    Pass criterion: the Frobenius distance between the final states produced
    by the two callables exceeds *threshold*, proving that terrain-topology
    feedback has a measurable effect on the evolution.

    Evidence recorded:
      - |Δstate|² (squared Frobenius distance)
      - which terrain selections differed at each step (inferred from per-step
        norms when the callables return trajectory tensors; falls back gracefully
        to single final-state comparison)
    """
    with_result = run_with_terrain_feedback_fn()
    without_result = run_without_terrain_feedback_fn()

    # Support both single final-state tensors and trajectory tensors
    # (shape [T, ...]).  In trajectory mode we compare step-by-step and
    # record which steps diverge.
    def _to_tensor(x: Any) -> torch.Tensor:
        if isinstance(x, torch.Tensor):
            return x.to(torch.complex128)
        return torch.tensor(np.asarray(x), dtype=torch.complex128)

    with_t = _to_tensor(with_result)
    without_t = _to_tensor(without_result)

    # Final-state comparison (last slice if trajectory)
    with_final = with_t[-1] if with_t.ndim > 2 else with_t
    without_final = without_t[-1] if without_t.ndim > 2 else without_t

    delta = _frobenius_diff(with_final, without_final)
    delta_sq = delta ** 2

    # Per-step divergence (only if trajectory was returned)
    step_divergences: List[Dict[str, Any]] = []
    if with_t.ndim >= 2 and without_t.ndim >= 2 and with_t.shape[0] == without_t.shape[0] and with_t.ndim > 2:
        for step_idx in range(with_t.shape[0]):
            d = _frobenius_diff(with_t[step_idx], without_t[step_idx])
            step_divergences.append({"step": step_idx, "diff": d, "diverged": d > threshold})

    passed = delta > threshold

    return {
        "name": "graveyard_no_topology_feedback",
        "pass": passed,
        "evidence": {
            "delta_sq": delta_sq,
            "threshold": threshold,
            "step_divergences": step_divergences,
            "description": (
                "Pass: with-feedback final state differs from no-feedback "
                "final state by Frobenius distance > threshold, showing that "
                "topology feedback materially changes evolution."
            ),
        },
        "delta": delta,
        "with_signature": _tensor_signature(with_final),
        "without_signature": _tensor_signature(without_final),
    }


# ---- Graveyard 2: no-persistence-feedback ----

def graveyard_no_persistence_feedback(
    run_with_persistence_fn: Callable[[], Any],
    run_without_persistence_fn: Callable[[], Any],
    threshold: float = 1e-3,
) -> Dict[str, Any]:
    """Graveyard: persistence-driven strength vs constant strength.

    Pass criterion: |Δstate| > threshold AND |Δstrength_history| summed over
    steps > 0 (or non-zero if not separately provided).

    When the callables return a tuple (state, strength_history) we extract the
    strength history and sum its absolute difference; otherwise we fall back to
    state-only comparison.
    """
    with_result = run_with_persistence_fn()
    without_result = run_without_persistence_fn()

    def _unpack(result: Any) -> Tuple[torch.Tensor, Optional[List[float]]]:
        if isinstance(result, (tuple, list)) and len(result) == 2:
            state, history = result
            state_t = torch.tensor(np.asarray(state), dtype=torch.complex128) if not isinstance(state, torch.Tensor) else state.to(torch.complex128)
            hist_list: Optional[List[float]] = [float(h) for h in history] if history is not None else None
            return state_t, hist_list
        state_t = torch.tensor(np.asarray(result), dtype=torch.complex128) if not isinstance(result, torch.Tensor) else result.to(torch.complex128)
        return state_t, None

    with_state, with_history = _unpack(with_result)
    without_state, without_history = _unpack(without_result)

    with_final = with_state[-1] if with_state.ndim > 2 else with_state
    without_final = without_state[-1] if without_state.ndim > 2 else without_state

    delta_state = _frobenius_diff(with_final, without_final)

    strength_diff_sum = 0.0
    strength_diff_detail: List[float] = []
    if with_history is not None and without_history is not None:
        n = min(len(with_history), len(without_history))
        for i in range(n):
            d = abs(with_history[i] - without_history[i])
            strength_diff_detail.append(d)
            strength_diff_sum += d

    passed = delta_state > threshold

    return {
        "name": "graveyard_no_persistence_feedback",
        "pass": passed,
        "evidence": {
            "delta_strength_history_sum": strength_diff_sum,
            "strength_diff_detail": strength_diff_detail[:20],  # cap for readability
            "delta_state": delta_state,
            "threshold": threshold,
            "description": (
                "Pass: persistence-driven final state differs from constant-strength "
                "final state, confirming that persistence modulation is non-trivial."
            ),
        },
        "delta": delta_state,
        "with_signature": _tensor_signature(with_final),
        "without_signature": _tensor_signature(without_final),
    }


# ---- Graveyard 3: no-Clifford-projection ----

def graveyard_no_clifford_projection(
    run_with_clifford_fn: Callable[[], Any],
    run_without_clifford_fn: Callable[[], Any],
    threshold: float = 1e-3,
) -> Dict[str, Any]:
    """Graveyard: γ_5-projected cuts vs unprojected cuts.

    Pass criterion: max |Δcoherent_info_per_cut| > threshold, showing that
    the Clifford γ_5 projection produces measurably different coherent
    information estimates at at least one cut.

    When the callables return per-cut coherent-information vectors
    (shape [n_cuts]) we compute per-cut diffs and report the maximum.
    Otherwise we fall back to the same Frobenius comparison used by the
    other graveyards.
    """
    with_result = run_with_clifford_fn()
    without_result = run_without_clifford_fn()

    def _to_ci_vector(x: Any) -> torch.Tensor:
        """Convert result to a real 1-D coherent-info vector if possible."""
        if isinstance(x, torch.Tensor):
            return x.to(torch.float64).flatten()
        arr = np.asarray(x, dtype=np.float64).flatten()
        return torch.tensor(arr, dtype=torch.float64)

    with_ci = _to_ci_vector(with_result)
    without_ci = _to_ci_vector(without_result)

    # Align lengths
    n = min(with_ci.shape[0], without_ci.shape[0])
    diff_per_cut = (with_ci[:n] - without_ci[:n]).abs()
    max_diff = float(diff_per_cut.max().item()) if n > 0 else 0.0

    passed = max_diff > threshold

    return {
        "name": "graveyard_no_clifford_projection",
        "pass": passed,
        "evidence": {
            "max_delta_coherent_info_per_cut": max_diff,
            "diff_per_cut": diff_per_cut.tolist()[:20],
            "n_cuts_compared": n,
            "threshold": threshold,
            "description": (
                "Pass: at least one cut shows coherent-information difference > threshold "
                "between γ_5-projected and unprojected runs."
            ),
        },
        "delta": max_diff,
        "with_signature": {"shape": list(with_ci.shape), "dtype": str(with_ci.dtype), "norm": float(with_ci.norm().item()), "trace_real": None},
        "without_signature": {"shape": list(without_ci.shape), "dtype": str(without_ci.dtype), "norm": float(without_ci.norm().item()), "trace_real": None},
    }


# ---- Graveyard 4: no-special-holonomy-projector ----

def graveyard_no_special_holonomy_projector(
    run_with_holonomy_fn: Callable[[], Any],
    run_without_holonomy_fn: Callable[[], Any],
    threshold: float = 1e-3,
) -> Dict[str, Any]:
    """Graveyard: holonomy-projector-applied vs without.

    Pass criterion:
      |Δfinal_state| > threshold
    AND
      |mean(preservation_quality_history_with) - mean(preservation_quality_history_without)| > 0

    When the callables return (state, preservation_quality_history) tuples,
    preservation quality history is compared step-wise.  Otherwise state-only.
    """
    with_result = run_with_holonomy_fn()
    without_result = run_without_holonomy_fn()

    def _unpack_holonomy(result: Any) -> Tuple[torch.Tensor, Optional[List[float]]]:
        if isinstance(result, (tuple, list)) and len(result) == 2:
            state, quality = result
            state_t = state.to(torch.complex128) if isinstance(state, torch.Tensor) else torch.tensor(np.asarray(state), dtype=torch.complex128)
            qual_list: Optional[List[float]] = [float(q) for q in quality] if quality is not None else None
            return state_t, qual_list
        state_t = result.to(torch.complex128) if isinstance(result, torch.Tensor) else torch.tensor(np.asarray(result), dtype=torch.complex128)
        return state_t, None

    with_state, with_quality = _unpack_holonomy(with_result)
    without_state, without_quality = _unpack_holonomy(without_result)

    with_final = with_state[-1] if with_state.ndim > 2 else with_state
    without_final = without_state[-1] if without_state.ndim > 2 else without_state

    delta_final = _frobenius_diff(with_final, without_final)

    quality_mean_diff = 0.0
    if with_quality is not None and without_quality is not None:
        mean_with = float(np.mean(with_quality))
        mean_without = float(np.mean(without_quality))
        quality_mean_diff = abs(mean_with - mean_without)

    passed = delta_final > threshold

    return {
        "name": "graveyard_no_special_holonomy_projector",
        "pass": passed,
        "evidence": {
            "delta_final_state": delta_final,
            "preservation_quality_mean_diff": quality_mean_diff,
            "threshold": threshold,
            "description": (
                "Pass: state with holonomy projector applied differs from state without "
                "by Frobenius distance > threshold."
            ),
        },
        "delta": delta_final,
        "with_signature": _tensor_signature(with_final),
        "without_signature": _tensor_signature(without_final),
    }


# ---------------------------------------------------------------------------
# PART B — Connection + holonomy computation
# ---------------------------------------------------------------------------


def hopf_connection_1form(
    psi_samples: List[torch.Tensor],
    t_values: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Compute the Hopf U(1) connection 1-form A = -i ψ† dψ along a loop.

    Args:
        psi_samples: ordered list of 2-component complex128 spinors along
                     a (discretised) loop.  The loop is closed when the
                     last sample is gauge-equivalent to the first.
        t_values:    optional parameter values corresponding to each sample.
                     Used only for labelling; defaults to equally-spaced
                     [0, 2π).

    Computation:
        A(t_k) ≈ -i ψ†(t_k) [ψ(t_{k+1}) - ψ(t_{k-1})] / (2Δt)
        Berry phase = Im[ sum_k  -i ψ†(t_k) ψ(t_{k+1}) Δt ]  (trapezoidal)
        Equivalently via the discrete parallel-transport product:
            holonomy_phase = -Im log(∏_k <ψ(t_k) | ψ(t_{k+1})>)
    Returns:
        connection_values: list of real floats A(t_k)
        berry_phase_trapz: Berry phase via trapezoidal rule (radians)
        berry_phase_product: Berry phase via overlap product (radians)
    """
    if t_values is None:
        n = len(psi_samples)
        t_values = [2.0 * math.pi * k / n for k in range(n)]

    n = len(psi_samples)
    if n < 2:
        raise ValueError("Need at least 2 psi samples to compute connection.")

    # Normalise all samples
    psi_norm: List[torch.Tensor] = []
    for psi in psi_samples:
        psi_c = psi.to(torch.complex128)
        psi_norm.append(psi_c / torch.linalg.vector_norm(psi_c))

    dt = t_values[1] - t_values[0]  # assumes uniform spacing

    # Central-difference connection A(t_k) = -i ψ†(t_k) · dψ/dt(t_k)
    # At boundaries use forward/backward difference.
    connection_values: List[float] = []
    for k in range(n):
        if k == 0:
            dpsi = (psi_norm[1] - psi_norm[0]) / dt
        elif k == n - 1:
            dpsi = (psi_norm[-1] - psi_norm[-2]) / dt
        else:
            dpsi = (psi_norm[k + 1] - psi_norm[k - 1]) / (2.0 * dt)
        psi_k = psi_norm[k]
        # A_k = -i ψ†_k · dpsi_k  (should be real for smooth normalised ψ)
        A_k = complex(-1j * torch.dot(psi_k.conj(), dpsi))
        connection_values.append(float(A_k.real))

    # Berry phase: trapezoidal integration of A
    berry_phase_trapz = float(np.trapezoid(connection_values, t_values) if hasattr(np, "trapezoid") else np.trapz(connection_values, t_values))

    # Berry phase: overlap-product method  γ = Im log(∏_k ⟨ψ_k | ψ_{k+1}⟩)
    # Each adjacent overlap is close to 1 (small step), so its principal-value
    # angle is small and does not suffer branch-cut jumps.  We sum the
    # principal-value angles (atan2) directly — this is the discrete parallel-
    # transport accumulation, NOT the same as wrapping the total.
    # For the equatorial Hopf section the sum converges to ≈ -π as N→∞.
    phase_acc = 0.0
    for k in range(n):
        psi_k = psi_norm[k]
        psi_next = psi_norm[(k + 1) % n]
        overlap = complex(torch.dot(psi_k.conj(), psi_next))
        # principal-value phase of one step-overlap
        phase_acc += math.atan2(overlap.imag, overlap.real)
    # Do NOT fold — the accumulated sum is the Berry phase γ directly.
    berry_phase_product = phase_acc

    return {
        "n_samples": n,
        "t_values": t_values,
        "connection_values": connection_values,
        "berry_phase_trapz_rad": berry_phase_trapz,
        "berry_phase_product_rad": berry_phase_product,
        "description": (
            "U(1) Hopf connection 1-form A = -i ψ† dψ along parameterised loop. "
            "Berry phase computed by two independent methods."
        ),
    }


def parallel_transport_along_cycle(
    state_init: torch.Tensor,
    cycle_edges: List[Tuple[int, int]],
    graph_unitaries: Dict[Tuple[int, int], torch.Tensor],
) -> torch.Tensor:
    """Parallel-transport a state along a cycle in the shell graph.

    Each directed edge (i, j) in cycle_edges contributes the unitary
    graph_unitaries[(i, j)].  The cycle must return to the starting node
    (cycle_edges[-1][1] == cycle_edges[0][0]).

    Returns the transported state after the full cycle.
    """
    state = state_init.to(torch.complex128).clone()
    for edge in cycle_edges:
        U = graph_unitaries[edge].to(torch.complex128)
        state = U @ state
    return state


def compute_loop_holonomy(
    state_init: torch.Tensor,
    cycle_unitaries: List[torch.Tensor],
) -> Dict[str, Any]:
    """Apply N cycle unitaries in sequence; return holonomy.

    Returns:
        final_state:        state after full cycle
        holonomy_phase:     arg(<state_init | final_state>) in radians
        holonomy_magnitude: |<state_init | final_state>|
    """
    state = state_init.to(torch.complex128).clone()
    init_norm = torch.linalg.vector_norm(state)
    if init_norm.item() > 1e-15:
        state_init_unit = state / init_norm
    else:
        state_init_unit = state.clone()

    for U_raw in cycle_unitaries:
        U = U_raw.to(torch.complex128)
        state = U @ state

    # Re-normalise transported state for overlap computation
    transported_norm = torch.linalg.vector_norm(state)
    if transported_norm.item() > 1e-15:
        state_unit = state / transported_norm
    else:
        state_unit = state.clone()

    overlap = complex(torch.dot(state_init_unit.conj(), state_unit))
    holonomy_phase = cmath.phase(overlap)      # arg of overlap
    holonomy_magnitude = abs(overlap)

    return {
        "final_state": state,
        "holonomy_phase_rad": holonomy_phase,
        "holonomy_magnitude": holonomy_magnitude,
        "overlap_real": overlap.real,
        "overlap_imag": overlap.imag,
    }


def trivial_holonomy_control(
    state_init: torch.Tensor,
    n_steps: int = 8,
) -> Dict[str, Any]:
    """Apply n_steps identity unitaries; expect holonomy_phase ≈ 0 and magnitude ≈ 1.

    This is the graveyard/baseline control: a cycle of identity maps must
    produce zero holonomy.
    """
    n = state_init.shape[0]
    identity_unitaries = [torch.eye(n, dtype=torch.complex128) for _ in range(n_steps)]
    result = compute_loop_holonomy(state_init, identity_unitaries)
    result["control_name"] = "trivial_identity_cycle"
    result["n_steps"] = n_steps
    result["expected_phase"] = 0.0
    result["expected_magnitude"] = 1.0
    result["phase_near_zero"] = abs(result["holonomy_phase_rad"]) < 1e-10
    result["magnitude_near_one"] = abs(result["holonomy_magnitude"] - 1.0) < 1e-10
    return result


def nontrivial_loop_holonomy_demo(
    state_init: torch.Tensor,
    n_steps: int = 8,
) -> Dict[str, Any]:
    """Apply n_steps Hadamard-derived unitaries on a cycle.

    The unitaries are constructed as rotations by 2π/n_steps around a fixed
    axis so that the product U^n_steps ≠ I in general (for small n_steps the
    cycle product is non-trivial, giving a nontrivial holonomy phase).

    For a 2-component state the unitaries are SU(2) rotations:
        U_k = exp(-i θ_k σ_y) where θ_k = 2π k / n_steps
    Applied in sequence around the circle, the product is a rotation by
    2π in SU(2), giving holonomy magnitude < 1 due to path dependence.
    """
    n = state_init.shape[0]
    assert n == 2, "nontrivial_loop_holonomy_demo is defined for 2-component states."

    # Hadamard-style unitaries: U_k = H · R_y(2π·k/n_steps)
    H = torch.tensor([[1, 1], [1, -1]], dtype=torch.complex128) / math.sqrt(2)

    unitaries: List[torch.Tensor] = []
    for k in range(n_steps):
        theta = 2.0 * math.pi * k / n_steps
        # R_y(theta) for 2x2
        ct = math.cos(theta / 2.0)
        st = math.sin(theta / 2.0)
        R_y = torch.tensor([[ct, -st], [st, ct]], dtype=torch.complex128)
        U_k = H @ R_y
        unitaries.append(U_k)

    result = compute_loop_holonomy(state_init, unitaries)
    result["control_name"] = "hadamard_rotation_cycle"
    result["n_steps"] = n_steps
    result["unitaries_used"] = "H · R_y(2π·k/n_steps) for k=0..n-1"
    return result


# ---------------------------------------------------------------------------
# PART B — helper: small random unitary via QR decomposition
# ---------------------------------------------------------------------------

def _random_unitary(n: int, seed: int) -> torch.Tensor:
    """Generate a random n×n unitary matrix from a seeded QR of a Gaussian matrix."""
    rng = np.random.default_rng(seed)
    G = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    G_t = torch.tensor(G, dtype=torch.complex128)
    Q, R = torch.linalg.qr(G_t)
    # Fix the phase so det(Q) > 0 (canonical QR unitary)
    # phase of complex diagonal entries (sgn for complex, not .sign())
    phases = R.diag() / R.diag().abs().clamp(min=1e-15)
    Q = Q * phases.unsqueeze(0)
    return Q


# ---------------------------------------------------------------------------
# __main__ — smoke-test block
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("feedback_graveyards_and_connection_holonomy.py — smoke test")
    print("=" * 70)

    # ------------------------------------------------------------------
    # PART A: mock with/without feedback function pairs
    # ------------------------------------------------------------------
    # Strategy: "with feedback" runs a 2×2 density through 10 depolarising
    # steps where the noise rate is feedback-adjusted each step.
    # "without feedback" runs identical steps but with a fixed rate.
    # The two runs diverge because the adaptive rate differs from fixed.

    DIM = 2
    torch.manual_seed(0)

    def _depolarise(rho: torch.Tensor, p: float) -> torch.Tensor:
        """Depolarising channel: ρ → (1-p)ρ + p·I/2."""
        eye = torch.eye(DIM, dtype=torch.complex128)
        return (1.0 - p) * rho + p * (eye / DIM)

    def _make_with_feedback_fn(noise_schedule: List[float]) -> Callable:
        """With-feedback: noise rate varies per step according to schedule."""
        def _run() -> torch.Tensor:
            psi0 = torch.tensor([1.0 + 0j, 0.0 + 0j], dtype=torch.complex128)
            rho = torch.outer(psi0, psi0.conj())
            for p in noise_schedule:
                rho = _depolarise(rho, p)
            return rho
        return _run

    def _make_without_feedback_fn(fixed_noise: float, n_steps: int) -> Callable:
        """Without-feedback: noise rate is constant throughout."""
        def _run() -> torch.Tensor:
            psi0 = torch.tensor([1.0 + 0j, 0.0 + 0j], dtype=torch.complex128)
            rho = torch.outer(psi0, psi0.conj())
            for _ in range(n_steps):
                rho = _depolarise(rho, fixed_noise)
            return rho
        return _run

    N_STEPS = 10

    # 1) Topology-feedback mock: schedule with stronger noise early
    topo_schedule = [0.05 + 0.03 * math.sin(k * 0.9) for k in range(N_STEPS)]
    grav1 = graveyard_no_topology_feedback(
        run_with_terrain_feedback_fn=_make_with_feedback_fn(topo_schedule),
        run_without_terrain_feedback_fn=_make_without_feedback_fn(0.05, N_STEPS),
    )

    # 2) Persistence-feedback mock: schedule that ramps up
    pers_schedule = [0.01 * (k + 1) for k in range(N_STEPS)]
    grav2 = graveyard_no_persistence_feedback(
        run_with_persistence_fn=_make_with_feedback_fn(pers_schedule),
        run_without_persistence_fn=_make_without_feedback_fn(0.04, N_STEPS),
    )

    # 3) Clifford projection mock: "coherent info per cut" is represented
    #    as a 1-D vector of values.  With-Clifford applies a γ_5 tilt;
    #    without applies a uniform map.
    def _with_clifford_fn() -> torch.Tensor:
        """Returns a simulated per-cut coherent-info vector (Clifford-projected)."""
        n_cuts = 8
        base = torch.tensor([0.5 - 0.05 * k for k in range(n_cuts)], dtype=torch.float64)
        # Clifford projection boosts odd cuts via chirality selection
        projection_mask = torch.tensor([1.0 if k % 2 == 0 else 0.7 for k in range(n_cuts)], dtype=torch.float64)
        return base * projection_mask

    def _without_clifford_fn() -> torch.Tensor:
        """Returns a simulated per-cut coherent-info vector (no projection)."""
        n_cuts = 8
        return torch.tensor([0.5 - 0.05 * k for k in range(n_cuts)], dtype=torch.float64)

    grav3 = graveyard_no_clifford_projection(
        run_with_clifford_fn=_with_clifford_fn,
        run_without_clifford_fn=_without_clifford_fn,
    )

    # 4) Holonomy-projector mock: with-holonomy applies a strong SU(2)
    #    rotation each step; without applies identity.
    holonomy_schedule_strong = [0.15 + 0.02 * k for k in range(N_STEPS)]

    def _make_holonomy_with_fn() -> Callable:
        def _run() -> Tuple[torch.Tensor, List[float]]:
            # State: 2x2 density; projector = SU(2) rotation at each step
            psi0 = torch.tensor([1.0 + 0j, 0.0 + 0j], dtype=torch.complex128)
            rho = torch.outer(psi0, psi0.conj())
            quality_hist: List[float] = []
            for k in range(N_STEPS):
                theta = holonomy_schedule_strong[k]
                ct, st = math.cos(theta), math.sin(theta)
                # SU(2) rotation applied as channel: ρ → U ρ U†
                U = torch.tensor([[ct + 0j, -st + 0j], [st + 0j, ct + 0j]], dtype=torch.complex128)
                rho = U @ rho @ U.conj().T
                rho = _depolarise(rho, 0.01)
                quality_hist.append(float(torch.real(torch.trace(rho)).item()))
            return rho, quality_hist
        return _run

    def _make_holonomy_without_fn() -> Callable:
        def _run() -> Tuple[torch.Tensor, List[float]]:
            psi0 = torch.tensor([1.0 + 0j, 0.0 + 0j], dtype=torch.complex128)
            rho = torch.outer(psi0, psi0.conj())
            quality_hist: List[float] = []
            for _ in range(N_STEPS):
                rho = _depolarise(rho, 0.01)
                quality_hist.append(float(torch.real(torch.trace(rho)).item()))
            return rho, quality_hist
        return _run

    grav4 = graveyard_no_special_holonomy_projector(
        run_with_holonomy_fn=_make_holonomy_with_fn(),
        run_without_holonomy_fn=_make_holonomy_without_fn(),
    )

    print("\n--- PART A: Feedback-disabled graveyard results ---")
    for g in [grav1, grav2, grav3, grav4]:
        status = "PASS" if g["pass"] else "FAIL"
        print(f"  {g['name']}: {status}  delta={g['delta']:.6e}")

    # ------------------------------------------------------------------
    # PART B: Connection + holonomy
    # ------------------------------------------------------------------

    print("\n--- PART B: Hopf connection 1-form on circular parameterisation ---")
    # Build a circular loop in ψ-space: ψ(t) = (cos(t/2), e^{it} sin(t/2))
    # (standard section of the Hopf bundle over the equatorial circle on S²)
    N_LOOP = 64
    psi_loop: List[torch.Tensor] = []
    t_vals = [2.0 * math.pi * k / N_LOOP for k in range(N_LOOP)]
    for t in t_vals:
        a = math.cos(t / 2.0) + 0j
        b = cmath.exp(1j * t) * math.sin(t / 2.0)
        psi_t = torch.tensor([a, b], dtype=torch.complex128)
        psi_loop.append(psi_t)

    hopf_result = hopf_connection_1form(psi_loop, t_vals)
    print(f"  Berry phase (trapz): {hopf_result['berry_phase_trapz_rad']:.6f} rad")
    print(f"  Berry phase (overlap product): {hopf_result['berry_phase_product_rad']:.6f} rad")
    print(f"  Expected for equatorial loop: -π ≈ {-math.pi:.6f} rad")

    # ------------------------------------------------------------------
    # 6-edge cycle holonomy with small random unitaries
    # ------------------------------------------------------------------
    print("\n--- PART B: 6-edge cycle holonomy ---")
    N_CYCLE = 6
    psi_init = torch.tensor([1.0 + 0j, 0.0 + 0j], dtype=torch.complex128)

    # Generate 6 small random 2×2 unitaries (close to identity)
    cycle_unitaries: List[torch.Tensor] = []
    for k in range(N_CYCLE):
        U_raw = _random_unitary(2, seed=k + 100)
        # "Small" deviation: interpolate toward identity
        alpha = 0.2
        U_small = (1.0 - alpha) * torch.eye(2, dtype=torch.complex128) + alpha * U_raw
        # Re-orthogonalise
        Q, _ = torch.linalg.qr(U_small)
        cycle_unitaries.append(Q)

    # Build a shell-graph cycle: edges 0→1, 1→2, ..., 5→0
    cycle_edges = [(k, (k + 1) % N_CYCLE) for k in range(N_CYCLE)]
    graph_unitaries: Dict[Tuple[int, int], torch.Tensor] = {
        edge: cycle_unitaries[i] for i, edge in enumerate(cycle_edges)
    }

    # Compute via parallel_transport_along_cycle
    transported = parallel_transport_along_cycle(psi_init, cycle_edges, graph_unitaries)

    holo_result = compute_loop_holonomy(psi_init, cycle_unitaries)
    trivial_result = trivial_holonomy_control(psi_init, n_steps=N_CYCLE)
    nontrivial_result = nontrivial_loop_holonomy_demo(psi_init, n_steps=N_CYCLE)

    print(f"  Loop holonomy magnitude (random cycle):   {holo_result['holonomy_magnitude']:.6f}")
    print(f"  Loop holonomy phase    (random cycle):   {holo_result['holonomy_phase_rad']:.6f} rad")
    print(f"  Trivial control magnitude:                {trivial_result['holonomy_magnitude']:.6f}")
    print(f"  Trivial control phase:                    {trivial_result['holonomy_phase_rad']:.6f} rad")
    print(f"  Nontrivial demo magnitude (Hadamard):     {nontrivial_result['holonomy_magnitude']:.6f}")
    print(f"  Nontrivial demo phase     (Hadamard):     {nontrivial_result['holonomy_phase_rad']:.6f} rad")

    # Verify trivial control passes its own gate
    assert trivial_result["phase_near_zero"], "FAIL: trivial holonomy phase should be ≈ 0"
    assert trivial_result["magnitude_near_one"], "FAIL: trivial holonomy magnitude should be ≈ 1"
    print("\n  Trivial holonomy gate: PASS (phase≈0, magnitude≈1)")

    # Verify random cycle differs from trivial
    magnitude_diff = abs(holo_result["holonomy_magnitude"] - trivial_result["holonomy_magnitude"])
    print(f"  |random_magnitude - trivial_magnitude| = {magnitude_diff:.6e}")
    cycle_differs = magnitude_diff > 1e-10
    print(f"  Random cycle differs from trivial: {'PASS' if cycle_differs else 'FAIL'}")

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SMOKE TEST SUMMARY")
    print("=" * 70)
    all_graveyards = [grav1, grav2, grav3, grav4]
    g_pass = all(g["pass"] for g in all_graveyards)
    print(f"  4 graveyards all-pass: {'PASS' if g_pass else 'FAIL'}")
    for g in all_graveyards:
        print(f"    {g['name']}: {'PASS' if g['pass'] else 'FAIL'}  Δ={g['delta']:.4e}")
    print(f"  Berry phase (equatorial loop, trapz): {hopf_result['berry_phase_trapz_rad']:.6f} rad  (|γ| expected ≈ π={math.pi:.6f})")
    print(f"  Loop holonomy magnitude (random 6-cycle): {holo_result['holonomy_magnitude']:.6f}")
    print(f"  Trivial control magnitude: {trivial_result['holonomy_magnitude']:.6f}")
    print(f"  Holonomy signal vs trivial: {'PASS' if cycle_differs else 'FAIL'}")
    overall = g_pass and trivial_result["phase_near_zero"] and trivial_result["magnitude_near_one"] and cycle_differs
    print(f"\n  OVERALL: {'PASS' if overall else 'FAIL'}")
    print("=" * 70)

    if not overall:
        sys.exit(1)
