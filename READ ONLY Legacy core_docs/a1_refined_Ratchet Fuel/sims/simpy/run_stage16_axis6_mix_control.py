#!/usr/bin/env python3
# run_stage16_axis6_mix_control.py
# Produces:
#   results_stage16_axis6_mix_control.json
#   sim_evidence_pack.txt  (1 SIM_EVIDENCE block for S_SIM_STAGE16_AXIS6_MIX_CONTROL)

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
    return rho / np.trace(rho)

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())

def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))

# ---- terrain maps ----
def apply_kraus(rho: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    return out / np.trace(out)

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

# ---- operators (4) ----
def op_ti(rho: np.ndarray) -> np.ndarray:
    P0 = np.array([[1,0],[0,0]], dtype=complex)
    P1 = np.array([[0,0],[0,1]], dtype=complex)
    out = P0 @ rho @ P0 + P1 @ rho @ P1
    return out / np.trace(out)

def op_te(rho: np.ndarray, theta_te: float) -> np.ndarray:
    U = expm_2x2(-1j * theta_te * X)
    out = U @ rho @ U.conj().T
    return out / np.trace(out)

def op_fi(rho: np.ndarray, q_fi: float) -> np.ndarray:
    out = (1-q_fi) * rho + q_fi * (Z @ rho @ Z)
    return out / np.trace(out)

def op_fe(rho: np.ndarray, d: float) -> np.ndarray:
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

# uniform axis6: same for all 4 operators inside stage
def stage_uniform(rho: np.ndarray, *, terrain: str, axis6: str, U: np.ndarray, tparams: dict, oparams: dict) -> np.ndarray:
    for opname in ["ti","te","fi","fe"]:
        rho = (U @ rho @ U.conj().T) / np.trace(rho)
        Ks = TERRAIN[terrain](tparams)
        if axis6 == "UP":
            rho = apply_kraus(apply_operator(rho, opname, oparams), Ks)
        else:
            rho = apply_operator(apply_kraus(rho, Ks), opname, oparams)
    return rho

# mixed axis6: alternates per operator inside stage (UP,DOWN,UP,DOWN)
def stage_mixed(rho: np.ndarray, *, terrain: str, axis6_base: str, U: np.ndarray, tparams: dict, oparams: dict) -> np.ndarray:
    pat = ["UP","DOWN","UP","DOWN"] if axis6_base == "UP" else ["DOWN","UP","DOWN","UP"]
    for opname,axis6 in zip(["ti","te","fi","fe"], pat):
        rho = (U @ rho @ U.conj().T) / np.trace(rho)
        Ks = TERRAIN[terrain](tparams)
        if axis6 == "UP":
            rho = apply_kraus(apply_operator(rho, opname, oparams), Ks)
        else:
            rho = apply_operator(apply_kraus(rho, Ks), opname, oparams)
    return rho

def main():
    TERRAIN_ORDER = ["Se","Ne","Ni","Si"]

    # same stage axis6 pattern used in your Stage16 sim
    OUTER_AXIS6 = ["UP","DOWN","DOWN","UP"]
    INNER_AXIS6 = ["DOWN","UP","UP","DOWN"]

    seed = 0
    rng = np.random.default_rng(seed)
    num_states = 512

    theta = 0.07
    n_vec = np.array([0.3, 0.4, 0.866025403784], float)

    tparams = {"gamma": 0.12, "p": 0.08, "q": 0.10}
    oparams = {"theta_te": 0.05, "q_fi": 0.06, "d_fe": 0.04}

    def run(axis3_sign: int) -> dict:
        U = unitary_from_axis(n_vec, theta, axis3_sign)
        out = {"outer": {}, "inner": {}}
        for loop_name, axis6_list in [("outer", OUTER_AXIS6), ("inner", INNER_AXIS6)]:
            for idx, terr in enumerate(TERRAIN_ORDER):
                ax6 = axis6_list[idx]
                du = []
                pu = []
                dm = []
                pm = []
                for _ in range(num_states):
                    rho0 = ginibre_density(2, rng)
                    rU = stage_uniform(rho0, terrain=terr, axis6=ax6, U=U, tparams=tparams, oparams=oparams)
                    rM = stage_mixed(rho0, terrain=terr, axis6_base=ax6, U=U, tparams=tparams, oparams=oparams)
                    du.append(vn_entropy(rU)); pu.append(purity(rU))
                    dm.append(vn_entropy(rM)); pm.append(purity(rM))
                out[loop_name][f"{idx+1}_{terr}_{ax6}"] = {
                    "U_Smean": float(np.mean(du)),
                    "U_Pmean": float(np.mean(pu)),
                    "M_Smean": float(np.mean(dm)),
                    "M_Pmean": float(np.mean(pm)),
                    "dS": float(np.mean(dm) - np.mean(du)),
                    "dP": float(np.mean(pm) - np.mean(pu)),
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
        "type1": run(+1),
        "type2": run(-1),
    }

    raw = json.dumps(res, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_stage16_axis6_mix_control.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_STAGE16_AXIS6_MIX_CONTROL")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")

    for typ in ["type1","type2"]:
        for loop in ["outer","inner"]:
            for k,v in res[typ][loop].items():
                lines.append(f"METRIC: {typ}_{loop}_{k}_dS={v['dS']}")
                lines.append(f"METRIC: {typ}_{loop}_{k}_dP={v['dP']}")

    lines.append("EVIDENCE_SIGNAL S_SIM_STAGE16_AXIS6_MIX_CONTROL CORR E_SIM_STAGE16_AXIS6_MIX_CONTROL")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_stage16_axis6_mix_control.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()