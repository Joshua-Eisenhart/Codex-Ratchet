#!/usr/bin/env python3
"""
qit_runtime_state_history_adapter.py

Build the smallest honest graph-adjacent runtime slice for the QIT lane.

This helper does NOT mutate the owner graph and does NOT claim a live runtime
graph already exists. It maps `engine_core.EngineState` and its append-only
history into:
  - a mutable `RuntimeStateOverlay`
  - an append-only `HistoryRunPacket`

Both surfaces reference stable QIT `public_id`s from the owner graph builder.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "probes"))

from qit_owner_schemas import (
    EngineTypeEnum,
    HistoryRunPacket,
    HistoryStepRecord,
    OperatorEnum,
    RuntimeStateOverlay,
)
from engine_core import EngineState, TERRAINS


def _utc_tag() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _public_id(prefix: str, name: str) -> str:
    return f"qit::{prefix}::{name}"


def _engine_public_id(engine_type: int) -> str:
    engine_name = "type1_deductive" if engine_type == 1 else "type2_inductive"
    return _public_id("ENGINE", engine_name)


def _engine_enum(engine_type: int) -> EngineTypeEnum:
    return EngineTypeEnum.DEDUCTIVE if engine_type == 1 else EngineTypeEnum.INDUCTIVE


def _terrain_name(stage_idx_mod8: int) -> str:
    return str(TERRAINS[stage_idx_mod8]["name"])


def _stage_public_id(engine_type: int, terrain: str) -> str:
    engine_name = "type1_deductive" if engine_type == 1 else "type2_inductive"
    return _public_id("MACRO_STAGE", f"{engine_name}_{terrain}")


def _step_public_id(engine_type: int, terrain: str, operator: str) -> str:
    engine_name = "type1_deductive" if engine_type == 1 else "type2_inductive"
    return _public_id("SUBCYCLE_STEP", f"{engine_name}_{terrain}_{operator}")


def _parse_history_stage_token(stage_token: str) -> tuple[str, str]:
    terrain, operator = stage_token.rsplit("_", 1)
    return terrain, operator


def build_runtime_state_overlay(state: EngineState) -> RuntimeStateOverlay:
    stage_idx_mod8 = int(state.stage_idx % 8)
    terrain = _terrain_name(stage_idx_mod8)
    last_completed_step_public_id = None
    if state.history:
        last_terrain, last_operator = _parse_history_stage_token(str(state.history[-1]["stage"]))
        last_completed_step_public_id = _step_public_id(state.engine_type, last_terrain, last_operator)

    return RuntimeStateOverlay(
        engine_public_id=_engine_public_id(state.engine_type),
        active_stage_public_id=_stage_public_id(state.engine_type, terrain),
        last_completed_step_public_id=last_completed_step_public_id,
        stage_index_mod8=stage_idx_mod8,
        engine_type=_engine_enum(state.engine_type),
        eta=float(state.eta),
        theta1=float(state.theta1),
        theta2=float(state.theta2),
        ga0_level=float(state.ga0_level),
        history_length=len(state.history),
    )


def build_history_run_packet(state: EngineState, run_id: str | None = None) -> HistoryRunPacket:
    records: list[HistoryStepRecord] = []
    for idx, entry in enumerate(state.history):
        terrain, operator = _parse_history_stage_token(str(entry["stage"]))
        records.append(
            HistoryStepRecord(
                sequence_index=idx,
                step_public_id=_step_public_id(state.engine_type, terrain, operator),
                stage_public_id=_stage_public_id(state.engine_type, terrain),
                operator=OperatorEnum(operator),
                engine_type=_engine_enum(state.engine_type),
                dphi_L=float(entry["dphi_L"]),
                dphi_R=float(entry["dphi_R"]),
                strength=float(entry["strength"]),
                ga0_before=float(entry["ga0_before"]),
                ga0_after=float(entry["ga0_after"]),
            )
        )

    return HistoryRunPacket(
        run_id=run_id or f"run::{_engine_enum(state.engine_type).value}::{_utc_tag()}",
        engine_public_id=_engine_public_id(state.engine_type),
        engine_type=_engine_enum(state.engine_type),
        total_steps=len(records),
        macro_stages_completed=int(state.stage_idx),
        step_records=records,
    )


def build_runtime_slice(state: EngineState, run_id: str | None = None) -> dict[str, Any]:
    overlay = build_runtime_state_overlay(state)
    history = build_history_run_packet(state, run_id=run_id)
    return {
        "schema": "QIT_RUNTIME_SLICE_v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "owner_graph_role": "read_only_reference_only",
        "state_overlay": overlay.model_dump(),
        "history_packet": history.model_dump(),
    }


if __name__ == "__main__":
    from engine_core import GeometricEngine

    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    state = engine.step(state, stage_idx=0)
    print(json.dumps(build_runtime_slice(state), indent=2))
