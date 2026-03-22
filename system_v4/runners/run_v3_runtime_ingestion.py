"""
V3 Runtime Deep-Read Ingestion — A2 Graph Refinery Pass

Ingests the concepts extracted from the deep-read of all 19 v3 runtime files
(~8,600 lines) into the A2 graph. Also registers system_v4/ files as source
documents for tracking.

Run:
  cd ~/Desktop/Codex\ Ratchet
  python3 -m system_v4.runners.run_v3_runtime_ingestion
"""

import sys
from pathlib import Path


if __name__ == "__main__":
    REPO_ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(REPO_ROOT))

    from system_v4.skills.a2_graph_refinery import A2GraphRefinery, ExtractionMode

    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session("SESSION_V3_RUNTIME_DEEP_INGESTION_2026-03-18")
    print(f"Started session: {sid}")

    # ── Runtime Source Documents ──────────────────────────────────────────
    # Register each runtime file as a SOURCE_DOCUMENT node

    RUNTIME_DIR = REPO_ROOT / "system_v3" / "runtime" / "bootpack_b_kernel_v1"
    RUNTIME_FILES = [
        "kernel.py", "a1_a0_b_sim_runner.py", "sim_engine.py", "a0_compiler.py",
        "a1_strategy.py", "a1_autowiggle.py", "a1_bridge.py", "a1_debug_policy.py",
        "a1_model_selector.py", "state.py", "containers.py", "snapshot.py",
        "pipeline.py", "gateway.py", "sim_dispatcher.py",
        "zip_protocol_v2_validator.py", "zip_protocol_v2_writer.py",
    ]

    # ── Core Loop Concepts (from kernel.py, a1_a0_b_sim_runner.py, sim_engine.py) ──

    print("\n--- INGESTING: Core Loop Concepts ---")
    refinery.ingest_document(
        doc_path=str(RUNTIME_DIR / "kernel.py"),
        extraction_mode=ExtractionMode.ENGINE_PATTERN,
        batch_id="BATCH_V3RT_CORE_LOOP_001",
        concepts=[
            {
                "name": "B_KERNEL_LINE_FENCE_VALIDATION",
                "description": "Every line in an export block must match a recognized regex pattern (SPEC_HYP, DEF_FIELD, REQUIRES, etc.). Unrecognized lines cause immediate REJECT. This is a fail-closed content gate.",
                "tags": ["b_kernel", "validation", "fail_closed", "determinism"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "L0_LEXEME_SET_18_STRUCTURAL_TOKENS",
                "description": "Exactly 18 structural tokens are L0-legal: finite, dimensional, hilbert, space, density, matrix, operator, channel, cptp, unitary, lindblad, hamiltonian, commutator, anticommutator, trace, partial, tensor, superoperator, generator. Everything else is derived-only.",
                "tags": ["lexicon", "b_kernel", "l0_boundary", "determinism"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "DERIVED_ONLY_TERMS_70_BLOCKLIST",
                "description": "70+ terms (equal, identity, coordinate, time, cause, optimize, probability, platonic, etc.) are DERIVED_ONLY — they cannot appear in export blocks unless their canonical term has already been permitted through the evidence ladder.",
                "tags": ["lexicon", "b_kernel", "constraint", "jargon_quarantine"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "GENESIS_ROOT_CONSTRAINTS",
                "description": "KernelState seeds F01_FINITUDE and N01_NONCOMMUTATION as root constraint items in the survivor ledger BEFORE any axiom is admitted. These are constraints-before-axioms — the system cannot run without them.",
                "tags": ["b_kernel", "genesis", "root_constraint", "finitude", "noncommutation"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "PROMOTION_GATES_G0_THROUGH_G6",
                "description": "SIM specs must clear 7 gates for promotion: G0 (interaction density), G1 (dependency coverage), G2 (negative coverage), G3 (graveyard coverage), G4 (reproducibility — identical run hashes), G5 (no bypass flag), G6 (stress coverage — BASELINE + BOUNDARY_SWEEP + PERTURBATION families).",
                "tags": ["sim_engine", "promotion", "evidence_ladder", "quality_gate"],
                "authority": "SOURCE_CLAIM",
            },
        ]
    )

    # ── Pipeline Architecture Concepts ──

    print("\n--- INGESTING: Pipeline Architecture ---")
    refinery.ingest_document(
        doc_path=str(RUNTIME_DIR / "zip_protocol_v2_validator.py"),
        extraction_mode=ExtractionMode.ENGINE_PATTERN,
        batch_id="BATCH_V3RT_ZIP_PROTOCOL_001",
        concepts=[
            {
                "name": "ZIP_PROTOCOL_V2_EIGHT_TYPE_SYSTEM",
                "description": "8 ZIP types define the full communication topology: A2_TO_A1_PROPOSAL_ZIP, A1_TO_A0_STRATEGY_ZIP, A0_TO_B_EXPORT_BATCH_ZIP (FORWARD) + B_TO_A0_STATE_UPDATE_ZIP, SIM_TO_A0_SIM_RESULT_ZIP, A0_TO_A1_SAVE_ZIP, A1_TO_A2_SAVE_ZIP, A2_META_SAVE_ZIP (BACKWARD). Each type has fixed source/target layers and allowed payload files.",
                "tags": ["zip_protocol", "architecture", "communication", "pipeline"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "SEQUENCE_MONOTONICITY_WITH_PARK",
                "description": "ZIP packets carry monotonically increasing sequence numbers per (run_id, source_layer) pair. Out-of-order packets are PARKED (not rejected) for later replay. Regression (sequence <= last_accepted) is hard-rejected.",
                "tags": ["zip_protocol", "sequencing", "determinism", "ordering"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "CANONICAL_SERIALIZATION_EVERYWHERE",
                "description": "All JSON files use json.dumps(sort_keys=True, separators=(',',':')) with trailing newline. All text files enforce no-CR, no-trailing-spaces, trailing-LF. ZIP timestamps are fixed to (1980,1,1,0,0,0). This makes every byte deterministic and hashable.",
                "tags": ["determinism", "serialization", "reproducibility", "hashing"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "FORBIDDEN_CONTAINER_ISOLATION",
                "description": "Each ZIP type has a forbidden container set. Export ZIPs forbid SIM_EVIDENCE and SNAPSHOT. SIM ZIPs forbid EXPORT_BLOCK and SNAPSHOT. Save ZIPs forbid all mutation containers. This prevents layer-crossing contamination.",
                "tags": ["zip_protocol", "isolation", "trust_boundary", "security"],
                "authority": "SOURCE_CLAIM",
            },
        ]
    )

    # ── Strategy + Compiler Concepts ──

    print("\n--- INGESTING: Strategy + Compiler ---")
    refinery.ingest_document(
        doc_path=str(RUNTIME_DIR / "a0_compiler.py"),
        extraction_mode=ExtractionMode.ENGINE_PATTERN,
        batch_id="BATCH_V3RT_STRATEGY_COMPILER_001",
        concepts=[
            {
                "name": "FIVE_REPAIR_OPERATORS",
                "description": "A0 compiler applies 5 deterministic repair operators to strategies before emitting export blocks: OP_INJECT_PROBE (adds missing probes), OP_REORDER_DEPENDENCIES (topological sort), OP_MUTATE_LEXEME (L0/L1 token substitution), OP_REPAIR_DEF_FIELD (schema fixes), OP_NEG_SIM_EXPAND (negative class expansion).",
                "tags": ["a0_compiler", "repair", "determinism", "strategy"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "STRUCTURAL_DIGEST_DEDUP",
                "description": "Before admission, candidate export blocks are hashed (structural digest) and compared against existing survivor digests using both SHA256 exact match and Jaccard similarity. Near-duplicates are rejected to prevent ledger bloat.",
                "tags": ["a0_compiler", "dedup", "near_duplicate", "jaccard"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "CANONICAL_ASCENT_UNIT",
                "description": "Autowiggle generates strategies using a deterministic 4-step ascent unit: MATH_DEF → TERM_DEF → CANON_PERMIT → SIM_SPEC. Each ascent unit is a self-contained ratchet package that can stand alone.",
                "tags": ["a1_autowiggle", "strategy_generation", "determinism", "ascent"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "THREAD_B_FENCE_PRE_VALIDATION",
                "description": "Autowiggle pre-validates every generated strategy against Thread-B fence rules BEFORE emission. Strategies that would fail the kernel are caught and discarded at generation time, preventing wasted cycles.",
                "tags": ["a1_autowiggle", "thread_b", "validation", "efficiency"],
                "authority": "SOURCE_CLAIM",
            },
        ]
    )

    # ── Dispatch + Gateway Concepts ──

    print("\n--- INGESTING: Dispatch + Gateway ---")
    refinery.ingest_document(
        doc_path=str(RUNTIME_DIR / "sim_dispatcher.py"),
        extraction_mode=ExtractionMode.ENGINE_PATTERN,
        batch_id="BATCH_V3RT_DISPATCH_GATEWAY_001",
        concepts=[
            {
                "name": "SIM_DISPATCH_TIER_SUITE_ORDERING",
                "description": "SimDispatcher plans SIM campaigns using a multi-key sort: (blocked, stage_rank, tier_rank, suite_rank, sim_id). 8 suite kinds ordered: micro_suite → mid_suite → segment_suite → engine_suite → mega_suite → failure_isolation → graveyard_rescue → replay_from_tape. Engine/mega suites are blocked until all lower-tier stages complete.",
                "tags": ["sim_dispatcher", "ordering", "campaign", "determinism"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "GATEWAY_MESSAGE_ROUTING",
                "description": "BootpackBGateway routes inbound messages to 4 handlers: COMMAND (REQUEST DUMP_LEDGER etc.), EXPORT (→ kernel.evaluate_export_block), SNAPSHOT (→ validate + admit), SIM_EVIDENCE (→ kernel.ingest_sim_evidence_pack). Unrecognized messages are hard-rejected as MULTI_ARTIFACT_OR_PROSE.",
                "tags": ["gateway", "message_routing", "b_kernel", "protocol"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "COMMENT_BAN_ENFORCEMENT",
                "description": "Lines starting with '#' or '//' are banned in all SIM_EVIDENCE and SNAPSHOT messages. This prevents prose/annotation from contaminating structured artifacts. The gateway checks this before any content parsing.",
                "tags": ["gateway", "validation", "fail_closed", "hygiene"],
                "authority": "SOURCE_CLAIM",
            },
        ]
    )

    # ── LLM Containment Concepts ──

    print("\n--- INGESTING: LLM Containment ---")
    refinery.ingest_document(
        doc_path=str(RUNTIME_DIR / "a1_model_selector.py"),
        extraction_mode=ExtractionMode.ENGINE_PATTERN,
        batch_id="BATCH_V3RT_LLM_CONTAINMENT_001",
        concepts=[
            {
                "name": "MODEL_SELECTOR_PREFERS_NO_LLM",
                "description": "a1_model_selector ranks benchmark results by: needs_real_llm (prefer FALSE) → id_churn_signal (prefer FALSE) → rejected_total (minimize) → parked_total (minimize) → accepted_total (maximize). Models that don't need an actual LLM are always ranked first.",
                "tags": ["a1_model_selector", "llm_containment", "determinism", "jp_principle"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "ESCALATION_HARD_FAILURE_TAGS",
                "description": "5 hard failure tags trigger escalation: SCHEMA_FAIL, UNDEFINED_TERM_USE, DERIVED_ONLY_PRIMITIVE_USE, DERIVED_ONLY_NOT_PERMITTED, SPEC_KIND_UNSUPPORTED. If ≥3 consecutive rejects all carry hard tags, or generation/schema fail limits are exceeded, the system escalates rather than retrying.",
                "tags": ["a1_debug_policy", "escalation", "fail_closed", "error_handling"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "THREE_SOURCE_MULTIPLEXER",
                "description": "A1Bridge multiplexes between 3 strategy sources: REPLAY (deterministic template rotation — no LLM), PACKET (ZIP inbox consumption — may involve LLM output), AUTOWIGGLE (deterministic branchy generation — no LLM). This means 2 of 3 modes run entirely without LLM contact.",
                "tags": ["a1_bridge", "source_multiplexing", "determinism", "llm_containment"],
                "authority": "SOURCE_CLAIM",
            },
        ]
    )

    # ── Bidirectional Loop Concepts ──

    print("\n--- INGESTING: Bidirectional Loop ---")
    refinery.ingest_document(
        doc_path=str(RUNTIME_DIR / "a1_a0_b_sim_runner.py"),
        extraction_mode=ExtractionMode.ENGINE_PATTERN,
        batch_id="BATCH_V3RT_BIDIR_LOOP_001",
        concepts=[
            {
                "name": "BIDIRECTIONAL_LOOP_EVERY_STEP",
                "description": "The main loop in a1_a0_b_sim_runner fires BOTH forward (A1→A0→B strategy evaluation) and backward (SIM execution → evidence ingestion → state snapshot) in EVERY iteration. There is no separate audit pass — auditing is integral to every ratchet step.",
                "tags": ["loop", "bidirectional", "architecture", "ratchet_core"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "GRAVEYARD_RESCUE_FRACTION",
                "description": "Autowiggle allocates a configurable fraction of strategy targets (default ~50% when graveyard is non-empty) to RESCUE operations, pulling killed items back from the graveyard for re-evaluation. The graveyard is not a trash can — it is a dependency-aware staging area.",
                "tags": ["graveyard", "rescue", "strategy_generation", "lifecycle"],
                "authority": "SOURCE_CLAIM",
            },
            {
                "name": "FIVE_LAYER_PIPELINE_A2_A1_A0_B_SIM",
                "description": "The runtime implements a 5-layer deterministic pipeline connected by file-based ZIP capsules: A2 (graph controller) → A1 (strategy generator) → A0 (compiler) → B (enforcement kernel) → SIM (evidence engine). No in-process RPC, no shared memory — all inter-layer communication is artifact-based.",
                "tags": ["architecture", "pipeline", "layers", "determinism"],
                "authority": "SOURCE_CLAIM",
            },
        ]
    )

    # ── Register remaining runtime files as source docs ──

    print("\n--- REGISTERING: Remaining runtime source documents ---")
    for fname in RUNTIME_FILES:
        fpath = RUNTIME_DIR / fname
        if fpath.exists() and fname not in {
            "kernel.py", "zip_protocol_v2_validator.py", "a0_compiler.py",
            "sim_dispatcher.py", "a1_model_selector.py", "a1_a0_b_sim_runner.py",
        }:
            refinery.ingest_document(
                doc_path=str(fpath),
                extraction_mode=ExtractionMode.SOURCE_MAP,
                batch_id=f"BATCH_V3RT_REG_{fname.replace('.py','').upper()[:30]}",
                concepts=[],  # registered as source doc only, concepts already covered above
            )
            print(f"  Registered: {fname}")

    # ── Register system_v4/ key files ──

    print("\n--- REGISTERING: system_v4 key files ---")
    V4_DIR = REPO_ROOT / "system_v4"
    v4_files_to_register = [
        V4_DIR / "skills" / "a2_graph_refinery.py",
        V4_DIR / "skills" / "v4_graph_builder.py",
        V4_DIR / "skills" / "run_wave_0_1_extraction.py",
        V4_DIR / "skills" / "run_promotion_audit.py",
        V4_DIR / "skills" / "run_contradiction_scan.py",
        V4_DIR / "skills" / "run_mass_extraction.py",
        V4_DIR / "skills" / "a2_boot.py",
        V4_DIR / "skills" / "test_a2_graph_refinery_patched.py",
        V4_DIR / "a2_state" / "A2_GRAPH_REFINERY_PROCESS__v2.md",
        V4_DIR / "a2_state" / "THREAD_CONTEXT_EXTRACT__ANTIGRAVITY__2026_03_18__v8.md",
        V4_DIR / "a2_state" / "THREAD_CONTEXT_EXTRACT__OPUS__2026_03_18__v7.md",
    ]

    for fpath in v4_files_to_register:
        if fpath.exists():
            refinery.ingest_document(
                doc_path=str(fpath),
                extraction_mode=ExtractionMode.SOURCE_MAP,
                batch_id=f"BATCH_V4_REG_{fpath.stem.upper()[:30]}",
                concepts=[],  # registered as source doc, deep extraction done separately
            )
            print(f"  Registered: {fpath.name}")

    # ── Seal the thread context ──

    print("\n--- SEALING THREAD CONTEXT ---")
    seal_id = refinery.seal_thread(
        active_tasks=[
            "Deep-read v3 runtime test files (20+ files)",
            "Materialize JP determinism principle (good/bad examples + workflow)",
            "Cross-reference Lev OS repos",
            "Build daemon/background process runner",
            "Process system_v4/ through refinery (deep extraction, not just registration)",
            "Build v4 proto loop runner with bidirectional architecture",
        ],
        context_notes=(
            "V3 runtime deep-read COMPLETE: 19 files, ~8,600 lines. "
            "All concepts ingested into A2 graph. "
            "Key patterns: determinism-first, fail-closed, graveyard lifecycle, "
            "promotion gates G0-G6, bidirectional loop every step, LLM containment. "
            "System_v4 files registered but need deep extraction pass. "
            "Thread context extract v8 written."
        ),
    )
    print(f"Thread sealed: {seal_id}")

    log_path = refinery.end_session()
    print(f"\nSession ended. Log: {log_path}")
    print(f"Total graph: {len(refinery.builder.pydantic_model.nodes)} nodes, "
          f"{len(refinery.builder.pydantic_model.edges)} edges")
