"""
autoresearch_operator.py

Implements 'autoresearch' as a first-class skill, derived from the Karpathy 
design philosophy. Rather than just being an implicit loop, this operator
explicitly explores a bounded search space (the 'truth-space') of possible
patterns, generating hypotheses and evaluating them to find stable motifs.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Callable, List

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.runtime_state_kernel import (
    RuntimeState, BoundaryTag, WitnessKind, StepEvent, utc_iso,
)
from system_v4.skills.bounded_improve_operator import bounded_improve

def autoresearch_sweep(
    seed_state: RuntimeState,
    hypothesis_generator: Callable[[RuntimeState], List[RuntimeState]],
    evaluator: Callable[[RuntimeState], float],
    max_breadth: int = 5,
    max_depth: int = 3,
) -> tuple[RuntimeState, dict[str, Any]]:
    """
    Conducts an automated research sweep.
    
    Generates multiple hypotheses from the seed state, evaluates them all, 
    keeps the best, and then recursively expands up to max_depth.
    """
    best_state = seed_state
    best_score = evaluator(seed_state)
    
    trace_log = []
    
    current_frontier = [seed_state]
    
    for depth in range(max_depth):
        next_frontier = []
        for state in current_frontier:
            # Generate new hypotheses
            try:
                hypotheses = hypothesis_generator(state)[:max_breadth]
            except Exception as e:
                trace_log.append(f"Depth {depth}: Generator exception: {e}")
                continue
                
            for hyp in hypotheses:
                score = evaluator(hyp)
                trace_log.append(f"Depth {depth}: Evaluated {hyp.region} -> {score:.2f}")
                next_frontier.append((score, hyp))
                
                if score > best_score:
                    best_score = score
                    best_state = hyp
                    trace_log.append(f"  -> NEW BEST: {score:.2f}")
                    
        if not next_frontier:
            break
            
        # Select top candidates for the next layer of expansion
        next_frontier.sort(key=lambda x: x[0], reverse=True)
        current_frontier = [h for s, h in next_frontier[:max_breadth]]
        
    return best_state, {
        "best_score": best_score,
        "max_depth_reached": depth,
        "trace": trace_log,
        "improved": best_score > evaluator(seed_state)
    }

def run_autoresearch(ctx: dict[str, Any]) -> dict[str, Any]:
    """Adapter for dynamic dispatch."""
    state = ctx.get("state")
    generator = ctx.get("generator")
    evaluator = ctx.get("evaluator")
    
    if not state or not generator or not evaluator:
        return {"error": "Missing required autoresearch arguments (state, generator, evaluator)"}
        
    best_state, stats = autoresearch_sweep(
        state, 
        generator, 
        evaluator,
        max_breadth=ctx.get("max_breadth", 3),
        max_depth=ctx.get("max_depth", 3)
    )
    
    if "recorder" in ctx and "witness_tags" in ctx:
        w_kind = WitnessKind.POSITIVE if stats["improved"] else WitnessKind.NEGATIVE
        from system_v4.skills.runtime_state_kernel import Witness
        witness = Witness(
            kind=w_kind,
            passed=stats["improved"],
            violations=[] if stats["improved"] else ["No better hypothesis found in search space"],
            touched_boundaries=[BoundaryTag.FRONTIER],
            trace=[StepEvent(
                at=utc_iso(), 
                op="autoresearch",
                before_hash=state.hash(), 
                after_hash=best_state.hash(),
                notes=stats["trace"][-5:]  # Log last 5 steps to avoid bloat
            )]
        )
        ctx["recorder"].record(witness, tags=ctx["witness_tags"])
        
    return {
        "best_state": best_state,
        "stats": stats
    }

if __name__ == "__main__":
    # Self-test
    seed = RuntimeState(region="research_seed", dof={"val": 0.5})
    
    def dummy_gen(s: RuntimeState) -> List[RuntimeState]:
        v = s.dof["val"]
        return [
            RuntimeState(region=f"hyp_{v+0.1:.2f}", dof={"val": v + 0.1}),
            RuntimeState(region=f"hyp_{v-0.1:.2f}", dof={"val": v - 0.1})
        ]
        
    best, stats = autoresearch_sweep(
        seed, 
        dummy_gen,
        lambda s: s.dof["val"] if s.dof["val"] < 0.8 else 0.0, # local maxima
        max_depth=5
    )
    
    assert stats["improved"]
    assert "hyp_0.80" in best.region
    print(f"PASS: autoresearch_operator self-test (optimal value found: {best.dof['val']:.2f})")

"""
Skill registration metadata:
  skill_id: autoresearch-operator
  skill_type: agent
  applicable_trust_zones: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
  capabilities: {is_phase_runner: true}
  source_path: system_v4/skills/autoresearch_operator.py
  adapters: {shell: system_v4/skills/autoresearch_operator.py}
"""
