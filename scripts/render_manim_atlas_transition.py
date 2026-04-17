from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from system_v4.visualization.manim_export import collect_manim_export

try:
    from manim import Create, DOWN, FadeOut, Line, Polygon, Scene, Text, UP, VGroup
except ImportError:  # pragma: no cover - runtime-gated in tests and capability sim
    Create = DOWN = FadeOut = Line = Polygon = Scene = Text = UP = VGroup = None

BG = "#1C1C1C"
PRIMARY = "#58C4DD"
SECONDARY = "#83C167"
ACCENT = "#FFFF00"
WARNING = "#FF6B6B"
TEXT_COLOR = "#EAEAEA"


def _project_point(point: list[float]) -> np.ndarray:
    array = np.array(point[:2], dtype=float)
    return np.array([array[0] * 2.4, array[1] * 2.4, 0.0], dtype=float)


def load_scene_payload(run_dir: Path) -> dict:
    payload = collect_manim_export(Path(run_dir))
    patches = []
    for survivor in payload.get("admitted_survivors", []):
        if survivor.get("entity_kind") != "mesh_patch":
            continue
        points = survivor.get("points_xyz") or []
        if len(points) < 3:
            continue
        projected_points = [_project_point(point).tolist() for point in points]
        centroid = np.mean(np.array(projected_points, dtype=float), axis=0).tolist()
        patches.append(
            {
                "entity_id": survivor.get("entity_id"),
                "patch_id": survivor.get("patch_id"),
                "chart_id": survivor.get("chart_id"),
                "points": projected_points,
                "centroid": centroid,
                "seam_edges": list(survivor.get("seam_edges", [])),
                "transition_meta": list(survivor.get("transition_meta", [])),
            }
        )

    transitions = []
    for patch in patches:
        for transition in patch.get("transition_meta", []):
            transitions.append(
                {
                    "from_patch": patch.get("patch_id"),
                    "to_patch": transition.get("neighbor_patch_id"),
                    "transition_kind": transition.get("transition_kind"),
                }
            )

    return {
        "run_id": payload.get("run_id"),
        "sim_name": payload.get("sim_name"),
        "constraint_set": payload.get("constraint_set"),
        "probe_family": payload.get("probe_family"),
        "status_label": payload.get("status_label"),
        "claim_state": payload.get("claim_state"),
        "promotion_status": payload.get("promotion_status"),
        "exclusion_count": payload.get("exclusions", {}).get("exclusion_event_count", 0),
        "patches": patches,
        "transitions": transitions,
    }


def load_scene_payload_from_env() -> dict:
    run_dir = os.environ.get("MANIM_VIZ_RUN_DIR")
    if not run_dir:
        raise RuntimeError("MANIM_VIZ_RUN_DIR is required for AtlasTransitionOverview")
    return load_scene_payload(Path(run_dir))


if Scene is None:
    class AtlasTransitionOverview:  # pragma: no cover - only used to fail closed when runtime is missing
        def __init__(self, *args, **kwargs):
            raise RuntimeError("manim runtime is unavailable for AtlasTransitionOverview")
else:
    class AtlasTransitionOverview(Scene):
        def construct(self):
            self.camera.background_color = BG
            payload = load_scene_payload_from_env()

            title = Text("Atlas Transition Overview", font_size=42, color=PRIMARY)
            title.to_edge(UP, buff=0.6)
            subtitle = Text(
                f"{payload['constraint_set']} | {payload['probe_family']}",
                font_size=22,
                color=TEXT_COLOR,
            )
            subtitle.next_to(title, DOWN, buff=0.35)
            self.play(Create(title), run_time=1.2)
            self.play(Create(subtitle), run_time=0.8)
            self.wait(1.0)

            patch_group = VGroup()
            centroid_map = {}
            palette = [PRIMARY, SECONDARY, "#C792EA", "#F78C6C"]
            for index, patch in enumerate(payload["patches"]):
                polygon = Polygon(*[np.array(point) for point in patch["points"]], color=palette[index % len(palette)])
                polygon.set_fill(palette[index % len(palette)], opacity=0.25)
                label = Text(f"{patch['patch_id']}\n{patch['chart_id']}", font_size=18, color=TEXT_COLOR)
                label.move_to(np.array(patch["centroid"]))
                patch_group.add(polygon, label)
                centroid_map[patch["patch_id"]] = np.array(patch["centroid"])
            if patch_group:
                self.play(Create(patch_group), run_time=1.6)
                self.wait(1.0)

            transition_group = VGroup()
            seen_pairs = set()
            for transition in payload["transitions"]:
                key = tuple(sorted([str(transition["from_patch"]), str(transition["to_patch"])]))
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                start = centroid_map.get(transition["from_patch"])
                end = centroid_map.get(transition["to_patch"])
                if start is None or end is None:
                    continue
                line = Line(start, end, color=ACCENT, stroke_width=6)
                label = Text(str(transition["transition_kind"]), font_size=16, color=ACCENT)
                label.move_to((start + end) / 2 + np.array([0.0, 0.35, 0.0]))
                transition_group.add(line, label)
            if transition_group:
                self.play(Create(transition_group), run_time=1.4)
                self.wait(1.2)

            footer = Text(
                f"claim={payload['claim_state']} | promotion={payload['promotion_status']} | exclusions={payload['exclusion_count']}",
                font_size=20,
                color=WARNING if payload["exclusion_count"] else TEXT_COLOR,
            )
            footer.to_edge(DOWN, buff=0.7)
            self.play(Create(footer), run_time=0.8)
            self.wait(1.2)
            self.play(FadeOut(VGroup(*self.mobjects)), run_time=0.6)
