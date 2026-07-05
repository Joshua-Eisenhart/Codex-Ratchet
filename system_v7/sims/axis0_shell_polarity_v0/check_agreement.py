#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEYS = ["Delta_H_Omega", "Delta_S_B", "K_binding", "log_Z_path", "order_gap", "I_c"]


def load(name):
    return json.loads((ROOT / name).read_text())


def main():
    jax = load("axis0_shell_polarity_v0_jax_results.json")
    julia = load("axis0_shell_polarity_v0_julia_results.json")
    diffs = {}
    for regime in ["open", "binding"]:
        for key in KEYS:
            a = jax["component_means"][regime][key]
            b = julia["component_means"][regime][key]
            diffs[f"{regime}.{key}"] = abs(a - b)
    max_diff = max(diffs.values())
    controls = jax["controls"]
    required_kills = all(v["kill_or_weaken"] for v in controls.values())
    parity = max_diff < 1e-9
    lint = (
        jax["classification"] == "scratch_diagnostic"
        and jax["promotion_allowed"] is False
        and jax["capstone"] == "DRAFT_UNAUDITED"
        and jax["axis0_near_object"] == "shell-polarity readout"
        and len(jax["component_table"]["open"]) >= 6
        and len(jax["discovered_projection"]["used_components"]) > 0
        and required_kills
    )
    out = {
        "sim_id": "axis0_shell_polarity_v0",
        "parity": parity,
        "max_mean_abs_diff": max_diff,
        "lint": lint,
        "required_controls_kill_or_weaken": required_kills,
        "discovered_projection": jax["discovered_projection"],
        "control_outcomes": controls,
    }
    (ROOT / "agreement.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))
    raise SystemExit(0 if parity and lint else 1)


if __name__ == "__main__":
    main()
