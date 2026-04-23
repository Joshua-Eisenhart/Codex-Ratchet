#!/usr/bin/env python3
# run_axis0_tiny_matched_control.py
# Produces:
#   results_axis0_tiny_matched_control.json
#   sim_evidence_pack.txt  (1 SIM_EVIDENCE block for S_SIM_AXIS0_TINY_MATCHED_CONTROL)

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
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)


def expm_2x2(a: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eig(a)
    return (v @ np.diag(np.exp(w)) @ np.linalg.inv(v)).astype(complex)


def unitary_from_axis(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = n / np.linalg.norm(n)
    H = n[0] * X + n[1] * Y + n[2] * Z
    return expm_2x2(-1j * sign * theta * H)


def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())


def partial_trace_AB_to_A(rhoAB: np.ndarray) -> np.ndarray:
    rhoA = np.zeros((2, 2), dtype=complex)
    for a in range(2):
        for ap in range(2):
            s = 0.0 + 0.0j
            for b in range(2):
                i = 2 * a + b
                j = 2 * ap + b
                s += rhoAB[i, j]
            rhoA[a, ap] = s
    return rhoA / np.trace(rhoA)


def partial_trace_AB_to_B(rhoAB: np.ndarray) -> np.ndarray:
    rhoB = np.zeros((2, 2), dtype=complex)
    for b in range(2):
        for bp in range(2):
            s = 0.0 + 0.0j
            for a in range(2):
                i = 2 * a + b
                j = 2 * a + bp
                s += rhoAB[i, j]
            rhoB[b, bp] = s
    return rhoB / np.trace(rhoB)


def mi_and_sAgB(rhoAB: np.ndarray) -> tuple[float, float]:
    rhoA = partial_trace_AB_to_A(rhoAB)
    rhoB = partial_trace_AB_to_B(rhoAB)
    sab = vn_entropy(rhoAB)
    sa = vn_entropy(rhoA)
    sb = vn_entropy(rhoB)
    mi = sa + sb - sab
    sAgB = sab - sb
    return float(mi), float(sAgB)


def ginibre_density(d: int, rng: np.random.Generator) -> np.ndarray:
    a = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    rho = a @ a.conj().T
    return rho / np.trace(rho)


def bell_seed_state(rng: np.random.Generator) -> np.ndarray:
    phi = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    rho = np.outer(phi, phi.conj())
    a = rng.uniform(0, 2 * np.pi)
    b = rng.uniform(0, 2 * np.pi)
    UA = expm_2x2(-1j * a * Z)
    UB = expm_2x2(-1j * b * X)
    rho = (np.kron(UA, I2) @ rho @ np.kron(UA, I2).conj().T) / np.trace(rho)
    rho = (np.kron(I2, UB) @ rho @ np.kron(I2, UB).conj().T) / np.trace(rho)
    return rho


CNOT = np.array(
    [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ],
    dtype=complex,
)


def apply_unitary_A(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UA = np.kron(U, I2)
    out = UA @ rhoAB @ UA.conj().T
    return out / np.trace(out)


def apply_unitary_AB(rhoAB: np.ndarray, UAB: np.ndarray) -> np.ndarray:
    out = UAB @ rhoAB @ UAB.conj().T
    return out / np.trace(out)


def apply_kraus_A(rhoAB: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4, 4), dtype=complex)
    for K in Ks:
        KA = np.kron(K, I2)
        out += KA @ rhoAB @ KA.conj().T
    return out / np.trace(out)


def terrain_Se(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    E1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    return [E0, E1]


def terrain_Ne(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(1 - p) * I2
    K1 = np.sqrt(p) * X
    return [K0, K1]


def terrain_Ni(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(1 - q) * I2
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
               axis3_sign: int, theta: float, n_vec: tuple[float, float, float],
               params: dict, entangle_reps: int, init_mode: str) -> dict:
    rng = np.random.default_rng(seed)
    U = unitary_from_axis(np.array(n_vec, float), theta, axis3_sign)
    mi_list = []
    sagb_list = []

    for _ in range(trials):
        rho = bell_seed_state(rng) if init_mode == "BELL" else ginibre_density(4, rng)
        for _c in range(cycles):
            for terr in seq:
                Ks = TERRAIN[terr](params)
                rho = apply_unitary_A(rho, U)
                rho = apply_kraus_A(rho, Ks)
                for _k in range(entangle_reps):
                    rho = apply_unitary_AB(rho, CNOT)
        mi, sagb = mi_and_sAgB(rho)
        mi_list.append(mi)
        sagb_list.append(sagb)

    mi_arr = np.array(mi_list, float)
    sg_arr = np.array(sagb_list, float)
    return {
        "MI_mean": float(mi_arr.mean()),
        "MI_min": float(mi_arr.min()),
        "MI_max": float(mi_arr.max()),
        "SAgB_mean": float(sg_arr.mean()),
        "SAgB_min": float(sg_arr.min()),
        "SAgB_max": float(sg_arr.max()),
        "neg_SAgB_frac": float(np.mean((sg_arr < 0.0).astype(float))),
    }


def build_parser():
    import argparse

    parser = argparse.ArgumentParser(description="Run the tiny Axis0 Bell-vs-Ginibre matched-control witness.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--trials", type=int, default=8)
    parser.add_argument("--cycles", type=int, default=4)
    parser.add_argument("--axis3-sign", type=int, default=1, choices=[-1, 1])
    parser.add_argument("--theta", type=float, default=0.07)
    parser.add_argument("--nx", type=float, default=0.3)
    parser.add_argument("--ny", type=float, default=0.4)
    parser.add_argument("--nz", type=float, default=0.866025403784)
    parser.add_argument("--gamma", type=float, default=0.02)
    parser.add_argument("--p", type=float, default=0.02)
    parser.add_argument("--q", type=float, default=0.02)
    parser.add_argument("--entangle-reps", type=int, default=1)
    return parser


def main():
    SEQ01 = ["Se", "Ne", "Ni", "Si"]
    SEQ04 = ["Se", "Si", "Ne", "Ni"]
    args = build_parser().parse_args()
    seed = args.seed
    trials = args.trials
    cycles = args.cycles
    axis3_sign = args.axis3_sign
    theta = args.theta
    n_vec = (args.nx, args.ny, args.nz)
    params = {"gamma": args.gamma, "p": args.p, "q": args.q}
    entangle_reps = args.entangle_reps

    out = {
        "seed": seed,
        "trials": trials,
        "cycles": cycles,
        "axis3_sign": axis3_sign,
        "theta": theta,
        "n_vec": list(n_vec),
        "terrain_params": dict(params),
        "entangle_reps": entangle_reps,
        "SEQ01": SEQ01,
        "SEQ04": SEQ04,
    }

    for init_mode in ["GINIBRE", "BELL"]:
        r1 = run_branch(SEQ01, seed=seed, trials=trials, cycles=cycles, axis3_sign=axis3_sign,
                        theta=theta, n_vec=n_vec, params=params, entangle_reps=entangle_reps, init_mode=init_mode)
        r4 = run_branch(SEQ04, seed=seed, trials=trials, cycles=cycles, axis3_sign=axis3_sign,
                        theta=theta, n_vec=n_vec, params=params, entangle_reps=entangle_reps, init_mode=init_mode)
        out[f"{init_mode}_SEQ01"] = r1
        out[f"{init_mode}_SEQ04"] = r4
        out[f"{init_mode}_delta_SAgB_min_SEQ04_minus_SEQ01"] = float(r4["SAgB_min"] - r1["SAgB_min"])
        out[f"{init_mode}_delta_negfrac_SEQ04_minus_SEQ01"] = float(r4["neg_SAgB_frac"] - r1["neg_SAgB_frac"])

    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)

    with open("results_axis0_tiny_matched_control.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_AXIS0_TINY_MATCHED_CONTROL")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for init_mode in ["GINIBRE", "BELL"]:
        for k, v in out[f"{init_mode}_SEQ01"].items():
            lines.append(f"METRIC: {init_mode}_SEQ01_{k}={v}")
        for k, v in out[f"{init_mode}_SEQ04"].items():
            lines.append(f"METRIC: {init_mode}_SEQ04_{k}={v}")
        lines.append(f"METRIC: {init_mode}_delta_SAgB_min_SEQ04_minus_SEQ01={out[f'{init_mode}_delta_SAgB_min_SEQ04_minus_SEQ01']}")
        lines.append(f"METRIC: {init_mode}_delta_negfrac_SEQ04_minus_SEQ01={out[f'{init_mode}_delta_negfrac_SEQ04_minus_SEQ01']}")
    lines.append("EVIDENCE_SIGNAL S_SIM_AXIS0_TINY_MATCHED_CONTROL CORR E_SIM_AXIS0_TINY_MATCHED_CONTROL")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_axis0_tiny_matched_control.json and sim_evidence_pack.txt")


if __name__ == "__main__":
    main()
