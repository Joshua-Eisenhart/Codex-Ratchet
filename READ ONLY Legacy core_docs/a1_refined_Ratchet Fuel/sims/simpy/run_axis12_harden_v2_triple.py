#!/usr/bin/env python3
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
    M = rng.normal(size=(2,2)) + 1j*rng.normal(size=(2,2))
    rho = M @ M.conj().T
    rho = rho / np.trace(rho)
    return rho.astype(complex)

def ch_amp_damp(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def ch_bit_flip(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-p) * I2
    K1 = np.sqrt(p) * X
    return [K0, K1]

def ch_phase_flip(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-q) * I2
    K1 = np.sqrt(q) * Z
    return [K0, K1]

def ch_id() -> list[np.ndarray]:
    return [I2]

def alt_phase_flip(gamma: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-gamma) * I2
    K1 = np.sqrt(gamma) * Z
    return [K0, K1]

def alt_y_flip(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-p) * I2
    K1 = np.sqrt(p) * Y
    return [K0, K1]

def alt_x_flip(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-q) * I2
    K1 = np.sqrt(q) * X
    return [K0, K1]

SEQ = {
    "SEQ01": ["Se","Ne","Ni","Si"],
    "SEQ02": ["Se","Si","Ni","Ne"],
    "SEQ03": ["Se","Ne","Si","Ni"],
    "SEQ04": ["Se","Si","Ne","Ni"],
}

def edges_in_seq(seq: list[str]) -> set[tuple[str,str]]:
    return set(zip(seq, seq[1:] + [seq[0]]))

def axis12_flags(seq: list[str]) -> dict:
    e = edges_in_seq(seq)
    seni = int(("Se","Ni") in e or ("Ni","Se") in e)
    nesi = int(("Ne","Si") in e or ("Si","Ne") in e)
    seta_bad = int(("Se","Si") in e or ("Si","Se") in e) + int(("Ne","Ni") in e or ("Ni","Ne") in e)
    setb_bad = int(("Se","Ne") in e or ("Ne","Se") in e) + int(("Si","Ni") in e or ("Ni","Si") in e)
    return {"seni_within": seni, "nesi_within": nesi, "seta_bad": seta_bad, "setb_bad": setb_bad}

def run_block(*, rng: np.random.Generator, U: np.ndarray, params: dict, cycles: int,
              num_states: int, chan_map: dict[str, list[np.ndarray]]) -> dict:
    out = {}
    for sid, seq in SEQ.items():
        S_list, P_list = [], []
        for _ in range(num_states):
            rho = random_density_1q(rng)
            for _c in range(cycles):
                for terr in seq:
                    rho = apply_unitary(rho, U)
                    rho = apply_kraus(rho, chan_map[terr](params))
            S_list.append(vn_entropy(rho))
            P_list.append(purity(rho))
        S = np.array(S_list,float); P = np.array(P_list,float)
        f = axis12_flags(seq)
        out[sid] = {
            "vn_entropy_mean": float(S.mean()),
            "purity_mean": float(P.mean()),
            **f,
        }
    return out

def discrim_seni(block: dict) -> dict:
    A = [v for v in block.values() if v["seni_within"] == 1]
    B = [v for v in block.values() if v["seni_within"] == 0]
    def m(x,k): return float(np.mean([t[k] for t in x])) if x else 0.0
    return {
        "dS": m(A,"vn_entropy_mean") - m(B,"vn_entropy_mean"),
        "dP": m(A,"purity_mean") - m(B,"purity_mean"),
    }

def main():
    seed = 0
    rng = np.random.default_rng(seed)
    num_states = 512
    cycles = 64
    theta = 0.07
    n_vec = np.array([0.3, 0.4, 0.866025403784], float)

    sweep = [
        {"gamma": 0.02, "p": 0.02, "q": 0.02},
        {"gamma": 0.08, "p": 0.08, "q": 0.08},
        {"gamma": 0.12, "p": 0.08, "q": 0.10},
    ]
    signs = [+1, -1]

    base_map = {
        "Se": lambda p: ch_amp_damp(p["gamma"]),
        "Ne": lambda p: ch_bit_flip(p["p"]),
        "Ni": lambda p: ch_phase_flip(p["q"]),
        "Si": lambda p: ch_id(),
    }
    alt_map = {
        "Se": lambda p: alt_phase_flip(p["gamma"]),
        "Ne": lambda p: alt_y_flip(p["p"]),
        "Ni": lambda p: alt_x_flip(p["q"]),
        "Si": lambda p: ch_id(),
    }
    # negative control: relabel topology->channel (swap Se<->Ne; Ni<->Si)
    neg_map = {
        "Se": lambda p: base_map["Ne"](p),
        "Ne": lambda p: base_map["Se"](p),
        "Ni": lambda p: base_map["Si"](p),
        "Si": lambda p: base_map["Ni"](p),
    }

    # ---- SIM1 ----
    rows1 = []
    for sgn in signs:
        U = unitary_from_axis(n_vec, theta, sgn)
        for params in sweep:
            blk = run_block(rng=rng, U=U, params=params, cycles=cycles, num_states=num_states, chan_map=base_map)
            rows1.append({"axis3_sign": sgn, "params": params, "disc": discrim_seni(blk)})
    out1 = {"rows": rows1}
    raw1 = json.dumps(out1, indent=2, sort_keys=True).encode()
    h1 = sha256_bytes(raw1)
    with open("results_axis12_paramsweep_v2.json","wb") as f: f.write(raw1)

    # ---- SIM2 ----
    rows2 = []
    for sgn in signs:
        U = unitary_from_axis(n_vec, theta, sgn)
        for params in sweep:
            blk = run_block(rng=rng, U=U, params=params, cycles=cycles, num_states=num_states, chan_map=alt_map)
            rows2.append({"axis3_sign": sgn, "params": params, "disc": discrim_seni(blk)})
    out2 = {"rows": rows2}
    raw2 = json.dumps(out2, indent=2, sort_keys=True).encode()
    h2 = sha256_bytes(raw2)
    with open("results_axis12_altchan_v2.json","wb") as f: f.write(raw2)

    # ---- SIM3 ----
    rows3 = []
    for sgn in signs:
        U = unitary_from_axis(n_vec, theta, sgn)
        for params in sweep:
            blk = run_block(rng=rng, U=U, params=params, cycles=cycles, num_states=num_states, chan_map=neg_map)
            rows3.append({"axis3_sign": sgn, "params": params, "disc": discrim_seni(blk)})
    out3 = {"rows": rows3}
    raw3 = json.dumps(out3, indent=2, sort_keys=True).encode()
    h3 = sha256_bytes(raw3)
    with open("results_axis12_negctrl_label_v2.json","wb") as f: f.write(raw3)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines += [
        "BEGIN SIM_EVIDENCE v1",
        "SIM_ID: S_SIM_AXIS12_PARAMSWEEP_V2",
        f"CODE_HASH_SHA256: {code_hash}",
        f"OUTPUT_HASH_SHA256: {h1}",
        f"METRIC: rows={len(rows1)}",
        f"METRIC: dS_min={min(r['disc']['dS'] for r in rows1)}",
        f"METRIC: dS_max={max(r['disc']['dS'] for r in rows1)}",
        f"METRIC: dP_min={min(r['disc']['dP'] for r in rows1)}",
        f"METRIC: dP_max={max(r['disc']['dP'] for r in rows1)}",
        "EVIDENCE_SIGNAL S_SIM_AXIS12_PARAMSWEEP_V2 CORR E_SIM_AXIS12_PARAMSWEEP_V2",
        "END SIM_EVIDENCE v1",
        "",
        "BEGIN SIM_EVIDENCE v1",
        "SIM_ID: S_SIM_AXIS12_ALTCHAN_V2",
        f"CODE_HASH_SHA256: {code_hash}",
        f"OUTPUT_HASH_SHA256: {h2}",
        f"METRIC: rows={len(rows2)}",
        f"METRIC: dS_min={min(r['disc']['dS'] for r in rows2)}",
        f"METRIC: dS_max={max(r['disc']['dS'] for r in rows2)}",
        f"METRIC: dP_min={min(r['disc']['dP'] for r in rows2)}",
        f"METRIC: dP_max={max(r['disc']['dP'] for r in rows2)}",
        "EVIDENCE_SIGNAL S_SIM_AXIS12_ALTCHAN_V2 CORR E_SIM_AXIS12_ALTCHAN_V2",
        "END SIM_EVIDENCE v1",
        "",
        "BEGIN SIM_EVIDENCE v1",
        "SIM_ID: S_SIM_AXIS12_NEGCTRL_LABEL_V2",
        f"CODE_HASH_SHA256: {code_hash}",
        f"OUTPUT_HASH_SHA256: {h3}",
        f"METRIC: rows={len(rows3)}",
        f"METRIC: dS_min={min(r['disc']['dS'] for r in rows3)}",
        f"METRIC: dS_max={max(r['disc']['dS'] for r in rows3)}",
        f"METRIC: dP_min={min(r['disc']['dP'] for r in rows3)}",
        f"METRIC: dP_max={max(r['disc']['dP'] for r in rows3)}",
        "EVIDENCE_SIGNAL S_SIM_AXIS12_NEGCTRL_LABEL_V2 CORR E_SIM_AXIS12_NEGCTRL_LABEL_V2",
        "END SIM_EVIDENCE v1",
        "",
    ]
    with open("sim_evidence_pack.txt","w",encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("DONE: results_axis12_paramsweep_v2.json, results_axis12_altchan_v2.json, results_axis12_negctrl_label_v2.json, sim_evidence_pack.txt")

if __name__ == "__main__":
    main()