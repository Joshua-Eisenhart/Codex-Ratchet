# THREAD_AND_AUTOMATION_PROCESS_FLOWS__2026_03_11__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL NOTE
Date: 2026-03-11
Role: exact process-flow map for Codex A2 threads, Codex A1 threads, Pro threads, ZIP-bound workers, and later automation

## 1) Purpose

This note answers:
- what thread classes exist
- what boot each class needs
- how they relate
- what order they run in
- how later automation should reduce manual signaling

## 2) Codex A2 controller thread

### Boot
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`

### Role
- whole-system A2 control
- bounded refinery
- queue routing
- execution-state updates
- A1 dispatch readiness

### Inputs
- active owner/control surfaces
- bounded return artifacts
- bounded cleanup/routing notes

### Outputs
- `A2_UPDATE_NOTE`
- routing note
- audit note
- execution-state update
- optional `A1_READY_PACKET`

### Stop rule
- one bounded pass only

## 3) Codex A2 worker thread

### Boot
- same A2 boot

### Role
- one bounded non-overlapping A2 pass

Examples:
- family routing
- queue audit
- cleanup-prep
- delta consolidation
- return capture

### Rule
- worker may not silently become controller

## 4) Codex A1 thread

### Boot
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`

### Start condition
- only from valid queue status
- only from valid handoff

### Valid queue states
- `READY_FROM_NEW_A2_HANDOFF`
- `READY_FROM_EXISTING_FUEL`
- `READY_FROM_A2_PREBUILT_BATCH`

### Valid roles
- `A1_ROSETTA`
- `A1_PROPOSAL`
- `A1_PACKAGING`

### Outputs
- bounded proposal-side result only

### Stop rule
- one bounded pass only

## 5) `a1?` process flow

1. controller checks current A2 fuel and queue status
2. if a valid bounded family slice exists, prefer compiling one queue-status packet through:
   - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`
   - using either `packet` or `bundle` preparation mode
   - if more than one bounded family slice exists, select one explicitly or fail closed
3. otherwise, controller emits one queue-status packet
4. if `NO_WORK`, stop
5. if ready, emit one `A1_READY_PACKET`
6. operator may launch one A1 thread from that packet or prepared bundle
7. A1 returns bounded result
8. controller captures result and resets queue status

## 6) Pro thread classes

### Class P1: narrow source worker
Purpose:
- one source family
- one acquisition packet

Context depth:
- narrow packet only

### Class P2: method comparison worker
Purpose:
- compare method families or thinker clusters

Context depth:
- packet set + selected A2 overlays

### Class P3: lane refinery worker
Purpose:
- one larger external lane
- multiple packet families

Context depth:
- broader boot
- lane-level packet set

### Class P4: full A2-style reasoning space
Purpose:
- exploratory high-context reasoning
- philosophy/retooling/problem-shaping

Context depth:
- large A2 slice
- possibly broad system_v3 context

Trust rule:
- exploratory only
- never direct authority
- must return through audit

## 7) Pro thread process flow

1. choose thread class
2. choose proper boot/context depth
3. issue zip artifact with explicit role
4. run in web UI `Pro`
5. collect return artifact
6. audit in web UI `Thinking / Heavy`
7. only then route safe keepers into A2

## 8) ZIP-bound worker process flow

1. ZIP declares:
- role
- boot surface
- allowed actions
- blocked actions
- required outputs
- stop rule

2. worker runs from ZIP only
3. worker emits bounded result artifact
4. controller audits or ingests
5. no hidden-memory continuation

## 9) Lower-loop process flow

1. A2 prepares bounded fuel
2. A1 emits proposal-side packets
3. A0 compiles
4. B constrains
5. SIM executes evidence pass
6. result flows back upward as evidence/graveyard/update input

## 10) Go-on process flow

### Thread-action `go on`
Definition:
- one next action this thread itself can perform

Rule:
- one bounded pass only

### Workflow next action
Definition:
- an overall project next step that may happen outside this thread

Rule:
- do not confuse it with a thread-action `go on`

## 11) Future automation buildout

### First automation layer
- recurring A2 maintenance
- recurring thread monitoring
- recurring closeout capture

### Second automation layer
- auto-continue rule for safe bounded thread continuation
- A1 queue polling / `a1?` support
- Pro return ingest support

### Third automation layer
- browser automation for launching threads, delivering zips, retrieving returns, and feeding audit steps

Blocked until stability:
- broad autonomous swarms
- auto-scaling without audit

## 12) Immediate next process work

1. keep using booted A2 controller work
2. keep converting external scaffolds into source-bearing packets
3. use A1 only from queue-ready packets
4. build the later automation layer only after these loops prove stable
