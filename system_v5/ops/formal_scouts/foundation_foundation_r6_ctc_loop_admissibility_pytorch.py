#!/usr/bin/env python3
"""PyTorch torch.func sensitivity leg for foundation R6 CTC loop admissibility."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_ctc_loop_admissibility"
OBJECT_ID = "foundation_foundation_r6_ctc_loop_admissibility_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_ctc_loop_admissibility_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_ctc_loop_admissibility_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
EVENTS = ["A_prepare", "B_apply", "C_measure", "D_record"]
RDTYPE = torch.float64

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "supportive float64 finite adjacency and closed-walk score tensors"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity of the loop score with respect to installed retrocausal edge weight"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing"}


def base_adjacency(drop_forward: bool = False, force_commutative: bool = False) -> torch.Tensor:
    adj = torch.zeros((4, 4), dtype=RDTYPE)
    edges = [(0, 1), (1, 2), (2, 3)]
    if drop_forward:
        edges = [(0, 1), (2, 3)]
    if force_commutative:
        edges = sorted(set([*edges, *[(dst, src) for src, dst in edges]]))
    for src, dst in edges:
        adj[src, dst] = 1.0
    return adj


def loop_score(retro_weight: torch.Tensor, *, drop_forward: bool = False, force_commutative: bool = False) -> torch.Tensor:
    adj = base_adjacency(drop_forward=drop_forward, force_commutative=force_commutative).clone()
    adj[3, 0] = retro_weight
    closed_walk_4 = torch.trace(adj @ adj @ adj @ adj)
    return closed_walk_4


def quotient_from_scores(scores: dict[str, float]) -> dict[str, Any]:
    groups: dict[str, list[str]] = {}
    for name, score in scores.items():
        loop = abs(score) > 1.0e-10
        groups.setdefault(str(loop), []).append(name)
    return {
        "loop_admissibility_class_count": len(groups),
        "loop_admissibility_classes": [
            {"class_id": "loop_excluded", "loop_admissible": False, "members": sorted(groups.get("False", []))},
            {"class_id": "loop_admissible", "loop_admissible": True, "members": sorted(groups.get("True", []))},
        ],
    }


def constraints_report() -> dict[str, Any]:
    details = []
    dim = len(EVENTS)
    for idx, event_id in enumerate(EVENTS):
        state = torch.zeros((dim, 1), dtype=RDTYPE)
        state[idx, 0] = 1.0
        rho = state @ state.T
        eigs = torch.linalg.eigvalsh(rho)
        details.append(
            {
                "id": event_id,
                "trace_residual": float(torch.abs(torch.trace(rho) - 1.0).detach().item()),
                "hermitian_residual": float(torch.linalg.vector_norm(rho - rho.T).detach().item()),
                "min_eigenvalue": float(torch.min(eigs).detach().item()),
                "normalization_residual": float(torch.abs((state.T @ state)[0, 0] - 1.0).detach().item()),
                "psd": bool(float(torch.min(eigs).detach().item()) >= -1.0e-12),
            }
        )
    return {
        "trace_one": all(row["trace_residual"] <= 1.0e-12 for row in details),
        "hermitian": all(row["hermitian_residual"] <= 1.0e-12 for row in details),
        "psd": all(row["psd"] for row in details),
        "normalized": all(row["normalization_residual"] <= 1.0e-12 for row in details),
        "details": details,
    }


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(RDTYPE)
    theta_zero = torch.tensor(0.0, dtype=RDTYPE)
    theta_one = torch.tensor(1.0, dtype=RDTYPE)
    eps = torch.tensor(1.0e-6, dtype=RDTYPE)

    bare_score = loop_score(theta_zero)
    retro_score = loop_score(theta_one)
    drop_score = loop_score(theta_one, drop_forward=True)
    commutative_score = loop_score(theta_zero, force_commutative=True)
    jac_at_zero = jacrev(loop_score)(theta_zero)
    jac_at_one = jacrev(loop_score)(theta_one)
    drop_jac = jacrev(lambda t: loop_score(t, drop_forward=True))(theta_one)
    commutative_jac = jacrev(lambda t: loop_score(t, force_commutative=True))(theta_zero)
    finite_diff = (loop_score(eps) - loop_score(-eps)) / (2.0 * eps)
    finite_diff_residual = torch.abs(jac_at_zero - finite_diff)
    constraints = constraints_report()
    scores = {
        "bare_order": float(bare_score.detach().item()),
        "retrocausal_edge_installed": float(retro_score.detach().item()),
        "retro_edge_but_B_to_C_dropped": float(drop_score.detach().item()),
        "forced_commutative_bare_edges": float(commutative_score.detach().item()),
    }
    quotient = quotient_from_scores(scores)
    genuine_independent_check = bool(
        abs(float(jac_at_zero.detach().item())) > 1.0e-10
        and abs(float(jac_at_one.detach().item())) > 1.0e-10
        and abs(float(drop_jac.detach().item())) <= 1.0e-10
        and float(finite_diff_residual.detach().item()) <= 1.0e-9
    )
    all_pass = (
        READS_PEER_RESULT is False
        and constraints["trace_one"]
        and constraints["hermitian"]
        and constraints["psd"]
        and constraints["normalized"]
        and float(bare_score.detach().item()) == 0.0
        and float(retro_score.detach().item()) > 0.0
        and float(drop_score.detach().item()) == 0.0
        and float(commutative_score.detach().item()) > 0.0
        and genuine_independent_check
    )
    return {
        "schema_version": "engine_leg_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "python_executable": sys.executable,
        "packages_used": ["torch", "torch.func", "json", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "torch_version": torch.__version__,
        "torch_dtype": str(torch.get_default_dtype()),
        "claim_ceiling": "Scratch PyTorch differentiable sensitivity check for finite R6 loop installation only; no authority, no promotion, no formal admission.",
        "M": {
            "explicit_probe_family": [
                "edge(A_prepare,B_apply)",
                "edge(B_apply,C_measure)",
                "edge(C_measure,D_record)",
                "edge(D_record,A_prepare)",
                "closed_directed_loop_exists",
                "jacrev(retrocausal_edge_weight -> trace(A^4))",
            ],
            "measurement_object": "finite weighted directed adjacency for sensitivity only",
        },
        "C": {
            "state_constraints": ["trace=1", "PSD", "Hermiticity", "normalization"],
            "state_constraint_values": constraints,
            "rung_specific_constraint": "Loop score is trace(A^4) on the four-event order; retro edge weight D->A is the differentiable installed parameter.",
        },
        "S": {"carrier": "finite weighted directed causal-order scenarios over four events", "events": EVENTS},
        "S_quotient": quotient,
        "differentiable_check": {
            "genuine_independent_check": genuine_independent_check,
            "loop_score": "trace(A^4), so A->B->C->D->A contributes four closed-walk diagonal hits when the retro edge is installed",
            "retro_weight_at_bare": float(theta_zero.detach().item()),
            "retro_weight_at_installed": float(theta_one.detach().item()),
            "jacrev_at_bare": float(jac_at_zero.detach().item()),
            "jacrev_at_installed": float(jac_at_one.detach().item()),
            "finite_difference_at_bare": float(finite_diff.detach().item()),
            "finite_difference_residual": float(finite_diff_residual.detach().item()),
            "drop_forward_edge_jacrev": float(drop_jac.detach().item()),
            "force_commutativity_jacrev": float(commutative_jac.detach().item()),
        },
        "values": {
            "bare_loop_score": float(bare_score.detach().item()),
            "retrocausal_edge_loop_score": float(retro_score.detach().item()),
            "drop_forward_edge_loop_score": float(drop_score.detach().item()),
            "forced_commutative_loop_score": float(commutative_score.detach().item()),
            "bare_loop_admissible": bool(float(bare_score.detach().item()) > 0.0),
            "retrocausal_edge_loop_admissible": bool(float(retro_score.detach().item()) > 0.0),
            "drop_forward_edge_loop_admissible": bool(float(drop_score.detach().item()) > 0.0),
            "forced_commutative_loop_admissible": bool(float(commutative_score.detach().item()) > 0.0),
            "bare_loop_int": int(float(bare_score.detach().item()) > 0.0),
            "retro_loop_int": int(float(retro_score.detach().item()) > 0.0),
        },
        "negative_control_flip": {
            "bare_score": float(bare_score.detach().item()),
            "retrocausal_edge_score": float(retro_score.detach().item()),
            "drop_forward_edge_after_retro_score": float(drop_score.detach().item()),
            "forced_commutative_bare_score": float(commutative_score.detach().item()),
            "drop_forward_edge_kills_retro_loop": float(drop_score.detach().item()) == 0.0,
            "force_commutativity_changes_bare_result": float(commutative_score.detach().item()) > float(bare_score.detach().item()),
            "jacrev_nonzero_for_retro_installation": abs(float(jac_at_zero.detach().item())) > 1.0e-10,
        },
        "forced_vs_installed": "INSTALLED",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    values = result["values"]
    diff = result["differentiable_check"]
    print(
        "FOUNDATION_R6_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"bare_score={values['bare_loop_score']} retro_score={values['retrocausal_edge_loop_score']} "
        f"drop_score={values['drop_forward_edge_loop_score']} jac={diff['jacrev_at_bare']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
