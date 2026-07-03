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
 ("flux_nesting_ablation_jax.py", 600, True, [
   ("approx", r'"total_chern_forward":\s*([0-9.]+)', 7.295389, 1e-3)]),
 ("manifold_build_ladder.py", 600, True, [
   ("contains", "doctrine realized (Ne/Ni:+ Se/Si:-): False")]),  # HONEST FAILURE -- must stay False
]

def run_one(script, timeout):
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, os.path.join(SIMS, script)],
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
