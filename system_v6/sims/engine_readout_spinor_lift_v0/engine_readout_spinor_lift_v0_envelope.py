#!/usr/bin/env python3
"""Envelope for engine_readout_spinor_lift_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "engine_readout_spinor_lift_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
PYTHON_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
MODE = "FIELD"

TOOL_MANIFEST = {
    "QuantumOptics": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia carrier check for the 2pi spinor sign and density erasure",
    },
    "Z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia finite sign identity and erased-flip control",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Python finite sign identity and erased-flip control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Python finite sign identity and erased-flip control",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive dense statevector replay, overlap readout, and density quotient hashes",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope, runtime preflight, hashing, and JSON",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "QuantumOptics": "load_bearing",
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_hash_fresh(payload: dict[str, Any]) -> bool:
    source = ROOT / payload["source_path"]
    return source.exists() and sha256_file(source) == payload["source_sha256"]


def runtime_preflight() -> dict[str, Any]:
    cmd = [SIM_PY, "scripts/codex_runtime_env_doctor.py", "--json"]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False, timeout=180)
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


def engine_record(engine: str, payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    if engine == "julia":
        packages_used = payload["packages_used"]
        load_bearing = payload["aligned_packages_load_bearing"]
        role = "julia_quantumoptics_z3_sign_mirror"
    else:
        packages_used = payload["packages_used"]
        load_bearing = payload["aligned_packages_load_bearing"]
        role = "python_dense_overlap_z3_cvc5_primary"
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": rel(result_path),
        "result_sha256": sha256_file(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "mode": payload["mode"],
        "tool_calls": payload["tool_calls"],
        "values": payload["values"],
        "gate_pass": payload["gate_pass"],
        "role": role,
    }


def compare(julia: dict[str, Any], jax: dict[str, Any]) -> dict[str, Any]:
    keys = ["strategy_count", "lift_separated_count", "lift_still_repeating_count", "parent_groups_split_by_lift"]
    rows = []
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
            "same_answer": max_div == 0.0,
            "interpretation": (
                "Julia independently verifies the spinor sign and finite sign identity; "
                "Python/JAX-labeled lane carries the full n=8 overlap table and quotient control."
            ),
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    py = load_json(PYTHON_RESULT_PATH)
    jl = load_json(JULIA_RESULT_PATH)
    preflight = runtime_preflight()
    div = compare(jl, py)
    proofs = {
        "z3": py["crossover_proofs"]["z3"],
        "cvc5": py["crossover_proofs"]["cvc5"],
        "julia_z3": jl["crossover_proofs"]["julia_z3"],
    }
    gate_pass = {
        "legs_all_pass": py["all_pass"] is True and jl["all_pass"] is True,
        "mode_declared_field": py["mode"] == MODE and jl["mode"] == MODE,
        "ceiling_exact": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in (py, jl)
        ),
        "source_hashes_fresh": source_hash_fresh(py) and source_hash_fresh(jl),
        "no_peer_result_reads": py["reads_peer_result"] is False and jl["reads_peer_result"] is False,
        "runtime_preflight_ok": preflight["ok"] is True,
        "strategy_count_16": py["values"]["strategy_count"] == 16 and jl["values"]["strategy_count"] == 16,
        "all_lift_analogs_separate": py["values"]["lift_separated_count"] == 16 and jl["values"]["lift_separated_count"] == 16,
        "no_720_vs_360_lift_repeats": py["values"]["lift_still_repeating_count"] == 0
        and jl["values"]["lift_still_repeating_count"] == 0,
        "quotient_erasure_control_pass": py["controls"]["quotient_erasure"]["collapses_to_committed_repeat_result"] is True,
        "phase_randomized_control_pass": py["controls"]["phase_randomized"]["kills_separation"] is True,
        "reference_independence_pass": py["controls"]["reference_state_independence"]["all_references_separate_all_rows"] is True,
        "anti_collapse_groups_honest": py["values"]["parent_groups_split_by_lift"] == 0
        and jl["values"]["parent_groups_split_by_lift"] == 0,
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
        "claim": (
            "Scratch diagnostic: phase-sensitive spinor-lift readouts separate the second 360 traversal "
            "from the first for the committed 16 readout strategies, while density quotient erasure "
            "collapses back to the e2d9d5407 repeat classes."
        ),
        "allowed_claims": [
            "n=8 loop-local spinor-lift readout over committed statevector evolution",
            "16 lift-analog 720-vs-360 separation table",
            "density quotient erasure back to committed readout groups",
            "phase-randomized control kills lift separation",
            "parent anti-collapse groups checked for lift splitting",
        ],
        "disallowed_claims": [
            "strategy promotion",
            "engine admission",
            "formal admission",
            "claim beyond n=8 loop-local statevector readout",
            "splitting parent slot-copy groups",
        ],
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "schema_mode_field": MODE,
            "lanes": ["julia", "jax"],
            "lane_note": "No PyTorch lane is scoped because there is no graph/network/autograd claim path.",
            "audit_order": ["combined_envelope", "julia_sign_mirror", "python_dense_overlap", "controller_comparison"],
            "reads_peer_result": False,
            "interpreter": SIM_PY,
        },
        "parent_lineage": {
            "controller": "main_codex_thread",
            "native_subagents": [],
            "external_workers": [],
            "honest_route_note": "Builder-only packet; no audit_verdict.md and no subagent receipt is claimed.",
            "consumed_inputs": py["parent_lineage"],
        },
        "runtime_preflight": preflight,
        "source_refs": py["source_refs"],
        "pin_sha256": py["pin_sha256"],
        "lifted_states": py["lifted_states"],
        "strategy_rows": py["strategy_rows"],
        "separation_table": py["separation_table"],
        "distinguishability": py["distinguishability"],
        "controls": py["controls"],
        "crossover_proofs": proofs,
        "engines": {
            "julia": engine_record("julia", jl, JULIA_RESULT_PATH),
            "jax": engine_record("jax", py, PYTHON_RESULT_PATH),
        },
        "component_results": {
            "julia": {
                "path": rel(JULIA_RESULT_PATH),
                "sha256": sha256_file(JULIA_RESULT_PATH),
                "all_pass": jl["all_pass"],
            },
            "jax": {
                "path": rel(PYTHON_RESULT_PATH),
                "sha256": sha256_file(PYTHON_RESULT_PATH),
                "all_pass": py["all_pass"],
            },
        },
        "claim_path_tools": ["QuantumOptics", "Z3", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            *jl["tool_calls"],
            *py["tool_calls"],
        ],
        "divergence": div,
        "divergence_log": py["divergence_log"],
        "values": py["values"],
        "gate_pass": gate_pass,
        "limits": [
            "Scratch diagnostic only; promotion_allowed=false and formal_admission_allowed=false.",
            "Lift separation is phase-sensitive and disappears under density/projective erasure.",
            "The committed parent slot-copy groups remain unresolved by this lift readout.",
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
                "lift_separated_count": result["values"]["lift_separated_count"],
                "parent_groups_split_by_lift": result["values"]["parent_groups_split_by_lift"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
