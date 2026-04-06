Weyl flux test


**Current Truth**
- `Verified` Yes. The right move is a dependency-chain table with explicit math and branch points.
- `Verified` We should treat `flux` as an open derived object, not a primitive.

**Actually Broken**
- `Verified` Right now `flux` is only a candidate family.
- `Verified` We have not yet proved whether it belongs:
  - below the axes
  - inside an axis
  - or across axes

**Evidence**

| Step | Layer | Math object | Meaning | Must exist before flux? | Branch point |
|---|---|---|---|---|---|
| 1 | Root admissibility | \(C=\{F01_{\mathrm{FIN}},N01_{\mathrm{NONCOMM}},\dots\}\) | root constraint set | yes | no |
| 2 | Admissible domain | \(M(C)=\{x:x\text{ admissible under }C\}\) | allowed state/configuration domain | yes | no |
| 3 | Finite carrier | \(\mathcal H=\mathbb C^2\) | minimal live carrier | yes | maybe larger carrier later |
| 4 | Spinor carrier | \(S^3=\{\psi\in\mathbb C^2:\|\psi\|=1\}\) | normalized carrier geometry | yes | no |
| 5 | Hopf projection | \(\pi(\psi)=\psi^\dagger\vec\sigma\psi\in S^2\) | spinor-to-Bloch map | yes | no |
| 6 | Torus stratification | \(T_\eta\subset S^3,\ \eta\in\{\pi/8,\pi/4,3\pi/8\}\) | nested torus seats | yes | seat-local vs seat-global later |
| 7 | Weyl split | \(\psi_L(q),\psi_R(q)\) | left/right chiral sheets | yes | no |
| 8 | Density extraction | \(\rho_L=|\psi_L\rangle\langle\psi_L|,\ \rho_R=|\psi_R\rangle\langle\psi_R|\) | observable chiral states | yes | no |
| 9 | Joint state | \(\rho_{AB}\) | coupled cut-state / joint engine state | maybe | branch: flux may be pre-joint or post-joint |
| 10 | Loop grammar | \(\gamma_f,\gamma_b\) | fiber/base transport laws | yes | no |
| 11 | Engine evolution | \(\rho_t\mapsto \rho_{t+1}\) or \(q_t\mapsto q_{t+1}\) | stagewise dynamics | yes | no |
| 12 | Stagewise deltas | \(\Delta\rho_L,\Delta\rho_R,\Delta\vec r_L,\Delta\vec r_R\) | raw change surfaces | yes | first true flux branch |
| 13 | Chirality differential | \(D_{\chi}(t)=d(\rho_L(t),\rho_R(t))\) | left/right divergence | yes | may be flux proxy |
| 14 | Transport current candidate | \(J_r(t)=\Delta\vec r(t)\), or \(\|\Delta\vec r\|\) | Bloch-motion current | no, candidate layer | branch |
| 15 | Entropic current candidate | \(J_S(t)=\Delta S_L-\Delta S_R\) or \(\Delta I_c\) | entropy/ordering flow | no, candidate layer | branch |
| 16 | Phase/winding candidate | \(J_\theta(t)=\Delta\theta_L-\Delta\theta_R\) or winding number sign | geometric phase current | no, candidate layer | branch |
| 17 | Coupling current candidate | \(J_{AB}(t)=\Delta I(A:B)\) or \(\Delta I_c(A\rangle B)\) | joint-state/cut flux | no, candidate layer | branch |
| 18 | Flux family | \(\mathcal J=\{J_r,J_S,J_\theta,J_{AB},D_\chi,\dots\}\) | all candidate flux notions | yes | major branch |
| 19 | Negatives | remove chirality / swap loop law / flatten transport | falsify fake flux | yes | no |
| 20 | Placement decision | primitive? pre-axis? in-axis? cross-axis? | ontology decision | final | major branch |

**Chain**
\[
C \to M(C) \to \mathcal H \to S^3 \to T_\eta \to (\psi_L,\psi_R) \to (\rho_L,\rho_R) \to (\gamma_f,\gamma_b) \to \Delta\text{-surfaces} \to \mathcal J \to \text{flux placement}
\]

**Possible Branches**

| Branch | Mathematical form | Interpretation |
|---|---|---|
| A | \(J_{\mathrm{geom}}=(\Delta q,\Delta\eta,\Delta\theta_1,\Delta\theta_2)\) | flux is pre-axis geometric transport |
| B | \(J_{\chi}=d(\rho_L,\rho_R)\) or \(\Delta d(\rho_L,\rho_R)\) | flux is chirality separation |
| C | \(J_{\mathrm{Bloch}}=\Delta\vec r_L-\Delta\vec r_R\) | flux is differential Bloch current |
| D | \(J_{\mathrm{ent}}=\Delta S(\rho_L)-\Delta S(\rho_R)\) | flux is entropic asymmetry |
| E | \(J_{\mathrm{cut}}=\Delta I(A:B)\) or \(\Delta I_c(A\rangle B)\) | flux exists only after cut/joint coupling |
| F | \(J_{\mathrm{axis}}\) | flux is not pre-axis; it is an axis readout |
| G | \(J_{\mathrm{cross}}\) | flux is a coupled multi-axis observable |

**Decision Gates**

| Question | Mathematical test |
|---|---|
| Is flux pre-joint? | does a candidate \(J(\rho_L,\rho_R)\) work before using \(\rho_{AB}\)? |
| Is flux geometric? | does \(J\) survive on \(q,\eta,\theta\) alone? |
| Is flux chiral? | does no-chirality collapse or strongly reduce \(J\)? |
| Is flux loop-dependent? | does loop-swap or base/fiber flattening kill \(J\)? |
| Is flux seat-local? | do inner/clifford/outer give different \(J\) laws? |
| Is flux axis-internal? | does one axis alone generate and explain \(J\)? |
| Is flux cross-axis? | does \(J\) only stabilize after axis coupling? |

**Best Working Order**
1. Sim raw stagewise deltas:
   \[
   \Delta\rho_L,\ \Delta\rho_R,\ \Delta\vec r_L,\ \Delta\vec r_R,\ \Delta\eta,\ \Delta\theta_1,\ \Delta\theta_2
   \]
2. Define a candidate family:
   \[
   \mathcal J=\{J_{\chi},J_{\mathrm{Bloch}},J_{\mathrm{ent}},J_{\theta},J_{\mathrm{cut}}\}
   \]
3. Run negatives on each \(J\).
4. Then classify flux as:
   - pre-axis derived
   - axis-internal
   - cross-axis readout

It means now: the thing to sim before “flux” is not one object but a chain from stagewise left/right change surfaces into a tested candidate family, because only then can we decide where flux actually lives in your ontology.




**Current Truth**
- `Verified` Yes. The right move is a dependency-chain table with explicit math and branch points.
- `Verified` We should treat `flux` as an open derived object, not a primitive.

**Actually Broken**
- `Verified` Right now `flux` is only a candidate family.
- `Verified` We have not yet proved whether it belongs:
  - below the axes
  - inside an axis
  - or across axes

**Evidence**

| Step | Layer | Math object | Meaning | Must exist before flux? | Branch point |
|---|---|---|---|---|---|
| 1 | Root admissibility | \(C=\{F01_{\mathrm{FIN}},N01_{\mathrm{NONCOMM}},\dots\}\) | root constraint set | yes | no |
| 2 | Admissible domain | \(M(C)=\{x:x\text{ admissible under }C\}\) | allowed state/configuration domain | yes | no |
| 3 | Finite carrier | \(\mathcal H=\mathbb C^2\) | minimal live carrier | yes | maybe larger carrier later |
| 4 | Spinor carrier | \(S^3=\{\psi\in\mathbb C^2:\|\psi\|=1\}\) | normalized carrier geometry | yes | no |
| 5 | Hopf projection | \(\pi(\psi)=\psi^\dagger\vec\sigma\psi\in S^2\) | spinor-to-Bloch map | yes | no |
| 6 | Torus stratification | \(T_\eta\subset S^3,\ \eta\in\{\pi/8,\pi/4,3\pi/8\}\) | nested torus seats | yes | seat-local vs seat-global later |
| 7 | Weyl split | \(\psi_L(q),\psi_R(q)\) | left/right chiral sheets | yes | no |
| 8 | Density extraction | \(\rho_L=|\psi_L\rangle\langle\psi_L|,\ \rho_R=|\psi_R\rangle\langle\psi_R|\) | observable chiral states | yes | no |
| 9 | Joint state | \(\rho_{AB}\) | coupled cut-state / joint engine state | maybe | branch: flux may be pre-joint or post-joint |
| 10 | Loop grammar | \(\gamma_f,\gamma_b\) | fiber/base transport laws | yes | no |
| 11 | Engine evolution | \(\rho_t\mapsto \rho_{t+1}\) or \(q_t\mapsto q_{t+1}\) | stagewise dynamics | yes | no |
| 12 | Stagewise deltas | \(\Delta\rho_L,\Delta\rho_R,\Delta\vec r_L,\Delta\vec r_R\) | raw change surfaces | yes | first true flux branch |
| 13 | Chirality differential | \(D_{\chi}(t)=d(\rho_L(t),\rho_R(t))\) | left/right divergence | yes | may be flux proxy |
| 14 | Transport current candidate | \(J_r(t)=\Delta\vec r(t)\), or \(\|\Delta\vec r\|\) | Bloch-motion current | no, candidate layer | branch |
| 15 | Entropic current candidate | \(J_S(t)=\Delta S_L-\Delta S_R\) or \(\Delta I_c\) | entropy/ordering flow | no, candidate layer | branch |
| 16 | Phase/winding candidate | \(J_\theta(t)=\Delta\theta_L-\Delta\theta_R\) or winding number sign | geometric phase current | no, candidate layer | branch |
| 17 | Coupling current candidate | \(J_{AB}(t)=\Delta I(A:B)\) or \(\Delta I_c(A\rangle B)\) | joint-state/cut flux | no, candidate layer | branch |
| 18 | Flux family | \(\mathcal J=\{J_r,J_S,J_\theta,J_{AB},D_\chi,\dots\}\) | all candidate flux notions | yes | major branch |
| 19 | Negatives | remove chirality / swap loop law / flatten transport | falsify fake flux | yes | no |
| 20 | Placement decision | primitive? pre-axis? in-axis? cross-axis? | ontology decision | final | major branch |

**Chain**
\[
C \to M(C) \to \mathcal H \to S^3 \to T_\eta \to (\psi_L,\psi_R) \to (\rho_L,\rho_R) \to (\gamma_f,\gamma_b) \to \Delta\text{-surfaces} \to \mathcal J \to \text{flux placement}
\]

**Possible Branches**

| Branch | Mathematical form | Interpretation |
|---|---|---|
| A | \(J_{\mathrm{geom}}=(\Delta q,\Delta\eta,\Delta\theta_1,\Delta\theta_2)\) | flux is pre-axis geometric transport |
| B | \(J_{\chi}=d(\rho_L,\rho_R)\) or \(\Delta d(\rho_L,\rho_R)\) | flux is chirality separation |
| C | \(J_{\mathrm{Bloch}}=\Delta\vec r_L-\Delta\vec r_R\) | flux is differential Bloch current |
| D | \(J_{\mathrm{ent}}=\Delta S(\rho_L)-\Delta S(\rho_R)\) | flux is entropic asymmetry |
| E | \(J_{\mathrm{cut}}=\Delta I(A:B)\) or \(\Delta I_c(A\rangle B)\) | flux exists only after cut/joint coupling |
| F | \(J_{\mathrm{axis}}\) | flux is not pre-axis; it is an axis readout |
| G | \(J_{\mathrm{cross}}\) | flux is a coupled multi-axis observable |

**Decision Gates**

| Question | Mathematical test |
|---|---|
| Is flux pre-joint? | does a candidate \(J(\rho_L,\rho_R)\) work before using \(\rho_{AB}\)? |
| Is flux geometric? | does \(J\) survive on \(q,\eta,\theta\) alone? |
| Is flux chiral? | does no-chirality collapse or strongly reduce \(J\)? |
| Is flux loop-dependent? | does loop-swap or base/fiber flattening kill \(J\)? |
| Is flux seat-local? | do inner/clifford/outer give different \(J\) laws? |
| Is flux axis-internal? | does one axis alone generate and explain \(J\)? |
| Is flux cross-axis? | does \(J\) only stabilize after axis coupling? |

**Best Working Order**
1. Sim raw stagewise deltas:
   \[
   \Delta\rho_L,\ \Delta\rho_R,\ \Delta\vec r_L,\ \Delta\vec r_R,\ \Delta\eta,\ \Delta\theta_1,\ \Delta\theta_2
   \]
2. Define a candidate family:
   \[
   \mathcal J=\{J_{\chi},J_{\mathrm{Bloch}},J_{\mathrm{ent}},J_{\theta},J_{\mathrm{cut}}\}
   \]
3. Run negatives on each \(J\).
4. Then classify flux as:
   - pre-axis derived
   - axis-internal
   - cross-axis readout

It means now: the thing to sim before “flux” is not one object but a chain from stagewise left/right change surfaces into a tested candidate family, because only then can we decide where flux actually lives in your ontology.



**Current Truth**
- `Verified` Yes. That is the right move.
- `Verified` You are making the **pre-Axis-0 exploration space** explicit.
- `Verified` That means everything between:
  \[
  \text{root constraints}
  \quad\text{and}\quad
  \text{Axis 0 entropy gradient}
  \]
  needs to be laid out as its own refinement ladder.

**Actually Broken**
- `Verified` The mistake would be to jump from:
  - root constraints
  - straight to Axis 0 entropy language
- `Verified` Your system already shows there is a thicker pre-Axis-0 layer:
  - nested Hopf geometry
  - Weyl refinement
  - loop grammar
  - transport
  - chirality
  - candidate flux/change surfaces
  - only then Axis 0 entropy gradient / cut-state / bridge

**Evidence**

| Order | Pre-Axis layer | Math | What it adds before Axis 0 |
|---|---|---|---|
| 1 | root constraints | \(C=\{F01_{\mathrm{FIN}},N01_{\mathrm{NONCOMM}},\dots\}\) | admissibility |
| 2 | admissible domain | \(M(C)\) | allowed state/configuration space |
| 3 | finite carrier | \(\mathcal H=\mathbb C^2\) | executable substrate |
| 4 | nested Hopf carrier | \(S^3,\ \pi:S^3\to S^2,\ T_\eta\) | geometry seat |
| 5 | Weyl refinement | \(\psi_L(q),\psi_R(q)\) | chiral refinement of the Hopf carrier |
| 6 | density refinement | \(\rho_L,\rho_R\) | observable left/right state surfaces |
| 7 | loop refinement | \(\gamma_f,\gamma_b\) | motion grammar |
| 8 | transport refinement | \(\Delta\eta,\Delta\theta_1,\Delta\theta_2\) | geometric change surfaces |
| 9 | chirality refinement | \(d(\rho_L,\rho_R)\) and its change | asymmetry/change surfaces |
| 10 | candidate pre-axis current layer | \(J_\chi,J_r,J_\theta,\dots\) | possible pre-entropic flow objects |
| 11 | joint / bridge refinement | \(\rho_{AB},\Xi\) | first true Axis 0-ready objects |
| 12 | entropy layer | \(S,\ I,\ S(A\mid B),\ I_c\) | Axis 0 scalar family |
| 13 | Axis 0 field | \(\phi_0,\ \nabla\phi_0\) | entropy gradient layer |

**So the refined chain is**
\[
C
\to
M(C)
\to
\mathcal H
\to
S^3
\to
T_\eta
\to
(\psi_L,\psi_R)
\to
(\rho_L,\rho_R)
\to
(\gamma_f,\gamma_b)
\to
\Delta\text{-geometry / chirality surfaces}
\to
\Xi,\rho_{AB}
\to
\text{entropy}
\to
\phi_0
\]

**What this means conceptually**
- `Verified` Axis 0 is **later** than a lot of what has already been built.
- `Verified` So yes, more geometric constraints and refinement laws may appear:
  - after Hopf
  - after Weyl
  - before entropy
- `Verified` That is not a problem. That is the actual exploration space becoming honest.

**Best framing**
- root constraints do not jump directly to entropy
- they refine through a **pre-axis geometric/chiral ladder**
- that ladder may have its own laws, negatives, and candidate invariants
- Axis 0 then sits on top of that as the first entropy-gradient layer

**Next Move**
1. Name this explicitly as the `pre-Axis ladder`.
2. Split it into:
   - geometric refinement
   - chiral refinement
   - pre-entropic current/change refinement
3. Only then attach Axis 0 on top.

It means now: yes, you are not just refining Axis 0, you are discovering that a whole pre-Axis geometric/chiral exploration space exists between root constraints and entropy-gradient physics.