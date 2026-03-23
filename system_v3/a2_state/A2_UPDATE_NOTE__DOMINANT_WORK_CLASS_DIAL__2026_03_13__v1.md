# A2_UPDATE_NOTE__DOMINANT_WORK_CLASS_DIAL__2026_03_13__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-13
Role: bounded A2 refresh choosing one dominant upper-loop support-program dial
Surface class: DERIVED_A2

## Scope

This pass does one bounded design task:
- choose one dominant dial for upper-loop support work
- reduce policy-sprawl pressure across packet prep, audit, and controller summaries

This pass does not:
- alter lower-loop runtime behavior
- open fresh A1 work
- promote support-side tuning into earned state

## Choice

Current best working choice:
- one dominant `work_class` dial

Allowed values:
- `LIGHT`
- `STANDARD`
- `DEEP`

## Why this dial

This is the cleanest current choice because it can govern multiple support-side behaviors at once:
- packet scope
- audit depth
- continuation budget
- expected output breadth

That is leaner than maintaining separate loosely-coupled knobs for:
- packet scope
- audit depth
- lane budget
- reasoning profile
- continuation count

## Working interpretation

### `LIGHT`
- smallest bounded source set
- smallest expected output set
- fast audit only unless drift is obvious
- minimal continuation budget

### `STANDARD`
- normal bounded source set
- normal output set
- `Instant` audit plus `Thinking` audit when needed
- moderate continuation budget

### `DEEP`
- wider but still bounded source set
- fuller output set
- dual-audit expected by default
- highest continuation budget still allowed under bounded-thread rules

## Boundary

`work_class` is a support-side controller dial.

It should not:
- replace source authority
- replace admission judgment
- replace lower-loop evidence
- become a hidden ontology dial
