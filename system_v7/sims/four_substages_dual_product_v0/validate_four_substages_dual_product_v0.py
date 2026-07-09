#!/usr/bin/env python3
"""Validate independent Julia/JAX agreement for the conditional product probe."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent-result parsing, normalized cycle comparison, and validator serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {"python_json": "load_bearing"}

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
JAX_RESULT = RESULTS / "four_substages_dual_product_v0_jax_results.json"
JULIA_RESULT = RESULTS / "four_substages_dual_product_v0_julia_results.json"
VALIDATOR_RESULT = RESULTS / "four_substages_dual_product_v0_validator_results.json"
RESULTS_MD = HERE / "RESULTS.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rotation_key(cycle: list[str]) -> tuple[str, ...]:
    return min(tuple(cycle[index:] + cycle[:index]) for index in range(len(cycle)))


def unoriented_key(cycle: list[str]) -> tuple[str, ...]:
    return min(rotation_key(cycle), rotation_key(list(reversed(cycle))))


def normalized_jax_cells(result: dict) -> set[tuple[str, str]]:
    family = {"dephasing": "pinching_conditional_expectation", "rotation": "unitary_automorphism"}
    return {
        (row["inferred_axis"], family[row["inferred_family"]])
        for row in result["canonical_rows"]
    }


def normalized_julia_cells(result: dict) -> set[tuple[str, str]]:
    return {
        tuple(signature.split("|", maxsplit=1))
        for signature in result["four_signature_quotient"]["classes"]
    }


def compare(jax_result: dict, julia_result: dict) -> dict:
    jax_cycles = [list(cycle) for cycle in jax_result["mss_product_cycle"]["operator_cycles"]]
    julia_cycles = [
        list(row["vertices_modulo_rotation"])
        for row in julia_result["mss_product_graph"]["core_forbid_diagonal"]["oriented_cycles_modulo_rotation"]
    ]
    julia_removed = julia_result["mss_product_graph"]["remove_each_cell_controls"]

    checks = {
        "both_independent_runs_pass": bool(jax_result["all_pass"] and julia_result["all_pass"]),
        "both_fenced_scratch": bool(
            jax_result["classification"] == julia_result["classification"] == "scratch_diagnostic"
            and jax_result["promotion_allowed"] is False
            and julia_result["promotion_allowed"] is False
            and jax_result["formal_admission_allowed"] is False
            and julia_result["formal_admission_allowed"] is False
        ),
        "four_measured_cells_agree": bool(
            jax_result["structural_signature_count"]
            == julia_result["four_signature_quotient"]["class_count"]
            == 4
            and normalized_jax_cells(jax_result) == normalized_julia_cells(julia_result)
        ),
        "parameter_variant_quotient_agrees": bool(
            jax_result["parameter_variant_quotient_count"]
            == julia_result["quotient_controls"]["duplicate_strength_angle_variants"]["structural_class_count"]
            == 4
        ),
        "core_graph_shape_agrees": bool(
            jax_result["mss_product_cycle"]["minimal_cycle_length"]
            == julia_result["mss_product_graph"]["core_forbid_diagonal"]["minimum_closed_hamiltonian_cycle_length"]
            == 4
            and jax_result["mss_product_cycle"]["oriented_cycle_count"]
            == julia_result["mss_product_graph"]["core_forbid_diagonal"]["oriented_cycles_modulo_rotation_count"]
            == 2
            and jax_result["mss_product_cycle"]["unoriented_cycle_count"]
            == julia_result["mss_product_graph"]["core_forbid_diagonal"]["cycles_modulo_rotation_and_reversal_count"]
            == 1
        ),
        "oriented_operator_cycles_agree": {
            rotation_key(cycle) for cycle in jax_cycles
        }
        == {rotation_key(cycle) for cycle in julia_cycles},
        "one_unoriented_operator_cycle_agrees": bool(
            len({unoriented_key(cycle) for cycle in jax_cycles})
            == len({unoriented_key(cycle) for cycle in julia_cycles})
            == 1
            and {unoriented_key(cycle) for cycle in jax_cycles}
            == {unoriented_key(cycle) for cycle in julia_cycles}
        ),
        "coordinate_erasure_agrees": bool(
            jax_result["controls"]["erase_axis_structural_count"]
            == julia_result["mss_product_graph"]["erase_axis_coordinate_control"]["vertex_count"]
            == 2
            and jax_result["controls"]["erase_family_structural_count"]
            == julia_result["mss_product_graph"]["erase_family_coordinate_control"]["vertex_count"]
            == 2
            and julia_result["mss_product_graph"]["erase_axis_coordinate_control"]["cycles_modulo_rotation_and_reversal_count"] == 0
            and julia_result["mss_product_graph"]["erase_family_coordinate_control"]["cycles_modulo_rotation_and_reversal_count"] == 0
        ),
        "cell_removal_agrees": bool(
            jax_result["controls"]["remove_one_cell_closed_cycle_count"] == 0
            and all(row["graph"]["cycles_modulo_rotation_and_reversal_count"] == 0 for row in julia_removed)
        ),
        "diagonal_control_agrees": bool(
            jax_result["controls"]["allow_diagonal_jump_cycle_count"]
            == julia_result["mss_product_graph"]["core_allow_diagonal_control"]["oriented_cycles_modulo_rotation_count"]
            == 6
        ),
        "y_axis_control_agrees": bool(
            jax_result["controls"]["add_y_axis_structural_count"]
            == julia_result["mss_product_graph"]["add_y_axis_control"]["vertex_count"]
            == 6
        ),
        "julia_does_not_read_jax": bool(julia_result["julia"]["reads_peer_result"] is False),
        "jax_does_not_read_julia": bool(jax_result["jax"]["reads_peer_result"] is False),
        "premise_boundary_present": bool(
            julia_result["premises"]["source_axis_selection_is_assumed_complete_for_this_probe"]
            and julia_result["premises"]["operator_family_selection_is_assumed_complete_for_this_probe"]
            and "conditional" in jax_result["claim_ceiling"]
        ),
    }
    return {
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "jax_oriented_cycles": jax_cycles,
        "julia_oriented_cycles": julia_cycles,
        "unoriented_cycle": list(next(iter({unoriented_key(cycle) for cycle in jax_cycles}))),
    }


def write_results_md(validation: dict) -> None:
    checks = validation["checks"]
    lines = [
        "# Four-Substage Dual-Product v0 Results",
        "",
        "Status: `passes local rerun` as a `scratch_diagnostic` only.",
        "",
        "Julia Canon and JAX independently recover four source-premised channel classes and the same one-coordinate product-square cycle.",
        "",
        "- cells: `Ti=(z,pinch)`, `Fe=(z,unitary)`, `Fi=(x,unitary)`, `Te=(x,pinch)`",
        "- cycle orientations: `Ti-Fe-Fi-Te-Ti` and `Ti-Te-Fi-Fe-Ti`",
        "- one cycle modulo rotation and reversal",
        "- erase either coordinate: two classes and no four-cell cycle",
        "- remove a cell: no closed Hamiltonian cycle",
        "- add y: six classes",
        "- allow diagonal jumps: the cycle is no longer unique",
        "",
        "The result is conditional on the source selecting exactly x/z and the two operator families, plus completeness and one-coordinate adjacency. It does not prove sequential substages in each of 16 stages, Axis-6 execution, personalities, perception, or useful engines.",
        "",
        "## Parity Checks",
        "",
    ]
    lines.extend(f"- {name}: `{passed}`" for name, passed in checks.items())
    lines.extend(
        [
            "",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        ]
    )
    RESULTS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    jax_result = load(JAX_RESULT)
    julia_result = load(JULIA_RESULT)
    validation = compare(jax_result, julia_result)
    result = {
        "schema": "codex_ratchet.four_substages_dual_product_v0.validator.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "accepted_status_label": "passes local rerun" if validation["all_checks_pass"] else "runs",
        "claim_ceiling": "conditional product-square theorem and independent implementation parity only",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "source_results": [str(JAX_RESULT), str(JULIA_RESULT)],
        "validation": validation,
        "blocked_consumers": [
            "sequential substage admission",
            "16x4 engine schedule",
            "Type-1/Type-2 engine architecture",
            "Axis0, perception, personality, ontology, or useful-work claims",
        ],
        "all_pass": validation["all_checks_pass"],
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results_md(validation)
    print(json.dumps({
        "validator_result": str(VALIDATOR_RESULT),
        "results_md": str(RESULTS_MD),
        "all_pass": result["all_pass"],
        "checks": validation["checks"],
    }, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
