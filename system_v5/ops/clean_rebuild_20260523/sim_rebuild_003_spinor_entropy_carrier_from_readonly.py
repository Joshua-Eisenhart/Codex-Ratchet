#!/usr/bin/env python3
"""Clean-room rebuild 003: spinor entropy carrier from read-only atlas.

This scout rebuilds the finite spinor carrier and the minimal entropy readouts
that Axis0 candidates later depend on. It does not test or admit Axis0.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "rebuild_003_spinor_entropy_carrier_from_readonly_results.json"

classification = "clean_rebuild_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical_clean_rebuild"
SOURCE_ALIGNMENT_CATEGORY = "spinor_entropy_carrier_readonly_rebuild"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Clean rebuild scout only: rebuilds finite spinor, Bloch, density, torus "
    "average entropy, and b0 sign behavior from read-only source math. It does "
    "not admit Axis0, Xi, Phi0, final entropy gradient, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite spinor, density, eigenvalue entropy, Bloch, and cut-state carrier checks",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive clean rebuild receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result paths"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
EPS = 1e-12


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize(v: torch.Tensor) -> torch.Tensor:
    return v / torch.clamp(torch.linalg.vector_norm(v), min=EPS)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def density(psi: torch.Tensor) -> torch.Tensor:
    rho = torch.outer(psi, torch.conj(psi))
    return (rho + torch.conj(rho).T) / 2.0


def bloch(rho: torch.Tensor) -> torch.Tensor:
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ SX)).item(),
            torch.real(torch.trace(rho @ SY)).item(),
            torch.real(torch.trace(rho @ SZ)).item(),
        ],
        dtype=DTYPE,
    )


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + torch.conj(rho).T) / 2.0).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    nz = vals[vals > EPS]
    return float((-torch.sum(nz * torch.log(nz))).item())


def torus_average_density(eta: float) -> torch.Tensor:
    return torch.diag(torch.tensor([math.cos(eta) ** 2, math.sin(eta) ** 2], dtype=CDTYPE))


def analytic_torus_entropy(eta: float) -> float:
    p = math.cos(eta) ** 2
    q = math.sin(eta) ** 2
    return -p * math.log(p) - q * math.log(q)


def sign_with_zero(x: float, tol: float = 1e-12) -> int:
    if abs(x) <= tol:
        return 0
    return 1 if x > 0.0 else -1


def spinor_density_gate() -> dict[str, Any]:
    rows = []
    max_norm_gap = 0.0
    max_trace_gap = 0.0
    max_purity_gap = 0.0
    max_bloch_formula_gap = 0.0
    for phi, chi, eta in ((0.11, 0.23, 0.31), (0.74, -0.42, math.pi / 4), (1.17, 0.88, 1.09)):
        psi = spinor(phi, chi, eta)
        rho = density(psi)
        r = bloch(rho)
        expected = torch.tensor(
            [
                math.sin(2 * eta) * math.cos(2 * chi),
                -math.sin(2 * eta) * math.sin(2 * chi),
                math.cos(2 * eta),
            ],
            dtype=DTYPE,
        )
        norm_gap = abs(torch.linalg.vector_norm(psi).item() - 1.0)
        trace_gap = abs(torch.real(torch.trace(rho)).item() - 1.0)
        purity_gap = abs(torch.real(torch.trace(rho @ rho)).item() - 1.0)
        formula_gap = float(torch.linalg.vector_norm(r - expected).item())
        max_norm_gap = max(max_norm_gap, norm_gap)
        max_trace_gap = max(max_trace_gap, trace_gap)
        max_purity_gap = max(max_purity_gap, purity_gap)
        max_bloch_formula_gap = max(max_bloch_formula_gap, formula_gap)
        rows.append({"eta": eta, "norm_gap": norm_gap, "trace_gap": trace_gap, "purity_gap": purity_gap, "bloch_formula_gap": formula_gap})
    return {
        "pass": max_norm_gap < 1e-12 and max_trace_gap < 1e-12 and max_purity_gap < 1e-12 and max_bloch_formula_gap < 1e-12,
        "source": "AXES atlas lines 103-123: spinor, Hopf map, density reduction, torus stratum",
        "rows": rows,
        "max_norm_gap": max_norm_gap,
        "max_trace_gap": max_trace_gap,
        "max_purity_gap": max_purity_gap,
        "max_bloch_formula_gap": max_bloch_formula_gap,
    }


def torus_entropy_gate() -> dict[str, Any]:
    rows = []
    for eta in (math.pi / 8.0, math.pi / 4.0, 3.0 * math.pi / 8.0):
        rho_bar = torus_average_density(eta)
        s_numeric = entropy(rho_bar)
        s_analytic = analytic_torus_entropy(eta)
        rows.append(
            {
                "eta": eta,
                "b0_sign_cos_2eta": sign_with_zero(math.cos(2 * eta)),
                "entropy_numeric": s_numeric,
                "entropy_analytic": s_analytic,
                "entropy_gap": abs(s_numeric - s_analytic),
            }
        )
    max_gap = max(row["entropy_gap"] for row in rows)
    middle_is_max = rows[1]["entropy_numeric"] > rows[0]["entropy_numeric"] and rows[1]["entropy_numeric"] > rows[2]["entropy_numeric"]
    signs = [row["b0_sign_cos_2eta"] for row in rows]
    return {
        "pass": max_gap < 1e-12 and middle_is_max and signs == [1, 0, -1],
        "source": "AXES atlas lines 208-224, 231-233: rho_bar entropy and b0 = sign(cos(2 eta))",
        "rows": rows,
        "max_entropy_gap": max_gap,
        "clifford_torus_entropy": rows[1]["entropy_numeric"],
        "b0_signs": signs,
    }


def two_qubit_cut_gate() -> dict[str, Any]:
    psi_a = spinor(0.21, 0.37, 0.46)
    psi_b = spinor(-0.13, 0.58, 0.67)
    product = torch.kron(psi_a, psi_b)
    bell_like = normalize(torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=CDTYPE))
    rho_product = density(product)
    rho_entangled = density(bell_like)
    rho_product_a = torch.einsum("abcb->ac", rho_product.reshape(2, 2, 2, 2))
    rho_entangled_a = torch.einsum("abcb->ac", rho_entangled.reshape(2, 2, 2, 2))
    s_product_a = entropy(rho_product_a)
    s_entangled_a = entropy(rho_entangled_a)
    return {
        "pass": s_product_a < 1e-10 and abs(s_entangled_a - math.log(2.0)) < 1e-10,
        "source": "AXES/Weyl flux docs require rho_AB only as a later branch; this gate establishes the finite cut carrier control before Axis0",
        "product_reduced_entropy": s_product_a,
        "max_entangled_reduced_entropy": s_entangled_a,
        "log2": math.log(2.0),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    sections = {
        "spinor_density_gate": spinor_density_gate(),
        "torus_entropy_gate": torus_entropy_gate(),
        "two_qubit_cut_gate": two_qubit_cut_gate(),
    }
    all_pass = all(bool(section["pass"]) for section in sections.values())
    result = {
        "schema": "clean_rebuild_result_v1",
        "name": "rebuild_003_spinor_entropy_carrier_from_readonly",
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "sections": sections,
        "axis0_status": {
            "carrier_entropy_rebuilt": bool(sections["torus_entropy_gate"]["pass"] and sections["two_qubit_cut_gate"]["pass"]),
            "axis0_formula_admitted": False,
            "next_required_test": "rebuild Xi/rho_AB candidate family against these carrier controls without importing contaminated bridge receipts",
        },
        "source_boundary": {
            "reads_formal_scout_results": False,
            "reads_grok_sim": False,
            "reads_external_audits": False,
            "reads_cross_lane_synthesis_docs": False,
            "primary_reference_docs": [
                "system_v5/READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md",
                "system_v5/READ ONLY Reference Docs/Weyl Flux.md",
            ],
        },
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
