#!/usr/bin/env python3
"""Validate a three-engine sim result envelope.

This checks the result-shape contract only. It does not prove the math.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    from audit_three_engine_source_claims import audit_engine
except Exception:  # pragma: no cover - optional stricter source gate.
    audit_engine = None


JULIA_ALIGNED = {
    "CliffordAlgebras",
    "Grassmann",
    "QuantumOptics",
    "QuantumClifford",
    "Manifolds",
    "Graphs",
    "Attractors",
    "DynamicalSystems",
    "Z3",
    "ITensors",
    "ITensorMPS",
    "ITensorNetworks",
    "DifferentialEquations",
    "TensorKit",
    "julia_gf4_stdlib",
}
JAX_ALIGNED = {
    "diffrax",
    "netket",
    "quimb",
    "quimb.tensor",
    "z3",
    "cvc5",
    "e3nn_jax",
    "ott",
    "jraph",
    "networkx",
    "qutip",
    "sympy",
    "jaxopt",
    "lineax",
    "galois",
    "gudhi",
    "toponetx",
}
PYTORCH_ALIGNED = {
    "clifford",
    "geomstats",
    "e3nn",
    "torch_ga",
    "kingdon",
    "torch_geometric",
    "torch.func",
    "functorch",
    "z3",
    "cvc5",
    "sympy",
}
CONTROL_ONLY = {"numpy", "scipy", "mpmath"}


class ValidationError(Exception):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _as_dict(value: Any, name: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{name} must be an object")
    return value


def _as_list(value: Any, name: str) -> list[Any]:
    _require(isinstance(value, list), f"{name} must be a list")
    return value


def _tool_set(record: dict[str, Any], key: str) -> set[str]:
    return {str(item) for item in _as_list(record.get(key), key)}


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _reject_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not permitted: {value}")


def _load_json_strict(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_object,
        parse_constant=_reject_non_finite_constant,
    )


def _validate_engine(name: str, record: dict[str, Any], aligned: set[str]) -> None:
    _require(record.get("ran") is True, f"{name}.ran must be true")
    _require(bool(record.get("source_path")), f"{name}.source_path is required")
    _require(record.get("reads_peer_result") is False, f"{name}.reads_peer_result must be false")
    packages_used = _tool_set(record, "packages_used")
    load_bearing = _tool_set(record, "aligned_packages_load_bearing")
    _require(packages_used, f"{name}.packages_used must be non-empty")
    _require(load_bearing, f"{name}.aligned_packages_load_bearing must be non-empty")
    _require(
        bool(load_bearing & aligned),
        f"{name} must have at least one aligned load-bearing package: {sorted(aligned)}",
    )
    _require(
        load_bearing <= packages_used,
        f"{name}.aligned_packages_load_bearing must be a subset of packages_used",
    )


def _validate_package_observables(name: str, record: dict[str, Any], load_bearing: set[str]) -> list[str]:
    errors: list[str] = []
    observables = record.get("package_observables")
    if not isinstance(observables, dict):
        return [f"{name}.package_observables is required for load-bearing packages"]
    for package in sorted(load_bearing):
        observable = observables.get(package)
        if not _non_empty_string(observable):
            errors.append(f"{name}.package_observables.{package} must name the exact observable")
    return errors


def _validate_tool_intent(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    tool_intent = payload.get("tool_intent")
    if tool_intent is None:
        return errors
    if audit_engine is None:
        return ["tool-intent audit unavailable: could not import audit_three_engine_source_claims.audit_engine"]
    try:
        intent = _as_dict(tool_intent, "tool_intent")
        claim_classes = _as_list(intent.get("claim_classes"), "tool_intent.claim_classes")
        if not claim_classes:
            errors.append("tool_intent.claim_classes must be non-empty")
        engine_tool_intent = _as_dict(intent.get("engine_tool_intent"), "tool_intent.engine_tool_intent")
        engines = _as_dict(payload.get("engines"), "engines")
    except ValidationError as exc:
        return [str(exc)]

    repo_root = Path(__file__).resolve().parents[1]
    for name, record_value in engines.items():
        if not isinstance(record_value, dict):
            errors.append(f"{name}: engine record must be an object for tool-intent audit")
            continue
        name = str(name)
        record = record_value
        load_bearing = _tool_set(record, "aligned_packages_load_bearing")
        if not load_bearing:
            continue
        errors.extend(_validate_package_observables(name, record, load_bearing))
        lane_intent = engine_tool_intent.get(name)
        if not isinstance(lane_intent, dict):
            errors.append(f"tool_intent.engine_tool_intent.{name} is required for load-bearing packages")
            continue
        for package in sorted(load_bearing):
            observable = lane_intent.get(package)
            if not _non_empty_string(observable):
                errors.append(f"tool_intent.engine_tool_intent.{name}.{package} must name the exact observable/proof")
        audit = audit_engine(name, record, repo_root)
        backed = set(audit.get("source_backed_load_bearing", {}))
        for package in sorted(load_bearing - backed):
            problems = "; ".join(str(p) for p in audit.get("problems", []))
            suffix = f": {problems}" if problems else ""
            errors.append(f"{name}.{package} tool_intent declared but source-token-thin/not-backed{suffix}")
    return errors


def _validate_crossover(payload: dict[str, Any]) -> None:
    proofs = _as_dict(payload.get("crossover_proofs"), "crossover_proofs")
    z3 = _as_dict(proofs.get("z3"), "crossover_proofs.z3")
    cvc5 = _as_dict(proofs.get("cvc5"), "crossover_proofs.cvc5")
    for name, record in (("z3", z3), ("cvc5", cvc5)):
        _require(record.get("ran") is True, f"{name}.ran must be true")
        _require(
            record.get("load_bearing") is True or record.get("supportive") is True,
            f"{name} must be load-bearing or explicitly supportive",
        )
        _require(record.get("verdict") in {"sat", "unsat"}, f"{name}.verdict must be sat or unsat")
    _require(z3["verdict"] == cvc5["verdict"], "z3 and cvc5 verdicts must agree")
    if "julia_z3" in proofs:
        julia_z3 = _as_dict(proofs["julia_z3"], "crossover_proofs.julia_z3")
        _require(julia_z3.get("ran") is True, "julia_z3.ran must be true when present")
        _require(julia_z3.get("verdict") in {"sat", "unsat"}, "julia_z3.verdict must be sat or unsat")


def _validate_source_backing(payload: dict[str, Any], *, strict: bool = False) -> list[str]:
    errors: list[str] = []
    if audit_engine is None:
        return ["source-backed audit unavailable: could not import audit_three_engine_source_claims.audit_engine"]
    repo_root = Path(__file__).resolve().parents[1]
    engines = _as_dict(payload.get("engines"), "engines")
    acceptable = {"source_backed_rich_tool_claim", "mixed_source_backed_with_thin_claims"}
    for name, record in engines.items():
        if not isinstance(record, dict):
            errors.append(f"{name}: engine record must be an object for source-backed audit")
            continue
        audit = audit_engine(str(name), record, repo_root)
        cls = audit.get("classification")
        if cls not in acceptable:
            problems = "; ".join(str(p) for p in audit.get("problems", []))
            errors.append(f"{name}: source-backed audit failed ({cls}): {problems}")
        elif strict and cls == "mixed_source_backed_with_thin_claims":
            problems = "; ".join(str(p) for p in audit.get("problems", []))
            errors.append(f"{name}: strict source-backed audit requires no thin declared claims: {problems}")
    return errors


def validate(
    payload: dict[str, Any],
    require_pytorch: bool = False,
    allow_canonical: bool = False,
    require_source_backed: bool = False,
    strict_source_backed: bool = False,
    require_tool_intent: bool = False,
) -> list[str]:
    errors: list[str] = []
    try:
        _require(payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version must be three_engine_sim_result_v1")
        if not allow_canonical:
            _require(payload.get("promotion_allowed") is False, "promotion_allowed must be false without --allow-canonical")
        engines = _as_dict(payload.get("engines"), "engines")
        _validate_engine("julia", _as_dict(engines.get("julia"), "engines.julia"), JULIA_ALIGNED)
        _validate_engine("jax", _as_dict(engines.get("jax"), "engines.jax"), JAX_ALIGNED)
        if require_pytorch:
            _validate_engine("pytorch", _as_dict(engines.get("pytorch"), "engines.pytorch"), PYTORCH_ALIGNED)
        elif "pytorch" in engines:
            _validate_engine("pytorch", _as_dict(engines["pytorch"], "engines.pytorch"), PYTORCH_ALIGNED)

        claim_path_tools = {str(item) for item in payload.get("claim_path_tools", [])}
        _require(not (claim_path_tools & CONTROL_ONLY), "control-only tools may not appear in claim_path_tools")
        _validate_crossover(payload)

        divergence = _as_dict(payload.get("divergence"), "divergence")
        engine_values = _as_dict(divergence.get("engine_values"), "divergence.engine_values")
        _require(divergence.get("julia_authoritative") is True, "divergence.julia_authoritative must be true")
        _require("julia" in engine_values and "jax" in engine_values, "engine_values must include julia and jax")
        _require("max_divergence" in divergence, "divergence.max_divergence is required")
        max_divergence = divergence.get("max_divergence")
        _require(
            type(max_divergence) is int
            or (type(max_divergence) is float and math.isfinite(max_divergence)),
            "divergence.max_divergence must be a finite number",
        )
        _require(
            max_divergence >= 0,
            "divergence.max_divergence must be nonnegative",
        )
    except ValidationError as exc:
        errors.append(str(exc))
    if require_source_backed or strict_source_backed:
        try:
            errors.extend(_validate_source_backing(payload, strict=strict_source_backed))
        except ValidationError as exc:
            errors.append(str(exc))
    if require_tool_intent:
        errors.extend(_validate_tool_intent(payload))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_json", type=Path)
    parser.add_argument("--require-pytorch", action="store_true")
    parser.add_argument("--allow-canonical", action="store_true")
    parser.add_argument(
        "--require-source-backed",
        action="store_true",
        help="Also read declared engine source files and require source-backed rich package evidence.",
    )
    parser.add_argument(
        "--strict-source-backed",
        action="store_true",
        help="Like --require-source-backed, but fail mixed/thin declared load-bearing claims too.",
    )
    parser.add_argument(
        "--require-tool-intent",
        action="store_true",
        help="When tool_intent is present, require load-bearing package intents, observables, and source-token backing.",
    )
    args = parser.parse_args()

    payload = _load_json_strict(args.result_json)
    if not isinstance(payload, dict):
        raise ValueError("result_json must contain a JSON object")
    errors = validate(
        payload,
        require_pytorch=args.require_pytorch,
        allow_canonical=args.allow_canonical,
        require_source_backed=args.require_source_backed,
        strict_source_backed=args.strict_source_backed,
        require_tool_intent=args.require_tool_intent,
    )
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "result_json": str(args.result_json)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
