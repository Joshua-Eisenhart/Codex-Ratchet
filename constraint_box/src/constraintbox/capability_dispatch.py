"""Static controller dispatch for bounded external capability test flows.

The mapping is deliberately source-owned and finite.  A caller may name one
registered capability ID, but cannot provide a module, callable, executable,
worker, function, gate, transition, or tolerance.  Every selected flow is an
external workload behind its own Mini-LevOS tool-to-gate receipt path.
"""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import inspect
import os
from pathlib import Path
from typing import Any

from .capability_origin import (
    CAPABILITY_FLOW_RESULT_NAME,
    ORIGIN_ATTESTATION_NAME,
    ORIGIN_ATTESTATION_SCHEMA,
    ORIGIN_POLICY_ID,
    CapabilityOrigin,
    capability_ids as _registered_capability_ids,
    origin_for_capability,
    registry_sha256,
    source_path,
)
from .intake import canonical_json
from .external_capability import CAPABILITY_ID as PYTORCH_CAPABILITY_ID
from .external_capability_flow import run_pytorch_capability_flow
from .external_diffrax_capability import CAPABILITY_ID as DIFFRAX_CAPABILITY_ID
from .external_diffrax_capability_flow import run_diffrax_tsit5_capability_flow
from .external_e3nn_capability import CAPABILITY_ID as E3NN_CAPABILITY_ID
from .external_e3nn_capability_flow import run_e3nn_capability_flow
from .external_graph_topology_capability import (
    CAPABILITY_ID as GRAPH_TOPOLOGY_CAPABILITY_ID,
    run_graph_topology_capability_flow,
)
from .external_jax_capability import CAPABILITY_ID as JAX_CAPABILITY_ID
from .external_jax_capability_flow import run_jax_capability_flow
from .external_julia_capability import CAPABILITY_ID as JULIA_CAPABILITY_ID
from .external_julia_capability_flow import run_julia_capability_flow
from .external_multiengine_capability import (
    CAPABILITY_ID as MULTIENGINE_CAPABILITY_ID,
)
from .external_multiengine_capability import run_multiengine_capability_flow
from .external_packet_integration_capability import (
    CAPABILITY_ID as PACKET_INTEGRATION_CAPABILITY_ID,
)
from .external_packet_integration_capability_flow import (
    run_basic_packet_cross_engine_capability_flow,
)
from .external_pydmd_capability import CAPABILITY_ID as PYDMD_CAPABILITY_ID
from .external_pydmd_capability_flow import run_pydmd_capability_flow
from .external_pykoopman_capability import CAPABILITY_ID as PYKOOPMAN_CAPABILITY_ID
from .external_pykoopman_capability import run_pykoopman_capability_flow
from .external_pymdp_capability import CAPABILITY_ID as PYMDP_CAPABILITY_ID
from .external_pymdp_capability_flow import run_pymdp_capability_flow
from .external_pysindy_capability import CAPABILITY_ID as PYSINDY_CAPABILITY_ID
from .external_pysindy_capability_flow import run_pysindy_capability_flow
from .external_quimb_cotengra_capability import (
    CAPABILITY_ID as QUIMB_COTENGRA_CAPABILITY_ID,
)
from .external_quimb_cotengra_capability_flow import (
    run_quimb_cotengra_capability_flow,
)
from .external_scipy_capability import CAPABILITY_ID as SCIPY_CAPABILITY_ID
from .external_scipy_capability_flow import run_scipy_expm_capability_flow


CapabilityRunner = Callable[..., dict[str, Any]]


class CapabilityDispatchError(ValueError):
    """The named capability is not one of the controller-owned profiles."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _persist_result_exclusive(run_root: Path, result: dict[str, Any]) -> None:
    """Persist the controller-returned result for later independent consumption."""

    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise CapabilityDispatchError("capability run root must be one absolute pathlib.Path")
    try:
        with (run_root / CAPABILITY_FLOW_RESULT_NAME).open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(result).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except (OSError, TypeError, ValueError) as exc:
        raise CapabilityDispatchError(
            f"could not persist canonical capability result: {exc}"
        ) from exc


_RUNNERS: dict[str, CapabilityRunner] = {
    PYTORCH_CAPABILITY_ID: run_pytorch_capability_flow,
    JAX_CAPABILITY_ID: run_jax_capability_flow,
    PYSINDY_CAPABILITY_ID: run_pysindy_capability_flow,
    JULIA_CAPABILITY_ID: run_julia_capability_flow,
    SCIPY_CAPABILITY_ID: run_scipy_expm_capability_flow,
    DIFFRAX_CAPABILITY_ID: run_diffrax_tsit5_capability_flow,
    GRAPH_TOPOLOGY_CAPABILITY_ID: run_graph_topology_capability_flow,
    PYDMD_CAPABILITY_ID: run_pydmd_capability_flow,
    PYMDP_CAPABILITY_ID: run_pymdp_capability_flow,
    PYKOOPMAN_CAPABILITY_ID: run_pykoopman_capability_flow,
    QUIMB_COTENGRA_CAPABILITY_ID: run_quimb_cotengra_capability_flow,
    MULTIENGINE_CAPABILITY_ID: run_multiengine_capability_flow,
    PACKET_INTEGRATION_CAPABILITY_ID: run_basic_packet_cross_engine_capability_flow,
    E3NN_CAPABILITY_ID: run_e3nn_capability_flow,
}
if tuple(_RUNNERS) != _registered_capability_ids():
    raise RuntimeError("capability dispatch and provenance registry differ")


def _source_sha256(path: Path, label: str) -> str:
    try:
        return _sha256(path.read_bytes())
    except OSError as exc:
        raise CapabilityDispatchError(f"{label} source is unavailable: {exc}") from exc


def _runner_metadata(
    runner: CapabilityRunner,
    origin: CapabilityOrigin,
) -> dict[str, str]:
    """Pin the exact fixed runner selected by this controller call."""

    if (
        getattr(runner, "__module__", None) != origin.runner_module
        or getattr(runner, "__qualname__", None) != origin.runner_qualname
    ):
        raise CapabilityDispatchError("registered runner binding differs from origin registry")
    try:
        reported = inspect.getsourcefile(runner)
        actual = Path(reported or "").resolve(strict=True)
    except (OSError, TypeError) as exc:
        raise CapabilityDispatchError(f"registered runner source is unavailable: {exc}") from exc
    expected = source_path(origin.runner_source_filename).resolve(strict=True)
    if actual != expected:
        raise CapabilityDispatchError("registered runner source path differs from origin registry")
    return {
        "module": origin.runner_module,
        "qualname": origin.runner_qualname,
        "source_path": str(expected),
        "source_sha256": _source_sha256(expected, "registered runner"),
    }


def _attestation_for_result(
    *,
    run_root: Path,
    result: dict[str, Any],
    origin: CapabilityOrigin,
    runner: CapabilityRunner,
) -> dict[str, Any]:
    """Record that the fixed dispatcher, not a caller, selected this flow."""

    required = {
        "capability_id",
        "request_id",
        "run_id",
        "schema",
        "flow_policy_sha256",
        "disposition",
        "external_system",
        "kernel_membership",
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
    }
    if not isinstance(result, dict) or not required.issubset(result):
        raise CapabilityDispatchError("fixed runner returned no attestable capability result")
    if (
        result["capability_id"] != origin.capability_id
        or result["schema"] != origin.result_schema
        or result["disposition"] not in {"ELIGIBLE", "BLOCKED", "PARKED", "HOLD"}
        or result["external_system"] is not True
        or result["kernel_membership"] != "EXTERNAL_NOT_CB_KERNEL"
        or result["release_allowed"] is not False
        or result["engine_readiness_claim"] is not False
        or result["cr_truth_claim"] is not False
        or result["promotion_allowed"] is not False
    ):
        raise CapabilityDispatchError("fixed runner result differs from controller boundary")
    if not all(isinstance(result[key], str) for key in ("request_id", "run_id", "flow_policy_sha256")):
        raise CapabilityDispatchError("fixed runner result lacks bounded origin bindings")

    runner_metadata = _runner_metadata(runner, origin)
    flow_source = source_path(origin.flow_source_filename).resolve(strict=True)
    flow_source_sha256 = _source_sha256(flow_source, "registered flow")
    hooks = [
        {
            "hook_id": hook.hook_id,
            "module": hook.module,
            "qualname": hook.qualname,
            "source_path": str(flow_source),
            "source_sha256": flow_source_sha256,
        }
        for hook in origin.hooks
    ]
    dispatch_source = Path(__file__).resolve()
    body = {
        "schema": ORIGIN_ATTESTATION_SCHEMA,
        "policy_id": ORIGIN_POLICY_ID,
        "capability_id": origin.capability_id,
        "request_id": result["request_id"],
        "run_id": result["run_id"],
        "run_root": str(run_root.resolve(strict=True)),
        "capability_result_path": str(
            (run_root / CAPABILITY_FLOW_RESULT_NAME).resolve(strict=True)
        ),
        "capability_result_sha256": _sha256(canonical_json(result)),
        "flow_policy_sha256": result["flow_policy_sha256"],
        "result_disposition": result["disposition"],
        "origin": {
            "result_schema": origin.result_schema,
            "flow_id": origin.flow_id,
            "flow_module": origin.flow_module,
            "flow_source_path": str(flow_source),
            "flow_source_sha256": flow_source_sha256,
            "hooks": hooks,
            "registry_sha256": registry_sha256(),
        },
        "runner": runner_metadata,
        "issuer": {
            "module": "constraintbox.capability_dispatch",
            "source_path": str(dispatch_source),
            "source_sha256": _source_sha256(dispatch_source, "dispatcher"),
        },
        "issued_after_fixed_runner_return": True,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "promotion_allowed": False,
    }
    return {**body, "attestation_sha256": _sha256(canonical_json(body))}


def _persist_origin_attestation_exclusive(run_root: Path, attestation: dict[str, Any]) -> None:
    try:
        with (run_root / ORIGIN_ATTESTATION_NAME).open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(attestation).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except (OSError, TypeError, ValueError) as exc:
        raise CapabilityDispatchError(
            f"could not persist controller origin attestation: {exc}"
        ) from exc


def capability_ids() -> tuple[str, ...]:
    """Return the fixed ordered controller capability registry."""

    return _registered_capability_ids()


def run_capability_flow(
    *,
    capability_id: str,
    request_id: str,
    run_root: Path,
) -> dict[str, Any]:
    """Run exactly one fixed capability flow selected from the static table."""

    try:
        origin = origin_for_capability(capability_id)
    except ValueError as exc:
        raise CapabilityDispatchError(
            f"unsupported controller capability: {capability_id}"
        ) from exc
    runner = _RUNNERS.get(capability_id)
    if runner is None:
        raise CapabilityDispatchError("registered capability has no fixed runner")
    _runner_metadata(runner, origin)
    result = runner(request_id=request_id, run_root=run_root)
    _persist_result_exclusive(run_root, result)
    _persist_origin_attestation_exclusive(
        run_root,
        _attestation_for_result(
            run_root=run_root,
            result=result,
            origin=origin,
            runner=runner,
        ),
    )
    return result
