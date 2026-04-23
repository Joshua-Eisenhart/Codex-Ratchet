# AGM-11 Clifford Exception Audit Return

## Audit Context
This audit examines the handling of the Clifford torus anomaly (η = π/4) as documented in the `AXIS0_CLIFFORD_ANOMALY_NOTE.md` and evidenced in the Phase 5B/5C simulation results.

## Audit Verdict: Honest with Cautious Fencing
The handling of the Clifford exception is **honestly characterized as a geometric control result** rather than a system failure. The explanation for lower Mutual Information (MI) and higher variance is structurally sound based on S³ geometry. However, some specific data points (scramble reversal) are being correctly dismissed as noise but should not be featured as semi-supportive evidence in the observation table.

---

### What is genuinely special
- **Geometric Degeneracy:** The equatorial latitude (η = π/4) is the unique point where L/R Hopf radii are equal. The resulting collapse of the chirality discriminator (`lr_asymmetry` ~0.71 vs ~0.99) is a genuine geometric fact, not a parameter tuning artifact.
- **Saddle Point Dynamics:** The massive increase in variance (Std: 0.256 vs 0.047) in random-initialization trials confirms that the Clifford torus sits on a critical boundary between regimes. This justifies its role as a "control point" for measuring engine sensitivity.
- **MI Floor:** The ~2.5× lower MI is a direct consequence of the engine’s architecture being optimized for chiral separation. Seeing it fail precisely where chirality is minimized validates the mechanism.

### What is only weak evidence
- **Scramble Reversal:** The `mi_drop` of -0.037 in Phase 5C is effectively zero. Treating this as a "reversal direction" in the note's summary table is a slight over-reach of pattern recognition on noise.
- **"Anticipated" Behavior:** Claiming the 10× drift increase was "anticipated" feels like post-hoc smoothing. While the *direction* of the anomaly (lower performance) is expected, the *magnitude* of the drift (0.053) suggests a lack of stability at the equator that wasn't fully modeled in the bridge theory.

### What should stay fenced
- **Doctrine Data:** The Clifford results **must remain fenced** from the "Earned" credentials of the inner and outer bridge families. The anomaly is a known edge case; allowing its "failure" to degrade the overall bridge certification would be a category error in the audit.
- **Control Status:** Clifford should be maintained strictly as a **Calibration/Control point**, not an operational regime. No bridge logic should be "fixed" to accommodate Clifford if it compromises the high-performance inner/outer results.
- **Wait-and-See on Reversal:** The scramble reversal signal is too weak/noisy to integrate into the official Xi_hist theory. Fencing it off prevents "phantom physics" from entering the doctrine.

---

## Clifford Read (Fenced)
```markdown
[CLIFFORD_EXCEPTION_FENCE]
Latitude: η = π/4
Root Cause: L/R Hopf Equality (Chirality Null)
Metrics: MI ~0.72, Asymmetry ~0.71, Std ~0.25
Status: CALIBRATION_ONLY
Action: Exclude from winner-path-drift certification; preserve as mechanism-check.
[/CLIFFORD_EXCEPTION_FENCE]
```
