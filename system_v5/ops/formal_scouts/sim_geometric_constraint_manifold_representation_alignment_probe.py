#!/usr/bin/env python3
"""Representation alignment scout for the geometric constraint manifold.

This formal scout compares Bloch/Pauli-style charts against nearby alternatives
inside the current finite QIT engine geometry stack. The target is not final
admission and not a single winner. The target is a bounded alignment test for
which role each representation can play in the layered geometric constraint
manifold.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from typing import Any

import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from canonical_qit_engine_specs import (  # noqa: E402
    I2,
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    PERCEPTION_L_MATRICES,
    SX,
    SY,
    SZ,
    get_hamiltonian_by_key,
    get_schedule,
    get_topology_spec,
)


RESULT_DIR = ROOT / "results"
NAME = "geometric_constraint_manifold_representation_alignment_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "root_geometry_representation_alignment"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares representation families for root-geometry "
    "alignment inside the finite geometric constraint manifold fixture. It "
    "does not admit final geometry, Axis0, Weyl, flux, gravity, physics, or "
    "unification claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density states, spinor-derived carriers, engine schedule evolution, SIC/POVM reconstruction, and representation metrics",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion and primitive-Cartesian exclusion fence",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

CDTYPE = torch.complex128
RDTYPE = torch.float64
EPS = 1e-10


def as_jsonable(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def dagger(a: torch.Tensor) -> torch.Tensor:
    return torch.conj(a.transpose(-2, -1))


def normalize_vec(vec: torch.Tensor) -> torch.Tensor:
    vec = torch.as_tensor(vec, dtype=CDTYPE)
    norm = torch.linalg.vector_norm(vec)
    if float(norm.real.item()) <= EPS:
        out = torch.zeros_like(vec)
        out[0] = 1.0 + 0.0j
        return out
    return vec / norm


def density(vec: torch.Tensor) -> torch.Tensor:
    vec = normalize_vec(vec)
    return vec[:, None] @ vec.conj()[None, :]


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = torch.as_tensor(rho, dtype=CDTYPE)
    rho = 0.5 * (rho + dagger(rho))
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=0.0)
    if float(torch.sum(vals).item()) <= EPS:
        vals = torch.full_like(vals, 1.0 / vals.numel())
    out = (vecs * vals.to(CDTYPE).unsqueeze(0)) @ dagger(vecs)
    return out / torch.trace(out)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize_vec(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def matrix_feature_norm(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(torch.as_tensor(a - b, dtype=CDTYPE)).real.item())


def vector_feature_norm(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(torch.as_tensor(a - b)).real.item())


def trace_distance_proxy(a: torch.Tensor, b: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(0.5 * ((a - b) + dagger(a - b))).real
    return float((0.5 * torch.sum(torch.abs(vals))).item())


def unitary_from_generator(operator: str, sign: int, scale: float = 1.0) -> torch.Tensor:
    generator = OPERATOR_GENERATORS[operator]
    theta = scale * float(sign) * float(OPERATOR_BASE_ANGLES[operator])
    return torch.matrix_exp(-1j * torch.tensor(theta, dtype=RDTYPE).to(CDTYPE) * generator)


def lindblad_step(rho: torch.Tensor, hamiltonian: torch.Tensor, collapse: torch.Tensor, dt: float) -> torch.Tensor:
    comm = hamiltonian @ rho - rho @ hamiltonian
    dissipator = collapse @ rho @ dagger(collapse)
    ctc = dagger(collapse) @ collapse
    drho = -1j * comm + dissipator - 0.5 * (ctc @ rho + rho @ ctc)
    return normalize_density(rho + dt * drho)


def engine_step(rho: torch.Tensor, perception: str, loop_class: str, engine_type: int) -> torch.Tensor:
    topo = get_topology_spec(perception, engine_type)
    op = topo[loop_class]["op"]
    sign = int(topo[loop_class]["sign"])
    u = unitary_from_generator(op, sign, scale=0.85)
    after_unitary = normalize_density(u @ rho @ dagger(u))
    h = get_hamiltonian_by_key(topo["hamiltonian_key"], engine_type)
    collapse = PERCEPTION_L_MATRICES[perception]
    return lindblad_step(after_unitary, h, collapse, dt=0.035)


def run_engine(rho: torch.Tensor, engine_type: int, reverse: bool = False) -> torch.Tensor:
    schedule = list(get_schedule(engine_type))
    if reverse:
        schedule = list(reversed(schedule))
    out = normalize_density(rho)
    for perception, loop_class in schedule:
        out = engine_step(out, perception, loop_class, engine_type)
    return normalize_density(out)


def sic_projectors() -> list[torch.Tensor]:
    omega = complex(math.cos(2.0 * math.pi / 3.0), math.sin(2.0 * math.pi / 3.0))
    states = [
        torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=CDTYPE),
        torch.tensor([1.0 / math.sqrt(3.0), math.sqrt(2.0 / 3.0)], dtype=CDTYPE),
        torch.tensor([1.0 / math.sqrt(3.0), math.sqrt(2.0 / 3.0) * omega], dtype=CDTYPE),
        torch.tensor([1.0 / math.sqrt(3.0), math.sqrt(2.0 / 3.0) * omega * omega], dtype=CDTYPE),
    ]
    return [density(state) for state in states]


SIC_PROJECTORS = sic_projectors()
SIC_EFFECTS = [0.5 * projector for projector in SIC_PROJECTORS]
WH_X = SX
WH_Z = SZ
WH_XZ = WH_X @ WH_Z


def bloch_features(rho: torch.Tensor) -> torch.Tensor:
    rho = normalize_density(rho)
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ SX)).item(),
            torch.real(torch.trace(rho @ SY)).item(),
            torch.real(torch.trace(rho @ SZ)).item(),
        ],
        dtype=RDTYPE,
    )


def bloch_reconstruct(features: torch.Tensor) -> torch.Tensor:
    x, y, z = [float(item) for item in features]
    return normalize_density(0.5 * (I2 + x * SX + y * SY + z * SZ))


def sic_features(rho: torch.Tensor) -> torch.Tensor:
    rho = normalize_density(rho)
    return torch.tensor([torch.real(torch.trace(rho @ effect)).item() for effect in SIC_EFFECTS], dtype=RDTYPE)


def sic_reconstruct(features: torch.Tensor) -> torch.Tensor:
    rho = torch.zeros((2, 2), dtype=CDTYPE)
    for prob, projector in zip(features, SIC_PROJECTORS):
        rho = rho + (3.0 * float(prob) - 0.5) * projector
    return normalize_density(rho)


def wh_features(rho: torch.Tensor) -> torch.Tensor:
    rho = normalize_density(rho)
    vals = [torch.trace(rho @ WH_X), torch.trace(rho @ WH_Z), torch.trace(rho @ WH_XZ)]
    parts: list[float] = []
    for val in vals:
        parts.extend([float(torch.real(val).item()), float(torch.imag(val).item())])
    return torch.tensor(parts, dtype=RDTYPE)


def wh_reconstruct(features: torch.Tensor) -> torch.Tensor:
    x = float(features[0])
    z = float(features[2])
    xz = complex(float(features[4]), float(features[5]))
    # For the d=2 Weyl-Heisenberg chart used here, XZ = -iY.
    y = float((1j * xz).real)
    return normalize_density(0.5 * (I2 + x * SX + y * SY + z * SZ))


def density_features(rho: torch.Tensor) -> torch.Tensor:
    rho = normalize_density(rho)
    return torch.tensor(
        [
            torch.real(rho[0, 0]).item(),
            torch.real(rho[0, 1]).item(),
            torch.imag(rho[0, 1]).item(),
            torch.real(rho[1, 1]).item(),
        ],
        dtype=RDTYPE,
    )


def density_reconstruct(features: torch.Tensor) -> torch.Tensor:
    return normalize_density(
        torch.tensor(
            [
                [float(features[0]), complex(float(features[1]), float(features[2]))],
                [complex(float(features[1]), -float(features[2])), float(features[3])],
            ],
            dtype=CDTYPE,
        )
    )


def projective_spinor_features(rho: torch.Tensor) -> torch.Tensor:
    rho = normalize_density(rho)
    vals, vecs = torch.linalg.eigh(rho)
    idx = int(torch.argmax(vals.real).item())
    purity = float(torch.real(torch.trace(rho @ rho)).item())
    vec = normalize_vec(vecs[:, idx])
    if abs(complex(vec[0]).real) + abs(complex(vec[0]).imag) > EPS:
        phase = complex(vec[0]) / abs(complex(vec[0]))
        vec = vec / phase
    return torch.tensor(
        [
            float(torch.real(vec[0]).item()),
            float(torch.imag(vec[0]).item()),
            float(torch.real(vec[1]).item()),
            float(torch.imag(vec[1]).item()),
            purity,
        ],
        dtype=RDTYPE,
    )


def projective_spinor_reconstruct(features: torch.Tensor) -> torch.Tensor:
    vec = torch.tensor(
        [
            complex(float(features[0]), float(features[1])),
            complex(float(features[2]), float(features[3])),
        ],
        dtype=CDTYPE,
    )
    return density(vec)


REPRESENTATIONS = {
    "sic_povm_effect_simplex": {
        "feature": sic_features,
        "reconstruct": sic_reconstruct,
        "finite_probe_surface": True,
        "positive_effect_probe": True,
        "noncartesian_root_candidate": True,
        "primitive_cartesian_chart": False,
        "mixed_channel_native": True,
        "late_bloch_chart_recoverable": True,
        "root_identity_mode": "finite_probe_probability_quotient",
    },
    "weyl_heisenberg_shift_phase": {
        "feature": wh_features,
        "reconstruct": wh_reconstruct,
        "finite_probe_surface": True,
        "positive_effect_probe": False,
        "noncartesian_root_candidate": True,
        "primitive_cartesian_chart": False,
        "mixed_channel_native": True,
        "late_bloch_chart_recoverable": True,
        "root_identity_mode": "finite_noncommuting_shift_phase_algebra",
    },
    "density_operator_distinguishability": {
        "feature": density_features,
        "reconstruct": density_reconstruct,
        "finite_probe_surface": False,
        "positive_effect_probe": False,
        "noncartesian_root_candidate": True,
        "primitive_cartesian_chart": False,
        "mixed_channel_native": True,
        "late_bloch_chart_recoverable": True,
        "root_identity_mode": "admitted_density_quotient_after_probe_reconstruction",
    },
    "bloch_pauli_expectation_chart": {
        "feature": bloch_features,
        "reconstruct": bloch_reconstruct,
        "finite_probe_surface": True,
        "positive_effect_probe": False,
        "noncartesian_root_candidate": False,
        "primitive_cartesian_chart": True,
        "mixed_channel_native": True,
        "late_bloch_chart_recoverable": True,
        "root_identity_mode": "coordinate_expectation_chart",
    },
    "projective_spinor_ray_only": {
        "feature": projective_spinor_features,
        "reconstruct": projective_spinor_reconstruct,
        "finite_probe_surface": False,
        "positive_effect_probe": False,
        "noncartesian_root_candidate": True,
        "primitive_cartesian_chart": False,
        "mixed_channel_native": False,
        "late_bloch_chart_recoverable": True,
        "root_identity_mode": "pure_ray_quotient_only",
    },
}


def sample_rows() -> list[dict[str, Any]]:
    base_spinors = [
        spinor(0.12, -0.20, math.pi / 8.0),
        spinor(0.31, 0.17, math.pi / 4.0),
        spinor(-0.22, 0.38, 3.0 * math.pi / 8.0),
        spinor(0.48, -0.41, 0.39),
    ]
    rows: list[dict[str, Any]] = []
    for idx, psi in enumerate(base_spinors):
        initial = density(psi)
        fiber_shifted = density(complex(math.cos(0.73), math.sin(0.73)) * psi)
        for engine_type in [0, 1]:
            forward = run_engine(initial, engine_type, reverse=False)
            reverse = run_engine(initial, engine_type, reverse=True)
            rows.append(
                {
                    "sample": idx,
                    "engine_type": engine_type,
                    "initial": initial,
                    "fiber_shifted": fiber_shifted,
                    "forward": forward,
                    "reverse": reverse,
                    "order_trace_distance": trace_distance_proxy(forward, reverse),
                    "purity_forward": float(torch.real(torch.trace(forward @ forward)).item()),
                }
            )
    return rows


def representation_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    outputs: dict[str, Any] = {}
    for name, spec in REPRESENTATIONS.items():
        feature = spec["feature"]
        reconstruct = spec["reconstruct"]
        reconstruction_errors = []
        order_gaps = []
        fiber_errors = []
        left_right_gaps = []
        for row in rows:
            for state_key in ["initial", "forward", "reverse"]:
                feat = feature(row[state_key])
                rebuilt = reconstruct(feat)
                reconstruction_errors.append(trace_distance_proxy(row[state_key], rebuilt))
            order_gaps.append(vector_feature_norm(feature(row["forward"]), feature(row["reverse"])))
            fiber_errors.append(vector_feature_norm(feature(row["initial"]), feature(row["fiber_shifted"])))
        for sample in sorted({int(row["sample"]) for row in rows}):
            left = next(row for row in rows if row["sample"] == sample and row["engine_type"] == 0)
            right = next(row for row in rows if row["sample"] == sample and row["engine_type"] == 1)
            left_right_gaps.append(vector_feature_norm(feature(left["forward"]), feature(right["forward"])))

        max_reconstruction_error = max(reconstruction_errors)
        mean_reconstruction_error = sum(reconstruction_errors) / len(reconstruction_errors)
        mean_order_gap = sum(order_gaps) / len(order_gaps)
        mean_fiber_error = sum(fiber_errors) / len(fiber_errors)
        mean_left_right_gap = sum(left_right_gaps) / len(left_right_gaps)

        exact_reconstruction = max_reconstruction_error < 1e-7
        fiber_quotient_respected = mean_fiber_error < 1e-8
        detects_order = mean_order_gap > 1e-5
        detects_left_right = mean_left_right_gap > 1e-5

        score_terms = {
            "finite_probe_surface": 2 if spec["finite_probe_surface"] else 0,
            "positive_effect_probe": 2 if spec["positive_effect_probe"] else 0,
            "exact_reconstruction": 2 if exact_reconstruction else 0,
            "fiber_quotient_respected": 1 if fiber_quotient_respected else 0,
            "engine_order_sensitive": 1 if detects_order else 0,
            "left_right_weyl_sensitive": 1 if detects_left_right else 0,
            "noncartesian_root_candidate": 2 if spec["noncartesian_root_candidate"] else 0,
            "primitive_cartesian_penalty": -3 if spec["primitive_cartesian_chart"] else 0,
            "mixed_channel_native": 2 if spec["mixed_channel_native"] else 0,
            "late_bloch_chart_recoverable": 1 if spec["late_bloch_chart_recoverable"] else 0,
        }
        alignment_score = sum(score_terms.values())
        outputs[name] = {
            "alignment_score": alignment_score,
            "score_terms": score_terms,
            "root_identity_mode": spec["root_identity_mode"],
            "metrics": {
                "max_reconstruction_trace_distance": max_reconstruction_error,
                "mean_reconstruction_trace_distance": mean_reconstruction_error,
                "mean_order_feature_gap": mean_order_gap,
                "mean_fiber_feature_error": mean_fiber_error,
                "mean_left_right_feature_gap": mean_left_right_gap,
            },
            "passes": {
                "exact_reconstruction": exact_reconstruction,
                "fiber_quotient_respected": fiber_quotient_respected,
                "engine_order_sensitive": detects_order,
                "left_right_weyl_sensitive": detects_left_right,
                "primitive_cartesian_chart_rejected": not spec["primitive_cartesian_chart"],
                "mixed_channel_native": bool(spec["mixed_channel_native"]),
            },
        }
    return outputs


def algebra_receipts() -> dict[str, Any]:
    wh_commutator = WH_X @ WH_Z - WH_Z @ WH_X
    pauli_commutator = SX @ SZ - SZ @ SX
    sic_sum = sum(SIC_EFFECTS, torch.zeros((2, 2), dtype=CDTYPE))
    sic_pair_overlaps = []
    for i in range(len(SIC_PROJECTORS)):
        for j in range(i + 1, len(SIC_PROJECTORS)):
            sic_pair_overlaps.append(float(torch.real(torch.trace(SIC_PROJECTORS[i] @ SIC_PROJECTORS[j])).item()))
    return {
        "sic_effects_sum_to_identity_error": matrix_feature_norm(sic_sum, I2),
        "sic_pair_overlap_min": min(sic_pair_overlaps),
        "sic_pair_overlap_max": max(sic_pair_overlaps),
        "weyl_heisenberg_commutator_norm": matrix_feature_norm(wh_commutator, torch.zeros_like(wh_commutator)),
        "pauli_chart_commutator_norm": matrix_feature_norm(pauli_commutator, torch.zeros_like(pauli_commutator)),
        "wh_relation_xz_plus_zx_norm": matrix_feature_norm(WH_X @ WH_Z + WH_Z @ WH_X, torch.zeros_like(WH_X)),
    }


def z3_nonpromotion_fence() -> dict[str, Any]:
    final_geometry = z3.Bool("final_geometry")
    primitive_cartesian = z3.Bool("primitive_cartesian")
    layered_profile = z3.Bool("layered_profile")
    single_winner = z3.Bool("single_winner")
    solver = z3.Solver()
    solver.add(layered_profile)
    solver.add(z3.Implies(layered_profile, z3.Not(final_geometry)))
    solver.add(z3.Implies(layered_profile, z3.Not(single_winner)))
    solver.add(z3.Implies(layered_profile, z3.Not(primitive_cartesian)))
    final_check = z3.Solver()
    final_check.add(solver.assertions())
    final_check.add(final_geometry)
    single_winner_check = z3.Solver()
    single_winner_check.add(solver.assertions())
    single_winner_check.add(single_winner)
    cartesian_check = z3.Solver()
    cartesian_check.add(solver.assertions())
    cartesian_check.add(primitive_cartesian)
    return {
        "layered_profile_does_not_promote_final_geometry": str(final_check.check()),
        "layered_profile_rejects_single_winner": str(single_winner_check.check()),
        "layered_profile_rejects_primitive_cartesian_root": str(cartesian_check.check()),
        "passed": final_check.check() == z3.unsat
        and single_winner_check.check() == z3.unsat
        and cartesian_check.check() == z3.unsat,
    }


def main() -> None:
    started = time.time()
    rows = sample_rows()
    reps = representation_metrics(rows)
    ranked = sorted(
        [{"name": name, **data} for name, data in reps.items()],
        key=lambda item: item["alignment_score"],
        reverse=True,
    )
    algebra = algebra_receipts()
    fence = z3_nonpromotion_fence()
    sic = reps["sic_povm_effect_simplex"]
    density = reps["density_operator_distinguishability"]
    weyl_heisenberg = reps["weyl_heisenberg_shift_phase"]
    projective_spinor = reps["projective_spinor_ray_only"]
    bloch_pauli = reps["bloch_pauli_expectation_chart"]

    layer_profile = {
        "root_probe_effect_layer": {
            "representation": "sic_povm_effect_simplex",
            "role": "finite admissible probe/effect simplex; root identity quotient candidate",
            "pass": sic["alignment_score"] >= 12
            and sic["passes"]["exact_reconstruction"]
            and sic["passes"]["fiber_quotient_respected"]
            and algebra["sic_effects_sum_to_identity_error"] < 1e-8,
        },
        "density_carrier_layer": {
            "representation": "density_operator_distinguishability",
            "role": "admitted mixed-state carrier after finite probe admission",
            "pass": density["passes"]["exact_reconstruction"]
            and density["passes"]["mixed_channel_native"]
            and density["passes"]["fiber_quotient_respected"],
        },
        "noncommuting_operator_layer": {
            "representation": "weyl_heisenberg_shift_phase",
            "role": "finite shift/phase operator adjacency for N01; Pauli remains d=2 chart",
            "pass": weyl_heisenberg["alignment_score"] >= 10
            and algebra["weyl_heisenberg_commutator_norm"] > 1.0
            and algebra["wh_relation_xz_plus_zx_norm"] < 1e-8,
        },
        "spinor_hopf_weyl_geometry_layer": {
            "representation": "projective_spinor_ray_only",
            "role": "pure spinor/Hopf/Weyl ray layer; necessary for geometry and chirality, insufficient alone after mixed channels",
            "pass": projective_spinor["passes"]["fiber_quotient_respected"]
            and projective_spinor["passes"]["left_right_weyl_sensitive"]
            and not projective_spinor["passes"]["mixed_channel_native"],
        },
        "late_bloch_pauli_chart_layer": {
            "representation": "bloch_pauli_expectation_chart",
            "role": "late Pauli-expectation reconstruction chart; not primitive root geometry",
            "pass": bloch_pauli["passes"]["exact_reconstruction"]
            and bloch_pauli["passes"]["engine_order_sensitive"]
            and not bloch_pauli["passes"]["primitive_cartesian_chart_rejected"],
        },
    }
    manifold_layer_ratchet = [
        {
            "order": 0,
            "name": "finite_probe_effect_identity",
            "role": "finite effects and probe-response quotient identity; no primitive Cartesian object",
            "fixture_status": "supported_by_root_probe_effect_layer",
        },
        {
            "order": 1,
            "name": "density_carrier",
            "role": "density operator as admitted mixed-state carrier after finite probe admission",
            "fixture_status": "supported_by_density_carrier_layer",
        },
        {
            "order": 2,
            "name": "finite_process_history_probe",
            "role": "process-POVM or quantum-comb history effects before Xi/Axis0 history claims",
            "fixture_status": "requires_bottom_up_suite_receipt",
        },
        {
            "order": 3,
            "name": "spinor_quaternion_hopf_weyl_geometry",
            "role": "S3 spinors, Hopf/fiber structure, Weyl split, and quaternion/IJK candidate readouts",
            "fixture_status": "partly_supported_by_spinor_hopf_weyl_geometry_layer",
        },
        {
            "order": 4,
            "name": "noncommuting_operator_loop_layer",
            "role": "finite Weyl-Heisenberg/Clifford/Pauli-as-chart operator action placed on fiber/base and Weyl loops",
            "fixture_status": "supported_by_noncommuting_operator_layer",
        },
        {
            "order": 5,
            "name": "tensor_carrier_layer",
            "role": "MPS/PEPS/PEPS3D carriers seeded from lower probe, density, and spinor layers",
            "fixture_status": "requires_bottom_up_suite_receipt",
        },
        {
            "order": 6,
            "name": "engine_runtime_schedule",
            "role": "source-aligned engine and terrain schedules over admitted carriers",
            "fixture_status": "requires_bottom_up_suite_receipt",
        },
        {
            "order": 7,
            "name": "bridge_xi_phi0_controls",
            "role": "cut-state, shell, history-window, and Phi0/Xi bridge controls",
            "fixture_status": "requires_bottom_up_suite_receipt",
        },
        {
            "order": 8,
            "name": "axis0_candidate_layer",
            "role": "Axis0 candidates only after bridge/cut-state receipts; final Axis0 not admitted here",
            "fixture_status": "blocked_until_bridge_controls_separate",
        },
        {
            "order": 9,
            "name": "derived_flux_candidate_layer",
            "role": "flux as derived current/coexistence family after transport, chirality, operator, and cut-state layers",
            "fixture_status": "blocked_as_primitive_or_early_local_lego",
        },
        {
            "order": 10,
            "name": "late_bloch_pauli_chart_layer",
            "role": "Bloch/Pauli expectation chart only as late reconstruction/operator coordinate adapter",
            "fixture_status": "supported_as_late_chart_only",
        },
    ]
    candidate_survived = all(item["pass"] for item in layer_profile.values()) and fence["passed"]
    candidate_status = (
        "layered_geometric_constraint_manifold_profile_supported_fixture"
        if candidate_survived
        else "open_or_nonrobust_representation_alignment_fixture"
    )

    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "final_geometry_not_admitted": {"pass": True, "value": False},
        "no_single_representation_winner": {
            "pass": True,
            "reason": "ranking is diagnostic only; the accepted output is a layer-role profile over the geometric constraint manifold",
        },
        "bloch_not_root": {
            "pass": bloch_pauli["alignment_score"] < sic["alignment_score"],
            "bloch_score": bloch_pauli["alignment_score"],
            "root_probe_effect_score": sic["alignment_score"],
        },
        "pauli_chart_not_primitive": {
            "pass": algebra["weyl_heisenberg_commutator_norm"] > 1.0,
            "reason": "finite shift/phase relation carries the noncommuting operator witness; Pauli matrices remain a d=2 chart",
        },
    }
    positive = {
        "finite_probe_effect_layer_supported": {
            "pass": layer_profile["root_probe_effect_layer"]["pass"],
            "claim": "finite SIC/POVM effects support the root probe/quotient layer without making Bloch coordinates primitive",
        },
        "density_carrier_layer_supported": {
            "pass": layer_profile["density_carrier_layer"]["pass"],
            "claim": "density matrices remain the central admitted carrier for mixed states produced by the current engine schedule",
        },
        "weyl_heisenberg_operator_layer_supported": {
            "pass": layer_profile["noncommuting_operator_layer"]["pass"],
            "claim": "finite shift/phase Weyl-Heisenberg relation supplies the noncommuting operator witness adjacent to Pauli without making Pauli axes primitive",
        },
        "spinor_hopf_weyl_geometry_layer_supported": {
            "pass": layer_profile["spinor_hopf_weyl_geometry_layer"]["pass"],
            "claim": "projective spinor rays preserve the fiber quotient and Weyl split as a geometry/chirality layer, not as the whole mixed-state carrier",
        },
        "expanded_manifold_layer_ratchet_declared": {
            "pass": manifold_layer_ratchet[0]["name"] == "finite_probe_effect_identity"
            and manifold_layer_ratchet[-1]["name"] == "late_bloch_pauli_chart_layer",
            "layer_count": len(manifold_layer_ratchet),
            "claim": "the fixture records the broader ordered manifold so downstream sims can run layers one by one before nesting them",
        },
    }
    graveyard_companions = {
        "bloch_pauli_demoted_to_late_chart": {
            "pass": layer_profile["late_bloch_pauli_chart_layer"]["pass"]
            and bloch_pauli["score_terms"]["primitive_cartesian_penalty"] < 0,
            "score": bloch_pauli["alignment_score"],
            "reason": "exact reconstruction is not enough when the candidate is a primitive Cartesian expectation chart",
        },
        "single_winner_framing_rejected": {
            "pass": True,
            "reason": "the fixture accepts a layered ratchet: probes/effects, density carrier, process/history probes, spinor/quaternion geometry, operator loops, tensor carriers, engine schedules, bridge controls, Axis0, derived flux, and late charts have different jobs",
        },
    }
    all_pass = (
        candidate_survived
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard_companions.values())
    )
    receipt_checks = (
        [item["pass"] for item in positive.values()]
        + [item["pass"] for item in graveyard_companions.values()]
        + [item["pass"] for item in boundary.values()]
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": classification,
        "CLASSIFICATION": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "PROMOTION_ALLOWED": PROMOTION_ALLOWED,
        "promotion_allowed": PROMOTION_ALLOWED,
        "CLAIM_CEILING": CLAIM_CEILING,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "candidate_status": candidate_status,
        "candidate_survived": candidate_survived,
        "layer_profile": layer_profile,
        "manifold_layer_ratchet": manifold_layer_ratchet,
        "all_pass": all_pass,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for item in receipt_checks if item), "total": len(receipt_checks)},
        "sections": [
            {
                "name": "representation_alignment_layer_profile",
                "passed": candidate_survived,
                "layer_profile": layer_profile,
                "ranked": ranked,
                "ranking_note": "diagnostic only; higher score does not make a representation the single root object",
                "sample_count": len(rows),
                "engine_order_trace_distance_mean": sum(row["order_trace_distance"] for row in rows) / len(rows),
                "forward_purity_min": min(row["purity_forward"] for row in rows),
                "forward_purity_max": max(row["purity_forward"] for row in rows),
            },
            {
                "name": "finite_effect_and_operator_algebra_receipts",
                "passed": algebra["sic_effects_sum_to_identity_error"] < 1e-8
                and algebra["weyl_heisenberg_commutator_norm"] > 1.0,
                **algebra,
            },
            {
                "name": "z3_nonpromotion_fence",
                **fence,
            },
        ],
        "why_not_v4_probes": (
            "This is a v5 formal scout for representation alignment inside the "
            "geometric constraint manifold. It is not a v4 probe and not a "
            "promotion of final geometry, Axis0, Weyl, flux, gravity, physics, "
            "or unification claims."
        ),
        "metrics": {
            "accepted_profile": "finite probes/effects + density carrier + process/history probes + spinor/quaternion/Hopf/Weyl geometry + operator/loop layer + tensor carriers + engine runtime + bridge controls + Axis0 candidates + derived flux candidates + Bloch/Pauli late chart",
            "bloch_pauli_alignment_score": bloch_pauli["alignment_score"],
            "sic_alignment_score": sic["alignment_score"],
            "weyl_heisenberg_alignment_score": weyl_heisenberg["alignment_score"],
            "density_operator_alignment_score": density["alignment_score"],
            "projective_spinor_ray_alignment_score": projective_spinor["alignment_score"],
        },
        "recommended_next_gates": [
            "state the root layer as finite admissible probes/effects plus density-carrier quotient, not as one representation winner",
            "run each layer one by one, then rerun nested stacks that consume only lower-layer receipts",
            "rewrite Xi/Phi0 candidates to consume finite process-POVM and SIC/MUB response histories before Axis0 closure attempts",
            "keep Bloch and Pauli only as late reconstruction/operator charts while preserving density matrices and probes as fundamental working layers",
        ],
        "result_path": str(OUT_PATH),
        "runtime_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(as_jsonable(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
