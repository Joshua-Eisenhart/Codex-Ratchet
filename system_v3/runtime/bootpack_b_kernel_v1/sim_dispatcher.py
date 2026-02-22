from dataclasses import dataclass

from sim_engine import SimTask, TIER_ORDER
from state import KernelState


@dataclass(frozen=True)
class DispatchItem:
    tier_rank: int
    sim_id: str
    task: SimTask


class A0SimDispatcher:
    def plan_tasks(self, state: KernelState) -> list[SimTask]:
        planned: list[DispatchItem] = []
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
            task = SimTask(
                sim_id=sim_id,
                spec_id=spec_id,
                evidence_token=evidence_token,
                tier=tier,
                family=family,
                target_class=target_class,
                negative_class=negative_class,
                depends_on=depends_on,
            )
            planned.append(DispatchItem(tier_rank=TIER_ORDER.get(tier, 0), sim_id=sim_id, task=task))
        planned.sort(key=lambda item: (item.tier_rank, item.sim_id, item.task.spec_id))
        return [item.task for item in planned]

