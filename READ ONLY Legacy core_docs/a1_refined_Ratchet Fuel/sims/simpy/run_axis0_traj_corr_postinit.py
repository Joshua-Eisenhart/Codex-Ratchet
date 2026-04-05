#!/usr/bin/env python3
# run_axis0_traj_corr_postinit.py
# Outputs:
#   results_axis0_traj_corr_postinit.json
#   sim_evidence_pack_postinit.txt

from __future__ import annotations

import argparse
import importlib.util
import json
import hashlib
import os
from pathlib import Path

import numpy as np


BASE_RUNNER = Path(__file__).with_name("run_axis0_traj_corr_metrics.py")


def load_base_module():
    spec = importlib.util.spec_from_file_location("axis0_traj_base", BASE_RUNNER)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute Bell-vs-Ginibre post-init trajectory negativity.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--trials", type=int, default=256)
    parser.add_argument("--cycles", type=int, default=64)
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


def run_postinit_branch(mod, seq, *, seed: int, trials: int, cycles: int, axis3_sign: int,
                        theta: float, n_vec: tuple[float, float, float], params: dict,
                        entangle_reps: int, init_mode: str) -> dict:
    rng = np.random.default_rng(seed)
    U = mod.unitary_from_axis(np.array(n_vec, float), theta, axis3_sign)

    SAgB_ts = np.zeros((trials, cycles + 1), float)
    MI_ts = np.zeros((trials, cycles + 1), float)

    for t in range(trials):
        rho = mod.bell_seed_state(rng) if init_mode == "BELL" else mod.ginibre_density(4, rng)
        mi0, s0 = mod.mi_and_sAgB(rho)
        MI_ts[t, 0] = mi0
        SAgB_ts[t, 0] = s0

        for c in range(1, cycles + 1):
            for terr in seq:
                Ks = mod.TERRAIN[terr](params)
                rho = mod.apply_unitary_A(rho, U)
                rho = mod.apply_kraus_A(rho, Ks)
                for _ in range(entangle_reps):
                    rho = mod.apply_unitary_AB(rho, mod.CNOT)

            mi, sAgB = mod.mi_and_sAgB(rho)
            MI_ts[t, c] = mi
            SAgB_ts[t, c] = sAgB

    post = SAgB_ts[:, 1:]
    return {
        "MI_init_mean": float(MI_ts[:, 0].mean()),
        "MI_final_mean": float(MI_ts[:, -1].mean()),
        "MI_traj_mean": float(MI_ts.mean()),
        "SAgB_init_mean": float(SAgB_ts[:, 0].mean()),
        "SAgB_final_mean": float(SAgB_ts[:, -1].mean()),
        "SAgB_traj_mean": float(SAgB_ts.mean()),
        "SAgB_traj_neg_frac": float((SAgB_ts < 0.0).mean()),
        "SAgB_postinit_neg_frac": float((post < 0.0).mean()),
        "SAgB_postinit_mean": float(post.mean()),
        "SAgB_postinit_min": float(post.min()),
        "SAgB_postinit_max": float(post.max()),
    }


def main() -> int:
    mod = load_base_module()
    args = build_parser().parse_args()

    seq01 = ["Se", "Ne", "Ni", "Si"]
    seq02 = ["Se", "Si", "Ni", "Ne"]
    params = {"gamma": args.gamma, "p": args.p, "q": args.q}
    n_vec = (args.nx, args.ny, args.nz)

    out = {
        "seed": args.seed,
        "trials": args.trials,
        "cycles": args.cycles,
        "axis3_sign": args.axis3_sign,
        "theta": args.theta,
        "n_vec": list(n_vec),
        "terrain_params": dict(params),
        "entangle_reps": args.entangle_reps,
        "SEQ01": seq01,
        "SEQ02": seq02,
    }

    for init_mode in ["GINIBRE", "BELL"]:
        r1 = run_postinit_branch(
            mod,
            seq01,
            seed=args.seed,
            trials=args.trials,
            cycles=args.cycles,
            axis3_sign=args.axis3_sign,
            theta=args.theta,
            n_vec=n_vec,
            params=params,
            entangle_reps=args.entangle_reps,
            init_mode=init_mode,
        )
        r2 = run_postinit_branch(
            mod,
            seq02,
            seed=args.seed,
            trials=args.trials,
            cycles=args.cycles,
            axis3_sign=args.axis3_sign,
            theta=args.theta,
            n_vec=n_vec,
            params=params,
            entangle_reps=args.entangle_reps,
            init_mode=init_mode,
        )
        out[f"{init_mode}_SEQ01"] = r1
        out[f"{init_mode}_SEQ02"] = r2
        out[f"{init_mode}_delta_SAgB_postinit_neg_frac_SEQ02_minus_SEQ01"] = float(
            r2["SAgB_postinit_neg_frac"] - r1["SAgB_postinit_neg_frac"]
        )
        out[f"{init_mode}_delta_SAgB_postinit_mean_SEQ02_minus_SEQ01"] = float(
            r2["SAgB_postinit_mean"] - r1["SAgB_postinit_mean"]
        )

    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)

    with open("results_axis0_traj_corr_postinit.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_AXIS0_TRAJ_CORR_POSTINIT")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for init_mode in ["GINIBRE", "BELL"]:
        for k, v in out[f"{init_mode}_SEQ01"].items():
            lines.append(f"METRIC: {init_mode}_SEQ01_{k}={v}")
        for k, v in out[f"{init_mode}_SEQ02"].items():
            lines.append(f"METRIC: {init_mode}_SEQ02_{k}={v}")
        lines.append(
            f"METRIC: {init_mode}_delta_SAgB_postinit_neg_frac_SEQ02_minus_SEQ01="
            f"{out[f'{init_mode}_delta_SAgB_postinit_neg_frac_SEQ02_minus_SEQ01']}"
        )
        lines.append(
            f"METRIC: {init_mode}_delta_SAgB_postinit_mean_SEQ02_minus_SEQ01="
            f"{out[f'{init_mode}_delta_SAgB_postinit_mean_SEQ02_minus_SEQ01']}"
        )
    lines.append("EVIDENCE_SIGNAL S_SIM_AXIS0_TRAJ_CORR_POSTINIT CORR E_SIM_AXIS0_TRAJ_CORR_POSTINIT")
    lines.append("END SIM_EVIDENCE v1")

    with open("sim_evidence_pack_postinit.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("DONE: wrote results_axis0_traj_corr_postinit.json and sim_evidence_pack_postinit.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
