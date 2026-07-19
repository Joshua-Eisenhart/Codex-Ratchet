#!/usr/bin/env python3
"""Nested-manifold engine leg — JAX replication of manifold_one.py.

Replicates the rung-ONE tick loop (the base run only: grow / propagate /
flux / nest / lock) with every density-matrix, entropy, holonomy, and
Schur-complement computation done in jax.numpy at float64/complex128.
The combinatorial drive (packet growth, dC, gamma) is exact scalar math
shared with the numpy reference by construction; the parity question this
leg answers is whether an INDEPENDENT linear-algebra substrate reproduces
the 30-tick entropy series of the committed numpy receipt
(results/manifold_one/receipt.json).

Contract: max abs elementwise diff over each of the series
S_L, S_R, S_LR, I, I_c, negativity, Phi0, flux must be < 1e-8 against the
numpy receipt. The gate can FAIL (a float32 run, a vec-convention slip, or
a transposed partial trace all blow past 1e-8 by orders of magnitude).

Engine-estate rule: this process loads ONLY the JAX stack (no torch, no
julia) and fully exits when done.

Claim ceiling: engine-parity probe on an executed finite instance;
scratch_diagnostic; promotion_allowed=false; no new physics claim.
"""
import json
import math
import sys
from pathlib import Path

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

HERE = Path(__file__).resolve().parent
NUMPY_RECEIPT = HERE.parent / "results" / "manifold_one" / "receipt.json"
OUT = HERE.parent / "results" / "manifold_one_jax"

# ---- constants traced to manifold_one.py (must match exactly) ----------
N_TICKS = 30
TICK_DT = 0.4
NSUB = 8
NSUB_OUT = 8
N_LOOP = 200
OMEGA, ALPHA = 1.3, 0.7
J_XY = 0.35
GAMMA_BASE = 0.6
ETA1 = 0.2
A_SCHED = [3 + ((t + 1) % 3) for t in range(N_TICKS)]
OUTER = {"Delta4": 1.0, "Delta5": 1.5, "gph": 0.1,
         "g": 0.5, "g2": 0.35, "k_out": 0.8}
CUT_W = (0.5, 0.5)

I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
SM = jnp.array([[0, 1], [0, 0]], dtype=jnp.complex128)


# ---- rung-A machinery (jax) --------------------------------------------
def spinor(eta, phi, chi):
    return jnp.array([jnp.exp(1j * phi) * jnp.cos(eta),
                      jnp.exp(1j * chi) * jnp.sin(eta)])


def chi_loop(eta, phi0=0.3):
    ts = jnp.linspace(0, 2 * jnp.pi, N_LOOP, endpoint=False)
    return [spinor(eta, phi0, t) for t in ts]


def loop_holonomy(points):
    tot = 0.0
    for k in range(len(points)):
        tot += float(jnp.angle(jnp.vdot(points[k],
                                        points[(k + 1) % len(points)])))
    return tot


# ---- rung-C machinery (jax) --------------------------------------------
def vn_entropy(rho):
    w = jnp.linalg.eigvalsh(rho)
    w = w[w > 1e-14]
    return float(-(w * jnp.log2(w)).sum())


def ptrace(rho, keep):
    r = rho.reshape(2, 2, 2, 2)
    if keep == "L":
        return jnp.trace(r, axis1=1, axis2=3)
    return jnp.trace(r, axis1=0, axis2=2)


def negativity(rho):
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    w = jnp.linalg.eigvalsh(pt)
    return float(-w[w < 0].sum())


def cut_readouts(rho):
    S_L = vn_entropy(ptrace(rho, "L"))
    S_R = vn_entropy(ptrace(rho, "R"))
    S_LR = vn_entropy(rho)
    Ic_LR = -(S_LR - S_R)
    Ic_RL = -(S_LR - S_L)
    w1, w2 = CUT_W
    return {"S_L": S_L, "S_R": S_R, "S_LR": S_LR,
            "I": S_L + S_R - S_LR, "I_c": Ic_LR,
            "negativity": negativity(rho),
            "Phi0": w1 * Ic_LR + w2 * Ic_RL}


# ---- rung-B machinery (jax) --------------------------------------------
def build_joint_h():
    nx, nz = math.sin(ALPHA), math.cos(ALPHA)
    H_L = 0.5 * OMEGA * (nx * SX + nz * SZ)
    H_R = -H_L
    return (jnp.kron(H_L, I2) + jnp.kron(I2, H_R)
            + J_XY * (jnp.kron(SX, SX) + jnp.kron(SY, SY)))


def bank_jumps(stage, gamma):
    if gamma <= 0.0:
        return []
    if stage == 0:
        return ([jnp.sqrt(gamma / 4) * jnp.kron(s, I2)
                 for s in (SX, SY, SZ)]
                + [jnp.sqrt(gamma / 4) * jnp.kron(I2, s.conj())
                   for s in (SX, SY, SZ)])
    if stage == 1:
        return [jnp.sqrt(gamma) * jnp.kron(SZ, I2),
                jnp.sqrt(gamma) * jnp.kron(I2, SZ.conj())]
    return [jnp.sqrt(gamma) * jnp.kron(SM, I2),
            jnp.sqrt(gamma) * jnp.kron(I2, SM.conj())]


def gksl_rhs(rho, H, Ls):
    d = -1j * (H @ rho - rho @ H)
    for L in Ls:
        Ld = L.conj().T
        d += L @ rho @ Ld - 0.5 * (Ld @ L @ rho + rho @ Ld @ L)
    return d


def evolve_tick(rho, H, Ls):
    dt = TICK_DT / NSUB
    for _ in range(NSUB):
        k1 = gksl_rhs(rho, H, Ls)
        k2 = gksl_rhs(rho + 0.5 * dt * k1, H, Ls)
        k3 = gksl_rhs(rho + 0.5 * dt * k2, H, Ls)
        k4 = gksl_rhs(rho + dt * k3, H, Ls)
        rho = rho + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        rho = 0.5 * (rho + rho.conj().T)
    return rho


# ---- rung-D machinery (jax) --------------------------------------------
def op6(i, j):
    return jnp.zeros((6, 6), dtype=jnp.complex128).at[i, j].set(1.0)


def liouvillian(H, jumps):
    d = H.shape[0]
    I = jnp.eye(d, dtype=jnp.complex128)
    L = -1j * (jnp.kron(I, H) - jnp.kron(H.T, I))
    for K in jumps:
        KdK = K.conj().T @ K
        L += (jnp.kron(K.conj(), K)
              - 0.5 * jnp.kron(I, KdK) - 0.5 * jnp.kron(KdK.T, I))
    return L


def build_outer_schur():
    c = OUTER
    H = (c["Delta4"] * op6(4, 4) + c["Delta5"] * op6(5, 5)
         + c["g"] * (op6(3, 4) + op6(4, 3))
         + c["g2"] * (op6(0, 5) + op6(5, 0)))
    jumps = [jnp.sqrt(c["k_out"]) * op6(1, 4),
             jnp.sqrt(c["k_out"]) * op6(2, 5),
             jnp.sqrt(c["gph"]) * (op6(4, 4) - op6(5, 5))]
    L = liouvillian(H, jumps)
    P = [i + 6 * j for j in range(4) for i in range(4)]
    Q = [n for n in range(36) if n not in P]
    L_II = L[jnp.ix_(jnp.array(P), jnp.array(P))]
    L_IO = L[jnp.ix_(jnp.array(P), jnp.array(Q))]
    L_OI = L[jnp.ix_(jnp.array(Q), jnp.array(P))]
    L_OO = L[jnp.ix_(jnp.array(Q), jnp.array(Q))]
    L_eff = L_II - L_IO @ jnp.linalg.solve(L_OO, L_OI)
    h = TICK_DT / NSUB_OUT
    A = h * L_eff
    P_step = (jnp.eye(16) + A + A @ A / 2.0
              + A @ A @ A / 6.0 + A @ A @ A @ A / 24.0)
    M_tick = jnp.linalg.matrix_power(P_step, NSUB_OUT)
    return M_tick


def apply_outer(rho, M_tick):
    v = rho.T.flatten()                     # column-stack == flatten(order="F")
    v = M_tick @ v
    r = v.reshape((4, 4)).T
    r = 0.5 * (r + r.conj().T)
    w, U = jnp.linalg.eigh(r)
    w = jnp.clip(w, 0.0, None)
    r = (U * w) @ U.conj().T
    return r / jnp.trace(r).real


# ---- the tick loop (base run only; drive is exact shared scalar math) --
def run():
    class_counts = [1, 1, 1, 0, 0]
    rho = None
    rho0_L = 0.5 * (I2 + 0.5 * SX + 0.3 * SY - 0.4 * SZ)
    rho = jnp.kron(rho0_L, rho0_L.conj())
    M_tick = build_outer_schur()
    H = build_joint_h()
    series = {k: [] for k in ("dC", "flux", "S_L", "S_R", "S_LR",
                              "I", "I_c", "negativity", "Phi0")}
    for t in range(N_TICKS):
        a = A_SCHED[t]
        old_total = sum(class_counts)
        class_counts = [old_total - class_counts[x] if x < a else 0
                        for x in range(5)]
        dC = math.log(sum(class_counts)) - math.log(old_total)
        stage = t // 10
        gamma = GAMMA_BASE * dC / math.log(4)
        rho = evolve_tick(rho, H, bank_jumps(stage, gamma))
        p1L = float(jnp.real(ptrace(rho, "L")[1, 1]))
        eta2 = 0.3 + 0.4 * min(max(p1L, 0.0), 1.0)
        flux = loop_holonomy(chi_loop(ETA1)) - loop_holonomy(chi_loop(eta2))
        rho = apply_outer(rho, M_tick)
        cr = cut_readouts(rho)
        series["dC"].append(dC)
        series["flux"].append(flux)
        for k in ("S_L", "S_R", "S_LR", "I", "I_c", "negativity", "Phi0"):
            series[k].append(cr[k])
    return series


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")
    if not NUMPY_RECEIPT.exists():
        raise SystemExit(f"numpy receipt missing: {NUMPY_RECEIPT}")
    OUT.mkdir(parents=True)
    ref = json.loads(NUMPY_RECEIPT.read_text())["data"]["series"]

    checks, data, findings = {}, {}, []
    checks["x64_enabled"] = bool(jax.config.jax_enable_x64)
    data["jax_backend"] = jax.default_backend()

    series = run()
    gate = 1e-8
    diffs = {}
    for k in ("S_L", "S_R", "S_LR", "I", "I_c", "negativity", "Phi0",
              "flux", "dC"):
        d = max(abs(a - b) for a, b in zip(series[k], ref[k]))
        diffs[k] = d
    data["max_abs_diff_vs_numpy_receipt"] = diffs
    data["gate"] = gate
    entropy_keys = ("S_L", "S_R", "S_LR", "I", "I_c", "Phi0")
    checks["parity_entropy_series_lt_1e-8"] = bool(
        all(diffs[k] < gate for k in entropy_keys))
    checks["parity_negativity_lt_1e-8"] = bool(diffs["negativity"] < gate)
    checks["parity_flux_lt_1e-8"] = bool(diffs["flux"] < gate)
    checks["drive_scalar_identical"] = bool(diffs["dC"] == 0.0)
    checks["series_complete_30"] = bool(
        all(len(series[k]) == N_TICKS for k in series))

    data["S_L_series_jax"] = series["S_L"]
    data["Phi0_series_jax"] = series["Phi0"]

    findings += [
        "jax leg runs eagerly (no jit/vmap): the parity target is the "
        "committed numpy trajectory, and eager float64 keeps the "
        "operation order comparable; jit is a declared non-goal here",
        "the combinatorial drive (dC, gamma) is exact scalar math.log "
        "arithmetic, identical by construction (diff 0.0 recorded); the "
        "independent content of this leg is the linear algebra: eigh, "
        "solve, matrix_power, RK4 GKSL, partial trace, holonomy angles",
    ]

    receipt = {
        "schema": "ratchet.v8.nested-manifold.engine-leg.jax.v0",
        "engine": "jax", "float64": checks["x64_enabled"],
        "reference": str(NUMPY_RECEIPT),
        "checks": {k: bool(v) for k, v in checks.items()},
        "data": data, "findings": findings,
        "all_pass": bool(all(checks.values())),
        "promotion_allowed": False, "formal_admission_allowed": False,
        "claim_ceiling": ("engine-parity probe: jax float64 replication of "
                          "the rung-ONE base tick loop vs the numpy "
                          "receipt; scratch_diagnostic; no new claim"),
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"rung": "ENG-jax", "all_pass": receipt["all_pass"],
                      "checks": receipt["checks"],
                      "max_abs_diffs": diffs}, indent=2, default=float))
    sys.exit(0 if receipt["all_pass"] else 1)


if __name__ == "__main__":
    main()
