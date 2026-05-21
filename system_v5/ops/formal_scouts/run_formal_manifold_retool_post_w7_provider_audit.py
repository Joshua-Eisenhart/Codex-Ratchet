#!/usr/bin/env python3
"""Run post-W7 Gemini/Grok audits for the final claim table."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import pathlib
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from provider_mmm_prompt import build_mmm_prompt_block


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
OUT_DIR = ROOT / "provider_receipts"
RESULT_DIR = ROOT / "results"

GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = os.environ.get("WIZARD_GROK_MODEL", "grok-4.3").strip() or "grok-4.3"
GEMINI_MODEL = os.environ.get("WIZARD_GEMINI_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash"

GROUNDING_TARGETS = [
    "system_v5/ops/NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md",
    "system_v5/docs/CONSTRAINT_MANIFOLD_ORDERING_STATUS_CORRECTION_20260520.md",
    ".lev/pm/handoffs/20260520-formal-manifold-tooling-retool-session-1.md",
    "system_v5/ops/formal_scouts/results/two_root_constraint_terrain_engine_pseudo_basin_tensor_substrate_scope_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_constraint_final_synthesis_receipt.json",
    "system_v5/ops/formal_scouts/results/two_root_constraint_final_synthesis_receipt_results.json",
    "system_v5/ops/formal_scouts/results/constraint_admissible_tool_role_gate_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_constraint_estate_tool_gate_blocker_partition_probe_results.json",
    "system_v5/evidence/formal_scout_readiness_index.json",
]

MINI_IDS = [
    "decision.evidence_boundary",
    "failure.falsifier_council",
    "failure.loophole_auditor_council",
    "follow_up.next_move_selector",
    "voice.hume",
    "voice.feynman",
    "voice.popper",
    "voice.pushback",
    "voice.strategy",
    "voice.systems",
]


@dataclass(frozen=True)
class Lane:
    lane_id: str
    route_card: str
    council_role: str
    task: str


LANES = [
    Lane(
        "post_w7_final_claim_table_audit",
        "formal_manifold_retool.post_w7_final_claim_table",
        "decision.evidence_boundary+failure.loophole_auditor_council",
        "Audit the post-W7 final claim table for overclaim, scale collapse, W3/W7 promotion leakage, and missing blockers.",
    ),
    Lane(
        "post_w7_completion_blocker_audit",
        "formal_manifold_retool.post_w7_completion_blockers",
        "failure.falsifier_council+follow_up.next_move_selector",
        "Audit whether the current final synthesis correctly treats goal_complete=true as tooling closeout only, without promoting scientific manifold/basin claims.",
    ),
]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def result_summary(path: pathlib.Path) -> dict[str, Any]:
    data = read_json(path)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "name": data.get("name"),
        "all_pass": data.get("all_pass"),
        "goal_complete": data.get("goal_complete"),
        "cleanup_authorized": data.get("cleanup_authorized"),
        "promotion_allowed": data.get("promotion_allowed"),
        "claim_ceiling": data.get("claim_ceiling"),
        "open_blockers": data.get("open_blockers", [])[:8],
        "final_claim_table_rows": len(data.get("final_claim_table", [])),
        "tooling_exit_status": data.get("tooling_exit_status", {}),
        "provider_audit_status": data.get("provider_audit_status", {}),
    }


def text_hits(path: pathlib.Path, needles: list[str], limit: int = 12) -> list[dict[str, Any]]:
    rows = []
    lowered = [needle.lower() for needle in needles]
    for line_no, line in enumerate(read_text(path).splitlines(), start=1):
        low = line.lower()
        if any(needle in low for needle in lowered):
            rows.append({"path": rel(path), "line": line_no, "text": line[:260]})
            if len(rows) >= limit:
                break
    return rows


def local_context() -> dict[str, Any]:
    final_result = RESULT_DIR / "two_root_constraint_final_synthesis_receipt.json"
    w7_result = RESULT_DIR / "two_root_constraint_terrain_engine_pseudo_basin_tensor_substrate_scope_probe_results.json"
    return {
        "grounding_targets": [
            {"path": target, "sha256": sha256_file(REPO / target)}
            for target in GROUNDING_TARGETS
        ],
        "w7_result": result_summary(w7_result),
        "final_synthesis": result_summary(final_result),
        "historical_plan_hits": text_hits(
            REPO / "system_v5/ops/NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md",
            ["Terrain micro-pseudo-basin", "Engine pseudo-basin", "Engine-stage site count", "goal_complete", "provider cross-audit"],
        ),
        "correction_hits": text_hits(
            REPO / "system_v5/docs/CONSTRAINT_MANIFOLD_ORDERING_STATUS_CORRECTION_20260520.md",
            ["Pseudo-basin", "Natural tensor-substrate", "terrain-stage or engine-stage", "Cl(p,q)"],
        ),
        "handoff_hits": text_hits(
            REPO / ".lev/pm/handoffs/20260520-formal-manifold-tooling-retool-session-1.md",
            ["D86", "goal_complete=true", "cleanup_authorized=true", "open_blocker_count=0", "post-W7 provider audit"],
        ),
        "required_provider_question": "Does the post-W7/D86 final claim table preserve W7 as scope-only evidence while justifying tooling closeout without scientific promotion?",
    }


def build_prompt(provider: str, lane: Lane) -> tuple[str, dict[str, Any]]:
    mmm_block, mmm_meta = build_mmm_prompt_block(
        route_card=f"{provider}.{lane.route_card}",
        council_role=lane.council_role,
        mini_ids=MINI_IDS,
    )
    context = local_context()
    prompt = f"""{mmm_block}

Post-W7/D86 provider audit replay for the formal manifold retool.

Authority boundary:
- Your output is provider audit/proposal only.
- Local formal-scout receipts and validators remain authority.
- Do not promote final manifold, real attractor basin, Axis0, engine theorem, physics validation, Holodeck, PEPS/PEPS3D/full tensor-network, multi-qubit Lindblad, canonical layer order, or Clifford theorem claims.
- The same grounded context is sent independently to Gemini and Grok.

Provider: {provider}
Lane id: {lane.lane_id}
Lane task: {lane.task}

Required answers:
1. Does W7 remain scope-only evidence for terrain/engine pseudo-basin tensor-substrate design?
2. Does the final claim table keep E, L, R, q, and selected operator count N separate?
3. Did W3 finite-channel schedule evidence leak into PEPS/PEPS3D/full tensor-network or multi-qubit Lindblad claims?
4. Did grok_sim 115-124 leak into promotable multi-qubit or tensor-network evidence?
5. Are `goal_complete=true`, `cleanup_authorized=true`, and `open_blocker_count=0` justified as tooling closeout only?
6. Is B1, the post-W7 provider-audit requirement, addressed by these receipts only as provider proposal evidence?
7. Which next scientific or proof receipt remains open after tooling closeout, without treating cleanup as manifold promotion?

Return concise sections:
- lane_verdict
- direct_answers
- overclaims_to_block
- remaining_blockers
- exact_next_receipt
- stop_condition

BEGIN_LOCAL_CONTEXT_JSON
{json.dumps(context, indent=2, sort_keys=True)}
END_LOCAL_CONTEXT_JSON
"""
    return prompt, mmm_meta


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def make_receipt(
    provider: str,
    lane: Lane,
    model: str,
    status: str,
    prompt_hash: str,
    wizard_mmm: dict[str, Any],
    *,
    text: str = "",
    blocked: str = "",
    raw: Any = None,
) -> dict[str, Any]:
    endpoint = GROK_ENDPOINT if provider == "grok" else f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    return {
        "schema": "PROVIDER_PROPOSAL_RECEIPT_v1",
        "provider": provider,
        "route": f"{provider}.{lane.route_card}",
        "lane_id": lane.lane_id,
        "status": status,
        "classification": "provider_audit",
        "promotion_allowed": False,
        "evidence_allowed": False,
        "claim_ceiling": "Provider audit/proposal only. Local formal-scout receipts and validators remain authority.",
        "repo_grounding": {
            "targets": GROUNDING_TARGETS,
            "local_facts_embedded_in_prompt": True,
            "same_context_for_both_providers": True,
            "wizard_mmm_loaded_in_prompt": bool(wizard_mmm.get("mmm_loaded")),
        },
        "wizard_mmm": wizard_mmm,
        "prompt_sha256": prompt_hash,
        "model": model,
        "proposal_text": text,
        "blocked_reason": blocked,
        "live_api_proof": {"endpoint": endpoint, "model": model, "answer_sha256": sha256(text)} if text else {},
        "raw_response": raw,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def write_receipt(stamp: str, provider: str, lane: Lane, data: dict[str, Any]) -> pathlib.Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{stamp}_{provider}_{lane.lane_id}_formal_manifold_retool_post_w7_audit.json"
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def run_grok(lane: Lane, timeout: float, stamp: str) -> pathlib.Path:
    prompt, meta = build_prompt("grok", lane)
    prompt_hash = sha256(prompt)
    key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if not key:
        data = make_receipt("grok", lane, GROK_MODEL, "blocked", prompt_hash, meta, blocked="XAI_API_KEY/GROK_API_KEY not set")
    else:
        try:
            raw = post_json(
                GROK_ENDPOINT,
                {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                {"model": GROK_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "max_tokens": 1600},
                timeout,
            )
            text = raw["choices"][0]["message"]["content"].strip()
            data = make_receipt("grok", lane, GROK_MODEL, "completed", prompt_hash, meta, text=text, raw={"id": raw.get("id"), "model": raw.get("model"), "usage": raw.get("usage")})
        except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            data = make_receipt("grok", lane, GROK_MODEL, "blocked", prompt_hash, meta, blocked=repr(exc))
    return write_receipt(stamp, "grok", lane, data)


def run_gemini(lane: Lane, timeout: float, stamp: str) -> pathlib.Path:
    prompt, meta = build_prompt("gemini", lane)
    prompt_hash = sha256(prompt)
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        data = make_receipt("gemini", lane, GEMINI_MODEL, "blocked", prompt_hash, meta, blocked="GEMINI_API_KEY/GOOGLE_API_KEY not set")
    else:
        try:
            raw = post_json(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
                {"Content-Type": "application/json", "x-goog-api-key": key},
                {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}}},
                timeout,
            )
            text = "\n".join(str(part.get("text", "")) for part in raw["candidates"][0]["content"]["parts"]).strip()
            data = make_receipt("gemini", lane, GEMINI_MODEL, "completed", prompt_hash, meta, text=text, raw={"model": GEMINI_MODEL, "usageMetadata": raw.get("usageMetadata"), "finishReason": raw.get("candidates", [{}])[0].get("finishReason")})
        except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            data = make_receipt("gemini", lane, GEMINI_MODEL, "blocked", prompt_hash, meta, blocked=repr(exc))
    return write_receipt(stamp, "gemini", lane, data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    parser.add_argument("--timeout", type=float, default=360)
    parser.add_argument("--providers", nargs="*", default=["grok", "gemini"], choices=["grok", "gemini"])
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()
    jobs = []
    for lane in LANES:
        if "grok" in args.providers:
            jobs.append((run_grok, lane))
        if "gemini" in args.providers:
            jobs.append((run_gemini, lane))
    outputs: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.max_workers, len(jobs)))) as executor:
        futures = [executor.submit(fn, lane, args.timeout, args.stamp) for fn, lane in jobs]
        for future in concurrent.futures.as_completed(futures):
            out = str(future.result())
            outputs.append(out)
            print(out)
    print(json.dumps({"stamp": args.stamp, "count": len(outputs), "outputs": sorted(outputs)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
