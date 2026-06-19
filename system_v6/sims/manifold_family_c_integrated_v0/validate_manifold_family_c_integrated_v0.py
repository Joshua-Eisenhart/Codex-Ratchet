#!/usr/bin/env python3
"""Packet-local validator for manifold_family_c_integrated_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import manifold_family_c_integrated_v0_common as common


SIM_ID = common.SIM_ID
ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT_DIR = common.RESULT_DIR
RESULT_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
    "envelope": RESULT_DIR / f"{SIM_ID}_envelope_results.json",
}
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"
SOURCE_PATH = SIM_DIR / f"validate_{SIM_ID}.py"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


FORBIDDEN_PHRASES = [
    "formal admission",
    "promotion allowed",
    "bridge evidence",
    "axis evidence",
    "physics evidence",
    "canonical result",
    "final M(C)",
    "QIT-engine admission",
    "new minimum",
    "actual n=5 result",
    "n>4 rung evidence",
    "copied parent state-vector row",
    "committed bare-current parent-row comparison",
    "A+B weld relation computed",
    "cross-family weld controls computed",
    "flux-carrying L/R asymmetric engine object computed",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def scan_for_forbidden_word(errors: list[str]) -> None:
    terrain_banned = "fix" + "ture"
    for path in SIM_DIR.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        if not path.is_file() or path.name == f"{SIM_ID}_validator_results.json":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if terrain_banned in text:
            errors.append(f"forbidden wording {terrain_banned!r} appears in {path.relative_to(ROOT)}")


def validate_leg(errors: list[str], label: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{label} sim_id mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, f"{label} classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{label} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{label} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{label} reads_peer_result must be false")
    require(errors, payload.get("engine_mode") == common.ENGINE_MODE, f"{label} engine_mode mismatch")
    require(errors, payload.get("all_pass") is True, f"{label} all_pass must be true")
    require(errors, bool(payload.get("packages_used")), f"{label} packages_used missing")
    require(errors, bool(payload.get("aligned_packages_load_bearing")), f"{label} load-bearing package list missing")
    require(errors, payload.get("state_object_id") == common.STATE_OBJECT_ID, f"{label} state object mismatch")


def validate_envelope(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "mode must be all_three_full_sims")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    require(errors, set(payload.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must contain all three engines")
    require(errors, payload.get("engine_contract", {}).get("mode") == common.ENGINE_MODE, "engine_contract.mode mismatch")
    require(errors, payload.get("state_object_id") == common.STATE_OBJECT_ID, "state_object_id mismatch")

    require(errors, payload.get("live_rungs") == ["n3", "n4"], "live rungs must be n3/n4 only")
    require(errors, payload.get("n5_behavior_continuation_claimed") is False, "n5 behavior continuation must be false")
    require(errors, payload.get("behavior_class_growth_claimed") is False, "behavior growth claim must be false")
    require(errors, payload.get("raw_stage_lifted_rows_used") is False, "raw lifted rows must not be consumed directly")

    floor = payload.get("floor_anchor", {})
    require(errors, floor.get("sim_id") == "geo_s1_three_qubit_floor_exact_v0", "floor anchor sim id mismatch")
    require(errors, floor.get("commit") == "6ed5e961e", "floor anchor commit mismatch")
    require(errors, floor.get("hilbert_dim") == 8, "floor anchor must be C^8")

    stress = payload.get("boundary_stress_context", {})
    require(errors, stress.get("commit") == "b27d22317", "stress boundary commit mismatch")
    require(errors, stress.get("run_role") == "BOUNDARY_STRESS_CONTEXT_ONLY", "stress context role mismatch")
    require(errors, stress.get("run_in_this_packet") is False, "stress context must not run in this packet")

    state = payload.get("integrated_state_object", {})
    require(errors, state.get("state_object_id") == common.STATE_OBJECT_ID, "integrated state object id mismatch")
    for rung, expected_dim, expected_commit in (("n3", 8, "1b36e4a3c"), ("n4", 16, "c36a80f6b")):
        row = state.get(rung, {})
        require(errors, row.get("source_commit") == expected_commit, f"{rung} commit mismatch")
        require(errors, row.get("carrier_dimension") == expected_dim, f"{rung} carrier dimension mismatch")
        require(errors, row.get("continuity_pass") is True, f"{rung} bare continuity failed")
        require(errors, row.get("conditioned_continuity_pass") is True, f"{rung} conditioned continuity failed")
        require(errors, float(row.get("conditioned_total_abs_current", 0.0)) > 0.0, f"{rung} conditioned current missing")
        require(errors, row.get("carrier_source_kind") == "reconstructed_from_committed_stage_site_spinors", f"{rung} carrier source boundary missing")
        require(errors, row.get("parent_state_vector_row_copied") is False, f"{rung} copied parent state vector")
        require(errors, bool(row.get("source_sha256")), f"{rung} source sha missing")

    mechanics = payload.get("surviving_mechanics", {})
    require(errors, mechanics.get("flux_continuity_same_trajectory", {}).get("survives_composition") is True, "flux continuity did not survive composition")
    current = mechanics.get("conditioned_total_abs_current", {})
    require(errors, current.get("recomputed_in_run") is True, "conditioned current must be recomputed in run")
    for rung in ("n3", "n4"):
        row = current.get("per_rung", {}).get(rung, {})
        require(errors, abs(float(row.get("recomputed", -1.0)) - float(row.get("committed", -2.0))) <= 1.0e-12, f"{rung} recomputed current mismatch")

    controls = payload.get("integration_controls", {})
    for name in ("zero_terrain_network", "decoupled_leaf", "scrambled_coupling"):
        control = controls.get(name, {})
        require(errors, control.get("fires") is True, f"{name} did not fire")
        require(errors, control.get("moves_named_rows") is True, f"{name} did not move named rows")
        require(errors, control.get("demotes_if_not_firing") is True, f"{name} missing demotion condition")

    boundaries = payload.get("carried_boundaries", {})
    require(errors, "no committed bare-current parent-row comparison" in boundaries.get("G3", ""), "G3 boundary missing")
    require(errors, "carrier reconstructed, not copied" in boundaries.get("G4", ""), "G4 boundary missing")

    artifact = payload.get("trajectory_artifact", {})
    require(errors, artifact.get("sha_verified") is True, "trajectory artifact sha not verified")
    artifact_path = ROOT / artifact.get("path", "")
    sha_path = ROOT / artifact.get("sha_path", "")
    require(errors, artifact_path.exists(), "trajectory artifact path missing")
    require(errors, sha_path.exists(), "trajectory sidecar path missing")
    if artifact_path.exists():
        stored = load_json(artifact_path)
        require(errors, stored.get("state_object_id") == common.STATE_OBJECT_ID, "trajectory state object mismatch")
        classes = {row.get("row_step_class") for row in stored.get("step_rows", [])}
        require(errors, {"STEP_DEPENDENT", "INVARIANT"} <= classes, "trajectory needs dependent and invariant rows")
        require(errors, all(row.get("sha_verified") is True for row in stored.get("step_rows", [])), "trajectory row sha flag failed")

    proofs = payload.get("crossover_proofs", {})
    for name in ("z3", "cvc5", "julia_z3"):
        proof = proofs.get(name, {})
        require(errors, proof.get("ran") is True, f"{name} proof did not run")
        require(errors, proof.get("load_bearing") is True, f"{name} proof must be load-bearing")
        require(errors, proof.get("verdict") == "unsat", f"{name} verdict must be unsat")
        require(errors, proof.get("erased_flip_verdict") == "sat", f"{name} erased flip must be sat")
        require(errors, proof.get("asserted_precomputed_boolean") is False, f"{name} must not assert precomputed boolean")
        require(errors, proof.get("formula_terms_bound") is True, f"{name} formula terms not bound")
        require(errors, proof.get("edge_current_terms_in_solver") is True, f"{name} edge-current terms not bound")
        require(errors, proof.get("divergence_derived_in_solver") is True, f"{name} divergence derivation not bound")

    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    require(errors, "A+B weld relation" in payload.get("out_of_scope", []), "A+B weld relation must remain out of scope")
    require(errors, payload.get("no_builder_audit_verdict") is True, "builder/audit boundary flag missing")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))


def main() -> int:
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
        validate_envelope(errors, payloads["envelope"])
    scan_for_forbidden_word(errors)

    result = {
        "schema_version": f"{SIM_ID}.validator.v1",
        "sim_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "validator": SOURCE_PATH.relative_to(ROOT).as_posix(),
        "validator_sha256": sha256_file(SOURCE_PATH),
        "ok": not errors,
        "errors": errors,
        "checked_paths": [path.relative_to(ROOT).as_posix() for path in RESULT_PATHS.values()],
    }
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps({"ok": not errors, "errors": errors, "result_path": VALIDATOR_RESULT.relative_to(ROOT).as_posix()}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
