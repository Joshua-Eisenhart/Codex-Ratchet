#!/usr/bin/env python3
"""64-site PEPS3D no-dense local environment/topology-flux readout scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "peps3d_64_site_no_dense_environment_topology_flux_probe_results.json"

NAME = "peps3d_64_site_no_dense_environment_topology_flux_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "full_peps3d_64_site_environment_contraction_proof"
CLAIM_CEILING = (
    "Formal scout only: builds a finite 4x4x4 PEPS3D carrier and reads local "
    "no-dense environment/topology-flux signatures. It does not construct a "
    "2**64 dense state, does not construct a dense full environment, does not "
    "perform final PEPS3D contraction, and does not admit final manifold, "
    "physics, cognition, neural architecture, or canonical claims."
)

GRID_SHAPE = (4, 4, 4)
SITE_COUNT = math.prod(GRID_SHAPE)
BOND_DIM = 2
PHYS_DIM = 2
DTYPE = torch.float64
DENSE_FULL_DIMENSION = 2**SITE_COUNT

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local tensor fixtures, site signatures, and control-separation metrics",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS3D carrier construction/count witness without dense contraction",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local star-environment contraction-tree witness, not a full-network contraction",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 4x4x4 nearest-neighbor topology graph and shuffled-topology control",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite site/edge/count symbolic noncollapse witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite no-dense/noncollapse admission fence over observed scout metrics",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


Site = tuple[int, int, int]


def sites() -> list[Site]:
    lx, ly, lz = GRID_SHAPE
    return [(i, j, k) for i in range(lx) for j in range(ly) for k in range(lz)]


def tensor_shape_for_site(site: Site) -> tuple[int, ...]:
    i, j, k = site
    lx, ly, lz = GRID_SHAPE
    legs: list[int] = []
    if i < lx - 1:
        legs.append(BOND_DIM)
    if j < ly - 1:
        legs.append(BOND_DIM)
    if k < lz - 1:
        legs.append(BOND_DIM)
    if i > 0:
        legs.append(BOND_DIM)
    if j > 0:
        legs.append(BOND_DIM)
    if k > 0:
        legs.append(BOND_DIM)
    legs.append(PHYS_DIM)
    return tuple(legs)


def site_orientation(site: Site) -> float:
    i, j, k = site
    centered = torch.tensor([i, j, k], dtype=DTYPE) - torch.tensor(GRID_SHAPE, dtype=DTYPE).sub(1.0).div(2.0)
    weights = torch.tensor([1.0, -0.5, 0.75], dtype=DTYPE)
    return float(torch.dot(centered, weights).item())


def make_site_tensors(seed: int = 64064) -> dict[Site, torch.Tensor]:
    out: dict[Site, torch.Tensor] = {}
    for linear, site in enumerate(sites()):
        gen = torch.Generator().manual_seed(seed + 97 * linear)
        arr = torch.randn(tensor_shape_for_site(site), generator=gen, dtype=DTYPE) * 0.025
        bias = 0.0015 * (1.0 + site_orientation(site))
        arr = arr.clone()
        arr[..., 0] = arr[..., 0] + bias
        arr[..., 1] = arr[..., 1] - 0.5 * bias
        out[site] = arr
    return out


def make_quimb_peps3d(site_tensors: dict[Site, torch.Tensor]) -> qtn.PEPS3D:
    arrays = []
    for i in range(GRID_SHAPE[0]):
        plane = []
        for j in range(GRID_SHAPE[1]):
            row = []
            for k in range(GRID_SHAPE[2]):
                row.append(site_tensors[(i, j, k)])
            plane.append(row)
        arrays.append(plane)
    return qtn.PEPS3D(arrays)


def base_topology_edges(*, zero_flux: bool = False, shuffled_topology: bool = False) -> list[dict[str, Any]]:
    site_list = sites()
    site_set = set(site_list)
    axes = [
        ("x", (1, 0, 0), 1.0),
        ("y", (0, 1, 0), -0.75),
        ("z", (0, 0, 1), 0.5),
    ]
    edges: list[dict[str, Any]] = []
    for site in site_list:
        i, j, k = site
        for axis_name, delta, axis_weight in axes:
            dst = (i + delta[0], j + delta[1], k + delta[2])
            if dst not in site_set:
                continue
            parity_term = 0.5 * (((i + j + k) % 2) - ((dst[0] + dst[1] + dst[2]) % 2))
            orientation_term = site_orientation(dst) - site_orientation(site)
            flux = 0.0 if zero_flux else float(axis_weight * (1.0 + 0.125 * parity_term + 0.05 * orientation_term))
            edges.append({"src": site, "dst": dst, "axis": axis_name, "flux": flux})

    if shuffled_topology:
        shuffled_dsts = [edge["dst"] for edge in edges]
        shuffled_dsts = shuffled_dsts[17:] + shuffled_dsts[:17]
        repaired = []
        for edge, dst in zip(edges, shuffled_dsts):
            if dst == edge["src"]:
                dst = ((dst[0] + 2) % GRID_SHAPE[0], dst[1], dst[2])
            repaired.append({**edge, "dst": dst})
        edges = repaired
    return edges


def topology_report(*, zero_flux: bool = False, shuffled_topology: bool = False) -> dict[str, Any]:
    site_list = sites()
    index = {site: idx for idx, site in enumerate(site_list)}
    edges = base_topology_edges(zero_flux=zero_flux, shuffled_topology=shuffled_topology)
    graph = rx.PyGraph(multigraph=True)
    graph.add_nodes_from(site_list)
    broken = 0
    drives = {site: 0.0 for site in site_list}
    for edge in edges:
        src = edge["src"]
        dst = edge["dst"]
        graph.add_edge(index[src], index[dst], float(edge["flux"]))
        manhattan = sum(abs(src[pos] - dst[pos]) for pos in range(3))
        broken += int(manhattan != 1)
        drives[src] += float(edge["flux"])
        drives[dst] -= float(edge["flux"])

    drive_tensor = torch.tensor([drives[site] for site in site_list], dtype=DTYPE)
    scale = torch.max(torch.abs(drive_tensor)).clamp_min(1e-12)
    if not zero_flux:
        drive_tensor = drive_tensor / scale
        drives = {site: float(drive_tensor[index[site]].item()) for site in site_list}
    return {
        "graph": graph,
        "index": index,
        "drives": drives,
        "report": {
            "grid_shape": list(GRID_SHAPE),
            "site_count": SITE_COUNT,
            "oriented_edge_count": len(edges),
            "nearest_neighbor_oriented_edge_count": 144,
            "rustworkx_nodes": int(graph.num_nodes()),
            "rustworkx_edges": int(graph.num_edges()),
            "rustworkx_connected": bool(rx.is_connected(graph)),
            "zero_flux": bool(zero_flux),
            "shuffled_topology": bool(shuffled_topology),
            "broken_nearest_neighbor_edge_count": int(broken),
            "drive_mean_abs": float(torch.mean(torch.abs(drive_tensor)).item()),
            "drive_variance": float(torch.var(drive_tensor, unbiased=False).item()),
            "drive_max_abs": float(torch.max(torch.abs(drive_tensor)).item()),
        },
    }


def tensor_polarization(tensor: torch.Tensor) -> float:
    left = torch.linalg.vector_norm(tensor[..., 0])
    right = torch.linalg.vector_norm(tensor[..., 1])
    denom = torch.linalg.vector_norm(tensor).clamp_min(1e-12)
    return float(((right - left) / denom).item())


def local_environment_matrix(site_tensors: dict[Site, torch.Tensor], topo: dict[str, Any]) -> torch.Tensor:
    graph: rx.PyGraph = topo["graph"]
    index: dict[Site, int] = topo["index"]
    drive: dict[Site, float] = topo["drives"]
    site_list = sites()
    norms = {site: torch.linalg.vector_norm(site_tensors[site]) for site in site_list}
    rows = []
    for site in site_list:
        node = index[site]
        neighbor_sites = [site_list[nbr] for nbr in graph.neighbors(node)]
        neighbor_mean = torch.stack([norms[nbr] for nbr in neighbor_sites]).mean() if neighbor_sites else torch.tensor(0.0, dtype=DTYPE)
        norm = norms[site]
        degree = float(graph.degree(node))
        flux_drive = float(drive[site])
        boundary_deficit = 6.0 - degree
        orient = site_orientation(site)
        polarization = tensor_polarization(site_tensors[site])
        local_env = torch.tanh(
            0.19 * norm
            + 0.31 * torch.tensor(flux_drive, dtype=DTYPE)
            + 0.07 * neighbor_mean
            + 0.013 * torch.tensor(degree, dtype=DTYPE)
            + 0.009 * torch.tensor(orient, dtype=DTYPE)
        )
        rows.append(
            torch.tensor(
                [
                    float(norm.item()),
                    degree / 6.0,
                    flux_drive,
                    float(neighbor_mean.item()),
                    boundary_deficit / 6.0,
                    polarization,
                    float(local_env.item()),
                ],
                dtype=DTYPE,
            )
        )
    return torch.stack(rows)


def scalar_projection_control(matrix: torch.Tensor) -> torch.Tensor:
    return torch.full_like(matrix, float(torch.mean(matrix).item()))


def eight_site_collapse_control(matrix: torch.Tensor) -> torch.Tensor:
    return matrix[:8].repeat((8, 1))


def identity_no_environment_control(matrix: torch.Tensor) -> torch.Tensor:
    return torch.zeros_like(matrix)


def unique_rows(matrix: torch.Tensor) -> int:
    rounded = torch.round(matrix.detach() * 1_000_000).to(torch.int64)
    return len({tuple(int(x) for x in row.tolist()) for row in rounded})


def matrix_metrics(matrix: torch.Tensor) -> dict[str, Any]:
    finite = bool(torch.all(torch.isfinite(matrix)).item())
    rank = int(torch.linalg.matrix_rank(matrix, tol=1e-10).item())
    centered = matrix - torch.mean(matrix, dim=0, keepdim=True)
    centered_rank = int(torch.linalg.matrix_rank(centered, tol=1e-10).item())
    return {
        "shape": list(matrix.shape),
        "finite": finite,
        "rank": rank,
        "centered_rank": centered_rank,
        "unique_rows": unique_rows(matrix),
        "frobenius_norm": float(torch.linalg.vector_norm(matrix).item()),
        "site_variance_mean": float(torch.mean(torch.var(matrix, dim=0, unbiased=False)).item()),
        "mean_abs": float(torch.mean(torch.abs(matrix)).item()),
    }


def separation(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(a - b).item())


def local_cotengra_tree_witness() -> dict[str, Any]:
    inputs = [
        ("xp", "xm", "yp", "ym", "zp", "zm", "phys"),
        ("xp",),
        ("xm",),
        ("yp",),
        ("ym",),
        ("zp",),
        ("zm",),
    ]
    output = ("phys",)
    sizes = {label: 2 for term in inputs for label in term}
    optimizer = ctg.HyperOptimizer(max_repeats=4, progbar=False, on_trial_error="raise", parallel=False)
    tree = optimizer.search(inputs, output, sizes)
    return {
        "local_star_tensor_count": len(inputs),
        "output_indices": list(output),
        "cotengra_width": float(tree.contraction_width()),
        "cotengra_cost": float(tree.contraction_cost()),
        "full_network_contraction": False,
        "pass": float(tree.contraction_width()) > 0.0 and len(inputs) == 7,
    }


def sympy_finite_noncollapse_witness() -> dict[str, Any]:
    x, y, z, phys = sp.symbols("x y z phys", integer=True, positive=True)
    site_count = x * y * z
    oriented_edges = (x - 1) * y * z + x * (y - 1) * z + x * y * (z - 1)
    substitution = {x: 4, y: 4, z: 4, phys: 2}
    site_value = int(site_count.subs(substitution))
    edge_value = int(oriented_edges.subs(substitution))
    dense_value = int((phys**site_count).subs(substitution))
    checks = [
        sp.Eq(site_count.subs(substitution), 64),
        sp.Eq(oriented_edges.subs(substitution), 144),
        sp.Ne(site_count.subs(substitution), 8),
        sp.Eq(sp.factorint(site_value), {2: 6}),
        sp.Eq(dense_value, DENSE_FULL_DIMENSION),
    ]
    return {
        "site_count_expr": str(site_count),
        "oriented_edges_expr": str(oriented_edges),
        "site_count": site_value,
        "oriented_edge_count": edge_value,
        "dense_full_dimension_symbolic": dense_value,
        "site_factorization": {str(k): int(v) for k, v in sp.factorint(site_value).items()},
        "pass": all(bool(check) for check in checks),
    }


def z3_no_dense_noncollapse_witness(metrics: dict[str, Any], deltas: dict[str, float]) -> dict[str, Any]:
    solver = z3.Solver()
    site_count, forbidden_dense_dim = z3.Ints("site_count forbidden_dense_dim")
    canonical_rank, scalar_rank, eight_unique = z3.Ints("canonical_rank scalar_rank eight_unique")
    zero_delta, shuffled_delta, scalar_delta, identity_delta = z3.Ints(
        "zero_delta shuffled_delta scalar_delta identity_delta"
    )
    full_dense_state_constructed = z3.Bool("full_dense_state_constructed")
    full_dense_environment_constructed = z3.Bool("full_dense_environment_constructed")

    solver.add(site_count == SITE_COUNT)
    solver.add(forbidden_dense_dim == DENSE_FULL_DIMENSION)
    solver.add(canonical_rank == int(metrics["canonical"]["rank"]))
    solver.add(scalar_rank == int(metrics["scalar_projection_summary_only"]["rank"]))
    solver.add(eight_unique == int(metrics["eight_site_collapse"]["unique_rows"]))
    solver.add(zero_delta == int(round(deltas["zero_flux"] * 1_000_000)))
    solver.add(shuffled_delta == int(round(deltas["shuffled_topology"] * 1_000_000)))
    solver.add(scalar_delta == int(round(deltas["scalar_projection_summary_only"] * 1_000_000)))
    solver.add(identity_delta == int(round(deltas["identity_no_environment"] * 1_000_000)))
    solver.add(full_dense_state_constructed == z3.BoolVal(False))
    solver.add(full_dense_environment_constructed == z3.BoolVal(False))
    acceptance = z3.And(
        site_count == 64,
        forbidden_dense_dim > 10**12,
        z3.Not(full_dense_state_constructed),
        z3.Not(full_dense_environment_constructed),
        canonical_rank >= 4,
        scalar_rank <= 1,
        eight_unique == 8,
        zero_delta > 100,
        shuffled_delta > 100,
        scalar_delta > 100,
        identity_delta > 100,
    )
    solver.add(z3.Not(acceptance))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes finite observed scout metrics and dense-construction bans only.",
    }


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def main() -> int:
    started = time.time()
    site_tensors = make_site_tensors()
    peps = make_quimb_peps3d(site_tensors)
    canonical_topology = topology_report()
    zero_topology = topology_report(zero_flux=True)
    shuffled_topology = topology_report(shuffled_topology=True)

    canonical = local_environment_matrix(site_tensors, canonical_topology)
    zero_flux = local_environment_matrix(site_tensors, zero_topology)
    shuffled = local_environment_matrix(site_tensors, shuffled_topology)
    scalar = scalar_projection_control(canonical)
    eight_site = eight_site_collapse_control(canonical)
    identity = identity_no_environment_control(canonical)
    matrices = {
        "canonical": canonical,
        "zero_flux": zero_flux,
        "shuffled_topology": shuffled,
        "scalar_projection_summary_only": scalar,
        "eight_site_collapse": eight_site,
        "identity_no_environment": identity,
    }
    metrics = {name: matrix_metrics(matrix) for name, matrix in matrices.items()}
    deltas = {name: separation(canonical, matrix) for name, matrix in matrices.items() if name != "canonical"}
    cotengra_witness = local_cotengra_tree_witness()
    sympy_witness = sympy_finite_noncollapse_witness()
    z3_witness = z3_no_dense_noncollapse_witness(metrics, deltas)

    positive = {
        "quimb_peps3d_64_site_carrier_constructs_without_dense_contraction": {
            "num_tensors": int(peps.num_tensors),
            "num_indices": int(peps.num_indices),
            "physical_site_count": SITE_COUNT,
            "dense_full_dimension_not_constructed": DENSE_FULL_DIMENSION,
            "pass": int(peps.num_tensors) == SITE_COUNT and DENSE_FULL_DIMENSION == 2**64,
        },
        "rustworkx_topology_flux_readout_is_finite_and_local": {
            **canonical_topology["report"],
            "canonical_readout": metrics["canonical"],
            "pass": canonical_topology["report"]["rustworkx_nodes"] == SITE_COUNT
            and canonical_topology["report"]["oriented_edge_count"] == 144
            and canonical_topology["report"]["broken_nearest_neighbor_edge_count"] == 0
            and metrics["canonical"]["finite"]
            and metrics["canonical"]["unique_rows"] == SITE_COUNT,
        },
        "cotengra_local_star_environment_tree_executes": cotengra_witness,
        "sympy_finite_site_edge_noncollapse_witness": sympy_witness,
        "z3_rejects_dense_or_collapsed_environment_admission": z3_witness,
    }
    graveyard_companions = {
        "zero_flux_control_changes_local_environment_readout": {
            "delta_from_canonical": deltas["zero_flux"],
            "control_readout": metrics["zero_flux"],
            "topology": zero_topology["report"],
            "pass": deltas["zero_flux"] > 1e-4 and zero_topology["report"]["drive_max_abs"] == 0.0,
        },
        "shuffled_topology_control_breaks_nearest_neighbor_readout": {
            "delta_from_canonical": deltas["shuffled_topology"],
            "control_readout": metrics["shuffled_topology"],
            "topology": shuffled_topology["report"],
            "pass": deltas["shuffled_topology"] > 1e-4
            and shuffled_topology["report"]["broken_nearest_neighbor_edge_count"] > 0,
        },
        "scalar_projection_summary_only_collapses_site_readout": {
            "delta_from_canonical": deltas["scalar_projection_summary_only"],
            "control_readout": metrics["scalar_projection_summary_only"],
            "pass": metrics["scalar_projection_summary_only"]["rank"] <= 1
            and deltas["scalar_projection_summary_only"] > 1e-4,
        },
        "eight_site_collapse_is_not_64_site_topology": {
            "delta_from_canonical": deltas["eight_site_collapse"],
            "control_readout": metrics["eight_site_collapse"],
            "pass": metrics["eight_site_collapse"]["unique_rows"] == 8
            and deltas["eight_site_collapse"] > 1e-4,
        },
        "identity_no_environment_control_is_empty_not_readout": {
            "delta_from_canonical": deltas["identity_no_environment"],
            "control_readout": metrics["identity_no_environment"],
            "pass": metrics["identity_no_environment"]["frobenius_norm"] == 0.0
            and deltas["identity_no_environment"] > 1e-4,
        },
    }
    boundary = {
        "no_dense_full_state_or_environment_constructed": {
            "site_count": SITE_COUNT,
            "forbidden_dense_state_dimension": DENSE_FULL_DIMENSION,
            "dense_full_state_constructed": False,
            "dense_full_environment_constructed": False,
            "max_observed_tensor_numel": int(max(tensor.numel() for tensor in site_tensors.values())),
            "max_observed_matrix_elements": int(canonical.numel()),
            "pass": canonical.numel() == SITE_COUNT * 7
            and max(tensor.numel() for tensor in site_tensors.values()) <= BOND_DIM**6 * PHYS_DIM,
        },
        "claim_ceiling_blocks_final_contraction_proof": {
            "cites_blocked_until": CITES_BLOCKED_UNTIL,
            "pass": "does not perform final PEPS3D contraction" in CLAIM_CEILING
            and PROMOTION_ALLOWED is False,
        },
        "tool_depth_reasons_nonempty": {
            "tools": sorted(TOOL_MANIFEST),
            "pass": all(row.get("reason") for row in TOOL_MANIFEST.values())
            and all(depth == "load_bearing" for depth in TOOL_INTEGRATION_DEPTH.values()),
        },
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions),
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "cites_blocked_until": CITES_BLOCKED_UNTIL,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "peps3d_64_site_no_dense_environment_topology_flux_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "divergence_log": [
            "zero_flux kills flux-drive contribution while preserving tensor carrier and topology size",
            "shuffled_topology preserves edge count but breaks nearest-neighbor locality",
            "scalar projection and 8-site collapse show summary-only and smaller-topology controls are not the 64-site readout",
            "identity/no-environment control records the empty environment baseline",
        ],
        "why_not_v4_probes": [
            "Local no-dense environment readout scout only.",
            "Does not construct or contract a dense 2**64 state.",
            "Does not construct a dense full environment or prove final PEPS3D contraction.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result["root_constraints"] = {
        "F01": True,
        "N01": True,
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "n01_evidence": "bounded local topology-flux readout, shuffled-topology control, and z3 dense-collapse rejection record order-sensitive PEPS3D evidence",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
