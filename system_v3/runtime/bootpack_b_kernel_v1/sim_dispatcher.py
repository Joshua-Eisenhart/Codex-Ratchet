from dataclasses import dataclass

from sim_engine import SimTask, TIER_ORDER
from state import KernelState

SUITE_KIND_ORDER = {
    "micro_suite": 0,
    "mid_suite": 1,
    "segment_suite": 2,
    "engine_suite": 3,
    "mega_suite": 4,
    "failure_isolation": 5,
    "graveyard_rescue": 6,
    "replay_from_tape": 7,
}


@dataclass(frozen=True)
class DispatchItem:
    blocked: int
    tier_rank: int
    stage_rank: int
    suite_rank: int
    stage_id: str
    stage_suite_kind: str
    sim_id: str
    task: SimTask


@dataclass
class DispatchPlan:
    tasks: list[SimTask]
    stages_seen: tuple[str, ...]
    suite_modes_seen: tuple[str, ...]
    blocked_stage_ids: tuple[str, ...]
    blocked_suite_modes: tuple[str, ...]
    stage_task_counts: dict[str, int]
    suite_mode_task_counts: dict[str, int]


class A0SimDispatcher:
    def build_campaign_plan(self, state: KernelState) -> DispatchPlan:
        planned: list[DispatchItem] = []
        stage_pending: dict[str, int] = {}
        stage_depends_on: dict[str, tuple[str, ...]] = {}
        stage_rank_cache: dict[str, int] = {}
        stage_tier_rank: dict[str, int] = {}
        stage_suite_kind: dict[str, str] = {}

        for spec_id in sorted(state.evidence_pending.keys()):
            spec_meta = state.spec_meta.get(spec_id, {})
            if spec_meta.get("kind") != "SIM_SPEC":
                continue
            stage_id = str(spec_meta.get("stage_id", "")).strip()
            if stage_id:
                stage_pending[stage_id] = int(stage_pending.get(stage_id, 0)) + 1
                stage_depends_on[stage_id] = tuple(sorted(str(x).strip() for x in spec_meta.get("stage_depends_on", []) if str(x).strip()))
                stage_tier_rank[stage_id] = min(
                    TIER_ORDER.get(str(spec_meta.get("tier", "T0_ATOM")), 0),
                    stage_tier_rank.get(stage_id, 99),
                )
                suite_kind = str(spec_meta.get("stage_suite_kind", "")).strip()
                if suite_kind:
                    stage_suite_kind[stage_id] = suite_kind

        def _stage_rank(stage_id: str, visiting: set[str] | None = None) -> int:
            if not stage_id:
                return 0
            if stage_id in stage_rank_cache:
                return stage_rank_cache[stage_id]
            visiting = visiting or set()
            if stage_id in visiting:
                return 0
            visiting.add(stage_id)
            deps = stage_depends_on.get(stage_id, ())
            rank = 1 + max((_stage_rank(dep, visiting) for dep in deps), default=0)
            visiting.remove(stage_id)
            stage_rank_cache[stage_id] = rank
            return rank

        for spec_id in sorted(state.evidence_pending.keys()):
            spec_meta = state.spec_meta.get(spec_id, {})
            if spec_meta.get("kind") != "SIM_SPEC":
                continue
            sim_id = str(spec_meta.get("sim_id", spec_id))
            evidence_token = str(spec_meta.get("evidence_token", ""))
            tier = str(spec_meta.get("tier", "T0_ATOM"))
            family = str(spec_meta.get("family", "BASELINE"))
            target_class = str(spec_meta.get("target_class", spec_id))
            negative_class = str(spec_meta.get("negative_class", ""))
            depends_on = tuple(sorted(spec_meta.get("depends_on", [])))
            stage_id = str(spec_meta.get("stage_id", "")).strip()
            suite_kind = str(spec_meta.get("stage_suite_kind", "")).strip()
            tier_rank = TIER_ORDER.get(tier, 0)
            stage_rank = _stage_rank(stage_id)
            blocked = 0
            if stage_id:
                if any(stage_pending.get(dep_stage, 0) > 0 for dep_stage in stage_depends_on.get(stage_id, ())):
                    blocked = 1
                elif suite_kind in {"engine_suite", "mega_suite"}:
                    lower_stage_open = any(
                        other_stage != stage_id
                        and pending_count > 0
                        and stage_tier_rank.get(other_stage, 0) < tier_rank
                        for other_stage, pending_count in stage_pending.items()
                    )
                    if lower_stage_open:
                        blocked = 1
            task = SimTask(
                sim_id=sim_id,
                spec_id=spec_id,
                evidence_token=evidence_token,
                tier=tier,
                family=family,
                target_class=target_class,
                negative_class=negative_class,
                depends_on=depends_on,
                stage_id=stage_id,
                stage_suite_kind=suite_kind,
                stage_depends_on=tuple(stage_depends_on.get(stage_id, ())),
            )
            planned.append(
                DispatchItem(
                    blocked=blocked,
                    tier_rank=tier_rank,
                    stage_rank=stage_rank,
                    suite_rank=SUITE_KIND_ORDER.get(suite_kind, 99),
                    stage_id=stage_id,
                    stage_suite_kind=suite_kind,
                    sim_id=sim_id,
                    task=task,
                )
            )
        ready = [item for item in planned if item.blocked == 0]
        active = ready if ready else planned
        active.sort(key=lambda item: (item.blocked, item.stage_rank, item.tier_rank, item.suite_rank, item.sim_id, item.task.spec_id))
        stage_task_counts: dict[str, int] = {}
        suite_mode_task_counts: dict[str, int] = {}
        for item in active:
            if item.stage_id:
                stage_task_counts[item.stage_id] = int(stage_task_counts.get(item.stage_id, 0)) + 1
            if item.stage_suite_kind:
                suite_mode_task_counts[item.stage_suite_kind] = int(suite_mode_task_counts.get(item.stage_suite_kind, 0)) + 1
        stages_seen = tuple(
            item.stage_id
            for item in sorted(active, key=lambda row: (row.stage_rank, row.tier_rank, row.stage_id, row.sim_id))
            if item.stage_id
        )
        suite_modes_seen = tuple(
            kind
            for kind, _ in sorted(suite_mode_task_counts.items(), key=lambda row: (SUITE_KIND_ORDER.get(row[0], 99), row[0]))
        )
        blocked_stage_ids = tuple(sorted({item.stage_id for item in planned if item.blocked and item.stage_id}))
        blocked_suite_modes = tuple(
            kind
            for kind in sorted(
                {item.stage_suite_kind for item in planned if item.blocked and item.stage_suite_kind},
                key=lambda row: (SUITE_KIND_ORDER.get(row, 99), row),
            )
        )
        return DispatchPlan(
            tasks=[item.task for item in active],
            stages_seen=stages_seen,
            suite_modes_seen=suite_modes_seen,
            blocked_stage_ids=blocked_stage_ids,
            blocked_suite_modes=blocked_suite_modes,
            stage_task_counts=stage_task_counts,
            suite_mode_task_counts=suite_mode_task_counts,
        )

    def plan_tasks(self, state: KernelState) -> list[SimTask]:
        return self.build_campaign_plan(state).tasks
