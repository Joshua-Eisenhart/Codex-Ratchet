# Fleet verdict — "carrier forced" REFUTED; genuine null-flip but only low-rank structure, not a carrier

**Fleet (wf wcbxuskm3, 9 external models incl openrouter/fusion + a fresh-context re-runner that EXECUTED an attack + codex2-xhigh arbiter): MIXED.** `self_fulfilling_synthetic_benchmark` 9/10 true; `quotient_baseline_is_strawman` 10/10 true; `forces_a_real_carrier_class` 10/10 FALSE. The "a low-DoF shared carrier is FORCED" claim is **REFUTED**. scratch_diagnostic, DRAFT_UNAUDITED, no promotion. **Caught BEFORE commit (discipline win, unlike the capstone).**

## The two killer findings
1. **Strawman quotient (10/10).** The baseline was train-MEAN (no transfer by construction). Any low-rank-exploiting method beats it trivially.
2. **No specific carrier is forced — fleet-EXECUTED counterexample.** The fresh-context re-runner actually ran **iterative rank-3 SVD matrix completion** (Candès–Recht soft-impute, **DoF=0, no latent vectors, no carrier**). It **passes every gate the "carrier" passes** (held-out ratio ≤ 0.12 all seeds; fails on the null world like the carrier). So the test forces **LOW-RANK MATRIX-COMPLETION STRUCTURE**, not a shared-latent-vector carrier. (Now added to the sim as the `NONCARRIER_svd` arm so it self-documents.)

## Self-fulfilling
The positive data is **planted low-rank** (generated rank-3, then fit rank-3) — "a low-rank model detects low-rank structure it was designed to detect" (gemini/fusion). fusion's sharpest: PASS occurs *only* when `d_fit == d_true`, and the `DoF<46` compression gate "does all the discriminating work, not transfer." So it does not yet say anything non-tautological about *real* probe statistics.

## What GENUINELY survives (the re-runner confirmed, executed)
- The **null-flip is real**: full-rank structureless data **defeats all methods including iterative SVD** (it is not rigged).
- **Shuffle collapses** transfer (confirmed).
- So there is a genuine "low-rank structure present → transfers; absent → doesn't" diagnostic — just **not** a carrier-forcing result.

## Required fixes (to become a genuine forced-carrier test)
1. Strongest **non-carrier baselines** in the sim: iterative SVD (done), index-aware averaging, k-NN, graph/kernel interpolation, MDL/Bayesian — under equal complexity accounting.
2. **Real / non-Gram-generator data** where ground-truth rank is NOT built in (the carrier must beat alternatives on data not drawn from its own family).
3. **Pre-registered thresholds**; no post-hoc tuning (do not tighten 0.3→0.01 to exclude SVD without independent justification).
4. Rename the earned claim to **"low-rank matrix-completion structure,"** not "carrier."

## Disposition
The deflationary thesis holds with executed evidence: even when held-out transfer works, it is **generic low-rank compressibility (carrier-free), not a forced carrier.** This sim stays a scratch low-rank-transfer diagnostic with a real null-flip. The honest open question — does ANY data force a *specific* carrier over the strongest non-carrier baseline — is still open, and is the right next build (real/non-Gram data + the baseline suite). The process worked: DRAFT_UNAUDITED + an active defeat-attempt killed the overclaim before it was committed as earned.
