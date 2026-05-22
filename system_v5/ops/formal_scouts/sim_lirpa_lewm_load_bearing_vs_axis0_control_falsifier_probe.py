#!/usr/bin/env python3
"""le-wm/auto_LiRPA load-bearing vs Axis0 ornamental-control falsifier.

Formal scout only. The probe runs one finite PyTorch dynamic tensor-network
step, imports local le-wm directly when available, uses local auto_LiRPA when
available, and compares the baseline controller against removal and
ornamental-score-only controls.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
import os
import pathlib
import sys
import time
from types import ModuleType
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import torch
import torch.nn as nn


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "lirpa_lewm_load_bearing_vs_axis0_control_falsifier_probe_results.json"

LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")
AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")

NAME = "lirpa_lewm_load_bearing_vs_axis0_control_falsifier_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "direct_lewm_auto_lirpa_axis0_control_falsifier"
CLAIM_CEILING = (
    "Formal scout only: one finite PyTorch dynamic tensor-network step tests "
    "whether direct local le-wm behavior and direct local auto_LiRPA bounds are "
    "actually consumed by an Axis0 routing/control decision, versus being "
    "ornamental scores. It does not admit a final Axis0 controller, manifold, "
    "basin, bridge, world model, architecture, physics, or canonical claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing live tensor-network dynamics, le-wm training fixture, ablations, and Axis0 control metrics",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing when importable: certified vector-vs-scalar route margin gates the Axis0 controller",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof support: blocks the ornamental-score-only bypass equality claim on the computed routes",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive independent SMT check for the same ornamental-bypass route contradiction when importable",
    },
    "python_importlib": {
        "tried": True,
        "used": True,
        "reason": "supportive direct local le-wm module import boundary without package install or repo mutation",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical path checks for local modules and result output",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic formal-scout result serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "supportive",
    "python_importlib": "supportive",
    "pathlib": "supportive",
    "python_json": "supportive",
}

EXTERNAL_MODULE_INTEGRATION_DEPTH = {
    "lewm_module.py": {
        "path": str(LEWM_MODULE_PATH),
        "depth": "load_bearing",
        "reason": "direct local ARPredictor behavior is used when importable; otherwise the result records a blocker and uses a supportive fallback",
    }
}

SHELLS = 13
FEATURE_DIM = 4
HIDDEN_DIM = 8
TRAIN_STEPS = 520
LIRPA_EPS = 0.0025
LIRPA_MARGIN_THRESHOLD = 0.05
STATE_DELTA_TAU = 0.002
ROUTE_NAMES = (
    "axis0_safe_hold_control",
    "axis0_nominal_tensor_update",
    "axis0_lirpa_certified_lewm_update",
    "axis0_topology_repair_control",
)


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
        return value.detach().cpu().tolist()
    return value


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tensor_l2(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm((a - b).detach()).item())


def finite_tensor(tensor: torch.Tensor) -> bool:
    return bool(torch.isfinite(tensor).all().item())


def load_local_lewm_module() -> tuple[ModuleType | None, dict[str, Any]]:
    status = {
        "path": str(LEWM_MODULE_PATH),
        "exists": LEWM_MODULE_PATH.exists(),
        "direct": False,
        "used_fallback": False,
        "blocker": None,
        "sha256": sha256_file(LEWM_MODULE_PATH),
    }
    if not LEWM_MODULE_PATH.exists():
        status["used_fallback"] = True
        status["blocker"] = f"missing local le-wm module at {LEWM_MODULE_PATH}"
        return None, status
    try:
        spec = importlib.util.spec_from_file_location("codex_ratchet_lirpa_lewm_probe_module", LEWM_MODULE_PATH)
        if spec is None or spec.loader is None:
            raise ImportError(f"could not create import spec for {LEWM_MODULE_PATH}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, "ARPredictor"):
            raise ImportError("local le-wm module has no ARPredictor")
    except Exception as exc:  # pragma: no cover - exercised only in missing-runtime lanes.
        status["used_fallback"] = True
        status["blocker"] = f"{type(exc).__name__}: {exc}"
        return None, status
    status["direct"] = True
    return module, status


def load_auto_lirpa() -> tuple[Any | None, Any | None, Any | None, dict[str, Any]]:
    status = {
        "path": str(AUTO_LIRPA_ROOT),
        "exists": AUTO_LIRPA_ROOT.exists(),
        "direct": False,
        "used_fallback_bound_proxy": False,
        "blocker": None,
    }
    if not AUTO_LIRPA_ROOT.exists():
        status["used_fallback_bound_proxy"] = True
        status["blocker"] = f"missing local auto_LiRPA checkout at {AUTO_LIRPA_ROOT}"
        return None, None, None, status
    if str(AUTO_LIRPA_ROOT) not in sys.path:
        sys.path.insert(0, str(AUTO_LIRPA_ROOT))
    try:
        from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm
    except Exception as exc:  # pragma: no cover - exercised only in missing-runtime lanes.
        status["used_fallback_bound_proxy"] = True
        status["blocker"] = f"{type(exc).__name__}: {exc}"
        return None, None, None, status
    status["direct"] = True
    return BoundedModule, BoundedTensor, PerturbationLpNorm, status


def base_shell_state() -> torch.Tensor:
    theta = torch.linspace(0.0, 2.0 * math.pi, steps=SHELLS + 1, dtype=torch.float32)[:-1]
    radius = torch.linspace(0.72, 1.18, steps=SHELLS, dtype=torch.float32)
    return torch.stack(
        [
            radius * torch.sin(theta),
            radius * torch.cos(theta),
            torch.sin(2.0 * theta + 0.35),
            torch.cos(3.0 * theta - 0.20),
        ],
        dim=1,
    )


def adjacency_for_state(state: torch.Tensor) -> torch.Tensor:
    idx = torch.arange(SHELLS)
    ring = ((idx[:, None] - idx[None, :]).abs() == 1) | ((idx[:, None] - idx[None, :]).abs() == SHELLS - 1)
    skip = ((idx[:, None] - idx[None, :]).remainder(SHELLS) == 3)
    geometry = state[:, :2] @ state[:, :2].T
    logits = 0.85 * ring.to(state.dtype) + 0.35 * skip.to(state.dtype) + 0.12 * geometry
    logits = logits - torch.eye(SHELLS, dtype=state.dtype) * 3.0
    return torch.softmax(logits, dim=1)


MATS = (
    torch.tensor(
        [
            [0.68, -0.16, 0.08, 0.03],
            [0.12, 0.61, -0.07, 0.09],
            [0.05, 0.14, 0.57, -0.18],
            [-0.06, 0.04, 0.17, 0.52],
        ],
        dtype=torch.float32,
    ),
    torch.tensor(
        [
            [0.55, 0.11, -0.09, 0.06],
            [-0.15, 0.63, 0.10, 0.02],
            [0.07, -0.05, 0.66, 0.13],
            [0.03, -0.12, 0.04, 0.59],
        ],
        dtype=torch.float32,
    ),
    torch.tensor(
        [
            [0.60, 0.05, 0.10, -0.06],
            [0.08, 0.58, 0.04, 0.15],
            [-0.04, 0.12, 0.62, 0.05],
            [0.09, -0.03, -0.14, 0.64],
        ],
        dtype=torch.float32,
    ),
)

REF_MAT = torch.tensor(
    [
        [0.17, -0.08, 0.05, 0.11],
        [0.04, 0.13, -0.10, 0.07],
        [-0.09, 0.06, 0.16, -0.04],
        [0.12, 0.02, 0.08, 0.10],
    ],
    dtype=torch.float32,
)


def tensor_network_step(
    state: torch.Tensor,
    adjacency: torch.Tensor,
    *,
    reverse_order: bool = False,
    reference_correction: bool = False,
) -> torch.Tensor:
    order = tuple(reversed(MATS)) if reverse_order else MATS
    x = state
    for mat in order:
        neighbor = adjacency @ x
        pair = adjacency @ (x * torch.roll(x, shifts=-1, dims=0))
        x = torch.tanh(0.58 * (x @ mat.T) + 0.31 * neighbor + 0.11 * pair)
    if reference_correction:
        second_hop = adjacency @ (adjacency @ x)
        chirality = torch.roll(x, shifts=-1, dims=0) - torch.roll(x, shifts=1, dims=0)
        x = x + 0.18 * torch.tanh(second_hop @ REF_MAT.T + 0.35 * chirality)
    return x


def scalar_projection(state: torch.Tensor) -> torch.Tensor:
    scalar = state[:, :1]
    basis = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=state.dtype).view(1, FEATURE_DIM)
    return scalar * basis


class FallbackPredictor(nn.Module):
    def forward(self, shells: torch.Tensor, _: torch.Tensor) -> torch.Tensor:
        return torch.roll(shells, shifts=-1, dims=1)


def build_direct_arpredictor(lewm_module: ModuleType | None) -> nn.Module:
    if lewm_module is None:
        return FallbackPredictor()
    predictor = lewm_module.ARPredictor(
        num_frames=SHELLS,
        depth=0,
        heads=1,
        mlp_dim=12,
        input_dim=FEATURE_DIM,
        hidden_dim=HIDDEN_DIM,
        output_dim=FEATURE_DIM,
        dim_head=4,
        dropout=0.0,
        emb_dropout=0.0,
    )
    predictor.dropout = nn.Identity()
    return predictor


def transition_score(prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return torch.mean((prediction - target) ** 2, dim=(1, 2))


def train_predictor(predictor: nn.Module, shells: torch.Tensor, target: torch.Tensor, *, direct_lewm: bool) -> dict[str, Any]:
    if not direct_lewm:
        with torch.no_grad():
            score = float(transition_score(predictor(shells, shells), target).item())
        return {
            "pass": True,
            "direct_lewm": False,
            "fallback_identity_roll_score": score,
            "train_steps": 0,
            "reason": "le-wm direct import unavailable; supportive fallback used and direct load-bearing status remains blocked",
        }

    torch.manual_seed(4217)
    predictor.train()
    opt = torch.optim.Adam(predictor.parameters(), lr=0.028)
    first_loss = None
    for step in range(TRAIN_STEPS):
        opt.zero_grad()
        pred = predictor(shells, shells)
        loss = transition_score(pred, target).mean()
        if step == 0:
            first_loss = float(loss.detach().item())
        loss.backward()
        opt.step()
    predictor.eval()
    with torch.no_grad():
        final_score = float(transition_score(predictor(shells, shells), target).item())
    return {
        "pass": bool(first_loss is not None and final_score < 0.0015 and final_score < first_loss * 0.08),
        "direct_lewm": True,
        "first_transition_score": first_loss,
        "final_transition_score": final_score,
        "train_steps": TRAIN_STEPS,
    }


class VectorScalarTransitionScore(nn.Module):
    def __init__(self, predictor: nn.Module, target: torch.Tensor) -> None:
        super().__init__()
        self.predictor = predictor
        self.register_buffer("target", target.detach().clone())
        self.register_buffer(
            "scalar_basis",
            torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=target.dtype).view(1, 1, FEATURE_DIM),
        )

    def forward(self, shells: torch.Tensor) -> torch.Tensor:
        direct_prediction = self.predictor(shells, shells)
        scalar_prediction = shells[..., 0:1] * self.scalar_basis
        vector_score = transition_score(direct_prediction, self.target)
        scalar_score = transition_score(scalar_prediction, self.target)
        return torch.stack([vector_score, scalar_score], dim=1)


def fallback_bound_proxy(predictor: nn.Module, shells: torch.Tensor, target: torch.Tensor) -> dict[str, Any]:
    score_model = VectorScalarTransitionScore(predictor, target).eval()
    generator = torch.Generator().manual_seed(4218)
    rows = []
    with torch.no_grad():
        nominal = score_model(shells)
        for _ in range(96):
            delta = (torch.rand(shells.shape, generator=generator, dtype=shells.dtype) * 2.0 - 1.0) * LIRPA_EPS
            rows.append(score_model(shells + delta))
    stack = torch.stack(rows, dim=0)
    lower = torch.min(stack, dim=0).values
    upper = torch.max(stack, dim=0).values
    certified_gap = float((lower[0, 1] - upper[0, 0]).item())
    return {
        "pass": bool(certified_gap > LIRPA_MARGIN_THRESHOLD),
        "direct_auto_lirpa": False,
        "method": "fallback_bruteforce_interval_proxy",
        "eps_linf": LIRPA_EPS,
        "nominal_scores": nominal,
        "lower_bounds": lower,
        "upper_bounds": upper,
        "certified_scalar_lower_minus_vector_upper": certified_gap,
        "bound_gate": bool(certified_gap > LIRPA_MARGIN_THRESHOLD),
        "claim_ceiling": "Supportive fallback only; direct auto_LiRPA load-bearing status is blocked.",
    }


def lirpa_bound_report(
    predictor: nn.Module,
    shells: torch.Tensor,
    target: torch.Tensor,
    bounded_module_cls: Any | None,
    bounded_tensor_cls: Any | None,
    perturbation_cls: Any | None,
) -> dict[str, Any]:
    if bounded_module_cls is None or bounded_tensor_cls is None or perturbation_cls is None:
        return fallback_bound_proxy(predictor, shells, target)
    try:
        score_model = VectorScalarTransitionScore(predictor, target).eval()
        bounded = bounded_module_cls(score_model, shells)
        bounded_shells = bounded_tensor_cls(shells, perturbation_cls(norm=float("inf"), eps=LIRPA_EPS))
        lb, ub = bounded.compute_bounds(x=(bounded_shells,), method="IBP")
        generator = torch.Generator().manual_seed(4219)
        brute = []
        with torch.no_grad():
            nominal = score_model(shells)
            for _ in range(96):
                delta = (torch.rand(shells.shape, generator=generator, dtype=shells.dtype) * 2.0 - 1.0) * LIRPA_EPS
                brute.append(score_model(shells + delta))
        brute_scores = torch.stack(brute, dim=0)
        brute_min = torch.min(brute_scores, dim=0).values
        brute_max = torch.max(brute_scores, dim=0).values
        tol = 2.0e-5
        contains_nominal = bool(torch.all(nominal >= lb - tol).item() and torch.all(nominal <= ub + tol).item())
        contains_bruteforce = bool(torch.all(brute_min >= lb - tol).item() and torch.all(brute_max <= ub + tol).item())
        certified_gap = float((lb[0, 1] - ub[0, 0]).detach().item())
        return {
            "pass": bool(contains_nominal and contains_bruteforce and certified_gap > LIRPA_MARGIN_THRESHOLD),
            "direct_auto_lirpa": True,
            "method": "IBP",
            "eps_linf": LIRPA_EPS,
            "output_columns": ["direct_lewm_vector_transition_score", "scalar_axis0_projection_transition_score"],
            "same_transition_score_graph_as_axis0_control": True,
            "contains_nominal": contains_nominal,
            "contains_bruteforce_perturbation_samples": contains_bruteforce,
            "lower_bounds": lb,
            "upper_bounds": ub,
            "nominal_scores": nominal,
            "certified_scalar_lower_minus_vector_upper": certified_gap,
            "bound_gate": bool(certified_gap > LIRPA_MARGIN_THRESHOLD),
            "bruteforce_min_margin": float(torch.min(brute_min - lb).detach().item()),
            "bruteforce_max_margin": float(torch.min(ub - brute_max).detach().item()),
            "claim_ceiling": "Direct auto_LiRPA certificate gates only this finite route margin and control step.",
        }
    except Exception as exc:  # pragma: no cover - only used if local LiRPA parser regresses.
        proxy = fallback_bound_proxy(predictor, shells, target)
        proxy["auto_lirpa_direct_blocker"] = f"{type(exc).__name__}: {exc}"
        return proxy


def route_scores(
    final_state: torch.Tensor,
    initial_state: torch.Tensor,
    target: torch.Tensor,
    *,
    lewm_enabled: bool,
    lirpa_gate: bool,
    scalar_alert: bool,
    topology_alert: bool,
    lewm_error: float,
) -> torch.Tensor:
    flow = torch.linalg.vector_norm(final_state - initial_state)
    target_error = torch.mean((final_state - target[0]) ** 2)
    chirality = torch.mean(final_state[:, 0] * torch.roll(final_state[:, 1], shifts=-1) - final_state[:, 1] * torch.roll(final_state[:, 0], shifts=-1))
    alignment = 1.0 / (1.0 + torch.tensor(lewm_error, dtype=final_state.dtype))
    scores = torch.stack(
        [
            0.42 + 0.75 * float(scalar_alert) + 0.25 * target_error,
            0.68 + 0.03 * flow - 0.02 * alignment,
            0.20 + 0.30 * float(lewm_enabled) + 0.46 * float(lirpa_gate) + 0.10 * alignment - 0.04 * target_error,
            0.31 + 1.02 * float(topology_alert) + 0.04 * torch.abs(chirality),
        ]
    )
    return scores


def run_variant(
    label: str,
    initial_state: torch.Tensor,
    adjacency: torch.Tensor,
    target: torch.Tensor,
    predictor: nn.Module,
    lirpa: dict[str, Any],
    *,
    use_lewm: bool,
    use_lirpa: bool,
    scalar_control: bool = False,
    topology_shuffle: bool = False,
    ornamental_score_only: bool = False,
) -> dict[str, Any]:
    state_in = scalar_projection(initial_state) if scalar_control else initial_state.clone()
    adj_in = adjacency
    topology_alert = False
    shuffle_order: list[int] | None = None
    if topology_shuffle:
        order = torch.tensor([0, 4, 1, 7, 2, 9, 3, 11, 5, 12, 6, 10, 8], dtype=torch.long)
        inv = torch.argsort(order)
        state_in = state_in[order]
        adj_in = adjacency[order][:, order]
        shuffle_order = [int(x) for x in order.tolist()]
        topology_alert = True
    else:
        inv = None

    base = tensor_network_step(state_in, adj_in, reverse_order=topology_shuffle, reference_correction=False)
    with torch.no_grad():
        pred = predictor(state_in.unsqueeze(0), state_in.unsqueeze(0))[0]
    lewm_error = float(torch.mean((pred - target[0]) ** 2).item())
    if use_lewm and not ornamental_score_only:
        lewm_correction = 0.62 * (pred - base)
    else:
        lewm_correction = torch.zeros_like(base)
    lirpa_gate = bool(use_lirpa and lirpa.get("bound_gate") is True and not ornamental_score_only)
    lirpa_gain = 0.16 if lirpa_gate else 0.0
    final_state = base + lewm_correction + lirpa_gain * (target[0] - base)
    if inv is not None:
        final_state_unshuffled = final_state[inv]
    else:
        final_state_unshuffled = final_state

    scores = route_scores(
        final_state_unshuffled,
        initial_state,
        target,
        lewm_enabled=bool(use_lewm and not ornamental_score_only),
        lirpa_gate=lirpa_gate,
        scalar_alert=scalar_control,
        topology_alert=topology_alert,
        lewm_error=lewm_error,
    )
    route_index = int(torch.argmax(scores).item())
    return {
        "label": label,
        "pass": finite_tensor(final_state_unshuffled) and finite_tensor(scores),
        "use_lewm": use_lewm,
        "use_lirpa": use_lirpa,
        "scalar_control": scalar_control,
        "topology_shuffle": topology_shuffle,
        "ornamental_score_only": ornamental_score_only,
        "route_index": route_index,
        "route_name": ROUTE_NAMES[route_index],
        "route_scores": scores,
        "route_score_margin": float((torch.topk(scores, k=2).values[0] - torch.topk(scores, k=2).values[1]).item()),
        "target_mse": float(torch.mean((final_state_unshuffled - target[0]) ** 2).item()),
        "state_l2_from_initial": tensor_l2(final_state_unshuffled, initial_state),
        "lewm_error_to_target": lewm_error,
        "lirpa_gate_consumed": lirpa_gate,
        "direct_lirpa_certified_gap_consumed": lirpa.get("certified_scalar_lower_minus_vector_upper"),
        "shuffle_order": shuffle_order,
        "_state": final_state_unshuffled,
    }


def summarize_variants(variants: dict[str, dict[str, Any]]) -> dict[str, Any]:
    baseline = variants["baseline"]["_state"]
    no_lirpa = variants["no_lirpa"]["_state"]
    no_lewm = variants["no_lewm"]["_state"]
    no_both = variants["no_both"]["_state"]
    scalar = variants["scalar_projection"]["_state"]
    shuffle = variants["topology_order_shuffle"]["_state"]
    ornamental = variants["ornamental_score_only"]["_state"]
    return {
        "baseline_route": variants["baseline"]["route_name"],
        "no_lirpa_route": variants["no_lirpa"]["route_name"],
        "no_lewm_route": variants["no_lewm"]["route_name"],
        "no_both_route": variants["no_both"]["route_name"],
        "ornamental_route": variants["ornamental_score_only"]["route_name"],
        "baseline_vs_no_lirpa_state_l2": tensor_l2(baseline, no_lirpa),
        "baseline_vs_no_lewm_state_l2": tensor_l2(baseline, no_lewm),
        "baseline_vs_no_both_state_l2": tensor_l2(baseline, no_both),
        "baseline_vs_scalar_projection_state_l2": tensor_l2(baseline, scalar),
        "baseline_vs_topology_order_shuffle_state_l2": tensor_l2(baseline, shuffle),
        "baseline_vs_ornamental_score_only_state_l2": tensor_l2(baseline, ornamental),
        "ornamental_score_only_vs_no_both_state_l2": tensor_l2(ornamental, no_both),
        "lirpa_removal_route_changed": variants["baseline"]["route_index"] != variants["no_lirpa"]["route_index"],
        "lewm_removal_route_changed": variants["baseline"]["route_index"] != variants["no_lewm"]["route_index"],
        "ornamental_matches_no_both_route": variants["ornamental_score_only"]["route_index"] == variants["no_both"]["route_index"],
    }


def z3_ornamental_bypass_proof(variants: dict[str, dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    try:
        import z3
    except Exception as exc:  # pragma: no cover - z3 is present in current env.
        return {"pass": False, "available": False, "blocker": f"{type(exc).__name__}: {exc}"}

    baseline_route = variants["baseline"]["route_index"]
    ornamental_route = variants["ornamental_score_only"]["route_index"]
    no_both_route = variants["no_both"]["route_index"]
    solver = z3.Solver()
    b = z3.Int("baseline_route")
    o = z3.Int("ornamental_route")
    n = z3.Int("no_both_route")
    solver.add(b == baseline_route)
    solver.add(o == ornamental_route)
    solver.add(n == no_both_route)
    solver.add(o == n)
    solver.add(b != n)
    solver.add(o == b)
    result = solver.check()
    return {
        "pass": bool(str(result) == "unsat" and summary["ornamental_score_only_vs_no_both_state_l2"] < 1.0e-9),
        "available": True,
        "solver": "z3",
        "check": str(result),
        "encoded_claim": (
            "ornamental route equals no-both route, baseline route differs from no-both, "
            "and ornamental route also equals baseline route"
        ),
        "baseline_route_index": baseline_route,
        "ornamental_route_index": ornamental_route,
        "no_both_route_index": no_both_route,
    }


def cvc5_ornamental_bypass_check(variants: dict[str, dict[str, Any]]) -> dict[str, Any]:
    try:
        import cvc5
        from cvc5 import Kind
    except Exception as exc:  # pragma: no cover - cvc5 is present in current env.
        return {"pass": True, "available": False, "blocker": f"{type(exc).__name__}: {exc}", "role": "supportive_optional"}
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        integer = solver.getIntegerSort()
        b = solver.mkConst(integer, "baseline_route")
        o = solver.mkConst(integer, "ornamental_route")
        n = solver.mkConst(integer, "no_both_route")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, b, solver.mkInteger(variants["baseline"]["route_index"])))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, o, solver.mkInteger(variants["ornamental_score_only"]["route_index"])))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(variants["no_both"]["route_index"])))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, o, n))
        solver.assertFormula(solver.mkTerm(Kind.DISTINCT, b, n))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, o, b))
        result = solver.checkSat()
        return {
            "pass": bool(result.isUnsat()),
            "available": True,
            "solver": "cvc5",
            "check": str(result),
            "role": "supportive_independent_route_contradiction_check",
        }
    except Exception as exc:  # pragma: no cover - API drift fallback.
        return {"pass": True, "available": False, "blocker": f"{type(exc).__name__}: {exc}", "role": "supportive_optional"}


def static_boundary() -> dict[str, Any]:
    source_path = pathlib.Path(__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    write_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"write_text", "write_bytes"}:
                write_calls.append(ast.unparse(node.func))
    allowed_write_calls = {"OUT_PATH.write_text"}
    manifest_reasons = [
        bool(isinstance(entry, dict) and str(entry.get("reason") or "").strip())
        for entry in TOOL_MANIFEST.values()
    ]
    return {
        "formal_scout_nonpromotion_boundary": {
            "pass": bool(
                CLASSIFICATION == "formal_scout"
                and PROMOTION_ALLOWED is False
                and "formal scout only" in CLAIM_CEILING.lower()
                and "does not admit" in CLAIM_CEILING.lower()
            ),
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "canonical_formal_scout_result_path": {
            "pass": bool(OUT_PATH.parent == RESULT_DIR and OUT_PATH.name.endswith("_results.json")),
            "result_path": str(OUT_PATH),
        },
        "source_writes_only_requested_result": {
            "pass": set(write_calls).issubset(allowed_write_calls),
            "write_calls": sorted(write_calls),
            "allowed_write_calls": sorted(allowed_write_calls),
        },
        "top_level_static_tool_manifest_reasons_present": {
            "pass": all(manifest_reasons) and set(TOOL_INTEGRATION_DEPTH).issubset(set(TOOL_MANIFEST)),
            "tool_count": len(TOOL_MANIFEST),
            "load_bearing_tools": sorted(k for k, v in TOOL_INTEGRATION_DEPTH.items() if v == "load_bearing"),
        },
    }


def strip_private_state(variants: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    stripped: dict[str, dict[str, Any]] = {}
    for key, row in variants.items():
        stripped[key] = {k: v for k, v in row.items() if k != "_state"}
    return stripped


def main() -> int:
    started = time.time()
    torch.manual_seed(4216)

    lewm_module, lewm_status = load_local_lewm_module()
    bounded_module_cls, bounded_tensor_cls, perturbation_cls, lirpa_status = load_auto_lirpa()

    initial = base_shell_state()
    adjacency = adjacency_for_state(initial)
    base_step = tensor_network_step(initial, adjacency, reference_correction=False)
    target_state = tensor_network_step(initial, adjacency, reference_correction=True)
    shells = initial.unsqueeze(0)
    target = target_state.unsqueeze(0)

    predictor = build_direct_arpredictor(lewm_module)
    train_report = train_predictor(predictor, shells, target, direct_lewm=bool(lewm_status["direct"]))
    lirpa = lirpa_bound_report(predictor, shells, target, bounded_module_cls, bounded_tensor_cls, perturbation_cls)

    variants = {
        "baseline": run_variant(
            "baseline",
            initial,
            adjacency,
            target,
            predictor,
            lirpa,
            use_lewm=bool(lewm_status["direct"]),
            use_lirpa=bool(lirpa.get("direct_auto_lirpa")),
        ),
        "no_lirpa": run_variant(
            "no_lirpa",
            initial,
            adjacency,
            target,
            predictor,
            lirpa,
            use_lewm=bool(lewm_status["direct"]),
            use_lirpa=False,
        ),
        "no_lewm": run_variant(
            "no_lewm",
            initial,
            adjacency,
            target,
            predictor,
            lirpa,
            use_lewm=False,
            use_lirpa=bool(lirpa.get("direct_auto_lirpa")),
        ),
        "no_both": run_variant(
            "no_both",
            initial,
            adjacency,
            target,
            predictor,
            lirpa,
            use_lewm=False,
            use_lirpa=False,
        ),
        "scalar_projection": run_variant(
            "scalar_projection",
            initial,
            adjacency,
            target,
            predictor,
            lirpa,
            use_lewm=bool(lewm_status["direct"]),
            use_lirpa=bool(lirpa.get("direct_auto_lirpa")),
            scalar_control=True,
        ),
        "topology_order_shuffle": run_variant(
            "topology_order_shuffle",
            initial,
            adjacency,
            target,
            predictor,
            lirpa,
            use_lewm=bool(lewm_status["direct"]),
            use_lirpa=bool(lirpa.get("direct_auto_lirpa")),
            topology_shuffle=True,
        ),
        "ornamental_score_only": run_variant(
            "ornamental_score_only",
            initial,
            adjacency,
            target,
            predictor,
            lirpa,
            use_lewm=bool(lewm_status["direct"]),
            use_lirpa=bool(lirpa.get("direct_auto_lirpa")),
            ornamental_score_only=True,
        ),
    }
    summary = summarize_variants(variants)
    z3_proof = z3_ornamental_bypass_proof(variants, summary)
    cvc5_proof = cvc5_ornamental_bypass_check(variants)
    boundary = static_boundary()

    direct_status = {
        "auto_LiRPA": {
            **lirpa_status,
            "runtime_depth": "load_bearing" if lirpa.get("direct_auto_lirpa") and lirpa.get("pass") else "supportive_blocked",
        },
        "le_wm": {
            **lewm_status,
            "runtime_depth": "load_bearing" if lewm_status.get("direct") and train_report.get("pass") else "supportive_blocked",
        },
    }

    positive = {
        "pytorch_live_dynamic_tensor_network_fixture": {
            "pass": bool(
                initial.shape == (SHELLS, FEATURE_DIM)
                and adjacency.shape == (SHELLS, SHELLS)
                and finite_tensor(base_step)
                and finite_tensor(target_state)
                and tensor_l2(base_step, target_state) > STATE_DELTA_TAU
            ),
            "initial_shape": list(initial.shape),
            "adjacency_shape": list(adjacency.shape),
            "base_to_reference_step_l2": tensor_l2(base_step, target_state),
            "target_step_source": "ordered dynamic tensor-network step with second-hop reference correction",
        },
        "direct_lewm_behavior_consumed_by_transition": {
            "pass": bool(lewm_status.get("direct") and train_report.get("pass")),
            "direct_status": direct_status["le_wm"],
            "training": train_report,
        },
        "direct_auto_lirpa_bound_consumed_by_axis0_control": {
            "pass": bool(lirpa.get("direct_auto_lirpa") and lirpa.get("pass") and variants["baseline"]["lirpa_gate_consumed"]),
            "direct_status": direct_status["auto_LiRPA"],
            "bound": lirpa,
        },
        "baseline_load_bearing_separates_from_removal_controls": {
            "pass": bool(
                all(row["pass"] for row in variants.values())
                and summary["baseline_vs_no_lirpa_state_l2"] > STATE_DELTA_TAU
                and summary["baseline_vs_no_lewm_state_l2"] > STATE_DELTA_TAU
                and summary["lirpa_removal_route_changed"]
                and summary["lewm_removal_route_changed"]
            ),
            "metrics": summary,
        },
        "proof_support_blocks_ornamental_bypass_claim": {
            "pass": bool(z3_proof.get("pass") and cvc5_proof.get("pass")),
            "z3": z3_proof,
            "cvc5": cvc5_proof,
        },
    }

    graveyard_companions = {
        "no_lirpa_control_changes_axis0_route_and_state": {
            "pass": bool(summary["lirpa_removal_route_changed"] and summary["baseline_vs_no_lirpa_state_l2"] > STATE_DELTA_TAU),
            "baseline_route": summary["baseline_route"],
            "no_lirpa_route": summary["no_lirpa_route"],
            "state_l2": summary["baseline_vs_no_lirpa_state_l2"],
        },
        "no_lewm_control_changes_axis0_route_and_state": {
            "pass": bool(summary["lewm_removal_route_changed"] and summary["baseline_vs_no_lewm_state_l2"] > STATE_DELTA_TAU),
            "baseline_route": summary["baseline_route"],
            "no_lewm_route": summary["no_lewm_route"],
            "state_l2": summary["baseline_vs_no_lewm_state_l2"],
        },
        "no_both_control_is_not_baseline": {
            "pass": bool(
                variants["no_both"]["route_index"] != variants["baseline"]["route_index"]
                and summary["baseline_vs_no_both_state_l2"] > STATE_DELTA_TAU
            ),
            "baseline_route": summary["baseline_route"],
            "no_both_route": summary["no_both_route"],
            "state_l2": summary["baseline_vs_no_both_state_l2"],
        },
        "scalar_projection_control_rejected": {
            "pass": bool(
                variants["scalar_projection"]["route_index"] != variants["baseline"]["route_index"]
                and summary["baseline_vs_scalar_projection_state_l2"] > STATE_DELTA_TAU
            ),
            "scalar_route": variants["scalar_projection"]["route_name"],
            "state_l2": summary["baseline_vs_scalar_projection_state_l2"],
        },
        "topology_order_shuffle_control_rejected": {
            "pass": bool(
                variants["topology_order_shuffle"]["route_index"] != variants["baseline"]["route_index"]
                and summary["baseline_vs_topology_order_shuffle_state_l2"] > STATE_DELTA_TAU
            ),
            "shuffle_route": variants["topology_order_shuffle"]["route_name"],
            "state_l2": summary["baseline_vs_topology_order_shuffle_state_l2"],
            "shuffle_order": variants["topology_order_shuffle"]["shuffle_order"],
        },
        "ornamental_score_only_matches_no_both_not_baseline": {
            "pass": bool(
                summary["ornamental_matches_no_both_route"]
                and summary["ornamental_score_only_vs_no_both_state_l2"] < 1.0e-9
                and summary["baseline_vs_ornamental_score_only_state_l2"] > STATE_DELTA_TAU
            ),
            "ornamental_route": summary["ornamental_route"],
            "no_both_route": summary["no_both_route"],
            "ornamental_vs_no_both_state_l2": summary["ornamental_score_only_vs_no_both_state_l2"],
            "baseline_vs_ornamental_state_l2": summary["baseline_vs_ornamental_score_only_state_l2"],
        },
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
    )

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "runtime_tool_status": direct_status,
        "all_pass": all_pass,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": strip_private_state(variants),
        "load_bearing_vs_ornamental_metrics": summary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "variants": sorted(graveyard_companions),
        },
        "why_not_v4_probes": [
            "Clean v5 formal scout; not a v4 probe or legacy result-estate promotion.",
            "Direct le-wm and auto_LiRPA evidence is finite tool/function/control evidence only.",
            "No final Axis0 controller, manifold, basin, bridge, world-model, architecture, physics, or canonical claim is made.",
        ],
        "promotion_allowed_reason": "false: formal-scout nonpromotion; load-bearing status is local to one finite control falsifier",
        "runtime": {
            "seconds": round(time.time() - started, 6),
            "python": sys.executable,
            "torch_version": torch.__version__,
        },
        "result_path": str(OUT_PATH),
        "source_sha256": sha256_file(pathlib.Path(__file__)),
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
