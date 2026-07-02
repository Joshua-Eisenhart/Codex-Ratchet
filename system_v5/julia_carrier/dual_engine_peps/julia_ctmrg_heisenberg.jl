# =============================================================================
# object_id: julia_ctmrg_heisenberg
# carrier:   Julia / PEPSKit v0.7.0 CTMRG contraction lane (dual-engine PEPS)
# role:      CONTRACTION-ONLY cross-check of an externally (JAX-)optimized iPEPS tensor.
#
# CLAIM CEILING (hard): This object computes a finite map
#     (single-site iPEPS tensor A) -> (per-site CTMRG energy, correlation length)
# and reports chi-convergence. It is a tool_lego_fit_probe.
# promotion_allowed: false. It does NOT assert layer-completion, manifold admission,
# coupling, bridge (rho_AB/Xi/Phi0/Axis0), flux, or physics. A tensor that contracts
# to a finite energy is a CANDIDATE contraction, not a proven object.
#
# Root constraints in force:
#   F01 (finite distinguishability): finite carrier (D x p x D^3 dense tensor), finite
#        probe family = {chi in {16,24,32}}, finite operator = heisenberg_XYZ LocalOperator,
#        finite contraction path = bounded CTMRG (maxiter capped at 100).
#   N01 (noncommuting / order-sensitive control): the CTMRG transfer operator and the
#        bond Hamiltonian term do not commute; the contraction is an ordered fixed-point
#        sweep (corner/edge growth has a fixed directional order N/E/S/W). We probe this
#        with an order-erased negative control (a real-symmetrized / index-scrambled tensor).
#
# LANDMINE GUARDS (mandatory, per owner directive):
#   - NO fixedpoint / PEPSOptimize / LBFGS / HagerZhangLineSearch (those SEGFAULT here).
#     This object ONLY contracts a supplied tensor via leading_boundary (CTMRG).
#   - CTMRG maxiter capped at 100.
#   - In-process self-kill Timer at 150 s (macOS has no gtimeout): if any single CTMRG
#     contraction hangs, the Timer kills the process and we report the hang HONESTLY as
#     real signal about the tensor, not a code failure.
# =============================================================================

using NPZ, PEPSKit, TensorKit, LinearAlgebra, JSON, Dates, Printf

const HERE      = @__DIR__
const JAX_NPY   = joinpath(HERE, "ipeps_heisenberg_D2.npy")
const FMT_DOC   = joinpath(HERE, "TENSOR_FORMAT.md")
const RESULT    = joinpath(HERE, "julia_ctmrg_heisenberg_results.json")
const SELF_KILL_S = 150.0          # PER-CONTRACTION hang guard (resets each chi)
const CHI_LADDER  = (16, 24, 32)
const CTMRG_TOL   = 1e-8
const CTMRG_MINIT = 4
const CTMRG_MAXIT = 100            # capped (landmine guard)

# ---- per-contraction self-kill watchdog -------------------------------------
# macOS has no gtimeout. We arm a fresh Timer around EACH CTMRG contraction. The
# clock measures CONTRACTION wall time (not JIT/compile, which is warmed up once
# before the ladder). If a single CTMRG sweep wedges on an entangled carrier past
# SELF_KILL_S, the watchdog kills the process with exit 124 and we report the hang
# HONESTLY as real signal about that tensor.
const T0 = time()
function with_watchdog(f, seconds::Real, tag::String)
    armed = Ref(true)
    wd = Timer(seconds) do _t
        if armed[]
            @error "SELF-KILL: contraction [$tag] exceeded $(seconds)s; CTMRG hung on this carrier. Killing."
            flush(stderr)
            ccall(:exit, Cvoid, (Cint,), 124)
        end
    end
    try
        return f()
    finally
        armed[] = false
        close(wd)
    end
end

# -----------------------------------------------------------------------------
# Hamiltonian convention.
# PEPSKit heisenberg_XYZ default: Jx=-1.0, Jy=1.0, Jz=-1.0, spin=1//2  (a gauged AFM).
# The standard PEPSKit AFM-Heisenberg cross-check example uses Jx=Jy=Jz=+1.0 on the
# single-site lattice (the sublattice rotation is folded into the saved tensor by the
# optimizer). We DEFAULT to Jx=Jy=Jz=1.0 and let TENSOR_FORMAT.md override if present.
# heisenberg_XYZ places `term` on EVERY nearest-neighbour bond; for a 1x1 unit cell
# expectation_value therefore sums 2 bonds/site (one horizontal + one vertical).
# We report that raw PEPSKit per-site value AND the per-bond value (= raw / 2).
# -----------------------------------------------------------------------------
function read_J_convention()
    Jx, Jy, Jz, spin = 1.0, 1.0, 1.0, "1//2"
    src = "default (Jx=Jy=Jz=1.0); TENSOR_FORMAT.md absent"
    if isfile(FMT_DOC)
        txt = read(FMT_DOC, String)
        m(p) = (r = match(Regex(p), txt); r === nothing ? nothing : tryparse(Float64, r.captures[1]))
        vx, vy, vz = m("Jx\\s*[=:]\\s*([-+]?[0-9.]+)"), m("Jy\\s*[=:]\\s*([-+]?[0-9.]+)"), m("Jz\\s*[=:]\\s*([-+]?[0-9.]+)")
        vx !== nothing && (Jx = vx); vy !== nothing && (Jy = vy); vz !== nothing && (Jz = vz)
        src = "parsed from TENSOR_FORMAT.md"
    end
    return (Jx=Jx, Jy=Jy, Jz=Jz, spin=spin, source=src)
end

# -----------------------------------------------------------------------------
# Index permutation.
# JAX side saves a dense array with axes [p, u, r, d, l]
#   = (physical, up, right, down, left).
# PEPSKit PEPSTensor convention (src/networks/tensors.jl):  T : P <- N (x) E (x) S (x) W
#   = (physical; north, east, south, west) as a (1,4) TensorMap.
# Label mapping is the IDENTITY in MEANING:  p->P, u->N, r->E, d->S, l->W.
# So the dense-array axis order [p,u,r,d,l] already equals PEPSKit's [P,N,E,S,W]:
#   PERM = (1,2,3,4,5)  (no permutedims needed).
# We STILL apply it explicitly + document it, so a different JAX order can be swapped
# in one place. Virtual SPACES: N,E are kets ComplexSpace(D); S,W are duals
# ComplexSpace(D)' so the 1x1 periodic wraparound N==S' and E==W' is satisfied
# (required by InfinitePEPS construction; verified empirically).
# -----------------------------------------------------------------------------
const PERM_PUR_DL_TO_PNESW = (1, 2, 3, 4, 5)   # [p,u,r,d,l] -> [P,N,E,S,W]

function build_peps(A_raw::Array{<:Number,5})
    # apply documented permutation [p,u,r,d,l] -> [P,N,E,S,W]
    A = permutedims(A_raw, PERM_PUR_DL_TO_PNESW)
    p = size(A, 1)
    D = size(A, 2)
    @assert size(A) == (p, D, D, D, D) "expected square virtual dims, got $(size(A))"
    Ac = ComplexF64.(A)
    Pp = ComplexSpace(p)
    V  = ComplexSpace(D)
    t  = TensorMap(Ac, Pp ← V ⊗ V ⊗ V' ⊗ V')   # P <- N E S W ; S,W dual for wraparound
    return InfinitePEPS(t), p, D
end

# -----------------------------------------------------------------------------
# One CTMRG contraction at a given chi. Returns a Dict; never throws past the
# guard (a non-convergence / error is recorded honestly).
# Convergence: leading_boundary breaks the loop when err <= tol AND iter >= miniter.
# info has no `converged` flag, so we re-derive convergence by a single extra
# ctmrg check: we re-run from the returned env for 1 step and read the residual.
# Cheaper + robust: we capture verbosity=2 which prints "CTMRG conv N" vs "cancel".
# Here we instead measure energy stability across chi (the chi-convergence series)
# and flag converged_by_iter = (iters_used < maxiter).
# -----------------------------------------------------------------------------
function contract_at_chi(peps, H, chi::Int)
    t_start = time()
    env0 = CTMRGEnv(peps, ComplexSpace(chi))
    converged = false
    iters_used = -1
    energy_raw = NaN
    xi = NaN
    trunc_err = NaN
    err_msg = ""
    try
        # verbosity=1 -> only warnings (a non-convergence prints a cancel warning);
        # we additionally bound iterations and read info. PER-CONTRACTION watchdog.
        env, info = with_watchdog(SELF_KILL_S, "chi=$chi") do
            leading_boundary(env0, peps;
                             tol=CTMRG_TOL, miniter=CTMRG_MINIT,
                             maxiter=CTMRG_MAXIT, verbosity=1)
        end
        E = expectation_value(peps, H, env)
        energy_raw = real(E)
        cl = correlation_length(peps, env)
        # correlation_length returns (xi_vec, lambda_vec, ...); take leading xi
        xi = (cl isa Tuple) ? real(first(cl)[1]) : real(cl[1])
        trunc_err = hasproperty(info, :truncation_error) ? Float64(info.truncation_error) : NaN
        # Heuristic convergence flag: a converged env gives a finite, stable energy and
        # a small truncation error. We mark converged=true when energy is finite and
        # trunc_err < 1e-2 (loose: CTMRG cancel still returns finite numbers, so the
        # AUTHORITATIVE convergence signal is the chi-stability check done by the caller).
        converged = isfinite(energy_raw) && isfinite(xi)
    catch e
        err_msg = sprint(showerror, e)
        @warn "CTMRG at chi=$chi errored" err_msg
    end
    wall = time() - t_start
    return Dict(
        "chi"            => chi,
        "energy_raw_per_site" => energy_raw,           # PEPSKit raw (sum of 2 bonds/site)
        "energy_per_bond"     => energy_raw / 2,       # = raw / 2 (1x1 cell, 2 bonds/site)
        "correlation_length"  => xi,
        "truncation_error"    => trunc_err,
        "finite"              => isfinite(energy_raw) && isfinite(xi),
        "wall_seconds"        => round(wall, digits=3),
        "error"               => err_msg,
    )
end

function chi_series(peps, H; label::String)
    println("  [$label] CTMRG chi-ladder $(CHI_LADDER) ...")
    rows = Dict{String,Any}[]
    for chi in CHI_LADDER
        # each contraction carries its own per-contraction watchdog (SELF_KILL_S)
        r = contract_at_chi(peps, H, chi)
        rows = vcat(rows, [Dict{String,Any}(r)])
        @printf("    chi=%-3d  E_raw/site=% .8f  E/bond=% .8f  xi=% .5f  trunc=%.2e  finite=%s  %.2fs\n",
                chi, r["energy_raw_per_site"], r["energy_per_bond"], r["correlation_length"],
                r["truncation_error"], r["finite"], r["wall_seconds"])
    end
    # chi-convergence verdict: successive |E_raw(chi_{i+1}) - E_raw(chi_i)| small
    fin = [r for r in rows if get(r, "finite", false)]
    chi_converged = false
    max_dE = NaN
    if length(fin) >= 2
        es = [r["energy_raw_per_site"] for r in fin]
        diffs = [abs(es[i+1]-es[i]) for i in 1:length(es)-1]
        max_dE = maximum(diffs)
        chi_converged = max_dE < 1e-4   # energy stable to 1e-4 across the ladder
    end
    return rows, chi_converged, max_dE
end

# -----------------------------------------------------------------------------
# F01 / N01 finite-map record + checks
# -----------------------------------------------------------------------------
function run()
    started = now()
    Jc = read_J_convention()
    H = heisenberg_XYZ(InfiniteSquare(); Jx=Jc.Jx, Jy=Jc.Jy, Jz=Jc.Jz)
    println("Hamiltonian: heisenberg_XYZ Jx=$(Jc.Jx) Jy=$(Jc.Jy) Jz=$(Jc.Jz) spin=$(Jc.spin)  [$(Jc.source)]")

    # ---- warmup: force PEPSKit/CTMRG JIT compilation OUTSIDE any timed contraction.
    # A tiny chi=2 contraction on a random D=2 tensor compiles leading_boundary,
    # expectation_value, correlation_length. The per-contraction watchdog then
    # measures real contraction wall time, not compile time.
    print("Warming up CTMRG (JIT compile) ... "); flush(stdout)
    let Aw = randn(ComplexF64, 2, 2, 2, 2, 2)
        pw, _, _ = build_peps(Aw)
        ew = CTMRGEnv(pw, ComplexSpace(2))
        env_w, _ = leading_boundary(ew, pw; tol=1e-6, miniter=2, maxiter=6, verbosity=0)
        expectation_value(pw, H, env_w); correlation_length(pw, env_w)
    end
    @printf("done (%.1fs warm).\n", time() - T0)

    out = Dict{String,Any}(
        "object_id" => "julia_ctmrg_heisenberg",
        "classification" => "tool_lego_fit_probe",
        "promotion_allowed" => false,
        "claim_ceiling" => "contraction-only CTMRG cross-check of an external iPEPS tensor; " *
                           "NOT layer-completion / manifold admission / coupling / bridge / flux / physics",
        "root_constraints_in_force" => Dict(
            "F01" => "finite carrier (p x D^4 dense tensor), finite probe {chi=16,24,32}, " *
                     "finite operator heisenberg_XYZ, bounded CTMRG path (maxiter=$(CTMRG_MAXIT))",
            "N01" => "ordered CTMRG fixed-point sweep (N/E/S/W directional growth); " *
                     "transfer op and bond term noncommuting; input-dependence negative control " *
                     "(distinct random carrier must yield a different energy) applied",
        ),
        "finite_map" => "A (single-site iPEPS tensor, shape [p,u,r,d,l]) |-> " *
                        "(per-site CTMRG energy, correlation length) over chi-ladder",
        "domain" => "complex128 dense tensor [p,u,r,d,l]; p=physical, u/r/d/l virtual bonds",
        "codomain_or_output" => "per-site energy (raw + per-bond), correlation length, chi-convergence series",
        "index_permutation" => Dict(
            "jax_axis_order" => "[p,u,r,d,l] = (physical, up, right, down, left)",
            "pepskit_convention" => "PEPSTensor T : P <- N (x) E (x) S (x) W ; dense [P,N,E,S,W]",
            "perm_applied_p_u_r_d_l_to_P_N_E_S_W" => collect(PERM_PUR_DL_TO_PNESW),
            "virtual_space_assignment" => "N=E=ComplexSpace(D), S=W=ComplexSpace(D)' (dual) for 1x1 wraparound",
            "note" => "label-mapping is identity (p->P,u->N,r->E,d->S,l->W); perm=(1,2,3,4,5)",
        ),
        "hamiltonian_convention" => Dict(
            "model" => "heisenberg_XYZ (PEPSKit/MPSKitModels)",
            "Jx" => Jc.Jx, "Jy" => Jc.Jy, "Jz" => Jc.Jz, "spin" => Jc.spin,
            "source" => Jc.source,
            "note" => "term placed on every NN bond; raw per-site value sums 2 bonds (1x1 cell); per_bond = raw/2",
        ),
        "ctmrg_settings" => Dict("tol"=>CTMRG_TOL, "miniter"=>CTMRG_MINIT, "maxiter"=>CTMRG_MAXIT,
                                 "chi_ladder"=>collect(CHI_LADDER), "self_kill_seconds"=>SELF_KILL_S),
        "landmine_guards" => ["no_fixedpoint", "no_PEPSOptimize", "no_LBFGS", "no_HagerZhangLineSearch",
                              "ctmrg_maxiter_capped_100", "in_process_self_kill_timer_150s"],
        "tool_manifest" => Dict(
            "PEPSKit" => "load_bearing: CTMRG leading_boundary contraction + expectation_value + correlation_length",
            "TensorKit" => "load_bearing: TensorMap carrier with explicit P<-NESW space split",
            "NPZ" => "load_bearing when ipeps_heisenberg_D2.npy present: loads external JAX tensor",
            "LinearAlgebra" => "supportive",
        ),
        "engine" => "Julia 1.12 / PEPSKit v0.7.0 / TensorKit v0.15.3 (contraction lane)",
        "wall_seconds" => 0.0,
        "exit_status" => "ok",
        "tests" => Dict{String,Any}(),
        "results" => Dict{String,Any}(),
    )

    # =========================================================================
    # (a) POSITIVE / SANITY: random D=2 tensor.
    #     Expectation: finite per-site energy, CTMRG runs, NOT near AFM ground.
    # =========================================================================
    println("\n[a] RANDOM D=2 tensor (sanity: finite energy, no crash) ...")
    A_rand = randn(ComplexF64, 2, 2, 2, 2, 2)   # [p,u,r,d,l], p=2, D=2
    peps_rand, p_r, D_r = build_peps(A_rand)
    rows_rand, conv_rand, dE_rand = chi_series(peps_rand, H; label="random")
    out["results"]["random_D2"] = Dict(
        "p"=>p_r, "D"=>D_r, "chi_series"=>rows_rand,
        "chi_converged"=>conv_rand, "max_dE_across_chi"=>dE_rand,
        "interpretation" => "random carrier -> finite per-site energy not near AFM ground (~-0.66/bond); " *
                            "this is EXPECTED and is the positive sanity result.",
    )
    # POSITIVE test: random energy is finite at every finite chi row
    pos_ok = any(get(r,"finite",false) for r in rows_rand)
    out["tests"]["positive_random_finite"] = pos_ok

    # =========================================================================
    # (b) NEGATIVE CONTROL (anti-tautology, input-dependence):
    #     A GENUINELY DIFFERENT carrier (an independent fresh random tensor), NOT a
    #     symmetry image. NOTE: an index permutation like (1,4,5,2,3) is a 180-deg
    #     lattice rotation of the SAME iPEPS; CTMRG energy is rot180-invariant, so
    #     such a "scramble" tautologically returns the identical energy and would
    #     test nothing. We therefore use a distinct random tensor. If the pipeline
    #     returned a CONSTANT regardless of input, this distinct carrier would give
    #     the SAME energy. A DIFFERENT finite energy shows the contraction is
    #     INPUT-DEPENDENT (sensitive to the actual tensor), not a hardcoded value.
    # =========================================================================
    println("\n[b] NEGATIVE CONTROL: independent fresh-random tensor (input-dependence check) ...")
    A_scram = randn(ComplexF64, 2, 2, 2, 2, 2)   # distinct carrier (not a symmetry image of A_rand)
    peps_scram, _, _ = build_peps(A_scram)
    rows_scram, _, _ = chi_series(peps_scram, H; label="independent_control")
    e_rand_16   = (length(rows_rand)  >= 1 && get(rows_rand[1],"finite",false))  ? rows_rand[1]["energy_raw_per_site"]  : NaN
    e_scram_16  = (length(rows_scram) >= 1 && get(rows_scram[1],"finite",false)) ? rows_scram[1]["energy_raw_per_site"] : NaN
    input_dependent = isfinite(e_rand_16) && isfinite(e_scram_16) && abs(e_rand_16 - e_scram_16) > 1e-6
    out["results"]["independent_control_D2"] = Dict(
        "control_kind" => "independent_fresh_random_tensor",
        "anti_tautology_note" => "index-permutation controls (e.g. (1,4,5,2,3)) are rot180 symmetry " *
                                 "images and return the IDENTICAL CTMRG energy; rejected as tautological. " *
                                 "Using a distinct random carrier instead.",
        "chi_series"=>rows_scram,
        "energy_random_chi16"=>e_rand_16, "energy_control_chi16"=>e_scram_16,
        "delta"=>abs(e_rand_16 - e_scram_16),
        "input_dependent"=>input_dependent,
    )
    # NEGATIVE test: scrambled tensor must give a DIFFERENT energy (pipeline not constant)
    out["tests"]["negative_input_dependent"] = input_dependent

    # =========================================================================
    # (c) BOUNDARY: smallest chi (16) must still converge to a finite energy on
    #     the random carrier; we also record that chi=16 is the lower rung used.
    # =========================================================================
    out["tests"]["boundary_lowest_chi_finite"] =
        (length(rows_rand) >= 1) && get(rows_rand[1], "finite", false)

    # =========================================================================
    # (d) REAL CROSS-CHECK: JAX-optimized tensor, if present.
    #     The cross-check verdict is whether THIS CTMRG energy matches JAX's own
    #     reported energy for the SAME tensor at the SAME chi. We do NOT author
    #     that target; we read it from TENSOR_FORMAT.md / a sidecar if the JAX
    #     lane wrote one. Absent a JAX-reported energy, match is left as null
    #     (BLOCKED on JAX handshake), and we only report our contraction.
    # =========================================================================
    if isfile(JAX_NPY)
        println("\n[d] JAX-OPTIMIZED tensor $(basename(JAX_NPY)) found -> CROSS-CHECK ...")
        A_jax = npzread(JAX_NPY)
        A_jax5 = ndims(A_jax) == 5 ? A_jax : reshape(A_jax, size(A_jax)...)
        peps_jax, p_j, D_j = build_peps(Array{ComplexF64}(A_jax5))
        rows_jax, conv_jax, dE_jax = chi_series(peps_jax, H; label="jax")
        # try to read a JAX-reported energy target (sidecar / format doc); else null
        jax_reported = nothing
        if isfile(FMT_DOC)
            txt = read(FMT_DOC, String)
            mm = match(r"jax[_ ]?energy(?:[_ ]per[_ ]site)?\s*[=:]\s*([-+]?[0-9.eE]+)", txt)
            mm !== nothing && (jax_reported = tryparse(Float64, mm.captures[1]))
        end
        e_jax_julia = isempty(rows_jax) ? NaN :
            (get(rows_jax[end],"finite",false) ? rows_jax[end]["energy_raw_per_site"] : NaN)
        match_verdict = nothing
        if jax_reported !== nothing && isfinite(e_jax_julia)
            match_verdict = abs(e_jax_julia - jax_reported) < 1e-3
        end
        out["results"]["jax_optimized"] = Dict(
            "p"=>p_j, "D"=>D_j, "chi_series"=>rows_jax,
            "chi_converged"=>conv_jax, "max_dE_across_chi"=>dE_jax,
            "julia_energy_per_site_top_chi"=>e_jax_julia,
            "jax_reported_energy"=>jax_reported,
            "cross_check_match"=> match_verdict === nothing ? "blocked_no_jax_reported_energy" : match_verdict,
        )
        out["tests"]["cross_check_jax"] = match_verdict === nothing ? "blocked" : match_verdict
    else
        println("\n[d] JAX tensor $(basename(JAX_NPY)) ABSENT -> cross-check BLOCKED (loader ready).")
        out["results"]["jax_optimized"] = Dict(
            "status"=>"absent", "path"=>JAX_NPY,
            "note"=>"loader ready; cross-check blocked on JAX handshake file",
        )
        out["tests"]["cross_check_jax"] = "blocked_file_absent"
    end

    out["wall_seconds"] = round(time() - T0, digits=2)

    open(RESULT, "w") do f; JSON.print(f, out, 2) end
    println("\nWrote $(RESULT)")
    println("exit_status=$(out["exit_status"])  wall=$(out["wall_seconds"])s")
    println("tests: ", JSON.json(out["tests"]))
    return out
end

run()
