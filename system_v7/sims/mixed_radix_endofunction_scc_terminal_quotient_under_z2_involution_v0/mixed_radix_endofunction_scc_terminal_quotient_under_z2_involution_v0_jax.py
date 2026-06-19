#!/usr/bin/env python3
"""JAX leg: vmapped exhaustive transition-table materialization.

The only shared input is spec.json. This file does not import the v6 feedstock
and does not read Julia or PyTorch results.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import networkx as nx
import z3

jax.config.update("jax_enable_x64", True)

SIM_ID = "mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0"
HERE = os.path.dirname(os.path.abspath(__file__))


def sha256_of(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def encode(coords: tuple[int, int, int, int], shape: list[int]) -> int:
    out = 0
    for value, modulus in zip(coords, shape):
        out = out * modulus + value
    return int(out)


def decode_scalar(state_id: int, shape: list[int]) -> tuple[int, int, int, int]:
    values = []
    rest = int(state_id)
    for modulus in reversed(shape):
        values.append(rest % modulus)
        rest //= modulus
    return tuple(reversed(values))  # type: ignore[return-value]


def decode_batch(ids: jax.Array, shape: list[int]) -> tuple[jax.Array, jax.Array, jax.Array, jax.Array]:
    z = ids % shape[3]
    rest = ids // shape[3]
    d2 = rest % shape[2]
    rest = rest // shape[2]
    d1 = rest % shape[1]
    d0 = rest // shape[1]
    return d0, d1, d2, z


def readout_sign(spec: dict, orientation: str, d0: int, d1: int) -> int:
    word = spec["orientation_tables"][orientation]["radix_digit_0_word_rows"][d0][d1]
    component = spec["word_readout_components"][word][d0]
    return int(spec["readout_sign_map"][component])


def base_next_scalar(spec: dict, orientation: str, state_id: int) -> tuple[int, bool, int, int]:
    shape = spec["mixed_radix_shape"]
    d0, d1, d2, z = decode_scalar(state_id, shape)
    current = readout_sign(spec, orientation, d0, d1)
    nxt = readout_sign(spec, orientation, d0, (d1 + 1) % shape[1])
    next_d2 = (d2 + (1 if d0 == 0 else 3)) % shape[2]
    next_d0, next_d1 = d0, d1
    if next_d2 == 0:
        inc = 1 if current != nxt else 2
        next_d1 += inc
        while next_d1 >= shape[1]:
            next_d1 -= shape[1]
            next_d0 = (next_d0 + 1) % shape[0]
    boundary = (next_d0 != d0) or (next_d1 != d1)
    return encode((next_d0, next_d1, next_d2, z), shape), boundary, current, readout_sign(spec, orientation, next_d0, next_d1)


def event_selected(spec: dict, orientation: str, state_id: int) -> bool:
    base_id, boundary, _current, next_sign = base_next_scalar(spec, orientation, state_id)
    del base_id
    d0, _d1, _d2, _z = decode_scalar(state_id, spec["mixed_radix_shape"])
    orientation_sign = int(spec["orientation_tables"][orientation]["orientation_sign"])
    orientation_row = (orientation_sign > 0 and d0 == 0) or (orientation_sign < 0 and d0 == 1)
    return bool(boundary and orientation_row and orientation_sign * next_sign < 0)


def apply_law(spec: dict, orientation: str, state_id: int, law: str) -> int:
    shape = spec["mixed_radix_shape"]
    base_id, _boundary, _current, _next = base_next_scalar(spec, orientation, state_id)
    d0, d1, d2, z = decode_scalar(base_id, shape)
    old_z = decode_scalar(state_id, shape)[3]
    event = event_selected(spec, orientation, state_id)
    if law == "conserved_control":
        next_z = old_z
    elif law == "parity_flipping_law":
        next_z = 1 if (event and old_z == 0) else old_z
    elif law == "reference_toggle_law":
        next_z = 1 - old_z if event else old_z
    else:
        raise ValueError(law)
    return encode((d0, d1, d2, next_z), shape)


def transition_table_python(spec: dict, orientation: str, law: str) -> list[int]:
    return [apply_law(spec, orientation, state_id, law) for state_id in range(64)]


def transition_table_jax(spec: dict, orientation: str, law: str) -> list[int]:
    shape = spec["mixed_radix_shape"]
    words = spec["orientation_tables"][orientation]["radix_digit_0_word_rows"]
    comp = spec["word_readout_components"]
    sign_map = spec["readout_sign_map"]
    sign_rows = []
    for d0 in range(shape[0]):
        row = []
        for d1 in range(shape[1]):
            row.append(sign_map[comp[words[d0][d1]][d0]])
        sign_rows.append(row)
    signs = jnp.array(sign_rows, dtype=jnp.int64)
    orientation_sign = int(spec["orientation_tables"][orientation]["orientation_sign"])
    ids = jnp.arange(64, dtype=jnp.int64)

    def one(state_id: jax.Array) -> jax.Array:
        d0, d1, d2, z = decode_batch(state_id, shape)
        current = signs[d0, d1]
        nxt = signs[d0, (d1 + 1) % shape[1]]
        next_d2 = (d2 + jnp.where(d0 == 0, 1, 3)) % shape[2]
        inc = jnp.where(current != nxt, 1, 2)
        raw_d1 = d1 + inc
        carried_d1 = raw_d1 % shape[1]
        carried_d0 = (d0 + (raw_d1 // shape[1])) % shape[0]
        crosses = next_d2 == 0
        out_d0 = jnp.where(crosses, carried_d0, d0)
        out_d1 = jnp.where(crosses, carried_d1, d1)
        out_d2 = next_d2
        next_sign = signs[out_d0, out_d1]
        boundary = jnp.logical_or(out_d0 != d0, out_d1 != d1)
        orientation_row = jnp.where(orientation_sign > 0, d0 == 0, d0 == 1)
        event = jnp.logical_and(jnp.logical_and(boundary, orientation_row), orientation_sign * next_sign < 0)
        if law == "conserved_control":
            out_z = z
        elif law == "parity_flipping_law":
            out_z = jnp.where(jnp.logical_and(event, z == 0), 1, z)
        elif law == "reference_toggle_law":
            out_z = jnp.where(event, 1 - z, z)
        else:
            raise ValueError(law)
        return (((out_d0 * shape[1] + out_d1) * shape[2] + out_d2) * shape[3] + out_z).astype(jnp.int64)

    table = jax.vmap(one)(ids)
    return [int(x) for x in table.tolist()]


def scc_summary(table: list[int]) -> dict:
    graph = nx.DiGraph()
    graph.add_nodes_from(range(len(table)))
    graph.add_edges_from((idx, dst) for idx, dst in enumerate(table))
    classes = [sorted(list(comp)) for comp in nx.strongly_connected_components(graph)]
    classes.sort(key=lambda row: (min(row), len(row)))
    class_of = {}
    for idx, members in enumerate(classes):
        for member in members:
            class_of[member] = idx
    outgoing = {idx: set() for idx in range(len(classes))}
    for src, dst in enumerate(table):
        a, b = class_of[src], class_of[dst]
        if a != b:
            outgoing[a].add(b)
    terminal = [idx for idx in range(len(classes)) if not outgoing[idx]]
    return {
        "scc_count": len(classes),
        "scc_classes": classes,
        "quotient_classes": classes,
        "quotient_class_count": len(classes),
        "terminal_scc_count": len(terminal),
        "terminal_scc_sizes": sorted(len(classes[idx]) for idx in terminal),
        "terminal_scc_class_ids": terminal,
        "condensation_edge_count": sum(len(v) for v in outgoing.values()),
    }


def sigma_table(shape: list[int]) -> list[int]:
    out = []
    for state_id in range(64):
        d0, d1, d2, z = decode_scalar(state_id, shape)
        out.append(encode((d0, d1, d2, 1 - z), shape))
    return out


def direct_separators(table: list[int], sigma: list[int]) -> list[dict[str, int]]:
    rows = []
    for state_id in range(len(table)):
        left = table[sigma[state_id]]
        right = sigma[table[state_id]]
        if left != right:
            rows.append({"state_id": state_id, "left_image": left, "right_image": right})
    return rows


def z3_exists_separator(table: list[int], sigma: list[int]) -> str:
    solver = z3.Solver()
    array_sort = z3.ArraySort(z3.IntSort(), z3.IntSort())
    trans = z3.Const("T", array_sort)
    inv = z3.Const("sigma", array_sort)
    for idx, value in enumerate(table):
        solver.add(z3.Select(trans, z3.IntVal(idx)) == z3.IntVal(value))
    for idx, value in enumerate(sigma):
        solver.add(z3.Select(inv, z3.IntVal(idx)) == z3.IntVal(value))
    clauses = [
        z3.Select(trans, z3.IntVal(sigma[idx])) != z3.Select(inv, z3.IntVal(table[idx]))
        for idx in range(len(table))
    ]
    solver.add(z3.Or(*clauses))
    return str(solver.check())


def cvc5_exists_separator(table: list[int], sigma: list[int]) -> str:
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_AUFLIA")
    int_sort = tm.getIntegerSort()
    array_sort = tm.mkArraySort(int_sort, int_sort)
    trans = tm.mkConst(array_sort, "T")
    inv = tm.mkConst(array_sort, "sigma")
    for idx, value in enumerate(table):
        solver.assertFormula(
            tm.mkTerm(Kind.EQUAL, tm.mkTerm(Kind.SELECT, trans, tm.mkInteger(idx)), tm.mkInteger(value))
        )
    for idx, value in enumerate(sigma):
        solver.assertFormula(
            tm.mkTerm(Kind.EQUAL, tm.mkTerm(Kind.SELECT, inv, tm.mkInteger(idx)), tm.mkInteger(value))
        )
    clauses = []
    for idx, value in enumerate(table):
        left = tm.mkTerm(Kind.SELECT, trans, tm.mkInteger(sigma[idx]))
        right = tm.mkTerm(Kind.SELECT, inv, tm.mkInteger(value))
        clauses.append(tm.mkTerm(Kind.DISTINCT, left, right))
    solver.assertFormula(clauses[0] if len(clauses) == 1 else tm.mkTerm(Kind.OR, *clauses))
    result = solver.checkSat()
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def build_result() -> dict:
    with open(os.path.join(HERE, "spec.json"), encoding="utf-8") as handle:
        spec = json.load(handle)
    shape = spec["mixed_radix_shape"]
    sigma = sigma_table(shape)
    laws = list(spec["update_law_identifiers"].keys())
    orientations = ["map_plus", "map_minus"]
    summaries = {}
    direct = {}
    smt_rows = {}
    for orientation in orientations:
        summaries[orientation] = {}
        direct[orientation] = {}
        for law in laws:
            table = transition_table_jax(spec, orientation, law)
            scalar_table = transition_table_python(spec, orientation, law)
            if table != scalar_table:
                raise AssertionError(f"JAX table disagrees with scalar table for {orientation}/{law}")
            summary = scc_summary(table)
            summary["endofunction_table"] = table
            summaries[orientation][law] = summary
            direct[orientation][law] = direct_separators(table, sigma)
        eq_table = summaries[orientation]["conserved_control"]["endofunction_table"]
        neq_table = summaries[orientation]["parity_flipping_law"]["endofunction_table"]
        smt_rows[orientation] = {
            "z3_equivariant_map": z3_exists_separator(eq_table, sigma),
            "z3_nonequivariant_map": z3_exists_separator(neq_table, sigma),
            "cvc5_equivariant_map": cvc5_exists_separator(eq_table, sigma),
            "cvc5_nonequivariant_map": cvc5_exists_separator(neq_table, sigma),
            "direct_equivariant_separator_count": len(direct[orientation]["conserved_control"]),
            "direct_nonequivariant_separator_count": len(direct[orientation]["parity_flipping_law"]),
            "direct_nonequivariant_separator_sample": direct[orientation]["parity_flipping_law"][:8],
        }

    selected = {orientation: summaries[orientation]["parity_flipping_law"] for orientation in orientations}
    smt_ok = all(
        row["z3_equivariant_map"] == "unsat"
        and row["z3_nonequivariant_map"] == "sat"
        and row["cvc5_equivariant_map"] == "unsat"
        and row["cvc5_nonequivariant_map"] == "sat"
        and row["direct_equivariant_separator_count"] == 0
        and row["direct_nonequivariant_separator_count"] > 0
        for row in smt_rows.values()
    )
    if not smt_ok:
        raise AssertionError(f"SMT structural flip failed: {smt_rows}")

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "computation_style": "jax_vmap_exhaustive_endofunction_table_plus_smt_arrays",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_jax_results.json",
        "mixed_radix_shape": shape,
        "finite_set_size": 64,
        "state_labels": [str(i) for i in range(64)],
        "transition_map": {k: v["endofunction_table"] for k, v in selected.items()},
        "endofunction_table": {k: v["endofunction_table"] for k, v in selected.items()},
        "scc_count": {k: v["scc_count"] for k, v in selected.items()},
        "scc_classes": {k: v["scc_classes"] for k, v in selected.items()},
        "quotient_classes": {k: v["quotient_classes"] for k, v in selected.items()},
        "quotient_class_count": {k: v["quotient_class_count"] for k, v in selected.items()},
        "terminal_scc_count": {k: v["terminal_scc_count"] for k, v in selected.items()},
        "terminal_scc_sizes": {k: v["terminal_scc_sizes"] for k, v in selected.items()},
        "involution_definition": spec["involution_definition"],
        "involution_is_equivariant": {
            orientation: {law: len(direct[orientation][law]) == 0 for law in laws}
            for orientation in orientations
        },
        "per_orientation": summaries,
        "smt_equivariance_flip": {
            "question": "does there exist a state s with T(sigma(s)) != sigma(T(s))?",
            "encoding": "Integer arrays T and sigma are constrained to the computed images over all 64 states; the query is a disjunction over computed image disequalities, not a count tautology.",
            "z3_equivariant_map": smt_rows["map_plus"]["z3_equivariant_map"],
            "z3_nonequivariant_map": smt_rows["map_plus"]["z3_nonequivariant_map"],
            "cvc5_equivariant_map": smt_rows["map_plus"]["cvc5_equivariant_map"],
            "cvc5_nonequivariant_map": smt_rows["map_plus"]["cvc5_nonequivariant_map"],
            "per_orientation": smt_rows,
            "real_structural_flip_confirmed": smt_ok,
        },
        "lineage": spec["lineage"],
        "legacy_project_labels": spec["legacy_project_labels"],
        "legacy_paths": spec["legacy_paths"],
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "load-bearing vmapped construction of the full 64-entry endofunction table"},
            "networkx": {"tried": True, "used": True, "reason": "load-bearing SCC and terminal quotient computation from the edge list"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing array encoding of equivariance counterexample existence"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent array encoding of the same counterexample query"}
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "networkx": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"},
        "packages_used": ["jax", "networkx", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["jax", "networkx", "z3", "cvc5"]
    }


def main() -> None:
    result = build_result()
    out = os.path.join(HERE, "results", f"{SIM_ID}_jax_results.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"jax leg wrote {out}")
    print(json.dumps(result["terminal_scc_sizes"], sort_keys=True))
    print(json.dumps(result["smt_equivariance_flip"], sort_keys=True))


if __name__ == "__main__":
    main()
