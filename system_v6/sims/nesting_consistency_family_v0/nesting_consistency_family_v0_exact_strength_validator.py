#!/usr/bin/env python3
"""Packet-local validator for nesting_consistency_family_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "nesting_consistency_family_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_PATH = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
ALLOWED_STRENGTHS = {
    "diagnostic_family_comparison",
    "exact_integer_combinatorial",
    "exact_smt",
    "finite_exhaustive_enumeration",
    "pointwise_exact_sample",
    "symbolic_identity",
}
REQUIRED_ARROW_TYPES = {
    "tensor",
    "algebra extension",
    "quotient",
    "principal-bundle / fibration",
    "subset/submanifold",
    "filtration",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def arrow_types_in(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        if "arrow_type" in value:
            raw = value["arrow_type"]
            if isinstance(raw, list):
                found.update(str(item) for item in raw)
            else:
                found.add(str(raw))
        for child in value.values():
            found.update(arrow_types_in(child))
    elif isinstance(value, list):
        for child in value:
            found.update(arrow_types_in(child))
    return found


def main() -> int:
    envelope = load(RESULT_PATH)
    require(envelope["all_pass"] is True, "envelope all_pass is false")
    require(envelope["classification"] == "scratch_diagnostic", "classification drift")
    require(envelope["promotion_allowed"] is False, "promotion_allowed drift")
    require(envelope["formal_admission_allowed"] is False, "formal_admission_allowed drift")
    require(envelope["divergence"]["max_divergence"] == 0, "nonzero divergence")
    for gate_name, gate in envelope["build_gates"].items():
        require(gate["pass"] is True, f"build gate failed: {gate_name}")

    engine_payloads = {}
    for engine, path_text in envelope["engine_result_paths"].items():
        path = ROOT / path_text
        payload = load(path)
        engine_payloads[engine] = payload
        require(payload["source_sha256"] == file_sha256(ROOT / payload["source_path"]), f"{engine} source sha drift")
        require(set(payload["strength_tokens"]) <= ALLOWED_STRENGTHS, f"{engine} non-literal strength token")
        require(payload["controls"]["self_check_is_not_evidence"] is True, f"{engine} self-check boundary missing")
        require(payload["shared_scalars"]["GHZ3_Tr_last_nonzero_spectrum"] == "1/2|1/2", f"{engine} GHZ spectrum drift")
        require(payload["shared_scalars"]["W4_Tr_last_weights"] == "3/4|1/4", f"{engine} W weights drift")
        require(payload["shared_scalars"]["product4_Tr_middle_nonzero_spectrum"] == "1", f"{engine} product spectrum drift")
        require(payload["shared_scalars"]["cluster4_Tr_last_nonzero_spectrum"] == "1/2|1/2", f"{engine} cluster spectrum drift")
        require(payload["shared_scalars"]["promoted_variant"] == "None", f"{engine} promoted a variant")
        require(REQUIRED_ARROW_TYPES & arrow_types_in(payload["receipts"]), f"{engine} arrow types missing")

    shared_sets = {json.dumps(payload["shared_scalars"], sort_keys=True) for payload in engine_payloads.values()}
    require(len(shared_sets) == 1, "engine shared scalar sets differ")
    require(set(envelope["family_comparison"]["what_breaks"]) == {"GHZ", "W", "linear_cluster"}, "family break table drift")
    require(envelope["family_comparison"]["promoted_variant"] is None, "family comparison promoted a variant")

    print(json.dumps({"ok": True, "result_json": str(RESULT_PATH.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
