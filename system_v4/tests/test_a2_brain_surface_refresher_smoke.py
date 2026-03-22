"""Smoke test for the audit-mode A2 brain surface refresher."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_brain_surface_refresher import (
    build_a2_brain_surface_refresh_report,
    run_a2_brain_surface_refresher,
)
from system_v4.skills.skill_registry import SkillRegistry


PRIMARY_SURFACES = [
    "system_v3/a2_state/INTENT_SUMMARY.md",
    "system_v3/a2_state/A2_BRAIN_SLICE__v1.md",
    "system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md",
    "system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md",
    "system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md",
    "system_v3/a2_state/OPEN_UNRESOLVED__v1.md",
    "system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md",
    "system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md",
    "system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md",
    "system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md",
]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_temp_workspace(root: Path) -> None:
    for rel in PRIMARY_SURFACES:
        if rel.endswith("A2_TERM_CONFLICT_MAP__v1.md"):
            continue
        text = "# seeded surface\nDate: 2026-03-13\n"
        if rel.endswith("A2_KEY_CONTEXT_APPEND_LOG__v1.md"):
            text += "doc_index does not index these key owner specs\n"
        if rel.endswith("A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md"):
            text += "registry fail-closes to `0`\n"
        _write_text(root / rel, text)

    _write_json(
        root / "system_v3/a2_state/doc_index.json",
        {
            "documents": [
                {"path": "system_v3/specs/01_REQUIREMENTS_LEDGER.md"},
                {"path": "system_v3/specs/02_OWNERSHIP_MAP.md"},
                {"path": "system_v3/specs/07_A2_OPERATIONS_SPEC.md"},
                {"path": "system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md"},
                {"path": "SKILL_SOURCE_CORPUS.md"},
                {"path": "REPO_SKILL_INTEGRATION_TRACKER.md"},
                {"path": "SKILL_CANDIDATES_BACKLOG.md"},
                {"path": "LOCAL_SOURCE_REPO_INVENTORY.md"},
            ]
        },
    )
    for rel in (
        "SKILL_SOURCE_CORPUS.md",
        "REPO_SKILL_INTEGRATION_TRACKER.md",
        "SKILL_CANDIDATES_BACKLOG.md",
        "LOCAL_SOURCE_REPO_INVENTORY.md",
        "A2_V4_RECOVERY_AUDIT.md",
        "system_v4/V4_SYSTEM_SPEC__CURRENT.md",
        "system_v3/specs/07_A2_OPERATIONS_SPEC.md",
        "system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md",
        "system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md",
    ):
        _write_text(root / rel, "# support\n")

    registry = json.loads(
        (REPO_ROOT / "system_v4/a1_state/skill_registry_v1.json").read_text(encoding="utf-8")
    )
    _write_json(root / "system_v4/a1_state/skill_registry_v1.json", registry)
    _write_json(
        root / "system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json",
        {
            "schema": "GRAPH_CAPABILITY_AUDIT_v1",
            "skill_graph_coverage": {
                "active_skill_count": 91,
                "graphed_skill_node_count": 91,
                "missing_active_skill_count": 0,
                "stale_skill_node_count": 0,
                "single_edge_skill_node_count": 36,
            },
        },
    )
    for rel in (
        "system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json",
        "system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.json",
        "system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json",
        "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json",
    ):
        _write_json(root / rel, {"status": "ok", "generated_utc": "2026-03-21T00:00:00Z"})


def main() -> None:
    report = build_a2_brain_surface_refresh_report(REPO_ROOT)
    _assert(report["audit_only"] is True, "refresher should stay audit-only")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _seed_temp_workspace(root)
        canonical_paths = [root / rel for rel in PRIMARY_SURFACES if (root / rel).exists()]
        before_hashes = {str(path): _sha256(path) for path in canonical_paths}
        before_inventory = sorted(str(path.relative_to(root)) for path in root.glob("system_v3/a2_state/*"))

        json_path = root / "system_v4/a2_state/audit_logs/brain_refresh.json"
        md_path = root / "system_v4/a2_state/audit_logs/brain_refresh.md"
        packet_path = root / "system_v4/a2_state/audit_logs/brain_refresh.packet.json"
        emitted = run_a2_brain_surface_refresher(
            {
                "repo": str(root),
                "report_path": str(json_path),
                "markdown_path": str(md_path),
                "packet_path": str(packet_path),
                "record_runtime_context": False,
            }
        )

        _assert(json_path.exists(), "brain refresh json was not written")
        _assert(md_path.exists(), "brain refresh markdown was not written")
        _assert(packet_path.exists(), "brain refresh packet was not written")
        _assert(emitted["audit_only"] is True, "emitted report should remain audit-only")
        _assert(emitted["nonoperative"] is True, "emitted report should remain nonoperative")
        _assert(emitted["do_not_promote"] is True, "emitted report should remain non-promotable")
        missing = [
            item["path"]
            for item in emitted["active_owner_surface_status"]
            if not item["exists"]
        ]
        _assert(
            "system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md" in missing,
            "missing canonical surface was not reported",
        )
        finding_ids = {item["id"] for item in emitted["priority_surface_findings"]}
        _assert("owner_law_indexing_stale" in finding_ids, "owner-law stale claim was not caught")
        _assert("registry_zero_stale" in finding_ids, "registry-zero stale claim was not caught")

        after_hashes = {str(path): _sha256(path) for path in canonical_paths}
        after_inventory = sorted(str(path.relative_to(root)) for path in root.glob("system_v3/a2_state/*"))
        _assert(before_hashes == after_hashes, "canonical A2 surfaces were mutated by audit-only refresher")
        _assert(before_inventory == after_inventory, "audit-only refresher changed canonical A2 inventory")

        # A prior refresh report should not count as "latest evidence" against the
        # standing A2 surfaces, or the refresher will create a permanent self-lag.
        base_mtime = 1_700_000_000
        for rel in (
            PRIMARY_SURFACES
            + [
                "SKILL_SOURCE_CORPUS.md",
                "REPO_SKILL_INTEGRATION_TRACKER.md",
                "SKILL_CANDIDATES_BACKLOG.md",
                "LOCAL_SOURCE_REPO_INVENTORY.md",
                "A2_V4_RECOVERY_AUDIT.md",
                "system_v4/V4_SYSTEM_SPEC__CURRENT.md",
                "system_v3/specs/07_A2_OPERATIONS_SPEC.md",
                "system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md",
                "system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md",
                "system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json",
                "system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json",
                "system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.json",
                "system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json",
                "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json",
            ]
        ):
            path = root / rel
            if path.exists():
                os.utime(path, (base_mtime, base_mtime))

        seeded_generated_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(base_mtime))
        for rel in (
            "system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json",
            "system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.json",
            "system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json",
            "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json",
            "system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json",
        ):
            path = root / rel
            if not path.exists():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["generated_utc"] = seeded_generated_utc
            _write_json(path, payload)
            os.utime(path, (base_mtime, base_mtime))

        prior_refresh_report = root / "system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json"
        _write_json(prior_refresh_report, {"status": "ok"})
        os.utime(prior_refresh_report, (base_mtime + 120, base_mtime + 120))
        self_lag_report = build_a2_brain_surface_refresh_report(root)
        older_paths = {
            item["path"]
            for item in self_lag_report["active_owner_surface_status"]
            if item["older_than_latest_evidence"]
        }
        _assert(
            "system_v3/a2_state/A2_BRAIN_SLICE__v1.md" not in older_paths,
            "refresher incorrectly treated its own prior report as latest evidence",
        )

        # A current evidence report with a noisy filesystem mtime but an older
        # embedded generated_utc should not force the standing A2 surfaces stale.
        external_report = root / "system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json"
        _write_json(
            external_report,
            {
                "status": "ok",
                "generated_utc": seeded_generated_utc,
            },
        )
        os.utime(external_report, (base_mtime + 360, base_mtime + 360))
        generated_utc_report = build_a2_brain_surface_refresh_report(root)
        generated_utc_older_paths = {
            item["path"]
            for item in generated_utc_report["active_owner_surface_status"]
            if item["older_than_latest_evidence"]
        }
        _assert(
            "system_v3/a2_state/A2_BRAIN_SLICE__v1.md" not in generated_utc_older_paths,
            "refresher incorrectly used noisy report mtime instead of generated_utc",
        )

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_brain_surface_refresher.py": lambda ctx: "a2-brain-surface-refresher-dispatch",
        }
    )
    refresher_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["brain-refresh"],
    )
    _assert(
        any(skill.skill_id == "a2-brain-surface-refresher" for skill in refresher_skills),
        "a2-brain-surface-refresher was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        refresher_skills,
        ["a2-brain-surface-refresher"],
        runtime_model="shell",
    )
    _assert(selected == "a2-brain-surface-refresher", f"unexpected refresher selection: {selected}")
    _assert(not fallback, "a2-brain-surface-refresher unexpectedly fell back")
    _assert(dispatch is not None, "a2-brain-surface-refresher dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected refresher reason: {reason}")

    print("PASS: a2 brain surface refresher smoke")


if __name__ == "__main__":
    main()
