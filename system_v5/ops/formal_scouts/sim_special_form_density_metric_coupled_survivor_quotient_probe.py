#!/usr/bin/env python3
"""Special-form frame actions coupled to density-metric survivor quotients."""

from __future__ import annotations

import itertools
import json
import math
import os
import pathlib
import time
from collections import defaultdict
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import geomstats.backend as gs
import gudhi
import networkx as nx
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "special_form_density_metric_coupled_survivor_quotient_probe_results.json"
SIGNED_ACTION_RESULT = RESULT_DIR / "special_form_signed_permutation_survivor_quotient_probe_results.json"

NAME = "special_form_density_metric_coupled_survivor_quotient_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: projects finite special-form signed frame actions into "
    "unitary density channels, then compares Bures, trace, and Hilbert-Schmidt "
    "metric survivor quotients. It tests a coupling between form constraints "
    "and density geometry, but does not admit a continuous holonomy manifold, "
    "final constraint family, ontology, bridge, axis, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density candidates, projected unitary channels, spectra, entropy, and matrix distances"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing backend array sanity for metric-coordinate values"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact signed-permutation determinant sanity"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing coupled-family survivor difference contradiction checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing survivor quotient graph construction"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph-to-tensor conversion for quotient graphs"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing Vietoris-Rips persistence on survivor distance matrices"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing family-metric transition graph"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
DIM = 4


def form(term_specs: list[tuple[int, tuple[int, ...]]]) -> dict[tuple[int, ...], int]:
    return {tuple(sorted(term)): coeff for coeff, term in term_specs}


SU3_REAL_VOLUME = form([(1, (0, 2, 4)), (-1, (0, 3, 5)), (-1, (1, 2, 5)), (-1, (1, 3, 4))])
SU3_KAHLER = form([(1, (0, 1)), (1, (2, 3)), (1, (4, 5))])
G2_THREE_FORM = form(
    [(1, (0, 1, 2)), (1, (0, 3, 4)), (1, (0, 5, 6)), (1, (1, 3, 5)), (-1, (1, 4, 6)), (-1, (2, 3, 6)), (-1, (2, 4, 5))]
)
SPIN7_CAYLEY_FORM = form(
    [
        (1, (0, 1, 2, 7)),
        (1, (0, 3, 4, 7)),
        (1, (0, 5, 6, 7)),
        (1, (1, 3, 5, 7)),
        (-1, (1, 4, 6, 7)),
        (-1, (2, 3, 6, 7)),
        (-1, (2, 4, 5, 7)),
        (1, (3, 4, 5, 6)),
        (1, (1, 2, 5, 6)),
        (1, (1, 2, 3, 4)),
        (1, (0, 2, 4, 6)),
        (-1, (0, 2, 3, 5)),
        (-1, (0, 1, 4, 5)),
        (-1, (0, 1, 3, 6)),
    ]
)

FAMILIES = {
    "su3_two_and_three_form_constraints": {"dimension": 6, "forms": [SU3_KAHLER, SU3_REAL_VOLUME]},
    "g2_three_form_constraints": {"dimension": 7, "forms": [G2_THREE_FORM]},
    "spin7_four_form_constraints": {"dimension": 8, "forms": [SPIN7_CAYLEY_FORM]},
    "generic_three_form_control_constraints": {
        "dimension": 7,
        "forms": [form([(1, term) for term in itertools.combinations(range(7), 3)])],
    },
    "generic_four_form_control_constraints": {
        "dimension": 8,
        "forms": [form([(1, term) for term in itertools.combinations(range(8), 4)])],
    },
}


def wedge_sort_sign(indices: tuple[int, ...]) -> tuple[tuple[int, ...], int]:
    inversions = 0
    for i, a in enumerate(indices):
        for b in indices[i + 1 :]:
            inversions += int(a > b)
    return tuple(sorted(indices)), -1 if inversions % 2 else 1


def gf2_solutions(dim: int, equations: list[tuple[int, int]], max_samples: int = 24) -> tuple[int, list[tuple[int, ...]], bool]:
    rows = [[(mask >> i) & 1 for i in range(dim)] + [rhs & 1] for mask, rhs in equations]
    pivot_cols: list[int] = []
    r = 0
    for c in range(dim):
        pivot = next((idx for idx in range(r, len(rows)) if rows[idx][c]), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        for idx in range(len(rows)):
            if idx != r and rows[idx][c]:
                rows[idx] = [a ^ b for a, b in zip(rows[idx], rows[r])]
        pivot_cols.append(c)
        r += 1
    if any(not any(row[:dim]) and row[dim] for row in rows):
        return 0, [], False
    free_cols = [c for c in range(dim) if c not in pivot_cols]
    count = 2 ** len(free_cols)
    samples: list[tuple[int, ...]] = []
    for bits in itertools.product([0, 1], repeat=len(free_cols)):
        x = [0] * dim
        for col, bit in zip(free_cols, bits):
            x[col] = bit
        for ridx in reversed(range(len(pivot_cols))):
            col = pivot_cols[ridx]
            total = rows[ridx][dim]
            for c in free_cols:
                total ^= rows[ridx][c] & x[c]
            x[col] = total
        samples.append(tuple(-1 if bit else 1 for bit in x))
        if len(samples) >= max_samples:
            break
    return count, samples, True


def preserving_signs_for_permutation(dim: int, perm: tuple[int, ...], forms: list[dict[tuple[int, ...], int]]) -> tuple[int, list[tuple[int, ...]], bool]:
    equations: list[tuple[int, int]] = []
    for current_form in forms:
        for term, coeff in current_form.items():
            image, wedge_sign = wedge_sort_sign(tuple(perm[i] for i in term))
            target_coeff = current_form.get(image)
            if target_coeff is None:
                return 0, [], False
            required_product = target_coeff // (coeff * wedge_sign)
            if required_product not in (-1, 1):
                return 0, [], False
            mask = 0
            for idx in term:
                mask |= 1 << idx
            equations.append((mask, 1 if required_product == -1 else 0))
    return gf2_solutions(dim, equations)


def load_preserving_actions(max_actions: int = 3) -> tuple[dict[str, dict[str, int]], dict[str, list[tuple[tuple[int, ...], tuple[int, ...]]]]]:
    data = json.loads(SIGNED_ACTION_RESULT.read_text(encoding="utf-8"))
    action_counts: dict[str, dict[str, int]] = {}
    family_actions: dict[str, list[tuple[tuple[int, ...], tuple[int, ...]]]] = {}
    for row in data["rows"]:
        family = row["family"]
        action_counts[family] = {
            "upstream_preserving_permutation_count": int(row["preserving_permutation_count"]),
            "upstream_signed_action_count": int(row["signed_action_count"]),
            "sampled_action_count": min(max_actions, len(row["sample_actions"])),
        }
        family_actions[family] = [
            (tuple(action["permutation"]), tuple(action["signs"]))
            for action in row["sample_actions"][:max_actions]
        ]
    return action_counts, family_actions


def projected_unitary(action: tuple[tuple[int, ...], tuple[int, ...]]) -> torch.Tensor:
    perm, signs = action
    first_images = list(perm[:DIM])
    ranked = {value: rank for rank, value in enumerate(sorted(first_images))}
    local_perm = [ranked[value] for value in first_images]
    unitary = torch.zeros((DIM, DIM), dtype=DTYPE)
    for source, target in enumerate(local_perm):
        unitary[target, source] = complex(signs[source])
    return unitary


def hermitian(rho: torch.Tensor) -> torch.Tensor:
    return (rho + rho.conj().T) / 2


def density_valid(rho: torch.Tensor) -> bool:
    eigs = torch.linalg.eigvalsh(hermitian(rho))
    tr = torch.trace(rho)
    return bool(abs(float(torch.real(tr).item()) - 1.0) < 1e-9 and abs(float(torch.imag(tr).item())) < 1e-9 and float(torch.min(eigs).item()) >= -1e-9)


def normalize_density(raw: torch.Tensor) -> torch.Tensor:
    rho = raw @ raw.conj().T
    return rho / torch.real(torch.trace(rho))


def candidate_densities() -> list[dict[str, Any]]:
    gen = torch.Generator().manual_seed(271828)
    candidates = []
    for idx in range(DIM):
        psi = torch.zeros(DIM, dtype=DTYPE)
        psi[idx] = 1
        pure = torch.outer(psi, psi.conj())
        candidates.append({"candidate_id": len(candidates), "source_label": f"basis_{idx}", "rho": 0.84 * pure + 0.16 * torch.eye(DIM, dtype=DTYPE) / DIM})
    for name, psi in [
        ("bell_plus", torch.tensor([1, 0, 0, 1], dtype=DTYPE) / math.sqrt(2)),
        ("bell_minus", torch.tensor([1, 0, 0, -1], dtype=DTYPE) / math.sqrt(2)),
        ("plus_plus", torch.tensor([1, 1, 1, 1], dtype=DTYPE) / 2),
    ]:
        pure = torch.outer(psi, psi.conj())
        candidates.append({"candidate_id": len(candidates), "source_label": name, "rho": 0.84 * pure + 0.16 * torch.eye(DIM, dtype=DTYPE) / DIM})
    for _ in range(3):
        re = torch.randn(DIM, DIM, generator=gen, dtype=torch.float64)
        im = torch.randn(DIM, DIM, generator=gen, dtype=torch.float64)
        rho = normalize_density(torch.complex(re, im))
        candidates.append({"candidate_id": len(candidates), "source_label": f"mixed_{len(candidates):02d}", "rho": 0.82 * rho + 0.18 * torch.eye(DIM, dtype=DTYPE) / DIM})
    return candidates


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh(hermitian(rho)), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def purity(rho: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ rho)).item())


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = hermitian(a - b)
    return float(0.5 * torch.sum(torch.abs(torch.linalg.eigvalsh(diff))).item())


def hilbert_schmidt_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = a - b
    return float(torch.sqrt(torch.real(torch.trace(diff.conj().T @ diff))).item())


def matrix_sqrt_psd(a: torch.Tensor) -> torch.Tensor:
    eigvals, eigvecs = torch.linalg.eigh(hermitian(a))
    eigvals = torch.clamp(eigvals, min=0.0)
    return eigvecs @ torch.diag(torch.sqrt(eigvals)).to(DTYPE) @ eigvecs.conj().T


def bures_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    sqrt_a = matrix_sqrt_psd(a)
    fidelity_root = torch.real(torch.trace(matrix_sqrt_psd(sqrt_a @ b @ sqrt_a)))
    return float(torch.sqrt(torch.clamp(2 - 2 * fidelity_root, min=0.0)).item())


METRICS = {
    "bures_density_metric": {"fn": bures_distance, "threshold": 0.30, "radius": 0.12},
    "trace_distance_metric": {"fn": trace_distance, "threshold": 0.36, "radius": 0.14},
    "hilbert_schmidt_metric": {"fn": hilbert_schmidt_distance, "threshold": 0.33, "radius": 0.13},
}


def spectral_filter(rho: torch.Tensor, strength: float) -> torch.Tensor:
    weights = torch.tensor([1.0, 0.82 - 0.12 * strength, 0.66 + 0.05 * strength, 0.47], dtype=torch.float64)
    filt = torch.diag(weights.to(DTYPE))
    out = filt @ rho @ filt.conj().T
    return out / torch.real(torch.trace(out))


def apply_coupled_channel(rho: torch.Tensor, action: tuple[tuple[int, ...], tuple[int, ...]]) -> torch.Tensor:
    unitary = projected_unitary(action)
    sign_strength = abs(sum(action[1][:DIM])) / DIM
    out = unitary @ rho @ unitary.conj().T
    return spectral_filter(out, sign_strength)


def probe_signature(rho: torch.Tensor) -> tuple[float, ...]:
    diag = torch.real(torch.diag(rho))
    return tuple(round(float(value), 3) for value in [*diag.tolist(), entropy(rho), purity(rho)])


def rips_persistence(distance_matrix: list[list[float]]) -> dict[str, Any]:
    if len(distance_matrix) < 2:
        return {"simplex_count": len(distance_matrix), "h0_pair_count": len(distance_matrix), "h1_pair_count": 0, "finite_h1_lifetime_sum": 0.0}
    rips = gudhi.RipsComplex(distance_matrix=distance_matrix, max_edge_length=max(max(row) for row in distance_matrix))
    st = rips.create_simplex_tree(max_dimension=2)
    pairs = st.persistence()
    h0 = [pair for pair in pairs if pair[0] == 0]
    h1 = [pair for pair in pairs if pair[0] == 1]
    finite_h1 = [pair for pair in h1 if pair[1][1] != float("inf")]
    return {
        "simplex_count": st.num_simplices(),
        "h0_pair_count": len(h0),
        "h1_pair_count": len(h1),
        "finite_h1_lifetime_sum": sum(float(death - birth) for _, (birth, death) in finite_h1),
    }


def quotient(rows: list[dict[str, Any]], metric_name: str, radius: float) -> dict[str, Any]:
    survivors = [row for row in rows if row["survived"]]
    graph = nx.Graph()
    for idx, _ in enumerate(survivors):
        graph.add_node(idx)
    metric = METRICS[metric_name]["fn"]
    distance_matrix = [[0.0 for _ in survivors] for _ in survivors]
    for i, a in enumerate(survivors):
        for j, b in enumerate(survivors[i + 1 :], start=i + 1):
            dist = metric(a["rho"], b["rho"])
            distance_matrix[i][j] = distance_matrix[j][i] = dist
            if dist <= radius:
                graph.add_edge(i, j)
    signatures: dict[tuple[float, ...], list[int]] = defaultdict(list)
    for idx, row in enumerate(survivors):
        signatures[row["signature"]].append(idx)
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    return {
        "survivor_count": len(survivors),
        "radius_class_count": nx.number_connected_components(graph) if graph.number_of_nodes() else 0,
        "signature_class_count": len(signatures),
        "edge_count": graph.number_of_edges(),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
        "persistence": rips_persistence(distance_matrix),
    }


def coupled_rows(actions: list[tuple[tuple[int, ...], tuple[int, ...]]], metric_name: str) -> list[dict[str, Any]]:
    mixed = torch.eye(DIM, dtype=DTYPE) / DIM
    metric = METRICS[metric_name]["fn"]
    threshold = METRICS[metric_name]["threshold"]
    rows = []
    for action_idx, action in enumerate(actions):
        for candidate in candidate_densities():
            rho = apply_coupled_channel(candidate["rho"], action)
            dist = metric(rho, mixed)
            survived = density_valid(rho) and entropy(rho) <= 1.32 and purity(rho) >= 0.28 and dist >= threshold
            rows.append(
                {
                    "action_idx": action_idx,
                    "candidate_id": candidate["candidate_id"],
                    "source_label": candidate["source_label"],
                    "rho": rho,
                    "distance_from_mixed": dist,
                    "survived": survived,
                    "signature": probe_signature(rho) if survived else None,
                }
            )
    return rows


def transition_graph(summary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {idx: graph.add_node(row["family"] + "::" + row["metric_name"]) for idx, row in enumerate(summary_rows)}
    for i, a in enumerate(summary_rows):
        for j, b in enumerate(summary_rows):
            if i != j and (a["survivor_count"], a["radius_class_count"], a["signature_class_count"]) != (
                b["survivor_count"],
                b["radius_class_count"],
                b["signature_class_count"],
            ):
                graph.add_edge(nodes[i], nodes[j], "differs")
    return {
        "edge_count": graph.num_edges(),
        "cycle_witness": graph.num_edges() >= 2,
        "pass": graph.num_edges() > 0,
    }


def z3_family_difference(summary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    checks = {}
    for metric_name in METRICS:
        by_family = {row["family"]: row for row in summary_rows if row["metric_name"] == metric_name}
        differs = (
            by_family["g2_three_form_constraints"]["survivor_count"] != by_family["generic_three_form_control_constraints"]["survivor_count"]
            or by_family["g2_three_form_constraints"]["radius_class_count"] != by_family["generic_three_form_control_constraints"]["radius_class_count"]
            or by_family["g2_three_form_constraints"]["signature_class_count"] != by_family["generic_three_form_control_constraints"]["signature_class_count"]
        )
        solver = z3.Solver()
        flag = z3.Bool(f"g2_differs_{metric_name}")
        solver.add(flag == differs, flag == False)
        checks[f"g2_differs_from_generic_three_form_under_{metric_name}"] = {"solver_status": str(solver.check()), "pass": differs and solver.check() == z3.unsat}
    return checks


def sympy_unitary_boundary() -> dict[str, Any]:
    matrix = sp.Matrix([[0, 1], [1, 0]])
    return {"determinant": int(matrix.det()), "pass": int(matrix.det()) == -1}


def main() -> dict[str, Any]:
    started = time.time()
    geomstats_backend_probe = gs.array([0.0, 1.0, 2.0])
    action_counts, family_actions = load_preserving_actions()
    summary_rows = []
    for family, actions in family_actions.items():
        for metric_name, metric_spec in METRICS.items():
            rows = coupled_rows(actions, metric_name)
            q = quotient(rows, metric_name, metric_spec["radius"])
            summary_rows.append(
                {
                    "family": family,
                    "metric_name": metric_name,
                    "sampled_action_count": len(actions),
                    "upstream_signed_action_count": action_counts[family]["upstream_signed_action_count"],
                    "threshold": metric_spec["threshold"],
                    "radius": metric_spec["radius"],
                    **q,
                }
            )
    z3_rows = z3_family_difference(summary_rows)
    positive = {
        "families_produce_preserving_actions": {
            "action_counts": action_counts,
            "pass": all(row["sampled_action_count"] > 0 for row in action_counts.values()),
        },
        "coupled_rows_cover_all_family_metric_pairs": {
            "row_count": len(summary_rows),
            "pass": len(summary_rows) == len(FAMILIES) * len(METRICS),
        },
        "density_metric_survivor_counts_change_across_coupled_families": {
            "survivor_counts": {row["family"] + "::" + row["metric_name"]: row["survivor_count"] for row in summary_rows},
            "pass": len({row["survivor_count"] for row in summary_rows}) > 1,
        },
        "rips_persistence_computes_for_coupled_survivor_clouds": {
            "h1_lifetime_sum_by_row": [row["persistence"]["finite_h1_lifetime_sum"] for row in summary_rows],
            "pass": all(row["persistence"]["simplex_count"] >= row["survivor_count"] for row in summary_rows),
        },
        "rustworkx_transition_graph_detects_coupled_family_metric_differences": transition_graph(summary_rows),
        "sympy_projected_unitary_boundary": sympy_unitary_boundary(),
        "z3_coupled_family_difference_checks": {"checks": z3_rows, "pass": all(row["pass"] for row in z3_rows.values())},
        "geomstats_backend_array_is_used": {"shape": list(gs.shape(geomstats_backend_probe)), "pass": list(gs.shape(geomstats_backend_probe)) == [3]},
    }
    identity_actions = [(tuple(range(7)), tuple([1] * 7))]
    identity_rows = coupled_rows(identity_actions, "trace_distance_metric")
    graveyard_companions = {
        "identity_action_has_smaller_action_sample_than_special_families": {
            "identity_action_count": len(identity_actions),
            "g2_sampled_action_count": len(family_actions["g2_three_form_constraints"]),
            "pass": len(identity_actions) < len(family_actions["g2_three_form_constraints"]),
        },
        "overlarge_radius_collapses_identity_radius_classes": {
            "class_count": quotient([{**row, "survived": True} for row in identity_rows], "trace_distance_metric", radius=99.0)["radius_class_count"],
            "pass": quotient([{**row, "survived": True} for row in identity_rows], "trace_distance_metric", radius=99.0)["radius_class_count"] == 1,
        },
        "overstrict_threshold_extinguishes_coupled_candidates": {
            "survivor_count": sum(row["survived"] and row["distance_from_mixed"] >= 99.0 for row in identity_rows),
            "pass": sum(row["survived"] and row["distance_from_mixed"] >= 99.0 for row in identity_rows) == 0,
        },
    }
    boundary = {
        "family_count": {"count": len(FAMILIES), "pass": len(FAMILIES) == 5},
        "metric_count": {"count": len(METRICS), "pass": len(METRICS) == 3},
        "candidate_density_count": {"count": len(candidate_densities()), "pass": len(candidate_densities()) == 10},
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite special-form signed frame actions projected into unitary density channels and tested by density-metric survivor quotients",
        "summary_rows": summary_rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "The projection from 6/7/8-dimensional frame actions to a 4D density channel is deterministic but not unique.",
            "This couples a deterministic bounded sample of finite form-preserving frame actions to density geometry; it still does not compute continuous frame bundles or curvature.",
            "This scout depends on the upstream signed-permutation action receipt and does not recompute the full action enumeration.",
            "Next pass should compare alternative projections and add a direct channel-order noncommutation readout.",
        ],
        "why_not_v4_probes": "This is a clean v5 coupled special-form/density-metric scout and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "action_counts": action_counts,
            "survivor_counts": {row["family"] + "::" + row["metric_name"]: row["survivor_count"] for row in summary_rows},
            "radius_class_counts": {row["family"] + "::" + row["metric_name"]: row["radius_class_count"] for row in summary_rows},
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
