# Thermodynamics Lane Audit

Repo: `Joshua-Eisenhart/Codex-Ratchet`
Anchor commit: `c480a4a6154a181d3ff9ec1e8dbf679fcc7b3631`
Audit date: `2026-04-10`
Branch: `pro/deepresearch-thermo-lane-20260410`

Repo files read first:
- `new docs/references/STOCHASTIC_THERMODYNAMICS_REFERENCE.md`
- `new docs/AXIS_AND_ENTROPY_REFERENCE.md`
- `new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md`
- `system_v4/probes/a2_state/sim_results/qit_szilard_landauer_cycle_results.json`
- `system_v4/probes/a2_state/sim_results/qit_strong_coupling_landauer_results.json`

Guardrails used:
- separate bookkeeping from ontology
- do not inflate into Carnot unless justified
- keep the repo's entropy-late discipline intact

## 1. What the repo currently earns

- A real **finite bookkeeping lane** for Landauer/Szilard-style accounting. The strongest claim supported by the current repo is a closed finite-carrier demonstration that measurement/feedback work extraction is matched by reset cost.
- A real **strong-coupling caution lane**. The strong-coupling results support the narrower claim that naive reduced-state bookkeeping can appear to break Clausius/Landauer-style bounds when interaction and correlation terms are dropped, while fuller joint bookkeeping restores consistency.
- Useful **entropy-late governance**. The axis/admission references help keep entropy as a derived bookkeeping object instead of treating it as a free ontological engine substance.
- The repo is strongest when presented as a program of **small exact accounting rows**, not as a broad thermodynamic completion.

## 2. What is still only support or analogy

- Any move from an internal entropy decrease to a literal Joule cost is still analogy unless the repo specifies a physical memory, a reset map, a bath at temperature `T`, and a logically irreversible operation.
- Any use of cycle terms like compression, exhaust, battery, or voltage is still analogy unless explicit work/heat definitions and physical carriers are given.
- `Phi` / negentropy style scores are still internal compression diagnostics unless tied to a standard thermodynamic potential and a reference equilibrium.
- Demon-style measurement language is still partly analogical if it treats measurement gain as just entropy reduction of the measured system. The more literature-grounded quantity is system-memory correlation / mutual information.
- Carnot-style language remains analogy unless explicit reservoirs and explicit heat/work flows are defined.

## 3. Best external sources for:

### Landauer
- Landauer (1961), *Irreversibility and Heat Generation in the Computing Process*  
  https://cir.nii.ac.jp/crid/1361699993435029376
- Bérut et al. (2012), experimental verification of Landauer’s principle  
  https://www.nature.com/articles/nature10872
- Reeb & Wolf (2014), finite-size corrections to Landauer  
  https://portal.fis.tum.de/en/publications/an-improved-landauer-principle-with-finite-size-corrections/
- Faist et al. (2015), minimal work cost of information processing  
  https://www.nature.com/articles/ncomms8669

### strong-coupling corrections
- Hilt et al. (2011), *Landauer’s principle in the quantum regime*  
  https://journals.aps.org/pre/abstract/10.1103/PhysRevE.83.030102
- *Hamiltonian of mean force for damped quantum systems*  
  https://journals.aps.org/pre/abstract/10.1103/PhysRevE.84.031110
- *Fluctuation Theorem for Arbitrary Open Quantum Systems*  
  https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.102.210401
- *Stochastic thermodynamics in the strong coupling regime: an unambiguous approach based on coarse graining over the system-environment boundary*  
  https://journals.aps.org/pre/abstract/10.1103/PhysRevE.95.062101
- *Stochastic and Macroscopic Thermodynamics of Strongly Coupled Systems*  
  https://journals.aps.org/prx/abstract/10.1103/PhysRevX.7.011008

### stochastic thermodynamics
- Seifert (2012), review  
  https://pubmed.ncbi.nlm.nih.gov/23168354/
- Sekimoto (1998), *Langevin Equation and Thermodynamics*  
  https://academic.oup.com/ptps/article/doi/10.1143/PTPS.130.17/1842313
- Jarzynski (1997)  
  https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.78.2690
- Crooks (1999)  
  https://journals.aps.org/pre/abstract/10.1103/PhysRevE.60.2721

### measurement and feedback control
- Sagawa & Ueda (2010), generalized Jarzynski equality under feedback  
  https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.104.090602
- Sagawa & Ueda (2009), minimal energy cost of measurement and erasure  
  https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.102.250602
- *Thermodynamics of information*  
  https://www.nature.com/articles/nphys3230
- Ito & Sagawa (2013), information thermodynamics on causal networks  
  https://pubmed.ncbi.nlm.nih.gov/24237500/

## 4. Best next bounded sim/doc lane

Best next bounded lane: a **stochastic-thermodynamics erasure lane** built around a double-well memory with explicit trajectory bookkeeping.

Recommended deliverables:
- `system_v4/probes/sim_stoch_doublewell_landauer_erasure.py`
- `system_v4/probes/a2_state/sim_results/stoch_doublewell_landauer_erasure_results.json`
- `new docs/references/STOCH_ERASURE_LANE_SPEC.md`

Minimal scope:
- overdamped Langevin dynamics
- one thermal bath at fixed `T`
- a controllable double-well one-bit memory
- a family of erasure schedules from fast to quasi-static
- trajectory-level work/heat bookkeeping
- output: mean dissipated heat vs protocol duration, erasure success, and approach toward `k_B T ln 2` in the quasi-static limit

Why this lane: it upgrades the repo from information-only toy rows into explicit trajectory heat/work accounting without forcing a premature jump into Carnot or broad engine claims.

## 5. Dangerous overclaims to avoid

- Do not call an abstract entropy drop a physical Landauer erasure without specifying memory, reset map, bath, and logical irreversibility.
- Do not say strong coupling violates Landauer. Safer: naive reduced-state bookkeeping can appear to violate the bound; fuller composite accounting restores consistency.
- Do not call finite toy rows Carnot-like unless reservoirs and explicit heat/work flows are present.
- Do not equate `Phi` / negentropy with free energy or work capacity by default.
- Do not treat measurement gain as only system entropy reduction; the literature centers system-memory correlations and mutual information.

## 6. Suggested wording upgrades grounded in literature

### Landauer wording
> If a physical controller or memory is reset each cycle, and that reset reduces the memory’s information content by `ΔH_erase` bits while coupled to a bath at temperature `T`, then the reversible lower bound on dissipated heat is `Q_min >= k_B T ln 2 · ΔH_erase`. Finite-time and non-ideal implementations dissipate more.

### Strong-coupling wording
> At strong system-bath coupling, the reduced state of the system need not be Gibbs with respect to the bare system Hamiltonian. Naive reduced-state heat/entropy bookkeeping can therefore appear to violate Clausius/Landauer-style inequalities. Composite bookkeeping that retains interaction and correlation contributions restores a generalized second-law-consistent accounting.

### Measurement / feedback wording
> The measurement step is modeled as creating correlations between system and memory. The feedback step converts those correlations into useful work subject to information-theoretic bounds. The reset step closes the cycle by paying a Landauer-type cost to restore the memory.

### Phi / negentropy wording
> `Phi` is used here as an internal structure/compression diagnostic relative to a chosen state-space reference. It is not automatically a thermodynamic free energy or available-work quantity unless a bath model, control protocol, and reference equilibrium are explicitly specified.

### Anti-Carnot guardrail wording
> Carnot bounds apply to engines operating between reservoirs with well-defined heat flows. The finite-carrier bookkeeping rows in this repo do not claim Carnot-relevant efficiency unless `Q_in`, `Q_out`, and `W` are explicitly defined within an explicit reservoir model.

## Bottom line

The repo’s thermodynamics lane is strongest when framed as a careful finite bookkeeping program aligned with Landauer, strong-coupling corrections, and information-thermodynamics literature. The strongest next addition is not a broader engine claim. It is a bounded stochastic-erasure lane with explicit heat/work trajectory accounting and a short companion doc that keeps bookkeeping, ontology, and scope sharply separated.
