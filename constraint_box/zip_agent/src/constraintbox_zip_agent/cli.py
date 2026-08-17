from __future__ import annotations

import argparse
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path

from .cache import cache_result
from .council_zip import COUNCIL_MEMBERS as COUNCIL_ROSTERS
from .council_zip import VOICES as COUNCIL_VOICES
from .council_zip import build_named_council_packet
from .council_zip import build_three_member_council_packet
from .failure_wave import build_demo_packet, build_failure_wave_packet
from .operation_ids import KNOWN_OPERATION_IDS
from .operation_probe_field import build_operation_probe_field_packet
from .prompt_handshake import build_prompt_handshake_packet
from .project_ledger import (
    ProjectLedger,
    import_artifact,
    import_codex_rollout,
    import_hermes_session,
    record_text_event,
    write_current_view,
)
from .protocol import ZipJobRefusal, sha256_bytes, strict_json_loads, validate_packet, validate_return_zip
from .replay_verifier import packet_replay_is_supported
from .runtime import execute_packet
from .work_cycle import build_work_cycle_packet


def _emit(value: dict[str, object]) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _write_distinct(source: Path | None, destination: Path, data: bytes) -> None:
    resolved = destination.expanduser().resolve()
    if source is not None and source.expanduser().resolve() == resolved:
        raise ZipJobRefusal("REFUSE_INPUT_OUTPUT_ALIAS", str(resolved))
    _atomic_write(resolved, data)


def _failure_report(return_bytes: bytes) -> dict[str, object]:
    with zipfile.ZipFile(io.BytesIO(return_bytes), "r") as archive:
        data = archive.read("output/failure_wave.json")
    report = strict_json_loads(data, label="output/failure_wave.json")
    if not isinstance(report, dict):
        raise ZipJobRefusal("REFUSE_FAILURE_REPORT_SHAPE")
    return report


def _council_agent_file(agent_id: str) -> bytes:
    role = {
        "failure": "Find one concrete failure mechanism and its finite falsifier.",
        "repair": "Propose one bounded repair candidate; do not edit or promote source.",
        "strategy": "Check the larger owner object, proxy drift, and one preserved alternative.",
        "likely": "Find the most likely concrete failure mechanism and one finite falsifier.",
        "dangerous": "Find the most dangerous authority or evidence failure and one finite falsifier.",
        "assumption": "Find the strongest hidden assumption and one finite falsifier.",
        "bypass": "Find the most likely bypass around a declared gate and one finite falsifier.",
        "fail_open": "Find a path that turns missing evidence into continued execution and one finite falsifier.",
        "authority_swap": "Find a place where a valid local artifact could be mistaken for authority and one finite falsifier.",
        "smallest": "Propose the smallest repair to the bound failure return; do not edit source.",
        "test": "Design the finite positive, refusal, replay, and mutation tests for the bound repair.",
        "ceiling": "Audit the repair claim ceiling and name what remains unproved.",
        "systems_boundary": "Map the actual system boundary and active feedback loops.",
        "object_preservation": "Check whether the owner object is preserved or replaced by a proxy.",
        "divergent_futures": "Keep multiple next paths live and resist premature convergence.",
    }.get(agent_id)
    if role is None:
        raise ZipJobRefusal("REFUSE_COUNCIL_RUN_CONFIG", "agent_id")
    return (
        f"role: {agent_id}\n"
        f"{role}\n"
        "Read every assigned file in the controller-provided order.\n"
        "Write the exact required marker and council line.\n"
        "Include evidence:, limit:, falsifier:, and next: lines.\n"
        "Copy the skill-token and every assigned mmm-token from input/council_manifest.json.\n"
        "Copy the tool-token from output/tool_evidence.json.\n"
        "Never claim promotion or launch a child yourself.\n"
    ).encode("utf-8")


def _validated_prior_return(
    *, label: str, packet_path: Path | None, return_path: Path | None
) -> tuple[dict[str, bytes], list[str], str] | None:
    if packet_path is None and return_path is None:
        return None
    if packet_path is None or return_path is None:
        raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_RECEIPT", f"{label}_packet_or_return")
    packet_bytes = packet_path.read_bytes()
    return_bytes = return_path.read_bytes()
    manifest = validate_return_zip(return_bytes, input_packet_bytes=packet_bytes)
    return_digest = sha256_bytes(return_bytes)
    packet_target = f"input/prior/{label}/packet.zip"
    return_target = f"input/prior/{label}/return.zip"
    files = {
        packet_target: packet_bytes,
        return_target: return_bytes,
    }
    # The digest in bound_receipts must name bytes the isolated worker can
    # actually inspect.  Merely placing the ZIPs in the outer packet is not
    # enough: md-agent workspaces copy only declared context paths.
    context_paths: list[str] = [packet_target, return_target]
    with zipfile.ZipFile(io.BytesIO(return_bytes), "r") as archive:
        manifest_path = f"input/prior/{label}/RETURN_MANIFEST.json"
        files[manifest_path] = archive.read("RETURN_MANIFEST.json")
        context_paths.append(manifest_path)
        for source_path in sorted(manifest.required_output_file_list):
            if source_path == "output/roster_receipt.json" or source_path.endswith(".md"):
                target_path = f"input/prior/{label}/{source_path.removeprefix('output/')}"
                files[target_path] = archive.read(source_path)
                context_paths.append(target_path)
    return files, context_paths, return_digest


def _build_council_from_files(
    *,
    owner_prompt: Path,
    run_config: Path,
    mmm_dir: Path,
    council_id: str = "failure-repair-strategy",
    failure_packet: Path | None = None,
    failure_return: Path | None = None,
    repair_packet: Path | None = None,
    repair_return: Path | None = None,
    context_files: list[Path] | None = None,
) -> bytes:
    config = strict_json_loads(run_config.read_bytes(), label=str(run_config))
    if not isinstance(config, dict) or config.get("schema") != "constraintbox.internal-council-run.v1":
        raise ZipJobRefusal("REFUSE_COUNCIL_RUN_CONFIG", "schema")
    expected_members = COUNCIL_ROSTERS.get(council_id)
    if expected_members is None:
        raise ZipJobRefusal("REFUSE_COUNCIL_RUN_CONFIG", "council_id")
    agents = config.get("agents")
    if not isinstance(agents, list) or [row.get("agent_id") for row in agents if isinstance(row, dict)] != list(expected_members):
        raise ZipJobRefusal("REFUSE_COUNCIL_RUN_CONFIG", "agents")
    prior_files: dict[str, bytes] = {}
    prior_context_paths: list[str] = []
    bound_receipts: dict[str, str] = {}
    for index, source in enumerate(context_files or []):
        resolved = source.expanduser().resolve()
        if not resolved.is_file():
            raise ZipJobRefusal("REFUSE_COUNCIL_CONTEXT_SOURCE", str(resolved))
        target = f"input/context/{index:03d}-{resolved.name}"
        prior_files[target] = resolved.read_bytes()
        prior_context_paths.append(target)
    for label, packet_path, return_path in (
        ("failure", failure_packet, failure_return),
        ("repair", repair_packet, repair_return),
    ):
        validated = _validated_prior_return(
            label=label, packet_path=packet_path, return_path=return_path
        )
        if validated is None:
            continue
        files, context_paths, return_digest = validated
        prior_files.update(files)
        prior_context_paths.extend(context_paths)
        bound_receipts[f"{label}_return_sha256"] = return_digest
    expected_receipts = {
        "failure-repair-strategy": set(),
        "failure": set(),
        "failure-deep": set(),
        "repair": {"failure_return_sha256"},
        "strategy": {"failure_return_sha256", "repair_return_sha256"},
    }[council_id]
    if set(bound_receipts) != expected_receipts:
        raise ZipJobRefusal(
            "REFUSE_COUNCIL_ZIP_RECEIPT",
            f"expected={sorted(expected_receipts)};observed={sorted(bound_receipts)}",
        )
    built_agents: list[dict[str, object]] = []
    extra_files: dict[str, bytes] = {}
    for row in agents:
        if not isinstance(row, dict):
            raise ZipJobRefusal("REFUSE_COUNCIL_RUN_CONFIG", "agent")
        agent_id = str(row["agent_id"])
        value = dict(row)
        value.update(
            {
                "agent_path": f"AGENTS/{agent_id}.md",
                "output_path": f"output/{agent_id}.md",
                "required_fragments": [
                    "evidence:",
                    "limit:",
                    "falsifier:",
                    "next:",
                    *[
                        f"prior-return-token: {digest}"
                        for digest in bound_receipts.values()
                    ],
                ],
                "context_paths": list(
                    dict.fromkeys(
                        [*list(row.get("context_paths") or []), *prior_context_paths]
                    )
                ),
                "max_output_bytes": int(row.get("max_output_bytes") or 65536),
            }
        )
        built_agents.append(value)
        extra_files[f"AGENTS/{agent_id}.md"] = _council_agent_file(agent_id)
    extra_files.update(prior_files)
    mmm_files: dict[str, bytes] = {}
    for voice in COUNCIL_VOICES:
        source = mmm_dir / f"MMM_VOICE_{voice.upper()}_COMPACT_v4_1.md"
        if not source.is_file():
            raise ZipJobRefusal("REFUSE_COUNCIL_ZIP_MMM_SOURCE", str(source))
        mmm_files[f"MMMS/{voice}.md"] = source.read_bytes()
    seed = config.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ZipJobRefusal("REFUSE_COUNCIL_RUN_CONFIG", "seed")
    run_id = config.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ZipJobRefusal("REFUSE_COUNCIL_RUN_CONFIG", "run_id")
    if council_id == "failure-repair-strategy":
        return build_three_member_council_packet(
            owner_prompt=owner_prompt.read_bytes(),
            seed=seed,
            run_id=run_id,
            agents=built_agents,
            mmm_files=mmm_files,
            extra_files=extra_files,
        )
    return build_named_council_packet(
        council_id=council_id,
        owner_prompt=owner_prompt.read_bytes(),
        seed=seed,
        run_id=run_id,
        agents=built_agents,
        mmm_files=mmm_files,
        extra_files=extra_files,
        bound_receipts=bound_receipts,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cb-zip")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a ZIP_JOB without executing it")
    validate.add_argument("packet", type=Path)

    run = sub.add_parser("run", help="execute one validated ZIP_JOB")
    run.add_argument("packet", type=Path)
    run.add_argument("--return-zip", required=True, type=Path)
    run.add_argument("--cache-dir", type=Path)

    demo = sub.add_parser("build-demo", help="create a deterministic one-operation packet")
    demo.add_argument("--out", required=True, type=Path)

    work_cycle = sub.add_parser("build-work-cycle", help="build one 93-tool ZIP probe work cycle")
    work_cycle.add_argument("--prompt", required=True, type=Path)
    work_cycle.add_argument("--tool-manifest", required=True, type=Path)
    work_cycle.add_argument("--prior-field", required=True, type=Path)
    work_cycle.add_argument("--seed", type=int, default=81402)
    work_cycle.add_argument("--jobs", type=int, default=16)
    work_cycle.add_argument("--pair-samples", type=int, default=128)
    work_cycle.add_argument("--out", required=True, type=Path)

    operation_probe = sub.add_parser(
        "build-operation-probe",
        help="build one model-free explicit-operation probe field ZIP",
    )
    operation_probe.add_argument("--request", required=True, type=Path)
    operation_probe.add_argument("--tool-manifest", required=True, type=Path)
    operation_probe.add_argument("--operation-catalog", required=True, type=Path)
    operation_probe.add_argument("--job-id", default="operation-probe-field")
    operation_probe.add_argument("--out", required=True, type=Path)

    handshake = sub.add_parser(
        "build-prompt-handshake",
        help="build one deterministic prompt-handshake ZIP",
    )
    handshake.add_argument("--owner-prompt", required=True, type=Path)
    handshake.add_argument("--composed-prompt", required=True, type=Path)
    handshake.add_argument("--preload-receipt", required=True, type=Path)
    handshake.add_argument("--mmm-bundle", required=True, type=Path)
    handshake.add_argument("--run-settings", required=True, type=Path)
    handshake.add_argument("--tool-qualification", required=True, type=Path)
    handshake.add_argument("--provider-calls", required=True, type=Path)
    handshake.add_argument("--source-receipts", required=True, type=Path)
    handshake.add_argument("--template-catalog", required=True, type=Path)
    handshake.add_argument("--candidate-observations", required=True, type=Path)
    handshake.add_argument("--tool-field-packet", required=True, type=Path)
    handshake.add_argument("--tool-field-return", required=True, type=Path)
    handshake.add_argument("--handshake-test-report", required=True, type=Path)
    handshake.add_argument("--out", required=True, type=Path)

    council = sub.add_parser(
        "build-council",
        help="build one three-member council ZIP from exact mini-MMM bytes and run data",
    )
    council.add_argument("--owner-prompt", required=True, type=Path)
    council.add_argument("--run-config", required=True, type=Path)
    council.add_argument("--mmm-dir", required=True, type=Path)
    council.add_argument(
        "--council-id",
        choices=tuple(COUNCIL_ROSTERS),
        default="failure-repair-strategy",
    )
    council.add_argument("--failure-packet", type=Path)
    council.add_argument("--failure-return", type=Path)
    council.add_argument("--repair-packet", type=Path)
    council.add_argument("--repair-return", type=Path)
    council.add_argument("--context-file", action="append", default=[], type=Path)
    council.add_argument("--out", required=True, type=Path)

    failure = sub.add_parser("failure-wave", help="run the ZIP-native three-child self-falsifier")
    failure.add_argument("--target", required=True, type=Path)
    failure.add_argument(
        "--target-return",
        type=Path,
        help="verify this existing return in authority audit; do not re-execute the target",
    )
    failure.add_argument("--wave-packet", type=Path)
    failure.add_argument("--return-zip", required=True, type=Path)
    failure.add_argument("--cache-dir", type=Path)

    inspect_return = sub.add_parser("verify-return", help="verify a return ZIP and its input binding")
    inspect_return.add_argument("return_zip", type=Path)
    inspect_return.add_argument("--input", required=True, type=Path)

    project_sync = sub.add_parser(
        "project-sync",
        help="import exact Codex, Hermes, and file evidence into the append-only project ledger",
    )
    project_sync.add_argument("--project-state", required=True, type=Path)
    project_sync.add_argument("--codex-rollout", type=Path)
    project_sync.add_argument("--hermes-db", type=Path)
    project_sync.add_argument("--hermes-session")
    project_sync.add_argument("--artifact", action="append", default=[], type=Path)

    project_record = sub.add_parser(
        "project-record",
        help="append one digest-bound text event to the project ledger",
    )
    project_record.add_argument("--project-state", required=True, type=Path)
    project_record.add_argument("--source-file", required=True, type=Path)
    project_record.add_argument("--event-id", required=True)
    project_record.add_argument("--event-type", required=True)
    project_record.add_argument("--source-kind", required=True)
    project_record.add_argument("--run-id", action="append", default=[])
    project_record.add_argument("--receipt-id", action="append", default=[])
    project_record.add_argument("--expected-head-sha256")

    project_verify = sub.add_parser(
        "project-verify", help="verify the project event chain and every retained object"
    )
    project_verify.add_argument("--project-state", required=True, type=Path)

    project_render = sub.add_parser(
        "project-render", help="render the non-authoritative current project view"
    )
    project_render.add_argument("--project-state", required=True, type=Path)
    project_render.add_argument("--out", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "project-sync":
            ledger = ProjectLedger(args.project_state)
            imports: list[dict[str, object]] = []
            if args.codex_rollout is not None:
                imports.append(import_codex_rollout(ledger, args.codex_rollout))
            if (args.hermes_db is None) != (args.hermes_session is None):
                raise ZipJobRefusal(
                    "REFUSE_PROJECT_SYNC_ARGUMENTS", "hermes-db and hermes-session are paired"
                )
            if args.hermes_db is not None:
                imports.append(import_hermes_session(ledger, args.hermes_db, args.hermes_session))
            for artifact in args.artifact:
                imports.append(import_artifact(ledger, artifact))
            verified = ledger.verify()
            current_view = write_current_view(ledger, args.project_state / "CURRENT.md")
            _emit(
                {
                    "disposition": "PROJECT_CONTEXT_SYNCED_LOCAL",
                    "imports": imports,
                    "event_count": verified["event_count"],
                    "head_sha256": verified["head_sha256"],
                    "current_view": current_view,
                    "promotion_allowed": False,
                }
            )
            return 0
        if args.command == "project-record":
            ledger = ProjectLedger(args.project_state)
            result = record_text_event(
                ledger,
                args.source_file,
                event_id=args.event_id,
                event_type=args.event_type,
                source_kind=args.source_kind,
                run_ids=args.run_id,
                receipt_ids=args.receipt_id,
                expected_head_sha256=args.expected_head_sha256,
            )
            result["current_view"] = write_current_view(
                ledger, args.project_state / "CURRENT.md"
            )
            _emit(result)
            return 0
        if args.command == "project-verify":
            _emit(ProjectLedger(args.project_state).verify())
            return 0
        if args.command == "project-render":
            _emit(write_current_view(ProjectLedger(args.project_state), args.out))
            return 0
        if args.command == "validate":
            packet = args.packet.read_bytes()
            validated = validate_packet(packet, known_operations=set(KNOWN_OPERATION_IDS))
            _emit(
                {
                    "disposition": "ZIP_JOB_VALIDATED_LOCAL",
                    "job_id": validated.manifest.job_id,
                    "packet_sha256": validated.packet_sha256,
                    "task_count": len(validated.tasks),
                    "promotion_allowed": False,
                }
            )
            return 0
        if args.command == "build-demo":
            packet = build_demo_packet()
            _write_distinct(None, args.out, packet)
            _emit(
                {
                    "disposition": "ZIP_JOB_DEMO_BUILT",
                    "packet": str(args.out.resolve()),
                    "packet_sha256": sha256_bytes(packet),
                    "promotion_allowed": False,
                }
            )
            return 0
        if args.command == "build-work-cycle":
            packet = build_work_cycle_packet(
                prompt=args.prompt.read_bytes(),
                tool_manifest=args.tool_manifest.read_bytes(),
                prior_field_summary=args.prior_field.read_bytes(),
                seed=args.seed,
                jobs=args.jobs,
                pair_samples=args.pair_samples,
            )
            _write_distinct(None, args.out, packet)
            _emit(
                {
                    "disposition": "ZIP_PROBE_WORK_CYCLE_BUILT",
                    "packet": str(args.out.resolve()),
                    "packet_sha256": sha256_bytes(packet),
                    "promotion_allowed": False,
                }
            )
            return 0
        if args.command == "build-operation-probe":
            packet = build_operation_probe_field_packet(
                request=args.request.read_bytes(),
                manifest=args.tool_manifest.read_bytes(),
                operation_catalog=args.operation_catalog.read_bytes(),
                job_id=args.job_id,
            )
            _write_distinct(None, args.out, packet)
            _emit(
                {
                    "disposition": "ZIP_OPERATION_PROBE_BUILT_LOCAL",
                    "packet": str(args.out.resolve()),
                    "packet_sha256": sha256_bytes(packet),
                    "promotion_allowed": False,
                }
            )
            return 0
        if args.command == "build-prompt-handshake":
            packet = build_prompt_handshake_packet(
                owner_prompt=args.owner_prompt.read_bytes(),
                composed_prompt=args.composed_prompt.read_bytes(),
                preload_receipt=args.preload_receipt.read_bytes(),
                mmm_bundle=args.mmm_bundle.read_bytes(),
                run_settings=args.run_settings.read_bytes(),
                tool_qualification=args.tool_qualification.read_bytes(),
                provider_calls=args.provider_calls.read_bytes(),
                source_receipts=args.source_receipts.read_bytes(),
                template_catalog=args.template_catalog.read_bytes(),
                candidate_observations=args.candidate_observations.read_bytes(),
                tool_field_packet=args.tool_field_packet.read_bytes(),
                tool_field_return=args.tool_field_return.read_bytes(),
                handshake_test_report=args.handshake_test_report.read_bytes(),
            )
            _write_distinct(None, args.out, packet)
            _emit(
                {
                    "disposition": "PROMPT_HANDSHAKE_ZIP_BUILT_LOCAL",
                    "packet": str(args.out.resolve()),
                    "packet_sha256": sha256_bytes(packet),
                    "execution_authorized": False,
                    "promotion_allowed": False,
                }
            )
            return 0
        if args.command == "build-council":
            packet = _build_council_from_files(
                owner_prompt=args.owner_prompt,
                run_config=args.run_config,
                mmm_dir=args.mmm_dir,
                council_id=args.council_id,
                failure_packet=args.failure_packet,
                failure_return=args.failure_return,
                repair_packet=args.repair_packet,
                repair_return=args.repair_return,
                context_files=args.context_file,
            )
            _write_distinct(None, args.out, packet)
            _emit(
                {
                    "disposition": "COUNCIL_ZIP_BUILT_LOCAL",
                    "packet": str(args.out.resolve()),
                    "packet_sha256": sha256_bytes(packet),
                    "promotion_allowed": False,
                }
            )
            return 0
        if args.command == "run":
            packet = args.packet.read_bytes()
            if args.cache_dir is not None and not packet_replay_is_supported(packet):
                raise ZipJobRefusal("HOLD_CACHE_REPLAY_UNSUPPORTED")
            result = execute_packet(packet)
            cache_path = cache_result(args.cache_dir, packet, result) if args.cache_dir else None
            _write_distinct(args.packet, args.return_zip, result.return_zip_bytes)
            _emit(
                {
                    "disposition": "ZIP_JOB_EXECUTED_LOCAL",
                    "job_id": result.job_id,
                    "input_packet_sha256": result.input_packet_sha256,
                    "return_zip": str(args.return_zip.resolve()),
                    "return_zip_sha256": result.return_zip_sha256,
                    "cache_index": str(cache_path) if cache_path else None,
                    "promotion_allowed": False,
                }
            )
            return 0
        if args.command == "failure-wave":
            target = args.target.read_bytes()
            target_return = args.target_return.read_bytes() if args.target_return else None
            wave = build_failure_wave_packet(target, target_return=target_return)
            if args.wave_packet and args.wave_packet.expanduser().resolve() == args.return_zip.expanduser().resolve():
                raise ZipJobRefusal("REFUSE_OUTPUT_ALIAS", str(args.return_zip.resolve()))
            if args.wave_packet:
                _write_distinct(args.target, args.wave_packet, wave)
            if args.cache_dir is not None and not packet_replay_is_supported(wave):
                raise ZipJobRefusal("HOLD_CACHE_REPLAY_UNSUPPORTED")
            result = execute_packet(wave)
            cache_path = cache_result(args.cache_dir, wave, result) if args.cache_dir else None
            report = _failure_report(result.return_zip_bytes)
            _write_distinct(args.target, args.return_zip, result.return_zip_bytes)
            _emit(
                {
                    "disposition": "ZIP_FAILURE_WAVE_EXECUTED_LOCAL",
                    "target_sha256": sha256_bytes(target),
                    "wave_packet_sha256": sha256_bytes(wave),
                    "return_zip_sha256": result.return_zip_sha256,
                    "verdict": report.get("verdict"),
                    "member_status": report.get("member_status"),
                    "cache_index": str(cache_path) if cache_path else None,
                    "promotion_allowed": False,
                }
            )
            return 0 if report.get("verdict") == "PASS" else 1
        if args.command == "verify-return":
            input_bytes = args.input.read_bytes() if args.input else None
            expected = sha256_bytes(input_bytes) if input_bytes is not None else None
            data = args.return_zip.read_bytes()
            manifest = validate_return_zip(
                data,
                expected_input_sha256=expected,
                input_packet_bytes=input_bytes,
            )
            _emit(
                {
                    "disposition": "ZIP_RETURN_INTEGRITY_BOUND",
                    "job_id": manifest.job_id,
                    "input_packet_sha256": manifest.input_packet_sha256,
                    "return_zip_sha256": sha256_bytes(data),
                    "promotion_allowed": False,
                }
            )
            return 0
    except (OSError, ZipJobRefusal) as exc:
        reason = exc.reason_code if isinstance(exc, ZipJobRefusal) else "REFUSE_LOCAL_IO_ERROR"
        detail = exc.detail if isinstance(exc, ZipJobRefusal) else str(exc)
        _emit(
            {
                "disposition": reason,
                "detail": detail,
                "authoritative_output_written": False,
                "promotion_allowed": False,
            }
        )
        return 2
    return 2
