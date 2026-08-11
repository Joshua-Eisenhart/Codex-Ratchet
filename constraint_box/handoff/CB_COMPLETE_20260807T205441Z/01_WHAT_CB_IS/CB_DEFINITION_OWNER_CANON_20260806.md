# WHAT CONSTRAINTBOX IS — the definition, owner canon (2026-08-06)

**Provenance: owner-minted.** This supersedes every model-authored
description of CB in this repository, including mine.

## The one-line definition

> CB is a **deterministic gating LLM constraint harness for mass
> looping swarms, of diverse LLMs, where the LLMs don't control their
> own gating.**

Every clause carries weight:

| Clause | Meaning |
|---|---|
| **deterministic gating** | the gate is code, not judgment; replayable without a model |
| **constraint harness** | it constrains the option set and the format; it does not decide truth |
| **mass looping swarms** | the subject is many agents over many waves, not one careful thread |
| **diverse LLMs** | heterogeneity is structural — diverse MMMs, real prompt diversity |
| **LLMs don't control their own gating** | the decisive separation; a producer never sets its own ceiling |

## Why LevOS is insufficient, and where CB fits

> LevOS fails because **LLMs control the gates in it.** It tries to be
> a constraint harness, and has LLMs deciding all deep down. **CB is
> essential for LevOS processes.**

LevOS has the right ambition and the wrong authority structure. Its own
upstream contract already gropes toward the fix — provider evidence may
not carry verdict bits, only core/eval emits verdicts — but the
deciding remains model-side in practice. CB supplies the missing half:
a gate that is code all the way down, which LevOS-style processes can
call but cannot argue with.

## Why the Python tooling matters *more* under this definition

> this is why python tooling and libraries are extra needed. more well
> made pre existing deterministic tools that can do a lot of what is
> needed. and not just that narrow base set. but a lot of the ones we
> laid out recently.

If the gate must be deterministic, every gate obligation must resolve
to a *tool*, not to an opinion. Mature libraries already implement most
of what the gates need, and each one that lands is one fewer place
where a model gets to decide. Mapping from the measured trials:

| Gate obligation | Deterministic tool |
|---|---|
| bounded satisfiability, erased controls | z3, cvc5 (+ enumeration as third decider) |
| exact symbolic recompute | sympy |
| DAG/order/reachability/cycle verdicts | rustworkx |
| rewriting-logic state transitions | maude |
| receipt contract enforcement | msgspec (strict decode, typed errors) — trialled 0.06 ms, refuses unknown field / wrong type / missing field |
| admissible range membership, unfalsifiable-box detection | portion — trialled; refused D < 0 and CPTP modulus > 1 as *not possible answers* |
| lease/tree custody without subprocess | pygit2 — trialled, identical tree id, 65x faster |
| exact receipt lookup, context-rot reduction | stdlib sqlite3 — measured 54,055x fewer tokens on a bounded question |
| canonical bytes before hashing | rfc8785 (JCS) |
| adversarial input generation | hypothesis |
| import-boundary / architecture invariants | import-linter, stdlib ast |
| input-diversity measurement | stdlib hashing + shingles (`input_diversity_gate.py`) |
| pinned environment resolution | uv, lock files |
| attestation / external authority seam | cryptography, in-toto |

**The base set is not enough.** Five core tools cover deciding and
rewriting; the gates also need format, range, custody, canonicalization,
graph, and diversity — and those are exactly the secondary tier already
measured for maintenance, wheel purity, and install cost.

## Waves as a loop-management system

> the waves are also a **loop management system for mass agent swarms**,
> where there is actually more structure and formalized divergence and
> convergence in the swarm, with diverse mmms and real prompt diversity
> and more real gating.

So a wave is not only a barrier. It is the unit of loop control over a
swarm: different waves handle different things, and they loop on each
other. Divergence and convergence are formalized per wave rather than
left to a single model's discretion.

Three practical consequences, stated by the owner:

1. **It does not need the smartest agents.** The structure carries the
   work. The measured ladder already shows Haiku scouts at 8x8 and
   8x12 completing cleanly; Opus is reserved for rare arbitration.
   Intelligence per node is not the scaling variable — diversity,
   nesting, and gating are.
2. **Members need not be LLMs.** Sim engines and Python library tools
   can sit as members. A council containing a z3 call, a rustworkx
   check, and a sympy recompute alongside three voices is still a
   council — and its deterministic members cannot drift.
3. **Full max councils do not run for everything.** Scale the shape to
   the task; the honesty ladder (`SMOKE_FORMAT`, `SMOKE_TOPOLOGY`,
   `REAL_ATTEMPT_PARTIAL`, `REAL_ATTEMPT_FULL`) is what keeps a small
   run from being reported as a full one.

**Open, and named as open:** good wave-structure design has not been
worked out. Which wave handles what, how they loop on each other, and
what the standard shapes are — that is unfinished design work, not a
solved thing to be documented.

## The through-line from the CR problem

The original failure: deterministic gates existed by v3, and there was
**no exploration at the gates** — models absorbed the gate ontology and
went hyper-conservative, so orders had to be driven by hand.

The resolution is now structural rather than exhortative:

```
mass swarm of diverse LLMs        <- exploration cannot collapse:
  diverse MMMs, dissimilar roots     nodes do not share a basin
      |
  nested councils, waves           <- divergence and convergence are
  looping on each other               stages, not hopes
      |
  CB deterministic gates           <- gating is code; the swarm never
  running ON the swarm                sets its own ceiling
```

CB gates run **on mass swarms**, not on one hyper-controlled model.
That is the difference between a harness that constrains exploration
and one that enables it.
