# Constraint Manifold Gap Analysis (v1)

## Objective
Cross-reference the 16 core constraints (C1-C8, X1-X8) defined in `constraint_manifold.yaml` against the active telemetry produced by `unified_evidence_report.json`. Identify constraints with missing (`NO SIM`) or failing (`KILL`) coverage and propose tactical replacements.

## Structural Context: The IGT Halt
Per a direct user override (`stop with igt. don't do igt until the system stabalizes and is correct. it only makes drift`), the simulations `igt_game_theory_sim.py` and `igt_advanced_sim.py` were halted and excised from the Unified SIM pipeline. 
**Consequently, any constraint relying entirely on IGT mathematics has immediately lost its test coverage.**

---

## Active Coverage Map (11/16 Verified)

| ID | Constraint Definition | SIM Coverage | Telemetry Status |
|----|-----------------------|--------------|------------------|
| **C1** | Finitude | `foundations_sim.py` | **PASS** |
| **C2** | Noncommutation | `foundations_sim.py`, `topology_operator_sim.py` | **PASS** |
| **C3** | CPTP Admissibility | `topology_operator_sim.py` | **PASS** |
| **C4** | Operational Equivalence | `constraint_gap_sim.py` | **PASS** |
| **C5** | Entropy Monotonicity | `foundations_sim.py`, `math_foundations_sim.py` | **PASS** |
| **C7** | Spinor Periodicity | `full_8stage_engine_sim.py` | **PASS** |
| **C8** | Ratchet Gain | `constraint_gap_sim.py` | **PASS** |
| **X1** | GT Isolation | `constraint_gap_sim.py` | **PASS** |
| **X6** | Refinement Noncommutative | `constraint_gap_sim.py` | **PASS** |
| **X7** | Finite Stability | `constraint_gap_sim.py` | **PASS** |
| **X8** | Holodeck Fixed Point | `nlm_batch2_sim.py` | **PASS** |

---

## Gap Analysis: Orphaned Constraints (5/16 Uncovered)

### 1. C6_dual_loop_requirement
* **Statement**: Sustainable evolution requires both deductive (FeTi) and inductive (TeFi) loops.
* **Former Coverage**: `igt_advanced_sim.py` (Halted)
* **Status**: **NO SIM**
* **Proposed Replacement**: Build `structural_dual_loop_sim.py`. Evolve the 8-stage dual loop exclusively against an active thermal bath without injecting game theory labels (Win/Lose) to prove survivorship purely via entropic decay avoidance.

### 2. X2_chirality_matters
* **Statement**: T-first and F-first orderings produce measurably different outcomes.
* **Former Coverage**: `igt_game_theory_sim.py` (Halted)
* **Status**: **NO SIM**
* **Proposed Replacement**: Expand `axis0_correlation_sim.py` or `topology_operator_sim.py` to test operator non-commutativity sequentially over a 64-stage array, comparing [Te,Fi] vs [Fi,Te] eigenvalue distributions. 

### 3. X3_attractor_is_nash
* **Statement**: The engine's attractor state is a Nash equilibrium.
* **Former Coverage**: `igt_game_theory_sim.py` (Halted)
* **Status**: **NO SIM** (Falsified/Halted Concept)
* **Proposed Replacement**: *Deprecate constraint.* As requested, mapping QIT attractors to Nash Equilibriums forces gamified jargon. The constraint should either be renamed `X3_attractor_is_fixed_point` and mapped to `full_8stage_engine_sim.py` or permanently struck from the manifold.

### 4. X4_structure_saturation_stalls
* **Statement**: Agents exclusively seeking structure gain stall due to entropic debt accumulation.
* **Former Coverage**: `igt_advanced_sim.py` (Halted)
* **Status**: **NO SIM**
* **Proposed Replacement**: Build `entropic_debt_stall_sim.py`. Inject a strictly structurally-greedy projection loop and empirically measure the Landauer work scalar until the state space locks (`trace(rho) = 1` but operations `S(E(rho)) - S(rho) = 0`).

### 5. X5_irrational_escape
* **Statement**: Temporary entropy increase enables escape from local minima.
* **Former Coverage**: `igt_advanced_sim.py` (Halted)
* **Status**: **NO SIM**
* **Proposed Replacement**: Map to the existing `sim_moloch_trap_field.py`, expanding the Moloch escape theorem to formally capture phase-space escapes via entropy dilution.
