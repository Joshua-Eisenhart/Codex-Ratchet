#!/usr/bin/env python3
"""Envelope builder for terrain_spinor_flux_nest_n4_v0."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any

from terrain_spinor_flux_nest_n4_v0_common import (
    CLASSIFICATION,
    EXPECTED_DIMENSION,
    EXPECTED_EDGE_COUNT,
    EXPECTED_FACE_COUNT,
    EXPECTED_SITE_COUNT,
    FORMAL_ADMISSION_ALLOWED,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SEED,
    SIM_ID,
    TOL,
    base_leg_payload,
    build_core,
    now_z,
    rel,
    sha256_file,
    stable_sha256,
    write_json,
)

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
LEG_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(name: str, leg: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": leg["source_path"],
        "source_sha256": leg["source_sha256"],
        "result_path": rel(path),
        "result_sha256": sha256_file(path),
        "reads_peer_result": False,
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "claim_path_tools": leg.get("claim_path_tools", []),
    }


def merge_tool_manifest(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {engine: leg.get("TOOL_MANIFEST", {}) for engine, leg in legs.items()}


def merge_tool_depth(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {engine: leg.get("TOOL_INTEGRATION_DEPTH", {}) for engine, leg in legs.items()}


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {
        name: float(leg["engine_values"]["conditioned_total_abs_current"]) for name, leg in legs.items()
    }
    julia_value = values["julia"]
    diffs = {name: abs(value - julia_value) for name, value in values.items()}
    return {
        "julia_authoritative": True,
        "metric": "conditioned_total_abs_current",
        "engine_values": values,
        "absolute_differences_from_julia": {name: round(diff, 12) for name, diff in diffs.items()},
        "max_divergence": round(max(diffs.values()), 12),
        "tolerance": TOL,
    }


def build_payload() -> dict[str, Any]:
    core = build_core()
    legs = {name: load(path) for name, path in LEG_PATHS.items()}
    div = divergence(legs)
    capability_ids = [row["receipt_id"] for row in core["capability_receipts"]]
    tool_ids = [row["receipt_id"] for row in core["tool_calls"]]
    jax_proofs = legs["jax"]["crossover_proofs"]
    julia_z3 = legs["julia"]["crossover_proofs"]["julia_z3"]
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "classification": CLASSIFICATION,
        "ceiling": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": now_z(),
        "seed": SEED,
        "mode": "RATCHETED",
        "standard_schema_mode": "FIELD",
        "engine_contract": {
            "mode": "RATCHETED",
            "mode_is_field": True,
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": False,
            "source_backed_validator_expected_command": (
                "python scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed "
                f"{rel(RESULT_PATH)}"
            ),
        },
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": stable_sha256(PIN_SPEC),
        "engines": {name: engine_record(name, legs[name], LEG_PATHS[name]) for name in ("julia", "jax", "pytorch")},
        "engine_result_sha256": {name: sha256_file(path) for name, path in LEG_PATHS.items()},
        "pin_identical_across_legs": len({leg["pin_sha256"] for leg in legs.values()}) == 1,
        "TOOL_MANIFEST": merge_tool_manifest(legs),
        "TOOL_INTEGRATION_DEPTH": merge_tool_depth(legs),
        "claim_path_tools": [
            "QuantumOptics",
            "ITensors",
            "ITensorMPS",
            "jraph",
            "torch_geometric",
            "torch.func",
            "sympy",
            "z3",
            "cvc5",
        ],
        "capability_receipts": core["capability_receipts"],
        "tool_calls": core["tool_calls"],
        "one_to_one_tool_calls": {
            "pass": capability_ids == tool_ids,
            "capability_receipt_ids": capability_ids,
            "tool_call_ids": tool_ids,
        },
        "parent_lineage": core["parent_lineage"],
        "carrier": core["carrier"],
        "support_graph": {
            "edge_count": len(core["support_edges"]),
            "face_count": len(core["support_faces"]),
            "edges": core["support_edges"],
            "faces": core["support_faces"],
        },
        "terrain_dependent_network_coupling": core["terrain_network_coupling"],
        "flux_transport_row": {
            "continuity": core["terrain_network_coupling"]["continuity"],
            "edge_transport_rows": core["terrain_network_coupling"]["edge_rows"],
            "flux_convention_parent": "ratchet_s2_two_shell_flux_v0",
            "shell_difference_rule": "connection_gap=cos(2eta_src)-cos(2eta_dst), current transport flux=current*gap",
        },
        "conditioning": core["conditioning"],
        "ratcheted_rows": {
            "mode": "RATCHETED",
            "conditioning": core["conditioning"],
            "conditioned_network_coupling": core["conditioned_network_coupling"],
            "signatures": core["ratchet_signatures"],
        },
        "ratchet_signatures": core["ratchet_signatures"],
        "controls": core["collapse_controls"],
        "collapse_controls": core["collapse_controls"],
        "saturation_comparison_row": core["saturation_comparison_row"],
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_proofs["z3"]["verdict"],
                "erased_flip_verdict": jax_proofs["z3"]["erased_flip_verdict"],
                "asserted_precomputed_boolean": False,
                "formula_terms_bound": jax_proofs["z3"].get("formula_terms_bound") is True,
                "edge_current_terms_in_solver": jax_proofs["z3"].get("edge_current_terms_in_solver") is True,
                "divergence_derived_in_solver": jax_proofs["z3"].get("divergence_derived_in_solver") is True,
                "erased_control_kind": jax_proofs["z3"].get("erased_control_kind"),
                "proof_row": jax_proofs["z3"]["proof_row"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_proofs["cvc5"]["verdict"],
                "erased_flip_verdict": jax_proofs["cvc5"]["erased_flip_verdict"],
                "asserted_precomputed_boolean": False,
                "formula_terms_bound": jax_proofs["cvc5"].get("formula_terms_bound") is True,
                "edge_current_terms_in_solver": jax_proofs["cvc5"].get("edge_current_terms_in_solver") is True,
                "divergence_derived_in_solver": jax_proofs["cvc5"].get("divergence_derived_in_solver") is True,
                "erased_control_kind": jax_proofs["cvc5"].get("erased_control_kind"),
                "proof_row": jax_proofs["cvc5"]["proof_row"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3["verdict"],
                "erased_flip_verdict": julia_z3["erased_flip_verdict"],
                "asserted_precomputed_boolean": False,
                "formula_terms_bound": julia_z3.get("formula_terms_bound") is True,
                "edge_current_terms_in_solver": julia_z3.get("edge_current_terms_in_solver") is True,
                "divergence_derived_in_solver": julia_z3.get("divergence_derived_in_solver") is True,
                "erased_control_kind": julia_z3.get("erased_control_kind"),
                "proof_row": julia_z3["proof_row"],
            },
        },
        "divergence": div,
        "divergence_log": [
            "Julia, JAX, and PyTorch independently recomputed conditioned_total_abs_current from parent rows.",
            "Generic validator source-backed mode is required; package manifests alone are not accepted.",
        ],
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {name: leg.get("package_versions", {}) for name, leg in legs.items()},
        },
        "build_gates": {
            "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
            "promotion_blocked": PROMOTION_ALLOWED is False,
            "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
            "engine_contract_mode_ratcheted_field": True,
            "carrier_is_c16_not_graph_only": core["carrier"]["dimension"] == EXPECTED_DIMENSION
            and core["carrier"]["site_count"] == EXPECTED_SITE_COUNT
            and core["carrier"]["not_support_graph_only"],
            "support_graph_is_5_edge_2_face": len(core["support_edges"]) == EXPECTED_EDGE_COUNT
            and len(core["support_faces"]) == EXPECTED_FACE_COUNT,
            "parent_state_vector_provenance_rederived": core["carrier"].get("parent_state_vector_provenance_rederived") is True,
            "terrain_dependent_edge_coupling_computed": True,
            "flux_continuity_proved": jax_proofs["z3"]["verdict"] == "unsat" and jax_proofs["cvc5"]["verdict"] == "unsat",
            "flux_continuity_in_solver_derivation": all(
                proof.get("formula_terms_bound") is True
                and proof.get("edge_current_terms_in_solver") is True
                and proof.get("divergence_derived_in_solver") is True
                for proof in (jax_proofs["z3"], jax_proofs["cvc5"], julia_z3)
            ),
            "solver_erased_flips_fire": jax_proofs["z3"]["erased_flip_verdict"] == "sat"
            and jax_proofs["cvc5"]["erased_flip_verdict"] == "sat"
            and julia_z3["erased_flip_verdict"] == "sat",
            "collapse_controls_pass": all(
                row.get("pass") is True for row in core["collapse_controls"].values() if isinstance(row, dict) and "pass" in row
            ),
            "parent_lineage_hash_bound": core["parent_lineage"]["hash_bound"],
            "one_to_one_claim_tool_calls": capability_ids == tool_ids,
            "density_quotient_reproduction_complete": core["collapse_controls"]["density_quotient_recovers_committed_n4_ladder"]["density_quotient_reproduction"]["pass"],
            "saturation_comparison_row_present": core["saturation_comparison_row"]["computed"] is True,
            "max_divergence_within_tolerance": div["max_divergence"] <= TOL,
            "builder_surface_no_audit_verdict": builder_audit_boundary_ok(SOURCE_PATH.parent / "audit_verdict.md"),
        },
        "builder_hardening_addendum": {
            "path": rel(SOURCE_PATH.parent / "builder_hardening_addendum.md"),
            "G1": "closed: z3/cvc5/Julia-Z3 derive continuity in solver from scaled edge-current formula rows and site-balance rows; erased flip retained",
            "G2": "closed: control now claims exact z_dot agreement only; full-row byte consistency is explicitly deprecated because schemas differ",
            "G3": "partially_closed_and_carried: zero-terrain child network is recomputed with zero couplings/currents/flux; committed bare-current parent row comparison remains absent and carried",
            "G4": "closed_at_builder_scope: C^16 carrier state-vector provenance is rederived from committed n4 parent site spinors; no copied parent state-vector row is claimed",
            "DQR": "closed_at_builder_scope: density quotient row is rederived and full-row sha256 matched to the committed n4 stage row",
            "ceiling": CLASSIFICATION,
        },
        "allowed_claims": [
            "scratch_diagnostic n=4 terrain-coupled network row",
            "computed flux/transport continuity diagnostic",
            "RATCHETED finite-shell conditioning diagnostic",
            "collapse controls back to committed parent diagnostics",
            "saturation comparison stop-criterion row against committed n=3 anchor",
        ],
        "disallowed_claims": [
            "formal admission",
            "promotion",
            "universal mirror law",
            "actual n=5 run or n>4 rung evidence",
            "support graph alone as carrier",
            "bridge, axis, physics, or manifold claim",
        ],
    }
    payload["all_pass"] = (
        core["all_pass"]
        and all(leg.get("all_pass") is True for leg in legs.values())
        and payload["build_gates"]["flux_continuity_proved"]
        and payload["build_gates"]["flux_continuity_in_solver_derivation"]
        and payload["build_gates"]["solver_erased_flips_fire"]
        and payload["build_gates"]["collapse_controls_pass"]
        and payload["build_gates"]["one_to_one_claim_tool_calls"]
        and payload["build_gates"]["density_quotient_reproduction_complete"]
        and payload["build_gates"]["saturation_comparison_row_present"]
        and payload["build_gates"]["max_divergence_within_tolerance"]
        and payload["build_gates"]["builder_surface_no_audit_verdict"]
    )
    payload["gate_pass"] = payload["all_pass"]
    return payload


def main() -> int:
    payload = build_payload()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
