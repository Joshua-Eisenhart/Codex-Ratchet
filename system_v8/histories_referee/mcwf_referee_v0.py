#!/usr/bin/env python3
"""system_v8/histories_referee: mcwf_referee_v0 — FINITE sum-over-histories
referee (owner framing: Feynman integrations, finite, aligned).

Takes the amplitude-damping (family A) GKSL channel already receipted at
system_v8/deep_integration/results/qit_referee/receipt.json (built by
tools_qit_referee.py, mirrored from julia_manifold_tick.jl law_runs:
OMEGA=1.3, ALPHA=0.7, J_XY=0.35, TICK_DT=0.4, N_TICKS=30, gam=0.5, rho0_L
Bloch (0.5, 0.3, -0.4), right sheet = -H_L with conjugated jump op) and runs
qutip.mcsolve (Monte Carlo wave-function / quantum-jump unraveling) against
qutip.mesolve (density evolution) on the SAME H / rho0 / gamma.

rho0 is MIXED (Bloch length sqrt(0.5) < 1 on each sheet before tensoring), so
a single-ket mcsolve run cannot represent it. This referee decomposes rho0
into its eigenbasis (a FINITE classical mixture of pure states — the finite
"sum over histories" object) and allocates the requested trajectory budget
across components in proportion to their eigenvalue weight; the pooled,
equally-weighted trajectory ensemble is then a valid Monte Carlo estimator
of rho(t) by linearity of the GKSL propagator.

PREREGISTERED GATES (fixed before any run; header is read-only after run):
  G1 mesolve_reproduces_receipt: mesolve rerun here (fresh process) must
     reproduce the amplitude-damping relative-entropy series recorded in
     deep_integration/results/qit_referee/receipt.json
     (data.A_relent_series_qutip) to max abs diff < 1e-6.
  G2 mcwf_matches_mesolve_2000: for the 2000-trajectory MCWF run, the max
     abs deviation over all (density-matrix element, tick) pairs between
     the pooled trajectory-average rho_mc(t) and the mesolve rho(t) must be
     < 3 * the per-element Monte Carlo standard error at that same
     (element, tick) (SE = pooled sample std of the trajectory values at
     that element/tick, divided by sqrt(N_effective)).
  G3 control_20traj_deviation_larger: the identical comparison rerun with
     only 20 trajectories (same allocation rule, same H/rho0/gamma) must
     show a max abs deviation STRICTLY LARGER than the 2000-trajectory run
     — finite-N convergence must be demonstrated, not assumed.
  G4 control_wrong_gamma_fails: an MCWF run using a deliberately wrong
     damping rate (gamma_wrong = 1.5 * GAM_LAW) at N=2000, compared against
     the CORRECT-gamma mesolve reference, must FAIL gate G2's 3-SE bound
     (max deviation / local SE >= 3 somewhere) — the check must be able to
     fail, not vacuously pass.

Classification: tool_lego_fit_probe / scratch_diagnostic.
promotion_allowed: false. This referee does not certify the amplitude-
damping channel beyond the four gates above; it does not extend to the
driven tick loop, drive/nesting/flux (those live in the julia lane), or any
of the other GKSL law families (U, D) in the parent receipt.

Interpreter: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
Memory guard: refuses to import qutip if available system memory < 25%
(checked via psutil BEFORE the qutip import, fail-closed).

No deletes. No commit. Refuses to reuse its own output dir.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
V8 = HERE.parent
OUT = HERE / "results" / "mcwf_referee_v0"
QIT_REFEREE_RECEIPT = (
    V8 / "deep_integration" / "results" / "qit_referee" / "receipt.json"
)

# ---- parameters mirrored from tools_qit_referee.py / julia_manifold_tick.jl
N_TICKS = 30
TICK_DT = 0.4
OMEGA = 1.3
ALPHA = 0.7
J_XY = 0.35
GAM_LAW = 0.5          # amplitude-damping (family A) rate, receipted channel
GAM_WRONG = 1.5 * GAM_LAW   # G4 control: deliberately wrong rate

N_TRAJ_MAIN = 2000
N_TRAJ_CONTROL_LOW = 20
SEED_BASE = 20260719   # fixed seed (today's date), preregistered

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
SM = np.array([[0, 1], [0, 0]], dtype=complex)


def check_memory_guard(min_pct=0.25):
    """Fail-closed memory guard. Must run BEFORE `import qutip`."""
    import psutil
    vm = psutil.virtual_memory()
    pct_available = vm.available / vm.total
    return pct_available, pct_available >= min_pct


def alloc_traj(weights, n_total):
    """Largest-remainder allocation of n_total trajectories across
    components proportional to `weights` (must sum to ~1)."""
    raw = weights * n_total
    counts = np.floor(raw).astype(int)
    remainder = int(n_total - counts.sum())
    frac = raw - counts
    order = np.argsort(-frac)
    for k in range(remainder):
        counts[order[k % len(order)]] += 1
    return counts


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output dir: {OUT}")

    mem_pct, mem_ok = check_memory_guard(0.25)
    if not mem_ok:
        OUT.mkdir(parents=True)
        blocked = {
            "schema": "ratchet.v8.histories-referee.mcwf-referee.v0",
            "lane": "histories_referee",
            "status": "BLOCKED_MEMORY_GUARD",
            "mem_pct_available_at_check": mem_pct,
            "mem_guard_threshold": 0.25,
            "message": ("refused to import qutip: available system memory "
                        f"{mem_pct:.3%} < 25% threshold. No sim executed."),
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        }
        (OUT / "receipt.json").write_text(json.dumps(blocked, indent=2) + "\n")
        print(json.dumps(blocked, indent=2))
        sys.exit(2)

    import qutip as qt

    # ---- read the receipted amplitude-damping lane -------------------
    if not QIT_REFEREE_RECEIPT.exists():
        raise SystemExit(f"missing input receipt: {QIT_REFEREE_RECEIPT}")
    parent = json.loads(QIT_REFEREE_RECEIPT.read_text())
    if not parent.get("all_pass"):
        raise SystemExit("refusing to build on a non-all_pass parent receipt")
    A_relent_receipted = np.asarray(parent["data"]["A_relent_series_qutip"],
                                     dtype=float)
    A_rho_ss_min_eig_receipted = parent["data"]["A_rho_ss_min_eig_qutip"]

    OUT.mkdir(parents=True)

    def q2(m):
        return qt.Qobj(np.asarray(m, dtype=complex))

    # ---- same joint 2-sheet objects as tools_qit_referee.py -----------
    nx, nz = np.sin(ALPHA), np.cos(ALPHA)
    H_L = 0.5 * OMEGA * (nx * SX + nz * SZ)
    H = (qt.tensor(q2(H_L), q2(I2)) + qt.tensor(q2(I2), q2(-H_L))
         + J_XY * (qt.tensor(q2(SX), q2(SX)) + qt.tensor(q2(SY), q2(SY))))
    rho0_L = 0.5 * (I2 + 0.5 * SX + 0.3 * SY - 0.4 * SZ)
    rho0 = qt.tensor(q2(rho0_L), q2(np.conj(rho0_L)))

    def c_ops_damp(g):
        return [np.sqrt(g) * qt.tensor(q2(SM), q2(I2)),
                np.sqrt(g) * qt.tensor(q2(I2), q2(np.conj(SM)))]

    tlist = np.arange(N_TICKS + 1) * TICK_DT

    def clip_state(R):
        R = 0.5 * (R + R.conj().T)
        w, V = np.linalg.eigh(R)
        w = np.clip(w, 0.0, None)
        R2 = (V * w) @ V.conj().T
        return R2 / np.trace(R2).real

    def ent_bits(R):
        w = np.linalg.eigvalsh(clip_state(R))
        w = w[w > 1e-14]
        return float(-np.sum(w * np.log2(w)))

    def relent_bits(R, sig_full):
        Rc = clip_state(R)
        s_bits = ent_bits(Rc)
        ws, Vs = np.linalg.eigh(0.5 * (sig_full + sig_full.conj().T))
        log_sig = (Vs * np.log(np.clip(ws, 1e-300, None))) @ Vs.conj().T
        cross = float(np.trace(Rc @ log_sig).real) / np.log(2.0)
        return -s_bits - cross

    checks, data, findings = {}, {}, []

    # ==== G1: mesolve rerun reproduces the receipted series =============
    cA = c_ops_damp(GAM_LAW)
    opts_me = {"atol": 1e-12, "rtol": 1e-10, "nsteps": 200000,
               "store_states": True}
    rho_ss = qt.steadystate(H, cA)
    ss_min_eig_here = float(np.min(np.linalg.eigvalsh(rho_ss.full())))
    resA_me = qt.mesolve(H, rho0, tlist, c_ops=cA, options=opts_me)
    A_relent_here = np.array([relent_bits(r.full(), rho_ss.full())
                               for r in resA_me.states])
    g1_diff = float(np.max(np.abs(A_relent_here - A_relent_receipted)))
    checks["G1_mesolve_reproduces_receipt_lt_1e-6"] = g1_diff < 1e-6
    checks["G1_rho_ss_min_eig_matches_receipt_lt_1e-6"] = \
        abs(ss_min_eig_here - A_rho_ss_min_eig_receipted) < 1e-6
    data["G1_max_abs_diff_relent_vs_receipt"] = g1_diff
    data["A_rho_ss_min_eig_here"] = ss_min_eig_here
    data["A_rho_ss_min_eig_receipted"] = A_rho_ss_min_eig_receipted

    rho_mesolve = np.array([r.full() for r in resA_me.states])  # (T,4,4)

    # ==== eigen-decompose rho0 into a finite mixture of pure states =====
    w0, V0 = np.linalg.eigh(rho0.full())
    w0 = np.clip(w0, 0.0, None)
    w0 = w0 / w0.sum()
    keep = w0 > 1e-10
    weights = w0[keep]
    psis = [V0[:, i] / np.linalg.norm(V0[:, i])
            for i in range(len(w0)) if keep[i]]
    data["rho0_eigen_weights"] = [float(x) for x in weights]
    data["rho0_eigen_components_kept"] = int(len(weights))

    def run_mcwf_ensemble(gamma, n_total, seed_offset):
        """Pool trajectories across rho0's eigen-components, allocated
        proportional to eigenvalue weight. Returns (rho_mc[T,4,4],
        elementwise SE[T,4,4], per_trajectory_col_counts[list])."""
        c_ops = c_ops_damp(gamma)
        counts = alloc_traj(weights, n_total)
        all_states = []   # list over trajectories of arrays (T,4)
        jump_counts = []
        for i, (psi_i, n_i) in enumerate(zip(psis, counts)):
            if n_i == 0:
                continue
            res = qt.mcsolve(
                H, qt.Qobj(psi_i, dims=rho0.dims[0]), tlist,
                c_ops=c_ops, ntraj=int(n_i),
                options={"store_states": True, "map": "serial"},
                seeds=SEED_BASE + seed_offset + i,
            )
            for traj_states in res.states:
                all_states.append(np.array([s.full().flatten()
                                             for s in traj_states]))
            col_times = getattr(res, "col_times", None)
            if col_times is not None:
                jump_counts.extend(int(len(ct)) for ct in col_times)
        n_eff = len(all_states)
        stacked = np.stack(all_states, axis=0)  # (N_eff, T, 4) ket comps
        # build outer products |psi><psi| per trajectory per tick
        rho_samples = np.einsum("ntj,ntk->ntjk", stacked, stacked.conj())
        rho_mc = rho_samples.mean(axis=0)  # (T,4,4)
        std_re = rho_samples.real.std(axis=0, ddof=1)
        std_im = rho_samples.imag.std(axis=0, ddof=1)
        se = np.sqrt(std_re**2 + std_im**2) / np.sqrt(n_eff)
        return rho_mc, se, n_eff, jump_counts

    # ==== G2: 2000-trajectory MCWF vs mesolve ============================
    rho_mc_main, se_main, n_eff_main, jumps_main = run_mcwf_ensemble(
        GAM_LAW, N_TRAJ_MAIN, seed_offset=0)
    dev_main = np.abs(rho_mc_main - rho_mesolve)
    se_safe = np.where(se_main > 0, se_main, np.finfo(float).eps)
    ratio_main = dev_main / se_safe
    max_dev_main = float(dev_main.max())
    max_ratio_main = float(ratio_main.max())
    idx_main = np.unravel_index(np.argmax(dev_main), dev_main.shape)
    checks["G2_mcwf_matches_mesolve_2000_lt_3SE"] = max_ratio_main < 3.0
    data["G2_n_traj_effective"] = n_eff_main
    data["G2_max_abs_deviation"] = max_dev_main
    data["G2_max_deviation_ratio_to_SE"] = max_ratio_main
    data["G2_max_deviation_at_tick"] = float(tlist[idx_main[0]])
    data["G2_jump_count_distribution"] = {
        str(k): int(np.sum(np.array(jumps_main) == k))
        for k in sorted(set(jumps_main))
    } if jumps_main else {}
    data["G2_jump_count_mean"] = float(np.mean(jumps_main)) if jumps_main else None
    data["G2_jump_count_max"] = int(np.max(jumps_main)) if jumps_main else None

    # ==== G3: 20-trajectory control must show LARGER deviation ==========
    rho_mc_lo, se_lo, n_eff_lo, jumps_lo = run_mcwf_ensemble(
        GAM_LAW, N_TRAJ_CONTROL_LOW, seed_offset=5000)
    dev_lo = np.abs(rho_mc_lo - rho_mesolve)
    max_dev_lo = float(dev_lo.max())
    checks["G3_control_20traj_deviation_larger"] = max_dev_lo > max_dev_main
    data["G3_n_traj_effective"] = n_eff_lo
    data["G3_max_abs_deviation_20traj"] = max_dev_lo
    data["G3_max_abs_deviation_2000traj"] = max_dev_main
    data["G3_ratio_20_over_2000"] = (max_dev_lo / max_dev_main
                                      if max_dev_main > 0 else None)

    # ==== G4: wrong-gamma control must FAIL the G2 gate ==================
    rho_mc_wrong, se_wrong, n_eff_wrong, jumps_wrong = run_mcwf_ensemble(
        GAM_WRONG, N_TRAJ_MAIN, seed_offset=9000)
    dev_wrong = np.abs(rho_mc_wrong - rho_mesolve)   # vs CORRECT-gamma mesolve
    se_wrong_safe = np.where(se_wrong > 0, se_wrong, np.finfo(float).eps)
    ratio_wrong = dev_wrong / se_wrong_safe
    max_dev_wrong = float(dev_wrong.max())
    max_ratio_wrong = float(ratio_wrong.max())
    checks["G4_control_wrong_gamma_fails_3SE_gate"] = max_ratio_wrong >= 3.0
    data["G4_gamma_wrong"] = GAM_WRONG
    data["G4_n_traj_effective"] = n_eff_wrong
    data["G4_max_abs_deviation"] = max_dev_wrong
    data["G4_max_deviation_ratio_to_SE"] = max_ratio_wrong

    all_pass = bool(all(checks.values()))

    findings += [
        (f"G1: mesolve rerun (fresh process) reproduces the receipted "
         f"amplitude-damping relative-entropy series to max abs diff "
         f"{g1_diff:.3e} (gate 1e-6); rho_ss min eig here "
         f"{ss_min_eig_here:.6f} vs receipted {A_rho_ss_min_eig_receipted:.6f}."),
        (f"G2: pooled {n_eff_main}-trajectory MCWF ensemble (eigen-mixture "
         f"of rho0, allocation proportional to eigenvalue weight) vs "
         f"mesolve: max abs deviation {max_dev_main:.3e} at tick "
         f"{data['G2_max_deviation_at_tick']:.2f}, {max_ratio_main:.2f} "
         f"local standard errors (gate < 3 SE)."),
        (f"G3 control (20 trajectories, n_eff={n_eff_lo}): max abs "
         f"deviation {max_dev_lo:.3e} vs {max_dev_main:.3e} at 2000 "
         f"trajectories — ratio {data['G3_ratio_20_over_2000']:.2f}x "
         f"larger, confirming finite-N convergence is real, not an "
         f"artifact of a loose tolerance."),
        (f"G4 control (gamma_wrong={GAM_WRONG} vs correct {GAM_LAW}, "
         f"n_eff={n_eff_wrong}): max abs deviation {max_dev_wrong:.3e}, "
         f"{max_ratio_wrong:.2f} local SEs against the CORRECT-gamma "
         f"mesolve reference — {'FAILS' if max_ratio_wrong >= 3.0 else 'PASSES'} "
         f"the G2 3-SE bound, confirming the gate can discriminate."),
        ("scope: single receipted amplitude-damping (family A) channel "
         "only; does not extend to families U/D, the driven tick loop, or "
         "any other stage64 pair. tool_lego_fit_probe / scratch_diagnostic; "
         "no physics claim beyond the four executed gates."),
    ]

    receipt = {
        "schema": "ratchet.v8.histories-referee.mcwf-referee.v0",
        "lane": "histories_referee",
        "inputs": {
            "qit_referee_receipt": str(QIT_REFEREE_RECEIPT),
            "channel": "amplitude_damping (family A, GAM_LAW=0.5)",
        },
        "packages": {
            "qutip": ("load_bearing: mcsolve is the Monte Carlo wave-"
                      "function / quantum-jump unraveling under test; "
                      "mesolve supplies the density-evolution reference; "
                      "steadystate re-derives the fixed point"),
        },
        "config": {
            "N_TICKS": N_TICKS, "TICK_DT": TICK_DT, "OMEGA": OMEGA,
            "ALPHA": ALPHA, "J_XY": J_XY, "GAM_LAW": GAM_LAW,
            "GAM_WRONG": GAM_WRONG, "N_TRAJ_MAIN": N_TRAJ_MAIN,
            "N_TRAJ_CONTROL_LOW": N_TRAJ_CONTROL_LOW,
            "SEED_BASE": SEED_BASE,
        },
        "mem_pct_available_at_check": mem_pct,
        "checks": {k: bool(v) for k, v in checks.items()},
        "all_pass": all_pass,
        "data": data,
        "findings": findings,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "classification": "tool_lego_fit_probe",
        "claim_ceiling": ("finite-trajectory MCWF/mesolve agreement on ONE "
                          "receipted amplitude-damping channel, with a "
                          "convergence control and a discriminating-power "
                          "control; scratch_diagnostic; no claim beyond the "
                          "four executed gates"),
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"lane": "histories_referee",
                      "file": str(Path(__file__).resolve()),
                      "all_pass": all_pass,
                      "checks": {k: bool(v) for k, v in checks.items()},
                      "findings": findings}, indent=2))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
