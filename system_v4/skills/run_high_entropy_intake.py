"""
A2 Graph Refinery — High-Entropy Doc Intake Runner

Processes the 4 high-entropy test-fuel documents through the A2-3 intake
layer, extracts core concepts from each, registers cross-doc contradictions,
promotes refined concepts to A2-2, and admits kernel candidates to A2-1.

Usage:
    cd /Users/joshuaeisenhart/Desktop/Codex Ratchet
    python -m system_v4.skills.run_high_entropy_intake
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root on path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_graph_refinery import (
    A2GraphRefinery,
    ExtractionMode,
)

WORKSPACE = str(REPO_ROOT)

# ── Source Documents ──────────────────────────────────────────────────

HIGH_ENTROPY_DIR = REPO_ROOT / "core_docs" / "a2_feed_high entropy doc"

DOCS = {
    "leviathan": HIGH_ENTROPY_DIR / "Leviathan v3.2 word.txt",
    "holodeck":  HIGH_ENTROPY_DIR / "holodeck docs.md",
    "toe_chat":  HIGH_ENTROPY_DIR / "x grok chat TOE.txt",
    "unified_physics": HIGH_ENTROPY_DIR / "grok unified phuysics nov 29th.txt",
}


# ── Concept Extraction (manual, curated per-doc) ─────────────────────
# Each document gets its own concept set.  These are the high-signal
# concepts a future LLM extraction pass would produce; for this test
# run we hardcode them to exercise the full pipeline.

LEVIATHAN_CONCEPTS = [
    {
        "name": "Delegated Proxy Voting",
        "description": "Multi-layered hierarchical governance where voting power flows upward to a single apex leader, with veto powers retained at the base. Rejects committee/equity governance.",
        "tags": ["governance", "hierarchy", "leviathan", "social_contract"],
        "source_line_range": "250-405",
    },
    {
        "name": "Recursive Scientific Methodology",
        "description": "Bidirectional scientific process combining inductive and deductive approaches with observers inside the experimental frame. Feedback loops refine hypotheses. Embeds nominalism.",
        "tags": ["science", "methodology", "empiricism", "recursion"],
        "source_line_range": "508-515",
    },
    {
        "name": "Individual Development Mirror (Ugly Mirror)",
        "description": "AI-driven self-assessment tracking Physical/Mental-Emotional/Status Attractiveness (1-10 each). Drives P2P training and SBC currency. Private reflection engine.",
        "tags": ["mirror", "self_assessment", "SBC", "attractiveness"],
        "source_line_range": "581-683",
    },
    {
        "name": "Organizational Development Mirror",
        "description": "Decentralized platform tracking Development Capacity, System Openness, Trust Attractiveness. Uses CRC currency and Group Reflection Engine.",
        "tags": ["mirror", "organization", "CRC", "cooperative"],
        "source_line_range": "686-785",
    },
    {
        "name": "Triple Currency System (SBC/CRC/ECC)",
        "description": "Three-tier cryptocurrency: SBC for service barter, CRC for cooperative resources, ECC for ecosystem contributions. Each tied to a mirror layer.",
        "tags": ["currency", "SBC", "CRC", "ECC", "economics"],
        "source_line_range": "43-47",
    },
    {
        "name": "Paladin System with Multi-Classing",
        "description": "Four specializations: Science, Guardian, Civic, Engineering. Individuals can multi-class for combined impact. Validated by P2P audits.",
        "tags": ["paladins", "specialization", "multi_class", "community"],
        "source_line_range": "532-539",
    },
    {
        "name": "Cooperative Community Layer",
        "description": "Network of voluntary community groups for social cohesion, family support, demographic sustainability. Distinct from profit-driven coops.",
        "tags": ["cooperative", "community", "family", "demographics"],
        "source_line_range": "516-523",
    },
    {
        "name": "Leviathan OS (Semantic Computing Platform)",
        "description": "LLM-based platform with semantic computing. Natural language interface, intent understanding, self-organizing systems. Contextual and sovereign.",
        "tags": ["OS", "semantic_computing", "AI", "platform"],
        "source_line_range": "183-246",
    },
]

HOLODECK_CONCEPTS = [
    {
        "name": "Projective Holodeck Perception Model",
        "description": "Perception as active prediction: project first, then error-correct against sensory input. Based on predictive coding + allostasis. System projects internal model onto world, compares, hashes confirmed states.",
        "tags": ["perception", "predictive_coding", "allostasis", "holodeck"],
        "source_line_range": "1-60",
    },
    {
        "name": "Semantic Hash Memory Architecture",
        "description": "Memories stored as compressed semantic hashes, confirmed by matching generated predictions. Contextual triggers boot recall chains. Stacked self-referencing hashes in a vector sea.",
        "tags": ["memory", "hash", "compression", "recall", "vector"],
        "source_line_range": "34-46",
    },
    {
        "name": "NetHack-Like Simulation Recall Space",
        "description": "ASCII/text-based procedural sim worlds that embed semantic hashes as game entities. Persistent compressible maps serve as 'recall spaces' for chain memory. Solves Genie 3's forgetting problem.",
        "tags": ["simulation", "ASCII", "recall_space", "persistence", "compression"],
        "source_line_range": "166-169",
    },
    {
        "name": "Comic Vision Reduction",
        "description": "Complex perceptions reduced to comic-like storyboards/games for storage and recall. Ideas become playable games or visual sequences. Entropy reduction as singularity bubbling.",
        "tags": ["comic_vision", "compression", "storyboard", "approximation"],
        "source_line_range": "46",
    },
    {
        "name": "Embodied Consciousness Loop (Hardware Holodeck)",
        "description": "Projector + camera system applying predictive perception to physical surfaces. Project prediction, sense actual, error-correct, loop. Calibrate then control surface as display.",
        "tags": ["embodied", "hardware", "projector", "perception_loop"],
        "source_line_range": "513-620",
    },
    {
        "name": "Active Inference Projector (pyMDP)",
        "description": "Active inference agent using free energy minimization. Maps hidden states to observations. Plans actions to minimize expected free energy. Uses pyMDP library.",
        "tags": ["active_inference", "free_energy", "pyMDP", "prediction"],
        "source_line_range": "621-664",
    },
]

TOE_CHAT_CONCEPTS = [
    {
        "name": "Entropy as Spacetime (Axiom)",
        "description": "Spacetime IS entropy. Dark energy = positive entropy (expansion). Dark matter = negative entropy (preservation). Both are properties of spacetime, not separate particles.",
        "tags": ["physics", "entropy", "spacetime", "axiom", "dark_energy", "dark_matter"],
        "source_line_range": "22-25",
    },
    {
        "name": "Retrocausal Multiverse (Converging Futures)",
        "description": "Many possible futures create the present — NOT branching. Causality converges, not diverges. Consciousness is the only causal force. A retrocausal future entity could create reality from finite possibilities.",
        "tags": ["physics", "retrocausality", "multiverse", "convergence", "consciousness"],
        "source_line_range": "38-55",
    },
    {
        "name": "Gravity as FTL Possibility Push",
        "description": "Gravity = all of spacetime pushing onto us. Spacetime contains all future possibilities. Inverse square law = square of possibilities converging. FTL 'signal' with no information.",
        "tags": ["physics", "gravity", "FTL", "possibilities", "inverse_square"],
        "source_line_range": "66",
    },
    {
        "name": "Dark Matter as Micro-Gravitational Waves",
        "description": "Dark matter = micro-GW structures forming 2D loops from negative entropy. Clumps via interference. In Big Bangs, some forms into 3D matter shapes. DM is the base building block of matter, not a mystery particle.",
        "tags": ["physics", "dark_matter", "gravitational_waves", "loops", "matter"],
        "source_line_range": "74-81",
    },
    {
        "name": "White Noise Hypersphere Origin",
        "description": "Universe begins as pure random white noise on hypersphere surface. No pattern or information between frames. Time = connection/sequence between frames. First pattern was entangled expanding field.",
        "tags": ["physics", "cosmology", "white_noise", "hypersphere", "origin"],
        "source_line_range": "30",
    },
]

UNIFIED_PHYSICS_CONCEPTS = [
    {
        "name": "Eisenhart Unified Physics Module",
        "description": "Reality begins as pure randomness on hypersphere. One stuff: matter/DM/DE/gravity/light are phase-states of same entropic field. One force: gravity and dark energy are same retrocausal syncing in different density regimes.",
        "tags": ["physics", "unified_field", "entropy", "axiom", "canonical"],
        "source_line_range": "1-41",
    },
    {
        "name": "Sequential Bubble Multiverse Cosmology",
        "description": "Entropy creates energy → supervoids as entangled bubbles → white-hole bursts → daughter universes. CMB smoothness from parent vacuum uniformity. No inflation needed.",
        "tags": ["physics", "cosmology", "bubbles", "supervoid", "CMB"],
        "source_line_range": "12-15",
    },
    {
        "name": "Win/Lose Strategy Game Theory (8-State Model)",
        "description": "4 strategies (Win-Win/Win-Lose/Lose-Lose/Lose-Win) each with 2 sub-strategies (T-first competitive vs F-second cooperative). Maps to entropy qubits, Bloch sphere, and quaternion operators.",
        "tags": ["psychology", "game_theory", "entropy_qubit", "strategy", "topology"],
        "source_line_range": "44-108",
    },
    {
        "name": "Four Judging Operators (Te/Ti/Fe/Fi)",
        "description": "Te=Gradient Descent, Ti=Eigenvalue Solver, Fe=Phase Locking, Fi=Resonant Standing Wave. First sub-strategy (T) = competitive/linear/pain-seeking. Second (F) = cooperative/circular/pleasure-seeking.",
        "tags": ["operators", "gradient_descent", "eigenvalue", "phase_locking", "standing_wave"],
        "source_line_range": "189-226",
    },
    {
        "name": "S3 + Hopf + Weyl Topology (Chiral Types)",
        "description": "S³ with Hopf fibration and Weyl spinors is the airtight geometry. Type 1 = left-handed Weyl, Type 2 = right-handed. Gives true global chirality. Klein bottle only as visualization aid.",
        "tags": ["topology", "S3", "Hopf", "Weyl", "chirality", "spinor"],
        "source_line_range": "150-188",
    },
    {
        "name": "720° Spinor Double Cover (16-State Model)",
        "description": "720° identity creates chiral Type 1/Type 2 as opposite chirality fibers. 4 states × 2 types × 2 amplitudes (big/small) = 16 total states. MAX loop = high-flow/low-voltage. MIN loop = high-pressure/high-voltage.",
        "tags": ["spinor", "chirality", "16_state", "amplitude", "max_min_loop"],
        "source_line_range": "107-108",
    },
]


# ── Cross-Document Contradictions / Tensions ─────────────────────────
# These are real tensions between the docs that the refinery should
# preserve as explicit CONTRADICTS edges (not smooth over).

CROSS_DOC_CONTRADICTIONS = [
    # Holodeck says memory is hash-based confirmation;
    # Unified Physics says all info is preserved via entropy.
    # Tension: hash is lossy, entropy preservation implies lossless.
    ("Semantic Hash Memory Architecture", "Eisenhart Unified Physics Module",
     "Hash compression is inherently lossy, but the physics axiom demands all information is preserved via entropy. Tension: how can hash-compressed memory satisfy lossless entropy preservation?"),

    # TOE says consciousness is the only causal force;
    # Leviathan says merit/empiricism rules, not feelings.
    # Tension: causal primacy of consciousness vs empirical primacy.
    ("Retrocausal Multiverse (Converging Futures)", "Recursive Scientific Methodology",
     "TOE places consciousness as the sole causal force (retrocausal), but Leviathan's scientific methodology demands empirical/measurable results over subjective experience. Tension: whose primacy?"),

    # Holodeck active inference uses free energy minimization;
    # Unified Physics uses positive entropy (expansion) as creative force.
    # Tension: minimize free energy vs maximize entropy.
    ("Active Inference Projector (pyMDP)", "Eisenhart Unified Physics Module",
     "Active inference minimizes free energy (prediction error), but the physics model treats positive entropy (expansion/creation) as the generative axiom. Tension: minimize vs maximize entropy as creative principle."),
]


def main():
    print("=" * 60)
    print("A2 GRAPH REFINERY — High-Entropy Doc Intake")
    print("=" * 60)

    refinery = A2GraphRefinery(WORKSPACE)

    # ── Phase 1: A2-3 Intake (one batch per document) ────────────────
    all_a2_3_batch_ids = []
    doc_concept_map: dict[str, list[str]] = {}  # doc_key → list of concept node IDs

    intake_jobs = [
        ("leviathan",       ExtractionMode.SOURCE_MAP,     LEVIATHAN_CONCEPTS),
        ("holodeck",        ExtractionMode.ENGINE_PATTERN,  HOLODECK_CONCEPTS),
        ("toe_chat",        ExtractionMode.QIT_BRIDGE,      TOE_CHAT_CONCEPTS),
        ("unified_physics", ExtractionMode.MATH_CLASS,      UNIFIED_PHYSICS_CONCEPTS),
    ]

    for doc_key, mode, concepts in intake_jobs:
        doc_path = str(DOCS[doc_key])
        batch_id = f"HE_INTAKE_{doc_key.upper()}_001"
        print(f"\n▸ Ingesting {doc_key} ({len(concepts)} concepts) into A2-3...")

        batch = refinery.ingest_document(
            doc_path=doc_path,
            extraction_mode=mode,
            batch_id=batch_id,
            concepts=concepts,
        )
        all_a2_3_batch_ids.append(batch.batch_id)
        # Store node IDs (skip the source doc node at [0])
        doc_concept_map[doc_key] = batch.node_ids[1:]

        print(f"  ✓ Batch {batch.batch_id}: {len(batch.node_ids)} nodes, {len(batch.edge_ids)} edges")

    # ── Phase 2: A2-2 Mid-Refinement (cross-doc synthesis) ───────────
    print(f"\n{'─' * 60}")
    print("▸ Promoting cross-doc refined concepts to A2-2...")

    # Build refined concepts by grouping related A2-3 nodes
    refined_concepts = [
        {
            "name": "Entropy-First Unified Framework",
            "description": "Synthesis: Spacetime=entropy (TOE axiom), matter/DM/DE as phase-states, with recursive scientific validation (Leviathan). The generative engine is positive entropy; preservation is negative entropy.",
            "source_node_ids": [
                doc_concept_map["toe_chat"][0],        # Entropy as Spacetime
                doc_concept_map["unified_physics"][0],  # Eisenhart Unified Physics
                doc_concept_map["leviathan"][1],        # Recursive Scientific Methodology
            ],
        },
        {
            "name": "Perception as Predictive Projection",
            "description": "Synthesis: Holodeck model (project → sense → error-correct → hash) maps to active inference (minimize free energy) and to the physics model (retrocausal futures shape present perception).",
            "source_node_ids": [
                doc_concept_map["holodeck"][0],         # Projective Holodeck Model
                doc_concept_map["holodeck"][5],          # Active Inference Projector
                doc_concept_map["toe_chat"][1],          # Retrocausal Multiverse
            ],
        },
        {
            "name": "Chiral Game Theory Operators",
            "description": "Synthesis: 8-state win/lose model with Te/Ti/Fe/Fi operators maps to S3+Hopf+Weyl topology. Operators are entropy transformers on the manifold. 16-state model via spinor double cover.",
            "source_node_ids": [
                doc_concept_map["unified_physics"][2],  # Win/Lose Strategy
                doc_concept_map["unified_physics"][3],  # Four Operators
                doc_concept_map["unified_physics"][4],  # S3+Hopf+Weyl
                doc_concept_map["unified_physics"][5],  # 720° Spinor
            ],
        },
        {
            "name": "Mirror-Driven Self-Governance Stack",
            "description": "Synthesis: Three-tier mirror system (Individual/Organizational/Ecosystem) drives three-tier currency (SBC/CRC/ECC) under delegated proxy voting governance. Community layer for demographics/family.",
            "source_node_ids": [
                doc_concept_map["leviathan"][0],        # Delegated Proxy Voting
                doc_concept_map["leviathan"][2],        # Individual Mirror
                doc_concept_map["leviathan"][3],        # Organizational Mirror
                doc_concept_map["leviathan"][4],        # Triple Currency
                doc_concept_map["leviathan"][6],        # Cooperative Community
            ],
        },
        {
            "name": "Hash-Embedded Simulation Memory",
            "description": "Synthesis: Semantic hashes embedded in NetHack-like ASCII sim worlds as recall spaces. Comic vision reduces perception to playable approximations. Connects to Letta/MemGPT for stateful memory.",
            "source_node_ids": [
                doc_concept_map["holodeck"][1],         # Semantic Hash Memory
                doc_concept_map["holodeck"][2],         # NetHack Sim
                doc_concept_map["holodeck"][3],         # Comic Vision
            ],
        },
    ]

    # Build contradiction tuples using A2-2 concept node IDs
    # We need to resolve names to IDs at the A2-3 level first, then
    # let the refinery build edges. For cross-doc contradictions we
    # reference the A2-3 concept nodes directly.
    def find_a2_3_node_id(concept_name: str) -> str:
        """Find the first A2-3 node whose name matches."""
        for node in refinery.builder.pydantic_model.nodes.values():
            if node.name == concept_name and node.trust_zone == "A2_3_INTAKE":
                return node.id
        return f"UNRESOLVED::{concept_name}"

    contradictions = [
        (find_a2_3_node_id(a), find_a2_3_node_id(b), desc)
        for a, b, desc in CROSS_DOC_CONTRADICTIONS
    ]

    a2_2_batch = refinery.promote_to_a2_2(
        source_batch_ids=all_a2_3_batch_ids,
        refined_concepts=refined_concepts,
        new_batch_id="HE_REFINE_CROSS_DOC_001",
        contradictions=contradictions,
    )
    print(f"  ✓ A2-2 Batch {a2_2_batch.batch_id}: {len(a2_2_batch.node_ids)} refined, {len(a2_2_batch.edge_ids)} edges (incl. {len(contradictions)} contradiction edges)")

    # ── Phase 3: A2-1 Kernel Promotion (highest-confidence concepts) ──
    print(f"\n{'─' * 60}")
    print("▸ Promoting kernel candidates to A2-1...")

    kernel_concepts = [
        {
            "name": "KERNEL: Entropy-First Unified Framework",
            "description": "Highest-confidence synthesis: Spacetime=entropy, one stuff, one force, recursive empirical validation. The axiomatic foundation of the entire system.",
            "source_node_ids": [a2_2_batch.node_ids[0]],  # Entropy-First Unified Framework
        },
        {
            "name": "KERNEL: Chiral Game Theory Operators",
            "description": "Highest-confidence synthesis: 8-state → 16-state model with Te/Ti/Fe/Fi operators on S3+Hopf+Weyl. Mathematically locked and verified.",
            "source_node_ids": [a2_2_batch.node_ids[2]],  # Chiral Game Theory Operators
        },
    ]

    a2_1_batch = refinery.promote_to_kernel(
        source_batch_ids=[a2_2_batch.batch_id],
        kernel_concepts=kernel_concepts,
        new_batch_id="HE_KERNEL_001",
    )
    print(f"  ✓ A2-1 Batch {a2_1_batch.batch_id}: {len(a2_1_batch.node_ids)} kernel nodes, {len(a2_1_batch.edge_ids)} edges")

    # ── Summary ──────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("REFINERY SUMMARY")
    print(f"{'=' * 60}")

    from system_v4.skills.a2_graph_refinery import RefineryLayer
    for layer in RefineryLayer:
        count = refinery.get_layer_node_count(layer)
        print(f"  {layer.value:25s}: {count} nodes")

    total_nodes = len(refinery.builder.pydantic_model.nodes)
    total_edges = len(refinery.builder.pydantic_model.edges)
    print(f"\n  Total graph: {total_nodes} nodes, {total_edges} edges")
    print(f"  Batches: {refinery.get_batch_summary()}")
    print(f"\n  Batch index saved to: {refinery.batch_index_path}")
    print(f"  Graph artifacts saved to: system_v4/a2_state/")
    print(f"\n{'=' * 60}")
    print("✓ High-entropy intake complete. Graph is hot.")


if __name__ == "__main__":
    main()
