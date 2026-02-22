MEGABOOT THREAD TOPOLOGY QUOTE (verbatim)

- AXIOM_HYP N01_NONCOMMUTATION
This is a QIT constraint system, not a proof system.

THREAD TOPOLOGY (CANONICAL)
- THREAD_A1: Meta / Rosetta / Mining (chatty boundary; proposal-only; noncanon; deterministic export modes)
- THREAD_A0: Deterministic Orchestrator (chatless execution; large-batch ratchet; absorbs save + SIM wrapper logic)
- THREAD_B: Canon Kernel (constraint surface; sole source of truth; accepts/rejects; no megaboot knowledge required)
- TERMINAL_SIM: Deterministic SIM executor (non-LLM; runs approved sim packs)

HARD
- No separate THREAD_S (save/graveyard/packaging functions are executed by A0 as deterministic routines).
- No separate THREAD_SIM chat agent (SIM execution is terminal; SIM wrapper is A0).
- Mining + Rosetta live in A1.

A2_WORKING_UPGRADE_CONTEXT THREAD LAYERING QUOTE (verbatim)

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


A1 BOOTPACK QUOTE POINTER

See: work/rebaseline/BOOTPACK_THREAD_A1_v1.0__VERBATIM.md
