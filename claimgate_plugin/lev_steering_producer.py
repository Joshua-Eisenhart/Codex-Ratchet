#!/usr/bin/env python3
"""CR-side producer for ClaimGate -> Lev `.lev/steering/runs/<run-id>` projections.

WHAT THIS IS
------------
This is the PRODUCER half of the ClaimGate -> Lev host/source split. It renders a
`post_receipt_gate.sh` run on a CR receipt into the exact five-file source
projection that Lev's host consumer independently recomputes and consumes:

    <out-root>/<run-id>/
        run.json
        proof-spec.json
        eval-job.json
        eval-job-output.json
        boundary.json

The schema is defined, authoritatively, by the Lev SOURCE (the host is the spec):
    core/orchestration/src/proof/claim-gate-steering-run.ts   (consumer / validator)
    core/orchestration/src/proof/claim-gate-steering-produce.ts (Lev's own producer)
This file is a faithful Python mirror of that producer, driven by the CR hook
instead of a Lev council execution. Every field name, binding, and value here is
chosen to pass the host validator `validateProjection` with zero error findings.

HONEST CEILING — CONSUME SURFACE IS LIVE; SOURCE STILL CANNOT SELF-PROMOTE
-------------------------------------------------------------------------
The passive consume surface

    ./core/poly/bin/lev orchestration claimgate-steering consume <run-dir> [--json] [--no-write]

IS REACHABLE and was demonstrated live 2026-07-22 — run it from the Lev repo root
via the POLY BUILD binary (core/poly/bin/lev). The earlier "BLOCKED-ON-PRODUCER at
the CLI boundary" reading was a WRONG-BINARY artifact, not a missing surface: the
installed GLOBAL `lev` (~/.local/bin/lev, which respawns into the CR-facing lev-main
worktree) still has NO `orchestration` subcommand ("Unknown command: orchestration"),
but the poly build ships it. Verified: the `good` fixture -> host_consumed
(recomputed verdict pass); this producer's own cut_dependent_entropy.json projection
-> host_reviewed_failed (recomputed `conditional`, correctly NOT admitted — a probe
cannot self-promote). The ceiling below is what remains real: the producer prepares
the projection but never mints host authority — Lev recomputes and decides.

This producer prepares the source projection so recording works the instant the
surface ships. It does NOT — and cannot — make the run `host_consumed`:

  * A pass/pass admission additionally requires a HOST-ISSUED execution witness
    (HMAC-bound to a per-process host secret) plus the full 14-gate internal
    ClaimGate obligation set. A producer cannot mint host authority. See the Lev
    test "produces a structurally consistent run that the host blocks until the
    full internal gate set is present" — even Lev's own partial producer run is
    `host_blocked`. That is the expected, honest state.
  * For a receipt admitted only at tier0 with deeper tiers unmet (hook exit 3,
    INSUFFICIENT_DEPTH), the projected verdict is `conditional`, not pass. The
    host would review it as `host_reviewed_failed` (structurally consumed,
    verdict != pass) — again, honest and correct, not an error.

FUTURE RECORDING INVOCATION (run by the host, once the surface ships)
---------------------------------------------------------------------
    lev orchestration claimgate-steering consume \
        <out-root>/<run-id> --json --no-write

`--no-write` recomputes and reports without mutating the source projection; drop
it to have the host write its own `lev-consumption-*.json` authority receipts
alongside the source files. This producer NEVER writes into `.lev`, never into a
Lev trust root, and never into the CR repo trust root — only under the caller's
chosen `--out` path.

WRITER-EXEC HAZARD — AVOIDED
----------------------------
This producer does not run any Lev writer, does not run `consume`, and does not
mint witnesses. It only emits source JSON and (optionally) runs the CR hook with
an isolated floor store so the CR repo is untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Mirrors Lev's ClaimGate adapter constants only in SHAPE; the value is CR-labelled
# so provenance is honest. The host does not validate this string's value — it is
# carried through as opaque evidence.
PRODUCER_VERSION = "0.1.0-cr-lev-steering-producer"
VERIFIER_VERSION = f"cr-lev-steering-producer/{PRODUCER_VERSION}"

# ClaimGate steering runs stay under the claimgate.* scope (Lev's `scope` internal
# gate requires it on a pass/pass admission).
DEFAULT_TARGET_REF = "claimgate.cr-ratchet-receipt-gate"

VALID_PROOF_STATUSES = {"passed", "failed", "timeout", "skipped"}

HOOK_REL_PATH = "hooks/post_receipt_gate.sh"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def derive_verdict(statuses: list[str]) -> str:
    """Mirror of Lev host `deriveVerdict` / producer `recomputeVerdict`.

    any failed|timeout -> 'fail'; all passed -> 'pass'; else -> 'conditional'
    (an empty or skipped-bearing set degrades to conditional, never pass).
    """
    if not statuses:
        return "conditional"
    if any(s in ("failed", "timeout") for s in statuses):
        return "fail"
    if all(s == "passed" for s in statuses):
        return "pass"
    return "conditional"


def _tier_status_to_obligation_status(tier_status: str) -> str:
    """Map a CR claim_verify tier status onto a Lev ProofResult status."""
    mapping = {
        "PASS": "passed",
        "FAIL": "failed",
        "REJECTED": "failed",
        "ERROR": "failed",
        "SKIP": "skipped",
    }
    return mapping.get(str(tier_status).upper(), "skipped")


def _parse_concatenated_json(text: str) -> list[dict[str, Any]]:
    """Parse the hook's stdout, which concatenates several top-level JSON objects
    (claimgate lint, claim_verify, ratchet_floor)."""
    decoder = json.JSONDecoder()
    out: list[dict[str, Any]] = []
    idx = 0
    n = len(text)
    while idx < n:
        # Skip whitespace / non-JSON separators until the next object start.
        while idx < n and text[idx] not in "{[":
            idx += 1
        if idx >= n:
            break
        try:
            obj, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            idx += 1
            continue
        if isinstance(obj, dict):
            out.append(obj)
        idx = end
    return out


def run_hook(receipt_path: Path, plugin_dir: Path) -> dict[str, Any]:
    """Run post_receipt_gate.sh on a receipt with an ISOLATED floor store so the
    CR repo is never mutated. Returns a structured summary of the hook run.

    The floor stage (`ratchet_floor.py admit`) only writes when it ADMITS a known
    key; RF_STORE is redirected to a throwaway temp file regardless, so even an
    admitting run leaves the repo untouched.
    """
    hook = plugin_dir / HOOK_REL_PATH
    if not hook.is_file():
        raise FileNotFoundError(f"hook not found: {hook}")

    env = dict(os.environ)
    # RF_STORE must point at a NON-EXISTENT path, not an empty file: ratchet_floor
    # reads the store as JSON and an empty file is a decode error (floor IO fail,
    # exit 1) that would corrupt the honest hook verdict. A missing path is treated
    # as a fresh store. The temp dir keeps any floor write off the CR repo.
    tmp_dir = tempfile.mkdtemp(prefix="cr_steering_isolated_floor_")
    env["RF_STORE"] = os.path.join(tmp_dir, "floor_store.json")
    try:
        proc = subprocess.run(
            ["sh", str(hook), str(receipt_path)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
    finally:
        try:
            import shutil

            shutil.rmtree(tmp_dir, ignore_errors=True)
        except OSError:
            pass

    blocks = _parse_concatenated_json(proc.stdout)
    by_tool: dict[str, dict[str, Any]] = {}
    for b in blocks:
        tool = b.get("tool")
        if isinstance(tool, str):
            by_tool[tool] = b

    return {
        "exit": proc.returncode,
        "stderr": proc.stderr,
        "lint": by_tool.get("claimgate.lint-receipt"),
        "claim_verify": by_tool.get("claim_verify"),
        "floor": by_tool.get("ratchet_floor"),
    }


def _obligations_from_hook(hook_result: dict[str, Any], receipt_ref: str) -> list[dict[str, Any]]:
    """Build the obligation list from the hook's structured tier ladder.

    Each obligation carries the receipt hash and file ref as evidence. The
    shellCheck is CR-namespaced (`cr:post_receipt_gate:<name>`) so it does NOT
    masquerade as one of Lev's 14 internal ClaimGate gates — these are CR-side
    tier checks, honestly labelled.
    """
    obligations: list[dict[str, Any]] = []

    cv = hook_result.get("claim_verify")
    if isinstance(cv, dict) and isinstance(cv.get("tier_results"), list):
        for tr in cv["tier_results"]:
            name = str(tr.get("tier", "tier"))
            status = _tier_status_to_obligation_status(tr.get("status", "SKIP"))
            ev = [receipt_ref]
            er = tr.get("evidence_ref")
            if isinstance(er, str) and er:
                ev.append(f"claimref:{er}")
            obligations.append(
                {
                    "name": name,
                    "constraint_id": f"claimgate.{name}",
                    "status": status,
                    "evidence_refs": ev,
                }
            )
    else:
        # Hook produced no structured tier ladder (e.g. tier0 rejected before
        # claim_verify emitted). Fall back to a single obligation from the exit.
        exit_code = int(hook_result.get("exit", 1))
        status = "passed" if exit_code == 0 else ("skipped" if exit_code == 3 else "failed")
        obligations.append(
            {
                "name": "post_receipt_gate",
                "constraint_id": "claimgate.post_receipt_gate",
                "status": status,
                "evidence_refs": [receipt_ref],
            }
        )

    # Floor stage as an honest non-decisive obligation (PARKED/ADMITTED -> skipped;
    # a floor regression that fails the hook is already reflected in the exit path).
    floor = hook_result.get("floor")
    if isinstance(floor, dict):
        fv = str(floor.get("verdict", "")).upper()
        floor_status = "failed" if fv in ("REJECTED", "REGRESSION") else "skipped"
        obligations.append(
            {
                "name": "floor",
                "constraint_id": "claimgate.floor",
                "status": floor_status,
                "evidence_refs": [receipt_ref],
            }
        )

    return obligations


def produce_steering_run(
    receipt_path: str | Path,
    out_root: str | Path,
    hook_result: dict[str, Any] | None = None,
    generated_at: str | None = None,
    target_ref: str = DEFAULT_TARGET_REF,
    input_receipt_id: str | None = None,
    plugin_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Emit a schema-valid ClaimGate -> Lev source projection for a hook run.

    If `hook_result` is not supplied, the CR hook is run (with an isolated floor
    store). Returns a summary dict; writes five JSON files under
    `<out_root>/<run_id>/`.
    """
    receipt_path = Path(receipt_path).resolve()
    out_root = Path(out_root)
    plugin_dir = Path(plugin_dir) if plugin_dir else Path(__file__).resolve().parent

    if not receipt_path.is_file():
        raise FileNotFoundError(f"receipt not found: {receipt_path}")

    receipt_bytes = receipt_path.read_bytes()
    receipt_sha = sha256_hex(receipt_bytes)
    receipt_ref = f"sha256:{receipt_sha}"

    if hook_result is None:
        hook_result = run_hook(receipt_path, plugin_dir)

    hook_exit = int(hook_result.get("exit", 1))
    lint = hook_result.get("lint") or {}
    cv = hook_result.get("claim_verify") or {}
    floor = hook_result.get("floor") or {}

    generated_at = generated_at or _iso_now()

    # Receipt identity for the eval input receipt id. The receipt HASH is the
    # load-bearing binding evidence; this id just names the input.
    if input_receipt_id is None:
        input_receipt_id = f"cr-{receipt_path.stem}-{receipt_sha[:16]}"

    run_id = f"cg-{input_receipt_id}"
    spec_id = f"ps-claimgate-{run_id}"        # contains run_id (object_binding)
    job_id = f"ej-claimgate-{run_id}"          # contains run_id (object_binding)
    suite_id = target_ref                      # == constraintPackId (object_binding)

    obligations = _obligations_from_hook(hook_result, receipt_ref)
    statuses = [o["status"] for o in obligations]
    verdict = derive_verdict(statuses)

    # eval-job-output.json evidence: one entry per obligation, order-aligned so the
    # host's spec-vs-output status comparison matches pairwise.
    evidence = [
        {
            "status": o["status"],
            "elapsedMs": 0,
            "verifierVersion": VERIFIER_VERSION,
            "evidenceRefs": o["evidence_refs"],
        }
        for o in obligations
    ]

    proof_obligations = [
        {
            "obligationId": f"obl-claimgate-{o['name']}",
            "constraintId": o["constraint_id"],
            # CR-namespaced: honestly NOT a Lev internal ClaimGate gate.
            "shellCheck": f"cr:post_receipt_gate:{o['name']}",
            "expectedResult": "exit_zero",
            "actualResult": {
                "status": o["status"],
                "elapsedMs": 0,
                "verifierVersion": VERIFIER_VERSION,
                "evidenceRefs": o["evidence_refs"],
            },
        }
        for o in obligations
    ]

    eval_output = {
        "verdict": verdict,
        "evidence": evidence,
        "receiptId": input_receipt_id,
    }

    run_json = {
        "version": PRODUCER_VERSION,
        "run_id": run_id,
        "suite_id": suite_id,
        "target_ref": target_ref,
        "layout": ".lev/steering/runs/<run-id>",
        "compatibility_only": True,
        "live_lev_consumed": False,
        "claim_ceiling": "adapter_partial",
        "release_admission_allowed": False,
        "generated_at": generated_at,
        # CR hook evidence (non-authority, non-true-flag metadata — carried through).
        "cr_source": "claimgate_plugin/hooks/post_receipt_gate.sh",
        "cr_receipt_path": str(receipt_path),
        "cr_receipt_sha256": receipt_ref,
        "cr_hook_exit": hook_exit,
        "cr_hook_tier0_lint_verdict": lint.get("verdict"),
        "cr_hook_claim_verify_verdict": cv.get("verdict"),
        "cr_hook_floor_verdict": floor.get("verdict"),
        "not_yet_recordable": (
            "consume surface not in installed CLI; host witness + full internal "
            "gate set required for host_consumed"
        ),
    }

    proof_spec = {
        "specId": spec_id,
        "targetRef": target_ref,
        "constraintPackId": target_ref,
        "proofObligations": proof_obligations,
        "proofStrategy": "compiled_guard",
        "generatedAt": generated_at,
    }

    eval_job = {
        "jobId": job_id,
        "jobClass": "eval",
        "targetRef": target_ref,
        "proofSpecId": spec_id,
        "constraintPackId": target_ref,
        "inputReceiptIds": [input_receipt_id],
        "startedAt": generated_at,
        "completedAt": generated_at,
        "output": eval_output,
    }

    boundary = {
        "version": PRODUCER_VERSION,
        "status": "adapter_projection_only",
        "live_lev_consumed": False,
        "claim_ceiling": "adapter_partial",
        "release_admission_allowed": False,
        "authority": (
            "host Lev EvalFlow / ProofSpec / execution ledger must consume this "
            "before it is Lev-admitted"
        ),
        "required_host_receipt_fields": [
            "execution_ledger_receipt_id",
            "run_seal_ref",
            "host_lev_runtime",
            "proof_spec_consumed",
            "eval_job_output_consumed",
        ],
        "target_files": [
            "core/orchestration/src/proof/eval-job-types.ts",
            "core/orchestration/src/proof/flows/eval-flow.ts",
            "core/orchestration/src/proof/proof-spec-generator.ts",
            "core/flowmind/src/gate-evaluator.ts",
            "core/flowmind/src/kernel/constraint-manifold.ts",
        ],
        "generated_at": generated_at,
    }

    run_dir = out_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    def _write(name: str, data: Any) -> str:
        p = run_dir / name
        p.write_text(json.dumps(data, indent=2) + "\n")
        return str(p)

    files = [
        _write("run.json", run_json),
        _write("proof-spec.json", proof_spec),
        _write("eval-job.json", eval_job),
        _write("eval-job-output.json", eval_output),
        _write("boundary.json", boundary),
    ]

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "verdict": verdict,
        "hook_exit": hook_exit,
        "files": files,
        "recordable": False,
        "future_invocation": (
            f"lev orchestration claimgate-steering consume {run_dir} --json --no-write"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Produce a ClaimGate -> Lev source steering projection from a CR hook run."
    )
    ap.add_argument("receipt", help="path to the CR receipt JSON")
    ap.add_argument(
        "--out",
        required=True,
        help="output root; the projection is written to <out>/<run-id>/ "
        "(NOT into .lev, NOT the repo trust root)",
    )
    ap.add_argument("--target-ref", default=DEFAULT_TARGET_REF)
    ap.add_argument("--generated-at", default=None, help="ISO timestamp (for deterministic output)")
    ap.add_argument("--json", action="store_true", help="emit the result summary as JSON")
    args = ap.parse_args(argv)

    result = produce_steering_run(
        receipt_path=args.receipt,
        out_root=args.out,
        generated_at=args.generated_at,
        target_ref=args.target_ref,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"run_id        : {result['run_id']}")
        print(f"run_dir       : {result['run_dir']}")
        print(f"verdict       : {result['verdict']}  (hook exit {result['hook_exit']})")
        print(f"recordable    : {result['recordable']}")
        print(f"future consume: {result['future_invocation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
