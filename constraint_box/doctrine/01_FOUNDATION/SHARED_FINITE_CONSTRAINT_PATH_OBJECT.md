# Shared Finite Constraint-Path Object

Nominalist programming, constraint engineering, SMT checking, entropy,
geometry, path sums, and Ratchet settlement are views or operations on one
shared finite object.

## Carrier

\[
\mathfrak C=
\left(
\mathcal H,
\{X_v\},
\{C_\alpha\},
\{\pi_q\},
\{R_{\ell+1,\ell}\},
D,
\mathcal V
\right).
\]

| Component | Meaning |
|---|---|
| \(\mathcal H\) | finite complete histories |
| \(X_v\) | finite local carriers |
| \(C_\alpha\) | active compatibility constraints |
| \(\pi_q\) | projections and probes |
| \(R_{\ell+1,\ell}\) | relations between nested presentations |
| \(D\) | currently demanded distinctions |
| \(\mathcal V\) | declared valuation algebra |

The compatible whole is

\[
\mathcal T=\{h\in\mathcal H:\forall\alpha,\ C_\alpha(h)\}.
\]

A present view is a projection, not one selected narrative:

\[
P_t=\pi_t(\mathcal T).
\]

For \(x\in P_t\), its compatible completion fibre is

\[
F_t(x)=\{h\in\mathcal T:\pi_t(h)=x\}.
\]

The branch stays alive exactly when \(F_t(x)\ne\varnothing\).  Its finite
extension capacity is

\[
\kappa_t(x)=\log_2|F_t(x)|.
\]

The same operation has a geometric and entropic reading:

\[
F_{t+1}(x)=F_t(x)\cap C_{t+1}.
\]

Geometry is the changed fibre structure.  Entropy/capacity is the changed
cardinality or rank.  Neither is a narrative gloss added afterward.

## Valuation profiles

\[
Z(b)=
\bigoplus_{h\in\mathcal H_b}
\bigotimes_\alpha \psi_\alpha(h_\alpha).
\]

| Profile | Addition/product | Bounded meaning |
|---|---|---|
| Boolean | OR/AND | compatible history exists |
| Counting | \(+,\times\) | number of compatible histories |
| Tropical | \(\min,+\) | least declared cost |
| Probability | nonnegative \(+,\times\) | probability under an earned probability model |
| Complex amplitude | complex \(+,\times\) | interfering finite path amplitude |
| Operator | addition/composition | ordered channel history |

These profiles share a finite combinatorial carrier but are not flattened into
one score or interpretation.

## History-pair field

For ordered channel histories,

\[
D(j,k)=\operatorname{Tr}(K_j\rho_0K_k^\dagger).
\]

\(j=k\) contains diagonal history weights.  \(j\ne k\) contains coherence
between histories.  A CR adapter must preserve both when the task requires the
history-pair carrier.  The generic ConstraintBox core does not label a
classical possibility set as the complete quantum field.

## Anti-teleological reading

The completion space constrains which present sections are possible.  This
does not require literal backward causation or a chosen final goal.  No
attractor is installed as the destination.  A basin is a measured property of
the declared dynamics or it remains a candidate.
