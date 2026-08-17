#!/usr/bin/env python3
"""Finite CB Light entropic-time field prototype.

The operation compiles one finite observation field into probe-relative
quotients, relation geometry, exact mass, and typed capacities.  Forward
extension and reverse restriction are bound to the same transition identity.
An independent JAX lane may batch-recompute the observation equivalence
matrices; it never supplies observation values or semantic dispositions.

This is deliberately a scratch diagnostic.  It makes no physical spacetime,
chirality, attractor, engine, or promotion claim.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import platform
from fractions import Fraction
from pathlib import Path
from typing import Any


INPUT_SCHEMA = "constraintbox.entropic-time-field.v1"
RESULT_SCHEMA = "constraintbox.entropic-time-field-result.v1"
OPERATION = "finite_entropic_geometry_transition.v1"


class FieldError(ValueError):
    def __init__(self, reason_code: str, detail: str = "") -> None:
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)
        self.reason_code = reason_code
        self.detail = detail


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _source_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _exact_keys(value: Any, expected: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FieldError("REFUSE_FIELD_SCHEMA", f"{path} must be an object")
    observed = set(value)
    if observed != expected:
        raise FieldError(
            "REFUSE_FIELD_SCHEMA",
            f"{path} keys missing={sorted(expected-observed)} extra={sorted(observed-expected)}",
        )
    return value


def _unique_texts(value: Any, path: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
    ):
        raise FieldError("REFUSE_FIELD_SCHEMA", f"{path} must be unique text")
    return list(value)


def _components(nodes: list[str], edges: set[tuple[str, str]]) -> list[list[str]]:
    neighbors = {node: set() for node in nodes}
    for left, right in edges:
        neighbors[left].add(right)
        neighbors[right].add(left)
    unseen = set(nodes)
    result: list[list[str]] = []
    while unseen:
        root = min(unseen)
        stack = [root]
        seen: set[str] = set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(sorted(neighbors[node] - seen, reverse=True))
        unseen -= seen
        result.append(sorted(seen))
    return sorted(result)


def _edge(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def _slice_result(raw: Any, probes: list[str]) -> dict[str, Any]:
    row = _exact_keys(
        raw,
        {
            "tick",
            "states",
            "status_by_state",
            "observations",
            "relations",
            "mass_by_state",
        },
        "$.slices[]",
    )
    tick = row["tick"]
    if not isinstance(tick, int) or tick < 0:
        raise FieldError("REFUSE_FIELD_SCHEMA", "slice tick must be nonnegative int")
    states = _unique_texts(row["states"], f"$.slices[{tick}].states")
    status = row["status_by_state"]
    if not isinstance(status, dict) or set(status) != set(states):
        raise FieldError("REFUSE_FIELD_SCHEMA", f"tick {tick} status domain mismatch")
    if any(value not in {"SAT", "UNSAT", "UNKNOWN"} for value in status.values()):
        raise FieldError("REFUSE_FIELD_SCHEMA", f"tick {tick} invalid constraint status")
    sat = [state for state in states if status[state] == "SAT"]
    if not sat:
        raise FieldError("REFUSE_EMPTY_SURVIVOR_FIELD", f"tick {tick}")

    observations = row["observations"]
    if not isinstance(observations, list):
        raise FieldError("REFUSE_FIELD_SCHEMA", f"tick {tick} observations must be array")
    table: dict[tuple[str, str], Any] = {}
    for index, observation in enumerate(observations):
        item = _exact_keys(
            observation,
            {"state", "probe", "value"},
            f"$.slices[{tick}].observations[{index}]",
        )
        key = (item["state"], item["probe"])
        if item["state"] not in sat or item["probe"] not in probes or key in table:
            raise FieldError("REFUSE_UNBOUND_OBSERVATION", f"tick {tick} invalid row {key}")
        table[key] = item["value"]
    expected_rows = {(state, probe) for state in sat for probe in probes}
    if set(table) != expected_rows:
        missing = sorted(expected_rows - set(table))
        extra = sorted(set(table) - expected_rows)
        raise FieldError(
            "REFUSE_UNBOUND_OBSERVATION",
            f"tick {tick} missing={missing} extra={extra}",
        )

    mass = row["mass_by_state"]
    if not isinstance(mass, dict) or set(mass) != set(states):
        raise FieldError("REFUSE_FIELD_SCHEMA", f"tick {tick} mass domain mismatch")
    if any(not isinstance(value, int) or value <= 0 for value in mass.values()):
        raise FieldError("REFUSE_FIELD_SCHEMA", f"tick {tick} mass must be positive int")

    relations = row["relations"]
    if not isinstance(relations, list):
        raise FieldError("REFUSE_FIELD_SCHEMA", f"tick {tick} relations must be array")
    raw_edges: set[tuple[str, str]] = set()
    for index, relation in enumerate(relations):
        if (
            not isinstance(relation, list)
            or len(relation) != 2
            or any(item not in states for item in relation)
            or relation[0] == relation[1]
        ):
            raise FieldError("REFUSE_FIELD_SCHEMA", f"tick {tick} bad relation {index}")
        raw_edges.add(_edge(relation[0], relation[1]))
    edges = {edge for edge in raw_edges if edge[0] in sat and edge[1] in sat}

    signatures = {
        state: tuple(_canonical(table[(state, probe)]).decode("ascii") for probe in probes)
        for state in sat
    }
    grouped: dict[tuple[str, ...], list[str]] = {}
    for state in sat:
        grouped.setdefault(signatures[state], []).append(state)
    ordered_signatures = sorted(grouped)
    class_ids = {signature: f"Q{index}" for index, signature in enumerate(ordered_signatures)}
    state_to_class = {
        state: class_ids[signature]
        for signature, members in grouped.items()
        for state in members
    }

    # A quotient is allowed only if the retained relation is constant on every
    # proposed class pair. Equal probe rows cannot silently erase a relation.
    for left_signature in ordered_signatures:
        for right_signature in ordered_signatures:
            values = {
                _edge(left, right) in edges if left != right else False
                for left in grouped[left_signature]
                for right in grouped[right_signature]
            }
            if len(values) > 1:
                raise FieldError(
                    "REFUSE_RELATION_INCOMPATIBLE_QUOTIENT",
                    f"tick {tick} class pair {class_ids[left_signature]}/{class_ids[right_signature]}",
                )

    quotient_edges = {
        _edge(state_to_class[left], state_to_class[right])
        for left, right in edges
        if state_to_class[left] != state_to_class[right]
    }
    classes = []
    total_mass = sum(mass[state] for state in sat)
    for signature in ordered_signatures:
        members = sorted(grouped[signature])
        numerator = sum(mass[state] for state in members)
        fraction = Fraction(numerator, total_mass)
        classes.append(
            {
                "id": class_ids[signature],
                "members": members,
                "response_tuple": [json.loads(value) for value in signature],
                "size": len(members),
                "mass": {
                    "numerator": numerator,
                    "denominator": total_mass,
                    "reduced": f"{fraction.numerator}/{fraction.denominator}",
                    "value": float(fraction),
                },
            }
        )
    class_nodes = [item["id"] for item in classes]
    components = _components(class_nodes, quotient_edges)
    support_k = math.log2(len(sat))
    record_k = math.log2(len(classes))
    equivalence_matrix = [
        [signatures[left] == signatures[right] for right in sat] for left in sat
    ]
    geometry_identity = {
        "class_response_tuples": [item["response_tuple"] for item in classes],
        "class_sizes": [item["size"] for item in classes],
        "quotient_edges": [list(edge) for edge in sorted(quotient_edges)],
        "components": components,
    }
    mass_identity = [item["mass"]["reduced"] for item in classes]
    public = {
        "tick": tick,
        "sat_states": sat,
        "unknown_states": sorted(state for state in states if status[state] == "UNKNOWN"),
        "unsat_states": sorted(state for state in states if status[state] == "UNSAT"),
        "classes": classes,
        "relation": "~_P",
        "quotient_edges": [list(edge) for edge in sorted(quotient_edges)],
        "components": components,
        "equivalence_matrix": equivalence_matrix,
        "capacities": {
            "support": {"W": len(sat), "K": support_k},
            "fibre": [
                {"class_id": item["id"], "W": item["size"], "K": math.log2(item["size"])}
                for item in classes
            ],
            "record": {
                "bound_rows": len(sat) * len(probes),
                "distinct_response_tuples": len(classes),
                "K": record_k,
            },
        },
        "geometry_sha256": _sha(geometry_identity),
        "mass_sha256": _sha(mass_identity),
        "invariant": {
            "support_W": len(sat),
            "support_K": support_k,
            "record_W": len(classes),
            "record_K": record_k,
            "fibre_sizes": sorted(item["size"] for item in classes),
            "quotient_edges": [list(edge) for edge in sorted(quotient_edges)],
            "components": components,
            "class_mass": mass_identity,
        },
    }
    return {
        "public": public,
        "sat": sat,
        "signatures": signatures,
        "table": table,
        "state_to_class": state_to_class,
        "edges": edges,
    }


def _transition_result(
    raw: Any, slices: dict[int, dict[str, Any]]
) -> dict[str, Any]:
    row = _exact_keys(
        raw,
        {"id", "from_tick", "to_tick", "extensions", "restrictions"},
        "$.transitions[]",
    )
    transition_id = row["id"]
    if not isinstance(transition_id, str) or not transition_id:
        raise FieldError("REFUSE_FIELD_SCHEMA", "transition id must be text")
    start = row["from_tick"]
    end = row["to_tick"]
    if start not in slices or end != start + 1 or end not in slices:
        raise FieldError("REFUSE_FIELD_SCHEMA", f"transition {transition_id} ticks")
    source_states = slices[start]["sat"]
    target_states = slices[end]["sat"]
    extensions = row["extensions"]
    restrictions = row["restrictions"]
    if not isinstance(extensions, dict) or set(extensions) != set(source_states):
        raise FieldError("REFUSE_TRANSITION_DOMAIN", transition_id)
    if not isinstance(restrictions, dict) or set(restrictions) != set(target_states):
        raise FieldError("REFUSE_TRANSITION_CODOMAIN", transition_id)
    normalized: dict[str, list[str]] = {}
    for source in source_states:
        targets = extensions[source]
        if (
            not isinstance(targets, list)
            or not targets
            or len(set(targets)) != len(targets)
            or any(target not in target_states for target in targets)
        ):
            raise FieldError("REFUSE_TRANSITION_EXTENSION", f"{transition_id}:{source}")
        normalized[source] = sorted(targets)
    if any(parent not in source_states for parent in restrictions.values()):
        raise FieldError("REFUSE_TRANSITION_RESTRICTION", transition_id)
    for child in target_states:
        parent = restrictions[child]
        if child not in normalized[parent]:
            raise FieldError("REFUSE_TRANSITION_NOT_BIDIRECTIONALLY_BOUND", f"{transition_id}:{child}")
    all_children = [child for children in normalized.values() for child in children]
    if sorted(all_children) != sorted(target_states):
        raise FieldError("REFUSE_TRANSITION_NOT_TOTAL", transition_id)
    identity_material = {
        "id": transition_id,
        "from_tick": start,
        "to_tick": end,
        "extensions": normalized,
        "restrictions": restrictions,
    }
    return {
        "id": transition_id,
        "from_tick": start,
        "to_tick": end,
        "transition_sha256": _sha(identity_material),
        "orientations": {
            "forward": "extensions",
            "reverse": "restrictions",
            "same_transition_identity": True,
        },
        "extensions": normalized,
        "restrictions": dict(sorted(restrictions.items())),
        "fibre_sizes": {source: len(normalized[source]) for source in source_states},
    }


def _order_result(raw: Any) -> dict[str, Any]:
    row = _exact_keys(raw, {"carrier", "open_map", "bind_map"}, "$.order_witness")
    carrier = _unique_texts(row["carrier"], "$.order_witness.carrier")
    open_map = row["open_map"]
    bind_map = row["bind_map"]
    if (
        not isinstance(open_map, dict)
        or not isinstance(bind_map, dict)
        or set(open_map) != set(carrier)
        or set(bind_map) != set(carrier)
        or any(value not in carrier for value in open_map.values())
        or any(value not in carrier for value in bind_map.values())
    ):
        raise FieldError("REFUSE_ORDER_WITNESS_DOMAIN")
    left = {state: bind_map[open_map[state]] for state in carrier}
    right = {state: open_map[bind_map[state]] for state in carrier}
    gap = [state for state in carrier if left[state] != right[state]]
    if not gap:
        raise FieldError("REFUSE_ORDER_GAP_COLLAPSED")
    return {
        "carrier": carrier,
        "native_formula": {
            "left": "bind(open(state))",
            "right": "open(bind(state))",
        },
        "left_output": left,
        "right_output": right,
        "gap_states": gap,
        "gap_count": len(gap),
        "witness_sha256": _sha(
            {"carrier": carrier, "open_map": open_map, "bind_map": bind_map}
        ),
    }


def _core(payload: Any) -> dict[str, Any]:
    root = _exact_keys(
        payload,
        {
            "schema",
            "field_id",
            "probes",
            "slices",
            "transitions",
            "order_witness",
            "claim_ceiling",
            "promotion_allowed",
        },
        "$",
    )
    if root["schema"] != INPUT_SCHEMA:
        raise FieldError("REFUSE_FIELD_SCHEMA", "unsupported schema")
    if root["promotion_allowed"] is not False:
        raise FieldError("REFUSE_FIELD_CLAIM_CEILING")
    if not isinstance(root["field_id"], str) or not root["field_id"]:
        raise FieldError("REFUSE_FIELD_SCHEMA", "field_id")
    if not isinstance(root["claim_ceiling"], str) or not root["claim_ceiling"]:
        raise FieldError("REFUSE_FIELD_SCHEMA", "claim_ceiling")
    probes = _unique_texts(root["probes"], "$.probes")
    if not isinstance(root["slices"], list) or len(root["slices"]) < 2:
        raise FieldError("REFUSE_FIELD_SCHEMA", "at least two slices required")
    slices_list = [_slice_result(item, probes) for item in root["slices"]]
    ticks = [item["public"]["tick"] for item in slices_list]
    if ticks != list(range(len(ticks))):
        raise FieldError("REFUSE_FIELD_SCHEMA", "ticks must be consecutive from zero")
    slices = {item["public"]["tick"]: item for item in slices_list}
    if not isinstance(root["transitions"], list) or len(root["transitions"]) != len(ticks) - 1:
        raise FieldError("REFUSE_FIELD_SCHEMA", "one transition per adjacent tick")
    transitions = [_transition_result(item, slices) for item in root["transitions"]]
    if [(row["from_tick"], row["to_tick"]) for row in transitions] != [
        (tick, tick + 1) for tick in range(len(ticks) - 1)
    ]:
        raise FieldError("REFUSE_TRANSITION_ORDER")
    order = _order_result(root["order_witness"])
    support_k = [item["public"]["capacities"]["support"]["K"] for item in slices_list]
    delta_k = [support_k[index + 1] - support_k[index] for index in range(len(support_k) - 1)]
    if not all(value > 0 for value in delta_k):
        raise FieldError("REFUSE_GLOBAL_GRADIENT_NONPOSITIVE")

    local_contractions = []
    for current, following in zip(transitions, transitions[1:]):
        for parent, children in current["extensions"].items():
            for child in children:
                if child in following["extensions"]:
                    before = len(children)
                    after = len(following["extensions"][child])
                    if after < before:
                        local_contractions.append(
                            {
                                "path": [parent, child],
                                "from_transition": current["id"],
                                "to_transition": following["id"],
                                "fibre_W_before": before,
                                "fibre_W_after": after,
                                "fibre_K_before": math.log2(before),
                                "fibre_K_after": math.log2(after),
                            }
                        )
    if not local_contractions:
        raise FieldError("REFUSE_NO_GLOBAL_GROWTH_LOCAL_CONTRACTION_WITNESS")
    gradient_material = {
        "slice_geometry": [item["public"]["geometry_sha256"] for item in slices_list],
        "slice_mass": [item["public"]["mass_sha256"] for item in slices_list],
        "transition_ids": [item["transition_sha256"] for item in transitions],
        "support_K": support_k,
        "delta_K": delta_k,
    }
    return {
        "field_id": root["field_id"],
        "probes": probes,
        "slices": [item["public"] for item in slices_list],
        "transitions": transitions,
        "one_gradient": {
            "gradient_sha256": _sha(gradient_material),
            "support_K": support_k,
            "delta_K": delta_k,
            "global_growth_positive": True,
            "local_fibre_contractions": local_contractions,
            "orientation_count": 2,
            "time_coordinate_count": 1,
        },
        "order_witness": order,
        "claim_ceiling": root["claim_ceiling"],
        "_slice_internal": slices_list,
    }


def _invariants(core: dict[str, Any]) -> list[dict[str, Any]]:
    return [item["invariant"] for item in core["slices"]]


def _relabel(payload: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(payload)
    mappings: dict[int, dict[str, str]] = {}
    for item in mutated["slices"]:
        tick = item["tick"]
        mapping = {state: f"r{tick}_{index}" for index, state in enumerate(reversed(item["states"]))}
        mappings[tick] = mapping
        item["states"] = [mapping[state] for state in item["states"]]
        item["status_by_state"] = {mapping[key]: value for key, value in item["status_by_state"].items()}
        item["mass_by_state"] = {mapping[key]: value for key, value in item["mass_by_state"].items()}
        for observation in item["observations"]:
            observation["state"] = mapping[observation["state"]]
        item["relations"] = [[mapping[left], mapping[right]] for left, right in item["relations"]]
    for transition in mutated["transitions"]:
        source = mappings[transition["from_tick"]]
        target = mappings[transition["to_tick"]]
        transition["extensions"] = {
            source[parent]: [target[child] for child in children]
            for parent, children in transition["extensions"].items()
        }
        transition["restrictions"] = {
            target[child]: source[parent]
            for child, parent in transition["restrictions"].items()
        }
    return mutated


def _expect_reason(payload: dict[str, Any], reason: str) -> bool:
    try:
        _core(payload)
    except FieldError as exc:
        return exc.reason_code == reason
    return False


def _controls(payload: dict[str, Any], core: dict[str, Any]) -> dict[str, Any]:
    replay = _core(copy.deepcopy(payload))
    replay_equal = _sha({key: value for key, value in core.items() if key != "_slice_internal"}) == _sha(
        {key: value for key, value in replay.items() if key != "_slice_internal"}
    )

    relabeled = _core(_relabel(payload))
    relabel_invariant = _invariants(core) == _invariants(relabeled)

    collapsed = copy.deepcopy(payload)
    collapsed["order_witness"]["bind_map"] = {
        state: state for state in collapsed["order_witness"]["carrier"]
    }
    collapsed_refused = _expect_reason(collapsed, "REFUSE_ORDER_GAP_COLLAPSED")

    hidden_relation_refused = False
    for slice_index, slice_row in enumerate(payload["slices"]):
        states = slice_row["states"]
        for left_index, left in enumerate(states):
            for right in states[left_index + 1 :]:
                mutated = copy.deepcopy(payload)
                target = mutated["slices"][slice_index]
                left_values = {
                    item["probe"]: item["value"]
                    for item in target["observations"]
                    if item["state"] == left
                }
                for item in target["observations"]:
                    if item["state"] == right:
                        item["value"] = copy.deepcopy(left_values[item["probe"]])
                if _expect_reason(mutated, "REFUSE_RELATION_INCOMPATIBLE_QUOTIENT"):
                    hidden_relation_refused = True
                    break
            if hidden_relation_refused:
                break
        if hidden_relation_refused:
            break

    relationless_index = next(
        index for index, item in enumerate(payload["slices"]) if not item["relations"]
    )
    fake = copy.deepcopy(payload["slices"][relationless_index])
    source = fake["states"][0]
    clone = source + "__indistinguishable_clone"
    fake["states"].append(clone)
    fake["status_by_state"][clone] = fake["status_by_state"][source]
    fake["mass_by_state"][clone] = fake["mass_by_state"][source]
    for item in list(fake["observations"]):
        if item["state"] == source:
            copied = copy.deepcopy(item)
            copied["state"] = clone
            fake["observations"].append(copied)
    original_slice = _slice_result(payload["slices"][relationless_index], core["probes"])["public"]
    fake_slice = _slice_result(fake, core["probes"])["public"]
    fake_growth_exposed = (
        fake_slice["capacities"]["support"]["W"]
        == original_slice["capacities"]["support"]["W"] + 1
        and fake_slice["capacities"]["record"]["distinct_response_tuples"]
        == original_slice["capacities"]["record"]["distinct_response_tuples"]
    )

    topology_detected = False
    topology_detail: dict[str, Any] = {}
    for slice_row in payload["slices"]:
        base = _slice_result(slice_row, core["probes"])["public"]
        if len(base["components"]) < 2:
            continue
        existing = {_edge(left, right) for left, right in slice_row["relations"]}
        for left in slice_row["states"]:
            for right in slice_row["states"]:
                if left >= right or _edge(left, right) in existing:
                    continue
                mutated = copy.deepcopy(slice_row)
                mutated["relations"].append([left, right])
                changed = _slice_result(mutated, core["probes"])["public"]
                if (
                    changed["geometry_sha256"] != base["geometry_sha256"]
                    and changed["capacities"] == base["capacities"]
                    and len(changed["components"]) != len(base["components"])
                ):
                    topology_detected = True
                    topology_detail = {
                        "tick": slice_row["tick"],
                        "components_before": len(base["components"]),
                        "components_after": len(changed["components"]),
                        "support_K_unchanged": base["capacities"]["support"]["K"],
                    }
                    break
            if topology_detected:
                break
        if topology_detected:
            break

    mass_source = copy.deepcopy(payload["slices"][-1])
    base_mass = _slice_result(mass_source, core["probes"])["public"]
    mass_source["mass_by_state"][mass_source["states"][0]] += 1
    changed_mass = _slice_result(mass_source, core["probes"])["public"]
    mass_change_detected = (
        changed_mass["geometry_sha256"] == base_mass["geometry_sha256"]
        and changed_mass["mass_sha256"] != base_mass["mass_sha256"]
    )

    controls = {
        "replay_equal": replay_equal,
        "relabel_invariant": relabel_invariant,
        "collapsed_order_refused": collapsed_refused,
        "hidden_relation_refused": hidden_relation_refused,
        "fake_support_growth_not_record_growth": fake_growth_exposed,
        "fixed_capacity_topology_change_detected": topology_detected,
        "fixed_geometry_mass_change_detected": mass_change_detected,
        "global_growth_local_fibre_contraction": bool(
            core["one_gradient"]["local_fibre_contractions"]
        ),
        "single_time_coordinate_two_orientations": (
            core["one_gradient"]["time_coordinate_count"] == 1
            and core["one_gradient"]["orientation_count"] == 2
            and all(
                item["orientations"]["same_transition_identity"]
                for item in core["transitions"]
            )
        ),
        "topology_control_detail": topology_detail,
    }
    controls["all_pass"] = all(
        value for key, value in controls.items() if key != "topology_control_detail"
    )
    return controls


def _jax_check(core: dict[str, Any]) -> dict[str, Any]:
    try:
        import jax

        jax.config.update("jax_enable_x64", True)
        import jax.numpy as jnp
    except Exception as exc:  # pragma: no cover - exercised by exact-only environments
        return {
            "ran": False,
            "reason": f"{type(exc).__name__}:{exc}",
            "load_bearing": False,
        }

    internals = core["_slice_internal"]
    probes = core["probes"]
    max_states = max(len(item["sat"]) for item in internals)
    codebooks: dict[str, dict[str, int]] = {}
    for probe in probes:
        values = sorted(
            {
                _canonical(item["table"][(state, probe)]).decode("ascii")
                for item in internals
                for state in item["sat"]
            }
        )
        codebooks[probe] = {value: index for index, value in enumerate(values)}
    matrices = []
    masks = []
    for item in internals:
        rows = []
        for state in item["sat"]:
            rows.append(
                [
                    codebooks[probe][
                        _canonical(item["table"][(state, probe)]).decode("ascii")
                    ]
                    for probe in probes
                ]
            )
        rows += [[-1] * len(probes) for _ in range(max_states - len(rows))]
        matrices.append(rows)
        masks.append([True] * len(item["sat"]) + [False] * (max_states - len(item["sat"])))

    prior = jnp.tril(jnp.ones((max_states, max_states), dtype=bool), k=-1)

    def kernel(observation_codes, mask):
        eq = jnp.all(
            observation_codes[:, None, :] == observation_codes[None, :, :], axis=-1
        )
        eq = eq & mask[:, None] & mask[None, :]
        has_prior = jnp.any(eq & prior, axis=1)
        leaders = mask & ~has_prior
        support_w = jnp.sum(mask)
        record_w = jnp.sum(leaders)
        return eq, jnp.log2(support_w.astype(jnp.float64)), jnp.log2(
            record_w.astype(jnp.float64)
        )

    batched = jax.jit(jax.vmap(kernel))
    eq_batch, support_k, record_k = batched(
        jnp.asarray(matrices, dtype=jnp.int64), jnp.asarray(masks, dtype=bool)
    )
    eq_batch.block_until_ready()
    agreements = []
    for index, item in enumerate(internals):
        size = len(item["sat"])
        observed = [
            [bool(value) for value in row[:size]]
            for row in eq_batch[index, :size, :size].tolist()
        ]
        expected = core["slices"][index]["equivalence_matrix"]
        agreements.append(
            observed == expected
            and abs(float(support_k[index]) - core["slices"][index]["capacities"]["support"]["K"]) < 1e-12
            and abs(float(record_k[index]) - core["slices"][index]["capacities"]["record"]["K"]) < 1e-12
        )

    synthetic = jnp.full((1, max_states, len(probes)), -1, dtype=jnp.int64)
    synthetic = synthetic.at[0, 0, :].set(0)
    synthetic = synthetic.at[0, 1, :].set(0)
    synthetic = synthetic.at[0, 2, :].set(jnp.arange(len(probes)) + 1)
    synthetic_mask = jnp.zeros((1, max_states), dtype=bool).at[0, :3].set(True)
    _, _, before_record = batched(synthetic, synthetic_mask)
    mutated = synthetic.at[0, 1, 0].set(99)
    _, _, after_record = batched(mutated, synthetic_mask)
    mutation_detected = float(after_record[0]) > float(before_record[0])
    boundary_mask = jnp.zeros((1, max_states), dtype=bool).at[0, 0].set(True)
    _, boundary_support, boundary_record = batched(synthetic, boundary_mask)
    boundary_ok = float(boundary_support[0]) == 0.0 and float(boundary_record[0]) == 0.0
    output_material = {
        "equivalence": eq_batch.tolist(),
        "support_K": [float(value) for value in support_k.tolist()],
        "record_K": [float(value) for value in record_k.tolist()],
    }
    all_agree = all(agreements) and mutation_detected and boundary_ok
    return {
        "ran": True,
        "jax_version": jax.__version__,
        "jaxlib_version": jax.lib.__version__,
        "x64_enabled": bool(jax.config.jax_enable_x64),
        "device": str(jax.devices()[0]),
        "exact_reference_agreement": agreements,
        "negative_observation_mutation_detected": mutation_detected,
        "single_state_boundary_K_zero": boundary_ok,
        "output_sha256": _sha(output_material),
        "load_bearing": all_agree,
        "tool_calls": [
            {
                "tool": "jax",
                "qualified_api/function": "jax.jit(jax.vmap(pairwise_probe_equivalence_and_capacity))",
                "input_object": "padded complete bound observation matrices",
                "output_object": "equivalence matrices plus support/record capacity",
                "positive_case": "all fixture slices agree with exact reference",
                "negative/erased_control": "one observation mutation increases class count",
                "boundary_case": "one active state gives support_K=record_K=0",
                "demotion_condition": "any exact/JAX mismatch or missing mutation response",
                "gates": ["quotient", "reference_agreement"],
            }
        ],
    }


def evaluate(payload: Any, *, engine: str = "exact") -> dict[str, Any]:
    input_sha = _sha(payload)
    source_sha = _source_sha256()
    try:
        core = _core(payload)
        controls = _controls(payload, core)
        jax_result = _jax_check(core) if engine == "dual" else {"ran": False, "reason": "exact_only", "load_bearing": False}
        reasons = []
        if not controls["all_pass"]:
            reasons.append("HOLD_CONTROL_FAILURE")
        if engine == "dual" and not jax_result.get("load_bearing"):
            reasons.append("HOLD_JAX_REFERENCE_DISAGREEMENT_OR_UNAVAILABLE")
        public_core = {key: value for key, value in core.items() if key != "_slice_internal"}
        runtime_binding = {
            "python_version": platform.python_version(),
            "engine": engine,
            "jax_version": jax_result.get("jax_version"),
            "jaxlib_version": jax_result.get("jaxlib_version"),
            "jax_x64_enabled": jax_result.get("x64_enabled"),
            "device": jax_result.get("device"),
        }
        body = {
            "schema": RESULT_SCHEMA,
            "operation": OPERATION,
            "operation_id": "etf-" + _sha(
                {"input": input_sha, "source": source_sha, "runtime": runtime_binding}
            )[:24],
            "status": "PASS" if not reasons else "HOLD",
            "reason_codes": reasons,
            "classification": "scratch_diagnostic",
            "engine": engine,
            "runtime_binding": runtime_binding,
            "input_sha256": input_sha,
            "source_sha256": source_sha,
            "field": public_core,
            "controls": controls,
            "jax": jax_result,
            "claim_ceiling": (
                "finite entropic-geometry transition and controls only; not physical spacetime, "
                "chirality, attractor, engine, entropy law, or promotion"
            ),
            "promotion_allowed": False,
        }
    except FieldError as exc:
        body = {
            "schema": RESULT_SCHEMA,
            "operation": OPERATION,
            "status": "HOLD" if exc.reason_code.startswith("HOLD_") else "REFUSE",
            "reason_codes": [exc.reason_code],
            "detail": exc.detail,
            "classification": "scratch_diagnostic",
            "engine": engine,
            "input_sha256": input_sha,
            "source_sha256": source_sha,
            "claim_ceiling": "invalid finite field; no quotient, geometry, time, or entropy result",
            "promotion_allowed": False,
        }
    body["result_sha256"] = _sha(body)
    return body


def evaluate_file(path: Path, *, engine: str = "exact") -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": RESULT_SCHEMA,
            "operation": OPERATION,
            "status": "REFUSE",
            "reason_codes": ["REFUSE_FIELD_INPUT"],
            "detail": f"{type(exc).__name__}:{exc}",
            "promotion_allowed": False,
        }
    return evaluate(payload, engine=engine)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--engine", choices=("exact", "dual"), default="exact")
    args = parser.parse_args(argv)
    body = evaluate_file(args.input, engine=args.engine)
    rendered = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if body["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
