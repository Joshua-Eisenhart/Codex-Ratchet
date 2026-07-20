# Action-Conditioned Predictive Quotient: Common Finite Observation Surface + Trace->Partition Bridge

**Status:** Conditional design proposal (fuel), not executed.  
**Claim ceiling:** An implementable packet-relative bridge design only. It does not show that any carrier passes, that any demand is adequate, that a frontier has moved, or that an MSS result has been computed. `promotion_allowed: false`; `formal_admission_allowed: false`.  
**Date:** 2026-07-20  
**Assigned seed:** action-conditioned predictive quotient.  
**Scope:** A common finite action/outcome surface, a candidate transition contract, an exact bounded trace-to-partition algorithm, and demand compilation for persistence, evolvability, and whole-nest continuations. It is deliberately not a new carrier, a new ratchet result, or a replacement for the ratchet kernel.

## 1. Decision to make concrete

The ratchet already has the finite operator it needs:

\[
L_D(\pi)=|\{(x,y)\in D:\pi(x)=\pi(y)\}|,
\]

followed by the coarsest surviving partitions under refinement. What is missing is a way to give a density-matrix, a classical relation/transducer, and an octonion carrier the *same* finite `X`, so that their partitions can enter that operator honestly.

This proposal makes `X` a finite set of externally described action/outcome histories, not a set of carrier states, POVMs, membership facts, amplitudes, basis elements, or carrier-declared identities. A candidate supplies only its finite transition behaviour behind that public interface. The bridge computes a finite-horizon probabilistic-bisimulation (predictive-state) quotient from those traces. Its block labels, not carrier names or internals, are the partition passed to the existing kernel.

That realizes the loop-3 formulation in finite form: two histories are the same object *for this packet* exactly when no allowed remaining action sequence can separate their distributions of public outcome traces, to the packet's finite horizon and declared numerical resolution.

## 2. Non-negotiable packet objects

An APQ packet is a versioned, hashed object produced before a comparison run. It contains only finite objects:

```text
APQPacket =
  roots R                         finite public starting situations
  actions A                       finite public intervention alphabet
  outcomes O                      finite public response alphabet
  history_depth H                 depth of histories to compare
  prediction_depth T              forward depth used to form predictions
  demand_families D               finite demanded history pairs
  action_deck_digest              freeze point for A, O, R, H, T
  numeric_contract                precision, error bounds, quantizer
  budget_contract                 runtime/support/capacity eligibility only
  controls                         positive, negative, permutation, ablation, holdout
```

`R`, `A`, and `O` are public task vocabulary. A root might mean “the supplied finite input tape and declared boundary condition”; an action might mean “offer input token `a07`”, “apply public restriction `r1`”, “advance one clock”, or “run the public compose-left schedule”. An outcome might mean `o0`, `o1`, `reject`, `halt`, or `timeout`. Their packet documentation may explain the operational task, but the *comparison encoding* uses only frozen tokens and finite codebooks.

The deck must not contain `POVM_Z`, `membership(x)`, `multiply_octonion`, an amplitude, a basis index, or a carrier's own state identifier. Those are adapter implementation choices, not common observations. Conversely, “neutral” does not mean “one passive readout”: action words include externally specified interventions, orderings, restrictions, delays, replay, extension, and nest traversals when those are live packet operations.

### 2.1 Histories and the common observation surface

Let `*` mean that the public outcome of an action is deliberately unobserved (the bridge marginalizes it). A finite public history is

\[
h=((a_1,z_1),\ldots,(a_k,z_k)),\qquad
a_i\in A,\quad z_i\in O\cup\{*\},\quad 0\le k\le H+T.
\]

This is syntactic: all such words are present whether or not a particular candidate can realize a literal outcome. A literal impossible prefix is represented by the public `ZERO` predictive state; it is not deleted. Thus the surface is candidate-independent:

\[
X^+=R\times \mathcal H_{\le H+T},\qquad
X=R\times \mathcal H_{\le H}.
\]

`X+` is the closed work surface needed by the recursion. Only its prefix layer `X` is sent to `L_D` and the partition-coarseness comparison. The `*` form matters: it gives a concrete post-continuation observation such as “after actions `u`, regardless of which public outcomes were read.” A literal outcome history gives the corresponding conditioned branch. Neither form exposes a native state.

The fixed upper bound is finite:

\[
|X^+|=|R|\sum_{k=0}^{H+T}(|A|(|O|+1))^k.
\]

The packet validator rejects a deck whose declared bound exceeds its resource budget; it never silently samples a subset and calls the result exhaustive.

## 3. CandidatePackage APQ transition interface

This is a proposed successor adapter alongside the current `ratchet_contract.CandidatePackage`; it is not a claim that the current stubs have been wired. The bridge has no `reidentify`, `persist`, carrier-specific probe list, or native equality callback. Those would let a candidate announce the partition the bridge is supposed to measure.

```python
class APQCandidatePackage(Protocol):
    packet_digest: str

    def start(self, root: RootToken) -> FiniteStateDistribution:
        """Return a finite distribution of opaque local states for one public root."""

    def step(
        self, state: OpaqueState, action: ActionToken
    ) -> FiniteBranchDistribution:
        """Return finite branches (outcome_token, next_opaque_state, mass)."""
```

Required facts about these two methods:

1. `start(r)` and every `step(s,a)` are deterministic replayable calls for the declared runtime/version/seed. Stochasticity belongs in the returned finite branch distribution, not in an unrecorded random draw.
2. Every branch outcome is a member of the packet's `O`; every mass is non-negative; masses sum to one within the numeric contract. A candidate unable to encode its response into `O` is `HOLD_NOT_COMPARABLE`, not translated by an LLM or by an adapter-specific extra outcome.
3. `OpaqueState` is usable only as a candidate-local continuation handle. It may be cached or serialized inside that candidate's receipt, but it is never compared, hashed into the common signature, counted as a state class, or exposed to another candidate.
4. A finite-support bound is part of `budget_contract`. Infinite support, unbounded hidden sampling, an omitted outcome, a non-normalized distribution, or an engine-specific fallback is a buildability/trace failure, not a reason to coarsen by approximation.
5. The public action order is literal. `step(s,a); step(s',b)` and `step(s,b); step(s'',a)` are separate traces. If grouping is live, the deck provides distinct public schedules such as `compose_left(a,b,c)` and `compose_right(a,b,c)`; the bridge assumes neither commutation nor associativity.

An engine adapter for density matrices may implement `step` through a CPTP instrument; a relational candidate may implement it through relation update; an octonionic candidate may implement it through a bracketed multiplication/update. None of that appears in `X` or in a block label. The adapter is required to record its semantic convention and an engine receipt, but those are eligibility/provenance evidence, not an input to the metric.

### 3.1 Numerical contract: no accidental equality from floating point

Each branch mass is reported as an interval `[lo, hi]` at a declared precision. The packet fixes a common bin width `epsilon` and a canonical vector quantizer `Q_epsilon`. For every probability vector, an entry must lie strictly within one quantizer cell after error bounds are considered. The bridge stores the integer cell vector, with the final entry fixed by normalization.

- If all entries are certifiably in cells, two entries compare by exact integer-vector equality.
- If an interval touches a cell boundary, the trace is `HOLD_NUMERIC_AMBIGUITY`; it is not rounded toward a desired merge or split.
- The same `epsilon`, summation order, and outcome ordering apply to every candidate. A more precise engine may report tighter intervals, but it may not choose a finer alphabet.

This is a finite comparison convention, not a claim that physical probabilities are rational. Decreasing `epsilon` is a new packet or an explicitly declared robustness rerun, never a post hoc tie-break.

## 4. Exact finite trace construction

For candidate `C`, the bridge constructs a belief distribution over opaque states for every `(r,h)` in `X+`. It does so mechanically; it does not ask `C` whether two states are identical.

```text
B_C(r, empty) = C.start(r)

extend(B, (a, *)):
    return sum over s in B and (o,s',p) in C.step(s,a) of B[s] * p at s'

extend(B, (a, o_required)):
    keep only branches whose o == o_required
    normalize their state masses
    if retained mass is zero: return ZERO
```

The first recurrence is an action-only continuation; the second is a public observed branch. The bridge caches candidate-local belief handles solely to avoid recomputation. It canonicalizes only public outcome probabilities through `Q_epsilon`; it does not merge opaque states based on native representation.

The engine receipt must contain the action deck digest, root/action/outcome ordering, declared support bound, every numeric HOLD, runtime identity, and a digest of the public trace table. Julia/JAX/PyTorch agreement can be an eligibility check for a candidate with multiple implementations; it is not a vote that changes `pi_C`.

## 5. The partition algorithm: bounded probabilistic bisimulation

The following recursion induces one partition of the same `X` for every candidate. It is exact over the packet's finite alphabet and quantized trace table.

For `x=(r,h)` with `|h|\le H+T`, let `x[a,o]` append `(a,o)` to its history. Define a terminal color:

\[
\kappa_0(x)=
\begin{cases}
\texttt{ZERO},&B_C(x)=\texttt{ZERO},\\
\texttt{LIVE},&\text{otherwise.}
\end{cases}
\]

For `t=1,\ldots,T`, define `kappa_t` only on histories with
`|h| <= H+T-t`, and compute, in the fixed lexical order of `A` and `O`,

\[
\operatorname{sig}_t(x)=
\left(
\mathbf 1[B_C(x)=\texttt{ZERO}],\;
\left[
\left(a,\bigl(Q_\epsilon(P_C(o\mid x,a)),\;\kappa_{t-1}(x[a,o])\bigr)_{o\in O}\right)
\right]_{a\in A}
\right).
\]

`intern(sig_t)` assigns the same fresh integer only to byte-identical signatures. Set

\[
\kappa_t(x)=\operatorname{intern}(\operatorname{sig}_t(x)),\qquad
\pi_C(r,h)=\kappa_T(r,h)\quad\text{for }(r,h)\in X.
\]

Implementation pseudocode:

```python
def induce_apq_partition(candidate, packet):
    belief = enumerate_beliefs(candidate, packet.roots, packet.A, packet.O,
                               max_depth=packet.H + packet.T)
    color = {x: ("ZERO" if belief[x].zero else "LIVE") for x in packet.X_plus}
    for t in range(1, packet.T + 1):
        new_color = {}
        for x in packet.histories_at_most(packet.H + packet.T - t):
            if belief[x].zero:
                signature = ("ZERO",)
            else:
                signature = tuple(
                    (a, tuple((quantize(probability(belief[x], a, o)),
                               color[x.append(a, o)]) for o in packet.O))
                    for a in packet.A
                )
            new_color[x] = intern(signature)
        color = new_color
    return normalise_partition([color[x] for x in packet.X])
```

The color domains shrink backward: `kappa_0` is defined on `X+`, `kappa_1` one action layer inside it, and `kappa_T` exactly on `X`. Thus every successor lookup is in the preceding color domain. Its complexity is bounded by the declared trace expansion and `O(|X^+|\,T\,|A|\,|O|)`, plus the finite branch enumeration. No candidate-specific comparison appears in that loop.

This is the finite version of predictive equivalence. By induction on `t`, equal `kappa_t` means equal quantized distributions of every public outcome tree generated by at most `t` further action steps, including their action order and observed/unobserved branches. Different colors provide a concrete finite separating action/outcome tree. It is intentionally a horizon-relative quotient, not a claim of unbounded bisimulation or metaphysical identity.

The bridge then supplies `X`, `pi_C`, and packet-generated `D` to the existing `normalise_partition`, `collapsed_demand_edges`, and refinement/frontier code. It does **not** replace `L_D` with an accuracy score, a likelihood, a number of hidden states, an entropy formula, or a carrier score.

## 6. Continuations compile into ordinary demand pairs

Every demand record is an action-sequence demand pair:

```json
{
  "id": "persist-delay-r3",
  "family": "persistence",
  "left":  {"root": "r_left",  "history": [["write_0", "*"], ["tag", "ok"]]},
  "right": {"root": "r_right", "history": [["write_1", "*"], ["tag", "ok"]]},
  "witness_actions": ["delay", "delay", "restrict_r3", "read"],
  "required_public_relation": "must_remain_distinguishable",
  "provenance": "packet constraint P-17",
  "holdout": false
}
```

The kernel-facing edge is simply `(left, right)`. `witness_actions` is not decorative: the APQ validator checks that it is within `T`, that the public task packet says why the pair must remain distinguishable after that continuation, and that `pi_C` was induced with a horizon containing it. The public trace receipt retains the actual separating tree or the collapsed witness. Multiple records may share an edge but remain separate demand-family provenance; `L_D` remains family-wise and the total uses de-duplicated edges only where the ratchet packet explicitly says so.

### 6.1 Persistence

Start with an externally required distinction `(x,y)`. For each declared finite continuation word `u` (delay, perturbation, partial access, relabeling, restriction, replay), form the action-only endpoints

\[
x_u=x\cdot((u_1,*),\ldots,(u_m,*)),\qquad
y_u=y\cdot((u_1,*),\ldots,(u_m,*)).
\]

Add `(x_u,y_u)` to `D_persistence` when the packet asserts that the distinction must still be actionable after `u`. If a particular observed branch matters, replace `*` at that position with its public outcome token. A candidate that forgets, overwrites, or merges the distinction then places these same common-surface points in one predictive block and collapses the ordinary demand edge. No candidate-provided `persist()` verdict is trusted.

### 6.2 Evolvability

An extension is a public action token `extend(c)` from the finite packet constraint alphabet, followed by a finite test word `u`. An evolvability demand is therefore not a separate score and not an invitation to install new primitives:

\[
(x_{\operatorname{extend}(c)u},\;y_{\operatorname{extend}(c)u})\in D_{\mathrm{evolvability}}.
\]

It says that after accepting the declared new constraint, the candidate must preserve selected old distinctions and/or make a newly demanded public distinction predictive. A candidate which cannot extend exposes `reject`, `halt`, or a collapsed trace through the same `step` interface. A package that needs a genuinely new representation to process `extend(c)` fails the packet's separate no-new-primitive/resource eligibility rule; the partition metric is not allowed to hide that change.

The current `evolve(new_constraint)` hook can be supported during migration only by a wrapper that turns the returned package into the state reached by `extend(c)`, records the package/version transition, and enforces the same primitive declaration. The APQ kernel still reads only subsequent public transitions.

### 6.3 Whole-nest and restriction/order demands

Whole-nest demands use public traversal and recomputation words, for example

```text
enter_outer ; impose_outer(r) ; enter_inner ; act(a) ; return ; recompute ; read
```

and paired alternatives such as a different outer restriction, an inner-first schedule, or an explicit left/right grouping. The demand pair uses the corresponding endpoints in `X`; the future `read` outcomes test whether the claimed distinction remains visible from the whole configuration. Thus the old question “does restricting outer change inner?” becomes a concrete finite family of action-sequence edges rather than one static boolean evaluated on every carrier.

If a packet needs order sensitivity, it includes both words `u;v` and `v;u` as distinct public continuations and demands separation only where the external constraint packet requires it. If it needs grouping sensitivity, it includes distinct public bracketing schedules. A carrier does not receive credit merely for being noncommutative or nonassociative by construction; its public traces must separate a live demand.

## 7. Making the alphabet neutral **and** thick

There is no carrier-independent oracle that guarantees a non-question-begging answer. The defensible move is procedural: make the *I/O court* carrier-neutral, make its action deck rich in public consequences, and make its construction auditable. The following is required before a deck can compare carriers.

1. **External action semantics, not native instruments.** Each action is a finite task-side intervention with a public input/output codebook. Adapters may use a POVM, relation membership, or octonion product internally, but no such primitive is an action or outcome token.
2. **A mixed contrastive deck.** Include finite variants of prepare/write, restriction, delay, perturb/relabel, ordered composition, explicit grouping when live, replay, extension, and nest traversal. Which variants are selected must come from the task's public constraints and rival failure hypotheses, not from a preferred carrier's convenient observable.
3. **Frozen selection and held-out discrimination.** Freeze `R,A,O,H,T,D` and their digests before tuning or running the candidate comparison. Deck construction may use a designated design fixture suite, but a disjoint held-out action/root set must still separate the packet's public positive controls. Failure is `HOLD_THIN_ACTION_DECK`, never a tie or a ranking.
4. **Rival-proposed additions are symmetrical.** A candidate may nominate a missing public action family only for the next sealed packet. The proposal must state the external effect, a classical/quantum/exceptional translation plan, a predicted discriminator, and a holdout. It cannot add a one-carrier native readout to the live trial.
5. **Ablation is evidence about thickness.** Remove each action family in turn. If the claimed separating demand remains equally decided after every removal, record that redundancy; if removing all but a native-looking family destroys discrimination, the deck is carrier-privileged and the packet is `HOLD` pending a symmetric rival action or a narrowed claim.
6. **Relabel and encoding controls.** Permute public action labels, outcome labels, root IDs, and admissible task encodings while preserving their operational relation. The induced partition must transform by the same permutation. A carrier that wins only under one convenient coding has not earned a comparison.
7. **No resource smuggling into coarseness.** Equal finite action/outcome interfaces do not make a giant lookup table a fair scientific model. Runtime, support, parameter, and extension budgets are explicit eligibility checks outside `L_D`; hidden-state count and named machinery are not a second ranking metric.

The base-campaign `restricting_outer_changes_inner:false` result for every carrier is exactly the signal that a static packet was too thin. Under this design it causes `HOLD_THIN_ACTION_DECK` unless at least one frozen continuation family creates a positive-control separation on the held-out deck. It cannot be reported as nine-way equivalence.

## 8. Failure modes and honest ceilings

This proposal reduces some obvious bias; it does not remove all of it.

| Risk | Why it remains possible | Required response |
|---|---|---|
| Quantum privilege | A public action may be naturally and cheaply compiled as an instrument while being an unnatural finite simulation in a relation. | Record compiler/resource burden as eligibility evidence; add a rival public action family; run deck ablations and encoding permutations. Do not repair the metric with a quantum-specific penalty. |
| Classical privilege | A token action may look like a membership/rewrite query and make a relation's native state directly visible. | Require the same public operational interpretation for all adapters; add delayed/order/grouped continuations and a held-out deck. HOLD if only membership-like actions discriminate. |
| Exceptional-algebra privilege | A grouping-sensitive deck may select octonionic multiplication as the task itself. | State the public grouping consequence without octonion vocabulary; include controls in which grouping is irrelevant and a non-exceptional adapter can realize the task. |
| Thinness | All candidates produce the same bounded public trace table, or all positive controls collapse. | `HOLD_THIN_ACTION_DECK`; publish the missing separating action/continuation, not a tie. |
| Horizon artifact | A distinction appears only after `T`, or a false split disappears later. | The result is explicitly `(H,T,epsilon)`-relative. Increase horizon in a new packet and report refinement stability; never call bounded equality final identity. |
| Quantization artifact | A result changes when probabilities cross an arbitrary bin edge. | Use interval certification; boundary contact is HOLD; repeat under a predeclared epsilon ladder. |
| Adapter cheat / opaque-state leak | An adapter could encode root IDs or carrier labels in output routing. | Run root/action/outcome relabel controls, trace-schema validation, and independent engine replay. Opaque state IDs are forbidden from signatures. |
| Demand tailoring | A demand can be selected after seeing which carrier loses it. | Seal packet/digest before test runs; any new discriminator starts a subsequent packet with design/holdout separation. |

Consequently, an APQ run can at most produce a packet-relative partition and the existing kernel's packet-relative frontier. It cannot establish that the alphabet is universally neutral, that a carrier has an absolute identity, or that a scientific/canonical rung advanced.

## 9. Minimal implementation sequence (not executed here)

1. Add an immutable `APQPacket` schema and validator: finite alphabets, closure/budget calculation, no native-token vocabulary in the common deck, valid demand endpoints, frozen digests, and numeric contract.
2. Add an `APQCandidatePackage` adapter and a trace writer implementing only `start`/`step`; fail closed on non-finite support, missing outcomes, mass error, or unsupported action.
3. Implement `enumerate_beliefs` and the backward `kappa_t` refinement above. Emit `X` ordering, trace-table digest, partition labels, and a separating action tree for each non-equal pair queried by controls.
4. Compile packet demand records to plain `(x,y)` edges plus retained continuation provenance. Feed only those edges and `pi_C` to the existing ratchet partition kernel.
5. Start with a deliberately small toy deck containing a persistent candidate and an amnesiac candidate. The expected check is not a ranking: the continuation demand must separate the positive control and the static-only ablation must go `HOLD_THIN_ACTION_DECK`.
6. Add one independently replayed adapter each for a classical finite transducer, a density-matrix instrument, and a bracketed exceptional carrier. Require exact packet/action/outcome agreement before any frontier run. Only then run a sealed mixed deck and its holdouts/ablations.

The deliverable of the first implementation is an engineering receipt saying whether this bridge compiles traces to partitions and whether its controls pass. It is not an engine comparison result.

## 10. Integration boundary

`system_v7/constraint_core/ratchet/ratchet_engine.py` remains the only component that computes `L_D`, survivor status, and partition-coarseness frontier. Lev may schedule traces, validators, and receipt capture. LLMs may propose the action deck and demand provenance, but neither determines a partition block nor an MSS winner.

The bridge is therefore:

```text
sealed public action/outcome packet
  -> candidate start/step traces
  -> finite belief histories and bounded predictive quotient pi_C
  -> continuation-derived ordinary demand pairs D
  -> existing L_D / coarsest-survivor frontier code
```

Until that chain is implemented and run with passing controls, this document is fuel only.
