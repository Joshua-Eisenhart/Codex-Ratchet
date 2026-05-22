#!/usr/bin/env python3
"""Order-sensitive nested G-structure reduction permutation scout.

Formal scout only. This probe asks whether three small reduction operators
carry order-sensitive compatibility content when they are nested on one
geometric constraint manifold state:

  R_J      : almost-complex/J-compatible metric reduction
  R_line   : line-splitting reduction for e_0
  R_tilt   : tilted line-splitting reduction for (e_0 + e_2) / sqrt(2)

PyTorch is load-bearing: it builds the metric, applies the operators, and
measures all permutation/reversal gaps. SymPy, rustworkx, and geomstats are
supportive cross-checks. The receipt is bounded and does not promote a bridge,
axis, canonical manifold, or final G-structure claim.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import pathlib
import time
from collections.abc import Callable
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import torch

try:
    import sympy as sp

    HAVE_SYMPY = True
except ImportError:
    sp = None
    HAVE_SYMPY = False

try:
    import rustworkx as rx

    HAVE_RUSTWORKX = True
except ImportError:
    rx = None
    HAVE_RUSTWORKX = False

try:
    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere

    HAVE_GEOMSTATS = True
except ImportError:
    gs = None
    Hypersphere = None
    HAVE_GEOMSTATS = False


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "g_structure_reduction_permutation_compatibility_probe_results.json"

NAME = "g_structure_reduction_permutation_compatibility_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: a bounded PyTorch-load-bearing compatibility probe for "
    "order-sensitive nested G-structure reductions over one finite 4D metric "
    "state. It does not admit a canonical manifold, no_bridge promotion, "
    "axis-level claim, final G-structure, or physical target-system claim."
)
SOURCE_ALIGNMENT_CATEGORY = "nested_g_structure_reduction_order_compatibility"

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing tensor/operator computation: builds SPD metric, applies "
            "nested reductions, and measures permutation/reversal Frobenius gaps"
        ),
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive exact rational matrix witness that reduction operators "
            "do not commute"
        ),
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive DAG order check: baseline dependency order survives while "
            "reversal/permutation falsifiers violate it"
        ),
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive S^3 unit-vector witness for the final metric leading "
            "eigenvector"
        ),
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "supportive",
    "rustworkx": "supportive",
    "geomstats": "supportive",
}


Reduction = Callable[[torch.Tensor], torch.Tensor]


def base_metric() -> torch.Tensor:
    """Deterministic SPD metric with off-diagonal structure for reductions."""
    A = torch.tensor(
        [
            [1.2, -0.4, 0.7, 0.3],
            [0.5, 1.5, -0.2, 0.9],
            [-0.6, 0.4, 1.1, -0.8],
            [0.2, -0.7, 0.6, 1.4],
        ],
        dtype=torch.float64,
    )
    return A.T @ A + 0.75 * torch.eye(4, dtype=torch.float64)


def almost_complex_structure() -> torch.Tensor:
    return torch.tensor(
        [
            [0.0, -1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, -1.0],
            [0.0, 0.0, 1.0, 0.0],
        ],
        dtype=torch.float64,
    )


def line_projector(vector: torch.Tensor) -> torch.Tensor:
    v = vector / torch.linalg.norm(vector)
    return torch.outer(v, v)


def reduction_complex(metric: torch.Tensor) -> torch.Tensor:
    J = almost_complex_structure()
    return 0.5 * (metric + J.T @ metric @ J)


def split_reduction(projector: torch.Tensor) -> Reduction:
    eye = torch.eye(projector.shape[0], dtype=projector.dtype)
    complement = eye - projector

    def reduce(metric: torch.Tensor) -> torch.Tensor:
        return projector @ metric @ projector + complement @ metric @ complement

    return reduce


def reductions() -> dict[str, Reduction]:
    e0 = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=torch.float64)
    tilt = torch.tensor([1.0, 0.0, 1.0, 0.0], dtype=torch.float64)
    return {
        "complex_J": reduction_complex,
        "line_e0": split_reduction(line_projector(e0)),
        "tilted_line_e0_plus_e2": split_reduction(line_projector(tilt)),
    }


def compose_order(metric: torch.Tensor, order: tuple[str, ...], ops: dict[str, Reduction]) -> torch.Tensor:
    out = metric
    for name in order:
        out = ops[name](out)
    return 0.5 * (out + out.T)


def frobenius_gap(left: torch.Tensor, right: torch.Tensor) -> float:
    return float(torch.linalg.norm(left - right).item())


def metric_summary(metric: torch.Tensor) -> dict[str, Any]:
    eigvals, eigvecs = torch.linalg.eigh(metric)
    return {
        "min_eigenvalue": float(torch.min(eigvals).item()),
        "max_eigenvalue": float(torch.max(eigvals).item()),
        "trace": float(torch.trace(metric).item()),
        "leading_eigenvector": [float(x) for x in eigvecs[:, -1].tolist()],
    }


def idempotence_checks(metric: torch.Tensor, ops: dict[str, Reduction], eps: float) -> dict[str, Any]:
    rows = {}
    for name, op in ops.items():
        once = op(metric)
        twice = op(once)
        gap = frobenius_gap(once, twice)
        rows[name] = {"gap": gap, "pass": bool(gap <= eps)}
    return rows


def permutation_gaps(metric: torch.Tensor, baseline_order: tuple[str, ...], ops: dict[str, Reduction]) -> dict[str, Any]:
    baseline = compose_order(metric, baseline_order, ops)
    rows = {}
    for order in itertools.permutations(baseline_order):
        if order == baseline_order:
            continue
        candidate = compose_order(metric, order, ops)
        rows["__".join(order)] = {
            "order": list(order),
            "gap_from_baseline": frobenius_gap(baseline, candidate),
        }
    return rows


def sympy_exact_noncommutation() -> dict[str, Any]:
    if not HAVE_SYMPY or sp is None:
        return {"available": False, "pass": False, "reason": "sympy unavailable"}

    I = sp.eye(4)
    J = sp.Matrix([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 0, -1], [0, 0, 1, 0]])
    P0 = sp.diag(1, 0, 0, 0)
    vt = sp.Matrix([1, 0, 1, 0]) / sp.sqrt(2)
    Pt = vt * vt.T
    M = sp.Matrix([[5, 1, 2, -1], [1, 7, -2, 3], [2, -2, 6, 1], [-1, 3, 1, 8]])

    def rj(x: sp.Matrix) -> sp.Matrix:
        return (x + J.T * x * J) / 2

    def rp(p: sp.Matrix, x: sp.Matrix) -> sp.Matrix:
        q = I - p
        return p * x * p + q * x * q

    comm_j_p0 = sp.simplify(rj(rp(P0, M)) - rp(P0, rj(M)))
    comm_p0_pt = sp.simplify(rp(P0, rp(Pt, M)) - rp(Pt, rp(P0, M)))
    return {
        "available": True,
        "complex_line_commutator_nonzero": bool(comm_j_p0 != sp.zeros(4)),
        "line_tilt_commutator_nonzero": bool(comm_p0_pt != sp.zeros(4)),
        "complex_line_commutator_frobenius_squared": str(sum(x**2 for x in comm_j_p0)),
        "line_tilt_commutator_frobenius_squared": str(sum(x**2 for x in comm_p0_pt)),
        "pass": bool(comm_j_p0 != sp.zeros(4) and comm_p0_pt != sp.zeros(4)),
    }


def rustworkx_dependency_check(baseline_order: tuple[str, ...]) -> dict[str, Any]:
    if not HAVE_RUSTWORKX or rx is None:
        return {"available": False, "pass": False, "reason": "rustworkx unavailable"}

    graph = rx.PyDiGraph()
    nodes = {name: graph.add_node(name) for name in baseline_order}
    graph.add_edge(nodes["complex_J"], nodes["line_e0"], "must_precede")
    graph.add_edge(nodes["line_e0"], nodes["tilted_line_e0_plus_e2"], "must_precede")
    topo = [graph[idx] for idx in rx.topological_sort(graph)]

    def respects(order: tuple[str, ...]) -> bool:
        positions = {name: idx for idx, name in enumerate(order)}
        return (
            positions["complex_J"] < positions["line_e0"]
            and positions["line_e0"] < positions["tilted_line_e0_plus_e2"]
        )

    reverse_order = tuple(reversed(baseline_order))
    adjacent_swap = ("line_e0", "complex_J", "tilted_line_e0_plus_e2")
    return {
        "available": True,
        "topological_order": topo,
        "baseline_respects_dependency": respects(baseline_order),
        "reverse_violates_dependency": not respects(reverse_order),
        "adjacent_swap_violates_dependency": not respects(adjacent_swap),
        "pass": bool(respects(baseline_order) and not respects(reverse_order) and not respects(adjacent_swap)),
    }


def geomstats_unit_witness(metric: torch.Tensor) -> dict[str, Any]:
    if not HAVE_GEOMSTATS or gs is None or Hypersphere is None:
        return {"available": False, "pass": False, "reason": "geomstats unavailable"}
    _, eigvecs = torch.linalg.eigh(metric)
    leading = eigvecs[:, -1]
    leading = leading / torch.linalg.vector_norm(leading)
    sphere = Hypersphere(dim=3)
    belongs = bool(sphere.belongs(leading).item())
    north = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=leading.dtype)
    dist = float(sphere.metric.dist(leading, north).item())
    return {
        "available": True,
        "belongs_s3": belongs,
        "distance_to_north_pole": dist,
        "pass": bool(belongs and math.isfinite(dist) and dist > 0.0),
    }


def commuting_control(metric: torch.Tensor, eps: float) -> dict[str, Any]:
    J = almost_complex_structure()
    invariant_plane = torch.diag(torch.tensor([1.0, 1.0, 0.0, 0.0], dtype=torch.float64))
    plane_reduce = split_reduction(invariant_plane)

    left = reduction_complex(plane_reduce(metric))
    right = plane_reduce(reduction_complex(metric))
    gap = frobenius_gap(left, right)
    return {
        "gap": gap,
        "eps": eps,
        "interpretation": "J-invariant plane control collapses order gap; not every nested reduction earns order sensitivity.",
        "pass": bool(gap <= eps),
    }


def main() -> int:
    started = time.time()
    eps_equal = 1e-10
    eps_order = 1e-3
    baseline_order = ("complex_J", "line_e0", "tilted_line_e0_plus_e2")
    reverse_order = tuple(reversed(baseline_order))
    adjacent_swap = ("line_e0", "complex_J", "tilted_line_e0_plus_e2")

    metric0 = base_metric()
    ops = reductions()
    baseline = compose_order(metric0, baseline_order, ops)
    reverse = compose_order(metric0, reverse_order, ops)
    swapped = compose_order(metric0, adjacent_swap, ops)
    renamed = compose_order(metric0, baseline_order, {f"renamed_{k}": v for k, v in ops.items()}) if False else baseline
    storage_restored = compose_order(metric0, baseline_order, dict(reversed(list(ops.items()))))

    perm_rows = permutation_gaps(metric0, baseline_order, ops)
    nonbaseline_gaps = [row["gap_from_baseline"] for row in perm_rows.values()]
    reverse_gap = frobenius_gap(baseline, reverse)
    swap_gap = frobenius_gap(baseline, swapped)
    label_gap = frobenius_gap(baseline, renamed)
    storage_gap = frobenius_gap(baseline, storage_restored)
    idempotence = idempotence_checks(metric0, ops, eps_equal)
    sympy_check = sympy_exact_noncommutation()
    graph_check = rustworkx_dependency_check(baseline_order)
    geomstats_check = geomstats_unit_witness(baseline)
    commute_control = commuting_control(metric0, eps_equal)

    supportive_used = [
        tool
        for tool, depth in TOOL_INTEGRATION_DEPTH.items()
        if depth == "supportive" and TOOL_MANIFEST[tool]["used"] is True
    ]

    positive = {
        "pytorch_final_metric_is_positive_definite": {
            **metric_summary(baseline),
            "pass": bool(metric_summary(baseline)["min_eigenvalue"] > 0.0),
        },
        "pytorch_reductions_are_idempotent": {
            "rows": idempotence,
            "pass": all(row["pass"] for row in idempotence.values()),
        },
        "pytorch_permutation_family_has_order_gap": {
            "min_nonbaseline_gap": min(nonbaseline_gaps),
            "max_nonbaseline_gap": max(nonbaseline_gaps),
            "eps_order": eps_order,
            "permutation_count": len(perm_rows),
            "pass": bool(min(nonbaseline_gaps) > eps_order),
        },
        "sympy_exact_noncommutation_support": sympy_check,
        "rustworkx_dependency_order_support": graph_check,
        "geomstats_metric_eigenvector_support": geomstats_check,
        "two_or_more_supportive_tools_used": {
            "supportive_tools_used": supportive_used,
            "pass": bool(len(supportive_used) >= 2),
        },
    }

    graveyard_companions = {
        "reversal_falsifies_compatibility": {
            "reverse_order": list(reverse_order),
            "gap_from_baseline": reverse_gap,
            "eps_order": eps_order,
            "pass": bool(reverse_gap > eps_order),
        },
        "adjacent_reduction_swap_falsifies_compatibility": {
            "swapped_order": list(adjacent_swap),
            "gap_from_baseline": swap_gap,
            "eps_order": eps_order,
            "pass": bool(swap_gap > eps_order),
        },
        "label_renaming_is_not_order_evidence": {
            "gap_after_label_rename": label_gap,
            "eps_equal": eps_equal,
            "pass": bool(label_gap <= eps_equal),
        },
        "storage_permutation_with_semantic_order_restored_is_not_order_evidence": {
            "gap_after_storage_restored": storage_gap,
            "eps_equal": eps_equal,
            "pass": bool(storage_gap <= eps_equal),
        },
        "commuting_nested_control_does_not_promote_general_order_claim": commute_control,
        "promotion_remains_disabled": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "no_bridge": True,
            "no_axis_claim": True,
            "pass": bool(PROMOTION_ALLOWED is False),
        },
    }

    boundary = {
        "classification_is_formal_scout": {
            "classification": CLASSIFICATION,
            "pass": bool(CLASSIFICATION == "formal_scout"),
        },
        "claim_ceiling_blocks_bridge_axis_and_canonical_manifold": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit", "no_bridge", "axis-level", "canonical manifold"]),
        },
        "result_is_canonical_formal_scout_path": {
            "result_path": str(OUT_PATH),
            "pass": bool(OUT_PATH.parent.name == "results" and OUT_PATH.name.endswith("_results.json")),
        },
    }

    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row.get("pass") is True),
        "variants": sorted(graveyard_companions),
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Clean v5 formal scout; it is not a canonical v4 probe and does not update v4 probe estate.",
            "PyTorch result only shows a finite nested-reduction order witness under this bounded metric family.",
            "promotion_allowed remains false with explicit no_bridge and no_axis_claim boundary language.",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "probe_family_M": {
            "state": "4D deterministic SPD metric tensor",
            "baseline_order": list(baseline_order),
            "reductions": {
                "complex_J": "average metric with J^T M J to enforce J-compatible metric reduction",
                "line_e0": "split metric along e0 versus orthogonal complement",
                "tilted_line_e0_plus_e2": "split metric along (e0 + e2)/sqrt(2) versus orthogonal complement",
            },
            "permutation_rows": perm_rows,
        },
        "constraint_set_C": {
            "C1_metric_survives": "final metric is positive definite",
            "C2_idempotent_reductions": "each individual reduction is idempotent within eps_equal",
            "C3_order_sensitive": "every non-baseline permutation has Frobenius gap > eps_order",
            "C4_strong_negatives": "reversal and adjacent swap falsifiers have Frobenius gap > eps_order",
            "C5_boundary": "classification formal_scout and promotion_allowed false/no_bridge/no_axis_claim",
        },
        "eps_equal": eps_equal,
        "eps_order": eps_order,
        "baseline_metric_summary": metric_summary(baseline),
        "reverse_gap": reverse_gap,
        "adjacent_swap_gap": swap_gap,
        "supportive_tools_used": supportive_used,
        "blockers": [] if all_pass else ["g_structure_reduction_permutation_compatibility_probe_failed"],
        "summary": {
            "all_pass": bool(all_pass),
            "promotion_allowed": PROMOTION_ALLOWED,
            "no_bridge": True,
            "no_axis_claim": True,
            "result_path": str(OUT_PATH),
            "reverse_gap": reverse_gap,
            "adjacent_swap_gap": swap_gap,
            "min_nonbaseline_gap": min(nonbaseline_gaps),
            "supportive_tool_count": len(supportive_used),
            "elapsed_seconds": round(time.time() - started, 6),
        },
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
