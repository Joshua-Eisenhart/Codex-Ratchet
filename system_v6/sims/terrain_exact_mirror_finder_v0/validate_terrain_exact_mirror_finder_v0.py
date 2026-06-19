#!/usr/bin/env python3
"""Packet-local validator for terrain_exact_mirror_finder_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "terrain_exact_mirror_finder_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
PYTHON_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_python_results.json"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
ENVELOPE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
SOURCE_PATH = SIM_DIR / f"validate_{SIM_ID}.py"
TOL = 1.0e-9


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    py = load_json(PYTHON_RESULT_PATH)
    jl = load_json(JULIA_RESULT_PATH)
    env = load_json(ENVELOPE_RESULT_PATH)
    errors.extend(builder_audit_boundary_errors(env, SIM_DIR / "audit_verdict.md"))
    for label, payload in (("python", py), ("julia", jl), ("envelope", env)):
        require(errors, payload.get("classification") == "scratch_diagnostic", f"{label} classification must be scratch_diagnostic")
        require(errors, payload.get("promotion_allowed") is False, f"{label} promotion_allowed must be false")
        require(errors, payload.get("formal_admission_allowed") is False, f"{label} formal_admission_allowed must be false")
        require(errors, payload.get("all_pass") is True, f"{label} all_pass must be true")
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "envelope schema mismatch")
    require(errors, env.get("engine_contract", {}).get("mode") == "FIELD", "engine_contract.mode must be FIELD")
    require(errors, "pytorch" not in env.get("engines", {}), "pytorch must remain omitted")
    require(errors, env.get("owner_single_mirror_reading_survives") is False, "owner common mirror reading must not survive")
    require(errors, py.get("owner_single_mirror_reading_survives") is False, "python owner common mirror reading must not survive")
    require(errors, py.get("s5_hash_ok") is True and jl.get("s5_hash_ok") is True, "S5 hash checks must pass")

    sols = py.get("per_family_solution_sets", {})
    require(errors, sols.get("Se", {}).get("dimension") == "one_parameter_continuum", "Se solution dimension mismatch")
    require(errors, sols.get("Ne", {}).get("dimension") == "one_parameter_continuum", "Ne solution dimension mismatch")
    require(errors, sols.get("Ni", {}).get("solution_set") == "single matrix", "Ni must have a single matrix solution")
    require(errors, sols.get("Si", {}).get("dimension") == "one_parameter_continuum", "Si solution dimension mismatch")
    require(errors, sols.get("Si", {}).get("candidate_class_a_pi_rotations_perp_h0") == "empty", "Si corrected sigma_y analog class must be empty")
    require(errors, sols.get("Ni", {}).get("representative_exact") is True, "Ni representative must be exact")
    require(errors, sols.get("Si", {}).get("proper_representative_exact") is True, "Si proper representative must be exact")
    require(errors, sols.get("Si", {}).get("reflection_representative_exact") is True, "Si reflection representative must be exact")

    common = py.get("common_intersection", {})
    require(errors, common.get("common_all_four_solution_set") == "empty", "common all-four solution set must be empty")
    require(errors, common.get("common_all_four_exists") is False, "common all-four exists flag must be false")
    rows = common.get("Se_Ne_Ni_common_representative_rows", [])
    require(errors, len(rows) == 4, "M_Ni common representative rows must cover four families")
    require(errors, all(row.get("exact") for row in rows if row.get("family") in {"Se", "Ne", "Ni"}), "M_Ni must solve Se/Ne/Ni")
    require(errors, any(row.get("family") == "Si" and row.get("exact") is False and row.get("max_abs_residual", 0) > TOL for row in rows), "M_Ni must fail Si")

    controls = py.get("controls", {})
    require(errors, controls.get("sigma_y_candidate", {}).get("all_fail") is True, "sigma_y must fail all four")
    require(errors, controls.get("sigma_y_candidate", {}).get("matches_committed_refutation") is True, "sigma_y residuals must match refutation")
    require(errors, controls.get("identity_candidate", {}).get("all_fail") is True, "identity control must fail")
    require(errors, controls.get("random_orthogonal_candidate", {}).get("all_fail") is True, "random orthogonal control must fail")
    require(errors, py.get("xz_frame_positive_control", {}).get("exact") is True, "Hxz positive control must recover sigma_y exactly")
    require(errors, py.get("spinor_lift_consistency", {}).get("pass") is True, "spinor lift consistency must pass")
    require(errors, py.get("spinor_lift_consistency", {}).get("liouvillian_intertwining_residual_norm", 1) <= TOL, "spinor Liouvillian residual too large")
    require(errors, all(row.get("pass") is True for row in py.get("smt_solve_space_identities", {}).values()), "python SMT rows must pass")
    require(errors, jl.get("symbolics_rows", {}).get("pass") is True, "Julia Symbolics rows must pass")
    z3_rows = jl.get("z3_rows", {})
    require(errors, z3_rows.get("M_Ni_first_three_zero", {}).get("any_nonzero_status") == "unsat", "Julia M_Ni zero any-nonzero must be unsat")
    require(errors, z3_rows.get("Si_erased_flip_control_nonzero", {}).get("forced_zero_status") == "unsat", "Julia erased Si control forced-zero must be unsat")
    require(errors, env.get("divergence", {}).get("julia_authoritative") is True, "divergence.julia_authoritative must be true")
    require(errors, env.get("divergence", {}).get("max_divergence") == 0.0, "divergence.max_divergence must be zero")

    payload = {
        "schema_version": f"{SIM_ID}.validator.v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "validator": str(SOURCE_PATH.relative_to(ROOT)),
        "validator_sha256": sha256_file(SOURCE_PATH),
        "ok": not errors,
        "errors": errors,
        "checked_paths": [
            str(PYTHON_RESULT_PATH.relative_to(ROOT)),
            str(JULIA_RESULT_PATH.relative_to(ROOT)),
            str(ENVELOPE_RESULT_PATH.relative_to(ROOT)),
        ],
    }
    with VALIDATOR_RESULT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({"ok": not errors, "errors": errors, "result_path": str(VALIDATOR_RESULT_PATH)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
