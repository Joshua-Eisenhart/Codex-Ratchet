#!/usr/bin/env python3
# run_stage16_sub4_axis6u.py
# Produces:
#   results_stage16_sub4_axis6u.json
#   sim_evidence_pack.txt  (1 SIM_EVIDENCE block for S_SIM_STAGE16_SUB4_AXIS6U)

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

def ginibre_density(d: int, rng: np.random.Generator) -> np.ndarray:
    a = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    rho = a @ a.conj().T
    rho = rho / np.trace(rho)
    return rho

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())

def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))

# ---- Terrains (CPTP maps) on 1-qubit density matrices ----
def apply_kraus(rho: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    out = out / np.trace(out)
    return out

def terr_Se(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def terr_Ne(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-p) * I2
    K1 = np.sqrt(p) * X
    return [K0, K1]

def terr_Ni(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-q) * I2
    K1 = np.sqrt(q) * Z
    return [K0, K1]

def terr_Si() -> list[np.ndarray]:
    return [I2]

TERRAIN = {
    "Se": lambda params: terr_Se(params["gamma"]),
    "Ne": lambda params: terr_Ne(params["p"]),
    "Ni": lambda params: terr_Ni(params["q"]),
    "Si": lambda params: terr_Si(),
}

# ---- Operators (4) as CPTP/Unitary maps on 1-qubit density matrices ----
def op_ti(rho: np.ndarray) -> np.ndarray:
    # projective pinching in Z basis
    P0 = np.array([[1,0],[0,0]], dtype=complex)
    P1 = np.array([[0,0],[0,1]], dtype=complex)
    out = P0 @ rho @ P0 + P1 @ rho @ P1
    return out / np.trace(out)

def op_te(rho: np.ndarray, theta_te: float) -> np.ndarray:
    U = expm_2x2(-1j * theta_te * X)
    out = U @ rho @ U.conj().T
    return out / np.trace(out)

def op_fi(rho: np.ndarray, q_fi: float) -> np.ndarray:
    # phase-flip
    return ((1-q_fi) * rho + q_fi * (Z @ rho @ Z)) / np.trace(rho)

def op_fe(rho: np.ndarray, d: float) -> np.ndarray:
    # depolarizing
    out = (1-d) * rho + (d/3.0) * (X @ rho @ X + Y @ rho @ Y + Z @ rho @ Z)
    return out / np.trace(out)

def apply_operator(rho: np.ndarray, opname: str, oparams: dict) -> np.ndarray:
    if opname == "ti":
        return op_ti(rho)
    if opname == "te":
        return op_te(rho, oparams["theta_te"])
    if opname == "fi":
        return op_fi(rho, oparams["q_fi"])
    if opname == "fe":
        return op_fe(rho, oparams["d_fe"])
    raise ValueError("bad opname")

def stage_run(rho: np.ndarray, *, terrain: str, axis6: str, U: np.ndarray, tparams: dict, oparams: dict) -> np.ndarray:
    # 4 substages always in same order
    for opname in ["ti","te","fi","fe"]:
        rho = (U @ rho @ U.conj().T) / np.trace(rho)
        Ks = TERRAIN[terrain](tparams)
        if axis6 == "UP":
            rho = apply_kraus(apply_operator(rho, opname, oparams), Ks)
        else:
            rho = apply_operator(apply_kraus(rho, Ks), opname, oparams)
    return rho

def main():
    # fixed terrain order per your canonical loop
    TERRAIN_ORDER = ["Se","Ne","Ni","Si"]

    # 6–5–3 per-engine stage axis6 pattern (outer+inner, same terrain order)
    # Type-1 (sign +1)
    TYPE1_OUTER_AXIS6 = ["UP","DOWN","DOWN","UP"]     # TiSe, NeTi, NiFe, FeSi
    TYPE1_INNER_AXIS6 = ["DOWN","UP","UP","DOWN"]     # SeFi, FiNe, TeNi, SiTe
    # Type-2 (sign -1)
    TYPE2_OUTER_AXIS6 = ["UP","DOWN","DOWN","UP"]     # FiSe, NeFi, NiTe, TeSi
    TYPE2_INNER_AXIS6 = ["DOWN","UP","UP","DOWN"]     # SeTi, TiNe, FeNi, SiFe

    seed = 0
    rng = np.random.default_rng(seed)
    num_states = 512

    # axis3_sign for engines
    theta = 0.07
    n_vec = np.array([0.3, 0.4, 0.866025403784], float)

    # terrain params (same family you’ve been using)
    tparams = {"gamma": 0.12, "p": 0.08, "q": 0.10}

    # operator params
    oparams = {"theta_te": 0.05, "q_fi": 0.06, "d_fe": 0.04}

    def run_engine(axis3_sign: int, outer_axis6: list[str], inner_axis6: list[str]) -> dict:
        U = unitary_from_axis(n_vec, theta, axis3_sign)

        # collect per-stage means across random initial states
        out = {"outer": {}, "inner": {}}

        for loop_name, axis6_list in [("outer", outer_axis6), ("inner", inner_axis6)]:
            for idx, terr in enumerate(TERRAIN_ORDER):
                axis6 = axis6_list[idx]
                ent = []
                pur = []
                for _ in range(num_states):
                    rho0 = ginibre_density(2, rng)
                    rho1 = stage_run(rho0, terrain=terr, axis6=axis6, U=U, tparams=tparams, oparams=oparams)
                    ent.append(vn_entropy(rho1))
                    pur.append(purity(rho1))
                out[loop_name][f"{idx+1}_{terr}_{axis6}"] = {
                    "vn_entropy_mean": float(np.mean(ent)),
                    "vn_entropy_min": float(np.min(ent)),
                    "vn_entropy_max": float(np.max(ent)),
                    "purity_mean": float(np.mean(pur)),
                    "purity_min": float(np.min(pur)),
                    "purity_max": float(np.max(pur)),
                }
        return out

    res = {
        "seed": seed,
        "num_states": num_states,
        "theta": theta,
        "n_vec": [float(x) for x in n_vec.tolist()],
        "terrain_params": dict(tparams),
        "operator_params": dict(oparams),
        "terrain_order": list(TERRAIN_ORDER),
        "type1_sign": +1,
        "type2_sign": -1,
        "type1": run_engine(+1, TYPE1_OUTER_AXIS6, TYPE1_INNER_AXIS6),
        "type2": run_engine(-1, TYPE2_OUTER_AXIS6, TYPE2_INNER_AXIS6),
    }

    raw = json.dumps(res, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_stage16_sub4_axis6u.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    # SIM_EVIDENCE: compact summary metrics (stage entropy_mean/purity_mean only)
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_STAGE16_SUB4_AXIS6U")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")

    def emit(loop: str, k: str, v: dict, prefix: str):
        lines.append(f"METRIC: {prefix}_{loop}_{k}_Smean={v['vn_entropy_mean']}")
        lines.append(f"METRIC: {prefix}_{loop}_{k}_Pmean={v['purity_mean']}")

    for k,v in res["type1"]["outer"].items():
        emit("outer", k, v, "T1")
    for k,v in res["type1"]["inner"].items():
        emit("inner", k, v, "T1")
    for k,v in res["type2"]["outer"].items():
        emit("outer", k, v, "T2")
    for k,v in res["type2"]["inner"].items():
        emit("inner", k, v, "T2")

    lines.append("EVIDENCE_SIGNAL S_SIM_STAGE16_SUB4_AXIS6U CORR E_SIM_STAGE16_SUB4_AXIS6U")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_stage16_sub4_axis6u.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()