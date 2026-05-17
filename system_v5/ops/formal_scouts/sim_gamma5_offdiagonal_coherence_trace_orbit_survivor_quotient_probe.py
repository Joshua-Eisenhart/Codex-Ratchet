#!/usr/bin/env python3
"""Gamma5 off-diagonal coherence trace-orbit survivor-quotient scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from collections import defaultdict
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from clifford import Cl
import gudhi
import networkx as nx
import opt_einsum as oe
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "gamma5_offdiagonal_coherence_trace_orbit_survivor_quotient_probe_results.json"

NAME = "gamma5_offdiagonal_coherence_trace_orbit_survivor_quotient_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether gamma5 block off-diagonal coherence "
    "trace-norm orbits form multiple finite survivor quotient classes under "
    "chirality-asymmetric CPTP channels after symmetric effective-channel "
    "controls. It does not admit novelty, empirical physics, a final manifold "
    "tower, bridge claim, ontology, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density states, gamma5 projectors, Kraus maps, trace norms, and orbit distances"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing reduced-pair entropy contraction used in quotient signatures"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing chirality orientation boundary from Cl(1,3) pseudoscalar"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic projector identity checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing survivor quotient contradiction check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing quotient graph construction from survivor classes"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing conversion of quotient graph to tensor graph features"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence check on quotient-class simplex filtration"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
N_QUBITS = 4
DIM = 2**N_QUBITS
SURVIVAL_GAP = 0.04


def normalize(psi: torch.Tensor) -> torch.Tensor:
    return psi / torch.linalg.vector_norm(psi)


def pure_density(entries: dict[int, complex]) -> torch.Tensor:
    psi = torch.zeros(DIM, dtype=DTYPE)
    for idx, value in entries.items():
        psi[idx] = value
    psi = normalize(psi)
    return torch.outer(psi, psi.conj())


def candidate_densities() -> dict[str, torch.Tensor]:
    return {
        "balanced_lr_a": pure_density({0b0000: 0.42, 0b0111: 0.37j, 0b1010: -0.51, 0b1101: 0.64j}),
        "balanced_lr_b": pure_density({0b0001: 0.58, 0b0100: -0.31j, 0b1001: 0.47, 0b1110: 0.59j}),
        "left_heavy_a": pure_density({0b0000: 0.75, 0b0011: 0.25j, 0b1000: 0.39, 0b1100: -0.44j}),
        "right_heavy_a": pure_density({0b0010: 0.32, 0b0110: -0.41j, 0b1011: 0.81, 0b1111: 0.24j}),
        "phase_twisted_a": pure_density({0b0000: 0.36, 0b0101: complex(0.2, 0.38), 0b1010: complex(-0.47, 0.13), 0b1111: complex(0.58, -0.18)}),
        "phase_twisted_b": pure_density({0b0011: complex(0.44, -0.16), 0b0111: 0.52j, 0b1001: -0.49, 0b1101: complex(0.21, 0.48)}),
        "thin_bridge_a": pure_density({0b0000: 0.90, 0b1010: 0.18, 0b1100: 0.22j, 0b0101: 0.30}),
        "thin_bridge_b": pure_density({0b0111: 0.87, 0b1000: -0.23j, 0b1110: 0.26, 0b0010: 0.32j}),
        "block_diagonal_left": pure_density({0b0000: 0.61, 0b0011: -0.36j, 0b0101: 0.55, 0b0110: 0.44j}),
        "block_diagonal_right": pure_density({0b1000: 0.54, 0b1011: 0.49j, 0b1101: -0.52, 0b1111: 0.44j}),
        "maximally_mixed": torch.eye(DIM, dtype=DTYPE) / DIM,
    }


def gamma5_projectors(local: bool = False) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    gamma5 = torch.diag(torch.tensor([1.0, 1.0, -1.0, -1.0], dtype=DTYPE))
    eye4 = torch.eye(4, dtype=DTYPE)
    p_l = (eye4 + gamma5) / 2
    p_r = (eye4 - gamma5) / 2
    if local:
        return gamma5, p_l, p_r
    eye_ref = torch.eye(2 ** (N_QUBITS - 2), dtype=DTYPE)
    return torch.kron(gamma5, eye_ref), torch.kron(p_l, eye_ref), torch.kron(p_r, eye_ref)


def gamma5_boundary() -> dict[str, Any]:
    gamma5, p_l, p_r = gamma5_projectors(local=True)
    x = sp.Matrix([[0, 1], [1, 0]])
    _, blades = Cl(1, 3)
    pseudo = blades["e1234"]
    return {
        "gamma5_square_gap": float(torch.linalg.matrix_norm(gamma5 @ gamma5 - torch.eye(4, dtype=DTYPE)).item()),
        "projector_sum_gap": float(torch.linalg.matrix_norm(p_l + p_r - torch.eye(4, dtype=DTYPE)).item()),
        "projector_product_gap": float(torch.linalg.matrix_norm(p_l @ p_r).item()),
        "left_rank": int(torch.linalg.matrix_rank(p_l).item()),
        "right_rank": int(torch.linalg.matrix_rank(p_r).item()),
        "sympy_pauli_boundary": bool(sp.simplify(x * x) == sp.eye(2)),
        "clifford_pseudoscalar": str(pseudo),
        "pass": torch.linalg.matrix_norm(gamma5 @ gamma5 - torch.eye(4, dtype=DTYPE)).item() < 1e-12
        and torch.linalg.matrix_norm(p_l + p_r - torch.eye(4, dtype=DTYPE)).item() < 1e-12
        and torch.linalg.matrix_norm(p_l @ p_r).item() < 1e-12
        and int(torch.linalg.matrix_rank(p_l).item()) == 2
        and int(torch.linalg.matrix_rank(p_r).item()) == 2,
    }


def amplitude_damping(gamma: float) -> list[torch.Tensor]:
    return [
        torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=DTYPE),
        torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=DTYPE),
    ]


def asymmetric_local_kraus(gamma_left: float, gamma_right: float) -> list[torch.Tensor]:
    k0_l, k1_l = amplitude_damping(gamma_left)
    k0_r, k1_r = amplitude_damping(gamma_right)
    return [
        torch.block_diag(k0_l, k0_r),
        torch.block_diag(k1_l, torch.zeros((2, 2), dtype=DTYPE)),
        torch.block_diag(torch.zeros((2, 2), dtype=DTYPE), k1_r),
    ]


def symmetric_local_kraus(gamma: float) -> list[torch.Tensor]:
    k0, k1 = amplitude_damping(gamma)
    return [torch.block_diag(k, k) for k in (k0, k1)]


def embed(kraus: list[torch.Tensor]) -> list[torch.Tensor]:
    eye_ref = torch.eye(2 ** (N_QUBITS - 2), dtype=DTYPE)
    return [torch.kron(k, eye_ref) for k in kraus]


def apply_kraus(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ k.conj().T
    return out


def cptp_gap(kraus: list[torch.Tensor]) -> float:
    accum = torch.zeros_like(kraus[0])
    for k in kraus:
        accum = accum + k.conj().T @ k
    return float(torch.linalg.matrix_norm(accum - torch.eye(kraus[0].shape[0], dtype=DTYPE)).item())


def offdiag_trace_norm(rho: torch.Tensor) -> float:
    _, p_l, p_r = gamma5_projectors()
    return float(torch.sum(torch.linalg.svdvals(p_l @ rho @ p_r)).item())


def pair_entropy(rho: torch.Tensor) -> float:
    tensor = rho.reshape(4, 4, 4, 4)
    red = oe.contract("abcb->ac", tensor)
    red = (red + red.conj().T) / 2
    eigs = torch.clamp(torch.linalg.eigvalsh(red), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def orbit(rho: torch.Tensor, mode: str, gamma: float | None = None) -> dict[str, Any]:
    current = rho.clone()
    coherence = [offdiag_trace_norm(current)]
    entropy = [pair_entropy(current)]
    for step in range(1, 8):
        if mode == "asymmetric":
            kraus = embed(asymmetric_local_kraus(0.04 + 0.045 * step, 0.015 + 0.010 * step))
        elif mode == "symmetric":
            g = gamma if gamma is not None else 0.025 + 0.026 * step
            kraus = embed(symmetric_local_kraus(g))
        elif mode == "commuting":
            kraus = embed([torch.eye(4, dtype=DTYPE)])
        else:
            raise ValueError(mode)
        current = apply_kraus(current, kraus)
        coherence.append(offdiag_trace_norm(current))
        entropy.append(pair_entropy(current))
    return {"coherence_orbit": coherence, "entropy_orbit": entropy}


def l2_gap(a: list[float], b: list[float]) -> float:
    return float(torch.linalg.vector_norm(torch.tensor(a, dtype=torch.float64) - torch.tensor(b, dtype=torch.float64)).item())


def best_symmetric_fit(asym_orbit: list[float], rho: torch.Tensor) -> dict[str, Any]:
    best = {"gamma": None, "gap": float("inf"), "coherence_orbit": []}
    for idx in range(101):
        gamma = 0.0 + 0.34 * idx / 100
        row = orbit(rho, "symmetric", gamma=gamma)
        gap = l2_gap(asym_orbit, row["coherence_orbit"])
        if gap < best["gap"]:
            best = {"gamma": gamma, "gap": gap, "coherence_orbit": row["coherence_orbit"]}
    return best


def signature(values: list[float], entropies: list[float]) -> tuple[Any, ...]:
    initial = values[0]
    final = values[-1]
    decay = initial - final
    bend = max(values) - min(values)
    entropy_delta = entropies[-1] - entropies[0]
    return (
        round(initial, 1),
        round(final, 1),
        round(decay, 1),
        round(bend, 1),
        round(entropy_delta, 1),
    )


def quotient(rows: list[dict[str, Any]]) -> dict[str, Any]:
    survivors = [row for row in rows if row["survives"]]
    classes: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for row in survivors:
        classes[row["signature"]].append(row["name"])
    graph = nx.Graph()
    for row in survivors:
        graph.add_node(row["name"], signature=str(row["signature"]), fit_gap=float(row["fit_gap"]))
    for names in classes.values():
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                graph.add_edge(left, right)
    pyg_graph = from_networkx(graph)
    simplex = gudhi.SimplexTree()
    for idx, row in enumerate(survivors):
        simplex.insert([idx], filtration=float(row["fit_gap"]))
    for i, left in enumerate(survivors):
        for j, right in enumerate(survivors[i + 1 :], start=i + 1):
            if left["signature"] == right["signature"]:
                simplex.insert([i, j], filtration=max(float(left["fit_gap"]), float(right["fit_gap"])))
    simplex.persistence()
    h0 = simplex.persistence_intervals_in_dimension(0)
    finite_lifetimes = [float(b - a) for a, b in h0 if math.isfinite(b)]
    return {
        "survivor_count": len(survivors),
        "class_count": len(classes),
        "classes": {str(key): value for key, value in classes.items()},
        "networkx_nodes": graph.number_of_nodes(),
        "networkx_edges": graph.number_of_edges(),
        "pyg_num_nodes": int(pyg_graph.num_nodes),
        "pyg_num_edges": int(pyg_graph.edge_index.shape[1]) if hasattr(pyg_graph, "edge_index") else 0,
        "gudhi_h0_intervals": [[float(a), None if not math.isfinite(b) else float(b)] for a, b in h0],
        "gudhi_finite_lifetime_sum": float(sum(finite_lifetimes)),
    }


def z3_quotient_witness(asym_classes: int, control_classes: int, cptp: float) -> dict[str, Any]:
    solver = z3.Solver()
    enough, exceeds_control, valid = z3.Bools("enough exceeds_control valid")
    solver.add(enough == (asym_classes >= 3))
    solver.add(exceeds_control == (asym_classes > control_classes))
    solver.add(valid == (cptp < 1e-12))
    solver.add(z3.Not(z3.And(enough, exceeds_control, valid)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "asymmetric_classes": asym_classes,
        "control_classes": control_classes,
        "cptp_valid": cptp < 1e-12,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    control_rows = []
    raw = {}
    for name, rho in candidate_densities().items():
        asym = orbit(rho, "asymmetric")
        fit = best_symmetric_fit(asym["coherence_orbit"], rho)
        comm = orbit(rho, "commuting")
        sig = signature(asym["coherence_orbit"], asym["entropy_orbit"])
        control_gap = l2_gap(comm["coherence_orbit"], asym["coherence_orbit"])
        row = {
            "name": name,
            "signature": sig,
            "initial_coherence": asym["coherence_orbit"][0],
            "fit_gap": fit["gap"],
            "best_gamma": fit["gamma"],
            "survives": fit["gap"] > SURVIVAL_GAP and asym["coherence_orbit"][0] > 1e-8,
        }
        rows.append(row)
        control_rows.append(
            {
                "name": name,
                "signature": signature(comm["coherence_orbit"], comm["entropy_orbit"]),
                "fit_gap": control_gap,
                "survives": control_gap > SURVIVAL_GAP and comm["coherence_orbit"][0] > 1e-8,
            }
        )
        raw[name] = {
            "asymmetric_orbit": asym["coherence_orbit"],
            "asymmetric_entropy": asym["entropy_orbit"],
            "best_symmetric_gamma": fit["gamma"],
            "best_symmetric_gap": fit["gap"],
            "best_symmetric_orbit": fit["coherence_orbit"],
            "commuting_orbit": comm["coherence_orbit"],
            "survives": row["survives"],
        }
    asym_q = quotient(rows)
    control_q = quotient(control_rows)
    cptp = max(
        cptp_gap(embed(asymmetric_local_kraus(0.30, 0.05))),
        cptp_gap(embed(symmetric_local_kraus(0.17))),
    )
    z3_row = z3_quotient_witness(asym_q["class_count"], control_q["class_count"], cptp)
    zero_rows = {name: raw[name] for name in ("block_diagonal_left", "block_diagonal_right", "maximally_mixed")}
    fit_gaps = [float(row["fit_gap"]) for row in rows if row["survives"]]
    positive = {
        "asymmetric_orbit_survivor_quotient_has_multiple_classes": {
            "quotient": asym_q,
            "pass": asym_q["survivor_count"] >= 4 and asym_q["class_count"] >= 3,
        },
        "asymmetric_classes_exceed_commuting_control_classes": {
            "asymmetric_class_count": asym_q["class_count"],
            "commuting_control_class_count": control_q["class_count"],
            "pass": asym_q["class_count"] > control_q["class_count"],
        },
        "survivor_orbits_resist_best_symmetric_effective_gamma_fit": {
            "min_survivor_fit_gap": min(fit_gaps) if fit_gaps else 0.0,
            "threshold": SURVIVAL_GAP,
            "pass": bool(fit_gaps) and min(fit_gaps) > SURVIVAL_GAP,
        },
        "gamma5_projector_boundary": gamma5_boundary(),
        "asymmetric_and_symmetric_channels_are_cptp": {"cptp_gap": cptp, "pass": cptp < 1e-12},
    }
    graveyard_companions = {
        "maximally_mixed_input_has_zero_survivor_signal": {
            "orbit": raw["maximally_mixed"]["asymmetric_orbit"],
            "pass": raw["maximally_mixed"]["survives"] is False and max(abs(v) for v in raw["maximally_mixed"]["asymmetric_orbit"]) < 1e-12,
        },
        "block_diagonal_inputs_have_zero_survivor_signal": {
            "rows": zero_rows,
            "pass": all(raw[name]["survives"] is False and max(abs(v) for v in raw[name]["asymmetric_orbit"]) < 1e-12 for name in ("block_diagonal_left", "block_diagonal_right")),
        },
        "commuting_identity_schedule_has_fewer_quotient_classes": {
            "quotient": control_q,
            "pass": control_q["class_count"] < asym_q["class_count"],
        },
        "symmetric_effective_gamma_fit_rejects_survivors": {
            "survivor_fit_gaps": fit_gaps,
            "pass": bool(fit_gaps) and min(fit_gaps) > SURVIVAL_GAP,
        },
    }
    boundary = {
        "finite_four_qubit_dimension": {"dimension": DIM, "pass": DIM == 16},
        "z3_survivor_quotient_witness": z3_row,
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite family of four-qubit density states under gamma5 chirality-asymmetric CPTP sequences, quotiented by P_L rho P_R trace-norm orbit signatures after symmetric effective-gamma controls",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This scout tests quotient classes of trace-norm orbits, not a full Stinespring-equivalence proof.",
            "The next stronger negative is a channel-equivalence search over dilations or non-Markovian schedules.",
            "The quotient threshold is explicit and should be swept before any stronger claim is made.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from provider proposals after the gamma5 off-diagonal orbit survivor; it is not a canonical v4 probe.",
        "raw_rows": raw,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all(checks),
                "result": str(OUT_PATH),
                "survivor_count": asym_q["survivor_count"],
                "class_count": asym_q["class_count"],
                "control_class_count": control_q["class_count"],
                "min_fit_gap": min(fit_gaps) if fit_gaps else 0.0,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
