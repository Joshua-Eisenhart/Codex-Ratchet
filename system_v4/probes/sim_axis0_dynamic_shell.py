#!/usr/bin/env python3
"""
Axis 0 Dynamic Shell Discrimination Sim
========================================
Tests whether a discrete pulsing shell model provides measurable
discrimination beyond a static shell partition.

Three lanes per PROTO_RATCHET_AXIS0_DYNAMIC_SHELL_SIM_PROGRAM.md:

  Lane A — Dynamic shell vs static shell
    Does moving the cut shell produce nontrivial changes in shell-cut
    observables that the static version misses?

  Lane B — Discrete finite ticks vs continuum-style gradation
    Do finite shell differences already carry the bridge information,
    or is a fake continuum secretly required?

  Lane C — Multi-layer tensor reading vs single-cut bookkeeping
    Does reading MI/Ic across stacked shell layers sharpen discrimination
    beyond a single cut?

Shell model:
  The torus latitude eta in [0, pi/2] serves as the shell radius.
  Shell levels: N discrete eta values (the "shell ladder").
  Cut at shell level k: partition into sub-ladder [0..k] vs [k+1..N-1].
  Static shell: cut fixed at shell level k0 = N//2 throughout.
  Dynamic shell: cut position updates by ±1 each tick according to a
    discrete rule (outward if MI increasing, inward otherwise).
  The shell-cut observable is MI and Ic measured across the bipartition.

Carrier:
  Same engine as Phase4/5 — GeometricEngine on Hopf tori.
  History trajectory from one full engine cycle per torus type.
  Shell-cut applied to the trajectory density matrices.
"""

from __future__ import annotations
import json, os, sys
from datetime import UTC, datetime
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER

TORUS_CONFIGS = [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]
N_SHELL_LEVELS = 8  # discrete shell ladder size
# Shell levels as thresholds on ax0_torus_entropy ∈ [0, 1]
SHELL_ETA_LEVELS = np.linspace(0.05, 0.95, N_SHELL_LEVELS)
BELL_PSI_MINUS = np.outer(
    np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2),
    np.array([0, 1, -1, 0], dtype=complex).conj() / np.sqrt(2),
)

EPS = 1e-12


# --------------------------------------------------------------------------- #
# Quantum information utilities                                                #
# --------------------------------------------------------------------------- #

def vne(rho: np.ndarray) -> float:
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0


def ptr_B(r: np.ndarray) -> np.ndarray:
    return np.trace(r.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def ptr_A(r: np.ndarray) -> np.ndarray:
    return np.trace(r.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def mi_val(rho_AB: np.ndarray) -> float:
    return max(0.0, vne(ptr_B(rho_AB)) + vne(ptr_A(rho_AB)) - vne(rho_AB))


def ic_val(rho_AB: np.ndarray) -> float:
    return vne(ptr_A(rho_AB)) - vne(rho_AB)


# --------------------------------------------------------------------------- #
# Shell partition utilities                                                    #
# --------------------------------------------------------------------------- #

def shell_bipartition_rho(history: list[dict], shell_level: int) -> np.ndarray:
    """
    Build a bipartite density matrix from a trajectory split at shell_level.

    Interior = trajectory steps whose torus eta is below
               SHELL_ETA_LEVELS[shell_level].
    Exterior = all other steps.

    The bipartition density is:
      rho_AB = weighted average of rho_L (interior) ⊗ rho_R (exterior)
    This is the simplest shell-cut observable that uses the earned Phase4
    bridge pattern (L ⊗ R across the cut).

    Returns a valid 4x4 density matrix.
    """
    eta_thresh = SHELL_ETA_LEVELS[shell_level]
    interior = [s for s in history if s.get("eta", 0.0) <= eta_thresh]
    exterior = [s for s in history if s.get("eta", 0.0) > eta_thresh]

    if not interior or not exterior:
        # Degenerate cut — no split; return maximally mixed
        return np.eye(4, dtype=complex) / 4

    rho_L_int = _ensure_valid_density(
        np.mean([s["rho_L"] for s in interior], axis=0)
    )
    rho_R_ext = _ensure_valid_density(
        np.mean([s["rho_R"] for s in exterior], axis=0)
    )

    # Use Phase4 retro-weighted chiral bridge pattern
    lr_diff = np.linalg.norm(rho_L_int - rho_R_ext)
    p_bell = float(np.clip(lr_diff * 0.5, 0.01, 0.99))
    prod = _ensure_valid_density(np.kron(rho_L_int, rho_R_ext))
    rho_AB = _ensure_valid_density((1 - p_bell) * prod + p_bell * BELL_PSI_MINUS)
    return rho_AB


def shell_cut_observables(history: list[dict], shell_level: int) -> dict:
    """MI and Ic at a given shell level."""
    rho = shell_bipartition_rho(history, shell_level)
    return {
        "shell_level": shell_level,
        "eta_thresh": float(SHELL_ETA_LEVELS[shell_level]),
        "mi": mi_val(rho),
        "ic": ic_val(rho),
        "interior_steps": sum(1 for s in history if s.get("eta", 0.0) <= SHELL_ETA_LEVELS[shell_level]),
        "exterior_steps": sum(1 for s in history if s.get("eta", 0.0) > SHELL_ETA_LEVELS[shell_level]),
    }


# --------------------------------------------------------------------------- #
# Lane A — Dynamic shell vs static shell                                      #
# --------------------------------------------------------------------------- #

def lane_a_dynamic_vs_static(history: list[dict]) -> dict:
    """
    Static: measure MI at fixed midpoint shell level throughout.
    Dynamic: start at midpoint; each tick move the cut ±1 based on whether
             MI increases (outward) or decreases (inward).
    Compare final MI and variance across tick sequence.
    """
    mid = N_SHELL_LEVELS // 2

    # Static: fixed cut
    static_obs = shell_cut_observables(history, mid)
    static_mi = static_obs["mi"]

    # Dynamic: greedy hill-climbing on MI
    level = mid
    dynamic_trajectory = []
    prev_mi = shell_cut_observables(history, level)["mi"]

    for _ in range(N_SHELL_LEVELS * 2):  # 2 full traversals
        # Try moving outward
        next_out = min(level + 1, N_SHELL_LEVELS - 1)
        next_in = max(level - 1, 0)
        mi_out = shell_cut_observables(history, next_out)["mi"]
        mi_in = shell_cut_observables(history, next_in)["mi"]

        if mi_out >= mi_in and mi_out >= prev_mi:
            level = next_out
        elif mi_in > mi_out and mi_in >= prev_mi:
            level = next_in
        # else stay

        obs = shell_cut_observables(history, level)
        dynamic_trajectory.append({
            "level": level,
            "mi": obs["mi"],
            "ic": obs["ic"],
        })
        prev_mi = obs["mi"]

    dynamic_mi_vals = [t["mi"] for t in dynamic_trajectory]
    dynamic_peak_mi = max(dynamic_mi_vals)
    dynamic_final_mi = dynamic_trajectory[-1]["mi"]
    dynamic_variance = float(np.var(dynamic_mi_vals))

    static_variance = 0.0  # fixed cut has zero variance by definition

    # Keep signal: dynamic_peak_mi > static_mi + threshold
    separation = dynamic_peak_mi - static_mi
    lane_a_keep = bool(separation > 0.05)

    return {
        "static_mi": static_mi,
        "static_ic": static_obs["ic"],
        "dynamic_peak_mi": dynamic_peak_mi,
        "dynamic_final_mi": dynamic_final_mi,
        "dynamic_variance": dynamic_variance,
        "static_variance": static_variance,
        "separation": separation,
        "lane_a_keep": lane_a_keep,
        "dynamic_trajectory_length": len(dynamic_trajectory),
    }


# --------------------------------------------------------------------------- #
# Lane B — Discrete ticks vs continuum gradation                              #
# --------------------------------------------------------------------------- #

def lane_b_discrete_vs_continuum(history: list[dict]) -> dict:
    """
    Discrete: measure MI at each of N_SHELL_LEVELS integer shell levels.
    Continuum approximation: linear interpolation of MI between levels.
    Check whether discrete finite differences carry meaningful gradient signal.
    """
    discrete_obs = [shell_cut_observables(history, k) for k in range(N_SHELL_LEVELS)]
    discrete_mi = [o["mi"] for o in discrete_obs]
    discrete_ic = [o["ic"] for o in discrete_obs]

    # Finite differences
    first_diffs = [discrete_mi[k + 1] - discrete_mi[k] for k in range(N_SHELL_LEVELS - 1)]
    abs_diffs = [abs(d) for d in first_diffs]
    mean_abs_diff = float(np.mean(abs_diffs))
    max_abs_diff = float(np.max(abs_diffs))
    sign_changes = sum(1 for i in range(len(first_diffs) - 1)
                       if first_diffs[i] * first_diffs[i + 1] < 0)

    # Continuum interpolation: how much extra info does it add?
    # Measured as residual between actual discrete values and linear interp
    interp_mi = np.interp(
        np.linspace(0, N_SHELL_LEVELS - 1, N_SHELL_LEVELS * 4),
        np.arange(N_SHELL_LEVELS),
        discrete_mi,
    )
    # Residual of discrete points vs linear between endpoints only
    linear_baseline = np.linspace(discrete_mi[0], discrete_mi[-1], N_SHELL_LEVELS)
    nonlinearity = float(np.mean(np.abs(np.array(discrete_mi) - linear_baseline)))

    # Keep signal: mean_abs_diff > 0.05 (finite differences carry real signal)
    lane_b_keep = bool(mean_abs_diff > 0.05)

    return {
        "discrete_mi": discrete_mi,
        "discrete_ic": discrete_ic,
        "first_diffs": first_diffs,
        "mean_abs_diff": mean_abs_diff,
        "max_abs_diff": max_abs_diff,
        "sign_changes": sign_changes,
        "nonlinearity": nonlinearity,
        "lane_b_keep": lane_b_keep,
    }


# --------------------------------------------------------------------------- #
# Lane C — Multi-layer tensor reading vs single cut                           #
# --------------------------------------------------------------------------- #

def lane_c_multilayer_vs_single_cut(history: list[dict]) -> dict:
    """
    Single cut: MI at a single midpoint shell level.
    Multi-layer: sum / max of MI across all shell levels
                 (compression score = how much MI concentrates in one layer).
    Check whether multi-layer reading sharpens discrimination.
    """
    mid_obs = shell_cut_observables(history, N_SHELL_LEVELS // 2)
    single_mi = mid_obs["mi"]
    single_ic = mid_obs["ic"]

    layer_obs = [shell_cut_observables(history, k) for k in range(N_SHELL_LEVELS)]
    layer_mi = np.array([o["mi"] for o in layer_obs])
    layer_ic = np.array([o["ic"] for o in layer_obs])

    multi_sum_mi = float(np.sum(layer_mi))
    multi_max_mi = float(np.max(layer_mi))
    multi_peak_level = int(np.argmax(layer_mi))
    multi_std_mi = float(np.std(layer_mi))

    # Compression score: fraction of total MI concentrated in top 2 layers
    sorted_mi = np.sort(layer_mi)[::-1]
    top2_fraction = float(sorted_mi[:2].sum() / (multi_sum_mi + EPS))

    # IC sign pattern: how many layers have Ic > 0 (coherent information positive)
    positive_ic_layers = int(np.sum(layer_ic > 0))

    # Keep signal: multi_max_mi > single_mi + 0.1 (multi-layer finds better cut)
    lane_c_keep = bool(multi_max_mi > single_mi + 0.1)

    return {
        "single_cut_mi": single_mi,
        "single_cut_ic": single_ic,
        "multi_max_mi": multi_max_mi,
        "multi_peak_level": multi_peak_level,
        "multi_sum_mi": multi_sum_mi,
        "multi_std_mi": multi_std_mi,
        "top2_fraction": top2_fraction,
        "positive_ic_layers": positive_ic_layers,
        "lane_c_keep": lane_c_keep,
    }


# --------------------------------------------------------------------------- #
# Runner                                                                       #
# --------------------------------------------------------------------------- #

def run_torus(engine_type: int, torus_name: str, torus_val: float) -> dict:
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=torus_val)
    final_state = engine.run_cycle(state)

    # ax0_torus_entropy = -cos²η ln cos²η - sin²η ln sin²η ∈ [0, 1]
    # Use it as a normalized shell-radius proxy (0 = poles, 1 = equator)
    history = []
    for step in final_state.history:
        history.append({
            "rho_L": step["rho_L"],
            "rho_R": step["rho_R"],
            "eta": float(step.get("ax0_torus_entropy", 0.5)),
        })

    a = lane_a_dynamic_vs_static(history)
    b = lane_b_discrete_vs_continuum(history)
    c = lane_c_multilayer_vs_single_cut(history)

    # Overall keep/kill
    keep_count = sum([a["lane_a_keep"], b["lane_b_keep"], c["lane_c_keep"]])

    verdict = "KEEP" if keep_count >= 2 else "KILL"

    print(f"  {engine_type}/{torus_name}: "
          f"A={'KEEP' if a['lane_a_keep'] else 'kill'} "
          f"(sep={a['separation']:.3f}) | "
          f"B={'KEEP' if b['lane_b_keep'] else 'kill'} "
          f"(Δ={b['mean_abs_diff']:.3f}) | "
          f"C={'KEEP' if c['lane_c_keep'] else 'kill'} "
          f"(gain={c['multi_max_mi']-c['single_cut_mi']:.3f}) | "
          f"→ {verdict}")

    return {
        "engine_type": engine_type,
        "torus": torus_name,
        "lane_a": a,
        "lane_b": b,
        "lane_c": c,
        "keep_count": keep_count,
        "verdict": verdict,
    }


def main() -> None:
    print("=" * 72)
    print("AXIS 0 DYNAMIC SHELL DISCRIMINATION SIM")
    print("=" * 72)
    print(f"Shell levels: {N_SHELL_LEVELS}  |  eta range: "
          f"[{SHELL_ETA_LEVELS[0]:.3f}, {SHELL_ETA_LEVELS[-1]:.3f}]")
    print()

    results = []
    for eng_type in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            r = run_torus(eng_type, torus_name, torus_val)
            results.append(r)

    # Aggregate
    keep_a = sum(1 for r in results if r["lane_a"]["lane_a_keep"])
    keep_b = sum(1 for r in results if r["lane_b"]["lane_b_keep"])
    keep_c = sum(1 for r in results if r["lane_c"]["lane_c_keep"])
    full_keeps = sum(1 for r in results if r["verdict"] == "KEEP")
    N = len(results)

    print()
    print("=" * 72)
    print("OVERALL VERDICT")
    print("=" * 72)
    print(f"  Lane A (dynamic > static):     {keep_a}/{N} keep")
    print(f"  Lane B (finite diffs carry MI): {keep_b}/{N} keep")
    print(f"  Lane C (multi-layer sharpens):  {keep_c}/{N} keep")
    print(f"  Full KEEP (≥2 lanes):           {full_keeps}/{N}")
    print()

    if keep_a >= N // 2:
        print("  ✓ Lane A KEEP — dynamic shell motion produces nontrivial MI separation")
    else:
        print("  ✗ Lane A KILL — dynamic shell adds no separation over static cut")

    if keep_b >= N // 2:
        print("  ✓ Lane B KEEP — discrete finite shell ticks carry real bridge signal")
    else:
        print("  ✗ Lane B KILL — finite ticks do not carry sufficient signal")

    if keep_c >= N // 2:
        print("  ✓ Lane C KEEP — multi-layer reading sharpens discrimination")
    else:
        print("  ✗ Lane C KILL — multi-layer adds no gain over single cut")

    print()
    overall = "SHELL PROPOSAL SUPPORTED" if full_keeps >= N // 2 else "SHELL PROPOSAL NOT SUPPORTED"
    print(f"  → {overall}")

    print()
    print("================================================================================")
    print(f"PROBE STATUS: {'PASS' if full_keeps > 0 else 'FAIL'}")
    print("================================================================================")

    # Serialize (convert ndarray → list for JSON)
    def to_json_safe(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, dict):
            return {k: to_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [to_json_safe(v) for v in obj]
        return obj

    output = {
        "timestamp": datetime.now(UTC).isoformat(),
        "n_shell_levels": N_SHELL_LEVELS,
        "shell_eta_levels": SHELL_ETA_LEVELS.tolist(),
        "results": to_json_safe(results),
        "summary": {
            "keep_lane_a": keep_a,
            "keep_lane_b": keep_b,
            "keep_lane_c": keep_c,
            "full_keeps": full_keeps,
            "total": N,
            "overall": overall,
        },
    }

    out_path = os.path.join(
        os.path.dirname(__file__),
        "a2_state", "sim_results", "axis0_dynamic_shell_results.json",
    )
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
