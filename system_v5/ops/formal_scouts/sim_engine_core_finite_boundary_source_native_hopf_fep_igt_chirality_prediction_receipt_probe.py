#!/usr/bin/env python3
"""Finite EngineCore quarantine receipt for Hopf/FEP/IGT chirality prediction."""

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
    "name": "engine_core_finite_boundary_source_native_hopf_fep_igt_chirality_prediction_receipt_probe",
    "target_name": "source_native_hopf_fep_igt_chirality_prediction_probe",
    "finite_scope": "finite Hopf-base displacement prediction rows and scalar prediction-error readouts",
    "admitted_uses": [
        "finite EngineCore chirality-prediction JSON/scalar dependency receipt",
        "bounded Hopf/FEP/IGT readout quarantine evidence",
    ],
}


if __name__ == "__main__":
    raise SystemExit(write_receipt(CONFIG, __file__))
