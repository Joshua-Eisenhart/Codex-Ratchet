# Free Energy Principle and Active Inference: Formal Reference

Date: 2026-04-05
Status: Reference doc — the actual framework, not the system's application

---

## Variational Free Energy

F = E_q[-ln P(y,x)] - H[q(x)]

Where q(x) is the recognition density (approximate belief about hidden states),
P(y,x) is the generative density, H is Shannon entropy.

Two decompositions:

Decomposition 1 — KL + Surprise:
  F = D_KL[q(x) || P(x|y)] + (-ln P(y))
  F = KL divergence + Surprise
Since KL >= 0, free energy is an upper bound on surprise. Minimizing F drives
q toward the true posterior P(x|y) — approximate Bayesian inference.

Decomposition 2 — Complexity minus Accuracy:
  F = D_KL[q(x) || P(x)] - E_q[ln P(y|x)]
  F = Complexity - Accuracy
System balances model complexity against prediction accuracy.

Surprise = -ln P(y) = improbability of observations under generative model.
Self-information in information theory. NOT colloquial surprise.

---

## Active Inference: Perception-Action Unification

Both perception and action minimize the SAME objective — variational free energy.

Perception: minimize F by updating internal states (adjusting q).
  dmu/dt ∝ -dF/dmu

Action: minimize F by changing sensory input through acting on the world.
  da/dt ∝ -dF/dy · dy/da

The inversion: the organism actively sculpts sensory input to match its
generative model, rather than passively processing what arrives.

Policy selection uses expected free energy G (for future/counterfactual
observations), not variational free energy F.

---

## Markov Blankets

Originally from Pearl (1988): the Markov blanket of a node is its parents,
children, and co-parents. Given the blanket, the node is conditionally
independent of all other nodes.

FEP partition of state space:

| States | Role |
|---|---|
| External (η) | Hidden causes in environment |
| Sensory (s) | Affected by external; affect internal |
| Active (a) | Affected by internal; affect external |
| Internal (μ) | The system's internal dynamics |

Blanket = sensory + active states.
Internal conditionally independent of external given blanket (and vice versa).
Sensory mediates outside-in; active mediates inside-out.

Anything that persists as a distinguishable entity must possess a Markov
blanket. The partition is recursive: blankets within blankets (cells within
organs within organisms within ecosystems).

---

## Expected Free Energy (Planning)

G(π) = E_Q(o,s|π)[ln Q(s|π) - ln P(o,s)]

Decomposes into:
  G(π) = -E_Q(s|π)[H[P(o|s)]] + D_KL[Q(o|π) || P(o)]
         (epistemic value /        (pragmatic value /
          information gain)         preference satisfaction)

Epistemic value: favors policies resolving uncertainty (exploration, curiosity)
Pragmatic value: favors policies producing preferred outcomes (exploitation)

Policy selection: Q(π) = σ(ln P(π) - G(π))
Planning as inference — selecting a policy is Bayesian model comparison.

---

## FEP and Physics

Starting point: Langevin dynamics. dx/dt = f(x) + ω

At nonequilibrium steady state (NESS), the Helmholtz decomposition:
  f(x) = -(Q + Γ) · ∇ln p*(x)

Dissipative (curl-free) flow: gradient descent on surprisal.
Solenoidal (divergence-free) flow: circulates on iso-probability contours.

Systems that persist look AS IF they minimize surprisal.

Connection to Jaynes' MaxEnt: maximizing entropy given constraints is
dual to minimizing variational free energy given a generative model.

Connection to thermodynamic free energy: F = U - TS. Variational version
replaces thermodynamic quantities with information-theoretic ones.

---

## FEP and Evolution

Natural selection eliminates phenotypes with high average surprisal.
Organisms that persist appear to minimize long-run average surprisal —
equivalently, maximize model evidence P(y|m).

Adaptive fitness IS model evidence: an organism's fitness is proportional
to how well its implicit generative model is compatible with its
sensory states.

Friston acknowledges the tautological structure: "Why am I here? Because
I have adaptive fitness. Why do I have adaptive fitness? Because I am here."
The FEP is not a mechanism for life — it characterizes what it means for
biological systems to exist at all.

Free energy minimization occurs at multiple timescales:
- Milliseconds: perception
- Seconds: action
- Lifetimes: learning
- Evolutionary time: natural selection

---

## Prediction-First: The Inversion

Traditional: sensory input → brain processes → perception → response.

FEP/Predictive processing: brain continuously generates top-down predictions.
Only prediction errors propagate upward. Perception = explaining away errors.

The brain is primarily GENERATIVE — hallucinating a model of the world and
correcting when reality contradicts. Sensory data is correction signal, not
primary input.

When prediction errors cannot be resolved by updating the model, the system
acts to change the world to match predictions (active inference).

---

## Relation to Bayesian Brain

Bayesian brain hypothesis: brain performs approximate Bayesian inference.
Computational-level claim, no mechanism commitment.

Predictive coding (Rao & Ballard 1999): one algorithmic proposal for how
Bayesian inference might be implemented.

FEP encompasses and extends both:
1. FEP entails Bayesian brain (minimizing F = approximate Bayesian inference)
2. FEP goes beyond inference (unifies perception with action)
3. FEP is broader (applies to all self-organizing systems, not just brains)
4. Predictive coding is one implementation (requires hierarchical model,
   Gaussian recognition density, Laplace approximation, gradient descent)
5. FEP is a principle, not a hypothesis (mathematical framework, not
   falsifiable — but specific models derived from it ARE)

Hierarchy: FEP (principle) → Bayesian brain (consequence) → Predictive
coding (one implementation).

---

## Critiques

**Tautology/Unfalsifiability (strongest critique):** Any system with a Markov
blanket at NESS can be described as minimizing free energy. If it applies to
everything, it predicts nothing specific.

**Technical errors (Biehl, Pollock, Kanai, 2021):** Definitions of "Markov
blanket" across Friston's papers are not equivalent. Crucial equation
rewriting steps are "not generally correct without additional previously
unstated assumptions." The free energy lemma is "proved by counterexample
to be wrong when taken at face value."

**Emperor's New Markov Blankets (Bruineberg et al.):** The step from
statistical Markov blankets to physical system boundaries involves an
unjustified metaphysical leap. A Markov blanket is statistical; treating
it as a physical boundary conflates map and territory.

**"The math is not the territory" (Andrews):** The formalism and what it
claims to represent are not as tightly connected as proponents suggest.

**Defenders' response:** FEP is a mathematical framework (like the principle
of stationary action), not a falsifiable theory. Specific models derived
from it are falsifiable. The framework/model distinction is key.

---

## Key People

| Person | Contribution |
|---|---|
| Karl Friston | Originator of FEP (2005-2010), active inference, UCL |
| Thomas Parr | Active Inference textbook (MIT Press 2022) with Pezzulo, Friston |
| Giovanni Pezzulo | Co-author, embodied cognition, CNR Italy |
| Jakob Hohwy | The Predictive Mind (2013), Monash |
| Andy Clark | Surfing Uncertainty (2015), Sussex |
| Maxwell Ramstead | Enactive inference, multiscale blankets |
| Michael Kirchhoff | Markov blankets of life, Wollongong |

---

## Sources

Friston (2010) Nature Reviews Neuroscience. Friston (2019) A free energy
principle for a particular physics. Parr, Pezzulo, Friston (2022) Active
Inference, MIT Press. Biehl, Pollock, Kanai (2021) technical critique.
Bruineberg et al. Emperor's New Markov Blankets. Andrews, The math is
not the territory. Kirchhoff et al. (2018) Markov blankets of life,
Royal Society Interface.
