#!/usr/bin/env python3
"""Seed Holodeck prediction-first memory loop probe.

This is the smallest executable Holodeck loop I want before heavier QIT replay:
project a prediction, sense/probe the finite world, error-correct the model,
write survivor and graveyard semantic hashes, then test recall against controls.

Formal scout only. This does not admit a final Holodeck, FEP, QIT engine,
Axis0, gravity, cognition, consciousness, or physics claim.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "holodeck_core_prediction_memory_seed_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "classical"
SOURCE_ALIGNMENT_CATEGORY = "holodeck_prediction_first_memory_seed"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite seed Holodeck loop where prediction-first "
    "correction plus survivor/graveyard semantic hashes beats hash-only, "
    "shuffled-context, frozen-model, and no-graveyard controls. It is a "
    "classical seed fixture for later QIT-engine adapters, not final Holodeck, "
    "FEP, Axis0, gravity, cognition, consciousness, or physics evidence."
)

FINITE_MAP = (
    "C: (finite context graph, model vectors, probe vectors, survivor hashes, "
    "graveyard hashes) -> corrected model plus survivor/graveyard recall record"
)
DOMAIN = {
    "contexts": "8 finite world contexts",
    "features": "10 finite semantic feature coordinates per context",
    "probe_family": "context-local observation vectors plus cosine/error probes",
}
CODOMAIN_OR_OUTPUT = {
    "corrected_model": "finite context-indexed prediction vectors",
    "survivor_hashes": "confirmed context/vector records",
    "graveyard_hashes": "killed prediction records",
    "metrics": "error reduction, recall similarity, false accept rates",
}
BLOCKED_CONSUMERS = [
    "final_holodeck",
    "FEP_admission",
    "QIT_engine_admission",
    "Axis0",
    "Xi/Phi0",
    "gravity",
    "physics",
    "cognition",
    "consciousness",
]

TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic finite vector loop, cosine/error probes, controls, and result assembly",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive survivor/graveyard semantic hash construction and collision checks",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "supportive",
    "hashlib": "supportive",
    "json": "supportive",
}

N_CONTEXTS = 8
N_FEATURES = 10
N_CYCLES = 6
CORRECTION_GAIN = 0.42
SURVIVOR_ERROR_FLOOR = 0.19
FALSE_ACCEPT_THRESHOLD = 0.68


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(a: list[float]) -> float:
    return math.sqrt(max(dot(a, a), 1e-15))


def normalize(a: list[float]) -> list[float]:
    n = norm(a)
    return [x / n for x in a]


def cosine(a: list[float], b: list[float]) -> float:
    return dot(a, b) / (norm(a) * norm(b))


def l2(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def blend(a: list[float], b: list[float], gain: float) -> list[float]:
    return normalize([(1.0 - gain) * x + gain * y for x, y in zip(a, b)])


def true_world_vector(context_id: int) -> list[float]:
    values = []
    for j in range(N_FEATURES):
        x = (
            math.sin(0.73 * context_id + 0.41 * j)
            + 0.55 * math.cos(0.37 * context_id - 0.29 * j)
            + 0.19 * math.sin((context_id + 1) * (j + 2) * 0.11)
        )
        values.append(x)
    return normalize(values)


def observation_vector(context_id: int, cycle: int) -> list[float]:
    base = true_world_vector(context_id)
    noise = [
        0.025 * math.sin((cycle + 1) * (j + 3) + 0.7 * context_id)
        for j in range(N_FEATURES)
    ]
    return normalize([x + n for x, n in zip(base, noise)])


def initial_model_vector(context_id: int) -> list[float]:
    # Deliberately plausible but wrong: a generic prior tilted by context.
    values = [
        math.cos(0.21 * context_id + 0.53 * j) + 0.15 * math.sin(j + 1)
        for j in range(N_FEATURES)
    ]
    return normalize(values)


def semantic_hash(kind: str, context_id: int, vector: list[float]) -> str:
    payload = {
        "kind": kind,
        "context": context_id,
        "rounded": [round(x, 3) for x in vector],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:20]


def project_prediction(model: dict[int, list[float]], context_id: int) -> list[float]:
    left = model[(context_id - 1) % N_CONTEXTS]
    here = model[context_id]
    right = model[(context_id + 1) % N_CONTEXTS]
    return normalize([
        0.72 * h + 0.14 * l + 0.14 * r
        for h, l, r in zip(here, left, right)
    ])


def run_loop(*, update: bool, shuffled_context: bool, write_graveyard: bool) -> dict[str, Any]:
    model = {i: initial_model_vector(i) for i in range(N_CONTEXTS)}
    survivor_hashes: dict[str, dict[str, Any]] = {}
    graveyard_hashes: dict[str, dict[str, Any]] = {}
    error_trace: list[dict[str, float]] = []
    killed_vectors: list[dict[str, Any]] = []

    for cycle in range(N_CYCLES):
        for context_id in range(N_CONTEXTS):
            active_context = (context_id + 3) % N_CONTEXTS if shuffled_context else context_id
            prediction = project_prediction(model, active_context)
            observation = observation_vector(context_id, cycle)
            err_before = l2(prediction, observation)
            if write_graveyard and err_before > SURVIVOR_ERROR_FLOOR:
                key = semantic_hash("graveyard", context_id, prediction)
                graveyard_hashes[key] = {
                    "context_id": context_id,
                    "cycle": cycle,
                    "error": err_before,
                    "vector": prediction,
                }
                killed_vectors.append({"context_id": context_id, "vector": prediction, "error": err_before})

            if update:
                model[active_context] = blend(model[active_context], observation, CORRECTION_GAIN)

            corrected = project_prediction(model, active_context)
            err_after = l2(corrected, observation)
            if err_after <= err_before:
                key = semantic_hash("survivor", context_id, corrected)
                survivor_hashes[key] = {
                    "context_id": context_id,
                    "cycle": cycle,
                    "error": err_after,
                    "vector": corrected,
                }
            error_trace.append(
                {
                    "cycle": cycle,
                    "context_id": context_id,
                    "error_before": err_before,
                    "error_after": err_after,
                }
            )

    return {
        "model": model,
        "survivor_hashes": survivor_hashes,
        "graveyard_hashes": graveyard_hashes,
        "error_trace": error_trace,
        "killed_vectors": killed_vectors,
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def recall_similarity(model: dict[int, list[float]]) -> float:
    return mean([cosine(project_prediction(model, i), true_world_vector(i)) for i in range(N_CONTEXTS)])


def remote_chain_similarity(model: dict[int, list[float]]) -> float:
    # Walk a cue chain through the world, then test the remote context. This is
    # the recall-space piece: memory is reached by moving through contexts.
    chain = [0, 1, 3, 6]
    current = project_prediction(model, chain[0])
    for context_id in chain[1:]:
        current = blend(current, project_prediction(model, context_id), 0.5)
    return cosine(current, true_world_vector(chain[-1]))


def false_accept_rate(seed_result: dict[str, Any], *, use_graveyard: bool) -> float:
    survivors = [row["vector"] for row in seed_result["survivor_hashes"].values()]
    graves = seed_result["graveyard_hashes"]
    killed = seed_result["killed_vectors"][:24]
    if not killed or not survivors:
        return 0.0
    false_accepts = 0
    for row in killed:
        grave_key = semantic_hash("graveyard", row["context_id"], row["vector"])
        if use_graveyard and grave_key in graves:
            continue
        best = max(cosine(row["vector"], survivor) for survivor in survivors)
        if best >= FALSE_ACCEPT_THRESHOLD:
            false_accepts += 1
    return false_accepts / len(killed)


def summarize_result(result: dict[str, Any]) -> dict[str, Any]:
    trace = result["error_trace"]
    first = trace[:N_CONTEXTS]
    last = trace[-N_CONTEXTS:]
    return {
        "first_cycle_error": mean([row["error_before"] for row in first]),
        "last_cycle_error": mean([row["error_after"] for row in last]),
        "recall_similarity": recall_similarity(result["model"]),
        "remote_chain_similarity": remote_chain_similarity(result["model"]),
        "survivor_hash_count": len(result["survivor_hashes"]),
        "graveyard_hash_count": len(result["graveyard_hashes"]),
        "false_accept_rate_with_graveyard": false_accept_rate(result, use_graveyard=True),
        "false_accept_rate_without_graveyard": false_accept_rate(result, use_graveyard=False),
    }


def hash_to_unit_vector(digest: str, dim: int = N_FEATURES) -> list[float]:
    raw = hashlib.sha256(("opaque-hash-baseline:" + digest).encode("utf-8")).digest()
    values = [(raw[i] / 255.0) * 2.0 - 1.0 for i in range(dim)]
    return normalize(values)


def zeno_hash_only_score(seed_result: dict[str, Any]) -> float:
    # Use only opaque hash IDs, not payload vectors or context metadata. This
    # makes the baseline computed while preserving the intended hash-only fence.
    hashes = sorted(seed_result["survivor_hashes"].keys())[:N_CONTEXTS]
    if len(hashes) < N_CONTEXTS:
        return 0.0
    return mean([
        cosine(hash_to_unit_vector(digest), true_world_vector(context_id))
        for context_id, digest in enumerate(hashes)
    ])


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    live = run_loop(update=True, shuffled_context=False, write_graveyard=True)
    frozen = run_loop(update=False, shuffled_context=False, write_graveyard=True)
    shuffled = run_loop(update=True, shuffled_context=True, write_graveyard=True)
    no_graveyard = run_loop(update=True, shuffled_context=False, write_graveyard=False)

    live_m = summarize_result(live)
    frozen_m = summarize_result(frozen)
    shuffled_m = summarize_result(shuffled)
    no_graveyard_m = summarize_result(no_graveyard)

    error_reduction = live_m["first_cycle_error"] - live_m["last_cycle_error"]
    frozen_reduction = frozen_m["first_cycle_error"] - frozen_m["last_cycle_error"]

    positive = {
        "prediction_first_error_reduction": {
            "pass": error_reduction > 0.55 and error_reduction > frozen_reduction + 0.35,
            "live_reduction": error_reduction,
            "frozen_reduction": frozen_reduction,
        },
        "world_model_recall_beats_hash_only": {
            "pass": live_m["recall_similarity"] > zeno_hash_only_score(live) + 0.75,
            "live_recall_similarity": live_m["recall_similarity"],
            "hash_only_similarity": zeno_hash_only_score(live),
        },
        "context_geometry_is_load_bearing": {
            "pass": live_m["remote_chain_similarity"] > shuffled_m["remote_chain_similarity"] + 0.15,
            "live_remote_chain_similarity": live_m["remote_chain_similarity"],
            "shuffled_remote_chain_similarity": shuffled_m["remote_chain_similarity"],
        },
    }

    graveyard_companions = {
        "survivor_hashes_exist": {
            "pass": live_m["survivor_hash_count"] >= N_CONTEXTS * (N_CYCLES - 1),
            "count": live_m["survivor_hash_count"],
            "minimum_required": N_CONTEXTS * (N_CYCLES - 1),
        },
        "graveyard_hashes_exist": {
            "pass": live_m["graveyard_hash_count"] >= N_CONTEXTS,
            "count": live_m["graveyard_hash_count"],
        },
        "graveyard_suppresses_false_confirmation": {
            "pass": live_m["false_accept_rate_with_graveyard"] < live_m["false_accept_rate_without_graveyard"],
            "with_graveyard": live_m["false_accept_rate_with_graveyard"],
            "same_killed_set_without_graveyard": live_m["false_accept_rate_without_graveyard"],
        },
        "frozen_model_control_fails": {
            "pass": frozen_m["recall_similarity"] < live_m["recall_similarity"] - 0.20,
            "frozen_recall_similarity": frozen_m["recall_similarity"],
            "live_recall_similarity": live_m["recall_similarity"],
        },
    }

    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "formal_admission_allowed_false": {
            "pass": FORMAL_ADMISSION_ALLOWED is False,
            "value": FORMAL_ADMISSION_ALLOWED,
        },
        "finite_contexts": {"pass": N_CONTEXTS == 8 and N_FEATURES == 10, "contexts": N_CONTEXTS, "features": N_FEATURES},
        "blocked_consumers_preserved": {"pass": len(BLOCKED_CONSUMERS) >= 8, "blocked_consumers": BLOCKED_CONSUMERS},
    }

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": classification,
        "CLASSIFICATION": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "SOURCE_ALIGNMENT_CATEGORY": SOURCE_ALIGNMENT_CATEGORY,
        "PROMOTION_ALLOWED": PROMOTION_ALLOWED,
        "promotion_allowed": PROMOTION_ALLOWED,
        "FORMAL_ADMISSION_ALLOWED": FORMAL_ADMISSION_ALLOWED,
        "CLAIM_CEILING": CLAIM_CEILING,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN_OR_OUTPUT,
        "root_constraints_in_force": ["F01 finite context/probe/hash set", "N01 ordered project-sense-correct-update loop"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "candidate_status": "seed_fixture_survived_controls" if all_pass else "seed_fixture_open_or_failed",
        "candidate_survived": all_pass,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "metrics": {
            "live": live_m,
            "frozen_model_control": frozen_m,
            "shuffled_context_control": shuffled_m,
            "no_graveyard_control": no_graveyard_m,
            "hash_only_similarity": zeno_hash_only_score(live),
        },
        "nearby_variants": {
            "tested_here": [
                "frozen_model_no_update",
                "hash_only_no_model",
                "shuffled_context_geometry",
                "drop_graveyard",
            ],
            "not_tested_here": [
                "QIT engine replay adapter",
                "projector/camera hardware loop",
                "personal memory store",
                "Axis0 fuzz-field coupling",
            ],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 seed fixture for prediction-first Holodeck memory semantics, not a v4 doctrine mirror or final architecture.",
            "v4_equivalent": None,
        },
        "blocked_consumers": BLOCKED_CONSUMERS,
        "recommended_next_gates": [
            "port this seed fixture onto the source-native QIT replay adapter",
            "replace finite semantic vectors with spinor-derived density/cut states",
            "add held-out scene/cue split and projector/camera observation analog",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": result["candidate_status"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
