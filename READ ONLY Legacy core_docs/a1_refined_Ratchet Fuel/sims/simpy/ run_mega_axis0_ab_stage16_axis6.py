#!/usr/bin/env python3
# run_mega_axis0_ab_stage16_axis6.py
# One run produces:
#   results_mega_axis0_ab_stage16_axis6.json
#   sim_evidence_pack.txt  (1 SIM_EVIDENCE block for S_SIM_MEGA_AXIS0_AB_AND_STAGE16_AXIS6)

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

# ---------------- AB helpers ----------------
CNOT = np.array([[1,0,0,0],
                 [0,1,0,0],
                 [0,0,0,1],
                 [0,0,1,0]], dtype=complex)

def apply_unitary_A_AB(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UA = np.kron(U, I2)
    out = UA @ rhoAB @ UA.conj().T
    return out / np.trace(out)

def apply_unitary_AB(rhoAB: np.ndarray, UAB: np.ndarray) -> np.ndarray:
    out = UAB @ rhoAB @ UAB.conj().T
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

def ginibre_density(d: int, rng: np.random.Generator) -> np.ndarray:
    a = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    rho = a @ a.conj().T
    return rho / np.trace(rho)

def bell_seed_state(rng: np.random.Generator) -> np.ndarray:
    phi = np.array([1,0,0,1], dtype=complex) / np.sqrt(2)
    rho = np.outer(phi, phi.conj())
    a = rng.uniform(0, 2*np.pi)
    b = rng.uniform(0, 2*np.pi)
    UA = expm_2x2(-1j * a * Z)
    UB = expm_2x2(-1j * b * X)
    rho = (np.kron(UA, I2) @ rho @ np.kron(UA, I2).conj().T) / np.trace(rho)
    rho = (np.kron(I2, UB) @ rho @ np.kron(I2, UB).conj().T) / np.trace(rho)
    return rho

def fit_lambda_from_series(x: np.ndarray, y: np.ndarray) -> float:
    m = (y > 0.0)
    if np.sum(m) < 2:
        return float("nan")
    xx = x[m]
    yy = np.log(y[m])
    A = np.vstack([np.ones_like(xx), xx]).T
    coef, *_ = np.linalg.lstsq(A, yy, rcond=None)
    b = coef[1]
    return float(-b)

# ---------------- terrain maps (same family as your harness) ----------------
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

def apply_kraus_1q(rho: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    return out / np.trace(out)

# ---------------- 4 operators (exemplar math) ----------------
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

# ---------------- stage = 4 substages; axis6 either uniform or mixed ----------------
def stage16_one(rng: np.random.Generator, rho0: np.ndarray, terr: str, base_axis6: str,
               U: np.ndarray, tparams: dict, oparams: dict, mix_mode: str) -> np.ndarray:
    ops = ["ti","te","fi","fe"]
    if mix_mode == "UNIFORM":
        pat = [base_axis6]*4
    elif mix_mode == "MIX_R":
        pat = rng.choice(["UP","DOWN"], size=4, replace=True).tolist()
    else:
        raise ValueError("bad mix_mode")

    rho = rho0
    for opname, ax6 in zip(ops, pat):
        rho = (U @ rho @ U.conj().T) / np.trace(rho)
        Ks = TERRAIN[terr](tparams)
        if ax6 == "UP":
            rho = apply_kraus_1q(apply_operator(rho, opname, oparams), Ks)
        else:
            rho = apply_operator(apply_kraus_1q(rho, Ks), opname, oparams)
    return rho

def run_axis0_ab_suite(rng: np.random.Generator, *, seq: list[str], direction: str, axis3_sign: int,
                       init_mode: str, trials: int, cycles: int, theta: float, n_vec: np.ndarray,
                       tparams_ab: dict, entangle_reps: int) -> dict:
    U = unitary_from_axis(n_vec, theta, axis3_sign)
    seq_use = list(seq) if direction == "FWD" else list(reversed(seq))

    MI_ts = np.zeros((trials, cycles+1), float)
    SAgB_ts = np.zeros((trials, cycles+1), float)

    for t in range(trials):
        rho = bell_seed_state(rng) if init_mode == "BELL" else ginibre_density(4, rng)
        mi0, s0 = mi_and_sAgB(rho)
        MI_ts[t,0] = mi0
        SAgB_ts[t,0] = s0

        for c in range(1, cycles+1):
            for terr in seq_use:
                Ks = TERRAIN[terr](tparams_ab)
                rho = apply_unitary_A_AB(rho, U)
                rho = apply_kraus_A_AB(rho, Ks)
                for _k in range(entangle_reps):
                    rho = apply_unitary_AB(rho, CNOT)

            mi, sAgB = mi_and_sAgB(rho)
            MI_ts[t,c] = mi
            SAgB_ts[t,c] = sAgB

    tgrid = np.arange(cycles+1, dtype=float)
    MI_mean_series = MI_ts.mean(axis=0)

    return {
        "MI_traj_mean": float(MI_ts.mean()),
        "MI_lambda_fit": float(fit_lambda_from_series(tgrid, MI_mean_series)),
        "SAgB_traj_mean": float(SAgB_ts.mean()),
        "SAgB_neg_frac_traj": float(np.mean((SAgB_ts < 0.0).astype(float))),
    }

def main():
    # ---- knobs (increase these to make it heavier) ----
    seeds = [0, 1, 2, 3]       # more seeds = more work
    stage_states = 1024        # stage16 states
    axis0_trials = 256         # AB trials
    axis0_cycles = 64          # AB cycles

    theta = 0.07
    n_vec = np.array([0.3, 0.4, 0.866025403784], float)

    # 1q stage params
    tparams_1q = {"gamma": 0.12, "p": 0.08, "q": 0.10}
    oparams_1q = {"theta_te": 0.05, "q_fi": 0.06, "d_fe": 0.04}

    # AB axis0 params (weaker noise so MI can survive)
    tparams_ab = {"gamma": 0.02, "p": 0.02, "q": 0.02}
    entangle_reps = 1

    SEQS = {
        "SEQ01": ["Se","Ne","Ni","Si"],
        "SEQ02": ["Se","Si","Ni","Ne"],
        "SEQ03": ["Se","Ne","Si","Ni"],
        "SEQ04": ["Se","Si","Ne","Ni"],
    }

    TERRAIN_ORDER = ["Se","Ne","Ni","Si"]
    OUTER_AXIS6 = ["UP","DOWN","DOWN","UP"]
    INNER_AXIS6 = ["DOWN","UP","UP","DOWN"]

    res = {
        "seeds": list(seeds),
        "theta": theta,
        "n_vec": [float(x) for x in n_vec.tolist()],
        "stage_states": stage_states,
        "axis0_trials": axis0_trials,
        "axis0_cycles": axis0_cycles,
        "tparams_1q": dict(tparams_1q),
        "oparams_1q": dict(oparams_1q),
        "tparams_ab": dict(tparams_ab),
        "entangle_reps": entangle_reps,
        "seqs": SEQS,
        "stage16": {},
        "axis0_ab": {},
    }

    # ---- stage16: uniform vs random-mix delta per stage (aggregated across seeds) ----
    for sign, tag in [(+1,"T1"),(-1,"T2")]:
        U = unitary_from_axis(n_vec, theta, sign)
        for loop_name, axis6_list in [("outer", OUTER_AXIS6), ("inner", INNER_AXIS6)]:
            for idx, terr in enumerate(TERRAIN_ORDER):
                base_ax6 = axis6_list[idx]
                dS_list = []
                dP_list = []
                for s in seeds:
                    rng = np.random.default_rng(s + 1000 + idx)
                    ent_u = []; pur_u = []
                    ent_m = []; pur_m = []
                    for _ in range(stage_states):
                        rho0 = ginibre_density(2, rng)
                        rU = stage16_one(rng, rho0, terr, base_ax6, U, tparams_1q, oparams_1q, "UNIFORM")
                        rM = stage16_one(rng, rho0, terr, base_ax6, U, tparams_1q, oparams_1q, "MIX_R")
                        ent_u.append(vn_entropy(rU)); pur_u.append(purity(rU))
                        ent_m.append(vn_entropy(rM)); pur_m.append(purity(rM))
                    dS_list.append(float(np.mean(ent_m) - np.mean(ent_u)))
                    dP_list.append(float(np.mean(pur_m) - np.mean(pur_u)))
                res["stage16"][f"{tag}_{loop_name}_{idx+1}_{terr}_{base_ax6}"] = {
                    "dS_mean_over_seeds": float(np.mean(dS_list)),
                    "dP_mean_over_seeds": float(np.mean(dP_list)),
                    "dS_min_over_seeds": float(np.min(dS_list)),
                    "dS_max_over_seeds": float(np.max(dS_list)),
                }

    # ---- axis0 AB: trajectory metrics for all SEQs × FWD/REV × sign × init ----
    for sign, tag in [(+1,"T1"),(-1,"T2")]:
        for init_mode in ["GINIBRE","BELL"]:
            for direction in ["FWD","REV"]:
                for seq_name, seq in SEQS.items():
                    MI_list = []; lam_list = []; s_list = []; neg_list = []
                    for s in seeds:
                        rng = np.random.default_rng(5000 + s)
                        r = run_axis0_ab_suite(
                            rng, seq=seq, direction=direction, axis3_sign=sign,
                            init_mode=init_mode, trials=axis0_trials, cycles=axis0_cycles,
                            theta=theta, n_vec=n_vec, tparams_ab=tparams_ab, entangle_reps=entangle_reps
                        )
                        MI_list.append(r["MI_traj_mean"])
                        lam_list.append(r["MI_lambda_fit"])
                        s_list.append(r["SAgB_traj_mean"])
                        neg_list.append(r["SAgB_neg_frac_traj"])
                    res["axis0_ab"][f"{tag}_{init_mode}_{direction}_{seq_name}"] = {
                        "MI_traj_mean": float(np.mean(MI_list)),
                        "MI_lambda_fit": float(np.mean(lam_list)),
                        "SAgB_traj_mean": float(np.mean(s_list)),
                        "SAgB_neg_frac_traj": float(np.mean(neg_list)),
                    }

    raw = json.dumps(res, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_mega_axis0_ab_stage16_axis6.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_MEGA_AXIS0_AB_AND_STAGE16_AXIS6")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")

    # compact metrics: stage16 deltas + axis0 deltas vs SEQ01
    for k,v in res["stage16"].items():
        lines.append(f"METRIC: {k}_dS={v['dS_mean_over_seeds']}")
        lines.append(f"METRIC: {k}_dP={v['dP_mean_over_seeds']}")

    for tag in ["T1","T2"]:
        for init_mode in ["GINIBRE","BELL"]:
            for direction in ["FWD","REV"]:
                base = res["axis0_ab"][f"{tag}_{init_mode}_{direction}_SEQ01"]
                for seq_name in ["SEQ02","SEQ03","SEQ04"]:
                    other = res["axis0_ab"][f"{tag}_{init_mode}_{direction}_{seq_name}"]
                    lines.append(f"METRIC: {tag}_{init_mode}_{direction}_{seq_name}_dMI={other['MI_traj_mean']-base['MI_traj_mean']}")
                    lines.append(f"METRIC: {tag}_{init_mode}_{direction}_{seq_name}_dLam={other['MI_lambda_fit']-base['MI_lambda_fit']}")
                    lines.append(f"METRIC: {tag}_{init_mode}_{direction}_{seq_name}_dSAgB={other['SAgB_traj_mean']-base['SAgB_traj_mean']}")
                    lines.append(f"METRIC: {tag}_{init_mode}_{direction}_{seq_name}_dNegFrac={other['SAgB_neg_frac_traj']-base['SAgB_neg_frac_traj']}")

    lines.append("EVIDENCE_SIGNAL S_SIM_MEGA_AXIS0_AB_AND_STAGE16_AXIS6 CORR E_SIM_MEGA_AXIS0_AB_AND_STAGE16_AXIS6")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_mega_axis0_ab_stage16_axis6.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()