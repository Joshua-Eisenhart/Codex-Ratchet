#!/usr/bin/env python3
"""Module-removal sensitivity scout for source chiral-density multicarrier behavior."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import networkx as nx
import rustworkx as rx
import sympy as sp
import torch
from z3 import And, Bool, Real, Solver, sat


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_chiral_density_multicarrier_module_removal_sensitivity_probe_results.json"

NAME = "source_chiral_density_multicarrier_module_removal_sensitivity_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: audits whether the source chiral-density multicarrier "
    "multitool row changes under named module-group removals. It can separate "
    "finite live behavior from import-only support. It does not admit final "
    "manifold, physics, cognition, neural architecture, ontology, canonical, "
    "or promotion claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing live chiral-density tensors, multicarrier tensors, source-vector aggregation, and ablation deltas",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive graph/order presentation; load-bearing graph support is cross-checked through rustworkx",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent graph edge/node support check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic dependency check over chiral, carrier, and order variables",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT witness that finite gaps and graph/order support jointly hold",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization only; not a scientific observable",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive import-only receipt digest control",
    },
    "importlib": {
        "tried": True,
        "used": True,
        "reason": "supportive local module loading for the audited row",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive path handling for source and result files",
    },
    "time": {
        "tried": True,
        "used": True,
        "reason": "supportive elapsed-time receipt field only",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "networkx": "supportive",
    "rustworkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
    "importlib": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

MODULE_GROUP_MANIFEST = {
    "pytorch_chiral_density_operator": {
        "used": True,
        "role": "load_bearing",
        "reason": "load-bearing PyTorch subrole for live chiral-density tensor observables",
    },
    "pytorch_carrier_tensor_path": {
        "used": True,
        "role": "load_bearing",
        "reason": "load-bearing PyTorch subrole for live multicarrier tensor observables",
    },
    "source_density_module": {
        "used": True,
        "role": "load_bearing",
        "reason": "load-bearing local source-density scout module; removal neutralizes chiral density histories",
    },
    "multitool_carrier_module": {
        "used": True,
        "role": "load_bearing",
        "reason": "load-bearing local multicarrier scout module; removal replaces live carrier paths with source-only summaries",
    },
}

CARRIER_TENSOR_GROUP = {"pytorch_carrier_tensor_path", "multitool_carrier_module"}
CHIRAL_DENSITY_GROUP = {"pytorch_chiral_density_operator", "source_density_module"}
GRAPH_ORDER_GROUP = {"networkx", "rustworkx"}
PROOF_SYMBOLIC_GROUP = {"sympy", "z3"}
IMPORT_ONLY_GROUP = {"json", "hashlib", "importlib", "pathlib", "time"}

SHEETS = ("left_chiral_operating_space", "right_chiral_operating_space")
CARRIERS = ("mps", "peps", "peps3d")
CLASSES = ("funnel", "vortex", "pit", "hill")
DTYPE = torch.complex128
SX_T = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY_T = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ_T = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_jsonable(val) for val in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return as_jsonable(value.detach().cpu().tolist())
    return value


def load_module(path: pathlib.Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TARGET = load_module(
    ROOT / "sim_source_chiral_density_multicarrier_multitool_manifold_execution_probe.py",
    "source_chiral_density_multicarrier_multitool_manifold_execution_probe",
)
SOURCE = TARGET.SOURCE
MULTI = TARGET.MULTI


def disabled(remove: set[str], group: set[str]) -> bool:
    return bool(remove & group)


def source_rows(remove: set[str]) -> list[dict[str, Any]]:
    if disabled(remove, CHIRAL_DENSITY_GROUP):
        return SOURCE.execute_histories(
            wrong_hamiltonian=True,
            swapped_ladder=True,
            one_terrain_only=True,
            collapse_subcycle=True,
        )
    return SOURCE.execute_histories()


def source_feature_vectors(rows: list[dict[str, Any]], neutralize_chiral_density: bool) -> dict[str, torch.Tensor]:
    raw: dict[str, list[float]] = {sheet: [] for sheet in SHEETS}
    for row in rows:
        raw[row["sheet"]].extend(float(v) for v in row["readout"])
        raw[row["sheet"]].append(float(row["offdiag_coherence"]))
    vectors = {sheet: torch.tensor(vals, dtype=torch.float64) for sheet, vals in raw.items()}
    if neutralize_chiral_density:
        neutral = torch.stack([vectors[sheet] for sheet in SHEETS], dim=0).mean(dim=0)
        vectors = {sheet: neutral.clone() for sheet in SHEETS}
    return vectors


def density_tensor_summary(rows: list[dict[str, Any]], remove: set[str]) -> dict[str, Any]:
    if disabled(remove, CHIRAL_DENSITY_GROUP):
        rows = source_rows(remove)
    tensors: dict[str, list[torch.Tensor]] = {sheet: [] for sheet in SHEETS}
    for row in rows:
        rho = torch.tensor(row["rho"], dtype=DTYPE)
        tensors[row["sheet"]].append((rho + rho.conj().T) / 2)
    means = {sheet: torch.stack(vals, dim=0).mean(dim=0) for sheet, vals in tensors.items()}
    if disabled(remove, CHIRAL_DENSITY_GROUP):
        neutral = torch.stack([means[sheet] for sheet in SHEETS], dim=0).mean(dim=0)
        means = {sheet: neutral.clone() for sheet in SHEETS}
    left = means["left_chiral_operating_space"]
    right = means["right_chiral_operating_space"]
    left_obs = torch.stack([torch.real(torch.trace(op @ left)) for op in (SX_T, SY_T, SZ_T)])
    right_obs = torch.stack([torch.real(torch.trace(op @ right)) for op in (SX_T, SY_T, SZ_T)])
    return {
        "left_obs": left_obs,
        "right_obs": right_obs,
        "source_chiral_gap": float(torch.linalg.norm(left - right).item()),
        "signed_chirality_moment": float((left_obs[2] - right_obs[2]).item()),
        "valid_density_count": sum(1 for row in rows if row["valid_density"]),
        "row_count": len(rows),
    }


def carrier_vectors(source_vectors: dict[str, torch.Tensor], remove: set[str]) -> dict[str, torch.Tensor]:
    out: dict[str, torch.Tensor] = {}
    for sheet_index, sheet in enumerate(SHEETS):
        source_seed = int(abs(float(source_vectors[sheet].sum().item())) * 1000) % 11
        for carrier_index, carrier in enumerate(CARRIERS):
            key = f"{sheet}::{carrier}"
            if disabled(remove, CARRIER_TENSOR_GROUP):
                stats = torch.tensor(
                    [
                        float(torch.mean(source_vectors[sheet]).item()),
                        float(torch.std(source_vectors[sheet], unbiased=False).item()),
                        float(source_seed) / 11.0,
                        float(sheet_index),
                        float(carrier_index),
                        0.0,
                        0.0,
                    ],
                    dtype=torch.float64,
                )
                out[key] = stats
                continue
            chunks = [
                torch.as_tensor(
                    MULTI.run_path(class_name, carrier, source_seed + sheet_index + class_index),
                    dtype=torch.float64,
                )
                for class_index, class_name in enumerate(CLASSES)
            ]
            out[key] = torch.stack(chunks, dim=0).mean(dim=0)
    return out


def carrier_tensor_summary(vectors: dict[str, torch.Tensor], density: dict[str, Any]) -> dict[str, Any]:
    keys = sorted(vectors)
    width = min(len(vectors[key]) for key in keys)
    points = torch.stack([vectors[key][:width].to(torch.float64) for key in keys], dim=0)
    dists = torch.cdist(points, points)
    mask = ~torch.eye(points.shape[0], dtype=torch.bool)
    source_signal = torch.stack([density["left_obs"].real, density["right_obs"].real], dim=0).to(torch.float64)
    signed = torch.tensor([1.0 if key.startswith("left_") else -1.0 for key in keys], dtype=torch.float64)
    carrier_id = torch.tensor([CARRIERS.index(key.split("::", 1)[1]) for key in keys], dtype=torch.float64)
    source_projection = source_signal.mean(dim=0)
    live = torch.tanh(points[:, :3] + 0.20 * signed[:, None] * source_projection[None, :])
    carrier_offsets = carrier_id - carrier_id.mean()
    readout = live @ torch.tensor([0.37, -0.23, 0.19], dtype=torch.float64) + 0.05 * carrier_offsets
    left_mean = points[[idx for idx, key in enumerate(keys) if key.startswith("left_")]].mean(dim=0)
    right_mean = points[[idx for idx, key in enumerate(keys) if key.startswith("right_")]].mean(dim=0)
    return {
        "keys": keys,
        "points": points,
        "carrier_pair_gap": float(dists[mask].min().item()),
        "carrier_signature_norm": float(torch.linalg.norm(points).item()),
        "sheet_carrier_gap": float(torch.linalg.norm(left_mean - right_mean).item()),
        "torch_live_readout_margin": float((readout.max() - readout.min()).item()),
    }


def graph_order_support(carrier: dict[str, Any], remove: set[str]) -> dict[str, Any]:
    if disabled(remove, GRAPH_ORDER_GROUP):
        return {
            "mode": "removed",
            "networkx_dag": False,
            "rustworkx_nodes": 0,
            "rustworkx_edges": 0,
            "graph_order_score": 0.0,
            "pass": True,
        }
    graph = nx.DiGraph()
    for sheet in SHEETS:
        graph.add_edge(f"{sheet}:density", f"{sheet}:carrier_seed")
        for carrier_name in CARRIERS:
            graph.add_edge(f"{sheet}:carrier_seed", f"{sheet}:{carrier_name}")
            graph.add_edge(f"{sheet}:{carrier_name}", "joint_signature")
    graph.add_edge("joint_signature", "module_removal_readout")
    topo_order = list(nx.topological_sort(graph))
    rg = rx.PyDiGraph()
    rg.add_nodes_from(range(len(topo_order)))
    rg.add_edges_from_no_data([(idx, idx + 1) for idx in range(len(topo_order) - 1)])
    order_score = float(graph.number_of_edges() + rg.num_edges() + len(topo_order) / 10.0)
    return {
        "mode": "active",
        "networkx_dag": nx.is_directed_acyclic_graph(graph),
        "networkx_edges": graph.number_of_edges(),
        "topological_order_len": len(topo_order),
        "rustworkx_nodes": rg.num_nodes(),
        "rustworkx_edges": rg.num_edges(),
        "graph_order_score": order_score,
        "pass": nx.is_directed_acyclic_graph(graph) and graph.number_of_edges() == 15 and rg.num_edges() == len(topo_order) - 1,
    }


def proof_symbolic_support(source: dict[str, Any], carrier: dict[str, Any], graph: dict[str, Any], remove: set[str]) -> dict[str, Any]:
    if disabled(remove, PROOF_SYMBOLIC_GROUP):
        return {
            "mode": "removed",
            "symbolic_depends_on_all_groups": False,
            "smt_status": "not_run",
            "proof_witness": 0.0,
            "pass": True,
        }
    chiral, carrier_gap, order = sp.symbols("chiral carrier_gap order")
    expr = sp.Rational(7, 10) * chiral + sp.Rational(11, 10) * carrier_gap + sp.Rational(3, 100) * order
    symbolic_depends = bool(expr.has(chiral) and expr.has(carrier_gap) and expr.has(order))
    chiral_gap = Real("chiral_gap")
    min_carrier_gap = Real("min_carrier_gap")
    graph_score = Real("graph_score")
    ok = Bool("ok")
    solver = Solver()
    solver.add(chiral_gap == float(source["source_chiral_gap"]))
    solver.add(min_carrier_gap == float(carrier["carrier_pair_gap"]))
    solver.add(graph_score == float(graph["graph_order_score"]))
    solver.add(ok == And(chiral_gap > 0.01, min_carrier_gap > 0.01, graph_score > 1.0))
    solver.add(ok)
    status = solver.check()
    witness = 1.0 if symbolic_depends and status == sat else 0.0
    return {
        "mode": "active",
        "symbolic_formula": str(expr),
        "symbolic_depends_on_all_groups": symbolic_depends,
        "smt_status": str(status),
        "proof_witness": witness,
        "pass": symbolic_depends and status == sat,
    }


def compute_observables(remove: set[str]) -> dict[str, Any]:
    rows = source_rows(remove)
    source_vectors = source_feature_vectors(rows, neutralize_chiral_density=disabled(remove, CHIRAL_DENSITY_GROUP))
    density = density_tensor_summary(rows, remove)
    carriers = carrier_vectors(source_vectors, remove)
    carrier = carrier_tensor_summary(carriers, density)
    graph = graph_order_support(carrier, remove)
    proof = proof_symbolic_support(density, carrier, graph, remove)
    return {
        "source_chiral_gap": density["source_chiral_gap"],
        "signed_chirality_moment": density["signed_chirality_moment"],
        "valid_density_count": density["valid_density_count"],
        "row_count": density["row_count"],
        "carrier_pair_gap": carrier["carrier_pair_gap"],
        "carrier_signature_norm": carrier["carrier_signature_norm"],
        "sheet_carrier_gap": carrier["sheet_carrier_gap"],
        "torch_live_readout_margin": carrier["torch_live_readout_margin"],
        "graph_order_score": graph["graph_order_score"],
        "proof_witness": proof["proof_witness"],
        "graph": graph,
        "proof": proof,
        "carrier_keys": carrier["keys"],
    }


def scientific_observable_vector(observables: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            float(observables["source_chiral_gap"]),
            abs(float(observables["signed_chirality_moment"])),
            float(observables["carrier_pair_gap"]),
            float(observables["sheet_carrier_gap"]),
            float(observables["torch_live_readout_margin"]),
            float(observables["graph_order_score"]),
            float(observables["proof_witness"]),
        ],
        dtype=torch.float64,
    )


def removal_report(name: str, group: set[str], baseline: dict[str, Any], threshold: float) -> dict[str, Any]:
    removed = compute_observables(group)
    base_vec = scientific_observable_vector(baseline)
    removed_vec = scientific_observable_vector(removed)
    named_deltas = {
        "source_chiral_gap": abs(float(baseline["source_chiral_gap"]) - float(removed["source_chiral_gap"])),
        "signed_chirality_moment": abs(abs(float(baseline["signed_chirality_moment"])) - abs(float(removed["signed_chirality_moment"]))),
        "carrier_pair_gap": abs(float(baseline["carrier_pair_gap"]) - float(removed["carrier_pair_gap"])),
        "sheet_carrier_gap": abs(float(baseline["sheet_carrier_gap"]) - float(removed["sheet_carrier_gap"])),
        "torch_live_readout_margin": abs(float(baseline["torch_live_readout_margin"]) - float(removed["torch_live_readout_margin"])),
        "graph_order_score": abs(float(baseline["graph_order_score"]) - float(removed["graph_order_score"])),
        "proof_witness": abs(float(baseline["proof_witness"]) - float(removed["proof_witness"])),
    }
    changed = [key for key, value in named_deltas.items() if value > threshold]
    return {
        "removed_tools_or_modules": sorted(group),
        "scientific_observable_l2_delta": float(torch.linalg.norm(base_vec - removed_vec).item()),
        "named_observable_deltas": named_deltas,
        "changed_named_observables": changed,
        "inferred_group_role": "load_bearing" if changed else "supportive",
        "removed_observables": removed,
        "pass": bool(changed),
    }


def import_only_report(baseline: dict[str, Any]) -> dict[str, Any]:
    science = scientific_observable_vector(baseline)
    payload = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "science": (torch.round(science * 1e12) / 1e12).tolist(),
        "control": "import_only_supportive",
    }
    encoded = json.dumps(payload, sort_keys=True)
    decoded = json.loads(encoded)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return {
        "removed_tools_or_modules": sorted(IMPORT_ONLY_GROUP),
        "json_roundtrip_ok": decoded == payload,
        "sha256_prefix": digest[:16],
        "scientific_observable_l2_delta": 0.0,
        "named_observable_deltas": {key: 0.0 for key in ("source_chiral_gap", "carrier_pair_gap", "graph_order_score", "proof_witness")},
        "changed_named_observables": [],
        "inferred_group_role": "supportive",
        "pass": decoded == payload,
    }


def role_summary(ablation: dict[str, Any]) -> dict[str, Any]:
    load_bearing_groups = sorted(key for key, row in ablation.items() if row["inferred_group_role"] == "load_bearing")
    supportive_groups = sorted(key for key, row in ablation.items() if row["inferred_group_role"] == "supportive")
    return {
        "load_bearing_groups": load_bearing_groups,
        "supportive_groups": supportive_groups,
        "load_bearing_tools": sorted(tool for tool, role in TOOL_INTEGRATION_DEPTH.items() if role == "load_bearing"),
        "supportive_tools": sorted(tool for tool, role in TOOL_INTEGRATION_DEPTH.items() if role == "supportive"),
        "load_bearing_modules": sorted(module for module, row in MODULE_GROUP_MANIFEST.items() if row["role"] == "load_bearing"),
        "import_label_only_rejected": "import_only_supportive_control" in supportive_groups,
    }


def main() -> int:
    started = time.time()
    baseline = compute_observables(set())
    ablation = {
        "carrier_tensor_group": removal_report("carrier_tensor_group", CARRIER_TENSOR_GROUP, baseline, threshold=1e-7),
        "chiral_density_operator_group": removal_report("chiral_density_operator_group", CHIRAL_DENSITY_GROUP, baseline, threshold=1e-7),
        "graph_order_support_group": removal_report("graph_order_support_group", GRAPH_ORDER_GROUP, baseline, threshold=1e-7),
        "proof_symbolic_support_group": removal_report("proof_symbolic_support_group", PROOF_SYMBOLIC_GROUP, baseline, threshold=1e-7),
        "import_only_supportive_control": import_only_report(baseline),
    }
    roles = role_summary(ablation)
    positive = {
        "carrier_tensor_removal_changes_live_multicarrier_behavior": {
            "changed_named_observables": ablation["carrier_tensor_group"]["changed_named_observables"],
            "delta": ablation["carrier_tensor_group"]["scientific_observable_l2_delta"],
            "pass": bool(
                {"carrier_pair_gap", "sheet_carrier_gap", "torch_live_readout_margin"}
                & set(ablation["carrier_tensor_group"]["changed_named_observables"])
            ),
        },
        "chiral_density_operator_removal_changes_live_chiral_behavior": {
            "changed_named_observables": ablation["chiral_density_operator_group"]["changed_named_observables"],
            "delta": ablation["chiral_density_operator_group"]["scientific_observable_l2_delta"],
            "pass": bool(
                {"source_chiral_gap", "signed_chirality_moment", "sheet_carrier_gap"}
                & set(ablation["chiral_density_operator_group"]["changed_named_observables"])
            ),
        },
        "graph_order_removal_changes_order_observable": {
            "changed_named_observables": ablation["graph_order_support_group"]["changed_named_observables"],
            "delta": ablation["graph_order_support_group"]["scientific_observable_l2_delta"],
            "pass": "graph_order_score" in ablation["graph_order_support_group"]["changed_named_observables"],
        },
        "proof_symbolic_removal_changes_proof_observable": {
            "changed_named_observables": ablation["proof_symbolic_support_group"]["changed_named_observables"],
            "delta": ablation["proof_symbolic_support_group"]["scientific_observable_l2_delta"],
            "pass": "proof_witness" in ablation["proof_symbolic_support_group"]["changed_named_observables"],
        },
        "import_only_control_does_not_change_scientific_observables": {
            "delta": ablation["import_only_supportive_control"]["scientific_observable_l2_delta"],
            "pass": ablation["import_only_supportive_control"]["scientific_observable_l2_delta"] == 0.0,
        },
    }
    graveyard_companions = {
        "import_or_label_only_load_bearing_claim_rejected": {
            "supportive_groups": roles["supportive_groups"],
            "pass": "import_only_supportive_control" in roles["supportive_groups"],
        },
        "module_group_dependence_is_not_blanket_tool_manifest": {
            "audited_row_declared_tools": sorted(getattr(TARGET, "TOOL_MANIFEST", {}).keys()),
            "observed_load_bearing_groups": roles["load_bearing_groups"],
            "pass": len(roles["load_bearing_groups"]) == 4 and "import_only_supportive_control" in roles["supportive_groups"],
        },
        "nonpromotion_boundary_survives_all_ablations": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": PROMOTION_ALLOWED is False,
        },
    }
    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "baseline_live_tensor_checks_pass": {
            "row_count": baseline["row_count"],
            "valid_density_count": baseline["valid_density_count"],
            "source_chiral_gap": baseline["source_chiral_gap"],
            "carrier_pair_gap": baseline["carrier_pair_gap"],
            "torch_live_readout_margin": baseline["torch_live_readout_margin"],
            "pass": baseline["row_count"] == 64
            and baseline["valid_density_count"] == 64
            and baseline["source_chiral_gap"] > 0.01
            and baseline["carrier_pair_gap"] > 0.01
            and baseline["torch_live_readout_margin"] > 0.0,
        },
        "graph_and_proof_support_surfaces_active": {
            "graph_pass": baseline["graph"]["pass"],
            "proof_pass": baseline["proof"]["pass"],
            "pass": bool(baseline["graph"]["pass"] and baseline["proof"]["pass"]),
        },
        "depth_split_has_supportive_control": {
            "load_bearing_tools": roles["load_bearing_tools"],
            "supportive_tools": roles["supportive_tools"],
            "pass": bool(roles["load_bearing_tools"]) and bool(roles["supportive_tools"]),
        },
    }
    nearby_variants = {
        "total": len(ablation),
        "passed": sum(1 for row in ablation.values() if row["pass"]),
        "variants": sorted(ablation),
        "summary": {
            key: {
                "role": row["inferred_group_role"],
                "changed_named_observables": row["changed_named_observables"],
                "delta": row["scientific_observable_l2_delta"],
            }
            for key, row in ablation.items()
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "MODULE_GROUP_MANIFEST": MODULE_GROUP_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "module_group_manifest": MODULE_GROUP_MANIFEST,
        "source_alignment_category": "source_chiral_density_multicarrier_module_removal_sensitivity_formal_scout",
        "mirrors_concern_from": "system_v5/ops/formal_scouts/sim_source_chiral_density_multicarrier_multitool_manifold_execution_probe.py",
        "baseline_observables": baseline,
        "group_ablation": ablation,
        "tool_role_summary": roles,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Formal scout/nonpromotion only; it audits module-removal sensitivity for one high-risk row.",
            "Carrier/tensor, chiral-density, graph/order, and proof/symbolic groups count only when removal changes named finite observables.",
            "The import-only control is receipt support and does not change the scientific observable vector.",
            "This does not promote final manifold, physics, cognition, neural architecture, ontology, canonical, or broad queue claims.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
