#!/usr/bin/env python3
"""Run bounded Grok/Gemini audits for tool-foundation repair."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import time
import urllib.error
import urllib.request
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
OUT_DIR = ROOT / "provider_receipts"

PROMPT = """Read-only audit for Codex Ratchet tool-foundation repair.

Current owner correction:
- Actual nonclassical QIT engine/manifold attractor-basin sims cannot use numpy in the load-bearing path.
- Formal sims have three lanes: classical sims may use numpy load-bearing for classical numerical claims; bridge/baseline/supportive sims may use numpy with explicit role boundaries; source-native nonclassical QIT engine/manifold/FEP/Holodeck sims cannot use numpy as the load-bearing attractor-basin path.
- Tools must meet the standards of the constraints, or no real attractor basin can form.
- Redo means patch and rerun, not delete old receipts.

Current local facts:
- Runner preflight is green; active stage is lego.
- tool_function_receipt_matrix reports 108 passing rows, 0 missing receipts, but receipt_schema_observed_missing_count=108.
- stale_tool_depth_scan found 12 stale depth rows, 0 active-admission stale rows.
- v5 primitive lego shelf has PyTorch/SymPy/Z3/Clifford/GUDHI/TopoNetX/XGI/PyG legos plus one explicit NumPy-only baseline.
- numpy_quarantine_source_native_nonclassical_gate found 32 hard source-native/nonclassical numpy-tainted scouts and 85 review-required numpy surfaces.
- constraint_admissible_tool_role_gate found 47 nonclassical/source-native result surfaces; after normalization, 45 blocked and 2 tool-role candidates. Blockers: 42 numpy load-bearing, 3 no constraint-admissible load-bearing tool. Candidates: eight_qubit_mps_channel_order_graph_leakage_pyg_pytorch_opt_einsum_z3 and eight_qubit_mps_entropy_readout_layer_constraint.

Audit task:
1. Premortem the repair plan: validate all tool integration sims from foundations upward, then patch/rerun dependent source-native engine/manifold/FEP/Holodeck sims.
2. Identify the smallest receipt-bearing first repair that creates real progress.
3. Name overclaims to block.
4. Propose a parallel lane map across tools: PyTorch/autograd, z3/cvc5, sympy, Clifford, geomstats, e3nn, rustworkx, XGI, TopoNetX, GUDHI, PyG, quimb/cotengra/kahypar.

Provider output is proposal/audit only. Local formal scouts and validators remain authority."""


def provider_receipt(
    *,
    provider: str,
    status: str,
    proposal_text: str = "",
    blocked_reason: str = "",
    model: str = "",
    raw_response: Any = None,
) -> dict[str, Any]:
    return {
        "schema": "PROVIDER_PROPOSAL_RECEIPT_v1",
        "provider": provider,
        "route": "tool_foundation_repair_audit",
        "status": status,
        "classification": "provider_audit",
        "promotion_allowed": False,
        "evidence_allowed": False,
        "claim_ceiling": "Provider audit/proposal only. Local formal-scout receipts and validators remain authority.",
        "repo_grounding": {
            "targets": [
                "system_v5/evidence/tool_function_receipt_matrix.json",
                "system_v5/docs/TOOL_FUNCTION_RECEIPT_MATRIX.md",
                "system_v5/ops/tooling/stale_tool_depth_scan.json",
                "system_v5/ops/formal_scouts/results/numpy_quarantine_source_native_nonclassical_gate_probe_results.json",
                "system_v5/ops/formal_scouts/results/constraint_admissible_tool_role_gate_probe_results.json",
                "system_v5/docs/LEGO_SIM_CONTRACT.md",
            ],
            "local_facts_embedded_in_prompt": True,
        },
        "model": model,
        "proposal_text": proposal_text,
        "blocked_reason": blocked_reason,
        "raw_response": raw_response,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def run_grok(timeout: float) -> dict[str, Any]:
    key = os.environ.get("XAI_API_KEY")
    model = "grok-4.3"
    if not key:
        return provider_receipt(provider="grok", status="blocked", blocked_reason="XAI_API_KEY not set", model=model)
    try:
        raw = post_json(
            "https://api.x.ai/v1/chat/completions",
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            {"model": model, "messages": [{"role": "user", "content": PROMPT}], "temperature": 0},
            timeout,
        )
        return provider_receipt(provider="grok", status="completed", proposal_text=raw["choices"][0]["message"]["content"], model=model, raw_response=raw)
    except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return provider_receipt(provider="grok", status="blocked", blocked_reason=repr(exc), model=model)


def run_gemini(timeout: float) -> dict[str, Any]:
    key = os.environ.get("GEMINI_API_KEY")
    model = "gemini-2.5-flash"
    if not key:
        return provider_receipt(provider="gemini", status="blocked", blocked_reason="GEMINI_API_KEY not set", model=model)
    try:
        raw = post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {"Content-Type": "application/json", "x-goog-api-key": key},
            {
                "contents": [{"parts": [{"text": PROMPT}]}],
                "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}},
            },
            timeout,
        )
        text = "\n".join(str(part.get("text", "")) for part in raw["candidates"][0]["content"]["parts"]).strip()
        return provider_receipt(provider="gemini", status="completed", proposal_text=text, model=model, raw_response=raw)
    except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return provider_receipt(provider="gemini", status="blocked", blocked_reason=repr(exc), model=model)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["grok", "gemini"], required=True)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    args = parser.parse_args()

    receipt = run_grok(args.timeout) if args.provider == "grok" else run_gemini(args.timeout)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.stamp}_{args.provider}_tool_foundation_repair_audit.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"path": str(out), "provider": args.provider, "status": receipt["status"]}))
    return 0 if receipt["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
