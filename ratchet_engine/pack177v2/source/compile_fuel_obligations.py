#!/usr/bin/env python3
"""Compile source-anonymous residual pressure into fair Ratchet obligations.

This is deliberately narrower than a successor engine.  It consumes the exact
r3-r6 receipts already produced by the source-balanced calibration and makes
the missing fuel explicit:

* continuation conflicts;
* held-out candidate kills;
* plural surviving completions/quotients; and
* incomplete source runtimes.

It emits no scalar score and never reads source-family or owner-hypothesis
labels while constructing mathematical obligations.  A separate unranked
proposal projection preserves the complete fuel registry.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT / "receipts"
REGISTRY = ROOT / "fuel" / "FUEL_REGISTRY.json"
FEATURES = ("h0", "h1", "p")
MONOMIALS: tuple[tuple[str, ...], ...] = (
    (),
    ("h0",),
    ("h1",),
    ("p",),
    ("h0", "h1"),
    ("h0", "p"),
    ("h1", "p"),
    ("h0", "h1", "p"),
)


def load(name: str) -> dict[str, Any]:
    value = json.loads((RECEIPTS / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a JSON object")
    return value


def dump(name: str, value: dict[str, Any]) -> None:
    (RECEIPTS / name).write_text(
        json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )


def eval_anf(mask: int, context: dict[str, int]) -> int:
    result = 0
    for index, monomial in enumerate(MONOMIALS):
        if not mask & (1 << index):
            continue
        term = 1
        for name in monomial:
            term &= context[name]
        result ^= term
    return result


def discriminating_contexts(masks: list[int]) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    for bits in itertools.product((0, 1), repeat=3):
        context = dict(zip(FEATURES, bits, strict=True))
        outputs: dict[int, list[int]] = {0: [], 1: []}
        for mask in masks:
            outputs[eval_anf(mask, context)].append(mask)
        if outputs[0] and outputs[1]:
            contexts.append(
                {
                    "context": [context[name] for name in FEATURES],
                    "zero_survivors": outputs[0],
                    "one_survivors": outputs[1],
                }
            )
    return contexts


def full_context_row(analysis: dict[str, Any]) -> dict[str, Any]:
    hits = [
        row
        for row in analysis["coordinate_refinement_lattice"]
        if row.get("features") == list(FEATURES)
    ]
    if len(hits) != 1:
        raise ValueError("expected exactly one full-context quotient row")
    return hits[0]


def add_obligation(
    obligations: list[dict[str, Any]],
    handle: str,
    kind: str,
    reason: str,
    required_return: list[str],
    forbidden_substitutions: list[str],
) -> None:
    ordinal = len(obligations)
    obligations.append(
        {
            "obligation_id": f"{handle}:o{ordinal}:{kind}",
            "kind": kind,
            "reason": reason,
            "required_return": required_return,
            "forbidden_substitutions": forbidden_substitutions,
            "mathematical_status": "UNRESOLVED",
        }
    )


def compile_source(
    r3: dict[str, Any], r5: dict[str, Any], r6: dict[str, Any]
) -> dict[str, Any]:
    handle = str(r6["handle"])
    analysis = r6["full_recompute"]
    full = full_context_row(analysis)
    geometry = full["geometry_view"]
    entropy = full["entropy_view"]
    masks = [int(mask) for mask in analysis["anf_exact_survivor_masks"]]
    killed = len(r5["purgatory_events"])
    antichain = analysis["minimal_sufficient_coordinate_antichain"]
    runtime_errors = int(r3["source_runtime_error_count"])
    relation_only = not bool(masks)

    pressure = {
        "continuation_conflict_contexts": int(geometry["conflict_context_count"]),
        "distinction_violation_pairs": int(geometry["distinction_violation_pair_count"]),
        "unresolved_branch_excess": int(entropy["unresolved_excess"]),
        "heldout_candidate_kills": killed,
        "surviving_deterministic_completions": len(masks),
        "minimal_quotient_antichain_size": len(antichain),
        "source_runtime_errors": runtime_errors,
        "relation_only": relation_only,
    }
    active = []
    if pressure["continuation_conflict_contexts"]:
        active.append("CONTINUATION_CONFLICT")
    if pressure["heldout_candidate_kills"]:
        active.append("HELDOUT_KILL")
    if len(masks) > 1 or len(antichain) > 1:
        active.append("PLURAL_SURVIVORS")
    if runtime_errors:
        active.append("SOURCE_RUNTIME_GAP")

    obligations: list[dict[str, Any]] = []
    if relation_only:
        add_obligation(
            obligations,
            handle,
            "PRESERVE_AND_CHALLENGE_RELATION",
            "Identical returned full contexts have plural observed continuations; no Boolean function over the returned coordinates closes.",
            [
                "fresh source-native continuation records",
                "relation edge-deletion witnesses",
                "recomputed quotient and completion frontier",
            ],
            [
                "choosing one continuation",
                "inventing a coordinate from source identity",
                "calling a relation failure noise without a source control",
            ],
        )
        add_obligation(
            obligations,
            handle,
            "MEASURE_COORDINATE_OR_LONGER_HISTORY",
            "The current returned quotient predicts less than the observed continuation relation.",
            [
                "one independently measured coordinate or a longer source-native history",
                "ablation proving that the added distinction closes at least one measured conflict",
                "held-out test under the expanded context",
            ],
            [
                "source-family label as a feature",
                "owner-hypothesis label as a feature",
                "fabricated phase, spinor, bracket, or geometry field",
            ],
        )
        add_obligation(
            obligations,
            handle,
            "COMPETE_FINITE_TRANSDUCER",
            "A finite history-dependent update is a lower-assumption rival to forcing a memoryless function.",
            [
                "bounded transducer grammar",
                "MSS frontier against the retained relation and longer-coordinate rival",
                "state-deletion and held-out continuation controls",
            ],
            ["unbounded hidden state", "hand-authored target states", "raw-row accuracy ranking"],
        )
    elif len(masks) > 1:
        contexts = discriminating_contexts(masks)
        add_obligation(
            obligations,
            handle,
            "DISCRIMINATE_DETERMINISTIC_COMPLETIONS",
            "Several exact deterministic completions survive the returned records.",
            [
                "source execution at one or more listed distinguishing Boolean contexts",
                "held-out result before selector access",
                "full frontier recomputation with killed candidates sent to Purgatory",
            ],
            ["lowest mask as truth", "degree-only admission", "owner-label tie break"],
        )
        obligations[-1]["candidate_discriminating_contexts"] = contexts

    if len(antichain) > 1:
        add_obligation(
            obligations,
            handle,
            "RESOLVE_OR_RETAIN_QUOTIENT_ANTICHAIN",
            "Several incomparable minimally sufficient coordinate sets survive.",
            [
                "new probe or continuation that separates quotient predictions",
                "all incomparable minima retained if no separator exists",
                "coordinate deletion witnesses after recomputation",
            ],
            ["single hidden complexity scalar", "lexical coordinate preference"],
        )

    if killed:
        add_obligation(
            obligations,
            handle,
            "RETAIN_PURGATORY_AND_REOFFER",
            "Held-out records killed train-stage completions and changed the candidate space.",
            [
                "immutable kill receipts",
                "universal eligibility after a material context change",
                "dependency-aware selective rerun receipt",
            ],
            ["permanent deletion", "automatic resurrection", "candidate-count entropy as truth"],
        )

    if runtime_errors:
        add_obligation(
            obligations,
            handle,
            "REPAIR_SOURCE_RUNTIME_AND_RERUN",
            "The projection is mathematically usable at its declared ceiling, but its full source runtime reported errors.",
            [
                "authorized local source-runtime repair in an isolated worktree",
                "fresh raw execution receipt",
                "comparison against the inherited projection",
            ],
            ["promotion from projection alone", "fixture renamed fresh run", "canonical worktree mutation"],
        )

    if not obligations:
        add_obligation(
            obligations,
            handle,
            "PERTURB_AND_DELETE_UNIQUE_COMPLETION",
            "No current residual component is active; uniqueness must still survive explicit perturbation and deletion controls.",
            ["feature deletion", "new continuation", "recomputed uniqueness receipt"],
            ["claiming universality from one closed packet"],
        )

    return {
        "handle": handle,
        "pressure_vector": pressure,
        "active_pressure_dimensions": active,
        "obligations": obligations,
        "scalar_priority_score": None,
    }


def fair_schedule(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Round-robin all source obligations; hashes break logistical ties only."""
    ordered = sorted(
        sources,
        key=lambda row: hashlib.sha256(row["handle"].encode("utf-8")).hexdigest(),
    )
    queue: list[dict[str, Any]] = []
    max_depth = max(len(row["obligations"]) for row in ordered)
    for round_index in range(max_depth):
        for source in ordered:
            if round_index >= len(source["obligations"]):
                continue
            obligation = source["obligations"][round_index]
            queue.append(
                {
                    "queue_index": len(queue),
                    "fair_round": round_index,
                    "handle": source["handle"],
                    "obligation_id": obligation["obligation_id"],
                    "kind": obligation["kind"],
                    "epistemic_priority": None,
                }
            )
    return queue


def run() -> None:
    r3 = load("r3_projection_eligibility.json")
    r5 = load("r5_heldout_reoffer.json")
    r6 = load("r6_full_recompute.json")
    by3 = {row["handle"]: row for row in r3["sources"]}
    by5 = {row["handle"]: row for row in r5["sources"]}
    by6 = {row["handle"]: row for row in r6["sources"]}
    handles = sorted(by6)
    if set(handles) != set(by3) or set(handles) != set(by5):
        raise ValueError("r3/r5/r6 source handles do not agree")
    sources = [compile_source(by3[h], by5[h], by6[h]) for h in handles]
    obligations = {
        "schema_version": "ratchet.fuel-obligations/0.2",
        "kind": "anonymous_residual_pressure_and_typed_next_work",
        "source_count": len(sources),
        "pressure_is_vector_not_scalar": True,
        "source_labels_present": False,
        "owner_hypothesis_labels_present": False,
        "sources": sources,
        "every_source_has_obligation": all(row["obligations"] for row in sources),
        "status": "EXECUTED_RESIDUAL_TO_OBLIGATION_COMPILATION",
        "claim_ceiling": "Packet-relative work compiler; no source claim, ontology, owner hypothesis, physics, or engine admitted.",
    }
    queue = fair_schedule(sources)
    schedule = {
        "schema_version": "ratchet.fuel-schedule-projection/0.2",
        "kind": "source_fair_round_robin_logistical_projection",
        "queue": queue,
        "obligation_count": len(queue),
        "all_obligations_scheduled_once": len(queue)
        == sum(len(row["obligations"]) for row in sources),
        "epistemic_score_used": False,
        "native_leviathan_ingested": False,
        "status": "PROJECTION_READY__NATIVE_LEV_NOT_RUN_HERE",
    }

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries = registry["entries"]
    proposal_projection = {
        "schema_version": "ratchet.proposal-fuel-projection/0.2",
        "kind": "unranked_complete_registry_projection",
        "entry_count": len(entries),
        "entries": [
            {
                "id": row["id"],
                "layer": row["layer"],
                "status": row["status"],
                "executable_surface": row["executable_surface"],
                "evidence_license": row["evidence_license"],
                "epistemic_priority": None,
            }
            for row in entries
        ],
        "all_registry_entries_retained": True,
        "selector_access": False,
        "status": "UNRANKED_PROPOSAL_FUEL_PRESERVED",
    }
    dump("fuel_obligations.json", obligations)
    dump("fuel_schedule_projection.json", schedule)
    dump("proposal_fuel_projection.json", proposal_projection)


def validate() -> list[str]:
    failures: list[str] = []
    names = (
        "fuel_obligations.json",
        "fuel_schedule_projection.json",
        "proposal_fuel_projection.json",
    )
    for name in names:
        if not (RECEIPTS / name).is_file():
            failures.append(f"missing {name}")
    if failures:
        return failures
    obligations = load("fuel_obligations.json")
    schedule = load("fuel_schedule_projection.json")
    proposal = load("proposal_fuel_projection.json")
    provenance = load("provenance_map.json")
    source_blob = json.dumps(obligations, sort_keys=True)
    forbidden_labels = [row["family_id"] for row in provenance["sources"]]
    if any(label in source_blob for label in forbidden_labels):
        failures.append("source-family label leaked into mathematical obligations")
    if obligations.get("source_count") != 8:
        failures.append("expected eight anonymous source obligations")
    if obligations.get("pressure_is_vector_not_scalar") is not True:
        failures.append("pressure vector contract missing")
    if obligations.get("every_source_has_obligation") is not True:
        failures.append("an anonymous source has no next obligation")
    if any(row.get("scalar_priority_score") is not None for row in obligations["sources"]):
        failures.append("scalar source priority detected")
    all_ids = {
        item["obligation_id"]
        for row in obligations["sources"]
        for item in row["obligations"]
    }
    scheduled_ids = [row["obligation_id"] for row in schedule["queue"]]
    if set(scheduled_ids) != all_ids or len(scheduled_ids) != len(all_ids):
        failures.append("fair schedule does not cover every obligation exactly once")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if proposal.get("entry_count") != len(registry["entries"]):
        failures.append("proposal projection dropped registry entries")
    if proposal.get("selector_access") is not False:
        failures.append("proposal registry exposed to selector")
    forbidden_imports = ("import numpy", "from numpy")
    for path in ROOT.rglob("*.py"):
        source = path.read_text(encoding="utf-8", errors="ignore")
        if any(
            line.lstrip().startswith(prefix)
            for line in source.splitlines()
            for prefix in forbidden_imports
        ):
            failures.append(f"NumPy import on Python claim path: {path.relative_to(ROOT)}")
    return failures


def self_test() -> None:
    context = {"h0": 1, "h1": 0, "p": 1}
    if eval_anf(0, context) != 0:
        raise AssertionError("zero ANF failed")
    if eval_anf(2, context) != 1:
        raise AssertionError("h0 ANF failed")
    if eval_anf(8, context) != 1:
        raise AssertionError("p ANF failed")
    if not discriminating_contexts([0, 1]):
        raise AssertionError("constant functions should be distinguishable")
    synthetic = [
        {"handle": "a", "obligations": [{"obligation_id": "a0", "kind": "x"}, {"obligation_id": "a1", "kind": "y"}]},
        {"handle": "b", "obligations": [{"obligation_id": "b0", "kind": "x"}]},
    ]
    queue = fair_schedule(synthetic)
    if {row["obligation_id"] for row in queue} != {"a0", "a1", "b0"}:
        raise AssertionError("fair scheduler dropped an obligation")


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--validate", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print(json.dumps({"ok": True, "self_test": "PASS"}, indent=2))
        return 0
    if args.run:
        run()
        print(json.dumps({"ok": True, "run": "PASS"}, indent=2))
        return 0
    failures = validate()
    print(json.dumps({"ok": not failures, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
