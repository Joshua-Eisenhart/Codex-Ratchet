"""Confirm MMM packs were loaded into an LLM prompt before any spawn.

CB does not launch a model on a request that only names packs. The gate
recomputes the declared packs from disk, matches the declared sha256, and
requires the recomputed pack bytes to appear as a contiguous substring of
the prompt. Missing, drifted, or unused packs refuse before the process
starts.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Mapping

SAFE_PACK = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")
BOX_ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = Path(
    os.environ.get("CB_MMM_PACKS_ROOT", str(BOX_ROOT / "mmm" / "packs"))
).expanduser().absolute()
SEPARATOR = "\n\n---\n\n"


class MmmLoadError(ValueError):
    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        super().__init__(detail)


def discover_packs() -> list[str]:
    return sorted(path.stem for path in PACKS_DIR.glob("*.md") if path.is_file())


def compose_packs(names: list[str]) -> str:
    available = set(discover_packs())
    bodies: list[str] = []
    for name in names:
        if name not in available:
            raise MmmLoadError("REFUSE_MMM_PACKS_INVALID", f"unknown pack: {name}")
        bodies.append((PACKS_DIR / f"{name}.md").read_text(encoding="utf-8"))
    return SEPARATOR.join(bodies)


DEFAULT_REQUIRED_PACKS = ("nominalist", "smt")


def materialize_bound_prompt(
    source: Path,
    dest: Path,
    packs: list[str] | None = None,
) -> dict[str, Any]:
    """Copy ``source`` to ``dest``, prepend missing packs, and return request fields."""
    names = list(packs or DEFAULT_REQUIRED_PACKS)
    text = compose_packs(names)
    raw = text.encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    existing = source.read_bytes()
    bound = existing if raw in existing else raw + b"\n\n" + existing
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(bound)
    return confirm_mmm_load({"mmm_packs": names, "mmm_sha256": digest}, bound)


def confirm_job_mmm(job: Any) -> dict[str, Any]:
    """Confirm a provider job declared packs and loaded them into its prompt."""
    task = getattr(job, "task", None)
    packs = getattr(job, "mmm_packs", None)
    digest = getattr(job, "mmm_sha256", None)
    prompt = getattr(job, "prompt", None)
    if task is not None:
        if not packs:
            packs = getattr(task, "mmm_packs", None)
        if not digest:
            digest = getattr(task, "mmm_sha256", None)
        if prompt is None:
            prompt = getattr(task, "prompt", "")
    request: dict[str, Any] = {}
    if packs:
        request["mmm_packs"] = list(packs)
    if digest:
        request["mmm_sha256"] = digest
    raw = prompt.encode("utf-8") if isinstance(prompt, str) else (prompt or b"")
    return confirm_mmm_load(request, raw)


def confirm_mmm_load(request: Mapping[str, Any], prompt: bytes) -> dict[str, Any]:
    """Return a confirmation record or raise before any LLM spawn."""
    if "mmm_packs" not in request or "mmm_sha256" not in request:
        raise MmmLoadError(
            "REFUSE_MMM_LOAD_MISSING",
            "mmm_packs and mmm_sha256 are required before any LLM spawn",
        )
    packs = request["mmm_packs"]
    declared = request["mmm_sha256"]
    if not isinstance(packs, list) or not packs:
        raise MmmLoadError("REFUSE_MMM_PACKS_INVALID", "mmm_packs must be a nonempty list")
    if any(not isinstance(name, str) or SAFE_PACK.fullmatch(name) is None for name in packs):
        raise MmmLoadError("REFUSE_MMM_PACKS_INVALID", "mmm_packs entries are invalid")
    if not isinstance(declared, str) or SHA256_HEX.fullmatch(declared) is None:
        raise MmmLoadError("REFUSE_MMM_PACKS_INVALID", "mmm_sha256 is invalid")
    text = compose_packs(packs)
    raw = text.encode("utf-8")
    observed = hashlib.sha256(raw).hexdigest()
    if observed != declared:
        raise MmmLoadError(
            "REFUSE_MMM_SHA256_MISMATCH",
            f"declared {declared} recomputed {observed}",
        )
    if raw not in prompt:
        raise MmmLoadError(
            "REFUSE_MMM_NOT_IN_PROMPT",
            "recomputed pack bytes are not a contiguous substring of the prompt",
        )
    return {
        "mmm_packs": list(packs),
        "mmm_sha256": observed,
        "mmm_bytes": len(raw),
        "mmm_load_confirmed": True,
    }
