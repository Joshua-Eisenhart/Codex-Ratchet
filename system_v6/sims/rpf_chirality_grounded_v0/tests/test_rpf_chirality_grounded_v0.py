#!/usr/bin/env python3
"""Minimal local assertions for rpf_chirality_grounded_v0."""

from __future__ import annotations

import os
import sys


SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SIM_DIR not in sys.path:
    sys.path.insert(0, SIM_DIR)

import rpf_chirality_grounded_v0 as sim  # noqa: E402
import validate_rpf_chirality_grounded_v0 as validator  # noqa: E402


def test_result_acceptance() -> None:
    result = sim.build_result()
    failures = validator.validate(result)
    assert failures == []
    assert result["CHIRALITY_TEST"]["present_survivor_L"] != result["CHIRALITY_TEST"]["present_survivor_R"]
    assert result["INDEPENDENT_MIRROR_TEST"]["is_gnvw_swap_tautology"] is False
    assert result["SYMMETRIC_CONTROL_COLLAPSE"]["L_equals_R_on_symmetric_subcarrier"] is True


if __name__ == "__main__":
    test_result_acceptance()
    print("ok")
