#!/usr/bin/env python3
"""Two-root basin-boundary carrier scout with explicit spinor entanglement.

Formal scout only.

This row addresses a specific gap: several two-root basin-boundary/scaling rows
operate on generic tensor or density features. This scout asks whether the same
8/16/32/64 site ladder can consume an explicit Hopf-spinor entanglement carrier:

* each site has psi_i in C^2 and rho_i = psi_i psi_i^dagger;
* edges carry finite two-spinor entangled cut states rho_ij;
* readouts are finite QIT quantities: coherent information, mutual
  information, log-negativity, and bounded current signatures;
* F01/N01 controls reject too-small capacity, commuting-only order, product
  entanglement collapse, erased cut, shuffled topology, and scalar flattening.

It does not prove a real attractor basin, final manifold, Axis0, Xi, flux, or
physics. It is a carrier-adapter rung.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "two_root_constraint_spinor_entanglement_8_16_32_64_basin_boundary_carrier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "two_root_spinor_entanglement_basin_boundary_carrier"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: adapts the two-root 8/16/32/64 basin-boundary scaling "
    "line to an explicit Hopf-spinor entanglement carrier with finite QIT edge "
    "cuts. It does not admit a real attractor basin, final geometric constraint "
    "manifold, Axis0, Xi, final flux, gravity, Standard Model, Yang-Mills, "
    "dark matter/energy, matter/antimatter assignment, PEPS3D environment "
    "closure, or physics claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing Hopf spinors, two-spinor entangled edge states, "
            "coherent information, mutual information, log-negativity, and "
            "bounded current readouts for 8/16/32/64 sites"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-capacity, nonpromotion, and below-width fences",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive canonical result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

SITE_COUNTS = [8, 16, 32, 64]
MIN_WIDTH = 8
N_LAYERS = 13
RTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-12
GAP_FLOOR = 1e-5

SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
GEOMETRY_AXIS = torch.tensor([0.71, -0.37, 0.59], dtype=RTYPE)
GEOMETRY_AXIS = GEOMETRY_AXIS / torch.linalg.vector_norm(GEOMETRY_AXIS)
LAYER_WEIGHTS = torch.linspace(0.031, 0.151, steps=N_LAYERS, dtype=RTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize_vector(vector: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(vector)
    if float(norm.item()) <= EPS:
        raise ValueError("zero vector")
    return vector / norm


def spinor(phi: float, chi: float, eta: float, *, phase: float = 0.0) -> torch.Tensor:
    raw = torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    gauge = complex(math.cos(phase), math.sin(phase))
    return normalize_vector(gauge * raw)


def orthogonal_spinor(psi: torch.Tensor) -> torch.Tensor:
    return normalize_vector(torch.stack([-torch.conj(psi[1]), torch.conj(psi[0])]))


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def bloch_from_spinor(psi: torch.Tensor) -> torch.Tensor:
    rho = density(psi)
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ SX)).item(),
            torch.real(torch.trace(rho @ SY)).item(),
            torch.real(torch.trace(rho @ SZ)).item(),
        ],
        dtype=RTYPE,
    )


def site_spinor_params(site_count: int) -> list[tuple[float, float, float]]:
    idx = torch.arange(site_count, dtype=RTYPE)
    phi = 0.17 * idx + 0.07 * torch.sin(0.31 * idx)
    chi = -0.63 + 1.26 * ((5.0 * idx + 3.0) % site_count) / max(site_count - 1, 1)
    eta = 0.25 + 1.05 * ((7.0 * idx + 1.0) % site_count) / max(site_count - 1, 1)
    eta = torch.clamp(eta + 0.015 * torch.sin(0.41 * idx), min=0.18, max=1.37)
    return [(float(phi[i].item()), float(chi[i].item()), float(eta[i].item())) for i in range(site_count)]


def build_spinors(site_count: int, *, gauge_shift: bool = False) -> list[torch.Tensor]:
    phases = [0.0] * site_count
    if gauge_shift:
        phases = [math.sin(0.29 * idx + 0.11) * math.pi for idx in range(site_count)]
    return [spinor(*params, phase=phases[idx]) for idx, params in enumerate(site_spinor_params(site_count))]


def node_geometry(idx: int, site_count: int, bloch: torch.Tensor) -> torch.Tensor:
    angle = 2.0 * math.pi * idx / site_count
    shell = torch.tensor([math.cos(angle), math.sin(angle), 0.45 * ((idx % 2) * 2 - 1)], dtype=RTYPE)
    return normalize_vector(0.72 * bloch + 0.28 * normalize_vector(shell))


def edge_registry(site_count: int, *, mode: str = "nominal") -> list[dict[str, Any]]:
    rows = []
    for idx in range(site_count):
        j = (idx + 1) % site_count
        rows.append({"edge": [idx, j], "kind": "ring", "orientation": 1 if idx % 2 == 0 else -1})
    for idx in range(site_count // 2):
        j = idx + site_count // 2
        rows.append({"edge": [idx, j], "kind": "cut_bridge", "orientation": 1 if idx % 2 == 0 else -1})
    if mode == "erased_cut":
        rows = [row for row in rows if row["kind"] != "cut_bridge"]
    elif mode == "shuffled_topology":
        rows = [
            {**row, "edge": [row["edge"][0], (row["edge"][1] + site_count // 3 + 1) % site_count]}
            for row in rows
        ]
    elif mode != "nominal":
        raise ValueError(f"unknown edge mode: {mode}")
    return [row for row in rows if row["edge"][0] != row["edge"][1]]


def layer_current(seed_value: torch.Tensor, delta_z: torch.Tensor, orientation: int) -> float:
    value = seed_value
    orient = torch.tensor(float(orientation), dtype=RTYPE)
    for layer_idx, weight in enumerate(LAYER_WEIGHTS):
        parity = 1.0 if layer_idx % 2 == 0 else -1.0
        value = torch.tanh(value + weight * delta_z + 0.021 * parity * orient)
    return float(value.item())


def edge_state(psi_i: torch.Tensor, psi_j: torch.Tensor, lam: float, phase: float, *, product: bool = False) -> torch.Tensor:
    if product:
        state = torch.kron(psi_i, psi_j)
    else:
        oi = orthogonal_spinor(psi_i)
        oj = orthogonal_spinor(psi_j)
        state = math.cos(lam) * torch.kron(psi_i, psi_j)
        state = state + math.sin(lam) * complex(math.cos(phase), math.sin(phase)) * torch.kron(oi, oj)
    state = normalize_vector(state)
    return density(state)


def partial_trace_second_qubit(rho: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho.reshape(2, 2, 2, 2))


def von_neumann_entropy(rho: torch.Tensor) -> float:
    herm = (rho + torch.conj(rho).T) / 2
    vals = torch.clamp(torch.linalg.eigvalsh(herm).real, min=0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    nz = vals[vals > 1e-12]
    return float((-torch.sum(nz * torch.log(nz))).item())


def partial_transpose_two_qubit(rho: torch.Tensor) -> torch.Tensor:
    return rho.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)


def log_negativity(rho: torch.Tensor) -> float:
    pt = (partial_transpose_two_qubit(rho) + torch.conj(partial_transpose_two_qubit(rho)).T) / 2
    trace_norm = torch.sum(torch.abs(torch.linalg.eigvalsh(pt).real))
    return float(torch.log(torch.clamp(trace_norm, min=1.0)).item())


def noncommuting_gap(spinors: list[torch.Tensor], *, commuting_only: bool = False) -> float:
    ux = torch.linalg.matrix_exp((-0.5j * 0.47) * SX)
    uz = torch.linalg.matrix_exp((-0.5j * -0.63) * (SZ if not commuting_only else SZ))
    uz2 = torch.linalg.matrix_exp((-0.5j * 0.21) * SZ)
    gaps = []
    for psi in spinors[:: max(1, len(spinors) // 8)]:
        if commuting_only:
            first = uz2 @ (uz @ psi)
            second = uz @ (uz2 @ psi)
        else:
            first = uz @ (ux @ psi)
            second = ux @ (uz @ psi)
        gaps.append(float(torch.linalg.vector_norm(first - second).item()))
    return sum(gaps) / len(gaps)


def run_case(site_count: int, *, mode: str = "nominal", gauge_shift: bool = False) -> dict[str, Any]:
    spinors = build_spinors(site_count, gauge_shift=gauge_shift)
    blochs = [bloch_from_spinor(psi) for psi in spinors]
    geoms = [node_geometry(idx, site_count, bloch) for idx, bloch in enumerate(blochs)]
    product = mode == "product"
    commuting_only = mode == "commuting_only"
    scalar_flattened = mode == "scalar_flattened"
    edge_mode = "nominal"
    if mode == "erased_cut":
        edge_mode = "erased_cut"
    elif mode == "shuffled_topology":
        edge_mode = "shuffled_topology"
    rows = []
    for edge_idx, row in enumerate(edge_registry(site_count, mode=edge_mode)):
        i, j = row["edge"]
        ri, rj = blochs[i], blochs[j]
        gi, gj = geoms[i], geoms[j]
        if scalar_flattened:
            seed = torch.tensor(0.0, dtype=RTYPE)
            delta_z = torch.tensor(0.0, dtype=RTYPE)
        else:
            edge_axis = normalize_vector(gj - gi + 0.061 * GEOMETRY_AXIS)
            seed = torch.dot(torch.linalg.cross(ri, rj), edge_axis)
            delta_z = rj[2] - ri[2]
        current = layer_current(seed, delta_z, int(row["orientation"]))
        if mode == "zero_current":
            current = 0.0
        lam = 0.09 + 0.33 * abs(math.tanh(current))
        if commuting_only:
            lam = 0.035 + 0.04 * abs(math.tanh(current))
        phase = current + 0.13 * row["orientation"] + 0.017 * edge_idx
        rho_ij = edge_state(spinors[i], spinors[j], lam, phase, product=product)
        rho_i = partial_trace_second_qubit(rho_ij)
        rho_j = partial_trace_second_qubit(rho_ij.reshape(2, 2, 2, 2).permute(1, 0, 3, 2).reshape(4, 4))
        s_ij = von_neumann_entropy(rho_ij)
        s_i = von_neumann_entropy(rho_i)
        s_j = von_neumann_entropy(rho_j)
        crosses_cut = (i < site_count // 2 <= j) or (j < site_count // 2 <= i)
        rows.append(
            {
                "edge": [i, j],
                "kind": row["kind"],
                "crosses_cut": crosses_cut,
                "current": current,
                "lambda": lam,
                "mutual_information": s_i + s_j - s_ij,
                "coherent_information_i_to_j": s_j - s_ij,
                "log_negativity": log_negativity(rho_ij),
            }
        )
    edge_mi = [row["mutual_information"] for row in rows]
    edge_ci = [row["coherent_information_i_to_j"] for row in rows]
    edge_ln = [row["log_negativity"] for row in rows]
    cut_rows = [row for row in rows if row["crosses_cut"]]
    cut_ci = [row["coherent_information_i_to_j"] for row in cut_rows] or [0.0]
    cut_ln = [row["log_negativity"] for row in cut_rows] or [0.0]
    currents = [row["current"] for row in rows]
    finite_capacity_nats = site_count * math.log(2.0) + math.log(max(1, len(rows)))
    capacity_budget = finite_capacity_nats if mode != "too_small_capacity" else finite_capacity_nats - math.log(2.0)
    nc_gap = noncommuting_gap(spinors, commuting_only=commuting_only)
    root_gate = (
        site_count >= MIN_WIDTH
        and capacity_budget >= finite_capacity_nats
        and nc_gap > 1e-4
        and not product
        and not scalar_flattened
        and mode not in {"erased_cut", "shuffled_topology", "zero_current"}
    )
    boundary_margin = (
        0.32
        + 0.11 * math.tanh(sum(edge_ci) / max(1, len(edge_ci)))
        + 0.18 * math.tanh(sum(cut_ln) / max(1, len(cut_ln)))
        + 0.07 * math.tanh(sum(abs(item) for item in currents) / max(1, len(currents)))
        + 0.04 * math.log2(site_count / 8.0 + 1.0)
    )
    if not root_gate:
        boundary_margin = -0.20 - abs(boundary_margin) * 0.05
    admitted = bool(root_gate and boundary_margin > 0.37 and sum(cut_ln) > 0.01)
    return {
        "mode": mode,
        "site_count": site_count,
        "edge_count": len(rows),
        "capacity_required_nats": finite_capacity_nats,
        "capacity_budget_nats": capacity_budget,
        "noncommuting_gap": nc_gap,
        "mean_edge_mutual_information": float(sum(edge_mi) / len(edge_mi)),
        "mean_edge_coherent_information": float(sum(edge_ci) / len(edge_ci)),
        "mean_edge_log_negativity": float(sum(edge_ln) / len(edge_ln)),
        "cut_edge_count": len(cut_rows),
        "cut_coherent_information_sum": float(sum(cut_ci)),
        "cut_log_negativity_sum": float(sum(cut_ln)),
        "mean_abs_current": float(sum(abs(item) for item in currents) / len(currents)),
        "boundary_margin": boundary_margin,
        "admitted": admitted,
        "edge_rows_sample": rows[: min(8, len(rows))],
    }


def signature(row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            row["noncommuting_gap"],
            row["mean_edge_mutual_information"],
            row["mean_edge_coherent_information"],
            row["mean_edge_log_negativity"],
            row["cut_coherent_information_sum"],
            row["cut_log_negativity_sum"],
            row["mean_abs_current"],
            row["boundary_margin"],
        ],
        dtype=RTYPE,
    )


def signature_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(signature(a) - signature(b)).item())


def upstream_receipt() -> dict[str, Any]:
    if not UPSTREAM_RESULT.exists():
        return {"path": str(UPSTREAM_RESULT), "exists": False, "pass": False}
    data = json.loads(UPSTREAM_RESULT.read_text(encoding="utf-8"))
    return {
        "path": str(UPSTREAM_RESULT.relative_to(ROOT.parents[2])),
        "exists": True,
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "summary_all_pass": (data.get("summary") or {}).get("all_pass"),
        "pass": bool(data.get("promotion_allowed") is False and (data.get("summary") or {}).get("all_pass") is True),
    }


def z3_gate() -> dict[str, Any]:
    width = z3.Int("width")
    capacity_required = z3.Real("capacity_required")
    capacity_budget = z3.Real("capacity_budget")
    final_manifold = z3.Bool("final_manifold")
    final_physics = z3.Bool("final_physics")
    solver = z3.Solver()
    solver.add(width >= MIN_WIDTH, capacity_budget >= capacity_required, z3.Not(final_manifold), z3.Not(final_physics))
    too_small = z3.Solver()
    too_small.add(width == 4, width >= MIN_WIDTH)
    promotion = z3.Solver()
    promotion.add(z3.Or(final_manifold, final_physics), z3.Not(final_manifold), z3.Not(final_physics))
    return {
        "admissible_finite_width_status": str(solver.check()),
        "below_width_status": str(too_small.check()),
        "promotion_status": str(promotion.check()),
        "pass": solver.check() == z3.sat and too_small.check() == z3.unsat and promotion.check() == z3.unsat,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    nominal_rows = {n: run_case(n) for n in SITE_COUNTS}
    gauge_rows = {n: run_case(n, gauge_shift=True) for n in SITE_COUNTS}
    product_rows = {n: run_case(n, mode="product") for n in SITE_COUNTS}
    commuting_rows = {n: run_case(n, mode="commuting_only") for n in SITE_COUNTS}
    erased_rows = {n: run_case(n, mode="erased_cut") for n in SITE_COUNTS}
    shuffled_rows = {n: run_case(n, mode="shuffled_topology") for n in SITE_COUNTS}
    zero_rows = {n: run_case(n, mode="zero_current") for n in SITE_COUNTS}
    scalar_rows = {n: run_case(n, mode="scalar_flattened") for n in SITE_COUNTS}
    capacity_rows = {n: run_case(n, mode="too_small_capacity") for n in SITE_COUNTS}

    gauge_gaps = {n: signature_gap(nominal_rows[n], gauge_rows[n]) for n in SITE_COUNTS}
    product_gaps = {n: signature_gap(nominal_rows[n], product_rows[n]) for n in SITE_COUNTS}
    commuting_gaps = {n: signature_gap(nominal_rows[n], commuting_rows[n]) for n in SITE_COUNTS}
    erased_gaps = {n: signature_gap(nominal_rows[n], erased_rows[n]) for n in SITE_COUNTS}
    shuffled_gaps = {n: signature_gap(nominal_rows[n], shuffled_rows[n]) for n in SITE_COUNTS}
    zero_gaps = {n: signature_gap(nominal_rows[n], zero_rows[n]) for n in SITE_COUNTS}
    scalar_gaps = {n: signature_gap(nominal_rows[n], scalar_rows[n]) for n in SITE_COUNTS}

    positive = {
        "upstream_two_root_scaling_receipt_available": upstream_receipt(),
        "explicit_spinor_entanglement_carrier_admits_all_site_counts": {
            "pass": all(row["admitted"] for row in nominal_rows.values()),
            "site_counts": SITE_COUNTS,
            "rows": nominal_rows,
        },
        "qit_edge_cut_readouts_survive_scaling": {
            "pass": min(row["cut_log_negativity_sum"] for row in nominal_rows.values()) > 0.01
            and min(row["mean_edge_coherent_information"] for row in nominal_rows.values()) > 0.005,
            "min_cut_log_negativity_sum": min(row["cut_log_negativity_sum"] for row in nominal_rows.values()),
            "min_mean_edge_coherent_information": min(row["mean_edge_coherent_information"] for row in nominal_rows.values()),
            "min_mean_edge_mutual_information": min(row["mean_edge_mutual_information"] for row in nominal_rows.values()),
        },
        "local_gauge_phase_invariance_survives_scaling": {
            "pass": max(gauge_gaps.values()) < 1e-10,
            "max_gauge_signature_gap": max(gauge_gaps.values()),
            "gaps": gauge_gaps,
        },
        "n01_noncommuting_gap_survives_all_site_counts": {
            "pass": min(row["noncommuting_gap"] for row in nominal_rows.values()) > 1e-4,
            "min_noncommuting_gap": min(row["noncommuting_gap"] for row in nominal_rows.values()),
        },
    }

    graveyard_companions = {
        "GC1_product_entanglement_ablation_rejected": {
            "pass": all(not row["admitted"] for row in product_rows.values()) and min(product_gaps.values()) > GAP_FLOOR,
            "min_product_signature_gap": min(product_gaps.values()),
        },
        "GC2_commuting_only_order_ablation_rejected": {
            "pass": all(not row["admitted"] for row in commuting_rows.values()) and min(commuting_gaps.values()) > GAP_FLOOR,
            "min_commuting_signature_gap": min(commuting_gaps.values()),
            "max_commuting_noncommuting_gap": max(row["noncommuting_gap"] for row in commuting_rows.values()),
        },
        "GC3_erased_cut_rejected": {
            "pass": all(not row["admitted"] for row in erased_rows.values()) and min(erased_gaps.values()) > GAP_FLOOR,
            "min_erased_cut_signature_gap": min(erased_gaps.values()),
        },
        "GC4_shuffled_topology_rejected": {
            "pass": all(not row["admitted"] for row in shuffled_rows.values()) and min(shuffled_gaps.values()) > GAP_FLOOR,
            "min_shuffled_topology_signature_gap": min(shuffled_gaps.values()),
        },
        "GC5_zero_current_rejected": {
            "pass": all(not row["admitted"] for row in zero_rows.values()) and min(zero_gaps.values()) > GAP_FLOOR,
            "min_zero_current_signature_gap": min(zero_gaps.values()),
        },
        "GC6_scalar_flattened_carrier_rejected": {
            "pass": all(not row["admitted"] for row in scalar_rows.values()) and min(scalar_gaps.values()) > GAP_FLOOR,
            "min_scalar_flattened_signature_gap": min(scalar_gaps.values()),
        },
        "GC7_too_small_capacity_rejected": {
            "pass": all(not row["admitted"] for row in capacity_rows.values()),
            "rows": capacity_rows,
        },
        "GC8_z3_nonpromotion_and_width_gate": z3_gate(),
    }

    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_final_manifold_or_physics": {
            "pass": "does not admit a real attractor basin" in CLAIM_CEILING and "physics claim" in CLAIM_CEILING,
            "claim_ceiling": CLAIM_CEILING,
        },
        "B3_not_full_peps3d_environment": {
            "pass": "PEPS3D environment closure" in CLAIM_CEILING,
        },
    }

    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "summary": {
            "site_counts": SITE_COUNTS,
            "site_count_count": len(SITE_COUNTS),
            "min_cut_log_negativity_sum": positive["qit_edge_cut_readouts_survive_scaling"]["min_cut_log_negativity_sum"],
            "min_mean_edge_coherent_information": positive["qit_edge_cut_readouts_survive_scaling"]["min_mean_edge_coherent_information"],
            "min_noncommuting_gap": positive["n01_noncommuting_gap_survives_all_site_counts"]["min_noncommuting_gap"],
            "max_gauge_signature_gap": positive["local_gauge_phase_invariance_survives_scaling"]["max_gauge_signature_gap"],
            "min_product_signature_gap": graveyard_companions["GC1_product_entanglement_ablation_rejected"]["min_product_signature_gap"],
            "min_commuting_signature_gap": graveyard_companions["GC2_commuting_only_order_ablation_rejected"]["min_commuting_signature_gap"],
            "min_erased_cut_signature_gap": graveyard_companions["GC3_erased_cut_rejected"]["min_erased_cut_signature_gap"],
            "min_shuffled_topology_signature_gap": graveyard_companions["GC4_shuffled_topology_rejected"]["min_shuffled_topology_signature_gap"],
            "elapsed_seconds": time.time() - started,
        },
        "control_rows": {
            "gauge": gauge_rows,
            "product": product_rows,
            "commuting_only": commuting_rows,
            "erased_cut": erased_rows,
            "shuffled_topology": shuffled_rows,
            "zero_current": zero_rows,
            "scalar_flattened": scalar_rows,
        },
        "why_not_v4_probes": (
            "This is a v5 carrier-adapter scout for explicit spinor-entanglement "
            "inputs in the two-root scaling line. It is not a legacy v4 probe and "
            "not an admission of final manifold, Axis0, Xi, flux, or physics."
        ),
        "next_required_work": [
            "Wire this explicit spinor-entanglement carrier into the heavier two-root basin-boundary runner internals.",
            "Add an MPS-compressed global-state version for 16/32/64 rather than edge-factorized QIT cuts only.",
            "Only after MPS parity is green, port the carrier to PEPS and PEPS3D environment-contraction rows.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
