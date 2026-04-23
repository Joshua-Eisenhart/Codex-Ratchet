#!/usr/bin/env python3
# run_ultra4_full_stack.py
# Output:
#   results_ultra4_full_stack.json
#   sim_evidence_pack.txt  (SIM_EVIDENCE for S_SIM_ULTRA4_FULL_STACK)

from __future__ import annotations
import json, hashlib, os
import numpy as np

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

I2 = np.eye(2, dtype=complex)
X  = np.array([[0,1],[1,0]], dtype=complex)
Y  = np.array([[0,-1j],[1j,0]], dtype=complex)
Z  = np.array([[1,0],[0,-1]], dtype=complex)

def expm_2x2(a: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eig(a)
    return (v @ np.diag(np.exp(w)) @ np.linalg.inv(v)).astype(complex)

def unitary_from_axis(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = n / np.linalg.norm(n)
    H = n[0]*X + n[1]*Y + n[2]*Z
    return expm_2x2(-1j * sign * theta * H)

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())

def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))

def ginibre_density(d: int, rng: np.random.Generator) -> np.ndarray:
    a = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    rho = a @ a.conj().T
    return rho / np.trace(rho)

# ---------- Axis3 geometry: Berry flux approx (qubit monopole, should be ±2π) ----------
def berry_flux_approx(sign: int, gridN: int = 48) -> float:
    thetas = np.linspace(1e-6, np.pi-1e-6, gridN)
    phis = np.linspace(0, 2*np.pi, 2*gridN, endpoint=False)
    flux = 0.0
    for i in range(len(thetas)-1):
        for j in range(len(phis)-1):
            th0, th1 = thetas[i], thetas[i+1]
            ph0, ph1 = phis[j], phis[j+1]
            dA = (ph1-ph0) * (np.cos(th0) - np.cos(th1))
            flux += sign * 0.5 * dA
    return float(flux)

# ---------- Terrains (1q CPTP on A) ----------
def apply_kraus_1q(rho: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    return out / np.trace(out)

def terr_Se(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def terr_Ne(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-p) * I2
    K1 = np.sqrt(p) * X
    return [K0, K1]

def terr_Ni(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-q) * I2
    K1 = np.sqrt(q) * Z
    return [K0, K1]

def terr_Si() -> list[np.ndarray]:
    return [I2]

TERRAIN = {
    "Se": lambda params: terr_Se(params["gamma"]),
    "Ne": lambda params: terr_Ne(params["p"]),
    "Ni": lambda params: terr_Ni(params["q"]),
    "Si": lambda params: terr_Si(),
}

# ---------- 4 operators (1q exemplar maps) ----------
def op_ti(rho: np.ndarray) -> np.ndarray:
    P0 = np.array([[1,0],[0,0]], dtype=complex)
    P1 = np.array([[0,0],[0,1]], dtype=complex)
    out = P0 @ rho @ P0 + P1 @ rho @ P1
    return out / np.trace(out)

def op_te(rho: np.ndarray, theta_te: float) -> np.ndarray:
    U = expm_2x2(-1j * theta_te * X)
    out = U @ rho @ U.conj().T
    return out / np.trace(out)

def op_fi(rho: np.ndarray, q_fi: float) -> np.ndarray:
    out = (1-q_fi) * rho + q_fi * (Z @ rho @ Z)
    return out / np.trace(out)

def op_fe(rho: np.ndarray, d: float) -> np.ndarray:
    out = (1-d) * rho + (d/3.0) * (X @ rho @ X + Y @ rho @ Y + Z @ rho @ Z)
    return out / np.trace(out)

def apply_operator(rho: np.ndarray, opname: str, oparams: dict) -> np.ndarray:
    if opname == "ti":
        return op_ti(rho)
    if opname == "te":
        return op_te(rho, oparams["theta_te"])
    if opname == "fi":
        return op_fi(rho, oparams["q_fi"])
    if opname == "fe":
        return op_fe(rho, oparams["d_fe"])
    raise ValueError("bad opname")

# Axis6 patterns across 4 substages
def axis6_pattern(mode: str, base: str, rng: np.random.Generator) -> list[str]:
    if mode == "UNIFORM":
        return [base]*4
    if mode == "MIX_A":
        return ["UP","DOWN","UP","DOWN"]
    if mode == "MIX_B":
        return ["DOWN","UP","DOWN","UP"]
    if mode == "MIX_R":
        return rng.choice(["UP","DOWN"], size=4, replace=True).tolist()
    raise ValueError("bad axis6 mode")

def stage_apply(rng: np.random.Generator, rho: np.ndarray, terr: str, base_axis6: str, axis6_mode: str,
                U: np.ndarray, tparams: dict, oparams: dict) -> np.ndarray:
    ops = ["ti","te","fi","fe"]
    pat = axis6_pattern(axis6_mode, base_axis6, rng)
    for opname, ax6 in zip(ops, pat):
        rho = (U @ rho @ U.conj().T) / np.trace(rho)
        Ks = TERRAIN[terr](tparams)
        if ax6 == "UP":
            rho = apply_kraus_1q(apply_operator(rho, opname, oparams), Ks)
        else:
            rho = apply_operator(apply_kraus_1q(rho, Ks), opname, oparams)
    return rho

def stage16_delta(seed: int, axis3_sign: int, terr: str, base_axis6: str, axis6_mode: str,
                  states: int, theta: float, n_vec: np.ndarray, tparams: dict, oparams: dict) -> tuple[float,float]:
    rng = np.random.default_rng(seed)
    U = unitary_from_axis(n_vec, theta, axis3_sign)
    dS=[]; dP=[]
    for _ in range(states):
        rho0 = ginibre_density(2, rng)
        rU = stage_apply(rng, rho0, terr, base_axis6, "UNIFORM", U, tparams, oparams)
        rM = stage_apply(rng, rho0, terr, base_axis6, axis6_mode, U, tparams, oparams)
        dS.append(vn_entropy(rM) - vn_entropy(rU))
        dP.append(purity(rM) - purity(rU))
    return float(np.mean(dS)), float(np.mean(dP))

# ---------- Axis0 AB trajectory suite ----------
CNOT = np.array([[1,0,0,0],
                 [0,1,0,0],
                 [0,0,0,1],
                 [0,0,1,0]], dtype=complex)
CZ = np.array([[1,0,0,0],
               [0,1,0,0],
               [0,0,1,0],
               [0,0,0,-1]], dtype=complex)

def apply_unitary_AB(rhoAB: np.ndarray, UAB: np.ndarray) -> np.ndarray:
    out = UAB @ rhoAB @ UAB.conj().T
    return out / np.trace(out)

def apply_unitary_A_AB(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UA = np.kron(U, I2)
    out = UA @ rhoAB @ UA.conj().T
    return out / np.trace(out)

def apply_kraus_A_AB(rhoAB: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4,4), dtype=complex)
    for K in Ks:
        KA = np.kron(K, I2)
        out += KA @ rhoAB @ KA.conj().T
    return out / np.trace(out)

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

def bell_seed(rng: np.random.Generator) -> np.ndarray:
    phi = np.array([1,0,0,1], dtype=complex) / np.sqrt(2)
    rho = np.outer(phi, phi.conj())
    a = rng.uniform(0, 2*np.pi)
    b = rng.uniform(0, 2*np.pi)
    UA = expm_2x2(-1j * a * Z)
    UB = expm_2x2(-1j * b * X)
    rho = (np.kron(UA, I2) @ rho @ np.kron(UA, I2).conj().T) / np.trace(rho)
    rho = (np.kron(I2, UB) @ rho @ np.kron(I2, UB).conj().T) / np.trace(rho)
    return rho

def axis0_traj(seed: int, axis3_sign: int, seq: list[str], direction: str, init_mode: str,
              trials: int, cycles: int, theta: float, n_vec: np.ndarray,
              tparams_ab: dict, entangler: np.ndarray, entangle_reps: int) -> dict:
    rng = np.random.default_rng(seed)
    U = unitary_from_axis(n_vec, theta, axis3_sign)
    seq_use = list(seq) if direction == "FWD" else list(reversed(seq))
    MI=[]; SA=[]; NF=[]
    for _ in range(trials):
        rho = bell_seed(rng) if init_mode == "BELL" else ginibre_density(4, rng)
        mi0, s0 = mi_and_sAgB(rho)
        mi_series=[mi0]; s_series=[s0]
        for _c in range(cycles):
            for terr in seq_use:
                Ks = TERRAIN[terr](tparams_ab)
                rho = apply_unitary_A_AB(rho, U)
                rho = apply_kraus_A_AB(rho, Ks)
                for _k in range(entangle_reps):
                    rho = apply_unitary_AB(rho, entangler)
            mi, sAgB = mi_and_sAgB(rho)
            mi_series.append(mi); s_series.append(sAgB)
        mi_series=np.array(mi_series,float); s_series=np.array(s_series,float)
        MI.append(mi_series.mean())
        SA.append(s_series.mean())
        NF.append(float(np.mean((s_series < 0.0).astype(float))))
    return {
        "MI_traj_mean": float(np.mean(MI)),
        "SAgB_traj_mean": float(np.mean(SA)),
        "neg_SAgB_frac_traj": float(np.mean(NF)),
    }

# Axis12 adjacency counts (edge checks)
def axis12_counts(seqs: dict) -> dict:
    def has_edge(seq, a, b):
        n = len(seq)
        for i in range(n):
            x = seq[i]; y = seq[(i+1)%n]
            if (x==a and y==b) or (x==b and y==a):
                return 1
        return 0
    out={}
    for name, seq in seqs.items():
        out[f"{name}_SENI"]=has_edge(seq,"Se","Ni")
        out[f"{name}_NESI"]=has_edge(seq,"Ne","Si")
    return out

def main():
    seeds = [0,1,2,3]
    stage_states = 2048
    axis0_trials = 128
    axis0_cycles = 64

    theta = 0.07
    n_vec = np.array([0.3, 0.4, 0.866025403784], float)

    SEQS = {
        "SEQ01": ["Se","Ne","Ni","Si"],
        "SEQ02": ["Se","Si","Ni","Ne"],
        "SEQ03": ["Se","Ne","Si","Ni"],
        "SEQ04": ["Se","Si","Ne","Ni"],
    }

    TERRAIN_ORDER = ["Se","Ne","Ni","Si"]
    OUTER_AXIS6 = ["UP","DOWN","DOWN","UP"]
    INNER_AXIS6 = ["DOWN","UP","UP","DOWN"]
    axis6_modes = ["MIX_A","MIX_B","MIX_R"]

    tparams_1q = {"gamma": 0.12, "p": 0.08, "q": 0.10}
    oparams_1q = {"theta_te": 0.05, "q_fi": 0.06, "d_fe": 0.04}

    tparams_ab = {"gamma": 0.02, "p": 0.02, "q": 0.02}
    entanglers = {"CNOT": CNOT, "CZ": CZ}
    entangle_reps_list = [1,2]

    out = {
        "seeds": seeds,
        "stage_states": stage_states,
        "axis0_trials": axis0_trials,
        "axis0_cycles": axis0_cycles,
        "theta": theta,
        "n_vec": [float(x) for x in n_vec.tolist()],
        "berry_flux_plus": berry_flux_approx(+1),
        "berry_flux_minus": berry_flux_approx(-1),
        "axis12": axis12_counts(SEQS),
        "tparams_1q": dict(tparams_1q),
        "oparams_1q": dict(oparams_1q),
        "tparams_ab": dict(tparams_ab),
        "seqs": SEQS,
        "stage16": {},
        "axis0_ab": {},
    }

    # Stage16: uniform-vs-mix deltas (both types, both loops, all terrains)
    for sign, tag in [(+1,"T1"),(-1,"T2")]:
        for loop_name, axis6_list in [("outer", OUTER_AXIS6), ("inner", INNER_AXIS6)]:
            for idx, terr in enumerate(TERRAIN_ORDER):
                base_ax6 = axis6_list[idx]
                for mm in axis6_modes:
                    dS=[]; dP=[]
                    for s in seeds:
                        ds, dp = stage16_delta(10000+idx*10+s, sign, terr, base_ax6, mm,
                                               stage_states, theta, n_vec, tparams_1q, oparams_1q)
                        dS.append(ds); dP.append(dp)
                    out["stage16"][f"{tag}_{loop_name}_{idx+1}_{terr}_{base_ax6}_{mm}"] = {
                        "dS": float(np.mean(dS)),
                        "dP": float(np.mean(dP)),
                    }

    # Axis0 AB: SEQ deltas vs SEQ01 baseline, across dirs, init, entangler, reps, types
    for sign, tag in [(+1,"T1"),(-1,"T2")]:
        for direction in ["FWD","REV"]:
            for init_mode in ["GINIBRE","BELL"]:
                for ent_name, entU in entanglers.items():
                    for reps in entangle_reps_list:
                        base = None
                        for seq_name, seq in SEQS.items():
                            MI=[]; SA=[]; NF=[]
                            for s in seeds:
                                r = axis0_traj(20000+s, sign, seq, direction, init_mode,
                                               axis0_trials, axis0_cycles, theta, n_vec,
                                               tparams_ab, entU, reps)
                                MI.append(r["MI_traj_mean"])
                                SA.append(r["SAgB_traj_mean"])
                                NF.append(r["neg_SAgB_frac_traj"])
                            rec = {
                                "MI_traj_mean": float(np.mean(MI)),
                                "SAgB_traj_mean": float(np.mean(SA)),
                                "neg_SAgB_frac_traj": float(np.mean(NF)),
                            }
                            k = f"{tag}_{direction}_{init_mode}_{ent_name}_R{reps}_{seq_name}"
                            if seq_name == "SEQ01":
                                base = rec
                                out["axis0_ab"][k] = rec
                            else:
                                out["axis0_ab"][k] = {
                                    "dMI": rec["MI_traj_mean"] - base["MI_traj_mean"],
                                    "dSAgB": rec["SAgB_traj_mean"] - base["SAgB_traj_mean"],
                                    "dNegFrac": rec["neg_SAgB_frac_traj"] - base["neg_SAgB_frac_traj"],
                                }

    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_ultra4_full_stack.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    stage_abs_dS = [abs(v["dS"]) for v in out["stage16"].values()]
    stage_abs_dP = [abs(v["dP"]) for v in out["stage16"].values()]

    lines=[]
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_ULTRA4_FULL_STACK")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    lines.append(f"METRIC: berry_flux_plus={out['berry_flux_plus']}")
    lines.append(f"METRIC: berry_flux_minus={out['berry_flux_minus']}")
    lines.append(f"METRIC: stage16_dS_absmax={float(np.max(stage_abs_dS))}")
    lines.append(f"METRIC: stage16_dP_absmax={float(np.max(stage_abs_dP))}")

    # Axis12 edge counts
    for k,v in sorted(out["axis12"].items()):
        lines.append(f"METRIC: axis12_{k}={v}")

    # Emit only SEQ04 deltas (largest stress) to keep evidence short
    for k,v in sorted(out["axis0_ab"].items()):
        if k.endswith("_SEQ04"):
            lines.append(f"METRIC: {k}_dMI={v['dMI']}")
            lines.append(f"METRIC: {k}_dSAgB={v['dSAgB']}")
            lines.append(f"METRIC: {k}_dNegFrac={v['dNegFrac']}")

    lines.append("EVIDENCE_SIGNAL S_SIM_ULTRA4_FULL_STACK CORR E_SIM_ULTRA4_FULL_STACK")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt","w",encoding="utf-8") as f:
        f.write("\n".join(lines)+"\n")

    print("DONE: wrote results_ultra4_full_stack.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()