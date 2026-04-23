#!/usr/bin/env python3
# run_axis0_boundary_bookkeep_sweep_v2.py
#
# Sweep boundary record bandwidth:
#   REC1: single-body + (Z,Z)
#   REC3: single-body + (X,X),(Y,Y),(Z,Z)
#   REC9: single-body + all (a,b) with a,b in {X,Y,Z}
#
# Outputs:
#   results_axis0_boundary_bookkeep_sweep_v2.json
#   sim_evidence_pack.txt  (1 SIM_EVIDENCE block)

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
PAULI = {"I": I2, "X": X, "Y": Y, "Z": Z}
KEYS = ["I","X","Y","Z"]

def expm_2x2(a: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eig(a)
    return (v @ np.diag(np.exp(w)) @ np.linalg.inv(v)).astype(complex)

def unitary_from_axis(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = np.asarray(n, float)
    n = n / np.linalg.norm(n)
    H = n[0]*X + n[1]*Y + n[2]*Z
    return expm_2x2(-1j * sign * theta * H)

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

CNOT = np.array([[1,0,0,0],
                 [0,1,0,0],
                 [0,0,0,1],
                 [0,0,1,0]], dtype=complex)

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())

def trA(rhoAB: np.ndarray) -> np.ndarray:
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

def trB(rhoAB: np.ndarray) -> np.ndarray:
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

def mi_sAgB(rhoAB: np.ndarray) -> tuple[float,float]:
    rhoA = trA(rhoAB)
    rhoB = trB(rhoAB)
    sab = vn_entropy(rhoAB)
    sa  = vn_entropy(rhoA)
    sb  = vn_entropy(rhoB)
    mi = sa + sb - sab
    sAgB = sab - sb
    return float(mi), float(sAgB)

def frob(a: np.ndarray) -> float:
    return float(np.sqrt(np.sum(np.abs(a)**2)).real)

def terrain_Se(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def terrain_Ne(p: float) -> list[np.ndarray]:
    return [np.sqrt(1-p)*I2, np.sqrt(p)*X]

def terrain_Ni(q: float) -> list[np.ndarray]:
    return [np.sqrt(1-q)*I2, np.sqrt(q)*Z]

def terrain_Si() -> list[np.ndarray]:
    return [I2]

TERRAIN = {
    "Se": lambda prm: terrain_Se(prm["gamma"]),
    "Ne": lambda prm: terrain_Ne(prm["p"]),
    "Ni": lambda prm: terrain_Ni(prm["q"]),
    "Si": lambda prm: terrain_Si(),
}

def pauli_coeffs(rhoAB: np.ndarray) -> dict[tuple[str,str], float]:
    out = {}
    for a in KEYS:
        for b in KEYS:
            P = np.kron(PAULI[a], PAULI[b])
            out[(a,b)] = float(np.trace(P @ rhoAB).real)
    return out

def reconstruct(rec: dict[tuple[str,str], float]) -> np.ndarray:
    rho = np.zeros((4,4), dtype=complex)
    for (a,b), val in rec.items():
        rho += val * np.kron(PAULI[a], PAULI[b])
    rho = (1/4) * rho
    w, v = np.linalg.eigh((rho + rho.conj().T)/2)
    w = np.clip(w.real, 0.0, None)
    if w.sum() <= 0:
        rho = np.eye(4, dtype=complex) / 4
    else:
        rho = (v @ np.diag(w) @ v.conj().T)
        rho = rho / np.trace(rho)
    return rho

def record_sets() -> dict[str, set[tuple[str,str]]]:
    single = {("I","I"), ("X","I"),("Y","I"),("Z","I"), ("I","X"),("I","Y"),("I","Z")}
    rec1 = set(single) | {("Z","Z")}
    rec3 = set(single) | {("X","X"),("Y","Y"),("Z","Z")}
    rec9 = set(single)
    for a in ["X","Y","Z"]:
        for b in ["X","Y","Z"]:
            rec9.add((a,b))
    return {"REC1": rec1, "REC3": rec3, "REC9": rec9}

def boundary_record(rhoAB: np.ndarray, keep: set[tuple[str,str]]) -> dict[tuple[str,str], float]:
    c = pauli_coeffs(rhoAB)
    return {k: c[k] for k in keep}

def random_rho4(rng: np.random.Generator) -> np.ndarray:
    M = rng.normal(size=(4,4)) + 1j*rng.normal(size=(4,4))
    rho = M @ M.conj().T
    return rho / np.trace(rho)

def bell_rho(rng: np.random.Generator) -> np.ndarray:
    phi = np.array([1,0,0,1], dtype=complex) / np.sqrt(2)
    rho = np.outer(phi, phi.conj())
    thA = rng.uniform(0, 2*np.pi)
    thB = rng.uniform(0, 2*np.pi)
    UA = expm_2x2(-1j * thA * Z)
    UB = expm_2x2(-1j * thB * X)
    rho = apply_unitary_A(rho, UA)
    UBf = np.kron(I2, UB)
    rho = UBf @ rho @ UBf.conj().T
    return rho / np.trace(rho)

def run_one(seq: list[str], init_kind: str, keep: set[tuple[str,str]],
            *, seed: int, trials: int, cycles: int, axis3_sign: int,
            theta: float, n_vec: tuple[float,float,float], params: dict,
            entangle_reps: int) -> dict:

    rng = np.random.default_rng(seed)
    U = unitary_from_axis(np.array(n_vec,float), theta, axis3_sign)

    dMI = []
    dSAgB = []
    dF = []

    for _ in range(trials):
        rho = bell_rho(rng) if init_kind == "BELL" else random_rho4(rng)

        for _c in range(cycles):
            for terr in seq:
                rho = apply_unitary_A(rho, U)
                rho = apply_kraus_A(rho, TERRAIN[terr](params))
                for _k in range(entangle_reps):
                    rho = apply_unitary_AB(rho, CNOT)

        mi, sagb = mi_sAgB(rho)
        rec = boundary_record(rho, keep)
        rho_hat = reconstruct(rec)
        mi_h, sagb_h = mi_sAgB(rho_hat)

        dMI.append(mi_h - mi)
        dSAgB.append(sagb_h - sagb)
        dF.append(frob(rho_hat - rho))

    dMI = np.array(dMI, float)
    dSAgB = np.array(dSAgB, float)
    dF = np.array(dF, float)
    return {"dMI_mean": float(dMI.mean()), "dSAgB_mean": float(dSAgB.mean()), "frob_err_mean": float(dF.mean())}

def main():
    SEQ01 = ["Se","Ne","Ni","Si"]
    SEQ02 = ["Se","Si","Ni","Ne"]

    seed = 0
    trials = 512
    cycles = 64
    theta = 0.07
    n_vec = (0.3, 0.4, 0.866025403784)
    params = {"gamma": 0.01, "p": 0.01, "q": 0.01}
    entangle_reps = 1

    recs = record_sets()
    out = {
        "seed": seed, "trials": trials, "cycles": cycles,
        "theta": theta, "n_vec": list(n_vec), "terrain_params": dict(params),
        "entangle_reps": entangle_reps,
        "SEQ01": SEQ01, "SEQ02": SEQ02,
        "runs": {}
    }

    for axis3_sign in (+1, -1):
        for init in ("GINIBRE","BELL"):
            for rec_name, keep in recs.items():
                k = f"sign{axis3_sign}_{init}_{rec_name}"
                out["runs"][k] = {
                    "SEQ01": run_one(SEQ01, init, keep, seed=seed, trials=trials, cycles=cycles,
                                    axis3_sign=axis3_sign, theta=theta, n_vec=n_vec, params=params, entangle_reps=entangle_reps),
                    "SEQ02": run_one(SEQ02, init, keep, seed=seed, trials=trials, cycles=cycles,
                                    axis3_sign=axis3_sign, theta=theta, n_vec=n_vec, params=params, entangle_reps=entangle_reps),
                }

    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_axis0_boundary_bookkeep_sweep_v2.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    # Emit compact metrics: SEQ02-SEQ01 deltas for dMI_mean and frob_err_mean per bucket
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_AXIS0_BOUNDARY_BOOKKEEP_SWEEP_V2")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")

    for k, d in out["runs"].items():
        dmi = d["SEQ02"]["dMI_mean"] - d["SEQ01"]["dMI_mean"]
        df  = d["SEQ02"]["frob_err_mean"] - d["SEQ01"]["frob_err_mean"]
        lines.append(f"METRIC: {k}_delta_dMI_mean_SEQ02mSEQ01={dmi}")
        lines.append(f"METRIC: {k}_delta_frob_err_mean_SEQ02mSEQ01={df}")

    lines.append("EVIDENCE_SIGNAL S_SIM_AXIS0_BOUNDARY_BOOKKEEP_SWEEP_V2 CORR E_SIM_AXIS0_BOUNDARY_BOOKKEEP_SWEEP_V2")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_axis0_boundary_bookkeep_sweep_v2.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()