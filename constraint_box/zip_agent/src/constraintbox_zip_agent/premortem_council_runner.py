from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .protocol import ZipJobRefusal, declared_controller_src, materialize_controller_bound_prompt

PROFILES = {
    "premortem": {
        "schema": "constraintbox.premortem-council-round.v1",
        "wave_id": "zip-premortem-loop",
        "parent_id": "premortem-council",
        "run_prefix": "zip-premortem",
        "task_title": "PREMORTEM CELL",
        "task_focus": (
            "The target failed six months later. Distinguish delivery from cognition, integrity from semantics, "
            "hooks from CB, and CB-run tools from model-run tools."
        ),
        "return_fields": (
            "lens, target_sha256, failure_mechanisms, direct_evidence, limits, falsifiers, "
            "earliest_warnings, finite_repairs, rerun_tests, claim_ceiling"
        ),
        "claim_ceiling": "advisory premortem council only; no authority, promotion, or release",
        "lenses": {
            "likely_failure": "Identify the most likely concrete mechanism by which this ZIP runtime fails in ordinary repeated use.",
            "dangerous_failure": "Identify the most dangerous authority, containment, or evidence failure even if it is less frequent.",
            "hidden_assumption": "Identify the strongest hidden assumption that lets passing tests or receipts overstate what occurred."
        },
        "seeds": {"likely_failure": 460101, "dangerous_failure": 460202, "hidden_assumption": 460303}
    },
    "strategy": {
        "schema": "constraintbox.strategy-council-round.v1",
        "wave_id": "cb-strategy-wave",
        "parent_id": "strategy-council",
        "run_prefix": "cb-strategy",
        "task_title": "SYSTEMS STRATEGY CELL",
        "task_focus": (
            "Evaluate whether the current local repairs preserve the owner's larger ConstraintBox object. "
            "Step back from local optimization, preserve alternative futures, and distinguish current evidence from hypotheses."
        ),
        "return_fields": (
            "lens, target_sha256, system_boundary, active_feedback_loops, direct_evidence, missing_context, "
            "local_optimization_risks, preserved_alternatives, intervention, falsifiers, context_delta, disposition, claim_ceiling"
        ),
        "claim_ceiling": "advisory systems-strategy council only; no test, gate, promotion, or release authority",
        "lenses": {
            "systems_boundary": "Name the actual system boundary, active feedback loops, and second-order effects of the current CB, ZIP, hook, MMM, and council work.",
            "object_preservation": "Check whether the current repairs preserve the owner's primary object or substitute a proxy such as hooks, receipts, models, or councils for CB.",
            "divergent_futures": "Preserve multiple plausible next paths, identify premature collapse, and recommend the smallest intervention that improves direction without canonizing a hypothesis."
        },
        "seeds": {"systems_boundary": 461101, "object_preservation": 461202, "divergent_futures": 461303}
    }
}

REPO: Path
MMM: Path
CONTROLLER: Path
PROFILE: dict[str, Any]
LENSES: dict[str, str]
SEEDS: dict[str, int]
MEMBERS: dict[str, dict[str, Any]]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def controller_env() -> dict[str, str]:
    """Run explicit controller tools/adapters without ambient package lookup."""

    if "CONTROLLER" not in globals():
        raise ZipJobRefusal("HOLD_PROVIDER_CONTROLLER_UNBOUND", "controller_src")
    env = dict(os.environ)
    env["CB_CONTROLLER_SRC"] = str(CONTROLLER)
    env["PYTHONPATH"] = str(CONTROLLER)
    env["PYTHONNOUSERSITE"] = "1"
    return env


def source_bundle(target: Path) -> tuple[bytes, str, dict[str, str]]:
    rows: dict[str, str] = {}
    chunks: list[bytes] = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.suffix.lower() not in {".py", ".md", ".json", ".toml", ".txt", ".sh"}:
            continue
        rel = path.relative_to(target).as_posix()
        raw = path.read_bytes()
        rows[rel] = sha(raw)
        chunks.extend([
            f"\n\n===== FILE {rel} sha256={rows[rel]} =====\n".encode(),
            raw,
        ])
    digest = sha(canonical(rows))
    return b"".join(chunks), digest, rows


def make_task(root: Path, target: Path, lens: str, round_no: int, repair_note: str) -> Path:
    bundle, target_digest, rows = source_bundle(target)
    baseline = (root / f"round{round_no}-baseline.txt").read_bytes()
    task = (
        f"{PROFILE['task_title']}\n"
        f"round: {round_no}\n"
        f"lens: {lens}\n"
        f"target_sha256: {target_digest}\n"
        f"lens_instruction: {LENSES[lens]}\n"
        f"prior_repairs: {repair_note or 'none'}\n\n"
        "The target is a local ConstraintBox ZIP-agent and council prototype. "
        f"{PROFILE['task_focus']} "
        "Use only the supplied source and baseline. Do not invent a web UI. "
        "Do not propose model names as kernel policy. Treat the context snapshot as noncanonical input, not truth. "
        "Return concrete evidence, limits, and falsifiers rather than narrative confidence.\n\n"
        "Return ONLY one JSON object with exactly these fields: "
        f"{PROFILE['return_fields']}. "
        "All plural fields are arrays of strings. claim_ceiling must say advisory_only.\n\n"
        f"SOURCE_REGISTRY={json.dumps(rows, sort_keys=True)}\n"
        f"BASELINE_TEST_OUTPUT:\n{baseline.decode('utf-8', errors='replace')}\n"
        "SOURCE_BUNDLE:\n"
    ).encode() + bundle
    path = root / f"round{round_no}" / lens / "task.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(task)
    return path


def prepare(root: Path, target: Path, lens: str, round_no: int, repair_note: str) -> dict[str, Any]:
    task = make_task(root, target, lens, round_no, repair_note)
    cell = root / f"round{round_no}" / lens
    command = [
        sys.executable, str(MMM), "prepare",
        "--task-file", str(task), "--output-dir", str(cell / "preload"),
        "--run-id", f"{PROFILE['run_prefix']}-r{round_no}", "--agent-id", lens,
        "--parent-id", str(PROFILE["parent_id"]), "--wave-id", str(PROFILE["wave_id"]),
        "--round", str(round_no), "--depth", "1", "--seed", str(SEEDS[lens]),
        "--voice-count", "3", "--voice-variant", "compact", "--max-bytes", "700000",
    ]
    done = subprocess.run(command, capture_output=True, text=True, env=controller_env(), check=False)
    if done.returncode:
        raise RuntimeError(done.stdout + done.stderr)
    return json.loads((cell / "preload" / "preload_receipt.json").read_text())


def write_request(
    member: dict[str, Any],
    request_id: str,
    prompt: Path,
    cwd: Path,
    out: Path,
    controller_src: Path,
    *,
    grok_max_turns: int = 4,
) -> tuple[Path, Path, Path]:
    kind = str(member["kind"])
    model = str(member["model"])
    runner = Path(str(member["runner_path"])).expanduser().resolve()
    request = out / "request.json"
    response = out / "response.json"
    receipt = out / "adapter_receipt.json"
    if kind == "codex":
        value = {
            "schema": "constraintbox.codex-cli-request.v1", "request_id": request_id,
            "runner_path": str(runner), "model": model,
            "reasoning_effort": str(member.get("reasoning_effort") or "max"),
            "sandbox_mode": "read-only", "prompt_path": str(prompt), "cwd": str(cwd),
        }
    elif kind == "grok":
        value = {
            "schema": "constraintbox.grok-cli-request.v1", "request_id": request_id,
            "runner_path": str(runner), "model": model, "prompt_path": str(prompt),
            "cwd": str(cwd), "max_turns": grok_max_turns, "tools": "", "permission_mode": "plan",
        }
    else:
        value = {
            "schema": "constraintbox.claude-bridge-request.v1", "request_id": request_id,
            "bridge_path": str(Path(str(member["bridge_path"])).expanduser().resolve()),
            "model": model, "effort": str(member.get("reasoning_effort") or "high"),
            "budget_usd": float(member.get("budget_usd") or 1.5),
            "timeout_seconds": 900, "prompt_path": str(prompt), "cwd": str(cwd),
            "out_dir": str(out / "claude"), "tools": "",
        }
    bound = out / "adapter_prompt.txt"
    try:
        fields = materialize_controller_bound_prompt(prompt, bound, controller_src)
    except ZipJobRefusal as exc:
        raise RuntimeError(f"{exc.reason_code}: {exc}") from exc
    value["prompt_path"] = str(bound)
    value["mmm_packs"] = list(fields["mmm_packs"])
    value["mmm_sha256"] = fields["mmm_sha256"]
    request.write_bytes(canonical(value))
    return request, response, receipt


def extract(kind: str, adapter: dict[str, Any], response: Path) -> bytes:
    if kind == "codex":
        messages = adapter.get("agent_messages") or []
        return (messages[-1] if messages else "").encode()
    if kind == "grok":
        try:
            value = json.loads(response.read_bytes())
            return str(value.get("text") or "").encode()
        except Exception:
            return b""
    path = adapter.get("nested_output_path")
    return Path(path).read_bytes() if isinstance(path, str) and Path(path).is_file() else b""


def call_one(
    root: Path,
    target: Path,
    lens: str,
    round_no: int,
    member: str,
    *,
    grok_max_turns: int = 4,
) -> dict[str, Any]:
    member_spec = MEMBERS[member]
    kind, model = str(member_spec["kind"]), str(member_spec["model"])
    cell = root / f"round{round_no}" / lens
    base_out = cell / member
    out = base_out
    if (out / "request.json").exists() or (out / "adapter_receipt.json").exists():
        retry_index = 2
        while (base_out / f"attempt-{retry_index}").exists():
            retry_index += 1
        out = base_out / f"attempt-{retry_index}"
    out.mkdir(parents=True, exist_ok=True)
    prompt = cell / "preload" / "composed_prompt.md"
    preload_path = cell / "preload" / "preload_receipt.json"
    preload = json.loads(preload_path.read_text())
    request_id = f"pm046-r{round_no}-{lens}-{member}"
    request, response, receipt_path = write_request(
        member_spec,
        request_id,
        prompt,
        target,
        out,
        CONTROLLER,
        grok_max_turns=grok_max_turns,
    )
    adapter_script = Path(str(member_spec["adapter_path"])).expanduser().resolve()
    command = [sys.executable, str(adapter_script), "--request", str(request), "--receipt", str(receipt_path)]
    if kind in {"codex", "grok"}:
        command.extend(["--response", str(response), "--timeout", "900"])
    env = controller_env()
    if kind == "codex":
        env["CODEX_HOME"] = str(Path(str(member_spec["codex_home"])).expanduser().resolve())
    done = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=960,
        env=env,
        check=False,
    )
    adapter = json.loads(receipt_path.read_text()) if receipt_path.is_file() else {
        "disposition": "FAILED", "reason_code": "MISSING_ADAPTER_RECEIPT"
    }
    raw = extract(kind, adapter, response)
    (out / "model_output.txt").write_bytes(raw)
    if kind == "codex":
        observed = [adapter.get("model_observed")] if adapter.get("model_observed") else []
    elif kind == "grok":
        observed = adapter.get("models_observed_in_output") or []
    else:
        observed = adapter.get("models_observed") or []
    terminal = "COMPLETED" if adapter.get("disposition") == "OBSERVED" else "REFUSED"
    call = {
        "schema": "constraintbox.provider-call.v1",
        "run_id": f"{PROFILE['run_prefix']}-r{round_no}", "agent_id": lens,
        "parent_id": PROFILE["parent_id"], "wave_id": PROFILE["wave_id"],
        "round": round_no, "depth": 1,
        "preload_receipt_sha256": sha(preload_path.read_bytes()),
        "composed_prompt_sha256": preload["composed_prompt_sha256"],
        "provider_request_id": request_id, "terminal_state": terminal,
        "provider": kind, "model_requested": model, "models_observed": observed,
        "adapter_disposition": adapter.get("disposition"),
        "adapter_reason_code": adapter.get("reason_code"),
        "adapter_receipt_sha256": sha(receipt_path.read_bytes()) if receipt_path.is_file() else None,
        "artifact_dir": str(out),
        "output_sha256": sha(raw), "output_bytes": len(raw), "process_returncode": done.returncode,
    }
    call_path = out / "provider_call_receipt.json"
    call_path.write_bytes(canonical(call))
    verify = subprocess.run([
        sys.executable, str(MMM), "verify", "--receipt", str(preload_path),
        "--call-receipt", str(call_path), "--expect-run-id", call["run_id"],
        "--expect-agent-id", lens, "--expect-parent-id", str(PROFILE["parent_id"]),
        "--expect-wave-id", str(PROFILE["wave_id"]), "--expect-round", str(round_no),
        "--expect-depth", "1",
    ], capture_output=True, text=True, env=controller_env(), check=False)
    call["mmm_verify"] = json.loads(verify.stdout) if verify.stdout.strip() else {"disposition": "FAILED"}
    return call


def parse_json(raw: bytes) -> dict[str, Any] | None:
    text = raw.decode("utf-8", errors="replace").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip()
    try:
        value = json.loads(text)
        if isinstance(value, dict) and isinstance(value.get("result"), str):
            return parse_json(value["result"].encode())
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 < end:
            try:
                value = json.loads(text[start:end + 1])
                if isinstance(value, dict) and isinstance(value.get("result"), str):
                    return parse_json(value["result"].encode())
                return value if isinstance(value, dict) else None
            except json.JSONDecodeError:
                return None
        return None


def main() -> int:
    global REPO, MMM, CONTROLLER, PROFILE, LENSES, SEEDS, MEMBERS
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--target", type=Path, required=True)
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--profile", choices=tuple(PROFILES), default="premortem")
    ap.add_argument("--run-config", type=Path, required=True)
    ap.add_argument("--repair-note", default="")
    ap.add_argument("--retry-lens")
    ap.add_argument("--retry-member")
    ap.add_argument("--grok-max-turns", type=int, default=4)
    args = ap.parse_args()
    runtime = json.loads(args.run_config.read_text(encoding="utf-8"))
    if runtime.get("schema") != "constraintbox.council-run-config.v1":
        raise SystemExit("invalid council run config schema")
    REPO = Path(str(runtime["repo_path"])).expanduser().resolve()
    MMM = Path(str(runtime["mmm_script"])).expanduser().resolve()
    try:
        CONTROLLER = declared_controller_src(runtime.get("controller_src"))
    except ZipJobRefusal as exc:
        raise SystemExit(f"{exc.reason_code}:{exc.detail}") from exc
    member_rows = runtime.get("members")
    if not isinstance(member_rows, list) or not 2 <= len(member_rows) <= 8:
        raise SystemExit("run config needs 2..8 members")
    MEMBERS = {}
    for row in member_rows:
        if not isinstance(row, dict) or row.get("kind") not in {"codex", "grok", "claude"}:
            raise SystemExit("invalid council member")
        member_id = str(row.get("member_id") or "")
        if not member_id or member_id in MEMBERS or not row.get("model"):
            raise SystemExit("invalid or duplicate member id")
        for field in ("runner_path", "adapter_path"):
            if not Path(str(row.get(field) or "")).expanduser().is_file():
                raise SystemExit(f"member {member_id} missing {field}")
        if row["kind"] == "claude" and not Path(str(row.get("bridge_path") or "")).expanduser().is_file():
            raise SystemExit(f"member {member_id} missing bridge_path")
        if row["kind"] == "codex":
            codex_home = Path(str(row.get("codex_home") or "")).expanduser()
            if not codex_home.is_absolute() or not codex_home.is_dir():
                raise SystemExit(f"member {member_id} missing codex_home")
        MEMBERS[member_id] = row
    PROFILE = PROFILES[args.profile]
    LENSES = dict(PROFILE["lenses"])
    SEEDS = dict(PROFILE["seeds"])
    root, target, round_no = args.root.resolve(), args.target.resolve(), args.round
    if bool(args.retry_lens) != bool(args.retry_member):
        raise SystemExit("--retry-lens and --retry-member must be supplied together")
    if args.retry_lens and (args.retry_lens not in LENSES or args.retry_member not in MEMBERS):
        raise SystemExit("unknown retry cell")
    if not 1 <= args.grok_max_turns <= 16:
        raise SystemExit("--grok-max-turns must be in 1..16")
    if args.retry_lens:
        receipt_path = root / f"round{round_no}" / "round_receipt.json"
        receipt = json.loads(receipt_path.read_text())
        if receipt["target_registry_sha256"] != source_bundle(target)[1]:
            raise SystemExit("target changed since the round receipt")
        call = call_one(
            root,
            target,
            args.retry_lens,
            round_no,
            args.retry_member,
            grok_max_turns=args.grok_max_turns,
        )
        raw = (Path(call["artifact_dir"]) / "model_output.txt").read_bytes()
        parsed = parse_json(raw)
        cell = receipt["cells"][args.retry_lens]
        row = next(item for item in cell["members"] if item["member"] == args.retry_member)
        row["call"] = call
        row["parsed_output"] = parsed
        cell["all_models_completed"] = all(
            item["call"]["terminal_state"] == "COMPLETED" for item in cell["members"]
        )
        cell["all_mmm_verified"] = all(
            item["call"]["mmm_verify"].get("disposition") == "MMM_CALL_VERIFIED"
            for item in cell["members"]
        )
        receipt["all_declared_models_completed"] = all(
            value["all_models_completed"] for value in receipt["cells"].values()
        )
        receipt["all_calls_mmm_verified"] = all(
            value["all_mmm_verified"] for value in receipt["cells"].values()
        )
        receipt["all_outputs_normalized"] = all(
            isinstance(item.get("parsed_output"), dict)
            for value in receipt["cells"].values()
            for item in value["members"]
        )
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps({
            "round_receipt": str(receipt_path),
            "retried": f"{args.retry_lens}:{args.retry_member}",
            "adapter_disposition": call["adapter_disposition"],
            "models_completed": receipt["all_declared_models_completed"],
            "mmm_verified": receipt["all_calls_mmm_verified"],
            "outputs_normalized": receipt["all_outputs_normalized"],
        }, indent=2, sort_keys=True))
        return 0 if (
            receipt["all_declared_models_completed"]
            and receipt["all_calls_mmm_verified"]
            and receipt["all_outputs_normalized"]
        ) else 2
    preloads = {lens: prepare(root, target, lens, round_no, args.repair_note) for lens in LENSES}
    verify_round = subprocess.run([
        sys.executable, str(MMM), "verify-round", "--receipts",
        *[str(root / f"round{round_no}" / lens / "preload" / "preload_receipt.json") for lens in LENSES],
    ], capture_output=True, text=True, check=False)
    jobs = [(lens, member) for lens in LENSES for member in MEMBERS]
    with ThreadPoolExecutor(max_workers=6) as pool:
        calls = list(pool.map(lambda pair: call_one(root, target, pair[0], round_no, pair[1]), jobs))
    cells: dict[str, Any] = {}
    for lens in LENSES:
        rows = []
        for member in MEMBERS:
            raw = (root / f"round{round_no}" / lens / member / "model_output.txt").read_bytes()
            call = next(row for row in calls if row["agent_id"] == lens and row["provider_request_id"].endswith(member))
            rows.append({"member": member, "call": call, "parsed_output": parse_json(raw)})
        cells[lens] = {
            "preload_receipt": preloads[lens], "members": rows,
            "all_models_completed": all(row["call"]["terminal_state"] == "COMPLETED" for row in rows),
            "all_mmm_verified": all(row["call"]["mmm_verify"].get("disposition") == "MMM_CALL_VERIFIED" for row in rows),
        }
    receipt = {
        "schema": PROFILE["schema"], "profile": args.profile, "round": round_no,
        "target_registry_sha256": source_bundle(target)[1],
        "mmm_round_verification": json.loads(verify_round.stdout), "cells": cells,
        "all_declared_models_completed": all(cell["all_models_completed"] for cell in cells.values()),
        "all_calls_mmm_verified": all(cell["all_mmm_verified"] for cell in cells.values()),
        "promotion_allowed": False,
        "claim_ceiling": PROFILE["claim_ceiling"],
    }
    path = root / f"round{round_no}" / "round_receipt.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "round_receipt": str(path), "target_sha256": receipt["target_registry_sha256"],
        "models_completed": receipt["all_declared_models_completed"],
        "mmm_verified": receipt["all_calls_mmm_verified"],
        "member_states": {lens: {row["member"]: row["call"]["adapter_disposition"] for row in cell["members"]} for lens, cell in cells.items()},
    }, indent=2, sort_keys=True))
    return 0 if receipt["all_declared_models_completed"] and receipt["all_calls_mmm_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
