"""
Master Evidence Graph & Test Runner
=====================================
Unified runner for ALL SIM suites with dependency tracking.
Generates the evidence dependency graph showing how tokens
flow from axioms → derived → emergent.
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all SIM suites
from proto_ratchet_sim_runner import EvidenceToken


EVIDENCE_GRAPH = {
    # Layer 0: Root Axioms (no dependencies)
    "F01_FINITUDE": {"layer": 0, "deps": [], "file": "proto_directional_accumulator_sim_runner.py"},
    "N01_NONCOMMUTATION": {"layer": 0, "deps": [], "file": "proto_directional_accumulator_sim_runner.py"},
    
    # Layer 1: Derived Constraints (depend on axioms)
    "ACTION_PRECEDENCE": {"layer": 1, "deps": ["N01"], "file": "proto_directional_accumulator_sim_runner.py"},
    "VARIANCE_DIRECTION": {"layer": 1, "deps": ["F01", "N01"], "file": "proto_directional_accumulator_sim_runner.py"},
    
    # Layer 2: Process_Cycle Operator_Dynamics (depend on derived)
    "INVARIANT_TARGET_CONVERGENT_SUBSET": {"layer": 2, "deps": ["F01", "N01"], "file": "proto_directional_accumulator_sim_runner.py"},
    "LEFT_WEYL": {"layer": 2, "deps": ["N01", "ACTION_PRECEDENCE"], "file": "dual_weyl_spinor_process_cycle_sim.py"},
    "RIGHT_WEYL": {"layer": 2, "deps": ["N01", "ACTION_PRECEDENCE"], "file": "dual_weyl_spinor_process_cycle_sim.py"},
    "DUAL_LOOP_720": {"layer": 2, "deps": ["LEFT_WEYL", "RIGHT_WEYL"], "file": "dual_weyl_spinor_process_cycle_sim.py"},
    "CHIRAL_NON_STATE_REDUCTION": {"layer": 2, "deps": ["LEFT_WEYL", "RIGHT_WEYL"], "file": "dual_weyl_spinor_process_cycle_sim.py"},
    "FULL_8STAGE_v2": {"layer": 2, "deps": ["INVARIANT_TARGET_CONVERGENT_SUBSET", "DUAL_LOOP_720"], "file": "full_8stage_process_cycle_sim.py"},
    "FRACTAL_NESTING": {"layer": 2, "deps": ["FULL_8STAGE_v2"], "file": "full_8stage_process_cycle_sim.py"},
    
    # Layer 3: Math Foundations (depend on process_cycle)
    "NE_IS_TURING": {"layer": 3, "deps": ["F01", "N01"], "file": "math_foundations_sim.py"},
    "F01_DISCRETE": {"layer": 3, "deps": ["F01"], "file": "math_foundations_sim.py"},
    "N01_FORCES_COMPLEX": {"layer": 3, "deps": ["N01"], "file": "math_foundations_sim.py"},
    "CHIRALITY_FORCED": {"layer": 3, "deps": ["F01", "N01"], "file": "math_foundations_sim.py"},
    "PROCESS_CYCLE_SUPER_NE": {"layer": 3, "deps": ["NE_IS_TURING", "FULL_8STAGE_v2"], "file": "math_foundations_sim.py"},
    "GODEL_STALL": {"layer": 3, "deps": ["NE_IS_TURING"], "file": "godel_stall_sim.py"},
    "GODEL_RESOLUTION": {"layer": 3, "deps": ["GODEL_STALL", "PROCESS_CYCLE_SUPER_NE"], "file": "godel_stall_sim.py"},
    "STALL_DETECTION": {"layer": 3, "deps": ["GODEL_STALL"], "file": "godel_stall_sim.py"},
    
    # Layer 4: Operational Identity (depend on math)
    "OP_EQUIVALENCE": {"layer": 4, "deps": ["F01", "N01_FORCES_COMPLEX"], "file": "foundations_sim.py"},
    "ENTROPIC_MONISM": {"layer": 4, "deps": ["F01", "F01_DISCRETE"], "file": "foundations_sim.py"},
    "MATH_PHYSICS_FUSION": {"layer": 4, "deps": ["N01_FORCES_COMPLEX", "CHIRALITY_FORCED", "F01_DISCRETE"], "file": "foundations_sim.py"},
    "NO_PRIMITIVE_ID": {"layer": 4, "deps": ["OP_EQUIVALENCE"], "file": "foundations_sim.py"},
    "EQUIV_CLASSES": {"layer": 4, "deps": ["OP_EQUIVALENCE", "F01"], "file": "foundations_sim.py"},
    "REFINEMENT_PREORDER": {"layer": 4, "deps": ["EQUIV_CLASSES"], "file": "proof_cost_sim.py"},
    "SCALAR_POTENTIAL": {"layer": 4, "deps": ["ENTROPIC_MONISM"], "file": "proof_cost_sim.py"},
    "IDENTITY_COST_D2": {"layer": 4, "deps": ["NO_PRIMITIVE_ID", "F01"], "file": "proof_cost_sim.py"},
    
    # Layer 5: Arithmetic & State_Structure (depend on identity)
    "COUNTING": {"layer": 5, "deps": ["REFINEMENT_PREORDER"], "file": "arithmetic_gravity_sim.py"},
    "ADDITION": {"layer": 5, "deps": ["COUNTING", "ENTROPIC_MONISM"], "file": "arithmetic_gravity_sim.py"},
    "MULTIPLICATION": {"layer": 5, "deps": ["COUNTING", "F01"], "file": "arithmetic_gravity_sim.py"},
    "PRIMES": {"layer": 5, "deps": ["MULTIPLICATION"], "file": "arithmetic_gravity_sim.py"},
    "ENTROPIC_GRAVITY": {"layer": 5, "deps": ["SCALAR_POTENTIAL"], "file": "arithmetic_gravity_sim.py"},
}


def print_dependency_graph():
    """Print the evidence dependency tree layer by layer."""
    print(f"\n{'='*70}")
    print(f"EVIDENCE DEPENDENCY GRAPH")
    print(f"{'='*70}")
    
    for layer in range(6):
        tokens = {k: v for k, v in EVIDENCE_GRAPH.items() if v["layer"] == layer}
        if tokens:
            print(f"\n  Layer {layer}: {'ROOT AXIOMS' if layer == 0 else 'DERIVED' if layer == 1 else 'PROCESS_CYCLE' if layer == 2 else 'MATH' if layer == 3 else 'IDENTITY' if layer == 4 else 'ARITHMETIC'}")
            print(f"  {'─' * 60}")
            for name, info in tokens.items():
                deps = " ← " + ", ".join(info["deps"]) if info["deps"] else " (axiom)"
                print(f"    {name:25s}{deps}")
    
    # Print stats
    total = len(EVIDENCE_GRAPH)
    files = set(v["file"] for v in EVIDENCE_GRAPH.values())
    print(f"\n  Total tokens: {total}")
    print(f"  SIM files: {len(files)}")
    print(f"  Max depth: {max(v['layer'] for v in EVIDENCE_GRAPH.values())}")
    
    # Print layer counts
    for layer in range(6):
        count = sum(1 for v in EVIDENCE_GRAPH.values() if v["layer"] == layer)
        bar = "█" * count
        label = ["ROOT", "DERIVED", "PROCESS_CYCLE", "MATH", "IDENTITY", "ARITHMETIC"][layer]
        print(f"  L{layer} {label:12s}: {count:2d} {bar}")


def generate_mermaid():
    """Generate Mermaid diagram of the evidence graph."""
    lines = ["graph TD"]
    
    # Style by layer
    styles = {
        0: "fill:#4CAF50,color:#fff",  # green - axioms
        1: "fill:#2196F3,color:#fff",  # blue - derived
        2: "fill:#FF9800,color:#fff",  # orange - process_cycle
        3: "fill:#9C27B0,color:#fff",  # purple - math
        4: "fill:#E91E63,color:#fff",  # pink - identity
        5: "fill:#F44336,color:#fff",  # red - arithmetic
    }
    
    for name, info in EVIDENCE_GRAPH.items():
        short = name[:15]
        lines.append(f'    {name}["{short}"]')
        for dep in info["deps"]:
            if dep in EVIDENCE_GRAPH:
                lines.append(f'    {dep} --> {name}')
    
    # Apply styles
    for name, info in EVIDENCE_GRAPH.items():
        lines.append(f'    style {name} {styles[info["layer"]]}')
    
    return "\n".join(lines)


def save_graph():
    """Save the evidence graph as JSON."""
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    
    outpath = os.path.join(results_dir, "evidence_graph.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "total_tokens": len(EVIDENCE_GRAPH),
            "layers": {
                str(layer): [k for k, v in EVIDENCE_GRAPH.items() if v["layer"] == layer]
                for layer in range(6)
            },
            "graph": EVIDENCE_GRAPH,
        }, f, indent=2)
    print(f"\n  Graph saved to: {outpath}")
    
    mermaid_path = os.path.join(results_dir, "evidence_graph.mermaid")
    with open(mermaid_path, "w") as f:
        f.write(generate_mermaid())
    print(f"  Mermaid saved to: {mermaid_path}")


if __name__ == "__main__":
    print_dependency_graph()
    save_graph()
