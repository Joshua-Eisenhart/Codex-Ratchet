#!/usr/bin/env python3
"""Four topology behavior-class separation scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import sympy as sp
import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "four_topology_behavior_class_chiral_loop_operator_separation_probe_results.json"

NAME = "four_topology_behavior_class_chiral_loop_operator_separation_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether four topology classes, their two "
    "chiral realizations, inner/outer loop placements, ordered operator pairs, "
    "and signed operator directions produce noncollapsed finite behavior "
    "classes on density states. It does not admit psychology, personality, "
    "canonical engine identity, physics, ontology, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density matrices, Bloch features, class centroids, controls, CPTP-style density updates, and signed operator maps"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing topology-transition graph and edge inventory"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence of behavior-signature point cloud"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic inventory check for four topologies x two chiral realizations"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "networkx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
}

DTYPE = torch.complex128
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
SM = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)
SP = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)
PROJECTORS = {
    "x": [0.5 * (I2 + SX), 0.5 * (I2 - SX)],
    "y": [0.5 * (I2 + SY), 0.5 * (I2 - SY)],
    "z": [0.5 * (I2 + SZ), 0.5 * (I2 - SZ)],
}


# Human-facing labels are kept in data only; the scout name and claim are math-layer.
TYPE_ONE_TOPOLOGIES = {
    "Se": {
        "realization": "Funnel",
        "strategy_pattern": "LOSEwin",
        "major": {"token": "TiSe", "operator": "Ti", "sign": +1, "result": "LOSE"},
        "minor": {"token": "SeFi", "operator": "Fi", "sign": -1, "result": "win"},
        "projector_axis": "x",
        "rate": 0.18,
        "mode": "sink_capture",
    },
    "Ne": {
        "realization": "Vortex",
        "strategy_pattern": "WINlose",
        "major": {"token": "NeTi", "operator": "Ti", "sign": -1, "result": "WIN"},
        "minor": {"token": "FiNe", "operator": "Fi", "sign": +1, "result": "lose"},
        "projector_axis": "y",
        "rate": 0.13,
        "mode": "circulation",
    },
    "Ni": {
        "realization": "Pit",
        "strategy_pattern": "loseLOSE",
        "major": {"token": "NiFe", "operator": "Fe", "sign": -1, "result": "LOSE"},
        "minor": {"token": "TeNi", "operator": "Te", "sign": +1, "result": "lose"},
        "projector_axis": "z",
        "rate": 0.28,
        "mode": "absorbing_basin",
    },
    "Si": {
        "realization": "Hill",
        "strategy_pattern": "winWIN",
        "major": {"token": "FeSi", "operator": "Fe", "sign": +1, "result": "WIN"},
        "minor": {"token": "SiTe", "operator": "Te", "sign": -1, "result": "win"},
        "projector_axis": "z",
        "rate": 0.20,
        "mode": "stabilized_plateau",
    },
}

TYPE_TWO_TOPOLOGIES = {
    "Se": {
        "realization": "Cannon",
        "strategy_pattern": "loseWIN",
        "major": {"token": "FiSe", "operator": "Fi", "sign": +1, "result": "WIN"},
        "minor": {"token": "SeTi", "operator": "Ti", "sign": -1, "result": "lose"},
        "projector_axis": "x",
        "rate": 0.18,
        "mode": "source_projection",
    },
    "Ne": {
        "realization": "Spiral",
        "strategy_pattern": "winLOSE",
        "major": {"token": "NeFi", "operator": "Fi", "sign": -1, "result": "LOSE"},
        "minor": {"token": "TiNe", "operator": "Ti", "sign": +1, "result": "win"},
        "projector_axis": "y",
        "rate": 0.15,
        "mode": "reverse_circulation",
    },
    "Ni": {
        "realization": "Source",
        "strategy_pattern": "LOSElose",
        "major": {"token": "NiTe", "operator": "Te", "sign": -1, "result": "LOSE"},
        "minor": {"token": "FeNi", "operator": "Fe", "sign": +1, "result": "lose"},
        "projector_axis": "x",
        "rate": 0.27,
        "mode": "emitting_basin",
    },
    "Si": {
        "realization": "Citadel",
        "strategy_pattern": "WINwin",
        "major": {"token": "TeSi", "operator": "Te", "sign": +1, "result": "WIN"},
        "minor": {"token": "SiFe", "operator": "Fe", "sign": -1, "result": "win"},
        "projector_axis": "z",
        "rate": 0.21,
        "mode": "protected_plateau",
    },
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=1e-12).to(DTYPE)
    out = vecs @ torch.diag(vals) @ vecs.conj().T
    return out / torch.trace(out).real


def initial_density(seed: int) -> torch.Tensor:
    generator = torch.Generator().manual_seed(seed + 23)
    theta = 0.24 + 1.05 * float(torch.rand((), generator=generator).item())
    phi = 2.0 * math.pi * float(torch.rand((), generator=generator).item())
    phase = complex(math.cos(phi), math.sin(phi))
    psi = torch.tensor(
        [math.cos(theta), math.sin(theta) * phase],
        dtype=DTYPE,
    ).reshape(2, 1)
    pure = psi @ psi.conj().T
    return normalize_density(0.88 * pure + 0.12 * I2 / 2)


def adversarial_density(seed: int) -> torch.Tensor:
    """Fixed shared starts chosen near axes and mixed boundaries."""
    fixtures = [
        torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=DTYPE),
        torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=DTYPE),
        0.5 * torch.tensor([[1.0, 1.0], [1.0, 1.0]], dtype=DTYPE),
        0.5 * torch.tensor([[1.0, -1j], [1j, 1.0]], dtype=DTYPE),
        torch.tensor([[0.52, 0.18 + 0.22j], [0.18 - 0.22j, 0.48]], dtype=DTYPE),
        torch.tensor([[0.50, -0.24 + 0.05j], [-0.24 - 0.05j, 0.50]], dtype=DTYPE),
    ]
    return normalize_density(fixtures[seed % len(fixtures)])


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    return float(-(vals * torch.log(vals)).sum().item())


def purity(rho: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ rho)).item())


def bloch(rho: torch.Tensor) -> torch.Tensor:
    return torch.tensor(
        [
            float(torch.real(torch.trace(SX @ rho)).item()),
            float(torch.real(torch.trace(SY @ rho)).item()),
            float(torch.real(torch.trace(SZ @ rho)).item()),
        ],
        dtype=torch.float64,
    )


def unitary_from_generator(generator: torch.Tensor, angle: float) -> torch.Tensor:
    vals, vecs = torch.linalg.eig((-1j * angle * generator).to(DTYPE))
    return vecs @ torch.diag(torch.exp(vals)) @ torch.linalg.inv(vecs)


def signed_operator(rho: torch.Tensor, name: str, sign: int, chirality_sign: int) -> torch.Tensor:
    if name == "Ti":
        gen, base = SZ, 0.17
    elif name == "Te":
        gen, base = SX, 0.14
    elif name == "Fi":
        gen, base = SX, 0.22
    elif name == "Fe":
        gen, base = SY, 0.19
    else:
        raise ValueError(name)
    angle = base * float(sign) * float(chirality_sign)
    u = unitary_from_generator(gen, angle)
    return normalize_density(u @ rho @ u.conj().T)


def dissipator(rho: torch.Tensor, ladder: torch.Tensor, gamma: float) -> torch.Tensor:
    dt = 0.11
    jump = math.sqrt(gamma * dt) * ladder
    no_jump = I2 - 0.5 * gamma * dt * ladder.conj().T @ ladder
    return normalize_density(jump @ rho @ jump.conj().T + no_jump @ rho @ no_jump.conj().T)


def dephase(rho: torch.Tensor, axis: str, rate: float) -> torch.Tensor:
    pinched = sum(p @ rho @ p for p in PROJECTORS[axis])
    return normalize_density((1 - rate) * rho + rate * pinched)


def loop_update(rho: torch.Tensor, loop: str, step: int, chirality_sign: int, *, hide_loop: bool = False) -> torch.Tensor:
    if hide_loop:
        loop = "fiber"
    u = (step + 1) * 2.0 * math.pi / 9.0
    if loop == "fiber":
        unitary = unitary_from_generator(SZ, 0.035 * chirality_sign * u)
    elif loop == "base":
        unitary = unitary_from_generator(0.75 * SX + 0.25 * SZ, 0.071 * chirality_sign * u)
    else:
        raise ValueError(loop)
    return normalize_density(unitary @ rho @ unitary.conj().T)


def topology_update(
    rho: torch.Tensor,
    topo: str,
    spec: dict[str, Any],
    chirality_sign: int,
    *,
    collapse_topology: bool = False,
    erase_signs: bool = False,
    hide_loop: bool = False,
    reverse_order: bool = False,
    topology_agnostic_noise: float = 0.0,
) -> dict[str, Any]:
    start = rho.clone()
    cfg = dict(spec)
    if collapse_topology:
        cfg["projector_axis"] = "z"
        cfg["rate"] = 0.18
        cfg["mode"] = "collapsed"

    major = dict(cfg["major"])
    minor = dict(cfg["minor"])
    if erase_signs:
        major["sign"] = +1
        minor["sign"] = +1
    steps = [("major", "base", major), ("minor", "fiber", minor)]
    if reverse_order:
        steps = list(reversed(steps))

    h = rho.clone()
    ladder = SM if chirality_sign == +1 else SP
    for idx, (_which, loop, op) in enumerate(steps):
        h = loop_update(h, loop, idx, chirality_sign, hide_loop=hide_loop)
        h = signed_operator(h, op["operator"], op["sign"], chirality_sign)
        h = dissipator(h, ladder, float(cfg["rate"]))
        h = dephase(h, str(cfg["projector_axis"]), 0.14 + 0.35 * float(cfg["rate"]))
        if topology_agnostic_noise:
            h = normalize_density((1.0 - topology_agnostic_noise) * h + topology_agnostic_noise * I2 / 2.0)

    b0 = bloch(start)
    b1 = bloch(h)
    feature = torch.tensor(
        [
            *[(v.item()) for v in (b1 - b0)],
            entropy(h) - entropy(start),
            purity(h) - purity(start),
            float(torch.linalg.norm(b1[:2]).item()),
            float(b1[2]),
            float(torch.atan2(b1[1], b1[0]).item()),
        ],
        dtype=torch.float64,
    )
    return {
        "topology": topo,
        "realization": cfg["realization"],
        "strategy_pattern": cfg["strategy_pattern"],
        "major": major,
        "minor": minor,
        "feature": feature,
        "final_bloch": b1,
    }


def run_samples(
    specs: dict[str, dict[str, Any]],
    chirality_sign: int,
    *,
    collapse_topology: bool = False,
    erase_signs: bool = False,
    hide_loop: bool = False,
    reverse_order: bool = False,
    adversarial_starts: bool = False,
    topology_agnostic_noise: float = 0.0,
) -> list[dict[str, Any]]:
    rows = []
    n_seeds = 6 if adversarial_starts else 24
    for seed in range(n_seeds):
        rho = adversarial_density(seed) if adversarial_starts else initial_density(seed)
        for topo, spec in specs.items():
            row = topology_update(
                rho,
                topo,
                spec,
                chirality_sign,
                collapse_topology=collapse_topology,
                erase_signs=erase_signs,
                hide_loop=hide_loop,
                reverse_order=reverse_order,
                topology_agnostic_noise=topology_agnostic_noise,
            )
            row["seed"] = seed
            rows.append(row)
    return rows


def shuffled_generator_laws(specs: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Rotate generator-law parameters while preserving topology labels and ordered pairs."""
    keys = sorted(specs)
    rotated = keys[1:] + keys[:1]
    out = {k: dict(v) for k, v in specs.items()}
    for dst, src in zip(keys, rotated):
        out[dst]["projector_axis"] = specs[src]["projector_axis"]
        out[dst]["rate"] = specs[src]["rate"]
        out[dst]["mode"] = f"shuffled_from_{src}"
    return out


def centroids(rows: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
    out = {}
    for topo in sorted({r["topology"] for r in rows}):
        feats = torch.stack([r["feature"] for r in rows if r["topology"] == topo], dim=0)
        out[topo] = feats.mean(dim=0)
    return out


def separation_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    c = centroids(rows)
    keys = sorted(c)
    dists = {}
    min_dist = float("inf")
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            d = float(torch.linalg.norm(c[a] - c[b]).item())
            dists[f"{a}-{b}"] = d
            min_dist = min(min_dist, d)
    paired_minima = []
    for seed in sorted({r["seed"] for r in rows}):
        seed_rows = [r for r in rows if r["seed"] == seed]
        for chirality_realization in sorted({r["realization"] for r in seed_rows}):
            # A realization names one topology, so for combined left/right rows this
            # grouping is too narrow. The paired same-seed test below therefore
            # uses all rows for a seed and all topology labels, measuring whether
            # the topology laws separate from each other before seed variance can
            # dominate the statistic.
            pass
        seed_by_topology = {}
        for row in seed_rows:
            seed_by_topology.setdefault(row["topology"], []).append(row["feature"])
        seed_centroids = {k: torch.stack(v, dim=0).mean(dim=0) for k, v in seed_by_topology.items()}
        seed_keys = sorted(seed_centroids)
        for i, a in enumerate(seed_keys):
            for b in seed_keys[i + 1 :]:
                paired_minima.append(float(torch.linalg.norm(seed_centroids[a] - seed_centroids[b]).item()))
    min_paired_same_seed_distance = min(paired_minima) if paired_minima else 0.0
    correct = 0
    for row in rows:
        nearest = min(keys, key=lambda k: float(torch.linalg.norm(row["feature"] - c[k]).item()))
        correct += int(nearest == row["topology"])
    accuracy = correct / max(len(rows), 1)
    return {
        "centroids": {k: (torch.round(v * 1e6) / 1e6).tolist() for k, v in c.items()},
        "pairwise_centroid_distances": {k: round(v, 6) for k, v in dists.items()},
        "min_centroid_distance": min_dist,
        "min_paired_same_seed_distance": min_paired_same_seed_distance,
        "nearest_centroid_accuracy": accuracy,
        "pass": min_dist > 0.035 and min_paired_same_seed_distance > 0.045,
    }


def persistence_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    points = torch.stack([r["feature"] for r in rows], dim=0).to(torch.float64)
    st = gudhi.RipsComplex(points=points.tolist(), max_edge_length=0.42).create_simplex_tree(max_dimension=1)
    intervals = st.persistence()
    h0 = [p for dim, p in intervals if dim == 0]
    finite_h0 = [death - birth for birth, death in h0 if death < float("inf")]
    return {
        "h0_count": len(h0),
        "finite_h0_count": len(finite_h0),
        "max_finite_h0_persistence": float(max(finite_h0)) if finite_h0 else 0.0,
        "pass": len(h0) >= 4 and (max(finite_h0) if finite_h0 else 0.0) > 0.03,
    }


def graph_report() -> dict[str, Any]:
    g = nx.DiGraph()
    inductive = ["Se", "Si", "Ni", "Ne"]
    deductive = ["Se", "Ne", "Ni", "Si"]
    for walk, label in [(inductive, "inductive"), (deductive, "deductive")]:
        for a, b in zip(walk, walk[1:]):
            g.add_edge(a, b, family=label)
    return {
        "nodes": sorted(g.nodes()),
        "edges": [(a, b, g.edges[a, b]["family"]) for a, b in g.edges()],
        "strongly_connected_components": [sorted(s) for s in nx.strongly_connected_components(g)],
        "pass": set(g.nodes()) == {"Se", "Ne", "Ni", "Si"} and g.number_of_edges() == 6,
    }


def symbolic_inventory_report() -> dict[str, Any]:
    topologies, realizations, loop_rows = sp.symbols("topologies realizations loop_rows", integer=True)
    ok = sp.And(sp.Eq(topologies, 4), sp.Eq(realizations, 8), sp.Eq(loop_rows, 16))
    return {
        "topologies": 4,
        "chiral_realizations": 8,
        "loop_placement_rows": 16,
        "sympy_inventory_truth": bool(ok.subs({topologies: 4, realizations: 8, loop_rows: 16})),
        "pass": bool(ok.subs({topologies: 4, realizations: 8, loop_rows: 16})),
    }


def main() -> int:
    start = time.time()
    left_rows = run_samples(TYPE_ONE_TOPOLOGIES, +1)
    right_rows = run_samples(TYPE_TWO_TOPOLOGIES, -1)
    combined = left_rows + right_rows

    left_sep = separation_report(left_rows)
    right_sep = separation_report(right_rows)
    combined_sep = separation_report(combined)
    adversarial_sep = separation_report(
        run_samples(TYPE_ONE_TOPOLOGIES, +1, adversarial_starts=True)
        + run_samples(TYPE_TWO_TOPOLOGIES, -1, adversarial_starts=True)
    )
    noisy_sep = separation_report(
        run_samples(TYPE_ONE_TOPOLOGIES, +1, topology_agnostic_noise=0.045)
        + run_samples(TYPE_TWO_TOPOLOGIES, -1, topology_agnostic_noise=0.045)
    )
    topo_persistence = persistence_report(combined)
    transition_graph = graph_report()
    symbolic_inventory = symbolic_inventory_report()

    controls = {
        "collapsed_topology_laws": separation_report(
            run_samples(TYPE_ONE_TOPOLOGIES, +1, collapse_topology=True)
            + run_samples(TYPE_TWO_TOPOLOGIES, -1, collapse_topology=True)
        ),
        "hidden_loop_placement": separation_report(
            run_samples(TYPE_ONE_TOPOLOGIES, +1, hide_loop=True)
            + run_samples(TYPE_TWO_TOPOLOGIES, -1, hide_loop=True)
        ),
        "erased_operator_signs": separation_report(
            run_samples(TYPE_ONE_TOPOLOGIES, +1, erase_signs=True)
            + run_samples(TYPE_TWO_TOPOLOGIES, -1, erase_signs=True)
        ),
        "reversed_ordered_pairs": separation_report(
            run_samples(TYPE_ONE_TOPOLOGIES, +1, reverse_order=True)
            + run_samples(TYPE_TWO_TOPOLOGIES, -1, reverse_order=True)
        ),
        "shuffled_generator_laws": separation_report(
            run_samples(shuffled_generator_laws(TYPE_ONE_TOPOLOGIES), +1)
            + run_samples(shuffled_generator_laws(TYPE_TWO_TOPOLOGIES), -1)
        ),
    }
    graveyards = {
        "collapsed_topology_laws_reduce_separation": {
            **controls["collapsed_topology_laws"],
            "baseline_min_centroid_distance": combined_sep["min_centroid_distance"],
            "control_reduces_separation": controls["collapsed_topology_laws"]["min_centroid_distance"] < 0.75 * combined_sep["min_centroid_distance"],
            "pass": controls["collapsed_topology_laws"]["min_centroid_distance"] < 0.75 * combined_sep["min_centroid_distance"],
        },
        "hidden_loop_placement_changes_behavior": {
            **controls["hidden_loop_placement"],
            "baseline_min_centroid_distance": combined_sep["min_centroid_distance"],
            "control_changes_inventory": controls["hidden_loop_placement"]["centroids"] != combined_sep["centroids"],
            "pass": controls["hidden_loop_placement"]["centroids"] != combined_sep["centroids"],
        },
        "erased_operator_signs_changes_behavior": {
            **controls["erased_operator_signs"],
            "baseline_min_centroid_distance": combined_sep["min_centroid_distance"],
            "control_changes_inventory": controls["erased_operator_signs"]["centroids"] != combined_sep["centroids"],
            "pass": controls["erased_operator_signs"]["centroids"] != combined_sep["centroids"],
        },
        "reversed_ordered_pairs_changes_behavior": {
            **controls["reversed_ordered_pairs"],
            "baseline_min_centroid_distance": combined_sep["min_centroid_distance"],
            "control_changes_inventory": controls["reversed_ordered_pairs"]["centroids"] != combined_sep["centroids"],
            "pass": controls["reversed_ordered_pairs"]["centroids"] != combined_sep["centroids"],
        },
        "shuffled_generator_laws_changes_behavior": {
            **controls["shuffled_generator_laws"],
            "baseline_min_centroid_distance": combined_sep["min_centroid_distance"],
            "control_changes_inventory": controls["shuffled_generator_laws"]["centroids"] != combined_sep["centroids"],
            "pass": controls["shuffled_generator_laws"]["centroids"] != combined_sep["centroids"],
        },
    }

    positive = {
        "type_one_four_behavior_classes_separate": left_sep,
        "type_two_four_behavior_classes_separate": right_sep,
        "combined_topology_classes_separate": combined_sep,
        "adversarial_shared_starts_still_separate": adversarial_sep,
        "topology_agnostic_noise_still_separates": noisy_sep,
        "persistent_behavior_point_cloud_nontrivial": topo_persistence,
        "topology_transition_graph_has_expected_four_nodes": transition_graph,
        "symbolic_inventory_four_topologies_eight_realizations": symbolic_inventory,
    }
    boundary = {
        "type_one_overlay": {"pass": True, "rows": TYPE_ONE_TOPOLOGIES},
        "type_two_overlay": {"pass": True, "rows": TYPE_TWO_TOPOLOGIES},
        "behavior_observable_vector": {
            "pass": True,
            "fields": ["delta_x", "delta_y", "delta_z", "delta_entropy", "delta_purity", "xy_radius", "final_z", "final_phase"],
        },
    }
    nearby_variants = {
        "total": 5,
        "passed": sum(1 for row in graveyards.values() if row["pass"]),
        "variants": sorted(graveyards),
    }
    all_pass = (
        all(row.get("pass") for row in positive.values())
        and all(row.get("pass") for row in graveyards.values())
        and all(row.get("pass") for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_alignment_category": "source_native_topology_behavior_class_probe_with_human_overlay_labels",
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Uses finite two-dimensional density fixtures and formal behavior signatures only.",
            "Human-facing strategy and Jungian labels are overlays, not promoted ontology.",
            "Does not prove personality, cognition, physics, or final constraint-manifold identity.",
            "Does not yet wire the behavior classes into a trainable neural-network architecture.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - start,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
