#!/usr/bin/env python3
"""Build a deterministic curated Ratchet Process v1 bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path, PurePosixPath


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREFIX = PurePosixPath("codex_ratchet_process_v1_20260710")
FIXED_TIME = (2026, 7, 10, 0, 0, 0)

CURATED_PATHS = [
    "system_v7/control/CORATCHET_CORE_EXECUTION_CHARTER_20260710.md",
    "system_v7/control/ratchet_process_v1/00_START_HERE.md",
    "system_v7/control/ratchet_process_v1/README.md",
    "system_v7/control/ratchet_process_v1/RATCHET_SPEC.md",
    "system_v7/control/ratchet_process_v1/ratchet_card.schema.json",
    "system_v7/control/ratchet_process_v1/validate_ratchet_card.py",
    "system_v7/control/ratchet_process_v1/build_bundle.py",
    "system_v7/control/ratchet_process_v1/verify_bundle.py",
    "system_v7/control/ratchet_process_v1/SOURCE_MANIFEST.json",
    "system_v7/control/ratchet_process_v1/CURRENT_EVIDENCE_CEILING.md",
    "system_v7/control/ratchet_process_v1/INDEPENDENT_PROCESS_AUDIT_20260710.md",
    "system_v7/control/ratchet_process_v1/examples/coratchet_recursive_foundations_v1.card.json",
    "system_v7/control/ratchet_process_v1/examples/raw_distinction_fixture_v0.json",
    "system_v7/control/ratchet_process_v1/examples/obligation_generation_rule_v0.json",
    "system_v7/control/ratchet_process_v1/examples/sealed_target_suite_v0.json",
    "system_v7/control/ratchet_process_v1/tests/test_validate_ratchet_card.py",
    "system_v7/control/ratchet_process_v1/validation_result.json",
    "system_v7/constraint_core/external_packet_audits/packet_122_20260710/AUDIT.md",
    "system_v7/constraint_core/external_packet_audits/packet_122_20260710/receipt.json",
    "system_v7/constraint_core/reference_docs_from_josh/foundations/mss_and_rung_climb_foundations_DRAFT_20260615.md",
    "system_v7/constraint_core/reference_docs_from_josh/physics_program/ratchet_runbook_DRAFT_20260615.md",
    "system_v7/constraint_core/reference_docs_from_josh/physics_program/ratchet_definition_and_emergence_spec_DRAFT_20260614.md",
    "system_v7/constraint_core/reference_docs_from_josh/foundations/fresh_llm_simulation_target_spec_20260615.md",
    "system_v7/sims/dual_ratchet_four_count_nonforcing_smt_v0/RESULTS.md",
    "system_v7/sims/dual_ratchet_substage_survivor_discovery_v0/RESULTS.md",
    "system_v7/sims/ratchet_coratchet_loop_v0/CAPSTONE_AUDIT_20260704.md",
    "system_v7/sims/finite_probe_behavioral_object_engine_v1/RESULTS.md",
    "system_v7/sims/unseen_finite_predictive_objects_v1/RESULTS.md",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_value(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def write_member(zf: zipfile.ZipFile, name: PurePosixPath, data: bytes) -> None:
    info = zipfile.ZipInfo(str(name), date_time=FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    zf.writestr(info, data)


def dirty_paths() -> list[str]:
    lines = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPO,
        text=True,
    ).splitlines()
    return sorted(line[3:] for line in lines if len(line) >= 4)


def build(output: Path, allow_dirty_curated: bool = False) -> dict:
    missing = [path for path in CURATED_PATHS if not (REPO / path).is_file()]
    if missing:
        raise FileNotFoundError(f"missing curated files: {missing}")

    members = []
    payloads: list[tuple[str, bytes]] = []
    for relative in CURATED_PATHS:
        data = (REPO / relative).read_bytes()
        payloads.append((relative, data))
        members.append({"path": relative, "sha256": sha256(data), "bytes": len(data)})

    dirty = dirty_paths()
    dirty_curated = sorted(set(dirty) & set(CURATED_PATHS))
    dirty_excluded = sorted(set(dirty) - set(CURATED_PATHS))
    if dirty_curated and not allow_dirty_curated:
        raise RuntimeError(
            "curated worktree files are dirty; commit them or pass "
            f"--allow-dirty-curated to bind the payload by hash: {dirty_curated}"
        )
    manifest = {
        "schema": "codex_ratchet.curated_process_bundle.v1",
        "bundle_name": str(PREFIX),
        "classification": "curated_process_proposal_and_evidence_pack",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source_repo": str(REPO),
        "source_commit_context": git_value("rev-parse", "HEAD"),
        "source_branch": git_value("branch", "--show-current"),
        "payload_source": "working_tree",
        "payload_commit_bound": not dirty_curated,
        "source_tree_dirty": bool(dirty),
        "dirty_curated_files": dirty_curated,
        "included_files": members,
        "excluded_dirty_paths": dirty_excluded,
        "authority_boundary": "The bundle is not a repo and does not admit any claim. Live repo receipts control current state.",
    }
    manifest_data = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as zf:
        write_member(zf, PREFIX / "bundle_manifest.json", manifest_data)
        for relative, data in payloads:
            write_member(zf, PREFIX / PurePosixPath(relative), data)

    return {
        "output": str(output),
        "sha256": sha256(output.read_bytes()),
        "members": len(payloads) + 1,
        "source_commit_context": manifest["source_commit_context"],
        "payload_commit_bound": manifest["payload_commit_bound"],
        "dirty_curated_files": dirty_curated,
        "source_tree_dirty": manifest["source_tree_dirty"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-dirty-curated", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.allow_dirty_curated), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
