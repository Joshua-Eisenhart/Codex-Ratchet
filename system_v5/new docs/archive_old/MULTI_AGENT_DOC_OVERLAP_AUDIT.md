# Multi-Agent Doc Overlap Audit

Date: 2026-04-05
Purpose: Where Opus and Hermes agree/diverge on overlapping docs

---

## Distinguishability Docs

Opus: DISTINGUISHABILITY_FORMAL_REFERENCE.md (339 lines)
Hermes: CONSTRAINT_ON_DISTINGUISHABILITY_FORMAL_REFERENCE.md (180 lines)

### Where they AGREE
- Both list: trace distance, operational equivalence, coarse-graining,
  data processing inequality, Blackwell order, Helstrom bound
- Both correctly note DPI as the linchpin (processing can't increase
  distinguishability)
- Both note identity as derived from distinguishability (Leibniz PII)

### Where they DIVERGE
- Opus includes: fidelity + Fuchs-van de Graaf, Holevo bound, Spekkens
  contextuality, Harrigan-Spekkens classification, PBR theorem, quotient
  structures in detail, RG/universality, Fisher information (Cramér-Rao,
  Fisher-Rao metric, Čencov uniqueness theorem), quantum Fisher info,
  resource theory of distinguishability (Wang/Wilde, Takagi/Regula),
  hypothesis testing (Neyman-Pearson), quantum Stein's lemma
- Hermes includes: pseudometric (Opus doesn't), superselection rules
  (Opus doesn't), simpler fit/mismatch notes per concept
- Hermes adds "fit/mismatch" framing for each concept — useful for
  the system mapping that Opus doesn't do

### Signal
Both agents independently identified the same core formal concepts
as most relevant. The DPI as linchpin emerged independently in both.
This convergence from divergent agents is evidence that these really
are the right formal anchors.

Hermes's lighter doc is better for quick reference and system mapping.
Opus's heavier doc is better for formal depth and mathematical rigor.
Both useful. Keep both.

---

## LLM Bias Docs

Opus: LLM_BIAS_AND_FAILURE_MODES_REFERENCE.md (203 lines)
Hermes: LLM_BIAS_AND_MULTI_THREAD_HARNESS_REFERENCE.md (135 lines)

### Where they AGREE
- Both list: sycophancy, hallucination/smoothing, narrative collapse,
  summary bias, overconfident closure, flattening/compression
- Both identify next-token prediction as compression objective as root cause

### Where they DIVERGE
- Opus includes: 18 paper citations with arxiv IDs, formal definitions
  from specific papers (Perez 2022, Sharma 2023, Ji 2023, Liu 2023,
  Kadavath 2022, Gao 2023, Turpin 2023), RLHF reward hacking details,
  context window architectural causes, mitigations table with evidence,
  adversarial robustness (indirect prompt injection)
- Hermes includes: multi-thread harness mitigations (merge gates,
  provenance, branch-preserving), context compression loss as a named
  mode, "do not resolve yet" as explicit state — more operational,
  less academic
- Hermes adds harness-specific mitigations that Opus doesn't

### Signal
Opus is better as a formal reference (cited papers, formal definitions).
Hermes is better as an operational guide (what to actually do about it
in the boot/harness context). Both useful. Keep both.

---

## Key Finding

The multi-agent overlap pattern is itself evidence:
- Where both agents converge independently = high-confidence concepts
- Where they diverge = complementary perspectives (depth vs operations)
- Neither is sufficient alone
- The divergence IS the information (per session doctrine)
