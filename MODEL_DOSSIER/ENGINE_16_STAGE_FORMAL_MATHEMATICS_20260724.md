# 16-stage QIT Engine Mathematics and Schedule Ledger

**Status:** formalization draft; no owner-canonical schedule is asserted here.

**Purpose:** give a model or simulator one unambiguous mathematical interface for the sixteen chart placements without importing psychological labels, IGT casing, MBTI labels, thermodynamic metaphors, or a silently chosen loop start.

**Claim ceiling:** this specifies finite density-level candidate maps and the tests required to use them. It does not establish a physical engine, a thermodynamic cycle, a complete 64-state closure, a spinor-manifold theorem, or a successful simulation.

## 0. Anti-collapse rules

The source estate contains several real alternatives. They must remain alternatives until an owner locks one and a conformance run is attached.

1. `Ne`, `Ni`, `Si`, and `Se` below are **opaque terrain addresses**. They are not psychological functions in the mathematics.
2. `Ti`, `Te`, `Fi`, and `Fe` below are **operator addresses**. They are not software backends, personality labels, or thermodynamic strokes.
3. A stage is the triple **terrain flow + operator kernel + precedence**. Neither a terrain name nor an operator name alone defines a stage.
4. The schedule that orders four already-defined stages is separate from the stage maps. A cyclic rotation is not numerically harmless for noncommuting, dissipative maps started from a fixed state.
5. A simulator must select and record a `terrain_law_id`, `operator_kernel_id`, and `schedule_id`. It may not infer any of them from prose.
6. The 64-slot scaffold is not a 64-step sequential program. The chart has sixteen macro placements; a separate four-substage expansion can make 64 addressable slots.

The goal is deliberately narrower than a narrative: make it impossible to run one branch while reporting another.

## 1. Authority and evidence ledger

| Item | Status in this document | Reason |
|---|---|---|
| Two engine types; two loops each; four macro stages per loop | structural contract | This gives (2\times2\times4=16) placements. |
| Density-level stage algebra | formal candidate realization | It is an explicit executable layer, not full spinor closure. |
| Four terrain generator equations | candidate terrain-law family | GitHub and the attached PDF explicitly leave concrete jumps, rates, and frames open. |
| Runtime operator kernel `K-R` | repo-reported executable branch | Current GitHub source implements dephasing/rotation channels. |
| Structural operator kernel `K-S` | competing PDF branch | It differs materially from `K-R`; it cannot be silently mixed with it. |
| Historical chart schedules | repo-reported | The current GitHub chart is Se-starting. |
| N-first / S-first science-method schedule | owner-provided recovery candidate | It was stated in the current conversation as non-canon recovery evidence. |
| A single default schedule | intentionally unset | Earlier owner and repository surfaces conflict. This document forces a declared selection. |

### GitHub alignment consulted on 2026-07-24

- `system_v4/docs/ENGINE_GRAMMAR_DISCRETE.md` (`755fd225…`): 16 chart cells, precedence and the older Se-starting schedules.
- `system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md` (`151a0c51…`): source-normalized four runtime operators and the full 16-token matrix.
- `system_v7/sims/type1_engine_v0/type1_engine_common.py` (`090a2f3b…`): Type-1 v0 source-pinned diagnostic metadata.
- `system_v7/sims/type1_engine_v0/results/RESULTS.md` (`abbd10fb…`): explicitly reports a `scratch_diagnostic` with NumPy and Julia; JAX is listed as queued, not evidence for that v0 run.
- `system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_common.py` (`21ad8d1b…`): current 16 macro-row chart used by the bounded 64-slot scout.
- Attached `gemini thread 2 save 2. engine mechanics..pdf`: useful source recovery, but it itself contains conflicting operator and schedule branches. It is not treated as a single authority.

## 2. Carrier, sheets, and notation

Let

\[
\mathcal D_2=\{\rho\in M_2(\mathbb C):\rho=\rho^\dagger,\ \rho\succeq0,\ \operatorname{Tr}\rho=1\}
\]

be the finite density-state carrier used by this layer. A spinor realization, when declared, is

\[
\psi_e\in S^3\subset\mathbb C^2,\qquad
\rho_e=\psi_e\psi_e^\dagger\in\mathcal D_2,
\]

for engine (e\in\{1,2\}). Set the sheet sign

\[
s_1=+1,\qquad s_2=-1.
\]

The density reduction is not injective:

\[
\rho(e^{i\alpha}\psi)=\rho(\psi).
\]

Consequently, a density-level pass cannot certify lost phase, a full Weyl-spinor statement, or a Hopf-fibre closure. Those require an explicitly retained spinor-path witness.

Use the Pauli matrices (\sigma_x,\sigma_y,\sigma_z), and define

\[
\sigma_{-s}=\frac{\sigma_x-is\sigma_y}{2}.
\]

Thus (\sigma_{-s}=\sigma_-\) for (s=+1) and (\sigma_{-s}=\sigma_+\) for (s=-1). For every jump operator (L), use the GKLS dissipator

\[
\mathcal D[L](\rho)=L\rho L^\dagger-\frac12\{L^\dagger L,\rho\}.
\]

All rates and durations appearing below must be recorded and satisfy

\[
\gamma_s,\epsilon_F,\epsilon_V,\epsilon_P,\kappa_{j,s},\tau_{T,s}\ge0.
\]

## 3. Terrain-law family `TL-1`

The four symbols are formal terrain addresses:

\[
\mathsf T=\{\mathrm{Se},\mathrm{Ne},\mathrm{Ni},\mathrm{Si}\}.
\]

For compact mathematics, read these addresses as

\[
\mathrm{Se}\equiv\mathsf S_e,\qquad
\mathrm{Si}\equiv\mathsf S_i,\qquad
\mathrm{Ni}\equiv\mathsf N_i,\qquad
\mathrm{Ne}\equiv\mathsf N_e.
\]

The suffixes `e` and `i` are formal external/internal position indices and
the letters `S` and `N` are branch labels. No psychological semantics are used
to derive a generator or a stage map.

Fix Hermitian (H_0), (H_C), jump sets (L_{r,s}^{\mathrm{Se}},L_{r,s}^{\mathrm{Ne}}), and projectors (P_{j,s}=P_{j,s}^\dagger=P_{j,s}^2). The candidate terrain generators are

\[
\begin{aligned}
\mathcal L_{\mathrm{Se},s}(\rho)
 &=\sum_r\mathcal D[L_{r,s}^{\mathrm{Se}}](\rho)-is\epsilon_F[H_0,\rho],\\
\mathcal L_{\mathrm{Ne},s}(\rho)
 &=-is[H_0,\rho]+\epsilon_V\sum_r\mathcal D[L_{r,s}^{\mathrm{Ne}}](\rho),\\
\mathcal L_{\mathrm{Ni},s}(\rho)
 &=\mathcal D[\sqrt{\gamma_s}\,\sigma_{-s}](\rho)-is\epsilon_P[H_0,\rho],\\
\mathcal L_{\mathrm{Si},s}(\rho)
 &=-is[H_C,\rho]+\sum_j\kappa_{j,s}\mathcal D[P_{j,s}](\rho),
 \qquad [H_C,P_{j,s}]=0.
\end{aligned}
\]

The terrain propagator is the superoperator exponential

\[
\Phi_{T,s}=\exp\!\bigl(\tau_{T,s}\mathcal L_{T,s}\bigr),
\qquad T\in\mathsf T.
\]

When the declared data meet the conditions above, (\Phi_{T,s}) is a CPTP map. The equations are a *family*, not a fully specified engine: choosing (L_{r,s}^{T}), (H_0), (H_C), rates, times, and a Type-2 frame is load-bearing configuration.

### Finite qubit benchmark `TL-Q2` (candidate instantiation)

For a bounded two-dimensional test, a fully typed specialization of `TL-1` is

\[
\begin{aligned}
H_0&=h_x\sigma_x+h_y\sigma_y+h_z\sigma_z,
\qquad H_C=\omega\sigma_z,\\
\mathcal L^{\rm Q2}_{\mathrm{Se},s}
 &=\gamma_{\rm Se}\mathcal D[\sigma_z]-is\epsilon_F[H_0,\,\cdot\,],\\
\mathcal L^{\rm Q2}_{\mathrm{Ne},s}
 &=-is[H_0,\,\cdot\,]+\epsilon_V\gamma_{\rm Ne}\mathcal D[\sigma_x],\\
\mathcal L^{\rm Q2}_{\mathrm{Ni},s}
 &=\gamma_{\rm Ni}\mathcal D[\sigma_{-s}]-is\epsilon_P[H_0,\,\cdot\,],\\
\mathcal L^{\rm Q2}_{\mathrm{Si},s}
 &=-is[\omega\sigma_z,\,\cdot\,]
 +\kappa\bigl(\mathcal D[P^z_+]+\mathcal D[P^z_-]\bigr).
\end{aligned}
\]

This is a benchmark contract, not the final terrain ontology. It is useful
because every symbol is finite and testable, and it prevents an implementation
from claiming to run an equation while leaving the jumps undefined. A run still
must pin the real values of the parameter vector

\[
\vartheta_{\rm Q2}=(h_x,h_y,h_z,\omega,\gamma_{\rm Se},\gamma_{\rm Ne},\gamma_{\rm Ni},
\epsilon_F,\epsilon_V,\epsilon_P,\kappa,\tau_{T,s}).
\]

### Explicit open fork: terrain instantiation

Do not substitute the unrelated two-by-two table sometimes found in recovery material—e.g. `Ni` with a (\sigma_y) jump and `Si` with a (\sigma_-) jump—into `TL-1` and report it as this same law. That is a rival `terrain_law_id`, not a simplification. In particular, `TL-1` uses a sheet-dependent ladder jump on `Ni` and projector dissipators on `Si`.

## 4. Operator-kernel registry

The stage grammar is independent of which kernel branch is selected. A run must choose exactly one `operator_kernel_id` for all cells unless it explicitly defines and tests a new mixed branch.

### 4.1 `K-R`: repo-reported runtime channel branch

Let

\[
P_\pm^z=\frac{I\pm\sigma_z}{2},\qquad
P_\pm^x=\frac{I\pm\sigma_x}{2}.
\]

For (q_z,q_x\in[0,1]), define

\[
\begin{aligned}
\mathcal O_{\mathrm{Ti}}(\rho)
 &= (1-q_z)\rho+q_z\sum_{a\in\{+,-\}}P_a^z\rho P_a^z,\\
\mathcal O_{\mathrm{Te}}(\rho)
 &= (1-q_x)\rho+q_x\sum_{a\in\{+,-\}}P_a^x\rho P_a^x,\\
\mathcal O_{\mathrm{Fi},s}(\rho)
 &=U_{x,s}(\theta_s)\rho U_{x,s}(\theta_s)^\dagger,
 \qquad U_{x,s}(\theta_s)=e^{-i\theta_s X_s/2},\\
\mathcal O_{\mathrm{Fe},s}(\rho)
 &=U_{z,s}(\varphi_s)\rho U_{z,s}(\varphi_s)^\dagger,
 \qquad U_{z,s}(\varphi_s)=e^{-i\varphi_s Z_s/2}.
\end{aligned}
\]

Here \(X_s,Z_s\) are declared sheet-frame Pauli observables. A Type-2 frame flip is not assumed merely because a prose source says “mirror”; it must be specified in the receipt. With \(X_s=\sigma_x\) and \(Z_s=\sigma_z\), this is the current GitHub runtime form: `Ti` and `Te` are pinching/dephasing channels and `Fi` and `Fe` are unitary rotations.

If no frame transform is declared, set \(\mathcal O_{\mathrm{Ti},s}=\mathcal O_{\mathrm{Ti}}\) and \(\mathcal O_{\mathrm{Te},s}=\mathcal O_{\mathrm{Te}}\). A sheet-specific frame is an explicit parameterization, not a license to alter the kernel.

All four `K-R` maps are CPTP.

### 4.2 `K-S`: competing structural-kernel branch recovered from the PDF

The PDF also presents a materially different candidate registry:

\[
\begin{aligned}
\widetilde{\mathcal O}_{\mathrm{Ti}}(\rho)&=\sum_kP_k\rho P_k,\\
\widetilde{\mathcal O}_{\mathrm{Te}}(\rho)&=e^{-iH_g t}\rho e^{+iH_g t},\\
\widetilde{\mathcal O}_{\mathrm{Fe}}(\rho)&=e^{t\mathcal L_{\mathrm{diss}}}(\rho),
\quad \mathcal L_{\mathrm{diss}}=\sum_j\mathcal D[L_j],\\
\mathcal I_{\mathrm{Fi}}(\rho)&=F\rho F^\dagger,
\quad p_F(\rho)=\operatorname{Tr}\mathcal I_{\mathrm{Fi}}(\rho),\\
\widetilde{\mathcal O}_{\mathrm{Fi}}(\rho)&=\frac{\mathcal I_{\mathrm{Fi}}(\rho)}{p_F(\rho)}
\quad\text{only when }p_F(\rho)>0.
\end{aligned}
\]

This is **not** interchangeable with `K-R`. In particular, the normalized (F\rho F^\dagger) operation is a conditional instrument update, generally nonlinear as a map on unconditional density states. It is not an unconditional CPTP channel unless its outcome record and success probability are handled explicitly. A simulator that calls it simply “a channel” is mathematically incomplete.

`K-S` is retained as an explicit rival, not used as an invisible replacement for `K-R`.

## 5. Precedence algebra

For a terrain (T), kernel operator (a), and sheet (s), define the two legal stage forms:

\[
\boxed{\ \Psi^{\uparrow}_{T,a,s}=\Phi_{T,s}\circ\mathcal O_{a,s}\ }
\qquad\text{and}\qquad
\boxed{\ \Psi^{\downarrow}_{T,a,s}=\mathcal O_{a,s}\circ\Phi_{T,s}\ }.
\]

Rightmost acts first. Thus

\[
\Psi^{\uparrow}_{T,a,s}(\rho)=\Phi_{T,s}(\mathcal O_{a,s}(\rho)),
\qquad
\Psi^{\downarrow}_{T,a,s}(\rho)=\mathcal O_{a,s}(\Phi_{T,s}(\rho)).
\]

The token spelling records execution order:

\[
\texttt{TiSe}\equiv\Psi^{\uparrow}_{\mathrm{Se},\mathrm{Ti},s},
\qquad
\texttt{SeTi}\equiv\Psi^{\downarrow}_{\mathrm{Se},\mathrm{Ti},s}.
\]

Do **not** replace this with raw left/right multiplication (A\rho) or (\rho A). Those are useful Liouville-space bookkeeping actions,

\[
\mathfrak L_A(X)=AX,\qquad\mathfrak R_A(X)=XA,
\]

but are not, in general, trace-preserving density-state channels. Any claim that action-side notation and the CPTP precedence maps are equivalent must be demonstrated row by row, not assumed.

The noncommutation witness for one terrain/operator pair is

\[
\delta_{T,a,s}(\rho)=\left\|\Phi_{T,s}(\mathcal O_{a,s}(\rho))
-\mathcal O_{a,s}(\Phi_{T,s}(\rho))\right\|_1.
\]

It is an observable to measure, not a quantity that may be declared nonzero by naming the stage.

## 6. The sixteen macro-stage maps

The formal name of a stage is

\[
\operatorname{Stage}(e,\ell;T,a,\epsilon)
\equiv\Psi_{T,a,s_e}^{\epsilon}.
\]

The following table is the 16-placement chart. The identifiers are mathematical addresses; no psychological or game-theory term is used in the equations.

| ID | Engine/sheet | Loop address | Token | (T,a,\epsilon) | Formal stage map |
|---|---|---|---|---|---|
| `E1.O.01` | (1,+) | outer | `TiSe` | ((\mathrm{Se},\mathrm{Ti},\uparrow)) | (\Phi_{\mathrm{Se},+}\circ\mathcal O_{\mathrm{Ti},+}) |
| `E1.O.02` | (1,+) | outer | `NeTi` | ((\mathrm{Ne},\mathrm{Ti},\downarrow)) | (\mathcal O_{\mathrm{Ti},+}\circ\Phi_{\mathrm{Ne},+}) |
| `E1.O.03` | (1,+) | outer | `NiFe` | ((\mathrm{Ni},\mathrm{Fe},\downarrow)) | (\mathcal O_{\mathrm{Fe},+}\circ\Phi_{\mathrm{Ni},+}) |
| `E1.O.04` | (1,+) | outer | `FeSi` | ((\mathrm{Si},\mathrm{Fe},\uparrow)) | (\Phi_{\mathrm{Si},+}\circ\mathcal O_{\mathrm{Fe},+}) |
| `E1.I.05` | (1,+) | inner | `SeFi` | ((\mathrm{Se},\mathrm{Fi},\downarrow)) | (\mathcal O_{\mathrm{Fi},+}\circ\Phi_{\mathrm{Se},+}) |
| `E1.I.06` | (1,+) | inner | `SiTe` | ((\mathrm{Si},\mathrm{Te},\downarrow)) | (\mathcal O_{\mathrm{Te},+}\circ\Phi_{\mathrm{Si},+}) |
| `E1.I.07` | (1,+) | inner | `TeNi` | ((\mathrm{Ni},\mathrm{Te},\uparrow)) | (\Phi_{\mathrm{Ni},+}\circ\mathcal O_{\mathrm{Te},+}) |
| `E1.I.08` | (1,+) | inner | `FiNe` | ((\mathrm{Ne},\mathrm{Fi},\uparrow)) | (\Phi_{\mathrm{Ne},+}\circ\mathcal O_{\mathrm{Fi},+}) |
| `E2.O.09` | (2,-) | outer | `FiSe` | ((\mathrm{Se},\mathrm{Fi},\uparrow)) | (\Phi_{\mathrm{Se},-}\circ\mathcal O_{\mathrm{Fi},-}) |
| `E2.O.10` | (2,-) | outer | `TeSi` | ((\mathrm{Si},\mathrm{Te},\uparrow)) | (\Phi_{\mathrm{Si},-}\circ\mathcal O_{\mathrm{Te},-}) |
| `E2.O.11` | (2,-) | outer | `NiTe` | ((\mathrm{Ni},\mathrm{Te},\downarrow)) | (\mathcal O_{\mathrm{Te},-}\circ\Phi_{\mathrm{Ni},-}) |
| `E2.O.12` | (2,-) | outer | `NeFi` | ((\mathrm{Ne},\mathrm{Fi},\downarrow)) | (\mathcal O_{\mathrm{Fi},-}\circ\Phi_{\mathrm{Ne},-}) |
| `E2.I.13` | (2,-) | inner | `SeTi` | ((\mathrm{Se},\mathrm{Ti},\downarrow)) | (\mathcal O_{\mathrm{Ti},-}\circ\Phi_{\mathrm{Se},-}) |
| `E2.I.14` | (2,-) | inner | `TiNe` | ((\mathrm{Ne},\mathrm{Ti},\uparrow)) | (\Phi_{\mathrm{Ne},-}\circ\mathcal O_{\mathrm{Ti},-}) |
| `E2.I.15` | (2,-) | inner | `FeNi` | ((\mathrm{Ni},\mathrm{Fe},\uparrow)) | (\Phi_{\mathrm{Ni},-}\circ\mathcal O_{\mathrm{Fe},-}) |
| `E2.I.16` | (2,-) | inner | `SiFe` | ((\mathrm{Si},\mathrm{Fe},\downarrow)) | (\mathcal O_{\mathrm{Fe},-}\circ\Phi_{\mathrm{Si},-}) |

### Example expansions under `TL-1 + K-R`

These demonstrate exactly how the table becomes executable without assigning any informal meaning.

\[
\begin{aligned}
\Psi_{\texttt{NeTi}}(\rho)
 &= (1-q_z)\Phi_{\mathrm{Ne},+}(\rho)
 +q_z\sum_{a\in\{+,-\}}P_a^z\Phi_{\mathrm{Ne},+}(\rho)P_a^z,\\
\Psi_{\texttt{FeSi}}(\rho)
 &=\Phi_{\mathrm{Si},+}\!\left(U_{z,+}(\varphi_+)\rho U_{z,+}(\varphi_+)^\dagger\right),\\
\Psi_{\texttt{SeFi}}(\rho)
 &=U_{x,+}(\theta_+)\Phi_{\mathrm{Se},+}(\rho)U_{x,+}(\theta_+)^\dagger,\\
\Psi_{\texttt{NiTe}}(\rho)
 &= (1-q_x)\Phi_{\mathrm{Ni},-}(\rho)
 +q_x\sum_{a\in\{+,-\}}P_a^x\Phi_{\mathrm{Ni},-}(\rho)P_a^x.
\end{aligned}
\]

All other rows are obtained from the table and the two boxed precedence equations. A run must emit the fully expanded parameter values it used; it may not use these symbolic forms as evidence of execution.

## 7. Loop and engine composition

Let a loop schedule be an ordered tuple of the four cell IDs belonging to that loop,

\[
\pi_{e,\ell}=(c_1,c_2,c_3,c_4).
\]

Its map is

\[
\Phi_{e,\ell}^{\pi}
=\Psi_{c_4}\circ\Psi_{c_3}\circ\Psi_{c_2}\circ\Psi_{c_1},
\qquad
\rho_{e,\ell,k}=\Psi_{c_k}(\rho_{e,\ell,k-1}).
\]

Thus (c_1) is applied first even though it is rightmost in the composed expression.

For a no-reset eight-stage engine configuration, the required handoff is

\[
\rho_{e,\mathrm{inner},0}=\rho_{e,\mathrm{outer},4},
\qquad
\Phi_e=\Phi_{e,\mathrm{inner}}\circ\Phi_{e,\mathrm{outer}}.
\]

The handoff witness is

\[
\varepsilon_{\mathrm{handoff},e}
=\left\|\rho_{e,\mathrm{inner},0}-\rho_{e,\mathrm{outer},4}\right\|_1.
\]

Any claimed continuous eight-stage/720-degree execution requires (\varepsilon_{\mathrm{handoff},e}=0) to numerical tolerance **and** a receipt proving no fresh state was substituted between loops.

The two engines are independent by default:

\[
\rho_1\in\mathcal D_2,\qquad\rho_2\in\mathcal D_2.
\]

There is no implicit tensor-product interaction, common bath, or geometry backreaction in these equations. A coupling requires a separately named map

\[
\mathcal C:\mathcal D_2\times\mathcal D_2\longrightarrow\mathcal D_4
\quad\text{or}\quad
\mathcal C_G\text{ on a declared shared carrier},
\]

and must be tested as a new component.

## 8. Schedule ledger: do not silently choose a starting cut

The stage maps above are stable addresses. The following schedules are incompatible configuration candidates, not prose variants of one another.

| Schedule ID | Induction word | Deduction word | Status / source |
|---|---|---|---|
| `SCH-REPO-SE-START` | \(\mathrm{Se}\to\mathrm{Si}\to\mathrm{Ni}\to\mathrm{Ne}\) | \(\mathrm{Se}\to\mathrm{Ne}\to\mathrm{Ni}\to\mathrm{Si}\) | GitHub historical chart and current v7 bounded scouts. |
| `SCH-ORIENTATION-20260723` | \(\mathrm{Ne}\to\mathrm{Ni}\to\mathrm{Se}\to\mathrm{Si}\) | \(\mathrm{Ne}\to\mathrm{Si}\to\mathrm{Se}\to\mathrm{Ni}\) | Earlier orientation document reported via personal-context recovery as `CURRENT DEFAULT`; conflicts with later recovery material. |
| `SCH-NFIRST-SFIRST-20260724` | \(\mathrm{Se}\to\mathrm{Si}\to\mathrm{Ni}\to\mathrm{Ne}\) | \(\mathrm{Ne}\to\mathrm{Ni}\to\mathrm{Si}\to\mathrm{Se}\) | Current owner-provided science-method recovery candidate; explicitly not an authority override. |

The current GitHub `type1_engine_v0` diagnostic is an execution of the
repo-reported Se-starting chart, not an execution witness for
`SCH-NFIRST-SFIRST-20260724`. A future receipt must not borrow its numerical
results or its claimed backend status for the N-first/S-first schedule.

Examples under `SCH-NFIRST-SFIRST-20260724`:

\[
\begin{aligned}
\pi_{1,\mathrm{outer}}&=(\texttt{NeTi},\texttt{NiFe},\texttt{FeSi},\texttt{TiSe}),\\
\pi_{1,\mathrm{inner}}&=(\texttt{SeFi},\texttt{SiTe},\texttt{TeNi},\texttt{FiNe}),\\
\pi_{2,\mathrm{outer}}&=(\texttt{FiSe},\texttt{TeSi},\texttt{NiTe},\texttt{NeFi}),\\
\pi_{2,\mathrm{inner}}&=(\texttt{TiNe},\texttt{FeNi},\texttt{SiFe},\texttt{SeTi}).
\end{aligned}
\]

For example, the Type-1 outer map under that schedule is

\[
\Phi_{1,\mathrm{outer}}^{\mathrm{NF}}
=\Psi_{\texttt{TiSe}}\circ\Psi_{\texttt{FeSi}}
\circ\Psi_{\texttt{NiFe}}\circ\Psi_{\texttt{NeTi}}.
\]

The historical Se-first word has the same adjacent terrain cycle in a different cut, but the maps need not agree from a fixed initial density state:

\[
\Phi_{1,\mathrm{outer}}^{\mathrm{NF}}\ne
\Phi_{1,\mathrm{outer}}^{\mathrm{SeStart}}
\quad\text{in general}.
\]

The reason is not semantic; it is mathematical. The constituent maps are generally noncommuting and may be noninvertible. Any claim that a rotation “does not matter” must be supported by a schedule-equivalence test, not by a circle diagram.

## 9. Geometry interface: separate from density-stage algebra

A commonly used local spinor chart is

\[
\psi(\eta,\phi,\chi)=
\begin{pmatrix}
e^{i(\phi+\chi)}\cos\eta\\
e^{i(\phi-\chi)}\sin\eta
\end{pmatrix},
\qquad
A=d\phi+\cos(2\eta)\,d\chi.
\]

Two candidate loop representatives are

\[
\gamma_f(u)=\psi(\eta_0,\phi_0+u,\chi_0),
\]

and

\[
\gamma_b(u)=\psi\bigl(\eta_0,\phi_0-\cos(2\eta_0)u,\chi_0+u\bigr).
\]

The first leaves the density reduction stationary while the second can change it. This does **not** make either curve a stage map. A complete simulation must give an explicit transport/injection map between the geometric path and the density stage,

\[
\Gamma_{e,\ell,k}: (\psi,\rho)\mapsto(\psi',\rho')
\quad\text{with}\quad
\rho'=\Psi_{c_k}(\rho),
\]

or state that it is running only the density-level reduction. Without (\Gamma\), do not report a Hopf, Weyl, or manifold traversal as executed.

## 10. Entropy and thermodynamic discipline

For a stage (c), the minimal state-level entropy observation is

\[
\Delta S_{\mathrm{vN},c}(\rho)
=S_{\mathrm{vN}}(\Psi_c(\rho))-S_{\mathrm{vN}}(\rho),
\qquad
S_{\mathrm{vN}}(\rho)=-\operatorname{Tr}(\rho\log\rho).
\]

It is not valid to infer its sign from the terrain or operator token. Even a dissipative channel can lower entropy for some input states, and a unitary operator can sit inside a nonunitary stage.

Keep noncommensurate outputs typed, for example

\[
\mathbf r_c=(\Delta S_{\mathrm{vN},c},\ \sigma_c,\ \Delta H(R)_c,\ \Delta\kappa_c,\ \Delta C_c),
\]

and do not sum them into one “entropy” scalar without a separately justified functional.

No stage is automatically Carnot, Otto, Szilard, isothermal, or adiabatic. A comparison map to a thermodynamic stroke is an additional object that must supply:

\[
(H(t),\ \beta\text{ or bath model},\ Q,\ W,\ \text{closure condition},\ \text{reverse-cycle control}).
\]

In particular:

- an adiabatic claim requires an isolated declared dynamics and the relevant entropy/work conditions;
- an isothermal claim requires a declared bath and temperature/Gibbs relation;
- a cyclic claim requires a state or control closure test, not merely four named operations.

This keeps thermodynamic simulations as comparison controls rather than smuggling their physics into the engine equations.

## 11. Mandatory deterministic conformance checks

For every claimed stage and loop, record these quantities from actual execution.

| Check | Required test |
|---|---|
| CPTP | Choi matrix (J(\Psi_c)\succeq0) and (\operatorname{Tr}_{\rm out}J(\Psi_c)=I\), or an equivalent independently checked finite test. |
| Kernel integrity | Receipt contains `operator_kernel_id`; reject a mix of `K-R` and `K-S` unless a named hybrid contract exists. |
| Terrain integrity | Receipt contains `terrain_law_id`, all jump operators, rates, frames, durations, and sheet sign. |
| Precedence | Measure (\delta_{T,a,s}) over a declared probe family; do not swap a token’s word order. |
| Schedule | Receipt contains `schedule_id`, ordered token list, initial-state hash, and rightmost-first composition notation. |
| No-reset handoff | Report (\varepsilon_{\rm handoff,e}) and hash both handoff arrays/records. |
| Geometry claim | Supply the actual (\Gamma_{e,\ell,k}) witness; otherwise label the run density-level only. |
| Multi-engine claim | Independently execute the declared JAX/Julia lanes and show each owns its numerical work; a queued backend is not an execution witness. |

The schedule-order discriminator is

\[
\Delta_{\pi,\pi'}=
\max_{\rho\in\mathcal P}
\left\|\Phi_{e,\ell}^{\pi}(\rho)-\Phi_{e,\ell}^{\pi'}(\rho)\right\|_1,
\]

for a declared finite probe family (\mathcal P\). This is the test that separates historical Se-first, N-first/S-first, and other schedule candidates.

## 12. LLM failure modes this specification blocks

An agent must be rejected or marked `PENDING` if it does any of the following:

1. Uses a historical Se-first schedule while describing a N-first deduction experiment.
2. Replaces `K-R` dephasing/rotation maps with `K-S` projector/drive/diffusion/filter maps without changing `operator_kernel_id`.
3. Calls (F\rho F^\dagger/\operatorname{Tr}(F\rho F^\dagger)) a CPTP channel without an instrument outcome and success probability.
4. Treats (A\rho) or (\rho A) as a density-state channel without a CPTP completion.
5. Treats a density-only result as proof of the full spinor/Hopf geometry.
6. Reinitializes the inner loop while claiming an unreset eight-stage/720-degree run.
7. Collapses the sixteen macro stages or the 64-slot grid into a generic four-operation Monte Carlo sequence.
8. Uses `JAX queued` or an import check as evidence that JAX ran the current Type-1 v0 simulation.
9. Deduces hot/cold, expansion/compression, or ascent/descent from a token name instead of reporting a defined functional and measured result.
10. Reintroduces psychological labels into the numerical equations as though they determined the maps.

## 13. Minimal run contract

```yaml
engine_run_contract_v1:
  carrier: density_level_qubit
  engine_id: 1_or_2
  sheet_sign: +1_or_-1
  terrain_law_id: TL-1
  operator_kernel_id: K-R_or_K-S
  schedule_id: explicit_schedule_identifier
  ordered_tokens: [four_exact_tokens]
  initial_state_sha256: required
  operator_parameters: required
  terrain_parameters_and_jumps: required
  geometry_transport_id: density_only_or_explicit_Gamma_id
  inner_initial_state_sha256: required_for_eight_stage_run
  handoff_witness: required_for_no_reset_claim
  cptp_or_instrument_witness: required
  precedence_witness: required
  claim_ceiling: bounded_density_level_stage_or_loop_test
```

This is the correct interface for ClaimGate: the gate validates a declared finite object and its evidence. It does not decide which schedule or kernel is metaphysically correct.

## 14. Immediate next owner decisions

Before anyone builds a “full 16-stage simulation,” the following must be answered explicitly:

1. Which schedule ID is active for the next run? This document deliberately refuses to guess.
2. Is the run using `K-R`, `K-S`, or a new explicitly named kernel? `K-R` is code-backed; `K-S` needs an instrument-aware implementation.
3. Which concrete (H_0,H_C,L_{r,s}^{T},P_{j,s},\tau,\epsilon,\gamma,\kappa) define the terrain law?
4. Is the claim density-level only, or does it include a declared geometry transport map (\Gamma)?
5. Does the engine require the outer-to-inner no-reset handoff? If yes, make its witness a hard ClaimGate requirement.

Until those choices are supplied, the mathematics is formal and ready to instantiate, but it must remain a structured candidate rather than a falsified-or-passing engine claim.
