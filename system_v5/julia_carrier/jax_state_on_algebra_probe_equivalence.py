#!/usr/bin/env python3
# object_id: state_on_algebra_probe_equivalence
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite state-on-algebra/probe-equivalence diagnostic only. No
# basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.

import jax

jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "state_on_algebra_probe_equivalence"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "state_on_algebra_probe_equivalence_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "state_on_algebra_probe_equivalence_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
STRUCTURE_PROBE_COUNT = 12
FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]
OFFDIAG_PAIRS = [(0, 1), (0, 2), (1, 2)]


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def paulis() -> tuple[jax.Array, jax.Array, jax.Array, jax.Array]:
    ident = jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
    sx = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
    sy = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
    sz = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
    return ident, sx, sy, sz


def omega_m2(rho: jax.Array, x: jax.Array) -> jax.Array:
    return jnp.trace(rho @ x)


def complex_sample_matrices() -> list[jax.Array]:
    ident, sx, sy, sz = paulis()
    return [
        ident,
        sx,
        sy,
        sz,
        jnp.asarray([[0.2 + 0.1j, -0.4 + 0.3j], [0.7 - 0.2j, 0.5 + 0.6j]], dtype=jnp.complex128),
        jnp.asarray([[-0.1 + 0.8j, 0.25 - 0.35j], [-0.2 + 0.15j, 0.4 - 0.45j]], dtype=jnp.complex128),
    ]


def reconstruct_hermitian_from_probes(expectations: jax.Array, probes: list[jax.Array]) -> jax.Array:
    n = len(probes)
    gram_rows = []
    for i in range(n):
        gram_rows.append([py_float(jnp.real(jnp.trace(probes[i] @ probes[j]))) for j in range(n)])
    gram = jnp.asarray(gram_rows, dtype=jnp.float64)
    coeffs = jnp.linalg.solve(gram, expectations)
    out = jnp.zeros((2, 2), dtype=jnp.complex128)
    for i, probe in enumerate(probes):
        out = out + coeffs[i] * probe
    return out


def von_neumann_entropy(rho: jax.Array) -> float:
    vals = jnp.linalg.eigvalsh(rho)
    total = 0.0
    for idx in range(vals.shape[0]):
        x = max(py_float(jnp.real(vals[idx])), 0.0)
        if x > TOL:
            total -= x * float(jnp.log(x))
    return total


def m2c_checks() -> dict[str, Any]:
    ident, sx, sy, sz = paulis()
    probes = [ident, sx, sy, sz]
    nonspanning = [ident, sz]
    rx, ry, rz = 0.35, -0.22, 0.41
    rho = 0.5 * (ident + rx * sx + ry * sy + rz * sz)
    rho_plus = 0.5 * (ident + 0.20 * sx)
    rho_minus = 0.5 * (ident - 0.20 * sx)
    trace_residual = abs(py_float(jnp.real(jnp.trace(rho))) - 1.0)
    hermitian_residual = py_float(jnp.linalg.norm(rho - jnp.conj(rho.T)))
    min_eigenvalue = py_float(jnp.min(jnp.linalg.eigvalsh(rho)))
    normalization_residual = abs(omega_m2(rho, ident) - 1.0)
    samples = complex_sample_matrices()
    positivity_vals = [py_float(jnp.real(omega_m2(rho, jnp.conj(x.T) @ x))) for x in samples]
    positivity_min = min(positivity_vals)
    a = samples[-2]
    b = samples[-1]
    alpha = 0.3 - 0.2j
    beta = -0.4 + 0.7j
    linearity = py_float(jnp.abs(omega_m2(rho, alpha * a + beta * b) - (alpha * omega_m2(rho, a) + beta * omega_m2(rho, b))))
    star_preservation = max(py_float(jnp.abs(omega_m2(rho, jnp.conj(x.T)) - jnp.conj(omega_m2(rho, x)))) for x in samples)
    expectations = jnp.asarray([py_float(jnp.real(omega_m2(rho, p))) for p in probes], dtype=jnp.float64)
    reconstructed = reconstruct_hermitian_from_probes(expectations, probes)
    spanning_reconstruction_residual = py_float(jnp.linalg.norm(reconstructed - rho))
    spanning_reconstructed_pair_max_abs_diff = max(
        abs(py_float(jnp.real(omega_m2(reconstructed, p))) - py_float(jnp.real(omega_m2(rho, p)))) for p in probes
    )
    full_probe_distinct_gap = max(abs(py_float(jnp.real(omega_m2(rho_plus, p))) - py_float(jnp.real(omega_m2(rho_minus, p)))) for p in probes)
    nonspanning_collision_max_abs_diff = max(abs(py_float(jnp.real(omega_m2(rho_plus, p))) - py_float(jnp.real(omega_m2(rho_minus, p)))) for p in nonspanning)
    nonspanning_state_gap = py_float(jnp.linalg.norm(rho_plus - rho_minus))
    coarse_expectations = jnp.asarray([py_float(jnp.real(omega_m2(rho, p))) for p in nonspanning], dtype=jnp.float64)
    rho_coarse = reconstruct_hermitian_from_probes(coarse_expectations, nonspanning)
    entropy_full = von_neumann_entropy(rho)
    entropy_coarse = von_neumann_entropy(rho_coarse)
    entropy_gap = abs(entropy_coarse - entropy_full)
    bad_trace = jnp.asarray([[0.7, 0.0], [0.0, 0.7]], dtype=jnp.complex128)
    bad_positive = jnp.asarray([[1.2, 0.0], [0.0, -0.2]], dtype=jnp.complex128)
    bad_trace_normalization_residual = abs(py_float(jnp.real(omega_m2(bad_trace, ident))) - 1.0)
    projector_2 = jnp.asarray([[0.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
    bad_positive_min = min(py_float(jnp.real(omega_m2(bad_positive, x))) for x in [ident, projector_2])
    return {
        "state_valid": (
            trace_residual < TOL
            and hermitian_residual < TOL
            and min_eigenvalue >= -TOL
            and py_float(jnp.abs(normalization_residual)) < TOL
            and positivity_min >= -TOL
            and linearity < TOL
            and star_preservation < TOL
        ),
        "spanning_separates": spanning_reconstruction_residual < TOL and full_probe_distinct_gap > 1.0e-3,
        "nonspanning_collision": nonspanning_collision_max_abs_diff < TOL and nonspanning_state_gap > 1.0e-3,
        "entropy_is_readout": entropy_full > 0.0 and entropy_gap > 1.0e-3,
        "bad_controls_ok": bad_trace_normalization_residual > 1.0e-3 and bad_positive_min < -1.0e-3,
        "numbers": {
            "trace_residual": trace_residual,
            "hermitian_residual": hermitian_residual,
            "min_eigenvalue": min_eigenvalue,
            "normalization_residual": py_float(jnp.abs(normalization_residual)),
            "linearity_max_residual": linearity,
            "star_preservation_residual": star_preservation,
            "positivity_min_AstarA": positivity_min,
            "spanning_reconstruction_frobenius_residual": spanning_reconstruction_residual,
            "spanning_reconstructed_pair_max_abs_diff": spanning_reconstructed_pair_max_abs_diff,
            "full_probe_distinct_gap": full_probe_distinct_gap,
            "nonspanning_collision_max_abs_diff": nonspanning_collision_max_abs_diff,
            "nonspanning_state_frobenius_gap": nonspanning_state_gap,
            "entropy_full": entropy_full,
            "entropy_coarse": entropy_coarse,
            "entropy_coarsening_gap_abs": entropy_gap,
            "bad_trace_normalization_residual": bad_trace_normalization_residual,
            "bad_positive_min_AstarA": bad_positive_min,
        },
    }


def qbasis(idx: int) -> jax.Array:
    return jnp.eye(4, dtype=jnp.float64)[idx]


def qreal(x: float) -> jax.Array:
    return jnp.asarray([x, 0.0, 0.0, 0.0], dtype=jnp.float64)


def qzero() -> jax.Array:
    return jnp.zeros((4,), dtype=jnp.float64)


def qconj(q: jax.Array) -> jax.Array:
    return q * jnp.asarray([1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)


def qnorm2(q: jax.Array) -> float:
    return py_float(jnp.sum(q * q))


def qmul(x: jax.Array, y: jax.Array) -> jax.Array:
    a, b, c, d = x
    e, f, g, h = y
    return jnp.asarray(
        [
            a * e - b * f - c * g - d * h,
            a * f + b * e + c * h - d * g,
            a * g - b * h + c * e + d * f,
            a * h + b * g - c * f + d * e,
        ],
        dtype=jnp.float64,
    )


def qmat_zero() -> jax.Array:
    return jnp.zeros((2, 2, 4), dtype=jnp.float64)


def qmat_identity() -> jax.Array:
    out = qmat_zero()
    out = out.at[0, 0, :].set(qreal(1.0))
    out = out.at[1, 1, :].set(qreal(1.0))
    return out


def qmat_z() -> jax.Array:
    out = qmat_zero()
    out = out.at[0, 0, :].set(qreal(1.0))
    out = out.at[1, 1, :].set(qreal(-1.0))
    return out


def qmat_offdiag(q: jax.Array) -> jax.Array:
    out = qmat_zero()
    out = out.at[0, 1, :].set(q)
    out = out.at[1, 0, :].set(qconj(q))
    return out


def qmat_mul(a: jax.Array, b: jax.Array) -> jax.Array:
    out = qmat_zero()
    for i in range(2):
        for k in range(2):
            acc = qzero()
            for j in range(2):
                acc = acc + qmul(a[i, j], b[j, k])
            out = out.at[i, k, :].set(acc)
    return out


def qmat_adj(a: jax.Array) -> jax.Array:
    out = qmat_zero()
    for i in range(2):
        for j in range(2):
            out = out.at[i, j, :].set(qconj(a[j, i]))
    return out


def qmat_real_trace(a: jax.Array) -> float:
    return py_float(a[0, 0, 0] + a[1, 1, 0])


def qmat_inner(a: jax.Array, b: jax.Array) -> float:
    return qmat_real_trace(qmat_mul(a, b))


def qmat_residual(a: jax.Array, b: jax.Array) -> float:
    return py_float(jnp.linalg.norm(jnp.ravel(a - b)))


def qmat_sample_matrices() -> list[jax.Array]:
    samples = [qmat_identity(), qmat_z()]
    for i in range(4):
        samples.append(qmat_offdiag(qbasis(i)))
    row = qmat_zero()
    row = row.at[0, 0, :].set(qreal(0.2))
    row = row.at[0, 1, :].set(jnp.asarray([0.1, -0.4, 0.3, 0.2], dtype=jnp.float64))
    row = row.at[1, 0, :].set(jnp.asarray([-0.2, 0.5, -0.1, 0.4], dtype=jnp.float64))
    row = row.at[1, 1, :].set(jnp.asarray([0.6, -0.3, 0.2, -0.5], dtype=jnp.float64))
    samples.append(row)
    neg = qmat_zero()
    neg = neg.at[0, 0, :].set(qreal(1.0))
    neg = neg.at[0, 1, :].set(-1.0 * qbasis(1))
    samples.append(neg)
    return samples


def qmat_density(a: float, q: jax.Array) -> jax.Array:
    out = qmat_zero()
    out = out.at[0, 0, :].set(qreal(a))
    out = out.at[1, 1, :].set(qreal(1.0 - a))
    out = out.at[0, 1, :].set(q)
    out = out.at[1, 0, :].set(qconj(q))
    return out


def omega_h(rho: jax.Array, x: jax.Array) -> float:
    return qmat_inner(rho, x)


def reconstruct_qhermitian(expectations: jax.Array, probes: list[jax.Array]) -> jax.Array:
    n = len(probes)
    gram_rows = []
    for i in range(n):
        gram_rows.append([qmat_inner(probes[i], probes[j]) for j in range(n)])
    gram = jnp.asarray(gram_rows, dtype=jnp.float64)
    coeffs = jnp.linalg.solve(gram, expectations)
    out = qmat_zero()
    for i in range(n):
        out = out + coeffs[i] * probes[i]
    return out


def quaternionic_checks() -> dict[str, Any]:
    probes = [qmat_identity(), qmat_z()] + [qmat_offdiag(qbasis(i)) for i in range(4)]
    nonspanning = probes[0:3]
    q = jnp.asarray([0.08, 0.05, -0.03, 0.04], dtype=jnp.float64)
    rho = qmat_density(0.55, q)
    trace_residual = abs(qmat_real_trace(rho) - 1.0)
    hermitian_residual = qmat_residual(rho, qmat_adj(rho))
    determinant_margin = 0.55 * 0.45 - qnorm2(q)
    positivity_vals = [omega_h(rho, qmat_mul(qmat_adj(x), x)) for x in qmat_sample_matrices()]
    positivity_min = min(positivity_vals)
    expectations = jnp.asarray([omega_h(rho, p) for p in probes], dtype=jnp.float64)
    reconstructed = reconstruct_qhermitian(expectations, probes)
    reconstruction_residual = qmat_residual(reconstructed, rho)
    rho_plus = qmat_density(0.5, jnp.asarray([0.0, 0.1, 0.0, 0.0], dtype=jnp.float64))
    rho_minus = qmat_density(0.5, jnp.asarray([0.0, -0.1, 0.0, 0.0], dtype=jnp.float64))
    full_probe_distinct_gap = max(abs(omega_h(rho_plus, p) - omega_h(rho_minus, p)) for p in probes)
    nonspanning_collision_max_abs_diff = max(abs(omega_h(rho_plus, p) - omega_h(rho_minus, p)) for p in nonspanning)
    nonspanning_state_gap = qmat_residual(rho_plus, rho_minus)
    bad_rho = qmat_density(0.5, jnp.asarray([0.0, 0.8, 0.0, 0.0], dtype=jnp.float64))
    bad_positive_min = min(omega_h(bad_rho, qmat_mul(qmat_adj(x), x)) for x in qmat_sample_matrices())
    return {
        "state_valid": trace_residual < TOL and hermitian_residual < TOL and determinant_margin > TOL and positivity_min >= -TOL,
        "spanning_separates": reconstruction_residual < TOL and full_probe_distinct_gap > 1.0e-3,
        "nonspanning_collision": nonspanning_collision_max_abs_diff < TOL and nonspanning_state_gap > 1.0e-3,
        "bad_controls_ok": bad_positive_min < -1.0e-3,
        "numbers": {
            "trace_residual": trace_residual,
            "hermitian_residual": hermitian_residual,
            "determinant_margin": determinant_margin,
            "positivity_min_XstarX": positivity_min,
            "spanning_reconstruction_residual": reconstruction_residual,
            "full_probe_distinct_gap": full_probe_distinct_gap,
            "nonspanning_collision_max_abs_diff": nonspanning_collision_max_abs_diff,
            "nonspanning_state_frobenius_gap": nonspanning_state_gap,
            "bad_positive_min_XstarX": bad_positive_min,
        },
    }


def setprod(table: jax.Array, a: int, b: int, c: int, s: float) -> jax.Array:
    return table.at[c, a, b].set(s)


def add_identity(table: jax.Array, dim: int) -> jax.Array:
    for a in range(dim):
        table = setprod(table, 0, a, a, 1.0)
        table = setprod(table, a, 0, a, 1.0)
    return table


def octonion_table() -> jax.Array:
    table = jnp.zeros((8, 8, 8), dtype=jnp.float64)
    table = add_identity(table, 8)
    for a in range(1, 8):
        table = setprod(table, a, a, 0, -1.0)
    for i, j, k in FANO:
        for a, b, c, s in [
            (i, j, k, 1.0),
            (j, k, i, 1.0),
            (k, i, j, 1.0),
            (j, i, k, -1.0),
            (k, j, i, -1.0),
            (i, k, j, -1.0),
        ]:
            table = setprod(table, a, b, c, s)
    return table


def obasis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def omul(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def oct_conj(x: jax.Array) -> jax.Array:
    signs = jnp.asarray([1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)
    return x * signs


def j3_zero() -> jax.Array:
    return jnp.zeros((3, 3, 8), dtype=jnp.float64)


def j3_identity() -> jax.Array:
    out = j3_zero()
    for i in range(3):
        out = out.at[i, i, 0].set(1.0)
    return out


def j3_from_coords(coords: jax.Array) -> jax.Array:
    matrix = j3_zero()
    for i in range(3):
        matrix = matrix.at[i, i, 0].set(coords[i])
    idx = 3
    for i, j in OFFDIAG_PAIRS:
        v = coords[idx:idx + 8]
        matrix = matrix.at[i, j, :].set(v)
        matrix = matrix.at[j, i, :].set(oct_conj(v))
        idx += 8
    return matrix


def j3_coords_basis(idx: int) -> jax.Array:
    return j3_from_coords(jnp.eye(27, dtype=jnp.float64)[idx])


def j3_probe_coords(sample_idx: int, side: int) -> jax.Array:
    vals: list[float] = []
    for j in range(1, 28):
        raw = (
            (sample_idx + 23) * (j + 11) * (side + 3) * 29
            + j ** 2 * 17
            + sample_idx * 31
            + side * 7
        ) % 113
        vals.append((float(raw) - 56.0) / 41.0)
    return jnp.asarray(vals, dtype=jnp.float64)


def j3_matmul(table: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    out = j3_zero()
    for i in range(3):
        for k in range(3):
            acc = jnp.zeros((8,), dtype=jnp.float64)
            for j in range(3):
                acc = acc + omul(table, a[i, j], b[j, k])
            out = out.at[i, k, :].set(acc)
    return out


def jordan(table: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    return 0.5 * (j3_matmul(table, a, b) + j3_matmul(table, b, a))


def j3_trace(a: jax.Array) -> float:
    return py_float(a[0, 0, 0] + a[1, 1, 0] + a[2, 2, 0])


def j3_trace_square_expected(a: jax.Array) -> float:
    total = a[0, 0, 0] ** 2 + a[1, 1, 0] ** 2 + a[2, 2, 0] ** 2
    for i, j in OFFDIAG_PAIRS:
        total = total + 2.0 * jnp.sum(a[i, j, :] ** 2)
    return py_float(total)


def j3_probe_family() -> list[jax.Array]:
    matrices = [j3_coords_basis(idx) for idx in range(27)]
    for sample_idx in range(1, STRUCTURE_PROBE_COUNT + 1):
        matrices.append(j3_from_coords(j3_probe_coords(sample_idx, 5)))
    return matrices


def j3_state_checks() -> dict[str, Any]:
    table = octonion_table()
    probes = j3_probe_family()
    identity = j3_identity()

    def omega(a: jax.Array) -> float:
        return j3_trace(a) / 3.0

    normalization_residual = abs(omega(identity) - 1.0)
    min_square = float("inf")
    max_trace_square_residual = 0.0
    for a in probes:
        square = jordan(table, a, a)
        value = omega(square)
        min_square = min(min_square, value)
        max_trace_square_residual = max(max_trace_square_residual, abs(j3_trace(square) - j3_trace_square_expected(a)))
    p = j3_zero()
    u = obasis(8, 1)
    p = p.at[0, 0, 0].set(0.5)
    p = p.at[1, 1, 0].set(0.5)
    p = p.at[0, 1, :].set(-0.5 * u)
    p = p.at[1, 0, :].set(oct_conj(p[0, 1, :]))
    rank1_idempotent_residual = py_float(jnp.linalg.norm(jnp.ravel(jordan(table, p, p) - p)))
    bad_normalization_residual = abs((j3_trace(identity) / 2.0) - 1.0)
    return {
        "state_valid": normalization_residual < TOL and min_square >= -TOL and max_trace_square_residual < TOL,
        "bad_controls_ok": bad_normalization_residual > 1.0e-3,
        "numbers": {
            "identity_normalization_residual": normalization_residual,
            "positivity_min_square": min_square,
            "trace_square_max_residual": max_trace_square_residual,
            "rank1_idempotent_residual": rank1_idempotent_residual,
            "bad_normalization_residual": bad_normalization_residual,
        },
    }


def prefix_numbers(prefix: str, numbers: dict[str, Any]) -> dict[str, Any]:
    return {f"{prefix}.{key}": value for key, value in numbers.items()}


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "missing_julia_reference",
            "shared_scalar_rows": [],
            "max_diff_key": None,
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(peer_path)}],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": True,
        }
    peer = json.loads(peer_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    max_diff_key = None
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jv = float(value)
        pv = float(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        row = {"key": key, "jax": jv, "julia": pv, "abs_diff": diff}
        rows.append(row)
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    return {
        "peer_result_path": str(peer_path),
        "status": "compared",
        "shared_scalar_rows": rows,
        "max_diff_key": max_diff_key,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff < TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    m2c = m2c_checks()
    h = quaternionic_checks()
    j3o = j3_state_checks()
    verdicts = {
        "state_on_algebra_valid_M2C": bool(m2c["state_valid"]),
        "state_on_algebra_valid_H": bool(h["state_valid"]),
        "state_on_algebra_valid_J3O": bool(j3o["state_valid"]),
        "state_on_algebra_valid_all": bool(m2c["state_valid"] and h["state_valid"] and j3o["state_valid"]),
        "probe_relative_identity": bool(m2c["spanning_separates"] and m2c["nonspanning_collision"] and h["spanning_separates"] and h["nonspanning_collision"]),
        "entropy_is_readout": bool(m2c["entropy_is_readout"]),
    }
    controls = {
        "M2C_bad_functionals_fail": bool(m2c["bad_controls_ok"]),
        "H_bad_functional_fails": bool(h["bad_controls_ok"]),
        "J3O_bad_normalization_fails": bool(j3o["bad_controls_ok"]),
    }
    controls["control_miswired"] = not (
        controls["M2C_bad_functionals_fail"]
        and controls["H_bad_functional_fails"]
        and controls["J3O_bad_normalization_fails"]
    )
    shared_scalars = {}
    shared_scalars.update(prefix_numbers("M2C", m2c["numbers"]))
    shared_scalars.update(prefix_numbers("H", h["numbers"]))
    shared_scalars.update(prefix_numbers("J3O", j3o["numbers"]))
    shared_booleans: dict[str, bool] = {}
    for key, value in verdicts.items():
        shared_booleans[f"verdict.{key}"] = bool(value)
    for key, value in controls.items():
        shared_booleans[f"control.{key}"] = bool(value)
    all_verdicts = all(bool(v) for v in verdicts.values())
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax_full_sim",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Finite state-on-algebra/probe-equivalence diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.",
        "sim_execution_kind": "nonclassical",
        "sim_class": "state_probe_equivalence_probe",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "question": "Can state-on-algebra be computed as a positive normalized probe-functional across M2(C), quaternionic 2x2 observables, and J3(O), with identity only relative to the probe family?",
        "tool_manifest": {
            "JAX": "load_bearing complex, quaternionic, and octonionic finite algebra construction",
            "jax.numpy": "load_bearing x64 eigenvalue, norm, reconstruction, entropy, and finite algebra computations",
            "JSON": "supportive result serialization",
        },
        "tool_integration_depth": {
            "JAX": "load_bearing",
            "jax.numpy": "load_bearing",
            "JSON": "supportive",
        },
        "verdicts": verdicts,
        "controls": controls,
        "numbers": shared_scalars,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "algebras": {
            "M2C": {"basis": "Hermitian Pauli probe basis I,X,Y,Z", "state": "density matrix rho"},
            "H": {"basis": "2x2 quaternionic Hermitian basis I,Z,offdiag{1,i,j,k}", "state": "positive trace-one quaternionic Hermitian matrix"},
            "J3O": {"basis": "3x3 octonionic Hermitian Jordan algebra coordinates", "state": "normalized trace functional omega(A)=Tr(A)/3"},
        },
        "plain_sentence": "A state can be computed as a positive normalized functional on M2(C), quaternionic 2x2 observables, and J3(O); probe identity changes when the probe family is coarsened, and entropy is only a downstream readout of rho.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = controls["control_miswired"] or not all_verdicts or bool(result["parity"]["stop_condition_fired"])
    return result


def print_summary(result: dict[str, Any]) -> None:
    s = result["shared_scalars"]
    print("state_on_algebra_probe_equivalence - JAX full sim")
    print(
        f"classification: {result['classification']} | promotion_allowed: {str(result['promotion_allowed']).lower()} | "
        f"formal_admission_allowed: {str(result['formal_admission_allowed']).lower()} | jax_enable_x64: {str(result['jax_enable_x64']).lower()}"
    )
    print(
        f"state_on_algebra_valid_M2C={str(result['verdicts']['state_on_algebra_valid_M2C']).lower()} "
        f"min_eigen={s['M2C.min_eigenvalue']} positivity_min={s['M2C.positivity_min_AstarA']}"
    )
    print(
        f"state_on_algebra_valid_H={str(result['verdicts']['state_on_algebra_valid_H']).lower()} "
        f"determinant_margin={s['H.determinant_margin']} positivity_min={s['H.positivity_min_XstarX']}"
    )
    print(
        f"state_on_algebra_valid_J3O={str(result['verdicts']['state_on_algebra_valid_J3O']).lower()} "
        f"positivity_min_square={s['J3O.positivity_min_square']} trace_square_residual={s['J3O.trace_square_max_residual']}"
    )
    print(
        f"probe_relative_identity={str(result['verdicts']['probe_relative_identity']).lower()} "
        f"M2C_nonspan_collision={s['M2C.nonspanning_collision_max_abs_diff']} H_nonspan_collision={s['H.nonspanning_collision_max_abs_diff']}"
    )
    print(
        f"entropy_is_readout={str(result['verdicts']['entropy_is_readout']).lower()} "
        f"entropy_full={s['M2C.entropy_full']} entropy_coarse={s['M2C.entropy_coarse']} gap={s['M2C.entropy_coarsening_gap_abs']}"
    )
    parity = result["parity"]
    print(f"parity_max_diff={parity['parity_max_diff']} within_1e-9={str(parity['within_1e_9']).lower()} max_diff_key={parity.get('max_diff_key')}")
    if parity["strict_divergence_gt_1e_6"] or parity["boolean_mismatches"] or parity["missing_keys"]:
        print("STOP: JAX and Julia disagree beyond the strict parity stop condition:")
        print(json.dumps({
            "strict_divergence_gt_1e_6": parity["strict_divergence_gt_1e_6"],
            "boolean_mismatches": parity["boolean_mismatches"],
            "missing_keys": parity["missing_keys"],
        }, indent=2, sort_keys=True))
    if result["controls"]["control_miswired"]:
        print("STOP: state_on_algebra_probe_equivalence control failed.")
    print(result["plain_sentence"])
    print(f"wrote: {result['result_path']}")
    if not result["stop_condition_fired"]:
        print("CODEX2_B2_DONE")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
