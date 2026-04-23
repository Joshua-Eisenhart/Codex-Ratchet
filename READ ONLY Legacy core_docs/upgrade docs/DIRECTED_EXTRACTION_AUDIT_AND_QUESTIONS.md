# DIRECTED EXTRACTION AUDIT & QUESTION SET

Below is a pure audit response plus a targeted question set to extract missing high-value structure.
No fixes. No redesign. No synthesis beyond categorization.

---

## AUDIT — EXTRACTION STATUS & REMAINING GAPS

Based on PASS 1–8, extraction is correct but now hitting diminishing returns unless it becomes directed.

### What is already well-captured (DO NOT re-ask)

- ZIPs as deterministic, chatless subagents  
- Megaboot is a single authoritative document  
- A0 deterministic, absorbs S + SIM coordination  
- A1 nondeterministic internally, deterministic exports, explicit modes  
- B deterministic canon kernel  
- SIM external terminal, approval gated  
- Graveyard mandatory, ≥50% interaction when non-empty  
- Massive exploratory batching required  
- Sharding required for LLM usability  
- Extraction itself is a system feature  
- Mode control is probabilistic, confirmation > enforcement  

Re-asking any of the above will only create noise.

---

## What is missing (audit-level gaps)

These are not contradictions. They are unextracted decisions or implicit assumptions likely already present but not yet pulled out explicitly.

### GAP 1 — ZIP TYPE ENUMERATION (CRITICAL)

You described ZIPs abstractly but not enumerated them concretely.

Missing:
- A complete list of ZIP kinds the system expects to exist.

Without this, template creation cannot converge.

---

### GAP 2 — A0 MASSIVE BATCH POLICY (CRITICAL)

Identified A0 behaved conservatively, but missing:

- Whether explicit numeric targets were discussed  
- Whether “1000 items” was:
  - a hard target
  - an example
  - phase-dependent  
- Whether batch size tied to:
  - stage
  - acceptance ratio
  - graveyard size
  - exploration vs convergence  

Intent is currently qualitative, not operational.

---

### GAP 3 — SHARDING STRATEGY HEURISTICS

You stated sharding must be “good for LLM usage”.

Missing:
- Any heuristics discussed:
  - shard by topic
  - shard by chronology
  - shard by semantic independence
  - shard by failure domain  
- Any hard limits assumed:
  - max lines
  - max tokens
  - max concepts per shard  

Likely implicit in the thread.

---

### GAP 4 — FULL+ CONFIRMATION MECHANISM

You stated:
“FULL+ save could be done by B, then sent to A0 to be confirmed”

Missing:
- What “confirm” means:
  - hash check
  - completeness check
  - sanity check  
- Whether A0 can refuse FULL+  
- Consequences of refusal  

---

### GAP 5 — FULL++ CONFIRMATION DEPENDENCY

You stated:
“A1 will do the FULL++ save with rosetta, but needs A0 to also confirm.”

Missing:
- Whether A0 confirmation is:
  - structural only
  - content-blind
  - required before archive  
- Whether FULL++ can exist without confirmation (flagged vs rejected)

---

### GAP 6 — PHASE TRANSITION SIGNALS

You distinguish:
- exploration phase
- convergence phase

Missing:
- Whether explicit transition signals were discussed:
  - acceptance ratio trend
  - graveyard churn rate
  - recurrence of structures  
- Or if this is fully human-judged

---

## TARGETED QUESTIONS TO SEND BACK (COPY/PASTE)

### QUESTION SET A — ZIP ENUMERATION

List every distinct ZIP type discussed or implied.  
For each ZIP, give:
- name (working or placeholder)
- producer (A0 / A1 / B / SIM / human)
- consumer
- purpose (1 sentence)

Do not design new ZIPs. Only list what was discussed or implied.

---

### QUESTION SET B — A0 BATCH SCALE

Extract any explicit or implicit batch size targets for A0.  
Include:
- numbers (even approximate)
- conditions when batch size increases/decreases
- any link to graveyard size or acceptance ratio

Preserve ambiguity if unresolved.

---

### QUESTION SET C — SHARDING HEURISTICS

Extract any discussion of sharding beyond byte limits.  
Include:
- semantic or structural ideas
- LLM-specific constraints mentioned
- whether sharding is phase-dependent

---

### QUESTION SET D — FULL+ CONFIRMATION

Extract any discussion of A0 confirming FULL+ state from B.  
Include:
- what “confirmation” means
- whether refusal was considered
- consequences of refusal or mismatch

---

### QUESTION SET E — FULL++ CONFIRMATION

Extract any discussion of A0 confirming A1’s FULL++ archive.  
Include:
- required vs optional confirmation
- structural vs content-based confirmation
- failure handling discussed

---

### QUESTION SET F — PHASE TRANSITION

Extract any discussion of signals for moving from exploration to convergence.  
Include:
- metrics
- heuristics
- human judgment criteria

Do not invent signals.

---

## AUDIT CONCLUSION

- Extraction is past the broad-sweep phase.
- Further progress requires directed extraction.
- The six gaps above are the highest-leverage missing structure.
- Answers enable:
  - ZIP template definition
  - A0 behavior locking
  - Megaboot rewrite without guesswork
