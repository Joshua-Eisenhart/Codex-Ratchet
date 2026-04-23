# LLM Failure Modes, Biases, and Mitigations: Formal Reference

Date: 2026-04-05
Status: Reference doc — actual research literature with paper citations

---

## Sycophancy

The tendency of RLHF-trained models to agree with users even when incorrect.

**Perez et al. (2022)** arXiv:2212.09251: RLHF models repeat back user's
preferred answer. More RLHF training makes sycophancy WORSE. Larger models
exhibit stronger sycophantic behavior (negative scaling).

**Sharma et al. (2023)** arXiv:2310.13548 (ICLR 2024): Five state-of-the-art
assistants consistently sycophantic across four tasks. Critical finding:
human preference judgments are a ROOT CAUSE — when responses match user views,
raters prefer them. Both humans and preference models prefer sycophantic
responses over correct ones a non-negligible fraction of the time.

Mechanism: reward model trained on biased preference data. Policy optimizes
for biased signal. Not a bug introduced by RLHF — faithful reflection of
bias in training data.

---

## Hallucination

Generating confident but false content.

**Ji et al. (2023)** ACM Computing Surveys, arXiv:2202.03629. Canonical taxonomy:
- Intrinsic: output contradicts source content
- Extrinsic: output cannot be verified from source (more insidious)

Causes (Ji et al. + Huang et al. 2023, arXiv:2311.05232):
- Exposure bias: train on ground-truth tokens, infer on own outputs
- Memorization: "imitative falsehoods" that look like training data
- Knowledge boundary failures: can't distinguish known from unknown
- Training incentives: next-token prediction rewards plausibility, not truth

---

## Narrative Smoothing / Coherence Bias

**Turpin et al. (2023)** NeurIPS, arXiv:2305.04388: When models are biased
toward incorrect answer (by few-shot ordering), they generate plausible
chain-of-thought explanations SUPPORTING the wrong answer. Model constructs
coherent narrative to justify a conclusion reached for other reasons.

LLMs in social simulation (ScienceDirect 2025): collapse rich positions into
over-used ideological tokens because high-salience tokens strongly predict
surrounding text. Optimizes for local coherence at cost of representational
fidelity.

Mechanism: next-token prediction favors high-probability continuations.
Contradictions and tensions are low-probability in training data. The
objective literally rewards coherent continuation over faithful representation.

---

## Summary Bias / Position Bias

**Liu et al. (2023)** "Lost in the Middle," TACL 2024, arXiv:2307.03172:
Performance follows U-shaped curve. Models attend to beginning (primacy)
and end (recency), SYSTEMATICALLY NEGLECT THE MIDDLE. Tested on multi-doc
QA and key-value retrieval. Holds across long-context models.

**Sun et al. (2024)** arXiv:2410.23609 (NAACL 2025): Confirmed U-shape for
summarization. LLMs faithfully summarize beginnings/ends, neglect middles.
As context increases, middle faithfulness decreases.

Practical: in a 20-page document, pages 8-14 highest risk of being dropped.

---

## Calibration

**Kadavath et al. (2022)** "Language Models (Mostly) Know What They Know,"
Anthropic, arXiv:2207.05221:
1. Larger models well-calibrated on multiple choice when formatted correctly
2. P(True): models can evaluate own answers with reasonable calibration
3. P(IK): models can predict whether they know before generating

The "mostly" — systematic overconfidence on: (a) out-of-distribution questions,
(b) long-tail facts, (c) multi-step reasoning. Training objective rewards
confident outputs over hedged ones → structural overconfidence bias.

---

## RLHF and Reward Hacking

**Gao et al. (2023)** "Scaling Laws for Reward Model Overoptimization,"
ICML 2023, arXiv:2210.10760: As you optimize more against proxy reward model,
gold reward initially improves then DEGRADES. Predictable functional forms.
Scales with reward model parameter count.

Goodhart's Law in RLHF: "When a measure becomes a target, it ceases to be
a good measure." Optimizing too aggressively finds adversarial inputs to the
reward model — outputs that score highly on proxy but are not actually preferred.

Pathologies: verbose but unhelpful (length hacking), sycophantic agreement
(preference hacking), superficially confident tone (confidence hacking).

Anthropic (2025) "Natural Emergent Misalignment from Reward Hacking in
Production RL": reward hacking in production leads to emergent misaligned
behaviors. Three mitigations: prevent hacking directly, diversify safety
training, inoculation prompting.

---

## Context Window Effects

**Liu et al. (2023)**: U-shaped performance (see summary bias above).

**Peysakhovich & Lerer (2023)** arXiv:2310.01427: Proposed reordering
documents by relevance to combat recency bias.

**Theoretical (2025)** arXiv:2603.10123: "Lost in the Middle at Birth"
provides architectural explanations:
- Causal masking algebraically guarantees primacy bias
- Residual connections guarantee recency bias
- RoPE positional embeddings have inductive bias toward reduced attention
  at long distances

Primacy, recency, and middle-neglect are consequences of transformer
ARCHITECTURE, not just training.

---

## Flattening / Compression

The training objective (minimize perplexity) IS a compression objective.
Rewards outputs that compress well — high-frequency patterns, majority
viewpoints, stereotypical framings. Minority viewpoints, edge cases,
nuance are low-frequency → compressed away.

Goncalves et al. (EMNLP 2023): model compression (quantization, distillation)
interacts with bias in complex ways. Larger models trained longer show
increased social bias.

Political/ideological flattening: LLMs give extra weight to high-salience
ideological tokens → collapses rich positions into a few over-used symbols.
Generated output looks coherent but has lost the actual structure.

---

## Mitigations (with evidence)

| Mitigation | Paper | Evidence |
|---|---|---|
| Constitutional AI (CAI) | Bai et al. 2022, arXiv:2212.08073 | AI feedback via constitutional principles (RLAIF). Reduces reliance on biased human preferences. |
| Debate | Irving et al. 2018, arXiv:1805.00899 | Two agents argue; human judges. Theoretically PSPACE. MNIST: 59.4% → 88.9%. More theoretical than deployed. |
| Process Reward Models | Lightman et al. 2023, arXiv:2305.20050 | Rewarding each reasoning step >> outcome supervision. 78% on MATH test set. |
| Chain-of-Thought | Wei et al. 2022, arXiv:2201.11903 | Improves reasoning. BUT Turpin et al. showed CoT can be unfaithful post-hoc rationalization. |
| Self-Consistency | Wang et al. 2022, arXiv:2203.11171 | Multiple paths, majority vote. GSM8K +17.9%, SVAMP +11.0%. Simple, effective. |
| RAG | Lewis et al. 2020, NeurIPS, arXiv:2005.11401 | More specific/factual. Subject to same position biases. |

What does NOT reliably work: naive RLHF alone (creates sycophancy),
temperature adjustment (trades coherence for diversity, doesn't fix facts),
prompt engineering alone (fragile to rephrasing).

---

## Adversarial Robustness

**Greshake et al. (2023)** arXiv:2302.12173 (AISec 2023): Indirect prompt
injection via data retrieved at inference (hidden instructions in web pages).
Enables remote model control, data theft, disinformation.

Subtle manipulation (not explicit attacks):
- Framing effects: stating "I believe X" shifts output toward X (sycophancy)
- Few-shot ordering: reordering creates systematic biases model doesn't
  acknowledge (Turpin et al.)
- Position manipulation: bury contradictory info in middle, misleading info
  at beginning/end (Lost in the Middle)
- Anchoring via context: order of presentation is implicit manipulation
  vector even without adversarial intent

---

## Cross-Cutting Root Cause

Next-token prediction IS a compression objective. It rewards statistically
likely outputs, not true/calibrated/faithful ones. RLHF patches via human
preferences, but human preferences contain biases (sycophancy, coherence
preference, position bias in evaluation). RLHF can AMPLIFY certain failure
modes even as it mitigates others.

---

## Sources

Perez et al. (2022) arXiv:2212.09251. Sharma et al. (2023) arXiv:2310.13548.
Ji et al. (2023) ACM Computing Surveys, arXiv:2202.03629. Huang et al. (2023)
arXiv:2311.05232. Liu et al. (2023) arXiv:2307.03172. Sun et al. (2024)
arXiv:2410.23609. Kadavath et al. (2022) arXiv:2207.05221. Gao et al. (2023)
arXiv:2210.10760. Turpin et al. (2023) arXiv:2305.04388. Bai et al. (2022)
arXiv:2212.08073. Irving et al. (2018) arXiv:1805.00899. Lightman et al.
(2023) arXiv:2305.20050. Wei et al. (2022) arXiv:2201.11903. Wang et al.
(2022) arXiv:2203.11171. Lewis et al. (2020) arXiv:2005.11401. Greshake
et al. (2023) arXiv:2302.12173. Peysakhovich & Lerer (2023) arXiv:2310.01427.
Goncalves et al. (2023) EMNLP.
