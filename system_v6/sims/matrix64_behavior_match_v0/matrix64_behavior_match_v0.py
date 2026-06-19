#!/usr/bin/env python3
"""Behavioral quotient descent table for the pinned 64-stage realization."""

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


SIM_ID = "matrix64_behavior_match_v0"
SCHEMA_VERSION = "matrix64_behavior_match_result_v0"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "realization_relative_behavioral_symmetry_table_only"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT = RESULT_DIR / f"{SIM_ID}_results.json"

ICHING_SIM = "iching_symmetry_match_v0"
FINGERPRINT_SIM = "eng64_stage_fingerprint_ids_v0"

SOURCE_PATHS = {
    "iching_packet": ROOT / "system_v6/sims/iching_symmetry_match_v0/iching_symmetry_match_v0.py",
    "iching_result": ROOT / "system_v6/sims/iching_symmetry_match_v0/results/iching_symmetry_match_v0_results.json",
    "iching_audit": ROOT / "system_v6/sims/iching_symmetry_match_v0/audit_verdict.md",
    "fingerprint_packet": ROOT / "system_v6/sims/eng64_stage_fingerprint_ids_v0/eng64_stage_fingerprint_ids_v0.py",
    "fingerprint_result": ROOT
    / "system_v6/sims/eng64_stage_fingerprint_ids_v0/results/eng64_stage_fingerprint_ids_v0_results.json",
    "eng64_result": ROOT / "system_v5/julia_carrier/eng_64_hexagram_julia_results.json",
}

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


TOOL_MANIFEST = {
    "python_enumeration": {
        "used": True,
        "reason": "load-bearing: enumerates the 64-stage finite action, quotient descent rows, and descending subgroup",
    },
    "eng64_fingerprint_ids": {
        "used": True,
        "reason": "load-bearing: supplies stable label-free component IDs for the pinned realization quotient",
    },
    "hashlib": {
        "used": True,
        "reason": "supportive: pins source/result/audit inputs by sha256",
    },
    "json": {
        "used": True,
        "reason": "supportive: emits bounded packet and validator artifacts",
    },
    "builder_audit_boundary": {
        "used": True,
        "reason": "load-bearing: enforces G.2a builder/audit idempotency without hard audit absence",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "python_enumeration": "load_bearing",
    "eng64_fingerprint_ids": "load_bearing",
    "hashlib": "supportive",
    "json": "supportive",
    "builder_audit_boundary": "load_bearing",
}

LINE_TO_AXIS = {1: 6, 2: 5, 3: 3, 4: 4, 5: 1, 6: 2}


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bits(n: int, width: int = 6) -> list[int]:
    return [(n >> i) & 1 for i in range(width)]


def from_bits(values: list[int]) -> int:
    return sum((bit & 1) << idx for idx, bit in enumerate(values))


def bit_reverse_6(value: int) -> int:
    return from_bits(list(reversed(bits(value))))


def complement_6(value: int) -> int:
    return value ^ 0b111111


def phi_hex_to_engine(h: int) -> int:
    line_bits = bits(h)
    axis_bits = [line_bits[4], line_bits[5], line_bits[2], line_bits[3], line_bits[1], line_bits[0]]
    return from_bits(axis_bits)


def phi_engine_to_hex(e: int) -> int:
    axis_bits = bits(e)
    line_bits = [axis_bits[5], axis_bits[4], axis_bits[2], axis_bits[3], axis_bits[0], axis_bits[1]]
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
    return tuple(p[q[i]] for i in range(len(q)))


def closure_with_words(generators: dict[str, list[int]]) -> dict[tuple[int, ...], list[str]]:
    gens = {name: tuple(perm) for name, perm in generators.items()}
    identity = tuple(range(64))
    words: dict[tuple[int, ...], list[str]] = {identity: []}
    queue: deque[tuple[int, ...]] = deque([identity])
    while queue:
        cur = queue.popleft()
        for name, gen in gens.items():
            nxt = compose(gen, cur)
            if nxt not in words:
                words[nxt] = words[cur] + [name]
                queue.append(nxt)
    return words


def generator_surfaces() -> tuple[dict[str, list[int]], dict[str, list[int]], dict[str, str]]:
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
    return hex_generators, engine_generators, generator_map


def component_surfaces(fingerprint_result: dict[str, Any]) -> tuple[dict[int, str], dict[str, list[int]], dict[str, int]]:
    stage_to_component = {
        int(row["stage"]): str(row["component_id"])
        for row in fingerprint_result["stage_fingerprint_components"]
    }
    components = {
        str(row["component_id"]): [int(stage) for stage in row["stages"]]
        for row in fingerprint_result["components"]
    }
    representative = {component_id: min(stages) for component_id, stages in components.items()}
    return stage_to_component, components, representative


def descent_analysis(
    perm: list[int] | tuple[int, ...],
    stage_to_component: dict[int, str],
    components: dict[str, list[int]],
    representatives: dict[str, int],
) -> dict[str, Any]:
    component_action = []
    breaking_components = []
    pointwise_changed = []
    for component_id, stages in sorted(components.items(), key=lambda item: min(item[1])):
        image_rows = []
        image_components = set()
        for stage in stages:
            after_stage = int(perm[stage])
            after_component = stage_to_component[after_stage]
            image_components.add(after_component)
            if after_component != component_id:
                pointwise_changed.append(stage)
            image_rows.append(
                {
                    "stage": stage,
                    "after_stage": after_stage,
                    "after_component_id": after_component,
                    "after_component_representative_stage": representatives[after_component],
                }
            )
        sorted_images = sorted(image_components, key=lambda cid: representatives[cid])
        if len(sorted_images) == 1:
            component_action.append(
                {
                    "source_component_id": component_id,
                    "source_representative_stage": min(stages),
                    "target_component_id": sorted_images[0],
                    "target_representative_stage": representatives[sorted_images[0]],
                }
            )
        else:
            breaking_components.append(
                {
                    "source_component_id": component_id,
                    "source_stages": stages,
                    "image_component_ids": sorted_images,
                    "image_representative_stages": [representatives[cid] for cid in sorted_images],
                    "image_rows": image_rows,
                }
            )
    descends = not breaking_components
    return {
        "descends": descends,
        "status": "descends_component_action" if descends else "breaks_quotient",
        "pointwise_preserves_components": not pointwise_changed,
        "pointwise_changed_stage_count": len(set(pointwise_changed)),
        "component_action": component_action if descends else [],
        "component_action_sample": component_action[:8] if descends else [],
        "breaking_component_count": len(breaking_components),
        "breaking_components": breaking_components,
        "breaking_components_sample": breaking_components[:4],
    }


def affine_descriptor(perm: tuple[int, ...]) -> dict[str, Any]:
    translation = perm[0]
    basis_images = [perm[1 << idx] ^ translation for idx in range(6)]
    pure_coordinate = all(image != 0 and image & (image - 1) == 0 for image in basis_images)
    descriptor: dict[str, Any] = {
        "translation_mask": translation,
        "translation_axes": [f"Axis{idx + 1}" for idx, bit in enumerate(bits(translation)) if bit],
        "linear_basis_images": basis_images,
        "pure_coordinate_permutation": pure_coordinate,
    }
    if pure_coordinate:
        descriptor["linear_axis_map"] = {
            f"Axis{idx + 1}": f"Axis{basis_images[idx].bit_length()}"
            for idx in range(6)
        }
    return descriptor


def quotient_signature(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        row["generator"]: {
            "descends": row["descends"],
            "breaks": row["breaking_component_count"],
            "pointwise_changed_stage_count": row["pointwise_changed_stage_count"],
        }
        for row in rows
    }


def randomized_component_assignment(
    stage_to_component: dict[int, str],
    components: dict[str, list[int]],
    seed: int,
) -> tuple[dict[int, str], dict[str, list[int]], dict[str, int]]:
    labels = [stage_to_component[stage] for stage in range(64)]
    rng = random.Random(seed)
    rng.shuffle(labels)
    random_stage_to_component = {stage: labels[stage] for stage in range(64)}
    random_components: dict[str, list[int]] = {component_id: [] for component_id in components}
    for stage, component_id in random_stage_to_component.items():
        random_components[component_id].append(stage)
    random_representatives = {component_id: min(stages) for component_id, stages in random_components.items()}
    return random_stage_to_component, random_components, random_representatives


def coarsened_component_assignment(
    stage_to_component: dict[int, str],
    components: dict[str, list[int]],
) -> tuple[dict[int, str], dict[str, list[int]], dict[str, int], list[str]]:
    ordered_ids = [component_id for component_id, _ in sorted(components.items(), key=lambda item: min(item[1]))]
    merge_ids = ordered_ids[4:6]
    merged_id = "coarsened_merge_" + "_".join(str(min(components[cid])) for cid in merge_ids)
    coarsened_stage_to_component = {
        stage: merged_id if component_id in merge_ids else component_id
        for stage, component_id in stage_to_component.items()
    }
    coarsened_components: dict[str, list[int]] = {}
    for stage, component_id in coarsened_stage_to_component.items():
        coarsened_components.setdefault(component_id, []).append(stage)
    coarsened_representatives = {component_id: min(stages) for component_id, stages in coarsened_components.items()}
    return coarsened_stage_to_component, coarsened_components, coarsened_representatives, merge_ids


def build_generator_rows(
    engine_generators: dict[str, list[int]],
    generator_map: dict[str, str],
    stage_to_component: dict[int, str],
    components: dict[str, list[int]],
    representatives: dict[str, int],
) -> list[dict[str, Any]]:
    rows = []
    for generator in [
        "flip_line_1",
        "flip_line_2",
        "flip_line_3",
        "flip_line_4",
        "flip_line_5",
        "flip_line_6",
        "complement",
        "vertical_rotation",
        "trigram_swap",
    ]:
        engine_generator = generator_map[generator]
        analysis = descent_analysis(engine_generators[engine_generator], stage_to_component, components, representatives)
        rows.append(
            {
                "generator": generator,
                "engine_generator": engine_generator,
                "criterion": "for every source component, all member stages map into one target component",
                **analysis,
            }
        )
    return rows


def build() -> dict[str, Any]:
    fingerprint_result = load_json(SOURCE_PATHS["fingerprint_result"])
    eng64_result = load_json(SOURCE_PATHS["eng64_result"])
    iching_result = load_json(SOURCE_PATHS["iching_result"])
    stage_to_component, components, representatives = component_surfaces(fingerprint_result)
    _, engine_generators, generator_map = generator_surfaces()
    address_generators_on_realization = {
        name: engine_generators[generator_map[name]]
        for name in generator_map
    }
    generator_rows = build_generator_rows(
        engine_generators,
        generator_map,
        stage_to_component,
        components,
        representatives,
    )
    generator_descends = {row["generator"]: bool(row["descends"]) for row in generator_rows}
    pointwise_preserves = {row["generator"]: bool(row["pointwise_preserves_components"]) for row in generator_rows}

    group_words = closure_with_words(address_generators_on_realization)
    descending_elements = []
    for perm, word in sorted(group_words.items(), key=lambda item: (len(item[1]), item[1], item[0])):
        analysis = descent_analysis(perm, stage_to_component, components, representatives)
        if analysis["descends"]:
            descriptor = affine_descriptor(perm)
            descending_elements.append(
                {
                    "word": word or ["identity"],
                    "translation_mask": descriptor["translation_mask"],
                    "translation_axes": descriptor["translation_axes"],
                    "linear_basis_images": descriptor["linear_basis_images"],
                    "pure_coordinate_permutation": descriptor["pure_coordinate_permutation"],
                }
            )

    identity_perm = tuple(range(64))
    identity_analysis = descent_analysis(identity_perm, stage_to_component, components, representatives)

    random_stage_to_component, random_components, random_representatives = randomized_component_assignment(
        stage_to_component, components, seed=20260612
    )
    random_rows = build_generator_rows(
        engine_generators,
        generator_map,
        random_stage_to_component,
        random_components,
        random_representatives,
    )
    random_non_identity_descending_count = sum(
        1 for row in random_rows if row["generator"] != "identity" and row["descends"]
    )

    coarsened_stage_to_component, coarsened_components, coarsened_representatives, merge_ids = (
        coarsened_component_assignment(stage_to_component, components)
    )
    coarsened_rows = build_generator_rows(
        engine_generators,
        generator_map,
        coarsened_stage_to_component,
        coarsened_components,
        coarsened_representatives,
    )
    base_signature = quotient_signature(generator_rows)
    coarsened_signature = quotient_signature(coarsened_rows)

    old_audit_expected = {
        "flip_line_1": {"pointwise_changed_stage_count": 64, "old_audit_status": "homomorphism_only"},
        "flip_line_2": {"pointwise_changed_stage_count": 64, "old_audit_status": "homomorphism_only"},
        "flip_line_3": {"pointwise_changed_stage_count": 64, "old_audit_status": "homomorphism_only"},
        "flip_line_4": {"pointwise_changed_stage_count": 64, "old_audit_status": "homomorphism_only"},
        "flip_line_5": {"pointwise_changed_stage_count": 0, "old_audit_status": "quotient_symmetry"},
        "flip_line_6": {"pointwise_changed_stage_count": 0, "old_audit_status": "quotient_symmetry"},
        "complement": {"pointwise_changed_stage_count": 64, "old_audit_status": "homomorphism_only"},
        "vertical_rotation": {"pointwise_changed_stage_count": 56, "old_audit_status": "homomorphism_only"},
        "trigram_swap": {"pointwise_changed_stage_count": 56, "old_audit_status": "homomorphism_only"},
    }
    audit_check_rows = [
        {
            "generator": row["generator"],
            "old_audit_status": old_audit_expected[row["generator"]]["old_audit_status"],
            "old_audit_pointwise_changed_count_expected": old_audit_expected[row["generator"]][
                "pointwise_changed_stage_count"
            ],
            "pointwise_changed_count_recomputed": row["pointwise_changed_stage_count"],
            "pointwise_check_matches_audit": row["pointwise_changed_stage_count"]
            == old_audit_expected[row["generator"]]["pointwise_changed_stage_count"],
            "new_descent_status": row["status"],
        }
        for row in generator_rows
    ]

    descending_generator_names = [row["generator"] for row in generator_rows if row["descends"]]
    all_pass = (
        fingerprint_result.get("all_pass") is True
        and fingerprint_result.get("summary", {}).get("n_distinct_fresh_fingerprints") == 16
        and eng64_result.get("fingerprint_counts", {}).get("n_distinct") == 16
        and iching_result.get("group_check", {}).get("hex_group_size") == 256
        and len(group_words) == 256
        and len(descending_elements) == 64
        and len(descending_elements) < len(group_words)
        and all(generator_descends[name] for name in [f"flip_line_{line}" for line in range(1, 7)])
        and generator_descends["complement"]
        and not generator_descends["vertical_rotation"]
        and not generator_descends["trigram_swap"]
        and pointwise_preserves["flip_line_5"]
        and pointwise_preserves["flip_line_6"]
        and all(row["pointwise_check_matches_audit"] for row in audit_check_rows)
        and identity_analysis["descends"]
        and not all(row["descends"] for row in random_rows)
        and random_non_identity_descending_count < len(random_rows)
        and base_signature != coarsened_signature
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
            "iching_audit": rel(SOURCE_PATHS["iching_audit"]),
            "user_supplied_iching_audit_hash_hint": "2b32714a0",
            "fingerprint_ids_packet": rel(SOURCE_PATHS["fingerprint_result"]),
            "user_supplied_fingerprint_ids_hash_hint": "fab7b2253",
            "audited_64_run": rel(SOURCE_PATHS["eng64_result"]),
            "user_supplied_audited_64_run_hash_hint": "23cfa5536",
            "named_next": "separate Matrix64 behavior packet after fingerprint IDs exist",
        },
        "source_locks": {
            "iching_packet": source_lock(SOURCE_PATHS["iching_packet"], "address-level group/action packet", "2b32714a0"),
            "iching_result": source_lock(SOURCE_PATHS["iching_result"], "address-level group/action result", "2b32714a0"),
            "iching_audit": source_lock(SOURCE_PATHS["iching_audit"], "authority audit", "2b32714a0"),
            "fingerprint_packet": source_lock(
                SOURCE_PATHS["fingerprint_packet"], "stable label-free component ID packet", "fab7b2253"
            ),
            "fingerprint_result": source_lock(
                SOURCE_PATHS["fingerprint_result"], "stable label-free component ID result", "fab7b2253"
            ),
            "eng64_result": source_lock(SOURCE_PATHS["eng64_result"], "audited pinned 64-run", "23cfa5536"),
        },
        "objects": {
            "pinned_realization": "eng_64 committed 64-stage density-channel realization",
            "stage_count": 64,
            "component_count": len(components),
            "component_size_histogram": {
                str(size): count
                for size, count in sorted(Counter(len(stages) for stages in components.values()).items())
            },
        },
        "quotient_definition": {
            "source": rel(SOURCE_PATHS["fingerprint_result"]),
            "component_id_source": "stage_fingerprint_components[*].component_id",
            "well_defined_descent_criterion": (
                "for every component C, the set {component_id(g(stage)) for stage in C} has cardinality 1"
            ),
            "realization_relative": True,
            "matrix64_general_claim": False,
        },
        "generator_descent_rows": generator_rows,
        "audit_check_rows": audit_check_rows,
        "subgroup": {
            "full_address_group_size": len(group_words),
            "descending_subgroup_size": len(descending_elements),
            "proper_subgroup": len(descending_elements) < len(group_words),
            "descending_named_generators": descending_generator_names,
            "minimal_observed_generators": [f"flip_line_{line}" for line in range(1, 7)],
            "structural_description": (
                "all 64 address translations descend on the pinned 16-component quotient; "
                "the reversal/trigram V4 coordinate-permutation part does not descend"
            ),
            "descending_elements": descending_elements,
        },
        "summary": {
            "descends": {row["generator"]: row["descends"] for row in generator_rows},
            "pointwise_preserves_components": pointwise_preserves,
            "breaking_generators": [row["generator"] for row in generator_rows if not row["descends"]],
            "descending_subgroup_size": len(descending_elements),
            "full_address_group_size": len(group_words),
            "proper_subgroup_descends": len(descending_elements) < len(group_words),
            "result": "proper_subgroup_descends",
        },
        "controls": {
            "identity_descends_trivially": {
                "descends": identity_analysis["descends"],
                "pointwise_preserves_components": identity_analysis["pointwise_preserves_components"],
                "breaking_component_count": identity_analysis["breaking_component_count"],
            },
            "random_stage_to_component_relabeling": {
                "seed": 20260612,
                "control": "shuffle the 64 stage-to-component labels while preserving the 16x4 label multiset",
                "breaks_descent_table": not all(row["descends"] for row in random_rows),
                "non_identity_descending_generator_count": random_non_identity_descending_count,
                "rows": [
                    {
                        "generator": row["generator"],
                        "descends": row["descends"],
                        "breaking_component_count": row["breaking_component_count"],
                    }
                    for row in random_rows
                ],
            },
            "deliberately_coarsened_quotient": {
                "merged_component_ids": merge_ids,
                "original_component_count": len(components),
                "coarsened_component_count": len(coarsened_components),
                "descent_table_changed": base_signature != coarsened_signature,
                "coarsened_rows": [
                    {
                        "generator": row["generator"],
                        "descends": row["descends"],
                        "breaking_component_count": row["breaking_component_count"],
                        "pointwise_changed_stage_count": row["pointwise_changed_stage_count"],
                    }
                    for row in coarsened_rows
                ],
            },
        },
        "claim_boundary": {
            "scratch_diagnostic": True,
            "realization_relative_behavioral_symmetry_table_only": True,
            "pinned_realization_only": True,
            "does_not_claim_matrix64_general": True,
            "does_not_claim_64_behavior_iso": True,
            "does_not_claim_matrix64_completion": True,
            "king_wen_comparator_only": True,
            "does_not_promote_eng_64": True,
            "not_qit_admission": True,
            "not_physics_admission": True,
            "not_bridge_or_axis_closure": True,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": {
            "file_disjoint_packet": True,
            "boundary_helper_path": "scripts/builder_audit_boundary.py",
            "boundary_helper_fully_used": True,
            "g2a_boundary_helper_from_birth": True,
            "no_hard_audit_absence_assertion": True,
            "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "builder_self_assessment_expected": rel(SIM_DIR / "builder_self_assessment.md"),
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build()
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": payload["all_pass"],
                "result": rel(RESULT),
                "descending_subgroup_size": payload["summary"]["descending_subgroup_size"],
                "full_address_group_size": payload["summary"]["full_address_group_size"],
                "breaking_generators": payload["summary"]["breaking_generators"],
            },
            sort_keys=True,
        )
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
