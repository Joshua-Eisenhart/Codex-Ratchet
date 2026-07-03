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

H-25 VERIFIED (seventh audit, second sandbox): engines 1q AND 3q validate
              3/3 substrates including owner-hardware Julia results (1e-12 /
              9.9e-13); all 8 new sims run green individually incl. the three
              L18 bridges; ledger fencing on gravity/evolution confirmed
              correct; corrections packet absorbed (Julia vec fix, scoped
              a2 no-go, tier corrections all consistent with prior audits).
H-26 ADDED    STATE_OF_THE_MODEL.md — master summary: tower grades, audit
              trail, doc-corpus integration map (5 lanes -> layers, reading
              order), complete open ledger, three-phase plan (Consolidate /
              Contact / Extend). Source citations: scaffold L113 (Axis-2 =
              V_s frame, connection K=iV†V̇) confirms the installed-frame
              resolution from the owner's own hand.
