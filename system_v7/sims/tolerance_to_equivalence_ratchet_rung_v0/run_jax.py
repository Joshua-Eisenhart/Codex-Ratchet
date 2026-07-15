#!/usr/bin/env python3
"""Independent JAX exhaustive lane for the first tolerance/equivalence rung."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import jax
import jax.numpy as jnp


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "jax": {
        "used": True,
        "reason": "JAX arrays, vmap, and lax fixed-point updates execute the exhaustive closure and census lane.",
    },
}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing"}

jax.config.update("jax_enable_x64", True)
SIM_DIR = Path(__file__).resolve().parent
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = SIM_DIR / "results" / "jax_results.json"
EXPECTED = {
    "1": {"tolerances": 1, "equivalences": 1, "nontransitive": 0},
    "2": {"tolerances": 2, "equivalences": 2, "nontransitive": 0},
    "3": {"tolerances": 8, "equivalences": 5, "nontransitive": 3},
    "4": {"tolerances": 64, "equivalences": 15, "nontransitive": 49},
    "5": {"tolerances": 1024, "equivalences": 52, "nontransitive": 972},
}


def relation_from_mask(n: int, mask: jax.Array) -> jax.Array:
    relation = jnp.eye(n, dtype=jnp.bool_)
    bit = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            value = ((mask >> bit) & 1) == 1
            relation = relation.at[i, j].set(value)
            relation = relation.at[j, i].set(value)
            bit += 1
    return relation


def relation_from_edges(n: int, edges: list[list[int]]) -> jax.Array:
    relation = jnp.eye(n, dtype=jnp.bool_)
    for i, j in edges:
        relation = relation.at[i, j].set(True)
        relation = relation.at[j, i].set(True)
    return relation


def is_transitive(relation: jax.Array) -> jax.Array:
    violations = relation[:, :, None] & relation[None, :, :] & ~relation[:, None, :]
    return ~jnp.any(violations)


def closure(relation: jax.Array) -> jax.Array:
    n = relation.shape[0]

    def step(k: int, current: jax.Array) -> jax.Array:
        return current | (current[:, k, None] & current[k, None, :])

    return jax.lax.fori_loop(0, n, step, relation)


def normalized_labels(relation: list[list[bool]]) -> list[int]:
    rows: list[tuple[bool, ...]] = []
    labels: list[int] = []
    for row in relation:
        key = tuple(row)
        if key not in rows:
            rows.append(key)
        labels.append(rows.index(key))
    return labels


def census(n: int) -> dict[str, int]:
    total = 1 << (n * (n - 1) // 2)
    masks = jnp.arange(total, dtype=jnp.int32)
    matrices = jax.vmap(lambda mask: relation_from_mask(n, mask))(masks)
    transitive = jax.jit(jax.vmap(is_transitive))(matrices)
    equivalences = int(jnp.sum(transitive))
    return {"tolerances": total, "equivalences": equivalences, "nontransitive": total - equivalences}


def relation_contains(candidate: list[list[bool]], raw: list[list[bool]]) -> bool:
    return all((not raw[i][j]) or candidate[i][j] for i in range(len(raw)) for j in range(len(raw)))


def added_pairs(candidate: list[list[bool]], raw: list[list[bool]]) -> int:
    return sum(candidate[i][j] and not raw[i][j] for i in range(len(raw)) for j in range(i + 1, len(raw)))


def mss_antichain(raw_array: jax.Array) -> list[dict[str, object]]:
    n = raw_array.shape[0]
    raw = [[bool(x) for x in row] for row in raw_array.tolist()]
    candidates: list[dict[str, object]] = []
    for mask in range(1 << (n * (n - 1) // 2)):
        matrix_array = relation_from_mask(n, jnp.asarray(mask, dtype=jnp.int32))
        if not bool(is_transitive(matrix_array)):
            continue
        matrix = [[bool(x) for x in row] for row in matrix_array.tolist()]
        if relation_contains(matrix, raw):
            labels = normalized_labels(matrix)
            candidates.append(
                {
                    "labels": labels,
                    "added_pair_count": added_pairs(matrix, raw),
                    "quotient_class_count": len(set(labels)),
                }
            )
    survivors = [
        candidate
        for candidate in candidates
        if not any(
            other is not candidate
            and int(other["added_pair_count"]) <= int(candidate["added_pair_count"])
            and int(other["quotient_class_count"]) <= int(candidate["quotient_class_count"])
            and (
                int(other["added_pair_count"]) < int(candidate["added_pair_count"])
                or int(other["quotient_class_count"]) < int(candidate["quotient_class_count"])
            )
            for other in candidates
        )
    ]
    return sorted(survivors, key=lambda x: (x["added_pair_count"], x["quotient_class_count"], x["labels"]))


def coface_loss(labels: list[int], demand_edges: list[list[int]]) -> int:
    return sum(labels[i] == labels[j] for i, j in demand_edges)


def drive_record() -> dict[str, object]:
    raw = relation_from_edges(4, [[0, 1], [2, 3]])
    closed = closure(raw)
    closed_list = [[bool(x) for x in row] for row in closed.tolist()]
    proposal = normalized_labels(closed_list)
    initial = [0, 0, 0, 0]
    demand = [[1, 2]]
    scrambled = [[0, 1]]
    initial_loss = coface_loss(initial, demand)
    proposal_loss = coface_loss(proposal, demand)
    drive = initial_loss - proposal_loss
    reverse_drive = proposal_loss - initial_loss
    null_drive = coface_loss(initial, []) - coface_loss(proposal, [])
    universal = [0] * len(initial)
    universal_drive = initial_loss - coface_loss(universal, demand)
    scrambled_drive = coface_loss(initial, scrambled) - coface_loss(proposal, scrambled)
    flat_drive = coface_loss(proposal, demand) - coface_loss(proposal, demand)
    return {
        "raw_closure": closed_list,
        "initial_labels": initial,
        "proposal_labels": proposal,
        "initial_coface_loss": initial_loss,
        "proposal_coface_loss": proposal_loss,
        "drive": drive,
        "decision": "COMMIT_TOOTH" if drive > 0 else "HOLD",
        "controls": {
            "reverse_drive": reverse_drive,
            "reverse_decision": "COMMIT_TOOTH" if reverse_drive > 0 else "HOLD",
            "null_drive": null_drive,
            "null_decision": "COMMIT_TOOTH" if null_drive > 0 else "HOLD",
            "universal_proposal_drive": universal_drive,
            "universal_proposal_decision": "COMMIT_TOOTH" if universal_drive > 0 else "HOLD",
            "scrambled_drive": scrambled_drive,
            "scrambled_decision": "COMMIT_TOOTH" if scrambled_drive > 0 else "HOLD",
            "flat_drive": flat_drive,
            "flat_decision": "COMMIT_TOOTH" if flat_drive > 0 else "HOLD",
        },
        "mss_antichain": mss_antichain(raw),
    }


def main() -> int:
    observed = {str(n): census(n) for n in range(1, 6)}
    chain = relation_from_edges(3, [[0, 1], [1, 2]])
    chain_closed = closure(chain)
    chain_matrix = [[bool(x) for x in row] for row in chain_closed.tolist()]
    chain_labels = normalized_labels(chain_matrix)
    drive = drive_record()
    controls = drive["controls"]
    all_pass = bool(
        observed == EXPECTED
        and not bool(is_transitive(chain))
        and chain_matrix[0][2]
        and chain_labels == [0, 0, 0]
        and drive["proposal_labels"] == [0, 0, 1, 1]
        and drive["drive"] == 1
        and drive["decision"] == "COMMIT_TOOTH"
        and controls["reverse_drive"] < 0
        and controls["null_drive"] == 0
        and controls["universal_proposal_drive"] == 0
        and controls["scrambled_drive"] == 0
        and len(drive["mss_antichain"]) == 2
    )
    result = {
        "schema": "codex_ratchet.tolerance_to_equivalence.engine_result.v1",
        "sim_id": "tolerance_to_equivalence_ratchet_rung_v0",
        "engine": "jax",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "reads_peer_result": False,
        "source_path": str(SOURCE_PATH.relative_to(SIM_DIR.parents[2])),
        "source_sha256": hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest(),
        "runtime": {"jax_version": jax.__version__, "backend": jax.default_backend(), "x64": bool(jax.config.x64_enabled)},
        "packages_used": ["jax", "jax.numpy"],
        "aligned_packages_load_bearing": ["jax", "jax.numpy", "jax.vmap", "jax.lax.fori_loop"],
        "census": observed,
        "transitivity_witness": {
            "raw_transitive": bool(is_transitive(chain)),
            "closure_labels": chain_labels,
            "forced_endpoint_related": chain_matrix[0][2],
            "closure_matrix": chain_matrix,
        },
        "drive_fixture": drive,
        "all_pass": all_pass,
        "claim_ceiling": "one frozen finite tolerance-to-equivalence scratch rung only",
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"JAX_TOLERANCE_RUNG_DONE all_pass={str(all_pass).lower()} drive={drive['drive']} mss={len(drive['mss_antichain'])}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
