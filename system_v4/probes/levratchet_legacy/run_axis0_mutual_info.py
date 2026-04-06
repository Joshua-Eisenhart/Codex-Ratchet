#!/usr/bin/env python3
# run_axis0_mutual_info.py
# Produces:
#   results_axis0_mutual_info.json
#   sim_evidence_pack.txt   (1 SIM_EVIDENCE block for S_SIM_AXIS0_MI_TEST)

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

def ginibre_density(d: int, rng: np.random.Generator) -> np.ndarray:
    a = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    rho = a @ a.conj().T
    rho = rho / np.trace(rho)
    return rho

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())

def partial_trace_AB_to_A(rhoAB: np.ndarray) -> np.ndarray:
    # rhoAB is 4x4 for 2 qubits, basis |a,b>
    # trace out B
    rhoA = np.zeros((2,2), dtype=complex)
    for a in range(2):
        for ap in range(2):
            s = 0.0+0.0j
            for b in range(2):
                i = 2*a + b
                j = 2*ap + b
                s += rhoAB[i,j]
            rhoA[a,ap] = s
    rhoA = rhoA / np.trace(rhoA)
    return rhoA

def partial_trace_AB_to_B(rhoAB: np.ndarray) -> np.ndarray:
    # trace out A
    rhoB = np.zeros((2,2), dtype=complex)
    for b in range(2):
        for bp in range(2):
            s = 0.0+0.0j
            for a in range(2):
                i = 2*a + b
                j = 2*a + bp
                s += rhoAB[i,j]
            rhoB[b,bp] = s
    rhoB = rhoB / np.trace(rhoB)
    return rhoB

def main():
    seed = 0
    trials = 512

    rng = np.random.default_rng(seed)

    S_AB = []
    S_A = []
    S_B = []
    MI = []
    S_A_given_B = []
    neg_frac = 0

    for _ in range(trials):
        rhoAB = ginibre_density(4, rng)
        rhoA = partial_trace_AB_to_A(rhoAB)
        rhoB = partial_trace_AB_to_B(rhoAB)

        sab = vn_entropy(rhoAB)
        sa = vn_entropy(rhoA)
        sb = vn_entropy(rhoB)

        mi = sa + sb - sab
        s_a_given_b = sab - sb  # conditional entropy S(A|B), can be negative

        S_AB.append(sab)
        S_A.append(sa)
        S_B.append(sb)
        MI.append(mi)
        S_A_given_B.append(s_a_given_b)
        if s_a_given_b < 0:
            neg_frac += 1

    S_AB = np.array(S_AB, float)
    S_A = np.array(S_A, float)
    S_B = np.array(S_B, float)
    MI = np.array(MI, float)
    S_A_given_B = np.array(S_A_given_B, float)

    metrics = {
        "SAB_mean": float(S_AB.mean()),
        "SA_mean": float(S_A.mean()),
        "SB_mean": float(S_B.mean()),
        "MI_mean": float(MI.mean()),
        "MI_min": float(MI.min()),
        "MI_max": float(MI.max()),
        "SAgB_mean": float(S_A_given_B.mean()),
        "SAgB_min": float(S_A_given_B.min()),
        "SAgB_max": float(S_A_given_B.max()),
        "neg_SAgB_frac": float(neg_frac / trials),
    }

    out_obj = {"seed": seed, "trials": trials, "metrics": metrics}
    raw = json.dumps(out_obj, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)

    with open("results_axis0_mutual_info.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_AXIS0_MI_TEST")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for k,v in metrics.items():
        lines.append(f"METRIC: {k}={v}")
    # kill candidate if it never produces negative conditional entropy at all
    if metrics["neg_SAgB_frac"] == 0.0:
        lines.append("KILL_SIGNAL S_AXIS0_CAND_MI_V1 CORR AX0MI_FAIL")
    lines.append("EVIDENCE_SIGNAL S_SIM_AXIS0_MI_TEST CORR E_SIM_AXIS0_MI_TEST")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_axis0_mutual_info.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()
