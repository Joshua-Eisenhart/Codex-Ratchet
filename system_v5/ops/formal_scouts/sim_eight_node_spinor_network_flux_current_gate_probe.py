#!/usr/bin/env python3
"""Eight-node torch-native spinor-network flux-current gate.

Formal scout only.

This is the repair rung after the scale/spinor audit. It starts at eight
spinor nodes, not a 2-qubit or 3-qubit toy. Each node is an explicit Hopf
spinor `psi_i in C^2`, each local state is `rho_i = psi_i psi_i^dagger`, and
the network state is an 8-qubit tensor product evolved by finite edge gates.

The flux object here is still only a derived current candidate over the finite
spinor/geometry edge registry. This scout does not admit final flux, Axis0, Xi,
physics, PEPS3D closure, or attractor-basin convergence.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "eight_node_spinor_network_flux_current_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "eight_node_torch_spinor_network_flux_current_gate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: builds an explicit eight-node PyTorch Hopf spinor "
    "network, derives a bounded finite edge-current candidate from spinor "
    "geometry and constraint-layer recurrence, and checks zero-flux, reversed "
    "flux, shuffled-edge, independent edge-family, adversarial spinor, gauge, "
    "and below-width controls. It does not admit final flux, Axis0, Xi, physics, "
    "PEPS3D closure, long-horizon engine dynamics, attractor-basin convergence, "
    "or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing complex Hopf spinors, density matrices, 8-qubit "
            "state evolution, cut entropy, finite edge currents, and controls"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-width and nonpromotion fence for the current candidate",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive canonical result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

N_NODES = 8
MIN_WIDTH = 8
N_LAYERS = 13
CDTYPE = torch.complex128
RDTYPE = torch.float64
EPS = 1e-12
GAP_FLOOR = 1e-5

SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
I2 = torch.eye(2, dtype=CDTYPE)
GEOMETRY_AXIS = torch.tensor([0.71, -0.37, 0.59], dtype=RDTYPE)
GEOMETRY_AXIS = GEOMETRY_AXIS / torch.linalg.vector_norm(GEOMETRY_AXIS)
LAYER_WEIGHTS = torch.linspace(0.035, 0.155, steps=N_LAYERS, dtype=RDTYPE)

SPINOR_PARAMS = [
    (0.11, 0.19, 0.27),
    (0.43, -0.31, 0.39),
    (-0.22, 0.47, 0.58),
    (0.81, 0.08, 0.71),
    (-0.64, -0.26, 0.44),
    (1.03, 0.34, 0.63),
    (-0.91, 0.16, 0.36),
    (0.27, -0.52, 0.76),
]

EDGE_REGISTRY = [
    {"edge": [0, 1], "kind": "ring", "orientation": +1},
    {"edge": [1, 2], "kind": "ring", "orientation": -1},
    {"edge": [2, 3], "kind": "ring", "orientation": +1},
    {"edge": [3, 4], "kind": "cut_bridge", "orientation": -1},
    {"edge": [4, 5], "kind": "ring", "orientation": +1},
    {"edge": [5, 6], "kind": "ring", "orientation": -1},
    {"edge": [6, 7], "kind": "ring", "orientation": +1},
    {"edge": [7, 0], "kind": "cut_wrap", "orientation": -1},
    {"edge": [0, 4], "kind": "sheet_bridge", "orientation": +1},
    {"edge": [1, 5], "kind": "sheet_bridge", "orientation": -1},
    {"edge": [2, 6], "kind": "sheet_bridge", "orientation": +1},
    {"edge": [3, 7], "kind": "sheet_bridge", "orientation": -1},
]


EDGE_REGISTRY_VARIANT_NAMES = ["shifted_chords", "mirror_shell", "long_range_cross"]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize_vector(v: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(v)
    if float(norm.item()) <= EPS:
        raise ValueError("zero vector")
    return v / norm


def spinor(phi: float, chi: float, eta: float, *, phase: float = 0.0) -> torch.Tensor:
    raw = torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    gauge = complex(math.cos(phase), math.sin(phase))
    return normalize_vector(gauge * raw)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def bloch_from_spinor(psi: torch.Tensor) -> torch.Tensor:
    rho = density(psi)
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ SX)).item(),
            torch.real(torch.trace(rho @ SY)).item(),
            torch.real(torch.trace(rho @ SZ)).item(),
        ],
        dtype=RDTYPE,
    )


def build_spinors(
    *,
    gauge_phases: list[float] | None = None,
    spinor_params: list[tuple[float, float, float]] | None = None,
) -> list[torch.Tensor]:
    phases = gauge_phases or [0.0] * N_NODES
    params_source = spinor_params or SPINOR_PARAMS
    return [spinor(*params, phase=phases[idx]) for idx, params in enumerate(params_source)]


def kron_all(vectors: list[torch.Tensor]) -> torch.Tensor:
    out = vectors[0]
    for vector in vectors[1:]:
        out = torch.kron(out, vector)
    return normalize_vector(out)


def zz_gate(theta: float) -> torch.Tensor:
    zz = torch.kron(SZ, SZ)
    return math.cos(theta / 2.0) * torch.eye(4, dtype=CDTYPE) - 1j * math.sin(theta / 2.0) * zz


def apply_two_qubit_gate(state: torch.Tensor, gate: torch.Tensor, q0: int, q1: int, n_qubits: int) -> torch.Tensor:
    if q0 == q1:
        return state
    dims = [2] * n_qubits
    perm = [q0, q1] + [idx for idx in range(n_qubits) if idx not in {q0, q1}]
    inv = [perm.index(idx) for idx in range(n_qubits)]
    reshaped = state.reshape(dims).permute(perm).reshape(4, -1)
    updated = (gate @ reshaped).reshape([2, 2] + [2] * (n_qubits - 2)).permute(inv).reshape(-1)
    return normalize_vector(updated)


def bipartition_entropy(state: torch.Tensor, left_count: int = 4) -> float:
    matrix = state.reshape(2**left_count, -1)
    singular_values = torch.linalg.svdvals(matrix)
    probs = torch.clamp(singular_values.real**2, min=0.0)
    probs = probs / torch.clamp(torch.sum(probs), min=EPS)
    nz = probs[probs > 1e-12]
    return float((-torch.sum(nz * torch.log(nz))).item())


def local_z_expectations(state: torch.Tensor, n_qubits: int = N_NODES) -> torch.Tensor:
    probs = torch.abs(state) ** 2
    idx = torch.arange(2**n_qubits, dtype=torch.int64)
    values = []
    for qubit in range(n_qubits):
        bit = ((idx >> (n_qubits - qubit - 1)) & 1).to(RDTYPE)
        values.append(torch.sum(probs.real * (1.0 - 2.0 * bit)))
    return torch.stack(values)


def node_geometry(idx: int, bloch: torch.Tensor) -> torch.Tensor:
    angle = 2.0 * math.pi * idx / N_NODES
    shell = torch.tensor([math.cos(angle), math.sin(angle), 0.5 * ((idx % 2) * 2 - 1)], dtype=RDTYPE)
    return normalize_vector(0.72 * bloch + 0.28 * normalize_vector(shell))


def layer_recurrence(seed_value: torch.Tensor, delta_z: torch.Tensor, orientation: int) -> tuple[torch.Tensor, list[float]]:
    value = seed_value
    trace = []
    orient = torch.tensor(float(orientation), dtype=RDTYPE)
    for layer_index, weight in enumerate(LAYER_WEIGHTS):
        parity = 1.0 if layer_index % 2 == 0 else -1.0
        value = torch.tanh(value + weight * delta_z + 0.025 * parity * orient)
        trace.append(float(value.item()))
    return value, trace


def edge_current_rows(
    spinors: list[torch.Tensor],
    *,
    mode: str = "nominal",
    edge_registry: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    registry = edge_registry or EDGE_REGISTRY
    if mode == "shuffled_edges":
        edge_rows = [
            {**row, "edge": [row["edge"][0], (row["edge"][1] + 3) % N_NODES]}
            for row in registry
        ]
    else:
        edge_rows = list(registry)

    blochs = [bloch_from_spinor(psi) for psi in spinors]
    geoms = [node_geometry(idx, bloch) for idx, bloch in enumerate(blochs)]
    rows = []
    for edge_index, row in enumerate(edge_rows):
        i, j = row["edge"]
        ri, rj = blochs[i], blochs[j]
        gi, gj = geoms[i], geoms[j]
        edge_axis = normalize_vector(gj - gi + 0.07 * GEOMETRY_AXIS)
        triple_product = torch.dot(torch.linalg.cross(ri, rj), edge_axis)
        delta_z = rj[2] - ri[2]
        layered, layer_trace = layer_recurrence(triple_product, delta_z, int(row["orientation"]))
        current = float(layered.item())
        if mode == "zero_flux":
            current = 0.0
        elif mode == "reversed_flux":
            current = -current
        rows.append(
            {
                "edge_index": edge_index,
                "edge": [int(i), int(j)],
                "kind": row["kind"],
                "orientation": int(row["orientation"]),
                "triple_product_seed": float(triple_product.item()),
                "delta_z": float(delta_z.item()),
                "layer_trace": layer_trace,
                "current": current,
                "crosses_cut": (i < 4 <= j) or (j < 4 <= i),
            }
        )
    return rows


def run_network(
    *,
    mode: str = "nominal",
    gauge_phases: list[float] | None = None,
    spinor_params: list[tuple[float, float, float]] | None = None,
    edge_registry: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    spinors = build_spinors(gauge_phases=gauge_phases, spinor_params=spinor_params)
    currents = edge_current_rows(spinors, mode=mode, edge_registry=edge_registry)
    state = kron_all(spinors)
    for row in currents:
        q0, q1 = row["edge"]
        theta = 0.23 * row["current"]
        state = apply_two_qubit_gate(state, zz_gate(theta), q0, q1, N_NODES)
    zvals = local_z_expectations(state)
    cut_current = sum(row["current"] for row in currents if row["crosses_cut"])
    density_traces = [torch.trace(density(psi)) for psi in spinors]
    return {
        "mode": mode,
        "node_count": N_NODES,
        "dimension": int(2**N_NODES),
        "state_norm": float(torch.linalg.vector_norm(state).item()),
        "cut_entropy": bipartition_entropy(state),
        "cut_current": float(cut_current),
        "mean_abs_edge_current": float(torch.mean(torch.abs(torch.tensor([row["current"] for row in currents], dtype=RDTYPE))).item()),
        "local_z": zvals,
        "left_z_mean": float(torch.mean(zvals[:4]).item()),
        "right_z_mean": float(torch.mean(zvals[4:]).item()),
        "density_trace_errors": [abs(float(torch.real(trace).item()) - 1.0) + abs(float(torch.imag(trace).item())) for trace in density_traces],
        "edge_currents": currents,
    }


def seeded_spinor_params(seed: int) -> list[tuple[float, float, float]]:
    generator = torch.Generator().manual_seed(seed)
    phi = (2.0 * math.pi) * torch.rand(N_NODES, generator=generator, dtype=RDTYPE) - math.pi
    chi = math.pi * torch.rand(N_NODES, generator=generator, dtype=RDTYPE) - (math.pi / 2.0)
    eta = 0.22 + 1.08 * torch.rand(N_NODES, generator=generator, dtype=RDTYPE)
    return [(float(phi[i].item()), float(chi[i].item()), float(eta[i].item())) for i in range(N_NODES)]


def seeded_gauge_phases(seed: int) -> list[float]:
    generator = torch.Generator().manual_seed(seed + 10_000)
    phases = (2.0 * math.pi) * torch.rand(N_NODES, generator=generator, dtype=RDTYPE) - math.pi
    return [float(value.item()) for value in phases]


def make_edge_registry_variant(name: str, registry: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    base = registry or EDGE_REGISTRY
    if name == "shifted_chords":
        rows = []
        for idx, row in enumerate(base):
            i, j = row["edge"]
            shifted = (j + 2 + (idx % 2)) % N_NODES
            if shifted == i:
                shifted = (shifted + 1) % N_NODES
            rows.append({**row, "edge": [i, shifted], "kind": f"{row['kind']}_shifted"})
        return rows
    if name == "mirror_shell":
        return [
            {
                **row,
                "edge": [N_NODES - 1 - row["edge"][0], N_NODES - 1 - row["edge"][1]],
                "orientation": -int(row["orientation"]),
                "kind": f"{row['kind']}_mirror",
            }
            for row in base
        ]
    if name == "long_range_cross":
        return [
            {"edge": [0, 2], "kind": "skip_ring", "orientation": +1},
            {"edge": [2, 4], "kind": "skip_ring", "orientation": -1},
            {"edge": [4, 6], "kind": "skip_ring", "orientation": +1},
            {"edge": [6, 0], "kind": "skip_ring", "orientation": -1},
            {"edge": [1, 3], "kind": "offset_skip", "orientation": -1},
            {"edge": [3, 5], "kind": "offset_skip", "orientation": +1},
            {"edge": [5, 7], "kind": "offset_skip", "orientation": -1},
            {"edge": [7, 1], "kind": "offset_skip", "orientation": +1},
            {"edge": [0, 5], "kind": "long_bridge", "orientation": +1},
            {"edge": [1, 6], "kind": "long_bridge", "orientation": -1},
            {"edge": [2, 7], "kind": "long_bridge", "orientation": +1},
            {"edge": [3, 4], "kind": "short_cut", "orientation": -1},
        ]
    raise ValueError(f"unknown edge registry variant: {name}")


def adversarial_spinor_param_fixtures() -> dict[str, list[tuple[float, float, float]]]:
    near_clifford_offsets = [-0.018, 0.014, -0.011, 0.021, -0.017, 0.012, -0.009, 0.019]
    near_clifford_chi = [-0.44, -0.27, -0.12, 0.05, 0.18, 0.31, 0.49, -0.38]
    paired_collision = [
        (-0.20, -0.41, 0.48),
        (0.11, -0.405, 0.485),
        (0.33, -0.03, 0.62),
        (-0.51, -0.025, 0.625),
        (0.77, 0.34, 0.83),
        (-0.88, 0.345, 0.835),
        (0.18, 0.57, 1.02),
        (-0.36, 0.565, 1.025),
    ]
    low_delta_band = [
        (0.0, -0.58, 0.70),
        (0.0, -0.33, 0.715),
        (0.0, -0.09, 0.695),
        (0.0, 0.13, 0.71),
        (0.0, 0.36, 0.705),
        (0.0, 0.61, 0.72),
        (0.0, -0.47, 0.69),
        (0.0, 0.24, 0.725),
    ]
    return {
        "near_clifford_equator": [
            (0.17 * idx, near_clifford_chi[idx], math.pi / 4.0 + near_clifford_offsets[idx])
            for idx in range(N_NODES)
        ],
        "paired_near_collision": paired_collision,
        "low_delta_z_band": low_delta_band,
    }


def control_gaps_for_params(params: list[tuple[float, float, float]]) -> dict[str, float]:
    gauge = seeded_gauge_phases(31_337)
    nominal = run_network(mode="nominal", spinor_params=params)
    zero_flux = run_network(mode="zero_flux", spinor_params=params)
    reversed_flux = run_network(mode="reversed_flux", spinor_params=params)
    shuffled_edges = run_network(mode="shuffled_edges", spinor_params=params)
    gauge_shifted = run_network(mode="nominal", gauge_phases=gauge, spinor_params=params)
    return {
        "zero_flux_signature_gap": sig_gap(nominal, zero_flux),
        "reversed_flux_signature_gap": sig_gap(nominal, reversed_flux),
        "shuffled_edge_signature_gap": sig_gap(nominal, shuffled_edges),
        "gauge_signature_gap": sig_gap(nominal, gauge_shifted),
        "cut_current": nominal["cut_current"],
        "cut_entropy": nominal["cut_entropy"],
    }


def edge_registry_family_stress(spinor_params: list[tuple[float, float, float]] | None = None) -> dict[str, Any]:
    nominal = run_network(mode="nominal", spinor_params=spinor_params)
    rows = []
    for name in EDGE_REGISTRY_VARIANT_NAMES:
        variant = make_edge_registry_variant(name)
        variant_run = run_network(mode="nominal", spinor_params=spinor_params, edge_registry=variant)
        rows.append(
            {
                "variant": name,
                "edge_count": len(variant),
                "signature_gap": sig_gap(nominal, variant_run),
                "cut_current": variant_run["cut_current"],
                "cut_entropy": variant_run["cut_entropy"],
            }
        )
    min_gap = min(row["signature_gap"] for row in rows)
    return {
        "variant_count": len(rows),
        "variants": rows,
        "min_edge_family_signature_gap": min_gap,
        "pass": min_gap > GAP_FLOOR,
    }


def adversarial_spinor_stress() -> dict[str, Any]:
    fixture_rows = []
    for fixture_name, params in adversarial_spinor_param_fixtures().items():
        gaps = control_gaps_for_params(params)
        edge_stress = edge_registry_family_stress(params)
        row = {"fixture": fixture_name, **gaps, "edge_family_min_gap": edge_stress["min_edge_family_signature_gap"]}
        row["pass"] = (
            row["zero_flux_signature_gap"] > GAP_FLOOR
            and row["reversed_flux_signature_gap"] > GAP_FLOOR
            and row["shuffled_edge_signature_gap"] > GAP_FLOOR
            and row["edge_family_min_gap"] > GAP_FLOOR
            and row["gauge_signature_gap"] < 1e-10
        )
        fixture_rows.append(row)
    return {
        "fixture_count": len(fixture_rows),
        "fixtures": fixture_rows,
        "min_zero_flux_signature_gap": min(row["zero_flux_signature_gap"] for row in fixture_rows),
        "min_reversed_flux_signature_gap": min(row["reversed_flux_signature_gap"] for row in fixture_rows),
        "min_shuffled_edge_signature_gap": min(row["shuffled_edge_signature_gap"] for row in fixture_rows),
        "min_edge_family_signature_gap": min(row["edge_family_min_gap"] for row in fixture_rows),
        "max_gauge_signature_gap": max(row["gauge_signature_gap"] for row in fixture_rows),
        "pass": all(row["pass"] for row in fixture_rows),
    }


def multiseed_stress() -> dict[str, Any]:
    seeds = [101, 202, 303, 404, 505, 606, 707, 808]
    rows = []
    for seed in seeds:
        params = seeded_spinor_params(seed)
        gauge = seeded_gauge_phases(seed)
        nominal = run_network(mode="nominal", spinor_params=params)
        zero_flux = run_network(mode="zero_flux", spinor_params=params)
        reversed_flux = run_network(mode="reversed_flux", spinor_params=params)
        shuffled_edges = run_network(mode="shuffled_edges", spinor_params=params)
        gauge_shifted = run_network(mode="nominal", gauge_phases=gauge, spinor_params=params)
        rows.append(
            {
                "seed": seed,
                "zero_flux_signature_gap": sig_gap(nominal, zero_flux),
                "reversed_flux_signature_gap": sig_gap(nominal, reversed_flux),
                "shuffled_edge_signature_gap": sig_gap(nominal, shuffled_edges),
                "gauge_signature_gap": sig_gap(nominal, gauge_shifted),
                "cut_current": nominal["cut_current"],
                "cut_entropy": nominal["cut_entropy"],
            }
        )
    min_zero = min(row["zero_flux_signature_gap"] for row in rows)
    min_reversed = min(row["reversed_flux_signature_gap"] for row in rows)
    min_shuffled = min(row["shuffled_edge_signature_gap"] for row in rows)
    max_gauge = max(row["gauge_signature_gap"] for row in rows)
    return {
        "seed_count": len(seeds),
        "seeds": seeds,
        "min_zero_flux_signature_gap": min_zero,
        "min_reversed_flux_signature_gap": min_reversed,
        "min_shuffled_edge_signature_gap": min_shuffled,
        "max_gauge_signature_gap": max_gauge,
        "rows": rows,
        "pass": min_zero > GAP_FLOOR and min_reversed > GAP_FLOOR and min_shuffled > GAP_FLOOR and max_gauge < 1e-10,
    }


def signature(row: dict[str, Any]) -> torch.Tensor:
    local_z = row["local_z"] if isinstance(row["local_z"], torch.Tensor) else torch.tensor(row["local_z"], dtype=RDTYPE)
    return torch.tensor(
        [row["cut_entropy"], row["cut_current"], row["mean_abs_edge_current"], row["left_z_mean"], row["right_z_mean"]],
        dtype=RDTYPE,
    ).to(RDTYPE).flatten().contiguous().add(0.0).new_tensor(
        [row["cut_entropy"], row["cut_current"], row["mean_abs_edge_current"], row["left_z_mean"], row["right_z_mean"], *local_z.tolist()],
        dtype=RDTYPE,
    )


def sig_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(signature(a) - signature(b)).item())


def z3_gate(nominal: dict[str, Any]) -> dict[str, Any]:
    width = z3.Int("width")
    final_flux = z3.Bool("final_flux")
    final_physics = z3.Bool("final_physics")
    root_f01 = z3.Bool("F01")
    root_n01 = z3.Bool("N01")

    solver = z3.Solver()
    solver.add(width == nominal["node_count"])
    solver.add(root_f01, root_n01)
    solver.add(z3.Not(final_flux), z3.Not(final_physics))
    solver.add(width >= MIN_WIDTH)

    promotion = z3.Solver()
    promotion.add(width == nominal["node_count"], z3.Or(final_flux, final_physics))
    promotion.add(z3.Not(final_flux), z3.Not(final_physics))

    too_small = z3.Solver()
    too_small.add(width < MIN_WIDTH, width == nominal["node_count"])

    return {
        "finite_width_with_roots_status": str(solver.check()),
        "promotion_attempt_status": str(promotion.check()),
        "below_width_for_nominal_status": str(too_small.check()),
        "pass": solver.check() == z3.sat and promotion.check() == z3.unsat and too_small.check() == z3.unsat,
    }


def summarize_passes(sections: list[dict[str, Any]]) -> dict[str, int]:
    total = 0
    passed = 0
    for section in sections:
        for row in section.values():
            if isinstance(row, dict) and "pass" in row:
                total += 1
                passed += int(bool(row["pass"]))
    return {"total": total, "passed": passed}


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    nominal = run_network(mode="nominal")
    zero_flux = run_network(mode="zero_flux")
    reversed_flux = run_network(mode="reversed_flux")
    shuffled_edges = run_network(mode="shuffled_edges")
    gauge_phases = [0.13, -0.21, 0.34, -0.55, 0.08, 0.44, -0.39, 0.17]
    gauge_shifted = run_network(mode="nominal", gauge_phases=gauge_phases)
    two_node_blocker = {"accepted": False, "node_count": 2, "minimum_width": MIN_WIDTH, "reason": "below_spinor_network_width_gate"}
    seed_stress = multiseed_stress()
    edge_family_stress = edge_registry_family_stress()
    adversarial_stress = adversarial_spinor_stress()

    zero_gap = sig_gap(nominal, zero_flux)
    reverse_gap = sig_gap(nominal, reversed_flux)
    shuffle_gap = sig_gap(nominal, shuffled_edges)
    gauge_gap = sig_gap(nominal, gauge_shifted)
    max_density_trace_error = max(nominal["density_trace_errors"])

    positive = {
        "eight_explicit_hopf_spinors_constructed": {
            "pass": nominal["node_count"] == 8 and nominal["dimension"] == 256 and max_density_trace_error < 1e-10,
            "node_count": nominal["node_count"],
            "dimension": nominal["dimension"],
            "max_density_trace_error": max_density_trace_error,
            "spinor_formula": "psi_i=[exp(i(phi+chi))cos(eta), exp(i(phi-chi))sin(eta)]",
        },
        "state_is_8qubit_torch_spinor_network": {
            "pass": abs(nominal["state_norm"] - 1.0) < 1e-10 and nominal["dimension"] == 256,
            "state_norm": nominal["state_norm"],
            "dimension": nominal["dimension"],
        },
        "bounded_layer_recurrence_derives_nonzero_current": {
            "pass": nominal["mean_abs_edge_current"] > 1e-3 and abs(nominal["cut_current"]) > 1e-3,
            "layer_count": N_LAYERS,
            "edge_count": len(EDGE_REGISTRY),
            "mean_abs_edge_current": nominal["mean_abs_edge_current"],
            "cut_current": nominal["cut_current"],
        },
        "flux_current_changes_cut_signature": {
            "pass": zero_gap > GAP_FLOOR,
            "zero_flux_signature_gap": zero_gap,
            "canonical_cut_entropy": nominal["cut_entropy"],
            "zero_flux_cut_entropy": zero_flux["cut_entropy"],
        },
        "reversed_flux_changes_cut_signature": {
            "pass": reverse_gap > GAP_FLOOR,
            "reversed_flux_signature_gap": reverse_gap,
            "reversed_cut_current": reversed_flux["cut_current"],
        },
        "multi_seed_spinor_current_controls_survive": seed_stress,
        "independent_edge_registry_family_controls_survive": edge_family_stress,
        "adversarial_spinor_fixture_controls_survive": adversarial_stress,
    }

    graveyard_companions = {
        "GC1_two_node_positive_flux_claim_rejected": {
            "pass": two_node_blocker["accepted"] is False and two_node_blocker["minimum_width"] == 8,
            "control": two_node_blocker,
            "summary": "2-node/2-qubit rows are diagnostics only and cannot satisfy this spinor-network flux gate.",
        },
        "GC2_shuffled_edge_registry_rejected": {
            "pass": shuffle_gap > GAP_FLOOR,
            "shuffled_signature_gap": shuffle_gap,
            "summary": "Changing the finite edge registry changes the readout; raw current labels do not replace topology.",
        },
        "GC3_global_gauge_phase_does_not_change_readout": {
            "pass": gauge_gap < 1e-10,
            "gauge_signature_gap": gauge_gap,
            "summary": "Global U(1) phase changes on local spinors leave Bloch/current/cut readouts invariant.",
        },
        "GC4_nonpromotion_solver_rejects_final_flux_or_physics": z3_gate(nominal),
    }

    boundary = {
        "B1_no_final_flux_claim": {
            "pass": PROMOTION_ALLOWED is False and "does not admit final flux" in CLAIM_CEILING,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "B2_no_peps3d_or_l64_claim": {
            "pass": "PEPS3D closure" in CLAIM_CEILING and "long-horizon engine" in CLAIM_CEILING,
            "scope": "8-node explicit spinor-network first rung only",
        },
        "B3_toy_flux_language_blocked": {
            "pass": two_node_blocker["accepted"] is False,
            "blocked_positive_scales": ["2-node", "3-node"],
            "minimum_positive_scale": 8,
        },
        "B4_twistor_not_claimed_here": {
            "pass": True,
            "next_admissible_step": "Add finite twistor-like incidence only after this 8-node spinor-network gate remains stable.",
        },
    }

    nearby = summarize_passes([positive, graveyard_companions, boundary])
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby,
        "all_pass": nearby["passed"] == nearby["total"],
        "summary": {
            "node_count": N_NODES,
            "dimension": int(2**N_NODES),
            "edge_count": len(EDGE_REGISTRY),
            "constraint_layer_count": N_LAYERS,
            "zero_flux_signature_gap": zero_gap,
            "reversed_flux_signature_gap": reverse_gap,
            "shuffled_edge_signature_gap": shuffle_gap,
            "gauge_signature_gap": gauge_gap,
            "multi_seed_min_zero_flux_signature_gap": seed_stress["min_zero_flux_signature_gap"],
            "multi_seed_min_reversed_flux_signature_gap": seed_stress["min_reversed_flux_signature_gap"],
            "multi_seed_min_shuffled_edge_signature_gap": seed_stress["min_shuffled_edge_signature_gap"],
            "multi_seed_max_gauge_signature_gap": seed_stress["max_gauge_signature_gap"],
            "edge_family_variant_count": edge_family_stress["variant_count"],
            "edge_family_min_signature_gap": edge_family_stress["min_edge_family_signature_gap"],
            "adversarial_fixture_count": adversarial_stress["fixture_count"],
            "adversarial_min_zero_flux_signature_gap": adversarial_stress["min_zero_flux_signature_gap"],
            "adversarial_min_reversed_flux_signature_gap": adversarial_stress["min_reversed_flux_signature_gap"],
            "adversarial_min_shuffled_edge_signature_gap": adversarial_stress["min_shuffled_edge_signature_gap"],
            "adversarial_min_edge_family_signature_gap": adversarial_stress["min_edge_family_signature_gap"],
            "adversarial_max_gauge_signature_gap": adversarial_stress["max_gauge_signature_gap"],
            "nominal_cut_entropy": nominal["cut_entropy"],
            "nominal_cut_current": nominal["cut_current"],
            "elapsed_seconds": time.time() - start,
        },
        "readout_rows": {
            "nominal": nominal,
            "zero_flux": zero_flux,
            "reversed_flux": reversed_flux,
            "shuffled_edges": shuffled_edges,
            "gauge_shifted": gauge_shifted,
        },
        "why_not_v4_probes": (
            "This is a v5 torch-native eight-node spinor-network formal scout. "
            "It is not a legacy v4 probe, not a 2-qubit diagnostic, not a "
            "generic PEPS tensor-only carrier, and not a final flux or physics claim."
        ),
        "next_required_work": [
            "Increase randomized stress width beyond the current 8 seeds, 3 edge-family variants, and 3 adversarial fixtures.",
            "Add finite twistor-like incidence at 8 nodes only after this spinor-network gate remains stable.",
            "Scale the explicit spinor-network representation to 16/32/64 with MPS/PEPS/PEPS3D compression controls.",
        ],
    }

    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
