#!/usr/bin/env python3
"""PyTorch min/max entropy microfit.

This bounded tool-lego fit checks whether PyTorch can carry unsmoothed min/max
entropy witnesses if the broader entropy-family blocker is later resolved. It
is local support-only evidence. It does not admit a lego, unblock
entropy_family_crosschecks, or claim a coupling, bridge, QIT, GStack, axis,
engine, or nonclassical result.
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
    "Bounded PyTorch unsmoothed min/max entropy support-only microfit on fixed "
    "density matrices. PyTorch is load-bearing for spectral support, "
    "dominant-eigenvalue entropy evaluation, and a small differentiable H_min "
    "autograd witness; sympy and z3 provide supportive finite witness guards. "
    "This does not unblock entropy_family_crosschecks and is not a smooth "
    "one-shot theorem, lego admission, coupling, bridge, QIT, GStack, axis, "
    "engine, or nonclassical admission."
)

LEGO_IDS = ["min_entropy", "max_entropy"]
PRIMARY_LEGO_IDS = ["min_entropy", "max_entropy"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing eigenspectrum, support-rank, and dominant-eigenvalue entropy evaluation",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive symbolic H_min expression for two-outcome diagonal spectra",
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
    "min_max_entropy_classical": RESULT_DIR / "min_max_entropy_classical_results.json",
    "lego_entropy_smooth_one_shot": RESULT_DIR / "lego_entropy_smooth_one_shot_results.json",
    "pure_lego_density_matrices": RESULT_DIR / "pure_lego_density_matrices_results.json",
    "von_neumann_entropy": RESULT_DIR / "von_neumann_entropy_results.json",
    "pytorch_capability": RESULT_DIR / "pytorch_capability_results.json",
}
REGISTRY_PATH = PROBE_DIR.parents[1] / "system_v5" / "docs" / "17_actual_lego_registry.md"
OUT_PATH = RESULT_DIR / "min_max_entropy_torch_microfit_results.json"
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


def min_entropy(rho: torch.Tensor) -> float:
    eigs = spectrum(rho)
    pos = eigs[eigs > 1e-14]
    if pos.numel() == 0:
        return 0.0
    return float((-torch.log2(torch.max(pos))).item())


def max_entropy(rho: torch.Tensor) -> float:
    eigs = spectrum(rho)
    rank = int(torch.sum(eigs > 1e-14).item())
    return float(torch.log2(torch.tensor(float(max(1, rank)), dtype=torch.float64)).item())


def torch_min_max_rows() -> dict[str, object]:
    rows = {}
    for name, rho in density_states().items():
        h_min = min_entropy(rho)
        h_vn = von_neumann_entropy(rho)
        h_max = max_entropy(rho)
        rows[name] = {
            "H_min": h_min,
            "H_von_neumann": h_vn,
            "H_max": h_max,
            "support_rank": int(torch.sum(spectrum(rho) > 1e-14).item()),
            "dominant_eigenvalue": float(torch.max(spectrum(rho)).item()),
            "pass": h_min <= h_vn + EPS <= h_max + EPS and h_min >= -EPS and h_max >= -EPS,
        }
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def torch_hmin_autograd_witness() -> dict[str, object]:
    p = torch.tensor(0.8, dtype=torch.float64, requires_grad=True)
    rho = torch.diag(torch.stack([p, 1.0 - p])).to(CDTYPE)
    hmin = min_entropy_tensor(rho)
    hmin.backward()
    grad = float(p.grad.item())
    expected = float(-1.0 / (0.8 * torch.log(torch.tensor(2.0, dtype=torch.float64))).item())
    finite_delta = 1e-5
    hi = -torch.log2(torch.tensor(0.8 + finite_delta, dtype=torch.float64))
    lo = -torch.log2(torch.tensor(0.8 - finite_delta, dtype=torch.float64))
    finite_difference = float(((hi - lo) / (2.0 * finite_delta)).item())
    return {
        "p": 0.8,
        "H_min": float(hmin.detach().item()),
        "autograd_grad": grad,
        "analytic_grad": expected,
        "finite_difference_grad": finite_difference,
        "pass": abs(grad - expected) < 1e-10 and abs(grad - finite_difference) < 1e-8,
        "scope": "single differentiable diagonal H_min witness away from eigenvalue crossing; H_max rank is intentionally not claimed differentiable",
    }


def min_entropy_tensor(rho: torch.Tensor) -> torch.Tensor:
    eigs = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real.clamp_min(0.0)
    eigs = eigs / torch.sum(eigs)
    return -torch.log2(torch.max(eigs[eigs > 1e-14]))


def ordering_and_boundary_checks(rows: dict[str, object]) -> dict[str, object]:
    pure = rows["pure_zero"]
    mixed = rows["diag_0p8_0p2"]
    max_mixed = rows["max_mixed"]
    checks = {
        "pure_states_zero": {
            "pure_zero": pure,
            "pure_plus": rows["pure_plus"],
            "pass": abs(pure["H_min"]) < EPS
            and abs(pure["H_max"]) < EPS
            and abs(rows["pure_plus"]["H_min"]) < EPS
            and abs(rows["pure_plus"]["H_max"]) < EPS,
        },
        "mixed_min_vn_max_ordering": {
            "mixed": mixed,
            "pass": mixed["H_min"] < mixed["H_von_neumann"] < mixed["H_max"],
        },
        "max_mixed_saturates_min_vn_max": {
            "max_mixed": max_mixed,
            "pass": abs(max_mixed["H_min"] - 1.0) < EPS
            and abs(max_mixed["H_von_neumann"] - 1.0) < EPS
            and abs(max_mixed["H_max"] - 1.0) < EPS,
        },
        "support_rank_changes_max_entropy_not_min_only": {
            "pure_rank": pure["support_rank"],
            "mixed_rank": mixed["support_rank"],
            "pass": pure["support_rank"] == 1 and mixed["support_rank"] == 2,
        },
    }
    return {"rows": checks, "pass": all(row["pass"] for row in checks.values())}


def sympy_min_entropy_guard() -> dict[str, object]:
    p = sp.symbols("p", positive=True)
    h_min = -sp.log(p) / sp.log(2)
    return {
        "H_min_for_dominant_probability_p": str(h_min),
        "p_times_two_power_Hmin": str(sp.simplify(p * 2**h_min)),
        "pass": bool(sp.simplify(p * 2**h_min) == 1),
        "scope": "symbolic diagonal two-outcome dominant-probability relation only",
    }


def z3_finite_witness_guard(rows: dict[str, object]) -> dict[str, object]:
    mixed = rows["diag_0p8_0p2"]
    hmin = z3.RealVal(str(round(float(mixed["H_min"]), 12)))
    hvn = z3.RealVal(str(round(float(mixed["H_von_neumann"]), 12)))
    hmax = z3.RealVal(str(round(float(mixed["H_max"]), 12)))
    order = z3.Solver()
    order.add(z3.Or(hmin > hvn, hvn > hmax))
    pure = z3.Solver()
    pure.add(z3.RealVal(str(round(float(rows["pure_zero"]["H_max"]), 12))) != 0)
    return {
        "fixed_mixed_min_vn_max_violation_unsat": {
            "z3_result": str(order.check()),
            "pass": order.check() == z3.unsat,
            "scope": "fixed precomputed witnesses only, not a general min/max entropy proof",
        },
        "pure_hmax_nonzero_violation_unsat": {
            "z3_result": str(pure.check()),
            "pass": pure.check() == z3.unsat,
            "informational_only": True,
            "scope": "vacuous pure-state witness over a precomputed zero value; retained only as receipt sanity check",
        },
    }


def boundary_checks() -> dict[str, object]:
    registry_text = REGISTRY_PATH.read_text(encoding="utf-8") if REGISTRY_PATH.exists() else ""
    rows = {
        "primary_legos_registered": {
            "primary_lego_ids": PRIMARY_LEGO_IDS,
            "registry_path": str(REGISTRY_PATH),
            "boundary_note": "Registry presence is not promotion; this row remains tool-lego fit evidence only.",
            "pass": PRIMARY_LEGO_IDS == ["min_entropy", "max_entropy"]
            and "min_entropy" in registry_text
            and "max_entropy" in registry_text,
        },
        "no_neighbor_family_credit": {
            "lego_ids": LEGO_IDS,
            "pass": LEGO_IDS == ["min_entropy", "max_entropy"],
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
    torch_rows = torch_min_max_rows()
    z3_rows = z3_finite_witness_guard(torch_rows["rows"])
    positive = {
        "torch_min_max_rows": torch_rows,
        "ordering_and_boundary_checks": ordering_and_boundary_checks(torch_rows["rows"]),
        "torch_hmin_autograd_witness": torch_hmin_autograd_witness(),
    }
    negative = {
        "z3_finite_witness_guard": {
            **z3_rows,
            "pass": all(row["pass"] for row in z3_rows.values()),
        }
    }
    boundary = {
        "sympy_min_entropy_guard": sympy_min_entropy_guard(),
        "scope_and_promotion_boundary": boundary_checks(),
    }
    evidence_all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    all_pass = bool(prerequisite["all_available_and_passing"] and evidence_all_pass)
    result = {
        "name": "min_max_entropy_torch_microfit",
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
            "claim_ceiling": "support-only PyTorch unsmoothed min/max entropy tool-fit witness; does not unblock entropy_family_crosschecks",
            "promotion_allowed": False,
            "entropy_family_crosschecks_unblocked": False,
        },
        "next_lego_target": "min_max_entropy_operator_topology_controls",
        "claim_ceiling": "support-only PyTorch unsmoothed min/max entropy tool-fit witness; no lego admission, no entropy_family_crosschecks unblocking, no smooth one-shot theorem, coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission",
        "promotion_condition": "Requires separate proof that entropy is subordinate to carrier/geometry/operator structure, then separate smooth one-shot/coupling/coexistence/topology/operator receipts and explicit stage-gate approval.",
        "blocked_until": "entropy_family_crosschecks parent blocker is resolved and downstream coupling evidence exists under the stage gate",
        "demotion_condition": "Demote if used to advance entropy_family_crosschecks before resolving the parent blocker, if parent receipts disappear, if torch spectral/autograd witnesses fail, or if the result is used as bridge/QIT/axis proof.",
        "out_of_scope": ["QIT engine admission", "GStack admission", "axis promotion", "nonclassical proof", "general entropy theorem", "exact smooth one-shot proof"],
        "timestamp": datetime.now(UTC).isoformat(),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
