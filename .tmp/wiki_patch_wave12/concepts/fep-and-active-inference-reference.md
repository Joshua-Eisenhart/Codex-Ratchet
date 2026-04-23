---
title: Fep And Active Inference Reference
created: 2026-04-07
updated: 2026-04-11
type: summary
tags: [reference, research, system]
sources:
  - raw/articles/new-docs/references/FEP_AND_ACTIVE_INFERENCE_REFERENCE.md
  - raw/articles/legacy-books/the-grandmaster-of-the-universe-copy.md
framing: mixed
---

# Free Energy Principle and Active Inference: Formal Reference

## Overview
Reference doc covering the actual Friston framework: variational free energy, active inference, Markov blankets, expected free energy, the prediction-first inversion, and key critiques. Not the system's application.

## Variational Free Energy

F = E_q[-ln P(y,x)] - H[q(x)]. Two decompositions: (1) KL + Surprise: F = D_KL[q(x) || P(x|y)] + (-ln P(y)). Since KL >= 0, free energy is an upper bound on surprise. Minimizing F drives q toward true posterior P(x|y) — approximate Bayesian inference. (2) Complexity - Accuracy: F = D_KL[q||P(x)] - E_q[ln P(y|x)]. System balances model complexity against prediction accuracy. Surprise = -ln P(y) = self-information in information theory, NOT colloquial surprise.

## Active Inference: Perception-Action Unification

Both perception and action minimize the SAME objective — variational free energy. Perception: minimize F by updating internal states (adjusting q). Action: minimize F by changing sensory input through acting on the world. The inversion: the organism actively sculpts sensory input to match its generative model, rather than passively processing what arrives. Policy selection uses expected free energy G (for future/counterfactual observations), not variational free energy F.

## Markov Blankets

Originally from Pearl (1988): blanket of a node = parents, children, co-parents. FEP partition: external (hidden causes), sensory (affected by external), active (affects external), internal (system dynamics). Blanket = sensory + active. Internal conditionally independent of external given blanket (and vice versa). Anything that persists as a distinguishable entity must possess a Markov blanket. The partition is recursive: blankets within blankets (cells within organs within organisms within ecosystems).

## Expected Free Energy (Planning)

G(π) decomposes into: epistemic value (information gain, exploration, curiosity) + pragmatic value (preference satisfaction, exploitation). Planning as inference: selecting a policy is Bayesian model comparison, Q(π) = σ(ln P(π) - G(π)).

## FEP and Physics

Starting point: Langevin dynamics dx/dt = f(x) + ω. At nonequilibrium steady state (NESS), Helmholtz decomposition: dissipative (curl-free) flow = gradient descent on surprisal, solenoidal (divergence-free) flow = circulates on iso-probability contours. Systems that persist look AS IF they minimize surprisal. Connection to Jaynes' MaxEnt: maximizing entropy given constraints is dual to minimizing variational free energy given a generative model.

## FEP and Evolution

Adaptive fitness IS model evidence: an organism's fitness is proportional to how well its implicit generative model is compatible with its sensory states. Natural selection eliminates phenotypes with high average surprisal. Friston acknowledges the tautological structure: "Why am I here? Because I have adaptive fitness. Why do I have adaptive fitness? Because I am here." The FEP characterizes what it means for biological systems to exist. Free energy minimization occurs at multiple timescales: milliseconds (perception), seconds (action), lifetimes (learning), evolutionary time (natural selection).

## Prediction-First: The Inversion

Traditional: sensory input -> brain processes -> perception -> response. FEP/Predictive processing: brain continuously generates top-down predictions. Only prediction errors propagate upward. Perception = explaining away errors. The brain is primarily GENERATIVE — hallucinating a model of the world and correcting when reality contradicts. Sensory data is correction signal, not primary input.

## Relation to Bayesian Brain

Hierarchy: FEP (principle) -> Bayesian brain (consequence) -> Predictive coding (one implementation). FEP entails Bayesian brain, goes beyond inference (unifies perception with action), applies to all self-organizing systems not just brains. Predictive coding is one implementation requiring hierarchical model, Gaussian recognition density, Laplace approximation, gradient descent.

## Critiques

**Tautology/Unfalsifiability:** Any system with a Markov blanket at NESS can be described as minimizing free energy. If it applies to everything, it predicts nothing specific. **Technical errors (Biehl, Pollock, Kanai, 2021):** Markov blanket definitions not equivalent across papers. Crucial equation rewriting steps "not generally correct without additional previously unstated assumptions." **Emperor's New Markov Blankets (Bruineberg et al.):** Statistical Markov blankets to physical boundaries is unjustified metaphysical leap — conflates map and territory. **Defenders' response:** FEP is a mathematical framework (like the principle of stationary action), not a falsifiable theory. Specific models derived from it are falsifiable. The framework/model distinction is key.

## How it connects
This reference supports [[constraint-surface-and-process]] (the prediction-first correspondence) and [[owner-thesis-and-cosmology]] (FEP as literal physics mirror). See [[viability-theory-reference]] for the survive-within-constraints framing.

## Fit for this wiki
Best fit:
- predictive-processing language for perception/action unification
- a mathematically explicit account of surprisal, blanket structure, and policy selection
- a bridge between self-maintenance and model evidence

Mismatch:
- FEP is not the whole of enactivism
- blanket formalism does not automatically settle the system's admissibility geometry
- high-level metaphor should not replace the actual variational quantities

## Live Repo Status
The live repo only earns a bounded predictive-processing claim so far.

- `sim_qit_predictive_world_model.py` is the bounded predictive-world-model row currently pointed to by this lane; in this workspace pass I did not verify a checked-in `qit_predictive_world_model_results.json` artifact alongside it, so treat the row as script-level support rather than a fully re-audited owner artifact.
- `world_model_sim.py` is an older exploratory sidecar, not the owner surface.
- No live row yet earns a full FEP derivation, Markov-blanket theorem, or active-inference action-policy doctrine.

So the safe bridge is: predictive error minimization and bounded state adaptation are supported; the larger FEP metaphysics remain research support, not earned lower-loop truth.

## 2026-04-10 arXiv source addition

### 1906.10184 — A Free Energy Principle for a Particular Physics
- Frames a "particular physics" around distinguishability, Markov blankets, NESS, and recursive composition across scales.
- Useful as a direct source for the FEP / active-inference support lane and the relation between self-organization and information geometry.
- Best fit pages: [[fep-and-active-inference-reference]], [[autopoiesis-and-enactivism-reference]], [[current-research-overlays]].

## Cross-links to related support layers
- [[autopoiesis-and-enactivism-reference]] for the enactive side of the debate
- [[viability-theory-reference]] for the constraint-survival framing
- [[distinguishability-formal-reference]] for the information-theoretic support layer
- [[holodeck-as-recall-space]] for the recall-space interpretation of prediction-first perception and memory
- [[prediction-first-memory-vs-llm-memory]] for the model-first memory translation
- [[current-research-overlays]] for routing into the broader support graph

## Legacy Foundational Overlay (Grandmaster)

The Grandmaster frames prediction as cosmic principle: "We can only guess the future, and that is all consciousness does." Systems that predict survive: "Things move towards this pattern in time, such that a chaotic system, with an underlying possible order evolves towards that order." Free energy minimization as physics: "The universe seeks the lowest energy path, and does things the easiest way, this is the most root law of physics."

The prediction-first framing is explicit: "Consciousness is made from the most likely and simplest set of rules. These rules have fundamental connections and relationships. These patterns are the same to create the universe and math, because anything else would be too complex to exist more than the simpler form." The universe selects for the most probable: "Life is not made up of highly complex rules, it is made up of the most likely possible rules that could form life. The universe is made up of the most likely set of rules."

This is best treated as a legacy foundational overlay, not as lower-loop mathematical support. FEP's formal role here remains the bounded predictive-processing and variational free-energy layer. See [[autopoiesis-and-enactivism]] for the self-creation view and [[evolutionary-epistemology-reference]] for universal selection.

## Open questions
- Whether F01+N01 necessarily produce FEP-like dynamics (structural correspondence noted, derivation not yet done).
- Whether the tautology critique applies to the system's constraint-surface version of FEP.
- Which parts of the current stack need active-inference language versus simpler viability language.

- [[self-similar-frameworks-and-teleological-doctrine]] — owner doctrine: five self-similar frameworks (holodeck/QIT/science/IGT/Leviathan), teleological admissibility
