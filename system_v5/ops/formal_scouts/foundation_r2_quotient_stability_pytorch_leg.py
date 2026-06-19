#!/usr/bin/env python3
"""PyTorch support leg for foundation R2 quotient stability v2."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


OBJECT_ID = "foundation_r2_quotient_stability_v2"
ENGINE = "pytorch"
RUNG_ID = "foundation_r2_quotient_stability_v2"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r2_quotient_stability_pytorch_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r2_quotient_stability_pytorch_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "supportive complex128 carrier density matrices and operation images"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity of class-preservation residual"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing"}

CDTYPE = torch.complex128
RDTYPE = torch.float64
I2 = torch.eye(2, dtype=CDTYPE)
PZ0 = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=CDTYPE)
U_H = torch.tensor([[1.0, 1.0], [1.0, -1.0]], dtype=CDTYPE) / torch.sqrt(torch.tensor(2.0, dtype=RDTYPE))


def ket(values: list[complex]) -> torch.Tensor:
    vec = torch.tensor(values, dtype=CDTYPE)
    return vec / torch.sqrt(torch.vdot(vec, vec).real).to(CDTYPE)


def density(vec: torch.Tensor) -> torch.Tensor:
    return torch.outer(vec, torch.conj(vec))


def states() -> dict[str, torch.Tensor]:
    s2 = torch.sqrt(torch.tensor(2.0, dtype=RDTYPE)).to(CDTYPE)
    return {
        "pure_z0": ket([1.0 + 0.0j, 0.0 + 0.0j]),
        "pure_z1": ket([0.0 + 0.0j, 1.0 + 0.0j]),
        "pure_x_plus": ket([1.0 + 0.0j, 1.0 + 0.0j]),
        "pure_x_minus": ket([1.0 + 0.0j, -1.0 + 0.0j]),
        "pure_y_plus": torch.tensor([1.0 + 0.0j, 0.0 + 1.0j], dtype=CDTYPE) / s2,
        "pure_y_minus": torch.tensor([1.0 + 0.0j, 0.0 - 1.0j], dtype=CDTYPE) / s2,
    }


def candidates() -> list[dict[str, Any]]:
    rows = [{"id": name, "rho": density(vec)} for name, vec in states().items()]
    rows.append({"id": "maximally_mixed", "rho": 0.5 * I2})
    return rows


def phase_unitary(theta: torch.Tensor) -> torch.Tensor:
    zero_real = torch.zeros((), dtype=RDTYPE)
    zero_complex = torch.zeros((), dtype=CDTYPE)
    one = torch.exp(1j * zero_real)
    phase = torch.exp(1j * theta)
    return torch.stack([torch.stack([one, zero_complex]), torch.stack([zero_complex, phase])])


def apply_unitary(rho: torch.Tensor, unitary: torch.Tensor) -> torch.Tensor:
    return unitary @ rho @ torch.conj(unitary.T)


def unitary_residual(unitary: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(torch.conj(unitary.T) @ unitary - I2).real)


def z0_expectation(rho: torch.Tensor) -> torch.Tensor:
    return torch.trace(rho @ PZ0).real


def expectation_table(rows: list[dict[str, Any]]) -> list[list[float]]:
    return [[round(float(z0_expectation(row["rho"])), 12)] for row in rows]


def image_rows(rows: list[dict[str, Any]], unitary: torch.Tensor) -> list[dict[str, Any]]:
    return [{"id": row["id"], "rho": apply_unitary(row["rho"], unitary)} for row in rows]


def relation_from_table(table: list[list[float]]) -> list[list[bool]]:
    return [[table[i] == table[j] for j in range(len(table))] for i in range(len(table))]


def quotient(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    classes: dict[str, dict[str, Any]] = {}
    for row, sig in zip(rows, expectation_table(rows), strict=True):
        key = json.dumps(sig, sort_keys=True, separators=(",", ":"))
        classes.setdefault(key, {"members": [], "signature": sig})
        classes[key]["members"].append(row["id"])
    ordered = [
        {"class_id": f"{name}_q{idx}", "members": sorted(classes[key]["members"]), "signature": classes[key]["signature"]}
        for idx, key in enumerate(sorted(classes))
    ]
    return {"name": name, "probe_names": ["Z0"], "class_count": len(ordered), "classes": ordered}


def dropped_quotient(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "name": "dropped_M_empty",
        "probe_names": [],
        "class_count": 1,
        "classes": [{"class_id": "dropped_M_empty_q0", "members": sorted(row["id"] for row in rows), "signature": []}],
    }


def stability_report(base_rows: list[dict[str, Any]], unitary: torch.Tensor) -> dict[str, Any]:
    base_rel = relation_from_table(expectation_table(base_rows))
    img_rel = relation_from_table(expectation_table(image_rows(base_rows, unitary)))
    ids = [row["id"] for row in base_rows]
    violating = [
        {"left": ids[i], "right": ids[j]}
        for i in range(len(ids))
        for j in range(len(ids))
        if base_rel[i][j] and not img_rel[i][j]
    ]
    return {"stable": not violating, "violating_pairs": violating}


def class_residual_for_pair(theta: torch.Tensor) -> torch.Tensor:
    st = states()
    unitary = phase_unitary(theta)
    left = apply_unitary(density(st["pure_x_plus"]), unitary)
    right = apply_unitary(density(st["pure_x_minus"]), unitary)
    diff = z0_expectation(left) - z0_expectation(right)
    return diff * diff


def hadamard_residual_for_pair() -> torch.Tensor:
    st = states()
    left = apply_unitary(density(st["pure_x_plus"]), U_H)
    right = apply_unitary(density(st["pure_x_minus"]), U_H)
    diff = z0_expectation(left) - z0_expectation(right)
    return diff * diff


def main() -> int:
    rows = candidates()
    theta = torch.tensor(torch.pi / 2.0, dtype=RDTYPE)
    admitted_unitary = phase_unitary(theta)
    q = quotient(rows, "active_M_Z0")
    dropped_q = dropped_quotient(rows)
    admitted_stability = stability_report(rows, admitted_unitary)
    nonadmitted_stability = stability_report(rows, U_H)
    admitted_residual = class_residual_for_pair(theta)
    admitted_jacrev = jacrev(class_residual_for_pair)(theta)
    nonadmitted_residual = hadamard_residual_for_pair()
    proof_encoding_note = (
        "PyTorch support leg computes the same Tr(rho_i O) expectations and uses torch.func.jacrev for "
        "class-preservation residual sensitivity; z3/cvc5 Real expectation-variable proof is run in the JAX "
        "crossover leg and summarized by the envelope, with no precomputed Bool relation matrix."
    )
    all_pass = bool(
        q["class_count"] == 3
        and dropped_q["class_count"] == 1
        and admitted_stability["stable"]
        and not nonadmitted_stability["stable"]
        and abs(float(admitted_residual)) <= TOL
        and abs(float(admitted_jacrev)) <= TOL
        and float(nonadmitted_residual) > 0.9
    )
    result = {
        "schema_version": "engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "engine": ENGINE,
        "rung_id": RUNG_ID,
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "python_executable": sys.executable,
        "packages_used": ["torch", "torch.func", "json", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "M": {"active_probe_family": ["Z0"], "probes": [{"name": "Z0", "effect": "|0><0|"}], "dropped_probe_family": []},
        "C": {
            "state_constraints": ["trace=1", "PSD", "Hermitian"],
            "admitted_operation": "phase_Z_pi_over_2",
            "nonadmitted_control_operation": "Hadamard",
            "rung_specific_constraint": "active-M equivalence must be stable under admitted operations",
            "operation_constraints_hold": {
                "admitted_unitary_residual": unitary_residual(admitted_unitary),
                "nonadmitted_control_unitary_residual": unitary_residual(U_H),
                "admitted_operation_stable": admitted_stability["stable"],
                "nonadmitted_operation_stable": nonadmitted_stability["stable"],
            },
        },
        "S": {"ids": [row["id"] for row in rows], "size": len(rows), "density_matrix_shape": [2, 2]},
        "expectations": {"active_M": expectation_table(rows), "row_ids": [row["id"] for row in rows], "probe_order": ["Z0"]},
        "quotient": q,
        "S_quotient": {"classes": q["classes"], "class_count": q["class_count"]},
        "stability": {"admitted_operation": admitted_stability, "nonadmitted_operation": nonadmitted_stability},
        "differentiable_check": {
            "support_only": False,
            "equivalent_pair": ["pure_x_plus", "pure_x_minus"],
            "residual_quantity": "squared Z0 expectation difference after operation",
            "admitted_theta": float(theta),
            "admitted_residual": float(admitted_residual),
            "admitted_jacrev": float(admitted_jacrev),
            "nonadmitted_hadamard_residual": float(nonadmitted_residual),
            "genuine_independent_check": True,
        },
        "negative_control_flip": {
            "active_M_class_count": q["class_count"],
            "drop_M_class_count": dropped_q["class_count"],
            "drop_M_changed_quotient": q["class_count"] > dropped_q["class_count"],
            "admitted_operation_stable": admitted_stability["stable"],
            "nonadmitted_operation_stable": nonadmitted_stability["stable"],
            "z3_main_verdict": "not_run_in_pytorch_support_leg",
            "cvc5_main_verdict": "not_run_in_pytorch_support_leg",
            "z3_nonadmitted_violation_verdict": "not_run_in_pytorch_support_leg",
            "cvc5_nonadmitted_violation_verdict": "not_run_in_pytorch_support_leg",
        },
        "proof_encoding_note": proof_encoding_note,
        "values": {
            "class_count": q["class_count"],
            "drop_M_class_count": dropped_q["class_count"],
            "admitted_stable": admitted_stability["stable"],
            "nonadmitted_stable": nonadmitted_stability["stable"],
            "admitted_residual": float(admitted_residual),
            "admitted_jacrev": float(admitted_jacrev),
            "nonadmitted_residual": float(nonadmitted_residual),
        },
        "all_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_R2_PYTORCH_V2_DONE "
        f"all_pass={str(all_pass).lower()} class_count={q['class_count']} drop_M_class_count={dropped_q['class_count']} "
        f"admitted_residual={float(admitted_residual)} admitted_jacrev={float(admitted_jacrev)} "
        f"nonadmitted_residual={float(nonadmitted_residual)}"
    )
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
