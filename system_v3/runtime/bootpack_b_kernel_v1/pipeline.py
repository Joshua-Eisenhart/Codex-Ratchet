from gateway import BootpackBGateway
from kernel import BootpackBKernel
from sim_dispatcher import A0SimDispatcher
from sim_engine import SimEngine
from state import KernelState


class A0BSimPipeline:
    def __init__(self):
        self.kernel = BootpackBKernel()
        self.gateway = BootpackBGateway(kernel=self.kernel)
        self.dispatcher = A0SimDispatcher()
        self.sim_engine = SimEngine()

    def handle_message(self, message_text: str, state: KernelState, batch_id: str = "") -> dict:
        return self.gateway.handle_message(message_text, state, batch_id=batch_id)

    def ingest_export_block(self, export_block_text: str, state: KernelState, batch_id: str = "") -> dict:
        return self.kernel.evaluate_export_block(export_block_text, state, batch_id=batch_id)

    def run_sim_cycle(self, state: KernelState, batch_id: str = "") -> dict:
        plan = self.dispatcher.build_campaign_plan(state)
        tasks = plan.tasks
        evidence_blocks = [self.sim_engine.run_task(state, task) for task in tasks]
        satisfied = []
        for index, evidence in enumerate(evidence_blocks):
            result = self.kernel.ingest_sim_evidence_pack(evidence, state, batch_id=f"{batch_id}_SIM_{index + 1:04d}")
            satisfied.extend(result.get("satisfied", []))
        return {
            "planned_task_count": len(tasks),
            "planned_sim_ids": [task.sim_id for task in tasks],
            "evidence_block_count": len(evidence_blocks),
            "satisfied_spec_ids": sorted(set(satisfied)),
            "stages_seen": list(plan.stages_seen),
            "suite_modes_seen": list(plan.suite_modes_seen),
            "blocked_stage_ids": list(plan.blocked_stage_ids),
        }
