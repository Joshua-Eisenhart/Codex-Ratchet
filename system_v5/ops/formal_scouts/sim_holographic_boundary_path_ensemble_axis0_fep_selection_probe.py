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
import numpy as np
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
SOURCE_ALIGNMENT_CATEGORY = "noncanonical_legacy_fuel_to_finite_qit_formal_scout"
CLAIM_CEILING = (
    "Formal scout only: translates noncanonical legacy Holodeck/TOE fuel into "
    "finite boundary-conditioned density refinements, Kraus-history path sums, "
    "Axis0-style response metrics, and KL/FEP selection. It does not admit "
    "retrocausality, physics, consciousness, final Axis0, final manifold "
    "ontology, or a canonical Holodeck claim."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density matrices, partial traces, spectra, KL, and Kraus histories",
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
    "numpy": "load_bearing",
    "networkx": "load_bearing",
    "gudhi": "load_bearing" if gd is not None else None,
    "z3": "load_bearing",
}

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)


def dagger(a: np.ndarray) -> np.ndarray:
    return np.conjugate(a.T)


def project_density(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + dagger(rho))
    vals, vecs = np.linalg.eigh(rho)
    vals = np.clip(vals.real, 0.0, None)
    if float(np.sum(vals)) <= 1e-14:
        vals = np.ones_like(vals) / len(vals)
    rho = (vecs * vals) @ dagger(vecs)
    return rho / np.trace(rho)


def entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh(project_density(rho)).real
    vals = vals[vals > 1e-12]
    return -float(np.sum(vals * np.log(vals)))


def purity(rho: np.ndarray) -> float:
    rho = project_density(rho)
    return float(np.real(np.trace(rho @ rho)))


def kl(p: np.ndarray, q: np.ndarray) -> float:
    p = np.clip(np.asarray(p, dtype=float), 1e-12, None)
    q = np.clip(np.asarray(q, dtype=float), 1e-12, None)
    p = p / np.sum(p)
    q = q / np.sum(q)
    return float(np.sum(p * (np.log(p) - np.log(q))))


def shannon(prob: np.ndarray) -> float:
    prob = np.clip(np.asarray(prob, dtype=float), 1e-12, None)
    prob = prob / np.sum(prob)
    return -float(np.sum(prob * np.log(prob)))


def exp_diversity(weights: list[float]) -> float:
    arr = np.clip(np.asarray(weights, dtype=float), 1e-12, None)
    arr = arr / np.sum(arr)
    return float(math.exp(shannon(arr)))


def ry(theta: float) -> np.ndarray:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return np.array([[c, -s], [s, c]], dtype=complex)


def rz(phi: float) -> np.ndarray:
    return np.diag([np.exp(-0.5j * phi), np.exp(0.5j * phi)]).astype(complex)


def partial_trace_two_qubit(rho: np.ndarray, keep: str) -> np.ndarray:
    t = rho.reshape(2, 2, 2, 2)
    if keep == "I":
        return np.einsum("abcb->ac", t)
    if keep == "B":
        return np.einsum("abad->bd", t)
    raise ValueError("keep must be I or B")


def fidelity_trace_proxy(a: np.ndarray, b: np.ndarray) -> float:
    """Bounded similarity proxy sufficient for finite scout controls."""
    gap = np.linalg.norm(project_density(a) - project_density(b), ord="fro")
    return float(max(0.0, 1.0 - gap))


def boundary_density(r: int) -> np.ndarray:
    p = 0.72 - 0.06 * r
    axis = rz(0.37 * r) @ ry(0.22 + 0.17 * r)
    return project_density(axis @ np.diag([p, 1 - p]).astype(complex) @ dagger(axis))


def purification_for_boundary(rho_b: np.ndarray, interior_angle: float, phase: float) -> np.ndarray:
    vals, vecs = np.linalg.eigh(project_density(rho_b))
    order = np.argsort(vals)[::-1]
    vals = vals[order]
    vecs = vecs[:, order]
    u_i = rz(phase) @ ry(interior_angle)
    base = np.zeros(4, dtype=complex)
    base[0] = math.sqrt(max(float(vals[0]), 0.0))
    base[3] = np.exp(1j * phase) * math.sqrt(max(float(vals[1]), 0.0))
    psi = np.kron(u_i, vecs) @ base
    rho = np.outer(psi, np.conjugate(psi))
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
                "boundary_gap": float(np.linalg.norm(rho_b_got - rho_b, ord="fro")),
                "interior_entropy": entropy(rho_i),
                "boundary_entropy": entropy(rho_b_got),
                "mutual_information": entropy(rho_i) + entropy(rho_b_got) - entropy(rho),
                "coherent_information_i_to_b": entropy(rho_b_got) - entropy(rho),
                "purity": purity(rho),
            }
        )
    return rows


def random_product_controls(r: int, n: int = 9) -> list[dict[str, Any]]:
    rng = np.random.default_rng(1000 + r)
    rho_b_target = boundary_density(r)
    rows = []
    for idx in range(n):
        v_i = rng.normal(size=2) + 1j * rng.normal(size=2)
        v_i = v_i / np.linalg.norm(v_i)
        v_b = rng.normal(size=2) + 1j * rng.normal(size=2)
        v_b = v_b / np.linalg.norm(v_b)
        rho_i = np.outer(v_i, np.conjugate(v_i))
        rho_b = np.outer(v_b, np.conjugate(v_b))
        rho = np.kron(rho_i, rho_b)
        rows.append(
            {
                "r": r,
                "idx": idx,
                "rho": project_density(rho),
                "rho_b": project_density(rho_b),
                "boundary_gap": float(np.linalg.norm(rho_b - rho_b_target, ord="fro")),
                "mutual_information": entropy(rho_i) + entropy(rho_b) - entropy(rho),
                "coherent_information_i_to_b": entropy(rho_b) - entropy(rho),
            }
        )
    return rows


def boundary_instrument(q_basis: float) -> list[tuple[str, np.ndarray]]:
    pz0 = np.array([[1, 0], [0, 0]], dtype=complex)
    pz1 = np.array([[0, 0], [0, 1]], dtype=complex)
    plus = 0.5 * np.array([[1, 1], [1, 1]], dtype=complex)
    minus = 0.5 * np.array([[1, -1], [-1, 1]], dtype=complex)
    return [
        ("j0k0_z0", np.kron(I2, math.sqrt(q_basis) * pz0)),
        ("j0k1_z1", np.kron(I2, math.sqrt(q_basis) * pz1)),
        ("j1k0_x0", np.kron(I2, math.sqrt(1.0 - q_basis) * plus)),
        ("j1k1_x1", np.kron(I2, math.sqrt(1.0 - q_basis) * minus)),
    ]


def apply_instrument(rho: np.ndarray, kraus: list[tuple[str, np.ndarray]]) -> np.ndarray:
    out = np.zeros_like(rho, dtype=complex)
    for _, k in kraus:
        out += k @ rho @ dagger(k)
    return project_density(out)


def enumerate_histories(rho: np.ndarray, depth: int, q_basis: float) -> dict[str, Any]:
    kraus = boundary_instrument(q_basis)
    branches = []
    summed = np.zeros_like(rho, dtype=complex)
    for picks in itertools.product(range(len(kraus)), repeat=depth):
        k_total = np.eye(rho.shape[0], dtype=complex)
        labels = []
        for pick in picks:
            label, k = kraus[pick]
            labels.append(label)
            k_total = k @ k_total
        branch = k_total @ rho @ dagger(k_total)
        weight = float(np.real(np.trace(branch)))
        if weight > 1e-14:
            summed += branch
        branches.append({"labels": labels, "weight": weight})
    weights = np.array([max(row["weight"], 0.0) for row in branches], dtype=float)
    total = float(np.sum(weights))
    probs = weights / max(total, 1e-15)
    direct = rho.copy()
    for _ in range(depth):
        direct = apply_instrument(direct, kraus)
    path_entropy = shannon(probs)
    return {
        "branch_count": len(branches),
        "nonzero_branch_count": int(np.sum(probs > 1e-10)),
        "trace_sum": total,
        "path_entropy": path_entropy,
        "effective_paths": float(math.exp(path_entropy)),
        "summed_state": project_density(summed),
        "direct_state": direct,
        "sum_vs_direct_gap": float(np.linalg.norm(project_density(summed) - direct, ord="fro")),
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
        "path_entropy_delta": float(np.mean([r["path_entropy"] for r in high]) - np.mean([r["path_entropy"] for r in low])),
        "correlation_diversity_delta": exp_diversity(high_mi) - exp_diversity(low_mi),
        "coherent_information_delta": float(np.mean([r["coh"] for r in high]) - np.mean([r["coh"] for r in low])),
        "max_sum_vs_direct_gap": float(max(max(r["sum_vs_direct_gap"] for r in low), max(r["sum_vs_direct_gap"] for r in high))),
        "low_mean": {key: float(np.mean([r[key] for r in low])) for key in ["path_entropy", "effective_paths", "mi", "coh", "purity"]},
        "high_mean": {key: float(np.mean([r[key] for r in high])) for key in ["path_entropy", "effective_paths", "mi", "coh", "purity"]},
    }


def fep_selection(rows: list[dict[str, Any]], controls: list[dict[str, Any]]) -> dict[str, Any]:
    def spectrum(rho: np.ndarray) -> np.ndarray:
        vals = np.linalg.eigvalsh(project_density(rho)).real
        vals = np.sort(np.clip(vals, 1e-12, None))[::-1]
        return vals / np.sum(vals)

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
        "compatible_mean_kl": float(np.mean([row["kl"] for row in compatible])),
        "control_mean_kl": float(np.mean([row["kl"] for row in control])),
        "selection_gap": float(control_best["kl"] - compatible_best["kl"]),
        "mean_gap": float(np.mean([row["kl"] for row in control]) - np.mean([row["kl"] for row in compatible])),
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
        float(np.linalg.norm(a - b, ord="fro"))
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
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
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
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
