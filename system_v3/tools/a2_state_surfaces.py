from __future__ import annotations

from pathlib import Path


# Recovery-era boot-critical A2 surfaces plus the canonical persistent-state files.
# Keep this explicit so autosave/snapshot coverage stays deterministic and does not
# accidentally absorb the broad one-off note stack.
_A2_STATE_SURFACE_GLOBS: list[str] = [
    "A2_BOOT_READ_ORDER__CURRENT__v1.md",
    "A2_BRAIN_SLICE__v1.md",
    "A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md",
    "A2_TERM_CONFLICT_MAP__v1.md",
    "A2_TO_A1_DISTILLATION_INPUTS__v1.md",
    "INTENT_SUMMARY.md",
    "MODEL_CONTEXT.md",
    "OPEN_UNRESOLVED__v1.md",
    "SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md",
    "A2_KEY_CONTEXT_APPEND_LOG__v1.md",
    "A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md",
    "CURRENT_EXECUTION_STATE__2026_03_10__v1.md",
    "A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md",
    "A2_CONTROLLER_LAUNCH_PACKET__CURRENT__*.json",
    "A2_CONTROLLER_LAUNCH_GATE_RESULT__CURRENT__*.json",
    "A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__*.json",
    "A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__*.json",
    "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__*.json",
    "A2_CONTROLLER_SEND_TEXT__CURRENT__*.md",
    "A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__*.json",
    "A1_QUEUE_STATUS_PACKET__CURRENT__*.json",
    "A1_QUEUE_STATUS__CURRENT__*.md",
    "memory.jsonl",
    "doc_index.json",
    "constraint_surface.json",
    "rosetta.json",
    "fuel_queue.json",
    "ingest/index_v1.json",
    "ingest/index_v1.sha256",
    "ingest/system_map_v1.md",
    "ingest/doc_cards/*.md",
]


def iter_a2_state_surfaces(a2_state_dir: Path) -> list[Path]:
    files: list[Path] = []
    for glob_pattern in _A2_STATE_SURFACE_GLOBS:
        files.extend(a2_state_dir.glob(glob_pattern))
    files = [p for p in files if p.is_file() and p.name != ".DS_Store"]
    files.sort(key=lambda p: p.as_posix())
    return files
