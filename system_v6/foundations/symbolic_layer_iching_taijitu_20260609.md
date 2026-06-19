---
status: symbolic-layer reference (I Ching / yin-yang / taijitu / Jung / IGT) — PROPOSAL/SYMBOLIC SUPPORT, not root math (owner's own framing, 2026-06-09)
claim_ceiling: symbolic/readout layer over the lower engine geometry. Five layers kept separate per the taijitu doc: (1) actual lower-axis mathematics, (2) actual simulated geometry, (3) taijitu symbolic layer, (4) Jung/IGT label layer, (5) open or inverted symbolic assignments.
provenance: owner-curated consolidation (2026-06-09 session) + cited source docs
sources: ~/wiki/raw/articles/system-v5-reference-docs/TAIJITU_AXES_0_6_EXPLICIT_SYMBOLIC_LAYER copy.md; ~/wiki/queries/packet-f-axes-math-apple-notes-dump-extraction-2026-05-19.md; system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md; ~/wiki/raw/articles/system-v5-reference-docs/iching axes rosetta.md (owner working notes); system_v6/receipts/screenshots_math_report_20260609.md (Type1/Type2 full charts transcribed)
---

# Symbolic Layer: I Ching / Taijitu / Jung / IGT over Axes 0-6

Position in the stack (owner): Hopf/Weyl carrier + density/QIT operators -> terrain families and loop placements -> axis readouts 0-6 -> **I Ching/taijitu/Jung/IGT symbolic map** -> Carnot/Szilard engine analogues as finite-map probes.

## 1. Taijitu on the Clifford torus (symbolic geometry witness)

Outer symbolic drive = Axis 0 (the enclosing circle). Local anchor b_0 = sign(cos 2eta): eta < pi/4 upper/white side; eta = pi/4 neutral threshold; eta > pi/4 lower/black side.
Clifford-torus witness: q(theta1,theta2) = (cos(pi/4) e^{i theta1}, sin(pi/4) e^{i theta2}); boundary branches theta1 = theta2 and theta1 = theta2 + pi; black region theta1-theta2 in (0,pi), white in (pi,2pi); black dot = eta->0 limit, white dot = eta->pi/2 limit.
This is a symbolic geometry witness; it does NOT override the lower-stack Axis-0 seat/bridge definitions (bridge open).

## 2. Master axis table (symbol <-> Jung <-> IGT <-> math anchor)

| Axis | Taijitu symbol | Jung | IGT | Math anchor | Status |
|---|---|---|---|---|---|
| 0 | black vs white + enclosing circle | Ni/Ne vs Si/Se | WinLose/LoseLose vs LoseWin/WinWin | b0 = sign(cos 2eta); later Phi0(rho_AB) | strong symbolic; bridge OPEN |
| 1 | dot-in-teardrop pairs | Se/Ni vs Ne/Si | LoseWin/LoseLose vs WinLose/WinWin | unitary vs proper-CPTP legality | usable |
| 2 | dots vs teardrops | Se/Ne vs Si/Ni | direct vs conjugated | rho vs V†rhoV (connection K_t = iV†V̇) | usable |
| 3 | inner tail-chasing vs outer fat-tip-chasing | inner/outer token sets | — | fiber gamma_f vs lifted-base gamma_b | strongest symbolic reading |
| 4 | CW vs CCW spin | TiFe vs FeTi (runtime FeTi vs TeFi) | — | Phi_D vs Phi_I; [L_R,L_C] commutator | spin assignment OPEN |
| 5 | S-curve/lobe weighting | FeFi vs TiTe | rotation-class vs dephasing-class tokens | {Ti,Te} vs {Fi,Fe}; broader FGA vs FSA | overlay OPEN |
| 6 | up vs down reading of same symbol | judging-first vs perceiving-first | up/down tokens | b6 = -b0*b3; L_A vs R_A; Phi_T∘O vs O∘Phi_T | strong symbolic |

Axis1 x Axis2 four-part placement: white dot=Ni/LoseLose, black teardrop=Se/LoseWin, white teardrop=Ne/WinLose, black dot=Si/WinWin.
Axis6 directional table (derives b6=-b0*b3 token-explicitly): inner+white=up, inner+black=down, outer+white=down, outer+black=up.

## 3. Six-line / I Ching placement (PROPOSAL-ONLY per taijitu doc)

| Hexagram line | Axis |
|---|---|
| line 1 | Axis 6 |
| line 2 | Axis 5 |
| line 3 | Axis 3 |
| line 4 | Axis 4 |
| line 5 | Axis 1 |
| line 6 | Axis 2 |

**Axis 0 is OUTSIDE the six-line stack** — "external drive through the six-line space," the enclosing/cut/readout field, not one more hexagram bit. This matches the dual-stack axis-placement (scaffold section 15): Axis0 = readout field; Axes 1-6 = finite update schedule structure.

## 4. The 64 correspondences (status discipline)

- I Ching 64-hexagram layer = SCHEDULE INDEX layer (atlas: "IGT = stage grammar. Jung = operator grammar. I Ching = 64-schedule index. They do not overlap. They do not redefine each other.").
- Live runtime 64 = 2 engines x 8 terrains x 4 operator slots (engine_core.py); chart-locked macro-stages = 16; current eng_64 receipt: 64 stages enumerate but n_distinct=16 fingerprints (honest degeneracy, dynamic distinctness NOT established).
- OPEN (atlas's own warning): two different 8-way constructions on file — generalized-spinor 8 = 4 topologies x 2 loop families, and Terrain8 = Topology4 x Flux2 — "correlated, but not proven the same object." Discriminator sim queued.
- 8 Terrains x 8 Signed Operators = 64: strong scaffold, STILL PROPOSAL until runtime decodes it structurally (RUNTIME_TO_STRUCTURE_BRIDGE.md).

## 5. Type1/Type2 full charts

The complete stage-token charts (topology | terrain | loop | order family | token | Axis6 UP/DOWN | signed op | WIN/LOSE result | pattern) are transcribed verbatim in system_v6/receipts/screenshots_math_report_20260609.md (NeTX.png / Topology.png / Outer Malor.png sections) and summarized in the owner scaffold. Global locks: Type1 = flux IN, outer deductive FeTi / inner inductive TeFi; Type2 = flux OUT, outer inductive TeFi / inner deductive FeTi. Loop orders: inductive Se->Si->Ni->Ne; deductive Se->Ne->Ni->Si. Terrain graph edges: Ax0 = Se-Si, Ne-Ni; Ax2 = Se-Ne, Si-Ni. WIN/LOSE casing = readout grammar ONLY (fence).

## 6. Engine packets as finite-map probes (file-verified 2026-06-09)

- eng_carnot_axiswired: all_pass=true, tool_lego_fit_probe, promotion blocked. Carnot = thermodynamic-legality grammar (4 strokes x 4 substages x 2 directions = 32; Clausius bookkeeping as Axis0 readout). The wiki inventory note claiming verdict=False is stale/unsupported by the result file.
- eng_szilard_axiswired: all_pass=true, tool_lego_fit_probe. Szilard axis map: Ax0 entropy readout only (not a stage bit); Ax1 expand/compress Bloch-volume CP channel; Ax2 open-isothermal vs closed-adiabatic; Ax3 Carnot/Szilard selector; Ax4 CW-forward vs CCW-reversed; Ax5 spectral/hot vs gradient/cold; Ax6 stroke order/precedence.
- Packet F Carnot analogue of Type-1 deductive loop: Ni singular collapse = isothermal compression; Si stable basin = adiabatic compression; Ne spiral mixing = isothermal expansion; Se gradient descent = adiabatic expansion. Analogy/probe lane, not proof.
- Current dual-stack doctrine: scaffold sections 14-15 (Carnot+Szilard = two legality grammars dual-stacked on one finite QIT carrier).

## 7. Keep-separate rule (binding)

The symbolic layer supplies the PLACEMENT MAP. The sim target is always the Hopf-Weyl/QIT finite carrier with terrain laws and signed operator precedence. Jung/I-Ching/yin-yang labels are correlation layers, never primary mathematics, never promotion evidence.

## 8. Owner correction: two-engine WIN/LOSE pattern should be encoded, not forced into I Ching

Owner correction, 2026-06-09:

```text
there are 2 engine types.
this pattern is probraibly important to encode in other forms and math, and save.
since in my thinking it creates the qit engine math naturally and the 0-6 axes.
and maps to the iching.
I wasnt trying to force iching convergence.
i suspected it was possible and wanted it to naturaly emerge at the end.
```

Processed status:

- The object to preserve is the **paired two-engine casing structure**, not one isolated chart, and not an unordered square:

```text
(Type 1 WIN/LOSE/win/lose table, Type 2 WIN/LOSE/win/lose table)
```

- Owner correction: the terrain/function families are read in **two directed loop orders**:

```text
Se -> Ne -> Ni -> Si
Se -> Si -> Ni -> Ne
```

These are loop orders / directed cycles, not just four vertices of a static `Z2 x Z2` square. Any later finite-automaton, QIT-schedule, 64-index, or I Ching comparison must preserve the order separately from the content labels.

- Owner correction: on an actual engine loop, the active readout is the **loop-selected component** of the paired word, not necessarily the whole paired word. Example:

```text
Ni stage word = loseLOSE
active loop may read = lose
```

and:

```text
Type 1 outer loop at WINlose stage reads WIN
```

So the paired word preserves the two-loop stage structure, while each engine loop reads its own selected casing/component. This applies across the 16 strategies. Encoding the full word as the active loop value would overstate the per-loop readout.

- Current finite discriminator evidence says the pattern is rigid only with the right data named:

```text
balance + case-inversion duality -> 36 possible paired two-engine tables
balance + case-inversion duality + sign scaffold + operator placement -> 1 paired table
```

- Therefore the honest current result is:

```text
The documented two-engine WIN/LOSE pattern is unique under sign scaffold + operator placement.
It is not sign-only, and it is not yet a physics/admission theorem.
```

- This pattern should be encoded in multiple mathematical forms before stronger claims are made:
  - finite CSP / model-count form;
  - signed operator-placement table;
  - two-engine paired chart;
  - 64-schedule index candidate;
  - QIT channel/order schedule candidate;
  - Axis 0-6 readout candidate.

- I Ching/hexagram convergence must remain a downstream emergence test:

```text
Do not force I Ching at the start.
Let the two-engine pattern, axes, signed operators, and QIT schedule produce a 64-structure first.
Then compare that emergent 64-structure against I Ching/taijitu mappings.
```

This keeps the owner's intended direction intact: the I Ching map was suspected as a possible natural endpoint, not imposed as a premise.
