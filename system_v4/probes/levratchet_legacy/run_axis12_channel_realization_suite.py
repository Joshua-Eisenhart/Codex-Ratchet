#!/usr/bin/env python3
# run_axis12_channel_realization_suite.py
# Output:
#   results_axis12_channel_realization_suite.json
#   sim_evidence_pack_axis12_channel_realization_suite.txt

from __future__ import annotations
import json, hashlib, os
import numpy as np

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
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

def apply_kraus(rho: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    return out / np.trace(out)

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w*np.log(w)).sum())

def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))

def ginibre_density_2(rng: np.random.Generator) -> np.ndarray:
    G = (rng.normal(size=(2,2)) + 1j*rng.normal(size=(2,2))) / np.sqrt(2.0)
    rho = G @ G.conj().T
    return rho / np.trace(rho)

# Concrete channel representatives for the 4 topologies (same family you already use)
def Se(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(max(1-gamma,0.0))]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def Ne(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(max(1-p,0.0))*I2
    K1 = np.sqrt(p)*X
    return [K0, K1]

def Ni(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(max(1-q,0.0))*I2
    K1 = np.sqrt(q)*Z
    return [K0, K1]

def Si() -> list[np.ndarray]:
    return [I2]

TERR = {
    "Se": lambda prm: Se(prm["gamma"]),
    "Ne": lambda prm: Ne(prm["p"]),
    "Ni": lambda prm: Ni(prm["q"]),
    "Si": lambda prm: Si(),
}

SEQ = {
    "SEQ01": ["Se","Ne","Ni","Si"],
    "SEQ02": ["Se","Si","Ni","Ne"],
    "SEQ03": ["Se","Ne","Si","Ni"],
    "SEQ04": ["Se","Si","Ne","Ni"],
}

# Axis-1/2 “edge constraints” evaluator (same spirit as your existing counter sim)
def has_edge(seq: list[str], a: str, b: str) -> int:
    n = len(seq)
    for i in range(n):
        x = seq[i]; y = seq[(i+1)%n]
        if (x==a and y==b) or (x==b and y==a):
            return 1
    return 0

def main():
    seed = 0
    rng = np.random.default_rng(seed)

    # same parameters style as your other runs
    params = {"gamma": 0.12, "p": 0.08, "q": 0.10}
    theta = 0.07
    n_vec = np.array([0.3, 0.4, 0.866025403784], float)

    cycles = 64
    states = 256

    out = {
        "seed": seed,
        "cycles": cycles,
        "states": states,
        "theta": theta,
        "n_vec": [float(x) for x in n_vec.tolist()],
        "terrain_params": dict(params),
        "seqs": SEQ,
        "axis12_edges": {},
        "results": {},
    }

    # Axis-12 edge booleans (SENI / NESI) per sequence
    for name, seq in SEQ.items():
        out["axis12_edges"][name] = {
            "SENI": has_edge(seq, "Se", "Ni"),
            "NESI": has_edge(seq, "Ne", "Si"),
        }

    # QIT realization: run each sequence for Axis-3 sign ±1 and measure endpoint S,P
    for axis3_sign in [+1, -1]:
        U = unitary_from_axis(n_vec, theta, axis3_sign)
        for name, seq in SEQ.items():
            S_list=[]; P_list=[]
            for _ in range(states):
                rho = ginibre_density_2(rng)
                for _c in range(cycles):
                    for terr in seq:
                        # unitary transport (Axis-3 sign) then terrain channel
                        rho = (U @ rho @ U.conj().T) / np.trace(rho)
                        rho = apply_kraus(rho, TERR[terr](params))
                S_list.append(vn_entropy(rho))
                P_list.append(purity(rho))
            out["results"][f"axis3_{axis3_sign}_{name}"] = {
                "vn_entropy_mean": float(np.mean(S_list)),
                "purity_mean": float(np.mean(P_list)),
            }

    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_axis12_channel_realization_suite.json","wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    # Minimal metrics for Thread B (keep it short, but still informative)
    lines=[]
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_AXIS12_CHANNEL_REALIZATION_SUITE")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")

    # Edge flags
    for name in ["SEQ01","SEQ02","SEQ03","SEQ04"]:
        lines.append(f"METRIC: {name}_SENI={out['axis12_edges'][name]['SENI']}")
        lines.append(f"METRIC: {name}_NESI={out['axis12_edges'][name]['NESI']}")

    # Endpoint summaries (Axis-3 +1) for all sequences
    for name in ["SEQ01","SEQ02","SEQ03","SEQ04"]:
        r = out["results"][f"axis3_{+1}_{name}"]
        lines.append(f"METRIC: plus_{name}_S_mean={r['vn_entropy_mean']}")
        lines.append(f"METRIC: plus_{name}_P_mean={r['purity_mean']}")

    # Endpoint summaries (Axis-3 -1) for all sequences
    for name in ["SEQ01","SEQ02","SEQ03","SEQ04"]:
        r = out["results"][f"axis3_{-1}_{name}"]
        lines.append(f"METRIC: minus_{name}_S_mean={r['vn_entropy_mean']}")
        lines.append(f"METRIC: minus_{name}_P_mean={r['purity_mean']}")

    lines.append("EVIDENCE_SIGNAL S_SIM_AXIS12_CHANNEL_REALIZATION_SUITE CORR E_SIM_AXIS12_CHANNEL_REALIZATION_SUITE")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack_axis12_channel_realization_suite.txt","w",encoding="utf-8") as f:
        f.write("\n".join(lines)+"\n")

    print("DONE: wrote results_axis12_channel_realization_suite.json and sim_evidence_pack_axis12_channel_realization_suite.txt")

if __name__ == "__main__":
    main()