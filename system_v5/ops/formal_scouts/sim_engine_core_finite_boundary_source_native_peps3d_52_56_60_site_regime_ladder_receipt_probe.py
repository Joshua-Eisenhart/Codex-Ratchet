#!/usr/bin/env python3
"""Finite EngineCore quarantine receipt for PEPS3D 52/56/60 ladder readouts."""

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
    "name": "engine_core_finite_boundary_source_native_peps3d_52_56_60_site_regime_ladder_receipt_probe",
    "target_name": "source_native_peps3d_52_56_60_site_regime_ladder_probe",
    "finite_scope": "finite slot-record replay into 52/56/60-site PEPS3D regime-ladder signatures",
    "admitted_uses": [
        "finite EngineCore PEPS3D ladder JSON/scalar dependency receipt",
        "bounded regime-ladder quarantine evidence",
    ],
}


if __name__ == "__main__":
    raise SystemExit(write_receipt(CONFIG, __file__))
