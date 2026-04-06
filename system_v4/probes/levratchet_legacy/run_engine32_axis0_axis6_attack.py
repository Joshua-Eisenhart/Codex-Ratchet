#!/usr/bin/env python3
# run_engine32_axis0_axis6_attack.py
# One run produces:
#   results_engine32_axis0_axis6_attack.json
#   sim_evidence_pack.txt  (1 SIM_EVIDENCE block for S_SIM_ENGINE32_AXIS0_AXIS6_ATTACK)

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

# ---- Terrains (CPTP maps) ----
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

# ---- Operators (4) ----
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

# ---- Axis0 proxy score on 1-qubit: trajectory entropy mean + purity mean ----
# (We keep Axis0 simple here: produces trajectory readouts. No AB coupling in this batch.)
def traj_metrics(rhos: list[np.ndarray]) -> dict:
    ent = np.array([vn_entropy(r) for r in rhos], float)
    pur = np.array([purity(r) for r in rhos], float)
    return {
        "S_traj_mean": float(ent.mean()),
        "P_traj_mean": float(pur.mean()),
        "S_final": float(ent[-1]),
        "P_final": float(pur[-1]),
    }

def stage_apply(rho: np.ndarray, terr: str, base_axis6: str, mix_mode: str,
                U: np.ndarray, tparams: dict, oparams: dict, rng: np.random.Generator) -> np.ndarray:
    ops = ["ti","te","fi","fe"]
    if mix_mode == "UNIFORM":
        pat = [base_axis6]*4
    elif mix_mode == "MIX_R":
        pat = rng.choice(["UP","DOWN"], size=4, replace=True).tolist()
    else:
        raise ValueError("bad mix_mode")

    for opname, ax6 in zip(ops, pat):
        rho = (U @ rho @ U.conj().T) / np.trace(rho)
        Ks = TERRAIN[terr](tparams)
        if ax6 == "UP":
            rho = apply_kraus(apply_operator(rho, opname, oparams), Ks)
        else:
            rho = apply_operator(apply_kraus(rho, Ks), opname, oparams)
    return rho

def run_engine(axis3_sign: int, seq: list[str], loop_axis6: list[str],
               mix_mode: str, *, seed: int, states: int, cycles: int,
               theta: float, n_vec: np.ndarray, tparams: dict, oparams: dict) -> dict:
    rng = np.random.default_rng(seed)
    U = unitary_from_axis(n_vec, theta, axis3_sign)
    rec = {"stage_metrics": {}}

    for i, terr in enumerate(seq):
        base_ax6 = loop_axis6[i]
        all_traj = []
        for _ in range(states):
            rho = ginibre_density(2, rng)
            traj = [rho]
            for _c in range(cycles):
                rho = stage_apply(rho, terr, base_ax6, mix_mode, U, tparams, oparams, rng)
                traj.append(rho)
            all_traj.append(traj_metrics(traj))
        # aggregate across states
        rec["stage_metrics"][f"{i+1}_{terr}_{base_ax6}"] = {
            "S_traj_mean": float(np.mean([x["S_traj_mean"] for x in all_traj])),
            "P_traj_mean": float(np.mean([x["P_traj_mean"] for x in all_traj])),
        }
    return rec

def main():
    SEQS = {
        "SEQ01": ["Se","Ne","Ni","Si"],
        "SEQ02": ["Se","Si","Ni","Ne"],
        "SEQ03": ["Se","Ne","Si","Ni"],
        "SEQ04": ["Se","Si","Ne","Ni"],
    }

    OUTER_AXIS6 = ["UP","DOWN","DOWN","UP"]
    INNER_AXIS6 = ["DOWN","UP","UP","DOWN"]

    seed = 0
    states = 256
    cycles = 16  # shorter cycles to widen suite
    theta = 0.07
    n_vec = np.array([0.3, 0.4, 0.866025403784], float)

    tparams = {"gamma": 0.12, "p": 0.08, "q": 0.10}
    oparams = {"theta_te": 0.05, "q_fi": 0.06, "d_fe": 0.04}

    res = {
        "seed": seed, "states": states, "cycles": cycles, "theta": theta,
        "n_vec": [float(x) for x in n_vec.tolist()],
        "terrain_params": dict(tparams),
        "operator_params": dict(oparams),
        "seqs": SEQS,
        "results": {},
    }

    for sign, tag in [(+1,"T1"),(-1,"T2")]:
        for seq_name, seq in SEQS.items():
            for loop_name, axis6_list in [("outer", OUTER_AXIS6), ("inner", INNER_AXIS6)]:
                for mix_mode in ["UNIFORM","MIX_R"]:
                    k = f"{tag}_{seq_name}_{loop_name}_{mix_mode}"
                    res["results"][k] = run_engine(
                        axis3_sign=sign, seq=seq, loop_axis6=axis6_list, mix_mode=mix_mode,
                        seed=seed, states=states, cycles=cycles, theta=theta, n_vec=n_vec,
                        tparams=tparams, oparams=oparams
                    )

    raw = json.dumps(res, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_engine32_axis0_axis6_attack.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_ENGINE32_AXIS0_AXIS6_ATTACK")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")

    # emit deltas: MIX_R - UNIFORM for each stage key
    for tag in ["T1","T2"]:
        for seq_name in SEQS.keys():
            for loop_name in ["outer","inner"]:
                u = res["results"][f"{tag}_{seq_name}_{loop_name}_UNIFORM"]["stage_metrics"]
                m = res["results"][f"{tag}_{seq_name}_{loop_name}_MIX_R"]["stage_metrics"]
                for sk in u.keys():
                    lines.append(f"METRIC: {tag}_{seq_name}_{loop_name}_{sk}_dS_traj={m[sk]['S_traj_mean']-u[sk]['S_traj_mean']}")
                    lines.append(f"METRIC: {tag}_{seq_name}_{loop_name}_{sk}_dP_traj={m[sk]['P_traj_mean']-u[sk]['P_traj_mean']}")

    lines.append("EVIDENCE_SIGNAL S_SIM_ENGINE32_AXIS0_AXIS6_ATTACK CORR E_SIM_ENGINE32_AXIS0_AXIS6_ATTACK")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_engine32_axis0_axis6_attack.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()