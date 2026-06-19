#!/usr/bin/env python3
"""Packet-local validator for terrain_spinor_flux_nest_n3_v0."""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "terrain_spinor_flux_nest_n3_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
    "envelope": RESULT_DIR / f"{SIM_ID}_envelope_results.json",
}
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
SOURCE_PATH = SIM_DIR / f"validate_{SIM_ID}.py"
REQUIRED_PARENT_IDS = {
    "stage_lifted_spinor_shell_n3_v0",
    "terrain_spinor_shell_nest_v0",
    "geo_s5_terrain_flows_v0",
    "ratchet_s2_two_shell_flux_v0",
    "geo_disintegration_machinery_v0",
    "geo_union_rule_k_leaves_v0",
    "terrain_exact_mirror_finder_v0",
}
TOL = 1.0e-8


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def scan_for_forbidden_word(errors: list[str]) -> None:
    forbidden = "fix" + "ture"
    for path in SIM_DIR.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        if not path.is_file() or path.name == f"{SIM_ID}_validator_results.json":
            continue
        if path.name == "audit_verdict.md":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if forbidden in text:
            errors.append(f"forbidden wording {forbidden!r} appears in {path.relative_to(ROOT)}")


def validate_envelope(errors: list[str], env: dict[str, Any], phase: str) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "envelope schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "envelope sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, env.get("ceiling") == "scratch_diagnostic", "ceiling must be scratch_diagnostic")
    require(errors, env.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, env.get("mode") == "RATCHETED", "top-level mode must be RATCHETED")
    require(errors, env.get("standard_schema_mode") == "FIELD", "standard_schema_mode must be FIELD")
    require(errors, env.get("engine_contract", {}).get("mode") == "RATCHETED", "engine_contract.mode must be RATCHETED")
    require(errors, env.get("engine_contract", {}).get("mode_is_field") is True, "engine_contract mode must be marked as FIELD")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must contain julia/jax/pytorch")
    require(errors, env.get("all_pass") is True, "all_pass must be true")

    parent_rows = env.get("parent_lineage", {}).get("consumed_inputs", [])
    parent_ids = {row.get("sim_id") for row in parent_rows if isinstance(row, dict)}
    require(errors, REQUIRED_PARENT_IDS <= parent_ids, "parent_lineage missing required parent ids")
    require(errors, all(row.get("sha256") for row in parent_rows if isinstance(row, dict)), "parent lineage rows need sha256")

    carrier = env.get("carrier", {})
    require(errors, carrier.get("dimension") == 8, "carrier dimension must be 8")
    require(errors, carrier.get("site_count") == 3, "carrier site_count must be 3")
    require(errors, carrier.get("not_support_graph_only") is True, "carrier must not be support graph only")
    require(
        errors,
        carrier.get("carrier_source_kind") == "reconstructed_from_committed_stage_site_spinors",
        "carrier source kind must state reconstructed-from-parent-site-spinors",
    )
    require(errors, carrier.get("parent_state_vector_row_copied") is False, "carrier must not claim copied parent state-vector row")
    require(errors, bool(carrier.get("reconstructed_state_vector_sha256")), "carrier reconstruction hash missing")
    require(errors, bool(carrier.get("reconstructed_probabilities_sha256")), "carrier probability hash missing")
    require(errors, abs(float(carrier.get("norm", 0.0)) - 1.0) <= TOL, "carrier norm must be 1")

    coupling = env.get("terrain_dependent_network_coupling", {})
    matrix_elements = coupling.get("coupling_construction", {}).get("matrix_elements", {})
    for key in ("A_zx", "A_zy", "A_zz", "b_z"):
        require(errors, key in matrix_elements, f"coupling construction missing {key}")
    require(errors, len(coupling.get("edge_rows", [])) == 3, "terrain coupling must have three edge rows")
    require(errors, coupling.get("continuity", {}).get("pass") is True, "continuity row must pass")

    flux = env.get("flux_transport_row", {})
    require(errors, len(flux.get("edge_transport_rows", [])) == 3, "flux transport row must include three edges")
    require(errors, flux.get("continuity", {}).get("max_abs_residual") == 0.0, "flux continuity residual must be zero")

    ratcheted = env.get("ratcheted_rows", {})
    require(errors, ratcheted.get("mode") == "RATCHETED", "ratcheted_rows.mode mismatch")
    conditioning = ratcheted.get("conditioning", {})
    require(errors, abs(float(conditioning.get("weight_sum", 0.0)) - 1.0) <= TOL, "conditioning weights must sum to 1")
    require(errors, "universal_all-family_mirror" in conditioning.get("network_observables_excluded", []), "mirror exclusion missing")

    controls = env.get("collapse_controls", {})
    for key in (
        "decoupling_edges_recovers_rung2_per_site",
        "density_quotient_recovers_committed_n3_ladder",
        "dropping_terrain_recovers_bare_network",
        "permuted_etas",
        "shuffled_couplings",
        "naive_conditioning_fails",
    ):
        require(errors, controls.get(key, {}).get("pass") is True, f"control {key} must pass")
    require(
        errors,
        controls.get("decoupling_edges_recovers_rung2_per_site", {}).get("z_dot_consistent_on_parent_rows") is True,
        "decoupling control must assert exact z_dot agreement on parent rows",
    )
    require(
        errors,
        controls.get("decoupling_edges_recovers_rung2_per_site", {}).get("byte_consistent_on_parent_exact_rows") is not True,
        "decoupling control must not claim full-row byte consistency across different schemas",
    )
    require(
        errors,
        controls.get("decoupling_edges_recovers_rung2_per_site", {}).get("parent_child_row_schema_identical") is False,
        "decoupling control must state parent/child full-row schemas differ",
    )
    for terrain, row in controls.get("decoupling_edges_recovers_rung2_per_site", {}).get("rows", {}).items():
        require(errors, row.get("z_dot_rows_same_schema_sha256_match") is True, f"{terrain} z_dot same-schema hash must match")
        require(errors, row.get("full_schema_byte_comparison_claimed") is False, f"{terrain} must not claim full-schema byte comparison")

    zero_control = controls.get("dropping_terrain_recovers_bare_network", {})
    require(errors, zero_control.get("terrain_zero_recomputed") is True, "dropping terrain control must recompute zero-terrain network")
    require(errors, zero_control.get("couplings_zero") is True, "zero-terrain couplings must be zero")
    require(errors, zero_control.get("currents_zero") is True, "zero-terrain currents must be zero")
    require(errors, zero_control.get("transport_flux_zero") is True, "zero-terrain transport flux must be zero")
    require(
        errors,
        zero_control.get("committed_bare_current_parent_row_compared") is False,
        "dropping terrain control must honestly carry absent committed bare-current parent row comparison",
    )
    require(errors, bool(zero_control.get("carried_caveat")), "dropping terrain control must carry named G3 remainder")

    proofs = env.get("crossover_proofs", {})
    for name in ("z3", "cvc5", "julia_z3"):
        proof = proofs.get(name, {})
        require(errors, proof.get("ran") is True, f"{name} proof must run")
        require(errors, proof.get("load_bearing") is True, f"{name} proof must be load-bearing")
        require(errors, proof.get("verdict") == "unsat", f"{name} proof verdict must be unsat")
        require(errors, proof.get("erased_flip_verdict") == "sat", f"{name} erased flip must be sat")
        require(errors, proof.get("asserted_precomputed_boolean") is False, f"{name} must not assert only a precomputed boolean")
        require(errors, proof.get("formula_terms_bound") is True, f"{name} must bind formula terms in solver")
        require(errors, proof.get("edge_current_terms_in_solver") is True, f"{name} must bind edge current terms in solver")
        require(errors, proof.get("divergence_derived_in_solver") is True, f"{name} must derive divergence in solver")
        proof_row = proof.get("proof_row", {})
        require(errors, bool(proof_row.get("edge_formula_rows")), f"{name} proof row must include edge formula rows")
        require(errors, bool(proof_row.get("site_balance_rows")), f"{name} proof row must include site balance rows")
        target_rows = [row for row in proof_row.get("site_balance_rows", []) if row.get("site_id") == proof_row.get("site_id")]
        require(errors, len(target_rows) == 1, f"{name} proof must have exactly one target site row")
        if target_rows:
            target_row = target_rows[0]
            require(errors, target_row.get("derived_divergence_matches_row") is True, f"{name} target site divergence must be derived from edge currents")
            require(errors, target_row.get("balance_residual_scaled") == 0, f"{name} target site balance residual must be zero")

    hardening = env.get("builder_hardening_addendum", {})
    for caveat in ("G1", "G2", "G3", "G4"):
        require(errors, bool(hardening.get(caveat)), f"builder hardening addendum must name {caveat}")

    one_to_one = env.get("one_to_one_tool_calls", {})
    require(errors, one_to_one.get("pass") is True, "one-to-one tool call gate must pass")
    require(errors, one_to_one.get("capability_receipt_ids") == one_to_one.get("tool_call_ids"), "tool call ids must match capability ids")

    divergence = env.get("divergence", {})
    require(errors, divergence.get("julia_authoritative") is True, "divergence.julia_authoritative must be true")
    require(errors, float(divergence.get("max_divergence", 1.0)) <= TOL, "max divergence too large")

    gates = env.get("build_gates", {})
    for key, value in gates.items():
        require(errors, value is True, f"build gate {key} must be true")
    if phase == "builder":
        errors.extend(builder_audit_boundary_errors(env, SIM_DIR / "audit_verdict.md"))


def validate_leg(errors: list[str], label: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{label} sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", f"{label} classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{label} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{label} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{label} reads_peer_result must be false")
    require(errors, payload.get("engine_contract", {}).get("mode") == "RATCHETED", f"{label} engine_contract.mode mismatch")
    require(errors, payload.get("all_pass") is True, f"{label} all_pass must be true")
    require(errors, bool(payload.get("packages_used")), f"{label} packages_used missing")
    require(errors, bool(payload.get("aligned_packages_load_bearing")), f"{label} load-bearing package list missing")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["builder", "post_audit"], default="builder")
    args = parser.parse_args()

    errors: list[str] = []
    payloads: dict[str, Any] = {}
    for label, path in RESULT_PATHS.items():
        if not path.exists():
            errors.append(f"missing {label} result: {path.relative_to(ROOT)}")
            continue
        payloads[label] = load_json(path)

    for label in ("julia", "jax", "pytorch"):
        if isinstance(payloads.get(label), dict):
            validate_leg(errors, label, payloads[label])
    if isinstance(payloads.get("envelope"), dict):
        validate_envelope(errors, payloads["envelope"], args.phase)

    scan_for_forbidden_word(errors)

    result = {
        "schema_version": f"{SIM_ID}.validator.v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "validator": SOURCE_PATH.relative_to(ROOT).as_posix(),
        "validator_sha256": sha256_file(SOURCE_PATH),
        "phase": args.phase,
        "ok": not errors,
        "errors": errors,
        "checked_paths": [path.relative_to(ROOT).as_posix() for path in RESULT_PATHS.values()],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not errors, "errors": errors, "result_path": VALIDATOR_RESULT_PATH.relative_to(ROOT).as_posix()}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
