The audit of the QIT-FEP Axis0 Spinor Path-Integral Scout has been completed based on the provided code, documentation, and receipt highlights.

Here are the findings for each audit question:

1.  **Are the pass conditions real falsifiers or are any still tautological?**
    Most pass conditions are real falsifiers, designed to test specific hypotheses regarding the noncommuting order signal, entanglement's role, B-side gauge invariance, and manifold sensitivity. For example, `noncommuting_order_gap > 1e-3` and `commuting_quantum_order_gap < 1e-9` are explicit falsifiable conditions. However, the checks within `run_core_fixture()` (path sum linearity, QVFE identity) and `run_z3_dependency_fence()` are explicitly labeled in `QIT_FEP_AXIS0_SPINOR_PATH_INTEGRAL_WORKOUT_20260523.md` as "correctness check only" and "declared nonpromotion guard, not a derivation" respectively, indicating they serve as implementation consistency checks or logical gates rather than falsifiers of the physical model.

2.  **Is `Phi_QFEP_provisional = log Z + I_c` honestly scoped as provisional?**
    Yes, `Phi_QFEP_provisional` is consistently and explicitly scoped as provisional throughout the code comments and the `QIT_FEP_AXIS0_SPINOR_PATH_INTEGRAL_WORKOUT_20260523.md` document. It is clearly stated as "not admitted as final Axis0" and its components (`log Z` and `I_c`) are always reported separately. The "Premortem" section even identifies premature promotion of this scalar as a key risk.

3.  **Does the scout avoid classical Markov-chain ontology as a primitive?**
    Yes, the scout actively avoids classical Markov-chain ontology as a primitive. It frames quantum instrument histories as the replacement for classical hidden states and treats classical/commuting dynamics as explicit ablation controls rather than the base model. The `sim_execution_kind` is "nonclassical", and the documentation highlights this as a key improvement over older FEP framings.

4.  **Does the B-side fixed-cut gauge control now make the right claim?**
    Yes, the B-side fixed-cut gauge control makes a precisely limited claim. Both the Python script's docstring and the `WORKOUT.md` explicitly state that it "is not a proof that every extension of rho_A is equivalent" but rather "only blocks a spurious dependence on the arbitrary B-side basis for a fixed cut." This clearly and correctly scopes its scope and implications.

5.  **Does the commuting manifold null actually separate flux sensitivity from generic grid variance?**
    Yes, the commuting manifold null successfully separates flux sensitivity from generic grid variance. The receipt highlights show a significant `noncommuting flux_mean_gap` while the `commuting flux_mean_gap` is near zero. The `WORKOUT.md` clearly explains this, noting that the null preserves coordinate variance but erases flux-direction sensitivity, demonstrating that the engine's perception of flux is tied to noncommuting dynamics.

6.  **What is the strongest remaining failure mode?**
    The `Premortem` section in `QIT_FEP_AXIS0_SPINOR_PATH_INTEGRAL_WORKOUT_20260523.md` outlines several critical failure modes for the overall program, the strongest being:
    *   Premature promotion of the `Phi_QFEP_provisional` additive scalar before a bridge `Xi` is proven.
    *   The scout remaining limited to "bounded toy instruments" and not evolving to "full engine charts."
    Within the current scout's scope, the `min_order_gap` from the parameter robustness sweep is very close to its threshold (`0.0010019519603086113` vs. `1e-3`), indicating a potential fragility or boundary condition that could lead to signal loss under certain parameter variations.

7.  **Which alternative Axis0 candidate should be tested next?**
    Based on Section 12 ("Alternative Axis0 Families To Explore") and the nature of `Phi_QFEP_provisional = log Z + I_c`, the most logical next alternative candidates to test as "smallest falsifiers" would be the individual components: `Phi = I_c(A -> B)` alone and `Phi = log Z_path` alone. Additionally, `Phi = I(A:B)` alone, which was recently added to the component decomposition, is also a strong candidate for further exploration to understand its distinct contribution.

---
**Verdict:**

`ADMIT_AS_FORMAL_SCOUT`

The scout is robustly designed, thoroughly tested with appropriate controls and ablations, and its claims are meticulously scoped. The explicit provisional labeling of `Phi_QFEP_provisional` and the `Premortem` section demonstrate a strong self-awareness of potential risks and a clear path for future development. It performs as intended within its defined scope as a formal scout candidate.
