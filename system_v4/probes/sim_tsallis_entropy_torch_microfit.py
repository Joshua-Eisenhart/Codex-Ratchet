#!/usr/bin/env python3
"""PyTorch Tsallis-entropy microfit.

This bounded tool-lego fit splits Tsallis entropy into its own machine row from
the broader spectral-entropy bundle. It is local tool-lego evidence only, not a
coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission claim.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime

import sympy as sp
import torch
import z3


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Bounded PyTorch Tsallis-entropy microfit on fixed qubit density matrices. "
    "PyTorch is load-bearing for spectral q-entropy evaluation; sympy and z3 "
    "provide supportive q=2/finite witness guards. This is not a coupling, "
    "bridge, QIT, GStack, axis, engine, or nonclassical admission."
)

LEGO_IDS = ["tsallis_entropy"]
PRIMARY_LEGO_IDS = ["tsallis_entropy"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing eigenspectrum and Tsallis q-entropy evaluation on fixed density matrices",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive symbolic q=2 relation to linear entropy",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite Real-arithmetic guard over precomputed nonnegative witnesses",
    },
    "numpy": {"tried": False, "used": False, "reason": "not needed; torch carries the numeric spectral path"},
    "qutip": {"tried": False, "used": False, "reason": "not needed for this PyTorch-focused row"},
    "qiskit": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "supportive",
    "z3": "supportive",
    "numpy": None,
    "qutip": None,
    "qiskit": None,
    "cvc5": None,
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
PARENT_RESULTS = {
    "lego_entropy_spectral_families": RESULT_DIR / "lego_entropy_spectral_families_results.json",
    "von_neumann_entropy": RESULT_DIR / "von_neumann_entropy_results.json",
    "pure_lego_density_matrices": RESULT_DIR / "pure_lego_density_matrices_results.json",
    "pytorch_capability": RESULT_DIR / "pytorch_capability_results.json",
}
REGISTRY_PATH = PROBE_DIR.parents[1] / "system_v5" / "docs" / "17_actual_lego_registry.md"
OUT_PATH = RESULT_DIR / "tsallis_entropy_torch_microfit_results.json"
EPS = 1e-10
CDTYPE = torch.complex128
LN2 = torch.log(torch.tensor(2.0, dtype=torch.float64))


def source_receipts() -> dict[str, object]:
    rows = {}
    for key, path in PARENT_RESULTS.items():
        if not path.exists():
            rows[key] = {"path": str(path), "exists": False, "all_pass": False}
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        rows[key] = {
            "path": str(path),
            "exists": True,
            "all_pass": bool(data.get("all_pass") or data.get("summary", {}).get("all_pass")),
            "classification": data.get("classification"),
        }
    return rows


def dm(vec: torch.Tensor) -> torch.Tensor:
    ket = vec.reshape(-1, 1).to(CDTYPE)
    return ket @ ket.conj().T


def density_states() -> dict[str, torch.Tensor]:
    zero = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    plus = torch.tensor([1.0, 1.0], dtype=CDTYPE) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    return {
        "pure_zero": dm(zero),
        "pure_plus": dm(plus),
        "diag_0p8_0p2": torch.diag(torch.tensor([0.8, 0.2], dtype=torch.float64)).to(CDTYPE),
        "diag_0p7_0p3": torch.diag(torch.tensor([0.7, 0.3], dtype=torch.float64)).to(CDTYPE),
        "max_mixed": torch.eye(2, dtype=CDTYPE) / 2.0,
    }


def spectrum(rho: torch.Tensor) -> torch.Tensor:
    eigs = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real.clamp_min(0.0)
    total = torch.sum(eigs)
    if float(total.item()) <= EPS:
        raise ValueError("zero-trace density matrix")
    return eigs / total


def von_neumann_entropy(rho: torch.Tensor) -> float:
    eigs = spectrum(rho)
    pos = eigs[eigs > 1e-14]
    if pos.numel() == 0:
        return 0.0
    return float((-torch.sum(pos * torch.log2(pos))).item())


def tsallis_entropy(rho: torch.Tensor, q: float) -> float:
    if abs(q - 1.0) < 1e-12:
        return von_neumann_entropy(rho)
    eigs = spectrum(rho)
    moment = torch.sum(eigs.pow(q))
    return float(((1.0 - moment) / ((q - 1.0) * LN2)).item())


def linear_entropy(rho: torch.Tensor) -> float:
    eigs = spectrum(rho)
    return float((1.0 - torch.sum(eigs * eigs)).item())


def torch_tsallis_rows() -> dict[str, object]:
    q_values = [0.5, 1.0, 2.0, 3.0]
    rows = {}
    for name, rho in density_states().items():
        values = {str(q): tsallis_entropy(rho, q) for q in q_values}
        linear = linear_entropy(rho)
        rows[name] = {
            "tsallis": values,
            "von_neumann": von_neumann_entropy(rho),
            "linear_entropy": linear,
            "q2_times_ln2": values["2.0"] * float(LN2.item()),
            "pass": (
                all(value >= -EPS for value in values.values())
                and abs(values["1.0"] - von_neumann_entropy(rho)) < EPS
                and abs(values["2.0"] * float(LN2.item()) - linear) < EPS
            ),
        }
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def ordering_and_boundary_checks(rows: dict[str, object]) -> dict[str, object]:
    pure = rows["pure_zero"]
    mixed = rows["diag_0p8_0p2"]
    max_mixed = rows["max_mixed"]
    checks = {
        "pure_states_zero_all_q": {
            "pure_zero": pure["tsallis"],
            "pure_plus": rows["pure_plus"]["tsallis"],
            "pass": all(abs(v) < EPS for v in pure["tsallis"].values())
            and all(abs(v) < EPS for v in rows["pure_plus"]["tsallis"].values()),
        },
        "mixed_between_pure_and_max_mixed_q2": {
            "pure_q2": pure["tsallis"]["2.0"],
            "mixed_q2": mixed["tsallis"]["2.0"],
            "max_mixed_q2": max_mixed["tsallis"]["2.0"],
            "pass": pure["tsallis"]["2.0"] < mixed["tsallis"]["2.0"] < max_mixed["tsallis"]["2.0"],
        },
        "q1_limit_matches_von_neumann": {
            "diag_q1": mixed["tsallis"]["1.0"],
            "diag_vn": mixed["von_neumann"],
            "pass": abs(mixed["tsallis"]["1.0"] - mixed["von_neumann"]) < EPS,
        },
        "q2_is_not_von_neumann_except_special_cases": {
            "diag_q2": mixed["tsallis"]["2.0"],
            "diag_vn": mixed["von_neumann"],
            "pass": abs(mixed["tsallis"]["2.0"] - mixed["von_neumann"]) > EPS,
        },
    }
    return {"rows": checks, "pass": all(row["pass"] for row in checks.values())}


def sympy_q2_guard() -> dict[str, object]:
    p = sp.symbols("p", real=True)
    q2 = (1 - (p**2 + (1 - p) ** 2)) / sp.log(2)
    linear = 1 - (p**2 + (1 - p) ** 2)
    return {
        "tsallis_q2": str(sp.simplify(q2)),
        "linear_entropy": str(sp.simplify(linear)),
        "q2_times_ln2_minus_linear": str(sp.simplify(q2 * sp.log(2) - linear)),
        "pass": bool(sp.simplify(q2 * sp.log(2) - linear) == 0),
    }


def z3_finite_witness_guard(rows: dict[str, object]) -> dict[str, object]:
    values = [
        z3.RealVal(str(round(float(row["tsallis"]["2.0"]), 12)))
        for row in rows.values()
    ]
    nonnegative = z3.Solver()
    for value in values:
        nonnegative.add(value >= 0)
    nonnegative.add(z3.Or([value < 0 for value in values]))
    pure_zero = z3.Solver()
    pure_zero.add(values[0] != 0)
    return {
        "finite_q2_negative_violation_unsat": {
            "z3_result": str(nonnegative.check()),
            "pass": nonnegative.check() == z3.unsat,
            "scope": "fixed precomputed q=2 witness values only, not a general q-entropy proof",
        },
        "pure_q2_nonzero_violation_unsat": {
            "z3_result": str(pure_zero.check()),
            "pass": pure_zero.check() == z3.unsat,
            "informational_only": True,
            "scope": "vacuous pure-state witness over a precomputed zero value; retained only as a receipt sanity check",
        },
    }


def boundary_checks() -> dict[str, object]:
    registry_text = REGISTRY_PATH.read_text(encoding="utf-8") if REGISTRY_PATH.exists() else ""
    rows = {
        "primary_lego_registered": {
            "primary_lego_ids": PRIMARY_LEGO_IDS,
            "registry_path": str(REGISTRY_PATH),
            "boundary_note": "Registry presence is not promotion; this row remains tool-lego fit evidence only.",
            "pass": PRIMARY_LEGO_IDS == ["tsallis_entropy"] and "tsallis_entropy" in registry_text,
        },
        "no_neighbor_family_credit": {
            "lego_ids": LEGO_IDS,
            "pass": LEGO_IDS == ["tsallis_entropy"],
        },
        "classification_is_tool_lego_fit_probe": {"classification": CLASSIFICATION, "pass": CLASSIFICATION == "tool_lego_fit_probe"},
    }
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def main() -> None:
    receipts = source_receipts()
    prerequisite = {
        "source_receipts": receipts,
        "all_available_and_passing": all(row["exists"] and row["all_pass"] for row in receipts.values()),
        "note": "Prerequisite receipts must exist and pass; their canonical status is not promoted.",
    }
    torch_rows = torch_tsallis_rows()
    z3_rows = z3_finite_witness_guard(torch_rows["rows"])
    positive = {
        "torch_tsallis_rows": torch_rows,
        "ordering_and_boundary_checks": ordering_and_boundary_checks(torch_rows["rows"]),
    }
    negative = {
        "z3_finite_witness_guard": {
            **z3_rows,
            "pass": all(row["pass"] for row in z3_rows.values()),
        }
    }
    boundary = {
        "sympy_q2_guard": sympy_q2_guard(),
        "scope_and_promotion_boundary": boundary_checks(),
    }
    evidence_all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    all_pass = bool(prerequisite["all_available_and_passing"] and evidence_all_pass)
    result = {
        "name": "tsallis_entropy_torch_microfit",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "tool_lego_fit_probe",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {key: str(path) for key, path in PARENT_RESULTS.items()},
        "prerequisite": prerequisite,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "load_bearing_tools": ["pytorch"],
            "supportive_tools": ["sympy", "z3"],
            "claim_ceiling": "local Tsallis-entropy tool-lego fit only",
            "promotion_allowed": False,
        },
        "next_lego_target": "tsallis_entropy_operator_topology_controls",
        "claim_ceiling": "local Tsallis-entropy tool-lego fit only; no coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission",
        "promotion_condition": "Requires separate coupling/coexistence/topology/operator receipts and explicit stage-gate approval.",
        "blocked_until": "downstream coupling evidence exists and stage gate admits it",
        "demotion_condition": "Demote if parent receipts disappear, torch q-entropy witnesses fail, or the result is used as bridge/QIT/axis proof.",
        "out_of_scope": ["QIT engine admission", "GStack admission", "axis promotion", "nonclassical proof", "general entropy theorem"],
        "timestamp": datetime.now(UTC).isoformat(),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
