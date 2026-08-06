#!/usr/bin/env python3
"""Verify a retained attractor-basin controller envelope without rerunning engines."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any


EXPECTED_COUNTS = {"negative": 165, "boundary": 11, "positive": 165}
EXPECTED_RADII = [6, 12, 6]
EXPECTED_WRONG_RADII = [14, 8, 14]
ENGINE_NAMES = ("jax", "julia", "pytorch")
CONTROL_NAMES = {
    "mutated_counts",
    "erased_labels",
    "wrong_provenance",
    "missing_lane",
    "role_conflation",
    "workflow_cycle",
    "workflow_skipped_prerequisite",
    "diffrax_operation_severance",
    "smt_severance",
}
FORMAL_CASES = {
    "workflow_valid": ("ELIGIBLE", "workflow_graph_obligations_satisfied"),
    "workflow_cycle": ("BLOCKED", "workflow_graph_cycle_detected"),
    "workflow_skipped_prerequisite": (
        "BLOCKED",
        "workflow_graph_required_reachability_missing",
    ),
    "symbolic_x3_minus_x": ("ELIGIBLE", "exact_polynomial_recomputed"),
    "boundary_valid": ("ELIGIBLE", "boundary_contract_roles_separated"),
    "boundary_role_conflation": ("BLOCKED", "boundary_role_conflation"),
}


class VerificationError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_object_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                VerificationError(f"non-finite JSON value: {value}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"{path} root is not an object")
    return value


def as_object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path}:not_object")
        return {}
    return value


def check_file(path_value: Any, expected_hash: Any, label: str, errors: list[str]) -> None:
    if not isinstance(path_value, str) or not isinstance(expected_hash, str):
        errors.append(f"{label}:path_or_hash_invalid")
        return
    path = Path(path_value)
    if not path.is_file():
        errors.append(f"{label}:file_missing")
        return
    if sha256_file(path) != expected_hash:
        errors.append(f"{label}:sha256_mismatch")


def replay_projection(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "receipt_sha256"}


def load_controller_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        "constraintbox_retained_basin_controller", path
    )
    if spec is None or spec.loader is None:
        raise VerificationError("cannot load retained controller source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_envelope(path: Path) -> dict[str, Any]:
    envelope = read_object(path)
    errors: list[str] = []
    body = {key: value for key, value in envelope.items() if key != "envelope_sha256"}
    if envelope.get("envelope_sha256") != sha256_bytes(canonical(body)):
        errors.append("envelope:canonical_body_sha256_mismatch")
    if envelope.get("schema") != "three_engine_sim_result_v1":
        errors.append("envelope:schema_mismatch")

    controller = as_object(envelope.get("controller"), "controller", errors)
    check_file(
        controller.get("source_path"),
        controller.get("source_sha256"),
        "controller_source",
        errors,
    )
    controller_source = Path(str(controller.get("source_path", "")))
    controller_module: Any | None = None
    if controller_source.is_file():
        try:
            controller_module = load_controller_module(controller_source)
        except Exception as exc:
            errors.append(f"controller_source:load_failed:{type(exc).__name__}:{exc}")
    object_card = as_object(envelope.get("object_card"), "object_card", errors)
    check_file(object_card.get("path"), object_card.get("sha256"), "object_card", errors)

    boundary = as_object(envelope.get("boundary"), "boundary", errors)
    if boundary.get("external_sim_engines_are_constraintbox_core") is not False:
        errors.append("boundary:external_sim_conflated_with_core")
    if boundary.get("smt_is_external_sim_engine") is not False:
        errors.append("boundary:smt_conflated_with_sim_engine")
    if boundary.get("claim_gate_sim_admission") is not False:
        errors.append("boundary:unsupported_claimgate_admission")

    result = as_object(envelope.get("result"), "result", errors)
    if result.get("bounded_run_status") != "PASS":
        errors.append("result:not_bounded_pass")
    if result.get("partition_counts") != EXPECTED_COUNTS:
        errors.append("result:partition_counts_mismatch")
    if result.get("fixed_point_spectral_radii_tenths") != EXPECTED_RADII:
        errors.append("result:nominal_radii_mismatch")
    if result.get("wrong_fixed_point_spectral_radii_tenths") != EXPECTED_WRONG_RADII:
        errors.append("result:wrong_radii_mismatch")
    for field in (
        "promotion_allowed",
        "continuous_basin_proof",
        "formal_admission_allowed",
        "scientific_admission_allowed",
        "whole_sim_estate_integrated",
        "automatic_tuning_established",
    ):
        if result.get(field) is not False:
            errors.append(f"result:{field}_must_be_false")

    controls = as_object(envelope.get("adversarial_controls"), "controls", errors)
    if set(controls) != CONTROL_NAMES:
        errors.append("controls:name_set_mismatch")
    for name in CONTROL_NAMES:
        if as_object(controls.get(name), f"controls.{name}", errors).get("caught") is not True:
            errors.append(f"controls.{name}:not_caught")
    smt_severance_control = as_object(
        controls.get("smt_severance"), "controls.smt_severance", errors
    )
    negative_flow = as_object(
        smt_severance_control.get("retained_negative_minilev"),
        "controls.smt_severance.retained_negative_minilev",
        errors,
    )
    if negative_flow.get("terminal") != "BLOCKED":
        errors.append("controls.smt_severance:negative_flow_not_blocked")
    negative_root = path.parent / "outer_minilev_smt_severed"
    check_file(
        str(negative_root / "flow_receipt.json"),
        negative_flow.get("receipt_file_sha256"),
        "controls.smt_severance.receipt",
        errors,
    )
    check_file(
        str(negative_root / "flow_ledger.jsonl"),
        negative_flow.get("ledger_sha256"),
        "controls.smt_severance.ledger",
        errors,
    )

    engine_runs = as_object(envelope.get("engine_runs"), "engine_runs", errors)
    agreed = as_object(
        envelope.get("agreed_engine_observations"), "agreed_engine_observations", errors
    )
    if set(engine_runs) != set(ENGINE_NAMES) or set(agreed) != set(ENGINE_NAMES):
        errors.append("engines:lane_set_mismatch")
    for name in ENGINE_NAMES:
        lane = as_object(engine_runs.get(name), f"engine_runs.{name}", errors)
        if lane.get("semantic_replay_equal") is not True:
            errors.append(f"engine_runs.{name}:replay_not_equal")
        runs = lane.get("runs")
        if not isinstance(runs, list) or len(runs) != 2:
            errors.append(f"engine_runs.{name}:run_count_mismatch")
            continue
        normalized: list[dict[str, Any]] = []
        rederived: list[dict[str, Any]] = []
        for index, run_value in enumerate(runs):
            run = as_object(run_value, f"engine_runs.{name}.runs[{index}]", errors)
            check_file(
                run.get("receipt_path"),
                run.get("receipt_sha256"),
                f"engine_runs.{name}.runs[{index}].receipt",
                errors,
            )
            item = as_object(run.get("normalized"), f"engine_runs.{name}.normalized", errors)
            if item.get("receipt_sha256") != run.get("receipt_sha256"):
                errors.append(f"engine_runs.{name}.runs[{index}]:normalized_receipt_hash_mismatch")
            normalized.append(item)
            if controller_module is not None and isinstance(run.get("receipt_path"), str):
                receipt_path = Path(run["receipt_path"])
                try:
                    raw_receipt = read_object(receipt_path)
                    worker_root = controller_source.parent
                    if name == "jax":
                        recomputed = controller_module.normalize_jax(
                            raw_receipt,
                            source_path=worker_root / "jax_basin.py",
                            python_runtime=Path(
                                str(controller["worker_python_runtime_resolved"])
                            ),
                            receipt_path=receipt_path,
                        )
                    elif name == "julia":
                        active_project = Path(
                            str(
                                as_object(
                                    raw_receipt.get("runtime"),
                                    "julia.runtime",
                                    errors,
                                ).get("active_project", "")
                            )
                        )
                        recomputed = controller_module.normalize_julia(
                            raw_receipt,
                            source_path=worker_root / "julia_basin.jl",
                            julia_runtime=Path(
                                str(controller["julia_runtime_invocation"])
                            ).resolve(),
                            julia_project_file=active_project,
                            receipt_path=receipt_path,
                        )
                    else:
                        recomputed = controller_module.normalize_torch(
                            raw_receipt,
                            source_path=worker_root / "torch_basin.py",
                            python_runtime=Path(
                                str(controller["worker_python_runtime_resolved"])
                            ),
                            receipt_path=receipt_path,
                        )
                    rederived.append(recomputed)
                    if recomputed != item:
                        errors.append(
                            f"engine_runs.{name}.runs[{index}]:receipt_content_not_normalized"
                        )
                except Exception as exc:
                    errors.append(
                        f"engine_runs.{name}.runs[{index}]:rederive_failed:"
                        f"{type(exc).__name__}:{exc}"
                    )
        if replay_projection(normalized[0]) != replay_projection(normalized[1]):
            errors.append(f"engine_runs.{name}:semantic_projection_mismatch")
        observation = as_object(agreed.get(name), f"agreed.{name}", errors)
        if rederived and observation != rederived[0]:
            errors.append(f"agreed.{name}:not_derived_from_first_receipt")
        if observation.get("partition_counts") != EXPECTED_COUNTS:
            errors.append(f"agreed.{name}:counts_mismatch")
        if observation.get("fixed_point_spectral_radii_tenths") != EXPECTED_RADII:
            errors.append(f"agreed.{name}:radii_mismatch")
        if observation.get("wrong_fixed_point_spectral_radii_tenths") != EXPECTED_WRONG_RADII:
            errors.append(f"agreed.{name}:wrong_radii_mismatch")
        if not observation.get("actual_apis"):
            errors.append(f"agreed.{name}:actual_apis_missing")
        worker_source = controller_source.parent / {
            "jax": "jax_basin.py",
            "julia": "julia_basin.jl",
            "pytorch": "torch_basin.py",
        }[name]
        if not worker_source.is_file() or observation.get("source_sha256") != sha256_file(
            worker_source
        ):
            errors.append(f"agreed.{name}:worker_source_provenance_mismatch")

    jax_lane = as_object(engine_runs.get("jax"), "engine_runs.jax", errors)
    diffrax_severance = as_object(
        jax_lane.get("diffrax_operation_severance"),
        "engine_runs.jax.diffrax_operation_severance",
        errors,
    )
    if not (
        diffrax_severance.get("returncode") == 1
        and diffrax_severance.get("expected_returncode") == 1
        and "CB_DIFFRAX_OPERATION_SEVERED"
        in str(diffrax_severance.get("stderr", ""))
    ):
        errors.append("engine_runs.jax:diffrax_operation_poison_not_observed")

    smt = as_object(envelope.get("smt"), "smt", errors)
    if smt.get("semantic_replay_equal") is not True:
        errors.append("smt:replay_not_equal")
    smt_runs = smt.get("runs")
    if not isinstance(smt_runs, list) or len(smt_runs) != 2:
        errors.append("smt:run_count_mismatch")
    else:
        smt_normalized: list[dict[str, Any]] = []
        smt_rederived: list[dict[str, Any]] = []
        for index, run_value in enumerate(smt_runs):
            run = as_object(run_value, f"smt.runs[{index}]", errors)
            check_file(
                run.get("receipt_path"),
                run.get("receipt_sha256"),
                f"smt.runs[{index}].receipt",
                errors,
            )
            normalized_item = as_object(run.get("normalized"), "smt.normalized", errors)
            smt_normalized.append(normalized_item)
            if controller_module is not None and isinstance(run.get("receipt_path"), str):
                receipt_path = Path(run["receipt_path"])
                try:
                    recomputed = controller_module.normalize_smt(
                        read_object(receipt_path),
                        source_path=controller_source.parent / "smt_basin.py",
                        python_runtime=Path(
                            str(controller["worker_python_runtime_resolved"])
                        ),
                        bundle=as_object(
                            as_object(
                                envelope.get("observation_bundle"),
                                "observation_bundle",
                                errors,
                            ).get("value"),
                            "observation_bundle.value",
                            errors,
                        ),
                        receipt_path=receipt_path,
                    )
                    smt_rederived.append(recomputed)
                    if recomputed != normalized_item:
                        errors.append(
                            f"smt.runs[{index}]:receipt_content_not_normalized"
                        )
                except Exception as exc:
                    errors.append(
                        f"smt.runs[{index}]:rederive_failed:{type(exc).__name__}:{exc}"
                    )
        if replay_projection(smt_normalized[0]) != replay_projection(smt_normalized[1]):
            errors.append("smt:semantic_projection_mismatch")
    selected = as_object(smt.get("selected"), "smt.selected", errors)
    if 'smt_rederived' in locals() and smt_rederived and selected != smt_rederived[0]:
        errors.append("smt.selected:not_derived_from_first_receipt")
    solvers = as_object(selected.get("solvers"), "smt.solvers", errors)
    for solver_name in ("z3", "cvc5"):
        solver = as_object(solvers.get(solver_name), f"smt.{solver_name}", errors)
        if as_object(solver.get("positive"), "smt.positive", errors).get("verdict") != "sat":
            errors.append(f"smt.{solver_name}:positive_not_sat")
        solver_controls = as_object(solver.get("controls"), "smt.controls", errors)
        for control_name in ("contradictory_label", "erased_label", "wrong_sign_stability"):
            control = as_object(solver_controls.get(control_name), "smt.control", errors)
            if control.get("verdict") != "unsat" or control.get(
                "core_contains_control_assumption"
            ) is not True:
                errors.append(f"smt.{solver_name}.{control_name}:unsat_core_missing")

    formal = as_object(envelope.get("constraintbox_formal"), "formal", errors)
    for name, (disposition, reason) in FORMAL_CASES.items():
        case = as_object(formal.get(name), f"formal.{name}", errors)
        decision = as_object(case.get("decision"), f"formal.{name}.decision", errors)
        if decision.get("disposition") != disposition or decision.get("reason") != reason:
            errors.append(f"formal.{name}:decision_mismatch")
        if decision.get("promotion_allowed") is not False:
            errors.append(f"formal.{name}:promotion_must_be_false")
        run_root = Path(str(case.get("run_root", "")))
        check_file(
            str(run_root / "formal_flow_receipt.json"),
            case.get("flow_receipt_sha256"),
            f"formal.{name}.receipt",
            errors,
        )
        check_file(
            str(run_root / "formal_flow_events.jsonl"),
            case.get("flow_ledger_sha256"),
            f"formal.{name}.ledger",
            errors,
        )

    outer = as_object(envelope.get("outer_minilev"), "outer_minilev", errors)
    if outer.get("terminal") != "ELIGIBLE" or outer.get("steps") != 2:
        errors.append("outer_minilev:terminal_or_step_mismatch")
    if outer.get("verification") != "flow receipt and semantic ledger match":
        errors.append("outer_minilev:verification_mismatch")
    if outer.get("promotion_allowed") is not False:
        errors.append("outer_minilev:promotion_must_be_false")
    outer_root = path.parent / "outer_minilev"
    check_file(
        str(outer_root / "flow_receipt.json"),
        outer.get("receipt_file_sha256"),
        "outer_minilev.receipt",
        errors,
    )
    check_file(
        str(outer_root / "flow_ledger.jsonl"),
        outer.get("ledger_sha256"),
        "outer_minilev.ledger",
        errors,
    )

    return {
        "schema": "constraintbox.attractor-basin-envelope-verification.v1",
        "envelope": str(path),
        "envelope_file_sha256": sha256_file(path),
        "envelope_body_sha256": envelope.get("envelope_sha256"),
        "errors": sorted(set(errors)),
        "state": "VERIFIED" if not errors else "FAILED",
        "claim_ceiling": result.get("claim_ceiling"),
        "promotion_allowed": False,
    }


def write_exclusive(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise VerificationError(f"refusing to overwrite {path}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--envelope", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = verify_envelope(args.envelope.expanduser().resolve(strict=True))
        if args.receipt is not None:
            write_exclusive(args.receipt.expanduser().absolute(), result)
    except (OSError, VerificationError, ValueError) as exc:
        result = {
            "schema": "constraintbox.attractor-basin-envelope-verification.v1",
            "state": "FAILED",
            "errors": [str(exc)],
            "promotion_allowed": False,
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
