#!/usr/bin/env julia
# ax6op_julia.jl  —  Axis-6 operator sim, codex2-MAX
#
# CORE FACT encoded:
#   Axis-6 up/down is the SAME operator placed operator-first (up = T(O(r)))
#   vs terrain-first (down = O(T(r))).  NOT a +/- variant.
#
# object_id: ax6op_axis6_operator_placement_julia
# claim_ceiling: bounded finite-map receipt; not layer-complete; not bridge;
#                not layer-completion; no manifold admission claim.
# promotion_allowed: false
#
# Root constraints in force:
#   F01  finite distinguishability — all carrier/operator/terrain sets are finite
#   N01  noncommutation — operator composition order is structurally non-trivial

using Dates
using JSON
using LinearAlgebra
using SHA

# ---------------------------------------------------------------------------
# 0. Constants and Pauli basis
# ---------------------------------------------------------------------------
const I2 = Matrix{ComplexF64}(I, 2, 2)
const sx = ComplexF64[0 1; 1 0]
const sz = ComplexF64[1 0; 0 -1]

# z-basis projectors
const PZ0 = (I2 + sz) / 2          # |0><0|
const PZ1 = (I2 - sz) / 2          # |1><1|

# x-basis projectors
const PX_p = (I2 + sx) / 2         # |+><+|
const PX_m = (I2 - sx) / 2         # |-><-|

# ---------------------------------------------------------------------------
# 1. Four operators as exact Bloch / channel maps
#    Ti  = z-dephase : (x,y,z) -> (lambda1*x, lambda1*y, z)   lambda1 = 1-2q1
#    Te  = x-dephase : (x,y,z) -> (x, lambda2*y, lambda2*z)   lambda2 = 1-2q2
#    Fi  = R_x(theta) rotation about x-axis
#    Fe  = R_z(phi)   rotation about z-axis
# ---------------------------------------------------------------------------
const Q1    = 0.3          # dephasing strength for Ti
const Q2    = 0.3          # dephasing strength for Te
const THETA = pi / 5       # rotation angle for Fi (R_x)
const PHI   = pi / 7       # rotation angle for Fe (R_z)

function apply_Ti(rho::Matrix{ComplexF64})
    # Ti: z-dephase  rho -> (1-q1)*rho + q1*(P0 rho P0 + P1 rho P1)
    pinched = PZ0 * rho * PZ0 + PZ1 * rho * PZ1
    return (1.0 - Q1) * rho + Q1 * pinched
end

function apply_Te(rho::Matrix{ComplexF64})
    # Te: x-dephase  rho -> (1-q2)*rho + q2*(Q+ rho Q+ + Q- rho Q-)
    pinched = PX_p * rho * PX_p + PX_m * rho * PX_m
    return (1.0 - Q2) * rho + Q2 * pinched
end

function apply_Fi(rho::Matrix{ComplexF64})
    # Fi: R_x(theta)
    U = cos(THETA / 2) * I2 - im * sin(THETA / 2) * sx
    return U * rho * U'
end

function apply_Fe(rho::Matrix{ComplexF64})
    # Fe: R_z(phi)
    U = cos(PHI / 2) * I2 - im * sin(PHI / 2) * sz
    return U * rho * U'
end

const OPS = Dict(
    "Ti" => apply_Ti,
    "Te" => apply_Te,
    "Fi" => apply_Fi,
    "Fe" => apply_Fe,
)

# Bloch vector of rho
bloch(rho::Matrix{ComplexF64}) = [
    2 * real(rho[1, 2]),
    2 * imag(rho[2, 1]),
    real(rho[1, 1] - rho[2, 2]),
]

# ---------------------------------------------------------------------------
# 2. Eight terrain Bloch maps
#    Terrain = Lindblad-step approximation applied once to rho
#    Se / Ne (direct frame):   native judging ops Ti, Fi
#    Ni / Si (conj. frame):    native judging ops Te, Fe
#    in / out = fiber vs lifted-base loop class (geometry tag only;
#               the Bloch-map action we use is a discrete step of the
#               terrain's canonical Lindblad with fixed step epsilon)
#
#    Concrete Bloch-map per terrain (one-step discretisation):
#      Se_out (expansion, direct, dissipative-Lindblad):
#             rho -> rho + eps * L_se(rho)
#             L_se(rho) = sigma_x rho sigma_x - rho   (radial push-out in x)
#      Ne_in  (expansion, direct, Hamiltonian-dominant):
#             rho -> exp(-i eps H0) rho exp(+i eps H0),  H0 = sz
#      Ni_in  (compression, conj, attractor-Lindblad):
#             rho -> rho + eps * L_ni(rho)
#             L_ni(rho) = PZ0 rho PZ0 - rho            (projection toward |0>)
#      Si_out (compression, conj, invariant strata):
#             rho -> rho + eps * L_si(rho)
#             L_si(rho) = PX_p rho PX_p + PX_m rho PX_m - rho
# ---------------------------------------------------------------------------
const EPS_T = 0.2    # discrete terrain step

function terrain_Se_out(rho::Matrix{ComplexF64})
    # dissipative expansion along x (Se direct, outer fiber)
    Lrho = sx * rho * sx - rho
    raw = rho + EPS_T * Lrho
    # re-normalise trace (Lindblad step can drift)
    return raw / tr(raw)
end

function terrain_Ne_in(rho::Matrix{ComplexF64})
    # Hamiltonian circulation (Ne direct, inner fiber)
    H0 = sz
    U  = exp(-im * EPS_T * H0)
    return U * rho * U'
end

function terrain_Ni_in(rho::Matrix{ComplexF64})
    # compression attractor toward |0> (Ni conj, inner base)
    Lrho = PZ0 * rho * PZ0 - rho
    raw = rho + EPS_T * Lrho
    return raw / tr(raw)
end

function terrain_Si_out(rho::Matrix{ComplexF64})
    # stratified retention in invariant x-strata (Si conj, outer base)
    Lrho = PX_p * rho * PX_p + PX_m * rho * PX_m - rho
    raw = rho + EPS_T * Lrho
    return raw / tr(raw)
end

const TERRAINS = Dict(
    "Se_out" => terrain_Se_out,
    "Ne_in"  => terrain_Ne_in,
    "Ni_in"  => terrain_Ni_in,
    "Si_out" => terrain_Si_out,
)

# ---------------------------------------------------------------------------
# 3. Sixteen signed placements
#    Each signed op has 2 terrains per the token chart (atlas sec.14):
#      Ti_up  -> TiSe (Se_out), TiNe (Ne_in)
#      Ti_dn  -> SeTi (Se_out), NeTi (Ne_in)
#      Te_up  -> TeNi (Ni_in),  TeSi (Si_out)
#      Te_dn  -> NiTe (Ni_in),  SiTe (Si_out)
#      Fi_up  -> FiNe (Ne_in),  FiSe (Se_out)
#      Fi_dn  -> NeFi (Ne_in),  SeFi (Se_out)
#      Fe_up  -> FeNi (Ni_in),  FeSi (Si_out)
#      Fe_dn  -> NiFe (Ni_in),  SiFe (Si_out)
#
#    up placement  = T(O(r))  : apply operator first, then terrain
#    down placement = O(T(r)) : apply terrain first, then operator
# ---------------------------------------------------------------------------
const PLACEMENTS = [
    # (token,       op_name, terrain_name,  order)
    ("TiSe",  "Ti", "Se_out", "up"),
    ("TiNe",  "Ti", "Ne_in",  "up"),
    ("SeTi",  "Ti", "Se_out", "down"),
    ("NeTi",  "Ti", "Ne_in",  "down"),
    ("TeNi",  "Te", "Ni_in",  "up"),
    ("TeSi",  "Te", "Si_out", "up"),
    ("NiTe",  "Te", "Ni_in",  "down"),
    ("SiTe",  "Te", "Si_out", "down"),
    ("FiNe",  "Fi", "Ne_in",  "up"),
    ("FiSe",  "Fi", "Se_out", "up"),
    ("NeFi",  "Fi", "Ne_in",  "down"),
    ("SeFi",  "Fi", "Se_out", "down"),
    ("FeNi",  "Fe", "Ni_in",  "up"),
    ("FeSi",  "Fe", "Si_out", "up"),
    ("NiFe",  "Fe", "Ni_in",  "down"),
    ("SiFe",  "Fe", "Si_out", "down"),
]

# ---------------------------------------------------------------------------
# 4. Finite sample set — 8 Bloch-ball points well inside unit ball
# ---------------------------------------------------------------------------
function sample_states(n::Int=8)
    # n evenly spaced polar angles on a small sphere (r=0.7)
    r = 0.7
    rhos = Matrix{ComplexF64}[]
    for k in 0:(n-1)
        # spherical coordinates, avoid poles
        theta_s = pi * (k + 0.5) / n
        phi_s   = 2 * pi * k / n
        bx = r * sin(theta_s) * cos(phi_s)
        by = r * sin(theta_s) * sin(phi_s)
        bz = r * cos(theta_s)
        rho_k = (I2 + bx * sx + bz * sz) / 2
        # add tiny off-diagonal via by  (sy not imported, build from sx,sz)
        sy = ComplexF64[0 -im; im 0]
        rho_k = (I2 + bx * sx + by * sy + bz * sz) / 2
        push!(rhos, rho_k)
    end
    return rhos
end

# ---------------------------------------------------------------------------
# 5. Delta = T(O(r)) - O(T(r)) per placement, all samples
# ---------------------------------------------------------------------------
function compute_delta(token, op_fn, terrain_fn, rho)
    up_result   = terrain_fn(op_fn(rho))     # T(O(r))
    down_result = op_fn(terrain_fn(rho))     # O(T(r))
    delta       = up_result - down_result
    return delta, norm(delta)
end

# ---------------------------------------------------------------------------
# 6. Functional probes
#    V_z(r) = rx^2 + ry^2   (decreases under Ti z-dephase)
#    V_x(r) = ry^2 + rz^2   (decreases under Te x-dephase)
# ---------------------------------------------------------------------------
function V_z(rho)
    b = bloch(rho)
    return b[1]^2 + b[2]^2
end

function V_x(rho)
    b = bloch(rho)
    return b[2]^2 + b[3]^2
end

# For Te-up ascent test:
#   V_Si = (M_out . r)^2   M_out = bloch vector of Si_out eigenvector ~ x-direction = [1,0,0]
#   V_Ni = ||r - pit_bottom||^2  pit_bottom = Ni attractor = [0,0,1] (|0> state)
function V_Si(rho)
    b = bloch(rho)
    # Si terrain has x-stratum projectors; the "mountain" direction is x
    return b[1]^2
end

function V_Ni(rho)
    b = bloch(rho)
    # Ni attractor is |0>, bloch = [0,0,1]
    pit_b = [0.0, 0.0, 1.0]
    diff = b - pit_b
    return dot(diff, diff)
end

# ---------------------------------------------------------------------------
# 7. Main computation
# ---------------------------------------------------------------------------
function main()
    samples = sample_states(8)

    # --- 4 operators: verify Bloch map contractions ---
    op_bloch_checks = Dict{String,Any}()

    # Ti z-dephase: rx,ry shrink, rz unchanged
    ti_lambda1 = 1.0 - 2 * Q1
    ti_checks = Dict{String,Any}()
    for (k, rho) in enumerate(samples)
        b_in  = bloch(rho)
        b_out = bloch(apply_Ti(rho))
        ti_checks["s$(k)_rx_ratio"] = abs(b_in[1]) > 1e-10 ? b_out[1] / b_in[1] : "~0"
        ti_checks["s$(k)_ry_ratio"] = abs(b_in[2]) > 1e-10 ? b_out[2] / b_in[2] : "~0"
        ti_checks["s$(k)_rz_diff"]  = abs(b_out[3] - b_in[3])
    end
    ti_lambda1_expected = round(ti_lambda1; digits=6)
    op_bloch_checks["Ti"] = Dict(
        "lambda1"    => ti_lambda1_expected,
        "bloch_map"  => "(lambda1*rx, lambda1*ry, rz)",
        "per_sample" => ti_checks,
    )

    # Te x-dephase: rx unchanged, ry,rz shrink
    te_lambda2 = 1.0 - 2 * Q2
    te_checks = Dict{String,Any}()
    for (k, rho) in enumerate(samples)
        b_in  = bloch(rho)
        b_out = bloch(apply_Te(rho))
        te_checks["s$(k)_ry_ratio"] = abs(b_in[2]) > 1e-10 ? b_out[2] / b_in[2] : "~0"
        te_checks["s$(k)_rz_ratio"] = abs(b_in[3]) > 1e-10 ? b_out[3] / b_in[3] : "~0"
        te_checks["s$(k)_rx_diff"]  = abs(b_out[1] - b_in[1])
    end
    op_bloch_checks["Te"] = Dict(
        "lambda2"    => round(te_lambda2; digits=6),
        "bloch_map"  => "(rx, lambda2*ry, lambda2*rz)",
        "per_sample" => te_checks,
    )

    # Fi R_x(theta): norm-preserving
    fi_norm_checks = Float64[]
    for rho in samples
        push!(fi_norm_checks, abs(norm(bloch(apply_Fi(rho))) - norm(bloch(rho))))
    end
    op_bloch_checks["Fi"] = Dict(
        "rotation"   => "R_x($(round(THETA; digits=4)))",
        "norm_diffs" => fi_norm_checks,
        "max_norm_diff" => maximum(fi_norm_checks),
    )

    # Fe R_z(phi): norm-preserving
    fe_norm_checks = Float64[]
    for rho in samples
        push!(fe_norm_checks, abs(norm(bloch(apply_Fe(rho))) - norm(bloch(rho))))
    end
    op_bloch_checks["Fe"] = Dict(
        "rotation"   => "R_z($(round(PHI; digits=4)))",
        "norm_diffs" => fe_norm_checks,
        "max_norm_diff" => maximum(fe_norm_checks),
    )

    # --- check (3): all 16 placements ---
    placement_results = Dict{String,Any}()
    all_delta_norms   = Float64[]
    for (token, op_name, terrain_name, order) in PLACEMENTS
        op_fn      = OPS[op_name]
        terrain_fn = TERRAINS[terrain_name]
        per_sample_delta = Float64[]
        for rho in samples
            _, dn = compute_delta(token, op_fn, terrain_fn, rho)
            push!(per_sample_delta, dn)
        end
        max_delta = maximum(per_sample_delta)
        push!(all_delta_norms, max_delta)
        placement_results[token] = Dict(
            "op"            => op_name,
            "terrain"       => terrain_name,
            "order"         => order,
            "up_formula"    => "T(O(r)) — terrain $(terrain_name) applied after op $(op_name)",
            "down_formula"  => "O(T(r)) — op $(op_name) applied after terrain $(terrain_name)",
            "per_sample_delta_norms" => per_sample_delta,
            "max_delta_norm" => max_delta,
        )
    end
    global_max_delta = maximum(all_delta_norms)

    # --- check (4): noncommute_delta and commuting_control_zero ---
    # commuting control: Ti with z-diagonal pseudo-terrain
    # both Ti and terrain_Ti are z-diagonal -> Delta should be ~0
    function terrain_Ti_control(rho)
        # pure z-dephase, same form as Ti but with independent parameter
        q_ctrl = 0.25
        pinched = PZ0 * rho * PZ0 + PZ1 * rho * PZ1
        return (1.0 - q_ctrl) * rho + q_ctrl * pinched
    end
    ctrl_deltas = Float64[]
    for rho in samples
        _, dn = compute_delta("TiCtrl", apply_Ti, terrain_Ti_control, rho)
        push!(ctrl_deltas, dn)
    end
    commuting_control_delta = maximum(ctrl_deltas)

    # noncommute_delta: max over all 16 placements
    noncommute_delta = global_max_delta

    # --- check (5): ti_te_gradient_descent ---
    ti_vz_descent = Bool[]
    te_vx_descent = Bool[]
    for rho in samples
        vz_in  = V_z(rho)
        vz_out = V_z(apply_Ti(rho))
        push!(ti_vz_descent, vz_out <= vz_in + 1e-14)   # V_z decreases or equal

        vx_in  = V_x(rho)
        vx_out = V_x(apply_Te(rho))
        push!(te_vx_descent, vx_out <= vx_in + 1e-14)
    end
    ti_vz_all   = all(ti_vz_descent)
    te_vx_all   = all(te_vx_descent)
    ti_te_gradient_descent = ti_vz_all && te_vx_all

    # --- check (6): fi_fe_norm_preserving ---
    fi_max_err = maximum(fi_norm_checks)
    fe_max_err = maximum(fe_norm_checks)
    fi_fe_norm_preserving = fi_max_err < 1e-12 && fe_max_err < 1e-12

    # --- check (7): te_up_ascent_test ---
    # Te-up placements: TeNi (Ni_in terrain, operator-first) and TeSi (Si_out terrain, operator-first)
    # up = T(O(r)), so we apply Te first then terrain
    # Test: does V_Si monotonically increase along TeNi-up chain?
    #        does V_Ni monotonically increase along TeSi-up chain?
    # "ascent" = functional strictly increases at each step; test across 8 samples
    te_up_teni = Dict{String,Any}()
    te_up_tesi = Dict{String,Any}()

    vni_diffs = Float64[]   # V_Ni after TeNi-up minus before
    vsi_diffs = Float64[]   # V_Si after TeSi-up minus before

    for rho in samples
        # TeNi up = T(O(r)) = terrain_Ni_in(apply_Te(rho))
        r_TeNi_up = terrain_Ni_in(apply_Te(rho))
        vni_before = V_Ni(rho)
        vni_after  = V_Ni(r_TeNi_up)
        push!(vni_diffs, vni_after - vni_before)

        # TeSi up = T(O(r)) = terrain_Si_out(apply_Te(rho))
        r_TeSi_up = terrain_Si_out(apply_Te(rho))
        vsi_before = V_Si(rho)
        vsi_after  = V_Si(r_TeSi_up)
        push!(vsi_diffs, vsi_after - vsi_before)
    end

    teni_all_positive = all(d > 0 for d in vni_diffs)
    tesi_all_positive = all(d > 0 for d in vsi_diffs)
    teni_any_positive = any(d > 0 for d in vni_diffs)
    tesi_any_positive = any(d > 0 for d in vsi_diffs)

    # Honest classification
    function ascent_label(all_pos, any_pos)
        if all_pos
            return "all_positive"
        elseif any_pos
            return "partial"
        else
            return "none"
        end
    end

    te_up_teni_label = ascent_label(teni_all_positive, teni_any_positive)
    te_up_tesi_label = ascent_label(tesi_all_positive, tesi_any_positive)

    if te_up_teni_label == "all_positive" && te_up_tesi_label == "all_positive"
        te_up_ascent_test = "all_positive"
    elseif te_up_teni_label == "none" && te_up_tesi_label == "none"
        te_up_ascent_test = "none"
    else
        te_up_ascent_test = "partial — TeNi_up=$(te_up_teni_label), TeSi_up=$(te_up_tesi_label)"
    end

    # --- check (4): four_operators_exact ---
    # Record explicit Bloch-map parameters
    four_operators_exact = Dict(
        "Ti" => Dict(
            "map"     => "(lambda1*rx, lambda1*ry, rz)",
            "lambda1" => ti_lambda1,
            "q1"      => Q1,
        ),
        "Te" => Dict(
            "map"     => "(rx, lambda2*ry, lambda2*rz)",
            "lambda2" => te_lambda2,
            "q2"      => Q2,
        ),
        "Fi" => Dict(
            "map"     => "R_x(theta) on Bloch sphere",
            "theta"   => THETA,
        ),
        "Fe" => Dict(
            "map"     => "R_z(phi) on Bloch sphere",
            "phi"     => PHI,
        ),
    )

    # --- check: sixteen_placements summary ---
    sixteen_placements = Dict(
        "count"             => length(PLACEMENTS),
        "token_list"        => [p[1] for p in PLACEMENTS],
        "global_max_delta_norm" => global_max_delta,
        "all_nonzero"       => all(v > 1e-14 for v in all_delta_norms),
    )

    # --- parity scalars (written to JSON for JAX lane to cross-check) ---
    parity_scalars = Dict(
        "noncommute_delta_max"       => noncommute_delta,
        "commuting_control_max"      => commuting_control_delta,
        "ti_vz_descent_all"          => ti_vz_all,
        "te_vx_descent_all"          => te_vx_all,
        "fi_max_norm_err"            => fi_max_err,
        "fe_max_norm_err"            => fe_max_err,
        "te_up_teni_label"           => te_up_teni_label,
        "te_up_tesi_label"           => te_up_tesi_label,
        "te_up_ascent_test"          => te_up_ascent_test,
        "ti_te_gradient_descent"     => ti_te_gradient_descent,
        "fi_fe_norm_preserving"      => fi_fe_norm_preserving,
    )

    # --- Build result payload ---
    payload = Dict(
        "object_id"          => "ax6op_axis6_operator_placement_julia",
        "engine"             => "julia_linearalgebra",
        "generated_at"       => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path"        => @__FILE__,
        "source_sha256"      => bytes2hex(sha256(read(@__FILE__))),
        "run_command"        => "julia /Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/ax6op_julia.jl",
        "claim_ceiling"      => "bounded finite-map receipt; not layer-complete; not bridge; no manifold admission",
        "promotion_allowed"  => false,
        "root_constraints"   => [
            "F01: finite carrier/probe/operator/terrain set",
            "N01: noncommuting/order-sensitive operator control",
        ],
        "core_fact"          => "Axis-6 up/down is the SAME operator; up=T(O(r)) operator-first, down=O(T(r)) terrain-first. NOT a +/- variant.",
        "four_operators_exact"       => four_operators_exact,
        "sixteen_placements"         => sixteen_placements,
        "placement_results"          => placement_results,
        "noncommute_delta"           => Dict(
            "value"       => noncommute_delta,
            "description" => "max ||T(O(r))-O(T(r))|| over all 16 placements and 8 samples",
        ),
        "commuting_control_zero"     => Dict(
            "value"       => commuting_control_delta,
            "description" => "Ti with pure z-dephase terrain (both z-diagonal) -> Delta~0",
            "pass_1e8"    => commuting_control_delta < 1e-8,
        ),
        "ti_te_gradient_descent"     => Dict(
            "ti_vz_descent_all"  => ti_vz_all,
            "te_vx_descent_all"  => te_vx_all,
            "both"               => ti_te_gradient_descent,
        ),
        "fi_fe_norm_preserving"      => Dict(
            "fi_max_err"  => fi_max_err,
            "fe_max_err"  => fe_max_err,
            "pass_1e12"   => fi_fe_norm_preserving,
        ),
        "te_up_ascent_test"          => Dict(
            "TeNi_up_label"  => te_up_teni_label,
            "TeSi_up_label"  => te_up_tesi_label,
            "summary"        => te_up_ascent_test,
            "vni_diffs"      => vni_diffs,
            "vsi_diffs"      => vsi_diffs,
            "honest_note"    => "If partial/none: ascent needs a different functional; V_Ni and V_Si may not be monotone under the discrete Lindblad step chosen.",
        ),
        "op_bloch_checks"            => op_bloch_checks,
        "parity_scalars"             => parity_scalars,
        "downstream_blocks"          => ["layer_completion","Axis0","flux","bridge","physics","coupling"],
    )

    result_path = joinpath(@__DIR__, "ax6op_julia_results.json")
    open(result_path, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end

    println("ax6op done | result: $(result_path)")
    println("  noncommute_delta      = $(noncommute_delta)")
    println("  commuting_ctrl_max    = $(commuting_control_delta) (pass<1e-8: $(commuting_control_delta < 1e-8))")
    println("  ti_te_gradient_descent= $(ti_te_gradient_descent)")
    println("  fi_fe_norm_preserving = $(fi_fe_norm_preserving)")
    println("  te_up_ascent_test     = $(te_up_ascent_test)")

    return 0
end

exit(main())
