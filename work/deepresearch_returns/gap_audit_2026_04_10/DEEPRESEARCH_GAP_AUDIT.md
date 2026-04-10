1. Repo Surfaces Confirmed
- Confirmed readable at anchor commit `c480a4a6154a181d3ff9ec1e8dbf679fcc7b3631`:
  - `new docs/05_research_index.md`
  - `new docs/TRADITION_SYSTEM_MAPPING_DETAILED.md`
  - `new docs/references/DISTINGUISHABILITY_FORMAL_REFERENCE.md`
  - `new docs/references/INFORMATION_GEOMETRY_REFERENCE.md`
  - `new docs/references/FIBER_BUNDLES_AND_SPIN_GEOMETRY_REFERENCE.md`
  - `new docs/references/ATTRACTOR_BASINS_FORMAL_REFERENCE.md`
  - `new docs/references/VIABILITY_THEORY_REFERENCE.md`
  - `new docs/references/STOCHASTIC_THERMODYNAMICS_REFERENCE.md`
  - `new docs/references/FEP_AND_ACTIVE_INFERENCE_REFERENCE.md`
  - `new docs/references/LLM_BIAS_AND_FAILURE_MODES_REFERENCE.md`
  - `new docs/references/CHINESE_PHILOSOPHY_REFERENCE.md`
- External-source recommendations below are based on established literature rather than a live web sweep because live web search was not available in this session.
- Net result: the repo already has serious anchor surfaces across distinguishability, information geometry, spin/bundle geometry, attractors/viability, stochastic thermodynamics, FEP, LLM failure modes, and Chinese support-tradition mapping.

2. Strong Research Lanes Already Present
- Distinguishability / operational equivalence / quotient / DPI / Blackwell / hypothesis testing / Fisher / resource-theoretic framing.
- Information geometry from Fisher-Rao through alpha-connections, exponential families, projection theorems, quantum monotone metrics, and applied bridges to ML, thermodynamics, and FEP.
- Fiber bundle / spin / Hopf / Berry / gauge lane is unusually strong for a system repo and already separated from direct application claims.
- Attractor-basins lane is not naive: it already includes stochastic basins, fractal/riddled basins, NK landscapes, neutral networks, Hopfield, and explicit critiques of high-dimensional landscape intuition.
- Viability lane is solid and correctly distinguished from attractor language.
- Stochastic thermodynamics lane covers fluctuation theorems, path-probability entropy production, Landauer/Szilard, NESS, TUR, and biological information-processing hooks.
- FEP lane is better than average because it already includes critique, not just advocacy.
- LLM failure modes lane is operationally useful and unusually explicit about sycophancy, smoothing, position bias, calibration, RLHF overoptimization, and prompt injection.
- Chinese philosophy lane is already framed mostly as support-tradition rather than technical proof, which is the right default.

3. Thin or Missing Research Lanes
- Statistical experiment comparison beyond Blackwell: Le Cam deficiency, comparison of experiments, asymptotic distinguishability, and quantum Chernoff/Stein/Sanov are still thin relative to the centrality of “constraint on distinguishability.”
- Quantum information geometry beyond first-pass Petz coverage: operator means, monotone-metric families, scalar curvature, and quantum statistical manifold structure need more depth if the repo wants the geometry lane to do real explanatory work.
- Viability computation and reachability are thin relative to the conceptual weight given to viability. The repo has theory, but not enough on Hamilton-Jacobi reachability, level-set computation, and high-dimensional approximations.
- Metastability / chain recurrence / Morse decomposition are underdeveloped. This matters because the repo frequently needs to separate true attractors, transient trapping, and stochastic residence.
- Large-deviation / optimal-transport / Schrödinger-bridge literature is mostly absent. This is a missed bridge between stochastic thermodynamics, information geometry, and constraint-guided evolution.
- FEP scope conditions remain thinner than the enthusiasm of some bridge claims. Blanket semantics, NESS assumptions, and the exact conditions for Bayesian-mechanics-style derivations need a harder fence.
- Chinese philosophy guardrails still need more sinological ballast wherever the mapping risks drifting from structural support to doctrinal claim.
- LLM failure-mode coverage is good on symptoms but thinner on evaluation theory, latent-knowledge gaps, and formal limits of RLHF.

4. Best 15 External Sources To Add Next
1. Erik Torgersen, *Comparison of Statistical Experiments* (1991) — best upgrade for experiment comparison, deficiency, and decision-theoretic distinguishability beyond the current Blackwell-only emphasis.
2. Koenraad Audenaert et al., “Discriminating States: The Quantum Chernoff Bound” (2007) — sharpens asymptotic state discrimination and error exponents.
3. Masahito Hayashi, *Quantum Information Theory: Mathematical Foundation* (2017) — broadens the repo’s distinguishability lane into a more complete hypothesis-testing / asymptotic-information framework.
4. Dénes Petz and Catalin Ghinea, “Introduction to Quantum Fisher Information” (2011) — strengthens the quantum-metric side of the geometry lane beyond the current first-pass summary.
5. Nihat Ay, Jürgen Jost, Hông Vân Lê, and Lorenz Schwachhöfer, *Information Geometry* (2017) — adds modern geometric depth and sharper treatment of dual structure.
6. Ian Mitchell, Alexandre Bayen, and Claire Tomlin, “A Time-Dependent Hamilton-Jacobi Formulation of Reachable Sets for Continuous Dynamic Games” (2005) — best immediate add for scalable viability/reachability computation.
7. Charles Conley, *Isolated Invariant Sets and the Morse Index* (1978) — gives a cleaner dynamical-systems language for chain recurrence and decomposition beyond simple attractor talk.
8. Anton Bovier and Frank den Hollander, *Metastability: A Potential-Theoretic Approach* — adds the missing metastability / residence-time / escape-barrier discipline.
9. Juan Parrondo, Jordan Horowitz, and Takahiro Sagawa, “Thermodynamics of Information” (2015) — strongest single review for information-thermodynamics beyond the repo’s current Szilard/Landauer spine.
10. Jordan Horowitz and Todd Gingrich, “Thermodynamic Uncertainty Relations Constrain Nonequilibrium Fluctuations” (2020) — sharpens TUR scope, meaning, and limits.
11. Christian Léonard, “A Survey of the Schrödinger Problem and Some of its Connections with Optimal Transport” (2014) — high-value bridge source for stochastic thermodynamics, inference, and constrained dynamics.
12. Judea Pearl, *Probabilistic Reasoning in Intelligent Systems* (1988) — needed to harden the blanket semantics in the FEP doc instead of relying mainly on downstream reinterpretations.
13. Stephen Casper et al., “Open Problems and Fundamental Limitations of Reinforcement Learning from Human Feedback” (2023) — best next source for formalizing RLHF limitations beyond symptom catalogs.
14. Brook Ziporyn, *Zhuangzi: The Essential Writings with Selections from Traditional Commentaries* (2009) — best next source to refine perspectivalism / equalizing-things usage without overtechnicalizing it.
15. Philip J. Ivanhoe and Bryan W. Van Norden (eds.), *Readings in Classical Chinese Philosophy* — best compact guardrail source for keeping support-tradition use broad, accurate, and non-doctrinal.

5. For each source: what repo doc it should strengthen
1. Torgersen → `new docs/references/DISTINGUISHABILITY_FORMAL_REFERENCE.md`
2. Audenaert et al. → `new docs/references/DISTINGUISHABILITY_FORMAL_REFERENCE.md`
3. Hayashi → `new docs/references/DISTINGUISHABILITY_FORMAL_REFERENCE.md` and `new docs/05_research_index.md`
4. Petz & Ghinea → `new docs/references/INFORMATION_GEOMETRY_REFERENCE.md`
5. Ay/Jost/Lê/Schwachhöfer → `new docs/references/INFORMATION_GEOMETRY_REFERENCE.md`
6. Mitchell/Bayen/Tomlin → `new docs/references/VIABILITY_THEORY_REFERENCE.md`
7. Conley → `new docs/references/ATTRACTOR_BASINS_FORMAL_REFERENCE.md`
8. Bovier/den Hollander → `new docs/references/ATTRACTOR_BASINS_FORMAL_REFERENCE.md` and `new docs/references/STOCHASTIC_THERMODYNAMICS_REFERENCE.md`
9. Parrondo/Horowitz/Sagawa → `new docs/references/STOCHASTIC_THERMODYNAMICS_REFERENCE.md` and `new docs/references/FEP_AND_ACTIVE_INFERENCE_REFERENCE.md`
10. Horowitz/Gingrich → `new docs/references/STOCHASTIC_THERMODYNAMICS_REFERENCE.md`
11. Léonard → `new docs/references/STOCHASTIC_THERMODYNAMICS_REFERENCE.md` and `new docs/references/INFORMATION_GEOMETRY_REFERENCE.md`
12. Pearl → `new docs/references/FEP_AND_ACTIVE_INFERENCE_REFERENCE.md`
13. Casper et al. → `new docs/references/LLM_BIAS_AND_FAILURE_MODES_REFERENCE.md`
14. Ziporyn → `new docs/references/CHINESE_PHILOSOPHY_REFERENCE.md` and `new docs/TRADITION_SYSTEM_MAPPING_DETAILED.md`
15. Ivanhoe/Van Norden → `new docs/references/CHINESE_PHILOSOPHY_REFERENCE.md` and `new docs/TRADITION_SYSTEM_MAPPING_DETAILED.md`

6. Overclaim Risks
- The repo is strongest when it says correspondence, mismatch, or exact shared object. It gets risky when shared structure is allowed to slide into shared explanatory role.
- The FEP bridge is the most obvious escalation risk. “Correspondence” is supportable; “derive FEP from constraint surface” is not yet earned on the current docs.
- The identity/distinguishability lane needs constant fencing: probe-relative indistinguishability is not automatically absolute ontology unless the admissible probe family is fixed and defended.
- The geometry lane should not let “same topology/object” become “same engine semantics.” Hopf/SU(2)/Weyl exactness does not by itself validate system-level dynamics.
- The attractor lane needs continued discipline around metastability, stochastic residence, and chain recurrence. Otherwise “survival,” “trapping,” and “attraction” will get blurred.
- The Chinese philosophy lane must remain support-tradition only. Zhengming, Zhuangzi, correlative thinking, qi, yin-yang, and I-Ching should not be promoted as technical proof or hidden precursor math.
- The LLM lane needs citation hygiene and recency discipline. One example: `arXiv:2603.10123` is labeled “2025” in the current doc even though the identifier is 2026-era format; that kind of slippage weakens the whole audit surface.
- Across the whole set, the main general risk is moving too fast from “useful support literature” to “canon-level derivation.”

7. Best 5 immediate fill-in jobs
1. Add a decision-theoretic distinguishability supplement covering deficiency, comparison of experiments, quantum Chernoff/Stein, and asymptotic error exponents.
2. Add a viability computation supplement covering Hamilton-Jacobi reachability, level-set methods, and what can or cannot scale beyond low-dimensional grids.
3. Add a metastability / chain recurrence supplement so the repo can sharply separate attractors, transient trapping, and stochastic escape.
4. Add an FEP scope-and-assumptions supplement that isolates Markov blanket semantics, NESS requirements, exact derivation conditions, and critical objections in one place.
5. Add a support-tradition guardrail supplement for Chinese philosophy that explicitly marks allowed uses, disallowed uses, and mismatch conditions, then run a citation-hygiene pass on the LLM reference doc.
