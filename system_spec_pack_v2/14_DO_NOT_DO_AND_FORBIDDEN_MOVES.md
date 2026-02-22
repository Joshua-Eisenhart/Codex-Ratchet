# DO NOT DO + Forbidden Moves (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: enumerate explicit forbidden moves and misinterpretations that would break the system or contaminate canon.

==================================================
0) Root Constraint Violations (forbidden)
==================================================

- Do NOT treat `F01_FINITUDE` or `N01_NONCOMMUTATION` as negotiable, optional, or “axioms you can swap”.
- Do NOT introduce new “root constraints” as ontological peers of `F01_FINITUDE` and `N01_NONCOMMUTATION`.
  - Operational meta rules (audit, locality, canonicalization) are allowed only as harness rules above/beside the kernel.

==================================================
1) Noncommutation Misread (forbidden)
==================================================

- Do NOT interpret `N01_NONCOMMUTATION` as “dependency graph must be a DAG; no cycles”.
  - Cycles/loops may exist as explicit objects and explicit sim-validated structures.
  - The forbidden move is: assuming commutation or assuming order irrelevance.

==================================================
2) Canon Contamination (forbidden)
==================================================

- Do NOT admit overlay/jargon terms into Thread B canon as primitives.
  - Examples (non-exhaustive): `axis`, `engine`, `spinor`, `hopf`, `bloch`, `weyl`, MBTI/IGT labels.
  - These belong only in A2/A1 overlay and may map to canon terms via rosetta after canon terms exist.

- Do NOT allow free English to cross into B-scanned fields.
  - Any natural language notes must remain above the boundary (A1 strategy / A2 docs).
  - B-facing artifacts must remain strictly in bootpack grammar.

==================================================
3) Artifact Boundary Violations (forbidden)
==================================================

- Do NOT send YAML to B as a canon artifact.
  - YAML is allowed above the boundary (A2/A1).
  - B accepts only: `EXPORT_BLOCK`, `SIM_EVIDENCE`, `THREAD_S_SAVE_SNAPSHOT` (per bootpack).

- Do NOT mix prose with artifacts.
  - B-facing messages must be single-artifact containers only.

==================================================
4) “Ratcheted” Mislabeling (forbidden)
==================================================

- Do NOT claim “ratcheted” when only a TERM_DEF exists.
- Do NOT treat “admitted” as “validated”.

Minimum meaning for “ratcheted (meaningful)” is:
- positive sim evidence exists
- negative sim evidence exists (at least one)
- plausible alternative(s) exist and failed (graveyard)

==================================================
5) Evidence / SIM Shortcuts (forbidden)
==================================================

- Do NOT fabricate SIM_EVIDENCE without a real sim run + manifest trail.
- Do NOT treat “sim exists on disk” as evidence; evidence must be ingested as SIM_EVIDENCE and recorded in state.
- Do NOT accept “negative sim missing” as normal for meaningful survivors.

==================================================
6) Graveyard Shortcuts (forbidden)
==================================================

- Do NOT create a “graveyard” by padding with garbage probes or irrelevant junk.
- Do NOT record graveyard entries without verbatim `raw_lines`.
  - Without raw lines, the graveyard is not replayable and cannot be mined for resurrection.

==================================================
7) Doc Explosion (forbidden)
==================================================

- Do NOT create one file per batch by default.
  - Use append + shard.

- Do NOT write unbounded new docs into the repo root.
  - All outputs must be contained under an explicit run directory or an archive/quarantine directory.

==================================================
8) Determinism Boundary Breach (forbidden)
==================================================

- Do NOT let LLM behavior leak below the boundary:
  - A0 compilation must be deterministic.
  - B evaluation must be deterministic.
  - SIM execution must be deterministic (given pinned code + pinned inputs).

- Do NOT let B or SIM depend on “interpretation” of natural language.

