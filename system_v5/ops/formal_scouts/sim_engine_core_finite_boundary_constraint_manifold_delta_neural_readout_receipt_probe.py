#!/usr/bin/env python3
"""Finite EngineCore quarantine receipt for delta neural readout."""

from __future__ import annotations

from engine_core_finite_boundary_receipt_utils import write_receipt


CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "engine_core_finite_boundary_classifier"
TOOL_MANIFEST = {
    "engine_core_finite_boundary_receipt_utils": {
        "tried": True,
        "used": True,
        "reason": "supportive shared finite-boundary receipt builder for the exact target",
    }
}
TOOL_INTEGRATION_DEPTH = {"engine_core_finite_boundary_receipt_utils": "supportive"}

CONFIG = {
    "name": "engine_core_finite_boundary_constraint_manifold_delta_neural_readout_receipt_probe",
    "target_name": "constraint_manifold_delta_neural_readout_probe",
    "finite_scope": "paired finite manifold-on/off density-delta readout features over bounded placement slots",
    "admitted_uses": [
        "finite EngineCore density-delta JSON/scalar dependency receipt",
        "bounded readout-feature quarantine evidence",
    ],
}


if __name__ == "__main__":
    raise SystemExit(write_receipt(CONFIG, __file__))
