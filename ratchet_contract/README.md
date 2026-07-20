# Ratchet execution contract v0

This is fuel-adjacent infrastructure, not the ratchet itself. It defines a
code-level interface (`contract.py`) and deterministic gate/MSS operators
(`gates.py`, `mss.py`) so executable candidates can be compared with zero LLM
judgment. Style matches `fuel_gate/fuel_adequacy_gate.py`: every check is
code, every verdict carries a reasons dict, nothing is decided from prose.

## The boundary

LLMs and councils produce and vet fuel: candidates, demand sets, weakness
proposals. LLMs never compute relative MSS, presumption, or any tooth. That
is the ratchet's job, and the ratchet is code. See
`system_v8/candidates/RANKING_VOID_llm_did_ratchets_job.md` for the incident
that makes this binding, and `ROOT/HOW_THE_ENGINES_RUN_THE_RATCHET.md` for
the process this contract implements. No function in this directory ranks by
prose, model brand, or machinery count.

## The contract (`contract.py`)

`CandidatePackage` is an abstract base class. A candidate must supply:

- `carrier` — finite state representation plus allowed ops.
- `states()`, `probes()` — finite populations.
- `apply(op, state)` — the one application primitive. Argument order is
  fixed (op, then state); composition through `apply_sequence` never
  assumes associativity — "left" and "right" bracketing are computed
  separately and are allowed to disagree.
- `reidentify(record, current_state)` — the central function. Every gate
  and the MSS operator use it to induce the candidate's partition of a
  shared observation surface `X`: two elements land in the same block iff
  `reidentify` says so both ways. This is the candidate's presentation as a
  probe-relative quotient.
- `persist(state, ...)` — returns the state after a declared continuation
  (perturbation, delay, partial access, relabeling). It returns a state,
  not a self-reported viability flag: gates.py decides viability by
  re-running the partition kernel on what comes back, never by trusting the
  candidate's own claim.
- `evolve(new_constraint)` — returns an extended candidate or `None`.
- `nest_interface()` — inner/outer/neighbour connection, optionally
  carrying a self-claimed `recompute_digest` that `extension_gate` checks
  against a fresh recompute.
- `declared_primitives()` — explicit list drawn from `identity, equality,
  time, metric, probability, frame`.
- `controls()` — positive and negative control pairs.

`EngineAdapter` (plus `JuliaEngineAdapter`, `JaxEngineAdapter`,
`PyTorchEngineAdapter`) is the same idea for engines: every method raises
`NotImplementedError` with a docstring describing the contract a real engine
will have to satisfy. Wiring them up is a later increment; see "State"
below.

## The six gates (`gates.py`)

Every gate returns `PASS`, `FAIL`, `HOLD`, or `UNRESOLVED` plus a reasons
dict. `HOLD` means the evidence needed to decide is missing or thin — it is
never a tie and never silently upgraded to pass.

| Gate | What it checks |
|---|---|
| `buildability_gate` | Does the candidate instantiate and run its own probes on its own states without error? |
| `probe_validity_gate` | Does the supplied demand family `D` separate the candidate's declared positive controls? Too thin → `HOLD "probe family has not demonstrated discrimination power"`, never a tie. |
| `IDENTITY_GATE` | The nominalist core. See below. |
| `persistence_gate` | Demand generator: pushes `D` through `persist()` and checks survivorship with the same partition kernel. |
| `evolvability_gate` | Demand generator: pushes `D` through `evolve()` and checks survivorship, plus a no-new-primitive check. |
| `extension_gate` | Demand generator (whole-nest): does a declared `recompute_digest` match a fresh recompute of the induced partition? |
| `adequacy` | Combines all six: `Distinguish` (identity) `AND Persist AND Evolve AND Compose` (buildability) `AND Extend AND PassControls` (probe validity). |

### IDENTITY_GATE — the executable form of a=a iff a~b

`IDENTITY_GATE` computes two partitions of the same observation surface `X`
and compares them:

- `pi_probes` — group states by raw probe-fingerprint equality (what the
  probe family can actually see).
- `pi_reidentify` — the candidate's own induced partition, from
  `reidentify`.

If they match exactly, identity is earned: `PASS`. If `reidentify` is a
strict refinement of `pi_probes` — it splits states no probe separates, or
the candidate declares `identity`/`equality` as an installed primitive —
that is unearned identity: `FAIL`. If `reidentify` is strictly coarser than
what the probes support, that is under-discrimination relative to the
evidence: `HOLD`, "new probe required."

`IDENTITY_GATE` gates eligibility. A candidate that fails it has a partition
that cannot be trusted, so it is excluded from every coarseness comparison
in `mss.py` — it does not get scored down, it does not compete.

## MSS is partition coarseness (`mss.py`)

MSS is not a weighted score over identity burden, persistence, and
evolvability. It is one judge: partition coarseness on a probe-honest,
demand-thickened partition, mirroring
`system_v7/constraint_core/ratchet/ratchet_engine.py`'s `_partition_coarser`
and `compute_frontier_cache` directly (this file ports
`_normalise_partition` and `_partition_coarser` byte-for-byte onto
`CandidatePackage.reidentify`). Persistence, evolvability, and whole-nest
recompute are demand generators, not separate scores: each one enlarges the
demand family `D` that the same kernel evaluates, by pushing `D`'s pairs
through a continuation (`persist`, `evolve`, or nest recompute) and checking
whether they still come out distinguished.

`pairwise_mss(A, B, X, D, ...)` runs three stages, in order:

1. **Eligibility.** `IDENTITY_GATE(A)` and `IDENTITY_GATE(B)` must both
   `PASS`. Otherwise `HOLD` — an unhonest partition cannot be compared.
2. **Demand-thickened survivorship**, opt-in per call
   (`thicken_persistence`, `thicken_evolvability`, `thicken_wholenest`).
   Each requested layer must `PASS` for both candidates or the pair is
   `HOLD`, naming exactly which layer and which candidate failed.
3. **Coarseness**, only reached once both candidates clear stages 1–2.
   Compare the two induced partitions over the base surface with
   `partition_coarser`. `A_WEAKER` or `B_WEAKER` when one is a strict
   coarsening of the other; `INCOMPARABLE` otherwise (including when the
   two partitions are identical — a signal for re-merge, not a decision).

`frontier(candidates, X, D, ...)` classifies a whole pool: candidates that
fail eligibility or a requested demand layer go to **purgatory** with the
exact failure and a re-entry condition; survivors are grouped into
**branches** by identical induced partition (two branches that induce the
same partition re-merge into one); the **antichain** is the branches with
no strictly-coarser surviving branch dominating them. It never returns a
single winner.

## Self-check result

`python3 run_contract_selfcheck.py` instantiates four toy candidates, each
built to isolate exactly one gate's failure, and writes the full
discrimination matrix, every pairwise comparison, and both frontiers to
`results/selfcheck.json`. Current result (all four gates plus `adequacy`
show at least two distinct verdicts across the toy set — none is
vacuous):

| Gate | toy_raw_label | toy_quotient_respecting | toy_frozen | toy_amnesiac |
|---|---|---|---|---|
| `buildability_gate` | PASS | PASS | PASS | PASS |
| `probe_validity_gate` (own D / thin D) | PASS / HOLD | PASS / HOLD | PASS / HOLD | PASS / HOLD |
| `IDENTITY_GATE` | **FAIL** | PASS | PASS | PASS |
| `persistence_gate` | PASS | PASS | PASS | **FAIL** |
| `evolvability_gate` | PASS | PASS | **FAIL** | PASS |
| `extension_gate` | HOLD | PASS | **FAIL** | HOLD |
| `adequacy` | FAIL | **PASS** | FAIL | FAIL |

`buildability_gate`'s `FAIL` branch is demonstrated separately, through a
small non-roster fixture whose `apply()` always raises — the four roster
toys are all well-formed on purpose, so breaking buildability on one of them
would have blurred the clean single-axis isolation the other three gates
rely on.

Headline `pairwise_mss` result, base demand only (no thickening):
`pairwise_mss(toy_frozen, toy_quotient_respecting)` → **`A_WEAKER`**.
`toy_frozen` distinguishes states only by a coarser category (warm/cool)
where `toy_quotient_respecting` distinguishes by exact value; both still
separate everything the (deliberately thin) base demand set actually asks
for, so `toy_frozen`'s partition is a strict coarsening — more MSS, on the
base comparison alone. Once `evolvability` and `whole-nest` are added as
required demands, the same pair returns `HOLD`: `toy_frozen` cannot evolve
and its nest claim is stale, so it drops out of eligibility for the
thickened comparison entirely. `toy_quotient_respecting` and `toy_amnesiac`
induce byte-identical partitions on the base surface — `INCOMPARABLE`, and
in `frontier()` they re-merge into one branch. The full base frontier keeps
only `toy_frozen` on the antichain (it dominates the re-merged branch); the
fully demand-thickened frontier keeps only `toy_quotient_respecting` (the
other three fall to purgatory, each for its own named reason).

## State

v0 ships: the typed contract, all six gates fully coded (not stubs), the
partition kernel, the MSS operator as pure coarseness, and a self-check that
proves every gate discriminates on toy candidates built for that purpose.

Not yet built, and explicitly deferred: `JuliaEngineAdapter`,
`JaxEngineAdapter`, and `PyTorchEngineAdapter` are interface-only stubs —
compiling a real candidate's states/probes/apply onto Julia canon, a JAX
batched sweep, or a PyTorch learned component is the next increment.
Compiling any real (non-toy) candidate from `system_v8/candidates/` into
this contract is also deferred; nothing here has been run on a real
candidate.

`promotion_allowed: false`. This is infrastructure, self-tested on toy
candidates built to exercise it — not a ratchet result on any real
candidate.
