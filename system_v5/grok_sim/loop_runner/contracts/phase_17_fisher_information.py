"""phase_17_fisher_information.py — Fisher information matrix emerges from the architecture.

IGT (Information Geometry Theory): a Riemannian metric on the state manifold given by
Fisher information. For our 7-axis architecture, each axis defines a direction in state
space, and the Fisher matrix F_ij = ⟨∂_i log p · ∂_j log p⟩ captures the local geometry.

If the 7 axes are GENUINELY independent (per Phase 16's pairwise-distinct outputs), the
Fisher information matrix must be:
  - 7×7 symmetric
  - Positive semi-definite (PSD): all eigenvalues ≥ 0
  - Full rank (non-degenerate): determinant > 0
  - Eigenvalues distributed (not all equal — different axes have different "speed")

The architecture must EXPOSE this via `fisher_information_matrix(theta=0.01) -> dict`.
Grok shouldn't fake the math — Opus recomputes eigenvalues and determinant independently.
"""
import numpy as np


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "fisher_information_matrix"):
        return {
            "pass": False,
            "failures": [{
                "check": "fisher_information_matrix_exists",
                "msg": "Required function `fisher_information_matrix(theta_perturbation: float = 0.01) -> dict` "
                       "is not exported. The 7-axis architecture must expose its IGT structure: the Fisher "
                       "information matrix F_ij computed from perturbing each axis parameter. Return dict: "
                       "{matrix: 7x7 list-of-lists float, eigenvalues: list[7] float, determinant: float, "
                       "symmetric: bool, psd: bool}.",
            }],
            "metrics": metrics,
        }

    try:
        r = candidate.fisher_information_matrix(0.01)
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "fisher_call",
                          "msg": f"fisher_information_matrix raised {type(e).__name__}: {str(e)[:300]}"}],
            "metrics": metrics,
        }

    required = ("matrix", "eigenvalues", "determinant", "symmetric", "psd")
    for k in required:
        if k not in r:
            failures.append({"check": f"fisher_missing_{k}", "msg": f"missing key `{k}` in fisher_information_matrix() return"})
    if failures:
        return {"pass": False, "failures": failures, "metrics": metrics}

    # Independently parse and verify the matrix
    try:
        M = np.asarray(r["matrix"], dtype=float)
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "fisher_matrix_parse",
                          "msg": f"could not parse matrix as 2d numeric array: {e}"}],
            "metrics": {"matrix_raw": r.get("matrix")},
        }

    metrics["matrix_shape"] = tuple(M.shape)

    if M.shape != (7, 7):
        failures.append({
            "check": "fisher_matrix_shape",
            "msg": f"Fisher matrix has shape {M.shape}, expected (7, 7). The 7 axes "
                   f"should give a 7×7 metric.",
        })
        return {"pass": False, "failures": failures, "metrics": metrics}

    # Symmetric (within tolerance)
    asym = float(np.max(np.abs(M - M.T)))
    metrics["asymmetry"] = asym
    if asym > 0.01:
        failures.append({
            "check": "fisher_symmetric",
            "msg": f"max |M - M^T| = {asym:.4f}, exceeds 0.01. Fisher info matrix must be "
                   f"symmetric (Re part of quantum Fisher info is symmetric by construction).",
        })

    # Compute eigenvalues independently — don't trust candidate's reported values
    sym_M = 0.5 * (M + M.T)
    eigs_independent = np.linalg.eigvalsh(sym_M)
    metrics["eigenvalues_independent"] = [float(x) for x in eigs_independent]
    metrics["eigenvalues_reported"] = list(r["eigenvalues"])
    metrics["determinant_independent"] = float(np.linalg.det(sym_M))
    metrics["determinant_reported"] = float(r["determinant"])

    min_eig = float(eigs_independent.min())
    if min_eig < -1e-6:
        failures.append({
            "check": "fisher_psd",
            "msg": f"min eigenvalue of Fisher matrix = {min_eig:.4e}, expected ≥ 0. "
                   f"Fisher information is positive semi-definite by construction.",
        })

    # Rank: count eigenvalues above tiny threshold
    rank = int((eigs_independent > 1e-8).sum())
    metrics["rank"] = rank
    if rank < 7:
        failures.append({
            "check": "fisher_full_rank",
            "msg": f"Fisher matrix has rank {rank}/7. Linearly dependent axes — the 7 "
                   f"directions don't span 7-dimensional space.",
        })

    # Determinant cross-check (sanity)
    det_disagree = abs(float(r["determinant"]) - float(np.linalg.det(sym_M)))
    if det_disagree > max(1e-3, 0.05 * abs(np.linalg.det(sym_M))):
        failures.append({
            "check": "fisher_determinant_recompute",
            "msg": f"reported det = {r['determinant']:.4e}, independent det = {np.linalg.det(sym_M):.4e}, "
                   f"|Δ| = {det_disagree:.4e}",
        })

    # Eigenvalue distribution: not all equal (degenerate metric → no scale separation)
    eig_spread = float(eigs_independent.max() - eigs_independent.min())
    metrics["eigenvalue_spread"] = eig_spread
    if eig_spread < 1e-6:
        failures.append({
            "check": "fisher_nontrivial_spectrum",
            "msg": f"All Fisher eigenvalues are approximately equal (spread = {eig_spread:.2e}). "
                   f"A non-trivial metric should have distinct curvature in different directions.",
        })

    # PSD field matches our recompute
    if r.get("psd") != (min_eig >= -1e-6):
        failures.append({
            "check": "fisher_psd_consistent",
            "msg": f"reported psd = {r.get('psd')}, but min_eig = {min_eig:.2e} (independent recompute)",
        })

    # Determinism: same theta → same matrix
    try:
        r2 = candidate.fisher_information_matrix(0.01)
        M2 = np.asarray(r2["matrix"], dtype=float)
        det_drift = float(np.max(np.abs(M - M2)))
        if det_drift > 1e-4:
            failures.append({
                "check": "fisher_deterministic",
                "msg": f"two calls returned matrices differing by max |Δ| = {det_drift:.2e}",
            })
    except Exception:
        pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "Fisher matrix = zero matrix (no info) — fails non-degenerate + rank checks",
            "Fisher matrix = identity (all axes equivalent) — fails eigenvalue spread",
            "Fisher matrix with negative eigenvalues — fails PSD",
            "Fisher matrix not symmetric — fails symmetric check",
            "Fisher matrix with hardcoded values not matching independent recompute — fails det_recompute",
        ],
        "baseline_variants": [
            "1×1 baseline (single parameter): trivial F_11 — fails shape check",
            "rank-1 baseline (parameters span a line): one eigenvalue, rest zero — fails full rank",
            "Cramer-Rao saturating estimator: F symmetric, PSD, non-degenerate — should pass",
        ],
    }
