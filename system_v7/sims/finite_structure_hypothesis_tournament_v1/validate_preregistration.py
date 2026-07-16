#!/usr/bin/env python3
"""Fail-closed preregistration validator for the frozen v1 tournament."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SPEC = ROOT / "spec.json"
CARD = ROOT / "wizard_v4_3_object_card.json"


def strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name: str, condition: bool, detail: object) -> dict[str, object]:
    return {"name": name, "pass": bool(condition), "detail": detail}


def validate() -> dict[str, object]:
    spec = load_json(SPEC)
    card = load_json(CARD)
    primary = card["primary_object_card"]
    checks: list[dict[str, object]] = []

    statement = str(primary["object_statement"])
    statement_hash = hashlib.sha256(statement.encode("utf-8")).hexdigest()
    checks.append(check("object_statement_hash", statement_hash == primary["object_statement_sha256"], statement_hash))
    checks.append(check("spec_frozen", str(spec["spec_status"]).startswith("frozen_before_execution"), spec["spec_status"]))
    checks.append(check("scratch_only", spec["classification"] == "scratch_diagnostic" and not spec["promotion_candidate"] and not spec["formal_admission_candidate"], spec["classification"]))

    bounds = spec["execution_bounds"]
    observed_counts = {str(n): 2 ** (n * n) for n in bounds["exhaustive_carrier_sizes"]}
    checks.append(check("relation_counts", observed_counts == bounds["binary_relation_count_by_exhaustive_size"], observed_counts))
    checks.append(check("no_search_or_ratchet_execution", bounds["search_steps_run"] == 0 and bounds["ratchet_epochs_run"] == 0, {"search_steps_run": bounds["search_steps_run"], "ratchet_epochs_run": bounds["ratchet_epochs_run"]}))
    checks.append(check("no_randomness", bounds["random_seeds"] == [] and spec["candidate_grammar"]["proposal_randomness"] == "none", spec["candidate_grammar"]["proposal_randomness"]))

    mode = spec["engine_mode"]
    checks.append(check("pytorch_omission_explicit", str(mode["pytorch"]).startswith("not_scoped_by_mode"), mode["pytorch"]))
    checks.append(check("engine_independent_construction", "constructs candidates and permutations from spec.json" in mode["cross_runtime_rule"], mode["cross_runtime_rule"]))

    native_logic = json.dumps(
        {
            "candidate_grammar": spec["candidate_grammar"],
            "preorders": spec["presumption_preorders"],
            "viability": spec["viability_predicates"],
            "mss": spec["mss_rule"],
            "stop_rule": bounds["stop_rule"],
        },
        sort_keys=True,
    ).lower()
    leaked = [token for token in ["axis0", "axis 0", "cosmology", "physics", "qit engine", "two-engine"] if token in native_logic]
    checks.append(check("downstream_target_sealed_from_native_logic", leaked == [], leaked))

    root_ids = [entry["id"] for entry in spec["candidate_grammar"]["root_presentations"]]
    checks.append(check("root_presentations_exact", root_ids == ["U_n", "J_n", "C_n", "K0_n"], root_ids))
    checks.append(check("jc_semantics_separate", spec["candidate_grammar"]["root_presentations"][1]["semantic_type"] != spec["candidate_grammar"]["root_presentations"][2]["semantic_type"], [spec["candidate_grammar"]["root_presentations"][1]["semantic_type"], spec["candidate_grammar"]["root_presentations"][2]["semantic_type"]]))
    checks.append(check("registry_identity_frozen", "semantic_type" in spec["candidate_grammar"]["registry_identity"] and "aliases" in spec["candidate_grammar"]["alias_policy"], {"registry_identity": spec["candidate_grammar"]["registry_identity"], "alias_policy": spec["candidate_grammar"]["alias_policy"]}))
    stochastic = next(row for row in spec["presumption_preorders"] if row["id"] == "stochastic_neutrality")
    checks.append(check("stochastic_metrics_exact", all(key in stochastic for key in ["source_dependence_distance", "destination_bias_distance", "arithmetic"]) and stochastic["arithmetic"].startswith("exact rationals"), stochastic))
    checks.append(check("typed_entropy_separation", spec["entropy_capacity_readouts"]["K0_fixed_n_state_entropy_change"] == "exactly zero" and "none is a drive" in spec["entropy_capacity_readouts"]["causal_status"], spec["entropy_capacity_readouts"]["causal_status"]))

    source_locks = card["evidence_spine"]["source_math_locks"]
    missing_sources = [entry["path"] for entry in source_locks if not (REPO / entry["path"]).exists()]
    checks.append(check("source_math_locks_exist", missing_sources == [], missing_sources))
    ceiling_lower = spec["claim_ceiling"].lower()
    checks.append(
        check(
            "claim_ceiling_blocks_basin_qit",
            all(token in ceiling_lower for token in ["basin", "qit", "ontolog"]),
            spec["claim_ceiling"],
        )
    )

    errors = [entry for entry in checks if not entry["pass"]]
    return {
        "schema_version": "finite_structure_hypothesis_tournament.preregistration.v1",
        "all_pass": not errors,
        "classification": "preregistration_validation_only",
        "claim_ceiling": "Frozen-object and source-boundary validation only; no simulation, proof, frontier, Ratchet, basin, QIT, ontology, cosmology, or physics claim.",
        "command": [sys.executable, str(Path(__file__).resolve()), "--out", str((ROOT / "preregistration_receipt.json").resolve())],
        "cwd": os.getcwd(),
        "runner_identity": {"implementation": platform.python_implementation(), "python": platform.python_version(), "executable": sys.executable},
        "runtime": {"platform": platform.platform()},
        "source_sha256": sha256(Path(__file__).resolve()),
        "spec_sha256": sha256(SPEC),
        "object_card_sha256": sha256(CARD),
        "checks": checks,
        "errors": errors,
        "blocked_consumers": spec["blocked_consumers"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = validate()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
