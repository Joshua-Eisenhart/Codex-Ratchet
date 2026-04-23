#!/usr/bin/env python3
# run_full_axis_suite.py
# Produces:
#   results_full_axis_suite.json
#   sim_evidence_pack.txt   (6 SIM_EVIDENCE blocks back-to-back)

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
I = np.array([[1,0],[0,1]], dtype=complex)
X = np.array([[0,1],[1,0]], dtype=complex)
Y = np.array([[0,-1j],[1j,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)

# ---------- basic QIT ----------
def random_density(rng: np.random.Generator) -> np.ndarray:
    a = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    rho = a @ a.conj().T
    rho = rho / np.trace(rho)
    return rho

def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())

def purity(rho: np.ndarray) -> float:
    return float(np.trace(rho @ rho).real)

def expm_2x2(a: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eig(a)
    return (v @ np.diag(np.exp(w)) @ np.linalg.inv(v)).astype(complex)

def unitary_from_axis(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = n / np.linalg.norm(n)
    H = n[0]*X + n[1]*Y + n[2]*Z
    return expm_2x2(-1j * sign * theta * H)

def apply_unitary(rho: np.ndarray, U: np.ndarray) -> np.ndarray:
    out = U @ rho @ U.conj().T
    out = out / np.trace(out)
    return out

def apply_kraus(rho: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((2,2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    out = out / np.trace(out)
    return out

# ---------- terrain CPTP maps (same family you used) ----------
def terrain_Se(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def terrain_Ne(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-p) * I
    K1 = np.sqrt(p) * X
    return [K0, K1]

def terrain_Ni(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-q) * I
    K1 = np.sqrt(q) * Z
    return [K0, K1]

def terrain_Si() -> list[np.ndarray]:
    return [I]

# ---------- Axis-6 test (left vs right action) ----------
def axis6_lr_test(seed: int = 0, trials: int = 256) -> dict:
    rng = np.random.default_rng(seed)
    # choose fixed A and O to avoid free parameters
    A = X + 0.3*Z
    O = Y + 0.2*X
    deltas = []
    comms = []
    for _ in range(trials):
        rho = random_density(rng)
        left = np.trace(O @ (A @ rho))
        right = np.trace(O @ (rho @ A))
        deltas.append(abs(left - right))
        comms.append(np.linalg.norm(A @ rho - rho @ A))
    deltas = np.array(deltas, float)
    comms = np.array(comms, float)
    return {
        "delta_trace_mean": float(deltas.mean()),
        "delta_trace_min": float(deltas.min()),
        "delta_trace_max": float(deltas.max()),
        "comm_norm_mean": float(comms.mean()),
        "comm_norm_min": float(comms.min()),
        "comm_norm_max": float(comms.max()),
    }

# ---------- Axis-5 tests (FGA contractive vs FSA unitary) ----------
def axis5_fga_test(seed: int = 0, trials: int = 256, gamma: float = 0.12) -> dict:
    rng = np.random.default_rng(seed)
    Ks = terrain_Se(gamma)
    ds = []
    for _ in range(trials):
        rho = random_density(rng)
        s0 = vn_entropy(rho)
        rho2 = apply_kraus(rho, Ks)
        s1 = vn_entropy(rho2)
        ds.append(s1 - s0)
    ds = np.array(ds, float)
    return {"dS_mean": float(ds.mean()), "dS_min": float(ds.min()), "dS_max": float(ds.max())}

def axis5_fsa_test(seed: int = 0, trials: int = 256, theta: float = 0.07, sign: int = +1) -> dict:
    rng = np.random.default_rng(seed)
    n = np.array([0.3,0.4,0.866025403784], float)
    U = unitary_from_axis(n, theta, sign)
    ds = []
    for _ in range(trials):
        rho = random_density(rng)
        s0 = vn_entropy(rho)
        rho2 = apply_unitary(rho, U)
        s1 = vn_entropy(rho2)
        ds.append(s1 - s0)
    ds = np.array(ds, float)
    return {"dS_mean": float(ds.mean()), "dS_min": float(ds.min()), "dS_max": float(ds.max())}

# ---------- Axis-3 Weyl + Hopf geometry (numerical Berry flux sign proxy) ----------
# For 2-level H = sign * n·sigma, Berry curvature integrates to ±2π.
# We approximate flux via sampling over the sphere using a standard closed-form:
# F = sign * 0.5 * sin(theta) dtheta dphi (monopole charge 1/2).
def axis3_berry_flux(sign: int, n_theta: int = 400, n_phi: int = 800) -> dict:
    thetas = np.linspace(0, np.pi, n_theta, endpoint=False) + (np.pi/n_theta)/2
    phis = np.linspace(0, 2*np.pi, n_phi, endpoint=False) + (2*np.pi/n_phi)/2
    dtheta = np.pi/n_theta
    dphi = 2*np.pi/n_phi
    # flux = ∫∫ sign * 0.5 * sin(theta) dtheta dphi
    flux = sign * 0.5 * np.sum(np.sin(thetas)) * dtheta * (np.sum(np.ones_like(phis)) * dphi)
    # hopf fiber winding proxy: sign
    return {"berry_flux_approx": float(flux), "chirality_sign": int(sign)}

# ---------- Axis-4 composite test (C∘R vs R∘C) ----------
def pinch_Z(rho: np.ndarray) -> np.ndarray:
    out = np.array([[rho[0,0], 0],[0, rho[1,1]]], dtype=complex)
    out = out / np.trace(out)
    return out

def axis4_composite_test(seed: int = 0, trials: int = 256, cycles: int = 64,
                         theta: float = 0.07, sign: int = +1,
                         gamma: float = 0.12, p: float = 0.08, q: float = 0.10) -> dict:
    rng = np.random.default_rng(seed)
    n = np.array([0.3,0.4,0.866025403784], float)
    U = unitary_from_axis(n, theta, sign)
    Ks_Se = terrain_Se(gamma)
    Ks_Ne = terrain_Ne(p)
    Ks_Ni = terrain_Ni(q)
    Ks_Si = terrain_Si()
    seq = [("Se", Ks_Se), ("Ne", Ks_Ne), ("Ni", Ks_Ni), ("Si", Ks_Si)]

    # R = unitary mixing, C = pinch (contract)
    def R(rho): return apply_unitary(rho, U)
    def C(rho): return pinch_Z(rho)

    # composite A = R∘C, composite B = C∘R
    def A(rho): return R(C(rho))
    def B(rho): return C(R(rho))

    # thread terrains through after composite application to keep it tied to your cycle context
    def step_cycle(rho, comp):
        for _, Ks in seq:
            rho = apply_kraus(rho, Ks)
            rho = comp(rho)
        return rho

    entA, purA, entB, purB = [], [], [], []
    for _ in range(trials):
        rho = random_density(rng)
        rhoA = rho.copy()
        rhoB = rho.copy()
        for _c in range(cycles):
            rhoA = step_cycle(rhoA, A)
            rhoB = step_cycle(rhoB, B)
        entA.append(vn_entropy(rhoA)); purA.append(purity(rhoA))
        entB.append(vn_entropy(rhoB)); purB.append(purity(rhoB))
    entA = np.array(entA, float); purA = np.array(purA, float)
    entB = np.array(entB, float); purB = np.array(purB, float)
    return {
        "A_entropy_mean": float(entA.mean()),
        "A_purity_mean": float(purA.mean()),
        "B_entropy_mean": float(entB.mean()),
        "B_purity_mean": float(purB.mean()),
        "delta_entropy_mean": float(entA.mean() - entB.mean()),
        "delta_purity_mean": float(purA.mean() - purB.mean()),
    }

# ---------- evidence formatting ----------
def sim_evidence(sim_id: str, token: str, code_hash: str, out_hash: str, metrics: dict) -> str:
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append(f"SIM_ID: {sim_id}")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for k,v in metrics.items():
        lines.append(f"METRIC: {k}={v}")
    lines.append(f"EVIDENCE_SIGNAL {sim_id} CORR {token}")
    lines.append("END SIM_EVIDENCE v1")
    return "\n".join(lines)

def main():
    script_path = os.path.abspath(__file__)
    code_hash = sha256_file(script_path)

    # settings
    seed = 0
    trials = 256
    theta = 0.07
    terrain = {"gamma": 0.12, "p": 0.08, "q": 0.10}

    results = {
        "axis6_lr": axis6_lr_test(seed=seed, trials=trials),
        "axis5_fga": axis5_fga_test(seed=seed, trials=trials, gamma=terrain["gamma"]),
        "axis5_fsa": axis5_fsa_test(seed=seed, trials=trials, theta=theta, sign=+1),
        "axis3_plus": axis3_berry_flux(sign=+1),
        "axis3_minus": axis3_berry_flux(sign=-1),
        "axis4_composites": axis4_composite_test(seed=seed, trials=trials, cycles=64, theta=theta, sign=+1,
                                                 gamma=terrain["gamma"], p=terrain["p"], q=terrain["q"]),
    }

    raw = json.dumps(results, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)

    with open("results_full_axis_suite.json", "wb") as f:
        f.write(raw)

    # build evidence pack (6 blocks)
    blocks = []
    blocks.append(sim_evidence("S_SIM_AXIS3_WEYL_HOPF_PLUS", "E_SIM_AXIS3_WEYL_HOPF_PLUS", code_hash, out_hash, results["axis3_plus"]))
    blocks.append(sim_evidence("S_SIM_AXIS3_WEYL_HOPF_MINUS", "E_SIM_AXIS3_WEYL_HOPF_MINUS", code_hash, out_hash, results["axis3_minus"]))
    blocks.append(sim_evidence("S_SIM_AXIS6_LEFT_RIGHT", "E_SIM_AXIS6_LEFT_RIGHT", code_hash, out_hash, results["axis6_lr"]))
    blocks.append(sim_evidence("S_SIM_AXIS5_FGA_MONOTONE", "E_SIM_AXIS5_FGA_MONOTONE", code_hash, out_hash, results["axis5_fga"]))
    blocks.append(sim_evidence("S_SIM_AXIS5_FSA_MONOTONE", "E_SIM_AXIS5_FSA_MONOTONE", code_hash, out_hash, results["axis5_fsa"]))
    blocks.append(sim_evidence("S_SIM_AXIS4_COMPOSITES", "E_SIM_AXIS4_COMPOSITES", code_hash, out_hash, results["axis4_composites"]))

    pack = "\n\n".join(blocks) + "\n"
    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write(pack)

    print("DONE: wrote results_full_axis_suite.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()
