# Explicit nested layers of the executed constraint manifold

This is the exact layer list used by Pack 186.  A layer is not an independent
sheet placed on top of a finished lower layer.  Every listed state is a
projection of one complete compatible nest, and the active nesting `G` changes
the histories, cuts, surfaces, and functions that exist.

The shared law is: a named finite divergence or capacity supplies the entropy
comparison; its Hessian, covariance, weighted boundary operator, or quantum
geometric tensor supplies the geometry.  Geometry is not added as decoration.

## Root — constrained distinguishability and finitude

Complete candidates are finite tuples

\[
\mathcal T_G=\{(x_0,\ldots,x_{15}):
\bigwedge_r C_r(x_{\le r})\land
\bigwedge_r R_{r+1,r}(x_{r+1},x_r)\}.
\]

Operational identity is

\[
x\sim_{\Pi}y\iff \pi(x)=\pi(y)\quad\forall\pi\in\Pi,
\]

for an explicit finite probe family.  The code enumerates 1,350 complete
sections and 216 unique start contexts.  Finitude enters here: state sets,
histories, probes, parameters, and comparisons are all bounded in this run.

Entropy/geometry unity: continuation capacity is

\[
N(c)=|\{s\in\mathcal T_G:c\preceq s\}|,\qquad \kappa(c)=\log N(c),
\]

and the cells and their shared complete extensions generate the rooted complex
used at depth 0.

## Layer 0 — capacity-weighted finite admissibility complex

Every complete section gives a chain

\[
\text{root}\to G\to\text{chirality}\to\text{parameter}
\to\text{history prefix}_0\to\cdots\to\text{history prefix}_k.
\]

With node and edge extension capacities `N_v,N_e`, the executed differential
and Laplacian are

\[
d_N=W_e^{1/2}\,\partial\,W_v^{-1/2},\qquad L_N=d_N^*d_N.
\]

The entropy potential on complete-section frequencies is negative Shannon
entropy

\[
\Phi(p)=\sum_s p_s\log p_s.
\]

For a nesting partition `G`, it obeys the exact chain identity

\[
\Phi(p)=\Phi(p_G)+\sum_g p_G(g)\Phi(p_{s|g}).
\]

Its Hessian is the Fisher metric

\[
\|\dot p\|_F^2=\sum_s\frac{\dot p_s^2}{p_s},
\]

which obeys the corresponding coarse-plus-conditional chain identity.  The
same weighted nesting formula fails for the Euclidean tangent metric in this
census.  Numerically the complex has 2,713 nodes, 2,712 edges, maximum depth 7,
and spectral gap about `0.043704798532`.

## Layer 1 — operational quotient

For each start `u`, let `Lambda(u)` be its finite admissible history language.
Four probe candidates are compared:

\[
q_0(u)=0,
\quad q_d(u)=\max_{w\in\Lambda(u)}|w|,
\quad q_G(u)=G(u),
\quad q_{\rm full}(u)=u.
\]

A quotient is sufficient when

\[
q(u)=q(v)\Longrightarrow\Lambda(u)=\Lambda(v).
\]

The constant quotient fails: it merges flat starts with language `{epsilon}`
and nonflat starts with eight three-bit words.  `q_d` is sufficient with two
classes and is less presumptive than the four authored nesting labels or 216
full identities.

For class probabilities

\[
p_\theta(k)\propto p_0(k)e^{\theta f_k},
\]

the entropy is the explicitly scoped class Shannon entropy and the geometry is

\[
g=\left.\frac{d^2}{d\theta^2}D_{KL}(p_\theta\|p_0)\right|_0
=\operatorname{Var}_{p_0}(f)=1.6875.
\]

This is where Shannon is licensed; it is not a universal manifold entropy.

## Layer 2 — finite density carrier and noncommutation

The running carrier is

\[
\rho\in\mathcal D((\mathbb C^2)^{\otimes4}),\qquad
\rho\succeq0,\quad\operatorname{tr}\rho=1.
\]

The compared classical simplex and real-projective carriers retain some order
effects but fail the required complex orientation witness.  The current
packet-relative carrier is a complex two-component spinor presentation with a
positive density readout.

Noncommutation enters as

\[
\Delta_{ij}(\rho)=\tfrac12\|T_iT_j(\rho)-T_jT_i(\rho)\|_1>0.
\]

The entropies are

\[
S(\rho)=-\operatorname{tr}\rho\log\rho,
\qquad
D(\rho\|\sigma)=\operatorname{tr}\rho(\log\rho-\log\sigma),
\]

and the smooth geometry is the BKM Hessian of `D`.  Rank strata and
partial-trace fibers are the nonsmooth geometric part.

## Layer 3 — spinor sphere and Hopf projection

The local carrier chart is

\[
\psi(\eta,\phi,\chi)=
(e^{i\phi}\cos\eta,e^{i\chi}\sin\eta)\in S^3,
\]

with Hopf projection to the Bloch sphere and a `U(1)` fiber.  The projective
quantum geometric tensor is

\[
Q_{ij}=\langle\partial_i\psi|
(1-|\psi\rangle\langle\psi|)|\partial_j\psi\rangle
=g^{FS}_{ij}+\frac{i}{2}F_{ij}.
\]

Thus Fubini–Study metric and Berry curvature are the real and imaginary parts
of one tensor.  A reduced density licenses spectral entropy; quotienting the
fiber is recorded as lost phase capacity rather than falsely assigning von
Neumann entropy to an isolated pure ray.

## Layer 4 — nested Hopf tori / Schmidt shells

The explicit foliation is

\[
S^3=\bigcup_{0<\eta<\pi/2}T_\eta,
\quad
T_\eta=\{(e^{i\phi}\cos\eta,e^{i\chi}\sin\eta)\}.
\]

Its geometry and entanglement entropy are

\[
ds^2=d\eta^2+\cos^2\eta\,d\phi^2+\sin^2\eta\,d\chi^2,
\]

\[
S(\eta)=h(\cos^2\eta).
\]

The leaves are exactly entropy level sets.  In the four-qubit object, the
admitted `eta` values are obtained from actual marginal Bloch radii/Schmidt
spectra.  Changing the cut family or the channel order changes those shells.

## Layer 5 — connection, curvature, and Wilson flux

For neighboring finite spinors, the link variable is

\[
U_{ab}=\frac{\langle\psi_a|\psi_b\rangle}
{|\langle\psi_a|\psi_b\rangle|}.
\]

For each interleaf plaquette

\[
W_p=U_{i_j i_{j+1}}U_{i_{j+1}o_{j+1}}
U_{o_{j+1}o_j}U_{o_j i_j},
\qquad
\Phi_B=\operatorname{Arg}\prod_{p\subset B}W_p.
\]

In the chart actually simulated,

\[
\Phi_B\to
2\pi\bigl(\cos^2\eta_{\rm inner}-\cos^2\eta_{\rm outer}\bigr)
\]

with opposite sign on the conjugate Weyl sheet.  There are 256 explicit
plaquettes in the reference strip.  Local gauge phases cancel.  Deleting all
radial links leaves both boundary loops but no interleaf 2-cells, so relative
interleaf flux is undefined and defaults to zero.  One radial seam is also
insufficient.  A separate contractible CP1 loop has ordinary Berry flux without
two nested leaves; this is retained as the boundary of the nesting claim.

Entropy is the finite distinguishability of holonomy/phase records; geometry
is the connection and its curvature, the imaginary component of `Q`.

## Layer 6 — joint Weyl sheets and chirality

The two sheets are not stored only as marginals.  The running joint candidate is

\[
|\Psi_{LR}\rangle=
\cos\alpha\,|L,R\rangle+
e^{i\beta}\sin\alpha\,|L_\perp,R_\perp\rangle,
\qquad \rho_{LR}=|\Psi_{LR}\rangle\langle\Psi_{LR}|.
\]

The entropic vector is

\[
(S_L,S_R,S_{LR},I(L{:}R),S(L|R),I_c,\mathcal N),
\]

where

\[
I(L{:}R)=S_L+S_R-S_{LR},\quad
I_c=-S(L|R),\quad
\mathcal N=\sum_{\lambda(\rho^{T_L})<0}|\lambda|.
\]

The geometry is the BKM Hessian of joint Umegaki divergence on
`(eta,alpha,beta)`.  A Bell state and a classically correlated state with
identical L and R marginals give different joint negativity, proving that the
marginal-only candidate is insufficient.  Chirality is the `Z2` orientation
relating the two Wilson curvatures, `F_R=-F_L`.

## Layer 7 — tensor cuts and the entropy cone

For every cut `A` admitted by `G`,

\[
\rho_A=\operatorname{tr}_{\bar A}\rho.
\]

The cut entropy vector obeys the usual finite quantum inequalities, including
subadditivity and strong subadditivity where the needed marginals exist.  The
executed balanced, chain, and reverse candidates each have six active cuts but
different cut families.  Their cut divergences contribute

\[
g^{\rm cuts}_{ij}=\partial_i\partial'_j
\sum_{A\in G}D(\rho_A(\theta)\|\rho_A(\theta'))|_{\theta'=\theta}.
\]

The entropy cone and cut lattice are the geometry; mutual and conditional
quantities are coordinates on it, not extra labels.

## Layer 8 — ordered CPTP flows

Every channel is explicit:

\[
T(\rho)=\sum_aK_a\rho K_a^\dagger,
\qquad \sum_aK_a^\dagger K_a=I.
\]

Process states use the Choi density

\[
J(T)=\frac1d\sum_a|K_a\rangle\!\rangle
\langle\!\langle K_a|.
\]

The geometry compares `J(T_i o T_j)` and `J(T_j o T_i)` by trace distance and
Umegaki divergence and uses a BKM Hessian over channel parameters.  The entropy
pawl is relative entropy to the appropriate fixed structure; raw von Neumann
entropy is not assumed monotone for nonunital damping.  All sixteen native
stage pairs are distinct in Choi geometry.

## Layer 9 — finite coherent histories

For the histories selected by `G`, construct branch vectors `A_h|psi>` and the
normalized Gram state

\[
G_{hh'}=\langle A_h\psi|A_{h'}\psi\rangle.
\]

The resolved-record control is `diag(G)`.  The entropies are

\[
S_{\rm history}=S(G),\quad
S_{\rm record}=S(\operatorname{diag}G),\quad
C_{\rm rel}=S_{\rm record}-S_{\rm history}.
\]

The geometry is the BKM Hessian of `D(G_theta||G_0)`.  Balanced, chain, and
reverse orderings produce different history metrics.  Erasing off-diagonal
interference changes the metric; flat has one history and zero history metric.

## Layer 10 — nonassociative stacking and G2

The compared Cayley–Dickson ladder is

\[
\mathbb R\to\mathbb C\to\mathbb H\to\mathbb O\to\mathbb S.
\]

It is tested under

\[
[a,b]=ab-ba,\qquad
[a,b,c]=(ab)c-a(bc),\qquad
\|ab\|^2=\|a\|^2\|b\|^2.
\]

R/C fail noncommutation, H fails nonassociativity, O passes all three, and S
fails persistence.  The sedenion failure has an exact witness:

\[
(e_1+e_{10})(e_5+e_{14})=0
\]

although both factors are nonzero.

For each basis triple `t`, the full signed associator vector `a_t` is the
sufficient statistic of an exponential family.  Its entropic geometry is

\[
p_\theta(t)\propto w_t e^{\theta\cdot a_t},
\qquad
g_{ij}=\operatorname{Cov}_{p_0}(a_{t,i},a_{t,j}).
\]

The scalar associator norm was tried first and failed because all nonzero
octonion basis associators have the same norm.  The signed vector metric has
rank 7 and trace 4.  Solving the derivation constraints gives

\[
G_2=\operatorname{Der}(\mathbb O),\qquad\dim G_2=14.
\]

## Layer 11 — bounded Jordan stack and F4

The executed owner extension is the Albert algebra

\[
J_3(\mathbb O)=\{A=A^\dagger\in M_3(\mathbb O)\},
\qquad A\circ B=\tfrac12(AB+BA).
\]

The native algebra calculation derives

\[
F_4=\operatorname{Der}(J_3(\mathbb O)),\quad\dim F_4=52,
\]

and embeds an octonion derivation entrywise with Jordan-derivation defect about
`9.49e-15`.  It also derives the 78-dimensional structure algebra readout
labeled E6; E7/E8 remain cited-only and are not active layers.

On an exact positive diagonal spectral slice,

\[
\lambda_i\ge0,\quad\sum_i\lambda_i=1,
\quad S_J=-\sum_i\lambda_i\log\lambda_i,
\quad D_J(\lambda\|\mu)=\sum_i\lambda_i\log\frac{\lambda_i}{\mu_i}.
\]

The Hessian is the positive two-dimensional Fisher/BKM metric.  This executes
J3(O)/F4 but does not prove it is forced by all lower requirements.

## Layer 12 — structure reduction

The running reduction graph is

\[
SO(8)\supset Spin(7)\supset G_2\supset SU(3)\supset SU(2),
\]

with generator capacities `28,21,14,8,3` and edge codimensions `7,7,6,5`.
Each node is the stabilizer of additional structure.  The finite entropy
readout is `log(dim generator space)` and the geometry is the directed
stabilizer-inclusion graph with its codimensions.  Pack 186 does not falsely
label that count as a computed Haar orbit volume.

## Layer 13 — terrains

There are four explicitly declared channel families on each Weyl sheet.  For
terrain `t`, let `T_t` have fixed state `sigma_t`.  The two populated modes are

\[
T_t^{\uparrow}:\Delta S=S(T_t\rho)-S(\rho)>0,
\]

\[
T_t^{\downarrow}:\Delta U_t=
D(T_t\rho\|\sigma_t)-D(\rho\|\sigma_t)<0.
\]

Across 384 sampled Bloch states per terrain, both modes are populated for all
eight signed placements; relative entropy never increases in the sample.  The
terrain geometry is its fixed-point basin flow and the BKM metric of its Choi
state.  The family names Se/Ne/Ni/Si and the mapping to the proposed engine
operators remain owner-model coordinates; their existence is executed, not
claimed to have emerged without that proposal.

## Layer 14 — whole-manifold dynamics and feedback

The active smooth divergence is a sum on shared coordinates:

\[
D_G=D_{\rm history}+\sum_{A\in G}D_A
+\sum_tD_{T_t}+D_{LR},
\]

so

\[
g_G=\nabla^2D_G
=g_{\rm history}+g_{\rm cuts}+g_{\rm terrain/process}+g_{LR}.
\]

For balanced nesting the metric is

\[
\begin{pmatrix}
47.93653&12.08081&-8.75062\\
12.08081&46.82566&-7.87097\\
-8.75062&-7.87097&50.69720
\end{pmatrix},
\]

with positive eigenvalues approximately `(35.27476,42.54107,67.64356)`.
Removing any smooth component changes the whole metric.  Replacing balanced by
chain or reverse changes the settled metric.  Discrete layers simultaneously
change the domain, cuts, histories, surface cells, and stack state.

The feedback map is

\[
Z_{t+1}=\operatorname{settle}
(\operatorname{return}_{\rm terrain}(Z_t)).
\]

The selected return refits earlier carrier parameters and then rebuilds cuts,
metric, flux, terrains, and stages.  Two finite ticks reach the same default;
alternate returns remain in the record.

## Layer 15 — response polarity / Axis 0

The response remains a vector:

\[
g_{r,k}(\delta)=
\frac{d(X^\delta_{r,k},X_{r,k})}
{d(X^\delta_{0,k},X_{0,k})}.
\]

Its entries include continuation-capacity change, boundary entropy, mutual
information, coherent-history evidence, process-order distance, and Wilson
flux.  They are not collapsed into a universal score.  The inherited
64-coordinate Walsh response candidate executes and reconstructs its four
response families, but the extra 48 coordinates do not improve the existing
16-stage separation; it remains a tested coordinate candidate.

At the stage boundary, composition order changes all sixteen states/Choi
objects.  Fourteen pairs also produce distinct nested shells and nonzero
Wilson flux.  Stages 3 and 11 have equal shell radius and zero interleaf flux;
that negative result is retained.

## Current depth and open continuation

All root-through-15 objects above run in one finite campaign.  Balanced is the
default; chain and reverse remain unbeaten nonflat alternatives.  The Ratchet
can next add finer complete sections, new carrier/stack competitors, another
nesting graph, or a measured physical constraint and recompute every affected
projection.  There is intentionally no “absolute maximum depth” or final MSS.
