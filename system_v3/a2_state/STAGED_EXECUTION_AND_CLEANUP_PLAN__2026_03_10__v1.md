# STAGED_EXECUTION_AND_CLEANUP_PLAN__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: explicit staged plan for finishing A2 refinement, stabilizing controller rebootability, reducing system bloat safely, and restoring real ratchet execution

## 1) Immediate priority order

1. stabilize recurring A2 brain refresh
2. finish bounded A2 refinery on the highest-value unresolved lanes
3. get thread automation and closeout capture working in real use
4. bring run-folder / artifact-bloat under control with high caution
5. improve whole-system A2 surface understanding and file-role mapping
6. restart regular A1-from-A2 operation
7. push real bounded batches to the ratchet
8. form an actual attractor basin through repeated monitored loops
9. only then judge whether the QIT-engine lane is valid by evidence

## 2) What should run regularly now

### A2 maintenance threads
- `a2-brain-refresh`
- `thread-run-monitor`
- `thread-closeout-auditor`
- `closeout-result-ingest`
- `brain-delta-consolidation`

### External refinery threads
- bounded Pro/deep-research external packs
- return audit before A2 ingestion

### Internal bounded revisit threads
- selected sibling-pair revisits
- selected A2-mid residual families
- queue / duplicate / stale-surface audits

## 3) Immediate thread classes to run next

### Class A: A2 continuity / rebootability
Purpose:
- keep controller state repo-held
- reduce dependence on one live thread

Run:
- recurring `A2 brain refresh`
- recurring `brain delta consolidation`
- recurring `thread closeout capture`

Expected outputs:
- bounded `A2_UPDATE_NOTE`
- bounded `A2_TO_A1_IMPACT_NOTE`
- admitted small deltas
- captured closeout packets

### Class B: system-shape and cleanup-under-caution
Purpose:
- understand the whole system shape
- identify useless/redundant/outdated surfaces
- do not delete recklessly

Run:
- file-role mapping pass
- active-owner vs derived vs archive classification pass
- run-folder / bloat audit pass
- duplicate/doc-drift audit pass

Expected outputs:
- one owner map
- one bloat map
- one caution-classified cleanup candidate list:
  - keep
  - archive
  - quarantine
  - investigate

Hard rule:
- no deletion based only on annoyance or age
- classify before mutating

### Class C: finish A2 refinery where it matters most
Purpose:
- complete enough A2 reduction that the system can run from A2 cleanly

Run first:
- external entropy / Carnot / Szilard lane
- selected unresolved `core_docs` / older `A2_LAYER1_5` residues that still matter to active system operation
- high-value `system_v3` residual lanes that affect process law, sim law, or file-role clarity

Expected outputs:
- bounded A2-mid/controller packets
- admitted A2 deltas
- clearer `usable now / usable after retool / reject` splits

### Class D: restart real A1 operation
Purpose:
- restore A1 as a live proposal engine rather than a mostly remembered contract

Run:
- `a1-from-a2-distillation`
- A1 family-role refresh
- admissibility-hint refresh
- proposal pack generation only from refreshed A2

Expected outputs:
- live proposal families
- explicit negative branches
- rescue branches
- better executable-head vs passenger placement

### Class E: real ratchet / attractor formation
Purpose:
- stop endless prep
- get repeated monitored loops running

Run:
- small real batches through the full path
- monitor outcomes
- preserve graveyard and rescue structure
- repeat with bounded corrections

Desired signal:
- repeated useful movement through the same disciplined path
- less controller repair per cycle
- more reusable deltas per cycle

## 4) The right cleanup doctrine

Use this rule:
- understand first
- classify second
- archive or quarantine before delete when possible
- mutate only with a stated reason

Surface classes:
- active owner
- derived helper
- runtime evidence
- proposal only
- archive only
- unclear / investigate

Delete only when at least one is true:
- exact duplicate with stronger retained owner
- stale generated helper reproducible from active owner
- transient run spillover with no retained evidence role
- clearly broken obsolete scaffolding already replaced

Do not delete just because:
- it is old
- it is verbose
- it is annoying
- it looks redundant without lineage check

## 5) What Pro threads are for

Use Pro/deep-research threads for:
- high-entropy external research
- broad philosophical / mathematical source mining
- large cartridge generation
- source-linked comparative research packs

Do not use Pro as authority.
Use it as cartridge/refinery production.

Required pattern:
1. bounded boot pack
2. bounded output contract
3. instant audit
4. only then A2 reduction

## 6) Concrete near-term execution sequence

### Step 1
Run the prepared external entropy / Carnot / Szilard lane.

### Step 2
Run recurring A2 refresh / delta consolidation to make controller reboot easy.

### Step 3
Run one bounded system-shape audit:
- file-role map
- run-folder bloat map
- cleanup candidates under caution

### Step 4
Run one bounded A2 residual-refinery batch for the most important unresolved active lane.

### Step 5
Run one bounded A1-from-A2 restart cycle and emit a live proposal family.

### Step 6
Push one real bounded batch down the ratchet and preserve the result.

### Step 7
Repeat the monitored loop until repeated movement appears.

## 7) What “proper attractor basin” means here

Signs of a real attractor basin:
- A2 updates happen regularly and repo-held
- controller reboot is easy
- fewer stale-owner / stale-thread failures
- A1 emits cleaner live families
- real batches move through the ratchet repeatedly
- graveyard / rescue structure accumulates usefully
- external research returns are actually being converted into bounded A2/A1 deltas
- the system starts needing less emergency repair

## 8) QIT engine lane rule

Do not force the QIT-engine lane by desire.

Treat it like any other serious lane:
- bounded proposal
- admissibility
- evidence burden
- negative pressure
- repeated monitored execution

If valid, it should survive through this process.
If weak, the graveyard should expose that.

## 9) Operator instruction

For now:
- automate A2 maintenance
- automate external refinery launch/audit
- automate closeout/ingest
- keep cleanup cautious
- run more A2 threads only when they are bounded and attached to this staged order

Do not reopen broad freeform exploration as the default mode.
