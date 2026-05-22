#!/usr/bin/env python3
"""Run bounded Grok/Gemini audits for manifold integration and basin solidity."""

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
ROUTE_CARD = "manifold_integration_premortem_audit"
COUNCIL_ROLE = "failure.premortem_council+failure.falsifier_council"
ROUTE_MINI_MMM_IDS = [
    "failure.premortem_council",
    "failure.falsifier_council",
    "failure.loophole_auditor_council",
    "premortem.likely_failure",
    "premortem.dangerous_failure",
    "premortem.hidden_assumption",
    "premortem.sim_evidence_corruption",
    "voice.hume",
    "voice.popper",
    "voice.pushback",
    "voice.systems",
]

BASE_PROMPT = """Read-only premortem audit for Codex Ratchet geometric-constraint-manifold integration.

Authority boundary:
- Provider output is proposal/audit only. Local formal-scout receipts and validators remain authority.
- The geometric constraint manifold is the candidate root surface; the 13-shell inventory is a current indexing fixture / candidate scaffold, not an admitted source-model layer order.
- PEPS/PEPS3D, Axis0, attractor-basin receipts, graph/proof tools, auto_LiRPA, and le-wm are evidence surfaces over that candidate, not final manifold promotion.

Indexed local receipt facts from sim_estate_integration_index; do not treat this prompt as fresh validation:
- Formal-scout source/result estate: 331 sources and 331 result receipts.
- Independent grok_sim process line: 2502 files in the current sim-estate index, proposal/failure-pattern mining until translated into formal scouts.
- Scratch/council estate: /tmp/engine_v2 has 275 files, not canonical evidence.
- Index rows: manifold=285, PEPS/PEPS3D/MPS=98, Axis0=152, attractor-basin=151, auto_LiRPA/le-wm=36.
- Tool-role gate: 188 scanned nonclassical/source-native result surfaces; 178 candidates; 10 `blocked_result_not_all_pass` rows. The 10 blocked rows are preserved red/nonclearance evidence, not active EngineCore importer-boundary blockers.
- NumPy quarantine: source scan sees 16 NumPy-pattern files total, 0 hard quarantines, 0 review-required surfaces, 15 reviewed NumPy-bearing boundary files preserved as nonclassical-claim blocked, 1 quarantine-scanner self-hit / legacy-baseline boundary file separate, and 0 receipt hard quarantines.

Core manifold receipts to audit:
- antiteleology_geometric_constraint_manifold_pytorch_branch_tensor_network_probe: all_pass true, formal_scout/promotion_allowed false, 13 layers, 5 anti-teleological branch orders, PyTorch autograd MPS/PEPS/PEPS3D tensor-network signatures, active direct import of local le-wm module.py SIGReg/ARPredictor through EXTERNAL_MODULE_MANIFEST, auto_LiRPA IBP branch-energy bounds, PyG/rustworkx graph-order checks, XGI/TopoNetX/GUDHI topology checks, and z3/cvc5 cross-solver admission/knockout witnesses.
- nested_geometry_tower_dependency_order_probe: 13 layers, all_pass true, load-bearing clifford/geomstats/gudhi/opt_einsum/pytorch/rustworkx/toponetx/torch_geometric/xgi/z3; dependency-order scout, not dynamic evolution.
- integrated_nested_geometric_constraint_manifold_dynamic_tensor_network_probe: 13 layers, summary.all_pass true, 64 microsteps, max coherent information 0.4022, min conditional entropy -0.4022, promotion_allowed false.
- thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe: 13 layers, summary.all_pass true, 64 microsteps, cross-track divergence 1.6891, track A max coherent information 0.3991, track B 0.0974, promotion_allowed false, tool-role gate now marks tool_role_candidate after NumPy demotion/boundary handling.
- thirteen_layer_active_manifold_layer_removal_graph_order_pyg_rustworkx_probe: all_pass true, consumes the active 13-layer parent receipt, uses PyG Data.validate/MessagePassing plus rustworkx PyDiGraph/topological_sort/transitive_reduction/reachability and z3 noncollapse witness as direct load-bearing pass predicates.
- axis0_vector_bundle_thirteen_shell_pytorch_peps3d_lirpa_noncollapse_probe: all_pass true, formal_scout/promotion_allowed false, consumes admitted Axis0 candidates as a 13x3 vector bundle across all 13 shells, rejects scalar-projection, zero-axis, drop-one, and blocked-candidate controls, and uses PyTorch/PEPS3D, le-wm ARPredictor pressure, auto_LiRPA IBP, PyG/rustworkx, z3, and cvc5. It is a vector-valued fixture, not an upstream Axis0 actuator repair.
- dynamic_manifold_stability_cross_track_lirpa_falsifier_probe: all_pass true, formal_scout/promotion_allowed false, consumes the integrated 13-layer manifold receipts plus the Axis0 vector-bundle and Axis0 LiRPA assembly receipts. It tests both evolve-then-enforce and enforce-then-evolve orders over 64/128/256 horizons with PyTorch/autograd, PEPS3D signatures, le-wm ARPredictor, auto_LiRPA IBP, PyG/rustworkx/GUDHI, and z3/cvc5. Verdict: current_real_convergence_claim_status killed; finite_fixture_status open.
- constraint_manifold_multitool_entropy_geometry_carrier_integration_probe: all_pass true, MPS/PEPS/PEPS3D carrier paths separate, but includes numpy and is still scout-level.
- lirpa_policy_bound_gated_multicarrier_environment_probe: all_pass true and tool_role_candidate after downstream gate/signature math moved to PyTorch; generic load-bearing capability verifier now reports pytorch/quimb/z3 all ok; upstream subdense carrier/environment-density implementation is still explicitly bounded as NumPy/quimb-backed, so do not call this a full PyTorch substrate migration.

Axis0 current state:
- Admitted candidates: fep_gradient_polarity, correlation_diversity_derivative, retrocausal_many_futures_policy_scoring.
- Blocked candidates: path_entropy, holographic_boundary_interior_reconstruction.
- Contribution rank: 3.
- Scalar projection blocker remains: per-candidate controls are preserved, but actuation still projects bundle to a scalar before carrier actuation.
- New vector-bundle fixture: axis0_vector_bundle_thirteen_shell_pytorch_peps3d_lirpa_noncollapse_probe rejects scalar projection over the admitted bundle, but explicitly does not repair the upstream scalar-weighted actuator.
- New dynamic stability falsifier: dynamic_manifold_stability_cross_track_lirpa_falsifier_probe kills the current real attractor-basin convergence claim while leaving the finite vector fixture open under the 64/128/256-horizon order envelope.

Audit task:
1. Premortem: assume six months from now the team admits the manifold/basin claim too early and it fails. Name the failure chain.
2. Assess whether current evidence supports "real attractor basin convergence" or only scout-level basin evidence. Name exact receipt types that can and cannot count.
3. Assess geometric constraint manifold solidity: which layers/tools/carriers are solid, which remain tool-role or coupling gaps, and where PEPS/PEPS3D actually bears load.
4. Identify the smallest next repair or scout that creates real progress without broad queue relaunch.
5. Identify graph/proof/PyTorch integration gaps, including z3/cvc5, sympy, Clifford, rustworkx, XGI, TopoNetX, GUDHI, PyG, PyTorch/autograd, quimb/cotengra, auto_LiRPA, and le-wm.
6. List overclaims to block in the next controller synthesis.

Return concise JSON-like sections:
- premortem_failure_chain
- current_evidence_verdict
- peps_peps3d_verdict
- tool_integration_gaps
- smallest_next_repair
- overclaims_to_block
- falsifier_for_next_scout"""


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
                "system_v5/evidence/sim_estate_integration_index.json",
                "system_v5/docs/SIM_ESTATE_INTEGRATION_INDEX.md",
                "system_v5/docs/GEOMETRIC_CONSTRAINT_MANIFOLD_FORMAL_SCOUT_CONTRACT.md",
                "system_v5/docs/GEOMETRIC_CONSTRAINT_MANIFOLD_FULL_THREAD_HANDOFF_20260515.md",
                "system_v5/docs/MANIFOLD_FULL_NESTED_LAYER_TOWER_AND_GSTRUCTURE_AND_INTEGRATION_GAP_20260515.md",
                "system_v5/ops/formal_scouts/results/antiteleology_geometric_constraint_manifold_pytorch_branch_tensor_network_probe_results.json",
                "system_v5/ops/formal_scouts/results/integrated_nested_geometric_constraint_manifold_dynamic_tensor_network_probe_results.json",
                "system_v5/ops/formal_scouts/results/thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe_results.json",
                "system_v5/ops/formal_scouts/results/constraint_manifold_multitool_entropy_geometry_carrier_integration_probe_results.json",
                "system_v5/ops/formal_scouts/results/axis0_plural_candidate_multicarrier_drive_controls_probe_results.json",
                "system_v5/ops/formal_scouts/results/constraint_admissible_tool_role_gate_probe_results.json",
                "system_v5/ops/formal_scouts/results/numpy_quarantine_source_native_nonclassical_gate_probe_results.json",
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
    parser.add_argument("--timeout", type=float, default=120.0)
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

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = run_grok(args.timeout) if args.provider == "grok" else run_gemini(args.timeout)
    out = OUT_DIR / f"{args.stamp}_{args.provider}_manifold_integration_premortem_audit.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(f"status={receipt['status']}")
    if receipt.get("blocked_reason"):
        print(receipt["blocked_reason"])
    return 0 if receipt["status"] in {"completed", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
