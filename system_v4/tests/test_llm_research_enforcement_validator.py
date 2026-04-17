from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "system_v4" / "skills" / "llm_research_enforcement_validator.py"


def load_module():
    if not SCRIPT_PATH.exists():
        pytest.fail(f"missing validator script: {SCRIPT_PATH}")
    spec = importlib.util.spec_from_file_location("llm_research_enforcement_validator", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("unable to load llm_research_enforcement_validator module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_closeout(*, status: str = "runs") -> dict:
    return {
        "class": "A",
        "claim_type": "bounded local probe",
        "target_family": "density_matrices",
        "file": "system_v4/probes/sim_density_probe.py",
        "result_file": "system_v4/probes/a2_state/sim_results/density_probe_results.json",
        "fresh_rerun": "N" if status != "canonical by process" else "Y",
        "status": status,
        "load_bearing_tools": ["z3"] if status == "canonical by process" else [],
        "negative_tests": "Y",
        "open_gaps": "next bounded coupling step",
    }


@pytest.mark.parametrize("status", ["exists", "runs", "passes local rerun", "canonical by process"])
def test_validate_closeout_accepts_current_controller_status_terms(status: str):
    mod = load_module()
    errors = mod.validate_closeout(valid_closeout(status=status))
    assert errors == []


@pytest.mark.parametrize("legacy_status", ["runs locally", "proof-backed"])
def test_validate_closeout_rejects_legacy_status_terms(legacy_status: str):
    mod = load_module()
    errors = mod.validate_closeout(valid_closeout(status=legacy_status))
    assert any("invalid_status" in err for err in errors)


def test_validate_gap_matrix_rejects_legacy_status_term_entries(tmp_path: Path):
    mod = load_module()
    matrix_path = tmp_path / "gap_matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "execution_ladder": [
                    "A_local",
                    "B_pairwise_coupling",
                    "C_multi_shell_coexistence",
                    "D_topology_variant",
                    "E_emergence",
                ],
                "status_terms": ["exists", "runs locally", "passes local rerun", "proof-backed", "canonical by process"],
                "claim_tool_map": {"impossibility_forced": {"required": "z3", "cross_check": "cvc5"}},
                "families": [
                    {
                        "family": "density_matrices",
                        "cells": {
                            "A_local": "GAP",
                            "B_pairwise_coupling": "GAP",
                            "C_multi_shell_coexistence": "GAP",
                            "D_topology_variant": "GAP",
                            "E_emergence": "GAP",
                        },
                        "evidence": [],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    errors = mod.validate_gap_matrix(str(matrix_path))
    assert any("status_terms" in err for err in errors)



def test_main_blocks_emergence_closeout_without_a_to_d_support(tmp_path: Path):
    mod = load_module()
    closeout_path = tmp_path / "closeout.json"
    closeout_path.write_text(
        json.dumps(
            {
                **valid_closeout(status="canonical by process"),
                "class": "E",
                "target_family": "density_matrices",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    matrix_path = tmp_path / "gap_matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "execution_ladder": [
                    "A_local",
                    "B_pairwise_coupling",
                    "C_multi_shell_coexistence",
                    "D_topology_variant",
                    "E_emergence",
                ],
                "status_terms": ["exists", "runs", "passes local rerun", "canonical by process"],
                "claim_tool_map": {"impossibility_forced": {"required": "z3", "cross_check": "cvc5"}},
                "families": [
                    {
                        "family": "density_matrices",
                        "cells": {
                            "A_local": "DONE",
                            "B_pairwise_coupling": "PARTIAL",
                            "C_multi_shell_coexistence": "GAP",
                            "D_topology_variant": "DONE",
                            "E_emergence": "GAP",
                        },
                        "evidence": [],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    rc = mod.main(["validator", str(closeout_path), str(matrix_path)])
    assert rc == 1
