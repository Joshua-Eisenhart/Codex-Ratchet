"""Candidate-aware smoke for skill-improver dry-runs against readiness operator."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _load_candidate_module(candidate_path: Path):
    spec = importlib.util.spec_from_file_location(
        "candidate_a2_skill_improver_readiness_operator",
        candidate_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load candidate module from {candidate_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    _assert(len(sys.argv) == 2, "expected one candidate path argument")
    candidate_path = Path(sys.argv[1]).resolve()
    _assert(candidate_path.exists(), f"candidate path does not exist: {candidate_path}")

    candidate_module = _load_candidate_module(candidate_path)
    report, packet = candidate_module.build_skill_improver_readiness_report(REPO_ROOT)
    _assert(report["audit_only"] is True, "candidate readiness operator should stay audit-only")
    _assert(report["nonoperative"] is True, "candidate readiness operator should stay nonoperative")
    _assert(report["do_not_promote"] is True, "candidate readiness operator should stay non-promotable")
    _assert(
        report["target_skill_id"] == "skill-improver-operator",
        "candidate readiness operator targeted the wrong skill",
    )
    _assert(
        packet["allow_live_repo_mutation"] is False,
        "candidate readiness packet should not allow live mutation",
    )

    with tempfile.TemporaryDirectory() as td:
        temp_root = Path(td)
        json_path = temp_root / "readiness.json"
        md_path = temp_root / "readiness.md"
        packet_path = temp_root / "readiness.packet.json"
        emitted = candidate_module.run_a2_skill_improver_readiness(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "candidate readiness json was not written")
        _assert(md_path.exists(), "candidate readiness markdown was not written")
        _assert(packet_path.exists(), "candidate readiness packet was not written")
        _assert(
            emitted["status"] == "ok",
            "candidate readiness did not emit an ok summary",
        )
        _assert(
            emitted["target_readiness"] == "bounded_ready_for_first_target",
            "candidate readiness emitted the wrong readiness summary",
        )

    print("PASS: a2 skill improver readiness operator candidate smoke")


if __name__ == "__main__":
    main()
