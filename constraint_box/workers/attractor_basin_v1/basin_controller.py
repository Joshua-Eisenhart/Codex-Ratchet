#!/usr/bin/env python3
"""Deterministic controller for the bounded three-engine basin challenge.

The controller owns orchestration, validation, comparison, formal checks, and
the final claim ceiling.  JAX, Julia, and PyTorch remain independent external
simulation-evidence producers.  The SMT subprocess is a CB-owned finite gate
over the controller-built observation bundle; it is not a simulation engine.
No worker reads a peer receipt and no worker is allowed to admit its own result.

This file intentionally contains no installation-specific path.  Every
runtime, source root, and output root is supplied explicitly on the command
line.  The selected output directory must not already exist.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


CHALLENGE_ID = "cb_attractor_basin_three_engine_20260801"
OBJECT_CARD_NAME = "object_card.json"
MAP_FORMULA = "F_h(x,y)=(x-h*(x^3-x),0.5*y)"
EXPECTED_COUNTS = {"negative": 165, "boundary": 11, "positive": 165}
EXPECTED_RADII_TENTHS = [6, 12, 6]
EXPECTED_WRONG_RADII_TENTHS = [14, 8, 14]
EXPECTED_STEPS = 80
EXPECTED_GRID_SHAPE = [31, 11]
EXPECTED_GRID_POINTS = 341
ENGINE_NAMES = ("jax", "julia", "pytorch")
EXPECTED_ROLES = {
    "jax": "jax_batched_workhorse_sim_builder",
    "julia": "julia_authoritative_sim_builder",
    "pytorch": "external_sim_engine_evidence_producer",
}
CLAIM_CEILING = (
    "scratch diagnostic: two fresh runs of each bounded external simulation "
    "lane, two fresh runs of the CB-owned finite SMT checker, ConstraintBox "
    "formal profiles, and one retained "
    "Mini-Lev tool-to-gate flow; no continuous-basin proof, Julia Canon or CR "
    "admission, whole-estate claim, release promotion, or automatic tuning"
)


class ControllerError(RuntimeError):
    """A fail-closed controller validation or execution error."""


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ControllerError(f"value is not canonical JSON: {exc}") from exc


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        raise ControllerError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def _reject_nonfinite_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant {value!r}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(
            raw.decode("utf-8"), parse_constant=_reject_nonfinite_json_constant
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ControllerError(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ControllerError(f"JSON root at {path} is not an object")
    return value


def write_json_exclusive(path: Path, value: Any) -> None:
    payload = json.dumps(
        value,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    try:
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ControllerError(f"cannot retain {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ControllerError(message)


def require_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ControllerError(f"{path} must be an object")
    return value


def require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ControllerError(f"{path} must be an array")
    return value


def resolved_file(path: Path, label: str, *, executable: bool = False) -> Path:
    try:
        result = path.expanduser().resolve(strict=True)
    except OSError as exc:
        raise ControllerError(f"{label} does not resolve: {path}: {exc}") from exc
    require(result.is_file(), f"{label} is not a file: {result}")
    if executable:
        require(os.access(result, os.X_OK), f"{label} is not executable: {result}")
    return result


def executable_invocation(path: Path, label: str) -> tuple[Path, Path]:
    """Keep a venv/shim invocation path while separately pinning its target.

    Executing a resolved Python symlink can bypass the virtual-environment
    prefix that selected the installed package set.  The controller therefore
    invokes the explicit caller path and hashes/compares its resolved binary.
    """

    invocation = path.expanduser().absolute()
    try:
        identity = invocation.resolve(strict=True)
    except OSError as exc:
        raise ControllerError(f"{label} does not resolve: {path}: {exc}") from exc
    require(identity.is_file(), f"{label} is not a file: {identity}")
    require(os.access(invocation, os.X_OK), f"{label} is not executable: {invocation}")
    return invocation, identity


def resolved_directory(path: Path, label: str) -> Path:
    try:
        result = path.expanduser().resolve(strict=True)
    except OSError as exc:
        raise ControllerError(f"{label} does not resolve: {path}: {exc}") from exc
    require(result.is_dir(), f"{label} is not a directory: {result}")
    return result


def require_sha256(value: Any, path: str) -> str:
    require(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdefABCDEF" for character in value),
        f"{path} must be a SHA-256 hex string",
    )
    return value.lower()


def formula_key(value: Any, path: str) -> str:
    require(isinstance(value, str), f"{path} must be a string")
    normalized = "".join(value.split())
    require(normalized == MAP_FORMULA, f"{path} does not match the fixed map")
    return MAP_FORMULA


def tenths(values: Any, path: str) -> list[int]:
    raw = require_list(values, path)
    require(len(raw) == 3, f"{path} must contain three radii")
    result: list[int] = []
    for index, value in enumerate(raw):
        require(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value)),
            f"{path}[{index}] must be finite numeric",
        )
        scaled = float(value) * 10.0
        rounded = round(scaled)
        require(
            abs(scaled - rounded) <= 1.0e-8,
            f"{path}[{index}] is not an exact tenth",
        )
        result.append(int(rounded))
    return result


def require_counts(value: Any, path: str, *, torch_labels: bool = False) -> dict[str, int]:
    raw = require_dict(value, path)
    if torch_labels:
        expected_keys = {"-1", "0", "1", "99"}
        require(set(raw) == expected_keys, f"{path} label keys mismatch")
        require(raw["99"] == 0, f"{path} has invalid/out-of-bound nominal labels")
        counts = {
            "negative": raw["-1"],
            "boundary": raw["0"],
            "positive": raw["1"],
        }
    else:
        require(set(raw) == set(EXPECTED_COUNTS), f"{path} keys mismatch")
        counts = dict(raw)
    require(
        all(isinstance(item, int) and not isinstance(item, bool) for item in counts.values()),
        f"{path} counts must be integers",
    )
    require(counts == EXPECTED_COUNTS, f"{path} != {EXPECTED_COUNTS}")
    return counts


def require_controls_true(values: dict[str, Any], key: str) -> None:
    record = require_dict(values.get(key), f"controls.{key}")
    observed = record.get("observed", record.get("passed", record.get("caught")))
    require(observed is True, f"controls.{key} did not pass")


def command_receipt(
    *,
    command: list[str],
    cwd: Path,
    output_dir: Path,
    environment: dict[str, str],
    expected_returncode: int = 0,
    required_stderr_substring: str | None = None,
) -> dict[str, Any]:
    require(not output_dir.exists(), f"worker output lane already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=600,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ControllerError(f"worker subprocess failed to execute: {command[0]}: {exc}") from exc
    receipt = {
        "schema": "cb_attractor_basin_subprocess_receipt_v1",
        "argv": command,
        "cwd": str(cwd),
        "executable_sha256": sha256_file(Path(command[0]).resolve()),
        "returncode": completed.returncode,
        "stdout": completed.stdout.decode("utf-8", errors="replace"),
        "stderr": completed.stderr.decode("utf-8", errors="replace"),
        "output_dir": str(output_dir),
        "expected_returncode": expected_returncode,
        "required_stderr_substring": required_stderr_substring,
    }
    write_json_exclusive(output_dir.parent / f"{output_dir.name}_subprocess.json", receipt)
    require(
        completed.returncode == expected_returncode,
        f"worker returned {completed.returncode}, expected {expected_returncode}: {command[0]}: "
        f"{receipt['stderr'][-1000:]}",
    )
    if required_stderr_substring is not None:
        require(
            required_stderr_substring in receipt["stderr"],
            f"worker stderr omitted required marker {required_stderr_substring!r}",
        )
    require(output_dir.is_dir(), f"worker did not create output lane: {output_dir}")
    return receipt


def _tool_api_values(rows: Any, path: str) -> list[str]:
    values: list[str] = []
    for index, row_value in enumerate(require_list(rows, path)):
        row = require_dict(row_value, f"{path}[{index}]")
        api = row.get("qualified_api/function", row.get("qualified_api"))
        require(isinstance(api, str) and api, f"{path}[{index}] has no actual API")
        values.append(api)
    require(values, f"{path} must not be empty")
    return values


def normalize_jax(
    receipt: dict[str, Any], *, source_path: Path, python_runtime: Path, receipt_path: Path
) -> dict[str, Any]:
    require(receipt.get("schema_version") == "three_engine_sim_engine_fragment_v1", "JAX schema mismatch")
    require(receipt.get("engine") == "jax", "JAX engine mismatch")
    require(receipt.get("role_id") == EXPECTED_ROLES["jax"], "JAX role mismatch")
    source_sha256 = sha256_file(source_path)
    require(receipt.get("source_sha256") == source_sha256, "JAX source hash mismatch")
    runtime = require_dict(receipt.get("runtime_manifest"), "JAX runtime_manifest")
    require(runtime.get("python_executable_sha256") == sha256_file(python_runtime), "JAX Python runtime hash mismatch")
    require(runtime.get("jax_enable_x64") is True, "JAX x64 was not enabled")
    manifest_sha256 = sha256_bytes(canonical_json_bytes(runtime))
    require(receipt.get("runtime_manifest_sha256") == manifest_sha256, "JAX runtime manifest hash mismatch")

    claim = require_dict(receipt.get("claim"), "JAX claim")
    formula_key(claim.get("map"), "JAX claim.map")
    require(claim.get("h") == 0.2, "JAX nominal h mismatch")
    require(claim.get("steps") == EXPECTED_STEPS, "JAX step count mismatch")
    require(claim.get("dtype") == "float64", "JAX dtype mismatch")
    grid = require_dict(claim.get("grid"), "JAX grid")
    require(grid == {"x": "-1.5:0.1:1.5", "y": "-0.5:0.1:0.5", "points": 341}, "JAX grid mismatch")
    result = require_dict(receipt.get("result"), "JAX result")
    counts = require_counts(result.get("partition_counts"), "JAX partition_counts")
    radii = tenths(result.get("fixed_point_spectral_radii"), "JAX nominal radii")
    require(radii == EXPECTED_RADII_TENTHS, "JAX nominal radii mismatch")
    controls = require_dict(receipt.get("controls"), "JAX controls")
    wrong = require_dict(controls.get("wrong_sign_h"), "JAX wrong_sign_h")
    require(wrong.get("h") == -0.2 and wrong.get("caught") is True, "JAX wrong-sign control failed")
    wrong_radii = tenths(wrong.get("fixed_point_spectral_radii"), "JAX wrong radii")
    require(wrong_radii == EXPECTED_WRONG_RADII_TENTHS, "JAX wrong radii mismatch")
    require_controls_true(controls, "erased_labels")
    require_controls_true(controls, "boundary")
    replay = require_dict(controls.get("replay"), "JAX replay")
    require(replay.get("direct_exact_match") is True and replay.get("diffrax_exact_match") is True, "JAX replay failed")
    diffrax_requirement = require_dict(
        controls.get("diffrax_operation_requirement"),
        "JAX Diffrax operation requirement",
    )
    require(
        diffrax_requirement.get("diffrax_value_gate_passed") is True
        and diffrax_requirement.get("requires_controller_operation_poison") is True
        and diffrax_requirement.get("controller_poison_environment_key")
        == "CONSTRAINTBOX_TEST_SEVER_DIFFRAX",
        "JAX Diffrax operation requirement was not retained",
    )
    require(receipt.get("all_pass") is True and receipt.get("exit_code") == 0, "JAX lane did not pass")
    require(receipt.get("reads_peer_result") is False, "JAX read a peer result")
    require(receipt.get("claim_path_host_copy") is False, "JAX used a host-copy claim path")
    require(receipt.get("promotion_allowed") is False, "JAX self-promoted")
    require(receipt.get("formal_admission_allowed") is False, "JAX self-admitted formally")
    require(receipt.get("continuous_basin_proof") is False, "JAX claimed a continuous proof")
    require(receipt.get("admission_decision") is None, "JAX made an admission decision")
    apis = _tool_api_values(receipt.get("tool_calls"), "JAX tool_calls")
    for required_api in (
        "jax.jit(jax.vmap(iterate_one))",
        "jax.jacrev(step_map)",
        "jax.grad(potential)",
    ):
        require(required_api in apis, f"JAX missing load-bearing API {required_api}")
    require(any(api.startswith("diffrax.diffeqsolve") for api in apis), "JAX missing Diffrax operation")
    depth = require_dict(receipt.get("tool_integration_depth"), "JAX integration depth")
    require(depth.get("jax") == "claim_load_bearing" and depth.get("diffrax") == "claim_load_bearing", "JAX/Diffrax are not load-bearing")

    projection_record = require_dict(receipt.get("semantic_replay"), "JAX semantic_replay")
    semantic_body = {
        key: value
        for key, value in receipt.items()
        if key not in {"run_instance", "runtime_manifest", "runtime_manifest_sha256", "semantic_replay"}
    }
    require(
        projection_record.get("projection_sha256") == sha256_bytes(canonical_json_bytes(semantic_body)),
        "JAX semantic projection hash is invalid",
    )
    return {
        "engine": "jax",
        "role": receipt["role_id"],
        "source_sha256": source_sha256,
        "runtime_executable_sha256": sha256_file(python_runtime),
        "runtime_manifest_sha256": manifest_sha256,
        "receipt_sha256": sha256_file(receipt_path),
        "semantic_replay_sha256": projection_record["projection_sha256"],
        "map": MAP_FORMULA,
        "h": 0.2,
        "wrong_h": -0.2,
        "steps": EXPECTED_STEPS,
        "grid_shape": EXPECTED_GRID_SHAPE,
        "partition_counts": counts,
        "fixed_point_spectral_radii_tenths": radii,
        "wrong_fixed_point_spectral_radii_tenths": wrong_radii,
        "radii_evidence": "JAX jacrev Jacobians followed by eigvals",
        "actual_apis": apis,
        "package_versions": receipt.get("package_versions"),
        "all_controls_passed": True,
        "reads_peer_result": False,
        "self_admission": False,
    }


def normalize_julia(
    receipt: dict[str, Any], *, source_path: Path, julia_runtime: Path, julia_project_file: Path, receipt_path: Path
) -> dict[str, Any]:
    require(receipt.get("schema_version") == "cb_attractor_basin_three_engine.julia.v1", "Julia schema mismatch")
    require(receipt.get("role_id") == EXPECTED_ROLES["julia"], "Julia role mismatch")
    require(receipt.get("worker_status") == "raw_execution_complete", "Julia worker status mismatch")
    source = require_dict(receipt.get("source"), "Julia source")
    source_sha256 = sha256_file(source_path)
    require(source.get("sha256") == source_sha256, "Julia source hash mismatch")
    runtime = require_dict(receipt.get("runtime"), "Julia runtime")
    require(Path(str(runtime.get("julia_executable"))).resolve() == julia_runtime, "Julia executable mismatch")
    require(Path(str(runtime.get("active_project"))).resolve() == julia_project_file, "Julia active project mismatch")
    require(runtime.get("active_project_sha256") == sha256_file(julia_project_file), "Julia project hash mismatch")
    manifest_path = julia_project_file.parent / "Manifest.toml"
    require(manifest_path.is_file(), "Julia Manifest.toml is missing")
    require(Path(str(runtime.get("manifest_path"))).resolve() == manifest_path.resolve(), "Julia manifest path mismatch")
    require(runtime.get("manifest_sha256") == sha256_file(manifest_path), "Julia manifest hash mismatch")

    challenge = require_dict(receipt.get("fixed_challenge"), "Julia fixed_challenge")
    formula_key(challenge.get("equation"), "Julia equation")
    require(challenge.get("nominal_h") == 0.2 and challenge.get("wrong_sign_h") == -0.2, "Julia h mismatch")
    require(challenge.get("steps") == EXPECTED_STEPS and challenge.get("float_type") == "Float64", "Julia steps/dtype mismatch")
    grid = require_dict(challenge.get("grid"), "Julia grid")
    require(grid.get("grid_point_count") == EXPECTED_GRID_POINTS and grid.get("shape") == EXPECTED_GRID_SHAPE, "Julia grid mismatch")
    measurements = require_dict(receipt.get("measurements"), "Julia measurements")
    counts = require_counts(measurements.get("terminal_sign_label_counts"), "Julia terminal counts")
    require(measurements.get("nominal_terminal_mismatch_count") == 0, "Julia Attractors/sign partition mismatch")
    controls = require_dict(receipt.get("controls"), "Julia controls")
    for name in ("positive", "wrong_sign", "erased_positive_attractor", "boundary", "replay", "severance"):
        require_controls_true(controls, name)
    wrong = require_dict(controls.get("wrong_sign"), "Julia wrong_sign")
    derivatives = require_dict(wrong.get("abs_x_derivative"), "Julia derivative controls")
    radii = tenths(
        [
            max(float(derivatives.get("nominal_at_plus_minus_one")), 0.5),
            max(float(derivatives.get("nominal_at_origin")), 0.5),
            max(float(derivatives.get("nominal_at_plus_minus_one")), 0.5),
        ],
        "Julia nominal radii",
    )
    wrong_radii = tenths(
        [
            max(float(derivatives.get("wrong_sign_at_plus_minus_one")), 0.5),
            max(float(derivatives.get("wrong_sign_at_origin")), 0.5),
            max(float(derivatives.get("wrong_sign_at_plus_minus_one")), 0.5),
        ],
        "Julia wrong radii",
    )
    require(radii == EXPECTED_RADII_TENTHS, "Julia nominal radii mismatch")
    require(wrong_radii == EXPECTED_WRONG_RADII_TENTHS, "Julia wrong radii mismatch")
    severance = require_dict(controls.get("severance"), "Julia severance")
    require(severance.get("reads_peer_result") is False and severance.get("peer_result_paths") == [], "Julia peer-read boundary failed")
    execution = require_dict(receipt.get("execution"), "Julia execution")
    require(execution.get("reads_peer_result") is False and execution.get("cross_engine_result_comparison") is False, "Julia compared peer results")
    require(receipt.get("promotion_allowed") is False, "Julia self-promoted")
    require(receipt.get("formal_admission_allowed") is False, "Julia self-admitted formally")
    require(receipt.get("scientific_admission_allowed") is False, "Julia self-admitted scientifically")
    apis = require_list(receipt.get("actual_apis"), "Julia actual_apis")
    require(all(isinstance(api, str) and api for api in apis), "Julia actual_apis invalid")
    for required_api in (
        "Attractors.DynamicalSystemsBase.DeterministicIteratedMap",
        "Attractors.AttractorsViaProximity",
        "Attractors.basins_of_attraction",
    ):
        require(required_api in apis, f"Julia missing load-bearing API {required_api}")
    normalized = {
        "engine": "julia",
        "role": receipt["role_id"],
        "source_sha256": source_sha256,
        "runtime_executable_sha256": sha256_file(julia_runtime),
        "project_sha256": sha256_file(julia_project_file),
        "manifest_sha256": sha256_file(manifest_path),
        "receipt_sha256": sha256_file(receipt_path),
        "map": MAP_FORMULA,
        "h": 0.2,
        "wrong_h": -0.2,
        "steps": EXPECTED_STEPS,
        "grid_shape": EXPECTED_GRID_SHAPE,
        "partition_counts": counts,
        "fixed_point_spectral_radii_tenths": radii,
        "wrong_fixed_point_spectral_radii_tenths": wrong_radii,
        "radii_evidence": (
            "Julia analytic derivative of the fixed map combined with the "
            "declared y contraction; Attractors supplies the basin partition"
        ),
        "actual_apis": list(apis),
        "package_versions": {
            name: require_dict(value, f"Julia packages.{name}").get("version")
            for name, value in require_dict(receipt.get("packages"), "Julia packages").items()
        },
        "all_controls_passed": True,
        "reads_peer_result": False,
        "self_admission": False,
    }
    normalized["semantic_replay_sha256"] = sha256_bytes(
        canonical_json_bytes({key: value for key, value in normalized.items() if key != "receipt_sha256"})
    )
    return normalized


def normalize_torch(
    receipt: dict[str, Any], *, source_path: Path, python_runtime: Path, receipt_path: Path
) -> dict[str, Any]:
    require(receipt.get("schema") == "constraintbox.external-sim.pytorch-basin-receipt.v1", "PyTorch schema mismatch")
    producer = require_dict(receipt.get("producer"), "PyTorch producer")
    require(producer.get("engine") == "pytorch" and producer.get("engine_role") == EXPECTED_ROLES["pytorch"], "PyTorch role mismatch")
    source_sha256 = sha256_file(source_path)
    require(producer.get("source_sha256") == source_sha256, "PyTorch source hash mismatch")
    runtime = require_dict(receipt.get("runtime"), "PyTorch runtime")
    runtime_python = require_dict(runtime.get("python"), "PyTorch runtime.python")
    require(Path(str(runtime_python.get("executable_resolved"))).resolve() == python_runtime, "PyTorch Python runtime mismatch")
    type_contract = require_dict(receipt.get("type_contract"), "PyTorch type_contract")
    require(type_contract.get("state_dtype") == "torch.float64" and type_contract.get("device") == "cpu", "PyTorch type/device mismatch")
    require(type_contract.get("forbidden_claim_path_bridges_used") == [], "PyTorch used a forbidden claim-path bridge")
    mapping = require_dict(receipt.get("mathematical_map"), "PyTorch mathematical_map")
    formula_key(mapping.get("formula"), "PyTorch formula")
    require(mapping.get("positive_h") == 0.2 and mapping.get("wrong_control_h") == -0.2, "PyTorch h mismatch")
    require(mapping.get("steps") == EXPECTED_STEPS, "PyTorch steps mismatch")
    measurements = require_dict(receipt.get("measurements"), "PyTorch measurements")
    grid = require_dict(measurements.get("initial_grid"), "PyTorch initial_grid")
    require(grid.get("state_count") == EXPECTED_GRID_POINTS, "PyTorch grid point count mismatch")
    positive = require_dict(measurements.get("positive"), "PyTorch positive")
    counts = require_counts(positive.get("label_counts"), "PyTorch nominal counts", torch_labels=True)
    radii = tenths(positive.get("fixed_point_spectral_radii"), "PyTorch nominal radii")
    require(radii == EXPECTED_RADII_TENTHS, "PyTorch nominal radii mismatch")
    wrong = require_dict(measurements.get("wrong"), "PyTorch wrong")
    wrong_radii = tenths(wrong.get("fixed_point_spectral_radii"), "PyTorch wrong radii")
    require(wrong_radii == EXPECTED_WRONG_RADII_TENTHS, "PyTorch wrong radii mismatch")
    controls = require_dict(receipt.get("controls"), "PyTorch controls")
    for name, value in controls.items():
        require(require_dict(value, f"PyTorch controls.{name}").get("passed") is True, f"PyTorch control {name} failed")
    require(receipt.get("all_required_controls_passed") is True, "PyTorch controls did not all pass")
    graph = require_dict(measurements.get("graph_diagnostic"), "PyTorch graph diagnostic")
    require(graph.get("severance_detected") is True, "PyG severance was not detected")
    training = require_dict(measurements.get("training_diagnostic"), "PyTorch training diagnostic")
    require(set(training) == {"positive_internal_labels", "permuted_internal_labels"}, "PyTorch training controls missing")
    require(producer.get("reads_peer_result") is False and producer.get("peer_result_paths_read") == [], "PyTorch read a peer result")
    admission = require_dict(receipt.get("admission"), "PyTorch admission")
    require(admission.get("producer_made_admission_decision") is False and admission.get("promotion_allowed") is False, "PyTorch self-admitted")
    apis = require_list(receipt.get("actual_api_calls"), "PyTorch actual_api_calls")
    for required_api in (
        "torch.func.vmap",
        "torch.func.jacrev",
        "torch_geometric.nn.MessagePassing.propagate",
        "torch.optim.Adam.step",
    ):
        require(required_api in apis, f"PyTorch missing load-bearing API {required_api}")
    hashes = require_dict(receipt.get("hashes"), "PyTorch hashes")
    require(hashes.get("source_sha256") == source_sha256, "PyTorch repeated source hash mismatch")
    semantic_sha256 = require_sha256(hashes.get("path_independent_semantic_replay_sha256"), "PyTorch semantic replay hash")
    require(
        semantic_sha256 == hashes.get("first_run_signature_sha256") == hashes.get("replay_run_signature_sha256"),
        "PyTorch internal replay signatures disagree",
    )
    body = {key: value for key, value in receipt.items() if key != "hashes"}
    require(hashes.get("receipt_body_sha256") == sha256_bytes(canonical_json_bytes(body)), "PyTorch receipt body hash mismatch")
    sidecar = receipt_path.with_suffix(".sha256")
    require(sidecar.is_file(), "PyTorch receipt sidecar missing")
    sidecar_parts = sidecar.read_text(encoding="utf-8").strip().split()
    require(sidecar_parts and sidecar_parts[0] == sha256_file(receipt_path), "PyTorch receipt sidecar mismatch")
    return {
        "engine": "pytorch",
        "role": producer["engine_role"],
        "source_sha256": source_sha256,
        "runtime_executable_sha256": sha256_file(python_runtime),
        "receipt_sha256": sha256_file(receipt_path),
        "semantic_replay_sha256": semantic_sha256,
        "map": MAP_FORMULA,
        "h": 0.2,
        "wrong_h": -0.2,
        "steps": EXPECTED_STEPS,
        "grid_shape": EXPECTED_GRID_SHAPE,
        "partition_counts": counts,
        "fixed_point_spectral_radii_tenths": radii,
        "wrong_fixed_point_spectral_radii_tenths": wrong_radii,
        "radii_evidence": "PyTorch jacrev Jacobians followed by eigvals",
        "actual_apis": list(apis),
        "package_versions": {
            "torch": require_dict(runtime.get("torch"), "PyTorch runtime.torch").get("version"),
            "torch_geometric": require_dict(runtime.get("torch_geometric"), "PyTorch runtime.torch_geometric").get("version"),
        },
        "all_controls_passed": True,
        "reads_peer_result": False,
        "self_admission": False,
    }


def replay_projection(normalized: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in normalized.items()
        if key not in {"receipt_sha256"}
    }


def validate_engine_set(
    engines: dict[str, dict[str, Any]], expected_source_hashes: dict[str, str]
) -> list[str]:
    errors: list[str] = []
    if set(engines) != set(ENGINE_NAMES):
        errors.append("required_engine_lane_set_mismatch")
    for name in ENGINE_NAMES:
        engine = engines.get(name)
        if not isinstance(engine, dict):
            continue
        if engine.get("engine") != name:
            errors.append(f"{name}:engine_identity_mismatch")
        if engine.get("role") != EXPECTED_ROLES[name]:
            errors.append(f"{name}:role_mismatch")
        if engine.get("source_sha256") != expected_source_hashes[name]:
            errors.append(f"{name}:source_provenance_mismatch")
        if engine.get("map") != MAP_FORMULA:
            errors.append(f"{name}:map_mismatch")
        if engine.get("steps") != EXPECTED_STEPS:
            errors.append(f"{name}:step_count_mismatch")
        if engine.get("grid_shape") != EXPECTED_GRID_SHAPE:
            errors.append(f"{name}:grid_shape_mismatch")
        if engine.get("partition_counts") != EXPECTED_COUNTS:
            errors.append(f"{name}:partition_counts_mismatch")
        if engine.get("fixed_point_spectral_radii_tenths") != EXPECTED_RADII_TENTHS:
            errors.append(f"{name}:nominal_radii_mismatch")
        if engine.get("wrong_fixed_point_spectral_radii_tenths") != EXPECTED_WRONG_RADII_TENTHS:
            errors.append(f"{name}:wrong_radii_mismatch")
        if engine.get("all_controls_passed") is not True:
            errors.append(f"{name}:controls_not_passed")
        if engine.get("reads_peer_result") is not False:
            errors.append(f"{name}:peer_read_detected")
        if engine.get("self_admission") is not False:
            errors.append(f"{name}:self_admission_detected")
    return sorted(errors)


def build_observation_bundle(engines: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "cb_attractor_basin_observations_v1",
        "map": {
            "formula": MAP_FORMULA,
            "h_numerator": 1,
            "h_denominator": 5,
            "steps": EXPECTED_STEPS,
            "grid_shape": EXPECTED_GRID_SHAPE,
        },
        "engines": {
            name: {
                "partition_counts": engines[name]["partition_counts"],
                "fixed_point_spectral_radii_tenths": engines[name][
                    "fixed_point_spectral_radii_tenths"
                ],
                "wrong_fixed_point_spectral_radii_tenths": engines[name][
                    "wrong_fixed_point_spectral_radii_tenths"
                ],
                "all_controls_passed": engines[name]["all_controls_passed"],
                "source_sha256": engines[name]["source_sha256"],
                "receipt_sha256": engines[name]["receipt_sha256"],
            }
            for name in ENGINE_NAMES
        },
        "controller": {"validated_receipts": True, "roles_separated": True},
    }


def normalize_smt(
    receipt: dict[str, Any], *, source_path: Path, python_runtime: Path, bundle: dict[str, Any], receipt_path: Path
) -> dict[str, Any]:
    require(receipt.get("schema_version") == "cb_attractor_basin_smt_receipt.v1", "SMT schema mismatch")
    require(receipt.get("role_id") == "smt_crossover_proof_engineer", "SMT role mismatch")
    require(receipt.get("worker_status") == "raw_execution_complete", "SMT worker status mismatch")
    source = require_dict(receipt.get("source"), "SMT source")
    source_sha256 = sha256_file(source_path)
    require(source.get("sha256") == source_sha256, "SMT source hash mismatch")
    runtime = require_dict(receipt.get("runtime"), "SMT runtime")
    require(Path(str(runtime.get("python_executable"))).resolve() == python_runtime, "SMT Python runtime mismatch")
    input_record = require_dict(receipt.get("input"), "SMT input")
    bundle_sha256 = sha256_bytes(canonical_json_bytes(bundle))
    require(input_record.get("canonical_bundle_sha256") == bundle_sha256, "SMT canonical input hash mismatch")
    require(input_record.get("reads_raw_peer_receipt_paths") is False, "SMT read raw peer receipts")
    require(receipt.get("observation_bundle") == bundle, "SMT echoed observation bundle mismatch")
    require(receipt.get("continuous_basin_proof") is False, "SMT claimed continuous proof")
    require(receipt.get("promotion_allowed") is False, "SMT self-promoted")
    require(receipt.get("formal_admission_allowed") is False and receipt.get("scientific_admission_allowed") is False, "SMT self-admitted")
    controls = require_dict(receipt.get("controls"), "SMT controls")
    for name in ("positive", "contradictory_label", "erased_label", "wrong_sign_stability", "operation_severance"):
        require_controls_true(controls, name)
    solvers = require_dict(receipt.get("solvers"), "SMT solvers")
    for solver_name in ("z3", "cvc5"):
        solver = require_dict(solvers.get(solver_name), f"SMT {solver_name}")
        require(require_dict(solver.get("positive"), f"SMT {solver_name}.positive").get("verdict") == "sat", f"SMT {solver_name} positive was not SAT")
        solver_controls = require_dict(solver.get("controls"), f"SMT {solver_name}.controls")
        for control_name in ("contradictory_label", "erased_label", "wrong_sign_stability"):
            control = require_dict(solver_controls.get(control_name), f"SMT {solver_name}.{control_name}")
            require(control.get("verdict") == "unsat" and control.get("core_contains_control_assumption") is True, f"SMT {solver_name} did not retain the {control_name} UNSAT assumption")
    enumeration = require_dict(receipt.get("independent_enumeration"), "SMT enumeration")
    require(enumeration.get("positive_observed") is True, "SMT CPython enumeration failed")
    apis = require_dict(receipt.get("actual_apis"), "SMT actual_apis")
    require(set(apis) == {"z3", "cvc5", "cpython_stdlib"}, "SMT actual API groups mismatch")
    normalized = {
        "role": receipt["role_id"],
        "source_sha256": source_sha256,
        "runtime_executable_sha256": sha256_file(python_runtime),
        "receipt_sha256": sha256_file(receipt_path),
        "bundle_sha256": bundle_sha256,
        "observation_bundle": receipt["observation_bundle"],
        "actual_apis": apis,
        "solvers": solvers,
        "independent_enumeration": enumeration,
        "controls": controls,
        "all_controls_passed": True,
        "reads_peer_result": False,
        "self_admission": False,
        "continuous_basin_proof": False,
    }
    normalized["semantic_replay_sha256"] = sha256_bytes(
        canonical_json_bytes({key: value for key, value in normalized.items() if key != "receipt_sha256"})
    )
    return normalized


def run_formal_profiles(
    *, output_root: Path, constraintbox_root: Path, controller_source: Path
) -> dict[str, Any]:
    source_root = constraintbox_root / "src"
    require((source_root / "constraintbox").is_dir(), "ConstraintBox src package missing")
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    try:
        from constraintbox.boundary_contract import (
            CB_EXTERNAL_ADAPTER_IDS,
            CB_FORMAL_GATE_IDS,
            CB_MINILEV_IDS,
            CB_RUNTIME_IDS,
            EXTERNAL_FORMAL_RUNTIME_IDS,
            EXTERNAL_SIM_PROFILE_IDS,
            TASK_BOUNDARY_CONTRACT,
        )
        from constraintbox.formal_registry import (
            TASK_SYMBOLIC_POLYNOMIAL,
            TASK_WORKFLOW_GRAPH,
            run_formal_task,
        )
    except Exception as exc:
        raise ControllerError(f"cannot import ConstraintBox formal APIs: {exc}") from exc

    workflow_nodes = sorted(
        [
            "engine_jax",
            "engine_julia",
            "engine_pytorch",
            "intake",
            "observations_bundle",
            "proposal_ready",
            "smt_gate",
        ]
    )
    workflow_edges = sorted(
        [
            ["engine_jax", "observations_bundle"],
            ["engine_julia", "observations_bundle"],
            ["engine_pytorch", "observations_bundle"],
            ["intake", "engine_jax"],
            ["intake", "engine_julia"],
            ["intake", "engine_pytorch"],
            ["observations_bundle", "smt_gate"],
            ["smt_gate", "proposal_ready"],
        ]
    )
    valid_workflow = {"nodes": workflow_nodes, "edges": workflow_edges}
    cyclic_workflow = {
        "nodes": workflow_nodes,
        "edges": sorted(workflow_edges + [["proposal_ready", "intake"]]),
    }
    skipped_workflow = {
        "nodes": workflow_nodes,
        "edges": sorted(
            [edge for edge in workflow_edges if edge[0] != "intake"]
        ),
    }
    polynomial = {
        "coefficients": [
            {"degree": 1, "numerator": -1, "denominator": 1},
            {"degree": 3, "numerator": 1, "denominator": 1},
        ],
        "claimed_canonical": [
            {"degree": 1, "numerator": -1, "denominator": 1},
            {"degree": 3, "numerator": 1, "denominator": 1},
        ],
    }
    valid_boundary = {
        "bundle_contains_external_sim_engines": False,
        "cb_external_adapter_ids": list(CB_EXTERNAL_ADAPTER_IDS),
        "cb_formal_gate_ids": list(CB_FORMAL_GATE_IDS),
        "cb_minilev_ids": list(CB_MINILEV_IDS),
        "cb_runtime_ids": list(CB_RUNTIME_IDS),
        "evidence_receipt_ids": ["evidence:cb-attractor-basin-three-engine-20260801"],
        "evidence_receipts_are_cb_core_components": False,
        "external_formal_runtime_ids": list(EXTERNAL_FORMAL_RUNTIME_IDS),
        "external_sim_profile_ids": list(EXTERNAL_SIM_PROFILE_IDS),
        "external_sim_profiles_are_cb_core": False,
        "report_kind": "constraintbox.product-evidence-status.v1",
        "schema": "constraintbox.boundary-contract.v1",
        "untrusted_llm_role": "proposal_or_advisory_only",
    }
    conflated_boundary = copy.deepcopy(valid_boundary)
    conflated_boundary["cb_formal_gate_ids"] = sorted(
        list(CB_FORMAL_GATE_IDS) + ["sim:pytorch-jacobian-v1"]
    )
    conflated_boundary["external_sim_profiles_are_cb_core"] = True

    cases: list[tuple[str, str, dict[str, Any], str, str]] = [
        ("workflow_valid", TASK_WORKFLOW_GRAPH, valid_workflow, "ELIGIBLE", "workflow_graph_obligations_satisfied"),
        ("workflow_cycle", TASK_WORKFLOW_GRAPH, cyclic_workflow, "BLOCKED", "workflow_graph_cycle_detected"),
        ("workflow_skipped_prerequisite", TASK_WORKFLOW_GRAPH, skipped_workflow, "BLOCKED", "workflow_graph_required_reachability_missing"),
        ("symbolic_x3_minus_x", TASK_SYMBOLIC_POLYNOMIAL, polynomial, "ELIGIBLE", "exact_polynomial_recomputed"),
        ("boundary_valid", TASK_BOUNDARY_CONTRACT, valid_boundary, "ELIGIBLE", "boundary_contract_roles_separated"),
        ("boundary_role_conflation", TASK_BOUNDARY_CONTRACT, conflated_boundary, "BLOCKED", "boundary_role_conflation"),
    ]
    summary: dict[str, Any] = {}
    formal_root = output_root / "formal"
    formal_root.mkdir(parents=True, exist_ok=False)
    for case_name, task_kind, payload, expected_disposition, expected_reason in cases:
        run_root = formal_root / case_name
        run_root.mkdir()
        decision = run_formal_task(
            task_kind=task_kind,
            request_id=f"cb-basin-{case_name}",
            payload=canonical_json_bytes(payload),
            run_root=run_root.resolve(),
        )
        decision_dict = decision.to_dict()
        require(decision_dict.get("disposition") == expected_disposition, f"formal case {case_name} disposition mismatch")
        require(decision_dict.get("reason") == expected_reason, f"formal case {case_name} reason mismatch: {decision_dict.get('reason')}")
        require(decision_dict.get("promotion_allowed") is False, f"formal case {case_name} self-promoted")
        flow_receipt_path = run_root / "formal_flow_receipt.json"
        flow_ledger_path = run_root / "formal_flow_events.jsonl"
        require(flow_receipt_path.is_file() and flow_ledger_path.is_file(), f"formal case {case_name} did not retain Mini-Lev evidence")
        summary[case_name] = {
            "decision": decision_dict,
            "payload_sha256": sha256_bytes(canonical_json_bytes(payload)),
            "flow_receipt_sha256": sha256_file(flow_receipt_path),
            "flow_ledger_sha256": sha256_file(flow_ledger_path),
            "run_root": str(run_root),
        }
    summary["controller_source_sha256"] = sha256_file(controller_source)
    return summary


def run_adversarial_controls(
    *,
    engines: dict[str, dict[str, Any]],
    expected_source_hashes: dict[str, str],
    formal: dict[str, Any],
    diffrax_operation_severance: dict[str, Any],
) -> dict[str, Any]:
    controls: dict[str, Any] = {}

    mutated_counts = copy.deepcopy(engines)
    mutated_counts["jax"]["partition_counts"]["positive"] = 166
    errors = validate_engine_set(mutated_counts, expected_source_hashes)
    controls["mutated_counts"] = {
        "caught": "jax:partition_counts_mismatch" in errors,
        "errors": errors,
    }

    erased_labels = copy.deepcopy(engines)
    erased_labels["julia"]["partition_counts"]["positive"] = 0
    errors = validate_engine_set(erased_labels, expected_source_hashes)
    controls["erased_labels"] = {
        "caught": "julia:partition_counts_mismatch" in errors,
        "errors": errors,
    }

    wrong_provenance = copy.deepcopy(engines)
    wrong_provenance["pytorch"]["source_sha256"] = "0" * 64
    errors = validate_engine_set(wrong_provenance, expected_source_hashes)
    controls["wrong_provenance"] = {
        "caught": "pytorch:source_provenance_mismatch" in errors,
        "errors": errors,
    }

    missing_lane = copy.deepcopy(engines)
    del missing_lane["pytorch"]
    errors = validate_engine_set(missing_lane, expected_source_hashes)
    controls["missing_lane"] = {
        "caught": "required_engine_lane_set_mismatch" in errors,
        "errors": errors,
    }

    role_conflation = copy.deepcopy(engines)
    role_conflation["jax"]["role"] = "constraintbox_core"
    errors = validate_engine_set(role_conflation, expected_source_hashes)
    controls["role_conflation"] = {
        "caught": "jax:role_mismatch" in errors,
        "errors": errors,
        "boundary_formal_case_blocked": formal["boundary_role_conflation"]["decision"]["disposition"] == "BLOCKED",
    }

    controls["workflow_cycle"] = {
        "caught": formal["workflow_cycle"]["decision"]["disposition"] == "BLOCKED",
        "reason": formal["workflow_cycle"]["decision"]["reason"],
    }
    controls["workflow_skipped_prerequisite"] = {
        "caught": formal["workflow_skipped_prerequisite"]["decision"]["disposition"] == "BLOCKED",
        "reason": formal["workflow_skipped_prerequisite"]["decision"]["reason"],
    }
    controls["diffrax_operation_severance"] = {
        "caught": (
            diffrax_operation_severance.get("returncode") == 1
            and diffrax_operation_severance.get("expected_returncode") == 1
            and "CB_DIFFRAX_OPERATION_SEVERED"
            in str(diffrax_operation_severance.get("stderr", ""))
        ),
        "subprocess_receipt": diffrax_operation_severance,
    }
    require(all(record.get("caught") is True for record in controls.values()), "one or more adversarial controls was not caught")
    return controls


def _outer_tool(context: dict[str, Any]) -> Any:
    from constraintbox.intake import canonical_json as cb_canonical_json
    from constraintbox.mini_levos import HookResult, HookSignal

    gate_input = context.get("gate_input")
    if not isinstance(gate_input, dict):
        raise ControllerError("outer Mini-Lev tool gate_input missing")
    expected_keys = {
        "adversarial_controls_observed",
        "bundle_sha256",
        "engines_observed",
        "formal_observed",
        "formal_summary_sha256",
        "roles_separated",
        "smt_observed",
        "smt_receipt_sha256",
    }
    if set(gate_input) != expected_keys:
        raise ControllerError("outer Mini-Lev tool gate_input keys mismatch")
    binding_sha256 = sha256_bytes(cb_canonical_json(gate_input))
    observation = {
        "state": "OBSERVED",
        "binding_sha256": binding_sha256,
    }
    return HookResult(
        HookSignal.OBSERVED,
        observation,
        {
            "outer_observation_state": "OBSERVED",
            "outer_observation_binding_sha256": binding_sha256,
        },
    )


def _outer_gate(context: dict[str, Any]) -> Any:
    from constraintbox.intake import canonical_json as cb_canonical_json
    from constraintbox.mini_levos import HookResult, HookSignal

    gate_input = context.get("gate_input")
    state = context.get("outer_observation_state")
    observed_sha256 = context.get("outer_observation_binding_sha256")
    if not isinstance(gate_input, dict) or state != "OBSERVED" or not isinstance(observed_sha256, str):
        return HookResult(HookSignal.BLOCKED, {"state": "INVALID_OBSERVATION"})
    recomputed = sha256_bytes(cb_canonical_json(gate_input))
    boolean_keys = (
        "adversarial_controls_observed",
        "engines_observed",
        "formal_observed",
        "roles_separated",
        "smt_observed",
    )
    passed = recomputed == observed_sha256 and all(gate_input.get(key) is True for key in boolean_keys)
    return HookResult(
        HookSignal.PASS if passed else HookSignal.BLOCKED,
        {"state": "VERIFIED" if passed else "REJECTED", "binding_sha256": recomputed},
    )


def run_outer_minilev(
    *,
    output_root: Path,
    constraintbox_root: Path,
    gate_input: dict[str, Any],
    controller_source: Path,
    flow_directory: str = "outer_minilev",
    flow_id: str = "cb-basin-controller-outer-flow-v1",
    run_id: str = "cb-basin-controller-outer-v1",
    expected_terminal: str = "ELIGIBLE",
) -> dict[str, Any]:
    source_root = constraintbox_root / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    try:
        from constraintbox.mini_levos import (
            FlowNode,
            FlowPolicy,
            FlowTransition,
            HookKind,
            HookRegistration,
            HookSignal,
            MiniLevRuntime,
            handler_code_sha256,
            verify_flow_receipt,
        )
    except Exception as exc:
        raise ControllerError(f"cannot import ConstraintBox Mini-Lev APIs: {exc}") from exc

    flow_root = output_root / flow_directory
    flow_root.mkdir(parents=True, exist_ok=False)
    ledger_path = flow_root / "flow_ledger.jsonl"
    source_sha256 = sha256_file(controller_source)

    def registration(
        hook_id: str,
        kind: Any,
        handler: Callable[[dict[str, Any]], Any],
        signals: tuple[Any, ...],
        update_keys: tuple[str, ...] = (),
    ) -> Any:
        return HookRegistration(
            hook_id=hook_id,
            kind=kind,
            handler=handler,
            source_path=controller_source,
            source_sha256=source_sha256,
            code_sha256=handler_code_sha256(handler),
            allowed_signals=signals,
            allowed_update_keys=update_keys,
            max_output_bytes=65_536,
        )

    tool = registration(
        "cb-basin-controller-tool",
        HookKind.TOOL,
        _outer_tool,
        (HookSignal.OBSERVED,),
        ("outer_observation_state", "outer_observation_binding_sha256"),
    )
    gate = registration(
        "cb-basin-controller-gate",
        HookKind.GATE,
        _outer_gate,
        (HookSignal.PASS, HookSignal.BLOCKED),
    )
    policy = FlowPolicy(
        flow_id=flow_id,
        entry_node="evidence-tool",
        nodes=(FlowNode("evidence-tool", tool.hook_id), FlowNode("evidence-gate", gate.hook_id)),
        transitions=(
            FlowTransition("evidence-tool", HookSignal.OBSERVED, "evidence-gate"),
            FlowTransition("evidence-tool", HookSignal.HOLD, "HOLD"),
            FlowTransition("evidence-gate", HookSignal.PASS, "ELIGIBLE"),
            FlowTransition("evidence-gate", HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition("evidence-gate", HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("ELIGIBLE", "BLOCKED", "HOLD"),
        required_nodes=("evidence-tool", "evidence-gate"),
        max_steps=2,
        max_visits_per_node=1,
        max_retries=0,
        max_context_bytes=65_536,
        max_event_bytes=131_072,
        max_receipt_bytes=1_048_576,
        claim_ceiling=CLAIM_CEILING,
    )
    runtime = MiniLevRuntime(
        policy,
        (tool, gate),
        run_id=run_id,
        ledger_path=ledger_path,
    )
    receipt = runtime.run({"gate_input": gate_input})
    require(
        receipt.get("terminal") == expected_terminal,
        f"outer Mini-Lev terminal {receipt.get('terminal')!r} != {expected_terminal!r}",
    )
    require(receipt.get("promotion_allowed") is False, "outer Mini-Lev self-promoted")
    valid, reason = verify_flow_receipt(
        receipt,
        expected_run_id=run_id,
        expected_policy_sha256=runtime.policy_sha256,
        expected_ledger_path=ledger_path,
        expected_retained_head_sha256=runtime.retained_head_sha256,
        expected_receipt_sha256=runtime.receipt_sha256,
    )
    require(valid, f"outer Mini-Lev receipt verification failed: {reason}")
    receipt_path = flow_root / "flow_receipt.json"
    write_json_exclusive(receipt_path, receipt)
    return {
        "terminal": receipt["terminal"],
        "steps": receipt["steps"],
        "completed_nodes": receipt["completed_nodes"],
        "policy_sha256": runtime.policy_sha256,
        "retained_head_sha256": runtime.retained_head_sha256,
        "receipt_sha256": runtime.receipt_sha256,
        "receipt_file_sha256": sha256_file(receipt_path),
        "ledger_sha256": sha256_file(ledger_path),
        "verification": reason,
        "promotion_allowed": False,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--constraintbox-root", type=Path, required=True)
    python_group = parser.add_mutually_exclusive_group(required=True)
    python_group.add_argument(
        "--worker-python-runtime",
        "--python-runtime",
        dest="worker_python_runtime",
        type=Path,
        help=(
            "Python used only for the JAX, PyTorch, and finite-SMT workers; "
            "--python-runtime remains a compatibility alias"
        ),
    )
    parser.add_argument("--julia-runtime", type=Path, required=True)
    parser.add_argument("--julia-project", type=Path, required=True)
    parser.add_argument("--worker-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    controller_source = Path(__file__).resolve()
    constraintbox_root = resolved_directory(args.constraintbox_root, "ConstraintBox root")
    require(sys.implementation.name == "cpython", "controller requires CPython")
    require(
        (3, 11) <= sys.version_info[:2] < (3, 14),
        "controller CPython must satisfy >=3.11,<3.14",
    )
    controller_python_invocation, controller_python_runtime = executable_invocation(
        Path(sys.executable), "controller Python runtime"
    )
    python_runtime_invocation, python_runtime = executable_invocation(
        args.worker_python_runtime, "worker Python runtime"
    )
    julia_runtime_invocation, julia_runtime = executable_invocation(
        args.julia_runtime, "Julia runtime"
    )
    worker_root = resolved_directory(args.worker_root, "worker root")
    julia_project_input = args.julia_project.expanduser().resolve(strict=True)
    if julia_project_input.is_dir():
        julia_project_dir = julia_project_input
        julia_project_file = resolved_file(julia_project_dir / "Project.toml", "Julia Project.toml")
    else:
        julia_project_file = resolved_file(julia_project_input, "Julia Project.toml")
        require(julia_project_file.name == "Project.toml", "--julia-project file must be Project.toml")
        julia_project_dir = julia_project_file.parent
    require((julia_project_dir / "Manifest.toml").is_file(), "Julia project has no Manifest.toml")

    output_root = args.output_dir.expanduser().resolve()
    require(not output_root.exists(), f"controller output directory already exists: {output_root}")
    output_root.mkdir(parents=True, exist_ok=False)

    object_card_path = resolved_file(worker_root / OBJECT_CARD_NAME, "object card")
    object_card = read_json(object_card_path)
    require(object_card.get("schema_version") == "wizard_v4_3_primary_object_card_v1", "object card schema mismatch")
    primary = require_dict(object_card.get("primary_object_card"), "object card primary_object_card")
    statement = primary.get("object_statement")
    require(isinstance(statement, str), "object statement missing")
    require(primary.get("object_statement_sha256") == sha256_bytes(statement.encode("utf-8")), "object statement hash mismatch")

    sources = {
        "jax": resolved_file(worker_root / "jax_basin.py", "JAX worker"),
        "julia": resolved_file(worker_root / "julia_basin.jl", "Julia worker"),
        "pytorch": resolved_file(worker_root / "torch_basin.py", "PyTorch worker"),
        "smt": resolved_file(worker_root / "smt_basin.py", "SMT worker"),
    }
    source_hashes = {name: sha256_file(path) for name, path in sources.items()}
    worker_output_root = output_root / "workers"
    worker_output_root.mkdir()
    cache_root = output_root / "runtime_cache"
    cache_root.mkdir()
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONHASHSEED": "0",
            "NUMBA_CACHE_DIR": str(cache_root / "numba"),
            "MPLCONFIGDIR": str(cache_root / "matplotlib"),
        }
    )

    engine_normalized: dict[str, dict[str, Any]] = {}
    engine_run_pairs: dict[str, Any] = {}
    engine_specs: dict[str, tuple[str, Callable[..., dict[str, Any]], list[str]]] = {
        "jax": (
            "jax_basin_receipt.json",
            normalize_jax,
            [str(python_runtime_invocation), str(sources["jax"])],
        ),
        "julia": (
            "julia_basin_receipt.json",
            normalize_julia,
            [
                str(julia_runtime_invocation),
                "--startup-file=no",
                f"--project={julia_project_dir}",
                str(sources["julia"]),
            ],
        ),
        "pytorch": (
            "torch_basin_receipt.json",
            normalize_torch,
            [str(python_runtime_invocation), str(sources["pytorch"])],
        ),
    }
    for engine_name in ENGINE_NAMES:
        receipt_name, normalizer, base_command = engine_specs[engine_name]
        normalized_runs: list[dict[str, Any]] = []
        run_records: list[dict[str, Any]] = []
        for replay_name in ("run_a", "run_b"):
            lane = worker_output_root / engine_name / replay_name
            command = base_command + ["--output-dir", str(lane)]
            if engine_name == "jax" and replay_name == "run_b":
                command.extend(
                    [
                        "--audit-against",
                        str(worker_output_root / "jax" / "run_a" / receipt_name),
                    ]
                )
            subprocess_receipt = command_receipt(
                command=command,
                cwd=worker_root,
                output_dir=lane,
                environment=environment,
            )
            receipt_path = lane / receipt_name
            require(receipt_path.is_file(), f"{engine_name} receipt missing: {receipt_path}")
            worker_receipt = read_json(receipt_path)
            if engine_name == "jax":
                normalized = normalizer(
                    worker_receipt,
                    source_path=sources[engine_name],
                    python_runtime=python_runtime,
                    receipt_path=receipt_path,
                )
            elif engine_name == "julia":
                normalized = normalizer(
                    worker_receipt,
                    source_path=sources[engine_name],
                    julia_runtime=julia_runtime,
                    julia_project_file=julia_project_file,
                    receipt_path=receipt_path,
                )
            else:
                normalized = normalizer(
                    worker_receipt,
                    source_path=sources[engine_name],
                    python_runtime=python_runtime,
                    receipt_path=receipt_path,
                )
            worker_replay_audit: dict[str, Any] | None = None
            if engine_name == "jax" and replay_name == "run_b":
                audit_path = lane / "jax_semantic_replay_audit.json"
                require(audit_path.is_file(), "JAX worker replay audit is missing")
                audit = read_json(audit_path)
                require(
                    audit.get("audit_pass") is True
                    and audit.get("semantic_projection_match") is True
                    and audit.get("source_hash_match") is True
                    and audit.get("package_versions_match") is True,
                    "JAX worker replay audit failed",
                )
                worker_replay_audit = {
                    "path": str(audit_path),
                    "sha256": sha256_file(audit_path),
                    "audit_pass": True,
                }
            normalized_runs.append(normalized)
            run_records.append(
                {
                    "receipt_path": str(receipt_path),
                    "receipt_sha256": sha256_file(receipt_path),
                    "subprocess_receipt": subprocess_receipt,
                    "normalized": normalized,
                    "worker_replay_audit": worker_replay_audit,
                }
            )
        require(
            replay_projection(normalized_runs[0]) == replay_projection(normalized_runs[1]),
            f"{engine_name} path-independent semantic replay mismatch",
        )
        selected = copy.deepcopy(normalized_runs[0])
        selected["receipt_sha256"] = normalized_runs[0]["receipt_sha256"]
        engine_normalized[engine_name] = selected
        engine_run_pairs[engine_name] = {
            "runs": run_records,
            "semantic_replay_equal": True,
            "semantic_replay_sha256": normalized_runs[0]["semantic_replay_sha256"],
        }

    diffrax_poison_lane = worker_output_root / "jax" / "diffrax_operation_severed"
    diffrax_poison_environment = dict(environment)
    diffrax_poison_environment["CONSTRAINTBOX_TEST_SEVER_DIFFRAX"] = "1"
    diffrax_operation_severance = command_receipt(
        command=[
            str(python_runtime_invocation),
            str(sources["jax"]),
            "--output-dir",
            str(diffrax_poison_lane),
        ],
        cwd=worker_root,
        output_dir=diffrax_poison_lane,
        environment=diffrax_poison_environment,
        expected_returncode=1,
        required_stderr_substring="CB_DIFFRAX_OPERATION_SEVERED",
    )
    require(
        not (diffrax_poison_lane / "jax_basin_receipt.json").exists(),
        "Diffrax-poisoned JAX run emitted a passing receipt",
    )
    engine_run_pairs["jax"]["diffrax_operation_severance"] = (
        diffrax_operation_severance
    )

    engine_errors = validate_engine_set(
        engine_normalized,
        {name: source_hashes[name] for name in ENGINE_NAMES},
    )
    require(not engine_errors, "engine set validation failed: " + "; ".join(engine_errors))
    observation_bundle = build_observation_bundle(engine_normalized)
    bundle_path = output_root / "cb_attractor_basin_observations_v1.json"
    write_json_exclusive(bundle_path, observation_bundle)

    smt_runs: list[dict[str, Any]] = []
    smt_normalized_runs: list[dict[str, Any]] = []
    for replay_name in ("run_a", "run_b"):
        lane = worker_output_root / "smt" / replay_name
        command = [
            str(python_runtime_invocation),
            str(sources["smt"]),
            "--input",
            str(bundle_path),
            "--output-dir",
            str(lane),
        ]
        subprocess_receipt = command_receipt(
            command=command,
            cwd=worker_root,
            output_dir=lane,
            environment=environment,
        )
        receipt_path = lane / "smt_basin_receipt.json"
        require(receipt_path.is_file(), f"SMT receipt missing: {receipt_path}")
        receipt = read_json(receipt_path)
        normalized = normalize_smt(
            receipt,
            source_path=sources["smt"],
            python_runtime=python_runtime,
            bundle=observation_bundle,
            receipt_path=receipt_path,
        )
        smt_normalized_runs.append(normalized)
        smt_runs.append(
            {
                "receipt_path": str(receipt_path),
                "receipt_sha256": sha256_file(receipt_path),
                "subprocess_receipt": subprocess_receipt,
                "normalized": normalized,
            }
        )
    require(
        replay_projection(smt_normalized_runs[0]) == replay_projection(smt_normalized_runs[1]),
        "SMT path-independent semantic replay mismatch",
    )
    smt_selected = smt_normalized_runs[0]

    formal = run_formal_profiles(
        output_root=output_root,
        constraintbox_root=constraintbox_root,
        controller_source=controller_source,
    )
    formal_summary_sha256 = sha256_bytes(canonical_json_bytes(formal))
    adversarial_controls = run_adversarial_controls(
        engines=engine_normalized,
        expected_source_hashes={name: source_hashes[name] for name in ENGINE_NAMES},
        formal=formal,
        diffrax_operation_severance=diffrax_operation_severance,
    )
    formal_positive = all(
        formal[name]["decision"]["disposition"] == expected
        for name, expected in {
            "workflow_valid": "ELIGIBLE",
            "workflow_cycle": "BLOCKED",
            "workflow_skipped_prerequisite": "BLOCKED",
            "symbolic_x3_minus_x": "ELIGIBLE",
            "boundary_valid": "ELIGIBLE",
            "boundary_role_conflation": "BLOCKED",
        }.items()
    )
    smt_severed_gate_input = {
        "adversarial_controls_observed": all(
            row.get("caught") is True for row in adversarial_controls.values()
        ),
        "bundle_sha256": sha256_file(bundle_path),
        "engines_observed": not engine_errors,
        "formal_observed": formal_positive,
        "formal_summary_sha256": formal_summary_sha256,
        "roles_separated": all(
            engine_normalized[name]["role"] == EXPECTED_ROLES[name]
            for name in ENGINE_NAMES
        ),
        "smt_observed": False,
        "smt_receipt_sha256": "0" * 64,
    }
    smt_severed_flow = run_outer_minilev(
        output_root=output_root,
        constraintbox_root=constraintbox_root,
        gate_input=smt_severed_gate_input,
        controller_source=controller_source,
        flow_directory="outer_minilev_smt_severed",
        flow_id="cb-basin-controller-outer-smt-severed-flow-v1",
        run_id="cb-basin-controller-outer-smt-severed-v1",
        expected_terminal="BLOCKED",
    )
    adversarial_controls["smt_severance"] = {
        "caught": smt_severed_flow["terminal"] == "BLOCKED",
        "intact_smt_observed": smt_selected["all_controls_passed"],
        "gate_if_smt_removed": False,
        "retained_negative_minilev": smt_severed_flow,
    }
    require(
        all(record.get("caught") is True for record in adversarial_controls.values()),
        "one or more final adversarial controls was not caught",
    )
    gate_input = {
        "adversarial_controls_observed": all(
            row.get("caught") is True for row in adversarial_controls.values()
        ),
        "bundle_sha256": sha256_file(bundle_path),
        "engines_observed": not engine_errors,
        "formal_observed": formal_positive,
        "formal_summary_sha256": formal_summary_sha256,
        "roles_separated": all(
            engine_normalized[name]["role"] == EXPECTED_ROLES[name]
            for name in ENGINE_NAMES
        ),
        "smt_observed": smt_selected["all_controls_passed"],
        "smt_receipt_sha256": smt_selected["receipt_sha256"],
    }
    outer_flow = run_outer_minilev(
        output_root=output_root,
        constraintbox_root=constraintbox_root,
        gate_input=gate_input,
        controller_source=controller_source,
    )

    envelope_body = {
        "schema": "three_engine_sim_result_v1",
        "challenge_id": CHALLENGE_ID,
        "object_card": {
            "path": str(object_card_path),
            "sha256": sha256_file(object_card_path),
            "object_statement_sha256": primary["object_statement_sha256"],
        },
        "controller": {
            "source_path": str(controller_source),
            "source_sha256": sha256_file(controller_source),
            "controller_python_runtime_invocation": str(controller_python_invocation),
            "controller_python_runtime_resolved": str(controller_python_runtime),
            "controller_python_runtime_sha256": sha256_file(controller_python_runtime),
            "controller_python_version": ".".join(
                str(value) for value in sys.version_info[:3]
            ),
            "worker_python_runtime_invocation": str(python_runtime_invocation),
            "worker_python_runtime_resolved": str(python_runtime),
            "worker_python_runtime_sha256": sha256_file(python_runtime),
            "controller_and_worker_python_same_identity": (
                controller_python_runtime == python_runtime
            ),
            "julia_runtime_sha256": sha256_file(julia_runtime),
            "julia_runtime_invocation": str(julia_runtime_invocation),
            "julia_project_sha256": sha256_file(julia_project_file),
            "julia_manifest_sha256": sha256_file(julia_project_file.parent / "Manifest.toml"),
            "deterministic_bounded_gate_authority": True,
            "llm_called": False,
        },
        "boundary": {
            "constraintbox_core": [
                "CPython controller",
                "Z3/CVC5/CPython finite SMT checker",
                "ConstraintBox formal profiles",
                "Mini-Lev runtime",
            ],
            "external_sim_engines": ["JAX/Diffrax", "Julia Attractors/DynamicalSystems", "PyTorch/PyG"],
            "external_sim_engines_are_constraintbox_core": False,
            "smt_lane": "CB-owned finite obligation checker over the typed observation bundle",
            "smt_is_external_sim_engine": False,
            "claim_gate_sim_admission": False,
            "claim_gate_sim_admission_reason": "no current ClaimGate registry link admits this basin profile",
        },
        "engine_runs": engine_run_pairs,
        "agreed_engine_observations": engine_normalized,
        "observation_bundle": {
            "path": str(bundle_path),
            "sha256": sha256_file(bundle_path),
            "value": observation_bundle,
        },
        "smt": {
            "runs": smt_runs,
            "semantic_replay_equal": True,
            "selected": smt_selected,
        },
        "constraintbox_formal": formal,
        "adversarial_controls": adversarial_controls,
        "outer_minilev": outer_flow,
        "result": {
            "bounded_run_status": "PASS",
            "partition_counts": EXPECTED_COUNTS,
            "fixed_point_spectral_radii_tenths": EXPECTED_RADII_TENTHS,
            "wrong_fixed_point_spectral_radii_tenths": EXPECTED_WRONG_RADII_TENTHS,
            "promotion_allowed": False,
            "continuous_basin_proof": False,
            "formal_admission_allowed": False,
            "scientific_admission_allowed": False,
            "whole_sim_estate_integrated": False,
            "automatic_tuning_established": False,
            "claim_ceiling": CLAIM_CEILING,
        },
        "blocked_consumers": [
            "continuous attractor-basin proof",
            "Julia Canon admission",
            "formal CR admission",
            "whole sim estate integrated claim",
            "ConstraintBox release promotion",
            "automatic tuning claim",
        ],
    }
    envelope = {
        **envelope_body,
        "envelope_sha256": sha256_bytes(canonical_json_bytes(envelope_body)),
    }
    envelope_path = output_root / "controller_envelope.json"
    write_json_exclusive(envelope_path, envelope)
    print(
        json.dumps(
            {
                "bounded_run_status": "PASS",
                "controller_envelope": str(envelope_path),
                "controller_envelope_file_sha256": sha256_file(envelope_path),
                "envelope_sha256": envelope["envelope_sha256"],
                "promotion_allowed": False,
                "continuous_basin_proof": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
