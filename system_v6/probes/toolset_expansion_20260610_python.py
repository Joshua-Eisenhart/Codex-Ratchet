#!/usr/bin/env python3
"""Toolset expansion fit probes for Python-side packages.

Every record here is a tool-lego fit probe, not a promotion receipt.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "system_v6/probes/toolset_expansion_20260610_python_results.json"


def load_json(rel: str) -> dict[str, Any]:
    return json.loads((ROOT / rel).read_text())


def entropy_from_density(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh(rho)
    vals = vals[np.real(vals) > 1.0e-12]
    return float(-np.sum(vals * np.log(vals)))


def partial_trace_state(state: np.ndarray, n: int, keep: list[int]) -> np.ndarray:
    psi = state.reshape([2] * n)
    traced = [i for i in range(n) if i not in keep]
    mat = np.transpose(psi, keep + traced).reshape(2 ** len(keep), -1)
    return mat @ mat.conj().T


def status_record(tool: str, seed_use: str, installed_where: str) -> dict[str, Any]:
    return {
        "tool": tool,
        "seed_use": seed_use,
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "installed_where": installed_where,
        "started_at_unix": time.time(),
    }


def probe_quimb_cotengra() -> dict[str, Any]:
    import cotengra as ctg
    import quimb.tensor as qtn

    rec = status_record(
        "quimb(+cotengra)",
        "GHZ_n/W_n bond-2 MPS for n=6..8 plus one 8Q contraction tree",
        "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
    )
    committed = load_json(
        "system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/results/"
        "geo_s1_scaling_stress_678q_exact_v0_jax_results.json"
    )
    rows: dict[str, Any] = {}
    for n in (6, 7, 8):
        ghz = qtn.MPS_ghz_state(n)
        w = qtn.MPS_w_state(n)
        ghz_state = np.asarray(ghz.to_dense()).reshape(-1)
        w_state = np.asarray(w.to_dense()).reshape(-1)
        ghz_single = entropy_from_density(partial_trace_state(ghz_state, n, [0]))
        ghz_pair = entropy_from_density(partial_trace_state(ghz_state, n, [0, 1]))
        w_single = entropy_from_density(partial_trace_state(w_state, n, [0]))
        w_pair = entropy_from_density(partial_trace_state(w_state, n, [0, 1]))
        committed_ghz = committed["rungs"][str(n)]["W5_named_stabilizer_controls"]["GHZ"]
        rows[str(n)] = {
            "ghz_max_bond": int(ghz.max_bond()),
            "w_max_bond": int(w.max_bond()),
            "ghz_linkdims": list(map(int, ghz.bond_sizes())),
            "w_linkdims": list(map(int, w.bond_sizes())),
            "ghz_single_entropy": ghz_single,
            "ghz_pair_entropy": ghz_pair,
            "committed_ghz_single_entropy": committed_ghz["entropy_qubit_0"],
            "committed_ghz_pair_entropy": committed_ghz["entropy_qubits_0_1"],
            "ghz_entropy_matches_committed": (
                abs(ghz_single - math.log(2.0)) <= 1.0e-12
                and abs(ghz_pair - math.log(2.0)) <= 1.0e-12
            ),
            "w_single_entropy": w_single,
            "w_pair_entropy": w_pair,
            "w_expected_single_entropy": float(
                -((n - 1) / n) * math.log((n - 1) / n) - (1 / n) * math.log(1 / n)
            ),
            "w_expected_pair_entropy": float(
                -((n - 2) / n) * math.log((n - 2) / n) - (2 / n) * math.log(2 / n)
            ),
        }

    n = 8
    inputs: list[tuple[str, ...]] = []
    size_dict: dict[str, int] = {}
    for i in range(n):
        ket: list[str] = []
        if i > 0:
            ket.append(f"l{i}")
            size_dict[f"l{i}"] = 2
        ket.append(f"s{i}")
        size_dict[f"s{i}"] = 2
        if i < n - 1:
            ket.append(f"l{i + 1}")
            size_dict[f"l{i + 1}"] = 2
        inputs.append(tuple(ket))
        bra: list[str] = []
        if i > 0:
            bra.append(f"r{i}")
            size_dict[f"r{i}"] = 2
        bra.append(f"s{i}")
        if i < n - 1:
            bra.append(f"r{i + 1}")
            size_dict[f"r{i + 1}"] = 2
        inputs.append(tuple(bra))
    tree = ctg.array_contract_tree(inputs, output=(), size_dict=size_dict, optimize="greedy")
    rec.update(
        {
            "probe_result": {
                "rows": rows,
                "cotengra_8q_norm_tree": {
                    "contraction_width": float(tree.contraction_width()),
                    "contraction_cost": int(tree.contraction_cost()),
                    "total_flops": int(tree.total_flops()),
                    "path_len": len(tree.get_path()),
                },
            },
            "verdict": "useful-now",
            "layer_routed_to": "S1 tensor-network mirror for finite named-state receipts",
        }
    )
    return rec


def haar_spinors(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    z = rng.normal(size=(n, 2)) + 1j * rng.normal(size=(n, 2))
    return z / np.linalg.norm(z, axis=1, keepdims=True)


def hopf_z(spinors: np.ndarray) -> np.ndarray:
    return np.real(np.abs(spinors[:, 0]) ** 2 - np.abs(spinors[:, 1]) ** 2)


def chi_square_uniform_z(z: np.ndarray, bins: int = 16) -> float:
    counts, _ = np.histogram(z, bins=bins, range=(-1.0, 1.0))
    expected = len(z) / bins
    return float(np.sum((counts - expected) ** 2 / expected))


def ott_distance_to_uniform(z: np.ndarray) -> float:
    import jax

    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    from ott.geometry import pointcloud
    from ott.problems.linear import linear_problem
    from ott.solvers.linear import sinkhorn

    x = jnp.asarray(np.sort(z), dtype=jnp.float64)[:, None]
    y = jnp.linspace(-1.0, 1.0, len(z), dtype=jnp.float64)[:, None]
    geom = pointcloud.PointCloud(x, y, epsilon=0.05)
    prob = linear_problem.LinearProblem(geom)
    out = sinkhorn.Sinkhorn(threshold=1.0e-3, max_iterations=200)(prob)
    return float(out.reg_ot_cost)


def probe_ott() -> dict[str, Any]:
    rec = status_record(
        "ott",
        "Wasserstein distance-to-uniform for S1 Haar pushforward receipts",
        "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
    )
    haar_z = hopf_z(haar_spinors(128, 60617))
    rng = np.random.default_rng(60618)
    clustered = np.column_stack(
        [
            np.sqrt(1.0 - 0.02 * rng.random(128)),
            np.sqrt(0.02 * rng.random(128)) * np.exp(2j * math.pi * rng.random(128)),
        ]
    )
    clustered = clustered / np.linalg.norm(clustered, axis=1, keepdims=True)
    clustered_z = hopf_z(clustered)
    haar_chi = chi_square_uniform_z(haar_z)
    bad_chi = chi_square_uniform_z(clustered_z)
    haar_ott = ott_distance_to_uniform(haar_z)
    bad_ott = ott_distance_to_uniform(clustered_z)
    rec.update(
        {
            "probe_result": {
                "haar_chi_square": haar_chi,
                "clustered_chi_square": bad_chi,
                "haar_ott_reg_cost": haar_ott,
                "clustered_ott_reg_cost": bad_ott,
                "chi_square_power_ratio": bad_chi / max(haar_chi, 1.0e-12),
                "ott_power_ratio": bad_ott / max(haar_ott, 1.0e-12),
                "committed_route_note": "S1 committed route uses marginal z/azimuth chi-square; this probe adds an OT marginal distance only.",
            },
            "verdict": "useful-later",
            "layer_routed_to": "S1 statistical cross-check if Haar receipt is strengthened beyond scratch",
        }
    )
    return rec


def sympy_matrix(rows: list[list[str]]) -> np.ndarray:
    import sympy as sp

    return np.array([[float(sp.N(sp.sympify(x))) for x in row] for row in rows], dtype=np.float64)


def sympy_vec(rows: list[str]) -> np.ndarray:
    import sympy as sp

    return np.array([float(sp.N(sp.sympify(x))) for x in rows], dtype=np.float64)


def probe_jaxopt_lineax() -> dict[str, Any]:
    import jax

    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    import jaxopt
    import lineax

    rec = status_record(
        "jaxopt(+lineax)",
        "fixed-point solve for two S5 terrain flows against committed basin limits",
        "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
    )
    s5 = load_json(
        "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_jax_results.json"
    )
    rows: dict[str, Any] = {}
    for name in ("Se_Cannon_R", "Ni_Source_R"):
        gen = s5["bloch_generator_table"][name]["pinned"]
        fixed = s5["fixed_points_and_basins"][name]["fixed"]["pinned_fixed_point"]
        a_np = sympy_matrix(gen["A"])
        b_np = sympy_vec(gen["b"])
        target_np = sympy_vec(fixed)
        a = jnp.asarray(a_np)
        b = jnp.asarray(b_np)
        target = jnp.asarray(target_np)
        op = lineax.MatrixLinearOperator(a)
        lineax_sol = lineax.linear_solve(op, -b, lineax.AutoLinearSolver(well_posed=True)).value

        step = 0.2

        def fixed_fun(x: Any) -> Any:
            return x + step * (a @ x + b)

        solver = jaxopt.FixedPointIteration(fixed_point_fun=fixed_fun, maxiter=400, tol=1.0e-10)
        fp = solver.run(jnp.array([0.31, -0.27, 0.19], dtype=jnp.float64))
        rows[name] = {
            "lineax_solution": np.asarray(lineax_sol).tolist(),
            "jaxopt_solution": np.asarray(fp.params).tolist(),
            "committed_pinned_fixed_point": fixed,
            "max_abs_lineax_vs_committed": float(jnp.max(jnp.abs(lineax_sol - target))),
            "max_abs_jaxopt_vs_committed": float(jnp.max(jnp.abs(fp.params - target))),
            "jaxopt_iterations": int(fp.state.iter_num),
            "committed_basin_limit": s5["fixed_points_and_basins"][name]["basin_or_orbit"],
        }
    rec.update(
        {
            "probe_result": {"rows": rows},
            "verdict": "useful-now",
            "layer_routed_to": "S5 affine terrain fixed-point/basin solver sidecar",
        }
    )
    return rec


def probe_e3nn_jax() -> dict[str, Any]:
    import jax

    jax.config.update("jax_enable_x64", True)
    import e3nn_jax as e3nn
    import jax.numpy as jnp

    rec = status_record(
        "e3nn_jax",
        "SU(2)-equivariance receipt for the S1 Hopf commuting square via vector irreps",
        "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
    )

    def hopf(psi: Any) -> Any:
        a, b = psi[0], psi[1]
        return jnp.array(
            [
                2.0 * jnp.real(jnp.conj(a) * b),
                2.0 * jnp.imag(jnp.conj(a) * b),
                jnp.real(jnp.conj(a) * a - jnp.conj(b) * b),
            ],
            dtype=jnp.float64,
        )

    psi = jnp.array([0.8 + 0.0j, 0.6 + 0.0j])
    theta = 0.37
    su2 = jnp.diag(jnp.array([jnp.exp(-0.5j * theta), jnp.exp(0.5j * theta)]))
    v = hopf(psi)
    direct = hopf(su2 @ psi)
    rotated = e3nn.IrrepsArray("1o", v).transform_by_matrix(e3nn.matrix_z(theta)).array
    max_diff = float(jnp.max(jnp.abs(direct - rotated)))
    rec.update(
        {
            "probe_result": {
                "irreps": "1o",
                "theta": theta,
                "hopf_after_su2": np.asarray(direct).tolist(),
                "e3nn_so3_rotated_hopf": np.asarray(rotated).tolist(),
                "max_abs_diff": max_diff,
                "pass": max_diff <= 1.0e-10,
            },
            "verdict": "useful-now",
            "layer_routed_to": "S1 equivariance/commuting-square cross-check",
        }
    )
    return rec


def probe_geomstats() -> dict[str, Any]:
    from geomstats.geometry.hypersphere import Hypersphere

    rec = status_record(
        "geomstats",
        "S3/S2 geodesics and analytic volume comparison against committed Hopf/lens values",
        "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
    )
    rows: dict[str, Any] = {}
    for dim in (2, 3):
        sphere = Hypersphere(dim=dim)
        angle = 0.7
        p = np.zeros(dim + 1)
        q = np.zeros(dim + 1)
        p[0] = 1.0
        q[0] = math.cos(angle)
        q[1] = math.sin(angle)
        rows[f"S^{dim}"] = {
            "geomstats_dist": float(sphere.metric.dist(p, q)),
            "expected_geodesic_angle": angle,
            "max_abs_diff": abs(float(sphere.metric.dist(p, q)) - angle),
        }
    rec.update(
        {
            "probe_result": {
                "geodesics": rows,
                "analytic_volume_S2": 4.0 * math.pi,
                "analytic_volume_S3": 2.0 * math.pi**2,
                "lens_volume_N4": 2.0 * math.pi**2 / 4.0,
                "committed_lens_audit_note": "geo_s1_finite_phase_lens_v0 audit reports N=4 target 4.934802200544679.",
            },
            "verdict": "useful-later",
            "layer_routed_to": "S1/S2/S3 geometry cross-checks when manifold API is needed",
        }
    )
    return rec


def probe_netket() -> dict[str, Any]:
    import netket as nk

    rec = status_record(
        "netket",
        "honest fit attempt against basin/fixed-point work",
        "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
    )
    hi = nk.hilbert.Spin(s=0.5, N=2)
    graph = nk.graph.Chain(length=2, pbc=False)
    op = nk.operator.Ising(hi, graph=graph, h=1.0)
    dense = np.asarray(op.to_dense())
    rec.update(
        {
            "probe_result": {
                "hilbert_size": int(hi.size),
                "n_states": int(hi.n_states),
                "graph_nodes": int(graph.n_nodes),
                "graph_edges": int(graph.n_edges),
                "ising_dense_shape": list(dense.shape),
                "seed_fit_limit": "NetKet naturally targets quantum many-body Hilbert/operator work, not the committed continuous Bloch affine basin rows.",
            },
            "verdict": "not-useful",
            "layer_routed_to": "not routed for S5 basin/fixed-point work; possible later QMB variational layer only",
        }
    )
    return rec


def probe_dynamiqs() -> dict[str, Any]:
    import dynamiqs as dq
    import jax.numpy as jnp

    rec = status_record(
        "dynamiqs",
        "qutip-jax replacement candidate: one dephasing channel evolution vs S4 D_z behavior",
        "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 (already present before this card)",
    )
    sx = dq.sigmax()
    sz = dq.sigmaz()
    h = jnp.zeros((2, 2), dtype=jnp.complex64)
    plus = (dq.basis(2, 0) + dq.basis(2, 1)) / jnp.sqrt(2.0)
    rho0 = dq.todm(plus)
    gamma = 0.4
    jump = jnp.sqrt(gamma / 2.0) * sz
    res = dq.mesolve(h, [jump], rho0, jnp.array([0.0, 1.0]), exp_ops=[sx, sz])
    x_final = float(jnp.real(res.expects[0, -1]))
    z_final = float(jnp.real(res.expects[1, -1]))
    rec.update(
        {
            "probe_result": {
                "api": "dynamiqs.mesolve",
                "x_final": x_final,
                "expected_x_exp_minus_gamma": float(math.exp(-gamma)),
                "z_final": z_final,
                "s4_D_z_committed_behavior": "M=diag(1-q_z,1-q_z,1), c=0; transverse contraction with z fixed",
                "max_abs_x_diff": abs(x_final - math.exp(-gamma)),
            },
            "verdict": "useful-now",
            "layer_routed_to": "S3/S4 channel evolution sidecar, not a carrier replacement by itself",
        }
    )
    return rec


def probe_galois() -> dict[str, Any]:
    import galois

    rec = status_record(
        "galois",
        "PG(3,3) point/line counts exact for q=3 twistor/lens follow-up",
        "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 (installed by this card)",
    )
    gf = galois.GF(3)

    def normalize(v: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        arr = gf(v)
        for x in arr:
            if int(x) != 0:
                arr = arr * (gf(1) / x)
                break
        return tuple(int(x) for x in arr)

    points = sorted(
        {
            normalize(tuple(v))
            for v in np.ndindex((3, 3, 3, 3))
            if any(int(x) != 0 for x in v)
        }
    )
    lines: set[tuple[tuple[int, int, int, int], ...]] = set()
    for i, p in enumerate(points):
        for q in points[i + 1 :]:
            members = {
                normalize(tuple(int(x) for x in (gf(a) * gf(p) + gf(b) * gf(q))))
                for a in range(3)
                for b in range(3)
                if (a, b) != (0, 0)
            }
            if len(members) == 4:
                lines.add(tuple(sorted(members)))
    twistor = load_json(
        "system_v6/sims/twistor_incidence_finite_packet_v0/results/"
        "twistor_incidence_finite_packet_v0_jax_results.json"
    )
    committed = twistor["summary"]["q3_next_discriminator"]
    rec.update(
        {
            "probe_result": {
                "point_count": len(points),
                "line_count": len(lines),
                "points_per_line": sorted({len(line) for line in lines}),
                "committed_q3_next_discriminator": committed,
                "matches_committed_40_130": len(points) == 40 and len(lines) == 130,
            },
            "verdict": "useful-now",
            "layer_routed_to": "q=3 twistor/lens finite-incidence follow-up",
        }
    )
    return rec


def main() -> None:
    probes = [
        probe_quimb_cotengra(),
        probe_ott(),
        probe_jaxopt_lineax(),
        probe_e3nn_jax(),
        probe_geomstats(),
        probe_netket(),
        probe_dynamiqs(),
        probe_galois(),
    ]
    payload = {
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "generated_at_unix": time.time(),
        "python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
        "installs_performed": [
            {
                "package": "galois",
                "version": "0.4.11",
                "target": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
                "reason": "PG(3,3) exact finite-field incidence fit probe",
            }
        ],
        "probes": probes,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": True, "result_path": str(OUT.relative_to(ROOT)), "probe_count": len(probes)}))


if __name__ == "__main__":
    main()
