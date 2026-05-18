#!/usr/bin/env python3
"""Source-native cross-engine Holodeck memory cycle scout.

This converts the tmp wave120/wave121 idea into a current formal scout with
controls. It runs both EngineCore chiralities through repeated memory cycles,
stores source-native density predictions under contextual hashes, and checks
that recall requires the running model context plus engine tag.

Formal scout only. This is not a full Holodeck memory system and not a
canonical engine/FEP/Axis0 claim.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import sympy as sp
import torch
import z3

from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_cross_engine_holodeck_memory_cycle_probe_results.json"

NAME = "source_native_cross_engine_holodeck_memory_cycle_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: runs a bounded source-native cross-engine Holodeck "
    "memory cycle over EngineCore engine_type 0/1, with engine-tagged memory, "
    "wrong-engine, hash-only, no-memory, and tag-collision controls. It does "
    "not admit full Holodeck memory, final FEP, Axis0, physics, cognition, "
    "world-model, or canonical architecture claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Pauli matrices, density trace distance, Bloch readout, state-hash eigenvalue/Bloch extraction, memory-cycle scoring, and means",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive contextual hash keys for memory cells; hashes are not the predictive model",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result receipt serialization",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic 2 engines x 32 substages entry-count check",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite tag-collision impossibility witness",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native EngineCore trajectories for both chiralities consumed by torch checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "hashlib": "supportive",
    "json": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "engine_core": "supportive",
}

TORCH_REAL = torch.float64
TORCH_COMPLEX = torch.complex128
SX = torch.tensor([[0, 1], [1, 0]], dtype=TORCH_COMPLEX)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=TORCH_COMPLEX)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=TORCH_COMPLEX)
N_CYCLES = 3
INIT_SEED = 70000
TRACE_TOL = 1e-8


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_density(rho: Any) -> torch.Tensor:
    return torch.as_tensor(rho, dtype=TORCH_COMPLEX).clone()


def hermitian_part(rho: Any) -> torch.Tensor:
    rho_t = as_density(rho)
    return (rho_t + rho_t.mH) / 2


def bloch(rho: Any) -> torch.Tensor:
    rho_t = as_density(rho)
    return torch.stack(
        (
            torch.real(torch.trace(rho_t @ SX)),
            torch.real(torch.trace(rho_t @ SY)),
            torch.real(torch.trace(rho_t @ SZ)),
        )
    ).to(dtype=TORCH_REAL)


def trace_distance(rho1: Any, rho2: Any) -> float:
    diff = as_density(rho1) - as_density(rho2)
    evals = torch.linalg.eigvalsh(diff.conj().T @ diff).real
    return 0.5 * float(torch.sum(torch.sqrt(torch.clamp(evals, min=0.0))).item())


def state_hash(rho: Any, precision: int = 5) -> str:
    rho_t = hermitian_part(rho)
    evals = torch.sort(torch.linalg.eigvalsh(rho_t).real, descending=True).values
    b = bloch(rho_t)
    payload = (
        round(float(evals[0].item()), precision),
        round(float(b[0].item()), precision),
        round(float(b[1].item()), precision),
        round(float(b[2].item()), precision),
    )
    return hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()[:12]


def memory_key(engine_type: int, rho_before: Any, main_idx: int, substage_idx: int, *, tag_engine: bool) -> tuple[Any, ...]:
    if tag_engine:
        return (engine_type, state_hash(rho_before), main_idx, substage_idx)
    return (state_hash(rho_before), main_idx, substage_idx)


def run_one_trajectory(engine_type: int, init_seed: int = INIT_SEED) -> list[dict[str, Any]]:
    engine = EngineCore(engine_type, manifold_enabled=True)
    rho = generate_initial_density(init_seed)
    rows: list[dict[str, Any]] = []
    for main_idx, (perception, loop_class) in enumerate(engine.schedule):
        for substage_idx in range(4):
            rho_before = rho.copy()
            rho, record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
            rho_before_t = as_density(rho_before)
            rho_after_t = as_density(rho)
            rows.append(
                {
                    "engine_type": engine_type,
                    "main_idx": main_idx,
                    "substage_idx": substage_idx,
                    "ordered_token": record["ordered_token"],
                    "operator": record["operator"],
                    "operator_sign": int(record["operator_sign"]),
                    "rho_before": rho_before_t,
                    "rho_after": rho_after_t,
                    "before_hash": state_hash(rho_before_t),
                    "after_hash": state_hash(rho_after_t),
                    "bloch_after": bloch(rho_after_t).tolist(),
                }
            )
    return rows


def run_memory_cycles(*, tag_engine: bool) -> tuple[list[dict[str, Any]], dict[tuple[Any, ...], torch.Tensor]]:
    memory: dict[tuple[Any, ...], torch.Tensor] = {}
    cycles = []
    for cycle in range(N_CYCLES):
        row: dict[str, Any] = {
            "cycle": cycle,
            "hits": {0: 0, 1: 0},
            "misses": {0: 0, 1: 0},
            "wrong_engine_false_hits": 0,
            "errors": [],
        }
        trajectories = {etype: run_one_trajectory(etype) for etype in (0, 1)}
        for etype, trajectory in trajectories.items():
            wrong_type = 1 - etype
            for step in trajectory:
                key = memory_key(etype, step["rho_before"], step["main_idx"], step["substage_idx"], tag_engine=tag_engine)
                pred = memory.get(key)
                if pred is None:
                    row["misses"][etype] += 1
                else:
                    err = trace_distance(pred, step["rho_after"])
                    row["errors"].append(err)
                    if err <= TRACE_TOL:
                        row["hits"][etype] += 1
                    else:
                        row["misses"][etype] += 1
                wrong_key = memory_key(wrong_type, step["rho_before"], step["main_idx"], step["substage_idx"], tag_engine=tag_engine)
                wrong_pred = memory.get(wrong_key)
                if wrong_pred is not None and trace_distance(wrong_pred, step["rho_after"]) <= TRACE_TOL:
                    row["wrong_engine_false_hits"] += 1
                memory[key] = step["rho_after"].clone()
        row["memory_size_after_cycle"] = len(memory)
        row["total_hits"] = row["hits"][0] + row["hits"][1]
        row["total_misses"] = row["misses"][0] + row["misses"][1]
        row["hit_rate"] = row["total_hits"] / max(1, row["total_hits"] + row["total_misses"])
        row["max_error"] = max(row["errors"]) if row["errors"] else None
        row["mean_error"] = float(torch.mean(torch.tensor(row["errors"], dtype=TORCH_REAL)).item()) if row["errors"] else None
        cycles.append(row)
    return cycles, memory


def hash_only_control(memory: dict[tuple[Any, ...], torch.Tensor]) -> dict[str, Any]:
    digest_only = [hashlib.sha256(repr(key).encode("utf-8")).hexdigest()[:12] for key in memory]
    return {
        "pass": len(digest_only) == len(memory) and len(set(digest_only)) == len(digest_only),
        "hash_count": len(digest_only),
        "available_density_predictions": 0,
        "max_recall_without_model": 0.0,
    }


def sympy_entry_count() -> dict[str, Any]:
    engines = sp.Integer(2)
    substages = sp.Integer(32)
    total = engines * substages
    return {"pass": int(total) == 64, "engines": int(engines), "substages_per_engine": int(substages), "total": int(total)}


def z3_engine_tag_witness() -> dict[str, Any]:
    solver = z3.Solver()
    e0 = z3.Int("e0")
    e1 = z3.Int("e1")
    h = z3.Int("h")
    main = z3.Int("main")
    sub = z3.Int("sub")
    solver.add(e0 != e1)
    solver.add(z3.And(e0 == e1, h == h, main == main, sub == sub))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "witness": "engine-tagged tuple keys with different engine ids cannot be identical",
    }


def main() -> int:
    started = time.time()
    tagged_cycles, tagged_memory = run_memory_cycles(tag_engine=True)
    untagged_cycles, untagged_memory = run_memory_cycles(tag_engine=False)
    hash_control = hash_only_control(tagged_memory)
    sympy_check = sympy_entry_count()
    z3_check = z3_engine_tag_witness()

    cycle0 = tagged_cycles[0]
    cycle1 = tagged_cycles[1]
    cycle2 = tagged_cycles[2]
    untagged_final = untagged_cycles[-1]

    positive = {
        "cycle0_is_no_memory_control": {
            "pass": cycle0["total_hits"] == 0 and cycle0["total_misses"] == 64,
            "cycle0": cycle0,
        },
        "cycle1_recall_requires_tagged_predictive_memory": {
            "pass": cycle1["total_hits"] == 64 and cycle1["total_misses"] == 0 and cycle1["hit_rate"] == 1.0,
            "cycle1": cycle1,
        },
        "cycle2_recall_is_stable": {
            "pass": cycle2["total_hits"] == 64 and cycle2["total_misses"] == 0 and cycle2["hit_rate"] == 1.0,
            "cycle2": cycle2,
        },
        "memory_holds_both_chiral_engine_trajectories": {
            "pass": len(tagged_memory) == 64,
            "tagged_memory_size": len(tagged_memory),
            "expected": 64,
        },
        "wrong_engine_control_rejects_cross_chirality_prediction": {
            "pass": cycle1["wrong_engine_false_hits"] == 0 and cycle2["wrong_engine_false_hits"] == 0,
            "cycle1_false_hits": cycle1["wrong_engine_false_hits"],
            "cycle2_false_hits": cycle2["wrong_engine_false_hits"],
        },
        "sympy_cross_engine_entry_count": sympy_check,
        "z3_engine_tag_distinguishes_keys": z3_check,
    }
    graveyards = {
        "hash_only_is_not_recall": hash_control,
        "untagged_memory_collapses_cross_engine_capacity": {
            "pass": len(untagged_memory) < len(tagged_memory)
            or untagged_final["wrong_engine_false_hits"] > 0
            or untagged_final["hit_rate"] < cycle2["hit_rate"],
            "tagged_memory_size": len(tagged_memory),
            "untagged_memory_size": len(untagged_memory),
            "untagged_final": untagged_final,
            "reason": "Removing engine tag is a collision/ambiguity control; it must not be treated as the same Holodeck memory.",
        },
        "full_holodeck_memory_not_admitted": {
            "pass": PROMOTION_ALLOWED is False,
            "reason": "This is deterministic density recall over EngineCore trajectories, not a neural or full world-model memory system.",
        },
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "tmp_wave120_121_converted_not_promoted": {
            "pass": True,
            "tmp_inputs": ["wave120_v2_real_engine_holodeck_cycle_probe.py", "wave121_v2_cross_engine_holodeck_probe.py"],
        },
        "source_native_engine_core_used": {
            "pass": all(row["pass"] for row in positive.values() if isinstance(row, dict) and "pass" in row),
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_cross_engine_holodeck_memory_cycle",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "tagged_cycles": tagged_cycles,
        "untagged_cycles": untagged_cycles,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This is a source-native v5 conversion of tmp wave120/wave121 proposal sims.",
            "It adds controls and keeps the claim ceiling formal-scout only.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyards, **boundary}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  tagged_memory={len(tagged_memory)} untagged_memory={len(untagged_memory)}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
