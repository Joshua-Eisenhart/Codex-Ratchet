#!/usr/bin/env python3
"""Packet-local validator for z4_syndrome_record_v0."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any


SIM_ID = "z4_syndrome_record_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = PACKET / "results" / f"{SIM_ID}_envelope_results.json"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], name: str) -> dict[str, Any]:
    require(isinstance(value, dict), errors, f"{name} must be an object")
    return value if isinstance(value, dict) else {}


def close_to(value: float, target: float, tol: float = 1e-12) -> bool:
    return abs(float(value) - target) <= tol


def main() -> int:
    result_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RESULT
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema version mismatch")
    require(payload.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification mismatch")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")
    require(set(payload.get("engines", {})) == {"julia", "jax", "pytorch"}, errors, "all three engines required")

    table = payload.get("syndrome_table")
    require(isinstance(table, list) and len(table) == 24, errors, "syndrome table must have 24 rows")
    if isinstance(table, list):
        by_orbit: dict[str, set[int]] = {}
        for row in table:
            if isinstance(row, dict):
                by_orbit.setdefault(str(row.get("orbit_id")), set()).add(int(row.get("syndrome", -1)))
        require(len(by_orbit) == 6, errors, "six pinned orbits required")
        require(all(syndromes == {0, 1, 2, 3} for syndromes in by_orbit.values()), errors, "each orbit must have four syndrome reps")

    regimes = as_dict(payload.get("regimes"), errors, "regimes")
    positive = as_dict(regimes.get("positive"), errors, "regimes.positive")
    erased = as_dict(regimes.get("negative_erased_record"), errors, "regimes.negative_erased_record")
    partial = as_dict(regimes.get("negative_partial_record"), errors, "regimes.negative_partial_record")
    trivial = as_dict(regimes.get("boundary_trivial_quotient"), errors, "regimes.boundary_trivial_quotient")
    require(positive.get("different_code_paths") is True, errors, "positive row must use different code paths")
    require(close_to(positive.get("state_loss_without_record_nats", -1), math.log(4)), errors, "positive loss must be ln4")
    require(close_to(positive.get("record_retained_nats", -1), math.log(4)), errors, "positive record must be ln4")
    require(close_to(positive.get("computed_defect_nats", -1), 0.0), errors, "positive defect must be 0")
    require(close_to(erased.get("computed_defect_nats", -1), math.log(4)), errors, "erased defect must be ln4")
    require(close_to(partial.get("computed_defect_nats", -1), math.log(2)), errors, "partial defect must be ln2")
    require(close_to(trivial.get("state_loss_without_record_nats", -1), 0.0), errors, "trivial loss must be 0")
    require(close_to(trivial.get("record_retained_nats", -1), 0.0), errors, "trivial record must be 0")
    for name, row in {"positive": positive, "erased": erased, "partial": partial, "trivial": trivial}.items():
        require(row.get("typed_entropy_label") == "finite_counting_entropy_nats", errors, f"{name} typed entropy label mismatch")

    require(payload.get("regime_hashes_distinct") is True, errors, "regime hashes must be distinct")
    reconstruction = as_dict(payload.get("reconstruction"), errors, "reconstruction")
    with_syndrome = as_dict(reconstruction.get("with_quotient_and_syndrome"), errors, "reconstruction.with_quotient_and_syndrome")
    quotient_alone = as_dict(reconstruction.get("quotient_alone"), errors, "reconstruction.quotient_alone")
    for engine in ["julia", "jax", "pytorch"]:
        require(as_dict(with_syndrome.get(engine), errors, f"with_syndrome.{engine}").get("bit_exact_roundtrip") is True, errors, f"{engine} roundtrip must pass")
        qrow = as_dict(quotient_alone.get(engine), errors, f"quotient_alone.{engine}")
        require(qrow.get("reconstruction_fails") is True, errors, f"{engine} quotient-alone must fail")
        require(qrow.get("computed_ambiguity") == 4, errors, f"{engine} ambiguity must be 4")

    controls = as_dict(payload.get("controls"), errors, "controls")
    for engine in ["julia", "jax", "pytorch"]:
        require(as_dict(controls["shuffled_syndrome"].get(engine), errors, f"shuffled.{engine}").get("failure_rate") == 1.0, errors, f"{engine} shuffled syndrome must fail all rows")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    require(as_dict(proofs.get("z3"), errors, "proofs.z3").get("verdict") == "unsat", errors, "top-level z3 must be unsat")
    require(as_dict(proofs.get("cvc5"), errors, "proofs.cvc5").get("verdict") == "unsat", errors, "top-level cvc5 must be unsat")
    require(as_dict(proofs.get("julia_z3"), errors, "proofs.julia_z3").get("verdict") == "unsat", errors, "julia_z3 must be unsat")
    jax_proofs = as_dict(payload.get("jax_proof_controls"), errors, "jax_proof_controls")
    require(as_dict(as_dict(jax_proofs.get("z3"), errors, "jax.z3").get("erased_record_control"), errors, "jax.z3.erased").get("verdict") == "sat", errors, "z3 erased must be sat")
    require(as_dict(as_dict(jax_proofs.get("cvc5"), errors, "jax.cvc5").get("partial_record_control"), errors, "jax.cvc5.partial").get("verdict") == "sat", errors, "cvc5 partial must be sat")

    require("tool_intent" in payload, errors, "tool_intent/TOOL_INTENT_MATRIX payload missing")
    require("build_three_engine_envelope" in payload.get("TOOL_MANIFEST", {}), errors, "standard envelope helper manifest missing")

    if not errors:
        nested = subprocess.run(
            [
                SIM_PY,
                "scripts/validate_three_engine_sim_result.py",
                "--require-pytorch",
                "--strict-source-backed",
                "--require-tool-intent",
                str(result_path),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        require(nested.returncode == 0, errors, f"nested strict validator failed: {nested.stdout} {nested.stderr}")

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "result_json": str(result_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

