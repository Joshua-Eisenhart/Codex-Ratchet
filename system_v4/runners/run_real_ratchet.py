"""
run_real_ratchet.py — Procedure-Driven Queue-Fed Ratchet Pipeline

This runs the current v4 ratchet loop, but only when repo-held controller and
A1 queue artifacts explicitly authorize the run. It is not supposed to be an
ad hoc "just run A1 -> B -> SIM" entrypoint.

What it does:
1. Verifies the current controller launch surfaces are coherent and ready
2. Verifies the current A1 queue packet is in an explicit READY_* state
3. Loads bounded graph fuel only from the current A1 ready packet
4. A1 brain extracts candidates via the selected skill path
5. B kernel enforces 7-stage deterministic pipeline
6. SIM engine runs T0_ATOM campaign on survivors
7. State is persisted and bridged back into the graph

What to expect: if the procedure surfaces are missing or say `NO_WORK`, this
runner now fails closed instead of improvising.
"""
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Optional

CODE_ROOT = str(Path(__file__).resolve().parents[2])
REPO = os.environ.get("RATCHET_REPO_ROOT", CODE_ROOT)
sys.path.insert(0, CODE_ROOT)
if REPO != CODE_ROOT:
    sys.path.insert(0, REPO)

from system_v4.skills.a1_brain import (
    A1Brain, L0_LEXEME_SET, DERIVED_ONLY_TERMS
)
from system_v4.skills.b_kernel import BKernel
from system_v4.skills.sim_engine import SimEngine
from system_v4.skills.skill_registry import SkillRegistry

# ── Live kernel skill imports ─────────────────────────────────────────────
from system_v4.skills.runtime_state_kernel import (
    RuntimeState, BoundaryTag, WitnessKind, FnTransform,
    make_step_event, utc_iso,
)
from system_v4.skills.witness_recorder import WitnessRecorder
from system_v4.skills.z3_constraint_checker import (
    check_constraints, standard_constraints, constraints_to_witness,
    z3_check_phase_boundaries,
)
from system_v4.skills.bounded_improve_operator import bounded_improve
from system_v4.skills.intent_runtime_policy import normalize_intent_runtime_policy


# ── Skill Resolver & Dispatch ─────────────────────────────────────────────

# Dispatch table: maps resolved adapter_path → callable(ctx) → result.
# Each callable receives a context dict with the live objects.
# Runtime behavior should branch on canonical skill -> model adapter ->
# execution binding, not on skill_id alone.
SKILL_DISPATCH: dict[str, Any] = {}
READY_A1_QUEUE_STATUSES = {
    "READY_FROM_NEW_A2_HANDOFF",
    "READY_FROM_EXISTING_FUEL",
    "READY_FROM_A2_PREBUILT_BATCH",
}
ALLOWED_A1_QUEUE_STATUSES = READY_A1_QUEUE_STATUSES | {
    "NO_WORK",
    "BLOCKED_MISSING_BOOT",
    "BLOCKED_MISSING_ARTIFACTS",
}


def _register_dispatch() -> None:
    """Populate the live adapter-path dispatch table.

    Kept idempotent so runtime code and maintenance tests can bootstrap the
    same authoritative dispatch bindings without reimplementing them.
    """
    SKILL_DISPATCH.clear()

    def wrap_cartridge(ctx):
        return ctx["brain"].build_strategy_packet(
            ctx["candidate_ids"], ctx["graph_nodes"],
            strategy_id=f"A1_STRAT_LIVE_{int(time.time())}",
            lane_id=ctx.get("lane_id"),
            bias_config=ctx.get("bias_config"),
            intent_control=ctx.get("intent_control"),
        )

    for path in [
        "system_v4/skills/a1_brain.py",
        "system_v4/skills/a1_cartridge_assembler.py",
        "system_v4/skill_specs/a1-cartridge-assembler/SKILL.md",
    ]:
        SKILL_DISPATCH[path] = wrap_cartridge

    SKILL_DISPATCH["system_v4/skills/b_kernel.py"] = lambda ctx: ctx["kernel"].adjudicate_batch(
        ctx["targets"], ctx["alternatives"],
    )
    SKILL_DISPATCH["system_v4/skills/a2_high_intake_graph_builder.py"] = lambda ctx: (
        __import__("system_v4.skills.a2_high_intake_graph_builder", fromlist=["write_a2_high_intake_graph"])
        .write_a2_high_intake_graph(ctx.get("repo", REPO))
    )
    SKILL_DISPATCH["system_v4/skills/a2_mid_refinement_graph_builder.py"] = lambda ctx: (
        __import__("system_v4.skills.a2_mid_refinement_graph_builder", fromlist=["write_a2_mid_refinement_graph"])
        .write_a2_mid_refinement_graph(ctx.get("repo", REPO))
    )
    SKILL_DISPATCH["system_v4/skills/a2_low_control_graph_builder.py"] = lambda ctx: (
        __import__("system_v4.skills.a2_low_control_graph_builder", fromlist=["write_a2_low_control_graph"])
        .write_a2_low_control_graph(ctx.get("repo", REPO))
    )
    SKILL_DISPATCH["system_v4/skills/a1_jargoned_graph_builder.py"] = lambda ctx: (
        __import__("system_v4.skills.a1_jargoned_graph_builder", fromlist=["write_a1_jargoned_graph"])
        .write_a1_jargoned_graph(ctx.get("repo", REPO))
    )
    SKILL_DISPATCH["system_v4/skills/a1_stripped_graph_builder.py"] = lambda ctx: (
        __import__("system_v4.skills.a1_stripped_graph_builder", fromlist=["write_a1_stripped_graph"])
        .write_a1_stripped_graph(ctx.get("repo", REPO))
    )
    SKILL_DISPATCH["system_v4/skills/a1_cartridge_graph_builder.py"] = lambda ctx: (
        __import__("system_v4.skills.a1_cartridge_graph_builder", fromlist=["write_a1_cartridge_graph"])
        .write_a1_cartridge_graph(ctx.get("repo", REPO))
    )
    SKILL_DISPATCH["system_v4/skills/intent_refinement_graph_builder.py"] = lambda ctx: (
        __import__("system_v4.skills.intent_refinement_graph_builder", fromlist=["build_intent_refinement_graph"])
        .build_intent_refinement_graph(ctx.get("repo", REPO))
    )
    SKILL_DISPATCH["system_v4/skills/intent_control_surface_builder.py"] = lambda ctx: (
        __import__("system_v4.skills.intent_control_surface_builder", fromlist=["build_intent_control_surface"])
        .build_intent_control_surface(ctx.get("repo", REPO))
    )
    SKILL_DISPATCH["system_v4/skills/sim_engine.py"] = lambda ctx: ctx["sim"].run_t0_with_differential(
        ctx["sid"], ctx["survivor"], ctx["graveyard_items"],
    )
    SKILL_DISPATCH["system_v4/skills/runtime_graph_bridge.py"] = lambda ctx: (
        __import__("system_v4.skills.runtime_graph_bridge", fromlist=["bridge_runtime_to_graph"])
        .bridge_runtime_to_graph(REPO, clean=True)
    )
    SKILL_DISPATCH["system_v4/skills/ratchet_overseer.py"] = lambda ctx: (
        __import__("system_v4.skills.ratchet_overseer", fromlist=["build_convergence_report"])
        .build_convergence_report(**ctx)
    )
    SKILL_DISPATCH["system_v4/skills/graveyard_lawyer.py"] = lambda ctx: (
        __import__("system_v4.skills.graveyard_lawyer", fromlist=["build_rescue_report"])
        .build_rescue_report(**ctx)
    )
    SKILL_DISPATCH["system_v4/skills/wiggle_lane_runner.py"] = lambda ctx: (
        __import__("system_v4.skills.wiggle_lane_runner", fromlist=["build_wiggle_envelope"])
        .build_wiggle_envelope(**ctx)
    )

    SKILL_DISPATCH["system_v4/skills/z3_constraint_checker.py"] = lambda ctx: (
        check_constraints(ctx["state"], ctx.get("constraints", standard_constraints()))
    )
    SKILL_DISPATCH["system_v4/skills/witness_recorder.py"] = lambda ctx: (
        ctx["recorder"].record(ctx["witness"], tags=ctx.get("tags"))
    )
    SKILL_DISPATCH["system_v4/skills/bounded_improve_operator.py"] = lambda ctx: (
        bounded_improve(
            ctx["state"], ctx["mutate"], ctx["eval_fn"],
            rounds=ctx.get("rounds", 5),
        )
    )
    SKILL_DISPATCH["system_v4/skills/autoresearch_operator.py"] = lambda ctx: (
        __import__("system_v4.skills.autoresearch_operator", fromlist=["run_autoresearch"])
        .run_autoresearch(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/llm_council_operator.py"] = lambda ctx: (
        __import__("system_v4.skills.llm_council_operator", fromlist=["run_llm_council"])
        .run_llm_council(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/skill_improver_operator.py"] = lambda ctx: (
        __import__("system_v4.skills.skill_improver_operator", fromlist=["run_skill_improver"])
        .run_skill_improver(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/evermem_adapter.py"] = lambda ctx: (
        __import__("system_v4.skills.evermem_adapter", fromlist=["run_evermem_store"])
        .run_evermem_store(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/witness_evermem_sync.py"] = lambda ctx: (
        __import__("system_v4.skills.witness_evermem_sync", fromlist=["run_witness_sync"])
        .run_witness_sync(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/witness_memory_retriever.py"] = lambda ctx: (
        __import__("system_v4.skills.witness_memory_retriever", fromlist=["run_witness_memory_retriever"])
        .run_witness_memory_retriever(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_evermem_backend_reachability_audit_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_evermem_backend_reachability_audit_operator",
            fromlist=["run_a2_evermem_backend_reachability_audit_operator"],
        ).run_a2_evermem_backend_reachability_audit_operator(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/pimono_evermem_adapter.py"] = lambda ctx: (
        __import__("system_v4.skills.pimono_evermem_adapter", fromlist=["run_pimono_evermem_adapter"])
        .run_pimono_evermem_adapter(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_skill_source_intake_operator.py"] = lambda ctx: (
        __import__("system_v4.skills.a2_skill_source_intake_operator", fromlist=["run_a2_skill_source_intake"])
        .run_a2_skill_source_intake(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_tracked_work_operator.py"] = lambda ctx: (
        __import__("system_v4.skills.a2_tracked_work_operator", fromlist=["run_a2_tracked_work"])
        .run_a2_tracked_work(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_research_deliberation_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_research_deliberation_operator",
            fromlist=["run_a2_research_deliberation"],
        ).run_a2_research_deliberation(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_brain_surface_refresher.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_brain_surface_refresher",
            fromlist=["run_a2_brain_surface_refresher"],
        ).run_a2_brain_surface_refresher(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_workshop_analysis_gate_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_workshop_analysis_gate_operator",
            fromlist=["run_a2_workshop_analysis_gate"],
        ).run_a2_workshop_analysis_gate(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/outer_session_ledger.py"] = lambda ctx: (
        __import__("system_v4.skills.outer_session_ledger", fromlist=["run_outer_session_ledger"])
        .run_outer_session_ledger(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/outside_control_shell_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.outside_control_shell_operator",
            fromlist=["run_outside_control_shell_operator"],
        ).run_outside_control_shell_operator(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_skill_improver_readiness_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_skill_improver_readiness_operator",
            fromlist=["run_a2_skill_improver_readiness"],
        ).run_a2_skill_improver_readiness(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_skill_improver_dry_run_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_skill_improver_dry_run_operator",
            fromlist=["run_a2_skill_improver_dry_run"],
        ).run_a2_skill_improver_dry_run(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_skill_improver_target_selector_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_skill_improver_target_selector_operator",
            fromlist=["run_a2_skill_improver_target_selector"],
        ).run_a2_skill_improver_target_selector(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_skill_improver_first_target_proof_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_skill_improver_first_target_proof_operator",
            fromlist=["run_a2_skill_improver_first_target_proof"],
        ).run_a2_skill_improver_first_target_proof(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_skill_improver_second_target_admission_audit_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_skill_improver_second_target_admission_audit_operator",
            fromlist=["run_a2_skill_improver_second_target_admission_audit"],
        ).run_a2_skill_improver_second_target_admission_audit(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_lev_agents_promotion_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_lev_agents_promotion_operator",
            fromlist=["run_a2_lev_agents_promotion"],
        ).run_a2_lev_agents_promotion(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_lev_autodev_loop_audit_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_lev_autodev_loop_audit_operator",
            fromlist=["run_a2_lev_autodev_loop_audit"],
        ).run_a2_lev_autodev_loop_audit(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_lev_architecture_fitness_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_lev_architecture_fitness_operator",
            fromlist=["run_a2_lev_architecture_fitness"],
        ).run_a2_lev_architecture_fitness(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_lev_builder_placement_audit_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_lev_builder_placement_audit_operator",
            fromlist=["run_a2_lev_builder_placement_audit"],
        ).run_a2_lev_builder_placement_audit(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_lev_builder_formalization_proposal_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_lev_builder_formalization_proposal_operator",
            fromlist=["run_a2_lev_builder_formalization_proposal"],
        ).run_a2_lev_builder_formalization_proposal(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_lev_builder_formalization_skeleton_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_lev_builder_formalization_skeleton_operator",
            fromlist=["run_a2_lev_builder_formalization_skeleton"],
        ).run_a2_lev_builder_formalization_skeleton(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_lev_builder_post_skeleton_readiness_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_lev_builder_post_skeleton_readiness_operator",
            fromlist=["run_a2_lev_builder_post_skeleton_readiness"],
        ).run_a2_lev_builder_post_skeleton_readiness(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_lev_builder_post_skeleton_follow_on_selector_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_lev_builder_post_skeleton_follow_on_selector_operator",
            fromlist=["run_a2_lev_builder_post_skeleton_follow_on_selector"],
        ).run_a2_lev_builder_post_skeleton_follow_on_selector(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_lev_builder_post_skeleton_disposition_audit_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_lev_builder_post_skeleton_disposition_audit_operator",
            fromlist=["run_a2_lev_builder_post_skeleton_disposition_audit"],
        ).run_a2_lev_builder_post_skeleton_disposition_audit(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_lev_builder_post_skeleton_future_lane_existence_audit_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_lev_builder_post_skeleton_future_lane_existence_audit_operator",
            fromlist=["run_a2_lev_builder_post_skeleton_future_lane_existence_audit"],
        ).run_a2_lev_builder_post_skeleton_future_lane_existence_audit(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_next_state_signal_adaptation_audit_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_next_state_signal_adaptation_audit_operator",
            fromlist=["run_a2_next_state_signal_adaptation_audit"],
        ).run_a2_next_state_signal_adaptation_audit(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_next_state_directive_signal_probe_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_next_state_directive_signal_probe_operator",
            fromlist=["run_a2_next_state_directive_signal_probe"],
        ).run_a2_next_state_directive_signal_probe(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_next_state_improver_context_bridge_audit_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_next_state_improver_context_bridge_audit_operator",
            fromlist=["run_a2_next_state_improver_context_bridge_audit"],
        ).run_a2_next_state_improver_context_bridge_audit(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_next_state_first_target_context_consumer_admission_audit_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_next_state_first_target_context_consumer_admission_audit_operator",
            fromlist=["run_a2_next_state_first_target_context_consumer_admission_audit"],
        ).run_a2_next_state_first_target_context_consumer_admission_audit(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_next_state_first_target_context_consumer_proof_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_next_state_first_target_context_consumer_proof_operator",
            fromlist=["run_a2_next_state_first_target_context_consumer_proof"],
        ).run_a2_next_state_first_target_context_consumer_proof(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_source_family_lane_selector_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_source_family_lane_selector_operator",
            fromlist=["run_a2_source_family_lane_selection"],
        ).run_a2_source_family_lane_selection(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_autoresearch_council_runtime_proof_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_autoresearch_council_runtime_proof_operator",
            fromlist=["run_a2_autoresearch_council_runtime_proof"],
        ).run_a2_autoresearch_council_runtime_proof(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_context_spec_workflow_pattern_audit_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_context_spec_workflow_pattern_audit_operator",
            fromlist=["run_a2_context_spec_workflow_pattern_audit"],
        ).run_a2_context_spec_workflow_pattern_audit(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_context_spec_workflow_follow_on_selector_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_context_spec_workflow_follow_on_selector_operator",
            fromlist=["run_a2_context_spec_workflow_follow_on_selector"],
        ).run_a2_context_spec_workflow_follow_on_selector(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_append_safe_context_shell_audit_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_append_safe_context_shell_audit_operator",
            fromlist=["run_a2_append_safe_context_shell_audit"],
        ).run_a2_append_safe_context_shell_audit(ctx)
    )
    SKILL_DISPATCH["system_v4/skills/a2_context_spec_workflow_post_shell_selector_operator.py"] = lambda ctx: (
        __import__(
            "system_v4.skills.a2_context_spec_workflow_post_shell_selector_operator",
            fromlist=["run_a2_context_spec_workflow_post_shell_selector"],
        ).run_a2_context_spec_workflow_post_shell_selector(ctx)
    )


def resolve_skill(
    candidates: list,
    preferred: list[str],
) -> tuple[Optional[str], bool]:
    """Pick a skill from candidates, preferring the given list.
    Returns (skill_id, fallback_used). fallback_used=True only when no skill
    was selected; adapter-path binding is computed later."""
    candidate_ids = [c.skill_id for c in candidates]
    selected = None
    for pref in preferred:
        if pref in candidate_ids:
            selected = pref
            break
    if selected is None and candidate_ids:
        selected = candidate_ids[0]
    fallback = selected is None
    return selected, fallback


def get_runtime_model(reg: SkillRegistry) -> str:
    """Resolve runtime model explicitly from CLI/env, then fallback to registry detection."""
    args = sys.argv[1:]
    for idx, arg in enumerate(args):
        if arg.startswith("--runtime-model="):
            return arg.split("=", 1)[1].strip()
        if arg == "--runtime-model" and idx + 1 < len(args):
            return args[idx + 1].strip()
    return reg.detect_runtime()


def _latest_current_json(state_dir: Path, pattern: str) -> Optional[Path]:
    matches = sorted(state_dir.glob(pattern))
    return matches[-1] if matches else None


def _resolve_repo_path(repo_root: str, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (Path(repo_root) / path)


def _load_owner_graph_preflight_report(
    repo_root: str,
    result: Any,
    *,
    expected_schema: str,
    label: str,
) -> tuple[dict[str, Any], Path, Path]:
    if not isinstance(result, dict):
        raise ValueError(f"{label} returned non-dict result")

    raw_json_path = str(result.get("json_path", "")).strip()
    raw_audit_note_path = str(result.get("audit_note_path", "")).strip()
    if not raw_json_path or not raw_audit_note_path:
        raise ValueError(
            f"{label} missing json_path/audit_note_path contract: {sorted(result.keys())}"
        )

    json_path = _resolve_repo_path(repo_root, raw_json_path)
    audit_note_path = _resolve_repo_path(repo_root, raw_audit_note_path)
    if not json_path.exists():
        raise ValueError(f"{label} json_path missing on disk: {json_path}")
    if not audit_note_path.exists():
        raise ValueError(f"{label} audit_note_path missing on disk: {audit_note_path}")

    report = json.loads(json_path.read_text(encoding="utf-8"))
    if report.get("schema") != expected_schema:
        raise ValueError(
            f"{label} schema mismatch: {report.get('schema', '<missing>')} != {expected_schema}"
        )

    build_status = report.get("build_status")
    materialized = report.get("materialized")
    summary = report.get("summary")
    blockers = report.get("blockers")
    if build_status not in {"MATERIALIZED", "FAIL_CLOSED"}:
        raise ValueError(f"{label} invalid build_status: {build_status!r}")
    if not isinstance(materialized, bool):
        raise ValueError(f"{label} materialized must be bool")
    if build_status == "MATERIALIZED" and not materialized:
        raise ValueError(f"{label} reported MATERIALIZED with materialized=false")
    if build_status == "FAIL_CLOSED" and materialized:
        raise ValueError(f"{label} reported FAIL_CLOSED with materialized=true")
    if not isinstance(summary, dict):
        raise ValueError(f"{label} summary missing or not dict")
    if not isinstance(blockers, list):
        raise ValueError(f"{label} blockers missing or not list")

    return report, json_path, audit_note_path


def _load_intent_control_surface_report(
    repo_root: str,
    result: Any,
) -> tuple[dict[str, Any], Path, Path]:
    if not isinstance(result, dict):
        raise ValueError("intent control builder returned non-dict result")

    raw_json_path = str(result.get("json_path", "")).strip()
    raw_audit_note_path = str(result.get("audit_note_path", "")).strip()
    if not raw_json_path or not raw_audit_note_path:
        raise ValueError("intent control builder missing json_path/audit_note_path")

    json_path = _resolve_repo_path(repo_root, raw_json_path)
    audit_note_path = _resolve_repo_path(repo_root, raw_audit_note_path)
    if not json_path.exists():
        raise ValueError(f"intent control surface missing on disk: {json_path}")
    if not audit_note_path.exists():
        raise ValueError(f"intent control audit note missing on disk: {audit_note_path}")

    report = json.loads(json_path.read_text(encoding="utf-8"))
    if report.get("schema") != "A2_INTENT_CONTROL_SURFACE_v1":
        raise ValueError(
            f"intent control surface schema mismatch: {report.get('schema', '<missing>')}"
        )
    if not isinstance(report.get("classification"), dict):
        raise ValueError("intent control surface missing classification")
    if not isinstance(report.get("control"), dict):
        raise ValueError("intent control surface missing control block")
    if not isinstance(report.get("self_audit"), dict):
        raise ValueError("intent control surface missing self_audit block")
    return report, json_path, audit_note_path


def _validate_intent_control_surface(report: dict[str, Any]) -> list[str]:
    audit = report.get("self_audit", {}) or {}
    failures: list[str] = []
    if int(audit.get("maker_intent_count", 0)) < 1:
        failures.append("missing preserved maker intent")
    if int(audit.get("runtime_context_count", 0)) < 1:
        failures.append("missing runtime context")
    if int(audit.get("refined_intent_count", 0)) < 1:
        failures.append("missing graph-backed refined intent")
    if int(audit.get("focus_term_count", 0)) < 1:
        failures.append("missing focus terms")
    return failures


def _score_candidate_focus(node: dict[str, Any], focus_terms: list[str]) -> int:
    haystacks = [
        str(node.get("name", "")),
        str(node.get("description", "")),
        " ".join(str(tag) for tag in (node.get("tags", []) or [])),
    ]
    corpus = " ".join(h.lower() for h in haystacks)
    score = 0
    for term in focus_terms:
        if term and term.lower() in corpus:
            score += 1
    return score


def _apply_intent_concept_selection(
    eligible_reopened: list[str],
    eligible_fresh: list[str],
    graph_nodes: dict[str, dict[str, Any]],
    intent_control: dict[str, Any] | None,
    *,
    explicit_targets_used: bool,
    batch_limit: int = 10,
) -> tuple[list[str], dict[str, Any]]:
    runtime_policy = normalize_intent_runtime_policy(intent_control)
    selection = (runtime_policy.get("concept_selection", {}) or {})
    focus_terms = list(selection.get("focus_terms") or runtime_policy.get("focus_terms") or [])
    gating_focus_terms = list(
        selection.get("gating_focus_terms")
        or runtime_policy.get("steering_focus_terms")
        or focus_terms
    )
    configured_mode = str(selection.get("mode", "disabled"))
    fallback_mode = str(selection.get("fallback_mode", "reorder_only"))
    min_focus_score = int(selection.get("min_focus_score", 1) or 1)
    gate_min_concepts = int(selection.get("gate_min_concepts", 1) or 1)
    respect_explicit_targets = bool(selection.get("respect_explicit_targets", True))

    report = {
        "configured_mode": configured_mode,
        "effective_mode": "disabled",
        "focus_terms": focus_terms,
        "gating_focus_terms": gating_focus_terms,
        "ranking_focus_terms": gating_focus_terms or focus_terms,
        "steering_quality_status": ((runtime_policy.get("steering_quality", {}) or {}).get("status", "")),
        "min_focus_score": min_focus_score,
        "gate_min_concepts": gate_min_concepts,
        "respect_explicit_targets": respect_explicit_targets,
        "explicit_targets_used": explicit_targets_used,
        "eligible_reopened_count": len(eligible_reopened),
        "eligible_fresh_count": len(eligible_fresh),
        "focused_reopened_count": 0,
        "focused_fresh_count": 0,
        "selected_count": 0,
        "suppressed_count": 0,
        "gate_applied": False,
    }

    ranking_focus_terms = gating_focus_terms or focus_terms

    def _sort_ids(ids: list[str]) -> list[str]:
        return sorted(
            ids,
            key=lambda nid: (-_score_candidate_focus(graph_nodes.get(nid, {}), ranking_focus_terms), nid),
        )

    if not focus_terms:
        reopened_candidate_ids = eligible_reopened[:batch_limit]
        fresh_budget = max(0, batch_limit - len(reopened_candidate_ids))
        fresh_candidate_ids = eligible_fresh[:fresh_budget]
        selected = (reopened_candidate_ids + fresh_candidate_ids)[:batch_limit]
        report["effective_mode"] = "disabled"
        report["selected_count"] = len(selected)
        return selected, report

    if explicit_targets_used and respect_explicit_targets:
        selected = []
        report["effective_mode"] = "explicit-target-passthrough"
        report["selected_count"] = len(selected)
        return selected, report

    focused_reopened = [
        nid for nid in eligible_reopened
        if _score_candidate_focus(graph_nodes.get(nid, {}), gating_focus_terms) >= min_focus_score
    ]
    focused_fresh = [
        nid for nid in eligible_fresh
        if _score_candidate_focus(graph_nodes.get(nid, {}), gating_focus_terms) >= min_focus_score
    ]
    report["focused_reopened_count"] = len(focused_reopened)
    report["focused_fresh_count"] = len(focused_fresh)

    total_focused = len(focused_reopened) + len(focused_fresh)
    if configured_mode == "focus-term-gate-then-reorder" and total_focused >= gate_min_concepts:
        reopened_candidate_ids = _sort_ids(focused_reopened)[:batch_limit]
        fresh_budget = max(0, batch_limit - len(reopened_candidate_ids))
        fresh_candidate_ids = _sort_ids(focused_fresh)[:fresh_budget]
        selected = (reopened_candidate_ids + fresh_candidate_ids)[:batch_limit]
        report["effective_mode"] = "focus-term-gated"
        report["gate_applied"] = True
        report["suppressed_count"] = (len(eligible_reopened) + len(eligible_fresh)) - len(selected)
        report["selected_count"] = len(selected)
        return selected, report

    reopened_candidate_ids = _sort_ids(eligible_reopened)[:batch_limit]
    fresh_budget = max(0, batch_limit - len(reopened_candidate_ids))
    fresh_candidate_ids = _sort_ids(eligible_fresh)[:fresh_budget]
    selected = (reopened_candidate_ids + fresh_candidate_ids)[:batch_limit]
    report["effective_mode"] = fallback_mode
    report["suppressed_count"] = 0
    report["selected_count"] = len(selected)
    return selected, report


def load_procedure_context(repo_root: str) -> dict[str, Any]:
    """
    Load the current controller + A1 queue procedure surfaces and fail closed
    if they do not authorize an A1 run.
    """
    a2_state = Path(repo_root) / "system_v3" / "a2_state"
    controller_spine_path = _latest_current_json(
        a2_state, "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__*.json"
    )
    controller_handoff_path = _latest_current_json(
        a2_state, "A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__*.json"
    )
    a1_queue_path = _latest_current_json(
        a2_state, "A1_QUEUE_STATUS_PACKET__CURRENT__*.json"
    )

    errors: list[str] = []
    if controller_spine_path is None:
        errors.append("missing current controller launch spine")
    if controller_handoff_path is None:
        errors.append("missing current controller launch handoff")
    if a1_queue_path is None:
        errors.append("missing current A1 queue status packet")
    if errors:
        return {"ok": False, "errors": errors}

    controller_spine = json.loads(controller_spine_path.read_text(encoding="utf-8"))
    controller_handoff = json.loads(controller_handoff_path.read_text(encoding="utf-8"))
    a1_queue = json.loads(a1_queue_path.read_text(encoding="utf-8"))

    if controller_spine.get("schema") != "A2_CONTROLLER_LAUNCH_SPINE_v1":
        errors.append("controller launch spine schema mismatch")
    if controller_spine.get("launch_gate_status") != "LAUNCH_READY":
        errors.append(
            f"controller launch gate is not ready: {controller_spine.get('launch_gate_status', '')}"
        )
    if controller_spine.get("mode") != "CONTROLLER_ONLY":
        errors.append("controller launch spine mode is not CONTROLLER_ONLY")

    if controller_handoff.get("schema") != "A2_CONTROLLER_LAUNCH_HANDOFF_v1":
        errors.append("controller launch handoff schema mismatch")
    if controller_handoff.get("thread_class") != "A2_CONTROLLER":
        errors.append("controller handoff thread_class is not A2_CONTROLLER")
    if controller_handoff.get("mode") != "CONTROLLER_ONLY":
        errors.append("controller handoff mode is not CONTROLLER_ONLY")
    if not controller_handoff.get("dispatch_rule"):
        errors.append("controller handoff missing dispatch_rule")
    if not controller_handoff.get("stop_rule"):
        errors.append("controller handoff missing stop_rule")

    if a1_queue.get("schema") != "A1_QUEUE_STATUS_PACKET_v1":
        errors.append("A1 queue packet schema mismatch")
    queue_status = a1_queue.get("queue_status", "")
    if queue_status not in ALLOWED_A1_QUEUE_STATUSES:
        errors.append(f"invalid A1 queue status: {queue_status or '<missing>'}")

    queue_line = f"A1_QUEUE_STATUS: {queue_status}" if queue_status else ""
    if controller_spine.get("current_a1_queue_status") != queue_line:
        errors.append(
            "controller/A1 queue mismatch: "
            f"{controller_spine.get('current_a1_queue_status', '<missing>')} "
            f"!= {queue_line or '<missing>'}"
        )

    a1_ready_packet: dict[str, Any] | None = None
    a1_ready_packet_path: Path | None = None

    if queue_status not in READY_A1_QUEUE_STATUSES:
        errors.append(f"A1 queue not ready: {queue_line or '<missing>'}")
    else:
        for field in (
            "dispatch_id",
            "target_a1_role",
            "required_a1_boot",
            "ready_packet_json",
        ):
            value = a1_queue.get(field)
            if not value:
                errors.append(f"A1 ready packet missing {field}")

        ready_packet_raw = str(a1_queue.get("ready_packet_json", "")).strip()
        if ready_packet_raw:
            a1_ready_packet_path = _resolve_repo_path(repo_root, ready_packet_raw)
            if not a1_ready_packet_path.exists():
                errors.append(f"missing A1 ready packet: {a1_ready_packet_path}")
            else:
                a1_ready_packet = json.loads(a1_ready_packet_path.read_text(encoding="utf-8"))
                if a1_ready_packet.get("schema") != "A1_WORKER_LAUNCH_PACKET_v1":
                    errors.append("A1 ready packet schema mismatch")
                for field in (
                    "dispatch_id",
                    "target_a1_role",
                    "required_a1_boot",
                    "source_a2_artifacts",
                    "prompt_to_send",
                    "stop_rule",
                ):
                    value = a1_ready_packet.get(field)
                    if not value:
                        errors.append(f"A1 worker launch packet missing {field}")
                for field in ("dispatch_id", "target_a1_role", "required_a1_boot"):
                    queue_value = str(a1_queue.get(field, "")).strip()
                    ready_value = str(a1_ready_packet.get(field, "")).strip()
                    if queue_value and ready_value and queue_value != ready_value:
                        errors.append(f"A1 queue / ready packet mismatch on {field}")

    return {
        "ok": not errors,
        "errors": errors,
        "controller_spine_path": str(controller_spine_path),
        "controller_handoff_path": str(controller_handoff_path),
        "a1_queue_path": str(a1_queue_path),
        "a1_ready_packet_path": str(a1_ready_packet_path) if a1_ready_packet_path else "",
        "controller_spine": controller_spine,
        "controller_handoff": controller_handoff,
        "a1_queue": a1_queue,
        "a1_ready_packet": a1_ready_packet,
    }


def load_bounded_graph_fuel(repo_root: str, procedure: dict[str, Any]) -> dict[str, Any]:
    """
    Load graph-backed fuel surfaces strictly from the current A1 ready packet.
    Fail closed if the queue points only at non-graph artifacts.
    """
    ready_packet = procedure.get("a1_ready_packet") or {}
    source_artifacts = ready_packet.get("source_a2_artifacts", [])
    if not isinstance(source_artifacts, list) or not source_artifacts:
        return {"ok": False, "errors": ["A1 ready packet has no source_a2_artifacts"]}

    graph_nodes: dict[str, Any] = {}
    graph_paths: list[str] = []
    errors: list[str] = []

    for raw_artifact in source_artifacts:
        artifact_path = _resolve_repo_path(repo_root, str(raw_artifact))
        if not artifact_path.exists():
            errors.append(f"missing source artifact: {artifact_path}")
            continue
        if artifact_path.suffix.lower() != ".json":
            continue
        try:
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append(f"invalid JSON source artifact: {artifact_path}")
            continue
        nodes = payload.get("nodes")
        edges = payload.get("edges")
        if isinstance(nodes, dict) and isinstance(edges, list):
            graph_paths.append(str(artifact_path))
            graph_nodes.update(nodes)

    if errors:
        return {"ok": False, "errors": errors}
    if not graph_paths:
        return {
            "ok": False,
            "errors": [
                "A1 ready packet source_a2_artifacts contain no graph-backed JSON surfaces"
            ],
        }
    return {"ok": True, "graph_nodes": graph_nodes, "graph_paths": graph_paths}


def resolve_phase_binding(
    reg: SkillRegistry,
    candidates: list,
    preferred: list[str],
    runtime_model: str,
) -> tuple[Optional[str], bool, Optional[dict], Optional[Any], str]:
    """
    Resolve one phase all the way through:
      skill query -> selected skill -> export_for_model -> execution binding.
    Returns (selected_skill_id, fallback_used, adapter_info, dispatch_fn, reason).
    """
    selected, no_skill = resolve_skill(candidates, preferred)
    adapter_info = reg.export_for_model(selected, runtime_model) if selected else None
    execution_path = adapter_info.get("execution_path") if adapter_info else None
    if execution_path and not SKILL_DISPATCH:
        _register_dispatch()
    dispatch_fn = SKILL_DISPATCH.get(execution_path) if execution_path else None

    if no_skill:
        return selected, True, adapter_info, None, "fallback: no-skill"
    if dispatch_fn is None:
        return selected, True, adapter_info, None, "fallback: no-adapter-binding"
    return selected, False, adapter_info, dispatch_fn, "dispatch-table"


def log_skill_invocation(
    batch_id: str,
    phase: str,
    trust_zone: str,
    graph_family: str,
    considered: list[str],
    selected: Optional[str],
    fallback_used: bool,
    reason: str = "",
    adapter_info: Optional[dict] = None,
) -> None:
    """Append one invocation record to skill_invocation_log.jsonl."""
    log_path = Path(REPO) / "system_v4" / "a1_state" / "skill_invocation_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "batch_id": batch_id,
        "phase": phase,
        "trust_zone": trust_zone,
        "graph_family": graph_family,
        "considered_skill_ids": considered,
        "selected_skill_id": selected,
        "fallback_used": fallback_used,
        "reason": reason,
    }
    if adapter_info:
        record["adapter_path"] = adapter_info.get("adapter_path", "")
        record["execution_path"] = adapter_info.get("execution_path", "")
        record["model"] = adapter_info.get("model", "")
        record["execution_runtime"] = adapter_info.get("execution_runtime", "")
        record["unsupported"] = adapter_info.get("unsupported_for_model", [])
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def build_bootstrap_batch(brain: A1Brain):
    """Build the L0-bootstrapping batch: TERM_DEFs + MATH_DEFs using only L0."""
    targets = []
    alternatives = []

    # Phase 0: TERM_DEF candidates — bootstrap new vocabulary
    # Each TERM_DEF's term_literal is exempt from the undefined-term fence
    # (self-admission), but structural_form must still use L0 tokens only.
    term_candidates = [
        ("state", "density_operator_hilbert_space"),
        ("algebra", "operator_hilbert_space"),
        ("map", "channel_cptp_operator"),
        ("basis", "operator_finite_dimensional"),
        ("norm", "trace_operator"),
        ("spectrum", "hamiltonian_operator"),
        ("dual", "channel_cptp_superoperator"),
        ("evolution", "unitary_generator_hamiltonian"),
        ("product", "tensor_hilbert_space"),
        ("kernel", "superoperator_operator_space"),
    ]

    for term, struct in term_candidates:
        cid = brain._next_id("F")
        targets.append({
            "item_class": "AXIOM_HYP",
            "id": cid,
            "kind": "TERM_DEF",
            "requires": [],
            "def_fields": [
                {"field_id": f"DF_{cid}_01", "name": "term_literal",
                 "value_kind": "BARE", "value": term},
                {"field_id": f"DF_{cid}_02", "name": "structural_form",
                 "value_kind": "BARE", "value": struct},
                {"field_id": f"DF_{cid}_03", "name": "description",
                 "value_kind": "LABEL_QUOTED",
                 "value": f"Structural term '{term}' with L0 grounding: {struct}"},
            ],
            "asserts": [
                {"assert_id": f"A_{cid}_01", "token_class": "TERM_ADMISSION",
                 "token": term},
            ],
            "operator_id": "OP_COLD_CORE_EXTRACT",
            "_name": f"term_{term}",
        })

    # Phase 1: MATH_DEF candidates using ONLY L0 vocabulary
    math_candidates = [
        {
            "name": "density_operator_on_hilbert_space",
            "structural_form": "density_matrix_operator_hilbert_space",
            "desc": "A density matrix is a positive semidefinite trace-one operator "
                    "on a finite dimensional Hilbert space",
        },
        {
            "name": "cptp_channel_on_operator_space",
            "structural_form": "channel_cptp_operator_space",
            "desc": "A CPTP channel is a completely positive trace preserving "
                    "superoperator between operator spaces",
        },
        {
            "name": "lindblad_generator_form",
            "structural_form": "lindblad_generator_operator_commutator",
            "desc": "The Lindblad generator is a superoperator expressed via "
                    "commutator and anticommutator terms",
        },
        {
            "name": "tensor_product_hilbert_space",
            "structural_form": "tensor_hilbert_space_finite_dimensional",
            "desc": "The tensor product of finite dimensional Hilbert spaces",
        },
        {
            "name": "partial_trace_superoperator",
            "structural_form": "partial_trace_superoperator_operator",
            "desc": "The partial trace is a superoperator that maps density matrices "
                    "to reduced density matrices",
        },
        {
            "name": "unitary_channel",
            "structural_form": "unitary_channel_operator",
            "desc": "A unitary channel on a finite dimensional Hilbert space operator",
        },
        {
            "name": "hamiltonian_generator",
            "structural_form": "hamiltonian_generator_unitary",
            "desc": "The Hamiltonian is the generator of unitary evolution on a "
                    "Hilbert space",
        },
    ]

    name_to_cid = {}  # Track mc name -> assigned candidate ID for lineage

    for mc in math_candidates:
        cid = brain._next_id("F")
        name_to_cid[mc["name"]] = cid
        targets.append({
            "item_class": "AXIOM_HYP",
            "id": cid,
            "kind": "MATH_DEF",
            "requires": [],
            "def_fields": [
                {"field_id": f"DF_{cid}_01", "name": "structural_form",
                 "value_kind": "BARE", "value": mc["structural_form"]},
                {"field_id": f"DF_{cid}_02", "name": "description",
                 "value_kind": "LABEL_QUOTED", "value": mc["desc"]},
            ],
            "asserts": [
                {"assert_id": f"A_{cid}_01", "token_class": "STRUCTURAL",
                 "token": mc["structural_form"].split("_")[0]},
                {"assert_id": f"A_{cid}_02", "token_class": "STRUCTURAL",
                 "token": mc["structural_form"].split("_")[1]},
            ],
            "operator_id": "OP_COLD_CORE_EXTRACT",
            "_name": mc["name"],
        })

        # Probe for each MATH_DEF
        pid = brain._next_id("P")
        targets.append({
            "item_class": "PROBE_HYP",
            "id": pid,
            "kind": "SIM_SPEC",
            "requires": [cid],
            "def_fields": [
                {"field_id": f"DF_{pid}_01", "name": "probe_target",
                 "value_kind": "BARE", "value": cid},
            ],
            "asserts": [
                {"assert_id": f"A_{pid}_01", "token_class": "PROBE_CHECK",
                 "token": mc["structural_form"].split("_")[0]},
            ],
            "operator_id": "OP_COLD_CORE_EXTRACT",
            "_name": f"probe_{mc['name']}",
        })

    # Phase 2: Designed-to-fail alternatives
    for mc in math_candidates[:3]:
        # Alt: derived-only poison
        alt_id = brain._next_id("F")
        alternatives.append({
            "item_class": "AXIOM_HYP",
            "id": alt_id,
            "kind": "MATH_DEF",
            "requires": [],
            "def_fields": [
                {"field_id": f"DF_{alt_id}_01", "name": "structural_form",
                 "value_kind": "BARE", "value": "equality_identity_mapping"},
                {"field_id": f"DF_{alt_id}_02", "name": "description",
                 "value_kind": "LABEL_QUOTED", "value": "Designed to fail: derived-only terms"},
            ],
            "asserts": [
                {"assert_id": f"A_{alt_id}_01", "token_class": "STRUCTURAL",
                 "token": "equality"},
            ],
            "operator_id": "OP_COLD_CORE_EXTRACT",
            "source_concept_id": name_to_cid.get(mc["name"], ""),
            "_name": f"alt_poison_{mc['name']}",
        })

        # Alt: forward dependency
        alt2_id = brain._next_id("F")
        alternatives.append({
            "item_class": "AXIOM_HYP",
            "id": alt2_id,
            "kind": "MATH_DEF",
            "requires": ["UNDEFINED_9999"],
            "def_fields": [
                {"field_id": f"DF_{alt2_id}_01", "name": "structural_form",
                 "value_kind": "BARE", "value": mc["structural_form"]},
                {"field_id": f"DF_{alt2_id}_02", "name": "description",
                 "value_kind": "LABEL_QUOTED", "value": "Designed to fail: forward dep"},
            ],
            "asserts": [],
            "operator_id": "OP_COLD_CORE_EXTRACT",
            "source_concept_id": name_to_cid.get(mc["name"], ""),
            "_name": f"alt_fwddep_{mc['name']}",
        })

    # Alt: non-L0 token
    alt3_id = brain._next_id("F")
    alternatives.append({
        "item_class": "AXIOM_HYP",
        "id": alt3_id,
        "kind": "MATH_DEF",
        "requires": [],
        "def_fields": [
            {"field_id": f"DF_{alt3_id}_01", "name": "structural_form",
             "value_kind": "BARE", "value": "classical_probability_distribution"},
            {"field_id": f"DF_{alt3_id}_02", "name": "description",
             "value_kind": "LABEL_QUOTED", "value": "Designed to fail: non-L0 tokens"},
        ],
        "asserts": [],
        "operator_id": "OP_COLD_CORE_EXTRACT",
        "_name": "alt_nonl0_classical",
    })

    return targets, alternatives


def main() -> int:
    print("=" * 60)
    print("REAL RATCHET: PROCEDURE-DRIVEN QUEUE-FED BATCH")
    print("=" * 60)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(f"L0 lexeme set ({len(L0_LEXEME_SET)}): {sorted(L0_LEXEME_SET)}")

    # ─── Skill Registry ───
    reg = SkillRegistry(REPO)
    print(f"\nSkill registry: {reg.summary()['total']} skills loaded")
    runtime_model = get_runtime_model(reg)
    print(f"Runtime model: {runtime_model}")

    procedure = load_procedure_context(REPO)
    print(f"\nProcedure gate:")
    if not procedure["ok"]:
        print("  RESULT: FAIL_CLOSED")
        for err in procedure["errors"]:
            print(f"  - {err}")
        print("  Required surfaces:")
        print("  - current A2 controller launch spine")
        print("  - current A2 controller launch handoff")
        print("  - current A1 queue status packet in READY_* state")
        return 2

    print("  RESULT: PASS")
    print(f"  Controller spine:  {procedure['controller_spine_path']}")
    print(f"  Controller handoff:{procedure['controller_handoff_path']}")
    print(f"  A1 queue packet:   {procedure['a1_queue_path']}")
    print(f"  Queue status:      {procedure['a1_queue']['queue_status']}")
    print(f"  Dispatch ID:       {procedure['a1_queue'].get('dispatch_id', '')}")
    print(f"  Required A1 boot:  {procedure['a1_queue'].get('required_a1_boot', '')}")
    print(f"  Target A1 role:    {procedure['a1_queue'].get('target_a1_role', '')}")
    print(f"  Ready packet:      {procedure.get('a1_ready_packet_path', '')}")

    # ─── Initialize ───
    brain = A1Brain(REPO)
    kernel = BKernel(brain)
    sim = SimEngine(kernel)

    print(f"\nPrior state:")
    print(f"  Term registry:  {len(brain.term_registry)}")
    print(f"  Survivors:      {len(kernel.survivor_ledger)}")
    print(f"  Graveyard:      {len(kernel.graveyard)}")
    print(f"  SIM evidence:   {len(sim.evidence_log)}")

    # ─── Build Dispatch Table ───
    # Each entry maps adapter_path → callable that performs that phase's work.
    # The callable receives a context dict and returns a result.
    # This is what makes the registry AUTHORITATIVE, not just advisory.
    _register_dispatch()

    # ─── Load Graph Fuel ───
    batch_id = f"BATCH_LIVE_{int(time.time())}"

    # ── Initialize live witness recorder ──
    witness_path = Path(REPO) / "system_v4" / "a2_state" / "witness_corpus_v1.json"
    witness_recorder = WitnessRecorder(witness_path)
    evermem_sync_state_path = Path(REPO) / "system_v4" / "a2_state" / "EVERMEM_WITNESS_SYNC_STATE__CURRENT__v1.json"
    evermem_sync_report_json = (
        Path(REPO) / "system_v4" / "a2_state" / "audit_logs" / "EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json"
    )
    evermem_sync_report_md = (
        Path(REPO) / "system_v4" / "a2_state" / "audit_logs" / "EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.md"
    )
    a2_brain_refresh_report_json = (
        Path(REPO) / "system_v4" / "a2_state" / "audit_logs" / "A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json"
    )
    a2_brain_refresh_report_md = (
        Path(REPO) / "system_v4" / "a2_state" / "audit_logs" / "A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.md"
    )
    a2_brain_refresh_packet_json = (
        Path(REPO) / "system_v4" / "a2_state" / "audit_logs" / "A2_BRAIN_SURFACE_REFRESH_PACKET__CURRENT__v1.json"
    )
    outer_session_ledger_state_json = (
        Path(REPO) / "system_v4" / "a2_state" / "OUTER_SESSION_LEDGER_STATE__CURRENT__v1.json"
    )
    outer_session_ledger_events_jsonl = (
        Path(REPO) / "system_v4" / "a2_state" / "OUTER_SESSION_LEDGER_EVENTS__APPEND_ONLY__v1.jsonl"
    )
    outer_session_ledger_report_json = (
        Path(REPO) / "system_v4" / "a2_state" / "audit_logs" / "OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.json"
    )
    outer_session_ledger_report_md = (
        Path(REPO) / "system_v4" / "a2_state" / "audit_logs" / "OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.md"
    )

    # ── Continuous intent & context capture ──
    # Record system context at batch start — every run preserves its own state
    witness_recorder.record_context(
        context_text=(
            f"Batch {batch_id} started. "
            f"Queue status: {procedure['a1_queue']['queue_status']}. "
            f"Dispatch ID: {procedure['a1_queue'].get('dispatch_id', '')}. "
            f"Terms: {len(brain.term_registry)}. "
            f"Survivors: {len(kernel.survivor_ledger)}. "
            f"Graveyard: {len(kernel.graveyard)}."
        ),
        source="system",
        tags={"batch": batch_id, "phase": "STARTUP"},
    )

    # If the queue packet declares intent, record it as first-class
    queue_intent = procedure["a1_queue"].get("maker_intent", "")
    queue_notes = procedure["a1_queue"].get("notes", "")
    if queue_intent:
        witness_recorder.record_intent(
            intent_text=queue_intent,
            source="maker",
            tags={"batch": batch_id, "phase": "STARTUP"},
        )
    if queue_notes:
        witness_recorder.record_intent(
            intent_text=queue_notes,
            source="maker",
            tags={"batch": batch_id, "phase": "STARTUP", "type": "queue_notes"},
        )
    witness_recorder.flush()

    # ─── Upstream Graph Phases Orchestration ───
    # Sequentially invoke the registry-bound upstream layers before reaching extraction.
    upstream_phases = [
        ("PHASE_A2_3_INTAKE", ["a2-high-intake-graph-builder"]),
        ("PHASE_A2_2_CONTRADICTION", ["a2-mid-refinement-graph-builder"]),
        ("PHASE_A2_1_PROMOTION", ["a2-low-control-graph-builder"]),
        ("PHASE_A1_ROSETTA", ["a1-jargoned-graph-builder", "a1-rosetta-mapper"]),
        ("PHASE_A1_STRIPPER", ["a1-stripped-graph-builder", "a1-rosetta-stripper"]),
    ]
    for layer_id, preferred_skills in upstream_phases:
        phase_skills = reg.find_relevant(
            layer_id=layer_id,
            capabilities_all=["is_phase_runner", "is_generic_phase_handler"],
        )
        p_sel, p_fall, p_adp, p_disp, p_reas = resolve_phase_binding(
            reg, phase_skills, preferred_skills, runtime_model=runtime_model
        )
        upstream_fallback_used = p_sel is None
        log_skill_invocation(
            batch_id=batch_id, phase=layer_id, trust_zone=layer_id, graph_family="upstream",
            considered=[s.skill_id for s in phase_skills], selected=p_sel, fallback_used=upstream_fallback_used,
            reason=p_reas, adapter_info=p_adp
        )
        print(f"\n{'─'*60}")
        print(f"UPSTREAM PHASE: {layer_id}")
        print(f"  Skill:     {p_sel or 'FALLBACK'} {'[dispatch]' if p_disp else '[unwired registry pass]'}")
        print(f"  Available: {len(phase_skills)} candidates")
        if p_disp:
            try:
                upstream_result = p_disp({"repo": REPO, "phase": layer_id})
            except FileNotFoundError as exc:
                print(f"  Result:    skipped")
                print(f"  Reason:    missing prerequisite: {exc}")
                print(f"{'─'*60}")
                continue
            except Exception as exc:
                print(f"  RESULT:    FAIL_CLOSED")
                print(f"  Error:     upstream phase dispatch failed: {exc}")
                return 2
            print(f"  Result:    executed")
            if isinstance(upstream_result, dict):
                for key, value in sorted(upstream_result.items()):
                    print(f"  {key}: {value}")
        else:
            print(f"  Result:    not executed ({p_reas})")
        print(f"{'─'*60}")

    cartridge_owner_skills = reg.find_relevant(
        trust_zone="A1_CARTRIDGE",
        graph_family="strategy",
        capabilities_all=["is_owner_graph_builder"],
    )
    c_owner_sel, c_owner_fall, c_owner_adp, c_owner_disp, c_owner_reas = resolve_phase_binding(
        reg,
        cartridge_owner_skills,
        preferred=["a1-cartridge-graph-builder"],
        runtime_model=runtime_model,
    )
    log_skill_invocation(
        batch_id=batch_id,
        phase="A1_CARTRIDGE_OWNER_GRAPH",
        trust_zone="A1_CARTRIDGE",
        graph_family="strategy",
        considered=[s.skill_id for s in cartridge_owner_skills],
        selected=c_owner_sel,
        fallback_used=c_owner_fall,
        reason=c_owner_reas,
        adapter_info=c_owner_adp,
    )
    print(f"\n{'─'*60}")
    print("PRE-PHASE: A1 CARTRIDGE OWNER GRAPH")
    print(
        f"  Skill:     {c_owner_sel or 'FALLBACK'} "
        f"{'[dispatch]' if c_owner_disp else '[unwired registry pass]'}"
    )
    print(f"  Available: {len(cartridge_owner_skills)} candidates")
    if c_owner_disp:
        try:
            cartridge_owner_result = c_owner_disp({"repo": REPO})
            cartridge_owner_report, cartridge_owner_json_path, cartridge_owner_audit_note_path = (
                _load_owner_graph_preflight_report(
                    REPO,
                    cartridge_owner_result,
                    expected_schema="A1_CARTRIDGE_GRAPH_v1",
                    label="A1 cartridge owner preflight",
                )
            )
        except Exception as exc:
            print("  RESULT:    FAIL_CLOSED")
            print(f"  Error:     cartridge owner preflight failed: {exc}")
            return 2
        else:
            print("  Result:    executed")
            print(f"  json_path: {cartridge_owner_json_path}")
            print(f"  audit_note_path: {cartridge_owner_audit_note_path}")
            print(f"  build_status: {cartridge_owner_report['build_status']}")
            print(f"  materialized: {cartridge_owner_report['materialized']}")
            print(
                f"  node_count: {cartridge_owner_report['summary'].get('node_count', 0)}"
            )
            print(
                f"  edge_count: {cartridge_owner_report['summary'].get('edge_count', 0)}"
            )
            print(f"  blocker_count: {len(cartridge_owner_report['blockers'])}")
            if cartridge_owner_report["build_status"] == "FAIL_CLOSED":
                print(
                    "  Semantics: fail-closed owner-graph preflight; "
                    "continuing to packaging operator"
                )
            else:
                print("  Semantics: owner graph materialized")
    else:
        print(f"  Result:    not executed ({c_owner_reas})")
    print(f"{'─'*60}")

    # Skill selection: Phase 1 (Cartridge Packaging Operator)
    # This live phase still expects a strategy-packet style runtime operator,
    # not an owner-graph materialization report. If a phase-bound owner builder
    # ever exists, prefer it first; otherwise stay on the current operator path.
    p1_owner_builder_skills = reg.find_relevant(
        layer_id="PHASE_A1_CARTRIDGE",
        capabilities_all=[
            "is_phase_runner",
            "is_generic_phase_handler",
            "is_owner_graph_builder",
        ],
    )
    p1_skills = p1_owner_builder_skills or reg.find_relevant(
        layer_id="PHASE_A1_CARTRIDGE",
        capabilities_all=["is_phase_runner", "is_generic_phase_handler"],
    )
    p1_selector_mode = "owner-builder" if p1_owner_builder_skills else "generic-operator"
    if not p1_skills:  # Fallback to legacy
        p1_skills = reg.find_relevant(trust_zone="A1_STRIPPED", graph_family="dependency", skill_type="extraction")
        p1_selector_mode = "legacy-fallback"
        
    p1_selected, p1_fallback, p1_adapter, p1_dispatch, p1_reason = resolve_phase_binding(
        reg,
        p1_skills,
        preferred=["a1-cartridge-graph-builder", "a1-cartridge-assembler", "a1-brain"],
        runtime_model=runtime_model,
    )
    print(f"\n{'─'*60}")
    print(f"PHASE 1: A1 CARTRIDGE PACKAGING")
    print(f"  Skill: {p1_selected or 'FALLBACK(direct)'} {'[dispatch]' if not p1_fallback else '[fallback]'} (considered {len(p1_skills)})")
    print(f"  Selector mode: {p1_selector_mode}")
    print(f"{'─'*60}")
    
    fuel = load_bounded_graph_fuel(REPO, procedure)
    if not fuel["ok"]:
        print("❌ Bounded fuel load failed:")
        for err in fuel["errors"]:
            print(f"  - {err}")
        return 2
    graph_nodes = fuel["graph_nodes"]
    print(f"  Bounded graph sources: {len(fuel['graph_paths'])}")
    for path in fuel["graph_paths"]:
        print(f"    - {path}")

    intent_control: dict[str, Any] | None = None
    intent_lane_id: str | None = None
    intent_bias_config: dict[str, Any] | None = None
    intent_graph_skills = reg.find_relevant(
        trust_zone="A2_2_CANDIDATE",
        tags_any=["intent-control"],
    )
    ig_selected, ig_fallback, ig_adapter, ig_dispatch, ig_reason = resolve_phase_binding(
        reg,
        intent_graph_skills,
        preferred=["intent-refinement-graph-builder"],
        runtime_model=runtime_model,
    )
    log_skill_invocation(
        batch_id=batch_id,
        phase="A2_INTENT_GRAPH_SYNC",
        trust_zone="A2_2_CANDIDATE",
        graph_family="control",
        considered=[s.skill_id for s in intent_graph_skills],
        selected=ig_selected,
        fallback_used=ig_fallback,
        reason=ig_reason,
        adapter_info=ig_adapter,
    )
    print(f"\n{'─'*60}")
    print("PRE-PHASE: A2 INTENT GRAPH SYNC")
    print(
        f"  Skill:     {ig_selected or 'FALLBACK'} "
        f"{'[dispatch]' if ig_dispatch else '[unwired registry pass]'}"
    )
    print(f"  Available: {len(intent_graph_skills)} candidates")
    if ig_dispatch:
        try:
            intent_graph_result = ig_dispatch({"repo": REPO})
        except Exception as exc:
            print("  RESULT:    FAIL_CLOSED")
            print(f"  Error:     intent graph sync failed: {exc}")
            return 2
        else:
            print("  Result:    executed")
            if isinstance(intent_graph_result, dict):
                print(f"  raw_intent_nodes: {intent_graph_result.get('raw_intent_nodes', 0)}")
                print(f"  raw_context_nodes: {intent_graph_result.get('raw_context_nodes', 0)}")
                print(f"  refined_intent_nodes: {intent_graph_result.get('refined_intent_nodes', 0)}")
    else:
        print(f"  Result:    not executed ({ig_reason})")
    print(f"{'─'*60}")

    intent_control_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="control",
        tags_any=["intent-control"],
    )
    ic_selected, ic_fallback, ic_adapter, ic_dispatch, ic_reason = resolve_phase_binding(
        reg,
        intent_control_skills,
        preferred=["intent-control-surface-builder"],
        runtime_model=runtime_model,
    )
    log_skill_invocation(
        batch_id=batch_id,
        phase="A2_INTENT_CONTROL",
        trust_zone="A2_LOW_CONTROL",
        graph_family="control",
        considered=[s.skill_id for s in intent_control_skills],
        selected=ic_selected,
        fallback_used=ic_fallback,
        reason=ic_reason,
        adapter_info=ic_adapter,
    )
    print(f"\n{'─'*60}")
    print("PRE-PHASE: A2 INTENT CONTROL")
    print(
        f"  Skill:     {ic_selected or 'FALLBACK'} "
        f"{'[dispatch]' if ic_dispatch else '[unwired registry pass]'}"
    )
    print(f"  Available: {len(intent_control_skills)} candidates")
    if ic_dispatch:
        try:
            intent_control_result = ic_dispatch({"repo": REPO})
            intent_control, intent_json_path, intent_audit_path = _load_intent_control_surface_report(
                REPO,
                intent_control_result,
            )
        except Exception as exc:
            print("  RESULT:    FAIL_CLOSED")
            print(f"  Error:     intent control build failed: {exc}")
            return 2
        else:
            intent_lane_id = intent_control.get("control", {}).get("lane_id")
            control_block = intent_control.setdefault("control", {})
            runtime_policy = normalize_intent_runtime_policy(intent_control)
            control_block["runtime_policy"] = runtime_policy
            control_block["focus_terms"] = runtime_policy.get("focus_terms", [])
            control_block["concept_selection"] = runtime_policy.get("concept_selection", {})
            control_block["candidate_policy"] = runtime_policy.get("candidate_policy", {})
            control_block["alternative_policy"] = runtime_policy.get("alternative_policy", {})
            control_block["bias_config"] = runtime_policy.get("bias_config", {})
            intent_bias_config = runtime_policy.get("bias_config", {})
            print("  Result:    executed")
            print(f"  json_path: {intent_json_path}")
            print(f"  audit_note_path: {intent_audit_path}")
            print(
                f"  maker_intents: {intent_control['self_audit'].get('maker_intent_count', 0)}"
            )
            print(
                f"  runtime_contexts: {intent_control['self_audit'].get('runtime_context_count', 0)}"
            )
            print(
                f"  refined_intents: {intent_control['self_audit'].get('refined_intent_count', 0)}"
            )
            print(
                f"  focus_terms: {intent_control['self_audit'].get('focus_term_count', 0)}"
            )
            for tension in intent_control.get("open_tensions", [])[:3]:
                print(f"  tension:    {tension}")
            intent_control_failures = _validate_intent_control_surface(intent_control)
            if intent_control_failures:
                print("  RESULT:    FAIL_CLOSED")
                for failure in intent_control_failures:
                    print(f"  blocker:    {failure}")
                return 2
    else:
        print(f"  Result:    not executed ({ic_reason})")
        print("  RESULT:    FAIL_CLOSED")
        print("  blocker:    missing intent control surface dispatch")
        return 2
    print(f"{'─'*60}")
    
    # ─── Disciplined Graph Selector ───
    # Build the set of concept IDs already treated by the runtime (survived,
    # killed, parked, or graveyarded).  Any concept whose source_concept_id
    # or lineage_ref is already in this set is skipped.
    treated_ids: set = set()
    for nd in graph_nodes.values():
        nt = nd.get("node_type", "")
        if nt in ("B_SURVIVOR", "B_PARKED", "GRAVEYARD_RECORD", "SIM_KILL"):
            # The node's properties.candidate_id or properties.target_ref
            # is the original concept / candidate that was already processed.
            props = nd.get("properties", {})
            for key in ("candidate_id", "target_ref", "target_id", "source_concept_id"):
                val = props.get(key)
                if val:
                    treated_ids.add(val)
            lineage_refs = props.get("lineage_refs", [])
            if isinstance(lineage_refs, list):
                for ref in lineage_refs:
                    if ref:
                        treated_ids.add(ref)
            # Also treat the raw node id prefix (e.g. B_SURVIVOR::F001 → F001)
            raw = nd.get("id", "")
            if "::" in raw:
                treated_ids.add(raw.split("::", 1)[1])

    # Now select REFINED_CONCEPT / EXTRACTED_CONCEPT nodes NOT already treated.
    # Also skip concepts already routed by A1 (diverted, no-op, or discourse).
    from system_v4.skills.a1_routing_state import A1RoutingState
    a1_routing = A1RoutingState(REPO)
    a1_blocked = a1_routing.get_blocked_ids()
    reopened_ids = a1_routing.get_reopen_requested_ids()

    eligible_reopened = []
    eligible_fresh = []
    for nd in graph_nodes.values():
        nid = nd.get("id", "")
        if nd.get("node_type") not in ("REFINED_CONCEPT", "EXTRACTED_CONCEPT"):
            continue
        # Skip anything the runtime has already ingested
        if nid in treated_ids and nid not in reopened_ids:
            continue
        # Skip anything A1 has already routed (Rosetta, no-op, discourse)
        if nid in a1_blocked:
            continue
        if nid in reopened_ids:
            eligible_reopened.append(nid)
        else:
            eligible_fresh.append(nid)

    ready_packet = procedure.get("a1_ready_packet") or {}
    explicit_targets = ready_packet.get("target_concept_ids", [])
    
    explicit_targets_used = bool(explicit_targets)
    concept_selection_report: dict[str, Any] = {
        "configured_mode": "disabled",
        "effective_mode": "disabled",
        "selected_count": 0,
        "suppressed_count": 0,
        "explicit_targets_used": explicit_targets_used,
    }

    if explicit_targets:
        # Strict Fuel: Only process concepts explicitly handed off by the controller.
        candidate_ids = [nid for nid in explicit_targets if nid in graph_nodes and nid not in treated_ids and nid not in a1_blocked]
        if intent_control:
            _, concept_selection_report = _apply_intent_concept_selection(
                [],
                [],
                graph_nodes,
                intent_control,
                explicit_targets_used=True,
                batch_limit=len(candidate_ids) or 10,
            )
            concept_selection_report["selected_count"] = len(candidate_ids)
        print(f"  🚀 Strict Controller Fuel Applied: Selected {len(candidate_ids)} explicitly nominated targets.")
    else:
        # Legacy fallback scan, optionally tightened by intent-control gating.
        candidate_ids, concept_selection_report = _apply_intent_concept_selection(
            eligible_reopened,
            eligible_fresh,
            graph_nodes,
            intent_control,
            explicit_targets_used=False,
            batch_limit=10,
        )
        print(
            f"  ⚠️ Global Scan Fallback: Selected {len(candidate_ids)} concepts "
            f"({min(len(candidate_ids), len(eligible_reopened))} reopened/focus-prioritized, "
            f"{max(0, len(candidate_ids) - min(len(candidate_ids), len(eligible_reopened)))} fresh/focus-prioritized; "
            f"excluded {len(treated_ids)} runtime-treated, {len(a1_blocked)} A1-routed)."
        )

    if intent_control:
        intent_control = json.loads(json.dumps(intent_control))
        control_block = intent_control.setdefault("control", {})
        runtime_policy = normalize_intent_runtime_policy(intent_control)
        runtime_policy["concept_selection_runtime"] = concept_selection_report
        concept_selection = dict(runtime_policy.get("concept_selection", {}))
        concept_selection["runtime"] = concept_selection_report
        runtime_policy["concept_selection"] = concept_selection
        control_block["runtime_policy"] = runtime_policy
        control_block["focus_terms"] = runtime_policy.get("focus_terms", [])
        control_block["concept_selection"] = concept_selection
        control_block["candidate_policy"] = runtime_policy.get("candidate_policy", {})
        control_block["alternative_policy"] = runtime_policy.get("alternative_policy", {})
        control_block["bias_config"] = runtime_policy.get("bias_config", {})
        control_block["concept_selection_runtime"] = concept_selection_report
        effective_mode = concept_selection_report.get("effective_mode", "disabled")
        if effective_mode == "focus-term-gated":
            print(
                "  🎯 Intent concept gate applied: "
                f"{concept_selection_report.get('focused_reopened_count', 0) + concept_selection_report.get('focused_fresh_count', 0)} "
                f"focus-matched eligible concepts -> {len(candidate_ids)} admitted."
            )
        elif effective_mode == "reorder_only":
            print(
                f"  🎯 Intent focus reorder applied: {len(concept_selection_report.get('focus_terms', []))} terms "
                f"over {len(candidate_ids)} fallback candidates."
            )
        elif effective_mode == "explicit-target-passthrough":
            print("  🎯 Intent steering held bounded: explicit controller targets passed through unchanged.")

    from system_v4.skills.v4_tape_writer import V4TapeWriter
    tape_writer = V4TapeWriter(str(Path(REPO) / "system_v4" / "runtime_state"))

    # ─── Wiggle Pre-Phase (optional) ───
    # If wiggle-lane-runner is active (not draft), run multi-lane extraction.
    # Otherwise fall through to single-lane.
    wiggle_skills = reg.find_relevant(
        trust_zone="A1_STRIPPED", graph_family="dependency",
        skill_type="agent", tags_any=["wiggle"],
    )
    pw_selected, pw_fallback, pw_adapter, pw_dispatch, pw_reason = resolve_phase_binding(
        reg, wiggle_skills, preferred=["wiggle-lane-runner"], runtime_model=runtime_model,
    )
    wiggle_active = pw_dispatch is not None and not pw_fallback

    if wiggle_active:
        log_skill_invocation(
            batch_id=batch_id, phase="A1_WIGGLE",
            trust_zone="A1_STRIPPED", graph_family="dependency",
            considered=[s.skill_id for s in wiggle_skills],
            selected=pw_selected, fallback_used=pw_fallback,
            reason=pw_reason, adapter_info=pw_adapter,
        )
        print(f"\n{'─'*60}")
        print(f"PRE-PHASE: A1 WIGGLE ({pw_selected})")
        print(f"{'─'*60}")
        wiggle_envelope = pw_dispatch({
            "repo": REPO, "brain": brain,
            "concept_ids": candidate_ids, "graph_nodes": graph_nodes,
            "lane_id": intent_lane_id,
            "bias_config": intent_bias_config,
            "intent_control": intent_control,
        })
        merged = wiggle_envelope.merged_strategy_packet
        targets = merged.get("targets", [])
        alternatives = merged.get("alternatives", [])
        merge_report = wiggle_envelope.merge_report
        print(f"  Wiggle ID:     {wiggle_envelope.wiggle_id}")
        print(f"  Lanes run:     {len(wiggle_envelope.lane_packets)}")
        print(f"  Merged targets:      {len(targets)}")
        print(f"  Merged alternatives: {len(alternatives)}")
        for entry in merge_report.get("comparison_matrix", []):
            support = entry.get("support_count", 0)
            lanes = entry.get("lane_ids", [])
            kind = entry.get("kind", "")
            marker = "🔗" if support >= 2 else "⚠️"
            print(f"    {marker} {kind:12s} support={support} lanes={lanes}")
    else:
        # Single-lane A1 extraction (original path)
        log_skill_invocation(
            batch_id=batch_id, phase="A1_EXTRACTION",
            trust_zone="A1_STRIPPED", graph_family="dependency",
            considered=[s.skill_id for s in p1_skills],
            selected=p1_selected, fallback_used=p1_fallback,
            reason=p1_reason, adapter_info=p1_adapter,
        )
        if p1_dispatch:
            packet = p1_dispatch({
                "brain": brain, "candidate_ids": candidate_ids,
                "graph_nodes": graph_nodes,
                "lane_id": intent_lane_id,
                "bias_config": intent_bias_config,
                "intent_control": intent_control,
            })
        else:
            packet = brain.build_strategy_packet(
                candidate_ids, graph_nodes,
                strategy_id=f"A1_STRAT_LIVE_{int(time.time())}",
                lane_id=intent_lane_id,
                bias_config=intent_bias_config,
                intent_control=intent_control,
            )
        targets = packet.targets
        alternatives = packet.alternatives

    outcomes = []
    accept = []
    park = []
    reject = []
    batch_structural = []
    skipped_probes = 0
    empty_batch = not targets
    
    print(f"  A1 Extracted Targets:      {len(targets)}")
    print(f"  A1 Generated Alternatives: {len(alternatives)} (designed to fail)")
    for t in targets:
        print(f"    [{t['id']}] {t['kind']:10s} {t.get('_name', '')}")
    for a in alternatives:
        print(f"    [{a['id']}] ALT        {a.get('_name', '')}")

    # ─── Empty batch guard: skip downstream if A1 found nothing ───
    if empty_batch:
        print(f"\n  ⏭  No kernel targets extracted — skipping B/SIM/tape for {batch_id}")
    else:
        # ─── Artifact emission: EXPORT_BLOCK ───
        export_block_str = tape_writer.write_export_block(batch_id, targets, alternatives)
        print(f"  📝 Initialized EXPORT_BLOCK for {batch_id}")
        # ─── LLM COUNCIL: ENSEMBLE ADJUDICATION ───
        lc_skills = reg.find_relevant(trust_zone="B_ADJUDICATED", graph_family="runtime", tags_any=["llm-council"])
        lc_selected, lc_fallback, lc_adapter, lc_dispatch, lc_reason = resolve_phase_binding(
            reg, lc_skills, preferred=["llm-council-operator"], runtime_model=runtime_model
        )
        if lc_dispatch:
            log_skill_invocation(
                batch_id=batch_id, phase="LLM_COUNCIL",
                trust_zone="B_ADJUDICATED", graph_family="runtime",
                considered=[s.skill_id for s in lc_skills],
                selected=lc_selected, fallback_used=lc_fallback,
                reason=lc_reason, adapter_info=lc_adapter,
            )
            print(f"\n{'─'*60}")
            print(f"PRE-PHASE: LLM COUNCIL ENSEMBLE ADJUDICATION")
            print(f"  Skill: {lc_selected or 'FALLBACK'} {'[dispatch]' if not lc_fallback else '[fallback]'}")
            print(f"{'─'*60}")
            from system_v4.skills.runtime_state_kernel import RuntimeState
            state_targets = [RuntimeState(region=t["id"], invariants=t.get("invoices", [])) for t in targets]
            lc_result = lc_dispatch({
                "candidates": state_targets,
                "consensus_threshold": 0.51,
                "recorder": witness_recorder,
                "witness_tags": {"batch": batch_id, "phase": "LLM_COUNCIL"}
            })
            accepted_regions = {s.region for s in lc_result.get("accepted", [])}
            print(f"  Council accepted {len(accepted_regions)}/{len(targets)} targets")
            targets = [t for t in targets if t["id"] in accepted_regions]
            if not targets:
                print(f"  [LLM Council] All targets rejected. Skipping B_ENFORCEMENT.")
                empty_batch = True

        # ─── B: Enforcement ───
        # Skill selection: Phase 2
        p2_skills = reg.find_relevant(trust_zone="B_ADJUDICATED", graph_family="runtime", skill_type="verification")
        p2_selected, p2_fallback, p2_adapter, p2_dispatch, p2_reason = resolve_phase_binding(
            reg, p2_skills, preferred=["b-kernel"], runtime_model=runtime_model
        )
        log_skill_invocation(
            batch_id=batch_id, phase="B_ENFORCEMENT",
            trust_zone="B_ADJUDICATED", graph_family="runtime",
            considered=[s.skill_id for s in p2_skills],
            selected=p2_selected, fallback_used=p2_fallback,
            reason=p2_reason,
            adapter_info=p2_adapter,
        )
        print(f"\n{'─'*60}")
        print(f"PHASE 2: B KERNEL ENFORCEMENT (7 stages)")
        print(f"  Skill: {p2_selected or 'FALLBACK(direct)'} {'[dispatch]' if not p2_fallback else '[fallback]'} (considered {len(p2_skills)})")
        print(f"{'─'*60}")
        if p2_dispatch:
            outcomes = p2_dispatch({
                "kernel": kernel, "targets": targets, "alternatives": alternatives,
            })
        else:
            outcomes = kernel.adjudicate_batch(targets, alternatives)
        
        # ─── Artifact emission: THREAD_B_REPORT & CAMPAIGN_TAPE ───
        tape_writer.write_thread_b_report(batch_id, outcomes, export_block_str)
        print(f"  📝 Appended THREAD_B_REPORT to CAMPAIGN_TAPE {batch_id}")

        accept = [o for o in outcomes if o.outcome == "ACCEPT"]
        park = [o for o in outcomes if o.outcome == "PARK"]
        reject = [o for o in outcomes if o.outcome == "REJECT"]

        print(f"\n  ✅ ACCEPT: {len(accept)}")
        print(f"  ⏸️  PARK:   {len(park)}")
        print(f"  ❌ REJECT: {len(reject)}")

        for o in outcomes:
            marker = {"ACCEPT": "✅", "PARK": "⏸️ ", "REJECT": "❌"}.get(o.outcome, "?")
            cand = next((c for c in targets + alternatives if c["id"] == o.candidate_id), None)
            name = cand.get("_name", "") if cand else ""
            stage = f" @ {o.stage_failed}" if o.stage_failed else ""
            tag = f" [{o.reason_tag}]" if o.reason_tag else ""
            print(f"  {marker} {o.candidate_id:6s} {name:40s} → {o.outcome}{stage}{tag}")
            if o.outcome != "ACCEPT" and o.detail:
                print(f"       {o.detail[:90]}")

        # ─── Z3 HARDNESS GATE: structural constraint check on accepted outcomes ───
        z3_gate_violations = 0
        for o in accept:
            survivor = kernel.survivor_ledger.get(o.candidate_id)
            if not survivor:
                continue
            # Build a RuntimeState from the survivor's structural form
            gate_state = RuntimeState(
                region=f"B_ADJUDICATED:{o.candidate_id}",
                phase_index=0,
                phase_period=8,
                boundaries=[BoundaryTag.STABLE],
                invariants=list(survivor.get("structural_form", {}).get("def_fields", [])),
            )
            z3_result = z3_check_phase_boundaries(gate_state)
            if not z3_result.all_satisfied:
                z3_gate_violations += 1
                z3_witness = constraints_to_witness(gate_state, z3_result)
                witness_recorder.record(z3_witness, tags={
                    "batch": batch_id, "phase": "B_ENFORCEMENT",
                    "candidate": o.candidate_id, "gate": "z3_hardness",
                })
        if z3_gate_violations:
            print(f"  ⚠️  Z3 hardness gate: {z3_gate_violations} constraint violations recorded")
        else:
            print(f"  ✅ Z3 hardness gate: all {len(accept)} accepted outcomes pass")

        # Save B state
        kernel.save_state()
        brain.save_state()

        # ─── SIM: T0 Campaign on BATCH-LOCAL accepted survivors only ───
        # Collect exactly the candidate IDs that were accepted in THIS batch.
        batch_accepted_ids = {o.candidate_id for o in accept}

        if accept:
            # Skill selection: Phase 3
            p3_skills = reg.find_relevant(trust_zone="SIM_EVIDENCED", graph_family="runtime", skill_type="verification")
            p3_selected, p3_fallback, p3_adapter, p3_dispatch, p3_reason = resolve_phase_binding(
                reg, p3_skills, preferred=["sim-engine"], runtime_model=runtime_model
            )
            log_skill_invocation(
                batch_id=batch_id, phase="SIM_EVIDENCE",
                trust_zone="SIM_EVIDENCED", graph_family="runtime",
                considered=[s.skill_id for s in p3_skills],
                selected=p3_selected, fallback_used=p3_fallback,
                reason=p3_reason,
                adapter_info=p3_adapter,
            )
            print(f"\n{'─'*60}")
            print(f"PHASE 3: SIM T0_ATOM CAMPAIGN ({len(accept)} batch-local survivors)")
            print(f"  Skill: {p3_selected or 'FALLBACK(direct)'} {'[dispatch]' if not p3_fallback else '[fallback]'} (considered {len(p3_skills)})")
            print(f"{'─'*60}")

            t0_results = {}
            for sid in batch_accepted_ids:
                survivor = kernel.survivor_ledger.get(sid)
                if not survivor:
                    continue
                # Skip probes — they have no structural_form for T0 structural tests
                if survivor.get("class") == "PROBE_HYP" or survivor.get("kind") == "SIM_SPEC":
                    skipped_probes += 1
                    continue

                batch_structural.append(sid)

                # Use run_t0_with_differential to include DIFFERENTIAL tests
                graveyard_items = []
                for g in kernel.graveyard:
                    item = getattr(g, "item", None) or {}
                    graveyard_items.append({
                        "candidate_id": g.candidate_id,
                        "kind": item.get("kind", "GRAVEYARD"),
                        "item": item if item else {"def_fields": []},
                    })
                # Dispatch through registry or fallback
                if p3_dispatch:
                    results = p3_dispatch({
                        "sim": sim, "sid": sid, "survivor": survivor,
                        "graveyard_items": graveyard_items,
                    })
                else:
                    results = sim.run_t0_with_differential(sid, survivor, graveyard_items)
                t0_results[sid] = results

                pass_count = sum(1 for r in results if r.outcome == "PASS")
                fail_count = sum(1 for r in results if r.outcome == "FAIL")
                tier_ok = sim.is_tier_complete(sid, "T0_ATOM")

                print(f"\n  [{sid}] {pass_count} PASS / {fail_count} FAIL → "
                      f"{'T0 COMPLETE ✅' if tier_ok else 'T0 INCOMPLETE ❌'}")

                coverage = sim.compute_tier_coverage(sid, "T0_ATOM")
                for family, cov in coverage.items():
                    status = "✅" if cov["met"] else "❌"
                    print(f"    {status} {family:20s} {cov['passed']}/{cov['required']}")

            tape_writer.write_sim_evidence_pack(batch_id, t0_results)
            print(f"\n  📝 Saved SIM_EVIDENCE_PACK for {batch_id} ({len(batch_structural)} structural survivors)")
            sim.save_state()

            # ─── WITNESS RECORDER: persist all SIM evidence as append-only witnesses ───
            sim_witnesses_recorded = 0
            for sid_key, results in t0_results.items():
                for r in results:
                    from system_v4.skills.runtime_state_kernel import (
                        Witness as KernelWitness, StepEvent,
                    )
                    w_kind = WitnessKind.POSITIVE if r.outcome == "PASS" else WitnessKind.NEGATIVE
                    failure_detail = getattr(r, "reason", "") or getattr(r, "detail", "")
                    test_family = getattr(r, "test_family", "") or getattr(r, "family", "")
                    test_name = getattr(r, "test_name", "") or getattr(r, "sim_id", "")
                    kw = KernelWitness(
                        kind=w_kind,
                        passed=(r.outcome == "PASS"),
                        violations=[failure_detail] if r.outcome != "PASS" and failure_detail else [],
                        touched_boundaries=[BoundaryTag.STABLE if r.outcome == "PASS"
                                            else BoundaryTag.UNSTABLE],
                        trace=[StepEvent(
                            at=utc_iso(), op=f"SIM_T0:{test_family}:{test_name}",
                            before_hash=sid_key[:16], after_hash=sid_key[:16],
                            notes=[f"outcome={r.outcome}"],
                        )],
                    )
                    witness_recorder.record(kw, tags={
                        "batch": batch_id, "phase": "SIM_EVIDENCE",
                        "candidate": sid_key, "test": test_name, "family": test_family,
                    })
                    sim_witnesses_recorded += 1
            wn = witness_recorder.flush()
            print(f"  📝 Witness recorder: {sim_witnesses_recorded} SIM witnesses → {witness_path.name} ({wn} total)")

    # ─── Batch-Local Summary ───
    print(f"\n{'='*60}")
    print(f"BATCH {batch_id} — LOCAL RESULTS")
    print(f"{'='*60}")
    print(f"  Concepts selected:  {len(candidate_ids)}")
    print(f"  Targets extracted:  {len(targets)}")
    print(f"  Alternatives:       {len(alternatives)}")
    print(f"  Accepted:           {len(accept)}")
    print(f"  Parked:             {len(park)}")
    print(f"  Rejected:           {len(reject)}")
    print(f"  SIM structural:     {len(batch_structural)}")
    if skipped_probes:
        print(f"  Probes (skipped):   {skipped_probes}")

    # ─── Global State Summary ───
    print(f"\n{'='*60}")
    print(f"GLOBAL RUNTIME STATE (cumulative)")
    print(f"{'='*60}")
    print(f"  Survivors:    {len(kernel.survivor_ledger)}")
    print(f"  Parked:       {len(kernel.park_set)}")
    print(f"  Graveyard:    {len(kernel.graveyard)}")
    print(f"  Terms:        {len(brain.term_registry)}")
    print(f"  SIM evidence: {len(sim.evidence_log)}")
    print(f"  SIM kills:    {len(sim.kill_log)}")
    print(f"  Witnesses:    {len(sim.witness_log)}")

    # T0 completeness: count only T0-eligible structural survivors
    t0_eligible = [sid for sid in kernel.survivor_ledger
                   if kernel.survivor_ledger[sid].get("class") != "PROBE_HYP"
                   and kernel.survivor_ledger[sid].get("kind") != "SIM_SPEC"]
    t0_complete = sum(1 for sid in t0_eligible
                      if sim.is_tier_complete(sid, "T0_ATOM"))
    print(f"  T0 complete:  {t0_complete}/{len(t0_eligible)} structural survivors")

    # Graveyard detail
    print(f"\n  --- Graveyard (by rejection reason) ---")
    from collections import Counter
    tag_dist = Counter(g.reason_tag for g in kernel.graveyard)
    for tag, count in tag_dist.most_common():
        print(f"    {tag:30s} {count}")

    # Evidence blocks
    if sim.evidence_log:
        print(f"\n  --- First SIM_EVIDENCE v1 Block ---")
        print(f"  {sim.evidence_log[0].to_evidence_block()}")

    # ─── Ratchet Overseer ───
    p5_skills = reg.find_relevant(trust_zone="GRAVEYARD", graph_family="runtime", skill_type="supervisor")
    p5_selected, p5_fallback, p5_adapter, p5_dispatch, p5_reason = resolve_phase_binding(
        reg, p5_skills, preferred=["ratchet-overseer"], runtime_model=runtime_model
    )
    log_skill_invocation(
        batch_id=batch_id, phase="RATCHET_OVERSEER",
        trust_zone="GRAVEYARD", graph_family="runtime",
        considered=[s.skill_id for s in p5_skills],
        selected=p5_selected, fallback_used=p5_fallback,
        reason=p5_reason,
        adapter_info=p5_adapter,
    )
    print(f"\n{'─'*60}")
    print(f"POST-BATCH: RATCHET OVERSEER")
    print(f"  Skill: {p5_selected or 'FALLBACK(direct)'} {'[dispatch]' if not p5_fallback else '[fallback]'} (considered {len(p5_skills)})")
    print(f"{'─'*60}")
    if p5_dispatch:
        overseer_report = p5_dispatch({
            "repo": REPO,
            "batch_id": batch_id,
            "candidate_ids": candidate_ids,
            "targets": targets,
            "alternatives": alternatives,
            "outcomes": outcomes,
            "batch_structural": batch_structural,
            "skipped_probes": skipped_probes,
            "kernel": kernel,
            "sim": sim,
        })
    else:
        from system_v4.skills.ratchet_overseer import build_convergence_report
        overseer_report = build_convergence_report(
            repo=REPO,
            batch_id=batch_id,
            candidate_ids=candidate_ids,
            targets=targets,
            alternatives=alternatives,
            outcomes=outcomes,
            batch_structural=batch_structural,
            skipped_probes=skipped_probes,
            kernel=kernel,
            sim=sim,
        )
    print(f"  State:              {overseer_report['ratchet_state']}")
    print(f"  Action:             {overseer_report['recommended_action']}")
    print(f"  Acceptance trend:   {overseer_report['acceptance_rate_trend']}")

    # ─── Graveyard Lawyer ───
    p6_skills = reg.find_relevant(trust_zone="GRAVEYARD", graph_family="graveyard", skill_type="agent", tags_any=["rescue"])
    p6_selected, p6_fallback, p6_adapter, p6_dispatch, p6_reason = resolve_phase_binding(
        reg, p6_skills, preferred=["graveyard-lawyer"], runtime_model=runtime_model
    )
    log_skill_invocation(
        batch_id=batch_id, phase="GRAVEYARD_REVIEW",
        trust_zone="GRAVEYARD", graph_family="graveyard",
        considered=[s.skill_id for s in p6_skills],
        selected=p6_selected, fallback_used=p6_fallback,
        reason=p6_reason,
        adapter_info=p6_adapter,
    )
    print(f"\n{'─'*60}")
    print(f"POST-BATCH: GRAVEYARD LAWYER")
    print(f"  Skill: {p6_selected or 'FALLBACK(direct)'} {'[dispatch]' if not p6_fallback else '[fallback]'} (considered {len(p6_skills)})")
    print(f"{'─'*60}")
    if p6_dispatch:
        graveyard_report = p6_dispatch({
            "repo": REPO,
            "batch_id": batch_id,
            "kernel": kernel,
            "brain": brain,
        })
    else:
        from system_v4.skills.graveyard_lawyer import build_rescue_report
        graveyard_report = build_rescue_report(
            repo=REPO,
            batch_id=batch_id,
            kernel=kernel,
            brain=brain,
        )
    print(f"  Reviewed:           {graveyard_report['reviewed_count']}")
    print(f"  Reopen proposals:   {graveyard_report['reopen_count']}")
    print(f"  Reclassify proposals:{graveyard_report['reclassify_count']}")

    # ─── Runtime → Graph Bridge ───
    # Skill selection: Phase 4
    p4_skills = reg.find_relevant(trust_zone="GRAVEYARD", graph_family="runtime", skill_type="bridge")
    p4_selected, p4_fallback, p4_adapter, p4_dispatch, p4_reason = resolve_phase_binding(
        reg, p4_skills, preferred=["runtime-graph-bridge"], runtime_model=runtime_model
    )
    log_skill_invocation(
        batch_id=batch_id, phase="GRAPH_BRIDGE",
        trust_zone="GRAVEYARD", graph_family="runtime",
        considered=[s.skill_id for s in p4_skills],
        selected=p4_selected, fallback_used=p4_fallback,
        reason=p4_reason,
        adapter_info=p4_adapter,
    )
    print(f"\n{'─'*60}")
    print(f"PHASE 4: RUNTIME → GRAPH BRIDGE")
    print(f"  Skill: {p4_selected or 'FALLBACK(direct)'} {'[dispatch]' if not p4_fallback else '[fallback]'} (considered {len(p4_skills)})")
    print(f"{'─'*60}")
    witness_recorder.flush()
    if p4_dispatch:
        bridge_stats = p4_dispatch({"repo": REPO})
    else:
        from system_v4.skills.runtime_graph_bridge import bridge_runtime_to_graph
        bridge_stats = bridge_runtime_to_graph(REPO, clean=True)
    print(f"  Nodes added:        {bridge_stats['nodes_added']}")
    print(f"  Edges added:        {bridge_stats['edges_added']}")
    print(f"  CANON→SOURCE_CLAIM: {bridge_stats['canon_fixed']}")
    print(f"  Total graph nodes:  {bridge_stats['total_nodes']}")
    print(f"  Total graph edges:  {bridge_stats['total_edges']}")

    # ─── BOUNDED IMPROVE: A2 refinement loop on graph state ───
    print(f"\n{'─'*60}")
    print(f"POST-BATCH: BOUNDED IMPROVE (A2 refinement)")
    print(f"{'─'*60}")

    # Build an A2 RuntimeState from graph stats
    a2_state = RuntimeState(
        region="A2_REFINEMENT",
        phase_index=0,
        phase_period=8,
        loop_scale=__import__('system_v4.skills.runtime_state_kernel',
                              fromlist=['LoopScale']).LoopScale.MESO,
        boundaries=[BoundaryTag.STABLE],
        invariants=["graph_connected", "edge_density_nonzero"],
        dof={"nodes": bridge_stats.get("total_nodes", 0),
             "edges": bridge_stats.get("total_edges", 0)},
        context={"batch_id": batch_id,
                 "survivors": len(kernel.survivor_ledger),
                 "graveyard": len(kernel.graveyard)},
    )

    # Mutate: simulate adding one more round of refinement edges
    def a2_mutate(s: RuntimeState) -> RuntimeState:
        d = s.__dict__.copy()
        d["dof"] = {**s.dof, "edges": s.dof.get("edges", 0) + 50}
        d["phase_index"] = (s.phase_index + 1) % s.phase_period
        return RuntimeState(**d)

    # Eval: prefer higher edge density per node
    def a2_eval(s: RuntimeState) -> float:
        nodes = s.dof.get("nodes", 1)
        edges = s.dof.get("edges", 0)
        return edges / max(nodes, 1)

    improved_state, improve_result = bounded_improve(
        a2_state, a2_mutate, a2_eval, rounds=3,
    )
    print(f"  Rounds:    {improve_result.rounds}")
    print(f"  Improved:  {improve_result.improved}")
    print(f"  Score:     {a2_eval(a2_state):.2f} → {improve_result.final_score:.2f}")
    for d in improve_result.decisions:
        marker = "✅" if d.kept else "⏭"
        print(f"    {marker} round {d.round_index}: {d.score_before:.2f} → {d.score_after:.2f} ({d.rationale})")

    # Record the improvement outcome
    from system_v4.skills.runtime_state_kernel import Witness as KWitness
    improve_witness = KWitness(
        kind=WitnessKind.POSITIVE if improve_result.improved else WitnessKind.NEGATIVE,
        passed=improve_result.improved,
        violations=[] if improve_result.improved else ["no_improvement"],
        touched_boundaries=[BoundaryTag.FRONTIER if improve_result.improved
                            else BoundaryTag.STABLE],
        trace=[make_step_event(
            "bounded_improve", a2_state, improved_state,
            notes=[f"rounds={improve_result.rounds}",
                   f"score={improve_result.final_score:.2f}"],
        )],
    )
    witness_recorder.record(improve_witness, tags={
        "batch": batch_id, "phase": "A2_REFINEMENT",
        "operator": "bounded-improve",
    })
    # ─── AUTORESEARCH: MOTIF SEARCH (A2 exploration) ───
    print(f"\n{'─'*60}")
    print(f"POST-BATCH: AUTORESEARCH (Motif Search)")
    print(f"{'─'*60}")
    def ar_generator(s: RuntimeState) -> list[RuntimeState]:
        variants = []
        base_edges = s.dof.get("edges", 0)
        variants.append(RuntimeState(region=s.region+":motif_A", dof={"nodes": s.dof.get("nodes", 1), "edges": base_edges + 10}))
        variants.append(RuntimeState(region=s.region+":motif_B", dof={"nodes": s.dof.get("nodes", 1), "edges": max(0, base_edges - 5)}))
        return variants
    def ar_eval(s: RuntimeState) -> float:
        return s.dof.get("edges", 0) / max(s.dof.get("nodes", 1), 1)
    ar_skills = reg.find_relevant(trust_zone="A2_MID_REFINEMENT", graph_family="runtime", tags_any=["autoresearch"])
    ar_selected, ar_fallback, ar_adapter, ar_dispatch, ar_reason = resolve_phase_binding(
        reg, ar_skills, preferred=["autoresearch-operator"], runtime_model=runtime_model
    )
    if ar_dispatch:
        log_skill_invocation(
            batch_id=batch_id, phase="AUTORESEARCH",
            trust_zone="A2_MID_REFINEMENT", graph_family="runtime",
            considered=[s.skill_id for s in ar_skills],
            selected=ar_selected, fallback_used=ar_fallback,
            reason=ar_reason, adapter_info=ar_adapter,
        )
        ar_result = ar_dispatch({
            "state": improved_state,
            "generator": ar_generator,
            "evaluator": ar_eval,
            "max_breadth": 2,
            "max_depth": 2,
            "recorder": witness_recorder,
            "witness_tags": {"batch": batch_id, "phase": "AUTORESEARCH"}
        })
        ar_stats = ar_result["stats"]
        print(f"  Best motif score: {ar_stats['best_score']:.2f}")
        for t in ar_stats["trace"][-3:]:
            print(f"    {t}")
    rd_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["research-deliberation"],
    )
    rd_selected, rd_fallback, rd_adapter, rd_dispatch, rd_reason = resolve_phase_binding(
        reg,
        rd_skills,
        preferred=["a2-research-deliberation-operator"],
        runtime_model=runtime_model,
    )
    if rd_dispatch:
        log_skill_invocation(
            batch_id=batch_id,
            phase="RESEARCH_DELIBERATION_CLUSTER",
            trust_zone="A2_MID_REFINEMENT",
            graph_family="runtime",
            considered=[s.skill_id for s in rd_skills],
            selected=rd_selected,
            fallback_used=rd_fallback,
            reason=rd_reason,
            adapter_info=rd_adapter,
        )
        print(f"\n{'─'*60}")
        print("POST-BATCH: RESEARCH / DELIBERATION CLUSTER")
        print(f"  Skill: {rd_selected or 'FALLBACK'} {'[dispatch]' if not rd_fallback else '[fallback]'}")
        print(f"{'─'*60}")
        rd_result = rd_dispatch(
            {
                "question": "Evaluate current runtime motifs for the active batch",
                "state": improved_state,
                "generator": ar_generator,
                "evaluator": ar_eval,
                "max_breadth": 2,
                "max_depth": 2,
                "consensus_threshold": 0.34,
                "random_seed": 42,
                "recorder": witness_recorder,
                "witness_tags": {"batch": batch_id, "phase": "RESEARCH_DELIBERATION"},
            }
        )
        rd_execution = rd_result.get("execution", {})
        print(f"  Route:     {rd_execution.get('route', 'unknown')}")
        print(
            f"  Accepted:  {rd_execution.get('accepted_count', 0)}/"
            f"{rd_execution.get('candidate_count', 0)}"
        )
        if rd_execution.get("accepted_regions"):
            print(f"  Regions:   {', '.join(rd_execution['accepted_regions'])}")
    wn_final = witness_recorder.flush()
    sync_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="runtime",
        tags_any=["witness-sync"],
    )
    sync_selected, sync_fallback, sync_adapter, sync_dispatch, sync_reason = resolve_phase_binding(
        reg, sync_skills, preferred=["witness-evermem-sync"], runtime_model=runtime_model
    )
    if sync_dispatch:
        log_skill_invocation(
            batch_id=batch_id,
            phase="WITNESS_EVERMEM_SYNC",
            trust_zone="A2_LOW_CONTROL",
            graph_family="runtime",
            considered=[s.skill_id for s in sync_skills],
            selected=sync_selected,
            fallback_used=sync_fallback,
            reason=sync_reason,
            adapter_info=sync_adapter,
        )
        sync_result = sync_dispatch(
            {
                "witness_path": str(witness_path),
                "state_path": str(evermem_sync_state_path),
                "report_json_path": str(evermem_sync_report_json),
                "report_md_path": str(evermem_sync_report_md),
                "evermem_url": os.environ.get("RATCHET_EVERMEM_URL", "http://localhost:1995/api/v1"),
            }
        )
        print(
            f"  EverMem witness sync: {sync_result.get('synced', 0)} entries "
            f"(status={sync_result.get('status', 'unknown')})"
        )
    refresh_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["brain-refresh"],
    )
    refresh_selected, refresh_fallback, refresh_adapter, refresh_dispatch, refresh_reason = (
        resolve_phase_binding(
            reg,
            refresh_skills,
            preferred=["a2-brain-surface-refresher"],
            runtime_model=runtime_model,
        )
    )
    if refresh_dispatch:
        log_skill_invocation(
            batch_id=batch_id,
            phase="A2_BRAIN_SURFACE_REFRESH",
            trust_zone="A2_MID_REFINEMENT",
            graph_family="runtime",
            considered=[s.skill_id for s in refresh_skills],
            selected=refresh_selected,
            fallback_used=refresh_fallback,
            reason=refresh_reason,
            adapter_info=refresh_adapter,
        )
        print(f"\n{'─'*60}")
        print("POST-BATCH: A2 BRAIN SURFACE REFRESH")
        print(f"  Skill: {refresh_selected or 'FALLBACK'} {'[dispatch]' if not refresh_fallback else '[fallback]'}")
        print(f"{'─'*60}")
        refresh_result = refresh_dispatch(
            {
                "repo": REPO,
                "task_signal": "post_batch_truth_maintenance",
                "pending_a1_work": procedure["a1_queue"].get("queue_status", ""),
                "new_run_evidence": [
                    str(evermem_sync_report_json),
                    str(evermem_sync_report_md),
                    str(witness_path),
                ],
                "report_path": str(a2_brain_refresh_report_json),
                "markdown_path": str(a2_brain_refresh_report_md),
                "packet_path": str(a2_brain_refresh_packet_json),
                "record_runtime_context": True,
            }
        )
        print(
            f"  A2 brain refresh: status={refresh_result.get('status', 'unknown')} "
            f"refresh_required={refresh_result.get('refresh_required', False)} "
            f"stale={refresh_result.get('surface_classification_summary', {}).get('stale_surface_count', 0)} "
            f"missing={refresh_result.get('surface_classification_summary', {}).get('missing_surface_count', 0)}"
        )
    ledger_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="runtime",
        tags_any=["session-ledger"],
    )
    ledger_selected, ledger_fallback, ledger_adapter, ledger_dispatch, ledger_reason = resolve_phase_binding(
        reg,
        ledger_skills,
        preferred=["outer-session-ledger"],
        runtime_model=runtime_model,
    )
    if ledger_dispatch:
        log_skill_invocation(
            batch_id=batch_id,
            phase="OUTER_SESSION_LEDGER",
            trust_zone="A2_LOW_CONTROL",
            graph_family="runtime",
            considered=[s.skill_id for s in ledger_skills],
            selected=ledger_selected,
            fallback_used=ledger_fallback,
            reason=ledger_reason,
            adapter_info=ledger_adapter,
        )
        print(f"\n{'─'*60}")
        print("POST-BATCH: OUTER SESSION LEDGER")
        print(f"  Skill: {ledger_selected or 'FALLBACK'} {'[dispatch]' if not ledger_fallback else '[fallback]'}")
        print(f"{'─'*60}")
        ledger_result = ledger_dispatch(
            {
                "repo": REPO,
                "host_kind": "ratchet_prompt_stack",
                "state_path": str(outer_session_ledger_state_json),
                "events_path": str(outer_session_ledger_events_jsonl),
                "report_json_path": str(outer_session_ledger_report_json),
                "report_md_path": str(outer_session_ledger_report_md),
            }
        )
        print(
            f"  Session ledger: status={ledger_result.get('status', 'unknown')} "
            f"sessions={ledger_result.get('sessions_found', 0)}"
        )
    print(f"  📝 Witness corpus: {wn_final} total witnesses")

    print(f"\nState saved to:")
    print(f"  {brain.brain_state_path}")
    print(f"  {kernel.state_path}")
    print(f"  {sim.state_path}")
    print(f"  {witness_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
