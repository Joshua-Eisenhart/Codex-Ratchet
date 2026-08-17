"""A fixed finite-state rewrite Mini-Lev for the contained CB Light runtime.

The request chooses only one state and one label from the controller-owned
carrier.  It cannot provide a rewrite theory, machine topology, or executable
source.  This is deliberately a second operation shape beside the polynomial
bridge, while retaining the same local parent and append-only attempt route.
"""

from __future__ import annotations

import hashlib
from importlib import metadata
import json
import sqlite3
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, NamedTuple

from hookkernel.cb_light_domain import canonical_json, compile_domain, sha256_bytes
from hookkernel.cb_light_minilev_state import SUCCESS, record_attempt
from hookkernel.cb_light_runtime import ROOT, MANDATED_INTERPRETER, same_declared_interpreter
from hookkernel.cb_light_state import StateError, append_only_transaction, connect


REQUEST_SCHEMA = "constraintbox.mini-lev-transition-request.v1"
RESULT_SCHEMA = "constraintbox.mini-lev-transition-result.v1"
TASK = "mini_lev.finite_state_rewrite_transition.v1"
PARENT_CANDIDATE_ID = "pydantic"
PARENT_OPERATION_CONTRACT = {
    "candidate_id": PARENT_CANDIDATE_ID,
    "registry_tool_id": "python.pydantic",
    "required_roles": (
        "strict_typed_hostile_input_boundary",
        "bounded_request_normalization",
    ),
    "generic_corpus_selection_required": False,
}
REQUIRED_OPERATIONAL_AVAILABILITY_TOOLS = (
    "pypi:automaton",
    "pypi:jsonschema",
    "pypi:maude",
    "pypi:rustworkx",
    "pypi:z3-solver",
)
_OPERATIONAL_AVAILABILITY = frozenset(
    {
        "OPEN_BASIN:ADMISSIBLE_COMPLETION_EXISTS",
        "SELECTED_FOR_WORK:WORK_CONSTRAINTS_SATISFIED",
    }
)
CLAIM_CEILING = (
    "Contained CB Light finite-state Mini-Lev local operation only; no "
    "membership, adoption, portability, provider, CB Heavy, release, model, "
    "or semantic replay claim."
)

_STATES = ("idle", "running", "done")
_RULES = (
    ("start", "idle", "running"),
    ("finish", "running", "done"),
)
_RULE_TARGETS = {(label, initial): target for label, initial, target in _RULES}
_STATE_CODE = {state: index for index, state in enumerate(_STATES)}
_ACTION_CODE = {label: index for index, (label, _, _) in enumerate(_RULES)}
_FIXED_CARRIER = {
    "states": list(_STATES),
    "terminal_states": ["done"],
    "rules": [
        {"label": label, "lhs": initial, "rhs": target}
        for label, initial, target in _RULES
    ],
}
_CARRIER_SHA256 = sha256_bytes(canonical_json(_FIXED_CARRIER))
_MAUDE_MODULE_NAME = f"CB_LIGHT_TRANSITION_{_CARRIER_SHA256[:16].upper()}"
_MAUDE_SOURCE = (
    f"mod {_MAUDE_MODULE_NAME} is "
    "sorts State . "
    "ops idle running done : -> State . "
    "rl [start] : idle => running . "
    "rl [finish] : running => done . "
    "endm"
)

_REQUEST_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://constraintbox.local/schema/mini-lev-transition-request-v1",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema",
        "bridge_request_id",
        "candidate_operation_id",
        "task",
        "payload",
    ],
    "properties": {
        "schema": {"const": REQUEST_SCHEMA},
        "bridge_request_id": {
            "type": "string",
            "minLength": 1,
            "maxLength": 128,
            "pattern": "^[A-Za-z0-9._:-]+$",
        },
        "candidate_operation_id": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "task": {"const": TASK},
        "payload": {
            "type": "object",
            "additionalProperties": False,
            "required": ["initial_state", "rule_label", "claimed_target_state"],
            "properties": {
                "initial_state": {"enum": list(_STATES)},
                "rule_label": {"enum": ["start", "finish"]},
                "claimed_target_state": {"enum": list(_STATES)},
            },
        },
    },
}


class TransitionMiniLevError(RuntimeError):
    """A typed disposition that is returned before the append-only write."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail


class _TransitionPayload:
    def __init__(self, initial_state: str, rule_label: str, claimed_target_state: str) -> None:
        self.initial_state = initial_state
        self.rule_label = rule_label
        self.claimed_target_state = claimed_target_state

    def as_dict(self) -> dict[str, str]:
        return {
            "initial_state": self.initial_state,
            "rule_label": self.rule_label,
            "claimed_target_state": self.claimed_target_state,
        }


class _TransitionRequest:
    def __init__(
        self,
        schema_name: str,
        bridge_request_id: str,
        candidate_operation_id: str,
        task: str,
        payload: _TransitionPayload,
    ) -> None:
        self.schema_name = schema_name
        self.bridge_request_id = bridge_request_id
        self.candidate_operation_id = candidate_operation_id
        self.task = task
        self.payload = payload

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema_name,
            "bridge_request_id": self.bridge_request_id,
            "candidate_operation_id": self.candidate_operation_id,
            "task": self.task,
            "payload": self.payload.as_dict(),
        }


class _ParentSelectionTriple(NamedTuple):
    snapshot_id: str
    probe_run_id: str
    selection_id: str


def _result(disposition: str, reason_code: str, *, detail: str) -> dict[str, Any]:
    return {
        "schema": RESULT_SCHEMA,
        "disposition": disposition,
        "reason_code": reason_code,
        "detail": detail,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def _validate_request(raw: Mapping[str, Any]) -> _TransitionRequest:
    """Run JSON Schema and Pydantic independently, with lazy dependency use."""

    value = dict(raw)
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
    except ModuleNotFoundError as exc:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_JSONSCHEMA_RUNTIME_UNAVAILABLE",
            "The declared JSON Schema boundary is unavailable in this runtime.",
        ) from exc
    try:
        Draft202012Validator(_REQUEST_JSON_SCHEMA).validate(value)
    except JsonSchemaValidationError as exc:
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_JSON_SCHEMA_INVALID",
            f"Independent JSON Schema boundary refused request: {exc.message}",
        ) from exc

    try:
        from pydantic import BaseModel, ConfigDict, Field, ValidationError
    except ModuleNotFoundError as exc:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PYDANTIC_RUNTIME_UNAVAILABLE",
            "The declared Pydantic typed boundary is unavailable in this runtime.",
        ) from exc

    class PayloadModel(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

        initial_state: Literal["idle", "running", "done"]
        rule_label: Literal["start", "finish"]
        claimed_target_state: Literal["idle", "running", "done"]

    class RequestModel(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True, strict=True, populate_by_name=True)

        schema_name: Literal[REQUEST_SCHEMA] = Field(alias="schema")
        bridge_request_id: str = Field(
            min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$"
        )
        candidate_operation_id: str = Field(pattern=r"^[0-9a-f]{64}$")
        task: Literal[TASK]
        payload: PayloadModel

    try:
        parsed = RequestModel.model_validate(value, strict=True)
    except ValidationError as exc:
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_TYPED_BOUNDARY_INVALID",
            f"Pydantic typed boundary refused request: {exc}",
        ) from exc
    return _TransitionRequest(
        parsed.schema_name,
        parsed.bridge_request_id,
        parsed.candidate_operation_id,
        parsed.task,
        _TransitionPayload(
            parsed.payload.initial_state,
            parsed.payload.rule_label,
            parsed.payload.claimed_target_state,
        ),
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _distribution_version(distribution: str, fallback: str = "unknown") -> str:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return fallback


_EXECUTING_SOURCE_LABELS = {
    "transition_mini_lev.py": "light_runtime/src/constraintbox/transition_mini_lev.py",
    "core_cli.py": "light_runtime/src/constraintbox/core_cli.py",
    "core_tools.py": "light_runtime/src/constraintbox/core_tools.py",
    "control_plane.py": "light_runtime/src/constraintbox/control_plane.py",
    "cb_light_probes.py": "light_runtime/src/constraintbox/cb_light_probes.py",
    "core_tool_registry_v9.json": "config/core_tool_registry_v9.json",
    "cb_light_domain.py": "light_runtime/src/hookkernel/cb_light_domain.py",
    "cb_light_minilev_state.py": "light_runtime/src/hookkernel/cb_light_minilev_state.py",
    "cb_light_runtime.py": "light_runtime/src/hookkernel/cb_light_runtime.py",
    "cb_light_state.py": "light_runtime/src/hookkernel/cb_light_state.py",
}


def _executing_source_paths() -> dict[str, Path]:
    """Return the actual package files participating in this transition.

    The labels deliberately use checkout-relative identities.  A wheel may
    execute from site-packages, but it must be byte-identical to the logical
    source named by the current checkout manifest before it may write state.
    """

    from . import cb_light_probes, control_plane, core_cli, core_tools
    from hookkernel import (
        cb_light_domain,
        cb_light_minilev_state,
        cb_light_runtime,
        cb_light_state,
    )

    return {
        "transition_mini_lev.py": Path(__file__),
        "core_cli.py": Path(core_cli.__file__ or ""),
        "core_tools.py": Path(core_tools.__file__ or ""),
        "control_plane.py": Path(control_plane.__file__ or ""),
        "cb_light_probes.py": Path(cb_light_probes.__file__ or ""),
        # The registry is an execution input, so bind the registry that this
        # installed module would actually read rather than a legacy checkout.
        "core_tool_registry_v9.json": Path(__file__).with_name("core_tool_registry_v9.json"),
        "cb_light_domain.py": Path(cb_light_domain.__file__ or ""),
        "cb_light_minilev_state.py": Path(cb_light_minilev_state.__file__ or ""),
        "cb_light_runtime.py": Path(cb_light_runtime.__file__ or ""),
        "cb_light_state.py": Path(cb_light_state.__file__ or ""),
    }


def _attest_executing_source_custody() -> tuple[dict[str, str], str]:
    """Fail closed unless checkout manifest and executing package agree.

    This is custody of the operation code, not semantic replay.  Both the
    checkout logical file and the currently imported package file must match
    the same generated manifest digest.  A missing manifest is a HOLD because
    execution cannot establish which generated lifecycle it belongs to.
    """

    manifest_path = ROOT / "config" / "cb_light_tools_v1.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = manifest["source_hashes"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_SOURCE_MANIFEST_UNAVAILABLE",
            "The current CB Light generated source manifest is unavailable or invalid.",
        ) from exc
    if not isinstance(expected, dict):
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_SOURCE_MANIFEST_UNAVAILABLE",
            "The current CB Light generated source manifest has no source hash map.",
        )
    manifest_identity = dict(manifest)
    manifest_sha256 = manifest_identity.pop("manifest_sha256", None)
    if (
        manifest.get("schema") != "constraintbox.cb-light-tool-manifest.v1"
        or not isinstance(manifest_sha256, str)
        or len(manifest_sha256) != 64
        or sha256_bytes(canonical_json(manifest_identity)) != manifest_sha256
    ):
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_SOURCE_MANIFEST_IDENTITY_DRIFT",
            "The current CB Light generated manifest schema or identity digest is invalid.",
        )

    executing_paths = _executing_source_paths()
    observed: dict[str, str] = {}
    for local_name, logical_name in _EXECUTING_SOURCE_LABELS.items():
        expected_digest = expected.get(logical_name)
        checkout_path = ROOT / logical_name
        executing_path = executing_paths[local_name]
        if not isinstance(expected_digest, str) or len(expected_digest) != 64:
            raise TransitionMiniLevError(
                "HOLD_TRANSITION_SOURCE_MANIFEST_STALE",
                f"The generated manifest does not bind {logical_name}.",
            )
        try:
            checkout_digest = _sha256_file(checkout_path)
            executing_digest = _sha256_file(executing_path)
        except OSError as exc:
            raise TransitionMiniLevError(
                "HOLD_TRANSITION_EXECUTING_SOURCE_UNREADABLE",
                f"Cannot read executing or checkout source for {logical_name}.",
            ) from exc
        if checkout_digest != expected_digest or executing_digest != expected_digest:
            raise TransitionMiniLevError(
                "HOLD_TRANSITION_EXECUTING_SOURCE_DRIFT",
                f"Executing source custody differs from the current manifest for {logical_name}.",
            )
        observed[logical_name] = executing_digest
    return observed, sha256_bytes(canonical_json(observed))


def _parent_operation_contract() -> dict[str, Any]:
    from .core_tools import load_registry

    registry = load_registry()
    tool = next(
        (
            row
            for row in registry["tools"]
            if row.get("id") == PARENT_OPERATION_CONTRACT["registry_tool_id"]
        ),
        None,
    )
    required_roles = set(PARENT_OPERATION_CONTRACT["required_roles"])
    observed_roles = tool.get("cb_roles") if isinstance(tool, dict) else None
    if (
        not isinstance(tool, dict)
        or tool.get("distribution") != PARENT_CANDIDATE_ID
        or not isinstance(observed_roles, list)
        or not required_roles.issubset(set(observed_roles))
    ):
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_ROLE_CONTRACT_DRIFT",
            "The packaged Pydantic registry no longer declares the required typed-boundary roles.",
        )
    return {
        "candidate_id": PARENT_CANDIDATE_ID,
        "registry_tool_id": PARENT_OPERATION_CONTRACT["registry_tool_id"],
        "required_roles": sorted(required_roles),
        "generic_corpus_selection_required": False,
    }


def _current_light_python_version() -> str:
    return ".".join(map(str, sys.version_info[:3]))


def _current_parent_binding() -> tuple[str, str, str, str]:
    """Rebind a stored parent to the producer currently executing.

    This proves custody of the inputs used for the existing operation ID.  It
    intentionally does not re-run the Pydantic decision from unavailable
    original request bytes.
    """

    from . import control_plane

    try:
        model, _ = control_plane._request_model()
        schema_sha256 = sha256_bytes(canonical_json(model.model_json_schema(by_alias=True)))
        pin_sha256 = control_plane.sha256_file(control_plane.PIN_FILE)
        runtime_sha256 = sha256_bytes(canonical_json(control_plane._runtime_attestation()))
        source_sha256 = control_plane.sha256_file(Path(control_plane.__file__ or ""))
    except Exception as exc:  # current producer must fail closed at this boundary
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_PRODUCER_UNAVAILABLE",
            "The current control-plane producer cannot be attested.",
        ) from exc
    return schema_sha256, pin_sha256, source_sha256, runtime_sha256


def _assert_parent_is_current(
    connection: Any, parent: Any
) -> None:
    """Require fresh selection/probe/domain bindings without semantic replay."""

    if parent["all_contracts_satisfied"] != 1:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_DECLARED_TOOL_PROBES_UNSATISFIED",
            "The parent selection was not backed by fully satisfied declared-tool probes.",
        )
    if not same_declared_interpreter(str(parent["probe_interpreter"]), MANDATED_INTERPRETER):
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_PROBE_RUNTIME_DRIFT",
            "The parent probe did not run under the contained CB Light interpreter.",
        )
    if str(parent["probe_python_version"]) != _current_light_python_version():
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_PROBE_PYTHON_DRIFT",
            "The parent probe Python version differs from the current runtime.",
        )
    try:
        current_domain = compile_domain(interpreter=str(MANDATED_INTERPRETER))
    except Exception as exc:  # domain bundle is an external custody input here
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_CURRENT_DOMAIN_UNAVAILABLE",
            "The current CB Light proposal domain cannot be compiled for parent verification.",
        ) from exc
    if str(parent["source_manifest_sha256"]) != current_domain["source_manifest_sha256"]:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_DOMAIN_SOURCE_DRIFT",
            "The parent selection is bound to a different current CB Light domain manifest.",
        )
    latest = connection.execute(
        "SELECT selection_id FROM selection_run ORDER BY captured_at DESC, rowid DESC LIMIT 1"
    ).fetchone()
    if latest is None or str(latest["selection_id"]) != str(parent["selection_id"]):
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_SELECTION_STALE",
            "The parent candidate evaluation is not bound to the latest selection run.",
        )
    try:
        from .cb_light_probes import run_core_probe_matrix

        current_matrix = run_core_probe_matrix()
    except Exception as exc:  # subprocess/core-probe failures are holds, never authority
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_CURRENT_DECLARED_TOOL_PROBES_UNAVAILABLE",
            "The current declared-tool probe matrix could not be recomputed.",
        ) from exc
    if not current_matrix.get("all_contracts_satisfied"):
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_CURRENT_DECLARED_TOOL_PROBES_UNSATISFIED",
            "The current declared-tool probe matrix is not fully satisfied.",
        )
    current_python = str(current_matrix.get("python_version", ""))
    if current_python != _current_light_python_version():
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_CURRENT_DECLARED_TOOL_PROBE_PYTHON_DRIFT",
            "The freshly recomputed declared-tool matrix does not report the current Python version.",
        )
    current_interpreter = str(current_matrix.get("interpreter", ""))
    if not same_declared_interpreter(current_interpreter, MANDATED_INTERPRETER):
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_CURRENT_DECLARED_TOOL_PROBE_RUNTIME_DRIFT",
            "The freshly recomputed declared-tool matrix did not run in the contained interpreter.",
        )
    for key in ("contract_set_sha256", "source_set_sha256", "evidence_set_sha256"):
        if str(parent[key]) != str(current_matrix.get(key, "")):
            raise TransitionMiniLevError(
                "HOLD_TRANSITION_PARENT_PROBE_EVIDENCE_DRIFT",
                f"The parent {key} differs from the freshly recomputed declared-tool matrix.",
            )


def _assert_parent_producer_binding(parent: Any) -> None:
    schema_sha256, pin_sha256, source_sha256, runtime_sha256 = _current_parent_binding()
    if str(parent["schema_sha256"]) != schema_sha256:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_REQUEST_SCHEMA_DRIFT",
            "The parent request schema does not match the current control-plane schema.",
        )
    if str(parent["candidate_pin_sha256"]) != pin_sha256:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_PIN_DRIFT",
            "The parent candidate pin digest does not match the current pin file.",
        )
    if str(parent["source_sha256"]) != source_sha256:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_CONTROL_PLANE_SOURCE_DRIFT",
            "The parent control-plane source digest does not match the executing producer.",
        )
    expected_operation_id = sha256_bytes(
        canonical_json(
            {
                "request_sha256": str(parent["request_sha256"]),
                "schema_sha256": schema_sha256,
                "candidate_pin_sha256": pin_sha256,
                "selection_id": str(parent["selection_id"]),
                "source_sha256": source_sha256,
                "runtime_sha256": runtime_sha256,
            }
        )
    )
    if str(parent["operation_id"]) != expected_operation_id:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_OPERATION_BINDING_DRIFT",
            "The parent operation id no longer binds the current producer custody inputs.",
        )


def _load_parent_and_cohort(
    connection: Any, request: _TransitionRequest
) -> tuple[_ParentSelectionTriple, dict[str, str], dict[str, Any]]:
    parent_contract = _parent_operation_contract()
    parent = connection.execute(
        """
        SELECT
            candidate_evaluation.operation_id,
            candidate_evaluation.candidate_id,
            candidate_evaluation.disposition,
            candidate_evaluation.request_sha256,
            candidate_evaluation.schema_sha256,
            candidate_evaluation.candidate_pin_sha256,
            candidate_evaluation.source_sha256,
            candidate_evaluation.snapshot_id AS candidate_snapshot_id,
            candidate_evaluation.probe_run_id AS candidate_probe_run_id,
            candidate_evaluation.selection_id AS candidate_selection_id,
            selection_run.selection_id,
            selection_run.snapshot_id,
            selection_run.probe_run_id,
            domain_snapshot.source_manifest_sha256,
            probe_run.all_contracts_satisfied,
            probe_run.interpreter AS probe_interpreter,
            probe_run.python_version AS probe_python_version,
            probe_run.contract_set_sha256,
            probe_run.source_set_sha256,
            probe_run.evidence_set_sha256
        FROM candidate_evaluation
        JOIN selection_run
            ON selection_run.selection_id = candidate_evaluation.selection_id
        JOIN domain_snapshot
            ON domain_snapshot.snapshot_id = selection_run.snapshot_id
        JOIN probe_run
            ON probe_run.run_id = selection_run.probe_run_id
        WHERE candidate_evaluation.operation_id = ?
        """,
        (request.candidate_operation_id,),
    ).fetchone()
    if parent is None:
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_PARENT_OPERATION_UNKNOWN",
            "The supplied candidate operation does not exist in this CB Light SQLite state.",
        )
    if parent["disposition"] != "CANDIDATE_EVALUATED_LOCAL":
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_PARENT_DISPOSITION",
            "The parent operation is not a local candidate evaluation.",
        )
    if parent["candidate_id"] != PARENT_CANDIDATE_ID:
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_PARENT_CANDIDATE",
            "This contained transition Mini-Lev requires the typed Pydantic parent.",
        )
    if (
        str(parent["candidate_snapshot_id"]) != str(parent["snapshot_id"])
        or str(parent["candidate_probe_run_id"]) != str(parent["probe_run_id"])
        or str(parent["candidate_selection_id"]) != str(parent["selection_id"])
    ):
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_PARENT_SELECTION_TRIPLE_DRIFT",
            "The candidate evaluation no longer agrees with its joined selection triple.",
        )
    _assert_parent_is_current(connection, parent)
    _assert_parent_producer_binding(parent)
    parent_selection = _ParentSelectionTriple(
        snapshot_id=str(parent["snapshot_id"]),
        probe_run_id=str(parent["probe_run_id"]),
        selection_id=str(parent["selection_id"]),
    )
    selection_id = parent_selection.selection_id
    placeholders = ", ".join("?" for _ in REQUIRED_OPERATIONAL_AVAILABILITY_TOOLS)
    rows = connection.execute(
        f"""
        SELECT candidate_id, disposition, reason_code FROM selection_decision
        WHERE selection_id = ? AND candidate_id IN ({placeholders})
        """,
        (selection_id, *REQUIRED_OPERATIONAL_AVAILABILITY_TOOLS),
    ).fetchall()
    cohort = {
        str(row["candidate_id"]): f"{row['disposition']}:{row['reason_code']}"
        for row in rows
    }
    unavailable = [
        candidate_id
        for candidate_id in REQUIRED_OPERATIONAL_AVAILABILITY_TOOLS
        if cohort.get(candidate_id) not in _OPERATIONAL_AVAILABILITY
    ]
    if unavailable:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_REQUIRED_TOOL_COHORT_UNAVAILABLE",
            "The contained transition Mini-Lev requires operational availability: "
            + ", ".join(unavailable),
        )
    return parent_selection, cohort, parent_contract


def _topology() -> tuple[dict[str, Any], str]:
    try:
        import rustworkx
    except ModuleNotFoundError as exc:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_RUSTWORKX_RUNTIME_UNAVAILABLE",
            "The declared Rustworkx topology gate is unavailable in this runtime.",
        ) from exc
    labels = (
        "typed-envelope",
        "maude-rewrite-witness",
        "automaton-crosscheck",
        "z3-transition-gate",
    )
    graph = rustworkx.PyDiGraph()
    nodes = graph.add_nodes_from(labels)
    graph.add_edges_from_no_data(
        ((nodes[0], nodes[1]), (nodes[1], nodes[2]), (nodes[2], nodes[3]))
    )
    order = [graph[index] for index in rustworkx.topological_sort(graph)]
    topology = {
        "schema": "constraintbox.mini-lev-transition-topology.v1",
        "nodes": list(labels),
        "edges": [[labels[0], labels[1]], [labels[1], labels[2]], [labels[2], labels[3]]],
        "topological_order": order,
        "edge_count": graph.num_edges(),
    }
    if order != list(labels) or graph.num_edges() != 3:
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_TOPOLOGY_INVALID",
            "The fixed transition Mini-Lev topology did not remain an ordered three-edge DAG.",
        )
    return topology, sha256_bytes(canonical_json(topology))


def _maude_witness(payload: _TransitionPayload) -> dict[str, Any]:
    try:
        import maude
    except ModuleNotFoundError as exc:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_MAUDE_RUNTIME_UNAVAILABLE",
            "The declared Maude rewrite witness is unavailable in this runtime.",
        ) from exc
    initialized = maude.init(
        loadPrelude=False, randomSeed=0, advise=False, handleInterrupts=False
    )
    # Maude is process-global.  A second exact replay may report that this
    # digest-named module already exists; the authoritative check is the exact
    # loaded module inventory below, not an unnecessary second load result.
    maude.input(_MAUDE_SOURCE)
    module = maude.getModule(_MAUDE_MODULE_NAME)
    if module is None:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_MAUDE_MODULE_UNAVAILABLE",
            "The generated fixed transition module was not retrievable from Maude.",
        )
    rules = [
        {
            "label": str(rule.getLabel()),
            "lhs": str(rule.getLhs()),
            "rhs": str(rule.getRhs()),
        }
        for rule in module.getRules()
    ]
    if rules != [
        {"label": label, "lhs": initial, "rhs": target}
        for label, initial, target in _RULES
    ] or list(module.getEquations()):
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_MAUDE_MODULE_INVENTORY_DRIFT",
            "The generated Maude module did not expose exactly the two fixed rules and zero equations.",
        )
    term = module.parseTerm(payload.initial_state)
    applications = list(term.apply(payload.rule_label, minDepth=0, maxDepth=0))
    if len(applications) != 1:
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_MAUDE_RULE_INAPPLICABLE",
            "The requested fixed rule is not applicable at the carrier root state.",
        )
    target = str(applications[0][0])
    expected = _RULE_TARGETS.get((payload.rule_label, payload.initial_state))
    if expected is None or target != expected:
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_MAUDE_EXPECTED_TARGET_MISMATCH",
            "The Maude root rewrite did not equal the fixed-carrier transition relation.",
        )
    return {
        "backend": "maude",
        "version": _distribution_version("maude", str(getattr(maude, "__version__", "unknown"))),
        "initialized": initialized is True or module is not None,
        "module_name": _MAUDE_MODULE_NAME,
        "module_sha256": sha256_bytes(_MAUDE_SOURCE.encode("utf-8")),
        "rules": rules,
        "equation_count": 0,
        "applied_label": payload.rule_label,
        "initial_state": payload.initial_state,
        "target_state": target,
        "root_depth": 0,
    }


def _automaton_witness(payload: _TransitionPayload) -> dict[str, Any]:
    try:
        import automaton
        from automaton.machines import FiniteMachine
    except ModuleNotFoundError as exc:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_AUTOMATON_RUNTIME_UNAVAILABLE",
            "The declared Automaton cross-check is unavailable in this runtime.",
        ) from exc
    machine = FiniteMachine()
    for state in _STATES:
        machine.add_state(state, terminal=state == "done")
    for label, initial, target in _RULES:
        machine.add_transition(initial, target, label)
    machine.initialize(payload.initial_state)
    try:
        machine.process_event(payload.rule_label)
    except Exception as exc:
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_AUTOMATON_EVENT_REFUSED",
            "The requested fixed event is not actionable for the carrier state.",
        ) from exc
    target = str(machine.current_state)
    expected = _RULE_TARGETS.get((payload.rule_label, payload.initial_state))
    if expected is None or target != expected:
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_AUTOMATON_EXPECTED_TARGET_MISMATCH",
            "The Automaton result did not equal the fixed-carrier transition relation.",
        )
    return {
        "backend": "automaton",
        "version": _distribution_version(
            "automaton", str(getattr(automaton, "__version__", "unknown"))
        ),
        "states": list(_STATES),
        "terminal_states": ["done"],
        "event": payload.rule_label,
        "initial_state": payload.initial_state,
        "target_state": target,
        "terminated": bool(machine.terminated),
    }


def _z3_witness(payload: _TransitionPayload) -> dict[str, Any]:
    try:
        import z3
    except ModuleNotFoundError as exc:
        raise TransitionMiniLevError(
            "HOLD_TRANSITION_Z3_RUNTIME_UNAVAILABLE",
            "The declared Z3 transition gate is unavailable in this runtime.",
        ) from exc
    initial = z3.Int("transition_initial")
    action = z3.Int("transition_action")
    target = z3.Int("transition_target")
    solver = z3.Solver()
    solver.add(initial == _STATE_CODE[payload.initial_state])
    solver.add(action == _ACTION_CODE[payload.rule_label])
    solver.add(target == _STATE_CODE[payload.claimed_target_state])
    solver.add(
        z3.Or(
            z3.And(
                initial == _STATE_CODE[source],
                action == _ACTION_CODE[label],
                target == _STATE_CODE[destination],
            )
            for label, source, destination in _RULES
        )
    )
    status = str(solver.check())
    if status != "sat":
        raise TransitionMiniLevError(
            "REFUSE_TRANSITION_Z3_RELATION_UNSAT",
            "The claimed transition is outside the fixed finite-state relation.",
        )
    return {
        "backend": "z3-solver",
        "version": _distribution_version("z3-solver", z3.get_version_string()),
        "status": status,
        "initial_state": payload.initial_state,
        "rule_label": payload.rule_label,
        "claimed_target_state": payload.claimed_target_state,
        "state_codes": _STATE_CODE,
        "action_codes": _ACTION_CODE,
    }


def run_transition_mini_lev(
    raw: Mapping[str, Any], *, db_path: Path
) -> dict[str, Any]:
    """Run and append one finite-state contained-Light Mini-Lev attempt."""

    if not isinstance(raw, Mapping):
        return _result(
            "REFUSE",
            "REFUSE_TRANSITION_REQUEST_MAPPING_REQUIRED",
            detail="The transition Mini-Lev request must be a JSON object.",
        )
    try:
        request = _validate_request(raw)
    except TransitionMiniLevError as exc:
        return _result(
            "HOLD" if exc.reason_code.startswith("HOLD_") else "REFUSE",
            exc.reason_code,
            detail=exc.detail,
        )
    request_sha256 = sha256_bytes(canonical_json(request.as_dict()))
    schema_sha256 = sha256_bytes(canonical_json(_REQUEST_JSON_SCHEMA))
    try:
        _, source_sha256 = _attest_executing_source_custody()
    except TransitionMiniLevError as exc:
        return _result("HOLD", exc.reason_code, detail=exc.detail)
    from hookkernel.cb_light_basin_view import hold_result_if_incomplete

    held = hold_result_if_incomplete()
    if held is not None:
        return {
            **_result("HOLD", held["reason_code"], detail=held["detail"]),
            "basin_view": held["basin_view"],
        }
    try:
        connection = connect(db_path)
    except (OSError, sqlite3.Error) as exc:
        return _result(
            "HOLD",
            "HOLD_TRANSITION_STATE_UNAVAILABLE",
            detail=f"CB Light SQLite state cannot be opened: {exc}",
        )
    try:
        parent_selection, cohort, parent_contract = _load_parent_and_cohort(
            connection, request
        )
        selection_id = parent_selection.selection_id
        topology, topology_sha256 = _topology()
        maude = _maude_witness(request.payload)
        automaton = _automaton_witness(request.payload)
        z3 = _z3_witness(request.payload)
        claimed = request.payload.claimed_target_state
        observed_targets = {
            "maude": maude.get("target_state"),
            "automaton": automaton.get("target_state"),
            "claimed": claimed,
        }
        if len(set(observed_targets.values())) != 1:
            raise TransitionMiniLevError(
                "REFUSE_TRANSITION_BACKEND_TARGET_DISAGREEMENT",
                "Maude, Automaton, and the claimed target did not agree.",
            )
        cohort_sha256 = sha256_bytes(canonical_json(cohort))
        result_material = {
            "schema": RESULT_SCHEMA,
            "task": TASK,
            "bridge_request_id": request.bridge_request_id,
            "candidate_operation_id": request.candidate_operation_id,
            "selection_id": selection_id,
            "parent_contract": parent_contract,
            "cohort": cohort,
            "topology": topology,
            "fixed_carrier": _FIXED_CARRIER,
            "fixed_carrier_sha256": _CARRIER_SHA256,
            "maude": maude,
            "automaton": automaton,
            "z3": z3,
            "observed_targets": observed_targets,
            "disposition": SUCCESS,
            "reason_code": "MINILEV_FIXED_TRANSITION_MAUDE_AUTOMATON_Z3_BOUND",
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        # Serialize the final authority read with the append.  The expensive
        # probes and finite backends run before the writer lock, but no result
        # may be recorded unless every authority input still matches exactly.
        with append_only_transaction(connection):
            (
                current_parent_selection,
                current_cohort,
                current_parent_contract,
            ) = _load_parent_and_cohort(connection, request)
            if current_parent_selection != parent_selection:
                raise TransitionMiniLevError(
                    "HOLD_TRANSITION_PARENT_SELECTION_TRIPLE_DRIFT",
                    "The parent selection triple changed after backend evaluation.",
                )
            if current_cohort != cohort:
                raise TransitionMiniLevError(
                    "HOLD_TRANSITION_REQUIRED_TOOL_COHORT_DRIFT",
                    "The exact required-tool cohort changed after backend evaluation.",
                )
            if current_parent_contract != parent_contract:
                raise TransitionMiniLevError(
                    "HOLD_TRANSITION_PARENT_ROLE_CONTRACT_DRIFT",
                    "The parent role contract changed after backend evaluation.",
                )
            _, source_sha256_before_write = _attest_executing_source_custody()
            if source_sha256_before_write != source_sha256:
                raise TransitionMiniLevError(
                    "HOLD_TRANSITION_EXECUTING_SOURCE_DRIFT",
                    "Executing transition source changed after the initial custody check.",
                )
            persisted = record_attempt(
                connection,
                bridge_request_id=request.bridge_request_id,
                candidate_operation_id=request.candidate_operation_id,
                request_sha256=request_sha256,
                schema_sha256=schema_sha256,
                source_sha256=source_sha256,
                selection_id=selection_id,
                topology_sha256=topology_sha256,
                cohort_sha256=cohort_sha256,
                result=result_material,
                claim_ceiling=CLAIM_CEILING,
            )
        return {
            **result_material,
            **persisted,
            "request_sha256": request_sha256,
            "schema_sha256": schema_sha256,
            "source_sha256": source_sha256,
            "topology_sha256": topology_sha256,
            "cohort_sha256": cohort_sha256,
        }
    except TransitionMiniLevError as exc:
        return _result(
            "HOLD" if exc.reason_code.startswith("HOLD_") else "REFUSE",
            exc.reason_code,
            detail=exc.detail,
        )
    except StateError as exc:
        return _result(
            "REFUSE",
            "REFUSE_TRANSITION_ATTEMPT_IDENTITY_CONFLICT",
            detail=str(exc),
        )
    finally:
        connection.close()


def run_transition_mini_lev_file(request_path: Path, *, db_path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _result(
            "REFUSE",
            "REFUSE_TRANSITION_REQUEST_INVALID_JSON",
            detail=f"Cannot read transition Mini-Lev JSON request: {exc}",
        )
    return run_transition_mini_lev(raw, db_path=db_path)
