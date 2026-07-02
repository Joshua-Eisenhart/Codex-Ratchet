# Cross-Lane Sim Independence Reset - 2026-05-23

Status: recovery protocol
Scope: `system_v5/ops/formal_scouts`, `system_v5/grok_sim`, external audit docs,
and generated result/index surfaces touched by the 2026-05-23 mixed Grok/Claude
and formal-scout wave.

## Decision

The contaminated wave is not an evidence bridge.

Formal and informal sims must be rerun independently. Neither lane may use the
other lane's results, result JSONs, generated indexes, synthesis docs, or
conclusions as evidence of anything.

They may share:

- source docs;
- repo contracts;
- mathematical specifications;
- named target questions;
- failure patterns;
- proposal prompts;
- hand-written implementation ideas that are not result claims.

They may not share as evidence:

- pass/fail outcomes;
- result JSONs;
- readiness or integration indexes;
- classifier summaries;
- synthesis docs;
- claims that a target survived, failed, killed, admitted, or converged;
- route-truth statements from the other lane.

## Lane Roles

### Formal lane

Location: `system_v5/ops/formal_scouts/`

Formal reruns must be built from source docs, repo contracts, and local formal
scout code only. `grok_sim` may suggest a target, but the formal scout must
compute its own observables, controls, validator pass, and result receipt.

Formal receipts may be used for formal-scout readiness only after they are
produced inside the formal lane and pass the formal sim contract.

### Informal lane

Location: `system_v5/grok_sim/`

Informal reruns must be built and executed inside `grok_sim`. Formal-scout
receipts may suggest an attack, failure pattern, or target, but cannot be copied
or cited as informal evidence.

Informal receipts remain proposal/failure-pattern material only unless a later
formal translation rebuilds and reruns them independently.

## Contamination Rule

Any file or result created during the mixed wave is suspect until classified.
Suspect does not mean false. It means not admissible as evidence.

The current suspect surfaces include:

- new untracked formal-scout sim files created during the mixed wave;
- matching generated formal-scout result JSONs;
- tracked formal-scout classifier and README edits made during the same wave;
- generated readiness/integration docs and JSON indexes from the same wave;
- cross-lane synthesis docs that describe agreement or convergence.

## Recovery Steps

1. Freeze the mixed-wave state. Do not stage or commit it as progress.
2. Inventory suspect source files, generated results, docs, and indexes.
3. Decide path by path: quarantine, revert, or rebuild from scratch.
4. Rerun formal targets inside `formal_scouts` with no dependency on informal
   results.
5. Rerun informal targets inside `grok_sim` with no dependency on formal
   results.
6. Compare lanes only after both sides have independent receipts.
7. Label cross-lane agreement as hypothesis support, not proof, unless the
   comparison document demonstrates independent receipt generation.

## Admission Ceiling

Until the reset is complete:

- cross-lane convergence claims are blocked;
- readiness/index updates from the contaminated wave are blocked;
- formal-scout promotion based on informal outputs is blocked;
- informal success based on formal outputs is blocked;
- any salvaged target must be rerun independently before it can support a claim.
