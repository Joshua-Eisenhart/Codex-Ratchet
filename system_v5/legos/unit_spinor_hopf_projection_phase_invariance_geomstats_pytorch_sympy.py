#!/usr/bin/env python3
"""Unit spinor Hopf projection lego with phase-invariance checks."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import geomstats.backend as gs
from geomstats.geometry.hypersphere import Hypersphere
import numpy as np
import sympy as sp
import torch


ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "unit_spinor_hopf_projection_phase_invariance_geomstats_pytorch_sympy_results.json"

NAME = "unit_spinor_hopf_projection_phase_invariance_geomstats_pytorch_sympy"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Hopf projection lego only: checks a finite unit spinor as a point on S3, "
    "projects it to S2, verifies global U(1) phase invariance, and rejects "
    "nearby non-unit or non-global-phase variants. It does not admit a full "
    "manifold tower, Weyl chirality, loop independence, cycle, bridge, or "
    "target-system claim."
)

TOOL_MANIFEST = {
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing S3 and S2 hypersphere membership checks",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex spinor, global phase action, and Hopf projection tensor computation",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Hopf projection and unit-sphere algebra for a rational/sqrt witness",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive real array conversion for geomstats membership calls",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "geomstats": "load_bearing",
    "pytorch": "load_bearing",
    "sympy": "load_bearing",
    "numpy": "supportive",
}


def real_embedding(spinor: torch.Tensor) -> np.ndarray:
    return np.array(
        [
            float(torch.real(spinor[0]).item()),
            float(torch.imag(spinor[0]).item()),
            float(torch.real(spinor[1]).item()),
            float(torch.imag(spinor[1]).item()),
        ]
    )


def hopf_projection(spinor: torch.Tensor) -> torch.Tensor:
    a = spinor[0]
    b = spinor[1]
    product = a * torch.conj(b)
    return torch.stack(
        [
            2.0 * torch.real(product),
            2.0 * torch.imag(product),
            torch.abs(a) ** 2 - torch.abs(b) ** 2,
        ]
    ).to(torch.float64)


def spinor_checks(spinor: torch.Tensor, tol: float = 1e-10) -> dict[str, Any]:
    s3 = Hypersphere(dim=3)
    s2 = Hypersphere(dim=2)
    embedded = real_embedding(spinor)
    base = hopf_projection(spinor)
    carrier_norm = float(torch.linalg.vector_norm(spinor).item())
    base_norm = float(torch.linalg.vector_norm(base).item())
    s3_belongs = bool(gs.all(s3.belongs(gs.array(embedded), atol=tol)))
    s2_belongs = bool(gs.all(s2.belongs(gs.array(base.detach().numpy()), atol=tol)))
    return {
        "carrier_norm": carrier_norm,
        "base_norm": base_norm,
        "hopf_base": [float(value.item()) for value in base],
        "geomstats_s3_belongs": s3_belongs,
        "geomstats_s2_belongs": s2_belongs,
        "pass": bool(abs(carrier_norm - 1.0) < tol and abs(base_norm - 1.0) < tol and s3_belongs and s2_belongs),
    }


def phase_distance(spinor: torch.Tensor, theta: float) -> dict[str, Any]:
    phase = torch.exp(torch.tensor(1j * theta, dtype=torch.complex128))
    base_before = hopf_projection(spinor)
    base_after = hopf_projection(phase * spinor)
    distance = float(torch.linalg.vector_norm(base_before - base_after).item())
    return {"base_distance_after_global_phase": distance, "pass": bool(distance < 1e-10)}


def component_phase_distance(spinor: torch.Tensor, theta: float) -> dict[str, Any]:
    phase = torch.exp(torch.tensor(1j * theta, dtype=torch.complex128))
    transformed = torch.stack([phase * spinor[0], torch.conj(phase) * spinor[1]])
    distance = float(torch.linalg.vector_norm(hopf_projection(spinor) - hopf_projection(transformed)).item())
    return {"base_distance_after_componentwise_opposite_phase": distance, "pass": bool(distance > 1e-3)}


def sympy_exact_witness() -> dict[str, Any]:
    a = 1 / sp.sqrt(2)
    b = sp.I / sp.sqrt(2)
    product = a * sp.conjugate(b)
    x = sp.simplify(2 * sp.re(product))
    y = sp.simplify(2 * sp.im(product))
    z = sp.simplify(sp.Abs(a) ** 2 - sp.Abs(b) ** 2)
    norm = sp.simplify(x**2 + y**2 + z**2)
    return {
        "spinor": ["1/sqrt(2)", "I/sqrt(2)"],
        "hopf_base": [str(x), str(y), str(z)],
        "base_norm_squared": str(norm),
        "pass": bool(norm == 1),
    }


def main() -> dict[str, Any]:
    started = time.time()
    dtype = torch.complex128
    spinor = torch.tensor([1.0 + 0.0j, 1.0j], dtype=dtype) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    north_pole_spinor = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=dtype)
    non_unit_spinor = torch.tensor([1.0 + 0.0j, 1.0j], dtype=dtype)
    zero_spinor = torch.tensor([0.0 + 0.0j, 0.0 + 0.0j], dtype=dtype)

    positive = {
        "unit_spinor_projects_from_s3_to_s2": spinor_checks(spinor),
        "global_u1_phase_preserves_hopf_base": phase_distance(spinor, theta=0.73),
        "sympy_exact_hopf_projection_has_unit_base_norm": sympy_exact_witness(),
    }
    graveyards = {
        "non_unit_spinor_rejected": {
            "validity": spinor_checks(non_unit_spinor),
            "pass": not spinor_checks(non_unit_spinor)["pass"],
        },
        "zero_spinor_rejected": {
            "validity": spinor_checks(zero_spinor),
            "pass": not spinor_checks(zero_spinor)["pass"],
        },
        "componentwise_opposite_phase_not_global_u1": component_phase_distance(spinor, theta=0.73),
    }
    boundary = {
        "north_pole_spinor_maps_to_north_pole_base": {
            "validity": spinor_checks(north_pole_spinor),
            "expected_base": [0.0, 0.0, 1.0],
            "pass": spinor_checks(north_pole_spinor)["pass"]
            and max(abs(v - e) for v, e in zip(spinor_checks(north_pole_spinor)["hopf_base"], [0.0, 0.0, 1.0])) < 1e-10,
        }
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "Hopf projection from unit two-component complex spinor on S3 to base point on S2",
        "observable": [
            "S3 carrier membership",
            "S2 base membership",
            "Hopf base coordinates",
            "base distance after global U(1) phase",
            "exact symbolic base norm",
        ],
        "predicate": "unit spinor projects to unit base sphere and global U(1) phase leaves the base point invariant",
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
        },
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
