"""Classical baseline: Holodeck carrier shell spectrum.

Mirrors the holodeck carrier-shell idea with a classical analog: the Laplacian
spectrum of a ring graph (the "shell") has a known closed form
lambda_k = 2 - 2 cos(2*pi*k/N). We treat the spectrum as the carrier and
check that it matches the analytic formula.

scope_note: classical_baseline; mirrors OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md
holodeck framework and ENGINE_MATH_REFERENCE.md shell spectrum baseline.
"""
import numpy as np
from _common import write_results


def ring_laplacian(n):
    A = np.zeros((n, n))
    for i in range(n):
        A[i, (i + 1) % n] = 1
        A[i, (i - 1) % n] = 1
    D = np.diag(A.sum(axis=1))
    return D - A


def analytic_spectrum(n):
    k = np.arange(n)
    return np.sort(2 - 2 * np.cos(2 * np.pi * k / n))


def run_positive():
    out = {}
    for n in (6, 12, 24):
        eig = np.sort(np.linalg.eigvalsh(ring_laplacian(n)))
        ref = analytic_spectrum(n)
        err = float(np.max(np.abs(eig - ref)))
        out[f"ring_n{n}"] = {"max_abs_err": err, "pass": err < 1e-8}
    return out


def run_negative():
    # A path graph is NOT a ring; its spectrum differs from ring formula.
    n = 12
    A = np.zeros((n, n))
    for i in range(n - 1):
        A[i, i + 1] = 1; A[i + 1, i] = 1
    D = np.diag(A.sum(axis=1))
    eig = np.sort(np.linalg.eigvalsh(D - A))
    ref = analytic_spectrum(n)
    err = float(np.max(np.abs(eig - ref)))
    return {"path_not_ring": {"max_abs_err": err, "pass": err > 1e-3}}


def run_boundary():
    # n=3 smallest non-trivial ring; eigs = {0, 3, 3}.
    eig = np.sort(np.linalg.eigvalsh(ring_laplacian(3)))
    ref = np.array([0.0, 3.0, 3.0])
    err = float(np.max(np.abs(eig - ref)))
    return {"ring_n3_min": {"eig": eig.tolist(), "max_abs_err": err, "pass": err < 1e-8}}


if __name__ == "__main__":
    write_results(
        "sim_classical_holodeck_carrier_shell_spectrum",
        "classical_baseline for holodeck carrier-shell (OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md, ENGINE_MATH_REFERENCE.md)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_holodeck_carrier_shell_spectrum_results.json",
    )
