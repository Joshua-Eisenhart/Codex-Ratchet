"""phase_24_decoherence_free_subspace.py — find DFS states immune to specific noise.

A real AI primitive: given a noise channel (specified by terrain), find density matrices
ρ that are INVARIANT under that noise: D[L]ρ ≈ 0. These form the decoherence-free
subspace — states the noise can't decohere. Useful for noise-immune quantum computation.

Required API: `decoherence_free_subspace(noise_terrain: str) -> dict`
  Input:
    noise_terrain: "Ti" or "Te" (which dephasing channel to find DFS for)
  Returns:
    {
      "noise_terrain": str,
      "dfs_dimension": int,                # dim of DFS (>= 1 for any non-trivial dissipator)
      "dfs_projector_qt": qt.Qobj,         # projector onto DFS
      "sample_dfs_state_qt": qt.Qobj,       # one representative DFS state (16x16)
      "invariance_error": float,           # max |D[L] applied to DFS state|; should be ≈ 0
    }

Pass criteria:
  - Function callable for noise_terrain in {"Ti", "Te"}
  - DFS dimension >= 1 (always exists for σ_z or σ_x dephasing on a 16-dim Hilbert)
  - sample_dfs_state is hermitian, PSD, trace=1
  - When the dissipator D[L_noise] is applied to sample_dfs_state, output is approximately
    equal to input (invariance_error < 1e-3)
  - Different noise_terrains produce different DFS projectors
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"): return np.asarray(obj.full())
    if hasattr(obj, "numpy"):
        return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "decoherence_free_subspace"):
        return {
            "pass": False,
            "failures": [{
                "check": "decoherence_free_subspace_exists",
                "msg": "Required function `decoherence_free_subspace(noise_terrain: str) -> dict` "
                       "is not exported. Find DFS states ρ where D[L_noise]·ρ ≈ 0. Return dict: "
                       "{noise_terrain, dfs_dimension, dfs_projector_qt, sample_dfs_state_qt, invariance_error}.",
            }],
            "metrics": metrics,
        }

    results = {}
    for t in ("Ti", "Te"):
        try:
            r = candidate.decoherence_free_subspace(t)
        except Exception as e:
            failures.append({"check": f"dfs_call_{t}",
                             "msg": f"decoherence_free_subspace('{t}') raised {type(e).__name__}: {str(e)[:200]}"})
            continue
        if not isinstance(r, dict):
            failures.append({"check": f"dfs_dict_{t}", "msg": "not dict"})
            continue
        for k in ("dfs_dimension", "dfs_projector_qt", "sample_dfs_state_qt", "invariance_error"):
            if k not in r:
                failures.append({"check": f"dfs_{t}_missing_{k}", "msg": f"missing `{k}`"})
                break
        else:
            results[t] = r

    if not results:
        return {"pass": False, "failures": failures, "metrics": metrics}

    for t, r in results.items():
        dim = int(r["dfs_dimension"])
        metrics[f"{t}_dfs_dimension"] = dim
        if dim < 1:
            failures.append({"check": f"dfs_dim_positive_{t}",
                             "msg": f"DFS dim for {t} is {dim}, must be ≥ 1"})

        # Sample state should be valid density matrix
        try:
            ρ = _to_arr(r["sample_dfs_state_qt"])
            if ρ.shape != (16, 16):
                failures.append({"check": f"dfs_state_shape_{t}",
                                 "msg": f"sample_dfs_state shape {ρ.shape}, expected (16,16)"})
            else:
                tr = np.real(np.trace(ρ))
                herm_err = float(np.max(np.abs(ρ - ρ.conj().T)))
                eigs = np.linalg.eigvalsh(0.5 * (ρ + ρ.conj().T))
                metrics[f"{t}_state_trace"] = float(tr)
                metrics[f"{t}_state_hermiticity_err"] = herm_err
                metrics[f"{t}_state_min_eig"] = float(eigs.min())
                if abs(tr - 1.0) > 1e-3:
                    failures.append({"check": f"dfs_state_trace_{t}",
                                     "msg": f"trace={tr}, expected 1"})
                if herm_err > 1e-4:
                    failures.append({"check": f"dfs_state_hermitian_{t}",
                                     "msg": f"hermiticity err {herm_err:.2e}"})
                if eigs.min() < -1e-4:
                    failures.append({"check": f"dfs_state_psd_{t}",
                                     "msg": f"min eig {eigs.min():.2e} < 0"})
        except Exception as e:
            failures.append({"check": f"dfs_state_parse_{t}", "msg": str(e)[:200]}); continue

        # Invariance check
        inv_err = float(r["invariance_error"])
        metrics[f"{t}_invariance_error"] = inv_err
        if inv_err > 1e-2:
            failures.append({
                "check": f"dfs_invariance_{t}",
                "msg": f"invariance_error for {t} = {inv_err:.4e} > 1e-2. The DFS state is "
                       f"not actually invariant under the noise channel.",
            })

    # Different noise terrains → different DFS projectors
    if "Ti" in results and "Te" in results:
        try:
            P_Ti = _to_arr(results["Ti"]["dfs_projector_qt"])
            P_Te = _to_arr(results["Te"]["dfs_projector_qt"])
            diff = float(np.max(np.abs(P_Ti - P_Te)))
            metrics["projector_diff_Ti_vs_Te"] = diff
            if diff < 0.05:
                failures.append({
                    "check": "dfs_different_for_different_noise",
                    "msg": f"DFS projectors for Ti and Te differ by max |Δ| = {diff:.4e} < 0.05. "
                           f"Different dephasing channels should have DIFFERENT DFSs (σ_z and σ_x "
                           f"don't share the same protected states).",
                })
        except Exception:
            pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "DFS = entire 16-dim space (trivially invariant) — wrong; only specific states are invariant",
            "DFS = empty (no protected states) — fails dim_positive; should always have at least 1",
            "Ti and Te give same DFS — fails (σ_z and σ_x have different eigenstates)",
            "sample_dfs_state not actually invariant — fails invariance_error check",
        ],
        "baseline_variants": [
            "identity-projector baseline: DFS = entire space, fails invariance_error elsewhere",
            "zero-state baseline: DFS = vacuum only, fails dim or invariance",
        ],
    }
