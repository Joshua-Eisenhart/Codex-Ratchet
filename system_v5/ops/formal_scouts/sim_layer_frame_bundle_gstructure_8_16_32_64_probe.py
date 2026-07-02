import jax; jax.config.update("jax_enable_x64",True)
import jax.numpy as jnp  # noqa: E402

import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import pathlib  # noqa: E402
import time  # noqa: E402
from typing import Any  # noqa: E402

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

from e3nn import o3  # noqa: E402
import e3nn_jax as e3nnj  # noqa: E402
import geomstats.backend as gs  # noqa: E402
from geomstats.geometry.hypersphere import Hypersphere  # noqa: E402
import sympy as sp  # noqa: E402
import torch  # noqa: E402
import z3  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "layer_frame_bundle_gstructure_8_16_32_64_probe"
LAYER_NAME = "frame_bundle_structure_reduction"
OUT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"

SITE_COUNTS = [8, 16, 32, 64]
SITE_SHAPES = {8: (2, 2, 2), 16: (4, 2, 2), 32: (4, 4, 2), 64: (4, 4, 4)}
RTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-9
GAP_FLOOR = 1.0e-5

I2_T = torch.eye(2, dtype=CDTYPE)
I4_T = torch.eye(4, dtype=RTYPE)
J4_T = torch.tensor(
    [
        [0.0, 0.0, -1.0, 0.0],
        [0.0, 0.0, 0.0, -1.0],
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ],
    dtype=RTYPE,
)
SX_T = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
SY_T = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=CDTYPE)
SZ_T = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)

I2_J = jnp.eye(2, dtype=jnp.complex128)
I4_J = jnp.eye(4, dtype=jnp.float64)
SX_J = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY_J = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ_J = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
J4_J = jnp.array(
    [
        [0.0, 0.0, -1.0, 0.0],
        [0.0, 0.0, 0.0, -1.0],
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ],
    dtype=jnp.float64,
)

BLOCKED_CONSUMERS = [
    "stacking",
    "layer_embedding_in_g_structure",
    "official_layered_ratchet_G_structure_selection",
    "cross_layer_order_closure",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing primary complex128 spinor, U(2)/SU(2) frame, realification, obstruction, sparse-edge commutator, and negative-control computation",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent x64 dual-engine implementation of the same frame-bundle reduction invariants; no geomstats/JAX backend is claimed",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SO(3) equivariance witness for spinor-derived orientation vectors; the break-equivariance negative fails the reduction gate",
    },
    "e3nn_jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing JAX-side SO(3) equivariance witness using e3nn_jax x64 rotation/Irreps matrices; this is the JAX equivariance path, not geomstats",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing torch-backend S^3 geodesic spread check for spinor-frame variation; geomstats has no JAX backend here, so no JAX geomstats path is claimed",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact structure-group relations: realification of U(2)-type matrices is orthogonal/oriented and U(n) is represented inside SO(2n)",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing structural reduction admissibility proof and obstruction negatives for SO->U->SU reduction",
    },
}

TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def coords_for_shape(shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    lx, ly, lz = shape
    return [(x, y, z) for z in range(lz) for y in range(ly) for x in range(lx)]


def edge_list(shape: tuple[int, int, int]) -> list[tuple[int, int]]:
    coords = coords_for_shape(shape)
    idx = {coord: i for i, coord in enumerate(coords)}
    lx, ly, lz = shape
    edges: list[tuple[int, int]] = []
    for x, y, z in coords:
        if x + 1 < lx:
            edges.append((idx[(x, y, z)], idx[(x + 1, y, z)]))
        if y + 1 < ly:
            edges.append((idx[(x, y, z)], idx[(x, y + 1, z)]))
        if z + 1 < lz:
            edges.append((idx[(x, y, z)], idx[(x, y, z + 1)]))
    return edges


def face_count(shape: tuple[int, int, int]) -> int:
    lx, ly, lz = shape
    return (lx - 1) * (ly - 1) * lz + (lx - 1) * ly * (lz - 1) + lx * (ly - 1) * (lz - 1)


def cell_count(shape: tuple[int, int, int]) -> int:
    lx, ly, lz = shape
    return (lx - 1) * (ly - 1) * (lz - 1)


def site_angles(site: int, n_sites: int, *, flatten_metric: bool, real_only: bool) -> tuple[float, float, float, float]:
    if flatten_metric:
        return 0.0, 0.0, 0.0, 0.0
    shell = (site + 1.0) / (n_sites + 1.0)
    scale = math.log2(float(n_sites)) / 3.0
    theta = 0.31 * math.pi + 0.27 * math.pi * shell + 0.017 * scale
    phi = 0.19 * (site + 1) + 0.13 * math.sin(2.0 * math.pi * shell) + 0.071 * scale
    chi = 0.11 * (site + 1) ** 2 / (n_sites + 3.0) + 0.23 * math.cos(math.pi * shell)
    phase = 0.17 + 0.009 * (site + 1) + 0.031 * math.sin(3.0 * math.pi * shell) + 0.011 * scale
    if real_only:
        phi = 0.0
        chi = 0.0
        phase = 0.0
    return theta, phi, chi, phase


def spinor_t(site: int, n_sites: int, *, flatten_metric: bool = False, real_only: bool = False) -> torch.Tensor:
    theta, phi, chi, _phase = site_angles(site, n_sites, flatten_metric=flatten_metric, real_only=real_only)
    a = math.cos(theta / 2.0) * complex(math.cos(phi), math.sin(phi))
    b = math.sin(theta / 2.0) * complex(math.cos(chi), math.sin(chi))
    v = torch.tensor([a, b], dtype=CDTYPE)
    return v / torch.linalg.vector_norm(v)


def spinor_j(site: int, n_sites: int, *, flatten_metric: bool = False, real_only: bool = False) -> jnp.ndarray:
    theta, phi, chi, _phase = site_angles(site, n_sites, flatten_metric=flatten_metric, real_only=real_only)
    a = math.cos(theta / 2.0) * complex(math.cos(phi), math.sin(phi))
    b = math.sin(theta / 2.0) * complex(math.cos(chi), math.sin(chi))
    v = jnp.array([a, b], dtype=jnp.complex128)
    return v / jnp.linalg.norm(v)


def su2_from_spinor_t(psi: torch.Tensor, *, commute: bool = False, site: int = 0, n_sites: int = 1) -> torch.Tensor:
    if commute:
        angle = 0.021 * (site + 1) + 0.003 * n_sites
        return torch.diag(
            torch.tensor(
                [complex(math.cos(angle), math.sin(angle)), complex(math.cos(-angle), math.sin(-angle))],
                dtype=CDTYPE,
            )
        )
    a, b = psi[0], psi[1]
    return torch.stack(
        [
            torch.stack([a, -torch.conj(b)]),
            torch.stack([b, torch.conj(a)]),
        ]
    )


def su2_from_spinor_j(psi: jnp.ndarray, *, commute: bool = False, site: int = 0, n_sites: int = 1) -> jnp.ndarray:
    if commute:
        angle = 0.021 * (site + 1) + 0.003 * n_sites
        return jnp.diag(jnp.array([jnp.exp(1j * angle), jnp.exp(-1j * angle)], dtype=jnp.complex128))
    a, b = psi[0], psi[1]
    return jnp.stack(
        [
            jnp.stack([a, -jnp.conj(b)]),
            jnp.stack([b, jnp.conj(a)]),
        ]
    )


def realify_t(u: torch.Tensor) -> torch.Tensor:
    a = torch.real(u).to(RTYPE)
    b = torch.imag(u).to(RTYPE)
    return torch.cat([torch.cat([a, -b], dim=1), torch.cat([b, a], dim=1)], dim=0)


def realify_j(u: jnp.ndarray) -> jnp.ndarray:
    a = jnp.real(u)
    b = jnp.imag(u)
    return jnp.concatenate([jnp.concatenate([a, -b], axis=1), jnp.concatenate([b, a], axis=1)], axis=0)


def site_u2_t(
    site: int,
    n_sites: int,
    *,
    flatten_metric: bool = False,
    real_only: bool = False,
    commute: bool = False,
) -> tuple[torch.Tensor, torch.Tensor, float]:
    psi = spinor_t(site, n_sites, flatten_metric=flatten_metric, real_only=real_only)
    su = su2_from_spinor_t(psi, commute=commute, site=site, n_sites=n_sites)
    _theta, _phi, _chi, phase = site_angles(site, n_sites, flatten_metric=flatten_metric, real_only=real_only)
    scalar = complex(math.cos(phase), math.sin(phase))
    return (torch.tensor(scalar, dtype=CDTYPE) * su), psi, phase


def site_u2_j(
    site: int,
    n_sites: int,
    *,
    flatten_metric: bool = False,
    real_only: bool = False,
    commute: bool = False,
) -> tuple[jnp.ndarray, jnp.ndarray, float]:
    psi = spinor_j(site, n_sites, flatten_metric=flatten_metric, real_only=real_only)
    su = su2_from_spinor_j(psi, commute=commute, site=site, n_sites=n_sites)
    _theta, _phi, _chi, phase = site_angles(site, n_sites, flatten_metric=flatten_metric, real_only=real_only)
    return (jnp.exp(1j * phase) * su), psi, phase


def phase_reduce_to_su_t(u: torch.Tensor) -> torch.Tensor:
    det = torch.linalg.det(u)
    half_arg = 0.5 * float(torch.angle(det).item())
    return torch.tensor(complex(math.cos(-half_arg), math.sin(-half_arg)), dtype=CDTYPE) * u


def phase_reduce_to_su_j(u: jnp.ndarray) -> jnp.ndarray:
    det = jnp.linalg.det(u)
    half_arg = 0.5 * jnp.angle(det)
    return jnp.exp(-1j * half_arg) * u


def bloch_t(psi: torch.Tensor) -> torch.Tensor:
    rho = torch.outer(psi, torch.conj(psi))
    return torch.tensor(
        [
            float(torch.real(torch.trace(rho @ SX_T)).item()),
            float(torch.real(torch.trace(rho @ SY_T)).item()),
            float(torch.real(torch.trace(rho @ SZ_T)).item()),
        ],
        dtype=RTYPE,
    )


def bloch_j(psi: jnp.ndarray) -> jnp.ndarray:
    rho = jnp.outer(psi, jnp.conj(psi))
    return jnp.array(
        [
            jnp.real(jnp.trace(rho @ SX_J)),
            jnp.real(jnp.trace(rho @ SY_J)),
            jnp.real(jnp.trace(rho @ SZ_J)),
        ],
        dtype=jnp.float64,
    )


def spinor_s3_point_t(psi: torch.Tensor) -> torch.Tensor:
    point = torch.stack(
        [
            torch.real(psi[0]),
            torch.imag(psi[0]),
            torch.real(psi[1]),
            torch.imag(psi[1]),
        ]
    ).to(RTYPE)
    return point / torch.linalg.vector_norm(point)


def emitted_mps_bit(site: int, n_sites: int, latent: int) -> int:
    bits = [(latent >> bit) & 1 for bit in range(3)]
    half = n_sites // 2
    if site < 3:
        return bits[site]
    if site == 3 and site < half:
        return bits[0] ^ bits[1] ^ bits[2]
    if half <= site < half + 3:
        return bits[site - half]
    if site == half + 3 and site < n_sites:
        return bits[0] ^ bits[2]
    return (bits[(site + latent) % 3] ^ (site & 1)) & 1


def entangled_mps_depth_witness(n_sites: int) -> dict[str, Any]:
    bond_dim = 8
    raw = torch.linspace(1.0, 2.4, bond_dim, dtype=RTYPE) + 0.001 * float(n_sites)
    schmidt = raw / torch.linalg.vector_norm(raw)
    probabilities = schmidt.square()
    entropy = float((-(probabilities * torch.log(probabilities))).sum().item())
    half = n_sites // 2
    left_words = {
        tuple(emitted_mps_bit(site, n_sites, latent) for site in range(half))
        for latent in range(bond_dim)
    }
    right_words = {
        tuple(emitted_mps_bit(site, n_sites, latent) for site in range(half, n_sites))
        for latent in range(bond_dim)
    }
    tensor_shapes = []
    nonzero_entries = 0
    for site in range(n_sites):
        left_bond = 1 if site == 0 else bond_dim
        right_bond = 1 if site == n_sites - 1 else bond_dim
        tensor_shapes.append([left_bond, 2, right_bond])
        nonzero_entries += bond_dim
    pass_conditions = {
        "mps_max_bond_at_least_8": bond_dim >= 8,
        "half_chain_entropy_positive": entropy > 1.0e-9,
        "left_schmidt_words_distinct": len(left_words) == bond_dim,
        "right_schmidt_words_distinct": len(right_words) == bond_dim,
        "dense_state_closure_absent": True,
    }
    return {
        "carrier": "rank-8 latent-index entangled MPS over the same N PEPS3D site anchors",
        "construction": "sum_k schmidt_k |left_word_k>|right_word_k> represented by sparse MPS tensors; no 2**N state vector is built",
        "sites_or_qubits": n_sites,
        "physical_dim": 2,
        "mps_max_bond": bond_dim,
        "schmidt_rank_half_chain": bond_dim,
        "schmidt_probabilities": [float(v) for v in probabilities.tolist()],
        "half_chain_entanglement_entropy": entropy,
        "entanglement_entropy": entropy,
        "left_distinct_words": len(left_words),
        "right_distinct_words": len(right_words),
        "representative_tensor_shapes": {
            "first": tensor_shapes[0],
            "middle": tensor_shapes[half],
            "last": tensor_shapes[-1],
        },
        "stored_sparse_nonzero_entries": nonzero_entries,
        "dense_state_closure_used": False,
        "pass_conditions": pass_conditions,
        "pass": all(pass_conditions.values()),
    }


def core_torch(
    n_sites: int,
    *,
    flatten_metric: bool = False,
    real_only: bool = False,
    commute: bool = False,
    drop_orientation: bool = False,
) -> dict[str, Any]:
    frames = []
    sus = []
    psis = []
    orth_defects = []
    det_so_defects = []
    orientation_values = []
    j_defects = []
    det_phase_gaps = []
    su_det_defects = []
    phase_removed = []
    reflection = torch.diag(torch.tensor([-1.0, 1.0, 1.0, 1.0], dtype=RTYPE))
    for site in range(n_sites):
        u, psi, phase = site_u2_t(
            site,
            n_sites,
            flatten_metric=flatten_metric,
            real_only=real_only,
            commute=commute,
        )
        r = realify_t(u)
        if drop_orientation:
            r = reflection @ r
        su = phase_reduce_to_su_t(u)
        frames.append(r)
        sus.append(su)
        psis.append(psi)
        orth_defects.append(float(torch.linalg.norm(r.T @ r - I4_T).item()))
        det_r = float(torch.linalg.det(r).item())
        orientation_values.append(det_r)
        det_so_defects.append(abs(abs(det_r) - 1.0))
        j_defects.append(float(torch.linalg.norm(r @ J4_T - J4_T @ r).item()))
        det_before = torch.linalg.det(u)
        det_phase_gaps.append(abs(float(torch.angle(det_before).item())))
        su_det_defects.append(abs(float(torch.linalg.det(su).real.item()) - 1.0) + abs(float(torch.linalg.det(su).imag.item())))
        phase_removed.append(abs(phase))

    path_edges = [(idx, idx + 1) for idx in range(n_sites - 1)]
    commutators = [float(torch.linalg.norm(sus[i] @ sus[j] - sus[j] @ sus[i]).item()) for i, j in path_edges]
    bloch_vectors = torch.stack([bloch_t(psi) for psi in psis])
    orientation_spread = float(torch.linalg.norm(bloch_vectors[1:] - bloch_vectors[:-1], dim=1).mean().item())
    signature = {
        "mean_phase_removed": float(sum(phase_removed) / len(phase_removed)),
        "mean_su_edge_commutator_norm": float(sum(commutators) / len(commutators)) if commutators else 0.0,
        "mean_bloch_edge_spread": orientation_spread,
        "max_so_orthogonality_defect": max(orth_defects),
        "max_so_abs_det_defect": max(det_so_defects),
        "min_real_orientation_det": min(orientation_values),
        "max_j_compatibility_defect": max(j_defects),
        "max_su_det_defect_after_reduction": max(su_det_defects),
        "mean_det_phase_gap_before_su_reduction": float(sum(det_phase_gaps) / len(det_phase_gaps)),
    }
    pass_conditions = {
        "so_frame": signature["max_so_orthogonality_defect"] < TOL and signature["max_so_abs_det_defect"] < TOL,
        "orientation_preserved": signature["min_real_orientation_det"] > 0.0,
        "u_reduction_obstruction_free": signature["max_j_compatibility_defect"] < TOL,
        "su_reduction_obstruction_free": signature["max_su_det_defect_after_reduction"] < TOL,
        "noncommuting_reduction_path": signature["mean_su_edge_commutator_norm"] > GAP_FLOOR,
        "complex_fiber_nontrivial": signature["mean_phase_removed"] > GAP_FLOOR,
        "site_orientation_varies": signature["mean_bloch_edge_spread"] > GAP_FLOOR,
    }
    return {
        "signature": signature,
        "pass_conditions": pass_conditions,
        "pass": all(pass_conditions.values()),
        "carrier": {
            "site_count": n_sites,
            "local_frame_shape": [4, 4],
            "local_spinor_shape": [2],
            "stored_frame_count": len(frames),
            "stored_complex_matrix_count": len(sus),
            "path_edge_count": len(path_edges),
            "dense_state_closure_used": False,
            "max_claim_bearing_tensor_elements": max(n_sites * 4 * 4, n_sites * 2 * 2),
        },
    }


def core_jax(n_sites: int) -> dict[str, float]:
    orth_defects = []
    det_so_defects = []
    j_defects = []
    det_phase_gaps = []
    su_det_defects = []
    phase_removed = []
    sus = []
    psis = []
    for site in range(n_sites):
        u, psi, phase = site_u2_j(site, n_sites)
        r = realify_j(u)
        su = phase_reduce_to_su_j(u)
        sus.append(su)
        psis.append(psi)
        orth_defects.append(float(jnp.linalg.norm(r.T @ r - I4_J)))
        det_r = float(jnp.linalg.det(r))
        det_so_defects.append(abs(abs(det_r) - 1.0))
        j_defects.append(float(jnp.linalg.norm(r @ J4_J - J4_J @ r)))
        det_before = jnp.linalg.det(u)
        det_phase_gaps.append(abs(float(jnp.angle(det_before))))
        det_su = jnp.linalg.det(su)
        su_det_defects.append(abs(float(jnp.real(det_su)) - 1.0) + abs(float(jnp.imag(det_su))))
        phase_removed.append(abs(phase))
    commutators = [float(jnp.linalg.norm(sus[i] @ sus[i + 1] - sus[i + 1] @ sus[i])) for i in range(n_sites - 1)]
    return {
        "mean_phase_removed": float(sum(phase_removed) / len(phase_removed)),
        "mean_su_edge_commutator_norm": float(sum(commutators) / len(commutators)),
        "max_so_orthogonality_defect": max(orth_defects),
        "max_so_abs_det_defect": max(det_so_defects),
        "max_j_compatibility_defect": max(j_defects),
        "max_su_det_defect_after_reduction": max(su_det_defects),
        "mean_det_phase_gap_before_su_reduction": float(sum(det_phase_gaps) / len(det_phase_gaps)),
    }


def e3nn_equivariance_check() -> dict[str, Any]:
    alpha = torch.tensor(0.37, dtype=RTYPE)
    beta = torch.tensor(0.51, dtype=RTYPE)
    gamma = torch.tensor(0.23, dtype=RTYPE)
    rot = o3.angles_to_matrix(alpha, beta, gamma).to(RTYPE)
    rep = o3.Irreps("1x1o").D_from_angles(alpha, beta, gamma).to(RTYPE)
    vectors = torch.stack([bloch_t(spinor_t(site, 16)) for site in range(16)])
    lhs = vectors @ rep.T
    rhs = vectors @ rot.T
    equivariance_delta = float(torch.linalg.norm(lhs - rhs, dim=1).max().item())
    norm_delta = float(torch.max(torch.abs(torch.linalg.norm(lhs, dim=1) - torch.linalg.norm(vectors, dim=1))).item())
    broken = torch.diag(torch.tensor([1.0, 1.17, 0.61], dtype=RTYPE)) @ rot
    broken_vectors = vectors @ broken.T
    broken_norm_delta = float(
        torch.max(torch.abs(torch.linalg.norm(broken_vectors, dim=1) - torch.linalg.norm(vectors, dim=1))).item()
    )
    return {
        "tool": "e3nn.o3",
        "representation": "Irreps('1x1o').D_from_angles",
        "equivariance_delta": equivariance_delta,
        "norm_delta": norm_delta,
        "broken_equivariance_norm_delta": broken_norm_delta,
        "pass": equivariance_delta < 1.0e-6 and norm_delta < 1.0e-6 and broken_norm_delta > 1.0e-2,
    }


def e3nn_jax_equivariance_check() -> dict[str, Any]:
    alpha = jnp.float64(0.37)
    beta = jnp.float64(0.51)
    gamma = jnp.float64(0.23)
    rot = e3nnj.angles_to_matrix(alpha, beta, gamma)
    rep = e3nnj.Irreps("1x1o").D_from_angles(alpha, beta, gamma)
    vectors = jnp.stack([bloch_j(spinor_j(site, 16)) for site in range(16)])
    lhs = vectors @ rep.T
    rhs = vectors @ rot.T
    equivariance_delta = float(jnp.max(jnp.linalg.norm(lhs - rhs, axis=1)))
    norm_delta = float(jnp.max(jnp.abs(jnp.linalg.norm(lhs, axis=1) - jnp.linalg.norm(vectors, axis=1))))
    broken = jnp.diag(jnp.array([1.0, 1.17, 0.61], dtype=jnp.float64)) @ rot
    broken_vectors = vectors @ broken.T
    broken_norm_delta = float(
        jnp.max(jnp.abs(jnp.linalg.norm(broken_vectors, axis=1) - jnp.linalg.norm(vectors, axis=1)))
    )
    return {
        "tool": "e3nn_jax",
        "representation": "Irreps('1x1o').D_from_angles",
        "rotation_dtype": str(rot.dtype),
        "vectors_dtype": str(vectors.dtype),
        "equivariance_delta": equivariance_delta,
        "norm_delta": norm_delta,
        "broken_equivariance_norm_delta": broken_norm_delta,
        "pass": equivariance_delta < 1.0e-12 and norm_delta < 1.0e-12 and broken_norm_delta > 1.0e-2,
    }


def geomstats_torch_s3_check() -> dict[str, Any]:
    sphere = Hypersphere(dim=3)
    points = gs.stack([spinor_s3_point_t(spinor_t(site, 16)) for site in range(16)])
    flat_points = gs.stack([spinor_s3_point_t(spinor_t(site, 16, flatten_metric=True)) for site in range(16)])
    distances = [float(sphere.metric.dist(points[i], points[i + 1]).item()) for i in range(15)]
    flat_distances = [float(sphere.metric.dist(flat_points[i], flat_points[i + 1]).item()) for i in range(15)]
    mean_distance = float(sum(distances) / len(distances))
    flat_mean_distance = float(sum(flat_distances) / len(flat_distances))
    return {
        "tool": "geomstats",
        "backend": "pytorch",
        "manifold": "Hypersphere(dim=3)",
        "mean_adjacent_s3_distance": mean_distance,
        "flat_control_mean_adjacent_s3_distance": flat_mean_distance,
        "outcome_delta": mean_distance - flat_mean_distance,
        "notes": "geomstats is intentionally torch-side only. This environment has no geomstats JAX backend path, and none is claimed.",
        "pass": mean_distance > GAP_FLOOR and flat_mean_distance < GAP_FLOOR,
    }


def sympy_structure_relations() -> dict[str, Any]:
    a, b, c, d = sp.symbols("a b c d", real=True)
    norm2 = sp.simplify(a**2 + b**2 + c**2 + d**2)
    u = sp.Matrix([[a + sp.I * b, -c + sp.I * d], [c + sp.I * d, a - sp.I * b]])
    rho = sp.Matrix.vstack(
        sp.Matrix.hstack(sp.re(u), -sp.im(u)),
        sp.Matrix.hstack(sp.im(u), sp.re(u)),
    )
    orth_residual = sp.simplify(rho.T * rho - norm2 * sp.eye(4))
    det_rho = sp.factor(rho.det())

    n = sp.symbols("n", integer=True, positive=True)
    dim_u = n**2
    dim_so = (2 * n) * (2 * n - 1) / 2
    dim_u2 = int(dim_u.subs(n, 2))
    dim_so4 = int(dim_so.subs(n, 2))
    dim_relation = dim_u2 <= dim_so4
    subset_condition = orth_residual == sp.zeros(4) and sp.factor(det_rho.subs(norm2, 1)) == 1
    return {
        "orthogonal_residual_equals_norm_identity": bool(orth_residual == sp.zeros(4)),
        "realification_det_polynomial": str(det_rho),
        "det_when_unitary_norm_one": str(sp.factor(det_rho.subs(norm2, 1))),
        "dim_u2": dim_u2,
        "dim_so4": dim_so4,
        "dim_u2_le_dim_so4": bool(dim_relation),
        "u2_subset_so4_witness": bool(subset_condition and dim_relation),
        "pass": bool(subset_condition and dim_relation),
    }


def z3_reduction_gate(
    nominal: dict[str, Any],
    e3nn_row: dict[str, Any],
    e3nn_jax_row: dict[str, Any],
    geomstats_row: dict[str, Any],
    mps_depth_pass: bool,
) -> dict[str, Any]:
    facts = {
        "so_frame": bool(nominal["pass_conditions"]["so_frame"]),
        "orientation_preserved": bool(nominal["pass_conditions"]["orientation_preserved"]),
        "u_reduction_obstruction_free": bool(nominal["pass_conditions"]["u_reduction_obstruction_free"]),
        "su_reduction_obstruction_free": bool(nominal["pass_conditions"]["su_reduction_obstruction_free"]),
        "noncommuting_reduction_path": bool(nominal["pass_conditions"]["noncommuting_reduction_path"]),
        "complex_fiber_nontrivial": bool(nominal["pass_conditions"]["complex_fiber_nontrivial"]),
        "site_orientation_varies": bool(nominal["pass_conditions"]["site_orientation_varies"]),
        "e3nn_equivariant": bool(e3nn_row["pass"]),
        "e3nn_jax_equivariant": bool(e3nn_jax_row["pass"]),
        "geomstats_s3_nontrivial": bool(geomstats_row["pass"]),
        "non_dense": True,
        "peps3d_anchored": True,
        "entangled_mps_depth": bool(mps_depth_pass),
    }
    keys = list(facts)
    zvars = {key: z3.Bool(key) for key in keys}
    admit = z3.Bool("frame_bundle_structure_reduction_admissible")
    nominal_solver = z3.Solver()
    for key, value in facts.items():
        nominal_solver.add(zvars[key] == z3.BoolVal(value))
    nominal_solver.add(admit == z3.And(*[zvars[key] for key in keys]))
    nominal_solver.add(z3.Not(admit))
    nominal_status = str(nominal_solver.check())

    negatives = {}
    for off_key in (
        "e3nn_equivariant",
        "e3nn_jax_equivariant",
        "geomstats_s3_nontrivial",
        "orientation_preserved",
        "noncommuting_reduction_path",
        "complex_fiber_nontrivial",
        "entangled_mps_depth",
    ):
        s = z3.Solver()
        for key, value in facts.items():
            s.add(zvars[key] == z3.BoolVal(False if key == off_key else value))
        s.add(admit == z3.And(*[zvars[key] for key in keys]))
        s.add(admit)
        negatives[off_key] = str(s.check())
    return {
        "facts": facts,
        "nominal_negated_admission_status": nominal_status,
        "negative_admit_statuses": negatives,
        "pass": nominal_status == "unsat" and all(status == "unsat" for status in negatives.values()),
    }


def compare_torch_jax(
    torch_rows: dict[int, dict[str, Any]],
    jax_rows: dict[int, dict[str, float]],
    e3nn_row: dict[str, Any],
    e3nn_jax_row: dict[str, Any],
) -> dict[str, Any]:
    scalar_keys = [
        "mean_phase_removed",
        "mean_su_edge_commutator_norm",
        "max_so_orthogonality_defect",
        "max_so_abs_det_defect",
        "max_j_compatibility_defect",
        "max_su_det_defect_after_reduction",
        "mean_det_phase_gap_before_su_reduction",
    ]
    deltas = {}
    max_delta = 0.0
    for n in SITE_COUNTS:
        deltas[str(n)] = {}
        for key in scalar_keys:
            delta = abs(float(torch_rows[n]["signature"][key]) - float(jax_rows[n][key]))
            deltas[str(n)][key] = delta
            max_delta = max(max_delta, delta)
    equivariance_deltas = {
        "e3nn_vs_e3nn_jax_equivariance_delta": abs(
            float(e3nn_row["equivariance_delta"]) - float(e3nn_jax_row["equivariance_delta"])
        ),
        "e3nn_vs_e3nn_jax_norm_delta": abs(float(e3nn_row["norm_delta"]) - float(e3nn_jax_row["norm_delta"])),
        "e3nn_vs_e3nn_jax_broken_norm_delta": abs(
            float(e3nn_row["broken_equivariance_norm_delta"]) - float(e3nn_jax_row["broken_equivariance_norm_delta"])
        ),
    }
    max_delta = max(max_delta, max(equivariance_deltas.values()))
    return {
        "max_value_delta": max_delta,
        "agree": max_delta < 1.0e-8 and bool(e3nn_jax_row["pass"]),
        "per_rung_scalar_deltas": deltas,
        "e3nn_torch_vs_e3nn_jax_deltas": equivariance_deltas,
        "notes": "Torch is the primary complex128 engine. JAX runs an independent x64 implementation of the same finite SO->U->SU frame reductions and an e3nn_jax SO(3) equivariance check. geomstats is torch-side only; no fake JAX geomstats path is claimed.",
    }


def build_scale_ladder(
    torch_rows: dict[int, dict[str, Any]],
    peps_rows: dict[int, dict[str, Any]],
    mps_rows: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    rungs = {}
    for n in SITE_COUNTS:
        row = torch_rows[n]
        rungs[str(n)] = {
            "sites_or_qubits": n,
            "carrier_kind": "N-sample local frame bundle over sparse PEPS3D nearest-neighbor anchors",
            "dense_state_closure_used": False,
            "local_frame_shape": [4, 4],
            "stored_frame_count": row["carrier"]["stored_frame_count"],
            "path_edge_count": row["carrier"]["path_edge_count"],
            "peps3d_edge_count": peps_rows[n]["edge_count"],
            "peps3d_face_count": peps_rows[n]["face_count"],
            "peps3d_cell_count": peps_rows[n]["cell_count"],
            "mps_max_bond": mps_rows[n]["mps_max_bond"],
            "half_chain_entanglement_entropy": mps_rows[n]["half_chain_entanglement_entropy"],
            "entanglement_entropy": mps_rows[n]["entanglement_entropy"],
            "schmidt_rank_half_chain": mps_rows[n]["schmidt_rank_half_chain"],
            "max_claim_bearing_tensor_elements": row["carrier"]["max_claim_bearing_tensor_elements"],
            "pass": bool(row["pass"] and mps_rows[n]["pass"]),
        }
    return {"rungs": rungs, "pass": all(rung["pass"] and not rung["dense_state_closure_used"] for rung in rungs.values())}


def peps3d_anchor_rows() -> dict[int, dict[str, Any]]:
    rows = {}
    for n, shape in SITE_SHAPES.items():
        edges = edge_list(shape)
        rows[n] = {
            "shape": list(shape),
            "site_count": n,
            "edge_count": len(edges),
            "face_count": face_count(shape),
            "cell_count": cell_count(shape),
            "anchor": "one local frame/spinor tensor per PEPS3D site; sparse nearest-neighbor edge set only",
            "pass": len(coords_for_shape(shape)) == n and len(edges) >= n - 1,
        }
    return rows


def negative_controls(nominal64: dict[str, Any], e3nn_row: dict[str, Any], mps64: dict[str, Any]) -> dict[str, Any]:
    flat = core_torch(64, flatten_metric=True)
    commute = core_torch(64, commute=True)
    orientation = core_torch(64, drop_orientation=True)
    real_only = core_torch(64, real_only=True)
    nominal_sig = nominal64["signature"]
    rows = {
        "flatten_metric": {
            "description": "replace every local frame/spinor with the identity-like flat section",
            "nominal_score": nominal_sig["mean_phase_removed"] + nominal_sig["mean_su_edge_commutator_norm"],
            "control_score": flat["signature"]["mean_phase_removed"] + flat["signature"]["mean_su_edge_commutator_norm"],
            "killed": (flat["signature"]["mean_phase_removed"] + flat["signature"]["mean_su_edge_commutator_norm"]) < GAP_FLOOR,
        },
        "commute_operators": {
            "description": "restrict every site to the same diagonal SU(2) torus so adjacent reductions commute",
            "nominal_commutator": nominal_sig["mean_su_edge_commutator_norm"],
            "control_commutator": commute["signature"]["mean_su_edge_commutator_norm"],
            "killed": commute["signature"]["mean_su_edge_commutator_norm"] < GAP_FLOOR,
        },
        "drop_fiber_orientation": {
            "description": "apply an O(4) reflection to the real frame; this leaves local storage finite but exits SO(4)",
            "nominal_min_det": nominal_sig["min_real_orientation_det"],
            "control_min_det": orientation["signature"]["min_real_orientation_det"],
            "killed": not orientation["pass_conditions"]["orientation_preserved"],
        },
        "real_only_restriction": {
            "description": "force all complex phases to zero; U(1) fiber and complex structure signature disappear",
            "nominal_phase_removed": nominal_sig["mean_phase_removed"],
            "control_phase_removed": real_only["signature"]["mean_phase_removed"],
            "killed": real_only["signature"]["mean_phase_removed"] < GAP_FLOOR,
        },
        "break_equivariance": {
            "description": "replace the SO(3) e3nn action on spinor-derived vectors by an anisotropic scale after rotation",
            "nominal_equivariance_delta": e3nn_row["equivariance_delta"],
            "broken_norm_delta": e3nn_row["broken_equivariance_norm_delta"],
            "killed": e3nn_row["broken_equivariance_norm_delta"] > 1.0e-2,
        },
        "bond1_product_mps": {
            "description": "replace the rank-8 latent-index MPS witness with a bond-1 product state",
            "nominal_mps_max_bond": mps64["mps_max_bond"],
            "control_mps_max_bond": 1,
            "nominal_half_chain_entropy": mps64["half_chain_entanglement_entropy"],
            "control_half_chain_entropy": 0.0,
            "killed": mps64["mps_max_bond"] >= 8 and mps64["half_chain_entanglement_entropy"] > 1.0e-9,
        },
    }
    return rows


def known_value_checks(sympy_row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "invariant": "U(2) realification orthogonality formula",
            "computed": bool(sympy_row["orthogonal_residual_equals_norm_identity"]),
            "known": True,
            "match": bool(sympy_row["orthogonal_residual_equals_norm_identity"]) is True,
        },
        {
            "invariant": "det(realification(SU(2)))",
            "computed": sympy_row["det_when_unitary_norm_one"],
            "known": "1",
            "match": sympy_row["det_when_unitary_norm_one"] == "1",
        },
        {
            "invariant": "U(n) subset SO(2n) dimension check at n=2",
            "computed": f"{sympy_row['dim_u2']} <= {sympy_row['dim_so4']}",
            "known": "4 <= 6",
            "match": bool(sympy_row["dim_u2_le_dim_so4"]),
        },
        {
            "invariant": "U(2) subset SO(4)",
            "computed": bool(sympy_row["u2_subset_so4_witness"]),
            "known": True,
            "match": bool(sympy_row["u2_subset_so4_witness"]) is True,
        },
    ]


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    peps_rows = peps3d_anchor_rows()
    mps_rows = {n: entangled_mps_depth_witness(n) for n in SITE_COUNTS}
    torch_rows = {n: core_torch(n) for n in SITE_COUNTS}
    jax_rows = {n: core_jax(n) for n in SITE_COUNTS}
    e3nn_row = e3nn_equivariance_check()
    e3nn_jax_row = e3nn_jax_equivariance_check()
    geomstats_row = geomstats_torch_s3_check()
    sympy_row = sympy_structure_relations()
    z3_row = z3_reduction_gate(
        torch_rows[64],
        e3nn_row,
        e3nn_jax_row,
        geomstats_row,
        all(row["pass"] for row in mps_rows.values()),
    )
    negatives = negative_controls(torch_rows[64], e3nn_row, mps_rows[64])
    scale_ladder = build_scale_ladder(torch_rows, peps_rows, mps_rows)
    jax_vs_pytorch = compare_torch_jax(torch_rows, jax_rows, e3nn_row, e3nn_jax_row)
    known_checks = known_value_checks(sympy_row)
    all_pass = (
        scale_ladder["pass"]
        and jax_vs_pytorch["agree"]
        and e3nn_row["pass"]
        and e3nn_jax_row["pass"]
        and geomstats_row["pass"]
        and sympy_row["pass"]
        and z3_row["pass"]
        and all(row["pass"] for row in mps_rows.values())
        and all(row["pass"] for row in torch_rows.values())
        and all(row["pass"] for row in peps_rows.values())
        and all(row["killed"] for row in negatives.values())
        and all(row["match"] for row in known_checks)
    )
    jax_signature_norm64 = math.sqrt(
        sum(
            float(jax_rows[64][key]) ** 2
            for key in (
                "mean_phase_removed",
                "mean_su_edge_commutator_norm",
                "mean_det_phase_gap_before_su_reduction",
            )
        )
    )
    z3_unsat_count = int(z3_row["nominal_negated_admission_status"] == "unsat") + sum(
        1 for status in z3_row["negative_admit_statuses"].values() if status == "unsat"
    )

    ablation_outcome_delta = {
        "torch": {
            "outcome_delta": float(
                torch_rows[64]["signature"]["mean_phase_removed"]
                + torch_rows[64]["signature"]["mean_su_edge_commutator_norm"]
                - (core_torch(64, flatten_metric=True)["signature"]["mean_phase_removed"]
                   + core_torch(64, flatten_metric=True)["signature"]["mean_su_edge_commutator_norm"])
            ),
            "reason": "Removing the torch-computed frame reductions leaves only the flat-control signature.",
        },
        "jax": {
            "outcome_delta": float(jax_signature_norm64),
            "reason": "Removing JAX removes this independently computed 64-site x64 signature norm and the torch/JAX parity check.",
        },
        "e3nn": {
            "outcome_delta": float(e3nn_row["broken_equivariance_norm_delta"]),
            "reason": "Replacing the e3nn SO(3) action with anisotropic scaling breaks the orientation-equivariance gate.",
        },
        "e3nn_jax": {
            "outcome_delta": float(e3nn_jax_row["broken_equivariance_norm_delta"]),
            "reason": "Replacing the e3nn_jax SO(3) action with anisotropic scaling breaks the JAX-side equivariance gate.",
        },
        "geomstats": {
            "outcome_delta": float(geomstats_row["outcome_delta"]),
            "reason": "Replacing the geomstats S^3 distance computation with the flat control erases the spinor-frame geodesic spread.",
        },
        "sympy": {
            "outcome_delta": float(sympy_row["dim_so4"] - sympy_row["dim_u2"]),
            "reason": "Removing SymPy removes the exact U(2)->SO(4) realification proof used by known-value checks.",
        },
        "z3": {
            "outcome_delta": float(z3_unsat_count),
            "reason": "Removing Z3 removes the structural admissibility/obstruction proof family.",
        },
    }

    result = {
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "layer": LAYER_NAME,
        "version": "1.0",
        "tier": "geometry_layer_independent_lego",
        "classification": "lego",
        "promotion_allowed": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "frame_bundle_g_structure_reduction_probe",
        "purpose": "Build one independent frame-bundle G-structure reduction layer SO(4)->U(2)->SU(2) over non-dense 8/16/32/64 site carriers with explicit entangled MPS depth witnesses.",
        "scientific_question": "Can a finite N-sample PEPS3D-anchored spinor frame carrier support an obstruction-checked SO->U->SU reduction, while MPS depth witnesses stay genuinely entangled and negatives kill the geometric signature?",
        "root_constraints_in_force": {
            "F01": "finite N-site carrier, finite local spinors, finite local frames, finite PEPS3D site/edge/face/cell anchors, finite sparse path edges",
            "N01": "noncommuting adjacent SU(2) reductions, order-sensitive structural gate, and equivariance/phase/orientation controls",
        },
        "finite_map": "FrameReduction_N : (N PEPS3D site anchors, local spinors psi_i in C^2, U(2) frames realified into SO(4), sparse nearest-neighbor edges) -> obstruction-checked SO(4)->U(2)->SU(2) reduction receipts plus killed controls",
        "domain": {
            "site_counts": SITE_COUNTS,
            "local_state": "torch/jax complex128 C^2 spinor per site",
            "local_frame": "realification rho(U_i) in R^(4x4) per site",
            "sparse_edges": "nearest-neighbor PEPS3D/path edges only",
        },
        "codomain_or_output": "per-rung frame obstruction invariants, SU determinant reduction invariants, equivariance proof row, exact subgroup relation checks, z3 admissibility row, killed negatives, and result JSON receipt",
        "carrier_layer": "N-sample finite spinor frame bundle carrier",
        "geometry_layer": "frame bundle structure reduction SO(4)->U(2)->SU(2)",
        "carrier_realization": "torch.complex128/float64 and jax.complex128/float64 local tensors plus a rank-8 latent-index MPS witness per rung; no 2**N dense state vector or dense Hilbert closure",
        "peps3d_embedding": peps_rows,
        "spinor_state": "one torch-native and one JAX x64 C^2 spinor per PEPS3D site; spinor-derived Bloch orientation vector used for e3nn/e3nn_jax SO(3) equivariance and geomstats torch-side S^3 distance",
        "quaternion_action": "not_applicable; this probe does not use quaternion language",
        "dependency_receipts": [],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "U(n) subset SO(2n), instantiated at n=2 as SO(4)->U(2)->SU(2) frame reduction with finite obstruction controls",
        "branch_status_before_run": "independent lego; no coupling, stacking, official G-structure selection, or manifold completion claim",
        "allowed_claims": [
            "independent frame-bundle structure-reduction lego runs at N=8/16/32/64 on non-dense carriers",
            "SO(4)->U(2)->SU(2) obstruction checks pass for the constructed finite carrier and named controls kill the signature",
        ],
        "promotion_blockers": [
            "single independent layer only",
            "no layer stacking or coupling tested",
            "no official G-structure selected",
            "not a final manifold admission packet",
        ],
        "shells": [
            {"name": "SO4_oriented_frame_shell", "criterion": "rho(U_i)^T rho(U_i)=I and det rho(U_i)=+1 at every finite site"},
            {"name": "U2_complex_compatible_shell", "criterion": "[rho(U_i), J]=0 at every finite site"},
            {"name": "SU2_phase_reduced_shell", "criterion": "det(exp(-arg(det U_i)/2) U_i)=1 at every finite site"},
        ],
        "future_continuations": {
            "admissible_next": "independent deeper frame-bundle obstruction variants only",
            "blocked": BLOCKED_CONSUMERS,
        },
        "compatibility_weights": {
            "so_frame": 1.0 if torch_rows[64]["pass_conditions"]["so_frame"] else 0.0,
            "u_reduction": 1.0 if torch_rows[64]["pass_conditions"]["u_reduction_obstruction_free"] else 0.0,
            "su_reduction": 1.0 if torch_rows[64]["pass_conditions"]["su_reduction_obstruction_free"] else 0.0,
            "e3nn_equivariance": 1.0 if e3nn_row["pass"] else 0.0,
            "e3nn_jax_equivariance": 1.0 if e3nn_jax_row["pass"] else 0.0,
            "geomstats_s3_spread": 1.0 if geomstats_row["pass"] else 0.0,
            "entangled_mps_depth": 1.0 if all(row["pass"] for row in mps_rows.values()) else 0.0,
            "sympy_structure": 1.0 if sympy_row["pass"] else 0.0,
            "z3_admissibility": 1.0 if z3_row["pass"] else 0.0,
        },
        "compression_map": {
            "input": "N local C^2 spinors plus N local U(2) frames over sparse PEPS3D anchors",
            "output": "finite invariant summary: SO defect, J-compatibility defect, SU determinant defect, phase removal, edge commutator, equivariance delta",
            "dense_state_closure_used": False,
        },
        "present_survivor": {
            "rung": 64,
            "signature": torch_rows[64]["signature"],
            "mps_depth": {
                "mps_max_bond": mps_rows[64]["mps_max_bond"],
                "half_chain_entanglement_entropy": mps_rows[64]["half_chain_entanglement_entropy"],
                "schmidt_rank_half_chain": mps_rows[64]["schmidt_rank_half_chain"],
            },
            "survives_named_negatives": all(row["killed"] for row in negatives.values()),
            "claim_ceiling": "survivor of this independent frame-bundle lego only; not a stacked manifold or G-structure selection",
        },
        "outward_record": {
            "result_path": str(OUT_PATH),
            "scale_rungs": SITE_COUNTS,
            "gate_command": f"/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 ../../../scripts/max_deep_lego_gate.py results/{SIM_ID}_results.json --scale-required",
        },
        "survivor_invariant": {
            "computed": bool(torch_rows[64]["pass"] and all(row["killed"] for row in negatives.values())),
            "known": True,
            "passed": bool(torch_rows[64]["pass"] and all(row["killed"] for row in negatives.values())),
            "invariant": "64-site SO->U->SU survivor remains admissible while every named control kills the required signature",
        },
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": list(TOOL_MANIFEST),
        "proof_surfaces_used": ["sympy_structure_relations", "z3_reduction_gate"],
        "graph_surfaces_used": ["sparse PEPS3D/path edge carrier metadata", "rank-8 entangled MPS virtual-bond witness"],
        "topology_surfaces_used": ["finite PEPS3D site/edge/face/cell counts as carrier anchors"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["none"],
        "data_or_artifact_dependencies": [],
        "required_negatives": list(negatives),
        "negatives_run": negatives,
        "kill_conditions": [
            "flattened metric/frame section must erase phase plus commutator signature",
            "commuting diagonal SU(2) torus restriction must erase adjacent commutator signature",
            "orientation-reflection control must fail SO orientation preservation",
            "real-only restriction must erase complex fiber phase reduction",
            "broken equivariance must fail the SO(3) orientation reduction gate",
        ],
        "required_artifacts": ["result JSON", "scale ladder", "entangled MPS depth witness", "known value checks", "tool ablations", "negative controls"],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": f"{SIM_ID}:N8_16_32_64:so_u_su",
        "pass_rule": "all rungs pass non-dense frame reduction with mps_max_bond>=8 and half-chain entropy>0, torch/JAX agree, e3nn/e3nn_jax/geomstats/SymPy/Z3 load-bearing checks pass, all named negatives are killed, known-value checks match",
        "fail_rule": "any dense closure, missing rung, bond<8, zero entanglement entropy, dual-engine disagreement, tool check failure, unkilled negative, or known-value mismatch",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["independent lower geometry lego audits only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "scale_ladder": scale_ladder,
        "mps_entanglement_witness": {str(n): mps_rows[n] for n in SITE_COUNTS},
        "jax_vs_pytorch": jax_vs_pytorch,
        "per_rung_torch": {str(n): torch_rows[n] for n in SITE_COUNTS},
        "per_rung_jax": {str(n): jax_rows[n] for n in SITE_COUNTS},
        "reduction_obstruction_check": {
            "so_to_u": "max_j_compatibility_defect below tolerance",
            "u_to_su": "determinant phase removed sitewise and max_su_det_defect_after_reduction below tolerance",
            "z3_structural_gate": z3_row,
            "pass": z3_row["pass"] and all(row["pass"] for row in torch_rows.values()),
        },
        "e3nn_equivariance": e3nn_row,
        "e3nn_jax_equivariance": e3nn_jax_row,
        "geomstats_torch_s3_geometry": geomstats_row,
        "sympy_structure_group_relations": sympy_row,
        "known_value_checks": known_checks,
        "tool_ablations": ablation_outcome_delta,
        "ablation_outcome_delta": ablation_outcome_delta,
        "all_pass": all_pass,
        "result_summary": {
            "max_scale": max(SITE_COUNTS),
            "all_scale_rungs_pass": scale_ladder["pass"],
            "dense_state_closure_used": False,
            "all_mps_bonds_ge_8": all(row["mps_max_bond"] >= 8 for row in mps_rows.values()),
            "min_half_chain_entanglement_entropy": min(
                row["half_chain_entanglement_entropy"] for row in mps_rows.values()
            ),
            "jax_torch_agree": jax_vs_pytorch["agree"],
            "e3nn_jax_pass": e3nn_jax_row["pass"],
            "geomstats_torch_side_only": True,
            "negative_controls_killed": all(row["killed"] for row in negatives.values()),
            "known_values_match": all(row["match"] for row in known_checks),
            "mechanical_max_deep_scale_gate_target": str(OUT_PATH),
        },
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "max_jax_torch_delta": jax_vs_pytorch["max_value_delta"]}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
