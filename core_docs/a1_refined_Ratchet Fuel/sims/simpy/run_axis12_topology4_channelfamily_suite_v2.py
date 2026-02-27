#!/usr/bin/env python3
# run_axis12_topology4_channelfamily_suite_v2.py
#
# Produces:
#   results_axis12_topology4_channelfamily_suite_v2.json
#   sim_evidence_pack.txt  (SIM_EVIDENCE for S_SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_SUITE_V2)
#
# What it tests (math-only):
# - Axis-1 signal proxy: change in H expectation under a channel family (deltaH_absmean)
# - Axis-2 signal proxy: linearity/convexity deviation (lin_err_mean) between fixed vs state-adaptive updates
# - Topology4 = 2x2 product of {Energy-Open vs Energy-Closed} x {Channel-Fixed vs Channel-Adaptive}

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
    # tiny PSD repair if needed
    w, v = np.linalg.eigh(r)
    w = np.clip(w.real, 0.0, None)
    r = (v @ np.diag(w) @ v.conj().T)
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

# -------- Channel families --------
# Energy-Open representative (EO): amplitude damping (changes <Z> typically)
def chan_amp_damp(rho: np.ndarray, gamma: float) -> np.ndarray:
    gamma = float(np.clip(gamma, 0.0, 1.0))
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    out = E0 @ rho @ E0.conj().T + E1 @ rho @ E1.conj().T
    return normalize_dm(out)

# Energy-Closed representative (EC): dephasing about Z (commutes with Z, preserves <Z>)
def chan_dephase_z(rho: np.ndarray, q: float) -> np.ndarray:
    q = float(np.clip(q, 0.0, 1.0))
    out = (1-q)*rho + q*(Z @ rho @ Z)
    return normalize_dm(out)

# Axis-2: parameter selection rule
# - Fixed: constant p0
# - Adaptive: depends on state via H_expect(Z) (nonlinear update)
def param_fixed(p0: float, _rho: np.ndarray) -> float:
    return float(p0)

def param_adapt(p0: float, k: float, rho: np.ndarray) -> float:
    hz = H_expect(rho, Z)  # in [-1,1]
    p = p0 + k*hz
    return float(np.clip(p, 0.0, 1.0))

def apply_family(rho: np.ndarray, *, axis1: str, axis2: str, p0: float, k: float) -> np.ndarray:
    # axis1: "EO" or "EC"
    # axis2: "FX" or "AD"
    if axis2 == "FX":
        p = param_fixed(p0, rho)
    else:
        p = param_adapt(p0, k, rho)

    if axis1 == "EO":
        return chan_amp_damp(rho, p)
    else:
        return chan_dephase_z(rho, p)

def linearity_error(rng: np.random.Generator, fam_kwargs: dict, trials: int = 512) -> float:
    # measures || Phi(p*r1+(1-p)*r2) - (p*Phi(r1)+(1-p)*Phi(r2)) ||_F
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

    # Base params
    p0 = 0.12  # base strength
    k  = 0.18  # adaptive slope (creates nonlinearity in AD cases)

    # Topology4 families = {EO,EC} x {FX,AD}
    fams = [
        ("EO","FX"),  # energy-open + fixed channel
        ("EO","AD"),  # energy-open + state-adaptive channel
        ("EC","FX"),  # energy-closed + fixed channel
        ("EC","AD"),  # energy-closed + state-adaptive channel
    ]

    out = {
        "seed": seed,
        "num_states": num_states,
        "lin_trials": lin_trials,
        "H": "Z",
        "p0": p0,
        "k": k,
        "families": {},
    }

    # sample states once for deltaH stats
    states = [random_dm_1q(rng) for _ in range(num_states)]

    for axis1, axis2 in fams:
        key = f"{axis1}_{axis2}"
        deltas = []
        min_eigs = []
        ent_dS = []

        for rho in states:
            e0 = H_expect(rho, H)
            rho2 = apply_family(rho, axis1=axis1, axis2=axis2, p0=p0, k=k)
            e1 = H_expect(rho2, H)
            deltas.append(abs(e1 - e0))

            w = np.linalg.eigvalsh(rho2).real
            min_eigs.append(float(np.min(w)))

            ent_dS.append(vn_entropy(rho2) - vn_entropy(rho))

        lin_err = linearity_error(rng, {"axis1":axis1, "axis2":axis2, "p0":p0, "k":k}, trials=lin_trials)

        out["families"][key] = {
            "deltaH_absmean": float(np.mean(deltas)),
            "deltaH_absmax": float(np.max(deltas)),
            "min_eig_min": float(np.min(min_eigs)),
            "dS_mean": float(np.mean(ent_dS)),
            "lin_err_mean": float(lin_err),
        }

    return out

def emit_sim_evidence(sim_id: str, code_hash: str, out_hash: str, metrics: dict) -> str:
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append(f"SIM_ID: {sim_id}")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")

    # flatten metrics
    for fam_key, fam_vals in metrics["families"].items():
        for mk, mv in fam_vals.items():
            lines.append(f"METRIC: {fam_key}_{mk}={mv}")

    lines.append(f"EVIDENCE_SIGNAL {sim_id} CORR E_SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_SUITE_V2")
    lines.append("END SIM_EVIDENCE v1")
    return "\n".join(lines) + "\n"

def main():
    sim_id = "S_SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_SUITE_V2"
    out = suite(seed=0, num_states=4096, lin_trials=512)

    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)

    with open("results_axis12_topology4_channelfamily_suite_v2.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    block = emit_sim_evidence(sim_id, code_hash, out_hash, out)
    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write(block)

    print("DONE")
    print("  results_axis12_topology4_channelfamily_suite_v2.json")
    print("  sim_evidence_pack.txt")

if __name__ == "__main__":
    main()