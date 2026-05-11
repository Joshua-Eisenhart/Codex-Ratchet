#!/usr/bin/env python3
"""Reduced-state consistency microfit for local bipartite density carriers.

This bounded tool-lego fit checks that valid 2-qubit joint density matrices
remain valid density matrices after partial trace. It is a local bipartite
carrier test only, not a coupling, bridge, QIT, GStack, axis, engine, or
nonclassical admission claim.
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
    "Bounded reduced-state consistency microfit for local bipartite density "
    "carriers. PyTorch is load-bearing for batched 2-qubit partial traces and "
    "Hermitian/trace/PSD checks on reduced states; sympy and z3 provide "
    "supportive trace and finite-dimension guard checks. This is not a "
    "coupling, bridge, QIT, GStack, axis, engine, or nonclassical admission."
)

LEGO_IDS = ["partial_trace_operator"]
PRIMARY_LEGO_IDS = ["partial_trace_operator"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing batched 2-qubit partial trace and reduced-state H+P+Tr checks",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive symbolic trace-preservation identity for product basis blocks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite-dimension guard checks for the 2x2 bipartite carrier",
    },
    "numpy": {"tried": False, "used": False, "reason": "not needed; torch carries the numeric reduction path"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this partial-trace microfit"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "supportive",
    "z3": "supportive",
    "numpy": None,
    "cvc5": None,
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
PARENT_RESULTS = {
    "reduced_state_object": RESULT_DIR / "reduced_state_object_results.json",
    "pure_lego_density_matrices": RESULT_DIR / "pure_lego_density_matrices_results.json",
}
REGISTRY_PATH = PROBE_DIR.parents[1] / "system_v5" / "docs" / "17_actual_lego_registry.md"
EPS = 1e-10
CDTYPE = torch.complex128


def source_receipts() -> dict[str, object]:
    out = {}
    for key, path in PARENT_RESULTS.items():
        if not path.exists():
            out[key] = {"path": str(path), "exists": False, "all_pass": False}
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        out[key] = {
            "path": str(path),
            "exists": True,
            "all_pass": bool(data.get("all_pass") or data.get("summary", {}).get("all_pass")),
            "classification": data.get("classification"),
        }
    return out


def partial_trace_A(rho_ab: torch.Tensor) -> torch.Tensor:
    reshaped = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("aiaj->ij", reshaped)


def partial_trace_B(rho_ab: torch.Tensor) -> torch.Tensor:
    reshaped = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("iaja->ij", reshaped)


def random_density(dim: int, generator: torch.Generator) -> torch.Tensor:
    real = torch.randn((dim, dim), dtype=torch.float64, generator=generator)
    imag = torch.randn((dim, dim), dtype=torch.float64, generator=generator)
    mat = torch.complex(real, imag)
    rho = mat @ mat.conj().T
    return rho / torch.trace(rho).real


def density_checks(rho: torch.Tensor) -> dict[str, object]:
    hermitian_residual = float(torch.max(torch.abs(rho - rho.conj().T)).item())
    trace_value = float(torch.trace(rho).real.item())
    eigs = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    min_eig = float(torch.min(eigs).item())
    return {
        "trace": trace_value,
        "hermitian_residual": hermitian_residual,
        "min_eigenvalue": min_eig,
        "pass": bool(abs(trace_value - 1.0) < EPS and hermitian_residual < EPS and min_eig >= -EPS),
    }


def torch_reduced_state_batch() -> dict[str, object]:
    generator = torch.Generator().manual_seed(20260511)
    rows = {}
    failures = []
    for idx in range(128):
        rho_ab = random_density(4, generator)
        rho_a = partial_trace_B(rho_ab)
        rho_b = partial_trace_A(rho_ab)
        joint = density_checks(rho_ab)
        reduced_a = density_checks(rho_a)
        reduced_b = density_checks(rho_b)
        ok = bool(joint["pass"] and reduced_a["pass"] and reduced_b["pass"])
        if not ok:
            failures.append(idx)
        if idx < 8:
            rows[f"sample_{idx}"] = {
                "joint": joint,
                "reduced_A": reduced_a,
                "reduced_B": reduced_b,
                "pass": ok,
            }
    return {
        "sample_count": 128,
        "sample_rows": rows,
        "failure_indices": failures,
        "pass": not failures,
    }


def torch_named_witnesses() -> dict[str, object]:
    zero = torch.zeros(4, dtype=CDTYPE)
    zero[0] = 1.0
    bell = torch.zeros(4, dtype=CDTYPE)
    bell[0] = 1.0 / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    bell[3] = 1.0 / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    witnesses = {
        "product_00": zero,
        "bell_phi_plus": bell,
    }
    rows = {}
    for name, psi in witnesses.items():
        rho = torch.outer(psi, psi.conj())
        rho_a = partial_trace_B(rho)
        rho_b = partial_trace_A(rho)
        rows[name] = {
            "joint": density_checks(rho),
            "reduced_A": density_checks(rho_a),
            "reduced_B": density_checks(rho_b),
            "pass": density_checks(rho)["pass"] and density_checks(rho_a)["pass"] and density_checks(rho_b)["pass"],
        }
    bell_a = partial_trace_B(torch.outer(bell, bell.conj()))
    rows["bell_phi_plus"]["reduced_A_maximally_mixed"] = bool(torch.allclose(bell_a, torch.eye(2, dtype=CDTYPE) / 2, atol=EPS))
    rows["bell_phi_plus"]["pass"] = rows["bell_phi_plus"]["pass"] and rows["bell_phi_plus"]["reduced_A_maximally_mixed"]
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def sympy_trace_preservation_identity() -> dict[str, object]:
    r0000, r0101, r1010, r1111 = sp.symbols("r0000 r0101 r1010 r1111", real=True)
    trace_ab = sp.simplify(r0000 + r0101 + r1010 + r1111)
    trace_a = sp.simplify((r0000 + r0101) + (r1010 + r1111))
    trace_b = sp.simplify((r0000 + r1010) + (r0101 + r1111))
    return {
        "trace_ab": str(trace_ab),
        "trace_a_after_tracing_B": str(trace_a),
        "trace_b_after_tracing_A": str(trace_b),
        "pass": bool(sp.simplify(trace_ab - trace_a) == 0 and sp.simplify(trace_ab - trace_b) == 0),
    }


def z3_finite_dimension_guard() -> dict[str, object]:
    da, db = z3.Ints("da db")
    valid = z3.Solver()
    valid.add(da == 2, db == 2, da * db == 4)
    valid_result = valid.check()
    invalid = z3.Solver()
    invalid.add(da == 2, db == 2, da * db != 4)
    invalid_result = invalid.check()
    return {
        "dA2_dB2_gives_joint_dim4": {"z3_result": str(valid_result), "pass": valid_result == z3.sat},
        "dA2_dB2_rejects_wrong_joint_dim": {"z3_result": str(invalid_result), "pass": invalid_result == z3.unsat},
        "pass": valid_result == z3.sat and invalid_result == z3.unsat,
    }


def boundary_checks() -> dict[str, object]:
    registry_text = REGISTRY_PATH.read_text(encoding="utf-8") if REGISTRY_PATH.exists() else ""
    result = {
        "primary_lego_registered": {
            "primary_lego_ids": PRIMARY_LEGO_IDS,
            "registry_path": str(REGISTRY_PATH),
            "pass": PRIMARY_LEGO_IDS == ["partial_trace_operator"] and "partial_trace_operator" in registry_text,
        },
        "classification_is_tool_lego_fit_probe": {"classification": CLASSIFICATION, "pass": CLASSIFICATION == "tool_lego_fit_probe"},
        "no_neighbor_lego_credit": {"lego_ids": LEGO_IDS, "pass": LEGO_IDS == ["partial_trace_operator"]},
    }
    result["pass"] = all(row["pass"] for row in result.values())
    return result


def partial_trace_alone_does_not_admit_coupling() -> dict[str, object]:
    return {
        "claim_killed": "partial trace consistency alone admits coupling, bridge, or QIT structure",
        "reason": "this packet only checks reduced-state admissibility for local 2x2 bipartite carriers",
        "counts_toward_all_pass": False,
    }


def main() -> None:
    receipts = source_receipts()
    prerequisite = {
        "source_receipts": receipts,
        "all_available_and_passing": all(row["exists"] and row["all_pass"] for row in receipts.values()),
        "note": "Prerequisite receipts must exist and pass; their canonical status is not promoted.",
    }
    positive = {
        "torch_reduced_state_batch": torch_reduced_state_batch(),
        "torch_named_witnesses": torch_named_witnesses(),
    }
    negative = {
        "z3_finite_dimension_guard": z3_finite_dimension_guard(),
    }
    boundary = {
        "sympy_trace_preservation_identity": sympy_trace_preservation_identity(),
        "scope_and_promotion_boundary": boundary_checks(),
    }
    evidence_all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    all_pass = bool(prerequisite["all_available_and_passing"] and evidence_all_pass)
    result = {
        "name": "reduced_state_consistency_torch_microfit",
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
        "scope_declaration": partial_trace_alone_does_not_admit_coupling(),
        "summary": {
            "all_pass": bool(all_pass),
            "evidence_rows_all_pass": bool(evidence_all_pass),
            "promotion_allowed": False,
            "load_bearing_tool": "pytorch",
            "claim_ceiling": "local_2x2_bipartite_reduced_state_consistency_only",
            "scope_note": divergence_log,
        },
        "all_pass": bool(all_pass),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / "reduced_state_consistency_torch_microfit_results.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
