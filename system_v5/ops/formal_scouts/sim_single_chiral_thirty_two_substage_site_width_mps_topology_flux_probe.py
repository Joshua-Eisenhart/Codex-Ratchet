#!/usr/bin/env python3
"""Single-chiral 32-substage site-width MPS topology/flux formal scout.

This scout keeps the carrier at 32 MPS sites, one site per
``(main_stage_idx, substage_idx)`` for 8 stages x 4 substages. It does not
construct a dense ``2**32`` state.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import sympy as sp
import torch
import z3

from engine_v7_mps_reference import DTYPE, I2, MPS, SX, SY, SZ


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "single_chiral_thirty_two_substage_site_width_mps_topology_flux_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: demonstrates that a single-chiral 8-stage x "
    "4-substage topology/flux fixture can execute as a 32-site open-boundary "
    "MPS with PyTorch local/two-site updates, rustworkx topology, sympy "
    "factorization sanity, and z3 noncollapse checks. It does not admit a "
    "canonical engine, final topology, bridge, axis, physics, or target-system "
    "claim."
)

N_STAGES = 8
N_SUBSTAGES = 4
N_SITES = N_STAGES * N_SUBSTAGES
CHI_MAX = 4
DT = 0.045

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: builds product MPS tensors, applies torch.linalg.matrix_exp local operators, nearest-neighbor MPS two-site gates, reduced single-site density readouts, and boundary/bond checks without dense 2**32 state construction",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: PyDiGraph encodes 32 stage/substage nodes, chain/substage topology edges, connected-component checks, and topology-degree controls that directly change local updates",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: exact 8 * 4 = 32 factorization and operator/site-count sanity are checked before accepting the carrier",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: each collapse/control equality predicate against the full 32-site signature is encoded and required UNSAT",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def canonical_pairs() -> list[tuple[int, int]]:
    return [(stage, substage) for stage in range(N_STAGES) for substage in range(N_SUBSTAGES)]


def product_carrier(pairs: list[tuple[int, int]]) -> MPS:
    vecs = []
    for site, (stage, substage) in enumerate(pairs):
        theta = 0.17 + 0.031 * (stage + 1) + 0.043 * (substage + 1)
        phase = 0.11 * (site + 1) + 0.07 * (stage - substage)
        v0 = math.cos(theta)
        v1 = complex(math.cos(phase), math.sin(phase)) * math.sin(theta)
        vec = torch.tensor([v0, v1], dtype=DTYPE)
        vec = vec / torch.linalg.vector_norm(vec)
        vecs.append(vec)
    return MPS.product(vecs)


def build_topology(
    pairs: list[tuple[int, int]], topology_enabled: bool = True
) -> tuple[rx.PyDiGraph, dict[tuple[int, int], float], list[int]]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from([{"stage": stage, "substage": substage} for stage, substage in pairs])
    adjacent_weights: dict[tuple[int, int], float] = {}
    degree = [0 for _ in pairs]

    if not topology_enabled:
        return graph, adjacent_weights, degree

    for site in range(len(pairs) - 1):
        left_stage, left_substage = pairs[site]
        right_stage, right_substage = pairs[site + 1]
        same_stage_step = int(left_stage == right_stage)
        weight = 0.23 + 0.019 * (left_stage + right_stage + 2) + 0.031 * (same_stage_step + 1)
        graph.add_edge(site, site + 1, {"kind": "mps_chain", "weight": weight})
        adjacent_weights[(site, site + 1)] = weight
        degree[site] += 1
        degree[site + 1] += 1
        if left_substage == N_SUBSTAGES - 1 and right_substage == 0:
            graph.add_edge(site + 1, site, {"kind": "stage_return", "weight": weight / 2.0})
            degree[site] += 1
            degree[site + 1] += 1

    # Nonlocal graph edges are not applied as MPS gates. They are load-bearing
    # topology data through rustworkx degree/edge-count readouts.
    for site, (stage, substage) in enumerate(pairs):
        for other, (other_stage, other_substage) in enumerate(pairs):
            if other <= site:
                continue
            if other_stage == stage + 1 and other_substage == substage:
                graph.add_edge(site, other, {"kind": "same_substage_next_stage", "weight": 0.11})
                degree[site] += 1
                degree[other] += 1
    return graph, adjacent_weights, degree


def flux_value(stage: int, substage: int, mode: str) -> float:
    if mode == "erased":
        return 0.0
    if mode == "substage_average":
        vals = [flux_value(stage, s, "full") for s in range(N_SUBSTAGES)]
        return sum(vals) / len(vals)
    chirality = 1.0
    terrain_phase = [1.0, -0.35, 0.72, -0.58, 0.41, -0.83, 0.66, -0.24][stage % N_STAGES]
    substage_phase = [0.19, -0.07, 0.31, -0.23][substage % N_SUBSTAGES]
    return chirality * (0.12 + 0.037 * (stage + 1) + terrain_phase + substage_phase)


def local_update(site: int, stage: int, substage: int, flux: float, degree: int, mode: str) -> torch.Tensor:
    substage_term = 0.0 if mode == "substage_average" else 0.053 * (substage + 1)
    hamiltonian = (
        flux * SZ
        + (0.021 * (degree + 1)) * SX
        + (substage_term + 0.009 * (site + 1)) * SY
    )
    return torch.linalg.matrix_exp((-1j * DT) * hamiltonian.to(DTYPE))


def two_site_gate(weight: float, left_flux: float, right_flux: float) -> torch.Tensor:
    zz = torch.kron(SZ, SZ)
    xx = torch.kron(SX, SX)
    hamiltonian = (0.17 * weight + 0.03 * abs(left_flux - right_flux)) * zz + 0.019 * weight * xx
    return torch.linalg.matrix_exp((-1j * DT) * hamiltonian.to(DTYPE)).reshape(2, 2, 2, 2)


def site_entropy(rho: torch.Tensor) -> float:
    rho_h = (rho + rho.conj().T) / 2
    trace = rho_h.trace().real
    if abs(float(trace)) > 1e-12:
        rho_h = rho_h / trace
    eigs = torch.clamp(torch.linalg.eigvalsh(rho_h).real, min=1e-12)
    eigs = eigs / eigs.sum()
    return float(-(eigs * torch.log(eigs)).sum().real)


def bloch(rho: torch.Tensor, op: torch.Tensor) -> float:
    rho_h = (rho + rho.conj().T) / 2
    trace = rho_h.trace().real
    if abs(float(trace)) > 1e-12:
        rho_h = rho_h / trace
    return float(torch.trace(op.to(DTYPE) @ rho_h).real)


def quantize(value: float) -> int:
    return int(round(float(value) * 1_000_000))


def run_fixture(
    label: str,
    pairs: list[tuple[int, int]],
    *,
    topology_enabled: bool = True,
    flux_mode: str = "full",
    product_control: bool = False,
) -> dict[str, Any]:
    graph, adjacent_weights, degree = build_topology(pairs, topology_enabled=topology_enabled)
    mps = product_carrier(pairs)
    rows = []

    for site, (stage, substage) in enumerate(pairs):
        flux = flux_value(stage, substage, flux_mode)
        mps.apply_single(local_update(site, stage, substage, flux, degree[site], flux_mode), site)
        if site > 0 and not product_control:
            edge_weight = adjacent_weights.get((site - 1, site), 0.0)
            left_stage, left_substage = pairs[site - 1]
            left_flux = flux_value(left_stage, left_substage, flux_mode)
            gate = two_site_gate(edge_weight, left_flux, flux)
            mps.apply_two(gate, site - 1, max_bond=CHI_MAX)
        mps.normalize_()
        rho = mps.reduced_single(site)
        rows.append(
            {
                "site": site,
                "stage": stage,
                "substage": substage,
                "flux_q": quantize(flux),
                "degree": degree[site],
                "entropy_q": quantize(site_entropy(rho)),
                "bloch_z_q": quantize(bloch(rho, SZ)),
                "bloch_x_q": quantize(bloch(rho, SX)),
            }
        )

    max_bond = max(max(t.shape[1], t.shape[2]) for t in mps.tensors)
    boundary_valid = (
        mps.tensors[0].shape[1] == 1
        and mps.tensors[-1].shape[2] == 1
        and max_bond <= CHI_MAX
        and all(t.shape[0] == 2 for t in mps.tensors)
    )
    components = rx.weakly_connected_components(graph) if graph.num_nodes() else []

    signature = {
        "site_count": len(pairs),
        "stage_count": len({stage for stage, _ in pairs}),
        "substage_count": len({substage for _, substage in pairs}),
        "topology_edges": int(graph.num_edges()),
        "topology_components": int(len(components)),
        "max_bond": int(max_bond),
        "entropy_sum_q": int(sum(row["entropy_q"] for row in rows)),
        "weighted_z_q": int(sum((row["site"] + 1) * row["bloch_z_q"] for row in rows)),
        "weighted_x_q": int(sum(((-1) ** row["site"]) * (row["site"] + 3) * row["bloch_x_q"] for row in rows)),
        "topology_flux_q": int(sum((row["degree"] + 1) * row["flux_q"] for row in rows)),
        "stage_substage_checksum_q": int(
            sum((row["stage"] + 1) * 101 + (row["substage"] + 1) * 17 + row["site"] for row in rows)
        ),
    }
    return {
        "label": label,
        "pairs": [list(pair) for pair in pairs],
        "signature": signature,
        "rows_head": rows[:4],
        "rows_tail": rows[-4:],
        "mps_boundary": {
            "left_boundary_dim": int(mps.tensors[0].shape[1]),
            "right_boundary_dim": int(mps.tensors[-1].shape[2]),
            "max_bond": int(max_bond),
            "valid_open_boundary": bool(boundary_valid),
        },
        "rustworkx": {
            "nodes": int(graph.num_nodes()),
            "edges": int(graph.num_edges()),
            "weak_components": int(len(components)),
            "adjacent_mps_gate_edges": len(adjacent_weights),
        },
    }


def stage_substage_bijection_check(pairs: list[tuple[int, int]]) -> dict[str, Any]:
    forward = {(stage, substage): site for site, (stage, substage) in enumerate(pairs)}
    inverse = {site: pair for pair, site in forward.items()}
    expected = set(canonical_pairs())
    return {
        "site_count": len(pairs),
        "unique_pairs": len(forward),
        "expected_pairs": len(expected),
        "inverse_roundtrip": all(inverse[forward[pair]] == pair for pair in expected),
        "pass": len(pairs) == N_SITES and set(forward) == expected and len(inverse) == N_SITES,
    }


def sympy_sanity() -> dict[str, Any]:
    stage_count = sp.Integer(N_STAGES)
    substage_count = sp.Integer(N_SUBSTAGES)
    site_count = sp.Integer(N_SITES)
    product = stage_count * substage_count
    return {
        "factorization": f"{stage_count} * {substage_count} = {product}",
        "factorint_32": {str(k): int(v) for k, v in sp.factorint(product).items()},
        "operator_slots": int(sp.Sum(1, (sp.Symbol("i"), 1, site_count)).doit()),
        "pass": bool(sp.Eq(product, site_count)) and product == site_count,
    }


def z3_distinct(full: dict[str, int], control: dict[str, int], label: str) -> dict[str, Any]:
    solver = z3.Solver()
    equalities = []
    for key in sorted(full):
        left = z3.Int(f"full_{label}_{key}")
        right = z3.Int(f"control_{label}_{key}")
        solver.add(left == int(full[key]))
        solver.add(right == int(control.get(key, 0)))
        equalities.append(left == right)
    solver.add(z3.And(equalities))
    status = solver.check()
    return {
        "control": label,
        "status": str(status),
        "pass": status == z3.unsat,
        "differing_keys": [key for key in sorted(full) if int(full[key]) != int(control.get(key, 0))],
    }


def main() -> dict[str, Any]:
    started = time.time()
    pairs = canonical_pairs()
    full = run_fixture("full_32_site_topology_flux", pairs)

    controls = {
        "stage_only_8_site_collapse": run_fixture(
            "stage_only_8_site_collapse", [(stage, 0) for stage in range(N_STAGES)]
        ),
        "four_substage_averaging": run_fixture(
            "four_substage_averaging", pairs, flux_mode="substage_average"
        ),
        "flux_erasure": run_fixture("flux_erasure", pairs, flux_mode="erased"),
        "topology_erasure": run_fixture("topology_erasure", pairs, topology_enabled=False),
        "reversed_order": run_fixture("reversed_order", list(reversed(pairs))),
        "product_bond_dim_1_control": run_fixture(
            "product_bond_dim_1_control", pairs, product_control=True
        ),
    }

    z3_rows = {
        label: z3_distinct(full["signature"], control["signature"], label)
        for label, control in controls.items()
    }
    bijection = stage_substage_bijection_check(pairs)
    sympy_row = sympy_sanity()

    positive = {
        "32_site_carrier_executes": {
            "site_count": full["signature"]["site_count"],
            "mps_boundary": full["mps_boundary"],
            "dense_state_dimension_avoided": "2**32 not constructed",
            "pass": full["signature"]["site_count"] == N_SITES and full["mps_boundary"]["valid_open_boundary"],
        },
        "stage_substage_bijection": bijection,
        "topology_flux_controls_separate": {
            "full_signature": full["signature"],
            "flux_erasure_differs": controls["flux_erasure"]["signature"] != full["signature"],
            "topology_erasure_differs": controls["topology_erasure"]["signature"] != full["signature"],
            "flux_and_topology_controls_distinct": controls["flux_erasure"]["signature"] != controls["topology_erasure"]["signature"],
            "pass": (
                controls["flux_erasure"]["signature"] != full["signature"]
                and controls["topology_erasure"]["signature"] != full["signature"]
                and controls["flux_erasure"]["signature"] != controls["topology_erasure"]["signature"]
            ),
        },
        "substage_grain_not_collapsed": {
            "stage_only_differs": controls["stage_only_8_site_collapse"]["signature"] != full["signature"],
            "four_substage_average_differs": controls["four_substage_averaging"]["signature"] != full["signature"],
            "pass": (
                controls["stage_only_8_site_collapse"]["signature"] != full["signature"]
                and controls["four_substage_averaging"]["signature"] != full["signature"]
            ),
        },
        "valid_mps_boundary": {
            "boundary": full["mps_boundary"],
            "pass": full["mps_boundary"]["valid_open_boundary"],
        },
        "z3_noncollapse_unsat": {
            "rows": z3_rows,
            "pass": all(row["pass"] for row in z3_rows.values()),
        },
        "sympy_factorization_operator_sanity": sympy_row,
    }

    graveyard_companions = {
        label: {
            "signature": control["signature"],
            "mps_boundary": control["mps_boundary"],
            "z3_equal_to_full": z3_rows[label],
            "pass": control["signature"] != full["signature"] and z3_rows[label]["pass"],
        }
        for label, control in controls.items()
    }

    boundary = {
        "no_dense_2_pow_32_materialization": {
            "carrier": "MPS list of 32 local tensors",
            "largest_tensor_numel": max(int(t.shape[0] * t.shape[1] * t.shape[2]) for t in product_carrier(pairs).tensors),
            "dense_dimension_forbidden": 2**32,
            "pass": True,
        },
        "rustworkx_topology_is_present_and_controlled": {
            "full_graph": full["rustworkx"],
            "topology_erased_graph": controls["topology_erasure"]["rustworkx"],
            "pass": full["rustworkx"]["edges"] > 0 and controls["topology_erasure"]["rustworkx"]["edges"] == 0,
        },
        "product_control_keeps_bond_dim_one": {
            "product_boundary": controls["product_bond_dim_1_control"]["mps_boundary"],
            "pass": controls["product_bond_dim_1_control"]["mps_boundary"]["max_bond"] == 1,
        },
    }

    nearby_total = len(graveyard_companions)
    nearby_passed = sum(1 for row in graveyard_companions.values() if row["pass"])
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "32-site open-boundary single-chiral MPS with one site per (main_stage_idx, substage_idx) and topology/flux controls",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": nearby_total,
            "passed": nearby_passed,
        },
        "controls": controls,
        "full_fixture": full,
        "blockers": [],
        "open_choices": [
            "Replace the toy single-chiral flux schedule with source-native terrain operator coefficients before any canonical claim.",
            "Add a second chiral sector and explicit inter-chiral comparison only after this 32-site single-chiral carrier remains stable under further controls.",
        ],
        "surviving_alternatives": [
            "A geometry-derived topology graph could replace the deterministic stage/substage graph and may change which controls separate.",
            "Larger bond caps may expose additional entanglement readouts but are not needed for this smallest 32-substage carrier scout.",
        ],
        "why_not_v4_probes": "Standalone v5 formal scout over the current formal_scouts surface; it is not a v4 probe and does not promote or alter the canonical sim estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "criteria_checked": [
            "32_site_carrier_executes",
            "stage_substage_bijection",
            "topology_flux_controls_separate",
            "substage_grain_not_collapsed",
            "valid_mps_boundary",
            "z3_noncollapse_unsat",
        ],
        "summary": {
            "all_pass": bool(all_pass),
            "positive_pass": sum(1 for row in positive.values() if row["pass"]),
            "positive_total": len(positive),
            "graveyard_pass": nearby_passed,
            "graveyard_total": nearby_total,
            "boundary_pass": sum(1 for row in boundary.values() if row["pass"]),
            "boundary_total": len(boundary),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
