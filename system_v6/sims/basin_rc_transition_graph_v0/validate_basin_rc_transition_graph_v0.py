#!/usr/bin/env python3
"""Packet-local validator for basin_rc_transition_graph_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from basin_rc_transition_graph_v0_common import ROOT, SIM_DIR, RESULT_DIR, SIM_ID, rel, sha256_file, write_json


RESULT_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
    "envelope": RESULT_DIR / f"{SIM_ID}_envelope_results.json",
}
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def scan_for_forbidden_word(errors: list[str]) -> None:
    forbidden = "fix" + "ture"
    for path in SIM_DIR.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        if not path.is_file() or path.name in {f"{SIM_ID}_validator_results.json", "audit_verdict.md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if forbidden in text:
            errors.append(f"forbidden wording appears in {rel(path)}")


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


def validate_envelope(errors: list[str], env: dict[str, Any], legs: dict[str, dict[str, Any]]) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "envelope sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "envelope classification mismatch")
    require(errors, env.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, env.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must include all three engines")
    require(errors, env.get("finite_S", {}).get("state_count") == 33, "finite state count must be 33")
    require(errors, env.get("finite_S", {}).get("conditioned_shell_cell_count") == 4, "conditioned shell count must be 4")
    require(errors, env.get("R_C_explicit", {}).get("generator_count") == 6, "generator count must be 6")
    require(errors, len(env.get("transition_graph", {}).get("terminal_classes", [])) == 1, "must have one terminal class")
    for row in env.get("transition_graph", {}).get("terminal_classes", []):
        require(errors, row.get("absent_exit_proof", {}).get("no_exit") is True, "terminal absent-exit proof failed")
        require(errors, row.get("absent_exit_proof", {}).get("outgoing_edge_count") == 0, "terminal outgoing edge exists")
    lyap = env.get("transition_graph", {}).get("monotone_exclusion_observable", {})
    require(errors, lyap.get("edge_violation_count") == 0, "monotone-exclusion edge violations must be zero")
    require(errors, lyap.get("monotone_non_decreasing_on_edges") is True, "monotone-exclusion must pass")
    require(errors, lyap.get("reachable_size_edge_violation_count") == 0, "reachable-set size edge violations must be zero")
    require(errors, lyap.get("reachable_size_non_increasing_on_edges") is True, "reachable-set size must be non-increasing")
    require(errors, "non-decreasing" in lyap.get("direction_convention", ""), "Lyapunov direction convention must be explicit")
    semantics = lyap.get("semantics_checks", {})
    require(
        errors,
        semantics.get("can_reach_terminal_existential_may", {}).get("direction_verified") is True,
        "existential/may Lyapunov sample check failed",
    )
    require(
        errors,
        semantics.get("sure_basin_omega_containment_universal_must", {}).get("direction_verified") is True,
        "universal/must Lyapunov sample check failed",
    )
    basin_map = env.get("basin_partition", {}).get("basin_map", {})
    require(errors, bool(basin_map), "basin map missing")
    for class_id, row in basin_map.items():
        require(errors, row.get("semantic_fork", "").startswith("standard nondeterministic"), f"{class_id} semantic fork missing")
        require(errors, row.get("can_reach_terminal", {}).get("semantics") == "existential/may", f"{class_id} may semantics missing")
        require(errors, row.get("can_reach_terminal", {}).get("size") == 33, f"{class_id} can_reach_terminal size must be 33")
        require(errors, row.get("sure_basin_omega_containment", {}).get("semantics") == "universal/must", f"{class_id} must semantics missing")
        require(errors, row.get("sure_basin_omega_containment", {}).get("cells") == [16], f"{class_id} sure basin must be [16]")
    vocab = env.get("basin_partition", {}).get("basin_contract_vocabulary", {})
    require(errors, "may/existential" in vocab.get("can_reach_terminal", ""), "contract vocabulary must define may basin row")
    require(errors, "must/universal" in vocab.get("sure_basin_omega_containment", ""), "contract vocabulary must define must basin row")
    controls = env.get("negative_controls", {})
    for key in (
        "similarity_only_cluster",
        "shuffled_order",
        "root_off",
        "F01_only",
        "N01_only",
        "quotient_erased",
        "commutative_collapse",
    ):
        require(errors, controls.get(key, {}).get("fired") is True, f"negative control {key} must fire")
    proofs = env.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 proof must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 proof must be unsat")
    require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 proof must be unsat")
    require(errors, proofs.get("z3", {}).get("erased_flip_verdict") == "sat", "z3 erased flip must be sat")
    require(errors, proofs.get("cvc5", {}).get("erased_flip_verdict") == "sat", "cvc5 erased flip must be sat")
    require(errors, proofs.get("julia_z3", {}).get("erased_flip_verdict") == "sat", "julia_z3 erased flip must be sat")
    gates = env.get("build_gates", {})
    for key, value in gates.items():
        require(errors, value is True, f"build gate {key} must be true")
    require(errors, env.get("engine_comparison", {}).get("partition_signature_agreement") is True, "partition signatures disagree")
    hashes = {name: legs[name].get("partition_signature_sha256") for name in ("julia", "jax", "pytorch")}
    require(errors, len(set(hashes.values())) == 1, f"leg partition hashes disagree: {hashes}")
    require(errors, (SIM_DIR / "audit_verdict.md").exists(), "audit_verdict.md read anchor must exist for this hardening round")
    require(errors, len(env.get("build_contract_9_requirements", [])) == 9, "must emit all 9 contract requirements")
    require(
        errors,
        env.get("sub_basin_honesty", {}).get("result") == "single_terminal_class_with_split_may_must_basin_rows",
        "sub-basin honesty row must carry split may/must basin semantics",
    )
    require(
        errors,
        "CAVEAT-COARSE-33" in env.get("sub_basin_honesty", {}).get("carried_caveats", []),
        "CAVEAT-COARSE-33 must stay carried by name",
    )


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
    scan_for_forbidden_word(errors)
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
