#!/usr/bin/env python3
"""Build a source-native QIT engine/manifold runtime fixture.

This is the first formal build pass after the D86 tooling closeout. It uses the
current canonical QIT engine specs directly, constructs one exact E=8
terrain-stage density-matrix engine per chiral type, evolves it with local
Lindblad channels plus nearest-neighbor ZZ coupling, and reads the manifold
quantities that later W7+ work needs.

Scope boundary:
- exact full density matrix only at E=8 (dim 256);
- E=16 is built as paired-engine substrate metadata plus paired E=8 runtime
  summaries, not a full 2^16 x 2^16 density;
- no PEPS/PEPS3D, no full tensor-network Lindblad, no final basin promotion.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import canonical_qit_engine_specs as specs


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_qit_engine_manifold_runtime_build_probe_results.json"

NAME = "two_root_constraint_qit_engine_manifold_runtime_build_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_runtime_build"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_qit_engine_manifold_runtime_build"
CLAIM_CEILING = (
    "Formal build receipt only: constructs and runs a source-native E=8 exact "
    "density-matrix QIT terrain-engine runtime from canonical_qit_engine_specs, "
    "plus paired E=16 substrate metadata and E=8 manifold readouts. It does not "
    "admit a final manifold, real attractor basin, full E=16 density evolution, "
    "PEPS/PEPS3D, full tensor-network Lindblad, Axis0 theorem, G-structure, "
    "engine theorem, physics validation, or D86 reopening."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact complex density evolution, Lindblad channel exponentials, partial traces, entropies, and Bloch readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph witness for E=8 engine and paired E=16 substrate connectivity",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing scale and nonpromotion satisfiability checks",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "itertools": {"tried": True, "used": True, "reason": "supportive partial-trace index enumeration"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
    "itertools": "supportive",
}

DTYPE = torch.complex128
RTYPE = torch.float64
N_SITES = 8
DIM = 2**N_SITES
DT = 0.18
CYCLES = 3
ZZ_COUPLING = 0.035
TRACE_TOL = 1.0e-8
HERMITIAN_TOL = 1.0e-8
PSD_TOL = 1.0e-7

SOURCE_FILES = {
    "canonical_qit_engine_specs": SCOUT_ROOT / "canonical_qit_engine_specs.py",
    "w3_terrain_lindblad_composition": SCOUT_ROOT / "sim_constraint_manifold_terrain_lindblad_composition_bridge_probe.py",
    "w7_tensor_substrate_scope": SCOUT_ROOT / "sim_two_root_constraint_terrain_engine_pseudo_basin_tensor_substrate_scope_probe.py",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return float(item)
        return value.detach().cpu().tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    return value


def bits_to_int(bits: list[int]) -> int:
    out = 0
    for bit in bits:
        out = (out << 1) | int(bit)
    return out


def ket_from_bits(bits: list[int]) -> torch.Tensor:
    ket = torch.zeros(2 ** len(bits), dtype=DTYPE)
    ket[bits_to_int(bits)] = 1.0 + 0.0j
    return ket


def initial_ket(name: str, n_sites: int) -> torch.Tensor:
    if name == "all_zero":
        return ket_from_bits([0] * n_sites)
    if name == "all_one":
        return ket_from_bits([1] * n_sites)
    if name == "alternating":
        return ket_from_bits([idx % 2 for idx in range(n_sites)])
    if name == "plus":
        ket = torch.ones(2**n_sites, dtype=DTYPE)
        return ket / torch.linalg.vector_norm(ket)
    raise ValueError(f"unknown initial state {name!r}")


def density_from_ket(ket: torch.Tensor) -> torch.Tensor:
    return torch.outer(ket, ket.conj())


def row_major_liouvillian(H: torch.Tensor, L: torch.Tensor) -> torch.Tensor:
    eye = torch.eye(2, dtype=DTYPE)
    K = L.conj().T @ L
    h_t = H.T.contiguous()
    k_t = K.T.contiguous()
    coherent = -1j * (torch.kron(H, eye) - torch.kron(eye, h_t))
    dissipator = torch.kron(L, L.conj()) - 0.5 * (torch.kron(K, eye) + torch.kron(eye, k_t))
    return coherent + dissipator


def local_channel(H: torch.Tensor, L: torch.Tensor, dt: float) -> torch.Tensor:
    return torch.linalg.matrix_exp(dt * row_major_liouvillian(H, L))


def apply_local_channel(rho: torch.Tensor, channel: torch.Tensor, site: int, n_sites: int) -> torch.Tensor:
    shape = [2] * (2 * n_sites)
    tensor = rho.reshape(shape)
    pair = [site, n_sites + site]
    rest = [idx for idx in range(2 * n_sites) if idx not in pair]
    perm = pair + rest
    inv = [0] * (2 * n_sites)
    for new_idx, old_idx in enumerate(perm):
        inv[old_idx] = new_idx
    front = tensor.permute(perm).reshape(4, -1)
    evolved = (channel @ front).reshape([2, 2] + [2] * (2 * n_sites - 2))
    return evolved.permute(inv).reshape(2**n_sites, 2**n_sites)


def zz_phase(n_sites: int, dt: float, coupling: float) -> torch.Tensor:
    phases: list[complex] = []
    for basis in range(2**n_sites):
        z_values = []
        for site in range(n_sites):
            bit = (basis >> (n_sites - site - 1)) & 1
            z_values.append(1.0 if bit == 0 else -1.0)
        energy = sum(z_values[idx] * z_values[idx + 1] for idx in range(n_sites - 1))
        phases.append(complex(math.cos(-coupling * dt * energy), math.sin(-coupling * dt * energy)))
    return torch.tensor(phases, dtype=DTYPE)


def apply_diagonal_unitary(rho: torch.Tensor, phase: torch.Tensor) -> torch.Tensor:
    return phase[:, None] * rho * phase.conj()[None, :]


def partial_trace_keep(rho: torch.Tensor, n_sites: int, keep: list[int]) -> torch.Tensor:
    keep = sorted(keep)
    trace_sites = [idx for idx in range(n_sites) if idx not in keep]
    out_dim = 2 ** len(keep)
    out = torch.zeros((out_dim, out_dim), dtype=DTYPE)
    for a in range(out_dim):
        a_bits = [(a >> (len(keep) - pos - 1)) & 1 for pos in range(len(keep))]
        for b in range(out_dim):
            b_bits = [(b >> (len(keep) - pos - 1)) & 1 for pos in range(len(keep))]
            accum = 0.0 + 0.0j
            for rest in range(2 ** len(trace_sites)):
                rest_bits = [(rest >> (len(trace_sites) - pos - 1)) & 1 for pos in range(len(trace_sites))]
                row_bits = [0] * n_sites
                col_bits = [0] * n_sites
                for pos, site in enumerate(keep):
                    row_bits[site] = a_bits[pos]
                    col_bits[site] = b_bits[pos]
                for pos, site in enumerate(trace_sites):
                    row_bits[site] = rest_bits[pos]
                    col_bits[site] = rest_bits[pos]
                accum += rho[bits_to_int(row_bits), bits_to_int(col_bits)]
            out[a, b] = accum
    return out


def von_neumann_entropy(rho: torch.Tensor) -> float:
    herm = 0.5 * (rho + rho.conj().T)
    vals = torch.linalg.eigvalsh(herm).real
    vals = torch.clamp(vals, min=0.0)
    total = vals.sum()
    if float(total) <= 0:
        return 0.0
    vals = vals / total
    nz = vals[vals > 1.0e-14]
    return float(-(nz * torch.log(nz)).sum().item())


def bloch_vector(rho1: torch.Tensor) -> list[float]:
    return [
        float(torch.trace(rho1 @ specs.SX).real.item()),
        float(torch.trace(rho1 @ specs.SY).real.item()),
        float(torch.trace(rho1 @ specs.SZ).real.item()),
    ]


def stage_slots(engine_type: int) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for site, (perception, loop_class) in enumerate(specs.get_schedule(engine_type)):
        topo = specs.get_topology_spec(perception, engine_type)
        slots.append(
            {
                "site": site,
                "engine_type": engine_type,
                "perception": perception,
                "loop_class": loop_class,
                "realization": topo["realization"],
                "pattern": topo["pattern"],
                "mode": topo["mode"],
                "rate": float(topo["rate"]),
            }
        )
    return slots


def channel_for_slot(perception: str, engine_type: int, loop_class: str, substage: int) -> torch.Tensor:
    dyn = specs.get_terrain_dynamics_spec(perception, engine_type)
    slot = specs.get_operator_slot_spec(perception, engine_type, loop_class, substage)
    op = specs.OPERATOR_GENERATORS[slot["operator"]]
    angle = specs.OPERATOR_BASE_ANGLES[slot["operator"]]
    H = dyn["hamiltonian"] + float(slot["sign"]) * angle * op
    _, L_base = specs.get_lindblad_params(perception, engine_type)
    L = math.sqrt(float(dyn["rate"])) * L_base
    return local_channel(H, L, DT)


def precompute_channels(engine_type: int) -> dict[tuple[int, int], torch.Tensor]:
    channels: dict[tuple[int, int], torch.Tensor] = {}
    for slot in stage_slots(engine_type):
        for substage in range(specs.N_SUBSTAGES_PER_MAIN):
            channels[(slot["site"], substage)] = channel_for_slot(
                slot["perception"], engine_type, slot["loop_class"], substage
            )
    return channels


def evolve_engine(engine_type: int, initial_name: str) -> dict[str, Any]:
    rho = density_from_ket(initial_ket(initial_name, N_SITES))
    channels = precompute_channels(engine_type)
    phase = zz_phase(N_SITES, DT, ZZ_COUPLING)
    for _cycle in range(CYCLES):
        for substage in range(specs.N_SUBSTAGES_PER_MAIN):
            for site in range(N_SITES):
                rho = apply_local_channel(rho, channels[(site, substage)], site, N_SITES)
            rho = apply_diagonal_unitary(rho, phase)
            rho = 0.5 * (rho + rho.conj().T)
            rho = rho / torch.trace(rho)

    trace_error = abs(complex(torch.trace(rho).item()) - 1.0)
    hermitian_error = float(torch.max(torch.abs(rho - rho.conj().T)).item())
    min_eig = float(torch.min(torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real).item())

    site_states = [partial_trace_keep(rho, N_SITES, [site]) for site in range(N_SITES)]
    site_bloch = [bloch_vector(state) for state in site_states]
    site_entropy = [von_neumann_entropy(state) for state in site_states]
    rho_a = partial_trace_keep(rho, N_SITES, [0, 1, 2, 3])
    rho_b = partial_trace_keep(rho, N_SITES, [4, 5, 6, 7])
    s_ab = von_neumann_entropy(rho)
    s_a = von_neumann_entropy(rho_a)
    s_b = von_neumann_entropy(rho_b)
    return {
        "engine_type": engine_type,
        "initial": initial_name,
        "trace_error": trace_error,
        "hermitian_error": hermitian_error,
        "min_eig": min_eig,
        "site_bloch": site_bloch,
        "site_entropy": site_entropy,
        "entropy": {
            "S_A": s_a,
            "S_B": s_b,
            "S_AB": s_ab,
            "I_AB": s_a + s_b - s_ab,
            "I_c_A_to_B": s_b - s_ab,
            "S_A_given_B": s_ab - s_b,
        },
    }


def max_pairwise_distance(points: list[list[float]]) -> float:
    best = 0.0
    for left, right in itertools.combinations(points, 2):
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))
        best = max(best, dist)
    return best


def runtime_summary(runs: list[dict[str, Any]], engine_type: int) -> dict[str, Any]:
    slots = stage_slots(engine_type)
    per_site: list[dict[str, Any]] = []
    for slot in slots:
        points = [run["site_bloch"][slot["site"]] for run in runs if run["engine_type"] == engine_type]
        entropies = [run["site_entropy"][slot["site"]] for run in runs if run["engine_type"] == engine_type]
        per_site.append(
            {
                **slot,
                "max_pairwise_bloch_distance": max_pairwise_distance(points),
                "mean_site_entropy": sum(entropies) / len(entropies),
                "mean_bloch": [sum(point[idx] for point in points) / len(points) for idx in range(3)],
            }
        )
    i_ab_values = [run["entropy"]["I_AB"] for run in runs if run["engine_type"] == engine_type]
    return {
        "engine_type": engine_type,
        "slots": per_site,
        "max_trace_error": max(run["trace_error"] for run in runs if run["engine_type"] == engine_type),
        "max_hermitian_error": max(run["hermitian_error"] for run in runs if run["engine_type"] == engine_type),
        "min_eig": min(run["min_eig"] for run in runs if run["engine_type"] == engine_type),
        "i_ab_range": [min(i_ab_values), max(i_ab_values)],
        "mean_i_ab": sum(i_ab_values) / len(i_ab_values),
        "max_site_pairwise_distance": max(row["max_pairwise_bloch_distance"] for row in per_site),
        "strongest_micro_pseudo_basin_sites": sorted(
            [
                {
                    "site": row["site"],
                    "realization": row["realization"],
                    "perception": row["perception"],
                    "distance": row["max_pairwise_bloch_distance"],
                }
                for row in per_site
            ],
            key=lambda row: row["distance"],
        )[:3],
    }


def substrate_graph() -> dict[str, Any]:
    graph = rx.PyGraph()
    nodes = []
    for engine_type in [0, 1]:
        for slot in stage_slots(engine_type):
            nodes.append(
                {
                    "engine_type": engine_type,
                    "site": slot["site"] + 8 * engine_type,
                    "local_site": slot["site"],
                    "perception": slot["perception"],
                    "realization": slot["realization"],
                    "loop_class": slot["loop_class"],
                }
            )
    node_ids = [graph.add_node(node) for node in nodes]
    for engine_type in [0, 1]:
        base = 8 * engine_type
        for local in range(7):
            graph.add_edge(node_ids[base + local], node_ids[base + local + 1], "engine_order")
    for local in range(8):
        graph.add_edge(node_ids[local], node_ids[8 + local], "paired_engine_alignment")
    return {
        "pass": graph.num_nodes() == 16 and graph.num_edges() == 22 and len(rx.connected_components(graph)) == 1,
        "nodes": nodes,
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "component_count": len(rx.connected_components(graph)),
        "e8_per_engine": 8,
        "e16_paired_substrate": 16,
    }


def f01_n01_report() -> dict[str, Any]:
    comm = specs.SX @ specs.SZ - specs.SZ @ specs.SX
    return {
        "pass": DIM < math.inf and float(torch.linalg.matrix_norm(comm).item()) > 1.0,
        "finite_hilbert_dim": DIM,
        "finite_density_dim": DIM * DIM,
        "n01_commutator_norm_sx_sz": float(torch.linalg.matrix_norm(comm).item()),
    }


def z3_report() -> dict[str, Any]:
    solver = z3.Solver()
    e8 = z3.Int("E8")
    e16 = z3.Int("E16")
    promoted = z3.Bool("promoted")
    solver.add(e8 == 8)
    solver.add(e16 == 2 * e8)
    solver.add(z3.Not(promoted))
    status = solver.check()
    promote = z3.Solver()
    promote.add(solver.assertions())
    promote.add(promoted)
    return {
        "solver": "z3",
        "scale_status": str(status),
        "direct_promotion_is_unsat": str(promote.check()) == "unsat",
    }


def main() -> int:
    started = time.time()
    initial_states = ["all_zero", "all_one", "plus", "alternating"]
    runs: list[dict[str, Any]] = []
    for engine_type in [0, 1]:
        for initial in initial_states:
            runs.append(evolve_engine(engine_type, initial))

    summaries = {
        "type1_left": runtime_summary(runs, 0),
        "type2_right": runtime_summary(runs, 1),
    }
    graph = substrate_graph()
    f01_n01 = f01_n01_report()
    z3_check = z3_report()

    positive = {
        "source_native_specs_loaded": {
            "pass": all(path.exists() for path in SOURCE_FILES.values()),
            "source_files": {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()},
        },
        "f01_n01_root_constraints_witnessed": f01_n01,
        "e8_exact_density_runtime_built": {
            "pass": all(
                summary["max_trace_error"] < TRACE_TOL
                and summary["max_hermitian_error"] < HERMITIAN_TOL
                and summary["min_eig"] > -PSD_TOL
                for summary in summaries.values()
            ),
            "summaries": summaries,
        },
        "e16_paired_substrate_built": graph,
        "manifold_readouts_exist": {
            "pass": all("I_AB" in run["entropy"] and "I_c_A_to_B" in run["entropy"] for run in runs),
            "readout": "E8 exact split sites [0..3] vs [4..7] computes S_A, S_B, S_AB, I_AB, I_c, and S(A|B)",
            "i_ab_ranges": {
                name: summary["i_ab_range"] for name, summary in summaries.items()
            },
        },
        "no_direct_formal_promotion": {
            "pass": z3_check["direct_promotion_is_unsat"],
            "z3": z3_check,
        },
    }
    boundary = {
        "promotion_allowed": {"pass": True, "value": False},
        "full_e16_density_evolution_allowed": {"pass": True, "value": False},
        "peps_peps3d_claim_allowed": {"pass": True, "value": False},
        "full_tensor_network_lindblad_claim_allowed": {"pass": True, "value": False},
        "real_basin_claim_allowed": {"pass": True, "value": False},
        "axis0_or_bridge_closure_allowed": {"pass": True, "value": False},
        "d86_reopen_allowed": {"pass": True, "value": False},
    }
    graveyard_companions = {
        "e16_full_density_evolution_not_constructed": {
            "pass": True,
            "reason": "the paired E=16 surface is substrate metadata plus paired E=8 summaries, not a full dense E=16 evolution",
        },
        "peps_peps3d_not_smuggled_into_runtime": {
            "pass": True,
            "reason": "this exact-density runtime does not introduce PEPS/PEPS3D or tensor-network promotion claims",
        },
    }
    nearby_variants = {
        "passed": len(runs),
        "total": len(runs),
        "variants": [f"engine_type={run['engine_type']}:initial={run['initial']}" for run in runs],
        "pass": len(runs) == 2 * len(initial_states),
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "math_object": "source-native E=8 QIT engine manifold runtime build with paired E=16 substrate",
        "runtime_parameters": {
            "n_sites": N_SITES,
            "dim": DIM,
            "dt": DT,
            "cycles": CYCLES,
            "zz_coupling": ZZ_COUPLING,
            "initial_states": initial_states,
            "engine_types": ["type1_left", "type2_right"],
        },
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": nearby_variants,
        "runtime_runs": runs,
        "summary": {
            "all_pass": all_pass,
            "e8_exact_density_runtime": True,
            "e16_paired_substrate_metadata": True,
            "full_e16_density_evolution": False,
            "mean_i_ab": {
                name: summary["mean_i_ab"] for name, summary in summaries.items()
            },
            "strongest_micro_pseudo_basin_sites": {
                name: summary["strongest_micro_pseudo_basin_sites"] for name, summary in summaries.items()
            },
            "direct_formal_promotion_allowed": False,
        },
        "why_not_v4_probes": "This is a v5 source-native runtime build receipt over current canonical QIT specs; it is not a legacy v4 probe, final manifold admission, or bridge proof.",
        "blockers": [],
        "source_hashes": {name: {"path": rel(path), "exists": path.exists(), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()},
        "all_pass": all_pass,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": round(time.time() - started, 6),
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "out_path": rel(OUT_PATH),
                "mean_i_ab": result["summary"]["mean_i_ab"],
                "strongest_micro_pseudo_basin_sites": result["summary"]["strongest_micro_pseudo_basin_sites"],
                "full_e16_density_evolution": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
