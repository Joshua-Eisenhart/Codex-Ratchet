#!/usr/bin/env python3
# run_terrain8_sign_suite.py
# Produces sim_evidence_pack.txt with 1 SIM_EVIDENCE block for S_SIM_TERRAIN8_SIGN_SUITE

from __future__ import annotations
import json, hashlib, os
import numpy as np

I = np.array([[1,0],[0,1]], dtype=complex)
X = np.array([[0,1],[1,0]], dtype=complex)
Y = np.array([[0,-1j],[1j,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def random_density(rng: np.random.Generator) -> np.ndarray:
    a = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    rho = a @ a.conj().T
    rho = rho / np.trace(rho)
    return rho

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())

def purity(rho: np.ndarray) -> float:
    return float(np.trace(rho @ rho).real)

def expm_2x2(a: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eig(a)
    return (v @ np.diag(np.exp(w)) @ np.linalg.inv(v)).astype(complex)

def unitary_from_axis(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = n / np.linalg.norm(n)
    H = n[0]*X + n[1]*Y + n[2]*Z
    return expm_2x2(-1j * sign * theta * H)

def apply_unitary(rho: np.ndarray, U: np.ndarray) -> np.ndarray:
    out = U @ rho @ U.conj().T
    out = out / np.trace(out)
    return out

def apply_kraus(rho: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    out = out / np.trace(out)
    return out

def terrain_Se(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def terrain_Ne(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-p) * I
    K1 = np.sqrt(p) * X
    return [K0, K1]

def terrain_Ni(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-q) * I
    K1 = np.sqrt(q) * Z
    return [K0, K1]

def terrain_Si() -> list[np.ndarray]:
    return [I]

TERRAIN = {
    "Se": lambda params: terrain_Se(params["gamma"]),
    "Ne": lambda params: terrain_Ne(params["p"]),
    "Ni": lambda params: terrain_Ni(params["q"]),
    "Si": lambda params: terrain_Si(),
}

def main():
    seed = 0
    num_states = 256
    cycles = 64
    theta = 0.07
    n_vec = np.array([0.3, 0.4, 0.866025403784], float)
    params = {"gamma": 0.12, "p": 0.08, "q": 0.10}

    rng = np.random.default_rng(seed)

    metrics = {}
    for sign_label, sign in [("plus", +1), ("minus", -1)]:
        U = unitary_from_axis(n_vec, theta, sign)
        for terr in ["Se","Ne","Ni","Si"]:
            Ks = TERRAIN[terr](params)
            ents, purs = [], []
            for _ in range(num_states):
                rho = random_density(rng)
                for _c in range(cycles):
                    rho = apply_unitary(rho, U)
                    rho = apply_kraus(rho, Ks)
                ents.append(vn_entropy(rho))
                purs.append(purity(rho))
            ents = np.array(ents, float)
            purs = np.array(purs, float)
            metrics[f"{sign_label}_{terr}_entropy_mean"] = float(ents.mean())
            metrics[f"{sign_label}_{terr}_purity_mean"] = float(purs.mean())

    out_obj = {"metrics": metrics}
    raw = json.dumps(out_obj, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)

    with open("results_terrain8_sign_suite.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_TERRAIN8_SIGN_SUITE")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for k,v in metrics.items():
        lines.append(f"METRIC: {k}={v}")
    lines.append("EVIDENCE_SIGNAL S_SIM_TERRAIN8_SIGN_SUITE CORR E_SIM_TERRAIN8_SIGN_SUITE")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_terrain8_sign_suite.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()
