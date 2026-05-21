#!/usr/bin/env python3
"""Run Grok/Gemini audits for two-root layer option exploration."""

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
OUT_DIR = ROOT / "provider_receipts"
GROK_MODEL = "grok-4.3"
GEMINI_MODEL = os.environ.get("WIZARD_GEMINI_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash"
GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"

MINI_IDS = [
    "decision.context_strategy",
    "decision.evidence_boundary",
    "failure.premortem_council",
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

FACTS = """Indexed local receipt facts; do not treat this provider prompt as fresh validation or a fresh rerun:
- two_root_constraint_layer_alignment_matrix_probe was indexed by the local receipt set as all_pass/validator passing at receipt time; this prompt does not rerun it.
- Alignment matrix: 13 layers, 52 exploratory branches, 8 layers marked retune_required, 6 direct root candidates, first layer currently not full-root-valid if only finite cells.
- two_root_layer_option_full_tool_explorer_probe was indexed by the local receipt set as all_pass/validator passing at receipt time; this prompt does not rerun it.
- Full-tool explorer: option_count=52, all_tool_passing_option_count=52, minimum_options_per_layer=4, first_layer_tool_passing_options=4.
- Full local tools consumed: PyTorch, SymPy, z3, cvc5, Clifford, geomstats, rustworkx, XGI, TopoNetX, GUDHI, PyG, e3nn.
- two_root_layer_option_emergence_ablation_probe was indexed by the local receipt set as all_pass/validator passing at receipt time; this prompt does not rerun it.
- Ablation: option_count=52, survivor_count=52, minimum_survivors_per_layer=4, first_layer_survivors=4.
- Controls: both roots active survives; F01-only, N01-only, neither-root, commuting/order-erased controls are blocked by z3/cvc5 gates.
- Boundary: these receipts select strict retune branches; they do not prove unique emergence, final layer order, final manifold, or real attractor basin.
"""

GROUNDING_TARGETS = [
    "system_v5/ops/formal_scouts/results/two_root_constraint_layer_alignment_matrix_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_layer_option_full_tool_explorer_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_layer_option_emergence_ablation_probe_results.json",
]


@dataclass(frozen=True)
class Lane:
    lane_id: str
    route_card: str
    council_role: str
    task: str


LANES = [
    Lane("optimistic_glory", "two_root_options.optimistic_glory", "decision.context_strategy+voice.strategy", "Assume the manifold is close. Identify the strongest evidence that the layer set can be retuned rather than discarded, and name the best branch families."),
    Lane("pessimistic_falsifier", "two_root_options.pessimistic_falsifier", "failure.falsifier_council+voice.popper", "Try to kill the all-52-survivor interpretation. Find the sharpest remaining loopholes and the exact next negative controls."),
    Lane("proof_tool_audit", "two_root_options.proof_tool_audit", "decision.evidence_boundary+failure.loophole_auditor_council", "Audit what the proof/graph/geometry tools actually proved versus what they did not prove. Separate local gates from emergence proof."),
    Lane("next_stack_selector", "two_root_options.next_stack_selector", "follow_up.next_move_selector+follow_up.compile_gate_council", "Select the next executable scout after all 52 options survived both-root ablation. Keep it narrow and formal-scout admissible."),
]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def build_prompt(provider: str, lane: Lane) -> tuple[str, dict[str, Any]]:
    mmm, meta = build_mmm_prompt_block(route_card=f"{provider}.{lane.route_card}", council_role=lane.council_role, mini_ids=MINI_IDS)
    prompt = f"""{mmm}

Focused Wizard v4.2 external audit lane: two-root manifold layer option exploration.

Authority boundary:
- Provider output is audit/proposal only.
- Local formal-scout receipts and validators remain authority.
- Mix optimistic exploration with pessimistic constraint.
- Do not promote final manifold, final order, or attractor basin.

{FACTS}

Lane: {lane.lane_id}
Task: {lane.task}

Return concise sections:
- mmm_saliency_delta
- lane_verdict
- strongest_positive_reading
- sharpest_negative_or_loophole
- exact_next_executable_scout
- overclaims_to_block
- stop_condition
"""
    return prompt, meta


def make_receipt(provider: str, lane: Lane, model: str, status: str, prompt_hash: str, wizard_mmm: dict[str, Any], text: str = "", blocked: str = "", raw: Any = None) -> dict[str, Any]:
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
        "repo_grounding": {"targets": GROUNDING_TARGETS, "local_facts_embedded_in_prompt": True, "wizard_mmm_loaded_in_prompt": bool(wizard_mmm.get("mmm_loaded"))},
        "wizard_mmm": wizard_mmm,
        "prompt_sha256": prompt_hash,
        "model": model,
        "proposal_text": text,
        "blocked_reason": blocked,
        "live_api_proof": {"endpoint": endpoint, "model": model, "answer_sha256": sha256(text)} if text else {},
        "raw_response": raw,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def run_grok(lane: Lane, timeout: float, stamp: str) -> pathlib.Path:
    prompt, meta = build_prompt("grok", lane)
    prompt_hash = sha256(prompt)
    key = os.environ.get("XAI_API_KEY")
    if not key:
        data = make_receipt("grok", lane, GROK_MODEL, "blocked", prompt_hash, meta, blocked="XAI_API_KEY not set")
    else:
        try:
            raw = post_json(GROK_ENDPOINT, {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, {"model": GROK_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0}, timeout)
            text = raw["choices"][0]["message"]["content"].strip()
            data = make_receipt("grok", lane, GROK_MODEL, "completed", prompt_hash, meta, text=text, raw={"id": raw.get("id"), "model": raw.get("model"), "usage": raw.get("usage")})
        except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            data = make_receipt("grok", lane, GROK_MODEL, "blocked", prompt_hash, meta, blocked=repr(exc))
    return write(stamp, "grok", lane, data)


def run_gemini(lane: Lane, timeout: float, stamp: str) -> pathlib.Path:
    prompt, meta = build_prompt("gemini", lane)
    prompt_hash = sha256(prompt)
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        data = make_receipt("gemini", lane, GEMINI_MODEL, "blocked", prompt_hash, meta, blocked="GEMINI_API_KEY/GOOGLE_API_KEY not set")
    else:
        try:
            raw = post_json(f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent", {"Content-Type": "application/json", "x-goog-api-key": key}, {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0}}, timeout)
            text = "\n".join(str(part.get("text", "")) for part in raw["candidates"][0]["content"]["parts"]).strip()
            data = make_receipt("gemini", lane, GEMINI_MODEL, "completed", prompt_hash, meta, text=text, raw={"model": GEMINI_MODEL, "usageMetadata": raw.get("usageMetadata"), "finishReason": raw.get("candidates", [{}])[0].get("finishReason")})
        except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            data = make_receipt("gemini", lane, GEMINI_MODEL, "blocked", prompt_hash, meta, blocked=repr(exc))
    return write(stamp, "gemini", lane, data)


def write(stamp: str, provider: str, lane: Lane, data: dict[str, Any]) -> pathlib.Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{stamp}_{provider}_{lane.lane_id}_two_root_option_audit.json"
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    parser.add_argument("--timeout", type=float, default=240)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--providers", nargs="*", default=["grok", "gemini"], choices=["grok", "gemini"])
    args = parser.parse_args()
    jobs = []
    for lane in LANES:
        if "grok" in args.providers:
            jobs.append((run_grok, lane))
        if "gemini" in args.providers:
            jobs.append((run_gemini, lane))
    outputs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futures = [ex.submit(fn, lane, args.timeout, args.stamp) for fn, lane in jobs]
        for future in concurrent.futures.as_completed(futures):
            outputs.append(str(future.result()))
            print(outputs[-1])
    print(json.dumps({"stamp": args.stamp, "count": len(outputs), "outputs": sorted(outputs)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
