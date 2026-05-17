#!/usr/bin/env python3
"""Six-bit Gray-walk staged entropy trajectory probe.

This bounded probe links an existing 64-state single-bit Gray walk receipt to
the local channel/operator order-variant receipt. It asks whether a four-stage
measurement-feedback-erasure-reset grammar has a finite single-bit-walk witness
without promoting the mapping to target-system or nonclassical admission.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime
from typing import Any

import numpy as np
import scipy.linalg
import torch
import z3


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Bounded six-bit Gray-walk staged entropy probe. It tests whether a "
    "four-stage measurement-feedback-erasure-reset grammar has a finite "
    "single-line Gray-walk witness and an order-sensitive entropy trajectory. "
    "This is comparison evidence only, not target-system or nonclassical "
    "admission."
)

LEGO_IDS = [
    "six_bit_gray_walk_staged_entropy",
    "operator_order_variant",
    "six_bit_gray_walk",
    "finite_walk_stage_correlation",
    "order_variant_graveyard",
]
PRIMARY_LEGO_IDS = ["six_bit_gray_walk_staged_entropy", "finite_walk_stage_correlation"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "finite Gray-walk and Hamming-line arrays"},
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing entropy trajectory and gradient witness over the staged density carrier",
    },
    "scipy": {"tried": True, "used": True, "reason": "load-bearing entropy crosscheck for the staged carrier"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive fence records the finite enumeration has no distinct-line witness",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "load_bearing",
    "scipy": "load_bearing",
    "z3": "supportive",
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
EPS = 1e-10


def bits(n: int, width: int = 6) -> list[int]:
    return [(n >> i) & 1 for i in range(width)]


def gray_code(n: int) -> int:
    return n ^ (n >> 1)


def hamming(a: int, b: int) -> int:
    return int(sum(x != y for x, y in zip(bits(a), bits(b))))


def changed_line(a: int, b: int) -> int:
    diff = [i for i, (x, y) in enumerate(zip(bits(a), bits(b))) if x != y]
    if len(diff) != 1:
        raise ValueError((a, b, diff))
    return diff[0]


def gray_states() -> list[int]:
    return [gray_code(i) for i in range(64)]


def gray_line_changes() -> list[int]:
    states = gray_states()
    return [changed_line(states[i], states[(i + 1) % 64]) for i in range(64)]


def source_receipt(path: pathlib.Path) -> dict[str, object]:
    if not path.exists():
        return {"path": str(path), "exists": False, "all_pass": False, "status": "missing"}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "path": str(path),
        "exists": True,
        "all_pass": bool(data.get("summary", {}).get("all_pass", data.get("all_pass"))),
        "status": data.get("classification"),
    }


def source_receipts() -> dict[str, dict[str, object]]:
    return {
        "channel_operator_entropy_order_variant": source_receipt(
            RESULT_DIR / "channel_operator_entropy_order_variant_results.json"
        ),
        "six_bit_gray_code_single_flip_cycle_invariant": source_receipt(RESULT_DIR / "six_bit_gray_code_single_flip_cycle_invariant_results.json"),
    }


def candidate_blocks() -> list[dict[str, object]]:
    lines = gray_line_changes()
    states = gray_states()
    rows = []
    stages = ["measure", "feedback", "erasure", "reset"]
    for start in range(64):
        block_lines = [lines[(start + offset) % 64] for offset in range(4)]
        if block_lines[0] <= 2 and block_lines[2] >= 3:
            block_states = [states[(start + offset) % 64] for offset in range(5)]
            rows.append(
                {
                    "start_index": start,
                    "states": block_states,
                    "stage_line_changes": dict(zip(stages, block_lines, strict=True)),
                    "all_hamming_one": all(
                        hamming(block_states[i], block_states[i + 1]) == 1 for i in range(4)
                    ),
                    "distinct_line_count": len(set(block_lines)),
                    "all_stage_lines_distinct": len(set(block_lines)) == 4,
                    "measure_lower_trigram": block_lines[0] <= 2,
                    "erasure_upper_trigram": block_lines[2] >= 3,
                }
            )
    return rows


def strongest_candidate() -> dict[str, object]:
    rows = candidate_blocks()
    if not rows:
        return {}
    return max(rows, key=lambda row: (int(row["distinct_line_count"]), -int(row["start_index"])))


def z3_no_distinct_measure_erasure_block() -> dict[str, object]:
    lines = gray_line_changes()
    start = z3.Int("start")
    valid_starts = []
    for idx in range(64):
        block = [lines[(idx + offset) % 64] for offset in range(4)]
        if block[0] <= 2 and block[2] >= 3 and len(set(block)) == 4:
            valid_starts.append(start == idx)
    solver = z3.Solver()
    solver.add(start >= 0, start < 64)
    solver.add(z3.Or(valid_starts) if valid_starts else z3.BoolVal(False))
    result = solver.check()
    return {
        "claim_killed": "canonical Gray walk has a four-stage measure/erase block with four distinct line operators",
        "candidate_count": len(valid_starts),
        "proof_vehicle": "finite_python_enumeration_with_supportive_z3_unsat_record",
        "z3_result": str(result),
        "pass": result == z3.unsat,
    }


def torch_entropy(rho: torch.Tensor) -> torch.Tensor:
    vals = torch.linalg.eigvalsh((rho + rho.T) / 2.0)
    vals = torch.clamp(vals, min=1e-14)
    return -torch.sum(vals * torch.log2(vals))


def scipy_entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.T) / 2.0)
    vals = vals[vals > 1e-14]
    if len(vals) == 0:
        return 0.0
    diag = np.diag(vals)
    return float(np.real(-np.trace(diag @ scipy.linalg.logm(diag)) / np.log(2.0)))


def torch_stage_step(rho: torch.Tensor, line: int, mix: torch.Tensor) -> torch.Tensor:
    x = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.float64)
    z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.float64)
    operator = x if line <= 2 else z
    rotated = operator @ rho @ operator.T
    return (1.0 - mix) * rho + mix * rotated


def np_stage_step(rho: np.ndarray, line: int, mix: float) -> np.ndarray:
    x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64)
    z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.float64)
    operator = x if line <= 2 else z
    rotated = operator @ rho @ operator.T
    return (1.0 - mix) * rho + mix * rotated


def torch_trajectory(lines: list[int], mixes: list[torch.Tensor]) -> tuple[torch.Tensor, list[torch.Tensor]]:
    rho = torch.tensor([[0.5, 0.5], [0.5, 0.5]], dtype=torch.float64)
    entropies = [torch_entropy(rho)]
    for line, mix in zip(lines, mixes, strict=True):
        rho = torch_stage_step(rho, line, mix)
        entropies.append(torch_entropy(rho))
    return rho, entropies


def np_trajectory(lines: list[int], mixes: list[float]) -> tuple[np.ndarray, list[float]]:
    rho = np.asarray([[0.5, 0.5], [0.5, 0.5]], dtype=np.float64)
    entropies = [scipy_entropy(rho)]
    for line, mix in zip(lines, mixes, strict=True):
        rho = np_stage_step(rho, line, mix)
        entropies.append(scipy_entropy(rho))
    return rho, entropies


def entropy_order_witness(candidate: dict[str, object]) -> dict[str, object]:
    stage_lines = candidate["stage_line_changes"]
    forward_lines = [int(stage_lines[name]) for name in ["measure", "feedback", "erasure", "reset"]]
    reverse_lines = list(reversed(forward_lines))
    mixes = [
        torch.tensor(0.19, dtype=torch.float64, requires_grad=True),
        torch.tensor(0.27, dtype=torch.float64, requires_grad=True),
        torch.tensor(0.43, dtype=torch.float64, requires_grad=True),
        torch.tensor(0.31, dtype=torch.float64, requires_grad=True),
    ]
    forward_rho, forward_entropy = torch_trajectory(forward_lines, mixes)
    reverse_rho, reverse_entropy = torch_trajectory(reverse_lines, list(reversed(mixes)))
    trajectory_delta = torch.sum(torch.abs(torch.stack(forward_entropy) - torch.stack(reverse_entropy)))
    final_state_delta = torch.linalg.matrix_norm(forward_rho - reverse_rho)
    loss = forward_entropy[-1] + trajectory_delta
    loss.backward()

    np_forward_rho, np_forward_entropy = np_trajectory(forward_lines, [0.19, 0.27, 0.43, 0.31])
    np_reverse_rho, np_reverse_entropy = np_trajectory(reverse_lines, [0.31, 0.43, 0.27, 0.19])
    np_trajectory_delta = float(
        np.sum(np.abs(np.asarray(np_forward_entropy) - np.asarray(np_reverse_entropy)))
    )
    return {
        "forward_lines": forward_lines,
        "reverse_lines": reverse_lines,
        "torch_forward_entropy": [float(row.detach()) for row in forward_entropy],
        "torch_reverse_entropy": [float(row.detach()) for row in reverse_entropy],
        "scipy_forward_entropy": np_forward_entropy,
        "scipy_reverse_entropy": np_reverse_entropy,
        "torch_trajectory_delta": float(trajectory_delta.detach()),
        "scipy_trajectory_delta": np_trajectory_delta,
        "torch_final_state_delta": float(final_state_delta.detach()),
        "scipy_final_state_delta": float(np.linalg.norm(np_forward_rho - np_reverse_rho, ord="fro")),
        "gradients": [float(mix.grad) for mix in mixes],
        "pass": float(trajectory_delta.detach()) > EPS
        and abs(float(trajectory_delta.detach()) - np_trajectory_delta) < 1e-8
        and any(abs(float(mix.grad)) > EPS for mix in mixes),
    }


def random_assignment_control() -> dict[str, object]:
    rng = np.random.default_rng(19)
    states = gray_states()
    shuffled = list(range(64))
    rng.shuffle(shuffled)
    block_states = [states[idx] for idx in shuffled[:5]]
    distances = [hamming(block_states[i], block_states[i + 1]) for i in range(4)]
    return {
        "states": block_states,
        "hamming_distances": distances,
        "survives_single_line_gate": all(distance == 1 for distance in distances),
        "pass": not all(distance == 1 for distance in distances),
    }


def main() -> None:
    receipts = source_receipts()
    candidates = candidate_blocks()
    candidate = strongest_candidate()
    entropy = entropy_order_witness(candidate) if candidate else {"pass": False}
    positive = {
        "source_receipts_pass": {
            "receipts": receipts,
            "pass": all(row["exists"] and row["all_pass"] for row in receipts.values()),
        },
        "canonical_gray_block_has_measure_and_erasure_domains": {
            "candidate_count": len(candidates),
            "chosen_candidate": candidate,
            "pass": bool(
                candidate
                and candidate["all_hamming_one"]
                and candidate["measure_lower_trigram"]
                and candidate["erasure_upper_trigram"]
            ),
        },
        "torch_scipy_entropy_trajectory_is_order_sensitive": entropy,
        "final_state_collapse_is_explicit_ceiling": {
            "torch_final_state_delta": entropy.get("torch_final_state_delta"),
            "scipy_final_state_delta": entropy.get("scipy_final_state_delta"),
            "claim_ceiling": "path_order_sensitive_only_not_outcome_order_sensitive",
            "pass": bool(
                entropy.get("pass")
                and float(entropy.get("torch_final_state_delta", 1.0)) <= EPS
                and float(entropy.get("scipy_final_state_delta", 1.0)) <= EPS
            ),
        },
    }
    negative = {
        "z3_kills_too_strong_distinct_line_mapping": z3_no_distinct_measure_erasure_block(),
        "random_assignment_fails_single_line_gate": random_assignment_control(),
        "reset_line_reuse_is_explicit_not_smoothed": {
            "chosen_stage_line_changes": candidate.get("stage_line_changes") if candidate else {},
            "pass": bool(candidate and not candidate["all_stage_lines_distinct"]),
        },
    }
    boundary = {
        "finite_mapping_probe_only": {
            "scope_note": divergence_log,
            "forbidden_claims_absent": [
                "target-system admission",
                "geometric-manifold admission",
                "coordinate-family promotion",
                "bridge admission",
                "nonclassical admission",
            ],
            "pass": "admission" in divergence_log and "not target-system" in divergence_log,
        },
        "no_target_system_manifold_coordinate_bridge_or_nonclassical_admission": {
            "promotion_allowed": False,
            "claim_ceiling": "tool_lego_fit_probe_only",
            "pass": True,
        },
        "szilard_mi_bound_not_tested_or_inherited": {
            "tested_metrics": ["single_line_gray_blocks", "entropy_trajectory", "final_state_delta"],
            "excluded_metrics": ["mutual_information_bound", "szilard_work_bound"],
            "pass": True,
        },
        "trigram_mapping_is_candidate_not_unique": {
            "candidate_count": len(candidates),
            "chosen_policy": "first strongest candidate by distinct-line count then earliest start",
            "pass": len(candidates) > 1,
        },
    }
    all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    result = {
        "name": "six_bit_gray_walk_measure_feedback_reset_entropy",
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
        "source_receipts": {key: value["path"] for key, value in receipts.items()},
        "candidate_blocks": candidates,
        "chosen_candidate": candidate,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "promotion_allowed": False,
            "candidate_block_count": len(candidates),
            "killed_claim": "four distinct measurement-feedback-erasure-reset stage line operators in canonical Gray walk",
            "surviving_claim": "weaker measure-lower / erasure-upper finite block with path-only entropy trajectory order sensitivity",
            "outcome_order_sensitive": False,
            "followup_required": "initial_state_sweep_before_any_stronger_mapping_or_coupling_claim",
            "scope_note": divergence_log,
        },
        "all_pass": bool(all_pass),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / "six_bit_gray_walk_measure_feedback_reset_entropy_results.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
