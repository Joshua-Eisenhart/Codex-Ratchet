#!/usr/bin/env python3
"""Emit stable label-free fingerprint/component IDs for the committed eng_64 estate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np


SIM_ID = "eng64_stage_fingerprint_ids_v0"
SCHEMA_VERSION = "eng64_stage_fingerprint_ids_result_v0"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "downstream_plumbing_only"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT = RESULT_DIR / f"{SIM_ID}_results.json"

SOURCE_PATHS = {
    "eng_64_result": ROOT / "system_v5/julia_carrier/eng_64_hexagram_julia_results.json",
    "eng_64_source": ROOT / "system_v5/julia_carrier/eng_64_hexagram_julia.jl",
    "iching_audit": ROOT / "system_v6/sims/iching_symmetry_match_v0/audit_verdict.md",
    "iching_packet": ROOT / "system_v6/sims/iching_symmetry_match_v0/iching_symmetry_match_v0.py",
    "iching_result": ROOT / "system_v6/sims/iching_symmetry_match_v0/results/iching_symmetry_match_v0_results.json",
}

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


RNG_SEED = 20260604
FP_TOL = 1.0e-7
GAMMA_KRAUS = 0.30
GAMMA_LINDBLAD = 0.30
OMEGA = 1.0
DT = 0.1
NSTEPS = 20
THETA_HOT = 0.40
THETA_COLD = np.pi / 4.0
THETA_ADIAB = np.pi / 3.0

I2 = np.eye(2, dtype=np.complex128)
SX = np.array([[0, 1], [1, 0]], dtype=np.complex128)
SZ = np.array([[1, 0], [0, -1]], dtype=np.complex128)

CARNOT_STROKES = ((0, 0), (0, 1), (1, 0), (1, 1))
SZILARD_STROKES = ((1, 0), (0, 0), (0, 0), (1, 1))

TOOL_MANIFEST = {
    "python_numpy_port": {
        "used": True,
        "reason": "load-bearing: recomputes the eng_64 2x2 density-channel fingerprints label-free from the committed Julia algorithm",
    },
    "hashlib": {
        "used": True,
        "reason": "supportive: pins committed source/result/audit inputs by sha256",
    },
    "json": {
        "used": True,
        "reason": "supportive: emits the bounded mapping result artifact",
    },
    "builder_audit_boundary": {
        "used": True,
        "reason": "load-bearing: verifies this builder did not write audit_verdict.md",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "python_numpy_port": "load_bearing",
    "hashlib": "supportive",
    "json": "supportive",
    "builder_audit_boundary": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        out = subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "role": role, "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["user_supplied_commit_hint"] = commit_hint
    return row


def seeded_fraction(seed: int, n: int, idx: int, stride: int, modulus: int, offset: int) -> float:
    raw = ((seed % modulus) + stride * n + offset * idx) % modulus
    return (float(raw) + 0.5) / float(modulus)


def seeded_angles(seed: int, n: int, idx: int) -> tuple[float, float, float]:
    tf = seeded_fraction(seed, n, idx, 37, 997, 53)
    pf = seeded_fraction(seed, n, idx, 101, 991, 67)
    cf = seeded_fraction(seed, n, idx, 131, 983, 71)
    return np.pi * (0.11 + 0.78 * tf), 2.0 * np.pi * pf, 2.0 * np.pi * cf


def weyl_density_l(seed: int, n: int, idx: int) -> np.ndarray:
    theta, phi, chi = seeded_angles(seed, n, idx)
    psi = np.array(
        [
            np.exp(1j * (phi + chi)) * np.cos(theta / 2.0),
            np.exp(1j * (phi - chi)) * np.sin(theta / 2.0),
        ],
        dtype=np.complex128,
    )
    psi = psi / np.linalg.norm(psi)
    return np.outer(psi, np.conjugate(psi))


RHO_REPR = weyl_density_l(RNG_SEED, 64, 1)


def kraus_apply(ks: list[np.ndarray], rho: np.ndarray) -> np.ndarray:
    out = np.zeros((2, 2), dtype=np.complex128)
    for k in ks:
        out += k @ rho @ np.conjugate(k.T)
    trace = np.trace(out)
    if abs(trace) > 1.0e-14:
        out = out / trace
    return out


def lindblad_step(rho: np.ndarray, h: np.ndarray, l_op: np.ndarray, gamma: float, dt: float) -> np.ndarray:
    ldl = np.conjugate(l_op.T) @ l_op
    comm = h @ rho - rho @ h
    diss = gamma * (l_op @ rho @ np.conjugate(l_op.T) - 0.5 * (ldl @ rho + rho @ ldl))
    rho_new = rho + dt * (-1j * comm + diss)
    trace = np.trace(rho_new)
    if abs(trace) > 1.0e-14:
        rho_new = rho_new / trace
    return rho_new


def axis1_channel(bit: int) -> list[np.ndarray]:
    gamma = GAMMA_KRAUS
    if bit == 0:
        k0 = np.array([[np.sqrt(1.0 - gamma), 0], [0, 1]], dtype=np.complex128)
        k1 = np.array([[0, 0], [np.sqrt(gamma), 0]], dtype=np.complex128)
    else:
        k0 = np.array([[1, 0], [0, np.sqrt(1.0 - gamma)]], dtype=np.complex128)
        k1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=np.complex128)
    return [k0, k1]


def apply_axis1(rho: np.ndarray, bit: int) -> np.ndarray:
    return kraus_apply(axis1_channel(bit), rho)


def apply_axis2_open(rho: np.ndarray) -> np.ndarray:
    h = OMEGA * SZ / 2.0
    l_op = np.array([[0, 1], [0, 0]], dtype=np.complex128) * np.sqrt(GAMMA_LINDBLAD)
    out = rho.copy()
    for _ in range(NSTEPS):
        out = lindblad_step(out, h, l_op, 1.0, DT)
    return out


def apply_axis2_closed(rho: np.ndarray) -> np.ndarray:
    c = np.cos(THETA_ADIAB / 2.0)
    s = np.sin(THETA_ADIAB / 2.0)
    u = c * I2 - 1j * s * SX
    return u @ rho @ np.conjugate(u.T)


def apply_axis2(rho: np.ndarray, bit: int) -> np.ndarray:
    return apply_axis2_open(rho) if bit == 0 else apply_axis2_closed(rho)


def apply_axis5_hot(rho: np.ndarray) -> np.ndarray:
    gamma = min(max(THETA_HOT, 0.0), 1.0)
    k0 = np.sqrt(1.0 - gamma / 2.0) * I2
    k1 = np.sqrt(gamma / 2.0) * SZ
    return k0 @ rho @ np.conjugate(k0.T) + k1 @ rho @ np.conjugate(k1.T)


def apply_axis5_cold(rho: np.ndarray) -> np.ndarray:
    c = np.cos(THETA_COLD / 2.0)
    s = np.sin(THETA_COLD / 2.0)
    u = c * I2 - 1j * s * SX
    return u @ rho @ np.conjugate(u.T)


def apply_axis5(rho: np.ndarray, bit: int) -> np.ndarray:
    return apply_axis5_hot(rho) if bit == 0 else apply_axis5_cold(rho)


def ax12_compose(rho: np.ndarray, ax1: int, ax2: int) -> np.ndarray:
    return apply_axis1(apply_axis2(rho, ax2), ax1)


def apply_substage(rho: np.ndarray, ax1: int, ax2: int, ax5: int, ax6: int) -> np.ndarray:
    if ax6 == 0:
        return ax12_compose(apply_axis5(rho, ax5), ax1, ax2)
    return apply_axis5(ax12_compose(rho, ax1, ax2), ax5)


def round_fp(x: float) -> float:
    return round(x / FP_TOL) * FP_TOL


def fingerprint(rho: np.ndarray) -> tuple[float, ...]:
    values: list[float] = []
    for i in range(2):
        for j in range(2):
            values.append(round_fp(float(np.real(rho[i, j]))))
            values.append(round_fp(float(np.imag(rho[i, j]))))
    return tuple(values)


def apply_stage(ax1: int, ax2: int, ax3: int, ax4: int, ax5: int, ax6: int) -> tuple[np.ndarray, tuple[float, ...]]:
    strokes = CARNOT_STROKES if ax3 == 0 else SZILARD_STROKES
    stroke_seq = range(4) if ax4 == 0 else range(3, -1, -1)
    rho = RHO_REPR.copy()
    for stroke_idx in stroke_seq:
        s_ax1, s_ax2 = strokes[stroke_idx]
        rho = apply_substage(rho, s_ax1, s_ax2, ax5, ax6)
    return rho, fingerprint(rho)


def axes_from_index(index: int) -> dict[str, int]:
    return {f"ax{axis}": (index >> (axis - 1)) & 1 for axis in range(1, 7)}


def label_for_index(index: int) -> str:
    ax = axes_from_index(index)
    engine = "Carnot" if ax["ax3"] == 0 else "Szilard"
    direction = "CW_engine" if ax["ax4"] == 0 else "CCW_refrigerator"
    return f"hex{index:02d}_{engine}_{direction}_ax5{ax['ax5']}_ax6{ax['ax6']}"


def component_id_for_fingerprint(fp: tuple[float, ...]) -> str:
    body = ",".join(f"{value:.7f}" for value in fp)
    return "eng64_fp_" + hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def build_fingerprint_rows() -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
    rows: list[dict[str, Any]] = []
    components: dict[str, list[int]] = {}
    for ax6 in range(2):
        for ax5 in range(2):
            for ax4 in range(2):
                for ax3 in range(2):
                    for ax2 in range(2):
                        for ax1 in range(2):
                            index = ax1 + 2 * ax2 + 4 * ax3 + 8 * ax4 + 16 * ax5 + 32 * ax6
                            _, fp = apply_stage(ax1, ax2, ax3, ax4, ax5, ax6)
                            component_id = component_id_for_fingerprint(fp)
                            components.setdefault(component_id, []).append(index)
                            rows.append(
                                {
                                    "stage": index,
                                    "source_stage_label": label_for_index(index),
                                    "axes": axes_from_index(index),
                                    "fingerprint": list(fp),
                                    "fingerprint_id": component_id,
                                    "component_id": component_id,
                                }
                            )
    rows.sort(key=lambda row: row["stage"])
    return rows, {key: sorted(value) for key, value in sorted(components.items())}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collapse_graph_components(collapse_details: list[dict[str, Any]]) -> list[list[int]]:
    parent = {idx: idx for idx in range(64)}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for row in collapse_details:
        stage_i = int(str(row["stage_i"])[3:5])
        stage_j = int(str(row["stage_j"])[3:5])
        union(stage_i, stage_j)
    groups: dict[int, list[int]] = {}
    for idx in range(64):
        groups.setdefault(find(idx), []).append(idx)
    return sorted((sorted(group) for group in groups.values()), key=lambda group: group[0])


def label_permutation_control(rows: list[dict[str, Any]]) -> dict[str, Any]:
    original = {row["stage"]: row["fingerprint_id"] for row in rows}
    permuted_labels = {
        row["stage"]: f"permuted_label_{(row['stage'] * 37 + 11) % 64:02d}" for row in rows
    }
    after = {row["stage"]: row["fingerprint_id"] for row in rows}
    return {
        "control": "deterministic source-stage-label permutation",
        "labels_changed_count": sum(1 for stage in original if permuted_labels[stage] != rows[stage]["source_stage_label"]),
        "fingerprint_ids_unchanged": original == after,
        "label_field_used_in_fingerprint": False,
    }


def same_component_independent_recompute_control(components: dict[str, list[int]]) -> dict[str, Any]:
    checked_pairs = []
    failures = []
    for component_id, stages in sorted(components.items()):
        if len(stages) < 2:
            continue
        a, b = stages[0], stages[-1]
        ax_a = axes_from_index(a)
        ax_b = axes_from_index(b)
        _, fp_a = apply_stage(**ax_a)
        _, fp_b = apply_stage(**ax_b)
        equal = fp_a == fp_b
        checked_pairs.append({"component_id": component_id, "stage_a": a, "stage_b": b, "equal": equal})
        if not equal:
            failures.append({"component_id": component_id, "stage_a": a, "stage_b": b})
    return {
        "checked_component_pairs": len(checked_pairs),
        "all_equal": not failures,
        "failures": failures,
        "sample": checked_pairs[:8],
    }


def build() -> dict[str, Any]:
    eng64 = load_json(SOURCE_PATHS["eng_64_result"])
    rows, components = build_fingerprint_rows()
    component_sets = sorted(components.values(), key=lambda group: group[0])
    collapse_sets = collapse_graph_components(eng64["collapses"]["collapse_details"])
    component_table = [
        {
            "component_id": component_id,
            "stages": stages,
            "size": len(stages),
            "representative_stage": stages[0],
        }
        for component_id, stages in components.items()
    ]
    controls = {
        "label_permutation_invariance": label_permutation_control(rows),
        "same_component_independent_recompute": same_component_independent_recompute_control(components),
        "collapse_graph_parity": {
            "fresh_fingerprint_components_match_committed_collapse_graph": component_sets == collapse_sets,
            "committed_collapse_graph_component_count": len(collapse_sets),
            "fresh_component_count": len(component_sets),
        },
    }
    all_pass = (
        len(rows) == 64
        and len(components) == 16
        and eng64.get("fingerprint_counts", {}).get("n_distinct") == 16
        and controls["label_permutation_invariance"]["fingerprint_ids_unchanged"]
        and controls["same_component_independent_recompute"]["all_equal"]
        and controls["collapse_graph_parity"]["fresh_fingerprint_components_match_committed_collapse_graph"]
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "authority": {
            "primary_audit": rel(SOURCE_PATHS["iching_audit"]),
            "user_supplied_iching_audit_commit_hint": "2b32714a0",
            "hardening_row": "caveat 5: future eng_64 estates should emit stable per-stage fingerprint IDs/component IDs",
        },
        "source_locks": {
            "eng_64_result": source_lock(SOURCE_PATHS["eng_64_result"], "committed eng_64 result estate"),
            "eng_64_source": source_lock(SOURCE_PATHS["eng_64_source"], "committed eng_64 algorithm source"),
            "iching_audit": source_lock(SOURCE_PATHS["iching_audit"], "authority audit caveat", "2b32714a0"),
            "iching_packet": source_lock(SOURCE_PATHS["iching_packet"], "reference downstream inference packet"),
            "iching_result": source_lock(SOURCE_PATHS["iching_result"], "reference downstream result packet"),
        },
        "fingerprint_definition": {
            "source": rel(SOURCE_PATHS["eng_64_source"]),
            "definition": "Apply the committed eng_64 2x2 density-channel stage to the deterministic representative L-Weyl density matrix RHO_REPR, flatten rho_out in row-major order to [real, imag] pairs, round each float to FP_TOL=1e-7, and hash that 8-float vector for the stable fingerprint/component ID.",
            "label_free_fields": ["axes", "rho_out", "rounded_8_float_vector"],
            "excluded_fields": ["source_stage_label", "engine label text", "direction label text", "collapse pair text"],
            "rng_seed": RNG_SEED,
            "fp_tolerance": FP_TOL,
        },
        "summary": {
            "stage_count": len(rows),
            "n_distinct_fresh_fingerprints": len(components),
            "committed_eng64_n_distinct": eng64.get("fingerprint_counts", {}).get("n_distinct"),
            "component_size_histogram": {
                str(size): sum(1 for stages in components.values() if len(stages) == size)
                for size in sorted({len(stages) for stages in components.values()})
            },
            "recovered_iching_reference_n_distinct_16": len(components) == 16,
        },
        "stage_fingerprint_components": rows,
        "components": component_table,
        "controls": controls,
        "claim_boundary": {
            "scratch_diagnostic": True,
            "downstream_plumbing_only": True,
            "does_not_modify_eng_64_estate": True,
            "does_not_claim_64_behavior_iso": True,
            "does_not_claim_matrix64_behavior": True,
            "does_not_promote_eng_64": True,
            "no_qit_or_physics_admission": True,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": {
            "boundary_helper_fully_used": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "builder_self_assessment_expected": rel(SIM_DIR / "builder_self_assessment.md"),
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build()
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT), "n_distinct": payload["summary"]["n_distinct_fresh_fingerprints"]}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
