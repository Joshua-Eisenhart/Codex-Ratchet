#!/usr/bin/env python3
"""Packet-local validator for spinor_network_surface_v2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "spinor_network_surface_v2"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

RESULT_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
    "envelope": ENVELOPE_PATH,
}

REQUIRED_PACKET_FILES = [
    "build_card.md",
    f"{SIM_ID}_julia.jl",
    f"{SIM_ID}_jax.py",
    f"{SIM_ID}_pytorch.py",
    f"{SIM_ID}_envelope.py",
    f"validate_{SIM_ID}.py",
]

V0_CAVEATS = {
    "A_CHART_BY_CONSTRUCTION",
    "FALSIFIER_STRING_MISMATCH",
    "STALE_CONSUMED_PATHS",
    "DECLARATIVE_CPTP",
    "BOOLEAN_EXIT_EVIDENCE",
    "NONHERMITIAN_WRONG_ROW",
    "SHARED_COMMON_MODULE",
    "JULIA_SCALAR_STUB",
    "PYTORCH_SUPPORTIVE_NOT_LOAD_BEARING",
    "POST_AUDIT_BOUNDARY",
}

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_packet_files(errors: list[str], phase: str) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    if phase == "builder":
        build_card = SIM_DIR / "build_card.md"
        require(errors, build_card.is_file() and "spinor_network_surface_v2" in build_card.read_text(encoding="utf-8"), "build_card.md was not copied for v2")


def validate_leg(errors: list[str], name: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{name} sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{name} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{name} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
    require(errors, payload.get("all_pass") is True, f"{name} all_pass must be true")
    require(errors, bool(payload.get("packages_used")), f"{name} packages_used missing")
    require(errors, bool(payload.get("aligned_packages_load_bearing")), f"{name} load-bearing package list missing")
    values = payload.get("engine_values", {})
    require(errors, values.get("recovered_nonorigin_cell_count") == 16, f"{name} recovered count must be 16")
    require(errors, values.get("load_bearing_recovered_nonorigin_cell_count") == 11, f"{name} load-bearing recovered count must be 11")
    require(errors, values.get("control_fail_count") == 4, f"{name} control fail count must be 4")
    require(errors, values.get("terminal_scc_count") == 14, f"{name} terminal SCC count must be 14")
    require(errors, values.get("spurious_attractor_count") == 6, f"{name} spurious count must be 6")
    require(errors, values.get("typed_entangled_negative_count") == 6, f"{name} typed negative count must be 6")
    require(errors, values.get("haar_null_expected_nonorigin_cell_count_scaled") == 7607, f"{name} Haar null expected count drift")
    require(errors, values.get("identity_surprisal_scaled", 0) > values.get("null_surprisal_mean_scaled", 10**9), f"{name} identity statistic must exceed null mean")
    require(errors, values.get("a33_reachable_in_principle_count") == 33, f"{name} A33 reachability ceiling must be 33")
    require(errors, values.get("kraus_choi_witness_count") == 10, f"{name} Kraus/Choi witness count must be 10")
    require(errors, values.get("v1_anchor_recovered_nonorigin_cell_count") == 6, f"{name} v1 anchor recovery must remain 6")
    source = ROOT / str(payload.get("source_path", ""))
    require(errors, source.exists(), f"{name} source path missing")


def validate_controls(errors: list[str], controls: dict[str, Any]) -> None:
    required = {
        "maximally_mixed_state": 0,
        "quotient_erased_state": 0,
        "off_axis_rotated_states": 13,
        "wrong_row_classifier": 17,
    }
    require(errors, set(controls) == set(required), "no-structure controls mismatch")
    for name, expected_nonorigin in required.items():
        row = controls.get(name, {})
        require(errors, row.get("verdict") == "RECOVERY_FAIL", f"{name} must fail recovery")
        require(errors, row.get("control_fired") is True, f"{name} failure branch did not fire")
        require(errors, row.get("registered_falsifier_fired") is True, f"{name} registered falsifier not recorded")
        require(errors, row.get("recovered_nonorigin_cell_count") == expected_nonorigin, f"{name} nonorigin count drift")
        require(errors, row.get("classifier_id") == "A33_committed_predeclared", f"{name} must use the real classifier")
    require(errors, controls.get("off_axis_rotated_states", {}).get("identity_pairs_match_expected") is False, "off-axis control must fail identity predicate")
    require(errors, controls.get("wrong_row_classifier", {}).get("identity_pairs_match_expected") is False, "wrong-row control must fail identity predicate")
    require(
        errors,
        "permuted row-label ledger" in controls.get("wrong_row_classifier", {}).get("control_design", ""),
        "wrong-row control design must be structure-sensitive",
    )


def v1_anchor_ids(anchor: dict[str, Any]) -> set[str]:
    actual = anchor.get("actual", anchor)
    return set(
        actual.get(
            "recovered_nonorigin_cell_ids",
            actual.get("actual_recovered_nonorigin_cell_ids", []),
        )
    )


def validate_envelope(errors: list[str], env: dict[str, Any], phase: str) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, env.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, env.get("all_pass") is True, "all_pass must be true")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "all three engines required")
    if phase == "builder":
        errors.extend(builder_audit_boundary_errors(env, SIM_DIR / "audit_verdict.md"))
        require(errors, env.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
        require(errors, env.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")
        require(errors, env.get("builder_gates", {}).get("no_builder_audit_verdict") is True, "builder gate false")

    generic_errors = validate_three_engine(
        env,
        require_pytorch=True,
        strict_source_backed=True,
        require_tool_intent=True,
    )
    errors.extend(f"generic three-engine validator: {err}" for err in generic_errors)

    verdict = env.get("recoverability_VERDICT", {})
    require(errors, verdict.get("verdict") == "RECOVERY_PASS_FAMILY_TIED_IDENTITY_ABOVE_HAAR_NULL", "recoverability verdict mismatch")
    require(errors, verdict.get("recovered_nonorigin_cell_count") == 16, "recoverability nonorigin count must be 16")
    require(errors, verdict.get("load_bearing_recovered_nonorigin_cell_count") == 11, "load-bearing recovery count must be 11")
    require(errors, verdict.get("expected_cell_count") == 33, "A33 expected count must be 33")
    require(errors, 7.0 <= float(verdict.get("haar_null_expected_nonorigin_cell_count", 0.0)) <= 8.3, "Haar null expected count out of range")
    require(errors, float(verdict.get("identity_surprisal_z", 0.0)) > 0.0, "identity statistic must beat null")
    require(errors, verdict.get("registered_falsifier_fired") is False, "positive row falsifier should not fire")

    positive = env.get("positive_section", {})
    require(errors, positive.get("classifier", "").startswith("A33 committed"), "classifier predeclaration missing")
    pattern_families = set(positive.get("pattern_families", []))
    require(
        errors,
        {
            "estate_chiral_quaternion_Hopf_Weyl",
            "entangled_nonproduct",
            "pinned_random_v1_anchor",
            "haar_pinned_seed_6608",
            "haar_pinned_seed_6609",
            "haar_pinned_seed_6610",
            "haar_pinned_seed_6611",
        }
        <= pattern_families,
        "required independent pattern families missing",
    )
    require(errors, "rho'=(1-alpha)" in positive.get("retrieval_channel", ""), "computed retrieval relation missing")

    haar_null = env.get("haar_null_row", {})
    require(errors, haar_null.get("kind") == "haar_null_identity_control", "Haar null row missing")
    require(errors, haar_null.get("trials") == 2048, "Haar null trial count drift")
    require(errors, 7.0 <= float(haar_null.get("expected_nonorigin_cell_count", 0.0)) <= 8.3, "Haar null expected count out of range")
    require(errors, haar_null.get("observed_load_bearing_nonorigin_cell_count") == 11, "Haar observed load-bearing count drift")
    require(errors, haar_null.get("observed_family_tied_pair_count") == 16, "Haar observed family-pair count drift")
    require(errors, haar_null.get("verdict") == "IDENTITY_ABOVE_NULL", "Haar null verdict mismatch")
    require(errors, float(haar_null.get("identity_surprisal_z", 0.0)) > 0.0, "Haar identity z must be positive")

    family_rows = env.get("per_family_recovery_table", [])
    load_bearing_rows = [row for row in family_rows if row.get("load_bearing_for_identity_claim") is True]
    require(errors, len(load_bearing_rows) == 4, "must have four load-bearing unbiased Haar families")
    require(
        errors,
        all(row.get("bias_class") == "haar_sampled_then_seed_pinned_no_preferred_chart_axis" for row in load_bearing_rows),
        "load-bearing rows must be no-preferred-axis Haar-pinned families",
    )
    require(errors, all(row.get("seed_hash") for row in load_bearing_rows), "load-bearing Haar rows must persist seed hashes")
    require(errors, all(row.get("recovered_nonorigin_cell_count") == 4 for row in load_bearing_rows), "per-family recovery counts drift")

    a33 = env.get("A33_reachability_ceiling", {})
    require(errors, a33.get("geometric_ceiling_cell_count") == 33, "A33 geometric ceiling must be 33")
    require(errors, a33.get("recovered_reachable_cell_count") == 16, "A33 recovered reachable count must be 16")
    require(errors, len(a33.get("reachable_not_recovered_cell_ids", [])) == 17, "A33 unrecovered ceiling remainder must be 17")

    kraus = env.get("kraus_choi_witness_ledger", {})
    require(errors, kraus.get("witness_count") == 10, "Kraus/Choi witness count must be 10")
    require(errors, kraus.get("all_completeness_pass") is True, "Kraus completeness ledger failed")
    require(errors, kraus.get("all_choi_positivity_pass") is True, "Choi positivity ledger failed")
    require(errors, kraus.get("all_trace_preserving_pass") is True, "Choi trace-preserving ledger failed")
    require(errors, len(kraus.get("rows", [])) == 10, "Kraus/Choi witness rows missing")

    expected_v1 = {
        "A33_x00_y00_zp10",
        "A33_x00_yp5_z00",
        "A33_xp10_y00_z00",
        "A33_xp5_y00_z00",
        "A33_xp5_y00_zm5",
        "A33_xp5_y00_zp5",
    }
    require(errors, v1_anchor_ids(env.get("v1_anchor_reproduction", {})) == expected_v1, "v1 anchor recovered cells drift")

    controls = env.get("negative_section", {}).get("no_structure_controls", {})
    validate_controls(errors, controls)
    require(errors, env.get("negative_section", {}).get("falsifier_reachability", {}).get("control_fail_count") == 4, "falsifier reachability count mismatch")

    basin = env.get("basin_partition", {})
    require(errors, basin.get("node_count") == 48, "transition graph node count drift")
    require(errors, basin.get("edge_count") == 48, "transition graph edge count drift")
    require(errors, basin.get("terminal_scc_count") == 14, "terminal SCC count drift")
    require(errors, basin.get("stored_patterns_all_trapping") is True, "stored trapping evidence missing")
    require(errors, basin.get("absent_exit_ok") is True, "absent-exit graph evidence missing")
    require(errors, float(basin.get("max_lyapunov_delta", 1.0)) <= 1.0e-10, "positive Lyapunov row not monotone")
    coverage = basin.get("coverage", {})
    require(errors, coverage.get("pair_mixture_enumerated") == coverage.get("pair_mixture_denominator") == 6, "spurious pair coverage denominator mismatch")
    require(errors, basin.get("spurious_attractor_count") == 6, "spurious attractor count drift")
    require(errors, len(env.get("spurious_attractor_table", [])) == 6, "spurious table must contain six rows")

    escape = env.get("escape_graph_evidence", {})
    require(errors, escape.get("stored_patterns_all_trapping") is True, "escape graph trapping flag missing")
    require(errors, escape.get("absent_exit_ok") is True, "escape graph absent-exit flag missing")
    require(errors, escape.get("trajectory_count") == coverage.get("seed_state_count") == 14, "trajectory coverage mismatch")

    nonhermitian = env.get("nonhermitian_control", {})
    require(errors, nonhermitian.get("control_fired") is True, "non-Hermitian control did not fire")
    require(errors, nonhermitian.get("same_row_as_positive_claim") == "V(rho)=1-max terminal fidelity", "non-Hermitian control used wrong row")
    require(errors, float(nonhermitian.get("lyapunov_delta", 0.0)) > 0.0, "non-Hermitian control must break monotonicity")

    typed = env.get("typed_information", {})
    require(errors, typed.get("bipartition") == {"A": [0], "B": [1, 2, 3]}, "typed bipartition mismatch")
    negatives = typed.get("entangled_negative_conditional_rows", [])
    require(errors, len(negatives) >= 1, "typed rows must show non-product negative conditional entropy")
    require(errors, env.get("premature_typed_row_control", {}).get("raised") is True, "premature typed control must raise")

    source_quotes = env.get("source_line_quotes", [])
    require(errors, len(source_quotes) == 4, "source quote ledger must contain four repaired-estate slices")
    for row in source_quotes:
        require(errors, (ROOT / row.get("path", "")).is_file(), f"quoted source path missing: {row.get('path')}")
        require(errors, bool(row.get("quote", "").strip()), f"quoted source slice empty: {row.get('path')}")

    caveats = env.get("v0_caveat_response", {})
    require(errors, set(caveats) == V0_CAVEATS, "v0 caveat response set mismatch")
    requirements = env.get("surface_v2_requirements", {})
    for key, value in requirements.items():
        require(errors, value is True, f"surface v2 requirement not satisfied: {key}")

    require(errors, bool(env.get("TOOL_INTENT_MATRIX")), "TOOL_INTENT_MATRIX missing")
    tool_intent = env.get("tool_intent", {})
    require(errors, bool(tool_intent.get("claim_classes")), "tool_intent claim classes missing")
    for engine, record in env.get("engines", {}).items():
        engine_intent = tool_intent.get("engine_tool_intent", {}).get(engine, {})
        for package in record.get("aligned_packages_load_bearing", []):
            require(errors, bool(engine_intent.get(package)), f"tool_intent missing {engine}.{package}")

    tool_manifest = env.get("TOOL_MANIFEST", {})
    tool_depth = env.get("TOOL_INTEGRATION_DEPTH", {})
    for tool in (
        "build_three_engine_envelope",
        "Graphs",
        "Z3",
        "LinearAlgebra",
        "Statistics",
        "jax",
        "networkx",
        "sympy",
        "z3",
        "cvc5",
        "torch",
        "torch_geometric",
        "torch.func",
    ):
        require(errors, tool_manifest.get(tool, {}).get("used") is True, f"TOOL_MANIFEST missing {tool}")
        require(errors, tool_depth.get(tool) == "load_bearing", f"TOOL_INTEGRATION_DEPTH must mark {tool} load_bearing")

    require(errors, bool(env.get("positive_section")), "positive section required")
    require(errors, bool(env.get("negative_section")), "negative section required")
    require(errors, bool(env.get("boundary_section")), "boundary section required")
    require(errors, bool(env.get("validator_expected_commands")), "validator command ledger missing")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["builder", "post_audit"], default="builder")
    args = parser.parse_args()

    errors: list[str] = []
    validate_packet_files(errors, args.phase)

    payloads: dict[str, dict[str, Any]] = {}
    for name, path in RESULT_PATHS.items():
        if not path.is_file():
            errors.append(f"missing result: {path.relative_to(ROOT)}")
            continue
        payloads[name] = load(path)

    for engine in ("julia", "jax", "pytorch"):
        if engine in payloads:
            validate_leg(errors, engine, payloads[engine])
    if "envelope" in payloads:
        validate_envelope(errors, payloads["envelope"], args.phase)

    result = {
        "ok": not errors,
        "phase": args.phase,
        "errors": errors,
        "validated_path": str(ENVELOPE_PATH.relative_to(ROOT)),
    }
    write_json(VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
