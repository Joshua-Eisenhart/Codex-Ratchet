# AXIS STRUCTURE EMPIRICAL AUDIT

**Date:** 2026-03-27  
**Method:** Hilbert-Schmidt displacement overlap across d={2,4,8,16,32}, 100-200 trials per test  
**Sims:** `sim_axis_anti_conflation.py`, `sim_axis_exploration_suite.py`, `sim_missing_axis_search.py`, `sim_axis7_deep_test.py`, `sim_broad_axis_search.py`, `sim_axis_7_12_audit.py`

---

## 1. Base Axes 0-6: What Survived

| Axis | Name | ± Labels | Math | Status |
|---|---|---|---|---|
| 0 | Coarse-graining | fine / coarse | Fiber averaging, sub-block conditioning | ✅ Verified |
| 1 | Dissipation class | open / closed-channel | CPTP vs Unitary | ✅ |
| 2 | Boundary | flux / path | Eulerian vs Lagrangian | ✅ |
| 3 | Chirality | inward / outward | Hopf fiber phase `e^{±iθ}` | ✅ **FIXED** |
| 4 | Composition order | constraint / release-first | B∘A vs A∘B | ✅ |
| 5 | Generator algebra | gradient / spectral | FGA vs FSA | ❌ **= Axis 1** |
| 6 | Action side | pre / post | Aρ vs ρA | ✅ |

### Mergers
- **Ax1 ≈ Ax5**: overlap **0.9997**. "Channel class" and "algebra class" are the same degree of freedom. One must be dropped.

### Fixes
- **Ax3 must use `e^{±iθ}` (Hopf fiber phase)**, NOT `±G` (generator sign). With `±G`, Ax3 conflates with Ax6 at **0.71 overlap**. With `e^{±iθ}`, overlap drops to **0.000**.

### Anti-Conflation Labels (verified orthogonal)
- Ax0: **fine/coarse** — NOT left/right, NOT in/out
- Ax3: **inward/outward** — NOT left/right
- Ax6: **pre/post** — NOT left/right Weyl

---

## 2. Commutator Axes 7-12: What Survived

| Axis | Construction | Norm | Redundancy | Status |
|---|---|---|---|---|
| A7 | [A1, A3] | 0.360 | Independent | ✅ |
| A8 | [A1, A6] | 0.394 | ≈ A11 (overlap 0.850) | ⚠️ |
| A9 | [A3, A6] | 0.172 | **≡ A10** (overlap **1.000**) | ❌ |
| A10 | [A4, A6] | 0.172 | **≡ A9** (overlap **1.000**) | ❌ |
| A11 | [A2, A6] | 0.506 | ≈ A8 (overlap 0.850) | ⚠️ |
| A12 | [A1, A5] | 0.451 | Independent | ⚠️ suspicious |

### Collapses
- **A9 ≡ A10**: overlap 1.000, same norm. [A3,A6] and [A4,A6] produce identical displacements. One is made up.
- **A8 ≈ A11**: overlap 0.850. [A1,A6] and [A2,A6] nearly the same — the Ax1/Ax2 difference is weak inside commutators.

### After dedup: 4 independent commutator directions (A7, A8≈A11, A9≡A10, A12)

---

## 3. New Axis Candidates

Tested 15 QIT operations. After dedup, 1 strong new candidate:

| Candidate | Residual | Max Overlap (base) | Max Overlap (commutator) | Status |
|---|---|---|---|---|
| **measurement_basis** | **0.946** | 0.23 (Ax0) | **0.132** | 🔥 **Genuinely new** |
| non_markovianity | 0.845 | 0.50 (Ax0) | 0.299 (A11) | ⚠️ Partially in commutator space |

### measurement_basis properties
- **Residual scales UP with d**: 0.53 → 0.87 → 0.94 → 0.97 → 0.99 (d=2→32)
- **0.000 overlap with Ax3 and Ax4**
- **Stable**: 0.941 ± 0.002 across 5 independent seed sets
- **Not any single Jungian operator**: Ti=0.34, Fe=0.31, Te=0.24, Fi=0.39
- **NOT in commutator space**: max overlap 0.132 with any commutator axis
- **Math**: z-basis dephasing vs Fourier-basis dephasing (frame selection)
- **No Jungian label yet** — needs engine grounding before assignment

---

## 4. Definitive Independence Matrix (`f034d015`)

Full 11×11 overlap matrix at d=8, 150 trials. **8 independent clusters:**

| Cluster | Axes | Type |
|---|---|---|
| 1 | **Ax0 ≈ Ax1 ≈ Ax2** (overlap 0.54–0.77) | Base — may be one compound axis |
| 2 | **Ax3** (U vs U*, max overlap 0.38) | Base — chirality, marginal but real |
| 3 | **Ax4** (B∘A vs A∘B, zero norm issue) | Base — maps nearly commute at d=8 |
| 4 | **Ax6** (Aρ vs ρA, max overlap 0.39) | Base — action side |
| 5 | **A7=[A1,A3]** (max overlap 0.48) | Commutator — independent |
| 6 | **A8=[A1,A6] ≈ A12=[A1,A5]** (overlap 0.57) | Commutator — cluster of 2 |
| 7 | **A9=[A3,A6]** (max overlap 0.33) | Commutator — independent |
| 8 | **measurement_basis** (max overlap 0.25) | NEW — cleanest axis in the system |

### Formulation Notes
- **Ax3**: Must use U vs U* (Weyl conjugate), NOT `e^{±iθ}` (global phase cancels in ρ→UρU†)
- **Ax4**: zero norm at d=8 because dephasing and amplitude damping nearly commute. Needs stronger non-commuting map pair or may only activate at small d.
- **Ax0/Ax1/Ax2 cluster**: fine-graining, dissipation, boundary all share the "how much information is lost" direction. May be aspects of a single metastructure.

---

## 5. Dimension Scaling (`42032863`)

Tested at d={2,4,8,16,32}:

| Question | d=2 | d=8 | d=32 | Answer |
|---|---|---|---|---|
| **Ax0/Ax1/Ax2 split?** | cluster (0.57) | cluster (0.66) | cluster (0.56) | **NEVER SPLITS** — one compound axis |
| **Ax3 get clean?** | dirty (0.49) | dirty (0.38) | dirty (0.34) | **Slowly improving** but never clean |
| **Ax4 activate?** | active (0.014) | zero (0.005) | zero (0.001) | **VANISHES at d≥8** |
| **meas_basis stable?** | dirty (0.52) | OK (0.25) | clean (0.12) | **Gets cleaner with d** |

---

## 6. Revised Axis Count

| Layer | Claimed | Verified Independent |
|---|---|---|
| Base (0-6) | 7 | **~3** (Ax0/1/2=one, Ax1=Ax5, Ax4 vanishes) |
| Commutator (7-12) | 6 | **~3** (A9≡A10, A8≈A11≈A12) |
| New candidates | 0 | **1** (measurement_basis) |
| **Total** | **13** | **~5-7 real axes** |

---

## 7. Open Questions for Engine

1. **What is measurement_basis in the engine?** Frame/basis selection — no Jungian label yet.
2. **Should Ax0/Ax1/Ax2 collapse to one axis?** d-scaling says YES — they never split.
3. **Is Ax4 real at d>2?** d-scaling says NO — it vanishes. May only matter at qubit level.
4. **Why does Ax3 stay dirty (0.34)?** Persistent overlap with Ax1. Chirality and dissipation may share structure.
5. **Which commutator axes matter for engine dynamics?** A7=[A1,A3] is the strongest independent one.

---

## 8. Sim Files (all in `system_v4/probes/`)

| File | What it tests |
|---|---|
| `sim_axis_anti_conflation.py` | Pairwise overlap of 7 axes, danger pairs |
| `sim_axis_exploration_suite.py` | Ax1/Ax5 redundancy, Ax3/Ax6 disentanglement, torus η |
| `sim_missing_axis_search.py` | 7 candidates for missing axis |
| `sim_axis7_deep_test.py` | Deep validation of measurement_basis + squeezing |
| `sim_broad_axis_search.py` | 15 candidates broad search |
| `sim_axis_7_12_audit.py` | Commutator axes redundancy + candidate mapping |
| `sim_axis_independence_matrix.py` | **Definitive 11×11 overlap matrix** |

| `sim_axis_dimension_scaling.py` | **d-scaling of 7 axes at d=2,4,8,16,32** |

## 9. Results Files (all in `system_v4/a2_state/sim_results/`)

| File | Content |
|---|---|
| `axis_anti_conflation_results.json` | 7×7 overlap + danger pairs |
| `axis_exploration_suite_results.json` | Ax1/Ax5, Ax3/Ax6 disentangle, torus η |
| `missing_axis_search_results.json` | 7 candidates residual analysis |
| `axis7_deep_test_results.json` | Deep validation metadata |
| `broad_axis_search_results.json` | 15 candidates full results |
| `axis_7_12_audit_results.json` | Commutator norms, overlap, candidate mapping |
| `axis_independence_matrix.json` | **Definitive 11×11 matrix + clusters** |
| `axis_dimension_scaling.json` | **d-scaling tracking for all 4 questions** |
