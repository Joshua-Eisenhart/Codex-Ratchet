#!/usr/bin/env python3
"""Standalone replication for the frozen T2 order-carried loop result."""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from itertools import permutations
from pathlib import Path

import numpy as np
from scipy.linalg import expm


G = 0.35
KAP = 1.0
T_FLOW = 1.0
N_STEPS = 220
CYCLES = 3
N_PROBES = 9
RADIUS = 0.62
Q = 1.0 - np.exp(-1.0)
TH = np.pi / 4.0
R2_GATE = 0.90

SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)
H0 = (SX + SY + SZ) / np.sqrt(3.0)

TERRAIN = {
    "Se-out": (-1, "damp", -1),
    "Ne-out": (-1, "depol", 0),
    "Ni-out": (-1, "damp", 1),
    "Si-out": (-1, "proj", 0),
}

LOOPS = {
    "Type2-inner-deductive": [
        {"step": 1, "terrain": "Se-out", "operator": "Ti", "axis6_sign": "down"},
        {"step": 2, "terrain": "Ne-out", "operator": "Ti", "axis6_sign": "up"},
        {"step": 3, "terrain": "Ni-out", "operator": "Fe", "axis6_sign": "up"},
        {"step": 4, "terrain": "Si-out", "operator": "Fe", "axis6_sign": "down"},
    ],
    "Type2-outer-inductive": [
        {"step": 1, "terrain": "Se-out", "operator": "Fi", "axis6_sign": "up"},
        {"step": 2, "terrain": "Si-out", "operator": "Te", "axis6_sign": "up"},
        {"step": 3, "terrain": "Ni-out", "operator": "Te", "axis6_sign": "down"},
        {"step": 4, "terrain": "Ne-out", "operator": "Fi", "axis6_sign": "down"},
    ],
}


def density_matrix(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    norm = np.linalg.norm(v)
    if norm >= 0.98:
        v = v / norm * 0.98
    return 0.5 * (I2 + v[0] * SX + v[1] * SY + v[2] * SZ)


def bloch_vector(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.trace(rho @ s).real) for s in (SX, SY, SZ)])


def dissipator(op_l: np.ndarray, rho: np.ndarray) -> np.ndarray:
    ldag_l = op_l.conj().T @ op_l
    return op_l @ rho @ op_l.conj().T - 0.5 * (ldag_l @ rho + rho @ ldag_l)


def terrain_rhs(name: str):
    eps, kind, pole = TERRAIN[name]
    hamiltonian = eps * H0

    def rhs(rho: np.ndarray) -> np.ndarray:
        out = -1j * G * (hamiltonian @ rho - rho @ hamiltonian)
        if kind == "damp":
            out = out + KAP * dissipator(SP if pole > 0 else SM, rho)
        elif kind == "depol":
            out = out + 0.5 * KAP * (dissipator(SX, rho) + dissipator(SY, rho))
        elif kind == "proj":
            out = out + KAP * dissipator(SZ, rho)
        else:
            raise ValueError(f"unknown terrain kind {kind!r}")
        return out

    return rhs


def operator_channel(name: str):
    p0 = 0.5 * (I2 + SZ)
    p1 = 0.5 * (I2 - SZ)
    qp = 0.5 * (I2 + SX)
    qm = 0.5 * (I2 - SX)
    if name == "Ti":
        return lambda rho: (1 - Q) * rho + Q * (p0 @ rho @ p0 + p1 @ rho @ p1)
    if name == "Te":
        return lambda rho: (1 - Q) * rho + Q * (qp @ rho @ qp + qm @ rho @ qm)
    if name == "Fi":
        unitary = expm(-1j * TH / 2.0 * SX)
        return lambda rho: unitary @ rho @ unitary.conj().T
    if name == "Fe":
        unitary = expm(-1j * TH / 2.0 * SZ)
        return lambda rho: unitary @ rho @ unitary.conj().T
    raise ValueError(f"unknown operator {name!r}")


def normalize_rho(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + rho.conj().T)
    return rho / np.trace(rho).real


def rk4_step(rhs, rho: np.ndarray, dt: float) -> np.ndarray:
    k1 = rhs(rho)
    k2 = rhs(rho + 0.5 * dt * k1)
    k3 = rhs(rho + 0.5 * dt * k2)
    k4 = rhs(rho + dt * k3)
    return normalize_rho(rho + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4))


def flow_trajectory(rhs, rho: np.ndarray):
    dt = T_FLOW / N_STEPS
    points = [bloch_vector(rho)]
    for _ in range(N_STEPS):
        rho = rk4_step(rhs, rho, dt)
        points.append(bloch_vector(rho))
    return rho, np.asarray(points), dt


def probe_set(rng: np.random.Generator):
    probes = []
    for _ in range(N_PROBES):
        point = rng.normal(size=3)
        probes.append(RADIUS * point / np.linalg.norm(point))
    return probes


def collect_segment_data(slots, probes):
    segments = [[] for _ in range(4)]
    for probe in probes:
        rho = density_matrix(probe)
        for _ in range(CYCLES):
            for pos, slot in enumerate(slots):
                rhs = terrain_rhs(slot["terrain"])
                op = operator_channel(slot["operator"])
                if slot["axis6_sign"] == "up":
                    rho = normalize_rho(op(rho.copy()))
                    rho, traj, _ = flow_trajectory(rhs, rho)
                elif slot["axis6_sign"] == "down":
                    rho, traj, _ = flow_trajectory(rhs, rho)
                    rho = normalize_rho(op(rho.copy()))
                else:
                    raise ValueError(f"bad axis6_sign {slot['axis6_sign']!r}")
                segments[pos].append(traj)
    return segments


def fit_sindy(train_trajs, test_trajs):
    import pysindy as ps

    dt = T_FLOW / N_STEPS
    model = ps.SINDy(
        feature_library=ps.PolynomialLibrary(degree=2),
        optimizer=ps.STLSQ(threshold=0.02),
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Sparsity parameter is too big.*", category=UserWarning)
        model.fit([np.asarray(traj) for traj in train_trajs], t=dt)
    coeffs = np.asarray(model.coefficients())
    try:
        r2 = float(model.score([np.asarray(traj) for traj in test_trajs], t=dt))
    except Exception:
        r2 = float("nan")
    return coeffs, r2, int(np.count_nonzero(np.abs(coeffs) > 1e-12))


def fit_loop_signature(slots, train_probes, null_probes, test_probes):
    train = collect_segment_data(slots, train_probes)
    null = collect_segment_data(slots, null_probes)
    test = collect_segment_data(slots, test_probes)
    signature = []
    null_signature = []
    metrics = []
    for pos in range(4):
        coeff, r2, nonzero = fit_sindy(train[pos], test[pos])
        null_coeff, null_r2, null_nonzero = fit_sindy(null[pos], test[pos])
        signature.append(coeff)
        null_signature.append(null_coeff)
        metrics.append(
            {
                "position": pos + 1,
                "heldout_r2": r2,
                "null_refit_heldout_r2": null_r2,
                "nonzero_terms": nonzero,
                "null_nonzero_terms": null_nonzero,
                "instrument_valid_at_segment": bool(np.isfinite(r2) and r2 >= R2_GATE),
            }
        )
    return signature, null_signature, metrics


def segment_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a.reshape(-1) - b.reshape(-1)) / np.sqrt(a.size))


def ordered_distance(sig_a, sig_b) -> float:
    return float(sum(segment_distance(sig_a[i], sig_b[i]) for i in range(4)))


def unordered_distance(sig_a, sig_b):
    best = None
    best_perm = None
    for perm in permutations(range(4)):
        dist = float(sum(segment_distance(sig_a[i], sig_b[perm[i]]) for i in range(4)))
        if best is None or dist < best:
            best = dist
            best_perm = perm
    return best, [p + 1 for p in best_perm]


def run(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    train_probes = probe_set(rng)
    null_probes = probe_set(rng)
    test_probes = probe_set(rng)

    signatures = {}
    null_signatures = {}
    metrics = {}
    for label, slots in sorted(LOOPS.items()):
        sig, null_sig, met = fit_loop_signature(slots, train_probes, null_probes, test_probes)
        signatures[label] = sig
        null_signatures[label] = null_sig
        metrics[label] = met

    label_a = "Type2-inner-deductive"
    label_b = "Type2-outer-inductive"
    ordered = ordered_distance(signatures[label_a], signatures[label_b])
    unordered, best_perm = unordered_distance(signatures[label_a], signatures[label_b])
    self_nulls = {
        label: unordered_distance(signatures[label], null_signatures[label])[0]
        for label in sorted(signatures)
    }
    null_band = float(max(self_nulls.values()))

    r2_values = [m["heldout_r2"] for rows in metrics.values() for m in rows]
    instrument_valid = bool(all(np.isfinite(v) and v >= R2_GATE for v in r2_values))
    ordered_gate = bool(ordered > null_band)
    unordered_gate = bool(unordered <= null_band)
    passed = bool(instrument_valid and ordered_gate and unordered_gate)

    return {
        "packet_id": "t2_order_carried_v1",
        "seed": seed,
        "ordered_distance": ordered,
        "unordered_distance": unordered,
        "null_band": null_band,
        "self_nulls": self_nulls,
        "best_match_positions_outer": best_perm,
        "instrument": {
            "r2_gate": R2_GATE,
            "min_segment_r2": float(np.nanmin(r2_values)),
            "mean_segment_r2": float(np.nanmean(r2_values)),
            "instrument_valid_all_segments": instrument_valid,
            "per_segment_metrics": metrics,
        },
        "criteria": {
            "ordered_distance_gt_null_band": ordered_gate,
            "unordered_distance_lte_null_band": unordered_gate,
            "instrument_validity_gate": instrument_valid,
        },
        "pass": passed,
        "verdict": "PASS" if passed else "FAIL",
        "claim_ceiling": "standalone replication run only; compare to expected_ours.json after recording this result",
    }


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run the frozen T2 order-carried replication packet.")
    parser.add_argument("--seed", type=int, required=True, help="Required user-chosen seed.")
    parser.add_argument("--output", type=Path, default=None, help="Optional results JSON path.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = run(args.seed)
    output = args.output if args.output is not None else Path.cwd() / f"results_seed_{args.seed}.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print("T2 ORDER-CARRIED REPLICATION")
    print(f"seed: {args.seed}")
    print(f"ordered_distance: {result['ordered_distance']:.12f}")
    print(f"unordered_distance: {result['unordered_distance']:.12f}")
    print(f"null_band: {result['null_band']:.12f}")
    print(f"instrument_min_r2: {result['instrument']['min_segment_r2']:.12f}")
    print(f"instrument_valid: {result['instrument']['instrument_valid_all_segments']}")
    print(f"ordered_gt_null_band: {result['criteria']['ordered_distance_gt_null_band']}")
    print(f"unordered_within_null_band: {result['criteria']['unordered_distance_lte_null_band']}")
    print(f"verdict: {result['verdict']}")
    print(f"results_json: {output}")
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
