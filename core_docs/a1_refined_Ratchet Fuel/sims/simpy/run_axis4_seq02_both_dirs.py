#!/usr/bin/env python3
# run_axis4_seq02_both_dirs.py
# Writes sim_evidence_pack.txt containing 2 SIM_EVIDENCE blocks:
#   S_SIM_AXIS4_SEQ02_FWD  token E_SIM_AXIS4_SEQ02_FWD
#   S_SIM_AXIS4_SEQ02_REV  token E_SIM_AXIS4_SEQ02_REV

from __future__ import annotations
import json, hashlib, os
from dataclasses import dataclass
from typing import Dict, List, Tuple
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

def apply_kraus(rho: np.ndarray, Ks: List[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    out = out / np.trace(out)
    return out

def terrain_Se(gamma: float) -> List[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def terrain_Ne(p: float) -> List[np.ndarray]:
    K0 = np.sqrt(1-p) * I
    K1 = np.sqrt(p) * X
    return [K0, K1]

def terrain_Ni(q: float) -> List[np.ndarray]:
    K0 = np.sqrt(1-q) * I
    K1 = np.sqrt(q) * Z
    return [K0, K1]

def terrain_Si() -> List[np.ndarray]:
    return [I]

TERRAIN_KRAUS = {
    "Se": lambda params: terrain_Se(params["gamma"]),
    "Ne": lambda params: terrain_Ne(params["p"]),
    "Ni": lambda params: terrain_Ni(params["q"]),
    "Si": lambda params: terrain_Si(),
}

def pinch_Z(rho: np.ndarray) -> np.ndarray:
    out = np.array([[rho[0,0], 0],[0, rho[1,1]]], dtype=complex)
    out = out / np.trace(out)
    return out

def run_sequence(seq: List[str], *, seed: int, num_states: int, cycles: int, axis3_sign: int,
                 theta: float, n_vec: Tuple[float,float,float], params: Dict[str,float],
                 polarity: int) -> Dict[str,float]:
    rng = np.random.default_rng(seed)
    n = np.array(n_vec, dtype=float)
    U = unitary_from_axis(n, theta, axis3_sign)

    def step(rho: np.ndarray, terrain: str) -> np.ndarray:
        Ks = TERRAIN_KRAUS[terrain](params)
        if polarity == +1:
            rho1 = apply_kraus(rho, Ks)
            return pinch_Z(rho1)
        else:
            rho1 = apply_unitary(rho, U)
            return apply_kraus(rho1, Ks)

    ents, purs = [], []
    for _ in range(num_states):
        rho = random_density(rng)
        for _ in range(cycles):
            for t in seq:
                rho = step(rho, t)
        ents.append(vn_entropy(rho))
        purs.append(purity(rho))
    ents = np.array(ents, float)
    purs = np.array(purs, float)
    return {
        "vn_entropy_mean": float(ents.mean()),
        "vn_entropy_min": float(ents.min()),
        "vn_entropy_max": float(ents.max()),
        "purity_mean": float(purs.mean()),
        "purity_min": float(purs.min()),
        "purity_max": float(purs.max()),
    }

def sim_evidence(sim_id: str, token: str, code_hash: str, out_hash: str, metrics: Dict[str,float]) -> str:
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

def main():
    # fixed SEQ02 forward and reverse
    seq_fwd = ["Se","Si","Ni","Ne"]
    seq_rev = list(reversed(seq_fwd))  # ["Ne","Ni","Si","Se"]

    # parameters (edit in one place if needed)
    seed = 0
    num_states = 256
    cycles = 64
    axis3_sign = +1
    theta = 0.07
    n_vec = (0.3, 0.4, 0.866025403784)
    params = {"gamma": 0.12, "p": 0.08, "q": 0.10}

    script_path = os.path.abspath(__file__)
    code_hash = sha256_file(script_path)

    # run both polarities for each direction and flatten metrics with prefixes
    res = {
        "sim_id_fwd": "S_SIM_AXIS4_SEQ02_FWD",
        "sim_id_rev": "S_SIM_AXIS4_SEQ02_REV",
        "sequence_fwd": seq_fwd,
        "sequence_rev": seq_rev,
        "seed": seed, "num_states": num_states, "cycles": cycles,
        "axis3_sign": axis3_sign, "theta": theta, "n_vec": list(n_vec),
        "terrain_params": dict(params),
        "fwd_plus": run_sequence(seq_fwd, seed=seed, num_states=num_states, cycles=cycles, axis3_sign=axis3_sign, theta=theta, n_vec=n_vec, params=params, polarity=+1),
        "fwd_minus": run_sequence(seq_fwd, seed=seed, num_states=num_states, cycles=cycles, axis3_sign=axis3_sign, theta=theta, n_vec=n_vec, params=params, polarity=-1),
        "rev_plus": run_sequence(seq_rev, seed=seed, num_states=num_states, cycles=cycles, axis3_sign=axis3_sign, theta=theta, n_vec=n_vec, params=params, polarity=+1),
        "rev_minus": run_sequence(seq_rev, seed=seed, num_states=num_states, cycles=cycles, axis3_sign=axis3_sign, theta=theta, n_vec=n_vec, params=params, polarity=-1),
    }

    raw = json.dumps(res, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)

    with open("results_axis4_seq02_both_dirs.json", "wb") as f:
        f.write(raw)

    # evidence for fwd and rev (include both polarity metrics in each evidence block)
    metrics_fwd = {f"plus_{k}": v for k,v in res["fwd_plus"].items()}
    metrics_fwd.update({f"minus_{k}": v for k,v in res["fwd_minus"].items()})

    metrics_rev = {f"plus_{k}": v for k,v in res["rev_plus"].items()}
    metrics_rev.update({f"minus_{k}": v for k,v in res["rev_minus"].items()})

    ev1 = sim_evidence("S_SIM_AXIS4_SEQ02_FWD", "E_SIM_AXIS4_SEQ02_FWD", code_hash, out_hash, metrics_fwd)
    ev2 = sim_evidence("S_SIM_AXIS4_SEQ02_REV", "E_SIM_AXIS4_SEQ02_REV", code_hash, out_hash, metrics_rev)

    pack = ev1 + "\n\n" + ev2 + "\n"
    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write(pack)

    print("DONE: wrote results_axis4_seq02_both_dirs.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()
