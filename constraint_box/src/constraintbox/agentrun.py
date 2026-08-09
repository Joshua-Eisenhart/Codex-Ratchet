"""One caller-reachable, fail-closed ConstraintBox LLM loop.

This module is deliberately a thin integration layer.  It reuses the tracked
LLM provider/notary, the existing strict proposal controller, the simulation
estate worker and controls, the finite enumeration/Z3 backends, deterministic
discharge, branch retention, and ClaimGate.

The model is an untrusted proposer.  It cannot choose the tool, command,
profile, constraints, retry budget, gate, claim kind, or released text.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .boundary_contract import controller_boundary_context
from .boxrun import BoxRunError, VerifiedBoxRun, verify_box_run
from .branching import BranchLedger
from .constraints import FiniteConstraintProblem, SolverStatus
from .contracts import Disposition, TaskRequest
from .controller import AgentProposalProfile, ConstraintBoxController
from .discharge import Observation, PASS, Policy, Requirement, discharge
from .dualsolve import dual_solve
from .estate import CapabilityState, EstateRunner
from .gate import run_gate
from .intake import IntakeError, canonical_json, parse_json_object
from .proposal_minilev_flow import (
    ClaimGateCallbackResult,
    ClaimGateSignal,
    ProposalCallbackResult,
    ProposalGateCallbackResult,
    ProposalGateSignal,
    ProposalMiniLevCallbacks,
    ProposalMiniLevFlowResult,
    ProposalMiniLevFlowError,
    ProposalSignal,
    run_proposal_minilev_flow,
    verify_proposal_minilev_flow,
)
from .proposal_provider_policy import (
    POLICY_SCHEMA as PROPOSAL_PROVIDER_POLICY_SCHEMA,
    ProposalProviderPolicyError,
    select_proposal_provider,
)
from .simrun import write_receipt_atomic


# Capture the production release checker at import time.  The public runner
# never obtains this callable from user, model, CLI, or run-directory input.
# This does not purport to defend against code already executing with the same
# Python-process privileges; that broader containment is outside this package's
# stated ceiling.
_PRODUCTION_CLAIM_GATE = run_gate


SCHEMA = "constraintbox.agent-run.v2"
TASK_SCHEMA = "constraintbox.agent-task.v2"
PROFILE_ID = "constraintbox.cr-gksl-numpy-density.darwin.v1"
PROPOSAL_TASK_KIND = "agent_proposal"
ALLOWED_CLAIM = "bounded_tool_execution"
MAX_ATTEMPTS = 2
MAX_PROVIDER_OUTPUT_BYTES = 1_048_576
MAX_INSTRUCTION_CHARS = 20_000
PROVIDER_TIMEOUT_SECONDS = 180.0
TOOL_TIMEOUT_SECONDS = 12.0

BOX_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BOX_ROOT.parent
FIXTURE_PATH = BOX_ROOT / "fixtures" / "cr" / "cr_gksl_fixture_v1.json"
EXTERNAL_ESTATE_ROOT = REPO_ROOT / "external_sim_estate" / "legacy_estate_v2"
ESTATE_MANIFEST_PATH = EXTERNAL_ESTATE_ROOT / "sim_estate_v2.json"
MMM_PACKS_DIR = BOX_ROOT / "mmm" / "packs"
WORKER_PATH = EXTERNAL_ESTATE_ROOT / "workers" / "capability_worker.py"
BLOCKER_PATH = EXTERNAL_ESTATE_ROOT / "workers" / "import_blocker.py"
POISONER_PATH = EXTERNAL_ESTATE_ROOT / "workers" / "operation_poisoner.py"

# This first live profile is intentionally exact and local.  Drift parks the
# run; it is never silently reinterpreted as success on a different estate.
PROFILE_PINS = {
    "fixture": "27df1ad2b3e35ae7cc342963bcfe0fe5a0b1a2599cac4b624ca48f8686e6222f",
    # Repinned 2026-08-08, for the second time: the first repin was reverted by an
    # agent restoring an unrelated temporary edit.  estate.py hashes its own source,
    # and 563d1afd50.. predates the v9 import at a99094897, so every `constraintbox
    # run` PARKed on PROFILE_INPUT_DRIFT:estate_controller against the box's own
    # shipped controller.  be2ef0c911.. is the sha256 of estate.py at BOTH HEAD and
    # worktree, verified independently twice.  The other four pins match their files.
    "estate_controller": "be2ef0c911cc9cdecc299969ebf1f2bad1011d734ccbe0a094544cdfdcfb295e",
    "worker": "355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257",
    "import_blocker": "b3e027e60eb963cd8bf143bad4c721b7fd2581508bb62a1d4a7a81970e2b6418",
    "operation_poisoner": "6710454e9f88389f1eb48f5ac0e8dbe79eecfeca6c1f2b5b510fba76936cd3f0",
}
PROFILE_NUMPY_VERSION = "2.3.4"

MMM_PACK_PINS = {
    "claimgate": "07537fe62f4056d7fc8fd3a7708217fa925d9fa2f2e4ff1da97244d5b119b862",
    "constraint-programming": "1ecd4162a42d86ed90d7512d99c2ea515eae0486060003cb9e2abe8b0f63dc6b",
    "cr-ratchet": "cff83646e32bae5c658935fb9fcb322ef1fc25e9c245a5e4c3b07d06ea0eca06",
    "lev-os": "66978f264fabe9da42d420681e2abd7caef22baf7aa7b89ca1bd527f612eb671",
    "nominalist": "380554750988c1af5959cc2e11e94a3c0de4b9bf66088f2edf5e8ac72c528edd",
    "smt": "11a5074a5d4ae999ba41642eaee9748786aab00cc37b06464766fa9a11608886",
}
MMM_PACK_ORDER = (
    "nominalist",
    "constraint-programming",
    "smt",
    "claimgate",
    "cr-ratchet",
    "lev-os",
)

RELEASE_TEXT = (
    "ConstraintBox observed the registered NumPy density worker pass its fixed "
    "local fixture and the positive, dispatch, mutation, replay, import-severance, "
    "and operation-severance controls. Scope: bounded local tool execution only."
)
CLAIM_CEILING = (
    "one fixed local NumPy worker fixture and named controls; no promotion"
)
BOX_HANDOFF_CLAIM_CEILING = (
    "captured local receipt and artifact integrity only; no authentication "
    "against another same-user process and no hostile-code containment"
)

RUN_EXIT_CODES = {
    "RELEASED": 0,
    "REFUSED": 1,
    "PARKED": 4,
    "EVALUATION_ERROR": 5,
}

_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}")
_HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
_CLAIM_VALUES = (
    ALLOWED_CLAIM,
    "scientific_result",
    "canonical_result",
)
_BOOLEAN_GATES = (
    "provider_receipt_admitted",
    "provider_tool_free",
    "strict_intake_eligible",
    "proposal_schema_valid",
    "evidence_ref_matches",
    "falsifier_present",
    "tool_profile_ready",
    "tool_controls_complete",
    "tool_operation_bound",
)
_REQUIRED_TOOL_CONTROLS = frozenset(
    {"positive", "dispatch", "mutation", "replay", "severance", "operation"}
)


class AgentRunError(RuntimeError):
    """The controller could not construct or start the requested run."""


@dataclass(frozen=True)
class AgentTask:
    task_id: str
    instruction: str
    box_receipt_sha256: str
    request_sha256: str
    compiled_user_context_sha256: str
    external_engine_packet_sha256: str
    schema: str = TASK_SCHEMA

    def to_dict(self) -> dict[str, str]:
        return {
            "schema": self.schema,
            "task_id": self.task_id,
            "instruction": self.instruction,
            "box_receipt_sha256": self.box_receipt_sha256,
            "request_sha256": self.request_sha256,
            "compiled_user_context_sha256": (
                self.compiled_user_context_sha256
            ),
            "external_engine_packet_sha256": (
                self.external_engine_packet_sha256
            ),
        }


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    return _sha256_bytes(canonical_json(value))


def _jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return _jsonable(dataclasses.asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(child) for child in value]
    return value


def _write_json(path: Path, value: Any) -> None:
    write_receipt_atomic(path, _jsonable(value))


def load_task(path: Path) -> AgentTask:
    del path
    raise AgentRunError(
        "direct agent task files are disabled; use a verified first-box run"
    )


def _task_from_verified_box(box_run: VerifiedBoxRun) -> AgentTask:
    if _SAFE_ID.fullmatch(box_run.request_id) is None:
        raise AgentRunError("verified box request_id is not a safe bounded identifier")
    try:
        instruction = box_run.request_canonical.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AgentRunError("verified box request is not UTF-8") from exc
    if not instruction or len(instruction) > MAX_INSTRUCTION_CHARS:
        raise AgentRunError(
            f"verified box request must be 1..{MAX_INSTRUCTION_CHARS} characters"
        )
    return AgentTask(
        task_id=box_run.request_id,
        instruction=instruction,
        box_receipt_sha256=box_run.receipt_sha256,
        request_sha256=box_run.request_sha256,
        compiled_user_context_sha256=box_run.context_sha256,
        external_engine_packet_sha256=(
            box_run.external_engine_packet_sha256
        ),
    )


def _proposal_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "proposal_id": {"type": "string"},
            "candidate": {
                "type": "object",
                "properties": {
                    "requested_claim": {
                        "type": "string",
                        "enum": list(_CLAIM_VALUES),
                    },
                    "evidence_ref": {"type": "string"},
                },
                "required": ["requested_claim", "evidence_ref"],
                "additionalProperties": False,
            },
            "falsifiers": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["proposal_id", "candidate", "falsifiers"],
        "additionalProperties": False,
    }


def _profile_paths() -> dict[str, Path]:
    from . import estate

    return {
        "fixture": FIXTURE_PATH,
        "estate_controller": Path(estate.__file__).resolve(),
        "worker": WORKER_PATH,
        "import_blocker": BLOCKER_PATH,
        "operation_poisoner": POISONER_PATH,
    }


def _load_profile_inputs() -> tuple[dict[str, Any], list[str]]:
    observed: dict[str, Any] = {}
    errors: list[str] = []
    for name, path in _profile_paths().items():
        if not path.is_file():
            errors.append(f"PROFILE_INPUT_MISSING:{name}")
            continue
        digest = _sha256_file(path)
        observed[name] = {"path": str(path), "sha256": digest}
        if digest != PROFILE_PINS[name]:
            errors.append(f"PROFILE_INPUT_DRIFT:{name}")

    pack_rows = []
    pack_texts = []
    for name in MMM_PACK_ORDER:
        path = MMM_PACKS_DIR / f"{name}.md"
        if not path.is_file():
            errors.append(f"MMM_PACK_MISSING:{name}")
            continue
        raw = path.read_bytes()
        digest = _sha256_bytes(raw)
        pack_rows.append({"name": name, "path": str(path), "sha256": digest})
        if digest != MMM_PACK_PINS[name]:
            errors.append(f"MMM_PACK_DRIFT:{name}")
        pack_texts.append(raw.decode("utf-8"))

    mmm_text = "\n\n---\n\n".join(pack_texts)
    observed["mmm"] = {
        "packs": pack_rows,
        "sha256": _sha256_bytes(mmm_text.encode("utf-8")),
        "text": mmm_text,
    }
    return observed, errors


def _write_one_capability_manifest(path: Path) -> dict[str, Any]:
    body = {
        "schema": "constraintbox.sim-estate.v2",
        "status": "CONTROLLER_OWNED_PROFILE",
        "promotion_allowed": False,
        "controller_sha256": PROFILE_PINS["estate_controller"],
        "worker_sha256": PROFILE_PINS["worker"],
        "import_blocker_sha256": PROFILE_PINS["import_blocker"],
        "operation_poisoner_sha256": PROFILE_PINS["operation_poisoner"],
        "tiers": [
            {
                "tier_id": "CB1",
                "name": PROFILE_ID,
                "boot_budget_seconds": TOOL_TIMEOUT_SECONDS,
                "capabilities": [
                    {
                        "id": "numpy_density",
                        "required": True,
                        "locked_version": PROFILE_NUMPY_VERSION,
                    }
                ],
            }
        ],
    }
    _write_json(path, body)
    return body


def _tool_profile_errors(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    capabilities = receipt.get("capabilities")
    if not isinstance(capabilities, (list, tuple)) or len(capabilities) != 1:
        return ["TOOL_PROFILE_CARDINALITY"]
    row = capabilities[0]
    controls = row.get("controls", {})
    evidence = row.get("evidence", {})
    if row.get("capability_id") != "numpy_density":
        errors.append("TOOL_PROFILE_ID_MISMATCH")
    if row.get("state") != CapabilityState.READY.value:
        errors.append(f"TOOL_STATE_{row.get('state', 'MISSING')}")
    if row.get("reason") != "all_required_controls_passed":
        errors.append("TOOL_REQUIRED_CONTROLS_NOT_PASSED")
    if set(controls) != _REQUIRED_TOOL_CONTROLS or not all(
        controls.get(name) is True for name in _REQUIRED_TOOL_CONTROLS
    ):
        errors.append("TOOL_CONTROL_SET_INCOMPLETE")
    if row.get("expected_version") != PROFILE_NUMPY_VERSION:
        errors.append("TOOL_EXPECTED_VERSION_MISMATCH")
    if row.get("observed_version") != PROFILE_NUMPY_VERSION:
        errors.append("TOOL_OBSERVED_VERSION_MISMATCH")
    if row.get("worker_sha256") != PROFILE_PINS["worker"]:
        errors.append("TOOL_WORKER_DIGEST_MISMATCH")
    if row.get("fixture_sha256") != PROFILE_PINS["fixture"]:
        errors.append("TOOL_FIXTURE_DIGEST_MISMATCH")
    if evidence.get("operation_severed") != "numpy.linalg.eigvalsh":
        errors.append("TOOL_OPERATION_SEVERANCE_MISSING")
    if "numpy.linalg.eigvalsh" not in evidence.get("dispatch", []):
        errors.append("TOOL_OPERATION_DISPATCH_MISSING")
    if evidence.get("operation_never_called") is True:
        errors.append("TOOL_OPERATION_NOT_LOAD_BEARING")
    if evidence.get("controls_timed_out"):
        errors.append("TOOL_CONTROL_TIMEOUT")
    if evidence.get("controls_not_measured"):
        errors.append("TOOL_CONTROL_NOT_MEASURED")
    return errors


def _run_fixed_tool(
    run_dir: Path,
    *,
    python_executable: Path | None,
    timeout_seconds: float,
) -> tuple[dict[str, Any], list[str]]:
    manifest_path = run_dir / "controller_profile_manifest.json"
    manifest = _write_one_capability_manifest(manifest_path)
    # The timeout is controller-bounded downward; callers cannot widen the
    # fixed profile's resource ceiling.
    manifest["tiers"][0]["boot_budget_seconds"] = min(
        float(timeout_seconds), TOOL_TIMEOUT_SECONDS
    )
    _write_json(manifest_path, manifest)
    runner = EstateRunner(
        BOX_ROOT,
        manifest_path,
        FIXTURE_PATH,
        python_executable,
    )
    receipt = runner.run_tier("CB1", "acceptance").to_dict()
    wrapped = {
        "schema": "constraintbox.agent-tool-receipt.v1",
        "profile_id": PROFILE_ID,
        "profile_manifest": str(manifest_path),
        "profile_manifest_sha256": _sha256_file(manifest_path),
        "estate_receipt": receipt,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    return wrapped, _tool_profile_errors(receipt)


def _harness_components() -> dict[str, Any]:
    """Return the contained provider/notary components for the Mini-Lev loop.

    The only external runtime inputs are the selected provider executable or
    credential and the separately configured sim-estate operation.  The
    receipt, notary, and provider-gate implementation are carried inside the
    ConstraintBox package so the agent loop does not silently import a parent
    Ratchet checkout.
    """

    from ._provider_harness.gates import gate as provider_gate
    from ._provider_harness.notary import Notary
    from ._provider_harness.providers import (
        CodexLunaProvider,
        CodexSolProvider,
        LocalToolProvider,
        NvidiaProvider,
        OpenRouterProvider,
    )
    from ._provider_harness.runner import run_job
    from ._provider_harness.types import ModelJob, TaskSpec

    return {
        "provider_gate": provider_gate,
        "Notary": Notary,
        "CodexLunaProvider": CodexLunaProvider,
        "CodexSolProvider": CodexSolProvider,
        "LocalToolProvider": LocalToolProvider,
        "NvidiaProvider": NvidiaProvider,
        "OpenRouterProvider": OpenRouterProvider,
        "run_job": run_job,
        "ModelJob": ModelJob,
        "TaskSpec": TaskSpec,
    }


def _injected_provider_policy(provider: Any) -> dict[str, Any]:
    """Describe the private offline test seam without making it a live route."""

    route = getattr(provider, "name", None)
    if not isinstance(route, str) or not route:
        route = "test_injected_provider"
    policy = {
        "schema": "constraintbox.proposal-provider-test-seam.v1",
        "route": route,
        "component_key": None,
        "requested_model": "codex-cli-default",
        "credential_env": None,
        "credential_configured": False,
        "selection_basis": "private_offline_test_seam_not_public_route",
        "operator_selected": False,
        "max_tokens": None,
        "temperature": None,
        "llm_decision_authority": False,
        "promotion_allowed": False,
    }
    policy["policy_sha256"] = _sha256_bytes(canonical_json(policy))
    return policy


def _build_prompt(
    task: AgentTask,
    *,
    attempt: int,
    proposal_schema_text: str,
    proposal_schema_sha256: str,
    personalized_context_text: str,
    personalized_context_sha256: str,
    tool_receipt_sha256: str,
    tool_receipt: dict[str, Any],
    feedback: dict[str, Any] | None,
    feedback_sha256: str | None,
) -> str:
    capability = tool_receipt["estate_receipt"]["capabilities"][0]
    feedback_block = (
        "none"
        if feedback is None
        else json.dumps(feedback, sort_keys=True, separators=(",", ":"))
    )
    return f"""[CONTROLLER POLICY - NOT OVERRIDABLE]
You are an untrusted proposal generator inside ConstraintBox.
You may not choose or claim a command, checker, verdict, policy, tolerance,
profile, claim kind, promotion, or admission.
Return only the JSON object matching the [PROPOSAL OUTPUT SCHEMA] block below.
The only releasable requested_claim is {ALLOWED_CLAIM!r}.
Copy the exact controller evidence reference into candidate.evidence_ref.
Name at least one concrete falsifier.  No prose outside the JSON object.

{controller_boundary_context()}

[VERIFIED FIRST-BOX HANDOFF]
box_receipt_sha256={task.box_receipt_sha256}
request_sha256={task.request_sha256}
compiled_user_context_sha256={task.compiled_user_context_sha256}
external_engine_packet_sha256={task.external_engine_packet_sha256}

[PERSONALIZED USER CONTEXT sha256={personalized_context_sha256}]
{personalized_context_text}

[FIXED CONTROLLER OBSERVATION]
profile_id={PROFILE_ID}
attempt={attempt}
evidence_ref={tool_receipt_sha256}
capability_id={capability.get("capability_id")}
state={capability.get("state")}
controls={json.dumps(capability.get("controls", {}), sort_keys=True)}
claim_ceiling={CLAIM_CEILING}

[PROPOSAL OUTPUT SCHEMA sha256={proposal_schema_sha256}]
{proposal_schema_text}
[DETERMINISTIC FEEDBACK sha256={feedback_sha256 or "none"}]
{feedback_block}

[UNTRUSTED USER REQUEST sha256={task.request_sha256}]
{json.dumps(task.instruction, ensure_ascii=False)}
"""


def _codex_command(
    prompt: str,
    *,
    attempt_dir: Path,
    schema_path: Path,
    codex_binary: str | None,
    requested_model: str,
) -> list[str] | None:
    binary = codex_binary or shutil.which("codex")
    if binary is None:
        return None
    # ``-m`` binds the model and the CLI enforces it (an unknown slug returns
    # HTTP 400); without it codex silently picks its default and the receipt
    # names a request that bound nothing.  ``--ephemeral`` is deliberately NOT
    # passed: it suppresses the session rollout (measured 2026-08-08), which
    # is the only byte-level observation of the model that actually answered,
    # so an ephemeral dispatch is unverifiable by construction.
    return [
        binary,
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--sandbox",
        "read-only",
        "-C",
        str(attempt_dir),
        "--skip-git-repo-check",
        "-m",
        requested_model,
        "--json",
        "--output-schema",
        str(schema_path),
        prompt,
    ]


def _extract_proposal(
    receipt: Any,
    output_path: Path,
) -> tuple[bytes, bool, list[str], list[str]]:
    """Return proposal bytes, detected tool use, errors, and nonfatal warnings."""

    errors: list[str] = []
    warnings: list[str] = []
    tool_use = bool(getattr(receipt, "has_tool_calls", False))
    content = getattr(receipt, "content", None)
    if isinstance(content, str):
        raw = content.encode("utf-8")
        if len(raw) > MAX_PROVIDER_OUTPUT_BYTES:
            return b"", tool_use, ["PROVIDER_OUTPUT_EXCEEDS_BOUND"], warnings
        return raw, tool_use, errors, warnings

    try:
        event_bytes = output_path.read_bytes()
    except OSError:
        return b"", tool_use, ["PROVIDER_OUTPUT_MISSING"], warnings
    if len(event_bytes) > MAX_PROVIDER_OUTPUT_BYTES:
        return b"", tool_use, ["PROVIDER_OUTPUT_EXCEEDS_BOUND"], warnings

    allowed_events = {
        "thread.started",
        "turn.started",
        "turn.completed",
        "item.started",
        "item.updated",
        "item.completed",
        "error",
    }
    allowed_items = {"agent_message", "reasoning", "error"}
    messages: list[str] = []
    for line_number, line in enumerate(event_bytes.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = parse_json_object(line)
        except IntakeError:
            errors.append(f"PROVIDER_EVENT_INVALID:{line_number}")
            continue
        event_type = event.get("type")
        if event_type not in allowed_events:
            errors.append(f"PROVIDER_EVENT_TYPE_FORBIDDEN:{event_type}")
        item = event.get("item")
        if isinstance(item, dict):
            item_type = item.get("type")
            if item_type not in allowed_items:
                tool_use = True
                errors.append(f"PROVIDER_ITEM_TYPE_FORBIDDEN:{item_type}")
            elif item_type == "agent_message":
                text = item.get("text")
                if isinstance(text, str):
                    messages.append(text)
                else:
                    errors.append("PROVIDER_AGENT_MESSAGE_MISSING_TEXT")
            elif item_type == "error":
                warnings.append(str(item.get("message", "provider item error")))
        if event_type == "error":
            warnings.append(str(event.get("message", "provider event error")))
    if len(messages) != 1:
        errors.append(f"PROVIDER_AGENT_MESSAGE_COUNT:{len(messages)}")
    raw = messages[-1].encode("utf-8") if messages else b""
    return raw, tool_use, errors, warnings


def _proposal_shape_errors(
    proposal: dict[str, Any] | None,
) -> list[str]:
    if proposal is None:
        return ["PROPOSAL_NOT_STRICT_JSON_OBJECT"]
    errors: list[str] = []
    if set(proposal) != {"proposal_id", "candidate", "falsifiers"}:
        errors.append("PROPOSAL_ROOT_FIELDS")
    proposal_id = proposal.get("proposal_id")
    if (
        not isinstance(proposal_id, str)
        or not proposal_id
        or len(proposal_id) > 128
    ):
        errors.append("PROPOSAL_ID_INVALID")
    candidate = proposal.get("candidate")
    if not isinstance(candidate, dict):
        errors.append("PROPOSAL_CANDIDATE_INVALID")
    else:
        if set(candidate) != {"requested_claim", "evidence_ref"}:
            errors.append("PROPOSAL_CANDIDATE_FIELDS")
        if candidate.get("requested_claim") not in _CLAIM_VALUES:
            errors.append("PROPOSAL_CLAIM_ENUM")
        evidence_ref = candidate.get("evidence_ref")
        if (
            not isinstance(evidence_ref, str)
            or _HEX_SHA256.fullmatch(evidence_ref) is None
        ):
            errors.append("PROPOSAL_EVIDENCE_REF_INVALID")
    falsifiers = proposal.get("falsifiers")
    if (
        not isinstance(falsifiers, list)
        or not 1 <= len(falsifiers) <= 8
        or any(
            not isinstance(value, str)
            or not value.strip()
            or len(value) > 500
            for value in falsifiers
        )
        or (
            isinstance(falsifiers, list)
            and len(set(falsifiers)) != len(falsifiers)
        )
    ):
        errors.append("PROPOSAL_FALSIFIERS_INVALID")
    return errors


def _constraint(
    variable: str,
    value: Any,
) -> dict[str, Any]:
    return {
        "op": "eq",
        "left": {"var": variable},
        "right": {"const": value},
    }


def _solve_problem(spec: dict[str, Any]) -> dict[str, Any]:
    problem = FiniteConstraintProblem.from_spec(spec)
    solved = dual_solve(spec, max_states=problem.state_count)
    witnesses = solved.get("witnesses", {})

    def backend(name: str) -> dict[str, Any]:
        row = dict(solved["backend_results"][name])
        if name in witnesses:
            row["witness"] = witnesses[name]
        return row

    source_sha256 = {
        name: _sha256_file(Path(__file__).resolve().parent / name)
        for name in ("constraints.py", "dualsolve.py")
    }
    return {
        "spec_sha256": canonical_sha256(spec),
        "state_count": problem.state_count,
        "enumeration": backend("enumeration"),
        "z3": backend("z3"),
        "cvc5": backend("cvc5"),
        "backend_settings": solved["backend_settings"],
        "mandatory_deciders": ["z3", "cvc5", "enumeration"],
        "all_definite": solved["all_definite"],
        "agrees": solved["agree"],
        "disagreement": solved.get("disagreement"),
        "solver_source_sha256": source_sha256,
    }


def _smt_gate(observed: dict[str, Any]) -> dict[str, Any]:
    variables = {name: [False, True] for name in _BOOLEAN_GATES}
    variables["requested_claim"] = list(_CLAIM_VALUES)
    bindings = [_constraint(name, bool(observed[name])) for name in _BOOLEAN_GATES]
    bindings.append(_constraint("requested_claim", observed["requested_claim"]))
    admission = [_constraint(name, True) for name in _BOOLEAN_GATES]
    admission.append(_constraint("requested_claim", ALLOWED_CLAIM))

    proposal_spec = {
        "variables": variables,
        "constraints": bindings + admission,
    }
    hostile_bindings = [_constraint(name, True) for name in _BOOLEAN_GATES]
    hostile_bindings.append(_constraint("requested_claim", "scientific_result"))
    hostile_full_spec = {
        "variables": variables,
        "constraints": hostile_bindings + admission,
    }
    hostile_erased_spec = {
        "variables": variables,
        "constraints": hostile_bindings + admission[:-1],
    }
    proposal = _solve_problem(proposal_spec)
    hostile_full = _solve_problem(hostile_full_spec)
    hostile_erased = _solve_problem(hostile_erased_spec)
    expected = {
        "proposal": SolverStatus.BOUNDED_SAT.value,
        "hostile_full": SolverStatus.BOUNDED_UNSAT.value,
        "hostile_erased": SolverStatus.BOUNDED_SAT.value,
    }

    def status(row: dict[str, Any], backend: str) -> str:
        return row[backend]["status"]

    solved_rows = (proposal, hostile_full, hostile_erased)
    settled = all(row["agrees"] for row in solved_rows) and all(
        status(row, backend_name) == expected[row_name]
        for row_name, row in (
            ("hostile_full", hostile_full),
            ("hostile_erased", hostile_erased),
        )
        for backend_name in ("z3", "cvc5", "enumeration")
    )
    try:
        import z3  # type: ignore

        z3_version = z3.get_version_string()
    except ImportError:
        z3_version = None
    try:
        import cvc5  # type: ignore

        cvc5_version = cvc5.__version__
    except ImportError:
        cvc5_version = None
    return {
        "schema": "constraintbox.agent-smt-gate.v1",
        "encoding": "finite addresses; equality is domain-address equality",
        "z3_version": z3_version,
        "cvc5_version": cvc5_version,
        "proposal": proposal,
        "hostile_overclaim": hostile_full,
        "claim_constraint_erased_control": hostile_erased,
        "settled": settled,
        "proposal_admitted": (
            settled
            and all(
                status(proposal, backend_name) == expected["proposal"]
                for backend_name in ("z3", "cvc5", "enumeration")
            )
        ),
        "control_expected": expected,
        "promotion_allowed": False,
    }


def _policy() -> Policy:
    requirements = [
        Requirement(name, "eq", True)
        for name in (
            *_BOOLEAN_GATES,
            "smt_settled",
            "smt_proposal_admitted",
        )
    ]
    requirements.append(
        Requirement("requested_claim", "eq", ALLOWED_CLAIM)
    )
    return Policy(
        policy_id="constraintbox.agent-release.v1",
        requirements=tuple(requirements),
        max_age_seconds=60.0,
    )


def _model_slug_refines(requested: str, resolved: str) -> bool:
    """True iff the resolved slug is the requested slug or a dated/more-specific
    refinement of it (``requested + "-…"``).

    Justified from observed data, not assumption:
      * codex rollout bytes resolve exactly (``gpt-5.6-luna`` -> ``gpt-5.6-luna``,
        measured 2026-08-08), so equality passes.
      * HTTP bodies may resolve a dated refinement (``x-ai/grok-4.3`` ->
        ``x-ai/grok-4.3-20260430``, the receipt field's documented real
        behavior), which strict equality would wrongly flag.
      * the measured substitution (requested ``gpt-5.6-luna``, answered
        ``gpt-5.6-sol``) fails this rule: ``gpt-5.6-sol`` does not extend
        ``gpt-5.6-luna-``.

    Risk taken: the LENIENT direction.  If a route ever requests a bare family
    slug (e.g. ``gpt-5.6``) a sibling that extends it (``gpt-5.6-sol``) would
    pass.  Every registered route therefore requests a fully-qualified slug;
    the strict alternative would block every legitimately dated HTTP
    resolution.
    """

    return resolved == requested or resolved.startswith(requested + "-")


def _model_binding_reasons(
    model_requested: Any,
    model_resolved: Any,
) -> list[str]:
    """Deterministic check of the answering model against the requested one.

    Two distinct conditions, two distinct codes:
      * ``MODEL_RESOLVED_UNAVAILABLE`` -- the model that answered could not be
        established from provider bytes at all (``model_resolved`` absent).
        In CB vocabulary this is UNAVAILABLE: the run parks; it never passes.
      * ``MODEL_RESOLVED_MISMATCH`` -- a real substitution: the resolved model
        is neither the requested slug nor a refinement of it.
    """

    if not isinstance(model_requested, str) or not model_requested:
        return ["MODEL_RESOLVED_UNAVAILABLE"]
    if not isinstance(model_resolved, str) or not model_resolved:
        return ["MODEL_RESOLVED_UNAVAILABLE"]
    if not _model_slug_refines(model_requested, model_resolved):
        return ["MODEL_RESOLVED_MISMATCH"]
    return []


def _reason_codes(
    *,
    receipt: Any,
    provider_admitted: bool,
    tool_use: bool,
    extraction_errors: list[str],
    decision: Any,
    shape_errors: list[str],
    proposal: dict[str, Any] | None,
    evidence_ref: str,
    smt: dict[str, Any],
    discharge_status: str,
    release_safety: bool,
    model_requested: str,
) -> list[str]:
    reasons = list(extraction_errors)
    reasons.extend(
        _model_binding_reasons(
            model_requested,
            getattr(receipt, "model_resolved", None),
        )
    )
    if getattr(receipt, "status", None) != "success":
        reasons.append(f"PROVIDER_STATUS_{getattr(receipt, 'status', 'MISSING')}")
    if not provider_admitted:
        reasons.append("PROVIDER_RECEIPT_REJECTED")
    if tool_use:
        reasons.append("PROVIDER_TOOL_USE")
    if decision.disposition is not Disposition.ELIGIBLE:
        reasons.append(f"CONTROLLER_{decision.reason.upper()}")
    reasons.extend(shape_errors)
    candidate = proposal.get("candidate", {}) if proposal else {}
    candidate_evidence_ref = candidate.get("evidence_ref")
    if not candidate_evidence_ref:
        reasons.append("EVIDENCE_REF_MISSING")
    elif candidate_evidence_ref != evidence_ref:
        reasons.append("EVIDENCE_REF_MISMATCH")
    requested_claim = candidate.get("requested_claim")
    if not requested_claim:
        reasons.append("PROPOSAL_CLAIM_MISSING")
    elif requested_claim != ALLOWED_CLAIM:
        reasons.append("CLAIM_CEILING_EXCEEDED")
    if not smt["settled"]:
        reasons.append("SMT_UNAVAILABLE_OR_DIVERGENT")
    elif not smt["proposal_admitted"]:
        reasons.append("SMT_PROPOSAL_UNSAT")
    if discharge_status != PASS:
        reasons.append("DISCHARGE_NOT_PASS")
    if not release_safety:
        reasons.append("RELEASE_SAFETY_VETO")
    return sorted(set(reasons))


def _release_safety(
    *,
    raw: bytes,
    provider_admitted: bool,
    tool_use: bool,
    decision: Any,
    evidence_ref: str,
    tool_errors: list[str],
    smt: dict[str, Any],
    model_requested: str,
    model_resolved: Any,
) -> bool:
    """Independent final recomputation; no prior boolean verdict is trusted.

    The model binding is recomputed here from the raw requested/resolved
    values so a proposal blocked by ``_reason_codes`` for a substituted or
    unresolvable model can never still be judged release-safe.
    """

    try:
        proposal = parse_json_object(raw)
    except IntakeError:
        return False
    if _proposal_shape_errors(proposal):
        return False
    candidate = proposal["candidate"]
    return (
        provider_admitted
        and not tool_use
        and decision.disposition is Disposition.ELIGIBLE
        and not tool_errors
        and not _model_binding_reasons(model_requested, model_resolved)
        and candidate["requested_claim"] == ALLOWED_CLAIM
        and candidate["evidence_ref"] == evidence_ref
        and bool(proposal["falsifiers"])
        and smt["settled"]
        and smt["proposal_admitted"]
    )


def _claim_gate_is_strong(result: dict[str, Any]) -> bool:
    required = result.get("required_tiers")
    verified = result.get("verified_tiers")
    return (
        result.get("disposition") == "ADMITTED"
        and result.get("chain_exit_code") == 0
        and result.get("chain_verdict") == "VERIFIED"
        and result.get("required_unmet") == []
        and isinstance(required, list)
        and isinstance(verified, list)
        and "tier0" in required
        and set(required).issubset(verified)
        and result.get("tamper_events") == []
    )


def _final_result(
    *,
    task: AgentTask,
    box_run: VerifiedBoxRun,
    run_dir: Path,
    disposition: str,
    release: str | None,
    reason: str,
    profile_inputs: dict[str, Any],
    tool_receipt_path: Path | None,
    tool_receipt_sha256: str | None,
    tool_errors: list[str],
    attempts: list[dict[str, Any]],
    branch_ledger: BranchLedger,
    claim_gate: dict[str, Any] | None,
    release_receipt_path: Path | None,
    proposal_flow: dict[str, Any] | None = None,
    provider_policy: dict[str, Any] | None = None,
    formal_gates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "task_id": task.task_id,
        "profile_id": PROFILE_ID,
        "disposition": disposition,
        "reason": reason,
        "release": release,
        "release_allowed": disposition == "RELEASED" and release is not None,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "box_input": {
            "verified": True,
            "claim_ceiling": BOX_HANDOFF_CLAIM_CEILING,
            "run_directory": str(box_run.root),
            "box_receipt_sha256": box_run.receipt_sha256,
            "request_sha256": box_run.request_sha256,
            "profile_sha256": box_run.profile_sha256,
            "compiled_user_context_sha256": box_run.context_sha256,
            "external_engine_packet_sha256": (
                box_run.external_engine_packet_sha256
            ),
            "artifact_sha256s": dict(box_run.artifact_sha256s),
        },
        "maximum_attempts": MAX_ATTEMPTS,
        "run_directory": str(run_dir),
        "profile_inputs": {
            key: value
            for key, value in profile_inputs.items()
            if key != "mmm"
        }
        | {
            "controller_base_mmm_not_prompt_context": {
                "packs": profile_inputs.get("mmm", {}).get("packs", []),
                "sha256": profile_inputs.get("mmm", {}).get("sha256"),
            }
        },
        "tool_receipt": (
            str(tool_receipt_path) if tool_receipt_path is not None else None
        ),
        "tool_receipt_sha256": tool_receipt_sha256,
        "tool_errors": tool_errors,
        "proposal_provider_policy": provider_policy,
        "attempts": attempts,
        "branch_ledger": {
            "branches": {
                name: _jsonable(branch)
                for name, branch in branch_ledger.branches.items()
            },
            "events": _jsonable(branch_ledger.events),
        },
        "claim_gate": claim_gate,
        "proposal_flow": proposal_flow,
        "formal_gates": formal_gates,
        "release_receipt": (
            str(release_receipt_path)
            if release_receipt_path is not None
            else None
        ),
        "contained_provider_harness": {
            "module": "constraintbox._provider_harness",
            "inside_constraint_box": True,
            "vendored_source_manifest": "_provider_harness/VENDORED_SOURCE_MANIFEST.json",
            "parent_ratchet_checkout_imported": False,
        },
    }


def _run_formal_run_path_gates(run_dir: Path) -> dict[str, Any]:
    """Execute cb:sympy-exact-gate and cb:maude-transition-gate every run.

    Both formal gates run unconditionally on the REAL proposal FlowPolicy
    (proposal_minilev_flow.reference_flow_policy) — the same nodes,
    transitions, and budgets `run_proposal_minilev_flow` executes — with no
    usefulness heuristic.  The receipt is persisted next to the other run
    artifacts.  A gate crash is recorded as an ERROR execution rather than
    aborting the run; a MISMATCH verdict later excludes RELEASED.
    """

    from .gate_operations import FORMAL_RUN_GATES_SCHEMA, run_formal_flow_gates
    from .proposal_minilev_flow import reference_flow_policy

    try:
        receipt = run_formal_flow_gates(reference_flow_policy())
    except Exception as exc:  # noqa: BLE001 - recorded, never silently lost
        receipt = {
            "schema": FORMAL_RUN_GATES_SCHEMA,
            "executions": [],
            "error": f"{type(exc).__name__}: {exc}",
            "any_mismatch": False,
            "promotion_allowed": False,
        }
    _write_json(run_dir / "formal_gates_receipt.json", receipt)
    return receipt


def _formal_gates_mismatch(formal_gates: dict[str, Any]) -> bool:
    executions = formal_gates.get("executions")
    if not isinstance(executions, list):
        return False
    return any(
        isinstance(execution, dict) and execution.get("verdict") == "MISMATCH"
        for execution in executions
    )


def _run_mini_lev_proposal_loop(
    *,
    task: AgentTask,
    box_run: VerifiedBoxRun,
    run_dir: Path,
    profile_inputs: dict[str, Any],
    tool_receipt: dict[str, Any],
    tool_sha: str,
    components: dict[str, Any],
    provider: Any,
    provider_policy: dict[str, Any],
    notary: Any,
    schema_path: Path,
    schema_sha: str,
    task_sha: str,
    controller: ConstraintBoxController,
    branches: BranchLedger,
    claim_gate: Callable[[Path], dict[str, Any]],
    codex_binary: str | None,
    provider_timeout_seconds: float,
) -> dict[str, Any]:
    """Run the one fixed LLM proposal flow through Mini-LevOS.

    The callbacks below are controller code invoked only by the fixed static
    hooks in ``proposal_minilev_flow``.  The provider can supply candidate
    bytes; it cannot supply a transition, a retry decision, a ClaimGate
    decision, or released text.
    """

    attempts: list[dict[str, Any]] = []
    state: dict[str, Any] = {
        "accepted": None,
        "claim_gate": None,
        "feedback": None,
        "feedback_sha256": None,
        "latest": None,
        "release_receipt_path": None,
    }
    flow_binding_path = run_dir / "proposal_flow_binding.json"
    agent_source_sha256 = _sha256_file(Path(__file__).resolve())
    controller_source_sha256 = _sha256_file(
        Path(__file__).resolve().parent / "controller.py"
    )
    flow_binding = {
        "schema": "constraintbox.agent-proposal-flow-binding.v1",
        "task_sha256": task_sha,
        "box_receipt_sha256": box_run.receipt_sha256,
        "request_sha256": box_run.request_sha256,
        "profile_sha256": box_run.profile_sha256,
        "compiled_user_context_sha256": box_run.context_sha256,
        "external_engine_packet_sha256": box_run.external_engine_packet_sha256,
        "tool_receipt_sha256": tool_sha,
        "proposal_schema_sha256": schema_sha,
        "proposal_provider_policy": provider_policy,
        "proposal_provider_policy_sha256": canonical_sha256(provider_policy),
        "agent_source_path": str(Path(__file__).resolve()),
        "agent_source_sha256": agent_source_sha256,
        "controller_source_path": str(
            Path(__file__).resolve().parent / "controller.py"
        ),
        "controller_source_sha256": controller_source_sha256,
        "maximum_attempts": MAX_ATTEMPTS,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    _write_json(flow_binding_path, flow_binding)
    flow_binding_sha256 = _sha256_file(flow_binding_path)

    def write_attempt_artifact(
        attempt_dir: Path,
        name: str,
        body: dict[str, Any],
    ) -> tuple[Path, str]:
        path = attempt_dir / name
        _write_json(path, body)
        return path, _sha256_file(path)

    def proposal_callback(context) -> ProposalCallbackResult:
        attempt_number = context.attempt_number
        attempt_dir = run_dir / f"attempt-{attempt_number}"
        attempt_dir.mkdir()
        feedback = state["feedback"]
        feedback_sha256 = state["feedback_sha256"]
        schema_text = schema_path.read_text(encoding="utf-8")
        prompt = _build_prompt(
            task,
            attempt=attempt_number,
            proposal_schema_text=schema_text,
            proposal_schema_sha256=schema_sha,
            personalized_context_text=box_run.context_text,
            personalized_context_sha256=box_run.context_sha256,
            tool_receipt_sha256=tool_sha,
            tool_receipt=tool_receipt,
            feedback=feedback,
            feedback_sha256=feedback_sha256,
        )
        prompt_path = attempt_dir / "prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        output_path = attempt_dir / "provider_events.jsonl"
        command = (
            _codex_command(
                prompt,
                attempt_dir=attempt_dir,
                schema_path=schema_path,
                codex_binary=codex_binary,
                requested_model=provider_policy["requested_model"],
            )
            if provider_policy.get("route") == "local_tool"
            else None
        )
        task_spec = components["TaskSpec"](
            task_id=f"{task.task_id}-attempt-{attempt_number}",
            role="builder",
            prompt=prompt,
            classification="scratch_diagnostic",
            claim_ceiling=CLAIM_CEILING,
            gate_ceiling_rung="scratch_diagnostic",
            input_refs=[
                task_sha,
                box_run.receipt_sha256,
                box_run.request_sha256,
                box_run.profile_sha256,
                box_run.context_sha256,
                box_run.external_engine_packet_sha256,
                schema_sha,
                tool_sha,
                *([feedback_sha256] if feedback_sha256 else []),
            ],
            audit_required=False,
        )
        job = components["ModelJob"](
            task=task_spec,
            provider=provider_policy["route"],
            model=provider_policy["requested_model"],
            output_path=str(output_path),
            command=command,
            cwd=str(attempt_dir),
            produced_by="__default__",
            temperature=provider_policy.get("temperature"),
            max_tokens=provider_policy.get("max_tokens"),
            tools=[],
        )
        dispatch_time = datetime.now(timezone.utc).isoformat()
        provider_receipt_path = attempt_dir / "provider_receipt.json"
        try:
            receipt = components["run_job"](
                job,
                provider,
                timeout=min(
                    float(provider_timeout_seconds), PROVIDER_TIMEOUT_SECONDS
                ),
                started_at=dispatch_time,
                completed_at=dispatch_time,
                receipt_path=provider_receipt_path,
                notary=notary,
            )
        except Exception as exc:  # noqa: BLE001 - fail closed at provider boundary
            boundary_error_path = attempt_dir / "provider_boundary_error.json"
            boundary_error = {
                "schema": "constraintbox.provider-boundary-error.v1",
                "attempt": attempt_number,
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "provider_output_sha256": (
                    _sha256_file(output_path) if output_path.is_file() else None
                ),
                "promotion_allowed": False,
            }
            _write_json(boundary_error_path, boundary_error)
            branch_id = f"attempt-{attempt_number}"
            branches.add(branch_id, boundary_error)
            branches.park(branch_id, "PROVIDER_BOUNDARY_ERROR")
            attempts.append(
                {
                    "attempt": attempt_number,
                    "disposition": "PARKED",
                    "reason_codes": ["PROVIDER_BOUNDARY_ERROR"],
                    "prompt": str(prompt_path),
                    "prompt_sha256": _sha256_file(prompt_path),
                    "feedback_input_sha256": feedback_sha256,
                    "provider_receipt": None,
                    "provider_boundary_error": str(boundary_error_path),
                    "provider_boundary_error_sha256": _sha256_file(
                        boundary_error_path
                    ),
                    "feedback": None,
                    "feedback_sha256": None,
                }
            )
            _, artifact_sha256 = write_attempt_artifact(
                attempt_dir,
                "proposal_observation.json",
                {
                    "schema": "constraintbox.agent-proposal-observation.v1",
                    "attempt": attempt_number,
                    "status": "provider_boundary_parked",
                    "boundary_error_sha256": _sha256_file(boundary_error_path),
                    "prompt_sha256": _sha256_file(prompt_path),
                    "promotion_allowed": False,
                },
            )
            return ProposalCallbackResult(ProposalSignal.PARKED, artifact_sha256)

        provider_gate = components["provider_gate"](receipt)
        raw, tool_use, extraction_errors, extraction_warnings = _extract_proposal(
            receipt, output_path
        )
        provider_receipt_sha256 = _sha256_file(provider_receipt_path)
        state["latest"] = {
            "attempt": attempt_number,
            "attempt_dir": attempt_dir,
            "prompt_path": prompt_path,
            "feedback_sha256": feedback_sha256,
            "provider_receipt_path": provider_receipt_path,
            "provider_receipt_sha256": provider_receipt_sha256,
            "receipt": receipt,
            "provider_gate": provider_gate,
            "raw": raw,
            "tool_use": tool_use,
            "extraction_errors": extraction_errors,
            "extraction_warnings": extraction_warnings,
        }
        _, artifact_sha256 = write_attempt_artifact(
            attempt_dir,
            "proposal_observation.json",
            {
                "schema": "constraintbox.agent-proposal-observation.v1",
                "attempt": attempt_number,
                "prompt_sha256": _sha256_file(prompt_path),
                "feedback_input_sha256": feedback_sha256,
                "provider_receipt_sha256": provider_receipt_sha256,
                "provider_status": getattr(receipt, "status", None),
                "provider_gate_sha256": canonical_sha256(
                    _jsonable(provider_gate.to_dict())
                ),
                "proposal_sha256": _sha256_bytes(raw),
                "provider_tool_use": tool_use,
                "extraction_errors_sha256": canonical_sha256(extraction_errors),
                "promotion_allowed": False,
            },
        )
        return ProposalCallbackResult(ProposalSignal.OBSERVED, artifact_sha256)

    def proposal_gate_callback(context) -> ProposalGateCallbackResult:
        latest = state["latest"]
        if not isinstance(latest, dict) or latest.get("attempt") != context.attempt_number:
            raise AgentRunError("proposal gate did not receive its current observation")
        attempt_number = context.attempt_number
        raw = latest["raw"]
        try:
            proposal = parse_json_object(raw)
        except IntakeError:
            proposal = None
        shape_errors = _proposal_shape_errors(proposal)
        decision = controller.run(
            TaskRequest(
                PROPOSAL_TASK_KIND,
                raw,
                f"{task.task_id}-attempt-{attempt_number}",
            )
        )
        candidate = proposal.get("candidate", {}) if proposal else {}
        observed = {
            "provider_receipt_admitted": latest["provider_gate"].admitted,
            "provider_tool_free": not latest["tool_use"],
            "strict_intake_eligible": (
                decision.disposition is Disposition.ELIGIBLE
            ),
            "proposal_schema_valid": not shape_errors,
            "evidence_ref_matches": candidate.get("evidence_ref") == tool_sha,
            "falsifier_present": bool(
                proposal
                and isinstance(proposal.get("falsifiers"), list)
                and proposal["falsifiers"]
            ),
            "tool_profile_ready": True,
            "tool_controls_complete": True,
            "tool_operation_bound": True,
            "requested_claim": candidate.get("requested_claim", ""),
        }
        smt = _smt_gate(observed)
        observed["smt_settled"] = smt["settled"]
        observed["smt_proposal_admitted"] = smt["proposal_admitted"]
        decided_at = time.time()
        settlement = discharge(
            _policy(),
            {
                name: Observation(value, decided_at, "constraintbox.agent-run")
                for name, value in observed.items()
            },
            now=decided_at,
        )
        model_requested = provider_policy.get("requested_model")
        model_resolved = getattr(latest["receipt"], "model_resolved", None)
        model_binding_reasons = _model_binding_reasons(
            model_requested, model_resolved
        )
        release_safety = _release_safety(
            raw=raw,
            provider_admitted=latest["provider_gate"].admitted,
            tool_use=latest["tool_use"],
            decision=decision,
            evidence_ref=tool_sha,
            tool_errors=[],
            smt=smt,
            model_requested=model_requested,
            model_resolved=model_resolved,
        )
        reasons = _reason_codes(
            receipt=latest["receipt"],
            provider_admitted=latest["provider_gate"].admitted,
            tool_use=latest["tool_use"],
            extraction_errors=latest["extraction_errors"],
            decision=decision,
            shape_errors=shape_errors,
            proposal=proposal,
            evidence_ref=tool_sha,
            smt=smt,
            discharge_status=settlement.status,
            release_safety=release_safety,
            model_requested=model_requested,
        )
        eligible = settlement.status == PASS and release_safety and not reasons
        provider_or_solver_parked = (
            getattr(latest["receipt"], "status", None) != "success"
            or not smt["settled"]
            # An unresolvable answering model is UNAVAILABLE evidence, not a
            # judged refusal: the attempt parks.  A MISMATCH (real
            # substitution) stays a hard block, never a park.
            or "MODEL_RESOLVED_UNAVAILABLE" in model_binding_reasons
        )
        attempt_disposition = (
            "ELIGIBLE"
            if eligible
            else "PARKED"
            if provider_or_solver_parked
            else "BLOCKED"
        )
        branch_id = f"attempt-{attempt_number}"
        branches.add(
            branch_id,
            proposal
            if proposal is not None
            else {"unparsed_sha256": _sha256_bytes(raw)},
            parents=(("attempt-1",) if attempt_number == 2 else ()),
        )
        attempt_record = {
            "attempt": attempt_number,
            "disposition": attempt_disposition,
            "reason_codes": reasons,
            "prompt": str(latest["prompt_path"]),
            "prompt_sha256": _sha256_file(latest["prompt_path"]),
            "feedback_input_sha256": latest["feedback_sha256"],
            "provider_receipt": str(latest["provider_receipt_path"]),
            "provider_receipt_sha256": latest["provider_receipt_sha256"],
            "provider_gate": latest["provider_gate"].to_dict(),
            "provider_event_errors": latest["extraction_errors"],
            "provider_event_warnings": latest["extraction_warnings"],
            "proposal_sha256": _sha256_bytes(raw),
            "controller_decision": decision.to_dict(),
            "smt_gate": smt,
            "discharge": _jsonable(settlement),
            "release_safety": release_safety,
            "model_binding": {
                "model_requested": model_requested,
                "model_resolved": model_resolved,
                "reason_codes": model_binding_reasons,
                "missing_observation": (
                    "receipt.model_resolved (codex rollout turn_context "
                    "payload.model, or HTTP response body model)"
                    if "MODEL_RESOLVED_UNAVAILABLE" in model_binding_reasons
                    else None
                ),
            },
            "feedback": None,
            "feedback_sha256": None,
        }
        attempts.append(attempt_record)
        if eligible:
            state["accepted"] = {
                "raw": raw,
                "proposal": proposal,
                "decision": decision,
                "provider_gate": latest["provider_gate"],
                "tool_use": latest["tool_use"],
                "smt": smt,
                "attempt": attempt_number,
                "model_requested": model_requested,
                "model_resolved": model_resolved,
            }
            signal = ProposalGateSignal.PASS
        elif attempt_number < MAX_ATTEMPTS:
            branches.park(branch_id, ",".join(reasons) or attempt_disposition)
            feedback = {
                "schema": "constraintbox.agent-feedback.v1",
                "failed_attempt": attempt_number,
                "reason_codes": reasons,
                "required_claim": ALLOWED_CLAIM,
                "required_evidence_ref": tool_sha,
                "attempts_remaining": MAX_ATTEMPTS - attempt_number,
            }
            feedback_path = latest["attempt_dir"] / "feedback.json"
            _write_json(feedback_path, feedback)
            feedback_sha256 = _sha256_file(feedback_path)
            state["feedback"] = feedback
            state["feedback_sha256"] = feedback_sha256
            attempt_record["feedback"] = str(feedback_path)
            attempt_record["feedback_sha256"] = feedback_sha256
            signal = ProposalGateSignal.RETRY
        else:
            branches.park(branch_id, ",".join(reasons) or attempt_disposition)
            signal = (
                ProposalGateSignal.PARKED
                if provider_or_solver_parked
                else ProposalGateSignal.BLOCKED
            )
        _, artifact_sha256 = write_attempt_artifact(
            latest["attempt_dir"],
            "proposal_gate_observation.json",
            {
                "schema": "constraintbox.agent-proposal-gate-observation.v1",
                "attempt": attempt_number,
                "attempt_record_sha256": canonical_sha256(attempt_record),
                "controller_decision_sha256": canonical_sha256(
                    _jsonable(decision.to_dict())
                ),
                "smt_gate_sha256": canonical_sha256(smt),
                "discharge_sha256": canonical_sha256(_jsonable(settlement)),
                "terminal_signal": signal.value,
                "promotion_allowed": False,
            },
        )
        return ProposalGateCallbackResult(signal, artifact_sha256)

    def claim_gate_callback(context) -> ClaimGateCallbackResult:
        accepted = state["accepted"]
        if not isinstance(accepted, dict):
            raise AgentRunError("ClaimGate ran without a deterministic pass")
        attempt_dir = run_dir / f"attempt-{context.attempt_number}"
        release_safety = _release_safety(
            raw=accepted["raw"],
            provider_admitted=accepted["provider_gate"].admitted,
            tool_use=accepted["tool_use"],
            decision=accepted["decision"],
            evidence_ref=tool_sha,
            tool_errors=[],
            smt=accepted["smt"],
            model_requested=accepted["model_requested"],
            model_resolved=accepted["model_resolved"],
        )
        if not release_safety:
            _, artifact_sha256 = write_attempt_artifact(
                attempt_dir,
                "claim_gate_observation.json",
                {
                    "schema": "constraintbox.agent-claim-gate-observation.v1",
                    "attempt": context.attempt_number,
                    "release_safety": False,
                    "promotion_allowed": False,
                },
            )
            return ClaimGateCallbackResult(ClaimGateSignal.BLOCKED, artifact_sha256)

        release_receipt_path = run_dir / "release_receipt.json"
        release_receipt = {
            "classification": "scratch_diagnostic",
            "claim_kind": "field_only",
            "produced_by": "constraintbox.agent-run",
            "release_scope": ALLOWED_CLAIM,
            "release_statement": RELEASE_TEXT,
            "tool_receipt_sha256": tool_sha,
            "proposal_sha256": _sha256_bytes(accepted["raw"]),
            "controller_policy_sha256": controller.policy_sha256,
            "box_receipt_sha256": box_run.receipt_sha256,
            "request_sha256": box_run.request_sha256,
            "profile_sha256": box_run.profile_sha256,
            "compiled_user_context_sha256": box_run.context_sha256,
            "external_engine_packet_sha256": box_run.external_engine_packet_sha256,
            "proposal_flow_policy_sha256": context.flow_policy_sha256,
            "proposal_flow_binding_sha256": context.binding_artifact_sha256,
            "promotion_allowed": False,
        }
        _write_json(release_receipt_path, release_receipt)
        state["release_receipt_path"] = release_receipt_path
        try:
            gate_result = claim_gate(release_receipt_path)
        except Exception as exc:  # noqa: BLE001 - ClaimGate failure is non-release
            gate_result = {
                "disposition": "PARKED",
                "reason": "CLAIM_GATE_BOUNDARY_ERROR",
                "exception_type": type(exc).__name__,
                "error": str(exc),
            }
        if not isinstance(gate_result, dict):
            gate_result = {
                "disposition": "PARKED",
                "reason": "CLAIM_GATE_RESULT_TYPE_INVALID",
            }
        state["claim_gate"] = _jsonable(gate_result)
        if _claim_gate_is_strong(gate_result):
            signal = ClaimGateSignal.PASS
        elif gate_result.get("disposition") in {
            "PARKED",
            "EVALUATION_ERROR",
            "INSUFFICIENT_DEPTH",
            "ADMITTED",
        }:
            signal = ClaimGateSignal.PARKED
        else:
            signal = ClaimGateSignal.BLOCKED
        _, artifact_sha256 = write_attempt_artifact(
            attempt_dir,
            "claim_gate_observation.json",
            {
                "schema": "constraintbox.agent-claim-gate-observation.v1",
                "attempt": context.attempt_number,
                "release_receipt_sha256": _sha256_file(release_receipt_path),
                "claim_gate_result_sha256": canonical_sha256(
                    state["claim_gate"]
                ),
                "terminal_signal": signal.value,
                "promotion_allowed": False,
            },
        )
        return ClaimGateCallbackResult(signal, artifact_sha256)

    try:
        flow = run_proposal_minilev_flow(
            run_root=run_dir / "proposal_minilev_flow",
            controller_state_root=(
                run_dir.parent / ".constraintbox-controller-state"
            ).resolve(),
            caller_source_path=Path(__file__).resolve(),
            controller_source_path=Path(__file__).resolve().parent / "controller.py",
            binding_artifact_sha256=flow_binding_sha256,
            callbacks=ProposalMiniLevCallbacks(
                proposal_callback,
                proposal_gate_callback,
                claim_gate_callback,
            ),
        )
        valid, reason = verify_proposal_minilev_flow(flow)
        if not valid:
            raise ProposalMiniLevFlowError(
                f"caller replay verification failed: {reason}"
            )
        flow_record = flow.to_dict() | {
            "binding": str(flow_binding_path),
            "binding_sha256": flow_binding_sha256,
            "caller_replay_verified": True,
        }
        return {
            "terminal": flow.terminal,
            "attempts": attempts,
            "accepted": state["accepted"],
            "claim_gate": state["claim_gate"],
            "release_receipt_path": state["release_receipt_path"],
            "flow": flow_record,
        }
    except (OSError, ProposalMiniLevFlowError, ValueError) as exc:
        return {
            "terminal": "HOLD",
            "attempts": attempts,
            "accepted": None,
            "claim_gate": state["claim_gate"],
            "release_receipt_path": state["release_receipt_path"],
            "flow": {
                "schema": "constraintbox.proposal-minilev-flow-result.v1",
                "binding": str(flow_binding_path),
                "binding_sha256": flow_binding_sha256,
                "terminal": "HOLD",
                "caller_replay_verified": False,
                "error": str(exc),
                "promotion_allowed": False,
            },
        }


def run_agent(
    box_run_dir: Path,
    run_dir: Path,
) -> tuple[dict[str, Any], int]:
    """Run the production proposal loop from one verified box snapshot.

    This public boundary intentionally exposes no runtime, provider, timeout,
    command, or ClaimGate override.  Those are controller-owned production
    choices.  The separately named private helper below exists solely so the
    offline unit suite can inject deterministic fakes at its boundary.

    This is an API-boundary control, not hostile-process containment: code
    already executing with this user's Python privileges can still modify the
    process or source tree.
    """

    return _run_agent_for_test(
        box_run_dir,
        run_dir,
        python_executable=None,
        provider_timeout_seconds=PROVIDER_TIMEOUT_SECONDS,
        tool_timeout_seconds=TOOL_TIMEOUT_SECONDS,
        provider=None,
        codex_binary=None,
        claim_gate=_PRODUCTION_CLAIM_GATE,
    )


def _run_agent_for_test(
    box_run_dir: Path,
    run_dir: Path,
    *,
    python_executable: Path | None = None,
    provider_timeout_seconds: float = PROVIDER_TIMEOUT_SECONDS,
    tool_timeout_seconds: float = TOOL_TIMEOUT_SECONDS,
    provider: Any | None = None,
    codex_binary: str | None = None,
    claim_gate: Callable[[Path], dict[str, Any]] = run_gate,
) -> tuple[dict[str, Any], int]:
    """Injectable offline test seam; not a production authority boundary."""

    if not isinstance(provider_timeout_seconds, (int, float)) or (
        provider_timeout_seconds <= 0
    ):
        raise AgentRunError("provider timeout must be positive")
    if not isinstance(tool_timeout_seconds, (int, float)) or tool_timeout_seconds <= 0:
        raise AgentRunError("tool timeout must be positive")

    try:
        box_run = verify_box_run(Path(box_run_dir))
    except (BoxRunError, OSError, ValueError) as exc:
        raise AgentRunError(f"first-box handoff verification failed: {exc}") from exc
    task = _task_from_verified_box(box_run)
    run_dir = Path(run_dir).expanduser().resolve()
    if (
        run_dir == box_run.root
        or box_run.root in run_dir.parents
        or run_dir in box_run.root.parents
    ):
        raise AgentRunError(
            "agent run directory must be separate from the captured box run"
        )
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise AgentRunError(f"run directory already exists: {run_dir}") from exc
    except OSError as exc:
        raise AgentRunError(f"could not create run directory: {exc}") from exc

    task_path = run_dir / "task.json"
    _write_json(task_path, task.to_dict())
    # G1 wiring: both formal gates (sympy budgets, maude transitions) execute
    # on the real proposal FlowPolicy on EVERY run, before any early return.
    formal_gates = _run_formal_run_path_gates(run_dir)
    profile_inputs, profile_errors = _load_profile_inputs()
    branches = BranchLedger()
    if profile_errors:
        result = _final_result(
            task=task,
            box_run=box_run,
            run_dir=run_dir,
            disposition="PARKED",
            release=None,
            reason="controller profile inputs drifted or are unavailable",
            profile_inputs=profile_inputs,
            tool_receipt_path=None,
            tool_receipt_sha256=None,
            tool_errors=profile_errors,
            attempts=[],
            branch_ledger=branches,
            claim_gate=None,
            release_receipt_path=None,
            formal_gates=formal_gates,
        )
        _write_json(run_dir / "run_receipt.json", result)
        return result, RUN_EXIT_CODES["PARKED"]

    tool_receipt, tool_errors = _run_fixed_tool(
        run_dir,
        python_executable=python_executable,
        timeout_seconds=tool_timeout_seconds,
    )
    tool_path = run_dir / "tool_receipt.json"
    _write_json(tool_path, tool_receipt)
    tool_sha = _sha256_file(tool_path)
    if tool_errors:
        estate_state = tool_receipt["estate_receipt"].get("state")
        disposition = (
            "REFUSED"
            if estate_state == CapabilityState.FAILED.value
            else "PARKED"
        )
        result = _final_result(
            task=task,
            box_run=box_run,
            run_dir=run_dir,
            disposition=disposition,
            release=None,
            reason="fixed tool profile did not satisfy its controller-owned checks",
            profile_inputs=profile_inputs,
            tool_receipt_path=tool_path,
            tool_receipt_sha256=tool_sha,
            tool_errors=tool_errors,
            attempts=[],
            branch_ledger=branches,
            claim_gate=None,
            release_receipt_path=None,
            formal_gates=formal_gates,
        )
        _write_json(run_dir / "run_receipt.json", result)
        return result, RUN_EXIT_CODES[disposition]

    components = _harness_components()
    if provider is None:
        try:
            selected_provider = select_proposal_provider(components)
        except ProposalProviderPolicyError as exc:
            provider_policy = {
                "schema": PROPOSAL_PROVIDER_POLICY_SCHEMA,
                "state": "PARKED",
                "reason": "registered_provider_route_unavailable",
                "error": str(exc),
                "llm_decision_authority": False,
                "promotion_allowed": False,
            }
            result = _final_result(
                task=task,
                box_run=box_run,
                run_dir=run_dir,
                disposition="PARKED",
                release=None,
                reason="controller-owned proposal-provider route is unavailable",
                profile_inputs=profile_inputs,
                tool_receipt_path=tool_path,
                tool_receipt_sha256=tool_sha,
                tool_errors=[],
                attempts=[],
                branch_ledger=branches,
                claim_gate=None,
                release_receipt_path=None,
                provider_policy=provider_policy,
                formal_gates=formal_gates,
            )
            _write_json(run_dir / "run_receipt.json", result)
            return result, RUN_EXIT_CODES["PARKED"]
        provider = selected_provider.provider
        provider_policy = selected_provider.public_binding()
    else:
        provider_policy = _injected_provider_policy(provider)
    notary = components["Notary"]()
    schema_path = run_dir / "proposal_schema.json"
    _write_json(schema_path, _proposal_schema())
    schema_sha = _sha256_file(schema_path)
    task_sha = _sha256_file(task_path)
    controller = ConstraintBoxController(
        {PROPOSAL_TASK_KIND: AgentProposalProfile()},
        run_dir / "controller",
    )

    proposal_outcome = _run_mini_lev_proposal_loop(
        task=task,
        box_run=box_run,
        run_dir=run_dir,
        profile_inputs=profile_inputs,
        tool_receipt=tool_receipt,
        tool_sha=tool_sha,
        components=components,
        provider=provider,
        provider_policy=provider_policy,
        notary=notary,
        schema_path=schema_path,
        schema_sha=schema_sha,
        task_sha=task_sha,
        controller=controller,
        branches=branches,
        claim_gate=claim_gate,
        codex_binary=codex_binary,
        provider_timeout_seconds=provider_timeout_seconds,
    )
    terminal = proposal_outcome["terminal"]
    observed_claim_gate = proposal_outcome["claim_gate"]
    release_receipt_path = proposal_outcome["release_receipt_path"]
    if terminal == "RELEASED" and _formal_gates_mismatch(formal_gates):
        # An exact formal disagreement (sympy budget arithmetic or maude
        # rewrite observation against the run's own FlowPolicy) refuses the
        # release regardless of the ClaimGate outcome.  This only ever
        # narrows the release condition; it never widens it.
        disposition = "REFUSED"
        release = None
        reason = (
            "run-path formal gate MISMATCH: sympy/maude disagreed with the "
            "flow policy's own structure"
        )
    elif (
        terminal == "RELEASED"
        and isinstance(observed_claim_gate, dict)
        and _claim_gate_is_strong(observed_claim_gate)
        and isinstance(release_receipt_path, Path)
    ):
        disposition = "RELEASED"
        release = RELEASE_TEXT
        reason = "fixed Mini-Lev proposal and ClaimGate gates passed"
    elif terminal == "BLOCKED":
        disposition = "REFUSED"
        release = None
        reason = (
            "ClaimGate refused the controller release receipt"
            if observed_claim_gate is not None
            else "no proposal survived the bounded Mini-Lev gate budget"
        )
    elif terminal == "PARKED":
        disposition = "PARKED"
        release = None
        reason = (
            "ClaimGate was unavailable, shallow, or internally inconsistent"
            if observed_claim_gate is not None
            else "the bounded Mini-Lev proposal flow parked"
        )
    else:
        disposition = "PARKED"
        release = None
        reason = "the bounded Mini-Lev proposal flow held before release"

    result = _final_result(
        task=task,
        box_run=box_run,
        run_dir=run_dir,
        disposition=disposition,
        release=release,
        reason=reason,
        profile_inputs=profile_inputs,
        tool_receipt_path=tool_path,
        tool_receipt_sha256=tool_sha,
        tool_errors=tool_errors,
        attempts=proposal_outcome["attempts"],
        branch_ledger=branches,
        claim_gate=observed_claim_gate,
        release_receipt_path=release_receipt_path,
        proposal_flow=proposal_outcome["flow"],
        provider_policy=provider_policy,
        formal_gates=formal_gates,
    )
    _write_json(run_dir / "run_receipt.json", result)
    return result, RUN_EXIT_CODES[disposition]
