#!/usr/bin/env python3
# run_axis0_traj_corr_metrics.py
# Outputs:
#   results_axis0_traj_corr_metrics.json
#   sim_evidence_pack.txt  (1 SIM_EVIDENCE block for S_SIM_AXIS0_TRAJ_CORR_METRICS)

from __future__ import annotations
import json, hashlib, os
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

# ---------- Pauli ----------
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
    rho = rho / np.trace(rho)
    return rho

def bell_seed_state(rng: np.random.Generator) -> np.ndarray:
    # |Phi+> = (|00>+|11>)/sqrt(2)
    phi = np.array([1,0,0,1], dtype=complex) / np.sqrt(2)
    rho = np.outer(phi, phi.conj())
    # local scramble (keeps entanglement but avoids basis lock)
    a = rng.uniform(0, 2*np.pi)
    b = rng.uniform(0, 2*np.pi)
    UA = expm_2x2(-1j * a * Z)
    UB = expm_2x2(-1j * b * X)
    rho = (np.kron(UA, I2) @ rho @ np.kron(UA, I2).conj().T) / np.trace(rho)
    rho = (np.kron(I2, UB) @ rho @ np.kron(I2, UB).conj().T) / np.trace(rho)
    return rho

# ---------- AB entangler (fixed) ----------
CNOT = np.array([
    [1,0,0,0],
    [0,1,0,0],
    [0,0,0,1],
    [0,0,1,0],
], dtype=complex)

def apply_unitary_A(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UA = np.kron(U, I2)
    out = UA @ rhoAB @ UA.conj().T
    return out / np.trace(out)

def apply_unitary_AB(rhoAB: np.ndarray, UAB: np.ndarray) -> np.ndarray:
    out = UAB @ rhoAB @ UAB.conj().T
    return out / np.trace(out)

def apply_kraus_A(rhoAB: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4,4), dtype=complex)
    for K in Ks:
        KA = np.kron(K, I2)
        out += KA @ rhoAB @ KA.conj().T
    return out / np.trace(out)

# ---------- terrain CPTP maps on A ----------
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
    "Se": lambda params: terrain_Se(params["gamma"]),
    "Ne": lambda params: terrain_Ne(params["p"]),
    "Ni": lambda params: terrain_Ni(params["q"]),
    "Si": lambda params: terrain_Si(),
}

def fit_lambda_from_series(x: np.ndarray, y: np.ndarray) -> float:
    # fit log(y) = a + b x on y>0, return lambda = -b
    m = (y > 0.0)
    if np.sum(m) < 2:
        return float("nan")
    xx = x[m]
    yy = np.log(y[m])
    A = np.vstack([np.ones_like(xx), xx]).T
    coef, *_ = np.linalg.lstsq(A, yy, rcond=None)
    b = coef[1]
    return float(-b)

def run_branch(seq: list[str], *, seed: int, trials: int, cycles: int,
               axis3_sign: int, theta: float, n_vec: tuple[float,float,float],
               params: dict, entangle_reps: int, init_mode: str) -> dict:
    rng = np.random.default_rng(seed)
    U = unitary_from_axis(np.array(n_vec,float), theta, axis3_sign)

    # time series tracked after each outer cycle (not each terrain)
    MI_ts = np.zeros((trials, cycles+1), float)
    SAgB_ts = np.zeros((trials, cycles+1), float)

    for t in range(trials):
        rho = bell_seed_state(rng) if init_mode == "BELL" else ginibre_density(4, rng)
        mi0, s0 = mi_and_sAgB(rho)
        MI_ts[t,0] = mi0
        SAgB_ts[t,0] = s0

        for c in range(1, cycles+1):
            # one "outer cycle" = apply the full terrain sequence once
            for terr in seq:
                Ks = TERRAIN[terr](params)
                rho = apply_unitary_A(rho, U)
                rho = apply_kraus_A(rho, Ks)
                for _k in range(entangle_reps):
                    rho = apply_unitary_AB(rho, CNOT)

            mi, sAgB = mi_and_sAgB(rho)
            MI_ts[t,c] = mi
            SAgB_ts[t,c] = sAgB

    # aggregate trajectory functionals
    MI_mean_over_t = float(MI_ts.mean())
    MI_final_mean  = float(MI_ts[:,-1].mean())
    MI_init_mean   = float(MI_ts[:,0].mean())

    SAgB_mean_over_t = float(SAgB_ts.mean())
    SAgB_final_mean  = float(SAgB_ts[:,-1].mean())
    SAgB_init_mean   = float(SAgB_ts[:,0].mean())

    # fit lambda on mean MI(t)
    tgrid = np.arange(cycles+1, dtype=float)
    MI_mean_series = MI_ts.mean(axis=0)
    lam = fit_lambda_from_series(tgrid, MI_mean_series)

    # negativity incidence over whole trajectory (not just final)
    neg_frac_traj = float(np.mean((SAgB_ts < 0.0).astype(float)))

    return {
        "MI_traj_mean": MI_mean_over_t,
        "MI_init_mean": MI_init_mean,
        "MI_final_mean": MI_final_mean,
        "MI_lambda_fit": lam,
        "SAgB_traj_mean": SAgB_mean_over_t,
        "SAgB_init_mean": SAgB_init_mean,
        "SAgB_final_mean": SAgB_final_mean,
        "SAgB_neg_frac_traj": neg_frac_traj,
    }

def main():
    # branches: SEQ01 vs SEQ02
    SEQ01 = ["Se","Ne","Ni","Si"]
    SEQ02 = ["Se","Si","Ni","Ne"]

    # settings aligned with your harness
    seed = 0
    trials = 256
    cycles = 64
    axis3_sign = +1
    theta = 0.07
    n_vec = (0.3, 0.4, 0.866025403784)

    # noise (moderate) + AB coupling
    params = {"gamma": 0.02, "p": 0.02, "q": 0.02}
    entangle_reps = 1

    # run both init modes (GINIBRE and BELL) in one sim (richer evidence)
    out = {
        "seed": seed,
        "trials": trials,
        "cycles": cycles,
        "axis3_sign": axis3_sign,
        "theta": theta,
        "n_vec": list(n_vec),
        "terrain_params": dict(params),
        "entangle_reps": entangle_reps,
        "SEQ01": SEQ01,
        "SEQ02": SEQ02,
    }

    for init_mode in ["GINIBRE", "BELL"]:
        r1 = run_branch(SEQ01, seed=seed, trials=trials, cycles=cycles, axis3_sign=axis3_sign,
                        theta=theta, n_vec=n_vec, params=params, entangle_reps=entangle_reps, init_mode=init_mode)
        r2 = run_branch(SEQ02, seed=seed, trials=trials, cycles=cycles, axis3_sign=axis3_sign,
                        theta=theta, n_vec=n_vec, params=params, entangle_reps=entangle_reps, init_mode=init_mode)

        out[f"{init_mode}_SEQ01"] = r1
        out[f"{init_mode}_SEQ02"] = r2
        out[f"{init_mode}_delta_MI_traj_mean_SEQ02_minus_SEQ01"] = float(r2["MI_traj_mean"] - r1["MI_traj_mean"])
        out[f"{init_mode}_delta_MI_lambda_fit_SEQ02_minus_SEQ01"] = float(r2["MI_lambda_fit"] - r1["MI_lambda_fit"])
        out[f"{init_mode}_delta_SAgB_traj_mean_SEQ02_minus_SEQ01"] = float(r2["SAgB_traj_mean"] - r1["SAgB_traj_mean"])
        out[f"{init_mode}_delta_SAgB_neg_frac_traj_SEQ02_minus_SEQ01"] = float(r2["SAgB_neg_frac_traj"] - r1["SAgB_neg_frac_traj"])

    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)

    with open("results_axis0_traj_corr_metrics.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_AXIS0_TRAJ_CORR_METRICS")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")

    # emit compact metrics only (branch deltas + main scalars)
    for init_mode in ["GINIBRE", "BELL"]:
        for k,v in out[f"{init_mode}_SEQ01"].items():
            lines.append(f"METRIC: {init_mode}_SEQ01_{k}={v}")
        for k,v in out[f"{init_mode}_SEQ02"].items():
            lines.append(f"METRIC: {init_mode}_SEQ02_{k}={v}")

        lines.append(f"METRIC: {init_mode}_delta_MI_traj_mean_SEQ02_minus_SEQ01={out[f'{init_mode}_delta_MI_traj_mean_SEQ02_minus_SEQ01']}")
        lines.append(f"METRIC: {init_mode}_delta_MI_lambda_fit_SEQ02_minus_SEQ01={out[f'{init_mode}_delta_MI_lambda_fit_SEQ02_minus_SEQ01']}")
        lines.append(f"METRIC: {init_mode}_delta_SAgB_traj_mean_SEQ02_minus_SEQ01={out[f'{init_mode}_delta_SAgB_traj_mean_SEQ02_minus_SEQ01']}")
        lines.append(f"METRIC: {init_mode}_delta_SAgB_neg_frac_traj_SEQ02_minus_SEQ01={out[f'{init_mode}_delta_SAgB_neg_frac_traj_SEQ02_minus_SEQ01']}")

    lines.append("EVIDENCE_SIGNAL S_SIM_AXIS0_TRAJ_CORR_METRICS CORR E_SIM_AXIS0_TRAJ_CORR_METRICS")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_axis0_traj_corr_metrics.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()
