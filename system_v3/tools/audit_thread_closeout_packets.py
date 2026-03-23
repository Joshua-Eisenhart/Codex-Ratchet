#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def _load_packets(path: Path) -> list[dict]:
    packets: list[dict] = []
    if not path.exists():
        raise SystemExit(f"missing_sink:{path}")
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            packet = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid_jsonl:{path}:{lineno}:{exc.colno}") from exc
        packets.append(packet)
    return packets


def _top_outputs(packets: list[dict], limit: int) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    outputs: list[dict] = []
    for packet in packets:
        label = packet.get("source_thread_label", "")
        for item in packet.get("strongest_outputs", []):
            key = (label, item.get("artifact_path", ""))
            if key in seen:
                continue
            seen.add(key)
            outputs.append(
                {
                    "source_thread_label": label,
                    "artifact_path": item.get("artifact_path", ""),
                    "why_it_matters": item.get("why_it_matters", ""),
                    "status": item.get("status", ""),
                }
            )
            if len(outputs) >= limit:
                return outputs
    return outputs


def _summary(packets: list[dict], top_n: int) -> dict:
    decisions = Counter(packet.get("final_decision", "") for packet in packets)
    diagnoses = Counter(packet.get("thread_diagnosis", "") for packet in packets)
    labels = [packet.get("source_thread_label", "") for packet in packets]
    continued = [
        {
            "source_thread_label": packet.get("source_thread_label", ""),
            "next_step": packet.get("if_one_more_step", {}).get("next_step", ""),
            "stop_condition": packet.get("if_one_more_step", {}).get("stop_condition", ""),
        }
        for packet in packets
        if packet.get("final_decision") == "CONTINUE_ONE_BOUNDED_STEP"
    ]
    correction_later = [
        packet.get("source_thread_label", "")
        for packet in packets
        if packet.get("final_decision") == "CORRECT_LANE_LATER"
    ]
    stop_now = [
        packet.get("source_thread_label", "")
        for packet in packets
        if packet.get("final_decision") == "STOP"
    ]
    return {
        "schema": "THREAD_CLOSEOUT_AUDIT_SUMMARY_v1",
        "packet_count": len(packets),
        "source_thread_labels": labels,
        "decision_counts": dict(decisions),
        "diagnosis_counts": dict(diagnoses),
        "stop_now_labels": stop_now,
        "continue_one_bounded_step": continued,
        "correct_lane_later_labels": correction_later,
        "top_outputs": _top_outputs(packets, top_n),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Summarize captured thread closeout packets from the repo-held JSONL sink.")
    parser.add_argument(
        "--sink",
        default="system_v3/a2_derived_indices_noncanonical/thread_closeout_packets.000.jsonl",
        help="Path to the thread closeout packet JSONL sink.",
    )
    parser.add_argument(
        "--top-outputs",
        type=int,
        default=12,
        help="Maximum number of strongest outputs to include in the summary.",
    )
    args = parser.parse_args(argv)

    packets = _load_packets(Path(args.sink))
    print(json.dumps(_summary(packets, args.top_outputs), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
