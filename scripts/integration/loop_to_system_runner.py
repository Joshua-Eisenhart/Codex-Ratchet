#!/usr/bin/env python3
"""Run a scratch sim through the real Codex Ratchet gate chain.

This wrapper does not admit or repair sims on its own. It reruns the sim and
then invokes the repository validators/admission scripts as subprocesses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
DEFAULT_SIM = (
    REPO_ROOT
    / "system_v7"
    / "sims"
    / "order_sensitivity_noncommutation_floor_v0"
    / "order_sensitivity_scratch_diagnostic.py"
)
DEFAULT_STAGE_CLAIM = "tool_micro"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sim_python() -> str:
    return os.environ.get("SIM_PY") or str(DEFAULT_SIM_PY)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel_or_abs(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def run_command(args: list[str], *, cwd: Path = REPO_ROOT) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=str(cwd), text=True, capture_output=True, check=False)
    return {
        "command": args,
        "cwd": str(cwd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def result_path_for_sim(sim_path: Path) -> Path:
    return sim_path.with_name(f"{sim_path.stem}_results.json")


def stable_reproduction_signature(payload: dict[str, Any]) -> dict[str, Any]:
    pairs = []
    for pair in payload.get("pairs") or []:
        if not isinstance(pair, dict):
            continue
        pairs.append(
            {
                "pair_id": pair.get("pair_id"),
                "verdict": pair.get("verdict"),
                "differing_configs": pair.get("differing_configs"),
                "z3": pair.get("z3"),
                "cvc5": pair.get("cvc5"),
                "witness_membership": pair.get("witness_membership"),
            }
        )
    return {
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "support": payload.get("support"),
        "initial_partition": payload.get("initial_partition"),
        "all_pass": payload.get("all_pass"),
        "pairs": pairs,
    }


def seat_certify(sim_path: Path) -> tuple[Path, dict[str, Any]]:
    result_path = result_path_for_sim(sim_path)
    before = load_json(result_path) if result_path.exists() else None
    before_signature = stable_reproduction_signature(before) if before else None
    command = run_command([sim_python(), str(sim_path)])
    after = load_json(result_path) if result_path.exists() else {}
    after_signature = stable_reproduction_signature(after)
    required_facts = {
        "result_exists": result_path.exists(),
        "classification_is_scratch_diagnostic": after.get("classification") == "scratch_diagnostic",
        "promotion_allowed_false": after.get("promotion_allowed") is False,
        "all_pass_true": after.get("all_pass") is True,
        "noncommuting_x0_flip": _has_noncommuting_x0_flip(after),
        "commuting_control_trivial": _has_commuting_control(after),
    }
    reproduced = before_signature == after_signature if before_signature is not None else None
    ok = command["exit_code"] == 0 and all(required_facts.values()) and reproduced is not False
    return result_path, {
        "gate": "seat_certify",
        "verdict": "pass" if ok else "reject",
        "ok": ok,
        "result_path": str(result_path),
        "baseline_signature_present": before_signature is not None,
        "stable_signature_reproduced": reproduced,
        "required_facts": required_facts,
        "command": command,
    }


def _has_noncommuting_x0_flip(payload: dict[str, Any]) -> bool:
    for pair in payload.get("pairs") or []:
        if not isinstance(pair, dict) or pair.get("pair_id") != "noncommuting_blur_then_cut_pair":
            continue
        membership = ((pair.get("witness_membership") or {}).get("x0") or {})
        z3_membership = membership.get("z3") or {}
        cvc5_membership = membership.get("cvc5") or {}
        return (
            pair.get("verdict") == "genuine"
            and pair.get("differing_configs") == ["x0"]
            and (pair.get("z3") or {}).get("flip_exists") == "sat"
            and (pair.get("cvc5") or {}).get("flip_exists") == "sat"
            and z3_membership.get("A_then_B") == "unsat"
            and z3_membership.get("B_then_A") == "sat"
            and cvc5_membership.get("A_then_B") == "unsat"
            and cvc5_membership.get("B_then_A") == "sat"
        )
    return False


def _has_commuting_control(payload: dict[str, Any]) -> bool:
    for pair in payload.get("pairs") or []:
        if not isinstance(pair, dict) or pair.get("pair_id") != "commuting_saturated_pair":
            continue
        return (
            pair.get("verdict") == "trivial"
            and pair.get("differing_configs") == []
            and (pair.get("z3") or {}).get("flip_exists") == "unsat"
            and (pair.get("cvc5") or {}).get("flip_exists") == "unsat"
        )
    return False


def three_engine_schema_gap_report(payload: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    if payload.get("schema_version") != "three_engine_sim_result_v1":
        missing.append("schema_version=three_engine_sim_result_v1")
    if payload.get("promotion_allowed") is not False:
        missing.append("promotion_allowed=false")

    engines = payload.get("engines")
    if not isinstance(engines, dict):
        missing.extend(["engines.julia", "engines.jax"])
    else:
        for name in ("julia", "jax"):
            record = engines.get(name)
            if not isinstance(record, dict):
                missing.append(f"engines.{name}")
                continue
            for field in (
                "ran=true",
                "source_path",
                "reads_peer_result=false",
                "packages_used",
                "aligned_packages_load_bearing",
            ):
                key, _, expected = field.partition("=")
                value = record.get(key)
                if expected == "true" and value is not True:
                    missing.append(f"engines.{name}.{field}")
                elif expected == "false" and value is not False:
                    missing.append(f"engines.{name}.{field}")
                elif not expected and not value:
                    missing.append(f"engines.{name}.{field}")

    proofs = payload.get("crossover_proofs")
    if not isinstance(proofs, dict):
        missing.extend(["crossover_proofs.z3", "crossover_proofs.cvc5"])
    else:
        for name in ("z3", "cvc5"):
            record = proofs.get(name)
            if not isinstance(record, dict):
                missing.append(f"crossover_proofs.{name}")
                continue
            if record.get("ran") is not True:
                missing.append(f"crossover_proofs.{name}.ran=true")
            if record.get("verdict") not in {"sat", "unsat"}:
                missing.append(f"crossover_proofs.{name}.verdict=sat|unsat")
            if record.get("load_bearing") is not True and record.get("supportive") is not True:
                missing.append(f"crossover_proofs.{name}.load_bearing_or_supportive=true")

    divergence = payload.get("divergence")
    if not isinstance(divergence, dict):
        missing.extend(
            [
                "divergence.engine_values.julia",
                "divergence.engine_values.jax",
                "divergence.max_divergence",
                "divergence.julia_authoritative=true",
            ]
        )
    else:
        engine_values = divergence.get("engine_values")
        if not isinstance(engine_values, dict) or "julia" not in engine_values:
            missing.append("divergence.engine_values.julia")
        if not isinstance(engine_values, dict) or "jax" not in engine_values:
            missing.append("divergence.engine_values.jax")
        if "max_divergence" not in divergence:
            missing.append("divergence.max_divergence")
        if divergence.get("julia_authoritative") is not True:
            missing.append("divergence.julia_authoritative=true")

    return {
        "schema": (
            "three_engine_sim_result_v1"
            if payload.get("schema_version") == "three_engine_sim_result_v1"
            else "not_three_engine_sim_result_v1"
        ),
        "missing_or_invalid": missing,
    }


def run_three_engine_validator(result_path: Path) -> dict[str, Any]:
    command = run_command(
        [sim_python(), str(REPO_ROOT / "scripts" / "validate_three_engine_sim_result.py"), str(result_path), "--require-source-backed"]
    )
    parsed = parse_json_stdout(command)
    ok = command["exit_code"] == 0 and parsed.get("ok") is True
    payload = load_json(result_path)
    return {
        "gate": "validate_three_engine_sim_result",
        "verdict": "pass" if ok else "reject",
        "ok": ok,
        "real_validator": command,
        "real_validator_json": parsed,
        "schema_gaps": three_engine_schema_gap_report(payload) if not ok else {"missing_or_invalid": []},
    }


def parse_json_stdout(command: dict[str, Any]) -> dict[str, Any]:
    text = str(command.get("stdout") or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"unparsed_stdout": text}


def run_stage_gate(stage_claim: str) -> dict[str, Any]:
    gate_path = REPO_ROOT / "system_v5" / "ops" / "stage_gate.json"
    gate_payload = load_json(gate_path)
    command = run_command([sim_python(), str(REPO_ROOT / "scripts" / "stage_gate.py"), "--claim", stage_claim])
    parsed = parse_json_stdout(command)
    requested = parsed.get("requested_claim") if isinstance(parsed.get("requested_claim"), dict) else {}
    ok = command["exit_code"] == 0 and requested.get("allowed") is True
    return {
        "gate": "stage_gate",
        "verdict": "pass" if ok else "reject",
        "ok": ok,
        "stage_gate_path": str(gate_path),
        "active_stage": gate_payload.get("active_stage"),
        "sim_stage": "scratch_diagnostic",
        "stage_claim_checked": stage_claim,
        "real_stage_gate": command,
        "real_stage_gate_json": parsed,
        "reason": requested.get("reason"),
    }


def build_admission_artifact(*, result_path: Path, basename: str) -> dict[str, Any]:
    result = load_json(result_path)
    return {
        "schema": "wizard_admission_artifact_v1",
        "kind": "admission_artifact",
        "created_at": utc_now(),
        "basename": basename,
        "result_path": str(result_path),
        "result_sha256": sha256(result_path),
        "classification": result.get("classification"),
        "promotion_allowed": result.get("promotion_allowed"),
        "formal_admission_allowed": result.get("formal_admission_allowed"),
        "all_pass": result.get("all_pass"),
        "honest_status": "scratch_diagnostic_reproduced_not_promoted",
    }


def build_admission_payload(
    *,
    repo_root: Path,
    basename: str,
    sim_path: Path,
    result_path: Path,
    artifact_path: Path,
) -> dict[str, Any]:
    sim_rel = rel_or_abs(repo_root, sim_path)
    claim = "finite order-sensitivity scratch diagnostic with z3 and cvc5 flip witness"
    return {
        "schema": "wizard_sim_admission_v4_2",
        "basename": basename,
        "sim_path": sim_rel,
        "status": "queue_ready",
        "admitted_by": "guard.receipt_audit",
        "admission_artifact": str(artifact_path),
        "controller_read_artifacts": [str(artifact_path), str(result_path)],
        "bounded_work_compile_gate": {"status": "ready_for_execution"},
        "sim_packet_compile_gate": {"status": "queue_candidate"},
        "sim_admissibility_gate": {"result": "one_exact_packet"},
        "formal_sim_profile": {
            "stage": "micro",
            "claim": claim,
            "carrier_fixture": "finite six-token survivor partition",
            "exact_tool_or_function": "z3/cvc5 QF_LIA flip-existence and membership queries",
            "positive_check": "noncommuting order pair flips x0 by carve order",
            "negative_or_boundary_check": "commuting saturated-pair control has no flip",
            "expected_result_path": str(result_path),
        },
        "management_parent_surfaces": [
            "queue_liveness",
            "runner_preflight",
            "sim_admissibility",
            "queue_readiness",
            "formal_sim_profile",
            "stage_gate",
            "expected_result_surface",
            "controller_read_artifacts",
        ],
        "packet_contract": {
            "type": "MICRO",
            "tool_target": "z3",
            "function_surface": "z3/cvc5 finite integer membership flip query",
            "micro_claim": claim,
            "lego_target": basename,
            "function_receipt": "new",
            "prior_function_receipts": [],
            "why_this_lego": "the fixture exposes one bounded order-sensitivity check without broader promotion",
            "positive_case": "x0 survives exactly one carve order in z3 and cvc5",
            "negative_case": "commuting saturated-pair control has z3/cvc5 flip_exists=unsat",
            "boundary_case": "membership checks agree with the flip witness polarity",
            "demotion_condition": "demote if the x0 flip or commuting control fails to reproduce",
            "out_of_scope": [
                "no carrier promotion",
                "no geometry promotion",
                "no bridge claim",
                "no axis claim",
            ],
            "claim_ceiling": "scratch_diagnostic_only",
            "next_lego_target": "later canonical packet only after exact parent receipts and gates",
            "promotion_condition": "requires later admitted packet and explicit promotion gate",
            "blocked_until": "three-engine envelope or canonical lego contract is intentionally built and admitted",
            "promotion_boundary": "no promotion beyond scratch_diagnostic without a later admitted packet",
        },
    }


def run_wizard_admission(sim_path: Path, result_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    basename = sim_path.stem
    artifact_path = (
        REPO_ROOT
        / "system_v5"
        / "ops"
        / "wizard_admission_receipts"
        / f"{basename}_admission_artifact.json"
    )
    admission_path = REPO_ROOT / "system_v5" / "ops" / "wizard_admissions" / f"{basename}.json"
    artifact = build_admission_artifact(result_path=result_path, basename=basename)
    payload = build_admission_payload(
        repo_root=REPO_ROOT,
        basename=basename,
        sim_path=sim_path,
        result_path=result_path,
        artifact_path=artifact_path,
    )
    write_json(artifact_path, artifact)
    write_json(admission_path, payload)
    command = run_command(
        [
            sim_python(),
            str(REPO_ROOT / "scripts" / "wizard_sim_admission.py"),
            "--repo-root",
            str(REPO_ROOT),
            "--basename",
            basename,
            "--sim-path",
            rel_or_abs(REPO_ROOT, sim_path),
            "--admission-file",
            str(admission_path),
            "--expected-result-path",
            str(result_path),
        ]
    )
    parsed = parse_json_stdout(command)
    ok = command["exit_code"] == 0 and parsed.get("ok") is True
    return artifact_path, admission_path, {
        "gate": "wizard_sim_admission",
        "verdict": "pass" if ok else "reject",
        "ok": ok,
        "admission_artifact_path": str(artifact_path),
        "admission_packet_path": str(admission_path),
        "real_admission": command,
        "real_admission_json": parsed,
    }


def enter_purgatory(sim_path: Path, result_path: Path, gates: list[dict[str, Any]]) -> dict[str, Any]:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from system_v4.skills.a2_graph_refinery import A2GraphRefinery
    from system_v4.skills.graveyard_router import GraveyardRouter

    basename = sim_path.stem
    failing_gates = [
        f"{gate['gate']}={gate['verdict']}: {gate.get('reason') or gate.get('real_validator_json') or gate.get('real_admission_json')}"
        for gate in gates
        if gate.get("ok") is not True
    ]
    raw_lines = [
        f"status=scratch_diagnostic_reproduced_not_promoted",
        f"sim_path={sim_path}",
        f"result_path={result_path}",
        f"result_sha256={sha256(result_path)}",
        *failing_gates,
    ]
    refinery = A2GraphRefinery(str(REPO_ROOT))
    router = GraveyardRouter(refinery)
    node_id = router.route_parked(
        candidate_id=basename,
        reason_tag="SCRATCH_DIAGNOSTIC_PARKED_NOT_PROMOTED",
        raw_lines=raw_lines,
        target_ref=str(result_path),
    )
    node = refinery.builder.get_node(node_id)
    node_payload = {
        "node_id": node_id,
        "route": "route_parked",
        "status": "purgatory_resident",
        "reason_tag": "SCRATCH_DIAGNOSTIC_PARKED_NOT_PROMOTED",
        "target_ref": str(result_path),
        "raw_lines": raw_lines,
        "graph_json": str(REPO_ROOT / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"),
        "graphml": str(REPO_ROOT / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.graphml"),
        "refinery_batch_index": str(REPO_ROOT / "system_v4" / "a2_state" / "refinery_batch_index.json"),
    }
    if node is not None:
        node_payload.update(
            {
                "node_type": node.node_type,
                "layer": node.layer,
                "trust_zone": node.trust_zone,
                "authority": node.authority,
                "properties": node.properties,
            }
        )
    return {
        "gate": "graveyard_router",
        "verdict": "pass",
        "ok": True,
        "entry": node_payload,
    }


def run_loop(sim_path: Path, *, stage_claim: str = DEFAULT_STAGE_CLAIM) -> dict[str, Any]:
    sim_path = sim_path.resolve()
    if not sim_path.exists():
        raise FileNotFoundError(sim_path)
    result_path, seat = seat_certify(sim_path)
    three_engine = run_three_engine_validator(result_path)
    stage_gate = run_stage_gate(stage_claim)
    artifact_path, admission_path, admission = run_wizard_admission(sim_path, result_path)
    graveyard = enter_purgatory(sim_path, result_path, [seat, three_engine, stage_gate, admission])
    created_paths = {
        "sim": str(sim_path),
        "result": str(result_path),
        "admission_artifact": str(artifact_path),
        "admission_packet": str(admission_path),
        "graveyard_graph_json": graveyard["entry"]["graph_json"],
        "graveyard_graphml": graveyard["entry"]["graphml"],
    }
    return {
        "schema": "loop_to_system_runner_report_v1",
        "created_at": utc_now(),
        "repo_root": str(REPO_ROOT),
        "sim_python": sim_python(),
        "created_paths": created_paths,
        "gates": [seat, three_engine, stage_gate, admission, graveyard],
        "graveyard_entry": graveyard["entry"],
        "final_status": {
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "nothing_promoted": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim", default=str(DEFAULT_SIM), help="Path to the sim Python file.")
    parser.add_argument("--stage-claim", default=DEFAULT_STAGE_CLAIM)
    parser.add_argument("--out", help="Optional path for the JSON run report.")
    args = parser.parse_args()

    report = run_loop(Path(args.sim), stage_claim=args.stage_claim)
    if args.out:
        write_json(Path(args.out), report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(g.get("ok") is True for g in report["gates"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
