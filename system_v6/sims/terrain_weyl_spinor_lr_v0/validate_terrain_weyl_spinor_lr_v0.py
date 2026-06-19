#!/usr/bin/env python3
"""Packet-local validator for terrain_weyl_spinor_lr_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "terrain_weyl_spinor_lr_v0"
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

    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "envelope schema_version mismatch")
    require(errors, env.get("engine_contract", {}).get("mode") == "julia_canon_plus_python_exact_diagnostic", "engine_contract.mode mismatch")
    require(errors, isinstance(env.get("engines", {}).get("julia"), dict), "envelope must populate engines.julia")
    require(errors, isinstance(env.get("engines", {}).get("jax"), dict), "envelope must populate engines.jax")
    require(errors, "pytorch" not in env.get("engines", {}), "pytorch must remain omitted, not fake-populated")
    require(errors, env.get("divergence", {}).get("julia_authoritative") is True, "divergence.julia_authoritative must be true")
    require(errors, "per_observable" in env.get("divergence", {}), "divergence.per_observable missing")
    require(errors, env.get("divergence", {}).get("max_divergence") == 0.0, "divergence.max_divergence mismatch")
    hash_receipt = env.get("computed_subtree_hashes", {})
    require(errors, hash_receipt.get("kind") == "shape_only_repair_hash_receipt", "shape-only hash receipt missing")
    require(errors, bool(hash_receipt.get("fresh_current_hashes")), "computed subtree hashes missing")
    require(errors, env.get("owner_claim_sigma_y_exact_survives") is False, "owner exact sigma_y claim must not survive this diagnostic")
    require(errors, py.get("owner_claim_sigma_y_exact_survives") is False, "python result must mark owner claim as not surviving")
    require(errors, py.get("s5_hash_ok") is True, "python S5 hash must match expected committed input")
    require(errors, jl.get("s5_hash_ok") is True, "julia S5 hash must match expected committed input")

    mirror_rows = py.get("mirror_pairing_rows", [])
    require(errors, len(mirror_rows) == 4, "must have four mirror pairing rows")
    require(errors, all(row.get("sigma_y_exact") is False for row in mirror_rows), "all four sigma_y mirror exactness rows must be false")
    require(errors, all(row.get("sigma_y_max_abs_residual", 0) > TOL for row in mirror_rows), "all sigma_y mirror residuals must be nonzero")

    anchors = py.get("consistency_anchors", {})
    require(errors, anchors.get("pass") is True, "native lift projection anchors must pass")
    require(errors, anchors.get("max_native_projection_residual", 1) <= 2.0e-12, "native projection residual too large")
    se_anchor = anchors.get("se_funnel_l_gap_4_25_anchor", {})
    require(errors, se_anchor.get("bloch_angular_frequency_squared") == "4/25", "Se_Funnel_L 4/25 anchor missing")
    require(errors, se_anchor.get("pass") is True, "Se_Funnel_L 4/25/projection anchor must pass")

    quotient = py.get("quotient_erasure_row", {})
    require(errors, quotient.get("pass") is True, "quotient erasure row must pass")
    require(errors, quotient.get("two_pi_flip_row", {}).get("density_return_gap_norm", 1) <= TOL, "2pi density return gap too large")
    require(errors, quotient.get("two_pi_flip_row", {}).get("spinor_distance_to_negative_initial", 1) <= TOL, "2pi spinor negative-initial distance too large")

    chirality = py.get("chirality_readout_row", {})
    require(errors, chirality.get("pass") is True, "chirality readout control must pass")
    require(errors, chirality.get("max_blind_abs_signal", 1) <= TOL, "chirality-blind signal must be zero")

    smt = py.get("smt_mirror_residual_identities", {})
    require(errors, all(row.get("pass") is True for row in smt.values()), "python z3/cvc5 SMT rows must pass")
    require(errors, jl.get("quantumoptics_weyl_rows", {}).get("pass") is True, "Julia QuantumOptics row must pass")
    require(errors, jl.get("grassmann_even_subalgebra_row", {}).get("pass") is True, "Julia Grassmann row must pass")
    z3_rows = jl.get("z3_rows", {})
    require(errors, z3_rows.get("H0_sigma_y_exact_forced_control", {}).get("forced_zero_status") == "unsat", "Julia H0 forced-zero Z3 control must be unsat")
    require(errors, z3_rows.get("Hxz_sigma_y_exact_boundary", {}).get("any_nonzero_status") == "unsat", "Julia Hxz zero-boundary Z3 row must be unsat")

    payload = {
        "schema_version": "terrain_weyl_spinor_lr_v0.validator.v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "validator": str(SOURCE_PATH.relative_to(ROOT)),
        "validator_sha256": sha256_file(SOURCE_PATH),
        "declared_mode": "julia_canon_plus_python_exact_diagnostic",
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
