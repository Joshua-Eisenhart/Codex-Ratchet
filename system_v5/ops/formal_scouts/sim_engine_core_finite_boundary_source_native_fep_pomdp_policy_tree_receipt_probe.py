#!/usr/bin/env python3
"""Finite EngineCore quarantine receipt for the FEP/POMDP policy tree."""

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
    "name": "engine_core_finite_boundary_source_native_fep_pomdp_policy_tree_receipt_probe",
    "target_name": "source_native_fep_pomdp_policy_tree_probe",
    "finite_scope": "finite A/B/C/D policy-tree matrices and bounded policy score readouts",
    "admitted_uses": [
        "finite EngineCore policy-tree JSON/scalar dependency receipt",
        "bounded POMDP matrix/readout quarantine evidence",
    ],
}


if __name__ == "__main__":
    raise SystemExit(write_receipt(CONFIG, __file__))
