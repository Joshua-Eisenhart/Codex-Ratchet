#!/usr/bin/env python3
# run_oprole8_left_right_suite.py
# Produces sim_evidence_pack.txt with 1 SIM_EVIDENCE block for S_SIM_OPROLE8_LEFT_RIGHT_SUITE
# This suite uses 4 fixed operator matrices for roles R1..R4 as a harness (not claiming final Ti/Te/Fi/Fe).

from __future__ import annotations
import json, hashlib, os
import numpy as np

I = np.array([[1,0],[0,1]], dtype=complex)
X = np.array([[0,1],[1,0]], dtype=complex)
Y = np.array([[0,-1j],[1j,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)
H = (1/np.sqrt(2))*np.array([[1,1],[1,-1]], dtype=complex)

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

def main():
    seed = 0
    trials = 256
    rng = np.random.default_rng(seed)

    # role harness (placeholder matrices)
    OPS = {
        "R1": Z,
        "R2": X,
        "R3": Y,
        "R4": H,
    }

    # observable
    O = Y + 0.2*X

    metrics = {}
    for rname, A in OPS.items():
        deltas = []
        comms = []
        for _ in range(trials):
            rho = random_density(rng)
            left = np.trace(O @ (A @ rho))
            right = np.trace(O @ (rho @ A))
            deltas.append(abs(left - right))
            comms.append(np.linalg.norm(A @ rho - rho @ A))
        deltas = np.array(deltas, float)
        comms = np.array(comms, float)
        metrics[f"{rname}_delta_trace_mean"] = float(deltas.mean())
        metrics[f"{rname}_comm_norm_mean"] = float(comms.mean())

    out_obj = {"metrics": metrics}
    raw = json.dumps(out_obj, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)

    with open("results_oprole8_left_right_suite.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_OPROLE8_LEFT_RIGHT_SUITE")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for k,v in metrics.items():
        lines.append(f"METRIC: {k}={v}")
    lines.append("EVIDENCE_SIGNAL S_SIM_OPROLE8_LEFT_RIGHT_SUITE CORR E_SIM_OPROLE8_LEFT_RIGHT_SUITE")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_oprole8_left_right_suite.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()
