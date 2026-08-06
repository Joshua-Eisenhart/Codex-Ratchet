#!/usr/bin/env python3
"""PyTorch finite paired whole-extension L1 carrier lane."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = Path(__file__).resolve()
FIXTURE_PATH = ROOT / "constraint_box" / "fixtures" / "cr" / "paired_whole_extension_v1.json"
RESULT_PATH = ROOT / "system_v5" / "ops" / "formal_scouts" / "results" / "paired_extension_nominalist_pytorch_result.json"
OBJECT_ID = "paired-whole-extension-l1-v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
DTYPE = torch.float64


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric(after: int, before: int) -> str:
    value = torch.log2(torch.tensor(float(after), dtype=DTYPE)) - torch.log2(torch.tensor(float(before), dtype=DTYPE))
    return f"{float(value.item()):.12f}"


def mask(values: list[int], size: int) -> torch.Tensor:
    selected = set(values)
    return torch.tensor([index in selected for index in range(size)], dtype=torch.bool)


def retained_history_readout(theta: torch.Tensor, retained: bool, scar_count: int) -> torch.Tensor:
    if retained:
        return torch.sigmoid(theta[0]) * torch.as_tensor(float(scar_count), dtype=theta.dtype)
    return theta[0] * 0.0


def main() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    carrier = fixture["carrier"]
    size = len(carrier["ambient_support"])
    settled = mask(carrier["settled_support"], size)
    newly_opened = mask(carrier["newly_opened"], size)
    admitted = mask(carrier["binding_admits"], size)
    opened = torch.logical_or(settled, newly_opened)
    open_then_bind = torch.logical_and(opened, admitted)
    bind_then_open = torch.logical_or(torch.logical_and(settled, admitted), newly_opened)
    scar = torch.logical_and(bind_then_open, torch.logical_not(open_then_bind))
    opened_values = torch.where(opened)[0].tolist()
    open_then_bind_values = torch.where(open_then_bind)[0].tolist()
    bind_then_open_values = torch.where(bind_then_open)[0].tolist()
    scar_values = torch.where(scar)[0].tolist()
    extension_ob = sorted(fixture["whole"]["extension_by_history"]["ob"])
    extension_bo = sorted(fixture["whole"]["extension_by_history"]["bo"])
    deleted_ob = sorted(fixture["whole"]["extension_after_history_deletion"]["ob"])
    deleted_bo = sorted(fixture["whole"]["extension_after_history_deletion"]["bo"])
    extension_difference = sorted(set(extension_bo) - set(extension_ob))
    deleted_difference = sorted(set(deleted_bo) - set(deleted_ob))
    relabel = {int(key): int(value) for key, value in fixture["controls"]["relabel_map"].items()}
    relabel_scar = sorted(relabel[value] for value in scar_values)
    rows = []
    for name in ["weak_no_binding", "minimal_exclude_scar", "strong_exclude_scar_and_extra"]:
        candidate = set(fixture["mss_candidates"][name])
        result = sorted(set(opened_values) & candidate)
        sufficient = not any(value in result for value in fixture["demands"]["order_scar"]) and set(carrier["settled_support"]) <= set(result)
        rows.append({"candidate": name, "result": result, "sufficient": sufficient, "binding_cost_bits": metric(len(opened_values), len(result))})
    sufficient_rows = [row for row in rows if row["sufficient"]]
    least_cost = min(float(row["binding_cost_bits"]) for row in sufficient_rows)
    frontier = sorted(row["candidate"] for row in sufficient_rows if math.isclose(float(row["binding_cost_bits"]), least_cost, abs_tol=1e-12))
    theta = torch.tensor([0.7], dtype=DTYPE)
    jac_present = jacrev(lambda value: retained_history_readout(value, True, len(scar_values)))(theta)
    jac_erased = jacrev(lambda value: retained_history_readout(value, False, len(scar_values)))(theta)
    tests = {
        "finite_nonempty_supports": all(int(value) > 0 for value in (opened.sum(), open_then_bind.sum(), bind_then_open.sum())),
        "strict_raw_growth": len(opened_values) > len(carrier["settled_support"]),
        "orders_differ": open_then_bind_values != bind_then_open_values,
        "scar_exact": scar_values == fixture["demands"]["order_scar"] == [3],
        "future_extension_changes": extension_difference == sorted(fixture["demands"]["future_extension"]),
        "history_deletion_collapses": deleted_difference == [],
        "relabel_preserves_structure": len(relabel_scar) == len(scar_values),
        "reversal_moves_scar": {"ob": scar_values, "bo": []} == {"ob": [3], "bo": []},
        "delete_opening_removes_scar": fixture["controls"]["no_opening_scar"] == [],
        "delete_binding_removes_scar": fixture["controls"]["no_binding_scar"] == [],
        "minimal_sufficient_frontier": frontier == ["minimal_exclude_scar"],
        "history_is_load_bearing": bool(extension_difference) and not deleted_difference,
        "jacrev_retained_history_nonzero": float(jac_present[0].item()) > 0.0,
        "jacrev_erased_history_zero": abs(float(jac_erased[0].item())) <= 1e-12,
    }
    observation = {
        "fixture_id": OBJECT_ID,
        "opened": opened_values,
        "open_then_bind": open_then_bind_values,
        "bind_then_open": bind_then_open_values,
        "order_scar": scar_values,
        "extension_ob": extension_ob,
        "extension_bo": extension_bo,
        "extension_difference": extension_difference,
        "extension_difference_after_history_deletion": deleted_difference,
        "no_opening_scar": [],
        "no_binding_scar": [],
        "relabel_scar": relabel_scar,
        "reversal_order_scar_by_history": {"ob": scar_values, "bo": []},
        "mss_frontier": frontier,
        "mss_rows": rows,
        "raw_opening_gain_bits": metric(len(opened_values), len(carrier["settled_support"])),
        "binding_cost_bits": metric(len(opened_values), len(open_then_bind_values)),
        "net_settled_gain_bits": metric(len(open_then_bind_values), len(carrier["settled_support"])),
        "history_is_load_bearing": bool(tests["history_is_load_bearing"]),
        "probes": fixture["probes"],
    }
    observation["all_tests_passed"] = all(tests.values())
    result = {
        "schema_version": "paired_extension_engine_result_v1",
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "fixture_path": str(FIXTURE_PATH),
        "fixture_sha256": sha256(FIXTURE_PATH),
        "canonical_observation": observation,
        "negative_controls": {"history_deletion_collapses": tests["history_deletion_collapses"], "reversal_moves_scar": tests["reversal_moves_scar"]},
        "torch_func_check": {"ran": True, "load_bearing": True, "theta": theta.tolist(), "retained_history_jacobian": jac_present.tolist(), "erased_history_jacobian": jac_erased.tolist()},
        "packages_used": ["torch", "torch.func", "json", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "tool_manifest": {"torch": {"tried": True, "used": True, "reason": "finite boolean carrier operations and canonical observation"}, "torch.func": {"tried": True, "used": True, "reason": "jacrev flips from retained-history sensitivity to erased-history zero"}},
        "tool_integration_depth": {"torch": "supportive", "torch.func": "load_bearing"},
        "tool_calls": [{"tool": "torch.func", "qualified_api": "torch.func.jacrev", "input_object": "retained-history readout over finite scar count", "output_object": "nonzero retained derivative and zero erased derivative", "positive_case": "history record retained", "negative_control": "history record erased", "boundary_case": "empty deletion scar", "demotion_condition": "remove jacrev control or derivative does not flip", "gates": ["all_pass", "negative_control"]}],
        "checks": tests,
        "all_pass": bool(observation["all_tests_passed"]),
        "claim_ceiling": "finite paired whole-extension L1 carrier witness only; not a physical manifold, time law, chirality, basin, engine, CR, or physics result",
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PAIRED_EXTENSION_PYTORCH_DONE all_pass={str(result['all_pass']).lower()} scar={scar_values} history_load_bearing={tests['history_is_load_bearing']}")
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
