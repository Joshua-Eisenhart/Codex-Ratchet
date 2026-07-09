#!/usr/bin/env python3
"""Falsify the UP-130 claim that four substages emerge from a dual ratchet.

The audited source is the exact member
``sims_and_scripts/four_substages_emerge_from_dual_ratchet_sim.py`` from
``/Users/joshuaeisenhart/Desktop/97.zip`` with SHA-256
``6d412087c47b12dbf82b982589c801e531e8fff1c0398bdb117a64bd084b3741``.

This audit checks the source's own finite construction.  It does not propose a
replacement substage architecture.  A passing run means the overclaim was
caught: the claimed quarter-turn is a pi Bloch rotation, the two adjoint
channels commute, the unitary legs do not change entropy, the C3 predicate
already fixes word length four, the controls do not isolate their claimed
gates, ABAB and BABA are one cyclic orbit, and the source-chart count is not an
independent derivation.

Classification: scratch_diagnostic.  Promotion and formal admission are
forbidden.
"""

from __future__ import annotations

import ast
import datetime as dt
import hashlib
import itertools
import json
import math
import platform
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy import __version__ as scipy_version
from scipy.linalg import expm


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = SOURCE_PATH.with_name(f"{SOURCE_PATH.stem}_results.json")
PACKAGE_PATH = Path("/Users/joshuaeisenhart/Desktop/97.zip")
UP130_SOURCE_MEMBER = "sims_and_scripts/four_substages_emerge_from_dual_ratchet_sim.py"
UP130_RESULT_MEMBER = "sims_and_scripts/four_substages_emerge_from_dual_ratchet_sim_results.json"
CHART_MEMBER = "reference_docs/engine_math/source_schedule_tables/engine_16_source_stage_slots.json"
EXPECTED_UP130_SOURCE_SHA256 = "6d412087c47b12dbf82b982589c801e531e8fff1c0398bdb117a64bd084b3741"

SIM_ID = "four_substages_up130_fabrication_audit_sim"
classification = "scratch_diagnostic"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
promotion_allowed = False
formal_admission_allowed = False

CLAIM_CEILING = (
    "Scratch diagnostic only for the exact UP-130 source hash. A passing run "
    "catches the stated derivation overclaim; it does not establish a correct "
    "substage count, a replacement dual-ratchet mechanism, engine admission, "
    "Axis0, a manifold layer, or physics."
)

BLOCKED_CONSUMERS = [
    "four_substage_architecture",
    "dual_ratchet_architecture",
    "engine_schedule_admission",
    "manifold_layer_admission",
    "Axis0",
    "formal_admission",
    "physics",
]

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing complex matrix algebra, Bloch adjoint matrices, "
            "superoperator commutators, spectra, entropy, and finite controls"
        ),
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing scipy.linalg.expm reproduction of the audited "
            "exp(-i*pi*sigma/2) and half-leg operators"
        ),
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive ZIP-member source lock, SHA-256 hashing, AST inspection, "
            "word enumeration, timestamps, paths, and JSON serialization"
        ),
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "python_stdlib": "supportive",
}

I2 = np.eye(2, dtype=np.complex128)
SX = np.array([[0, 1], [1, 0]], dtype=np.complex128)
SY = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
SZ = np.array([[1, 0], [0, -1]], dtype=np.complex128)
PAULIS = (SX, SY, SZ)
AXES = {"A": SZ, "B": SX}
TOL = 1.0e-10
ENTROPY_TOL = 1.0e-12


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(row) for key, row in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(row) for row in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, np.generic):
        return jsonable(value.item())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_audit_target() -> dict[str, Any]:
    package_bytes = PACKAGE_PATH.read_bytes()
    with zipfile.ZipFile(PACKAGE_PATH) as archive:
        source_bytes = archive.read(UP130_SOURCE_MEMBER)
        result_bytes = archive.read(UP130_RESULT_MEMBER)
        chart_bytes = archive.read(CHART_MEMBER)
    target_result = json.loads(result_bytes.decode("utf-8"))
    actual_source_sha256 = sha256_bytes(source_bytes)
    source_lock_pass = actual_source_sha256 == EXPECTED_UP130_SOURCE_SHA256
    return {
        "source_bytes": source_bytes,
        "source_text": source_bytes.decode("utf-8"),
        "chart_bytes": chart_bytes,
        "target_result": target_result,
        "gate": {
            "package_path": str(PACKAGE_PATH),
            "package_sha256": sha256_bytes(package_bytes),
            "source_member": UP130_SOURCE_MEMBER,
            "expected_source_sha256": EXPECTED_UP130_SOURCE_SHA256,
            "actual_source_sha256": actual_source_sha256,
            "source_hash_match": source_lock_pass,
            "target_result_member": UP130_RESULT_MEMBER,
            "target_result_sha256": sha256_bytes(result_bytes),
            "target_result_claimed_verdict": bool(
                target_result.get("policy_eval", {}).get(
                    "FOUR_SUBSTAGES_DERIVED_FROM_DUAL_RATCHET"
                )
            ),
            "chart_member": CHART_MEMBER,
            "chart_sha256": sha256_bytes(chart_bytes),
            "pass": source_lock_pass,
        },
    }


def source_leg_unitary(axis: str, fraction: float = 1.0) -> np.ndarray:
    return expm(-1j * (math.pi / 2.0 * fraction) * AXES[axis])


def apply_unitary(rho: np.ndarray, unitary: np.ndarray) -> np.ndarray:
    return unitary @ rho @ unitary.conj().T


def bloch_rotation_matrix(unitary: np.ndarray) -> np.ndarray:
    return np.array(
        [
            [
                0.5 * np.trace(left @ unitary @ right @ unitary.conj().T).real
                for right in PAULIS
            ]
            for left in PAULIS
        ],
        dtype=np.float64,
    )


def principal_rotation_angle(rotation: np.ndarray) -> float:
    cosine = float(np.clip((np.trace(rotation) - 1.0) / 2.0, -1.0, 1.0))
    return math.acos(cosine)


def bloch_angle_gate() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for axis, label in (("A", "Z"), ("B", "X")):
        unitary = source_leg_unitary(axis)
        rotation = bloch_rotation_matrix(unitary)
        angle = principal_rotation_angle(rotation)
        rows[f"{axis}_about_{label}"] = {
            "source_exponential": f"exp(-i*pi*{label}/2)",
            "unitary_minus_minus_i_sigma_max_abs": float(
                np.max(np.abs(unitary - (-1j * AXES[axis])))
            ),
            "bloch_rotation_matrix": rotation,
            "actual_bloch_angle_radians": angle,
            "actual_bloch_angle_degrees": math.degrees(angle),
            "claimed_quarter_turn_degrees": 90.0,
            "angle_multiplier_over_claim": angle / (math.pi / 2.0),
        }
    actual_angles = [row["actual_bloch_angle_radians"] for row in rows.values()]
    passed = all(abs(angle - math.pi) <= TOL for angle in actual_angles)
    return {
        "rows": rows,
        "finding": (
            "exp(-i*pi*sigma/2)=-i*sigma induces a pi (180 degree) Bloch "
            "rotation, not a pi/2 quarter-turn."
        ),
        "pass": bool(passed),
    }


def adjoint_superoperator(unitary: np.ndarray) -> np.ndarray:
    # Column-vectorization: vec(U rho U^dagger)=(U* tensor U) vec(rho).
    return np.kron(unitary.conj(), unitary)


def superoperator_commutator_gate() -> dict[str, Any]:
    unitary_z = source_leg_unitary("A")
    unitary_x = source_leg_unitary("B")
    ad_z = adjoint_superoperator(unitary_z)
    ad_x = adjoint_superoperator(unitary_x)
    channel_commutator = ad_z @ ad_x - ad_x @ ad_z
    unitary_commutator = unitary_z @ unitary_x - unitary_x @ unitary_z
    channel_frobenius = float(np.linalg.norm(channel_commutator, ord="fro"))
    channel_spectral = float(np.linalg.norm(channel_commutator, ord=2))
    unitary_frobenius = float(np.linalg.norm(unitary_commutator, ord="fro"))
    passed = channel_frobenius <= TOL and unitary_frobenius > 1.0
    return {
        "Ad_Z_Ad_X_commutator_frobenius_norm": channel_frobenius,
        "Ad_Z_Ad_X_commutator_spectral_norm": channel_spectral,
        "underlying_unitary_commutator_frobenius_norm": unitary_frobenius,
        "adjoint_channels_commute": bool(channel_frobenius <= TOL),
        "finding": (
            "The Pauli representatives anticommute as unitaries, but their "
            "global phase disappears under conjugation, so Ad_Z and Ad_X commute."
        ),
        "pass": bool(passed),
    }


def probe_set(n: int = 12, seed: int = 0) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    probes = []
    for _ in range(n):
        vector = rng.normal(size=3)
        vector = 0.7 * vector / np.linalg.norm(vector)
        probes.append(
            0.5
            * (
                I2
                + vector[0] * SX
                + vector[1] * SY
                + vector[2] * SZ
            )
        )
    return probes


def run_word(
    word: str,
    rho: np.ndarray,
    half_leg_at: int | None = None,
) -> np.ndarray:
    result = rho
    for index, axis in enumerate(word):
        fraction = 0.5 if half_leg_at == index else 1.0
        result = apply_unitary(result, source_leg_unitary(axis, fraction))
    return result


def max_return_distance(
    word: str,
    probes: list[np.ndarray],
    half_leg_at: int | None = None,
) -> float:
    return max(
        float(np.linalg.norm(run_word(word, probe, half_leg_at) - probe, ord="fro"))
        for probe in probes
    )


def closes(
    word: str,
    probes: list[np.ndarray],
    half_leg_at: int | None = None,
) -> bool:
    return max_return_distance(word, probes, half_leg_at) < 1.0e-9


def alternating(word: str) -> bool:
    return all(word[index] != word[(index + 1) % len(word)] for index in range(len(word)))


def source_c3_count_predicate(word: str) -> bool:
    return word.count("A") == 2 and word.count("B") == 2


def semantic_full_leg_c3(word: str, half_leg_at: int | None = None) -> bool:
    return source_c3_count_predicate(word) and half_leg_at is None


def von_neumann_entropy(rho: np.ndarray) -> float:
    hermitian = 0.5 * (rho + rho.conj().T)
    eigenvalues = np.linalg.eigvalsh(hermitian).real
    eigenvalues = np.clip(eigenvalues, 0.0, 1.0)
    positive = eigenvalues[eigenvalues > 0.0]
    return float(-np.sum(positive * np.log(positive)))


def entropy_change_gate(probes: list[np.ndarray]) -> dict[str, Any]:
    schedules = {
        "A": ("A", None),
        "B": ("B", None),
        "AB": ("AB", None),
        "ABAB": ("ABAB", None),
        "ABAB_half_A_at_0": ("ABAB", 0),
    }
    rows: dict[str, Any] = {}
    all_deltas: list[float] = []
    for label, (word, half_leg_at) in schedules.items():
        deltas = [
            von_neumann_entropy(run_word(word, probe, half_leg_at))
            - von_neumann_entropy(probe)
            for probe in probes
        ]
        all_deltas.extend(deltas)
        rows[label] = {
            "min_delta_entropy_nats": min(deltas),
            "max_delta_entropy_nats": max(deltas),
            "max_abs_delta_entropy_nats": max(abs(delta) for delta in deltas),
        }
    max_abs_delta = max(abs(delta) for delta in all_deltas)
    passed = max_abs_delta <= ENTROPY_TOL
    return {
        "probe_count": len(probes),
        "probe_bloch_radius": 0.7,
        "rows": rows,
        "global_max_abs_delta_entropy_nats": max_abs_delta,
        "entropy_ratcheting_detected": bool(max_abs_delta > ENTROPY_TOL),
        "finding": "Every audited leg is unitary conjugation, so von Neumann entropy is invariant.",
        "pass": bool(passed),
    }


def source_static_analysis(source_text: str) -> dict[str, Any]:
    tree = ast.parse(source_text)
    both_directions = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "both_directions"
    )
    count_requirements: dict[str, int] = {}
    return_node = next(node for node in ast.walk(both_directions) if isinstance(node, ast.Return))
    for comparison in ast.walk(return_node.value):
        if not (
            isinstance(comparison, ast.Compare)
            and len(comparison.ops) == 1
            and isinstance(comparison.ops[0], ast.Eq)
            and len(comparison.comparators) == 1
            and isinstance(comparison.comparators[0], ast.Constant)
            and isinstance(comparison.comparators[0].value, int)
        ):
            continue
        call = comparison.left
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "count"
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "word"
            and len(call.args) == 1
            and isinstance(call.args[0], ast.Constant)
            and isinstance(call.args[0].value, str)
        ):
            continue
        count_requirements[call.args[0].value] = comparison.comparators[0].value

    engine_match_assignment = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "g_engine_match" for target in node.targets)
    )
    equality_pairs = []
    for comparison in ast.walk(engine_match_assignment.value):
        if not (
            isinstance(comparison, ast.Compare)
            and len(comparison.ops) == 1
            and isinstance(comparison.ops[0], ast.Eq)
            and len(comparison.comparators) == 1
        ):
            continue
        left = comparison.left
        right = comparison.comparators[0]
        if isinstance(left, ast.Name) and isinstance(right, ast.Name):
            equality_pairs.append([left.id, right.id])
    chart_equals_minimal = any(
        set(pair) == {"engine_substages_per_stage", "minimal"}
        for pair in equality_pairs
    )
    return {
        "both_directions_line": both_directions.lineno,
        "both_directions_return_expression": ast.get_source_segment(source_text, return_node.value),
        "count_requirements": count_requirements,
        "g_engine_match_line": engine_match_assignment.lineno,
        "g_engine_match_expression": ast.get_source_segment(
            source_text, engine_match_assignment.value
        ),
        "chart_count_compared_to_minimal": chart_equals_minimal,
    }


def count_constraint_gate(static_analysis: dict[str, Any]) -> dict[str, Any]:
    matching_by_length = {}
    for length in range(1, 9):
        words = ("".join(symbols) for symbols in itertools.product("AB", repeat=length))
        matching_by_length[str(length)] = sum(
            1 for word in words if source_c3_count_predicate(word)
        )
    allowed_lengths = [
        int(length)
        for length, count in matching_by_length.items()
        if count > 0
    ]
    requirements = static_analysis["count_requirements"]
    forced_length = sum(requirements.values()) if requirements == {"A": 2, "B": 2} else None
    passed = (
        requirements == {"A": 2, "B": 2}
        and forced_length == 4
        and allowed_lengths == [4]
        and matching_by_length["4"] == 6
    )
    return {
        "source_ast": {
            "line": static_analysis["both_directions_line"],
            "return_expression": static_analysis["both_directions_return_expression"],
            "count_requirements": requirements,
        },
        "logical_identity": "length = count(A) + count(B) = 2 + 2 = 4",
        "forced_length": forced_length,
        "matching_words_by_length": matching_by_length,
        "allowed_lengths_under_C3": allowed_lengths,
        "n_C3_words_at_length_4": matching_by_length["4"],
        "minimal_length_preselected_by_C3": bool(forced_length == 4),
        "finding": "C3 alone fixes L=4, so the scan cannot independently derive the count four.",
        "pass": bool(passed),
    }


def truth_vector(
    word: str,
    probes: list[np.ndarray],
    half_leg_at: int | None,
) -> dict[str, Any]:
    c1 = closes(word, probes, half_leg_at)
    c2 = alternating(word)
    c3_source = source_c3_count_predicate(word)
    c3_semantic = semantic_full_leg_c3(word, half_leg_at)
    source_vector = [c1, c2, c3_source]
    semantic_vector = [c1, c2, c3_semantic]
    gate_names = ["C1_closure", "C2_alternation", "C3_both_directions"]
    source_failures = [name for name, truth in zip(gate_names, source_vector) if not truth]
    semantic_failures = [name for name, truth in zip(gate_names, semantic_vector) if not truth]
    return {
        "word": word,
        "half_leg_at": half_leg_at,
        "return_distance": max_return_distance(word, probes, half_leg_at),
        "source_predicate_truth_vector_C1_C2_C3": source_vector,
        "source_predicate_failed_gates": source_failures,
        "source_predicate_failure_count": len(source_failures),
        "semantic_full_leg_truth_vector_C1_C2_C3": semantic_vector,
        "semantic_full_leg_failed_gates": semantic_failures,
        "semantic_full_leg_failure_count": len(semantic_failures),
    }


def control_truth_vector_gate(probes: list[np.ndarray]) -> dict[str, Any]:
    controls = {
        "AB": {"target_gate": "C1_closure", "row": truth_vector("AB", probes, None)},
        "AAAA": {"target_gate": "C2_alternation", "row": truth_vector("AAAA", probes, None)},
        "ABAB_half_A_at_0": {
            "target_gate": "C3_both_directions",
            "row": truth_vector("ABAB", probes, 0),
        },
    }
    for control in controls.values():
        target_gate = control["target_gate"]
        row = control["row"]
        row["isolates_exactly_one_source_gate"] = row["source_predicate_failure_count"] == 1
        row["isolates_claimed_source_gate"] = row["source_predicate_failed_gates"] == [target_gate]
        row["isolates_exactly_one_semantic_gate"] = row["semantic_full_leg_failure_count"] == 1
        row["isolates_claimed_semantic_gate"] = row["semantic_full_leg_failed_gates"] == [target_gate]
    exact_vectors = (
        controls["AB"]["row"]["source_predicate_truth_vector_C1_C2_C3"]
        == [False, True, False]
        and controls["AAAA"]["row"]["source_predicate_truth_vector_C1_C2_C3"]
        == [True, False, False]
        and controls["ABAB_half_A_at_0"]["row"]["source_predicate_truth_vector_C1_C2_C3"]
        == [False, True, True]
        and controls["ABAB_half_A_at_0"]["row"]["semantic_full_leg_truth_vector_C1_C2_C3"]
        == [False, True, False]
    )
    none_isolates_claimed_gate = not any(
        control["row"]["isolates_claimed_source_gate"]
        or control["row"]["isolates_claimed_semantic_gate"]
        for control in controls.values()
    )
    passed = exact_vectors and none_isolates_claimed_gate
    return {
        "gate_order": ["C1_closure", "C2_alternation", "C3_both_directions"],
        "controls": controls,
        "each_control_isolates_its_claimed_gate": False,
        "finding": (
            "AB and AAAA each fail two source predicates. The half-leg fails "
            "source C1 while source C3 remains true because C3 ignores leg size; "
            "under the intended full-leg meaning it fails C1 and C3 together."
        ),
        "pass": bool(passed),
    }


def cyclic_rotations(word: str) -> list[str]:
    return sorted({word[index:] + word[:index] for index in range(len(word))})


def cyclic_orbit_gate() -> dict[str, Any]:
    words = ["ABAB", "BABA"]
    representatives = {min(cyclic_rotations(word)) for word in words}
    same_orbit = len(representatives) == 1
    reversal_is_rotation = words[0][::-1] in cyclic_rotations(words[0])
    passed = same_orbit and reversal_is_rotation
    return {
        "words": words,
        "orbits": {word: cyclic_rotations(word) for word in words},
        "canonical_representatives": sorted(representatives),
        "distinct_cyclic_orbit_count": len(representatives),
        "ABAB_and_BABA_same_cyclic_orbit": same_orbit,
        "ABAB_reversal_is_a_rotation": reversal_is_rotation,
        "finding": "ABAB and BABA are rotations of one period-two cyclic word, not two cyclic classes.",
        "pass": bool(passed),
    }


def chart_count_circularity_gate(
    chart_bytes: bytes,
    static_analysis: dict[str, Any],
    count_gate: dict[str, Any],
) -> dict[str, Any]:
    slots = json.loads(chart_bytes.decode("utf-8"))
    steps_by_loop: dict[tuple[str, str], set[int]] = defaultdict(set)
    for slot in slots:
        steps_by_loop[(slot["engine"], slot["loop"])].add(int(slot["step"]))
    per_loop_counts = {
        f"{engine}/{loop}": len(steps)
        for (engine, loop), steps in sorted(steps_by_loop.items())
    }
    unique_counts = sorted(set(per_loop_counts.values()))
    chart_count = unique_counts[0] if len(unique_counts) == 1 else None
    c3_forced_length = count_gate["forced_length"]
    source_uses_equality_check = static_analysis["chart_count_compared_to_minimal"]
    chart_matches_forced_count = chart_count == c3_forced_length == 4
    circularity_caught = bool(
        source_uses_equality_check
        and count_gate["minimal_length_preselected_by_C3"]
        and chart_matches_forced_count
    )
    return {
        "chart_member": CHART_MEMBER,
        "slot_count": len(slots),
        "per_engine_loop_distinct_step_counts": per_loop_counts,
        "unique_substage_counts": unique_counts,
        "chart_substage_count": chart_count,
        "C3_forced_length": c3_forced_length,
        "chart_matches_C3_forced_length": chart_matches_forced_count,
        "source_ast": {
            "line": static_analysis["g_engine_match_line"],
            "expression": static_analysis["g_engine_match_expression"],
            "chart_count_compared_to_minimal": source_uses_equality_check,
        },
        "chart_count_is_independent_derivation": False,
        "chart_count_circularity_caught": circularity_caught,
        "finding": (
            "The chart already contains four steps per loop, while C3 already "
            "forces L=4; testing equality between those two fours is consistency, "
            "not an independent derivation of the architecture."
        ),
        "pass": circularity_caught,
    }


def main() -> dict[str, Any]:
    target = load_audit_target()
    static_analysis = source_static_analysis(target["source_text"])
    probes = probe_set()
    count_gate = count_constraint_gate(static_analysis)
    gates = {
        "source_lock": target["gate"],
        "actual_bloch_angle": bloch_angle_gate(),
        "adjoint_superoperator_commutator": superoperator_commutator_gate(),
        "unitary_entropy_changes": entropy_change_gate(probes),
        "C3_count_constraint_forces_length_4": count_gate,
        "control_truth_vectors": control_truth_vector_gate(probes),
        "ABAB_BABA_cyclic_orbit_count": cyclic_orbit_gate(),
        "chart_count_circularity": chart_count_circularity_gate(
            target["chart_bytes"], static_analysis, count_gate
        ),
    }
    all_pass = all(bool(gate["pass"]) for gate in gates.values())
    verdict = "UP130_OVERCLAIM_CAUGHT" if all_pass else "UP130_AUDIT_INCONCLUSIVE"
    own_source_sha256 = sha256_bytes(SOURCE_PATH.read_bytes())
    result = {
        "schema": "RATCHET_SCRATCH_DIAGNOSTIC_RESULT_v1",
        "sim_id": SIM_ID,
        "up_id": "UP-130",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "claim_ceiling": CLAIM_CEILING,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "source": {
            "audit_sim_path": str(SOURCE_PATH),
            "audit_sim_sha256": own_source_sha256,
            "package_path": str(PACKAGE_PATH),
            "target_member": UP130_SOURCE_MEMBER,
            "target_sha256": target["gate"]["actual_source_sha256"],
        },
        "runtime": {
            "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "python_executable": sys.executable,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy_version,
            "command": f"{sys.executable} {SOURCE_PATH}",
            "deterministic": True,
            "random_seed": 0,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "gates": gates,
        "fabrication_audit": {
            "found_fabrication": bool(all_pass),
            "found_overclaim": bool(all_pass),
            "finding_types": [
                "misidentified Bloch angle",
                "commuting adjoint channels presented as order-sensitive axes",
                "zero entropy change presented as an entropy-sector ratchet",
                "minimal length imposed by C3",
                "non-isolating controls",
                "duplicate cyclic representatives presented as two chiralities",
                "chart-count circularity",
            ],
            "target_claim_disposition": (
                "rejected for the exact source hash" if all_pass else "inconclusive"
            ),
        },
        "allowed_claims": [
            "The audited source executes a finite two-letter word construction.",
            "Its exp(-i*pi*sigma/2) legs induce 180-degree Bloch rotations.",
            "Its Ad_Z and Ad_X channels commute and preserve von Neumann entropy.",
            "Its C3 count predicate fixes length four before the scan.",
            "Its stated controls do not isolate their claimed gates.",
            "ABAB and BABA form one cyclic orbit.",
            "The parsed chart count is four but is not an independent derivation.",
        ],
        "rejected_claims": [
            "The source implements quarter-turn legs.",
            "The source demonstrates an order-sensitive dual ratchet.",
            "The source demonstrates entropy ratcheting.",
            "The source independently derives the count four.",
            "The controls each isolate the claimed gate.",
            "ABAB and BABA are two cyclic chiralities.",
            "Agreement with the four-step chart closes the architecture claim.",
        ],
        "policy_eval": {"UP130_OVERCLAIM_CAUGHT": bool(all_pass)},
        "verdict": verdict,
        "all_gates_pass": bool(all_pass),
    }
    RESULT_PATH.write_text(
        json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "sim_id": SIM_ID,
        "verdict": verdict,
        "all_gates_pass": all_pass,
        "source_hash_match": gates["source_lock"]["source_hash_match"],
        "actual_bloch_angle_degrees": gates["actual_bloch_angle"]["rows"]["A_about_Z"][
            "actual_bloch_angle_degrees"
        ],
        "Ad_Z_Ad_X_commutator_frobenius_norm": gates[
            "adjoint_superoperator_commutator"
        ]["Ad_Z_Ad_X_commutator_frobenius_norm"],
        "max_abs_entropy_change_nats": gates["unitary_entropy_changes"][
            "global_max_abs_delta_entropy_nats"
        ],
        "C3_allowed_lengths": gates["C3_count_constraint_forces_length_4"][
            "allowed_lengths_under_C3"
        ],
        "controls_isolate_claimed_gates": gates["control_truth_vectors"][
            "each_control_isolates_its_claimed_gate"
        ],
        "distinct_cyclic_orbit_count": gates["ABAB_BABA_cyclic_orbit_count"][
            "distinct_cyclic_orbit_count"
        ],
        "chart_count_is_independent_derivation": gates["chart_count_circularity"][
            "chart_count_is_independent_derivation"
        ],
        "result_path": str(RESULT_PATH),
    }
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    if not all_pass:
        raise SystemExit(1)
    return result


if __name__ == "__main__":
    main()
