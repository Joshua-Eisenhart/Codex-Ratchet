#!/usr/bin/env python3
"""Wizard v4.2 MMM prompt helpers for provider audit lanes."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


PACKET_ROOT = Path.home() / "wiki" / "wizard" / "packet-v4-2-current"
COMPACT_MMM_PATH = PACKET_ROOT / "mmm" / "COMPACT_MMM_v4_2.md"
MINI_MMM_REGISTRY_PATH = PACKET_ROOT / "mmm" / "mini" / "MEMBER_MINI_MMM_REGISTRY_v4_2.md"
SALIENCY_TRANCHE_PATH = PACKET_ROOT / "mmm" / "SALIENCY_TRANCHE_01_CANDIDATE.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _yaml_blocks(markdown: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_block = False
    for line in markdown.splitlines():
        if line.strip() == "```yaml":
            in_block = True
            current = [line]
            continue
        if not in_block:
            continue
        current.append(line)
        if line.strip() == "```":
            blocks.append("\n".join(current))
            in_block = False
            current = []
    return blocks


def _extract_mini_slices(registry_text: str, mini_ids: list[str]) -> str:
    blocks = _yaml_blocks(registry_text)
    selected: list[str] = []
    missing: list[str] = []
    for mini_id in mini_ids:
        needle = f"id: {mini_id}"
        for block in blocks:
            if any(line.strip() == needle for line in block.splitlines()):
                selected.append(block)
                break
        else:
            missing.append(mini_id)
    if missing:
        selected.append("```yaml\nmissing_mini_mmm_ids: " + ", ".join(missing) + "\n```")
    return "\n\n".join(selected)


def build_mmm_prompt_block(*, route_card: str, council_role: str, mini_ids: list[str]) -> tuple[str, dict[str, Any]]:
    """Return a prompt block plus receipt metadata proving the MMM load."""

    compact = _read(COMPACT_MMM_PATH)
    registry = _read(MINI_MMM_REGISTRY_PATH)
    saliency_tranche = _read(SALIENCY_TRANCHE_PATH) if SALIENCY_TRANCHE_PATH.exists() else ""
    mini_slices = _extract_mini_slices(registry, mini_ids)
    metadata = {
        "mmm_loaded": True,
        "mmm_load_kind": "compact_mmm_plus_route_mini_slices_plus_reference_saliency_test",
        "route_card": route_card,
        "council_role": council_role,
        "mmm_source_paths": [
            str(COMPACT_MMM_PATH),
            str(MINI_MMM_REGISTRY_PATH),
            str(SALIENCY_TRANCHE_PATH),
        ],
        "mmm_sha256": {
            str(COMPACT_MMM_PATH): _sha256(compact),
            str(MINI_MMM_REGISTRY_PATH): _sha256(registry),
            str(SALIENCY_TRANCHE_PATH): _sha256(saliency_tranche),
        },
        "route_mini_mmm_ids": mini_ids,
        "compact_mmm_line_count": len(compact.splitlines()),
        "mini_mmm_registry_line_count": len(registry.splitlines()),
        "saliency_tranche_authority": "reference_only_test_material",
        "saliency_tranche_line_count": len(saliency_tranche.splitlines()),
    }
    prompt_block = f"""Wizard v4.2 MMM load for this external provider lane.

Receipt obligations:
- Treat this as an external Wizard audit lane, not local formal evidence.
- Preserve the geometric constraint manifold as the root object.
- Do not promote provider output; return falsifiers, overclaims, blockers, and smallest executable next moves.
- State when a claim is killed, open, blocked, or only scout-level.
- Include an `mmm_saliency_delta` section: name 2-5 concrete priorities,
  blockers, or word choices that changed because of the MMM load. If the MMM
  did not change the answer, say `no_material_delta` and explain why.
- Include a `saliency_failure_mode` section: name the closest way this answer
  could still drift into generic provider/audit behavior despite the MMM.

Route card: {route_card}
Council role: {council_role}
MMM sources:
- {COMPACT_MMM_PATH}
- {MINI_MMM_REGISTRY_PATH}

BEGIN COMPACT_MMM_v4_2
```md
{compact}
```
END COMPACT_MMM_v4_2

BEGIN ROUTE_MINI_MMM_SLICES
{mini_slices}
END ROUTE_MINI_MMM_SLICES

BEGIN REFERENCE_ONLY_SALIENCY_TEST_TRANCHE
Authority boundary: this tranche is reference-only test material, not canonical
runtime boot material. Use it only to test whether salience is being driven
toward constraint-ratchet, finite evidence, noncommutation, artifact-tier
boundaries, killed/open branch preservation, tool-quarantine pressure, and
anti-teleological wording.
```md
{saliency_tranche}
```
END REFERENCE_ONLY_SALIENCY_TEST_TRANCHE
"""
    return prompt_block, metadata
