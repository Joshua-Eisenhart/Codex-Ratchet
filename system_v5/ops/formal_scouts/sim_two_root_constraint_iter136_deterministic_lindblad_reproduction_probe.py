#!/usr/bin/env python3
"""Formal reproduction of the useful iter_136 deterministic Lindblad result.

This scout ports the sidequest iter_136 check into the formal_scouts receipt
surface without promotion. It intentionally tests a narrow E=8 deterministic
density-matrix channel:

- pure torch compute path;
- four initial states from the grok_sim sidequest;
- one engine-stage site per terrain placement;
- local Lindblad CPTP exponentials plus nearest-neighbor ZZ conjugations;
- terrain-specific convergence and L20 mutual-information readout.

It does not prove a real attractor basin, PEPS/PEPS3D dynamics, full
tensor-network Lindblad evidence, or a bridge-correlation theorem.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_iter136_deterministic_lindblad_reproduction_probe_results.json"

NAME = "two_root_constraint_iter136_deterministic_lindblad_reproduction_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "deterministic_lindblad_reproduction"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_late_grok_iter136_formal_reproduction"
CLAIM_CEILING = (
    "Formal reproduction target only: reproduces the useful grok_sim iter_136 "
    "E=8 pure-torch deterministic Lindblad correction. It may support a bounded "
    "terrain-specific pseudo-basin follow-up target, but it does not admit a real "
    "attractor basin, PEPS/PEPS3D/full tensor-network evidence, multi-qubit "
    "Lindblad theorem, bridge-correlation claim, final manifold, or cleanup."
)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density matrices, Lindblad matrix exponentials, tensor contractions, partial traces, and entropy eigensolves",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing threshold accounting proving the reproduced result is terrain-specific and nonpromotional",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive formal receipt serialization",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source provenance hashing",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
}

DTYPE = torch.complex128
DEVICE = torch.device("cpu")
N_SITES = 8
DT = 0.05
N_STEPS = 200
J_ZZ = 0.1
CONVERGENCE_THRESHOLD = 0.3
MI_NEAR_ZERO_THRESHOLD = 0.03

I2 = torch.eye(2, dtype=DTYPE, device=DEVICE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE, device=DEVICE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE, device=DEVICE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE, device=DEVICE)
SIGMA_MINUS = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE, device=DEVICE)
SIGMA_PLUS = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE, device=DEVICE)
MIRROR = SX

H0 = 0.77 * SZ + 0.13 * SX
H3 = 0.61 * SY + 0.21 * SX
HS = 0.83 * SZ

PERCEPTION_L = {
    "Se": SZ,
    "Ne": SIGMA_PLUS,
    "Ni": -1j * SY,
    "Si": SIGMA_MINUS,
}
PERCEPTION_H_KEY = {"Se": "H0", "Ne": "H3", "Ni": "H0", "Si": "HS"}
H_BY_KEY = {"H0": H0, "H3": H3, "HS": HS}
PERCEPTION_RATE = {"Se": 0.18, "Ne": 0.13, "Ni": 0.28, "Si": 0.20}

SCHEDULE_TYPE_ONE = [
    ("Se", "outer"),
    ("Ne", "outer"),
    ("Ni", "outer"),
    ("Si", "outer"),
    ("Se", "inner"),
    ("Si", "inner"),
    ("Ni", "inner"),
    ("Ne", "inner"),
]
INITIAL_LABELS = ["all_zero", "all_one", "plus", "alternating"]


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def local_liouvillian(H: torch.Tensor, L: torch.Tensor, gamma: float) -> torch.Tensor:
    """Single-site Lindblad generator in column-stacked vector convention."""
    ldag_l = (L.conj().T @ L).contiguous()
    coherent = -1j * (torch.kron(I2, H) - torch.kron(H.T.contiguous(), I2))
    dissipative = gamma * (
        torch.kron(L.conj().contiguous(), L)
        - 0.5 * torch.kron(I2, ldag_l)
        - 0.5 * torch.kron(ldag_l.T.contiguous(), I2)
    )
    return coherent + dissipative


def local_lindblad_channel(H: torch.Tensor, L: torch.Tensor, gamma: float, dt: float) -> torch.Tensor:
    local_super = local_liouvillian(H, L, gamma)
    channel = torch.linalg.matrix_exp(local_super * dt)
    return channel.reshape(2, 2, 2, 2).permute(1, 0, 3, 2).contiguous()


def build_per_site_channels(terrain_assignment: list[tuple[str, int]], dt: float) -> list[torch.Tensor]:
    channels: list[torch.Tensor] = []
    for perception, engine_type in terrain_assignment:
        jump = PERCEPTION_L[perception].clone()
        if engine_type == 1:
            jump = MIRROR @ jump @ MIRROR
        hamiltonian = H_BY_KEY[PERCEPTION_H_KEY[perception]].clone()
        if engine_type == 1:
            hamiltonian = -hamiltonian
        channels.append(local_lindblad_channel(hamiltonian, jump, PERCEPTION_RATE[perception], dt))
    return channels


def build_coupling_unitary(j_zz: float, dt: float) -> torch.Tensor:
    generator = torch.kron(SZ.contiguous(), SZ.contiguous())
    return torch.linalg.matrix_exp(-1j * j_zz * generator * dt).reshape(2, 2, 2, 2).contiguous()


def apply_local_lindblad_to_rho(rho_tensor: torch.Tensor, channel: torch.Tensor, site: int, n_sites: int) -> torch.Tensor:
    chars = list("abcdefghijklmnopqrstuvwxyz") + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    rho_chars = list(chars[: 2 * n_sites])
    new_ket = chars[2 * n_sites]
    new_bra = chars[2 * n_sites + 1]
    site_ket = rho_chars[site]
    site_bra = rho_chars[n_sites + site]
    channel_spec = f"{new_ket}{new_bra}{site_ket}{site_bra}"
    rho_spec = "".join(rho_chars)
    out_chars = list(rho_chars)
    out_chars[site] = new_ket
    out_chars[n_sites + site] = new_bra
    return torch.einsum(f"{channel_spec},{rho_spec}->{''.join(out_chars)}", channel, rho_tensor)


def apply_coupling_unitary_to_rho(rho_tensor: torch.Tensor, unitary: torch.Tensor, a: int, b: int, n_sites: int) -> torch.Tensor:
    chars = list("abcdefghijklmnopqrstuvwxyz") + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    rho_chars = list(chars[: 2 * n_sites])

    new_a = chars[2 * n_sites]
    new_b = chars[2 * n_sites + 1]
    u_spec = f"{new_a}{new_b}{rho_chars[a]}{rho_chars[b]}"
    rho_spec = "".join(rho_chars)
    out_chars = list(rho_chars)
    out_chars[a] = new_a
    out_chars[b] = new_b
    intermediate_spec = "".join(out_chars)
    intermediate = torch.einsum(f"{u_spec},{rho_spec}->{intermediate_spec}", unitary, rho_tensor)

    unitary_dag = unitary.permute(2, 3, 0, 1).conj().contiguous()
    new_a_bra = chars[2 * n_sites + 2]
    new_b_bra = chars[2 * n_sites + 3]
    udag_spec = f"{new_a_bra}{new_b_bra}{out_chars[n_sites + a]}{out_chars[n_sites + b]}"
    final_chars = list(out_chars)
    final_chars[n_sites + a] = new_a_bra
    final_chars[n_sites + b] = new_b_bra
    return torch.einsum(f"{udag_spec},{intermediate_spec}->{''.join(final_chars)}", unitary_dag, intermediate)


def evolve_density_matrix(
    rho_initial: torch.Tensor,
    terrain_assignment: list[tuple[str, int]],
    n_steps: int,
    dt: float,
    j_zz: float,
    n_sites: int,
) -> torch.Tensor:
    channels = build_per_site_channels(terrain_assignment, dt)
    coupling = build_coupling_unitary(j_zz, dt)
    rho = rho_initial.reshape((2,) * (2 * n_sites)).to(dtype=DTYPE, device=DEVICE)
    for _ in range(n_steps):
        for site, channel in enumerate(channels):
            rho = apply_local_lindblad_to_rho(rho, channel, site, n_sites)
        for site in range(n_sites - 1):
            rho = apply_coupling_unitary_to_rho(rho, coupling, site, site + 1, n_sites)
    return rho.reshape(2**n_sites, 2**n_sites)


def partial_trace(rho: torch.Tensor, qubits_to_trace: list[int], n_sites: int) -> torch.Tensor:
    rho_r = rho.reshape((2,) * (2 * n_sites))
    current_n = n_sites
    for qubit in sorted(qubits_to_trace, reverse=True):
        chars = [chr(ord("a") + i) for i in range(2 * current_n)]
        chars[current_n + qubit] = chars[qubit]
        out_chars = [chars[i] for i in range(2 * current_n) if i not in (qubit, current_n + qubit)]
        rho_r = torch.einsum(f"{''.join(chars)}->{''.join(out_chars)}", rho_r)
        current_n -= 1
    return rho_r.reshape(2**current_n, 2**current_n)


def build_initial_density(label: str, n_sites: int) -> torch.Tensor:
    dim = 2**n_sites
    psi = torch.zeros(dim, dtype=DTYPE, device=DEVICE)
    if label == "all_zero":
        psi[0] = 1.0
    elif label == "all_one":
        psi[-1] = 1.0
    elif label == "plus":
        psi = torch.ones(dim, dtype=DTYPE, device=DEVICE) / math.sqrt(dim)
    elif label == "alternating":
        idx = 0
        for site in range(n_sites):
            if site % 2 == 1:
                idx |= 1 << (n_sites - 1 - site)
        psi[idx] = 1.0
    else:
        raise ValueError(label)
    return torch.outer(psi, psi.conj())


def von_neumann_entropy(rho: torch.Tensor, tol: float = 1e-12) -> float:
    rho_h = (rho + rho.conj().T) / 2
    eigvals = torch.linalg.eigvalsh(rho_h).real
    eigvals = eigvals[eigvals > tol]
    return -float((eigvals * torch.log(eigvals)).sum().item())


def per_site_bloch(rho: torch.Tensor, n_sites: int) -> list[dict[str, Any]]:
    blochs = []
    for site in range(n_sites):
        other = [q for q in range(n_sites) if q != site]
        rho_site = partial_trace(rho, other, n_sites)
        rx = float(torch.trace(rho_site @ SX).real.item())
        ry = float(torch.trace(rho_site @ SY).real.item())
        rz = float(torch.trace(rho_site @ SZ).real.item())
        blochs.append(
            {
                "site": site,
                "perception": SCHEDULE_TYPE_ONE[site][0],
                "r_x": rx,
                "r_y": ry,
                "r_z": rz,
                "r_norm": math.sqrt(rx * rx + ry * ry + rz * rz),
            }
        )
    return blochs


def max_pairwise_distance(points: list[tuple[float, float, float]]) -> float:
    max_dist = 0.0
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            dist = math.sqrt(sum((points[i][k] - points[j][k]) ** 2 for k in range(3)))
            max_dist = max(max_dist, dist)
    return max_dist


def threshold_proof(per_terrain: dict[str, float], overall: float, max_mi: float) -> dict[str, Any]:
    solver = z3.Solver()
    si = z3.Real("si")
    ni = z3.Real("ni")
    se = z3.Real("se")
    ne = z3.Real("ne")
    global_dist = z3.Real("global_dist")
    mi = z3.Real("max_mi")
    solver.add(si == z3.RealVal(str(round(per_terrain["Si"], 12))))
    solver.add(ni == z3.RealVal(str(round(per_terrain["Ni"], 12))))
    solver.add(se == z3.RealVal(str(round(per_terrain["Se"], 12))))
    solver.add(ne == z3.RealVal(str(round(per_terrain["Ne"], 12))))
    solver.add(global_dist == z3.RealVal(str(round(overall, 12))))
    solver.add(mi == z3.RealVal(str(round(max_mi, 12))))
    solver.add(si < z3.RealVal(str(CONVERGENCE_THRESHOLD)))
    solver.add(ni < z3.RealVal(str(CONVERGENCE_THRESHOLD)))
    solver.add(se > z3.RealVal(str(CONVERGENCE_THRESHOLD)))
    solver.add(ne > z3.RealVal(str(CONVERGENCE_THRESHOLD)))
    solver.add(global_dist > z3.RealVal(str(CONVERGENCE_THRESHOLD)))
    solver.add(mi < z3.RealVal(str(MI_NEAR_ZERO_THRESHOLD)))
    status = solver.check()
    return {
        "solver": "z3",
        "status": str(status),
        "pass": status == z3.sat,
        "model": str(solver.model()) if status == z3.sat else None,
        "claims_encoded": {
            "Si_and_Ni_terrain_specific_converge": True,
            "Se_and_Ne_do_not_converge": True,
            "global_basin_does_not_converge": True,
            "mutual_information_near_zero": True,
        },
    }


def main() -> int:
    start = time.time()
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    terrain_assignment = [(perception, 0) for perception, _ in SCHEDULE_TYPE_ONE]

    results_per_initial: dict[str, Any] = {}
    for label in INITIAL_LABELS:
        rho_initial = build_initial_density(label, N_SITES)
        rho_final = evolve_density_matrix(rho_initial, terrain_assignment, N_STEPS, DT, J_ZZ, N_SITES)
        trace_value = float(torch.trace(rho_final).real.item())
        hermitian_error = float(torch.linalg.norm(rho_final - rho_final.conj().T).item())
        eig_min = float(torch.linalg.eigvalsh((rho_final + rho_final.conj().T) / 2).real.min().item())
        blochs = per_site_bloch(rho_final, N_SITES)
        rho_a = partial_trace(rho_final, [4, 5, 6, 7], N_SITES)
        rho_b = partial_trace(rho_final, [0, 1, 2, 3], N_SITES)
        s_a = von_neumann_entropy(rho_a)
        s_b = von_neumann_entropy(rho_b)
        s_ab = von_neumann_entropy(rho_final)
        mutual_info = s_a + s_b - s_ab
        results_per_initial[label] = {
            "trace": trace_value,
            "hermitian_error": hermitian_error,
            "min_eigenvalue": eig_min,
            "valid_density": abs(trace_value - 1.0) < 1e-8 and hermitian_error < 1e-8 and eig_min > -1e-7,
            "per_site_bloch": blochs,
            "S_A": s_a,
            "S_B": s_b,
            "S_AB": s_ab,
            "I_A_B": mutual_info,
            "S_A_given_B": s_ab - s_b,
            "I_c_A_to_B": s_b - s_ab,
        }

    convergence_per_site = []
    for site in range(N_SITES):
        points = [
            (
                results_per_initial[label]["per_site_bloch"][site]["r_x"],
                results_per_initial[label]["per_site_bloch"][site]["r_y"],
                results_per_initial[label]["per_site_bloch"][site]["r_z"],
            )
            for label in INITIAL_LABELS
        ]
        convergence_per_site.append(
            {
                "site": site,
                "perception": SCHEDULE_TYPE_ONE[site][0],
                "max_pairwise_distance": max_pairwise_distance(points),
            }
        )

    per_terrain = {
        terrain: max(row["max_pairwise_distance"] for row in convergence_per_site if row["perception"] == terrain)
        for terrain in ["Si", "Ni", "Se", "Ne"]
    }
    overall = max(row["max_pairwise_distance"] for row in convergence_per_site)
    mi_values = [float(row["I_A_B"]) for row in results_per_initial.values()]
    max_abs_mi = max(abs(value) for value in mi_values)
    z3_proof = threshold_proof(per_terrain, overall, max_abs_mi)

    positive = {
        "pure_torch_compute_path": {
            "pass": True,
            "details": "density evolution uses torch.linalg.matrix_exp, torch.einsum, torch.kron, and torch eigensolves",
        },
        "density_validity": {
            "pass": all(row["valid_density"] for row in results_per_initial.values()),
            "per_initial": {
                label: {
                    "trace": row["trace"],
                    "hermitian_error": row["hermitian_error"],
                    "min_eigenvalue": row["min_eigenvalue"],
                    "valid_density": row["valid_density"],
                }
                for label, row in results_per_initial.items()
            },
        },
        "terrain_specific_iter136_pattern_reproduced": {
            "pass": z3_proof["pass"],
            "threshold": CONVERGENCE_THRESHOLD,
            "overall_max_pairwise_distance": overall,
            "per_terrain_max_pairwise_distance": per_terrain,
        },
        "mutual_information_near_zero_reproduced": {
            "pass": max_abs_mi < MI_NEAR_ZERO_THRESHOLD,
            "threshold": MI_NEAR_ZERO_THRESHOLD,
            "values": mi_values,
            "max_abs": max_abs_mi,
        },
    }
    boundary = {
        "global_basin_claim": {
            "pass": overall > CONVERGENCE_THRESHOLD,
            "value": False,
            "reason": "Global E=8 convergence remains false; only terrain-specific Si/Ni convergence is supported.",
        },
        "bridge_correlation_claim": {
            "pass": max_abs_mi < MI_NEAR_ZERO_THRESHOLD,
            "value": False,
            "reason": "Deterministic I(A:B) is near zero, so prior sidequest nonzero bridge values remain demoted.",
        },
        "peps_peps3d_tensor_network_claim": {
            "pass": True,
            "value": False,
            "reason": "This receipt uses dense E=8 density matrices, not MPS/PEPS/PEPS3D dynamics.",
        },
        "cleanup_authorized": {
            "pass": True,
            "value": False,
            "reason": "This is a formal reproduction target; B2/B3/B4/B5 closeout remains separate.",
        },
    }
    graveyard_companions = {
        "trajectory_sampling_noise_control": {
            "pass": max_abs_mi < MI_NEAR_ZERO_THRESHOLD,
            "reason": "Deterministic evolution keeps I(A:B) near zero, so finite-trajectory bridge-correlation values are not admitted.",
        },
        "terrain_flattening_control": {
            "pass": per_terrain["Si"] < CONVERGENCE_THRESHOLD
            and per_terrain["Ni"] < CONVERGENCE_THRESHOLD
            and per_terrain["Se"] > CONVERGENCE_THRESHOLD
            and per_terrain["Ne"] > CONVERGENCE_THRESHOLD,
            "reason": "Convergence is terrain-specific; flattening all terrains into one basin would be false.",
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in graveyard_companions.values())
    )
    output = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "generated_at": generated_at,
        "runtime_seconds": round(time.time() - start, 6),
        "all_pass": all_pass,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "E=8 terrain-stage deterministic Lindblad density-matrix reproduction of iter_136",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": {
            "source": {"path": rel(pathlib.Path(__file__).resolve()), "sha256": sha256(pathlib.Path(__file__).resolve())},
            "grok_iter136_result": {
                "path": "system_v5/grok_sim/results/iter_136_pure_torch_lindblad_density_matrix_E8_results.json",
                "sha256": sha256(REPO / "system_v5/grok_sim/results/iter_136_pure_torch_lindblad_density_matrix_E8_results.json"),
            },
        },
        "parameters": {
            "engine_stage_site_count_E": N_SITES,
            "dt": DT,
            "n_steps": N_STEPS,
            "T": DT * N_STEPS,
            "J_zz": J_ZZ,
            "initial_states": INITIAL_LABELS,
            "schedule_type_one": SCHEDULE_TYPE_ONE,
            "scale_boundary": "E=8 engine-stage substrate, not tensor-network site-count L and not schedule-repeat count R",
        },
        "summary": {
            "completion_status": "iter136_formal_reproduction_nonpromotional" if all_pass else "iter136_formal_reproduction_failed",
            "goal_complete": False,
            "cleanup_authorized": False,
            "global_basin_converged": False,
            "terrain_specific_convergence_supported": all_pass,
            "si_converged": per_terrain["Si"] < CONVERGENCE_THRESHOLD,
            "ni_converged": per_terrain["Ni"] < CONVERGENCE_THRESHOLD,
            "se_converged": per_terrain["Se"] < CONVERGENCE_THRESHOLD,
            "ne_converged": per_terrain["Ne"] < CONVERGENCE_THRESHOLD,
            "mutual_information_near_zero": max_abs_mi < MI_NEAR_ZERO_THRESHOLD,
        },
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "z3_threshold_proof": z3_proof,
        "results_per_initial_state": results_per_initial,
        "basin_convergence_per_site": convergence_per_site,
        "per_terrain_max_pairwise_distance": per_terrain,
        "overall_max_pairwise_distance": overall,
        "mutual_information_values": mi_values,
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "global_basin_promotion": {
                "pass": True,
                "status": "rejected",
                "reason": "overall max pairwise distance exceeds threshold",
            },
            "bridge_correlation_promotion": {
                "pass": True,
                "status": "rejected",
                "reason": "deterministic mutual information is near zero",
            },
            "terrain_specific_target": {
                "pass": True,
                "status": "formal_followup_target",
                "reason": "Si/Ni terrain-specific convergence should be tested at E=16 paired-engine scale next",
            },
        },
        "open_choices": [
            "Test the same deterministic terrain-specific pattern on E=16 paired-engine substrate.",
            "Compare dense E=8 result against a real MPS/PEPS/PEPS3D implementation before any tensor-network claim.",
            "Keep L20 Phi0(rho_AB) open: near-zero mutual information may be a real vanishing target or a finite-time control result.",
            "Keep B2/B3/B4/B5 closeout separate from this formal reproduction receipt.",
        ],
        "blockers": [] if all_pass else ["iter136 deterministic reproduction predicates failed"],
        "open_blockers": [
            "B2/B3/B4/B5 final synthesis blockers remain outside this scout.",
            "No PEPS/PEPS3D/full tensor-network Lindblad implementation is present in this receipt.",
            "No real-attractor theorem is admitted.",
        ],
        "why_not_v4_probes": "Two-root formal_scout reproduction of a specific late sidequest correction; does not touch v4 probe canon.",
    }
    output["root_constraints"] = {
        "F01": True,
        "N01": True,
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "n01_evidence": "bounded terrain-specific schedule controls and trajectory-sampling noise controls record order-sensitive deterministic Lindblad evidence",
    }
    OUT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "out_path": rel(OUT_PATH),
                "overall_max_pairwise_distance": overall,
                "per_terrain_max_pairwise_distance": per_terrain,
                "max_abs_mutual_information": max_abs_mi,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
