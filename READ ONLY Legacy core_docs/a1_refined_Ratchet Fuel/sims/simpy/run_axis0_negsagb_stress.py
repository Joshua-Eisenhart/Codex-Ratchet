#!/usr/bin/env python3
# run_axis0_negsagb_stress.py
# Produces:
#   results_axis0_negsagb_stress.json
#   sim_evidence_pack.txt  (1 SIM_EVIDENCE block for S_SIM_AXIS0_NEGSAGB_STRESS)

from __future__ import annotations
import json, hashlib, os
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

# ---------- Pauli ----------
I2 = np.eye(2, dtype=complex)
X = np.array([[0,1],[1,0]], dtype=complex)
Y = np.array([[0,-1j],[1j,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)

def expm_2x2(a: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eig(a)
    return (v @ np.diag(np.exp(w)) @ np.linalg.inv(v)).astype(complex)

def unitary_from_axis(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = n / np.linalg.norm(n)
    H = n[0]*X + n[1]*Y + n[2]*Z
    return expm_2x2(-1j * sign * theta * H)

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

def mutual_info_and_condA_given_B(rhoAB: np.ndarray) -> tuple[float,float]:
    rhoA = partial_trace_AB_to_A(rhoAB)
    rhoB = partial_trace_AB_to_B(rhoAB)
    sab = vn_entropy(rhoAB)
    sa  = vn_entropy(rhoA)
    sb  = vn_entropy(rhoB)
    mi = sa + sb - sab
    sAgB = sab - sb
    return float(mi), float(sAgB)

# ---------- AB entanglers ----------
CNOT = np.array([
    [1,0,0,0],
    [0,1,0,0],
    [0,0,0,1],
    [0,0,1,0],
], dtype=complex)

CZ = np.array([
    [1,0,0,0],
    [0,1,0,0],
    [0,0,1,0],
    [0,0,0,-1],
], dtype=complex)

def apply_unitary_A(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UA = np.kron(U, I2)
    out = UA @ rhoAB @ UA.conj().T
    out = out / np.trace(out)
    return out

def apply_unitary_AB(rhoAB: np.ndarray, UAB: np.ndarray) -> np.ndarray:
    out = UAB @ rhoAB @ UAB.conj().T
    out = out / np.trace(out)
    return out

def apply_kraus_A(rhoAB: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4,4), dtype=complex)
    for K in Ks:
        KA = np.kron(K, I2)
        out += KA @ rhoAB @ KA.conj().T
    out = out / np.trace(out)
    return out

# ---------- CPTP terrain maps on A ----------
def terrain_Se(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def terrain_Ne(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-p) * I2
    K1 = np.sqrt(p) * X
    return [K0, K1]

def terrain_Ni(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-q) * I2
    K1 = np.sqrt(q) * Z
    return [K0, K1]

def terrain_Si() -> list[np.ndarray]:
    return [I2]

TERRAIN = {
    "Se": lambda params: terrain_Se(params["gamma"]),
    "Ne": lambda params: terrain_Ne(params["p"]),
    "Ni": lambda params: terrain_Ni(params["q"]),
    "Si": lambda params: terrain_Si(),
}

def run_branch(seq: list[str], *, seed: int, trials: int, cycles: int,
               axis3_sign: int, theta: float, n_vec: tuple[float,float,float],
               params: dict, entangler: str, entangle_reps: int,
               entangle_pos: str) -> dict:
    rng = np.random.default_rng(seed)
    U = unitary_from_axis(np.array(n_vec,float), theta, axis3_sign)
    UAB = CNOT if entangler == "CNOT" else CZ

    mi_list = []
    sagb_list = []

    for _ in range(trials):
        rho = ginibre_density(4, rng)
        for _c in range(cycles):
            for terr in seq:
                Ks = TERRAIN[terr](params)

                rho = apply_unitary_A(rho, U)

                if entangle_pos == "BEFORE":
                    for _k in range(entangle_reps):
                        rho = apply_unitary_AB(rho, UAB)

                rho = apply_kraus_A(rho, Ks)

                if entangle_pos == "AFTER":
                    for _k in range(entangle_reps):
                        rho = apply_unitary_AB(rho, UAB)

        mi, sagb = mutual_info_and_condA_given_B(rho)
        mi_list.append(mi)
        sagb_list.append(sagb)

    mi_arr = np.array(mi_list, float)
    sg_arr = np.array(sagb_list, float)
    neg_frac = float(np.mean((sg_arr < 0.0).astype(float)))

    return {
        "MI_mean": float(mi_arr.mean()),
        "MI_min": float(mi_arr.min()),
        "MI_max": float(mi_arr.max()),
        "SAgB_mean": float(sg_arr.mean()),
        "SAgB_min": float(sg_arr.min()),
        "SAgB_max": float(sg_arr.max()),
        "neg_SAgB_frac": neg_frac,
    }

def main():
    # branch set: SEQ01 vs SEQ02
    SEQ01 = ["Se","Ne","Ni","Si"]
    SEQ02 = ["Se","Si","Ni","Ne"]

    # fixed knobs (aligned with your existing harness)
    seed = 0
    theta = 0.07
    n_vec = (0.3, 0.4, 0.866025403784)

    # sweep knobs (rich but bounded)
    axis3_sign_list = [+1, -1]
    cycles_list = [8, 16, 32, 64]
    trials = 512

    # noise downshift to allow entanglement to survive
    gamma_list = [0.02, 0.05, 0.08, 0.12]
    p_list     = [0.02, 0.05, 0.08]
    q_list     = [0.02, 0.05, 0.10]

    entanglers = ["CNOT", "CZ"]
    entangle_reps_list = [1, 2, 4]
    entangle_pos_list = ["BEFORE", "AFTER"]

    best = None  # by max(mean neg frac across branches)
    records = []

    def score(r1: dict, r2: dict) -> float:
        return 0.5*(r1["neg_SAgB_frac"] + r2["neg_SAgB_frac"])

    for axis3_sign in axis3_sign_list:
        for cycles in cycles_list:
            for gamma in gamma_list:
                for p in p_list:
                    for q in q_list:
                        params = {"gamma": gamma, "p": p, "q": q}
                        for entangler in entanglers:
                            for entangle_reps in entangle_reps_list:
                                for entangle_pos in entangle_pos_list:
                                    r1 = run_branch(SEQ01, seed=seed, trials=trials, cycles=cycles, axis3_sign=axis3_sign,
                                                    theta=theta, n_vec=n_vec, params=params,
                                                    entangler=entangler, entangle_reps=entangle_reps, entangle_pos=entangle_pos)
                                    r2 = run_branch(SEQ02, seed=seed, trials=trials, cycles=cycles, axis3_sign=axis3_sign,
                                                    theta=theta, n_vec=n_vec, params=params,
                                                    entangler=entangler, entangle_reps=entangle_reps, entangle_pos=entangle_pos)

                                    rec = {
                                        "axis3_sign": axis3_sign,
                                        "cycles": cycles,
                                        "params": params,
                                        "entangler": entangler,
                                        "entangle_reps": entangle_reps,
                                        "entangle_pos": entangle_pos,
                                        "SEQ01": r1,
                                        "SEQ02": r2,
                                        "delta_MI_mean_SEQ02_minus_SEQ01": float(r2["MI_mean"] - r1["MI_mean"]),
                                        "delta_SAgB_mean_SEQ02_minus_SEQ01": float(r2["SAgB_mean"] - r1["SAgB_mean"]),
                                        "delta_negfrac_SEQ02_minus_SEQ01": float(r2["neg_SAgB_frac"] - r1["neg_SAgB_frac"]),
                                    }
                                    records.append(rec)

                                    sc = score(r1, r2)
                                    if (best is None) or (sc > best["score"]):
                                        best = {"score": sc, "rec": rec}

            # early stop if strong negativity appears
            if best is not None and best["score"] >= 0.05:
                break

    out = {
        "fixed": {"seed": seed, "theta": theta, "n_vec": list(n_vec), "trials": trials},
        "best": best,
        "records_count": len(records),
        "records_sample": records[:10],  # keep file small
    }

    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)

    with open("results_axis0_negsagb_stress.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    # Evidence metrics: best found
    m = {}
    if best is None:
        m["best_score"] = 0.0
    else:
        rec = best["rec"]
        m["best_score"] = float(best["score"])
        m["best_axis3_sign"] = float(rec["axis3_sign"])
        m["best_cycles"] = float(rec["cycles"])
        m["best_gamma"] = float(rec["params"]["gamma"])
        m["best_p"] = float(rec["params"]["p"])
        m["best_q"] = float(rec["params"]["q"])
        m["best_entangler"] = 0.0 if rec["entangler"] == "CNOT" else 1.0  # encode as numeric
        m["best_entangle_reps"] = float(rec["entangle_reps"])
        m["best_entangle_pos"] = 0.0 if rec["entangle_pos"] == "BEFORE" else 1.0  # numeric

        for k,v in rec["SEQ01"].items():
            m[f"SEQ01_{k}"] = float(v)
        for k,v in rec["SEQ02"].items():
            m[f"SEQ02_{k}"] = float(v)

        m["delta_MI_mean_SEQ02_minus_SEQ01"] = float(rec["delta_MI_mean_SEQ02_minus_SEQ01"])
        m["delta_SAgB_mean_SEQ02_minus_SEQ01"] = float(rec["delta_SAgB_mean_SEQ02_minus_SEQ01"])
        m["delta_negfrac_SEQ02_minus_SEQ01"] = float(rec["delta_negfrac_SEQ02_minus_SEQ01"])

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_AXIS0_NEGSAGB_STRESS")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for k,v in m.items():
        lines.append(f"METRIC: {k}={v}")
    lines.append("EVIDENCE_SIGNAL S_SIM_AXIS0_NEGSAGB_STRESS CORR E_SIM_AXIS0_NEGSAGB_STRESS")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_axis0_negsagb_stress.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()
