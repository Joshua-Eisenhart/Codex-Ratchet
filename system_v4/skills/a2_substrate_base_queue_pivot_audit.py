"""
a2_substrate_base_queue_pivot_audit.py

Run one bounded A2 control pass that checks whether the dormant substrate-base
family slice can honestly replace the current entropy-selected A1 queue choice.
This lane proves the pivot through the existing queue selector before copying
results into the live current queue surfaces.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


HANDOFF_PACKET = (
    "system_v4/a2_state/launch_bundles/"
    "nested_graph_build_a2_substrate_base_queue_pivot_audit/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A2_SUBSTRATE_BASE_QUEUE_PIVOT_"
    "AUDIT__2026_03_20__v1.json"
)
CURRENT_QUEUE_PACKET = "system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json"
CURRENT_QUEUE_NOTE = "system_v3/a2_state/A1_QUEUE_STATUS__CURRENT__2026_03_16__v1.md"
CURRENT_CANDIDATE_REGISTRY = "system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json"
DUAL_SLICE = "system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__DUAL_STACKED_ENGINE_2026_03_17__v1.json"
SUBSTRATE_SLICE = "system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
SUBSTRATE_SAMPLE_NOTE = (
    "system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_SAMPLE__SUBSTRATE_BASE_"
    "SCAFFOLD__2026_03_15__v1.md"
)
QUEUE_SURFACE_SPEC = "system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md"
ROLE_SPLIT_SPEC = "system_v3/specs/33_A2_VS_A1_ROLE_SPLIT__v1.md"
SUBSTRATE_CAMPAIGN = "system_v3/a1_state/A1_FIRST_SUBSTRATE_FAMILY_CAMPAIGN__v1.md"
ROSETTA_PROBE = "system_v3/a1_state/A1_ROSETTA_BATCH__PROBE_OPERATOR__v1.md"
CARTRIDGE_PROBE = "system_v3/a1_state/A1_CARTRIDGE_REVIEW__PROBE_OPERATOR__v1.md"
RUN_ANCHOR_SUBSTRATE = "system_v3/run_anchor_surface/RUN_ANCHOR__SUBSTRATE_BASE_VALIDITY_FAMILY__v1.md"
OUTPUT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A2_SUBSTRATE_BASE_QUEUE_PIVOT_AUDIT__2026_03_20__v1.md"
)
LIVE_DISPATCH_ID = "A1_DISPATCH__SUBSTRATE_BASE_CURRENT__2026_03_20__v1"
LIVE_OUT_DIR = (
    "system_v3/a2_state/launch_bundles/"
    "a1_substrate_base_current__2026_03_20__v1"
)


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (root / path)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _run_json(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "").strip() or f"command_failed:{cmd[0]}")
    return json.loads(proc.stdout)


def _validate_handoff(
    handoff_path: Path,
    handoff: dict[str, Any],
    *,
    expected_unit_id: str,
    expected_layer_id: str,
) -> list[str]:
    errors: list[str] = []
    if not handoff_path.exists():
        errors.append("handoff_packet_missing")
    if not handoff:
        errors.append("handoff_packet_unreadable_or_empty")
        return errors
    for key in ["unit_id", "dispatch_id", "layer_id", "queue_status", "role_type", "thread_class", "mode"]:
        if not str(handoff.get(key, "")).strip():
            errors.append(f"missing_handoff_field:{key}")
    for key in ["required_boot", "source_artifacts", "expected_outputs", "write_scope"]:
        value = handoff.get(key)
        if not isinstance(value, list) or not value:
            errors.append(f"missing_handoff_list:{key}")
    if str(handoff.get("unit_id", "")) and str(handoff.get("unit_id", "")) != expected_unit_id:
        errors.append("handoff_unit_id_mismatch")
    if str(handoff.get("layer_id", "")) and str(handoff.get("layer_id", "")) != expected_layer_id:
        errors.append("handoff_layer_id_mismatch")
    return errors


def _find_first_line(path: Path, contains_all: list[str]) -> dict[str, Any]:
    text = _load_text(path)
    if not text:
        return {}
    lowered_needles = [needle.lower() for needle in contains_all]
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        lowered = line.lower()
        if all(needle in lowered for needle in lowered_needles):
            return {"path": str(path), "line": lineno, "text": line}
    return {}


def _format_evidence(label: str, evidence: dict[str, Any]) -> str:
    if not evidence:
        return f"- {label}: MISSING"
    return f"- {label}: {evidence['path']}:{evidence['line']} :: {evidence['text']}"


def run_a2_substrate_base_queue_pivot_audit(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    handoff_path = _resolve(root, HANDOFF_PACKET)
    handoff = _load_json(handoff_path)
    handoff_errors = _validate_handoff(
        handoff_path,
        handoff,
        expected_unit_id="A2_SUBSTRATE_BASE_QUEUE_PIVOT_AUDIT",
        expected_layer_id="A2_LOW_CONTROL",
    )

    current_packet_path = _resolve(root, CURRENT_QUEUE_PACKET)
    current_note_path = _resolve(root, CURRENT_QUEUE_NOTE)
    current_registry_path = _resolve(root, CURRENT_CANDIDATE_REGISTRY)
    dual_slice_path = _resolve(root, DUAL_SLICE)
    substrate_slice_path = _resolve(root, SUBSTRATE_SLICE)
    live_out_dir = _resolve(root, LIVE_OUT_DIR)
    output_audit_path = _resolve(root, OUTPUT_AUDIT)

    queue_before = _load_json(current_packet_path)
    registry_before = _load_json(current_registry_path)

    evidence = {
        "queue_surface_registry_rule": _find_first_line(
            _resolve(root, QUEUE_SURFACE_SPEC),
            ["registry is the bounded candidate input set"],
        ),
        "role_split_queue_routing": _find_first_line(
            _resolve(root, ROLE_SPLIT_SPEC),
            ["queue routing"],
        ),
        "substrate_sample_best_first": _find_first_line(
            _resolve(root, SUBSTRATE_SAMPLE_NOTE),
            ["first substrate family", "best first slice"],
        ),
        "substrate_campaign_head": _find_first_line(
            _resolve(root, SUBSTRATE_CAMPAIGN),
            ["active strategy head:"],
        ),
        "probe_rosetta_head": _find_first_line(
            _resolve(root, ROSETTA_PROBE),
            ["active strategy head on the substrate lane"],
        ),
        "probe_cartridge_readiness": _find_first_line(
            _resolve(root, CARTRIDGE_PROBE),
            ["readiness: PASS"],
        ),
        "substrate_run_anchor": _find_first_line(
            _resolve(root, RUN_ANCHOR_SUBSTRATE),
            ["graveyard-first execution is real on this lane"],
        ),
    }
    missing_evidence = [label for label, item in evidence.items() if not item]

    result_value = "SUBSTRATE_BASE_QUEUE_PIVOT_AUDIT_BLOCKED"
    decision = "Do not change the live A1 queue yet."
    live_queue_status = ""
    live_ready_packet = ""
    live_bundle_result = ""
    live_gate_result = ""
    live_send_text = ""
    live_handoff = ""
    live_selected_family = ""
    live_note_path_str = str(current_note_path)
    live_queue_packet_path_str = str(current_packet_path)
    live_registry_path_str = str(current_registry_path)
    temp_queue_status = ""
    temp_ready_packet = ""
    copied_live = False

    if not handoff_errors and not missing_evidence:
        with tempfile.TemporaryDirectory(prefix="substrate_queue_pivot_") as tmpdir:
            tmp = Path(tmpdir)
            tmp_registry = tmp / "candidate_registry.json"
            tmp_queue = tmp / "queue_status.json"
            tmp_note = tmp / current_note_path.name

            _run_json(
                [
                    sys.executable,
                    str(root / "system_v3" / "tools" / "create_a1_queue_candidate_registry.py"),
                    "--family-slice-json",
                    str(dual_slice_path),
                    "--family-slice-json",
                    str(substrate_slice_path),
                    "--selected-family-slice-json",
                    str(substrate_slice_path),
                    "--out-json",
                    str(tmp_registry),
                ]
            )
            _run_json(
                [
                    sys.executable,
                    str(root / "system_v3" / "tools" / "prepare_current_a1_queue_status_from_candidates.py"),
                    "--candidate-registry-json",
                    str(tmp_registry),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    LIVE_DISPATCH_ID,
                    "--preparation-mode",
                    "packet",
                    "--out-dir",
                    str(live_out_dir),
                    "--out-json",
                    str(tmp_queue),
                    "--out-note",
                    str(tmp_note),
                ]
            )

            temp_packet = _load_json(tmp_queue)
            temp_queue_status = str(temp_packet.get("queue_status", ""))
            temp_ready_packet = str(temp_packet.get("ready_packet_json", ""))
            temp_selected_family = str(temp_packet.get("family_slice_json", ""))

            if (
                temp_queue_status == "READY_FROM_NEW_A2_HANDOFF"
                and temp_selected_family == str(substrate_slice_path)
                and temp_ready_packet
                and Path(temp_ready_packet).exists()
            ):
                shutil.copy2(tmp_registry, current_registry_path)
                shutil.copy2(tmp_queue, current_packet_path)
                shutil.copy2(tmp_note, current_note_path)
                current_note_lines = current_note_path.read_text(encoding="utf-8").splitlines()
                if current_note_lines and current_note_lines[0].startswith("# "):
                    current_note_lines[0] = f"# {current_note_path.stem}"
                    current_note_path.write_text("\n".join(current_note_lines) + "\n", encoding="utf-8")
                copied_live = True
                live_packet = _load_json(current_packet_path)
                live_queue_status = str(live_packet.get("queue_status", ""))
                live_ready_packet = str(live_packet.get("ready_packet_json", ""))
                live_selected_family = str(live_packet.get("family_slice_json", ""))
                if (
                    live_queue_status == "READY_FROM_NEW_A2_HANDOFF"
                    and live_selected_family == str(substrate_slice_path)
                    and live_ready_packet
                ):
                    bundle_result = _run_json(
                        [
                            sys.executable,
                            str(root / "system_v3" / "tools" / "prepare_codex_launch_bundle.py"),
                            "--packet-json",
                            live_ready_packet,
                            "--out-dir",
                            str(live_out_dir),
                        ]
                    )
                    live_bundle_result = str(live_out_dir / (Path(live_ready_packet).stem + "__BUNDLE_RESULT.json"))
                    live_gate_result = str(bundle_result.get("gate_result_json", ""))
                    live_send_text = str(bundle_result.get("send_text_path", ""))
                    live_handoff = str(bundle_result.get("handoff_json", ""))
                    result_value = "SUBSTRATE_BASE_QUEUE_PIVOT_CONFIRMED__READY_FROM_NEW_A2_HANDOFF"
                    decision = (
                        "Promote the substrate-base scaffold family into the live "
                        "A1 candidate registry and current queue surfaces. The real "
                        "queue selector accepts the owner family slice and produces "
                        "a ready A1_PROPOSAL packet plus an operator-ready launch "
                        "bundle without touching the paused entropy branch."
                    )
                else:
                    result_value = "SUBSTRATE_BASE_QUEUE_PIVOT_LIVE_COPY_DRIFTED"
                    decision = (
                        "The temp selector admitted the substrate pivot, but the live "
                        "current queue surfaces do not reflect the same ready packet "
                        "after copy. Leave this as a correction-needed result."
                    )
            else:
                result_value = "SUBSTRATE_BASE_QUEUE_PIVOT_NOT_ADMITTED"
                decision = (
                    "The real queue selector did not admit the substrate-base slice "
                    "as a ready A1 current packet. Keep the live queue unchanged."
                )
                live_queue_status = str(queue_before.get("queue_status", ""))
                live_selected_family = str(registry_before.get("selected_family_slice_json", ""))
    elif handoff_errors:
        result_value = "MISSING_OR_INVALID_HANDOFF_PACKET"
        decision = "Fail closed because the queue-pivot handoff is missing or structurally invalid."
    else:
        result_value = "MISSING_DOCTRINE_EVIDENCE"
        decision = "Fail closed because the substrate queue-pivot doctrine evidence is incomplete."

    output_audit_path.parent.mkdir(parents=True, exist_ok=True)
    output_audit_path.write_text(
        "\n".join(
            [
                "# A2_SUBSTRATE_BASE_QUEUE_PIVOT_AUDIT__2026_03_20__v1",
                "",
                f"generated_utc: {_utc_iso()}",
                f"result: {result_value}",
                f"decision: {decision}",
                f"handoff_packet: {handoff_path}",
                f"current_queue_packet_before: {current_packet_path}",
                f"current_queue_status_before: {queue_before.get('queue_status', '')}",
                f"current_registry_selected_before: {registry_before.get('selected_family_slice_json', '')}",
                f"temp_queue_status: {temp_queue_status}",
                f"temp_ready_packet: {temp_ready_packet}",
                f"copied_live: {copied_live}",
                f"current_queue_status_after: {live_queue_status}",
                f"current_registry_selected_after: {live_selected_family}",
                f"current_candidate_registry: {live_registry_path_str}",
                f"current_queue_packet: {live_queue_packet_path_str}",
                f"current_queue_note: {live_note_path_str}",
                f"live_ready_packet: {live_ready_packet}",
                f"live_bundle_result: {live_bundle_result}",
                f"live_gate_result: {live_gate_result}",
                f"live_send_text: {live_send_text}",
                f"live_handoff: {live_handoff}",
                "",
                "## Evidence",
                _format_evidence("queue_surface_registry_rule", evidence["queue_surface_registry_rule"]),
                _format_evidence("role_split_queue_routing", evidence["role_split_queue_routing"]),
                _format_evidence("substrate_sample_best_first", evidence["substrate_sample_best_first"]),
                _format_evidence("substrate_campaign_head", evidence["substrate_campaign_head"]),
                _format_evidence("probe_rosetta_head", evidence["probe_rosetta_head"]),
                _format_evidence("probe_cartridge_readiness", evidence["probe_cartridge_readiness"]),
                _format_evidence("substrate_run_anchor", evidence["substrate_run_anchor"]),
                "",
                "## Notes",
                "- This lane proves the pivot through the current queue selector before copying the live current surfaces.",
                "- The paused entropy direct-executable branch in system_v4 remains paused; this is a separate queue-side A1_PROPOSAL readiness result.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "generated_utc": _utc_iso(),
        "result": result_value,
        "decision": decision,
        "current_queue_status_before": str(queue_before.get("queue_status", "")),
        "current_queue_status_after": live_queue_status,
        "current_registry_selected_after": live_selected_family,
        "copied_live": copied_live,
        "audit_path": str(output_audit_path),
        "current_candidate_registry": live_registry_path_str,
        "current_queue_packet": live_queue_packet_path_str,
        "current_queue_note": live_note_path_str,
        "live_ready_packet": live_ready_packet,
        "live_bundle_result": live_bundle_result,
        "live_gate_result": live_gate_result,
        "live_send_text": live_send_text,
        "live_handoff": live_handoff,
        "handoff_errors": handoff_errors,
        "missing_evidence": missing_evidence,
    }


def main(argv: list[str] | None = None) -> int:
    workspace_root = argv[1] if argv and len(argv) > 1 else str(REPO_ROOT)
    result = run_a2_substrate_base_queue_pivot_audit(workspace_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
