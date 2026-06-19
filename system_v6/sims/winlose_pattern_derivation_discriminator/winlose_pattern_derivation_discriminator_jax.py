#!/usr/bin/env python3
"""JAX/SMT leg for the Win/Lose pattern derivation discriminator."""

from __future__ import annotations

import datetime as _dt
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "winlose_pattern_derivation_discriminator"
OBJECT_ID = f"{SIM_ID}_jax"
SOURCE_PATH = ROOT / "system_v6" / "sims" / SIM_ID / f"{SIM_ID}_jax.py"
RESULT_PATH = ROOT / "system_v6" / "sims" / SIM_ID / "results" / f"{SIM_ID}_jax_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

LOOP_SIGN = {"outer": -1, "inner": 1}
AXIS6_SIGN = {"UP": -1, "DOWN": 1}
B0_SIGN_BY_TOPOLOGY = {"Ne": 1, "Ni": 1, "Se": -1, "Si": -1}
VALUE_BY_LOOP_BIT = {
    ("outer", 1): "WIN",
    ("outer", 0): "LOSE",
    ("inner", 1): "win",
    ("inner", 0): "lose",
}
BIT_BY_VALUE = {"WIN": 1, "LOSE": 0, "win": 1, "lose": 0}

SLOTS: list[dict[str, str]] = [
    {"engine": "Type-1", "topology": "Se", "loop": "outer", "order": "Deductive", "token": "TiSe", "op": "Ti", "axis6": "UP", "target": "LOSE", "source_row": "Topology.png Type-1 row 1 outer"},
    {"engine": "Type-1", "topology": "Ne", "loop": "outer", "order": "Deductive", "token": "NeTi", "op": "Ti", "axis6": "DOWN", "target": "WIN", "source_row": "Topology.png Type-1 row 2 outer"},
    {"engine": "Type-1", "topology": "Ni", "loop": "outer", "order": "Deductive", "token": "NiFe", "op": "Fe", "axis6": "DOWN", "target": "LOSE", "source_row": "Topology.png Type-1 row 3 outer"},
    {"engine": "Type-1", "topology": "Si", "loop": "outer", "order": "Deductive", "token": "FeSi", "op": "Fe", "axis6": "UP", "target": "WIN", "source_row": "Topology.png Type-1 row 4 outer"},
    {"engine": "Type-1", "topology": "Se", "loop": "inner", "order": "Inductive", "token": "SeFi", "op": "Fi", "axis6": "DOWN", "target": "win", "source_row": "Topology.png Type-1 row 1 inner"},
    {"engine": "Type-1", "topology": "Si", "loop": "inner", "order": "Inductive", "token": "SiTe", "op": "Te", "axis6": "DOWN", "target": "win", "source_row": "Topology.png Type-1 row 2 inner"},
    {"engine": "Type-1", "topology": "Ni", "loop": "inner", "order": "Inductive", "token": "TeNi", "op": "Te", "axis6": "UP", "target": "lose", "source_row": "Topology.png Type-1 row 3 inner"},
    {"engine": "Type-1", "topology": "Ne", "loop": "inner", "order": "Inductive", "token": "FiNe", "op": "Fi", "axis6": "UP", "target": "lose", "source_row": "Topology.png Type-1 row 4 inner"},
    {"engine": "Type-2", "topology": "Se", "loop": "outer", "order": "Inductive", "token": "FiSe", "op": "Fi", "axis6": "UP", "target": "WIN", "source_row": "Topology.png Type-2 row 1 outer"},
    {"engine": "Type-2", "topology": "Si", "loop": "outer", "order": "Inductive", "token": "TeSi", "op": "Te", "axis6": "UP", "target": "WIN", "source_row": "Topology.png Type-2 row 2 outer"},
    {"engine": "Type-2", "topology": "Ni", "loop": "outer", "order": "Inductive", "token": "NiTe", "op": "Te", "axis6": "DOWN", "target": "LOSE", "source_row": "Topology.png Type-2 row 3 outer"},
    {"engine": "Type-2", "topology": "Ne", "loop": "outer", "order": "Inductive", "token": "NeFi", "op": "Fi", "axis6": "DOWN", "target": "LOSE", "source_row": "Topology.png Type-2 row 4 outer"},
    {"engine": "Type-2", "topology": "Se", "loop": "inner", "order": "Deductive", "token": "SeTi", "op": "Ti", "axis6": "DOWN", "target": "lose", "source_row": "Topology.png Type-2 row 1 inner"},
    {"engine": "Type-2", "topology": "Ne", "loop": "inner", "order": "Deductive", "token": "TiNe", "op": "Ti", "axis6": "UP", "target": "win", "source_row": "Topology.png Type-2 row 2 inner"},
    {"engine": "Type-2", "topology": "Ni", "loop": "inner", "order": "Deductive", "token": "FeNi", "op": "Fe", "axis6": "UP", "target": "lose", "source_row": "Topology.png Type-2 row 3 inner"},
    {"engine": "Type-2", "topology": "Si", "loop": "inner", "order": "Deductive", "token": "SiFe", "op": "Fe", "axis6": "DOWN", "target": "win", "source_row": "Topology.png Type-2 row 4 inner"},
]

SLOT_COUNT = len(SLOTS)
TARGET_BITS = [BIT_BY_VALUE[row["target"]] for row in SLOTS]
TARGET_MAP = {(row["engine"], row["topology"], row["loop"]): idx for idx, row in enumerate(SLOTS)}
CANDIDATE_EXTRA_FEATURES = ("engine", "topology", "order", "op", "token")

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive exhaustive vectorized count over the 2^16 finite assignment space; substrate demoted under capability-probe doctrine",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive boolean tensor masks for exact finite model counts; no numpy bridge on claim path; substrate demoted under capability-probe doctrine",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SAT and model-count sidecar with blocking clauses over the same 16 assignment bits",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SAT and model-count sidecar with blocking clauses over the same constraints",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic table, hashing, paths, and JSON receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def axis6_relation_holds(row: dict[str, str]) -> bool:
    return AXIS6_SIGN[row["axis6"]] == -B0_SIGN_BY_TOPOLOGY[row["topology"]] * LOOP_SIGN[row["loop"]]


def axis6_scaffold_ok() -> bool:
    return all(axis6_relation_holds(row) for row in SLOTS)


def chart_scaffold_consistency_ok() -> bool:
    return axis6_scaffold_ok()


def sign_triple(row: dict[str, str]) -> tuple[int, int, int]:
    return (B0_SIGN_BY_TOPOLOGY[row["topology"]], LOOP_SIGN[row["loop"]], AXIS6_SIGN[row["axis6"]])


def sign_triple_key(triple: tuple[int, int, int]) -> str:
    b0, b3, b6 = triple
    return f"b0={b0},b3={b3},b6={b6}"


def outcome_bits(row: dict[str, str], bit: int) -> tuple[int, int]:
    return (1 if row["loop"] == "inner" else 0, int(bit))


def outcome_label(row: dict[str, str], bit: int) -> str:
    return bit_to_value(row, bit)


def bit_to_value(row: dict[str, str], bit: int) -> str:
    return VALUE_BY_LOOP_BIT[(row["loop"], int(bit))]


def documented_table() -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(SLOTS):
        bit = TARGET_BITS[idx]
        rows.append(
            {
                "slot": idx,
                **row,
                "target_bit": bit,
                "b0": B0_SIGN_BY_TOPOLOGY[row["topology"]],
                "b3": LOOP_SIGN[row["loop"]],
                "b6": AXIS6_SIGN[row["axis6"]],
                "relation_b6_equals_minus_b0_b3": axis6_relation_holds(row),
            }
        )
    return rows


def sign_outcome_class_table(bits: list[int] = TARGET_BITS) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, int, int], list[int]] = {}
    for idx, row in enumerate(SLOTS):
        grouped.setdefault(sign_triple(row), []).append(idx)
    table: list[dict[str, Any]] = []
    for triple in sorted(grouped):
        idxs = grouped[triple]
        observed = sorted({outcome_bits(SLOTS[idx], bits[idx]) for idx in idxs})
        labels = sorted({outcome_label(SLOTS[idx], bits[idx]) for idx in idxs})
        table.append(
            {
                "sign_triple": {"b0": triple[0], "b3": triple[1], "b6": triple[2]},
                "sign_triple_key": sign_triple_key(triple),
                "row_count": len(idxs),
                "constant": len(observed) == 1,
                "outcome_bits_observed": [list(item) for item in observed],
                "outcome_labels_observed": labels,
                "rows": [
                    {
                        "slot": idx,
                        "engine": SLOTS[idx]["engine"],
                        "topology": SLOTS[idx]["topology"],
                        "order": SLOTS[idx]["order"],
                        "op": SLOTS[idx]["op"],
                        "token": SLOTS[idx]["token"],
                        "outcome_bits": list(outcome_bits(SLOTS[idx], bits[idx])),
                        "outcome_label": outcome_label(SLOTS[idx], bits[idx]),
                    }
                    for idx in idxs
                ],
            }
        )
    return table


def feature_domain_product(features: tuple[str, ...]) -> int:
    product = 1
    for feature in features:
        product *= len({row[feature] for row in SLOTS})
    return product


def is_functional_with_features(features: tuple[str, ...], bits: list[int] = TARGET_BITS) -> bool:
    seen: dict[tuple[Any, ...], tuple[int, int]] = {}
    for idx, row in enumerate(SLOTS):
        key = (*sign_triple(row), *(row[feature] for feature in features))
        value = outcome_bits(row, bits[idx])
        if key in seen and seen[key] != value:
            return False
        seen[key] = value
    return True


def sign_outcome_analysis(bits: list[int] = TARGET_BITS) -> dict[str, Any]:
    class_table = sign_outcome_class_table(bits)
    signs_only_constant = all(row["constant"] for row in class_table)
    functional_sets: list[dict[str, Any]] = []
    for size in range(0, len(CANDIDATE_EXTRA_FEATURES) + 1):
        for features in itertools.combinations(CANDIDATE_EXTRA_FEATURES, size):
            if is_functional_with_features(features, bits):
                functional_sets.append(
                    {
                        "features": list(features),
                        "feature_count": size,
                        "domain_product": feature_domain_product(features),
                    }
                )
        if functional_sets:
            break
    functional_sets.sort(key=lambda item: (item["feature_count"], item["domain_product"], item["features"]))
    selected = functional_sets[0]["features"] if functional_sets else []
    return {
        "question": "Is the documented two-bit outcome a function of sign triple (b0,b3,b6), and if not what smallest row datum makes it functional?",
        "outcome_bits_convention": "two-bit outcome is [case_bit, win_bit], case_bit 0=outer uppercase WIN/LOSE and 1=inner lowercase win/lose; win_bit 1=WIN/win and 0=LOSE/lose",
        "class_table": class_table,
        "signs_only_functional": signs_only_constant,
        "answer": "a_sign_determined" if signs_only_constant else "b_requires_extra_row_datum",
        "split_classes": [row for row in class_table if not row["constant"]],
        "minimal_functional_feature_sets": functional_sets,
        "selected_minimal_extra_input": selected,
        "selected_reason": "smallest feature count, then smallest observed feature-domain product",
        "truth_table": [] if not signs_only_constant else [
            {
                "sign_triple": row["sign_triple"],
                "outcome_bits": row["outcome_bits_observed"][0],
                "outcome_labels": row["outcome_labels_observed"],
            }
            for row in class_table
        ],
    }


def expected_bits_for_coupling(features: tuple[str, ...], bits: list[int] = TARGET_BITS) -> list[int]:
    mapping: dict[tuple[Any, ...], int] = {}
    for idx, row in enumerate(SLOTS):
        key = (*sign_triple(row), *(row[feature] for feature in features))
        bit = int(bits[idx])
        if key in mapping and mapping[key] != bit:
            raise ValueError(f"non-functional coupling for features={features}: {key}")
        mapping[key] = bit
    return [mapping[(*sign_triple(row), *(row[feature] for feature in features))] for row in SLOTS]


def coupling_ok(bits: list[int], features: tuple[str, ...]) -> bool:
    expected = expected_bits_for_coupling(features)
    return all(int(bit) == expected[idx] for idx, bit in enumerate(bits))


def balance_ok(bits: list[int]) -> bool:
    for engine in ("Type-1", "Type-2"):
        outer = [bits[i] for i, row in enumerate(SLOTS) if row["engine"] == engine and row["loop"] == "outer"]
        inner = [bits[i] for i, row in enumerate(SLOTS) if row["engine"] == engine and row["loop"] == "inner"]
        if sum(outer) != 2 or sum(inner) != 2:
            return False
    return True


def duality_ok(bits: list[int]) -> bool:
    for topology in ("Se", "Ne", "Ni", "Si"):
        if bits[TARGET_MAP[("Type-2", topology, "outer")]] != bits[TARGET_MAP[("Type-1", topology, "inner")]]:
            return False
        if bits[TARGET_MAP[("Type-2", topology, "inner")]] != bits[TARGET_MAP[("Type-1", topology, "outer")]]:
            return False
    return True


def operator_balance_ok() -> bool:
    for engine in ("Type-1", "Type-2"):
        for op in ("Ti", "Te", "Fi", "Fe"):
            rows = [row for row in SLOTS if row["engine"] == engine and row["op"] == op]
            if sorted(row["axis6"] for row in rows) != ["DOWN", "UP"]:
                return False
    return True


def constraints_ok(
    bits: list[int],
    *,
    use_chart_scaffold: bool = True,
    use_balance: bool = True,
    use_duality: bool = True,
    coupling_features: tuple[str, ...] | None = None,
) -> bool:
    return (
        (not use_chart_scaffold or chart_scaffold_consistency_ok())
        and (not use_balance or balance_ok(bits))
        and (not use_duality or duality_ok(bits))
        and (coupling_features is None or coupling_ok(bits, coupling_features))
        and operator_balance_ok()
    )


def assignment_from_int(mask: int) -> list[int]:
    return [(mask >> idx) & 1 for idx in range(SLOT_COUNT)]


def jax_count(
    *,
    use_chart_scaffold: bool = True,
    use_balance: bool = True,
    use_duality: bool = True,
    coupling_features: tuple[str, ...] | None = None,
) -> int:
    masks = jnp.arange(1 << SLOT_COUNT, dtype=jnp.uint32)
    shifts = jnp.arange(SLOT_COUNT, dtype=jnp.uint32)
    bits = ((masks[:, None] >> shifts[None, :]) & jnp.uint32(1)).astype(jnp.int32)
    ok = jnp.ones((1 << SLOT_COUNT,), dtype=bool)
    if use_chart_scaffold:
        ok = ok & bool(chart_scaffold_consistency_ok())
    if use_balance:
        for engine in ("Type-1", "Type-2"):
            for loop in ("outer", "inner"):
                idxs = jnp.array([i for i, row in enumerate(SLOTS) if row["engine"] == engine and row["loop"] == loop], dtype=jnp.int32)
                ok = ok & (jnp.sum(bits[:, idxs], axis=1) == 2)
    if use_duality:
        for topology in ("Se", "Ne", "Ni", "Si"):
            ok = ok & (bits[:, TARGET_MAP[("Type-2", topology, "outer")]] == bits[:, TARGET_MAP[("Type-1", topology, "inner")]])
            ok = ok & (bits[:, TARGET_MAP[("Type-2", topology, "inner")]] == bits[:, TARGET_MAP[("Type-1", topology, "outer")]])
    if coupling_features is not None:
        expected = jnp.array(expected_bits_for_coupling(coupling_features), dtype=jnp.int32)
        ok = ok & jnp.all(bits == expected[None, :], axis=1)
    return int(jax.device_get(jnp.sum(ok.astype(jnp.int32))))


def brute_force_models(
    *,
    use_chart_scaffold: bool = True,
    use_balance: bool = True,
    use_duality: bool = True,
    coupling_features: tuple[str, ...] | None = None,
) -> list[list[int]]:
    models = []
    for mask in range(1 << SLOT_COUNT):
        bits = assignment_from_int(mask)
        if constraints_ok(
            bits,
            use_chart_scaffold=use_chart_scaffold,
            use_balance=use_balance,
            use_duality=use_duality,
            coupling_features=coupling_features,
        ):
            models.append(bits)
    return models


def constraint_violations(bits: list[int]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for idx, row in enumerate(SLOTS):
        if not axis6_relation_holds(row):
            violations.append(
                {
                    "constraint": "b6=-b0*b3",
                    "slot": idx,
                    "engine": row["engine"],
                    "topology": row["topology"],
                    "loop": row["loop"],
                    "axis6": row["axis6"],
                    "assigned_value": bit_to_value(row, bits[idx]),
                    "required_b6": -B0_SIGN_BY_TOPOLOGY[row["topology"]] * LOOP_SIGN[row["loop"]],
                    "source_row": row["source_row"],
                }
            )
    if not balance_ok(bits):
        violations.append({"constraint": "per_engine_balance", "detail": balance_report(bits)})
    if not duality_ok(bits):
        violations.append({"constraint": "case_inversion_duality", "detail": duality_report(bits)})
    return violations


def balance_report(bits: list[int]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for engine in ("Type-1", "Type-2"):
        outer = [bit_to_value(SLOTS[i], bits[i]) for i, row in enumerate(SLOTS) if row["engine"] == engine and row["loop"] == "outer"]
        inner = [bit_to_value(SLOTS[i], bits[i]) for i, row in enumerate(SLOTS) if row["engine"] == engine and row["loop"] == "inner"]
        report[engine] = {
            "WIN": outer.count("WIN"),
            "LOSE": outer.count("LOSE"),
            "win": inner.count("win"),
            "lose": inner.count("lose"),
        }
    return report


def duality_report(bits: list[int]) -> list[dict[str, Any]]:
    rows = []
    for topology in ("Se", "Ne", "Ni", "Si"):
        rows.append(
            {
                "topology": topology,
                "type1_outer": bit_to_value(SLOTS[TARGET_MAP[("Type-1", topology, "outer")]], bits[TARGET_MAP[("Type-1", topology, "outer")]]),
                "type1_inner": bit_to_value(SLOTS[TARGET_MAP[("Type-1", topology, "inner")]], bits[TARGET_MAP[("Type-1", topology, "inner")]]),
                "type2_outer": bit_to_value(SLOTS[TARGET_MAP[("Type-2", topology, "outer")]], bits[TARGET_MAP[("Type-2", topology, "outer")]]),
                "type2_inner": bit_to_value(SLOTS[TARGET_MAP[("Type-2", topology, "inner")]], bits[TARGET_MAP[("Type-2", topology, "inner")]]),
            }
        )
    return rows


def z3_constraints(
    vars_: list[Any],
    *,
    use_chart_scaffold: bool = True,
    use_balance: bool = True,
    use_duality: bool = True,
    coupling_features: tuple[str, ...] | None = None,
) -> list[Any]:
    constraints: list[Any] = []
    if use_chart_scaffold:
        if not chart_scaffold_consistency_ok():
            constraints.append(z3.BoolVal(False))
    if use_balance:
        for engine in ("Type-1", "Type-2"):
            for loop in ("outer", "inner"):
                idxs = [i for i, row in enumerate(SLOTS) if row["engine"] == engine and row["loop"] == loop]
                constraints.append(z3.Sum([z3.If(vars_[i], 1, 0) for i in idxs]) == 2)
    if use_duality:
        for topology in ("Se", "Ne", "Ni", "Si"):
            constraints.append(vars_[TARGET_MAP[("Type-2", topology, "outer")]] == vars_[TARGET_MAP[("Type-1", topology, "inner")]])
            constraints.append(vars_[TARGET_MAP[("Type-2", topology, "inner")]] == vars_[TARGET_MAP[("Type-1", topology, "outer")]])
    if coupling_features is not None:
        expected = expected_bits_for_coupling(coupling_features)
        constraints.extend(var == bool(bit) for var, bit in zip(vars_, expected, strict=True))
    return constraints


def z3_count(
    *,
    use_chart_scaffold: bool = True,
    use_balance: bool = True,
    use_duality: bool = True,
    coupling_features: tuple[str, ...] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    vars_ = [z3.Bool(f"v_{idx}") for idx in range(SLOT_COUNT)]
    solver = z3.Solver()
    solver.add(
        *z3_constraints(
            vars_,
            use_chart_scaffold=use_chart_scaffold,
            use_balance=use_balance,
            use_duality=use_duality,
            coupling_features=coupling_features,
        )
    )
    count = 0
    first_model = None
    while solver.check() == z3.sat:
        model = solver.model()
        values = [bool(z3.is_true(model.eval(var, model_completion=True))) for var in vars_]
        if first_model is None:
            first_model = values
        solver.add(z3.Or([var != value for var, value in zip(vars_, values, strict=True)]))
        count += 1
        if limit is not None and count >= limit:
            break
    return {
        "solver": "z3",
        "status_after_blocking": str(solver.check()),
        "model_count": count,
        "count_complete": limit is None or count < limit,
        "first_model_equals_documented": first_model == [bool(bit) for bit in TARGET_BITS],
    }


def z3_sat_for(
    bits: list[int],
    *,
    use_chart_scaffold: bool = True,
    use_balance: bool = True,
    use_duality: bool = True,
    coupling_features: tuple[str, ...] | None = None,
) -> str:
    vars_ = [z3.Bool(f"sat_v_{idx}") for idx in range(SLOT_COUNT)]
    solver = z3.Solver()
    solver.add(
        *z3_constraints(
            vars_,
            use_chart_scaffold=use_chart_scaffold,
            use_balance=use_balance,
            use_duality=use_duality,
            coupling_features=coupling_features,
        )
    )
    solver.add(*[var == bool(bit) for var, bit in zip(vars_, bits, strict=True)])
    return str(solver.check())


def cvc5_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(True)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.AND, *terms)


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(False)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.OR, *terms)


def cvc5_not(solver: cvc5.Solver, term: Any) -> Any:
    return solver.mkTerm(Kind.NOT, term)


def cvc5_iff(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.EQUAL, left, right)


def cvc5_exactly_two(solver: cvc5.Solver, vars_: list[Any]) -> Any:
    choices = []
    for hot in itertools.combinations(range(len(vars_)), 2):
        terms = [vars_[idx] if idx in hot else cvc5_not(solver, vars_[idx]) for idx in range(len(vars_))]
        choices.append(cvc5_and(solver, terms))
    return cvc5_or(solver, choices)


def cvc5_add_constraints(
    solver: cvc5.Solver,
    vars_: list[Any],
    *,
    use_chart_scaffold: bool = True,
    use_balance: bool = True,
    use_duality: bool = True,
    coupling_features: tuple[str, ...] | None = None,
) -> None:
    if use_chart_scaffold:
        if not chart_scaffold_consistency_ok():
            solver.assertFormula(solver.mkBoolean(False))
    if use_balance:
        for engine in ("Type-1", "Type-2"):
            for loop in ("outer", "inner"):
                idxs = [i for i, row in enumerate(SLOTS) if row["engine"] == engine and row["loop"] == loop]
                solver.assertFormula(cvc5_exactly_two(solver, [vars_[i] for i in idxs]))
    if use_duality:
        for topology in ("Se", "Ne", "Ni", "Si"):
            solver.assertFormula(cvc5_iff(solver, vars_[TARGET_MAP[("Type-2", topology, "outer")]], vars_[TARGET_MAP[("Type-1", topology, "inner")]]))
            solver.assertFormula(cvc5_iff(solver, vars_[TARGET_MAP[("Type-2", topology, "inner")]], vars_[TARGET_MAP[("Type-1", topology, "outer")]]))
    if coupling_features is not None:
        expected = expected_bits_for_coupling(coupling_features)
        for var, bit in zip(vars_, expected, strict=True):
            solver.assertFormula(cvc5_iff(solver, var, solver.mkBoolean(bool(bit))))


def cvc5_status(result: Any) -> str:
    text = str(result)
    if text.startswith("sat"):
        return "sat"
    if text.startswith("unsat"):
        return "unsat"
    return text


def cvc5_count(
    *,
    use_chart_scaffold: bool = True,
    use_balance: bool = True,
    use_duality: bool = True,
    coupling_features: tuple[str, ...] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    vars_ = [solver.mkConst(bool_sort, f"v_{idx}") for idx in range(SLOT_COUNT)]
    cvc5_add_constraints(
        solver,
        vars_,
        use_chart_scaffold=use_chart_scaffold,
        use_balance=use_balance,
        use_duality=use_duality,
        coupling_features=coupling_features,
    )
    count = 0
    first_model = None
    while cvc5_status(solver.checkSat()) == "sat":
        values = [str(solver.getValue(var)) == "true" for var in vars_]
        if first_model is None:
            first_model = values
        blocks = [cvc5_not(solver, var) if value else var for var, value in zip(vars_, values, strict=True)]
        solver.assertFormula(cvc5_or(solver, blocks))
        count += 1
        if limit is not None and count >= limit:
            break
    return {
        "solver": "cvc5",
        "status_after_blocking": cvc5_status(solver.checkSat()),
        "model_count": count,
        "count_complete": limit is None or count < limit,
        "first_model_equals_documented": first_model == [bool(bit) for bit in TARGET_BITS],
    }


def cvc5_sat_for(
    bits: list[int],
    *,
    use_chart_scaffold: bool = True,
    use_balance: bool = True,
    use_duality: bool = True,
    coupling_features: tuple[str, ...] | None = None,
) -> str:
    solver = cvc5.Solver()
    bool_sort = solver.getBooleanSort()
    vars_ = [solver.mkConst(bool_sort, f"sat_v_{idx}") for idx in range(SLOT_COUNT)]
    cvc5_add_constraints(
        solver,
        vars_,
        use_chart_scaffold=use_chart_scaffold,
        use_balance=use_balance,
        use_duality=use_duality,
        coupling_features=coupling_features,
    )
    for var, bit in zip(vars_, bits, strict=True):
        solver.assertFormula(cvc5_iff(solver, var, solver.mkBoolean(bool(bit))))
    return cvc5_status(solver.checkSat())


def z3_sign_class_functionality(bits: list[int] = TARGET_BITS) -> list[dict[str, Any]]:
    rows = []
    for class_row in sign_outcome_class_table(bits):
        idxs = [row["slot"] for row in class_row["rows"]]
        case_vars = [z3.Bool(f"class_{class_row['sign_triple_key']}_case_{idx}") for idx in idxs]
        win_vars = [z3.Bool(f"class_{class_row['sign_triple_key']}_win_{idx}") for idx in idxs]
        solver = z3.Solver()
        for var, idx in zip(case_vars, idxs, strict=True):
            solver.add(var == bool(outcome_bits(SLOTS[idx], bits[idx])[0]))
        for var, idx in zip(win_vars, idxs, strict=True):
            solver.add(var == bool(outcome_bits(SLOTS[idx], bits[idx])[1]))
        solver.add(*[var == case_vars[0] for var in case_vars[1:]])
        solver.add(*[var == win_vars[0] for var in win_vars[1:]])
        rows.append(
            {
                "solver": "z3",
                "sign_triple": class_row["sign_triple"],
                "sign_triple_key": class_row["sign_triple_key"],
                "constant_constraint_status": str(solver.check()),
                "interpretation": "sat means the fixed documented outcomes are constant within this sign class; unsat means this class splits",
            }
        )
    return rows


def cvc5_sign_class_functionality(bits: list[int] = TARGET_BITS) -> list[dict[str, Any]]:
    rows = []
    for class_row in sign_outcome_class_table(bits):
        solver = cvc5.Solver()
        bool_sort = solver.getBooleanSort()
        idxs = [row["slot"] for row in class_row["rows"]]
        case_vars = [solver.mkConst(bool_sort, f"class_{class_row['sign_triple_key']}_case_{idx}") for idx in idxs]
        win_vars = [solver.mkConst(bool_sort, f"class_{class_row['sign_triple_key']}_win_{idx}") for idx in idxs]
        for var, idx in zip(case_vars, idxs, strict=True):
            solver.assertFormula(cvc5_iff(solver, var, solver.mkBoolean(bool(outcome_bits(SLOTS[idx], bits[idx])[0]))))
        for var, idx in zip(win_vars, idxs, strict=True):
            solver.assertFormula(cvc5_iff(solver, var, solver.mkBoolean(bool(outcome_bits(SLOTS[idx], bits[idx])[1]))))
        for var in case_vars[1:]:
            solver.assertFormula(cvc5_iff(solver, var, case_vars[0]))
        for var in win_vars[1:]:
            solver.assertFormula(cvc5_iff(solver, var, win_vars[0]))
        rows.append(
            {
                "solver": "cvc5",
                "sign_triple": class_row["sign_triple"],
                "sign_triple_key": class_row["sign_triple_key"],
                "constant_constraint_status": cvc5_status(solver.checkSat()),
                "interpretation": "sat means the fixed documented outcomes are constant within this sign class; unsat means this class splits",
            }
        )
    return rows


def coupling_count_report(feature_sets: list[tuple[str, ...]]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for features in feature_sets:
        key = "signs_only" if not features else "signs_plus_" + "_".join(features)
        full_models = brute_force_models(coupling_features=features)
        rows[key] = {
            "features": list(features),
            "functional": is_functional_with_features(features),
            "brute_force_model_count": len(full_models),
            "jax_model_count": jax_count(coupling_features=features),
            "z3_model_count": z3_count(coupling_features=features)["model_count"],
            "cvc5_model_count": cvc5_count(coupling_features=features)["model_count"],
            "drops_from_36_to_1": len(full_models) == 1,
        }
    return rows


def relaxed_axis6_orbit_diagnostic() -> dict[str, Any]:
    models = brute_force_models()
    orbit_sizes = {0: 0, 1: 0, 2: 0}
    for bits in models:
        outer_wins = {topology for topology in ("Se", "Ne", "Ni", "Si") if bits[TARGET_MAP[("Type-1", topology, "outer")]] == 1}
        inner_wins = {topology for topology in ("Se", "Ne", "Ni", "Si") if bits[TARGET_MAP[("Type-1", topology, "inner")]] == 1}
        orbit_sizes[len(outer_wins & inner_wins)] += 1
    return {
        "reading": "documented_axis6_scaffold_with_casing_balance_and_case_loop_duality",
        "raw_model_count": len(models),
        "declared_relabeling_group": "simultaneous S4 relabeling of the four stage/topology slots, preserving loop and engine duality",
        "orbit_count": 3,
        "orbit_sizes_by_type1_outer_inner_win_intersection": orbit_sizes,
        "documented_table_orbit_key": len(
            {topology for topology in ("Se", "Ne", "Ni", "Si") if TARGET_BITS[TARGET_MAP[("Type-1", topology, "outer")]] == 1}
            & {topology for topology in ("Se", "Ne", "Ni", "Si") if TARGET_BITS[TARGET_MAP[("Type-1", topology, "inner")]] == 1}
        ),
        "larger_wreath_product_note": "advisory surfaces mention larger bit/value relabeling groups; this diagnostic uses the conservative simultaneous stage relabeling only",
    }


def assignment_table(bits: list[int]) -> list[dict[str, Any]]:
    return [
        {
            "slot": idx,
            "engine": row["engine"],
            "topology": row["topology"],
            "loop": row["loop"],
            "token": row["token"],
            "op": row["op"],
            "axis6": row["axis6"],
            "assigned": bit_to_value(row, bits[idx]),
            "bit": int(bits[idx]),
        }
        for idx, row in enumerate(SLOTS)
    ]


def build_result() -> dict[str, Any]:
    full_models = brute_force_models()
    no_scaffold_models = brute_force_models(use_chart_scaffold=False)
    no_balance_models = brute_force_models(use_balance=False)
    scrambled = list(TARGET_BITS)
    scrambled[0] = 1 - scrambled[0]
    sign_analysis = sign_outcome_analysis()
    coupling_feature_sets = [tuple(row["features"]) for row in sign_analysis["minimal_functional_feature_sets"]]
    coupling_counts = coupling_count_report(coupling_feature_sets)
    full_count_jax = jax_count()
    no_scaffold_count_jax = jax_count(use_chart_scaffold=False)
    no_balance_count_jax = jax_count(use_balance=False)
    z3_full = z3_count()
    z3_no_scaffold = z3_count(use_chart_scaffold=False)
    z3_no_balance = z3_count(use_balance=False)
    cvc5_full = cvc5_count()
    cvc5_no_scaffold = cvc5_count(use_chart_scaffold=False)
    cvc5_no_balance = cvc5_count(use_balance=False)
    documented_z3 = z3_sat_for(TARGET_BITS)
    documented_cvc5 = cvc5_sat_for(TARGET_BITS)
    scrambled_z3 = z3_sat_for(scrambled)
    scrambled_cvc5 = cvc5_sat_for(scrambled)

    counts_agree = (
        full_count_jax == len(full_models) == z3_full["model_count"] == cvc5_full["model_count"]
        and no_scaffold_count_jax == len(no_scaffold_models) == z3_no_scaffold["model_count"] == cvc5_no_scaffold["model_count"]
        and no_balance_count_jax == len(no_balance_models) == z3_no_balance["model_count"] == cvc5_no_balance["model_count"]
    )
    target_sat = documented_z3 == documented_cvc5 == "sat" and constraints_ok(TARGET_BITS)
    scramble_unsat = scrambled_z3 == scrambled_cvc5 == "unsat" and not constraints_ok(scrambled)
    all_pass = bool(
        counts_agree
        and target_sat
        and scramble_unsat
        and full_count_jax == 36
        and no_scaffold_count_jax == full_count_jax
        and any(row["drops_from_36_to_1"] for row in coupling_counts.values())
        and no_balance_count_jax == 256
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "schema_version": "three_engine_leg_result_v1",
        "sim_id": SIM_ID,
        "object_id": OBJECT_ID,
        "engine": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_sha256(),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {"jax_enable_x64": bool(jax.config.jax_enable_x64), "jax_version": jax.__version__},
        "identity_pin": {
            "documented_table_sources": [
                "system_v6/receipts/screenshots_math_report_20260609.md:NeTX.png",
                "system_v6/receipts/screenshots_math_report_20260609.md:Topology.png",
                "system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:section 2",
            ],
            "bit_convention": "outer WIN=1 LOSE=0; inner win=1 lose=0; b0 is separate Axis0 family sign: Ne/Ni=+1, Se/Si=-1",
            "b3": LOOP_SIGN,
            "b6": AXIS6_SIGN,
            "relation": "b6=-b0*b3",
            "readout_fence": "WIN/LOSE/win/lose casing values are assignment/readout grammar, not b0 itself",
            "chart_scaffold_consistency": {
                "status": chart_scaffold_consistency_ok(),
                "interpretation": "metadata identity over documented row scaffold, not a predicate over assignment bits",
            },
        },
        "documented_table": documented_table(),
        "sign_outcome_analysis": sign_analysis,
        "solution_counts": {
            "full_constraints": full_count_jax,
            "drop_chart_scaffold_consistency": no_scaffold_count_jax,
            "drop_balance": no_balance_count_jax,
        },
        "controls": {
            "drop_chart_scaffold_consistency_increases": no_scaffold_count_jax > full_count_jax,
            "drop_chart_scaffold_consistency_interpretation": "does not increase because b6=-b0*b3 is a documented row-scaffold metadata identity, not an assignment-bit predicate",
            "outcome_coupling_counts": coupling_counts,
            "outcome_coupling_interpretation": "signs alone are not functional; adding operator id makes outcome a function and drops the balanced-dual model count from 36 to 1",
            "drop_balance_changes_count": no_balance_count_jax != full_count_jax,
            "drop_balance_interpretation": "balance is load-bearing for the casing-table count under the documented b0/readout separation",
            "scramble_one_documented_cell": {
                "slot": 0,
                "from": "LOSE",
                "to": "WIN",
                "z3": scrambled_z3,
                "cvc5": scrambled_cvc5,
                "violations": constraint_violations(scrambled),
            },
        },
        "documented_table_sat": {
            "direct_constraints": target_sat,
            "z3": documented_z3,
            "cvc5": documented_cvc5,
        },
        "smt": {
            "z3": {
                "verdict": documented_z3,
                "documented_table_sat": documented_z3,
                "full_constraints": z3_full,
                "drop_chart_scaffold_consistency": z3_no_scaffold,
                "drop_balance": z3_no_balance,
                "sign_class_functionality": z3_sign_class_functionality(),
                "scrambled_table_sat": scrambled_z3,
            },
            "cvc5": {
                "verdict": documented_cvc5,
                "documented_table_sat": documented_cvc5,
                "full_constraints": cvc5_full,
                "drop_chart_scaffold_consistency": cvc5_no_scaffold,
                "drop_balance": cvc5_no_balance,
                "sign_class_functionality": cvc5_sign_class_functionality(),
                "scrambled_table_sat": scrambled_cvc5,
            },
        },
        "relaxed_orbit_diagnostic": relaxed_axis6_orbit_diagnostic(),
        "witness_model": assignment_table(full_models[0]) if full_models else [],
        "verdict": f"underdetermined-{len(full_models)}",
        "shared_scalars": {
            "full_solution_count": float(full_count_jax),
            "drop_chart_scaffold_consistency_solution_count": float(no_scaffold_count_jax),
            "selected_outcome_coupling_solution_count": float(
                coupling_counts["signs_plus_" + "_".join(sign_analysis["selected_minimal_extra_input"])]["brute_force_model_count"]
            ),
            "drop_balance_solution_count": float(no_balance_count_jax),
            "documented_table_sat": 1.0 if target_sat else 0.0,
            "scrambled_table_sat": 1.0 if scrambled_z3 == "sat" or scrambled_cvc5 == "sat" else 0.0,
            "relaxed_raw_model_count": float(relaxed_axis6_orbit_diagnostic()["raw_model_count"]),
        },
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": documented_z3, "model_count_full_constraints": z3_full["model_count"], "uniqueness_after_blocking": z3_full["status_after_blocking"]},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": documented_cvc5, "model_count_full_constraints": cvc5_full["model_count"], "uniqueness_after_blocking": cvc5_full["status_after_blocking"]},
        },
        "all_pass": all_pass,
        "claim_ceiling": "finite combinatorics discriminator only; owner labels are annotations; no canonical promotion or scientific admission claim",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "WINLOSE_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"full={result['solution_counts']['full_constraints']} "
        f"drop_scaffold={result['solution_counts']['drop_chart_scaffold_consistency']} "
        f"selected_coupling={result['shared_scalars']['selected_outcome_coupling_solution_count']:.0f} "
        f"drop_balance={result['solution_counts']['drop_balance']} "
        f"z3={result['smt']['z3']['documented_table_sat']} "
        f"cvc5={result['smt']['cvc5']['documented_table_sat']} "
        f"verdict={result['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
