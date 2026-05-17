# Attractor-Basin Success Doctrine v0

Status: noncanonical method doctrine / audit criterion.
Date: 2026-05-17

This document formalizes a working success criterion for Codex Ratchet research:

> A result is stronger when independent methods converge toward the same surviving structure, and weaker when multiple lanes merely read the same proxy twice.

This is not a physics claim and not a claim that the engines themselves are always attractor-pull dynamics. It is a criterion for judging research convergence.

## Existing Guardrails

The local reference docs already keep the boundary sharp:

- Attractor basin: asks where trajectories converge.
- Viability kernel: asks where trajectories can remain admissible under constraints.
- Hume/nominalism: only probe-relative regularities are observed; causality and necessity are narrative compression unless earned by probe distinctions.
- Popper pressure: test the weirdest, most falsifiable predictions first; do not optimize for easy green receipts.

References:

- `system_v5/docs/references/ATTRACTOR_BASINS_FORMAL_REFERENCE.md`
- `system_v5/docs/references/VIABILITY_THEORY_REFERENCE.md`
- `system_v5/docs/NOMINALISM_IN_THIS_SYSTEM.md`
- `system_v5/docs/CONSTRAINT_SURFACE_AND_PROCESS.md`

## Core Distinction

### Deep Basin

A convergence is a deep basin when materially different methods, encodings, observables, or substrates independently reach the same survivor/exclusion.

Examples of method diversity:

- numerical simulation plus symbolic derivation;
- two non-isomorphic SMT encodings;
- independent observables with the same verdict;
- source-native engine execution plus a detached control;
- same claim surviving under carrier changes, gauge controls, finite-size controls, and matched nulls.

Deep-basin wording:

- "This structure survived independent methods under named controls."
- "The convergence appears method-multiple, not same-source repeated."
- "The claim ceiling remains bounded to the tested invariant."

### Shallow Basin

A convergence is shallow when several workers, models, or scripts agree because they reused the same proxy, input schedule, implementation assumption, or hidden scaffold.

Common shallow-basin patterns:

- multiple models reading the same cyclic schedule and calling it an invariant;
- a green receipt whose control is the same computation with a label swap;
- Z3 restating numpy predicates instead of adding an independent witness;
- scalar summaries standing in for a candidate bundle;
- path entropy, correlation, KL, or accuracy treated as the invariant before deeper pair tests.

Shallow-basin wording:

- "This is same-source convergence, not independent convergence."
- "The proxy is detected; the intended invariant remains open."
- "The receipt is green but the basin is shallow until a deeper invariant survives."

## Operational Criterion

Every major positive result should be classified on four axes:

| Axis | Question | Strong Answer |
|---|---|---|
| Source independence | Did the methods share the same input/proxy? | No; at least two genuinely different constructions agree. |
| Observable independence | Did the readouts measure the same scalar? | No; distinct observables preserve the verdict. |
| Control pressure | Did matched nulls attack the exact claim? | Yes; nulls include proxy-preserving and deeper-invariant-breaking cases. |
| Claim ceiling | Does the wording stay inside the receipt? | Yes; no physics/Axis0/Holodeck/engine promotion from a scout. |

The success classification is:

- `deep_basin`: method-multiple, proxy-resistant, control-survived.
- `candidate_basin`: promising but missing one independence axis.
- `shallow_basin`: repeated agreement on one proxy/source.
- `anti_basin`: falsifier shows the convergence target was wrong.
- `open_basin_boundary`: controls split or variance remains trajectory-dependent.

## Science-Method Loop

This maps onto the two-loop science method:

- Hume / inductive loop: collect repeated particulars, receipts, controls, and survivor patterns without treating them as necessary laws.
- Popper / deductive loop: throw high-falsifiability models at the survivor pattern and keep the graveyard as first-class output.

The loop is:

1. propose a candidate invariant;
2. build multiple independent probes;
3. run matched nulls that preserve the proxy but break the proposed invariant;
4. classify convergence as deep, candidate, shallow, anti, or open;
5. route failures into graveyard hashes and next falsifiers.

## Required Premortem For Basin Claims

Before calling any result a basin, ask:

1. Are all methods secretly consuming the same schedule, same proxy, same seed, same scalar, or same implementation?
2. Would a proxy-preserving / invariant-breaking pair kill the claim?
3. Would an invariant-preserving / proxy-breaking pair preserve the claim?
4. Does the result survive a carrier, gauge, finite-size, or encoding change appropriate to the claim?
5. Is the strongest negative as carefully implemented as the positive path?
6. Does the receipt distinguish "all_pass" from "deep basin"?
7. Is the claim ceiling narrow enough that a green result cannot become ontology?

## Current Application

Recent repairs illustrate the doctrine:

- `path_entropy` is a shallow-basin risk when multiple lanes read the same cyclic engine schedule.
- Online VMP needed a held-out deterministic observation-token control because a self-predicted argmax loop is not strong evidence of exogenous inference.
- The subdense multicarrier consumer needed full-vector Axis0 candidate controls because scalar means can fake downstream convergence.

The current foundation direction is therefore:

- prefer proxy-pair falsifiers over more agreement votes;
- keep scalar readouts as controls until they survive deeper-invariant tests;
- make every downstream consumer preserve candidate structure before optimizing higher-level Holodeck/Axis0 language.

## Implemented Formalization

The first formal scout for this doctrine exists:

- `system_v5/ops/formal_scouts/sim_attractor_basin_success_criteria_receipt_classifier_probe.py`
- `system_v5/ops/formal_scouts/results/attractor_basin_success_criteria_receipt_classifier_probe_results.json`

It scores selected existing receipts and named negative fixtures on the basin doctrine:

- input: receipt paths and named claim;
- output: `deep_basin`, `candidate_basin`, `shallow_basin`, `anti_basin`, or `open_basin_boundary`;
- required fields: method families, shared-source risk, proxy-preserving control, invariant-preserving control, claim ceiling;
- graveyard: green receipt with shallow convergence must fail deep-basin admission.

Initial validated label spread:

- `deep_basin`: one receipt-local encoded exclusion (`commutative_geometry_collapse`), not architecture promotion.
- `candidate_basin`: three bounded receipts with useful but incomplete independence/control coverage.
- `shallow_basin`: two same-source/proxy fixtures, including one adversarial false-independence fixture.
- `anti_basin`: four receipt-backed falsifications/demotions.
- `open_basin_boundary`: one incomplete-control fixture.

This scout does not promote any existing receipt. Its job is to prevent same-source agreement from being mistaken for a real attractor basin and to keep `all_pass=true` separate from `deep_basin`.
