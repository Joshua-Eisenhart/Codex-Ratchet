import hashlib
import json
from dataclasses import dataclass

from state import KernelState


TIER_ORDER = {
    "T0_ATOM": 0,
    "T1_COMPOUND": 1,
    "T2_OPERATOR": 2,
    "T3_STRUCTURE": 3,
    "T4_SYSTEM_SEGMENT": 4,
    "T5_ENGINE": 5,
    "T6_WHOLE_SYSTEM": 6,
}

REQUIRED_FAMILIES = {"BASELINE", "BOUNDARY_SWEEP", "PERTURBATION", "ADVERSARIAL_NEG", "COMPOSITION_STRESS"}
MASTER_SIM_ID = "SIM_MASTER_T6"
MASTER_NEG_SIM_ID = "SIM_MASTER_T6_NEG"


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _deterministic_hash_dict(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(encoded)


@dataclass(frozen=True)
class SimTask:
    sim_id: str
    spec_id: str
    evidence_token: str
    tier: str
    family: str
    target_class: str
    negative_class: str
    depends_on: tuple[str, ...]


class SimEngine:
    def __init__(self):
        self.code_hash_prefix = _sha256_bytes(b"bootpack_b_kernel_v1_sim_engine")

    def run_task(self, state: KernelState, task: SimTask) -> str:
        input_hash = state.hash()
        payload = {
            "sim_id": task.sim_id,
            "spec_id": task.spec_id,
            "tier": task.tier,
            "family": task.family,
            "target_class": task.target_class,
            "negative_class": task.negative_class,
            "depends_on": list(task.depends_on),
            "state_hash": input_hash,
        }
        output_hash = _deterministic_hash_dict(payload)
        code_hash = _sha256_bytes((self.code_hash_prefix + task.sim_id).encode("utf-8"))
        run_manifest_payload = {
            "manifest_schema": "SIM_RUN_MANIFEST_v1",
            "sim_engine_id": "bootpack_b_kernel_v1",
            "code_hash_sha256": code_hash,
            "input_hash_sha256": input_hash,
            "task": payload,
        }
        run_manifest_hash = _deterministic_hash_dict(run_manifest_payload)
        evidence_lines = [
            "BEGIN SIM_EVIDENCE v1",
            f"SIM_ID: {task.spec_id}",
            f"CODE_HASH_SHA256: {code_hash}",
            f"INPUT_HASH_SHA256: {input_hash}",
            f"OUTPUT_HASH_SHA256: {output_hash}",
            f"RUN_MANIFEST_SHA256: {run_manifest_hash}",
            f"METRIC: tier={task.tier}",
            f"METRIC: family={task.family}",
            f"METRIC: target_class={task.target_class}",
            f"METRIC: negative_class={task.negative_class or 'NONE'}",
            f"EVIDENCE_SIGNAL {task.spec_id} CORR {task.evidence_token}",
        ]
        if task.negative_class:
            evidence_lines.append(f"KILL_SIGNAL {task.spec_id} CORR NEG_{task.negative_class}")
        evidence_lines.append("END SIM_EVIDENCE v1")
        evidence_lines.append("")
        state.sim_results.setdefault(task.sim_id, []).append(
            {
                "spec_id": task.spec_id,
                "tier": task.tier,
                "family": task.family,
                "target_class": task.target_class,
                "negative_class": task.negative_class,
                "depends_on": list(task.depends_on),
                "code_hash": code_hash,
                "input_hash": input_hash,
                "output_hash": output_hash,
                "run_manifest_hash": run_manifest_hash,
            }
        )
        return "\n".join(evidence_lines)

    def evaluate_promotion(self, state: KernelState, sim_id: str, graveyard_by_target_class: dict[str, int]) -> dict:
        spec = state.sim_registry.get(sim_id)
        if not spec:
            return {"status": "PROMOTE_FAIL", "reason_tags": ["MISSING_SIM_SPEC"]}

        target_class = spec.get("target_class", "")
        tier = spec.get("tier", "T0_ATOM")
        dependencies = spec.get("depends_on", [])

        blockers: list[str] = []

        for dep in dependencies:
            dep_spec = state.sim_registry.get(dep)
            if not dep_spec:
                blockers.append("G1_DEPENDENCY_COVERAGE")
                continue
            dep_spec_id = dep_spec.get("spec_id", "")
            if dep_spec_id and dep_spec_id in state.evidence_pending:
                blockers.append("G1_DEPENDENCY_COVERAGE")

        target_results = [item for _, result_list in state.sim_results.items() for item in result_list if item.get("target_class") == target_class]
        has_negative = any(item.get("negative_class") for item in target_results)
        if not has_negative:
            blockers.append("G2_NEGATIVE_COVERAGE")

        if graveyard_by_target_class.get(target_class, 0) <= 0:
            blockers.append("G3_GRAVEYARD_COVERAGE")

        run_hashes = sorted({item.get("output_hash", "") for item in state.sim_results.get(sim_id, [])})
        if len(run_hashes) > 1:
            blockers.append("G4_REPRODUCIBILITY")

        if spec.get("bypass", False):
            blockers.append("G5_NO_BYPASS")

        families = {item.get("family", "") for item in target_results}
        if not REQUIRED_FAMILIES.issubset(families):
            blockers.append("G6_STRESS_COVERAGE")

        unique_blockers = sorted(set(blockers))
        if unique_blockers:
            state.sim_promotion_status[sim_id] = "PARKED"
            return {"status": "PROMOTE_FAIL", "reason_tags": unique_blockers}

        state.sim_promotion_status[sim_id] = "ACTIVE"
        return {"status": "PROMOTE_PASS", "reason_tags": []}

    def coverage_report(self, state: KernelState, graveyard_by_target_class: dict[str, int]) -> dict:
        tier_rows = []
        promotion_counts = {tier: {"pass": 0, "fail": 0} for tier in sorted(TIER_ORDER.keys(), key=lambda key: TIER_ORDER[key])}
        unresolved: list[dict] = []

        for sim_id, spec in sorted(state.sim_registry.items()):
            tier = spec.get("tier", "T0_ATOM")
            outcome = self.evaluate_promotion(state, sim_id, graveyard_by_target_class)
            if outcome["status"] == "PROMOTE_PASS":
                promotion_counts[tier]["pass"] += 1
            else:
                promotion_counts[tier]["fail"] += 1
                unresolved.append({"sim_id": sim_id, "tier": tier, "blockers": outcome["reason_tags"]})
            tier_rows.append(
                {
                    "sim_id": sim_id,
                    "tier": tier,
                    "target_class": spec.get("target_class", ""),
                    "promotion_status": state.sim_promotion_status.get(sim_id, "NOT_READY"),
                }
            )

        master_status = state.sim_promotion_status.get(MASTER_SIM_ID, "NOT_READY")
        if MASTER_SIM_ID in state.sim_registry:
            master_outcome = self.evaluate_promotion(state, MASTER_SIM_ID, graveyard_by_target_class)
            master_status = "ACTIVE" if master_outcome["status"] == "PROMOTE_PASS" else "PARKED"
            state.sim_promotion_status[MASTER_SIM_ID] = master_status
            if MASTER_NEG_SIM_ID not in state.sim_registry:
                master_status = "PARKED"
                unresolved.append({"sim_id": MASTER_SIM_ID, "tier": "T6_WHOLE_SYSTEM", "blockers": ["MISSING_MASTER_NEGATIVE_SIM"]})

        return {
            "tier_coverage_table": tier_rows,
            "promotion_counts_by_tier": promotion_counts,
            "master_sim_status": master_status,
            "unresolved_promotion_blockers": unresolved,
        }
