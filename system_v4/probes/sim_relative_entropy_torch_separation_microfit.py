#!/usr/bin/env python3
"""PyTorch relative-entropy separation microfit.

This bounded tool-lego fit isolates directional quantum relative entropy
D(rho||sigma) from JS-style symmetric comparisons on fixed full-rank qubit
density matrices. It is local tool-lego evidence only, not a coupling, bridge,
QIT, GStack, axis, engine, or nonclassical admission claim.
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
    "Bounded PyTorch relative-entropy microfit on fixed full-rank qubit density "
    "matrices. PyTorch is load-bearing for spectral matrix-log evaluation and "
    "one depolarizing-channel DPI sweep; sympy and z3 provide supportive finite "
    "classical/identity guards only. This is not a coupling, bridge, QIT, "
    "GStack, axis, engine, or nonclassical admission."
)

LEGO_IDS = ["relative_entropy"]
PRIMARY_LEGO_IDS = ["relative_entropy"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing spectral matrix-log relative entropy and depolarizing-channel DPI sweep",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive symbolic identity and second-derivative check for the binary classical restriction",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite guard for fixed precomputed nonnegative/zero relative-entropy witnesses",
    },
    "numpy": {"tried": False, "used": False, "reason": "not needed; torch carries the numeric matrix-log path"},
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
    "conditional_entropy_torch_separation_microfit": RESULT_DIR / "conditional_entropy_torch_separation_microfit_results.json",
    "pure_lego_density_matrices": RESULT_DIR / "pure_lego_density_matrices_results.json",
    "positivity_constraint": RESULT_DIR / "positivity_constraint_results.json",
    "von_neumann_entropy": RESULT_DIR / "von_neumann_entropy_results.json",
    "relative_entropy_js": RESULT_DIR / "relative_entropy_js_results.json",
    "pytorch_capability": RESULT_DIR / "pytorch_capability_results.json",
}
REGISTRY_PATH = PROBE_DIR.parents[1] / "system_v5" / "docs" / "17_actual_lego_registry.md"
OUT_PATH = RESULT_DIR / "relative_entropy_torch_separation_microfit_results.json"
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


def dm(psi: torch.Tensor) -> torch.Tensor:
    ket = psi.reshape(-1, 1).to(CDTYPE)
    return ket @ ket.conj().T


def mix_full_rank(rho: torch.Tensor, eps: float = 0.08) -> torch.Tensor:
    dim = rho.shape[0]
    return (1.0 - eps) * rho + eps * torch.eye(dim, dtype=CDTYPE) / dim


def state_family() -> dict[str, torch.Tensor]:
    zero = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    one = torch.tensor([0.0, 1.0], dtype=CDTYPE)
    plus = (zero + one) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    diag_bias = torch.diag(torch.tensor([0.72, 0.28], dtype=torch.float64)).to(CDTYPE)
    return {
        "zero_full_rank": mix_full_rank(dm(zero)),
        "one_full_rank": mix_full_rank(dm(one)),
        "plus_full_rank": mix_full_rank(dm(plus)),
        "diag_bias": diag_bias,
        "max_mixed": torch.eye(2, dtype=CDTYPE) / 2.0,
    }


def matrix_log_psd(rho: torch.Tensor) -> torch.Tensor:
    herm = 0.5 * (rho + rho.conj().T)
    eigvals, eigvecs = torch.linalg.eigh(herm)
    if float(torch.min(eigvals).item()) <= 0.0:
        raise ValueError("relative-entropy microfit requires full-rank positive inputs")
    log_diag = torch.diag(torch.log(eigvals).to(CDTYPE))
    return eigvecs @ log_diag @ eigvecs.conj().T


def relative_entropy(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    value = torch.trace(rho @ (matrix_log_psd(rho) - matrix_log_psd(sigma))).real / LN2
    return float(value.item())


def depolarize(rho: torch.Tensor, p: float) -> torch.Tensor:
    dim = rho.shape[0]
    return (1.0 - p) * rho + p * torch.eye(dim, dtype=CDTYPE) / dim


def torch_relative_entropy_rows() -> dict[str, object]:
    states = state_family()
    pairs = [
        ("zero_vs_zero", "zero_full_rank", "zero_full_rank"),
        ("zero_vs_one", "zero_full_rank", "one_full_rank"),
        ("zero_vs_plus", "zero_full_rank", "plus_full_rank"),
        ("diag_vs_mixed", "diag_bias", "max_mixed"),
        ("plus_vs_diag", "plus_full_rank", "diag_bias"),
    ]
    rows = {}
    for label, left, right in pairs:
        rho = states[left]
        sigma = states[right]
        d_forward = relative_entropy(rho, sigma)
        d_reverse = relative_entropy(sigma, rho)
        dpi_input = d_forward
        dpi_output = relative_entropy(depolarize(rho, 0.25), depolarize(sigma, 0.25))
        rows[label] = {
            "rho": left,
            "sigma": right,
            "D_rho_sigma": d_forward,
            "D_sigma_rho": d_reverse,
            "depolarized_D_rho_sigma": dpi_output,
            "dpi_gap_input_minus_output": dpi_input - dpi_output,
            "zero_iff_identical_expected": label == "zero_vs_zero",
            "pass": (
                d_forward >= -EPS
                and d_reverse >= -EPS
                and dpi_input + EPS >= dpi_output
                and ((label == "zero_vs_zero" and abs(d_forward) < EPS) or (label != "zero_vs_zero" and d_forward > EPS))
            ),
        }
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def separation_from_js(rows: dict[str, object]) -> dict[str, object]:
    zero_one = rows["zero_vs_one"]
    plus_diag = rows["plus_vs_diag"]
    asymmetric_gap = abs(plus_diag["D_rho_sigma"] - plus_diag["D_sigma_rho"])
    return {
        "directional_not_js_symmetric": {
            "plus_diag_forward": plus_diag["D_rho_sigma"],
            "plus_diag_reverse": plus_diag["D_sigma_rho"],
            "asymmetry_gap": asymmetric_gap,
            "pass": asymmetric_gap > EPS,
        },
        "orthogonal_like_full_rank_pair_large_but_finite": {
            "zero_vs_one": zero_one["D_rho_sigma"],
            "pass": zero_one["D_rho_sigma"] > plus_diag["D_rho_sigma"] > EPS,
        },
        "pass": asymmetric_gap > EPS and zero_one["D_rho_sigma"] > plus_diag["D_rho_sigma"] > EPS,
    }


def sympy_binary_guard() -> dict[str, object]:
    p, q = sp.symbols("p q", positive=True)
    d = p * sp.log(p / q) + (1 - p) * sp.log((1 - p) / (1 - q))
    second_at_q_eq_p = sp.simplify(sp.diff(d, q, 2).subs(q, p))
    identity_zero = sp.simplify(d.subs(q, p))
    expected = 1 / (p * (1 - p))
    return {
        "binary_kl_identity_zero": str(identity_zero),
        "second_derivative_at_identity": str(second_at_q_eq_p),
        "pass": bool(identity_zero == 0 and sp.simplify(second_at_q_eq_p - expected) == 0),
    }


def z3_finite_witness_guard(rows: dict[str, object]) -> dict[str, object]:
    solver = z3.Solver()
    witness_values = [z3.RealVal(str(round(float(row["D_rho_sigma"]), 12))) for row in rows.values()]
    for value in witness_values:
        solver.add(value >= 0)
    solver.add(z3.Or([value < 0 for value in witness_values]))
    zero_solver = z3.Solver()
    zero = z3.RealVal(str(round(float(rows["zero_vs_zero"]["D_rho_sigma"]), 12)))
    zero_solver.add(zero != 0)
    return {
        "finite_witness_negative_violation_unsat": {
            "z3_result": str(solver.check()),
            "pass": solver.check() == z3.unsat,
            "scope": "fixed precomputed witness values only, not a general matrix-log proof",
        },
        "identical_witness_nonzero_violation_unsat": {
            "z3_result": str(zero_solver.check()),
            "pass": zero_solver.check() == z3.unsat,
        },
    }


def boundary_checks() -> dict[str, object]:
    registry_text = REGISTRY_PATH.read_text(encoding="utf-8") if REGISTRY_PATH.exists() else ""
    rows = {
        "primary_lego_registered": {
            "primary_lego_ids": PRIMARY_LEGO_IDS,
            "registry_path": str(REGISTRY_PATH),
            "boundary_note": "Registry presence is not promotion; this row remains tool-lego fit evidence only.",
            "pass": PRIMARY_LEGO_IDS == ["relative_entropy"] and "relative_entropy" in registry_text,
        },
        "no_js_neighbor_credit": {
            "lego_ids": LEGO_IDS,
            "pass": LEGO_IDS == ["relative_entropy"] and "relative_entropy_js" not in LEGO_IDS,
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
    torch_rows = torch_relative_entropy_rows()
    positive = {
        "torch_relative_entropy_rows": torch_rows,
        "separation_from_js": separation_from_js(torch_rows["rows"]),
    }
    z3_rows = z3_finite_witness_guard(torch_rows["rows"])
    negative = {
        "z3_finite_witness_guard": {
            **z3_rows,
            "pass": all(row["pass"] for row in z3_rows.values()),
        }
    }
    boundary = {
        "sympy_binary_guard": sympy_binary_guard(),
        "scope_and_promotion_boundary": boundary_checks(),
    }
    evidence_all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    all_pass = bool(prerequisite["all_available_and_passing"] and evidence_all_pass)
    result = {
        "name": "relative_entropy_torch_separation_microfit",
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
            "claim_ceiling": "local relative-entropy tool-lego fit only",
            "promotion_allowed": False,
        },
        "claim_ceiling": "local relative-entropy tool-lego fit only; no coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission",
        "promotion_condition": "Requires separate coupling/coexistence/topology/operator receipts and explicit stage-gate approval.",
        "blocked_until": "downstream coupling evidence exists and stage gate admits it",
        "demotion_condition": "Demote if parent receipts disappear, torch matrix-log witnesses fail, or the result is used as bridge/QIT/axis proof.",
        "out_of_scope": ["QIT engine admission", "GStack admission", "axis promotion", "nonclassical proof", "general DPI theorem"],
        "timestamp": datetime.now(UTC).isoformat(),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
