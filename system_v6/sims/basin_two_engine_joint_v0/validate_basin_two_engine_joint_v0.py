#!/usr/bin/env python3
"""Packet-local validator for basin_two_engine_joint_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from basin_two_engine_joint_v0_common import ROOT, SIM_DIR, RESULT_DIR, SIM_ID, rel, sha256_file, write_json


RESULT_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
    "envelope": RESULT_DIR / f"{SIM_ID}_envelope_results.json",
}
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def scan_forbidden_words(errors: list[str]) -> None:
    forbidden = ["fix" + "ture", "to" + "y", "mo" + "ck", "dum" + "my"]
    for path in SIM_DIR.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        if not path.is_file() or path.name == f"{SIM_ID}_validator_results.json":
            continue
        if path.name == "audit_verdict.md":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for word in forbidden:
            if word in text:
                errors.append(f"forbidden wording {word!r} appears in {rel(path)}")


def validate_leg(errors: list[str], name: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{name} sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{name} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{name} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
    require(errors, payload.get("all_pass") is True, f"{name} all_pass must be true")
    require(errors, bool(payload.get("packages_used")), f"{name} packages_used missing")
    require(errors, bool(payload.get("aligned_packages_load_bearing")), f"{name} aligned load-bearing packages missing")
    require(errors, payload.get("one_to_one_tool_calls", {}).get("pass") is True, f"{name} one-to-one tool calls failed")
    source = ROOT / payload.get("source_path", "")
    require(errors, source.exists(), f"{name} source path missing")
    if source.exists():
        require(errors, payload.get("source_sha256") == sha256_file(source), f"{name} source sha drift")


def validate_hierarchy(errors: list[str], env: dict[str, Any]) -> None:
    hierarchy = env.get("hierarchy", {})
    basins = hierarchy.get("basins", {})
    subbasins = hierarchy.get("subbasins", {})
    subsub = hierarchy.get("subsubbasins", {})
    require(errors, env.get("joint_object", {}).get("state_count") == 64, "joint object state count must be 64")
    require(errors, env.get("joint_object", {}).get("stage_configuration_shape") == [8, 8], "joint object shape must be 8x8")
    require(errors, basins.get("both", {}).get("terminal_class_count") == 1, "basin terminal count must be 1")
    require(errors, subbasins.get("synchronous", {}).get("terminal_class_count") == 8, "synchronous subbasin terminal count must be 8")
    require(errors, subbasins.get("l_only", {}).get("terminal_class_count") == 8, "L-only subbasin terminal count must be 8")
    require(errors, subbasins.get("r_only", {}).get("terminal_class_count") == 8, "R-only subbasin terminal count must be 8")
    require(errors, subsub.get("earned_count") == 64, "subsubbasin count must be 64")
    require(errors, subsub.get("class_size_multiset") == [1] * 64, "subsubbasin classes must be singleton")
    for row in hierarchy.get("level_rows", []):
        require(errors, bool(row.get("terminal_classes")), f"{row.get('level')} terminal rows missing")
        require(errors, bool(row.get("morse_ordering", {}).get("nodes")), f"{row.get('level')} Morse nodes missing")
        require(errors, bool(row.get("may_must_partition", {}).get("rows")), f"{row.get('level')} may/must rows missing")
        for terminal in row.get("terminal_classes", []):
            require(errors, terminal.get("absent_exit_proof", {}).get("no_exit") is True, "terminal absent-exit proof failed")


def validate_controls(errors: list[str], env: dict[str, Any]) -> None:
    discipline = env.get("signature_discipline", {})
    require(errors, discipline.get("order_blind") is True, "signature must be order-blind")
    require(errors, discipline.get("label_free") is True, "signature must be label-free")
    require(errors, discipline.get("forbidden_components_present") == [], "forbidden signature components present")
    controls = env.get("controls", {})
    require(errors, controls.get("label_permutation", {}).get("count_invariant") is True, "label permutation count changed")
    require(errors, controls.get("decode_test", {}).get("passed") is True, "decode test failed")
    require(errors, controls.get("decode_test", {}).get("stage_label_recovered") is False, "decode recovered stage labels")
    require(errors, controls.get("decode_test", {}).get("stage_order_recovered") is False, "decode recovered stage order")
    require(errors, controls.get("similarity_cluster_contrast", {}).get("fired") is True, "similarity contrast did not fire")
    require(errors, controls.get("root_off", {}).get("fired") is True, "root-off control did not fire")
    marginals = controls.get("single_engine_marginals", {})
    require(errors, marginals.get("l_terminal_count") == 8, "L marginal terminal count must be 8")
    require(errors, marginals.get("r_terminal_count") == 8, "R marginal terminal count must be 8")
    lr_rows = env.get("lr_structure_rows", {})
    require(errors, lr_rows.get("chirality_asymmetry", {}).get("mirror_law_scope") == "family_local_no_universal_mirror_assumed", "mirror law scope mismatch")
    require(errors, lr_rows.get("noncommutation", {}).get("trace_order_moves") is True, "noncommutation trace row missing")


def validate_envelope(errors: list[str], env: dict[str, Any], legs: dict[str, dict[str, Any]]) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "envelope sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "envelope classification mismatch")
    require(errors, env.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, env.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must include all three engines")
    validate_hierarchy(errors, env)
    validate_controls(errors, env)
    adjudication = env.get("prediction_adjudication", {})
    require(errors, adjudication.get("pre_registered_count") == 64, "pre-registered count mismatch")
    require(errors, adjudication.get("computed_subsubbasin_count") == 64, "computed count mismatch")
    require(errors, adjudication.get("realized_factorization") == "8x8_joint_stage_configuration", "wrong realized factorization")
    require(errors, adjudication.get("candidate_factorizations", {}).get("8x8_joint_stage_configuration", {}).get("status") == "realized", "8x8 candidate not realized")
    require(errors, adjudication.get("candidate_factorizations", {}).get("64_matrix", {}).get("status") == "cardinality_compatible_not_structure_identified", "64-matrix status mismatch")
    require(errors, adjudication.get("candidate_factorizations", {}).get("16x4", {}).get("status") == "not_realized_by_primary_partition", "16x4 status mismatch")
    proofs = env.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 proof must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 proof must be unsat")
    require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 proof must be unsat")
    require(errors, proofs.get("z3", {}).get("erased_flip_verdict") == "sat", "z3 erased flip must be sat")
    require(errors, proofs.get("cvc5", {}).get("erased_flip_verdict") == "sat", "cvc5 erased flip must be sat")
    require(errors, proofs.get("julia_z3", {}).get("erased_flip_verdict") == "sat", "julia_z3 erased flip must be sat")
    comparison = env.get("engine_comparison", {})
    require(errors, comparison.get("subsubbasin_count_agreement") is True, "engine subsubbasin counts disagree")
    require(errors, comparison.get("terminal_count_agreement") is True, "engine terminal counts disagree")
    require(errors, env.get("divergence", {}).get("max_divergence") == 0.0, "engine divergence must be zero")
    errors.extend(builder_audit_boundary_errors(env, SIM_DIR / "audit_verdict.md"))
    gates = env.get("build_gates", {})
    for key, value in gates.items():
        require(errors, value is True, f"build gate {key} must be true")
    for name in ("julia", "jax", "pytorch"):
        require(errors, legs.get(name, {}).get("all_pass") is True, f"{name} leg did not pass")


def main() -> int:
    errors: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for name, path in RESULT_PATHS.items():
        if not path.exists():
            errors.append(f"missing result {rel(path)}")
            continue
        payloads[name] = load(path)
    for name in ("julia", "jax", "pytorch"):
        if name in payloads:
            validate_leg(errors, name, payloads[name])
    if "envelope" in payloads and all(name in payloads for name in ("julia", "jax", "pytorch")):
        validate_envelope(errors, payloads["envelope"], payloads)
    scan_forbidden_words(errors)
    result = {
        "ok": not errors,
        "errors": errors,
        "result_json": rel(RESULT_PATHS["envelope"]),
        "validator": rel(Path(__file__).resolve()),
    }
    write_json(VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
