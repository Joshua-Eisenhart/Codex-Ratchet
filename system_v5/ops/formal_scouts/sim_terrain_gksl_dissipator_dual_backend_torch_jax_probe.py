#!/usr/bin/env python3
"""Dual-backend GKSL (Lindblad) "terrain motion" dissipator probe (diagnostic_only).

REFERENCE dual-backend terrain-motion sim. PyTorch is the PRIMARY formal runtime;
JAX/Diffrax is the INDEPENDENT numeric mirror. z3/sympy are not in the hot loop
(no SMT wrap is needed for this dynamics probe; the analytic known-value checks are
the proof surface).

PHYSICS -- GKSL (Lindblad) master equation, the single-qubit "terrain motion":

    drho/dt = -i[H, rho] + sum_k ( L_k rho L_k^dag - 1/2 {L_k^dag L_k, rho} )

with the EXACT operators (shared by torch, jax, and the analytic check):

    H   = (omega/2) sigma_z
    L_1 = sqrt(gamma1)   * sigma_minus     (amplitude damping; sigma_minus=[[0,0],[1,0]])
    L_2 = sqrt(gammaphi) * sigma_z         (dephasing)

VECTORIZATION (column-stacking convention vec(A X B) = (B^T kron A) vec(X)):

    Lmat = -i (I kron H - H^T kron I)
         + sum_k [ conj(L_k) kron L_k
                   - 1/2 ( I kron (L_k^dag L_k) + (L_k^dag L_k)^T kron I ) ]
    rho(t) = unvec( expm(Lmat t) @ vec(rho0) ).

THREE EXECUTION PATHS over the SAME H, L_k:
  PRIMARY (torch)  : Lmat in torch.complex128; rho_torch(t)=unvec(matrix_exp(Lmat t) @ vec(rho0)).
  MIRROR-a (jax/diffrax, REAL Bloch path): rho=(I + r.sigma)/2; derive dr/dt = M r + c
       (purely REAL 3-vector ODE) from the SAME H, L_k; solve with Tsit5 + PIDController
       (diffrax's fully-supported real path).
  MIRROR-b (jax/diffrax, COMPLEX vec path): solve d vec(rho)/dt = Lmat vec(rho) with diffrax
       directly -- this exercises diffrax's self-flagged complex-dtype WIP path. The whole
       point is to see whether it AGREES with the exact torch matrix_exp.

BLOCH CONVENTION (ORDER-CHECKED; sigma_z = diag(1,-1)): rho = (I + r.sigma)/2, so
|0><0| has r=(0,0,+1) and |1><1| has r=(0,0,-1). The LITERAL operator
sigma_minus=[[0,0],[1,0]] sends |0>=(1,0) -> |1>=(0,1) and annihilates |1>; under the
(|0>,|1>) basis ordering this matrix is RAISING-type, so its amplitude-damping fixed
point is |1><1| (r_z=-1), NOT |0><0|. The Bloch equations DERIVED from these exact
operators (and confirmed against the torch matrix_exp drift) are
    dr_x/dt = -gamma2 r_x - omega r_y
    dr_y/dt = +omega  r_x - gamma2 r_y
    dr_z/dt = -gamma1 r_z - gamma1
with gamma2 = gamma1/2 + 2 gammaphi. Steady state r -> (0,0,-1) = |1><1| (the literal
sigma_minus fixed point). The DECAYING population is rho_00 = (1 + r_z)/2 ~ exp(-gamma1 t)
(T1=1/gamma1); transverse coherence |rho_01| = |r_x - i r_y|/2 decays at rate gamma2 (T2).
CONVENTION CONFLICT (recorded, not fudged): the task PROSE said the fixed point is the
ground |0><0| with excited population rho_11 decaying -- that holds only under the
OPPOSITE basis labelling. We keep the operator EXACTLY as specified and check the fixed
point / decaying population the literal operator actually produces.

DISAGREEMENT RULE: if torch and a jax sub-path disagree beyond tol (rho_delta > 1e-6),
it is recorded, that sub-path's pass is set False, and the suspect backend is named.
torch matrix_exp is exact; diffrax complex is WIP.

classification = "diagnostic_only", promotion_allowed = False. No validator gate.
"""

# JAX MUST be configured for float64 before any array is created. These two lines
# are deliberately the FIRST two executable statements.
import jax
jax.config.update("jax_enable_x64", True)

import json
import math
import pathlib
from typing import Any

import jax.numpy as jnp
import diffrax
import numpy as np
import torch

torch.set_default_dtype(torch.float64)

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL_TRACE = 1.0e-9          # |Tr rho - 1| tolerance
TOL_PSD = 1.0e-9            # min-eigenvalue floor for PSD
TOL_HERM = 1.0e-9           # Hermiticity defect tolerance
TOL_AGREE = 1.0e-6          # torch-vs-jax agreement tolerance (the disagreement gate)
TOL_KNOWN = 1.0e-9          # analytic known-value tolerance (matrix_exp is exact)
TOL_RATE = 1.0e-3           # T1/T2 fitted-rate relative-error tolerance
TOL_STEADY = 1.0e-3         # steady-state ||rho(T_big) - |0><0||| tolerance
TOL_GRAD = 1.0e-5           # |torch.autograd - jax.grad| purity gradient tolerance

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "terrain_gksl_dissipator_dual_backend_torch_jax_probe"

# Pauli matrices (exact). sigma_minus = [[0,0],[1,0]] (lowering operator).
I2_T = torch.eye(2, dtype=CDTYPE)
SX_T = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY_T = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ_T = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
SM_T = torch.tensor([[0, 0], [1, 0]], dtype=CDTYPE)   # sigma_minus (lowering)

# CONVENTION (order-checked): the LITERAL operator sigma_minus=[[0,0],[1,0]] sends
# |0>=(1,0) -> |1>=(0,1) and annihilates |1>. So under the (|0>,|1>) basis ordering
# this matrix is the RAISING-type operator and its amplitude-damping fixed point is
# |1><1|, NOT |0><0|. The decaying population is rho_00 (the |0> component). The task
# prose ("ground |0><0|", "excited population") assumes the opposite basis labelling;
# we keep the operator EXACTLY as specified and check the fixed point / decaying
# population that the literal operator actually produces, recording the convention
# conflict in the receipt rather than silently flipping the operator.
DAMP_FIXED_POINT_T = torch.tensor([[0, 0], [0, 1]], dtype=CDTYPE)   # |1><1| (the sigma_minus=[[0,0],[1,0]] fixed point)

I2_J = jnp.eye(2, dtype=jnp.complex128)
SX_J = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
SY_J = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ_J = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
SM_J = jnp.array([[0, 0], [1, 0]], dtype=jnp.complex128)


# --------------------------------------------------------------------------- #
# Shared operator builders                                                     #
# --------------------------------------------------------------------------- #
def H_torch(omega: float) -> torch.Tensor:
    return 0.5 * omega * SZ_T


def lindblad_ops_torch(gamma1: float, gammaphi: float) -> list[torch.Tensor]:
    return [math.sqrt(gamma1) * SM_T, math.sqrt(gammaphi) * SZ_T]


def lindbladian_superoperator_torch(omega: float, gamma1: float, gammaphi: float) -> torch.Tensor:
    """Build the 4x4 Lindbladian superoperator Lmat (column-stacking convention).

    vec(A X B) = (B^T kron A) vec(X). With this convention:
       -i[H, rho]      -> -i ( I kron H - H^T kron I )
       L rho L^dag     ->  conj(L) kron L
       {L^dag L, rho}  ->  I kron (L^dag L) + (L^dag L)^T kron I
    """
    H = H_torch(omega)
    Lmat = -1j * (torch.kron(I2_T, H) - torch.kron(H.T.contiguous(), I2_T))
    for L in lindblad_ops_torch(gamma1, gammaphi):
        LdL = L.conj().T @ L
        Lmat = Lmat + (
            torch.kron(L.conj(), L)
            - 0.5 * (torch.kron(I2_T, LdL) + torch.kron(LdL.T.contiguous(), I2_T))
        )
    return Lmat


def lindbladian_superoperator_jax(omega: float, gamma1: float, gammaphi: float) -> jnp.ndarray:
    H = 0.5 * omega * SZ_J
    Lmat = -1j * (jnp.kron(I2_J, H) - jnp.kron(H.T, I2_J))
    for L in [jnp.sqrt(jnp.asarray(gamma1, dtype=jnp.complex128)) * SM_J,
              jnp.sqrt(jnp.asarray(gammaphi, dtype=jnp.complex128)) * SZ_J]:
        LdL = jnp.conjugate(L.T) @ L
        Lmat = Lmat + (
            jnp.kron(jnp.conjugate(L), L)
            - 0.5 * (jnp.kron(I2_J, LdL) + jnp.kron(LdL.T, I2_J))
        )
    return Lmat


def vec_torch(rho: torch.Tensor) -> torch.Tensor:
    """Column-stacking vec: stack columns. For column-stacking, vec(X) flattens
    in column-major (Fortran) order."""
    return rho.T.reshape(-1)


def unvec_torch(v: torch.Tensor) -> torch.Tensor:
    return v.reshape(2, 2).T.contiguous()


def vec_jax(rho: jnp.ndarray) -> jnp.ndarray:
    return rho.T.reshape(-1)


def unvec_jax(v: jnp.ndarray) -> jnp.ndarray:
    return v.reshape(2, 2).T


# --------------------------------------------------------------------------- #
# PRIMARY: torch matrix_exp trajectory                                         #
# --------------------------------------------------------------------------- #
def rho_torch_traj(omega: float, gamma1: float, gammaphi: float,
                   rho0: torch.Tensor, ts) -> list[torch.Tensor]:
    """rho(t) = unvec( expm(Lmat t) @ vec(rho0) ) at each t in ts (exact)."""
    Lmat = lindbladian_superoperator_torch(omega, gamma1, gammaphi)
    v0 = vec_torch(rho0)
    out = []
    for t in ts:
        prop = torch.linalg.matrix_exp(Lmat * float(t))
        out.append(unvec_torch(prop @ v0))
    return out


# --------------------------------------------------------------------------- #
# MIRROR-a: REAL Bloch-vector ODE via diffrax Tsit5 + PIDController            #
# --------------------------------------------------------------------------- #
def bloch_M_c(omega: float, gamma1: float, gammaphi: float):
    """Real 3x3 drift M and constant c for dr/dt = M r + c, derived from the SAME
    H, L_k (sigma_minus damping + sigma_z dephasing). gamma2 = gamma1/2 + 2 gammaphi."""
    gamma2 = gamma1 / 2.0 + 2.0 * gammaphi
    M = jnp.array([
        [-gamma2, -omega, 0.0],
        [omega, -gamma2, 0.0],
        [0.0, 0.0, -gamma1],
    ], dtype=jnp.float64)
    # DERIVED from the LITERAL operator sigma_minus=[[0,0],[1,0]] (see CONVENTION
    # note below): this matrix maps |0>->|1> in the (|0>,|1>) basis ordering, so the
    # damping fixed point is |1><1| (r_z=-1), and dr_z/dt = -gamma1 r_z - gamma1.
    # The constant is -gamma1 (confirmed against the exact torch matrix_exp drift).
    c = jnp.array([0.0, 0.0, -gamma1], dtype=jnp.float64)   # steady r_z -> -1 (|1><1|)
    return M, c


def bloch_of_rho_jax(rho: jnp.ndarray) -> jnp.ndarray:
    rx = jnp.real(jnp.trace(rho @ SX_J))
    ry = jnp.real(jnp.trace(rho @ SY_J))
    rz = jnp.real(jnp.trace(rho @ SZ_J))
    return jnp.array([rx, ry, rz], dtype=jnp.float64)


def rho_of_bloch_jax(r: jnp.ndarray) -> jnp.ndarray:
    return 0.5 * (I2_J + r[0] * SX_J + r[1] * SY_J + r[2] * SZ_J)


def rho_jax_real_traj(omega: float, gamma1: float, gammaphi: float,
                      rho0: jnp.ndarray, ts) -> jnp.ndarray:
    """Solve the REAL Bloch ODE with diffrax Tsit5 + PIDController; return rho(t)."""
    M, c = bloch_M_c(omega, gamma1, gammaphi)
    r0 = bloch_of_rho_jax(rho0)

    def vf(t, y, args):
        return M @ y + c

    term = diffrax.ODETerm(vf)
    solver = diffrax.Tsit5()
    controller = diffrax.PIDController(rtol=1e-11, atol=1e-13)
    ts_arr = jnp.asarray(ts, dtype=jnp.float64)
    saveat = diffrax.SaveAt(ts=ts_arr)
    sol = diffrax.diffeqsolve(
        term, solver, t0=float(ts_arr[0]), t1=float(ts_arr[-1]), dt0=1e-4,
        y0=r0, saveat=saveat, stepsize_controller=controller, max_steps=1_000_000,
    )
    rhos = jax.vmap(rho_of_bloch_jax)(sol.ys)
    return rhos


# --------------------------------------------------------------------------- #
# MIRROR-b: COMPLEX vec(rho) ODE via diffrax directly (the WIP-caveat path)    #
# --------------------------------------------------------------------------- #
def rho_jax_complex_traj(omega: float, gamma1: float, gammaphi: float,
                         rho0: jnp.ndarray, ts) -> jnp.ndarray:
    """Solve d vec(rho)/dt = Lmat vec(rho) directly in complex128 with diffrax.
    This exercises diffrax's self-flagged complex-dtype WIP support."""
    Lmat = lindbladian_superoperator_jax(omega, gamma1, gammaphi)
    v0 = vec_jax(rho0)

    def vf(t, y, args):
        return Lmat @ y

    term = diffrax.ODETerm(vf)
    solver = diffrax.Tsit5()
    controller = diffrax.PIDController(rtol=1e-11, atol=1e-13)
    ts_arr = jnp.asarray(ts, dtype=jnp.float64)
    saveat = diffrax.SaveAt(ts=ts_arr)
    sol = diffrax.diffeqsolve(
        term, solver, t0=float(ts_arr[0]), t1=float(ts_arr[-1]), dt0=1e-4,
        y0=v0, saveat=saveat, stepsize_controller=controller, max_steps=1_000_000,
    )
    rhos = jax.vmap(unvec_jax)(sol.ys)
    return rhos


# --------------------------------------------------------------------------- #
# Invariants                                                                   #
# --------------------------------------------------------------------------- #
def trace_defect_torch(rho: torch.Tensor) -> float:
    return float((torch.trace(rho) - 1.0).abs().item())


def min_eig_torch(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().T) / 2
    return float(torch.linalg.eigvalsh(herm).real.min().item())


def herm_defect_torch(rho: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(rho - rho.conj().T).item())


def vn_entropy_torch(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().T) / 2
    w = torch.linalg.eigvalsh(herm).real
    w = torch.clamp(w, min=0.0)
    s = 0.0
    for x in w:
        xx = float(x.item())
        if xx > 1e-15:
            s -= xx * math.log(xx)
    return s


def purity_torch(rho: torch.Tensor) -> torch.Tensor:
    return torch.trace(rho @ rho).real


def jax_to_torch(rho_j: jnp.ndarray) -> torch.Tensor:
    return torch.tensor(np.asarray(rho_j), dtype=CDTYPE)


def fro_diff(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(a - b).item())


# --------------------------------------------------------------------------- #
# Gradients: d purity(rho(T))/d gamma1  (torch.autograd vs jax.grad)           #
# --------------------------------------------------------------------------- #
def purity_grad_torch(omega: float, gamma1: float, gammaphi: float,
                      rho0: torch.Tensor, T: float) -> float:
    g1 = torch.tensor(gamma1, dtype=RTYPE, requires_grad=True)
    H = 0.5 * omega * SZ_T
    L1 = torch.sqrt(g1.to(CDTYPE)) * SM_T
    L2 = math.sqrt(gammaphi) * SZ_T
    Lmat = -1j * (torch.kron(I2_T, H) - torch.kron(H.T.contiguous(), I2_T))
    for L in (L1, L2):
        LdL = L.conj().T @ L
        Lmat = Lmat + (
            torch.kron(L.conj(), L)
            - 0.5 * (torch.kron(I2_T, LdL) + torch.kron(LdL.T.contiguous(), I2_T))
        )
    v0 = vec_torch(rho0)
    prop = torch.linalg.matrix_exp(Lmat * T)
    rhoT = unvec_torch(prop @ v0)
    pur = torch.trace(rhoT @ rhoT).real
    pur.backward()
    return float(g1.grad.item())


def purity_grad_jax(omega: float, gamma1: float, gammaphi: float,
                    rho0: jnp.ndarray, T: float) -> float:
    def purity_of_g1(g1):
        H = 0.5 * omega * SZ_J
        L1 = jnp.sqrt(g1.astype(jnp.complex128)) * SM_J
        L2 = jnp.sqrt(jnp.asarray(gammaphi, dtype=jnp.complex128)) * SZ_J
        Lmat = -1j * (jnp.kron(I2_J, H) - jnp.kron(H.T, I2_J))
        for L in (L1, L2):
            LdL = jnp.conjugate(L.T) @ L
            Lmat = Lmat + (
                jnp.kron(jnp.conjugate(L), L)
                - 0.5 * (jnp.kron(I2_J, LdL) + jnp.kron(LdL.T, I2_J))
            )
        v0 = vec_jax(rho0)
        prop = jax.scipy.linalg.expm(Lmat * T)
        rhoT = unvec_jax(prop @ v0)
        return jnp.real(jnp.trace(rhoT @ rhoT))

    g1 = jnp.asarray(gamma1, dtype=jnp.float64)
    return float(jax.grad(purity_of_g1)(g1))


# --------------------------------------------------------------------------- #
# Trajectory comparison (torch vs both jax paths) over a parameter set         #
# --------------------------------------------------------------------------- #
def rho0_torch_from_bloch(r) -> torch.Tensor:
    rx, ry, rz = r
    return 0.5 * (I2_T + rx * SX_T + ry * SY_T + rz * SZ_T)


def rho0_jax_from_bloch(r) -> jnp.ndarray:
    rx, ry, rz = r
    return 0.5 * (I2_J + rx * SX_J + ry * SY_J + rz * SZ_J)


def compare_block(omega: float, gamma1: float, gammaphi: float,
                  bloch0, ts) -> dict[str, Any]:
    """Run all three paths on the SAME params, return per-t deltas + invariants."""
    rho0_t = rho0_torch_from_bloch(bloch0)
    rho0_j = rho0_jax_from_bloch(bloch0)

    rt = rho_torch_traj(omega, gamma1, gammaphi, rho0_t, ts)
    rj_real = rho_jax_real_traj(omega, gamma1, gammaphi, rho0_j, ts)
    rj_cplx = rho_jax_complex_traj(omega, gamma1, gammaphi, rho0_j, ts)

    rho_delta_real, rho_delta_cplx, ent_delta = [], [], []
    tr_t, eig_t, herm_t = [], [], []
    tr_jr, eig_jr, herm_jr = [], [], []
    tr_jc, eig_jc, herm_jc = [], [], []

    for i in range(len(ts)):
        rj_r = jax_to_torch(rj_real[i])
        rj_c = jax_to_torch(rj_cplx[i])
        rho_delta_real.append(fro_diff(rt[i], rj_r))
        rho_delta_cplx.append(fro_diff(rt[i], rj_c))
        ent_delta.append(abs(vn_entropy_torch(rt[i]) - vn_entropy_torch(rj_r)))

        tr_t.append(trace_defect_torch(rt[i]))
        eig_t.append(min_eig_torch(rt[i]))
        herm_t.append(herm_defect_torch(rt[i]))
        tr_jr.append(trace_defect_torch(rj_r))
        eig_jr.append(min_eig_torch(rj_r))
        herm_jr.append(herm_defect_torch(rj_r))
        tr_jc.append(trace_defect_torch(rj_c))
        eig_jc.append(min_eig_torch(rj_c))
        herm_jc.append(herm_defect_torch(rj_c))

    return {
        "omega": omega, "gamma1": gamma1, "gammaphi": gammaphi,
        "bloch0": list(bloch0),
        "max_rho_delta_real": max(rho_delta_real),
        "max_rho_delta_cplx": max(rho_delta_cplx),
        "max_entropy_delta": max(ent_delta),
        "torch_trace_defect": max(tr_t), "torch_min_eig": min(eig_t), "torch_herm_defect": max(herm_t),
        "jax_real_trace_defect": max(tr_jr), "jax_real_min_eig": min(eig_jr), "jax_real_herm_defect": max(herm_jr),
        "jax_cplx_trace_defect": max(tr_jc), "jax_cplx_min_eig": min(eig_jc), "jax_cplx_herm_defect": max(herm_jc),
    }


# --------------------------------------------------------------------------- #
# T1 / T2 decay-rate fit on the torch trajectory                               #
# --------------------------------------------------------------------------- #
def fit_decay_rate(ts, vals) -> float:
    """Fit ln(vals) = ln(v0) - rate t via least squares; return rate."""
    t = np.asarray(ts, dtype=np.float64)
    v = np.asarray(vals, dtype=np.float64)
    mask = v > 1e-12
    t, lv = t[mask], np.log(v[mask])
    A = np.vstack([t, np.ones_like(t)]).T
    sol, *_ = np.linalg.lstsq(A, lv, rcond=None)
    return float(-sol[0])


# --------------------------------------------------------------------------- #
# Known-value checks                                                           #
# --------------------------------------------------------------------------- #
def known_value_checks() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    aux: dict[str, Any] = {}

    # ---- Trace preservation + PSD across a parameter sweep, both backends ----
    param_set = [
        (1.0, 0.4, 0.0),    # amplitude damping only
        (2.0, 0.3, 0.15),   # full
        (0.5, 0.0, 0.25),   # dephasing only
        (1.5, 0.6, 0.2),    # full, faster
        (0.0, 0.2, 0.1),    # no precession
    ]
    bloch_inits = [
        (0.0, 0.0, -1.0),   # excited |1><1|
        (1.0, 0.0, 0.0),    # +x
        (0.0, 1.0, 0.0),    # +y
        (0.3, -0.4, 0.5),   # generic mixed (|r|<1)
    ]
    ts_main = [0.0, 0.2, 0.5, 1.0, 1.5, 2.0, 3.0]

    blocks = []
    for (om, g1, gp) in param_set:
        for b0 in bloch_inits:
            blocks.append(compare_block(om, g1, gp, b0, ts_main))
    aux["compare_blocks"] = blocks

    max_tr_t = max(b["torch_trace_defect"] for b in blocks)
    min_eig_t = min(b["torch_min_eig"] for b in blocks)
    max_herm_t = max(b["torch_herm_defect"] for b in blocks)
    max_tr_jr = max(b["jax_real_trace_defect"] for b in blocks)
    min_eig_jr = min(b["jax_real_min_eig"] for b in blocks)
    max_herm_jr = max(b["jax_real_herm_defect"] for b in blocks)
    max_tr_jc = max(b["jax_cplx_trace_defect"] for b in blocks)
    min_eig_jc = min(b["jax_cplx_min_eig"] for b in blocks)
    max_herm_jc = max(b["jax_cplx_herm_defect"] for b in blocks)

    max_delta_real = max(b["max_rho_delta_real"] for b in blocks)
    max_delta_cplx = max(b["max_rho_delta_cplx"] for b in blocks)
    max_ent_delta = max(b["max_entropy_delta"] for b in blocks)

    aux["max_rho_delta_real"] = max_delta_real
    aux["max_rho_delta_cplx"] = max_delta_cplx
    aux["max_entropy_delta"] = max_ent_delta

    checks.append({"invariant": "trace_preserved_Tr_rho(t)==1_torch",
                   "computed": f"max|Tr-1| = {max_tr_t:.2e}", "known": "1",
                   "match": max_tr_t < TOL_TRACE})
    checks.append({"invariant": "trace_preserved_Tr_rho(t)==1_jax_real",
                   "computed": f"max|Tr-1| = {max_tr_jr:.2e}", "known": "1",
                   "match": max_tr_jr < TOL_TRACE})
    checks.append({"invariant": "trace_preserved_Tr_rho(t)==1_jax_complex",
                   "computed": f"max|Tr-1| = {max_tr_jc:.2e}", "known": "1",
                   "match": max_tr_jc < TOL_TRACE})
    checks.append({"invariant": "CPTP_positivity_min_eig>=0_torch",
                   "computed": f"min_eig = {min_eig_t:.2e}", "known": ">= 0",
                   "match": min_eig_t > -TOL_PSD})
    checks.append({"invariant": "CPTP_positivity_min_eig>=0_jax_real",
                   "computed": f"min_eig = {min_eig_jr:.2e}", "known": ">= 0",
                   "match": min_eig_jr > -TOL_PSD})
    checks.append({"invariant": "CPTP_positivity_min_eig>=0_jax_complex",
                   "computed": f"min_eig = {min_eig_jc:.2e}", "known": ">= 0",
                   "match": min_eig_jc > -TOL_PSD})
    checks.append({"invariant": "Hermiticity_rho==rho^dag_torch",
                   "computed": f"max defect = {max_herm_t:.2e}", "known": "0",
                   "match": max_herm_t < TOL_HERM})
    checks.append({"invariant": "Hermiticity_rho==rho^dag_jax_real",
                   "computed": f"max defect = {max_herm_jr:.2e}", "known": "0",
                   "match": max_herm_jr < TOL_HERM})
    checks.append({"invariant": "Hermiticity_rho==rho^dag_jax_complex",
                   "computed": f"max defect = {max_herm_jc:.2e}", "known": "0",
                   "match": max_herm_jc < TOL_HERM})

    # ---- Amplitude-damping steady state (gammaphi=0): rho(T_big) -> |1><1| ----
    # (The literal sigma_minus=[[0,0],[1,0]] fixed point; see CONVENTION note.)
    om, g1, gp = 1.3, 0.8, 0.0
    rho0 = rho0_torch_from_bloch((0.6, -0.3, 0.7))   # toward the |0> end, mixed
    T_big = 40.0
    rhoT = rho_torch_traj(om, g1, gp, rho0, [T_big])[0]
    steady_err = fro_diff(rhoT, DAMP_FIXED_POINT_T)
    aux["amplitude_damping_steady_err"] = steady_err
    aux["amplitude_damping_fixed_point"] = "|1><1| (literal sigma_minus=[[0,0],[1,0]] fixed point; task prose said |0><0| under opposite basis labelling)"
    checks.append({"invariant": "amplitude_damping_steady_state(gammaphi=0)->sigma_minus_fixed_point(|1><1|)",
                   "computed": f"||rho(T=40) - |1><1||| = {steady_err:.2e}", "known": "0",
                   "match": steady_err < TOL_STEADY})

    # ---- T1 decay: the DECAYING population ~ exp(-gamma1 t) ----
    # Under sigma_minus=[[0,0],[1,0]] the |0> component decays, so rho_00 ~ exp(-gamma1 t).
    om, g1, gp = 0.0, 0.5, 0.0
    rho0 = rho0_torch_from_bloch((0.0, 0.0, 1.0))     # fully in |0><0|, the decaying end
    ts_fit = [0.1 * k for k in range(1, 25)]
    traj = rho_torch_traj(om, g1, gp, rho0, ts_fit)
    pe = [float(r[0, 0].real.item()) for r in traj]     # rho_00 = the decaying population
    rate_T1 = fit_decay_rate(ts_fit, pe)
    rel_T1 = abs(rate_T1 - g1) / g1
    aux["T1_fitted_rate"] = rate_T1
    aux["T1_analytic_gamma1"] = g1
    checks.append({"invariant": "T1_decaying_population(rho_00)_decay_rate==gamma1",
                   "computed": f"fitted = {rate_T1:.9f}, analytic gamma1 = {g1}",
                   "known": f"{g1}", "match": rel_T1 < TOL_RATE})

    # ---- T2 decay: coherence |rho_01| ~ exp(-gamma2 t), gamma2 = g1/2 + 2 gp ----
    om, g1, gp = 0.0, 0.4, 0.3      # omega=0 so coherence is a pure decaying real
    gamma2 = g1 / 2.0 + 2.0 * gp
    rho0 = rho0_torch_from_bloch((1.0, 0.0, 0.0))   # +x, max coherence
    traj = rho_torch_traj(om, g1, gp, rho0, ts_fit)
    coh = [float(r[0, 1].abs().item()) for r in traj]
    rate_T2 = fit_decay_rate(ts_fit, coh)
    rel_T2 = abs(rate_T2 - gamma2) / gamma2
    aux["T2_fitted_rate"] = rate_T2
    aux["T2_analytic_gamma2"] = gamma2
    checks.append({"invariant": "T2_coherence_decay_rate==gamma1/2+2gammaphi",
                   "computed": f"fitted = {rate_T2:.9f}, analytic gamma2 = {gamma2}",
                   "known": f"{gamma2}", "match": rel_T2 < TOL_RATE})

    # ---- Unitary limit (gamma1=gammaphi=0): purity preserved, precession about z ----
    om, g1, gp = 2.0, 0.0, 0.0
    rho0 = rho0_torch_from_bloch((1.0, 0.0, 0.0))   # +x pure
    ts_u = [0.0, 0.25, 0.5, 0.75, 1.0, math.pi / om, 2.0]
    traj = rho_torch_traj(om, g1, gp, rho0, ts_u)
    purities = [float(purity_torch(r).item()) for r in traj]
    pur_drift = max(abs(p - 1.0) for p in purities)
    aux["unitary_purity_drift"] = pur_drift
    # precession: Bloch vector rotates about z at frequency omega.
    # at t = pi/omega, +x -> -x (r_x = -1)
    r_half = rho0_jax_from_bloch  # noqa: (unused alias guard)
    rho_half = traj[5]
    rx_half = float(torch.trace(rho_half @ SX_T).real.item())
    precession_err = abs(rx_half - (-1.0))
    aux["unitary_precession_rx_at_pi_over_omega"] = rx_half
    checks.append({"invariant": "unitary_limit(g1=gp=0)_purity_Tr(rho^2)==1_preserved",
                   "computed": f"max|purity-1| = {pur_drift:.2e}", "known": "1",
                   "match": pur_drift < TOL_KNOWN})
    checks.append({"invariant": "unitary_limit_Bloch_precesses_about_z_freq_omega(r_x(pi/omega)=-1)",
                   "computed": f"r_x(pi/omega) = {rx_half:.12f}", "known": "-1",
                   "match": precession_err < 1e-7})

    return checks, aux


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    kvc, aux = known_value_checks()

    # ---- Owner comparison contract fields ----
    max_rho_delta_real = aux["max_rho_delta_real"]
    max_rho_delta_cplx = aux["max_rho_delta_cplx"]
    max_rho_delta = max(max_rho_delta_real, max_rho_delta_cplx)
    max_entropy_delta = aux["max_entropy_delta"]

    # gradient_delta: d purity(rho(T))/d gamma1, torch.autograd vs jax.grad
    g_omega, g_gamma1, g_gammaphi, g_T = 1.1, 0.35, 0.12, 1.0
    g_bloch0 = (0.5, 0.2, -0.6)
    rho0_t = rho0_torch_from_bloch(g_bloch0)
    rho0_j = rho0_jax_from_bloch(g_bloch0)
    grad_torch = purity_grad_torch(g_omega, g_gamma1, g_gammaphi, rho0_t, g_T)
    grad_jax = purity_grad_jax(g_omega, g_gamma1, g_gammaphi, rho0_j, g_T)
    gradient_delta = abs(grad_torch - grad_jax)
    aux["purity_grad_torch"] = grad_torch
    aux["purity_grad_jax"] = grad_jax

    # same_controls: both backends keep Tr=1, PSD, Hermitian for ALL sampled t.
    blocks = aux["compare_blocks"]
    torch_controls_ok = all(
        b["torch_trace_defect"] < TOL_TRACE and b["torch_min_eig"] > -TOL_PSD
        and b["torch_herm_defect"] < TOL_HERM for b in blocks)
    jax_real_controls_ok = all(
        b["jax_real_trace_defect"] < TOL_TRACE and b["jax_real_min_eig"] > -TOL_PSD
        and b["jax_real_herm_defect"] < TOL_HERM for b in blocks)
    jax_cplx_controls_ok = all(
        b["jax_cplx_trace_defect"] < TOL_TRACE and b["jax_cplx_min_eig"] > -TOL_PSD
        and b["jax_cplx_herm_defect"] < TOL_HERM for b in blocks)
    same_controls = bool(torch_controls_ok and jax_real_controls_ok and jax_cplx_controls_ok)

    # ---- Disagreement rule: real path and complex path each vs torch ----
    real_agrees = max_rho_delta_real <= TOL_AGREE
    cplx_agrees = max_rho_delta_cplx <= TOL_AGREE

    # Per-backend known_value_checks pass.
    # torch checks: every check naming "_torch" (or backend-agnostic analytic checks).
    torch_check_names = ("_torch", "amplitude_damping_steady", "T1_", "T2_", "unitary_")
    torch_checks = [c for c in kvc if any(n in c["invariant"] for n in torch_check_names)]
    torch_pass = bool(all(c["match"] for c in torch_checks))

    # jax checks: trace/PSD/Hermiticity on both jax paths, AND each jax path agrees with torch.
    jax_check_names = ("_jax_real", "_jax_complex")
    jax_checks = [c for c in kvc if any(n in c["invariant"] for n in jax_check_names)]
    jax_invariants_pass = all(c["match"] for c in jax_checks)
    jax_pass = bool(jax_invariants_pass and real_agrees and cplx_agrees)

    # ---- Blockers (anti-fabrication: record every non-match / disagreement) ----
    blockers: list[str] = []
    for c in kvc:
        if not c["match"]:
            blockers.append(f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}")
    if not real_agrees:
        blockers.append(
            f"DISAGREEMENT (real Bloch path): max||rho_torch - rho_jax_real|| = {max_rho_delta_real:.2e} > {TOL_AGREE:.0e}; "
            f"torch matrix_exp is exact, jax/diffrax REAL Bloch path is suspect")
    if not cplx_agrees:
        blockers.append(
            f"DISAGREEMENT (complex vec path): max||rho_torch - rho_jax_complex|| = {max_rho_delta_cplx:.2e} > {TOL_AGREE:.0e}; "
            f"torch matrix_exp is exact, diffrax COMPLEX-dtype path is WIP and is the suspect backend")
    if gradient_delta > TOL_GRAD:
        blockers.append(
            f"GRADIENT MISMATCH: |d purity/d gamma1 (torch.autograd) - (jax.grad)| = {gradient_delta:.2e} > {TOL_GRAD:.0e}")
    if not same_controls:
        if not torch_controls_ok:
            blockers.append("CONTROL VIOLATION: torch path broke Tr=1 / PSD / Hermitian on some t")
        if not jax_real_controls_ok:
            blockers.append("CONTROL VIOLATION: jax REAL path broke Tr=1 / PSD / Hermitian on some t")
        if not jax_cplx_controls_ok:
            blockers.append("CONTROL VIOLATION: jax COMPLEX path broke Tr=1 / PSD / Hermitian on some t")

    diffrax_complex_agrees = bool(cplx_agrees)
    diffrax_real_agrees = bool(real_agrees)
    gradient_match = gradient_delta <= TOL_GRAD

    all_pass = bool(torch_pass and jax_pass and same_controls and gradient_match)

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "PRIMARY runtime: builds the 4x4 Lindbladian superoperator in complex128 and computes rho(t)=unvec(matrix_exp(Lmat t) vec(rho0)) exactly; carries the autograd purity gradient d purity/d gamma1 through matrix_exp; all known-value invariants (trace, PSD, Hermiticity, steady state, T1/T2, unitary precession) are computed here"},
        "jax": {"used": True, "role": "load_bearing",
                "reason": "INDEPENDENT mirror runtime in float64 (jax_enable_x64); jax.grad gives the independent purity gradient via jax.scipy.linalg.expm; jax.vmap maps the diffrax solutions back to density matrices"},
        "diffrax": {"used": True, "role": "load_bearing",
                    "reason": "the ODE mirror: Tsit5 + PIDController solves the REAL Bloch-vector ODE (fully supported) and the COMPLEX vec(rho) ODE directly (self-flagged complex-dtype WIP path); agreement-with-torch is the cross-backend test"},
        "numpy": {"used": True, "role": "supportive",
                  "reason": "least-squares fit of the T1/T2 log-linear decay rates and dtype bridging of jax arrays into torch tensors for the Frobenius deltas; not a claim substrate"},
        "sympy": {"used": False, "role": None,
                  "reason": "no symbolic step needed for this dynamics probe; the analytic Bloch/T1/T2/steady-state values are the known-value proof surface and are checked numerically against the exact torch matrix_exp"},
        "z3": {"used": False, "role": None,
               "reason": "kept OUT of the hot loop by design; PSD/trace-1 are checked directly as min-eigenvalue and trace defects per the task contract (no SMT wrap on the dynamics)"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_dynamics",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "dynamics_probe",
        "purpose": "Reference dual-backend GKSL/Lindblad single-qubit dissipator ('terrain motion'): PyTorch matrix_exp (PRIMARY) vs JAX/diffrax (INDEPENDENT mirror, REAL Bloch + COMPLEX vec sub-paths), cross-checked against textbook open-quantum-system invariants (trace, CPTP positivity, amplitude-damping steady state, T1/T2 decay rates, unitary precession).",
        "scientific_question": "Does the GKSL master equation for H=(omega/2)sigma_z with amplitude damping (sqrt(gamma1) sigma_minus) and dephasing (sqrt(gammaphi) sigma_z) reproduce the known open-system invariants, and do the PyTorch matrix_exp path and the two JAX/diffrax paths (real Bloch ODE, complex vec ODE) agree on rho(t), entropy, and the purity gradient?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math open-quantum-system dynamics witness with a dual-backend cross-check. Does NOT admit any manifold layer, stacking, coupling, G-structure, Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(omega, gamma1, gammaphi, rho0, t) -> rho(t) via GKSL; reported through torch matrix_exp and jax/diffrax (real Bloch ODE + complex vec ODE)",
        "domain": "single-qubit density operators rho0 (pure + mixed Bloch initial conditions), real (omega, gamma1, gammaphi) parameter triples, a time grid",
        "codomain_or_output": "time-evolved density operators rho(t), their von Neumann entropies, purities, and the purity gradient w.r.t. gamma1",
        "carrier_layer": "single-qubit density operator under GKSL flow (the Bloch ball, contracted by dissipation)",
        "geometry_layer": "Lindblad-contracted Bloch dynamics: precession about z at frequency omega, transverse decay at gamma2, longitudinal decay to the ground state at gamma1",
        "carrier_realization": "torch.complex128 superoperator + matrix_exp (PRIMARY); jax float64/complex128 + diffrax Tsit5 ODE solves (MIRROR); no NumPy claim substrate, no hardcoded matches, no random claim matrices",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "single-qubit GKSL/Lindblad dissipative dynamics against textbook open-system invariants, with a PyTorch-vs-JAX/diffrax dual-backend cross-check",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math dynamics; unadmitted",
        "allowed_claims": ["standalone known-math GKSL dynamics witness; computed invariants match textbook values; reports whether the two backends agree"],
        "convention_note": "ORDER-CHECKED: the literal operator sigma_minus=[[0,0],[1,0]] maps |0>->|1> in the (|0>,|1>) basis ordering, so its amplitude-damping fixed point is |1><1| (r_z=-1) and the decaying population is rho_00 ~ exp(-gamma1 t). The task prose said the fixed point is the ground |0><0| with rho_11 decaying; that holds only under the opposite basis labelling. The operator was kept EXACTLY as specified and the checks target the fixed point / decaying population the literal operator actually produces; the conflict is recorded here rather than resolved by silently flipping the operator.",
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        # ---- OWNER COMPARISON CONTRACT (top-level) ----
        "torch_pass": torch_pass,
        "jax_pass": jax_pass,
        "max_rho_delta": float(max_rho_delta),
        "max_entropy_delta": float(max_entropy_delta),
        "gradient_delta": float(gradient_delta),
        "same_controls": same_controls,

        "comparison_contract": {
            "torch_pass": torch_pass,
            "jax_pass": jax_pass,
            "max_rho_delta": float(max_rho_delta),
            "max_rho_delta_real_bloch_vs_torch": float(max_rho_delta_real),
            "max_rho_delta_complex_vec_vs_torch": float(max_rho_delta_cplx),
            "max_entropy_delta": float(max_entropy_delta),
            "gradient_delta": float(gradient_delta),
            "purity_grad_torch_autograd": float(grad_torch),
            "purity_grad_jax_grad": float(grad_jax),
            "same_controls": same_controls,
            "agreement_tol": TOL_AGREE,
            "diffrax_real_bloch_agrees_with_torch": diffrax_real_agrees,
            "diffrax_complex_vec_agrees_with_torch": diffrax_complex_agrees,
            "suspect_backend_if_disagree": "diffrax (complex-dtype WIP) -- torch matrix_exp is exact",
        },

        "result_summary": {
            "all_pass": all_pass,
            "torch_pass": torch_pass,
            "jax_pass": jax_pass,
            "same_controls": same_controls,
            "gradient_match": gradient_match,
            "diffrax_complex_agrees": diffrax_complex_agrees,
            "diffrax_real_agrees": diffrax_real_agrees,
            "max_rho_delta": float(max_rho_delta),
            "max_entropy_delta": float(max_entropy_delta),
            "gradient_delta": float(gradient_delta),
            "n_known_value_checks": len(kvc),
            "n_compare_blocks": len(blocks),
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "known_value_aux": aux,

        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "torch path or a jax path breaks Tr=1 / PSD / Hermiticity at any sampled t",
            "the torch and jax-real Bloch trajectories disagree beyond 1e-6",
            "the torch and diffrax-complex vec trajectories disagree beyond 1e-6 (WIP-path test)",
            "the torch.autograd and jax.grad purity gradients disagree beyond 1e-5",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "jax": "load_bearing",
                                   "diffrax": "load_bearing", "numpy": "supportive",
                                   "sympy": None, "z3": None},
        "required_tools": ["torch", "jax", "diffrax"],
        "actual_tools_used": ["torch", "jax", "diffrax", "numpy"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "torch_pass (all torch+analytic known-value checks match) AND jax_pass (both jax paths preserve Tr/PSD/Hermiticity AND agree with torch within 1e-6) AND same_controls AND the torch.autograd-vs-jax.grad purity gradient matches within 1e-5",
        "fail_rule": "any known-value mismatch, any control violation, any backend disagreement beyond tol, or a gradient mismatch -- all recorded in blockers, none fudged",
        "eligible_consumers": ["other diagnostic_only open-quantum-system dynamics probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "build_lindbladian_superoperator", "convention": "column-stacking vec(AXB)=(B^T kron A)vec(X)", "tool": "torch.complex128 + jax.complex128"},
            {"step": "torch_matrix_exp_trajectory_PRIMARY", "tool": "torch.linalg.matrix_exp", "n_compare_blocks": len(blocks)},
            {"step": "jax_diffrax_real_bloch_ODE_MIRROR_a", "solver": "Tsit5+PIDController", "agrees_with_torch": diffrax_real_agrees, "max_delta": max_rho_delta_real},
            {"step": "jax_diffrax_complex_vec_ODE_MIRROR_b_WIP", "solver": "Tsit5+PIDController", "agrees_with_torch": diffrax_complex_agrees, "max_delta": max_rho_delta_cplx},
            {"step": "entropy_delta", "max_entropy_delta": max_entropy_delta},
            {"step": "purity_gradient_torch_autograd_vs_jax_grad", "grad_torch": grad_torch, "grad_jax": grad_jax, "gradient_delta": gradient_delta},
            {"step": "known_value_cross_checks", "n": len(kvc), "all_match": all(c["match"] for c in kvc)},
        ],
        "final_classification": "diagnostic_only",
        "all_pass": all_pass,
        "blockers": blockers,
    }

    out = RESULT_DIR / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    wit = RESULT_DIR / f"{SIM_ID}_witness.json"
    wit.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "wrote": str(out),
        "witness": str(wit),
        "all_pass": all_pass,
        "torch_pass": torch_pass,
        "jax_pass": jax_pass,
        "max_rho_delta": float(max_rho_delta),
        "max_rho_delta_real": float(max_rho_delta_real),
        "max_rho_delta_complex": float(max_rho_delta_cplx),
        "max_entropy_delta": float(max_entropy_delta),
        "gradient_delta": float(gradient_delta),
        "same_controls": same_controls,
        "diffrax_complex_agrees": diffrax_complex_agrees,
        "diffrax_real_agrees": diffrax_real_agrees,
        "blockers": blockers,
        "known_value_checks": [{"invariant": c["invariant"], "computed": c["computed"],
                                "known": c["known"], "match": c["match"]} for c in kvc],
    }, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
