#!/usr/bin/env python3
"""deep_integration lane: qit_referee — qutip as INDEPENDENT REFEREE of the
julia_manifold law runs + Choi CP audit of the stage64 operating pairs +
pennylane circuit-set representative of the two-sheet unitary stage.

UNOFFICIAL / working-sim bar, NOT proof-level. scratch_diagnostic.

Part 1 (qutip DEEP, independent referee):
  Re-solve the julia_manifold lane's three isolated generator families
  (unitary / depolarizing / amplitude damping) with qutip.mesolve on the
  SAME initial state and parameters as
  system_v8/engine_native/julia_manifold_tick.jl (law_runs():
  OMEGA=1.3, ALPHA=0.7, J_XY=0.35, TICK_DT=0.4, N_TICKS=30, gam=0.5,
  rho0_L Bloch (0.5, 0.3, -0.4), right sheet = -H_L with conj'd jumps).
  Gates: relative-entropy series match the julia receipt values to 1e-6
  (read from results/julia_manifold/receipt.json), analytic laws hold
  (unitary dS=0, Spohn monotone for the unital family, damping monotone
  to the unique fixed point). qutip.entropy_vn and qutip.ptrace are
  LOAD-BEARING: entropy_vn supplies the Tr rho log rho term of every
  relative-entropy value that is compared against julia, and ptrace
  decides the subadditivity/Araki-Lieb check on the damping trajectory.

  Choi audit: for each of the 16 stage64 operating pairs (read from
  results/stage64/receipt.json), build the GKSL propagator
  exp(dt*(D_a + H_b)) with the stage's terrain parameters (table mirrored
  from stage64_constraint_tournament.py), convert with qutip.to_choi,
  check complete positivity (all Choi eigenvalues >= -1e-12) for all 16.
  Control able to fail: the same construction with gamma -> -gamma must
  FAIL the CP check (min Choi eigenvalue < -1e-6).

Part 2 (pennylane, circuit set representative):
  The two Weyl sheets' unitary stage U = exp(-i H_joint dt) (H_joint =
  H_L (x) I - I (x) H_L + J_XY(XX+YY), dt=0.4) expressed as a 2-qubit
  circuit in {RY, RZ, CNOT} (+ trivial GlobalPhase bookkeeping): KAK
  decomposition via pennylane two_qubit_decomposition, every 1-qubit
  block expanded to ZYZ. Gates: circuit unitary matches scipy expm to
  1e-10 (phase-aligned), circuit output state on a representative pure
  state matches the matrix evolution to 1e-10, and the parameter-shift
  gradient of <Z0> of a small variational wrapper matches the autograd
  finite-difference gradient (circuit lane live, gradient nontrivial).

Receipt: results/qit_referee/receipt.json (checks bool, all_pass,
promotion_allowed=false, claim_ceiling). Refuses to reuse the outdir.
Light-lib process only (qutip + pennylane); no torch/jax/julia loaded.
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import expm

import qutip as qt
import pennylane as qml
from pennylane.ops import one_qubit_decomposition
from pennylane.ops.op_math.decompositions import two_qubit_decomposition

HERE = Path(__file__).resolve().parent
V8 = HERE.parent
OUT = HERE / "results" / "qit_referee"
JULIA_RECEIPT = V8 / "engine_native" / "results" / "julia_manifold" / "receipt.json"
STAGE64_RECEIPT = V8 / "nested_manifold" / "results" / "stage64" / "receipt.json"

# ---- parameters mirrored from julia_manifold_tick.jl (law_runs) -----------
N_TICKS = 30
TICK_DT = 0.4
OMEGA = 1.3
ALPHA = 0.7
J_XY = 0.35
GAM_LAW = 0.5

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
SM = np.array([[0, 1], [0, 0]], dtype=complex)

# ---- terrain table + candidate algebra mirrored from stage64 --------------
TERRAINS = {  # family -> (omega, gamma, declared frame sign)
    "family_0": (1.0, 0.20, +1),
    "family_1": (0.7, 0.35, -1),
    "family_2": (1.3, 0.15, +1),
    "family_3": (0.9, 0.50, -1),
}
W_HAD = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
JUMP = {"z": SM, "x": W_HAD @ SM @ W_HAD}
SIG = {"z": SZ, "x": SX}

LN2 = np.log(2.0)


def q2(m):
    return qt.Qobj(np.asarray(m, dtype=complex))


def clip_state(rho):
    """Hermitize, clip negative eigenvalues, renormalize (julia clip_op)."""
    R = rho.full()
    R = 0.5 * (R + R.conj().T)
    w, V = np.linalg.eigh(R)
    w = np.clip(w, 0.0, None)
    R2 = (V * w) @ V.conj().T
    return qt.Qobj(R2 / np.trace(R2).real, dims=rho.dims)


def ent_bits(rho):
    """von Neumann entropy in bits — qutip.entropy_vn LOAD-BEARING."""
    return float(qt.entropy_vn(clip_state(rho), base=2))


def relent_bits(rho, sig):
    """D(rho||sig) bits = -S(rho) - Tr(rho log2 sig); S from qutip.entropy_vn."""
    rho_c = clip_state(rho)
    s_bits = float(qt.entropy_vn(rho_c, base=2))
    ws, Vs = np.linalg.eigh(0.5 * (sig.full() + sig.full().conj().T))
    log_sig = (Vs * np.log(np.clip(ws, 1e-300, None))) @ Vs.conj().T
    cross = float(np.trace(rho_c.full() @ log_sig).real) / LN2
    return -s_bits - cross


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output dir: {OUT}")
    OUT.mkdir(parents=True)

    checks, data, findings = {}, {}, []

    jrec = json.loads(JULIA_RECEIPT.read_text())
    law = jrec["data"]["law_runs"]
    srec = json.loads(STAGE64_RECEIPT.read_text())
    op_pairs = srec["data"]["operating_pairs"]

    # ---- joint 2-sheet objects (julia conventions, L = subsystem 0) -------
    nx, nz = np.sin(ALPHA), np.cos(ALPHA)
    H_L = 0.5 * OMEGA * (nx * SX + nz * SZ)
    H = (qt.tensor(q2(H_L), q2(I2)) + qt.tensor(q2(I2), q2(-H_L))
         + J_XY * (qt.tensor(q2(SX), q2(SX)) + qt.tensor(q2(SY), q2(SY))))
    rho0_L = 0.5 * (I2 + 0.5 * SX + 0.3 * SY - 0.4 * SZ)
    rho0 = qt.tensor(q2(rho0_L), q2(np.conj(rho0_L)))

    def c_ops_depol(g):
        out = []
        for s in (SX, SY, SZ):
            out.append(np.sqrt(g / 4) * qt.tensor(q2(s), q2(I2)))
            out.append(np.sqrt(g / 4) * qt.tensor(q2(I2), q2(np.conj(s))))
        return out

    def c_ops_damp(g):
        return [np.sqrt(g) * qt.tensor(q2(SM), q2(I2)),
                np.sqrt(g) * qt.tensor(q2(I2), q2(np.conj(SM)))]

    tlist = np.arange(N_TICKS + 1) * TICK_DT
    opts = {"atol": 1e-12, "rtol": 1e-10, "nsteps": 200000,
            "store_states": True}

    # ---- family U: unitary, dS = 0 exact ---------------------------------
    resU = qt.mesolve(H, rho0, tlist, c_ops=[], options=opts)
    S_U = [ent_bits(r) for r in resU.states]
    u_drift = float(max(abs(s - S_U[0]) for s in S_U[1:]))
    checks["qutip_lawU_unitary_dS_zero_lt_1e-8"] = u_drift < 1e-8
    data["U_max_dS_qutip"] = u_drift
    data["U_max_dS_julia"] = law["U_max_dS"]

    # ---- family D: depolarizing (unital), Spohn to I/4 -------------------
    mix = qt.tensor(q2(I2 / 2), q2(I2 / 2))
    resD = qt.mesolve(H, rho0, tlist, c_ops=c_ops_depol(GAM_LAW),
                      options=opts)
    D_qt = [relent_bits(r, mix) for r in resD.states]
    D_jl = np.asarray(law["D_relent_series"], dtype=float)
    d_diff = float(np.max(np.abs(np.asarray(D_qt) - D_jl)))
    checks["qutip_lawD_series_matches_julia_lt_1e-6"] = d_diff < 1e-6
    checks["qutip_lawD_spohn_relent_monotone_down"] = \
        float(np.max(np.diff(D_qt))) < 1e-9
    data["D_series_max_abs_diff_vs_julia"] = d_diff
    data["D_max_step_increase_qutip"] = float(np.max(np.diff(D_qt)))
    data["D_relent_series_qutip"] = D_qt

    # ---- family A: amplitude damping, monotone to unique fixed point -----
    cA = c_ops_damp(GAM_LAW)
    Lfull = qt.liouvillian(H, cA)
    evL = np.linalg.eigvals(Lfull.full())
    null_dim = int(np.sum(np.abs(evL) < 1e-8))
    checks["qutip_lawA_fixed_point_unique"] = null_dim == 1
    rho_ss = qt.steadystate(H, cA)
    ss_min_eig = float(np.min(np.linalg.eigvalsh(rho_ss.full())))
    checks["qutip_lawA_rho_ss_min_eig_matches_julia_lt_1e-6"] = \
        abs(ss_min_eig - law["A_rho_ss_min_eig"]) < 1e-6
    resA = qt.mesolve(H, rho0, tlist, c_ops=cA, options=opts)
    A_qt = [relent_bits(r, rho_ss) for r in resA.states]
    A_jl = np.asarray(law["A_relent_series"], dtype=float)
    a_diff = float(np.max(np.abs(np.asarray(A_qt) - A_jl)))
    checks["qutip_lawA_series_matches_julia_lt_1e-6"] = a_diff < 1e-6
    checks["qutip_lawA_damping_relent_monotone_down"] = \
        float(np.max(np.diff(A_qt))) < 1e-9
    data["A_nullspace_dim_qutip"] = null_dim
    data["A_rho_ss_min_eig_qutip"] = ss_min_eig
    data["A_series_max_abs_diff_vs_julia"] = a_diff
    data["A_max_step_increase_qutip"] = float(np.max(np.diff(A_qt)))
    data["A_relent_series_qutip"] = A_qt

    # ---- qutip.ptrace load-bearing: cut laws on the damping trajectory ---
    sub_min, al_margin_min = np.inf, np.inf
    for r in resA.states:
        S_L = ent_bits(r.ptrace(0))   # qutip.ptrace decides this check
        S_R = ent_bits(r.ptrace(1))
        S_LR = ent_bits(r)
        sub_min = min(sub_min, S_L + S_R - S_LR)          # subadditivity
        al_margin_min = min(al_margin_min, S_LR - abs(S_L - S_R))
    checks["qutip_ptrace_subadditivity_all_ticks"] = sub_min > -1e-9
    checks["qutip_ptrace_araki_lieb_all_ticks"] = al_margin_min > -1e-9
    data["mutual_info_min_over_ticks"] = float(sub_min)
    data["araki_lieb_margin_min_over_ticks"] = float(al_margin_min)

    # ---- Choi CP audit of the 16 stage64 operating pairs -----------------
    def stage_propagator(sid, label, gamma_sign=+1.0):
        fam, sheet, fld = sid.split("|")
        omega, gamma, _ = TERRAINS[fam]
        s = +1 if sheet == "L" else -1
        f = +1 if fld == "f+1" else -1
        a, b = label[2], label[6]              # "D_a|H_b"
        H1 = q2(s * f * omega * SIG[b])
        jump = np.sqrt(gamma) * JUMP[a]
        L1 = qt.liouvillian(H1, [q2(np.sqrt(gamma_sign + 0j) * jump)]) \
            if gamma_sign > 0 else \
            (qt.liouvillian(H1, []) - qt.lindblad_dissipator(q2(jump)))
        return (TICK_DT * L1).expm()

    choi_min = {}
    for sid, label in op_pairs.items():
        prop = stage_propagator(sid, label)
        ch = qt.to_choi(prop)                  # qutip.to_choi LOAD-BEARING
        choi_min[sid] = float(np.min(np.linalg.eigvalsh(ch.full())))
    checks["qutip_choi_cp_all_16_stage64_pairs"] = \
        len(choi_min) == 16 and all(v >= -1e-12 for v in choi_min.values())
    data["choi_min_eig_per_stage"] = choi_min

    sid0 = next(iter(op_pairs))
    prop_bad = stage_propagator(sid0, op_pairs[sid0], gamma_sign=-1.0)
    bad_min = float(np.min(np.linalg.eigvalsh(qt.to_choi(prop_bad).full())))
    checks["qutip_choi_negative_gamma_control_fails_cp"] = bad_min < -1e-6
    data["choi_control_negative_gamma_min_eig"] = bad_min

    # ---- pennylane: two-sheet unitary stage as RY/RZ + CNOT circuit ------
    U_target = expm(-1j * H.full() * TICK_DT)
    raw_ops = two_qubit_decomposition(U_target, wires=[0, 1])
    weyl_ops = []
    for op in raw_ops:
        if op.name in ("CNOT", "RY", "RZ", "GlobalPhase"):
            weyl_ops.append(op)
        elif op.name == "QubitUnitary":
            weyl_ops += one_qubit_decomposition(
                op.matrix(), op.wires[0], "ZYZ", return_global_phase=True)
        elif op.name == "Rot":
            a, bb, c = op.parameters
            w = op.wires[0]
            weyl_ops += [qml.RZ(a, w), qml.RY(bb, w), qml.RZ(c, w)]
        else:
            raise SystemExit(f"unexpected op in decomposition: {op.name}")
    gate_names = sorted({op.name for op in weyl_ops})
    checks["pl_gateset_ry_rz_cnot_only"] = \
        set(gate_names) <= {"RY", "RZ", "CNOT", "GlobalPhase"}
    data["pl_gate_names"] = gate_names
    data["pl_gate_count"] = len(weyl_ops)
    data["pl_cnot_count"] = sum(1 for op in weyl_ops if op.name == "CNOT")

    U_circ = qml.matrix(qml.tape.QuantumScript(weyl_ops), wire_order=[0, 1])
    ph = np.vdot(U_circ.flatten(), U_target.flatten())
    ph = ph / abs(ph)
    u_diff = float(np.max(np.abs(U_circ * ph - U_target)))
    checks["pl_circuit_unitary_matches_expm_lt_1e-10"] = u_diff < 1e-10
    data["pl_unitary_max_abs_diff"] = u_diff

    # representative pure state: dominant eigenvector of the julia rho0
    w0, V0 = np.linalg.eigh(rho0.full())
    psi0 = V0[:, -1] / np.linalg.norm(V0[:, -1])
    dev = qml.device("default.qubit", wires=2)

    @qml.qnode(dev)
    def state_circ():
        qml.StatePrep(psi0, wires=[0, 1])
        for op in weyl_ops:
            qml.apply(op)
        return qml.state()

    psi_circ = np.asarray(state_circ())
    psi_ref = U_target @ psi0
    ph2 = np.vdot(psi_circ, psi_ref)
    ph2 = ph2 / abs(ph2)
    s_diff = float(np.max(np.abs(psi_circ * ph2 - psi_ref)))
    checks["pl_circuit_state_matches_matrix_evolution_lt_1e-10"] = \
        s_diff < 1e-10
    data["pl_state_max_abs_diff"] = s_diff

    # parameter-shift gradient of <Z0> vs autograd finite difference
    from pennylane import numpy as pnp

    def var_circ(theta):
        qml.RY(theta[0], wires=0)
        qml.RZ(theta[1], wires=1)
        for op in weyl_ops:
            qml.apply(op)
        return qml.expval(qml.PauliZ(0))

    qn_ps = qml.QNode(var_circ, dev, diff_method="parameter-shift")
    qn_fd = qml.QNode(var_circ, dev, diff_method="finite-diff")
    theta = pnp.array([0.37, -0.61], requires_grad=True)
    g_ps = np.asarray(qml.grad(qn_ps)(theta), dtype=float)
    g_fd = np.asarray(qml.grad(qn_fd)(theta), dtype=float)
    g_diff = float(np.max(np.abs(g_ps - g_fd)))
    checks["pl_paramshift_grad_matches_finite_diff_lt_1e-5"] = g_diff < 1e-5
    checks["pl_grad_nontrivial"] = float(np.max(np.abs(g_ps))) > 1e-4
    data["pl_grad_parameter_shift"] = [float(x) for x in g_ps]
    data["pl_grad_finite_diff"] = [float(x) for x in g_fd]
    data["pl_grad_max_abs_diff"] = g_diff

    all_pass = bool(all(checks.values()))

    findings += [
        ("qutip is an INDEPENDENT referee of the julia_manifold law runs: "
         "same H/rho0/gamma, different integrator (qutip.mesolve, atol "
         "1e-12 / rtol 1e-10, one sweep) vs julia timeevolution.master "
         "tick-restarted; relative-entropy series agree to "
         f"D={d_diff:.3e}, A={a_diff:.3e} (gate 1e-6), unitary drift "
         f"{u_drift:.3e} vs julia {law['U_max_dS']:.3e} (both < 1e-8)."),
        ("qutip.entropy_vn is load-bearing: it supplies the Tr rho log rho "
         "term of every compared relative-entropy value; qutip.ptrace is "
         "load-bearing: it decides the subadditivity + Araki-Lieb checks "
         f"on the damping trajectory (min I = {sub_min:.3e}, min AL margin "
         f"= {al_margin_min:.3e})."),
        ("amplitude-damping fixed point re-derived independently via "
         f"qutip.steadystate: min eig {ss_min_eig:.6f} vs julia "
         f"{law['A_rho_ss_min_eig']:.6f}; Liouvillian null space dim "
         f"{null_dim} (julia: {law['A_nullspace_dim']})."),
        ("Choi CP audit: all 16 stage64 operating-pair propagators "
         "exp(0.4*(D_a+H_b)) are completely positive via qutip.to_choi "
         f"(min Choi eigenvalue over 16 stages = "
         f"{min(choi_min.values()):.3e} >= -1e-12); the gamma -> -gamma "
         f"control FAILS CP (min eig {bad_min:.3e}) — the check can fail."),
        ("pennylane circuit lane live: the two-sheet unitary stage "
         "exp(-i H_joint 0.4) compiled to "
         f"{data['pl_cnot_count']} CNOTs + RY/RZ (KAK); circuit unitary "
         f"vs scipy expm max diff {u_diff:.3e}, output state vs matrix "
         f"evolution {s_diff:.3e} (both gates 1e-10, phase-aligned); "
         f"parameter-shift vs finite-diff gradient of <Z0> max diff "
         f"{g_diff:.3e}."),
        ("scope: referee re-solves the ISOLATED law runs, not the full "
         "driven tick loop (drive/nesting/flux live in the julia lane); "
         "UNOFFICIAL working-sim bar, no proof-level claim."),
    ]

    receipt = {
        "schema": "ratchet.v8.deep-integration.qit-referee.v0",
        "lane": "qit_referee",
        "inputs": {
            "julia_receipt": str(JULIA_RECEIPT),
            "stage64_receipt": str(STAGE64_RECEIPT),
        },
        "packages": {
            "qutip": ("load_bearing: mesolve re-solve of all three law "
                      "families; entropy_vn in every compared relent value; "
                      "ptrace decides the cut-law checks; to_choi decides "
                      "the CP audit"),
            "pennylane": ("load_bearing: KAK compilation of the unitary "
                          "stage to RY/RZ+CNOT; parameter-shift gradient "
                          "lane"),
        },
        "checks": {k: bool(v) for k, v in checks.items()},
        "all_pass": all_pass,
        "data": data,
        "findings": findings,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": ("independent-referee agreement on isolated law "
                          "runs + CP audit + circuit-set representative; "
                          "UNOFFICIAL working-sim bar, scratch_diagnostic; "
                          "no physics claim beyond the executed checks"),
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"lane": "qit_referee",
                      "file": str(Path(__file__).resolve()),
                      "all_pass": all_pass,
                      "checks": {k: bool(v) for k, v in checks.items()},
                      "findings": findings}, indent=2))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
