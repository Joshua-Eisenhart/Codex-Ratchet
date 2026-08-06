# Architecture and boundaries

## One system, three views

| Area | Input | Operation | Output | Authority ceiling |
|---|---|---|---|---|
| ConstraintBox control plane | untrusted proposal or claim | strict intake, policy selection, bounded checks, branch accounting | bounded decision record | may route, park, block, or mark eligible for further checks |
| Simulation estate | declared capability manifest, fixture, selected interpreter | boot, execute, mutate, replay, sever dependency, compare lock | capability and tier receipt | may report that a named tool performed one bounded fixture |
| Codex-Ratchet consumer | typed finite candidate, demands, maps, probes | manifold-specific measurement and relative ratchet comparison | plural survivors, failures, unresolved branches | may compare declared candidates under declared demands |

The same finite object can be viewed through all three areas, but the software
roles are not collapsed. A scientific candidate cannot select its own control
profile. A simulation runtime cannot promote its own receipt. ConstraintBox
cannot turn eligibility into scientific truth.

## Data flow

```text
LLM or human proposes a bounded object
              |
              v
strict byte intake -> semantic typing -> controller-owned applicability
              |                         |
              |                         v
              |                selected bounded instruments
              |                (stdlib / NumPy / SMT / JAX / ...)
              |                         |
              v                         v
      immutable input          independent observations
              \                         /
               \                       /
                -> controller settlement
                  ELIGIBLE / PARKED / BLOCKED / HOLD
                              |
                              v
                  CR adapter or Lev event adapter
```

## The shared formal object

The minimal implemented carrier is a finite set of complete histories
\(\mathcal H\), not a story about a privileged trajectory. A projection
\(p:\mathcal H\to X\) creates fibres

\[
\mathcal F_x=p^{-1}(x),
\qquad
\kappa(x)=\log_2 |\mathcal F_x|.
\]

If amplitudes \(a_j\) are supplied, the history-pair field is

\[
D_{jk}=a_j\overline{a_k}.
\]

The diagonal \(D_{jj}\) retains history weights; \(D_{jk}\) for \(j\ne k\)
retains relations that a plain set of alternatives would erase. ConstraintBox
implements both the finite ensemble and the history-pair field. It does not
assert that this carrier is a complete physical ontology.

Candidate observation maps induce partitions. Given a demand edge set
\(E_D\), the collapsed-demand loss is

\[
L_D(\pi)=
\{(u,v)\in E_D:\pi(u)=\pi(v)\}.
\]

A candidate survives the finite demand packet when \(L_D(\pi)=\varnothing\).
Only candidates with a declared nesting witness and common probe contract are
compared by refinement. Incomparable survivors remain plural.

## Rules that bind the implementation

1. Requests cannot select the profile, tolerance, exemption, solver status, or
   verdict.
2. Missing evidence parks or blocks; it never silently passes.
3. A tool is `READY` only after a bounded positive witness and the controls
   required by its profile.
4. Optional tools can leave a tier `DEGRADED`; required tools must be `READY`
   before a major run.
5. Candidate branches are retained until a declared discriminator earns a
   prune or merge.
6. MSS language is relative to the declared candidate set, demand packet,
   probes, and partial order.
7. Heterogeneous metrics remain typed values or a partial order; they are not
   added into an unnamed scalar.
8. All downstream physical interpretation is a proposal carried outside the
   generic controller kernel.

## Why downstream CR work improves the foundation

The manifold proposal asks more of the control plane than ordinary receipt
linting. It requires typed objects, restriction maps, finite carrier bounds,
multiple metrics, conditional branches, cross-layer compatibility, and honest
claim ceilings. Those requirements generalize:

- API migrations require explicit old/new maps.
- compiler claims require an input language, output language, and semantics.
- benchmark claims require typed metrics and a declared comparison set.
- agent workflows require retained alternatives and controller-owned pruning.
- scientific claims require evidence obligations selected outside the
  producer.

The CR model therefore acts as a difficult fixture suite. Its ontology is not
installed as the ontology of ConstraintBox.
