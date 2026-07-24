#!/usr/bin/env python3
"""Type-1 DEDUCTIVE outer loop — JAX leg (base workhorse, jax.numpy x64, no numpy).

ONE loop of the IGT engine, run as an engine cycle. Type-1 => left Weyl sheet,
s=+1, H_L=+H0. Deductive/outer loop = FeTi family (Ti,Fe), z-axis operators,
terrain visit order Se -> Ne -> Ni -> Si.

Stage math (Axis-6: UP=operator-first Phi_T o O ; DOWN=terrain-first O o Phi_T):
  1 Se, Ti^  (LOSE): rho -> Phi_Se( O_Ti(rho) )
  2 Ne, Ti_  (WIN) : rho -> O_Ti( Phi_Ne(rho) )
  3 Ni, Fe_  (LOSE): rho -> O_Fe( Phi_Ni(rho) )
  4 Si, Fe^  (WIN) : rho -> Phi_Si( O_Fe(rho) )

Terrain generators (s=+1, D[L]rho = L rho L^dag - 1/2{L^dag L, rho}):
  Se: L_Se(rho) = D[sqrt(gF) sz](rho)          - i eF [H0,rho]
  Ne: L_Ne(rho) =                                - i    [H0,rho] + eV D[sqrt(gV) sx](rho)
  Ni: L_Ni(rho) = D[sqrt(gP) s-](rho)          - i eP [H0,rho]
  Si: L_Si(rho) = kap(P0 rho P0+P1 rho P1 - 1/2{P0+P1,rho}) - i [w sz, rho]   ([H_C,P_j]=0)
Operators (live-engine set): O_Ti = z-dephasing(q); O_Fe = U_z(phi) rho U_z^dag.

STATUS: candidate engine-cycle probe. classification tool_lego_fit_probe;
promotion_allowed=false. Terrain generators are the doc's CANDIDATE instantiation
(Ni uses structural s-; the 2x2 table's sy is the rival). NOT canon, NOT admission.
"""
import json
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax.scipy.linalg import expm

I = jnp.eye(2, dtype=jnp.complex128)
sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
sm = jnp.array([[0, 0], [1, 0]], dtype=jnp.complex128)  # sigma_-  (|0><1|? convention: lowers)
P0 = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128)
P1 = jnp.array([[0, 0], [0, 1]], dtype=jnp.complex128)

# ---- fixed engine parameters (declared, frozen before outcomes) ----
NVEC = jnp.array([0.6, 0.0, 0.8])           # unit-ish drive axis n
H0 = NVEC[0] * sx + NVEC[1] * sy + NVEC[2] * sz
S_SIGN = +1.0                                # Type-1 left sheet: -i s [H0,.]
GAMMA = {"F": 0.6, "V": 0.6, "P": 0.6, "Si": 0.6}
EPS = {"F": 0.9, "V": 1.0, "P": 0.9}
W_SI = 0.8                                    # H_C = W_SI sz  ([H_C,P_j]=0)
TAU = 0.5                                     # stage integration time
NSTEP = 200                                   # substeps per stage
Q_TI = 0.5                                    # Ti dephasing strength
PHI_FE = 0.7                                  # Fe z-rotation angle (Type-1: +phi)


# ---- exact Lindblad propagator via superoperator expm (C-order vec) ----
# vec_C(A X B) = (A kron B^T) vec_C(X);  -i[H,.] = -i(H kron I - I kron H^T)
# D[L] = (L kron conj(L)) - 1/2( (Ld L) kron I ) - 1/2( I kron (Ld L)^T )
IK = jnp.eye(2, dtype=jnp.complex128)


def _super_H(H):
    return -1j * (jnp.kron(H, IK) - jnp.kron(IK, H.T))


def _super_D(L):
    Ld = L.conj().T
    LdL = Ld @ L
    return jnp.kron(L, L.conj()) - 0.5 * jnp.kron(LdL, IK) - 0.5 * jnp.kron(IK, LdL.T)


def _liouvillian(H_eff, jumps):
    Ls = _super_H(H_eff)
    for L in jumps:
        Ls = Ls + _super_D(L)
    return Ls


# terrain generators — EXACT per "terrain math.md" §Eight Terrain Generators (Type-1, s=+1):
#   Se/Funnel  X = lambda_Se * sum_{j=x,y,z} D[sigma_j] - i eps_Se [H0,.]   (DEPOLARIZING + Ham)
#   Ne/Vortex  X = -i[H0,.]                                                 (PURE Hamiltonian, no jumps)
#   Ni/Pit     X = gamma_Ni D[sigma_-] - i eps_Ni [H0,.]                    (sink + Ham)
#   Si/Hill    X = -i[omega m.sigma,.] + kappa(P+ rho P+ + P- rho P- - rho) (dephase in m-basis + Ham); m=z
# rates are the doc's free parameters (lambda,eps,gamma,kappa,omega), declared here.
def _terr_Se():
    j = jnp.sqrt(GAMMA["F"])
    return S_SIGN * EPS["F"] * H0, [j * sx, j * sy, j * sz]      # depolarizing (all 3 Paulis)


def _terr_Ne():
    return S_SIGN * H0, []                                        # PURE Hamiltonian circulation


def _terr_Ni():
    return S_SIGN * EPS["P"] * H0, [jnp.sqrt(GAMMA["P"]) * sm]


def _terr_Si():
    return S_SIGN * W_SI * sz, [jnp.sqrt(GAMMA["Si"]) * P0, jnp.sqrt(GAMMA["Si"]) * P1]


def flow_terr(terr, rho, tau=TAU):
    H_eff, jumps = terr()
    Ls = _liouvillian(H_eff, jumps)
    prop = expm(Ls * tau)                       # exact propagator over the stage
    rho_vec = rho.reshape(-1)
    out = (prop @ rho_vec).reshape(2, 2)
    return 0.5 * (out + out.conj().T) / jnp.trace(out).real   # hermitize+renorm rounding


def lind_flow_Se(rho): return flow_terr(_terr_Se, rho)
def lind_flow_Ne(rho): return flow_terr(_terr_Ne, rho)
def lind_flow_Ni(rho): return flow_terr(_terr_Ni, rho)
def lind_flow_Si(rho): return flow_terr(_terr_Si, rho)


def O_Ti(rho):                             # z-dephasing channel
    return (1 - Q_TI) * rho + Q_TI * (P0 @ rho @ P0 + P1 @ rho @ P1)


def O_Fe(rho):                             # z-rotation unitary, Type-1 +phi
    Uz = expm(-1j * PHI_FE * sz / 2)
    return Uz @ rho @ Uz.conj().T


def vN(rho):
    w = jnp.linalg.eigvalsh(rho)
    w = jnp.clip(w.real, 1e-12, 1.0)
    return float(-jnp.sum(w * jnp.log(w)))


def stage1(rho):  # Se, Ti^  operator-first
    return lind_flow_Se(O_Ti(rho))


def stage2(rho):  # Ne, Ti_  terrain-first
    return O_Ti(lind_flow_Ne(rho))


def stage3(rho):  # Ni, Fe_  terrain-first
    return O_Fe(lind_flow_Ni(rho))


def stage4(rho):  # Si, Fe^  operator-first
    return lind_flow_Si(O_Fe(rho))


def run_loop(rho):
    s1 = stage1(rho); s2 = stage2(s1); s3 = stage3(s2); s4 = stage4(s3)
    return [rho, s1, s2, s3, s4]


def main():
    # engine cycle from a fixed pure-ish start
    rho0 = 0.5 * (I + 0.5 * sx + 0.3 * sz)
    traj = run_loop(rho0)
    ent = [vN(r) for r in traj]
    rho_out = traj[-1]

    # cycle observables
    dS_loop = ent[-1] - ent[0]                                   # net entropy around the closed loop
    purity_out = float(jnp.trace(rho_out @ rho_out).real)
    # irreversibility: forward loop vs REVERSED-order loop on same start (engine non-commutation)
    rev = stage1(stage2(stage3(stage4(rho0))))
    loop_noncomm = float(jnp.linalg.norm(rho_out - rev))         # >0 => order is load-bearing
    # commuting control: all four terrains -> pure z-dephasing (mutually commuting) => order irrelevant
    def zterr():
        return jnp.zeros((2, 2), dtype=jnp.complex128), [jnp.sqrt(0.6) * sz]
    def zflow(rho):
        return flow_terr(zterr, rho)
    a = zflow(zflow(zflow(zflow(rho0))))          # some fixed order
    b = zflow(zflow(zflow(zflow(rho0))))          # reversed is identical (all commute) -> use dephase-then-rot swap
    # meaningful control: swap Ti/Fe order on a z-only loop; z-dephase and z-rot commute -> 0
    c1 = O_Fe(O_Ti(rho0)); c2 = O_Ti(O_Fe(rho0))
    ctrl_noncomm = float(jnp.linalg.norm(c1 - c2))

    out = {
        "engine": "jax:x64",
        "loop": "type1_deductive_outer",
        "terrain_order": "Se->Ne->Ni->Si",
        "operators": "Ti,Fe (FeTi/z-family)",
        "vN_entropy_trajectory": ent,
        "dS_loop": dS_loop,
        "purity_out": purity_out,
        "loop_noncomm_fwd_vs_rev": loop_noncomm,
        "commuting_control_noncomm": ctrl_noncomm,
        "ran": True,
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
