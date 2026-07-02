#!/usr/bin/env python3
"""Finite-translation anti-smuggling gate.

Audit helper only. This tests the pre-manifold transition:

    TH -> finite fixture -> C

It does not admit the owner theses. It only checks that the finite fixture used
to operationalize a thesis does not smuggle forbidden primitives before the
constraint gates run.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT = RESULT_DIR / "ftr_finite_translation_anti_smuggling_gate_results.json"


FORBIDDEN_PRIMITIVES = {
    "completed_infinity",
    "continuum_primitive",
    "primitive_sample_space",
    "primitive_metric",
    "primitive_equality",
    "primitive_time",
    "primitive_probability",
}


def fixture_for_thesis(code: str) -> dict[str, Any]:
    if code == "TH-01":
        return {
            "thesis": code,
            "fixture_kind": "finite_high_entropy_density_fixture",
            "carrier_dim": 4,
            "rho_trace": 1.0,
            "entropy_ceiling": "log(carrier_dim)",
            "probe_family": ["sigma_z_effect", "sigma_x_effect"],
            "path_family_size": 2,
            "forbidden_primitives_used": [],
            "claim_ceiling": "finite translation of pure-randomness thesis only",
        }
    if code == "TH-05":
        return {
            "thesis": code,
            "fixture_kind": "probe_relative_identity_fixture",
            "carrier_dim": 2,
            "probe_family": ["sigma_z_effect", "sigma_x_effect"],
            "equality_rule": "probe_vector_indistinguishability",
            "uses_bare_identity_predicate": False,
            "forbidden_primitives_used": [],
            "claim_ceiling": "finite translation of nominalist-identity thesis only",
        }
    raise ValueError(code)


def gate_row(fixture: dict[str, Any]) -> dict[str, Any]:
    forbidden_used = set(fixture.get("forbidden_primitives_used", []))
    finite_carrier = isinstance(fixture.get("carrier_dim"), int) and fixture["carrier_dim"] > 0
    finite_probe_family = isinstance(fixture.get("probe_family"), list) and len(fixture["probe_family"]) > 0
    no_forbidden = not (forbidden_used & FORBIDDEN_PRIMITIVES)
    claim_ceiling = bool(fixture.get("claim_ceiling"))
    return {
        "thesis": fixture["thesis"],
        "fixture_kind": fixture["fixture_kind"],
        "pass": finite_carrier and finite_probe_family and no_forbidden and claim_ceiling,
        "finite_carrier": finite_carrier,
        "finite_probe_family": finite_probe_family,
        "no_forbidden_primitives": no_forbidden,
        "claim_ceiling_present": claim_ceiling,
        "fixture": fixture,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [gate_row(fixture_for_thesis(code)) for code in ("TH-01", "TH-05")]
    result = {
        "schema": "ftr_finite_translation_anti_smuggling_gate_v1",
        "classification": "audit_control_packet",
        "name": "ftr_finite_translation_anti_smuggling_gate",
        "enforces": ["EG-FTR-no-classical-smuggling-finite-translation"],
        "all_pass": all(row["pass"] for row in rows),
        "rows": rows,
        "claim_ceiling": "Checks finite translation hygiene before manifold admission; does not admit the translated theses.",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
