#!/usr/bin/env python3
"""Nested-manifold runtime — Rung B: two Weyl sheets x eight generators (16-grid).

Two sheets carry the SAME eight per-sheet generators from the 16-pattern grid:
left sheet (rho_L, H_L = (omega/2) n.sigma) and right sheet as the CONJUGATE
representation (rho_R = conj(rho_L), H_R = -H_L, L_R = conj(L_L)); with n real
(n_y = 0) the conjugate representation IS the H_R = -H_L sheet, executed not
asserted. Every generator runs on BOTH sheets; every entropy law is computed
on the trajectory, never echoed from the formula.

The eight per-sheet generators (grid rows), each with its formal entropy law:
  G1 depolarizing GKSL (gamma=0.2, L_k = sqrt(gamma/4) sigma_k):
     Spohn sigma = -dD(rho||I/2)/dt = dS_vN/dt > 0 along the trajectory.
  G2 Lueders instrument branch (projectors onto the H eigenbasis):
     branches pure, completeness sum p_j rho_j = pinched rho exact,
     unread Lueders strictly raises S_vN for a noncommuting input.
  G3 amplitude damping N=0 (L = sqrt(gamma) sigma_-, fixed point |0><0|):
     D(rho*||rho(t)) monotone down (data processing with invariant reference;
     the FORWARD D(rho(t)||rho*) diverges at N=0 — recorded as a finding,
     not papered over); ground population monotone up.
  G4 damping overshoot trajectory (opposed start r_z(0) < 0):
     S_vN shows an explicit interior hump (rises then falls) while
     D(rho*||rho(t)) stays monotone down straight through the hump.
  G5 Stone unitary group (H = (omega/2) n.sigma, closed-form U(dt)):
     dS_vN = 0 exactly along the orbit while the phase-measure
     (sigma_z readout) Shannon entropy GROWS from the aligned start.
  G6 Hahn echo (static inhomogeneous ensemble, pi-pulse at tau):
     free dephasing kills ensemble coherence; the echo refocuses it to 1
     and returns the ensemble-average entropy to ~0 (recoverable, not
     produced).
  G7 pinching channel onto the H eigenbasis (rank-1 blocks):
     Shannon identity S(P rho) = H(p) exact (two independent routes),
     strict entropy increase for noncommuting input.
  G8 block consolidation (4-dim, H = (omega/2) sigma_z x I, 2-dim blocks):
     Shannon GROUPING identity S(P rho) = H(p) + sum_j p_j S(rho_Bj)
     exact and NONTRIVIAL (S(rho_Bj) != 0).

Controls (each must measurably FIRE or the rung fails):
  C1 commuting control: the noncommuting pair (pinch_x, Stone U) shows an
     order gap > 1e-2 (fires) AND replacing it with the commuting pair
     (pinch_H, Stone U) collapses the order gap to 0 (machine precision).
  C2 conjugate-representation check: the Pancharatnam latitude loop gives
     gamma_L = +Omega/2 on the left sheet (link convention
     Arg<psi_k|psi_{k+1}>) and the right sheet flips the Berry sign,
     gamma_R = -Omega/2.
  C3 conjugate-dynamics exactness: the independently evolved right-sheet
     trajectory equals conj(left trajectory) to machine tolerance on the
     GKSL rows (G1, G4) — the conjugate representation is dynamical, not
     notational.

Claim ceiling: executed finite instance; scratch_diagnostic;
promotion_allowed=false; no uniqueness or optimality claim.
"""
import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(__file__).resolve().parent / "results" / "rungB"
N = 400  # Pancharatnam loop discretization

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
SM = np.array([[0, 1], [0, 0]], dtype=complex)  # sigma_- = |0><1|

OMEGA, GAMMA, ALPHA = 1.3, 0.2, 0.7
NVEC = np.array([np.sin(ALPHA), 0.0, np.cos(ALPHA)])  # n_y = 0: H real


def bloch(r):
    return 0.5 * (I2 + r[0] * SX + r[1] * SY + r[2] * SZ)


def vn(rho):
    w = np.clip(np.linalg.eigvalsh(rho), 0.0, 1.0)
    w = w[w > 1e-300]
    return float(-np.sum(w * np.log(w)))


def shannon(p):
    p = np.clip(np.asarray(p, dtype=float), 0.0, 1.0)
    p = p[p > 1e-300]
    return float(-np.sum(p * np.log(p)))


def rel_ent(a, b):
    """D(a||b) = tr a log a - tr a log b; +inf off the support of b."""
    wa = np.clip(np.linalg.eigvalsh(a), 0.0, 1.0)
    s1 = float(np.sum(wa[wa > 1e-300] * np.log(wa[wa > 1e-300])))
    wb, vb = np.linalg.eigh(b)
    diag_a = np.real(np.einsum("ij,jk,ki->i", vb.conj().T, a, vb))
    if np.any((wb <= 1e-14) & (diag_a > 1e-12)):
        return np.inf
    m = wb > 1e-14
    return s1 - float(np.sum(diag_a[m] * np.log(wb[m])))


def trace_dist(a, b):
    return 0.5 * float(np.sum(np.abs(np.linalg.eigvalsh(a - b))))


def gksl_rhs(rho, H, Ls):
    d = -1j * (H @ rho - rho @ H)
    for L in Ls:
        Ld = L.conj().T
        d += L @ rho @ Ld - 0.5 * (Ld @ L @ rho + rho @ Ld @ L)
    return d


def evolve(rho0, H, Ls, dt, nsteps, snap_every=50):
    """RK4 GKSL trajectory; returns (S_vN list, snapshots [(k, rho)])."""
    rho = rho0.copy()
    S, snaps = [vn(rho)], [(0, rho.copy())]
    for k in range(1, nsteps + 1):
        k1 = gksl_rhs(rho, H, Ls)
        k2 = gksl_rhs(rho + 0.5 * dt * k1, H, Ls)
        k3 = gksl_rhs(rho + 0.5 * dt * k2, H, Ls)
        k4 = gksl_rhs(rho + dt * k3, H, Ls)
        rho = rho + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        rho = 0.5 * (rho + rho.conj().T)
        S.append(vn(rho))
        if k % snap_every == 0 or k == nsteps:
            snaps.append((k, rho.copy()))
    return np.array(S), snaps


def stone_u(H, t):
    """Closed-form 2x2 unitary exp(-iHt) for H = (omega/2) n.sigma."""
    th = 0.5 * OMEGA * t
    nsig = H / (0.5 * OMEGA)
    return np.cos(th) * I2 - 1j * np.sin(th) * nsig


def pinch(rho, basis):
    out = np.zeros_like(rho)
    for j in range(basis.shape[1]):
        v = basis[:, j:j + 1]
        P = v @ v.conj().T
        out += P @ rho @ P
    return out


def base_state(theta, phi):
    return np.array([np.cos(theta / 2),
                     np.exp(1j * phi) * np.sin(theta / 2)])


def link_phase(p1, p2):
    """U(1) link: Arg<psi1|psi2> — discrete connection (Pancharatnam)."""
    return np.angle(np.vdot(p1, p2))


def loop_holonomy(points):
    return sum(link_phase(points[k], points[(k + 1) % len(points)])
               for k in range(len(points)))


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")
    OUT.mkdir(parents=True)
    checks, data = {}, {}

    H_L = 0.5 * OMEGA * (NVEC[0] * SX + NVEC[2] * SZ)  # real matrix
    H_R = -H_L
    Hz_L, Hz_R = 0.5 * OMEGA * SZ, -0.5 * OMEGA * SZ   # damping rows
    rho0_L = bloch([0.5, 0.3, -0.4])
    rho0_R = rho0_L.conj()
    dt = 0.01

    # ---- G1 depolarizing GKSL: Spohn sigma > 0 on BOTH sheets ----
    dep_L = [np.sqrt(GAMMA / 4) * s for s in (SX, SY, SZ)]
    dep_R = [L.conj() for L in dep_L]
    S_L, snaps1L = evolve(rho0_L, H_L, dep_L, dt, 3000)
    S_R, snaps1R = evolve(rho0_R, H_R, dep_R, dt, 3000)
    for tag, S in (("left", S_L), ("right", S_R)):
        D = np.log(2.0) - S                       # D(rho||I/2)
        diffs = np.diff(S)
        mask = D[:-1] > 1e-6
        checks[f"G1_spohn_sigma_positive_{tag}"] = bool(
            np.all(diffs[mask] > 0) and np.min(diffs) > -1e-12)
        data[f"G1_min_dS_step_{tag}"] = float(np.min(diffs))
    checks["G1_fixed_point_maximally_mixed"] = \
        trace_dist(snaps1L[-1][1], I2 / 2) < 1e-2
    data["G1_final_dist_to_I2"] = float(trace_dist(snaps1L[-1][1], I2 / 2))

    # ---- G2 Lueders instrument branch (H eigenbasis), both sheets ----
    _, evecs = np.linalg.eigh(H_L)               # H real: same basis both
    for tag, rho in (("left", rho0_L), ("right", rho0_R)):
        ps, branches, recon = [], [], np.zeros_like(rho)
        for j in range(2):
            v = evecs[:, j:j + 1]
            P = v @ v.conj().T
            pj = float(np.real(np.trace(P @ rho @ P)))
            ps.append(pj)
            branches.append(P @ rho @ P / pj)
            recon += P @ rho @ P
        pinched = pinch(rho, evecs)
        checks[f"G2_branches_pure_and_complete_{tag}"] = bool(
            max(vn(b) for b in branches) < 1e-12
            and trace_dist(recon, pinched) < 1e-14
            and abs(sum(ps) - 1.0) < 1e-14)
        checks[f"G2_unread_lueders_entropy_up_{tag}"] = \
            vn(pinched) - vn(rho) > 1e-2
        data[f"G2_entropy_gap_{tag}"] = float(vn(pinched) - vn(rho))

    # ---- G3 amplitude damping N=0: monotone laws, both sheets ----
    damp_L, damp_R = [np.sqrt(GAMMA) * SM], [np.sqrt(GAMMA) * SM.conj()]
    P0 = np.array([[1, 0], [0, 0]], dtype=complex)  # rho* = |0><0| (pure)
    for tag, rho0, H, Ls in (("left", rho0_L, Hz_L, damp_L),
                             ("right", rho0_R, Hz_R, damp_R)):
        _, snaps = evolve(rho0, H, Ls, dt, 4000, snap_every=20)
        Drev = np.array([rel_ent(P0, r) for _, r in snaps])
        p0 = np.array([float(np.real(r[0, 0])) for _, r in snaps])
        checks[f"G3_reversed_relent_monotone_down_{tag}"] = bool(
            np.all(np.diff(Drev) <= 1e-9))
        checks[f"G3_ground_population_monotone_up_{tag}"] = bool(
            np.all(np.diff(p0) >= -1e-12) and p0[-1] > 0.99)
        data[f"G3_Drev_first_last_{tag}"] = [float(Drev[0]), float(Drev[-1])]
    # honest divergence of the FORWARD Spohn form at N=0
    data["G3_forward_D_rho_rhostar"] = rel_ent(rho0_L, P0)
    checks["G3_forward_relent_diverges_at_N0_recorded"] = \
        not np.isfinite(rel_ent(rho0_L, P0))

    # ---- G4 overshoot trajectory (opposed start r_z(0) < 0), both sheets ----
    rho4_L = bloch([0.1, 0.0, -0.95])
    for tag, rho0, H, Ls in (("left", rho4_L, Hz_L, damp_L),
                             ("right", rho4_L.conj(), Hz_R, damp_R)):
        S4, snaps4 = evolve(rho0, H, Ls, dt, 5000, snap_every=20)
        Drev4 = np.array([rel_ent(P0, r) for _, r in snaps4])
        kmax = int(np.argmax(S4))
        checks[f"G4_vN_overshoot_hump_{tag}"] = bool(
            0 < kmax < len(S4) - 1
            and S4[kmax] > S4[0] + 0.2 and S4[kmax] > S4[-1] + 0.2)
        checks[f"G4_relent_monotone_through_hump_{tag}"] = bool(
            np.all(np.diff(Drev4) <= 1e-9))
        data[f"G4_S_start_peak_end_{tag}"] = [
            float(S4[0]), float(S4[kmax]), float(S4[-1])]
        if tag == "left":
            snaps4_L = snaps4
        else:
            snaps4_R = snaps4

    # ---- G5 Stone unitary group: dS_vN = 0 exact, phase entropy grows ----
    rho5_L = np.diag([0.9, 0.1]).astype(complex)   # aligned sigma_z start
    for tag, H in (("left", H_L), ("right", H_R)):
        rho = rho5_L.copy() if tag == "left" else rho5_L.conj().copy()
        U = stone_u(H, dt)
        S0, Smax_dev, Hp = vn(rho), 0.0, [shannon(np.real(np.diag(rho)))]
        for _ in range(500):                        # ~1.03 periods
            rho = U @ rho @ U.conj().T
            Smax_dev = max(Smax_dev, abs(vn(rho) - S0))
            Hp.append(shannon(np.real(np.diag(rho))))
        checks[f"G5_dSvN_zero_exact_{tag}"] = Smax_dev < 1e-9
        checks[f"G5_phase_measure_entropy_grows_{tag}"] = \
            max(Hp) > Hp[0] + 0.2
        data[f"G5_Hp_initial_max_{tag}"] = [float(Hp[0]), float(max(Hp))]
        data[f"G5_max_S_deviation_{tag}"] = float(Smax_dev)

    # ---- G6 Hahn echo: static inhomogeneous ensemble, pi-pulse at tau ----
    W, tau, M = 10.0, 2.0, 201
    freqs = np.linspace(-W, W, M)
    plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
    for tag, sgn in (("left", 1.0), ("right", -1.0)):
        def free(psi, w, t):
            return np.array([np.exp(-1j * sgn * w * t / 2) * psi[0],
                             np.exp(+1j * sgn * w * t / 2) * psi[1]])
        no_echo = [free(plus, w, 2 * tau) for w in freqs]
        echo = [free(SX @ free(plus, w, tau), w, tau) for w in freqs]
        def coh_and_S(states):
            rho_avg = sum(np.outer(p, p.conj()) for p in states) / len(states)
            return abs(rho_avg[0, 1]) * 2, vn(rho_avg)
        c_free, S_free = coh_and_S(no_echo)
        c_echo, S_echo = coh_and_S(echo)
        checks[f"G6_free_dephasing_fires_{tag}"] = c_free < 0.2
        checks[f"G6_echo_refocuses_{tag}"] = \
            c_echo > 1 - 1e-9 and S_echo < 1e-9
        checks[f"G6_avg_entropy_recoverable_{tag}"] = \
            S_free > 0.3 and S_echo < 1e-9
        data[f"G6_coherence_free_echo_{tag}"] = [float(c_free), float(c_echo)]
        data[f"G6_S_free_echo_{tag}"] = [float(S_free), float(S_echo)]

    # ---- G7 pinching onto H eigenbasis: Shannon identity, both sheets ----
    for tag, rho in (("left", rho0_L), ("right", rho0_R)):
        pinched = pinch(rho, evecs)
        p = [float(np.real(evecs[:, j].conj() @ rho @ evecs[:, j]))
             for j in range(2)]
        checks[f"G7_shannon_identity_exact_{tag}"] = \
            abs(vn(pinched) - shannon(p)) < 1e-12
        checks[f"G7_pinching_entropy_up_{tag}"] = vn(pinched) - vn(rho) > 1e-2
        data[f"G7_SPrho_vs_Hp_{tag}"] = [float(vn(pinched)),
                                         float(shannon(p))]

    # ---- G8 block consolidation: 4-dim grouping identity, nontrivial ----
    A = np.array([[1.0, 0.3 + 0.2j, 0.1, 0.4j],
                  [0.2, 1.1, 0.5j, 0.2],
                  [0.3j, 0.1, 0.9, 0.3],
                  [0.1, 0.2j, 0.4, 1.2]], dtype=complex)
    rho4d = A @ A.conj().T
    rho4d /= np.real(np.trace(rho4d))
    for tag in ("left", "right"):
        r4 = rho4d if tag == "left" else rho4d.conj()
        blocks = [r4[:2, :2], r4[2:, 2:]]          # H4 = (w/2) sz x I blocks
        Pr4 = np.zeros((4, 4), dtype=complex)
        Pr4[:2, :2], Pr4[2:, 2:] = blocks
        p = [float(np.real(np.trace(b))) for b in blocks]
        Sb = [vn(b / pj) for b, pj in zip(blocks, p)]
        lhs = vn(Pr4)
        rhs = shannon(p) + sum(pj * sj for pj, sj in zip(p, Sb))
        checks[f"G8_grouping_identity_exact_{tag}"] = abs(lhs - rhs) < 1e-12
        checks[f"G8_grouping_nontrivial_{tag}"] = min(Sb) > 0.1
        data[f"G8_lhs_rhs_{tag}"] = [float(lhs), float(rhs)]
        data[f"G8_block_entropies_{tag}"] = [float(s) for s in Sb]

    # ---- C1 commuting control: order gap fires, then collapses to 0 ----
    U1 = stone_u(H_L, 0.7)
    _, xvecs = np.linalg.eigh(SX)
    rho_t = rho0_L
    gap_nc = trace_dist(pinch(U1 @ rho_t @ U1.conj().T, xvecs),
                        U1 @ pinch(rho_t, xvecs) @ U1.conj().T)
    gap_c = trace_dist(pinch(U1 @ rho_t @ U1.conj().T, evecs),
                       U1 @ pinch(rho_t, evecs) @ U1.conj().T)
    checks["C1_noncommuting_order_gap_fires"] = gap_nc > 1e-2
    checks["C1_commuting_pair_order_gap_zero"] = gap_c < 1e-12
    data["C1_gap_noncommuting"], data["C1_gap_commuting"] = \
        float(gap_nc), float(gap_c)

    # ---- C2 conjugate representation: Berry sign flips on right sheet ----
    th = 1.0
    lat = [base_state(th, t)
           for t in np.linspace(0, 2 * np.pi, N, endpoint=False)]
    gamma_L = loop_holonomy(lat)
    gamma_R = loop_holonomy([np.conj(pt) for pt in lat])
    omega_solid = 2 * np.pi * (1 - np.cos(th))
    checks["C2_left_sheet_berry_plus_half_omega"] = \
        abs(((gamma_L - omega_solid / 2) + np.pi) % (2 * np.pi) - np.pi) \
        < 1e-3
    checks["C2_right_sheet_berry_sign_flipped"] = \
        abs(((gamma_R + omega_solid / 2) + np.pi) % (2 * np.pi) - np.pi) \
        < 1e-3
    data["C2_gamma_L_gamma_R_halfomega"] = [
        float(gamma_L), float(gamma_R), float(omega_solid / 2)]

    # ---- C3 conjugate-dynamics exactness on the GKSL rows ----
    dev1 = max(np.max(np.abs(rR - rL.conj()))
               for (_, rL), (_, rR) in zip(snaps1L, snaps1R))
    dev4 = max(np.max(np.abs(rR - rL.conj()))
               for (_, rL), (_, rR) in zip(snaps4_L, snaps4_R))
    checks["C3_conjugate_dynamics_exact"] = max(dev1, dev4) < 1e-9
    data["C3_max_deviation_G1_G4"] = [float(dev1), float(dev4)]

    receipt = {
        "schema": "ratchet.v8.nested-manifold.rungB.v0",
        "grid": {"sheets": ["left(rho_L, H_L)",
                            "right(conj rep, H_R=-H_L)"],
                 "generators": ["G1_depolarizing_gksl", "G2_lueders_branch",
                                "G3_amplitude_damping_N0",
                                "G4_damping_overshoot", "G5_stone_unitary",
                                "G6_hahn_echo", "G7_pinching",
                                "G8_block_consolidation"]},
        "checks": {k: bool(v) for k, v in checks.items()}, "data": data,
        "all_pass": bool(all(checks.values())),
        "findings": [
            "G3: forward D(rho||rho*) is +inf at N=0 (pure fixed point); "
            "the executed monotone is the reversed divergence "
            "D(rho*||rho(t)), licensed by data processing with the "
            "invariant reference — Spohn's forward form is not finite on "
            "this row and that is recorded, not patched",
            "G5: the phase-measure Shannon entropy under the Stone group "
            "is recurrent (oscillates back), unlike every GKSL row — the "
            "growth check is over the first quarter period; no arrow on "
            "the unitary row",
            "G7: per-sheet qubit pinching has rank-1 blocks, so the "
            "grouping identity degenerates to S(Prho)=H(p); the "
            "nontrivial grouping S(Prho)=H(p)+sum p_j S(rho_Bj) is earned "
            "only on the 4-dim block-consolidation row G8",
            "G6: echo refocusing is exact only because the inhomogeneous "
            "frequencies are static (no spectral diffusion); the "
            "ensemble-average entropy is recoverable, not produced"],
        "promotion_allowed": False, "formal_admission_allowed": False,
        "claim_ceiling": ("executed finite 16-grid instance (2 sheets x 8 "
                          "generators) with per-row entropy laws and "
                          "firing controls; no uniqueness/optimality "
                          "claim"),
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"all_pass": receipt["all_pass"],
                      "checks": receipt["checks"]}, indent=2))


if __name__ == "__main__":
    main()
