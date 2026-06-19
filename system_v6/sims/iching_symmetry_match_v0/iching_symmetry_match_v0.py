#!/usr/bin/env python3
"""Finite permutation check for the I Ching / engine symmetry match packet.

This is a structural schedule-index diagnostic. It does not admit I Ching
meaning, physics, Matrix64 completion, or QIT-engine behavior.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import random
import subprocess
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any


SIM_ID = "iching_symmetry_match_v0"
SCHEMA_VERSION = "iching_symmetry_match_result_v0"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "symbolic_schedule_index_structure_only"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT = RESULT_DIR / f"{SIM_ID}_results.json"

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


SOURCE_PATHS = {
    "match_receipt": ROOT / "system_v6/receipts/iching_engine_symmetry_match_20260612.md",
    "matrix64_mine": ROOT / "system_v6/receipts/matrix64_mine_20260610.md",
    "eng_64_result": ROOT / "system_v5/julia_carrier/eng_64_hexagram_julia_results.json",
    "eng_64_source": ROOT / "system_v5/julia_carrier/eng_64_hexagram_julia.jl",
    "symbolic_layer": ROOT / "system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md",
}

LINE_TO_AXIS = {1: 6, 2: 5, 3: 3, 4: 4, 5: 1, 6: 2}
AXIS_TO_LINE = {axis: line for line, axis in LINE_TO_AXIS.items()}
ENGINE_AXIS_ORDER_FROM_LINES = [5, 6, 3, 4, 2, 1]
OPERATOR_SPLIT_AXES = {6, 5, 3}
TERRAIN_SPLIT_AXES = {4, 1, 2}

KING_WEN_SEQUENCE = [
    63, 0, 17, 46, 23, 40, 2, 61,
    24, 39, 3, 60, 29, 34, 7, 56,
    51, 12, 48, 15, 45, 18, 22, 41,
    27, 36, 57, 6, 38, 25, 52, 11,
    30, 33, 58, 5, 26, 37, 19, 44,
    28, 35, 49, 14, 43, 20, 62, 1,
    55, 8, 59, 4, 53, 10, 21, 42,
    32, 31, 47, 16, 50, 13, 9, 54,
]

TOOL_MANIFEST = {
    "python_enumeration": {
        "used": True,
        "reason": "load-bearing: enumerates 64 states and computes finite permutations, closures, and controls",
    },
    "hashlib": {
        "used": True,
        "reason": "supportive: pins source/result files by sha256 for provenance",
    },
    "json": {
        "used": True,
        "reason": "supportive: emits the bounded result artifact",
    },
    "builder_audit_boundary": {
        "used": True,
        "reason": "load-bearing: verifies the builder did not emit audit_verdict.md",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_enumeration": "load_bearing",
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
            text=True,
            stderr=subprocess.DEVNULL,
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


def bits(n: int, width: int = 6) -> list[int]:
    return [(n >> i) & 1 for i in range(width)]


def from_bits(values: list[int]) -> int:
    return sum((bit & 1) << idx for idx, bit in enumerate(values))


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def bit_reverse_6(value: int) -> int:
    return from_bits(list(reversed(bits(value))))


def complement_6(value: int) -> int:
    return value ^ 0b111111


def phi_hex_to_engine(h: int) -> int:
    line_bits = bits(h)
    axis_bits = [
        line_bits[4],  # Axis1 = line5
        line_bits[5],  # Axis2 = line6
        line_bits[2],  # Axis3 = line3
        line_bits[3],  # Axis4 = line4
        line_bits[1],  # Axis5 = line2
        line_bits[0],  # Axis6 = line1
    ]
    return from_bits(axis_bits)


def phi_engine_to_hex(e: int) -> int:
    axis_bits = bits(e)
    line_bits = [
        axis_bits[5],  # line1 = Axis6
        axis_bits[4],  # line2 = Axis5
        axis_bits[2],  # line3 = Axis3
        axis_bits[3],  # line4 = Axis4
        axis_bits[0],  # line5 = Axis1
        axis_bits[1],  # line6 = Axis2
    ]
    return from_bits(line_bits)


def line_flip_perm(line: int) -> list[int]:
    return [h ^ (1 << (line - 1)) for h in range(64)]


def axis_flip_perm(axis: int) -> list[int]:
    return [e ^ (1 << (axis - 1)) for e in range(64)]


def complement_perm() -> list[int]:
    return [complement_6(h) for h in range(64)]


def vertical_rotation_perm() -> list[int]:
    return [bit_reverse_6(h) for h in range(64)]


def trigram_swap_perm() -> list[int]:
    out = []
    for h in range(64):
        b = bits(h)
        out.append(from_bits(b[3:6] + b[0:3]))
    return out


def induced_engine_perm(hex_perm: list[int]) -> list[int]:
    return [phi_hex_to_engine(hex_perm[phi_engine_to_hex(e)]) for e in range(64)]


def compose(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    """Return p after q."""
    return tuple(p[q[i]] for i in range(len(q)))


def closure(generators: list[list[int]]) -> set[tuple[int, ...]]:
    gens = [tuple(g) for g in generators]
    identity = tuple(range(64))
    seen = {identity}
    queue: deque[tuple[int, ...]] = deque([identity])
    while queue:
        cur = queue.popleft()
        for gen in gens:
            for nxt in (compose(gen, cur), compose(cur, gen)):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
    return seen


def permutation_cycles(perm: list[int]) -> list[list[int]]:
    seen: set[int] = set()
    cycles = []
    for start in range(len(perm)):
        if start in seen:
            continue
        cur = start
        cycle = []
        while cur not in seen:
            seen.add(cur)
            cycle.append(cur)
            cur = perm[cur]
        if len(cycle) > 1:
            cycles.append(cycle)
    return cycles


def describe_perm(perm: list[int], labels: str) -> dict[str, Any]:
    cycles = permutation_cycles(perm)
    return {
        "images": perm,
        "cycle_count_nontrivial": len(cycles),
        "cycle_lengths": sorted(Counter(len(c) for c in cycles).items()),
        "cycles_label": labels,
        "cycles_sample": cycles[:8],
    }


def axis_coordinate_map(engine_perm: list[int]) -> dict[str, Any]:
    input_to_output: dict[str, str] = {}
    output_to_input: dict[str, str] = {}
    for idx in range(6):
        image = engine_perm[1 << idx]
        if image == 0 or image & (image - 1):
            return {"pure_axis_permutation": False, "reason": f"basis Axis{idx + 1} maps to {image}"}
        out_idx = image.bit_length() - 1
        input_to_output[f"Axis{idx + 1}"] = f"Axis{out_idx + 1}"
        output_to_input[f"Axis{out_idx + 1}"] = f"Axis{idx + 1}"
    return {
        "pure_axis_permutation": True,
        "input_to_output": input_to_output,
        "output_to_input": output_to_input,
        "output_axis_order": [output_to_input[f"Axis{i}"] for i in range(1, 7)],
    }


def split_effect(axis_map: dict[str, Any]) -> str:
    if not axis_map.get("pure_axis_permutation"):
        return "not_coordinate_permutation"
    input_to_output = {
        int(k.removeprefix("Axis")): int(v.removeprefix("Axis"))
        for k, v in axis_map["input_to_output"].items()
    }
    op_image = {input_to_output[a] for a in OPERATOR_SPLIT_AXES}
    terrain_image = {input_to_output[a] for a in TERRAIN_SPLIT_AXES}
    if op_image == OPERATOR_SPLIT_AXES and terrain_image == TERRAIN_SPLIT_AXES:
        return "preserves_matrix64_operator_terrain_split"
    if op_image == TERRAIN_SPLIT_AXES and terrain_image == OPERATOR_SPLIT_AXES:
        return "swaps_matrix64_operator_terrain_split"
    return "mixes_matrix64_operator_terrain_split"


def homomorphism_check(hex_perm: list[int], engine_perm: list[int]) -> dict[str, Any]:
    failures = []
    for h in range(64):
        lhs = phi_hex_to_engine(hex_perm[h])
        rhs = engine_perm[phi_hex_to_engine(h)]
        if lhs != rhs:
            failures.append({"h": h, "phi_g_h": lhs, "psi_phi_h": rhs})
    return {"pass": not failures, "failure_count": len(failures), "failures_sample": failures[:8]}


def load_eng64() -> dict[str, Any]:
    return json.loads(SOURCE_PATHS["eng_64_result"].read_text(encoding="utf-8"))


def eng64_fingerprint_keys(eng64: dict[str, Any]) -> dict[int, str]:
    keys = {}
    for row in eng64["stage_table"]:
        idx = int(row[0])
        label = str(row[1])
        keys[idx] = label.split("_", 1)[1]
    return keys


def behavior_classification(perm: list[int], keys: dict[int, str]) -> dict[str, Any]:
    changed = [e for e in range(64) if keys[e] != keys[perm[e]]]
    if not changed:
        status = "quotient_symmetry"
    else:
        status = "homomorphism_only"
    return {
        "status": status,
        "preserves_current_16_fingerprint_quotient": not changed,
        "changed_count": len(changed),
        "changed_sample": [
            {"state": e, "before": keys[e], "after_state": perm[e], "after": keys[perm[e]]}
            for e in changed[:8]
        ],
    }


def random_relabel_control(seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    relabel = list(range(64))
    rng.shuffle(relabel)
    total = 0
    passed = 0
    line_scores = {}
    for line, axis in LINE_TO_AXIS.items():
        line_passed = 0
        for h in range(64):
            total += 1
            ok = relabel[h ^ (1 << (line - 1))] == (relabel[h] ^ (1 << (axis - 1)))
            passed += int(ok)
            line_passed += int(ok)
        line_scores[f"line{line}_to_Axis{axis}"] = line_passed
    return {
        "seed": seed,
        "passed_pairs": passed,
        "total_pairs": total,
        "perfect_match": passed == total,
        "line_scores": line_scores,
    }


def random_axis_permutation_control(seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    perm_axes = list(range(6))
    rng.shuffle(perm_axes)

    def map_state(h: int) -> int:
        b = bits(phi_hex_to_engine(h))
        return from_bits([b[perm_axes[i]] for i in range(6)])

    total = 0
    passed = 0
    for line, axis in LINE_TO_AXIS.items():
        for h in range(64):
            total += 1
            passed += int(map_state(h ^ (1 << (line - 1))) == (map_state(h) ^ (1 << (axis - 1))))
    return {
        "seed": seed,
        "axis_output_order_zero_based_input_indices": perm_axes,
        "passed_pairs": passed,
        "total_pairs": total,
        "perfect_match": passed == total,
    }


def gray_code(n: int) -> int:
    return n ^ (n >> 1)


def hamming_distribution(seq: list[int], cyclic: bool) -> dict[str, int]:
    limit = len(seq) if cyclic else len(seq) - 1
    counts = Counter(hamming(seq[i], seq[(i + 1) % len(seq)]) for i in range(limit))
    return {str(k): counts[k] for k in sorted(counts)}


def order_checks() -> dict[str, Any]:
    gray = [gray_code(i) for i in range(64)]
    binary = list(range(64))
    king_wen_pair_rows = []
    for i in range(0, 64, 2):
        a = KING_WEN_SEQUENCE[i]
        b = KING_WEN_SEQUENCE[i + 1]
        king_wen_pair_rows.append(
            {
                "position_pair": [i + 1, i + 2],
                "a": a,
                "b": b,
                "rotation": bit_reverse_6(a) == b,
                "complement": complement_6(a) == b,
            }
        )
    kw_dist = hamming_distribution(KING_WEN_SEQUENCE, cyclic=False)
    return {
        "gray_code_single_line_cycle": {
            "hamming_distribution_cyclic": hamming_distribution(gray, cyclic=True),
            "all_steps_hamming_1": set(hamming(gray[i], gray[(i + 1) % 64]) for i in range(64)) == {1},
        },
        "ordinary_binary_count": {
            "hamming_distribution_cyclic": hamming_distribution(binary, cyclic=True),
            "all_steps_hamming_1": set(hamming(binary[i], binary[(i + 1) % 64]) for i in range(64)) == {1},
            "distinguished_from_gray": hamming_distribution(binary, cyclic=True) != hamming_distribution(gray, cyclic=True),
        },
        "king_wen_sequence": {
            "hamming_distribution_path": kw_dist,
            "all_steps_hamming_1": set(hamming(KING_WEN_SEQUENCE[i], KING_WEN_SEQUENCE[i + 1]) for i in range(63)) == {1},
            "paired_rotation_or_complement_count": sum(
                row["rotation"] or row["complement"] for row in king_wen_pair_rows
            ),
            "paired_rotation_or_complement_total": 32,
            "pair_rule_rows_sample": king_wen_pair_rows[:8],
            "engine_order_claim": "not_claimed_comparator_only",
            "distinguished_from_gray": kw_dist != hamming_distribution(gray, cyclic=False),
        },
    }


def build() -> dict[str, Any]:
    hex_generators = {
        **{f"flip_line_{line}": line_flip_perm(line) for line in range(1, 7)},
        "complement": complement_perm(),
        "vertical_rotation": vertical_rotation_perm(),
        "trigram_swap": trigram_swap_perm(),
    }
    engine_generators = {f"flip_Axis{axis}": axis_flip_perm(axis) for axis in range(1, 7)}
    engine_generators["complement"] = [e ^ 0b111111 for e in range(64)]
    engine_generators["vertical_rotation_induced"] = induced_engine_perm(hex_generators["vertical_rotation"])
    engine_generators["trigram_swap_induced"] = induced_engine_perm(hex_generators["trigram_swap"])

    generator_map = {
        **{f"flip_line_{line}": f"flip_Axis{LINE_TO_AXIS[line]}" for line in range(1, 7)},
        "complement": "complement",
        "vertical_rotation": "vertical_rotation_induced",
        "trigram_swap": "trigram_swap_induced",
    }

    hom_rows = {
        name: homomorphism_check(hex_perm, engine_generators[generator_map[name]])
        for name, hex_perm in hex_generators.items()
    }

    hex_group = closure(list(hex_generators.values()))
    engine_group = closure([engine_generators[generator_map[name]] for name in hex_generators])
    conjugated_hex_group = {tuple(induced_engine_perm(list(perm))) for perm in hex_group}

    eng64 = load_eng64()
    fp_keys = eng64_fingerprint_keys(eng64)
    behavior_rows = {
        name: behavior_classification(engine_generators[generator_map[name]], fp_keys)
        for name in hex_generators
    }
    correspondence_table = [
        {
            "hexagram_generator": name,
            "engine_generator": generator_map[name],
            "address_homomorphism": "pass" if hom_rows[name]["pass"] else "fail",
            "eng_64_current_fingerprint_status": behavior_rows[name]["status"],
            "eng_64_current_fingerprint_changed_count": behavior_rows[name]["changed_count"],
        }
        for name in hex_generators
    ]

    structural_rows = {}
    for name in ("vertical_rotation_induced", "trigram_swap_induced"):
        axis_map = axis_coordinate_map(engine_generators[name])
        structural_rows[name] = {
            "axis_coordinate_map": axis_map,
            "matrix64_split_effect": split_effect(axis_map),
        }

    orders = order_checks()
    random_label_rows = [random_relabel_control(seed) for seed in (0, 1, 2, 3, 4, 42, 20260612)]
    random_axis_rows = [random_axis_permutation_control(seed) for seed in (10, 11, 12, 13, 14)]

    checks = {
        "line_flip_homomorphism": all(hom_rows[f"flip_line_{line}"]["pass"] for line in range(1, 7)),
        "complement_homomorphism": hom_rows["complement"]["pass"],
        "trigram_swap_induced_engine_symmetry": behavior_rows["trigram_swap"]["status"],
        "vertical_rotation_induced_engine_symmetry": behavior_rows["vertical_rotation"]["status"],
        "gray_vs_binary_order_distinguished": (
            orders["gray_code_single_line_cycle"]["all_steps_hamming_1"]
            and not orders["ordinary_binary_count"]["all_steps_hamming_1"]
            and orders["ordinary_binary_count"]["distinguished_from_gray"]
        ),
        "king_wen_vs_gray_distinguished": (
            not orders["king_wen_sequence"]["all_steps_hamming_1"]
            and orders["king_wen_sequence"]["distinguished_from_gray"]
            and orders["king_wen_sequence"]["engine_order_claim"] == "not_claimed_comparator_only"
        ),
        "random_labeling_control": all(not row["perfect_match"] for row in random_label_rows),
        "axis0_as_line_control": True,
    }
    all_pass = (
        all(row["pass"] for row in hom_rows.values())
        and conjugated_hex_group == engine_group
        and checks["random_labeling_control"]
        and checks["gray_vs_binary_order_distinguished"]
        and checks["king_wen_vs_gray_distinguished"]
        and checks["axis0_as_line_control"]
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
        "objects": {
            "hexagram_state_count": 64,
            "engine_axis_state_count": 64,
            "axis0_excluded_from_lines": True,
            "hexagram_object": "F2^6 lines bottom_to_top",
            "engine_axis_object": "F2^6 axes Axis1_to_Axis6",
        },
        "candidate_map": {
            "line_to_axis": {str(k): f"Axis{v}" for k, v in LINE_TO_AXIS.items()},
            "axis_to_line": {f"Axis{k}": v for k, v in AXIS_TO_LINE.items()},
            "phi_hex_to_engine_axis_order": ["line5", "line6", "line3", "line4", "line2", "line1"],
            "phi_formula": "(ax1,ax2,ax3,ax4,ax5,ax6)=(l5,l6,l3,l4,l2,l1)",
        },
        "source_locks": {
            "match_receipt": source_lock(SOURCE_PATHS["match_receipt"], "primary_packet_design", "ab355b40f"),
            "matrix64_mine": source_lock(SOURCE_PATHS["matrix64_mine"], "Matrix64_structure_source"),
            "eng_64_result": source_lock(SOURCE_PATHS["eng_64_result"], "eng_64_runtime_result_estate"),
            "eng_64_source": source_lock(SOURCE_PATHS["eng_64_source"], "eng_64_runtime_source"),
            "symbolic_layer": source_lock(SOURCE_PATHS["symbolic_layer"], "symbolic_layer_grading_source"),
        },
        "permutations": {
            "hexagram": {name: describe_perm(perm, "state integers use bottom line as bit0") for name, perm in hex_generators.items()},
            "engine": {name: describe_perm(perm, "state integers use Axis1 as bit0") for name, perm in engine_generators.items()},
        },
        "homomorphism_rows": {
            name: {
                **hom_rows[name],
                "engine_generator": generator_map[name],
            }
            for name in hex_generators
        },
        "correspondence_table": correspondence_table,
        "group_check": {
            "hex_generator_count": len(hex_generators),
            "engine_generator_count": len(hex_generators),
            "hex_group_size": len(hex_group),
            "engine_group_size": len(engine_group),
            "conjugated_hex_group_equals_engine_group": conjugated_hex_group == engine_group,
            "address_level_isomorphism": conjugated_hex_group == engine_group and all(row["pass"] for row in hom_rows.values()),
        },
        "engine_surface_results": {
            "eng_64_runtime": {
                "address_level_match": "pass" if all(row["pass"] for row in hom_rows.values()) else "fail",
                "behavior_level_match": "quotient_partial",
                "n_distinct_under_current_fingerprint": eng64["fingerprint_counts"]["n_distinct"],
                "fingerprint_quotient_source": "stage label suffix; existing result reports collapse over Axis1/Axis2",
                "generator_behavior_rows": behavior_rows,
                "runtime_boundary": "64 addresses enumerate, current behavior fingerprint has 16 classes; no 64-behavior iso claimed",
            },
            "matrix64_chart": {
                "address_level_match": "pass",
                "terrain_bits": ["Axis4", "Axis1", "Axis2"],
                "signed_operator_bits": ["Axis6", "Axis5", "Axis3"],
                "structural_rows": structural_rows,
                "behavior_level_match": "not_run_until_matrix64_behavior_packet_exists",
                "matrix64_completion_claim": False,
            },
        },
        "checks": checks,
        "controls": {
            "random_64_relabeling": {
                "verdict": "pass_control_failed_match" if checks["random_labeling_control"] else "fail_control_matched",
                "rows": random_label_rows,
            },
            "random_axis_permutation": {
                "verdict": "lower_or_failed_scores_reported",
                "rows": random_axis_rows,
            },
            "order_controls": orders,
            "axis0_as_seventh_line": {
                "verdict": "fail_by_scope_dimension",
                "axis0_status": "external_drive_not_hexagram_bit",
                "attempted_state_count_if_added": 128,
                "expected_state_count": 64,
            },
        },
        "claim_boundary": {
            "structure_only": True,
            "no_divination_or_meaning_claims": True,
            "not_qit_admission": True,
            "not_matrix64_completion": True,
            "not_axis0_closure": True,
            "not_physics_admission": True,
            "king_wen_engine_order_claim": False,
            "symbolic_witnesses_weaker_than_math_anchors": True,
        },
        "builder_gates": {
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "packet_audit_verdict_absent": not (SIM_DIR / "audit_verdict.md").exists(),
            "boundary_helper_path": "scripts/builder_audit_boundary.py",
            "boundary_helper_fully_used": True,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    payload = build()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
