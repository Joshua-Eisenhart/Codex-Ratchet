# AXIS0_SPEC_OPTIONS v0.3
DATE_UTC: 2026-01-31
STATUS: DRAFT (NONCANON)
SCOPE: Axis-0 only (do not conflate with Axes 1–6)

## 0) Canon anchor (from your docs)

Axis 0 is **Correlation persistence polarity under perturbation**:

- **Allostatic**: correlation diversity increases under perturbation
- **Homeostatic**: correlation deviation is suppressed under perturbation

Everything else in this document is a *mathematization / measurement proposal* that should be treated as testable options, not as canon.

---

## 1) QIT-native setup (minimal math objects)

Let the system be described by a density operator \(\rho\) on a finite-dimensional Hilbert space \(\mathcal{H}\).

Choose a fixed decomposition into subsystems:
\[
\mathcal{H} = \bigotimes_{i=1}^n \mathcal{H}_i.
\]

A **perturbation family** is a one-parameter family of CPTP maps \(\Phi_\lambda\) with \(\Phi_0\) the identity or baseline channel:
\[
\rho(\lambda) = \Phi_\lambda(\rho).
\]

The core Axis-0 question becomes:

> Under perturbation \(\lambda\), does the *diversity / spread* of correlations across subsystem pairs increase (allostatic) or get damped (homeostatic)?

---

## 2) Option family A — correlation-spread functional on pairwise mutual information

For each pair \((i,j)\), define mutual information:
\[
I(i:j) = S(\rho_i) + S(\rho_j) - S(\rho_{ij}),
\]
with \(S(\cdot)\) the von Neumann entropy.

Define weights \(w_{ij}(\lambda) = I_{\rho(\lambda)}(i:j)\) and normalize:
\[
p_{ij}(\lambda) = \frac{w_{ij}(\lambda)}{\sum_{a<b} w_{ab}(\lambda)}.
\]

Define a **diversity** (effective number of correlated links) via Shannon entropy:
\[
H(\lambda) = -\sum_{i<j} p_{ij}(\lambda)\log p_{ij}(\lambda), \quad
D(\lambda)=\exp(H(\lambda)).
\]

**Axis-0 classifier (Option A)**:
- Allostatic if \(\left.\frac{d}{d\lambda}D(\lambda)\right|_{\lambda=0} > 0\)
- Homeostatic if \(\left.\frac{d}{d\lambda}D(\lambda)\right|_{\lambda=0} \le 0\)

Notes:
- This directly matches your “correlation diversity under perturbation” wording.
- It does **not** treat Axis-0 as “entropy sign.” It’s a response derivative.

---

## 3) Option family B — correlation deviation damping as variance control

Using the same weights \(w_{ij}(\lambda)\), define the mean and variance across pairs:
\[
\mu(\lambda)=\frac{1}{m}\sum_{i<j} w_{ij}(\lambda), \quad
\mathrm{Var}(\lambda)=\frac{1}{m}\sum_{i<j}(w_{ij}(\lambda)-\mu(\lambda))^2
\]
where \(m=\binom{n}{2}\).

**Axis-0 classifier (Option B)**:
- Allostatic if \(\left.\frac{d}{d\lambda}\mathrm{Var}(\lambda)\right|_{0} > 0\)
- Homeostatic if \(\left.\frac{d}{d\lambda}\mathrm{Var}(\lambda)\right|_{0} \le 0\)

Interpretation:
- Homeostatic means *perturbation does not increase deviation*—i.e., it damps correlation deviations.

---

## 4) Option family C — multi-information / “total correlation” response

Define the total correlation (multi-information):
\[
T(\rho)=\sum_{i=1}^n S(\rho_i) - S(\rho).
\]

**Axis-0 classifier (Option C)**:
- Allostatic if \(\left.\frac{d}{d\lambda}T(\rho(\lambda))\right|_{0} > 0\)
- Homeostatic if \(\left.\frac{d}{d\lambda}T(\rho(\lambda))\right|_{0} \le 0\)

Caveat:
- This measures “more or less total correlation,” not “diversity of where correlation lives.”
- Useful if your sims measure a global scalar more reliably than a distribution.

---

## 5) Option family D — “JK fuzz” as an unraveling / path-ensemble, with a clock-like monotone

If a channel admits a Kraus representation
\[
\Phi(\rho)=\sum_k K_k \rho K_k^\dagger,
\]
then an n-step composition induces a distribution over Kraus-index histories \(\mathbf{k}=(k_1,\dots,k_n)\) via the unnormalized branch states:
\[
\tilde{\rho}_\mathbf{k} = K_{k_n}\cdots K_{k_1}\,\rho\,K_{k_1}^\dagger\cdots K_{k_n}^\dagger.
\]
Branch weights:
\[
P(\mathbf{k})=\mathrm{Tr}\,\tilde{\rho}_\mathbf{k}.
\]

Define **path entropy**:
\[
H_{\mathrm{path}} = -\sum_\mathbf{k} P(\mathbf{k})\log P(\mathbf{k}),
\]
(after normalizing \(P\) if desired).

Then Axis-0 can be framed as:
- Allostatic: perturbation increases the *effective variety of admissible histories*
- Homeostatic: perturbation suppresses history diversification

This aligns with your “shell contains j,k as future possibilities” intuition (jk fuzz), while keeping it operational.

### 5.1) i-scalar as “global order parameter” (clock-like, not time)
Pick a global monotone \(G(\rho)\) such as:
- \(G(\rho)=T(\rho)\) (total correlation), or
- \(G(\rho)=\sum_{i<j} I(i:j)\) (total pairwise mutual information), or
- \(G(\rho)=H_{\mathrm{path}}\) (history variety)

Then define
\[
i := G(\rho)
\]
as the ordering scalar (not local time, not simultaneity). In your language: “local clocks vary; global correlation order does not.”

---

## 6) Practical simulation notes (what to compute later)

For any option above:
1. Choose \(n\) and a baseline \(\rho\).
2. Choose a perturbation family \(\Phi_\lambda\) (e.g., depolarizing strength, partial swap, dephasing, amplitude damping, etc.).
3. Numerically approximate derivatives with a small \(\epsilon\):
\[
\frac{d}{d\lambda}f(\lambda)\Big|_0 \approx \frac{f(\epsilon)-f(0)}{\epsilon}.
\]
4. Record sign and magnitude across many seeds and channel families.

---

## 7) What this does *not* decide

- Whether the physics interpretation is “negative entropy,” “entangled spacetime,” or “holographic bookkeeping.”
- Whether the clock-like scalar is best identified with “size of the universe,” “total entanglement,” or another invariant.

Those belong to a later layer, after the operational measurement is stable.
