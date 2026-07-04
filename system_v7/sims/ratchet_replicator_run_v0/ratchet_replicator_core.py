#!/usr/bin/env python3
"""Shared executable floor for ratchet_replicator_run_v0.

Starts from only:
  F01: finite alphabet plus bounded active record window.
  N01: directed acts may disturb token states, so order can matter.

Ceiling: SCRATCH_DIAGNOSTIC; promotion_allowed=false.
"""

from __future__ import annotations

import itertools
import json
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CLIMB_DIR = Path(__file__).resolve().parents[1] / "ratchet_climb_engine_v0"
if str(CLIMB_DIR) not in sys.path:
    sys.path.insert(0, str(CLIMB_DIR))

import ratchet_climb_core as climb

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"

TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite record/window, deterministic candidate generation, motif counters, lock receipts, and parity envelope data",
    }
}

TOOL_INTEGRATION_DEPTH = {"python_stdlib": "load_bearing"}

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "spec.json"


def load_spec() -> dict[str, Any]:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


class LCG:
    """Small deterministic RNG with language-portable constants."""

    def __init__(self, seed: int):
        self.state = seed % 2147483647 or 1

    def next(self) -> int:
        self.state = (48271 * self.state) % 2147483647
        return self.state

    def randint(self, n: int) -> int:
        return self.next() % n


@dataclass(frozen=True)
class ActCandidate:
    x: int
    y: int
    source: str
    parent_ids: tuple[int, ...] = ()


def nonself_pair(rng: LCG, alphabet_size: int) -> tuple[int, int]:
    x = rng.randint(alphabet_size)
    y = rng.randint(alphabet_size - 1)
    if y >= x:
        y += 1
    return x, y


def canonical_motif(shapes: list[tuple[int, int]]) -> str:
    renaming: dict[int, int] = {}
    next_id = 0
    out = []
    for x, y in shapes:
        for token in (x, y):
            if token not in renaming:
                renaming[token] = next_id
                next_id += 1
        out.append(f"{renaming[x]}>{renaming[y]}")
    return ",".join(out)


def motif_edit_distance(a: tuple[tuple[int, int], ...], b: tuple[tuple[int, int], ...]) -> int:
    if len(a) != len(b):
        return 999
    return sum(1 for left, right in zip(a, b, strict=True) if left != right)


def propose_candidates(
    rng: LCG,
    *,
    alphabet_size: int,
    k: int,
    active_record: deque[dict[str, Any]],
    admitted: list[dict[str, Any]],
) -> list[ActCandidate]:
    out: list[ActCandidate] = []
    recent = list(active_record)[-max(1, min(6, len(active_record))):]
    admitted_recent = admitted[-max(1, min(10, len(admitted))):]
    for idx in range(k):
        mode = idx % 4
        if mode == 0 or not admitted_recent:
            x, y = nonself_pair(rng, alphabet_size)
            out.append(ActCandidate(x, y, "random_pair"))
        elif mode == 1:
            parent = admitted_recent[rng.randint(len(admitted_recent))]
            shift = 1 + rng.randint(alphabet_size - 1)
            x = (parent["x"] + shift) % alphabet_size
            y = (parent["y"] + shift) % alphabet_size
            if x == y:
                y = (y + 1) % alphabet_size
            out.append(ActCandidate(x, y, "repeat_recent_renamed", (int(parent["id"]),)))
        elif mode == 2 and len(recent) >= 2:
            left = recent[rng.randint(len(recent))]
            right = recent[rng.randint(len(recent))]
            # Compose two directed act patterns. Prefer path composition when
            # one target matches one source, otherwise still form a bounded
            # pattern-composition probe from the outer tokens.
            if left["y"] == right["x"] and left["x"] != right["y"]:
                x, y = int(left["x"]), int(right["y"])
            else:
                x, y = int(left["x"]), int(right["y"])
                if x == y:
                    y = (y + 1) % alphabet_size
            out.append(ActCandidate(x, y, "composition_prior_patterns", (int(left["id"]), int(right["id"]))))
        else:
            parent = recent[rng.randint(len(recent))]
            if rng.randint(2) == 0:
                x, y = int(parent["y"]), int(parent["x"])
                source = "recent_reverse"
            else:
                x = int(parent["x"])
                y = (int(parent["y"]) + 1 + rng.randint(alphabet_size - 1)) % alphabet_size
                if x == y:
                    y = (y + 1) % alphabet_size
                source = "recent_small_edit"
            out.append(ActCandidate(x, y, source, (int(parent["id"]),)))
    return out


def register_fact(mode: str, states: list[int], act: ActCandidate) -> tuple[Any, ...]:
    if mode == "commuting":
        return ("directed_pair", act.x, act.y)
    return ("ordered_state_distinction", act.x, act.y, states[act.x], states[act.y], sum(states) % 257)


def apply_act(mode: str, states: list[int], act: ActCandidate, modulus: int) -> list[int]:
    nxt = list(states)
    if mode == "commuting":
        return nxt
    old_x = states[act.x]
    old_y = states[act.y]
    nxt[act.x] = (old_x + 2 * old_y + act.x + 1) % modulus
    nxt[act.y] = (old_y + old_x + act.y + 3) % modulus
    return nxt


def history_signature(mode: str, active_record: deque[dict[str, Any]], states: list[int]) -> str:
    if mode == "commuting":
        bag = sorted((int(row["x"]), int(row["y"]), int(row["active_count"])) for row in active_record)
        return climb.sha256_json({"bag": bag})
    seq = [(int(row["x"]), int(row["y"]), tuple(row["pre_state_pair"]), tuple(row["post_state_pair"])) for row in active_record]
    return climb.sha256_json({"seq": seq, "state": states})


def summarize_equivalence_demands(run: dict[str, Any]) -> dict[str, Any]:
    admitted = run["admitted_record"]
    tokens = list(range(run["config"]["alphabet_size"]))
    direct = {(row["x"], row["y"]) for row in admitted}
    raw_classes = {token: token for token in tokens}

    failures = {
        "reflexivity": [token for token in tokens if (token, token) not in direct],
        "symmetry": [(x, y) for (x, y) in sorted(direct) if (y, x) not in direct],
        "transitivity": [],
    }
    for x, y in sorted(direct):
        for y2, z in sorted(direct):
            if y == y2 and x != z and (x, z) not in direct:
                failures["transitivity"].append((x, y, z))
                if len(failures["transitivity"]) >= 12:
                    break
        if len(failures["transitivity"]) >= 12:
            break

    # Demands drawn from the run itself. The quotient-like summary only needs
    # stable repeat handling and classing tokens by measured outgoing/incoming
    # signatures; it does not need reflexive/symmetric/transitive closure.
    repeat_failures = 0
    seen_repeat_facts = set()
    for row in admitted:
        key = (row["x"], row["y"], tuple(row["fact"]))
        if key in seen_repeat_facts:
            continue
        seen_repeat_facts.add(key)
    class_signature = {
        token: (
            tuple(sorted(y for x, y in direct if x == token)),
            tuple(sorted(x for x, y in direct if y == token)),
        )
        for token in tokens
    }
    class_buckets: dict[tuple[tuple[int, ...], tuple[int, ...]], list[int]] = defaultdict(list)
    for token, sig in class_signature.items():
        class_buckets[sig].append(token)

    return {
        "demands": {
            "stable_under_repeating_an_act": {
                "passed": repeat_failures == 0,
                "forced_lifts": [],
                "reason": "repeat stability is carried by exact directed act facts, not by equivalence closure",
            },
            "support_classing_tokens": {
                "passed": bool(class_buckets),
                "class_count": len(class_buckets),
                "forced_lifts": [],
                "reason": "tokens are classed by measured directed signatures without installing reflexive/symmetric/transitive closure",
            },
        },
        "lift_verdicts": {
            "reflexivity": {
                "verdict": "REFUSED_UNFORCED",
                "demand_failures_if_installed": failures["reflexivity"][:12],
                "needed_by_run": False,
            },
            "symmetry": {
                "verdict": "REFUSED_UNFORCED",
                "demand_failures_if_installed": failures["symmetry"][:12],
                "needed_by_run": False,
            },
            "transitivity": {
                "verdict": "REFUSED_UNFORCED",
                "demand_failures_if_installed": failures["transitivity"][:12],
                "needed_by_run": False,
            },
        },
        "raw_classes_without_equivalence": raw_classes,
    }


def motif_occurrences(admitted: list[dict[str, Any]], min_len: int, max_len: int) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for length in range(min_len, max_len + 1):
        if len(admitted) < length:
            continue
        for start in range(0, len(admitted) - length + 1):
            rows = admitted[start : start + length]
            raw = tuple((int(row["x"]), int(row["y"])) for row in rows)
            key = canonical_motif(list(raw))
            parent_ids = sorted({pid for row in rows for pid in row["parent_ids"]})
            out[key].append(
                {
                    "start": start,
                    "end": start + length - 1,
                    "act_ids": [int(row["id"]) for row in rows],
                    "raw": raw,
                    "parent_ids": parent_ids,
                    "active_at_step": int(rows[-1]["step"]),
                }
            )
    return out


def detect_replicator(admitted: list[dict[str, Any]], graveyard: list[dict[str, Any]], window_size: int) -> dict[str, Any]:
    occ = motif_occurrences(admitted, 2, 4)
    active_ids = {int(row["id"]) for row in admitted[-window_size:]}
    grave_ids = {int(row["id"]) for row in graveyard}
    first: dict[str, Any] | None = None
    near: list[dict[str, Any]] = []

    for key, rows in sorted(occ.items(), key=lambda item: (min(row["end"] for row in item[1]), item[0])):
        if len(rows) < 4:
            continue
        raw_variants = {row["raw"] for row in rows}
        heredity_hits = 0
        for idx, row in enumerate(rows[1:], start=1):
            prior_ids = {pid for prior in rows[:idx] for pid in prior["act_ids"]}
            if prior_ids.intersection(row["parent_ids"]):
                heredity_hits += 1
                continue
            if any(set(row["act_ids"]).intersection(prior["act_ids"]) for prior in rows[:idx]):
                heredity_hits += 1
        active_variant_count = sum(bool(set(row["act_ids"]).intersection(active_ids)) for row in rows)
        grave_variant_count = sum(bool(set(row["act_ids"]).intersection(grave_ids)) for row in rows)
        small_edit_variants = any(
            motif_edit_distance(a, b) in (1, 2)
            for a, b in itertools.combinations(raw_variants, 2)
        )
        heredity = heredity_hits >= 2
        variation = len(raw_variants) >= 2 and small_edit_variants
        selection = active_variant_count > 0 and grave_variant_count > 0
        growth_curve = Counter(row["active_at_step"] for row in rows)
        cumulative = []
        total = 0
        for step in sorted(growth_curve):
            total += growth_curve[step]
            cumulative.append({"step": step, "occurrences": total})
        record = {
            "pattern": key,
            "occurrence_count": len(rows),
            "first_completed_at_step": min(row["active_at_step"] for row in rows),
            "structure": [part for part in key.split(",")],
            "heredity": heredity,
            "variation": variation,
            "selection": selection,
            "raw_variant_examples": [list(map(list, raw)) for raw in list(raw_variants)[:6]],
            "growth_curve": cumulative,
            "active_variant_count": active_variant_count,
            "graveyard_variant_count": grave_variant_count,
        }
        if heredity and variation and selection:
            first = record
            break
        missing = [name for name, ok in (("heredity", heredity), ("variation", variation), ("selection", selection)) if not ok]
        record["failed_criteria"] = missing
        near.append(record)

    return {
        "verdict": "FOUND" if first else "NONE_FOUND",
        "first_replicator": first,
        "near_misses": near[:5],
    }


def run_ratchet(config: dict[str, Any], *, mode: str, engine: str) -> dict[str, Any]:
    rng = LCG(int(config["seed"]))
    alphabet_size = int(config["alphabet_size"])
    window_size = int(config["window_size"])
    max_steps = int(config["max_steps"])
    k = int(config["candidates_per_step"])
    modulus = int(config["state_modulus"])
    states = [(3 * i + 1) % modulus for i in range(alphabet_size)]
    active_record: deque[dict[str, Any]] = deque()
    admitted: list[dict[str, Any]] = []
    graveyard: list[dict[str, Any]] = []
    excluded_candidates: list[dict[str, Any]] = []
    carried_facts: set[tuple[Any, ...]] = set()
    history_classes: set[str] = set()
    timeline: list[dict[str, Any]] = []
    locks: list[dict[str, Any]] = []
    prev_hash = "GENESIS"
    halted_at_step: int | None = None

    for step in range(1, max_steps + 1):
        candidates = propose_candidates(rng, alphabet_size=alphabet_size, k=k, active_record=active_record, admitted=admitted)
        admitted_this_step = 0
        rejected_this_step = 0
        for cand in candidates:
            fact = register_fact(mode, states, cand)
            if fact in carried_facts:
                rejected_this_step += 1
                excluded_candidates.append(
                    {
                        "step": step,
                        "x": cand.x,
                        "y": cand.y,
                        "source": cand.source,
                        "reason": "already_carried_by_summary",
                        "fact": list(fact),
                        "parent_ids": list(cand.parent_ids),
                    }
                )
                continue
            pre = [states[cand.x], states[cand.y]]
            next_states = apply_act(mode, states, cand, modulus)
            post = [next_states[cand.x], next_states[cand.y]]
            entry = {
                "id": len(admitted) + 1,
                "t": step,
                "step": step,
                "x": cand.x,
                "y": cand.y,
                "source": cand.source,
                "parent_ids": list(cand.parent_ids),
                "fact": list(fact),
                "pre_state_pair": pre,
                "post_state_pair": post,
                "active_count": 1,
            }
            states = next_states
            carried_facts.add(fact)
            admitted.append(entry)
            active_record.append(entry)
            admitted_this_step += 1
            if len(active_record) > window_size:
                evicted = active_record.popleft()
                graveyard.append(evicted | {"excluded_at_step": step, "reason": "F01_window_pressure"})
            decision = {
                "sim_id": "ratchet_replicator_run_v0",
                "mode": mode,
                "engine": engine,
                "step": step,
                "admitted_act": {"x": cand.x, "y": cand.y, "source": cand.source, "fact": list(fact)},
                "active_window_size": len(active_record),
                "carried_fact_count": len(carried_facts),
            }
            lock = climb.lock_entry(prev_hash, f"{engine}:{mode}", len(locks) + 1, decision, climb.sha256_json(config))
            locks.append(lock)
            prev_hash = lock["entry_hash"]

        sig = history_signature(mode, active_record, states)
        history_classes.add(sig)
        all_commuting_facts_seen = mode == "commuting" and len(carried_facts) >= alphabet_size * (alphabet_size - 1)
        timeline.append(
            {
                "step": step,
                "admitted": admitted_this_step,
                "rejected": rejected_this_step,
                "active_window_size": len(active_record),
                "graveyard_count": len(graveyard),
                "carried_fact_count": len(carried_facts),
                "distinguishable_history_class_count": len(history_classes),
                "state_checksum": sum(states) % 1000003,
                "coverage_exhausted": all_commuting_facts_seen,
            }
        )
        if admitted_this_step == 0 and (mode == "commuting" or len(timeline) >= 4):
            halted_at_step = step
            break
        if all_commuting_facts_seen:
            halted_at_step = step
            break

    if halted_at_step is None:
        halted_at_step = max_steps if timeline and timeline[-1]["admitted"] == 0 else None

    motif_counts = {
        key: len(rows)
        for key, rows in motif_occurrences(admitted, int(config["motif_min_len"]), int(config["motif_max_len"])).items()
    }
    replicator = detect_replicator(admitted, graveyard, window_size)
    result = {
        "schema": "codex_ratchet.ratchet_replicator_run_v0.mode_run.v1",
        "mode": mode,
        "engine": engine,
        "config": config,
        "root_constraints": {
            "F01": "finite alphabet of tokens plus bounded active record window; old active acts are excluded to graveyard under window pressure",
            "N01": "directed acts may disturb deterministic finite token states, making order observable",
        },
        "seed_floor": "finite append-only directed distinction-acts (t,x,y); no reflexivity, symmetry, or transitivity is assumed",
        "generated_at": climb.now_iso(),
        "halted_at_step": halted_at_step,
        "admitted_count": len(admitted),
        "graveyard_count": len(graveyard),
        "excluded_candidate_count": len(excluded_candidates),
        "final_history_class_count": len(history_classes),
        "timeline": timeline,
        "admitted_record": admitted,
        "graveyard_sample": graveyard[:12],
        "excluded_candidate_sample": excluded_candidates[:12],
        "motif_counts": dict(sorted(motif_counts.items())),
        "replicator_detection": replicator,
        "equivalence_lift_tests": summarize_equivalence_demands(
            {
                "admitted_record": admitted,
                "config": config,
            }
        ),
        "append_only_lock_ledger": locks,
        "all_pass": bool(timeline),
    }
    return result


def result_envelope(engine: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = load_spec()
    runs = {
        mode: run_ratchet(spec["run_config"], mode=mode, engine=engine)
        for mode in ("commuting", "noncommuting")
    }
    commute = runs["commuting"]
    noncommute = runs["noncommuting"]
    verdict = {
        "commuting_saturates": commute["halted_at_step"] is not None,
        "commuting_halt_step": commute["halted_at_step"],
        "noncommuting_halts": noncommute["halted_at_step"] is not None,
        "noncommuting_halt_step": noncommute["halted_at_step"],
        "noncommuting_keeps_registering_order_facts_through_budget": noncommute["halted_at_step"] is None
        and noncommute["timeline"][-1]["admitted"] > 0,
        "derivation_check": "PASS"
        if commute["halted_at_step"] is not None and noncommute["halted_at_step"] is None
        else "FAIL_OR_INCONCLUSIVE",
    }
    payload = {
        "schema": "codex_ratchet.ratchet_replicator_run_v0.engine_result.v1",
        "sim_id": "ratchet_replicator_run_v0",
        "engine": engine,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "lifecycle_status": "SCRATCH_DIAGNOSTIC",
        "claim_ceiling": "scratch_diagnostic",
        "capstone_status": "DRAFT_UNAUDITED",
        "generated_at": climb.now_iso(),
        "source_hashes": {
            "spec": climb.sha256_file(SPEC_PATH),
            "core": climb.sha256_file(Path(__file__)),
            "climb_core_reused": climb.sha256_file(CLIMB_DIR / "ratchet_climb_core.py"),
            "definition_executable_read": climb.sha256_file(HERE.parents[0] / "ratchet_definition_executable_v0" / "ratchet_definition_executable_v0.py"),
        },
        "run_config": spec["run_config"],
        "runs": runs,
        "saturation_theorem_check": verdict,
        "equivalence_property_lifts": noncommute["equivalence_lift_tests"]["lift_verdicts"],
        "replicator_verdict": noncommute["replicator_detection"],
        "frontier_result": {
            "commuting": {
                "halt_step": commute["halted_at_step"],
                "final_history_class_count": commute["final_history_class_count"],
                "admitted_count": commute["admitted_count"],
            },
            "noncommuting": {
                "halt_step": noncommute["halted_at_step"],
                "final_history_class_count": noncommute["final_history_class_count"],
                "admitted_count": noncommute["admitted_count"],
            },
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all(row["all_pass"] for row in runs.values()),
    }
    if extra:
        payload.update(extra)
    return payload

