#!/usr/bin/env python3
"""Standalone replication for UP-100 16/16 stage re-identification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def complex_matrix(rows):
    def cell(value):
        if isinstance(value, list) and len(value) == 2 and all(isinstance(x, (int, float)) for x in value):
            return complex(value[0], value[1])
        return complex(value, 0.0)

    return np.array([[cell(value) for value in row] for row in rows], dtype=complex)


def load_spec(path: Path) -> dict:
    return json.loads(path.read_text())


class StageEngine:
    def __init__(self, spec: dict):
        generator = spec["generator"]
        constants = generator["constants"]
        self.g = float(constants["G"])
        self.kap = float(constants["KAP"])
        self.q = float(constants["Q"])
        self.t_flow = float(constants["T_FLOW"])
        self.n_steps = int(constants["N_STEPS"])
        self.n_probes = int(constants["N_PROBES"])
        self.radius = float(constants["RADIUS"])

        matrices = generator["pauli_matrices"]
        self.i2 = complex_matrix(matrices["I2"])
        self.sx = complex_matrix(matrices["sx"])
        self.sy = complex_matrix(matrices["sy_complex"])
        self.sz = complex_matrix(matrices["sz"])
        self.sp = complex_matrix(matrices["sigma_plus_complex"])
        self.sm = complex_matrix(matrices["sigma_minus_complex"])
        self.h0 = complex_matrix(matrices["H0_complex"])

        ops = generator["operators"]
        self.p0 = complex_matrix(ops["Ti"]["P0"])
        self.p1 = complex_matrix(ops["Ti"]["P1"])
        self.qp = complex_matrix(ops["Te"]["Qp"])
        self.qm = complex_matrix(ops["Te"]["Qm"])
        self.ux = complex_matrix(ops["Fi"]["Ux_complex"])
        self.uz = complex_matrix(ops["Fe"]["Uz_complex"])

        self.terrains = generator["terrain_generators"]
        self.native = generator["native_operators"]

    def dissipator(self, op_l: np.ndarray, rho: np.ndarray) -> np.ndarray:
        ldag_l = op_l.conj().T @ op_l
        return op_l @ rho @ op_l.conj().T - 0.5 * (ldag_l @ rho + rho @ ldag_l)

    def terrain_rhs(self, name: str):
        terrain = self.terrains[name]
        eps = float(terrain["eps"])
        kind = terrain["kind"]
        pole = int(terrain["pole"])
        hamiltonian = eps * self.h0

        def rhs(rho: np.ndarray) -> np.ndarray:
            out = -1j * self.g * (hamiltonian @ rho - rho @ hamiltonian)
            if kind == "damp":
                out = out + self.kap * self.dissipator(self.sp if pole > 0 else self.sm, rho)
            elif kind == "depol":
                out = out + 0.5 * self.kap * (self.dissipator(self.sx, rho) + self.dissipator(self.sy, rho))
            elif kind == "proj":
                out = out + self.kap * self.dissipator(self.sz, rho)
            else:
                raise ValueError(f"unknown terrain kind {kind!r}")
            return out

        return rhs

    def operator_channel(self, name: str):
        if name == "Ti":
            return lambda rho: (1.0 - self.q) * rho + self.q * (self.p0 @ rho @ self.p0 + self.p1 @ rho @ self.p1)
        if name == "Te":
            return lambda rho: (1.0 - self.q) * rho + self.q * (self.qp @ rho @ self.qp + self.qm @ rho @ self.qm)
        if name == "Fi":
            return lambda rho: self.ux @ rho @ self.ux.conj().T
        if name == "Fe":
            return lambda rho: self.uz @ rho @ self.uz.conj().T
        raise ValueError(f"unknown operator {name!r}")

    def normalize_rho(self, rho: np.ndarray) -> np.ndarray:
        rho = 0.5 * (rho + rho.conj().T)
        return rho / np.trace(rho).real

    def flow(self, rhs, rho: np.ndarray) -> np.ndarray:
        dt = self.t_flow / self.n_steps
        for _ in range(self.n_steps):
            k1 = rhs(rho)
            k2 = rhs(rho + 0.5 * dt * k1)
            k3 = rhs(rho + 0.5 * dt * k2)
            k4 = rhs(rho + dt * k3)
            rho = self.normalize_rho(rho + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4))
        return rho

    def stage_channels(self):
        channels = []
        for terrain_name in sorted(self.terrains, key=lambda value: int(value[1:])):
            rhs = self.terrain_rhs(terrain_name)
            for operator_name in self.native[terrain_name]:
                op = self.operator_channel(operator_name)
                label = f"{terrain_name}:{operator_name}"
                channels.append((label, lambda rho, rhs=rhs, op=op: op(self.flow(rhs, rho.copy()))))
        return channels

    def bloch(self, rho: np.ndarray) -> np.ndarray:
        return np.array([float(np.trace(rho @ s).real) for s in (self.sx, self.sy, self.sz)])

    def rho_from_bloch(self, vector: np.ndarray) -> np.ndarray:
        return 0.5 * (self.i2 + vector[0] * self.sx + vector[1] * self.sy + vector[2] * self.sz)

    def probe_family(self, seed: int):
        rng = np.random.default_rng(seed)
        probes = []
        for _ in range(self.n_probes):
            vector = rng.normal(size=3)
            vector = self.radius * vector / np.linalg.norm(vector)
            probes.append(self.rho_from_bloch(vector))
        return probes

    def affine_signature(self, channel, probes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        inputs = np.array([self.bloch(probe) for probe in probes])
        outputs = np.array([self.bloch(channel(probe)) for probe in probes])
        augmented = np.hstack([inputs, np.ones((len(inputs), 1))])
        fitted, *_ = np.linalg.lstsq(augmented, outputs, rcond=None)
        a_matrix = fitted[:3, :].T
        b_vector = fitted[3, :]
        full_affine = np.concatenate([b_vector, a_matrix.reshape(-1)])
        return full_affine, a_matrix, b_vector


def seed_plan(seed: int) -> dict:
    return {
        "train_seed": 2 * seed + 101,
        "novel_seed": 2 * seed + 202,
        "noise_check_seed": 2 * seed + 303,
    }


def distance_matrix(left, right) -> np.ndarray:
    return np.array([[float(np.linalg.norm(left[i] - right[j])) for j in range(len(right))] for i in range(len(left))])


def nearest_results(distances: np.ndarray, names: list[str]) -> dict:
    n_items = len(names)
    nearest = np.argmin(distances, axis=1)
    self_distances = distances[np.arange(n_items), np.arange(n_items)]
    wrong_distances = distances.copy()
    np.fill_diagonal(wrong_distances, np.inf)
    nearest_wrong = np.min(wrong_distances, axis=1)
    margins = nearest_wrong - self_distances
    misses = [
        {"stage": names[i], "nearest": names[int(nearest[i])], "distance": float(distances[i, int(nearest[i])])}
        for i in range(n_items)
        if int(nearest[i]) != i
    ]
    return {
        "correct": int(np.sum(nearest == np.arange(n_items))),
        "total": n_items,
        "misses": misses,
        "max_self_noise": float(np.max(self_distances)),
        "min_self_noise": float(np.min(self_distances)),
        "min_nearest_wrong_distance": float(np.min(nearest_wrong)),
        "min_separation_margin": float(np.min(margins)),
        "per_stage_margin": {names[i]: float(margins[i]) for i in range(n_items)},
    }


def mirror_pair_contrast(names: list[str], a_train: list[np.ndarray], svd_train: list[np.ndarray], pairs: list[list[str]]):
    rows = []
    for left, right in pairs:
        i = names.index(left)
        j = names.index(right)
        rows.append(
            {
                "pair": [left, right],
                "full_A_distance": float(np.linalg.norm(a_train[i] - a_train[j])),
                "svd_A_distance": float(np.linalg.norm(svd_train[i] - svd_train[j])),
            }
        )
    return rows


def run(seed: int, spec: dict) -> dict:
    engine = StageEngine(spec)
    channels = engine.stage_channels()
    names = [label for label, _ in channels]
    seeds = seed_plan(seed)

    train_probes = engine.probe_family(seeds["train_seed"])
    novel_probes = engine.probe_family(seeds["novel_seed"])

    train = [engine.affine_signature(channel, train_probes) for _, channel in channels]
    novel = [engine.affine_signature(channel, novel_probes) for _, channel in channels]
    train_full = [row[0] for row in train]
    novel_full = [row[0] for row in novel]
    train_a = [row[1] for row in train]
    novel_a = [row[1] for row in novel]

    full_distances = distance_matrix(novel_full, train_full)
    full = nearest_results(full_distances, names)

    train_svd = [np.linalg.svd(a_matrix, compute_uv=False) for a_matrix in train_a]
    novel_svd = [np.linalg.svd(a_matrix, compute_uv=False) for a_matrix in novel_a]
    svd_distances = distance_matrix(novel_svd, train_svd)
    svd = nearest_results(svd_distances, names)

    mirror_contrast = mirror_pair_contrast(names, train_a, train_svd, spec["chirality_mirror_pairs"])
    svd_mirror_failures = [
        row for row in mirror_contrast if row["svd_A_distance"] < 1e-10 and row["full_A_distance"] > 1e-3
    ]
    separation_gate = bool(full["min_separation_margin"] > 10.0 * full["max_self_noise"])
    full_gate = bool(full["correct"] == full["total"])
    svd_gate = bool(svd["correct"] < svd["total"] and len(svd_mirror_failures) > 0)
    passed = bool(full_gate and separation_gate and svd_gate)

    return {
        "packet_id": spec["packet_id"],
        "seed": seed,
        "seed_plan": seeds,
        "stage_names": names,
        "full_affine_reidentification": full,
        "svd_only_contrast": {
            **svd,
            "chirality_mirror_pair_distances": mirror_contrast,
            "mirror_pairs_collapsed_under_svd": svd_mirror_failures,
        },
        "criteria": {
            "full_affine_16_of_16": full_gate,
            "separation_gt_10x_self_noise": separation_gate,
            "svd_variant_less_than_16_of_16_with_mirror_collapse": svd_gate,
        },
        "pass": passed,
        "verdict": "PASS" if passed else "FAIL",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "claim_ceiling": "standalone replication packet only; full affine re-identification and SVD contrast for the UP-100 stage claim",
    }


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run the frozen UP-100 16-stage re-identification replication packet.")
    parser.add_argument("--seed", type=int, required=True, help="Required user-chosen seed.")
    parser.add_argument("--output", type=Path, default=None, help="Optional results JSON path.")
    parser.add_argument("--spec", type=Path, default=Path(__file__).with_name("spec.json"), help="Spec JSON path.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    spec = load_spec(args.spec)
    result = run(args.seed, spec)
    output = args.output if args.output is not None else Path.cwd() / f"results_seed_{args.seed}.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    full = result["full_affine_reidentification"]
    svd = result["svd_only_contrast"]
    print("UP-100 STAGE RE-ID 16/16 REPLICATION")
    print(f"seed: {args.seed}")
    print(f"train_seed: {result['seed_plan']['train_seed']}")
    print(f"novel_seed: {result['seed_plan']['novel_seed']}")
    print(f"full_affine_reidentified: {full['correct']}/{full['total']}")
    print(f"full_affine_max_self_noise: {full['max_self_noise']:.12e}")
    print(f"full_affine_min_nearest_wrong_distance: {full['min_nearest_wrong_distance']:.12e}")
    print(f"full_affine_min_separation_margin: {full['min_separation_margin']:.12e}")
    print(f"separation_gt_10x_self_noise: {result['criteria']['separation_gt_10x_self_noise']}")
    print(f"svd_only_reidentified: {svd['correct']}/{svd['total']}")
    print(f"svd_mirror_collapses: {len(svd['mirror_pairs_collapsed_under_svd'])}")
    if svd["misses"]:
        print(f"svd_misses: {[(row['stage'], row['nearest']) for row in svd['misses']]}")
    print(f"verdict: {result['verdict']}")
    print(f"results_json: {output}")
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
