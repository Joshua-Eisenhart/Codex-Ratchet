#!/usr/bin/env python3
"""Source-pinned Type-1 engine v0 metadata.

This file intentionally contains only shared spec/annotation data and no
substrate result reads. Numeric engines reimplement the math independently.
"""

from __future__ import annotations

from copy import deepcopy


SIM_ID = "type1_engine_v0"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "QUARANTINE_EXPLORATORY"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

SOURCE_EXTRACTION = "../TYPE1_ENGINE_EXTRACTION_20260703.md"

SOURCE_CITES = {
    "terrain_type1": ["IGT:482-489", "ATLAS:82-85", "ATLAS:103-110", "ATLAS:135-141"],
    "operators": ["IGT:471-479", "SIGNED:136-557"],
    "stages": ["IGT:529-534", "ATLAS:217-231"],
    "traversals": ["IGT:464-469", "IGT:517-525", "ATLAS:156-179"],
    "open_gaps": ["ATLAS:82-85", "IGT:215-218", "IGT:656-658"],
}

TERRAIN_HEADER_NOTE = (
    "terrain equations are ONE CANDIDATE realization, not settled math (ATLAS:82-85)"
)

TERRAIN_ORDER = ["Se-in", "Ne-in", "Ni-in", "Si-in"]
OUTER_LOOP_TERRAIN_ORDER = ["Se-in", "Ne-in", "Ni-in", "Si-in"]
INNER_LOOP_TERRAIN_ORDER = ["Se-in", "Si-in", "Ni-in", "Ne-in"]
OUTER_LOOP_STAGE_IDS = ["TiSe", "NeTi", "NiFe", "FeSi"]
INNER_LOOP_STAGE_IDS = ["SeFi", "SiTe", "TeNi", "FiNe"]

OPERATORS = {
    "Ti": {
        "channel": "Ti_q(rho) = (1 - q1) rho + q1 E_z(rho)",
        "q": 1.0 - 0.69,
        "lambda": 0.69,
        "source": "SIGNED:136-148; IGT:475",
    },
    "Te": {
        "channel": "Te_q(rho) = (1 - q2) rho + q2 E_x(rho)",
        "q": 1.0 - 0.73,
        "lambda": 0.73,
        "source": "SIGNED:284-296; IGT:476",
    },
    "Fi": {
        "channel": "Fi_theta(rho) = U_x(theta) rho U_x(theta)^dagger",
        "theta": 0.41,
        "source": "SIGNED:437-445; IGT:477",
    },
    "Fe": {
        "channel": "Fe_phi(rho) = U_z(phi) rho U_z(phi)^dagger",
        "phi": -0.37,
        "source": "SIGNED:549-557; IGT:478",
    },
}

TERRAINS = {
    "Se-in": {
        "name": "Funnel",
        "flux": "IN",
        "jungian_function": "Se",
        "type": "Type 1",
        "generator": "sum_k D[L_k](rho) - i epsilon_F [H0, rho]",
        "scratch_bloch": "R_N(.13)(sqrt(.78)x, sqrt(.78)y, .78z+.22*.86)",
        "params": {"epsilon": 0.13, "keep_z": 0.78, "loss": 0.22, "target_z": 0.86},
        "source": "IGT:484-487; ATLAS:103-108",
    },
    "Ne-in": {
        "name": "Vortex",
        "flux": "IN",
        "jungian_function": "Ne",
        "type": "Type 1",
        "generator": "-i[H0, rho] + epsilon_V sum_k D[L_k](rho)",
        "scratch_bloch": ".94 R_N(.47)r",
        "params": {"rotation": 0.47, "shrink": 0.94},
        "source": "IGT:487; ATLAS:108",
    },
    "Ni-in": {
        "name": "Pit",
        "flux": "IN",
        "jungian_function": "Ni",
        "type": "Type 1",
        "generator": "D[sqrt(gamma) sigma_-](rho) - i epsilon_P [H0, rho]",
        "scratch_bloch": "R_N(.09)(sqrt(.70)x, sqrt(.70)y, .70z-.30*.92)",
        "params": {"epsilon": 0.09, "keep_z": 0.70, "loss": 0.30, "target_z": -0.92},
        "source": "IGT:488; ATLAS:109",
    },
    "Si-in": {
        "name": "Hill",
        "flux": "IN",
        "jungian_function": "Si",
        "type": "Type 1",
        "generator": "-i[H_C, rho] + sum_j kappa_j(P_j rho P_j - 1/2(P_j rho + rho P_j))",
        "scratch_bloch": "R_{M_in}(.19)(P_{M_in}(r)+.58(r-P_{M_in}(r)))",
        "params": {"rotation": 0.19, "transverse_keep": 0.58},
        "source": "IGT:489; ATLAS:110",
    },
}

STAGES = [
    {
        "stage_id": "TiSe",
        "loop": "outer",
        "terrain": "Se-in",
        "operator": "Ti",
        "composition": "terrain_after_operator",
        "order_text": "Se-in(Ti(rho))",
        "casing": "LOSE",
        "source": "IGT:529-532; ATLAS:219-222",
    },
    {
        "stage_id": "SeFi",
        "loop": "inner",
        "terrain": "Se-in",
        "operator": "Fi",
        "composition": "operator_after_terrain",
        "order_text": "Fi(Se-in(rho))",
        "casing": "win",
        "source": "IGT:529-532; ATLAS:219-222",
    },
    {
        "stage_id": "NeTi",
        "loop": "outer",
        "terrain": "Ne-in",
        "operator": "Ti",
        "composition": "operator_after_terrain",
        "order_text": "Ti(Ne-in(rho))",
        "casing": "WIN",
        "source": "IGT:532; ATLAS:222",
    },
    {
        "stage_id": "FiNe",
        "loop": "inner",
        "terrain": "Ne-in",
        "operator": "Fi",
        "composition": "terrain_after_operator",
        "order_text": "Ne-in(Fi(rho))",
        "casing": "lose",
        "source": "IGT:532; ATLAS:222",
    },
    {
        "stage_id": "NiFe",
        "loop": "outer",
        "terrain": "Ni-in",
        "operator": "Fe",
        "composition": "operator_after_terrain",
        "order_text": "Fe(Ni-in(rho))",
        "casing": "LOSE",
        "source": "IGT:533; ATLAS:223",
    },
    {
        "stage_id": "TeNi",
        "loop": "inner",
        "terrain": "Ni-in",
        "operator": "Te",
        "composition": "terrain_after_operator",
        "order_text": "Ni-in(Te(rho))",
        "casing": "lose",
        "source": "IGT:533; ATLAS:223",
    },
    {
        "stage_id": "FeSi",
        "loop": "outer",
        "terrain": "Si-in",
        "operator": "Fe",
        "composition": "terrain_after_operator",
        "order_text": "Si-in(Fe(rho))",
        "casing": "WIN",
        "source": "IGT:534; ATLAS:224",
    },
    {
        "stage_id": "SiTe",
        "loop": "inner",
        "terrain": "Si-in",
        "operator": "Te",
        "composition": "operator_after_terrain",
        "order_text": "Te(Si-in(rho))",
        "casing": "win",
        "source": "IGT:534; ATLAS:224",
    },
]

STAGE_BY_ID = {stage["stage_id"]: stage for stage in STAGES}

# Owner xlsx, Type One rows, copied from the pre-LLM file verified in this turn:
# /Users/joshuaeisenhart/Desktop/Personality theory._.xlsx
# sha256 5a2c6031707f77cb13195ffd5539710634159c7e299f23ea5f17d885c3ab67a8
XLSX_SOURCE = {
    "source": "owner_xlsx_pre_llm",
    "source_path": "/Users/joshuaeisenhart/Desktop/Personality theory._.xlsx",
    "repo_copy_path": "system_v7/constraint_core/inputs/Personality theory._.xlsx",
    "sha256": "5a2c6031707f77cb13195ffd5539710634159c7e299f23ea5f17d885c3ab67a8",
}

XLSX_CELLS = {
    ("Si", "Te"): {"mbti": "ISTJ", "raw_casing": "win", "xlsx_row": "Win Max, Big W"},
    ("Si", "Fe"): {"mbti": "ESFJ", "raw_casing": "WIN", "xlsx_row": "Win Max, Big W"},
    ("Ne", "Ti"): {"mbti": "ENTP", "raw_casing": "WIN", "xlsx_row": "Win Max, Big W"},
    ("Ne", "Fi"): {"mbti": "INFP", "raw_casing": "lose", "xlsx_row": "Win Max, Big W"},
    ("Se", "Ti"): {"mbti": "ISTP", "raw_casing": "LOSE", "xlsx_row": "Loss Max, Big L"},
    ("Se", "Fi"): {"mbti": "ESFP", "raw_casing": "win", "xlsx_row": "Loss Max, Big L"},
    ("Ni", "Te"): {"mbti": "ENTJ", "raw_casing": "Lose", "xlsx_row": "Loss Max, Big L"},
    ("Ni", "Fe"): {"mbti": "INFJ", "raw_casing": "LOSE", "xlsx_row": "Loss Max, Big L"},
}


def terrain_function(terrain: str) -> str:
    return terrain.split("-", 1)[0]


def build_mbti_annotation() -> dict:
    by_stage = {}
    for stage in STAGES:
        key = (terrain_function(stage["terrain"]), stage["operator"])
        cell = XLSX_CELLS[key]
        by_stage[stage["stage_id"]] = {
            "terrain": stage["terrain"],
            "operator": stage["operator"],
            "mbti": cell["mbti"],
            "xlsx_raw_casing": cell["raw_casing"],
            "xlsx_row": cell["xlsx_row"],
            "load_bearing": False,
        }
    return {
        **XLSX_SOURCE,
        "load_bearing": False,
        "note": "Labels only; never used by numeric terrain/operator computation.",
        "by_stage": by_stage,
    }


MBTI_ANNOTATION = build_mbti_annotation()


def build_casing_cross_check() -> list[dict]:
    rows = []
    for stage in STAGES:
        key = (terrain_function(stage["terrain"]), stage["operator"])
        xlsx = XLSX_CELLS[key]
        rows.append(
            {
                "stage_id": stage["stage_id"],
                "terrain": stage["terrain"],
                "operator": stage["operator"],
                "doc_casing": stage["casing"],
                "xlsx_raw_casing": xlsx["raw_casing"],
                "raw_case_agree": stage["casing"] == xlsx["raw_casing"],
                "normalized_agree": stage["casing"].lower() == xlsx["raw_casing"].lower(),
                "mbti": xlsx["mbti"],
                "source": "doc_vs_owner_xlsx_pre_llm",
                "load_bearing": False,
            }
        )
    return rows


def spec_dict() -> dict:
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_extraction": SOURCE_EXTRACTION,
        "source_cites": deepcopy(SOURCE_CITES),
        "terrain_header_note": TERRAIN_HEADER_NOTE,
        "terrains": deepcopy(TERRAINS),
        "operators": deepcopy(OPERATORS),
        "stages": deepcopy(STAGES),
        "traversals": {
            "outer": {
                "loop": "deductive",
                "direction": "CCW",
                "terrain_order": OUTER_LOOP_TERRAIN_ORDER,
                "stage_ids": OUTER_LOOP_STAGE_IDS,
                "source": "IGT:464-469; IGT:517-525",
            },
            "inner": {
                "loop": "inductive",
                "direction": "CW",
                "terrain_order": INNER_LOOP_TERRAIN_ORDER,
                "stage_ids": INNER_LOOP_STAGE_IDS,
                "source": "IGT:464-469; IGT:517-525",
            },
        },
        "mbti_annotation": deepcopy(MBTI_ANNOTATION),
        "casing_cross_check": build_casing_cross_check(),
        "substrates_in_v0": ["numpy", "julia"],
        "substrates_queued": ["jax", "torch"],
    }
