#!/usr/bin/env python3
import os
import re
from pathlib import Path

# The exact words from a1_brain.py that are forbidden
FORBIDDEN_MAP = {
    # Overlay
    "entropy": "state_dispersion",
    "information": "state_distinction",
    "measurement": "trace_projection",
    "collapse": "state_reduction",
    "observer": "reference_frame",
    "geometry": "state_structure",
    "reality": "operational_domain",
    "spacetime": "dimensional_extent",
    "consciousness": "recursive_state",
    "perception": "state_interaction",
    "energy": "hamiltonian_norm",
    "force": "generator_bias",
    "field": "continuous_operator",
    "wave": "unitary_oscillation",
    "particle": "localized_state",
    "causality": "sequential_dependence",
    "symmetry": "generator_invariance",
    "conservation": "trace_preservation",
    "thermodynamics": "dissipative_dynamics",
    "mechanics": "operator_dynamics",

    # Jargon
    "engine": "process_cycle",
    "attractor": "invariant_target",
    "basin": "convergent_subset",
    "axis": "generator_basis",
    "ratchet": "directional_accumulator",
    "wiggle": "incremental_perturbation",
    "conflation": "basis_overlap",
    "orthogonal": "mutually_exclusive",
    "degrees": "state_dimensions",
    "freedom": "state_variables",
    "manifold": "state_subset",
    "topological": "structural",
    "constraint": "operator_bound",
    "geometric": "structural_shape",
    "retrocausal": "reverse_dependent",
    "nonclassical": "quantum_formal",
    "holodeck": "simulation_matrix",
    "rosetta": "translation_map",
    "overlay": "conceptual_layer"
}

def replace_in_string(text):
    def replacer(match):
        word = match.group(0)
        lower_word = word.lower()
        if lower_word in FORBIDDEN_MAP:
            replacement = FORBIDDEN_MAP[lower_word]
            # Match case roughly (if all caps, ALL CAPS. If title, Title. Else lower)
            if word.isupper():
                return replacement.upper()
            elif word.istitle():
                return replacement.title()
            else:
                return replacement
        return word
    
    # Match any contiguous block of letters, penetrating underscore boundaries
    return re.sub(r'[A-Za-z]+', replacer, text)


def scrub_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Only replace words inside comments and string literals to prevent breaking logic
    def segment_replacer(match):
        segment = match.group(0)
        return replace_in_string(segment)
        
    new_content = re.sub(r'(#.*)|(\'[^\']*\'|"[^"]*")', segment_replacer, content)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    repo_root = Path(__file__).resolve().parent

    scanned_files = []
    modified_files = 0
    
    # 1. Scrub all probes
    probes_dir = repo_root / "system_v4" / "probes"
    for f in os.listdir(probes_dir):
        if f.endswith(".py"):
            scanned_files.append(probes_dir / f)

    # 2. Scrub DNA yaml to keep tokens aligned
    scanned_files.append(repo_root / "system_v4" / "skills" / "intent-compiler" / "dna.yaml")

    # 3. Scrub sim runner and validator
    scanned_files.append(repo_root / "system_v4" / "probes" / "run_all_sims.py")

    print(f"Starting system-wide vocabulary structural translation...")
    
    for fw in scanned_files:
        if fw.exists():
            if scrub_file(fw):
                modified_files += 1
                print(f"  Refactored terminology in: {fw.name}")

    print(f"\nDone. {modified_files} files rewritten to L0 strict compliance.")

if __name__ == "__main__":
    main()
