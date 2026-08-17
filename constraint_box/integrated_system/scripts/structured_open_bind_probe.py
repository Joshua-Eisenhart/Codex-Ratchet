#!/usr/bin/env python3
"""Probe a finite structured open/bind family against generic controls."""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any


INPUT_SCHEMA = "constraintbox.structured-open-bind-fixture.v1"
RESULT_SCHEMA = "constraintbox.structured-open-bind-result.v1"


class ProbeError(ValueError):
    def __init__(self, reason_code: str, detail: str = "") -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ProbeError("REFUSE_FIXTURE_SCHEMA", label)
    return value


def validate_fixture(raw: Any) -> dict[str, Any]:
    root = exact_keys(
        raw,
        {
            "schema",
            "fixture_id",
            "states",
            "parent_by_state",
            "probes",
            "observations",
            "bind_candidates",
            "relabel_permutation",
            "claim_ceiling",
            "promotion_allowed",
        },
        "$",
    )
    if root["schema"] != INPUT_SCHEMA or root["promotion_allowed"] is not False:
        raise ProbeError("REFUSE_FIXTURE_SCHEMA", "envelope")
    states = root["states"]
    probes = root["probes"]
    if (
        not isinstance(states, list)
        or len(states) < 2
        or len(states) > 8
        or len(set(states)) != len(states)
        or any(not isinstance(item, str) or not item for item in states)
    ):
        raise ProbeError("REFUSE_FIXTURE_SCHEMA", "states")
    if (
        not isinstance(probes, list)
        or not probes
        or len(set(probes)) != len(probes)
        or any(not isinstance(item, str) or not item for item in probes)
    ):
        raise ProbeError("REFUSE_FIXTURE_SCHEMA", "probes")
    parents = root["parent_by_state"]
    if not isinstance(parents, dict) or set(parents) != set(states):
        raise ProbeError("REFUSE_FIXTURE_SCHEMA", "parent_by_state")
    if any(not isinstance(parent, str) or not parent for parent in parents.values()):
        raise ProbeError("REFUSE_FIXTURE_SCHEMA", "parent values")
    rows: dict[tuple[str, str], str] = {}
    observations = root["observations"]
    if not isinstance(observations, list):
        raise ProbeError("REFUSE_FIXTURE_SCHEMA", "observations")
    for item in observations:
        row = exact_keys(item, {"state", "probe", "value"}, "observation")
        key = (row["state"], row["probe"])
        if (
            row["state"] not in states
            or row["probe"] not in probes
            or not isinstance(row["value"], str)
            or key in rows
        ):
            raise ProbeError("REFUSE_FIXTURE_SCHEMA", "observation row")
        rows[key] = row["value"]
    missing = [f"{state}/{probe}" for state in states for probe in probes if (state, probe) not in rows]
    if missing:
        raise ProbeError("REFUSE_UNBOUND_OBSERVATION", ",".join(missing))
    candidates = root["bind_candidates"]
    if not isinstance(candidates, list) or not candidates:
        raise ProbeError("REFUSE_FIXTURE_SCHEMA", "bind_candidates")
    normalized = []
    seen_ids: set[str] = set()
    for item in candidates:
        if not isinstance(item, dict) or set(item) not in (
            {"id", "probe", "allowed_values"},
            {"id", "probe", "allowed_values", "control"},
        ):
            raise ProbeError("REFUSE_FIXTURE_SCHEMA", "bind candidate")
        if item["id"] in seen_ids or item["probe"] not in probes:
            raise ProbeError("REFUSE_FIXTURE_SCHEMA", "bind candidate identity")
        allowed = item["allowed_values"]
        if not isinstance(allowed, list) or not allowed or len(set(allowed)) != len(allowed):
            raise ProbeError("REFUSE_FIXTURE_SCHEMA", "allowed_values")
        seen_ids.add(item["id"])
        normalized.append({**item, "allowed_values": sorted(str(value) for value in allowed)})
    permutation = root["relabel_permutation"]
    if not isinstance(permutation, list) or sorted(permutation) != list(range(len(states))):
        raise ProbeError("REFUSE_FIXTURE_SCHEMA", "relabel_permutation")
    return {
        **root,
        "states": list(states),
        "probes": list(probes),
        "rows": rows,
        "bind_candidates": normalized,
    }


def open_table(states: list[str], parents: dict[str, str]) -> list[int]:
    fibres: dict[str, int] = {}
    for index, state in enumerate(states):
        fibres[parents[state]] = fibres.get(parents[state], 0) | (1 << index)
    table = []
    for subset in range(1 << len(states)):
        opened = 0
        for index, state in enumerate(states):
            if subset & (1 << index):
                opened |= fibres[parents[state]]
        table.append(opened)
    return table


def candidate_masks(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    states = fixture["states"]
    rows = fixture["rows"]
    out = []
    for candidate in fixture["bind_candidates"]:
        allowed = set(candidate["allowed_values"])
        mask = 0
        for index, state in enumerate(states):
            if rows[(state, candidate["probe"])] in allowed:
                mask |= 1 << index
        out.append({**candidate, "mask": mask})
    return out


def gap_count(table: list[int], bind_mask: int) -> int:
    return sum(
        1
        for subset in range(len(table))
        if (table[subset] & bind_mask) != table[subset & bind_mask]
    )


def structured_metrics(fixture: dict[str, Any]) -> dict[str, Any]:
    table = open_table(fixture["states"], fixture["parent_by_state"])
    total_subsets = len(table)
    rows = []
    for candidate in candidate_masks(fixture):
        gaps = gap_count(table, candidate["mask"])
        rows.append(
            {
                "id": candidate["id"],
                "probe": candidate["probe"],
                "allowed_values": candidate["allowed_values"],
                "control": candidate.get("control"),
                "bind_mask": candidate["mask"],
                "gap_count": gaps,
                "commuting_count": total_subsets - gaps,
                "gap_rate": gaps / total_subsets,
            }
        )
    noncontrol = [row for row in rows if row["control"] is None]
    random_rows = [gap_count(table, mask) for mask in range(1 << len(fixture["states"]))]
    structured_cases = total_subsets * len(noncontrol)
    structured_gaps = sum(row["gap_count"] for row in noncontrol)
    return {
        "open_table": table,
        "rows": rows,
        "subset_count": total_subsets,
        "structured_noncontrol_gap_count": structured_gaps,
        "structured_noncontrol_case_count": structured_cases,
        "structured_noncontrol_gap_rate": structured_gaps / structured_cases if structured_cases else 0.0,
        "random_mask_gap_count": sum(random_rows),
        "random_mask_case_count": total_subsets * len(random_rows),
        "random_mask_gap_rate": sum(random_rows) / (total_subsets * len(random_rows)),
        "identity_gap_zero": any(
            row["control"] == "identity" and row["gap_count"] == 0 for row in rows
        ),
        "has_gap_case": any(row["gap_count"] > 0 for row in noncontrol),
        "has_commuting_case": any(row["gap_count"] == 0 for row in noncontrol),
    }


def generic_endomap_control(size: int) -> dict[str, Any]:
    maps = list(itertools.product(range(size), repeat=size))
    commuting = 0
    for left in maps:
        for right in maps:
            if all(left[right[index]] == right[left[index]] for index in range(size)):
                commuting += 1
    total = len(maps) * len(maps)
    return {
        "carrier_size": size,
        "map_count": len(maps),
        "pair_count": total,
        "commuting_pairs": commuting,
        "noncommuting_pairs": total - commuting,
        "noncommuting_rate": (total - commuting) / total,
        "comparison_note": "reference only; arbitrary endomap pairs are not the structured subset-mask family",
    }


def solver_mask_checks(fixture: dict[str, Any], masks: list[dict[str, Any]]) -> dict[str, Any]:
    import cvc5
    import z3

    states = fixture["states"]
    z3_ok = True
    cvc5_ok = True
    for candidate in masks:
        expected = [bool(candidate["mask"] & (1 << index)) for index in range(len(states))]
        zvars = [z3.Bool(f"{candidate['id']}_{index}") for index in range(len(states))]
        zsolver = z3.Solver()
        for var, value in zip(zvars, expected):
            zsolver.add(var == z3.BoolVal(value))
        if zsolver.check() != z3.sat:
            z3_ok = False
        else:
            model = zsolver.model()
            z3_ok = z3_ok and all(z3.is_true(model.eval(var)) == value for var, value in zip(zvars, expected))

        solver = cvc5.Solver()
        solver.setLogic("QF_UF")
        solver.setOption("produce-models", "true")
        bool_sort = solver.getBooleanSort()
        cvars = [solver.mkConst(bool_sort, f"{candidate['id']}_{index}") for index in range(len(states))]
        for var, value in zip(cvars, expected):
            solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, var, solver.mkBoolean(value)))
        if not solver.checkSat().isSat():
            cvc5_ok = False
        else:
            cvc5_ok = cvc5_ok and all(solver.getValue(var).getBooleanValue() == value for var, value in zip(cvars, expected))
    return {
        "z3": "PASS" if z3_ok else "REFUSE",
        "cvc5": "PASS" if cvc5_ok else "REFUSE",
        "agree": z3_ok and cvc5_ok,
        "mask_set_sha256": sha256_bytes(canonical_json_bytes(masks)),
    }


def jax_check(metrics: dict[str, Any], masks: list[dict[str, Any]]) -> dict[str, Any]:
    import jax

    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp

    table = jnp.asarray(metrics["open_table"], dtype=jnp.int64)
    subsets = jnp.arange(len(metrics["open_table"]), dtype=jnp.int64)
    bind_masks = jnp.asarray([row["mask"] for row in masks], dtype=jnp.int64)

    @jax.jit
    def one(mask):
        left = jnp.bitwise_and(table, mask)
        right = table[jnp.bitwise_and(subsets, mask)]
        return jnp.sum(left != right)

    counts = [int(value) for value in jax.vmap(one)(bind_masks)]
    expected = [row["gap_count"] for row in metrics["rows"]]
    return {
        "ran": True,
        "jax_version": jax.__version__,
        "jaxlib_version": __import__("jaxlib").__version__,
        "device": str(jax.devices()[0]),
        "gap_counts": counts,
        "exact_agreement": counts == expected,
        "output_sha256": sha256_bytes(canonical_json_bytes(counts)),
    }


def relabel_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    states = fixture["states"]
    permutation = fixture["relabel_permutation"]
    renamed = {state: f"r{permutation[index]}" for index, state in enumerate(states)}
    relabeled = copy.deepcopy(fixture)
    relabeled["states"] = [renamed[state] for state in states]
    relabeled["parent_by_state"] = {
        renamed[state]: f"p:{fixture['parent_by_state'][state]}" for state in states
    }
    relabeled["rows"] = {
        (renamed[state], probe): value for (state, probe), value in fixture["rows"].items()
    }
    return relabeled


def evaluate(raw: Any, engine: str = "exact") -> dict[str, Any]:
    try:
        fixture = validate_fixture(raw)
        metrics = structured_metrics(fixture)
        masks = candidate_masks(fixture)
        solver = solver_mask_checks(fixture, masks)
        relabeled_metrics = structured_metrics(relabel_fixture(fixture))
        relabel_invariant = (
            metrics["structured_noncontrol_gap_count"]
            == relabeled_metrics["structured_noncontrol_gap_count"]
            and metrics["random_mask_gap_count"] == relabeled_metrics["random_mask_gap_count"]
        )
        missing = copy.deepcopy(raw)
        missing["observations"] = missing["observations"][:-1]
        missing_refused = False
        try:
            validate_fixture(missing)
        except ProbeError as exc:
            missing_refused = exc.reason_code == "REFUSE_UNBOUND_OBSERVATION"
        generic = generic_endomap_control(len(fixture["states"]))
        jax = {"ran": False, "reason": "exact engine"}
        if engine == "dual":
            jax = jax_check(metrics, masks)
        controls = {
            "solver_masks_bound": solver["agree"],
            "relabel_invariant": relabel_invariant,
            "missing_observation_refused": missing_refused,
            "identity_bind_commutes": metrics["identity_gap_zero"],
            "structured_has_gap_case": metrics["has_gap_case"],
            "structured_has_commuting_case": metrics["has_commuting_case"],
            "structured_less_generic_than_random_masks": (
                metrics["structured_noncontrol_gap_rate"] < metrics["random_mask_gap_rate"]
            ),
            "jax_agrees_if_requested": engine == "exact" or bool(jax.get("exact_agreement")),
        }
        controls["all_pass"] = all(controls.values())
        finding = (
            "STRUCTURED_FAMILY_DIFFERS_FROM_RANDOM_MASKS"
            if controls["structured_less_generic_than_random_masks"]
            else "HOLD_STRUCTURED_SCAR_STILL_GENERIC"
        )
        status = "PASS" if controls["all_pass"] else "HOLD"
        body = {
            "schema": RESULT_SCHEMA,
            "status": status,
            "finding": finding,
            "engine": engine,
            "fixture_id": fixture["fixture_id"],
            "fixture_sha256": sha256_bytes(canonical_json_bytes(raw)),
            "source_sha256": sha256_bytes(Path(__file__).read_bytes()),
            "structured": {key: value for key, value in metrics.items() if key != "open_table"},
            "generic_endomap_control": generic,
            "solver": solver,
            "jax": jax,
            "controls": controls,
            "forbidden_inferences": [
                "order gap is chirality",
                "order gap is the odd gradient",
                "static quotient component is an attractor",
                "structured family result is manifold admission",
            ],
            "next_operation": "jax_vmap_named_bind_masks_only_if_more_width_is_needed",
            "claim_ceiling": fixture["claim_ceiling"],
            "promotion_allowed": False,
        }
        body["result_sha256"] = sha256_bytes(canonical_json_bytes(body))
        return body
    except (ProbeError, ImportError, ModuleNotFoundError) as exc:
        return {
            "schema": RESULT_SCHEMA,
            "status": "REFUSE" if isinstance(exc, ProbeError) else "HOLD",
            "reason_code": exc.reason_code if isinstance(exc, ProbeError) else "HOLD_DEPENDENCY_MISSING",
            "detail": getattr(exc, "detail", str(exc)),
            "engine": engine,
            "promotion_allowed": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--engine", choices=("exact", "dual"), default="exact")
    args = parser.parse_args()
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        body = {
            "schema": RESULT_SCHEMA,
            "status": "REFUSE",
            "reason_code": "REFUSE_FIXTURE_INPUT",
            "detail": f"{type(exc).__name__}:{exc}",
            "promotion_allowed": False,
        }
    else:
        body = evaluate(raw, engine=args.engine)
    rendered = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if body.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
