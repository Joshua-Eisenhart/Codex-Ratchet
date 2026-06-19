#!/usr/bin/env python3
"""Boundary checks for fiber_augmented_cover_v2_1."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
REQUIRED_CEILING = "axis_readout_candidate_only + decisive_repair_cover_no_admission"
VALID_LAW_STATUS = {
    "holds_on_decisive_repin_cover",
    "fails_on_decisive_repin_cover",
    "inconclusive_no_nonneutral_rows",
}
REQUIRED_COMPLEX_IDS = {
    "v2_1_shifted_degree_one_mod3",
    "zero_shift_product_control",
    "wrong_gluing_generator_not_threaded_control",
    "old_v2_regression_coboundary_control",
}
TOOL_MANIFEST = {
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "checks post-audit-idempotent G.2a boundary flags"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves packet and helper paths for boundary checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "builder_audit_boundary": "supportive",
    "pathlib": "supportive",
}


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _require_no_betti_field(errors: list[str], value: Any, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            require(errors, key.lower() != "betti", f"{path} must not contain a betti field")
            _require_no_betti_field(errors, child, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            _require_no_betti_field(errors, child, f"{path}[{idx}]")


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == REQUIRED_CEILING, "claim_ceiling mismatch")
    require(errors, payload.get("betti_computed") is False, "builder packet must not compute Betti")
    require(errors, payload.get("homology_computed") is False, "builder packet must not compute homology")
    _require_no_betti_field(errors, payload)

    base = payload.get("cellular_base", {})
    require(errors, base.get("v2_base_unchanged_by_hash") is True, "v2 base hash must be unchanged")
    require(errors, base.get("chain_sha256") == base.get("expected_chain_sha256"), "v2 base hash mismatch")
    require(errors, base.get("cell_counts") == {"C0": 33, "C1": 92, "C2": 61}, "cellular base counts mismatch")
    require(errors, base.get("euler_characteristic") == 2, "cellular base chi must be 2")
    require(errors, base.get("chain_checks", {}).get("d_squared_zero") is True, "base d^2 check failed")

    central = payload.get("central_math_adjudication", {})
    require(errors, central.get("not_a_reinterpretation_of_old_construction") is True, "v2.1 must be marked as a different pinned construction")
    require(errors, central.get("v2_1_seam_steps") == [1, 0, 0, 0], "v2.1 seam steps must be [1,0,0,0]")
    require(errors, central.get("v2_1_mod_fiber_holonomy") == 1, "v2.1 mod holonomy must be 1")
    require(errors, central.get("v2_1_integer_lift_sum") == 1, "v2.1 integer lift sum must be 1")

    family = payload.get("complex_family", {})
    require(errors, set(family.get("complex_order", [])) == REQUIRED_COMPLEX_IDS, "complex family ids mismatch")
    require(errors, family.get("all_d_squared_zero") is True, "all complexes must satisfy d^2=0")
    require(errors, family.get("betti_computed") is False, "complex family must not compute Betti")
    require(errors, family.get("homology_computed") is False, "complex family must not compute homology")
    complexes = family.get("complexes", {})
    for complex_id in REQUIRED_COMPLEX_IDS:
        row = complexes.get(complex_id, {})
        require(errors, row.get("cell_counts") == {"C0": 1, "C1": 1, "C2": 1, "C3": 1}, f"{complex_id} cell counts mismatch")
        require(errors, row.get("chain_checks", {}).get("d_squared_zero") is True, f"{complex_id} d^2 failed")
        require(errors, bool(row.get("chain_sha256")), f"{complex_id} missing chain hash")
        for matrix_name, matrix in row.get("boundary_matrices", {}).items():
            require(errors, matrix.get("format") == "sparse_coo", f"{complex_id} {matrix_name} must use sparse_coo")
            require(errors, bool(matrix.get("sha256")), f"{complex_id} {matrix_name} missing sha256")
        require(errors, row.get("betti_computed") is False, f"{complex_id} must not compute Betti")
        require(errors, row.get("homology_computed") is False, f"{complex_id} must not compute homology")

    shifted = complexes.get("v2_1_shifted_degree_one_mod3", {})
    require(errors, shifted.get("integer_lift_and_mod_holonomy", {}).get("mod_fiber_holonomy") == 1, "shifted complex must have mod-3 holonomy 1")
    require(errors, shifted.get("integer_lift_and_mod_holonomy", {}).get("integer_lift_sum") == 1, "shifted complex integer lift sum mismatch")
    require(errors, shifted.get("clutching", {}).get("attaches_fiber_cycle_with_coefficient") == 3, "shifted complex must attach fiber cycle with coefficient 3")
    require(errors, shifted.get("clutching", {}).get("threading_gate_passed") is True, "shifted complex threading gate failed")

    zero = complexes.get("zero_shift_product_control", {})
    require(errors, zero.get("integer_lift_and_mod_holonomy", {}).get("mod_fiber_holonomy") == 0, "zero control holonomy must be 0")
    require(errors, zero.get("clutching", {}).get("gate_passed") is True, "zero control gate must pass as refused control")

    wrong = complexes.get("wrong_gluing_generator_not_threaded_control", {})
    require(errors, wrong.get("integer_lift_and_mod_holonomy", {}).get("mod_fiber_holonomy") == 1, "wrong-gluing control must expose generator holonomy")
    require(errors, wrong.get("clutching", {}).get("threading_gate_passed") is False, "wrong-gluing control must fail threading")
    require(errors, wrong.get("clutching", {}).get("gate_passed") is True, "wrong-gluing control gate must pass as refused control")

    old = complexes.get("old_v2_regression_coboundary_control", {})
    require(errors, old.get("integer_lift_and_mod_holonomy", {}).get("integer_lift_sum") == 3, "old v2 integer lift sum must be 3")
    require(errors, old.get("integer_lift_and_mod_holonomy", {}).get("mod_fiber_holonomy") == 0, "old v2 mod holonomy must be 0")
    require(errors, old.get("integer_lift_and_mod_holonomy", {}).get("old_integer_lift_winding_if_divisible") == 1, "old v2 integer winding must be preserved")

    require(errors, len(payload.get("integer_lift_rows", [])) == 4, "integer/mod holonomy rows must cover all emitted complexes")

    law = payload.get("b6_law_test", {})
    require(errors, law.get("table_kind") == "faithful_decisive_repin_fiber_augmented_cover_table", "wrong law table kind")
    require(errors, law.get("construction_row") == "third_construction_v2_1_mod3_repin", "law table must identify the third construction")
    require(errors, law.get("witness_gate_passed") is True, "law table witness gate failed")
    require(errors, law.get("sample_total") == 99, "law table must have 99 cover states")
    require(errors, law.get("law_test_status") in VALID_LAW_STATUS, "invalid v2.1 law status")
    require(errors, law.get("relation_not_used_to_assign_axis3") is True, "Axis3 must not be assigned from b6 relation")
    require(errors, len(payload.get("sign_variant_table", [])) == 8, "full 8-variant table is required")

    faith = payload.get("faithfulness", {})
    require(errors, faith.get("axis0", {}).get("projects_to_committed_axis0") is True, "Axis0 pullback faithfulness failed")
    require(errors, faith.get("axis3", {}).get("source_backed_equivalent_adapter") is True, "Axis3 source-backed adapter missing")
    require(errors, faith.get("axis3", {}).get("predicate_mismatch_count") == 0, "Axis3 predicate mismatch count must be zero")
    require(errors, faith.get("axis6", {}).get("projects_to_committed_axis6") is True, "Axis6 pullback faithfulness failed")

    controls = payload.get("controls", {})
    require(errors, controls.get("zero_shift_product_control", {}).get("law_table_refused") is True, "zero-shift control must refuse law rows")
    require(errors, controls.get("wrong_gluing_control", {}).get("law_table_refused") is True, "wrong-gluing control must refuse law rows")
    require(errors, controls.get("v2_regression_old_shifts", {}).get("finite_triviality_reproduced") is True, "old v2 regression must reproduce finite triviality")
    require(errors, controls.get("scrambled_control", {}).get("ran") is True, "scrambled control must run")
    require(errors, controls.get("convention_flip_control", {}).get("ran") is True, "convention-flip control must run")

    for solver, row in payload.get("smt_rows", {}).items():
        require(errors, row.get("verdict") == "unsat", f"{solver} SMT verdict must be unsat")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{solver} erased flip must be sat")

    disallowed = set(payload.get("disallowed_claims", []))
    for claim in {
        "Betti computation",
        "homology certificate",
        "lens-space certificate",
        "SECOND certificate",
        "formal admission",
        "canonical by process",
        "physics/manifold claim",
        "global disproof of b6 law",
    }:
        require(errors, claim in disallowed, f"missing disallowed claim: {claim}")

    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")
    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
