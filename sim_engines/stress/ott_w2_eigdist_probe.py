#!/usr/bin/env python3
"""UNOFFICIAL STRESS PROBE — ott-jax Sinkhorn W2 between eigenvalue distributions.

classification: unofficial_stress_probe · promotion_allowed: false
claim_ceiling: capability demonstration only — shows ott-jax (pointcloud
geometry + Sinkhorn solver, epsilon 1e-3) computes entropic W2 optimal
transport between the eigenvalue distributions of 2-qubit density matrices,
a capability bare jnp lacks (jnp has no OT solver). Cross-checked against
the EXACT 1-D sorted-coupling closed form. No manifold, axis, or bridge
claim. Parks by definition.

Objects (all 4x4, trace 1, PSD):
  rho_R : real-constrained  — O diag(lam) O^T, O real orthogonal
  rho_C : genuinely complex — U diag(lam) U^dag, U complex unitary,
          SAME eigenvalue multiset lam = (0.475, 0.325, 0.175, 0.025)
  rho_D : complex, genuinely DIFFERENT spectrum lam_D = (0.6, 0.2, 0.15, 0.05)

Checks:
  1. eigvalsh recovers the constructed spectra (<1e-12); rho_C is genuinely
     complex (max|imag| > 0.01), rho_R strictly real.
  2. LOAD-BEARING ott: Sinkhorn transport cost sum(P*C) on the 4-point
     eigenvalue clouds matches the exact sorted-coupling closed form
     sum((sort(a)-sort(b))^2)/n to <1e-3 relative, for both nonzero pairs
     (R,D) and (C,D). Convergence = marginal error < 1e-5 (recorded in the
     receipt): at eps=1e-3 Sinkhorn's terminal contraction is ~(1 - 4e-5)
     per iteration, so 1e-9-level marginal thresholds are unreachable in a
     bounded budget; cost accuracy is verified INDEPENDENTLY by the exact
     closed form, not by the marginal threshold.
  3. NEGATIVE CONTROL that flips: identical spectra (R,C) -> W2^2 < 1e-6;
     distinct spectra (R,D) -> W2^2 bounded away from 0 (> 1e-3).

Exit 0 = probe completed (agreements recorded either way); 1 = infra failure.
"""
import json
import os
import time
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

import ott
from ott.geometry import pointcloud
from ott.problems.linear import linear_problem
from ott.solvers.linear import sinkhorn

HERE = Path(__file__).resolve().parent

LAM = (0.475, 0.325, 0.175, 0.025)   # equal gaps 0.15 — sum 1, PSD
LAM_D = (0.6, 0.2, 0.15, 0.05)       # genuinely different multiset, sum 1


def haar_like_unitary(key, dim, complex_):
    """QR-orthonormalized random matrix: orthogonal (real) or unitary (complex)."""
    if complex_:
        k1, k2 = jax.random.split(key)
        m = (jax.random.normal(k1, (dim, dim))
             + 1j * jax.random.normal(k2, (dim, dim))).astype(jnp.complex128)
    else:
        m = jax.random.normal(key, (dim, dim)).astype(jnp.float64)
    q, r = jnp.linalg.qr(m)
    return q * (jnp.diagonal(r) / jnp.abs(jnp.diagonal(r)))  # fix phase ambiguity


def rho_from_spectrum(lam, key, complex_):
    v = haar_like_unitary(key, len(lam), complex_)
    return v @ jnp.diag(jnp.asarray(lam, dtype=v.dtype)) @ v.conj().T


def sinkhorn_w2sq(a, b, epsilon):
    """Entropic OT via ott-jax: 1-D point clouds -> transport cost sum(P*C)."""
    geom = pointcloud.PointCloud(a[:, None], b[:, None], epsilon=epsilon)
    prob = linear_problem.LinearProblem(geom)
    out = sinkhorn.Sinkhorn(threshold=1e-5, max_iterations=50_000)(prob)
    errs = out.errors
    final_err = float(errs[errs > -1][-1]) if bool((errs > -1).any()) else float("nan")
    return (float(jnp.sum(out.matrix * geom.cost_matrix)),
            bool(out.converged), final_err, int(out.n_iters))


def exact_w2sq(a, b):
    """EXACT independent path: 1-D W2^2 = sum((sort(a)-sort(b))^2)/n.

    Pure python floats + sorted() — no jnp, no ott.
    """
    sa, sb = sorted(float(x) for x in a), sorted(float(x) for x in b)
    return sum((x - y) ** 2 for x, y in zip(sa, sb)) / len(sa)


def main():
    t0 = time.perf_counter()
    eps = 1e-3
    key = jax.random.PRNGKey(7)
    k_r, k_c, k_d = jax.random.split(key, 3)

    rho_r = rho_from_spectrum(LAM, k_r, complex_=False)
    rho_c = rho_from_spectrum(LAM, k_c, complex_=True)
    rho_d = rho_from_spectrum(LAM_D, k_d, complex_=True)

    # 1. object sanity: spectra recovered, realness/complexness as constructed
    ev = {name: jnp.linalg.eigvalsh(rho) for name, rho in
          [("rho_R", rho_r), ("rho_C", rho_c), ("rho_D", rho_d)]}
    spec_div = max(
        float(jnp.max(jnp.abs(ev["rho_R"] - jnp.asarray(sorted(LAM))))),
        float(jnp.max(jnp.abs(ev["rho_C"] - jnp.asarray(sorted(LAM))))),
        float(jnp.max(jnp.abs(ev["rho_D"] - jnp.asarray(sorted(LAM_D))))),
    )
    max_imag_c = float(jnp.max(jnp.abs(jnp.imag(rho_c))))
    max_imag_r = float(jnp.max(jnp.abs(jnp.imag(rho_r.astype(jnp.complex128)))))
    trace_div = max(float(abs(jnp.trace(m).real - 1.0)) for m in (rho_r, rho_c, rho_d))
    objects_ok = (spec_div < 1e-12 and max_imag_c > 1e-2
                  and max_imag_r == 0.0 and trace_div < 1e-12)

    # 2. LOAD-BEARING ott: sinkhorn vs exact sorted-coupling, all three pairs
    pairs = {"R_vs_C_identical_multiset": (ev["rho_R"], ev["rho_C"]),
             "R_vs_D_distinct": (ev["rho_R"], ev["rho_D"]),
             "C_vs_D_distinct": (ev["rho_C"], ev["rho_D"])}
    results = {}
    for name, (a, b) in pairs.items():
        sink, converged, marg_err, n_iters = sinkhorn_w2sq(a, b, eps)
        exact = exact_w2sq(a, b)
        rel = abs(sink - exact) / max(exact, 1e-12)
        results[name] = {"sinkhorn_w2sq": sink, "exact_sorted_w2sq": exact,
                         "abs_div": abs(sink - exact), "rel_div": rel,
                         "sinkhorn_converged": converged,
                         "final_marginal_error": marg_err,
                         "n_iters": n_iters}
    crosscheck_ok = all(
        results[k]["sinkhorn_converged"] and results[k]["rel_div"] < 1e-3
        for k in ("R_vs_D_distinct", "C_vs_D_distinct"))

    # 3. NEGATIVE CONTROL that flips: identical -> ~0; distinct -> away from 0
    w2_identical = results["R_vs_C_identical_multiset"]["sinkhorn_w2sq"]
    w2_distinct = results["R_vs_D_distinct"]["sinkhorn_w2sq"]
    control_ok = w2_identical < 1e-6 and w2_distinct > 1e-3

    all_pass = objects_ok and crosscheck_ok and control_ok
    receipt = {
        "classification": "unofficial_stress_probe",
        "promotion_allowed": False,
        "claim_ceiling": "capability demonstration only — ott-jax Sinkhorn W2 on "
                         "eigenvalue clouds, exact-closed-form cross-checked; no "
                         "manifold/axis/bridge claim; parks by definition",
        "engines_used": {
            "ott": ["geometry.pointcloud.PointCloud (SqEuclidean)",
                    "solvers.linear.sinkhorn.Sinkhorn (lse, eps=1e-3, "
                    "marginal threshold 1e-5) — LOAD-BEARING"],
            "jax": ["random+qr construction", "eigvalsh", "complex128_x64"],
            "exact_crosscheck": ["1-D sorted-coupling closed form, pure python floats"],
        },
        "ott_version": getattr(ott, "__version__", "unknown"),
        "epsilon": eps,
        "spectra": {"lam_shared": list(LAM), "lam_distinct": list(LAM_D)},
        "objects": {"spectrum_recovery_max_div": spec_div,
                    "rho_C_max_abs_imag": max_imag_c,
                    "rho_R_max_abs_imag": max_imag_r,
                    "trace_max_div": trace_div,
                    "pass": objects_ok},
        "w2_pairs": results,
        "crosscheck": {"rel_tolerance": 1e-3, "pass": crosscheck_ok},
        "negative_control": {"identical_spectra_w2sq": w2_identical,
                             "identical_threshold": 1e-6,
                             "distinct_spectra_w2sq": w2_distinct,
                             "distinct_floor": 1e-3,
                             "flips": control_ok},
        "all_pass": all_pass,
        "seconds": round(time.perf_counter() - t0, 3),
    }
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    with open(out / "ott_w2_eigdist_probe.json", "w") as f:
        json.dump(receipt, f, indent=1, sort_keys=True)
    print(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"[*] ott W2 probe COMPLETED — checks {'ALL HOLD' if all_pass else 'FAIL (recorded)'}; "
          f"receipt: {out / 'ott_w2_eigdist_probe.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
