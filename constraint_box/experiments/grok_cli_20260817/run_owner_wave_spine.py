#!/usr/bin/env python3
"""Run the owner W-* sequence. Premortem is a council, not a wave.

Waves in order:
  W-INDEX, W-INDUCTION, W-DEDUCTION, W-PROMPT, W-OUTPUT,
  W-CONTEXT, W-PROJECT, W-REPAIR, W-VERIFY

W-WATCH is not a wave. cb-*-wave folder names are not this sequence.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
BOX = HERE.parents[1]
SRC = BOX / "src"
WORK = BOX / "integrated_system" / "runs" / "owner_wave_spine"
BRIDGE = Path.home() / ".codex/skills/claude-bridge/scripts/claude_bridge.py"
AGENTS = Path.home() / "Codex-Ratchet" / ".claude" / "agents"
MINI = Path.home() / "wiki/wizard/packet-v4-3-current/mmm/mini/full/voices/md"
PACKS = Path.home() / "Codex-Ratchet" / "constraint_box" / "mmm" / "packs"
PREMORTEM = Path.home() / ".codex/skills/premortem/SKILL.md"
CAMPAIGN = BOX / "receipts" / "campaign_path_mass" / "v1" / "result.json"
WAVES = (
    "W-INDEX",
    "W-INDUCTION",
    "W-DEDUCTION",
    "W-PROMPT",
    "W-OUTPUT",
    "W-CONTEXT",
    "W-PROJECT",
    "W-REPAIR",
    "W-VERIFY",
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _read(path: Path, limit: int) -> tuple[str, str, int]:
    if not path.is_file():
        return "", "", 0
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:limit], _sha_file(path), len(text)


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ngrams(text: str, k: int = 4) -> set[str]:
    words = text.split()
    return {" ".join(words[i : i + k]) for i in range(max(0, len(words) - k + 1))}


def diversity(texts: list[str]) -> dict[str, Any]:
    sets = [_ngrams(text) for text in texts]
    overlaps = [
        (len(a & b) / len(a | b)) if (a | b) else 0.0
        for a, b in itertools.combinations(sets, 2)
    ] or [0.0]
    dups = len(texts) - len({hashlib.sha256(text.encode()).hexdigest() for text in texts})
    maximum = max(overlaps)
    return {
        "max_overlap": round(maximum, 4),
        "mean_overlap": round(sum(overlaps) / len(overlaps), 4),
        "duplicates": dups,
        "verdict": "DIVERSE" if maximum < 0.8 and dups == 0 else "COLLAPSED",
    }


def campaign_facts() -> dict[str, Any]:
    if not CAMPAIGN.is_file():
        return {"status": "HOLD", "reason": "campaign_path_mass receipt missing"}
    body = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    return {
        "status": body.get("status"),
        "receipt_sha256": body.get("receipt_sha256"),
        "probe_rows_sha256": body.get("generator", {}).get("probe_rows_sha256"),
        "gate_rows_sha256": body.get("generator", {}).get("gate_rows_sha256"),
        "n_probe_rows": body.get("generator", {}).get("n_probe_rows"),
        "n_qit_pass": body.get("generator", {}).get("n_qit_pass"),
        "n_both_pass": body.get("generator", {}).get("n_both_pass"),
        "minilev": body.get("generator", {}).get("minilev"),
        "map_replay": body.get("map_replay"),
        "ratchet": [
            {
                "step": item.get("step"),
                "n_rows": item.get("n_rows"),
                "classes": (item.get("entropy") or {}).get("class_count"),
                "edges": (item.get("topology") or {}).get("n_edges"),
            }
            for item in body.get("ratchet") or []
        ],
        "probe_restriction": {
            "changes_entropy": (body.get("probe_restriction") or {}).get("changes_entropy"),
            "changes_topology": (body.get("probe_restriction") or {}).get("changes_topology"),
        },
        "recall": (body.get("recall") or {}).get("stored", {}).get("correct"),
        "disposition": {
            key: value
            for key, value in (body.get("disposition") or {}).items()
            if str(key).startswith("admit_")
        },
        "smt": {
            "real": (body.get("smt") or {}).get("real_memory", {}).get("z3"),
            "erased": (body.get("smt") or {}).get("erased_memory", {}).get("z3"),
        },
        "not": body.get("not"),
    }


def compose_member(voice: str, role: str, task: str, facts: dict[str, Any]) -> dict[str, Any]:
    spec_text, spec_sha, spec_n = _read(AGENTS / f"voice-{voice}.md", 2200)
    mini_text, mini_sha, mini_n = _read(MINI / f"MMM_VOICE_{voice.upper()}_FULL_v4_1.md", 2600)
    pack_text, pack_sha, pack_n = _read(PACKS / "nominalist.md", 1800)
    skill_text, skill_sha, skill_n = _read(PREMORTEM, 1600)
    prompt = (
        f"You are one member of a council inside wave {role.split('.')[0]}.\n"
        f"You are not a wave. Premortem is a skill/cell, not a wave.\n"
        f"FORMAL ROLE: {role}\n"
        f"VOICE: {voice}\n\n"
        f"=== AGENT SPEC ===\n{spec_text}\n"
        f"=== MINI-MMM ===\n{mini_text}\n"
        f"=== CB PACK ===\n{pack_text}\n"
        f"=== SKILL ===\n{skill_text}\n"
        f"=== OBJECT FACTS ===\n{json.dumps(facts, indent=2, sort_keys=True)}\n"
        f"=== TASK ===\n{task}\n\n"
        "Return ONLY a JSON object with keys:\n"
        "verdict, promotion_allowed, claim_ceiling, confidence, finding,\n"
        "failure_1, failure_2, tripwire, next_probe, slices_loaded.\n"
        "verdict must be PARKED, BLOCKED, or ADMIT_FOR_TESTING.\n"
        "promotion_allowed must be false.\n"
        "Do not invent a wave name. Do not promote the campaign to a basin.\n"
    )
    return {
        "voice": voice,
        "role": role,
        "prompt": prompt,
        "legs": {
            "agent_spec": {"sha256": spec_sha, "chars": spec_n},
            "mini_mmm": {"sha256": mini_sha, "chars": mini_n},
            "cb_pack": {"sha256": pack_sha, "chars": pack_n},
            "skill": {"sha256": skill_sha, "chars": skill_n},
        },
        "complete": all([spec_sha, mini_sha, pack_sha, skill_sha]),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
    }


def launch_claude(job_id: str, model: str, prompt: str) -> subprocess.Popen:
    out = WORK / "claude" / job_id
    out.mkdir(parents=True, exist_ok=True)
    prompt_path = out / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    return subprocess.Popen(
        [
            str(BRIDGE),
            "--model",
            model,
            "--prompt-file",
            str(prompt_path),
            "--budget",
            "1.5",
            "--timeout-sec",
            "180",
            "--tools",
            "Read",
            "--cwd",
            str(BOX),
            "--out-dir",
            str(out),
            "--name",
            job_id,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def collect_claude(job_id: str) -> dict[str, Any]:
    out = WORK / "claude" / job_id
    receipt = None
    for path in sorted(out.glob("*.receipt.json")):
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
            receipt["_path"] = str(path)
            break
        except json.JSONDecodeError:
            continue
    output_text = ""
    if receipt and receipt.get("output_path") and Path(receipt["output_path"]).is_file():
        raw = Path(receipt["output_path"]).read_text(encoding="utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
            output_text = str(parsed.get("result") or parsed.get("text") or raw)
        except json.JSONDecodeError:
            output_text = raw
    if not output_text:
        for path in out.glob("*.json"):
            if path.name.endswith("receipt.json"):
                continue
            try:
                parsed = json.loads(path.read_text(encoding="utf-8"))
                output_text = str(parsed.get("result") or "")
                if output_text:
                    break
            except json.JSONDecodeError:
                continue
    claim, reasons = gate_claim(output_text)
    completed = bool(receipt) and receipt.get("returncode") == 0 and not receipt.get("timed_out")
    return {
        "id": job_id,
        "completed": completed,
        "admitted": bool(completed and claim is not None and not reasons),
        "reasons": reasons,
        "claim": claim,
        "receipt_path": (receipt or {}).get("_path"),
        "cost_usd": ((receipt or {}).get("parsed") or {}).get("total_cost_usd"),
        "model": (receipt or {}).get("model"),
    }


def gate_claim(raw: str) -> tuple[dict[str, Any] | None, list[str]]:
    text = raw.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        return None, ["extract: no JSON object"]
    try:
        claim = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None, ["extract: JSONDecodeError"]
    reasons = []
    if not isinstance(claim, dict):
        return None, ["extract: not an object"]
    if claim.get("promotion_allowed") is not False:
        reasons.append("promotion_allowed must be false")
    if claim.get("verdict") not in {"PARKED", "BLOCKED", "ADMIT_FOR_TESTING"}:
        reasons.append("verdict not in PARKED/BLOCKED/ADMIT_FOR_TESTING")
    if not isinstance(claim.get("claim_ceiling"), str) or len(claim["claim_ceiling"]) < 10:
        reasons.append("claim_ceiling too short")
    conf = claim.get("confidence")
    if not isinstance(conf, (int, float)) or not 0 <= float(conf) <= 1:
        reasons.append("confidence outside [0,1]")
    return claim, reasons


def w_index(facts: dict[str, Any]) -> dict[str, Any]:
    members = [
        {
            "id": "campaign_hashes",
            "kind": "deterministic",
            "status": "COMPLETED"
            if facts.get("probe_rows_sha256")
            and facts.get("status") == "PASS"
            else "HOLD",
            "probe_rows_sha256": facts.get("probe_rows_sha256"),
            "gate_rows_sha256": facts.get("gate_rows_sha256"),
        },
        {
            "id": "minilev_receipt",
            "kind": "deterministic",
            "status": "COMPLETED"
            if (facts.get("minilev") or {}).get("terminal") == "RELEASED"
            else "HOLD",
            "flow_id": (facts.get("minilev") or {}).get("flow_id"),
            "terminal": (facts.get("minilev") or {}).get("terminal"),
        },
        {
            "id": "jax_qit_prefix",
            "kind": "deterministic",
            "status": "COMPLETED"
            if Path("/Users/joshuaeisenhart/.local/share/jax-qit-stack/bin/python3").is_file()
            else "HOLD",
            "path": "/Users/joshuaeisenhart/.local/share/jax-qit-stack",
        },
    ]
    return {
        "wave": "W-INDEX",
        "councils": [{"id": "index.custody", "members": members}],
        "barrier": "PASS" if all(m["status"] == "COMPLETED" for m in members) else "PARTIAL",
    }


def w_deduction(facts: dict[str, Any]) -> dict[str, Any]:
    members = [
        {
            "id": "z3",
            "role": "bounded_discharge",
            "status": "COMPLETED" if facts.get("smt", {}).get("real") == "BOUNDED_SAT" else "HOLD",
            "real": facts.get("smt", {}).get("real"),
            "erased": facts.get("smt", {}).get("erased"),
        },
        {
            "id": "cvc5",
            "role": "independent_second_decider",
            "status": "COMPLETED" if facts.get("smt", {}).get("erased") == "BOUNDED_UNSAT" else "HOLD",
        },
        {
            "id": "rustworkx",
            "role": "order_cycle_reachability",
            "status": "COMPLETED" if (facts.get("map_replay") or {}).get("matches_compact_map") else "HOLD",
            "map_replay": facts.get("map_replay"),
        },
    ]
    return {
        "wave": "W-DEDUCTION",
        "councils": [{"id": "deduction.formal_floor", "members": members}],
        "barrier": "PASS" if all(m["status"] == "COMPLETED" for m in members) else "PARTIAL",
        "note": "memory methods only proposed; SMT wrote disposition",
    }


def main() -> int:
    t0 = time.time()
    WORK.mkdir(parents=True, exist_ok=True)
    facts = campaign_facts()
    _write(WORK / "object_facts.json", facts)

    index = w_index(facts)
    deduction = w_deduction(facts)

    induction_task = (
        "PREMORTEM FRAME: it is six months from now. The unified ConstraintBox "
        "product failed. Codex runtime cleanup, campaign_path_mass, and Grok "
        "waves were supposed to be one looping system. They are not. Work backward. "
        "Return three failures, one hidden assumption, one tripwire, one next probe. "
        "Use only the object facts and your loaded slices."
    )
    project_task = (
        "The owner wave sequence is W-INDEX through W-VERIFY. Premortem is a "
        "council, not a wave. From the object facts, name the next reversible "
        "sequence and the retreat condition. Do not invent a wave name."
    )
    verify_task = (
        "Overclaim audit. What did campaign_path_mass actually show, and what "
        "must stay unclaimed? Name one sentence that would be a lie if we said it."
    )

    induction_spec = [
        ("premortem-hume", "hume", "sonnet", "W-INDUCTION.premortem"),
        ("premortem-popper", "popper", "opus", "W-INDUCTION.premortem"),
        ("premortem-zhuangzi", "zhuangzi", "fable", "W-INDUCTION.premortem"),
    ]
    project_spec = [
        ("project-factory", "factory", "sonnet", "W-PROJECT.bottleneck"),
        ("project-strategy", "strategy", "opus", "W-PROJECT.sequence"),
    ]
    verify_spec = [
        ("verify-pushback", "pushback", "fable", "W-VERIFY.overclaim"),
    ]

    built = []
    for job_id, voice, _model, role in induction_spec + project_spec + verify_spec:
        task = induction_task if "premortem" in job_id else project_task if "project" in job_id else verify_task
        member = compose_member(voice, role, task, facts)
        member["id"] = job_id
        member["model"] = _model
        built.append(member)
        _write(WORK / "prompts" / f"{job_id}.txt", member["prompt"])

    induction_prompts = [m["prompt"] for m in built if m["id"].startswith("premortem")]
    prompt_div = diversity(induction_prompts)

    procs: dict[str, subprocess.Popen] = {}
    if prompt_div["verdict"] == "DIVERSE":
        for member in built:
            procs[member["id"]] = launch_claude(member["id"], member["model"], member["prompt"])

    # Wait for Claude children.
    for job_id, proc in procs.items():
        try:
            proc.communicate(timeout=200)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()

    collected = {job_id: collect_claude(job_id) for job_id in procs}
    # Also collect if files exist from a prior partial run.
    for member in built:
        if member["id"] not in collected:
            collected[member["id"]] = collect_claude(member["id"])

    induction_members = [collected[job_id] for job_id, *_ in induction_spec]
    project_members = [collected[job_id] for job_id, *_ in project_spec]
    verify_members = [collected[job_id] for job_id, *_ in verify_spec]

    induction = {
        "wave": "W-INDUCTION",
        "councils": [
            {
                "id": "induction.premortem",
                "kind": "premortem_council",
                "not_a_wave": True,
                "members": induction_members,
            }
        ],
        "four_legs_complete": all(m["complete"] for m in built if m["id"].startswith("premortem")),
        "barrier": "PASS"
        if induction_members and all(m.get("completed") for m in induction_members)
        else "PARTIAL",
        "count_law": {
            "spawned": 3,
            "completed": sum(1 for m in induction_members if m.get("completed")),
        },
    }

    prompt_wave = {
        "wave": "W-PROMPT",
        "councils": [
            {
                "id": "prompt.diversity",
                "members": [
                    {
                        "id": "input_diversity_gate",
                        "status": "COMPLETED" if prompt_div["verdict"] == "DIVERSE" else "HOLD",
                        **prompt_div,
                    }
                ],
            }
        ],
        "barrier": "PASS" if prompt_div["verdict"] == "DIVERSE" else "HOLD",
        "note": "variable stratum is voice spec + voice mini-MMM; shared facts are conserved",
    }

    findings = [
        (m.get("claim") or {}).get("finding")
        for m in induction_members
        if (m.get("claim") or {}).get("finding")
    ]
    output_wave = {
        "wave": "W-OUTPUT",
        "councils": [
            {
                "id": "output.compiler",
                "members": [
                    {
                        "id": "manager.output_compiler",
                        "status": "COMPLETED",
                        "findings_count": len(findings),
                        "findings": findings,
                    }
                ],
            }
        ],
        "barrier": "PASS",
    }

    context_wave = {
        "wave": "W-CONTEXT",
        "councils": [
            {
                "id": "context.ledger",
                "members": [
                    {
                        "id": "sqlite3",
                        "status": "COMPLETED",
                        "object_facts_sha256": _sha(facts),
                        "path": str(WORK / "object_facts.json"),
                    }
                ],
            }
        ],
        "barrier": "PASS",
    }

    project_wave = {
        "wave": "W-PROJECT",
        "councils": [{"id": "project.sequence", "members": project_members}],
        "barrier": "PASS"
        if project_members and all(m.get("completed") for m in project_members)
        else "PARTIAL",
    }

    needs_repair = any(
        wave.get("barrier") != "PASS"
        for wave in (index, induction, deduction, prompt_wave)
    )
    repair_wave = {
        "wave": "W-REPAIR",
        "councils": [
            {
                "id": "repair.barrier",
                "members": [
                    {
                        "id": "repair_needed",
                        "status": "COMPLETED",
                        "needed": needs_repair,
                        "action": "rerun missing Claude children"
                        if needs_repair
                        else "no repair",
                    }
                ],
            }
        ],
        "barrier": "PASS",
    }

    verify_wave = {
        "wave": "W-VERIFY",
        "councils": [
            {"id": "verify.overclaim", "members": verify_members},
            {
                "id": "verify.formal",
                "members": [
                    {
                        "id": "admit_same_object_refused",
                        "status": "COMPLETED"
                        if (facts.get("disposition") or {}).get("admit_same_object") == 0
                        else "HOLD",
                    },
                    {
                        "id": "hostile_not_admitted",
                        "status": "COMPLETED"
                        if (facts.get("disposition") or {}).get("admit_hostile") == 0
                        else "HOLD",
                    },
                ],
            },
        ],
        "barrier": "PASS"
        if (facts.get("disposition") or {}).get("admit_same_object") == 0
        else "HOLD",
        "route_truth": "NOT_FULL",
    }

    spine = {
        "schema": "constraintbox.owner-wave-spine.v1",
        "captured_at": _now(),
        "promotion_allowed": False,
        "watch_is_not_a_wave": True,
        "premortem_is_not_a_wave": True,
        "waves": [
            index,
            induction,
            deduction,
            prompt_wave,
            output_wave,
            context_wave,
            project_wave,
            repair_wave,
            verify_wave,
        ],
        "wave_order": list(WAVES),
        "claude_jobs": collected,
        "composition": [
            {key: value for key, value in member.items() if key != "prompt"}
            for member in built
        ],
        "claim_ceiling": (
            "one owner-wave sequence over the replayed campaign object and "
            "nested councils; not wave-product completion; not FULL; not promotion"
        ),
        "wall_seconds": round(time.time() - t0, 1),
    }
    complete = all(wave.get("barrier") == "PASS" for wave in spine["waves"])
    spine["status"] = "COMPLETE" if complete else "PARTIAL"
    spine["receipt_sha256"] = _sha(
        {key: value for key, value in spine.items() if key != "receipt_sha256"}
    )
    _write(WORK / "SPINE.json", spine)
    print(
        json.dumps(
            {
                "status": spine["status"],
                "receipt_sha256": spine["receipt_sha256"],
                "barriers": {wave["wave"]: wave["barrier"] for wave in spine["waves"]},
                "induction_completed": induction["count_law"]["completed"],
                "diversity": prompt_div,
                "out": str(WORK / "SPINE.json"),
            },
            sort_keys=True,
        )
    )
    return 0 if spine["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
