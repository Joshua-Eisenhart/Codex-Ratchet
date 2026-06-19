#!/usr/bin/env python3
"""Hermes-owned sim swarm controller for Codex Ratchet v7 work.

This is the Hermes control layer over the existing sim/gate surfaces.  It does
not replace the sim math and it does not trust model prose as evidence.  Its
job is to:

1. inspect available execution seats (codex CLI, OpenRouter key, CocoIndex MCP);
2. read the real target sim receipts and state the actual math observables;
3. emit parent/kid task cards for high-divergence swarms;
4. refuse to mark a model seat runnable when the runtime is missing.

Claim ceiling: controller/planning and receipt summarization only.  It grants no
sim promotion and performs no admission beyond the existing validators.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
SIMS = REPO / "system_v7" / "sims"
DEFAULT_OUT_ROOT = REPO / "system_v7" / "control" / "hermes_swarm_runs"
SIM_STACK_PY = Path(os.environ.get("SIM_STACK_PY", "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"))
JULIA = Path(os.environ.get("JULIA", "/opt/homebrew/bin/julia"))
JULIA_PROJECT = REPO / "system_v5" / "julia_carrier"
CR_COCOINDEX_MCP = Path("/Users/joshuaeisenhart/.local/bin/cocoindex-codex-ratchet-mcp")
WIKI_COCOINDEX_MCP = Path("/Users/joshuaeisenhart/.local/bin/cocoindex-wiki-mcp")

TARGET_SIMS = [
    "probe_quotient_fingerprint_floor_v1",
    "forced_or_installed_carrier_comparison_v0",
    "carrier_type_admissibility_matrix_v0",
]

PARENT_LENSES = [
    {
        "id": "floor_math_audit",
        "goal": "State the exact Rung-0 quotient math and separate forced finite-table quotient from solver consistency checks.",
        "falsifier": "A report that gives class counts but not the fingerprint rows/classes and erased-control witness fails.",
    },
    {
        "id": "forced_vs_installed_nesting",
        "goal": "Test whether a second layer is forced by prior quotient/readout constraints or merely installed by chosen carrier coordinates.",
        "falsifier": "A claimed nesting result with no free second object, no reproduce constraints, or no SAT/UNSAT polarity fails.",
    },
    {
        "id": "cross_type_carrier_matrix",
        "goal": "Construct carriers as math objects, not labels, and derive the admissibility/order relation structurally.",
        "falsifier": "A hand-ranked strength order or metadata carrier label fails even if the table is pretty.",
    },
    {
        "id": "order_bracket_noncommutation",
        "goal": "Probe whether layer order/bracketing changes admitted witnesses; include commuting controls.",
        "falsifier": "If all operators commute or the only witness is cardinality, the nesting claim is open or killed.",
    },
    {
        "id": "gate_schema_hole_finder",
        "goal": "Find holes in validators/admission surfaces that let unstated math, vibe judgments, or undefined tokens pass.",
        "falsifier": "A green local run with failed admission gates must be reported as runs-but-not-admitted, never PASS full stop.",
    },
]

MODEL_SEAT_TEMPLATE = [
    {"seat": "codex_a", "kind": "codex_cli", "model": "codex", "role": "builder"},
    {"seat": "codex_b", "kind": "codex_cli", "model": "codex", "role": "critic_builder"},
    {"seat": "deepseek", "kind": "openrouter", "model": "deepseek/deepseek-r1-0528", "role": "math_skeptic"},
    {"seat": "qwen", "kind": "openrouter", "model": "qwen/qwen3-235b-a22b", "role": "variant_builder"},
    {"seat": "kimi", "kind": "openrouter", "model": "moonshotai/kimi-k2", "role": "edge_case_miner"},
    {"seat": "grok", "kind": "openrouter", "model": "x-ai/grok-4.3", "role": "falsifier"},
    {"seat": "gemini", "kind": "openrouter", "model": "google/gemini-2.5-pro", "role": "structure_auditor"},
    {"seat": "glm", "kind": "openrouter", "model": "z-ai/glm-4.5", "role": "control_designer"},
]

@dataclass
class SeatStatus:
    kind: str
    runnable: bool
    evidence: str

@dataclass
class RuntimeProbe:
    codex_cli: SeatStatus
    codex1_alias: SeatStatus
    openrouter: SeatStatus
    cocoindex_repo_mcp: SeatStatus
    cocoindex_wiki_mcp: SeatStatus
    sim_stack_python: SeatStatus
    julia: SeatStatus

@dataclass
class TargetSummary:
    sim_id: str
    status: str
    result_path: str | None
    math_observables: dict[str, Any] = field(default_factory=dict)
    claim_ceiling: str | None = None
    admission_gate_status: str = "not_run"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(cmd: list[str], *, cwd: Path = REPO, timeout: int = 180) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return proc.returncode, proc.stdout


def which_status(name: str) -> SeatStatus:
    p = shutil.which(name)
    if p:
        return SeatStatus(name, True, p)
    return SeatStatus(name, False, f"missing executable: {name}")


def file_status(path: Path, kind: str) -> SeatStatus:
    return SeatStatus(kind, path.exists(), str(path) if path.exists() else f"missing: {path}")


def probe_runtime() -> RuntimeProbe:
    codex = which_status("codex")
    codex1 = which_status("codex1")
    openrouter_key = bool(os.environ.get("OPENROUTER_API_KEY"))
    openrouter = SeatStatus("openrouter", openrouter_key, "OPENROUTER_API_KEY present" if openrouter_key else "OPENROUTER_API_KEY missing")
    return RuntimeProbe(
        codex_cli=codex,
        codex1_alias=codex1,
        openrouter=openrouter,
        cocoindex_repo_mcp=file_status(CR_COCOINDEX_MCP, "cocoindex_repo_mcp"),
        cocoindex_wiki_mcp=file_status(WIKI_COCOINDEX_MCP, "cocoindex_wiki_mcp"),
        sim_stack_python=file_status(SIM_STACK_PY, "sim_stack_python"),
        julia=file_status(JULIA, "julia"),
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def floor_summary(sim_dir: Path) -> TargetSummary:
    path = sim_dir / "results" / "probe_quotient_fingerprint_floor_v1_three_engine_results.json"
    if not path.exists():
        return TargetSummary(sim_dir.name, "missing_result", None)
    doc = read_json(path)
    q = doc.get("quotient", {})
    flip = doc.get("smt_flip", {})
    return TargetSummary(
        sim_id=sim_dir.name,
        status="runs_receipt_present" if doc.get("all_pass") else "receipt_not_all_pass",
        result_path=str(path),
        math_observables={
            "support": q.get("support"),
            "full_classes": q.get("full_classes"),
            "erased_classes": q.get("erased_classes"),
            "full_class_count": q.get("full_class_count"),
            "erased_class_count": q.get("erased_class_count"),
            "erased_merge_pair": (doc.get("flip_control") or {}).get("erased_merge_pair"),
            "persistent_pair": (doc.get("boundary_tests") or {}).get("persistent_indistinguishable_pair_under_full_P"),
            "smt_flip": {
                "z3_full_P": ((doc.get("crossover_proofs") or {}).get("z3") or {}).get("full_P_verdict"),
                "z3_erased_P": ((doc.get("crossover_proofs") or {}).get("z3") or {}).get("erased_P_verdict"),
                "cvc5_full_P": ((doc.get("crossover_proofs") or {}).get("cvc5") or {}).get("full_P_verdict"),
                "cvc5_erased_P": ((doc.get("crossover_proofs") or {}).get("cvc5") or {}).get("erased_P_verdict"),
                "julia_z3_full_P": ((doc.get("crossover_proofs") or {}).get("julia_z3") or {}).get("full_P_verdict"),
                "julia_z3_erased_P": ((doc.get("crossover_proofs") or {}).get("julia_z3") or {}).get("erased_P_verdict"),
            },
            "solver_role": "supportive consistency only, not structural discovery",
        },
        claim_ceiling=doc.get("claim_ceiling"),
    )


def forced_installed_summary(sim_dir: Path) -> TargetSummary:
    path = sim_dir / "results" / "forced_or_installed_carrier_comparison_v0_three_engine_results.json"
    if not path.exists():
        return TargetSummary(sim_dir.name, "missing_result", None)
    doc = read_json(path)
    return TargetSummary(
        sim_id=sim_dir.name,
        status="runs_receipt_present" if doc.get("all_pass") else "receipt_not_all_pass",
        result_path=str(path),
        math_observables={
            "carrier_type": doc.get("carrier_type"),
            "decision_rule": doc.get("decision_rule"),
            "installed_fixture_statuses": ((doc.get("fixture_verdicts") or {}).get("installed_incomplete") or {}).get("statuses"),
            "forced_fixture_statuses": ((doc.get("fixture_verdicts") or {}).get("forced_complete") or {}).get("statuses"),
            "installed_C2_witness": doc.get("installed_multiplicity_witness"),
            "reproduce_on_off": doc.get("reproduce_on_off_comparison"),
            "non_isomorphism_predicate": doc.get("non_isomorphism_predicate"),
        },
        claim_ceiling=doc.get("claim_ceiling"),
    )


def carrier_matrix_summary(sim_dir: Path) -> TargetSummary:
    path = sim_dir / "results" / "carrier_type_admissibility_matrix_v0_three_engine_results.json"
    if not path.exists():
        return TargetSummary(sim_dir.name, "missing_result", None)
    doc = read_json(path)
    fixtures = doc.get("fixture_verdicts") or doc.get("fixtures") or {}
    return TargetSummary(
        sim_id=sim_dir.name,
        status="runs_receipt_present" if doc.get("all_pass") else "receipt_not_all_pass",
        result_path=str(path),
        math_observables={
            "claim": doc.get("claim"),
            "fixtures": doc.get("full_allowed_excluded_matrix"),
            "order_gap_clean_isolation_proof": doc.get("order_gap_clean_isolation_proof"),
            "multiplicity_fixture_witness": doc.get("multiplicity_fixture_witness"),
            "allowed_excluded_summary": doc.get("full_allowed_excluded_matrix"),
            "load_bearing_negative": "order_gap_clean excludes classical_noncontextual via non-disturbing joint contradiction, per BUILD_REPORT",
            "known_boundary": "real_rebit Y exclusion is by_construction boundary/control, not load-bearing negative",
        },
        claim_ceiling=doc.get("claim_ceiling"),
    )


def summarize_targets() -> list[TargetSummary]:
    out: list[TargetSummary] = []
    for sim_id in TARGET_SIMS:
        sim_dir = SIMS / sim_id
        if sim_id == "probe_quotient_fingerprint_floor_v1":
            out.append(floor_summary(sim_dir))
        elif sim_id == "forced_or_installed_carrier_comparison_v0":
            out.append(forced_installed_summary(sim_dir))
        elif sim_id == "carrier_type_admissibility_matrix_v0":
            out.append(carrier_matrix_summary(sim_dir))
    return out


def validate_sim(sim_id: str) -> dict[str, Any]:
    sim_dir = SIMS / sim_id
    code, out = run([str(SIM_STACK_PY), "scripts/validate_v7_admission.py", str(sim_dir)], timeout=240)
    try:
        parsed = json.loads(out)
    except json.JSONDecodeError:
        parsed = {"raw": out[:4000]}
    return {"sim_id": sim_id, "returncode": code, "ok": code == 0, "validator": parsed}


def card_for(parent: dict[str, str], seat: dict[str, str], runtime: RuntimeProbe, target_summaries: list[TargetSummary]) -> dict[str, Any]:
    seat_kind = seat["kind"]
    if seat_kind == "codex_cli":
        runnable = runtime.codex_cli.runnable
        block = None if runnable else runtime.codex_cli.evidence
    elif seat_kind == "openrouter":
        runnable = runtime.openrouter.runnable
        block = None if runnable else runtime.openrouter.evidence
    else:
        runnable = False
        block = "unknown seat kind"
    prompt = f"""You are a bounded Codex Ratchet sim worker under Hermes control.

Parent lens: {parent['id']}
Goal: {parent['goal']}
Strong falsifier: {parent['falsifier']}

Binding rules:
- State the actual math rule first: object, operation/probe, observable, pass/fail.
- Do not report class counts without the rule that produced them.
- Preserve live alternatives; do not promote a winner.
- Existing target receipts are data, not authority above their claim ceiling.
- If you propose a sim, include positive case, negative/erased control, boundary case, and demotion condition.
- Output JSON with fields: candidate_id, stated_math, operation, observable, pass_fail_condition, controls, falsifier, required_engines, holes_found, claim_ceiling.
"""
    return {
        "task_id": f"{parent['id']}__{seat['seat']}",
        "parent_lens": parent,
        "seat": seat,
        "runnable_now": runnable,
        "blocked_reason": block,
        "input_refs": [s.result_path for s in target_summaries if s.result_path],
        "prompt_sha256": sha256_text(prompt),
        "prompt": prompt,
        "classification": "scratch_diagnostic",
        "claim_ceiling": "candidate-generation/audit only; no sim promotion; math must be stated and mechanically checked before evidence",
    }


def emit_plan(out_dir: Path, parents: int, kids: int) -> dict[str, Any]:
    runtime = probe_runtime()
    summaries = summarize_targets()
    validations = [validate_sim(s.sim_id) for s in summaries if s.result_path]
    selected_parents = PARENT_LENSES[:parents]
    cards: list[dict[str, Any]] = []
    card_dir = out_dir / "cards"
    card_dir.mkdir(parents=True, exist_ok=True)
    for parent in selected_parents:
        seats = MODEL_SEAT_TEMPLATE[:kids]
        for seat in seats:
            card = card_for(parent, seat, runtime, summaries)
            cards.append(card)
            (card_dir / f"{card['task_id']}.json").write_text(json.dumps(card, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema": "codex_ratchet.hermes_sim_swarm_plan.v1",
        "created_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": str(REPO),
        "claim_ceiling": "Hermes controller plan and receipt summary only; no model output admitted as sim evidence.",
        "runtime": asdict(runtime),
        "targets": [asdict(s) for s in summaries],
        "validator_results": validations,
        "parents": selected_parents,
        "kids_per_parent": kids,
        "task_card_count": len(cards),
        "runnable_card_count": sum(1 for c in cards if c["runnable_now"]),
        "blocked_card_count": sum(1 for c in cards if not c["runnable_now"]),
        "cards_dir": str(card_dir),
        "holes_observed": holes_from_state(runtime, validations),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "REPORT.md").write_text(render_report(manifest), encoding="utf-8")
    return manifest


def holes_from_state(runtime: RuntimeProbe, validations: list[dict[str, Any]]) -> list[str]:
    holes: list[str] = []
    if not runtime.codex1_alias.runnable:
        holes.append("codex1 seat name requested by prior workflow is not a real executable here; only `codex` CLI is present.")
    if not runtime.openrouter.runnable:
        holes.append("OpenRouter fanout is blocked in this shell: OPENROUTER_API_KEY missing.")
    for v in validations:
        if not v.get("ok"):
            failed = (v.get("validator") or {}).get("failed_gates")
            holes.append(f"{v['sim_id']} runs locally but validate_v7_admission fails gates: {failed}")
    holes.append("Existing forced-vs-installed v0 proves coordinate-uniqueness inside chosen rho coordinates, not gauge/ontological uniqueness or cross-type foundation closure.")
    holes.append("Actual nesting remains open until an order/bracket/second-layer sim shows a structural SAT/UNSAT flip with stated math and controls.")
    return holes


def render_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Hermes Sim Swarm Plan",
        "",
        f"Created: `{manifest['created_at']}`",
        "",
        "## Status",
        "",
        f"- Task cards: `{manifest['task_card_count']}`",
        f"- Runnable now: `{manifest['runnable_card_count']}`",
        f"- Blocked now: `{manifest['blocked_card_count']}`",
        "- Claim ceiling: controller plan / receipt summary only; no promotion.",
        "",
        "## Runtime seats",
        "",
    ]
    for name, status in manifest["runtime"].items():
        lines.append(f"- `{name}`: `{status['runnable']}` — {status['evidence']}")
    lines += ["", "## Target math summaries", ""]
    for target in manifest["targets"]:
        lines.append(f"### `{target['sim_id']}`")
        lines.append(f"- status: `{target['status']}`")
        lines.append(f"- result: `{target['result_path']}`")
        if target.get("claim_ceiling"):
            lines.append(f"- claim ceiling: {target['claim_ceiling']}")
        obs = target.get("math_observables") or {}
        for key in sorted(obs):
            value = json.dumps(obs[key], sort_keys=True) if not isinstance(obs[key], str) else obs[key]
            lines.append(f"- `{key}`: {value}")
        lines.append("")
    lines += ["## Holes observed", ""]
    for h in manifest["holes_observed"]:
        lines.append(f"- {h}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe-runtime")
    sub.add_parser("summarize-targets")
    plan = sub.add_parser("plan")
    plan.add_argument("--out-dir", type=Path, default=None)
    plan.add_argument("--parents", type=int, default=5)
    plan.add_argument("--kids", type=int, default=8)
    args = parser.parse_args(argv)

    if args.cmd == "probe-runtime":
        print(json.dumps(asdict(probe_runtime()), indent=2, sort_keys=True))
        return 0
    if args.cmd == "summarize-targets":
        print(json.dumps([asdict(s) for s in summarize_targets()], indent=2, sort_keys=True))
        return 0
    if args.cmd == "plan":
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = args.out_dir or (DEFAULT_OUT_ROOT / stamp)
        manifest = emit_plan(out_dir, max(1, min(args.parents, len(PARENT_LENSES))), max(1, min(args.kids, len(MODEL_SEAT_TEMPLATE))))
        print(json.dumps({"ok": True, "manifest": str(out_dir / "manifest.json"), "report": str(out_dir / "REPORT.md"), "task_card_count": manifest["task_card_count"], "runnable_card_count": manifest["runnable_card_count"], "blocked_card_count": manifest["blocked_card_count"]}, indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
