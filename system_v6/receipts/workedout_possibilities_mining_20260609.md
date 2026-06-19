# Worked-Out Possibilities Deep-Mining Report

Generated: 2026-06-09
Lane: codex2 HIGH effort / deep-mining
Write boundary: only this file, `/tmp/found/workedout_possibilities_report.md`

## Scope And Provenance Labels

I mined these surfaces, with emphasis on exact quotes and line citations:

- `/Users/joshuaeisenhart/wiki/raw/`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/READ ONLY Reference Docs/`
- `/Users/joshuaeisenhart/Codex-Ratchet/READ ONLY Legacy core_docs/`
- `/Users/joshuaeisenhart/wiki/concepts/`
- `/Users/joshuaeisenhart/wiki/projects/`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v4/docs/`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v4/probes/`

Provenance labels used below:

- OWNER-AUTHORED: direct `You said:` / owner wording, or a document explicitly preserving owner statements.
- LLM-GENERATED / COMPILED: ChatGPT/Gemini/Grok/compiled reference docs. These are evidence of worked-out possibilities on file, not owner-canonical proof.
- CODE / RUNTIME: executable implementation or probe comments. These prove a worked-out implementation exists, not that the math is canonical.
- AUDIT / ROUTER: repo/wiki status pages that route evidence and preserve ceilings.

Important ceiling: this report does not promote anything to canonical. It only records worked-out possibilities on file before declaring anything missing.

## Search Pattern Summary

Representative searches run across the corpus:

```text
rg -n -i "sigma_|sigma_plus|sigma_minus|sigma\+|sigma-|Ne / Vortex|Ne / Spiral|Hamiltonian|weak dissipator|projector|m_L|m_R|P_j|commuting Hamiltonian|Phi|e\^{t|stage channel|finite time|16 placements|Y_in|Y_out|64 runtime|64-stage|nested Hopf tori|win lose functional|coherent information|trace distance|flux|holonomy|cos\(2eta\)|Weyl spinor|Q8|quaternion group|split octonion|split G2|associator|tetrahedron" ...
rg -n -i "Q8|quaternion group|finite group|8 operators|eight operators|operator.*Q8|terrain.*Q8|Pauli group|dihedral|Klein|Dih" ...
rg -n -i "split octonion|split-octonion|split G2|split-G2|split real form|octonion|sedenion|Fano|Spin\(7\)|\bG2\b" ...
rg -n -i "associator.*flux|flux.*associator|tetrahedron.*flux|flux.*tetrahedron|3-cocycle|three-cocycle|cocycle.*associator|associator|nonassoc|non-assoc|tetrahedron" ...
rg -n -i "finite-time|finite time|stage channel|rho_t|rho\(t\)|time step|stepped evolution|stepwise|stagewise|64-stage|64 stages|run_cycle|Run a full" ...
```

For absent/partial rows, I name the exact absence boundary in that row.

---

## 1. sigma_+ / sigma_- Convention For Ni Terrains

Status: FOUND, with a documented older disagreement.

Best current compact convention is Pit/left uses `sigma_-`, Source/right uses `sigma_+`.

LLM-GENERATED / COMPILED reference packet:

`system_v5/READ ONLY Reference Docs/terrain math.md:23`

> `| \(\sigma_-\) | \(\begin{pmatrix}0&0\\1&0\end{pmatrix}\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:24`

> `| \(\sigma_+\) | \(\begin{pmatrix}0&1\\0&0\end{pmatrix}\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:80`

> `| \`Ni / Pit\` | \(X_{Ni,L}(\rho)=\gamma_{Ni,L}D[\sigma_-](\rho)-i\,\varepsilon_{Ni,L}[H_L,\rho]\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:81`

> `| \`Ni / Source\` | \(X_{Ni,R}(\rho)=\gamma_{Ni,R}D[\sigma_+](\rho)-i\,\varepsilon_{Ni,R}[H_R,\rho]\) |`

A second compiled packet agrees:

`system_v5/READ ONLY Reference Docs/terrains.md:66`

> `| \`Ni / Pit\` | \(\displaystyle X_P^L(\rho_L)=\gamma_{P,L}D[\sigma_-](\rho_L)-i\,\varepsilon_{P,L}[H_L,\rho_L]\) |`

`system_v5/READ ONLY Reference Docs/terrains.md:74`

> `| \`Ni / Source\` | \(\displaystyle X_{So}^R(\rho_R)=\gamma_{So,R}D[\sigma_+](\rho_R)-i\,\varepsilon_{So,R}[H_R,\rho_R]\) |`

LLM-GENERATED Apple/raw working doc has a matching later pair-lock but also preserves an older candidate disagreement. The current useful resolution is the compact terrain packet above; the older candidate should be treated as historical drift, not silently erased.

Result: worked-out possibility on file is `Ni/Pit = D[sigma_-]`, `Ni/Source = D[sigma_+]`. The disagreement exists in older Apple material and should be flagged if that source is used.

---

## 2. Ne Terrain: Pure Hamiltonian vs Weak-Dissipator Variant

Status: FOUND. Both variants are worked out as named alternatives/surfaces.

Pure Hamiltonian compact terrain packet:

`system_v5/READ ONLY Reference Docs/terrain math.md:78`

> `| \`Ne / Vortex\` | \(X_{Ne,L}(\rho)=-i[H_L,\rho]\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:79`

> `| \`Ne / Spiral\` | \(X_{Ne,R}(\rho)=-i[H_R,\rho]\) |`

Weak-dissipator variant:

`system_v5/READ ONLY Reference Docs/terrains.md:65`

> `| \`Ne / Vortex\` | \(\displaystyle X_V^L(\rho_L)=-i[H_L,\rho_L]+\varepsilon_{V,L}\sum_k D[M^{V,L}_k](\rho_L)\) |`

`system_v5/READ ONLY Reference Docs/terrains.md:73`

> `| \`Ne / Spiral\` | \(\displaystyle X_S^R(\rho_R)=-i[H_R,\rho_R]+\varepsilon_{S,R}\sum_k D[M^{S,R}_k](\rho_R)\) |`

Source-grounded atlas explicitly classifies Ne as Hamiltonian-dominant with a small dissipator correction:

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:98`

> `| Se | **dissipative** | \`D\` dominant, small \`H\` correction |`

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:99`

> `| Ne | **Hamiltonian** | \`-is[H₀, ρ]\` dominant, small \`D\` correction |`

Result: both are on file. The safest wording is: pure Hamiltonian is the compact stripped terrain law; weak-dissipator is a Hamiltonian-dominant/open-system variant. No source I found collapses one as the only owner convention.

---

## 3. Si Projector Frames: m_L, m_R, P_j, Commuting Hamiltonian Frame

Status: FOUND.

Compact terrain packet:

`system_v5/READ ONLY Reference Docs/terrain math.md:82`

> `| \`Si / Hill\` | \(X_{Si,L}(\rho)=-i[\omega_L\,\hat m_L\!\cdot\!\vec\sigma,\rho]+\kappa_L\bigl(P_+^L\rho P_+^L+P_-^L\rho P_-^L-\rho\bigr)\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:83`

> `| \`Si / Citadel\` | \(X_{Si,R}(\rho)=-i[\omega_R\,\hat m_R\!\cdot\!\vec\sigma,\rho]+\kappa_R\bigl(P_+^R\rho P_+^R+P_-^R\rho P_-^R-\rho\bigr)\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:89`

> `| left projectors | \(P_\pm^L=\frac12(I\pm \hat m_L\!\cdot\!\vec\sigma)\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:90`

> `| right projectors | \(P_\pm^R=\frac12(I\pm \hat m_R\!\cdot\!\vec\sigma)\) |`

Stronger rosetta packet includes indexed projectors and commuting Hamiltonian frame:

`system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:57`

> `| left \(Si\) projectors | \(\displaystyle P_j^{H,L}=\frac12\left(I+\hat m_j^{H,L}\cdot\vec\sigma\right),\ P_j^{H,L}P_m^{H,L}=\delta_{jm}P_j^{H,L},\ \sum_jP_j^{H,L}=I,\ [K_L,P_j^{H,L}]=0\) |`

`system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:58`

> `| right \(Si\) projectors | \(\displaystyle P_j^{Ci,R}=\frac12\left(I+\hat m_j^{Ci,R}\cdot\vec\sigma\right),\ P_j^{Ci,R}P_m^{Ci,R}=\delta_{jm}P_j^{Ci,R},\ \sum_jP_j^{Ci,R}=I,\ [K_R,P_j^{Ci,R}]=0\) |`

Result: exact `m_L/m_R`, `P_j`, and commuting frame are worked out in compiled math docs.

---

## 4. Terrain Finite-Time Policy: Phi = e^{tX} vs Stepped Evolution

Status: FOUND/PARTIAL. Continuous semigroup policy exists with `t >= 0`; no fixed numeric terrain time `t` was found. Runtime stepped policy also exists.

Continuous channel policy:

`system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:71`

> `| stage channel | \(\displaystyle \Phi_\tau^s(t)=e^{tX_\tau^s},\qquad t\ge 0\) |`

Runtime stepped policy:

`system_v4/docs/generate_64_runtime_engine_table.py:3`

> `Generate the live 64-step runtime engine table from engine_core.py.`

`system_v4/docs/generate_64_runtime_engine_table.py:5`

> `This is intentionally separate from the 64 structural hexagram/state-space table.`

`system_v4/docs/generate_64_runtime_engine_table.py:7`

> `  2 engine types × 8 terrains × 4 operator slots = 64 runtime steps`

`system_v4/probes/engine_core.py:5`

> `The actual running engine. 8 macro-stages per type × 4 fixed operator`

`system_v4/probes/engine_core.py:6`

> `subcycles per macro-stage × 2 types = 64 operator applications.`

`system_v4/probes/engine_core.py:631`

> `        """Run a full 8-macro-stage cycle (32 operator applications).`

Search boundary: I searched for `finite-time`, `stage channel`, `rho(t)`, `time step`, `stepped evolution`, `stagewise`, `64-stage`, `run_cycle`. I found semigroup `t >= 0` and stepped runtime execution, but not a single owner-fixed numeric `t` convention for terrain channel duration.

Result: worked-out policy is dual: analytic `Phi_tau^s(t)=e^{tX_tau^s}` with open `t>=0`, plus executable 64-step stage/operator runtime.

---

## 5. Loop-Placement Binding: Terrain Law X With Y_in / Y_out, 16-Placement Table

Status: FOUND.

Compact 16 placement table:

`system_v5/READ ONLY Reference Docs/terrain math.md:122`

> `| 1 | \`Se / Funnel / inner\` | \((\dot\psi_L,\dot\rho_L)=\bigl(\Omega_{Se,L,\mathrm{in}}Y_{\mathrm{in}}\psi_L,\ X_{Se,L}(\rho_L)\bigr)\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:126`

> `| 5 | \`Ni / Pit / inner\` | \((\dot\psi_L,\dot\rho_L)=\bigl(\Omega_{Ni,L,\mathrm{in}}Y_{\mathrm{in}}\psi_L,\ X_{Ni,L}(\rho_L)\bigr)\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:134`

> `| 13 | \`Ni / Source / inner\` | \((\dot\psi_R,\dot\rho_R)=\bigl(\Omega_{Ni,R,\mathrm{in}}Y_{\mathrm{in}}\psi_R,\ X_{Ni,R}(\rho_R)\bigr)\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:137`

> `| 16 | \`Si / Citadel / outer\` | \((\dot\psi_R,\dot\rho_R)=\bigl(\Omega_{Si,R,\mathrm{out}}Y_{\mathrm{out}}\psi_R,\ X_{Si,R}(\rho_R)\bigr)\) |`

Explicit separation rule:

`system_v5/READ ONLY Reference Docs/terrain math.md:147`

> `This is the explicit terrain chart:`

`system_v5/READ ONLY Reference Docs/terrain math.md:148`

> `- the terrain is the generator \(X_{\tau,s}\)`

`system_v5/READ ONLY Reference Docs/terrain math.md:149`

> `- the loop is the spinor path field \(Y_{\mathrm{in}}\) or \(Y_{\mathrm{out}}\)`

`system_v5/READ ONLY Reference Docs/terrain math.md:150`

> `- a placement is the pair \((X_{\tau,s},Y_\ell)\)`

Strong rosetta version:

`system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:151`

> `\mathcal P_{s,\ell,\tau}=(\gamma_\ell^s,X_\tau^s,\Phi_\tau^s)`

`system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:183`

> `\{\text{16 placements}\}=\{\mathcal P_{s,\ell,\tau}:s\in\{L,R\},\ \ell\in\{f,b\},\ \tau\in\{Se,Ne,Ni,Si\}\}`

Result: 16-placement table and rule exist.

---

## 6. Per-Rung / Nested-Geometry Lift Across Nested Tori/Shells

Status: FOUND/PARTIAL. Single-shell formulas, nested-torus family, executable nested-torus engine, and owner demand for real nested Hopf-tori sims exist. Exact canonical multi-qubit/per-rung operator law is not fully closed.

Geometry formula:

`system_v5/READ ONLY Reference Docs/terrain math.md:30`

> `| torus family | \(T_\eta^s=\{\psi_s(\phi,\chi;\eta):\phi,\chi\in[0,2\pi)\}\subset S_s^3\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:31`

> `| connection | \(A=-i\,\psi_s^\dagger d\psi_s=d\phi+\cos(2\eta)\,d\chi\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:32`

> `| inner loop | \(\gamma_{\mathrm{in}}^s(u)=\psi_s(\phi_0+u,\chi_0;\eta_0)\) |`

`system_v5/READ ONLY Reference Docs/terrain math.md:33`

> `| outer loop | \(\gamma_{\mathrm{out}}^s(u)=\psi_s(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) |`

Live geometry table:

`system_v4/docs/QIT_ENGINE_GEOMETRY_ENTROPY_BRIDGE_MASTER_TABLE.md:57`

> `| 15 | geometry | nested Hopf tori | \`T_eta subset S^3\`, including Clifford torus \`T_{pi/4}\` | strong current torus realization and latitude organization inside \`S^3\` | yes | seat only | \`live geometry\` | \`AXIS0_GEOMETRIC_CONSTRAINT_MANIFOLD.md\`, \`axis0_full_constraint_manifold_guardrail_sim.py\`, \`sim_weyl_geometry_ladder_audit.py\` |`

Executable engine:

`system_v4/probes/engine_core.py:3`

> `Engine Core — Full 64-Step Geometric Engine on Nested Hopf Tori`

`system_v4/probes/engine_core.py:312`

> `    """Dual-loop geometric engine on nested Hopf tori with Weyl spinors.`

`system_v4/probes/engine_core.py:316`

> `    32 microsteps per engine type; 64 total across both types.`

OWNER-AUTHORED demand / framing:

`READ ONLY Legacy core_docs/a2_feed_high entropy doc/A0 new thread save before sim run.md:10387`

> `i think this is why i want to do mega sims. prove structure  in massive real sims. have actual nested hopf tori running my actual 2 engines through 64 stages. and run my holodeck with them. get real results.`

Compiled result claim:

`system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md:173`

> `| [test_engine_dual_loop_grammar.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/test_engine_dual_loop_grammar.py) and [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py) | PASS; live engine state carries explicit \`psi_L\`, \`psi_R\`, named nested-torus coordinates, and 32-step cycle execution per engine type | full left/right Weyl structure on nested Hopf tori exists in the executable engine |`

`system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md:174`

> `| [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py) | PASS; full 64-stage run executes with live axis deltas on Type 1 and Type 2 | the full geometry plus Weyl plus nested-torus engine path is real |`

Result: worked-out nested geometry and runtime exist. The precise per-rung/multi-qubit lift remains partial/open unless tied to a named executable/probe.

---

## 7. The 64 Grammar, Source Doc, And 64 -> 16 Degeneracy

Status: FOUND.

Script source/implementation:

`system_v4/docs/generate_64_runtime_engine_table.py:3`

> `Generate the live 64-step runtime engine table from engine_core.py.`

`system_v4/docs/generate_64_runtime_engine_table.py:5`

> `This is intentionally separate from the 64 structural hexagram/state-space table.`

`system_v4/docs/generate_64_runtime_engine_table.py:7`

> `  2 engine types × 8 terrains × 4 operator slots = 64 runtime steps`

`system_v4/docs/generate_64_runtime_engine_table.py:20`

> `from engine_core import GeometricEngine, StageControls, TERRAINS, OPERATORS  # noqa: E402`

Runtime order from implementation:

`system_v4/probes/engine_core.py:215`

> `# Type-1 (IN flux): outer=deductive on base, inner=inductive on fiber`

`system_v4/probes/engine_core.py:216`

> `# Type-2 (OUT flux): outer=inductive on fiber, inner=deductive on base`

`system_v4/probes/engine_core.py:219`

> `    1: [4, 6, 7, 5,   # outer deductive: Se_b→Ne_b→Ni_b→Si_b`

`system_v4/probes/engine_core.py:221`

> `    2: [0, 1, 3, 2,   # outer inductive:  Se_f→Si_f→Ni_f→Ne_f`

Atlas source grounding:

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:16`

> `## 0. SOURCE GROUNDING (owner docs only)`

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:20`

> `| \`Topology4\` math | \`core_docs/a1_refined_Ratchet Fuel/constraint ladder/Axis 1 2 topology math...md\` | owner math explicitly defines \`Se\`, \`Ne\`, \`Ni\`, \`Si\` as 4 topology / flow classes |`

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:21`

> `| pre-chirality stage structure | \`core_docs/a1_refined_Ratchet Fuel/constraint ladder/Axis 3 math Hopf fiber loop vs lifted base loop.md\` | owner math explicitly says \`8\` stages exist before left/right Weyl choice: \`4\` on Hopf fiber loop + \`4\` on lifted base loop |`

64 split and 16 chart relation:

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:268`

> `| Live runtime \`64\` | \`2 engines × 8 terrains × 4 operator slots\` | full signed-operator closure or hexagram equivalence |`

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:276`

> `Rows = terrains. Cols = signed operators. \`*\` = one of the 16 chart-locked macro-stage occupancies.`

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:314`

> `| Total microsteps | 64 (2 engines × 32) |`

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:320`

> `| Chart-locked macro-stages | 16 (starred cells in grid) |`

Open 64->16 equivalence warning:

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:367`

> `- Owner source surfaces currently contain two different 8-way constructions:`

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:368`

> `  - generalized-spinor \`8 = 4 topologies × 2 loop families\``

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:369`

> `  - Terrain8 \`= Topology4 × Flux2\``

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:370`

> `  This atlas correlates them, but does not prove they are the same object.`

Result: `generate_64_runtime_engine_table.py` implements `engine_core.py`, not a separate source doc. The 64 runtime, 16 chart-locked macro-stage occupancy, and correlation/open-equivalence warning are worked out.

---

## 8. Win/Lose As Functional Beyond Readout Grammar

Status: PARTIAL/FOUND. Named functionals exist as candidates/proxies; I did not find a promoted final `win/lose functional` doctrine.

QIT functionals:

`system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md:20`

> `| entropy | S(ρ) = -Tr(ρ log ρ) | von Neumann entropy |`

`system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md:22`

> `| coherent information | I_c(A⟩B)_ρ = -S(A\|B)_ρ = S(ρ_B) - S(ρ_AB) | directed coherent-information functional |`

`system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md:23`

> `| mutual information | I(A:B)_ρ = S(ρ_A) + S(ρ_B) - S(ρ_AB) | total correlation |`

Candidate kernel:

`system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md:143`

> `| generic kernel family | Φ₀(ρ_AB) | source-backed family, not one locked final formula |`

`system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md:144`

> `| preferred simple kernel | Φ₀(ρ_AB) = -S(A\|B)_ρ = I_c(A⟩B)_ρ | strongest current working candidate |`

`system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md:146`

> `| companion diagnostic | I(A:B)_ρ | source-backed companion quantity |`

Runtime proxies:

`system_v4/docs/QIT_ENGINE_GEOMETRY_ENTROPY_BRIDGE_MASTER_TABLE.md:66`

> `| 24 | entropy | runtime negentropy proxy | \`log(2) - S(rho)\` | executable local control / structure-gain proxy in the engine | yes | no | \`live proxy\` | \`engine_core.py\`, \`geometric_operators.py\` |`

`system_v4/docs/QIT_ENGINE_GEOMETRY_ENTROPY_BRIDGE_MASTER_TABLE.md:67`

> `| 25 | entropy | runtime entropy deltas | \`delta_phi\`, shell deltas, bookkeeping deltas | tracks local state-change effects through the engine | yes | no | \`live proxy\` | \`engine_core.py\`, \`axis0_full_spectrum_sim.py\` |`

Result: closest worked-out candidate is coherent information / conditional entropy, with mutual information and runtime negentropy/delta proxies. It remains a candidate/proxy layer, not a final win/lose functional.

---

## 9. Flux Ladder: Terrains, Holonomy/Flux Levels, cos(2eta), Shell Ladders

Status: FOUND/PARTIAL.

Holonomy / cos(2eta) carrier formula:

`system_v5/READ ONLY Reference Docs/terrain math.md:31`

> `| connection | \(A=-i\,\psi_s^\dagger d\psi_s=d\phi+\cos(2\eta)\,d\chi\) |`

`system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md:65`

> `| Hopf connection | 𝒜 = -i ψ† dψ = dφ + cos(2η) dχ | connection separating fiber from horizontal motion |`

`system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md:341`

> `| η torus latitude assignment | **resolved** — η is the Ax0 continuous field; $b_0 = \text{sgn}(\cos(2\eta))$; see \`AXIS_3_4_5_6_QIT_MATH.md\` |`

Flux2 / Berry sign:

`READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/AXIS_FOUNDATION_COMPANION_v1.4.md:141`

> `## 5) Terrain8 = Topology4 × Flux2 (the “same topology, different flow” claim)`

`READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/AXIS_FOUNDATION_COMPANION_v1.4.md:143`

> `### Flux2 (Axis‑3) = chirality / Berry‑flux sign`

`READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/AXIS_FOUNDATION_COMPANION_v1.4.md:145`

> `- approximate Berry flux ≈ ±6.28315 (≈ ±2π)`

`READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/AXIS_FOUNDATION_COMPANION_v1.4.md:149`

> `- **same base surface**, opposite flux sign.`

Weyl flux branch ladder:

`system_v5/READ ONLY Reference Docs/Weyl Flux.md:24`

> `| 6 | Torus stratification | \(T_\eta\subset S^3,\ \eta\in\{\pi/8,\pi/4,3\pi/8\}\) | nested torus seats | yes | seat-local vs seat-global later |`

`system_v5/READ ONLY Reference Docs/Weyl Flux.md:36`

> `| 18 | Flux family | \(\mathcal J=\{J_r,J_S,J_\theta,J_{AB},D_\chi,\dots\}\) | all candidate flux notions | yes | major branch |`

`system_v5/READ ONLY Reference Docs/Weyl Flux.md:42`

> `C \to M(C) \to \mathcal H \to S^3 \to T_\eta \to (\psi_L,\psi_R) \to (\rho_L,\rho_R) \to (\gamma_f,\gamma_b) \to \Delta\text{-surfaces} \to \mathcal J \to \text{flux placement}`

Result: flux ladder is worked out as a candidate family with holonomy/cos(2eta), Berry flux sign, and shell/torus seats. It is not final primitive doctrine.

---

## 10. Eight Stages In A Weyl-Spinor Picture: 4 Stages Per Loop x 2 Loops

Status: FOUND, including owner wording.

OWNER-AUTHORED direct quote:

`READ ONLY Legacy core_docs/ultra high entropy docs/txt/GPT 12_29 pro plan vs browser crashes.md.txt:6203`

> `and the 2 engines. both engines have a cooling and heating loop. the difference is the order. they are stacked in weyl spinors. lef and right spinors. so a left handed engine has one flow direction, and rtight handed has another flow direction. the left handed has the cooling loop on the outside loop and the heating on the inside loop. the right handed this is inversed. heating is outside loop. cooling insided loop`

Compiled owner-preservation doc:

`system_v4/docs/DUAL_LOOP_SPINOR_GRAMMAR.md:12`

> `- Two engine types are stacked on left/right Weyl spinor structure.`

`system_v4/docs/DUAL_LOOP_SPINOR_GRAMMAR.md:13`

> `- Both engine types have a cooling loop and a heating loop.`

`system_v4/docs/DUAL_LOOP_SPINOR_GRAMMAR.md:14`

> `- The difference is not "one heats, one cools"; the difference is the placement/order of those loops.`

`system_v4/docs/DUAL_LOOP_SPINOR_GRAMMAR.md:15`

> `- Left-handed engine:`

`system_v4/docs/DUAL_LOOP_SPINOR_GRAMMAR.md:16`

> `  - cooling outer`

`system_v4/docs/DUAL_LOOP_SPINOR_GRAMMAR.md:18`

> `- Right-handed engine:`

`system_v4/docs/DUAL_LOOP_SPINOR_GRAMMAR.md:19`

> `  - heating outer`

Source-grounded atlas:

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:21`

> `| pre-chirality stage structure | \`core_docs/a1_refined_Ratchet Fuel/constraint ladder/Axis 3 math Hopf fiber loop vs lifted base loop.md\` | owner math explicitly says \`8\` stages exist before left/right Weyl choice: \`4\` on Hopf fiber loop + \`4\` on lifted base loop |`

Runtime implementation:

`system_v4/probes/engine_core.py:311`

> `class GeometricEngine:`

`system_v4/probes/engine_core.py:312`

> `    """Dual-loop geometric engine on nested Hopf tori with Weyl spinors.`

`system_v4/probes/engine_core.py:314`

> `    Each engine type has 2 loops (outer/inner) with inverted heating/cooling`

`system_v4/probes/engine_core.py:315`

> `    roles across the two engine families. Each loop owns 4 terrain stages.`

Result: 4 stages per loop x 2 loops, left/right Weyl spinor stacking, and loop order inversion are worked out.

---

## 11. Q8 / Quaternion-Group Or Finite-Group Identification Of 8 Operators/Terrains

Status: PARTIAL. Discrete finite-group proxies exist; exact Q8-as-the-8-operators/terrains identification was not found.

Direct Q8/finite proxy mention:

`READ ONLY Legacy core_docs/ultra high entropy docs/txt/Gemini eisenhart model rebooted. lost most of thread. doing grok axiom loading. .txt:2844`

> `1. discrete finite-group spinor proxy (Q8 / Clifford)`

`READ ONLY Legacy core_docs/ultra high entropy docs/txt/Gemini eisenhart model rebooted. lost most of thread. doing grok axiom loading. .txt:2934`

> `* Option 1: Discrete Finite-Group Proxy (VALIDATED Proxy): Use the Pauli Group or Clifford Group on finite d. Sufficient for "Spinor-like" behavior without continuous geometry claims.`

`READ ONLY Legacy core_docs/ultra high entropy docs/txt/Gemini eisenhart model rebooted. lost most of thread. doing grok axiom loading. .txt:3187`

> `* Option 1 (Discrete Proxy): Finite Clifford group / Pauli group. Status: VALIDATED Proxy.`

Finite group / order-8 implementation surfaces found, but not exact 8 terrain/operator identity:

`system_v4/probes/sim_igt_4ring_operator_family.py:613`

> `                "T_R_non_commuting": "T∘R ≠ R∘T — generates dihedral D_4 of order 8",`

`system_v4/probes/sim_weyl_group_bc2_root_system.py:713`

> `            "Shell-local probe: Weyl group W(B2) = Dih4 (order 8) and B2 root system. "`

Searches run for exact identity:

```text
rg -n -i "Q8|quaternion group|finite group|8 operators|eight operators|operator.*Q8|terrain.*Q8|Pauli group|dihedral|Klein|Dih" ~/wiki/raw "system_v5/READ ONLY Reference Docs" "READ ONLY Legacy core_docs" ~/wiki/concepts ~/wiki/projects system_v4/docs system_v4/probes
```

Result: `Q8 / Clifford` and finite Pauli/Clifford/dihedral proxies are on file, but I did not find a worked-out owner/source claim that the 8 operators or 8 terrains are literally Q8, quaternion group, or one specific finite group. Treat exact finite-group identification as genuinely absent from the searched corpus; treat finite-group proxy as found.

---

## 12. Axis-4 vs Axis-6 Independence: Loop Order vs Precedence

Status: FOUND.

Axis 4 as order class:

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:888`

> `\Phi_D = e^{\tau_R \mathcal L_R} e^{\tau_C \mathcal L_C}`

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:891`

> `\Phi_I = e^{\tau_C \mathcal L_C} e^{\tau_R \mathcal L_R}`

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:913`

> `So \`Axis 4\` is the **order class of two non-commuting generators**.`

Axis 6 as action side / precedence:

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:996`

> `L_A(\rho)=A\rho`

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:999`

> `R_A(\rho)=\rho A`

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:1023`

> `So \`Axis 6\` is the **sidedness / precedence class**.`

Combined separation:

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:1046`

> `\text{Axis 5 chooses } \mathcal L_G \text{ or } \mathcal L_S`

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:1050`

> `\text{Axis 6 chooses } L_A \text{ or } R_A`

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:1054`

> `\text{Axis 4 chooses the order class }`

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:1063`

> `\text{Axis 4} = \text{order class}`

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:1069`

> `\text{Axis 6} = \text{action side}`

Atlas grounding agrees:

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:301`

> `| Ax4 | QIT ordering class: inductive vs deductive; chart correlates this to \`FeTi / TeFi\` | strongest source-grounded operator axis |`

`system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:303`

> `| Ax6 | action / precedence orientation: operator first vs terrain first (\`UP / DOWN\`) | partially source-grounded; chart binding is clearer than the source-side closure |`

Result: worked-out separation exists: Axis 4 is order class; Axis 6 is action side / precedence orientation.

---

## 13. Split Octonions / Split G2

Status: FOUND for split G2 branch; PARTIAL for split octonions specifically.

Audit/router preserving G2 variant family:

`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/octonion-g2-sedenion-carrier-geometry-audit-2026-06-08.md:20`

> `The octonion / \`G2\` / sedenion tower is not a late footnote. It is an early carrier-geometry frontier, behind the \`M(C)\` gate and canon algebra artifact, and it should be folded into Stage 4 same-carrier geometry work one bounded packet at a time.`

`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/octonion-g2-sedenion-carrier-geometry-audit-2026-06-08.md:62`

> `` `G2` is the leading candidate family, not the declared answer. Keep these variants separate until bounded controls exclude them: ``

`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/octonion-g2-sedenion-carrier-geometry-audit-2026-06-08.md:66`

> `- compact \`G2\` versus split \`G2(2)\` real-form branch.`

Checked envelope list:

`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/octonion-g2-sedenion-carrier-geometry-audit-2026-06-08.md:81`

> `| \`G2\` automorphism xhigh | \`system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_envelope_results.json\` | \`validate_three_engine_sim_result.py --require-pytorch\` ok; \`--strict-source-backed\` ok |`

`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/octonion-g2-sedenion-carrier-geometry-audit-2026-06-08.md:87`

> `| \`Spin(7)/G2\` calibration forms | \`system_v5/ops/formal_scouts/results/foundation_foundation_r6_spin7_g2_calibration_forms_envelope_results.json\` | \`--require-pytorch\` ok; \`--strict-source-backed\` ok |`

Searches run for split octonion/split G2:

```text
rg -n -i "split octonion|split-octonion|split G2|split-G2|split real form|octonion|sedenion|Fano|Spin\(7\)|\bG2\b" ...
```

Result: split `G2(2)` real-form branch is explicitly on file. I did not find an equally explicit “split octonion” worked-out source in the searched hits, but split G2 satisfies the target’s split-G2 half and should be preserved as a live variant, not flattened into compact G2.

---

## 14. Associator Cocycle / Flux-Through-Tetrahedron

Status: GENUINELY ABSENT for the exact connection; PARTIAL adjacent surfaces found.

Associator/nonassociativity evidence exists:

`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/nonassociativity-carrier-layer-status-2026-06-07.md:31`

> `| Associator | \`foundation_r3_associator_xhigh_envelope_results.json\` validator \`ok=true\`; prior strict panel and fresh source audit clean | genuine R3 bracketing scratch evidence: \`H\` has zero associator, \`O\` has nonzero associator |`

`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/nonassociativity-carrier-layer-status-2026-06-07.md:41`

> `Associator: H max norm 0.0; O max norm 2.0; O witness basis [1,2,4]; z3/cvc5 O-all-zero UNSAT -> erased SAT.`

`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/nonassociativity-carrier-layer-status-2026-06-07.md:76`

> `Non-associativity is a natural expression of a=a iff a~b applied to grouping.`

`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/nonassociativity-carrier-layer-status-2026-06-07.md:77`

> `Current receipts place it as R3 carrier/bracketing pressure.`

Flux family exists separately:

`system_v5/READ ONLY Reference Docs/Weyl Flux.md:36`

> `| 18 | Flux family | \(\mathcal J=\{J_r,J_S,J_\theta,J_{AB},D_\chi,\dots\}\) | all candidate flux notions | yes | major branch |`

Tetrahedron mentions exist in other math/probe contexts, but I did not find the exact owner/source connection `associator cocycle = flux through tetrahedron`.

Searches run for exact connection:

```text
rg -n -i "associator.*flux|flux.*associator|tetrahedron.*flux|flux.*tetrahedron|3-cocycle|three-cocycle|cocycle.*associator|associator|nonassoc|non-assoc|tetrahedron" ~/wiki/raw "system_v5/READ ONLY Reference Docs" "READ ONLY Legacy core_docs" ~/wiki/concepts ~/wiki/projects system_v4/docs system_v4/probes
```

Result: exact associator/flux-through-tetrahedron note is genuinely absent in the searched corpus. Adjacent worked-out pieces exist: associator/nonassociativity receipts, flux family candidates, 3-cocycle/gerbe probes, and tetrahedron/Weyl-chamber/simplex probes. Do not merge them without a new source or sim.

---

## End Summary Table

| target | FOUND/PARTIAL/ABSENT | best source | one-line content |
|---|---|---|---|
| 1. sigma_+/sigma_- for Ni | FOUND | `system_v5/READ ONLY Reference Docs/terrain math.md:80-81` | Current compact convention: Ni/Pit uses `D[sigma_-]`; Ni/Source uses `D[sigma_+]`; older Apple candidate drift exists. |
| 2. Ne Hamiltonian vs weak dissipator | FOUND | `terrain math.md:78-79`; `terrains.md:65,73`; `ENGINE_64_SCHEDULE_ATLAS.md:99` | Both pure Hamiltonian and Hamiltonian-dominant plus small dissipator variants are on file. |
| 3. Si projector frames | FOUND | `terrain rosetta strong math.md:57-58` | `P_j = 1/2(I + m_j dot sigma)`, projector algebra, and `[K,P_j]=0` commuting frame exist. |
| 4. finite-time policy | FOUND/PARTIAL | `terrain rosetta strong math.md:71`; `engine_core.py:5-6` | Continuous `Phi=e^{tX}, t>=0` exists; runtime uses fixed 64 operator applications; no fixed numeric terrain `t` found. |
| 5. loop-placement binding | FOUND | `terrain math.md:122-150`; `terrain rosetta strong math.md:151-183` | 16 placements and rule `(terrain generator X, loop path Y/gamma)` are explicit. |
| 6. per-rung/nested geometry lift | FOUND/PARTIAL | `engine_core.py:3,312-316`; `A0 new thread save before sim run.md:10387` | Nested Hopf tori plus 2 engines/64 stages are owner-demanded and executable; full multi-rung law not fully closed. |
| 7. 64 grammar/source/64->16 | FOUND | `generate_64_runtime_engine_table.py:3-7,20`; `ENGINE_64_SCHEDULE_ATLAS.md:268-320,367-370` | Script implements `engine_core.py`; 64 runtime, 16 chart-locked macro-stages, and unresolved 8-way correlation are documented. |
| 8. win/lose functional | PARTIAL | `AXIS_0_1_2_QIT_MATH.md:20-23,143-146`; `QIT_ENGINE_GEOMETRY_ENTROPY_BRIDGE_MASTER_TABLE.md:66-67` | Coherent information/conditional entropy, mutual information, negentropy, and deltas are candidates/proxies; no promoted final win/lose functional found. |
| 9. flux ladder | FOUND/PARTIAL | `AXIS_FOUNDATION_COMPANION_v1.4.md:141-149`; `Weyl Flux.md:24,36,42`; `AXIS_0_1_2_QIT_MATH.md:65,341` | Terrain8 = Topology4 x Flux2, Berry sign, cos(2eta), torus seats, and flux-family branches are on file. |
| 10. 8 stages in Weyl spinor | FOUND | `GPT 12_29 pro plan vs browser crashes.md.txt:6203`; `DUAL_LOOP_SPINOR_GRAMMAR.md:12-20`; `engine_core.py:312-316` | Owner wording and runtime agree: two Weyl-stacked engine types, two loops, four terrain stages per loop, inverted loop placement/order. |
| 11. Q8/quaternion/finite group | PARTIAL | `Gemini eisenhart model rebooted...txt:2844,2934,3187`; `sim_igt_4ring_operator_family.py:613` | Q8/Clifford and finite Pauli/dihedral proxies exist; exact finite-group identity of the 8 operators/terrains was not found. |
| 12. Axis-4 vs Axis-6 independence | FOUND | `apple axes terrain operator math.md:888-913,996-1023,1046-1069`; `ENGINE_64_SCHEDULE_ATLAS.md:301,303` | Axis 4 is order class; Axis 6 is action side / precedence orientation. |
| 13. split octonions / split G2 | FOUND/PARTIAL | `octonion-g2-sedenion-carrier-geometry-audit-2026-06-08.md:62-67,81-90,162` | Split `G2(2)` real-form branch is explicitly preserved; exact split-octonion note not found. |
| 14. associator cocycle / flux-through-tetrahedron | ABSENT exact / PARTIAL adjacent | `nonassociativity-carrier-layer-status-2026-06-07.md:31,41,76-78`; `Weyl Flux.md:36` | Associator and flux families exist separately; exact associator-as-flux-through-tetrahedron connection was not found after targeted searches. |
