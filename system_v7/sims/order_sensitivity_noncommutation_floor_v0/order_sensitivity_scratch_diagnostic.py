from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Mapping, Sequence, Tuple

import cvc5
from cvc5 import Kind
import z3


TOKENS: Tuple[str, ...] = ("x0", "x1", "x2", "x3", "x4", "x5")
TOKEN_INDEX: Dict[str, int] = {token: i for i, token in enumerate(TOKENS)}
INITIAL_PARTITION: Tuple[FrozenSet[str], ...] = tuple(frozenset([t]) for t in TOKENS)


@dataclass(frozen=True)
class CarveOperation:
    name: str
    keep: FrozenSet[str]
    probe: Mapping[str, str]
    math: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "survivor_keep_set": token_list(self.keep),
            "probe_partition": probe_partition(self.probe),
            "math": self.math,
        }


def token_key(token: str) -> int:
    return TOKEN_INDEX[token]


def token_list(tokens: Iterable[str]) -> List[str]:
    return sorted(tokens, key=token_key)


def cell_list(cell: FrozenSet[str]) -> List[str]:
    return token_list(cell)


def partition_to_lists(partition: Sequence[FrozenSet[str]]) -> List[List[str]]:
    return [cell_list(cell) for cell in partition]


def survivor_set(partition: Sequence[FrozenSet[str]]) -> FrozenSet[str]:
    out = set()
    for cell in partition:
        out.update(cell)
    return frozenset(out)


def normalize_partition(cells: Iterable[Iterable[str]]) -> Tuple[FrozenSet[str], ...]:
    frozen = [frozenset(cell) for cell in cells if cell]
    return tuple(sorted(frozen, key=lambda cell: min(TOKEN_INDEX[t] for t in cell)))


def probe_partition(probe: Mapping[str, str]) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    for token in TOKENS:
        groups.setdefault(probe[token], []).append(token)
    return {label: token_list(tokens) for label, tokens in sorted(groups.items())}


def apply_operation(
    partition: Sequence[FrozenSet[str]], operation: CarveOperation
) -> Tuple[Tuple[FrozenSet[str], ...], Dict[str, object]]:
    kept_cells: List[FrozenSet[str]] = []
    excluded_cells: List[FrozenSet[str]] = []
    for cell in partition:
        if cell.issubset(operation.keep):
            kept_cells.append(cell)
        else:
            excluded_cells.append(cell)

    quotient_groups: Dict[Tuple[str, ...], List[str]] = {}
    for cell in kept_cells:
        signature = tuple(sorted({operation.probe[token] for token in cell}))
        quotient_groups.setdefault(signature, []).extend(cell)

    next_partition = normalize_partition(quotient_groups.values())
    trace = {
        "operation": operation.name,
        "input_partition": partition_to_lists(partition),
        "strict_survivor_cells_kept": partition_to_lists(kept_cells),
        "strict_survivor_cells_excluded": partition_to_lists(excluded_cells),
        "quotient_signature_to_tokens": {
            ",".join(signature): token_list(tokens)
            for signature, tokens in sorted(quotient_groups.items())
        },
        "output_partition": partition_to_lists(next_partition),
    }
    return next_partition, trace


def run_order(
    first: CarveOperation, second: CarveOperation
) -> Tuple[Tuple[FrozenSet[str], ...], List[Dict[str, object]]]:
    partition, trace_first = apply_operation(INITIAL_PARTITION, first)
    partition, trace_second = apply_operation(partition, second)
    return partition, [trace_first, trace_second]


def z3_survives_expr(cfg: z3.IntNumRef, survivors: FrozenSet[int]):
    if not survivors:
        return z3.BoolVal(False)
    return z3.Or([cfg == index for index in sorted(survivors)])


def z3_flip_query(
    survivors_a_then_b: FrozenSet[int], survivors_b_then_a: FrozenSet[int]
) -> Dict[str, object]:
    cfg = z3.Int("cfg")
    in_a_then_b = z3_survives_expr(cfg, survivors_a_then_b)
    in_b_then_a = z3_survives_expr(cfg, survivors_b_then_a)
    solver = z3.Solver()
    solver.add(cfg >= 0, cfg < len(TOKENS))
    solver.add(
        z3.Or(
            z3.And(in_a_then_b, z3.Not(in_b_then_a)),
            z3.And(in_b_then_a, z3.Not(in_a_then_b)),
        )
    )
    result = solver.check()
    report: Dict[str, object] = {"flip_exists": str(result)}
    if result == z3.sat:
        index = solver.model()[cfg].as_long()
        report["witness"] = TOKENS[index]
    return report


def z3_membership_query(survivors: FrozenSet[int], token: str) -> str:
    cfg = z3.Int("cfg")
    solver = z3.Solver()
    solver.add(cfg >= 0, cfg < len(TOKENS))
    solver.add(cfg == TOKEN_INDEX[token])
    solver.add(z3_survives_expr(cfg, survivors))
    return str(solver.check())


def cvc5_or(solver: cvc5.Solver, terms: Sequence[cvc5.Term]) -> cvc5.Term:
    if not terms:
        return solver.mkBoolean(False)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.OR, *terms)


def cvc5_and(solver: cvc5.Solver, terms: Sequence[cvc5.Term]) -> cvc5.Term:
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.AND, *terms)


def cvc5_not(solver: cvc5.Solver, term: cvc5.Term) -> cvc5.Term:
    return solver.mkTerm(Kind.NOT, term)


def cvc5_survives_expr(
    solver: cvc5.Solver, cfg: cvc5.Term, survivors: FrozenSet[int]
) -> cvc5.Term:
    terms = [
        solver.mkTerm(Kind.EQUAL, cfg, solver.mkInteger(index))
        for index in sorted(survivors)
    ]
    return cvc5_or(solver, terms)


def make_cvc5_solver() -> cvc5.Solver:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("QF_LIA")
    return solver


def cvc5_flip_query(
    survivors_a_then_b: FrozenSet[int], survivors_b_then_a: FrozenSet[int]
) -> Dict[str, object]:
    solver = make_cvc5_solver()
    int_sort = solver.getIntegerSort()
    cfg = solver.mkConst(int_sort, "cfg")
    in_a_then_b = cvc5_survives_expr(solver, cfg, survivors_a_then_b)
    in_b_then_a = cvc5_survives_expr(solver, cfg, survivors_b_then_a)
    domain = cvc5_and(
        solver,
        [
            solver.mkTerm(Kind.GEQ, cfg, solver.mkInteger(0)),
            solver.mkTerm(Kind.LT, cfg, solver.mkInteger(len(TOKENS))),
        ],
    )
    flip = cvc5_or(
        solver,
        [
            cvc5_and(solver, [in_a_then_b, cvc5_not(solver, in_b_then_a)]),
            cvc5_and(solver, [in_b_then_a, cvc5_not(solver, in_a_then_b)]),
        ],
    )
    solver.assertFormula(domain)
    solver.assertFormula(flip)
    result = solver.checkSat()
    report: Dict[str, object] = {"flip_exists": str(result)}
    if result.isSat():
        index = int(str(solver.getValue(cfg)))
        report["witness"] = TOKENS[index]
    return report


def cvc5_membership_query(survivors: FrozenSet[int], token: str) -> str:
    solver = make_cvc5_solver()
    int_sort = solver.getIntegerSort()
    cfg = solver.mkConst(int_sort, "cfg")
    solver.assertFormula(solver.mkTerm(Kind.GEQ, cfg, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(Kind.LT, cfg, solver.mkInteger(len(TOKENS))))
    solver.assertFormula(
        solver.mkTerm(Kind.EQUAL, cfg, solver.mkInteger(TOKEN_INDEX[token]))
    )
    solver.assertFormula(cvc5_survives_expr(solver, cfg, survivors))
    return str(solver.checkSat())


def survivor_indices(partition: Sequence[FrozenSet[str]]) -> FrozenSet[int]:
    return frozenset(TOKEN_INDEX[token] for token in survivor_set(partition))


def order_result_dict(
    partition: Sequence[FrozenSet[str]], trace: Sequence[Dict[str, object]]
) -> Dict[str, object]:
    return {
        "survivor_set": token_list(survivor_set(partition)),
        "partition": partition_to_lists(partition),
        "trace": list(trace),
    }


def compare_pair(
    pair_id: str, description: str, operation_a: CarveOperation, operation_b: CarveOperation
) -> Dict[str, object]:
    a_then_b_partition, a_then_b_trace = run_order(operation_a, operation_b)
    b_then_a_partition, b_then_a_trace = run_order(operation_b, operation_a)

    a_then_b_survivors = survivor_indices(a_then_b_partition)
    b_then_a_survivors = survivor_indices(b_then_a_partition)
    symmetric_difference = a_then_b_survivors ^ b_then_a_survivors
    differing_configs = [TOKENS[index] for index in sorted(symmetric_difference)]

    z3_report = z3_flip_query(a_then_b_survivors, b_then_a_survivors)
    cvc5_report = cvc5_flip_query(a_then_b_survivors, b_then_a_survivors)

    witness_membership: Dict[str, object] = {}
    for token in differing_configs:
        witness_membership[token] = {
            "z3": {
                "A_then_B": z3_membership_query(a_then_b_survivors, token),
                "B_then_A": z3_membership_query(b_then_a_survivors, token),
            },
            "cvc5": {
                "A_then_B": cvc5_membership_query(a_then_b_survivors, token),
                "B_then_A": cvc5_membership_query(b_then_a_survivors, token),
            },
        }

    orders_same = (
        partition_to_lists(a_then_b_partition) == partition_to_lists(b_then_a_partition)
        and token_list(survivor_set(a_then_b_partition))
        == token_list(survivor_set(b_then_a_partition))
    )
    solver_says_no_flip = (
        z3_report["flip_exists"] == "unsat" and cvc5_report["flip_exists"] == "unsat"
    )
    solver_says_flip = (
        z3_report["flip_exists"] == "sat" and cvc5_report["flip_exists"] == "sat"
    )

    verdict = "genuine" if differing_configs and solver_says_flip else "trivial"
    if not differing_configs and not (orders_same and solver_says_no_flip):
        verdict = "invalid"

    return {
        "pair_id": pair_id,
        "description": description,
        "operations": {"A": operation_a.as_dict(), "B": operation_b.as_dict()},
        "composition_convention": "A_then_B means apply A first, then B; B_then_A means apply B first, then A.",
        "a_then_b": order_result_dict(a_then_b_partition, a_then_b_trace),
        "b_then_a": order_result_dict(b_then_a_partition, b_then_a_trace),
        "differing_configs": differing_configs,
        "z3": z3_report,
        "cvc5": cvc5_report,
        "witness_membership": witness_membership,
        "verdict": verdict,
    }


def build_operations() -> Dict[str, Tuple[CarveOperation, CarveOperation]]:
    all_tokens = frozenset(TOKENS)
    pair_probe = {
        "x0": "p01",
        "x1": "p01",
        "x2": "p23",
        "x3": "p23",
        "x4": "p45",
        "x5": "p45",
    }
    identity_probe = {token: token for token in TOKENS}
    blur01_probe = {
        "x0": "q01",
        "x1": "q01",
        "x2": "q2",
        "x3": "q3",
        "x4": "q4",
        "x5": "q5",
    }

    commuting_a = CarveOperation(
        name="C_A_pair_probe_keep_all",
        keep=all_tokens,
        probe=pair_probe,
        math="Keep X, then quotient by {{x0,x1},{x2,x3},{x4,x5}}.",
    )
    commuting_b = CarveOperation(
        name="C_B_pair_probe_keep_01_23",
        keep=frozenset(("x0", "x1", "x2", "x3")),
        probe=pair_probe,
        math="Keep {x0,x1,x2,x3}, then quotient by the same saturated pair probe.",
    )
    noncommuting_a = CarveOperation(
        name="N_A_blur_01_keep_all",
        keep=all_tokens,
        probe=blur01_probe,
        math="Keep X, then quotient x0~x1 while leaving x2,x3,x4,x5 singleton.",
    )
    noncommuting_b = CarveOperation(
        name="N_B_cut_x1_identity_probe",
        keep=frozenset(("x0", "x2", "x3", "x4", "x5")),
        probe=identity_probe,
        math="Keep X\\{x1}, then apply the identity probe quotient.",
    )

    return {
        "commuting_saturated_pair": (commuting_a, commuting_b),
        "noncommuting_blur_then_cut_pair": (noncommuting_a, noncommuting_b),
    }


def build_report(results_path: str | None = None) -> Dict[str, object]:
    operations = build_operations()
    commuting = compare_pair(
        "commuting_saturated_pair",
        "A saturated keep set is a union of A's quotient blocks, so the strict carve boundary is not crossed by the prior quotient.",
        operations["commuting_saturated_pair"][0],
        operations["commuting_saturated_pair"][1],
    )
    noncommuting = compare_pair(
        "noncommuting_blur_then_cut_pair",
        "A first erases the x0/x1 distinction; B can no longer keep x0 while excluding x1, so x0 flips.",
        operations["noncommuting_blur_then_cut_pair"][0],
        operations["noncommuting_blur_then_cut_pair"][1],
    )

    all_pass = (
        commuting["verdict"] == "trivial"
        and commuting["z3"]["flip_exists"] == "unsat"
        and commuting["cvc5"]["flip_exists"] == "unsat"
        and commuting["differing_configs"] == []
        and noncommuting["verdict"] == "genuine"
        and noncommuting["z3"]["flip_exists"] == "sat"
        and noncommuting["cvc5"]["flip_exists"] == "sat"
        and noncommuting["differing_configs"] == ["x0"]
        and noncommuting["witness_membership"]["x0"]["z3"]["A_then_B"] == "unsat"
        and noncommuting["witness_membership"]["x0"]["z3"]["B_then_A"] == "sat"
        and noncommuting["witness_membership"]["x0"]["cvc5"]["A_then_B"] == "unsat"
        and noncommuting["witness_membership"]["x0"]["cvc5"]["B_then_A"] == "sat"
    )

    report: Dict[str, object] = {
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "support": list(TOKENS),
        "initial_partition": partition_to_lists(INITIAL_PARTITION),
        "semantics": {
            "state": "A state is a partition of the surviving original tokens.",
            "operation": "An operation first keeps a current quotient cell only when that whole cell is a subset of the operation's survivor_keep_set; it then applies a quotient-only probe coarsening and never splits an existing cell.",
            "flip_query": "A flip exists when SMT can find cfg in X that survives exactly one of A_then_B or B_then_A.",
        },
        "pairs": [commuting, noncommuting],
        "anti_tautology_proof": "The same compare_pair and SMT flip machinery returns trivial for commuting_saturated_pair (z3/cvc5 flip_exists=unsat) and genuine for noncommuting_blur_then_cut_pair (z3/cvc5 flip_exists=sat, x0 membership is unsat vs sat by order).",
        "honest_scope": "Order is load-bearing only for noncommuting_blur_then_cut_pair in this finite survivor/quotient fixture; commuting_saturated_pair is trivial; forced-vs-installed remains OPEN; no carrier, geometry, physics, or canonical claim is made.",
        "all_pass": bool(all_pass),
    }
    if results_path is not None:
        report["results_file"] = results_path
    return report


def format_pair(pair: Mapping[str, object]) -> List[str]:
    lines: List[str] = []
    lines.append(f"PAIR {pair['pair_id']}")
    lines.append(f"verdict: {pair['verdict']}")
    lines.append(f"description: {pair['description']}")
    operations = pair["operations"]
    assert isinstance(operations, dict)
    for label in ("A", "B"):
        operation = operations[label]
        assert isinstance(operation, dict)
        lines.append(f"op {label}: {operation['name']}")
        lines.append(f"  survivor_keep_set: {operation['survivor_keep_set']}")
        lines.append(f"  probe_partition: {operation['probe_partition']}")
        lines.append(f"  math: {operation['math']}")

    a_then_b = pair["a_then_b"]
    b_then_a = pair["b_then_a"]
    assert isinstance(a_then_b, dict)
    assert isinstance(b_then_a, dict)
    lines.append("A_comp_B / A_then_B result (apply A first, then B):")
    lines.append(f"  survivor_set: {a_then_b['survivor_set']}")
    lines.append(f"  partition: {a_then_b['partition']}")
    lines.append("B_comp_A / B_then_A result (apply B first, then A):")
    lines.append(f"  survivor_set: {b_then_a['survivor_set']}")
    lines.append(f"  partition: {b_then_a['partition']}")
    lines.append(f"differing_configs: {pair['differing_configs']}")
    lines.append(f"z3 flip_exists: {pair['z3']['flip_exists']}")
    if "witness" in pair["z3"]:
        lines.append(f"z3 witness: {pair['z3']['witness']}")
    lines.append(f"cvc5 flip_exists: {pair['cvc5']['flip_exists']}")
    if "witness" in pair["cvc5"]:
        lines.append(f"cvc5 witness: {pair['cvc5']['witness']}")
    if pair["witness_membership"]:
        lines.append("per-witness membership SAT/UNSAT:")
        for token, witness in pair["witness_membership"].items():
            lines.append(
                f"  {token}: z3 A_then_B={witness['z3']['A_then_B']}, "
                f"z3 B_then_A={witness['z3']['B_then_A']}; "
                f"cvc5 A_then_B={witness['cvc5']['A_then_B']}, "
                f"cvc5 B_then_A={witness['cvc5']['B_then_A']}"
            )
    else:
        lines.append("per-witness membership SAT/UNSAT: none; flip-existence is UNSAT in both solvers.")
    return lines


def format_report(report: Mapping[str, object]) -> str:
    lines: List[str] = []
    lines.append("FOUNDATION ORDER-SENSITIVITY SCRATCH DIAGNOSTIC")
    lines.append(f"classification: {report['classification']}")
    lines.append(f"promotion_allowed: {report['promotion_allowed']}")
    lines.append(f"formal_admission_allowed: {report['formal_admission_allowed']}")
    lines.append(f"support: {report['support']}")
    lines.append(f"initial_partition: {report['initial_partition']}")
    semantics = report["semantics"]
    assert isinstance(semantics, dict)
    lines.append("semantics:")
    lines.append(f"  state: {semantics['state']}")
    lines.append(f"  operation: {semantics['operation']}")
    lines.append(f"  flip_query: {semantics['flip_query']}")
    for pair in report["pairs"]:
        lines.append("")
        lines.extend(format_pair(pair))
    lines.append("")
    lines.append(f"anti_tautology_proof: {report['anti_tautology_proof']}")
    lines.append(f"honest_scope: {report['honest_scope']}")
    lines.append(f"all_pass: {report['all_pass']}")
    if "results_file" in report:
        lines.append(f"results_file: {report['results_file']}")
    return "\n".join(lines)


def main() -> int:
    results_path = Path(__file__).resolve().with_name(
        "order_sensitivity_scratch_diagnostic_results.json"
    )
    report = build_report(str(results_path))
    results_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(format_report(report))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
