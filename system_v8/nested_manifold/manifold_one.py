#!/usr/bin/env python3
"""Nested-manifold runtime — Rung ONE: the single integrated manifold sim.

Composes the already-verified rungs A-E as ONE coupled object. Nothing here
is a new physics claim; every ingredient is the executed machinery of a
prior rung, now running inside one tick loop on one shared state:

  rung A -> leaf coordinate eta, U(1) connection links (Pancharatnam),
            flux = relative holonomy of the chi-loop class on two leaves.
  rung B -> generator bank (depolarizing G1, dephasing = GKSL limit of the
            pinching row G7, amplitude damping G3) on the two conjugate
            sheets (H_R = -H_L, right jumps = conj(left jumps)).
  rung C -> joint carrier rho_LR, cut readouts S_L, S_R, S_LR, I(L:R),
            I_c, negativity, Phi0 over the declared 2-cut family
            {(L|R), (R|L)}, weights (1/2, 1/2), entropies in bits.
  rung D -> outer enclosing layer (2 aux levels on top of the 4-dim joint
            space) eliminated exactly by the Schur complement
            L_eff = L_II - L_IO L_OO^{-1} L_OI; L_eff acts on vec(rho_LR)
            every tick (nesting acts every tick, not once).
  rung E -> the controls fire on trajectories, classified from computed
            series only, never from a scalar echo.

ManifoldState (one object): admissible packet set X_k (explicit strings
until |X| > CAP, exact big-int transfer counts always), quotient classes
under the declared last-symbol probe, rho_L / rho_R (marginals), rho_LR
(primary joint carrier), leaf coordinate eta (a declared function of the
state), connection links (Pancharatnam link phases on the two leaf loops),
the rung-B generator bank, and the rung-D outer layer with its Schur L_eff.

ONE tick(t):
  (1) GROW: one declared extension step of the admissible set (alphabet
      schedule a_t cycles 4,5,3; constraint: adjacent symbols differ);
      Hartley drive dC_t = log|X_{t+1}| - log|X_t| (nats), computed from
      the actual counts, never from the schedule.
  (2) PROPAGATE: quotient entropy recomputed from the class counts; rho_LR
      evolves one tick (RK4 GKSL) under the currently-operating stage
      generator from the bank (ticks 0-9 depolarizing, 10-19 dephasing,
      20-29 damping) with rate gamma_t = GAMMA_BASE * dC_t / log 4 —
      the drive is COUPLED into the quantum motion, declared here;
      S_L, S_R, S_LR, I(L:R), I_c, negativity recomputed from cuts.
  (3) FLUX: eta_2(t) = 0.3 + 0.4 * p1_L(t) (declared function of the
      state: excited population of the L sheet); flux = relative holonomy
      of the chi-loop on leaves eta_1 = 0.2 and eta_2(t), computed link by
      link (rung-A machinery), analytic strip value recorded alongside.
  (4) NEST: apply the outer layer via the precomputed one-tick Schur
      propagator on vec(rho_LR); hermitize / clip / renormalize with all
      correction magnitudes recorded (the Schur-eliminated layer exchanges
      weight with the aux levels; the renormalization is declared).
  (5) LOCK: append the lock-stroke record I_rec += dC_t (nats) and
      compute Phi0 from the end-of-tick cuts; full series stored.

30 ticks. Controls (each must be able to FAIL):
  K1 drive alive: dC_t > 0 every tick.
  K2 co-movement: Pearson correlation between the dC series and the
     per-tick increments of each downstream entropy series is COMPUTED;
     at least one exceeds +0.5.
  K3 record accumulates monotonically: I_rec strictly increases.
  K4 Phi0 computed each tick: 30 finite values, nonzero variation,
     full series stored in the receipt.
  K5 flatten-nesting control: rerun with step (4) skipped; the combined
     L2 difference of the downstream series (S_LR, Phi0, negativity,
     flux, S_L) exceeds 1e-6 (per-series norms recorded).
  K6 freeze-drive control: rerun with dC = 0 (no growth, gamma = 0;
     everything else identical, outer layer still on); quotient-entropy
     motion vanishes exactly and the total variation of S_LR drops by
     more than 1e-3 (ratio recorded) — the drive is load-bearing.
  K7 packet-set/transfer-count cross-check: while the explicit set is
     materialized, len(X_k) equals the transfer-matrix count exactly.

Backend switch: --backend numpy (default; the only backend built in this
file — jax / torch are declared switch positions and refuse to run).

Claim ceiling: executed finite instance; scratch_diagnostic;
promotion_allowed=false; no uniqueness or optimality claim.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

# ---------------- shared constants (traced to the rungs) ----------------
N_TICKS = 30
TICK_DT = 0.4
NSUB = 8                       # RK4 substeps per tick (stage generator)
NSUB_OUT = 8                   # substeps inside the outer-layer propagator
N_LOOP = 200                   # rung-A loop discretization
CAP = 20000                    # explicit-packet materialization cap
OMEGA, ALPHA = 1.3, 0.7        # rung-B sheet Hamiltonian
J_XY = 0.35                    # inter-sheet XY coupling
GAMMA_BASE = 0.6               # drive->dissipation coupling scale
ETA1 = 0.2                     # fixed base leaf (rung A)
A_SCHED = [3 + ((t + 1) % 3) for t in range(N_TICKS)]  # 4,5,3,4,5,3,...
CUT_FAMILY = {"cuts": ["L|R", "R|L"], "weights": [0.5, 0.5]}
# rung-D outer layer on top of the 4-dim joint space (levels 4,5 = aux)
OUTER = {"Delta4": 1.0, "Delta5": 1.5, "gph": 0.1,
         "g": 0.5, "g2": 0.35, "k_out": 0.8}

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
SM = np.array([[0, 1], [0, 0]], dtype=complex)


# ---------------- rung-A machinery: leaves, links, flux -----------------
def spinor(eta, phi, chi):
    return np.array([np.exp(1j * phi) * np.cos(eta),
                     np.exp(1j * chi) * np.sin(eta)])


def link_phase(p1, p2):
    return np.angle(np.vdot(p1, p2))


def loop_holonomy(points):
    return sum(link_phase(points[k], points[(k + 1) % len(points)])
               for k in range(len(points)))


def chi_loop(eta, phi0=0.3):
    ts = np.linspace(0, 2 * np.pi, N_LOOP, endpoint=False)
    return [spinor(eta, phi0, t) for t in ts]


# ---------------- rung-C machinery: cuts on rho_LR ----------------------
def vn_entropy(rho):
    w = np.linalg.eigvalsh(rho)
    w = w[w > 1e-14]
    return float(-(w * np.log2(w)).sum())


def ptrace(rho, keep):
    r = rho.reshape(2, 2, 2, 2)
    if keep == "L":
        return np.trace(r, axis1=1, axis2=3)
    return np.trace(r, axis1=0, axis2=2)


def negativity(rho):
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    w = np.linalg.eigvalsh(pt)
    return float(-w[w < 0].sum())


def cut_readouts(rho):
    S_L = vn_entropy(ptrace(rho, "L"))
    S_R = vn_entropy(ptrace(rho, "R"))
    S_LR = vn_entropy(rho)
    Ic_LR = -(S_LR - S_R)
    Ic_RL = -(S_LR - S_L)
    w1, w2 = CUT_FAMILY["weights"]
    return {"S_L": S_L, "S_R": S_R, "S_LR": S_LR,
            "I": S_L + S_R - S_LR, "I_c": Ic_LR,
            "negativity": negativity(rho),
            "Phi0": w1 * Ic_LR + w2 * Ic_RL}


# ---------------- rung-B machinery: sheets + generator bank -------------
def kron(a, b):
    return np.kron(a, b)


def build_joint_h():
    nvec = np.array([np.sin(ALPHA), 0.0, np.cos(ALPHA)])   # n_y=0: H real
    H_L = 0.5 * OMEGA * (nvec[0] * SX + nvec[2] * SZ)
    H_R = -H_L                                             # conjugate rep
    return (kron(H_L, I2) + kron(I2, H_R)
            + J_XY * (kron(SX, SX) + kron(SY, SY)))


def bank_jumps(stage, gamma):
    """Stage generator from the rung-B bank, on BOTH conjugate sheets."""
    if gamma <= 0.0:
        return []
    if stage == 0:      # G1 depolarizing
        return ([np.sqrt(gamma / 4) * kron(s, I2) for s in (SX, SY, SZ)]
                + [np.sqrt(gamma / 4) * kron(I2, s.conj())
                   for s in (SX, SY, SZ)])
    if stage == 1:      # G7 pinching row, GKSL limit = pure dephasing
        return [np.sqrt(gamma) * kron(SZ, I2),
                np.sqrt(gamma) * kron(I2, SZ.conj())]
    # G3 amplitude damping
    return [np.sqrt(gamma) * kron(SM, I2),
            np.sqrt(gamma) * kron(I2, SM.conj())]


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


# ---------------- rung-D machinery: outer layer + Schur L_eff -----------
def op6(i, j):
    m = np.zeros((6, 6), dtype=complex)
    m[i, j] = 1.0
    return m


def liouvillian(H, jumps):
    d = H.shape[0]
    I = np.eye(d, dtype=complex)
    L = -1j * (np.kron(I, H) - np.kron(H.T, I))
    for K in jumps:
        KdK = K.conj().T @ K
        L += (np.kron(K.conj(), K)
              - 0.5 * np.kron(I, KdK) - 0.5 * np.kron(KdK.T, I))
    return L


def build_outer_schur():
    """6-level model: joint 4-dim inner + 2 aux levels; exact Schur."""
    c = OUTER
    H = (c["Delta4"] * op6(4, 4) + c["Delta5"] * op6(5, 5)
         + c["g"] * (op6(3, 4) + op6(4, 3))
         + c["g2"] * (op6(0, 5) + op6(5, 0)))
    jumps = [np.sqrt(c["k_out"]) * op6(1, 4),
             np.sqrt(c["k_out"]) * op6(2, 5),
             np.sqrt(c["gph"]) * (op6(4, 4) - op6(5, 5))]
    L = liouvillian(H, jumps)
    P = [i + 6 * j for j in range(4) for i in range(4)]
    Q = [n for n in range(36) if n not in P]
    L_II = L[np.ix_(P, P)]
    L_IO = L[np.ix_(P, Q)]
    L_OI = L[np.ix_(Q, P)]
    L_OO = L[np.ix_(Q, Q)]
    L_eff = L_II - L_IO @ np.linalg.solve(L_OO, L_OI)
    # one-tick propagator: RK4 polynomial of h*L_eff, NSUB_OUT substeps
    h = TICK_DT / NSUB_OUT
    A = h * L_eff
    P_step = (np.eye(16) + A + A @ A / 2.0
              + A @ A @ A / 6.0 + A @ A @ A @ A / 24.0)
    M_tick = np.linalg.matrix_power(P_step, NSUB_OUT)
    return L_eff, M_tick, float(np.linalg.cond(L_OO))


def apply_outer(rho, M_tick):
    """One tick of the Schur-eliminated outer layer, corrections recorded."""
    v = rho.flatten(order="F")
    v = M_tick @ v
    r = v.reshape((4, 4), order="F")
    herm_dev = float(np.abs(r - r.conj().T).max())
    r = 0.5 * (r + r.conj().T)
    w, U = np.linalg.eigh(r)
    clip_mag = float(-w[w < 0].sum()) if np.any(w < 0) else 0.0
    w = np.clip(w, 0.0, None)
    r = (U * w) @ U.conj().T
    tr = float(np.trace(r).real)
    r = r / tr
    return r, {"herm_dev": herm_dev, "clip_mag": clip_mag,
               "trace_renorm": abs(tr - 1.0)}


# ---------------- the ONE manifold state --------------------------------
class ManifoldState:
    def __init__(self):
        # admissible packet set: length-1 strings over alphabet {0,1,2}
        self.packets = ["0", "1", "2"]          # explicit until CAP
        self.class_counts = [1, 1, 1, 0, 0]     # last-symbol probe classes
        self.materialized = True
        rho0_L = 0.5 * (I2 + 0.5 * SX + 0.3 * SY - 0.4 * SZ)  # rung B
        self.rho_LR = np.kron(rho0_L, rho0_L.conj())
        self.eta = (ETA1, None)                 # leaf pair; eta2 from state
        self.connection = {}                    # link/holonomy record
        self.bank = {0: "G1_depolarizing", 1: "G7_dephasing_pinch_limit",
                     2: "G3_amplitude_damping"}
        self.L_eff, self.M_tick, self.cond_LOO = build_outer_schur()
        self.I_rec = 0.0
        self.crosscheck_ok = True

    def total(self):
        return sum(self.class_counts)


def quotient_entropy(counts):
    tot = sum(counts)
    ps = [c / tot for c in counts if c > 0]
    return float(-sum(p * math.log(p) for p in ps))


def tick(st, t, frozen_drive=False, skip_outer=False):
    row = {}
    # (1) GROW — declared extension step; dC from actual counts
    if frozen_drive:
        dC = 0.0
    else:
        a = A_SCHED[t]
        old_total = st.total()
        new_counts = [0] * 5
        for x in range(a):
            new_counts[x] = old_total - st.class_counts[x]
        if st.materialized:
            new_packets = [s + str(x) for s in st.packets
                           for x in range(a) if str(x) != s[-1]]
            if len(new_packets) != sum(new_counts):
                st.crosscheck_ok = False
            if sum(new_counts) > CAP:
                st.packets, st.materialized = None, False
                row["materialization_dropped_at_count"] = sum(new_counts)
            else:
                st.packets = new_packets
        st.class_counts = new_counts
        dC = math.log(st.total()) - math.log(old_total)
    row["dC"] = dC

    # (2) PROPAGATE — quotient entropy + one tick of the stage generator
    row["H_quot"] = quotient_entropy(st.class_counts)
    stage = t // 10
    gamma = GAMMA_BASE * dC / math.log(4)
    st.rho_LR = evolve_tick(st.rho_LR, build_joint_h(),
                            bank_jumps(stage, gamma))
    row["stage"], row["gamma"] = st.bank[stage], gamma

    # (3) FLUX — eta2 is a declared function of the state
    p1L = float(np.real(ptrace(st.rho_LR, "L")[1, 1]))
    eta2 = 0.3 + 0.4 * min(max(p1L, 0.0), 1.0)
    st.eta = (ETA1, eta2)
    h1 = loop_holonomy(chi_loop(ETA1))
    h2 = loop_holonomy(chi_loop(eta2))
    st.connection = {"holonomy_eta1": h1, "holonomy_eta2": h2}
    row["eta2"] = eta2
    row["flux"] = h1 - h2
    row["flux_analytic"] = float(
        np.pi * (np.cos(2 * ETA1) - np.cos(2 * eta2)))

    # (4) NEST — outer layer via Schur L_eff (skipped only by the control)
    if not skip_outer:
        st.rho_LR, corr = apply_outer(st.rho_LR, st.M_tick)
        row["outer_corrections"] = corr

    # (5) LOCK — record stroke + Phi0 from end-of-tick cuts
    st.I_rec += dC
    row["I_rec"] = st.I_rec
    row.update(cut_readouts(st.rho_LR))
    return row


def run(frozen_drive=False, skip_outer=False):
    st = ManifoldState()
    rows = [tick(st, t, frozen_drive, skip_outer) for t in range(N_TICKS)]
    series = {k: [r[k] for r in rows] for k in
              ("dC", "H_quot", "flux", "I_rec", "S_L", "S_R", "S_LR",
               "I", "I_c", "negativity", "Phi0", "eta2", "gamma")}
    return st, rows, series


def tv(xs):
    return float(np.sum(np.abs(np.diff(np.asarray(xs)))))


def corr(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.std() < 1e-15 or b.std() < 1e-15:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="numpy",
                    choices=["numpy", "jax", "torch"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if args.backend != "numpy":
        raise SystemExit(
            f"backend '{args.backend}' is a declared switch position but "
            "is not built in this file; run with --backend numpy")
    out = Path(args.out) if args.out else \
        Path(__file__).resolve().parent / "results" / "manifold_one"
    if out.exists():
        raise SystemExit(f"refusing to reuse output: {out}")
    out.mkdir(parents=True)
    checks, data, findings = {}, {}, []

    st, rows, S = run()
    _, _, S_flat = run(skip_outer=True)
    _, _, S_frz = run(frozen_drive=True)
    data["series"] = S
    data["initial_readouts"] = cut_readouts(ManifoldState().rho_LR)
    data["cond_L_OO"] = st.cond_LOO
    data["outer_corrections_last_tick"] = rows[-1].get("outer_corrections")
    data["alphabet_schedule"] = A_SCHED
    data["declared_cut_family"] = CUT_FAMILY
    data["stage_schedule"] = st.bank
    data["units"] = {"dC_H_quot_I_rec": "nats", "cut_readouts": "bits"}

    # K1 drive alive
    checks["K1_drive_dC_positive_every_tick"] = bool(
        all(d > 0 for d in S["dC"]))
    data["dC_min_max"] = [min(S["dC"]), max(S["dC"])]

    # K2 co-movement: correlations COMPUTED between dC and downstream diffs
    base0 = data["initial_readouts"]
    diffs = {
        "dH_quot": np.diff([quotient_entropy([1, 1, 1, 0, 0])]
                           + S["H_quot"]),
        "dS_L": np.diff([base0["S_L"]] + S["S_L"]),
        "dS_LR": np.diff([base0["S_LR"]] + S["S_LR"]),
        "dPhi0": np.diff([base0["Phi0"]] + S["Phi0"]),
    }
    cors = {k: corr(S["dC"], v) for k, v in diffs.items()}
    data["drive_correlations"] = cors
    best = max(cors, key=lambda k: cors[k])
    checks["K2_downstream_entropy_comoves_with_drive"] = cors[best] > 0.5
    data["K2_best_comover"] = [best, cors[best]]

    # K3 record accumulates monotonically
    checks["K3_record_strictly_monotone"] = bool(
        all(b > a for a, b in zip([0.0] + S["I_rec"][:-1], S["I_rec"])))

    # K4 Phi0 computed each tick, full series stored
    phi = np.asarray(S["Phi0"])
    checks["K4_phi0_series_complete_finite_varying"] = bool(
        len(phi) == N_TICKS and np.all(np.isfinite(phi))
        and float(phi.std()) > 1e-12)
    data["phi0_std"] = float(phi.std())

    # K5 flatten-nesting control: skipping step 4 changes the trajectories
    per = {k: float(np.linalg.norm(np.asarray(S[k])
                                   - np.asarray(S_flat[k])))
           for k in ("S_LR", "Phi0", "negativity", "flux", "S_L")}
    combined = float(np.sqrt(sum(v * v for v in per.values())))
    checks["K5_flatten_nesting_diverges"] = combined > 1e-6
    data["flatten_series_l2"] = {"per_series": per, "combined": combined}

    # K6 freeze-drive control damps downstream motion
    tvq_b, tvq_f = tv(S["H_quot"]), tv(S_frz["H_quot"])
    tvs_b, tvs_f = tv(S["S_LR"]), tv(S_frz["S_LR"])
    checks["K6_freeze_drive_damps_downstream"] = bool(
        tvq_f == 0.0 and tvq_b > 0.0 and (tvs_b - tvs_f) > 1e-3)
    data["freeze_total_variation"] = {
        "H_quot": {"base": tvq_b, "frozen": tvq_f},
        "S_LR": {"base": tvs_b, "frozen": tvs_f,
                 "ratio": tvs_f / tvs_b if tvs_b > 0 else None}}

    # K7 explicit set vs transfer counts (while materialized)
    checks["K7_packet_set_matches_transfer_counts"] = st.crosscheck_ok
    drop = [r["materialization_dropped_at_count"] for r in rows
            if "materialization_dropped_at_count" in r]
    data["materialization_dropped_at"] = drop[0] if drop else None

    findings += [
        "the Schur-eliminated outer layer is not exactly trace-preserving "
        "on the inner block (weight exchanges with the aux levels); the "
        "per-tick trace renormalization and eigenvalue clip magnitudes "
        "are recorded, last tick: "
        + json.dumps(rows[-1].get("outer_corrections")),
        "negativity stays 0 on this trajectory (the XY coupling at "
        "J=0.35 does not entangle these mixed conjugate sheets past the "
        "PPT threshold before dissipation reabsorbs it) — recorded, not "
        "patched; the flatten control therefore leans on S_LR/Phi0/flux/"
        "S_L, whose norms are reported separately"
        if max(S["negativity"]) < 1e-9 else
        "negativity is transiently positive on the trajectory (max "
        f"{max(S['negativity']):.6f}) — the joint carrier crosses the "
        "PPT threshold under the XY coupling",
        "the dephasing stage is the GKSL limit of the rung-B pinching row "
        "G7, declared as such; the bank is a 3-row selection from the "
        "8-row rung-B grid, one row per 10-tick stage",
        "explicit packets are materialized only until |X| > 20000; after "
        "that the exact big-int transfer counts are the set's "
        "representation (K7 cross-checks the two while both exist)",
    ]

    receipt = {
        "schema": "ratchet.v8.nested-manifold.rungONE.v0",
        "backend": args.backend,
        "composed_rungs": {
            "A": "leaf eta + Pancharatnam links + relative holonomy flux",
            "B": "conjugate sheets + 3-row stage generator bank",
            "C": "rho_LR cut readouts + Phi0 over the 2-cut family",
            "D": "outer aux layer eliminated by exact Schur complement",
            "E": "controls classified from computed series only"},
        "parameters": {"n_ticks": N_TICKS, "tick_dt": TICK_DT,
                       "omega": OMEGA, "alpha": ALPHA, "J_xy": J_XY,
                       "gamma_base": GAMMA_BASE, "eta1": ETA1,
                       "outer": OUTER, "n_loop": N_LOOP, "cap": CAP},
        "checks": {k: bool(v) for k, v in checks.items()},
        "data": data, "findings": findings,
        "all_pass": bool(all(checks.values())),
        "promotion_allowed": False, "formal_admission_allowed": False,
        "claim_ceiling": ("executed finite instance of the integrated "
                          "manifold tick loop (30 ticks, numpy backend); "
                          "composition of verified rungs, no new physics "
                          "claim, no uniqueness/optimality claim"),
    }
    (out / "receipt.json").write_text(
        json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"rung": "ONE", "file": str(Path(__file__).resolve()),
                      "all_pass": receipt["all_pass"],
                      "checks": receipt["checks"],
                      "findings": findings}, indent=2))


if __name__ == "__main__":
    main()
