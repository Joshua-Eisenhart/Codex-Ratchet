#!/usr/bin/env python3
"""Validator for rpf_chirality_grounded_v0."""

from __future__ import annotations

import json
import os
import sys
from typing import Any


SIM_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_PATH = os.path.join(SIM_DIR, "results", "rpf_chirality_grounded_v0_results.json")


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def validate(result: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    require(result.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic", failures)
    require(result.get("promotion_allowed") is False, "promotion_allowed must be false", failures)
    require(result.get("formal_admission_allowed") is False, "formal_admission_allowed must be false", failures)
    require(result.get("all_pass") is True, "all_pass must be true", failures)
    require(result.get("chirality_earned_on_grounded_carrier") is True, "chirality_earned_on_grounded_carrier must be true", failures)

    hard = result.get("HARD_ACCEPTANCE", {})
    require(hard.get("L_R_different_survivors_on_chiral_carrier") is True, "L/R survivor divergence failed", failures)
    require(hard.get("independent_mirror_maps_L_to_R_not_constructor_swap") is True, "independent mirror failed", failures)
    require(hard.get("non_chiral_symmetric_control_L_equals_R") is True, "symmetric control collapse failed", failures)

    chirality = result.get("CHIRALITY_TEST", {})
    require(chirality.get("present_survivor_L") != chirality.get("present_survivor_R"), "L and R survivors are equal", failures)
    require(chirality.get("L_R_optimal_survivor_sets_disjoint") is True, "L/R optimal survivor sets overlap", failures)

    mirror = result.get("INDEPENDENT_MIRROR_TEST", {})
    require(mirror.get("P_is_independent_data_operation") is True, "P is not marked independent", failures)
    require(mirror.get("P_is_involution") is True, "P is not an involution", failures)
    require(mirror.get("P_moves_field") is True, "P does not move field", failures)
    require(mirror.get("equivariance_P_maps_L_to_R") is True, "P(L) != R over P(F)", failures)
    require(mirror.get("equivariance_P_maps_R_to_L") is True, "P(R) != L over P(F)", failures)
    require(mirror.get("engines_are_distinct_functions_objective_sha_differ") is True, "engine objective SHAs do not differ", failures)
    require(mirror.get("is_gnvw_swap_tautology") is False, "mirror marked as GNVW swap tautology", failures)

    symmetric = result.get("SYMMETRIC_CONTROL_COLLAPSE", {})
    require(symmetric.get("sigma_y_signs_all_zero") is True, "symmetric subcarrier sigma_y signs not all zero", failures)
    require(symmetric.get("L_equals_R_on_symmetric_subcarrier") is True, "L/R do not collapse on symmetric subcarrier", failures)
    require(
        symmetric.get("present_survivor_L_symmetric") == symmetric.get("present_survivor_R_symmetric"),
        "symmetric-control survivors differ",
        failures,
    )

    quotient = result.get("quotient_reproduction", {})
    require(quotient.get("reproduces_grounded_carve_8_classes") is True, "base x/z quotient did not reproduce 8 classes", failures)

    source = result.get("source_grounded_carrier", {})
    require(source.get("branch_count") == 16, "source carrier branch count is not 16", failures)
    require(source.get("all_density_matrices_valid") is True, "source density matrices invalid", failures)

    tools = result.get("tool_integration_depth", {})
    require(tools.get("numpy") == "load_bearing", "numpy must be load_bearing", failures)
    require(tools.get("itertools") == "load_bearing", "itertools must be load_bearing", failures)
    require(tools.get("hashlib") == "load_bearing", "hashlib must be load_bearing", failures)

    return failures


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else RESULT_PATH
    with open(path, "r", encoding="utf-8") as f:
        result = json.load(f)
    failures = validate(result)
    print(json.dumps({
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "path": os.path.relpath(path, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SIM_DIR))))),
    }, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
