from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import os
import shlex
import stat
import subprocess
import sys
import time
from pathlib import Path

from . import agentrun, dependencies
from .applicability import ApplicabilityRegistry
from .advisory_run import AdvisoryRunError, run_advisory_sidecar
from .boxrun import BoxRunError, run_first_box
from .capability_box import CapabilityBoxError, run_pytorch_capability_box
from .capability_dispatch import capability_ids, run_capability_flow
from .capability_suite import CapabilitySuiteError, run_capability_suite
from .failure_repair import (
    FailureRepairError,
    REPAIR_PLAN_NAME,
    write_repair_plan_for_run,
)
from .repair_outcome import RepairOutcomeError, run_fresh_rerun_outcome
from .constraints import FiniteConstraintProblem
from .crosscheck import cross_check, registered_claim_kinds
from .discharge import Observation, Policy, Requirement, discharge
from .doctor import build_report
from .ensemble import FiniteHistoryEnsemble
from .estate import EstateRunner
from .evidence import (
    DigestRoute,
    EvidenceError,
    FileRoute,
    SealVerdict,
    build_required_manifest,
    ref_from_dict,
    required_manifest_from_dict,
    route_table,
    seal_from_dict,
    seal_run,
    verify_seal,
)
from .gate import GateError, run_gate
from .integrated_workload import (
    IntegratedWorkloadError,
    run_integrated_core_workload,
)
from .sim_admission import SimAdmissionError, run_sim_admission
from .shared_affine_parity import SharedAffineParityError, run_shared_affine_parity
from .formal_registry import (
    FORMAL_MAX_PAYLOAD_BYTES,
    formal_catalog,
    formal_task_kinds,
    run_formal_task,
    run_temporal_pair,
)
from .formal_flow import FormalFlowError
from .lease import LeaseDenied, VALID, issue_lease, verify_lease_file
from .lev_eval_observation import (
    LevEvalObservationError,
)
from .lev_eval_observation_flow import (
    LevEvalObservationFlowError,
    run_lev_eval_observation_flow,
)
from .maintenance import major_run_preflight
from .parity import compare_density_receipts
from .advice import build_audit_brief, deterministic_explanation
from .user_profile import (
    DEFAULT_PROFILE_PATH,
    ProfileError,
    compile_user_profile,
)
from .user_request import (
    BLOCKED as REQUEST_BLOCKED,
    ELIGIBLE as REQUEST_ELIGIBLE,
    EVALUATION_ERROR as REQUEST_EVALUATION_ERROR,
    PARKED as REQUEST_PARKED,
    assess_user_request,
)
from . import ratchetrun, simrun
from .cr_sim_slice import CRSimSliceError, run_cr_sim_slice
from .candidate_world import CandidateWorldError, run_candidate_world
from .exploratory_sim import ExploratorySimError, run_ijk_prototype
from .manifold_foundation import (
    ManifoldFoundationError,
    validate_foundation_file,
    write_foundation_receipt,
)
from .runtime_profiles import (
    RuntimeProfileError,
    inspect_active_runtime,
    list_runtime_profiles,
)


def _read_regular_file_bounded(path: Path, maximum_bytes: int) -> bytes:
    """Read at most one byte beyond a fixed bound from one regular-file handle."""

    if not isinstance(path, Path):
        raise ValueError("payload path must be a pathlib.Path")
    if (
        isinstance(maximum_bytes, bool)
        or not isinstance(maximum_bytes, int)
        or maximum_bytes < 1
    ):
        raise ValueError("maximum_bytes must be a positive integer")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(
        os, "O_NONBLOCK", 0
    )
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("payload must be one regular file")
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            descriptor = -1
            return stream.read(maximum_bytes + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def demo() -> dict[str, object]:
    ensemble = FiniteHistoryEnsemble.from_mappings(
        [
            {"past": 0, "present": "a", "future": 0},
            {"past": 0, "present": "a", "future": 1},
            {"past": 1, "present": "b", "future": 1},
        ]
    )
    present = ensemble.project(("present",))
    fibres = {
        value[0]: ensemble.extension_fibre(("present",), value).count
        for value in present
    }
    problem = FiniteConstraintProblem.from_spec(
        {
            "variables": {"x": [0, 1], "y": [0, 1]},
            "constraints": [
                {
                    "op": "neq",
                    "left": {"var": "x"},
                    "right": {"var": "y"},
                }
            ],
        }
    )
    result = problem.solve_enumerated()
    return {
        "schema": "constraintbox.demo.v1",
        "compatible_histories": ensemble.count,
        "present_projection": present,
        "extension_fibres": fibres,
        "bounded_solver": {
            "status": result.status.value,
            "witness": result.witness,
            "reason": result.reason,
        },
        "claim_ceiling": "finite runtime demonstration only",
        "promotion_allowed": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="constraintbox")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo")
    sub.add_parser("doctor")
    runtime = sub.add_parser("runtime")
    runtime_sub = runtime.add_subparsers(dest="runtime_command", required=True)
    runtime_list = runtime_sub.add_parser("list")
    runtime_list.add_argument("--output", type=Path)
    runtime_inspect = runtime_sub.add_parser("inspect")
    runtime_inspect.add_argument("--output", type=Path)
    runtime_verify = runtime_sub.add_parser("verify")
    runtime_verify.add_argument("--output", type=Path)
    run = sub.add_parser("run")
    run.add_argument("--box-run-dir", type=Path, required=True)
    run.add_argument("--run-dir", type=Path, required=True)
    request = sub.add_parser("request")
    request.add_argument("--request", type=Path, required=True)
    request.add_argument("--include-context", action="store_true")
    request.add_argument("--output", type=Path)
    box = sub.add_parser("box")
    box.add_argument("--request", type=Path, required=True)
    box.add_argument("--run-dir", type=Path, required=True)
    box.add_argument("--output", type=Path)
    capability_box = sub.add_parser("capability-box")
    capability_box.add_argument("--request", type=Path, required=True)
    capability_box.add_argument("--run-dir", type=Path, required=True)
    capability_box.add_argument("--output", type=Path)
    capability_suite = sub.add_parser("capability-suite")
    capability_suite.add_argument("--request-id", required=True)
    capability_suite.add_argument("--run-dir", type=Path, required=True)
    capability_suite.add_argument("--output", type=Path)
    integrated_workload = sub.add_parser("integrated-workload")
    integrated_workload.add_argument("--request-id", required=True)
    integrated_workload.add_argument("--run-dir", type=Path, required=True)
    integrated_workload.add_argument("--output", type=Path)
    sim_admission = sub.add_parser("admit-sim-evidence")
    sim_admission.add_argument("--capability-suite", type=Path, required=True)
    sim_admission.add_argument("--attractor-basin-envelope", type=Path, required=True)
    sim_admission.add_argument("--run-dir", type=Path, required=True)
    sim_admission.add_argument("--output", type=Path)
    shared_affine_parity = sub.add_parser("shared-affine-parity")
    shared_affine_parity.add_argument("--run-dir", type=Path, required=True)
    shared_affine_parity.add_argument("--output", type=Path)
    lev_eval_observation = sub.add_parser("observe-lev-eval")
    lev_eval_observation.add_argument("--request-id", required=True)
    lev_eval_observation.add_argument("--source-run-dir", type=Path, required=True)
    lev_eval_observation.add_argument("--expected-execution-id", required=True)
    lev_eval_observation.add_argument("--expected-suite-id", required=True)
    lev_eval_observation.add_argument("--run-dir", type=Path, required=True)
    lev_eval_observation.add_argument("--output", type=Path)
    repair_plan = sub.add_parser("repair-plan")
    repair_plan.add_argument("--capability-run-dir", type=Path, required=True)
    repair_outcome = sub.add_parser("repair-outcome")
    repair_outcome.add_argument("--capability-run-dir", type=Path, required=True)
    repair_outcome.add_argument("--run-dir", type=Path, required=True)
    repair_outcome.add_argument(
        "--execute-fresh-rerun",
        action="store_true",
        required=True,
    )
    advise = sub.add_parser("advise")
    advise.add_argument("--box-run", type=Path, required=True)
    advise.add_argument(
        "--provider",
        choices=("nvidia", "openrouter"),
        required=True,
    )
    advise.add_argument("--run-dir", type=Path, required=True)
    advise.add_argument("--output", type=Path)
    engine_test = sub.add_parser("engine-test")
    engine_test.add_argument("--output", type=Path)
    engine_test.add_argument(
        "--capability",
        choices=capability_ids(),
    )
    engine_test.add_argument("--request-id")
    engine_test.add_argument("--run-dir", type=Path)
    deps = sub.add_parser("deps")
    deps_mode = deps.add_mutually_exclusive_group()
    deps_mode.add_argument("--check", action="store_true")
    deps_mode.add_argument("--report", action="store_true")
    deps.add_argument("--json", action="store_true")
    mmm = sub.add_parser("mmm")
    mmm.add_argument("packs", nargs="+")
    mmm.add_argument("--json", action="store_true")
    solve = sub.add_parser("solve")
    solve.add_argument("problem", type=Path)
    solve.add_argument("--backend", choices=("enumeration", "z3"), default="enumeration")
    crosscheck = sub.add_parser("crosscheck")
    crosscheck.add_argument("--claim-kind", choices=registered_claim_kinds())
    crosscheck.add_argument("--claim-file", type=Path)
    estate = sub.add_parser("estate")
    estate.add_argument("--pack-root", type=Path, required=True)
    estate.add_argument("--manifest", type=Path, required=True)
    estate.add_argument("--fixture", type=Path, required=True)
    estate.add_argument("--tier", required=True)
    estate.add_argument("--mode", choices=("boot", "acceptance"), default="boot")
    estate.add_argument("--python", type=Path)
    estate.add_argument("--enforce", action="store_true")
    estate.add_argument("--output", type=Path)
    cr_slice = sub.add_parser("cr-slice")
    cr_slice.add_argument(
        "--profile",
        choices=("foundation-seed", "cr-gksl-source", "paired-extension", "foundation-and-cr"),
        required=True,
    )
    cr_slice.add_argument("--run-dir", type=Path, required=True)
    cr_slice.add_argument("--cr-root", type=Path)
    cr_slice.add_argument("--manifest", type=Path)
    cr_slice.add_argument("--timeout-seconds", type=float, default=300.0)
    cr_slice.add_argument("--output", type=Path)
    exploratory_ijk = sub.add_parser("exploratory-ijk")
    exploratory_ijk.add_argument("--run-dir", type=Path, required=True)
    exploratory_ijk.add_argument("--cr-root", type=Path)
    exploratory_ijk.add_argument("--timeout-seconds", type=float, default=300.0)
    exploratory_ijk.add_argument("--output", type=Path)
    candidate_world = sub.add_parser("candidate-world")
    candidate_world.add_argument("--source-markdown", type=Path, required=True)
    candidate_world.add_argument("--run-dir", type=Path, required=True)
    candidate_world.add_argument("--cr-root", type=Path)
    candidate_world.add_argument("--timeout-seconds", type=float, default=600.0)
    candidate_world.add_argument("--output", type=Path)
    foundation = sub.add_parser("manifold-foundation")
    foundation.add_argument("--fixture", type=Path, required=True)
    foundation.add_argument("--output", type=Path)
    parity = sub.add_parser("estate-parity")
    parity.add_argument("receipts", type=Path, nargs="+")
    parity.add_argument("--tolerance", type=float, default=1e-8)
    parity.add_argument("--enforce", action="store_true")
    parity.add_argument("--output", type=Path)
    preflight = sub.add_parser("preflight")
    preflight.add_argument("receipts", type=Path, nargs="+")
    preflight.add_argument("--require-tier", action="append", required=True)
    preflight.add_argument("--max-age-hours", type=float, default=24.0)
    preflight.add_argument("--enforce", action="store_true")
    preflight.add_argument("--output", type=Path)

    lease = sub.add_parser("lease")
    lease_sub = lease.add_subparsers(dest="lease_command", required=True)
    lease_issue = lease_sub.add_parser("issue")
    lease_issue.add_argument("--repo", type=Path, required=True)
    lease_issue.add_argument("--runner", action="append", required=True)
    lease_issue.add_argument("--ttl-seconds", type=float, required=True)
    lease_issue.add_argument("--timeout-seconds", type=float, default=300.0)
    lease_issue.add_argument("--output", type=Path)
    lease_verify = lease_sub.add_parser("verify")
    lease_verify.add_argument("--lease", type=Path, required=True)
    lease_verify.add_argument("--repo", type=Path, required=True)
    lease_verify.add_argument("--output", type=Path)

    discharge_parser = sub.add_parser("discharge")
    discharge_parser.add_argument("--policy", type=Path, required=True)
    discharge_parser.add_argument("--observations", type=Path, required=True)
    discharge_parser.add_argument("--now", type=float)
    discharge_parser.add_argument("--output", type=Path)

    evidence = sub.add_parser("evidence")
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_seal = evidence_sub.add_parser("seal")
    evidence_seal.add_argument("--run-id", required=True)
    evidence_seal.add_argument("--manifest-id", required=True)
    evidence_seal.add_argument("--refs", type=Path, required=True)
    evidence_seal.add_argument("--manifest-output", type=Path, required=True)
    evidence_seal.add_argument("--file-root", type=Path)
    evidence_seal.add_argument("--digest-store", type=Path)
    evidence_seal.add_argument("--output", type=Path)
    evidence_verify = evidence_sub.add_parser("verify")
    evidence_verify.add_argument("--seal", type=Path, required=True)
    evidence_verify.add_argument(
        "--required-manifest",
        type=Path,
        required=True,
    )
    evidence_verify.add_argument("--file-root", type=Path)
    evidence_verify.add_argument("--digest-store", type=Path)
    evidence_verify.add_argument("--output", type=Path)

    applicability = sub.add_parser("applicability")
    applicability.add_argument("--registry", type=Path, required=True)
    applicability.add_argument("--claim-type", required=True)
    applicability.add_argument("--capability", action="append", default=[])
    applicability.add_argument("--output", type=Path)
    formal = sub.add_parser("formal")
    formal_sub = formal.add_subparsers(dest="formal_command", required=True)
    formal_list = formal_sub.add_parser("list")
    formal_list.add_argument("--output", type=Path)
    formal_run = formal_sub.add_parser("run")
    formal_run.add_argument("--task", choices=formal_task_kinds(), required=True)
    formal_run.add_argument("--request-id", required=True)
    formal_run.add_argument("--payload", type=Path, required=True)
    formal_run.add_argument("--run-dir", type=Path, required=True)
    formal_run.add_argument("--output", type=Path)
    formal_temporal = formal_sub.add_parser("temporal")
    formal_temporal.add_argument("--output", type=Path)
    gate = sub.add_parser("gate")
    gate.add_argument("receipt", type=Path)
    gate.add_argument("--output", type=Path)
    sim = sub.add_parser("sim")
    sim_sub = sim.add_subparsers(dest="sim_command", required=True)
    sim_run = sim_sub.add_parser("run")
    sim_run.add_argument("sim_path", type=Path)
    sim_run.add_argument("--receipt", type=Path)
    sim_run.add_argument(
        "--timeout",
        type=float,
        default=simrun.DEFAULT_TIMEOUT_SECONDS,
        metavar="SECONDS",
    )
    sim_run.add_argument("--python", type=Path)
    ratchet = sub.add_parser("ratchet")
    ratchet_sub = ratchet.add_subparsers(dest="ratchet_command", required=True)
    ratchet_tick = ratchet_sub.add_parser("tick")
    ratchet_tick.add_argument("--receipt", type=Path)
    ratchet_tick.add_argument("--v2", action="store_true")
    ratchet_tick.add_argument(
        "--timeout",
        type=float,
        default=ratchetrun.DEFAULT_TIMEOUT_SECONDS,
        metavar="SECONDS",
    )
    ratchet_tick.add_argument("--python", type=Path)
    ratchet_tick.add_argument("--no-pin-hashseed", action="store_true")
    return parser


def _evidence_routes(args: argparse.Namespace):
    routes = []
    if args.file_root is not None:
        routes.append(FileRoute(args.file_root))
    if args.digest_store is not None:
        routes.append(DigestRoute(args.digest_store))
    if not routes:
        raise EvidenceError("at least one of --file-root or --digest-store is required")
    return route_table(*routes)


def _run_crosscheck_command(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    if args.claim_kind is None and args.claim_file is None:
        print("REGISTERED CLAIM KINDS")
        for claim_kind in registered_claim_kinds():
            print(claim_kind)
        return
    if args.claim_kind is None or args.claim_file is None:
        parser.error("--claim-kind and --claim-file must be supplied together")
    try:
        claim = json.loads(args.claim_file.read_text(encoding="utf-8"))
        if not isinstance(claim, dict):
            raise ValueError("claim file must contain a JSON object")
        result = cross_check(args.claim_kind, claim)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"constraintbox crosscheck: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print("DECIDER | STATUS | RAW VERDICT | NORMAL VERDICT | DETAIL")
    for outcome in result.outcomes:
        cells = (
            outcome.decider,
            outcome.status,
            outcome.raw_verdict,
            outcome.normal_verdict,
            outcome.detail,
        )
        print(" | ".join("-" if cell is None else str(cell) for cell in cells))
    print(f"AGREEMENT | {result.agreement}")
    if result.reason:
        print(f"REASON | {result.reason}")
    if result.agreement == "UNRESOLVED":
        raise SystemExit(2)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "crosscheck":
        _run_crosscheck_command(parser, args)
        return
    if args.command == "mmm":
        loader_path = Path(__file__).resolve().parents[2] / "mmm" / "load.py"
        if not loader_path.exists():
            print(f"mmm loader not found: {loader_path}", file=sys.stderr)
            raise SystemExit(2)
        spec = importlib.util.spec_from_file_location(
            "constraint_box_mmm_load", loader_path
        )
        if spec is None or spec.loader is None:
            print(f"mmm loader could not be loaded: {loader_path}", file=sys.stderr)
            raise SystemExit(2)
        loader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loader)
        loader_args = [*args.packs]
        if args.json:
            loader_args.append("--json")
        exit_code = loader.main(loader_args)
        if exit_code:
            raise SystemExit(exit_code)
        return
    if args.command == "deps":
        try:
            report = dependencies.scan()
        except dependencies.DependencyScanError as exc:
            if args.json:
                print(json.dumps({"error": str(exc)}, sort_keys=True))
            else:
                print(f"deps: {exc}")
            raise SystemExit(dependencies.EXIT_CODES["IO_ERROR"])
        exit_code = dependencies.exit_code_for(report)
        if args.json:
            print(json.dumps(report, sort_keys=True, indent=2))
        elif args.check:
            print(dependencies.render_check(report))
        else:
            print(dependencies.render_table(report))
        if exit_code:
            raise SystemExit(exit_code)
        return
    if args.command == "runtime":
        try:
            if args.runtime_command == "list":
                value = list_runtime_profiles()
                exit_code = 0
            else:
                value = inspect_active_runtime()
                exit_code = (
                    {"ELIGIBLE": 0, "PARKED": 4, "BLOCKED": 1}[value["state"]]
                    if args.runtime_command == "verify"
                    else 0
                )
        except RuntimeProfileError as exc:
            value = {
                "schema": "constraintbox.runtime-profile-error.v1",
                "state": "BLOCKED",
                "reason": "runtime_profile_registry_error",
                "error": str(exc),
                "promotion_allowed": False,
            }
            exit_code = 5
        rendered = json.dumps(value, sort_keys=True, indent=2) + "\n"
        output = getattr(args, "output", None)
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
            temporary.write_text(rendered, encoding="utf-8")
            os.replace(temporary, output)
        print(rendered, end="")
        if exit_code:
            raise SystemExit(exit_code)
        return
    exit_code = 0
    if args.command == "run":
        try:
            value, exit_code = agentrun.run_agent(
                args.box_run_dir,
                args.run_dir,
            )
        except agentrun.AgentRunError as exc:
            value = {
                "schema": "constraintbox.agent-run-error.v1",
                "disposition": "EVALUATION_ERROR",
                "reason": "first_box_handoff_or_agent_configuration_error",
                "error": str(exc),
                "release_allowed": False,
                "promotion_allowed": False,
            }
            exit_code = 5
    elif args.command == "request":
        try:
            request_raw = args.request.read_bytes()
            assessment = assess_user_request(request_raw)
            compiled = compile_user_profile(DEFAULT_PROFILE_PATH.read_bytes())
            decision = assessment.to_dict()
            value = {
                "schema": "constraintbox.request-preflight.v1",
                "decision": decision,
                "user_context": compiled.to_dict(
                    include_text=args.include_context
                ),
                "deterministic_explanation": deterministic_explanation(
                    decision
                ).to_dict(),
                "external_audit_brief": build_audit_brief(
                    decision,
                    output_contract=compiled.output_contract,
                ),
                "next_step": (
                    "proposal_generation"
                    if assessment.disposition == REQUEST_ELIGIBLE
                    else "user_resubmission"
                    if assessment.disposition == REQUEST_PARKED
                    else "none"
                ),
                "promotion_allowed": False,
            }
            exit_code = {
                REQUEST_ELIGIBLE: 0,
                REQUEST_BLOCKED: 1,
                REQUEST_PARKED: 4,
                REQUEST_EVALUATION_ERROR: 5,
            }[assessment.disposition]
        except (OSError, ProfileError, ValueError) as exc:
            value = {
                "schema": "constraintbox.request-preflight.v1",
                "decision": {
                    "disposition": REQUEST_EVALUATION_ERROR,
                    "reason": "request_or_profile_configuration_error",
                    "error": str(exc),
                },
                "promotion_allowed": False,
            }
            exit_code = 5
    elif args.command == "box":
        try:
            if args.output is not None:
                resolved_output = args.output.expanduser().resolve()
                resolved_run_dir = args.run_dir.expanduser().resolve()
                if resolved_output == resolved_run_dir or (
                    resolved_run_dir in resolved_output.parents
                ):
                    args.output = None
                    raise BoxRunError(
                        "--output must be outside the box receipt directory"
                    )
            value, exit_code = run_first_box(
                args.request.read_bytes(),
                args.run_dir,
            )
        except (OSError, BoxRunError, ValueError) as exc:
            value = {
                "schema": "constraintbox.first-box-run.v1",
                "disposition": REQUEST_EVALUATION_ERROR,
                "reason": "first_box_configuration_error",
                "error": str(exc),
                "promotion_allowed": False,
                "release_allowed": False,
            }
            exit_code = 5
    elif args.command == "capability-box":
        try:
            if args.output is not None:
                resolved_output = args.output.expanduser().resolve()
                resolved_run_dir = args.run_dir.expanduser().resolve()
                if resolved_output == resolved_run_dir or (
                    resolved_run_dir in resolved_output.parents
                ):
                    args.output = None
                    raise CapabilityBoxError(
                        "--output must be outside the capability-box receipt "
                        "directory"
                    )
                args.output = resolved_output
            value, exit_code = run_pytorch_capability_box(
                args.request.read_bytes(),
                args.run_dir,
            )
        except (OSError, CapabilityBoxError, ValueError) as exc:
            value = {
                "schema": "constraintbox.capability-box-run.v1",
                "capability_id": "pytorch-jacobian-v1",
                "disposition": REQUEST_EVALUATION_ERROR,
                "reason": "capability_box_configuration_error",
                "error": str(exc),
                "promotion_allowed": False,
                "release_allowed": False,
            }
            exit_code = 5
    elif args.command == "capability-suite":
        try:
            resolved_run_dir = args.run_dir.expanduser().resolve()
            if args.output is not None:
                resolved_output = args.output.expanduser().resolve()
                if resolved_output == resolved_run_dir or (
                    resolved_run_dir in resolved_output.parents
                ):
                    args.output = None
                    raise CapabilitySuiteError(
                        "--output must be outside the capability-suite receipt "
                        "directory"
                    )
                args.output = resolved_output
            value, exit_code = run_capability_suite(
                request_id=args.request_id,
                run_root=resolved_run_dir,
            )
        except (OSError, CapabilitySuiteError, ValueError) as exc:
            value = {
                "schema": "constraintbox.capability-suite-receipt.v1",
                "disposition": "EVALUATION_ERROR",
                "reason": "capability_suite_configuration_error",
                "error": str(exc),
                "release_allowed": False,
                "engine_readiness_claim": False,
                "cr_truth_claim": False,
                "promotion_allowed": False,
            }
            exit_code = 5
    elif args.command == "integrated-workload":
        try:
            resolved_run_dir = args.run_dir.expanduser().resolve()
            if args.output is not None:
                resolved_output = args.output.expanduser().resolve()
                if resolved_output == resolved_run_dir or (
                    resolved_run_dir in resolved_output.parents
                ):
                    args.output = None
                    raise IntegratedWorkloadError(
                        "--output must be outside the integrated workload run directory"
                    )
                args.output = resolved_output
            value, exit_code = run_integrated_core_workload(
                request_id=args.request_id,
                run_root=resolved_run_dir,
            )
        except (IntegratedWorkloadError, OSError, ValueError) as exc:
            value = {
                "schema": "constraintbox.integrated-core-workload-error.v1",
                "disposition": "HOLD",
                "reason": "integrated_workload_configuration_error",
                "error": str(exc),
                "promotion_allowed": False,
            }
            exit_code = 5
    elif args.command == "admit-sim-evidence":
        try:
            resolved_run_dir = args.run_dir.expanduser().resolve()
            if args.output is not None:
                resolved_output = args.output.expanduser().resolve()
                if resolved_output == resolved_run_dir or resolved_run_dir in resolved_output.parents:
                    args.output = None
                    raise SimAdmissionError("--output must be outside the sim-admission run directory")
                args.output = resolved_output
            value, exit_code = run_sim_admission(
                capability_suite=args.capability_suite.expanduser().resolve(strict=True),
                attractor_basin_envelope=args.attractor_basin_envelope.expanduser().resolve(strict=True),
                claim_path=resolved_run_dir / "sim_admission_claim.json",
            )
        except (OSError, SimAdmissionError, ValueError) as exc:
            value = {
                "schema": "constraintbox.sim-admission-result.v1",
                "disposition": "HOLD",
                "reason": "sim_admission_configuration_error",
                "error": str(exc),
                "release_allowed": False,
                "promotion_allowed": False,
            }
            exit_code = 5
    elif args.command == "shared-affine-parity":
        try:
            resolved_run_dir = args.run_dir.expanduser().resolve()
            if args.output is not None:
                resolved_output = args.output.expanduser().resolve()
                if resolved_output == resolved_run_dir or resolved_run_dir in resolved_output.parents:
                    args.output = None
                    raise SharedAffineParityError("--output must be outside the parity run directory")
                args.output = resolved_output
            value, exit_code = run_shared_affine_parity(run_root=resolved_run_dir)
        except (OSError, SharedAffineParityError, subprocess.TimeoutExpired, ValueError) as exc:
            value = {
                "schema": "constraintbox.shared-affine-density-parity.v1",
                "state": "PARKED",
                "reason": "shared_affine_parity_configuration_or_runtime_error",
                "error": str(exc),
                "consistency_only": True,
                "release_allowed": False,
                "promotion_allowed": False,
            }
            exit_code = 5
    elif args.command == "repair-plan":
        try:
            value = write_repair_plan_for_run(args.capability_run_dir)
            exit_code = 0
        except (OSError, FailureRepairError, ValueError) as exc:
            value = {
                "schema": "constraintbox.capability-repair-plan-error.v1",
                "disposition": "HOLD",
                "reason": "capability_repair_plan_configuration_or_verification_error",
                "error": str(exc),
                "execution_authorized": False,
                "promotion_allowed": False,
            }
            exit_code = 5
    elif args.command == "repair-outcome":
        try:
            parent_run_dir = args.capability_run_dir.expanduser()
            rerun_dir = args.run_dir.expanduser()
            if not parent_run_dir.is_absolute() or not rerun_dir.is_absolute():
                raise RepairOutcomeError(
                    "repair-outcome directories must be supplied as absolute paths"
                )
            value = run_fresh_rerun_outcome(
                capability_run_root=parent_run_dir,
                run_root=rerun_dir,
                execute_fresh_rerun=args.execute_fresh_rerun,
            )
            exit_code = {
                "ELIGIBLE": 0,
                "BLOCKED": 1,
                "PARKED": 4,
            }.get(value.get("rerun", {}).get("disposition"), 5)
        except (OSError, FailureRepairError, RepairOutcomeError, ValueError) as exc:
            value = {
                "schema": "constraintbox.capability-repair-outcome-error.v1",
                "disposition": "HOLD",
                "reason": "capability_repair_outcome_configuration_or_verification_error",
                "error": str(exc),
                "execution_authorized": False,
                "release_allowed": False,
                "promotion_allowed": False,
            }
            exit_code = 5
    elif args.command == "advise":
        try:
            lexical_box_run = args.box_run.expanduser()
            lexical_sidecar_run = args.run_dir.expanduser()
            resolved_box_run = lexical_box_run.resolve()
            resolved_sidecar_run = lexical_sidecar_run.resolve()
            if args.output is not None:
                resolved_output = args.output.expanduser().resolve()
                protected_roots = (resolved_box_run, resolved_sidecar_run)
                if any(
                    resolved_output == root or root in resolved_output.parents
                    for root in protected_roots
                ):
                    args.output = None
                    raise AdvisoryRunError(
                        "--output must be outside the box and advisory "
                        "sidecar run directories"
                    )
                args.output = resolved_output
            value, exit_code = run_advisory_sidecar(
                lexical_box_run,
                args.provider,
                lexical_sidecar_run,
            )
        except (OSError, AdvisoryRunError, ValueError) as exc:
            value = {
                "schema": "constraintbox.advisory-sidecar-error.v1",
                "provider": args.provider,
                "disposition": "HOLD",
                "reason": "advisory_sidecar_configuration_error",
                "error": str(exc),
                "advisory_only": True,
                "changes_box_decision": False,
                "decision_authority": False,
                "release_allowed": False,
                "promotion_allowed": False,
            }
            exit_code = 5
    elif args.command == "engine-test":
        from .external_engine_packet import ExternalEnginePacketBroker

        try:
            if args.capability is None:
                if args.request_id is not None or args.run_dir is not None:
                    raise ValueError(
                        "--request-id and --run-dir require --capability"
                    )
                value = ExternalEnginePacketBroker().run()
                exit_code = {
                    "PASS": 0,
                    "FAIL": 1,
                    "PARKED": 4,
                }.get(value.get("status"), 5)
            else:
                if args.request_id is None or args.run_dir is None:
                    raise ValueError(
                        "--capability requires --request-id and --run-dir"
                    )
                resolved_run_dir = args.run_dir.expanduser().resolve()
                if args.output is not None:
                    resolved_output = args.output.expanduser().resolve()
                    if (
                        resolved_output == resolved_run_dir
                        or resolved_run_dir in resolved_output.parents
                    ):
                        args.output = None
                        raise ValueError(
                            "--output must be outside the capability receipt "
                            "directory"
                        )
                    args.output = resolved_output
                value = run_capability_flow(
                    capability_id=args.capability,
                    request_id=args.request_id,
                    run_root=resolved_run_dir,
                )
                if value.get("disposition") in {"BLOCKED", "PARKED"}:
                    write_repair_plan_for_run(resolved_run_dir)
                exit_code = {
                    "ELIGIBLE": 0,
                    "BLOCKED": 1,
                    "PARKED": 4,
                    "HOLD": 5,
                }.get(value.get("disposition"), 5)
        except (OSError, ValueError) as exc:
            if args.capability is None:
                value = {
                    "schema": "constraintbox.external-engine-packet-receipt.v1",
                    "status": "FAIL",
                    "reason": "external_packet_configuration_error",
                    "error": str(exc),
                    "external_system": True,
                    "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
                    "promotion_allowed": False,
                }
                exit_code = 1
            else:
                value = {
                    "schema": "constraintbox.external-capability-flow-error.v1",
                    "capability_id": args.capability,
                    "disposition": "HOLD",
                    "reason": "external_capability_configuration_error",
                    "error": str(exc),
                    "external_system": True,
                    "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
                    "release_allowed": False,
                    "promotion_allowed": False,
                }
                exit_code = 5
    elif args.command == "observe-lev-eval":
        try:
            resolved_source = args.source_run_dir.expanduser().resolve(strict=False)
            resolved_run_dir = args.run_dir.expanduser().resolve(strict=False)
            if args.output is not None:
                resolved_output = args.output.expanduser().resolve()
                protected_roots = (resolved_source, resolved_run_dir)
                if any(
                    resolved_output == root or root in resolved_output.parents
                    for root in protected_roots
                ):
                    args.output = None
                    raise LevEvalObservationFlowError(
                        "--output must be outside the foreign and CB observation flow directories"
                    )
                args.output = resolved_output
            result = run_lev_eval_observation_flow(
                request_id=args.request_id,
                source_run_dir=resolved_source,
                expected_execution_id=args.expected_execution_id,
                expected_suite_id=args.expected_suite_id,
                run_root=resolved_run_dir,
            )
            value = result.as_dict()
            exit_code = {"PARKED": 4, "HOLD": 5}.get(result.terminal, 5)
        except (OSError, LevEvalObservationError, LevEvalObservationFlowError, ValueError) as exc:
            value = {
                "schema": "constraintbox.lev-eval-observation-flow-error.v1",
                "disposition": "HOLD",
                "reason": "lev_eval_observation_flow_configuration_or_binding_error",
                "error": str(exc),
                "foreign_decision_authority": False,
                "comparison_performed": False,
                "promotion_allowed": False,
            }
            exit_code = 5
    elif args.command == "doctor":
        value = build_report()
    elif args.command == "demo":
        value = demo()
    elif args.command == "solve":
        spec = json.loads(args.problem.read_text(encoding="utf-8"))
        problem = FiniteConstraintProblem.from_spec(spec)
        result = (
            problem.solve_z3() if args.backend == "z3" else problem.solve_enumerated()
        )
        value = {
            "status": result.status.value,
            "witness": result.witness,
            "explored": result.explored,
            "reason": result.reason,
            "backend": result.backend,
        }
    elif args.command == "estate":
        runner = EstateRunner(
            args.pack_root,
            args.manifest,
            args.fixture,
            args.python,
        )
        value = runner.run_tier(args.tier, args.mode).to_dict()
        if args.enforce and value["state"] not in {"READY", "DEGRADED"}:
            exit_code = 3 if value["state"] in {"UNAVAILABLE", "UNTESTED"} else 1
    elif args.command == "cr-slice":
        try:
            resolved_run_dir = args.run_dir.expanduser().resolve()
            if args.output is not None:
                resolved_output = args.output.expanduser().resolve()
                if (
                    resolved_output == resolved_run_dir
                    or resolved_run_dir in resolved_output.parents
                ):
                    args.output = None
                    raise CRSimSliceError(
                        "--output must be outside the CR sim-slice run directory"
                    )
                args.output = resolved_output
            value, exit_code = run_cr_sim_slice(
                profile=args.profile,
                run_root=resolved_run_dir,
                cr_root=args.cr_root,
                manifest_path=args.manifest,
                timeout_seconds=args.timeout_seconds,
            )
        except (CRSimSliceError, OSError, ValueError) as exc:
            value = {
                "schema": "constraintbox.cr-sim-slice-receipt.v1",
                "status": "HOLD",
                "profile": args.profile,
                "reason": "cr_sim_slice_configuration_or_runtime_error",
                "error": str(exc),
                "external_system": True,
                "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
                "promotion_allowed": False,
                "cr_truth_claim": False,
            }
            exit_code = 5
    elif args.command == "exploratory-ijk":
        try:
            resolved_run_dir = args.run_dir.expanduser().resolve()
            if args.output is not None:
                resolved_output = args.output.expanduser().resolve()
                if resolved_output == resolved_run_dir or resolved_run_dir in resolved_output.parents:
                    args.output = None
                    raise ExploratorySimError(
                        "--output must be outside the exploratory IJK run directory"
                    )
                args.output = resolved_output
            value, exit_code = run_ijk_prototype(
                run_root=resolved_run_dir,
                cr_root=args.cr_root,
                timeout_seconds=args.timeout_seconds,
            )
        except (ExploratorySimError, OSError, ValueError) as exc:
            value = {
                "schema": "constraintbox.exploratory-ijk-receipt.v1",
                "operation_id": "manifold-ijk-engine-prototype",
                "status": "HOLD",
                "reason": "exploratory_ijk_configuration_or_runtime_error",
                "error": str(exc),
                "external_system": True,
                "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
                "checks_do_not_block_execution": True,
                "promotion_allowed": False,
                "validation_claim": False,
                "cr_truth_claim": False,
            }
            exit_code = 5
    elif args.command == "candidate-world":
        try:
            resolved_run_dir = args.run_dir.expanduser().resolve()
            if args.output is not None:
                resolved_output = args.output.expanduser().resolve()
                if resolved_output == resolved_run_dir or resolved_run_dir in resolved_output.parents:
                    args.output = None
                    raise CandidateWorldError(
                        "--output must be outside the candidate-world run directory"
                    )
                args.output = resolved_output
            value, exit_code = run_candidate_world(
                source_markdown=args.source_markdown,
                run_root=resolved_run_dir,
                cr_root=args.cr_root,
                timeout_seconds=args.timeout_seconds,
            )
        except (CandidateWorldError, OSError, ValueError) as exc:
            value = {
                "schema": "constraintbox.candidate-world-mstar-receipt.v1",
                "operation_id": "candidate-world-mstar-all-engine-envelope",
                "status": "HOLD",
                "reason": "candidate_world_configuration_or_runtime_error",
                "error": str(exc),
                "external_system": True,
                "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
                "checks_do_not_block_execution": True,
                "promotion_allowed": False,
                "validation_claim": False,
                "cr_truth_claim": False,
            }
            exit_code = 5
    elif args.command == "manifold-foundation":
        try:
            if args.output is None:
                value = validate_foundation_file(args.fixture)
            else:
                value = write_foundation_receipt(args.fixture, args.output)
            exit_code = 0
        except (ManifoldFoundationError, OSError, ValueError) as exc:
            value = {
                "schema": "constraintbox.manifold-foundation-validation.v1",
                "status": "HOLD",
                "reason": "manifold_foundation_configuration_or_validation_error",
                "error": str(exc),
                "promotion_allowed": False,
                "formal_admission_allowed": False,
            }
            exit_code = 5
    elif args.command == "estate-parity":
        value = compare_density_receipts(args.receipts, args.tolerance)
        if args.enforce:
            exit_code = {
                "CONSISTENT": 0,
                "INCONSISTENT": 1,
                "INSUFFICIENT": 4,
                "PARKED": 4,
            }.get(value["state"], 5)
    elif args.command == "preflight":
        value = major_run_preflight(
            args.receipts,
            args.require_tier,
            args.max_age_hours,
        )
        if args.enforce and value["disposition"] != "READY":
            exit_code = 4
    elif args.command == "lease":
        if args.lease_command == "issue":
            try:
                value = issue_lease(
                    args.repo,
                    [shlex.split(runner) for runner in args.runner],
                    ttl_seconds=args.ttl_seconds,
                    timeout_seconds=args.timeout_seconds,
                )
            except LeaseDenied as exc:
                value = {"error": str(exc), "runs": exc.runs}
                exit_code = 1
        else:
            verdict = verify_lease_file(args.lease, args.repo)
            value = dataclasses.asdict(verdict)
            if verdict.status != VALID:
                exit_code = 1
    elif args.command == "discharge":
        try:
            policy_body = json.loads(args.policy.read_text(encoding="utf-8"))
            policy = Policy(
                policy_id=policy_body["policy_id"],
                requirements=tuple(
                    Requirement(**requirement)
                    for requirement in policy_body["requirements"]
                ),
                max_age_seconds=policy_body["max_age_seconds"],
            )
            observations_body = json.loads(
                args.observations.read_text(encoding="utf-8")
            )
            observations = {
                name: Observation(**observation)
                for name, observation in observations_body.items()
            }
            result = discharge(
                policy,
                observations,
                now=args.now if args.now is not None else time.time(),
            )
            value = dataclasses.asdict(result)
            if result.status != "PASS":
                exit_code = 1
        except ValueError as exc:
            value = {"error": str(exc)}
            exit_code = 1
    elif args.command == "evidence":
        try:
            routes = _evidence_routes(args)
            if args.evidence_command == "seal":
                refs_body = json.loads(args.refs.read_text(encoding="utf-8"))
                refs = [ref_from_dict(body) for body in refs_body]
                required_manifest = build_required_manifest(
                    args.manifest_id,
                    refs,
                )
                simrun.write_receipt_atomic(
                    args.manifest_output,
                    required_manifest.to_dict(),
                )
                value = seal_run(
                    args.run_id,
                    required_manifest,
                    routes,
                ).to_dict()
            else:
                seal_body = json.loads(args.seal.read_text(encoding="utf-8"))
                manifest_body = json.loads(
                    args.required_manifest.read_text(encoding="utf-8")
                )
                required_manifest = required_manifest_from_dict(manifest_body)
                verification = verify_seal(
                    seal_from_dict(seal_body),
                    routes,
                    required_manifest=required_manifest,
                )
                value = verification.to_dict()
                if verification.verdict is not SealVerdict.SEALED:
                    exit_code = 1
        except EvidenceError as exc:
            value = {"error": str(exc)}
            exit_code = 1
    elif args.command == "applicability":
        try:
            capability_states = {}
            for capability in args.capability:
                name, state = capability.split("=", 1)
                capability_states[name] = state
            value = ApplicabilityRegistry.from_path(args.registry).assess(
                args.claim_type,
                capability_states,
            )
            if value["disposition"] != "ELIGIBLE_FOR_CHECKS":
                exit_code = 1
        except (KeyError, ValueError) as exc:
            value = {"error": str(exc)}
            exit_code = 1
    elif args.command == "formal":
        if args.formal_command == "list":
            value = formal_catalog()
        elif args.formal_command == "run":
            try:
                resolved_run_dir = args.run_dir.expanduser().resolve()
                if args.output is not None:
                    resolved_output = args.output.expanduser().resolve()
                    if (
                        resolved_output == resolved_run_dir
                        or resolved_run_dir in resolved_output.parents
                    ):
                        args.output = None
                        raise ValueError(
                            "--output must be outside the formal run directory"
                        )
                    args.output = resolved_output
                decision = run_formal_task(
                    task_kind=args.task,
                    request_id=args.request_id,
                    payload=_read_regular_file_bounded(
                        args.payload,
                        FORMAL_MAX_PAYLOAD_BYTES,
                    ),
                    run_root=resolved_run_dir,
                )
                value = decision.to_dict()
                exit_code = {
                    "ELIGIBLE": 0,
                    "BLOCKED": 1,
                    "PARKED": 4,
                    "HOLD": 5,
                }[decision.disposition.value]
            except (FormalFlowError, OSError, ValueError) as exc:
                value = {
                    "schema": "constraintbox.formal-cli-error.v1",
                    "disposition": "HOLD",
                    "reason": "formal_task_configuration_error",
                    "error": str(exc),
                    "promotion_allowed": False,
                }
                exit_code = 5
        else:
            value = run_temporal_pair()
            exit_code = {
                "ELIGIBLE": 0,
                "BLOCKED": 1,
                "PARKED": 4,
            }.get(value.get("disposition"), 5)
    elif args.command == "gate":
        try:
            from .gate import GATE_EXIT_CODES

            value = run_gate(args.receipt)
            exit_code = GATE_EXIT_CODES[value["disposition"]]
        except GateError as exc:
            value = {"error": str(exc)}
            exit_code = 2
    elif args.command == "sim":
        try:
            value, exit_code = simrun.run_sim(
                args.sim_path,
                timeout_seconds=args.timeout,
                interpreter=args.python,
            )
        except simrun.SimRunError as exc:
            print(f"constraintbox sim: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        if args.receipt is not None:
            try:
                simrun.write_receipt_atomic(args.receipt, value)
            except OSError as exc:
                print(
                    f"constraintbox sim: could not write receipt "
                    f"{args.receipt}: {exc}",
                    file=sys.stderr,
                )
                exit_code = 2
    elif args.command == "ratchet":
        try:
            value, exit_code = ratchetrun.run_ratchet_tick(
                v2=args.v2,
                timeout_seconds=args.timeout,
                interpreter=args.python,
                pin_hashseed=not args.no_pin_hashseed,
            )
        except ratchetrun.RatchetRunError as exc:
            print(f"constraintbox ratchet: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        if args.receipt is not None:
            try:
                ratchetrun.write_receipt_atomic(args.receipt, value)
            except OSError as exc:
                print(
                    f"constraintbox ratchet: could not write receipt "
                    f"{args.receipt}: {exc}",
                    file=sys.stderr,
                )
                exit_code = 2
    else:
        raise SystemExit(f"unreachable command: {args.command}")
    rendered = json.dumps(value, sort_keys=True, indent=2) + "\n"
    output = getattr(args, "output", None)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
        temporary.write_text(rendered, encoding="utf-8")
        os.replace(temporary, output)
    print(rendered, end="")
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
