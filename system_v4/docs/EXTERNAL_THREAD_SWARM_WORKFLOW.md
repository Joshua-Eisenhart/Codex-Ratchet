# External Thread Swarm Workflow

**Date:** 2026-03-29  
**Purpose:** Controller-safe workflow for running many fresh external model threads from repo-held boot packets, saving returns into the repo, and then ingesting or archiving them cleanly.  
**Scope:** Gemini High, Gemini Low, Opus, Sonnet, or any other external assistant thread that can read a file path and write a return packet.

---

## 1. Core Pattern

Use this thread as the controller.

External threads should:

1. read one boot packet
2. do one bounded task
3. write one return packet
4. stop

They should not act like long-lived authorities.

---

## 2. Repo Layout

Use these folders:

- `system_v4/controller_boot/`
  - controller-authored boot packets for fresh external worker threads
- `system_v4/controller_boot/templates/`
  - reusable boot and return templates
- `system_v4/thread_returns/`
  - raw worker return packets
- `system_v4/thread_archive/raw_returns/`
  - archived raw worker outputs after ingest or rejection

---

## 3. Thread Contract

Every external worker thread gets:

1. one boot file path
2. one exact output file path
3. one short launch prompt
4. explicit stop rules

Keep the chat prompt tiny. Put the real instructions in the boot file.

Shortest safe launch pattern:

```text
Read:
/absolute/path/to/BOOT_PACKET.md

Do only what that packet says.
Write your full result to:
/absolute/path/to/RETURN_PACKET.md

Do not use thread memory over repo files.
Do not promote staging to canon.
Do not change doctrine ranking.
If blocked, write a blocked report to the same return packet.
```

---

## 4. What External Threads May Do

Safe external lane classes:

- bounded audit
- contradiction-finding
- registry or naming check
- supersede or cleanup recommendation
- review-only derivation draft
- review-only export-shape draft
- sim-design proposal
- return normalization or comparison

Unsafe external lane classes unless explicitly controller-owned:

- final doctrine ranking
- bridge/cut closure
- canon or permit decisions
- silent owner-stack rewrites
- global synthesis from memory instead of repo packets

---

## 5. Required Boot Packet Fields

Every boot packet should contain:

- lane id
- purpose
- authority and scope
- allowed files
- forbidden files
- exact deliverable path
- output schema
- stop rules
- anti-smoothing rules

Use the template in:

- [EXTERNAL_THREAD_BOOT_TEMPLATE.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/controller_boot/templates/EXTERNAL_THREAD_BOOT_TEMPLATE.md)

---

## 6. Required Return Packet Fields

Every return packet should contain:

- source model / lane
- task status: `completed`, `partial`, `blocked`, or `aborted`
- files read
- files written
- findings or deliverable summary
- unresolved risks
- controller recommendation

Use the template in:

- [EXTERNAL_THREAD_RETURN_TEMPLATE.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/controller_boot/templates/EXTERNAL_THREAD_RETURN_TEMPLATE.md)

---

## 7. Controller Loop

The controller loop is:

1. write boot packets
2. launch fresh external threads
3. collect return packets in `system_v4/thread_returns/`
4. audit the returns in this controller thread
5. ingest accepted parts into owner surfaces
6. mark returns as accepted, partial, rejected, or archived
7. move stale raw returns to `system_v4/thread_archive/raw_returns/`

Do not let raw return packets silently become authority.

---

## 8. Suggested Naming

Boot packet:

```text
system_v4/controller_boot/BOOT__<LANE>__<YYYY_MM_DD>__v1.md
```

Return packet:

```text
system_v4/thread_returns/RETURN__<MODEL>__<LANE>__<YYYY_MM_DD>__v1.md
```

Archive destination:

```text
system_v4/thread_archive/raw_returns/
```

---

## 9. Model Routing

Recommended use:

- Gemini High
  - heavier audits
  - contradiction hunts
  - longer review-only derivation drafts
- Gemini Low
  - cleanup, naming, registry checks, diff-style audits
- Opus
  - deep synthesis on a bounded packet set
  - careful contradiction-preserving review
- Sonnet
  - fast cleanup, indexing, summarization, staging normalization

Keep all of them bounded by boot packets. Do not rely on thread memory.

---

## 10. Current Best Uses

Best current external lanes for this repo:

- stale or superseded doc detection
- Thread B registry / lexeme checks
- review-only axis export lineage checks
- sim proposal design
- contradiction audits between owner packets and secondary packets

Keep this thread as the only controller for:

- Ax0 doctrine state
- bridge/cut ranking
- canon / permit decisions
- final owner-stack acceptance

---

## 11. Copy-Paste Launch Prompts

### Gemini High

```text
Read:
/absolute/path/to/BOOT_PACKET.md

Follow the boot packet exactly.
Write the complete result to:
/absolute/path/to/RETURN_PACKET.md

Do not use prior thread memory over repo files.
Do not promote review or staging language to canon.
Do not change doctrine ranking.
If blocked, write a blocked report to the same return packet.
```

### Gemini Low

```text
Read this repo boot packet:
/absolute/path/to/BOOT_PACKET.md

Do only the bounded task in that file.
Write the result here:
/absolute/path/to/RETURN_PACKET.md

No doctrine changes.
No canon promotion.
If blocked, say blocked in the return packet and stop.
```

### Opus

```text
Use the repo as ground truth.
Read:
/absolute/path/to/BOOT_PACKET.md

Perform only that bounded task.
Write your full result to:
/absolute/path/to/RETURN_PACKET.md

Preserve contradictions.
Do not smooth open items into closure.
Do not promote staging or review shapes to canon.
If blocked, write a blocked packet instead.
```

### Sonnet

```text
Read:
/absolute/path/to/BOOT_PACKET.md

Do the exact bounded task from that file and write the result to:
/absolute/path/to/RETURN_PACKET.md

Use repo files, not thread memory.
Do not change doctrine ranking.
If blocked, write a short blocked report to the same return file.
```

---

## 12. After Ingest

After a batch is processed:

- preserve accepted outputs in owner or support surfaces
- mark rejected returns clearly
- archive raw worker returns
- supersede stale boot packets if they should not be reused

The goal is not to keep every worker thread alive. The goal is to keep the repo clean and controller-readable.
