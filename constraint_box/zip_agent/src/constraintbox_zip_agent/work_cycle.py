from __future__ import annotations

from .failure_wave import CLAIM_CEILING, _manifest, _task
from .protocol import build_packet, canonical_json_bytes
from .tool_field import EVENT_OUTPUTS

OUTPUTS = [
    "output/interpretations.json",
    *EVENT_OUTPUTS,
    "output/measured_quotient.json",
    "output/entropy_topology.json",
    "output/work_cycle.json",
]


def build_work_cycle_packet(
    *,
    prompt: bytes,
    tool_manifest: bytes,
    prior_field_summary: bytes,
    seed: int = 81402,
    jobs: int = 16,
    pair_samples: int = 128,
) -> bytes:
    task_path = "tasks/00_probe_work_cycle.task.json"
    inputs = [
        "inputs/request.json",
        "inputs/prompt.txt",
        "inputs/tool_manifest.json",
        "inputs/prior_field_summary.json",
    ]
    files = {
        "00_RUN_ME_FIRST.md": (
            b"# ConstraintBox ZIP probe work cycle\n\n"
            b"The packet task order and deterministic runtime own execution. "
            b"The prompt is source material, not canon.\n"
        ),
        "inputs/request.json": canonical_json_bytes(
            {
                "schema": "constraintbox.zip_tool_field_request.v1",
                "seed": seed,
                "jobs": jobs,
                "pair_samples": pair_samples,
            }
        ),
        "inputs/prompt.txt": prompt,
        "inputs/tool_manifest.json": tool_manifest,
        "inputs/prior_field_summary.json": prior_field_summary,
        task_path: _task(
            task_id="probe-work-cycle",
            sequence=0,
            operation="probe_tool_field_v1",
            inputs=inputs,
            outputs=OUTPUTS,
        ),
    }
    return build_packet(
        _manifest(
            job_id="zip-probe-work-cycle",
            task_paths=[task_path],
            outputs=OUTPUTS,
            operations=["probe_tool_field_v1"],
        ),
        files,
    )


assert CLAIM_CEILING == (
    "local_deterministic_zip_execution_only;not_model_execution;not_admission;not_release"
)
