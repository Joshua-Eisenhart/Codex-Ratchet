# MCT Advisory Crosscheck — 2026-06-10
# mct_dynamic_admissibility_packet_v0

Models: grok-4.3 (G), gemini-3.1-pro-preview (GP), gemini-2.5-flash (GF)
Blind sheet: mct_blind_expected_20260610.md

---

## 1. Five-row verdict table

| Problem | grok-4.3 | gemini-3.1-pro | gemini-2.5-flash | vs Blind |
|---|---|---|---|---|
| P1 rho form + fiber direction | AGREE | AGREE | AGREE | All 3 models agree with blind |
| P2 quotient class counts | DIVERGE | DIVERGE | AGREE | grok-4.3 and gemini-3.1-pro diverge from blind; gemini-2.5-flash agrees |
| P3 b0 values + sample counts | AGREE | AGREE | AGREE | All 3 models agree with blind |
| P4 commutator classification (all 6 pairs) | DIVERGE (pair c only) | AGREE | AGREE | grok-4.3 diverges on pair (c); gemini-3.1-pro and gemini-2.5-flash agree with blind |
| P5 fixture edge counts | AGREE (erase=4), AGREE (retain=8) | AGREE (erase=4), AGREE (retain=8) | AGREE (erase=4), DIVERGE (retain: 16 vs 8) | grok-4.3 and gemini-3.1-pro agree with blind on both; gemini-2.5-flash diverges on retain count |

---

## 2. Divergences — verbatim quotes and specific values

### P2 divergence: grok-4.3 and gemini-3.1-pro vs blind (and vs gemini-2.5-flash)

**grok-4.3 says:**
> "The three admissible values of η together with the four distinct values of χ mod π therefore produce exactly 12 distinct density matrices. Each such matrix is realized by precisely 384/12=32 samples (8 choices of φ, 2 sheets, and a factor-of-2 redundancy in the χ-grid). Hence the 384-sample set partitions into 12 equivalence classes of size 32 each. An additional probe that distinguishes the two sheets halves every class, yielding 24 classes of size 16."

**gemini-3.1-pro says:**
> "chi_j = 2πj/8 = πj/4 for j ∈ {0,1,...,7}. The off-diagonal phase term is e^{2i chi_j} = e^{iπj/2}. As j ranges from 0 to 7, this term cycles through 4 distinct values: 1, i, -1, -i. ... Number of distinct ρ matrices (equivalence classes) = 3 (from η) × 4 (from χ) = 12. Class size = 384 / 12 = 32. With sheet-separating probe: 12 × 2 = 24 classes of 16."

**gemini-2.5-flash says:**
> "Number of equivalence classes = (Number of eta values) * (Number of chi values) = 3 * 8 = 24 classes. Class size = (Number of phi values) * (Number of sheets) = 8 * 2 = 16 samples."

**Blind sheet says:**
> "Samples with different chi_j are not identified on the pinned 8-point grid because 2 chi_j has period 2pi and chi_j = j*pi/4 gives eight distinct e^{2i chi_j} values. ... Source-chart full-support density-only classes: 16 samples each: 2 sheets times 8 phi values."
> Class count: 24 (density-only, full support); 48 (with sheet-separating probe).

**Specific value that differs:**

The key arithmetic claim: how many distinct values does `e^{2i chi_j}` take on the 8-point grid `chi_j = 2*pi*j/8 = j*pi/4`, j=0..7?

- grok-4.3 and gemini-3.1-pro: `2*chi_j = j*pi/2`, which cycles with period 4, giving **4 distinct values** {1, i, -1, -i}. Claimed class count: **12 density-only, 24 with sheet probe**.
- gemini-2.5-flash and blind: treat all 8 chi_j values as giving **8 distinct** `e^{2i chi_j}`. Claimed class count: **24 density-only, 48 with sheet probe**.

This is a concrete arithmetic disagreement. The computation `e^{i*j*pi/2}` for j=0..7 does give period-4 cycling: j=0 gives 1, j=1 gives i, j=2 gives -1, j=3 gives -i, j=4 gives 1 again (same as j=0), etc. grok-4.3 and gemini-3.1-pro are arithmetically correct here. The blind sheet's claim that chi_j = j*pi/4 gives eight distinct `e^{2i chi_j}` values is not supported by the arithmetic; it appears to conflate the 8 distinct chi_j values with the 8 distinct `e^{i chi_j}` values (which do have period 8), not the 8 distinct `e^{2i chi_j}` values (which have period 4 on this grid).

**This divergence is preserved for the overseer. Both values are live readings: 12/32 and 24/16 for density-only (no sheet probe).**

---

### P4(c) divergence: grok-4.3 vs blind, gemini-3.1-pro, and gemini-2.5-flash

**grok-4.3 says:**
> "(c) Successive applications T_z∘T_x and T_x∘T_z produce distinct off-diagonal decay patterns, so the maps fail to commute (generically noncommuting)."

No explicit matrix computation is shown. The claim "distinct off-diagonal decay patterns" is asserted without derivation.

**Blind sheet says:**
> "Ti with Te: commute as Bloch-axis diagonal contractions: Ti scales (r_x,r_y) and preserves r_z; Te preserves r_x and scales (r_y,r_z), so the two diagonal scaling maps commute."

**gemini-3.1-pro says:**
> "Both operations are represented by diagonal matrices in the Bloch basis. Diagonal matrices always commute."

**gemini-2.5-flash shows explicit matrix multiplication:**
> "M_{T_z} M_{T_x} = diag(γ, γ², γ). M_{T_x} M_{T_z} = diag(γ, γ², γ). Since M_{T_z} M_{T_x} = M_{T_x} M_{T_z}, they commute."

**Specific value that differs:** grok-4.3 claims T_z and T_x are **generically noncommuting**. All other models (blind + gemini-3.1-pro + gemini-2.5-flash) classify them as **commuting**. The gemini-2.5-flash explicit matrix product confirms commutativity by direct calculation. grok-4.3's "distinct off-diagonal decay patterns" rationale is not derived and appears incorrect given that both operators are diagonal in the Bloch basis.

**This divergence is preserved for the overseer. grok-4.3 is isolated on this point; three independent sources converge on commuting.**

---

### P5(c) divergence: gemini-2.5-flash vs blind, grok-4.3, and gemini-3.1-pro

**gemini-2.5-flash says:**
> "If self-loops are retained and counted as edges, we simply count the total number of edges in the multiset E_3. From part (a), E_3 contains 16 edges (8 from the E_0 part of E_2, and 8 from the DeltaE+ part of E_2). There are 16 edges remaining."

**grok-4.3 says:**
> "Retaining self-loops yields the eight distinct edges (0,0),(1,1),(2,2),(3,3),(0,1),(1,2),(2,3),(3,0)."

**gemini-3.1-pro says:**
> "Keeping the self-loops adds them to the set of unique edges: {(0,1),(1,2),(2,3),(3,0),(0,0),(1,1),(2,2),(3,3)}. Answer: 8 distinct edges."

**Blind sheet says:**
> "|E_3| = 8 under self_loop_policy = retain."

**Specific value that differs:** gemini-2.5-flash gives retain count = **16** (treating E_3 as a multiset, counting preimage multiplicities). Blind + grok-4.3 + gemini-3.1-pro all give **8** (distinct edges after deduplication). The gemini-2.5-flash diff table in its own receipt flags this:
> "Outside model counted the full multiset (16 edges including duplicates) rather than distinct edges (8). No derivation is shown for why retaining self-loops yields 16 vs 8."

gemini-2.5-flash's own internal diff correctly identifies this as a deduplication failure. The problem statement asks for distinct edges, not multiset cardinality.

**This divergence is preserved for the overseer. gemini-2.5-flash is isolated on this point; three independent sources converge on 8.**

---

## 3. Build verify step: which blind predictions have outside confirmation, which are contested

### Confirmed by at least two independent outside models

- **P1 (rho form, coordinate dependence, fiber direction):** All three models independently derive the same closed-form density matrix and agree phi is the fiber direction. **Blind prediction confirmed independently.**
- **P3 (b0 values and sample counts):** All three models independently compute the same b0 values (+1/0/-1) and the same per-class sample count of 128. **Blind prediction confirmed independently.**
- **P4(a) T_z,R_z commuting:** All three models agree. **Blind prediction confirmed.**
- **P4(b) T_x,R_x commuting:** All three models agree. **Blind prediction confirmed.**
- **P4(c) T_z,T_x commuting:** Two of three models (gemini-3.1-pro, gemini-2.5-flash) plus explicit matrix derivation confirm this. grok-4.3 dissents without derivation. **Blind prediction has strong independent support; grok-4.3 dissent is unsubstantiated.**
- **P4(d) R_x,R_z noncommuting:** All three models agree. **Blind prediction confirmed.**
- **P4(e) T_z,R_x noncommuting:** All three models agree. **Blind prediction confirmed.**
- **P4(f) T_x,R_z noncommuting:** All three models agree. **Blind prediction confirmed.**
- **P5 erase count = 4:** All three models agree. **Blind prediction confirmed independently.**
- **P5 retain count = 8:** grok-4.3 and gemini-3.1-pro agree; gemini-2.5-flash dissents (counting multiset). **Blind prediction confirmed by two of three models; dissent is a deduplication failure, not a substantive disagreement about the underlying graph structure.**

### Contested — divergence not resolved

- **P2 (density-only class count):** This is a genuine arithmetic disagreement. Two outside models (grok-4.3, gemini-3.1-pro) with shown derivations compute **12 density-only classes of size 32** (24 with sheet probe, size 16). Gemini-2.5-flash and the blind sheet compute **24 density-only classes of size 16** (48 with sheet probe, size 8). The arithmetic at issue is the period of `e^{2i chi_j}` on the 8-point grid: period-4 gives 4 distinct values (grok/gemini-3.1-pro), period-8 gives 8 distinct values (flash/blind). The arithmetic of `e^{i*j*pi/2}` cycling with period 4 is a checkable fact; the overseer should run a direct numerical check before the verify step. **The verify step must compute `{e^{2i chi_j} : j=0..7}` explicitly and count distinct values.**

---

## 4. Failed API calls

No failed API calls are reported in any of the three receipt files. All three outside-model runs completed with `finishReason: STOP`.

---

## 5. Model metadata at time of run

| Model | finish | prompt tokens | output tokens |
|---|---|---|---|
| grok-4.3 | not stated explicitly | not stated | not stated |
| gemini-3.1-pro-preview | STOP | 1206 | 2848 (+8624 thoughts) |
| gemini-2.5-flash | STOP | 1206 | 6785 (+6840 thoughts) |
