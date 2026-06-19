#!/usr/bin/env python3
"""Envelope for engine_readout_strategy_fidelity_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "engine_readout_strategy_fidelity_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
MODE = "FREE"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA = "/opt/homebrew/bin/julia"

TOOL_MANIFEST = {
    "Z3": {"tried": True, "used": True, "reason": "load-bearing Julia-side computed periodicity identity"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing Python-side computed periodicity identity"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent Python-side computed periodicity identity"},
    "numpy": {"tried": True, "used": True, "reason": "supportive dense n=8 state replay and state trace hashing"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive envelope, runtime preflight, hashing, and JSON"},
}

TOOL_INTEGRATION_DEPTH = {
    "Z3": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "numpy": "supportive",
    "python_stdlib": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_result(engine: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def source_hash_fresh(payload: dict[str, Any]) -> bool:
    source = ROOT / payload["source_path"]
    return source.exists() and sha256_file(source) == payload["source_sha256"]


def runtime_preflight() -> dict[str, Any]:
    cmd = [SIM_PY, "scripts/codex_runtime_env_doctor.py", "--json"]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False, timeout=120)
    payload: dict[str, Any] | None = None
    if proc.returncode == 0:
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = None
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "ok": bool(payload and payload.get("summary", {}).get("ok") is True),
        "summary": payload.get("summary") if payload else None,
        "python": payload.get("python", {}).get("path") if payload else None,
        "julia": payload.get("julia", {}).get("path") if payload else None,
        "julia_active_project": payload.get("julia", {}).get("active_project") if payload else None,
        "stderr_head": proc.stderr[:500],
    }


def engine_record(engine: str, payload: dict[str, Any]) -> dict[str, Any]:
    result_path = ROOT / payload["result_path"]
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": payload["result_path"],
        "result_sha256": sha256_file(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "mode": payload["mode"],
        "pin_sha256": payload["pin_sha256"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload["tool_calls"],
        "values": payload["values"],
        "gate_pass": payload["gate_pass"],
        "summary": {
            "periodicity_violation_count": payload["values"]["periodicity_violation_count"],
            "strategy_count": payload["values"]["strategy_count"],
            "state_count_word": payload["values"]["state_count_word"],
            "state_count_double_720": payload["values"]["state_count_double_720"],
        },
        "role": "julia_dense_z3_mirror" if engine == "julia" else "python_dense_z3_cvc5_primary",
    }


def compare(julia: dict[str, Any], jax: dict[str, Any]) -> dict[str, Any]:
    rows = []
    keys = ["strategy_count", "periodicity_violation_count", "state_count_word", "state_count_double_720"]
    max_div = 0.0
    for key in keys:
        values = {"julia": float(julia["values"][key]), "jax": float(jax["values"][key])}
        diff = abs(values["julia"] - values["jax"])
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        max_div = max(max_div, diff)
    return {
        "julia_authoritative": True,
        "engine_values": {
            "julia": {key: float(julia["values"][key]) for key in keys},
            "jax": {key: float(jax["values"][key]) for key in keys},
        },
        "max_divergence": max_div,
        "comparison": {
            "rows": rows,
            "same_named_observable_sets": True,
            "interpretation": "Both legs independently replay n=8 dense loop-local states and bind the same 16-row readout table; exact state digests are not used as cross-language equality gates.",
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    julia = load_result("julia")
    jax = load_result("jax")
    preflight = runtime_preflight()
    proofs = {
        "z3": jax["crossover_proofs"]["z3"],
        "cvc5": jax["crossover_proofs"]["cvc5"],
        "julia_z3": julia["crossover_proofs"]["julia_z3"],
    }
    div = compare(julia, jax)
    gate_pass = {
        "legs_all_pass": julia["all_pass"] is True and jax["all_pass"] is True,
        "mode_declared_free": julia["mode"] == MODE and jax["mode"] == MODE,
        "ceiling_exact": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in (julia, jax)
        ),
        "pin_identical": julia["pin_sha256"] == jax["pin_sha256"],
        "source_hashes_fresh": source_hash_fresh(julia) and source_hash_fresh(jax),
        "no_peer_result_reads": julia["reads_peer_result"] is False and jax["reads_peer_result"] is False,
        "runtime_preflight_ok": preflight["ok"] is True,
        "periodicity_table_clean": julia["values"]["periodicity_violation_count"] == 0 and jax["values"]["periodicity_violation_count"] == 0,
        "strategy_count_16": julia["values"]["strategy_count"] == 16 and jax["values"]["strategy_count"] == 16,
        "state_counts_match_word_and_double": (
            julia["values"]["state_count_word"] == 8
            and jax["values"]["state_count_word"] == 8
            and julia["values"]["state_count_double_720"] == 16
            and jax["values"]["state_count_double_720"] == 16
        ),
        "z3_cvc5_julia_z3_clean": (
            proofs["z3"]["verdict"] == "unsat"
            and proofs["cvc5"]["verdict"] == "unsat"
            and proofs["julia_z3"]["verdict"] == "unsat"
        ),
        "erased_flip_controls_sat": (
            proofs["z3"]["control_verdict"] == "sat"
            and proofs["cvc5"]["control_verdict"] == "sat"
            and proofs["julia_z3"]["control_verdict"] == "sat"
        ),
        "controls_fire": (
            jax["controls"]["shuffled_stage_word_breaks_periodicity_table"] is True
            and jax["controls"]["strategy_blind_trace_constant"] is True
            and jax["controls"]["permuted_seat_assignment_breaks_alternating_paired_split"] is True
        ),
        "engine_value_divergence_zero": div["max_divergence"] == 0.0,
    }
    all_pass = all(gate_pass.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "mode": MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "claim": "Scratch diagnostic readout of the committed 16 strategy automaton on regenerated n=8 dense loop-local states from the committed stage-word cost discriminator.",
        "allowed_claims": [
            "n=8 dense replay of loop-local stage-word states",
            "computed 16-row strategy periodicity table",
            "computed 16x16 strategy distinguishability matrix",
            "z3/cvc5/Z3.jl finite periodicity pressure over computed rows",
        ],
        "disallowed_claims": [
            "strategy promotion",
            "formal admission",
            "physics or engine admission",
            "claim beyond n=8 loop-local replay",
        ],
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "lane_note": "No PyTorch lane is scoped because there is no graph/network/autograd claim path.",
            "audit_order": ["combined_envelope", "python_dense_readout", "julia_dense_z3_mirror", "controller_comparison"],
            "reads_peer_result": False,
        },
        "parent_lineage": {
            "controller": "main_codex_thread",
            "native_subagents": [],
            "external_workers": [],
            "honest_route_note": "Builder-only packet; no audit_verdict.md and no subagent receipt is claimed.",
        },
        "runtime_preflight": preflight,
        "source_refs": {
            "cost_discriminator": jax["source_refs"]["cost_discriminator"],
            "automaton": jax["source_refs"]["automaton"],
        },
        "pin_sha256": jax["pin_sha256"],
        "stage_word": jax["stage_word"],
        "stage_components": jax["stage_components"],
        "strategy_rows": jax["strategy_rows"],
        "periodicity_findings": jax["periodicity_findings"],
        "distinguishability": jax["distinguishability"],
        "controls": jax["controls"],
        "claim_path_tools": ["Z3", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record("julia", julia),
            "jax": engine_record("jax", jax),
        },
        "crossover_proofs": proofs,
        "capability_receipts": {
            "runtime_env_doctor": preflight,
            "python_tools": {
                "z3": jax["package_versions"]["z3"],
                "cvc5": jax["package_versions"]["cvc5"],
                "numpy": jax["package_versions"]["numpy"],
            },
            "julia_project": preflight["julia_active_project"],
        },
        "divergence": div,
        "values": {
            "strategy_count": jax["values"]["strategy_count"],
            "periodicity_violation_count": jax["values"]["periodicity_violation_count"],
            "unique_readouts_360": jax["values"]["unique_readouts_360"],
            "unique_readouts_double_720": jax["values"]["unique_readouts_double_720"],
            "double_720_separates_more_than_360": jax["values"]["double_720_separates_more_than_360"],
            "state_count_word": jax["values"]["state_count_word"],
            "state_count_double_720": jax["values"]["state_count_double_720"],
        },
        "gate_pass": gate_pass,
        "validator_expected_command": f"{SIM_PY} scripts/validate_three_engine_sim_result.py {rel(RESULT_PATH)}",
        "limits": [
            "scratch_diagnostic ceiling; promotion_allowed=false; formal_admission_allowed=false",
            "Readout is the committed stage-word component read rule applied to actual dense loop-local state traces.",
            "No audit verdict file is emitted by this builder packet.",
        ],
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": result["all_pass"],
                "result_path": rel(RESULT_PATH),
                "strategy_count": result["values"]["strategy_count"],
                "periodicity_violations": result["values"]["periodicity_violation_count"],
                "double_720_separates_more": result["values"]["double_720_separates_more_than_360"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
