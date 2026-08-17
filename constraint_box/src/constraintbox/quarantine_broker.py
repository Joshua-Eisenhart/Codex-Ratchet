"""Fixture quarantine broker — first slice, no spawn.

Outside proposals enter typed inbox. Deterministic gates settle.
Connector output is an inert observation. Never authoritative.

Codex failure-wave first slice:
  LaunchRequest → current BasinView → pydantic+jsonschema
  → rustworkx no connector→spawn → Automaton Propose→Quarantine
  → fixture ConnectorResult → quarantine
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any, Literal

import jsonschema
import rustworkx as rx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .basin_view_valve import BasinViewHold, require_basin_view

CLAIM = (
    "fixture quarantine only; not a live connector, not spawn, "
    "not SQLite authority, not promotion"
)
SCHEMA = "constraintbox.quarantine_broker.v1"
VERIFY_SCHEMA = "constraintbox.quarantine_receipt_verify.v1"

REQUEST_JSONSCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "request_id",
        "operation_id",
        "probe_digest",
        "from_state",
        "to_state",
    ],
    "properties": {
        # This is an outside correlation key, never the box's invocation ID.
        # The broker derives an opaque invocation ID after it has checked the
        # current deterministic authority.  Reusing a request_id binds the
        # caller to the original request and authority material.
        "request_id": {
            "type": "string",
            "minLength": 8,
            "maxLength": 128,
            "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$",
        },
        "operation_id": {"type": "string", "minLength": 3},
        "probe_digest": {"type": "string", "minLength": 8},
        "from_state": {"type": "string", "enum": ["inbox", "propose"]},
        "to_state": {"type": "string", "enum": ["propose", "quarantine"]},
        "note": {"type": "string"},
    },
}

LEGAL_TRANSITIONS = {("inbox", "propose"), ("propose", "quarantine")}
FORBIDDEN_KEYS = {
    "execute",
    "spawn",
    "promote",
    "sqlite_write",
    "model",
    "disposition",
    # Invocation IDs are issued by the broker.  A connector may correlate a
    # request, but cannot select or replay an authority identity directly.
    "invocation_id",
}
RECEIPT_DIR = Path(__file__).resolve().parents[2] / "receipts" / "box" / "quarantine"


class ProbeProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$",
    )
    operation_id: str = Field(min_length=3)
    probe_digest: str = Field(min_length=8)
    from_state: Literal["inbox", "propose"]
    to_state: Literal["propose", "quarantine"]
    note: str = ""


class ConnectorResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["fixture"] = "fixture"
    observation: str
    authoritative: Literal[False] = False


class BrokerRefuse(Exception):
    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail


class QuarantineReceiptVerificationError(Exception):
    """A retained quarantine receipt cannot support an integrity-only read."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail


def _canon(value: Any) -> bytes:
    """Version-one identity serialization; do not silently change it."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canon(value)).hexdigest()


def _request_slot(receipt_dir: Path, request_id: str) -> Path:
    """Map an untrusted correlation key to a private immutable slot path."""
    request_key = _sha256({"schema": SCHEMA, "request_id": request_id})
    return receipt_dir / "by_request" / f"{request_key}.json"


def _receipt_sha256(receipt: dict[str, Any]) -> str:
    """Integrity binding for the complete immutable receipt body."""
    return _sha256({key: value for key, value in receipt.items() if key != "receipt_sha256"})


_RECEIPT_KEYS = frozenset(
    {
        "schema",
        "ok",
        "reason_code",
        "invocation_id",
        "proposal",
        "connector",
        "identity_sha256",
        "authority_identity_sha256",
        "basin_view",
        "promotion_allowed",
        "authoritative",
        "claim_ceiling",
        "receipt_path",
        "receipt_sha256",
    }
)
_PROPOSAL_KEYS = frozenset(
    {"request_id", "operation_id", "probe_digest", "from_state", "to_state", "note"}
)
_CONNECTOR_KEYS = frozenset({"kind", "observation", "authoritative"})
_BASIN_VIEW_KEYS = frozenset({"operation", "status", "reason_code"})
_AUTHORITY_EDGES = ("inbox->gate", "gate->quarantine", "quarantine->record")


def _verify_error(reason_code: str, detail: str) -> None:
    raise QuarantineReceiptVerificationError(reason_code, detail)


def verify_quarantine_receipt(
    receipt_path: str | Path,
    *,
    receipt_dir: Path | None = None,
) -> dict[str, Any]:
    """Read one quarantine receipt without rerunning its semantic gates.

    This is a deliberately narrow consumer, not a generic receipt framework:
    it checks the immutable receipt's own envelope, canonical hash, private
    request-slot binding, and fixture result.  It never calls Pydantic,
    jsonschema, BasinView, the authority graph, or the automaton again.  It
    therefore says only that the supplied receipt is internally consistent;
    it does not authenticate custody, recompute the old decision, or attest
    that the current source or map still agrees with it.
    """
    root = (receipt_dir or RECEIPT_DIR).resolve()
    by_request = (root / "by_request").resolve()
    path = Path(receipt_path).resolve()
    try:
        path.relative_to(by_request)
    except ValueError:
        _verify_error(
            "REFUSE_QUARANTINE_RECEIPT_PATH_OUTSIDE",
            f"receipt is outside the quarantine request slots: {path}",
        )
    if path.suffix != ".json":
        _verify_error("REFUSE_QUARANTINE_RECEIPT_PATH_OUTSIDE", "receipt path must end in .json")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        _verify_error("HOLD_QUARANTINE_RECEIPT_MISSING", str(exc))
    except (OSError, json.JSONDecodeError) as exc:
        _verify_error("HOLD_QUARANTINE_RECEIPT_UNREADABLE", str(exc))
    if not isinstance(loaded, dict):
        _verify_error("HOLD_QUARANTINE_RECEIPT_ENVELOPE_INVALID", "receipt is not an object")
    if set(loaded) != _RECEIPT_KEYS:
        _verify_error(
            "HOLD_QUARANTINE_RECEIPT_ENVELOPE_INVALID",
            "receipt fields do not match the fixed quarantine envelope",
        )
    if (
        loaded.get("schema") != SCHEMA
        or loaded.get("ok") is not True
        or loaded.get("reason_code") != "QUARANTINED_FIXTURE"
        or loaded.get("promotion_allowed") is not False
        or loaded.get("authoritative") is not False
        or not isinstance(loaded.get("claim_ceiling"), str)
        or not isinstance(loaded.get("invocation_id"), str)
        or not str(loaded["invocation_id"]).startswith("qv1-")
    ):
        _verify_error("HOLD_QUARANTINE_RECEIPT_ENVELOPE_INVALID", "receipt envelope values are invalid")

    proposal = loaded.get("proposal")
    if not isinstance(proposal, dict) or set(proposal) != _PROPOSAL_KEYS:
        _verify_error("HOLD_QUARANTINE_RECEIPT_ENVELOPE_INVALID", "proposal envelope is invalid")
    if not all(isinstance(proposal.get(key), str) for key in _PROPOSAL_KEYS):
        _verify_error("HOLD_QUARANTINE_RECEIPT_ENVELOPE_INVALID", "proposal values are not strings")
    expected_slot = _request_slot(root, str(proposal["request_id"])).resolve()
    if path != expected_slot:
        _verify_error(
            "REFUSE_QUARANTINE_RECEIPT_SLOT_MISMATCH",
            "receipt location does not match its request-id slot",
        )
    if loaded.get("receipt_path") != str(path):
        _verify_error(
            "HOLD_QUARANTINE_RECEIPT_PATH_BINDING",
            "stored receipt path does not match the consumed slot",
        )
    if loaded.get("identity_sha256") != _sha256(proposal):
        _verify_error(
            "HOLD_QUARANTINE_RECEIPT_IDENTITY_MISMATCH",
            "proposal identity hash does not match the retained proposal",
        )

    connector = loaded.get("connector")
    expected_observation = (
        f"quarantined:{proposal['operation_id']}:{proposal['probe_digest'][:8]}"
    )
    if (
        not isinstance(connector, dict)
        or set(connector) != _CONNECTOR_KEYS
        or connector.get("kind") != "fixture"
        or connector.get("authoritative") is not False
        or connector.get("observation") != expected_observation
    ):
        _verify_error(
            "HOLD_QUARANTINE_RECEIPT_CONNECTOR_MISMATCH",
            "fixture connector envelope does not match retained proposal",
        )

    basin_view = loaded.get("basin_view")
    if (
        not isinstance(basin_view, dict)
        or set(basin_view) != _BASIN_VIEW_KEYS
        or basin_view.get("operation") != proposal["operation_id"]
        or basin_view.get("status") != "BASIN"
        or basin_view.get("reason_code") != "ADMIT_CURRENT_BASIN_VIEW"
    ):
        _verify_error(
            "HOLD_QUARANTINE_RECEIPT_AUTHORITY_MISMATCH",
            "stored BasinView binding is invalid",
        )
    expected_authority = _sha256(
        {
            "schema": SCHEMA,
            "request_identity_sha256": loaded["identity_sha256"],
            "basin_view": basin_view,
            "lifecycle": {
                "from": proposal["from_state"],
                "to": proposal["to_state"],
            },
            "authority_edges": list(_AUTHORITY_EDGES),
        }
    )
    if loaded.get("authority_identity_sha256") != expected_authority:
        _verify_error(
            "HOLD_QUARANTINE_RECEIPT_AUTHORITY_MISMATCH",
            "authority identity does not match the retained envelope",
        )
    if loaded.get("receipt_sha256") != _receipt_sha256(loaded):
        _verify_error(
            "HOLD_QUARANTINE_RECEIPT_INTEGRITY_MISMATCH",
            "receipt canonical hash does not match the retained body",
        )

    return {
        "schema": VERIFY_SCHEMA,
        "ok": True,
        "integrity_result": "RECEIPT_QUARANTINE_ENVELOPE_CONSISTENT",
        "receipt_path": str(path),
        "receipt_sha256": loaded["receipt_sha256"],
        "invocation_id": loaded["invocation_id"],
        "authoritative": False,
        "promotion_allowed": False,
        "claim_ceiling": (
            "read-only quarantine receipt envelope consistency only; not custody, "
            "authenticity, semantic replay, current-map validation, promotion, or spawn"
        ),
    }


def _load_existing_slot(
    path: Path,
    *,
    request_identity_sha256: str,
    authority_identity_sha256: str,
) -> dict[str, Any]:
    """Return an exact replay or refuse a reused/corrupt request slot.

    The live broker does not reinterpret an old receipt as a current decision:
    callers have already passed the current BasinView and lifecycle gates
    before this function runs.  This comparison only protects the immutable
    request slot from replacement or ambiguous replay.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BrokerRefuse("HOLD_REQUEST_SLOT_CORRUPT", str(exc)) from exc
    if not isinstance(data, dict):
        raise BrokerRefuse("HOLD_REQUEST_SLOT_CORRUPT", "receipt slot is not an object")
    if (
        data.get("schema") != SCHEMA
        or not isinstance(data.get("invocation_id"), str)
        or not data.get("invocation_id", "").startswith("qv1-")
    ):
        raise BrokerRefuse("HOLD_REQUEST_SLOT_CORRUPT", "receipt slot envelope is invalid")
    if data.get("receipt_sha256") != _receipt_sha256(data):
        raise BrokerRefuse("HOLD_REQUEST_SLOT_CORRUPT", "receipt integrity binding mismatches")
    if data.get("identity_sha256") != request_identity_sha256:
        raise BrokerRefuse(
            "REFUSE_REQUEST_ID_REUSE_MISMATCH",
            "request_id is already bound to different proposal material",
        )
    if data.get("authority_identity_sha256") != authority_identity_sha256:
        raise BrokerRefuse(
            "HOLD_REQUEST_AUTHORITY_DRIFT",
            "request_id is bound to a different BasinView/lifecycle authority",
        )
    if data.get("receipt_path") != str(path):
        raise BrokerRefuse("HOLD_REQUEST_SLOT_CORRUPT", "receipt path binding is invalid")
    return data


def _create_slot(path: Path, receipt: dict[str, Any]) -> None:
    """Create one receipt slot exactly once; never replace a prior receipt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
    except Exception:
        # Do not delete a partially-created slot: its presence is evidence of a
        # failed custody write and must HOLD the request rather than be hidden.
        raise


def _authority_ok() -> None:
    g = rx.PyDiGraph()
    idx = {n: g.add_node(n) for n in ("inbox", "gate", "connector", "quarantine", "record", "spawn")}
    for a, b in (("inbox", "gate"), ("gate", "quarantine"), ("quarantine", "record")):
        g.add_edge(idx[a], idx[b], None)
    if rx.has_path(g, idx["connector"], idx["spawn"]):
        raise BrokerRefuse("REFUSE_BYPASS", "connector reaches spawn")
    if not rx.is_directed_acyclic_graph(g):
        raise BrokerRefuse("HOLD_GRAPH", "authority graph is cyclic")


def _lifecycle_ok(src: str, dst: str) -> None:
    from automaton.machines import FiniteMachine

    if (src, dst) not in LEGAL_TRANSITIONS:
        raise BrokerRefuse("REFUSE_TRANSITION", f"illegal {src}→{dst}")
    m = FiniteMachine()
    for st in ("inbox", "propose", "quarantine"):
        m.add_state(st, terminal=st == "quarantine")
    m.add_transition("inbox", "propose", "submit")
    m.add_transition("propose", "quarantine", "observe")
    _ = m


def submit(
    raw: dict[str, Any],
    *,
    plan_path: Path | None = None,
    require_view: bool = True,
    receipt_dir: Path | None = None,
) -> dict[str, Any]:
    """Accept a typed proposal and create/replay one immutable receipt.

    ``request_id`` is a caller correlation key.  ``invocation_id`` is issued
    only here, after the deterministic gates have succeeded.  Neither a
    connector nor a hook payload can provide it.
    """
    if any(k in raw for k in FORBIDDEN_KEYS):
        raise BrokerRefuse("REFUSE_TYPED", f"forbidden keys: {sorted(set(raw) & FORBIDDEN_KEYS)}")
    try:
        proposal = ProbeProposal.model_validate(raw)
    except ValidationError as exc:
        raise BrokerRefuse("REFUSE_TYPED", str(exc)) from exc
    try:
        jsonschema.validate(proposal.model_dump(), REQUEST_JSONSCHEMA)
    except jsonschema.ValidationError as exc:
        raise BrokerRefuse("REFUSE_TYPED", exc.message) from exc

    try:
        view = require_basin_view(
            proposal.operation_id,
            plan_path=plan_path,
            require=require_view,
        )
    except BasinViewHold as exc:
        raise BrokerRefuse(exc.reason_code, exc.detail) from exc
    if not view.get("ok"):
        raise BrokerRefuse("HOLD_BASIN_FIELD_INCOMPLETE", f"no current BASIN for {proposal.operation_id}")

    _authority_ok()
    _lifecycle_ok(proposal.from_state, proposal.to_state)

    result = ConnectorResult(
        observation=f"quarantined:{proposal.operation_id}:{proposal.probe_digest[:8]}",
        authoritative=False,
    )
    proposal_data = proposal.model_dump()
    identity = _sha256(proposal_data)
    basin_binding = {
        "operation": view.get("operation"),
        "status": view.get("status"),
        "reason_code": view.get("reason_code"),
    }
    authority_identity = _sha256(
        {
            "schema": SCHEMA,
            "request_identity_sha256": identity,
            "basin_view": basin_binding,
            "lifecycle": {"from": proposal.from_state, "to": proposal.to_state},
            "authority_edges": [
                "inbox->gate",
                "gate->quarantine",
                "quarantine->record",
            ],
        }
    )
    dest_dir = receipt_dir or RECEIPT_DIR
    slot = _request_slot(dest_dir, proposal.request_id)
    if slot.exists():
        return _load_existing_slot(
            slot,
            request_identity_sha256=identity,
            authority_identity_sha256=authority_identity,
        )

    rec = {
        "schema": SCHEMA,
        "ok": True,
        "reason_code": "QUARANTINED_FIXTURE",
        "invocation_id": "qv1-" + secrets.token_hex(16),
        "proposal": proposal_data,
        "connector": result.model_dump(),
        "identity_sha256": identity,
        "authority_identity_sha256": authority_identity,
        "basin_view": basin_binding,
        "promotion_allowed": False,
        "authoritative": False,
        "claim_ceiling": CLAIM,
        "receipt_path": str(slot),
    }
    rec["receipt_sha256"] = _receipt_sha256(rec)
    try:
        _create_slot(slot, rec)
    except FileExistsError:
        # A concurrent writer won the same request slot.  It is an exact
        # replay only if all proposal and authority bindings agree.
        return _load_existing_slot(
            slot,
            request_identity_sha256=identity,
            authority_identity_sha256=authority_identity,
        )
    return rec


def main(argv: list[str] | None = None) -> int:
    """Expose only the read-only retained-receipt consumer as a module CLI."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 3 or args[0] != "verify" or args[1] != "--receipt":
        sys.stderr.write(
            "usage: python -m constraintbox.quarantine_broker verify --receipt PATH\\n"
        )
        return 2
    try:
        result = verify_quarantine_receipt(args[2])
    except QuarantineReceiptVerificationError as exc:
        result = {
            "schema": VERIFY_SCHEMA,
            "ok": False,
            "integrity_result": exc.reason_code,
            "detail": exc.detail,
            "authoritative": False,
            "promotion_allowed": False,
            "claim_ceiling": (
                "read-only quarantine receipt envelope consistency only; not custody, "
                "authenticity, semantic replay, current-map validation, promotion, or spawn"
            ),
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
