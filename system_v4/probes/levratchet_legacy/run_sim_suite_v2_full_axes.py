#!/usr/bin/env python3
# run_sim_suite_v2_full_axes.py
# Outputs:
#   sim_evidence_pack.txt
#   results_<SIM_ID>.json (one per SIM_ID)

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

def dump_json(path: str, obj: dict) -> str:
    raw = json.dumps(obj, indent=2, sort_keys=True).encode("utf-8")
    with open(path, "wb") as f:
        f.write(raw)
    return sha256_bytes(raw)

def emit_block(sim_id: str, code_hash: str, out_hash: str, metrics: dict, token: str) -> str:
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append(f"SIM_ID: {sim_id}")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for k,v in metrics.items():
        lines.append(f"METRIC: {k}={v}")
    lines.append(f"EVIDENCE_SIGNAL {sim_id} CORR {token}")
    lines.append("END SIM_EVIDENCE v1")
    return "\n".join(lines)

# ---------- QIT basics ----------
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
    return rho if abs(tr) < 1e-18 else (rho / tr)

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
    return normalize_rho(g @ g.conj().T)

def random_density_4(rng: np.random.Generator) -> np.ndarray:
    g = rng.normal(size=(4,4)) + 1j*rng.normal(size=(4,4))
    return normalize_rho(g @ g.conj().T)

def su2_axis_angle(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = np.array(n, float); n = n / np.linalg.norm(n)
    H = n[0]*X + n[1]*Y + n[2]*Z
    c = math.cos(theta); s = math.sin(theta)
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

# ---------- CPTP terrain maps (4 topologies representatives) ----------
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

def apply_kraus(rho: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    return normalize_rho(out)

def apply_kraus_A(rhoAB: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4,4), dtype=complex)
    for K in Ks:
        KA = np.kron(K, I2)
        out += KA @ rhoAB @ KA.conj().T
    return normalize_rho(out)

# ---------- Axis0 correlation metrics ----------
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

def bell_seed(rng: np.random.Generator) -> np.ndarray:
    v = np.array([1,0,0,1], dtype=complex)/np.sqrt(2)
    rho = np.outer(v, v.conj())
    a = rng.uniform(0, 2*np.pi)
    b = rng.uniform(0, 2*np.pi)
    UA = su2_axis_angle(np.array([0,0,1.0]), a, +1)
    UB = su2_axis_angle(np.array([1.0,0,0]), b, +1)
    rho = apply_unitary_A(rho, UA)
    rho = apply_unitary_B(rho, UB)
    return normalize_rho(rho)

# ---------- SIM A: Axis1/2/3 → Topology4 + Terrain8 suite ----------
def sim_axis12_topology4_terrain8_suite(seed=0, trials=512) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    prm = {"gamma":0.12,"p":0.08,"q":0.10}
    n_vec = (0.3,0.4,0.866025403784)
    theta = 0.07
    # check both chirality signs
    out = {"seed":seed,"trials":trials,"params":prm,"theta":theta,"n_vec":list(n_vec)}
    metrics = {}
    for sign in (+1,-1):
        U = su2_axis_angle(np.array(n_vec), theta, sign)
        for terr in ("Se","Ne","Ni","Si"):
            ent=[]
            pur=[]
            # axis6 variants (UP: Phi(U(rho)), DOWN: U(Phi(rho)))
            ent_up=[]; pur_up=[]
            ent_dn=[]; pur_dn=[]
            for _ in range(trials):
                rho0 = random_density_2(rng)
                Ks = TERRAIN[terr](prm)
                rho_up = apply_kraus(apply_unitary(rho0, U), Ks)
                rho_dn = apply_unitary(apply_kraus(rho0, Ks), U)
                ent_up.append(vn_entropy(rho_up)); pur_up.append(purity(rho_up))
                ent_dn.append(vn_entropy(rho_dn)); pur_dn.append(purity(rho_dn))
            out[f"{terr}_sign{sign}_UP"] = {"entropy_mean":float(np.mean(ent_up)),"purity_mean":float(np.mean(pur_up))}
            out[f"{terr}_sign{sign}_DOWN"] = {"entropy_mean":float(np.mean(ent_dn)),"purity_mean":float(np.mean(pur_dn))}
            metrics[f"{terr}_sign{sign}_UP_entropy_mean"] = out[f"{terr}_sign{sign}_UP"]["entropy_mean"]
            metrics[f"{terr}_sign{sign}_DOWN_entropy_mean"] = out[f"{terr}_sign{sign}_DOWN"]["entropy_mean"]
            metrics[f"{terr}_sign{sign}_UP_purity_mean"] = out[f"{terr}_sign{sign}_UP"]["purity_mean"]
            metrics[f"{terr}_sign{sign}_DOWN_purity_mean"] = out[f"{terr}_sign{sign}_DOWN"]["purity_mean"]
    return out, metrics

# ---------- SIM B: Axis4 composites check (two noncommuting composites) ----------
def sim_axis4_comp_check(seed=0, trials=512) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    prm = {"gamma":0.12,"p":0.08,"q":0.10}
    n_vec = (0.3,0.4,0.866025403784)
    theta = 0.07
    U = su2_axis_angle(np.array(n_vec), theta, +1)

    # define two composite maps A and B (placeholder consistent with existing axis4 composite sims):
    # A: (Se then Ni) inside one cycle; B: (Ni then Se) inside one cycle
    # (This is purely to test noncommutation at the CPTP+unitary level)
    def A_map(rho):
        rho = apply_unitary(rho, U)
        rho = apply_kraus(rho, TERRAIN["Se"](prm))
        rho = apply_unitary(rho, U)
        rho = apply_kraus(rho, TERRAIN["Ni"](prm))
        return rho
    def B_map(rho):
        rho = apply_unitary(rho, U)
        rho = apply_kraus(rho, TERRAIN["Ni"](prm))
        rho = apply_unitary(rho, U)
        rho = apply_kraus(rho, TERRAIN["Se"](prm))
        return rho

    dS=[]
    dP=[]
    for _ in range(trials):
        rho0 = random_density_2(rng)
        A = A_map(rho0)
        B = B_map(rho0)
        dS.append(vn_entropy(A) - vn_entropy(B))
        dP.append(purity(A) - purity(B))
    out = {"seed":seed,"trials":trials,"delta_entropy_mean":float(np.mean(dS)),"delta_purity_mean":float(np.mean(dP))}
    metrics = dict(out)
    return out, metrics

# ---------- SIM C: Axis5/6 operator4 LR suite (simple LR deltas per op) ----------
def sim_axis56_operator4_lr(seed=0, trials=512) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)

    # operator reps on density matrices (single-qubit superoperators)
    def TI(rho):  # Z pinching
        return apply_kraus(rho, [np.sqrt(0.5)*I2, np.sqrt(0.5)*Z])
    def TE(rho):  # unitary
        U = su2_axis_angle(np.array([0.3,0.4,0.866025403784]), 0.23, +1)
        return apply_unitary(rho, U)
    def FI(rho):  # X dephase / filter
        return apply_kraus(rho, [np.sqrt(0.8)*I2, np.sqrt(0.2)*X])
    def FE(rho):  # amplitude damping light
        return apply_kraus(rho, terrain_Se(0.08))

    OPS = {"TI":TI, "TE":TE, "FI":FI, "FE":FE}
    metrics={}
    out={"seed":seed,"trials":trials}
    for name, op in OPS.items():
        deltas=[]
        comms=[]
        # choose a noncommuting A for LR test
        A = X if name in ("TI","FE") else Z
        for _ in range(trials):
            rho = random_density_2(rng)
            L = A @ op(rho)
            R = op(rho) @ A
            deltas.append(trace_norm(L-R))
            comms.append(fro_norm(A@op(rho) - op(rho)@A))
        out[f"{name}_delta_trace_mean"]=float(np.mean(deltas))
        out[f"{name}_comm_norm_mean"]=float(np.mean(comms))
        metrics[f"{name}_delta_trace_mean"]=out[f"{name}_delta_trace_mean"]
        metrics[f"{name}_comm_norm_mean"]=out[f"{name}_comm_norm_mean"]
    return out, metrics

# ---------- SIM D: Stage16 (2 engines × outer/inner × 4 stages) with substage_4 uniform axis6 ----------
def sim_stage16_sub4_uniform_axis6(seed=0, trials=256) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    prm={"gamma":0.12,"p":0.08,"q":0.10}
    n_vec=(0.3,0.4,0.866025403784)
    theta=0.07

    stage_order = ["Se","Ne","Ni","Si"]
    outer_axis6 = {"Se":"UP","Ne":"DOWN","Ni":"DOWN","Si":"UP"}
    inner_axis6 = {"Se":"DOWN","Ne":"UP","Ni":"UP","Si":"DOWN"}

    def op_Ti(rho): return apply_kraus(rho, [np.sqrt(0.5)*I2, np.sqrt(0.5)*Z])
    def op_Te(rho, sign): return apply_unitary(rho, su2_axis_angle(np.array(n_vec), theta, sign))
    def op_Fi(rho): return apply_kraus(rho, [np.sqrt(0.8)*I2, np.sqrt(0.2)*X])
    def op_Fe(rho): return apply_kraus(rho, terrain_Se(0.08))

    def stage_apply(rho, terr, sign, axis6_tag):
        U = su2_axis_angle(np.array(n_vec), theta, sign)
        Phi = lambda r: apply_kraus(r, TERRAIN[terr](prm))
        ops = [
            lambda r: op_Ti(r),
            lambda r: op_Te(r, sign),
            lambda r: op_Fi(r),
            lambda r: op_Fe(r),
        ]
        r = rho
        for op in ops:
            r = Phi(op(r)) if axis6_tag=="UP" else op(Phi(r))
        r = apply_unitary(r, U)
        return r

    def run_one(sign: int, loop_axis6: dict) -> dict:
        out={}
        for idx, terr in enumerate(stage_order, start=1):
            ds=[]; dp=[]
            for _ in range(trials):
                rho0 = random_density_2(rng)
                S0=vn_entropy(rho0); P0=purity(rho0)
                rho1 = stage_apply(rho0, terr, sign, loop_axis6[terr])
                ds.append(vn_entropy(rho1)-S0)
                dp.append(purity(rho1)-P0)
            out[f"{idx}_{terr}_{loop_axis6[terr]}_dS"]=float(np.mean(ds))
            out[f"{idx}_{terr}_{loop_axis6[terr]}_dP"]=float(np.mean(dp))
        return out

    T1_outer = run_one(+1, outer_axis6)
    T1_inner = run_one(+1, inner_axis6)
    T2_outer = run_one(-1, outer_axis6)
    T2_inner = run_one(-1, inner_axis6)

    out={"seed":seed,"trials":trials,"order":stage_order,"T1_outer":T1_outer,"T1_inner":T1_inner,"T2_outer":T2_outer,"T2_inner":T2_inner}
    metrics={}
    for k,v in T1_outer.items(): metrics[f"T1_outer_{k}"]=v
    for k,v in T1_inner.items(): metrics[f"T1_inner_{k}"]=v
    for k,v in T2_outer.items(): metrics[f"T2_outer_{k}"]=v
    for k,v in T2_inner.items(): metrics[f"T2_inner_{k}"]=v
    return out, metrics

# ---------- SIM E: Axis0 trajectory suite (MI + S(A|B) along history) ----------
SEQ01 = ["Se","Ne","Ni","Si"]
SEQ02 = ["Se","Si","Ni","Ne"]

def sim_axis0_traj_corr_suite(seed=0, trials=256, cycles=64, entangle_reps=1, use_entangled_init=True) -> tuple[dict, dict]:
    rng=np.random.default_rng(seed)
    prm={"gamma":0.02,"p":0.02,"q":0.02}
    n_vec=(0.3,0.4,0.866025403784)
    theta=0.07
    U = su2_axis_angle(np.array(n_vec), theta, +1)

    def run_branch(seq):
        mi_means=[]; sagb_mins=[]; neg_fracs=[]
        for _ in range(trials):
            rho = bell_seed(rng) if use_entangled_init else random_density_4(rng)
            mi_vals=[]; sagb_vals=[]
            for _c in range(cycles):
                for terr in seq:
                    rho = apply_unitary_A(rho, U)
                    rho = apply_kraus_A(rho, TERRAIN[terr](prm))
                    for _k in range(entangle_reps):
                        rho = apply_unitary_AB(rho, CNOT)
                    mi, sagb = mi_and_sAgB(rho)
                    mi_vals.append(mi); sagb_vals.append(sagb)
            mi_vals=np.array(mi_vals,float); sagb_vals=np.array(sagb_vals,float)
            mi_means.append(float(np.mean(mi_vals)))
            sagb_mins.append(float(np.min(sagb_vals)))
            neg_fracs.append(float(np.mean((sagb_vals<0.0).astype(float))))
        return {
            "MI_mean": float(np.mean(mi_means)),
            "SAgB_min_mean": float(np.mean(sagb_mins)),
            "neg_SAgB_frac_mean": float(np.mean(neg_fracs)),
        }

    r1 = run_branch(SEQ01)
    r2 = run_branch(SEQ02)

    out = {
        "seed":seed,"trials":trials,"cycles":cycles,"entangle_reps":entangle_reps,"entangled_init":use_entangled_init,
        "SEQ01":SEQ01,"SEQ02":SEQ02,"SEQ01_metrics":r1,"SEQ02_metrics":r2,
        "delta_MI_mean_SEQ02_minus_SEQ01": float(r2["MI_mean"]-r1["MI_mean"]),
        "delta_SAgB_min_mean_SEQ02_minus_SEQ01": float(r2["SAgB_min_mean"]-r1["SAgB_min_mean"]),
        "delta_negfrac_mean_SEQ02_minus_SEQ01": float(r2["neg_SAgB_frac_mean"]-r1["neg_SAgB_frac_mean"]),
    }
    metrics = {
        "SEQ01_MI_mean": r1["MI_mean"],
        "SEQ02_MI_mean": r2["MI_mean"],
        "delta_MI_mean_SEQ02_minus_SEQ01": out["delta_MI_mean_SEQ02_minus_SEQ01"],
        "SEQ01_SAgB_min_mean": r1["SAgB_min_mean"],
        "SEQ02_SAgB_min_mean": r2["SAgB_min_mean"],
        "SEQ01_negfrac_mean": r1["neg_SAgB_frac_mean"],
        "SEQ02_negfrac_mean": r2["neg_SAgB_frac_mean"],
    }
    return out, metrics

# ---------- SIM F: Negctrl axis6 commute ----------
def sim_negctrl_axis6_commute(trials=512) -> tuple[dict, dict]:
    rng=np.random.default_rng(0)
    deltas=[]; comms=[]
    for _ in range(trials):
        a = rng.uniform(0.0, 1.0)
        rho = np.array([[a,0],[0,1-a]], dtype=complex)
        A = Z
        deltas.append(trace_norm(A@rho - rho@A))
        comms.append(fro_norm(A@rho - rho@A))
    out={"trials":trials,"delta_trace_mean":float(np.mean(deltas)),"comm_norm_mean":float(np.mean(comms))}
    metrics=dict(out)
    return out, metrics

# ---------- SIM G: Negctrl axis0 no entangler ----------
def sim_negctrl_axis0_noent(seed=0, trials=256, cycles=32) -> tuple[dict, dict]:
    out, met = sim_axis0_traj_corr_suite(seed=seed,trials=trials,cycles=cycles,entangle_reps=0,use_entangled_init=False)
    # just keep key metrics
    metrics = {
        "SEQ01_MI_mean": met["SEQ01_MI_mean"],
        "SEQ02_MI_mean": met["SEQ02_MI_mean"],
        "SEQ01_negfrac_mean": met["SEQ01_negfrac_mean"],
        "SEQ02_negfrac_mean": met["SEQ02_negfrac_mean"],
    }
    return out, metrics

def main():
    code_hash = sha256_file(os.path.abspath(__file__))
    blocks=[]

    # A
    out, met = sim_axis12_topology4_terrain8_suite()
    h = dump_json("results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json", out)
    blocks.append(emit_block("S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1", code_hash, h, met, "E_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1"))

    # B
    out, met = sim_axis4_comp_check()
    h = dump_json("results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json", out)
    blocks.append(emit_block("S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1", code_hash, h, met, "E_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1"))

    # C
    out, met = sim_axis56_operator4_lr()
    h = dump_json("results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json", out)
    blocks.append(emit_block("S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1", code_hash, h, met, "E_SIM_AXIS56_OPERATOR4_LR_SUITE_V1"))

    # D
    out, met = sim_stage16_sub4_uniform_axis6()
    h = dump_json("results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json", out)
    blocks.append(emit_block("S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5", code_hash, h, met, "E_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5"))

    # E
    out, met = sim_axis0_traj_corr_suite(seed=0,trials=256,cycles=64,entangle_reps=1,use_entangled_init=True)
    h = dump_json("results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json", out)
    blocks.append(emit_block("S_SIM_AXIS0_TRAJ_CORR_SUITE_V5", code_hash, h, met, "E_SIM_AXIS0_TRAJ_CORR_SUITE_V5"))

    # F
    out, met = sim_negctrl_axis6_commute()
    h = dump_json("results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V3.json", out)
    blocks.append(emit_block("S_SIM_NEGCTRL_AXIS6_COMMUTE_V3", code_hash, h, met, "E_SIM_NEGCTRL_AXIS6_COMMUTE_V3"))

    # G
    out, met = sim_negctrl_axis0_noent()
    h = dump_json("results_S_SIM_NEGCTRL_AXIS0_NOENT_V1.json", out)
    blocks.append(emit_block("S_SIM_NEGCTRL_AXIS0_NOENT_V1", code_hash, h, met, "E_SIM_NEGCTRL_AXIS0_NOENT_V1"))

    with open("sim_evidence_pack.txt","w",encoding="utf-8") as f:
        f.write("\n\n".join(blocks) + "\n")
    print("DONE: sim_evidence_pack.txt written")

if __name__ == "__main__":
    main()