"""Closed controller registry for external capability-flow provenance.

The simulation estate is outside the ConstraintBox kernel, but a capability
result may be consumed by the kernel only when it names one of the fixed
controller profiles below.  This module carries no engine imports and no
runner selection surface: it is a small, explicit description of the flows
that the dispatcher is allowed to issue and the repair/suite verifier is
allowed to consume.

An adjacent origin attestation is evidence of the dispatch path, not a claim
of hostile-host containment.  The current controller source and the retained
Mini-Lev receipt are checked again before any result becomes a suite state or
a repair-planning input.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .intake import canonical_json


CAPABILITY_FLOW_RESULT_NAME = "capability_flow_result.json"
ORIGIN_ATTESTATION_NAME = "controller_origin_attestation.json"
ORIGIN_ATTESTATION_SCHEMA = "constraintbox.capability-origin-attestation.v1"
ORIGIN_POLICY_ID = "constraintbox.external-capability-origin-policy.v1"


@dataclass(frozen=True)
class HookOrigin:
    """One exact hook expected in a controller-selected flow policy."""

    hook_id: str
    module: str
    qualname: str

    def to_dict(self) -> dict[str, str]:
        return {
            "hook_id": self.hook_id,
            "module": self.module,
            "qualname": self.qualname,
        }


@dataclass(frozen=True)
class CapabilityOrigin:
    """Static identity of one allowed external capability flow."""

    capability_id: str
    result_schema: str
    flow_id: str
    flow_module: str
    flow_source_filename: str
    runner_module: str
    runner_qualname: str
    runner_source_filename: str
    hooks: tuple[HookOrigin, HookOrigin]

    def to_dict(self) -> dict[str, object]:
        return {
            "capability_id": self.capability_id,
            "result_schema": self.result_schema,
            "flow_id": self.flow_id,
            "flow_module": self.flow_module,
            "flow_source_filename": self.flow_source_filename,
            "runner_module": self.runner_module,
            "runner_qualname": self.runner_qualname,
            "runner_source_filename": self.runner_source_filename,
            "hooks": [hook.to_dict() for hook in self.hooks],
        }


def _origin(
    capability_id: str,
    result_schema: str,
    flow_id: str,
    flow_module: str,
    flow_source_filename: str,
    runner_module: str,
    runner_qualname: str,
    runner_source_filename: str,
    tool_hook_id: str,
    tool_qualname: str,
    gate_hook_id: str,
    gate_qualname: str,
) -> CapabilityOrigin:
    return CapabilityOrigin(
        capability_id=capability_id,
        result_schema=result_schema,
        flow_id=flow_id,
        flow_module=flow_module,
        flow_source_filename=flow_source_filename,
        runner_module=runner_module,
        runner_qualname=runner_qualname,
        runner_source_filename=runner_source_filename,
        hooks=(
            HookOrigin(tool_hook_id, flow_module, tool_qualname),
            HookOrigin(gate_hook_id, flow_module, gate_qualname),
        ),
    )


_ORIGIN_ROWS = (
    _origin(
        "pytorch-jacobian-v1",
        "constraintbox.external-capability-flow-result.v1",
        "constraintbox.pytorch-jacobian-capability-flow.v1",
        "constraintbox.external_capability_flow",
        "external_capability_flow.py",
        "constraintbox.external_capability_flow",
        "run_pytorch_capability_flow",
        "external_capability_flow.py",
        "pytorch-jacobian-capability-tool",
        "_pytorch_capability_tool",
        "pytorch-jacobian-capability-gate",
        "_pytorch_capability_gate",
    ),
    _origin(
        "jax-autodiff-v1",
        "constraintbox.external-jax-capability-flow-result.v1",
        "constraintbox.jax-autodiff-capability-flow.v1",
        "constraintbox.external_jax_capability_flow",
        "external_jax_capability_flow.py",
        "constraintbox.external_jax_capability_flow",
        "run_jax_capability_flow",
        "external_jax_capability_flow.py",
        "jax-autodiff-capability-tool",
        "_jax_capability_tool",
        "jax-autodiff-capability-gate",
        "_jax_capability_gate",
    ),
    _origin(
        "pysindy-affine-generator-v1",
        "constraintbox.external-pysindy-capability-flow-result.v1",
        "constraintbox.pysindy-affine-generator-capability-flow.v1",
        "constraintbox.external_pysindy_capability_flow",
        "external_pysindy_capability_flow.py",
        "constraintbox.external_pysindy_capability_flow",
        "run_pysindy_capability_flow",
        "external_pysindy_capability_flow.py",
        "pysindy-affine-generator-capability-tool",
        "_pysindy_capability_tool",
        "pysindy-affine-generator-capability-gate",
        "_pysindy_capability_gate",
    ),
    _origin(
        "julia-diffeq-v1",
        "constraintbox.external-julia-capability-flow-result.v1",
        "constraintbox.julia-diffeq-capability-flow.v1",
        "constraintbox.external_julia_capability_flow",
        "external_julia_capability_flow.py",
        "constraintbox.external_julia_capability_flow",
        "run_julia_capability_flow",
        "external_julia_capability_flow.py",
        "julia-diffeq-capability-tool",
        "_julia_capability_tool",
        "julia-diffeq-capability-gate",
        "_julia_capability_gate",
    ),
    _origin(
        "scipy-expm-rotation-v1",
        "constraintbox.external-scipy-capability-flow-result.v1",
        "constraintbox.scipy-expm-capability-flow.v1",
        "constraintbox.external_scipy_capability_flow",
        "external_scipy_capability_flow.py",
        "constraintbox.external_scipy_capability_flow",
        "run_scipy_expm_capability_flow",
        "external_scipy_capability_flow.py",
        "scipy-expm-capability-tool",
        "_scipy_capability_tool",
        "scipy-expm-capability-gate",
        "_scipy_capability_gate",
    ),
    _origin(
        "diffrax-tsit5-affine-flow-v1",
        "constraintbox.external-diffrax-capability-flow-result.v1",
        "constraintbox.diffrax-tsit5-capability-flow.v1",
        "constraintbox.external_diffrax_capability_flow",
        "external_diffrax_capability_flow.py",
        "constraintbox.external_diffrax_capability_flow",
        "run_diffrax_tsit5_capability_flow",
        "external_diffrax_capability_flow.py",
        "diffrax-tsit5-capability-tool",
        "_diffrax_capability_tool",
        "diffrax-tsit5-capability-gate",
        "_diffrax_capability_gate",
    ),
    _origin(
        "graph-topology-crosscheck-v1",
        "constraintbox.external-graph-topology-capability-flow-result.v1",
        "constraintbox.graph-topology-crosscheck-capability-flow.v1",
        "constraintbox.external_graph_topology_capability",
        "external_graph_topology_capability.py",
        "constraintbox.external_graph_topology_capability",
        "run_graph_topology_capability_flow",
        "external_graph_topology_capability.py",
        "graph-topology-crosscheck-capability-tool",
        "_graph_topology_capability_tool",
        "graph-topology-crosscheck-capability-gate",
        "_graph_topology_capability_gate",
    ),
    _origin(
        "pydmd-discrete-rate-v1",
        "constraintbox.external-s3-capability-flow-result.v1",
        "constraintbox.pydmd-discrete-rate-capability-flow.v1",
        "constraintbox.external_s3_capability_flow",
        "external_s3_capability_flow.py",
        "constraintbox.external_pydmd_capability_flow",
        "run_pydmd_capability_flow",
        "external_pydmd_capability_flow.py",
        "pydmd-discrete-rate-capability-tool",
        "_pydmd_capability_tool",
        "pydmd-discrete-rate-capability-gate",
        "_pydmd_capability_gate",
    ),
    _origin(
        "pymdp-two-state-inference-v1",
        "constraintbox.external-s3-capability-flow-result.v1",
        "constraintbox.pymdp-two-state-inference-capability-flow.v1",
        "constraintbox.external_s3_capability_flow",
        "external_s3_capability_flow.py",
        "constraintbox.external_pymdp_capability_flow",
        "run_pymdp_capability_flow",
        "external_pymdp_capability_flow.py",
        "pymdp-two-state-inference-capability-tool",
        "_pymdp_capability_tool",
        "pymdp-two-state-inference-capability-gate",
        "_pymdp_capability_gate",
    ),
    _origin(
        "pykoopman-identity-edmd-v1",
        "constraintbox.external-pykoopman-capability-flow-result.v1",
        "constraintbox.pykoopman-identity-edmd-capability-flow.v1",
        "constraintbox.external_pykoopman_capability",
        "external_pykoopman_capability.py",
        "constraintbox.external_pykoopman_capability",
        "run_pykoopman_capability_flow",
        "external_pykoopman_capability.py",
        "pykoopman-identity-edmd-capability-tool",
        "_pykoopman_capability_tool",
        "pykoopman-identity-edmd-capability-gate",
        "_pykoopman_capability_gate",
    ),
    _origin(
        "quimb-cotengra-bounded-suite-v1",
        "constraintbox.external-quimb-cotengra-capability-flow-result.v1",
        "constraintbox.quimb-cotengra-bounded-capability-flow.v1",
        "constraintbox.external_quimb_cotengra_capability_flow",
        "external_quimb_cotengra_capability_flow.py",
        "constraintbox.external_quimb_cotengra_capability_flow",
        "run_quimb_cotengra_capability_flow",
        "external_quimb_cotengra_capability_flow.py",
        "quimb-cotengra-bounded-capability-tool",
        "_quimb_cotengra_capability_tool",
        "quimb-cotengra-bounded-capability-gate",
        "_quimb_cotengra_capability_gate",
    ),
    _origin(
        "multiengine-dlpack-diffeq-v1",
        "constraintbox.external-capability-flow-result.v1",
        "constraintbox.multiengine-dlpack-diffeq-flow.v1",
        "constraintbox.external_multiengine_capability",
        "external_multiengine_capability.py",
        "constraintbox.external_multiengine_capability",
        "run_multiengine_capability_flow",
        "external_multiengine_capability.py",
        "multiengine-dlpack-diffeq-tool",
        "_tool",
        "multiengine-dlpack-diffeq-gate",
        "_gate",
    ),
    _origin(
        "basic-packet-cross-engine-v1",
        "constraintbox.external-packet-integration-capability-flow-result.v1",
        "constraintbox.basic-packet-cross-engine-capability-flow.v1",
        "constraintbox.external_packet_integration_capability_flow",
        "external_packet_integration_capability_flow.py",
        "constraintbox.external_packet_integration_capability_flow",
        "run_basic_packet_cross_engine_capability_flow",
        "external_packet_integration_capability_flow.py",
        "basic-packet-cross-engine-capability-tool",
        "_packet_integration_tool",
        "basic-packet-cross-engine-capability-gate",
        "_packet_integration_gate",
    ),
    _origin(
        "e3nn-wigner-crosscheck-v1",
        "constraintbox.external-e3nn-capability-flow-result.v1",
        "constraintbox.e3nn-wigner-crosscheck-capability-flow.v1",
        "constraintbox.external_e3nn_capability_flow",
        "external_e3nn_capability_flow.py",
        "constraintbox.external_e3nn_capability_flow",
        "run_e3nn_capability_flow",
        "external_e3nn_capability_flow.py",
        "e3nn-wigner-crosscheck-capability-tool",
        "_e3nn_capability_tool",
        "e3nn-wigner-crosscheck-capability-gate",
        "_e3nn_capability_gate",
    ),
)

CAPABILITY_ORIGINS = {origin.capability_id: origin for origin in _ORIGIN_ROWS}
if len(CAPABILITY_ORIGINS) != len(_ORIGIN_ROWS):
    raise RuntimeError("capability origin registry has duplicate identifiers")


def capability_ids() -> tuple[str, ...]:
    """Return the source-owned capability order used by the dispatcher."""

    return tuple(CAPABILITY_ORIGINS)


def origin_for_capability(capability_id: str) -> CapabilityOrigin:
    """Return exactly one registered origin, never a caller-provided variant."""

    try:
        return CAPABILITY_ORIGINS[capability_id]
    except KeyError as exc:
        raise ValueError("capability is not controller-registered") from exc


def source_path(filename: str) -> Path:
    """Return a package-local source path from a registry filename."""

    candidate = Path(__file__).resolve().with_name(filename)
    if candidate.name != filename or candidate.parent != Path(__file__).resolve().parent:
        raise ValueError("capability origin source filename is invalid")
    return candidate


def registry_sha256() -> str:
    """Digest the closed registry shape, excluding mutable source bytes."""

    payload = {
        "schema": "constraintbox.capability-origin-registry.v1",
        "origins": [origin.to_dict() for origin in _ORIGIN_ROWS],
    }
    return hashlib.sha256(canonical_json(payload)).hexdigest()
