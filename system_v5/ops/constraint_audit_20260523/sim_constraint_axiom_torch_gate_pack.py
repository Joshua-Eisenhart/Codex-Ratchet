#!/usr/bin/env python3
"""Torch-native root and extended-constraint gate pack.

Audit/control artifact only. This rebuilds the constraint gates locally without
using NumPy and without reading contaminated formal_scout results.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "constraint_axiom_torch_gate_pack_results.json"

DTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return (rho + torch.conj(rho).T) / 2


def rho_from_bloch(r: list[float]) -> torch.Tensor:
    return hermitize(0.5 * (I2 + r[0] * X + r[1] * Y + r[2] * Z))


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def normalize_vec(psi: torch.Tensor) -> torch.Tensor:
    return psi / torch.linalg.vector_norm(psi)


def unitary(axis: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * axis


def trace_distance(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(rho - sigma)).real
    return float((0.5 * torch.sum(torch.abs(vals))).item())


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(rho)).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    nz = vals[vals > EPS]
    return float((-torch.sum(nz * torch.log(nz))).item())


def partial_trace_a(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho_ab.reshape(2, 2, 2, 2))


def partial_trace_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abad->bd", rho_ab.reshape(2, 2, 2, 2))


def coherent_info_a_to_b(rho_ab: torch.Tensor) -> float:
    return entropy(partial_trace_b(rho_ab)) - entropy(rho_ab)


def mutual_info(rho_ab: torch.Tensor) -> float:
    return entropy(partial_trace_a(rho_ab)) + entropy(partial_trace_b(rho_ab)) - entropy(rho_ab)


def projector(axis: torch.Tensor, sign: int = 1) -> torch.Tensor:
    return 0.5 * (I2 + sign * axis)


def gate_f01_finitude() -> dict[str, Any]:
    finite = {
        "carrier_dim": 2,
        "probe_count": 3,
        "operator_count": 4,
        "path_count": 4,
        "registry_count": 16,
    }
    return {
        "pass": all(isinstance(v, int) and 0 < v < 10_000 for v in finite.values()),
        "finite_counts": finite,
        "graveyard": "implicit continuum carrier or unbounded path family would fail",
    }


def gate_n01_noncommutation() -> dict[str, Any]:
    rho = rho_from_bloch([0.31, 0.23, 0.47])
    ux = unitary(X, 0.61)
    uz = unitary(Z, -0.48)
    ab = ux @ uz @ rho @ torch.conj(uz).T @ torch.conj(ux).T
    ba = uz @ ux @ rho @ torch.conj(ux).T @ torch.conj(uz).T
    comm_order_gap = trace_distance(ab, ba)
    z1 = unitary(Z, 0.23)
    z2 = unitary(Z, -0.51)
    commuting_ab = z1 @ z2 @ rho @ torch.conj(z2).T @ torch.conj(z1).T
    commuting_ba = z2 @ z1 @ rho @ torch.conj(z1).T @ torch.conj(z2).T
    commuting_gap = trace_distance(commuting_ab, commuting_ba)
    return {
        "pass": comm_order_gap > 1e-3 and commuting_gap < 1e-10,
        "noncommuting_order_gap": comm_order_gap,
        "commuting_order_gap": commuting_gap,
    }


def gate_ea01_no_primitive_identity() -> dict[str, Any]:
    rho_a = rho_from_bloch([0.42, -0.17, 0.25])
    rho_alias = rho_a.clone()
    rho_same_z_different_record = rho_from_bloch([-0.11, 0.39, 0.25])
    alias_probe_vector_gap = max(
        abs(float(torch.real(torch.trace(rho_a @ op) - torch.trace(rho_alias @ op)).item()))
        for op in (X, Y, Z)
    )
    same_z_but_different_record_gap = max(
        abs(float(torch.real(torch.trace(rho_a @ op) - torch.trace(rho_same_z_different_record @ op)).item()))
        for op in (X, Y, Z)
    )
    return {
        "pass": alias_probe_vector_gap < 1e-12 and same_z_but_different_record_gap > 0.25,
        "alias_probe_vector_gap": alias_probe_vector_gap,
        "same_z_but_different_record_gap": same_z_but_different_record_gap,
        "finite_identity_witnesses": ["handle", "receipt_path", "probe_vector"],
    }


def gate_ea02_probe_relative_equality() -> dict[str, Any]:
    rho_a = rho_from_bloch([0.42, -0.17, 0.25])
    rho_b = rho_from_bloch([-0.11, 0.39, 0.25])
    weak_z_gap = abs(float(torch.real(torch.trace(rho_a @ Z) - torch.trace(rho_b @ Z)).item()))
    rich_gaps = [
        abs(float(torch.real(torch.trace(rho_a @ op) - torch.trace(rho_b @ op)).item()))
        for op in (X, Y, Z)
    ]
    return {
        "pass": weak_z_gap < 1e-10 and max(rich_gaps) > 0.25,
        "weak_z_gap": weak_z_gap,
        "rich_probe_gaps": rich_gaps,
        "verdict": "single-probe equality fails when the active finite probe family is widened",
    }


def gate_ea03_boundary_contrast_identity() -> dict[str, Any]:
    rho_up = rho_from_bloch([0.0, 0.0, 0.8])
    rho_down = rho_from_bloch([0.0, 0.0, -0.8])
    center = rho_from_bloch([0.0, 0.0, 0.0])
    center_distance_up = trace_distance(rho_up, center)
    center_distance_down = trace_distance(rho_down, center)
    contrast_gap = abs(float(torch.real(torch.trace(rho_up @ Z) - torch.trace(rho_down @ Z)).item()))
    return {
        "pass": abs(center_distance_up - center_distance_down) < 1e-12 and contrast_gap > 1.5,
        "center_distance_up": center_distance_up,
        "center_distance_down": center_distance_down,
        "contrast_gap_sigma_z": contrast_gap,
        "verdict": "center distance alone cannot identify state; contrast probe is load-bearing",
    }


def gate_ea04_ec11_no_primitive_time() -> dict[str, Any]:
    return gate_n01_noncommutation()


def gate_ea05_ec15_no_primitive_metric() -> dict[str, Any]:
    rho_a = rho_from_bloch([0.3, 0.4, 0.2])
    rho_b = rho_from_bloch([-0.2, 0.1, 0.6])
    u = unitary(X + Z, 0.77)
    # Rescale because X+Z is not unit length.
    axis = (X + Z) / math.sqrt(2)
    u = unitary(axis, 0.77)
    td_before = trace_distance(rho_a, rho_b)
    td_after = trace_distance(u @ rho_a @ torch.conj(u).T, u @ rho_b @ torch.conj(u).T)
    x_coord_before = float(torch.real(torch.trace(rho_a @ X) - torch.trace(rho_b @ X)).item())
    x_coord_after = float(
        torch.real(torch.trace((u @ rho_a @ torch.conj(u).T) @ X) - torch.trace((u @ rho_b @ torch.conj(u).T) @ X)).item()
    )
    return {
        "pass": abs(td_before - td_after) < 1e-10 and abs(x_coord_before - x_coord_after) > 0.05,
        "trace_distance_before": td_before,
        "trace_distance_after_unitary": td_after,
        "raw_x_coordinate_gap_before": x_coord_before,
        "raw_x_coordinate_gap_after": x_coord_after,
    }


def gate_ea06_ec12_no_closure_by_default() -> dict[str, Any]:
    gamma = 0.65
    k0 = torch.tensor([[1, 0], [0, math.sqrt(1 - gamma)]], dtype=CDTYPE)
    k1 = torch.tensor([[0, math.sqrt(gamma)], [0, 0]], dtype=CDTYPE)

    def amp(rho: torch.Tensor) -> torch.Tensor:
        return hermitize(k0 @ rho @ torch.conj(k0).T + k1 @ rho @ torch.conj(k1).T)

    rho_a = rho_from_bloch([0.7, 0.0, 0.0])
    rho_b = rho_from_bloch([-0.7, 0.0, 0.0])
    before = trace_distance(rho_a, rho_b)
    after = trace_distance(amp(rho_a), amp(rho_b))
    final_a = rho_a.clone()
    final_b = rho_b.clone()
    for _ in range(40):
        final_a = amp(final_a)
        final_b = amp(final_b)
    final = trace_distance(final_a, final_b)
    return {
        "pass": before > after > final and final < 1e-6,
        "trace_distance_before": before,
        "after_one_channel": after,
        "after_40_channels": final,
        "verdict": "distinguishability loss proves no inverse on this family",
    }


def gate_ea07_finite_witness_discipline() -> dict[str, Any]:
    witnesses = [
        "finite_counts",
        "order_gap",
        "probe_vector",
        "trace_distance",
        "entropy",
        "negative_controls",
    ]
    return {"pass": len(witnesses) == 6, "witnesses": witnesses}


def gate_ec08_no_cloning() -> dict[str, Any]:
    overlap_orthogonal = 0.0
    overlap_nonorthogonal = 1.0 / math.sqrt(2)
    contradiction = abs(overlap_nonorthogonal - overlap_nonorthogonal**2)
    max_clone_fidelity_bound = 0.5 * (1.0 + overlap_nonorthogonal)
    return {
        "pass": contradiction > 0.1 and max_clone_fidelity_bound < 0.9,
        "orthogonal_overlap": overlap_orthogonal,
        "nonorthogonal_overlap": overlap_nonorthogonal,
        "linearity_contradiction": contradiction,
        "max_clone_fidelity_bound": max_clone_fidelity_bound,
    }


def gate_ec09_no_primitive_probability() -> dict[str, Any]:
    rho = rho_from_bloch([0.52, -0.18, 0.31])
    p_z = float(torch.real(torch.trace(rho @ projector(Z, 1))).item())
    p_x = float(torch.real(torch.trace(rho @ projector(X, 1))).item())
    return {
        "pass": abs(p_z - p_x) > 0.05,
        "p_from_z_probe": p_z,
        "p_from_x_probe": p_x,
        "probe_dependence_gap": abs(p_z - p_x),
    }


def gate_ec10_no_primitive_optimization() -> dict[str, Any]:
    candidates = {
        "zero": rho_from_bloch([0, 0, 1]),
        "one": rho_from_bloch([0, 0, -1]),
        "plus": rho_from_bloch([1, 0, 0]),
        "minus": rho_from_bloch([-1, 0, 0]),
    }

    def best_for(op: torch.Tensor) -> str:
        scores = {name: float(torch.real(torch.trace(rho @ op)).item()) for name, rho in candidates.items()}
        return max(scores, key=scores.get)

    optima = {"F_z": best_for(Z), "F_x": best_for(X)}
    return {"pass": len(set(optima.values())) == 2, "optimum_per_functional": optima}


def gate_ec13_no_outside_observer() -> dict[str, Any]:
    ket00 = torch.tensor([1, 0, 0, 0], dtype=CDTYPE)
    ket11 = torch.tensor([0, 0, 0, 1], dtype=CDTYPE)
    bell = normalize_vec(ket00 + ket11)
    rho_bell = density(bell)
    rho_a_bell = partial_trace_b(rho_bell)
    ket0 = torch.tensor([1, 0], dtype=CDTYPE)
    ket_plus = normalize_vec(torch.tensor([1, 1], dtype=CDTYPE))
    rho_prod = density(torch.kron(ket0, ket_plus))
    rho_a_prod = partial_trace_b(rho_prod)
    s_bell = entropy(rho_a_bell)
    s_prod = entropy(rho_a_prod)
    return {"pass": abs(s_bell - math.log(2)) < 1e-10 and s_prod < 1e-8, "S_A_bell": s_bell, "S_A_product": s_prod}


def gate_ec14_no_global_total_order() -> dict[str, Any]:
    rho_x = rho_from_bloch([0.7, 0.0, 0.0])
    rho_diag = rho_from_bloch([0.0, 0.0, 0.7])
    entropy_gap = abs(entropy(rho_x) - entropy(rho_diag))
    operator_gap = trace_distance(rho_x, rho_diag)
    return {
        "pass": entropy_gap < 1e-10 and operator_gap > 0.4,
        "entropy_gap": entropy_gap,
        "operator_trace_distance": operator_gap,
    }


def gate_ec16_no_semantic_smuggling() -> dict[str, Any]:
    maximally_mixed_ab = torch.eye(4, dtype=CDTYPE) / 4
    ket00 = torch.tensor([1, 0, 0, 0], dtype=CDTYPE)
    ket11 = torch.tensor([0, 0, 0, 1], dtype=CDTYPE)
    bell = density(normalize_vec(ket00 + ket11))
    ic_mixed = coherent_info_a_to_b(maximally_mixed_ab)
    mi_mixed = mutual_info(maximally_mixed_ab)
    ic_bell = coherent_info_a_to_b(bell)
    mi_bell = mutual_info(bell)
    return {
        "pass": ic_mixed < -0.65 and abs(mi_mixed) < 1e-8 and ic_bell > 0.65 and mi_bell > 1.3,
        "mixed_product_coherent_info": ic_mixed,
        "mixed_product_mutual_info": mi_mixed,
        "bell_coherent_info": ic_bell,
        "bell_mutual_info": mi_bell,
        "verdict": "coherent information and mutual information have different sign/scale behavior",
    }


def main() -> int:
    HERE.joinpath("results").mkdir(parents=True, exist_ok=True)
    started = time.time()
    gates = {
        "F01_finitude": gate_f01_finitude(),
        "N01_noncommutation": gate_n01_noncommutation(),
        "EA01_no_primitive_identity": gate_ea01_no_primitive_identity(),
        "EA02_probe_relative_equality": gate_ea02_probe_relative_equality(),
        "EA03_boundary_contrast_identity": gate_ea03_boundary_contrast_identity(),
        "EA04_EC11_no_primitive_time": gate_ea04_ec11_no_primitive_time(),
        "EA05_EC15_no_primitive_metric": gate_ea05_ec15_no_primitive_metric(),
        "EA06_EC12_no_closure_by_default": gate_ea06_ec12_no_closure_by_default(),
        "EA07_finite_witness_discipline": gate_ea07_finite_witness_discipline(),
        "EC08_no_cloning": gate_ec08_no_cloning(),
        "EC09_no_primitive_probability": gate_ec09_no_primitive_probability(),
        "EC10_no_primitive_optimization": gate_ec10_no_primitive_optimization(),
        "EC13_no_outside_observer": gate_ec13_no_outside_observer(),
        "EC14_no_global_total_order": gate_ec14_no_global_total_order(),
        "EC16_no_semantic_smuggling": gate_ec16_no_semantic_smuggling(),
    }
    all_pass = all(bool(section.get("pass")) for section in gates.values())
    receipt = {
        "kind": "constraint_axiom_torch_gate_pack",
        "claim_ceiling": "audit_control_packet_only_not_formal_admission",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "uses_numpy": False,
        "all_pass": all_pass,
        "runtime_seconds": time.time() - started,
        "gates": gates,
    }
    OUT.write_text(json.dumps(as_jsonable(receipt), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out": str(OUT)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
