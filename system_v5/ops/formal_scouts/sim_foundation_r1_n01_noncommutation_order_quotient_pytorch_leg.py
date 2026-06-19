#!/usr/bin/env python3
"""PyTorch support leg for R1 N01 noncommutation ordered quotient.

Scratch diagnostic only. PyTorch contributes a complex-tensor implementation
and a torch.func derivative of the order-gap observable.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import sys
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import grad, jacrev

OBJECT_ID = "foundation_r1_n01_noncommutation_order_quotient_v1"
ENGINE = "pytorch"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_foundation_r1_n01_noncommutation_order_quotient_pytorch_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r1_n01_noncommutation_order_quotient_pytorch_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result
TOL = 1.0e-10
DTYPE = torch.complex128

OUTCOME_LABELS = ["++", "+-", "-+", "--"]
STATE_IDS = ["ket0", "ket1", "ket_plus", "ket_minus", "ket_i_plus", "maximally_mixed"]
PROBE_IDS = ["Z", "X", "Z_duplicate"]
ORDERED_HISTORIES = ["Z_then_X", "X_then_Z", "Z_then_Z_duplicate", "Z_duplicate_then_Z"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 finite qubit density matrices, projectors, ordered projective histories, and commutator norms",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing autograd derivative and jacrev check for a finite order-gap observable under white-noise mixing",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Pauli commutator and rational ket0 order-gap check independent of torch numerics",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, paths, timestamps, and finite constants",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "load_bearing",
    "sympy": "load_bearing",
    "Python stdlib": "supportive",
}


def ket(values: list[complex]) -> torch.Tensor:
    vec = torch.tensor(values, dtype=DTYPE)
    return vec / torch.linalg.vector_norm(vec)


def density(vec: torch.Tensor) -> torch.Tensor:
    return torch.outer(vec, vec.conj())


def finite_torch_object() -> tuple[dict[str, torch.Tensor], dict[str, list[torch.Tensor]], torch.Tensor, torch.Tensor]:
    ket0 = ket([1.0 + 0j, 0.0 + 0j])
    ket1 = ket([0.0 + 0j, 1.0 + 0j])
    ket_plus = ket([1.0 + 0j, 1.0 + 0j])
    ket_minus = ket([1.0 + 0j, -1.0 + 0j])
    ket_i_plus = ket([1.0 + 0j, 1.0j])
    states = {
        "ket0": density(ket0),
        "ket1": density(ket1),
        "ket_plus": density(ket_plus),
        "ket_minus": density(ket_minus),
        "ket_i_plus": density(ket_i_plus),
        "maximally_mixed": torch.eye(2, dtype=DTYPE) / 2.0,
    }
    pz = [density(ket0), density(ket1)]
    px = [density(ket_plus), density(ket_minus)]
    projectors = {"Z": pz, "X": px, "Z_duplicate": pz}
    z_op = pz[0] - pz[1]
    x_op = px[0] - px[1]
    return states, projectors, z_op, x_op


def joint_distribution(rho: torch.Tensor, first: list[torch.Tensor], second: list[torch.Tensor]) -> list[float]:
    probs: list[float] = []
    for p1 in first:
        branch = p1 @ rho @ p1
        for p2 in second:
            probs.append(float(torch.real(torch.trace(p2 @ branch)).detach().cpu().item()))
    return probs


def joint_distribution_tensor(rho: torch.Tensor, first: list[torch.Tensor], second: list[torch.Tensor]) -> torch.Tensor:
    values = []
    for p1 in first:
        branch = p1 @ rho @ p1
        for p2 in second:
            values.append(torch.real(torch.trace(p2 @ branch)))
    return torch.stack(values)


def tv_gap(left: list[float], right: list[float]) -> float:
    return 0.5 * sum(abs(a - b) for a, b in zip(left, right))


def tv_gap_tensor(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return 0.5 * torch.sum(torch.abs(left - right))


def rounded(values: list[float], digits: int = 12) -> list[float]:
    return [round(float(v), digits) for v in values]


def quotient_classes(rows: list[dict[str, Any]], signature_key: str) -> dict[str, Any]:
    grouped: dict[str, list[str]] = {}
    for row in rows:
        key = "|".join(str(x) for x in row[signature_key])
        grouped.setdefault(key, []).append(row["state_id"])
    classes = [
        {"class_id": idx + 1, "signature_key": key, "state_ids": sorted(grouped[key])}
        for idx, key in enumerate(sorted(grouped))
    ]
    return {"class_count": len(classes), "classes": classes}


def order_gap_for_mix(lam: torch.Tensor) -> torch.Tensor:
    states, projectors, _, _ = finite_torch_object()
    rho = (1.0 - lam.to(DTYPE)) * states["ket0"] + lam.to(DTYPE) * torch.eye(2, dtype=DTYPE) / 2.0
    zx = joint_distribution_tensor(rho, projectors["Z"], projectors["X"])
    xz = joint_distribution_tensor(rho, projectors["X"], projectors["Z"])
    return tv_gap_tensor(zx, xz)


def sympy_exact_checks() -> dict[str, Any]:
    z = sp.Matrix([[1, 0], [0, -1]])
    x = sp.Matrix([[0, 1], [1, 0]])
    comm_zx = z * x - x * z
    comm_zz = z * z - z * z
    zx = [sp.Rational(1, 2), sp.Rational(1, 2), sp.Rational(0), sp.Rational(0)]
    xz = [sp.Rational(1, 4), sp.Rational(1, 4), sp.Rational(1, 4), sp.Rational(1, 4)]
    gap = sp.Rational(1, 2) * sum(abs(a - b) for a, b in zip(zx, xz))
    return {
        "commutator_ZX": str(comm_zx),
        "commutator_ZZ": str(comm_zz),
        "ZX_nonzero": any(value != 0 for value in comm_zx),
        "ZZ_zero": all(value == 0 for value in comm_zz),
        "ket0_tv_gap_exact": str(gap),
        "pass": any(value != 0 for value in comm_zx) and all(value == 0 for value in comm_zz) and gap == sp.Rational(1, 2),
    }


def build_result() -> dict[str, Any]:
    states, projectors, z_op, x_op = finite_torch_object()
    comm_zx = z_op @ x_op - x_op @ z_op
    comm_zz = z_op @ z_op - z_op @ z_op
    comm_zx_norm = float(torch.linalg.vector_norm(comm_zx).detach().cpu().item())
    comm_zz_norm = float(torch.linalg.vector_norm(comm_zz).detach().cpu().item())

    rows: list[dict[str, Any]] = []
    for state_id in STATE_IDS:
        rho = states[state_id]
        zx = joint_distribution(rho, projectors["Z"], projectors["X"])
        xz = joint_distribution(rho, projectors["X"], projectors["Z"])
        zz = joint_distribution(rho, projectors["Z"], projectors["Z_duplicate"])
        zdupz = joint_distribution(rho, projectors["Z_duplicate"], projectors["Z"])
        noncommuting_gap = tv_gap(zx, xz)
        control_gap = tv_gap(zz, zdupz)
        rows.append(
            {
                "state_id": state_id,
                "Z_then_X": rounded(zx),
                "X_then_Z": rounded(xz),
                "Z_then_Z_duplicate": rounded(zz),
                "Z_duplicate_then_Z": rounded(zdupz),
                "noncommuting_order_gap": noncommuting_gap,
                "commuting_control_order_gap": control_gap,
                "noncommuting_quotient_signature": rounded([*zx, *xz, noncommuting_gap]),
                "commuting_control_quotient_signature": rounded([*zz, *zdupz, control_gap]),
            }
        )

    noncommuting_quotient = quotient_classes(rows, "noncommuting_quotient_signature")
    commuting_quotient = quotient_classes(rows, "commuting_control_quotient_signature")
    witness = next(row for row in rows if row["state_id"] == "ket0")
    noncommuting_gap_max = max(row["noncommuting_order_gap"] for row in rows)
    commuting_gap_max = max(row["commuting_control_order_gap"] for row in rows)
    refined = noncommuting_quotient["class_count"] > commuting_quotient["class_count"]

    lam = torch.tensor(0.0, dtype=torch.float64)
    order_gap_value = order_gap_for_mix(lam)
    order_gap_grad = grad(order_gap_for_mix)(lam)
    order_gap_jacrev = jacrev(order_gap_for_mix)(lam)
    expected_gap_grad = -0.5
    autograd_checks = {
        "observable": "TV gap between Z_then_X and X_then_Z for rho(lambda)=(1-lambda)|0><0|+lambda*I/2",
        "lambda": float(lam.detach().cpu().item()),
        "order_gap": float(order_gap_value.detach().cpu().item()),
        "grad": float(order_gap_grad.detach().cpu().item()),
        "jacrev": float(order_gap_jacrev.detach().cpu().item()),
        "expected_grad": expected_gap_grad,
        "grad_residual": abs(float(order_gap_grad.detach().cpu().item()) - expected_gap_grad),
        "jacrev_residual": abs(float(order_gap_jacrev.detach().cpu().item()) - expected_gap_grad),
        "pass": abs(float(order_gap_value.detach().cpu().item()) - witness["noncommuting_order_gap"]) <= TOL
        and abs(float(order_gap_grad.detach().cpu().item()) - expected_gap_grad) <= TOL
        and abs(float(order_gap_jacrev.detach().cpu().item()) - expected_gap_grad) <= TOL,
    }
    sympy_checks = sympy_exact_checks()

    negative_controls = {
        "commuting_duplicate_Z_has_zero_commutator": {"pass": comm_zz_norm <= TOL, "commutator_norm": comm_zz_norm},
        "commuting_duplicate_Z_has_zero_order_gap_all_states": {"pass": commuting_gap_max <= TOL, "max_order_gap": commuting_gap_max},
        "noncommuting_ZX_has_nonzero_commutator": {"pass": comm_zx_norm > TOL, "commutator_norm": comm_zx_norm},
        "finite_witness_ket0_has_nonzero_order_gap": {"pass": witness["noncommuting_order_gap"] > TOL, "state_id": "ket0", "order_gap": witness["noncommuting_order_gap"]},
        "noncommuting_quotient_refines_commuting_control": {
            "pass": refined,
            "noncommuting_class_count": noncommuting_quotient["class_count"],
            "commuting_control_class_count": commuting_quotient["class_count"],
        },
    }
    all_pass = bool(
        all(row["commuting_control_order_gap"] <= TOL for row in rows)
        and witness["noncommuting_order_gap"] > TOL
        and comm_zx_norm > TOL
        and comm_zz_norm <= TOL
        and refined
        and autograd_checks["pass"]
        and sympy_checks["pass"]
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
        and READS_PEER_RESULT is False
    )

    return {
        "object_id": OBJECT_ID,
        "engine": ENGINE,
        "executable": sys.executable,
        "interpreter": sys.executable,
        "backend": "pytorch_torch_func_sympy",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "finite_object": {
            "hilbert_dimension": 2,
            "state_ids": STATE_IDS,
            "named_positive_witness": "ket0",
            "probe_ids": PROBE_IDS,
            "projective_probes": {"Z": "computational-basis rank-1 projectors", "X": "Hadamard-basis rank-1 projectors", "Z_duplicate": "duplicate/relabel of Z projectors"},
            "ordered_histories": ORDERED_HISTORIES,
            "outcome_labels": OUTCOME_LABELS,
        },
        "ordered_histories": {"rows": rows, "witness_ket0": witness},
        "quotient": {
            "definition": "States are quotiented by rounded ordered-history outcome-distribution signatures. Noncommuting uses Z_then_X and X_then_Z; control uses duplicate Z histories.",
            "noncommuting": noncommuting_quotient,
            "commuting_control": commuting_quotient,
            "strict_refinement_observed": refined,
        },
        "class_signatures": {"outcome_order": OUTCOME_LABELS, "state_rows": rows},
        "noncommuting": {
            "probe_pair": "Z,X",
            "commutator_norm": comm_zx_norm,
            "commutator_norm_fro": comm_zx_norm,
            "order_gap": witness["noncommuting_order_gap"],
            "order_gap_max": noncommuting_gap_max,
            "witness_state_id": "ket0",
            "classification": "nonzero_commutator_nonzero_order_gap_refined_quotient",
        },
        "commuting_control": {
            "probe_pair": "Z,Z_duplicate",
            "commutator_norm": comm_zz_norm,
            "commutator_norm_fro": comm_zz_norm,
            "order_gap": commuting_gap_max,
            "order_gap_max": commuting_gap_max,
            "classification": "zero_commutator_zero_order_gap_coarser_quotient",
        },
        "negative_controls": negative_controls,
        "finite_certificates": {"sympy": sympy_checks, "torch_func_order_gap_autograd": autograd_checks},
        "packages": {
            "load_bearing": ["torch", "torch.func", "sympy"],
            "supportive": ["json", "pathlib"],
            "control_only": [],
            "missing_required": [],
        },
        "package_observables": {
            "torch": "Complex tensor density/projector histories and commutator norms.",
            "torch.func": "Gradient and jacrev of the finite order-gap observable under white-noise mixing.",
            "sympy": "Exact commutator and rational ket0 order-gap certificate.",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "R1 N01 scratch diagnostic only: finite one-qubit projective-probe ordered-history quotient. PyTorch is a support/third substrate, not Julia authority. Not full M(C), not R0/R1-F01/R2, not formal admission, not canonical, not bridge, not axis, and not physics/gravity/entropy-master evidence.",
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"noncommuting_order_gap={result['noncommuting']['order_gap']} "
        f"commuting_control_order_gap={result['commuting_control']['order_gap']} "
        f"order_gap_grad={result['finite_certificates']['torch_func_order_gap_autograd']['grad']} "
        f"noncommuting_classes={result['quotient']['noncommuting']['class_count']} "
        f"commuting_control_classes={result['quotient']['commuting_control']['class_count']} "
        f"reads_peer_result={str(result['reads_peer_result']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
