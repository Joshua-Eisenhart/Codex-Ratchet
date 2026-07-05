#!/usr/bin/env python3
"""Run or reuse the G0-G12 tower chain into one scratch receipt."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = RESULTS / "tower_chain_run_v0_receipt.json"
PY = os.environ.get("PYTHON", str(ROOT / ".venv" / "bin" / "python3"))
JULIA = os.environ.get("JULIA", "julia")

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
CAPSTONE = "DRAFT_UNAUDITED"


RUNGS: list[dict[str, Any]] = [
    {"rung": "G0", "packet": "system_v7/sims/tower_g0_finite_support_v0", "mode": "rerun", "sweep": "BY-CONSTRUCTION — NOT chain-admissible", "caveats": ["toy/unbound solver controls in audit sweep; included only because campaign asks G0->G12 base instantiation"]},
    {"rung": "G1", "packet": "system_v7/sims/distinguishability_quotient_floor_v0", "mode": "rerun", "sweep": "READY from inventory", "caveats": ["scratch ceiling"]},
    {"rung": "G2", "packet": "system_v7/sims/finite_probe_quotient_inverse_limit_tower_1q_through_4q", "mode": "rerun", "sweep": "READY from inventory", "caveats": ["scratch ceiling"]},
    {"rung": "G3", "packet": "system_v7/sims/independent_survivor_restriction_noncommutation_verify_v0", "mode": "rerun", "sweep": "READY from inventory", "caveats": ["later carve variants not rerun here"]},
    {"rung": "G4", "packet": "system_v7/sims/ordered_channel_maps_noncommutation_matrix_v0", "mode": "rerun", "sweep": "READY from inventory", "caveats": ["ordered update/noncommutation matrix only"]},
    {"rung": "G5", "packet": "system_v7/sims/tower_g5_density_floor_v0", "mode": "rerun", "sweep": "GENUINE-W-CAVEATS", "caveats": ["closure-demand/expressibility facts asserted not tested; toy z3/cvc5 control; shuffle is invariance not kill"]},
    {"rung": "G6G7", "packet": "system_v7/sims/tower_g6g7_spinor_hopf_v0", "mode": "rerun", "sweep": "GENUINE-W-CAVEATS", "caveats": ["Hopf closed=measured self-plant; horizontal residual hardcoded 0.0; flat-S2 kill weak"]},
    {"rung": "G8", "packet": "system_v7/sims/tower_g8_two_sheets_v0", "mode": "rerun", "sweep": "GENUINE-W-CAVEATS — chain-admissible after repair", "caveats": ["relabel subcontrol recomputes sheet(1.0) instead of transforming measured right sheet"]},
    {"rung": "G9", "packet": "system_v7/sims/finite_ring_block_partition_reversible_qca_gnvw_index_v0", "mode": "rerun", "sweep": "READY from inventory", "caveats": ["loop/index behavior anchor"]},
    {"rung": "G10", "packet": "system_v7/sims/tower_g10_terrain_flows_v0", "mode": "rerun", "sweep": "GENUINE-W-CAVEATS — chain-admissible after repair", "caveats": ["fixture-authored terrain pairing; stale wrapper text in envelope"]},
    {"rung": "G11", "packet": "system_v5/ops/formal_scouts", "mode": "reused", "result_globs": ["foundation_nested_hopf_weyl_signed_cut_ratchet_*results.json", "../../julia_carrier/results/foundation_nested_hopf_weyl_signed_cut_ratchet_julia_results.json"], "sweep": "READY from inventory", "caveats": ["existing formal-scout/json receipt reused; not mechanically rerun here"]},
    {"rung": "G12", "packet": "system_v7/sims/cut_lattice_schmidt_entropy_v0", "mode": "rerun", "sweep": "READY from inventory", "caveats": ["cut-lattice entropy anchor"]},
]

NESTING = [
    ("G0", "G1", "G1 quotient presupposes finite carrier/classes from G0", "structural_only"),
    ("G1", "G2", "G2 probes refine quotient classes", "structural_only"),
    ("G2", "G3", "G3 survivors carve the probe quotient population", "structural_only"),
    ("G3", "G4", "G4 ordered updates act on survivor/state classes", "structural_only"),
    ("G4", "G5", "G5 installs rho after finite quotient/history prerequisites", "structural_only"),
    ("G5", "G6G7", "spinor-Hopf rung consumes rho/density-floor carrier licensing", "structural_only"),
    ("G6G7", "G8", "two-sheet chirality presupposes spinor/Hopf object class", "structural_only"),
    ("G8", "G9", "loop classes sit over sheet/fiber/base split", "structural_only"),
    ("G9", "G10", "terrain flows are applied after loop/fiber/base classes exist", "structural_only"),
    ("G10", "G11", "nested shells/flux presuppose terrain-flow stages", "structural_only"),
    ("G11", "G12", "cut lattice consumes nested shell/flux/cut class evidence", "structural_only"),
]


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command_for(path: pathlib.Path, script: pathlib.Path) -> list[str]:
    if script.suffix == ".jl":
        return [JULIA, str(script.name)]
    return [PY, str(script.name)]


def run_cmd(path: pathlib.Path, cmd: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))
    env.setdefault("NUMBA_CACHE_DIR", str(ROOT / ".cache" / "numba"))
    proc = subprocess.run(cmd, cwd=path, text=True, capture_output=True, timeout=240, env=env)
    return {"cmd": cmd, "exit": proc.returncode, "stdout_tail": proc.stdout[-1200:], "stderr_tail": proc.stderr[-1200:]}


def result_files(path: pathlib.Path, globs: list[str] | None = None) -> list[pathlib.Path]:
    if globs:
        found: list[pathlib.Path] = []
        for pat in globs:
            found.extend(path.glob(pat))
        return sorted(set(p for p in found if p.is_file()))
    return sorted((path / "results").glob("*.json")) if (path / "results").exists() else sorted(path.glob("*results.json"))


def small_witness(payload: Any, limit: int = 24) -> dict[str, Any]:
    out: dict[str, Any] = {}

    def walk(obj: Any, prefix: str = "") -> None:
        if len(out) >= limit:
            return
        if isinstance(obj, dict):
            for key, val in obj.items():
                if key in {"all_pass", "classification", "promotion_allowed", "formal_admission_allowed", "max_divergence", "quotient_class_count_full", "quotient_class_count_erased", "installed_vs_forced", "engine_parity", "divergence", "witnesses"}:
                    out[prefix + key] = val
                elif isinstance(val, (dict, list)):
                    walk(val, prefix + key + ".")
                elif isinstance(val, (str, int, float, bool)) and any(tok in key.lower() for tok in ("pass", "count", "residual", "distance", "entropy", "rank", "parity", "verdict", "class")):
                    out[prefix + key] = val
        elif isinstance(obj, list):
            for idx, val in enumerate(obj[:6]):
                walk(val, prefix + str(idx) + ".")

    walk(payload)
    return out


def load_jsons(files: list[pathlib.Path]) -> tuple[dict[str, str], dict[str, Any]]:
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in files}
    witnesses: dict[str, Any] = {}
    for p in files:
        try:
            witnesses[str(p.relative_to(ROOT))] = small_witness(json.loads(p.read_text(encoding="utf-8")))
        except Exception as exc:
            witnesses[str(p.relative_to(ROOT))] = {"json_load_error": str(exc)}
    return hashes, witnesses


def run_rung(item: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / item["packet"]
    runs: list[dict[str, Any]] = []
    if item["mode"] == "rerun":
        scripts = []
        for suffix in ("_julia.jl", "_jax.py", "_pytorch.py"):
            scripts.extend(sorted(p for p in path.iterdir() if p.is_file() and p.name.endswith(suffix)))
        scripts.extend(sorted(p for p in path.iterdir() if p.is_file() and p.name == "check_agreement.py"))
        for script in scripts:
            runs.append(run_cmd(path, command_for(path, script)))
    files = result_files(path, item.get("result_globs"))
    hashes, witnesses = load_jsons(files)
    exits = [r["exit"] for r in runs]
    return {
        "rung": item["rung"],
        "packet": item["packet"],
        "mode": "rerun" if item["mode"] == "rerun" else "reused_receipt",
        "rerun_commands": runs,
        "rerun_exit_ok": all(code == 0 for code in exits) if exits else None,
        "result_hashes": hashes,
        "witnesses": witnesses,
        "engine_parity": "fresh_check_exit_0" if exits and all(code == 0 for code in exits) else ("reused_existing_json" if not exits else "fresh_check_failed_or_partial"),
        "verdict_from_sweep": item["sweep"],
        "caveats_carried": item["caveats"],
    }


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rungs = [run_rung(item) for item in RUNGS]
    nesting = [{"from": a, "to": b, "check": text, "status": status} for a, b, text, status in NESTING]
    receipt = {
        "schema_version": "tower_chain_run_v0",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "capstone": CAPSTONE,
        "claim": "One scripted scratch pass instantiating the nested tower G0->G12 in admission order with Xi/G13 recorded open.",
        "claim_ceiling": "DRAFT_UNAUDITED chain receipt; reused receipts and structural-only nesting checks do not promote the tower.",
        "rungs": rungs,
        "nesting_checks": nesting,
        "open_top": {"rung": "G13", "name": "Xi", "status": "OPEN", "simulated": False},
        "chain_summary": {
            "rungs_instantiated": len(rungs),
            "rungs_reused": sum(1 for r in rungs if r["mode"] == "reused_receipt"),
            "nesting_checks_passed": sum(1 for n in nesting if n["status"] in {"dependency_witness", "structural_only"}),
            "nesting_checks_structural_only": sum(1 for n in nesting if n["status"] == "structural_only"),
            "open_top": "Xi",
            "fresh_rerun_fail_or_partial": [r["rung"] for r in rungs if r["rerun_exit_ok"] is False],
        },
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(OUT.relative_to(ROOT)), "rungs": len(rungs), "reused": receipt["chain_summary"]["rungs_reused"], "fresh_fail_or_partial": receipt["chain_summary"]["fresh_rerun_fail_or_partial"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
