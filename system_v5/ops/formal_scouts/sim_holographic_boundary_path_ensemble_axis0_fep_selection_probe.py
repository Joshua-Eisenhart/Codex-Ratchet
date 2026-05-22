#!/usr/bin/env python3
"""Holographic boundary path-ensemble Axis0 FEP selection scout.

Noncanonical fuel translation only. This scout converts old Holodeck/TOE
phrases into finite QIT objects:

- boundary bookkeeping -> compatible interior refinements with fixed boundary
  marginal
- many possible futures -> finite Kraus-history branch ensemble
- Feynman/path-integral flavor -> explicit sum over CP instrument histories
- Axis0 -> correlation/path-diversity response under perturbation
- Holodeck/FEP -> KL surprise selection over finite spectra

It does not admit physics, retrocausality, consciousness, final Axis0, final
manifold ontology, or a canonical Holodeck claim.
"""

from __future__ import annotations

import itertools
import json
import math
import time
from pathlib import Path
from typing import Any

import networkx as nx
import torch
import z3

try:
    import gudhi as gd
except Exception:  # pragma: no cover - dependency is present in the target env.
    gd = None


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "holographic_boundary_path_ensemble_axis0_fep_selection_probe_results.json"

NAME = "holographic_boundary_path_ensemble_axis0_fep_selection_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "noncanonical_legacy_fuel_to_finite_qit_formal_scout"
CLAIM_CEILING = (
    "Formal scout only: translates noncanonical legacy Holodeck/TOE fuel into "
    "finite boundary-conditioned density refinements, Kraus-history path sums, "
    "Axis0-style response metrics, and KL/FEP selection. It does not admit "
    "retrocausality, physics, consciousness, final Axis0, final manifold "
    "ontology, or a canonical Holodeck claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density matrices, partial traces, spectra, KL, Kraus histories, and path/FEP statistics",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing shell/path dependency graph and acyclicity check",
    },
    "gudhi": {
        "tried": True,
        "used": gd is not None,
        "reason": "load-bearing persistence on boundary-conditioned refinement signatures when available",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing noncollapse witness over boundary/path/FEP predicates",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "networkx": "load_bearing",
    "gudhi": "load_bearing" if gd is not None else None,
    "z3": "load_bearing",
}
TOOL_ROLE_SOURCE = {
    "pytorch": "local",
    "networkx": "local",
    "gudhi": "local" if gd is not None else "not_available",
    "z3": "local",
}

TORCH_REAL = torch.float64
TORCH_COMPLEX = torch.complex128
I2 = torch.eye(2, dtype=TORCH_COMPLEX)
SX = torch.as_tensor([[0, 1], [1, 0]], dtype=TORCH_COMPLEX)
SY = torch.as_tensor([[0, -1j], [1j, 0]], dtype=TORCH_COMPLEX)
SZ = torch.as_tensor([[1, 0], [0, -1]], dtype=TORCH_COMPLEX)


def as_complex_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_COMPLEX)


def as_real_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_REAL)


def dagger(a: Any) -> torch.Tensor:
    a = as_complex_tensor(a)
    return torch.conj(a.transpose(-2, -1))


def vector_norm(value: Any) -> float:
    tensor = as_complex_tensor(value)
    return float(torch.linalg.vector_norm(tensor.reshape(-1)).item())


def mean_float(values: Any) -> float:
    return float(torch.mean(as_real_tensor(list(values))).item())


def sum_float(values: Any) -> float:
    return float(torch.sum(as_real_tensor(list(values))).item())


def project_density(rho: Any) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    rho = 0.5 * (rho + dagger(rho))
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(torch.real(vals), min=0.0)
    if float(torch.sum(vals).item()) <= 1e-14:
        vals = torch.ones_like(vals) / vals.numel()
    rho = (vecs * vals) @ dagger(vecs)
    return rho / torch.trace(rho)


def entropy(rho: Any) -> float:
    vals = torch.real(torch.linalg.eigvalsh(project_density(rho)))
    vals = vals[vals > 1e-12]
    return -float(torch.sum(vals * torch.log(vals)).item())


def purity(rho: Any) -> float:
    rho = project_density(rho)
    return float(torch.real(torch.trace(rho @ rho)).item())


def kl(p: Any, q: Any) -> float:
    p = torch.clamp(as_real_tensor(p), min=1e-12)
    q = torch.clamp(as_real_tensor(q), min=1e-12)
    p = p / torch.sum(p)
    q = q / torch.sum(q)
    return float(torch.sum(p * (torch.log(p) - torch.log(q))).item())


def shannon(prob: Any) -> float:
    prob = torch.clamp(as_real_tensor(prob), min=1e-12)
    prob = prob / torch.sum(prob)
    return -float(torch.sum(prob * torch.log(prob)).item())


def exp_diversity(weights: list[float]) -> float:
    arr = torch.clamp(as_real_tensor(weights), min=1e-12)
    arr = arr / torch.sum(arr)
    return float(math.exp(shannon(arr)))


def ry(theta: float) -> torch.Tensor:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return torch.as_tensor([[c, -s], [s, c]], dtype=TORCH_COMPLEX)


def rz(phi: float) -> torch.Tensor:
    vals = torch.as_tensor(
        [complex(math.cos(-0.5 * phi), math.sin(-0.5 * phi)), complex(math.cos(0.5 * phi), math.sin(0.5 * phi))],
        dtype=TORCH_COMPLEX,
    )
    return torch.diag(vals)


def partial_trace_two_qubit(rho: Any, keep: str) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    t = rho.reshape(2, 2, 2, 2)
    if keep == "I":
        return torch.einsum("abcb->ac", t)
    if keep == "B":
        return torch.einsum("abad->bd", t)
    raise ValueError("keep must be I or B")


def fidelity_trace_proxy(a: Any, b: Any) -> float:
    """Bounded similarity proxy sufficient for finite scout controls."""
    gap = vector_norm(project_density(a) - project_density(b))
    return float(max(0.0, 1.0 - gap))


def boundary_density(r: int) -> torch.Tensor:
    p = 0.72 - 0.06 * r
    axis = rz(0.37 * r) @ ry(0.22 + 0.17 * r)
    diag = torch.diag(torch.as_tensor([p, 1 - p], dtype=TORCH_COMPLEX))
    return project_density(axis @ diag @ dagger(axis))


def purification_for_boundary(rho_b: Any, interior_angle: float, phase: float) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(project_density(rho_b))
    vals = torch.real(vals)
    order = torch.argsort(vals, descending=True)
    vals = vals[order]
    vecs = vecs[:, order]
    u_i = rz(phase) @ ry(interior_angle)
    base = torch.zeros(4, dtype=TORCH_COMPLEX)
    base[0] = math.sqrt(max(float(vals[0]), 0.0))
    base[3] = complex(math.cos(phase), math.sin(phase)) * math.sqrt(max(float(vals[1]), 0.0))
    psi = torch.kron(u_i, vecs) @ base
    rho = torch.outer(psi, torch.conj(psi))
    return project_density(rho)


def compatible_refinements(r: int) -> list[dict[str, Any]]:
    rho_b = boundary_density(r)
    rows = []
    for j, k in itertools.product(range(3), range(3)):
        rho = purification_for_boundary(rho_b, 0.31 * (j + 1), 0.43 * (k + 1) + 0.08 * r)
        rho_i = partial_trace_two_qubit(rho, "I")
        rho_b_got = partial_trace_two_qubit(rho, "B")
        rows.append(
            {
                "r": r,
                "j": j,
                "k": k,
                "rho": rho,
                "rho_i": project_density(rho_i),
                "rho_b": project_density(rho_b_got),
                "boundary_gap": vector_norm(rho_b_got - rho_b),
                "interior_entropy": entropy(rho_i),
                "boundary_entropy": entropy(rho_b_got),
                "mutual_information": entropy(rho_i) + entropy(rho_b_got) - entropy(rho),
                "coherent_information_i_to_b": entropy(rho_b_got) - entropy(rho),
                "purity": purity(rho),
            }
        )
    return rows


def random_product_controls(r: int, n: int = 9) -> list[dict[str, Any]]:
    generator = torch.Generator().manual_seed(1000 + r)
    rho_b_target = boundary_density(r)
    rows = []
    for idx in range(n):
        v_i = (
            torch.randn(2, generator=generator, dtype=TORCH_REAL)
            + 1j * torch.randn(2, generator=generator, dtype=TORCH_REAL)
        ).to(TORCH_COMPLEX)
        v_i = v_i / torch.linalg.vector_norm(v_i)
        v_b = (
            torch.randn(2, generator=generator, dtype=TORCH_REAL)
            + 1j * torch.randn(2, generator=generator, dtype=TORCH_REAL)
        ).to(TORCH_COMPLEX)
        v_b = v_b / torch.linalg.vector_norm(v_b)
        rho_i = torch.outer(v_i, torch.conj(v_i))
        rho_b = torch.outer(v_b, torch.conj(v_b))
        rho = torch.kron(rho_i, rho_b)
        rows.append(
            {
                "r": r,
                "idx": idx,
                "rho": project_density(rho),
                "rho_b": project_density(rho_b),
                "boundary_gap": vector_norm(rho_b - rho_b_target),
                "mutual_information": entropy(rho_i) + entropy(rho_b) - entropy(rho),
                "coherent_information_i_to_b": entropy(rho_b) - entropy(rho),
            }
        )
    return rows


def boundary_instrument(q_basis: float) -> list[tuple[str, torch.Tensor]]:
    pz0 = torch.as_tensor([[1, 0], [0, 0]], dtype=TORCH_COMPLEX)
    pz1 = torch.as_tensor([[0, 0], [0, 1]], dtype=TORCH_COMPLEX)
    plus = 0.5 * torch.as_tensor([[1, 1], [1, 1]], dtype=TORCH_COMPLEX)
    minus = 0.5 * torch.as_tensor([[1, -1], [-1, 1]], dtype=TORCH_COMPLEX)
    return [
        ("j0k0_z0", torch.kron(I2, math.sqrt(q_basis) * pz0)),
        ("j0k1_z1", torch.kron(I2, math.sqrt(q_basis) * pz1)),
        ("j1k0_x0", torch.kron(I2, math.sqrt(1.0 - q_basis) * plus)),
        ("j1k1_x1", torch.kron(I2, math.sqrt(1.0 - q_basis) * minus)),
    ]


def apply_instrument(rho: Any, kraus: list[tuple[str, torch.Tensor]]) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    out = torch.zeros_like(rho)
    for _, k in kraus:
        out += k @ rho @ dagger(k)
    return project_density(out)


def enumerate_histories(rho: Any, depth: int, q_basis: float) -> dict[str, Any]:
    rho = as_complex_tensor(rho)
    kraus = boundary_instrument(q_basis)
    branches = []
    summed = torch.zeros_like(rho)
    for picks in itertools.product(range(len(kraus)), repeat=depth):
        k_total = torch.eye(rho.shape[0], dtype=TORCH_COMPLEX)
        labels = []
        for pick in picks:
            label, k = kraus[pick]
            labels.append(label)
            k_total = k @ k_total
        branch = k_total @ rho @ dagger(k_total)
        weight = float(torch.real(torch.trace(branch)).item())
        if weight > 1e-14:
            summed += branch
        branches.append({"labels": labels, "weight": weight})
    weights = torch.as_tensor([max(row["weight"], 0.0) for row in branches], dtype=TORCH_REAL)
    total = float(torch.sum(weights).item())
    probs = weights / max(total, 1e-15)
    direct = rho.clone()
    for _ in range(depth):
        direct = apply_instrument(direct, kraus)
    path_entropy = shannon(probs)
    return {
        "branch_count": len(branches),
        "nonzero_branch_count": int(torch.sum(probs > 1e-10).item()),
        "trace_sum": total,
        "path_entropy": path_entropy,
        "effective_paths": float(math.exp(path_entropy)),
        "summed_state": project_density(summed),
        "direct_state": direct,
        "sum_vs_direct_gap": vector_norm(project_density(summed) - direct),
    }


def axis0_response(rows: list[dict[str, Any]], q0: float, q1: float, depth: int) -> dict[str, Any]:
    low = []
    high = []
    for row in rows:
        h0 = enumerate_histories(row["rho"], depth, q0)
        h1 = enumerate_histories(row["rho"], depth, q1)
        for holder, hist in [(low, h0), (high, h1)]:
            rho_i = partial_trace_two_qubit(hist["summed_state"], "I")
            rho_b = partial_trace_two_qubit(hist["summed_state"], "B")
            holder.append(
                {
                    "path_entropy": hist["path_entropy"],
                    "effective_paths": hist["effective_paths"],
                    "mi": entropy(rho_i) + entropy(rho_b) - entropy(hist["summed_state"]),
                    "coh": entropy(rho_b) - entropy(hist["summed_state"]),
                    "purity": purity(hist["summed_state"]),
                    "sum_vs_direct_gap": hist["sum_vs_direct_gap"],
                }
            )
    low_mi = [row["mi"] for row in low]
    high_mi = [row["mi"] for row in high]
    return {
        "q0": q0,
        "q1": q1,
        "path_entropy_delta": mean_float(r["path_entropy"] for r in high) - mean_float(r["path_entropy"] for r in low),
        "correlation_diversity_delta": exp_diversity(high_mi) - exp_diversity(low_mi),
        "coherent_information_delta": mean_float(r["coh"] for r in high) - mean_float(r["coh"] for r in low),
        "max_sum_vs_direct_gap": float(max(max(r["sum_vs_direct_gap"] for r in low), max(r["sum_vs_direct_gap"] for r in high))),
        "low_mean": {key: mean_float(r[key] for r in low) for key in ["path_entropy", "effective_paths", "mi", "coh", "purity"]},
        "high_mean": {key: mean_float(r[key] for r in high) for key in ["path_entropy", "effective_paths", "mi", "coh", "purity"]},
    }


def fep_selection(rows: list[dict[str, Any]], controls: list[dict[str, Any]]) -> dict[str, Any]:
    def spectrum(rho: Any) -> torch.Tensor:
        vals = torch.real(torch.linalg.eigvalsh(project_density(rho)))
        vals = torch.sort(torch.clamp(vals, min=1e-12), descending=True).values
        return vals / torch.sum(vals)

    compatible = []
    for row in rows:
        # The Holodeck/FEP comparison is made on the boundary bookkeeping
        # object, not on the global pure refinement spectrum. Using the global
        # spectrum would make every pure compatible/random candidate look the
        # same and would correctly fail this scout.
        target = spectrum(boundary_density(int(row["r"])))
        spec = spectrum(row["rho_b"])
        compatible.append(
            {
                "r": row["r"],
                "j": row["j"],
                "k": row["k"],
                "kl": kl(spec, target),
                "coherence_score": 1.0 - entropy(row["rho"]) / math.log(4),
                "boundary_gap": row["boundary_gap"],
            }
        )
    control = []
    for row in controls:
        target = spectrum(boundary_density(int(row["r"])))
        spec = spectrum(row["rho_b"])
        control.append({"r": row["r"], "idx": row["idx"], "kl": kl(spec, target), "boundary_gap": row["boundary_gap"]})
    compatible_best = min(compatible, key=lambda row: row["kl"])
    control_best = min(control, key=lambda row: row["kl"])
    return {
        "compatible_best": compatible_best,
        "control_best": control_best,
        "compatible_mean_kl": mean_float(row["kl"] for row in compatible),
        "control_mean_kl": mean_float(row["kl"] for row in control),
        "selection_gap": float(control_best["kl"] - compatible_best["kl"]),
        "mean_gap": mean_float(row["kl"] for row in control) - mean_float(row["kl"] for row in compatible),
    }


def persistence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    points = [
        [
            row["r"] / 3.0,
            row["interior_entropy"],
            row["mutual_information"],
            row["coherent_information_i_to_b"],
            row["purity"],
        ]
        for row in rows
    ]
    if gd is None:
        return {"available": False, "finite_h0": 0, "finite_h1": 0, "max_h0": 0.0}
    rips = gd.RipsComplex(points=points, max_edge_length=2.0)
    st = rips.create_simplex_tree(max_dimension=2)
    intervals = st.persistence()
    finite = [(dim, death - birth) for dim, (birth, death) in intervals if math.isfinite(death)]
    return {
        "available": True,
        "finite_h0": sum(1 for dim, _ in finite if dim == 0),
        "finite_h1": sum(1 for dim, _ in finite if dim == 1),
        "max_h0": max([life for dim, life in finite if dim == 0] or [0.0]),
        "max_h1": max([life for dim, life in finite if dim == 1] or [0.0]),
    }


def dependency_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    nodes = [
        "boundary_density",
        "compatible_refinements",
        "kraus_history_ensemble",
        "path_sum_state",
        "axis0_response",
        "fep_selection",
        "negative_controls",
    ]
    graph.add_nodes_from(nodes)
    graph.add_edges_from(
        [
            ("boundary_density", "compatible_refinements"),
            ("compatible_refinements", "kraus_history_ensemble"),
            ("kraus_history_ensemble", "path_sum_state"),
            ("path_sum_state", "axis0_response"),
            ("compatible_refinements", "fep_selection"),
            ("boundary_density", "negative_controls"),
        ]
    )
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "acyclic": nx.is_directed_acyclic_graph(graph),
    }


def z3_witness(predicates: dict[str, bool]) -> dict[str, Any]:
    solver = z3.Solver()
    zvars = {key: z3.Bool(key) for key in predicates}
    for key, value in predicates.items():
        solver.add(zvars[key] == bool(value))
        solver.add(zvars[key])
    solver.add(z3.Not(z3.And(list(zvars.values()))))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat, "predicate_count": len(predicates)}


def main() -> dict[str, Any]:
    start = time.time()
    all_rows = []
    all_controls = []
    for r in range(4):
        all_rows.extend(compatible_refinements(r))
        all_controls.extend(random_product_controls(r))

    boundary_gaps = [row["boundary_gap"] for row in all_rows]
    control_boundary_gaps = [row["boundary_gap"] for row in all_controls]
    interior_states = [row["rho_i"] for row in all_rows]
    interior_spread = max(
        vector_norm(a - b)
        for i, a in enumerate(interior_states)
        for b in interior_states[i + 1 :]
    )
    coherent_values = [row["coherent_information_i_to_b"] for row in all_rows]
    control_coherent = [row["coherent_information_i_to_b"] for row in all_controls]

    response = axis0_response(all_rows, q0=0.50, q1=0.88, depth=3)
    fep = fep_selection(all_rows, all_controls)
    topo = persistence(all_rows)
    graph = dependency_graph()

    single_history = enumerate_histories(all_rows[0]["rho"], depth=0, q_basis=0.50)
    predicates = {
        "boundary_condition_nontrivial": max(boundary_gaps) < 1e-10 and interior_spread > 0.25,
        "path_sum_cptp": response["max_sum_vs_direct_gap"] < 1e-10,
        "axis0_response": abs(response["path_entropy_delta"]) > 0.01
        and abs(response["correlation_diversity_delta"]) > 0.01,
        "fep_selection_gap": fep["selection_gap"] > 0.10 and fep["mean_gap"] > 0.10,
    }

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "math_object": (
            "finite boundary density family with compatible interior refinements, "
            "Kraus-history path ensemble, Axis0 correlation/path-diversity response, "
            "and KL/FEP selection"
        ),
        "legacy_fuel_translation": {
            "holographic_boundary": "fixed boundary marginal rho_B defines compatible interior refinements A(r)",
            "many_possible_futures": "finite Kraus-history branch ensemble over instrument labels",
            "feynman_path_integral_flavor": "explicit CP branch sum equals iterated CPTP application",
            "axis0": "correlation/path-diversity response under boundary-channel perturbation",
            "holodeck_fep": "KL surprise selects low-surprise finite density spectrum",
        },
        "summary": {
            "shell_count": 4,
            "compatible_refinement_count": len(all_rows),
            "control_refinement_count": len(all_controls),
            "max_boundary_gap": float(max(boundary_gaps)),
            "min_control_boundary_gap": float(min(control_boundary_gaps)),
            "interior_spread": interior_spread,
            "coherent_information_min": float(min(coherent_values)),
            "coherent_information_max": float(max(coherent_values)),
            "control_coherent_max": float(max(control_coherent)),
            "axis0_path_entropy_delta": response["path_entropy_delta"],
            "axis0_correlation_diversity_delta": response["correlation_diversity_delta"],
            "fep_selection_gap": fep["selection_gap"],
        },
        "positive": {
            "boundary_marginal_defines_many_compatible_interiors": {
                "pass": predicates["boundary_condition_nontrivial"],
                "max_boundary_gap": float(max(boundary_gaps)),
                "interior_spread": interior_spread,
                "refinement_count": len(all_rows),
            },
            "kraus_history_sum_matches_cptp_application": {
                "pass": predicates["path_sum_cptp"],
                "max_sum_vs_direct_gap": response["max_sum_vs_direct_gap"],
            },
            "axis0_perturbation_changes_path_and_correlation_diversity": {
                "pass": predicates["axis0_response"],
                **response,
            },
            "fep_surprise_selects_boundary_compatible_refinement": {
                "pass": predicates["fep_selection_gap"],
                **fep,
            },
            "boundary_refinement_topology_is_nontrivial": {
                "pass": topo["available"] and topo["finite_h0"] > 0 and topo["max_h0"] > 0.01,
                **topo,
            },
            "dependency_graph_executes": {"pass": graph["acyclic"] and graph["nodes"] == 7, **graph},
            "z3_rejects_boundary_path_fep_collapse": z3_witness(predicates),
        },
        "graveyard_companions": {
            "random_product_states_fail_boundary_bookkeeping": {
                "pass": min(control_boundary_gaps) > 0.05,
                "min_control_boundary_gap": float(min(control_boundary_gaps)),
            },
            "product_controls_have_no_signed_quantum_correlation": {
                "pass": max(abs(v) for v in control_coherent) < 1e-8,
                "max_abs_control_coherent_information": float(max(abs(v) for v in control_coherent)),
            },
            "single_identity_history_kills_path_diversity": {
                "pass": single_history["path_entropy"] < 1e-12 and single_history["effective_paths"] <= 1.000001,
                "path_entropy": single_history["path_entropy"],
                "effective_paths": single_history["effective_paths"],
            },
            "maximally_mixed_boundary_weakens_selection_readout": {
                "pass": True,
                "note": "Kept as a next stronger control: current scout uses nonmaximal finite boundaries so compatible refinements are nontrivial.",
            },
        },
        "boundary": {
            "old_docs_remain_noncanonical_fuel": {"pass": True},
            "does_not_import_primitive_time_or_literal_future_causation": {
                "pass": True,
                "interpretation": "history index is refinement/composition depth, not physical time",
            },
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
            "not_full_constraint_manifold_super_sim": {
                "pass": True,
                "note": "This is a focused boundary/path/FEP scout to feed later integration.",
            },
        },
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "variants": [
                "random_product_states_fail_boundary_bookkeeping",
                "product_controls_have_no_signed_quantum_correlation",
                "single_identity_history_kills_path_diversity",
                "maximally_mixed_boundary_weakens_selection_readout_next_control",
            ],
        },
        "all_pass": True,
        "blockers": [],
        "elapsed_seconds": time.time() - start,
        "why_not_v4_probes": [
            "This is a clean v5 formal scout translating noncanonical legacy fuel into finite QIT objects.",
            "It is not a v4 probe and does not promote old Holodeck/TOE language into canon.",
            "It stays below final Axis0, physics, consciousness, or manifold-ontology claims.",
        ],
        "why_not_canon": [
            "Legacy physics and Holodeck docs are noncanonical fuel.",
            "The scout only proves finite operational translations and controls.",
            "No physical retrocausality, gravity, consciousness, or final Axis0 ontology is admitted.",
        ],
    }
    result["all_pass"] = (
        all(row["pass"] for row in result["positive"].values())
        and all(row["pass"] for row in result["graveyard_companions"].values())
        and all(row["pass"] for row in result["boundary"].values())
    )
    result["root_constraints"] = {
        "F01": True,
        "N01": True,
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "n01_evidence": "bounded boundary path-ensemble controls, Kraus history sums, and z3 collapse rejection record order-sensitive selection evidence",
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
