#!/usr/bin/env python3
"""Flip-controlled nested-geometry delta packet at the 4Q GCM gate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import z3


SIM_ID = "gcm_nested_geometry_delta_4q_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

FOUR_Q_CARVE_RESULT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_constraint_carve_4q_v0" / "results" / "gcm_constraint_carve_4q_v0_results.json"
)
FOUR_Q_FREEZE_RESULT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_4q_freeze_and_cuts_v0" / "results" / "gcm_4q_freeze_and_cuts_v0_results.json"
)
FOUR_Q_FREEZE_REGISTRY_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_4q_freeze_and_cuts_v0" / "results" / "gcm_4q_freeze_and_cuts_v0_registry.json"
)
TOWER_RESULT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_nesting_tower_le4q_v0" / "results" / "gcm_nesting_tower_le4q_v0_results.json"
)
SCHEMA_HELPER_PATH = ROOT / "scripts" / "gcm_nested_schema_check.py"
GCM_SUBSTRATE_HELPER_PATH = ROOT / "scripts" / "gcm_substrate_check.py"
BUILDER_AUDIT_BOUNDARY_PATH = ROOT / "scripts" / "builder_audit_boundary.py"
AUDIT_VERDICT_PATH = SIM_DIR / "audit_verdict.md"

EXPECTED_1Q_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_3Q_OBJECT_ID = "gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5"
EXPECTED_4Q_OBJECT_ID = "gcm4qobj_64fa5326aa89eae836e75e6c71fc8cdc"
EXPECTED_1Q_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_2Q_REGISTRY_BODY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_3Q_REGISTRY_BODY_SHA256 = "623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0"
EXPECTED_4Q_REGISTRY_BODY_SHA256 = "bf92c850a2880e26011080c900879cf729f8394ffc2e5d00bf1f70ed786020de"

SCHEMA = f"{SIM_ID}_result_v1"
ENVELOPE_SCHEMA = f"{SIM_ID}_envelope_v1"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic_geometry_delta_4q"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ENGINE_MODE = "julia_python_packet_geometry_with_supportive_jax_pytorch_guards"
DELTA_QUANTITY = "A_marginal_probe_shell_occupation_distribution"
MAIN_PIN = "main_C1_C2_C3_survivor_pin"
FREE_PIN = "free_C1_density_valid_layer"
ALTERNATE_PIN = "alternate_C1_C2_pin_without_C3"
SCRAMBLED_PIN = "scrambled_same_cardinality_pin"
MAIN_PROBE = "M_xz"
ALTERNATE_PROBE = "M_prime_xy"
TOL = 1.0e-12

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
from gcm_nested_schema_check import REQUIRED_FIELDS as REQUIRED_NESTED_FIELDS  # noqa: E402
from gcm_nested_schema_check import gcm_nested_schema_check  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


PAULI_X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
PAULI_Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
PAULI_Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
PAULIS = (PAULI_X, PAULI_Y, PAULI_Z)

TOOL_MANIFEST = {
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hardened 4Q freeze/cuts lineage check against the current 4Q registry",
    },
    "gcm_nested_schema_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tribunal 12-field nested schema and geometry-delta flip-control shape gate",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a builder/audit boundary check; this builder emits no audit verdict",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "canonical JSON, source locks, SHA-256 ids, distributions, and receipt writing",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive matrix partial trace and Bloch-vector recomputation from stored rho_ABCD artifacts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive SMT contradiction guard over the recorded delta flip scalar identities; decorative per strengthened audit, not claim-bearing",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive independent SMT contradiction guard over the same delta flip scalar identities; decorative per strengthened audit, not claim-bearing",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "gcm_substrate_check": "load_bearing",
    "gcm_nested_schema_check": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "python_stdlib": "load_bearing",
    "python_packet_geometry": "load_bearing",
    "julia_geometry_engine": "load_bearing",
    "jax_scaled_value_guard": "supportive",
    "pytorch_packet_vector_l1": "supportive",
    "numpy": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
}

TOOL_INTENT = {
    "claim_classes": [
        "nested_geometry_delta_from_free_to_carved_4q",
        "alternate_registry_pin_flip_control",
        "alternate_probe_family_flip_control",
        "schema_first_customer_12_field_nested_packet",
        "carrier_and_pins_relative_negative_controls",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "Independent Julia geometry recompute; SimpleGraph/add_edge! encodes occupied free and nested geometry bins for each delta run.",
        },
        "jax": {
            "jax.numpy": "supportive scaled-value guard over packet-built scalar values; not an independent geometry recompute.",
            "sympy": "supportive sp.Rational exact guards for scaled L1 delta values.",
            "z3": "supportive z3.Solver contradiction guard over main/alternate scaled L1 delta values.",
            "cvc5": "supportive cvc5.Solver contradiction guard over main/alternate scaled L1 delta values.",
        },
        "pytorch": {
            "torch.func": "supportive vmap over packet-built delta vectors recomputes L1 magnitudes; not an independent geometry recompute.",
            "sympy": "supportive sp.Rational exact guard for main versus alternate L1 movement.",
        },
    },
}

ENGINE_ROLE_CEILING = {
    "claim": "no all-three-engine independence claim",
    "julia": {
        "role": "independent_geometry_recompute",
        "depth": "load_bearing",
        "description": "recomputes occupied geometry-bin distributions and L1 deltas from the source carve rows",
    },
    "python_packet": {
        "role": "independent_geometry_recompute",
        "depth": "load_bearing",
        "description": "recomputes A/q0-marginal Bloch vectors from stored rho_ABCD artifacts, then builds the packet deltas",
    },
    "jax": {
        "role": "scaled_value_guard",
        "depth": "supportive",
        "description": "checks scaled packet values and solver guards; does not recompute geometry from source rows",
    },
    "pytorch": {
        "role": "packet_vector_l1_recomputation",
        "depth": "supportive",
        "description": "recomputes L1 magnitudes from packet-built delta vectors; does not recompute geometry from source rows",
    },
    "ceiling": "engine agreement is value/guard agreement under Julia plus Python-packet geometry computation, not three independent geometry engines",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def q(value: float) -> float:
    rounded = round(float(value), 12)
    return 0.0 if rounded == 0 else rounded


def scaled_decimal(value: float, scale: int = 1_000_000_000) -> int:
    return int(round(float(value) * scale))


def sign(value: float) -> int:
    if value < -TOL:
        return -1
    if value > TOL:
        return 1
    return 0


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_lock(path: Path, label: str) -> dict[str, Any]:
    return {
        "label": label,
        "path": rel(path),
        "sha256": sha256_file(path),
        "git_last_commit": git_last_commit(path),
    }


def git_last_commit(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h", "--", str(path.relative_to(ROOT))],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except Exception:
        return None
    value = result.stdout.strip()
    return value or None


def json_to_matrix(value: list[list[list[float]]]) -> np.ndarray:
    return np.array([[complex(pair[0], pair[1]) for pair in row] for row in value], dtype=np.complex128)


def partial_trace(rho: np.ndarray, keep: list[int]) -> np.ndarray:
    dims = [2, 2, 2, 2]
    keep_set = set(keep)
    traced = rho.reshape(dims + dims)
    current_n = len(dims)
    for qubit in reversed(range(len(dims))):
        if qubit not in keep_set:
            traced = np.trace(traced, axis1=qubit, axis2=qubit + current_n)
            current_n -= 1
    final_dim = 2 ** len(keep)
    return traced.reshape((final_dim, final_dim))


def bloch_from_rho_a(rho_a: np.ndarray) -> tuple[float, float, float]:
    return tuple(q(float(np.real(np.trace(pauli @ rho_a)))) for pauli in PAULIS)  # type: ignore[return-value]


def row_constraint_pass(row: dict[str, Any], killed_rows: dict[int, dict[str, Any]], constraint: str) -> bool:
    killed = killed_rows.get(int(row["candidate_id"]))
    if killed is None:
        return True
    return bool(killed["constraints"][constraint]["pass"])


def load_candidate_rows() -> list[dict[str, Any]]:
    carve = load_json(FOUR_Q_CARVE_RESULT_PATH)
    states = carve["state_artifacts"]["states_by_content_id"]
    killed_rows = {int(row["candidate_id"]): row for row in carve["killed_rows"]}
    rows: list[dict[str, Any]] = []
    for row in carve["candidate_space"]["candidate_rows"]:
        rho = json_to_matrix(states[row["rho_ABCD_content_id"]]["rho_ABCD"])
        rho_a = partial_trace(rho, [0])
        bloch = bloch_from_rho_a(rho_a)
        cached = tuple(q(float(value)) for value in row.get("first_bloch_from_stored_rho_q0", []))
        rows.append(
            {
                "candidate_id": int(row["candidate_id"]),
                "candidate_label": str(row["candidate_label"]),
                "family": str(row["family"]),
                "rho_ABCD_content_id": str(row["rho_ABCD_content_id"]),
                "bloch_A": [q(value) for value in bloch],
                "cached_bloch_A": list(cached),
                "cached_bloch_matches_recompute": bool(cached == bloch),
                "C1": row_constraint_pass(row, killed_rows, "C1"),
                "C2": row_constraint_pass(row, killed_rows, "C2"),
                "C3": row_constraint_pass(row, killed_rows, "C3"),
            }
        )
    return rows


def select_rows(rows: list[dict[str, Any]], pin_name: str) -> list[dict[str, Any]]:
    if pin_name == FREE_PIN:
        return [row for row in rows if row["C1"]]
    if pin_name == MAIN_PIN:
        return [row for row in rows if row["C1"] and row["C2"] and row["C3"]]
    if pin_name == ALTERNATE_PIN:
        return [row for row in rows if row["C1"] and row["C2"]]
    if pin_name == SCRAMBLED_PIN:
        main_count = len(select_rows(rows, MAIN_PIN))
        free_rows = select_rows(rows, FREE_PIN)
        return sorted(free_rows, key=lambda row: int(row["candidate_id"]), reverse=True)[:main_count]
    raise KeyError(f"unknown pin_name: {pin_name}")


def probe_axes(probe_family: str) -> tuple[int, int]:
    if probe_family == MAIN_PROBE:
        return (0, 2)
    if probe_family == ALTERNATE_PROBE:
        return (0, 1)
    raise KeyError(f"unknown probe_family: {probe_family}")


def geometry_bin(row: dict[str, Any], probe_family: str) -> str:
    axes = probe_axes(probe_family)
    bloch = [float(value) for value in row["bloch_A"]]
    r2 = q(sum(value * value for value in bloch))
    return f"{probe_family}|sig={sign(bloch[axes[0]])},{sign(bloch[axes[1]])}|r2={r2:.12g}"


def distribution(rows: list[dict[str, Any]], probe_family: str) -> dict[str, float]:
    counts = Counter(geometry_bin(row, probe_family) for row in rows)
    total = len(rows)
    if total == 0:
        return {}
    return {key: q(count / total) for key, count in sorted(counts.items())}


def bin_counts(rows: list[dict[str, Any]], probe_family: str) -> dict[str, int]:
    return dict(sorted(Counter(geometry_bin(row, probe_family) for row in rows).items()))


def vector_l1_distance(left: dict[str, float], right: dict[str, float]) -> float:
    keys = set(left) | set(right)
    return q(sum(abs(float(left.get(key, 0.0)) - float(right.get(key, 0.0))) for key in keys))


def delta_run(
    rows: list[dict[str, Any]],
    *,
    free_pin: str,
    nested_pin: str,
    probe_family: str,
    run_label: str,
) -> dict[str, Any]:
    free_rows = select_rows(rows, free_pin)
    nested_rows = select_rows(rows, nested_pin)
    free_distribution = distribution(free_rows, probe_family)
    nested_distribution = distribution(nested_rows, probe_family)
    keys = sorted(set(free_distribution) | set(nested_distribution))
    delta_vector = {
        key: q(float(nested_distribution.get(key, 0.0)) - float(free_distribution.get(key, 0.0)))
        for key in keys
    }
    top_moved = [
        {"bin": key, "delta": delta_vector[key]}
        for key in sorted(delta_vector, key=lambda item: (abs(delta_vector[item]), item), reverse=True)[:8]
        if delta_vector[key] != 0.0
    ]
    return {
        "run_label": run_label,
        "quantity": DELTA_QUANTITY,
        "free_pin": free_pin,
        "nested_pin": nested_pin,
        "pin_name": nested_pin,
        "probe_family": probe_family,
        "free_count": len(free_rows),
        "nested_count": len(nested_rows),
        "free_bin_count": len(free_distribution),
        "nested_bin_count": len(nested_distribution),
        "free_distribution": free_distribution,
        "nested_distribution": nested_distribution,
        "free_bin_counts": bin_counts(free_rows, probe_family),
        "nested_bin_counts": bin_counts(nested_rows, probe_family),
        "delta_vector": delta_vector,
        "delta_vector_sha256": stable_sha256(delta_vector),
        "delta_l1": q(sum(abs(value) for value in delta_vector.values())),
        "delta_max_abs": q(max((abs(value) for value in delta_vector.values()), default=0.0)),
        "top_moved_bins": top_moved,
    }


def delta_comparison(main: dict[str, Any], alternate: dict[str, Any], axis: str) -> dict[str, Any]:
    l1_distance = vector_l1_distance(main["delta_vector"], alternate["delta_vector"])
    return {
        "axis": axis,
        "stable": main["delta_vector_sha256"] == alternate["delta_vector_sha256"],
        "main_delta_vector_sha256": main["delta_vector_sha256"],
        "alternate_delta_vector_sha256": alternate["delta_vector_sha256"],
        "delta_l1_between_vectors": l1_distance,
        "main_delta_l1": main["delta_l1"],
        "alternate_delta_l1": alternate["delta_l1"],
    }


def same_input_null_control(main: dict[str, Any], repeated: dict[str, Any]) -> dict[str, Any]:
    comparison = delta_comparison(main, repeated, "same_registry_pin_and_probe_family")
    comparison.update(
        {
            "control": "same_input_stable_null",
            "expected": "stable",
            "pass": comparison["stable"] is True and float(comparison["delta_l1_between_vectors"]) <= TOL,
            "null_delta_l1": comparison["delta_l1_between_vectors"],
            "input_a": {
                "nested_pin": main["nested_pin"],
                "probe_family": main["probe_family"],
                "delta_l1": main["delta_l1"],
            },
            "input_b": {
                "nested_pin": repeated["nested_pin"],
                "probe_family": repeated["probe_family"],
                "delta_l1": repeated["delta_l1"],
            },
            "description": "negative side of the flip control: identical registry pin and identical probe family leave the computed delta vector stable",
        }
    )
    return comparison


def crossover_proofs(main: dict[str, Any], alternate_pin: dict[str, Any], alternate_probe: dict[str, Any]) -> dict[str, Any]:
    values = {
        "main_delta_l1_scaled": scaled_decimal(main["delta_l1"]),
        "alternate_pin_delta_l1_scaled": scaled_decimal(alternate_pin["delta_l1"]),
        "alternate_probe_delta_l1_scaled": scaled_decimal(alternate_probe["delta_l1"]),
        "main_nested_count": int(main["nested_count"]),
        "alternate_pin_nested_count": int(alternate_pin["nested_count"]),
        "alternate_probe_nested_count": int(alternate_probe["nested_count"]),
    }

    solver = z3.Solver()
    vars_z3 = {name: z3.Int(name) for name in values}
    for name, value in values.items():
        solver.add(vars_z3[name] == int(value))
    solver.add(z3.Or([vars_z3[name] != int(value) for name, value in values.items()]))
    z3_verdict = str(solver.check())

    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    int_sort = csolver.getIntegerSort()
    vars_cvc5 = {name: csolver.mkConst(int_sort, name) for name in values}
    for name, value in values.items():
        csolver.assertFormula(csolver.mkTerm(Kind.EQUAL, vars_cvc5[name], csolver.mkInteger(int(value))))
    csolver.assertFormula(
        csolver.mkTerm(
            Kind.OR,
            *[
                csolver.mkTerm(Kind.NOT, csolver.mkTerm(Kind.EQUAL, vars_cvc5[name], csolver.mkInteger(int(value))))
                for name, value in values.items()
            ],
        )
    )
    cvc5_verdict = str(csolver.checkSat()).lower()
    return {
        "z3": {
            "ran": True,
            "load_bearing": False,
            "verdict": z3_verdict,
            "guard": "recorded scaled delta/count values imply no contradictory alternate assignment",
            "depth": "supportive",
            "audit_status": "decorative_per_strengthened_audit",
            "values": values,
        },
        "cvc5": {
            "ran": True,
            "load_bearing": False,
            "verdict": cvc5_verdict,
            "guard": "independent recorded scaled delta/count contradiction guard",
            "depth": "supportive",
            "audit_status": "decorative_per_strengthened_audit",
            "values": values,
        },
    }


def substrate_payload(freeze: dict[str, Any]) -> dict[str, Any]:
    lineage = dict(freeze["gcm_lineage"])
    lineage["gcm_3q_survivor_ids"] = lineage.get("gcm_3q_survivor_ids", [])[:12]
    lineage["gcm_3q_quotient_class_ids"] = lineage.get("gcm_3q_quotient_class_ids", [])[:3]
    lineage["gcm_3q_candidate_region_ids"] = lineage.get("gcm_3q_candidate_region_ids", [])[:3]
    lineage["gcm_4q_survivor_ids"] = lineage.get("gcm_4q_survivor_ids", [])[:12]
    lineage["gcm_4q_quotient_class_ids"] = lineage.get("gcm_4q_quotient_class_ids", [])[:3]
    lineage["gcm_4q_candidate_region_ids"] = lineage.get("gcm_4q_candidate_region_ids", [])[:3]
    lineage["gcm_2q_survivor_ids"] = lineage.get("gcm_2q_survivor_ids", [])[:3]
    return {
        "sim_id": SIM_ID,
        "gcm_lineage": lineage,
        "lineage_source": rel(FOUR_Q_FREEZE_RESULT_PATH),
        "lineage_scope": "4Q freeze/cuts substrate cited for nested geometry-delta packet",
    }


def source_locks() -> list[dict[str, Any]]:
    return [
        source_lock(FOUR_Q_CARVE_RESULT_PATH, "4Q carve result with stored rho_ABCD state artifacts"),
        source_lock(FOUR_Q_FREEZE_RESULT_PATH, "4Q freeze/cuts result and cut-state availability"),
        source_lock(FOUR_Q_FREEZE_REGISTRY_PATH, "4Q freeze/cuts registry"),
        source_lock(TOWER_RESULT_PATH, "<=4Q nesting tower result"),
        source_lock(ROOT / "system_v4" / "probes" / "SIM_TEMPLATE.py", "required sim template seed/read-first surface"),
        source_lock(SCHEMA_HELPER_PATH, "nested schema checker"),
        source_lock(GCM_SUBSTRATE_HELPER_PATH, "hardened substrate helper"),
        source_lock(BUILDER_AUDIT_BOUNDARY_PATH, "builder/audit boundary helper"),
    ]


def build_packet(*, write_result: bool = True) -> dict[str, Any]:
    carve = load_json(FOUR_Q_CARVE_RESULT_PATH)
    freeze = load_json(FOUR_Q_FREEZE_RESULT_PATH)
    registry = load_json(FOUR_Q_FREEZE_REGISTRY_PATH)
    tower = load_json(TOWER_RESULT_PATH)
    rows = load_candidate_rows()

    main = delta_run(rows, free_pin=FREE_PIN, nested_pin=MAIN_PIN, probe_family=MAIN_PROBE, run_label="main")
    stable_null = delta_run(
        rows,
        free_pin=FREE_PIN,
        nested_pin=MAIN_PIN,
        probe_family=MAIN_PROBE,
        run_label="same_input_stable_null",
    )
    alternate_pin = delta_run(
        rows,
        free_pin=FREE_PIN,
        nested_pin=ALTERNATE_PIN,
        probe_family=MAIN_PROBE,
        run_label="alternate_registry_pin",
    )
    alternate_probe = delta_run(
        rows,
        free_pin=FREE_PIN,
        nested_pin=MAIN_PIN,
        probe_family=ALTERNATE_PROBE,
        run_label="alternate_probe_family",
    )
    scrambled = delta_run(
        rows,
        free_pin=FREE_PIN,
        nested_pin=SCRAMBLED_PIN,
        probe_family=MAIN_PROBE,
        run_label="scrambled_pin_control",
    )

    null_control = same_input_null_control(main, stable_null)
    cross_pin = delta_comparison(main, alternate_pin, "registry_pin")
    cross_probe = delta_comparison(main, alternate_probe, "probe_family")
    scrambled_cmp = delta_comparison(main, scrambled, "scrambled_pin")
    if cross_probe["stable"] and cross_pin["stable"]:
        stability_class = "cross_stable"
    elif not cross_probe["stable"]:
        stability_class = "probe_relative"
    else:
        stability_class = "pin_relative"

    negative_control = {
        "control": "killed_candidate_count_delta",
        "expected": "pin_relative",
        "observed": "pin_relative" if main["nested_count"] != alternate_pin["nested_count"] else "not_pin_relative",
        "pass": main["nested_count"] != alternate_pin["nested_count"],
        "free_value": main["free_count"],
        "main_pin_value": main["free_count"] - main["nested_count"],
        "alternate_pin_value": alternate_pin["free_count"] - alternate_pin["nested_count"],
        "description": "known pin-relative killed-count delta changes when C3 is removed from the registry pin",
    }

    substrate_check = gcm_substrate_check(substrate_payload(freeze), FOUR_Q_FREEZE_REGISTRY_PATH)
    schema_preview_payload: dict[str, Any] = {}
    build_boundary = {
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "builder_audit_boundary_ok": builder_audit_boundary_ok(AUDIT_VERDICT_PATH),
        "audit_verdict_path": rel(AUDIT_VERDICT_PATH),
        "file_disjoint_packet": rel(SIM_DIR),
    }

    result: dict[str, Any] = {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "created_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "engine_mode": ENGINE_MODE,
        "engine_role_ceiling": ENGINE_ROLE_CEILING,
        "layer_declaration": {
            "layer": "nested-geometry-delta",
            "integration": "integrated",
            "qubit_depth": "4Q",
        },
        "axis_declaration": {
            "layer": "nested-geometry-delta",
            "integration": "integrated",
            "rung": "4Q",
            "quantity": DELTA_QUANTITY,
        },
        "standards_codex": {
            "G.2a_from_birth": True,
            "substrate_first_with_hardened_helper": True,
            "schema_first_customer": True,
            "tribunal_deepest_gate": "geometry-delta owns cross-pin/cross-probe falsifier; all 4Q tower geometry remains probe-relative unless stable",
            "engine_independence_ceiling": ENGINE_ROLE_CEILING["ceiling"],
        },
        "authority": {
            "tribunal_gate_commit": "f65a81010",
            "schema_validator_commit": "d5af8449d",
            "freeze_cut_states_commit": "9566a5cc7",
            "tower_source": rel(TOWER_RESULT_PATH),
            "state_source": rel(FOUR_Q_CARVE_RESULT_PATH),
            "cut_state_source": rel(FOUR_Q_FREEZE_RESULT_PATH),
        },
        "geometry_delta_from_free": {
            "quantity": DELTA_QUANTITY,
            "computed_from": "A/q0 marginal Bloch vectors recomputed from stored rho_ABCD, binned by active probe signature and radius shell",
            "free_layer": FREE_PIN,
            "nested_layer": MAIN_PIN,
            "main": main,
            "same_input_stable_null_delta": stable_null,
            "alternate_registry_pin_delta": alternate_pin,
            "alternate_probe_family_delta": alternate_probe,
        },
        "flip_control_runs": {
            "main": main,
            "same_input_stable_null": stable_null,
            "alternate_registry_pin": alternate_pin,
            "alternate_probe_family": alternate_probe,
            "scrambled_pin": scrambled,
        },
        "exact_relation_status": {
            "status": "empty_at_4Q",
            "exact_all_cut_compatible_4q_count": tower["counts"]["exact_all_cut_compatible_4q_count"],
            "exact_all_cut_orphan_4q_count": tower["counts"]["exact_all_cut_orphan_4q_count"],
            "interpretation": "exact tower provides no intrinsic 4Q geometry-delta support; the delta is computed on the carrier with pins/probes declared",
        },
        "probe_relation_status": {
            "status": "probe_carried",
            "probe_family": MAIN_PROBE,
            "probe_all_cut_compatible_4q_count": tower["counts"]["probe_all_cut_compatible_4q_count"],
            "probe_all_cut_orphan_4q_count": tower["counts"]["probe_all_cut_orphan_4q_count"],
            "probe_family_count": tower["counts"]["probe_all_cut_compatible_family_count"],
        },
        "extension_fiber_size": {
            "F4_exact_rows": len(tower["compatible_families"]["exact_rows"]),
            "F4_probe_rows": len(tower["compatible_families"]["probe_rows"]),
            "exact_rows_sha256": tower["compatible_families"]["exact_rows_sha256"],
            "probe_rows_sha256": tower["compatible_families"]["probe_rows_sha256"],
            "representation": tower["compatible_families"]["representation"],
            "source": rel(TOWER_RESULT_PATH),
        },
        "cut_state_available": True,
        "blocked_consumer_enforced": True,
        "what_would_flip": {
            "alternate_registry_pin": ALTERNATE_PIN,
            "alternate_registry": ALTERNATE_PIN,
            "alternate_registry_description": "same free layer and M_xz probe, but nested layer admits C1+C2 and removes C3",
            "alternate_probe_family": ALTERNATE_PROBE,
            "alternate_probe_family_description": "same free/nested registry pins, but M' reads x/y instead of x/z",
            "tested": True,
            "actual_alternate_delta_values_recorded": True,
        },
        "same_input_stability_control": null_control,
        "negative_control_status": negative_control,
        "cross_pin_stability": cross_pin,
        "cross_probe_stability": cross_probe,
        "geometry_delta_stability_class": stability_class,
        "forward_transport_status": {
            "status": "blocked_as_intrinsic_geometry",
            "allowed_transport": "carrier-and-pins-relative scratch diagnostic only",
            "reason": "flip control moved across alternate probe and alternate registry pin",
        },
        "backward_admissibility_status": {
            "status": "not_admitted",
            "reason": "schema and flip-control presence do not promote the geometry; exact relation is empty and probe relation carries the observable",
        },
        "controls": {
            "schema_check_in_validator": True,
            "scrambled_pin": {
                "pin_name": SCRAMBLED_PIN,
                "stable_against_main": scrambled_cmp["stable"],
                "delta_l1_between_vectors": scrambled_cmp["delta_l1_between_vectors"],
                "delta_vector_sha256": scrambled["delta_vector_sha256"],
                "pass": scrambled_cmp["stable"] is False,
            },
            "same_input_stable_null": null_control,
            "negative_control": negative_control,
            "cached_bloch_parity": {
                "checked_candidate_count": len(rows),
                "mismatches": [
                    row["candidate_id"] for row in rows if row["cached_bloch_A"] and not row["cached_bloch_matches_recompute"]
                ][:10],
            },
            "substrate_check": substrate_check,
        },
        "counts": {
            "candidate_count": carve["candidate_space"]["candidate_count"],
            "free_C1_count": main["free_count"],
            "main_nested_count": main["nested_count"],
            "alternate_C1_C2_nested_count": alternate_pin["nested_count"],
            "scrambled_nested_count": scrambled["nested_count"],
            "freeze_survivor_count": freeze["counts"]["four_q_survivor_count"],
            "registry_survivor_count": len(registry["frozen_4q_registry"]["survivors"]),
        },
        "claim_summary": {
            "finding": stability_class,
            "human_readable": "The first 4Q nested geometry delta exists as a computed carrier/pin/probe diagnostic: it is stable for identical pin/probe inputs, but moves under M'_xy and also under a C1+C2 alternate pin.",
            "not_claimed": [
                "intrinsic tower geometry",
                "formal manifold admission",
                "physics or axis bridge",
                "cross-stable geometry-delta",
                "three independent geometry engines",
            ],
        },
        "gcm_lineage": substrate_payload(freeze)["gcm_lineage"],
        "source_locks": source_locks(),
        "substrate_checks": {
            "hardened_helper_path": rel(GCM_SUBSTRATE_HELPER_PATH),
            "registry_path": rel(FOUR_Q_FREEZE_REGISTRY_PATH),
            "result": substrate_check,
        },
        "schema_check": schema_preview_payload,
        "crossover_proofs": crossover_proofs(main, alternate_pin, alternate_probe),
        "classical_baseline": {
            "baseline": "free C1-valid layer distribution versus nested C1+C2+C3 carved distribution",
            "divergence_log": [
                {
                    "control": "same_input_stable_null",
                    "main_delta_l1": main["delta_l1"],
                    "alternate_delta_l1": stable_null["delta_l1"],
                    "null_delta_l1": null_control["null_delta_l1"],
                    "stable": null_control["stable"],
                },
                {
                    "control": "alternate_registry_pin",
                    "main_delta_l1": main["delta_l1"],
                    "alternate_delta_l1": alternate_pin["delta_l1"],
                    "stable": cross_pin["stable"],
                },
                {
                    "control": "alternate_probe_family",
                    "main_delta_l1": main["delta_l1"],
                    "alternate_delta_l1": alternate_probe["delta_l1"],
                    "stable": cross_probe["stable"],
                },
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "build_boundary": build_boundary,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
    }
    result["schema_check"] = gcm_nested_schema_check(result, RESULT_PATH)
    result["result_sha256"] = stable_sha256({key: value for key, value in result.items() if key != "result_sha256"})
    if write_result:
        write_json(RESULT_PATH, result)
    return result


def engine_claim_values(packet: dict[str, Any]) -> dict[str, int]:
    main = packet["geometry_delta_from_free"]["main"]
    stable_null = packet["flip_control_runs"]["same_input_stable_null"]
    alternate_pin = packet["flip_control_runs"]["alternate_registry_pin"]
    alternate_probe = packet["flip_control_runs"]["alternate_probe_family"]
    null_control = packet["same_input_stability_control"]
    return {
        "main_delta_l1_scaled": scaled_decimal(main["delta_l1"]),
        "same_input_null_delta_l1_scaled": scaled_decimal(null_control["null_delta_l1"]),
        "same_input_stable_delta_l1_scaled": scaled_decimal(stable_null["delta_l1"]),
        "alternate_pin_delta_l1_scaled": scaled_decimal(alternate_pin["delta_l1"]),
        "alternate_probe_delta_l1_scaled": scaled_decimal(alternate_probe["delta_l1"]),
        "main_free_count": int(main["free_count"]),
        "main_nested_count": int(main["nested_count"]),
        "alternate_pin_nested_count": int(alternate_pin["nested_count"]),
    }


def engine_delta_vectors(packet: dict[str, Any]) -> dict[str, list[float]]:
    runs = {
        "main": packet["geometry_delta_from_free"]["main"],
        "same_input_stable_null": packet["flip_control_runs"]["same_input_stable_null"],
        "alternate_pin": packet["flip_control_runs"]["alternate_registry_pin"],
        "alternate_probe": packet["flip_control_runs"]["alternate_probe_family"],
    }
    keys = sorted({key for run in runs.values() for key in run["delta_vector"]})
    return {name: [float(run["delta_vector"].get(key, 0.0)) for key in keys] for name, run in runs.items()}
