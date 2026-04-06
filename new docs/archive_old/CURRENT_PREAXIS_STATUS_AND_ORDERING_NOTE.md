# Current Pre-Axis Status and Ordering Note

Date: 2026-04-04 (wave-2 updated)
Status: current snapshot — do not treat as closure
Source reviews: claude-c1/c2/operator-strict, claude-writeback-followup-topo-legal-const-sat, wave-2 sims

---

## Ordering law (non-negotiable)

Pre-Axis tiers must close before Axis 0 entry.

```
Tier 0  root constraints
Tier 1  finite carrier
Tier 2  geometry
Tier 3  transport
Tier 4  differential / chirality / flux
Tier 5  negatives
Tier 6  placement / pre-entropy
────────────────────────────────────────
Tier 7  AXIS-ENTRY  ← EMBARGOED until Tiers 3–6 justify it
```

The science chain is:
```
constraints → C (admissibility charter) → M(C) (admissible manifold)
→ geometry → Weyl layer → bridge Xi → cut A|B → kernel Phi_0(rho_AB)
→ then Axis 0
```

Bridge Xi is open. Cut A|B is open. Kernel is open.
None of these are prose-closable.

---

## What is now real and live

### Operator basis — B3 admitted at lower-tier substrate
- Type-1 fiber/base grammar crosscheck: probe canonical matches engine exactly ✓
- Graph artifact emitted: 4 operator nodes + loop-pair edges + cross-axis noncomm edges ✓
- Validator: 4/4 pass, verdict `admitted_lower_tier_substrate`, layer_status `B3_operator_basis_closed`
- Type-2 grammar inversion documented but not separately validated

### C2 (coherent information / VN entropy structure)
- Purity-only proxy negative: **KILLED on 8/8 VN-positive stages** ✓
- VN coherent information is necessary — purity arithmetic inverts in the near-pure-joint-state regime
- Negative is visible in JSON artifact, kill classification present
- Status: `keep_but_open` — VN Ic is a real signal; not yet proof-backed or graph-wired

### Hopf pointwise pullback (wave-2)
- Fiber loops: constant pullback (density-stationary) ✓
- Base loops: varying Bloch trajectory (density-traversing) ✓
- Product-state I(A:B) identically zero — confirms nontrivial bridge construction required
- `hopf_pointwise_pullback_results.json` — product_guardrail_pass=true

### Weyl geometry ladder audit (wave-2)
- Holonomy varies across torus ladder (inner/outer Berry gap ~1.84, clifford ~0) ✓
- Engine response varies too; Type1/Type2 both nontrivial
- Signatures separable: witness_separable=true, guardrail_pass=true ✓
- `weyl_geometry_ladder_audit_results.json` — Type2 inversion still open

### Kernel discriminator (wave-2)
- K1_Ic (coherent information) wins: 5/6 vs K2_MI 4/6 vs K3_shell_Ic 4/6
- K1_Ic passes R1_signed, R3_bell_ceiling, R4_werner_monotone, R5_schmidt_sensitive, R6_cq_honest
- Only failure: R2_sep_anchor (K1_Ic = 0 for separable states, not anchored below)
- `a0_kernel_discriminator_results.json` — 24-state battery, no bridge assumption
- **Does NOT unlock Tier 7.** Informative for kernel identity; embargoed until Tiers 3–6 close.

### Runtime graph / edge-state writeback
- Write-back path: 8/8 write hits, P1/P3/P4/P5 all pass ✓
- **JSON artifact now exists**: `edge_state_writeback_results.json` — artifact-confirmed as of 2026-04-04
- TOPO_LEGAL: now graded from live TopoNetX cc.skeleton(1) — 0.4 (1-cell adjacency); no 2-cells yet
- CONST_SAT: honest from engine nonclassical guard check per step
- 7/7 dynamic slot columns with nonzero variance

---

## What is NOT closed / still open

### C1 (entanglement object / MI witness)
- MI-based negatives: **neither kills** (0/16 stages each) — MI is not quantum-specific or pairing-specific
- Concurrence/negativity negatives (already probed in `c1_entanglement_object_search_results.json`):
  - Fake coupling: **ALL killed** (16/16 concurrence, 16/16 negativity) ✓
  - Mispair: **8/16 killed** — the 8 surviving mispairs involve Fe/Fi (universally entangling operators); structurally explained by `c1_mispair_probe_results.json` (operator-driven, not chirality-driven)
- Status: `keep_but_open` (PARTIAL) — MI witness is dead; concurrence/negativity is the live discriminator but mispair kill is incomplete
- Open design question: how to handle universally-entangling operators in the C1 negative control contract

### C1 + C2 shared blockers
- No z3 / formal proof surface on either
- No graph artifact wired to C1 results
- No topology-pressure artifact

### Bridge, cut, kernel
- Bridge family Xi: open (wave-2 bakeoff ran; chiral family is least-arbitrary with composite 0.80 and I_c>0 everywhere; history-window leads pointwise by ~0.93 MI; no single winner selected, no closure)
- Cut family A|B: open (shell/interior-boundary is strongest doctrine-facing candidate)
- Kernel Phi_0(rho_AB): open (kernel discriminator identifies K1_Ic as winner over MI and shell_Ic; informative but embargoed)

### Type-2 engine
- Operator basis: Type-2 fiber/base grammar is inverted vs Type-1; probe is Type-1 bounded only
- No separate Type-2 canonical validation pass yet

---

## Axis 0 status

**EMBARGOED.**

Tiers 3–6 are open. Bridge Xi is open. Cut A|B is open.
No evidence in the current review set justifies Axis-entry work.

---

## Immediate unblocking priorities (in order)

1. **C1 mispair contract resolution** — concurrence/negativity already probed; MI is dead; remaining open: 8/16 mispair kills survive due to universally-entangling operators (Fe/Fi); design decision needed on whether this is structural or a contract gap
2. **Bridge Xi family selection** — wave-2 bakeoff provides evidence (chiral leads on I_c sign, history leads on MI magnitude) but no winner is selected; need decision on whether chiral vs history is the live family or if both survive
3. **Proof surface (z3)** — encode forbidden classical assumptions; first deliverable `qit_nonclassical_guards.py` or equivalent; needed for both C1 and C2
4. **C2 graph artifact** — wire coherent information result to graph layer
5. **Type2 Weyl inversion adjudication** — ladder audit confirms structural difference; inversion is documented but not adjudicated as bug/feature

---

## What this note is not

This note is not promotion evidence.
It is a current operational snapshot for ordering discipline.
Tiers above the current high-water mark are not unlocked by this note.
