# Hardening changelog — 2026-07-01 (external audit pass, claude.ai session)
All changes below are audit-inserted; sync knowingly. Sims' mathematical
content untouched except H-3 (path containment only).

H-1  ADDED    CLAUDE.md — agent contract (hard rules, withdrawn-claims list,
              honest-failure guards, V/W anti-conflation, open-decision fence).
H-2  FIXED    spec_and_reports/ORIENTATION.md had diverged from root
              ORIENTATION.md (two different orientations = agent trap).
              Replaced with a pointer stub; root is canonical.
H-3  FIXED    manifold_build_ladder.py wrote 4 JSONs into the caller's CWD.
              Now writes to sims_and_scripts/out/ (path containment only; no
              math change; verified identical stdout).
H-4  ADDED    run_all.py — deterministic harness: 20 sims, per-sim headline
              invariants with explicit tolerances, honest-failure guards
              (Axis-0 doctrine must stay False; 11/64 collapse must stay 11),
              withdrawn-claim guards ("no linear law" string asserted), JAX
              graceful skip, exit 0/1, writes run_all_report.json.
H-5  ADDED    requirements.txt (numpy/scipy/sympy required, jax optional,
              matplotlib deliberately excluded).
H-6  EDITED   spec §7g: inline AUDIT FLAG on the two-64s tension marked
              PENDING OWNER DECISION (guards against silent harmonization).
H-7  ADDED    spec_and_reports/PURE_MATH_CORE.md — the de-jargoned P1–P11
              proposition ledger from the audit session (referenced by
              CLAUDE.md as the fast label-free entry point).

H-8  ADOPTED  spec v29 (adds §7v, the χ₂ open-path instrument) from the other
              thread's lineage; re-applied H-6 (the two-64s flag, absent in
              that lineage).
H-9  EDITED   spec §7v: AUDIT FLAG with the fourth audit's grade correction —
              (i) V-vs-V* is the K-mirror pair, not the a2 pair (χ₂ responds
              to all three pairs; not charge-specific); (ii) the terrain-level
              decisive test fails (2/8 / 6/8, ε-contaminated phases). §7m
              remains admissible-candidate.
H-10 ADDED    sims_and_scripts/chi2_decisive_test_sim.py — instrument +
              charge-specificity tests + the §7m decisive test, deterministic.
H-11 ADDED    run_all.py entry for H-10 (guards the 2/8 / 6/8 result and the
              non-specificity finding against silent "fixes").
H-12 EDITED   CLAUDE.md: §7m status guard and χ₂ overclaim guard added to the
              withdrawn/hardened-claims list; open-items list updated to the
              sharpened form (ε-even a2-specific functional).

# Fourth pass — 2026-07-01 (this thread: fable-v2 merge + §7w resolution)
Base = fable's v2 zip (H-8..H-12: adopts §7v, adds the fourth-audit grade
correction and chi2_decisive_test_sim.py). This pass merged that base with the
other thread's §7v instrument and then RESOLVED the sharpened open item.
Version-label correction (per reviewer): the earlier M-1 note in the prior
bundle mislabelled the merge as spec v28->v29 / rosetta v11->v12; the saved
artifacts were spec v30 / rosetta v13. This pass produces spec (fable-v2 base
+ §7w) and rosetta with a fourth audit-log entry.

MP-1 RESTORED  chi2_openpath_readout_sim.py + chi2_openpath_readout.png (the §7v
               instrument; fable's v2 kept only the decisive-test sim). Added a
               correction header: property D is demonstrated on the K-mirror
               pair (V vs V*), not the a2 pair; math unchanged.
MP-2 ADDED     spec §7w — the terrain-level a2 item RESOLVED as a layer
               statement (no-go with a located home): eps-symmetrization is
               achievable but the eps-even functional reads a1 not a2; a2 is
               exact at the operator layer (||W.Ti.W-Te||=9e-16) and does not
               descend to terrain generators (residual ~2.05).
MP-3 ADDED     sims_and_scripts/eps_even_a2_specificity_sim.py (the no-go,
               deterministic) + eps_even_a2_specificity.png.
MP-4 EDITED    spec §7n bridge-status reconciled: chi2 = earned sector meter,
               not a2-specific; parity reads end-to-end at the operator layer.
MP-5 EDITED    PURE_MATH_CORE P10 -> earned-as-sector-meter + a2 layer no-go;
               rosetta row + open queue updated; CLAUDE.md fence: terrain-a2
               and charge-specific-chi2 items moved from "open construction" to
               "resolved no-go (§7w)"; P9 admissibility named as the open item.
MP-6 ADDED     run_all.py guards for the instrument sim and the eps-even no-go.
MP-7 ADDED     rosetta _audit_log_2026-07-01_fourth (fourth audit + §7w).
Honest-failure and withdrawn-claim guards from H-4/H-11 all still hold.


# Unified bundle — 2026-07-01 (reference docs added)
UB-1 ADDED  reference_docs/ — key source material from the repos, so the bundle
            is self-contained for a fresh thread with no repo access:
            - engine_math/ (engine-math-reference, igt-pattern-explicit-math,
              TERRAIN_LAW_LEDGER, QIT four-operator signed math, 64-schedule atlas)
            - science_method/ (recursive-science-methodology, leviathan-science-
              method-qit-engine-crosswalk, leviathan-v3.2 raw source) — the
              bidirectional engine<->science-process mapping; deductive=inductive
              reversed = the spec's UEUE/EUEU loop (§7l) / N01 order-sensitivity.
            - holodeck/ (doctrine, projective memory model, QIT-FEP-Leviathan
              integration, prediction-first processing) — the perception/memory lane.
            reference_docs/README.md maps each file to the spec sections it sources.
            These are SOURCE/SUPPORT tier (candidate/witness per their own front-
            matter), not audited spec claims.
UB-2 EDITED ORIENTATION.md LAYOUT section: added reference_docs/ + the hardening
            infra files (CLAUDE.md, run_all.py, requirements.txt, CHANGELOG).
Harness unchanged: 21 pass / 0 fail / 2 skip (jax) -> GREEN.

H-13 FIXED    run_all.py signed-zero brittleness: chi2_openpath check expected
              "closed=+0.0000" but numpy builds differ on signed zero of
              -arg(); check is now value-based (|closed| <= 1e-9).
H-14 ADDED    engines/ lane: oracle_targets.py (numpy contract ->
              targets.json), jax_engine.py, torch_engine.py, julia_engine.jl,
              validate_engines.py, README_LAPTOP.md. Verified here: oracle +
              JAX + torch agree to 1e-6 on all 16 stages (three independent
              numerical routes). Julia authored, first run pending on laptop.
H-15 FINDING  (P12) 16/16 N01 order sensitivity is load-bearing on the
              coherent axis: with H0 on the z-axis the four Fe stages commute
              EXACTLY with their terrains (phase covariance) -> 12/16. The
              bundle contained two axis conventions across sims; they are not
              interchangeable. Guarded by axis_loadbearing_n01_sim.py (H-16).
H-16 ADDED    sims_and_scripts/axis_loadbearing_n01_sim.py + run_all entry.
H-17 EDITED   CLAUDE.md: engines lane in the map; P12 axis rule added.
H-18 NOTE     torch installs with a transient "Bus error" message in this
              sandbox but imports and runs correctly (2.12.1); harmless.


# Upgrade pass — 2026-07-01 (O1 derived + laptop package + engines in harness)
UP-1 DERIVED  O1 (was the top open item): "exactly 2 native operators per terrain"
              is now DERIVED from C2, not labelled. admissibility_two_operator_sim.py.
              Same-basis (D,H) pairs commute exactly (order-gap 0) -> C2 forbids;
              2 cross-basis survivors are Axis-2 (W) conjugates; terrain frame sign
              selects one. Added to run_all.py SUITE (23rd sim). PASS.
UP-2 WIRED    engines/ cross-substrate lane into run_all.py: run_engines_lane() runs
              the numpy RK4 oracle, any importable substrate engine (jax/torch), then
              validate_engines.py; asserts GREEN. Verified PASS with jax present
              (oracle vs jax agree), SKIP when no substrate engine importable.
UP-3 ADDED    LAPTOP_RUN.sh -- one-command setup+verify for a local laptop: makes a
              .venv, installs numpy/scipy/sympy (+ jax/torch unless --fast), runs the
              full harness incl. engines lane, and runs the Julia route if julia is on
              PATH. Exit 0 = GREEN. Added LAPTOP_README.md.
UP-4 EDITED   CLAUDE.md: P9/O1 marked CLOSED; fixed a stale "≈2.05" residual to the
              real per-pair values 2.112 / 1.990. MODEL_LAYER_LEDGER 5.6 -> EARNED.
Harness now: 23 pass / 0 fail / N skip -> GREEN (engines lane PASS when jax/torch present).


# O3 done — 3-qubit contract (2026-07-01)
UP-5 SCALED   O3 (was open): the 16-stage engine contract lifted to 3 qubits (C^8).
              engines/oracle_targets_3q.py (numpy RK4), jax_engine_3q.py (exact 64x64
              superoperator expm), validate_engines_3q.py. Readout = 63-dim Pauli-
              expectation vector. GENUINELY 3q: ZZ chain coupling makes evolution
              non-factorizing (max negativity 0.038>0); 16 stages distinct (min pairwise
              0.174); 8/8 fusion + 16/16 order gaps preserved. Oracle vs JAX agree ~1e-12
              on all 16 stages in 63-dim space. Wired into run_all engines lane
              (reports "1q GREEN; 3q GREEN"). Julia/torch 3q engines: next (schema mirrors
              the 1q ones).
UP-6 NORMALIZED  wiki layout: all 25 sims consolidated under sims_and_scripts/, engines/
              lane pushed (was absent on wiki), 20 flat root duplicates removed. Public
              repo now mirrors the zip layout.


# Full-usage pass — 2026-07-01 (3 substrates verified in-house + info-processing)
UP-7 VERIFIED  PyTorch run IN-HOUSE for the first time (torch 2.12.1, CPU, complex128):
               both 1q and 3q torch engines execute here and validate against the numpy
               oracle. No "Bus error" -> D2 was fable's environment, not the code. Three
               independent routes now confirmed at BOTH scales: numpy RK4 oracle, JAX exact
               expm, PyTorch matrix_exp. 3q agreement ~1e-12 across all 16 stages (63-dim
               Pauli). Julia remains the 4th route (laptop-only; no runtime in sandbox).
UP-8 ADDED     torch_engine_3q.py (3q PyTorch route). validate_engines_3q now GREEN on jax+torch.
UP-9 NEW SIM   info_processing_sim.py -- DOES the engine process information? Each stage as a
               CPTP channel on a message qubit entangled with a reference. Result: all 16 are
               open-system processors (I_coh<0); entropy injection spans 0.006..0.991 bits
               (distinct info work); the Choi matrix separates all 16 (min 0.277); scalar
               entropy metrics collapse 5 Weyl-mirror pairs (two-sector signature at the info
               layer). figures/info_processing.png. Added to harness (now 25 pass).


# Memory layer — 2026-07-01 (spinor + holodeck precursor)
UP-10 NEW SIM  memory_sim.py -- does the engine STORE/RECALL? Three mechanisms:
               (1) memory cells: only projective-Si terrains t3/t7 retain a written z-bit
               (margin 0.71/0.53 after 8 holds); dissipative/depolarizing erase to ~0.
               (2) spinor phase memory: 360deg->sign -1, 720deg->+1, invisible at rho level.
               (3) memory<->computation tradeoff: bit margin 0.00 (tau=1) -> 0.43 (tau=0.02);
               compute hard=forget, compute gently=remember. figures/memory.png. Added to
               harness (26 pass). Model ledger Layer 12; O6 holodeck now PARTIAL (precursor built).


# Learning layer — 2026-07-01 (holodeck prediction-first / active inference)
UP-11 NEW SIM  holodeck_sim.py -- prediction-first active-inference loop in PURE QIT (free
               energy = Umegaki relative entropy, no classical math). (1) prediction loop
               minimizes F 2.62->0 monotone; (2) stationary learning cuts surprise 99%
               (belief stored in Hill projective cell); (3) single-cell capacity boundary:
               learns k=1, fails k>=2 (~0.4 bits residual); (4) 3-qubit register learns
               k=2,3,4 to <0.05 bits -> independent derived reason for the 3-qubit floor.
               figures/holodeck.png. Added to harness (27 pass). Layer 13; O6 now MOSTLY DONE.


# Leviathan bridge — 2026-07-01 (world-engine output interface, stub)
UP-12 NEW SIM  lev_bridge_sim.py + QIT_LEV_BRIDGE_SPEC.md -- the engine as a signal source a
               Leviathan graph consumes. Defines the per-tick stream contract {belief_bloch,
               surprise_bits, fe_gradient} and the LevBridge adapter (.tick/.subscribe). Proven:
               surprise is near-zero on a stable world, spikes 1.50 on a regime shift, decays as
               the engine relearns -- a usable control signal for Lev attention/action. Pure QIT.
               Deliberately NOT coupled to live Lev internals yet (foundations-up). Added to
               harness (28 pass). Layer 14; O6 bridge stub done, live wiring + action edge ahead.


# Action half / closed loop — 2026-07-01 (running world-engine)
UP-13 NEW SIM  agent_loop_sim.py -- the CLOSED active-inference loop. Adds the ACTION half:
               pick the action minimizing EXPECTED free energy G = risk - epistemic_value
               (pure QIT). Perception+action closed: from a world opposite the goal (goal_dist
               1.37) the agent drives it to preference (goal_dist <0.01, world_z +0.85) and holds
               it -- it ACTS to make the world match its model. figures/agent_loop.png. Added to
               harness (29 pass). Layer 13.5. Reverse edge Layer 14 deferred, done engine-side.


# Julia substrate live in-house — 2026-07-02 (4th route; a real finding)
UP-14 VERIFIED Installed the Julia 1.10.5 runtime IN THE SANDBOX and ran julia_engine.jl +
               julia_engine_3q.jl (the 4th independent route, the user's aligned choice).
               FINDING (CLAUDE.md rule 1): first run DISAGREED with the oracle (1q min-dist
               0.096) -- Julia is column-major, so reshape(transpose(rho),4) mismatched numpy's
               column-stacking vec. Fixed to reshape(rho,4)/reshape(v,2,2). After the fix all
               four substrates agree: 1q min-dist 0.0276, 3q worst pvec dev 9.89e-13 on C^8.
               Made the Julia engines DEPENDENCY-FREE (hand-rolled JSON, no registry / no ] add).
               Wired both into run_all engines lane (reports "...+julia GREEN" when julia is on
               PATH). Julia runtime archived as an artifact so it survives workspace sweeps.


# Formal proof lane — 2026-07-02 (laws FORCED, not fitted; aligned tools installed)
UP-15 TOOLS    Read the 3-engine dependency contract and installed the aligned Python-lane
               tools it names: z3-solver + cvc5 (SMT proof pair), qutip (QIT library), plus
               quimb/cotengra/diffrax/optax/sympy/mpmath. Julia package registry remains
               blocked by sandbox TLS interception (pkg.julialang.org connects but the
               re-signed cert is unparseable by Julia's downloader) -> Julia engine stays
               dependency-free (LinearAlgebra); the strict-carrier Julia packages are a
               laptop-side TODO.
UP-16 NEW SIM  axis_laws_dual_proof.py -- the axis laws are FORCED (SMT), proven in Z3 AND
               cvc5 with agreement, WITH an erased control that flips the verdict (drop the Ni
               constraint -> XOR uniqueness breaks). Proves: (1) Axis-0=Axis-1 XOR Axis-2 is the
               UNIQUE boolean law and IS xor; (2) b6=-b0*b3 uniquely bilinear, no linear law
               fits. Satisfies the contract's "z3 & cvc5 agree with erased controls that flip".
UP-17 NEW SIM  terrain_qutip_crosscheck.py -- QuTiP (standard Lindblad) reproduces the hand-
               rolled terrain superoperators to 2.2e-16 across all 8 terrains, confirms all 8
               CPTP (Choi PSD) and the nonunitality bits. 5th independent route at operator level.
               Both sims self-skip if tools absent (portable). Layer 15; harness 30 pass (constraintcore).


# Proof lane extended — 2026-07-02 (three more manifold laws forced)
UP-18 NEW SIM  manifold_laws_smt_proof.py -- (1) 8-of-16 access law FORCED by the sheet law
               (Z3: any non-8/8 split UNSAT); (2) pole-mirror pairing (0,4)(2,6) forced by
               zero-sum AND cross-sheet -- with the logged FINDING that zero-sum ALONE is
               degenerate (2 matchings zero-sum; near-equal |fixed_z|); (3) two-sector theorem
               as a SYMBOLIC IDENTITY (sympy): eigs(rho(theta,phi))={p,1-p} for all angles,
               dS/dtheta=0 exactly -> entropy identically blind to Axis-2. Self-skips if
               z3/sympy absent. Layer 15.7-15.9; harness 31 pass (constraintcore).


# Physics bridges — 2026-07-02 (established physics on the info<->physics seam)
UP-19 NEW SIM  physics_bridge_sim.py -- the engine reproduces two pieces of confirmed physics
               (NOT a ToE validation). (1) Landauer: dissipative terrains erase a bit; pure
               limit saturates the bound (S:1->0, purity->1, bath >= kT ln2 = 2.87e-21 J@300K);
               coherent drive only makes erasure partial. (2) Einselection: Ti z-dephasing
               selects {|0>,|1>}, Te selects {|+>,|->}; pointer states ARE the purity-1 channel
               fixed points -- "an attractor basin that selects for itself" as decoherence
               physics. figures/physics_bridge.png. Self-skips if qutip absent. Layer 16.


# Fluctuation theorems — 2026-07-02 (nonequilibrium generalization of the Szilard bound)
UP-20 NEW SIM  fluctuation_theorem_sim.py -- the engine's unitary drive obeys Jarzynski
               (<e^-bW>=e^-bdF, 3e-14 at every drive speed) AND Crooks (P_F/P_R=e^{b(W-dF)}
               across all work bins). 2nd law <W>>=dF holds; dissipated work drops as drive
               slows. Genuine dF=-0.793 (nontrivial). FINDING: first Crooks pass failed at the
               tails -- a reverse-protocol bug, not physics; fixed time-reversed drive recovered
               the exact law. numpy-only. Layer 16.3; harness 33 pass (constraintcore).


# Quantum speed limit — 2026-07-02 (the model's two axioms as a physical bound)
UP-21 NEW SIM  quantum_speed_limit_sim.py -- the engine's drive obeys the QSL, tying FINITUDE
               and NONCOMMUTATION to dynamics. (1) t_orth=(pi/2)/dE saturates the Levitin-
               Toffoli bound (ratio 0.999) at every energy; larger dE = faster. (2) [H,rho]!=0
               <=> dE>0 <=> evolution (three equivalent); commuting H never moves; full
               orthogonality needs the state balanced across eigenstates (tilted H precesses
               part-way). numpy-only. Layer 16.4; harness 34 pass (constraintcore).


# Holographic bound + decoherence scaling — 2026-07-02 (finitude & the classical boundary)
UP-22 NEW SIM  holographic_bound_sim.py -- FINITUDE as the holographic/Bekenstein bound:
               S(rho)<=log2(dim) (maximally-mixed saturates); Page-curve area law S(A)<=
               min(|A|,|B|) on n=6 qubits (smaller boundary caps shared info). numpy-only. L16.5.
UP-23 NEW SIM  decoherence_scaling_sim.py -- HOW FAST einselection wins: GHZ decoherence rate
               ~2n (independent baths, linear) / ~2n^2 (collective, superdecoherence, exact).
               The quantum->classical boundary is a scaling law. numpy+scipy. L16.6.
               Harness 36 pass (constraintcore).


# Chemistry bridge — 2026-07-02 (Layer 17.1, the bridge ladder begins)
UP-24 NEW SIM  chemistry_bridge_sim.py -- the chemical bond from the axioms via the Hubbard
               dimer. Fermionic {c,c^dag}=delta (Pauli exclusion) exact; ground state a spin
               singlet (S^2=0) with E=(U-sqrt(U^2+16t^2))/2; bond IS entanglement (S(site1)
               2b->1b); covalent->ionic crossover (docc 0.25->0). numpy-only. Layer 17.1.
               Opens Layer 17 (bridge ladder: math->physics->chemistry->biochem->evolution->
               consciousness). Harness 40 pass (constraintcore, full).


# Noncommutation bounds — 2026-07-02 (Layer 16.7, math foundations = physics)
UP-25 NEW SIM  noncommutation_bounds_sim.py -- noncommutation as a sharp bound on information
               and correlation. (1) Maassen-Uffink entropic uncertainty H(A)+H(B)>=log2(1/c),
               tight at the MUB limit (1 bit for Z vs X). (2) CHSH quantum |S|=2sqrt2
               (Tsirelson) > classical 2; commuting control 1.41 cannot violate. numpy-only.
               Layer 16.7. Harness 41 pass (constraintcore, full).


# Holevo bound — 2026-07-02 (Layer 16.8, finitude of readout)
UP-26 NEW SIM  holevo_bound_sim.py -- accessible classical info capped: I(X:Y)<=chi<=log2(d).
               chi 0->1 bit as signals go identical->orthogonal; true upper bound (best
               measurement never beats chi); 4 tetrahedral symbols in a qubit still cap at 1
               bit. Caught+fixed a Bloch-normalization slip (unphysical chi>1) with a purity
               assertion. numpy-only. Layer 16.8. Harness 42 pass (constraintcore, full).


# Data-processing inequality — 2026-07-02 (Layer 16.9, the co-ratchet arrow)
UP-27 NEW SIM  data_processing_sim.py -- information only decreases under any channel. Rel-entropy
               monotonicity S(N(rho)||N(sigma))<=S(rho||sigma) (1.18->0.09 under dephasing) and
               chain DPI I(A:C)<=I(A:B); ZERO violations across 400 random CPTP channels each.
               The directional monotone einselection/Landauer/Holevo descend from. numpy-only.
               Layer 16.9. Harness 43 pass (constraintcore, full).


# No-cloning theorem — 2026-07-02 (Layer 16.10, store not copy)
UP-28 NEW SIM  no_cloning_sim.py -- no unitary copies an unknown state. Unitarity needs
               <a|b>=<a|b>^2 (orthogonal/identical only); CNOT cloner F=1 on basis, 0.5 on |+>;
               Buzek-Hillery UQCM constructed+measured F=5/6 constant (std 1e-16). Caught two
               bugs via construct-and-measure (malformed partial trace F>1; non-orthogonal
               branches). numpy-only. Layer 16.10. Harness 44 pass (constraintcore, full).


# Bridge loopback -> terrain enrichment — 2026-07-02 (Layer 17.2, engine-deepening)
UP-29 NEW SIM  terrain_information_signature_sim.py -- the Layer-16 bridges loop back onto the
               real 8 terrain GKSL channels. Bridge observables (||L(I)||, entropy-prod rate,
               coherence-kill rate, Holevo chi) sort terrains into 3 max-differentiated classes
               damp<depol<proj; classification FORCED by z3 AND cvc5 (both SAT law, both UNSAT
               erased control -- three-engine contract). FINDING: density-level observables
               separate the 3 KINDS not all 8 terrains (eps/pole signs = documented density
               blindness; 8-way needs spinor level). numpy+scipy+z3+cvc5. Layer 17.2.
               Harness 45 pass (constraintcore, full).


# Terrain-signature SMT correction — 2026-07-02 (audit fix)
FIX  terrain_information_signature_sim.py -- replaced the pinned-constant SMT (bind measured
     rates to z3.RealVal, compare inequalities = dressed-up float compare) with a GENUINE
     combinatorial forcing check: solver searches c:8->{0,1,2} (3^8), full law UNSAT to any
     second partition (partition unique/forced), erased control SAT to an alternative. z3+cvc5
     agree. Verdict now depends on a real search, not a pre-computed comparison. Harness 45 pass.

H-19 VERIFIED full harness GREEN in a second clean sandbox: 40 pass / 0 fail /
              5 dep-conditional skips; then z3-solver+cvc5+qutip installed and
              all 5 conditional sims PASS (45/45 total). 1q AND 3q engines
              cross-substrate GREEN (numpy oracle vs jax+torch).
H-20 ADDED    REPO_AUDIT_AND_RESOLUTIONS.md into the bundle (source-level
              resolutions from the public Codex-Ratchet audit).
H-21 EDITED   MODEL_LAYER_LEDGER 6.6: two-64s tension RESOLVED BY SOURCE
              (atlas 9-10 three-layer split, 16 starred macro-stages); pending
              transcription only. Addendum: terrain-level a2 RESOLVED BY
              SOURCE as an installed frame flag (TERRAIN_LAW_LEDGER 17-22);
              the "find the invariant" open item closes as ill-posed.
H-22 EDITED   PHYSICS_INFO_BRIDGE_INDEX.md: attribution AUDIT FLAG — the ten
              bridges are theorems of the installed U-1 carrier; they earn
              realization faithfulness, not axiom grounding. CLAUDE.md guard
              added.
H-23 FIXED    engines/trajectory_result.json had no producer in the bundle;
              quarantined to engines/quarantine/ with note (results must ship
              with their generators). lev_bridge_stream.json producer exists
              (lev_bridge_sim.py) — false alarm on that one.
H-24 EDITED   requirements.txt: z3-solver, cvc5, qutip declared as the
              optional set that unlocks the 5 dependency-conditional sims.


# 8-way terrain separation — 2026-07-02 (Layer 17.3, resolves 17.2 finding)
UP-30 NEW SIM  terrain_8way_separation_sim.py -- resolves the 17.2 finding. Two dynamical readers
               (steady-<sz> einselection pointer + coherence phase-velocity = -sign(eps)) added to
               the coherence-kill KIND coordinate SEPARATE all 8 terrains. z3 AND cvc5 search the
               28 pairs for a collision: full set UNSAT (separated), drop either reader -> SAT
               (each necessary). Uses the a2 source-resolution (REPO_AUDIT 1b: a2 = installed
               frame flag, read through dissipation). numpy+scipy+z3+cvc5. Layer 17.3. 46 pass.


# Co-ratchet + 7-axis orthogonality lattice — 2026-07-02 (Layer 17.4, deepen the ratchet)
UP-31 NEW SIM  coratchet_axis_orthogonality_sim.py -- (A) entropy CONSTRAINED to each terrain:
               native pointer-coherence monotone->0 under own Axis-5 T-op (einselection), foreign
               T plateaus, foreign F pumps up. (B) 2 signed ops on axes 5,6: T dS=+0.16, F dS=0
               exact; b6=-(b0*b3). (C) 7-axis lattice: 5 primitive DOF free (2^5=32), 2 derived
               (b0=b1*b2, b6=-(b0*b3)) forced -- z3 AND cvc5 UNSAT negation / SAT after erase.
               Loops einselection(16.2)+DPI(16.9) back in. numpy+scipy+z3+cvc5. Layer 17.4. 47 pass.


# Co-ratchet lattice SMT completion — 2026-07-02 (audit fix)
FIX  coratchet_axis_orthogonality_sim.py -- added cvc5_erased_frees(): the erase-frees (SAT)
     control was z3-only; now BOTH z3 and cvc5 verify BOTH halves (forced=UNSAT, erased=SAT),
     satisfying the three-engine contract's requirement that both solvers agree on the flipping
     control. Harness still 47 pass.


# Coupled co-ratchet (dual-loop 720) — 2026-07-02 (Layer 17.5, deepen the ratchet)
UP-32 NEW SIM  coupled_coratchet_dualloop_sim.py -- entropy ratchet + operator ratchet as ONE
               720deg double-loop (DUAL_LOOP_SPINOR_GRAMMAR, a documented runtime gap). COOL=amp
               damping->pure pointer (non-unital, S->0), HEAT=rotate+dephase (S->1). (A) opposite
               fixed points. (B) chirality asymmetry: LEFT-RIGHT flux sign-consistent across 200
               probes (mean +0.31). (C) orderings noncommute (0.22); z3 AND cvc5 model-count the
               chirality words: alternating->2, else 16 (count flips). numpy+scipy+z3+cvc5. 48 pass.


# Biochemistry bridge — 2026-07-02 (Layer 18.1, bridge ladder rung 4)
UP-33 NEW SIM  biochem_bridge_sim.py -- two-state biomolecular switch as a qubit; coherent
               tunneling L<->R = noncommutative (no classical shadow). (A) T=0 tunneling exact vs
               analytic. (B) quantum rate floor vs classical Kramers ->0; Arrhenius recovered.
               (C) catalysis = dual-loop coherent channel (>2x, endpoints fixed). (D) z3+cvc5:
               transfer requires the noncommuting tunneling term (SAT with, UNSAT without, both
               solvers both halves). Improves on the owner's classical Kramers baseline. 49 pass.


# Evolution / chirality bridge — 2026-07-02 (Layer 19.1, bridge ladder rung 5)
UP-34 NEW SIM  evolution_chirality_bridge_sim.py -- two chiral operating spaces (left/right Weyl
               engine families) as runnable math per the owner's build note. (A) both run the same
               8-stage finite loop, drive to opposite poles (emergent). (B) mirror non-equivalence
               (M.X_L.M=X_R but X_L!=X_R, no sign-flag collapse). (C) F01+N01 forcing gate: z3+cvc5
               self-mirror AND noncommuting UNSAT (chirality forced), drop N01 SAT only for null.
               (D) Frank autocatalysis: tiny bias -> homochirality. HONEST: does NOT derive WHICH
               chirality is physical (weak-force parity is empirical input). 50 pass.


# Root axiom + entropic monism + S-knots — 2026-07-02 (Layer 0.1, the foundation)
UP-35 NEW SIM  root_axiom_sim.py -- renders the owner's root derivation chain as runnable math.
               (A) EC-1/EC-2 probe-relative identity (~ classes change with P). (B) EC-3 root gate
               a=a iff a~b: z3+cvc5 SAT with distinction / UNSAT when erased (both halves). (C)
               entropic monism: S = log2(distinguishable branches). (D) identity needs the A|B cut
               (I(A:B): product 0, Bell 2). (E) S-knot: Hopf fiber Gauss linking invariant 1 vs 0.
               Also fixed Layer 19.1 selection-map source citation (A2_CHIRALITY only). 51 pass.


# THE MODEL CORE — 2026-07-02 (Layer 0.0, distinguishability-creation engine)
UP-36 NEW SIM  distinguishability_engine_core_sim.py -- engages the owner's INTEGRATED model as ONE
               object (not isolated keyword-demos). Primitive = constraint on distinguishability;
               entropy is a LATER measure. a=a iff a~b made dynamical on the Hopf carrier: (A) fiber
               density-stationary (3e-16) vs base density-traversing (0.932); (B) Berry holonomy =
               -pi(1-|cos2eta|) matches doc exactly (inner -0.920, Clifford -pi); (C) distinguish-
               ability 0.932 with entropy 3e-16 -> entropy is downstream, not the substance; (D)
               z3+cvc5 fiber-UNSAT/base-SAT gate. CORRECTION: root_axiom_sim.py de-primitivized
               entropy (was "entropy IS the one substance" -> "entropy is a later measure OF
               distinguishability"), per OWNER_THESIS_AND_COSMOLOGY.md. 52 pass.


# AXIS-0 GRAVITY MODEL — 2026-07-02 (Layer 0.2, gravity = entanglement-entropy gradient)
UP-37 NEW SIM  entropic_gravity_axis0_sim.py -- renders the owner's axis-0 gravity model (ENTROPIC_
               MONISM_ORIGIN_AND_COSMOLOGY sec 5-8 + seeding Grok chat) as checkable math. Einstein-
               form field eq sourced by grad of entanglement entropy: (1) negentropy well sources
               (grad S)^2=518.6, flat field 1.6e-29 (gravity needs a gradient); (2) two-regime sign
               structure (attractive well / repulsive hill, equal mag = one force); (3) z3+cvc5
               flat-UNSAT/gradient-SAT gate. Fenced as OWNER DOCTRINE under test per doc sec 7 (does
               not derive the field eq, not >1D GR, does not replace GR/QM). Built after reading the
               owner-supplied gravity docs, not presumed. 53 pass.


# GATE SOUNDNESS FIX — 2026-07-02 (audit response)
UP-38 FIX  distinguishability_engine_core_sim.py + entropic_gravity_axis0_sim.py: the z3/cvc5 gates
           previously hardcoded the branch boolean (pinned-constant if-check). Rewritten so solver
           inputs are DERIVED from the sims' own measured numbers (fib_drift/base_travel; source/
           source_flat), the structural law is tested for FIT against the measured data, and a
           counterfactual control flips UNSAT(with law)->SAT(law dropped) so the law -- not
           arithmetic -- carries the verdict. Ledger v34/v35 (D)/(3) wording corrected. 53 pass.


# CITATION CLOSURE (STATE_OF_THE_MODEL open-ledger V.1) — 2026-07-02
UP-39 CONFIRM  Open item V.1 ("igt-pattern lines 470-478 verbatim (wiki) — the one uncited sentence
               behind §7t's 'conjugated = x↔z image' source reading") is resolvable and now confirmed.
               VERIFIED: the wiki doc concepts/igt-pattern-explicit-math-reference.md contains the
               four-operator table verbatim at lines 475-478 (Ti z-dephasing / Te x-dephasing / Fi
               x-rotation / Fe z-rotation; native terrains Se,Ne direct vs Ni,Si conjugated) and the
               §7k tribunal sentence at line 166. The spec (CONSTRAINT_CORE_FORMAL_SPEC §7q/§7t) already
               cites these lines and upgrades the "conjugated = x↔z image of direct" reading to the exact
               W-covariance theorem (W·Ti·W=Te residual 3.4e-33). So the source is not merely cited but
               earned; the STATE doc's ledger simply lagged the spec. No new sim needed. 53 pass.
               NOTE ON PLAN: STATE_OF_THE_MODEL §VI orders Consolidate->Contact->Extend and warns
               "extension before contact is the failure mode the whole harness exists to prevent."
               A new coherent-information / i-scalar sim is a Phase-E action and is therefore HELD until
               the Phase-X contact items (V.1-V.4) are addressed. This turn does the cheapest Phase-X
               action (V.1 verbatim confirmation), per that ordering.


# PHASE-X V.2 — 2026-07-02 (charge-specific chi2 via dissipation foothold: NEGATIVE)
UP-40 NEW SIM (negative result)  eps_even_a2_dissipation_foothold_sim.py builds the instrument V.2
               proposed -- read the installed frame through dissipation -- and resolves it NEGATIVELY.
               Three honest findings: (1) the eps-even readout separates a2 but CIRCULARLY (a2 is the
               installed frame, fed in); (2) the 0.22-vs-0 dissipation gate FAILS (unitary dynamics
               also moves the eigenvector under the frame); (3) NOT a2-specific (any nontrivial frame
               fires). So a2 is an installed-frame flag / operator-layer W-covariance label, not a
               terrain-generator charge. STATE open-ledger V.2 -> RESOLVED NEGATIVE. Failure is signal:
               the decisive 7m test is not decidable by this instrument; a real a2-specific meter stays
               open. Held to Phase-X ordering (no Extend). 54 pass.


# LAYER 0.3 — 2026-07-02 (signed Axis-0 primitive; loops back into gravity 0.2)
UP-41 NEW LAYER  signed_axis0_primitive_sim.py builds the SIGNED Axis-0 primitive as its own
               foundational object: coherent information I_c(A>B)=S(rho_B)-S(rho_AB)=-S(A|B), sourced
               from ENTROPIC_MONISM sec 8 ("-S(A|B) kernel | Conditional entropy IS the entanglement
               measure") + the entropy-tables doc (signed primitive; mutual info the unsigned
               companion). FOUR results: (1) sign of I_c separates binding(+)/dispersing(-) where the
               unsigned I(A:B)>=0 cannot; (2) STRUCTURAL THEOREM -- 4000 separable states max I_c=-6e-6
               (positive I_c is a genuine, and STRICTER, entanglement witness: Werner entangled from
               p=1/3 but binds only from p*=0.7476); (3) LOOP-BACK -- the 0.2 gravity two-regime split
               is now the two MEASURED signs of I_c along a spatial chain (binding core attractive /
               dispersing halo), replacing the hand-placed +/-S_anom stand-in; (4) z3+cvc5 gate,
               derived inputs, law fits + flipped control. This EARNS the sign structure 0.2 asserted.
               Honest scope unchanged: entropic-gravity MECHANISM under test, not a GR derivation. 55 pass.


# LAYER 0.4 — 2026-07-02 (entropic foundation reproduces Newtonian gravity; dark-sector fenced)
UP-42 NEW LAYER  entropic_newton_limit_sim.py answers the owner framing ("new foundations to GR that
               lead to the SAME observations and account for what GR+visible-matter can't"). On the
               0.2/0.3 gravity=entropy-gradient substrate, in Verlinde entropic-force form: (1) EXACT
               Newtonian limit -- a=2pi c kT/hbar with holographic N=A c^3/(G hbar), kT=2Mc^2/N
               reproduces a=GM/r^2 to ratio 1.000000 across Earth/Sun/galaxy (Earth g=9.7275 falls
               out); (2) STRUCTURAL -- N∝r^p gives a∝r^(p-3): AREA p=2 -> slope -2 (Newton), VOLUME
               p=3 -> slope -3 (wrong); holographic area-scaling FORCES inverse-square; (3) FENCED
               dark-sector -- entropy-gradient 1/r term (log potential, the kind 0.3's signed I_c
               source gives for an isothermal profile) flattens rotation curves without particulate
               dark matter, BUT a0 is phenomenological NOT derived from RC-1+RC-2. Honest scope:
               (1)+(2) reproduce established entropic-gravity (Verlinde) on the substrate -- not novel
               physics; (3) owner doctrine under test (sec-7 fence). No claim to replace GR/SM. 56 pass.


# LAYER 20.1 — 2026-07-02 (Standard-Model bridge: weak force left-handedness from F01+N01)
UP-43 NEW LAYER  weak_force_chirality_bridge_sim.py earns one concrete SM fact -- the weak interaction
               couples ONLY to left-handed fields (maximal parity violation) -- from the SAME F01+N01
               move Layer 19.1 used for biological chirality, on the left-Weyl substrate. Source:
               A2_CHIRALITY ("Universe is Type 1 LEFT_WEYL_CONVERGENT"; "Weak force parity violation:
               only left-handed particles h=-1/2"; "Type 2 (Right) = antimatter") + axes-math sec 9
               (Axis-3 selects Weyl rep; SU(2)/Hopf orbits). Chiral projectors P_L=1/2(1-g5). RESULTS:
               (1) P_L vertex asymmetry A=1 (maximal, V-A) vs vector I control A=0 (parity conserved,
               EM-like); (2) F01+N01 forces chirality -- P_L is finite + parity-noncommuting
               (g0 P_L g0 = P_R), and the ONLY parity-symmetric combination 1/2(P_L+P_R)=I/2 is exactly
               the parity-blind vector coupling; so any finite parity-noncommuting coupling must be
               chiral (side=LEFT is empirical, as in 19.1); (3) z3+cvc5 gate, derived inputs, law
               "finite AND parity-noncommuting => chiral" fits + flipped control. HONEST SCOPE:
               reproduces the weak PARITY structure and its shared F01+N01 origin with 19.1/A2; does
               NOT derive SU(2)xU(1), the Weinberg angle, or couplings. Owner doctrine under test;
               no claim to replace the SM. 57 pass.


# LAYERS 0.5 + 0.6 — 2026-07-02 (deep foundations: division-algebra ratchet + cosmogenesis persistence)
UP-44 NEW LAYER 0.5  division_algebra_ratchet_sim.py -- the ratchet from WEAKEST structures / SHORTEST
               leaps with nonassociativity ratcheted, as the Cayley-Dickson ladder R->C->H->O->(S kill).
               Source: working_math_scaffold 10.3 (H assoc=0, O assoc!=0, sedenion zero-divisor kill-
               control; G2=Aut(O)) + root_axioms:51 (nonassociativity = GROUPING-level face of N01).
               Verified: commutativity dies at H, associativity at O (order/grouping faces of N01);
               Hurwitz |xy|=|x||y| holds R..O, fails S; explicit sedenion zero-divisor (e1+e10)(e5+e14)=0
               (persistence lost); G2=Aut(O) derivation-algebra dim = 14 (computed). z3+cvc5 gate:
               "admit rung IFF it divides" fits R..O, control admit-S UNSAT-with-law -> SAT-without.
UP-45 NEW LAYER 0.6  cosmogenesis_persistence_sim.py -- the owner's origin story (x_grok_chat_TOE lines
               30,38: static fuzz field, no info between frames, time = sequence; "first pattern was an
               entangled expanding field, dark energy came first"). The LEAST thing that persists between
               information-less frames = a NORM-PRESERVING carrier (the division property of 0.5) = a
               spinor. Verified: static fuzz frame-correlation ~0.01 (no carried time); norm-preserving
               map persists (||psi||=1) vs lossy annihilates (~1e-9, sedenion-type death); product |00>
               seed entangles I_c 0 -> +0.999, size 0 -> Bell (entangled expanding field); chirality ties
               +entropy=dark energy(right)/-entropy=dark matter(left) to the two Weyl sheets (0.3+A2).
HONEST SCOPE: 0.5 earns the ladder+kill-control+G2; does NOT build the octonion spinor network or derive
               SM gauge from G2 (downstream, scaffold 10.4). 0.6 is a mechanism illustration of the owner
               cosmogenesis, NOT a cosmological-constant derivation. Owner doctrine under test. FULL HARNESS VERIFIED: 59 pass / 0 fail / 0 skip GREEN
               (in /tmp/final_base incl JAX + Julia cross-substrate lanes).


# LAYER 0.7 — 2026-07-02 (loop-back / convergence: one basin, many perspectives)
UP-46 NEW LAYER 0.7  perspective_convergence_sim.py -- tests the owner reframe that the ratchet, QIT
               engines, and physics model are ONE attractor basin seen from different perspectives, not a
               divergent set. Takes ONE Werner state family and computes each already-built physics
               bridge by its OWN native recipe: gravity (0.4) = sign of signed I_c; chirality (19.1/20.1)
               = forced iff entangled (negativity>0); cosmogenesis (0.6) = expansion size S(rho_A).
               RESULTS: (1) all three are projections of the single parameter p -- one object, many
               views. (2) NESTED onset order: entanglement onsets at p=1/3, binding-sign at p*=0.7476 --
               entanglement is necessary but NOT sufficient for the gravitational binding sign (a strict
               entangled-but-nonbinding regime exists between). (3) LOOP-BACK LESSON: the master invariant
               governing the physical sign is the SIGNED I_c (Layer 0.3), strictly stronger than raw
               entanglement -- the convergence RANKS the invariants and tightens which quantity is
               foundational. (4) z3+cvc5 gate: law chain bind<=>I_c, I_c=>ent, forced<=>ent fits all three
               regimes; control "entangled-but-nonbinding forced to bind" UNSAT-with-law -> SAT-without.
               HONEST SCOPE: demonstrates the one-basin claim as computed convergence on a one-parameter
               family + extracts the invariant-ranking lesson; does NOT prove global basin uniqueness.
               FULL HARNESS VERIFIED: 60 pass / 0 fail / 0 skip GREEN (incl JAX + Julia lanes).


# LAYER 0.8 + LOOP-BACK PACKET REPAIRS — 2026-07-03 (octonion spinor network; WEB_THREAD_LOOPBACK_20260703)
UP-47 NEW LAYER 0.8  octonion_spinor_network_sim.py -- the practical sim carrier of scaffold 10.4/11: a
               finite spinor network, nodes=octonionic spinors, edges=noncommutative+nonassociative
               couplings, built ON Layer 0.5. Closes loop-back packet item 3 ("exhibit a G2 action, not
               just dim 14"). RESULTS: (1) path-bracketing gap ~1.6 across a 3-edge path = grouping-level
               N01 as a NETWORK-level observable; (2) single-edge control gap = 0 (nonassoc invisible on a
               point -> network necessary); (3) G2 ACTION exhibited: concrete phi=exp(0.3 D) with
               phi(xy)=phi(x)phi(y) to ~1e-16 (real Aut(O) element), bracketing gap INVARIANT under it ->
               G2 is the symmetry group of the network coupling schedule; (4) L/R chirality gap ~0.05 on
               the network (ties to 19.1/20.1). Hypothetical lane; does NOT yet run terrain/operator
               schedules on the network or derive SM gauge from G2.
UP-48 LOOP-BACK REPAIRS (WEB_THREAD_LOOPBACK_20260703, local-harness adversarial review):
   STATE_OF_THE_MODEL.md 6 wording-tier repairs (a-f): "validated across four substrates" -> "reproduced
     ... (reproducibility engineering, not formal verification)"; Axis-6 b6 law -> "0/8 violations
     OBSERVED ... construct-then-verify, known defect"; P12 (1,1,1)/sqrt3 -> "candidate/conditional per
     lineage"; "EARN REALIZATION FAITHFULNESS" -> "earned realization checks ... no encoding bugs FOUND";
     "P12 axis load-bearing" -> "axis-conditioned result"; added cross-family adversarial-review line.
   FENCE BREACH (item 4): removed EARNS/EARNED self-stamps from sim docstrings (signed_axis0,
     division_algebra, weak_force -> "renders/admits, hypothetical lane") and ledger rows; banned verb
     "creates NO distinguishability" -> "registers NO". CLAIM SPLITS (item 3): entropic_newton "CONSEQUENCE
     not assumed" -> "follows GIVEN assumed area law = Verlinde reproduced, not derived from F01+N01";
     weak_force "earns one SM fact" -> "admits chirality STRUCTURE forced; vertex+side empirical".
HONEST NEGATIVE recorded (item 5): eps_even_a2 dissipation-foothold route stays a diagnostic, not cited
     as positive. FULL HARNESS VERIFIED: 61 pass / 0 fail / 0 skip GREEN (incl JAX + Julia lanes).


# LAYER 0.9 — QIT FREE ENERGY PRINCIPLE EARNED THROUGH THE RATCHET — 2026-07-03
UP-49 NEW LAYER 0.9  qit_fep_ratchet_sim.py -- a pure-QIT FEP DERIVED FROM the constraint surface stage by
               stage, NO shortcuts, with EVERY classical/thermal primitive of standard FEP replaced by its
               constraint-surface origin (owner directive: "the real math must always come before the
               jargon"; "thermo sounds like a dangerous term"). Rejected the doc's own thermal prior
               exp(-E/T)/Z (Boltzmann) and the amplitude-damping "ground state"; replaced by GKSL fixed
               points of the native Axis-5 T-operators (Ti z-dephasing, Te x-dephasing), full-rank by
               construction so relative entropy is finite with ZERO regularization -- no temperature, no
               energy, no -log p, no classical probability anywhere in the math.
               REPLACEMENTS: p(z)->density spectrum (F01); exp(-E/T)->GKSL fixed point; -log p(x)->S(rho||sigma);
               Bayesian update->CPTP relaxation; Markov-blanket graph->vanishing I(A:C|B).
               SIX EARNED STAGES: (1) F01 distinguishability FORCES the functional -- S(rho||sigma) unique as
               BOTH CPTP-monotone AND additive (relent additive 3.6e-14; trace distance NOT, off 0.287).
               (2) Axis-0 geometry splits surprise EXACTLY (Pythagorean |d|=0) into classical spectral
               (entropy DOF) + quantum basis-mismatch (coherence DOF). (3) Axis-5 operators ARE inference:
               each native T-op drives surprise vs OWN pointer monotone to 0 (self-evidencing); foreign
               >0.1. (4) 3-qubit Markov blanket = vanishing I(A:C|B) (chain 0.0000; direct A-C 0.278).
               (5) active selection = min-surprise (z->Ti, x->Te). (6) z3 AND cvc5: law fits, foreign-forced
               control UNSAT->SAT. LOOP-BACK: FEP is a different VIEW of the ratchet, not a new mechanism.
               Hypothetical lane; no Friston hierarchical continuous-state claim. FULL HARNESS VERIFIED: 62 pass / 0 fail / 0 skip GREEN (incl JAX + Julia lanes).


# LAYER 0.10 — ACTIVE HALF OF QIT-FEP: POLICY SELECTION ON THE MANIFOLD — 2026-07-03
UP-50 NEW LAYER 0.10  qit_active_inference_planning_sim.py -- the ACTIVE half of the QIT Free Energy
               Principle (0.9 built perceptual), run as a PLANNING loop over operator PATHS. A policy is a
               sequence of native operators (Ti/Te dephasings + F rotations); cost = PATH INTEGRAL of
               surprise G(pi)=sum_t S(rho_t||goal); active inference = select min-cost policy. All CPTP +
               relative entropy; NO reward, NO temperature, NO classical probability (goal = density-op
               prior, cost = distinguishability). RESULTS: (1) PRAGMATIC: min-path-integral policy reaches
               a tilted-pointer goal (rotate-then-commit), final surprise 0.06 from 0.16. (2) N01 INHERITED:
               100/125 3-step policies cost != reverse (mean gap 0.21, max 0.87); selected fwd 0.31 vs rev
               0.84 -- policy space carries the manifold's noncommutation, the SAME path-dependence as the
               0.8 octonion-network bracketing gap. (3) EPISTEMIC (resolve which-concept, soft posterior
               q(c)~exp(-S(rho||prior_c))): committing/dephasing policy resolves concept-identity (+0.013
               bits), rotating does not (0.000) -- directional sign structure, magnitude honestly small
               (nearby anchors). (4) GATE z3 AND cvc5: law "valid policy <=> reaches AND order-consistent"
               fits, control "non-reaching forced valid" UNSAT-with-law->SAT-without. LOOP-BACK: closes the
               FEP loop -- perception (0.9) relaxes surprise, action (0.10) selects the path that will; both
               the SAME relative-entropy descent over trajectories; 0.8's N01 makes planning nontrivial.
               Hypothetical lane; finite 3-step enumeration, not continuous optimal control. FULL HARNESS VERIFIED: 63 pass / 0 fail / 0 skip GREEN (incl JAX + Julia lanes).


# LAYER 0.11 — 16-STAGE ENGINE SCHEDULE AS ACTIVE-INFERENCE POLICY SPACE — 2026-07-03
UP-51 NEW LAYER 0.11  sixteen_stage_engine_schedule_sim.py -- ties Layers 0.8/0.9/0.10 to the REAL geometric
               constraint manifold: the 8 terrains (earned all-distinct 17.3, eps-signed coherent drive +
               kind dissipator) as the state space, each admitting EXACTLY 2 of 4 native operators (one T,
               one F) on its Axis-2 sheet (eps>0 direct {Ti,Fi}; eps<0 conjugated {Te,Fe}) = 8x2 = 16
               distinct engine stages (owner: "16 unique stages ... each terrain has only 2 kinds of
               operators it can use, in a certain signed axis6 way"). RESULTS: (1) 16/16 stages DISTINCT as
               information transforms (fingerprint on 5-probe set, min pairwise 0.336) -- no DOF collapse.
               (2) SHEET-ADMISSIBILITY is the UNIQUE partition (z3+cvc5 SEARCH not pin): sheet bit forced to
               measured eps -> 1 model; eps-erased -> 2^8=256 ambiguous. (3) ACTIVE PLANNER (0.10 machinery)
               on the REAL 16-stage schedule: min-cost 2-stage policy REACHES terrain-4 pointer (surprise
               2.77->0.93); 240/256 policies order-sensitive (max gap 1.27) = N01 inherited from manifold.
               LOOP-BACK: terrains (geometry) + 2-op admissibility (Axis-5/6 signed rule) + active planner
               (0.10) are ONE engine -- the manifold with the FEP loop running on it. HONEST NEGATIVE:
               surprise-reduction as SOLE admissibility criterion is NOT clean (4/8 single-probe) and is NOT
               claimed; admissibility here is the structural Axis-2 sheet rule, SMT-gated. Hypothetical lane;
               does NOT run the 720deg double-loop or 64-schedule; 2-stage enumeration. HARNESS PENDING.
