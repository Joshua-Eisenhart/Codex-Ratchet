# BATCH 5 — 3-SYSTEM PARALLEL DISPATCH
## 47 Prompts: 15 Pro + 12 AG + 20 NLM | 2026-03-23

---

# PRO THREADS (15)
Each prompt is self-contained — one copy-paste per thread.

---

### PRO-1

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Axioms: F01 (finite d), N01 (AB≠BA), CAS04 (operational equivalence). 8-stage engine, 32 microstates/type, 720° spinor. LIVE: 33 SIMs, 99 tokens, 94 PASS, 5 KILL. BANNED: "Win/Lose" use SG/EE. "Axis/Axes" use physics names. SIMs in system_v4/probes/.

Read: system_v4/probes/gain_calibration_sim.py
Read: system_v4/probes/szilard_64stage_sim.py
Read: system_v4/a2_state/audit_logs/A2_NLM_BATCH4_FULL_SYNTHESIS__v1.md (NLM-16: γ≥2ω derivation)

PROBLEM: 64-stage Lindblad engine produces ALL-NEGATIVE ΔΦ (≈ -0.41) across entire γ_sub sweep (0.01–1.0, γ_dom=5.0). The engine never ratchets forward. Root causes: Fe not energy-selective (dampens all d(d-1) modes equally), operators simultaneous not sequential, γ global not per-stage. NLM-16 derived γ≥2ω for critical damping from damped harmonic oscillator model.

OUTPUT to system_v4/probes/: gain_calibration_v2_sim.py + GAIN_CALIBRATION_FIX_NOTES.md. Run it.
```

### PRO-2

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Axioms: F01 (finite d), N01 (AB≠BA), CAS04 (operational equivalence). 8-stage engine, 32 microstates/type. LIVE: 99 tokens, 94P/5K. BANNED: "Win/Lose" use SG/EE. SIMs in system_v4/probes/.

Read: system_v4/probes/abiogenesis_sim.py
Read: system_v4/probes/foundations_sim.py (operator implementations)

PROBLEM: 1 KILL: S_SIM_ABIOGENESIS_V1, reason NO_SPONTANEOUS_LIFE. Starts from I/d (maximally mixed), applies random CPTP, structure never emerges. FIX: The dual-loop mechanism is the key. Random SINGLE operators → thermal death (correct, should NOT produce life). But the DUAL LOOP (alternating Ti→Fe→Te→Fi ratchet cycle) should SOMETIMES find the attractor. Test both: (1) random single ops → never structure, (2) dual-loop cycle → sometimes structure.

OUTPUT to system_v4/probes/: abiogenesis_v2_sim.py + ABIOGENESIS_FIX_NOTES.md. Run it.
```

### PRO-3

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Axioms: F01 (finite d), N01 (AB≠BA). LIVE: 99 tokens, 94P/5K. BANNED: "Win/Lose" use SG/EE. SIMs in system_v4/probes/.

Read: system_v4/probes/complexity_gap_sim.py
Read: system_v4/probes/proof_cost_sim.py (Landauer costs)

PROBLEM: 1 KILL: S_SIM_BASIN_DEPTH_V1, reason NO_CORRELATION. P-NP gap doesn't scale with dimension d. FIX: Use Landauer's principle. Each Ti projection costs kT·ln(2) entropy per bit erasure. P operations (stay in basin) cost O(d). NP operations (cross basin boundary) cost O(d·ln(d)) due to Lindblad depth. Gap should grow logarithmically.

OUTPUT to system_v4/probes/: complexity_gap_v2_sim.py + COMPLEXITY_GAP_FIX_NOTES.md. Run it.
```

### PRO-4

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Axioms: F01 (finite d), N01 (AB≠BA). LIVE: 99 tokens, 94P/5K. SIMs in system_v4/probes/.

Read: system_v4/probes/arithmetic_gravity_sim.py
Read: system_v4/probes/deep_math_foundations_sim.py

The engine derives counting, addition, multiplication, primes from QIT axioms. Missing: division, zero, negation, fractions, order. BUILD: (1) Division = partial trace (d→d/k, remainder = lost entropy), (2) Zero = I/d (maximally mixed, additive identity), (3) Negation = time-reversal (ρ→ρᵀ), (4) Order = entropy ordering (ρ₁<ρ₂ ⟺ S(ρ₁)<S(ρ₂)), (5) Fractions = reduced density matrices.

OUTPUT to system_v4/probes/: extended_arithmetic_sim.py + EXTENDED_ARITHMETIC_NOTES.md. Run it.
```

### PRO-5

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). 8-stage engine, Type-1 (FeTi outer) + Type-2 (TeFi outer) = 64 total microstates. LIVE: 99 tokens, 94P/5K. SIMs in system_v4/probes/.

Read: system_v4/probes/szilard_64stage_sim.py
Read: system_v4/probes/full_8stage_engine_sim.py

PROBLEM: 1 KILL: S_SIM_DUAL_SZILARD_V1, reason ADDITIVE. Entropy changes across 64-stage dual-stacked cycle are not additive. The Szilard engine is Engine A output = Engine B input. Fe dissipation between A→B is not conservative, or partial trace at handoff loses entropy. Related to γ calibration — both about the γ ratio.

OUTPUT to system_v4/probes/: szilard_64stage_v2_sim.py + SZILARD_FIX_NOTES.md. Run it.
```

### PRO-6

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Axioms: F01 (finite d), N01 (AB≠BA). 8-stage engine. LIVE: 99 tokens, 94P/5K. SIMs in system_v4/probes/.

Read: system_v4/probes/rock_falsifier_sim.py
Read: system_v4/probes/rock_falsifier_enhanced_sim.py

Bridge T = single biggest ontological gap. "Solvency forces complexity" is CHOSEN not derived. TEST: Can a trivially simple system (d=2, single operator, "rock") outperform the 8-stage engine in long-term solvency across environmental shocks? The engine MUST win or Bridge T has a hole. Add proper EvidenceToken emission.

OUTPUT to system_v4/probes/: rock_falsifier_v3_sim.py (with EvidenceTokens) + BRIDGE_T_RESULTS.md. Run it.
```

### PRO-7

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Engine types: Type-1 (FeTi outer, γ-dominant, convergent) + Type-2 (TeFi outer, ω-dominant, divergent). 720° spinor. SIMs in system_v4/probes/.

Read: system_v4/probes/type2_engine_sim.py

Type-2 is ω-dominant (underdamped). It intentionally explores phase space. NLM-16 says Type-2 should have γ<2ω. Current SIM is basic. Build full parameterized Type-2 with: phase space exploration metrics, comparison to Type-1 convergence rate, verify spinor 720° property holds for both types.

OUTPUT to system_v4/probes/: type2_engine_v2_sim.py + TYPE2_ENGINE_NOTES.md. Run it.
```

### PRO-8

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). The engine uses a 6-bit control surface (bits 1-6) for operator selection at each stage. SIMs in system_v4/probes/.

NLM-15 flagged the 12-Bit Mirror (bits 7-12) as "enormous inferential leap, never simulated." Bits 1-6 define the control surface. Bits 7-12 should be the MIRROR — same algebraic structure, different thermodynamic domain, related via conjugation/reflection.

BUILD: SIM that constructs the full 12-bit address space and tests whether bits 7-12 genuinely mirror bits 1-6 structure. Test: is the mirror forced by F01+N01 or is it another CHOSEN structure?

OUTPUT to system_v4/probes/: mirror_12bit_sim.py + MIRROR_12BIT_NOTES.md. Run it.
```

### PRO-9

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Axioms: F01 (finite d), N01 (AB≠BA), CAS04 (operational equivalence). SIMs in system_v4/probes/.

Read: system_v4/probes/consciousness_sim.py (currently 2 PASS, basic)

Upgrade path SUGGESTIVE→STRUCTURAL requires: "Isolated CPTP proof of self-steering autopoietic fixed point." BUILD formal SIM testing: (1) Self-model: ρ_self such that Tr_env(ρ_total) ≈ ρ_self, (2) Autopoietic fixed point: E(ρ*)=ρ* under perturbation, (3) IIT-like: Φ>0 (integrated information strictly above any partition).

OUTPUT to system_v4/probes/: consciousness_formal_sim.py + CONSCIOUSNESS_FORMAL_NOTES.md. Run it.
```

### PRO-10

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). 8-stage dual-loop engine. SIMs in system_v4/probes/.

Read: system_v4/probes/alignment_sim.py (currently 2 PASS, basic)

Upgrade SUGGESTIVE→STRUCTURAL requires: "Mathematical Solvency Operator proving E(ρ*)=ρ* under shocks." BUILD: (1) Define solvency S(ρ) = ability to maintain structure under perturbation, (2) Apply random environmental shocks, (3) Show aligned system (dual-loop) maintains E(ρ*)≈ρ*, (4) Show misaligned (single-loop) degrades.

OUTPUT to system_v4/probes/: alignment_formal_sim.py + ALIGNMENT_FORMAL_NOTES.md. Run it.
```

### PRO-11

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Axioms: F01 (finite d), N01 (AB≠BA). SIMs in system_v4/probes/.

Read: system_v4/probes/yang_mills_sim.py (currently 2 PASS, basic)

Upgrade SUGGESTIVE→STRUCTURAL requires: "Finite gauge condensation with non-zero minimal energy state." BUILD: finite-d gauge group acting on ρ, show mass gap emerges from spectral gap of the CPTP channel. The key: non-commutative gauge group (from N01) forces spectral gap.

OUTPUT to system_v4/probes/: yang_mills_formal_sim.py + YANG_MILLS_FORMAL_NOTES.md. Run it.
```

### PRO-12

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). 6-bit control surface for operator selection. SIMs in system_v4/probes/.

Read: system_v4/probes/chemistry_sim.py (currently 3 PASS, basic)

Upgrade SUGGESTIVE→STRUCTURAL requires: "6-bit control surface producing bonding without 3D distance primitives." BUILD: Two subsystems interact via CPTP operators only (no spatial embedding). Show covalent-like sharing of eigenstate = "bonding." No distance metric allowed — bonding emerges from operator algebra alone.

OUTPUT to system_v4/probes/: chemistry_formal_sim.py + CHEMISTRY_FORMAL_NOTES.md. Run it.
```

### PRO-13

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Berry phase = accumulated geometric phase around closed operator loops. SIMs in system_v4/probes/.

Read: system_v4/probes/quantum_gravity_sim.py (currently 2 PASS, basic)

Upgrade STRUCTURAL→FORMAL requires: "Quantitative invariant from holonomy to spacetime metric without smuggling GR." BUILD: Define holonomy as accumulated phase around closed operator loop. Extract metric-like invariant from Berry phase. The metric must emerge from operator algebra, not be assumed.

OUTPUT to system_v4/probes/: quantum_gravity_formal_sim.py + QUANTUM_GRAVITY_FORMAL_NOTES.md. Run it.
```

### PRO-14

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Berry phase = geometric phase accumulated across engine cycles. SIMs in system_v4/probes/.

Read: system_v4/probes/scientific_method_sim.py (currently 3 PASS)

Upgrade STRUCTURAL→FORMAL requires: "Berry phase at handoff proving paradigm shifts from winding saturation." BUILD: Accumulate geometric phase across multiple engine cycles. Show phase quantization corresponds to paradigm boundaries. Kuhn's "normal science → crisis → revolution" = winding number saturation → topological transition.

OUTPUT to system_v4/probes/: scientific_method_formal_sim.py + SCIENTIFIC_METHOD_FORMAL_NOTES.md. Run it.
```

### PRO-15

```
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Axioms: F01 (finite d), N01 (AB≠BA). SIMs in system_v4/probes/.

Read: system_v4/probes/riemann_zeta_sim.py (currently 2 PASS, basic)

Upgrade SUGGESTIVE→STRUCTURAL requires: "CPTP channel generating primes, spectral operator mirroring zeros, within finite d." This is the OPEN KNOT — π(d)~d/ln(d) cannot be derived from F01+N01. BUILD: Construct sieve-like CPTP channel whose fixed points ARE primes in finite d. Test spectral structure against Riemann zero spacing.

OUTPUT to system_v4/probes/: riemann_primes_cptp_sim.py + RIEMANN_CPTP_NOTES.md. Run it.
```

---

# ANTIGRAVITY THREADS (12)
Each prompt is self-contained — one copy-paste per thread.

---

### AG-1

```
CODEX RATCHET ENGINE — QIT framework. 33 SIMs, 99 tokens, 94P/5K. SIMs in system_v4/probes/. Each SIM should emit EvidenceTokens (JSON to stdout with token_id, sim_spec_id, status, measured_value). The runner (run_all_sims.py) captures these.

4 SIMs run successfully but emit NO EvidenceTokens: system_v4/probes/navier_stokes_complexity_sim.py, system_v4/probes/dual_weyl_spinor_engine_sim.py, system_v4/probes/rock_falsifier_sim.py, system_v4/probes/scale_testing_sim.py. Read each, understand what it tests. Add EvidenceToken emission using foundations_sim.py as the pattern. Run: python3 system_v4/probes/run_all_sims.py to verify they now emit tokens.
```

### AG-2

```
CODEX RATCHET ENGINE — QIT framework. 8-stage engine. Bridge T = "solvency forces complexity" — the single biggest ontological gap. NLM-19 proposed a 4th axiom (retrocausality). SIMs in system_v4/probes/.

Read: system_v4/probes/rock_falsifier_sim.py and system_v4/probes/rock_falsifier_enhanced_sim.py. Read: system_v4/a2_state/audit_logs/A2_NLM_BATCH4_FULL_SYNTHESIS__v1.md (focus on NLM-15 and NLM-19). Run both rock falsifier SIMs. Does the rock ever win against the 8-stage engine? Write: system_v4/a2_state/audit_logs/A2_BRIDGE_T_AUDIT__v1.md with analysis.
```

### AG-3

```
CODEX RATCHET ENGINE — system_v4/skills/intent-compiler/dna.yaml lists 18 probes in its probe suite, but 33 SIM files exist in system_v4/probes/ (*_sim.py). The heartbeat daemon only runs SIMs listed in dna.yaml. 15 SIMs are invisible to the heartbeat.

List all *_sim.py files. Add every missing one to dna.yaml's probes section. Run: python3 system_v4/skills/intent-compiler/heartbeat_daemon.py --no-codex to verify. Write: system_v4/a2_state/audit_logs/A2_DNA_SYNC_AUDIT__v1.md
```

### AG-4

```
CODEX RATCHET ENGINE — QIT framework. SIMs in system_v4/probes/. Each SIM emits EvidenceTokens.

Read: system_v4/probes/world_model_sim.py. It currently tests two things at once: structure emergence and predictive learning. Split into 3 explicit tokens: S_SIM_WORLD_MODEL_STRUCTURE_V1 (does ρ develop structure from I/d?), S_SIM_WORLD_MODEL_LEARNING_V1 (does update rule reduce prediction error?), S_SIM_WORLD_MODEL_ADAPTIVE_GENERALIZATION_V1 (does it generalize to novel inputs?). Keep in one file, emit 3 separate EvidenceTokens. Run and save results.
```

### AG-5

```
CODEX RATCHET ENGINE — SIMs in system_v4/probes/. BANNED: "Win/Lose" — use "STRUCTURE_GAINED/ENTROPY_EXPELLED" (SG/EE).

Read: system_v4/probes/engine_terrain_sim.py. Currently passes at 6/8 terrains. Add: (1) STRUCTURAL_PASS token at 6/8 threshold, (2) CANONICAL_MATCH_PASS token only at 8/8, (3) Explicitly emit which 2 terrains mismatch and why as part of the token metadata. Also check for any "Win/Lose" terminology and replace with SG/EE.
```

### AG-6

```
CODEX RATCHET ENGINE — system_v4/probes/run_all_sims.py has a SIM_FILES list that determines which SIMs get executed. There may be *_sim.py files in system_v4/probes/ not in that list.

List all *_sim.py files in system_v4/probes/. Compare to the SIM_FILES list in run_all_sims.py. Add any missing files. Run: python3 system_v4/probes/run_all_sims.py to verify all execute. Report how many new tokens were added.
```

### AG-7

```
CODEX RATCHET ENGINE — system_v4/skills/evidence_witness_bridge.py converts probe EvidenceTokens from unified_evidence_report.json into witness records.

Read: system_v4/skills/evidence_witness_bridge.py. Run the bridge. Then audit: does every token in system_v4/probes/a2_state/sim_results/unified_evidence_report.json get a corresponding witness? Check for: missing witnesses, orphan witnesses, KILL witnesses properly tagged as NEGATIVE. Write: system_v4/a2_state/audit_logs/A2_BRIDGE_AUDIT__v1.md
```

### AG-8

```
CODEX RATCHET ENGINE — The probe evidence graph (system_v4/a2_state/graphs/probe_evidence_graph.json) is materialized from the unified evidence report by probe_graph_materializer.py.

Read: system_v4/a2_state/graphs/probe_evidence_graph.json and system_v4/probes/a2_state/sim_results/unified_evidence_report.json. Cross-check: Do node counts match? Do edges match token counts? Are ALL KILL tokens represented as KILL-status nodes? Are there orphan tokens with no edge? Write: system_v4/a2_state/audit_logs/A2_GRAPH_CROSSVAL__v1.md
```

### AG-9

```
CODEX RATCHET ENGINE — system_v4/skills/intent-compiler/dna.yaml has a graveyard section with known_open_kills (5 tokens) and resolved_kills (3 tokens).

Read dna.yaml graveyard section. Read system_v4/probes/a2_state/sim_results/unified_evidence_report.json. Verify: every token in resolved_kills actually PASSes now. Every token in known_open_kills actually KILLs. If any mismatch, fix dna.yaml. Write: system_v4/a2_state/audit_logs/A2_GRAVEYARD_AUDIT__v1.md
```

### AG-10

```
CODEX RATCHET ENGINE — system_v4/skills/intent-compiler/constraint_manifold.yaml defines the constraints the engine must satisfy. Each constraint should have SIM coverage.

Read constraint_manifold.yaml. Read system_v4/probes/a2_state/sim_results/unified_evidence_report.json. For each constraint, verify current SIM coverage. Flag any constraint with no SIM or with a KILL-producing SIM. Propose new SIMs for uncovered constraints. Write: system_v4/a2_state/audit_logs/A2_MANIFOLD_GAP__v1.md
```

### AG-11

```
CODEX RATCHET ENGINE — SIMs in system_v4/probes/. Navier-Stokes has multiple SIM files.

Read: system_v4/probes/navier_stokes_complexity_sim.py (emits NO_TOKENS). Read: system_v4/probes/navier_stokes_qit_sim.py (2 PASS). Check if system_v4/probes/navier_stokes_formal_sim.py exists. Fix navier_stokes_complexity_sim to emit EvidenceTokens. Consolidate: each N-S SIM should emit distinct tokens covering different aspects of the Navier-Stokes claim.
```

### AG-12

```
CODEX RATCHET ENGINE — Full system health check. Run these 4 commands in order:
1. python3 system_v4/probes/run_all_sims.py
2. python3 system_v4/skills/probe_graph_materializer.py
3. python3 system_v4/skills/evidence_witness_bridge.py
4. python3 system_v4/skills/intent-compiler/heartbeat_daemon.py --no-codex

Collect all outputs. Write: system_v4/a2_state/audit_logs/A2_FULL_SYSTEM_HEALTH__v1.md with: total token inventory, KILL analysis with root causes, graph node/edge stats, workstream status, constraint manifold coverage percentage.
```

---

# NOTEBOOKLM PROMPTS (20)
Each is short and self-contained. Fire in sequence.

---

### NLM-5A

```
BANNED: "Axis/Axes/AXIS", "Win/Lose" (use SG/EE), "FeTi/TeFi/NiTe/FeSi" (Jungian MBTI). Output the full replacement table.
```

### NLM-5B

```
Audit every claim vs current state: 94 PASS, 5 KILL. Changes: world_model 2K→2P, gain_cal false-PASS→honest 2K, demon K→P, Ti now context-aware. For each: formula, SIM, PASS/KILL/UNTESTED, root cause if KILL.
```

### NLM-5C

```
64-stage engine has ALL-NEGATIVE ΔΦ (≈ -0.41) across full γ_sub sweep. What is ACTUALLY wrong? A) Lindblad not energy-selective, B) wrong operator ordering, C) γ should be per-stage, D) something else? Cite source files.
```

### NLM-5D

```
NLM-19 proposed "Axiom of Retrocausality" as 4th axiom. Is it consistent with F01, N01, CAS04? Does it solve Bridge T or rename it? What would a SIM test look like?
```

### NLM-5E

```
List every concept in corpus with a mathematical claim but NO SIM. Table: Concept | Claim | Proposed SIM name | Priority 1-5
```

### NLM-5F

```
Ti eigenbasis audit: which existing SIMs use computational basis when they should use eigenbasis? NLM-17: isothermal/-Ti = computational, adiabatic/+Ti = eigenbasis. List each SIM and whether its Ti usage is correct.
```

### NLM-5G

```
Engine stage ordering analysis. 8-stage cycle: S1:-Ti, S2:+Te, S3:-Fi, S4:+Fe, S5:+Ti, S6:-Te, S7:+Fi, S8:-Fe. Is this optimal? Could reordering fix the γ calibration KILL?
```

### NLM-5H

```
Lindblad operator structure. Current Fe uses d(d-1) operators (all off-diagonal). Should it be energy-selective? What is theoretical minimum needed?
```

### NLM-5I

```
12-bit mirror validity. Bits 1-6 = control surface. Bits 7-12 = claimed mirror. Derivable from F01+N01? Or another CHOSEN structure like Bridge T?
```

### NLM-5J

```
Riemann-primes feasibility. π(d)~d/ln(d) from F01+N01. Formally possible? What would a CPTP prime sieve look like? What spectral structure maps to Riemann zeros?
```

### NLM-5K

```
Consciousness claims. Current: 2 PASS. What do the tokens actually prove? Is autopoietic fixed point real? What's missing for STRUCTURAL?
```

### NLM-5L

```
Alignment claims. Current: 2 PASS. What do the tokens prove? Is solvency operator well-defined? What's missing for STRUCTURAL?
```

### NLM-5M

```
Abiogenesis. The SIM KILLs (NO_SPONTANEOUS_LIFE). What is theoretical path from I/d to structure? Does dual-loop predict spontaneous organization?
```

### NLM-5N

```
Yang-Mills mass gap in QIT framework. Current: 2 PASS (basic). What would STRUCTURAL require? How does finite-d spectral gap map to Yang-Mills mass gap? Real mapping or analogy?
```

### NLM-5O

```
Chemistry bonding claims. Current: 3 PASS. 6-bit control surface producing bonding without 3D distance. What is the operator sequence for bond formation?
```

### NLM-5P

```
Quantum gravity. Current: 2 PASS. Holonomy → spacetime: real or circular? What observable distinguishes QIT-gravity from standard GR?
```

### NLM-5Q

```
World model FEP derivation. Now 2 PASS. Does Free Energy Principle emerge from CPTP framework? Is prediction error minimization a consequence of the ratchet?
```

### NLM-5R

```
Scientific method Berry phase. Current: 3 PASS. How does geometric phase map to paradigm shifts? Is Kuhn's structure a topological invariant of the engine?
```

### NLM-5S

```
Cross-domain patterns. Which mathematical structures appear in 3+ domain SIMs? Table: Structure | Domains | Significance
```

### NLM-5T

```
Full integrity report. 33 SIMs, 99 tokens, 94P/5K. Overall confidence? 5 highest-leverage improvements? What breaks if any of the 5 KILLs cannot be fixed?
```

---

**Fire order**: NLM-5A first → then all 15 Pro + 12 AG simultaneously → NLM 5B–5T in sequence.
