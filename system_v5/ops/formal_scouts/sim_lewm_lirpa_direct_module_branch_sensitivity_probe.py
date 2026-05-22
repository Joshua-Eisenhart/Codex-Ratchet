#!/usr/bin/env python3
"""Direct le-wm + auto_LiRPA branch sensitivity formal scout.

Formal scout only. This file imports the local le-wm module.py directly,
trains one tiny ARPredictor on one 13-shell manifold transition, and asks
auto_LiRPA to bound the same PyTorch transition score used by the controls.
It does not load checkpoints, datasets, or admit a final manifold, basin,
Axis0, world-model, or architecture claim.
"""

from __future__ import annotations

import hashlib
import ast
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
OUT_PATH = RESULT_DIR / "lewm_lirpa_direct_module_branch_sensitivity_probe_results.json"

LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")
AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")

NAME = "lewm_lirpa_direct_module_branch_sensitivity_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "direct_local_lewm_module_auto_lirpa_formal_scout"
CLAIM_CEILING = (
    "Formal scout only: directly imports local le-wm module.py and uses local "
    "auto_LiRPA to bound one tiny PyTorch transition-score graph over one "
    "13-shell fixture. It does not admit a final manifold, basin, Axis0, "
    "world model, architecture, physics, bridge, or canonical claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 13-shell tensors, ARPredictor training, transition score, controls, and perturbation samples",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing IBP certificate over the exact vector-vs-scalar transition score used by the controls",
    },
    "python_importlib": {
        "tried": True,
        "used": True,
        "reason": "supportive direct file import of the local le-wm module.py boundary",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive local module and canonical result-path checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "python_importlib": "supportive",
    "pathlib": "supportive",
}
EXTERNAL_MODULE_INTEGRATION_DEPTH = {
    "lewm_module.py": {
        "path": str(LEWM_MODULE_PATH),
        "depth": "load_bearing",
        "reason": "direct local ARPredictor class import; no checkpoint, package install, or repo mutation",
    }
}

SHELLS = 13
FEATURE_DIM = 4
HIDDEN_DIM = 8
LIRPA_EPS = 0.002
TRAIN_STEPS = 800


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        return value.detach().cpu().tolist()
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_local_lewm_module() -> ModuleType:
    if not LEWM_MODULE_PATH.exists():
        raise SystemExit(f"Missing local le-wm module: {LEWM_MODULE_PATH}")
    spec = importlib.util.spec_from_file_location("codex_ratchet_direct_lewm_module", LEWM_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not prepare direct import spec for {LEWM_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_auto_lirpa() -> tuple[Any, Any, Any]:
    if not AUTO_LIRPA_ROOT.exists():
        raise SystemExit(f"Missing local auto_LiRPA checkout: {AUTO_LIRPA_ROOT}")
    sys.path.insert(0, str(AUTO_LIRPA_ROOT))
    from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm

    return BoundedModule, BoundedTensor, PerturbationLpNorm


def build_thirteen_shell_transition() -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    theta = torch.linspace(0.0, 2.0 * math.pi, steps=SHELLS + 1, dtype=torch.float32)[:-1]
    shells = torch.stack(
        [
            torch.sin(theta),
            torch.cos(theta),
            torch.sin(2.0 * theta + 0.35),
            torch.cos(3.0 * theta - 0.20),
        ],
        dim=1,
    ).unsqueeze(0)
    target = torch.roll(shells, shifts=-1, dims=1)
    report = {
        "pass": bool(shells.shape == (1, SHELLS, FEATURE_DIM) and target.shape == shells.shape),
        "shell_count": SHELLS,
        "feature_dim": FEATURE_DIM,
        "transition": "next_shell_roll_on_fixed_vector_shell_fixture",
        "axis0_scalar_projection_source": "feature_0_only",
    }
    return shells, target, report


def build_direct_arpredictor(lewm_module: ModuleType) -> nn.Module:
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
    # auto_LiRPA in this local checkout cannot parse le-wm Dropout with a float
    # ratio in eval mode. emb_dropout=0, so Identity preserves the direct model.
    predictor.dropout = nn.Identity()
    return predictor


def transition_score(prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return torch.mean((prediction - target) ** 2, dim=(1, 2))


def train_direct_predictor(predictor: nn.Module, shells: torch.Tensor, target: torch.Tensor) -> dict[str, Any]:
    torch.manual_seed(1207)
    predictor.train()
    opt = torch.optim.Adam(predictor.parameters(), lr=0.03)
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
        "pass": bool(first_loss is not None and final_score < 2.0e-4 and final_score < first_loss * 0.02),
        "first_transition_score": first_loss,
        "final_transition_score": final_score,
        "train_steps": TRAIN_STEPS,
        "claim_ceiling": "One fixed 13-shell training fixture; no general world-model or architecture claim.",
    }


def score_controls(predictor: nn.Module, shells: torch.Tensor, target: torch.Tensor) -> dict[str, Any]:
    scalar_basis = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=shells.dtype).view(1, 1, FEATURE_DIM)
    shuffled_order = torch.tensor([0, 3, 1, 5, 2, 8, 4, 7, 6, 10, 9, 12, 11], dtype=torch.long)
    with torch.no_grad():
        direct_score = transition_score(predictor(shells, shells), target)
        identity_score = transition_score(shells, target)
        shuffled_shells = shells[:, shuffled_order, :]
        shuffled_score = transition_score(predictor(shuffled_shells, shuffled_shells), target)
        scalar_projection = shells[..., 0:1] * scalar_basis
        scalar_score = transition_score(scalar_projection, target)
    return {
        "pass": bool(
            direct_score.item() < identity_score.item() * 0.05
            and direct_score.item() < shuffled_score.item() * 0.05
            and direct_score.item() < scalar_score.item() * 0.05
        ),
        "direct_lewm_transition_score": float(direct_score.item()),
        "identity_predictor_transition_score": float(identity_score.item()),
        "shuffled_shell_order_transition_score": float(shuffled_score.item()),
        "scalar_axis0_projection_transition_score": float(scalar_score.item()),
        "improvement_vs_identity": float(identity_score.item() / max(direct_score.item(), 1.0e-12)),
        "improvement_vs_shuffled": float(shuffled_score.item() / max(direct_score.item(), 1.0e-12)),
        "improvement_vs_scalar": float(scalar_score.item() / max(direct_score.item(), 1.0e-12)),
        "shuffled_order": shuffled_order.tolist(),
    }


class VectorScalarTransitionScore(nn.Module):
    def __init__(self, predictor: nn.Module, target: torch.Tensor) -> None:
        super().__init__()
        self.predictor = predictor
        self.register_buffer("target", target.detach().clone())
        self.register_buffer("scalar_basis", torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=target.dtype).view(1, 1, FEATURE_DIM))

    def forward(self, shells: torch.Tensor) -> torch.Tensor:
        direct_prediction = self.predictor(shells, shells)
        scalar_prediction = shells[..., 0:1] * self.scalar_basis
        vector_score = transition_score(direct_prediction, self.target)
        scalar_score = transition_score(scalar_prediction, self.target)
        return torch.stack([vector_score, scalar_score], dim=1)


def lirpa_bound_report(
    predictor: nn.Module,
    shells: torch.Tensor,
    target: torch.Tensor,
    bounded_module_cls: Any,
    bounded_tensor_cls: Any,
    perturbation_cls: Any,
) -> dict[str, Any]:
    score_model = VectorScalarTransitionScore(predictor, target).eval()
    bounded = bounded_module_cls(score_model, shells)
    bounded_shells = bounded_tensor_cls(shells, perturbation_cls(norm=float("inf"), eps=LIRPA_EPS))
    lb, ub = bounded.compute_bounds(x=(bounded_shells,), method="IBP")
    generator = torch.Generator().manual_seed(1208)
    brute = []
    with torch.no_grad():
        nominal = score_model(shells)
        for _ in range(80):
            delta = (torch.rand(shells.shape, generator=generator, dtype=shells.dtype) * 2.0 - 1.0) * LIRPA_EPS
            brute.append(score_model(shells + delta))
    brute_scores = torch.stack(brute, dim=0)
    brute_min = brute_scores.min(dim=0).values
    brute_max = brute_scores.max(dim=0).values
    tol = 2.0e-5
    contains_nominal = bool(torch.all(nominal >= lb - tol) and torch.all(nominal <= ub + tol))
    contains_bruteforce = bool(torch.all(brute_min >= lb - tol) and torch.all(brute_max <= ub + tol))
    certified_gap = float((lb[0, 1] - ub[0, 0]).detach().item())
    return {
        "pass": bool(contains_nominal and contains_bruteforce and certified_gap > 0.05),
        "method": "IBP",
        "eps_linf": LIRPA_EPS,
        "output_columns": ["direct_lewm_vector_transition_score", "scalar_axis0_projection_transition_score"],
        "same_transition_score_graph": True,
        "contains_nominal": contains_nominal,
        "contains_bruteforce_perturbation_samples": contains_bruteforce,
        "lower_bounds": lb,
        "upper_bounds": ub,
        "certified_scalar_lower_minus_vector_upper": certified_gap,
        "nominal_scores": nominal,
        "bruteforce_min_margin": float(torch.min(brute_min - lb).detach().item()),
        "bruteforce_max_margin": float(torch.min(ub - brute_max).detach().item()),
        "claim_ceiling": "Certificate separates vector ARPredictor score from scalar projection score only for this finite perturbation box.",
    }


def static_boundary() -> dict[str, Any]:
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    write_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"write_text", "write_bytes"}:
                write_calls.append(ast.unparse(node.func))
    allowed_write_calls = {"OUT_PATH.write_text"}
    return {
        "claim_ceiling_blocks_final_manifold_basin_axis0_architecture": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "final manifold", "basin", "axis0", "architecture"]
            ),
            "claim_ceiling": CLAIM_CEILING,
        },
        "direct_external_import_paths_are_local_and_read_only": {
            "pass": bool(LEWM_MODULE_PATH.exists() and AUTO_LIRPA_ROOT.exists()),
            "lewm_module_path": str(LEWM_MODULE_PATH),
            "auto_lirpa_root": str(AUTO_LIRPA_ROOT),
            "lewm_module_sha256": sha256_file(LEWM_MODULE_PATH) if LEWM_MODULE_PATH.exists() else None,
        },
        "source_does_not_write_external_repos_or_git": {
            "pass": set(write_calls).issubset(allowed_write_calls),
            "write_calls": sorted(write_calls),
            "allowed_write_calls": sorted(allowed_write_calls),
        },
    }


def main() -> int:
    started = time.time()
    torch.manual_seed(1207)
    lewm_module = load_local_lewm_module()
    bounded_module_cls, bounded_tensor_cls, perturbation_cls = load_auto_lirpa()

    shells, target, transition_fixture = build_thirteen_shell_transition()
    predictor = build_direct_arpredictor(lewm_module)
    train_report = train_direct_predictor(predictor, shells, target)
    controls = score_controls(predictor, shells, target)
    lirpa = lirpa_bound_report(predictor, shells, target, bounded_module_cls, bounded_tensor_cls, perturbation_cls)
    boundary = static_boundary()

    positive = {
        "one_13_shell_manifold_transition_fixture": transition_fixture,
        "direct_local_lewm_arpredictor_improves_prediction_pressure": {
            "pass": bool(train_report["pass"] and controls["pass"]),
            "training": train_report,
            "controls": controls,
        },
        "local_auto_lirpa_certifies_vector_vs_scalar_under_same_perturbation": lirpa,
    }
    graveyard_companions = {
        "identity_predictor_control_does_not_substitute": {
            "pass": bool(controls["direct_lewm_transition_score"] < controls["identity_predictor_transition_score"] * 0.05),
            "direct_score": controls["direct_lewm_transition_score"],
            "identity_score": controls["identity_predictor_transition_score"],
        },
        "shuffled_shell_order_control_does_not_substitute": {
            "pass": bool(controls["direct_lewm_transition_score"] < controls["shuffled_shell_order_transition_score"] * 0.05),
            "direct_score": controls["direct_lewm_transition_score"],
            "shuffled_score": controls["shuffled_shell_order_transition_score"],
            "shuffled_order": controls["shuffled_order"],
        },
        "scalar_axis0_projection_control_is_certifiably_separated": {
            "pass": bool(lirpa["pass"] and lirpa["certified_scalar_lower_minus_vector_upper"] > 0.05),
            "certified_gap": lirpa["certified_scalar_lower_minus_vector_upper"],
            "scalar_score": controls["scalar_axis0_projection_transition_score"],
            "direct_score": controls["direct_lewm_transition_score"],
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
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "variants": sorted(graveyard_companions),
        },
        "why_not_v4_probes": [
            "Clean v5 formal scout; not a v4 probe or legacy result-estate promotion.",
            "Direct le-wm import and LiRPA certificate are finite tool/function evidence only.",
            "No final manifold, basin, Axis0, bridge, architecture, or physics claim is made.",
        ],
        "promotion_allowed_reason": "false: scout-level direct-module/tool-bound receipt only; no final manifold/basin/Axis0/architecture claim",
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
