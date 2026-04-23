#!/usr/bin/env python3
"""
run_axis4_sims.py
Creates:
  - results_<SIM_ID>.json for 4 SIM_IDs
  - sim_evidence_pack.txt with 4 SIM_EVIDENCE v1 blocks back-to-back

Edits you may want:
  - axis3_sign: +1 for Type-1, -1 for Type-2
  - cycles, num_states
  - terrain params gamma/p/q
"""

from __future__ import annotations
import json, hashlib, os
from dataclasses import dataclass
from typing import Dict, List, Tuple
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

# ---------- QIT basics ----------
I = np.array([[1,0],[0,1]], dtype=complex)
X = np.array([[0,1],[1,0]], dtype=complex)
Y = np.array([[0,-1j],[1j,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)

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

# ---------- Terrains as CPTP maps ----------
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

# ---------- Axis-4 concrete instantiation ----------
# polarity + : contract-first => CPTP then pinching
# polarity - : redistribute-first => unitary then CPTP

def pinch_Z(rho: np.ndarray) -> np.ndarray:
    out = np.array([[rho[0,0], 0],[0, rho[1,1]]], dtype=complex)
    out = out / np.trace(out)
    return out

@dataclass
class SimConfig:
    sim_id: str
    seq: List[str]
    evidence_token: str

def run_one(sim: SimConfig,
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
            rho1 = apply_kraus(rho, Ks)
            rho2 = pinch_Z(rho1)
            return rho2
        else:
            rho1 = apply_unitary(rho, U)
            rho2 = apply_kraus(rho1, Ks)
            return rho2

    def run_pol(polarity: int) -> Dict[str, float]:
        ents, purs = [], []
        for _ in range(num_states):
            rho = random_density(rng)
            for _c in range(cycles):
                for t in sim.seq:
                    rho = step(rho, t, polarity)
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

    plus = run_pol(+1)
    minus = run_pol(-1)

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
        "polarity_plus": plus,
        "polarity_minus": minus,
    }

def sim_evidence_block(sim_id: str, token: str, code_hash: str, out_hash: str, metrics: Dict[str, float]) -> str:
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append(f"SIM_ID: {sim_id}")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for k, v in metrics.items():
        lines.append(f"METRIC: {k}={v}")
    lines.append(f"EVIDENCE_SIGNAL {sim_id} CORR {token}")
    lines.append("END SIM_EVIDENCE v1")
    return "\n".join(lines)

def main():
    sims = [
        SimConfig("S_SIM_AXIS4_SEQ01_P03", ["Se","Ne","Ni","Si"], "E_SIM_AXIS4_SEQ01_P03"),
        SimConfig("S_SIM_AXIS4_SEQ02_P03", ["Se","Si","Ni","Ne"], "E_SIM_AXIS4_SEQ02_P03"),
        SimConfig("S_SIM_AXIS4_SEQ03_P03", ["Se","Ne","Si","Ni"], "E_SIM_AXIS4_SEQ03_P03"),
        SimConfig("S_SIM_AXIS4_SEQ04_P03", ["Se","Si","Ne","Ni"], "E_SIM_AXIS4_SEQ04_P03"),
    ]

    # --- edit knobs here ---
    seed = 0
    num_states = 256
    cycles = 64
    axis3_sign = +1   # +1 Type-1, -1 Type-2
    theta = 0.07
    n_vec = (0.3, 0.4, 0.866025403784)
    terrain_params = {"gamma": 0.12, "p": 0.08, "q": 0.10}
    # -----------------------

    code_hash = sha256_file(os.path.abspath(__file__))

    evidence_blocks = []

    for sim in sims:
        res = run_one(sim, seed, num_states, cycles, axis3_sign, theta, n_vec, terrain_params)
        raw = json.dumps(res, indent=2, sort_keys=True).encode("utf-8")
        out_hash = sha256_bytes(raw)

        out_json = f"results_{sim.sim_id}.json"
        with open(out_json, "wb") as f:
            f.write(raw)

        metrics = {}
        for k, v in res["polarity_plus"].items():
            metrics[f"plus_{k}"] = v
        for k, v in res["polarity_minus"].items():
            metrics[f"minus_{k}"] = v

        evidence_blocks.append(sim_evidence_block(sim.sim_id, sim.evidence_token, code_hash, out_hash, metrics))

    pack = "\n\n".join(evidence_blocks) + "\n"
    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write(pack)

    print("DONE: wrote results_*.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()
