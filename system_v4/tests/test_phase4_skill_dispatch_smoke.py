"""
Phase 4 smoke verification for the skill stack.

This is intentionally a standalone smoke artifact:
- verifies explicit runtime override via SkillRegistry.export_for_model(model=...)
- verifies all 4 phase skill selections resolve through adapter-path binding
- verifies adapter_info is written by log_skill_invocation()

Usage:
    cd "/Users/joshuaeisenhart/Desktop/Codex Ratchet"
    python -m system_v4.skills.test_phase4_skill_dispatch_smoke
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.skill_registry import SkillRegistry


PHASES = [
    {
        "phase": "A1_EXTRACTION",
        "trust_zone": "A1_STRIPPED",
        "graph_family": "dependency",
        "skill_type": "extraction",
        "preferred": ["a1-brain"],
    },
    {
        "phase": "B_ENFORCEMENT",
        "trust_zone": "B_ADJUDICATED",
        "graph_family": "runtime",
        "skill_type": "verification",
        "preferred": ["b-kernel"],
    },
    {
        "phase": "SIM_EVIDENCE",
        "trust_zone": "SIM_EVIDENCED",
        "graph_family": "runtime",
        "skill_type": "verification",
        "preferred": ["sim-engine"],
    },
    {
        "phase": "GRAPH_BRIDGE",
        "trust_zone": "GRAVEYARD",
        "graph_family": "runtime",
        "skill_type": "bridge",
        "preferred": ["runtime-graph-bridge"],
    },
]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    reg = SkillRegistry(str(REPO_ROOT))

    rr.SKILL_DISPATCH.clear()
    rr._register_dispatch()

    temp_root = Path(tempfile.mkdtemp(prefix="phase4_smoke_"))
    original_repo = rr.REPO
    rr.REPO = str(temp_root)

    try:
        print("Phase 4 smoke verification")
        print(f"Repo: {REPO_ROOT}")
        print(f"Temp log root: {temp_root}")

        invocation_entries = []

        for phase in PHASES:
            skills = reg.find_relevant(
                trust_zone=phase["trust_zone"],
                graph_family=phase["graph_family"],
                skill_type=phase["skill_type"],
            )
            selected, fallback_used, adapter_info, dispatch_fn, reason = rr.resolve_phase_binding(
                reg,
                skills,
                phase["preferred"],
                runtime_model="gemini",
            )
            _assert(selected == phase["preferred"][0], f"{phase['phase']}: expected {phase['preferred'][0]}, got {selected}")
            _assert(not fallback_used, f"{phase['phase']}: expected dispatch-table binding, got fallback")
            _assert(dispatch_fn is not None, f"{phase['phase']}: adapter path missing from dispatch table")
            _assert(reason == "dispatch-table", f"{phase['phase']}: expected dispatch-table reason, got {reason}")

            # Explicit runtime override: ask for gemini and confirm the model field changes.
            adapter_info = reg.export_for_model(selected, model="gemini")
            _assert(adapter_info is not None, f"{phase['phase']}: export_for_model returned None")
            _assert(adapter_info["model"] == "gemini", f"{phase['phase']}: adapter override did not force gemini")
            _assert(adapter_info["skill_id"] == selected, f"{phase['phase']}: adapter skill_id mismatch")
            _assert(adapter_info["execution_path"] in rr.SKILL_DISPATCH, f"{phase['phase']}: execution_path missing from dispatch table")

            rr.log_skill_invocation(
                batch_id="PHASE4_SMOKE",
                phase=phase["phase"],
                trust_zone=phase["trust_zone"],
                graph_family=phase["graph_family"],
                considered=[s.skill_id for s in skills],
                selected=selected,
                fallback_used=fallback_used,
                reason="dispatch-table",
                adapter_info=adapter_info,
            )

            invocation_entries.append(
                {
                    "phase": phase["phase"],
                    "selected": selected,
                    "adapter_path": adapter_info["adapter_path"],
                    "execution_path": adapter_info["execution_path"],
                    "model": adapter_info["model"],
                }
            )

        log_path = temp_root / "system_v4" / "a1_state" / "skill_invocation_log.jsonl"
        _assert(log_path.exists(), "invocation log was not written")

        lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        _assert(len(lines) == 4, f"expected 4 log entries, got {len(lines)}")

        parsed = [json.loads(line) for line in lines]
        for idx, entry in enumerate(parsed):
            _assert("adapter_path" in entry, f"entry {idx} missing adapter_path")
            _assert("execution_path" in entry, f"entry {idx} missing execution_path")
            _assert("model" in entry, f"entry {idx} missing model")
            _assert("unsupported" in entry, f"entry {idx} missing unsupported")
            _assert(entry["reason"] == "dispatch-table", f"entry {idx} reason mismatch")

        print("PASS: all 4 phases resolved through execution-path dispatch and logged adapter_info")
        for item in invocation_entries:
            print(
                f"  {item['phase']}: {item['selected']} [{item['model']}] "
                f"spec={item['adapter_path']} exec={item['execution_path']}"
            )

    finally:
        rr.REPO = original_repo
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
