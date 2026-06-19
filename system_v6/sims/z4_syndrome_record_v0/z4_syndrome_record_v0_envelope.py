#!/usr/bin/env python3
"""Controller envelope for z4_syndrome_record_v0.

The envelope shape is built through scripts/build_three_engine_envelope.py.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SIM_ID = "z4_syndrome_record_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = PACKET / "results"
SOURCE = PACKET / f"{SIM_ID}_envelope.py"
RESULT = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
ENGINES = ["julia", "jax", "pytorch"]

sys.path.insert(0, str(ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load_leg(engine: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def git_bytes(spec: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{spec}"], cwd=ROOT)


def git_rev(spec: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{spec}"], cwd=ROOT, text=True).strip()


def parent_lineage() -> dict[str, Any]:
    parents = {
        "manifold_information_throughput_v0": {
            "path": "system_v6/sims/manifold_information_throughput_v0/audit_verdict.md",
            "allowed_use": "hard Q1 caveat target; this packet resolves packet-local Z4 syndrome object only",
        },
        "ratchet_deep_chain_v0": {
            "path": "system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json",
            "allowed_use": "parent Z4 quotient generator alpha += pi/2 and orbit_order 4",
        },
        "compression_flow_radiated_record_v0": {
            "path": "system_v6/sims/compression_flow_radiated_record_v0/results/compression_flow_radiated_record_v0_envelope_results.json",
            "allowed_use": "record reconstruction/control row pattern only",
        },
        "manifold_entropy_ledger_v0": {
            "path": "system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json",
            "allowed_use": "typed entropy separation; finite counting entropy label discipline",
        },
    }
    out: dict[str, Any] = {}
    for name, row in parents.items():
        payload = git_bytes(row["path"])
        out[name] = {
            "path": row["path"],
            "blob": git_rev(row["path"]),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "allowed_use": row["allowed_use"],
            "source": "git show HEAD:<path>",
        }
    return out


def lane_record(leg: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": leg["result_path"],
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": leg["package_observables"],
        "all_pass": leg["all_pass"],
        "role_id": leg["role_id"],
        "claim_path_tools": leg["claim_path_tools"],
        "tool_calls": leg["tool_calls"],
    }


def max_abs_delta(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0


def build_result() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ENGINES}
    jax_regimes = legs["jax"]["regimes"]
    shared_keys = [
        ("positive", "state_loss_without_record_nats"),
        ("positive", "record_retained_nats"),
        ("positive", "computed_defect_nats"),
        ("negative_erased_record", "computed_defect_nats"),
        ("negative_partial_record", "computed_defect_nats"),
        ("boundary_trivial_quotient", "state_loss_without_record_nats"),
    ]
    shared_value_deltas = {
        f"{regime}.{field}": max_abs_delta([float(legs[engine]["regimes"][regime][field]) for engine in ENGINES])
        for regime, field in shared_keys
    }
    reconstruction_failures = {
        engine: legs[engine]["reconstruction"]["with_quotient_and_syndrome"]["failure_count"] for engine in ENGINES
    }
    quotient_ambiguity = {
        engine: legs[engine]["reconstruction"]["quotient_alone"]["computed_ambiguity"] for engine in ENGINES
    }
    shuffled_failure_rate = {
        engine: legs[engine]["controls"]["shuffled_syndrome"]["failure_rate"] for engine in ENGINES
    }
    regime_hashes = {
        name: jax_regimes[name]["row_hash"]
        for name in ["positive", "negative_erased_record", "negative_partial_record", "boundary_trivial_quotient"]
    }
    controls = {
        "erased_record": {engine: legs[engine]["controls"]["erased_record"] for engine in ENGINES},
        "partial_record_one_bit": {engine: legs[engine]["controls"]["partial_record_one_bit"] for engine in ENGINES},
        "shuffled_syndrome": {engine: legs[engine]["controls"]["shuffled_syndrome"] for engine in ENGINES},
        "trivial_quotient": {engine: legs[engine]["controls"]["trivial_quotient"] for engine in ENGINES},
    }
    z3 = legs["jax"]["crossover_proofs"]["z3"]["full_record"]
    cvc5 = legs["jax"]["crossover_proofs"]["cvc5"]["full_record"]
    julia_z3 = legs["julia"]["crossover_proofs"]["julia_z3"]["full_record"]
    all_pass = all(
        [
            all(legs[engine]["all_pass"] for engine in ENGINES),
            all(delta == 0.0 for delta in shared_value_deltas.values()),
            all(value == 0 for value in reconstruction_failures.values()),
            all(value == 4 for value in quotient_ambiguity.values()),
            all(value == 1.0 for value in shuffled_failure_rate.values()),
            len(set(regime_hashes.values())) == 4,
            z3["verdict"] == "unsat",
            cvc5["verdict"] == "unsat",
            legs["jax"]["crossover_proofs"]["z3"]["erased_record_control"]["verdict"] == "sat",
            legs["jax"]["crossover_proofs"]["z3"]["partial_record_control"]["verdict"] == "sat",
            legs["jax"]["crossover_proofs"]["cvc5"]["erased_record_control"]["verdict"] == "sat",
            legs["jax"]["crossover_proofs"]["cvc5"]["partial_record_control"]["verdict"] == "sat",
            julia_z3["verdict"] == "unsat",
        ]
    )
    lanes = {engine: lane_record(legs[engine]) for engine in ENGINES}
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "result_path": rel(RESULT),
        "all_pass": all_pass,
        "claim": "packet-local Z4 syndrome record object closes quotient loss only when the constructed syndrome is retained",
        "allowed_claims": [
            "packet-local Z4 syndrome/preimage table over the pinned state family",
            "finite counting entropy state-loss and record-retention row with separate code paths",
            "bit-exact reconstruction with quotient output plus syndrome",
            "computed erased, partial, shuffled, and trivial boundary controls",
        ],
        "disallowed_claims": [
            "formal admission",
            "canonical manifold theorem",
            "universal entropy scalar",
            "cross-type entropy conservation outside the finite state-plus-record bookkeeping convention",
        ],
        "typed_entropy_discipline": {
            "all_rows_label": "finite_counting_entropy_nats",
            "log_base": "e",
            "cross_type_sum": False,
            "product_bookkeeping_convention": "state quotient loss and retained finite syndrome record are compared within the same finite representative table",
        },
        "syndrome_table": legs["jax"]["syndrome_table"],
        "regimes": jax_regimes,
        "controls": controls,
        "reconstruction": {
            "with_quotient_and_syndrome": {engine: legs[engine]["reconstruction"]["with_quotient_and_syndrome"] for engine in ENGINES},
            "quotient_alone": {engine: legs[engine]["reconstruction"]["quotient_alone"] for engine in ENGINES},
        },
        "shared_value_deltas": shared_value_deltas,
        "regime_hashes": regime_hashes,
        "regime_hashes_distinct": len(set(regime_hashes.values())) == 4,
        "julia_z3_controls": legs["julia"]["crossover_proofs"]["julia_z3"],
        "jax_proof_controls": legs["jax"]["crossover_proofs"],
        "pytorch_proof_controls": legs["pytorch"]["crossover_proofs"],
        "tool_intent": {
            "claim_classes": ["finite_counting_entropy", "z4_syndrome_record", "smt_conservation_control"],
            "engine_tool_intent": {
                "julia": legs["julia"]["package_observables"],
                "jax": legs["jax"]["package_observables"],
                "pytorch": legs["pytorch"]["package_observables"],
            },
        },
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {
                "used": True,
                "reason": "load-bearing controller envelope construction through the standard helper",
            },
            "json": {"used": True, "reason": "supportive controller serialization"},
            "hashlib": {"used": True, "reason": "supportive lineage and row hashes"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            "json": "supportive",
            "hashlib": "supportive",
        },
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(PACKET / ('validate_' + SIM_ID + '.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed {rel(RESULT)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent {rel(RESULT)}",
        ],
    }
    envelope = build_envelope(
        sim_id=SIM_ID,
        lanes=lanes,
        mode="all_three_full_sims",
        claim_path_tools=["Graphs", "Z3", "sympy", "z3", "cvc5", "torch_geometric", "torch.func"],
        crossover_proofs={"z3": z3, "cvc5": cvc5, "julia_z3": julia_z3},
        divergence={
            "julia_authoritative": True,
            "observable": "positive.computed_defect_nats",
            "engine_values": {
                engine: legs[engine]["regimes"]["positive"]["computed_defect_nats"] for engine in ENGINES
            },
            "max_divergence": max_abs_delta(
                [float(legs[engine]["regimes"]["positive"]["computed_defect_nats"]) for engine in ENGINES]
            ),
            "shared_value_deltas": shared_value_deltas,
        },
        parent_lineage=parent_lineage(),
        expected_lanes=ENGINES,
        stability_pairs=[{"subtree": "regime_hashes", "hash": stable_hash(regime_hashes)}],
        generated_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        extra_fields=extra_fields,
    )
    return envelope


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

