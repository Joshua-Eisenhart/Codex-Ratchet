# Anomalous Computer-Science Translation

## Status

- Date: 2026-04-11
- Role: repo-facing translation layer
- Purpose: restate the system in explicit computer-science terms so the wiki and LLM workers can reason about it without flattening it into vague theory prose

## Why This Exists

Much of the repo uses local project language such as lego, shell, bridge, carrier, and queue.
That language is useful internally, but LLMs often perform better when the same system is also described as:

- a state machine
- a compiler pipeline
- a harness for bounded workers
- an evidence-backed registry system

This document is that translation layer.
It does not replace the repo ontology.
It makes the repo ontology easier for machines and future docs to use correctly.

## One-Sentence Translation

Codex Ratchet is an LLM-guided research compiler and verification harness that turns high-entropy source material into explicit testable objects, runs bounded local executables against them, records evidence, and updates persistent state only when the evidence changes what is honestly claimable.

## System Translation Table

| Repo term | Computer-science translation | Practical meaning |
|---|---|---|
| lego | primitive typed unit | smallest local object worth building or testing |
| candidate | provisional object | proposed unit not yet promoted by evidence |
| probe / sim | executable verification function | bounded run that tests one object or relation |
| result artifact | machine output record | JSON/log/audit emitted by execution |
| registry / ledger row | materialized state view | persistent projection of current object status |
| queue item | scheduled transition request | next allowed move with prerequisites and outputs |
| truth label | verification state | explicit claim level such as `exists`, `runs`, `passes local rerun`, `canonical by process` |
| maintenance surface | derived cache / projection | docs that must be updated after evidence changes |
| shell-local | single-node or single-module scope | object tested in isolation |
| pairwise / coexistence | interaction-level test | compatibility or coupling between already-real local objects |
| bridge claim | high-level integration claim | cross-object or cross-layer assertion that must come late |

## The System As A Pipeline

The repo can be described as a seven-stage pipeline:

1. source ingestion
2. object normalization
3. dependency resolution
4. bounded execution
5. evidence capture
6. state classification
7. projection and maintenance update

In CS terms, this is closer to a compiler plus test harness plus registry updater than to a notebook or wiki.

## The System As A State Machine

The core object lifecycle is:

`source fragment -> normalized object -> queued target -> executed probe -> evidence-backed status -> registry update -> possible successor`

Allowed transitions are narrow.
The controller should reject invalid transitions such as:

- prose claim without execution evidence
- bridge promotion before local-object validation
- status inflation from `exists` to `passes local rerun`
- queue motion without a named artifact path

## The System As An LLM Harness

For LLM purposes, the repo is not mainly a theory store.
It is a harness with the following parts:

- inputs: docs, legacy notes, ledgers, current result files
- controller: chooses one bounded object transition
- workers: Codex or other agents performing a narrow task
- validators: enforcement scripts, reruns, audits, tests
- artifacts: result JSONs, updated registries, patched docs
- closeout: claim classification plus maintenance updates

An LLM works well here only if it behaves like an orchestrator inside a constrained execution environment.
It works badly if it behaves like a freeform summarizer.

## What The Wiki Should Understand

The wiki should stop acting like a passive summary layer and instead model the repo as:

- a live object registry
- a queue-aware execution map
- a glossary with bidirectional translation
- a maintenance projection of current evidence

That means wiki pages should prefer:

- object definitions
- dependency chains
- result paths
- status labels
- next allowed transitions

over broad narrative explanation.

## Translation Rules For Wiki Pages

When writing or updating a wiki page, translate local terms into explicit CS concepts wherever useful:

- "lego" -> primitive object, bounded unit, local executable target
- "build order" -> dependency order, topological order, promotion order
- "truth audit" -> consistency check between claims and artifacts
- "maintenance surface" -> derived state view that must stay synchronized
- "controller" -> scheduler plus state-transition manager
- "bridge" -> higher-order integration layer

Do not erase the repo's own vocabulary.
Instead, pair project-native terms with a machine-readable explanation.

## Global Goal Translation

In computer-science terms, the global goal is:

Build a reliable research operating loop where LLMs can ingest noisy source material, extract typed bounded objects, execute narrow verification tasks, preserve claim/evidence separation, and iteratively improve the system state without hallucinating progress.

That is the harness objective.
The theory program matters, but the harness has to make theory processing operationally safe.

## Success Criteria

The translation is working if it causes future docs and wiki pages to do more of the following:

- name concrete objects instead of broad themes
- cite result paths instead of vague claims
- separate data, execution, and projection layers
- describe status as a finite state, not a vibe
- describe next work as a scheduled transition, not "understanding more"
- explain the repo as a harness for bounded LLM work

## Recommended Follow-On Pages

The wiki should eventually maintain companion pages for:

- system glossary: repo term <-> CS term
- object lifecycle and allowed transitions
- controller/runtime architecture
- evidence model and truth-label semantics
- maintenance surfaces and projection rules

## Bottom Line

The anomalous part of this system is not that it has unusual theory language.
The anomalous part is that it is trying to turn unstable research prose into a controlled execution graph.

The correct computer-science translation is:

Codex Ratchet is a bounded research-object compiler and verification harness with strict state transitions, explicit evidence semantics, and synchronized derived views.
