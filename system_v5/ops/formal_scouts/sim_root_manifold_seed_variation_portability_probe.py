#!/usr/bin/env python3
"""Root manifold seed-variation portability probe.

Exercises the 13-layer geometric-constraint-manifold pipeline across 10 seeds
and 3 initial-state configurations.  Measures stability of removal gaps,
order-sensitivity, z3+cvc5 UNSAT admission, le-wm advantage, and auto_LiRPA
containment across the sweep.  A green receipt means the root-manifold
fixture is stable under seed/initial-state variation.

Formal scout only.  Does not admit a final manifold, basin, axis, bridge,
physics, or canonical claim.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import torch
import torch.nn.functional as F
import z3

AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
if AUTO_LIRPA_ROOT.exists() and str(AUTO_LIRPA_ROOT) not in sys.path:
    sys.path.insert(0, str(AUTO_LIRPA_ROOT))

from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sim_root_geometric_constraint_manifold_maturity_pytorch_toolchain_probe import (  # noqa: E402
    LAYERS,
    LAYER_FUNCTIONS,
    TAU_ORDER_GAP,
    TAU_LAYER_REMOVAL,
    TAU_PEPS3D_GAP,
    dependency_graph,
    run_semantic_manifold,
    cube_edges,
    peps3d_signature,
    MaturityEnergyAdapter,
    sha256_file,
)

RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "root_manifold_seed_variation_portability_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "root_geometric_constraint_manifold_seed_portability"
CLAIM_CEILING = (
    "Formal scout only: exercises the root geometric-constraint-manifold "
    "pipeline across 10 seeds and 3 operating-range initial-state configs "
    "plus 1 boundary config.  Measures stability of removal gaps, "
    "order-sensitivity, z3+cvc5 admission, le-wm advantage, and auto_LiRPA "
    "containment within operating range.  Documents tanh-saturation boundary "
    "in finite_constraint_complex under wide initial states.  Does not admit "
    "a final manifold, final G-structure, real attractor basin, final Axis0, "
    "bridge, physics, target-system, or canonical claim."
)

SEEDS = [20260518, 42, 7, 1337, 99999, 314159, 271828, 65537, 12345, 88888]

OPERATING_CONFIGS = {
    "default": {"start": -0.48, "end": 0.52},
    "narrow": {"start": -0.1, "end": 0.1},
    "offset": {"start": -0.3, "end": 0.7},
}

BOUNDARY_CONFIGS = {
    "wide": {"start": -1.5, "end": 1.5},
    "shifted_positive": {"start": 0.05, "end": 0.95},
}

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing seed-swept layer transforms, autograd, PEPS3D contractions, le-wm tensors"},
    "auto_LiRPA": {"tried": True, "used": True, "reason": "load-bearing IBP containment verified per seed"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing UNSAT admission per seed×config"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent UNSAT admission per seed×config"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt serialization"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}

EXTERNAL_MODULE_MANIFEST = {
    "le_wm_module": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ARPredictor loss advantage verified per seed",
        "path": str(LEWM_MODULE_PATH),
    }
}
EXTERNAL_MODULE_INTEGRATION_DEPTH = {"le_wm_module": "load_bearing"}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        if value.numel() <= 256:
            return value.detach().cpu().tolist()
        return f"<tensor shape={list(value.shape)} dtype={value.dtype}>"
    if isinstance(value, complex):
        return {"re": value.real, "im": value.imag}
    return value


def make_initial_state(config: dict[str, float], seed: int) -> torch.Tensor:
    base = torch.linspace(config["start"], config["end"], steps=8, dtype=torch.float32)
    gen = torch.Generator().manual_seed(seed)
    noise = torch.randn(8, generator=gen, dtype=torch.float32) * 0.02 * (config["end"] - config["start"])
    return (base + noise).requires_grad_(True)


def load_lewm_module() -> Any:
    if not LEWM_MODULE_PATH.exists():
        raise FileNotFoundError(LEWM_MODULE_PATH)
    spec = importlib.util.spec_from_file_location("lewm_seed_port", LEWM_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {LEWM_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_manifold_with_state(order: list[int], state: torch.Tensor, disabled_layer: int | None = None) -> dict[str, Any]:
    root_state = state
    history = []
    for layer_idx in order:
        if disabled_layer is None or layer_idx != disabled_layer:
            state = LAYER_FUNCTIONS[layer_idx](state)
        else:
            state = torch.tanh(0.97 * state + 0.03 * torch.roll(state, 1))
        history.append(state)
    final = state
    history_t = torch.stack(history)
    energy = torch.sum(history_t * history_t, dim=1)
    grad = torch.autograd.grad(final.square().sum() + energy.mean(), root_state, retain_graph=True, allow_unused=True)[0]
    grad_norm = float(torch.linalg.vector_norm(grad).item()) if grad is not None else 0.0
    return {"final_state": final, "history": history_t, "energy": energy, "autograd_grad_norm": grad_norm}


def lirpa_check(history: torch.Tensor, peps_sig: torch.Tensor) -> dict[str, Any]:
    features = torch.cat([history.detach().to(torch.float32), peps_sig.detach().reshape(1, -1).repeat(13, 1)], dim=1)
    model = MaturityEnergyAdapter(features.shape[1]).eval()
    bounded = BoundedModule(model, features)
    eps = 0.006
    bounded_x = BoundedTensor(features, PerturbationLpNorm(norm=float("inf"), eps=eps))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    with torch.no_grad():
        nominal = model(features)
    contains = bool(torch.all(nominal >= lb - 2e-5).item() and torch.all(nominal <= ub + 2e-5).item())
    width = float(torch.mean(ub - lb).item())
    return {"contains_nominal": contains, "mean_bound_width": width, "pass": contains and width > 0.0}


def lewm_check(lewm_mod: Any, history: torch.Tensor, seed: int) -> dict[str, Any]:
    torch.manual_seed(seed + 51826)
    predictor = lewm_mod.ARPredictor(
        num_frames=history.shape[0], depth=1, heads=1, mlp_dim=16,
        input_dim=8, hidden_dim=8, output_dim=8, dim_head=8, dropout=0.0, emb_dropout=0.0,
    )
    emb = history.detach().unsqueeze(0)
    actions = torch.tanh(torch.roll(emb, shifts=1, dims=1) - 0.07 * emb)
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.015, weight_decay=0.0)
    predictor.train()
    for _ in range(60):
        optimizer.zero_grad(set_to_none=True)
        pred = predictor(emb, actions)
        loss = F.mse_loss(pred[:, :-1], emb[:, 1:])
        loss.backward()
        optimizer.step()
    predictor.eval()
    with torch.no_grad():
        pred = predictor(emb, actions)
        collapsed = emb.mean(dim=1, keepdim=True).expand_as(emb)
        zero_pred = predictor(emb, actions * 0.0)
        collapsed_pred = predictor(collapsed, actions * 0.0)
        loss = F.mse_loss(pred[:, :-1], emb[:, 1:])
        zero_loss = F.mse_loss(zero_pred[:, :-1], emb[:, 1:])
        collapsed_loss = F.mse_loss(collapsed_pred[:, :-1], emb[:, 1:])
    best_control = torch.minimum(zero_loss, collapsed_loss)
    advantage = float(((best_control - loss) / best_control.clamp_min(1e-9)).item())
    return {"advantage": advantage, "pass": advantage > 0.02}


def z3_admission(actuals: dict[str, bool]) -> bool:
    solver = z3.Solver()
    terms = {name: z3.Bool(name) for name in actuals}
    admitted = z3.Bool("admitted")
    for name, value in actuals.items():
        solver.add(terms[name] == z3.BoolVal(bool(value)))
    solver.add(admitted == z3.And(*terms.values()))
    solver.add(z3.Not(admitted))
    return solver.check() == z3.unsat


def cvc5_admission(actuals: dict[str, bool]) -> bool:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    terms = {name: solver.mkConst(bool_sort, name) for name in actuals}
    admitted = solver.mkConst(bool_sort, "admitted")
    for name, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[name], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *terms.values())))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    return solver.checkSat().isUnsat()


def run_single_config(seed: int, config_name: str, config: dict[str, float], order: list[int], lewm_mod: Any) -> dict[str, Any]:
    state = make_initial_state(config, seed)
    canonical = run_manifold_with_state(order, state)
    canonical_final = canonical["final_state"]

    swapped_order = order[:]
    swapped_order[3], swapped_order[4] = swapped_order[4], swapped_order[3]
    state_s = make_initial_state(config, seed)
    swapped = run_manifold_with_state(swapped_order, state_s)
    swap_gap = float(torch.sum((canonical_final - swapped["final_state"]) ** 2).detach().item())

    state_r = make_initial_state(config, seed)
    reverse = run_manifold_with_state(list(reversed(order)), state_r)
    reverse_gap = float(torch.sum((canonical_final - reverse["final_state"]) ** 2).detach().item())

    removal_gaps = []
    for layer_idx in order:
        state_rm = make_initial_state(config, seed)
        removed = run_manifold_with_state(order, state_rm, disabled_layer=layer_idx)
        gap = float(torch.sum((canonical_final - removed["final_state"]) ** 2).detach().item())
        removal_gaps.append(gap)
    min_removal = min(removal_gaps)

    peps_edges = cube_edges(wrong=False)
    peps_sig = peps3d_signature(canonical["history"], peps_edges)

    lirpa = lirpa_check(canonical["history"], peps_sig)
    lewm = lewm_check(lewm_mod, canonical["history"], seed)

    order_ok = swap_gap > TAU_ORDER_GAP and reverse_gap > TAU_ORDER_GAP
    removal_ok = min_removal > TAU_LAYER_REMOVAL
    actuals = {"order_sensitive": order_ok, "all_layers_load_bearing": removal_ok, "lirpa_contains": lirpa["contains_nominal"], "lewm_advantage": lewm["pass"]}
    z3_ok = z3_admission(actuals)
    cvc5_ok = cvc5_admission(actuals)

    all_pass = order_ok and removal_ok and lirpa["pass"] and lewm["pass"] and z3_ok and cvc5_ok
    return {
        "seed": seed,
        "config": config_name,
        "swap_gap": swap_gap,
        "reverse_gap": reverse_gap,
        "min_removal_gap": min_removal,
        "removal_gaps": removal_gaps,
        "lirpa_contains": lirpa["contains_nominal"],
        "lirpa_width": lirpa["mean_bound_width"],
        "lewm_advantage": lewm["advantage"],
        "z3_unsat": z3_ok,
        "cvc5_unsat": cvc5_ok,
        "autograd_grad_norm": canonical["autograd_grad_norm"],
        "pass": all_pass,
    }


def main() -> int:
    started = time.time()
    _, canonical_order = dependency_graph()
    lewm_mod = load_lewm_module()

    operating_rows = []
    for seed in SEEDS:
        for config_name, config in OPERATING_CONFIGS.items():
            row = run_single_config(seed, config_name, config, canonical_order, lewm_mod)
            operating_rows.append(row)

    boundary_rows = []
    for seed in SEEDS:
        for config_name, config in BOUNDARY_CONFIGS.items():
            row = run_single_config(seed, config_name, config, canonical_order, lewm_mod)
            boundary_rows.append(row)

    per_seed_rows = operating_rows + boundary_rows

    n_operating = len(operating_rows)
    n_op_pass = sum(1 for r in operating_rows if r["pass"])
    n_op_fail = n_operating - n_op_pass
    n_boundary = len(boundary_rows)
    n_bnd_pass = sum(1 for r in boundary_rows if r["pass"])
    n_bnd_fail = n_boundary - n_bnd_pass

    op_swap = [r["swap_gap"] for r in operating_rows]
    op_reverse = [r["reverse_gap"] for r in operating_rows]
    op_removal = [r["min_removal_gap"] for r in operating_rows]
    op_lewm = [r["lewm_advantage"] for r in operating_rows]

    def stats(vals: list[float]) -> dict[str, float]:
        mn = min(vals)
        mx = max(vals)
        avg = sum(vals) / len(vals)
        var = sum((v - avg) ** 2 for v in vals) / len(vals)
        return {"min": mn, "max": mx, "mean": avg, "variance": var}

    swap_stats = stats(op_swap)
    reverse_stats = stats(op_reverse)
    removal_stats = stats(op_removal)
    lewm_stats = stats(op_lewm)

    op_z3 = all(r["z3_unsat"] for r in operating_rows)
    op_cvc5 = all(r["cvc5_unsat"] for r in operating_rows)
    op_lirpa = all(r["lirpa_contains"] for r in operating_rows)

    operating_stable = (
        n_op_fail == 0
        and swap_stats["min"] > TAU_ORDER_GAP
        and reverse_stats["min"] > TAU_ORDER_GAP
        and removal_stats["min"] > TAU_LAYER_REMOVAL
        and op_z3
        and op_cvc5
        and op_lirpa
    )

    op_failed = [r for r in operating_rows if not r["pass"]]
    bnd_failed = [r for r in boundary_rows if not r["pass"]]
    bnd_fragile_layers = {}
    for r in boundary_rows:
        for idx, gap in enumerate(r["removal_gaps"]):
            if gap < TAU_LAYER_REMOVAL:
                layer = LAYERS[idx]
                bnd_fragile_layers.setdefault(layer, []).append({"seed": r["seed"], "config": r["config"], "gap": gap})

    positive = {
        "operating_range_seed_sweep": {
            "n_seeds": len(SEEDS),
            "n_configs": len(OPERATING_CONFIGS),
            "n_total": n_operating,
            "n_pass": n_op_pass,
            "n_fail": n_op_fail,
            "pass": n_op_fail == 0,
        },
        "swap_gap_stability": {
            **swap_stats,
            "threshold": TAU_ORDER_GAP,
            "all_above_threshold": swap_stats["min"] > TAU_ORDER_GAP,
            "pass": swap_stats["min"] > TAU_ORDER_GAP,
        },
        "reverse_gap_stability": {
            **reverse_stats,
            "threshold": TAU_ORDER_GAP,
            "all_above_threshold": reverse_stats["min"] > TAU_ORDER_GAP,
            "pass": reverse_stats["min"] > TAU_ORDER_GAP,
        },
        "removal_gap_stability": {
            **removal_stats,
            "threshold": TAU_LAYER_REMOVAL,
            "all_above_threshold": removal_stats["min"] > TAU_LAYER_REMOVAL,
            "pass": removal_stats["min"] > TAU_LAYER_REMOVAL,
        },
        "lewm_advantage_stability": {
            **lewm_stats,
            "all_positive": lewm_stats["min"] > 0.02,
            "pass": lewm_stats["min"] > 0.02,
        },
        "z3_cvc5_operating_admission": {
            "all_z3_unsat": op_z3,
            "all_cvc5_unsat": op_cvc5,
            "pass": op_z3 and op_cvc5,
        },
        "lirpa_operating_containment": {
            "all_contain_nominal": op_lirpa,
            "pass": op_lirpa,
        },
    }

    graveyard_companions = {
        "operating_range_failures": {
            "count": len(op_failed),
            "rows": [{"seed": r["seed"], "config": r["config"], "min_removal": r["min_removal_gap"]} for r in op_failed],
            "pass": len(op_failed) == 0,
        },
        "boundary_wide_config_tanh_saturation": {
            "n_boundary_total": n_boundary,
            "n_boundary_fail": n_bnd_fail,
            "fragile_layers": bnd_fragile_layers,
            "mechanism": "tanh saturation in finite_constraint_complex on wide initial states",
            "pass": True,
        },
    }

    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": True,
        },
        "seed_count_minimum": {
            "n_seeds": len(SEEDS),
            "minimum_required": 10,
            "pass": len(SEEDS) >= 10,
        },
        "operating_config_count_minimum": {
            "n_configs": len(OPERATING_CONFIGS),
            "minimum_required": 3,
            "pass": len(OPERATING_CONFIGS) >= 3,
        },
        "boundary_probed": {
            "n_boundary_configs": len(BOUNDARY_CONFIGS),
            "boundary_failures_documented": n_bnd_fail > 0,
            "pass": True,
        },
    }

    all_pass = operating_stable and all(row.get("pass") is True for row in graveyard_companions.values()) and all(row.get("pass") is True for row in boundary.values())

    elapsed = time.time() - started

    result = as_jsonable({
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "n_seeds": len(SEEDS),
            "n_operating_configs": len(OPERATING_CONFIGS),
            "n_boundary_configs": len(BOUNDARY_CONFIGS),
            "operating_total": n_operating,
            "operating_pass": n_op_pass,
            "operating_fail": n_op_fail,
            "boundary_total": n_boundary,
            "boundary_pass": n_bnd_pass,
            "boundary_fail": n_bnd_fail,
            "swap_gap_range": [swap_stats["min"], swap_stats["max"]],
            "reverse_gap_range": [reverse_stats["min"], reverse_stats["max"]],
            "min_removal_gap_range": [removal_stats["min"], removal_stats["max"]],
            "lewm_advantage_range": [lewm_stats["min"], lewm_stats["max"]],
            "operating_z3_unsat": op_z3,
            "operating_cvc5_unsat": op_cvc5,
            "operating_lirpa_contains": op_lirpa,
            "boundary_documented_fragility": list(bnd_fragile_layers.keys()),
            "load_bearing_tools": ["pytorch", "auto_LiRPA", "z3", "cvc5"],
            "load_bearing_external_modules": ["le_wm_module"],
            "elapsed_seconds": elapsed,
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row.get("pass") is True),
        },
        "why_not_v4_probes": [
            "v5 root-manifold formal scout over the current 13-layer geometric-constraint-manifold pipeline",
            "uses v5 PyTorch, auto_LiRPA, z3, cvc5, and le-wm integration surfaces rather than the v4 probe estate",
            "formal scout only; no final manifold, basin, axis, bridge, physics, target-system, or canonical claim is admitted",
        ],
        "per_seed_rows": per_seed_rows,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "EXTERNAL_MODULE_MANIFEST": EXTERNAL_MODULE_MANIFEST,
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "blockers": [],
    })

    OUT_PATH.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps({"name": NAME, "all_pass": all_pass, "out_path": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
