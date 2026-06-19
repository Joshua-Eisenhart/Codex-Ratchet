#!/usr/bin/env python3
"""Packet-local validator for spinor_network_surface_v0."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "spinor_network_surface_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
REQUIRED_FILES = [
    "build_card.md",
    f"{SIM_ID}_common.py",
    f"{SIM_ID}_julia.jl",
    f"{SIM_ID}_jax.py",
    f"{SIM_ID}_pytorch.py",
    f"{SIM_ID}_envelope.py",
    f"validate_{SIM_ID}.py",
    "builder_self_assessment.md",
]


sys.path.insert(0, str(ROOT / "scripts"))
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def check_required_files(errors: list[str], phase: str) -> None:
    for rel_path in REQUIRED_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    audit_path = SIM_DIR / "audit_verdict.md"
    if phase == "builder":
        errors.extend(builder_audit_boundary_errors(load_json(ENVELOPE_PATH) if ENVELOPE_PATH.is_file() else {}, audit_path))


def validate_tool_intent(errors: list[str], env: dict[str, Any]) -> None:
    intent = env.get("tool_intent")
    require(errors, isinstance(intent, dict), "tool_intent object is required")
    if not isinstance(intent, dict):
        return
    require(errors, bool(intent.get("claim_classes")), "tool_intent.claim_classes must be non-empty")
    engine_intent = intent.get("engine_tool_intent")
    require(errors, isinstance(engine_intent, dict), "tool_intent.engine_tool_intent must be an object")
    if not isinstance(engine_intent, dict):
        return
    for engine, record in env.get("engines", {}).items():
        lane = engine_intent.get(engine)
        require(errors, isinstance(lane, dict), f"tool_intent missing engine lane: {engine}")
        if not isinstance(lane, dict):
            continue
        for package in record.get("aligned_packages_load_bearing", []):
            require(errors, bool(lane.get(package)), f"tool_intent missing {engine}.{package}")


def validate_envelope(errors: list[str], env: dict[str, Any], phase: str) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, env.get("ceiling") == "scratch_diagnostic", "ceiling must be scratch_diagnostic")
    require(errors, env.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, env.get("all_pass") is True, "all_pass must be true")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must contain exactly julia/jax/pytorch")
    if phase == "builder":
        if "no_builder_audit_verdict" in env:
            require(errors, env.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict gate must be true")
        else:
            env.setdefault("boundary_field", "pre_convention_grandfathered")
        if "no_builder_audit_verdict_envelope_gate" in env:
            require(errors, env.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")

    generic_errors = validate_three_engine(
        env,
        require_pytorch=True,
        strict_source_backed=True,
        require_tool_intent=True,
    )
    errors.extend(f"generic three-engine validator: {err}" for err in generic_errors)
    validate_tool_intent(errors, env)

    carrier = env.get("carrier", {})
    require(errors, carrier.get("kind") == "strict_finite_quantum_hopfield_surface_carrier", "carrier kind mismatch")
    require(errors, carrier.get("site_count") == 4, "carrier site_count must be 4")
    require(errors, carrier.get("dimension") == 16, "carrier dimension must be 16")
    require(errors, len(carrier.get("support_edges", [])) == 5, "support graph must have five edges")
    require(errors, len(carrier.get("support_faces", [])) == 2, "support must have two faces")

    coupling = env.get("coupling", {})
    require(errors, float(coupling.get("hermitian_residual", 1.0)) <= 1.0e-10, "coupling must be Hermitian")
    require(errors, "V(rho)=1-max_mu" in coupling.get("energy_functional", ""), "energy functional must be declared")
    require(errors, "CPTP" in coupling.get("retrieval_dynamics", ""), "retrieval dynamics must name admissible CPTP-class map")

    basin = env.get("basin_contract", {})
    require(errors, bool(basin.get("S")), "basin contract must declare S")
    require(errors, bool(basin.get("Adm_C")), "basin contract must declare Adm_C")
    require(errors, bool(basin.get("M_C")), "basin contract must declare M_C")
    require(errors, bool(basin.get("R_C")), "basin contract must declare R_C")
    require(errors, basin.get("stored_patterns_all_trapping") is True, "stored patterns must earn trapping evidence")
    require(errors, basin.get("absent_exit_all_terminals") is True, "absent-exit evidence missing")
    require(errors, basin.get("escape_all_declared_seeds") is True, "escape evidence missing")
    require(errors, float(basin.get("max_lyapunov_delta", 1.0)) <= 1.0e-10, "Lyapunov monotonicity failed")
    require(errors, bool(basin.get("spurious_attractors_found")), "spurious attractors must be reported")
    require(errors, len(env.get("basin_partition_table", [])) >= 5, "basin partition table too small")

    chart = env.get("chart_recoverability_verdict", {})
    require(errors, chart.get("predicate") == "single_site_density_quotient_to_A33_bloch_chart_recovers_committed_A_chart_row_structure", "A-chart predicate mismatch")
    require(errors, chart.get("verdict") == "partial_recovery_nontrivial", "A-chart verdict must be partial nontrivial recovery")
    require(errors, chart.get("registered_falsifier_fired") is False, "A-chart registered falsifier fired")
    require(errors, int(chart.get("recovered_cell_count", 0)) > 1, "A-chart recovery must be nontrivial")
    require(errors, int(chart.get("expected_cell_count", 0)) == 33, "A-chart expected cell count must be 33")

    typed = env.get("typed_information_rows", {})
    require(errors, typed.get("family_id") == "pattern_conditioned_conditional_vn_S_A_given_B", "typed info family mismatch")
    require(errors, typed.get("bipartition_declared") == {"A": [0], "B": [1, 2, 3]}, "typed info bipartition mismatch")
    require(errors, len(typed.get("rows", [])) == 3, "typed information must contain three trajectory rows")
    for control in typed.get("premature_structure_controls", []):
        require(errors, control.get("pass") is True and control.get("sentinel_number_returned") is False, f"premature structure control failed: {control.get('operation')}")

    lr = env.get("lr_hook", {})
    require(errors, lr.get("distinguishable_under_probe") is True, "L/R hook must distinguish under declared probe")
    require(errors, "no engine or 64-claim" in lr.get("a_equals_a_iff_a_tilde_b_boundary", ""), "L/R hook must fence broader claims")

    controls = env.get("controls", {})
    guard = controls.get("guard_negative_controls", {})
    for key in ("similarity_only_clustering", "root_off", "shuffled_order", "quotient_erased", "F01_only", "N01_only", "commutative_collapse"):
        row = guard.get(key, {})
        require(errors, row.get("pass") is True, f"guard negative control {key} must pass as failed-required control")
        require(errors, row.get("verdict") == "failed_as_required", f"guard negative control {key} verdict mismatch")
    npc2 = controls.get("npc2_copied_controls", {})
    for key in ("pure_gauge", "random_patterns", "erased"):
        require(errors, npc2.get(key, {}).get("pass") is True, f"npc2 copied control {key} must pass")
    require(errors, controls.get("non_hermitian_coupling_control", {}).get("lyapunov_row_breaks") is True, "non-Hermitian control must break Lyapunov row")
    require(errors, controls.get("pattern_overload_boundary", {}).get("retrieval_degrades") is True, "pattern overload boundary must be computed")

    tool_manifest = env.get("TOOL_MANIFEST", {})
    tool_depth = env.get("TOOL_INTEGRATION_DEPTH", {})
    for tool in ("QuantumOptics", "Graphs", "Z3", "qutip", "networkx", "sympy", "z3", "cvc5", "torch_geometric", "torch.func"):
        require(errors, tool_manifest.get(tool, {}).get("used") is True, f"TOOL_MANIFEST missing used tool {tool}")
        require(errors, tool_depth.get(tool) == "load_bearing", f"TOOL_INTEGRATION_DEPTH for {tool} must be load_bearing")

    require(errors, bool(env.get("positive")), "positive section required")
    require(errors, bool(env.get("negative")), "negative section required")
    require(errors, bool(env.get("boundary")), "boundary section required")
    require(errors, bool(env.get("validator_expected_commands")), "validator command ledger required")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["builder", "post_audit"], default="builder")
    args = parser.parse_args()

    errors: list[str] = []
    check_required_files(errors, args.phase)
    if ENVELOPE_PATH.is_file():
        validate_envelope(errors, load_json(ENVELOPE_PATH), args.phase)
    else:
        errors.append(f"missing envelope result: {ENVELOPE_PATH.relative_to(ROOT)}")
    payload = {
        "ok": not errors,
        "phase": args.phase,
        "errors": errors,
        "validated_path": str(ENVELOPE_PATH.relative_to(ROOT)),
    }
    VALIDATOR_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
