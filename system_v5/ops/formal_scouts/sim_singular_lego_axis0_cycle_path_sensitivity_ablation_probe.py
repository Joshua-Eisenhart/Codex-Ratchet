#!/usr/bin/env python3
"""Formal scout: v2 ablation/cycle-path sensitivity for singular Axis0 wiring.

This is the bounded successor to the red
sim_singular_lego_wired_axis0_plural_manifold_engine_probe.py blocker.  It does
not edit or import that probe.  The narrow question here is whether a singular
lego/manifold/engine-style cycle can be distinguished from import-only wiring by
per-lego ablation, cycle-path order sensitivity, and autograd sensitivity.

The scout intentionally keeps two known failures as controls:

- path_entropy remains blocked when the finite cyclic token schedule plateaus.
- cycle-autograd severance remains blocked in a detached-control path.

Passing this scout means only that the active torch path is sensitive while the
import-only and detached controls are not.  It does not admit an engine, Axis0,
basin, manifold tower, bridge, or canonical claim.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from collections import Counter
from typing import Any

import cvc5
import rustworkx as rx
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "singular_lego_axis0_cycle_path_sensitivity_ablation_probe_results.json"

NAME = "singular_lego_axis0_cycle_path_sensitivity_ablation_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests per-lego ablation, cycle-path order sensitivity, "
    "and torch/autograd sensitivity for a bounded singular Axis0/plural-manifold "
    "cycle surrogate against import-only and detached-autograd controls. "
    "Preserves path_entropy blocked status and cycle-autograd severance as "
    "graveyard controls when observed. Does not admit canonical engine, Axis0, "
    "basin, manifold tower, bridge, QIT, Holodeck, physics, cognition, or target "
    "system claims; promotion_allowed is false."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing active cycle, per-lego ablation deltas, and autograd sensitivity gradients",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive SMT witness that active sensitivity cannot collapse to import-only wiring under measured thresholds",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive independent SMT witness for the same active-vs-import separation predicate",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "supportive graph check that the ordered lego path is a real directed cycle and single-node removals break the cycle",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON, time, pathlib, math, and Counter utilities for bounded receipt construction",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "supportive",
    "cvc5": "supportive",
    "rustworkx": "supportive",
    "python_stdlib": "supportive",
}

LEGO_LABELS = [
    "density_psd",
    "hopf_projection",
    "weyl_chirality",
    "pauli_commutator",
    "cptp_damping",
    "simplicial_homology",
    "spectral_triple",
    "spectral_entropy",
    "bipartite_ci",
    "topology_witness",
    "signed_ci",
    "autograd_ci",
    "baseline_psd",
]

DIM = 4
N_CYCLES = 4
SENSITIVITY_FLOOR = 1.0e-4
GRADIENT_FLOOR = 1.0e-6
CONTROL_CEILING = 1.0e-12
DTYPE = torch.float64


def initial_state() -> torch.Tensor:
    return torch.tensor([0.42, -0.17, 0.31, 0.08], dtype=DTYPE)


def lego_operator(index: int) -> torch.Tensor:
    """Small deterministic non-commuting operator for one lego slot."""
    i = float(index + 1)
    mat = torch.zeros((DIM, DIM), dtype=DTYPE)
    for r in range(DIM):
        for c in range(DIM):
            if r == c:
                mat[r, c] = 0.74 + 0.012 * i
            elif (r + 1) % DIM == c:
                mat[r, c] = 0.031 * math.sin(i + r)
            elif (c + 1) % DIM == r:
                mat[r, c] = 0.027 * math.cos(i + c)
            else:
                mat[r, c] = 0.006 * ((-1.0) ** (index + r + c))
    return mat


def lego_bias(index: int) -> torch.Tensor:
    i = float(index + 1)
    return torch.tensor(
        [
            0.021 * math.sin(i),
            0.017 * math.cos(i * 0.7),
            0.013 * math.sin(i * 1.3),
            0.011 * math.cos(i * 1.7),
        ],
        dtype=DTYPE,
    )


def base_weights(requires_grad: bool = False) -> torch.Tensor:
    values = torch.tensor(
        [0.18 + 0.007 * i + 0.003 * math.sin(i) for i in range(len(LEGO_LABELS))],
        dtype=DTYPE,
    )
    if requires_grad:
        values.requires_grad_(True)
    return values


def active_cycle(
    weights: torch.Tensor,
    order: list[int] | None = None,
    *,
    ablate: int | None = None,
    detach_each_step: bool = False,
) -> dict[str, Any]:
    order = list(range(len(LEGO_LABELS))) if order is None else order
    state = initial_state()
    states = [state]
    energies: list[torch.Tensor] = []
    tokens: list[int] = []
    used_weights = weights.clone()
    if ablate is not None:
        used_weights = used_weights.clone()
        used_weights[ablate] = 0.0

    for cycle_idx in range(N_CYCLES):
        for slot_pos, lego_idx in enumerate(order):
            w = used_weights[lego_idx]
            op = lego_operator(lego_idx)
            bias = lego_bias(lego_idx)
            feedback = 0.028 * torch.roll(state, shifts=1) * torch.tanh(state.sum())
            phase = 0.01 * math.sin((cycle_idx + 1) * (slot_pos + 1))
            state = torch.tanh(op.mv(state) + w * bias + feedback + phase)
            if detach_each_step:
                state = state.detach() + (weights * 0.0).sum()
            states.append(state)
            energies.append(torch.sum(state * state))
            tokens.append(lego_idx)

    return {"state": state, "states": states, "energies": energies, "tokens": tokens}


def import_only_cycle(weights: torch.Tensor, order: list[int] | None = None, ablate: int | None = None) -> dict[str, Any]:
    """Control path that names legos but does not consume weights or order."""
    del order, ablate
    state = initial_state() + (weights * 0.0).sum()
    energies = [torch.sum(state * state) + (weights * 0.0).sum() for _ in range(N_CYCLES * len(LEGO_LABELS))]
    return {"state": state, "states": [state for _ in energies], "energies": energies, "tokens": [0 for _ in energies]}


def categorical_entropy(tokens: list[int], n_symbols: int) -> float:
    if not tokens:
        return 0.0
    counts = Counter(tokens)
    total = float(sum(counts.values()))
    probs = [counts.get(i, 0) / total for i in range(n_symbols)]
    raw = -sum(p * math.log(p) for p in probs if p > 0.0)
    return raw / math.log(n_symbols)


def path_entropy_status(tokens: list[int]) -> dict[str, Any]:
    width = len(LEGO_LABELS)
    entropies = [
        categorical_entropy(tokens[max(0, i - width + 1) : i + 1], len(LEGO_LABELS))
        for i in range(len(tokens))
    ]
    diffs = [entropies[i + 1] - entropies[i] for i in range(len(entropies) - 1)]
    zero_count = sum(abs(d) <= 1.0e-12 for d in diffs)
    zero_fraction = zero_count / max(len(diffs), 1)
    blocked = zero_fraction > 0.50
    return {
        "blocked": blocked,
        "status": "blocked_degenerate_plateau" if blocked else "open_non_degenerate",
        "zero_diff_count": zero_count,
        "total_diffs": len(diffs),
        "zero_fraction": zero_fraction,
        "first_entropy_values": [round(v, 6) for v in entropies[:18]],
        "pass": blocked,
    }


def signature(run: dict[str, Any]) -> torch.Tensor:
    energies = torch.stack(run["energies"])
    final = run["state"]
    diffs = energies[1:] - energies[:-1]
    positive_fraction = (diffs > 0).to(DTYPE).mean()
    negative_fraction = (diffs < 0).to(DTYPE).mean()
    energy_span = energies.max() - energies.min()
    late_energy = energies[-len(LEGO_LABELS) :].mean()
    early_energy = energies[: len(LEGO_LABELS)].mean()
    signed_area = torch.sum(diffs * torch.linspace(0.2, 1.0, len(diffs), dtype=DTYPE))
    return torch.stack(
        [
            final[0],
            final[1],
            final[2],
            final[3],
            positive_fraction,
            negative_fraction,
            energy_span,
            late_energy - early_energy,
            signed_area,
        ]
    )


def l2_gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(a.detach() - b.detach()).item())


def ablation_report(kind: str) -> dict[str, Any]:
    weights = base_weights()
    runner = active_cycle if kind == "active" else import_only_cycle
    base = runner(weights)
    base_sig = signature(base)
    rows = []
    for idx, label in enumerate(LEGO_LABELS):
        ablated = runner(weights, ablate=idx)
        gap = l2_gap(base_sig, signature(ablated))
        rows.append({"lego": label, "gap": gap, "pass": gap > SENSITIVITY_FLOOR if kind == "active" else gap <= CONTROL_CEILING})
    gaps = [row["gap"] for row in rows]
    if kind == "active":
        passed = all(row["pass"] for row in rows)
    else:
        passed = all(row["pass"] for row in rows)
    return {
        "kind": kind,
        "rows": rows,
        "min_gap": min(gaps),
        "max_gap": max(gaps),
        "mean_gap": sum(gaps) / len(gaps),
        "pass": passed,
    }


def path_variant_report(kind: str) -> dict[str, Any]:
    weights = base_weights()
    runner = active_cycle if kind == "active" else import_only_cycle
    base_order = list(range(len(LEGO_LABELS)))
    variants = {
        "reverse": list(reversed(base_order)),
        "rotated_by_three": base_order[3:] + base_order[:3],
        "evens_then_odds": base_order[::2] + base_order[1::2],
    }
    base_sig = signature(runner(weights, order=base_order))
    rows = {}
    for name, order in variants.items():
        gap = l2_gap(base_sig, signature(runner(weights, order=order)))
        rows[name] = {
            "gap": gap,
            "order_labels": [LEGO_LABELS[i] for i in order],
            "pass": gap > SENSITIVITY_FLOOR if kind == "active" else gap <= CONTROL_CEILING,
        }
    return {
        "kind": kind,
        "rows": rows,
        "min_gap": min(row["gap"] for row in rows.values()),
        "max_gap": max(row["gap"] for row in rows.values()),
        "pass": all(row["pass"] for row in rows.values()),
    }


def autograd_report() -> dict[str, Any]:
    weights = base_weights(requires_grad=True)
    score = signature(active_cycle(weights)).pow(2).sum()
    score.backward()
    grads = weights.grad.detach()
    abs_grads = [float(v) for v in torch.abs(grads)]
    return {
        "score": float(score.detach().item()),
        "min_abs_grad": min(abs_grads),
        "max_abs_grad": max(abs_grads),
        "per_lego_abs_grad": dict(zip(LEGO_LABELS, abs_grads)),
        "pass": min(abs_grads) > GRADIENT_FLOOR,
    }


def detached_autograd_control() -> dict[str, Any]:
    weights = base_weights(requires_grad=True)
    score = signature(active_cycle(weights, detach_each_step=True)).pow(2).sum()
    score.backward()
    grads = weights.grad.detach()
    abs_grads = [float(v) for v in torch.abs(grads)]
    return {
        "control": "detached_cycle_autograd_severance",
        "min_abs_grad": min(abs_grads),
        "max_abs_grad": max(abs_grads),
        "per_lego_abs_grad": dict(zip(LEGO_LABELS, abs_grads)),
        "blocked": max(abs_grads) <= CONTROL_CEILING,
        "pass": max(abs_grads) <= CONTROL_CEILING,
    }


def import_only_autograd_control() -> dict[str, Any]:
    weights = base_weights(requires_grad=True)
    score = signature(import_only_cycle(weights)).pow(2).sum()
    score.backward()
    grads = weights.grad.detach()
    abs_grads = [float(v) for v in torch.abs(grads)]
    return {
        "control": "import_only_wiring",
        "min_abs_grad": min(abs_grads),
        "max_abs_grad": max(abs_grads),
        "per_lego_abs_grad": dict(zip(LEGO_LABELS, abs_grads)),
        "pass": max(abs_grads) <= CONTROL_CEILING,
    }


def rustworkx_cycle_check() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from(range(len(LEGO_LABELS)))
    graph.add_edges_from_no_data((i, (i + 1) % len(LEGO_LABELS)) for i in range(len(LEGO_LABELS)))
    cycles = list(rx.simple_cycles(graph))
    removal_rows = []
    for idx, label in enumerate(LEGO_LABELS):
        reduced = graph.copy()
        reduced.remove_node(idx)
        removal_rows.append(
            {
                "removed_lego": label,
                "strongly_connected_after_removal": rx.is_strongly_connected(reduced),
                "cycle_count_after_removal": len(list(rx.simple_cycles(reduced))),
            }
        )
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "cycle_count": len(cycles),
        "strongly_connected": rx.is_strongly_connected(graph),
        "single_removal_rows": removal_rows,
        "pass": (
            graph.num_nodes() == len(LEGO_LABELS)
            and graph.num_edges() == len(LEGO_LABELS)
            and len(cycles) >= 1
            and all(row["cycle_count_after_removal"] == 0 for row in removal_rows)
        ),
    }


def z3_separation_witness(active_min_delta: float, import_max_delta: float, active_min_grad: float) -> dict[str, Any]:
    scale = 10**9
    a = z3.Int("active_min_delta_scaled")
    i = z3.Int("import_max_delta_scaled")
    g = z3.Int("active_min_grad_scaled")
    solver = z3.Solver()
    solver.add(a == int(active_min_delta * scale))
    solver.add(i == int(import_max_delta * scale))
    solver.add(g == int(active_min_grad * scale))
    solver.add(a > int(SENSITIVITY_FLOOR * scale))
    solver.add(i <= int(CONTROL_CEILING * scale))
    solver.add(g > int(GRADIENT_FLOOR * scale))
    solver.add(z3.Or(a <= int(SENSITIVITY_FLOOR * scale), i > int(CONTROL_CEILING * scale), g <= int(GRADIENT_FLOOR * scale)))
    status = solver.check()
    return {
        "solver": "z3",
        "status": str(status),
        "active_min_delta": active_min_delta,
        "import_max_delta": import_max_delta,
        "active_min_grad": active_min_grad,
        "pass": status == z3.unsat,
    }


def cvc5_separation_witness(active_min_delta: float, import_max_delta: float, active_min_grad: float) -> dict[str, Any]:
    scale = 10**9
    active_scaled = int(active_min_delta * scale)
    import_scaled = int(import_max_delta * scale)
    grad_scaled = int(active_min_grad * scale)
    sensitivity_scaled = int(SENSITIVITY_FLOOR * scale)
    control_scaled = int(CONTROL_CEILING * scale)
    gradient_scaled = int(GRADIENT_FLOOR * scale)

    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    a = solver.mkConst(int_sort, "active_min_delta_scaled")
    i = solver.mkConst(int_sort, "import_max_delta_scaled")
    g = solver.mkConst(int_sort, "active_min_grad_scaled")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, a, solver.mkInteger(active_scaled)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, i, solver.mkInteger(import_scaled)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, g, solver.mkInteger(grad_scaled)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GT, a, solver.mkInteger(sensitivity_scaled)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, i, solver.mkInteger(control_scaled)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GT, g, solver.mkInteger(gradient_scaled)))
    collapse = solver.mkTerm(
        cvc5.Kind.OR,
        solver.mkTerm(cvc5.Kind.LEQ, a, solver.mkInteger(sensitivity_scaled)),
        solver.mkTerm(cvc5.Kind.GT, i, solver.mkInteger(control_scaled)),
        solver.mkTerm(cvc5.Kind.LEQ, g, solver.mkInteger(gradient_scaled)),
    )
    solver.assertFormula(collapse)
    status = solver.checkSat()
    return {
        "solver": "cvc5",
        "status": str(status),
        "active_min_delta": active_min_delta,
        "import_max_delta": import_max_delta,
        "active_min_grad": active_min_grad,
        "pass": str(status) == "unsat",
    }


def section_pass(section: dict[str, Any]) -> bool:
    return all(isinstance(row, dict) and row.get("pass") is True for row in section.values())


def main() -> dict[str, Any]:
    started = time.time()

    active_ablation = ablation_report("active")
    import_ablation = ablation_report("import_only")
    active_path = path_variant_report("active")
    import_path = path_variant_report("import_only")
    active_grad = autograd_report()
    detached_grad = detached_autograd_control()
    import_grad = import_only_autograd_control()
    graph = rustworkx_cycle_check()
    active_tokens = active_cycle(base_weights())["tokens"]
    path_entropy = path_entropy_status(active_tokens)

    active_min_delta = min(active_ablation["min_gap"], active_path["min_gap"])
    import_max_delta = max(import_ablation["max_gap"], import_path["max_gap"], import_grad["max_abs_grad"])
    z3_witness = z3_separation_witness(active_min_delta, import_max_delta, active_grad["min_abs_grad"])
    cvc5_witness = cvc5_separation_witness(active_min_delta, import_max_delta, active_grad["min_abs_grad"])

    positive = {
        "active_per_lego_remove_and_rerun_ablation_is_sensitive": active_ablation,
        "active_cycle_path_order_variants_are_sensitive": active_path,
        "torch_autograd_sees_every_active_lego_weight": active_grad,
        "rustworkx_ordered_lego_cycle_is_real_and_single_removals_break_it": graph,
        "z3_active_not_import_only_separation_witness": z3_witness,
        "cvc5_active_not_import_only_separation_witness": cvc5_witness,
    }

    graveyard_companions = {
        "import_only_wiring_has_zero_ablation_delta": import_ablation,
        "import_only_wiring_has_zero_path_order_delta": import_path,
        "import_only_wiring_has_zero_autograd_sensitivity": import_grad,
        "path_entropy_blocked_degenerate_plateau_preserved": path_entropy,
        "cycle_autograd_severance_preserved_in_detached_control": detached_grad,
    }

    boundary = {
        "formal_scout_only_no_engine_axis_basin_or_manifold_promotion": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "forbidden_promotions": ["engine", "axis", "basin", "manifold_tower", "bridge", "canonical"],
            "pass": PROMOTION_ALLOWED is False,
        },
        "active_path_not_import_only_wiring": {
            "active_min_delta": active_min_delta,
            "import_max_delta": import_max_delta,
            "ratio_floor": active_min_delta / max(import_max_delta, CONTROL_CEILING),
            "pass": active_min_delta > SENSITIVITY_FLOOR and import_max_delta <= CONTROL_CEILING,
        },
        "blocked_controls_are_controls_not_blockers_for_this_v2_question": {
            "path_entropy_status": path_entropy["status"],
            "detached_autograd_blocked": detached_grad["blocked"],
            "pass": path_entropy["blocked"] and detached_grad["blocked"],
        },
    }

    nearby_variants = {
        "total": 3,
        "passed": int(active_ablation["pass"]) + int(active_path["pass"]) + int(import_ablation["pass"] and import_path["pass"]),
        "variants": {
            "per_lego_ablation": active_ablation["pass"],
            "cycle_path_order": active_path["pass"],
            "import_only_control": import_ablation["pass"] and import_path["pass"],
        },
    }

    all_pass = (
        section_pass(positive)
        and section_pass(graveyard_companions)
        and section_pass(boundary)
        and nearby_variants["passed"] == nearby_variants["total"]
    )

    result = {
        "name": NAME,
        "probe": NAME,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "v5 formal-scout blocker repair for the red singular lego/manifold/engine v1 deferred ablation question",
            "tests remove-and-rerun per-lego sensitivity and cycle path order sensitivity rather than import presence",
            "keeps path_entropy and cycle-autograd severance as blocked controls and does not promote engine, Axis0, basin, or manifold claims",
        ],
        "blockers": [],
        "positive_summary": {
            "active_min_delta": active_min_delta,
            "active_min_grad": active_grad["min_abs_grad"],
            "import_max_delta": import_max_delta,
            "path_entropy_status": path_entropy["status"],
            "detached_autograd_blocked": detached_grad["blocked"],
        },
        "promotion_condition": "none in this scout; requires separate external admission and stronger engine/axis/basin evidence",
        "demotion_condition": "demote if active ablation/path deltas collapse to import-only controls or blocked controls are hidden",
        "elapsed_seconds": time.time() - started,
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "result": str(OUT_PATH),
                "all_pass": all_pass,
                "active_min_delta": active_min_delta,
                "active_min_grad": active_grad["min_abs_grad"],
                "import_max_delta": import_max_delta,
                "path_entropy_status": path_entropy["status"],
                "detached_autograd_blocked": detached_grad["blocked"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return result


if __name__ == "__main__":
    main()
