#!/usr/bin/env python3
"""Run a bounded MMM-loaded Gemini fanout over manifold follow-up lanes."""

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
from typing import Any

from provider_mmm_prompt import build_mmm_prompt_block
from run_manifold_grok_parallel_council import (
    COMMON_MINI_IDS,
    FACTS,
    GROUNDING_TARGETS,
    LANES,
    Lane,
)


ROOT = pathlib.Path(__file__).resolve().parent
OUT_DIR = ROOT / "provider_receipts"
DEFAULT_MODEL = os.environ.get("WIZARD_GEMINI_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_lane_prompt(lane: Lane) -> tuple[str, dict[str, Any]]:
    mmm_block, metadata = build_mmm_prompt_block(
        route_card=lane.route_card.replace("grok.", "gemini."),
        council_role=lane.council_role,
        mini_ids=COMMON_MINI_IDS,
    )
    prompt = f"""{mmm_block}

Mass-parallel Gemini manifold council lane.

Authority boundary:
- This is external provider audit/proposal, not local formal evidence.
- Local formal-scout receipts, validators, and Codex controller synthesis remain authority.
- Do not promote any claim. Return next executable scouts, falsifiers, blockers, and overclaim boundaries.
- Preserve the geometric constraint manifold as the root object.

{FACTS}

Lane id: {lane.lane_id}
Lane task:
{lane.task}

Return concise JSON-like sections:
- mmm_saliency_delta
- saliency_failure_mode
- lane_verdict
- evidence_used
- killed_or_blocked_claims
- smallest_next_executable_scout
- tool_or_manifold_gap
- overclaims_to_block
- stop_condition
"""
    return prompt, metadata


def provider_receipt(
    *,
    lane: Lane,
    status: str,
    model: str,
    proposal_text: str = "",
    blocked_reason: str = "",
    wizard_mmm: dict[str, Any],
    prompt_sha256: str,
    raw_response: Any = None,
) -> dict[str, Any]:
    live_api_proof = {}
    if proposal_text:
        live_api_proof = {
            "endpoint": f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "model": model,
            "answer_sha256": _sha256(proposal_text),
        }
    return {
        "schema": "PROVIDER_PROPOSAL_RECEIPT_v1",
        "provider": "gemini",
        "route": lane.route_card.replace("grok.", "gemini."),
        "lane_id": lane.lane_id,
        "status": status,
        "classification": "provider_audit",
        "promotion_allowed": False,
        "evidence_allowed": False,
        "claim_ceiling": "Provider audit/proposal only. Local formal-scout receipts and validators remain authority.",
        "repo_grounding": {
            "targets": GROUNDING_TARGETS,
            "local_facts_embedded_in_prompt": True,
            "wizard_mmm_loaded_in_prompt": bool(wizard_mmm.get("mmm_loaded")),
        },
        "wizard_mmm": wizard_mmm,
        "prompt_sha256": prompt_sha256,
        "model": model,
        "proposal_text": proposal_text,
        "blocked_reason": blocked_reason,
        "live_api_proof": live_api_proof,
        "raw_response": raw_response,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_text(raw: dict[str, Any]) -> str:
    parts = raw["candidates"][0]["content"]["parts"]
    return "\n".join(str(part.get("text", "")) for part in parts).strip()


def run_lane(lane: Lane, *, timeout: float, stamp: str, model: str) -> pathlib.Path:
    prompt, wizard_mmm = build_lane_prompt(lane)
    prompt_sha256 = _sha256(prompt)
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        receipt = provider_receipt(
            lane=lane,
            status="blocked",
            model=model,
            blocked_reason="GEMINI_API_KEY/GOOGLE_API_KEY not set",
            wizard_mmm=wizard_mmm,
            prompt_sha256=prompt_sha256,
        )
    else:
        try:
            raw = post_json(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                {"Content-Type": "application/json", "x-goog-api-key": key},
                {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0},
                },
                timeout,
            )
            text = _extract_text(raw)
            usage = raw.get("usageMetadata") or {}
            receipt = provider_receipt(
                lane=lane,
                status="completed",
                model=model,
                proposal_text=text,
                wizard_mmm=wizard_mmm,
                prompt_sha256=prompt_sha256,
                raw_response={
                    "model": model,
                    "usageMetadata": usage,
                    "finishReason": (raw.get("candidates") or [{}])[0].get("finishReason"),
                },
            )
        except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            receipt = provider_receipt(
                lane=lane,
                status="blocked",
                model=model,
                blocked_reason=repr(exc),
                wizard_mmm=wizard_mmm,
                prompt_sha256=prompt_sha256,
            )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{stamp}_gemini_{lane.lane_id}_parallel_manifold_audit.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--lanes", nargs="*", default=[lane.lane_id for lane in LANES])
    args = parser.parse_args()

    lane_map = {lane.lane_id: lane for lane in LANES}
    selected = [lane_map[lane_id] for lane_id in args.lanes if lane_id in lane_map]
    unknown = [lane_id for lane_id in args.lanes if lane_id not in lane_map]
    if unknown:
        raise SystemExit(f"unknown lane ids: {', '.join(unknown)}")
    if not selected:
        raise SystemExit("no lanes selected")

    outputs: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = [executor.submit(run_lane, lane, timeout=args.timeout, stamp=args.stamp, model=args.model) for lane in selected]
        for future in concurrent.futures.as_completed(futures):
            outputs.append(str(future.result()))
            print(outputs[-1])
    print(json.dumps({"stamp": args.stamp, "count": len(outputs), "model": args.model, "outputs": sorted(outputs)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
