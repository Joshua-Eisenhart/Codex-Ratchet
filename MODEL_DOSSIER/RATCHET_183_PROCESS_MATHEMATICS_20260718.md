# Process mathematics

## The clarification is the architecture

The Ratchet is not a one-way ladder and this pack does not replace the earlier
architecture.  It executes the clarification that was missing from the prior
run:

- there is always an operational default;
- no operational default is final;
- candidates are compared, not proved globally minimal;
- Purgatory retains beaten candidates and can re-offer them;
- nesting and nesting order are mathematical choices;
- a change at any depth causes the affected whole object to settle again;
- later requirements can change which earlier structures survive.

The directions called inward, outward, sideways, and renesting are all tested.
They are views of propagation through one nested object, not four independent
machines.

## Finite comparison law

Let

\[
Z=(b,n,e;O)
\]

be a complete finite candidate with base presentation \(b\), nesting
presentation \(n\), entropy-geometry presentation \(e\), and source packet set
\(O\).  The settling operation computes

\[
S(Z)=\bigl(D_n(O),\Phi_e,g_e,L_{n,e},L_{n,e}^{\mathrm{eff}}\bigr),
\]

where \(D_n(O)\) is the complete decoded history relation, \(\Phi_e\) is the
potential, \(g_e\) its declared Hessian metric, \(L_{n,e}\) the factor-complex
operator, and \(L_{n,e}^{\mathrm{eff}}\) the Schur-compressed inner operator.

For active requirements \(R\), each settled candidate has a failure set
\(F_R(Z)\) and an explicit presumption vector \(P(Z)\).  Candidate \(A\) beats
candidate \(B\) only when either

\[
F_R(A)\subsetneq F_R(B),
\]

or the failure sets are identical and

\[
P(A)\leq P(B)
\]

component by component, with at least one strict inequality.  Requirements
and presumption coordinates are not collapsed into one score.  Incomparable
candidates remain together on the frontier.

The current frontier is

\[
\mathcal F_R=\{Z:\nexists Y\text{ among the simulated proposals with }Y\prec_R Z\}.
\]

This is explicitly proposal-relative.  `candidate_universe_exhausted` is
always false.

## Base pass

Sixteen named base structures are executable candidates.  Every candidate is
simulated on every one of seven common four-coordinate packets before the
first comparison.  The small finite families are searched exhaustively where
that statement is possible:

- all 15 partitions;
- all 64 simple graphs and their clique families;
- every four-element partial order;
- all 65,536 set families for the matroid axioms;
- every one of the 24 variable orders for the reduced decision automaton.

The other carriers execute exact law controls and exact finite support
embeddings.  Those embeddings are sufficient simulations, not proofs that the
extra algebraic structure is necessary.

## Nesting pass

Each base survivor is crossed with eleven nesting candidates.  A nesting
candidate is a relation that settles to a set of complete three-layer states.
The engine compares the settled whole set, not merely its locally stored
edges.

The complete-pairwise and ternary presentations decode exactly the seven
baseline and eight expanded source states.  Ordered two-edge joins do not:
different orders decode 11 or 13 baseline states.  Thus the nesting order
changes the mathematical function.

## Entropic-geometric feedback pass

The process then loops back.  It re-offers all sixteen bases, all eleven
nestings, and all three declared potential/metric pairs.  This produces

\[
16\times 11\times 3=528
\]

complete candidates.  All 528 are settled before comparison.

For a decoded finite history set \(D\), the least-informative probability used
in this calibration is uniform.  The surviving potential and metric are

\[
\Phi(p)=\sum_{h\in D}p_h\log p_h,
\qquad
g_{hh'}=\frac{\partial^2\Phi}{\partial p_h\partial p_{h'}}
=\frac{\delta_{hh'}}{p_h}.
\]

Both the potential chain identity and the Fisher tangent-metric decomposition
hold exactly in the finite packet.  The quadratic/Euclidean rival is
co-generated but fails those nested chain requirements on the same histories.

Each nesting is realized as a factor complex.  Pairwise nesting introduces
binary relation factors; ternary nesting introduces three-input factors.  The
operator is the weighted factor Laplacian with a declared finite anchor.  All
non-inner nodes are eliminated:

\[
L^{\mathrm{eff}}_{II}=L_{II}-L_{IO}L_{OO}^{-1}L_{OI}.
\]

The same decoded histories determine entropy, metric weights, factor nodes,
and the compressed operator.  Expansion and renesting therefore recompute the
whole object rather than editing a label.

## Continuation and loopback

Five receipts are retained in both the nesting and whole passes:

1. structural requirements;
2. full requirements;
3. a requirement revision;
4. restoration and complete re-offer;
5. an idle tick with no new proposal.

The idle tick succeeds and retains a default.  A future proposal can be added
to the relevant registry and all comparisons rerun.  No receipt has a terminal
state.
