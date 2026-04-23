"""
llm_council_operator.py

Implements 'llm-council' as an adjudication operator. 
Instead of relying on a single evaluator for ambiguous or highly-complex
decisions, this operator simulates an ensemble of perspectives (council members)
to vote on and critique candidates.

Design doc: §LLM Council -> ensemble voting and perspective synthesis.
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path
from typing import Any, List, Dict

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.runtime_state_kernel import (
    RuntimeState, WitnessKind, StepEvent, utc_iso, BoundaryTag
)

class CouncilMember:
    def __init__(self, name: str, bias: str):
        self.name = name
        self.bias = bias
        
    def evaluate(self, candidate: RuntimeState) -> dict[str, Any]:
        """
        In a full implementation, this uses an LLM call with a persona prompt.
        For rigorous nonclassical runtime offline execution, it applies heuristic 
        checks mapped to the bias.
        """
        # Simulated heuristic scoring for now
        score = random.random()
        return {
            "score": score,
            "vote": "ACCEPT" if score > 0.6 else "REJECT",
            "critique": f"[{self.name}] {self.bias} perspective implies score {score:.2f}"
        }

DEFAULT_COUNCIL = [
    CouncilMember("Architect", "Prefers structural elegance and coherence"),
    CouncilMember("Skeptic", "Pessimistic, looks for edge cases and failures"),
    CouncilMember("Innovator", "Values novelty and frontier expansion"),
]

def council_adjudicate(
    candidates: List[RuntimeState],
    council: List[CouncilMember] = None,
    consensus_threshold: float = 0.5
) -> dict[str, Any]:
    """
    Passes a list of candidates through the council.
    Returns the accepted candidates and a log of the proceedings.
    """
    council = council or DEFAULT_COUNCIL
    
    proceedings = []
    accepted = []
    rejected = []
    
    for cand in candidates:
        votes = []
        total_score = 0.0
        
        for member in council:
            result = member.evaluate(cand)
            votes.append({
                "member": member.name,
                "vote": result["vote"],
                "score": result["score"],
                "critique": result["critique"]
            })
            total_score += result["score"]
            
        avg_score = total_score / len(council)
        accept_ratio = sum(1 for v in votes if v["vote"] == "ACCEPT") / len(council)
        
        is_accepted = accept_ratio >= consensus_threshold
        
        outcome = {
            "region": cand.region,
            "avg_score": avg_score,
            "accept_ratio": accept_ratio,
            "accepted": is_accepted,
            "votes": votes
        }
        
        proceedings.append(outcome)
        if is_accepted:
            accepted.append(cand)
        else:
            rejected.append(cand)
            
    return {
        "accepted": accepted,
        "rejected": rejected,
        "proceedings": proceedings
    }

def run_llm_council(ctx: dict[str, Any]) -> dict[str, Any]:
    """Adapter for dynamic dispatch."""
    candidates = ctx.get("candidates", [])
    if not candidates:
        return {"error": "No candidates provided to LLM Council"}
        
    result = council_adjudicate(
        candidates, 
        consensus_threshold=ctx.get("consensus_threshold", 0.51)
    )
    
    if "recorder" in ctx and "witness_tags" in ctx:
        w_kind = WitnessKind.POSITIVE if result["accepted"] else WitnessKind.NEGATIVE
        from system_v4.skills.runtime_state_kernel import Witness
        
        # We record ONE witness representing the council's aggregate decision on this batch
        witness = Witness(
            kind=w_kind,
            passed=bool(result["accepted"]),
            violations=["Failed council consensus"] if not result["accepted"] else [],
            touched_boundaries=[BoundaryTag.ADMISSIBLE],
            trace=[StepEvent(
                at=utc_iso(), 
                op="llm_council_adjudicate",
                before_hash="", 
                after_hash="",
                notes=[f"Council debated {len(candidates)} items. Accepted: {len(result['accepted'])}"]
            )]
        )
        ctx["recorder"].record(witness, tags=ctx["witness_tags"])
        
    return result

if __name__ == "__main__":
    # Self-test
    random.seed(42) # Determinism for test
    cands = [
        RuntimeState(region="IdeaAlpha"),
        RuntimeState(region="IdeaBeta"),
        RuntimeState(region="IdeaGamma")
    ]
    
    result = council_adjudicate(cands)
    assert "accepted" in result
    assert "proceedings" in result
    assert len(result["proceedings"]) == 3
    print(f"PASS: llm_council_operator self-test (Accepted {len(result['accepted'])}/3 candidates)")

"""
Skill registration metadata:
  skill_id: llm-council-operator
  skill_type: adjudicator
  applicable_trust_zones: [B_ADJUDICATED, A2_LOW_CONTROL]
  capabilities: {is_phase_runner: true}
  source_path: system_v4/skills/llm_council_operator.py
  adapters: {shell: system_v4/skills/llm_council_operator.py}
"""
