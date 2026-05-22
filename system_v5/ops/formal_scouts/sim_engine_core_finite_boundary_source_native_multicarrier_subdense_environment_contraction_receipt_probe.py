#!/usr/bin/env python3
"""Finite EngineCore quarantine receipt for multicarrier subdense readouts."""

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
    "name": "engine_core_finite_boundary_source_native_multicarrier_subdense_environment_contraction_receipt_probe",
    "target_name": "source_native_multicarrier_subdense_environment_contraction_probe",
    "finite_scope": "finite stage-record consumption into local MPS/PEPS/PEPS3D environment readouts",
    "admitted_uses": [
        "finite EngineCore multicarrier JSON/scalar dependency receipt",
        "bounded local-environment readout quarantine evidence",
    ],
}


if __name__ == "__main__":
    raise SystemExit(write_receipt(CONFIG, __file__))
