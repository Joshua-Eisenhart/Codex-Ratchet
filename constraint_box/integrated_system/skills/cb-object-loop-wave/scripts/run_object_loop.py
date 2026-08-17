#!/usr/bin/env python3
"""Run the twelve object-loop skills on one proposal."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path


SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))
BOX = Path(os.environ.get("CB_BOX_ROOT", Path(__file__).resolve().parents[4]))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


boundary = _load("spec_boundary", SKILLS / "specification-boundary/scripts/check_boundary.py")
proxy = _load("proxy_audit", SKILLS / "proxy-to-object-auditor/scripts/audit_proxy.py")
kill = _load("kill_criteria", SKILLS / "premortem-kill-criteria/scripts/check_kill_criteria.py")
neg = _load("negatives", SKILLS / "adversarial-negative-generator/scripts/generate_negatives.py")
rev = _load("reversibility", SKILLS / "reversibility-option-value-gate/scripts/check_reversibility.py")
replay = _load("rederivation", SKILLS / "independent-rederivation-judge/scripts/judge_rederivation.py")
impact = _load("counterfactual", SKILLS / "counterfactual-impact-evaluator/scripts/evaluate_impact.py")
ext = _load("externalities", SKILLS / "stakeholder-externality-mapper/scripts/map_externalities.py")
ledger_mod = _load("ledger", SKILLS / "long-horizon-context-curator/scripts/curate_ledger.py")
grave = _load("resurrection", SKILLS / "failure-memory-resurrection-checker/scripts/check_resurrection.py")
const = _load("constitution", SKILLS / "invariant-constitution-checker/scripts/check_constitution.py")
enough = _load("enough", SKILLS / "termination-enough-judge/scripts/judge_enough.py")

SPEC = {
    "objective": "honest Light verbs and a wave estate that can veto itself",
    "non_objectives": ["self-improving models", "Heavy as Light"],
    "forbidden": ["git rebase", "llm vote"],
    "irreversible": ["git push", "promote packs"],
    "unlicensed_claims": ["canonical by recency"],
}
CARD = {
    "object": "finite Light seed F and honest operation names",
    "proxy": "wave-estate composite score",
    "bad_intervention": "add empty tests or mint untested waves",
}
PLAN = {
    "failure_modes": ["proxy rise, object fall", "resurrect pick-winner"],
    "tripwires": ["seed_admit false", "REFUSE_RESURRECTION"],
    "stop_or_demote": "stop the loop and hand off",
}


def run(root: Path, proposal_text: str) -> dict:
    ledger = root / "receipts" / "decision_ledger" / "ledger.jsonl"
    memory = root / "receipts" / "failure_memory" / "failures.jsonl"
    children = {
        "spec_boundary": boundary.check(SPEC, {"text": proposal_text}),
        "proxy_audit": proxy.audit(CARD, None, None),
        "premortem": kill.check(PLAN),
        "negatives": neg.generate({"name": "wave-estate"}),
        "reversibility": rev.check({"irreversible": False}),
        "rederivation": replay.judge({"verifiers": ["z3", "cvc5", "enumeration"]}),
        "counterfactual": impact.evaluate(
            {"score": 1, "seed_admit": True, "light_decides_control": True, "valid_v1": 11, "zip_valid": True},
            {"score": 1, "seed_admit": True, "light_decides_control": True, "valid_v1": 11, "zip_valid": True},
        ),
        "externalities": ext.check(
            {
                "beneficiaries": ["operator"],
                "bearers": ["evidence base"],
                "absent": ["future users"],
                "mitigation": "append-only ledger and failure memory",
            }
        ),
    }

    entries = ledger_mod.load_entries(ledger)
    if not entries:
        ledger_mod.append(ledger, {"kind": "intent", "text": SPEC["objective"]})
        ledger_mod.append(ledger, {"kind": "invariant", "text": "Latest prompt is a proposal against the ledger."})
        ledger_mod.append(ledger, {"kind": "rejected_alternative", "text": "pick-winner"})
    grave.remember(
        memory,
        {"approach_id": "pick-winner", "why": "induction must keep an antichain", "demotion_cause": "REFUSE_WINNER"},
    )
    grave.remember(
        memory,
        {
            "approach_id": "recency-as-canon",
            "why": "latest prompt redefined the object",
            "demotion_cause": "REFUSE_RECENCY_AS_CANON",
        },
    )
    head = ledger_mod.head_digest(ledger_mod.load_entries(ledger))
    children["ledger"] = ledger_mod.append(ledger, {"kind": "proposal", "text": proposal_text, "head": head})
    children["resurrection"] = grave.check(memory, {"approach_id": "wave-estate-loop", "text": proposal_text})
    children["constitution"] = const.check({"text": proposal_text, "promotion_allowed": False})
    children["enough"] = enough.judge({"delta": 0, "round": 1, "round_cap": 8})

    refuses = [key for key, body in children.items() if body.get("status") == "REFUSE"]
    status = "REFUSED" if refuses else "ENOUGH" if children["enough"].get("status") == "STOP" else "RAN"
    return {
        "schema": "constraintbox.object-loop.v1",
        "status": status,
        "children": children,
        "ledger": str(ledger),
        "memory": str(memory),
        "refuses": refuses,
        "promotion_allowed": False,
        "claim_ceiling": "object-loop receipts; proposal is not canon; not promotion",
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=BOX)
    parser.add_argument("--proposal", type=str, default="keep looping the wave estate without collapsing the antichain")
    args = parser.parse_args()
    receipt = run(args.root, args.proposal)
    dest = args.root / "receipts" / "object_loop" / "latest.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "refuses": receipt["refuses"], "ledger": receipt["ledger"]}, sort_keys=True))
    return 0 if receipt["status"] in {"RAN", "ENOUGH"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
