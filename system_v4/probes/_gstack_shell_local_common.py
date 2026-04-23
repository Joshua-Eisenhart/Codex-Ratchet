#!/usr/bin/env python3
import json
import os


def compute_overall(*sections):
    merged = {}
    for section in sections:
        merged.update(section)
    return all(
        entry.get("pass", False)
        for entry in merged.values()
        if isinstance(entry, dict) and "pass" in entry
    )


def write_shell_local_result(stem, shell_name, tool_manifest, tool_integration_depth, positive, negative, boundary, extras=None):
    overall = compute_overall(positive, negative, boundary)
    payload = {
        "name": stem,
        "classification": "canonical",
        "overall_pass": overall,
        "shell": shell_name,
        "tool_manifest": tool_manifest,
        "tool_integration_depth": tool_integration_depth,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }
    if extras:
        payload.update(extras)
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{stem}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
    return out_path, overall
