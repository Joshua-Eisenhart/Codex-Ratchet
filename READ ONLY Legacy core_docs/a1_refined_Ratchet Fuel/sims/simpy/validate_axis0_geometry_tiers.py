#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_SIMSON_DIR = Path(
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson"
)


def load_json(path: Path):
    return json.loads(path.read_text())


def gate_result(passed: bool, value, threshold, source: str, details: dict) -> dict:
    return {
        "passed": bool(passed),
        "value": value,
        "threshold": threshold,
        "source": source,
        "details": details,
    }


def evaluate_g1(simson_dir: Path, min_neg_frac: float) -> dict:
    path = simson_dir / "results_axis0_mutual_info.json"
    data = load_json(path)
    metrics = data["metrics"]
    sagb_min = float(metrics["SAgB_min"])
    neg_frac = float(metrics["neg_SAgB_frac"])
    passed = sagb_min < 0.0 and neg_frac > min_neg_frac
    return gate_result(
        passed=passed,
        value={"SAgB_min": sagb_min, "neg_SAgB_frac": neg_frac},
        threshold={"SAgB_min": "< 0.0", "neg_SAgB_frac": f"> {min_neg_frac}"},
        source=str(path),
        details={"trials": data.get("trials"), "seed": data.get("seed")},
    )


def evaluate_g2(simson_dir: Path) -> dict:
    path = simson_dir / "results_axis0_tiny_matched_control.json"
    data = load_json(path)
    bell = data["BELL_SEQ01"]
    ginibre = data["GINIBRE_SEQ01"]
    bell_neg_frac = float(bell["neg_SAgB_frac"])
    bell_sagb_max = float(bell["SAgB_max"])
    ginibre_neg_frac = float(ginibre["neg_SAgB_frac"])
    ginibre_sagb_min = float(ginibre["SAgB_min"])
    passed = (
        bell_neg_frac >= 0.95
        and bell_sagb_max < 0.0
        and ginibre_neg_frac <= 0.001
        and ginibre_sagb_min > 0.0
    )
    return gate_result(
        passed=passed,
        value={
            "bell_seq01_neg_SAgB_frac": bell_neg_frac,
            "bell_seq01_SAgB_max": bell_sagb_max,
            "ginibre_seq01_neg_SAgB_frac": ginibre_neg_frac,
            "ginibre_seq01_SAgB_min": ginibre_sagb_min,
        },
        threshold={
            "bell_seq01_neg_SAgB_frac": ">= 0.95",
            "bell_seq01_SAgB_max": "< 0.0",
            "ginibre_seq01_neg_SAgB_frac": "<= 0.001",
            "ginibre_seq01_SAgB_min": "> 0.0",
        },
        source=str(path),
        details={"trials": data.get("trials"), "cycles": data.get("cycles"), "terrain_params": data.get("terrain_params", {})},
    )


def evaluate_g3(simson_dir: Path, min_neg_frac: float) -> dict:
    path = simson_dir / "results_axis0_sagb_entangle_seed.json"
    data = load_json(path)
    seq01 = float(data["metrics_SEQ01"]["neg_SAgB_frac"])
    seq02 = float(data["metrics_SEQ02"]["neg_SAgB_frac"])
    best = max(seq01, seq02)
    passed = seq01 > 0.95 and seq02 > 0.95 and best > min_neg_frac
    return gate_result(
        passed=passed,
        value={"SEQ01_neg_SAgB_frac": seq01, "SEQ02_neg_SAgB_frac": seq02, "best": best},
        threshold={
            "SEQ01_neg_SAgB_frac": "> 0.95",
            "SEQ02_neg_SAgB_frac": "> 0.95",
            "best_neg_SAgB_frac": f"> {min_neg_frac}",
        },
        source=str(path),
        details={"entangle_reps": data.get("entangle_reps"), "trials": data.get("trials")},
    )


def evaluate_g4(simson_dir: Path, min_neg_frac: float) -> dict:
    path = simson_dir / "results_axis0_traj_corr_metrics.json"
    data = load_json(path)
    bell = data["BELL_SEQ01"]
    ginibre = data["GINIBRE_SEQ01"]
    bell_neg_frac = float(bell["SAgB_neg_frac_traj"])
    ginibre_neg_frac = float(ginibre["SAgB_neg_frac_traj"])
    bell_init_mean = float(bell["SAgB_init_mean"])
    bell_final_mean = float(bell["SAgB_final_mean"])
    passed = (
        bell_init_mean < 0.0
        and bell_final_mean > 0.0
        and bell_neg_frac >= 0.09
        and ginibre_neg_frac <= 1e-3
    )
    return gate_result(
        passed=passed,
        value={
            "bell_seq01_SAgB_init_mean": bell_init_mean,
            "bell_seq01_SAgB_final_mean": bell_final_mean,
            "bell_seq01_neg_SAgB_frac_traj": bell_neg_frac,
            "ginibre_seq01_neg_SAgB_frac_traj": ginibre_neg_frac,
        },
        threshold={
            "bell_seq01_SAgB_init_mean": "< 0.0",
            "bell_seq01_SAgB_final_mean": "> 0.0",
            "bell_seq01_neg_SAgB_frac_traj": ">= 0.09",
            "ginibre_seq01_neg_SAgB_frac_traj": "<= 0.001",
        },
        source=str(path),
        details={"trials": data.get("trials"), "cycles": data.get("cycles"), "terrain_params": data.get("terrain_params", {})},
    )


def evaluate_g5(simson_dir: Path) -> dict:
    path = simson_dir / "results_ultra2_axis0_ab_stage16_axis6.json"
    data = load_json(path)
    stage16 = data.get("stage16", {})
    ds_values = []
    dp_values = []
    for record in stage16.values():
        if isinstance(record, dict):
            if "dS" in record:
                ds_values.append(abs(float(record["dS"])))
            if "dP" in record:
                dp_values.append(abs(float(record["dP"])))
    ds_absmax = max(ds_values) if ds_values else 0.0
    dp_absmax = max(dp_values) if dp_values else 0.0
    passed = len(stage16) == 48 and ds_absmax >= 0.0025 and dp_absmax >= 0.0020
    return gate_result(
        passed=passed,
        value={"stage16_len": len(stage16), "stage16_dS_absmax": ds_absmax, "stage16_dP_absmax": dp_absmax},
        threshold={"stage16_len": "== 48", "stage16_dS_absmax": ">= 0.0025", "stage16_dP_absmax": ">= 0.0020"},
        source=str(path),
        details={"axis0_cycles": data.get("axis0_cycles"), "axis0_trials": data.get("axis0_trials")},
    )


def evaluate_g6(simson_dir: Path) -> dict:
    path = simson_dir / "results_axis0_traj_corr_postinit.json"
    data = load_json(path)
    bell = data["BELL_SEQ01"]
    ginibre = data["GINIBRE_SEQ01"]
    bell_postinit_neg_frac = float(bell["SAgB_postinit_neg_frac"])
    bell_postinit_min = float(bell["SAgB_postinit_min"])
    ginibre_postinit_neg_frac = float(ginibre["SAgB_postinit_neg_frac"])
    ginibre_postinit_min = float(ginibre["SAgB_postinit_min"])
    passed = (
        bell_postinit_neg_frac >= 0.08
        and bell_postinit_min < 0.0
        and ginibre_postinit_neg_frac <= 0.001
        and ginibre_postinit_min > 0.0
    )
    return gate_result(
        passed=passed,
        value={
            "bell_seq01_SAgB_postinit_neg_frac": bell_postinit_neg_frac,
            "bell_seq01_SAgB_postinit_min": bell_postinit_min,
            "ginibre_seq01_SAgB_postinit_neg_frac": ginibre_postinit_neg_frac,
            "ginibre_seq01_SAgB_postinit_min": ginibre_postinit_min,
        },
        threshold={
            "bell_seq01_SAgB_postinit_neg_frac": ">= 0.08",
            "bell_seq01_SAgB_postinit_min": "< 0.0",
            "ginibre_seq01_SAgB_postinit_neg_frac": "<= 0.001",
            "ginibre_seq01_SAgB_postinit_min": "> 0.0",
        },
        source=str(path),
        details={"trials": data.get("trials"), "cycles": data.get("cycles"), "terrain_params": data.get("terrain_params", {})},
    )


def _collect_seq01_neg_fracs(axis0_ab: dict, needle: str) -> list[float]:
    values = []
    for key, record in axis0_ab.items():
        if needle in key and key.endswith("SEQ01") and isinstance(record, dict) and "neg_SAgB_frac_traj" in record:
            values.append(float(record["neg_SAgB_frac_traj"]))
    return values


def evaluate_g7(simson_dir: Path, bell_min_neg_frac: float) -> dict:
    path = simson_dir / "results_ultra4_full_stack.json"
    data = load_json(path)
    bell_values = _collect_seq01_neg_fracs(data.get("axis0_ab", {}), "_BELL_")
    best = max(bell_values) if bell_values else 0.0
    passed = best >= 0.09
    return gate_result(
        passed=passed,
        value={"bell_seq01_neg_SAgB_frac_traj_max": best},
        threshold={"bell_seq01_neg_SAgB_frac_traj_max": ">= 0.09"},
        source=str(path),
        details={"bell_seq01_count": len(bell_values)},
    )


def evaluate_g8(simson_dir: Path, separation_ratio: float) -> dict:
    path = simson_dir / "results_ultra4_full_stack.json"
    data = load_json(path)
    axis0_ab = data.get("axis0_ab", {})
    bell_values = _collect_seq01_neg_fracs(axis0_ab, "_BELL_")
    ginibre_values = _collect_seq01_neg_fracs(axis0_ab, "_GINIBRE_")
    bell_mean = sum(bell_values) / len(bell_values) if bell_values else 0.0
    ginibre_mean = sum(ginibre_values) / len(ginibre_values) if ginibre_values else 0.0
    ratio = bell_mean / ginibre_mean if ginibre_mean > 0.0 else None
    passed = ratio is not None and ratio >= 1000.0
    return gate_result(
        passed=passed,
        value={"bell_mean": bell_mean, "ginibre_mean": ginibre_mean, "ratio": ratio},
        threshold={"bell_to_ginibre_ratio": ">= 1000.0"},
        source=str(path),
        details={"bell_seq01_count": len(bell_values), "ginibre_seq01_count": len(ginibre_values)},
    )


def evaluate_g9(simson_dir: Path) -> dict:
    path = simson_dir / "results_ultra4_full_stack_postinit.json"
    data = load_json(path)
    bell = data["axis0_ab_postinit"]["T1_FWD_BELL_CNOT_R1_SEQ01"]
    ginibre = data["axis0_ab_postinit"]["T1_FWD_GINIBRE_CNOT_R1_SEQ01"]
    bell_postinit_neg_frac = float(bell["SAgB_postinit_neg_frac"])
    bell_postinit_min = float(bell["SAgB_postinit_min"])
    ginibre_postinit_neg_frac = float(ginibre["SAgB_postinit_neg_frac"])
    ginibre_postinit_min = float(ginibre["SAgB_postinit_min"])
    passed = (
        bell_postinit_neg_frac >= 0.08
        and bell_postinit_min < 0.0
        and ginibre_postinit_neg_frac <= 0.001
        and ginibre_postinit_min > 0.0
    )
    return gate_result(
        passed=passed,
        value={
            "bell_seq01_SAgB_postinit_neg_frac": bell_postinit_neg_frac,
            "bell_seq01_SAgB_postinit_min": bell_postinit_min,
            "ginibre_seq01_SAgB_postinit_neg_frac": ginibre_postinit_neg_frac,
            "ginibre_seq01_SAgB_postinit_min": ginibre_postinit_min,
        },
        threshold={
            "bell_seq01_SAgB_postinit_neg_frac": ">= 0.08",
            "bell_seq01_SAgB_postinit_min": "< 0.0",
            "ginibre_seq01_SAgB_postinit_neg_frac": "<= 0.001",
            "ginibre_seq01_SAgB_postinit_min": "> 0.0",
        },
        source=str(path),
        details={"axis0_trials": data.get("axis0_trials"), "axis0_cycles": data.get("axis0_cycles"), "tparams_ab": data.get("tparams_ab", {})},
    )


def build_summary(gates: dict[str, dict]) -> dict:
    passed = sum(1 for gate in gates.values() if gate["passed"])
    total = len(gates)
    return {
        "score": passed / total if total else 0.0,
        "passed_gates": passed,
        "total_gates": total,
        "failed_gate_ids": [gate_id for gate_id, gate in gates.items() if not gate["passed"]],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate pre-Axis0 geometry witness tiers from existing sim results.")
    parser.add_argument("--simson-dir", type=Path, default=DEFAULT_SIMSON_DIR)
    parser.add_argument("--min-neg-frac", type=float, default=0.001)
    parser.add_argument("--bell-min-neg-frac", type=float, default=0.09)
    parser.add_argument("--separation-ratio", type=float, default=1000.0)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    simson_dir = args.simson_dir
    gates = {
        "G1_tiny_negative_support": evaluate_g1(simson_dir, args.min_neg_frac),
        "G2_tiny_matched_control": evaluate_g2(simson_dir),
        "G3_entangled_seed_branch": evaluate_g3(simson_dir, args.min_neg_frac),
        "G4_bell_vs_ginibre_trajectory": evaluate_g4(simson_dir, args.min_neg_frac),
        "G5_stage16_geometry_structure": evaluate_g5(simson_dir),
        "G6_postinit_bell_vs_ginibre_trajectory": evaluate_g6(simson_dir),
        "G7_full_geometry_bell_negativity": evaluate_g7(simson_dir, args.bell_min_neg_frac),
        "G8_full_geometry_bell_vs_ginibre_separation": evaluate_g8(simson_dir, args.separation_ratio),
        "G9_full_geometry_postinit_bell_vs_ginibre": evaluate_g9(simson_dir),
    }
    payload = {
        "summary": build_summary(gates),
        "gates": gates,
    }
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
