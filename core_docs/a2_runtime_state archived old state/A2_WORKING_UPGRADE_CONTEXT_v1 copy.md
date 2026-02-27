# A2_WORKING_UPGRADE_CONTEXT_v1

## SCOPE OF THIS DOCUMENT
This document captures the *working context* of the system upgrade as of this A2 episode.
It is intentionally long-form and procedural.
It is not a summary and is not optimized for brevity.
It exists to preserve reasoning, ordering, and decisions that cannot be reduced to atomic invariants.

This document is append-only.
Future corrections or changes must be made by appending new sections.

---

## WHY MULTI-STEP SAVES WERE REQUIRED HERE (FINAL OCCURRENCE)

During this episode, the system was not yet operating under its own save discipline.
Key constraints, roles, and mechanisms were clarified *while* the system for saving them was being designed.

As a result, multiple retroactive saves were required to avoid loss of context.
This is acknowledged as an exceptional situation.

From this point forward:
- Saves will be frequent and incremental.
- Retroactive salvage should not be necessary.
- This document marks the transition point.

---

## CORE CONSTRAINTS GOVERNING THE ENTIRE SYSTEM

The system is designed under two non-negotiable constraints:

### Finitude
- LLM context is finite.
- Threads will collapse.
- Memory continuity cannot be relied upon.
- Reboots are expected and normal.

### Noncommutation
- Order matters.
- History cannot be rewritten.
- You cannot recover the same state by reordering steps.
- Only persisted artifacts preserve ordering.

These constraints are not philosophical; they are operational.

---

## THREAD LAYERING (CURRENT, AUTHORITATIVE)

The system uses layered threads with strictly decreasing nondeterminism:

### A2 — System Upgrade / Mining / Debugging
- Fully nondeterministic.
- Long-horizon.
- Proposal-driven.
- Disposable.
- Governed by JP’s Graph-Driven Intent Runtime in full.
- Produces documents and ZIP artifacts only.
- Has zero runtime authority.

### A1 — Runtime Nondeterministic Boundary
- Nondeterministic but narrower than A2.
- Uses a reduced subset of JP’s prompt.
- Responsible for proposals, coordination, and rosetta overlays.
- Must be easy to reboot.
- Must externalize context frequently.

### A0 — Deterministic Orchestrator
- Fully deterministic.
- No interpretation or narration.
- Routes ZIP artifacts only.
- Produces runnable directories for simulations.

### B — Canon Kernel
- Deterministic accept/reject only.
- Ratchets constraints.
- Produces FULL+ saves continuously.

### SIM — Terminal Execution Environment
- Not a chat thread.
- Executes code from A0-produced directories.
- Uses Python / shell / external tools.
- Results are files, later packaged as evidence.

---

## ZIP SNAPSHOTS AS THE RATCHET MECHANISM

All persistence is via full ZIP snapshots.

Properties:
- ZIPs are immutable.
- Each ZIP is a complete world-state snapshot.
- Even a single sentence change produces a new ZIP.
- ZIPs can be dropped into a fresh thread and used immediately.

ZIPs are treated as deterministic, chatless subagents.

---

## DOCUMENT RATC HETING MODEL

Persistence is document-based, not conversation-based.

Two append-only document classes exist:

### Persistent Library
- Stores invariants, boundaries, invalidations, and failure modes.
- Prevents regression.
- Mostly atomic entries.

### Persistent Working Docs
- Store plans, procedures, reasoning, and upgrade context.
- Allow paragraphs and structure.
- Preserve ordering and rationale.
- Are still append-only at the section level.

This document is a Persistent Working Doc.

---

## WHY UNIVERSAL POST-HOC THREAD EXTRACTION FAILED

Earlier attempts to build a universal extractor for already-collapsed threads failed because they attempted to:
- reconstruct intent after the fact,
- summarize large histories,
- infer importance retroactively.

This violated both finitude and noncommutation.

The correct model is *in-process context externalization*, not rescue after collapse.

---

## A1 SAVE REQUIREMENTS (EMERGING)

A1 will require:
- explicit copy/paste blocks at the end of messages,
- model-assisted save generation,
- frequent externalization of context,
- no reliance on thread continuity.

The upgrade process is currently teaching how to do this correctly.

---

## SAVE DISCIPLINE GOING FORWARD

From this point forward:
- Every meaningful clarification is written to a document.
- Micro-saves and working-doc appends occur during the episode.
- Full ZIP snapshots are emitted frequently.
- Threads are abandoned without hesitation once artifacts are sealed.

This document, together with the Persistent Library, ensures that no essential context from this episode is lost.

---

## STATUS

This document represents the stabilized working context of the upgrade as of this episode.
Future episodes should treat it as authoritative background and append new sections rather than re-deriving this reasoning.
