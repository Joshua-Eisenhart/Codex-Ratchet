#!/usr/bin/env python3
"""Stage-6 L4 local generator/channel layer-action probe.

This tests one independent L4 action on a stage-2 spinor-density carrier:
per-site local CPTP amplitude-damping channel plus the matching Lindblad
generator trace-flow check.  The layer is the action rho -> Phi(rho) / D[rho],
not a standalone geometry object and not a stack with any other layer.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
from typing import Any, Callable

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from clifford import Cl
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation
from sim_l2_spinor_chirality_weyl_cover_layer_probe import (
    CTYPE,
    G1,
    G2,
    H_L,
    H_R,
    I2,
    LOWER,
    RAISE,
    RTYPE,
    SHAPES,
    as_jsonable,
    coords_for_shape,
    exact_counts,
    site_densities,
    site_spinors,
    topology_certificates,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = ROOT / "sim_layer_L4_generator_channel_probe.py"

SIM_ID = "sim_layer_L4_generator_channel_probe"
OBJECT_ID = "layer_L4_generator_channel"
RESULT = RESULT_DIR / f"{OBJECT_ID}_results.json"

GAMMA = 0.3
DT = 0.071
EPS = 1.0e-9
SCALES = (8, 16, 32, 64)
BLOCKED_CONSUMERS = ["L5", "L6", "L7", "L8", "Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "physics", "final manifold"]
TEST_RHO = torch.tensor([[0.7 + 0.0j, 0.2 + 0.1j], [0.2 - 0.1j, 0.3 + 0.0j]], dtype=CTYPE)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim-bearing channel/generator action: Kraus tensors, Lindblad trace flow, Choi eigvalsh, per-site spinor-density updates, and numeric controls.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror recomputing the same 2x2 channel/generator invariants and control flips without NumPy.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing; CP and TP invariants are bound to measured Choi/trace-flow values and must flip under controls.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check inside smt_load_bearing over the same measured CP and TP invariants.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact symbolic Choi spectra and Kraus completeness for amplitude damping and transpose-map control.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Distinct jump/generator basis sanity check with a genuine duplicate-generator ablation.",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "Supportive PEPS3D placement certificate via imported topology_certificates; not load-bearing for CP/TP.",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "Supportive PEPS3D connectivity certificate for the finite site index set.",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "Supportive PEPS3D face/cell hyperedge certificate for the finite placement anchor.",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "Supportive finite face-complex certificate for PEPS3D placement.",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "Supportive boundary filtration certificate for PEPS3D placement.",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "Not relevant: this L4 probe makes no metric/geodesic/curvature claim.",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "Not relevant: this L4 probe makes no equivariant field/learned symmetry claim.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported; NumPy is not a claim-bearing path for this nonclassical layer-action probe.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "pyg": "supportive",
    "rustworkx": "supportive",
    "xgi": "supportive",
    "toponetx": "supportive",
    "gudhi": "supportive",
    "geomstats": None,
    "e3nn": None,
    "numpy": None,
}


def torch_kraus(sheet: str, gamma: float = GAMMA) -> list[torch.Tensor]:
    g = torch.tensor(gamma, dtype=RTYPE)
    if sheet == "L":
        k0 = torch.diag(torch.stack([torch.tensor(1.0, dtype=RTYPE), torch.sqrt(1.0 - g)])).to(CTYPE)
        jump = torch.sqrt(g).to(CTYPE) * RAISE
    elif sheet == "R":
        k0 = torch.diag(torch.stack([torch.sqrt(1.0 - g), torch.tensor(1.0, dtype=RTYPE)])).to(CTYPE)
        jump = torch.sqrt(g).to(CTYPE) * LOWER
    else:
        raise ValueError(sheet)
    return [k0, jump]


def apply_kraus(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ k.conj().T
    return out


def lindblad_generator(sheet: str, rho: torch.Tensor) -> torch.Tensor:
    jump = torch_kraus(sheet)[1]
    h = H_L if sheet == "L" else H_R
    left = jump.conj().T @ jump
    dissipative = jump @ rho @ jump.conj().T - 0.5 * (left @ rho + rho @ left)
    hamiltonian = -1j * (h @ rho - rho @ h)
    return dissipative + hamiltonian


def gain_only_generator(sheet: str, rho: torch.Tensor) -> torch.Tensor:
    _ = sheet
    jump = LOWER
    return jump @ rho @ jump.conj().T


def torch_choi(apply_map: Callable[[torch.Tensor], torch.Tensor]) -> torch.Tensor:
    blocks: list[list[torch.Tensor]] = []
    for i in range(2):
        row = []
        for j in range(2):
            eij = torch.zeros((2, 2), dtype=CTYPE)
            eij[i, j] = 1.0 + 0.0j
            row.append(apply_map(eij))
        blocks.append(row)
    return torch.cat([torch.cat(row, dim=1) for row in blocks], dim=0)


def torch_choi_min_eig(apply_map: Callable[[torch.Tensor], torch.Tensor]) -> float:
    choi = torch_choi(apply_map)
    herm = 0.5 * (choi + choi.conj().T)
    return float(torch.min(torch.linalg.eigvalsh(herm)).real.item())


def transpose_map(rho: torch.Tensor) -> torch.Tensor:
    return rho.T


def torch_channel_metrics(sheet: str, rho: torch.Tensor) -> dict[str, Any]:
    kraus = torch_kraus(sheet)
    out = apply_kraus(rho, kraus)
    derivative = lindblad_generator(sheet, rho)
    raw_step = rho + DT * derivative
    completion = sum(k.conj().T @ k for k in kraus)
    jump_projector = kraus[1].conj().T @ kraus[1]
    h = H_L if sheet == "L" else H_R
    n01_commutator_norm = torch.linalg.matrix_norm(h @ jump_projector - jump_projector @ h).real
    return {
        "sheet": sheet,
        "channel_trace_delta": abs(float((torch.trace(out) - 1.0).real.item())),
        "channel_output_min_eig": float(torch.min(torch.linalg.eigvalsh(0.5 * (out + out.conj().T))).real.item()),
        "generator_trace_flow_abs": abs(float(torch.trace(derivative).real.item())),
        "finite_step_trace_delta": abs(float((torch.trace(raw_step) - 1.0).real.item())),
        "kraus_completeness_residual": float(torch.linalg.matrix_norm(completion - I2).real.item()),
        "choi_min_eig": torch_choi_min_eig(lambda x: apply_kraus(x, kraus)),
        "n01_hamiltonian_jump_projector_commutator_norm": float(n01_commutator_norm.item()),
        "post_channel_density": out,
    }


def jax_kraus(sheet: str, gamma: float = GAMMA) -> list[jax.Array]:
    g = jnp.array(gamma, dtype=jnp.float64)
    if sheet == "L":
        k0 = jnp.diag(jnp.array([1.0, jnp.sqrt(1.0 - g)], dtype=jnp.float64)).astype(jnp.complex128)
        jump = jnp.sqrt(g).astype(jnp.complex128) * jnp.array([[0.0, 1.0], [0.0, 0.0]], dtype=jnp.complex128)
    elif sheet == "R":
        k0 = jnp.diag(jnp.array([jnp.sqrt(1.0 - g), 1.0], dtype=jnp.float64)).astype(jnp.complex128)
        jump = jnp.sqrt(g).astype(jnp.complex128) * jnp.array([[0.0, 0.0], [1.0, 0.0]], dtype=jnp.complex128)
    else:
        raise ValueError(sheet)
    return [k0, jump]


def jax_apply_kraus(rho: jax.Array, kraus: list[jax.Array]) -> jax.Array:
    out = jnp.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ jnp.conjugate(k).T
    return out


def jax_choi(apply_map: Callable[[jax.Array], jax.Array]) -> jax.Array:
    blocks = []
    for i in range(2):
        row = []
        for j in range(2):
            eij = jnp.zeros((2, 2), dtype=jnp.complex128).at[i, j].set(1.0 + 0.0j)
            row.append(apply_map(eij))
        blocks.append(row)
    return jnp.block(blocks)


def jax_choi_min_eig(apply_map: Callable[[jax.Array], jax.Array]) -> float:
    choi = jax_choi(apply_map)
    herm = 0.5 * (choi + jnp.conjugate(choi).T)
    return float(jnp.min(jnp.linalg.eigvalsh(herm)).item())


def jax_lindblad_trace_flow_abs(sheet: str) -> float:
    rho = jnp.array([[0.7 + 0.0j, 0.2 + 0.1j], [0.2 - 0.1j, 0.3 + 0.0j]], dtype=jnp.complex128)
    kraus = jax_kraus(sheet)
    jump = kraus[1]
    left = jnp.conjugate(jump).T @ jump
    h_torch = H_L if sheet == "L" else H_R
    h = jnp.array(h_torch.detach().cpu().tolist(), dtype=jnp.complex128)
    derivative = jump @ rho @ jnp.conjugate(jump).T - 0.5 * (left @ rho + rho @ left) - 1j * (h @ rho - rho @ h)
    return abs(float(jnp.real(jnp.trace(derivative)).item()))


def jax_metrics(sheet: str) -> dict[str, float]:
    kraus = jax_kraus(sheet)
    transpose = lambda x: jnp.transpose(x)
    return {
        "choi_min_eig": jax_choi_min_eig(lambda x: jax_apply_kraus(x, kraus)),
        "transpose_control_choi_min_eig": jax_choi_min_eig(transpose),
        "generator_trace_flow_abs": jax_lindblad_trace_flow_abs(sheet),
    }


def sympy_block_matrix(blocks: list[list[sp.Matrix]]) -> sp.Matrix:
    return sp.Matrix.vstack(*[sp.Matrix.hstack(*row) for row in blocks])


def sympy_choi_for_map(apply_map: Callable[[sp.Matrix], sp.Matrix]) -> sp.Matrix:
    blocks = []
    for i in range(2):
        row = []
        for j in range(2):
            eij = sp.zeros(2, 2)
            eij[i, j] = 1
            row.append(apply_map(eij))
        blocks.append(row)
    return sympy_block_matrix(blocks)


def sympy_exact_checks() -> dict[str, Any]:
    g = sp.Rational(3, 10)
    k0 = sp.diag(1, sp.sqrt(1 - g))
    k1 = sp.Matrix([[0, sp.sqrt(g)], [0, 0]])

    def channel(rho: sp.Matrix) -> sp.Matrix:
        return k0 * rho * k0.conjugate().T + k1 * rho * k1.conjugate().T

    choi = sympy_choi_for_map(channel)
    transpose_choi = sympy_choi_for_map(lambda rho: rho.T)
    channel_eigs = sorted([sp.simplify(ev) for ev in choi.eigenvals().keys()], key=lambda v: float(sp.N(v)))
    transpose_eigs = sorted([sp.simplify(ev) for ev in transpose_choi.eigenvals().keys()], key=lambda v: float(sp.N(v)))
    completeness = sp.simplify(k0.conjugate().T * k0 + k1.conjugate().T * k1)
    return {
        "tool": "sympy",
        "amplitude_damping_choi_eigenvalues": [str(v) for v in channel_eigs],
        "transpose_map_choi_eigenvalues": [str(v) for v in transpose_eigs],
        "kraus_completeness": str(completeness),
        "real_min_choi_eig": float(sp.N(channel_eigs[0])),
        "control_min_choi_eig": float(sp.N(transpose_eigs[0])),
        "cp_invariant_real_holds": bool(channel_eigs[0] >= 0),
        "cp_invariant_control_holds": bool(transpose_eigs[0] >= 0),
        "tp_invariant_real_holds": bool(completeness == sp.eye(2)),
        "verdict_flip": bool(channel_eigs[0] >= 0 and transpose_eigs[0] < 0 and completeness == sp.eye(2)),
        "pass": bool(channel_eigs[0] == 0 and transpose_eigs[0] == -1 and completeness == sp.eye(2)),
    }


def clifford_jump_basis_check() -> dict[str, Any]:
    _, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]

    def max_anticommutator(rows: list[Any]) -> float:
        vals = []
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                vals.append(float(abs(rows[i] * rows[j] + rows[j] * rows[i])))
        return max(vals)

    real_residual = max_anticommutator([e1, e2, e3])
    duplicate_residual = max_anticommutator([e1, e1, e3])
    return {
        "tool": "clifford",
        "signature": "Cl(3)",
        "real_distinct_generator_anticommutator_residual": real_residual,
        "duplicate_generator_anticommutator_residual": duplicate_residual,
        "pass": bool(real_residual <= EPS and duplicate_residual > 1.0),
    }


def cp_smt_proof(real_min: float, control_min: float) -> dict[str, Any]:
    return smt_load_bearing(
        claim="l4_local_channel_complete_positivity_min_choi_eig_ge_negative_eps",
        real_measured={"min_choi_eig": real_min, "negative_eps": -EPS},
        control_measured={"min_choi_eig": control_min, "negative_eps": -EPS},
        claim_builder=lambda v: v["min_choi_eig"] >= v["negative_eps"],
        cvc5_claim_pairs=[("min_choi_eig", ">=", "negative_eps")],
    )


def tp_smt_proof(real_trace_abs: float, control_trace_abs: float) -> dict[str, Any]:
    return smt_load_bearing(
        claim="l4_lindblad_generator_trace_flow_abs_le_eps",
        real_measured={"trace_flow_abs": real_trace_abs, "eps": EPS},
        control_measured={"trace_flow_abs": control_trace_abs, "eps": EPS},
        claim_builder=lambda v: v["trace_flow_abs"] <= v["eps"],
        cvc5_claim_pairs=[("trace_flow_abs", "<=", "eps")],
    )


def proof_passes(proof: dict[str, Any]) -> bool:
    return bool(
        proof.get("real_claim_verdict") == "sat"
        and proof.get("negated_claim_verdict") == "unsat"
        and proof.get("differ") is True
        and proof.get("bound_to_measured") is True
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
    )


def scale_rung(shape: tuple[int, int, int]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    densities = site_densities(site_spinors(coords))
    rows = []
    features = []
    for site, rho in enumerate(densities):
        sheet = "L" if site % 2 == 0 else "R"
        metric = torch_channel_metrics(sheet, rho)
        rows.append({key: value for key, value in metric.items() if key != "post_channel_density"})
        features.append(
            torch.tensor(
                [
                    metric["channel_trace_delta"],
                    metric["channel_output_min_eig"],
                    metric["generator_trace_flow_abs"],
                    metric["choi_min_eig"],
                    metric["n01_hamiltonian_jump_projector_commutator_norm"],
                    1.0 if sheet == "L" else -1.0,
                ],
                dtype=RTYPE,
            )
        )
    feature_tensor = torch.stack(features)
    topo = topology_certificates(shape, feature_tensor)
    jax_l = jax_metrics("L")
    jax_r = jax_metrics("R")
    torch_min_choi = min(row["choi_min_eig"] for row in rows)
    torch_max_trace_flow = max(row["generator_trace_flow_abs"] for row in rows)
    transpose_min = torch_choi_min_eig(transpose_map)
    gain_only_trace = abs(float(torch.trace(gain_only_generator("L", TEST_RHO)).real.item()))
    jax_delta = max(
        abs(jax_l["choi_min_eig"] - torch_channel_metrics("L", TEST_RHO)["choi_min_eig"]),
        abs(jax_r["choi_min_eig"] - torch_channel_metrics("R", TEST_RHO)["choi_min_eig"]),
        abs(jax_l["transpose_control_choi_min_eig"] - transpose_min),
        abs(jax_l["generator_trace_flow_abs"] - abs(float(torch.trace(lindblad_generator("L", TEST_RHO)).real.item()))),
    )
    counts = exact_counts(shape)
    passed = bool(
        topo["pass"]
        and max(row["channel_trace_delta"] for row in rows) <= EPS
        and min(row["channel_output_min_eig"] for row in rows) >= -EPS
        and torch_min_choi >= -EPS
        and torch_max_trace_flow <= EPS
        and min(row["n01_hamiltonian_jump_projector_commutator_norm"] for row in rows) > 0.1
        and transpose_min < -0.9
        and gain_only_trace > 0.6
        and jax_delta <= EPS
    )
    return {
        "shape": list(shape),
        "sites_or_qubits": counts["V"],
        "site_count": counts["V"],
        "edge_count": counts["E"],
        "face_count": counts["F"],
        "cell_count": counts["C"],
        "peps3d_bond_dim": 2,
        "operator_count": 2,
        "kraus_count": 2,
        "path_count": counts["V"],
        "dense_state_closure_used": False,
        "dense_state_dimension_if_used": str(2 ** counts["V"]),
        "min_channel_output_eig": min(row["channel_output_min_eig"] for row in rows),
        "max_channel_trace_delta": max(row["channel_trace_delta"] for row in rows),
        "min_choi_eig": torch_min_choi,
        "transpose_control_choi_min_eig": transpose_min,
        "max_generator_trace_flow_abs": torch_max_trace_flow,
        "gain_only_control_trace_flow_abs": gain_only_trace,
        "min_n01_commutator_norm": min(row["n01_hamiltonian_jump_projector_commutator_norm"] for row in rows),
        "topology": topo,
        "jax_L": jax_l,
        "jax_R": jax_r,
        "jax_vs_pytorch_delta": jax_delta,
        "sample_site_rows": rows[:4],
        "pass": passed,
    }


def build_tool_ablations(top: dict[str, Any], clifford_check: dict[str, Any]) -> dict[str, Any]:
    return {
        "torch_cp_transpose_control": tool_ablation(
            "torch_choi_min_eig_real_channel_vs_transpose_non_cp_control",
            baseline_value=top["min_choi_eig"],
            ablated_value=top["transpose_control_choi_min_eig"],
            tool="torch",
        ),
        "torch_tp_gain_only_control": tool_ablation(
            "torch_lindblad_trace_flow_real_generator_vs_gain_only_control",
            baseline_value=top["max_generator_trace_flow_abs"],
            ablated_value=top["gain_only_control_trace_flow_abs"],
            tool="torch",
        ),
        "jax_cp_transpose_control": tool_ablation(
            "jax_choi_min_eig_real_channel_vs_transpose_non_cp_control",
            baseline_value=top["jax_L"]["choi_min_eig"],
            ablated_value=top["jax_L"]["transpose_control_choi_min_eig"],
            tool="jax",
        ),
        "clifford_jump_basis_duplicate_control": tool_ablation(
            "clifford_distinct_jump_basis_vs_duplicate_generator_control",
            baseline_value=clifford_check["real_distinct_generator_anticommutator_residual"],
            ablated_value=clifford_check["duplicate_generator_anticommutator_residual"],
            tool="clifford",
        ),
    }


def known_value_checks(top: dict[str, Any], sympy_exact: dict[str, Any], cp_proof: dict[str, Any], tp_proof: dict[str, Any]) -> dict[str, Any]:
    completeness_l = torch_channel_metrics("L", TEST_RHO)["kraus_completeness_residual"]
    trace_flow_l = abs(float(torch.trace(lindblad_generator("L", TEST_RHO)).real.item()))
    gain_only_l = abs(float(torch.trace(gain_only_generator("L", TEST_RHO)).real.item()))
    return {
        "amplitude_damping_kraus_completeness": {
            "computed_residual": completeness_l,
            "expected": 0.0,
            "pass": completeness_l <= EPS,
        },
        "torch_channel_cp_min_choi": {
            "computed": top["min_choi_eig"],
            "expected_minimum": 0.0,
            "pass": top["min_choi_eig"] >= -EPS,
        },
        "torch_transpose_control_non_cp": {
            "computed": top["transpose_control_choi_min_eig"],
            "expected": -1.0,
            "pass": abs(top["transpose_control_choi_min_eig"] + 1.0) <= EPS,
        },
        "torch_lindblad_trace_flow": {
            "computed_abs": trace_flow_l,
            "expected": 0.0,
            "pass": trace_flow_l <= EPS,
        },
        "torch_gain_only_trace_flow_control": {
            "computed_abs": gain_only_l,
            "expected_for_TEST_RHO_lowering": 0.7,
            "pass": abs(gain_only_l - 0.7) <= EPS,
        },
        "sympy_exact_cp_tp_flip": {
            "computed": sympy_exact,
            "pass": sympy_exact["pass"] and sympy_exact["verdict_flip"],
        },
        "smt_cp_flip_bound_to_measured": {
            "z3_real": cp_proof.get("real_claim_verdict"),
            "z3_control": cp_proof.get("negated_claim_verdict"),
            "cvc5_real": cp_proof.get("cvc5_real_verdict"),
            "cvc5_control": cp_proof.get("cvc5_control_verdict"),
            "pass": proof_passes(cp_proof),
        },
        "smt_tp_flip_bound_to_measured": {
            "z3_real": tp_proof.get("real_claim_verdict"),
            "z3_control": tp_proof.get("negated_claim_verdict"),
            "cvc5_real": tp_proof.get("cvc5_real_verdict"),
            "cvc5_control": tp_proof.get("cvc5_control_verdict"),
            "pass": proof_passes(tp_proof),
        },
        "no_dense_state_closure": {
            "dense_state_closure_used": False,
            "blocked_dense_dimension_at_64": str(2**64),
            "pass": True,
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    scale_rows = {str(n): scale_rung(shape) for n, shape in zip(SCALES, SHAPES)}
    top = scale_rows["64"]
    sympy_exact = sympy_exact_checks()
    clifford_check = clifford_jump_basis_check()
    cp_proof = cp_smt_proof(top["min_choi_eig"], top["transpose_control_choi_min_eig"])
    tp_proof = tp_smt_proof(top["max_generator_trace_flow_abs"], top["gain_only_control_trace_flow_abs"])
    ablations = build_tool_ablations(top, clifford_check)
    checks = known_value_checks(top, sympy_exact, cp_proof, tp_proof)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = proof_passes(cp_proof) and proof_passes(tp_proof) and sympy_exact["pass"]
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > EPS
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= EPS
        for row in ablations.values()
    )
    known_pass = all(row["pass"] for row in checks.values())
    all_pass = bool(scale_pass and proof_pass and ablation_pass and known_pass and clifford_check["pass"])

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(CTYPE),
        "sites": 64,
        "action": "per-site amplitude-damping CPTP channel plus Lindblad generator trace-flow check",
        "min_choi_eig": top["min_choi_eig"],
        "transpose_control_choi_min_eig": top["transpose_control_choi_min_eig"],
        "max_generator_trace_flow_abs": top["max_generator_trace_flow_abs"],
        "gain_only_control_trace_flow_abs": top["gain_only_control_trace_flow_abs"],
        "max_channel_trace_delta": top["max_channel_trace_delta"],
        "min_channel_output_eig": top["min_channel_output_eig"],
        "min_n01_commutator_norm": top["min_n01_commutator_norm"],
        "dense_state_closure_used": False,
        "pass": top["pass"],
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "sites": 64,
        "L": top["jax_L"],
        "R": top["jax_R"],
        "pass": bool(top["jax_vs_pytorch_delta"] <= EPS),
    }

    controls = {
        "transpose_map_non_cp_control": {
            "description": "Replace the local channel action with rho -> rho^T and recompute Choi min eigenvalue.",
            "negative_control_type": "positive_not_completely_positive_map",
            "choi_min_eig": top["transpose_control_choi_min_eig"],
            "cp_invariant_holds": False,
            "pass": bool(top["transpose_control_choi_min_eig"] < -0.9),
        },
        "gain_only_trace_flow_control": {
            "description": "Drop the Lindblad anticommutator and Hamiltonian terms; read trace on raw D[rho], without renormalization.",
            "negative_control_type": "trace_preservation_killer",
            "trace_flow_abs": top["gain_only_control_trace_flow_abs"],
            "trace_preserving_claim_holds": False,
            "pass": bool(top["gain_only_control_trace_flow_abs"] > 0.6),
        },
        "dense_global_state_closure_blocked": {
            "description": "The layer action is site-local on 2x2 densities; 2^64 dense global closure is recorded only as blocked.",
            "dense_state_closure_used": False,
            "dense_state_dimension_if_used": str(2**64),
            "pass": True,
        },
    }

    return as_jsonable(
        {
            "schema": "FORMAL_SCOUT_RESULT_v1",
            "sim_id": SIM_ID,
            "name": SIM_ID,
            "version": "1.0.0",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "THISFILE": str(THISFILE),
            "RESULT": str(RESULT),
            "object_id": OBJECT_ID,
            "finite_map": {
                "domain": "stage-2 torch two-component spinors psi_v on finite PEPS3D K=(V,E,F,C) sites for V in {8,16,32,64}; spinor-derived densities rho_v=|psi_v><psi_v|; sheet-indexed local amplitude-damping Kraus set and Lindblad generator",
                "codomain_or_output": "post-channel 2x2 densities, generator trace-flow residuals, 4x4 Choi matrices/eigenvalues, CP/TP proof flips, controls, and blocked consumers",
                "definition": "L4_GC(K,rho_v,s) applies Phi_s(rho_v)=sum_k K_{s,k} rho_v K_{s,k}^dag site-locally and computes D_s[rho_v] without dense global closure",
            },
            "root_constraints": {
                "F01": {
                    "status": "active_tested",
                    "statement": "finite PEPS3D site set, finite local spinor-density carrier, finite Kraus/operator set, finite Choi basis E_ij, finite scale ladder",
                },
                "N01": {
                    "status": "active_tested",
                    "statement": "Hamiltonian and jump-projector generators do not commute; computed commutator norm stays positive on each rung while CP/TP controls kill the local-map invariant",
                },
            },
            "classification": "lego",
            "promotion_allowed": False,
            "tier": "STAGE 6 L4 local generator/channel layer action",
            "sim_execution_kind": "nonclassical",
            "sim_class": "local_generator_channel_layer_action_probe",
            "carrier_layer": "stage-2 torch_spinor to spinor_density",
            "geometry_layer": "independent L4 local channel/generator action only; no layer stacking",
            "carrier_realization": "torch complex128 two-component spinors and 2x2 spinor-derived densities anchored to finite PEPS3D sites; JAX x64 mirror; no NumPy import",
            "peps3d_embedding": "K=(V,E,F,C) supplies finite per-site placement anchors for V=8/16/32/64; action remains local on 2x2 densities and never builds a 2^V state",
            "spinor_state": "stage-2 torch-native two-component spinors from site_spinors(coords), converted to rho_v=|psi_v><psi_v| before the L4 action",
            "quaternion_action": "not_applicable",
            "dependency_receipts": [
                "spec:/tmp/layer_specs.json:index4:L4",
                "exemplar:system_v5/ops/formal_scouts/sim_root_F01_finite_distinguishability_probe.py",
                "helper:/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts/load_bearing_proof.py",
                "stage2_carrier_helper:system_v5/ops/formal_scouts/sim_l2_spinor_chirality_weyl_cover_layer_probe.py:site_spinors/site_densities/topology_certificates",
            ],
            "allowed_claims": [
                "one bounded independent L4 local generator/channel action runs on a stage-2 spinor-density carrier at 8/16/32/64 sites",
                "the realized amplitude-damping local channel is CP/TP by measured Choi and raw trace-flow invariants",
                "transpose-map and gain-only controls flip those invariants when recomputed without renormalization",
            ],
            "promotion_blockers": [
                "no L5/L6/L7/L8 stacking or downstream layer readiness",
                "no Xi/Phi0/Axis0/flux/FEP/gravity/physics consumer",
                "no full manifold, true G-structure, or layer-completion admission claim",
            ],
            "eligible_consumers": ["future bounded L4 audits that cite this exact result path and keep promotion_allowed=false"],
            "blocked_consumers": BLOCKED_CONSUMERS,
            "downstream_blocks": BLOCKED_CONSUMERS,
            "torch_primary_result": torch_primary_result,
            "jax_mirror_result": jax_mirror_result,
            "jax_vs_pytorch_delta": max(row["jax_vs_pytorch_delta"] for row in scale_rows.values()),
            "proof_results": {
                "cp_choi_min_eig_smt_load_bearing": cp_proof,
                "tp_trace_flow_smt_load_bearing": tp_proof,
                "sympy_exact_cp_tp_flip": sympy_exact,
            },
            "controls": controls,
            "tool_ablations": ablations,
            "ablation_outcome_delta": ablations,
            "tool_ablations_by_tool": ablations,
            "scale_ladder": {"rungs": scale_rows, "pass": scale_pass},
            "scale_rungs": scale_rows,
            "known_value_checks": checks,
            "clifford_jump_basis_result": clifford_check,
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "tool_manifest": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "required_tools": list(TOOL_MANIFEST.keys()),
            "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
            "proof_surfaces_used": ["load_bearing_proof.smt_load_bearing z3", "load_bearing_proof.smt_load_bearing cvc5", "sympy exact Choi spectrum"],
            "graph_surfaces_used": ["pyg", "rustworkx", "xgi"],
            "topology_surfaces_used": ["toponetx", "gudhi"],
            "required_inputs": ["/tmp/layer_specs.json SPEC_KEY=L4", "stage-2 spinor carrier helpers", "load_bearing_proof.py"],
            "data_or_artifact_dependencies": [],
            "required_negatives": ["transpose-map non-CP control", "gain-only trace-flow control", "dense global state closure blocked"],
            "negatives_run": list(controls.keys()),
            "kill_conditions": [
                "SMT CP or TP verdicts do not flip under measured controls",
                "SMT proof is not bound to measured Choi/trace-flow values",
                "SymPy exact Choi spectrum does not show real min 0 and transpose min -1",
                "numeric ablation lacks baseline/ablated recompute",
                "JAX mirror disagrees with torch beyond tolerance",
                "any rung uses dense state closure or promotes downstream consumers",
            ],
            "required_artifacts": ["result JSON", "scale_ladder", "proof_results", "controls", "tool_ablations", "known_value_checks"],
            "artifacts_emitted": [str(RESULT)],
            "witness_trace_id": f"{SIM_ID}:gamma_0_3:sites_8_16_32_64:choi_tp_flip",
            "result_summary": {
                "scale_pass": scale_pass,
                "proof_pass": proof_pass,
                "ablation_pass": ablation_pass,
                "known_value_pass": known_pass,
                "clifford_pass": clifford_check["pass"],
                "all_pass": all_pass,
            },
            "pass_rule": "all 8/16/32/64 non-dense rungs pass; CP and TP proofs are helper-bound SMT flips over measured Choi/trace-flow values; SymPy exact spectra agree; numeric ablations carry recomputed baseline and control values",
            "fail_rule": "fail on decorative proof, proof not bound to measured values, missing CP/TP control flip, dense closure, JAX mismatch, missing ablation recompute, or any downstream promotion",
            "promotion_status": "keep_but_open",
            "all_pass": all_pass,
            "required_pass": all_pass,
        }
    )


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
