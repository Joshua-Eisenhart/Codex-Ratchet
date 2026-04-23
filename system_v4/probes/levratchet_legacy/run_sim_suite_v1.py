#!/usr/bin/env python3
# run_sim_suite_v1.py
# Produces:
#   sim_evidence_pack.txt  (multiple SIM_EVIDENCE v1 blocks)
#   results_<SIM_ID>.json  (one per SIM_ID)

from __future__ import annotations
import json, hashlib, os, math
import numpy as np

# -------------------------
# hashing helpers
# -------------------------
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def dump_json(path: str, obj: dict) -> str:
    raw = json.dumps(obj, indent=2, sort_keys=True).encode("utf-8")
    with open(path, "wb") as f:
        f.write(raw)
    return sha256_bytes(raw)

# -------------------------
# basic QIT objects
# -------------------------
I2 = np.eye(2, dtype=complex)
X  = np.array([[0,1],[1,0]], dtype=complex)
Y  = np.array([[0,-1j],[1j,0]], dtype=complex)
Z  = np.array([[1,0],[0,-1]], dtype=complex)

CNOT = np.array([
    [1,0,0,0],
    [0,1,0,0],
    [0,0,0,1],
    [0,0,1,0],
], dtype=complex)

def normalize_rho(rho: np.ndarray) -> np.ndarray:
    tr = np.trace(rho)
    if abs(tr) < 1e-18:
        return rho
    return rho / tr

def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh((rho + rho.conj().T)/2).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w*np.log(w)).sum())

def trace_norm(a: np.ndarray) -> float:
    s = np.linalg.svd(a, compute_uv=False)
    return float(np.real(s).sum())

def fro_norm(a: np.ndarray) -> float:
    return float(np.real(np.sqrt(np.trace(a.conj().T @ a))))

def random_density_2(rng: np.random.Generator) -> np.ndarray:
    g = rng.normal(size=(2,2)) + 1j*rng.normal(size=(2,2))
    rho = g @ g.conj().T
    return normalize_rho(rho)

def random_density_4(rng: np.random.Generator) -> np.ndarray:
    g = rng.normal(size=(4,4)) + 1j*rng.normal(size=(4,4))
    rho = g @ g.conj().T
    return normalize_rho(rho)

def bell_seed(rng: np.random.Generator) -> np.ndarray:
    # |Phi+>
    v = np.array([1,0,0,1], dtype=complex)/np.sqrt(2)
    rho = np.outer(v, v.conj())
    # random local twirl to avoid basis-lock
    a = rng.uniform(0, 2*np.pi)
    b = rng.uniform(0, 2*np.pi)
    UA = su2_axis_angle(np.array([0,0,1.0]), a, +1)
    UB = su2_axis_angle(np.array([1.0,0,0]), b, +1)
    rho = apply_unitary_A(rho, UA)
    rho = apply_unitary_B(rho, UB)
    return normalize_rho(rho)

def partial_trace_A(rhoAB: np.ndarray) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for a in range(2):
        for ap in range(2):
            s = 0+0j
            for b in range(2):
                s += rhoAB[2*a+b, 2*ap+b]
            out[a,ap] = s
    return normalize_rho(out)

def partial_trace_B(rhoAB: np.ndarray) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for b in range(2):
        for bp in range(2):
            s = 0+0j
            for a in range(2):
                s += rhoAB[2*a+b, 2*a+bp]
            out[b,bp] = s
    return normalize_rho(out)

def mi_and_sAgB(rhoAB: np.ndarray) -> tuple[float,float]:
    rhoA = partial_trace_A(rhoAB)
    rhoB = partial_trace_B(rhoAB)
    sab = vn_entropy(rhoAB)
    sa  = vn_entropy(rhoA)
    sb  = vn_entropy(rhoB)
    mi  = sa + sb - sab
    sAgB = sab - sb
    return float(mi), float(sAgB)

# -------------------------
# SU(2) unitary from axis-angle (no expm)
# U = cos(theta) I - i sin(theta) (sign * n·sigma)
# -------------------------
def su2_axis_angle(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = np.array(n, float)
    n = n / np.linalg.norm(n)
    H = n[0]*X + n[1]*Y + n[2]*Z
    c = math.cos(theta)
    s = math.sin(theta)
    return (c*I2 - 1j*s*sign*H).astype(complex)

def apply_unitary(rho: np.ndarray, U: np.ndarray) -> np.ndarray:
    return normalize_rho(U @ rho @ U.conj().T)

def apply_unitary_A(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UA = np.kron(U, I2)
    return normalize_rho(UA @ rhoAB @ UA.conj().T)

def apply_unitary_B(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UB = np.kron(I2, U)
    return normalize_rho(UB @ rhoAB @ UB.conj().T)

def apply_unitary_AB(rhoAB: np.ndarray, UAB: np.ndarray) -> np.ndarray:
    return normalize_rho(UAB @ rhoAB @ UAB.conj().T)

# -------------------------
# CPTP terrain channels (qubit, act on A for AB tests)
# -------------------------
def terrain_Se(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def terrain_Ne(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-p) * I2
    K1 = np.sqrt(p) * X
    return [K0, K1]

def terrain_Ni(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-q) * I2
    K1 = np.sqrt(q) * Z
    return [K0, K1]

def terrain_Si() -> list[np.ndarray]:
    return [I2]

TERRAIN = {
    "Se": lambda prm: terrain_Se(prm["gamma"]),
    "Ne": lambda prm: terrain_Ne(prm["p"]),
    "Ni": lambda prm: terrain_Ni(prm["q"]),
    "Si": lambda prm: terrain_Si(),
}

def apply_kraus_A(rhoAB: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4,4), dtype=complex)
    for K in Ks:
        KA = np.kron(K, I2)
        out += KA @ rhoAB @ KA.conj().T
    return normalize_rho(out)

def apply_kraus(rho: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    return normalize_rho(out)

# -------------------------
# SIM helpers
# -------------------------
def emit_block(sim_id: str, code_hash: str, out_hash: str, metrics: dict, evidence_token: str) -> str:
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append(f"SIM_ID: {sim_id}")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for k,v in metrics.items():
        lines.append(f"METRIC: {k}={v}")
    lines.append(f"EVIDENCE_SIGNAL {sim_id} CORR {evidence_token}")
    lines.append("END SIM_EVIDENCE v1")
    return "\n".join(lines)

# -------------------------
# SIM 1: Axis-3 Hopf flux grid (numerical integral of curvature)
# -------------------------
def sim_axis3_hopf_grid() -> tuple[dict, dict]:
    # curvature integral for spin-1/2: F = ±(1/2) sin θ dθ dφ
    # numeric integration on (θ,φ) grid
    n_theta = 400
    n_phi   = 400
    thetas = np.linspace(0, np.pi, n_theta)
    phis   = np.linspace(0, 2*np.pi, n_phi, endpoint=False)
    dtheta = thetas[1]-thetas[0]
    dphi   = phis[1]-phis[0]

    # integrate for + and -
    sin_t = np.sin(thetas)
    area_weights = (sin_t[:,None] * dtheta * dphi) * np.ones((n_theta, n_phi))
    flux_plus  = float((0.5 * area_weights).sum())
    flux_minus = float((-0.5 * area_weights).sum())

    out = {
        "berry_flux_plus_approx": flux_plus,
        "berry_flux_minus_approx": flux_minus,
        "chirality_plus": 1,
        "chirality_minus": -1,
        "grid_theta": n_theta,
        "grid_phi": n_phi,
    }
    metrics = {
        "berry_flux_plus_approx": flux_plus,
        "berry_flux_minus_approx": flux_minus,
        "chirality_plus": 1,
        "chirality_minus": -1,
    }
    return out, metrics

# -------------------------
# SIM 2: Axis-6 left/right multi-operator suite
# -------------------------
def sim_axis6_lr_multi(seed=0, trials=512) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    deltas = []
    comms  = []
    # fixed set of operators (noncommuting)
    ops = [X, Y, Z, (X+Z)/np.sqrt(2)]
    for _ in range(trials):
        rho = random_density_2(rng)
        A = ops[rng.integers(0, len(ops))]
        L = A @ rho
        R = rho @ A
        deltas.append(trace_norm(L-R))
        comms.append(fro_norm(A@rho - rho@A))
    out = {
        "seed": seed,
        "trials": trials,
        "delta_trace_mean": float(np.mean(deltas)),
        "delta_trace_min": float(np.min(deltas)),
        "delta_trace_max": float(np.max(deltas)),
        "comm_norm_mean": float(np.mean(comms)),
        "comm_norm_min": float(np.min(comms)),
        "comm_norm_max": float(np.max(comms)),
    }
    metrics = {k: out[k] for k in out if k not in ("seed","trials")}
    return out, metrics

# -------------------------
# SIM 3/4: Axis-5 FGA / FSA sweeps
# FGA: apply small noise (entropy-changing)
# FSA: apply unitary only (entropy ~ invariant)
# -------------------------
def sim_axis5_sweep(kind: str, seed=0, trials=512, theta=0.23, n_vec=(0.3,0.4,0.866025403784), gamma=0.08) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    U = su2_axis_angle(np.array(n_vec), theta, +1)
    dS = []
    for _ in range(trials):
        rho0 = random_density_2(rng)
        S0 = vn_entropy(rho0)
        if kind == "FSA":
            rho1 = apply_unitary(rho0, U)
        else:
            # FGA representative: unitary + amplitude damping
            rho1 = apply_unitary(rho0, U)
            rho1 = apply_kraus(rho1, terrain_Se(gamma))
        dS.append(vn_entropy(rho1) - S0)
    out = {
        "kind": kind,
        "seed": seed,
        "trials": trials,
        "theta": theta,
        "n_vec": list(n_vec),
        "gamma": gamma,
        "dS_mean": float(np.mean(dS)),
        "dS_min": float(np.min(dS)),
        "dS_max": float(np.max(dS)),
    }
    metrics = {k: out[k] for k in out if k not in ("kind","seed","trials","theta","n_vec","gamma")}
    return out, metrics

# -------------------------
# SIM 5: Axis-4 sequences, forward+reverse, Type-1 (+) and Type-2 (-)
# Uses same terrain params, axis3 sign sets unitary sign.
# -------------------------
SEQ = {
    "SEQ01": ["Se","Ne","Ni","Si"],
    "SEQ02": ["Se","Si","Ni","Ne"],
    "SEQ03": ["Se","Ne","Si","Ni"],
    "SEQ04": ["Se","Si","Ne","Ni"],
}

def run_seq_qubit(seq: list[str], sign: int, seed=0, states=256, cycles=64,
                  theta=0.07, n_vec=(0.3,0.4,0.866025403784),
                  prm={"gamma":0.12,"p":0.08,"q":0.10}) -> dict:
    rng = np.random.default_rng(seed)
    U = su2_axis_angle(np.array(n_vec), theta, sign)
    ent_list = []
    pur_list = []
    for _ in range(states):
        rho = random_density_2(rng)
        for _c in range(cycles):
            for tname in seq:
                Ks = TERRAIN[tname](prm)
                # order here: unitary then terrain (one consistent convention)
                rho = apply_unitary(rho, U)
                rho = apply_kraus(rho, Ks)
        ent_list.append(vn_entropy(rho))
        pur_list.append(purity(rho))
    return {
        "vn_entropy_mean": float(np.mean(ent_list)),
        "vn_entropy_min": float(np.min(ent_list)),
        "vn_entropy_max": float(np.max(ent_list)),
        "purity_mean": float(np.mean(pur_list)),
        "purity_min": float(np.min(pur_list)),
        "purity_max": float(np.max(pur_list)),
    }

def sim_axis4_all_bidir() -> tuple[dict, dict]:
    out = {
        "params": {"seed":0,"states":256,"cycles":64,"theta":0.07,"n_vec":[0.3,0.4,0.866025403784],"gamma":0.12,"p":0.08,"q":0.10}
    }
    metrics = {}
    for name, seq in SEQ.items():
        rev = list(reversed(seq))
        r_t1_f = run_seq_qubit(seq, +1)
        r_t1_r = run_seq_qubit(rev, +1)
        r_t2_f = run_seq_qubit(seq, -1)
        r_t2_r = run_seq_qubit(rev, -1)
        out[name] = {"fwd": seq, "rev": rev, "T1_fwd": r_t1_f, "T1_rev": r_t1_r, "T2_fwd": r_t2_f, "T2_rev": r_t2_r}
        metrics[f"{name}_T1_fwd_entropy_mean"] = r_t1_f["vn_entropy_mean"]
        metrics[f"{name}_T1_rev_entropy_mean"] = r_t1_r["vn_entropy_mean"]
        metrics[f"{name}_T2_fwd_entropy_mean"] = r_t2_f["vn_entropy_mean"]
        metrics[f"{name}_T2_rev_entropy_mean"] = r_t2_r["vn_entropy_mean"]
    return out, metrics

# -------------------------
# SIM 6: Axis-12 sequence constraints (simple edge counts)
# -------------------------
def sim_axis12_seq_constraints() -> tuple[dict, dict]:
    # counts of SENI edges (Se-Ni adjacency) and NESI edges (Ne-Si adjacency) in each sequence
    def count_edges(seq: list[str], a: str, b: str) -> int:
        c = 0
        for i in range(len(seq)-1):
            if seq[i]==a and seq[i+1]==b:
                c += 1
        return c
    out = {}
    metrics = {}
    for name, seq in SEQ.items():
        seni = count_edges(seq, "Se","Ni") + count_edges(seq, "Ni","Se")
        nesi = count_edges(seq, "Ne","Si") + count_edges(seq, "Si","Ne")
        out[name] = {"seq": seq, "seni_edges": seni, "nesi_edges": nesi}
        metrics[f"{name}_seni_edges"] = seni
        metrics[f"{name}_nesi_edges"] = nesi
    return out, metrics

# -------------------------
# SIM 7: Axis-12 channel realization sweep (terrain parameter sweep)
# -------------------------
def sim_axis12_channel_realization(seed=0, trials=256) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    thetas = [0.03, 0.07, 0.12]
    gammas = [0.02, 0.08, 0.14]
    ps     = [0.02, 0.08, 0.14]
    qs     = [0.02, 0.08, 0.14]
    n_vec = (0.3,0.4,0.866025403784)

    out = {"seed": seed, "trials": trials, "grid": {"theta": thetas, "gamma": gammas, "p": ps, "q": qs}, "rows": []}
    # record mean entropy after 1 cycle of canonical order
    seq = SEQ["SEQ01"]
    for theta in thetas:
        for gamma in gammas:
            for p in ps:
                for q in qs:
                    U = su2_axis_angle(np.array(n_vec), theta, +1)
                    prm={"gamma":gamma,"p":p,"q":q}
                    ents=[]
                    for _ in range(trials):
                        rho = random_density_2(rng)
                        for tname in seq:
                            rho = apply_unitary(rho, U)
                            rho = apply_kraus(rho, TERRAIN[tname](prm))
                        ents.append(vn_entropy(rho))
                    out["rows"].append({"theta":theta,"gamma":gamma,"p":p,"q":q,"entropy_mean":float(np.mean(ents))})
    # metrics: just a few summaries
    em = [r["entropy_mean"] for r in out["rows"]]
    metrics = {
        "entropy_mean_min": float(np.min(em)),
        "entropy_mean_max": float(np.max(em)),
        "entropy_mean_mean": float(np.mean(em)),
        "rows": len(out["rows"]),
    }
    return out, metrics

# -------------------------
# SIM 8: Stage16 substage4 uniform axis6 (simple 2-engine / 2-loop / 4-stage dS,dP)
# -------------------------
def sim_stage16_sub4_axis6_uniform(seed=0, trials=256) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    n_vec=(0.3,0.4,0.866025403784)
    theta=0.07
    # operator family (substage_4): Ti, Te, Fi, Fe as simple representatives on qubit
    def op_Ti(rho):  # dephase in Z
        return apply_kraus(rho, [np.sqrt(0.5)*(I2+Z)/2*2, np.sqrt(0.5)*(I2-Z)/2*2])  # stable pinching-ish
    def op_Te(rho, sign):  # unitary rotation
        U = su2_axis_angle(np.array(n_vec), theta, sign)
        return apply_unitary(rho, U)
    def op_Fi(rho):  # dephase in X
        K0 = np.sqrt(1-0.2)*I2
        K1 = np.sqrt(0.2)*X
        return apply_kraus(rho, [K0, K1])
    def op_Fe(rho):  # amplitude damping light
        return apply_kraus(rho, terrain_Se(0.08))

    stage_order = ["Se","Ne","Ni","Si"]
    # axis6 pattern from your corrected table (outer)
    # Outer: Se UP, Ne DOWN, Ni DOWN, Si UP
    outer_axis6 = {"Se":"UP","Ne":"DOWN","Ni":"DOWN","Si":"UP"}
    # Inner: Se DOWN, Ne UP, Ni UP, Si DOWN
    inner_axis6 = {"Se":"DOWN","Ne":"UP","Ni":"UP","Si":"DOWN"}

    prm={"gamma":0.12,"p":0.08,"q":0.10}

    def stage_apply(rho, terr, sign, axis6_tag):
        U = su2_axis_angle(np.array(n_vec), theta, sign)
        # terrain map
        Phi = lambda r: apply_kraus(r, TERRAIN[terr](prm))
        # substage_4 operators all share same axis6 tag
        ops = []
        ops.append(lambda r: op_Ti(r))
        ops.append(lambda r: op_Te(r, sign))
        ops.append(lambda r: op_Fi(r))
        ops.append(lambda r: op_Fe(r))
        r = rho
        for op in ops:
            if axis6_tag == "UP":
                r = Phi(op(r))
            else:
                r = op(Phi(r))
        # also apply Weyl unitary transport once per stage (matches earlier harness style)
        r = apply_unitary(r, U)
        return r

    def run_one(sign: int, loop_axis6: dict) -> dict:
        dS={}
        dP={}
        for idx, terr in enumerate(stage_order, start=1):
            ds=[]
            dp=[]
            for _ in range(trials):
                rho0 = random_density_2(rng)
                S0 = vn_entropy(rho0); P0 = purity(rho0)
                rho1 = stage_apply(rho0, terr, sign, loop_axis6[terr])
                ds.append(vn_entropy(rho1)-S0)
                dp.append(purity(rho1)-P0)
            dS[f"{idx}_{terr}_{loop_axis6[terr]}_dS"]=float(np.mean(ds))
            dP[f"{idx}_{terr}_{loop_axis6[terr]}_dP"]=float(np.mean(dp))
        out = {}
        out.update(dS); out.update(dP)
        return out

    T1_outer = run_one(+1, outer_axis6)
    T1_inner = run_one(+1, inner_axis6)
    T2_outer = run_one(-1, outer_axis6)
    T2_inner = run_one(-1, inner_axis6)

    out = {"seed":seed,"trials":trials,"order":stage_order,"T1_outer":T1_outer,"T1_inner":T1_inner,"T2_outer":T2_outer,"T2_inner":T2_inner}
    metrics = {}
    # export a few key means to keep block compact
    for k,v in T1_outer.items(): metrics[f"T1_outer_{k}"]=v
    for k,v in T1_inner.items(): metrics[f"T1_inner_{k}"]=v
    for k,v in T2_outer.items(): metrics[f"T2_outer_{k}"]=v
    for k,v in T2_inner.items(): metrics[f"T2_inner_{k}"]=v
    return out, metrics

# -------------------------
# SIM 9: Negative control (Axis-6 commute)
# -------------------------
def sim_negctrl_axis6_commute(trials=256) -> tuple[dict, dict]:
    # choose rho diagonal, A diagonal => A rho == rho A
    rng = np.random.default_rng(0)
    deltas=[]
    comms=[]
    for _ in range(trials):
        a = rng.uniform(0.0, 1.0)
        rho = np.array([[a,0],[0,1-a]], dtype=complex)
        A = Z
        deltas.append(trace_norm(A@rho - rho@A))
        comms.append(fro_norm(A@rho - rho@A))
    out = {"trials":trials,"delta_trace_mean":float(np.mean(deltas)),"comm_norm_mean":float(np.mean(comms))}
    metrics = dict(out)
    return out, metrics

# -------------------------
# SIM 10: Axis-0 trajectory correlation suite (MI + S(A|B) along trajectory)
# -------------------------
def sim_axis0_traj_corr(seed=0, trials=256, cycles=16, entangle_reps=1) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    n_vec=(0.3,0.4,0.866025403784)
    theta=0.07
    prm={"gamma":0.02,"p":0.02,"q":0.02}
    U = su2_axis_angle(np.array(n_vec), theta, +1)

    seq = SEQ["SEQ01"]

    traj_min_sagb=[]
    traj_negfrac=[]
    traj_mean_mi=[]
    traj_mean_sagb=[]
    for _ in range(trials):
        rho = bell_seed(rng)
        mi_vals=[]
        sagb_vals=[]
        for _c in range(cycles):
            for terr in seq:
                rho = apply_unitary_A(rho, U)
                rho = apply_kraus_A(rho, TERRAIN[terr](prm))
                for _k in range(entangle_reps):
                    rho = apply_unitary_AB(rho, CNOT)
                mi, sagb = mi_and_sAgB(rho)
                mi_vals.append(mi)
                sagb_vals.append(sagb)
        mi_vals = np.array(mi_vals,float)
        sagb_vals = np.array(sagb_vals,float)
        traj_min_sagb.append(float(np.min(sagb_vals)))
        traj_mean_mi.append(float(np.mean(mi_vals)))
        traj_mean_sagb.append(float(np.mean(sagb_vals)))
        traj_negfrac.append(float(np.mean((sagb_vals < 0.0).astype(float))))

    out = {
        "seed": seed,
        "trials": trials,
        "cycles": cycles,
        "entangle_reps": entangle_reps,
        "sequence": seq,
        "terrain_params": prm,
        "theta": theta,
        "n_vec": list(n_vec),
        "MI_mean": float(np.mean(traj_mean_mi)),
        "SAgB_mean": float(np.mean(traj_mean_sagb)),
        "SAgB_min_mean": float(np.mean(traj_min_sagb)),
        "neg_SAgB_frac_mean": float(np.mean(traj_negfrac)),
        "neg_SAgB_frac_max": float(np.max(traj_negfrac)),
    }
    metrics = {k: out[k] for k in out if k not in ("seed","trials","cycles","entangle_reps","sequence","terrain_params","theta","n_vec")}
    return out, metrics

# -------------------------
# main
# -------------------------
def main():
    code_hash = sha256_file(os.path.abspath(__file__))
    blocks = []

    # SIM 1
    out, met = sim_axis3_hopf_grid()
    out_hash = dump_json("results_S_SIM_AXIS3_WEYL_HOPF_GRID_V1.json", out)
    blocks.append(emit_block("S_SIM_AXIS3_WEYL_HOPF_GRID_V1", code_hash, out_hash, met, "E_SIM_AXIS3_WEYL_HOPF_GRID_V1"))

    # SIM 2
    out, met = sim_axis6_lr_multi()
    out_hash = dump_json("results_S_SIM_AXIS6_LR_MULTI_V1.json", out)
    blocks.append(emit_block("S_SIM_AXIS6_LR_MULTI_V1", code_hash, out_hash, met, "E_SIM_AXIS6_LR_MULTI_V1"))

    # SIM 3
    out, met = sim_axis5_sweep("FGA")
    out_hash = dump_json("results_S_SIM_AXIS5_FGA_SWEEP_V1.json", out)
    blocks.append(emit_block("S_SIM_AXIS5_FGA_SWEEP_V1", code_hash, out_hash, met, "E_SIM_AXIS5_FGA_SWEEP_V1"))

    # SIM 4
    out, met = sim_axis5_sweep("FSA")
    out_hash = dump_json("results_S_SIM_AXIS5_FSA_SWEEP_V1.json", out)
    blocks.append(emit_block("S_SIM_AXIS5_FSA_SWEEP_V1", code_hash, out_hash, met, "E_SIM_AXIS5_FSA_SWEEP_V1"))

    # SIM 5
    out, met = sim_axis4_all_bidir()
    out_hash = dump_json("results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json", out)
    blocks.append(emit_block("S_SIM_AXIS4_SEQ_ALL_BIDIR_V1", code_hash, out_hash, met, "E_SIM_AXIS4_SEQ_ALL_BIDIR_V1"))

    # SIM 6
    out, met = sim_axis12_seq_constraints()
    out_hash = dump_json("results_S_SIM_AXIS12_SEQ_CONSTRAINTS_V2.json", out)
    blocks.append(emit_block("S_SIM_AXIS12_SEQ_CONSTRAINTS_V2", code_hash, out_hash, met, "E_SIM_AXIS12_SEQ_CONSTRAINTS_V2"))

    # SIM 7
    out, met = sim_axis12_channel_realization()
    out_hash = dump_json("results_S_SIM_AXIS12_CHANNEL_REALIZATION_V4.json", out)
    blocks.append(emit_block("S_SIM_AXIS12_CHANNEL_REALIZATION_V4", code_hash, out_hash, met, "E_SIM_AXIS12_CHANNEL_REALIZATION_V4"))

    # SIM 8
    out, met = sim_stage16_sub4_axis6_uniform()
    out_hash = dump_json("results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json", out)
    blocks.append(emit_block("S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4", code_hash, out_hash, met, "E_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4"))

    # SIM 9
    out, met = sim_negctrl_axis6_commute()
    out_hash = dump_json("results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V2.json", out)
    blocks.append(emit_block("S_SIM_NEGCTRL_AXIS6_COMMUTE_V2", code_hash, out_hash, met, "E_SIM_NEGCTRL_AXIS6_COMMUTE_V2"))

    # SIM 10
    out, met = sim_axis0_traj_corr()
    out_hash = dump_json("results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json", out)
    blocks.append(emit_block("S_SIM_AXIS0_TRAJ_CORR_SUITE_V4", code_hash, out_hash, met, "E_SIM_AXIS0_TRAJ_CORR_SUITE_V4"))

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(blocks) + "\n")

    print("DONE: wrote sim_evidence_pack.txt and results_*.json")

if __name__ == "__main__":
    main()