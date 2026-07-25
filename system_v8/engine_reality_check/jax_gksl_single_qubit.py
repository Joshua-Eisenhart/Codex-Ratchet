"""JAX leg of the shared single-qubit GKSL engine-reality check.

Density-operator formalism only (owner rule: density operators, never Bloch).

Task math (given, not derived here):
    rho0  = [[0.75, 0.25], [0.25, 0.25]]
    H     = 0.5 * sigma_z,  sigma_z = diag(1, -1)
    gamma = 0.3
    L     = sqrt(gamma) * sigma_minus,  sigma_minus = [[0, 0], [1, 0]]

    drho/dt = -i[H, rho] + L rho L^dag - 0.5 {L^dag L, rho}

Integration is by EXACT matrix exponential of the vectorised Liouvillian,
column-stacking convention: vec(A X B) = (B^T kron A) vec(X).
No hand-rolled ODE stepper anywhere in this file.

Engine lane: JAX, x64 enabled explicitly. Every linear-algebra operation below
is a jax / jax.numpy / jax.scipy call. numpy is not imported.

Claim ceiling: this is an engine reality check, not a canonical sim. It carries
no SIM_TEMPLATE provenance and admits nothing beyond "this engine executed this
math and these self-checks reported these values".
"""

import json
import os

import jax

# x64 must be set before any array is created; float32 will not hold the 1e-12 checks.
jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from jax.scipy.linalg import expm

TOL = 1e-12
GAMMA = 0.3
T_FINAL = 1.0


def vec_col(a):
    """Column-stacking vectorisation. For [[a,b],[c,d]] returns [a, c, b, d]."""
    return jnp.transpose(a).reshape(-1)


def unvec_col(v, n):
    """Inverse of vec_col."""
    return jnp.transpose(v.reshape(n, n))


def build_liouvillian(h, lop):
    """Vectorised GKSL generator under column-stacking.

    vec(A X B) = (B^T kron A) vec(X), so
      H rho        -> (I kron H)
      rho H        -> (H^T kron I)
      L rho L^dag  -> ((L^dag)^T kron L) = (conj(L) kron L)
      A rho        -> (I kron A)          with A = L^dag L
      rho A        -> (A^T kron I)
    """
    n = h.shape[0]
    eye = jnp.eye(n, dtype=jnp.complex128)
    ldag = jnp.conj(jnp.transpose(lop))
    ldl = ldag @ lop

    ham = -1j * (jnp.kron(eye, h) - jnp.kron(jnp.transpose(h), eye))
    diss_jump = jnp.kron(jnp.conj(lop), lop)
    diss_anti = -0.5 * (jnp.kron(eye, ldl) + jnp.kron(jnp.transpose(ldl), eye))
    return ham + diss_jump + diss_anti


def von_neumann_log2(rho):
    """S = -Tr(rho log2 rho) via the Hermitian eigenspectrum, 0*log0 := 0."""
    ev = jnp.linalg.eigvalsh(rho)
    ev = jnp.clip(ev, 0.0, None)
    safe = jnp.where(ev > 0.0, ev, 1.0)
    return -jnp.sum(jnp.where(ev > 0.0, ev * jnp.log2(safe), 0.0))


@jax.jit
def evolve(rho0, h, lop, t):
    liou = build_liouvillian(h, lop)
    prop = expm(liou * t)
    return unvec_col(prop @ vec_col(rho0), rho0.shape[0])


def main():
    rho0 = jnp.array([[0.75, 0.25], [0.25, 0.25]], dtype=jnp.complex128)
    sigma_z = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
    sigma_minus = jnp.array([[0.0, 0.0], [1.0, 0.0]], dtype=jnp.complex128)

    h = 0.5 * sigma_z
    lop = jnp.sqrt(jnp.asarray(GAMMA, dtype=jnp.complex128)) * sigma_minus

    rho_t = evolve(rho0, h, lop, jnp.asarray(T_FINAL, dtype=jnp.complex128))

    # --- the five reported quantities -------------------------------------
    t1_pop = jnp.real(rho_t[0, 0])
    t2_coh_re = jnp.real(rho_t[0, 1])
    t3_purity = jnp.real(jnp.trace(rho_t @ rho_t))
    t4_vn = von_neumann_log2(rho_t)
    t5_trace = jnp.real(jnp.trace(rho_t))

    # --- mandatory self-checks --------------------------------------------
    # C1 trace preserved to 1e-12
    c1_resid = jnp.abs(jnp.trace(rho_t) - 1.0)
    c1 = bool(c1_resid <= TOL)

    # C2 Hermitian to 1e-12
    c2_resid = jnp.max(jnp.abs(rho_t - jnp.conj(jnp.transpose(rho_t))))
    c2 = bool(c2_resid <= TOL)

    # C3 eigenvalues >= -1e-12
    eig_t = jnp.linalg.eigvalsh(rho_t)
    c3_min = jnp.min(eig_t)
    c3 = bool(c3_min >= -TOL)

    # C4 S at t=0 recomputed from rho0, reported beside S(rho_t)
    s0 = von_neumann_log2(rho0)
    c4 = bool((s0 >= -TOL) & (t4_vn >= -TOL) & jnp.isfinite(s0) & jnp.isfinite(t4_vn))

    # --- independent cross-check, not one of C1..C4 -----------------------
    # Closed-form amplitude damping under H = 0.5 sigma_z, L = sqrt(g) sigma_-:
    #   rho00(t) = rho00(0) e^{-g t}
    #   rho01(t) = rho01(0) e^{-i t} e^{-g t / 2}
    # Derived here from the generator above; used only to catch a wiring error
    # in the vectorisation, never as the reported value.
    g = jnp.asarray(GAMMA, dtype=jnp.float64)
    t = jnp.asarray(T_FINAL, dtype=jnp.float64)
    ana_pop = 0.75 * jnp.exp(-g * t)
    ana_coh_re = 0.25 * jnp.exp(-0.5 * g * t) * jnp.cos(t)
    ana_resid = jnp.maximum(jnp.abs(t1_pop - ana_pop), jnp.abs(t2_coh_re - ana_coh_re))

    out = {
        "t1_pop": float(t1_pop),
        "t2_coh_re": float(t2_coh_re),
        "t3_purity": float(t3_purity),
        "t4_vn_entropy_log2": float(t4_vn),
        "t5_trace": float(t5_trace),
        "c1": c1,
        "c2": c2,
        "c3": c3,
        "c4": c4,
        "c1_trace_residual": float(c1_resid),
        "c2_hermiticity_residual": float(c2_resid),
        "c3_min_eigenvalue": float(c3_min),
        "c4_vn_entropy_log2_t0": float(s0),
        "c4_vn_entropy_log2_t1": float(t4_vn),
        "engine": "jax",
        "jax_version": jax.__version__,
        "x64_enabled": bool(jax.config.jax_enable_x64),
        "dtype": str(rho_t.dtype),
        "device": str(list(rho_t.devices())[0]),
        "method": "expm of vectorised Liouvillian, column-stacking",
        "analytic_crosscheck_residual": float(ana_resid),
        "analytic_crosscheck_pass": bool(ana_resid <= 1e-12),
    }

    print("engine                 : jax %s  (x64=%s, dtype=%s, device=%s)"
          % (out["jax_version"], out["x64_enabled"], out["dtype"], out["device"]))
    print("T1 rho_t[0,0]          : %.12g" % out["t1_pop"])
    print("T2 Re rho_t[0,1]       : %.12g" % out["t2_coh_re"])
    print("T3 purity              : %.12g" % out["t3_purity"])
    print("T4 S (log2)            : %.12g" % out["t4_vn_entropy_log2"])
    print("T5 trace               : %.12g" % out["t5_trace"])
    print("C1 trace preserved     : %s   |Tr-1| = %.6g" % (c1, out["c1_trace_residual"]))
    print("C2 hermitian           : %s   max|rho-rho^dag| = %.6g" % (c2, out["c2_hermiticity_residual"]))
    print("C3 positivity          : %s   min eig = %.12g" % (c3, out["c3_min_eigenvalue"]))
    print("C4 S(rho0) / S(rho_t)  : %s   %.12g  /  %.12g"
          % (c4, out["c4_vn_entropy_log2_t0"], out["c4_vn_entropy_log2_t1"]))
    print("analytic cross-check   : %s   residual = %.6g"
          % (out["analytic_crosscheck_pass"], out["analytic_crosscheck_residual"]))

    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "jax_gksl_single_qubit.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print("json written           : %s" % dest)

    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
