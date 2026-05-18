#!/usr/bin/env python3
"""Run Grok/Gemini API audits for the current FEP repair packet."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
OUT_DIR = ROOT / "provider_receipts"
TARGETS = [
    "scripts/lint_sim_contract.py",
    "system_v5/ops/formal_scouts/sim_source_native_fep_pomdp_policy_tree_probe.py",
    "system_v5/ops/formal_scouts/sim_source_native_fep_online_vmp_policy_update_probe.py",
    "system_v5/ops/formal_scouts/sim_macro_sim_axis0_plural_stage_candidate_router_probe.py",
    "system_v5/ops/formal_scouts/sim_axis0_plural_candidate_multicarrier_drive_controls_probe.py",
    "system_v5/ops/formal_scouts/sim_axis0_fep_gradient_stage_local_adapter_closure_probe.py",
]


def run(args: list[str], limit: int = 20_000) -> str:
    try:
        text = subprocess.check_output(args, cwd=REPO, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        text = exc.output
    return text[:limit]


def build_prompt() -> str:
    diff = run(["git", "diff", "--", *TARGETS], limit=35_000)
    status = run(["git", "status", "--short", "--", *TARGETS], limit=8_000)
    # Avoid assuming a repo-local interpreter path; provider only needs source state.
    receipt_summary = run(
        [
            "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "-c",
            (
                "import json,pathlib; r=pathlib.Path('system_v5/ops/formal_scouts/results'); "
                "names=['source_native_fep_pomdp_policy_tree_probe','source_native_fep_online_vmp_policy_update_probe',"
                "'macro_sim_axis0_plural_stage_candidate_router_probe','axis0_plural_candidate_multicarrier_drive_controls_probe',"
                "'axis0_fep_gradient_stage_local_adapter_closure_probe','constraint_admissible_tool_role_gate_probe',"
                "'numpy_quarantine_source_native_nonclassical_gate_probe']; "
                "out={}; "
                "\nfor n in names:\n p=r/(n+'_results.json')\n out[n]={'exists':p.exists()}\n if p.exists():\n  d=json.loads(p.read_text()); out[n].update({'all_pass':d.get('all_pass'),'classification':d.get('classification'),'depth':d.get('TOOL_INTEGRATION_DEPTH') or d.get('tool_integration_depth')})\nprint(json.dumps(out,indent=2,sort_keys=True))"
            ),
        ],
        limit=12_000,
    )
    return f"""Read-only external audit for Codex Ratchet current FEP/Axis0 repair.

Owner intent:
- Existing QIT engine/manifold/FEP formal scouts must form real attractor-basin evidence, not green ornamental receipts.
- Source-native nonclassical FEP/Axis0/Holodeck sims cannot use NumPy/SciPy as load-bearing math.
- Torch/proof/tensor-network tools may be load-bearing when they match the constraint.
- Provider output is advisory only; local formal-scout receipts and validators remain authority.

Current repair packet:
- Router, Axis0 drive-control, and FEP-gradient closure were converted away from NumPy load-bearing and now show tool-role candidates.
- POMDP policy-tree scout was converted from NumPy/SciPy to Torch; fresh validation passed locally.
- Online-VMP scout is being converted to Torch and still needs external premortem before local validation is trusted.
- lint_sim_contract was repaired to recognize formal_scout/CLASSIFICATION and current v5 formal tool-admission receipts.

Audit task:
1. Premortem the current patch/diff for shallow-basin failure, invalid tool-role demotion, API compatibility, or false FEP claims.
2. Identify exact blockers before online-VMP and Axis0 closure can count as candidate-basin evidence.
3. Say whether the current direction should continue, be narrowed, or be reverted in any part.
4. Give exact local validation commands that should gate the next step.
5. Do not recommend broad rebuilds or abstract theory; stay on the files below.

Git status:
{status}

Receipt summary:
{receipt_summary}

Current diff:
{diff}
"""


def provider_receipt(
    *,
    provider: str,
    status: str,
    text: str = "",
    blocked_reason: str = "",
    model: str = "",
    raw_response: Any = None,
) -> dict[str, Any]:
    return {
        "schema": "PROVIDER_PROPOSAL_RECEIPT_v1",
        "provider": provider,
        "route": "current_fep_repair_audit",
        "status": status,
        "classification": "provider_audit",
        "promotion_allowed": False,
        "evidence_allowed": False,
        "claim_ceiling": "Provider audit only. Local formal-scout receipts and validators remain authority.",
        "repo_grounding": {
            "targets": TARGETS,
            "local_facts_embedded_in_prompt": True,
            "diff_embedded_in_prompt": True,
            "receipt_summary_embedded_in_prompt": True,
        },
        "model": model,
        "proposal_text": text,
        "blocked_reason": blocked_reason,
        "raw_response": raw_response,
        "targets": TARGETS,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def run_grok(prompt: str, timeout: float) -> dict[str, Any]:
    key = os.environ.get("XAI_API_KEY", "").strip()
    model = os.environ.get("WIZARD_GROK_MODEL", "grok-4.3")
    if not key:
        return provider_receipt(provider="grok_xai", status="blocked", blocked_reason="XAI_API_KEY not set", model=model)
    try:
        raw = post_json(
            "https://api.x.ai/v1/chat/completions",
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
            timeout,
        )
        return provider_receipt(provider="grok_xai", status="completed", text=raw["choices"][0]["message"]["content"], model=model, raw_response=raw)
    except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return provider_receipt(provider="grok_xai", status="blocked", blocked_reason=repr(exc), model=model)


def run_gemini(prompt: str, timeout: float) -> dict[str, Any]:
    key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()
    model = os.environ.get("WIZARD_GEMINI_MODEL", "gemini-2.5-flash")
    if not key:
        return provider_receipt(provider="gemini_direct", status="blocked", blocked_reason="GEMINI_API_KEY/GOOGLE_API_KEY not set", model=model)
    try:
        raw = post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {"Content-Type": "application/json", "x-goog-api-key": key},
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}},
            },
            timeout,
        )
        text = "\n".join(str(part.get("text", "")) for part in raw["candidates"][0]["content"]["parts"]).strip()
        return provider_receipt(provider="gemini_direct", status="completed", text=text, model=model, raw_response=raw)
    except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return provider_receipt(provider="gemini_direct", status="blocked", blocked_reason=repr(exc), model=model)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["grok", "gemini"], required=True)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    args = parser.parse_args()
    prompt = build_prompt()
    receipt = run_grok(prompt, args.timeout) if args.provider == "grok" else run_gemini(prompt, args.timeout)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.stamp}_{args.provider}_current_fep_repair_audit.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"path": str(out), "provider": args.provider, "status": receipt["status"]}))
    return 0 if receipt["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
