Status: `exists` — an authored proposal, not executed code. This document is
one candidate among rivals in `system_v8/candidates/`. It is not canon and
does not admit anything. `promotion_allowed: false`,
`formal_admission_allowed: false`. Role: `order_nesting_rival` — same
shared axis vocabulary (layers/axes 0 through 12) the pool's existing
bottom-up and top-down members already use, tested under a genuinely
different SCHEDULE ORDER: bidirectional from a middle layer, rather than a
single monotone sweep. This fills the gap `candidate_topdown_12to0.md`'s
own weaknesses section names but does not build: "a middle-out /
depths-both-ways order... absent from its schedule."

Provenance: authored by an NVIDIA-hosted model, `qwen/qwen3-next-80b-a3b-instruct`,
via a single `curl` POST to `https://integrate.api.nvidia.com/v1/chat/completions`
(`max_tokens: 2500`, response returned with `finish_reason: stop`, not
truncated). The verbatim prompt and full response are in
`fuel_gate/manifests/current_pool_provenance_manifest.json` under this
file's `provenance.prompt_lineage`. Body below is the model's output,
reproduced as generated (only this status/provenance preamble was added on
top; the model's own numbered-list format is kept as returned).

---

# Middle-Out Order-Nesting Rival Brief

1. If the minimal persisting structure of a finite ratchet can be meaningfully probed by simultaneously constraining outward from a central layer—rather than accumulating from the base or collapsing from the apex—then a middle-out bidirectional schedule may reveal coherence or contradiction invisible to monotonic sweeps.

2. This ordering installs the following assumptions: (a) that layer 6 (or another chosen mid-point) is epistemically accessible prior to the verification of its immediate neighbors, (b) that constraints discovered in opposite directions can be meaningfully compared without prior alignment of their lexical or structural vocabularies, and (c) that the middle layer's internal structure is sufficiently stable to serve as a pivot—despite the pool's shared axiom that no layer should be treated as foundational until its dependencies are earned. These are presumptions the bottom-up and top-down candidates explicitly reject; this schedule inherits their skepticism but violates their procedural discipline.

3. Carrier identifier: `system_v8/candidates` (same as pool), Nesting/order identifier: `middle_out_6_bidirectional`

4. Probe / distinguishability test: Run two concurrent constraint-sweeps from layer 6—downward toward layer 0 and upward toward layer 12—and record the set of admissible constraints at each step. If the downward sweep produces a constraint that explicitly forbids a constraint produced by the upward sweep at any symmetric pair of layers (e.g., layer 5 vs layer 7, layer 4 vs layer 8), then the schedule fails the test of mutual consistency. If no such contradiction arises after full traversal, the schedule passes the probe/test as structurally coherent under nominalist constraints.

5. This schedule would flip its viability if the middle layer (layer 6) is shown to contain emergent structure that cannot be reconstructed from either the lower or upper halves—thereby losing its claim to be a neutral pivot and revealing itself as an unearned assumption. It wins if the bidirectional sweeps converge on identical constraint boundaries without external mediation.

6. Known failure modes: (a) The middle layer (layer 6) may be underdefined or semantically unstable, making it a fragile anchor—exactly the kind of premature stabilization the bottom-up camp warns against; (b) bidirectional sweeps may generate incompatible constraint vocabularies (e.g., QIT density terms vs registry state terms) that cannot be reconciled without an external translation layer, violating the pool's nominalist constraint-admissibility ratchet; (c) the schedule may produce phantom coherence by conflating syntactic symmetry with semantic equivalence, creating false consistency where none exists.

7. promotion_allowed: false, formal_admission_allowed: false
