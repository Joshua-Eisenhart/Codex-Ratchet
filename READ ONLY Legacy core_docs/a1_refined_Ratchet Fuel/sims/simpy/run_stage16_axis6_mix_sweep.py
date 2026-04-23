#!/usr/bin/env python3
# run_stage16_axis6_mix_sweep.py
# Produces:
#   results_stage16_axis6_mix_sweep.json
#   sim_evidence_pack.txt  (1 SIM_EVIDENCE block for S_SIM_STAGE16_AXIS6_MIX_SWEEP)

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

def stage_step(rho: np.ndarray, *, terr: str, axis6: str, U: np.ndarray, tparams: dict, oparams: dict, opname: str) -> np.ndarray:
    rho = (U @ rho @ U.conj().T) / np.trace(rho)
    Ks = TERRAIN[terr](tparams)
    if axis6 == "UP":
        rho = apply_kraus(apply_operator(rho, opname, oparams), Ks)
    else:
        rho = apply_operator(apply_kraus(rho, Ks), opname, oparams)
    return rho

def run_one_stage(rng: np.random.Generator, *, terr: str, base_axis6: str, U: np.ndarray, tparams: dict, oparams: dict,
                  mix_mode: str) -> tuple[float,float]:
    # returns entropy_mean, purity_mean for this stage under given mix_mode
    order = ["ti","te","fi","fe"]

    if mix_mode == "UNIFORM":
        pat = [base_axis6]*4
    elif mix_mode == "MIX_A":
        pat = ["UP","DOWN","UP","DOWN"]
    elif mix_mode == "MIX_B":
        pat = ["DOWN","UP","DOWN","UP"]
    elif mix_mode == "MIX_R":
        pat = rng.choice(["UP","DOWN"], size=4, replace=True).tolist()
    else:
        raise ValueError("bad mix_mode")

    rho = ginibre_density(2, rng)
    for opname, ax6 in zip(order, pat):
        rho = stage_step(rho, terr=terr, axis6=ax6, U=U, tparams=tparams, oparams=oparams, opname=opname)

    return vn_entropy(rho), purity(rho)

def main():
    TERRAIN_ORDER = ["Se","Ne","Ni","Si"]
    OUTER_AXIS6 = ["UP","DOWN","DOWN","UP"]
    INNER_AXIS6 = ["DOWN","UP","UP","DOWN"]

    seed = 0
    rng = np.random.default_rng(seed)
    num_states = 512

    theta = 0.07
    n_vec = np.array([0.3, 0.4, 0.866025403784], float)

    tparams = {"gamma": 0.12, "p": 0.08, "q": 0.10}
    oparams = {"theta_te": 0.05, "q_fi": 0.06, "d_fe": 0.04}

    def run_engine(axis3_sign: int) -> dict:
        U = unitary_from_axis(n_vec, theta, axis3_sign)
        out = {"outer": {}, "inner": {}}
        for loop_name, axis6_list in [("outer", OUTER_AXIS6), ("inner", INNER_AXIS6)]:
            for idx, terr in enumerate(TERRAIN_ORDER):
                base_ax6 = axis6_list[idx]
                rec = {}
                for mix_mode in ["MIX_A","MIX_B","MIX_R"]:
                    eu = []; pu = []
                    em = []; pm = []
                    for _ in range(num_states):
                        # uniform baseline
                        su, pu1 = run_one_stage(rng, terr=terr, base_axis6=base_ax6, U=U, tparams=tparams, oparams=oparams, mix_mode="UNIFORM")
                        sm, pm1 = run_one_stage(rng, terr=terr, base_axis6=base_ax6, U=U, tparams=tparams, oparams=oparams, mix_mode=mix_mode)
                        eu.append(su); pu.append(pu1)
                        em.append(sm); pm.append(pm1)
                    rec[mix_mode] = {
                        "dS": float(np.mean(em) - np.mean(eu)),
                        "dP": float(np.mean(pm) - np.mean(pu)),
                    }
                out[loop_name][f"{idx+1}_{terr}_{base_ax6}"] = rec
        return out

    res = {
        "seed": seed,
        "num_states": num_states,
        "theta": theta,
        "n_vec": [float(x) for x in n_vec.tolist()],
        "terrain_params": dict(tparams),
        "operator_params": dict(oparams),
        "terrain_order": list(TERRAIN_ORDER),
        "type1": run_engine(+1),
        "type2": run_engine(-1),
    }

    raw = json.dumps(res, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_stage16_axis6_mix_sweep.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_STAGE16_AXIS6_MIX_SWEEP")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")

    for typ in ["type1","type2"]:
        for loop in ["outer","inner"]:
            for k, rec in res[typ][loop].items():
                for mix_mode in ["MIX_A","MIX_B","MIX_R"]:
                    lines.append(f"METRIC: {typ}_{loop}_{k}_{mix_mode}_dS={rec[mix_mode]['dS']}")
                    lines.append(f"METRIC: {typ}_{loop}_{k}_{mix_mode}_dP={rec[mix_mode]['dP']}")

    lines.append("EVIDENCE_SIGNAL S_SIM_STAGE16_AXIS6_MIX_SWEEP CORR E_SIM_STAGE16_AXIS6_MIX_SWEEP")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_stage16_axis6_mix_sweep.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()