#!/usr/bin/env python3
"""
Generate the live 64-step runtime engine table from engine_core.py.

This is intentionally separate from the 64 structural hexagram/state-space table.
It documents what the current engine actually executes:
  2 engine types × 8 terrains × 4 operator slots = 64 runtime steps
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "probes"))

from engine_core import GeometricEngine, StageControls, TERRAINS, OPERATORS  # noqa: E402


def runtime_rows():
    rows = []
    global_step = 0
    default_controls = StageControls()

    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        for stage_idx, terrain in enumerate(TERRAINS):
            for op_slot, op_name in enumerate(OPERATORS):
                ga0_target = engine._ga0_target(terrain, op_name, default_controls)
                strength = engine._operator_strength(
                    terrain, op_name, default_controls, ga0_level=ga0_target
                )

                if engine_type == 1:
                    dominant = (terrain["loop"] == "base" and op_name in ("Fe", "Ti")) or (
                        terrain["loop"] == "fiber" and op_name in ("Te", "Fi")
                    )
                else:
                    dominant = (terrain["loop"] == "base" and op_name in ("Te", "Fi")) or (
                        terrain["loop"] == "fiber" and op_name in ("Fe", "Ti")
                    )

                rows.append(
                    {
                        "global_step": global_step,
                        "engine_type": engine_type,
                        "stage_idx": stage_idx,
                        "terrain": terrain["name"],
                        "loop": terrain["loop"],
                        "expansion": terrain["expansion"],
                        "open": terrain["open"],
                        "operator_slot": op_slot,
                        "operator": op_name,
                        "dominant_for_type": dominant,
                        "default_ga0_target": round(float(ga0_target), 6),
                        "default_strength": round(float(strength), 6),
                    }
                )
                global_step += 1
    return rows


def build_markdown(rows):
    lines = []
    lines.append("# 64-Step Runtime Engine Table")
    lines.append("")
    lines.append("This is the live execution table generated from `engine_core.py`.")
    lines.append("It is not the same object as the 64 structural hexagram/state-space table.")
    lines.append("")
    lines.append("Shape:")
    lines.append("- `2 engine types × 8 terrains × 4 operator slots = 64 runtime steps`")
    lines.append("- Type 1 and Type 2 run the same operator order per terrain")
    lines.append("- What changes is dominance/strength by loop and type")
    lines.append("")
    lines.append("| Step | Type | Stage | Terrain | Loop | Exp | Open | Slot | Operator | Dominant | Default Ax0 Target | Default Strength |")
    lines.append("|---:|---:|---:|---|---|---:|---:|---:|---|---:|---:|---:|")
    for r in rows:
        lines.append(
            f"| {r['global_step']} | {r['engine_type']} | {r['stage_idx']} | "
            f"{r['terrain']} | {r['loop']} | {int(r['expansion'])} | {int(r['open'])} | "
            f"{r['operator_slot']} | {r['operator']} | {int(r['dominant_for_type'])} | "
            f"{r['default_ga0_target']:.6f} | {r['default_strength']:.6f} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This table documents current runtime semantics only.")
    lines.append("- It should be read alongside the structural 64-state table, not as a replacement for it.")
    lines.append("- If engine semantics change in `engine_core.py`, regenerate this table.")
    return "\n".join(lines)


def main():
    rows = runtime_rows()
    md = build_markdown(rows)

    out_md = Path(__file__).with_name("64_RUNTIME_ENGINE_TABLE.md")
    out_json = Path(__file__).with_name("64_RUNTIME_ENGINE_TABLE.json")

    out_md.write_text(md)
    out_json.write_text(json.dumps(rows, indent=2))

    print(f"Wrote {out_md}")
    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()
