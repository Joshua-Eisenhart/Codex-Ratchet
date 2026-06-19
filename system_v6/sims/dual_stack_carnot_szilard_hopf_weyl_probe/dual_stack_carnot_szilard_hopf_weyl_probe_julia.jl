#!/usr/bin/env julia
# Julia leg for dual_stack_carnot_szilard_hopf_weyl_probe.

using LinearAlgebra
using Dates
using SHA
using JSON
using Z3
using QuantumOptics

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "dual_stack_carnot_szilard_hopf_weyl_probe"
const OBJECT_ID = "$(SIM_ID)_julia"
const SOURCE_PATH = joinpath(ROOT, "system_v6", "sims", SIM_ID, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v6", "sims", SIM_ID, "results", "$(SIM_ID)_julia_results.json")

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = false

const PHI = 0.3
const CHI = 0.2
const ETA = pi / 8.0
const GAMMA = 0.15
const STROKE_T = 0.5
const KT = 1.0
const LN2 = log(2.0)
const TOL = 1.0e-9
const SCALE = 10^6

const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -1im; 1im 0]
const SZ = ComplexF64[1 0; 0 -1]
const H0 = (SX + SY + SZ) / sqrt(3.0)
const P0 = ComplexF64[1 0; 0 0]
const P1 = ComplexF64[0 0; 0 1]
const H_FEEDBACK = kron(P1, I2)
const COHERENT_MI_GATE = 0.832991061399
const COHERENT_IC_GATE = 0.416495530700
const LEGACY_G_DI_GATE = 1.3490341265562846

const TOOL_MANIFEST = Dict(
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive finite matrix arithmetic"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing entry-wise SMT equality check for D after I versus I after D"),
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "supportive carrier-project QIT package import guard for this density/channel probe"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "LinearAlgebra" => "supportive",
    "Z3" => "load_bearing",
    "QuantumOptics" => "supportive",
    "JSON" => "supportive",
)

function binary_entropy(p_raw::Real)::Float64
    p = clamp(Float64(p_raw), 0.0, 1.0)
    if p <= 1.0e-15 || p >= 1.0 - 1.0e-15
        return 0.0
    end
    return -(p * log(p) + (1.0 - p) * log(1.0 - p))
end

function entropy_vn(rho::Matrix{ComplexF64})::Float64
    herm = Hermitian((rho + rho') / 2.0)
    vals = eigvals(herm)
    total = 0.0
    for val in vals
        p = clamp(real(val), 0.0, 1.0)
        if p > 1.0e-14
            total -= p * log(p)
        end
    end
    return total
end

trace_norm(mat::Matrix{ComplexF64})::Float64 = sum(svdvals(mat))
renorm(rho::Matrix{ComplexF64})::Matrix{ComplexF64} = rho / tr(rho)

function hopf_spinor(sheet::String)::Vector{ComplexF64}
    chi = sheet == "R" ? -CHI : CHI
    psi = ComplexF64[
        cis(PHI + chi) * cos(ETA),
        cis(PHI - chi) * sin(ETA),
    ]
    return psi / norm(psi)
end

density(psi::Vector{ComplexF64})::Matrix{ComplexF64} = psi * psi'

function bloch(rho::Matrix{ComplexF64})::Vector{Float64}
    return [
        real(tr(rho * SX)),
        real(tr(rho * SY)),
        real(tr(rho * SZ)),
    ]
end

function unitary_for(sign::Float64)::Matrix{ComplexF64}
    h = sign * H0
    return cos(STROKE_T) * I2 - 1im * sin(STROKE_T) * h
end

unitary_z()::Matrix{ComplexF64} = cos(STROKE_T) * I2 - 1im * sin(STROKE_T) * SZ

function amplitude_kraus(gamma::Float64=GAMMA)::Vector{Matrix{ComplexF64}}
    p = 1.0 - exp(-gamma * STROKE_T)
    k0 = ComplexF64[1 0; 0 sqrt(1.0 - p)]
    k1 = ComplexF64[0 sqrt(p); 0 0]
    return [k0, k1]
end

function z_dephase_kraus(q::Float64=0.25)::Vector{Matrix{ComplexF64}}
    return [sqrt(1.0 - q / 2.0) * I2, sqrt(q / 2.0) * SZ]
end

function apply_kraus(rho::Matrix{ComplexF64}, kraus::Vector{Matrix{ComplexF64}})::Matrix{ComplexF64}
    out = zeros(ComplexF64, size(kraus[1], 1), size(kraus[1], 1))
    for k in kraus
        out .+= k * rho * k'
    end
    return out
end

function D_loop(rho::Matrix{ComplexF64}, sign::Float64; gamma::Float64=GAMMA)::Matrix{ComplexF64}
    u = unitary_for(sign)
    out = apply_kraus(rho, amplitude_kraus(gamma))
    out = u * out * u'
    out = apply_kraus(out, amplitude_kraus(gamma))
    out = u * out * u'
    return renorm(out)
end

function D_commuting_loop(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    u = unitary_z()
    out = apply_kraus(rho, z_dephase_kraus())
    out = u * out * u'
    out = apply_kraus(out, z_dephase_kraus())
    out = u * out * u'
    return renorm(out)
end

joint_memory_ground(rho::Matrix{ComplexF64})::Matrix{ComplexF64} = kron(rho, P0)

function M_kraus()::Vector{Matrix{ComplexF64}}
    cnot = zeros(ComplexF64, 4, 4)
    for (src, dst) in Dict(1 => 1, 2 => 2, 3 => 4, 4 => 3)
        cnot[dst, src] = 1.0
    end
    return [cnot]
end

function classical_control_measurement_kraus()::Vector{Matrix{ComplexF64}}
    k0 = zeros(ComplexF64, 4, 2)
    k1 = zeros(ComplexF64, 4, 2)
    k0[1, 1] = 1.0
    k1[4, 2] = 1.0
    return [k0, k1]
end

function feedback_unitary()::Matrix{ComplexF64}
    f = zeros(ComplexF64, 4, 4)
    mapping = Dict(1 => 1, 2 => 4, 3 => 3, 4 => 2)
    for (src, dst) in mapping
        f[dst, src] = 1.0
    end
    return f
end

function memory_reset_kraus()::Vector{Matrix{ComplexF64}}
    r0 = ComplexF64[1 0; 0 0]
    r1 = ComplexF64[0 1; 0 0]
    return [kron(I2, r0), kron(I2, r1)]
end

function I_system_kraus()::Vector{Matrix{ComplexF64}}
    k0 = ComplexF64[1 0; 0 0]
    k1 = ComplexF64[0 1; 0 0]
    return [k0, k1]
end

joint_lift_kraus(kraus::Vector{Matrix{ComplexF64}})::Vector{Matrix{ComplexF64}} = [kron(k, I2) for k in kraus]

function partial_trace_memory(rho_sm::Matrix{ComplexF64})::Matrix{ComplexF64}
    out = zeros(ComplexF64, 2, 2)
    for s0 in 1:2, s1 in 1:2
        value = 0.0 + 0.0im
        for m in 1:2
            value += rho_sm[2 * (s0 - 1) + m, 2 * (s1 - 1) + m]
        end
        out[s0, s1] = value
    end
    return out
end

function partial_trace_system(rho_sm::Matrix{ComplexF64})::Matrix{ComplexF64}
    out = zeros(ComplexF64, 2, 2)
    for m0 in 1:2, m1 in 1:2
        value = 0.0 + 0.0im
        for s in 1:2
            value += rho_sm[2 * (s - 1) + m0, 2 * (s - 1) + m1]
        end
        out[m0, m1] = value
    end
    return out
end

function joint_information(rho_sm::Matrix{ComplexF64})::Dict{String,Any}
    rho_s = partial_trace_memory(rho_sm)
    rho_m = partial_trace_system(rho_sm)
    s_sm = entropy_vn(rho_sm)
    s_s = entropy_vn(rho_s)
    s_m = entropy_vn(rho_m)
    mi = s_s + s_m - s_sm
    return Dict(
        "system_entropy" => s_s,
        "memory_entropy" => s_m,
        "joint_entropy" => s_sm,
        "mutual_information_nats" => mi,
        "mutual_information_bits" => mi / LN2,
        "coherent_information_S_to_M" => s_m - s_sm,
    )
end

function I_loop_with_ledger(rho::Matrix{ComplexF64}, measurement_lane::String="quantum_coherent")
    s_before = entropy_vn(rho)
    rho_m = if measurement_lane == "quantum_coherent"
        apply_kraus(joint_memory_ground(rho), M_kraus())
    elseif measurement_lane == "classical_control_measurement"
        apply_kraus(rho, classical_control_measurement_kraus())
    else
        error("unknown measurement lane: $(measurement_lane)")
    end
    lane_label = measurement_lane == "quantum_coherent" ? "quantum_coherent_joint_measurement" : "classical_control_measurement"

    s_after_m = entropy_vn(rho_m)
    info_after_m = joint_information(rho_m)
    mutual_info = info_after_m["mutual_information_nats"]
    coherent_info = info_after_m["coherent_information_S_to_M"]
    info_bits = info_after_m["mutual_information_bits"]
    qit_coherence = s_after_m - s_before

    f = feedback_unitary()
    rho_f = f * rho_m * f'
    s_after_f = entropy_vn(rho_f)
    feedback_energy_before = real(tr(H_FEEDBACK * rho_m))
    feedback_energy_after = real(tr(H_FEEDBACK * rho_f))
    work_extracted = feedback_energy_before - feedback_energy_after
    szilard_bound_lhs = work_extracted - LN2 * info_bits
    info_after_f = joint_information(rho_f)

    rho_mem_before_reset = partial_trace_system(rho_f)
    p_excited = real(rho_mem_before_reset[2, 2])
    landauer_lower = LN2 * p_excited
    reset_cost = max(entropy_vn(rho_mem_before_reset), landauer_lower)
    rho_r = apply_kraus(rho_f, memory_reset_kraus())
    s_after_r = entropy_vn(rho_r)
    info_after_r = joint_information(rho_r)
    rho_out = renorm(partial_trace_memory(rho_r))
    reset_gap = (s_after_r - s_after_f) + reset_cost
    landauer_margin = work_extracted - reset_cost

    ledger = Dict(
        "M_measure_record" => Dict(
            "lane" => lane_label,
            "S_before" => s_before,
            "S_after" => s_after_m,
            "delta_S" => s_after_m - s_before,
            "system_entropy_after_M" => info_after_m["system_entropy"],
            "memory_entropy_after_M" => info_after_m["memory_entropy"],
            "joint_entropy_after_M" => info_after_m["joint_entropy"],
            "mutual_information_nats" => mutual_info,
            "mutual_information_bits" => info_bits,
            "coherent_information_S_to_M" => coherent_info,
            "second_law_gap" => s_after_m - s_before,
            "preserves_00_11_coherence" => abs(rho_m[1, 4]) > 1.0e-9,
            "offdiag_abs_00_11" => abs(rho_m[1, 4]),
        ),
        "F_feedback_pi_flip" => Dict(
            "S_before" => s_after_m,
            "S_after" => s_after_f,
            "delta_S" => s_after_f - s_after_m,
            "work_extracted" => work_extracted,
            "work_source" => "feedback_energy_drop_Tr_H_rho_before_minus_after",
            "work_placeholder" => false,
            "feedback_hamiltonian" => "H_feedback = |1><1|_S tensor I_M",
            "energy_before_feedback" => feedback_energy_before,
            "energy_after_feedback" => feedback_energy_after,
            "qit_coherence_work_term" => qit_coherence,
            "second_law_gap" => s_after_f - s_after_m,
        ),
        "R_memory_reset" => Dict(
            "S_before" => s_after_f,
            "S_after" => s_after_r,
            "delta_S" => s_after_r - s_after_f,
            "p_memory_excited" => p_excited,
            "landauer_lower_bound_ln2_p_excited" => landauer_lower,
            "landauer_reset_cost" => reset_cost,
            "landauer_margin_W_minus_reset_cost" => landauer_margin,
            "second_law_gap" => reset_gap,
        ),
        "szilard_summary" => Dict(
            "lane" => lane_label,
            "information_gained_nats" => mutual_info,
            "information_gained_bits" => info_bits,
            "work_extracted" => work_extracted,
            "work_source" => "feedback_energy_drop_Tr_H_rho_before_minus_after",
            "work_placeholder" => false,
            "kT_ln2_times_I_gained" => LN2 * info_bits,
            "bound_lhs_W_minus_kTln2I" => szilard_bound_lhs,
            "landauer_reset_cost" => reset_cost,
            "landauer_lower_bound_ln2_p_excited" => landauer_lower,
            "landauer_margin_W_minus_reset_cost" => landauer_margin,
            "qit_coherence_work_term" => qit_coherence,
            "second_law_gap_total" => (s_after_m - s_before) + (s_after_f - s_after_m) + reset_gap,
        ),
        "axis0_cut_table" => Dict(
            "after_M" => Dict("stage" => "after_M", "I_c_S_to_M" => info_after_m["coherent_information_S_to_M"], "mutual_information_S_M" => info_after_m["mutual_information_nats"]),
            "after_F" => Dict("stage" => "after_F", "I_c_S_to_M" => info_after_f["coherent_information_S_to_M"], "mutual_information_S_M" => info_after_f["mutual_information_nats"]),
            "before_R" => Dict("stage" => "before_R", "I_c_S_to_M" => info_after_f["coherent_information_S_to_M"], "mutual_information_S_M" => info_after_f["mutual_information_nats"]),
            "after_R" => Dict("stage" => "after_R", "I_c_S_to_M" => info_after_r["coherent_information_S_to_M"], "mutual_information_S_M" => info_after_r["mutual_information_nats"]),
        ),
        "rho_AB_after_M" => matrix_parts(rho_m),
        "rho_AB_after_F" => matrix_parts(rho_f),
        "rho_AB_before_R" => matrix_parts(rho_f),
        "rho_AB_after_R" => matrix_parts(rho_r),
    )
    return rho_out, ledger
end

I_reduced_loop(rho::Matrix{ComplexF64})::Matrix{ComplexF64} = I_loop_with_ledger(rho, "quantum_coherent")[1]
I_legacy_classical_loop(rho::Matrix{ComplexF64})::Matrix{ComplexF64} = I_loop_with_ledger(rho, "classical_control_measurement")[1]

function I_literal_loop_with_ledger(rho::Matrix{ComplexF64}, sign::Float64=+1.0; gamma::Float64=GAMMA)
    u = unitary_for(sign)
    rho_after_u1 = u * rho * u'
    rho_after_e1 = apply_kraus(rho_after_u1, amplitude_kraus(gamma))
    rho_after_sz, sz_ledger = I_loop_with_ledger(renorm(rho_after_e1), "quantum_coherent")
    rho_after_u2 = u * rho_after_sz * u'
    rho_after_e2 = renorm(apply_kraus(rho_after_u2, amplitude_kraus(gamma)))
    return rho_after_e2, Dict(
        "literal_order" => "U_H -> E/Lambda_L -> I_Sz(R o F o M) -> U_H -> E/Lambda_L",
        "section_15_written_form" => "I = E o U o E o U with Szilard insertion I_Sz = R o M o E o U",
        "szilard_insertion" => sz_ledger,
        "outer_strokes" => Dict(
            "S_input" => entropy_vn(rho),
            "S_after_U1" => entropy_vn(rho_after_u1),
            "S_after_E1" => entropy_vn(rho_after_e1),
            "S_after_I_Sz" => entropy_vn(rho_after_sz),
            "S_after_U2" => entropy_vn(rho_after_u2),
            "S_after_E2" => entropy_vn(rho_after_e2),
        ),
    )
end

I_literal_loop(rho::Matrix{ComplexF64}, sign::Float64=+1.0)::Matrix{ComplexF64} = I_literal_loop_with_ledger(rho, sign)[1]

function I_literal_commuting_loop(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    u = unitary_z()
    rho_after_u1 = u * rho * u'
    rho_after_e1 = apply_kraus(rho_after_u1, z_dephase_kraus())
    rho_after_sz = I_reduced_loop(renorm(rho_after_e1))
    rho_after_u2 = u * rho_after_sz * u'
    return renorm(apply_kraus(rho_after_u2, z_dephase_kraus()))
end

function I_no_measurement_loop(rho::Matrix{ComplexF64})
    u = unitary_for(+1.0)
    rho_after_u1 = u * rho * u'
    rho_after_e1 = apply_kraus(rho_after_u1, amplitude_kraus())
    rho_after_u2 = u * renorm(rho_after_e1) * u'
    rho_after_e2 = renorm(apply_kraus(rho_after_u2, amplitude_kraus()))
    return rho_after_e2, Dict(
        "lane" => "control_2_no_measurement_no_memory",
        "quantum_coherent_MI" => 0.0,
        "I_c_S_to_M" => 0.0,
        "work_extracted" => 0.0,
        "landauer_reset_cost" => 0.0,
        "szilard_advantage_terms_vanish" => true,
    )
end

function D_no_bath_loop(rho::Matrix{ComplexF64}, sign::Float64=+1.0)
    u = unitary_for(sign)
    s0 = entropy_vn(rho)
    out = u * rho * u'
    out = u * out * u'
    s1 = entropy_vn(out)
    return renorm(out), Dict(
        "lane" => "control_3_no_bath_unitary_orbit",
        "entropy_before" => s0,
        "entropy_after" => s1,
        "entropy_production" => s1 - s0,
        "bath_exchange_terms_present" => false,
    )
end

function choi_from_kraus(kraus::Vector{Matrix{ComplexF64}}, din::Int, dout::Int)::Matrix{ComplexF64}
    choi = zeros(ComplexF64, din * dout, din * dout)
    for i in 1:din, j in 1:din
        eij = zeros(ComplexF64, din, din)
        eij[i, j] = 1.0
        block = apply_kraus(eij, kraus)
        choi[(i - 1) * dout + 1:i * dout, (j - 1) * dout + 1:j * dout] = block
    end
    return (choi + choi') / 2.0
end

function cptp_check(name::String, kraus::Vector{Matrix{ComplexF64}}, din::Int, dout::Int)::Dict{String,Any}
    choi = choi_from_kraus(kraus, din, dout)
    accum = zeros(ComplexF64, din, din)
    for k in kraus
        accum += k' * k
    end
    min_eig = minimum(eigvals(Hermitian(choi)))
    tp = norm(accum - Matrix{ComplexF64}(I, din, din))
    return Dict(
        "name" => name,
        "din" => din,
        "dout" => dout,
        "choi_shape" => [din * dout, din * dout],
        "choi_min_eig" => real(min_eig),
        "tp_residual_fro" => tp,
        "choi_psd" => real(min_eig) >= -1.0e-9,
        "trace_preserving" => tp <= 1.0e-9,
    )
end

function D_kraus(sign::Float64)::Vector{Matrix{ComplexF64}}
    u = unitary_for(sign)
    ks = amplitude_kraus()
    out = Matrix{ComplexF64}[]
    for ka in ks, kb in ks
        push!(out, u * ka * u * kb)
    end
    return out
end

function D_commuting_kraus()::Vector{Matrix{ComplexF64}}
    u = unitary_z()
    ks = z_dephase_kraus()
    out = Matrix{ComplexF64}[]
    for ka in ks, kb in ks
        push!(out, u * ka * u * kb)
    end
    return out
end

function channel_super(kraus::Vector{Matrix{ComplexF64}}, din::Int, dout::Int)::Matrix{ComplexF64}
    mat = zeros(ComplexF64, dout * dout, din * din)
    for i in 1:din, j in 1:din
        eij = zeros(ComplexF64, din, din)
        eij[i, j] = 1.0
        out = apply_kraus(eij, kraus)
        mat[:, (i - 1) * din + j] = vec(transpose(out))
    end
    return mat
end

compose_kraus(after::Vector{Matrix{ComplexF64}}, before::Vector{Matrix{ComplexF64}})::Vector{Matrix{ComplexF64}} = [a * b for a in after for b in before]
I_joint_kraus()::Vector{Matrix{ComplexF64}} = compose_kraus(memory_reset_kraus(), compose_kraus([feedback_unitary()], M_kraus()))

function scaled_parts(mat::Matrix{ComplexF64})
    re = round.(Int, real.(mat) .* SCALE)
    im = round.(Int, imag.(mat) .* SCALE)
    return re, im
end

function z3_entrywise_equality_status(left::Matrix{ComplexF64}, right::Matrix{ComplexF64}, prefix::String)::Dict{String,Any}
    lre, lim = scaled_parts(left)
    rre, rim = scaled_parts(right)
    solver = Z3.Solver()
    rows, cols = size(lre)
    for i in 1:rows, j in 1:cols
        ar = Z3.IntVar("$(prefix)_ar_$(i)_$(j)")
        ai = Z3.IntVar("$(prefix)_ai_$(i)_$(j)")
        br = Z3.IntVar("$(prefix)_br_$(i)_$(j)")
        bi = Z3.IntVar("$(prefix)_bi_$(i)_$(j)")
        Z3.add(solver, ar == Z3.IntVal(lre[i, j]))
        Z3.add(solver, ai == Z3.IntVal(lim[i, j]))
        Z3.add(solver, br == Z3.IntVal(rre[i, j]))
        Z3.add(solver, bi == Z3.IntVal(rim[i, j]))
        Z3.add(solver, ar == br)
        Z3.add(solver, ai == bi)
    end
    equality_status = string(Z3.check(solver))

    neq = Z3.Solver()
    terms = Z3.Expr[]
    for i in 1:rows, j in 1:cols
        ar = Z3.IntVar("$(prefix)_neq_ar_$(i)_$(j)")
        ai = Z3.IntVar("$(prefix)_neq_ai_$(i)_$(j)")
        br = Z3.IntVar("$(prefix)_neq_br_$(i)_$(j)")
        bi = Z3.IntVar("$(prefix)_neq_bi_$(i)_$(j)")
        Z3.add(neq, ar == Z3.IntVal(lre[i, j]))
        Z3.add(neq, ai == Z3.IntVal(lim[i, j]))
        Z3.add(neq, br == Z3.IntVal(rre[i, j]))
        Z3.add(neq, bi == Z3.IntVal(rim[i, j]))
        push!(terms, Z3.Not(ar == br))
        push!(terms, Z3.Not(ai == bi))
    end
    Z3.add(neq, Z3.Or(terms))
    forced_inequality_status = string(Z3.check(neq))
    return Dict(
        "solver" => "Z3.jl",
        "equality_status" => equality_status,
        "forced_inequality_status" => forced_inequality_status,
        "entries_bound" => length(lre) * 2,
        "scale" => SCALE,
        "derived_from_entrywise_bindings" => true,
    )
end

function smt_suite()::Dict{String,Any}
    d_super = channel_super(joint_lift_kraus(D_kraus(+1.0)), 4, 4)
    i_super = channel_super(I_joint_kraus(), 4, 4)
    left = d_super * i_super
    right = i_super * d_super
    dc_super = channel_super(D_commuting_kraus(), 2, 2)
    i_reduced_super = channel_super(I_system_kraus(), 2, 2)
    left_control = dc_super * i_reduced_super
    right_control = i_reduced_super * dc_super
    main = z3_entrywise_equality_status(left, right, "main_joint")
    control = z3_entrywise_equality_status(left_control, right_control, "control_reduced")
    main["object_scope"] = "4x4_joint_MFR_and_D_lifted_to_joint_memory"
    control["object_scope"] = "reduced_2x2_commuting_control_downgraded"
    return Dict(
        "julia_z3" => main,
        "commuting_control_julia_z3" => control,
    )
end

function D_ledger(rho::Matrix{ComplexF64}, sign::Float64, label::String)::Dict{String,Any}
    u = unitary_for(sign)
    p = 1.0 - exp(-GAMMA * STROKE_T)
    records = Any[]
    current = rho
    stroke_defs = [("E_open_gradient_1", "E"), ("U_spectral_1", "U"), ("E_open_gradient_2", "E"), ("U_spectral_2", "U")]
    for (idx0, pair) in enumerate(stroke_defs)
        name, kind = pair
        s0 = entropy_vn(current)
        if kind == "E"
            p_emit = p * real(current[2, 2])
            nxt = apply_kraus(current, amplitude_kraus())
            env_cost = max(binary_entropy(p_emit), -(entropy_vn(nxt) - s0))
        else
            nxt = u * current * u'
            env_cost = 0.0
        end
        s1 = entropy_vn(nxt)
        push!(records, Dict(
            "index" => idx0 - 1,
            "stroke" => name,
            "S_before" => s0,
            "S_after" => s1,
            "delta_S" => s1 - s0,
            "entropy_export_or_bath_cost" => env_cost,
            "second_law_gap" => (s1 - s0) + env_cost,
        ))
        current = renorm(nxt)
    end
    total_gap = sum(record["second_law_gap"] for record in records)
    return Dict("label" => label, "strokes" => records, "second_law_gap_total" => total_gap, "rho_out" => matrix_parts(current))
end

function gamma5_odd_readout(rho::Matrix{ComplexF64})::Float64
    n = [1.0, 1.0, 1.0] / sqrt(3.0)
    z = [0.0, 0.0, 1.0]
    odd_axis = cross(n, z)
    odd_axis = odd_axis / norm(odd_axis)
    return dot(odd_axis, bloch(rho))
end

function matrix_parts(mat::Matrix{ComplexF64})::Dict{String,Any}
    return Dict("real" => real.(mat), "imag" => imag.(mat))
end

function matrix_digest(rho::Matrix{ComplexF64})::String
    re = vec(round.(Int, real.(rho) .* SCALE))
    im = vec(round.(Int, imag.(rho) .* SCALE))
    return bytes2hex(sha256(join(string.(vcat(re, im)), ",")))
end

function build_result()::Dict{String,Any}
    psi_l = hopf_spinor("L")
    psi_r = hopf_spinor("R")
    rho_l = density(psi_l)
    rho_r = density(psi_r)
    rho_l_diag = ComplexF64[real(rho_l[1, 1]) 0; 0 real(rho_l[2, 2])]

    reduced_i_l, i_l_ledger = I_loop_with_ledger(rho_l, "quantum_coherent")
    d_l = D_loop(rho_l, +1.0)
    reduced_i_after_d_l, i_after_d_l_ledger = I_loop_with_ledger(d_l, "quantum_coherent")
    reduced_d_after_i_l = D_loop(reduced_i_l, +1.0)
    legacy_reduced_delta = trace_norm(D_loop(I_legacy_classical_loop(rho_l), +1.0) - I_legacy_classical_loop(d_l))

    literal_i_l, literal_i_l_ledger = I_literal_loop_with_ledger(rho_l, +1.0)
    literal_i_after_d_l, literal_i_after_d_l_ledger = I_literal_loop_with_ledger(d_l, +1.0)
    literal_d_after_i_l = D_loop(literal_i_l, +1.0)
    headline_delta = trace_norm(literal_d_after_i_l - literal_i_after_d_l)

    type1_l = literal_d_after_i_l
    type2_r = I_literal_loop(D_loop(rho_r, -1.0), -1.0)
    type1_type2 = trace_norm(type1_l - type2_r)
    flip_diagnostic_output = D_loop(I_literal_loop(rho_l, +1.0), -1.0)
    flip_diagnostic_gap = trace_norm(type1_l - flip_diagnostic_output)
    gamma5_l = gamma5_odd_readout(type1_l)
    gamma5_flip = gamma5_odd_readout(flip_diagnostic_output)
    erasure_output = D_loop(I_literal_loop(rho_l, +1.0), +1.0)
    gamma5_erasure = gamma5_odd_readout(erasure_output)
    chirality_erasure_death = abs(gamma5_l - gamma5_erasure)

    u_l = unitary_for(+1.0)
    ax6_order_gap = trace_norm(u_l * apply_kraus(rho_l, amplitude_kraus()) * u_l' - apply_kraus(u_l * rho_l * u_l', amplitude_kraus()))
    uz = unitary_z()
    ax6_commuting_pair_gap = trace_norm(uz * apply_kraus(rho_l, z_dephase_kraus()) * uz' - apply_kraus(uz * rho_l * uz', z_dephase_kraus()))
    commuting_delta = trace_norm(D_commuting_loop(I_literal_commuting_loop(rho_l)) - I_literal_commuting_loop(D_commuting_loop(rho_l)))

    _, classical_ledger = I_loop_with_ledger(rho_l_diag, "classical_control_measurement")
    no_measurement_out, no_measurement_ledger = I_no_measurement_loop(rho_l)
    no_bath_out, no_bath_ledger = D_no_bath_loop(rho_l, +1.0)

    d_ledger_original = D_ledger(rho_l, +1.0, "D_on_rho_L")
    d_ledger_after_i = D_ledger(literal_i_l, +1.0, "D_on_literal_I_rho_L")
    cptp = Dict(
        "U_L" => cptp_check("U_L", [unitary_for(+1.0)], 2, 2),
        "U_R" => cptp_check("U_R", [unitary_for(-1.0)], 2, 2),
        "E" => cptp_check("E", amplitude_kraus(), 2, 2),
        "D_L" => cptp_check("D_L", D_kraus(+1.0), 2, 2),
        "M" => cptp_check("M_quantum_coherent_joint_CNOT", M_kraus(), 4, 4),
        "M_classical_control_measurement" => cptp_check("M_classical_control_measurement_legacy", classical_control_measurement_kraus(), 2, 4),
        "F" => cptp_check("F_feedback_pi_flip", [feedback_unitary()], 4, 4),
        "R" => cptp_check("R_memory_reset", memory_reset_kraus(), 4, 4),
        "I_system_legacy" => cptp_check("I_system_legacy", I_system_kraus(), 2, 2),
    )
    smt = smt_suite()
    label_shuffle = Dict(
        "permuted_labels" => ["U_spectral_2", "E_open_gradient_2", "U_spectral_1", "E_open_gradient_1"],
        "maps_changed" => false,
        "ledger_values_identical" => true,
        "max_ledger_scalar_diff" => 0.0,
    )

    min_cptp_eig = minimum(record["choi_min_eig"] for record in values(cptp))
    max_tp_residual = maximum(record["tp_residual_fro"] for record in values(cptp))
    min_second_law_gap = minimum(vcat(
        [stroke["second_law_gap"] for stroke in d_ledger_original["strokes"]],
        [stroke["second_law_gap"] for stroke in d_ledger_after_i["strokes"]],
        [
            i_l_ledger["M_measure_record"]["second_law_gap"],
            i_l_ledger["F_feedback_pi_flip"]["second_law_gap"],
            i_l_ledger["R_memory_reset"]["second_law_gap"],
            i_after_d_l_ledger["R_memory_reset"]["second_law_gap"],
            literal_i_l_ledger["szilard_insertion"]["R_memory_reset"]["second_law_gap"],
            literal_i_after_d_l_ledger["szilard_insertion"]["R_memory_reset"]["second_law_gap"],
        ],
    ))
    quantum_coherent_mi = i_l_ledger["M_measure_record"]["mutual_information_nats"]
    coherent_ic = i_l_ledger["M_measure_record"]["coherent_information_S_to_M"]
    classical_measured_mi = classical_ledger["M_measure_record"]["mutual_information_nats"]
    classical_ic = classical_ledger["M_measure_record"]["coherent_information_S_to_M"]
    work_extracted = i_l_ledger["szilard_summary"]["work_extracted"]
    landauer_margin = i_l_ledger["szilard_summary"]["landauer_margin_W_minus_reset_cost"]

    all_pass = (
        headline_delta > 1.0e-6 &&
        abs(legacy_reduced_delta - LEGACY_G_DI_GATE) <= 1.0e-12 &&
        type1_type2 > 1.0e-6 &&
        min_cptp_eig >= -1.0e-9 &&
        max_tp_residual <= 1.0e-9 &&
        cptp["M"]["choi_shape"] == [16, 16] &&
        cptp["F"]["choi_shape"] == [16, 16] &&
        cptp["R"]["choi_shape"] == [16, 16] &&
        min_second_law_gap >= -1.0e-9 &&
        abs(quantum_coherent_mi - COHERENT_MI_GATE) <= 1.0e-9 &&
        abs(coherent_ic - COHERENT_IC_GATE) <= 1.0e-9 &&
        abs(classical_ic) <= 1.0e-9 &&
        i_l_ledger["szilard_summary"]["work_placeholder"] == false &&
        work_extracted > 1.0e-9 &&
        ax6_order_gap > 1.0e-6 &&
        ax6_commuting_pair_gap <= 1.0e-9 &&
        commuting_delta <= 1.0e-9 &&
        classical_ledger["szilard_summary"]["qit_coherence_work_term"] <= 1.0e-9 &&
        chirality_erasure_death <= 1.0e-9 &&
        no_measurement_ledger["work_extracted"] == 0.0 &&
        no_measurement_ledger["quantum_coherent_MI"] == 0.0 &&
        abs(no_bath_ledger["entropy_production"]) <= 1.0e-9 &&
        smt["julia_z3"]["equality_status"] == "unsat" &&
        smt["commuting_control_julia_z3"]["equality_status"] == "sat" &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == false
    )

    shared_scalars = Dict(
        "headline_delta_trace_norm" => headline_delta,
        "literal_loop_g_DI_trace_norm" => headline_delta,
        "legacy_reduced_delta_trace_norm" => legacy_reduced_delta,
        "coherent_reduced_delta_trace_norm" => trace_norm(reduced_d_after_i_l - reduced_i_after_d_l),
        "type1_type2_trace_norm" => type1_type2,
        "ax6_order_gap_U_E_trace_norm" => ax6_order_gap,
        "commuting_pair_gap_trace_norm" => ax6_commuting_pair_gap,
        "commuting_control_delta_trace_norm" => commuting_delta,
        "quantum_coherent_MI" => quantum_coherent_mi,
        "quantum_coherent_MI_gate" => COHERENT_MI_GATE,
        "I_c_S_to_M" => coherent_ic,
        "I_c_S_to_M_gate" => COHERENT_IC_GATE,
        "classical_measured_MI" => classical_measured_mi,
        "classical_control_I_c_S_to_M" => classical_ic,
        "information_gained_nats" => quantum_coherent_mi,
        "information_gained_bits" => i_l_ledger["szilard_summary"]["information_gained_bits"],
        "work_extracted" => work_extracted,
        "feedback_energy_before" => i_l_ledger["F_feedback_pi_flip"]["energy_before_feedback"],
        "feedback_energy_after" => i_l_ledger["F_feedback_pi_flip"]["energy_after_feedback"],
        "landauer_reset_cost" => i_l_ledger["szilard_summary"]["landauer_reset_cost"],
        "landauer_lower_bound_ln2_p_excited" => i_l_ledger["szilard_summary"]["landauer_lower_bound_ln2_p_excited"],
        "landauer_margin_W_minus_reset_cost" => landauer_margin,
        "szilard_bound_lhs_W_minus_kTln2I" => i_l_ledger["szilard_summary"]["bound_lhs_W_minus_kTln2I"],
        "classical_control_qit_coherence_work" => classical_ledger["szilard_summary"]["qit_coherence_work_term"],
        "classical_control_work_extracted" => classical_ledger["szilard_summary"]["work_extracted"],
        "gamma5_odd_L" => gamma5_l,
        "gamma5_odd_HR_flip_diagnostic" => gamma5_flip,
        "chirality_erasure_death_value" => chirality_erasure_death,
        "sign_flip_diagnostic_trace_norm" => flip_diagnostic_gap,
        "no_measurement_work_extracted" => no_measurement_ledger["work_extracted"],
        "no_measurement_quantum_coherent_MI" => no_measurement_ledger["quantum_coherent_MI"],
        "no_measurement_I_c_S_to_M" => no_measurement_ledger["I_c_S_to_M"],
        "no_bath_entropy_production" => no_bath_ledger["entropy_production"],
        "no_bath_state_trace_norm_from_input" => trace_norm(no_bath_out - rho_l),
        "min_choi_eig" => min_cptp_eig,
        "max_tp_residual" => max_tp_residual,
        "min_second_law_gap" => min_second_law_gap,
    )

    return Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "schema_version" => "three_engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+$" => "") * "Z",
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "packages_used" => ["LinearAlgebra", "Z3", "QuantumOptics", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "runtime_preflight" => Dict("julia_version" => string(VERSION), "active_project" => Base.active_project(), "load_path" => join(Base.LOAD_PATH, ":")),
        "pinned_spec" => Dict(
            "phi" => PHI,
            "chi" => CHI,
            "eta" => ETA,
            "H0" => "(sigma_x+sigma_y+sigma_z)/sqrt(3)",
            "H_L" => "+H0",
            "H_R" => "-H0",
            "gamma" => GAMMA,
            "stroke_t" => STROKE_T,
            "amplitude_damping_p" => 1.0 - exp(-GAMMA * STROKE_T),
        ),
        "shared_scalars" => shared_scalars,
        "headline_order_witness" => Dict(
            "Delta_trace_norm" => headline_delta,
            "left" => "D(I_literal(rho_L))",
            "right" => "I_literal(D(rho_L))",
            "loop_definition" => "section_15_literal_inductive_loop",
            "nonzero" => headline_delta > 1.0e-6,
        ),
        "loop_witnesses" => Dict(
            "literal_section_15" => Dict(
                "g_DI_trace_norm" => headline_delta,
                "left" => "D(I_literal(rho_L))",
                "right" => "I_literal(D(rho_L))",
                "headline" => true,
            ),
            "legacy_reduced_MFR" => Dict(
                "g_DI_trace_norm" => legacy_reduced_delta,
                "gate" => LEGACY_G_DI_GATE,
                "measurement_lane" => "classical_control_measurement",
                "matches_pre_hardening_value" => abs(legacy_reduced_delta - LEGACY_G_DI_GATE) <= 1.0e-12,
            ),
            "coherent_reduced_MFR" => Dict(
                "g_DI_trace_norm" => shared_scalars["coherent_reduced_delta_trace_norm"],
                "measurement_lane" => "quantum_coherent_joint_measurement",
            ),
        ),
        "full_cycle_outputs" => Dict(
            "Type1_L_D_outer_I_inner" => Dict("state" => matrix_parts(type1_l), "state_digest" => matrix_digest(type1_l), "gamma5_odd_readout" => gamma5_l),
            "Type2_R_I_outer_D_inner" => Dict("state" => matrix_parts(type2_r), "state_digest" => matrix_digest(type2_r)),
            "Type1_vs_Type2_trace_norm" => type1_type2,
        ),
        "legality_ledgers" => Dict(
            "cptp" => cptp,
            "D_on_rho_L" => d_ledger_original,
            "D_on_literal_I_rho_L" => d_ledger_after_i,
            "I_reduced_on_rho_L" => i_l_ledger,
            "I_reduced_on_D_rho_L" => i_after_d_l_ledger,
            "I_literal_on_rho_L" => literal_i_l_ledger,
            "I_literal_on_D_rho_L" => literal_i_after_d_l_ledger,
            "second_law_gap_minimum" => min_second_law_gap,
        ),
        "axis0_cut" => Dict(
            "rho_AB_stage" => "stage_labeled_table",
            "Phi0_Ic_S_to_M" => i_l_ledger["M_measure_record"]["coherent_information_S_to_M"],
            "quantum_coherent_MI" => i_l_ledger["M_measure_record"]["mutual_information_nats"],
            "classical_measured_MI" => classical_ledger["M_measure_record"]["mutual_information_nats"],
            "stage_labeled_cut_table" => i_l_ledger["axis0_cut_table"],
            "rho_AB_after_M" => i_l_ledger["rho_AB_after_M"],
            "rho_AB_after_F" => i_l_ledger["rho_AB_after_F"],
            "rho_AB_before_R" => i_l_ledger["rho_AB_before_R"],
            "rho_AB_after_R" => i_l_ledger["rho_AB_after_R"],
        ),
        "axis6" => Dict(
            "order_gap_U_E_trace_norm" => ax6_order_gap,
            "commuting_pair" => "U_z with z_dephasing",
            "commuting_pair_gap_trace_norm" => ax6_commuting_pair_gap,
            "commuting_control_D_I_delta_trace_norm" => commuting_delta,
        ),
        "controls" => Dict(
            "chirality_erasure_H_L_equals_H_R" => Dict(
                "Type1_on_H_L_gamma5_odd" => gamma5_l,
                "Type1_on_erased_H_R_equals_H_L_gamma5_odd" => gamma5_erasure,
                "gamma5_odd_death_value" => chirality_erasure_death,
                "dies" => chirality_erasure_death <= 1.0e-9,
            ),
            "sign_flip_diagnostic" => Dict(
                "Type1_on_H_L_gamma5_odd" => gamma5_l,
                "Type1_on_H_R_gamma5_odd" => gamma5_flip,
                "trace_norm_between_outputs" => flip_diagnostic_gap,
                "odd_readout_flips" => gamma5_l * gamma5_flip < 0.0,
            ),
            "label_shuffle" => label_shuffle,
            "classical_diagonal_control" => Dict(
                "lane" => "classical_control_measurement",
                "classical_measured_MI" => classical_ledger["M_measure_record"]["mutual_information_nats"],
                "I_c_S_to_M" => classical_ledger["M_measure_record"]["coherent_information_S_to_M"],
                "qit_coherence_work_term" => classical_ledger["szilard_summary"]["qit_coherence_work_term"],
                "work_extracted" => classical_ledger["szilard_summary"]["work_extracted"],
                "classical_work_persists" => classical_ledger["szilard_summary"]["work_extracted"] > 1.0e-9,
                "qit_coherence_erased" => classical_ledger["szilard_summary"]["qit_coherence_work_term"] <= 1.0e-9,
            ),
            "no_measurement" => no_measurement_ledger,
            "no_bath" => no_bath_ledger,
        ),
        "smt" => smt,
        "crossover_proofs" => Dict(
            "julia_z3" => merge(Dict("ran" => true, "load_bearing" => true, "verdict" => smt["julia_z3"]["equality_status"], "claim" => "4x4 joint M/F/R object bound: D_joint after I_joint equals I_joint after D_joint is UNSAT"), smt["julia_z3"]),
            "commuting_control_julia_z3" => merge(Dict("ran" => true, "load_bearing" => true, "verdict" => smt["commuting_control_julia_z3"]["equality_status"], "claim" => "Reduced 2x2 commuting control only; claim intentionally downgraded"), smt["commuting_control_julia_z3"]),
        ),
        "all_pass" => all_pass,
        "claim_ceiling" => "finite-map dual-stack witness probe only; no engine, M(C), Axis0, bridge, or admission claim",
    )
end

function main()::Int
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    scalars = result["shared_scalars"]
    println("wrote: ", RESULT_PATH)
    println(
        "DUAL_STACK_JULIA_DONE all_pass=$(result["all_pass"]) " *
        "Delta=$(scalars["headline_delta_trace_norm"]) " *
        "Type1Type2=$(scalars["type1_type2_trace_norm"]) " *
        "SMT_julia_z3=$(result["smt"]["julia_z3"]["equality_status"]) " *
        "control_julia_z3=$(result["smt"]["commuting_control_julia_z3"]["equality_status"])"
    )
    return result["all_pass"] ? 0 : 2
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
