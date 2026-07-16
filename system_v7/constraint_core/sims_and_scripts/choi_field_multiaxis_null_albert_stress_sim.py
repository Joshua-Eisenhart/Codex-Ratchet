#!/usr/bin/env python3
"""Choi field multi-axis null plus Albert stress probe.

Scratch diagnostic only.

This imports the useful UP-110 idea from the v77 external bundle without
promoting its language:

- engines-as-objects are represented by their Choi matrices;
- the mirror level is tested as related-but-not-isomorphic, not a strict copy;
- a tiny field graph is compared against random CPTP nulls;
- the existing local Albert/Jordan packing result is attached as a separate
  stress layer, not fused into an exceptional-symmetry claim.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


BUNDLE_ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = Path(__file__).resolve().parent
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = SIM_DIR / "choi_field_multiaxis_null_albert_stress_sim_results.json"
ALBERT_RESULT_PATH = SIM_DIR / "engine_field_choi_jordan_albert_probe_sim_results.json"
GROK_PRESSURE_PATH = SIM_DIR / "grok45_up110_upper_manifold_pressure_20260708.json"
EXTERNAL_ZIP_PATH = BUNDLE_ROOT / "external_inputs" / "77.zip"
EXTERNAL_NOTE_PATH = BUNDLE_ROOT / "external_inputs" / "pasted-text.txt"

SIM_ID = "choi_field_multiaxis_null_albert_stress"
SEED = 110
N_TERRAINS = 8
NULL_SAMPLES = 96
TOL_TP = 1.0e-9
TOL_DISTINCT = 0.1

SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
I2 = np.eye(2, dtype=complex)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)
G = 0.35
KAPPA = 1.0

TERRAINS = {
    0: (+1, "damp", +1),
    1: (+1, "depol", 0),
    2: (+1, "damp", -1),
    3: (+1, "proj", 0),
    4: (-1, "damp", -1),
    5: (-1, "depol", 0),
    6: (-1, "damp", +1),
    7: (-1, "proj", 0),
}

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite channel integration, Choi matrices, correlations, and null ensembles",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON, timestamps, source paths, and scalar bookkeeping",
    },
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "python_stdlib": "supportive"}


def dissipator(op: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return op @ rho @ op.conj().T - 0.5 * (op.conj().T @ op @ rho + rho @ op.conj().T @ op)


def lindblad(terrain_idx: int):
    eps, kind, pole = TERRAINS[terrain_idx]
    hamiltonian = eps * (SX + SY + SZ) / math.sqrt(3.0)

    def flow(rho: np.ndarray) -> np.ndarray:
        out = -1j * G * (hamiltonian @ rho - rho @ hamiltonian)
        if kind == "damp":
            out += KAPPA * dissipator(SP if pole > 0 else SM, rho)
        elif kind == "depol":
            out += 0.5 * KAPPA * (dissipator(SX, rho) + dissipator(SY, rho))
        else:
            out += KAPPA * dissipator(SZ, rho)
        return out

    return flow


def evolve(flow, matrix: np.ndarray, time: float = 1.0, steps: int = 200) -> np.ndarray:
    dt_step = time / steps
    rho = matrix.astype(complex)
    for _ in range(steps):
        k1 = flow(rho)
        k2 = flow(rho + 0.5 * dt_step * k1)
        k3 = flow(rho + 0.5 * dt_step * k2)
        k4 = flow(rho + dt_step * k3)
        rho = rho + (dt_step / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    return rho


def terrain_choi(terrain_idx: int) -> np.ndarray:
    flow = lindblad(terrain_idx)
    out = np.zeros((4, 4), complex)
    for i in range(2):
        for j in range(2):
            basis = np.zeros((2, 2), complex)
            basis[i, j] = 1.0
            out += np.kron(basis, evolve(flow, basis))
    return out


def partial_trace_output(choi: np.ndarray) -> np.ndarray:
    return np.array(
        [
            [choi[0, 0] + choi[1, 1], choi[0, 2] + choi[1, 3]],
            [choi[2, 0] + choi[3, 1], choi[2, 2] + choi[3, 3]],
        ],
        dtype=complex,
    )


def apply_choi(choi: np.ndarray, rho: np.ndarray) -> np.ndarray:
    out = np.zeros((2, 2), complex)
    for i in range(2):
        for j in range(2):
            block = choi[2 * i : 2 * i + 2, 2 * j : 2 * j + 2]
            out += rho[i, j] * block
    return out


def choi_entropy(choi: np.ndarray) -> float:
    normed = choi / max(float(np.trace(choi).real), 1.0e-12)
    eigs = np.linalg.eigvalsh((normed + normed.conj().T) / 2.0).real
    eigs = eigs[eigs > 1.0e-10]
    return float(-(eigs * np.log2(eigs)).sum())


def purity_loss(rho: np.ndarray) -> float:
    return float(1.0 - np.trace(rho @ rho).real)


def avg_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = 0.5 * (start + end - 1)
        start = end
    return ranks


def spearman(values_a: np.ndarray, values_b: np.ndarray) -> float:
    a = avg_ranks(np.asarray(values_a, dtype=float))
    b = avg_ranks(np.asarray(values_b, dtype=float))
    a -= a.mean()
    b -= b.mean()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom < 1.0e-12:
        return 0.0
    return float((a @ b) / denom)


def bloch_state(x: float, y: float, z: float) -> np.ndarray:
    vec = np.array([x, y, z], dtype=float)
    norm = np.linalg.norm(vec)
    if norm > 0.95:
        vec *= 0.95 / norm
    return 0.5 * (I2 + vec[0] * SX + vec[1] * SY + vec[2] * SZ)


def probe_ensemble() -> list[np.ndarray]:
    return [
        bloch_state(0.4, 0.3, 0.5),
        bloch_state(-0.5, 0.2, 0.1),
        bloch_state(0.1, -0.6, 0.2),
        bloch_state(0.0, 0.0, 0.7),
        bloch_state(0.6, 0.0, -0.2),
        bloch_state(-0.2, -0.3, -0.4),
        bloch_state(0.3, -0.4, 0.4),
        bloch_state(-0.4, 0.5, -0.1),
        bloch_state(0.0, 0.7, 0.0),
        bloch_state(0.55, 0.25, -0.25),
        bloch_state(-0.35, -0.15, 0.65),
        bloch_state(0.2, -0.2, -0.6),
    ]


def channel_readouts(chois: list[np.ndarray]) -> dict[str, np.ndarray]:
    ident_choi = np.zeros((4, 4), complex)
    for i in range(2):
        for j in range(2):
            basis = np.zeros((2, 2), complex)
            basis[i, j] = 1.0
            ident_choi += np.kron(basis, basis)

    probes = probe_ensemble()
    base_mixedness = []
    base_drift = []
    base_z_abs = []
    for choi in chois:
        outs = [apply_choi(choi, probe) for probe in probes]
        base_mixedness.append(float(np.mean([purity_loss(out) for out in outs])))
        base_drift.append(float(np.mean([np.linalg.norm(out - probe) for out, probe in zip(outs, probes)])))
        base_z_abs.append(float(np.mean([abs(np.trace(out @ SZ).real) for out in outs])))

    return {
        "base_mixedness_probe_mean": np.asarray(base_mixedness),
        "base_state_drift_probe_mean": np.asarray(base_drift),
        "base_abs_z_probe_mean": np.asarray(base_z_abs),
        "mirror_choi_entropy": np.asarray([choi_entropy(choi) for choi in chois]),
        "mirror_distance_from_identity": np.asarray([np.linalg.norm(choi - ident_choi) for choi in chois]),
        "mirror_unitality_defect": np.asarray([np.linalg.norm(apply_choi(choi, I2) - I2) for choi in chois]),
    }


def distance_matrix(chois: list[np.ndarray]) -> np.ndarray:
    return np.asarray([[np.linalg.norm(a - b) for b in chois] for a in chois], dtype=float)


def random_cptp_channel(rng: np.random.Generator, kraus_count: int = 3) -> list[np.ndarray]:
    raw = []
    for _ in range(kraus_count):
        mat = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
        raw.append(mat / math.sqrt(2.0 * kraus_count))
    gram = sum(mat.conj().T @ mat for mat in raw)
    vals, vecs = np.linalg.eigh(gram)
    invsqrt = vecs @ np.diag(1.0 / np.sqrt(np.maximum(vals, 1.0e-12))) @ vecs.conj().T
    return [mat @ invsqrt for mat in raw]


def choi_from_kraus(kraus: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4, 4), dtype=complex)
    for op in kraus:
        for i in range(2):
            for j in range(2):
                basis = np.zeros((2, 2), complex)
                basis[i, j] = 1.0
                out += np.kron(basis, op @ basis @ op.conj().T)
    return out


def field_stats(chois: list[np.ndarray]) -> dict[str, Any]:
    dist = distance_matrix(chois)
    centrality = dist.sum(axis=1)
    return {
        "choi_distance_centralities": [round(float(x), 6) for x in centrality],
        "centrality_variance": float(np.var(centrality)),
        "min_pair_distance": float(np.min(dist[np.triu_indices(len(chois), 1)])),
        "max_pair_distance": float(np.max(dist)),
        "field_nontrivial": bool(len(set(np.round(centrality, 4))) > 1),
    }


def null_field_stats(rng: np.random.Generator, terrain_variance: float) -> dict[str, Any]:
    variances = []
    min_distances = []
    for _ in range(NULL_SAMPLES):
        chois = [choi_from_kraus(random_cptp_channel(rng)) for _ in range(N_TERRAINS)]
        stats = field_stats(chois)
        variances.append(stats["centrality_variance"])
        min_distances.append(stats["min_pair_distance"])
    variances_np = np.asarray(variances)
    return {
        "samples": NULL_SAMPLES,
        "random_cptp_centrality_variance_mean": float(np.mean(variances_np)),
        "random_cptp_centrality_variance_q05": float(np.quantile(variances_np, 0.05)),
        "random_cptp_centrality_variance_q95": float(np.quantile(variances_np, 0.95)),
        "terrain_variance_percentile_vs_random_cptp": float(np.mean(variances_np <= terrain_variance)),
        "random_cptp_min_pair_distance_mean": float(np.mean(min_distances)),
        "null_interpretation": "If percentile is ordinary, the 8-terrain field nonuniformity is object validity only, not geometry admission.",
    }


def load_json_if_present(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_if_present(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    chois = [terrain_choi(idx) for idx in range(N_TERRAINS)]
    tp_defects = [float(np.linalg.norm(partial_trace_output(choi) - I2)) for choi in chois]
    min_eigs = [float(np.min(np.linalg.eigvalsh((choi + choi.conj().T) / 2.0).real)) for choi in chois]
    distances = distance_matrix(chois)
    min_distance = float(np.min(distances[np.triu_indices(N_TERRAINS, 1)]))
    mirror_object_ok = bool(max(tp_defects) < TOL_TP and min(min_eigs) > -1.0e-9 and min_distance > TOL_DISTINCT)

    readouts = channel_readouts(chois)
    correlation_pairs = {
        "mixedness_vs_choi_entropy": (
            "base_mixedness_probe_mean",
            "mirror_choi_entropy",
        ),
        "state_drift_vs_identity_distance": (
            "base_state_drift_probe_mean",
            "mirror_distance_from_identity",
        ),
        "abs_z_vs_unitality_defect": (
            "base_abs_z_probe_mean",
            "mirror_unitality_defect",
        ),
    }
    correlations = {
        name: {
            "base_readout": left,
            "mirror_readout": right,
            "spearman_rho_tie_aware": spearman(readouts[left], readouts[right]),
            "strictly_isomorphic": bool(abs(spearman(readouts[left], readouts[right]) - 1.0) < 1.0e-9),
        }
        for name, (left, right) in correlation_pairs.items()
    }
    related_not_iso_pairs = [
        name
        for name, row in correlations.items()
        if 0.25 < abs(float(row["spearman_rho_tie_aware"])) < 1.0 - 1.0e-9
    ]

    terrain_field = field_stats(chois)
    nulls = null_field_stats(rng, terrain_field["centrality_variance"])
    albert = load_json_if_present(ALBERT_RESULT_PATH)
    grok = load_json_if_present(GROK_PRESSURE_PATH)

    pass_conditions = {
        "choi_objects_are_cp_tp_and_distinct": mirror_object_ok,
        "multi_readout_related_not_strict_iso_has_at_least_two_pairs": len(related_not_iso_pairs) >= 2,
        "field_graph_nontrivial": terrain_field["field_nontrivial"],
        "random_cptp_nulls_were_computed": nulls["samples"] == NULL_SAMPLES,
        "albert_stress_result_present_and_passed": bool(albert and albert.get("all_pass") is True),
        "albert_result_remains_scratch_only": bool(albert and albert.get("promotion_allowed") is False),
    }

    return {
        "schema": "codex_ratchet.choi_field_multiaxis_null_albert_stress.v1",
        "sim_id": SIM_ID,
        "name": "Choi field multi-axis null plus Albert stress probe",
        "created_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_if_present(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "external_seed_paths": [
            str(EXTERNAL_ZIP_PATH),
            str(EXTERNAL_NOTE_PATH),
        ],
        "external_seed_sha256": {
            str(EXTERNAL_ZIP_PATH): sha256_if_present(EXTERNAL_ZIP_PATH),
            str(EXTERNAL_NOTE_PATH): sha256_if_present(EXTERNAL_NOTE_PATH),
        },
        "local_dependency_paths": [
            str(ALBERT_RESULT_PATH),
            str(GROK_PRESSURE_PATH),
        ],
        "local_dependency_sha256": {
            str(ALBERT_RESULT_PATH): sha256_if_present(ALBERT_RESULT_PATH),
            str(GROK_PRESSURE_PATH): sha256_if_present(GROK_PRESSURE_PATH),
        },
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_execution_kind": "classical",
        "sim_class": "engine_object_field_probe",
        "purpose": "Retest UP-110 as finite Choi engine-objects, weaken strict mirror-isomorphism to measured related-not-iso, add nulls, and attach local Albert/Jordan packing as a separate stress layer.",
        "root_constraints_in_force": [
            "F01 finite 8-terrain channel set, finite probe ensemble, finite random CPTP null ensemble",
            "N01 order-sensitive channel composition/readout context; noncommutative matrices; Albert stress delegated to the local octonion/Jordan probe",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "terrain_labels": {str(k): {"epsilon": v[0], "kind": v[1], "pole": v[2]} for k, v in TERRAINS.items()},
        "choi_object_checks": {
            "base_real_dim": 4,
            "choi_real_dim": 16,
            "max_tp_defect": max(tp_defects),
            "min_choi_eigenvalue": min(min_eigs),
            "choi_terrain_min_distance": min_distance,
            "mirror_object_ok": mirror_object_ok,
        },
        "readout_values": {name: [round(float(x), 6) for x in values] for name, values in readouts.items()},
        "base_mirror_correlation_matrix": correlations,
        "related_not_strictly_isomorphic_pairs": related_not_iso_pairs,
        "doc_correction": "The measured mirror level is related but not strictly isomorphic. This file does not admit A_i -> A_{i+6} as an exact map.",
        "field_graph": terrain_field,
        "random_cptp_nulls": nulls,
        "albert_stress_dependency": {
            "present": albert is not None,
            "verdict": None if albert is None else albert.get("verdict"),
            "all_pass": None if albert is None else albert.get("all_pass"),
            "claim_ceiling": None if albert is None else albert.get("claim_ceiling"),
            "blocked_downstream_consumers": None if albert is None else albert.get("blocked_downstream_consumers"),
        },
        "grok45_pressure_dependency": {
            "present": grok is not None,
            "verdict": None if grok is None else grok.get("response", {}).get("verdict", grok.get("verdict")),
            "required_controls_count": 0
            if grok is None
            else len(grok.get("response", {}).get("required_controls", grok.get("required_controls", []))),
        },
        "pass_conditions": pass_conditions,
        "verdict": "scratch_field_seed_survives_with_low_ceiling" if all(pass_conditions.values()) else "scratch_field_seed_failed_or_incomplete",
        "eligible_consumers": [],
        "blocked_consumers": [
            "axes 7-12 runtime admission",
            "strict A_i to A_i+6 isomorphism claim",
            "IGT game admission",
            "exceptional algebra symmetry action claim",
            "natural/canonical Choi-to-octonion or Choi-to-Albert map claim",
            "Axis0, bridge, manifold, physics, or geometry admission",
        ],
        "blocked_downstream_consumers": [
            "axes 7-12 runtime admission",
            "strict A_i to A_i+6 isomorphism claim",
            "IGT game admission",
            "exceptional algebra symmetry action claim",
            "natural/canonical Choi-to-octonion or Choi-to-Albert map claim",
            "Axis0, bridge, manifold, physics, or geometry admission",
        ],
        "divergence_log": [
            {
                "surface": "strict_mirror_isomorphism",
                "observed": "multiple readout correlations are not exact order-isomorphisms",
                "meaning": "mirror Choi layer is a distinct object/readout level, not a copy of the base state axis",
            },
            {
                "surface": "field_geometry",
                "observed": "centrality nonuniformity is compared to random CPTP nulls but not promoted",
                "meaning": "a field graph exists; intrinsic geometry still requires stronger null-surviving structure",
            },
            {
                "surface": "Albert/Jordan packing",
                "observed": "attached as existing local stress result only",
                "meaning": "passing H2/H3 and failing H4 does not make the Choi map natural or exceptional symmetry active",
            },
        ],
        "claim_ceiling": "Scratch diagnostic: finite Choi engine-objects are valid and multi-readout mirror measures are related-not-strictly-isomorphic; field nulls and local Albert/Jordan stress are attached as controls. No axes 7-12 admission, IGT admission, E-series action, natural map, Axis0, bridge, manifold, physics, or geometry claim.",
        "all_pass": all(pass_conditions.values()),
    }


def json_default(value: Any) -> Any:
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def print_summary(result: dict[str, Any]) -> None:
    checks = result["choi_object_checks"]
    print("CHOI_FIELD_MULTIAXIS_NULL_ALBERT_STRESS")
    print(f"seed={SEED} classification={result['classification']} promotion_allowed={result['promotion_allowed']}")
    print(
        "choi_objects "
        f"tp={checks['max_tp_defect']:.3e} min_eig={checks['min_choi_eigenvalue']:.3e} "
        f"min_dist={checks['choi_terrain_min_distance']:.6f} ok={checks['mirror_object_ok']}"
    )
    for name, row in result["base_mirror_correlation_matrix"].items():
        print(f"corr {name}: rho={row['spearman_rho_tie_aware']:+.3f} strict_iso={row['strictly_isomorphic']}")
    field = result["field_graph"]
    nulls = result["random_cptp_nulls"]
    print(
        "field "
        f"var={field['centrality_variance']:.6f} null_percentile={nulls['terrain_variance_percentile_vs_random_cptp']:.3f} "
        f"nontrivial={field['field_nontrivial']}"
    )
    albert = result["albert_stress_dependency"]
    print(f"albert_dependency present={albert['present']} verdict={albert['verdict']} all_pass={albert['all_pass']}")
    print(f"verdict={result['verdict']} all_pass={result['all_pass']}")
    print(f"wrote: {RESULT_PATH}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, default=json_default) + "\n", encoding="utf-8")
    print_summary(result)
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
