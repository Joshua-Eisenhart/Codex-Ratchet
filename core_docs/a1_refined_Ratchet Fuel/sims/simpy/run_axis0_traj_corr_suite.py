#!/usr/bin/env python3
# run_axis0_traj_corr_suite.py
# Produces:
#   results_axis0_traj_corr_suite.json
#   sim_evidence_pack.txt  (1 SIM_EVIDENCE block for S_SIM_AXIS0_TRAJ_CORR_SUITE)

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
    phi = np.array([1,0,0,1], dtype=complex) / np.sqrt(2)
    rho = np.outer(phi, phi.conj())
    a = rng.uniform(0, 2*np.pi)
    b = rng.uniform(0, 2*np.pi)
    UA = expm_2x2(-1j * a * Z)
    UB = expm_2x2(-1j * b * X)
    rho = (np.kron(UA, I2) @ rho @ np.kron(UA, I2).conj().T) / np.trace(rho)
    rho = (np.kron(I2, UB) @ rho @ np.kron(I2, UB).conj().T) / np.trace(rho)
    return rho

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
    m = (y > 0.0)
    if np.sum(m) < 2:
        return float("nan")
    xx = x[m]
    yy = np.log(y[m])
    A = np.vstack([np.ones_like(xx), xx]).T
    coef, *_ = np.linalg.lstsq(A, yy, rcond=None)
    b = coef[1]
    return float(-b)

def run_case(seq: list[str], axis3_sign: int, init_mode: str, direction: str,
             seed: int, trials: int, cycles: int, theta: float, n_vec: tuple[float,float,float],
             params: dict, entangle_reps: int) -> dict:
    rng = np.random.default_rng(seed)
    U = unitary_from_axis(np.array(n_vec,float), theta, axis3_sign)
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
                Ks = TERRAIN[terr](params)
                rho = apply_unitary_A(rho, U)
                rho = apply_kraus_A(rho, Ks)
                for _k in range(entangle_reps):
                    rho = apply_unitary_AB(rho, CNOT)

            mi, sAgB = mi_and_sAgB(rho)
            MI_ts[t,c] = mi
            SAgB_ts[t,c] = sAgB

    tgrid = np.arange(cycles+1, dtype=float)
    MI_mean_series = MI_ts.mean(axis=0)

    return {
        "MI_traj_mean": float(MI_ts.mean()),
        "MI_init_mean": float(MI_ts[:,0].mean()),
        "MI_final_mean": float(MI_ts[:,-1].mean()),
        "MI_lambda_fit": float(fit_lambda_from_series(tgrid, MI_mean_series)),
        "SAgB_traj_mean": float(SAgB_ts.mean()),
        "SAgB_init_mean": float(SAgB_ts[:,0].mean()),
        "SAgB_final_mean": float(SAgB_ts[:,-1].mean()),
        "SAgB_neg_frac_traj": float(np.mean((SAgB_ts < 0.0).astype(float))),
    }

def main():
    SEQS = {
        "SEQ01": ["Se","Ne","Ni","Si"],
        "SEQ02": ["Se","Si","Ni","Ne"],
        "SEQ03": ["Se","Ne","Si","Ni"],
        "SEQ04": ["Se","Si","Ne","Ni"],
    }

    seed = 0
    trials = 128
    cycles = 64
    theta = 0.07
    n_vec = (0.3, 0.4, 0.866025403784)
    params = {"gamma": 0.02, "p": 0.02, "q": 0.02}
    entangle_reps = 1

    out = {
        "seed": seed,
        "trials": trials,
        "cycles": cycles,
        "theta": theta,
        "n_vec": list(n_vec),
        "terrain_params": dict(params),
        "entangle_reps": entangle_reps,
        "seqs": SEQS,
        "results": {},
    }

    for axis3_sign in [+1, -1]:
        for init_mode in ["GINIBRE", "BELL"]:
            for direction in ["FWD", "REV"]:
                for name, seq in SEQS.items():
                    key = f"sign{axis3_sign}_{init_mode}_{direction}_{name}"
                    out["results"][key] = run_case(
                        seq=seq, axis3_sign=axis3_sign, init_mode=init_mode, direction=direction,
                        seed=seed, trials=trials, cycles=cycles, theta=theta, n_vec=n_vec,
                        params=params, entangle_reps=entangle_reps
                    )

    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_axis0_traj_corr_suite.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    # Evidence block: only deltas relative to SEQ01 to keep it compact
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_AXIS0_TRAJ_CORR_SUITE")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")

    def emit_delta(base_key: str, other_key: str, prefix: str):
        b = out["results"][base_key]
        o = out["results"][other_key]
        lines.append(f"METRIC: {prefix}_dMI_traj_mean={o['MI_traj_mean']-b['MI_traj_mean']}")
        lines.append(f"METRIC: {prefix}_dMI_lambda_fit={o['MI_lambda_fit']-b['MI_lambda_fit']}")
        lines.append(f"METRIC: {prefix}_dSAgB_traj_mean={o['SAgB_traj_mean']-b['SAgB_traj_mean']}")
        lines.append(f"METRIC: {prefix}_dSAgB_neg_frac_traj={o['SAgB_neg_frac_traj']-b['SAgB_neg_frac_traj']}")

    for axis3_sign in [+1, -1]:
        for init_mode in ["GINIBRE", "BELL"]:
            for direction in ["FWD", "REV"]:
                base = f"sign{axis3_sign}_{init_mode}_{direction}_SEQ01"
                for name in ["SEQ02","SEQ03","SEQ04"]:
                    other = f"sign{axis3_sign}_{init_mode}_{direction}_{name}"
                    pref = f"s{axis3_sign}_{init_mode}_{direction}_{name}_minus_SEQ01"
                    emit_delta(base, other, pref)

    lines.append("EVIDENCE_SIGNAL S_SIM_AXIS0_TRAJ_CORR_SUITE CORR E_SIM_AXIS0_TRAJ_CORR_SUITE")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_axis0_traj_corr_suite.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()
