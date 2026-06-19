#!/usr/bin/env python3
"""Packet-local validator for ring_checkerboard_automaton_v0."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from ring_checkerboard_automaton_v0_common import PACKET, RESULT_DIR, ROOT, SIM_ID, rel, sha256_file, write_json


RESULT_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
    "envelope": RESULT_DIR / f"{SIM_ID}_envelope_results.json",
}
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
BOUNDARY_KEYS = {
    "no_builder_audit_verdict",
    "no_builder_audit_verdict_envelope_gate",
    "no_audit_verdict",
    "no_audit_verdict_written",
    "no_audit_verdict_emitted",
    "packet_audit_verdict_absent",
    "file_disjoint_packet",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def find_boundary_flags(value: Any) -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in BOUNDARY_KEYS:
                found.append((key, item))
            found.extend(find_boundary_flags(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(find_boundary_flags(item))
    return found


def audit_verdict_header_is_independent(audit_path: Path) -> bool:
    if not audit_path.exists():
        return True
    header = "\n".join(audit_path.read_text(encoding="utf-8").splitlines()[:40]).lower()
    return (
        "auditor: independent" in header
        or "independent auditor" in header
        or "independent recomputation" in header
        or "fresh audit" in header
        or "read-only audit" in header
        or "audit mode: read-only" in header
        or ("fresh" in header and "audit" in header)
    )


def validate_builder_audit_boundary(errors: list[str], envelope: dict[str, Any], audit_path: Path) -> None:
    flags = find_boundary_flags(envelope)
    no_builder_flags = [value for key, value in flags if key == "no_builder_audit_verdict"]
    require(errors, bool(no_builder_flags), "no_builder_audit_verdict field missing")
    require(errors, any(value is True for value in no_builder_flags), "no_builder_audit_verdict must be true")
    require(
        errors,
        not audit_path.exists() or audit_verdict_header_is_independent(audit_path),
        "audit_verdict.md exists but its header does not declare an independent/fresh audit",
    )


def validate_leg(errors: list[str], name: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{name} sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{name} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{name} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
    require(errors, payload.get("all_pass") is True, f"{name} all_pass must be true")
    require(errors, bool(payload.get("packages_used")), f"{name} packages_used missing")
    require(errors, bool(payload.get("aligned_packages_load_bearing")), f"{name} load-bearing packages missing")
    require(errors, payload.get("one_to_one_tool_calls", {}).get("pass") is True, f"{name} one-to-one tool calls failed")
    source = ROOT / payload.get("source_path", "")
    require(errors, source.exists(), f"{name} source path missing")
    if source.exists():
        require(errors, payload.get("source_sha256") == sha256_file(source), f"{name} source sha drift")


def validate_envelope(errors: list[str], env: dict[str, Any], phase: str) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "envelope sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "classification mismatch")
    require(errors, env.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, env.get("all_pass") is True, "all_pass must be true")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "all three engine lanes required")
    validate_builder_audit_boundary(errors, env, PACKET / "audit_verdict.md")
    if phase == "builder":
        require(errors, env.get("builder_gates", {}).get("no_builder_audit_verdict") is True, "builder no-audit gate false")
    phase_test = env.get("phase_test", {})
    require(errors, phase_test.get("verdict") == "PASS_DISTINGUISHABLE_CLASSICAL_FLOOR", "phase-test verdict failed")
    require(errors, phase_test.get("alternating_order", {}).get("preserved") is True, "alternating order not preserved")
    require(errors, phase_test.get("paired_order", {}).get("preserved") is True, "paired order not preserved")
    require(errors, phase_test.get("terminal_structure_distinguishable") is True, "phase terminal structure not distinguished")
    require(errors, phase_test.get("orbit_structure_distinguishable") is True, "phase orbit structure not distinguished")
    require(errors, phase_test.get("order_shuffle_changes_dynamics") is True, "order shuffle did not change dynamics")

    object_row = env.get("object", {})
    require(errors, object_row.get("qca_index") == "v1_or_later_not_here", "QCA/index fence missing")
    require(errors, object_row.get("flat_mode") is True, "flat mode missing")
    require(errors, "later" in str(object_row.get("spinning_mode")), "spinning mode must be later variant")

    finite_s = env.get("finite_S", {})
    require(errors, finite_s.get("state_family", "").startswith("single active"), "state family not bounded single-token probe")
    require(errors, "full_binary_configuration_enumerated" in env.get("boundary_section", {}), "boundary full-binary row missing")
    require(errors, env["boundary_section"]["full_binary_configuration_enumerated"] is False, "full binary enumeration must be false")

    rows = env.get("microstate_count_rows", [])
    require(errors, [row.get("steps_per_ring") for row in rows] == [4, 8, 16], "microstate count rows must be for 4,8,16")
    for row in rows:
        n = int(row["steps_per_ring"])
        require(errors, row["support_cell_count"] == n * (n + 1), f"support count mismatch for n={n}")
        require(errors, row["single_active_readout_probe_microstates"] == 16 * n * (n + 1), f"probe count mismatch for n={n}")
        require(errors, row["full_binary_configuration_enumerated"] is False, f"binary enumeration flag wrong for n={n}")
        require(errors, row["alternating_terminal_count"] > 0, f"alternating terminal count empty for n={n}")
        require(errors, row["paired_terminal_count"] > 0, f"paired terminal count empty for n={n}")

    basin = env.get("basin_partition_tables", {})
    for name in ("alternating", "paired", "intrinsic"):
        row = basin.get(name, {})
        require(errors, bool(row.get("terminal_classes")), f"{name} terminal classes missing")
        for terminal in row.get("terminal_classes", []):
            require(errors, terminal.get("absent_exit_proof", {}).get("no_exit") is True, f"{name} terminal exit proof failed")
        require(errors, bool(row.get("basin_map")), f"{name} basin map missing")
        mono = row.get("monotone_exclusion_observable", {})
        require(errors, "exists_for_pinned_rules" in mono, f"{name} monotone observable declaration missing")

    controls = env.get("controls", {})
    required_firing = [
        "similarity_only_cluster",
        "non_partitioned_scramble",
        "order_shuffle",
        "ring_off",
        "checkerboard_off",
        "nesting_off",
        "frozen_phase",
    ]
    for key in required_firing:
        require(errors, controls.get(key, {}).get("fired") is True, f"control {key} must fire")
    require(errors, controls.get("label_permutation", {}).get("counts_invariant") is True, "label permutation must preserve counts")

    nesting = env.get("nesting_comparison", {})
    require(errors, nesting.get("terminal_structure_changed") is True, "nesting comparison did not change terminal structure")
    require(errors, "one attached-ring level" in nesting.get("claim_ceiling", ""), "nesting ceiling missing")

    proofs = env.get("crossover_proofs", {})
    for solver_name in ("z3", "cvc5"):
        proof = proofs.get(solver_name, {})
        require(errors, proof.get("verdict") == "unsat", f"{solver_name} verdict must be unsat")
        require(errors, proof.get("computed_perturbation_flip_verdict") == "sat", f"{solver_name} perturbation flip must be sat")
        require(errors, proof.get("load_bearing") is True, f"{solver_name} must be load-bearing")
    require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 must be unsat")

    require(errors, env.get("engine_comparison", {}).get("primary_state_count_agreement") is True, "engine state counts disagree")
    require(errors, env.get("engine_comparison", {}).get("primary_intrinsic_terminal_count_agreement") is True, "engine terminal counts disagree")
    for key, value in env.get("build_gates", {}).items():
        require(errors, value is True, f"build gate {key} must be true")
    require(errors, "TOOL_INTENT_MATRIX" in env, "TOOL_INTENT_MATRIX missing")
    require(errors, "tool_intent" in env, "tool_intent missing")


def run_nested_validator(errors: list[str], result_path: Path) -> None:
    nested = subprocess.run(
        [
            SIM_PY,
            "scripts/validate_three_engine_sim_result.py",
            "--require-pytorch",
            "--strict-source-backed",
            "--require-tool-intent",
            str(result_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    require(errors, nested.returncode == 0, f"nested strict validator failed: {nested.stdout} {nested.stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["builder", "post_audit"], default="builder")
    args = parser.parse_args()
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
    if "envelope" in payloads:
        validate_envelope(errors, payloads["envelope"], args.phase)
    if not errors and "envelope" in payloads:
        run_nested_validator(errors, RESULT_PATHS["envelope"])
    result = {
        "ok": not errors,
        "errors": errors,
        "phase": args.phase,
        "result_json": rel(RESULT_PATHS["envelope"]),
        "validator": rel(Path(__file__).resolve()),
    }
    write_json(VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
