#!/usr/bin/env python3
"""Boundary helpers for the 3Q runtime-flux scratch packet."""

from __future__ import annotations

import json

import gcm_runtime_flux_3q_v0_common as common


def boundary_payload() -> dict:
    return {
        "sim_id": common.SIM_ID,
        "classification": common.CLASSIFICATION,
        "declared_surface": common.DECLARED_SURFACE,
        "claim_ceiling": common.CLAIM_CEILING,
        "not_engine_admission": True,
        "not_physics": True,
        "not_geometric_hopf_flux": True,
        "carrier_and_pins_relative": True,
        "not_admitted_invariants": True,
        "no_builder_audit_verdict": True,
    }


def main() -> int:
    print(json.dumps(boundary_payload(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
