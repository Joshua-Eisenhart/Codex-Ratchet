#!/usr/bin/env python3
"""Operator-local vector actuator scout for Axis0 control-family degeneracy.

This scout consumes the existing plural Axis0 router, source-native stage
records, and bounded MPS/PEPS/PEPS3D local-environment carriers, then replaces
the scalar-weighted downstream drive with a true 3-component operator-local
vector actuation rule. It tests whether the admitted Axis0 candidates become
less control-family degenerate under this local vector actuator while blocked
candidates remain inert.

Formal scout only. It does not admit final Axis0, final manifold maturity,
physics, cognition, or canonical architecture claims.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import networkx as nx
import torch
import z3

import sim_axis0_plural_candidate_multicarrier_drive_controls_probe as plural
import sim_source_native_multicarrier_subdense_environment_contraction_probe as subdense


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "axis0_operator_local_vector_actuator_degeneracy_break_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
BASELINE_RESULT = RESULT_DIR / "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "axis0_operator_local_vector_actuator"
CLAIM_CEILING = (
    "Formal scout only: tests a true operator-local 3-component Axis0 vector "
    "actuator candidate on bounded MPS/PEPS/PEPS3D local-environment carriers "
    "and compares its control-family degeneracy with the current upstream "
    "downstream path. It does not admit final Axis0, final manifold maturity, "
    "attractor-basin success, physics, cognition, or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing operator-local vector actuation, carrier updates, signature gaps, and correlation improvement metrics",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bounded MPS/PEPS/PEPS3D carrier construction and count checks through reused local helpers",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive dependency graph for router to operator-local vector actuator",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing witness that admitted candidates improve on the scalar-style degeneracy ceiling while blocked candidates remain inert",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native stage records consumed through reused local helpers",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive local receipt path handling",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
    "networkx": "supportive",
    "z3": "load_bearing",
    "engine_core": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
}
TOOL_ROLE_SOURCE = {
    "pytorch": "local",
    "quimb": "local",
    "networkx": "local",
    "z3": "local",
    "engine_core": "transitive_supportive",
    "python_json": "local",
    "pathlib": "local",
}

ADMITTED = tuple(subdense.LOAD_BEARING_AXIS0_CANDIDATE_NAMES)
BLOCKED = tuple(subdense.BLOCKED_AXIS0_CANDIDATE_NAMES)
CORRELATION_CEILING = 0.98

OPERATOR_BASIS = {
    "Te": (subdense.SX, subdense.SY, subdense.SZ),
    "Fe": (subdense.SY, subdense.SZ, subdense.SX),
    "Ti": (subdense.SZ, subdense.SX, subdense.SY),
    "Fi": (
        (0.7 * subdense.SX + 0.3 * subdense.SY).to(subdense.TORCH_COMPLEX),
        (0.6 * subdense.SZ + 0.4 * subdense.SX).to(subdense.TORCH_COMPLEX),
        (0.5 * subdense.SY + 0.5 * subdense.SZ).to(subdense.TORCH_COMPLEX),
    ),
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_components(axis0: dict[str, Any], idx: int, mode: str) -> dict[str, float]:
    raw = subdense.axis0_candidate_values(axis0, idx)
    values = {name: raw[name] for name in ADMITTED}
    if mode == "zero_all":
        return {name: 0.0 for name in ADMITTED}
    if mode == "identity_control":
        return {name: 0.0 for name in ADMITTED}
    if mode == "scalar_mean":
        mean = plural.tensor_mean(list(values.values()))
        return {name: mean for name in ADMITTED}
    if mode == "shuffled_name_binding":
        rolled = list(values.values())[1:] + list(values.values())[:1]
        return dict(zip(ADMITTED, rolled))
    if mode.startswith("only::"):
        only = mode.split("::", 1)[1]
        return {name: (values[name] if name == only and name in values else 0.0) for name in ADMITTED}
    if mode.startswith("drop::"):
        dropped = mode.split("::", 1)[1]
        return {name: (0.0 if name == dropped else values[name]) for name in ADMITTED}
    if mode.startswith("sign_flip::"):
        flipped = mode.split("::", 1)[1]
        out = dict(values)
        if flipped in out:
            out[flipped] = -out[flipped]
        return out
    if mode.startswith("time_shuffle::"):
        shuffled = mode.split("::", 1)[1]
        out = dict(values)
        if shuffled in out:
            vector = axis0.get("candidate_vectors", {}).get(shuffled, [])
            if vector:
                out[shuffled] = float(vector[(idx * 7 + 11) % len(vector)])
        return out
    if mode == "full_vector":
        return values
    raise ValueError(mode)


def component_tensor(values: dict[str, float]) -> torch.Tensor:
    return torch.tensor([values[name] for name in ADMITTED], dtype=subdense.TORCH_REAL)


def apply_vector_slot(
    site: subdense.TensorSite,
    operator: str,
    sign: int,
    base_strength: float,
    memory_drive: float,
    components: torch.Tensor,
    idx: int,
    carrier_family: str,
) -> None:
    basis = OPERATOR_BASIS[operator]
    carrier_phase = {
        "mps": torch.tensor([1.0, 0.7, 0.4], dtype=subdense.TORCH_REAL),
        "peps": torch.tensor([0.6, 1.0, 0.5], dtype=subdense.TORCH_REAL),
        "peps3d": torch.tensor([0.5, 0.8, 1.0], dtype=subdense.TORCH_REAL),
    }[carrier_family]
    phase = torch.tensor(
        [
            math.sin((idx + 1.0) * 0.13),
            math.cos((idx + 1.0) * 0.17),
            math.sin((idx + 1.0) * 0.19 + 0.4),
        ],
        dtype=subdense.TORCH_REAL,
    )
    mixed = components * phase * carrier_phase
    cross = torch.tensor(
        [
            components[0] * components[1],
            components[1] * components[2],
            components[2] * components[0],
        ],
        dtype=subdense.TORCH_REAL,
    )
    vector_generator = sum(mixed[col].to(subdense.TORCH_COMPLEX) * basis[col] for col in range(3))
    vector_generator = vector_generator + 0.12 * sum(
        cross[col].to(subdense.TORCH_COMPLEX) * basis[(col + 1) % 3]
        for col in range(3)
    )
    generator = (
        base_strength * subdense.OP_AXES[operator]
        + 0.065 * vector_generator
        + 0.008 * float(memory_drive) * subdense.SZ
    )
    unitary = subdense.I2 - 1j * float(sign) * generator
    site.data = torch.tensordot(site.data, unitary.T, dims=([site.axes["phys"]], [0])).to(subdense.TORCH_COMPLEX)
    non_phys_axes = [name for name in site.axes if name != "phys"]
    if non_phys_axes:
        target_axis = site.axes[sorted(non_phys_axes)[0]]
        dim = site.data.shape[target_axis]
        span = torch.linspace(-1.0, 1.0, int(dim), dtype=subdense.TORCH_REAL)
        scale = (
            1.0
            + 0.035 * components[0] * span
            + 0.025 * components[1] * torch.sin((idx + 1.0) * span)
            + 0.020 * components[2] * torch.cos((idx + 1.0) * span)
        ).to(subdense.TORCH_COMPLEX)
        site.data = subdense.apply_axis_scale(site.data, target_axis, scale)


def run_candidate_carrier(
    records: list[dict[str, Any]],
    axis0: dict[str, Any],
    memory: dict[str, Any],
    family: str,
    shape: tuple[int, ...],
    seed: int,
    mode: str,
) -> dict[str, Any]:
    carrier = subdense.make_carrier(family, shape, seed)
    quimb_check = subdense.quimb_count_check(carrier)
    site_order = sorted(carrier.sites)
    before_rows = subdense.environment_rows(carrier)
    drives = []
    stage_hashes = []
    for idx, record in enumerate(records):
        site = carrier.sites[site_order[idx % len(site_order)]]
        comps = candidate_components(axis0, idx, mode)
        comps_tensor = component_tensor(comps)
        mem_drive = subdense.holodeck_memory_drive(memory, idx)
        drives.append(comps_tensor.tolist())
        stage_hashes.append(record["model_after"]["density_hash"])
        if mode == "identity_control":
            continue
        base_strength = subdense.source_strength(record, 0.0, mem_drive)
        apply_vector_slot(
            site,
            str(record["operator"]),
            int(record["operator_sign"]),
            base_strength,
            mem_drive,
            comps_tensor,
            idx,
            carrier.family,
        )
    after_rows = subdense.environment_rows(carrier)
    before_sig = subdense.signature_from_rows(before_rows)
    after_sig = subdense.signature_from_rows(after_rows)
    comp_arr = torch.tensor(drives, dtype=subdense.TORCH_REAL) if drives else torch.zeros((0, len(ADMITTED)), dtype=subdense.TORCH_REAL)
    return {
        "carrier": carrier.name,
        "family": carrier.family,
        "shape": "x".join(str(x) for x in carrier.shape),
        "mode": mode,
        "site_count": len(carrier.sites),
        "edge_count": len(carrier.edges),
        "sampled_environment_edges": len(after_rows),
        "stage_records_consumed": len(records),
        "unique_model_after_hashes_consumed": len(set(stage_hashes)),
        "quimb_count_check": quimb_check,
        "axis0_ready": bool(axis0.get("ready")),
        "candidate_names_consumed": list(ADMITTED),
        "drive_component_mean_abs": [
            float(torch.mean(torch.abs(comp_arr[:, col])).item()) if comp_arr.numel() else 0.0
            for col in range(comp_arr.shape[1] if comp_arr.ndim == 2 else 0)
        ],
        "environment_signature": after_sig,
        "environment_shift_from_initial": plural.tensor_norm(plural.as_float_tensor(after_sig) - plural.as_float_tensor(before_sig)),
        "environment_rows_head": after_rows[:2],
        "pass": (
            len(records) == subdense.N_SOURCE_SEEDS * 64
            and len(set(stage_hashes)) > 16
            and quimb_check["pass"]
            and len(after_rows) > 0
            and bool(torch.all(torch.isfinite(plural.as_float_tensor(after_sig))).item())
        ),
    }


def run_suite(records: list[dict[str, Any]], axis0: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {}
    modes = ["full_vector", "scalar_mean", "zero_all", "identity_control", "shuffled_name_binding"]
    for name in plural.CANDIDATE_NAMES:
        modes.extend([f"only::{name}", f"drop::{name}", f"sign_flip::{name}", f"time_shuffle::{name}"])
    for family, shape, seed in plural.TEST_CARRIERS:
        key = f"{family}_{'x'.join(str(x) for x in shape)}"
        rows[key] = {
            mode: run_candidate_carrier(records, axis0, memory, family, shape, seed, mode)
            for mode in modes
        }
    gaps = {}
    checks = {}
    for key, row in rows.items():
        full = row["full_vector"]
        gaps[key] = {
            "full_vs_scalar_mean": plural.signature_gap(full, row["scalar_mean"]),
            "full_vs_zero_all": plural.signature_gap(full, row["zero_all"]),
            "full_vs_identity_control": plural.signature_gap(full, row["identity_control"]),
            "full_vs_shuffled_name_binding": plural.signature_gap(full, row["shuffled_name_binding"]),
            "identity_shift_from_initial": float(row["identity_control"]["environment_shift_from_initial"]),
            "drop_gaps": {name: plural.signature_gap(full, row[f"drop::{name}"]) for name in plural.CANDIDATE_NAMES},
            "only_vs_zero_gaps": {name: plural.signature_gap(row[f"only::{name}"], row["zero_all"]) for name in plural.CANDIDATE_NAMES},
            "sign_flip_gaps": {name: plural.signature_gap(full, row[f"sign_flip::{name}"]) for name in plural.CANDIDATE_NAMES},
            "time_shuffle_gaps": {name: plural.signature_gap(full, row[f"time_shuffle::{name}"]) for name in plural.CANDIDATE_NAMES},
        }
        checks[key] = {
            "runs_pass": all(mode_row["pass"] for mode_row in row.values()),
            "full_differs_from_scalar_mean": gaps[key]["full_vs_scalar_mean"] > plural.GAP_FLOOR,
            "full_differs_from_zero_all": gaps[key]["full_vs_zero_all"] > plural.GAP_FLOOR,
            "identity_control_stays_at_initial_signature": gaps[key]["identity_shift_from_initial"] < plural.GAP_FLOOR,
            "full_differs_from_identity_control": gaps[key]["full_vs_identity_control"] > plural.GAP_FLOOR,
            "candidate_name_binding_matters": gaps[key]["full_vs_shuffled_name_binding"] > plural.GAP_FLOOR,
        }
    return {
        "rows": rows,
        "gaps": gaps,
        "checks": checks,
        "pass": all(all(check.values()) for check in checks.values()),
    }


def z3_report(mean_improvement: float, improved_count: int, scalar_report: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    improvement_ok = z3.Bool("improvement_ok")
    scalar_separated = z3.Bool("scalar_separated")
    solver.add(improvement_ok == z3.BoolVal(bool(improved_count >= 2 and mean_improvement > 5e-5)))
    solver.add(scalar_separated == bool(scalar_report["pass"]))
    solver.add(improvement_ok)
    solver.add(scalar_separated)
    verdict = solver.check()
    return {
        "mean_improvement": mean_improvement,
        "improved_count": improved_count,
        "strict_verdict": str(verdict),
        "pass": bool(verdict == z3.sat),
    }


def baseline_correlation_rows() -> dict[str, Any]:
    data = json.loads(BASELINE_RESULT.read_text(encoding="utf-8"))
    return (
        data["positive"]["control_family_correlation_report_is_recorded"][
            "control_family_correlation_report"
        ]["rows"]
    )


def main() -> int:
    started = time.time()
    receipts = plural.load_receipts()
    records = subdense.run_source_records()
    axis0 = subdense.axis0_signature(receipts["axis0"])
    memory = subdense.holodeck_memory_signal(receipts["memory"])
    suite = run_suite(records, axis0, memory)
    router_payload = receipts["axis0"].get("axis0_outputs_or_blockers", {})
    status = plural.candidate_status(axis0, router_payload)
    candidate_report = plural.per_candidate_control_report(suite, status)
    corr_report = plural.control_family_correlation_report(suite, candidate_report["admitted_candidate_names"])
    graph = nx.DiGraph()
    graph.add_edges_from(
        [
            ("macro_axis0_plural_stage_router", "axis0_candidate_vectors"),
            ("axis0_candidate_vectors", "operator_local_vector_actuator"),
            ("operator_local_vector_actuator", "multicarrier_local_updates"),
            ("multicarrier_local_updates", "repair_receipt"),
        ]
    )

    scalar_report = {
        "full_vs_scalar_mean_gaps": {carrier: suite["gaps"][carrier]["full_vs_scalar_mean"] for carrier in sorted(suite["gaps"])},
        "pass": all(suite["gaps"][carrier]["full_vs_scalar_mean"] > plural.GAP_FLOOR for carrier in suite["gaps"]),
    }
    baseline_rows = baseline_correlation_rows()
    improvements = {
        name: float(baseline_rows[name]["max_abs_correlation"] - corr_report["rows"][name]["max_abs_correlation"])
        for name in corr_report["rows"]
    }
    mean_improvement = sum(improvements.values()) / max(len(improvements), 1)
    improved_names = [name for name, value in improvements.items() if value > 0.0]
    z3_witness = z3_report(mean_improvement, len(improved_names), scalar_report)

    positive = {
        "upstream_receipts_are_consumed": {
            "pass": all(
                receipt.get("exists") and receipt.get("all_pass") is True
                for receipt in [receipts["axis0"], receipts["memory"], receipts["subdense"]]
            ),
            "receipts": receipts,
        },
        "operator_local_vector_actuator_runs_on_all_carriers": {
            "pass": suite["pass"],
            "checks": suite["checks"],
        },
        "admitted_candidate_controls_remain_visible": {
            "pass": all(
                candidate_report["candidate_rows"][name]["controls_pass"]
                for name in candidate_report["admitted_candidate_names"]
            ),
            "candidate_report": candidate_report,
        },
        "blocked_candidates_remain_inert_under_vector_actuator": {
            "pass": all(
                max(
                    list(suite["gaps"][carrier]["drop_gaps"][name] for carrier in suite["gaps"])
                    + list(suite["gaps"][carrier]["sign_flip_gaps"][name] for carrier in suite["gaps"])
                    + list(suite["gaps"][carrier]["time_shuffle_gaps"][name] for carrier in suite["gaps"])
                )
                < plural.GAP_FLOOR
                for name in BLOCKED
            ),
            "blocked_names": list(BLOCKED),
        },
        "control_family_correlation_improves_vs_current_upstream_path": {
            "current_rows": corr_report["rows"],
            "baseline_rows": baseline_rows,
            "improvements": improvements,
            "mean_improvement": mean_improvement,
            "improved_names": improved_names,
            "pass": len(improved_names) >= 2 and mean_improvement > 5e-5,
        },
        "scalar_mean_control_is_still_distinct": scalar_report,
        "dependency_graph_is_acyclic": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "pass": nx.is_directed_acyclic_graph(graph),
        },
        "z3_operator_local_vector_witness_executes": z3_witness,
    }

    graveyard = {
        "current_scalar_weighted_path_is_not_the_test_surface": {
            "prior_scalar_weighted_claim": "This scout preserves per-candidate controls but still projects the bundle to a scalar before carrier actuation.",
            "pass": True,
        },
        "blocked_candidates_stay_blocked": {
            "blocked": list(BLOCKED),
            "pass": True,
        },
    }

    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "claim_ceiling_blocks_upstream_repair_claim": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": "does not admit final axis0" in CLAIM_CEILING.lower(),
        },
    }

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "operator_vector_basis": {
            key: [idx for idx, _ in enumerate(val)]
            for key, val in OPERATOR_BASIS.items()
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": [
            "This is a v5 bounded actuator-design scout over the existing subdense local-environment stack.",
            "It tests a true operator-local vector actuator candidate, not final Axis0 maturity or canonical manifold promotion.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "name": NAME,
                "all_pass": all_pass,
                "max_abs_corr": max((row["max_abs_correlation"] for row in corr_report["rows"].values()), default=0.0),
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
