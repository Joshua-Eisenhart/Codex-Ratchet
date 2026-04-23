#!/usr/bin/env python3
# run_ultra4_full_stack_postinit.py
# Outputs:
#   results_ultra4_full_stack_postinit.json
#   sim_evidence_pack_ultra4_postinit.txt

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

import numpy as np


BASE_RUNNER = Path(__file__).with_name("run_ultra4_full_stack.py")


def load_base_module():
    spec = importlib.util.spec_from_file_location("ultra4_full_stack_base", BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load base runner: {BASE_RUNNER}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def axis0_traj_postinit(mod, seed: int, axis3_sign: int, seq: list[str], direction: str, init_mode: str,
                        trials: int, cycles: int, theta: float, n_vec: np.ndarray,
                        tparams_ab: dict, entangler: np.ndarray, entangle_reps: int) -> dict:
    rng = np.random.default_rng(seed)
    U = mod.unitary_from_axis(n_vec, theta, axis3_sign)
    seq_use = list(seq) if direction == "FWD" else list(reversed(seq))
    neg_post = []
    min_post = []
    mean_post = []
    final_mean = []
    init_mean = []

    for _ in range(trials):
        rho = mod.bell_seed(rng) if init_mode == "BELL" else mod.ginibre_density(4, rng)
        _, s0 = mod.mi_and_sAgB(rho)
        s_series = [s0]
        for _c in range(cycles):
            for terr in seq_use:
                Ks = mod.TERRAIN[terr](tparams_ab)
                rho = mod.apply_unitary_A_AB(rho, U)
                rho = mod.apply_kraus_A_AB(rho, Ks)
                for _k in range(entangle_reps):
                    rho = mod.apply_unitary_AB(rho, entangler)
            _, sAgB = mod.mi_and_sAgB(rho)
            s_series.append(sAgB)
        s_arr = np.array(s_series, float)
        post = s_arr[1:]
        neg_post.append(float(np.mean((post < 0.0).astype(float))))
        min_post.append(float(post.min()))
        mean_post.append(float(post.mean()))
        init_mean.append(float(s_arr[0]))
        final_mean.append(float(s_arr[-1]))

    return {
        "SAgB_init_mean": float(np.mean(init_mean)),
        "SAgB_final_mean": float(np.mean(final_mean)),
        "SAgB_postinit_mean": float(np.mean(mean_post)),
        "SAgB_postinit_min": float(np.mean(min_post)),
        "SAgB_postinit_neg_frac": float(np.mean(neg_post)),
    }


def main() -> int:
    mod = load_base_module()

    seeds = [0, 1, 2, 3]
    axis0_trials = 128
    axis0_cycles = 64
    theta = 0.07
    n_vec = np.array([0.3, 0.4, 0.866025403784], float)
    seqs = {
        "SEQ01": ["Se", "Ne", "Ni", "Si"],
        "SEQ02": ["Se", "Si", "Ni", "Ne"],
        "SEQ03": ["Se", "Ne", "Si", "Ni"],
        "SEQ04": ["Se", "Si", "Ne", "Ni"],
    }
    tparams_ab = {"gamma": 0.02, "p": 0.02, "q": 0.02}
    entanglers = {"CNOT": mod.CNOT, "CZ": mod.CZ}
    entangle_reps_list = [1, 2]

    out = {
        "seeds": seeds,
        "axis0_trials": axis0_trials,
        "axis0_cycles": axis0_cycles,
        "theta": theta,
        "n_vec": [float(x) for x in n_vec.tolist()],
        "tparams_ab": dict(tparams_ab),
        "seqs": {"SEQ01": seqs["SEQ01"]},
        "axis0_ab_postinit": {},
    }

    # Narrow to the exact matched-control full-geometry branch the validator needs.
    sign, tag = +1, "T1"
    direction = "FWD"
    ent_name, entU = "CNOT", mod.CNOT
    reps = 1
    seq_name, seq = "SEQ01", seqs["SEQ01"]
    for init_mode in ["GINIBRE", "BELL"]:
        rows = []
        for s in seeds:
            rows.append(
                axis0_traj_postinit(
                    mod,
                    30000 + s,
                    sign,
                    seq,
                    direction,
                    init_mode,
                    axis0_trials,
                    axis0_cycles,
                    theta,
                    n_vec,
                    tparams_ab,
                    entU,
                    reps,
                )
            )
        out["axis0_ab_postinit"][f"{tag}_{direction}_{init_mode}_{ent_name}_R{reps}_{seq_name}"] = {
            "SAgB_init_mean": float(np.mean([r["SAgB_init_mean"] for r in rows])),
            "SAgB_final_mean": float(np.mean([r["SAgB_final_mean"] for r in rows])),
            "SAgB_postinit_mean": float(np.mean([r["SAgB_postinit_mean"] for r in rows])),
            "SAgB_postinit_min": float(np.mean([r["SAgB_postinit_min"] for r in rows])),
            "SAgB_postinit_neg_frac": float(np.mean([r["SAgB_postinit_neg_frac"] for r in rows])),
        }

    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_ultra4_full_stack_postinit.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_ULTRA4_FULL_STACK_POSTINIT")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for key in ["T1_FWD_BELL_CNOT_R1_SEQ01", "T1_FWD_GINIBRE_CNOT_R1_SEQ01"]:
        rec = out["axis0_ab_postinit"][key]
        for metric, value in rec.items():
            lines.append(f"METRIC: {key}_{metric}={value}")
    lines.append("EVIDENCE_SIGNAL S_SIM_ULTRA4_FULL_STACK_POSTINIT CORR E_SIM_ULTRA4_FULL_STACK_POSTINIT")
    lines.append("END SIM_EVIDENCE v1")
    with open("sim_evidence_pack_ultra4_postinit.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_ultra4_full_stack_postinit.json and sim_evidence_pack_ultra4_postinit.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
