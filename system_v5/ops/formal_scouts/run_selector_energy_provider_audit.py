#!/usr/bin/env python3
"""Run Gemini/Grok cross-audit for the selector-energy metric-pass candidate."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.request
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
OUT_DIR = ROOT / "provider_receipts"
RESULT_PATH = ROOT / "results" / "two_root_constraint_group_action_weighted_selector_or_energy_probe_results.json"
PLAN_PATH = REPO / "system_v5" / "ops" / "NEXT_GOAL_SELECTOR_ENERGY_PHASE_PLAN.md"

GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = os.environ.get("WIZARD_GROK_MODEL", "grok-4.3").strip() or "grok-4.3"
GEMINI_MODEL = os.environ.get("WIZARD_GEMINI_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_json_object(text: str) -> dict[str, Any] | None:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1) if fenced else text
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def endpoint_for(provider: str, model: str) -> str:
    if provider == "grok":
        return GROK_ENDPOINT
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def selector_context() -> tuple[str, dict[str, Any]]:
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    plan_text = PLAN_PATH.read_text(encoding="utf-8")
    plan_slice = "\n".join(plan_text.splitlines()[10:230])
    prompt = f"""You are an independent external audit lane for Codex Ratchet.

Task: audit whether the candidate `commutator_balance_energy` from the selector-energy formal scout can be called a non-tautological survivor.

Authority boundary:
- Local formal-scout receipts are the source of evidence.
- Your output is provider audit/proposal only.
- Do not promote final manifold, final basin, Clifford basin, Axis0, engine, physics, target-system, or Holodeck claims.
- Do not assume the selector should survive. Find the strongest objection first.
- The same context is being sent independently to Gemini and Grok.

Required checks:
1. Does `commutator_balance_energy` directly or indirectly hardcode Cl-isomorphism, Cl signature, known Cl adjacency, or variance-zero?
2. Does it beat matched no-selector baselines on both active scales 8 and 16 under the stated bootstrap CI gate?
3. Does it rely on the historical 2-qubit Pauli substrate for a verdict?
4. Does the random-null commutator-balance calibration avoid Cl's known commute fraction?
5. Do any of these graveyard rules hit?
   - uses Cl-isomorphism/signature/adjacency as accept/reject;
   - only prefers lower degree variance;
   - makes the target absorbing by fiat;
   - succeeds only by preventing all exits;
   - cannot distinguish a hand-faked static fingerprint from true order-sensitive structure;
   - needs NumPy/classical glue as load-bearing nonclassical support;
   - fails to improve dwell/return/stationary mass over matched baselines.

Return one JSON object only with this exact shape:
{{
  "provider_verdict": "survived" | "borderline" | "graveyard" | "blocked",
  "non_tautological": true | false,
  "beats_matched_baseline": true | false,
  "graveyard_rule_hits": [
    {{"rule": "short rule name", "hit": true | false, "reason": "evidence-grounded reason"}}
  ],
  "strongest_objection": "text",
  "best_positive_reading": "text",
  "missing_evidence": ["text"],
  "required_next_move": "text"
}}

BEGIN PLAN EXCERPT
{plan_slice}
END PLAN EXCERPT

BEGIN RAW FORMAL SCOUT RESULT JSON
{json.dumps(result, indent=2, sort_keys=True)}
END RAW FORMAL SCOUT RESULT JSON
"""
    metadata = {
        "result_path": rel(RESULT_PATH),
        "result_sha256": sha256_file(RESULT_PATH),
        "plan_path": rel(PLAN_PATH),
        "plan_sha256": sha256_file(PLAN_PATH),
        "candidate": "commutator_balance_energy",
        "prompt_sha256": sha256(prompt),
    }
    return prompt, metadata


def make_receipt(provider: str, model: str, status: str, metadata: dict[str, Any], text: str = "", blocked: str = "", raw: Any = None) -> dict[str, Any]:
    text_sha = sha256(text) if text else ""
    return {
        "schema": "PROVIDER_PROPOSAL_RECEIPT_v1",
        "receipt_kind": "selector_energy_commutator_balance_cross_audit",
        "receipt_contract": "PROVIDER_SELECTOR_ENERGY_CROSS_AUDIT_v1",
        "provider": provider,
        "status": status,
        "classification": "provider_audit",
        "promotion_allowed": False,
        "evidence_allowed": False,
        "claim_ceiling": "Provider audit only; formal_scout ingest remains authority and cannot promote final basin claims.",
        "model": model,
        "candidate": metadata["candidate"],
        "route": f"{provider}.selector_energy.commutator_balance_cross_audit",
        "prompt_sha256": metadata["prompt_sha256"],
        "repo_grounding": {
            "targets": [
                metadata["result_path"],
                metadata["plan_path"],
            ],
            "result_path": metadata["result_path"],
            "result_sha256": metadata["result_sha256"],
            "plan_path": metadata["plan_path"],
            "plan_sha256": metadata["plan_sha256"],
            "same_context_for_both_providers": True,
        },
        "proposal_text": text,
        "parsed": extract_json_object(text) if text else None,
        "blocked_reason": blocked,
        "raw_response": raw,
        "raw_response_metadata": raw,
        "live_api_proof": {
            "endpoint": endpoint_for(provider, model),
            "model": model,
            "answer_sha256": text_sha,
            "provider": provider,
            "status": status,
            "prompt_sha256": metadata["prompt_sha256"],
            "response_text_sha256": text_sha,
        } if text else {},
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def run_grok(timeout: float, stamp: str) -> pathlib.Path:
    prompt, metadata = selector_context()
    key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if not key:
        receipt = make_receipt("grok", GROK_MODEL, "blocked", metadata, blocked="XAI_API_KEY/GROK_API_KEY not set")
    else:
        try:
            raw = post_json(
                GROK_ENDPOINT,
                {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                {
                    "model": GROK_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                    "max_tokens": 1600,
                },
                timeout,
            )
            text = raw["choices"][0]["message"]["content"].strip()
            receipt = make_receipt("grok", GROK_MODEL, "completed", metadata, text=text, raw={"id": raw.get("id"), "model": raw.get("model"), "usage": raw.get("usage")})
        except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            receipt = make_receipt("grok", GROK_MODEL, "blocked", metadata, blocked=repr(exc))
    return write_receipt(stamp, "grok", receipt)


def run_gemini(timeout: float, stamp: str) -> pathlib.Path:
    prompt, metadata = selector_context()
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        receipt = make_receipt("gemini", GEMINI_MODEL, "blocked", metadata, blocked="GEMINI_API_KEY/GOOGLE_API_KEY not set")
    else:
        try:
            raw = post_json(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
                {"Content-Type": "application/json", "x-goog-api-key": key},
                {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}},
                },
                timeout,
            )
            text = "\n".join(str(part.get("text", "")) for part in raw["candidates"][0]["content"]["parts"]).strip()
            receipt = make_receipt("gemini", GEMINI_MODEL, "completed", metadata, text=text, raw={"model": GEMINI_MODEL, "usageMetadata": raw.get("usageMetadata"), "finishReason": raw.get("candidates", [{}])[0].get("finishReason")})
        except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            receipt = make_receipt("gemini", GEMINI_MODEL, "blocked", metadata, blocked=repr(exc))
    return write_receipt(stamp, "gemini", receipt)


def write_receipt(stamp: str, provider: str, receipt: dict[str, Any]) -> pathlib.Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{stamp}_{provider}_selector_energy_commutator_balance_cross_audit.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    parser.add_argument("--timeout", type=float, default=240)
    parser.add_argument("--providers", nargs="*", default=["grok", "gemini"], choices=["grok", "gemini"])
    args = parser.parse_args()
    jobs = []
    if "grok" in args.providers:
        jobs.append(("grok", run_grok))
    if "gemini" in args.providers:
        jobs.append(("gemini", run_gemini))
    outputs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs) or 1) as executor:
        futures = [executor.submit(fn, args.timeout, args.stamp) for _provider, fn in jobs]
        for future in concurrent.futures.as_completed(futures):
            outputs.append(str(future.result()))
    print(json.dumps({"stamp": args.stamp, "count": len(outputs), "outputs": sorted(outputs)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
