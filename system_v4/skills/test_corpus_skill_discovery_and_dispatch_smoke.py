"""Smoke test for newly promoted corpus-derived skill discovery and dispatch."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills import run_real_ratchet as rr
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    reg = SkillRegistry(str(REPO_ROOT))

    rr.SKILL_DISPATCH.clear()
    rr._register_dispatch()

    autoresearch_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["autoresearch"],
    )
    _assert(
        any(skill.skill_id == "autoresearch-operator" for skill in autoresearch_skills),
        "autoresearch-operator was not discoverable by runtime query",
    )
    ar_selected, ar_fallback, _, ar_dispatch, ar_reason = rr.resolve_phase_binding(
        reg,
        autoresearch_skills,
        ["autoresearch-operator"],
        runtime_model="shell",
    )
    _assert(ar_selected == "autoresearch-operator", f"unexpected autoresearch selection: {ar_selected}")
    _assert(not ar_fallback, "autoresearch unexpectedly fell back")
    _assert(ar_dispatch is not None, "autoresearch dispatch binding missing")
    _assert(ar_reason == "dispatch-table", f"unexpected autoresearch reason: {ar_reason}")

    council_skills = reg.find_relevant(
        trust_zone="B_ADJUDICATED",
        graph_family="runtime",
        tags_any=["llm-council"],
    )
    _assert(
        any(skill.skill_id == "llm-council-operator" for skill in council_skills),
        "llm-council-operator was not discoverable by runtime query",
    )
    lc_selected, lc_fallback, _, lc_dispatch, lc_reason = rr.resolve_phase_binding(
        reg,
        council_skills,
        ["llm-council-operator"],
        runtime_model="shell",
    )
    _assert(lc_selected == "llm-council-operator", f"unexpected llm-council selection: {lc_selected}")
    _assert(not lc_fallback, "llm-council unexpectedly fell back")
    _assert(lc_dispatch is not None, "llm-council dispatch binding missing")
    _assert(lc_reason == "dispatch-table", f"unexpected llm-council reason: {lc_reason}")

    witness_sync_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="runtime",
        tags_any=["witness-sync"],
    )
    _assert(
        any(skill.skill_id == "witness-evermem-sync" for skill in witness_sync_skills),
        "witness-evermem-sync was not discoverable by runtime query",
    )
    ws_selected, ws_fallback, _, ws_dispatch, ws_reason = rr.resolve_phase_binding(
        reg,
        witness_sync_skills,
        ["witness-evermem-sync"],
        runtime_model="shell",
    )
    _assert(ws_selected == "witness-evermem-sync", f"unexpected witness sync selection: {ws_selected}")
    _assert(not ws_fallback, "witness-evermem-sync unexpectedly fell back")
    _assert(ws_dispatch is not None, "witness-evermem-sync dispatch binding missing")
    _assert(ws_reason == "dispatch-table", f"unexpected witness-evermem-sync reason: {ws_reason}")

    witness_retriever_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="runtime",
        tags_any=["witness-memory-retrieval"],
    )
    _assert(
        any(skill.skill_id == "witness-memory-retriever" for skill in witness_retriever_skills),
        "witness-memory-retriever was not discoverable by runtime query",
    )
    wr_selected, wr_fallback, _, wr_dispatch, wr_reason = rr.resolve_phase_binding(
        reg,
        witness_retriever_skills,
        ["witness-memory-retriever"],
        runtime_model="shell",
    )
    _assert(wr_selected == "witness-memory-retriever", f"unexpected witness retriever selection: {wr_selected}")
    _assert(not wr_fallback, "witness-memory-retriever unexpectedly fell back")
    _assert(wr_dispatch is not None, "witness-memory-retriever dispatch binding missing")
    _assert(wr_reason == "dispatch-table", f"unexpected witness-memory-retriever reason: {wr_reason}")

    evermem_reachability_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="runtime",
        tags_any=["backend-reachability"],
    )
    _assert(
        any(
            skill.skill_id == "a2-evermem-backend-reachability-audit-operator"
            for skill in evermem_reachability_skills
        ),
        "a2-evermem-backend-reachability-audit-operator was not discoverable by runtime query",
    )
    er_selected, er_fallback, _, er_dispatch, er_reason = rr.resolve_phase_binding(
        reg,
        evermem_reachability_skills,
        ["a2-evermem-backend-reachability-audit-operator"],
        runtime_model="shell",
    )
    _assert(
        er_selected == "a2-evermem-backend-reachability-audit-operator",
        f"unexpected EverMem reachability selection: {er_selected}",
    )
    _assert(not er_fallback, "a2-evermem-backend-reachability-audit-operator unexpectedly fell back")
    _assert(er_dispatch is not None, "a2-evermem-backend-reachability-audit-operator dispatch missing")
    _assert(er_reason == "dispatch-table", f"unexpected EverMem reachability reason: {er_reason}")

    refresher_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["brain-refresh"],
    )
    _assert(
        any(skill.skill_id == "a2-brain-surface-refresher" for skill in refresher_skills),
        "a2-brain-surface-refresher was not discoverable by runtime query",
    )
    rf_selected, rf_fallback, _, rf_dispatch, rf_reason = rr.resolve_phase_binding(
        reg,
        refresher_skills,
        ["a2-brain-surface-refresher"],
        runtime_model="shell",
    )
    _assert(rf_selected == "a2-brain-surface-refresher", f"unexpected refresher selection: {rf_selected}")
    _assert(not rf_fallback, "a2-brain-surface-refresher unexpectedly fell back")
    _assert(rf_dispatch is not None, "a2-brain-surface-refresher dispatch binding missing")
    _assert(rf_reason == "dispatch-table", f"unexpected refresher reason: {rf_reason}")

    workshop_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["workshop-analysis-gating"],
    )
    _assert(
        any(skill.skill_id == "a2-workshop-analysis-gate-operator" for skill in workshop_skills),
        "a2-workshop-analysis-gate-operator was not discoverable by runtime query",
    )
    wk_selected, wk_fallback, _, wk_dispatch, wk_reason = rr.resolve_phase_binding(
        reg,
        workshop_skills,
        ["a2-workshop-analysis-gate-operator"],
        runtime_model="shell",
    )
    _assert(
        wk_selected == "a2-workshop-analysis-gate-operator",
        f"unexpected workshop gate selection: {wk_selected}",
    )
    _assert(not wk_fallback, "a2-workshop-analysis-gate-operator unexpectedly fell back")
    _assert(wk_dispatch is not None, "a2-workshop-analysis-gate-operator dispatch binding missing")
    _assert(wk_reason == "dispatch-table", f"unexpected workshop gate reason: {wk_reason}")

    ledger_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="runtime",
        tags_any=["session-ledger"],
    )
    _assert(
        any(skill.skill_id == "outer-session-ledger" for skill in ledger_skills),
        "outer-session-ledger was not discoverable by runtime query",
    )
    ledger_selected, ledger_fallback, _, ledger_dispatch, ledger_reason = rr.resolve_phase_binding(
        reg,
        ledger_skills,
        ["outer-session-ledger"],
        runtime_model="shell",
    )
    _assert(
        ledger_selected == "outer-session-ledger",
        f"unexpected outer session ledger selection: {ledger_selected}",
    )
    _assert(not ledger_fallback, "outer-session-ledger unexpectedly fell back")
    _assert(ledger_dispatch is not None, "outer-session-ledger dispatch binding missing")
    _assert(ledger_reason == "dispatch-table", f"unexpected outer-session-ledger reason: {ledger_reason}")

    outside_shell_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="runtime",
        tags_any=["outside-control-shell"],
    )
    _assert(
        any(skill.skill_id == "outside-control-shell-operator" for skill in outside_shell_skills),
        "outside-control-shell-operator was not discoverable by runtime query",
    )
    shell_selected, shell_fallback, _, shell_dispatch, shell_reason = rr.resolve_phase_binding(
        reg,
        outside_shell_skills,
        ["outside-control-shell-operator"],
        runtime_model="shell",
    )
    _assert(
        shell_selected == "outside-control-shell-operator",
        f"unexpected outside control shell selection: {shell_selected}",
    )
    _assert(not shell_fallback, "outside-control-shell-operator unexpectedly fell back")
    _assert(shell_dispatch is not None, "outside-control-shell-operator dispatch binding missing")
    _assert(shell_reason == "dispatch-table", f"unexpected outside control shell reason: {shell_reason}")

    readiness_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["skill-improver-readiness"],
    )
    _assert(
        any(skill.skill_id == "a2-skill-improver-readiness-operator" for skill in readiness_skills),
        "a2-skill-improver-readiness-operator was not discoverable by runtime query",
    )
    readiness_selected, readiness_fallback, _, readiness_dispatch, readiness_reason = (
        rr.resolve_phase_binding(
            reg,
            readiness_skills,
            ["a2-skill-improver-readiness-operator"],
            runtime_model="shell",
        )
    )
    _assert(
        readiness_selected == "a2-skill-improver-readiness-operator",
        f"unexpected skill improver readiness selection: {readiness_selected}",
    )
    _assert(
        not readiness_fallback,
        "a2-skill-improver-readiness-operator unexpectedly fell back",
    )
    _assert(
        readiness_dispatch is not None,
        "a2-skill-improver-readiness-operator dispatch binding missing",
    )
    _assert(
        readiness_reason == "dispatch-table",
        f"unexpected skill improver readiness reason: {readiness_reason}",
    )

    selector_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["skill-improver-target-selection"],
    )
    _assert(
        any(skill.skill_id == "a2-skill-improver-target-selector-operator" for skill in selector_skills),
        "a2-skill-improver-target-selector-operator was not discoverable by runtime query",
    )
    selector_selected, selector_fallback, _, selector_dispatch, selector_reason = (
        rr.resolve_phase_binding(
            reg,
            selector_skills,
            ["a2-skill-improver-target-selector-operator"],
            runtime_model="shell",
        )
    )
    _assert(
        selector_selected == "a2-skill-improver-target-selector-operator",
        f"unexpected target selector selection: {selector_selected}",
    )
    _assert(
        not selector_fallback,
        "a2-skill-improver-target-selector-operator unexpectedly fell back",
    )
    _assert(
        selector_dispatch is not None,
        "a2-skill-improver-target-selector-operator dispatch binding missing",
    )
    _assert(
        selector_reason == "dispatch-table",
        f"unexpected target selector reason: {selector_reason}",
    )

    dry_run_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="runtime",
        tags_any=["skill-improver-dry-run"],
    )
    _assert(
        any(skill.skill_id == "a2-skill-improver-dry-run-operator" for skill in dry_run_skills),
        "a2-skill-improver-dry-run-operator was not discoverable by runtime query",
    )
    dry_run_selected, dry_run_fallback, _, dry_run_dispatch, dry_run_reason = rr.resolve_phase_binding(
        reg,
        dry_run_skills,
        ["a2-skill-improver-dry-run-operator"],
        runtime_model="shell",
    )
    _assert(
        dry_run_selected == "a2-skill-improver-dry-run-operator",
        f"unexpected dry-run selection: {dry_run_selected}",
    )
    _assert(not dry_run_fallback, "a2-skill-improver-dry-run-operator unexpectedly fell back")
    _assert(
        dry_run_dispatch is not None,
        "a2-skill-improver-dry-run-operator dispatch binding missing",
    )
    _assert(
        dry_run_reason == "dispatch-table",
        f"unexpected dry-run reason: {dry_run_reason}",
    )

    future_lane_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["future-lane-existence"],
    )
    _assert(
        any(
            skill.skill_id == "a2-lev-builder-post-skeleton-future-lane-existence-audit-operator"
            for skill in future_lane_skills
        ),
        "a2-lev-builder-post-skeleton-future-lane-existence-audit-operator was not discoverable by runtime query",
    )
    future_lane_selected, future_lane_fallback, _, future_lane_dispatch, future_lane_reason = (
        rr.resolve_phase_binding(
            reg,
            future_lane_skills,
            ["a2-lev-builder-post-skeleton-future-lane-existence-audit-operator"],
            runtime_model="shell",
        )
    )
    _assert(
        future_lane_selected == "a2-lev-builder-post-skeleton-future-lane-existence-audit-operator",
        f"unexpected future-lane audit selection: {future_lane_selected}",
    )
    _assert(
        not future_lane_fallback,
        "a2-lev-builder-post-skeleton-future-lane-existence-audit-operator unexpectedly fell back",
    )
    _assert(
        future_lane_dispatch is not None,
        "a2-lev-builder-post-skeleton-future-lane-existence-audit-operator dispatch binding missing",
    )
    _assert(
        future_lane_reason == "dispatch-table",
        f"unexpected future-lane audit reason: {future_lane_reason}",
    )

    print("PASS: corpus-derived skill discovery and dispatch smoke")


if __name__ == "__main__":
    main()
