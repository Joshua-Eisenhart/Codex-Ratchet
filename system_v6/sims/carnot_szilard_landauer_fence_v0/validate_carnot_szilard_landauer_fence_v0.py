#!/usr/bin/env python3
"""Packet-local validator for carnot_szilard_landauer_fence_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "carnot_szilard_landauer_fence_v0"
RESULT = ROOT / "system_v6" / "sims" / SIM_ID / "results" / f"{SIM_ID}_envelope_results.json"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def get_frac(row: dict[str, Any], key: str) -> tuple[int, int]:
    value = row[key]
    return int(value["num"]), int(value["den"])


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    errors: list[str] = []
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "envelope all_pass must be true")
    fence = payload["classical_fence"]
    require(errors, fence["computed"]["eta_C"]["num"] == 1 and fence["computed"]["eta_C"]["den"] == 2, "eta_C must be exactly 1/2")
    require(errors, fence["computed"]["typed_entropy_conversion"]["conversion"] == "1 bit * ln(2) = ln(2) nats", "typed entropy conversion row missing")
    require(errors, fence["computed"]["szilard_single_bit_work"]["exact"] == "ln(2)", "Szilard work must be ln(2) nats")
    require(errors, fence["computed"]["landauer_min_erasure_cost"]["exact"] == "ln(2)", "Landauer minimum must be ln(2) nats")
    expected = fence["expected_solver_status"]
    for name in ("sub_carnot_eta_1_4", "carnot_equality_boundary", "paid_erasure_one_bit", "trivial_zero_work"):
        require(errors, expected[name] == "sat", f"{name} must be SAT/admitted")
    for name in ("super_carnot_eta_3_4", "single_bath_positive_work", "below_landauer_half_paid", "unpaid_erasure_surplus"):
        require(errors, expected[name] == "unsat", f"{name} must be UNSAT/excluded")
    boundary_num, boundary_den = get_frac(fence["admitted_rows"]["carnot_equality_boundary"], "eta")
    require(errors, (boundary_num, boundary_den) == (1, 2), "equality boundary eta must be exactly 1/2")
    require(errors, "eta = eta_C is SAT" in payload["boundary_convention"], "boundary convention must explicitly admit eta=eta_C")
    controls = payload["controls"]
    broken = controls["broken_fence_drop_carnot_constraint_super_carnot"]
    for key, value in broken.items():
        if key != "expected":
            require(errors, value == "sat", f"broken-fence {key} must flip super-Carnot to SAT")
    shuffled = controls["shuffled_ledger_order"]
    require(errors, shuffled["julia"]["normal"]["verdict"] == "sat", "Julia normal order must be SAT")
    require(errors, shuffled["julia"]["shuffled"]["verdict"] == "unsat", "Julia shuffled order must be UNSAT")
    require(errors, shuffled["jax"]["normal_verdict"] == "sat" and shuffled["jax"]["shuffled_verdict"] == "unsat", "JAX order verdict must change")
    require(errors, shuffled["pytorch"]["normal_verdict"] == "sat" and shuffled["pytorch"]["shuffled_verdict"] == "unsat", "PyTorch order verdict must change")
    require(errors, payload["falsifier_results"]["mixed_bits_nats_row"].startswith("killed"), "mixed bits/nats falsifier must be killed")
    require(errors, "state-plus-record" in payload["connection_row"]["observation"], "connection row must name state-plus-record convention")
    require(errors, "no scalar conservation" in payload["connection_row"]["claim_boundary"] or "no cross-type" in payload["connection_row"]["claim_boundary"], "connection row must keep no-admission boundary")
    for engine in ("julia", "jax", "pytorch"):
        rec = payload["engines"][engine]
        require(errors, rec["ran"] is True, f"{engine} engine must have run")
        require(errors, rec["reads_peer_result"] is False, f"{engine} must not read peer result")
        require(errors, rec["classification"] == "scratch_diagnostic", f"{engine} classification drift")
        require(errors, rec["promotion_allowed"] is False, f"{engine} promotion drift")
    gates = payload["build_gates"]
    for key, value in gates.items():
        require(errors, value is True, f"build gate failed: {key}")
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "result_json": str(RESULT.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

