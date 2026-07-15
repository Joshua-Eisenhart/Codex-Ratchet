#!/usr/bin/env python3
"""Independent PyTorch/PyG graph lane for the first tolerance/equivalence rung."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import torch
import torch_geometric
from torch_geometric.nn import MessagePassing


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "pytorch": {
        "used": True,
        "reason": "PyTorch tensors execute the exhaustive relation and closure calculations.",
    },
    "pyg": {
        "used": True,
        "reason": "PyG MessagePassing executes the independent reachability closure lane.",
    },
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "pyg": "load_bearing"}

SIM_DIR = Path(__file__).resolve().parent
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = SIM_DIR / "results" / "pytorch_results.json"
EXPECTED = {
    "1": {"tolerances": 1, "equivalences": 1, "nontransitive": 0},
    "2": {"tolerances": 2, "equivalences": 2, "nontransitive": 0},
    "3": {"tolerances": 8, "equivalences": 5, "nontransitive": 3},
    "4": {"tolerances": 64, "equivalences": 15, "nontransitive": 49},
    "5": {"tolerances": 1024, "equivalences": 52, "nontransitive": 972},
}


class Reachability(MessagePassing):
    def __init__(self) -> None:
        super().__init__(aggr="max")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        propagated = self.propagate(edge_index, x=x)
        return torch.maximum(x, propagated)

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return x_j


def relation_from_edges(n: int, edges: list[list[int]]) -> torch.Tensor:
    relation = torch.eye(n, dtype=torch.bool)
    for i, j in edges:
        relation[i, j] = True
        relation[j, i] = True
    return relation


def relation_from_mask(n: int, mask: int) -> torch.Tensor:
    relation = torch.eye(n, dtype=torch.bool)
    bit = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            value = bool((mask >> bit) & 1)
            relation[i, j] = value
            relation[j, i] = value
            bit += 1
    return relation


def is_transitive(relation: torch.Tensor) -> bool:
    two_step = torch.matmul(relation.to(torch.int16), relation.to(torch.int16)) > 0
    return not bool(torch.any(two_step & ~relation))


def pyg_closure(relation: torch.Tensor) -> torch.Tensor:
    edge_index = relation.nonzero(as_tuple=False).t().contiguous()
    x = torch.eye(relation.shape[0], dtype=torch.float64)
    layer = Reachability()
    for _ in range(relation.shape[0]):
        x = layer(x, edge_index)
    return x > 0.5


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
    equivalences = sum(is_transitive(relation_from_mask(n, mask)) for mask in range(total))
    return {"tolerances": total, "equivalences": equivalences, "nontransitive": total - equivalences}


def relation_contains(candidate: torch.Tensor, raw: torch.Tensor) -> bool:
    return bool(torch.all(~raw | candidate))


def mss_antichain(raw: torch.Tensor) -> list[dict[str, object]]:
    n = raw.shape[0]
    candidates: list[dict[str, object]] = []
    for mask in range(1 << (n * (n - 1) // 2)):
        candidate = relation_from_mask(n, mask)
        if is_transitive(candidate) and relation_contains(candidate, raw):
            matrix = [[bool(x) for x in row] for row in candidate.tolist()]
            labels = normalized_labels(matrix)
            added = sum(bool(candidate[i, j] and not raw[i, j]) for i in range(n) for j in range(i + 1, n))
            candidates.append(
                {"labels": labels, "added_pair_count": added, "quotient_class_count": len(set(labels))}
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
    closed = pyg_closure(raw)
    matrix = [[bool(x) for x in row] for row in closed.tolist()]
    proposal = normalized_labels(matrix)
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
        "raw_closure": matrix,
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
    chain_closed = pyg_closure(chain)
    chain_matrix = [[bool(x) for x in row] for row in chain_closed.tolist()]
    chain_labels = normalized_labels(chain_matrix)
    drive = drive_record()
    controls = drive["controls"]
    all_pass = bool(
        observed == EXPECTED
        and not is_transitive(chain)
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
        "engine": "pytorch",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "reads_peer_result": False,
        "source_path": str(SOURCE_PATH.relative_to(SIM_DIR.parents[2])),
        "source_sha256": hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest(),
        "runtime": {"torch_version": torch.__version__, "torch_geometric_version": torch_geometric.__version__},
        "packages_used": ["torch", "torch_geometric"],
        "aligned_packages_load_bearing": ["torch", "torch.matmul", "torch_geometric.nn.MessagePassing"],
        "census": observed,
        "transitivity_witness": {
            "raw_transitive": is_transitive(chain),
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
    print(f"PYTORCH_TOLERANCE_RUNG_DONE all_pass={str(all_pass).lower()} drive={drive['drive']} mss={len(drive['mss_antichain'])}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
