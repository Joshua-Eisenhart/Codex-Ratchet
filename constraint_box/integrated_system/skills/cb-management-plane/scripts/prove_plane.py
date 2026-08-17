#!/usr/bin/env python3
"""Prove the management plane without launching models.

Writes constraintbox.wave-execution.v1 with model_free True and route_truth NOT_FULL.
Does not activate a WaveRecipe. Does not claim Heavy WAVE_EXECUTION_VERIFIED.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))
BOX = Path(os.environ.get("CB_BOX_ROOT", Path(__file__).resolve().parents[4]))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plane = _load("plane", SKILLS / "cb-management-plane/scripts/plane.py")
ledger = _load("ledger", SKILLS / "cb-context-ledger/scripts/ledger.py")
project = _load("project", SKILLS / "cb-context-projector/scripts/project.py")
delta = _load("delta", SKILLS / "cb-context-delta-admission/scripts/admit_delta.py")
recency = _load("recency", SKILLS / "cb-recency-bias-auditor/scripts/audit_recency.py")
omission = _load("omission", SKILLS / "cb-context-omission-auditor/scripts/audit_omission.py")
epoch = _load("epoch", SKILLS / "cb-context-epoch-compiler/scripts/compile_epoch.py")
memory = _load("memory", SKILLS / "cb-branch-failure-memory/scripts/remember.py")
bind = _load("bind", SKILLS / "cb-capability-binder/scripts/bind.py")
admit = _load("admit", SKILLS / "cb-wave-admission-gate/scripts/admit.py")
controller = _load("controller", SKILLS / "cb-wave-run-controller/scripts/run_controller.py")
watch = _load("watch", SKILLS / "cb-wave-watchdog/scripts/watch.py")
collapse = _load("collapse", SKILLS / "cb-council-collapse-auditor/scripts/audit_collapse.py")
output = _load("output", SKILLS / "cb-output-compiler/scripts/compile_output.py")
heavy = _load("heavy", SKILLS / "cb-wave-author/scripts/verify_wave_execution.py")


NEGATIVES = {
    "positive": "all context children complete on honest inputs",
    "reason_specific_negative": "shared source roots refuse",
    "boundary": "proposal without head holds",
    "replay": "append never rewrites",
    "severance": "route-truth refuses fake FULL",
    "cancellation": "controller CANCELLED when cancelled=true",
    "receipt_tamper": "output compiler marks fake_full",
}


def prove(root: Path) -> dict:
    out_dir = root / "receipts" / "management_plane"
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = root / "receipts" / "context_ledger" / "ledger.jsonl"
    memory_path = root / "receipts" / "branch_failure" / "memory.jsonl"

    owner = ledger.append(ledger_path, {"kind": "owner_statement", "text": "Management plane before multiplying councils."})
    card = ledger.append(ledger_path, {"kind": "object_card", "text": "finite Light seed F and honest operation names"})
    admitted_delta = delta.admit({"class": "observation", "text": "sealed v3 waves_launched false"})
    kernel = {
        "object_hash": plane.digest_obj("finite Light seed F"),
        "hard_constraints": ["no rebase", "no llm vote", "promotion_allowed false"],
        "claim_ceiling": "management plane exists; model-free; not FULL; not Heavy verified",
    }
    lanes = [
        {"id": "authority", "role": "authority", "source_roots": [str(ledger_path)]},
        {"id": "evidence", "role": "evidence", "source_roots": [str(root / "receipts/wave_self_loop/latest.json")]},
    ]
    projection = project.project(kernel, lanes)
    recency_receipt = recency.audit({"decision": "HOLD_UNACTIVATED"}, {"decision": "HOLD_UNACTIVATED"})
    omission_receipt = omission.audit(
        {
            "original_object": "finite Light seed F",
            "durable_constraints": "no rebase",
            "historical_failures": "sealed seed-check dirties receipts/",
            "unresolved_contradictions": "READ_THIS_FIRST still says v2",
            "current_evidence": "this-session verify waves_launched false",
            "rival_branches": "keep authored waves as specs only",
            "negative_results": "Heavy execution verifier requires provider calls",
        }
    )
    epoch_receipt = epoch.compile_epoch(None, [admitted_delta], genesis=True)
    remembered = memory.remember(
        memory_path,
        {"kind": "failed_candidate", "id": "activate-without-admission", "why": "skills are not the gate"},
    )
    resurrection = memory.resurrect(memory_path, {"id": "activate-without-admission"})

    wave = json.loads((SKILLS / "cb-context-wave/wave.json").read_text(encoding="utf-8"))
    binding = bind.bind_wave(wave)
    contract = {
        "object_card": card.get("entry_digest"),
        "target_digest": kernel["object_hash"],
        "context_epoch_digest": epoch_receipt.get("epoch_digest"),
        "parent": "cb-management-plane-prove",
        "progress_measure": "wave-execution.v1 exists with NOT_FULL",
        "claim_ceiling": kernel["claim_ceiling"],
        "downstream_consumer": "cb-route-truth-verifier",
        "promotion_allowed": False,
    }
    recipe = admit.admit(wave, NEGATIVES, contract)

    child_map = {
        "ledger": owner,
        "projector": projection,
        "delta_admission": admitted_delta,
        "recency": recency_receipt,
        "omission": omission_receipt,
        "epoch": epoch_receipt,
        "branch_memory": remembered,
    }
    child_results = []
    for child in wave["children"]:
        row = child_map[child["id"]]
        terminal = "COMPLETED" if row.get("status") in {"APPENDED", "PROJECTED", "ADMITTED", "STABLE", "COMPLETE", "SEALED", "REMEMBERED"} else "FAILED"
        child_results.append({"child_id": child["id"], "terminal_state": terminal, "status": row.get("status")})

    execution = controller.run(
        wave,
        child_results,
        budgets={"run_id": "mgmt-plane-prove-1", "depth": 0, "round": 0, "target_sha256": kernel["object_hash"]},
    )
    exec_path = out_dir / "wave-execution.v1.json"
    plane.write_json(exec_path, execution)
    watch_receipt = watch.watch(
        {
            "route_truth": execution["route_truth"],
            "model_free": execution["model_free"],
            "same_state_rounds": 0,
            "loop_count": 0,
            "max_rounds": 1,
        }
    )
    collapse_receipt = collapse.audit(
        [
            {"id": "authority", "source_roots": [str(ledger_path)], "prompt_sha256": "a"},
            {"id": "evidence", "source_roots": [str(root / "receipts/wave_self_loop/latest.json")], "prompt_sha256": "b"},
        ]
    )
    surface = output.compile_output(
        execution,
        {
            "failures": [] if execution["state"] == "COMPLETE" else [execution["state"]],
            "claim_ceiling": kernel["claim_ceiling"],
            "next_action": "do not activate; do not launch providers",
            "contradictions": ["Heavy verifier will refuse this receipt because there are no provider-call files"],
            "minority_branches": ["keep authored waves unactivated"],
        },
    )
    heavy_errors = heavy.verify(SKILLS / "cb-context-wave/wave.json", exec_path)

    receipt = {
        "schema": "constraintbox.management-plane-prove.v1",
        "status": "PROVED_MODEL_FREE",
        "wave_id": wave["wave_id"],
        "recipe_status": recipe.get("status"),
        "recipe_activated": recipe.get("activated"),
        "binding_status": binding.get("status"),
        "execution_schema": execution.get("schema"),
        "execution_state": execution.get("state"),
        "route_truth": execution.get("route_truth"),
        "model_free": execution.get("model_free"),
        "content_interpreted": execution.get("content_interpreted"),
        "watch_verb": watch_receipt.get("verb"),
        "collapse_status": collapse_receipt.get("status"),
        "effective_independent_lanes": collapse_receipt.get("effective_independent_lanes"),
        "surface_status": surface.get("status"),
        "heavy_execution_verified": not heavy_errors,
        "heavy_errors": heavy_errors[:12],
        "epoch_digest": epoch_receipt.get("epoch_digest"),
        "kernel_digest": projection.get("kernel_digest"),
        "resurrection_without_bridge": resurrection.get("reason"),
        "omission_status": omission_receipt.get("status"),
        "promotion_allowed": False,
        "execution_path": str(exec_path),
    }
    plane.write_json(out_dir / "latest.json", receipt)
    return receipt


def main() -> int:
    receipt = prove(BOX)
    print(json.dumps(receipt, sort_keys=True))
    if (
        receipt["execution_schema"] == "constraintbox.wave-execution.v1"
        and receipt["route_truth"] == "NOT_FULL"
        and receipt["recipe_activated"] is False
        and receipt["heavy_execution_verified"] is False
        and receipt["promotion_allowed"] is False
    ):
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
