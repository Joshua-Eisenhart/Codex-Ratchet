"""Small, deterministic controller for CB Light's first wave fixture.

This is intentionally *not* a general council runtime.  It runs one sealed
three-probe packet through exactly three local fake adapters, checks one fixed
Rustworkx DAG, and evaluates a finite local ``FactSet`` with Z3 plus an
exhaustive enumeration cross-check.  The three observations supply no
authority: they cannot issue PASS, promote anything, choose a provider, or
settle a result.

The terminal fixture dispositions are ``SETTLED`` and ``SETTLED_REFUTED``.
Both are local synthetic-fixture outcomes with ``promotion_allowed=false``.
A counterexample is a packet-bound local fact that changes the fixture
disposition to ``SETTLED_REFUTED`` and is recorded as a negative state
outcome; it is not a model vote or an external finding.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from hookkernel.cb_light_domain import canonical_json
from hookkernel.cb_light_state import StateError, append_only_transaction, connect
from hookkernel.cb_light_wave_state import (
    record_artifact,
    record_asset_binding,
    record_wave_attempt,
    record_wave_settlement,
    verify_wave_attempt,
)

from .wave_adapters import (
    ADAPTER_CLAIM_CEILING,
    OBSERVATION_AUTHORITY,
    OBSERVATION_KIND,
    OBSERVATION_SCHEMA,
    EvidenceMapObservationAdapter,
    FalsifierObservationAdapter,
    ProbeObservation,
    WitnessObservationAdapter,
    fixture_observation_adapters,
)
from .wave_contracts import (
    CLAIM_CEILING as CONTRACT_CLAIM_CEILING,
    PROBE_KINDS,
    PacketValidation,
    ProbeKind,
    ProbePacket,
    canonical_json_bytes,
    packet_sha256,
    validate_probe_packet,
)


WAVE_RESULT_SCHEMA = "constraintbox.wave-fixture-result.v1"
WAVE_RECEIPT_SCHEMA = "constraintbox.wave-fixture-receipt.v1"
WAVE_TOPOLOGY_SCHEMA = "constraintbox.wave-fixture-topology.v1"
WAVE_GATE_SCHEMA = "constraintbox.wave-fixture-factset-gate.v1"
WAVE_CONTROLLER_VERSION = "cb-light-fixture-wave-controller.v1"

FIXTURE_MODE = True
CORROBORATION = "none"
_FIXTURE_NODE_IDS = ("issue", "witness", "falsifier", "evidence_map", "settlement")
_FIXTURE_EDGES = (
    ("issue", "witness"),
    ("issue", "falsifier"),
    ("issue", "evidence_map"),
    ("witness", "settlement"),
    ("falsifier", "settlement"),
    ("evidence_map", "settlement"),
)
_EXPECTED_ADAPTER_TYPES = (
    WitnessObservationAdapter,
    FalsifierObservationAdapter,
    EvidenceMapObservationAdapter,
)
_EXPECTED_ADAPTER_IDS = tuple(adapter.adapter_id for adapter in fixture_observation_adapters())
_OBSERVATION_KEYS = frozenset(
    {
        "schema",
        "adapter_id",
        "probe_kind",
        "packet_sha256",
        "probe_sha256",
        "evidence_refs",
        "observation_kind",
        "authority",
        "claim_ceiling",
    }
)
_OBSERVATION_ATTRIBUTE_KEYS = frozenset(ProbeObservation.__dataclass_fields__)
_FORBIDDEN_OBSERVATION_KEYS = frozenset(
    {
        "pass",
        "status",
        "disposition",
        "terminal",
        "promotion",
        "promotion_allowed",
        "provider",
        "model",
    }
)
_FIXTURE_WITNESS_CLAIM = "target_is_admissible"
_FIXTURE_COUNTEREXAMPLE = "negates_target_admissibility"

CLAIM_CEILING = (
    "One local CB Light first-fixture wave only: exactly three deterministic "
    "synthetic adapters, a fixed topology check, and a bounded local FactSet "
    "gate. No external model/provider/skill/MMM execution, authority, "
    "corroboration, membership, adoption, portability, CB Heavy, or release claim."
)


class WaveControllerError(RuntimeError):
    """A typed local hold or refusal before an authoritative-looking result."""

    def __init__(self, disposition: str, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.disposition = disposition
        self.reason_code = reason_code
        self.detail = detail


@dataclass(frozen=True)
class FixtureFactSet:
    """Whitelisted booleans used by the local deterministic settlement law.

    Crucially, there is no provider/model/PASS input here.  ``counterexample``
    is the only semantic fixture fact, and is derived from a sealed local
    witness/falsifier relation rather than an adapter verdict.
    """

    packet_valid: bool
    fixed_topology_acyclic: bool
    exact_three_adapters: bool
    observations_bound_to_packet: bool
    all_observations_non_authoritative: bool
    counterexample_present: bool

    def as_dict(self) -> dict[str, bool]:
        return {
            "packet_valid": self.packet_valid,
            "fixed_topology_acyclic": self.fixed_topology_acyclic,
            "exact_three_adapters": self.exact_three_adapters,
            "observations_bound_to_packet": self.observations_bound_to_packet,
            "all_observations_non_authoritative": self.all_observations_non_authoritative,
            "counterexample_present": self.counterexample_present,
        }


@dataclass(frozen=True)
class _TopologyCheck:
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    topological_order: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": WAVE_TOPOLOGY_SCHEMA,
            "nodes": list(self.nodes),
            "edges": [list(edge) for edge in self.edges],
            "topological_order": list(self.topological_order),
            "acyclic": True,
            "fixed_fixture_topology": self.nodes == _FIXTURE_NODE_IDS
            and self.edges == _FIXTURE_EDGES,
        }


def _canonical_sha256(value: Any) -> str:
    return sha256(canonical_json(value)).hexdigest()


def _controller_source_sha256() -> str:
    """Bind a receipt to the installed controller source it actually ran."""

    try:
        return sha256(Path(__file__).read_bytes()).hexdigest()
    except OSError as exc:
        raise WaveControllerError(
            "HOLD",
            "HOLD_WAVE_CONTROLLER_SOURCE_UNREADABLE",
            "The installed local fixture controller source cannot be attested.",
        ) from exc


def _result(
    disposition: str,
    reason_code: str,
    detail: str,
    *,
    persisted: bool,
    **extra: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": WAVE_RESULT_SCHEMA,
        "controller": WAVE_CONTROLLER_VERSION,
        "profile": "cb_light",
        "fixture_mode": FIXTURE_MODE,
        "disposition": disposition,
        "reason_code": reason_code,
        "detail": detail,
        "promotion_allowed": False,
        "corroboration": CORROBORATION,
        "persisted": persisted,
        "claim_ceiling": CLAIM_CEILING,
        "exit_code_contract": (
            "CLI exit 0 means only a non-refuted local fixture settlement; "
            "HOLD, REFUSE, and SETTLED_REFUTED exit 2 and never grant claim acceptance."
        ),
        "external_assets": {
            "models": "not_invoked",
            "providers": "not_invoked",
            "skills": "not_invoked",
            "mmms": "reference_digest_only",
            "pydantic_ai": "not_imported",
            "cb_heavy": "not_imported",
            "network": "not_used",
        },
    }
    body.update(extra)
    return body


def _safe_packet_fields(validation: PacketValidation) -> dict[str, Any]:
    """Expose only metadata safe to return for a validated envelope failure."""

    body: dict[str, Any] = {}
    if validation.packet_sha256 is not None:
        body["packet_sha256"] = validation.packet_sha256
    if validation.contract_schema_sha256 is not None:
        body["contract_schema_sha256"] = validation.contract_schema_sha256
    return body


def _is_structurally_terminal_fixture_disposition(disposition: str) -> bool:
    """Allow a refuted fixture to persist without treating it as acceptance."""

    return disposition in {"SETTLED", "SETTLED_REFUTED"}


def _as_fixed_edges(
    topology_edges: Sequence[Sequence[str]] | None,
) -> tuple[tuple[str, str], ...]:
    if topology_edges is None:
        return _FIXTURE_EDGES
    normalized: list[tuple[str, str]] = []
    for edge in topology_edges:
        if not isinstance(edge, Sequence) or isinstance(edge, (str, bytes)) or len(edge) != 2:
            raise WaveControllerError(
                "REFUSE",
                "REFUSE_WAVE_TOPOLOGY_INVALID",
                "A fixture topology edge must be a two-node sequence.",
            )
        source, target = edge
        if not isinstance(source, str) or not isinstance(target, str):
            raise WaveControllerError(
                "REFUSE",
                "REFUSE_WAVE_TOPOLOGY_INVALID",
                "A fixture topology edge must name string nodes.",
            )
        if source not in _FIXTURE_NODE_IDS or target not in _FIXTURE_NODE_IDS:
            raise WaveControllerError(
                "REFUSE",
                "REFUSE_WAVE_TOPOLOGY_INVALID",
                "A fixture topology edge names a node outside the fixed fixture graph.",
            )
        normalized.append((source, target))
    return tuple(normalized)


def _check_fixed_topology(
    topology_edges: Sequence[Sequence[str]] | None = None,
) -> _TopologyCheck:
    """Run Rustworkx over the fixed first-fixture management graph.

    The ``topology_edges`` parameter is intentionally test-only injection.  It
    cannot be supplied through the public packet or CLI, so untrusted input
    cannot choose a graph.  Any shape drift or cycle is a refusal, never a
    best-effort topology result.
    """

    try:
        import rustworkx
    except ModuleNotFoundError as exc:
        if exc.name == "rustworkx":
            raise WaveControllerError(
                "HOLD",
                "HOLD_WAVE_RUSTWORKX_UNAVAILABLE",
                "The contained CB Light Rustworkx dependency is unavailable.",
            ) from exc
        raise

    edges = _as_fixed_edges(topology_edges)
    graph = rustworkx.PyDiGraph()
    node_indices = {name: graph.add_node(name) for name in _FIXTURE_NODE_IDS}
    graph.add_edges_from_no_data(
        [(node_indices[source], node_indices[target]) for source, target in edges]
    )
    try:
        order = tuple(str(graph[index]) for index in rustworkx.topological_sort(graph))
    except rustworkx.DAGHasCycle as exc:
        raise WaveControllerError(
            "REFUSE",
            "REFUSE_WAVE_TOPOLOGY_CYCLE",
            "The fixed fixture topology contains a cycle: " + str(exc),
        ) from exc

    if topology_edges is not None and edges != _FIXTURE_EDGES:
        raise WaveControllerError(
            "REFUSE",
            "REFUSE_WAVE_TOPOLOGY_DRIFT",
            "The first fixture accepts only its fixed Rustworkx DAG.",
        )

    if set(order) != set(_FIXTURE_NODE_IDS) or len(order) != len(_FIXTURE_NODE_IDS):
        raise WaveControllerError(
            "REFUSE",
            "REFUSE_WAVE_TOPOLOGY_INVALID",
            "Rustworkx did not return every fixed fixture node exactly once.",
        )
    return _TopologyCheck(nodes=_FIXTURE_NODE_IDS, edges=edges, topological_order=order)


def _expected_probe_sha256(packet: ProbePacket, kind: ProbeKind) -> str:
    probe = packet.probe_for(kind)
    return sha256(
        canonical_json_bytes(
            {
                "packet_sha256": packet_sha256(packet),
                "kind": probe.kind,
                "node_id": probe.node_id,
                "mmm_sha256": probe.mmm_sha256,
                "constrained_input_sha256": probe.constrained_input_sha256,
                "payload": dict(probe.payload),
                "evidence_refs": list(probe.evidence_refs),
            }
        )
    ).hexdigest()


def _witness_fact_sha256(packet: ProbePacket) -> str:
    """Address the witness fact without circularly hashing falsifier input."""

    witness = packet.probe_for("witness")
    return sha256(
        canonical_json_bytes(
            {
                "packet_id": packet.packet_id,
                "wave_definition_id": packet.wave_definition_id,
                "issue_root_input_sha256": packet.issue.root_input_sha256,
                "target_id": packet.target_id,
                "witness": witness.as_dict(),
            }
        )
    ).hexdigest()


def _verify_local_observation(
    observation: Any,
    *,
    packet: ProbePacket,
    kind: ProbeKind,
    adapter_id: str,
) -> ProbeObservation:
    """Reject a receipt-shaped assertion before it reaches the FactSet."""

    if type(observation) is not ProbeObservation:
        raise WaveControllerError(
            "REFUSE",
            "REFUSE_SYNTHETIC_OBSERVATION_FORGED",
            "A fixture adapter did not return the exact local ProbeObservation type.",
        )
    body = observation.as_dict()
    if (
        set(vars(observation)) != _OBSERVATION_ATTRIBUTE_KEYS
        or set(body) != _OBSERVATION_KEYS
        or _FORBIDDEN_OBSERVATION_KEYS.intersection(
        str(key).lower() for key in body
        )
    ):
        raise WaveControllerError(
            "REFUSE",
            "REFUSE_SYNTHETIC_OBSERVATION_FORGED",
            "A fixture observation carried undeclared or authority-shaped fields.",
        )
    expected_probe = packet.probe_for(kind)
    if (
        observation.schema != OBSERVATION_SCHEMA
        or observation.adapter_id != adapter_id
        or observation.probe_kind != kind
        or observation.packet_sha256 != packet_sha256(packet)
        or observation.probe_sha256 != _expected_probe_sha256(packet, kind)
        or observation.evidence_refs != expected_probe.evidence_refs
        or observation.observation_kind != OBSERVATION_KIND
        or observation.authority != OBSERVATION_AUTHORITY
        or observation.claim_ceiling != ADAPTER_CLAIM_CEILING
    ):
        raise WaveControllerError(
            "REFUSE",
            "REFUSE_SYNTHETIC_OBSERVATION_FORGED",
            "A fixture observation drifted from its sealed local packet binding.",
        )
    return observation


def _run_exactly_three_adapters(
    packet: ProbePacket,
    adapter_factory: Callable[[], Iterable[Any]],
) -> tuple[ProbeObservation, ...]:
    """Exercise the fixed local-only adapter set in deterministic role order."""

    try:
        adapters = tuple(adapter_factory())
    except Exception as exc:
        raise WaveControllerError(
            "HOLD",
            "HOLD_FIXTURE_ADAPTER_SET_UNAVAILABLE",
            "The local fixture adapter factory could not provide its three adapters.",
        ) from exc
    if len(adapters) != len(PROBE_KINDS):
        raise WaveControllerError(
            "REFUSE",
            "REFUSE_FIXTURE_ADAPTER_SET_DRIFT",
            "The fixture must run exactly witness, falsifier, and evidence-map adapters.",
        )

    observations: list[ProbeObservation] = []
    for kind, expected_type, expected_id, adapter in zip(
        PROBE_KINDS, _EXPECTED_ADAPTER_TYPES, _EXPECTED_ADAPTER_IDS, adapters
    ):
        if type(adapter) is not expected_type or getattr(adapter, "adapter_id", None) != expected_id:
            raise WaveControllerError(
                "REFUSE",
                "REFUSE_FIXTURE_ADAPTER_SET_DRIFT",
                "The fixture accepts only its three fixed local adapter implementations.",
            )
        try:
            raw_observation = adapter.observe(packet)
        except Exception as exc:
            raise WaveControllerError(
                "HOLD",
                "HOLD_FIXTURE_ADAPTER_EXECUTION_FAILED",
                f"The local {kind} fixture adapter did not return an observation.",
            ) from exc
        observations.append(
            _verify_local_observation(
                raw_observation,
                packet=packet,
                kind=kind,
                adapter_id=expected_id,
            )
        )
    return tuple(observations)


def _counterexample_present(packet: ProbePacket) -> bool:
    """Validate the finite local witness/counterexample relation.

    This remains a deliberately tiny fixture predicate, not a general semantic
    theorem prover.  A refutation needs both exact contradictory fixture
    literals *and* a digest/address binding to the specific witness probe.  A
    bare ``counterexample`` key cannot flip a result on its own.
    """

    witness = packet.probe_for("witness")
    falsifier = packet.probe_for("falsifier")
    witness_payload = dict(witness.payload)
    falsifier_payload = dict(falsifier.payload)
    return (
        witness_payload.get("fixture_claim") == _FIXTURE_WITNESS_CLAIM
        and falsifier_payload.get("counterexample") == _FIXTURE_COUNTEREXAMPLE
        and falsifier_payload.get("refutes_witness_node_id") == witness.node_id
        and falsifier_payload.get("refutes_witness_fact_sha256")
        == _witness_fact_sha256(packet)
    )


def _settlement_from_facts(facts: FixtureFactSet) -> str:
    structurally_settled = (
        facts.packet_valid
        and facts.fixed_topology_acyclic
        and facts.exact_three_adapters
        and facts.observations_bound_to_packet
        and facts.all_observations_non_authoritative
    )
    if not structurally_settled:
        return "REFUSE"
    return "SETTLED_REFUTED" if facts.counterexample_present else "SETTLED"


def _z3_enumeration_check(facts: FixtureFactSet) -> dict[str, Any]:
    """Prove this bounded gate matches exhaustive Boolean enumeration.

    This proves only the encoded finite law, not that a model or a collection
    of council nodes produced independent evidence.  The result records that
    literal ceiling rather than treating multiple adapters as corroboration.
    """

    try:
        import z3
    except ModuleNotFoundError as exc:
        if exc.name == "z3":
            raise WaveControllerError(
                "HOLD",
                "HOLD_WAVE_Z3_UNAVAILABLE",
                "The contained CB Light Z3 dependency is unavailable.",
            ) from exc
        raise

    names = (
        "packet_valid",
        "fixed_topology_acyclic",
        "exact_three_adapters",
        "observations_bound_to_packet",
        "all_observations_non_authoritative",
        "counterexample_present",
    )
    symbols = {name: z3.Bool(name) for name in names}
    structural = z3.And(
        symbols["packet_valid"],
        symbols["fixed_topology_acyclic"],
        symbols["exact_three_adapters"],
        symbols["observations_bound_to_packet"],
        symbols["all_observations_non_authoritative"],
    )
    refuted = z3.And(structural, symbols["counterexample_present"])

    input_values = facts.as_dict()
    solver = z3.Solver()
    solver.add(*(symbols[name] == z3.BoolVal(input_values[name]) for name in names))
    if solver.check() != z3.sat:
        raise WaveControllerError(
            "HOLD",
            "HOLD_WAVE_Z3_FACTSET_UNSAT",
            "The bounded local FactSet could not be evaluated by Z3.",
        )
    model = solver.model()
    z3_structural = z3.is_true(model.eval(structural, model_completion=True))
    z3_refuted = z3.is_true(model.eval(refuted, model_completion=True))

    # Exhaust all 64 combinations.  This is deliberately a small local
    # enumeration, independent of the current fact values, to catch a drift
    # between the Python settlement function and the Z3 predicate.
    enumeration_cases = 0
    for bits in range(1 << len(names)):
        candidate_values = {
            name: bool(bits & (1 << index)) for index, name in enumerate(names)
        }
        candidate = FixtureFactSet(**candidate_values)
        candidate_expected = _settlement_from_facts(candidate)
        candidate_solver = z3.Solver()
        candidate_solver.add(
            *(symbols[name] == z3.BoolVal(candidate_values[name]) for name in names)
        )
        if candidate_solver.check() != z3.sat:
            raise WaveControllerError(
                "HOLD",
                "HOLD_WAVE_Z3_ENUMERATION_UNSAT",
                "A finite FactSet assignment was unexpectedly unsatisfiable.",
            )
        candidate_model = candidate_solver.model()
        candidate_structural = z3.is_true(
            candidate_model.eval(structural, model_completion=True)
        )
        candidate_refuted = z3.is_true(
            candidate_model.eval(refuted, model_completion=True)
        )
        z3_expected = (
            "SETTLED_REFUTED"
            if candidate_structural and candidate_refuted
            else "SETTLED"
            if candidate_structural
            else "REFUSE"
        )
        if z3_expected != candidate_expected:
            raise WaveControllerError(
                "HOLD",
                "HOLD_WAVE_ENUMERATION_DISAGREEMENT",
                "Z3 and exhaustive local enumeration disagree about the fixture gate.",
            )
        enumeration_cases += 1

    expected = _settlement_from_facts(facts)
    z3_disposition = (
        "SETTLED_REFUTED"
        if z3_structural and z3_refuted
        else "SETTLED"
        if z3_structural
        else "REFUSE"
    )
    if z3_disposition != expected:
        raise WaveControllerError(
            "HOLD",
            "HOLD_WAVE_FACTSET_DISAGREEMENT",
            "The current Z3 result disagrees with the local deterministic gate.",
        )
    return {
        "schema": WAVE_GATE_SCHEMA,
        "facts": input_values,
        "z3_disposition": z3_disposition,
        "enumeration_disposition": expected,
        "enumeration_cases": enumeration_cases,
        "agreement": True,
        "corroboration": CORROBORATION,
        "claim_ceiling": (
            "Z3 and enumeration checked the same bounded local FactSet law; "
            "they do not establish independent evidence or external truth."
        ),
    }


def _plan_fingerprint(
    packet: ProbePacket,
    topology: _TopologyCheck,
    validation: PacketValidation,
    controller_source_sha256: str,
) -> str:
    return _canonical_sha256(
        {
            "controller": WAVE_CONTROLLER_VERSION,
            "controller_source_sha256": controller_source_sha256,
            "wave_definition_id": packet.wave_definition_id,
            "packet_schema": packet.schema,
            "contract_schema_sha256": validation.contract_schema_sha256,
            "topology": topology.as_dict(),
            "adapter_ids": list(_EXPECTED_ADAPTER_IDS),
            "corroboration": CORROBORATION,
            "fixture_mode": FIXTURE_MODE,
        }
    )


def _persist_fixture_wave(
    *,
    packet: ProbePacket,
    validation: PacketValidation,
    topology: _TopologyCheck,
    observations: tuple[ProbeObservation, ...],
    gate: Mapping[str, Any],
    disposition: str,
    controller_source_sha256: str,
    db_path: Path | None,
) -> dict[str, Any]:
    """Append, settle, and reverify one fixture attempt atomically."""

    connection = connect(db_path)
    try:
        with append_only_transaction(connection):
            topology_artifact = record_artifact(
                connection,
                artifact_kind="wave_fixture_topology",
                payload=topology.as_dict(),
                claim_ceiling=CLAIM_CEILING,
            )
            input_artifact = record_artifact(
                connection,
                artifact_kind="wave_fixture_packet",
                payload={
                    "packet": packet.as_dict(),
                    "packet_sha256": packet_sha256(packet),
                    "contract_schema_sha256": validation.contract_schema_sha256,
                    "contract_claim_ceiling": CONTRACT_CLAIM_CEILING,
                    "controller_source_sha256": controller_source_sha256,
                },
                claim_ceiling=CLAIM_CEILING,
            )
            attempt_id = record_wave_attempt(
                connection,
                plan_fingerprint=_plan_fingerprint(
                    packet,
                    topology,
                    validation,
                    controller_source_sha256,
                ),
                topology_artifact_sha256=topology_artifact,
                input_artifact_sha256=input_artifact,
                fixture_mode=True,
                claim_ceiling=CLAIM_CEILING,
            )

            observation_artifacts: list[str] = []
            binding_ids: list[str] = []
            for observation in observations:
                probe = packet.probe_for(observation.probe_kind)
                observation_artifact = record_artifact(
                    connection,
                    artifact_kind="wave_fixture_observation",
                    payload=observation.as_dict(),
                    claim_ceiling=CLAIM_CEILING,
                )
                observation_artifacts.append(observation_artifact)

                # The fixture does execute this local code, but this asset
                # ledger intentionally records the adapter and MMM only as
                # bound references.  That prevents a later reader from
                # inflating an in-process fake call into an external skill,
                # MMM, model, or provider invocation.
                adapter_asset = record_artifact(
                    connection,
                    artifact_kind="wave_fixture_adapter_asset",
                    payload={
                        "asset_id": observation.adapter_id,
                        "asset_kind": "local_fake_adapter",
                        "adapter_class": _EXPECTED_ADAPTER_TYPES[
                            PROBE_KINDS.index(observation.probe_kind)
                        ].__name__,
                        "adapter_source_claim_ceiling": ADAPTER_CLAIM_CEILING,
                    },
                    claim_ceiling=CLAIM_CEILING,
                )
                adapter_reference = record_artifact(
                    connection,
                    artifact_kind="wave_fixture_adapter_reference",
                    payload={
                        "packet_sha256": packet_sha256(packet),
                        "probe_kind": observation.probe_kind,
                        "probe_sha256": observation.probe_sha256,
                        "observation_artifact_sha256": observation_artifact,
                    },
                    claim_ceiling=CLAIM_CEILING,
                )
                binding_ids.append(
                    record_asset_binding(
                        connection,
                        attempt_id=attempt_id,
                        council_id=packet.wave_definition_id,
                        member_id=probe.node_id,
                        asset_id=observation.adapter_id,
                        purpose="local_fake_adapter_reference",
                        binding_state="bound_reference",
                        fixture_mode=True,
                        asset_artifact_sha256=adapter_asset,
                        reference_artifact_sha256=adapter_reference,
                        claim_ceiling=CLAIM_CEILING,
                    )
                )

                # A packet's MMM digest is a reference fingerprint only.  No
                # MMM contents, skill procedure, provider, or model is loaded
                # or invoked by this controller.
                mmm_asset = record_artifact(
                    connection,
                    artifact_kind="wave_fixture_mmm_digest_reference",
                    payload={
                        "asset_id": f"mmm-sha256:{probe.mmm_sha256}",
                        "mmm_sha256": probe.mmm_sha256,
                        "status": "reference_digest_only",
                    },
                    claim_ceiling=CLAIM_CEILING,
                )
                mmm_reference = record_artifact(
                    connection,
                    artifact_kind="wave_fixture_mmm_packet_reference",
                    payload={
                        "packet_sha256": packet_sha256(packet),
                        "probe_kind": probe.kind,
                        "node_id": probe.node_id,
                        "constrained_input_sha256": probe.constrained_input_sha256,
                    },
                    claim_ceiling=CLAIM_CEILING,
                )
                binding_ids.append(
                    record_asset_binding(
                        connection,
                        attempt_id=attempt_id,
                        council_id=packet.wave_definition_id,
                        member_id=probe.node_id,
                        asset_id=f"mmm-sha256:{probe.mmm_sha256}",
                        purpose="reference_only_mmm_digest",
                        binding_state="bound_reference",
                        fixture_mode=True,
                        asset_artifact_sha256=mmm_asset,
                        reference_artifact_sha256=mmm_reference,
                        claim_ceiling=CLAIM_CEILING,
                    )
                )

            gate_artifact = record_artifact(
                connection,
                artifact_kind="wave_fixture_factset_gate",
                payload=dict(gate),
                claim_ceiling=CLAIM_CEILING,
            )
            # The ledger must preserve the negative meaning of a bounded
            # counterexample.  The existing state vocabulary has no separate
            # ``REFUTED`` value, so it is stored as ``REFUSE`` with its exact
            # counterexample reason code rather than being normalized to a
            # positive ``SETTLED`` state.
            state_outcome = "SETTLED" if disposition == "SETTLED" else "REFUSE"
            reason_code = (
                "SETTLED_REFUTED_LOCAL_COUNTEREXAMPLE"
                if disposition == "SETTLED_REFUTED"
                else "SETTLED_LOCAL_FIXTURE_FACTSET"
            )
            receipt_artifact = record_artifact(
                connection,
                artifact_kind="wave_fixture_receipt",
                payload={
                    "schema": WAVE_RECEIPT_SCHEMA,
                    "controller_source_sha256": controller_source_sha256,
                    "attempt_id": attempt_id,
                    "packet_sha256": packet_sha256(packet),
                    "topology_artifact_sha256": topology_artifact,
                    "input_artifact_sha256": input_artifact,
                    "observation_artifact_sha256s": observation_artifacts,
                    "binding_ids": sorted(binding_ids),
                    "gate_artifact_sha256": gate_artifact,
                    "disposition": disposition,
                    "reason_code": reason_code,
                    "promotion_allowed": False,
                    "corroboration": CORROBORATION,
                    "external_assets": "not_invoked",
                },
                claim_ceiling=CLAIM_CEILING,
            )
            settlement_id = record_wave_settlement(
                connection,
                attempt_id=attempt_id,
                outcome=state_outcome,
                reason_code=reason_code,
                gate_artifact_sha256=gate_artifact,
                receipt_artifact_sha256=receipt_artifact,
                claim_ceiling=CLAIM_CEILING,
            )
            verified = verify_wave_attempt(connection, attempt_id)
            settlement = verified.get("settlement")
            if not isinstance(settlement, Mapping) or settlement.get("settlement_id") != settlement_id:
                raise StateError("CB Light wave settlement could not be reverified")
            if settlement.get("outcome") != state_outcome or settlement.get("reason_code") != reason_code:
                raise StateError("CB Light wave settlement result differs from the local gate")
        return {
            "attempt_id": attempt_id,
            "controller_source_sha256": controller_source_sha256,
            "settlement_id": settlement_id,
            "state_outcome": state_outcome,
            "topology_artifact_sha256": topology_artifact,
            "input_artifact_sha256": input_artifact,
            "gate_artifact_sha256": gate_artifact,
            "receipt_artifact_sha256": receipt_artifact,
            "observation_artifact_sha256s": observation_artifacts,
            "binding_ids": sorted(binding_ids),
            "state_verification": {
                "schema": verified["schema"],
                "schema_version": verified["schema_version"],
                "binding_count": len(verified["bindings"]),
                "retained_state_integrity_verified": True,
                "independent_semantic_proof": "not_claimed",
            },
        }
    finally:
        connection.close()


def run_fixture_wave(
    raw_packet: Any,
    *,
    db_path: Path | None = None,
    adapter_factory: Callable[[], Iterable[Any]] = fixture_observation_adapters,
    topology_edges: Sequence[Sequence[str]] | None = None,
) -> dict[str, Any]:
    """Run the bounded CB Light fixture wave and return an explicit receipt.

    ``adapter_factory`` and ``topology_edges`` are in-process test seams only;
    neither is accepted by the packet/CLI.  This keeps every public user input
    inside the strict Pydantic envelope and prevents topology or adapter choice
    from becoming an untrusted authority surface.
    """

    validation = validate_probe_packet(raw_packet)
    if not validation.is_validated:
        return _result(
            validation.disposition,
            validation.reason_code,
            validation.detail,
            persisted=False,
            **_safe_packet_fields(validation),
        )
    packet = validation.packet
    assert packet is not None

    try:
        controller_source_sha256 = _controller_source_sha256()
        topology = _check_fixed_topology(topology_edges)
        observations = _run_exactly_three_adapters(packet, adapter_factory)
        facts = FixtureFactSet(
            packet_valid=True,
            fixed_topology_acyclic=True,
            exact_three_adapters=len(observations) == len(PROBE_KINDS),
            observations_bound_to_packet=all(
                observation.packet_sha256 == packet_sha256(packet)
                for observation in observations
            ),
            all_observations_non_authoritative=all(
                observation.authority == OBSERVATION_AUTHORITY for observation in observations
            ),
            counterexample_present=_counterexample_present(packet),
        )
        gate = _z3_enumeration_check(facts)
        disposition = _settlement_from_facts(facts)
        if not _is_structurally_terminal_fixture_disposition(disposition):
            raise WaveControllerError(
                "REFUSE",
                "REFUSE_WAVE_FACTSET_UNSATISFIED",
                "The local fixture FactSet did not satisfy its deterministic structural gate.",
            )
        persisted = _persist_fixture_wave(
            packet=packet,
            validation=validation,
            topology=topology,
            observations=observations,
                gate=gate,
            disposition=disposition,
            controller_source_sha256=controller_source_sha256,
            db_path=db_path,
        )
    except WaveControllerError as exc:
        return _result(
            exc.disposition,
            exc.reason_code,
            exc.detail,
            persisted=False,
            packet_sha256=packet_sha256(packet),
            contract_schema_sha256=validation.contract_schema_sha256,
        )
    except StateError as exc:
        return _result(
            "HOLD",
            "HOLD_WAVE_STATE_WRITE_OR_VERIFY_FAILED",
            str(exc),
            persisted=False,
            packet_sha256=packet_sha256(packet),
            contract_schema_sha256=validation.contract_schema_sha256,
        )
    except OSError as exc:
        return _result(
            "HOLD",
            "HOLD_WAVE_STATE_UNAVAILABLE",
            str(exc),
            persisted=False,
            packet_sha256=packet_sha256(packet),
            contract_schema_sha256=validation.contract_schema_sha256,
        )

    return _result(
        disposition,
        (
            "SETTLED_REFUTED_LOCAL_COUNTEREXAMPLE"
            if disposition == "SETTLED_REFUTED"
            else "SETTLED_LOCAL_FIXTURE_FACTSET"
        ),
        (
            "The sealed local falsifier fact produced a synthetic refuted fixture result."
            if disposition == "SETTLED_REFUTED"
            else "The bounded local FactSet settled the synthetic fixture without a counterexample."
        ),
        persisted=True,
        packet_id=packet.packet_id,
        wave_definition_id=packet.wave_definition_id,
        fixture_claim_outcome=(
            "LOCAL_COUNTEREXAMPLE_BOUND"
            if disposition == "SETTLED_REFUTED"
            else "NO_LOCAL_COUNTEREXAMPLE"
        ),
        packet_sha256=packet_sha256(packet),
        contract_schema_sha256=validation.contract_schema_sha256,
        fact_set=facts.as_dict(),
        gate=dict(gate),
        executed_local_adapters=[observation.adapter_id for observation in observations],
        **persisted,
    )


def run_fixture_wave_file(
    request_path: Path,
    *,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Parse one local JSON request before opening or creating a state DB."""

    try:
        raw = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _result(
            "REFUSE",
            "REFUSE_WAVE_REQUEST_FILE_INVALID",
            f"Cannot parse the local wave request: {exc}",
            persisted=False,
        )
    return run_fixture_wave(raw, db_path=db_path)


__all__ = [
    "CLAIM_CEILING",
    "CORROBORATION",
    "FIXTURE_MODE",
    "FixtureFactSet",
    "WAVE_CONTROLLER_VERSION",
    "WAVE_GATE_SCHEMA",
    "WAVE_RECEIPT_SCHEMA",
    "WAVE_RESULT_SCHEMA",
    "WaveControllerError",
    "run_fixture_wave",
    "run_fixture_wave_file",
]
