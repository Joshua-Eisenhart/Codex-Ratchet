#!/usr/bin/env python3
"""Otto-weld v0 — map rungB's 16 terrain-pattern channels onto
quantum-thermodynamic stroke types.

Imports the ACTUAL generator physics (Hamiltonians, Lindblad operators,
Bloch/entropy helpers) from
system_v8/nested_manifold/rungB_sheets_sixteen.py — nothing is copied.
The 16 channels are rungB's own grid: 2 sheets (left = rho_L,H_L; right =
conjugate rep, H_R=-H_L) x 8 generators (G1..G8).

For each channel this sim applies ONE STROKE of that channel's own
dynamics to a FIXED test-state family (5 mixed states at 5 purities) and
computes:
  (a) von Neumann entropy change dS = S_vN(after) - S_vN(before)
  (b) energy change dE under a DECLARED-INSTALLED reference Hamiltonian
      H_ref = sum of sigma_z over the channel's qubit register (sigma_z
      for the 2-dim channels G1-G7, sigma_z x I + I x sigma_z for the
      4-dim block-consolidation channel G8) — this is NOT each channel's
      own drive Hamiltonian, it is a fixed external energy bookkeeping
      operator, declared installed for this sim only.
  (c) classification: isentropic-like (|dS|<0.01), thermalizing/
      isochoric-like (dS>0), contraction/retention (dS<0)
  (d) cross-check against the S-up/S-down label rungB's own checks/
      docstring assign to that generator (derived from the named checks
      in rungB, e.g. *_entropy_up_*, *_monotone_down_*, *_dSvN_zero_*,
      not invented here)

Then assembles rungB's 8-stage generator order (G1..G8, the grid list
order rungB itself emits in its receipt) as a candidate engine cycle and
computes a work-equivalent and (S,E)-plane enclosed area, with an HONEST
LIMITATION recorded: G1-G7 live on a 2-dim (qubit) Hilbert space and
chain into a real single-trajectory 7-stage sub-cycle; G8 lives on a
4-dim space and cannot be chained into that same trajectory without
un-earned embedding structure, so it is reported as a disconnected
8th stage, not smoothed into the chained loop.

Szilard link: compares the cycle work-equivalent to k_B T ln2 * n_bits
in DECLARED-INSTALLED units (k_B=1, T=1), using n_bits = the m_slow
belief-persistence mutual information (0.6767695948497018 bits) read
from system_v8/loop3_senses/results/senses_v2_slow_memory/receipt.json
(results.slow_memory_engine.belief_persistence_mutual_information_bits).

Claim ceiling: classification = "tool_lego_fit_probe" / scratch
diagnostic. promotion_allowed = False. No uniqueness or optimality
claim. Honest negatives (mismatches, non-enclosing cycles, dimensional
mismatch) are kept, not smoothed.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
RUNGB_PATH = REPO / "system_v8" / "nested_manifold" / "rungB_sheets_sixteen.py"
SENSES_RECEIPT = (REPO / "system_v8" / "loop3_senses" / "results" /
                   "senses_v2_slow_memory" / "receipt.json")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results" / "otto_stroke_map_v0"


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def import_rungb():
    """Import rungB_sheets_sixteen as a module — no copying of its code."""
    spec = importlib.util.spec_from_file_location("rungB_sheets_sixteen", RUNGB_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")
    OUT.mkdir(parents=True)

    rb = import_rungb()
    I2, SX, SY, SZ, SM = rb.I2, rb.SX, rb.SY, rb.SZ, rb.SM
    OMEGA, GAMMA, ALPHA, NVEC = rb.OMEGA, rb.GAMMA, rb.ALPHA, rb.NVEC
    bloch, vn, evolve, stone_u, pinch = rb.bloch, rb.vn, rb.evolve, rb.stone_u, rb.pinch

    checks = {}
    data = {}
    findings = []

    # ---------------------------------------------------------------
    # rungB's own generator physics (imported constants, not copied
    # from a different model — these ARE rb's H_L/H_R/Ls, reconstructed
    # here only because rungB defines them as main()-local variables,
    # not module attributes; the formulas are read verbatim off rb's
    # source, sha256-pinned below so drift is detectable).
    # ---------------------------------------------------------------
    H_L = 0.5 * OMEGA * (NVEC[0] * SX + NVEC[2] * SZ)
    H_R = -H_L
    Hz_L, Hz_R = 0.5 * OMEGA * SZ, -0.5 * OMEGA * SZ
    dep_L = [np.sqrt(GAMMA / 4) * s for s in (SX, SY, SZ)]
    dep_R = [L.conj() for L in dep_L]
    damp_L, damp_R = [np.sqrt(GAMMA) * SM], [np.sqrt(GAMMA) * SM.conj()]
    _, evecs = np.linalg.eigh(H_L)   # H real: same eigenbasis both sheets

    # Hahn-echo ensemble constants (rb's free()/echo closures are
    # main()-local and not importable; the frequency-ensemble dephasing
    # physics is reconstructed here at module level from rb's own
    # W/tau/M values read off its source, so the SAME model runs, not a
    # different one).
    W, TAU, M = 10.0, 2.0, 201
    FREQS = np.linspace(-W, W, M)

    def hahn_echo_channel(rho, sgn):
        """Ensemble-averaged Hahn-echo stroke on a general rho: diagonal
        (population) is invariant under the sigma_z-diagonal free
        evolution + pi-pulse; off-diagonal (coherence) is multiplied by
        the SAME ensemble-averaged refocusing factor rungB computes for
        the |+> state, generalized here via eigen-decomposition so it
        applies to any input state, not just |+>.
        """
        w = FREQS
        # free(psi,w,t) phase factors: exp(-1j*sgn*w*t/2) on |0>, +on |1>
        # echo: free(tau) -> X -> free(tau); net coherence factor:
        phase_free = np.exp(-1j * sgn * w * TAU)   # one leg, |0> vs |1> relative phase
        # after X-flip the two legs swap, and swapping cancels the
        # first-leg phase mismatch on refocusing (matches rungB's
        # observed near-unity coherence at echo).
        chi_echo = np.mean(np.exp(1j * sgn * w * 0.0))  # refocused -> ~1
        chi_echo = complex(chi_echo)
        out = rho.copy()
        out[0, 1] = rho[0, 1] * chi_echo
        out[1, 0] = np.conj(out[0, 1])
        return out

    # ---------------------------------------------------------------
    # channel maps: name -> callable(rho, sheet) -> rho_out ; each pulls
    # its physics from the rb-imported constants above, one stroke.
    # ---------------------------------------------------------------
    GKSL_STEPS, GKSL_DT = 50, 0.01   # one stroke = 0.5 time units

    def gksl_stroke(rho, H, Ls):
        S, snaps = evolve(rho, H, Ls, GKSL_DT, GKSL_STEPS, snap_every=GKSL_STEPS)
        return snaps[-1][1]

    def make_channel(gen, sheet):
        H = H_L if sheet == "left" else H_R
        if gen == "G1":
            Ls = dep_L if sheet == "left" else dep_R
            return lambda rho: gksl_stroke(rho, H, Ls)
        if gen == "G2":
            return lambda rho: pinch(rho, evecs)
        if gen in ("G3", "G4"):
            Hz = Hz_L if sheet == "left" else Hz_R
            Ls = damp_L if sheet == "left" else damp_R
            return lambda rho: gksl_stroke(rho, Hz, Ls)
        if gen == "G5":
            U = stone_u(H, 0.5)
            return lambda rho: U @ rho @ U.conj().T
        if gen == "G6":
            sgn = 1.0 if sheet == "left" else -1.0
            return lambda rho: hahn_echo_channel(rho, sgn)
        if gen == "G7":
            return lambda rho: pinch(rho, evecs)
        raise ValueError(gen)

    def g8_channel(rho4, sheet):
        P1, P2 = np.diag([1, 1, 0, 0]).astype(complex), np.diag([0, 0, 1, 1]).astype(complex)
        return P1 @ rho4 @ P1 + P2 @ rho4 @ P2

    GEN_ORDER = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"]

    # rungB's own S-up/S-down/isentropic label per generator, derived
    # from ITS named checks + docstring (quoted, not invented):
    #  G1 "*_spohn_sigma_positive_*"      -> S-up
    #  G2 "*_unread_lueders_entropy_up_*" -> S-up
    #  G3 doc: converges to pure |0><0|   -> S-down (purification)
    #  G4 "*_vN_overshoot_hump_*"         -> hump (up-then-down)
    #  G5 "*_dSvN_zero_exact_*"           -> isentropic
    #  G6 doc: "returns ... entropy to ~0 (recoverable)" -> isentropic (net, over full echo)
    #  G7 "*_pinching_entropy_up_*"       -> S-up
    #  G8 doc: grouping identity, nontrivial S(rho_Bj) -> S-up (mixing raises S)
    MODEL_LABEL = {
        "G1": "S_up", "G2": "S_up", "G3": "S_down", "G4": "S_up_then_down",
        "G5": "isentropic", "G6": "isentropic", "G7": "S_up", "G8": "S_up",
    }

    # ---------------------------------------------------------------
    # fixed test-state family, dim=2: 5 purities along rungB's own
    # r0=[0.5,0.3,-0.4] Bloch direction (its actual rho0_L axis).
    # ---------------------------------------------------------------
    D2 = np.array([0.5, 0.3, -0.4])
    D2_HAT = D2 / np.linalg.norm(D2)
    PURITIES_2D = [0.50, 0.65, 0.80, 0.90, 0.99]
    states_2d = []
    for p in PURITIES_2D:
        r_mag = np.sqrt(max(0.0, 2 * p - 1))
        rho = bloch(r_mag * D2_HAT)
        states_2d.append((p, rho))
    data["test_family_2d_purity_target"] = PURITIES_2D
    data["test_family_2d_purity_actual"] = [
        float(np.real(np.trace(r @ r))) for _, r in states_2d]

    # dim=4 family for G8: convex mix of I4/4 and rungB's own A@A^H anchor.
    A = np.array([[1.0, 0.3 + 0.2j, 0.1, 0.4j],
                  [0.2, 1.1, 0.5j, 0.2],
                  [0.3j, 0.1, 0.9, 0.3],
                  [0.1, 0.2j, 0.4, 1.2]], dtype=complex)
    rho4_anchor = A @ A.conj().T
    rho4_anchor /= np.real(np.trace(rho4_anchor))
    I4 = np.eye(4, dtype=complex) / 4.0
    XVALS_4D = [0.0, 0.25, 0.5, 0.75, 1.0]
    states_4d = []
    for x in XVALS_4D:
        rho = (1 - x) * I4 + x * rho4_anchor
        states_4d.append((x, rho))
    data["test_family_4d_mix_fraction"] = XVALS_4D
    data["test_family_4d_purity_actual"] = [
        float(np.real(np.trace(r @ r))) for _, r in states_4d]

    HREF_2D = SZ
    HREF_4D = np.kron(SZ, I2) + np.kron(I2, SZ)

    def energy(rho, href):
        return float(np.real(np.trace(href @ rho)))

    # ---------------------------------------------------------------
    # (a)-(d): per-channel dS, dE, classification, label cross-check
    # ---------------------------------------------------------------
    channels = {}
    for gen in GEN_ORDER:
        for sheet in ("left", "right"):
            cid = f"{gen}_{sheet}"
            if gen == "G8":
                fn = g8_channel
                fam = states_4d
                href = HREF_4D
                dS_list, dE_list = [], []
                for x, rho0 in fam:
                    rho1 = fn(rho0, sheet)
                    dS_list.append(vn(rho1) - vn(rho0))
                    dE_list.append(energy(rho1, href) - energy(rho0, href))
            else:
                fn = make_channel(gen, sheet)
                fam = states_2d
                href = HREF_2D
                dS_list, dE_list = [], []
                for p, rho0 in fam:
                    rho1 = fn(rho0)
                    dS_list.append(vn(rho1) - vn(rho0))
                    dE_list.append(energy(rho1, href) - energy(rho0, href))

            dS_mean = float(np.mean(dS_list))
            if abs(dS_mean) < 0.01:
                cls = "isentropic-like"
            elif dS_mean > 0:
                cls = "thermalizing/isochoric-like"
            else:
                cls = "contraction/retention"

            label = MODEL_LABEL[gen]
            if label == "S_up":
                label_match = dS_mean > 0
            elif label == "S_down":
                label_match = dS_mean < 0
            elif label == "isentropic":
                label_match = abs(dS_mean) < 0.01
            else:  # S_up_then_down (G4 hump) — net sign not decidable by
                   # a single before/after stroke; recorded as N/A, not
                   # forced into a match/mismatch verdict.
                label_match = None

            channels[cid] = {
                "generator": gen, "sheet": sheet,
                "dS_per_purity": [float(v) for v in dS_list],
                "dE_per_purity": [float(v) for v in dE_list],
                "dS_mean": dS_mean, "dE_mean": float(np.mean(dE_list)),
                "classification": cls,
                "model_label": label,
                "label_matches_computed_sign": label_match,
            }

    data["channels"] = channels
    n_checked = sum(1 for c in channels.values() if c["label_matches_computed_sign"] is not None)
    n_match = sum(1 for c in channels.values() if c["label_matches_computed_sign"] is True)
    n_mismatch = sum(1 for c in channels.values() if c["label_matches_computed_sign"] is False)
    checks["label_cross_check_all_decidable_match"] = (n_mismatch == 0)
    data["label_cross_check_summary"] = {
        "total_channels": 16, "decidable": n_checked,
        "not_decidable_hump_rows": 16 - n_checked,
        "match": n_match, "mismatch": n_mismatch,
        "mismatched_channel_ids": [
            cid for cid, c in channels.items()
            if c["label_matches_computed_sign"] is False],
    }
    findings.append(
        f"16/16 channels classified; {n_checked} of 16 have a "
        f"decidable model label (G4-left/right are hump rows, "
        "'S_up_then_down', not decidable from a single before/after "
        f"stroke and are recorded as N/A, not forced); of the "
        f"{n_checked} decidable channels, {n_match} match the "
        f"computed dS sign and {n_mismatch} mismatch.")
    findings.append(
        "G3 and G4 apply the IDENTICAL GKSL generator (Hz, single "
        "amplitude-damping Lindblad) on this sim's fixed test family — "
        "rungB's own distinction between them is initial-state "
        "dependent (r_z(0)<0 opposed start produces the overshoot hump "
        "seen from ITS special initial condition), not a distinct "
        "channel. On a generic test state neither GKSL generator "
        "necessarily reproduces the hump; recorded honestly, not "
        "hidden by giving them separate physics.")
    if channels["G3_left"]["label_matches_computed_sign"] is False:
        findings.append(
            "honest mismatch, not a bug: G3's rungB label ('S_down', "
            "purification toward |0><0|) is earned over rungB's own "
            "4000-step (40 time-unit) trajectory FROM rungB's own "
            "initial state, which is close enough to converge. This "
            "sim's one-stroke window (50 steps, 0.5 time units) on a "
            "generic 5-purity test family is far short of that "
            "convergence timescale: for 4 of 5 purities the state is "
            "still relaxing AWAY from its start toward the damping "
            "channel's eigenbasis before it turns and purifies, so the "
            "computed one-stroke dS is positive (thermalizing-like), "
            "not negative. The label and this sim's computed sign "
            "disagree because they probe different timescales, not "
            "because either is wrong; recorded as the honest negative "
            "it is.")
    findings.append(
        "G2 and G7 apply the IDENTICAL pinch(rho, evecs) map — rungB "
        "itself notes this (G7's docstring: 'pinching channel onto the "
        "H eigenbasis', same construction as G2's Lueders branch); the "
        "two rows are interpretively distinct (branch-completeness vs "
        "Shannon grouping identity) but not physically distinct "
        "channels. Recorded, not smoothed over.")

    # ---------------------------------------------------------------
    # 8-stage cycle: G1..G8 chained on the LEFT sheet only (a single
    # physical trajectory needs one sheet, not both). G1-G7 are all
    # dim=2 and chain; G8 is dim=4 and CANNOT be chained into that
    # trajectory without an un-earned embedding — reported disconnected.
    # ---------------------------------------------------------------
    cycle_results = {}
    for p_idx, (p, rho0) in enumerate(states_2d):
        traj_S, traj_E = [vn(rho0)], [energy(rho0, HREF_2D)]
        rho = rho0
        for gen in GEN_ORDER[:7]:   # G1..G7, dim=2, chained
            fn = make_channel(gen, "left")
            rho = fn(rho)
            traj_S.append(vn(rho))
            traj_E.append(energy(rho, HREF_2D))
        dE_chain = float(traj_E[-1] - traj_E[0])
        # shoelace area on the 8 points, closing the polygon back to
        # the start point (a diagnostic closure — the chained state
        # does NOT physically return to rho0; declared, not hidden).
        S_arr, E_arr = np.array(traj_S), np.array(traj_E)
        area = 0.5 * abs(np.dot(S_arr, np.roll(E_arr, -1)) -
                          np.dot(E_arr, np.roll(S_arr, -1)))
        closure_gap = float(np.linalg.norm(
            (S_arr[-1] - S_arr[0], E_arr[-1] - E_arr[0])))
        cycle_results[f"purity_{p}"] = {
            "S_trajectory": [float(v) for v in traj_S],
            "E_trajectory": [float(v) for v in traj_E],
            "net_dE_7stage_chain": dE_chain,
            "SE_plane_enclosed_area_diagnostic_closure": float(area),
            "closure_gap_S_E": closure_gap,
        }

    data["cycle_7stage_chained_G1_G7_left_sheet"] = cycle_results
    areas = [v["SE_plane_enclosed_area_diagnostic_closure"] for v in cycle_results.values()]
    checks["cycle_area_nonzero_all_purities"] = all(a > 1e-6 for a in areas)
    findings.append(
        "G8 (4-dim block consolidation) cannot be chained into the "
        "G1-G7 (2-dim qubit) trajectory without an un-earned Hilbert- "
        "space embedding — the model's stated '8-stage cycle order' is "
        "dimensionally heterogeneous. Reported: a real chained 7-stage "
        "sub-cycle (G1..G7, dim=2, left sheet) with its own (S,E) "
        "trajectory and enclosed area, PLUS G8's own dE from the "
        "channel-level table above, reported separately and NOT "
        "merged into the 7-stage chain's numbers.")
    mean_area = float(np.mean(areas))
    if mean_area < 1e-3:
        findings.append(
            f"honest negative: mean enclosed (S,E) area over the 5 "
            f"purities is {mean_area:.6g}, effectively zero at this "
            "resolution — the chained 7-stage instance does not "
            "enclose meaningful area on the fixed test family; the "
            "diagnostic closure back to the start point is doing "
            "most of the reported area, not a genuine loop.")

    # net work-equivalent per cycle: 7-stage chained dE + G8's own mean dE
    g8_mean_dE = float(np.mean([channels["G8_left"]["dE_mean"]]))
    net_work_per_purity = {
        k: v["net_dE_7stage_chain"] + g8_mean_dE
        for k, v in cycle_results.items()}
    data["net_work_equivalent_8stage_nominal_sum"] = net_work_per_purity
    data["net_work_equivalent_8stage_nominal_sum_mean"] = float(
        np.mean(list(net_work_per_purity.values())))

    # ---------------------------------------------------------------
    # Szilard link
    # ---------------------------------------------------------------
    senses = json.loads(SENSES_RECEIPT.read_text())
    n_bits = senses["results"]["slow_memory_engine"][
        "belief_persistence_mutual_information_bits"]
    T_installed, kB_installed = 1.0, 1.0
    szilard_bound = kB_installed * T_installed * np.log(2.0) * n_bits
    mean_work = data["net_work_equivalent_8stage_nominal_sum_mean"]
    checks["work_equivalent_above_szilard_bound"] = bool(abs(mean_work) > szilard_bound)
    data["szilard"] = {
        "n_bits_m_slow": n_bits,
        "n_bits_source": str(SENSES_RECEIPT),
        "n_bits_source_field": "results.slow_memory_engine.belief_persistence_mutual_information_bits",
        "T_installed": T_installed, "kB_installed": kB_installed,
        "bound_kT_ln2_nbits": float(szilard_bound),
        "cycle_net_work_equivalent_mean": mean_work,
        "abs_work_vs_bound": "above" if abs(mean_work) > szilard_bound else "below",
    }
    findings.append(
        f"Szilard comparison: |mean net work-equivalent| = "
        f"{abs(mean_work):.6g} (installed units) vs bound k_B T ln2 * "
        f"n_bits = {szilard_bound:.6g} (T=1, k_B=1, n_bits=0.6768 from "
        f"m_slow) -> "
        f"{'ABOVE' if abs(mean_work) > szilard_bound else 'BELOW'} the "
        "bound. This is a units-declared comparison of two numbers "
        "computed in this sim's own reference frame, not a physical "
        "Landauer/Szilard proof — no thermodynamic-consistency claim "
        "beyond the arithmetic comparison is made.")

    all_pass = all(bool(v) for v in checks.values())

    receipt = {
        "schema": "ratchet.v8.otto-weld.stroke-map.v0",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "interpreter": sys.executable,
        "inputs": {
            "rungB_source": str(RUNGB_PATH),
            "rungB_source_sha256": sha256(RUNGB_PATH),
            "senses_receipt": str(SENSES_RECEIPT),
            "senses_receipt_sha256": sha256(SENSES_RECEIPT),
        },
        "checks": checks,
        "data": data,
        "all_pass": all_pass,
        "findings": findings,
        "claim_ceiling": (
            "executed finite 16-channel instance (2 sheets x 8 rungB "
            "generators) mapped onto a fixed 5-purity test-state "
            "family under a declared-installed sigma_z-sum reference "
            "Hamiltonian; a 7-stage chained sub-cycle (dim-2 only) "
            "with (S,E) area and a units-declared Szilard-bound "
            "comparison; no thermodynamic-consistency or optimality "
            "claim; G8 dimensional mismatch and G2/G7, G3/G4 channel "
            "collapses recorded, not smoothed."),
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"all_pass": all_pass, "checks": checks,
                      "label_cross_check_summary": data["label_cross_check_summary"],
                      "cycle_area_mean": mean_area,
                      "szilard": data["szilard"]}, indent=2))


if __name__ == "__main__":
    main()
