#!/usr/bin/env python3
"""Independent fail-closed controller for the v1 behavioral-object packet.

The controller reconstructs the finite semantics without importing an engine
builder. Artifact validity is separate from scientific success: the frozen
per-seed and shuffled-label failures remain red, and T9 remains unearned.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[3]
SIM_ID = "finite_probe_behavioral_object_engine_v1"
STATE_COUNT = 64
RING_SIZE = 6
PAIR_COUNT = STATE_COUNT * STATE_COUNT
EXPECTED_ORBIT_COUNT = 88
GROUPS = ("train", "validation", "test_primary", "test_structural_holdout")
EXPECTED_COUNTS = {"train": 64, "validation": 16, "test_primary": 14, "test_structural_holdout": 2}
ORBIT_BLOCKS = {
    "train": set(range(0, 60)),
    "validation": set(range(60, 74)),
    "test_primary": set(range(74, 88)),
    "test_structural_holdout": set(range(74, 88)),
}
KNOWN_PYTORCH_REDS = {
    "every_seed_macro_mcc_at_least_0_35",
    "shuffled_training_label_test_mcc_at_most_0_05",
}
T9_FIELDS = {"role_contribution", "runtime_replaceability", "resource_advantage", "diversity_gain", "claim_ceiling"}

SPEC_PATH = ROOT / "spec.json"
PREREG_PATH = ROOT / "preregistration_receipt.json"
OBJECT_CARD_PATH = ROOT / "wizard_v4_3_object_card.json"
JULIA_SOURCE_PATH = ROOT / "run_julia.jl"
JAX_SOURCE_PATH = ROOT / "run_jax.py"
PYTORCH_SOURCE_PATH = ROOT / "run_pytorch.py"
RESULT_DIR = ROOT / "results"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
OUTPUT_PATH = RESULT_DIR / f"{SIM_ID}_validation.json"

SPEC_KEYS = {
    "schema", "sim_id", "classification", "engine_contract", "claim",
    "allowed_claim_label_if_all_learning_gates_pass", "carrier", "rule_symmetry_split",
    "behavioral_partition_hash", "fixtures", "learning_contract", "baselines",
    "primary_learning_gates", "negative_controls", "T9_rewrite", "validator_requirements",
    "blocked_consumers", "promotion_allowed", "formal_admission_allowed",
}
PREREG_KEYS = {
    "schema", "sim_id", "created_at", "status", "spec_path", "spec_sha256",
    "object_card_path", "object_card_sha256", "builder_sources_present_when_frozen",
    "frozen_surfaces", "change_policy", "promotion_allowed", "formal_admission_allowed",
}
OBJECT_CARD_KEYS = {
    "schema_version", "primary_object_card", "constraint_bands", "lateral_mappings",
    "exploration_contract", "loop_contract", "method_contracts", "evidence_spine",
}
JULIA_KEYS = {
    "ran", "semantic_role", "result_path", "scientific_pass_before_closed_json_gate",
    "claim_ceiling", "hashes", "packages_used", "behavioral_partition_hash_contract",
    "classification", "split_leakage_sentinel", "witness_trace", "sim_id",
    "reads_peer_result", "formal_admission_allowed", "input_provenance",
    "aligned_packages_load_bearing", "TOOL_MANIFEST", "all_pass",
    "foreign_runtime_manifest", "blocked_consumers", "divergence_log",
    "split_verification", "promotion_allowed", "TOOL_INTEGRATION_DEPTH", "fixtures",
    "schema", "tool_calls", "engine", "engine_contract", "rule_symmetry",
    "closed_json_validation", "source_path", "tests",
}
JAX_KEYS = {
    "T9_output_vector", "TOOL_INTEGRATION_DEPTH", "TOOL_MANIFEST", "actual_tools_used",
    "aligned_packages_load_bearing", "all_pass", "all_scientific_gates_pass", "allowed_claims",
    "artifact_hashes", "baselines", "behavioral_partitions", "blocked_consumers",
    "branch_status_before_run", "bridge_layer", "carrier_layer", "claim_ceiling",
    "claim_path_tools", "classification", "controls", "cut_layer",
    "data_or_artifact_dependencies", "demotion_condition", "eligible_consumers", "engine",
    "engine_contract", "engine_role", "exact_lane_pass", "fixture_summary",
    "forbidden_bridges_used", "foreign_runtime_manifest", "formal_admission_allowed",
    "geometry_layer", "input_integrity", "jax_version", "numpy_on_claim_path",
    "output_path", "packages_used", "peer_result_paths_read", "promotion_allowed",
    "promotion_status", "proof_surfaces_used", "purpose", "reads_peer_result",
    "required_inputs", "required_tools", "result_summary", "rule_symmetry", "schema",
    "schema_version", "scientific_question", "scientific_red_gates", "sim_class",
    "sim_execution_kind", "sim_id", "source_path", "source_sha256",
    "stage_movement_allowed", "tests", "tool_calls", "tool_integration_depth",
    "tool_manifest", "x64_enabled",
}
PYTORCH_KEYS = {
    "TOOL_INTEGRATION_DEPTH", "TOOL_MANIFEST", "actual_tools_used",
    "aligned_packages_load_bearing", "all_pass", "baselines", "claim_ceiling",
    "classification", "controls", "engine", "engine_contract", "exact_fixture_receipts",
    "formal_admission_allowed", "gates", "model_contract", "numpy_used_on_claim_path",
    "object_card_sha256", "object_card_statement_sha256", "packages_used",
    "peer_result_paths_read", "preregistration_bound_at_runtime",
    "preregistration_receipt_sha256", "promotion_allowed", "promotion_status",
    "reads_peer_result", "result_path", "schema", "schema_version", "sim_id",
    "source_path", "source_sha256", "spec_path", "spec_sha256", "split_validation",
    "stage_movement_allowed", "test_primary", "test_structural_holdout", "tool_calls",
    "training", "validation_selection",
}
JULIA_FIXTURE_KEYS = {
    "class_count_by_depth", "fixture_id", "graph_receipt", "one_bit_transition_mutation",
    "pair_order_sha256", "partition_sha256", "quotient", "rules", "split",
    "stable_class_count", "stable_depth", "stable_labels",
}
JAX_FIXTURE_KEYS = {
    "action_a_conflicting_ordered_pairs", "action_b_conflicting_ordered_pairs", "class_count",
    "fixture_index", "one_bit_transition_mutation", "quotient_congruent", "rules", "split",
    "stable_depth", "stable_labels", "stable_partition_sha256",
}
PYTORCH_RAW_KEYS = {
    "ensemble_metrics", "ensemble_scores", "partition_sha256", "per_seed_metrics",
    "predicted_same_object", "rules", "scores_per_seed", "target_same_object",
}
CONTROL_RAW_KEYS = {"ensemble_scores", "predicted_same_object", "rules"}
PYTORCH_PRIMARY_KEYS = {
    "ensemble_metrics", "per_seed_metrics", "rule_sensitive", "partition_metrics",
    "partition_macro_ari", "partition_macro_normalized_vi", "raw_predictions",
}
PYTORCH_STRUCTURAL_KEYS = {
    "required_for_stronger_label", "frozen_hash_binding", "ensemble_metrics",
    "per_seed_metrics", "raw_predictions",
}
PYTORCH_CONTROL_KEYS = {
    "same_weight_edge_erasure", "retrained_edge_erasure", "same_weight_probe_erasure",
    "same_weight_zero_transition_information", "same_weight_rule_identity_permutation",
    "shuffled_training_labels", "optimizer_erasure", "state_and_rotation_invariance",
    "action_swap_max_abs", "one_bit_transition_mutation", "claim_bearing_score_hashes",
}
METRIC_KEYS = {
    "count", "tp", "fp", "tn", "fn", "accuracy", "mcc", "balanced_accuracy",
    "positive_recall", "negative_recall", "false_positive_rate", "threshold",
    "average_precision", "positive_prevalence", "normalized_average_precision",
}
MACRO_KEYS = {f"macro_{key}" for key in (
    "accuracy", "mcc", "balanced_accuracy", "positive_recall", "negative_recall",
    "false_positive_rate", "average_precision", "normalized_average_precision",
)} | {"per_fixture"}


class ValidationError(RuntimeError):
    """A fail-closed packet validation error."""


@dataclass(frozen=True)
class ExactFixture:
    split: str
    rules: tuple[int, int]
    transition_a: tuple[int, ...]
    transition_b: tuple[int, ...]
    labels: tuple[int, ...]
    depth: int
    class_count: int
    partition_sha256: str


@dataclass
class Packet:
    spec: dict[str, Any]
    prereg: dict[str, Any]
    object_card: dict[str, Any]
    julia: dict[str, Any]
    jax: dict[str, Any]
    pytorch: dict[str, Any]


def reject_constant(token: str) -> None:
    raise ValidationError(f"non-finite JSON constant rejected: {token}")


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValidationError(f"duplicate JSON key rejected: {key}")
        out[key] = value
    return out


def strict_json_load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicate_pairs,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain one JSON object")
    return value


def require(condition: bool, path: str, message: str) -> None:
    if not condition:
        raise ValidationError(f"{path}: {message}")


def exact_keys(value: Any, expected: set[str], path: str) -> dict[str, Any]:
    require(isinstance(value, dict), path, "expected object")
    observed = set(value)
    require(
        observed == expected,
        path,
        f"closed schema differs; missing={sorted(expected - observed)}, extra={sorted(observed - expected)}",
    )
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=False).encode()).hexdigest()


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def canonicalize(values: Sequence[Any]) -> tuple[int, ...]:
    seen: dict[Any, int] = {}
    labels: list[int] = []
    for value in values:
        if value not in seen:
            seen[value] = len(seen)
        labels.append(seen[value])
    return tuple(labels)


def reflect_rule(rule: int) -> int:
    out = 0
    for neighborhood in range(8):
        reversed_neighborhood = ((neighborhood & 1) << 2) | (neighborhood & 2) | ((neighborhood & 4) >> 2)
        out |= ((rule >> reversed_neighborhood) & 1) << neighborhood
    return out


def conjugate_rule(rule: int) -> int:
    out = 0
    for neighborhood in range(8):
        out |= (1 - ((rule >> (7 - neighborhood)) & 1)) << neighborhood
    return out


def rule_orbit(rule: int) -> tuple[int, ...]:
    seen = {rule}
    pending = [rule]
    while pending:
        current = pending.pop()
        for candidate in (reflect_rule(current), conjugate_rule(current)):
            if candidate not in seen:
                seen.add(candidate)
                pending.append(candidate)
    return tuple(sorted(seen))


def ordered_orbits() -> list[list[int]]:
    unique = {rule_orbit(rule) for rule in range(256)}
    return [list(orbit) for orbit in sorted(
        unique,
        key=lambda orbit: hashlib.sha256(
            f"ECA6-PRBOG-v1|orbit|{','.join(map(str, orbit))}".encode()
        ).hexdigest(),
    )]


def pair_hash(pair: Sequence[int]) -> str:
    left, right = sorted((int(pair[0]), int(pair[1])))
    return hashlib.sha256(f"ECA6-PRBOG-v1|pair|{left},{right}".encode()).hexdigest()


def bits(state: int) -> tuple[int, ...]:
    return tuple((state >> site) & 1 for site in range(RING_SIZE))


def eca_step(rule: int, state: int) -> int:
    state_bits = bits(state)
    out = 0
    for site in range(RING_SIZE):
        neighborhood = (
            (state_bits[(site - 1) % RING_SIZE] << 2)
            | (state_bits[site] << 1)
            | state_bits[(site + 1) % RING_SIZE]
        )
        out |= ((rule >> neighborhood) & 1) << site
    return out


def probes(state: int) -> tuple[int, int]:
    state_bits = bits(state)
    return (
        sum(state_bits),
        sum(state_bits[site] != state_bits[(site + 1) % RING_SIZE] for site in range(RING_SIZE)),
    )


def exact_fixture(split: str, pair: Sequence[int]) -> ExactFixture:
    rule_a, rule_b = int(pair[0]), int(pair[1])
    action_a = tuple(eca_step(rule_a, state) for state in range(STATE_COUNT))
    action_b = tuple(eca_step(rule_b, state) for state in range(STATE_COUNT))
    labels = canonicalize([probes(state) for state in range(STATE_COUNT)])
    strict_refinements = 0
    for _ in range(63):
        refined = canonicalize([
            (labels[state], labels[action_a[state]], labels[action_b[state]])
            for state in range(STATE_COUNT)
        ])
        if refined == labels:
            break
        labels = refined
        strict_refinements += 1
    else:
        raise ValidationError(f"exact fixture {split}:{rule_a},{rule_b} did not stabilize")
    return ExactFixture(
        split=split,
        rules=(rule_a, rule_b),
        transition_a=action_a,
        transition_b=action_b,
        labels=labels,
        depth=strict_refinements,
        class_count=len(set(labels)),
        partition_sha256=compact_hash(list(labels)),
    )


def quotient_maps(fixture: ExactFixture) -> tuple[list[int], list[int]]:
    induced_a: list[int | None] = [None] * fixture.class_count
    induced_b: list[int | None] = [None] * fixture.class_count
    for state, label in enumerate(fixture.labels):
        targets = (fixture.labels[fixture.transition_a[state]], fixture.labels[fixture.transition_b[state]])
        for mapping, target in zip((induced_a, induced_b), targets, strict=True):
            if mapping[label] is None:
                mapping[label] = target
            require(mapping[label] == target, "exact.quotient", f"fixture {fixture.rules} is not congruent")
    return [int(value) for value in induced_a], [int(value) for value in induced_b]


def validate_split(spec: dict[str, Any], orbits: list[list[int]]) -> dict[str, Any]:
    require(len(orbits) == EXPECTED_ORBIT_COUNT, "split.orbits", "expected 88 symmetry orbits")
    rule_to_orbit = {rule: index for index, orbit in enumerate(orbits) for rule in orbit}
    require(set(rule_to_orbit) == set(range(256)), "split.orbits", "orbit coverage is not exactly 0..255")
    fixtures = exact_keys(spec["fixtures"], set(GROUPS), "spec.fixtures")
    used_rules: dict[int, str] = {}
    group_receipts: dict[str, Any] = {}
    for group in GROUPS:
        pairs = fixtures[group]
        require(isinstance(pairs, list) and len(pairs) == EXPECTED_COUNTS[group], f"spec.fixtures.{group}", "fixture count mismatch")
        hashes = [pair_hash(pair) for pair in pairs]
        if group != "test_structural_holdout":
            require(hashes == sorted(hashes), f"spec.fixtures.{group}", "pairs are not in frozen SHA256 order")
        orbit_indices: set[int] = set()
        local_rules: set[int] = set()
        for index, pair in enumerate(pairs):
            require(isinstance(pair, list) and len(pair) == 2, f"spec.fixtures.{group}[{index}]", "expected rule pair")
            left, right = pair
            require(type(left) is int and type(right) is int and 0 <= left < 256 and 0 <= right < 256, f"spec.fixtures.{group}[{index}]", "invalid rule")
            require(left < right, f"spec.fixtures.{group}[{index}]", "rules must be ascending and distinct")
            require(rule_to_orbit[left] != rule_to_orbit[right], f"spec.fixtures.{group}[{index}]", "pair members share a symmetry orbit")
            require(rule_to_orbit[left] in ORBIT_BLOCKS[group] and rule_to_orbit[right] in ORBIT_BLOCKS[group], f"spec.fixtures.{group}[{index}]", "rule outside frozen orbit block")
            for rule in pair:
                require(rule not in local_rules, f"spec.fixtures.{group}", f"rule {rule} reused within split")
                require(rule not in used_rules, f"spec.fixtures.{group}", f"rule {rule} crosses split from {used_rules.get(rule)}")
                local_rules.add(rule)
                used_rules[rule] = group
                orbit_indices.add(rule_to_orbit[rule])
        group_receipts[group] = {"fixture_count": len(pairs), "rule_count": len(local_rules), "orbit_indices": sorted(orbit_indices)}
    return {"orbit_count": len(orbits), "unique_rule_count": len(used_rules), "groups": group_receipts}


def build_exact_fixtures(spec: dict[str, Any]) -> dict[str, list[ExactFixture]]:
    return {
        group: [exact_fixture(group, pair) for pair in spec["fixtures"][group]]
        for group in GROUPS
    }


def load_packet() -> Packet:
    packet = Packet(
        spec=strict_json_load(SPEC_PATH),
        prereg=strict_json_load(PREREG_PATH),
        object_card=strict_json_load(OBJECT_CARD_PATH),
        julia=strict_json_load(JULIA_RESULT_PATH),
        jax=strict_json_load(JAX_RESULT_PATH),
        pytorch=strict_json_load(PYTORCH_RESULT_PATH),
    )
    exact_keys(packet.spec, SPEC_KEYS, "spec")
    exact_keys(packet.prereg, PREREG_KEYS, "preregistration")
    exact_keys(packet.object_card, OBJECT_CARD_KEYS, "object_card")
    exact_keys(packet.julia, JULIA_KEYS, "julia")
    exact_keys(packet.jax, JAX_KEYS, "jax")
    exact_keys(packet.pytorch, PYTORCH_KEYS, "pytorch")
    return packet


def validate_frozen_inputs(packet: Packet) -> dict[str, Any]:
    require(packet.spec["sim_id"] == SIM_ID and packet.prereg["sim_id"] == SIM_ID, "identity", "sim id mismatch")
    require(packet.spec["schema"] == "codex_ratchet.finite_probe_behavioral_object_engine_v1.spec.v1", "spec.schema", "unexpected schema")
    require(packet.prereg["status"] == "frozen_before_builder_source", "preregistration.status", "not preregistered before builders")
    require(packet.prereg["builder_sources_present_when_frozen"] is False, "preregistration.builder_sources_present_when_frozen", "must be false")
    require(packet.prereg["spec_sha256"] == sha256_file(SPEC_PATH), "preregistration.spec_sha256", "spec hash mismatch")
    require(packet.prereg["object_card_sha256"] == sha256_file(OBJECT_CARD_PATH), "preregistration.object_card_sha256", "object-card hash mismatch")
    require(packet.spec["classification"] == "scratch_diagnostic", "spec.classification", "scope escalation")
    require(packet.spec["promotion_allowed"] is False and packet.spec["formal_admission_allowed"] is False, "spec.promotion", "promotion must remain blocked")
    require(packet.spec["rule_symmetry_split"]["expected_orbit_count"] == EXPECTED_ORBIT_COUNT, "spec.rule_symmetry_split", "orbit count drift")
    require(packet.spec["learning_contract"]["seeds"] == [730241, 730251, 730261], "spec.learning_contract.seeds", "seed drift")
    require(set(packet.spec["T9_rewrite"]["output_vector"]) == T9_FIELDS, "spec.T9_rewrite.output_vector", "T9 vector drift")
    return {"spec_sha256": sha256_file(SPEC_PATH), "preregistration_sha256": sha256_file(PREREG_PATH), "object_card_sha256": sha256_file(OBJECT_CARD_PATH)}


def source_has_peer_result_read(source_path: Path, own_result: Path) -> bool:
    text = source_path.read_text(encoding="utf-8")
    peer_names = {path.name for path in (JULIA_RESULT_PATH, JAX_RESULT_PATH, PYTORCH_RESULT_PATH)} - {own_result.name}
    return any(name in text for name in peer_names)


def validate_source_bindings(packet: Packet) -> dict[str, Any]:
    expected = {
        "julia": (JULIA_SOURCE_PATH, packet.julia["hashes"]["run_julia_sha256"], JULIA_RESULT_PATH),
        "jax": (JAX_SOURCE_PATH, packet.jax["source_sha256"], JAX_RESULT_PATH),
        "pytorch": (PYTORCH_SOURCE_PATH, packet.pytorch["source_sha256"], PYTORCH_RESULT_PATH),
    }
    receipts: dict[str, Any] = {}
    for engine, (path, declared_hash, own_result) in expected.items():
        actual_hash = sha256_file(path)
        require(declared_hash == actual_hash, f"{engine}.source_sha256", "live source/result binding mismatch")
        result = getattr(packet, engine)
        require(result["reads_peer_result"] is False, f"{engine}.reads_peer_result", "peer result read declared")
        peer_paths = result.get("peer_result_paths_read", result.get("input_provenance", {}).get("peer_result_files_read", []))
        require(peer_paths == [], f"{engine}.peer_result_paths_read", "peer result paths must be empty")
        require(not source_has_peer_result_read(path, own_result), f"{engine}.source", "peer result filename appears in source")
        receipts[engine] = {"source_sha256": actual_hash, "result_sha256": sha256_file(own_result), "peer_result_reads_absent": True}
    for engine, result in (("julia", packet.julia), ("jax", packet.jax), ("pytorch", packet.pytorch)):
        require(result["classification"] == "scratch_diagnostic", f"{engine}.classification", "scope escalation")
        require(result["promotion_allowed"] is False and result["formal_admission_allowed"] is False, f"{engine}.promotion", "promotion must remain blocked")
    require(packet.jax["numpy_on_claim_path"] is False and packet.jax["forbidden_bridges_used"] == [], "jax.bridges", "forbidden bridge declared")
    require(packet.pytorch["numpy_used_on_claim_path"] is False, "pytorch.numpy_used_on_claim_path", "must be false")
    return receipts


def equivalent_partition(left: Sequence[int], right: Sequence[int]) -> bool:
    return canonicalize(left) == canonicalize(right)


def validate_julia(packet: Packet, exact: dict[str, list[ExactFixture]], orbits: list[list[int]]) -> dict[str, Any]:
    result = packet.julia
    require(result["schema"] == "codex_ratchet.finite_probe_behavioral_object_engine_v1.julia_result.v1", "julia.schema", "unexpected schema")
    require(result["engine"] == "julia" and result["ran"] is True, "julia.engine", "lane did not run")
    emitted_orbits = [row["members"] for row in result["rule_symmetry"]["ordered_orbits"]]
    require(emitted_orbits == orbits, "julia.rule_symmetry.ordered_orbits", "orbit reconstruction mismatch")
    require(result["rule_symmetry"]["actual_orbit_count"] == EXPECTED_ORBIT_COUNT, "julia.rule_symmetry.actual_orbit_count", "orbit count mismatch")
    require(exact_keys(result["fixtures"], set(GROUPS), "julia.fixtures") is not None, "julia.fixtures", "missing fixture groups")
    for group in GROUPS:
        rows = result["fixtures"][group]
        require(len(rows) == len(exact[group]), f"julia.fixtures.{group}", "fixture count mismatch")
        for index, (row, expected) in enumerate(zip(rows, exact[group], strict=True)):
            path = f"julia.fixtures.{group}[{index}]"
            exact_keys(row, JULIA_FIXTURE_KEYS, path)
            require(row["rules"] == list(expected.rules) and row["split"] == group, path, "fixture identity mismatch")
            require(equivalent_partition(row["stable_labels"], expected.labels), f"{path}.stable_labels", "partition mismatch")
            require(row["partition_sha256"] == expected.partition_sha256, f"{path}.partition_sha256", "partition hash mismatch")
            require(row["stable_class_count"] == expected.class_count, f"{path}.stable_class_count", "class count mismatch")
            require(row["stable_depth"] == expected.depth, f"{path}.stable_depth", "strict-refinement depth mismatch")
            induced_a, induced_b = quotient_maps(expected)
            require(row["quotient"]["congruent"] is True, f"{path}.quotient.congruent", "must be true")
            require(row["quotient"]["induced_a"] == induced_a and row["quotient"]["induced_b"] == induced_b, f"{path}.quotient", "induced map mismatch")
            require(row["graph_receipt"]["scc_parity"] is True and row["graph_receipt"]["signature_mutation_control"]["passed"] is True, f"{path}.graph_receipt", "Graphs control red")
    require(result["tests"]["T9_counterfactual_adaptive_replaceability"] is False, "julia.tests.T9", "T9 must remain red")
    require(result["all_pass"] is True and result["closed_json_validation"]["passed"] is True, "julia.all_pass", "artifact lane red")
    return {"fixture_count": sum(map(len, exact.values())), "exact_partitions_match": True, "T9_earned": False}


def validate_jax(packet: Packet, exact: dict[str, list[ExactFixture]], orbits: list[list[int]]) -> dict[str, Any]:
    result = packet.jax
    require(result["schema"] == "codex_ratchet.finite_probe_behavioral_object_engine_v1.jax_result.v1", "jax.schema", "unexpected schema")
    require(result["engine"] == "jax" and result["x64_enabled"] is True, "jax.engine", "x64 JAX lane missing")
    require(result["rule_symmetry"]["ordered_orbits"] == orbits, "jax.rule_symmetry.ordered_orbits", "orbit reconstruction mismatch")
    partitions = exact_keys(result["behavioral_partitions"], {
        "all_ordered_pair_targets_sha256", "all_stable_labels_sha256", "canonical_label_convention",
        "fixtures", "maximum_refinement_depth",
    }, "jax.behavioral_partitions")
    flat_exact = [fixture for group in GROUPS for fixture in exact[group]]
    rows = partitions["fixtures"]
    require(len(rows) == len(flat_exact) == 96, "jax.behavioral_partitions.fixtures", "fixture count mismatch")
    emitted_labels: list[list[int]] = []
    ordered_targets: list[list[bool]] = []
    for index, (row, expected) in enumerate(zip(rows, flat_exact, strict=True)):
        path = f"jax.behavioral_partitions.fixtures[{index}]"
        exact_keys(row, JAX_FIXTURE_KEYS, path)
        require(row["fixture_index"] == index and row["rules"] == list(expected.rules) and row["split"] == expected.split, path, "fixture identity mismatch")
        require(equivalent_partition(row["stable_labels"], expected.labels), f"{path}.stable_labels", "partition mismatch")
        require(row["stable_partition_sha256"] == expected.partition_sha256, f"{path}.stable_partition_sha256", "partition hash mismatch")
        require(row["class_count"] == expected.class_count and row["quotient_congruent"] is True, path, "class count or quotient mismatch")
        require(row["stable_depth"] == expected.depth + 1, f"{path}.stable_depth", "JAX convergence-check depth mismatch")
        require(row["action_a_conflicting_ordered_pairs"] == 0 and row["action_b_conflicting_ordered_pairs"] == 0, path, "quotient conflict reported")
        labels = list(canonicalize(row["stable_labels"]))
        emitted_labels.append(row["stable_labels"])
        ordered_targets.append([labels[left] == labels[right] for left in range(STATE_COUNT) for right in range(STATE_COUNT)])
    require(partitions["all_stable_labels_sha256"] == canonical_hash(emitted_labels), "jax.behavioral_partitions.all_stable_labels_sha256", "aggregate label hash mismatch")
    require(partitions["all_ordered_pair_targets_sha256"] == canonical_hash(ordered_targets), "jax.behavioral_partitions.all_ordered_pair_targets_sha256", "aggregate target hash mismatch")
    require(result["tests"]["T9_adaptive_replaceability_boundary"]["pass"] is False, "jax.tests.T9", "T9 must remain red")
    require(set(result["T9_output_vector"]) == T9_FIELDS, "jax.T9_output_vector", "T9 vector schema mismatch")
    require(result["exact_lane_pass"] is True and result["all_pass"] is True, "jax.all_pass", "exact artifact lane red")
    require(result["all_scientific_gates_pass"] is False and result["scientific_red_gates"] == ["T9_adaptive_replaceability_boundary"], "jax.scientific_red_gates", "T9 red was not preserved")
    return {"fixture_count": len(rows), "exact_partitions_match": True, "aggregate_hashes_match": True, "T9_earned": False}


def close_float(actual: Any, expected: float, path: str, tolerance: float = 1e-12) -> None:
    require(type(actual) in (int, float) and math.isfinite(float(actual)), path, "expected finite number")
    require(math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance), path, f"metric mismatch: {actual!r} != {expected!r}")


def mcc_from_counts(tp: int, fp: int, tn: int, fn: int) -> float:
    denominator = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    return (tp * tn - fp * fn) / math.sqrt(denominator) if denominator else 0.0


def average_precision(scores: Sequence[float], target: Sequence[bool]) -> float:
    order = sorted(range(len(scores)), key=lambda index: -scores[index])
    positives = sum(target)
    if positives == 0:
        return 0.0
    cumulative = 0
    precision_sum = 0.0
    for rank, index in enumerate(order, start=1):
        if target[index]:
            cumulative += 1
            precision_sum += cumulative / rank
    return precision_sum / positives


def scored_metrics(scores: Sequence[float], target: Sequence[bool], threshold: float) -> dict[str, Any]:
    require(len(scores) == len(target) and len(target) > 0, "metrics", "vector length mismatch")
    require(all(type(value) in (int, float) and math.isfinite(float(value)) for value in scores), "metrics.scores", "non-finite score")
    predicted = [value >= threshold for value in scores]
    tp = sum(pred and truth for pred, truth in zip(predicted, target, strict=True))
    fp = sum(pred and not truth for pred, truth in zip(predicted, target, strict=True))
    tn = sum(not pred and not truth for pred, truth in zip(predicted, target, strict=True))
    fn = sum(not pred and truth for pred, truth in zip(predicted, target, strict=True))
    positive_recall = tp / (tp + fn) if tp + fn else 0.0
    negative_recall = tn / (tn + fp) if tn + fp else 0.0
    false_positive_rate = fp / (fp + tn) if fp + tn else 0.0
    ap = average_precision(scores, target)
    prevalence = sum(target) / len(target)
    return {
        "count": len(target), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "accuracy": (tp + tn) / len(target),
        "mcc": mcc_from_counts(tp, fp, tn, fn),
        "balanced_accuracy": 0.5 * (positive_recall + negative_recall),
        "positive_recall": positive_recall,
        "negative_recall": negative_recall,
        "false_positive_rate": false_positive_rate,
        "threshold": threshold,
        "average_precision": ap,
        "positive_prevalence": prevalence,
        "normalized_average_precision": (ap - prevalence) / (1.0 - prevalence) if prevalence < 1.0 else 0.0,
    }


def macro_metrics(score_sets: Sequence[Sequence[float]], target_sets: Sequence[Sequence[bool]], threshold: float) -> dict[str, Any]:
    per_fixture = [scored_metrics(scores, targets, threshold) for scores, targets in zip(score_sets, target_sets, strict=True)]
    fields = (
        "accuracy", "mcc", "balanced_accuracy", "positive_recall", "negative_recall",
        "false_positive_rate", "average_precision", "normalized_average_precision",
    )
    return {f"macro_{field}": sum(item[field] for item in per_fixture) / len(per_fixture) for field in fields} | {"per_fixture": per_fixture}


def validate_metric(actual: Any, expected: dict[str, Any], path: str) -> None:
    exact_keys(actual, METRIC_KEYS, path)
    for key in ("count", "tp", "fp", "tn", "fn"):
        require(actual[key] == expected[key] and type(actual[key]) is int, f"{path}.{key}", "count mismatch")
    for key in METRIC_KEYS - {"count", "tp", "fp", "tn", "fn"}:
        close_float(actual[key], expected[key], f"{path}.{key}")


def validate_macro(actual: Any, expected: dict[str, Any], path: str) -> None:
    exact_keys(actual, MACRO_KEYS, path)
    require(len(actual["per_fixture"]) == len(expected["per_fixture"]), f"{path}.per_fixture", "length mismatch")
    for index, (left, right) in enumerate(zip(actual["per_fixture"], expected["per_fixture"], strict=True)):
        validate_metric(left, right, f"{path}.per_fixture[{index}]")
    for key in MACRO_KEYS - {"per_fixture"}:
        close_float(actual[key], expected[key], f"{path}.{key}")


def connected_components(relation: Sequence[bool]) -> list[int]:
    labels = [-1] * STATE_COUNT
    component = 0
    for start in range(STATE_COUNT):
        if labels[start] >= 0:
            continue
        labels[start] = component
        frontier = [start]
        while frontier:
            current = frontier.pop()
            for neighbor in range(STATE_COUNT):
                if (relation[current * STATE_COUNT + neighbor] or relation[neighbor * STATE_COUNT + current]) and labels[neighbor] < 0:
                    labels[neighbor] = component
                    frontier.append(neighbor)
        component += 1
    return labels


def adjusted_rand_index(predicted: Sequence[int], exact: Sequence[int]) -> float:
    contingency: dict[tuple[int, int], int] = {}
    predicted_counts: dict[int, int] = {}
    exact_counts: dict[int, int] = {}
    for left, right in zip(predicted, exact, strict=True):
        contingency[left, right] = contingency.get((left, right), 0) + 1
        predicted_counts[left] = predicted_counts.get(left, 0) + 1
        exact_counts[right] = exact_counts.get(right, 0) + 1
    choose2 = lambda value: value * (value - 1) / 2
    index = sum(choose2(value) for value in contingency.values())
    predicted_sum = sum(choose2(value) for value in predicted_counts.values())
    exact_sum = sum(choose2(value) for value in exact_counts.values())
    total = choose2(len(predicted))
    expected = predicted_sum * exact_sum / total if total else 0.0
    maximum = 0.5 * (predicted_sum + exact_sum)
    return 1.0 if maximum == expected else (index - expected) / (maximum - expected)


def normalized_vi(predicted: Sequence[int], exact: Sequence[int]) -> float:
    count = len(predicted)
    pred_counts: dict[int, int] = {}
    exact_counts: dict[int, int] = {}
    joint: dict[tuple[int, int], int] = {}
    for left, right in zip(predicted, exact, strict=True):
        pred_counts[left] = pred_counts.get(left, 0) + 1
        exact_counts[right] = exact_counts.get(right, 0) + 1
        joint[left, right] = joint.get((left, right), 0) + 1
    entropy_pred = -sum((value / count) * math.log(value / count) for value in pred_counts.values())
    entropy_exact = -sum((value / count) * math.log(value / count) for value in exact_counts.values())
    mutual = sum(
        (value / count) * math.log((value / count) / ((pred_counts[left] / count) * (exact_counts[right] / count)))
        for (left, right), value in joint.items()
    )
    return (entropy_pred + entropy_exact - 2.0 * mutual) / math.log(count)


def partition_metrics(scores: Sequence[float], threshold: float, exact_labels: Sequence[int]) -> dict[str, Any]:
    relation = [score >= threshold for score in scores]
    reflexive = sum(not relation[state * STATE_COUNT + state] for state in range(STATE_COUNT))
    symmetric = sum(
        relation[left * STATE_COUNT + right] != relation[right * STATE_COUNT + left]
        for left in range(STATE_COUNT) for right in range(left + 1, STATE_COUNT)
    )
    transitive = 0
    for middle in range(STATE_COUNT):
        for left in range(STATE_COUNT):
            if not relation[left * STATE_COUNT + middle]:
                continue
            for right in range(STATE_COUNT):
                transitive += bool(relation[middle * STATE_COUNT + right] and not relation[left * STATE_COUNT + right])
    predicted_labels = connected_components(relation)
    pred_sizes = [predicted_labels.count(label) for label in sorted(set(predicted_labels))]
    exact_sizes = [list(exact_labels).count(label) for label in sorted(set(exact_labels))]
    return {
        "reflexivity_violations": reflexive,
        "symmetry_violations": symmetric,
        "transitivity_violation_triples": transitive,
        "relation_laws_pass": reflexive == symmetric == transitive == 0,
        "connected_component_count": len(pred_sizes),
        "adjusted_rand_index": adjusted_rand_index(predicted_labels, exact_labels),
        "normalized_variation_of_information": normalized_vi(predicted_labels, exact_labels),
        "largest_predicted_class": max(pred_sizes),
        "largest_exact_class": max(exact_sizes),
        "largest_class_ratio": max(pred_sizes) / max(exact_sizes),
        "predicted_component_labels": predicted_labels,
    }


def validate_partition_metric(actual: dict[str, Any], expected: dict[str, Any], path: str) -> None:
    exact_keys(actual, set(expected), path)
    for key, value in expected.items():
        if type(value) is float:
            close_float(actual[key], value, f"{path}.{key}")
        else:
            require(actual[key] == value, f"{path}.{key}", "partition metric mismatch")


def validate_raw_predictions(
    rows: Any,
    exact_rows: Sequence[ExactFixture],
    threshold: float,
    path: str,
) -> tuple[list[list[float]], list[list[bool]], list[list[list[float]]]]:
    require(isinstance(rows, list) and len(rows) == len(exact_rows), path, "fixture count mismatch")
    score_sets: list[list[float]] = []
    targets: list[list[bool]] = []
    per_seed_score_sets: list[list[list[float]]] = [[], [], []]
    for index, (row, fixture) in enumerate(zip(rows, exact_rows, strict=True)):
        item_path = f"{path}[{index}]"
        exact_keys(row, PYTORCH_RAW_KEYS, item_path)
        target = [fixture.labels[left] == fixture.labels[right] for left in range(STATE_COUNT) for right in range(STATE_COUNT)]
        require(row["rules"] == list(fixture.rules), f"{item_path}.rules", "fixture identity mismatch")
        require(row["target_same_object"] == target, f"{item_path}.target_same_object", "target differs from independent partition")
        require(row["partition_sha256"] == fixture.partition_sha256, f"{item_path}.partition_sha256", "partition hash mismatch")
        scores = row["ensemble_scores"]
        require(isinstance(scores, list) and len(scores) == PAIR_COUNT, f"{item_path}.ensemble_scores", "score length mismatch")
        predicted = [score >= threshold for score in scores]
        require(row["predicted_same_object"] == predicted, f"{item_path}.predicted_same_object", "thresholded prediction mismatch")
        metric = scored_metrics(scores, target, threshold)
        validate_metric(row["ensemble_metrics"], metric, f"{item_path}.ensemble_metrics")
        require(isinstance(row["scores_per_seed"], list) and len(row["scores_per_seed"]) == 3, f"{item_path}.scores_per_seed", "expected three seeds")
        require(isinstance(row["per_seed_metrics"], list) and len(row["per_seed_metrics"]) == 3, f"{item_path}.per_seed_metrics", "expected three metrics")
        for seed_index, seed_scores in enumerate(row["scores_per_seed"]):
            seed_metric = scored_metrics(seed_scores, target, threshold)
            validate_metric(row["per_seed_metrics"][seed_index], seed_metric, f"{item_path}.per_seed_metrics[{seed_index}]")
            per_seed_score_sets[seed_index].append(seed_scores)
        score_sets.append(scores)
        targets.append(target)
    return score_sets, targets, per_seed_score_sets


def validate_control_raw(
    control: dict[str, Any],
    fixtures: Sequence[ExactFixture],
    targets: Sequence[Sequence[bool]],
    path: str,
) -> dict[str, Any]:
    expected_keys = {"raw_scores", "test_metrics"}
    if "training_receipts" in control:
        expected_keys.add("training_receipts")
    exact_keys(control, expected_keys, path)
    rows = control["raw_scores"]
    require(isinstance(rows, list) and len(rows) == len(fixtures), f"{path}.raw_scores", "fixture count mismatch")
    threshold = float(control["test_metrics"]["per_fixture"][0]["threshold"])
    scores: list[list[float]] = []
    for index, (row, fixture) in enumerate(zip(rows, fixtures, strict=True)):
        exact_keys(row, CONTROL_RAW_KEYS, f"{path}.raw_scores[{index}]")
        require(row["rules"] == list(fixture.rules), f"{path}.raw_scores[{index}].rules", "fixture identity mismatch")
        require(row["predicted_same_object"] == [score >= threshold for score in row["ensemble_scores"]], f"{path}.raw_scores[{index}].predicted_same_object", "threshold mismatch")
        scores.append(row["ensemble_scores"])
    expected = macro_metrics(scores, targets, threshold)
    validate_macro(control["test_metrics"], expected, f"{path}.test_metrics")
    return expected


def validate_pytorch(packet: Packet, exact: dict[str, list[ExactFixture]]) -> dict[str, Any]:
    result = packet.pytorch
    require(result["schema"] == "codex_ratchet.pytorch_heldout_rule_proxy_result.v1", "pytorch.schema", "unexpected schema")
    require(result["engine"] == "pytorch" and result["preregistration_bound_at_runtime"] is True, "pytorch.engine", "runtime preregistration missing")
    require(result["spec_sha256"] == sha256_file(SPEC_PATH), "pytorch.spec_sha256", "spec hash mismatch")
    require(result["object_card_sha256"] == sha256_file(OBJECT_CARD_PATH), "pytorch.object_card_sha256", "object-card hash mismatch")
    exact_keys(result["test_primary"], PYTORCH_PRIMARY_KEYS, "pytorch.test_primary")
    exact_keys(result["test_structural_holdout"], PYTORCH_STRUCTURAL_KEYS, "pytorch.test_structural_holdout")
    exact_keys(result["controls"], PYTORCH_CONTROL_KEYS, "pytorch.controls")
    exact_keys(result["claim_ceiling"], {
        "allowed_if_green", "current_label", "semantic_authority", "blocked_consumers",
        "T9_runtime_nonredundancy_earned",
    }, "pytorch.claim_ceiling")
    split_validation = exact_keys(result["split_validation"], {
        "expected_88_orbits", "fixture_rules_in_frozen_orbit_blocks",
        "fixture_rules_unique_within_each_split", "injected_symmetry_leakage_overlap_count",
        "injected_symmetry_leakage_sentinel_detected", "injected_symmetry_leakage_sentinel_rule",
        "no_train_held_orbit_overlap", "orbit_count", "orbit_manifest_sha256",
        "train_held_orbit_overlap_count",
    }, "pytorch.split_validation")
    require(
        split_validation["expected_88_orbits"] is True
        and all(split_validation["fixture_rules_in_frozen_orbit_blocks"].values())
        and all(split_validation["fixture_rules_unique_within_each_split"].values())
        and split_validation["injected_symmetry_leakage_sentinel_detected"] is True
        and split_validation["no_train_held_orbit_overlap"] is True,
        "pytorch.split_validation",
        "split or leakage sentinel red",
    )
    exact_keys(result["exact_fixture_receipts"], set(GROUPS), "pytorch.exact_fixture_receipts")
    for group in GROUPS:
        receipts = result["exact_fixture_receipts"][group]
        require(len(receipts) == len(exact[group]), f"pytorch.exact_fixture_receipts.{group}", "fixture count mismatch")
        for index, (receipt, fixture) in enumerate(zip(receipts, exact[group], strict=True)):
            path = f"pytorch.exact_fixture_receipts.{group}[{index}]"
            exact_keys(receipt, {"rules", "stabilization_depth", "class_count", "partition_sha256"}, path)
            require(receipt == {
                "rules": list(fixture.rules),
                "stabilization_depth": fixture.depth + 1,
                "class_count": fixture.class_count,
                "partition_sha256": fixture.partition_sha256,
            }, path, "exact fixture receipt mismatch")
    threshold = float(result["validation_selection"]["threshold"])
    require(threshold == result["training"]["single_validation_selected_threshold"], "pytorch.validation_selection.threshold", "threshold duplication mismatch")
    primary_scores, primary_targets, seed_scores = validate_raw_predictions(
        result["test_primary"]["raw_predictions"], exact["test_primary"], threshold, "pytorch.test_primary.raw_predictions"
    )
    primary_macro = macro_metrics(primary_scores, primary_targets, threshold)
    validate_macro(result["test_primary"]["ensemble_metrics"], primary_macro, "pytorch.test_primary.ensemble_metrics")
    require(len(result["test_primary"]["per_seed_metrics"]) == 3, "pytorch.test_primary.per_seed_metrics", "expected three seed macros")
    seed_macros = [macro_metrics(scores, primary_targets, threshold) for scores in seed_scores]
    for index, expected in enumerate(seed_macros):
        validate_macro(result["test_primary"]["per_seed_metrics"][index], expected, f"pytorch.test_primary.per_seed_metrics[{index}]")

    structural_scores, structural_targets, structural_seed_scores = validate_raw_predictions(
        result["test_structural_holdout"]["raw_predictions"], exact["test_structural_holdout"], threshold,
        "pytorch.test_structural_holdout.raw_predictions",
    )
    validate_macro(result["test_structural_holdout"]["ensemble_metrics"], macro_metrics(structural_scores, structural_targets, threshold), "pytorch.test_structural_holdout.ensemble_metrics")
    for index, scores in enumerate(structural_seed_scores):
        validate_macro(result["test_structural_holdout"]["per_seed_metrics"][index], macro_metrics(scores, structural_targets, threshold), f"pytorch.test_structural_holdout.per_seed_metrics[{index}]")

    partition_receipts = [partition_metrics(scores, threshold, fixture.labels) for scores, fixture in zip(primary_scores, exact["test_primary"], strict=True)]
    require(len(result["test_primary"]["partition_metrics"]) == len(partition_receipts), "pytorch.test_primary.partition_metrics", "length mismatch")
    for index, expected in enumerate(partition_receipts):
        validate_partition_metric(result["test_primary"]["partition_metrics"][index], expected, f"pytorch.test_primary.partition_metrics[{index}]")
    macro_ari = sum(item["adjusted_rand_index"] for item in partition_receipts) / len(partition_receipts)
    macro_nvi = sum(item["normalized_variation_of_information"] for item in partition_receipts) / len(partition_receipts)
    close_float(result["test_primary"]["partition_macro_ari"], macro_ari, "pytorch.test_primary.partition_macro_ari")
    close_float(result["test_primary"]["partition_macro_normalized_vi"], macro_nvi, "pytorch.test_primary.partition_macro_normalized_vi")

    sensitive_mask = [
        any(target[index] for target in primary_targets)
        and not all(target[index] for target in primary_targets)
        for index in range(PAIR_COUNT)
    ]
    sensitive_scores = [
        score for fixture_scores in primary_scores
        for index, score in enumerate(fixture_scores) if sensitive_mask[index]
    ]
    sensitive_targets = [
        truth for fixture_targets in primary_targets
        for index, truth in enumerate(fixture_targets) if sensitive_mask[index]
    ]
    sensitive_expected = scored_metrics(sensitive_scores, sensitive_targets, threshold)
    rule_sensitive = result["test_primary"]["rule_sensitive"]
    validate_metric(rule_sensitive["model"], sensitive_expected, "pytorch.test_primary.rule_sensitive.model")
    require(rule_sensitive["state_pair_count"] == sum(sensitive_mask), "pytorch.test_primary.rule_sensitive.state_pair_count", "sensitive-pair count mismatch")
    require(rule_sensitive["observation_count"] == len(sensitive_targets), "pytorch.test_primary.rule_sensitive.observation_count", "sensitive observation count mismatch")
    require(rule_sensitive["state_pair_mask_sha256"] == canonical_hash(sensitive_mask), "pytorch.test_primary.rule_sensitive.state_pair_mask_sha256", "sensitive mask hash mismatch")
    best_name = rule_sensitive["best_rule_blind_baseline"]
    require(best_name in rule_sensitive["rule_blind_baselines"], "pytorch.test_primary.rule_sensitive.best_rule_blind_baseline", "unknown baseline")
    best_mcc = rule_sensitive["rule_blind_baselines"][best_name]["mcc"]
    close_float(
        rule_sensitive["mcc_advantage_over_best_rule_blind"],
        sensitive_expected["mcc"] - best_mcc,
        "pytorch.test_primary.rule_sensitive.mcc_advantage_over_best_rule_blind",
    )

    controls = result["controls"]
    control_metrics = {
        name: validate_control_raw(controls[name], exact["test_primary"], primary_targets, f"pytorch.controls.{name}")
        for name in (
            "same_weight_edge_erasure", "retrained_edge_erasure", "same_weight_probe_erasure",
            "same_weight_zero_transition_information", "same_weight_rule_identity_permutation",
            "shuffled_training_labels", "optimizer_erasure",
        )
    }
    score_hash_sources = {
        "same_weight_edge_erasure": "same_weight_edge_erasure",
        "retrained_edge_erasure": "retrained_edge_erasure",
        "probe_erasure": "same_weight_probe_erasure",
        "zero_transition": "same_weight_zero_transition_information",
        "rule_permutation": "same_weight_rule_identity_permutation",
        "shuffled_labels": "shuffled_training_labels",
        "optimizer_erasure": "optimizer_erasure",
    }
    exact_keys(controls["claim_bearing_score_hashes"], set(score_hash_sources), "pytorch.controls.claim_bearing_score_hashes")
    for receipt_name, control_name in score_hash_sources.items():
        raw_scores = [row["ensemble_scores"] for row in controls[control_name]["raw_scores"]]
        require(
            controls["claim_bearing_score_hashes"][receipt_name] == canonical_hash(raw_scores),
            f"pytorch.controls.claim_bearing_score_hashes.{receipt_name}",
            "raw score hash mismatch",
        )
    symmetry_expected = []
    for scores in primary_scores:
        state_swap = max(
            abs(scores[left * STATE_COUNT + right] - scores[right * STATE_COUNT + left])
            for left in range(STATE_COUNT) for right in range(STATE_COUNT)
        )
        rotation = 0.0
        for offset in range(RING_SIZE):
            rotated = []
            for state in range(STATE_COUNT):
                state_bits = bits(state)
                value = 0
                for site in range(RING_SIZE):
                    value |= state_bits[(site - offset) % RING_SIZE] << site
                rotated.append(value)
            rotation = max(
                rotation,
                max(
                    abs(scores[left * STATE_COUNT + right] - scores[rotated[left] * STATE_COUNT + rotated[right]])
                    for left in range(STATE_COUNT) for right in range(STATE_COUNT)
                ),
            )
        symmetry_expected.append({"state_swap_max_abs": state_swap, "cyclic_rotation_max_abs": rotation})
    require(len(controls["state_and_rotation_invariance"]) == len(symmetry_expected), "pytorch.controls.state_and_rotation_invariance", "length mismatch")
    for index, expected in enumerate(symmetry_expected):
        close_float(controls["state_and_rotation_invariance"][index]["state_swap_max_abs"], expected["state_swap_max_abs"], f"pytorch.controls.state_and_rotation_invariance[{index}].state_swap_max_abs")
        close_float(controls["state_and_rotation_invariance"][index]["cyclic_rotation_max_abs"], expected["cyclic_rotation_max_abs"], f"pytorch.controls.state_and_rotation_invariance[{index}].cyclic_rotation_max_abs")

    mutation = controls["one_bit_transition_mutation"]
    mutated = exact_fixture("mutation", [exact["test_primary"][0].rules[0] ^ 1, exact["test_primary"][0].rules[1]])
    require(mutation["original_partition_sha256"] == exact["test_primary"][0].partition_sha256, "pytorch.controls.one_bit_transition_mutation.original_partition_sha256", "original hash mismatch")
    require(mutation["mutated_partition_sha256"] == mutated.partition_sha256, "pytorch.controls.one_bit_transition_mutation.mutated_partition_sha256", "mutated hash mismatch")
    require(mutation["label_hash_changed"] is (mutated.partition_sha256 != exact["test_primary"][0].partition_sha256), "pytorch.controls.one_bit_transition_mutation.label_hash_changed", "classification mismatch")
    require(mutation["behaviorally_silent"] is (mutated.partition_sha256 == exact["test_primary"][0].partition_sha256), "pytorch.controls.one_bit_transition_mutation.behaviorally_silent", "classification mismatch")

    structural_hashes = [fixture.partition_sha256 for fixture in exact["test_structural_holdout"]]
    train_validation_hashes = {
        fixture.partition_sha256 for group in ("train", "validation") for fixture in exact[group]
    }
    binding = result["test_structural_holdout"]["frozen_hash_binding"]
    exact_keys(binding, {"expected_hashes", "observed_hashes", "expected_hashes_match", "excluded_from_train_and_validation"}, "pytorch.test_structural_holdout.frozen_hash_binding")
    require(binding["observed_hashes"] == sorted(structural_hashes), "pytorch.test_structural_holdout.frozen_hash_binding.observed_hashes", "structural hash mismatch")
    require(binding["expected_hashes"] == sorted(packet.spec["behavioral_partition_hash"]["structural_holdout_hashes_excluded_from_train_and_validation"]), "pytorch.test_structural_holdout.frozen_hash_binding.expected_hashes", "frozen hash mismatch")
    require(binding["expected_hashes_match"] is True and binding["excluded_from_train_and_validation"] is True, "pytorch.test_structural_holdout.frozen_hash_binding", "structural binding gate red")
    gates = result["gates"]
    expected_gate_keys = set(packet.spec["primary_learning_gates"])
    require(set(gates) == {
        "test_primary_macro_mcc_at_least_0_55", "test_primary_macro_balanced_accuracy_at_least_0_78",
        "test_primary_macro_positive_recall_at_least_0_65", "test_primary_macro_false_positive_rate_at_most_0_04",
        "rule_sensitive_mcc_at_least_0_50", "rule_sensitive_advantage_at_least_0_15",
        "every_seed_macro_mcc_at_least_0_35", "predicted_partition_macro_ari_at_least_0_75",
        "predicted_partition_macro_nvi_at_most_0_20", "zero_relation_law_violations",
        "state_swap_invariance", "action_swap_invariance", "cyclic_rotation_invariance",
        "zero_transition_information_mcc_drop_at_least_0_15", "retrained_ring_edge_erasure_mcc_drop_at_least_0_10",
        "shuffled_training_label_test_mcc_at_most_0_05", "structural_holdout_report_present",
        "one_bit_transition_mutation_classified", "structural_holdout_hashes_bound",
        "structural_holdout_hashes_excluded_from_train_validation",
    }, "pytorch.gates", f"gate schema drift from frozen contract {sorted(expected_gate_keys)}")
    recomputed_gates = {
        "test_primary_macro_mcc_at_least_0_55": primary_macro["macro_mcc"] >= 0.55,
        "test_primary_macro_balanced_accuracy_at_least_0_78": primary_macro["macro_balanced_accuracy"] >= 0.78,
        "test_primary_macro_positive_recall_at_least_0_65": primary_macro["macro_positive_recall"] >= 0.65,
        "test_primary_macro_false_positive_rate_at_most_0_04": primary_macro["macro_false_positive_rate"] <= 0.04,
        "rule_sensitive_mcc_at_least_0_50": sensitive_expected["mcc"] >= 0.50,
        "rule_sensitive_advantage_at_least_0_15": rule_sensitive["mcc_advantage_over_best_rule_blind"] >= 0.15,
        "every_seed_macro_mcc_at_least_0_35": min(item["macro_mcc"] for item in seed_macros) >= 0.35,
        "predicted_partition_macro_ari_at_least_0_75": macro_ari >= 0.75,
        "predicted_partition_macro_nvi_at_most_0_20": macro_nvi <= 0.20,
        "zero_relation_law_violations": all(item["relation_laws_pass"] for item in partition_receipts),
        "zero_transition_information_mcc_drop_at_least_0_15": primary_macro["macro_mcc"] - control_metrics["same_weight_zero_transition_information"]["macro_mcc"] >= 0.15,
        "retrained_ring_edge_erasure_mcc_drop_at_least_0_10": primary_macro["macro_mcc"] - control_metrics["retrained_edge_erasure"]["macro_mcc"] >= 0.10,
        "shuffled_training_label_test_mcc_at_most_0_05": control_metrics["shuffled_training_labels"]["macro_mcc"] <= 0.05,
        "state_swap_invariance": max(item["state_swap_max_abs"] for item in symmetry_expected) <= 1e-10,
        "action_swap_invariance": controls["action_swap_max_abs"] <= 1e-10,
        "cyclic_rotation_invariance": max(item["cyclic_rotation_max_abs"] for item in symmetry_expected) <= 1e-8,
        "structural_holdout_report_present": len(exact["test_structural_holdout"]) == 2,
        "one_bit_transition_mutation_classified": mutation["label_hash_changed"] or mutation["behaviorally_silent"],
        "structural_holdout_hashes_bound": set(structural_hashes) == set(binding["expected_hashes"]),
        "structural_holdout_hashes_excluded_from_train_validation": not bool(set(structural_hashes) & train_validation_hashes),
    }
    for key, expected in recomputed_gates.items():
        require(gates[key] is expected, f"pytorch.gates.{key}", "not reconstructed from raw predictions")
    reported_reds = {key for key, passed in gates.items() if passed is False}
    require(reported_reds == KNOWN_PYTORCH_REDS, "pytorch.gates", f"scientific red set drifted: {sorted(reported_reds)}")
    require(result["all_pass"] is False, "pytorch.all_pass", "must remain false while frozen gates are red")
    require(result["claim_ceiling"]["current_label"] == "HELD_OUT_RULE_PROXY_GATES_RED", "pytorch.claim_ceiling.current_label", "red ceiling removed")
    require(result["claim_ceiling"]["T9_runtime_nonredundancy_earned"] is False, "pytorch.claim_ceiling.T9", "T9 must remain unearned")
    require(result["claim_ceiling"]["blocked_consumers"] == packet.spec["blocked_consumers"], "pytorch.claim_ceiling.blocked_consumers", "blocked consumers changed")
    return {
        "primary_macro_mcc": primary_macro["macro_mcc"],
        "minimum_seed_macro_mcc": min(item["macro_mcc"] for item in seed_macros),
        "shuffled_label_macro_mcc": control_metrics["shuffled_training_labels"]["macro_mcc"],
        "scientific_red_gates": sorted(reported_reds),
        "raw_prediction_metrics_recomputed": True,
        "T9_earned": False,
    }


def validate_claim_ceiling(packet: Packet) -> None:
    blocked = packet.spec["blocked_consumers"]
    require(blocked, "spec.blocked_consumers", "ceiling removal")
    require(packet.julia["blocked_consumers"] == blocked and packet.jax["blocked_consumers"] == blocked, "engine.blocked_consumers", "ceiling mismatch")
    require(packet.pytorch["claim_ceiling"]["blocked_consumers"] == blocked, "pytorch.claim_ceiling.blocked_consumers", "ceiling mismatch")
    require(packet.julia["tests"]["T9_counterfactual_adaptive_replaceability"] is False, "julia.T9", "must remain false")
    require(packet.jax["tests"]["T9_adaptive_replaceability_boundary"]["pass"] is False, "jax.T9", "must remain false")
    require(packet.pytorch["claim_ceiling"]["T9_runtime_nonredundancy_earned"] is False, "pytorch.T9", "must remain false")


def validate_packet(packet: Packet, *, enforce_source_hashes: bool = True) -> dict[str, Any]:
    frozen = validate_frozen_inputs(packet)
    orbits = ordered_orbits()
    split = validate_split(packet.spec, orbits)
    exact = build_exact_fixtures(packet.spec)
    source_bindings = validate_source_bindings(packet) if enforce_source_hashes else {}
    julia = validate_julia(packet, exact, orbits)
    jax = validate_jax(packet, exact, orbits)
    pytorch = validate_pytorch(packet, exact)
    validate_claim_ceiling(packet)
    return {
        "frozen_inputs": frozen,
        "split": split,
        "source_result_bindings": source_bindings,
        "julia": julia,
        "jax": jax,
        "pytorch": pytorch,
    }


def expect_rejection(name: str, packet: Packet, mutate: Callable[[Packet], None], needle: str) -> dict[str, Any]:
    candidate = copy.deepcopy(packet)
    mutate(candidate)
    try:
        validate_packet(candidate, enforce_source_hashes=True)
    except ValidationError as exc:
        message = str(exc)
        require(needle in message, f"corruption_tests.{name}", f"wrong rejection: {message}")
        return {"passed": True, "rejected_with": message}
    raise ValidationError(f"corruption_tests.{name}: coherent corruption escaped validation")


def run_corruption_tests(packet: Packet) -> dict[str, Any]:
    def leak(candidate: Packet) -> None:
        candidate.spec["fixtures"]["validation"][0][0] = candidate.spec["fixtures"]["train"][0][0]
        candidate.spec["fixtures"]["validation"].sort(key=pair_hash)

    def source_hash(candidate: Packet) -> None:
        candidate.jax["source_sha256"] = "0" * 64

    def metric(candidate: Packet) -> None:
        candidate.pytorch["test_primary"]["ensemble_metrics"]["macro_mcc"] = 0.123
        candidate.pytorch["test_primary"]["ensemble_metrics"]["per_fixture"][0]["mcc"] = 0.123

    def ceiling(candidate: Packet) -> None:
        candidate.pytorch["claim_ceiling"]["current_label"] = candidate.spec["allowed_claim_label_if_all_learning_gates_pass"]
        candidate.pytorch["claim_ceiling"]["T9_runtime_nonredundancy_earned"] = True
        candidate.pytorch["claim_ceiling"]["blocked_consumers"] = []

    tests = {
        "symmetry_leakage": expect_rejection("symmetry_leakage", packet, leak, "outside frozen orbit block"),
        "source_hash": expect_rejection("source_hash", packet, source_hash, "live source/result binding mismatch"),
        "raw_metric": expect_rejection("raw_metric", packet, metric, "metric mismatch"),
        "ceiling_removal": expect_rejection("ceiling_removal", packet, ceiling, "red ceiling removed"),
    }
    return {"kind": "in_memory_coherent_corruption", "all_pass": all(item["passed"] for item in tests.values()), "tests": tests}


def success_receipt(packet: Packet, validation: dict[str, Any]) -> dict[str, Any]:
    corruption = run_corruption_tests(packet)
    require(corruption["all_pass"], "corruption_tests", "one or more corruptions escaped")
    return {
        "schema": "codex_ratchet.finite_probe_behavioral_object_engine_v1.controller_validation.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "artifact_validation_all_pass": True,
        "all_scientific_gates_pass": False,
        "accepted_claim_label": "EXACT_CROSS_RUNTIME_CORE_WITH_LEARNING_GATES_RED",
        "scientific_red_gates": [
            "pytorch.every_seed_macro_mcc_at_least_0.35",
            "pytorch.shuffled_training_label_test_mcc_at_most_0.05",
            "T9.counterfactual_evidence_contribution_and_adaptive_replaceability",
        ],
        "validation": validation,
        "T9_output_vector": {
            "role_contribution": "exact Julia/JAX replication and PyTorch learned-proxy evidence are measured only in their assigned roles",
            "runtime_replaceability": "unearned; no role-neutral 3x3 adaptive replacement matrix ran",
            "resource_advantage": "unearned; no frozen equal-budget replacement comparison ran",
            "diversity_gain": "unearned; no blinded unique-fault-detection and common-mode analysis ran",
            "claim_ceiling": "multi-engine execution with exact-role parity and a red learned proxy; no runtime non-substitutability or engine intelligence",
        },
        "corruption_tests": corruption,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "blocked_consumers": packet.spec["blocked_consumers"],
        "validator_source_sha256": sha256_file(Path(__file__)),
    }


def failure_receipt(error: Exception) -> dict[str, Any]:
    return {
        "schema": "codex_ratchet.finite_probe_behavioral_object_engine_v1.controller_validation.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "artifact_validation_all_pass": False,
        "all_scientific_gates_pass": False,
        "accepted_claim_label": "VALIDATOR_REJECTED_PACKET",
        "error": f"{type(error).__name__}: {error}",
        "T9_output_vector": {
            "role_contribution": "not accepted",
            "runtime_replaceability": "unearned",
            "resource_advantage": "unearned",
            "diversity_gain": "unearned",
            "claim_ceiling": "no scientific claim after validator rejection",
        },
        "corruption_tests": "not_run_after_base_validation_failure",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "blocked_consumers": "all downstream scientific consumers",
        "validator_source_sha256": sha256_file(Path(__file__)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        packet = load_packet()
        receipt = success_receipt(packet, validate_packet(packet))
        exit_code = 0
    except Exception as exc:  # fail-closed receipt is intentional
        receipt = failure_receipt(exc)
        exit_code = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"artifact_validation_all_pass": receipt["artifact_validation_all_pass"], "output": str(args.output)}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
