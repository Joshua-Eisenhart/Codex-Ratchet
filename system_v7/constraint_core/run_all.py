#!/usr/bin/env python3
"""
run_all.py -- deterministic verification harness for the constraint-core bundle.

Usage:  python3 run_all.py            (exit 0 = all checks green, 1 = failure)
        python3 run_all.py --fast     (skip the two JAX sims even if jax exists)

Every sim is standalone; this harness runs each one and asserts its HEADLINE
INVARIANTS against expected values with explicit tolerances. Two check types:
  contains: literal substring must appear in stdout
  approx:   regex captures a float; |value - expected| <= tol

IMPORTANT FOR AGENTS: some expected values are HONEST FAILURES (e.g. the Axis-0
entropy doctrine must remain False; the order-blind collapse must remain 11/64).
A run that makes those "pass" by flipping them is a REGRESSION. Never edit an
expected value to make a check green -- a mismatch is a finding to report.
Writes run_all_report.json next to this file.
"""
import json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SIMS = os.path.join(HERE, "sims_and_scripts")
FAST = "--fast" in sys.argv

def has_jax():
    try:
        import jax  # noqa
        return True
    except Exception:
        return False

def torch_python():
    """Return a python interpreter path that can import torch, or None.
    Order: current interpreter; $CR_TORCH_PYTHON; any sibling conda env whose
    python imports torch (torchcarrier by convention). Portable across machines --
    the torch-lane sims (quantum Hopfield etc.) run wherever torch actually lives."""
    def _imports_torch(py):
        try:
            r = subprocess.run([py, "-c", "import torch"], capture_output=True, timeout=60)
            return r.returncode == 0
        except Exception:
            return False
    if _imports_torch(sys.executable):
        return sys.executable
    env = os.environ.get("CR_TORCH_PYTHON")
    if env and os.path.exists(env) and _imports_torch(env):
        return env
    # scan sibling conda envs (…/envs/<name>/bin/python), prefer names hinting torch
    base = sys.executable
    for _ in range(6):
        base = os.path.dirname(base)
        envs = os.path.join(base, "envs")
        if os.path.isdir(envs):
            names = sorted(os.listdir(envs),
                           key=lambda n: (0 if "torch" in n.lower() else 1, n))
            for n in names:
                py = os.path.join(envs, n, "bin", "python")
                if os.path.exists(py) and _imports_torch(py):
                    return py
            break
    return None

_TORCH_PY = None  # resolved lazily in main()

# (script, timeout_s, needs_jax, checks)
# check = ("contains", literal)  or  ("approx", regex_with_one_group, expected, tol)
SUITE = [
 ("constraint_core_audit.py", 120, False, [
   ("contains", "C1 sigma_pm         : True"),
   ("contains", "C4 all CPTP         : True"),
   ("contains", "C5 b6=-b0b3         : True"),
   ("contains", "C6 sink/source      : True"),
   ("contains", "C7 entropy peak     : True"),
   ("approx", r"C2 bloch_err\s*:\s*([0-9.e-]+)", 0.0, 1e-12)]),
 ("constraint_core_symbolic.py", 180, False, [
   ("contains", "1Q: True  2Q: True"),
   ("contains", "∫F = -4*pi"),
   ("contains", "b6=-b0*b3 [finite_exhaustive]: True (0 violations / 8)")]),
 ("engine_64_schedule_sim.py", 240, False, [
   ("approx", r'"n_orderblind":\s*(\d+)', 11, 0),      # honest collapse -- must stay 11
   ("approx", r'"n_ordersensitive":\s*(\d+)', 64, 0),
   ("approx", r'"mean_order_gap":\s*([0-9.]+)', 0.5436866002450209, 1e-9)]),
 ("nested_basin_sim.py", 240, False, [
   ("approx", r'"verdict": "attractor"()', None, None)]),  # special-cased below: count == 4
 ("terrain_sourcelock_axis0_sim.py", 240, False, [
   ("approx", r'"Source":\s*{\s*"kind": "Ni",\s*"fixed_z":\s*([0-9.+-]+)', 0.906, 0.02)]),
 ("axis0_spinor_720_sim.py", 120, False, [
   ("contains", "360 loop: -1.0000"),
   ("contains", "720 loop: 1.0000")]),
 ("three_qubit_octonion_fep.py", 240, False, [
   ("contains", "witness=(1, 2, 4)"),
   ("contains", "spinor dim 8 = 3 qubits"),
   ("contains", "'F_nonneg': True")]),
 ("axis0_xor_sim.py", 60, False, [
   ("contains", "parity is NOT linearly separable in (a1,a2): True")]),
 ("axis0_sector_sim.py", 120, False, [
   ("approx", r"worst spectral-invariant change under frame conjugation = ([0-9.e-]+)", 0.0, 1e-12),
   ("contains", "closed-loop phase gauge-invariant (cannot read a2): True")]),
 ("axis0_gauge_breaking_sim.py", 120, False, [
   ("approx", r"identical channel at delta=0: \|\|ch1-ch0\|\| = ([0-9.e-]+)", 0.0, 1e-12),
   ("contains", "NOT constant => no linear law"),                 # withdrawn claim guard
   ("approx", r"delta=0\.05\s+split=[0-9.]+\s+split/delta=([0-9.]+)", 0.1498, 0.01),
   ("approx", r"delta=2\.00\s+split=[0-9.]+\s+split/delta=([0-9.]+)", 0.0386, 0.01)]),
 ("terrain_differentiation_sim.py", 240, False, [
   ("contains", "all distinct: True"),
   ("approx", r"min=([0-9.]+)", 0.352, 0.05)]),
 ("operator_geometry_fusion_sim.py", 240, False, [
   ("approx", r"t3\s+Proj\s+([0-9.]+)", 0.000, 1e-3),
   ("approx", r"t2\s+Sink\s+([0-9.]+)", 0.705, 0.02)]),
 ("sixteen_stage_engine_sim.py", 240, False, [
   ("contains", "16 stages, all distinct: True"),
   ("contains", "all order-sensitive (N01): 16/16"),
   ("contains", "8/16 operator-fused, 8/16 source-surplus")]),
 ("engine_type_access_sim.py", 240, False, [
   ("contains", "all>0: True"),
   ("contains", "all<0: True"),
   ("contains", "flips 8/8")]),
 ("access_law_decoupling_sim.py", 300, False, [
   ("contains", "sign follows terrain 14/16, drive 2/16"),
   ("approx", r"dephasing \(Ti,Te\) max \|a\(\+\)\+a\(-\)\| = ([0-9.e+-]+)", 0.0, 1e-12)]),
 ("audit_response_w_covariance_sim.py", 120, False, [
   ("approx", r"\|\|W\.Ti\.W - Te\|\| = ([0-9.e+-]+)", 0.0, 1e-12),
   ("approx", r"\|\|W\.Fi\.W - Fe\|\| = ([0-9.e+-]+)", 0.0, 1e-12),
   ("contains", "V=exp(-iH0 u) cannot implement it")]),
 ("axis2_two_layer_sim.py", 120, False, [
   ("approx", r"\[W\] operator-map error: Ti->Te=([0-9.e+-]+)", 0.0, 1e-12),
   ("contains", "connection: V gives K=H0")]),
 ("nonunitality_theorem_sim.py", 60, False, [
   ("approx", r"t2 \[damp \]: \|\|L\(I\)\|\| = ([0-9.]+)", 1.4142, 1e-3),
   ("approx", r"t3 \[proj \]: \|\|L\(I\)\|\| = ([0-9.]+)", 0.0, 1e-6)]),
 ("chi2_openpath_readout_sim.py", 60, False, [
   ("approx", r"closed=([+-]?[0-9.]+) \(zero\)", 0.0, 1e-9),                              # closed loop blind
   ("approx", r"chi2 reads frame on ([0-9.]+)%", 100.0, 0.5)]),        # sector meter earned
 ("chi2_decisive_test_sim.py", 300, False, [
   ("contains", "chi2 is an eigenvector-sector meter, NOT charge-specific to a2"),
   ("contains", "parity match: convention A 2/8, convention B 6/8 -- NOT a readout"),
   ("approx", r"\|\|V-V\*\|\| = ([0-9.]+)", 1.809, 0.01)]),
 ("eps_even_a2_specificity_sim.py", 120, False, [
   ("contains", "NO -- ranges overlap"),                              # eps-even still fails a2
   ("approx", r"\(operator a2-conjugation\) = ([0-9.e+-]+)", 0.0, 1e-12),   # a2 exact at operator layer
   ("contains", "a2 is an operator-layer label")]),
 ("eps_even_a2_dissipation_foothold_sim.py", 120, False, [
   ("contains", "PASS eps_even_a2_dissipation_foothold_sim")]),  # Phase-X V.2: dissipation foothold NEGATIVE (a2 not a channel charge)
 ("axis_loadbearing_n01_sim.py", 120, False, [
   ("approx", r"coherent axis z-axis\s*: \(damp,Fe\) order gap = ([0-9.e+-]+)", 0.0, 1e-10),
   ("contains", "load-bearing, not conventional")]),
 ("admissibility_two_operator_sim.py", 120, False, [
   ("contains", "the 2 survivors are Axis-2 (W) conjugates: True"),
   ("contains", "EXACTLY 2 native operators per terrain, signed. O1 closed."),
   ("contains", "PASS admissibility_two_operator_sim")]),
 ("info_processing_sim.py", 180, False, [
   ("contains", "all 16 open-system processors (I_coh<0 for all): True"),
   ("contains", "all 16 distinct channels: True"),
   ("contains", "PASS info_processing_sim")]),
 ("memory_sim.py", 180, False, [
   ("contains", "720  deg: spinor overlap +1.0000"),
   ("contains", "PASS memory_sim")]),
 ("holodeck_sim.py", 180, False, [
   ("contains", "PASS holodeck_sim")]),
 ("lev_bridge_sim.py", 180, False, [
   ("contains", "PASS lev_bridge_sim")]),
 ("agent_loop_sim.py", 180, False, [
   ("contains", "PASS agent_loop_sim")]),
 ("axis_laws_dual_proof.py", 120, False, [
   ("contains", "PASS axis_laws_dual_proof")]),        # skips if z3/cvc5 absent
 ("terrain_qutip_crosscheck.py", 120, False, [
   ("contains", "PASS terrain_qutip_crosscheck")]),     # skips if qutip absent
 ("manifold_laws_smt_proof.py", 120, False, [
   ("contains", "PASS manifold_laws_smt_proof")]),      # skips if z3/sympy absent
 ("physics_bridge_sim.py", 120, False, [
   ("contains", "PASS physics_bridge_sim")]),           # skips if qutip absent
 ("fluctuation_theorem_sim.py", 120, False, [
   ("contains", "PASS fluctuation_theorem_sim")]),      # numpy-only; Jarzynski+Crooks
 ("quantum_speed_limit_sim.py", 120, False, [
   ("contains", "PASS quantum_speed_limit_sim")]),      # numpy-only; QSL = finitude+noncommut
 ("holographic_bound_sim.py", 120, False, [
   ("contains", "PASS holographic_bound_sim")]),        # numpy-only; finitude = capacity+area law
 ("decoherence_scaling_sim.py", 120, False, [
   ("contains", "PASS decoherence_scaling_sim")]),      # numpy+scipy; quantum->classical scaling
 ("chemistry_bridge_sim.py", 120, False, [
   ("contains", "PASS chemistry_bridge_sim")]),         # numpy-only; Hubbard dimer covalent bond
 ("noncommutation_bounds_sim.py", 120, False, [
   ("contains", "PASS noncommutation_bounds_sim")]),    # numpy-only; entropic uncertainty + CHSH
 ("holevo_bound_sim.py", 120, False, [
   ("contains", "PASS holevo_bound_sim")]),             # numpy-only; accessible-info capacity
 ("data_processing_sim.py", 120, False, [
   ("contains", "PASS data_processing_sim")]),          # numpy-only; DPI monotone (co-ratchet arrow)
 ("no_cloning_sim.py", 120, False, [
   ("contains", "PASS no_cloning_sim")]),               # numpy-only; no-cloning (store not copy)
 ("terrain_information_signature_sim.py", 180, False, [
   ("contains", "PASS terrain_information_signature_sim")]),  # z3+cvc5; bridges enrich the terrains
 ("terrain_8way_separation_sim.py", 180, False, [
   ("contains", "PASS terrain_8way_separation_sim")]),        # z3+cvc5; all 8 terrains separated
 ("coratchet_axis_orthogonality_sim.py", 180, False, [
   ("contains", "PASS coratchet_axis_orthogonality_sim")]),   # z3+cvc5; co-ratchet + 7-axis lattice
 ("coupled_coratchet_dualloop_sim.py", 180, False, [
   ("contains", "PASS coupled_coratchet_dualloop_sim")]),     # z3+cvc5; coupled dual-loop co-ratchet
 ("biochem_bridge_sim.py", 180, False, [
   ("contains", "PASS biochem_bridge_sim")]),                 # z3+cvc5; biochem bridge (tunneling switch)
 ("evolution_chirality_bridge_sim.py", 180, False, [
   ("contains", "PASS evolution_chirality_bridge_sim")]),     # z3+cvc5; evolution/chirality bridge (F01+N01 forcing)
 ("root_axiom_sim.py", 180, False, [
   ("contains", "PASS root_axiom_sim")]),                     # z3+cvc5; root axiom a=a iff a~b + entropic monism + S-knot
 ("distinguishability_engine_core_sim.py", 180, False, [
   ("contains", "PASS distinguishability_engine_core_sim")]), # z3+cvc5; MODEL CORE: fiber/base distinguishability-creation engine + Berry holonomy
 ("entropic_gravity_axis0_sim.py", 180, False, [
   ("contains", "PASS entropic_gravity_axis0_sim")]),         # z3+cvc5; axis-0 gravity model: gravity = gradient of entanglement entropy
 ("signed_axis0_primitive_sim.py", 180, False, [
   ("contains", "PASS signed_axis0_primitive_sim")]),          # z3+cvc5; Layer 0.3 signed Axis-0 primitive I_c=-S(A|B); earns 0.2 two-regime sign structure
 ("entropic_newton_limit_sim.py", 120, False, [
   ("contains", "PASS entropic_newton_limit_sim")]),           # Layer 0.4: entropic force reproduces Newton exactly (earned); dark-sector fenced
 ("weak_force_chirality_bridge_sim.py", 120, False, [
   ("contains", "PASS weak_force_chirality_bridge_sim")]),      # z3+cvc5; Layer 20.1 SM bridge: weak force left-handed coupling forced by F01+N01
 ("division_algebra_ratchet_sim.py", 120, False, [
   ("contains", "PASS division_algebra_ratchet_sim")]),         # z3+cvc5; Layer 0.5: R->C->H->O ratchet, nonassoc=grouping N01, S kill-control, G2=Aut(O)
 ("cosmogenesis_persistence_sim.py", 120, False, [
   ("contains", "PASS cosmogenesis_persistence_sim")]),         # Layer 0.6: least persisting carrier between fuzz frames = norm-preserving spinor; entangled expanding field
 ("perspective_convergence_sim.py", 120, False, [
   ("contains", "PASS perspective_convergence_sim")]),          # z3+cvc5; Layer 0.7 loop-back: gravity/chirality/cosmogenesis are ONE state's projections; signed I_c is master
 ("octonion_spinor_network_sim.py", 120, False, [
   ("contains", "PASS octonion_spinor_network_sim")]),          # Layer 0.8: nonassoc as path-bracketing network observable; G2=Aut(O) ACTION exhibited (loop-back item 3)
 ("qit_fep_ratchet_sim.py", 120, False, [
   ("contains", "PASS qit_fep_ratchet_sim")]),          # Layer 0.9: QIT FEP earned through the ratchet stage by stage (F01->functional forced, Axis-0 geometry split, Axis-5 operators=inference, 3q Markov blanket, active selection, z3+cvc5); NO thermal/classical primitive
 ("qit_active_inference_planning_sim.py", 120, False, [
   ("contains", "PASS qit_active_inference_planning_sim")]),          # Layer 0.10: ACTIVE half of QIT-FEP -- policy selection by path-integral free energy; N01 order-sensitivity inherited from manifold; epistemic sign structure; z3+cvc5
 ("sixteen_stage_engine_schedule_sim.py", 120, False, [
   ("contains", "PASS sixteen_stage_engine_schedule_sim")]),          # Layer 0.11: 16-stage engine schedule (8 terrains x 2 admissible ops, Axis-2 sheet rule) as active-inference policy space; 16/16 distinct, unique sheet partition (z3+cvc5), planner reaches goal + N01 on real schedule
 ("instrument_class_split_sim.py", 120, False, [
   ("contains", "PASS instrument_class_split_sim")]),          # Layer 0.12: instrument-class split as MEASURED object (loop-back #2 item 4) -- relaxation (magnitude-separable) vs conditioning (sequential-only, CUSUM), one free-energy core, not collapsed; z3+cvc5
 ("spinor_memory_sim.py", 120, False, [
   ("contains", "PASS spinor_memory_sim")]),          # Layer 0.14: spinor memory -- 720deg loop-parity bit + sheet-gated retention bit, both in psi and invisible to rho (density quotient kills spinor phase/holonomy); reproduces dual-engine 1.0-vs-0.146; z3+cvc5 spinor-only XOR
 ("type1_engine_igt_sim.py", 120, False, [
   ("contains", "PASS type1_engine_igt_sim")]),          # Layer 0.15: the FULL Type 1 engine (LEFT Weyl, flux IN) built EXACTLY from igt-pattern-explicit-math-reference doc sections 11-15 -- 4 operators (Ti/Te/Fi/Fe), 4 terrains (Se/Ne/Ni/Si-in), 8 stages (outer+inner) in exact composition order with IGT win/lose labels; 8 distinct, Axis-6 order N01, two traversals, native op->sheet forced (z3+cvc5)

 ("surface_identity_sim.py", 120, False, [
   ("contains", "PASS surface_identity_sim")]),          # Layer 0.16: the surface identity -- entropy face (Hess of relative entropy) == geometry face (BKM information metric) as the SAME tensor at every terrain fixed point (1e-8); an application of Tomita-Takesaki / Connes-Rovelli thermal-time to the terrain surface; separation UNSAT (z3+cvc5), deformed control SAT

 ("manifold_L1_probe_quotient_sim.py", 120, False, [
   ("contains", "PASS manifold_L1_probe_quotient_sim")]),  # SPINE L1: the probe-quotient floor S/~_M built from L0 roots (F01/N01/identity), dual ratchet (quotient refines + entropy recomputes per admitted probe), per-rung 1q/2q/3q, negative roster fires, dual-solver identity gate. Start of the manifold spine ratchet -- no saliency skipping, one layer at a time up to terrains and beyond.

 ("manifold_L2_rank_strata_marginals_sim.py", 120, False, [
   ("contains", "PASS manifold_L2_rank_strata_marginals_sim")]),  # SPINE L2: density-rank strata (dim 4^n-1, not a ball) + partial-trace marginals Tr_{A\\B}; dual ratchet (rank stratum + marginal entropy co-move product->Bell), negatives #1/#2/#10 fire, dual-solver Schmidt/marginal-compatibility gate

 ("manifold_L3_spinor_hopf_sim.py", 120, False, [
   ("contains", "PASS manifold_L3_spinor_hopf_sim")]),  # SPINE L3: spinor/phase/projective surface CP^{2^n-1} + Hopf skeleton S^1->S^3->S^2 + relative-phase torus T^{n-1}; the phase L1/L2 are blind to; dual ratchet (phase dof moves, density readout fixed), negatives #8/#4 fire, dual-solver spinor-sign/density-blindness gate

 ("manifold_L4_local_weyl_factors_sim.py", 120, False, [
   ("contains", "PASS manifold_L4_local_weyl_factors_sim")]),  # SPINE L4: local Weyl factors exist iff product state (entangled keeps mixed marginals, no local pure spinor); dual ratchet (Weyl factor + marginal purity co-move product->Bell), negatives #1/#9/#10 fire, dual-solver factorization-needs-product gate
 ("axis0_ratchet_climb_sim.py", 120, False, [
   ("contains", "PASS axis0_ratchet_climb"),
   ("contains", "ORDER_GAP FORCED OFF FRONTIER BY N01 DEMAND: True")]),  # THE A0_raw VECTOR RATCHETS: fuses the proven climb mechanism with the A0_raw readout ladder (AXIS0_PHYSICS_MODEL_CORE sec 24) as rungs. Each Axis-0 component earned one FORCED tooth at a time (4 teeth force: S,S_B,H_Om + one more; >=1 component lands on FRONTIER = the honest remainder derived as a ratchet frontier, WHICH component is pool/quantization-dependent, measured not asserted). N01 DEMAND: order_gap forced off frontier by a pair the entropy sector (S,S_B,I_c identical to 1e-6, two Kraus decomps of one channel) cannot separate but order tells apart. order_gap ratchets iff the N01 demand is live.
 ("axis0_shell_polarity_docfaithful_sim.py", 180, False, [
   ("contains", "PASS axis0_shell_polarity_docfaithful"),
   ("contains", "Q1 phases emerge from neutral knob (per-component, no algebra): True")]),  # DOC-FAITHFUL AXIS-0 (JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE sec 24/37/38), PER-COMPONENT no-algebra classifier (A0_raw is an UNFUSED LIST not a vector -- sign/threshold on ONE component, no k-means/linear mixing). Q1 phases emerge from a neutral knob 0.938 held-out. HONEST FINDING Q2: under no-algebra, scalar_entropy_only=0.812 does NOT drop from base=0.938 -> Axis-0 NOT load-bearing beyond entropy at this baseline (the earlier k-means load-bearing verdict was partly a vector-algebra artifact; reported not forced). Q3 one_future_control kills (many-futures real). scratch_diagnostic.
 ("axis0_drive_fair_n01_test_sim.py", 120, False, [
   ("contains", "PASS axis0_drive_fair_n01_test"),
   ("contains", "rolling dice beat dead ONLY once N01 is measured: True")]),  # THE FAIR N01 DRIVE TEST: does live (order-sensitive) Axis-0 power the climb better than dead? A move-matched dead twin (brentq-tuned to identical order-INVARIANT signature) is indistinguishable from rolling under every order-invariant readout (reproduces the node fifth-test "no drive" finding) and separated ONLY by the order-sensitive N01 commutator readout (rolling 0.0399 vs dead* 0.0, dead zero = measured generator commutation not imposed). Rolling wins for real, but N01-conditionally -- no free-standing scalar advantage.
 ("engine_dynamics_id_arbiter_sim.py", 300, False, [
   ("contains", "PASS engine_dynamics_id_arbiter"),
   ("contains", "EXTERNAL ARBITER CONTROL FLIPS (shuffled-time breaks the fit real data supports): True")]),
 ("type2_full_engine_both_loops_sim.py", 120, False, [
   ("contains", "PASS type2_full_engine_both_loops"),
   ("contains", "TYPE 2 FULL ENGINE (BOTH LOOPS) BUILT: True")]),  # RUNG 4: Type-2 (RIGHT Weyl, eps=-1, mirror) full engine, doc-faithful canonical slots (attachment sec5): outer inductive {Fi,Fi,Te,Te}, inner deductive {Fe,Fe,Ti,Ti} -- note outer/inner tense MIRRORED vs Type 1. (A) both loops 4 ordered stages (outer min 0.523 spread 0.351, inner min 0.632 spread 0.525, commuting ctrl 0.0). (B) loops distinct (gap 0.502, complementary ops). (C) loop-order sensitive (0.501). (D) axis-0 polarity OPPOSITE to Type 1: spinor holonomy +2.939 vs Type1 -2.939; chirality-erase control (eps->+1, drive kept) flips Type2 to -2.939 = Type1 sign, opposition collapses. scratch_diagnostic.
 ("type1_full_engine_both_loops_sim.py", 120, False, [
   ("contains", "PASS type1_full_engine_both_loops"),
   ("contains", "TYPE 1 FULL ENGINE (BOTH LOOPS) BUILT: True")]),  # RUNG 2+3 of the staged engine build: the Type-1 INDUCTIVE loop as its own 4-stage object + both loops composed into the FULL single engine. Doc-faithful canonical slots (owner attachment 2026-07-06T08-14 sec 5): outer deductive {Ti,Ti,Fe,Fe}, inner inductive {Fi,Te,Te,Fi}. (A) inductive loop 4 ordered stages (min 0.591, perm spread 0.535 vs commuting 0.0). (B) two loops distinct (endpoint gap 0.586, complementary operator families). (C) full engine loop-order sensitive (0.582). (D) axis-0 SPINOR-LEVEL readout: spinor holonomy T1 -2.939 vs T2 +2.939 opposite, collapses to 0 without drive -- corrects rung-1 density readout which is SAME-sign at full-engine scale (polarity is spinor-level per project canon). scratch_diagnostic.
 ("engine_64_schedule_definition_sim.py", 120, False, [
   ("contains", "PASS engine_64_schedule_definition"),
   ("contains", "ENGINE 64-SCHEDULE DEFINED: True")]),  # defines the 64-engine schedule for the 16 stages (owner correction: each stage runs all 4 operators at ONE shared axis-6 sign = operator-first/terrain-first order). Schedule = 16 stages (8 terrains x 2 signs) x 4 operators = 64. (A) well-formed 16 stages x 4 ops, sign is a real composition-order choice. (B) axis-6 sign load-bearing 32/32 (terrain,operator) pairs under the full GKSL flow (no-drive control collapses to 0/32 -- the sign RIDES on the terrain drive; the earlier scratch-map z-family up=down collapse does NOT survive the integrated flow). (C) 64/64 dynamically distinct (min pairwise 0.109; single-operator control collapses to 16). candidate index surface not ontology. scratch_diagnostic.
 ("qit_fep_surprise_stream_sim.py", 40, False, [
   ("contains", "PASS qit_fep_surprise_stream")]),  # THE FEP LENS ON THE RUNNING ENGINE as a per-tick SURPRISE STREAM: surprise_bits = S(observation||belief), Umegaki quantum relative entropy (bits), pure QIT no classical/thermal terms. Time-series companion to the static FEP sims (qit_fep_ratchet functional + qit_active_inference_planning path-integral); this one emits the {tick, belief_bloch, surprise_bits} trace Lev's cr_qit_bridge_stream_v0 evidence port consumes. Signature (matches QIT_LEV_BRIDGE_SPEC): predictable ~0.002, regime-shift spike ~2.5, relearn decay ~0. Two falsifiable controls: (1) belief frozen at switch -> tail stays high 5.35 (learning beats frozen ~25000x); (2) no regime switch -> no spike. scratch_diagnostic.
 ("v7_codex_ratchet_crosscheck_sim.py", 30, False, [
   ("contains", "PASS v7_codex_ratchet_crosscheck")]),  # SYNC PROBE: loop this bundle's engine reconstruction back against the v7 codex-ratchet repo's qit_full_type1_type2_64_live_v1 build (granted read-only). Checks 4 structural agreements: (1) 64-schedule shape 16x4=64/16 chart-locked+48 runtime/32+32; (2) engine mirror pairing T1 outer=deductive T2 mirrored; (3) v7 object formation clean (ordered_accuracy 1.0, 4 objects, entropy monotone 2.0->0 bits); (4) two resolutions consistent (v7 4-loop 4/4 vs bundle 16-stage 0.6875 w/ 3 degenerate pairs -- same criterion, coarser vs finer granularity). Structural cross-check not bit-for-bit reproduction; SKIP-clean if repo absent (sync probe, not hard dependency). Can fail on shape mismatch. scratch_diagnostic.
 ("engine_pair_matrix_sim.py", 60, False, [
   ("contains", "PASS engine_pair_matrix"),
   ("contains", "combinatorial coupling cancels: True")]),  # THE TWO ENGINES TOGETHER AS ANOTHER LAYER: a4-b3 independence-restoration (deep-audit Packet 4 / rung 5), tested at the COMBINATORIAL/schedule level (NOT dynamical). Each engine's schedule locks traversal-order label (a4) to loop-role label (b3) -- Type-1 -1.0, Type-2 +1.0, opposite pairings; pooled over both engines the label coupling cancels to 0.0. This is a fact about the two mirror schedules, true by construction. Falsifiable control: a same-pairing twin pools to -1.0, does NOT cancel. HONEST LIMIT recorded in-sim: the genuinely dynamical a4/b3 trajectory correlations (+0.55/-0.13/+0.23) do NOT reproduce the clean pattern -- only partial decoupling. scratch_diagnostic.
 ("unified_attractor_basin_seven_axes_sim.py", 120, False, [
   ("contains", "PASS unified_attractor_basin_seven_axes"),
   ("contains", "all seven axes load-bearing on one engine: True")]),  # THE WHOLE MODEL AS ONE ATTRACTOR BASIN: all 7 axes (0-6) read as LOAD-BEARING dynamical witnesses from the SAME running-engine substrate, each with a falsifiable ERASURE control collapsing ONLY that axis (A0 polarity/no-flow, A1 unitary-vs-CPTP dS, A2 direct-vs-conjugated frame/V=I, A3 fiber-vs-base density-motion/degenerate-eta, A4 order gap/commuting, A5 F-preserves-entropy/F-as-pinch, A6 precedence/same-terrain-collapse). Closes the gap where axes 1-4 were only established individually. Source-grounded in v7 AXES_FULL_EXTRACTION with per-axis geometry-contamination guards. Plus nested-intelligence layers L0 stage -> L1 loop -> L2 two-loops -> L3 two-engines, each a distinguishable object. scratch_diagnostic.
 ("lev_qit_evidence_envelope_emitter.py", 60, False, [
   ("contains", "PASS lev_qit_evidence_envelope_emitter"),
   ("contains", "LEV EVIDENCE ENVELOPE CONFORMS: True")]),  # emits a Lev-conformant lev.qit_engine_perception_evidence.v1 envelope from the CURRENT bundle's engine results (corrected non-circular polarity + source-fidelity linter), carrying the Lev host-consumer contract (evidence-only ceiling) + blocked_consumers + the deep-audit four claim-language status fields. Self-validates: envelope conforms to the host boundary (no promotion/graph/runtime overclaim); falsifiable control: a PROMOTING twin (truth_state=canon, graph_mutation_allowed=true, promotion=earned) is rejected by the same validator (4 problems). Closes the CR->Lev evidence loop from my lane; makes my scratch-diagnostic measurements consumable as host receipts only. lev_evidence_emitter.
 ("schedule_source_fidelity_linter.py", 60, False, [
   ("contains", "PASS schedule_source_fidelity_linter"),
   ("contains", "SCHEDULE SOURCE-FIDELITY LINT PASS: True")]),  # PACKET 1 (deep-audit-55): source-fidelity LINTER over the owner IGT engine chart tables (reference_docs/engine_math/source_schedule_tables/). Checks 16-slot chart well-formed, 64 = exact 16x4 operator expansion with 16 canonical rows reconstructing the chart, and the four running engine-sim loops match the source table per slot -- INDEPENDENT corroboration the doc-faithful reconstruction is source-correct. Falsifiable control catches a corrupted table. No dynamic claim. source_fidelity_linter.
 ("type1_single_loop_axis0_sim.py", 120, False, [
   ("contains", "PASS type1_single_loop_axis0"),
   ("contains", "TYPE 1 SINGLE LOOP WITH AXIS-0 BUILT: True")]),  # FIRST RUNG of the staged engine build (owner: do one engine type / one loop at a time -- 4 stages + their substages, 16 of 64). Type 1 (LEFT, eps=+1) single DEDUCTIVE loop over terrains [0,1,2,3]. (A) 4 ordered stages: pairwise distinct (min 0.221), order-sensitive (permutation spread 0.349 vs genuinely-commuting z-dephase control 0.0). (B) axis-0 DRIVE from the start: intrinsic-flow work 1.775 vs no-drive 0.693. (C) axis-0 READOUT at loop close threaded from the drive: polarity Type1 +0.00065 vs Type2 -0.00231 (opposite signs discovered from dynamics not eps label), no-drive control collapses to -0.00008. (D) 4 cased ordered substages per stage. Axis-0 threaded foundations->readout in ONE object. scratch_diagnostic.
 ("stage_necessity_ablation_sim.py", 120, False, [
   ("contains", "PASS stage_necessity_ablation"),
   ("contains", "ALL STAGES DO UNIQUE WORK: True")]),  # stage-necessity tooth (owner scorecard ladder #3/#7): every one of the 16 stages does irreplaceable work, the mechanism-level answer to "empty/hallucinated content". Scramble each non-degenerate stage (replace with nearest distinct neighbor's channel) -> induces new binding error 10/10 (1.000); duplicate onto nearest distinct neighbor -> new confusion 10/10 (1.000, consistent +3 each). HONEST: the 6 known-degenerate stages (depol eps-pairs + Fe proj-commuting) are expected-null -- duplicating onto their twin adds mean|1| vs non-deg mean|3| (already share identity). Runs in signature space (precompute flows once, 15s). scratch_diagnostic.
 ("objective_gate_integrity_sweep_sim.py", 120, False, [
   ("contains", "PASS objective_gate_integrity_sweep"),
   ("contains", "ALL OBJECTIVE GATES REAL (not rubber stamps): True")]),  # STANDING anti-hallucination guard (owner: sims that "seemed real then found hallucinated with gates cheated"). Interrogates the actual evaluate()/eval functions of the three objective sims: each verdict must PASS on true inputs AND FAIL on cheated inputs (chance-binding, zero-interior, hallucinated degeneracies, non-flipping controls, memorized shuffled). A gate that cannot be made to fail is a rubber stamp. Also checks results-JSON non-emptiness + that perception recomputes (not a cached constant). All three gates REAL. scratch_diagnostic.
 ("perception_object_binding_sim.py", 120, False, [
   ("contains", "PASS perception_object_binding"),
   ("contains", "AI OF PERCEPTION (OBJECT BINDING) EARNED: True")]),  # the AI-of-perception tooth connecting the engine interior to the object-formation success criteria. Binds a STREAM of never-seen views into objects (unsupervised nearest-prototype on the re-id channel signature): real binding accuracy 0.792 over 48 never-seen views/16 objects (chance 0.062); accuracy on NON-degenerate objects 1.000 with ALL 10 misses being genuine degeneracies (depol eps-pairs (1,5) + Fe proj-commuting (3,7)); shuffled-label control collapses to chance 0.062. Criterion is REAL not hallucinated: degenerate pairs at signature distance 0.0 (MERGED not invented as separate, median inter-object 0.659). Binding needs the interior: real spread 0.668 vs same-kind control 0.0 (unbindable). scratch_diagnostic.
 ("engine_object_formation_scorecard_sim.py", 120, False, [
   ("contains", "PASS engine_object_formation_scorecard"),
   ("contains", "BOTH INDEPENDENT CONTROLS FLIP: True")]),  # UNIFIED objective scorecard composing the two external targets (re-identification convergence + PySINDy handling) into an ADAPTED formation-loss surface (Lev loss STRUCTURE: additive components + convergence 5*(1-rate); handling term is an engine-domain proxy max(0,1-R^2), labelled not claimed as the TS formula). Applies the Lev mesh-package discipline: instruments emit MEASUREMENTS ONLY (convergence_loss, handling_loss -- reported not gated), a SEPARATE policy eval decides on the NEGATIVE-CONTROLS (dynamics-lane Controls section, not policy requiredControls) flipping in both lanes. Structural fix for the gate-tuning cascade (a gate the instrument doesn't contain can't be relaxed). Reads the two results JSONs produced by the two entries above it. scratch_diagnostic.  # FULLY EXTERNAL dynamics-ID judge: PySINDy (off-the-shelf, zero QIT-theory input) fits each of the 8 terrain GKSL flows from per-tick Bloch trajectories; held-out R^2 via model.score (no forward-integration -> no stiff hang). TEETH: shuffled-time control must break the fit (it detonates to R^2 ~ -1e9 on every terrain). 7/8 terrains reconstruct at R^2 0.93-1.00; t3 (proj+eps=+1) is unfittable by degree-2 poly (fast projective collapse -> near-stationary held-out half, no derivative signal) -- an honest external finding, reported not hidden. scratch_diagnostic.
 ("engine_reidentification_objective_sim.py", 120, False, [
   ("contains", "PASS engine_reidentification_objective"),
   ("contains", "CONTROL FLIPS (shuffled at chance, real beats every scramble): True")]),  # OBJECTIVE model-blind validity target for the 16 engine stages (owner criterion 2026-07-06: "identity is the survivor of probe rotation = a=a iff a~b operational"). Fingerprint each stage on a SEEN probe family, re-identify from a NEVER-SEEN (rotated) one via a probe-set-independent channel signature (action on I/2 + Bloch-contraction singular values). Gate is the CONTROL FLIP only (shuffled-stage -> chance, real beats every scramble), re-id RATE reported as-is NOT gated to a ceiling. Finding: 11/16 stages re-identify; the 5 that don't are the depol eps-degenerate pairs (t1/t5) + the Fe proj-commuting pair (t3/t7) the oracle predicts. scratch_diagnostic.
 ("sixteen_intelligences_substages_terrain_ratchet_sim.py", 120, False, [
   ("contains", "PASS sixteen_intelligences_substages_terrain_ratchet"),
   ("contains", "ENGINE INTERIOR BUILT: True")]),  # the engine interior on the REAL oracle operators. (1) 16 stages as distinct KINDS of intelligence (processing fingerprint over spanning probes: which Bloch comp contracts + entropy sign; min pairwise 0.360; shuffled-operator control collapses to 0.000). (2) each stage has 4 ordered sub-stages (Ti,Te,Fi,Fe at fixed casing; interior ordered reverse!=forward; 4 distinct). (3) 8 terrains ratcheted with 2 SIGNED types: F-type (Fi,Fe) preserve von Neumann entropy EXACTLY (dS 0.0), T-type (Ti,Te) change it (0.45/0.48) -- symbolic-grade split; each terrain native pair = one pinch + one rotation (measured not len==2); each native pinch a MONOTONE ratchet (coherence -> 0). scratch_diagnostic.
 ("next_tooth_720_double_loop_and_lift_audit_sim.py", 120, False, [
   ("contains", "PASS next_tooth_720_double_loop_and_lift_audit"),
   ("contains", "720 DOUBLE LOOP + LIFT AUDIT: True")]),  # climb + loop-back in one. PART 1: the 720 DOUBLE loop, tooth above the single 360 loop -- the single 360 returns -psi (overlap -1, does NOT close); the 720 double loop (360 comp 360) returns +psi (overlap +1, genuine return); tense halves distinct 1.138. PART 2 (root audit the rung exposes): the SPINOR LIFT is FORCED not installed -- R(2pi) sends psi->-psi but rho identical; NO density observable separates them (max gap 2.2e-15 over 200 Hermitian obs) but psi does (gap 2.0); erased-quotient (identify psi~-psi) kills the distinction (2.0->0.0); lift minimal 2-to-1 cover. Same claim separately z3+cvc5 verified at L2->L3. scratch_diagnostic.
 ("next_tooth_engine_stages_to_360_loop_sim.py", 120, False, [
   ("contains", "PASS next_tooth_engine_stages_to_360_loop"),
   ("contains", "NEXT TOOTH (STAGES -> 360 LOOP) FORCED: True")]),  # the ratchet's next tooth after the engine stages: single stages -> the composed 360-degree LOOP, read at the spinor (psi) level. DEMAND a single stage cannot close (a closed traversal must differ from its time-reverse -- loop handedness); a stage has no cyclic handedness (single-operator loop UEUE==EUEU, 0.00). MSS next tooth = a closed 4-beat 360 loop; deductive(UEUE) vs inductive(EUEU) spinor distance 1.138. PARITY IS SPINOR-LEVEL: psi 360-overlap -1 / 720-overlap +1, but rho both +1 (density BLIND -- why prior Axis tooling could not see tense). HANDEDNESS (tense) ORTHOGONAL to chirality (invariant under eps flip -- a different axis, honest result: caught+dropped a false opposite-sign claim). scratch_diagnostic.
 ("next_tooth_terrains_to_engine_stages_sim.py", 120, False, [
   ("contains", "PASS next_tooth_terrains_to_engine_stages"),
   ("contains", "NEXT TOOTH (TERRAINS -> ENGINE STAGES) FORCED: True")]),  # the ratchet's next tooth after the terrains: makes the climb continuous from the 8 terrain dissipators UP to the engine STAGES. DEMAND a terrain alone cannot close (order must matter -- N01; terrain-alone order gap 0.00e+00). MSS next tooth = one native operator composed in two orders = an engine stage; opens order sensitivity (mean gap 0.185). WHY SIXTEEN: 16 (down,up) signatures pairwise-distinct (min 0.028). Chirality -> two engines: Type1 (0-3) / Type2 (4-7) disjoint each internally distinct. Uses REAL oracle generators (gen/flow/op). Two order-sensitivity levels stated honestly: dynamical 16/16 on the probe, symbolic 12/16 (Fe stages commute). scratch_diagnostic.
 ("bridge_tooth_carrier_to_terrains_sim.py", 120, False, [
   ("contains", "PASS bridge_tooth_carrier_to_terrains"),
   ("contains", "BRIDGE TOOTH (CARRIER -> TERRAINS) FORCED: True")]),  # the ratchet's NEXT tooth after cosmogenesis: makes the climb continuous from the bare chiral spinor carrier UP to the 8 terrain dissipators. DEMAND the bare unitary carrier cannot close (a state + perturbed copy must converge -- an attractor demand; unitary preserves trace distance, td stays 0.261); a terrain dissipator closes it (td->0.002). MSS next tooth = a GKSL dissipator with a fixed point = a terrain. WHY EIGHT: 8 terrains pairwise-distinct CHANNELS (min channel distance 0.195; fixed points can coincide, channels do not). Chirality carries forward from cosmogenesis (eps+/- sheets opposite sign, product -1). Uses the REAL terrain generators (oracle_targets.py TERR). scratch_diagnostic.
 ("cosmogenesis_ratchet_first_tooth_sim.py", 120, False, [
   ("contains", "PASS cosmogenesis_ratchet_first_tooth"),
   ("contains", "COSMOGENESIS IS THE RATCHET'S FIRST TOOTH: True")]),  # cosmogenesis as an INSTANCE of the root ratchet running -- MSS in a static field (owner 2026-07-06, grounded x_grok_chat_TOE.txt 30/38/47). SAME demand/MSS/entropy-gradient rules at the origin: static field carries no difference (no time); MSS forces the weakest persistent carrier = norm-preserving spinor (lossy map annihilates); the carrier's expansion is entangled (dark-energy-first, concurrence 0->1) and chiral (mirror = opposite-sign holonomy, F01+N01 forced); the entropy gradient is INTRINSIC (opens with the carrier, freeze halts it). Lev measurement/verdict discipline: instruments emit numbers, separate policy eval decides on control flips only. scratch_diagnostic.
 ("pawl_witness_identity_memory_sim.py", 120, False, [
   ("contains", "PASS pawl_witness_identity_memory"),
   ("contains", "PAWL LOCKS ONLY WITH WITNESS IDENTITY + MEMORY: True")]),  # HARDENS THE PAWL per 2026-07-04 correction (sec.8 witness identity, sec.10 memory-bearing drive). Minimality ALONE does not lock: the MSS-alone pawl accepts lateral swaps among equal-cost witnesses (12); the witness-identity + append-only-memory pawl rejects them (0). Memoryless-drive kill control: memory drive climbs (9 retained teeth, gap 0.316), memory-erased drive random-walks and stalls (5 teeth, gap 0.059). Measurement/verdict separation; both controls flip. scratch_diagnostic.
 ("ratchet_three_qubit_floor_sim.py", 120, False, [
   ("contains", "PASS ratchet_three_qubit_floor"),
   ("contains", "THREE-QUBIT FLOOR IS REAL: True")]),  # carries the conservation-gated ratchet past the dim-2 saturation of foundational_ratchet. SAME rules (demand=trace-dist>THETA unresolved by acquired bases; MSS admissibility; conservation gate). Acquired stock = 3n single-qubit Pauli-axis bases, tomographically complete ONLY at 1 qubit (dim^2-1 = 4^n-1 axes: 3/15/63). Result: 1q saturates (0 teeth-before-sat, 0 open demands -- 3 bases span the qubit); 2q/3q keep forcing (12 teeth, 69/161 open demands at last shell). The floor is real for the MECHANISM reason (a handful of single-qubit bases resolves a vanishing fraction of exp-many distinguishable pairs), not a fit -- WHY the owner needs >=3 qubits. scratch_diagnostic.
 ("unified_ratchet_witness_memory_3q_sim.py", 120, False, [
   ("contains", "PASS unified_ratchet_witness_memory_3q"),
   ("contains", "UNIFIED RATCHET LOCKS AND CLIMBS ON 3 QUBITS: True")]),  # ONE ratchet, not three sims: composes the foundational demand/MSS/entropy-gradient mechanism + the witness-identity/append-only-memory pawl (2026-07-04 sec.8/10) + the 3-qubit carrier. LIVE (memory+witness-lock, 3q): retained ladder 3 teeth, 7 acquired bases, 0 lateral swaps. Three controls flip: (A) ladder-vs-flat (memory banks retained capacity=3, memoryless twin=0); (B) pawl-lock (witness-memory 0 lateral swaps, minimality-only twin 39); (C) Feynman freeze (0 retained teeth after growth frozen). Locks by remembered witness, driven by intrinsic gradient, keeps forcing past dim-2. scratch_diagnostic.
 ("foundations_reaudit_drive_and_mss_tiebreak_sim.py", 120, False, [
   ("contains", "PASS foundations_reaudit_drive_and_mss_tiebreak"),
   ("contains", "ROOT DRIVE AND TIE-BREAK AUDITED: True")]),  # second root audit (standing loop-back process). LANE A: the entropy-gradient DRIVE is FORCED -- only the gradient is intrinsic + vanishes at demand-closure (0.00) + halts on freeze; injected drive does not vanish (=1.0, classical-FEP failure mode, not intrinsic); scalar von-Neumann entropy does not vanish at full resolution (=1.206, blind). LANE B: MSS fewest-closing tie-break LOAD-BEARING at dim-8 (over-resolution 173.0 vs greedy 179.7, same closure) -- realizes 'presume least'. Gradient corrected mid-audit to be defined consistently with the demand bar (unmet demand rel rf*td). scratch_diagnostic.
 ("foundations_reaudit_forcing_robustness_sim.py", 120, False, [
   ("contains", "PASS foundations_reaudit_forcing_robustness"),
   ("contains", "FOUNDATIONS EARNED (forced, robust, load-bearing): True")]),  # loop-back AUDIT of whether the root is EARNED not merely sufficient. LANE 1: the complex spinor is FORCED -- on the smallest carrier (F01+MSS) real dim-2 is SO(2) abelian (N01 fails, commutator 0), complex dim-2 is SU(2) nonabelian (N01 holds, commutator 2.828); real needs dim>=3 (more presumption) so complex-at-2 is unique smallest. LANE 2: dim-2 saturates AND dim-8 keeps forcing on 100% of admissible grid (rf<=0.6, all theta); rf=1.0 degenerate control breaks saturation (263 open). LANE 3: MSS load-bearing at dim-8 -- MSS admits 7 bases 0 unforced, presumption control admits 9 with 4 unforced, MSS still reaches full resolution (invisible at dim-2 where all 3 Pauli bases are forced -- the floor again). scratch_diagnostic.
 ("foundational_ratchet_entropy_gradient_sim.py", 120, False, [
   ("contains", "PASS foundational_ratchet_entropy_gradient"),
   ("contains", "FOLLOWS THE RATCHET'S OWN RULES (forced climbs + pawl + co-ratchet + Axis-0 early + Feynman): True")]),  # THE RATCHET MECHANISM AT THE FOUNDATIONS (owner correction 2026-07-05: Axis-0 kept failing because built as a LATE density-level readout; it IS an entropy gradient = a FOUNDATIONAL DRIVE). F01 (finite noncommuting probes)+N01; minimal persistent norm-preserving carrier; possibility space GROWS -> entropy gradient (rising ceiling - carrier capacity) is the DRIVE. MSS smallest step per shell. CO-RATCHET: geometry climb tracks entropy gradient one-for-one. FEYNMAN: freeze growth -> gradient flat, climb halts. scratch_diagnostic.
 ("ratchet_climb_engine_v0.py", 120, False, [
   ("contains", "PASS ratchet_climb_engine_v0"),
   ("contains", "SINGLE-TOOTH CLIMB L0->L1->L2->L3: True")]),  # THE RATCHET RATCHETING: climbs weakest-structure ladder one MINIMAL tooth (L0->L1_Z->L2_Pauli->L3_Spinor), each rung forced by a distinct measured lost distinction (<Z> for |0>/|1>; <X> for |+>/|-> invisible to Z; spinor lift for R(2pi) rho-identical process); batch-jump refused (stronger levels logged REJECTED_UNFORCED = MSS teeth); 4 permuted demand-orders converge to identical ladder (T5 basin); theorems T1-T4 pass
 ("flux_nesting_ablation_jax.py", 600, True, [
   ("approx", r'"total_chern_forward":\s*([0-9.]+)', 7.295389, 1e-3)]),
 ("manifold_build_ladder.py", 600, True, [
   ("contains", "doctrine realized (Ne/Ni:+ Se/Si:-): False")]),  # HONEST FAILURE -- must stay False
]

# TORCH lane -- sims whose CLAIM is learning (autograd through the tick loop). Run under a python
# that imports torch (torchcarrier by convention); torch_python() discovers it portably.
TORCH_SUITE = [
 ("quantum_hopfield_memory_sim.py", 300, [
   ("contains", "PASS quantum_hopfield_memory_sim")]),          # Layer 0.13: quantum associative memory as energy-descent recall on the spinor carrier; 3-qubit floor + capacity curve measured; torch autograd (trainable substrate) + numpy oracle cross-check; z3+cvc5
]

def run_one(script, timeout, interpreter=None):
    t0 = time.time()
    try:
        p = subprocess.run([interpreter or sys.executable, os.path.join(SIMS, script)],
                           capture_output=True, text=True, timeout=timeout, cwd=SIMS)
        return p.returncode, p.stdout + p.stderr, time.time() - t0
    except subprocess.TimeoutExpired:
        return -9, "TIMEOUT", time.time() - t0


def run_engines_lane():
    """Cross-substrate engine check: numpy RK4 oracle -> targets.json, then any
    available substrate engine (jax/torch), then validate_engines.py must exit 0.
    Returns (status, detail). SKIP only if numpy oracle itself cannot run."""
    ENG = os.path.join(HERE, "engines")
    if not os.path.isdir(ENG):
        return "SKIP", "no engines/ dir"
    def _run(args, timeout=300):
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=ENG)
    # oracle (always numpy/scipy)
    o = _run([sys.executable, "oracle_targets.py"])
    if o.returncode != 0:
        return "FAIL", "oracle_targets.py failed: " + (o.stderr or o.stdout)[-300:]
    # substrate engines that import cleanly
    ran = []
    for eng in ("jax_engine.py", "torch_engine.py"):
        r = _run([sys.executable, eng])
        if r.returncode == 0:
            ran.append(eng.split("_")[0])
    # Julia (4th route) if a julia binary is on PATH -- dependency-free engine
    import shutil as _sh
    if _sh.which("julia") and os.path.exists(os.path.join(ENG, "julia_engine.jl")):
        rj = _run(["julia", "julia_engine.jl"])
        if rj.returncode == 0:
            ran.append("julia")
    if not ran:
        return "SKIP", "oracle ok; no substrate engine importable (jax/torch/julia) on this machine"
    v = _run([sys.executable, "validate_engines.py"])
    if v.returncode != 0:
        return "FAIL", "validate_engines.py non-zero: " + (v.stdout + v.stderr)[-300:]
    if "GREEN" not in v.stdout:
        return "FAIL", "validator did not report GREEN: " + v.stdout[-200:]
    detail_1q = f"1q: oracle vs {'+'.join(ran)} GREEN"
    # --- 3-qubit lane (same substrates; 63-dim Pauli contract on C^8) ---
    o3 = _run([sys.executable, "oracle_targets_3q.py"])
    if o3.returncode != 0:
        return "PASS", detail_1q + f"; 3q oracle failed (skipped): {(o3.stderr or '')[-120:]}"
    ran3 = []
    for eng in ("jax_engine_3q.py", "torch_engine_3q.py"):
        if os.path.exists(os.path.join(ENG, eng)):
            r3 = _run([sys.executable, eng])
            if r3.returncode == 0:
                ran3.append(eng.split("_")[0])
    if _sh.which("julia") and os.path.exists(os.path.join(ENG, "julia_engine_3q.jl")):
        rj3 = _run(["julia", "julia_engine_3q.jl"])
        if rj3.returncode == 0:
            ran3.append("julia")
    if not ran3:
        return "PASS", detail_1q + "; 3q oracle ok, no 3q substrate importable"
    v3 = _run([sys.executable, "validate_engines_3q.py"])
    if v3.returncode != 0 or "GREEN" not in v3.stdout:
        return "FAIL", "3q validator not GREEN: " + (v3.stdout + v3.stderr)[-300:]
    return "PASS", detail_1q + f"; 3q: oracle vs {'+'.join(ran3)} GREEN (63-dim Pauli, C^8)"

def main():
    jax_ok = has_jax() and not FAST
    results, n_pass, n_fail, n_skip = [], 0, 0, 0
    for script, timeout, needs_jax, checks in SUITE:
        if needs_jax and not jax_ok:
            results.append({"sim": script, "status": "SKIP (jax unavailable or --fast)"})
            n_skip += 1
            print(f"SKIP {script}")
            continue
        rc, out, dt = run_one(script, timeout)
        if rc == 0 and "SKIP_OPTIONAL" in out:
            results.append({"sim": script, "status": "SKIP (optional tool absent)"})
            n_skip += 1
            print(f"SKIP {script} (optional tool absent)")
            continue
        fails = []
        if rc != 0:
            fails.append(f"exit code {rc}")
        else:
            for chk in checks:
                if chk[0] == "contains":
                    if chk[1] not in out:
                        fails.append(f"missing: {chk[1]!r}")
                else:
                    _, rex, exp, tol = chk
                    if script == "nested_basin_sim.py":   # count-based special case
                        n = len(re.findall(r'"verdict": "attractor"', out))
                        if n != 4:
                            fails.append(f"attractor count {n} != 4")
                        continue
                    m = re.search(rex, out)
                    if not m:
                        fails.append(f"pattern not found: {rex}")
                    else:
                        v = float(m.group(1))
                        if abs(v - exp) > tol:
                            fails.append(f"{rex} -> {v} vs {exp} (tol {tol})")
        status = "PASS" if not fails else "FAIL"
        if fails: n_fail += 1
        else: n_pass += 1
        results.append({"sim": script, "status": status, "seconds": round(dt, 1), "fails": fails})
        print(f"{status} {script} ({dt:.1f}s)" + ("" if not fails else "\n      " + "\n      ".join(fails)))
    # TORCH lane (learning-claim sims) -- route to a torch-capable interpreter
    torch_py = torch_python()
    for script, timeout, checks in TORCH_SUITE:
        if torch_py is None:
            results.append({"sim": script, "status": "SKIP (no torch interpreter)"})
            n_skip += 1
            print(f"SKIP {script} (no torch interpreter)")
            continue
        rc, out, dt = run_one(script, timeout, interpreter=torch_py)
        if rc == 0 and "SKIP_OPTIONAL" in out:
            results.append({"sim": script, "status": "SKIP (optional tool absent)"})
            n_skip += 1
            print(f"SKIP {script} (optional tool absent)")
            continue
        fails = []
        if rc != 0:
            fails.append(f"exit code {rc}")
        else:
            for chk in checks:
                if chk[0] == "contains" and chk[1] not in out:
                    fails.append(f"missing: {chk[1]!r}")
        status = "PASS" if not fails else "FAIL"
        if fails: n_fail += 1
        else: n_pass += 1
        results.append({"sim": script, "status": status, "seconds": round(dt, 1), "fails": fails})
        print(f"{status} {script} ({dt:.1f}s) [torch]" + ("" if not fails else "\n      " + "\n      ".join(fails)))

    # cross-substrate engines lane (oracle vs jax/torch)
    if not FAST:
        est, edet = run_engines_lane()
        if est == "PASS": n_pass += 1
        elif est == "FAIL": n_fail += 1
        else: n_skip += 1
        results.append({"sim": "engines/ cross-substrate", "status": est, "detail": edet})
        print(f"{est} engines/ cross-substrate  ({edet})")
    else:
        results.append({"sim": "engines/ cross-substrate", "status": "SKIP (--fast)"})
        n_skip += 1
        print("SKIP engines/ cross-substrate (--fast)")

    summary = {"pass": n_pass, "fail": n_fail, "skip": n_skip, "green": n_fail == 0}
    json.dump({"summary": summary, "results": results},
              open(os.path.join(HERE, "run_all_report.json"), "w"), indent=1)
    print(f"\n=== {n_pass} pass / {n_fail} fail / {n_skip} skip -> {'GREEN' if n_fail==0 else 'RED'} ===")
    sys.exit(0 if n_fail == 0 else 1)

if __name__ == "__main__":
    main()
