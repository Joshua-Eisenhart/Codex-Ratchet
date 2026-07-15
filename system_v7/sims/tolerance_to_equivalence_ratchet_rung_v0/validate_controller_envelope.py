#!/usr/bin/env python3
"""Independent pure-Python reconstruction and source-binding validator."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[2]
DEFAULT_ENVELOPE = SIM_DIR / "results" / "controller_envelope.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def relation_from_mask(n: int, mask: int) -> list[list[bool]]:
    relation = [[i == j for j in range(n)] for i in range(n)]
    bit = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            value = bool((mask >> bit) & 1)
            relation[i][j] = value
            relation[j][i] = value
            bit += 1
    return relation


def transitive(relation: list[list[bool]]) -> bool:
    n = len(relation)
    return not any(relation[i][j] and relation[j][k] and not relation[i][k] for i in range(n) for j in range(n) for k in range(n))


def census() -> dict[str, dict[str, int]]:
    observed = {}
    for n in range(1, 6):
        total = 1 << (n * (n - 1) // 2)
        equivalences = sum(transitive(relation_from_mask(n, mask)) for mask in range(total))
        observed[str(n)] = {"tolerances": total, "equivalences": equivalences, "nontransitive": total - equivalences}
    return observed


def expected_witness() -> dict[str, Any]:
    return {
        "raw_transitive": False,
        "closure_labels": [0, 0, 0],
        "forced_endpoint_related": True,
        "closure_matrix": [[True, True, True], [True, True, True], [True, True, True]],
    }


def expected_drive() -> dict[str, Any]:
    return {
        "raw_closure": [
            [True, True, False, False],
            [True, True, False, False],
            [False, False, True, True],
            [False, False, True, True],
        ],
        "initial_labels": [0, 0, 0, 0],
        "proposal_labels": [0, 0, 1, 1],
        "initial_coface_loss": 1,
        "proposal_coface_loss": 0,
        "drive": 1,
        "decision": "COMMIT_TOOTH",
        "controls": {
            "reverse_drive": -1,
            "reverse_decision": "HOLD",
            "null_drive": 0,
            "null_decision": "HOLD",
            "universal_proposal_drive": 0,
            "universal_proposal_decision": "HOLD",
            "scrambled_drive": 0,
            "scrambled_decision": "HOLD",
            "flat_drive": 0,
            "flat_decision": "HOLD",
        },
        "mss_antichain": [
            {"labels": [0, 0, 1, 1], "added_pair_count": 0, "quotient_class_count": 2},
            {"labels": [0, 0, 0, 0], "added_pair_count": 4, "quotient_class_count": 1},
        ],
    }


def validate(envelope_path: Path) -> tuple[bool, list[str], dict[str, Any]]:
    findings: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            findings.append(message)

    envelope = load(envelope_path)
    spec = load(SIM_DIR / "spec.json")
    prereg = load(SIM_DIR / "preregistration_receipt.json")
    wizard = load(SIM_DIR / "wizard_v4_3_validation.json")
    recomputed_census = census()
    require(sha256(SIM_DIR / "spec.json") == prereg.get("spec_sha256"), "preregistered spec hash mismatch")
    require(sha256(SIM_DIR / "wizard_v4_3_object_card.json") == prereg.get("object_card_sha256"), "preregistered object-card hash mismatch")
    require(wizard.get("ok") is True and not wizard.get("errors"), "Wizard v4.3 object-card validation is not green")
    require(recomputed_census == spec["root_contract"]["expected_census"], "independent census disagrees with frozen spec")
    require(envelope.get("classification") == "scratch_diagnostic", "classification ceiling changed")
    require(envelope.get("promotion_allowed") is False, "promotion flag opened")
    require(envelope.get("formal_admission_allowed") is False, "formal-admission flag opened")
    require(envelope.get("llm_verdict_used") is False, "LLM verdict entered the gate")
    controller_path = ROOT / envelope.get("controller_source_path", "missing")
    require(controller_path.is_file(), "controller source missing")
    require(controller_path.is_file() and sha256(controller_path) == envelope.get("controller_source_sha256"), "controller source hash mismatch")
    result_paths = {
        "julia": SIM_DIR / "results" / "julia_results.json",
        "jax": SIM_DIR / "results" / "jax_results.json",
        "pytorch": SIM_DIR / "results" / "pytorch_results.json",
        "proof": SIM_DIR / "results" / "proof_results.json",
    }
    peers = {
        "julia": ["jax_results.json", "pytorch_results.json", "proof_results.json"],
        "jax": ["julia_results.json", "pytorch_results.json", "proof_results.json"],
        "pytorch": ["julia_results.json", "jax_results.json", "proof_results.json"],
        "proof": ["julia_results.json", "jax_results.json", "pytorch_results.json"],
    }
    disk_payloads: dict[str, dict[str, Any]] = {}
    for name, result_path in result_paths.items():
        require(result_path.is_file(), f"{name} result missing")
        if not result_path.is_file():
            continue
        payload = load(result_path)
        disk_payloads[name] = payload
        entry = envelope.get("engines", {}).get(name, {})
        require(entry.get("payload") == payload, f"{name} embedded payload differs from closed result")
        require(entry.get("result_sha256") == sha256(result_path), f"{name} result hash mismatch")
        source = ROOT / payload.get("source_path", "missing")
        require(source.is_file(), f"{name} source missing")
        require(source.is_file() and sha256(source) == payload.get("source_sha256"), f"{name} source hash mismatch")
        require(payload.get("reads_peer_result") is False, f"{name} reports a peer-result read")
        require(payload.get("all_pass") is True, f"{name} local result red")
        require(payload.get("classification") == "scratch_diagnostic", f"{name} classification changed")
        require(payload.get("promotion_allowed") is False and payload.get("formal_admission_allowed") is False, f"{name} admission fence opened")
        if source.is_file():
            text = source.read_text(encoding="utf-8")
            for token in peers[name]:
                require(token not in text, f"{name} source contains peer-result token {token}")
            require("import numpy" not in text and "from numpy" not in text, f"{name} imported NumPy on the claim path")
    expected_relation = expected_witness()
    expected_drive_record = expected_drive()
    for name in ("julia", "jax", "pytorch"):
        payload = disk_payloads.get(name, {})
        require(payload.get("census") == recomputed_census, f"{name} census mismatch")
        require(payload.get("transitivity_witness") == expected_relation, f"{name} transitivity witness mismatch")
        require(payload.get("drive_fixture") == expected_drive_record, f"{name} drive/MSS/control record mismatch")
    proof = disk_payloads.get("proof", {})
    expected_queries = {
        "sat_equivalence_containing_chain": "sat",
        "endpoint_negation_under_transitivity": "unsat",
        "strict_subclosure_containing_raw": "unsat",
        "drop_transitivity_endpoint_absent": "sat",
    }
    require(proof.get("free_boolean_relation_variables") is True and proof.get("ground_literal_only") is False, "proof variables are not free relation variables")
    require(proof.get("z3", {}).get("queries") == expected_queries, "z3 query vector mismatch")
    require(proof.get("cvc5", {}).get("queries") == expected_queries, "cvc5 query vector mismatch")
    commands = envelope.get("commands", [])
    require(len(commands) == 6 and all(item.get("returncode") == 0 and item.get("pass") is True for item in commands), "controller command vector is not six clean exits")
    for item in commands:
        command = item.get("command", [])
        require(bool(command) and Path(command[0]).is_absolute(), f"{item.get('label')} executable is not absolute")
        lowered = " ".join(command).lower()
        require(not any(token in lowered for token in ("claude", "openai", "anthropic", "nvidia", "xai", "--model")), f"{item.get('label')} invokes a model/provider surface")
    require(all(envelope.get("checks", {}).values()) and len(envelope.get("checks", {})) == 9, "controller G0-G8 vector not fully green")
    require(envelope.get("drive") == expected_drive_record, "envelope drive differs from independent reconstruction")
    require(envelope.get("mss_antichain") == expected_drive_record["mss_antichain"], "envelope MSS antichain mismatch")
    require(envelope.get("all_pass") is True, "controller all_pass is not true")
    require(envelope.get("decision") == "COMMIT_TOOTH_CANDIDATE", "controller candidate decision changed")
    require(envelope.get("ratchet_state_after") == "TOOTH_1_CANDIDATE", "candidate state changed")
    require(envelope.get("claim_ceiling") == spec["accepted_green_ceiling"], "claim ceiling mismatch")
    require(envelope.get("pending_gates") == ["G9 independent mutation rejection", "G10 deterministic Lev replay"], "pending gate boundary changed")
    summary = {
        "independent_census": recomputed_census,
        "expected_witness": expected_relation,
        "expected_drive": expected_drive_record,
        "checked_engine_count": len(disk_payloads),
    }
    return not findings, findings, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--envelope", type=Path, default=DEFAULT_ENVELOPE)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    ok, findings, summary = validate(args.envelope.resolve())
    receipt = {
        "schema": "codex_ratchet.tolerance_to_equivalence.validation.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "envelope_path": str(args.envelope.resolve()),
        "envelope_sha256": sha256(args.envelope.resolve()),
        "ok": ok,
        "finding_count": len(findings),
        "findings": findings,
        "summary": summary,
        "claim_ceiling": "artifact-valid bounded scratch rung only; G9 and G10 remain separate",
    }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
