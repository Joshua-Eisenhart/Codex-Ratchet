#!/usr/bin/env python3
"""Finite EngineCore quarantine receipt for PEPS3D 32/64 capacity readouts."""

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
    "name": "engine_core_finite_boundary_source_native_peps3d_32_64_site_capacity_receipt_probe",
    "target_name": "source_native_peps3d_32_64_site_capacity_probe",
    "finite_scope": "finite source-history replay into 32/64-site PEPS3D capacity signatures",
    "admitted_uses": [
        "finite EngineCore PEPS3D capacity JSON/scalar dependency receipt",
        "bounded capacity-signature quarantine evidence",
    ],
}


if __name__ == "__main__":
    raise SystemExit(write_receipt(CONFIG, __file__))
