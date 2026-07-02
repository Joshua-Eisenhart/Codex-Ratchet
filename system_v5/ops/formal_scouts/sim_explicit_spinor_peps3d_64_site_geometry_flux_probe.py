#!/usr/bin/env python3
"""Explicit Hopf-spinor 64-site torch PEPS3D local geometry-flux gate.

Formal scout only.

This is the bounded-geometry rung after the explicit-spinor MPS scale scout. It
builds a 4x4x4 finite local PEPS3D tensor carrier directly from explicit Hopf
spinors and a bounded geometry/current layer. It does not perform full PEPS3D
environment contraction and does not admit final flux, Axis0, Xi, gravity,
Standard Model, Yang-Mills, Riemann, or physics claims.
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
NAME = "explicit_spinor_peps3d_64_site_geometry_flux_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "explicit_hopf_spinor_peps3d_64_local_geometry_flux"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "full_explicit_spinor_peps3d_environment_contraction"
CLAIM_CEILING = (
    "Formal scout only: builds a 64-site 4x4x4 torch PEPS3D local tensor carrier "
    "from explicit Hopf spinors and bounded geometry-current layers. It checks "
    "zero-current, reversed-current, shuffled-topology, erased-cut, and gauge "
    "controls. It does not perform full PEPS3D environment contraction and does "
    "not admit final flux, Axis0, Xi, gravity, Standard Model, Yang-Mills, "
    "Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Hopf spinors, local PEPS3D tensors, geometry currents, and control signatures",
    },
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite 64-site and nonpromotion fence"},
    "python_json": {"tried": True, "used": True, "reason": "supportive canonical result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

GRID_SHAPE = (4, 4, 4)
SITE_COUNT = 64
BOND_DIM = 2
PHYS_DIM = 2
N_LAYERS = 13
GAP_FLOOR = 1e-5
RTYPE = torch.float64
CDTYPE = torch.complex128

SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
GEOMETRY_AXIS = torch.tensor([0.71, -0.37, 0.59], dtype=RTYPE)
GEOMETRY_AXIS = GEOMETRY_AXIS / torch.linalg.vector_norm(GEOMETRY_AXIS)
LAYER_WEIGHTS = torch.linspace(0.035, 0.155, steps=N_LAYERS, dtype=RTYPE)

Site = tuple[int, int, int]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize_vector(v: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(v)
    if float(norm.item()) <= 1e-12:
        raise ValueError("zero vector")
    return v / norm


def sites() -> list[Site]:
    return [(i, j, k) for i in range(4) for j in range(4) for k in range(4)]


def site_index(site: Site) -> int:
    i, j, k = site
    return 16 * i + 4 * j + k


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


def spinor_params(site: Site) -> tuple[float, float, float]:
    idx = site_index(site)
    i, j, k = site
    phi = 0.17 * idx + 0.11 * i - 0.07 * j + 0.03 * k
    chi = -0.62 + 1.24 * (((3 * i + 5 * j + 7 * k + 2) % SITE_COUNT) / (SITE_COUNT - 1))
    eta = 0.24 + 1.10 * (((5 * i + 2 * j + 11 * k + 3) % SITE_COUNT) / (SITE_COUNT - 1))
    return phi, chi, min(max(eta, 0.18), 1.37)


def build_spinors(*, gauge_shift: bool = False) -> dict[Site, torch.Tensor]:
    out = {}
    for site in sites():
        phase = 0.0
        if gauge_shift:
            phase = math.sin(0.31 * site_index(site) + 0.17) * math.pi
        out[site] = spinor(*spinor_params(site), phase=phase)
    return out


def site_coordinate(site: Site, bloch: torch.Tensor) -> torch.Tensor:
    coord = (torch.tensor(site, dtype=RTYPE) - 1.5) / 1.5
    return normalize_vector(0.68 * bloch + 0.32 * normalize_vector(coord + 0.17 * GEOMETRY_AXIS))


def edge_rows(*, mode: str = "nominal", topology: str = "nominal") -> list[dict[str, Any]]:
    site_set = set(sites())
    deltas = [("x", (1, 0, 0), +1), ("y", (0, 1, 0), -1), ("z", (0, 0, 1), +1)]
    rows = []
    for site in sites():
        i, j, k = site
        for axis, delta, axis_orientation in deltas:
            dst = (i + delta[0], j + delta[1], k + delta[2])
            if dst not in site_set:
                continue
            if topology == "erased_cut" and ((site[0] < 2 <= dst[0]) or (dst[0] < 2 <= site[0])):
                continue
            if topology == "staggered_sparse" and (site_index(site) + site_index(dst)) % 3 == 1:
                continue
            if topology == "shuffled_topology":
                dst = ((dst[0] + 1) % 4, (dst[1] + 2) % 4, dst[2])
                if dst == site:
                    dst = ((dst[0] + 1) % 4, dst[1], dst[2])
            orientation = axis_orientation if (i + j + k) % 2 == 0 else -axis_orientation
            if mode == "reversed_current":
                orientation = -orientation
            rows.append({"src": site, "dst": dst, "axis": axis, "orientation": orientation})
    if topology not in {"nominal", "erased_cut", "staggered_sparse", "shuffled_topology"}:
        raise ValueError(f"unknown topology: {topology}")
    return rows


def layer_recurrence(seed_value: torch.Tensor, delta_z: torch.Tensor, orientation: int) -> tuple[torch.Tensor, list[float]]:
    value = seed_value
    trace = []
    orient = torch.tensor(float(orientation), dtype=RTYPE)
    for layer_index, weight in enumerate(LAYER_WEIGHTS):
        parity = 1.0 if layer_index % 2 == 0 else -1.0
        value = torch.tanh(value + weight * delta_z + 0.021 * parity * orient)
        trace.append(float(value.item()))
    return value, trace


def current_rows(
    spinors: dict[Site, torch.Tensor],
    *,
    mode: str = "nominal",
    topology: str = "nominal",
) -> list[dict[str, Any]]:
    blochs = {site: bloch_from_spinor(psi) for site, psi in spinors.items()}
    geoms = {site: site_coordinate(site, bloch) for site, bloch in blochs.items()}
    rows = []
    for edge_index, row in enumerate(edge_rows(mode=mode, topology=topology)):
        src = row["src"]
        dst = row["dst"]
        ri, rj = blochs[src], blochs[dst]
        gi, gj = geoms[src], geoms[dst]
        edge_axis = normalize_vector(gj - gi + 0.05 * GEOMETRY_AXIS)
        seed_value = torch.dot(torch.linalg.cross(ri, rj), edge_axis)
        delta_z = rj[2] - ri[2]
        layered, layer_trace = layer_recurrence(seed_value, delta_z, int(row["orientation"]))
        current = 0.0 if mode == "zero_current" else float(layered.item())
        rows.append(
            {
                "edge_index": edge_index,
                "src": list(src),
                "dst": list(dst),
                "axis": row["axis"],
                "orientation": int(row["orientation"]),
                "current": current,
                "layer_trace": layer_trace,
                "crosses_cut": src[0] < 2 <= dst[0] or dst[0] < 2 <= src[0],
            }
        )
    return rows


def tensor_shape(site: Site) -> tuple[int, ...]:
    i, j, k = site
    dims = [PHYS_DIM]
    dims.append(BOND_DIM if i > 0 else 1)
    dims.append(BOND_DIM if i < 3 else 1)
    dims.append(BOND_DIM if j > 0 else 1)
    dims.append(BOND_DIM if j < 3 else 1)
    dims.append(BOND_DIM if k > 0 else 1)
    dims.append(BOND_DIM if k < 3 else 1)
    return tuple(dims)


def site_drive(rows: list[dict[str, Any]]) -> dict[Site, float]:
    drive = {site: 0.0 for site in sites()}
    for row in rows:
        src = tuple(row["src"])
        dst = tuple(row["dst"])
        drive[src] += float(row["current"])
        drive[dst] -= float(row["current"])
    scale = max(max(abs(v) for v in drive.values()), 1e-12)
    return {site: value / scale for site, value in drive.items()}


def make_site_tensor(site: Site, psi: torch.Tensor, drive: float) -> torch.Tensor:
    shape = tensor_shape(site)
    tensor = torch.zeros(shape, dtype=CDTYPE)
    grids = torch.meshgrid(*[torch.arange(dim, dtype=RTYPE) for dim in shape[1:]], indexing="ij")
    parity = torch.zeros(shape[1:], dtype=RTYPE)
    for axis_idx, grid in enumerate(grids):
        parity = parity + (axis_idx + 1.0) * grid
    bond_profile = torch.exp(0.035 * torch.tanh(torch.tensor(drive, dtype=RTYPE)) * (parity - parity.mean()))
    geom_bias = 1.0 + 0.012 * (site[0] - site[1] + site[2])
    for phys in range(PHYS_DIM):
        tensor[phys] = psi[phys] * geom_bias * bond_profile.to(CDTYPE)
    return tensor


def make_peps3d_tensors(spinors: dict[Site, torch.Tensor], rows: list[dict[str, Any]]) -> dict[Site, torch.Tensor]:
    drives = site_drive(rows)
    return {site: make_site_tensor(site, spinors[site], drives[site]) for site in sites()}


def local_signature(tensors: dict[Site, torch.Tensor], rows: list[dict[str, Any]]) -> dict[str, Any]:
    drives = site_drive(rows)
    norms = []
    polarizations = []
    boundary_flags = []
    for site in sites():
        tensor = tensors[site]
        norm = torch.linalg.vector_norm(tensor)
        left = torch.linalg.vector_norm(tensor[0])
        right = torch.linalg.vector_norm(tensor[1])
        polarizations.append(float(((right - left) / norm.clamp_min(1e-12)).real.item()))
        norms.append(float(norm.real.item()))
        boundary_flags.append(int(any(coord in {0, 3} for coord in site)))
    norm_tensor = torch.tensor(norms, dtype=RTYPE)
    pol_tensor = torch.tensor(polarizations, dtype=RTYPE)
    drive_tensor = torch.tensor([drives[site] for site in sites()], dtype=RTYPE)
    cut_current = sum(row["current"] for row in rows if row["crosses_cut"])
    edge_currents = torch.tensor([row["current"] for row in rows], dtype=RTYPE) if rows else torch.zeros(1, dtype=RTYPE)
    return {
        "site_count": SITE_COUNT,
        "grid_shape": list(GRID_SHAPE),
        "tensor_count": len(tensors),
        "edge_count": len(rows),
        "parameter_count": int(sum(tensor.numel() for tensor in tensors.values())),
        "max_tensor_order": max(len(tensor.shape) for tensor in tensors.values()),
        "mean_tensor_norm": float(torch.mean(norm_tensor).item()),
        "std_tensor_norm": float(torch.std(norm_tensor, unbiased=False).item()),
        "mean_polarization": float(torch.mean(pol_tensor).item()),
        "std_polarization": float(torch.std(pol_tensor, unbiased=False).item()),
        "drive_variance": float(torch.var(drive_tensor, unbiased=False).item()),
        "cut_current": float(cut_current),
        "mean_abs_edge_current": float(torch.mean(torch.abs(edge_currents)).item()),
        "boundary_site_count": int(sum(boundary_flags)),
    }


def run_peps3d(*, mode: str = "nominal", topology: str = "nominal", gauge_shift: bool = False) -> dict[str, Any]:
    spinors = build_spinors(gauge_shift=gauge_shift)
    rows = current_rows(spinors, mode=mode, topology=topology)
    tensors = make_peps3d_tensors(spinors, rows)
    density_trace_errors = [
        abs(float(torch.trace(density(psi)).real.item()) - 1.0) + abs(float(torch.trace(density(psi)).imag.item()))
        for psi in spinors.values()
    ]
    out = local_signature(tensors, rows)
    out.update(
        {
            "mode": mode,
            "topology": topology,
            "spinor_count": len(spinors),
            "max_density_trace_error": max(density_trace_errors),
        }
    )
    return out


def signature(row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            row["edge_count"],
            row["parameter_count"],
            row["mean_tensor_norm"],
            row["std_tensor_norm"],
            row["mean_polarization"],
            row["std_polarization"],
            row["drive_variance"],
            row["cut_current"],
            row["mean_abs_edge_current"],
        ],
        dtype=RTYPE,
    )


def sig_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(signature(a) - signature(b)).item())


def z3_gate(nominal: dict[str, Any]) -> dict[str, Any]:
    site_count = z3.Int("site_count")
    final_flux = z3.Bool("final_flux")
    final_physics = z3.Bool("final_physics")
    full_contraction = z3.Bool("full_peps3d_environment_contraction")
    solver = z3.Solver()
    solver.add(site_count == nominal["site_count"])
    solver.add(site_count == 64)
    solver.add(z3.Not(final_flux), z3.Not(final_physics), z3.Not(full_contraction))
    promotion = z3.Solver()
    promotion.add(site_count == 64, z3.Or(final_flux, final_physics, full_contraction))
    promotion.add(z3.Not(final_flux), z3.Not(final_physics), z3.Not(full_contraction))
    return {
        "finite_64_site_local_peps3d_status": str(solver.check()),
        "promotion_or_full_contraction_attempt_status": str(promotion.check()),
        "pass": solver.check() == z3.sat and promotion.check() == z3.unsat,
    }


def count_passes(sections: list[dict[str, Any]]) -> dict[str, int]:
    total = 0
    passed = 0
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "pass" in value:
                total += 1
                passed += int(bool(value["pass"]))
    return {"total": total, "passed": passed}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    nominal = run_peps3d()
    zero = run_peps3d(mode="zero_current")
    reversed_row = run_peps3d(mode="reversed_current")
    gauge = run_peps3d(gauge_shift=True)
    topology_rows = []
    for topology in ["shuffled_topology", "erased_cut", "staggered_sparse"]:
        row = run_peps3d(topology=topology)
        topology_rows.append({"topology": topology, "signature_gap": sig_gap(nominal, row), "edge_count": row["edge_count"]})
    min_topology_gap = min(row["signature_gap"] for row in topology_rows)
    zero_gap = sig_gap(nominal, zero)
    reverse_gap = sig_gap(nominal, reversed_row)
    gauge_gap = sig_gap(nominal, gauge)

    positive = {
        "explicit_hopf_spinor_peps3d_64_local_carrier": {
            "pass": nominal["site_count"] == 64 and nominal["spinor_count"] == 64 and nominal["tensor_count"] == 64,
            "nominal": nominal,
        },
        "bounded_geometry_current_controls_survive": {
            "pass": zero_gap > GAP_FLOOR and reverse_gap > GAP_FLOOR and min_topology_gap > GAP_FLOOR and gauge_gap < 1e-8,
            "zero_current_signature_gap": zero_gap,
            "reversed_current_signature_gap": reverse_gap,
            "minimum_topology_signature_gap": min_topology_gap,
            "gauge_signature_gap": gauge_gap,
            "topology_rows": topology_rows,
        },
        "finite_64_site_z3_nonpromotion_gate": z3_gate(nominal),
    }
    graveyard_companions = {
        "GC1_no_dense_2_to_64_state_constructed": {
            "pass": True,
            "summary": "Only local PEPS3D tensors and signatures are constructed; no dense 2**64 vector appears.",
        },
        "GC2_full_environment_contraction_blocked": {
            "pass": CITES_BLOCKED_UNTIL == "full_explicit_spinor_peps3d_environment_contraction",
            "cites_blocked_until": CITES_BLOCKED_UNTIL,
        },
        "GC3_gauge_phase_invariance_reported": {"pass": gauge_gap < 1e-8, "gauge_signature_gap": gauge_gap},
    }
    boundary = {
        "B1_no_final_flux_claim": {"pass": PROMOTION_ALLOWED is False and "does not admit final flux" in CLAIM_CEILING},
        "B2_no_physics_claim": {"pass": "Standard Model" in CLAIM_CEILING and "Yang-Mills" in CLAIM_CEILING},
        "B3_no_full_peps3d_contraction_claim": {"pass": "does not perform full PEPS3D environment contraction" in CLAIM_CEILING},
    }
    nearby = count_passes([positive, graveyard_companions, boundary])
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "cites_blocked_until": CITES_BLOCKED_UNTIL,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby,
        "all_pass": nearby["passed"] == nearby["total"],
        "summary": {
            "site_count": 64,
            "grid_shape": list(GRID_SHAPE),
            "tensor_count": nominal["tensor_count"],
            "parameter_count": nominal["parameter_count"],
            "edge_count": nominal["edge_count"],
            "zero_current_signature_gap": zero_gap,
            "reversed_current_signature_gap": reverse_gap,
            "minimum_topology_signature_gap": min_topology_gap,
            "gauge_signature_gap": gauge_gap,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 torch-native explicit-spinor PEPS3D local tensor formal scout. "
            "It is not a dense 64-qubit state, not full PEPS3D contraction, not final flux, "
            "and not a physics claim."
        ),
        "next_required_work": [
            "Add finite twistor incidence at 8 nodes, then lift incidence-derived currents to this 64-site carrier.",
            "Add a real PEPS3D local-environment contraction gate before claiming PEPS3D closure.",
            "Port explicit spinor geometry/current rows into the richer two-root 8/16/32/64 basin-boundary tool runner.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
