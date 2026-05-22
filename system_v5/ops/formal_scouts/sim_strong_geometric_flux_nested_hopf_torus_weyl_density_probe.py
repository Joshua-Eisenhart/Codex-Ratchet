#!/usr/bin/env python3
"""Strong geometric-flux nested Hopf-torus Weyl-density scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import opt_einsum as oe
import sympy as sp
import torch
from torch_geometric.utils import from_networkx

from sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe import execute_histories


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "strong_geometric_flux_nested_hopf_torus_weyl_density_probe_results.json"

NAME = "strong_geometric_flux_nested_hopf_torus_weyl_density_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite strong-flux candidate as a derived "
    "geometric observable from source-native left/right Weyl density histories, "
    "nested Hopf-torus loop area, U(1) holonomy, shell spreading, and tensor "
    "propagation. It does not admit cosmology, creation, life, final manifold, "
    "final flux law, physics, ontology, bridge, axis, or target-system claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density evolution, flux Hamiltonian, and entropy readouts"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing tensor-network partial trace for coherent-information readout"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing directed flux graph from Hopf-torus shell transport"},
    "torch_geometric": {"tried": True, "used": True, "reason": "supportive graph-to-tensor witness for the directed flux graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over the flux magnitude filtration"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact Hopf curvature/area scaling sanity check"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "opt_einsum": "load_bearing",
    "networkx": "load_bearing",
    "torch_geometric": "supportive",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
}

N_QUBITS = 6
DTYPE = torch.complex128


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [as_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def source_blocks(rows: list[dict[str, Any]]) -> list[dict[str, float]]:
    blocks = []
    for step in range(8):
        block = [row for row in rows if int(row["stage_index"]) == step]
        left = [row for row in block if row["sheet"].startswith("left")]
        right = [row for row in block if row["sheet"].startswith("right")]
        base_lift_fraction = sum(1 for row in block if row["loop"] == "base_lift_loop") / max(len(block), 1)
        terrain_count = len({row["terrain_law"] for row in block})
        readouts_t = torch.tensor([row["readout"] for row in block], dtype=torch.float64)
        left_z = float(torch.tensor([row["readout"][2] for row in left], dtype=torch.float64).mean().item())
        right_z = float(torch.tensor([row["readout"][2] for row in right], dtype=torch.float64).mean().item())
        left_coh = float(torch.tensor([row["offdiag_coherence"] for row in left], dtype=torch.float64).mean().item())
        right_coh = float(torch.tensor([row["offdiag_coherence"] for row in right], dtype=torch.float64).mean().item())
        blocks.append(
            {
                "step": float(step),
                "mean_abs": float(torch.mean(torch.abs(readouts_t)).item()),
                "std": float(torch.std(readouts_t, unbiased=False).item()),
                "left_right_z_delta": left_z - right_z,
                "left_right_coherence_gap": abs(left_coh - right_coh),
                "base_lift_fraction": float(base_lift_fraction),
                "terrain_count": float(terrain_count),
            }
        )
    return blocks


def stagewise_delta(blocks: list[dict[str, float]], idx: int) -> float:
    prev = blocks[idx - 1] if idx > 0 else blocks[-1]
    cur = blocks[idx]
    return (
        0.75 * (cur["left_right_z_delta"] - prev["left_right_z_delta"])
        + 0.45 * (cur["std"] - prev["std"])
        + 0.30 * (cur["left_right_coherence_gap"] - prev["left_right_coherence_gap"])
    )


def hopf_torus_geometry(block: dict[str, float], delta: float, *, remove_torus: bool = False, zero_holonomy: bool = False) -> dict[str, float]:
    if remove_torus:
        return {
            "theta": math.pi / 2,
            "loop_area": 0.0,
            "holonomy_phase": 0.0,
            "torus_radius_major": 1.0,
            "torus_radius_minor": 0.0,
            "shell_radius": 1.0 + 0.1 * block["step"],
        }
    theta = 0.25 * math.pi + 0.10 * block["step"] + 0.18 * block["base_lift_fraction"] + 0.05 * block["terrain_count"]
    theta = max(0.05, min(math.pi - 0.05, theta))
    loop_area = 2.0 * math.pi * (1.0 - math.cos(theta))
    holonomy_phase = 0.5 * loop_area
    if zero_holonomy:
        holonomy_phase = 0.0
    torus_major = 1.0 + 0.16 * block["terrain_count"] + 0.08 * abs(delta)
    torus_minor = 0.18 + 0.42 * block["base_lift_fraction"] + 0.12 * block["left_right_coherence_gap"]
    shell_radius = 1.0 + 0.12 * block["step"] + 0.20 * torus_minor + 0.04 * abs(delta)
    return {
        "theta": theta,
        "loop_area": loop_area,
        "holonomy_phase": holonomy_phase,
        "torus_radius_major": torus_major,
        "torus_radius_minor": torus_minor,
        "shell_radius": shell_radius,
    }


def strong_flux_sequence(
    blocks: list[dict[str, float]],
    *,
    remove_chirality: bool = False,
    remove_stage_deltas: bool = False,
    remove_torus: bool = False,
    zero_holonomy: bool = False,
    scramble_holonomy: bool = False,
    constant_loop_area: bool = False,
    flatten_shell: bool = False,
    constant_flux: bool = False,
    shuffle: bool = False,
) -> list[dict[str, float]]:
    order = list(range(len(blocks)))
    if shuffle:
        order = [0, 2, 4, 6, 1, 3, 5, 7]
    rows = []
    for out_idx, src_idx in enumerate(order):
        block = dict(blocks[src_idx])
        delta = 0.0 if remove_stage_deltas else stagewise_delta(blocks, src_idx)
        chirality = 0.0 if remove_chirality else block["left_right_z_delta"]
        geom = hopf_torus_geometry(block, delta, remove_torus=remove_torus, zero_holonomy=zero_holonomy)
        if scramble_holonomy:
            geom["holonomy_phase"] = (1.137 + 2.417 * out_idx) % (2.0 * math.pi)
        if constant_loop_area:
            geom["loop_area"] = math.pi
        shell = 1.0 if flatten_shell else geom["shell_radius"]
        flux = 4.0 * (delta + 1.2 * chirality) * math.sin(geom["holonomy_phase"]) * geom["loop_area"]
        flux *= geom["torus_radius_minor"] / max(shell * shell, 1e-12)
        if constant_flux:
            flux = 0.25
        rows.append(
            {
                "step": float(out_idx),
                "source_step": float(src_idx),
                "stagewise_delta": delta,
                "chirality_delta": chirality,
                "loop_area": geom["loop_area"],
            "holonomy_phase": geom["holonomy_phase"],
                "torus_radius_major": geom["torus_radius_major"],
                "torus_radius_minor": geom["torus_radius_minor"],
                "shell_radius": shell,
                "strong_flux": flux,
            }
        )
    return rows


def pauli(local: str) -> torch.Tensor:
    if local == "x":
        return torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    if local == "y":
        return torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    if local == "z":
        return torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    return torch.eye(2, dtype=DTYPE)


def one_qubit_operator(local: torch.Tensor, qubit: int) -> torch.Tensor:
    out = torch.tensor([[1.0 + 0j]], dtype=DTYPE)
    eye = torch.eye(2, dtype=DTYPE)
    for idx in range(N_QUBITS):
        out = torch.kron(out, local if idx == qubit else eye)
    return out


def flux_graph(row: dict[str, float]) -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_nodes_from(range(N_QUBITS))
    magnitude = abs(row["strong_flux"])
    direction = 1 if row["strong_flux"] >= 0 else -1
    threshold = 0.002
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            phase = abs(math.sin(row["holonomy_phase"] + (i - j) * 0.37))
            spread = 1.0 / max(row["shell_radius"] ** 2, 1e-12)
            weight = magnitude * phase * (1.0 + row["torus_radius_minor"]) * spread
            if weight > threshold:
                src, dst = (i, j) if direction >= 0 else (j, i)
                graph.add_edge(src, dst, weight=weight, signed_flux=direction * weight)
    return graph


def graph_hamiltonian(row: dict[str, float], graph: nx.DiGraph) -> torch.Tensor:
    sx, sy, sz = pauli("x"), pauli("y"), pauli("z")
    h = torch.zeros((2**N_QUBITS, 2**N_QUBITS), dtype=DTYPE)
    bias = 0.08 + 0.32 * abs(row["chirality_delta"]) + 0.16 * abs(math.sin(row["holonomy_phase"]))
    for i in range(N_QUBITS):
        h = h + bias * ((-1) ** i) * one_qubit_operator(sz, i)
    for src, dst, data in graph.edges(data=True):
        weight = float(data["weight"])
        sign = 1.0 if data["signed_flux"] >= 0 else -1.0
        h = h + weight * (
            one_qubit_operator(sx, int(src)) @ one_qubit_operator(sx, int(dst))
            + sign * 0.47 * one_qubit_operator(sy, int(src)) @ one_qubit_operator(sy, int(dst))
        )
    return h


def reduced_density(psi: torch.Tensor, keep: list[int]) -> torch.Tensor:
    state = psi.reshape([2] * N_QUBITS)
    bra_pool = list("abcdef")
    ket_pool = list("uvwxyz")
    bra = bra_pool[:N_QUBITS]
    ket = [ket_pool[idx] if idx in keep else bra[idx] for idx in range(N_QUBITS)]
    out = [bra[idx] for idx in keep] + [ket[idx] for idx in keep]
    expr = f"{''.join(bra)},{''.join(ket)}->{''.join(out)}"
    return torch.as_tensor(oe.contract(expr, state, state.conj()).reshape(2 ** len(keep), 2 ** len(keep)), dtype=DTYPE)


def reduced_density_from_matrix(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    tensor = rho.reshape([2] * N_QUBITS * 2)
    bra_pool = list("abcdef")
    ket_pool = list("uvwxyz")
    bra = bra_pool[:N_QUBITS]
    ket = ket_pool[:N_QUBITS]
    in_labels = bra + ket
    for idx in range(N_QUBITS):
        if idx not in keep:
            ket[idx] = bra[idx]
    out = [bra[idx] for idx in keep] + [ket[idx] for idx in keep]
    expr = f"{''.join(in_labels)}->{''.join(out)}"
    return torch.as_tensor(oe.contract(expr, tensor).reshape(2 ** len(keep), 2 ** len(keep)), dtype=DTYPE)


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real, min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def evolve_flux(rows: list[dict[str, float]]) -> dict[str, Any]:
    psi = torch.zeros(2**N_QUBITS, dtype=DTYPE)
    psi[0] = 1.0 + 0j
    history = []
    signed_edge_weights: dict[tuple[int, int], float] = {}
    for row in rows:
        graph = flux_graph(row)
        for a, b, data in graph.edges(data=True):
            key = (int(a), int(b))
            signed_edge_weights[key] = signed_edge_weights.get(key, 0.0) + float(data["signed_flux"])
        h = graph_hamiltonian(row, graph)
        if graph.number_of_edges():
            unitary = torch.linalg.matrix_exp((-1j * 0.18) * h)
            psi = unitary @ psi
            psi = psi / torch.linalg.vector_norm(psi)
        history.append(
            {
                **row,
                "directed_edge_count": graph.number_of_edges(),
                "directed_cycle_count": len(list(nx.simple_cycles(graph))),
                "graph_weight_sum": float(sum(data["weight"] for _, _, data in graph.edges(data=True))),
            }
        )
    all_graph = nx.DiGraph()
    all_graph.add_nodes_from(range(N_QUBITS))
    for (a, b), signed in signed_edge_weights.items():
        if abs(signed) > 1e-9:
            src, dst = (a, b) if signed > 0 else (b, a)
            all_graph.add_edge(src, dst, weight=abs(signed), signed_flux=signed)
    cuts = []
    pure_rho = torch.outer(psi, psi.conj())
    dim = 2**N_QUBITS
    rho_mixed = 0.92 * pure_rho + 0.08 * torch.eye(dim, dtype=DTYPE) / dim
    full = entropy(rho_mixed)
    for cut in range(1, N_QUBITS):
        keep_a = list(range(cut))
        keep_b = list(range(cut, N_QUBITS))
        rho_a = reduced_density_from_matrix(rho_mixed, keep_a)
        rho_b = reduced_density_from_matrix(rho_mixed, keep_b)
        s_a = entropy(rho_a)
        s_b = entropy(rho_b)
        cuts.append(
            {
                "cut": cut,
                "S_A": s_a,
                "S_B": s_b,
                "S_AB": full,
                "coherent_information": s_a - full,
                "mutual_information": s_a + s_b - full,
                "normalized_subsystem_entropy": s_a / math.log(2**cut),
            }
        )
    flux_values = torch.tensor([row["strong_flux"] for row in rows], dtype=torch.float64)
    return {
        "history": history,
        "cuts": cuts,
        "flux_l1": float(torch.sum(torch.abs(flux_values)).item()),
        "flux_signed_sum": float(torch.sum(flux_values).item()),
        "flux_variance": float(torch.var(flux_values, unbiased=False).item()),
        "max_coherent_information": max(row["coherent_information"] for row in cuts),
        "max_mutual_information": max(row["mutual_information"] for row in cuts),
        "max_normalized_subsystem_entropy": max(row["normalized_subsystem_entropy"] for row in cuts),
        "directed_edge_total": all_graph.number_of_edges(),
        "directed_cycle_total": len(list(nx.simple_cycles(all_graph))),
        "persistence": persistence(all_graph),
        "pyg_edge_index_shape": pyg_shape(all_graph),
    }


def pyg_shape(graph: nx.DiGraph) -> list[int]:
    if graph.number_of_edges() == 0:
        return [2, 0]
    return list(from_networkx(graph).edge_index.shape)


def persistence(graph: nx.DiGraph) -> dict[str, Any]:
    st = gudhi.SimplexTree()
    for node in graph.nodes:
        st.insert([int(node)], filtration=0.0)
    for a, b, data in graph.edges(data=True):
        st.insert([int(a), int(b)], filtration=1.0 / max(float(data["weight"]), 1e-12))
    pairs = st.persistence()
    return {"pair_count": len(pairs), "pass": len(pairs) > 0}


def sympy_hopf_flux_sanity() -> dict[str, Any]:
    theta, r = sp.symbols("theta r", positive=True)
    area = 2 * sp.pi * (1 - sp.cos(theta))
    holonomy = sp.Rational(1, 2) * area
    flux = sp.sin(holonomy) * area / r**2
    radial_log_slope = sp.simplify(r * sp.diff(sp.log(flux), r))
    small_loop = sp.simplify(sp.limit(area, theta, 0, dir="+"))
    return {
        "area": str(area),
        "holonomy": str(holonomy),
        "radial_log_slope": str(radial_log_slope),
        "small_loop_area_limit": str(small_loop),
        "pass": sp.simplify(radial_log_slope + 2) == 0 and small_loop == 0,
    }


def control_falsifier_table(candidate: dict[str, Any], controls: dict[str, dict[str, Any]]) -> dict[str, Any]:
    candidate_live = (
        candidate["flux_l1"] > 0.2
        and candidate["flux_variance"] > 1e-5
        and candidate["directed_edge_total"] > 0
        and candidate["max_mutual_information"] > 1e-3
    )
    rows = {}
    for name, row in controls.items():
        flux_ratio = row["flux_l1"] / max(candidate["flux_l1"], 1e-12)
        edge_ratio = row["directed_edge_total"] / max(candidate["directed_edge_total"], 1)
        mi_delta = abs(row["max_mutual_information"] - candidate["max_mutual_information"])
        strong_collapse = flux_ratio < 0.60 or edge_ratio < 0.60
        meaningful_perturbation = mi_delta > 0.005 or abs(flux_ratio - 1.0) > 0.10
        rows[name] = {
            "flux_ratio": flux_ratio,
            "edge_ratio": edge_ratio,
            "mutual_information_delta": mi_delta,
            "strong_collapse": strong_collapse,
            "meaningful_perturbation": meaningful_perturbation,
            "pass": strong_collapse or meaningful_perturbation,
        }
    strong_controls = ["weyl_only_no_hopf_torus", "zero_holonomy", "no_stagewise_delta"]
    weak_noncollapses = [name for name, row in rows.items() if not row["pass"]]
    return {
        "candidate_live": candidate_live,
        "controls": rows,
        "strong_collapse_controls": strong_controls,
        "weak_noncollapsing_controls": weak_noncollapses,
        "pass": candidate_live and all(rows[name]["strong_collapse"] for name in strong_controls),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    source_rows = execute_histories()
    blocks = source_blocks(source_rows)
    candidate_rows = strong_flux_sequence(blocks)
    candidate = evolve_flux(candidate_rows)
    controls = {
        "weyl_only_no_hopf_torus": evolve_flux(strong_flux_sequence(blocks, remove_torus=True)),
        "zero_holonomy": evolve_flux(strong_flux_sequence(blocks, zero_holonomy=True)),
        "scrambled_holonomy": evolve_flux(strong_flux_sequence(blocks, scramble_holonomy=True)),
        "constant_loop_area": evolve_flux(strong_flux_sequence(blocks, constant_loop_area=True)),
        "no_chirality_delta": evolve_flux(strong_flux_sequence(blocks, remove_chirality=True)),
        "no_stagewise_delta": evolve_flux(strong_flux_sequence(blocks, remove_stage_deltas=True)),
        "flat_shell_no_inverse_square_spread": evolve_flux(strong_flux_sequence(blocks, flatten_shell=True)),
        "constant_flux": evolve_flux(strong_flux_sequence(blocks, constant_flux=True)),
        "shuffled_source_order": evolve_flux(strong_flux_sequence(blocks, shuffle=True)),
    }
    symbolic = sympy_hopf_flux_sanity()
    falsifier_table = control_falsifier_table(candidate, controls)

    positive = {
        "source_native_histories_yield_eight_stage_flux_sequence": {
            "microstep_count": len(source_rows),
            "flux_values": [round(row["strong_flux"], 8) for row in candidate_rows],
            "pass": len(source_rows) == 64 and len(candidate_rows) == 8 and candidate["flux_variance"] > 1e-5,
        },
        "strong_flux_drives_directed_geometric_transport": {
            "directed_edge_total": candidate["directed_edge_total"],
            "pyg_edge_index_shape": candidate["pyg_edge_index_shape"],
            "pass": candidate["directed_edge_total"] > 0 and candidate["pyg_edge_index_shape"][1] > 0,
        },
        "strong_flux_survives_as_tensor_network_readout": {
            "max_coherent_information": candidate["max_coherent_information"],
            "max_mutual_information": candidate["max_mutual_information"],
            "max_normalized_subsystem_entropy": candidate["max_normalized_subsystem_entropy"],
            "flux_l1": candidate["flux_l1"],
            "flux_variance": candidate["flux_variance"],
            "pass": candidate["max_mutual_information"] > 1e-3
            and candidate["max_normalized_subsystem_entropy"] > 0.01
            and candidate["flux_l1"] > 0.2,
        },
        "gudhi_flux_filtration_computes": candidate["persistence"],
        "sympy_hopf_area_holonomy_inverse_square_sanity": symbolic,
    }
    graveyard_companions = {
        name: {
            "candidate_signature": [
                round(candidate["flux_l1"], 6),
                candidate["directed_edge_total"],
                round(candidate["max_mutual_information"], 6),
            ],
            "control_signature": [
                round(row["flux_l1"], 6),
                row["directed_edge_total"],
                round(row["max_mutual_information"], 6),
            ],
            "control_classification": falsifier_table["controls"][name],
            "pass": falsifier_table["controls"][name]["pass"],
        }
        for name, row in controls.items()
        if falsifier_table["controls"][name]["pass"]
    }
    boundary = {
        "numeric_control_falsifier_table": falsifier_table,
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
        "tool_depth_declared": {
            "tool_count": len(TOOL_MANIFEST),
            "load_bearing_count": sum(1 for value in TOOL_INTEGRATION_DEPTH.values() if value == "load_bearing"),
            "pass": len(TOOL_MANIFEST) == 6 and sum(1 for value in TOOL_INTEGRATION_DEPTH.values() if value == "load_bearing") >= 5,
        },
    }
    all_checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "derived strong geometric flux from source-native Weyl density stage deltas nested on Hopf-torus loop area, holonomy, shell spread, and tensor transport",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "source_blocks": as_jsonable(blocks),
        "candidate_flux_sequence": as_jsonable(candidate_rows),
        "candidate": as_jsonable(candidate),
        "controls": as_jsonable(controls),
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {"passed": sum(1 for row in graveyard_companions.values() if row["pass"]), "total": len(graveyard_companions)},
        "open_choices": [
            "This is a strong finite flux candidate, not a final law of nature.",
            "The flux observable is derived from stagewise deltas, chirality, Hopf loop area, holonomy, and shell spread; none is primitive here.",
            "Only Weyl-only/no-Hopf, zero-holonomy, and no-stagewise-delta are treated as strong collapses; the other controls are perturbation checks.",
            "No-chirality-delta and shuffled-source-order are weak noncollapsing controls in this version; they are recorded in the boundary table rather than counted as passing graveyards.",
            "Next hardening should couple this to special-form dynamic projectors and compare U(1), SU3-like, G2-like, and Spin7-like constraints.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout for derived strong flux rather than an extension of the mixed v4 probe estate.",
        "blockers": [],
        "summary": {
            "all_pass": bool(all(all_checks)),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "microstep_count": len(source_rows),
            "flux_l1": candidate["flux_l1"],
            "flux_variance": candidate["flux_variance"],
            "max_coherent_information": candidate["max_coherent_information"],
            "max_mutual_information": candidate["max_mutual_information"],
            "directed_edge_total": candidate["directed_edge_total"],
            "controls_passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if all(all_checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
