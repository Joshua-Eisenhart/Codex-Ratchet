# Formal Proposal Consolidation: Corrected Constraint-Core and Inverse-Limit Candidates

**Date:** 2026-07-22  
**Standing:** candidate mathematics plus repository-status reconciliation. Nothing in this document is promoted merely because it is formally expressible. Owner commitments constrain the comparison pool; they do not preselect a winner.

## Provenance rule

The submitted `Pasted text(65).txt`, `Pasted markdown (2)(5)(1).md`, and `Pasted text(64)(1).txt` are Gemini-generated secondary analyses. Their internal `OWNER` labels are hypotheses about provenance, not direct owner quotations. This document therefore distinguishes:

- direct owner constraints, quoted from the live thread or preserved owner ledgers;
- repository facts at the cited commit;
- executed calibrations with fresh receipts;
- mathematical candidates that remain to be compared.

In particular, the symbols \(\operatorname{ND}_{\preceq_{D_t}}\), the exact thermodynamic vector \((\Sigma_\tau,\Delta H(R),\Delta\kappa)\), the factor-graph solver \(Z(b)\), receipt-indexed Purgatory, and dynamic archive quotienting are candidate formalizations. They are not direct owner formulas and are not silently promoted by this consolidation.

## Governing whole-candidate Ratchet

A candidate is the complete finite object

\[
Z=
\left(
G,\rho_V,
\{X_A,Q_A,\bar C_{AB},\mathcal F^X_{A/B}\}_{B\subset A},
\Gamma(Q),\{\Phi_{e,k}\},\Pi,D,H,P,R
\right).
\]

The diagram \(G\), candidate sets, quotient probes, restrictions, fibres, stages, records, and requirements may all change. A proposal is settled before comparison:

\[
\widehat Z=\operatorname{settle}_{G'}(\operatorname{propose}(Z,y)).
\]

The next frontier is

\[
F_{t+1}
=
\operatorname{ND}_{\preceq_{D_t}}
\left(F_t\cup\{\widehat Z\}\cup\{Z_{\mathrm{default}}\}\right).
\]

This is provisional comparison, not an absolute MSS theorem. Incomparables remain plural; the default remains runnable; failed candidates may be re-offered when \(D_t\), \(\Pi\), evidence, or \(G\) changes.

## Binding corrections to the submitted consolidation

1. Four local candidates at each of 16 placements give \(4^{16}\) assignments, not \(8^{16}\).
2. A noncausal physical ontology does not imply that noncommuting computational operations can be reordered or replaced by a static contraction. Ordered execution and atemporal global settlement are separate candidates until common probes identify them.
3. Exact marginalization preserves the observables licensed by the chosen boundary sufficient statistic; it does not preserve arbitrary bulk-sensitive probes.
4. An extension fibre is a preimage of a restriction map, not its categorical inverse or exact dual.
5. The cardinality of a continuous density-matrix fibre is not a usable Hartley capacity. Count a finite survivor fibre or use an explicitly measured \(\varepsilon\)-covering number/volume.
6. Petz recovery is reference-dependent and exact only under data-processing equality; it is not a universal unique maximum-entropy lift.
7. Empty compatible support implies zero factor-graph amplitude. Zero amplitude does not imply empty support because complex amplitudes may cancel.
8. Partial trace does not create a classical record. A quantum instrument plus explicit record register does.
9. Spohn production requires a stationary reference and a valid CPTP/semigroup setting. Landauer rejection requires an explicit erasure protocol, bath, and temperature.
10. Quotienting an append-only archive creates a finite or coarser derived index only when this is actually bounded; it does not make an indefinitely growing raw history finite.
11. No statement that one candidate “dominates” another is an execution result unless both were settled and compared under the same frozen demands and probes.

## 1. Atemporal factor-graph marginalization

### Correct formal candidate

Let \(G=(V,F,E)\) be a finite factor graph, with finite variable spaces \(X_v\) and factors

\[
\psi_\alpha:\prod_{v\in\partial\alpha}X_v\to\mathbb C.
\]

For a boundary set \(B\subseteq V\), boundary value \(b\in X_B\), and compatible internal assignments

\[
\mathcal H_b
=
\{h\in\prod_{v\in V}X_v:h|_B=b\},
\]

define

\[
Z_G(b)
=
\sum_{h\in\mathcal H_b}
\prod_{\alpha\in F}
\psi_\alpha(h|_{\partial\alpha}).
\]

For an internal block \(A\), an exact boundary factor is

\[
\widetilde\psi_A(x_{\partial A})
=
\sum_{x_{A\setminus\partial A}}
\prod_{\alpha\in F_A}
\psi_\alpha(x|_{\partial\alpha}).
\]

This is an exact algebraic contraction for that factorization. It is not automatically equivalent to an ordered channel

\[
\Phi_{16}\circ\cdots\circ\Phi_1.
\]

Equivalence must be established relative to a common probe family \(\Pi\):

\[
Z_{\mathrm{factor}}\sim_\Pi Z_{\mathrm{ordered}}
\iff
O(Z_{\mathrm{factor}})=O(Z_{\mathrm{ordered}})
\quad\forall O\in\Pi.
\]

### What survives from Gemini

- A finite factor graph is a legitimate noncausal/global-settlement candidate.
- Exact internal marginalization can reduce a finite calculation without inventing causal ontology.
- It should compete with ordered execution and coherent histories under common probes.

### What does not survive

- \(8^{16}\) is unsupported by the declared four local candidates; use \(4^{16}\).
- Operational equivalence alone does not guarantee a low-rank or small exact representation.
- Noncausal ontology does not exclude order-sensitive noncommuting computation.
- The July 22 N=3 simulation does not run this relaxation solver. It runs ordered channels and a separate postselected coherent-history control.

### Current status

**Mathematical candidate; not implemented as the whole-manifold solver.** The GHZ boundary control already excludes unrestricted boundary compression: equal proper marginals and equal boundary cochain coexist with \(\langle XXX\rangle=+1\) and \(-1\).

## 2. Cohomological obstruction and guided renesting

### Correct formal candidate

Let \(K_A,K_B\) be finite cell complexes with shared boundary \(K_{AB}\), and let

\[
a_A\in C^1(K_A;\mathbb Z_n),
\qquad
a_B\in C^1(K_B;\mathbb Z_n).
\]

Their boundary discrepancy is

\[
d_{AB}=r_Aa_A-r_Ba_B\in C^1(K_{AB};\mathbb Z_n).
\]

Exact representative compatibility requires \(d_{AB}=0\). Gauge compatibility requires \(d_{AB}=\delta\lambda\) for some \(\lambda\in C^0(K_{AB};\mathbb Z_n)\). Only when \(\delta d_{AB}=0\) does it define a cohomology class

\[
o_{AB}=[d_{AB}]\in H^1(K_{AB};\mathbb Z_n).
\]

If \(o_{AB}\ne0\), the current gluing is obstructed. A receipt may generate a finite proposal set

\[
P(y,Z)=\{G'_1,\ldots,G'_m\},
\]

such as removing an edge, inserting a defect cell, refining a boundary, or changing a bundle chart. Each \(G'_j\) must be fully resettled and compared; the obstruction does not authorize one repair automatically.

For a factor-graph candidate,

\[
\mathcal H_b=\varnothing\Longrightarrow Z_G(b)=0,
\]

but the converse fails when compatible complex amplitudes cancel.

### What survives from Gemini

- A finite obstruction can direct renesting proposals.
- Incompatible assignments may be excluded without making a local edit the winner.
- A topology-changing proposal must trigger whole-candidate re-settlement.

### What does not survive

- Linear superposition is not intrinsically “unphysical”; incompatible assignments are excluded, while compatible amplitudes may interfere.
- Relative phase is not automatically a cohomology invariant.
- Boundary phase alone cannot be assumed sufficient for the bulk.
- A conflict receipt may index several repairs, not one deterministic repair.

### Current status

**Executed calibration at finite \(\mathbb Z_5\) level.** The July 22 run rejects a torn triangle, proposes a charged path renesting, fully resettles it, and admits it. The repair is dominated by its uncharged parent because no current state observable improves. This is not yet Hopf/Weyl cohomology or an atemporal factor-graph solver.

## 3. Plural extension fibres and SBS persistence filter

### Correct extension fibre

For a finite survivor system with restriction

\[
C_{AB}:X_A^t\to X_B^t,
\]

the exact finite fibre is

\[
\mathcal F^X_{A/B}(x_B)
=
C_{AB}^{-1}(x_B)
=
\{x_A\in X_A^t:C_{AB}(x_A)=x_B\}.
\]

Its finite capacity is

\[
\kappa^X_{A/B}(x_B)=\log|\mathcal F^X_{A/B}(x_B)|.
\]

For a continuous density fibre, replace raw cardinality with an explicitly defined covering number or measure, for example

\[
\kappa^{(\varepsilon)}_{A/B}(\rho_B)
=
\log N_\varepsilon
\left(
\{\rho_A:C_{AB}(\rho_A)=\rho_B\},d
\right).
\]

The Petz map for channel \(\mathcal N\) and faithful reference \(\sigma\) is

\[
\mathcal R_{\sigma,\mathcal N}(X)
=
\sigma^{1/2}
\mathcal N^\dagger
\left(
\mathcal N(\sigma)^{-1/2}X\mathcal N(\sigma)^{-1/2}
\right)
\sigma^{1/2}.
\]

It is an exact recovery of the relevant states only under data-processing saturation; it is not the inverse of \(C_{AB}\) on the entire fibre.

### Correct SBS candidate

An ideal spectrum-broadcast state has

\[
\rho_{SE_1\cdots E_m}
=
\sum_z p_z|z\rangle\langle z|
\otimes
\rho_{E_1}^{(z)}\otimes\cdots\otimes\rho_{E_m}^{(z)},
\]

with distinguishable conditional fragment records, for example

\[
F\!\left(\rho_{E_f}^{(z)},\rho_{E_f}^{(z')}\right)
\le\varepsilon_F
\quad(z\ne z').
\]

A finite admission test should also name the pointer basis, number of fragments, redundancy threshold, system-dephasing error, and conditional-dependence tolerance. SBS is a candidate persistence criterion, not proof that the resulting class is an ontologically fundamental object.

### Current status

**Partially executed calibration.** The N=3 run computes finite fibres, Hartley counts, \(\varepsilon\)-cover counts, system-dephasing error, conditional fragment fidelities, Helstrom discrimination, and conditional mutual information. Record-erasure, false-broadcast, and phase-scramble controls respond correctly. SBS does not yet gate the archive, and the current engine stages largely destroy the seed's redundant records.

## 4. Operational-equivalence indexing for Purgatory

### Correct formal candidate

Let \(Y\) be a finite or finitely encoded receipt space and let \(\sim_\Pi\) be an operational equivalence relation induced by frozen probes. Define a canonical signature

\[
s_\Pi:Y\to\Sigma_\Pi,
\qquad
s_\Pi(y)=s_\Pi(y')\iff y\sim_\Pi y'.
\]

Purgatory is a set-valued index

\[
\mathcal P_t:\Sigma_\Pi
\to
\mathcal P
\left(
\{(Z_{\mathrm{fail}},G'_{\mathrm{repair}},D,\Pi,evidence)\}
\right).
\]

Lookup by a hash table can be expected \(O(1)\) only after canonical finite serialization and collision handling. A hit re-offers repairs; it does not admit them:

\[
\operatorname{lookup}(s_\Pi(y_{\mathrm{new}}))
\longrightarrow
\{G'_j\}
\longrightarrow
\{\operatorname{settle}_{G'_j}(Z)\}
\longrightarrow
\operatorname{ND}_{\preceq_D}.
\]

The index key must bind the demand set and probe version. Otherwise two operationally different failures can alias after \(\Pi\) changes.

### What survives from Gemini

- Failure receipts can make historical repair retrieval bounded and relevant.
- Bulk-state equality is a poor retrieval key when the actual obstruction is probe-relative.
- Re-offered repairs must be resettled under the current whole state.

### What does not survive

- Exact receipt equality is not the same as operational equivalence.
- A signature may map to multiple repairs.
- Expected \(O(1)\) lookup does not make settlement or verification \(O(1)\).
- The current N=3 code has no persistent receipt-indexed Purgatory implementation.

### Current status

**Mathematical candidate.** Pack 179 contains real Purgatory and re-offer behavior for finite hypotheses, but not this quantum-instrument signature index.

## 5. Dynamic quotienting of a monotone archive

### Correct formal candidate

Separate immutable raw history from derived indexes:

\[
\mathcal A_t\subseteq\mathcal A_{t+1},
\]

\[
q_{\Pi,t}:\mathcal A_t\to\mathcal A_t/\!\sim_{\Pi,t}.
\]

The quotient may merge operational aliases while the source records remain addressable. If an outer restriction \(R_{BA}\) is used, quotient compatibility requires

\[
a\sim_{\Pi_A}a'
\Longrightarrow
R_{BA}(a)\sim_{\Pi_B}R_{BA}(a').
\]

This makes the induced quotient map well defined. The finite active object can be one of:

\[
\mathcal I_t=\mathcal A_t/\!\sim_{\Pi,t},
\qquad
\mathcal I_t^{(\varepsilon)}=\text{an }\varepsilon\text{-cover},
\qquad
\mathcal I_t^{(W)}=\text{a bounded active window},
\]

provided its loss/error contract is explicit.

### What survives from Gemini

- Raw monotonicity and finite working indexes can coexist.
- Coarser probes can merge formerly distinct signatures.
- Restriction-induced quotienting is legitimate when the congruence condition holds.

### What does not survive

- A growing raw archive is not made finite merely by quotienting its current view.
- Quotient changes can split as well as merge classes when probes are refined.
- Old quotient keys require versioning and migration.
- No current whole-manifold code executes this dynamic archive quotient.

### Current status

**Mathematical candidate.** The cumulative packs preserve raw evidence plus derived indexes, but this is packaging behavior rather than a running manifold law.

## 6. Typed multivector dissipation and partial-order arbitration

### Licensed coordinates

Finite survivor capacity:

\[
\kappa=\log|\mathcal F^X|.
\]

Quantum state entropy:

\[
S_{\mathrm{vN}}(\rho)=-\operatorname{Tr}(\rho\log\rho).
\]

Umegaki relative entropy:

\[
D_U(\rho\|\sigma)
=
\operatorname{Tr}\rho(\log\rho-\log\sigma).
\]

For a CPTP map \(\Phi\) with invariant faithful reference \(\Phi(\tau)=\tau\), a licensed finite-step Spohn/DPI decrement is

\[
\Sigma_\tau(\rho;\Phi)
=
D_U(\rho\|\tau)
-D_U(\Phi(\rho)\|\tau)
\ge0.
\]

For a continuous semigroup \(\Phi_t=e^{t\mathcal L}\) with stationary \(\tau\),

\[
\sigma_\tau(\rho_t)
=
-\frac{d}{dt}D_U(\rho_t\|\tau)
\ge0.
\]

An explicit instrument creates a classical record state

\[
\omega_R=\sum_y p_y|y\rangle\langle y|,
\qquad
H(R)=-\sum_y p_y\log p_y.
\]

Partial trace alone does not create \(\omega_R\).

### Typed comparison

Keep the receipt in a product space:

\[
h(Z)
=
\left(
\Sigma_\tau,
H(R),
\kappa,
D_U,
\ldots
\right)
\in
V_\Sigma\times V_H\times V_\kappa\times V_D\times\cdots.
\]

For a demand set declaring coordinate directions, \(Z_a\preceq_D Z_b\) iff \(Z_a\) is no worse in every demanded coordinate. Strict dominance requires one strict improvement. If \(Z_a\) has lower \(\Sigma\) but higher \(H(R)\) than \(Z_b\), and neither tradeoff is licensed, retain both. The engine does not stall: a fair scheduler may run any runnable frontier member, including the default, while the Ratchet retains the plural frontier.

### What survives from Gemini

- Hartley, Shannon, von Neumann, relative-entropy, and Spohn quantities must not be summed merely because they are called entropy.
- A typed Pareto frontier is the correct default when no exchange law is earned.
- Incomparability is a result, not a failure.

### What does not survive

- The receipt is a typed vector/product element, not automatically a tensor.
- Lower \(H(R)\) is not automatically better; the demand direction must be declared.
- Landauer rejection is invalid without an explicit reset, bath, temperature, and work accounting.
- The N=3 run's active Pareto frontier uses SBS diagnostics and structural charge. It records Spohn/DPI and fibre data separately but does not yet compare candidates on \((\Sigma,H,\kappa)\).

### Current status

**Partially executed calibration.** NumPy non-scalar frontier and licensed finite-step Spohn/DPI receipts run and pass. The requested typed thermodynamic frontier and native Julia/JAX/PyTorch agreement remain absent.

## Current simulated target after correction

The next candidate should not be described as already running. It is:

\[
\text{finite N=3 whole-state comparison}
+
\text{factor-graph candidate}
+
\text{typed }(\Sigma,H,\kappa)\text{ frontier}
+
\text{receipt-indexed Purgatory}
+
\text{dynamic archive quotient}.
\]

It must run the ordered and atemporal candidates side by side, preserve a common initial whole state, freeze the probe family before results, retain incomparables, and run independently in Julia, JAX, and PyTorch before any promoted claim.
