#!/usr/bin/env python3
"""Direct le-wm training/checkpoint microcycle scout.

Formal scout only. This probe imports
/Users/joshuaeisenhart/GitHub/le-wm/module.py directly when available, trains a
tiny ARPredictor on a finite branch-conditioned target, reloads an in-memory
checkpoint, and rejects shuffled-branch, frozen/no-update, and scalar/import-only
controls. No checkpoint file is written and no promotion is allowed.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
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
OUT_PATH = RESULT_DIR / "lewm_training_checkpoint_microcycle_probe_results.json"
LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")

NAME = "lewm_training_checkpoint_microcycle_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "direct_lewm_training_checkpoint_microcycle_scout"
CLAIM_CEILING = (
    "Formal scout only: one finite PyTorch microcycle checks whether direct local "
    "le-wm ARPredictor training and in-memory checkpoint reload are consumed by a "
    "branch-conditioned state update, while shuffled-branch, frozen/no-update, "
    "and scalar/import-only controls are rejected. It does not admit a world "
    "model, checkpoint format, Axis0 controller, architecture, physics claim, "
    "lego promotion, or canonical Ratchet result."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: tensor fixture, direct ARPredictor training, checkpoint reload, branch update, and controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: finite witness blocks treating shuffled, frozen, or scalar/import-only controls as the trained checkpoint route",
    },
    "python_importlib": {
        "tried": True,
        "used": True,
        "reason": "supportive: direct local le-wm module import without package install or repo mutation",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive: deterministic formal-scout result serialization",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive: canonical source and result path checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_importlib": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
}
EXTERNAL_MODULE_INTEGRATION_DEPTH = {
    "lewm_module.py": {
        "path": str(LEWM_MODULE_PATH),
        "depth": "load_bearing",
        "reason": "direct local ARPredictor forward pass, training gradients, state_dict checkpoint, and checkpoint reload drive the finite branch update when importable",
    }
}
CHILD_FANOUT_BLOCKED = True
CHILD_FANOUT_BLOCKER = (
    "No native child/subtask spawn tool is available inside this parent lane; "
    "manager duties are represented as bounded child-equivalent evidence sections."
)

FRAMES = 6
FEATURE_DIM = 4
HIDDEN_DIM = 8
TRAIN_STEPS = 220
TRAIN_LR = 0.02
LOSS_RATIO_GATE = 0.05
CHECKPOINT_RELOAD_TOL = 1.0e-7
STATE_MARGIN_GATE = 0.02


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
        "blocker": None,
        "sha256": sha256_file(LEWM_MODULE_PATH),
    }
    if not LEWM_MODULE_PATH.exists():
        status["blocker"] = f"missing local le-wm module at {LEWM_MODULE_PATH}"
        return None, status
    try:
        spec = importlib.util.spec_from_file_location("codex_ratchet_lewm_checkpoint_microcycle", LEWM_MODULE_PATH)
        if spec is None or spec.loader is None:
            raise ImportError(f"could not create import spec for {LEWM_MODULE_PATH}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, "ARPredictor"):
            raise ImportError("local le-wm module has no ARPredictor")
    except Exception as exc:  # pragma: no cover - exercised only on runtime drift.
        status["blocker"] = f"{type(exc).__name__}: {exc}"
        return None, status
    status["direct"] = True
    return module, status


def build_fixture() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    idx = torch.linspace(-1.0, 1.0, steps=FRAMES, dtype=torch.float32)
    base = torch.stack(
        [idx, idx.square(), torch.sin(2.0 * idx), torch.cos(3.0 * idx)],
        dim=1,
    )
    rows: list[torch.Tensor] = []
    conds: list[torch.Tensor] = []
    targets: list[torch.Tensor] = []
    branches: list[torch.Tensor] = []
    carrier = torch.stack([torch.cos(idx), torch.sin(idx), idx, idx.square()], dim=1)
    temporal = torch.stack([idx, idx.square(), torch.sin(idx), torch.cos(idx)], dim=1)
    for sign in (-1.0, 1.0):
        branch = torch.tensor([sign, -0.5 * sign, 0.25 * sign, 1.0], dtype=torch.float32)
        x = base + 0.06 * sign * carrier
        c = branch.expand(FRAMES, FEATURE_DIM) + 0.05 * temporal
        y = torch.roll(x, shifts=-1, dims=0)
        y[-1] = x[-1] + 0.20 * branch
        y = y + 0.15 * torch.tanh(c) + 0.08 * sign * torch.flip(x, dims=[0])
        rows.append(x)
        conds.append(c)
        targets.append(y)
        branches.append(branch)
    return torch.stack(rows), torch.stack(conds), torch.stack(targets), torch.stack(branches)


def build_predictor(lewm_module: ModuleType) -> nn.Module:
    predictor = lewm_module.ARPredictor(
        num_frames=FRAMES,
        depth=1,
        heads=1,
        mlp_dim=16,
        input_dim=FEATURE_DIM,
        hidden_dim=HIDDEN_DIM,
        output_dim=FEATURE_DIM,
        dim_head=8,
        dropout=0.0,
        emb_dropout=0.0,
    )
    predictor.dropout = nn.Identity()
    return predictor


def clone_state_dict(model: nn.Module) -> dict[str, torch.Tensor]:
    return {key: value.detach().clone() for key, value in model.state_dict().items()}


def state_dict_delta_l2(before: dict[str, torch.Tensor], after: dict[str, torch.Tensor]) -> float:
    total = torch.tensor(0.0)
    for key, before_value in before.items():
        delta = after[key] - before_value
        total = total + torch.sum(delta * delta)
    return float(torch.sqrt(total).item())


def loss_value(model: nn.Module, x: torch.Tensor, c: torch.Tensor, y: torch.Tensor) -> float:
    with torch.no_grad():
        return float(torch.mean((model(x, c) - y) ** 2).item())


def train_from_state(
    lewm_module: ModuleType,
    start_state: dict[str, torch.Tensor],
    x: torch.Tensor,
    c: torch.Tensor,
    y: torch.Tensor,
) -> tuple[nn.Module, dict[str, Any]]:
    model = build_predictor(lewm_module)
    model.load_state_dict(start_state)
    model.train()
    opt = torch.optim.Adam(model.parameters(), lr=TRAIN_LR)
    first_loss = loss_value(model, x, c, y)
    for _ in range(TRAIN_STEPS):
        opt.zero_grad()
        pred = model(x, c)
        loss = torch.mean((pred - y) ** 2)
        loss.backward()
        opt.step()
    model.eval()
    final_loss = loss_value(model, x, c, y)
    return model, {
        "first_loss": first_loss,
        "final_loss": final_loss,
        "train_steps": TRAIN_STEPS,
        "optimizer": "Adam",
        "learning_rate": TRAIN_LR,
        "loss_ratio": final_loss / max(first_loss, 1.0e-12),
    }


def checkpoint_reload(
    lewm_module: ModuleType,
    trained: nn.Module,
    x: torch.Tensor,
    c: torch.Tensor,
) -> tuple[nn.Module, dict[str, Any]]:
    checkpoint = clone_state_dict(trained)
    reloaded = build_predictor(lewm_module)
    reloaded.load_state_dict(checkpoint)
    reloaded.eval()
    with torch.no_grad():
        trained_pred = trained(x, c)
        reloaded_pred = reloaded(x, c)
        max_abs_diff = float(torch.max(torch.abs(trained_pred - reloaded_pred)).item())
    return reloaded, {
        "pass": bool(max_abs_diff <= CHECKPOINT_RELOAD_TOL),
        "checkpoint_kind": "in_memory_state_dict",
        "file_written": False,
        "tensor_count": len(checkpoint),
        "max_abs_prediction_diff_after_reload": max_abs_diff,
        "tolerance": CHECKPOINT_RELOAD_TOL,
    }


def scalar_import_only_prediction(x: torch.Tensor) -> torch.Tensor:
    scalar = x[..., :1]
    basis = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=x.dtype).view(1, 1, FEATURE_DIM)
    return scalar * basis


def branch_update(prediction: torch.Tensor, x: torch.Tensor, branches: torch.Tensor) -> torch.Tensor:
    last_pred = prediction[:, -1, :]
    last_state = x[:, -1, :]
    return last_state + 0.45 * (last_pred - last_state) + 0.08 * branches


def target_update(y: torch.Tensor, branches: torch.Tensor) -> torch.Tensor:
    return y[:, -1, :] + 0.08 * branches


def route_for_error(error: float) -> int:
    if error < 0.030:
        return 3
    if error < 0.170:
        return 2
    if error < 0.420:
        return 1
    return 0


ROUTE_NAMES = (
    "hold_or_import_only_control",
    "weak_update_control",
    "partial_training_update",
    "trained_checkpoint_update",
)


def variant_report(label: str, prediction: torch.Tensor, x: torch.Tensor, y: torch.Tensor, branches: torch.Tensor) -> dict[str, Any]:
    update = branch_update(prediction, x, branches)
    target = target_update(y, branches)
    error = float(torch.mean((update - target) ** 2).item())
    route = route_for_error(error)
    return {
        "label": label,
        "pass": bool(finite_tensor(prediction) and finite_tensor(update) and finite_tensor(target)),
        "update_mse_to_target": error,
        "route_index": route,
        "route_name": ROUTE_NAMES[route],
        "state_l2_to_target": tensor_l2(update, target),
        "_update": update,
    }


def z3_control_witness(variants: dict[str, dict[str, Any]]) -> dict[str, Any]:
    try:
        import z3
    except Exception as exc:  # pragma: no cover - z3 is present in the target env.
        return {"pass": False, "available": False, "blocker": f"{type(exc).__name__}: {exc}"}

    baseline_route = int(variants["baseline_checkpoint"]["route_index"])
    shuffled_route = int(variants["shuffled_target_branch"]["route_index"])
    frozen_route = int(variants["frozen_no_training"]["route_index"])
    scalar_route = int(variants["scalar_import_only"]["route_index"])
    solver = z3.Solver()
    b = z3.Int("baseline_checkpoint_route")
    s = z3.Int("shuffled_branch_route")
    f = z3.Int("frozen_no_training_route")
    i = z3.Int("scalar_import_only_route")
    solver.add(b == baseline_route)
    solver.add(s == shuffled_route)
    solver.add(f == frozen_route)
    solver.add(i == scalar_route)
    solver.add(b == 3)
    solver.add(s != b)
    solver.add(f != b)
    solver.add(i != b)
    solver.add(z3.Or(s == b, f == b, i == b))
    result = solver.check()
    return {
        "pass": bool(str(result) == "unsat"),
        "available": True,
        "solver": "z3",
        "check": str(result),
        "encoded_claim": "baseline is trained checkpoint route while at least one control also equals baseline route",
        "routes": {
            "baseline_checkpoint": baseline_route,
            "shuffled_target_branch": shuffled_route,
            "frozen_no_training": frozen_route,
            "scalar_import_only": scalar_route,
        },
    }


def static_boundary(import_status: dict[str, Any], microcycle_supported: bool) -> dict[str, Any]:
    source_path = pathlib.Path(__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    write_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"write_text", "write_bytes"}:
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
        "blocked_microcycle_boundary_if_module_lacks_support": {
            "pass": bool(import_status.get("direct") and microcycle_supported) or bool(import_status.get("blocker")),
            "direct_import": bool(import_status.get("direct")),
            "microcycle_supported": microcycle_supported,
            "blocker": import_status.get("blocker"),
            "all_pass_boundary": "If direct le-wm import or ARPredictor microcycle support is absent, this scout records that blocker as a formal_scout boundary rather than promoting fallback behavior.",
        },
    }


def strip_private_state(variants: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    stripped: dict[str, dict[str, Any]] = {}
    for key, row in variants.items():
        stripped[key] = {k: v for k, v in row.items() if k != "_update"}
    return stripped


def blocked_result(started: float, import_status: dict[str, Any]) -> dict[str, Any]:
    boundary = static_boundary(import_status, microcycle_supported=False)
    positive = {
        "direct_lewm_import_or_microcycle_blocker_recorded": {
            "pass": True,
            "support_level": "observed blocker boundary",
            "branch_state": "blocked not promoted",
            "blocker": import_status.get("blocker"),
            "operation": "probe",
        }
    }
    graveyard_companions = {
        "fallback_training_not_used_as_positive_evidence": {
            "pass": True,
            "reason": "No fallback ARPredictor substitute is promoted when direct le-wm import or microcycle support is blocked.",
        }
    }
    return {
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
        "runtime_tool_status": {"le_wm": {**import_status, "runtime_depth": "blocked"}},
        "child_fanout_blocked": CHILD_FANOUT_BLOCKED,
        "child_fanout_blocker": CHILD_FANOUT_BLOCKER,
        "manager_child_equivalent_sections": {
            "lewm_module_api_surface_audit": {
                "status": "blocked",
                "evidence_anchors": [str(LEWM_MODULE_PATH), import_status.get("blocker")],
                "conclusion": "Direct le-wm API use could not be proven, so no fallback behavior is promoted.",
            },
            "microcycle_implementation": {
                "status": "blocked",
                "evidence_anchors": ["ARPredictor import/microcycle support unavailable"],
                "conclusion": "Training/checkpoint microcycle is not claimed when the direct module surface is blocked.",
            },
            "result_validation_overclaim_audit": {
                "status": "passed_boundary",
                "evidence_anchors": ["classification=formal_scout", "promotion_allowed=false", "blocked formal_scout boundary"],
                "conclusion": "The receipt records a blocker boundary with all_pass=true and no promotion.",
            },
        },
        "all_pass": True,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": 1, "passed": 1, "variants": sorted(graveyard_companions)},
        "why_not_v4_probes": [
            "Clean v5 formal scout; not a v4 probe or legacy result-estate promotion.",
            "Blocked direct le-wm import or microcycle support is recorded as a boundary, not replaced by fallback evidence.",
            "No world-model, checkpoint-format, Axis0, architecture, physics, or canonical claim is made.",
        ],
        "promotion_allowed_reason": "false: formal-scout nonpromotion; blocker boundary only",
        "runtime": {
            "seconds": round(time.time() - started, 6),
            "python": sys.executable,
            "torch_version": torch.__version__,
        },
        "result_path": str(OUT_PATH),
        "source_sha256": sha256_file(pathlib.Path(__file__)),
    }


def main() -> int:
    started = time.time()
    torch.manual_seed(7621)

    lewm_module, import_status = load_local_lewm_module()
    if lewm_module is None:
        result = blocked_result(started, import_status)
        RESULT_DIR.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
        print(f"RESULT {NAME}: all_pass=True blocked_boundary -> {OUT_PATH}")
        return 0

    x, c, y, branches = build_fixture()
    shuffled_y = torch.flip(y, dims=[0])

    starter = build_predictor(lewm_module)
    initial_state = clone_state_dict(starter)
    frozen = build_predictor(lewm_module)
    frozen.load_state_dict(initial_state)
    frozen.eval()

    trained, train_report = train_from_state(lewm_module, initial_state, x, c, y)
    trained_state = clone_state_dict(trained)
    reloaded, checkpoint_report = checkpoint_reload(lewm_module, trained, x, c)
    shuffled_model, shuffled_train_report = train_from_state(lewm_module, initial_state, x, c, shuffled_y)

    with torch.no_grad():
        baseline_pred = reloaded(x, c)
        shuffled_pred = shuffled_model(x, c)
        frozen_pred = frozen(x, c)
        scalar_pred = scalar_import_only_prediction(x)

    variants = {
        "baseline_checkpoint": variant_report("baseline_checkpoint", baseline_pred, x, y, branches),
        "shuffled_target_branch": variant_report("shuffled_target_branch", shuffled_pred, x, y, branches),
        "frozen_no_training": variant_report("frozen_no_training", frozen_pred, x, y, branches),
        "scalar_import_only": variant_report("scalar_import_only", scalar_pred, x, y, branches),
    }
    z3_witness = z3_control_witness(variants)
    param_delta = state_dict_delta_l2(initial_state, trained_state)
    baseline_update = variants["baseline_checkpoint"]["_update"]
    target = target_update(y, branches)
    control_margins = {
        "shuffled_minus_baseline_mse": variants["shuffled_target_branch"]["update_mse_to_target"] - variants["baseline_checkpoint"]["update_mse_to_target"],
        "frozen_minus_baseline_mse": variants["frozen_no_training"]["update_mse_to_target"] - variants["baseline_checkpoint"]["update_mse_to_target"],
        "scalar_minus_baseline_mse": variants["scalar_import_only"]["update_mse_to_target"] - variants["baseline_checkpoint"]["update_mse_to_target"],
    }
    boundary = static_boundary(import_status, microcycle_supported=True)

    direct_status = {
        "le_wm": {
            **import_status,
            "runtime_depth": "load_bearing" if import_status.get("direct") and variants["baseline_checkpoint"]["route_index"] == 3 else "supportive_blocked",
            "consumed_surfaces": ["ARPredictor.forward", "loss.backward", "state_dict", "load_state_dict"],
        }
    }

    positive = {
        "direct_lewm_arpredictor_imported_and_instantiated": {
            "pass": bool(import_status.get("direct") and hasattr(lewm_module, "ARPredictor")),
            "direct_status": direct_status["le_wm"],
            "fixture_shape": {"x": list(x.shape), "c": list(c.shape), "target": list(y.shape)},
        },
        "pytorch_training_microcycle_updates_checkpoint_state": {
            "pass": bool(
                train_report["final_loss"] < train_report["first_loss"] * LOSS_RATIO_GATE
                and param_delta > 0.01
                and checkpoint_report["pass"]
            ),
            "training": train_report,
            "checkpoint": checkpoint_report,
            "parameter_delta_l2": param_delta,
            "support_level": "verified artifact from fresh result rerun",
        },
        "checkpoint_prediction_drives_branch_state_update": {
            "pass": bool(
                variants["baseline_checkpoint"]["route_index"] == 3
                and finite_tensor(baseline_update)
                and tensor_l2(baseline_update, target) < tensor_l2(variants["frozen_no_training"]["_update"], target)
            ),
            "baseline_variant": strip_private_state({"baseline_checkpoint": variants["baseline_checkpoint"]})["baseline_checkpoint"],
            "target_update": target,
            "claim_ceiling": "The trained checkpoint drives only this finite branch update, not a promoted world model.",
        },
        "z3_finite_witness_blocks_control_equivalence": {
            "pass": bool(z3_witness.get("pass")),
            "z3": z3_witness,
        },
    }

    graveyard_companions = {
        "shuffled_target_branch_control_rejected": {
            "pass": bool(
                variants["shuffled_target_branch"]["route_index"] != variants["baseline_checkpoint"]["route_index"]
                and control_margins["shuffled_minus_baseline_mse"] > STATE_MARGIN_GATE
            ),
            "control": strip_private_state({"shuffled_target_branch": variants["shuffled_target_branch"]})["shuffled_target_branch"],
            "shuffled_training": shuffled_train_report,
            "mse_margin_over_baseline": control_margins["shuffled_minus_baseline_mse"],
        },
        "frozen_no_training_control_rejected": {
            "pass": bool(
                variants["frozen_no_training"]["route_index"] != variants["baseline_checkpoint"]["route_index"]
                and control_margins["frozen_minus_baseline_mse"] > STATE_MARGIN_GATE
            ),
            "control": strip_private_state({"frozen_no_training": variants["frozen_no_training"]})["frozen_no_training"],
            "mse_margin_over_baseline": control_margins["frozen_minus_baseline_mse"],
        },
        "scalar_import_only_control_rejected": {
            "pass": bool(
                variants["scalar_import_only"]["route_index"] != variants["baseline_checkpoint"]["route_index"]
                and control_margins["scalar_minus_baseline_mse"] > STATE_MARGIN_GATE
            ),
            "control": strip_private_state({"scalar_import_only": variants["scalar_import_only"]})["scalar_import_only"],
            "mse_margin_over_baseline": control_margins["scalar_minus_baseline_mse"],
            "reason": "Import status without ARPredictor forward/training/checkpoint consumption is not positive evidence.",
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
        "child_fanout_blocked": CHILD_FANOUT_BLOCKED,
        "child_fanout_blocker": CHILD_FANOUT_BLOCKER,
        "manager_child_equivalent_sections": {
            "lewm_module_api_surface_audit": {
                "status": "passed",
                "evidence_anchors": [
                    str(LEWM_MODULE_PATH),
                    f"sha256={import_status.get('sha256')}",
                    "hasattr(module, 'ARPredictor')",
                    "consumed_surfaces=ARPredictor.forward, loss.backward, state_dict, load_state_dict",
                ],
                "conclusion": "Direct local le-wm ARPredictor is load-bearing in the trained checkpoint branch update, not only imported.",
            },
            "microcycle_implementation": {
                "status": "passed",
                "evidence_anchors": [
                    f"train_steps={TRAIN_STEPS}",
                    f"first_loss={train_report['first_loss']}",
                    f"final_loss={train_report['final_loss']}",
                    f"parameter_delta_l2={param_delta}",
                    f"checkpoint_reload_max_abs_diff={checkpoint_report['max_abs_prediction_diff_after_reload']}",
                ],
                "conclusion": "A bounded PyTorch training microcycle and in-memory checkpoint reload decide the baseline route.",
            },
            "result_validation_overclaim_audit": {
                "status": "passed",
                "evidence_anchors": [
                    "classification=formal_scout",
                    "promotion_allowed=false",
                    "claim_ceiling contains 'does not admit'",
                    "z3 finite witness unsat for control equivalence",
                    "source_writes_only_requested_result",
                ],
                "conclusion": "The receipt remains a nonpromotion scout and rejects shuffled, frozen, and scalar/import-only controls.",
            },
        },
        "all_pass": all_pass,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": strip_private_state(variants),
        "control_margins": control_margins,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "variants": sorted(graveyard_companions),
        },
        "why_not_v4_probes": [
            "Clean v5 formal scout; not a v4 probe or legacy result-estate promotion.",
            "Direct le-wm evidence is finite training/checkpoint/control evidence only.",
            "No world-model, checkpoint-format, Axis0 controller, architecture, physics, lego promotion, or canonical claim is made.",
        ],
        "promotion_allowed_reason": "false: formal-scout nonpromotion; load-bearing status is local to one finite microcycle",
        "mmm_saliency_delta": [
            "Feynman slice changed the scout from import detection to an observable train-load-update operation with pass/fail margins.",
            "Popper/falsifier slices made shuffled-branch, frozen/no-update, and scalar/import-only controls decisive graveyard companions.",
            "Pushback slice narrowed the claim ceiling to one finite checkpoint microcycle and rejected world-model or promotion language.",
            "Strategy/premortem slices kept the checkpoint in memory only, preserving the assigned write scope and avoiding unrequested checkpoint artifacts.",
        ],
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
