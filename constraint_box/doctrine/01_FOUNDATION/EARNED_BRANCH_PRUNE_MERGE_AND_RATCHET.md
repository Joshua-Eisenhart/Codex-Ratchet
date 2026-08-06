# Earned Branching, Pruning, Merging, and Ratchet Settlement

ConstraintBox stores a branch complex instead of one mutable conversation.

## Operations

| Operation | Default | Required evidence |
|---|---|---|
| branch | permitted as proposal | explicit rival payload and parent lineage |
| preserve | default | none |
| park | allowed | named missing evidence/resource |
| split | conditional | new probe or demanded distinction |
| prune | denied by default | empty finite extension fibre under frozen contract |
| merge | denied by default | indistinguishable under all active probes and continuations |
| re-offer | explicit | changed demand, probe, bound, contract, or evidence |
| settle | plural | completed bounded comparison |

Pruning requires

\[
F_t(x)=\varnothing
\]

under a content-addressed finite contract.  Low score, low LLM confidence, or
model consensus is insufficient.

Merging requires continuation-relative equivalence:

\[
x\equiv_{D,C}y
\iff
\forall e\in\operatorname{Ext}_C,\quad
\operatorname{Obs}_D(xe)=\operatorname{Obs}_D(ye).
\]

Current-output equality alone is insufficient.

## Relative Ratchet

For candidate partition \(\pi\),

\[
L_D(\pi)=
|\{(a,b)\in D:[a]_\pi=[b]_\pi\}|.
\]

Survivors have \(L_D(\pi)=0\).  The tested frontier retains the coarsest
survivors inside each verified nesting chain and preserves non-nested rivals
as uncompared.

The runtime returns `HOLD` when:

- \(D=\varnothing\);
- there is no candidate;
- probe contracts differ;
- demand edges are invalid;
- no candidate survives;
- no verified comparable nest exists.

It never emits an absolute MSS winner.
