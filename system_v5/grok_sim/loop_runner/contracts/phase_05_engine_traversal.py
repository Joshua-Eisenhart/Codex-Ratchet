"""phase_05_engine_traversal.py — engines actually traverse 32 stages each with state evolution.

This phase calls candidate.run_engine() and verifies:
  - Both engines have exactly 32 stage records each (64 total)
  - Each record has stage/obs/entropy fields
  - Entropy values VARY across stages (range > 0.05) — pure state under non-trivial
    evolution should grow entropy via dissipation
  - Final density matrices are valid: hermitian, trace ≈ 1, eigenvalues ≥ 0
  - cross_engine_observable and cycle_closure_a are real numbers in [0, 2]
"""
import numpy as np


def _check_density_matrix_valid(rho, label):
    """Check rho is hermitian, trace 1, eigenvalues ≥ 0 (small tolerance)."""
    failures = []
    # Accept torch tensor, numpy array, or qutip Qobj
    if hasattr(rho, "numpy"):
        arr = rho.detach().cpu().numpy() if hasattr(rho, "detach") else rho.numpy()
    elif hasattr(rho, "full"):
        arr = rho.full()
    else:
        arr = np.asarray(rho)

    if arr.shape != (16, 16):
        failures.append({"check": f"{label}_shape",
                         "msg": f"{label} has shape {arr.shape}, expected (16,16)"})
        return failures, {}

    # Hermitian
    herm_err = np.max(np.abs(arr - arr.conj().T))
    if herm_err > 1e-6:
        failures.append({"check": f"{label}_hermitian",
                         "msg": f"{label} hermiticity error = {herm_err:.2e}, expected < 1e-6"})

    # Trace
    tr = np.trace(arr).real
    if abs(tr - 1.0) > 1e-4:
        failures.append({"check": f"{label}_trace",
                         "msg": f"{label} trace = {tr:.6f}, expected ≈ 1.0"})

    # Eigenvalues ≥ 0
    eigs = np.linalg.eigvalsh(0.5 * (arr + arr.conj().T))
    min_eig = float(eigs.min())
    if min_eig < -1e-6:
        failures.append({"check": f"{label}_psd",
                         "msg": f"{label} min eigenvalue = {min_eig:.2e}, expected ≥ -1e-6"})

    return failures, {f"{label}_trace": float(tr),
                      f"{label}_min_eig": float(min_eig),
                      f"{label}_hermiticity_err": float(herm_err)}


def run(candidate):
    failures = []
    metrics = {}

    try:
        r = candidate.run_engine()
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "run_engine_call",
                          "msg": f"raised {type(e).__name__}: {str(e)[:400]}"}],
            "metrics": metrics,
        }

    # Required keys
    required = ["engine_a_final_state", "engine_b_final_state",
                "engine_a_stage_records", "engine_b_stage_records",
                "cross_engine_observable", "cycle_closure_a"]
    for k in required:
        if k not in r:
            failures.append({"check": f"run_engine_missing_{k}",
                             "msg": f"run_engine() missing key `{k}`"})
    if failures:
        return {"pass": False, "failures": failures, "metrics": metrics}

    # Stage record counts
    rec_a = r["engine_a_stage_records"]
    rec_b = r["engine_b_stage_records"]
    metrics["engine_a_stage_count"] = len(rec_a)
    metrics["engine_b_stage_count"] = len(rec_b)
    if len(rec_a) != 32:
        failures.append({"check": "engine_a_stage_count",
                         "msg": f"engine A has {len(rec_a)} stage records, expected 32"})
    if len(rec_b) != 32:
        failures.append({"check": "engine_b_stage_count",
                         "msg": f"engine B has {len(rec_b)} stage records, expected 32"})

    # Each record has stage/obs/entropy
    for engine_name, records in [("A", rec_a), ("B", rec_b)]:
        for rec in records[:5] + records[-5:]:
            for field in ("stage", "obs", "entropy"):
                if field not in rec:
                    failures.append({"check": f"engine_{engine_name}_record_field_{field}",
                                     "msg": f"record missing `{field}` field: {rec}"})
                    break

    # Entropy variation
    if len(rec_a) > 0 and all("entropy" in rec for rec in rec_a):
        ent_a = [float(rec["entropy"]) for rec in rec_a]
        ent_a_range = max(ent_a) - min(ent_a)
        metrics["engine_a_entropy_min"] = min(ent_a)
        metrics["engine_a_entropy_max"] = max(ent_a)
        metrics["engine_a_entropy_range"] = ent_a_range
        if ent_a_range < 0.05:
            failures.append({
                "check": "engine_a_entropy_varies",
                "msg": f"Engine A entropy range = {ent_a_range:.4f} < 0.05. "
                       f"From pure state, 32 stages of evolution should grow entropy via "
                       f"dissipation. Range near zero means either no dissipator in stages "
                       f"or dynamics trivially preserve purity.",
            })
        min_e_a = min(ent_a)
        if min_e_a < -1e-8:
            failures.append({
                "check": "engine_a_entropy_nonneg",
                "msg": f"Engine A min entropy = {min_e_a}. Von Neumann entropy is "
                       f"non-negative; this indicates eigenvalue clamping not catching "
                       f"floating-point negatives.",
            })

    if len(rec_b) > 0 and all("entropy" in rec for rec in rec_b):
        ent_b = [float(rec["entropy"]) for rec in rec_b]
        ent_b_range = max(ent_b) - min(ent_b)
        metrics["engine_b_entropy_range"] = ent_b_range
        if ent_b_range < 0.05:
            failures.append({
                "check": "engine_b_entropy_varies",
                "msg": f"Engine B entropy range = {ent_b_range:.4f} < 0.05",
            })

    # Density matrix validity on final states
    fa, ma = _check_density_matrix_valid(r["engine_a_final_state"], "engine_a_final")
    fb, mb = _check_density_matrix_valid(r["engine_b_final_state"], "engine_b_final")
    failures.extend(fa)
    failures.extend(fb)
    metrics.update(ma)
    metrics.update(mb)

    # Cross-engine + cycle closure are bounded reals
    ce = r.get("cross_engine_observable")
    cc = r.get("cycle_closure_a")
    metrics["cross_engine_observable"] = ce
    metrics["cycle_closure_a"] = cc
    if not isinstance(ce, (int, float)) or ce < 0 or ce > 2:
        failures.append({"check": "cross_engine_in_range",
                         "msg": f"cross_engine_observable = {ce}, expected real in [0, 2]"})
    if not isinstance(cc, (int, float)) or cc < 0 or cc > 2:
        failures.append({"check": "cycle_closure_in_range",
                         "msg": f"cycle_closure_a = {cc}, expected real in [0, 2]"})

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "entropy = 0 for all stages — fails entropy_varies (no dissipator in stage operators)",
            "32 stage records but all identical observables — fails (state not evolving)",
            "final state not hermitian — fails density-matrix validity (numerical instability)",
            "cross_engine_observable < 0 or > 2 — fails range check",
        ],
        "baseline_variants": [
            "all-unitary stage operators baseline — fails entropy_varies",
            "no-evolution baseline (identity stages) — fails entropy_varies",
        ],
    }
