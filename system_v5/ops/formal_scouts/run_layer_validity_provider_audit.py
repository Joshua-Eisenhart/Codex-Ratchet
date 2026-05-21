#!/usr/bin/env python3
"""Run focused Grok/Gemini provider audits for manifold layer validity."""

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
    "failure.premortem_council",
    "failure.falsifier_council",
    "failure.loophole_auditor_council",
    "follow_up.next_move_selector",
    "follow_up.compile_gate_council",
    "voice.hume",
    "voice.feynman",
    "voice.popper",
    "voice.pushback",
    "voice.strategy",
    "voice.systems",
    "expert.domain_specialist",
    "expert.standard_checker",
]

LAYERS = [
    "finite_constraint_complex",
    "complex_hilbert_carrier",
    "unit_spinor_sphere",
    "projective_base_sphere",
    "hopf_fiber_bundle",
    "hopf_torus_leaf_family",
    "connection_holonomy_geometry",
    "weyl_spinor_bundle",
    "chirality_orientation_cover",
    "clifford_module_geometry",
    "frame_bundle_structure_reduction",
    "tensor_product_coupling_geometry",
    "dynamic_transition_ratchet_geometry",
]

FACTS = f"""Indexed/local audit facts for this focused provider prompt; do not treat this prompt text as future fresh validation or a fresh rerun:
- The current question is layer validity, not Axis0 repair.
- The two root constraints under audit are F01_finitude and N01_noncommutation.
- The current 13 named layer list is: {", ".join(LAYERS)}.
- root_geometric_constraint_manifold_maturity_pytorch_toolchain_probe all_pass=true and executes an integrated 13-layer PyTorch path with graph/proof/topology/geometric tools, layer-removal deltas for all 13, reverse-order gap, semantic-swap gap, auto_LiRPA/le-wm pressure, and Axis0 excluded from pass conditions.
- constraint_manifold_layer_causal_responsibility_matrix_probe has effective_rank=13 and every row is non-substitutable under removal/validator/delay/advance/reverse/adversarial controls.
- g_structure_semantic_layer_operator_coupling_probe all_pass=true and supports semantic operator-role coupling, but it does not prove the named 13 layers emerge from F01/N01.
- two_root_constraint_attractor_basin_foundation_gate_probe all_pass=true as a blocking audit: executable_root_receipt_count=0, root_basin_admission_status=blocked, current_real_attractor_basin_convergence_claim_status=killed_or_unproven.
- geometric_manifold_layer_validity_root_constraint_audit_probe is an indexed 2026-05-21 controller-audit receipt row reporting operational_candidate_layer_count=13, root_ablation_supported_layer_count=13, layer_validity_status=root_ablation_supported_not_final_basin, next_required_scout=two_root_retuned_layer_stack_integration_probe; this provider prompt does not rerun it.
- Current honest boundary: operational candidate evidence is nontrivial, but root-emergent layer validity is not proven.
"""

GROUNDING_TARGETS = [
    "system_v5/ops/formal_scouts/results/root_geometric_constraint_manifold_maturity_pytorch_toolchain_probe_results.json",
    "system_v5/ops/formal_scouts/results/constraint_manifold_layer_causal_responsibility_matrix_probe_results.json",
    "system_v5/ops/formal_scouts/results/g_structure_semantic_layer_operator_coupling_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_constraint_attractor_basin_foundation_gate_probe_results.json",
    "system_v5/ops/formal_scouts/results/geometric_manifold_layer_validity_root_constraint_audit_probe_results.json",
]


@dataclass(frozen=True)
class Lane:
    lane_id: str
    route_card: str
    council_role: str
    task: str


LANES = [
    Lane(
        "layer_validity",
        "layer_validity.strict_boundary",
        "decision.domain_specialist+failure.falsifier_council",
        "Classify which of the 13 layers are valid under current evidence. Separate operational candidate, semantic/operator support, and root-emergent F01/N01 validity. Do not promote candidates into valid layers.",
    ),
    Lane(
        "root_emergence_falsifier",
        "layer_validity.root_emergence_falsifier",
        "failure.falsifier_council+voice.popper",
        "Design the smallest next executable formal scout that can test whether F01/N01 actually force, select, or ablate these layers. Include F01-only, N01-only, both, and neither controls.",
    ),
    Lane(
        "premortem_bullshit_risk",
        "layer_validity.premortem",
        "failure.premortem_council+failure.loophole_auditor_council",
        "Premortem the manifold layer program assuming it later proves to be made-up structure. Name the receipt misuse, early warning signs, and overclaims to block now.",
    ),
    Lane(
        "followup_selector",
        "layer_validity.followup_selector",
        "follow_up.next_move_selector+follow_up.compile_gate_council",
        "Select the next three automatic follow-up prompts. They must be executable formal scouts or provider audits, not orchestration-only work.",
    ),
]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def build_prompt(provider: str, lane: Lane) -> tuple[str, dict[str, Any]]:
    mmm_block, metadata = build_mmm_prompt_block(
        route_card=f"{provider}.{lane.route_card}",
        council_role=lane.council_role,
        mini_ids=MINI_IDS,
    )
    prompt = f"""{mmm_block}

Focused external provider audit: geometric constraint manifold layer validity.

Authority boundary:
- This is provider audit/proposal only. It is not formal evidence.
- Local formal-scout receipts and validators remain authority.
- Do not call the manifold mature, proven, admitted, or a real attractor basin.
- The task is to catch salience errors and define the next executable proof/sim, not to mirror the user's wording.

{FACTS}

Lane id: {lane.lane_id}
Lane task:
{lane.task}

Return concise JSON-like sections:
- mmm_saliency_delta
- lane_verdict
- per_layer_validity_boundary
- killed_or_blocked_claims
- smallest_next_executable_scout
- overclaims_to_block
- stop_condition
"""
    return prompt, metadata


def receipt(
    *,
    provider: str,
    lane: Lane,
    model: str,
    status: str,
    prompt_hash: str,
    wizard_mmm: dict[str, Any],
    proposal_text: str = "",
    blocked_reason: str = "",
    raw_response: Any = None,
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
            "wizard_mmm_loaded_in_prompt": bool(wizard_mmm.get("mmm_loaded")),
        },
        "wizard_mmm": wizard_mmm,
        "prompt_sha256": prompt_hash,
        "model": model,
        "proposal_text": proposal_text,
        "blocked_reason": blocked_reason,
        "live_api_proof": {
            "endpoint": endpoint,
            "model": model,
            "answer_sha256": sha256(proposal_text),
        } if proposal_text else {},
        "raw_response": raw_response,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def run_grok(lane: Lane, *, timeout: float, stamp: str) -> pathlib.Path:
    prompt, wizard_mmm = build_prompt("grok", lane)
    prompt_hash = sha256(prompt)
    key = os.environ.get("XAI_API_KEY")
    if not key:
        data = receipt(provider="grok", lane=lane, model=GROK_MODEL, status="blocked", prompt_hash=prompt_hash, wizard_mmm=wizard_mmm, blocked_reason="XAI_API_KEY not set")
    else:
        try:
            raw = post_json(
                GROK_ENDPOINT,
                {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                {"model": GROK_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
                timeout,
            )
            text = raw["choices"][0]["message"]["content"].strip()
            data = receipt(provider="grok", lane=lane, model=GROK_MODEL, status="completed", prompt_hash=prompt_hash, wizard_mmm=wizard_mmm, proposal_text=text, raw_response={"id": raw.get("id"), "model": raw.get("model"), "usage": raw.get("usage")})
        except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            data = receipt(provider="grok", lane=lane, model=GROK_MODEL, status="blocked", prompt_hash=prompt_hash, wizard_mmm=wizard_mmm, blocked_reason=repr(exc))
    return write_receipt(stamp, "grok", lane, data)


def run_gemini(lane: Lane, *, timeout: float, stamp: str) -> pathlib.Path:
    prompt, wizard_mmm = build_prompt("gemini", lane)
    prompt_hash = sha256(prompt)
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        data = receipt(provider="gemini", lane=lane, model=GEMINI_MODEL, status="blocked", prompt_hash=prompt_hash, wizard_mmm=wizard_mmm, blocked_reason="GEMINI_API_KEY/GOOGLE_API_KEY not set")
    else:
        try:
            raw = post_json(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
                {"Content-Type": "application/json", "x-goog-api-key": key},
                {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0}},
                timeout,
            )
            text = "\n".join(str(part.get("text", "")) for part in raw["candidates"][0]["content"]["parts"]).strip()
            data = receipt(provider="gemini", lane=lane, model=GEMINI_MODEL, status="completed", prompt_hash=prompt_hash, wizard_mmm=wizard_mmm, proposal_text=text, raw_response={"model": GEMINI_MODEL, "usageMetadata": raw.get("usageMetadata"), "finishReason": raw.get("candidates", [{}])[0].get("finishReason")})
        except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            data = receipt(provider="gemini", lane=lane, model=GEMINI_MODEL, status="blocked", prompt_hash=prompt_hash, wizard_mmm=wizard_mmm, blocked_reason=repr(exc))
    return write_receipt(stamp, "gemini", lane, data)


def write_receipt(stamp: str, provider: str, lane: Lane, data: dict[str, Any]) -> pathlib.Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{stamp}_{provider}_{lane.lane_id}_layer_validity_audit.json"
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    parser.add_argument("--providers", nargs="*", default=["grok", "gemini"], choices=["grok", "gemini"])
    parser.add_argument("--lanes", nargs="*", default=[lane.lane_id for lane in LANES])
    args = parser.parse_args()

    lane_map = {lane.lane_id: lane for lane in LANES}
    selected = [lane_map[lane_id] for lane_id in args.lanes if lane_id in lane_map]
    if len(selected) != len(args.lanes):
        raise SystemExit("unknown lane id")

    jobs = []
    for lane in selected:
        if "grok" in args.providers:
            jobs.append((run_grok, lane))
        if "gemini" in args.providers:
            jobs.append((run_gemini, lane))

    outputs: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = [executor.submit(fn, lane, timeout=args.timeout, stamp=args.stamp) for fn, lane in jobs]
        for future in concurrent.futures.as_completed(futures):
            outputs.append(str(future.result()))
            print(outputs[-1])
    print(json.dumps({"stamp": args.stamp, "count": len(outputs), "outputs": sorted(outputs)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
