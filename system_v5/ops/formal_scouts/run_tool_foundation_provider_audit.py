#!/usr/bin/env python3
"""Run bounded Grok/Gemini audits for tool-foundation repair."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import time
import urllib.error
import urllib.request
from typing import Any

from provider_mmm_prompt import build_mmm_prompt_block


ROOT = pathlib.Path(__file__).resolve().parent
OUT_DIR = ROOT / "provider_receipts"
ROUTE_CARD = "tool_foundation_repair_audit"
COUNCIL_ROLE = "decision.experts_council+failure.premortem_council+follow_up.lane_council"
ROUTE_MINI_MMM_IDS = [
    "decision.experts_council",
    "failure.premortem_council",
    "failure.falsifier_council",
    "follow_up.lane_council",
    "follow_up.compile_gate_council",
    "expert.domain_specialist",
    "expert.standard_checker",
    "lane.direct",
    "lane.alternative",
    "voice.hume",
    "voice.feynman",
    "voice.popper",
    "voice.pushback",
    "voice.factory",
    "voice.strategy",
    "voice.systems",
]

BASE_PROMPT = """Read-only audit for Codex Ratchet tool-foundation repair.

Current owner correction:
- Actual nonclassical QIT engine/manifold attractor-basin sims cannot use numpy in the load-bearing path.
- Formal sims have three lanes: classical sims may use numpy load-bearing for classical numerical claims; bridge/baseline/supportive sims may use numpy with explicit role boundaries; source-native nonclassical QIT engine/manifold/FEP/Holodeck sims cannot use numpy as the load-bearing attractor-basin path.
- Tools must meet the standards of the constraints, or no real attractor basin can form.
- Redo means patch and rerun, not delete old receipts.

Indexed local receipt facts from the refreshed repo indexes; do not treat this prompt as fresh validation:
- Formal-scout source/result estate: 331 sources and 331 result receipts; readiness validator pass/fail is 316/14 plus 1 non-formal boundary. All 14 validator-red rows are preserved red/nonclearance evidence, with 0 actionable validator-red repair rows.
- v5 primitive lego/tool rows remain bounded capability evidence, not promotion.
- sim_estate_integration_index maps the geometric constraint manifold as a candidate root object: manifold=285 rows, PEPS/PEPS3D/MPS=98 rows, Axis0=152 rows, attractor-basin=151 rows, and auto_LiRPA/le-wm=36 rows.
- numpy_quarantine_source_native_nonclassical_gate now reports 16 NumPy-pattern source files total, 0 hard quarantines, 0 review-required surfaces, 15 reviewed NumPy-bearing boundary files preserved as nonclassical-claim blocked, 1 quarantine-scanner self-hit / legacy-baseline boundary file separate, and 0 receipt hard quarantines.
- constraint_admissible_tool_role_gate now reports 188 nonclassical/source-native result surfaces, 178 tool-role candidates, and 10 `blocked_result_not_all_pass` rows. The 10 blocked rows are preserved red/nonclearance evidence, not active EngineCore importer-boundary blockers. A tool-role candidate is a bounded admissible role, not proof or promotion.
- Latest repairs: LiRPA multicarrier downstream gate/signature math moved from NumPy to PyTorch while remaining formal_scout/promotion_allowed=false; the upstream subdense carrier/environment-density path is still explicitly bounded as NumPy/quimb-backed; a new PyG/rustworkx graph-order successor consumes the active 13-layer receipt and makes Data.validate/MessagePassing plus PyDiGraph DAG/reachability pass predicates load-bearing.
- Latest branch scout: antiteleology_geometric_constraint_manifold_pytorch_branch_tensor_network_probe is all_pass true, formal_scout/promotion_allowed=false, and uses PyTorch/autograd, active direct le-wm module.py SIGReg/ARPredictor, auto_LiRPA, z3/cvc5, sympy, Clifford, geomstats, e3nn, rustworkx, XGI, TopoNetX, GUDHI, and PyG around five order-sensitive manifold branch futures without NumPy load-bearing.
- Latest capability repair: system_v4/probes/sim_quimb_capability.py now writes a passing quimb_capability_results.json; scripts/verify_load_bearing_has_capability_probe.py --sim sim_lirpa_policy_bound_gated_multicarrier_environment_probe.py reports pytorch/quimb/z3 all ok.

Audit task:
1. Premortem the repair plan: validate all tool integration sims from foundations upward, then patch/rerun dependent source-native engine/manifold/FEP/Holodeck sims.
2. Identify the smallest receipt-bearing first repair that creates real progress.
3. Name overclaims to block.
4. Propose a parallel lane map across tools: PyTorch/autograd, z3/cvc5, sympy, Clifford, geomstats, e3nn, rustworkx, XGI, TopoNetX, GUDHI, PyG, quimb/cotengra/kahypar.

Provider output is proposal/audit only. Local formal scouts and validators remain authority."""


def build_prompt() -> tuple[str, dict[str, Any]]:
    mmm_block, mmm_metadata = build_mmm_prompt_block(
        route_card=ROUTE_CARD,
        council_role=COUNCIL_ROLE,
        mini_ids=ROUTE_MINI_MMM_IDS,
    )
    return f"{mmm_block}\n\n{BASE_PROMPT}", mmm_metadata


def provider_receipt(
    *,
    provider: str,
    status: str,
    proposal_text: str = "",
    blocked_reason: str = "",
    model: str = "",
    wizard_mmm: dict[str, Any] | None = None,
    prompt_sha256: str = "",
    raw_response: Any = None,
) -> dict[str, Any]:
    return {
        "schema": "PROVIDER_PROPOSAL_RECEIPT_v1",
        "provider": provider,
        "route": ROUTE_CARD,
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
                "system_v5/evidence/sim_estate_integration_index.json",
                "system_v5/docs/SIM_ESTATE_INTEGRATION_INDEX.md",
                "system_v5/docs/LEGO_SIM_CONTRACT.md",
            ],
            "local_facts_embedded_in_prompt": True,
            "wizard_mmm_loaded_in_prompt": bool(wizard_mmm and wizard_mmm.get("mmm_loaded")),
        },
        "wizard_mmm": wizard_mmm or {},
        "prompt_sha256": prompt_sha256,
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
    prompt, wizard_mmm = build_prompt()
    prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    if not key:
        return provider_receipt(provider="grok", status="blocked", blocked_reason="XAI_API_KEY not set", model=model, wizard_mmm=wizard_mmm, prompt_sha256=prompt_sha256)
    try:
        raw = post_json(
            "https://api.x.ai/v1/chat/completions",
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
            timeout,
        )
        return provider_receipt(provider="grok", status="completed", proposal_text=raw["choices"][0]["message"]["content"], model=model, wizard_mmm=wizard_mmm, prompt_sha256=prompt_sha256, raw_response=raw)
    except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return provider_receipt(provider="grok", status="blocked", blocked_reason=repr(exc), model=model, wizard_mmm=wizard_mmm, prompt_sha256=prompt_sha256)


def run_gemini(timeout: float) -> dict[str, Any]:
    key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()
    model = os.environ.get("WIZARD_GEMINI_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash"
    prompt, wizard_mmm = build_prompt()
    prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    if not key:
        return provider_receipt(provider="gemini", status="blocked", blocked_reason="GEMINI_API_KEY/GOOGLE_API_KEY not set", model=model, wizard_mmm=wizard_mmm, prompt_sha256=prompt_sha256)
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
        return provider_receipt(provider="gemini", status="completed", proposal_text=text, model=model, wizard_mmm=wizard_mmm, prompt_sha256=prompt_sha256, raw_response=raw)
    except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return provider_receipt(provider="gemini", status="blocked", blocked_reason=repr(exc), model=model, wizard_mmm=wizard_mmm, prompt_sha256=prompt_sha256)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["grok", "gemini"], required=True)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    parser.add_argument("--print-prompt-metadata", action="store_true")
    parser.add_argument("--write-prompt", help="Write the MMM-loaded provider prompt and metadata sidecar, then exit.")
    args = parser.parse_args()

    if args.print_prompt_metadata:
        prompt, wizard_mmm = build_prompt()
        print(json.dumps({"prompt_chars": len(prompt), "wizard_mmm": wizard_mmm}, indent=2, sort_keys=True))
        return 0

    if args.write_prompt:
        prompt, wizard_mmm = build_prompt()
        prompt_path = pathlib.Path(args.write_prompt)
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt, encoding="utf-8")
        metadata_path = prompt_path.with_suffix(prompt_path.suffix + ".metadata.json")
        metadata = {
            "prompt_chars": len(prompt),
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "wizard_mmm": wizard_mmm,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"prompt_path": str(prompt_path), "metadata_path": str(metadata_path), **metadata}, indent=2, sort_keys=True))
        return 0

    receipt = run_grok(args.timeout) if args.provider == "grok" else run_gemini(args.timeout)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.stamp}_{args.provider}_tool_foundation_repair_audit.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"path": str(out), "provider": args.provider, "status": receipt["status"]}))
    return 0 if receipt["status"] in {"completed", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
