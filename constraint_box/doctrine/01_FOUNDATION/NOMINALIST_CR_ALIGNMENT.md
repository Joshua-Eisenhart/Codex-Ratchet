# Nominalist and Codex-Ratchet Alignment

ConstraintBox carries CR root constraints as programming restrictions while
keeping CR-specific scientific interpretations in an optional profile.

## Operational presentation, not primitive identity

For finite carrier \(X\) and probe family \(\Pi\),

\[
x\sim_\Pi y
\iff
\forall p\in\Pi,\ p(x)=p(y).
\]

The operational view is the quotient \(X/{\sim_\Pi}\).  File names, integer
labels, database keys, and SHA-256 digests are addresses.  They are not proofs
that two presentations possess or lack intrinsic identity.

## Always-on kernel rules

| Root constraint | Runtime consequence |
|---|---|
| Finitude | every executable search declares finite domains and bounds |
| No completed infinity | an unbounded search cannot return completion |
| No primitive identity | handles are references only |
| No primitive equality | semantic equivalence requires probes/relations |
| No primitive probability | unknown stays a set, interval, or `UNKNOWN` |
| No primitive metric | distances require a named carrier and metric |
| No primitive time | event order is explicit; wall time is metadata |
| No primitive causality | earlier execution does not establish causation |
| No privileged frame | coordinates/viewpoints are declared adapters |
| Noncommutation | ordered expressions and reversal controls are retained |
| No narrative-first | prose cannot write a controller disposition |
| Relative MSS only | frontier is packet-relative and candidate-relative |
| Plural survival | incomparable and untested rivals remain live |
| Purgatory | failure changes status; it does not erase lineage |
| Constraints precede axioms | candidates are tested under prior obligations |

## SMT boundary

SMT equality is equality of encoding terms.  It is not promoted to ontological
identity.  `SAT` means one witness in the declared finite encoding.  `UNSAT`
means no witness in that encoding and bound.  `UNKNOWN` parks.

ConstraintBox user vocabulary is:

- `BOUNDED_SAT`;
- `BOUNDED_UNSAT`;
- `UNKNOWN`;
- `PACKET_RELATIVE_FRONTIER`;
- `HOLD`;
- `INCOMPARABLE`;
- `BLOCKED`.

It avoids unqualified `PROVEN`, `TRUE`, `SOLVED`, or `ABSOLUTE_MSS`.

## Nested compatibility

\[
\mathcal T=
\{(x_0,\ldots,x_n):
C_i(x_i)\land R_{i+1,i}(x_{i+1},x_i)\}.
\]

Layer \(i\)'s admissible content is

\[
X_i^\*=\pi_i(\mathcal T).
\]

Locally valid layers cannot be ranked as whole candidates without a nesting
witness.  The runtime fixture enforces `HOLD` for flat candidates.

## Scientific profile separation

No-thermodynamic-literalism, no-observer-privilege, no-FTL-control, candidate
manifold geometry, QIT carriers, Hopf/Weyl/nonassociative branches, and engine
mechanics belong to the CR profile.  They are not generic assumptions imposed
on ordinary software tasks.
