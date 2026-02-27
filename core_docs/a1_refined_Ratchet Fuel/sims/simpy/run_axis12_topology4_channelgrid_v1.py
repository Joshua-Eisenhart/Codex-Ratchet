#!/usr/bin/env python3
# run_axis12_topology4_channelgrid_v1.py
#
# Outputs:
#   results_axis12_topology4_channelgrid_v1.json
#   sim_evidence_pack.txt  (SIM_EVIDENCE for S_SIM_AXIS12_TOPOLOGY4_CHANNELGRID_V1)
#
# Tests:
# - Axis1 proxy: deltaH_absmean under H=Z
# - Axis2 proxy: lin_err_mean (convexity deviation) to detect adaptive/nonlinear updates
# - Axis3 proxy: sign(+/-) of Weyl unitary U(sign) around channels
# - Negative control: choose commuting unitary axis n=(0,0,1) so sign should not matter

from __future__ import annotations
import json, hashlib, os
import numpy as np

EPS = 1e-16

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

def hermitize(r: np.ndarray) -> np.ndarray:
    return (r + r.conj().T) / 2.0

def normalize_dm(r: np.ndarray) -> np.ndarray:
    tr = np.trace(r)
    if abs(tr) < EPS:
        return I2/2
    r = r / tr
    r = hermitize(r)
    w, v = np.linalg.eigh(r)
    w = np.clip(w.real, 0.0, None)
    r = v @ np.diag(w) @ v.conj().T
    tr2 = np.trace(r)
    return r / tr2 if abs(tr2) > EPS else I2/2

def random_dm_1q(rng: np.random.Generator) -> np.ndarray:
    m = rng.normal(size=(2,2)) + 1j*rng.normal(size=(2,2))
    r = m @ m.conj().T
    return normalize_dm(r)

def frob(a: np.ndarray) -> float:
    return float(np.sqrt(np.real(np.trace(a.conj().T @ a))))

def vn_entropy(r: np.ndarray) -> float:
    w = np.linalg.eigvalsh(r).real
    w = np.clip(w, EPS, 1.0)
    return float(-(w * np.log(w)).sum())

def H_expect(r: np.ndarray, H: np.ndarray) -> float:
    return float(np.real(np.trace(H @ r)))

def expm_2x2(a: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eig(a)
    return (v @ np.diag(np.exp(w)) @ np.linalg.inv(v)).astype(complex)

def unitary_from_axis(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = np.array(n, float)
    n = n / np.linalg.norm(n)
    HH = n[0]*X + n[1]*Y + n[2]*Z
    return expm_2x2(-1j * sign * theta * HH)

def apply_unitary(rho: np.ndarray, U: np.ndarray) -> np.ndarray:
    out = U @ rho @ U.conj().T
    return normalize_dm(out)

# --- channel families ---
def chan_amp_damp(rho: np.ndarray, gamma: float) -> np.ndarray:
    gamma = float(np.clip(gamma, 0.0, 1.0))
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    out = E0 @ rho @ E0.conj().T + E1 @ rho @ E1.conj().T
    return normalize_dm(out)

def chan_dephase_z(rho: np.ndarray, q: float) -> np.ndarray:
    q = float(np.clip(q, 0.0, 1.0))
    out = (1-q)*rho + q*(Z @ rho @ Z)
    return normalize_dm(out)

def param_fixed(p0: float, _rho: np.ndarray) -> float:
    return float(p0)

def param_adapt(p0: float, k: float, rho: np.ndarray) -> float:
    hz = H_expect(rho, Z)  # in [-1,1]
    p = p0 + k*hz
    return float(np.clip(p, 0.0, 1.0))

def apply_family(rho: np.ndarray, *, axis1: str, axis2: str, p0: float, k: float) -> np.ndarray:
    p = param_fixed(p0, rho) if axis2 == "FX" else param_adapt(p0, k, rho)
    if axis1 == "EO":
        return chan_amp_damp(rho, p)
    return chan_dephase_z(rho, p)

def linearity_error(rng: np.random.Generator, fam_kwargs: dict, trials: int = 512) -> float:
    errs = []
    p_mix = 0.37
    for _ in range(trials):
        r1 = random_dm_1q(rng)
        r2 = random_dm_1q(rng)
        rm = normalize_dm(p_mix*r1 + (1-p_mix)*r2)
        a = apply_family(rm, **fam_kwargs)
        b = normalize_dm(p_mix*apply_family(r1, **fam_kwargs) + (1-p_mix)*apply_family(r2, **fam_kwargs))
        errs.append(frob(a - b))
    return float(np.mean(errs))

def suite(seed: int = 0, num_states: int = 4096, lin_trials: int = 512) -> dict:
    rng = np.random.default_rng(seed)
    H = Z
    p0 = 0.12
    k  = 0.18

    fams = [("EO","FX"),("EO","AD"),("EC","FX"),("EC","AD")]

    n_test = (0.3, 0.4, 0.866025403784)  # non-commuting with Z
    n_ctrl = (0.0, 0.0, 1.0)              # commutes with Z
    theta  = 0.07

    out = {
        "seed": seed,
        "num_states": num_states,
        "lin_trials": lin_trials,
        "H": "Z",
        "p0": p0,
        "k": k,
        "theta": theta,
        "n_test": list(n_test),
        "n_ctrl": list(n_ctrl),
        "families": {},
    }

    states = [random_dm_1q(rng) for _ in range(num_states)]

    def run_case(n_vec, sign, axis1, axis2):
        U = unitary_from_axis(np.array(n_vec,float), theta, sign)
        deltas, dS = [], []
        for rho in states:
            e0 = H_expect(rho, H)
            r1 = apply_unitary(rho, U)
            r2 = apply_family(r1, axis1=axis1, axis2=axis2, p0=p0, k=k)
            e1 = H_expect(r2, H)
            deltas.append(abs(e1 - e0))
            dS.append(vn_entropy(r2) - vn_entropy(rho))
        lin_err = linearity_error(rng, {"axis1":axis1, "axis2":axis2, "p0":p0, "k":k}, trials=lin_trials)
        return float(np.mean(deltas)), float(np.max(deltas)), float(np.mean(dS)), float(lin_err)

    for axis1, axis2 in fams:
        key = f"{axis1}_{axis2}"

        # TEST axis: sign should matter (generally)
        tp_m, tp_M, tp_dS, tp_lin = run_case(n_test, +1, axis1, axis2)
        tm_m, tm_M, tm_dS, tm_lin = run_case(n_test, -1, axis1, axis2)

        # CONTROL axis: sign should not matter much (commuting)
        cp_m, cp_M, cp_dS, cp_lin = run_case(n_ctrl, +1, axis1, axis2)
        cm_m, cm_M, cm_dS, cm_lin = run_case(n_ctrl, -1, axis1, axis2)

        out["families"][key] = {
            "TEST_plus_deltaH_absmean": tp_m,
            "TEST_minus_deltaH_absmean": tm_m,
            "TEST_delta_deltaH_absmean": float(tp_m - tm_m),
            "CTRL_plus_deltaH_absmean": cp_m,
            "CTRL_minus_deltaH_absmean": cm_m,
            "CTRL_delta_deltaH_absmean": float(cp_m - cm_m),
            "TEST_plus_dS_mean": tp_dS,
            "TEST_minus_dS_mean": tm_dS,
            "CTRL_plus_dS_mean": cp_dS,
            "CTRL_minus_dS_mean": cm_dS,
            "lin_err_mean": tp_lin,  # axis2 indicator; should be >>0 mainly for AD
        }

    return out

def emit_sim_evidence(sim_id: str, code_hash: str, out_hash: str, metrics: dict) -> str:
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append(f"SIM_ID: {sim_id}")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for fam_key, fam_vals in metrics["families"].items():
        for mk, mv in fam_vals.items():
            lines.append(f"METRIC: {fam_key}_{mk}={mv}")
    lines.append(f"EVIDENCE_SIGNAL {sim_id} CORR E_SIM_AXIS12_TOPOLOGY4_CHANNELGRID_V1")
    lines.append("END SIM_EVIDENCE v1")
    return "\n".join(lines) + "\n"

def main():
    sim_id = "S_SIM_AXIS12_TOPOLOGY4_CHANNELGRID_V1"
    out = suite(seed=0, num_states=4096, lin_trials=512)
    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_axis12_topology4_channelgrid_v1.json", "wb") as f:
        f.write(raw)
    code_hash = sha256_file(os.path.abspath(__file__))
    block = emit_sim_evidence(sim_id, code_hash, out_hash, out)
    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write(block)
    print("DONE")

if __name__ == "__main__":
    main()