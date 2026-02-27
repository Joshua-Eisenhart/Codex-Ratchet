#!/usr/bin/env python3
# run_axis0_historyop_rec_suite_v1.py
# Produces:
#   results_axis0_historyop_rec_suite_v1.json
#   sim_evidence_pack.txt  (4 SIM_EVIDENCE blocks)

from __future__ import annotations
import json, hashlib, os
import numpy as np

# ----------------- hashes -----------------

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------- basic ops -----------------

I2 = np.eye(2, dtype=complex)
X  = np.array([[0, 1],[1, 0]], dtype=complex)
Y  = np.array([[0,-1j],[1j,0]], dtype=complex)
Z  = np.array([[1, 0],[0,-1]], dtype=complex)

def expm_2x2(a: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eig(a)
    return (v @ np.diag(np.exp(w)) @ np.linalg.inv(v)).astype(complex)

def unitary_from_axis(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = np.array(n, float)
    n = n / np.linalg.norm(n)
    H = n[0]*X + n[1]*Y + n[2]*Z
    return expm_2x2(-1j * sign * theta * H)

def kron2(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return np.kron(A, B)

def apply_U_A(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UA = kron2(U, I2)
    out = UA @ rhoAB @ UA.conj().T
    return out / np.trace(out)

def apply_U_B(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UB = kron2(I2, U)
    out = UB @ rhoAB @ UB.conj().T
    return out / np.trace(out)

CNOT = np.array([
    [1,0,0,0],
    [0,1,0,0],
    [0,0,0,1],
    [0,0,1,0],
], dtype=complex)

def apply_U_AB(rhoAB: np.ndarray, UAB: np.ndarray) -> np.ndarray:
    out = UAB @ rhoAB @ UAB.conj().T
    return out / np.trace(out)

def apply_kraus_A(rhoAB: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4,4), dtype=complex)
    for K in Ks:
        KA = kron2(K, I2)
        out += KA @ rhoAB @ KA.conj().T
    return out / np.trace(out)

def apply_kraus_B(rhoAB: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4,4), dtype=complex)
    for K in Ks:
        KB = kron2(I2, K)
        out += KB @ rhoAB @ KB.conj().T
    return out / np.trace(out)

# ----------------- terrains -----------------

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

# ----------------- partial traces + entropies -----------------

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
    return rhoA / np.trace(rhoA)

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
    return rhoB / np.trace(rhoB)

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())

def mi_and_sAgB(rhoAB: np.ndarray) -> tuple[float,float]:
    rhoA = partial_trace_AB_to_A(rhoAB)
    rhoB = partial_trace_AB_to_B(rhoAB)
    sab = vn_entropy(rhoAB)
    sa  = vn_entropy(rhoA)
    sb  = vn_entropy(rhoB)
    mi = sa + sb - sab
    sAgB = sab - sb
    return float(mi), float(sAgB)

def frob(a: np.ndarray) -> float:
    return float(np.linalg.norm(a, ord="fro"))

# ----------------- initial states -----------------

def ginibre_state_4(rng: np.random.Generator) -> np.ndarray:
    G = rng.normal(size=(4,4)) + 1j*rng.normal(size=(4,4))
    rho = G @ G.conj().T
    rho = rho / np.trace(rho)
    return rho

def bell_seed_state(rng: np.random.Generator) -> np.ndarray:
    # |Phi+> = (|00>+|11>)/sqrt(2)
    phi = np.array([1,0,0,1], dtype=complex) / np.sqrt(2)
    rho = np.outer(phi, phi.conj())
    # small random local basis jitter
    a = rng.uniform(0, 2*np.pi)
    b = rng.uniform(0, 2*np.pi)
    UA = expm_2x2(-1j * a * Z)
    UB = expm_2x2(-1j * b * X)
    rho = apply_U_A(rho, UA)
    rho = apply_U_B(rho, UB)
    return rho / np.trace(rho)

# ----------------- record/reconstruct modes -----------------
# REC_ID   : record full rhoAB, reconstruct exact
# REC_MARG : record rhoA and rhoB, reconstruct rhoA ⊗ rhoB
# REC_MIX  : record nothing, reconstruct maximally mixed
# REC_SCR  : record rhoA⊗rhoB then apply fixed scramble U_scr

U_scr = np.kron(X, Z)  # fixed scramble

def reconstruct(rec_mode: str, rhoAB: np.ndarray) -> np.ndarray:
    if rec_mode == "REC_ID":
        return rhoAB
    if rec_mode == "REC_MARG":
        rhoA = partial_trace_AB_to_A(rhoAB)
        rhoB = partial_trace_AB_to_B(rhoAB)
        rec = np.kron(rhoA, rhoB)
        return rec / np.trace(rec)
    if rec_mode == "REC_MIX":
        return np.eye(4, dtype=complex) / 4.0
    if rec_mode == "REC_SCR":
        rhoA = partial_trace_AB_to_A(rhoAB)
        rhoB = partial_trace_AB_to_B(rhoAB)
        rec = np.kron(rhoA, rhoB)
        rec = rec / np.trace(rec)
        out = U_scr @ rec @ U_scr.conj().T
        return out / np.trace(out)
    raise ValueError("bad rec_mode")

# ----------------- finite history operator -----------------

SEQ = {
    "SEQ01": ["Se","Ne","Ni","Si"],
    "SEQ02": ["Se","Si","Ni","Ne"],
    "SEQ03": ["Se","Ne","Si","Ni"],
    "SEQ04": ["Se","Si","Ne","Ni"],
}

def run_one(seq: list[str], axis3_sign: int, rec_mode: str,
            init_mode: str, seed: int, trials: int,
            cycles: int, theta: float, n_vec: tuple[float,float,float],
            params: dict, entangle_reps: int) -> dict:
    rng = np.random.default_rng(seed)
    U = unitary_from_axis(np.array(n_vec,float), theta, axis3_sign)

    mi_traj = []
    sagb_traj = []
    err_traj = []

    mi_end = []
    sagb_end = []
    err_end = []

    for _ in range(trials):
        if init_mode == "GINIBRE":
            rho = ginibre_state_4(rng)
        else:
            rho = bell_seed_state(rng)

        mi_path = []
        sg_path = []
        er_path = []

        for _c in range(cycles):
            for terr in seq:
                # local Weyl-like unitary on A
                rho = apply_U_A(rho, U)
                # local terrain noise on A and B (same params)
                Ks = TERRAIN[terr](params)
                rho = apply_kraus_A(rho, Ks)
                rho = apply_kraus_B(rho, Ks)
                # AB entangler reps
                for _k in range(entangle_reps):
                    rho = apply_U_AB(rho, CNOT)

                mi, sg = mi_and_sAgB(rho)
                rec = reconstruct(rec_mode, rho)
                er = frob(rho - rec)

                mi_path.append(mi)
                sg_path.append(sg)
                er_path.append(er)

        mi_traj.append(float(np.mean(mi_path)))
        sagb_traj.append(float(np.mean(sg_path)))
        err_traj.append(float(np.mean(er_path)))

        mi_end.append(mi_path[-1])
        sagb_end.append(sg_path[-1])
        err_end.append(er_path[-1])

    def pack(arr: list[float]) -> dict:
        a = np.array(arr, float)
        return {"mean": float(a.mean()), "min": float(a.min()), "max": float(a.max())}

    return {
        "MI_traj": pack(mi_traj),
        "SAgB_traj": pack(sagb_traj),
        "ERR_traj": pack(err_traj),
        "MI_end": pack(mi_end),
        "SAgB_end": pack(sagb_end),
        "ERR_end": pack(err_end),
        "NEG_SAgB_end_frac": float(np.mean((np.array(sagb_end,float) < 0.0).astype(float))),
    }

def suite(rec_mode: str) -> dict:
    seed = 0
    trials = 256
    cycles = 16
    theta = 0.07
    n_vec = (0.3, 0.4, 0.866025403784)
    params = {"gamma": 0.02, "p": 0.02, "q": 0.02}
    entangle_reps = 1

    out = {
        "seed": seed,
        "trials": trials,
        "cycles": cycles,
        "theta": theta,
        "n_vec": list(n_vec),
        "terrain_params": dict(params),
        "entangle_reps": entangle_reps,
        "rec_mode": rec_mode,
        "SEQ": dict(SEQ),
        "runs": {}
    }

    for init_mode in ["GINIBRE", "BELL"]:
        for axis3_sign in [+1, -1]:
            key = f"{init_mode}_s{axis3_sign:+d}"
            out["runs"][key] = {}
            for seq_name, seq_list in SEQ.items():
                out["runs"][key][seq_name] = run_one(
                    seq_list, axis3_sign, rec_mode, init_mode,
                    seed, trials, cycles, theta, n_vec, params, entangle_reps
                )

    # small discriminators SEQ02-SEQ01 on trajectory MI_mean and end negfrac
    def pick(run_key: str, seq_name: str, field: str) -> float:
        return float(out["runs"][run_key][seq_name][field]["mean"])

    for run_key in out["runs"].keys():
        d = {}
        d["dMI_traj_mean_SEQ02_minus_SEQ01"] = pick(run_key, "SEQ02", "MI_traj") - pick(run_key, "SEQ01", "MI_traj")
        d["dERR_traj_mean_SEQ02_minus_SEQ01"] = pick(run_key, "SEQ02", "ERR_traj") - pick(run_key, "SEQ01", "ERR_traj")
        d["dNEG_end_frac_SEQ02_minus_SEQ01"] = float(out["runs"][run_key]["SEQ02"]["NEG_SAgB_end_frac"] - out["runs"][run_key]["SEQ01"]["NEG_SAgB_end_frac"])
        out["runs"][run_key]["DELTA_SEQ02_SEQ01"] = d

    return out

def emit_block(sim_id: str, token: str, data: dict) -> str:
    raw = json.dumps(data, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append(f"SIM_ID: {sim_id}")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")

    # compact metrics: per init/sign, include deltas and one key stat
    for run_key in sorted(data["runs"].keys()):
        d = data["runs"][run_key]["DELTA_SEQ02_SEQ01"]
        lines.append(f"METRIC: {run_key}_dMI_traj_mean={d['dMI_traj_mean_SEQ02_minus_SEQ01']}")
        lines.append(f"METRIC: {run_key}_dERR_traj_mean={d['dERR_traj_mean_SEQ02_minus_SEQ01']}")
        lines.append(f"METRIC: {run_key}_dNEG_end_frac={d['dNEG_end_frac_SEQ02_minus_SEQ01']}")
        # also report SEQ01 end means for MI and ERR (baseline scale)
        base = data["runs"][run_key]["SEQ01"]
        lines.append(f"METRIC: {run_key}_SEQ01_MI_end_mean={base['MI_end']['mean']}")
        lines.append(f"METRIC: {run_key}_SEQ01_ERR_end_mean={base['ERR_end']['mean']}")

    lines.append(f"EVIDENCE_SIGNAL {sim_id} CORR {token}")
    lines.append("END SIM_EVIDENCE v1")
    return "\n".join(lines) + "\n"

def main():
    cases = [
        ("S_SIM_AXIS0_HISTORYOP_REC_ID_V1",   "E_SIM_AXIS0_HISTORYOP_REC_ID_V1",   "REC_ID"),
        ("S_SIM_AXIS0_HISTORYOP_REC_MARG_V1", "E_SIM_AXIS0_HISTORYOP_REC_MARG_V1", "REC_MARG"),
        ("S_SIM_AXIS0_HISTORYOP_REC_MIX_V1",  "E_SIM_AXIS0_HISTORYOP_REC_MIX_V1",  "REC_MIX"),
        ("S_SIM_AXIS0_HISTORYOP_REC_SCR_V1",  "E_SIM_AXIS0_HISTORYOP_REC_SCR_V1",  "REC_SCR"),
    ]

    out_all = {"cases": {}}
    pack = []

    for sim_id, token, rec_mode in cases:
        data = suite(rec_mode)
        out_all["cases"][sim_id] = data
        pack.append(emit_block(sim_id, token, data))

    raw = json.dumps(out_all, indent=2, sort_keys=True).encode("utf-8")
    with open("results_axis0_historyop_rec_suite_v1.json", "wb") as f:
        f.write(raw)

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(pack))

    print("DONE: results_axis0_historyop_rec_suite_v1.json + sim_evidence_pack.txt")

if __name__ == "__main__":
    main()