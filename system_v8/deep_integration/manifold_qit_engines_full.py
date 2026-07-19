#!/usr/bin/env python3
"""manifold_qit_engines_full.py — THE FULL UNOFFICIAL SIM (deep_integration lane).

Whole manifold + TWO QIT engines running together for 60 ticks, with qutip as
the solver stack (the independent QIT-engine referee doubles as the runtime).

UNOFFICIAL / working-sim bar. NOT proof-level. promotion_allowed=false.

Inputs (load-bearing, read at runtime):
  - system_v8/manifold/results/source_packets.json
        9 base packets in declared order; accepted counts -> Hartley dC per
        tick under chaining (torch_graph receipt method: exact big-int chained
        product cross-checked against cumulative capacity bits).
  - system_v8/nested_manifold/results/stage64/receipt.json
        16 stages (4 families x 2 sheets x 2 loop fields) with the ADMITTED
        operating (D_a, H_b) pair per stage. The receipt decides which
        generator runs; this file only reconstructs the operators it names.
        Terrain family parameters (omega, gamma, frame sign) re-declared from
        system_v8/nested_manifold/stage64_constraint_tournament.py TERRAINS.

Architecture per tick t (t = 0..59):
  drive   dC_t = log2(count of packet t mod 9); scale_t = dC_t / mean(dC);
          gamma_eff = gamma_family * scale_t (drive scales dissipation).
  left    engine: qutip mesolve step on the LEFT sheet with the operating
          generator of left_order[t mod 8] (the 8 L-sheet stages); jump op
          basis from the receipt label, H = s*f*omega*sigma_b, s=+1.
  right   engine: same machinery, the 8 R-sheet stages in OPPOSITE order
          (chirality = schedule orientation), s=-1 (H -> -H per stage64).

Declared cycle traversal (run-1 lesson, kept as
results/full_sim_run1_receipt_order_flux_negative): cycling the stages in raw
receipt order puts each family's f=+1 and f=-1 stages adjacent, so every
family block's two rotations (same axis, opposite angle) compose to ~identity
— BOTH engines' cycle monodromies are near-trivial and the chirality flux
degenerates (opposite-sign gate failed honestly, split R^2=0.44). The engine
schedule is therefore DECLARED as the interleaved traversal: f=+1 sweep
through families 0,1,2,3 then f=-1 sweep through families 0,1,2,3. Under
this traversal the right engine (same stage set, OPPOSITE order, H -> -H)
applies exactly the inverse rotation factors in reversed order, so at the
unitary level U_R(cycle) = U_L(cycle)^{-1}: chirality is carried by schedule
orientation alone, which is the object under test.
  couple  entangling XY pulse U = expm(-i g_c (XX+YY) tau) on the joint state.
  readout ptrace/entropy_vn (base 2): S_L, S_R, S_LR, I(L:R), negativity
          (partial transpose), Phi0 = 0.5*Ic_LR + 0.5*Ic_RL (manifold_one
          CUT_FAMILY convention, weights [0.5, 0.5]).
  record  I_rec += dC_t (bits; manifold_one lock-stroke convention).

Flux: per engine, per completed 8-tick stage cycle, the gauge-invariant
Pancharatnam/Bargmann phase of the dominant eigenvector chain of the sheet
reduced state: gamma_c = arg( prod_j <v_j|v_{j+1}> * <v_7|v_0> ) over the
cycle's 8 recorded states. Accumulated Phi_L(c), Phi_R(c); split = Phi_L-Phi_R.

Terrains: 4 basin representatives per sheet = qutip.steadystate of each
family's operating generator (f=+1 stage, unscaled family gamma). Every tick's
sheet state classified to nearest basin by qutip tracedist -> occupation
histogram over 60 ticks = terrain census ON the running engines.

Response: one mid-run perturbation at tick 30 (unitary kick exp(-i eps sigma_y)
on the left sheet, eps=0.3); g-curve per rungE convention g_k = D(k)/D(1),
D = joint trace distance to the unperturbed trajectory.

Controls (each a full 60-tick rerun; each must fire):
  C1 freeze drive      (scale=0)          -> downstream damps (I_rec flat 0;
                                             cut-readout series leave the main
                                             trajectory: drive is load-bearing)
  C2 scramble schedule (fixed permutation
     of the left order, declared below)   -> flux accumulation changes
                                             measurably (order is content)
  C3 erase chirality   (right engine gets
     the LEFT stages, same order, s=+1)   -> split dies
  C4 decouple engines  (no XY pulse)      -> I(L:R) collapses

Additional gates: all states physical every tick in every run (min eigenvalue
> -1e-10, trace 1); entropy laws (subadditivity, Araki-Lieb) hold per stage
family.

Receipt: system_v8/deep_integration/results/full_sim/receipt.json
Refuses to reuse the outdir. Deterministic (no RNG; the scramble permutation
is a declared constant).
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import qutip as qt

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SRC_PACKETS = REPO / "system_v8/manifold/results/source_packets.json"
STAGE64_RECEIPT = REPO / "system_v8/nested_manifold/results/stage64/receipt.json"
OUT = REPO / "system_v8/deep_integration/results/full_sim"

if OUT.exists():
    raise SystemExit(f"refusing to reuse output: {OUT}")

# ---------------------------------------------------------------------------
# Constants (declared; TERRAINS re-declared from stage64_constraint_tournament)
# ---------------------------------------------------------------------------
N_TICKS = 60
DT = 0.35                # engine mesolve step length per tick
G_C = 0.125              # XY coupling strength (angle G_C*TAU_C = 0.05)
TAU_C = 0.4              # XY pulse length
EPS_KICK = 0.3           # response perturbation angle (sigma_y, left sheet)
KICK_TICK = 30
SCRAMBLE_PERM = [3, 6, 1, 7, 0, 5, 2, 4]   # declared fixed permutation (C2)

TERRAINS = {              # family -> (omega, gamma, frame_sign); stage64 line 67
    "family_0": (1.0, 0.20, +1),
    "family_1": (0.7, 0.35, -1),
    "family_2": (1.3, 0.15, +1),
    "family_3": (0.9, 0.50, -1),
}

SX, SY, SZ, I2 = qt.sigmax(), qt.sigmay(), qt.sigmaz(), qt.qeye(2)
SIG = {"z": SZ, "x": SX}
W = qt.Qobj(np.array([[1, 1], [1, -1]]) / np.sqrt(2))
SM = qt.Qobj(np.array([[0, 1], [0, 0]]))          # |0><1|: decay toward +z
JUMP = {"z": SM, "x": W * SM * W}                 # +x fixed axis via W-conj

# ---------------------------------------------------------------------------
# Load inputs
# ---------------------------------------------------------------------------
src = json.loads(SRC_PACKETS.read_text())
packets = src["base_packets"]
counts = [p["accepted_count"] for p in packets]
packet_ids = [p["packet_id"] for p in packets]

s64 = json.loads(STAGE64_RECEIPT.read_text())
stage_ids = s64["data"]["stage_ids"]
operating = s64["data"]["operating_pairs"]        # e.g. "family_0|L|f+1" -> "D_z|H_x"

def parse_stage(sid):
    fam, sheet, fstr = sid.split("|")
    f = +1 if fstr == "f+1" else -1
    omega, gamma, fsign = TERRAINS[fam]
    pair = operating[sid]                          # receipt decides the operator
    a = pair.split("|")[0][-1]                     # D_a basis
    b = pair.split("|")[1][-1]                     # H_b basis
    s = +1 if sheet == "L" else -1
    return {"sid": sid, "family": fam, "sheet": sheet, "f": f, "s": s,
            "omega": omega, "gamma": gamma, "a": a, "b": b}

def traversal(stages):
    """Declared cycle traversal: f=+1 sweep fam 0..3, then f=-1 sweep fam 0..3."""
    return ([st for st in stages if st["f"] == +1]
            + [st for st in stages if st["f"] == -1])

left_order = traversal([parse_stage(s) for s in stage_ids if "|L|" in s])
right_order = traversal([parse_stage(s) for s in stage_ids if "|R|" in s])[::-1]
assert len(left_order) == 8 and len(right_order) == 8

# ---------------------------------------------------------------------------
# Drive: Hartley dC per tick, big-int chained product (torch_graph method)
# ---------------------------------------------------------------------------
dC_ticks = [math.log2(counts[t % 9]) for t in range(N_TICKS)]
dC_mean = sum(math.log2(c) for c in counts) / len(counts)
chained_total = 1
for t in range(N_TICKS):
    chained_total *= counts[t % 9]                # exact Python big int
C_cum_bits = sum(dC_ticks)

# ---------------------------------------------------------------------------
# qutip machinery
# ---------------------------------------------------------------------------
def sheet_h(st):
    return st["s"] * st["f"] * st["omega"] * SIG[st["b"]]

def embed(op, which):
    return qt.tensor(op, I2) if which == "L" else qt.tensor(I2, op)

XY = qt.tensor(SX, SX) + qt.tensor(SY, SY)
U_COUPLE = (-1j * G_C * XY * TAU_C).expm()

def engine_step(rho, st, which, scale):
    """One qutip mesolve step of one engine on its sheet, gamma scaled by drive."""
    H = embed(sheet_h(st), which)
    g_eff = st["gamma"] * scale
    c_ops = [embed(np.sqrt(g_eff) * JUMP[st["a"]], which)] if g_eff > 0 else []
    res = qt.mesolve(H, rho, [0.0, DT], c_ops=c_ops)
    return res.states[-1]

def dominant_eigvec(rho2):
    w, v = np.linalg.eigh(rho2.full())
    gap = float(w[-1] - w[-2])
    return v[:, -1], gap

def bargmann_phase(vecs):
    """Gauge-invariant closed-chain Pancharatnam phase over one 8-state cycle."""
    prod = 1.0 + 0.0j
    n = len(vecs)
    for j in range(n):
        prod *= np.vdot(vecs[j], vecs[(j + 1) % n])
    return float(np.angle(prod)), float(abs(prod))

def cut_readouts(rho):
    rL, rR = rho.ptrace(0), rho.ptrace(1)
    S_L = float(qt.entropy_vn(rL, base=2))
    S_R = float(qt.entropy_vn(rR, base=2))
    S_LR = float(qt.entropy_vn(rho, base=2))
    Ic_LR, Ic_RL = -(S_LR - S_R), -(S_LR - S_L)
    pt = qt.partial_transpose(rho, [0, 1])
    wpt = np.linalg.eigvalsh(pt.full())
    neg = float(-wpt[wpt < 0].sum())
    return {"S_L": S_L, "S_R": S_R, "S_LR": S_LR, "I": S_L + S_R - S_LR,
            "negativity": neg, "Phi0": 0.5 * Ic_LR + 0.5 * Ic_RL}

# initial joint state: same tilted pure state on both sheets (not an eigenstate)
theta0, phi0 = 1.0, -np.pi / 2
ket = np.array([np.cos(theta0 / 2), np.exp(1j * phi0) * np.sin(theta0 / 2)])
psi0 = qt.tensor(qt.Qobj(ket), qt.Qobj(ket))
RHO0 = psi0 * psi0.dag()

# ---------------------------------------------------------------------------
# Terrain basins: steadystate of each family's operating generator per sheet
# ---------------------------------------------------------------------------
def family_fixed_points(sheet):
    fps = {}
    for st in (left_order if sheet == "L" else sorted(
            [parse_stage(s) for s in stage_ids if "|R|" in s],
            key=lambda x: x["sid"])):
        if st["f"] != +1:
            continue                               # f=+1 representative stage
        H = sheet_h(st)
        c = [np.sqrt(st["gamma"]) * JUMP[st["a"]]]
        fps[st["family"]] = qt.steadystate(H, c)
    return fps

FPS = {"L": family_fixed_points("L"), "R": family_fixed_points("R")}
FAMS = sorted(TERRAINS)

def classify(rho2, sheet):
    d = {f: float(qt.tracedist(rho2, FPS[sheet][f])) for f in FAMS}
    return min(d, key=d.get)

# ---------------------------------------------------------------------------
# The runner (all runs share it; mode switches implement the controls)
# ---------------------------------------------------------------------------
def run_sim(mode="main", rho_start=None, t_start=0, n_ticks=N_TICKS,
            kick_at=None):
    lorder = list(left_order)
    rorder = list(right_order)
    if mode == "scramble":
        lorder = [left_order[i] for i in SCRAMBLE_PERM]
    if mode == "erase":                            # right engine loses chirality:
        rorder = [dict(st, s=+1) for st in left_order]   # left stages, same order
    couple = mode != "decouple"

    rho = (RHO0 if rho_start is None else rho_start)
    S = {k: [] for k in ("S_L", "S_R", "S_LR", "I", "negativity", "Phi0",
                         "I_rec", "eigmin", "trace_err", "gapL", "gapR",
                         "family_now", "basin_L", "basin_R", "dC", "scale")}
    vL, vR, states = [], [], []
    I_rec = 0.0
    for t in range(t_start, t_start + n_ticks):
        dC = 0.0 if mode == "freeze" else dC_ticks[t]
        scale = dC / dC_mean
        stL, stR = lorder[t % 8], rorder[t % 8]
        rho = engine_step(rho, stL, "L", scale)
        rho = engine_step(rho, stR, "R", scale)
        if couple:
            rho = U_COUPLE * rho * U_COUPLE.dag()
        if kick_at is not None and t == kick_at:
            K = embed((-1j * EPS_KICK * SY / 2).expm(), "L")
            rho = K * rho * K.dag()
        wj = np.linalg.eigvalsh(rho.full())
        rL, rR = rho.ptrace(0), rho.ptrace(1)
        vecL, gapL = dominant_eigvec(rL)
        vecR, gapR = dominant_eigvec(rR)
        vL.append(vecL); vR.append(vecR); states.append(rho)
        ro = cut_readouts(rho)
        I_rec += dC
        for k, val in ro.items():
            S[k].append(val)
        S["I_rec"].append(I_rec)
        S["eigmin"].append(float(wj[0]))
        S["trace_err"].append(abs(float(rho.tr()) - 1.0))
        S["gapL"].append(gapL); S["gapR"].append(gapR)
        S["family_now"].append(stL["family"])
        S["basin_L"].append(classify(rL, "L"))
        S["basin_R"].append(classify(rR, "L" if mode == "erase" else "R"))
        S["dC"].append(dC); S["scale"].append(scale)
    # per-cycle Pancharatnam flux (complete 8-tick cycles only)
    n_cyc = n_ticks // 8
    fluxL, fluxR, ovl_min = [], [], 1.0
    for c in range(n_cyc):
        gL, mL = bargmann_phase(vL[8 * c: 8 * c + 8])
        gR, mR = bargmann_phase(vR[8 * c: 8 * c + 8])
        fluxL.append(gL); fluxR.append(gR)
        ovl_min = min(ovl_min, mL, mR)
    S["flux_cycle_L"], S["flux_cycle_R"] = fluxL, fluxR
    S["Phi_L"] = list(np.cumsum(fluxL)); S["Phi_R"] = list(np.cumsum(fluxR))
    S["split"] = list(np.array(S["Phi_L"]) - np.array(S["Phi_R"]))
    S["bargmann_min_abs"] = ovl_min
    S["states"] = states
    return S

# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------
main = run_sim("main")
freeze = run_sim("freeze")
scram = run_sim("scramble")
erase = run_sim("erase")
decup = run_sim("decouple")

# response: rerun ticks 30..59 from the stored tick-29 end state with the kick
base_tail = main["states"][KICK_TICK:]
pert = run_sim("main", rho_start=main["states"][KICK_TICK - 1],
               t_start=KICK_TICK, n_ticks=N_TICKS - KICK_TICK,
               kick_at=KICK_TICK)
D = np.array([float(qt.tracedist(p, b))
              for p, b in zip(pert["states"], base_tail)])
g_curve = (D / D[0]) if D[0] > 1e-15 else np.zeros_like(D)
DR = np.array([float(qt.tracedist(p.ptrace(1), b.ptrace(1)))
               for p, b in zip(pert["states"], base_tail)])
early, late = float(np.mean(g_curve[1:8])), float(np.mean(g_curve[22:30]))
g_class = ("opening" if late > 1.25 * early
           else "binding" if late < 0.8 * early else "mixed")

# ---------------------------------------------------------------------------
# Checks (gates are code; every one can fail)
# ---------------------------------------------------------------------------
checks, findings = {}, []
runs = {"main": main, "freeze": freeze, "scramble": scram,
        "erase": erase, "decouple": decup, "response_tail": pert}

# drive: big-int chain vs cumulative Hartley bits (exact-count cross-check)
checks["drive_bigint_chain_matches_cumulative_bits"] = (
    abs(math.log2(chained_total) - C_cum_bits) < 1e-9)
checks["drive_all_dC_positive_main"] = all(x > 0 for x in main["dC"])

# physicality: every tick, every run
eigmin_all = min(min(r["eigmin"]) for r in runs.values())
tracerr_all = max(max(r["trace_err"]) for r in runs.values())
checks["physical_min_eig_gt_neg1e-10_all_runs_all_ticks"] = eigmin_all > -1e-10
checks["physical_trace_one_1e-9_all_runs_all_ticks"] = tracerr_all < 1e-9

# entropy laws per stage family (main run)
ent_fam = {}
for fam in FAMS:
    idx = [i for i, f in enumerate(main["family_now"]) if f == fam]
    sub = all(main["S_L"][i] + main["S_R"][i] - main["S_LR"][i] > -1e-9
              for i in idx)
    al = all(main["S_LR"][i] >= abs(main["S_L"][i] - main["S_R"][i]) - 1e-9
             for i in idx)
    ent_fam[fam] = {"ticks": len(idx), "subadditivity": sub, "araki_lieb": al}
checks["entropy_subadditivity_holds_per_family"] = all(
    v["subadditivity"] for v in ent_fam.values())
checks["entropy_araki_lieb_holds_per_family"] = all(
    v["araki_lieb"] for v in ent_fam.values())
checks["entropy_all_4_families_visited"] = all(
    v["ticks"] > 0 for v in ent_fam.values())

# flux / chirality on the main run
n_cyc = len(main["flux_cycle_L"])
checks["flux_opposite_sign_every_cycle"] = all(
    gl * gr < 0 for gl, gr in zip(main["flux_cycle_L"], main["flux_cycle_R"]))
cyc = np.arange(1, n_cyc + 1, dtype=float)
split = np.array(main["split"])
slope, icept = np.polyfit(cyc, split, 1)
ss_res = float(np.sum((split - (slope * cyc + icept)) ** 2))
ss_tot = float(np.sum((split - split.mean()) ** 2))
r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
checks["flux_split_grows_linearly_r2_ge_0.98_slope_gt_1e-3"] = (
    r2 >= 0.98 and abs(slope) > 1e-3)
checks["flux_dominant_eigvec_well_conditioned_gap_gt_1e-6"] = (
    min(min(main["gapL"]), min(main["gapR"])) > 1e-6)

# terrains
dists = []
for sheet in ("L", "R"):
    for i, f1 in enumerate(FAMS):
        for f2 in FAMS[i + 1:]:
            dists.append(float(qt.tracedist(FPS[sheet][f1], FPS[sheet][f2])))
checks["terrain_fixed_points_pairwise_distinct_gt_5e-3"] = min(dists) > 5e-3
censL = {f: main["basin_L"].count(f) for f in FAMS}
censR = {f: main["basin_R"].count(f) for f in FAMS}
checks["terrain_census_total_60_each_engine"] = (
    sum(censL.values()) == N_TICKS and sum(censR.values()) == N_TICKS)
checks["terrain_census_ge_2_basins_each_engine"] = (
    sum(1 for v in censL.values() if v > 0) >= 2
    and sum(1 for v in censR.values() if v > 0) >= 2)

# joint / record
checks["joint_I_LR_exceeds_1e-3_main"] = max(main["I"]) > 1e-3
checks["record_I_rec_strictly_monotone_main"] = all(
    b > a for a, b in zip([0.0] + main["I_rec"][:-1], main["I_rec"]))
phi = np.array(main["Phi0"])
checks["phi0_series_complete_finite_varying"] = (
    len(phi) == N_TICKS and np.all(np.isfinite(phi)) and phi.std() > 0)

# response
checks["response_kick_registered_D1_gt_1e-6"] = D[0] > 1e-6
checks["response_g_curve_finite"] = bool(np.all(np.isfinite(g_curve)))
checks["response_reaches_right_sheet_via_coupling"] = float(DR.max()) > 1e-6

# C1 freeze drive -> downstream damps
l2 = {k: float(np.linalg.norm(np.array(main[k]) - np.array(freeze[k])))
      for k in ("S_LR", "Phi0", "S_L")}
checks["C1_freeze_drive_record_flat_and_downstream_damps"] = (
    freeze["I_rec"][-1] == 0.0 and main["I_rec"][-1] > 100.0
    and all(v > 1e-3 for v in l2.values()))

# C2 scramble one engine's schedule -> flux changes measurably
dflux = abs(scram["Phi_L"][-1] - main["Phi_L"][-1])
checks["C2_scramble_changes_left_flux_gt_1e-2"] = dflux > 1e-2

# C3 erase chirality -> split dies
checks["C3_erase_chirality_split_dies"] = (
    abs(main["split"][-1]) > 1e-2
    and abs(erase["split"][-1]) < 0.05 * abs(main["split"][-1]))

# C4 decouple -> I(L:R) collapses
checks["C4_decouple_I_LR_collapses_lt_1e-9"] = max(decup["I"]) < 1e-9

all_pass = all(checks.values())

findings += [
    (f"Drive: 60-tick chained big-int count = {chained_total} "
     f"(~2^{math.log2(chained_total):.3f}); cumulative Hartley capacity "
     f"{C_cum_bits:.6f} bits; exact match gate passed = "
     f"{checks['drive_bigint_chain_matches_cumulative_bits']}."),
    (f"Chirality: per-cycle Pancharatnam flux L={['%.4f' % x for x in main['flux_cycle_L']]}, "
     f"R={['%.4f' % x for x in main['flux_cycle_R']]}; split final "
     f"{main['split'][-1]:.4f} rad over {n_cyc} cycles, linear fit slope "
     f"{slope:.4f} rad/cycle, R^2={r2:.5f}."),
    (f"Terrain census (main): L={censL}, R={censR}; basin representatives "
     f"min pairwise tracedist {min(dists):.4f}."),
    (f"Joint: max I(L:R)={max(main['I']):.4f} bits, max negativity="
     f"{max(main['negativity']):.6f}, Phi0 in "
     f"[{min(main['Phi0']):.4f},{max(main['Phi0']):.4f}] "
     f"(std {phi.std():.4f}); I_rec final {main['I_rec'][-1]:.4f} bits."),
    (f"Response: D(1)={D[0]:.6f}, g-curve early={early:.3f} late={late:.3f} "
     f"-> {g_class}; right-sheet echo max {DR.max():.6f} (coupling carries "
     f"the perturbation)."),
    (f"Controls: freeze L2(S_LR)={l2['S_LR']:.4f}; scramble dPhi_L={dflux:.4f}; "
     f"erase split={erase['split'][-1]:.2e}; decouple max I={max(decup['I']):.2e}."),
    ("qutip is load-bearing in every verdict: mesolve runs both engines, "
     "steadystate defines the basins, ptrace/entropy_vn/partial_transpose/"
     "tracedist decide the cut, terrain, physicality and response checks."),
    ("Basin representatives are distinct but CLUSTERED (all four attractor "
     "directions lie near the +/-y axis because every operating pair rotates "
     "about an axis perpendicular to its dissipative axis); classification "
     "is well-posed but margins are small — recorded, not patched."),
    ("Run 1 (raw receipt stage order) is kept as results/"
     "full_sim_run1_receipt_order_flux_negative: family f+/f- blocks "
     "compose to ~identity, chirality flux degenerates — honest negative "
     "behind the declared interleaved traversal."),
]

def strip(S):
    return {k: v for k, v in S.items() if k != "states"}

receipt = {
    "schema": "ratchet.v8.deep_integration.full_sim.v0",
    "lane": "full_sim",
    "bar": "UNOFFICIAL working sim; NOT proof-level",
    "engine": {"python": sys.version.split()[0], "qutip": qt.__version__,
               "numpy": np.__version__},
    "inputs": {"source_packets": str(SRC_PACKETS),
               "stage64_receipt": str(STAGE64_RECEIPT),
               "packet_declared_order": packet_ids,
               "left_engine_order": [s["sid"] for s in left_order],
               "right_engine_order": [s["sid"] for s in right_order],
               "declared_cycle_traversal": "f+1 sweep fam 0..3, then f-1 sweep "
                                           "fam 0..3 (see docstring; run1 raw "
                                           "receipt order kept as negative)",
               "scramble_perm": SCRAMBLE_PERM},
    "params": {"n_ticks": N_TICKS, "dt": DT, "g_c": G_C, "tau_c": TAU_C,
               "eps_kick": EPS_KICK, "kick_tick": KICK_TICK,
               "terrains": {k: list(v) for k, v in TERRAINS.items()},
               "cut_family_weights": [0.5, 0.5]},
    "checks": {k: bool(v) for k, v in checks.items()},
    "all_pass": bool(all_pass),
    "promotion_allowed": False,
    "formal_admission_allowed": False,
    "claim_ceiling": ("executed 60-tick integrated instance of manifold drive "
                      "+ two chirality-split QIT engines on qutip; unofficial "
                      "working-sim bar; no uniqueness, optimality, or physics "
                      "claim beyond the executed checks"),
    "data": {
        "chained_total_count": str(chained_total),
        "C_cumulative_bits": C_cum_bits,
        "entropy_laws_per_family": ent_fam,
        "terrain_census": {"L": censL, "R": censR},
        "flux": {"per_cycle_L": main["flux_cycle_L"],
                 "per_cycle_R": main["flux_cycle_R"],
                 "Phi_L": main["Phi_L"], "Phi_R": main["Phi_R"],
                 "split": main["split"], "slope": float(slope),
                 "r2": float(r2),
                 "bargmann_min_abs": main["bargmann_min_abs"]},
        "response": {"D": [float(x) for x in D],
                     "g_curve": [float(x) for x in g_curve],
                     "right_echo": [float(x) for x in DR],
                     "class": g_class, "early": early, "late": late},
        "controls_l2_freeze": l2,
        "scramble_dPhi_L": float(dflux),
        "series_main": strip(main),
        "series_freeze": {k: freeze[k] for k in ("I_rec", "S_LR", "Phi0", "I")},
        "series_erase_split": erase["split"],
        "series_decouple_I": decup["I"],
        "physicality": {"eigmin_all_runs": eigmin_all,
                        "trace_err_max_all_runs": tracerr_all},
    },
    "findings": findings,
}

OUT.mkdir(parents=True)
(OUT / "receipt.json").write_text(json.dumps(receipt, indent=1, default=float) + "\n")

print(json.dumps({"lane": "full_sim",
                  "file": str(Path(__file__).resolve()),
                  "all_pass": bool(all_pass),
                  "checks": receipt["checks"],
                  "findings": findings}, indent=2))
sys.exit(0 if all_pass else 1)
