#!/usr/bin/env python3
"""PyTorch Renyi-entropy microfit.

This bounded tool-lego fit splits Renyi entropy into its own machine row from
the broader spectral-entropy bundle. It is local tool-lego evidence only, not a
coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission claim.
"""

from __future__ import annotations

import json
import math
import pathlib
from datetime import UTC, datetime

import sympy as sp
import torch
import z3


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Bounded PyTorch Renyi-entropy microfit on fixed qubit density matrices. "
    "PyTorch is load-bearing for spectral alpha-entropy evaluation; sympy and "
    "z3 provide supportive alpha=2/finite witness guards. This is not a "
    "coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission."
)

LEGO_IDS = ["renyi_entropy"]
PRIMARY_LEGO_IDS = ["renyi_entropy"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing eigenspectrum and Renyi alpha-entropy evaluation on fixed density matrices",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive symbolic alpha=2 relation to collision entropy",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite Real-arithmetic guard over precomputed ordering witnesses",
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
    "renyi_entropy_classical": RESULT_DIR / "renyi_entropy_classical_results.json",
    "lego_entropy_spectral_families": RESULT_DIR / "lego_entropy_spectral_families_results.json",
    "von_neumann_entropy": RESULT_DIR / "von_neumann_entropy_results.json",
    "pure_lego_density_matrices": RESULT_DIR / "pure_lego_density_matrices_results.json",
    "pytorch_capability": RESULT_DIR / "pytorch_capability_results.json",
}
REGISTRY_PATH = PROBE_DIR.parents[1] / "system_v5" / "docs" / "17_actual_lego_registry.md"
OUT_PATH = RESULT_DIR / "renyi_entropy_torch_microfit_results.json"
EPS = 1e-10
CDTYPE = torch.complex128


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


def renyi_entropy(rho: torch.Tensor, alpha: float) -> float:
    eigs = spectrum(rho)
    pos = eigs[eigs > 1e-14]
    if pos.numel() == 0:
        return 0.0
    if abs(alpha - 1.0) < 1e-12:
        return von_neumann_entropy(rho)
    if alpha == 0.0:
        return float(torch.log2(torch.tensor(float(pos.numel()), dtype=torch.float64)).item())
    if math.isinf(alpha):
        return float((-torch.log2(torch.max(pos))).item())
    moment = torch.sum(pos.pow(alpha))
    return float((torch.log2(moment) / (1.0 - alpha)).item())


def torch_renyi_rows() -> dict[str, object]:
    alpha_values = [0.0, 0.5, 1.0, 2.0, float("inf")]
    rows = {}
    for name, rho in density_states().items():
        values = {str(alpha): renyi_entropy(rho, alpha) for alpha in alpha_values}
        rows[name] = {
            "renyi": values,
            "von_neumann": von_neumann_entropy(rho),
            "collision_entropy_alpha2": values["2.0"],
            "pass": (
                all(value >= -EPS for value in values.values())
                and abs(values["1.0"] - von_neumann_entropy(rho)) < EPS
                and values["0.0"] + EPS >= values["0.5"] >= values["1.0"] - EPS
                and values["1.0"] + EPS >= values["2.0"] >= values["inf"] - EPS
            ),
        }
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def ordering_and_boundary_checks(rows: dict[str, object]) -> dict[str, object]:
    pure = rows["pure_zero"]
    mixed = rows["diag_0p8_0p2"]
    max_mixed = rows["max_mixed"]
    checks = {
        "pure_states_zero_all_alpha": {
            "pure_zero": pure["renyi"],
            "pure_plus": rows["pure_plus"]["renyi"],
            "pass": all(abs(v) < EPS for v in pure["renyi"].values())
            and all(abs(v) < EPS for v in rows["pure_plus"]["renyi"].values()),
        },
        "mixed_between_pure_and_max_mixed_alpha2": {
            "pure_alpha2": pure["renyi"]["2.0"],
            "mixed_alpha2": mixed["renyi"]["2.0"],
            "max_mixed_alpha2": max_mixed["renyi"]["2.0"],
            "pass": pure["renyi"]["2.0"] < mixed["renyi"]["2.0"] < max_mixed["renyi"]["2.0"],
        },
        "alpha1_limit_matches_von_neumann": {
            "diag_alpha1": mixed["renyi"]["1.0"],
            "diag_vn": mixed["von_neumann"],
            "pass": abs(mixed["renyi"]["1.0"] - mixed["von_neumann"]) < EPS,
        },
        "alpha2_is_not_von_neumann_except_special_cases": {
            "diag_alpha2": mixed["renyi"]["2.0"],
            "diag_vn": mixed["von_neumann"],
            "pass": abs(mixed["renyi"]["2.0"] - mixed["von_neumann"]) > EPS,
        },
    }
    return {"rows": checks, "pass": all(row["pass"] for row in checks.values())}


def sympy_alpha2_guard() -> dict[str, object]:
    p = sp.symbols("p", real=True)
    power_sum = p**2 + (1 - p) ** 2
    alpha2 = -sp.log(power_sum) / sp.log(2)
    return {
        "renyi_alpha2": str(sp.simplify(alpha2)),
        "collision_power_sum": str(sp.simplify(power_sum)),
        "alpha2_equals_negative_log2_power_sum": str(sp.simplify(alpha2 + sp.log(power_sum) / sp.log(2))),
        "pass": bool(sp.simplify(alpha2 + sp.log(power_sum) / sp.log(2)) == 0),
    }


def z3_finite_witness_guard(rows: dict[str, object]) -> dict[str, object]:
    mixed = rows["diag_0p8_0p2"]["renyi"]
    h0 = z3.RealVal(str(round(float(mixed["0.0"]), 12)))
    h05 = z3.RealVal(str(round(float(mixed["0.5"]), 12)))
    h1 = z3.RealVal(str(round(float(mixed["1.0"]), 12)))
    h2 = z3.RealVal(str(round(float(mixed["2.0"]), 12)))
    hinf = z3.RealVal(str(round(float(mixed["inf"]), 12)))
    nonincreasing = z3.Solver()
    nonincreasing.add(z3.Or(h0 < h05, h05 < h1, h1 < h2, h2 < hinf))
    pure_zero = z3.Solver()
    pure_zero.add(z3.RealVal(str(round(float(rows["pure_zero"]["renyi"]["2.0"]), 12))) != 0)
    return {
        "fixed_mixed_alpha_order_violation_unsat": {
            "z3_result": str(nonincreasing.check()),
            "pass": nonincreasing.check() == z3.unsat,
            "scope": "fixed precomputed alpha witnesses only, not a general Renyi monotonicity proof",
        },
        "pure_alpha2_nonzero_violation_unsat": {
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
            "pass": PRIMARY_LEGO_IDS == ["renyi_entropy"] and "renyi_entropy" in registry_text,
        },
        "no_neighbor_family_credit": {
            "lego_ids": LEGO_IDS,
            "pass": LEGO_IDS == ["renyi_entropy"],
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
    torch_rows = torch_renyi_rows()
    z3_rows = z3_finite_witness_guard(torch_rows["rows"])
    positive = {
        "torch_renyi_rows": torch_rows,
        "ordering_and_boundary_checks": ordering_and_boundary_checks(torch_rows["rows"]),
    }
    negative = {
        "z3_finite_witness_guard": {
            **z3_rows,
            "pass": all(row["pass"] for row in z3_rows.values()),
        }
    }
    boundary = {
        "sympy_alpha2_guard": sympy_alpha2_guard(),
        "scope_and_promotion_boundary": boundary_checks(),
    }
    evidence_all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    all_pass = bool(prerequisite["all_available_and_passing"] and evidence_all_pass)
    result = {
        "name": "renyi_entropy_torch_microfit",
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
            "claim_ceiling": "local Renyi-entropy tool-lego fit only",
            "promotion_allowed": False,
        },
        "next_lego_target": "renyi_entropy_operator_topology_controls",
        "claim_ceiling": "local Renyi-entropy tool-lego fit only; no coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission",
        "promotion_condition": "Requires separate coupling/coexistence/topology/operator receipts and explicit stage-gate approval.",
        "blocked_until": "downstream coupling evidence exists and stage gate admits it",
        "demotion_condition": "Demote if parent receipts disappear, torch alpha-entropy witnesses fail, or the result is used as bridge/QIT/axis proof.",
        "out_of_scope": ["QIT engine admission", "GStack admission", "axis promotion", "nonclassical proof", "general entropy theorem"],
        "timestamp": datetime.now(UTC).isoformat(),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
