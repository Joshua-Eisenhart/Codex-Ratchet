#!/usr/bin/env python3
"""Boundary checks for topology_parity_guard_v3."""

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
REQUIRED_CEILING = "scratch_diagnostic_consumer_guard_only_no_new_construction"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == REQUIRED_CEILING, "claim_ceiling mismatch")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")

    gates = payload.get("builder_gates", {})
    require(errors, gates.get("g2a_boundary_from_birth") is True, "G.2a from-birth boundary missing")
    require(errors, gates.get("no_new_cells_introduced") is True, "new-cell introduction must be forbidden")
    require(errors, gates.get("consumer_only") is True, "packet must stay consumer-only")
    require(errors, gates.get("hash_mismatch_stop_rule") is True, "hash mismatch stop rule missing")
    require(errors, gates.get("math_content_separability_added") is True, "math-content separability gate missing")

    source = payload.get("source_complex_lock", {})
    require(errors, source.get("hash_verification_passed") is True, "v2.1 hash verification failed")
    require(errors, source.get("builder_betti_computed") is False, "builder Betti boundary failed")
    require(errors, source.get("builder_homology_computed") is False, "builder homology boundary failed")

    refs = payload.get("reference_gate", {})
    require(errors, refs.get("reference_gate_passed") is True, "reference gate must pass")
    require(
        errors,
        refs.get("explicit_lens_space_l31", {}).get("homology", {}).get("torsion", {}).get("H1") == [3],
        "L(3,1) reference must compute H1=Z/3",
    )

    separability = payload.get("math_content_separability", {})
    require(errors, separability.get("passed") is True, "boundary-matrix-only separability failed")
    require(errors, separability.get("boundary_matrix_only_distinct_hash_count") == 2, "pure complex count must be two")

    complexes = payload.get("complexes", {})
    shifted = complexes.get("v2_1_shifted_degree_one_mod3", {})
    require(errors, shifted.get("homology", {}).get("betti_b0_b1_b2_b3") == [1, 0, 0, 1], "shifted Betti mismatch")
    require(errors, shifted.get("homology", {}).get("torsion", {}).get("H1") == [3], "shifted H1 torsion mismatch")
    for complex_id in (
        "zero_shift_product_control",
        "wrong_gluing_generator_not_threaded_control",
        "old_v2_regression_coboundary_control",
    ):
        row = complexes.get(complex_id, {})
        require(errors, row.get("homology", {}).get("betti_b0_b1_b2_b3") == [1, 1, 1, 1], f"{complex_id} Betti mismatch")
        require(errors, all(not values for values in row.get("homology", {}).get("torsion", {}).values()), f"{complex_id} torsion must be empty")

    controls = payload.get("controls", {})
    require(errors, controls.get("degree_2_torsion_trap", {}).get("pass") is True, "degree-2 torsion trap must pass")

    adjudication = payload.get("adjudication", {})
    require(errors, adjudication.get("winner") == "READING_A_REPAIRED_WINS", "adjudication winner mismatch")
    require(errors, adjudication.get("formal_admission_allowed") is False, "adjudication must not imply formal admission")

    disallowed = set(payload.get("disallowed_claims", []))
    for claim in {"new construction", "target Betti fitting", "formal admission", "work-order update"}:
        require(errors, claim in disallowed, f"missing disallowed claim: {claim}")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
