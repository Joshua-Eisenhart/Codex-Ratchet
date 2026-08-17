"""Compact, deterministic ZIP checkpoint for stateless ConstraintBox resumption."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

from .failure_wave import _manifest, _task
from .protocol import build_packet, canonical_json_bytes


SCHEMA = "constraintbox.resume-checkpoint.v1"
MANIFEST_CLAIM_CEILING = "append_only_project_memory;not_admission;not_release"
CLAIM_CEILING = (
    "transported resumable project snapshot with a verified ledger binding; "
    "not the full ledger, not execution authority, not admission, and not promotion"
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_resume_checkpoint_packet(
    *,
    materials: Mapping[str, bytes],
    ledger_binding: Mapping[str, Any],
    next_actions: Sequence[str],
    captured_at: str,
) -> bytes:
    """Build one self-contained checkpoint packet from exact source bytes."""
    if not materials:
        raise ValueError("materials must be nonempty")
    if ledger_binding.get("disposition") != "PROJECT_LEDGER_VERIFIED":
        raise ValueError("ledger binding is not verified")
    if ledger_binding.get("objects_verified") is not True:
        raise ValueError("ledger objects are not verified")
    if not isinstance(captured_at, str) or not captured_at:
        raise ValueError("captured_at must be nonempty")
    if not next_actions or any(not isinstance(item, str) or not item for item in next_actions):
        raise ValueError("next_actions must be nonempty strings")

    rows: list[dict[str, Any]] = []
    for logical_id, raw in sorted(materials.items()):
        if not isinstance(logical_id, str) or not logical_id:
            raise ValueError("material logical_id must be nonempty")
        if not isinstance(raw, bytes):
            raise TypeError(f"material {logical_id} must be bytes")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"material {logical_id} is not UTF-8") from exc
        rows.append(
            {
                "logical_id": logical_id,
                "sha256": _sha256(raw),
                "size": len(raw),
                "encoding": "utf-8",
                "text": text,
            }
        )

    identity_material = {
        "captured_at": captured_at,
        "materials": rows,
        "ledger": {
            "event_count": ledger_binding.get("event_count"),
            "head_sha256": ledger_binding.get("head_sha256"),
            "objects_verified": True,
        },
        "next_actions": list(next_actions),
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    identity_sha256 = _sha256(canonical_json_bytes(identity_material))
    checkpoint = {
        "schema": SCHEMA,
        "checkpoint_id": f"cb-resume-{identity_sha256[:24]}",
        "identity_sha256": identity_sha256,
        **identity_material,
    }
    checkpoint_bytes = canonical_json_bytes(checkpoint)
    task_path = "tasks/00_verify_checkpoint.task.json"
    output_path = "output/checkpoint_digest.json"
    files = {
        "00_RUN_ME_FIRST.md": (
            "# ConstraintBox stateless resume checkpoint\n\n"
            "Read `inputs/checkpoint.json`. Its material rows carry the exact "
            "bounded project context and next actions. CB, not this prose, owns "
            "validation and task order. Run and verify the ZIP before using it.\n"
        ).encode("utf-8"),
        "inputs/checkpoint.json": checkpoint_bytes,
        task_path: _task(
            task_id="verify-resume-checkpoint",
            sequence=0,
            operation="canonical_json_sha256_v1",
            inputs=["inputs/checkpoint.json"],
            outputs=[output_path],
        ),
    }
    return build_packet(
        _manifest(
            job_id=checkpoint["checkpoint_id"],
            task_paths=[task_path],
            outputs=[output_path],
            operations=["canonical_json_sha256_v1"],
            claim_ceiling=MANIFEST_CLAIM_CEILING,
        ),
        files,
    )
