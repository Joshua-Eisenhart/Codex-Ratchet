# Boot Prompts and Read-Order Templates

Date: 2026-04-05
Status: Operational template doc — for starting a fresh Hermes/Claude thread without collapsing layers

---

## Purpose

This doc gives concrete prompt templates and read orders for booting a new thread.

Use it when the stack is growing and a new agent must enter without flattening the distinctions between:
- governing constraints
- candidate thesis
- reference traditions
- audit notes
- rolling handoff state

---

## Default read order

For a fresh thread, read in this order:
1. SYSTEM_CONTEXT_HANDOFF__CURRENT.md
2. CONSTRAINT_SURFACE_AND_PROCESS.md
3. OWNER_THESIS_AND_COSMOLOGY.md
4. NOMINALISM_IN_THIS_SYSTEM.md
5. relevant reference doc(s)
6. relevant audit doc(s)
7. only then write or edit

If the task is narrow, read only the minimal subset needed.

---

## Boot prompt template: governing-doc rewrite

Use this when editing core system docs:

"Read SYSTEM_CONTEXT_HANDOFF__CURRENT.md first. Then read the governing docs for the task. Preserve the distinction between governing constraints, candidate thesis, and reference support. Do not introduce new ontology. Make only the requested rewrite. Report exact changes and remaining rough edges."

---

## Boot prompt template: reference doc writing

Use this when adding a new support tradition:

"Read the existing reference docs for style. Write a new reference doc that uses exact established terminology only. Include exact fit, mismatch notes, and system-side mapping. Do not collapse the support tradition into the system ontology."

---

## Boot prompt template: mapping doc writing

Use this when connecting traditions to the system:

"Write a mapping doc that links support traditions to the system’s actual claims. Keep the mapping explicit: tradition, exact support, mismatch, and do-not-use warnings. The document should sit between reference docs and governing docs."

---

## Boot prompt template: audit pass

Use this when auditing an overgrown folder:

"Audit the folder by role, not by filename alone. Separate governing docs, reference docs, audit docs, handoff docs, and archive residue. Identify overlap, residual ladder language, and any unsupported overclaiming. Then propose a narrow rewrite order."

---

## Boot prompt template: Claude Code run

Use this for an actual Claude Code run:

"Update only the files explicitly named in the task. Keep changes minimal and local. If a document is a candidate thesis, label it that way. If a document is a governing doc, keep it non-derivative and explicit. If a support doc uses an exact formal term, preserve it. Do not generalize or smooth over distinctions. After editing, summarize what changed and what remains to be fixed."

---

## Read-order rule

The read order should be driven by the task’s layer:
- governing change -> handoff + governing docs first
- support writing -> reference docs first, then mapping
- audit -> handoff + audit docs first
- consolidation -> all role docs, then overlap review

Never start with the broadest umbrella doc unless the task is specifically architectural.
