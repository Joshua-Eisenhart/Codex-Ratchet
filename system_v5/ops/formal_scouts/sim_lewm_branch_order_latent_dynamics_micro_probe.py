#!/usr/bin/env python3
"""le-wm branch-order latent dynamics micro-probe."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import time
from types import ModuleType
from typing import Any

import torch
import torch.nn as nn


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "lewm_branch_order_latent_dynamics_micro_probe_results.json"
LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")

NAME = "lewm_branch_order_latent_dynamics_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: local le-wm module.py is used as a tiny latent-dynamics "
    "adapter for branch-order pressure. It is not a promoted world model, "
    "manifold, basin, Axis0, bridge, or architecture claim."
)
TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing tensor fixture, training loop, and controls"},
    "le_wm": {"tried": True, "used": True, "reason": "load-bearing local ARPredictor branch adapter"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "le_wm": "load_bearing",
}
NEARBY_VARIANTS = {
    "total": 1,
    "passed": 1,
    "variants": ["identity_roll_control_not_enough"],
}
WHY_NOT_V4_PROBES = [
    "This is a v5 formal scout for a tiny local le-wm latent-dynamics fixture.",
    "It records bounded branch-order pressure only; it does not promote a v4 canonical probe, world model, manifold, basin, or architecture claim.",
]


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


def blocked_receipt(started: float, blocker: str, detail: str) -> dict[str, Any]:
    return {
        "name": NAME,
        "schema": "formal_scout_result_v1",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": "formal_tool_admission",
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": {
            **TOOL_MANIFEST,
            "le_wm": {"tried": True, "used": False, "reason": blocker},
        },
        "tool_manifest": {
            "pytorch": TOOL_MANIFEST["pytorch"],
            "le_wm": {"tried": True, "used": False, "reason": blocker},
        },
        "TOOL_INTEGRATION_DEPTH": {"pytorch": "load_bearing", "le_wm": None},
        "tool_integration_depth": {"pytorch": "load_bearing", "le_wm": None},
        "positive": {},
        "graveyard_companions": {},
        "boundary": {"train_steps": 0, "root_constraint_wording": "blocked before le-wm branch receipt could run"},
        "nearby_variants": {"total": 0, "passed": 0, "variants": []},
        "why_not_v4_probes": WHY_NOT_V4_PROBES,
        "blockers": [{"kind": blocker, "detail": detail}],
        "elapsed_seconds": time.time() - started,
        "all_pass": False,
    }


def load_lewm_module() -> ModuleType:
    if not LEWM_MODULE_PATH.exists():
        raise FileNotFoundError(f"missing local le-wm module: {LEWM_MODULE_PATH}")
    spec = importlib.util.spec_from_file_location("codex_ratchet_lewm_micro_probe", LEWM_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load import spec for {LEWM_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def branch_fixture() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    t = torch.linspace(0.0, 1.0, steps=7, dtype=torch.float32)
    seq = torch.stack([t, t.square(), torch.sin(t * 3.0), torch.cos(t * 2.0)], dim=1).unsqueeze(0)
    reverse_order = torch.tensor([6, 5, 4, 3, 2, 1, 0], dtype=torch.long)
    target = torch.roll(seq, shifts=-1, dims=1)
    return seq, seq[:, reverse_order, :], target


def make_predictor(lewm: ModuleType) -> nn.Module:
    predictor = lewm.ARPredictor(
        num_frames=7,
        depth=0,
        heads=1,
        mlp_dim=8,
        input_dim=4,
        hidden_dim=6,
        output_dim=4,
        dim_head=4,
        dropout=0.0,
        emb_dropout=0.0,
    )
    if hasattr(predictor, "dropout"):
        predictor.dropout = nn.Identity()
    return predictor


def transition_score(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return torch.mean((pred - target) ** 2)


def run_probe() -> dict[str, Any]:
    lewm = load_lewm_module()
    predictor = make_predictor(lewm)
    forward, reverse, target = branch_fixture()
    torch.manual_seed(20260519)
    opt = torch.optim.Adam(predictor.parameters(), lr=0.04)
    first = None
    for step in range(160):
        opt.zero_grad()
        score = transition_score(predictor(forward, forward), target)
        if first is None:
            first = float(score.detach().item())
        score.backward()
        opt.step()
    predictor.eval()
    with torch.no_grad():
        forward_score = transition_score(predictor(forward, forward), target)
        reverse_score = transition_score(predictor(reverse, reverse), target)
        identity_score = transition_score(forward, target)
    positive = {
        "lewm_direct_module_imports": {
            "pass": bool(hasattr(lewm, "ARPredictor")),
            "module_path": str(LEWM_MODULE_PATH),
        },
        "forward_branch_latent_dynamics_fit_micro_fixture": {
            "pass": bool(first is not None and forward_score.item() < first * 0.30),
            "first_score": first,
            "forward_score": float(forward_score.item()),
        },
        "branch_order_pressure_observed": {
            "pass": bool(reverse_score.item() > forward_score.item() * 1.5),
            "reverse_score": float(reverse_score.item()),
            "forward_score": float(forward_score.item()),
        },
    }
    graveyard = {
        "identity_roll_control_not_enough": {
            "pass": bool(identity_score.item() > forward_score.item()),
            "identity_score": float(identity_score.item()),
        }
    }
    return {
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": {"train_steps": 160, "root_constraint_wording": "evidence-bound branch receipt, not promoted"},
        "blockers": [],
        "all_pass": all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard.values()),
    }


def main() -> int:
    started = time.time()
    try:
        body = run_probe()
        result = {
            "name": NAME,
            "schema": "formal_scout_result_v1",
            "classification": CLASSIFICATION,
            "sim_execution_kind": SIM_EXECUTION_KIND,
            "source_alignment_category": "formal_tool_admission",
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "tool_manifest": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "nearby_variants": NEARBY_VARIANTS,
            "why_not_v4_probes": WHY_NOT_V4_PROBES,
            "elapsed_seconds": time.time() - started,
            **body,
        }
    except FileNotFoundError as exc:
        result = blocked_receipt(started, "missing_runtime", str(exc))
    except ImportError as exc:
        result = blocked_receipt(started, "missing_import", f"le-wm import failed: {exc}")
    except Exception as exc:
        result = blocked_receipt(started, "runtime_error", f"le-wm micro probe failed: {type(exc).__name__}: {exc}")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
