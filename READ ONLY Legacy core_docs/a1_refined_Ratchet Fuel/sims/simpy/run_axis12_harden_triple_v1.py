#!/usr/bin/env python3
# run_axis12_harden_triple_v1.py
#
# Produces:
#   results_axis12_paramsweep_v1.json
#   results_axis12_altchan_v1.json
#   results_axis12_negctrl_swap_v1.json
#   sim_evidence_pack.txt   (3 SIM_EVIDENCE blocks back-to-back)
#
# SIM_IDs:
#   S_SIM_AXIS12_PARAMSWEEP_V1
#   S_SIM_AXIS12_ALTCHAN_V1
#   S_SIM_AXIS12_NEGCTRL_SWAP_V1

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

# -------- basic 1q objects --------
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

def apply_unitary(rho: np.ndarray, U: np.ndarray) -> np.ndarray:
    out = U @ rho @ U.conj().T
    return out / np.trace(out)

def apply_kraus(rho: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    return out / np.trace(out)

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())

def purity(rho: np.ndarray) -> float:
    return float(np.trace(rho @ rho).real)

def random_density_1q(rng: np.random.Generator) -> np.ndarray:
    # Ginibre (2x2)
    M = rng.normal(size=(2,2)) + 1j*rng.normal(size=(2,2))
    rho = M @ M.conj().T
    rho = rho / np.trace(rho)
    return rho.astype(complex)

# -------- baseline channels per topology label --------
def ch_Se(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def ch_Ne(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-p) * I2
    K1 = np.sqrt(p) * X
    return [K0, K1]

def ch_Ni(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-q) * I2
    K1 = np.sqrt(q) * Z
    return [K0, K1]

def ch_Si() -> list[np.ndarray]:
    return [I2]

# -------- alternative channel set (still CPTP) --------
def alt_Se(gamma: float) -> list[np.ndarray]:
    # phase-flip instead of amp-damp
    K0 = np.sqrt(1-gamma) * I2
    K1 = np.sqrt(gamma) * Z
    return [K0, K1]

def alt_Ne(p: float) -> list[np.ndarray]:
    # depolarizing-lite: I and Y
    K0 = np.sqrt(1-p) * I2
    K1 = np.sqrt(p) * Y
    return [K0, K1]

def alt_Ni(q: float) -> list[np.ndarray]:
    # bit-flip instead of phase-flip
    K0 = np.sqrt(1-q) * I2
    K1 = np.sqrt(q) * X
    return [K0, K1]

def alt_Si() -> list[np.ndarray]:
    return [I2]

SEQ = {
    "SEQ01": ["Se","Ne","Ni","Si"],  # canonical
    "SEQ02": ["Se","Si","Ni","Ne"],
    "SEQ03": ["Se","Ne","Si","Ni"],
    "SEQ04": ["Se","Si","Ne","Ni"],
}

def edges_in_seq(seq: list[str]) -> set[tuple[str,str]]:
    return set(zip(seq, seq[1:] + [seq[0]]))

def compute_axis12_flags(seq: list[str]) -> dict:
    # Axis-1 edge tokens currently used in your harness
    # SENI edges: Se<->Ni ; NESI edges: Ne<->Si
    e = edges_in_seq(seq)
    seni = int(("Se","Ni") in e or ("Ni","Se") in e)
    nesi = int(("Ne","Si") in e or ("Si","Ne") in e)

    # Axis-2 adjacency sets used as “SetA / SetB” style constraints.
    # We model as counts of “disallowed” edges per set; tune here if your current SetA/SetB differ.
    # SetA blocks cross: Se<->Si and Ne<->Ni
    # SetB blocks cross: Se<->Ne and Si<->Ni
    seta_bad = int(("Se","Si") in e or ("Si","Se") in e) + int(("Ne","Ni") in e or ("Ni","Ne") in e)
    setb_bad = int(("Se","Ne") in e or ("Ne","Se") in e) + int(("Si","Ni") in e or ("Ni","Si") in e)

    return {
        "seni_within": seni,
        "nesi_within": nesi,
        "seta_bad": seta_bad,
        "setb_bad": setb_bad,
    }

def run_suite(*, seed: int, num_states: int, cycles: int, theta: float, n_vec: tuple[float,float,float],
              params: dict, axis3_sign: int, channel_mode: str) -> dict:
    rng = np.random.default_rng(seed)
    U = unitary_from_axis(np.array(n_vec,float), theta, axis3_sign)

    if channel_mode == "base":
        CH = {
            "Se": lambda p: ch_Se(p["gamma"]),
            "Ne": lambda p: ch_Ne(p["p"]),
            "Ni": lambda p: ch_Ni(p["q"]),
            "Si": lambda p: ch_Si(),
        }
    elif channel_mode == "alt":
        CH = {
            "Se": lambda p: alt_Se(p["gamma"]),
            "Ne": lambda p: alt_Ne(p["p"]),
            "Ni": lambda p: alt_Ni(p["q"]),
            "Si": lambda p: alt_Si(),
        }
    else:
        raise ValueError("channel_mode")

    out = {}
    for seq_id, seq in SEQ.items():
        S_list = []
        P_list = []
        for _ in range(num_states):
            rho = random_density_1q(rng)
            for _c in range(cycles):
                for terr in seq:
                    rho = apply_unitary(rho, U)
                    rho = apply_kraus(rho, CH[terr](params))
            S_list.append(vn_entropy(rho))
            P_list.append(purity(rho))
        S_arr = np.array(S_list,float)
        P_arr = np.array(P_list,float)

        flags = compute_axis12_flags(seq)

        out[seq_id] = {
            "vn_entropy_mean": float(S_arr.mean()),
            "vn_entropy_min": float(S_arr.min()),
            "vn_entropy_max": float(S_arr.max()),
            "purity_mean": float(P_arr.mean()),
            "purity_min": float(P_arr.min()),
            "purity_max": float(P_arr.max()),
            **flags,
        }
    return out

def summarize_discriminators(block: dict) -> dict:
    # summarize how sequences separate under axis12 flags (no claims; just numbers)
    # group A: seni_within==1 ; group B: seni_within==0
    A = [v for v in block.values() if v["seni_within"] == 1]
    B = [v for v in block.values() if v["seni_within"] == 0]
    def mean(x, k): return float(np.mean([t[k] for t in x])) if x else float("nan")
    return {
        "mean_entropy_seni1": mean(A, "vn_entropy_mean"),
        "mean_entropy_seni0": mean(B, "vn_entropy_mean"),
        "mean_purity_seni1": mean(A, "purity_mean"),
        "mean_purity_seni0": mean(B, "purity_mean"),
        "delta_entropy_seni1_minus_seni0": mean(A,"vn_entropy_mean") - mean(B,"vn_entropy_mean"),
        "delta_purity_seni1_minus_seni0": mean(A,"purity_mean") - mean(B,"purity_mean"),
    }

def main():
    seed = 0
    num_states = 256
    cycles = 64
    theta = 0.07
    n_vec = (0.3, 0.4, 0.866025403784)

    # sweep grid (kept small by default; increase as desired)
    sweep = [
        {"gamma": 0.02, "p": 0.02, "q": 0.02},
        {"gamma": 0.08, "p": 0.08, "q": 0.08},
        {"gamma": 0.12, "p": 0.08, "q": 0.10},
    ]
    axis3_signs = [+1, -1]

    # ---------- SIM 1: PARAMSWEEP ----------
    paramsweep_rows = []
    for sign in axis3_signs:
        for params in sweep:
            block = run_suite(seed=seed, num_states=num_states, cycles=cycles, theta=theta, n_vec=n_vec,
                              params=params, axis3_sign=sign, channel_mode="base")
            paramsweep_rows.append({
                "axis3_sign": sign,
                "params": dict(params),
                "by_seq": block,
                "summary": summarize_discriminators(block),
            })
    out1 = {
        "seed": seed, "num_states": num_states, "cycles": cycles,
        "theta": theta, "n_vec": list(n_vec),
        "rows": paramsweep_rows,
    }
    raw1 = json.dumps(out1, indent=2, sort_keys=True).encode("utf-8")
    out1_hash = sha256_bytes(raw1)
    with open("results_axis12_paramsweep_v1.json", "wb") as f:
        f.write(raw1)

    # ---------- SIM 2: ALT CHANNEL REALIZATION ----------
    alt_rows = []
    for sign in axis3_signs:
        for params in sweep:
            block = run_suite(seed=seed, num_states=num_states, cycles=cycles, theta=theta, n_vec=n_vec,
                              params=params, axis3_sign=sign, channel_mode="alt")
            alt_rows.append({
                "axis3_sign": sign,
                "params": dict(params),
                "by_seq": block,
                "summary": summarize_discriminators(block),
            })
    out2 = {
        "seed": seed, "num_states": num_states, "cycles": cycles,
        "theta": theta, "n_vec": list(n_vec),
        "rows": alt_rows,
    }
    raw2 = json.dumps(out2, indent=2, sort_keys=True).encode("utf-8")
    out2_hash = sha256_bytes(raw2)
    with open("results_axis12_altchan_v1.json", "wb") as f:
        f.write(raw2)

    # ---------- SIM 3: NEGATIVE CONTROL (swap edge labels; should flip flags) ----------
    # swap meanings: SENI<->NESI (pure combinatorial)
    neg = {}
    for seq_id, seq in SEQ.items():
        f = compute_axis12_flags(seq)
        neg[seq_id] = {
            "seni_within_swapped": f["nesi_within"],
            "nesi_within_swapped": f["seni_within"],
            "seta_bad": f["seta_bad"],
            "setb_bad": f["setb_bad"],
        }
    out3 = {"by_seq": neg}
    raw3 = json.dumps(out3, indent=2, sort_keys=True).encode("utf-8")
    out3_hash = sha256_bytes(raw3)
    with open("results_axis12_negctrl_swap_v1.json", "wb") as f:
        f.write(raw3)

    code_hash = sha256_file(os.path.abspath(__file__))

    # ---------- SIM_EVIDENCE PACK ----------
    lines = []

    # SIM 1
    lines += [
        "BEGIN SIM_EVIDENCE v1",
        "SIM_ID: S_SIM_AXIS12_PARAMSWEEP_V1",
        f"CODE_HASH_SHA256: {code_hash}",
        f"OUTPUT_HASH_SHA256: {out1_hash}",
        f"METRIC: rows={len(out1['rows'])}",
        "EVIDENCE_SIGNAL S_SIM_AXIS12_PARAMSWEEP_V1 CORR E_SIM_AXIS12_PARAMSWEEP_V1",
        "END SIM_EVIDENCE v1",
        "",
    ]

    # SIM 2
    lines += [
        "BEGIN SIM_EVIDENCE v1",
        "SIM_ID: S_SIM_AXIS12_ALTCHAN_V1",
        f"CODE_HASH_SHA256: {code_hash}",
        f"OUTPUT_HASH_SHA256: {out2_hash}",
        f"METRIC: rows={len(out2['rows'])}",
        "EVIDENCE_SIGNAL S_SIM_AXIS12_ALTCHAN_V1 CORR E_SIM_AXIS12_ALTCHAN_V1",
        "END SIM_EVIDENCE v1",
        "",
    ]

    # SIM 3
    lines += [
        "BEGIN SIM_EVIDENCE v1",
        "SIM_ID: S_SIM_AXIS12_NEGCTRL_SWAP_V1",
        f"CODE_HASH_SHA256: {code_hash}",
        f"OUTPUT_HASH_SHA256: {out3_hash}",
        "EVIDENCE_SIGNAL S_SIM_AXIS12_NEGCTRL_SWAP_V1 CORR E_SIM_AXIS12_NEGCTRL_SWAP_V1",
        "END SIM_EVIDENCE v1",
        "",
    ]

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("DONE")
    print("wrote results_axis12_paramsweep_v1.json")
    print("wrote results_axis12_altchan_v1.json")
    print("wrote results_axis12_negctrl_swap_v1.json")
    print("wrote sim_evidence_pack.txt")

if __name__ == "__main__":
    main()