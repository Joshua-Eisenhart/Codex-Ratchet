#!/usr/bin/env python3
"""PyTorch graph leg for packet-local Z4 syndrome records."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3


SIM_ID = "z4_syndrome_record_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = PACKET / "results" / f"{SIM_ID}_pytorch_results.json"
SOURCE = PACKET / f"{SIM_ID}_pytorch.py"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
LN2 = math.log(2.0)

BASE_STATES = ["z_plus", "z_minus", "x_plus", "x_minus", "y_plus", "y_minus"]
PHASES = [0, 1, 2, 3]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "version_unavailable"


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def build_table() -> list[dict[str, Any]]:
    rows = []
    for orbit_index, orbit_id in enumerate(BASE_STATES):
        for syndrome in PHASES:
            rows.append(
                {
                    "representative_id": f"{orbit_id}::phase_{syndrome}",
                    "orbit_id": orbit_id,
                    "orbit_index": orbit_index,
                    "quotient_output": f"orbit::{orbit_id}",
                    "syndrome": syndrome,
                    "syndrome_bits": format(syndrome, "02b"),
                    "representative_code": orbit_index * 4 + syndrome,
                }
            )
    return rows


def entropy_from_counts(counts: list[int]) -> dict[str, Any]:
    total = sum(counts)
    probs = [sp.Rational(count, total) for count in counts if count]
    entropy = sp.simplify(-sum(p * sp.log(p) for p in probs))
    value = float(sp.N(entropy, 30))
    return {
        "entropy_type": "finite_counting_entropy_nats",
        "log_base": "e",
        "counts": counts,
        "entropy_exact": str(entropy),
        "entropy_nats": value,
        "entropy_log2_coefficient": int(round(value / LN2)),
        "code_path_id": "torch_counts_to_sympy_shannon_entropy",
    }


def graph_preimage_loss(rows: list[dict[str, Any]], identity: bool = False) -> dict[str, Any]:
    quotient_count = len(rows) if identity else len(BASE_STATES)
    representative_count = len(rows)
    if identity:
        src = torch.arange(representative_count, dtype=torch.long)
        dst = torch.arange(representative_count, dtype=torch.long)
    else:
        src = torch.tensor([row["orbit_index"] for row in rows], dtype=torch.long)
        dst = torch.arange(representative_count, dtype=torch.long)
    edge_index = torch.stack([src, dst], dim=0)
    graph = Data(edge_index=edge_index, num_nodes=quotient_count + representative_count)
    counts_tensor = torch.bincount(graph.edge_index[0], minlength=quotient_count)
    counts = [int(x) for x in counts_tensor.tolist() if int(x) > 0]
    total = sum(counts)
    loss = sp.simplify(sum(sp.Rational(count, total) * sp.log(count) for count in counts))
    value = float(sp.N(loss, 30))
    groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        key = row["representative_id"] if identity else row["quotient_output"]
        groups[key].append(row["representative_id"])
    return {
        "entropy_type": "finite_counting_entropy_nats",
        "log_base": "e",
        "preimage_counts": sorted(counts),
        "state_loss_exact": str(loss),
        "state_loss_without_record_nats": value,
        "state_loss_log2_coefficient": int(round(value / LN2)),
        "code_path_id": "torch_geometric_incidence_graph_indegree_to_average_log_fiber_size",
        "graph_receipt": {
            "num_edges": int(graph.edge_index.shape[1]),
            "num_quotient_nodes": quotient_count,
            "num_representative_nodes": representative_count,
        },
        "preimage_table": {group: sorted(ids) for group, ids in sorted(groups.items())},
    }


def reconstruct_codes(rows: list[dict[str, Any]], shift: int = 0) -> dict[str, Any]:
    orbit = torch.tensor([row["orbit_index"] for row in rows], dtype=torch.long)
    syndrome = torch.tensor([row["syndrome"] for row in rows], dtype=torch.long)
    expected = torch.tensor([row["representative_code"] for row in rows], dtype=torch.long)

    def roundtrip(pair: torch.Tensor) -> torch.Tensor:
        return pair[0] * 4 + ((pair[1] + shift) % 4)

    pairs = torch.stack([orbit, syndrome], dim=1)
    recovered = vmap(roundtrip)(pairs)
    failures = recovered != expected
    return {
        "syndrome_shift": shift,
        "checked_count": int(expected.numel()),
        "failure_count": int(torch.sum(failures).item()),
        "failure_rate": float(torch.mean(failures.to(torch.float64)).item()),
        "bit_exact_roundtrip": bool(not torch.any(failures).item()),
        "recovered_code_sample": [int(x) for x in recovered[:8].tolist()],
    }


def quotient_alone(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["quotient_output"] for row in rows)
    ambiguity = max(counts.values())
    return {
        "computed_ambiguity": int(ambiguity),
        "unique_reconstruction_possible": ambiguity == 1,
        "reconstruction_fails": ambiguity > 1,
        "ambiguities": sorted(int(v) for v in counts.values()),
    }


def conservation_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    full_loss = graph_preimage_loss(rows)
    full_record = entropy_from_counts(list(Counter(row["syndrome"] for row in rows).values()))
    erased_record = entropy_from_counts([len(rows)])
    partial_record = entropy_from_counts(list(Counter(row["syndrome"] % 2 for row in rows).values()))
    trivial_loss = graph_preimage_loss(rows, identity=True)
    trivial_record = entropy_from_counts([len(rows)])

    def row(name: str, loss: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
        defect = loss["state_loss_without_record_nats"] - record["entropy_nats"]
        out = {
            "regime": name,
            "state_loss_without_record_nats": loss["state_loss_without_record_nats"],
            "record_retained_nats": record["entropy_nats"],
            "computed_defect_nats": defect,
            "state_loss_log2_coefficient": loss["state_loss_log2_coefficient"],
            "record_log2_coefficient": record["entropy_log2_coefficient"],
            "defect_log2_coefficient": int(round(defect / LN2)),
            "typed_entropy_label": "finite_counting_entropy_nats",
            "loss_code_path_id": loss["code_path_id"],
            "record_code_path_id": record["code_path_id"],
            "different_code_paths": loss["code_path_id"] != record["code_path_id"],
        }
        out["row_hash"] = stable_hash(
            {
                "regime": name,
                "loss": out["state_loss_log2_coefficient"],
                "record": out["record_log2_coefficient"],
                "defect": out["defect_log2_coefficient"],
            }
        )
        return out

    return {
        "positive": row("full_record", full_loss, full_record),
        "negative_erased_record": row("erased_record", full_loss, erased_record),
        "negative_partial_record": row("partial_record_one_bit", full_loss, partial_record),
        "boundary_trivial_quotient": row("trivial_quotient", trivial_loss, trivial_record),
        "source_rows": {
            "full_loss": full_loss,
            "full_record": full_record,
            "erased_record": erased_record,
            "partial_record": partial_record,
            "trivial_loss": trivial_loss,
            "trivial_record": trivial_record,
        },
    }


def z3_proofs(regimes: dict[str, Any]) -> dict[str, Any]:
    def prove(row: dict[str, Any]) -> dict[str, Any]:
        solver = z3.Solver()
        loss = z3.Int("loss")
        record = z3.Int("record")
        solver.add(loss == z3.IntVal(int(row["state_loss_log2_coefficient"])))
        solver.add(record == z3.IntVal(int(row["record_log2_coefficient"])))
        solver.add(loss != record)
        return {
            "solver": "z3",
            "ran": True,
            "load_bearing": True,
            "verdict": str(solver.check()),
            "bound_values": {
                "loss_log2_coefficient": row["state_loss_log2_coefficient"],
                "record_log2_coefficient": row["record_log2_coefficient"],
                "defect_log2_coefficient": row["defect_log2_coefficient"],
            },
        }

    return {
        "full_record": prove(regimes["positive"]),
        "erased_record_control": prove(regimes["negative_erased_record"]),
        "partial_record_control": prove(regimes["negative_partial_record"]),
        "trivial_quotient_boundary": prove(regimes["boundary_trivial_quotient"]),
    }


def cvc5_proofs(regimes: dict[str, Any]) -> dict[str, Any]:
    def prove(row: dict[str, Any]) -> dict[str, Any]:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        loss = solver.mkConst(int_sort, "loss")
        record = solver.mkConst(int_sort, "record")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, loss, solver.mkInteger(int(row["state_loss_log2_coefficient"]))))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, record, solver.mkInteger(int(row["record_log2_coefficient"]))))
        solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, loss, record)))
        result = solver.checkSat()
        return {
            "solver": "cvc5",
            "ran": True,
            "load_bearing": True,
            "verdict": "sat" if result.isSat() else "unsat" if result.isUnsat() else "unknown",
            "bound_values": {
                "loss_log2_coefficient": row["state_loss_log2_coefficient"],
                "record_log2_coefficient": row["record_log2_coefficient"],
                "defect_log2_coefficient": row["defect_log2_coefficient"],
            },
        }

    return {
        "full_record": prove(regimes["positive"]),
        "erased_record_control": prove(regimes["negative_erased_record"]),
        "partial_record_control": prove(regimes["negative_partial_record"]),
        "trivial_quotient_boundary": prove(regimes["boundary_trivial_quotient"]),
    }


def main() -> int:
    rows = build_table()
    regimes = conservation_rows(rows)
    z3_rows = z3_proofs(regimes)
    cvc5_rows = cvc5_proofs(regimes)
    controls = {
        "erased_record": regimes["negative_erased_record"],
        "partial_record_one_bit": regimes["negative_partial_record"],
        "shuffled_syndrome": reconstruct_codes(rows, shift=1),
        "trivial_quotient": regimes["boundary_trivial_quotient"],
    }
    all_pass = all(
        [
            regimes["positive"]["defect_log2_coefficient"] == 0,
            regimes["negative_erased_record"]["defect_log2_coefficient"] == 2,
            regimes["negative_partial_record"]["defect_log2_coefficient"] == 1,
            regimes["boundary_trivial_quotient"]["state_loss_log2_coefficient"] == 0,
            reconstruct_codes(rows)["bit_exact_roundtrip"],
            quotient_alone(rows)["computed_ambiguity"] == 4,
            controls["shuffled_syndrome"]["failure_rate"] == 1.0,
            len(
                {
                    regimes["positive"]["row_hash"],
                    regimes["negative_erased_record"]["row_hash"],
                    regimes["negative_partial_record"]["row_hash"],
                    regimes["boundary_trivial_quotient"]["row_hash"],
                }
            )
            == 4,
            z3_rows["full_record"]["verdict"] == "unsat",
            cvc5_rows["full_record"]["verdict"] == "unsat",
            z3_rows["erased_record_control"]["verdict"] == "sat",
            cvc5_rows["erased_record_control"]["verdict"] == "sat",
            z3_rows["partial_record_control"]["verdict"] == "sat",
            cvc5_rows["partial_record_control"]["verdict"] == "sat",
        ]
    )
    payload = {
        "schema_version": f"{SIM_ID}_pytorch_leg_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "engine": "pytorch",
        "role_id": "pytorch_graph_z4_syndrome_record_leg",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": rel(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "result_path": rel(RESULT),
        "reads_peer_result": False,
        "packages_used": ["torch", "torch_geometric", "torch.func", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["torch_geometric", "torch.func", "sympy", "z3", "cvc5"],
        "package_observables": {
            "torch_geometric": "Data.edge_index quotient-to-representative incidence graph; source-node counts compute preimage cardinalities",
            "torch.func": "vmap roundtrip reconstruction over all representative codes",
            "sympy": "sp.log/sp.Rational exact finite counting entropy rows from torch-derived counts",
            "z3": "z3.Solver over torch-derived log2 coefficients",
            "cvc5": "cvc5.Solver over torch-derived log2 coefficients",
        },
        "package_versions": {
            "torch": package_version("torch"),
            "torch-geometric": package_version("torch-geometric"),
            "sympy": package_version("sympy"),
            "z3-solver": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
        },
        "claim_path_tools": ["torch_geometric", "torch.func", "sympy", "z3", "cvc5"],
        "syndrome_table": rows,
        "regimes": regimes,
        "controls": controls,
        "reconstruction": {
            "with_quotient_and_syndrome": reconstruct_codes(rows),
            "quotient_alone": quotient_alone(rows),
        },
        "crossover_proofs": {"z3": z3_rows, "cvc5": cvc5_rows},
        "TOOL_MANIFEST": {
            "torch_geometric": {"used": True, "reason": "load-bearing graph incidence route for preimage counts"},
            "torch.func": {"used": True, "reason": "load-bearing vectorized reconstruction check"},
            "sympy": {"used": True, "reason": "load-bearing exact finite counting entropy rows"},
            "z3": {"used": True, "reason": "load-bearing SMT controls"},
            "cvc5": {"used": True, "reason": "independent load-bearing SMT controls"},
            "torch": {"used": True, "reason": "supportive tensor storage for graph and reconstruction lane"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch_geometric": "load_bearing",
            "torch.func": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "torch": "supportive",
        },
        "tool_calls": [
            {
                "tool": "torch_geometric",
                "qualified_api/function": "torch_geometric.data.Data",
                "input_object": "quotient-to-representative edge_index",
                "output_object": "preimage counts and ambiguity 4",
                "positive_case": "Z4 quotient has six quotient nodes each with four representatives",
                "negative/erased_control": "erased and partial record regimes use same graph loss with reduced record entropy",
                "boundary_case": "identity quotient graph has all preimage counts 1",
                "demotion_condition": "demote if graph incidence is replaced by literal count",
                "gates": ["state_loss_without_record", "all_pass"],
            },
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.vmap",
                "input_object": "orbit/syndrome representative code tensor",
                "output_object": "roundtrip reconstruction and shuffled-syndrome failure rate",
                "positive_case": "identity syndrome reconstructs all representatives",
                "negative/erased_control": "shifted syndrome fails all representatives",
                "boundary_case": "quotient-alone ambiguity remains 4",
                "demotion_condition": "demote if reconstruction is not evaluated over the table",
                "gates": ["reconstruction", "all_pass"],
            },
        ],
        "all_pass": all_pass,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": rel(RESULT)}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

