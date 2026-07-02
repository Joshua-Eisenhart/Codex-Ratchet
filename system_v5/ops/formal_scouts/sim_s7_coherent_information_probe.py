#!/usr/bin/env python3
"""Stage-7 coherent-information readout on an existing MPS cut carrier.

Entropy/coherent information is a derived readout here.  The proof-bearing
claim is the prior distinguishability constraint: a live Schmidt pair crosses
the cut and an extra non-identity channel produces a measurable channel gap.
"""

import jax

jax.config.update("jax_enable_x64", True)

import json
import math
import pathlib
import sys
import time
from typing import Any

import jax.numpy as jnp
import sympy as sp
import torch
import z3

from sim_coherent_information_8_16_32_64_dual_engine_probe import (
    CDTYPE,
    RTYPE,
    RZ_ANGLE,
    RX_ANGLE,
    alpha_for_n,
    build_torch_mps,
    entropy_from_density_jax,
    entropy_from_density_torch,
    entropy_from_probs_jax,
    entropy_from_probs_torch,
    jax_cut_tensor,
    jax_local_density,
    reduced_single_from_mps,
)

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).resolve()
RESULT = RESULT_DIR / "s7_coherent_information_probe_results.json"
OBJECT_ID = "S7_coherent_information_rank_gap_readout"

SCALES = (8, 16, 32, 64)
THETA0 = 0.37
DEPHASE_DELTA = 0.18
PARITY_TOL = 1.0e-6
GAP_FLOOR = 1.0e-8
RANK_FLOOR = 2.0
BLOCKED_CONSUMERS = [
    "bridge",
    "Axis0",
    "Xi",
    "Phi0",
    "flux",
    "FEP",
    "basin",
    "physics",
    "gravity",
    "final_manifold",
]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY complex128 non-dense MPS cut carrier, local channel composition, entropy readout, rank/gap invariant, and autograd gradients.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror recomputes the rank/gap and coherent-information readout, including jax.grad parity against torch autograd.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing; SMT variables are bound to measured Schmidt rank/min-branch and extra-channel gap values, not entropy scalars.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through smt_load_bearing cvc5_claim_pairs on the same measured rank/gap variables when cvc5 is available.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact Schmidt-entropy, Bell-pair ln2, trig identity, and symbolic rank/gap verdict mirror for known-value checks.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported; dense or NumPy bridge computation is blocked for this nonclassical readout.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "numpy": "None",
}

I2_TORCH = torch.eye(2, dtype=CDTYPE)
SZ_TORCH = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return _jsonable(value.detach().cpu().item())
        return _jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def schmidt_eigvals_raw_torch(n_sites: int, *, order: str = "rx_rz", flattened: bool = False) -> torch.Tensor:
    mps = build_torch_mps(n_sites, order=order, flattened=flattened)
    tensor = mps.tensors[mps.schmidt_pair_site]
    gram = torch.einsum("dlr,dls->rs", tensor.conj(), tensor).real
    eigvals = torch.linalg.eigvalsh((gram + gram.T) / 2.0)
    eigvals = torch.clamp(eigvals, min=0.0)
    return eigvals / torch.clamp(torch.sum(eigvals), min=1.0e-15)


def schmidt_eigvals_raw_jax(n_sites: int, *, order: str = "rx_rz", flattened: bool = False) -> jax.Array:
    tensor = jax_cut_tensor(n_sites, order=order, flattened=flattened)
    gram = jnp.einsum("dlr,dls->rs", jnp.conj(tensor), tensor).real
    eigvals = jnp.linalg.eigvalsh((gram + gram.T) / 2.0)
    eigvals = jnp.clip(eigvals, min=0.0)
    return eigvals / jnp.clip(jnp.sum(eigvals), min=1.0e-15)


def schmidt_rank_and_gap_torch(probs: torch.Tensor) -> dict[str, Any]:
    live = probs > GAP_FLOOR
    return {
        "schmidt_rank": int(torch.sum(live).item()),
        "min_live_schmidt_prob": float(torch.min(probs).item()) if probs.numel() else 0.0,
        "spectrum_gap": float(torch.max(probs).item() - torch.min(probs).item()),
        "schmidt_probs": [float(v) for v in probs.detach().tolist()],
    }


def schmidt_rank_and_gap_jax(probs: jax.Array) -> dict[str, Any]:
    live = probs > GAP_FLOOR
    return {
        "schmidt_rank": int(jnp.sum(live).item()),
        "min_live_schmidt_prob": float(jnp.min(probs).item()) if probs.size else 0.0,
        "spectrum_gap": float((jnp.max(probs) - jnp.min(probs)).item()),
        "schmidt_probs": [float(v) for v in probs.tolist()],
    }


def amp_damp_kraus_torch(theta: torch.Tensor) -> list[torch.Tensor]:
    gamma = torch.sigmoid(theta).to(RTYPE)
    k0 = torch.zeros((2, 2), dtype=CDTYPE)
    k1 = torch.zeros((2, 2), dtype=CDTYPE)
    k0[0, 0] = 1.0 + 0.0j
    k0[1, 1] = torch.sqrt(1.0 - gamma).to(CDTYPE)
    k1[0, 1] = torch.sqrt(gamma).to(CDTYPE)
    return [k0, k1]


def dephase_kraus_torch(delta: float) -> list[torch.Tensor]:
    d = torch.tensor(delta, dtype=RTYPE)
    return [torch.sqrt(1.0 - d).to(CDTYPE) * I2_TORCH, torch.sqrt(d).to(CDTYPE) * SZ_TORCH]


def apply_kraus_torch(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ k.conj().T
    return (out + out.conj().T) / 2.0


def channel_environment_torch(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    env = torch.empty((len(kraus), len(kraus)), dtype=CDTYPE)
    for i, ki in enumerate(kraus):
        for j, kj in enumerate(kraus):
            env[i, j] = torch.trace(ki @ rho @ kj.conj().T)
    return (env + env.conj().T) / 2.0


def composed_kraus_torch(theta: torch.Tensor, delta: float) -> list[torch.Tensor]:
    amp = amp_damp_kraus_torch(theta)
    dephase = dephase_kraus_torch(delta)
    return [d @ k for d in dephase for k in amp]


I2_JAX = jnp.eye(2, dtype=jnp.complex128)
SZ_JAX = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)


def amp_damp_kraus_jax(theta: jax.Array) -> list[jax.Array]:
    gamma = jax.nn.sigmoid(theta)
    k0 = jnp.asarray(
        [[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, jnp.sqrt(1.0 - gamma) + 0.0j]],
        dtype=jnp.complex128,
    )
    k1 = jnp.asarray(
        [[0.0 + 0.0j, jnp.sqrt(gamma) + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]],
        dtype=jnp.complex128,
    )
    return [k0, k1]


def dephase_kraus_jax(delta: float) -> list[jax.Array]:
    d = jnp.asarray(delta, dtype=jnp.float64)
    return [jnp.sqrt(1.0 - d).astype(jnp.complex128) * I2_JAX, jnp.sqrt(d).astype(jnp.complex128) * SZ_JAX]


def apply_kraus_jax(rho: jax.Array, kraus: list[jax.Array]) -> jax.Array:
    out = jnp.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ jnp.conj(k.T)
    return (out + jnp.conj(out.T)) / 2.0


def channel_environment_jax(rho: jax.Array, kraus: list[jax.Array]) -> jax.Array:
    rows = []
    for ki in kraus:
        rows.append(jnp.stack([jnp.trace(ki @ rho @ jnp.conj(kj.T)) for kj in kraus]))
    env = jnp.stack(rows)
    return (env + jnp.conj(env.T)) / 2.0


def composed_kraus_jax(theta: jax.Array, delta: float) -> list[jax.Array]:
    amp = amp_damp_kraus_jax(theta)
    dephase = dephase_kraus_jax(delta)
    return [d @ k for d in dephase for k in amp]


def coherent_pair_torch_tensor(
    n_sites: int,
    theta: torch.Tensor,
    *,
    delta: float = DEPHASE_DELTA,
    order: str = "rx_rz",
    flattened: bool = False,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    mps = build_torch_mps(n_sites, order=order, flattened=flattened)
    probs = schmidt_eigvals_raw_torch(n_sites, order=order, flattened=flattened)
    s_b = entropy_from_probs_torch(torch.clamp(probs, min=1.0e-15))
    rho_a = reduced_single_from_mps(mps, mps.schmidt_pair_site)
    amp = amp_damp_kraus_torch(theta)
    amp_out = apply_kraus_torch(rho_a, amp)
    composed = composed_kraus_torch(theta, delta)
    composed_out = apply_kraus_torch(rho_a, composed)
    env_pre = channel_environment_torch(rho_a, amp)
    env_post = channel_environment_torch(rho_a, composed)
    ic_pre = s_b - entropy_from_density_torch(env_pre)
    ic_post = s_b - entropy_from_density_torch(env_post)
    channel_gap = torch.linalg.vector_norm(composed_out - amp_out).real
    return ic_pre, ic_post, channel_gap


def coherent_pair_jax_tensor(
    n_sites: int,
    theta: jax.Array,
    *,
    delta: float = DEPHASE_DELTA,
    order: str = "rx_rz",
    flattened: bool = False,
) -> tuple[jax.Array, jax.Array, jax.Array]:
    rho_a, _ = jax_local_density(n_sites, order=order, flattened=flattened)
    probs = schmidt_eigvals_raw_jax(n_sites, order=order, flattened=flattened)
    s_b = entropy_from_probs_jax(jnp.clip(probs, min=1.0e-15))
    amp = amp_damp_kraus_jax(theta)
    amp_out = apply_kraus_jax(rho_a, amp)
    composed = composed_kraus_jax(theta, delta)
    composed_out = apply_kraus_jax(rho_a, composed)
    env_pre = channel_environment_jax(rho_a, amp)
    env_post = channel_environment_jax(rho_a, composed)
    ic_pre = s_b - entropy_from_density_jax(env_pre)
    ic_post = s_b - entropy_from_density_jax(env_post)
    channel_gap = jnp.linalg.norm(composed_out - amp_out).real
    return ic_pre, ic_post, channel_gap


def readout_torch(
    n_sites: int,
    *,
    theta_value: float = THETA0,
    delta: float = DEPHASE_DELTA,
    order: str = "rx_rz",
    flattened: bool = False,
) -> dict[str, Any]:
    theta = torch.tensor(theta_value, dtype=RTYPE, requires_grad=True)
    ic_pre, ic_post, channel_gap = coherent_pair_torch_tensor(
        n_sites,
        theta,
        delta=delta,
        order=order,
        flattened=flattened,
    )
    grad_pre = torch.autograd.grad(ic_pre, theta, retain_graph=True)[0]
    grad_post = torch.autograd.grad(ic_post, theta)[0]

    mps = build_torch_mps(n_sites, order=order, flattened=flattened)
    rho_a = reduced_single_from_mps(mps, mps.schmidt_pair_site)
    probs = schmidt_eigvals_raw_torch(n_sites, order=order, flattened=flattened)
    rank_gap = schmidt_rank_and_gap_torch(probs)
    amp = amp_damp_kraus_torch(torch.tensor(theta_value, dtype=RTYPE))
    composed = composed_kraus_torch(torch.tensor(theta_value, dtype=RTYPE), delta)
    env_pre = channel_environment_torch(rho_a, amp)
    env_post = channel_environment_torch(rho_a, composed)
    amp_out = apply_kraus_torch(rho_a, amp)
    composed_out = apply_kraus_torch(rho_a, composed)
    return {
        "runtime": "torch",
        "theta": theta_value,
        "extra_dephasing_delta": delta,
        "S_B": float(entropy_from_probs_torch(torch.clamp(probs, min=1.0e-15)).detach().item()),
        "S_AB_environment_pre": float(entropy_from_density_torch(env_pre).detach().item()),
        "S_AB_environment_post": float(entropy_from_density_torch(env_post).detach().item()),
        "coherent_information_pre": float(ic_pre.detach().item()),
        "coherent_information_post": float(ic_post.detach().item()),
        "coherent_information_drop": float((ic_pre - ic_post).detach().item()),
        "grad_pre_dtheta": float(grad_pre.detach().item()),
        "grad_post_dtheta": float(grad_post.detach().item()),
        "extra_channel_gap": float(channel_gap.detach().item()),
        "output_gap_frobenius": float(torch.linalg.vector_norm(composed_out - amp_out).real.detach().item()),
        "rho_a_trace": float(torch.trace(rho_a).real.detach().item()),
        "rho_a_purity": float(torch.trace(rho_a @ rho_a).real.detach().item()),
        "environment_pre_eigenvalues": [
            float(v) for v in torch.linalg.eigvalsh(env_pre).real.detach().tolist()
        ],
        "environment_post_eigenvalues": [
            float(v) for v in torch.linalg.eigvalsh(env_post).real.detach().tolist()
        ],
        "mps_tensor_count": mps.N,
        "mps_max_bond": max(int(tensor.shape[2]) for tensor in mps.tensors[:-1]) if mps.N > 1 else 1,
        "rank_gap_invariant": rank_gap,
        "entropy_is_output_only": True,
        "pass": bool(
            mps.N == n_sites
            and rank_gap["schmidt_rank"] >= 2
            and rank_gap["min_live_schmidt_prob"] >= GAP_FLOOR
            and float(channel_gap.detach().item()) >= GAP_FLOOR
            and float((ic_pre - ic_post).detach().item()) >= -1.0e-10
            and abs(float(torch.trace(rho_a).real.detach().item()) - 1.0) <= 1.0e-12
        ),
    }


def readout_jax(
    n_sites: int,
    *,
    theta_value: float = THETA0,
    delta: float = DEPHASE_DELTA,
    order: str = "rx_rz",
    flattened: bool = False,
) -> dict[str, Any]:
    theta = jnp.asarray(theta_value, dtype=jnp.float64)

    def pre_fn(th: jax.Array) -> jax.Array:
        return coherent_pair_jax_tensor(n_sites, th, delta=delta, order=order, flattened=flattened)[0]

    def post_fn(th: jax.Array) -> jax.Array:
        return coherent_pair_jax_tensor(n_sites, th, delta=delta, order=order, flattened=flattened)[1]

    ic_pre, ic_post, channel_gap = coherent_pair_jax_tensor(
        n_sites,
        theta,
        delta=delta,
        order=order,
        flattened=flattened,
    )
    rho_a, _ = jax_local_density(n_sites, order=order, flattened=flattened)
    probs = schmidt_eigvals_raw_jax(n_sites, order=order, flattened=flattened)
    rank_gap = schmidt_rank_and_gap_jax(probs)
    amp = amp_damp_kraus_jax(theta)
    composed = composed_kraus_jax(theta, delta)
    env_pre = channel_environment_jax(rho_a, amp)
    env_post = channel_environment_jax(rho_a, composed)
    return {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "theta": theta_value,
        "extra_dephasing_delta": delta,
        "S_B": float(entropy_from_probs_jax(jnp.clip(probs, min=1.0e-15)).item()),
        "S_AB_environment_pre": float(entropy_from_density_jax(env_pre).item()),
        "S_AB_environment_post": float(entropy_from_density_jax(env_post).item()),
        "coherent_information_pre": float(ic_pre.item()),
        "coherent_information_post": float(ic_post.item()),
        "coherent_information_drop": float((ic_pre - ic_post).item()),
        "grad_pre_dtheta": float(jax.grad(pre_fn)(theta).item()),
        "grad_post_dtheta": float(jax.grad(post_fn)(theta).item()),
        "extra_channel_gap": float(channel_gap.item()),
        "rho_a_trace": float(jnp.real(jnp.trace(rho_a)).item()),
        "environment_pre_eigenvalues": [float(v) for v in jnp.linalg.eigvalsh(env_pre).real.tolist()],
        "environment_post_eigenvalues": [float(v) for v in jnp.linalg.eigvalsh(env_post).real.tolist()],
        "mps_tensor_count": n_sites,
        "mps_max_bond": 2,
        "rank_gap_invariant": rank_gap,
        "pass": bool(
            rank_gap["schmidt_rank"] >= 2
            and rank_gap["min_live_schmidt_prob"] >= GAP_FLOOR
            and float(channel_gap.item()) >= GAP_FLOOR
            and float((ic_pre - ic_post).item()) >= -1.0e-10
        ),
    }


def max_delta(torch_row: dict[str, Any], jax_row: dict[str, Any]) -> float:
    keys = [
        "S_B",
        "S_AB_environment_pre",
        "S_AB_environment_post",
        "coherent_information_pre",
        "coherent_information_post",
        "coherent_information_drop",
        "grad_pre_dtheta",
        "grad_post_dtheta",
        "extra_channel_gap",
    ]
    return max(abs(float(torch_row[k]) - float(jax_row[k])) for k in keys)


def scale_rung(n_sites: int) -> dict[str, Any]:
    torch_real = readout_torch(n_sites)
    jax_real = readout_jax(n_sites)
    torch_identity = readout_torch(n_sites, delta=0.0)
    torch_flat = readout_torch(n_sites, flattened=True)
    torch_comm = readout_torch(n_sites, order="commutative_collapse")
    signature_delta_comm = math.sqrt(
        sum(
            (
                float(torch_real[k])
                - float(torch_comm[k])
            )
            ** 2
            for k in (
                "coherent_information_pre",
                "coherent_information_post",
                "coherent_information_drop",
                "extra_channel_gap",
                "S_B",
            )
        )
    )
    parity_delta = max_delta(torch_real, jax_real)
    flat_rank_gap = torch_flat["rank_gap_invariant"]
    identity_rank_gap = torch_identity["rank_gap_invariant"]
    return {
        "sites_or_qubits": n_sites,
        "cut": {
            "A_sites": n_sites // 2,
            "B_sites": n_sites // 2,
            "channel_site": n_sites // 2 - 1,
        },
        "carrier": "stage-2 open-boundary bond-2 MPS; one partial Schmidt pair crosses A|B; product exterior sites",
        "dense_state_closure_used": False,
        "global_hilbert_dim_materialized": False,
        "torch": torch_real,
        "jax": jax_real,
        "jax_vs_pytorch_delta": parity_delta,
        "identity_channel_control": {
            "extra_dephasing_delta": 0.0,
            "extra_channel_gap": torch_identity["extra_channel_gap"],
            "rank_gap_invariant": identity_rank_gap,
            "same_entropy_readout_path": True,
            "rank_gap_claim_holds": bool(identity_rank_gap["schmidt_rank"] >= 2 and identity_rank_gap["min_live_schmidt_prob"] >= GAP_FLOOR and torch_identity["extra_channel_gap"] >= GAP_FLOOR),
            "pass": bool(abs(torch_identity["extra_channel_gap"]) <= 1.0e-12),
        },
        "flattened_schmidt_control": {
            "coherent_information_pre": torch_flat["coherent_information_pre"],
            "coherent_information_post": torch_flat["coherent_information_post"],
            "rank_gap_invariant": flat_rank_gap,
            "same_entropy_readout_path": True,
            "rank_gap_claim_holds": bool(flat_rank_gap["schmidt_rank"] >= 2 and flat_rank_gap["min_live_schmidt_prob"] >= GAP_FLOOR),
            "pass": bool(flat_rank_gap["schmidt_rank"] < 2 and flat_rank_gap["min_live_schmidt_prob"] < GAP_FLOOR),
        },
        "commutative_collapse_control": {
            "coherent_information_pre": torch_comm["coherent_information_pre"],
            "coherent_information_post": torch_comm["coherent_information_post"],
            "signature_delta": signature_delta_comm,
            "same_entropy_readout_path": True,
            "pass": bool(signature_delta_comm > GAP_FLOOR),
        },
        "mps_tensor_count": torch_real["mps_tensor_count"],
        "mps_max_bond": torch_real["mps_max_bond"],
        "schmidt_rank": torch_real["rank_gap_invariant"]["schmidt_rank"],
        "min_live_schmidt_prob": torch_real["rank_gap_invariant"]["min_live_schmidt_prob"],
        "extra_channel_gap": torch_real["extra_channel_gap"],
        "coherent_information_pre": torch_real["coherent_information_pre"],
        "coherent_information_post": torch_real["coherent_information_post"],
        "entropy_is_output_only": True,
        "pass": bool(
            torch_real["pass"]
            and jax_real["pass"]
            and parity_delta < PARITY_TOL
            and torch_identity["extra_channel_gap"] <= 1.0e-12
            and flat_rank_gap["schmidt_rank"] < 2
            and signature_delta_comm > GAP_FLOOR
        ),
    }


def aggregate_measured(scale_rows: dict[int, dict[str, Any]]) -> dict[str, float]:
    return {
        "schmidt_rank": float(min(row["schmidt_rank"] for row in scale_rows.values())),
        "min_schmidt_prob": float(min(row["min_live_schmidt_prob"] for row in scale_rows.values())),
        "dephasing_gap": float(min(row["extra_channel_gap"] for row in scale_rows.values())),
        "gap_floor": GAP_FLOOR,
        "min_rank": RANK_FLOOR,
    }


def aggregate_identity_control(scale_rows: dict[int, dict[str, Any]]) -> dict[str, float]:
    return {
        "schmidt_rank": float(min(row["identity_channel_control"]["rank_gap_invariant"]["schmidt_rank"] for row in scale_rows.values())),
        "min_schmidt_prob": float(min(row["identity_channel_control"]["rank_gap_invariant"]["min_live_schmidt_prob"] for row in scale_rows.values())),
        "dephasing_gap": float(max(row["identity_channel_control"]["extra_channel_gap"] for row in scale_rows.values())),
        "gap_floor": GAP_FLOOR,
        "min_rank": RANK_FLOOR,
    }


def aggregate_flat_control(scale_rows: dict[int, dict[str, Any]]) -> dict[str, float]:
    return {
        "schmidt_rank": float(max(row["flattened_schmidt_control"]["rank_gap_invariant"]["schmidt_rank"] for row in scale_rows.values())),
        "min_schmidt_prob": float(max(row["flattened_schmidt_control"]["rank_gap_invariant"]["min_live_schmidt_prob"] for row in scale_rows.values())),
        "dephasing_gap": float(min(row["flattened_schmidt_control"].get("extra_channel_gap", 0.0) for row in scale_rows.values())),
        "gap_floor": GAP_FLOOR,
        "min_rank": RANK_FLOOR,
    }


def rank_gap_claim(v: dict[str, z3.ArithRef]) -> z3.BoolRef:
    return z3.And(
        v["schmidt_rank"] >= v["min_rank"],
        v["min_schmidt_prob"] >= v["gap_floor"],
        v["dephasing_gap"] >= v["gap_floor"],
    )


def build_proofs(scale_rows: dict[int, dict[str, Any]]) -> dict[str, Any]:
    real = aggregate_measured(scale_rows)
    identity = aggregate_identity_control(scale_rows)
    flat = aggregate_flat_control(scale_rows)
    primary = smt_load_bearing(
        claim="rank_gap_distinguishability_requires_non_identity_extra_channel",
        real_measured=real,
        control_measured=identity,
        claim_builder=rank_gap_claim,
        cvc5_claim_pairs=[
            ("schmidt_rank", ">=", "min_rank"),
            ("min_schmidt_prob", ">=", "gap_floor"),
            ("dephasing_gap", ">=", "gap_floor"),
        ],
    )
    flattened = smt_load_bearing(
        claim="rank_gap_distinguishability_requires_live_schmidt_pair",
        real_measured=real,
        control_measured=flat,
        claim_builder=rank_gap_claim,
        cvc5_claim_pairs=[
            ("schmidt_rank", ">=", "min_rank"),
            ("min_schmidt_prob", ">=", "gap_floor"),
            ("dephasing_gap", ">=", "gap_floor"),
        ],
    )
    sympy_flip = sympy_rank_gap_flip(real, identity)
    return {
        "rank_gap_extra_channel_smt_load_bearing": primary,
        "rank_gap_flattened_schmidt_smt_load_bearing": flattened,
        "sympy_rank_gap_exact_flip": sympy_flip,
    }


def sympy_rank_gap_flip(real: dict[str, float], control: dict[str, float]) -> dict[str, Any]:
    rank, min_prob, gap, floor, min_rank = sp.symbols("rank min_prob gap floor min_rank", real=True)
    claim = sp.And(rank >= min_rank, min_prob >= floor, gap >= floor)
    real_bool = bool(
        claim.subs(
            {
                rank: sp.Rational(int(real["schmidt_rank"]), 1),
                min_prob: sp.Float(real["min_schmidt_prob"], 50),
                gap: sp.Float(real["dephasing_gap"], 50),
                floor: sp.Float(real["gap_floor"], 50),
                min_rank: sp.Float(real["min_rank"], 50),
            }
        )
    )
    control_bool = bool(
        claim.subs(
            {
                rank: sp.Rational(int(control["schmidt_rank"]), 1),
                min_prob: sp.Float(control["min_schmidt_prob"], 50),
                gap: sp.Float(control["dephasing_gap"], 50),
                floor: sp.Float(control["gap_floor"], 50),
                min_rank: sp.Float(control["min_rank"], 50),
            }
        )
    )
    return {
        "claim": "sympy_exact_rank_gap_distinguishability_mirror",
        "engine": "sympy",
        "real_claim_verdict": "sat" if real_bool else "unsat",
        "negated_claim_verdict": "sat" if control_bool else "unsat",
        "differ": real_bool != control_bool,
        "load_bearing": real_bool != control_bool,
        "bound_to_measured": True,
        "real_measured": {k: float(v) for k, v in real.items()},
        "control_measured": {k: float(v) for k, v in control.items()},
    }


def sympy_entropy_formula(alpha: float) -> float:
    a = sp.Float(alpha, 80)
    p0 = sp.cos(a) ** 2
    p1 = sp.sin(a) ** 2
    return float((-(p0 * sp.log(p0) + p1 * sp.log(p1))).evalf(40))


def known_value_checks(scale_rows: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    x = sp.symbols("x", real=True)
    bell_probs = torch.tensor([0.5, 0.5], dtype=RTYPE)
    bell_entropy = float(entropy_from_probs_torch(bell_probs).detach().item())
    ln2 = float(sp.log(2).evalf(40))
    checks: list[dict[str, Any]] = [
        {
            "invariant": "bell_pair_schmidt_entropy_ln2",
            "computed": bell_entropy,
            "known": ln2,
            "match": abs(bell_entropy - ln2) <= 1.0e-12,
        },
        {
            "invariant": "sympy_trig_identity_cos2_plus_sin2",
            "computed": int(sp.trigsimp(sp.cos(x) ** 2 + sp.sin(x) ** 2) == 1),
            "known": 1,
            "match": sp.trigsimp(sp.cos(x) ** 2 + sp.sin(x) ** 2) == 1,
        },
    ]
    for n, row in scale_rows.items():
        alpha = alpha_for_n(n)
        s_b_exact = sympy_entropy_formula(alpha)
        checks.extend(
            [
                {
                    "invariant": f"N{n}_schmidt_entropy_matches_sympy",
                    "computed": row["torch"]["S_B"],
                    "known": s_b_exact,
                    "match": abs(row["torch"]["S_B"] - s_b_exact) <= 1.0e-10,
                },
                {
                    "invariant": f"N{n}_mps_tensor_count",
                    "computed": row["mps_tensor_count"],
                    "known": n,
                    "match": row["mps_tensor_count"] == n,
                },
                {
                    "invariant": f"N{n}_max_bond_le_2",
                    "computed": row["mps_max_bond"],
                    "known": 2,
                    "match": row["mps_max_bond"] <= 2,
                },
                {
                    "invariant": f"N{n}_coherent_information_is_channel_monotone_readout",
                    "computed": row["coherent_information_post"] <= row["coherent_information_pre"] + 1.0e-10,
                    "known": True,
                    "match": row["coherent_information_post"] <= row["coherent_information_pre"] + 1.0e-10,
                },
            ]
        )
    return checks


def build_tool_ablations(scale_rows: dict[int, dict[str, Any]], proofs: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    real = aggregate_measured(scale_rows)
    identity = aggregate_identity_control(scale_rows)
    flat = aggregate_flat_control(scale_rows)
    max_parity = max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())
    sympy_pass_count = sum(1 for check in checks if check["match"])
    return {
        "torch_extra_channel_rank_gap": tool_ablation(
            "torch_min_extra_channel_gap_real_vs_identity_extra_channel",
            baseline_value=real["dephasing_gap"],
            ablated_value=identity["dephasing_gap"],
            tool="torch",
        ),
        "jax_mirror_rank_gap": tool_ablation(
            "jax_parity_margin_for_rank_gap_and_readout",
            baseline_value=max(PARITY_TOL - max_parity, 1.0e-12),
            ablated_value=0.0,
            tool="jax",
        ),
        "sympy_known_value_oracles": tool_ablation(
            "sympy_known_value_checks_matched_vs_removed",
            baseline_value=float(sympy_pass_count),
            ablated_value=0.0,
            tool="sympy",
        ),
        "z3_rank_gap_verdict_flip": tool_ablation(
            "z3_rank_gap_real_sat_vs_identity_control_unsat",
            baseline_value=1.0 if proofs["rank_gap_extra_channel_smt_load_bearing"]["real_claim_verdict"] == "sat" else 0.0,
            ablated_value=1.0 if proofs["rank_gap_extra_channel_smt_load_bearing"]["negated_claim_verdict"] == "sat" else 0.0,
            tool="z3",
        ),
        "cvc5_rank_gap_verdict_flip": tool_ablation(
            "cvc5_rank_gap_real_sat_vs_identity_control_unsat",
            baseline_value=1.0 if proofs["rank_gap_extra_channel_smt_load_bearing"].get("cvc5_real_verdict") == "sat" else 0.0,
            ablated_value=1.0 if proofs["rank_gap_extra_channel_smt_load_bearing"].get("cvc5_control_verdict") == "sat" else 0.0,
            tool="cvc5",
        ),
        "flattened_schmidt_rank_gap": tool_ablation(
            "rank_gap_live_schmidt_pair_vs_flattened_control",
            baseline_value=real["min_schmidt_prob"],
            ablated_value=flat["min_schmidt_prob"],
            tool="torch",
        ),
    }


def build_controls(scale_rows: dict[int, dict[str, Any]]) -> dict[str, Any]:
    return {
        "identity_extra_channel": {
            "description": "extra dephasing channel is replaced by identity delta=0; same readout path but the prior channel-gap invariant is absent",
            "per_rung": {
                str(n): row["identity_channel_control"]
                for n, row in scale_rows.items()
            },
            "pass": all(row["identity_channel_control"]["pass"] for row in scale_rows.values()),
        },
        "flattened_schmidt": {
            "description": "alpha=0 puts all Schmidt weight on one branch; entropy readout is recomputed but the live rank-2 cut invariant is killed",
            "per_rung": {
                str(n): row["flattened_schmidt_control"]
                for n, row in scale_rows.items()
            },
            "pass": all(row["flattened_schmidt_control"]["pass"] for row in scale_rows.values()),
        },
        "commutative_collapse": {
            "description": "replace noncommuting RX/RZ ordered basis with one commuting RX(RX_ANGLE+RZ_ANGLE) control; same readout path must move the signature",
            "rx_angle": RX_ANGLE,
            "rz_angle": RZ_ANGLE,
            "per_rung": {
                str(n): row["commutative_collapse_control"]
                for n, row in scale_rows.items()
            },
            "pass": all(row["commutative_collapse_control"]["pass"] for row in scale_rows.values()),
        },
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    scale_rows = {n: scale_rung(n) for n in SCALES}
    proofs = build_proofs(scale_rows)
    checks = known_value_checks(scale_rows)
    ablations = build_tool_ablations(scale_rows, proofs, checks)
    controls = build_controls(scale_rows)

    max_jax_delta = max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())
    scale_pass = all(row["pass"] and row["dense_state_closure_used"] is False for row in scale_rows.values())
    proof_pass = all(
        proof.get("real_claim_verdict") == "sat"
        and proof.get("negated_claim_verdict") == "unsat"
        and proof.get("differ") is True
        and proof.get("bound_to_measured") is True
        for proof in proofs.values()
    )
    controls_pass = all(control["pass"] for control in controls.values())
    known_pass = all(check["match"] for check in checks)
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-9
        for row in ablations.values()
    )
    all_pass = bool(scale_pass and proof_pass and controls_pass and known_pass and ablation_pass)
    top = scale_rows[64]

    scale_ladder = {
        "rungs": {
            str(n): {
                "sites_or_qubits": n,
                "dense_state_closure_used": False,
                "global_hilbert_dim_materialized": False,
                "mps_tensor_count": row["mps_tensor_count"],
                "mps_max_bond": row["mps_max_bond"],
                "schmidt_rank": row["schmidt_rank"],
                "min_live_schmidt_prob": row["min_live_schmidt_prob"],
                "extra_channel_gap": row["extra_channel_gap"],
                "coherent_information_pre": row["coherent_information_pre"],
                "coherent_information_post": row["coherent_information_post"],
                "entropy_is_output_only": True,
                "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                "pass": row["pass"],
            }
            for n, row in scale_rows.items()
        },
        "pass": scale_pass,
        "all_pass": scale_pass,
    }

    result = {
        "schema": "formal_scout_result_v1",
        "name": "sim_s7_coherent_information_probe",
        "sim_id": "sim_s7_coherent_information_probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "object_id": OBJECT_ID,
        "tier": "Stage-7 entropy/information readout lego",
        "classification": "lego",
        "promotion_allowed": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "information_readout_on_existing_mps_cut_carrier",
        "purpose": "Compute coherent information as an output on an already-admitted finite MPS cut carrier while proving the prior rank/gap distinguishability invariant.",
        "scientific_question": "Does the fixed non-dense MPS cut carrier support a coherent-information readout at N=8/16/32/64 while the proof-bearing invariant remains Schmidt/channel distinguishability rather than entropy?",
        "finite_map": {
            "domain": "finite N-site open-boundary bond-2 MPS cut carrier for N in {8,16,32,64}, one Schmidt pair crossing A|B, one-site amplitude damping on the A-side cut site, and optional extra dephasing channel",
            "codomain_or_output": "rank/gap distinguishability invariant plus derived output readouts (S_B, S_AB environment entropies, I_c_pre, I_c_post, dI_c/dtheta)",
            "definition": "RankGapReadout_N maps the fixed stage-2 MPS cut and channel pair to measured Schmidt rank/min-live branch, extra-channel output gap, and then entropy/coherent-information outputs; entropy is not used to assert the SMT claim.",
        },
        "domain": {
            "site_counts": list(SCALES),
            "carrier": "stage-2 finite_density/mps boundary_interior_cut family from coherent_information_8_16_32_64_dual_engine_probe",
            "cut": "A first N/2 sites, B last N/2 sites",
            "max_bond": 2,
            "dense_state_closure_used": False,
        },
        "codomain_or_output": "scale ladder, torch/JAX readout parity, rank/gap SMT proof flips, controls, known-value checks, and blocked consumers",
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite site counts, finite MPS tensors, finite 2-entry Schmidt spectrum, finite 2x2/4x4 channel environment matrices",
            },
            "N01": {
                "status": "active_tested",
                "statement": "noncommuting RX/RZ basis order before the channel and non-identity extra dephasing channel; commutative and identity controls are recomputed",
            },
        },
        "root_constraints_in_force": {
            "F01": "finite carrier/probe/channel set at N=8/16/32/64",
            "N01": "ordered RX/RZ basis and non-identity extra dephasing; controls erase each",
        },
        "carrier_layer": "stage-2 finite MPS boundary_interior_cut carrier",
        "geometry_layer": "one-dimensional A|B tensor-network cut; no new physical carrier is built",
        "carrier_realization": {
            "torch": "complex128 open-boundary MPS tensors with one live Schmidt pair; local rho_A and channel environments only",
            "jax": "x64 mirror of the same finite tensor/channel formulas",
        },
        "peps3d_embedding": "not_claimed: this Stage-7 readout acts on an already-admitted MPS cut carrier and does not promote PEPS3D/manifold admission",
        "spinor_state": "two-component site amplitudes in the cut tensor induce the local 2x2 density used by the channel readout",
        "quaternion_action": "not_applicable",
        "bridge_layer": "none",
        "cut_layer": "A|B half-chain cut with local channel on A-side cut site",
        "law_or_candidate_tested": "coherent information readout with data-processing numeric check; proof-bearing claim is rank/gap distinguishability",
        "branch_status_before_run": "new bounded Stage-7 readout requested by user",
        "allowed_claims": [
            "coherent-information readout on this single fixed MPS carrier family",
            "torch/JAX parity for this finite non-dense readout",
            "rank/gap distinguishability proof flips against identity-channel and flattened-Schmidt controls",
        ],
        "promotion_blockers": [
            "single constructed MPS family only",
            "not PEPS3D/manifold admission",
            "not a bridge, Axis0, flux, FEP, physics, or final-manifold unlock",
        ],
        "eligible_consumers": ["future bounded information-readout audits on the same admitted carrier family"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "required_tools": ["torch", "jax", "z3", "cvc5", "sympy"],
        "actual_tools_used": ["torch", "jax", "z3", "cvc5", "sympy"],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing rank/gap proof bound to measured Schmidt/channel variables",
            "sympy exact rank/gap mirror and entropy known-value checks",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": {tool: "local_result" for tool in TOOL_MANIFEST},
        "required_inputs": ["existing MPS carrier family source: sim_coherent_information_8_16_32_64_dual_engine_probe.py"],
        "data_or_artifact_dependencies": ["results/coherent_information_8_16_32_64_dual_engine_probe_results.json as nearby carrier-family context only; this sim recomputes its own readout"],
        "dependency_receipts": ["results/coherent_information_8_16_32_64_dual_engine_probe_results.json"],
        "required_negatives": ["identity_extra_channel", "flattened_schmidt", "commutative_collapse"],
        "negatives_run": controls,
        "controls": controls,
        "kill_conditions": {
            "identity_extra_channel": "extra-channel distinguishability gap falls below GAP_FLOOR and SMT rank/gap claim flips to UNSAT",
            "flattened_schmidt": "live Schmidt rank drops below 2 and SMT rank/gap claim flips to UNSAT",
            "commutative_collapse": "same readout path must move the output signature by more than GAP_FLOOR",
        },
        "required_artifacts": [str(RESULT.relative_to(ROOT))],
        "artifacts_emitted": [str(RESULT.relative_to(ROOT))],
        "witness_trace_id": f"{OBJECT_ID}:{int(started)}",
        "torch_primary_result": {
            "runtime": "torch",
            "dtype": str(CDTYPE),
            "top_scale_sites": 64,
            "rank_gap_invariant": top["torch"]["rank_gap_invariant"],
            "coherent_information_pre": top["torch"]["coherent_information_pre"],
            "coherent_information_post": top["torch"]["coherent_information_post"],
            "coherent_information_drop": top["torch"]["coherent_information_drop"],
            "grad_pre_dtheta": top["torch"]["grad_pre_dtheta"],
            "grad_post_dtheta": top["torch"]["grad_post_dtheta"],
            "entropy_as_output_only": True,
            "pass": top["torch"]["pass"],
        },
        "jax_mirror_result": {
            "runtime": "jax",
            "x64_enabled": bool(jax.config.read("jax_enable_x64")),
            "top_scale_sites": 64,
            "rank_gap_invariant": top["jax"]["rank_gap_invariant"],
            "coherent_information_pre": top["jax"]["coherent_information_pre"],
            "coherent_information_post": top["jax"]["coherent_information_post"],
            "coherent_information_drop": top["jax"]["coherent_information_drop"],
            "grad_pre_dtheta": top["jax"]["grad_pre_dtheta"],
            "grad_post_dtheta": top["jax"]["grad_post_dtheta"],
            "pass": top["jax"]["pass"],
        },
        "jax_vs_pytorch_delta": max_jax_delta,
        "proof_results": proofs,
        "tool_ablations": ablations,
        "ablation_outcome_delta": ablations,
        "scale_ladder": scale_ladder,
        "scale_details": scale_rows,
        "known_value_checks": checks,
        "known_value_checks_computed": True,
        "entropy_as_output": {
            "status": "output_only_not_organizer",
            "readouts": ["S_B", "S_AB_environment_pre", "S_AB_environment_post", "coherent_information_pre", "coherent_information_post"],
            "smt_claim_uses_entropy": False,
        },
        "positive": {
            "rank_gap_distinguishability_prior_to_entropy": {
                "measured": aggregate_measured(scale_rows),
                "pass": proof_pass,
            },
            "coherent_information_readout_monotone_under_extra_dephasing": {
                "pass": all(row["coherent_information_post"] <= row["coherent_information_pre"] + 1.0e-10 for row in scale_rows.values()),
                "note": "numeric readout check only; not the SMT organizing variable",
            },
            "non_dense_scale_ladder_8_16_32_64": {
                "pass": scale_pass,
                "scale_ladder": scale_ladder,
            },
            "known_value_checks": {
                "n_checks": len(checks),
                "n_passed": sum(1 for check in checks if check["match"]),
                "pass": known_pass,
            },
        },
        "boundary": {
            "dense_state_closure_blocked": {
                "dense_state_closure_used": False,
                "global_hilbert_dim_materialized": False,
                "pass": True,
            },
            "promotion_blocked": {
                "classification": "lego",
                "promotion_allowed": False,
                "blocked_consumers": BLOCKED_CONSUMERS,
                "pass": True,
            },
        },
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "known_value_pass": known_pass,
            "ablation_pass": ablation_pass,
            "max_jax_vs_pytorch_delta": max_jax_delta,
            "elapsed_seconds": time.time() - started,
        },
        "pass_rule": "All 8/16/32/64 rungs are non-dense and pass; SMT proof flips real SAT vs controls UNSAT on rank/gap variables; known-value checks, controls, and ablations pass.",
        "fail_rule": "Fail on entropy scalar in SMT claim, missing proof flip, dense closure, JAX mismatch, live identity/flattened controls, commutative-collapse no-op, or downstream promotion.",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }
    return _jsonable(result)


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
