# AGM-08 Controller Closeout

**Date:** 2026-03-30
**Source returns read:** AGM-01 through AGM-07
**Controller stance:** No smoothing. Contradictions reported as contradictions.

---

## Most Important Earned Result

**LR-Chirality (Weyl asymmetry) is the sole confirmed mechanical lever on the bridge.**

AGM-01 established that Same-Run Coupling and Cross-Temporal Dominance are real — i.e., something non-trivial exists between $L(t)$ and $R(t+1)$ when measured against independent-run baselines. AGM-07 then settled the mechanism: Phase 5C showed that cross-temporal retro-weighting is noise across all 6 tested configurations (0/6 signal). The only surviving earned lever is LR-chirality (Weyl asymmetry), not temporal stride or retro-exponential decay. AGM-04 independently certified that point-reference cleanly separates fiber from base geometry (near-zero $I_{AB}$ on fiber loops, 0.48–0.67 on base loops), confirming that real geometrical differences exist in the engine that a bridge *could* track — but only if it uses the chirality axis, not the temporal one.

**Consequence:** The constructive winner's current name ("cross-temporal chiral retro-weighted") is partially a misnomer. The "retro-weighted" is noise. The "chiral" is the load-bearing part. The two have not been separated at the repo level as of AGM-07.

---

## Most Important Surviving Objection

**There is no candidate — constructive or earned — that achieves non-zero MI while preserving the engine's physical marginals. The marginal-compatible family collapses to the product state.**

This is not a gap in the sweep. AGM-02 is definitive: Phase 4 exhausted direction, stride, and weighting degrees of freedom across 69 candidates. Phase 5A independently confirmed from the optimization side (Nelder-Mead, 15 restarts, 12 blocks) that the maximum-MI state compatible with the engine marginals is the product state ($\approx 10^{-15}$ preserving MI). AGM-01 named the same problem: Phase 5A runs certify that the ~1.5-bit constructive winner is entirely Bell-injected — it captures information *by pulling marginals away from the engine's actual state*.

AGM-03 translates this into doctrine terms: the constructive winner fails three legitimacy tests simultaneously — marginal destruction, cut blindness, and shell disconnect. AGM-05 agrees: no shell-based candidate has found a marginal-preserving, high-MI state.

The objection is not falsified by the scale of the constructive MI number. The objection is: the number is measuring Bell injection, not engine physics.

---

## What Changed in the Search Space

1. **The temporal lever is closed.** Before this wave, "retro-weighted" was co-equal with "chiral" in the constructive winner label. After AGM-07 (Phase 5C), the temporal lever is noise. The only remaining executable direction is Weyl/chirality-indexed.

2. **The matched-marginal lane is closed on the current carrier.** AGM-02 eliminated this possibility. It is not a gap to fill with more Phase 4 variants — it is a structural property of the engine's marginals. The only way to re-open the lane is to change the carrier (different torus, initial conditions, or stage parameters) and re-run Phase 5A on the new carrier before claiming anything.

3. **Shell doctrine is now formally typed but still not executable.** AGM-05 established the Typed Shell Cut Contract $(r, w_r, A_r|B_r, \rho_r)_r$. This is clarifying progress — shell now owns a formal contract rather than a label. But AGM-03 and AGM-05 together confirm that no sim result satisfies this contract with physical marginals. Shell retains doctrinal primacy and loses executable primacy.

4. **The authority surface is clean.** AGM-06 confirmed zero live overclaims in the packet graph. Every "strongest constructive bridge family" line is negated by a co-located kill statement in the same file. The residual risk is drift from future readers who see the positive phrase without reading the adjacent negation.

5. **Repo and brain are asymmetrically ahead.** AGM-07 quantifies the gap: repo is ahead on contract typing and auth-guard discipline; brain is ahead on falsification of temporal lever, JK Fuzz operationalization (Path Entropy $H_{path}$ over the Kraus-history ensemble), FEP mapping (67/33 = Prior/Likelihood), and the identity axiom foundation for the bipartite cut.

---

## Best Next Exact Run

**Phase 5D: Maximum Earned Information Search (marginal-restricted), on Weyl/chirality-indexed states only.**

The design from AGM-01 is still the correct target: search for $\rho_{AB}$ in the set where $d(\rho_{AB}, \rho_A \otimes \rho_B) < \epsilon$ (strict marginal-proximity budget) and maximize correlation to the geometry ramp — not to raw MI. The modification required by the AGM-07 result: restrict the search family to chirality-indexed (Weyl-asymmetric) states, not temporal stride variants. The cross-temporal retro-weighted family is not worth retesting. If Phase 5D returns a null winner (product state again), it closes the "Maximum Earned Information" lane and the controller must decide whether to change the carrier.

**What this run must report:**
- `max_earned_MI` under $\epsilon$-marginal constraint for the Weyl/chirality family
- `marginal_deviation` for all candidates (must travel with MI — not separated as in past reporting)
- `best_source` label (product_seed vs non-trivial basin)
- If `best_source = product_seed` again: carrier-swap decision point must be logged explicitly

**Prerequisite before running:** Execute the Terminology Purge flagged in AGM-07 item 1 — rename the constructive winner from "retro-weighted" to "Chirality/Weyl-weighted" in the repo STATE_CARD and ACTIVE_PACKET_INDEX before the next sim run, so that the Phase 5D result lands in a packet that uses the correct lever name.

---

## What Is Still Definitely Not Solved

1. **Final Canon Xi.** The engine has no earned fixed-marginal closure. The winning constructive bridge family (`Xi_hist`) is the strongest live executable but is not a legitimate bipartite state $\rho_{AB}$ grounded in the engine's physical marginals. This is the primary open wall. It is not a naming problem. It is a physics problem.

2. **Shell Executable Closure.** Shell owns doctrine and now owns a typed contract. Shell does not own a sim-verified, marginal-preserving bridge. The "History-Shell Hybridization" path ($\Xi_\text{shellhist}$) is proposed but untested. The "core-vs-interface" micro-split is ranked but not closed algebraically.

3. **Canonical Xi Weighting Coefficient.** AGM-01 names the problem directly: the winning family uses $\alpha=0.1$ for retro-weighting, justified only by "it looks better." With the temporal lever now confirmed as noise (AGM-07), $\alpha$ may be irrelevant — but no principled derivation of the chirality-weighting parameter exists in its place.

4. **i-Scalar Selection.** AGM-07 lists the 4-part i-scalar functional sweep (Options A/B/C/D) for the Universal Clock monotone as a pending controller decision. No probe in this wave touched it.

5. **Doctrine Promotion of FEP Cosmology.** The "FEP as literal cosmology" (Prediction-First, 67/33 = Prior/Likelihood) framing exists only in the brain synthesis. Whether to promote it to the `AXIS0_CURRENT_DOCTRINE_STATE_CARD` as a primary anchor remains an open controller call. It was not evaluated as a probe; it arrived as a brain-side synthesis. Promoting it without a targeted adversarial test would violate the earned-vs-constructed standard this wave was designed to enforce.

6. **Attractor Proximity.** AGM-01's Still Open item remains open: the earned cross-temporal signal ($L(t) \otimes R(t+1)$ delta) has not been proven to be a "compression-from-future" attractor. It could still be a sophisticated artifact of the $t \to t+1$ stride. Phase 5D will not resolve this unless the marginal-restricted search finds a non-trivial winner.
