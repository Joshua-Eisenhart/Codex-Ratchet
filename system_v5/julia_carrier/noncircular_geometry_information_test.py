#!/usr/bin/env python3
"""Non-circular geometry/information test.

Builds a family of two-component links with independently measured geometric
linking, derives a qubit state from the projected crossings, and checks whether
curve-vs-curve log-negativity tracks topology or only the induced gates.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Iterable

import numpy as np


R_MAJOR = 2.0
R_MINOR = 0.35
N_GAUSS = 1600
N_PROJECT = 997
N_CURVE1_QUBITS = 10
N_CURVE2_QUBITS = 10
K_VALUES = [1, 2, 3, 4, 5]


def torus_link_curves(k: int, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Return a core circle and a (1,k) torus curve around it."""
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    c1 = np.column_stack(
        (
            R_MAJOR * np.cos(t),
            R_MAJOR * np.sin(t),
            np.zeros_like(t),
        )
    )
    radius = R_MAJOR + R_MINOR * np.cos(k * t)
    c2 = np.column_stack(
        (
            radius * np.cos(t),
            radius * np.sin(t),
            R_MINOR * np.sin(k * t),
        )
    )
    return c1, c2


def gauss_linking_number(curve1: np.ndarray, curve2: np.ndarray, chunk: int = 128) -> float:
    """Midpoint quadrature for the Gauss linking integral over closed polygons."""
    p0 = curve1
    p1 = np.roll(curve1, -1, axis=0)
    q0 = curve2
    q1 = np.roll(curve2, -1, axis=0)
    dp = p1 - p0
    dq = q1 - q0
    mp = 0.5 * (p0 + p1)
    mq = 0.5 * (q0 + q1)

    total = 0.0
    for start in range(0, len(mp), chunk):
        stop = min(start + chunk, len(mp))
        r = mp[start:stop, None, :] - mq[None, :, :]
        cross = np.cross(dp[start:stop, None, :], dq[None, :, :])
        numerator = np.einsum("ijk,ijk->ij", r, cross)
        denominator = np.linalg.norm(r, axis=2) ** 3
        total += float(np.sum(numerator / denominator))
    return total / (4.0 * math.pi)


def cross2(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def projected_intersections(curve1: np.ndarray, curve2: np.ndarray) -> list[dict[str, float]]:
    """Find transverse intersections between projected polygon segments."""
    p = curve1[:, :2]
    p_next = np.roll(p, -1, axis=0)
    q = curve2[:, :2]
    q_next = np.roll(q, -1, axis=0)
    records: list[dict[str, float]] = []
    eps = 1.0e-10

    s_all = q_next - q
    for i, (p_i, p_j) in enumerate(zip(p, p_next)):
        r = p_j - p_i
        q_minus_p = q - p_i
        denom = cross2(r, s_all)
        good = np.abs(denom) > eps
        if not np.any(good):
            continue
        u = np.full(len(q), np.nan)
        v = np.full(len(q), np.nan)
        u[good] = cross2(q_minus_p[good], s_all[good]) / denom[good]
        v[good] = cross2(q_minus_p[good], r) / denom[good]
        mask = good & (u > eps) & (u < 1.0 - eps) & (v > eps) & (v < 1.0 - eps)
        for j in np.flatnonzero(mask):
            point = p_i + u[j] * r
            records.append(
                {
                    "curve1_t_fraction": (i + float(u[j])) / len(p),
                    "curve2_t_fraction": (j + float(v[j])) / len(q),
                    "x": float(point[0]),
                    "y": float(point[1]),
                }
            )

    records.sort(key=lambda rec: (rec["curve2_t_fraction"], rec["curve1_t_fraction"]))
    return records


def nearest_cyclic_qubit(t_fraction: float, n_qubits: int) -> int:
    return int(math.floor((t_fraction % 1.0) * n_qubits + 0.5)) % n_qubits


def crossings_to_gates(crossings: Iterable[dict[str, float]]) -> list[tuple[int, int]]:
    gates: list[tuple[int, int]] = []
    for crossing in crossings:
        q1 = nearest_cyclic_qubit(crossing["curve1_t_fraction"], N_CURVE1_QUBITS)
        q2_local = nearest_cyclic_qubit(crossing["curve2_t_fraction"], N_CURVE2_QUBITS)
        gates.append((q1, N_CURVE1_QUBITS + q2_local))
    return gates


def plus_state(n_qubits: int) -> np.ndarray:
    shape = (2,) * n_qubits
    return np.full(shape, 1.0 / math.sqrt(2**n_qubits), dtype=np.complex128)


def apply_cz_in_place(psi: np.ndarray, q_a: int, q_b: int) -> None:
    index = [slice(None)] * psi.ndim
    index[q_a] = 1
    index[q_b] = 1
    psi[tuple(index)] *= -1.0


def build_state(gates: Iterable[tuple[int, int]]) -> np.ndarray:
    psi = plus_state(N_CURVE1_QUBITS + N_CURVE2_QUBITS)
    for q_a, q_b in gates:
        apply_cz_in_place(psi, q_a, q_b)
    return psi


def log_negativity_for_partition(psi: np.ndarray, part_a: list[int]) -> float:
    n_qubits = psi.ndim
    part_a_set = set(part_a)
    part_b = [q for q in range(n_qubits) if q not in part_a_set]
    matrix = np.transpose(psi, part_a + part_b).reshape(2 ** len(part_a), 2 ** len(part_b))
    singular_values = np.linalg.svd(matrix, compute_uv=False)
    return float(2.0 * np.log2(np.sum(singular_values)))


def run_case(k: int) -> dict[str, object]:
    c1_gauss, c2_gauss = torus_link_curves(k, N_GAUSS)
    signed_linking = gauss_linking_number(c1_gauss, c2_gauss)
    c1_project, c2_project = torus_link_curves(k, N_PROJECT)
    crossings = projected_intersections(c1_project, c2_project)
    gates = crossings_to_gates(crossings)
    psi = build_state(gates)
    curve1_partition = list(range(N_CURVE1_QUBITS))
    log_neg = log_negativity_for_partition(psi, curve1_partition)
    return {
        "k": k,
        "geo_linking_signed": signed_linking,
        "geo_linking": abs(signed_linking),
        "n_crossings": len(crossings),
        "n_crossing_gates": len(gates),
        "n_unique_crossing_gates": len(set(gates)),
        "log_neg": log_neg,
        "gates": gates,
    }


def classify(rows: list[dict[str, object]], kink_control: dict[str, object]) -> tuple[str, str]:
    log_negs = np.array([float(row["log_neg"]) for row in rows])
    crossings = np.array([float(row["n_crossings"]) for row in rows])
    monotone = bool(np.all(np.diff(log_negs) > 1.0e-8))
    crossing_only = bool(np.max(np.abs(log_negs - crossings)) < 1.0e-8)

    if monotone and not crossing_only and abs(float(kink_control["curve_split_delta"])) < 1.0e-8:
        return (
            "TRACKS",
            "curve-split log-neg is monotone in measured linking and is not equal to the crossing-gate count.",
        )
    if crossing_only:
        return (
            "CROSSING-COUNT-ONLY",
            "curve-split log-neg equals the number of inter-component crossing gates; the self-kink is local to curve2 and leaves this cut unchanged.",
        )
    return (
        "NO-TRACK",
        "curve-split log-neg is not a clean non-crossing-count monotone of the measured linking.",
    )


def main() -> None:
    rows = [run_case(k) for k in K_VALUES]

    kink_source = rows[2]
    base_gates = [tuple(gate) for gate in kink_source["gates"]]
    self_kink_gate = (N_CURVE1_QUBITS + 0, N_CURVE1_QUBITS + 1)
    curve1_partition = list(range(N_CURVE1_QUBITS))
    before = log_negativity_for_partition(build_state(base_gates), curve1_partition)
    after = log_negativity_for_partition(build_state(base_gates + [self_kink_gate]), curve1_partition)
    kink_control = {
        "type": "Reidemeister-I self-crossing control on curve2",
        "k": kink_source["k"],
        "geo_linking_before": kink_source["geo_linking"],
        "geo_linking_after_expected": kink_source["geo_linking"],
        "intercomponent_crossings_before": kink_source["n_crossings"],
        "added_self_crossings": 1,
        "curve_split_log_neg_before": before,
        "curve_split_log_neg_after": after,
        "curve_split_delta": after - before,
        "self_kink_gate": self_kink_gate,
        "note": "The selected information cut is curve1|curve2, so a self-crossing gate wholly inside curve2 is local to one side of the cut.",
    }

    verdict, justification = classify(rows, kink_control)
    receipt = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "script": "noncircular_geometry_information_test.py",
        "construction": {
            "curve_family": "core circle plus (1,k) torus curve",
            "k_values": K_VALUES,
            "gauss_samples_per_curve": N_GAUSS,
            "projection_samples_per_curve": N_PROJECT,
            "curve1_qubits": N_CURVE1_QUBITS,
            "curve2_qubits": N_CURVE2_QUBITS,
            "initial_state": "|+> on every qubit",
            "crossing_gate": "CZ at every detected inter-component projected crossing",
            "information_cut": "curve1 qubits | curve2 qubits",
        },
        "table": [
            {
                "k": int(row["k"]),
                "geo_linking": float(row["geo_linking"]),
                "geo_linking_signed": float(row["geo_linking_signed"]),
                "n_crossings": int(row["n_crossings"]),
                "n_crossing_gates": int(row["n_crossing_gates"]),
                "n_unique_crossing_gates": int(row["n_unique_crossing_gates"]),
                "log_neg": float(row["log_neg"]),
            }
            for row in rows
        ],
        "kink_control": kink_control,
        "classification": verdict,
        "justification": justification,
    }

    with open("noncircular_geometry_information_test_results.json", "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
        f.write("\n")

    print("k  geo_linking  n_crossings  log_neg")
    for row in rows:
        print(
            f"{int(row['k']):d}  "
            f"{float(row['geo_linking']):.6f}     "
            f"{int(row['n_crossings']):2d}           "
            f"{float(row['log_neg']):.6f}"
        )
    print(
        "kink_control "
        f"k={kink_control['k']} "
        f"added_self_crossings={kink_control['added_self_crossings']} "
        f"log_neg_before={kink_control['curve_split_log_neg_before']:.6f} "
        f"log_neg_after={kink_control['curve_split_log_neg_after']:.6f} "
        f"delta={kink_control['curve_split_delta']:.6e}"
    )
    print(f"VERDICT={verdict}")


if __name__ == "__main__":
    main()
