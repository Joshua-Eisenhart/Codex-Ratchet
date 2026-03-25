# Thread Prompt Bank — Spin Up As Many As Needed
Generated: 2026-03-22

All threads share these GUARDRAILS (paste at bottom of each):
```
GUARDRAILS:
- Activate: source .venv_spec_graph/bin/activate
- Do not install new packages without listing what you need first
- Do not modify existing graph JSON files
- Do not replace the base stack (pydantic, networkx, JSON artifacts)
- Write results to system_v4/a2_state/audit_logs/ only
- If something fails, record the failure and move on
- Graph JSON format: nodes=dict(id→attrs), edges=list with source_id/target_id keys
```

---

## CODE-HEAVY THREADS (good for Opus/Claude)

### Thread A: Pytest + Mutmut Quality Gate
```
You are working in /home/ratchet/Desktop/Codex Ratchet
Activate .venv_spec_graph.

1. Run the existing test suite:
   pytest system_v4/probes/test_nested_graph_builder.py -v
   
2. mutmut v3 uses a config file. Create system_v4/probes/mutmut.toml:
   [mutmut]
   paths_to_mutate = ["system_v4/skills/nested_graph_builder.py"]
   tests_dir = "system_v4/probes/"
   
3. Run: cd system_v4/probes && python3 -m mutmut run
4. Run: python3 -m mutmut results
5. Report survival rate and which mutants survived
6. Write: system_v4/a2_state/audit_logs/MUTMUT_QUALITY_GATE_REPORT__v1.md
```

### Thread B: Hypothesis Deep Invariant Suite
```
You are working in /home/ratchet/Desktop/Codex Ratchet
Activate .venv_spec_graph.

Write and run a comprehensive Hypothesis invariant test suite covering ALL graph files.
Load every graph in system_v4/a2_state/graphs/*.json and test:

1. Every node has a non-empty description
2. Every edge has source_id, target_id, and relation
3. No edge references a node that doesn't exist (no dangling edges)
4. Node IDs match their expected format (contain :: separator)
5. Layer trust zones are valid values
6. The promoted subgraph is a subset of the low-control graph
7. Adding a node to any graph preserves all existing edges
8. No duplicate edges exist
9. Cross-layer edge counts are consistent

Run with: pytest -v --tb=short
Write: system_v4/a2_state/audit_logs/HYPOTHESIS_DEEP_INVARIANT_REPORT__v1.md
Write script: system_v4/probes/test_graph_invariants_deep.py
```

### Thread C: OPA/Conftest Policy Engine Probe
```
You are working in /home/ratchet/Desktop/Codex Ratchet
Activate .venv_spec_graph.

Evaluate OPA (Open Policy Agent) and Conftest for graph artifact policy checking:

1. Install: pip install conftest (or download binary)
   If conftest not available via pip, use opa binary or write Python equivalent
   
2. Write 5 Rego-style policy rules as Python functions instead:
   - "kernel nodes must have admissibility_state = ADMITTED"
   - "no edge may reference a non-existent node"
   - "promoted nodes must appear in at least 2 layer graphs"
   - "skill nodes must have operation_type defined"
   - "graveyard nodes must not have LIVE status edges"
   
3. Run these policy checks against the actual graph JSON files
4. Report pass/fail for each policy on each graph
5. Write: system_v4/a2_state/audit_logs/POLICY_ENGINE_EVALUATION_REPORT__v1.md
6. Write: system_v4/probes/graph_policy_checker.py
```

### Thread D: egglog Promotion Auditor (Production-Grade)
```
You are working in /home/ratchet/Desktop/Codex Ratchet
Activate .venv_spec_graph. egglog 13.0.1 is installed.

Build on the working examples in:
system_v4/a2_state/audit_logs/EGGLOG_V13_WORKING_EXAMPLES__v1.md

1. Read the actual promoted_subgraph.json and a2_low_control_graph_v1.json
2. Load real node IDs and edges as egglog facts
3. Define promotion rules based on ACTUAL graph structure:
   - Node with >= 3 edges in low-control qualifies for kernel status
   - Node appearing in both low-control and promoted is confirmed
   - Node with CROSS_VALIDATED authority in a connected component is bridge-eligible
4. Run saturation and extract which nodes qualify
5. Compare egglog's answer to what the graph currently says
6. Write: system_v4/a2_state/audit_logs/EGGLOG_PROMOTION_AUDIT__v1.md
7. Write: system_v4/probes/egglog_promotion_auditor.py
```

### Thread E: PySMT Graph Legality Constraint Library
```
You are working in /home/ratchet/Desktop/Codex Ratchet  
Activate .venv_spec_graph. PySMT 0.9.6, z3-solver 4.16.0, cvc5 1.3.3 installed.

Build a reusable constraint library for graph legality:

1. Read system_v4/a2_state/audit_logs/CROSS_SOLVER_VERIFICATION_REPORT__v1.md for context
2. Define 8+ SMT formulas grounded in REAL graph data:
   - Layer membership: every node belongs to exactly one layer
   - Edge symmetry: if A→B exists as RELATED_TO, B→A should too
   - Trust zone monotonicity: kernel nodes have higher trust than intake nodes
   - Promotion requires evidence: promoted nodes have support edges
   - No orphan clusters: every connected component has >= 1 kernel-touching path
   - Community stability: moving one node changes <= 5% of community assignments
   - Description completeness: every node has description length > 10 chars
   - Edge type consistency: DEPENDS_ON edges go from higher to lower rank
3. Run each formula on Z3 AND cvc5, compare results
4. Write: system_v4/a2_state/audit_logs/SMT_GRAPH_LEGALITY_LIBRARY__v1.md
5. Write: system_v4/probes/smt_graph_legality.py
```

### Thread F: dotmotif Structural Pattern Catalog
```
You are working in /home/ratchet/Desktop/Codex Ratchet
Activate .venv_spec_graph. dotmotif 0.14.0 is installed.

Build a structural pattern catalog across all graphs:

1. Define 6+ motif patterns:
   - Triangle: A→B→C→A (cyclic dependency)
   - Star: A→B, A→C, A→D (hub node)
   - Chain-of-3: A→B→C (dependency chain)
   - Bidirectional: A→B, B→A (mutual dependency)
   - Fork: A→B, A→C with B≠C (branching)
   - Diamond: A→B, A→C, B→D, C→D (converging paths)
   
2. Run each motif on:
   - a2_low_control_graph_v1.json
   - promoted_subgraph.json
   - a2_high_intake_graph_v1.json (may be slow, use subgraph of 500 nodes)
   
3. Count occurrences. Identify the most common structural patterns.
4. Flag any surprising patterns (e.g., unexpected cycles, orphan stars)
5. Write: system_v4/a2_state/audit_logs/DOTMOTIF_PATTERN_CATALOG__v1.md
6. Write: system_v4/probes/dotmotif_pattern_catalog.py
```

---

## RESEARCH/ANALYSIS THREADS (good for Gemini)

### Thread G: Topology Comparison Deep Dive
```
You are working in /home/ratchet/Desktop/Codex Ratchet
Activate .venv_spec_graph. GUDHI 3.11.0, leidenalg 0.11.0 installed.

Read the existing results:
- system_v4/a2_state/audit_logs/LARGE_GRAPH_TOPOLOGY_REPORT__v1.md
- system_v4/a2_state/audit_logs/PHASE1_TOOL_ADOPTION_AUDIT_REPORT__v1.md

Extend the topology analysis:

1. Run GUDHI on EVERY graph in system_v4/a2_state/graphs/ that has < 5000 nodes
2. For each, compute: Betti numbers, persistence diagram statistics (birth/death ranges)
3. Run leidenalg on each at resolutions [0.1, 0.5, 1.0, 2.0, 5.0]
4. Build a topology comparison table showing how the graph hierarchy changes:
   intake → refinement → low-control → promoted
   Does fragmentation decrease? Do cycles appear?
5. Write: system_v4/a2_state/audit_logs/FULL_TOPOLOGY_COMPARISON__v1.md
```

### Thread H: Community-to-Layer Alignment Audit
```
You are working in /home/ratchet/Desktop/Codex Ratchet
Activate .venv_spec_graph. leidenalg installed.

The nested graph has 5 manually-defined layers (HIGH_INTAKE, MID_REFINEMENT, LOW_CONTROL, A1_JARGONED, PROMOTED).
leidenalg found 276 communities in low-control and 1757 in high-intake.

Question: Do the algorithmically-discovered communities ALIGN with the manual layers?

1. Load all layer graphs
2. For nodes that appear in multiple layers, track which community they land in
3. Compute: what % of each manual layer maps to a single community?
4. Identify: are there communities that span multiple layers? (these are bridge communities)
5. Identify: are there layers that split into many communities? (these are internally diverse)
6. Write: system_v4/a2_state/audit_logs/COMMUNITY_LAYER_ALIGNMENT_AUDIT__v1.md
```

### Thread I: Graph Health Dashboard
```
You are working in /home/ratchet/Desktop/Codex Ratchet
Activate .venv_spec_graph.

Build a comprehensive graph health check that tests the ENTIRE graph corpus:

1. Load every graph in system_v4/a2_state/graphs/
2. For each, compute and report:
   - Node count, edge count, density
   - Connected components count, largest component size
   - Degree distribution (min, max, mean, median)
   - Isolated nodes (degree 0)
   - Self-loops
   - Duplicate edges
   - Dangling edges (referencing non-existent nodes)
   - Node types distribution
   - Edge relation types distribution
   - Missing required fields (description, admissibility_state, etc.)
3. Flag any anomalies
4. Write: system_v4/a2_state/audit_logs/GRAPH_HEALTH_DASHBOARD__v1.md
5. Write: system_v4/probes/graph_health_check.py
```

### Thread J: Cross-Graph Overlap Analysis
```
You are working in /home/ratchet/Desktop/Codex Ratchet
Activate .venv_spec_graph.

Analyze how the 5 layer graphs overlap and relate:

1. For each pair of graphs, compute:
   - Shared node IDs (intersection)
   - Unique nodes (in A but not B)
   - Shared edges
2. Build a Jaccard similarity matrix
3. Check: is the promoted subgraph truly a subset of low-control?
4. Check: do nodes "flow down" from intake → refinement → control?
5. Identify: nodes that appear in unexpected places
6. Write: system_v4/a2_state/audit_logs/CROSS_GRAPH_OVERLAP_ANALYSIS__v1.md
```

### Thread K: Source Family Deep Eval (research)
```
Read these files:
- /home/ratchet/Desktop/RESEARCH_BY_DOMAIN/08__SOURCE_FAMILY_CORPUS_EXPANSION.md
- /home/ratchet/Desktop/RESEARCH_BY_DOMAIN/10__CROSS_REFERENCE__ANTIGRAVITY_x_CODEX_PRO.md

Do deep web research on the top 5 "save now" source families that we haven't installed yet:
1. Scikit-TDA (ripser, kepler-mapper, persim) — what does each sub-package actually do? API examples?
2. pysheaf (kb1dds) — is it maintained? Last commit? Python 3.13 compatible? API example?
3. ReGraph (Blue Brain) — is it maintained? How does sesqui-pushout rewriting work?
4. OpenViking (volcengine) — what exactly is the filesystem context model?
5. GitHub Spec Kit — what are the 4 phases? How does `specify` CLI work?

For each: exact install command, Python version compatibility, last release date, dependency weight.
Write results to: /home/ratchet/Desktop/RESEARCH_BY_DOMAIN/11__SOURCE_FAMILY_DEEP_EVAL__v1.md
```

### Thread L: Codex Pro Completed Output Deep Read
```
Read the completed Codex Pro ZIP outputs in:
/home/ratchet/Desktop/Codex Ratchet/work/to_send_to_pro/jobs/

Extract and organize the content from these completed ZIP files:
- COMPLETED_ZIP_JOB__*MEMORY_CONTINUITY*.zip
- EXTERNAL_RESEARCH_RETOOL_REFINERY__AUTORESEARCH_AND_COUNCIL*.zip
- EXTERNAL_RESEARCH_RETOOL_REFINERY__completed_outputs*.zip (both copies)
- EXTERNAL_RESEARCH_RETOOL_REFINERY__SKILL_INTEGRATION*.zip
- formal_search_synthesis_tool_discovery_outputs_v1.zip
- graph_geometry_topology_research_outputs_v1.zip
- research_bundle_outputs.zip

For each ZIP: extract the RATCHET_FUEL_SELECTION_MATRIX, REJECT_LOG, TOP_5 lists.
Cross-reference with:
/home/ratchet/Desktop/RESEARCH_BY_DOMAIN/10__CROSS_REFERENCE__ANTIGRAVITY_x_CODEX_PRO.md

Find any tools or findings the cross-reference document MISSED.
Write: /home/ratchet/Desktop/RESEARCH_BY_DOMAIN/12__CODEX_PRO_DEEP_READ__v1.md
```

---

## QUICK UTILITY THREADS (either model, fast)

### Thread M: Git Commit the DVC Setup
```
You are working in /home/ratchet/Desktop/Codex Ratchet
Read system_v4/a2_state/audit_logs/DVC_SETUP_REPORT__v1.md

1. Check git status
2. Add and commit the DVC setup files:
   git add .dvc/ system_v4/a2_state/graphs/*.dvc system_v4/a2_state/graphs/.gitignore system_v4/a2_state/experiments/
   git commit -m "Phase 1-2: DVC init, track 12 graph artifacts (130MB), experiment structure"
3. Add and commit the Phase 1-2 audit logs and probe scripts:
   git add system_v4/a2_state/audit_logs/PHASE* system_v4/a2_state/audit_logs/*REPORT__v1* system_v4/probes/
   git commit -m "Phase 1-2: tool adoption audit logs, probe scripts, test suite"
4. Report what was committed
5. Write: system_v4/a2_state/audit_logs/GIT_COMMIT_LOG__phase1_phase2__v1.md
```

### Thread N: pip freeze Snapshot
```
You are working in /home/ratchet/Desktop/Codex Ratchet
Activate .venv_spec_graph.

1. Run: pip freeze > system_v4/a2_state/audit_logs/PIP_FREEZE__venv_spec_graph__2026_03_22.txt
2. Count total packages
3. Categorize into: base stack, phase 1, phase 2, transitive deps
4. Flag any packages that seem unexpected or large
5. Write summary: system_v4/a2_state/audit_logs/PACKAGE_INVENTORY__v1.md
```
