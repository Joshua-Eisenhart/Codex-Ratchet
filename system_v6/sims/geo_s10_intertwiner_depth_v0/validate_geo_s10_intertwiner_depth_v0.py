#!/usr/bin/env python3
"""Validate geo_s10_intertwiner_depth_v0 result shape and bounded gates."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s10_intertwiner_depth_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
DEFAULT_RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def rel(path: Path) -> str:
    if not path.is_absolute():
        path = ROOT / path
    return str(path.relative_to(ROOT))


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def forbidden_token_errors() -> list[str]:
    token = "fix" + "ture"
    errors = []
    for path in SIM_DIR.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".jl", ".json", ".md"}:
            if token in path.read_text(encoding="utf-8"):
                errors.append(f"forbidden token found in {rel(path)}")
    return errors


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema_version mismatch")
    require(payload.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(payload.get("mode") == "SYMBOLIC_LIGHT_LOCAL_INTERTWINER_DEPTH", errors, "mode mismatch")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification must be scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("stage_movement_allowed") is False, errors, "stage_movement_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")

    parents = as_dict(payload.get("parent_lineage"), "parent_lineage", errors)
    require(set(parents) == {"geo_s10_g2_family_v0", "ratchet_g2_family_v0"}, errors, "parent_lineage mismatch")
    geo = as_dict(parents.get("geo_s10_g2_family_v0"), "geo parent", errors)
    ratchet = as_dict(parents.get("ratchet_g2_family_v0"), "ratchet parent", errors)
    require(str(geo.get("committed_commit", "")).startswith("77a4f5d19"), errors, "geo parent commit prefix mismatch")
    require(str(ratchet.get("committed_commit", "")).startswith("b5649217c"), errors, "ratchet parent commit prefix mismatch")
    require(bool(geo.get("envelope_sha256")) and bool(ratchet.get("envelope_sha256")), errors, "parent envelope hashes missing")

    engine_contract = as_dict(payload.get("engine_contract"), "engine_contract", errors)
    require(engine_contract.get("lanes") == ["julia", "jax"], errors, "engine lanes mismatch")
    aliases = as_dict(engine_contract.get("lane_aliases"), "engine_contract.lane_aliases", errors)
    require(aliases.get("jax") == "python_sympy_exact", errors, "jax lane alias mismatch")
    require(aliases.get("julia") == "julia_nemo_hecke", errors, "julia lane alias mismatch")
    omissions = as_dict(engine_contract.get("omitted_lanes"), "engine_contract.omitted_lanes", errors)
    require(bool(omissions.get("pytorch")), errors, "PyTorch omission declaration missing")
    require(
        engine_contract.get("standard_schema_binding")
        == "schema_version is a field with value three_engine_sim_result_v1; packet-local mode is declared separately",
        errors,
        "standard schema binding mismatch",
    )
    require(engine_contract.get("julia_project") == "system_v6/optional/nemo_hecke", errors, "Julia project declaration mismatch")

    math_payload = as_dict(payload.get("math_payload"), "math_payload", errors)
    triality = as_dict(math_payload.get("triality_intertwiners"), "triality_intertwiners", errors)
    reps = as_dict(triality.get("representations"), "representations", errors)
    require(set(reps) == {"8v", "8c", "8s"}, errors, "triality rep set mismatch")
    for name in ("8v", "8c", "8s"):
        row = as_dict(reps.get(name), f"representations.{name}", errors)
        require(row.get("generated_lie_closure_dimension") == 28, errors, f"{name} closure dimension must be 28")
        require(row.get("chevalley_generator_count") == 12, errors, f"{name} generator count must be 12")
    cycle_rows = triality.get("cycle_maps")
    trans_rows = triality.get("transposition_maps")
    require(isinstance(cycle_rows, list) and len(cycle_rows) == 3, errors, "cycle_maps must have three rows")
    require(isinstance(trans_rows, list) and len(trans_rows) == 3, errors, "transposition_maps must have three rows")
    for group_name, rows in (("cycle_maps", cycle_rows), ("transposition_maps", trans_rows)):
        if isinstance(rows, list):
            for idx, row_any in enumerate(rows):
                row = as_dict(row_any, f"{group_name}.{idx}", errors)
                verification = as_dict(row.get("verification"), f"{group_name}.{idx}.verification", errors)
                require(verification.get("passes") is True, errors, f"{group_name}.{idx} must pass")
                require(verification.get("residual_nonzero_entries") == 0, errors, f"{group_name}.{idx} residual must be zero")
                require(verification.get("verified_generator_count") == 12, errors, f"{group_name}.{idx} generator count drift")
                require(verification.get("matrix_rank") == 8, errors, f"{group_name}.{idx} rank must be 8")
    order = as_dict(triality.get("order_3_cubed_scalar"), "order_3_cubed_scalar", errors)
    require(order.get("passes") is True and str(order.get("scalar")) == "1", errors, "order-3 cubed scalar must be 1")
    require(as_dict(triality.get("transposition_squared_scalar"), "transposition_squared_scalar", errors).get("passes") is True, errors, "transposition square failed")
    require(as_dict(triality.get("s3_relation_TCT_equals_C_inverse"), "s3_relation", errors).get("passes") is True, errors, "S3 relation failed")
    wrong = as_dict(triality.get("wrong_intertwiner_control"), "wrong_intertwiner_control", errors)
    require(wrong.get("control_fired") is True, errors, "wrong-intertwiner control must fire")
    require(wrong.get("residual_nonzero_entries", 0) > 0, errors, "wrong-intertwiner residual must be nonzero")

    null_levi = as_dict(math_payload.get("split_null_Levi"), "split_null_Levi", errors)
    bookkeeping = as_dict(null_levi.get("dimension_bookkeeping"), "dimension_bookkeeping", errors)
    require(bookkeeping.get("stabilizer_dim") == 8, errors, "null stabilizer dim must be 8")
    require(bookkeeping.get("nilradical_dim") == 5, errors, "nilradical dim must be 5")
    require(bookkeeping.get("Levi_quotient_dim") == 3, errors, "Levi quotient dim must be 3")
    require(bookkeeping.get("identity_holds") is True, errors, "dimension identity must hold")
    require(null_levi.get("split_null_norm") == 0, errors, "split vector must be null")
    split_profile = as_dict(null_levi.get("split_null_decomposition"), "split_null_decomposition", errors)
    require(split_profile.get("radical_dim") == 5, errors, "radical dim must be 5")
    require(split_profile.get("nilradical_dim") == 5, errors, "nilradical dim must be 5")
    require(split_profile.get("nilradical_lower_central_dims") == [5, 3, 2, 0], errors, "nilradical lower central dims drift")
    quotient = as_dict(split_profile.get("Levi_quotient"), "Levi_quotient", errors)
    require(quotient.get("quotient_dim") == 3, errors, "quotient dim must be 3")
    require(quotient.get("derived_dim") == 3, errors, "quotient derived dim must be 3")
    require(quotient.get("center_dim") == 0, errors, "quotient center dim must be 0")
    require(quotient.get("killing_rank") == 3, errors, "quotient Killing rank must be 3")
    signature = as_dict(quotient.get("killing_signature"), "quotient.killing_signature", errors)
    require(signature.get("positive", 0) > 0 and signature.get("negative", 0) > 0, errors, "quotient Killing signature must be indefinite")
    require(quotient.get("identification") == "sl2_R_by_dim3_center0_derived3_and_indefinite_nonzero_Killing_form", errors, "quotient identification mismatch")

    compact_control = as_dict(null_levi.get("compact_positive_control"), "compact_positive_control", errors)
    require(compact_control.get("nilradical_zero") is True, errors, "compact nilradical must be zero")
    require(compact_control.get("reductive_control_passes") is True, errors, "compact reductive control must pass")
    sign_control = as_dict(null_levi.get("sign_flip_closure_control"), "sign_flip_closure_control", errors)
    require(sign_control.get("control_fired") is True, errors, "sign-flip closure control must fire")
    require(sign_control.get("closure_under_commutator") is False, errors, "mutated bracket closure must fail")

    proofs = as_dict(payload.get("crossover_proofs"), "crossover_proofs", errors)
    for solver in ("z3", "cvc5"):
        row = as_dict(proofs.get(solver), f"crossover_proofs.{solver}", errors)
        require(row.get("ran") is True, errors, f"{solver} must run")
        require(row.get("load_bearing") is True, errors, f"{solver} must be load-bearing")
        require(row.get("verdict") == "unsat", errors, f"{solver} positive verdict must be unsat")
        require(row.get("erased_flip_verdict") == "sat", errors, f"{solver} erased verdict must be sat")
        require(row.get("erased_flip_detected") is True, errors, f"{solver} erased flip missing")

    nemo = as_dict(payload.get("nemo_hecke"), "nemo_hecke", errors)
    require(nemo.get("all_pass") is True, errors, "Nemo sidecar must pass")
    runtime = as_dict(nemo.get("runtime"), "nemo.runtime", errors)
    require(str(runtime.get("active_project", "")).endswith("system_v6/optional/nemo_hecke/Project.toml"), errors, "Nemo active project mismatch")
    s3 = as_dict(nemo.get("outer_s3_row"), "outer_s3_row", errors)
    require(s3.get("gl2_2_order") == 6, errors, "GL(2,2) order must be 6")
    require(s3.get("cycle_order") == 3, errors, "Nemo cycle order must be 3")
    require(s3.get("transposition_order") == 2, errors, "Nemo transposition order must be 2")
    require(s3.get("s3_relation_TCT_equals_C_inverse") is True, errors, "Nemo S3 relation failed")

    calls = payload.get("tool_calls")
    require(isinstance(calls, list) and len(calls) == 4, errors, "tool_calls must contain four rows")
    if isinstance(calls, list):
        require([call.get("tool") for call in calls] == ["sympy", "z3", "cvc5", "Nemo"], errors, "tool call order mismatch")
        require(all(call.get("load_bearing") is True for call in calls), errors, "all tool calls must be load-bearing")
    require(payload.get("claim_path_tools") == ["sympy", "z3", "cvc5", "Nemo"], errors, "claim_path_tools mismatch")

    gates = as_dict(payload.get("build_gates"), "build_gates", errors)
    for gate in (
        "mode_declared",
        "ceilings_preserved",
        "parents_exactly_requested",
        "parent_commits_match_requested_prefixes",
        "triality_reps_generate_so8_dim28",
        "triality_intertwiner_residuals_zero",
        "triality_order3_cubed_scalar",
        "triality_s3_relations",
        "wrong_intertwiner_control_fired",
        "split_null_stabilizer_dim8",
        "split_null_nilradical_dim5",
        "split_null_Levi_quotient_dim3",
        "split_null_dim_bookkeeping",
        "split_null_Levi_quotient_sl2",
        "compact_positive_control_nilradical_zero",
        "sign_flip_closure_control_fired",
        "smt_positive_and_erased_flip",
        "nemo_sidecar_loaded",
        "nemo_project_recorded",
        "one_to_one_tool_calls",
        "capability_receipts_present",
        "forbidden_word_absent",
        "no_audit_verdict_emitted",
    ):
        require(gates.get(gate) is True, errors, f"gate {gate} must be true")

    errors.extend(forbidden_token_errors())
    return errors


def main(argv: list[str]) -> int:
    result_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_RESULT
    if not result_path.is_absolute():
        result_path = ROOT / result_path
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate(payload)
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    out = {
        "ok": not errors,
        "mode": payload.get("mode"),
        "result_json": rel(result_path),
        "validator": rel(Path(__file__)),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    VALIDATOR_RESULT.parent.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
