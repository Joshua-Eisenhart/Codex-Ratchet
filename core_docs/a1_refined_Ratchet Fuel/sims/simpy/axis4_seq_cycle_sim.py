#!/usr/bin/env python3
"""
run_axis4_sims.py

Produces:
- results_<SIM_ID>.json
- evidence_<SIM_ID>.txt  (a SIM_EVIDENCE v1 block ready to paste into Thread B)

This is an unofficial concrete instantiation of your Axis-4 objects:
- terrains: Se/Ne/Ni/Si as CPTP maps (Kraus)
- cycle: apply terrain sequence repeatedly
- polarity: run BOTH (+) and (-) passes per SIM_ID and report both metric sets
"""

from __future__ import annotations
import json, hashlib, os
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np

# -------------------------
# Basic QIT helpers
# -------------------------

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def is_density(rho: np.ndarray, tol: float = 1e-10) -> bool:
    if rho.shape != (2, 2): return False
    if not np.allclose(rho, rho.conj().T, atol=tol): return False
    tr = np.trace(rho).real
    if abs(tr - 1.0) > 1e-8: return False
    # eigenvalues >= 0
    w = np.linalg.eigvalsh(rho)
    return np.all(w >= -1e-9)

def random_density(rng: np.random.Generator) -> np.ndarray:
    # Ginibre -> rho = A A† / Tr
    a = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    rho = a @ a.conj().T
    rho = rho / np.trace(rho)
    return rho

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho)
    w = np.clip(w.real, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())

def purity(rho: np.ndarray) -> float:
    return float(np.trace(rho @ rho).real)

# Pauli matrices
I = np.array([[1,0],[0,1]], dtype=complex)
X = np.array([[0,1],[1,0]], dtype=complex)
Y = np.array([[0,-1j],[1j,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)

def unitary_from_axis(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    # U = exp(-i * sign * theta * (n·sigma))
    n = n / np.linalg.norm(n)
    H = n[0]*X + n[1]*Y + n[2]*Z
    return scipy_expm(-1j * sign * theta * H)

def scipy_expm(a: np.ndarray) -> np.ndarray:
    # small 2x2 expm, stable enough
    w, v = np.linalg.eig(a)
    return (v @ np.diag(np.exp(w)) @ np.linalg.inv(v)).astype(complex)

def apply_unitary(rho: np.ndarray, U: np.ndarray) -> np.ndarray:
    return U @ rho @ U.conj().T

def apply_kraus(rho: np.ndarray, Ks: List[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    # numerical renorm
    out = out / np.trace(out)
    return out

# -------------------------
# Terrains as CPTP maps
# -------------------------

def terrain_Se(gamma: float) -> List[np.ndarray]:
    # amplitude damping
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def terrain_Ne(p: float) -> List[np.ndarray]:
    # bit flip
    K0 = np.sqrt(1-p) * I
    K1 = np.sqrt(p) * X
    return [K0, K1]

def terrain_Ni(q: float) -> List[np.ndarray]:
    # phase flip
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

# -------------------------
# Axis-4 composites (concrete instantiation)
# -------------------------
# We need two different composites for polarity.
# Here we instantiate:
#   polarity + : apply terrain CPTP then a pinching projection (contract early)
#   polarity - : apply unitary then terrain CPTP (redistribute before contraction)
# This matches the abstract “contract vs redistribute” ordering without using Ti/Te/Fi/Fe as primitives.

def pinch_Z(rho: np.ndarray) -> np.ndarray:
    # projective pinching in Z basis (kills off-diagonals)
    out = np.array([[rho[0,0], 0],[0, rho[1,1]]], dtype=complex)
    out = out / np.trace(out)
    return out

@dataclass
class SimConfig:
    sim_id: str
    seq: List[str]
    evidence_token: str

def run_sim_one(sim: SimConfig, *,
                seed: int,
                num_states: int,
                cycles: int,
                axis3_sign: int,
                theta: float,
                n_vec: Tuple[float,float,float],
                terrain_params: Dict[str, float]) -> Dict:
    rng = np.random.default_rng(seed)
    n = np.array(n_vec, dtype=float)
    U = unitary_from_axis(n, theta, axis3_sign)

    def step(rho: np.ndarray, terrain: str, polarity: int) -> np.ndarray:
        Ks = TERRAIN_KRAUS[terrain](terrain_params)
        if polarity == +1:
            # contract early: CPTP then pinch
            rho1 = apply_kraus(rho, Ks)
            rho2 = pinch_Z(rho1)
            return rho2
        else:
            # redistribute early: unitary then CPTP
            rho1 = apply_unitary(rho, U)
            rho2 = apply_kraus(rho1, Ks)
            return rho2

    def run_polarity(polarity: int) -> Dict[str, float]:
        ents, purs = [], []
        for _ in range(num_states):
            rho = random_density(rng)
            assert is_density(rho)
            for _c in range(cycles):
                for t in sim.seq:
                    rho = step(rho, t, polarity)
            ents.append(vn_entropy(rho))
            purs.append(purity(rho))
        ents = np.array(ents, dtype=float)
        purs = np.array(purs, dtype=float)
        return {
            "vn_entropy_mean": float(ents.mean()),
            "vn_entropy_min": float(ents.min()),
            "vn_entropy_max": float(ents.max()),
            "purity_mean": float(purs.mean()),
            "purity_min": float(purs.min()),
            "purity_max": float(purs.max()),
        }

    out_plus = run_polarity(+1)
    out_minus = run_polarity(-1)

    return {
        "sim_id": sim.sim_id,
        "sequence": sim.seq,
        "seed": seed,
        "num_states": num_states,
        "cycles": cycles,
        "axis3_sign": axis3_sign,
        "theta": theta,
        "n_vec": list(n_vec),
        "terrain_params": dict(terrain_params),
        "polarity_plus": out_plus,
        "polarity_minus": out_minus,
    }

def write_evidence(sim_id: str, token: str, code_hash: str, out_hash: str, metrics: Dict[str, float]) -> str:
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append(f"SIM_ID: {sim_id}")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for k, v in metrics.items():
        lines.append(f"METRIC: {k}={v}")
    lines.append(f"EVIDENCE_SIGNAL {sim_id} CORR {token}")
    lines.append("END SIM_EVIDENCE v1")
    return "\n".join(lines) + "\n"

def main():
    # Map SIM_ID -> SEQ (matches your ratchet SEQ definitions)
    sims = [
        SimConfig("S_SIM_AXIS4_SEQ01_P03", ["Se","Ne","Ni","Si"], "E_SIM_AXIS4_SEQ01_P03"),
        SimConfig("S_SIM_AXIS4_SEQ02_P03", ["Se","Si","Ni","Ne"], "E_SIM_AXIS4_SEQ02_P03"),
        SimConfig("S_SIM_AXIS4_SEQ03_P03", ["Se","Ne","Si","Ni"], "E_SIM_AXIS4_SEQ03_P03"),
        SimConfig("S_SIM_AXIS4_SEQ04_P03", ["Se","Si","Ne","Ni"], "E_SIM_AXIS4_SEQ04_P03"),
    ]

    # Parameters (edit if you want)
    seed = 0
    num_states = 256
    cycles = 64
    axis3_sign = +1   # Type-1 (+), use -1 for Type-2
    theta = 0.07
    n_vec = (0.3, 0.4, 0.866025403784)  # unit vector-ish
    terrain_params = {"gamma": 0.12, "p": 0.08, "q": 0.10}

    script_path = os.path.abspath(__file__)
    code_hash = sha256_file(script_path)

    for sim in sims:
        res = run_sim_one(sim,
                          seed=seed,
                          num_states=num_states,
                          cycles=cycles,
                          axis3_sign=axis3_sign,
                          theta=theta,
                          n_vec=n_vec,
                          terrain_params=terrain_params)

        # write json
        out_json = f"results_{sim.sim_id}.json"
        raw = json.dumps(res, indent=2, sort_keys=True).encode("utf-8")
        with open(out_json, "wb") as f:
            f.write(raw)
        out_hash = sha256_bytes(raw)

        # flatten metrics (include both polarities with prefixes)
        m = {}
        for k, v in res["polarity_plus"].items():
            m[f"plus_{k}"] = v
        for k, v in res["polarity_minus"].items():
            m[f"minus_{k}"] = v

        ev = write_evidence(sim.sim_id, sim.evidence_token, code_hash, out_hash, m)
        out_txt = f"evidence_{sim.sim_id}.txt"
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(ev)

    print("DONE")
    print("Generated results_*.json and evidence_*.txt for four SIM_IDs.")

if __name__ == "__main__":
    main()
