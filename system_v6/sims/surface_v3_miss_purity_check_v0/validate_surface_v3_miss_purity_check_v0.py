#!/usr/bin/env python3
"""Boundary helper for surface_v3_miss_purity_check_v0."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path


SIM_ID = "surface_v3_miss_purity_check_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_PATH = SIM_DIR / "results" / f"{SIM_ID}_results.json"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    require(errors, RESULT_PATH.is_file(), f"missing result: {RESULT_PATH}")
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    adj = payload.get("adjudication", {})
    rows = payload.get("per_site_reduced_density_matrices", [])
    band = payload.get("predicted_minus_z_cell_radius_band", {})
    auth = payload.get("authority", {})
    tools = payload.get("TOOL_MANIFEST", {})
    depth = payload.get("TOOL_INTEGRATION_DEPTH", {})

    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    require(errors, auth.get("surface_v3_commit") == "b02444162", "surface v3 commit authority missing")
    require(errors, auth.get("alt_view_commit") == "731b61933", "alt-view commit authority missing")
    require(errors, bool(auth.get("v3_jax_source_sha256")), "v3 source hash missing")
    require(errors, bool(auth.get("v3_envelope_result_sha256")), "v3 result hash missing")
    require(errors, len(rows) == 4, "expected four single-site reduced rows")
    require(errors, all(row.get("corrected_cell") == "A33_x00_y00_zp10" for row in rows), "all sites must correct to +z cell")
    require(errors, all(row.get("bloch_radius", 0.0) < band.get("row_radius", 0.0) for row in rows), "radii must be below pure pole radius")
    require(errors, all(row.get("bloch", [0, 0, 0])[2] > 0.0 for row in rows), "reduced z components must be positive")
    require(errors, adj.get("prediction_error_not_recovery_error") is True, "prediction-error adjudication missing")
    require(errors, adj.get("corrected_prediction_recovered_by_v3") is True, "corrected cell recovery missing")
    require(errors, adj.get("alt_view_mixed_marginal_confirmed") is True, "mixed-marginal confirmation missing")
    require(errors, adj.get("alt_view_strict_radius_band_explanation_confirmed") is False, "strict radius-band discriminator should stay false under nearest-neighbor band")
    require(errors, payload.get("cheap_discriminators", {}).get("gauge_mismatch_phase_probe", {}).get("phase_invariant_reduced_states") is True, "phase gauge check failed/missing")
    require(errors, tools.get("numpy", {}).get("reason"), "numpy tool reason missing")
    require(errors, depth.get("numpy") == "load_bearing", "numpy depth must be load_bearing")
    require(errors, bool(payload.get("result_hash")), "result hash missing")
    require(errors, math.isclose(payload["exact_formula_rows"]["bloch_radius_value"], rows[0]["bloch_radius"], rel_tol=0.0, abs_tol=1.0e-12), "formula radius mismatch")

    print(json.dumps({"ok": not errors, "errors": errors, "result_path": str(RESULT_PATH.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
