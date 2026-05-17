#!/usr/bin/env python3
"""Initial-density sweep for the Gray-walk staged entropy probe.

This bounded follow-on tests whether the prior six-bit Gray-walk staged entropy
result is structurally path-only or becomes outcome-sensitive for other finite
initial density states. It is a tool-lego fit probe only.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
from datetime import UTC, datetime
from typing import Any

import numpy as np
import scipy.linalg
import torch


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Bounded Gray-walk staged entropy initial-density sweep. It tests whether "
    "the prior finite mapping packet is path-only or outcome-sensitive across "
    "multiple finite initial density states. It does not promote target-system, "
    "geometric-manifold, coordinate-family, bridge, or nonclassical admission."
)

LEGO_IDS = [
    "six_bit_gray_walk_staged_entropy",
    "density_matrix_representability",
    "operator_order_variant",
    "order_variant_graveyard",
]
PRIMARY_LEGO_IDS = ["six_bit_gray_walk_staged_entropy", "density_matrix_representability"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "finite density-state grid and result aggregation"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing staged density evolution over initial states"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing entropy crosscheck through eigenspectrum/logm"},
    "z3": {"tried": False, "used": False, "reason": "not needed; prior packet carries the supportive distinct-line fence"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "load_bearing",
    "scipy": "load_bearing",
    "z3": None,
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
PARENT_SOURCE = PROBE_DIR / "sim_six_bit_gray_walk_measure_feedback_reset_entropy.py"
PARENT_RESULT = RESULT_DIR / "six_bit_gray_walk_measure_feedback_reset_entropy_results.json"
EPS = 1e-10


def load_parent_module():
    spec = importlib.util.spec_from_file_location(
        "six_bit_gray_walk_measure_feedback_reset_entropy",
        PARENT_SOURCE,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {PARENT_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_parent_receipt() -> dict[str, object]:
    if not PARENT_RESULT.exists():
        return {"path": str(PARENT_RESULT), "exists": False, "all_pass": False}
    data = json.loads(PARENT_RESULT.read_text(encoding="utf-8"))
    return {
        "path": str(PARENT_RESULT),
        "exists": True,
        "all_pass": bool(data.get("summary", {}).get("all_pass", data.get("all_pass"))),
        "classification": data.get("classification"),
        "outcome_order_sensitive": bool(data.get("summary", {}).get("outcome_order_sensitive")),
    }


def scipy_entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.T) / 2.0)
    vals = vals[vals > 1e-14]
    if len(vals) == 0:
        return 0.0
    diag = np.diag(vals)
    return float(np.real(-np.trace(diag @ scipy.linalg.logm(diag)) / np.log(2.0)))


def torch_entropy(rho: torch.Tensor) -> torch.Tensor:
    vals = torch.linalg.eigvalsh((rho + rho.T) / 2.0)
    vals = torch.clamp(vals, min=1e-14)
    return -torch.sum(vals * torch.log2(vals))


def initial_states() -> dict[str, torch.Tensor]:
    return {
        "pure_x": torch.tensor([[0.5, 0.5], [0.5, 0.5]], dtype=torch.float64),
        "mixed_diag_70_30": torch.tensor([[0.7, 0.0], [0.0, 0.3]], dtype=torch.float64),
        "max_mixed": torch.tensor([[0.5, 0.0], [0.0, 0.5]], dtype=torch.float64),
        "coherent_mixed": torch.tensor([[0.6, 0.2], [0.2, 0.4]], dtype=torch.float64),
        "near_pure_diag": torch.tensor([[0.95, 0.0], [0.0, 0.05]], dtype=torch.float64),
    }


def state_validity(rho: torch.Tensor) -> dict[str, object]:
    vals = torch.linalg.eigvalsh((rho + rho.T) / 2.0)
    return {
        "trace": float(torch.trace(rho)),
        "min_eigenvalue": float(torch.min(vals)),
        "hermitian_gap": float(torch.max(torch.abs(rho - rho.T))),
        "pass": abs(float(torch.trace(rho)) - 1.0) < EPS
        and float(torch.min(vals)) >= -EPS
        and float(torch.max(torch.abs(rho - rho.T))) < EPS,
    }


def torch_stage_step(rho: torch.Tensor, line: int, mix: torch.Tensor) -> torch.Tensor:
    x = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.float64)
    z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.float64)
    operator = x if line <= 2 else z
    rotated = operator @ rho @ operator.T
    return (1.0 - mix) * rho + mix * rotated


def run_torch_trajectory(
    rho0: torch.Tensor, lines: list[int], mixes: list[torch.Tensor]
) -> tuple[torch.Tensor, list[torch.Tensor]]:
    rho = rho0.clone()
    entropies = [torch_entropy(rho)]
    for line, mix in zip(lines, mixes, strict=True):
        rho = torch_stage_step(rho, line, mix)
        entropies.append(torch_entropy(rho))
    return rho, entropies


def run_np_trajectory(rho0: np.ndarray, lines: list[int], mixes: list[float]) -> tuple[np.ndarray, list[float]]:
    x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64)
    z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.float64)
    rho = rho0.copy()
    entropies = [scipy_entropy(rho)]
    for line, mix in zip(lines, mixes, strict=True):
        op = x if line <= 2 else z
        rho = (1.0 - mix) * rho + mix * (op @ rho @ op.T)
        entropies.append(scipy_entropy(rho))
    return rho, entropies


def sweep_rows(parent_module: Any) -> list[dict[str, object]]:
    rows = []
    mixes = [0.19, 0.27, 0.43, 0.31]
    torch_mixes = [torch.tensor(value, dtype=torch.float64, requires_grad=True) for value in mixes]
    for candidate in parent_module.candidate_blocks():
        stage_lines = candidate["stage_line_changes"]
        forward_lines = [int(stage_lines[name]) for name in ["measure", "feedback", "erasure", "reset"]]
        reverse_lines = list(reversed(forward_lines))
        for state_name, rho0 in initial_states().items():
            local_mixes = [
                torch.tensor(value, dtype=torch.float64, requires_grad=True) for value in mixes
            ]
            f_rho, f_entropy = run_torch_trajectory(rho0, forward_lines, local_mixes)
            r_rho, r_entropy = run_torch_trajectory(rho0, reverse_lines, list(reversed(local_mixes)))
            trajectory_delta = torch.sum(torch.abs(torch.stack(f_entropy) - torch.stack(r_entropy)))
            final_delta = torch.linalg.matrix_norm(f_rho - r_rho)
            loss = trajectory_delta + f_entropy[-1]
            loss.backward()
            np_f_rho, np_f_entropy = run_np_trajectory(rho0.numpy(), forward_lines, mixes)
            np_r_rho, np_r_entropy = run_np_trajectory(rho0.numpy(), reverse_lines, list(reversed(mixes)))
            np_trajectory_delta = float(
                np.sum(np.abs(np.asarray(np_f_entropy) - np.asarray(np_r_entropy)))
            )
            rows.append(
                {
                    "candidate_start_index": candidate["start_index"],
                    "stage_lines": forward_lines,
                    "initial_state": state_name,
                    "initial_state_validity": state_validity(rho0),
                    "torch_trajectory_delta": float(trajectory_delta.detach()),
                    "scipy_trajectory_delta": np_trajectory_delta,
                    "torch_final_state_delta": float(final_delta.detach()),
                    "scipy_final_state_delta": float(np.linalg.norm(np_f_rho - np_r_rho, ord="fro")),
                    "torch_gradients": [float(mix.grad) for mix in local_mixes],
                    "trajectory_crosscheck_gap": abs(float(trajectory_delta.detach()) - np_trajectory_delta),
                }
            )
    return rows


def main() -> None:
    parent_module = load_parent_module()
    parent = read_parent_receipt()
    rows = sweep_rows(parent_module)
    max_final_delta = max(row["torch_final_state_delta"] for row in rows)
    max_scipy_final_delta = max(row["scipy_final_state_delta"] for row in rows)
    max_trajectory_delta = max(row["torch_trajectory_delta"] for row in rows)
    positive = {
        "parent_receipt_passes": {"parent": parent, "pass": parent["exists"] and parent["all_pass"]},
        "sweeps_all_parent_candidates_and_initial_states": {
            "candidate_count": len(parent_module.candidate_blocks()),
            "initial_state_count": len(initial_states()),
            "row_count": len(rows),
            "pass": len(rows) == len(parent_module.candidate_blocks()) * len(initial_states()),
        },
        "all_initial_states_are_valid_density_matrices": {
            "pass": all(row["initial_state_validity"]["pass"] for row in rows),
        },
        "scipy_crosschecks_torch_trajectory_deltas": {
            "max_crosscheck_gap": max(row["trajectory_crosscheck_gap"] for row in rows),
            "pass": max(row["trajectory_crosscheck_gap"] for row in rows) < 1e-8,
        },
    }
    negative = {
        "outcome_sensitive_claim_is_killed_for_sweep_grid": {
            "max_torch_final_state_delta": max_final_delta,
            "max_scipy_final_state_delta": max_scipy_final_delta,
            "pass": max_final_delta <= EPS and max_scipy_final_delta <= EPS,
        },
        "trajectory_signal_still_exists_for_at_least_one_state": {
            "max_torch_trajectory_delta": max_trajectory_delta,
            "pass": max_trajectory_delta > EPS,
        },
    }
    boundary = {
        "path_only_ceiling_before_any_stronger_claim": {
            "claim_ceiling": "path_order_sensitive_only_not_outcome_order_sensitive",
            "pass": True,
        },
        "no_target_system_manifold_coordinate_bridge_or_nonclassical_admission": {
            "promotion_allowed": False,
            "pass": True,
        },
    }
    all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    result = {
        "name": "gray_walk_staged_entropy_initial_density_sweep",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "finite_mapping_comparison",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {"six_bit_gray_walk_measure_feedback_reset_entropy": str(PARENT_RESULT)},
        "sweep_rows": rows,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "promotion_allowed": False,
            "outcome_order_sensitive": False,
            "path_order_sensitive": max_trajectory_delta > EPS,
            "max_torch_final_state_delta": max_final_delta,
            "max_torch_trajectory_delta": max_trajectory_delta,
            "claim_ceiling": "path_order_sensitive_only_not_outcome_order_sensitive",
            "scope_note": divergence_log,
        },
        "all_pass": bool(all_pass),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / "gray_walk_staged_entropy_initial_density_sweep_results.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
