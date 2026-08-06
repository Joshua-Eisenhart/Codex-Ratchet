"""Fixed Mini-LevOS retention flow for one foreign Lev eval bundle.

This is deliberately separate from the proposal/ClaimGate flow.  Its only
job is to retain and replay-check a controller-selected historical artifact
bundle.  A successful structural replay reaches ``PARKED``, not ``ELIGIBLE``
or ``RELEASED``: no semantic CB-to-Lev comparator exists yet.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import stat
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .intake import IntakeError, canonical_json, parse_json_object
from .lev_eval_observation import (
    LevEvalObservationBinding,
    LevEvalObservationError,
    LevEvalObservationHoldError,
    build_lev_eval_observation_binding,
    observe_lev_eval_bundle,
    verify_lev_eval_observation_snapshot,
)
from .mini_levos import (
    CONTROLLER_METADATA_KEY,
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookKind,
    HookRegistration,
    HookResult,
    HookSignal,
    MiniLevError,
    MiniLevRuntime,
    handler_code_sha256,
    verify_flow_receipt,
)


FLOW_ID = "constraintbox.lev-eval-observation-flow.v1"
FLOW_RECEIPT_NAME = "lev_eval_observation_flow_receipt.json"
FLOW_LEDGER_NAME = "lev_eval_observation_flow_events.jsonl"
FLOW_BINDING_NAME = "lev_eval_observation_binding.json"
OBSERVATION_DIRECTORY_NAME = "lev_eval_observation"
_SHA256 = hashlib.sha256
_CLAIM_CEILING = (
    "one controller-selected historical Lev eval path was captured and "
    "replay-checked through a fixed two-node Mini-LevOS flow; the retained "
    "material remains parked until a separate deterministic comparator exists"
)
_FIXED_NODES = [
    {"node_id": "observe-foreign-eval", "hook_id": "observe-foreign-eval"},
    {
        "node_id": "replay-verify-foreign-eval",
        "hook_id": "replay-verify-foreign-eval",
    },
]
_FIXED_TRANSITIONS = [
    {
        "from_node": "observe-foreign-eval",
        "signal": "OBSERVED",
        "to_node": "replay-verify-foreign-eval",
    },
    {
        "from_node": "observe-foreign-eval",
        "signal": "PARKED",
        "to_node": "PARKED",
    },
    {
        "from_node": "observe-foreign-eval",
        "signal": "HOLD",
        "to_node": "HOLD",
    },
    {
        "from_node": "replay-verify-foreign-eval",
        "signal": "PASS",
        "to_node": "PARKED",
    },
    {
        "from_node": "replay-verify-foreign-eval",
        "signal": "HOLD",
        "to_node": "HOLD",
    },
]
_FIXED_BOUNDS = {
    "max_steps": 2,
    "max_visits_per_node": 1,
    "max_retries": 0,
    "max_context_bytes": 16_384,
    "max_event_bytes": 65_536,
    "max_receipt_bytes": 524_288,
}


class LevEvalObservationFlowError(RuntimeError):
    """The fixed historical-observation Mini-Lev flow could not run or replay."""


@dataclass(frozen=True)
class LevEvalObservationFlowResult:
    """One non-promotable retained-observation flow result."""

    request_id: str
    binding: LevEvalObservationBinding
    run_id: str
    terminal: str
    flow_root: Path
    flow_receipt_path: Path
    flow_ledger_path: Path
    flow_receipt_sha256: str
    flow_receipt: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        final_context = self.flow_receipt["final_context"]
        if (
            self.terminal == "PARKED"
            and final_context.get("lev_eval_observation_capture_state") == "retained"
            and final_context.get("lev_eval_observation_replay_state")
            == "retained_snapshot_rechecked"
        ):
            claim_ceiling = _CLAIM_CEILING
        elif self.terminal == "PARKED":
            claim_ceiling = (
                "one selected historical Lev path could not be captured under the "
                "fixed contract and remains parked; no foreign result was admitted"
            )
        else:
            claim_ceiling = (
                "a local CB capture or replay integrity boundary held closed; no "
                "foreign result was admitted"
            )
        return {
            "schema": "constraintbox.lev-eval-observation-flow-result.v1",
            "request_id": self.request_id,
            "observation_request_sha256": self.binding.request_sha256,
            "run_id": self.run_id,
            "terminal": self.terminal,
            "capture_state": final_context.get("lev_eval_observation_capture_state"),
            "replay_state": final_context.get("lev_eval_observation_replay_state"),
            "observation_receipt_sha256": final_context.get(
                "lev_eval_observation_receipt_sha256"
            ),
            "snapshot_sha256": final_context.get("lev_eval_snapshot_sha256"),
            "flow_receipt": str(self.flow_receipt_path),
            "flow_receipt_sha256": self.flow_receipt_sha256,
            "foreign_decision_authority": False,
            "comparison_performed": False,
            "promotion_allowed": False,
            "claim_ceiling": claim_ceiling,
        }


@dataclass
class _ActiveObservationRun:
    binding: LevEvalObservationBinding
    flow_root: Path
    lock: threading.RLock
    capture_started: bool = False

    @property
    def observation_run_dir(self) -> Path:
        return self.flow_root / OBSERVATION_DIRECTORY_NAME


_ACTIVE_RUNS: dict[str, _ActiveObservationRun] = {}
_ACTIVE_RUNS_LOCK = threading.RLock()


def _source_sha256(path: Path) -> str:
    try:
        return _SHA256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise LevEvalObservationFlowError(
            f"observation-flow source is unavailable: {path}"
        ) from exc


def _source_registration(
    *,
    hook_id: str,
    kind: HookKind,
    handler,
    allowed_signals: tuple[HookSignal, ...],
    allowed_update_keys: tuple[str, ...] = (),
) -> HookRegistration:
    source_path = Path(__file__).resolve()
    return HookRegistration(
        hook_id=hook_id,
        kind=kind,
        handler=handler,
        source_path=source_path,
        source_sha256=_source_sha256(source_path),
        code_sha256=handler_code_sha256(handler),
        allowed_signals=allowed_signals,
        allowed_update_keys=allowed_update_keys,
        max_output_bytes=65_536,
    )


def _fixed_policy_reason(receipt: object) -> str | None:
    """Reject a merely valid Mini-Lev receipt that is not this exact flow.

    ``verify_flow_receipt`` establishes Mini-Lev kernel integrity, but it is
    intentionally generic.  This wrapper must additionally prove that the
    retained result used the fixed non-promotable observation policy rather
    than another valid flow that happens to be called similarly.
    """

    if not isinstance(receipt, dict):
        return "observation flow receipt is not an object"
    if receipt.get("flow_id") != FLOW_ID:
        return "observation flow id is not the fixed historical-observation flow"
    policy = receipt.get("policy")
    if not isinstance(policy, dict):
        return "observation flow policy is missing"
    if policy.get("flow_id") != FLOW_ID:
        return "observation policy flow id is not fixed"
    if policy.get("entry_node") != "observe-foreign-eval":
        return "observation policy entry node is not fixed"
    if policy.get("nodes") != _FIXED_NODES:
        return "observation policy nodes are not fixed"
    if policy.get("transitions") != _FIXED_TRANSITIONS:
        return "observation policy transitions are not fixed"
    if policy.get("terminal_nodes") != ["PARKED", "HOLD"]:
        return "observation policy terminals are not the parked/hold ceiling"
    if policy.get("required_nodes") != [
        "observe-foreign-eval",
        "replay-verify-foreign-eval",
    ]:
        return "observation policy required nodes are not fixed"
    if policy.get("bounds") != _FIXED_BOUNDS:
        return "observation policy bounds are not fixed"
    if policy.get("claim_ceiling") != _CLAIM_CEILING:
        return "observation policy claim ceiling is not fixed"
    if policy.get("promotion_allowed") is not False:
        return "observation policy attempted promotion"
    if "execution_lease" in policy:
        return "observation policy added an unneeded execution lease"
    source_path = str(Path(__file__).resolve())
    source_sha256 = _source_sha256(Path(__file__).resolve())
    expected_hooks = [
        {
            "hook_id": "observe-foreign-eval",
            "kind": HookKind.TOOL.value,
            "module": __name__,
            "qualname": _capture_foreign_eval_tool.__qualname__,
            "source_path": source_path,
            "source_sha256": source_sha256,
            "allowed_signals": [HookSignal.OBSERVED.value, HookSignal.PARKED.value],
            "allowed_update_keys": [
                "lev_eval_observation_capture_state",
                "lev_eval_observation_receipt_sha256",
                "lev_eval_observation_request_sha256",
                "lev_eval_snapshot_sha256",
            ],
            "max_output_bytes": 65_536,
        },
        {
            "hook_id": "replay-verify-foreign-eval",
            "kind": HookKind.GATE.value,
            "module": __name__,
            "qualname": _replay_foreign_eval_gate.__qualname__,
            "source_path": source_path,
            "source_sha256": source_sha256,
            "allowed_signals": [HookSignal.PASS.value],
            "allowed_update_keys": ["lev_eval_observation_replay_state"],
            "max_output_bytes": 65_536,
        },
    ]
    stored_hooks = policy.get("hooks")
    if not isinstance(stored_hooks, list) or len(stored_hooks) != len(expected_hooks):
        return "observation policy hooks are not the fixed controller hooks"
    expected_hook_keys = {
        "hook_id",
        "kind",
        "module",
        "qualname",
        "source_path",
        "source_sha256",
        "code_sha256",
        "allowed_signals",
        "allowed_update_keys",
        "max_output_bytes",
    }
    for expected, stored in zip(expected_hooks, stored_hooks, strict=True):
        if not isinstance(stored, dict) or set(stored) != expected_hook_keys:
            return "observation policy hooks are not the fixed controller hooks"
        differing = sorted(
            key for key, value in expected.items() if stored.get(key) != value
        )
        if differing:
            return (
                "observation policy hook identity drifted: "
                f"{expected['hook_id']} fields={','.join(differing)}"
            )
        code_sha256 = stored.get("code_sha256")
        if (
            not isinstance(code_sha256, str)
            or len(code_sha256) != 64
            or any(character not in "0123456789abcdef" for character in code_sha256)
        ):
            return "observation policy hook code digest is malformed"
    return None


def _receipt_keeps_foreign_input_private(
    receipt: dict[str, Any],
    binding: LevEvalObservationBinding,
) -> bool:
    """Ensure the Mini-Lev ledger retained only commitments, never raw input."""

    try:
        encoded = canonical_json(receipt).decode("utf-8")
    except (TypeError, ValueError, UnicodeDecodeError):
        return False
    return (
        str(binding.source_run_dir) not in encoded
        and "decision_verdict" not in encoded
        and "decision_reason_code" not in encoded
        and "foreign_claim_gate_authenticated" not in encoded
    )


def _active_state(context: dict[str, Any]) -> _ActiveObservationRun:
    metadata = context.get(CONTROLLER_METADATA_KEY)
    if not isinstance(metadata, dict) or set(metadata) != {
        "schema",
        "run_id",
        "policy_sha256",
        "node_id",
        "hook_id",
        "hook_kind",
    }:
        raise LevEvalObservationFlowError("Mini-Lev controller metadata is invalid")
    run_id = metadata.get("run_id")
    if not isinstance(run_id, str):
        raise LevEvalObservationFlowError("Mini-Lev controller run id is invalid")
    with _ACTIVE_RUNS_LOCK:
        state = _ACTIVE_RUNS.get(run_id)
    if state is None:
        raise LevEvalObservationFlowError("observation flow has no active controller state")
    return state


def _capture_foreign_eval_tool(context: dict[str, Any]) -> HookResult:
    """Capture one selected bundle and expose only fixed scalar commitments."""

    state = _active_state(context)
    with state.lock:
        if state.capture_started:
            raise LevEvalObservationFlowError("observation capture was invoked twice")
        state.capture_started = True
        source_run_dir = state.binding.source_run_dir
        if not isinstance(source_run_dir, Path):
            raise LevEvalObservationFlowError(
                "active capture binding lacks its controller-private source path"
            )
        try:
            captured = observe_lev_eval_bundle(
                source_run_dir=source_run_dir,
                observation_run_dir=state.observation_run_dir,
                binding=state.binding,
            )
        except LevEvalObservationHoldError:
            raise
        except LevEvalObservationError:
            return HookResult(
                HookSignal.PARKED,
                {"capture_state": "foreign_bundle_unavailable_or_rejected"},
                {
                    "lev_eval_observation_capture_state": "foreign_bundle_unavailable_or_rejected",
                },
            )
        snapshot_sha256 = captured.receipt["foreign_observation"].get(
            "snapshot_sha256"
        )
        if not isinstance(snapshot_sha256, str) or len(snapshot_sha256) != 64:
            raise LevEvalObservationFlowError(
                "observer did not return one bounded snapshot commitment"
            )
        return HookResult(
            HookSignal.OBSERVED,
            {
                "capture_state": "retained",
                "observation_request_sha256": state.binding.request_sha256,
                "observation_receipt_sha256": captured.receipt_sha256,
                "snapshot_sha256": snapshot_sha256,
            },
            {
                "lev_eval_observation_capture_state": "retained",
                "lev_eval_observation_request_sha256": state.binding.request_sha256,
                "lev_eval_observation_receipt_sha256": captured.receipt_sha256,
                "lev_eval_snapshot_sha256": snapshot_sha256,
            },
        )


def _replay_foreign_eval_gate(context: dict[str, Any]) -> HookResult:
    """Replay the CB-owned snapshot without consulting a foreign verdict."""

    state = _active_state(context)
    with state.lock:
        request_sha256 = context.get("lev_eval_observation_request_sha256")
        receipt_sha256 = context.get("lev_eval_observation_receipt_sha256")
        snapshot_sha256 = context.get("lev_eval_snapshot_sha256")
        if not all(
            isinstance(value, str)
            for value in (request_sha256, receipt_sha256, snapshot_sha256)
        ):
            raise LevEvalObservationFlowError(
                "observation gate context lacks scalar capture commitments"
            )
        if request_sha256 != state.binding.request_sha256:
            raise LevEvalObservationFlowError(
                "observation request commitment differs from active controller binding"
            )
        replayed = verify_lev_eval_observation_snapshot(
            observation_run_dir=state.observation_run_dir,
            expected_binding=state.binding,
            expected_receipt_sha256=receipt_sha256,
        )
        replay_snapshot_sha256 = replayed.receipt["foreign_observation"].get(
            "snapshot_sha256"
        )
        if replay_snapshot_sha256 != snapshot_sha256:
            raise LevEvalObservationFlowError(
                "observation snapshot commitment differs after retained replay"
            )
        return HookResult(
            HookSignal.PASS,
            {
                "replay_state": "retained_snapshot_rechecked",
                "observation_request_sha256": request_sha256,
                "observation_receipt_sha256": receipt_sha256,
                "snapshot_sha256": snapshot_sha256,
            },
            {
                "lev_eval_observation_replay_state": "retained_snapshot_rechecked",
            },
        )


def build_lev_eval_observation_flow(
    *,
    run_id: str,
    ledger_path: Path,
) -> MiniLevRuntime:
    """Construct the exact two-node historical-observation flow."""

    capture = _source_registration(
        hook_id="observe-foreign-eval",
        kind=HookKind.TOOL,
        handler=_capture_foreign_eval_tool,
        allowed_signals=(HookSignal.OBSERVED, HookSignal.PARKED),
        allowed_update_keys=(
            "lev_eval_observation_capture_state",
            "lev_eval_observation_request_sha256",
            "lev_eval_observation_receipt_sha256",
            "lev_eval_snapshot_sha256",
        ),
    )
    replay = _source_registration(
        hook_id="replay-verify-foreign-eval",
        kind=HookKind.GATE,
        handler=_replay_foreign_eval_gate,
        allowed_signals=(HookSignal.PASS,),
        allowed_update_keys=("lev_eval_observation_replay_state",),
    )
    policy = FlowPolicy(
        flow_id=FLOW_ID,
        entry_node="observe-foreign-eval",
        nodes=(
            FlowNode("observe-foreign-eval", capture.hook_id),
            FlowNode("replay-verify-foreign-eval", replay.hook_id),
        ),
        transitions=(
            FlowTransition(
                "observe-foreign-eval",
                HookSignal.OBSERVED,
                "replay-verify-foreign-eval",
            ),
            FlowTransition("observe-foreign-eval", HookSignal.PARKED, "PARKED"),
            FlowTransition("observe-foreign-eval", HookSignal.HOLD, "HOLD"),
            FlowTransition("replay-verify-foreign-eval", HookSignal.PASS, "PARKED"),
            FlowTransition("replay-verify-foreign-eval", HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("PARKED", "HOLD"),
        required_nodes=("observe-foreign-eval", "replay-verify-foreign-eval"),
        max_steps=2,
        max_visits_per_node=1,
        max_retries=0,
        max_context_bytes=16_384,
        max_event_bytes=65_536,
        max_receipt_bytes=524_288,
        claim_ceiling=_CLAIM_CEILING,
    )
    try:
        return MiniLevRuntime(
            policy,
            (capture, replay),
            run_id=run_id,
            ledger_path=ledger_path,
        )
    except MiniLevError as exc:
        raise LevEvalObservationFlowError(
            f"observation flow construction failed: {exc}"
        ) from exc


def _persist_exclusive(path: Path, value: dict[str, Any]) -> None:
    if path.name not in {FLOW_BINDING_NAME, FLOW_RECEIPT_NAME}:
        raise LevEvalObservationFlowError("observation flow artifact path is not fixed")
    root = path.parent
    try:
        root_metadata = root.lstat()
    except OSError as exc:
        raise LevEvalObservationFlowError(
            "observation flow root is unavailable for artifact persistence"
        ) from exc
    if root.is_symlink() or stat.S_ISLNK(root_metadata.st_mode):
        raise LevEvalObservationFlowError(
            "observation flow root must not be a symlink for artifact persistence"
        )
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise LevEvalObservationFlowError(
            "observation flow root is not a directory for artifact persistence"
        )
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        root_fd = os.open(root, directory_flags)
    except OSError as exc:
        raise LevEvalObservationFlowError(
            "observation flow root could not be opened for artifact persistence"
        ) from exc
    descriptor = -1
    try:
        opened_root = os.fstat(root_fd)
        if (
            not stat.S_ISDIR(opened_root.st_mode)
            or opened_root.st_dev != root_metadata.st_dev
            or opened_root.st_ino != root_metadata.st_ino
        ):
            raise LevEvalObservationFlowError(
                "observation flow root changed during artifact persistence"
            )
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        descriptor = os.open(path.name, flags, 0o600, dir_fd=root_fd)
        with os.fdopen(descriptor, "w", encoding="utf-8", closefd=True) as stream:
            descriptor = -1
            stream.write(canonical_json(value).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(root_fd)
    except FileExistsError as exc:
        raise LevEvalObservationFlowError(
            f"observation flow artifact already exists: {path.name}"
        ) from exc
    except OSError as exc:
        raise LevEvalObservationFlowError(
            f"observation flow artifact persistence failed: {exc}"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(root_fd)


def _read_persisted_flow_artifact(
    *,
    flow_root: Path,
    artifact_name: str,
    maximum_bytes: int,
) -> bytes:
    """Read one controller-owned artifact without path-following escapes."""

    if artifact_name not in {FLOW_BINDING_NAME, FLOW_RECEIPT_NAME}:
        raise LevEvalObservationFlowError(
            "observation flow artifact name is not fixed"
        )
    if isinstance(maximum_bytes, bool) or not isinstance(maximum_bytes, int) or maximum_bytes < 1:
        raise LevEvalObservationFlowError("observation flow artifact bound is invalid")
    try:
        root_metadata = flow_root.lstat()
    except OSError as exc:
        raise LevEvalObservationFlowError(
            "observation flow root is unavailable for artifact replay"
        ) from exc
    if flow_root.is_symlink() or stat.S_ISLNK(root_metadata.st_mode):
        raise LevEvalObservationFlowError(
            "observation flow root must not be a symlink during artifact replay"
        )
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise LevEvalObservationFlowError(
            "observation flow root is not a directory during artifact replay"
        )
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        root_fd = os.open(flow_root, directory_flags)
    except OSError as exc:
        raise LevEvalObservationFlowError(
            "observation flow root could not be opened for artifact replay"
        ) from exc
    try:
        opened_root = os.fstat(root_fd)
        if (
            not stat.S_ISDIR(opened_root.st_mode)
            or opened_root.st_dev != root_metadata.st_dev
            or opened_root.st_ino != root_metadata.st_ino
        ):
            raise LevEvalObservationFlowError(
                "observation flow root changed during artifact replay"
            )
        try:
            receipt_metadata = os.stat(
                artifact_name,
                dir_fd=root_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise LevEvalObservationFlowError(
                "observation flow artifact is unavailable for replay"
            ) from exc
        if (
            stat.S_ISLNK(receipt_metadata.st_mode)
            or not stat.S_ISREG(receipt_metadata.st_mode)
            or receipt_metadata.st_size > maximum_bytes + 1
        ):
            raise LevEvalObservationFlowError(
                "observation flow artifact is not one bounded regular file"
            )
        receipt_flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            receipt_fd = os.open(
                artifact_name,
                receipt_flags,
                dir_fd=root_fd,
            )
        except OSError as exc:
            raise LevEvalObservationFlowError(
                "observation flow artifact could not be opened for replay"
            ) from exc
        try:
            opened_receipt = os.fstat(receipt_fd)
            if (
                not stat.S_ISREG(opened_receipt.st_mode)
                or opened_receipt.st_dev != receipt_metadata.st_dev
                or opened_receipt.st_ino != receipt_metadata.st_ino
                or opened_receipt.st_size != receipt_metadata.st_size
            ):
                raise LevEvalObservationFlowError(
                    "observation flow artifact changed before replay"
                )
            with os.fdopen(receipt_fd, "rb", closefd=True) as stream:
                receipt_fd = -1
                raw = stream.read(maximum_bytes + 2)
                after = os.fstat(stream.fileno())
            if (
                len(raw) != opened_receipt.st_size
                or after.st_dev != opened_receipt.st_dev
                or after.st_ino != opened_receipt.st_ino
                or after.st_size != opened_receipt.st_size
                or after.st_mtime_ns != opened_receipt.st_mtime_ns
            ):
                raise LevEvalObservationFlowError(
                    "observation flow artifact changed during replay"
                )
            return raw
        finally:
            if receipt_fd >= 0:
                os.close(receipt_fd)
    finally:
        os.close(root_fd)


def _read_canonical_flow_object(
    *,
    flow_root: Path,
    artifact_name: str,
    maximum_bytes: int,
) -> dict[str, Any]:
    """Load an exact canonical controller artifact from the retained flow root."""

    raw = _read_persisted_flow_artifact(
        flow_root=flow_root,
        artifact_name=artifact_name,
        maximum_bytes=maximum_bytes,
    )
    try:
        value = parse_json_object(raw)
    except IntakeError as exc:
        raise LevEvalObservationFlowError(
            "persisted observation flow artifact is not strict JSON"
        ) from exc
    if raw != canonical_json(value) + b"\n":
        raise LevEvalObservationFlowError(
            "persisted observation flow artifact is not exclusively canonical"
        )
    return value


def _read_persisted_binding(flow_root: Path) -> LevEvalObservationBinding:
    try:
        return LevEvalObservationBinding.from_dict(
            _read_canonical_flow_object(
                flow_root=flow_root,
                artifact_name=FLOW_BINDING_NAME,
                maximum_bytes=16_384,
            )
        )
    except LevEvalObservationHoldError as exc:
        raise LevEvalObservationFlowError(
            "persisted observation binding is invalid"
        ) from exc


def run_lev_eval_observation_flow(
    *,
    request_id: str,
    source_run_dir: Path,
    expected_execution_id: str,
    expected_suite_id: str,
    run_root: Path,
) -> LevEvalObservationFlowResult:
    """Retain and replay one historical Lev bundle through Mini-LevOS.

    The controller deliberately does not accept a mode, hook, transition,
    foreign verdict, or terminal override.  The successful structural route
    ends parked because the required cross-system semantic comparator has not
    yet been built.
    """

    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise LevEvalObservationFlowError("flow run_root must be an absolute pathlib.Path")
    flow_root = run_root.expanduser().resolve(strict=False)
    if flow_root.exists():
        raise LevEvalObservationFlowError("observation flow root must not already exist")
    binding = build_lev_eval_observation_binding(
        request_id=request_id,
        source_run_dir=source_run_dir,
        expected_execution_id=expected_execution_id,
        expected_suite_id=expected_suite_id,
    )
    try:
        flow_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise LevEvalObservationFlowError(
            f"observation flow root creation failed: {exc}"
        ) from exc
    run_id = "lev-eval-observation-" + secrets.token_hex(16)
    try:
        runtime = build_lev_eval_observation_flow(
            run_id=run_id,
            ledger_path=flow_root / FLOW_LEDGER_NAME,
        )
    except Exception:
        try:
            flow_root.rmdir()
        except OSError:
            pass
        raise
    state = _ActiveObservationRun(
        binding=binding,
        flow_root=flow_root,
        lock=threading.RLock(),
    )
    with _ACTIVE_RUNS_LOCK:
        if run_id in _ACTIVE_RUNS:
            raise LevEvalObservationFlowError("observation flow run id collision")
        _ACTIVE_RUNS[run_id] = state
    try:
        flow_receipt = runtime.run(
            {"lev_eval_observation_request_sha256": binding.request_sha256}
        )
        result = LevEvalObservationFlowResult(
            request_id=request_id,
            binding=binding,
            run_id=run_id,
            terminal=flow_receipt["terminal"],
            flow_root=flow_root,
            flow_receipt_path=flow_root / FLOW_RECEIPT_NAME,
            flow_ledger_path=runtime.ledger_path,
            flow_receipt_sha256=runtime.receipt_sha256,
            flow_receipt=flow_receipt,
        )
        _persist_exclusive(flow_root / FLOW_BINDING_NAME, binding.as_dict())
        _persist_exclusive(result.flow_receipt_path, flow_receipt)
        valid, reason = verify_lev_eval_observation_flow(result)
        if not valid:
            raise LevEvalObservationFlowError(
                f"observation flow receipt failed verification: {reason}"
            )
        return result
    except MiniLevError as exc:
        raise LevEvalObservationFlowError(
            f"observation flow execution failed: {exc}"
        ) from exc
    finally:
        with _ACTIVE_RUNS_LOCK:
            _ACTIVE_RUNS.pop(run_id, None)


def verify_lev_eval_observation_flow(
    result: LevEvalObservationFlowResult,
) -> tuple[bool, str]:
    """Verify the Mini-Lev route and its retained observation snapshot."""

    if type(result) is not LevEvalObservationFlowResult:
        return False, "observation flow result type is invalid"
    fixed_reason = _fixed_policy_reason(result.flow_receipt)
    if fixed_reason is not None:
        return False, fixed_reason
    if not _receipt_keeps_foreign_input_private(result.flow_receipt, result.binding):
        return False, "observation flow receipt exposes foreign input or authority data"
    if result.terminal not in {"PARKED", "HOLD"}:
        return False, "observation flow result has an invalid terminal"
    try:
        persisted_binding = _read_persisted_binding(result.flow_root)
        persisted_receipt = _read_canonical_flow_object(
            flow_root=result.flow_root,
            artifact_name=FLOW_RECEIPT_NAME,
            maximum_bytes=524_288,
        )
    except LevEvalObservationFlowError as exc:
        return False, str(exc)
    if result.flow_receipt_path != result.flow_root / FLOW_RECEIPT_NAME:
        return False, "observation flow receipt path is not the fixed controller path"
    if persisted_binding.as_dict() != result.binding.as_dict():
        return False, "persisted observation binding differs from replay input"
    if persisted_receipt != result.flow_receipt:
        return False, "persisted observation flow receipt differs from replay input"
    try:
        valid, reason = verify_flow_receipt(
            result.flow_receipt,
            expected_run_id=result.run_id,
            expected_policy_sha256=result.flow_receipt["policy_sha256"],
            expected_ledger_path=result.flow_ledger_path,
            expected_retained_head_sha256=result.flow_receipt["ledger"][
                "retained_head_sha256"
            ],
            expected_receipt_sha256=result.flow_receipt_sha256,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return False, f"observation flow receipt binding is malformed: {exc}"
    if not valid:
        return False, f"Mini-Lev receipt failed replay: {reason}"
    if result.terminal == "HOLD" and result.flow_receipt["terminal"] == "HOLD":
        return True, "observation flow held on a local capture or replay integrity failure"
    if result.terminal != "PARKED" or result.flow_receipt["terminal"] != "PARKED":
        return False, "observation flow may only terminate PARKED or HOLD"
    initial_context = result.flow_receipt.get("initial_context")
    if initial_context != {
        "lev_eval_observation_request_sha256": result.binding.request_sha256
    }:
        return False, "observation flow initial context leaked or changed its binding"
    final_context = result.flow_receipt.get("final_context")
    if not isinstance(final_context, dict):
        return False, "observation flow final context is invalid"
    capture_state = final_context.get("lev_eval_observation_capture_state")
    if capture_state == "foreign_bundle_unavailable_or_rejected":
        if result.flow_receipt.get("steps") != 1:
            return False, "parked foreign rejection unexpectedly reached the replay gate"
        if result.flow_receipt.get("completed_nodes") != []:
            return False, "parked foreign rejection completed a non-observation node"
        if final_context != {
            "lev_eval_observation_request_sha256": result.binding.request_sha256,
            "lev_eval_observation_capture_state": "foreign_bundle_unavailable_or_rejected",
        }:
            return False, "parked foreign rejection retained unexpected context"
        return True, "foreign bundle was parked before capture"
    if capture_state != "retained":
        return False, "observation flow capture state is invalid"
    expected_scalars = {
        "lev_eval_observation_request_sha256": result.binding.request_sha256,
        "lev_eval_observation_capture_state": "retained",
        "lev_eval_observation_replay_state": "retained_snapshot_rechecked",
    }
    if any(final_context.get(key) != value for key, value in expected_scalars.items()):
        return False, "observation flow replay context is invalid"
    receipt_sha256 = final_context.get("lev_eval_observation_receipt_sha256")
    snapshot_sha256 = final_context.get("lev_eval_snapshot_sha256")
    if not isinstance(receipt_sha256, str) or not isinstance(snapshot_sha256, str):
        return False, "observation flow lacks retained snapshot commitments"
    if set(final_context) != {
        "lev_eval_observation_request_sha256",
        "lev_eval_observation_capture_state",
        "lev_eval_observation_receipt_sha256",
        "lev_eval_snapshot_sha256",
        "lev_eval_observation_replay_state",
    }:
        return False, "observation flow retained unexpected final context"
    try:
        replayed = verify_lev_eval_observation_snapshot(
            observation_run_dir=result.flow_root / OBSERVATION_DIRECTORY_NAME,
            expected_binding=result.binding,
            expected_receipt_sha256=receipt_sha256,
        )
    except LevEvalObservationError as exc:
        return False, f"retained observation snapshot failed replay: {exc}"
    if replayed.receipt["foreign_observation"].get("snapshot_sha256") != snapshot_sha256:
        return False, "observation flow snapshot commitment differs after replay"
    if result.flow_receipt.get("steps") != 2:
        return False, "retained observation did not execute both fixed nodes"
    if result.flow_receipt.get("completed_nodes") != [
        "observe-foreign-eval",
        "replay-verify-foreign-eval",
    ]:
        return False, "retained observation did not complete the fixed nodes"
    return True, "retained foreign bundle replayed and remains parked"


def load_lev_eval_observation_flow(
    flow_root: Path,
) -> LevEvalObservationFlowResult:
    """Reload and verify one durable observation flow without its source path.

    This is the post-restart audit entry point.  The controller-private source
    path is never persisted here: snapshot replay derives and hash-checks its
    text from the retained raw Lev bytes only.
    """

    if not isinstance(flow_root, Path) or not flow_root.is_absolute():
        raise LevEvalObservationFlowError("flow root must be an absolute pathlib.Path")
    root = flow_root.expanduser().resolve(strict=False)
    binding = _read_persisted_binding(root)
    flow_receipt = _read_canonical_flow_object(
        flow_root=root,
        artifact_name=FLOW_RECEIPT_NAME,
        maximum_bytes=524_288,
    )
    run_id = flow_receipt.get("run_id")
    terminal = flow_receipt.get("terminal")
    receipt_sha256 = flow_receipt.get("receipt_sha256")
    if not all(
        isinstance(value, str) and value
        for value in (run_id, terminal, receipt_sha256)
    ):
        raise LevEvalObservationFlowError(
            "persisted observation flow receipt lacks fixed identifiers"
        )
    result = LevEvalObservationFlowResult(
        request_id=binding.request_id,
        binding=binding,
        run_id=run_id,
        terminal=terminal,
        flow_root=root,
        flow_receipt_path=root / FLOW_RECEIPT_NAME,
        flow_ledger_path=root / FLOW_LEDGER_NAME,
        flow_receipt_sha256=receipt_sha256,
        flow_receipt=flow_receipt,
    )
    valid, reason = verify_lev_eval_observation_flow(result)
    if not valid:
        raise LevEvalObservationFlowError(
            f"persisted observation flow failed verification: {reason}"
        )
    return result
