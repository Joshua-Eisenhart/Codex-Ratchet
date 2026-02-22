# Thread Boundaries (A2/A1/A0/B/SIM)

Status: NONCANON | Updated: 2026-02-18

## Thread topology

| Thread | Role | Entropy | Determinism |
|--------|------|---------|-------------|
| A2 | System upgrade / mining / fuel extraction | High | Nondeterministic (LLM + user) |
| A1 | Strategy + proposal generation | Medium | Split: LLM strategy → Python expansion |
| A0 | Deterministic compiler | Low | Fully deterministic |
| B | Canon enforcement kernel | None | Fully deterministic |
| SIM | Evidence execution | None | Fully deterministic (Python, no LLM) |

## Hard boundary contracts

- **A2 → A1**: A2 produces fuel (structured entries). A1 reads fuel + B state and produces strategy JSON.
- **A1 → A0**: A1 expander outputs B-grammar proposals wrapped in ZIP. A0 compiles into EXPORT_BLOCK.
- **A0 → B**: A0 sends EXPORT_BLOCKs only. B accepts/rejects. No other communication.
- **B → SIM**: B flags specs needing evidence. SIM executes sims, returns SIM_EVIDENCE containers.
- **SIM → B**: SIM_EVIDENCE ingested by B. B resolves pending evidence.
- **B → A1 (feedback)**: Feedback loop records what B accepted/rejected, updates rosetta and constraint surface.

## What each thread may NOT do

- A2: never produces B-grammar, never runs sims, never claims canon
- A1: never sends directly to B, never emits EXPORT_BLOCKs, never decides canon
- A0: never interprets, never explains, never ingests raw high-entropy docs
- B: never reads fuel, prose, overlays, or non-container content
- SIM: never uses LLM, never modifies state, returns evidence only

## Entropy firewall (read/emit rules)

**A2** reads high-entropy docs, emits fuel artifacts + quarantine lists.
**A1** reads A2 fuel + B state + rosetta, emits strategy JSON + expanded proposals.
**A0** reads deterministic artifacts only (ZIPs, EXPORT_BLOCKs), emits compiled blocks.
**B** reads its boot + canonical containers only (EXPORT_BLOCK, SIM_EVIDENCE, SNAPSHOT).
**SIM** reads sim scripts + target spec info, emits stdout/stderr + exit code.

Rule 0: Only B can accept/reject canon. Nothing "becomes true" because A1/A2 said it.

## Save levels (from Megaboot)

- **MIN checkpoint**: fast rebootable checkpoint
- **FULL+ ratchet step**: complete canon restore state (no rosetta required)
- **FULL++ archive**: FULL+ plus campaign tape + optional rosetta/mining overlays

Source: Megaboot Section 4 — SAVE LEVELS

## A1 dual role

A1 does two things under nondeterministic search:
1. **Rosetta projection**: strip jargon, create pure-math candidates, reattach labels
2. **Evolutionary exploration**: search for constraint-compatible candidates with wiggle room

Both produce proposals. Neither touches canon. The A1→A0 handoff is where nondeterminism ends.

## Source pointers

- Megaboot thread topology: `work/rebaseline/BOUNDARY_QUOTES_A0_A1_A2.md`
- A0 verbatim boot: `work/rebaseline/BOOTPACK_THREAD_A0_v2.62__VERBATIM.md`
- A1 verbatim boot: `work/rebaseline/BOOTPACK_THREAD_A1_v1.0__VERBATIM.md`
