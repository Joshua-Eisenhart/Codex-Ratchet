#!/usr/bin/env python3
# run_batch_v3.py
# Produces:
#   results_batch_v3.json
#   sim_evidence_pack.txt  (4 SIM_EVIDENCE v1 blocks)

from __future__ import annotations
import json, hashlib, os, math
import numpy as np

# ---------- hashing ----------
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

# ---------- basic QIT ----------
I2 = np.eye(2, dtype=complex)
X  = np.array([[0,1],[1,0]], dtype=complex)
Y  = np.array([[0,-1j],[1j,0]], dtype=complex)
Z  = np.array([[1,0],[0,-1]], dtype=complex)
H2 = (1/np.sqrt(2))*np.array([[1,1],[1,-1]], dtype=complex)

def expm_2x2(a: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eig(a)
    return (v @ np.diag(np.exp(w)) @ np.linalg.inv(v)).astype(complex)

def unitary_from_axis(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = n / np.linalg.norm(n)
    HH = n[0]*X + n[1]*Y + n[2]*Z
    return expm_2x2(-1j * sign * theta * HH)

def rand_rho_qubit(rng: np.random.Generator) -> np.ndarray:
    # Ginibre -> normalize
    a = rng.normal(size=(2,2)) + 1j*rng.normal(size=(2,2))
    rho = a @ a.conj().T
    rho = rho / np.trace(rho)
    return rho

def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w*np.log(w)).sum())

# Axis-6 action orientation as algebraic sidedness (renormalize by trace)
def left_action(A: np.ndarray, rho: np.ndarray) -> np.ndarray:
    out = A @ rho
    tr = np.trace(out)
    if abs(tr) < 1e-16:  # fallback
        return rho
    return out / tr

def right_action(A: np.ndarray, rho: np.ndarray) -> np.ndarray:
    out = rho @ A
    tr = np.trace(out)
    if abs(tr) < 1e-16:
        return rho
    return out / tr

def comm_norm(A: np.ndarray, rho: np.ndarray) -> float:
    c = A @ rho - rho @ A
    return float(np.linalg.norm(c))

def delta_trace_lr(A: np.ndarray, rho: np.ndarray) -> float:
    lr = left_action(A, rho)
    rr = right_action(A, rho)
    return float(np.linalg.norm(lr - rr))

# ---------- terrains as CPTP on qubit ----------
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
    "Se": lambda par: terrain_Se(par["gamma"]),
    "Ne": lambda par: terrain_Ne(par["p"]),
    "Ni": lambda par: terrain_Ni(par["q"]),
    "Si": lambda par: terrain_Si(),
}

def apply_kraus(rho: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    tr = np.trace(out)
    return out / tr

def apply_unitary(rho: np.ndarray, U: np.ndarray) -> np.ndarray:
    out = U @ rho @ U.conj().T
    return out / np.trace(out)

# ---------- Axis12: pairing/adj counters on sequences ----------
PAIR_SENI = ("Se","Ni")
PAIR_NESI = ("Ne","Si")

def cyclic_edges(seq: list[str]) -> list[tuple[str,str]]:
    return [(seq[i], seq[(i+1)%len(seq)]) for i in range(len(seq))]

# candidate adjacency sets (two)
SETA_ALLOWED = {("Se","Ne"),("Ne","Ni"),("Ni","Si"),("Si","Se")}
SETB_ALLOWED = {("Se","Si"),("Si","Ni"),("Ni","Ne"),("Ne","Se")}

def axis12_counts(seq: list[str]) -> dict:
    edges = cyclic_edges(seq)
    seni = int(any((a,b)==PAIR_SENI or (a,b)==(PAIR_SENI[1],PAIR_SENI[0]) for (a,b) in edges))
    nesi = int(any((a,b)==PAIR_NESI or (a,b)==(PAIR_NESI[1],PAIR_NESI[0]) for (a,b) in edges))
    seta_bad = sum(1 for e in edges if e not in SETA_ALLOWED)
    setb_bad = sum(1 for e in edges if e not in SETB_ALLOWED)
    return {
        "seni_within": seni,
        "nesi_within": nesi,
        "seta_bad": int(seta_bad),
        "setb_bad": int(setb_bad),
    }

# ---------- Axis0: AB correlation trajectory metrics ----------
I4 = np.eye(4, dtype=complex)

def kron(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return np.kron(A, B)

def partial_trace_AB_to_A(rhoAB: np.ndarray) -> np.ndarray:
    rhoA = np.zeros((2,2), dtype=complex)
    for a in range(2):
        for ap in range(2):
            s = 0.0+0.0j
            for b in range(2):
                i = 2*a + b
                j = 2*ap + b
                s += rhoAB[i,j]
            rhoA[a,ap] = s
    return rhoA / np.trace(rhoA)

def partial_trace_AB_to_B(rhoAB: np.ndarray) -> np.ndarray:
    rhoB = np.zeros((2,2), dtype=complex)
    for b in range(2):
        for bp in range(2):
            s = 0.0+0.0j
            for a in range(2):
                i = 2*a + b
                j = 2*a + bp
                s += rhoAB[i,j]
            rhoB[b,bp] = s
    return rhoB / np.trace(rhoB)

def mi_and_sAgB(rhoAB: np.ndarray) -> tuple[float,float]:
    rhoA = partial_trace_AB_to_A(rhoAB)
    rhoB = partial_trace_AB_to_B(rhoAB)
    sab = vn_entropy(rhoAB)
    sa  = vn_entropy(rhoA)
    sb  = vn_entropy(rhoB)
    mi = sa + sb - sab
    sAgB = sab - sb
    return float(mi), float(sAgB)

def bell_phi_plus(rng: np.random.Generator) -> np.ndarray:
    phi = np.array([1,0,0,1], dtype=complex)/np.sqrt(2)
    rho = np.outer(phi, phi.conj())
    # random local twirl
    tA = rng.uniform(0, 2*np.pi)
    tB = rng.uniform(0, 2*np.pi)
    UA = expm_2x2(-1j*tA*Z)
    UB = expm_2x2(-1j*tB*X)
    UAB = kron(UA, UB)
    rho = UAB @ rho @ UAB.conj().T
    return rho / np.trace(rho)

CNOT = np.array([
    [1,0,0,0],
    [0,1,0,0],
    [0,0,0,1],
    [0,0,1,0],
], dtype=complex)

def apply_unitary_AB(rhoAB: np.ndarray, UAB: np.ndarray) -> np.ndarray:
    out = UAB @ rhoAB @ UAB.conj().T
    return out / np.trace(out)

def apply_kraus_A_on_AB(rhoAB: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4,4), dtype=complex)
    for K in Ks:
        KA = kron(K, I2)
        out += KA @ rhoAB @ KA.conj().T
    return out / np.trace(out)

def apply_unitary_A_on_AB(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UA = kron(U, I2)
    out = UA @ rhoAB @ UA.conj().T
    return out / np.trace(out)

# ---------- SIM 1: Axis12 channel realization ----------
def sim_axis12_channel_realization(seed: int=0) -> dict:
    rng = np.random.default_rng(seed)
    seqs = {
        "SEQ01": ["Se","Ne","Ni","Si"],
        "SEQ02": ["Se","Si","Ni","Ne"],
        "SEQ03": ["Se","Ne","Si","Ni"],
        "SEQ04": ["Se","Si","Ne","Ni"],
    }
    counts = {}
    for k,seq in seqs.items():
        c = axis12_counts(seq)
        for kk,v in c.items():
            counts[f"{kk}_{k}"] = v

    # quick channel realization metric (entropy/purity endstate) for +/- chirality
    n_vec = np.array([0.3,0.4,0.866025403784], float)
    theta = 0.07
    Uplus  = unitary_from_axis(n_vec, theta, +1)
    Uminus = unitary_from_axis(n_vec, theta, -1)
    params = {"gamma":0.12,"p":0.08,"q":0.1}
    cycles = 64
    trials = 256

    def run_seq(U: np.ndarray, seq: list[str]) -> tuple[float,float]:
        S_list = []
        P_list = []
        for _ in range(trials):
            rho = rand_rho_qubit(rng)
            for _c in range(cycles):
                for terr in seq:
                    rho = apply_unitary(rho, U)
                    rho = apply_kraus(rho, TERRAIN[terr](params))
            S_list.append(vn_entropy(rho))
            P_list.append(purity(rho))
        return float(np.mean(S_list)), float(np.mean(P_list))

    out = {"seed":seed, "counts":counts, "seqs":seqs, "cycles":cycles, "trials":trials,
           "theta":theta, "n_vec":n_vec.tolist(), "terrain_params":params}

    for name, seq in seqs.items():
        Sp,Pp = run_seq(Uplus, seq)
        Sm,Pm = run_seq(Uminus, seq)
        out[f"{name}_plus_S_mean"] = Sp
        out[f"{name}_plus_P_mean"] = Pp
        out[f"{name}_minus_S_mean"] = Sm
        out[f"{name}_minus_P_mean"] = Pm

    return out

# ---------- SIM 2: Stage16 substage-4 uniform axis6 ----------
def sim_stage16_sub4_axis6_uniform(seed: int=0) -> dict:
    rng = np.random.default_rng(seed)
    # operator matrices (placeholders; terms are already permitted in your ratchet)
    A_TI = Z
    A_TE = X
    A_FI = H2
    A_FE = Y

    # stage order fixed: Se -> Ne -> Ni -> Si
    order = ["Se","Ne","Ni","Si"]

    # axis6 per stage (UP/DOWN tags) for outer/inner (both types use same checker)
    outer_tag = {"Se":"UP", "Ne":"DOWN", "Ni":"DOWN", "Si":"UP"}
    inner_tag = {"Se":"DOWN", "Ne":"UP", "Ni":"UP", "Si":"DOWN"}

    def apply_axis6(tag: str, A: np.ndarray, rho: np.ndarray) -> np.ndarray:
        if tag == "UP":
            return left_action(A, rho)
        return right_action(A, rho)

    def one_pass(loop_tag: dict, mix_axis6: bool) -> dict:
        # returns mean dS/dP per terrain, per substage aggregated
        trials = 256
        d = {}
        for terr in order:
            tag = loop_tag[terr]
            dS = []
            dP = []
            for _ in range(trials):
                rho = rand_rho_qubit(rng)
                S0 = vn_entropy(rho); P0 = purity(rho)
                # 4 substages; uniform axis6 unless mix_axis6=True (flip each substage)
                tags = [tag, tag, tag, tag]
                if mix_axis6:
                    tags = ["UP","DOWN","UP","DOWN"]
                rho = apply_axis6(tags[0], A_TI, rho)
                rho = apply_axis6(tags[1], A_TE, rho)
                rho = apply_axis6(tags[2], A_FI, rho)
                rho = apply_axis6(tags[3], A_FE, rho)
                dS.append(vn_entropy(rho)-S0)
                dP.append(purity(rho)-P0)
            d[f"{terr}_dS_mean"] = float(np.mean(dS))
            d[f"{terr}_dP_mean"] = float(np.mean(dP))
        return d

    out = {"seed":seed, "order":order}
    out["outer_uniform"] = one_pass(outer_tag, mix_axis6=False)
    out["outer_mixed"]   = one_pass(outer_tag, mix_axis6=True)
    out["inner_uniform"] = one_pass(inner_tag, mix_axis6=False)
    out["inner_mixed"]   = one_pass(inner_tag, mix_axis6=True)

    # summary deltas (uniform minus mixed)
    def diff_block(a: dict, b: dict) -> dict:
        r = {}
        for k in a.keys():
            r[k] = float(a[k]-b[k])
        return r
    out["delta_outer_uniform_minus_mixed"] = diff_block(out["outer_uniform"], out["outer_mixed"])
    out["delta_inner_uniform_minus_mixed"] = diff_block(out["inner_uniform"], out["inner_mixed"])
    return out

# ---------- SIM 3: Axis0 trajectory correlation suite ----------
def sim_axis0_traj_corr_suite(seed: int=0) -> dict:
    rng = np.random.default_rng(seed)
    SEQ01 = ["Se","Ne","Ni","Si"]
    SEQ02 = ["Se","Si","Ni","Ne"]

    axis3_signs = [+1,-1]
    n_vec = np.array([0.3,0.4,0.866025403784], float)
    theta = 0.07
    params = {"gamma":0.02,"p":0.02,"q":0.02}
    cycles = 16
    trials = 256
    entangle_reps = 1

    def run(seq: list[str], sign: int) -> dict:
        U = unitary_from_axis(n_vec, theta, sign)
        MI_paths = []
        SA_paths = []
        for _ in range(trials):
            rho = bell_phi_plus(rng)
            mi_t = []
            sa_t = []
            for _c in range(cycles):
                for terr in seq:
                    rho = apply_unitary_A_on_AB(rho, U)
                    rho = apply_kraus_A_on_AB(rho, TERRAIN[terr](params))
                    for _k in range(entangle_reps):
                        rho = apply_unitary_AB(rho, CNOT)
                    mi, sAgB = mi_and_sAgB(rho)
                    mi_t.append(mi)
                    sa_t.append(sAgB)
            MI_paths.append(mi_t)
            SA_paths.append(sa_t)

        MI = np.array(MI_paths, float)   # shape [trials, T]
        SA = np.array(SA_paths, float)

        # time-avg
        MI_bar = float(np.mean(MI))
        SA_bar = float(np.mean(SA))

        # simple decay proxy: slope of log(MI+eps) vs step index
        eps = 1e-12
        x = np.arange(MI.shape[1], dtype=float)
        y = np.log(np.mean(MI, axis=0) + eps)
        # least squares slope
        xm = x.mean(); ym = y.mean()
        denom = float(np.sum((x-xm)**2)) + 1e-16
        slope = float(np.sum((x-xm)*(y-ym)) / denom)

        neg_frac = float(np.mean((SA < 0.0).astype(float)))

        return {
            "MI_mean": float(np.mean(MI[:,-1])),
            "MI_bar": MI_bar,
            "SAgB_mean": float(np.mean(SA[:,-1])),
            "SAgB_bar": SA_bar,
            "neg_SAgB_frac": neg_frac,
            "logMI_slope": slope,
        }

    out = {"seed":seed,"cycles":cycles,"trials":trials,"theta":theta,"n_vec":n_vec.tolist(),
           "terrain_params":params,"entangle_reps":entangle_reps,
           "SEQ01":SEQ01,"SEQ02":SEQ02}

    for sign in axis3_signs:
        r1 = run(SEQ01, sign)
        r2 = run(SEQ02, sign)
        out[f"sign{sign}_SEQ01"] = r1
        out[f"sign{sign}_SEQ02"] = r2
        out[f"sign{sign}_delta_MI_bar_SEQ02_minus_SEQ01"] = float(r2["MI_bar"] - r1["MI_bar"])
        out[f"sign{sign}_delta_SAgB_bar_SEQ02_minus_SEQ01"] = float(r2["SAgB_bar"] - r1["SAgB_bar"])
        out[f"sign{sign}_delta_negfrac_SEQ02_minus_SEQ01"] = float(r2["neg_SAgB_frac"] - r1["neg_SAgB_frac"])

    return out

# ---------- SIM 4: negative control (axis6 collapse via commute) ----------
def sim_negctrl_axis6_commute(seed: int=0) -> dict:
    rng = np.random.default_rng(seed)
    trials = 512
    A = I2  # commutes with all rho
    cn = []
    dt = []
    for _ in range(trials):
        rho = rand_rho_qubit(rng)
        cn.append(comm_norm(A, rho))
        dt.append(delta_trace_lr(A, rho))
    return {
        "comm_norm_mean": float(np.mean(cn)),
        "comm_norm_min": float(np.min(cn)),
        "comm_norm_max": float(np.max(cn)),
        "delta_trace_mean": float(np.mean(dt)),
        "delta_trace_min": float(np.min(dt)),
        "delta_trace_max": float(np.max(dt)),
    }

def make_sim_evidence(sim_id: str, code_hash: str, payload: dict, metrics: dict, token: str) -> str:
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append(f"SIM_ID: {sim_id}")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for k,v in metrics.items():
        lines.append(f"METRIC: {k}={v}")
    lines.append(f"EVIDENCE_SIGNAL {sim_id} CORR {token}")
    lines.append("END SIM_EVIDENCE v1")
    return "\n".join(lines) + "\n"

def main():
    code_hash = sha256_file(os.path.abspath(__file__))

    out_all = {}

    # SIM 1
    sim1_id = "S_SIM_AXIS12_CHANNEL_REALIZATION_V3"
    sim1 = sim_axis12_channel_realization(seed=0)
    m1 = {}
    for k,v in sim1["counts"].items():
        m1[k] = v
    # include small subset of realization metrics
    for name in ["SEQ01","SEQ02","SEQ03","SEQ04"]:
        m1[f"{name}_plus_S_mean"]  = sim1[f"{name}_plus_S_mean"]
        m1[f"{name}_plus_P_mean"]  = sim1[f"{name}_plus_P_mean"]
        m1[f"{name}_minus_S_mean"] = sim1[f"{name}_minus_S_mean"]
        m1[f"{name}_minus_P_mean"] = sim1[f"{name}_minus_P_mean"]
    out_all[sim1_id] = sim1

    # SIM 2
    sim2_id = "S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V3"
    sim2 = sim_stage16_sub4_axis6_uniform(seed=0)
    m2 = {}
    for blk in ["outer_uniform","outer_mixed","inner_uniform","inner_mixed"]:
        for k,v in sim2[blk].items():
            m2[f"{blk}_{k}"] = v
    out_all[sim2_id] = sim2

    # SIM 3
    sim3_id = "S_SIM_AXIS0_TRAJ_CORR_SUITE_V3"
    sim3 = sim_axis0_traj_corr_suite(seed=0)
    m3 = {}
    # flatten key metrics
    for sign in [+1,-1]:
        r1 = sim3[f"sign{sign}_SEQ01"]
        r2 = sim3[f"sign{sign}_SEQ02"]
        for kk in ["MI_bar","SAgB_bar","neg_SAgB_frac","logMI_slope"]:
            m3[f"sign{sign}_SEQ01_{kk}"] = r1[kk]
            m3[f"sign{sign}_SEQ02_{kk}"] = r2[kk]
        m3[f"sign{sign}_delta_MI_bar_SEQ02_minus_SEQ01"] = sim3[f"sign{sign}_delta_MI_bar_SEQ02_minus_SEQ01"]
        m3[f"sign{sign}_delta_SAgB_bar_SEQ02_minus_SEQ01"] = sim3[f"sign{sign}_delta_SAgB_bar_SEQ02_minus_SEQ01"]
        m3[f"sign{sign}_delta_negfrac_SEQ02_minus_SEQ01"] = sim3[f"sign{sign}_delta_negfrac_SEQ02_minus_SEQ01"]
    out_all[sim3_id] = sim3

    # SIM 4
    sim4_id = "S_SIM_NEGCTRL_AXIS6_COMMUTE_V1"
    sim4 = sim_negctrl_axis6_commute(seed=0)
    m4 = dict(sim4)
    out_all[sim4_id] = sim4

    # write results json (all)
    raw_all = json.dumps(out_all, indent=2, sort_keys=True).encode("utf-8")
    with open("results_batch_v3.json","wb") as f:
        f.write(raw_all)

    # write sim evidence pack
    blocks = []
    blocks.append(make_sim_evidence(sim1_id, code_hash, sim1, m1, "E_SIM_AXIS12_CHANNEL_REALIZATION_V3"))
    blocks.append(make_sim_evidence(sim2_id, code_hash, sim2, m2, "E_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V3"))
    blocks.append(make_sim_evidence(sim3_id, code_hash, sim3, m3, "E_SIM_AXIS0_TRAJ_CORR_SUITE_V3"))
    blocks.append(make_sim_evidence(sim4_id, code_hash, sim4, m4, "E_SIM_NEGCTRL_AXIS6_COMMUTE_V1"))

    with open("sim_evidence_pack.txt","w",encoding="utf-8") as f:
        f.write("\n".join(blocks))

    print("DONE: results_batch_v3.json + sim_evidence_pack.txt")

if __name__ == "__main__":
    main()