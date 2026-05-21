#!/usr/bin/env python3
"""Run W6 Gemini/Grok provider audits for the formal manifold retool receipts."""

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
PLAN_PATH = REPO / "system_v5" / "ops" / "NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md"
CORRECTION_PATH = REPO / "system_v5" / "docs" / "CONSTRAINT_MANIFOLD_ORDERING_STATUS_CORRECTION_20260520.md"
D86_FINAL_SYNTHESIS_PATH = RESULT_DIR / "two_root_constraint_final_synthesis_receipt.json"

GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = os.environ.get("WIZARD_GROK_MODEL", "grok-4.3").strip() or "grok-4.3"
GEMINI_MODEL = os.environ.get("WIZARD_GEMINI_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash"

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

GROUNDING_TARGETS = [
    "system_v5/ops/NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md",
    "system_v5/docs/CONSTRAINT_MANIFOLD_ORDERING_STATUS_CORRECTION_20260520.md",
    "system_v5/ops/formal_scouts/results/two_root_constraint_classical_admin_load_bearing_partition_repair_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_constraint_grok_97_114_boundary_ingest_probe_results.json",
    "system_v5/ops/formal_scouts/results/constraint_manifold_terrain_lindblad_composition_bridge_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_constraint_layer_order_noncanonical_inventory_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_constraint_formal_stack_dynamics_closure_audit_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_constraint_concrete_manifold_definition_and_selection_mechanism_probe_results.json",
    "system_v5/ops/formal_scouts/results/numpy_quarantine_source_native_nonclassical_gate_probe_results.json",
    "system_v5/ops/formal_scouts/results/constraint_admissible_tool_role_gate_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_constraint_chain_fresh_rerun_and_estate_tool_gate_repair_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_constraint_estate_tool_gate_blocker_partition_probe_results.json",
    "system_v5/ops/formal_scouts/results/two_root_constraint_final_synthesis_receipt.json",
]


@dataclass(frozen=True)
class Lane:
    lane_id: str
    route_card: str
    council_role: str
    task: str


LANES = [
    Lane(
        "claim_boundary_audit",
        "formal_manifold_retool.claim_boundary",
        "decision.evidence_boundary+failure.loophole_auditor_council",
        "Audit whether W3/W4/W5 preserve the plan boundaries: grok_sim is sidequest evidence, the 13-layer stack is candidate_legacy_stack, Cl/Clifford closure is not an F01/N01 consequence, and no terrain/bridge/manifold claim is promoted before provider audit.",
    ),
    Lane(
        "terrain_lindblad_mechanism_audit",
        "formal_manifold_retool.terrain_lindblad_mechanism",
        "failure.falsifier_council+voice.feynman",
        "Audit whether W3/W5 correctly treat the recorded 8-terrain Lindblad/Hamiltonian laws plus nested CPTP/channel schedule composition as the candidate selection mechanism X, without substituting TFIM, graph-edge dynamics, or 2-qubit-only evidence.",
    ),
    Lane(
        "atlas_bridge_audit",
        "formal_manifold_retool.atlas_bridge",
        "failure.falsifier_council+voice.popper",
        "Audit whether the receipts restore the 17/20 master-atlas objects and keep Xi, rho_AB, and Phi0(rho_AB) open instead of collapsing them into a Cl-basin verdict.",
    ),
    Lane(
        "final_claim_table_premortem",
        "formal_manifold_retool.final_claim_table_premortem",
        "failure.premortem_council+follow_up.next_move_selector",
        "Premortem the final synthesis table. Identify any remaining smuggling, overclaim, missing statistical-rigor or scale distinction, and distinguish tooling-closeout goal_complete from any still-open scientific/manifold proof receipt.",
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


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def compact_result(path: pathlib.Path) -> dict[str, Any]:
    data = load_json(path)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "schema": data.get("schema"),
        "name": data.get("name"),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "claim_ceiling": data.get("claim_ceiling"),
        "all_pass": data.get("all_pass") or data.get("summary", {}).get("all_pass"),
        "summary": data.get("summary", {}),
        "open_choices": data.get("open_choices", [])[:8],
        "blockers": data.get("blockers", [])[:8],
    }


def plan_excerpt() -> str:
    if not PLAN_PATH.exists():
        return (
            f"{rel(PLAN_PATH)} is a historical W6 plan surface removed after D86 cleanup "
            f"authorization. Use {rel(D86_FINAL_SYNTHESIS_PATH)} for current closeout status."
        )
    text = PLAN_PATH.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    interesting = []
    for idx, line in enumerate(lines, start=1):
        low = line.lower()
        if any(
            key in low
            for key in [
                "workstream 6",
                "provider prompt must ask",
                "durability:",
                "final closeout checklist",
                "do not do",
                "embedded-geometry stack",
                "concrete manifold-definition",
            ]
        ):
            start = max(1, idx - 4)
            end = min(len(lines), idx + 38)
            interesting.append(f"--- {rel(PLAN_PATH)}:{start}-{end} ---\n" + "\n".join(lines[start - 1 : end]))
    return "\n\n".join(interesting[:8])


def local_context() -> dict[str, Any]:
    result_paths = [REPO / target for target in GROUNDING_TARGETS if target.endswith(".json")]
    return {
        "plan": {"path": rel(PLAN_PATH), "sha256": sha256_file(PLAN_PATH), "excerpt": plan_excerpt()},
        "d86_final_synthesis": compact_result(D86_FINAL_SYNTHESIS_PATH),
        "correction_doc": {"path": rel(CORRECTION_PATH), "sha256": sha256_file(CORRECTION_PATH)},
        "results": [compact_result(path) for path in result_paths],
        "non_result_grounding_targets": [target for target in GROUNDING_TARGETS if not target.endswith(".json")],
        "claim_table_draft": [
            {
                "claim": "D86/B2 closed the actionable tool-role partition as tooling closeout: selected actionable rows are zero, while the current gate still preserves 10 blocked_result_not_all_pass nonclearance rows and reservoir counterevidence/admin-support rows as nonpromotional evidence.",
                "status": "bounded_tooling_closeout_complete",
                "ceiling": "tooling unlock evidence only",
            },
            {
                "claim": "grok_sim 97-114 is sidequest/imported Cl-basin evidence, not owner-source canon.",
                "status": "formal_ingest_only",
                "ceiling": "sidequest boundary evidence only",
            },
            {
                "claim": "W3 restores recorded terrain Lindblad/CPTP schedule composition and bounded Xi/rho_AB/Phi0 bridge candidates.",
                "status": "bounded_reframe",
                "ceiling": "not Axis0, engine, Holodeck, or Cl theorem",
            },
            {
                "claim": "The 13-layer fixture is demoted to candidate_legacy_stack; exact 13-layer forcing is killed_or_unproven.",
                "status": "demoted",
                "ceiling": "noncanonical inventory receipt only",
            },
            {
                "claim": "Existing W4 dynamics receipts do not allow algebra-level promotion or Clifford closure claims.",
                "status": "blocked",
                "ceiling": "formal closure audit only",
            },
            {
                "claim": "W5 selects topology_first_relation_scaffold as a working carrier pending provider audit.",
                "status": "working_candidate_selected_pending_provider_audit",
                "ceiling": "not final/survived until W6",
            },
        ],
    }


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def build_prompt(provider: str, lane: Lane) -> tuple[str, dict[str, Any]]:
    mmm_block, mmm_meta = build_mmm_prompt_block(
        route_card=f"{provider}.{lane.route_card}",
        council_role=lane.council_role,
        mini_ids=MINI_IDS,
    )
    context = local_context()
    prompt = f"""{mmm_block}

Focused external W6 provider audit: formal manifold tooling retool.

Authority boundary:
- Your output is provider audit/proposal only.
- Local formal-scout receipts and validators remain authority.
- Do not promote final manifold, final basin, Axis0, engine, physics, target-system, Holodeck, or Clifford theorem claims.
- The same grounded context is sent independently to Gemini and Grok.
- Keep the geometric constraint manifold as root object.
- This runner is historical/replayable W6 audit infrastructure; if the old long plan is absent, D86 final synthesis is the current tooling-closeout authority.

Lane id: {lane.lane_id}
Lane task: {lane.task}

Required audit questions:
1. Does the new receipt set preserve the grok_sim boundary as sidequest/imported-hypothesis evidence?
2. Is any selector, energy, bridge, closure, terrain, or manifold term smuggling Cl?
3. Is the bridge/cut-state/kernel reframe stated without Cl-basin overclaim?
4. Does the receipt set include the recorded bootpack/screenshot terrain Lindblad/composition system as candidate selection mechanism X without claiming it is already proven?
5. Does the receipt set test or demand fixed-state/fixed-observable/generated-channel algebra rather than generic ground-state evidence?
6. Does it restore the 17/20-layer master-atlas objects, especially Clifford torus T_(pi/4), Xi, rho_AB, and Phi0(rho_AB)?
7. Are 8/16/32/64 scale claims scoped correctly?
8. Are Clifford dimension, Pauli substrate qubit count, selected graph/operator count, and tensor-network site count kept separate?
9. Did any 2-qubit-only evidence leak into a decisive verdict?
10. Does any ground-state/Hamiltonian result get overused as an algebra-level conclusion?
11. Is there independent reconstruction of at least one master-atlas finding?
12. Does the algebra/closure audit distinguish Pauli basis, Clifford torus, Clifford algebra/module, and signature convention?
13. What exact next receipt would kill or strengthen the claim?

Return concise sections:
- mmm_saliency_delta
- saliency_failure_mode
- lane_verdict
- direct_answers_to_required_questions
- killed_or_blocked_claims
- overclaims_to_block
- missing_evidence
- exact_next_receipt
- stop_condition

BEGIN LOCAL_CONTEXT_JSON
{json.dumps(context, indent=2, sort_keys=True)}
END LOCAL_CONTEXT_JSON
"""
    return prompt, mmm_meta


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
    out = OUT_DIR / f"{stamp}_{provider}_{lane.lane_id}_formal_manifold_retool_w6_audit.json"
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
                {"model": GROK_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "max_tokens": 1800},
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
    parser.add_argument("--max-workers", type=int, default=8)
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
