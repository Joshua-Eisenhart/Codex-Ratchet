# A2_BRIDGE_T_AUDIT__v1

**Generated**: 2026-03-23T16:12:00-07:00  
**Auditor**: AG-02 (Antigravity)  
**Fuel**: NLM-15, NLM-19 (A2_NLM_BATCH4_FULL_SYNTHESIS__v1.md)  
**SIMs Executed**: `rock_falsifier_sim.py`, `rock_falsifier_enhanced_sim.py`

---

## 1. Question Under Test

> Does the rock ever win?

Bridge T (Teleological Weighting / "God" Attractor) is the single biggest unproven ontological assumption in the system (NLM-15). The hypothesis: **maximizing solvency FORCES increasing complexity**. If a low-action "rock" (near-identity channel, E_agent ≈ I) outperforms the full 8-stage engine under environmental volatility, the entire "solvency implies complexity" hypothesis is **KILLED**.

NLM-19 further clarifies: Bridge T **cannot** be derived from F01+N01+CAS04. It is strictly CHOSEN — a 4th axiom (Axiom of Retrocausality). This audit tests whether the empirical evidence supports the choice.

---

## 2. SIM 1: Rock Falsifier (Original)

**File**: `system_v4/probes/rock_falsifier_sim.py`  
**Config**: d=4, horizon=200, 10 trials, regime shifts every 50 steps  
**Rock**: Near-identity channel (0.99ρ + 0.01·I/d)  
**Engine**: Full 8-stage cycle (all operators, same d=4)

### Results by Volatility

| Volatility | Rock Avg Solvency | Engine Avg Solvency | Winner |
|:-----------|:------------------|:--------------------|:-------|
| 0.05       | 0.0480            | 0.3448              | ENGINE |
| 0.15       | 0.0000            | 0.3476              | ENGINE |
| 0.30       | 0.0000            | 0.3527              | ENGINE |
| 0.50       | 0.0000            | 0.3439              | ENGINE |

### Observations

- **The rock NEVER wins.** Not even at the lowest volatility (0.05).
- Rock solvency collapses to 0.0 at volatility ≥ 0.15 (rock dies — hits stall threshold).
- Engine solvency is remarkably stable at ~0.345 across ALL volatility levels.
- The expected crossover (rock wins calm, engine wins volatile) did NOT occur.
- SIM verdict: `COMPLEXITY_BIAS` — engine wins even in calm environments.

### Evidence Token

```
token_id:  E_SIM_ROCK_FALSIFIER_COMPLEXITY_BIAS
sim_spec:  S_SIM_ROCK_FALSIFIER_V1
status:    PASS
value:     0.3448
```

---

## 3. SIM 2: Enhanced Rock Falsifier (Bridge T Test)

**File**: `system_v4/probes/rock_falsifier_enhanced_sim.py`  
**Config**: Rock d=2, Engine d=4, horizon=100, **1000 trials**, regime shifts every 25 steps  
**Rock**: d=2 near-identity channel (no dual loop, minimal action)  
**Engine**: d=4 full 8-stage cycle (dual loop, all operators)  
**Complexity Costs**: Rock=0.01, Engine=0.32 (Landauer proxy: log2(d²) × 8 × 0.01)

### Aggregate Results

| Metric                | Engine     | Rock       |
|:----------------------|:-----------|:-----------|
| Wins                  | 1000       | 0          |
| Win Rate              | 100.0%     | 0.0%       |
| Ties                  | —          | 0          |
| Avg Final Solvency    | 0.3542     | 0.0000     |
| Survival Rate         | 100.0%     | 0.0%       |

### Intensity Bin Breakdown

| Bin    | Trials | Engine Win Rate | Rock Win Rate |
|:-------|:-------|:----------------|:--------------|
| Medium | 1000   | 100.0%          | 0.0%          |

### Per-Trial Detail (Sample)

All 50 sampled trials show the same pattern:
- Rock: `rock_alive = false`, `rock_final_solvency = 0.0`
- Engine: `engine_alive = true`, `engine_final_solvency ∈ [0.318, 0.460]`
- Engine competence: ~0.267–0.278 (despite 32× higher complexity cost)
- Rock competence: ~0.001–0.066 (even with near-zero complexity cost)

### Evidence Token

```
token_id:  E_SIM_ROCK_FALSIFIER_ENHANCED_OK
sim_spec:  S_SIM_ROCK_FALSIFIER_ENHANCED_V1
status:    PASS
value:     1.0
verdict:   SURVIVES
```

---

## 4. Verdict: Does the Rock Ever Win?

### **NO. The rock never wins. Not once across 1,040 total trials.**

| SIM | Trials | Rock Wins | Engine Wins | Survival |
|:----|:-------|:----------|:------------|:---------|
| Original (d=4 vs d=4)   | 40 (4 volatility × 10) | 0 | 40 | Rock dies at vol ≥ 0.15 |
| Enhanced (d=2 vs d=4)   | 1000                   | 0 | 1000 | Rock: 0%, Engine: 100% |

The rock doesn't just lose — it **dies**. In every trial of the enhanced sim, the rock's solvency drops below the stall threshold (0.01) before the horizon. The rock is not merely outperformed; it is **extinguished**.

---

## 5. Bridge T Status

### SURVIVES

Bridge T — the teleological weighting hypothesis that solvency forces complexity — is empirically supported by both SIMs. The evidence is stronger than expected:

1. **No crossover exists.** The original sim expected the rock to win in calm environments (complexity tax). It doesn't. The engine dominates at all volatility levels.

2. **The margin is not close.** Engine avg solvency ~0.354 vs Rock ~0.000. The rock doesn't gradually lose — it collapses entirely.

3. **Even with generous complexity accounting**, the engine wins. Despite 32× higher Landauer cost (0.32 vs 0.01), engine competence (~0.27) vastly exceeds rock competence (~0.01).

4. **100% survival rate for the engine across 1000 random perturbation sequences.** The 8-stage cycle is not just better — it is categorically robust.

### Caveats (per NLM-15 / NLM-19)

> [!WARNING]
> Bridge T is CHOSEN, not derived. These SIMs provide strong **empirical** support, but Bridge T remains an axiom (the 4th: Axiom of Retrocausality). The SIMs show the engine outperforms the rock, but they do NOT prove that solvency *logically forces* complexity. There may exist agents between "rock" and "full 8-stage engine" that perform well with less complexity. The dichotomous test (rock vs full engine) does not explore the intermediate space.

### Three remaining gaps flagged by NLM-15:
1. **12-Bit Mirror (Axes 7-12)**: Never simulated, flagged as "enormous inferential leap"
2. **Primes → Riemann**: Cannot be derived from F01+N01 (OPEN KNOT)
3. **γ Calibration**: Exact operator strengths unsolved, causes 64-stage KILL

---

## 6. Evidence Ledger

| Token ID | SIM Spec | Status | Value | Kill Reason |
|:---------|:---------|:-------|:------|:------------|
| `E_SIM_ROCK_FALSIFIER_COMPLEXITY_BIAS` | `S_SIM_ROCK_FALSIFIER_V1` | PASS | 0.3448 | — |
| `E_SIM_ROCK_FALSIFIER_ENHANCED_OK` | `S_SIM_ROCK_FALSIFIER_ENHANCED_V1` | PASS | 1.0 | — |

---

## 7. Residual Questions for Future Audits

1. **Intermediate agents**: What about a d=3 agent with 4 stages? Where does complexity become worth its cost?
2. **Adversarial shocks**: Current shocks are stochastic. What about adversarially chosen shock sequences targeting the engine's weaknesses?
3. **Longer horizons**: At horizon=10,000+, does the engine's solvency remain stable or does it eventually drift?
4. **Multiple attractors**: The engine's sigma_attractor is fixed. What if the environment has shifting attractors?
