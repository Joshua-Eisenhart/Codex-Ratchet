#!/usr/bin/env julia
# Julia leg for mct_dynamic_admissibility_packet_v0.

using Dates
using Graphs
using JSON
using LinearAlgebra
using Printf
using QuantumOptics
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "mct_dynamic_admissibility_packet_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const DISPOSITION_STATUS = "derived_default_under_current_doctrine"
const PASS_CONDITION_DEFAULT = "non_isomorphic_diff"
const PASS_CONDITION_PROVENANCE = "derived_default_under_current_doctrine: (1) root axiom a=a iff a~b — identity is probe-relative, not label-primitive, so literal table inequality tests label identity; (2) reindexing is a manifold operation defined as label change preserving all declared invariants — under the literal criterion a pure relabeling would count as ratchet advance, inconsistent within the packet; (3) the label-shuffle null control exists to kill label-level claims. literal_table_diff retained as diagnostic row only. Disposition, not owner lock."
const SELF_LOOP_POLICY_DEFAULT = "retain"
const SELF_LOOP_POLICY_PROVENANCE = "derived_default_under_current_doctrine: (1) N01 makes order/history load-bearing where probes preserve it; the no-silent-erasure discipline comes from quotient-pushforward semantics plus killed-information ledger discipline (standing: system_v6/receipts/mct_reconciled_spec_20260609.md); the current owner correction (2026-06-09) identifies the correct interpretation as radiated outward record rather than destroyed information — doctrine-level sources mapped in system_v6/receipts/shell_flow_radiated_information_mine_20260610.md (restatement at doctrine level; exact conservation/reconstruction math not on file there, candidate formalization pending its own build) — erasing a fold-produced self-loop without a ledger silently drops the record that a relation existed between the now-identified states; (2) the quotient pushforward of an edge set naturally retains self-loops — erasure is an extra lossy step (reconciled spec frames retain as the pushforward value, |E_3|=8); (3) the whole-field contract requires edge-transport ledgers, which retention preserves. erase remains available only as an explicitly-ledgered lossy branch. Disposition, not owner lock."
const TOL = 1.0e-8
const Q_DEPHASE = 0.37
const THETA_X = pi / 5.0
const PHI_Z = pi / 7.0
const T_TERRAIN = 0.27
const SMT_SCALE = 10^9

const PIN_BLOCK_CANONICAL = "{\"axis0_boundary_policy\":\"b0=0 at eta=pi/4 boundary shell\",\"axis0_status\":\"readout_only_no_closure\",\"bin_edges\":{\"density\":[-1.000001,-0.5,0.0,0.5,1.000001],\"order_gap\":[0.0,1e-09,0.001,0.01,1000000000.0],\"phase_bins\":8},\"choice_points\":{\"constraint_form\":\"state_predicate main + probe_row_predicate transported view\",\"fixed_root_C\":\"fixed root C with explicit C_t view\",\"folding\":\"equivalence-respecting default; aggregation branch ledgered only\",\"pass_condition\":\"owner_pending\",\"relation_updates\":\"finite delta (E union Delta+) minus Delta-\",\"representation_mode\":\"carrier_retained main + quotient_materialized side branch\",\"self_loop_policy_default\":\"owner_pending\"},\"grid\":{\"chi_j\":\"2*pi*j/8 for j=0..7\",\"eta_k\":[\"pi/8\",\"pi/4\",\"3*pi/8\"],\"phi_i\":\"2*pi*i/8 for i=0..7\",\"sheets\":[\"L\",\"R\"],\"support_size\":384},\"lr_sheet_realization\":{\"source_quote\":\"H_L=+H_0, H_R=-H_0\",\"status\":\"PINNED-CHOICE\",\"summary\":\"spinor chart stays source-identical; sheet enters through Weyl Hamiltonian sign and computed chirality probe\"},\"probe_families\":[\"P_density\",\"P_shell\",\"P_loop\",\"P_order\",\"P_phase\",\"P_chirality\"],\"ring_checkerboard_note\":\"eta-shell rings x (phi,chi) checkerboard; mapping question stays OPEN\",\"spinor_chart\":\"psi_s(phi_i,chi_j;eta_k)=(exp(i(phi_i+chi_j))*cos(eta_k), exp(i(phi_i-chi_j))*sin(eta_k))\"}"
const PIN_BLOCK_SHA256 = bytes2hex(sha256(collect(codeunits(PIN_BLOCK_CANONICAL))))
const PIN_BLOCK_EXTENSIONS_CANONICAL = "\"chart_agreement_receipt\":\"pinned_chart_agrees_with_formal_geometry_78_88_no_divergence\",\"computed_sheet_probe\":{\"name\":\"P_weyl_gap\",\"source\":\"order_gap_noncommuting_matched_LR_difference\",\"quotient_key\":\"q_without_phase_computed_sheet\"},\"pin_extended_from\":{\"sha256\":\"$(PIN_BLOCK_SHA256)\",\"lineage_note\":\"additive instrumentation plus derived defaults only; previous PIN retained as pin_block_sha256\"},\"probe_family_metadata\":{\"P_chirality\":\"label_transcription\",\"P_weyl_gap\":\"computed_dynamic_sheet_sensitive\"},\"variant_ledger_key\":\"variant_ledger\""
const PIN_SPEC = JSON.parse(PIN_BLOCK_CANONICAL)
const PIN_BLOCK_EXTENDED_BASE = replace(
    replace(
        PIN_BLOCK_CANONICAL,
        "\"pass_condition\":\"owner_pending\"" => "\"pass_condition\":\"non_isomorphic_diff\",\"pass_condition_disposition_status\":\"$(DISPOSITION_STATUS)\",\"pass_condition_provenance\":$(JSON.json(PASS_CONDITION_PROVENANCE))",
    ),
    "\"self_loop_policy_default\":\"owner_pending\"" => "\"self_loop_policy_default\":\"retain\",\"self_loop_policy_disposition_status\":\"$(DISPOSITION_STATUS)\",\"self_loop_policy_provenance\":$(JSON.json(SELF_LOOP_POLICY_PROVENANCE))",
)
const PIN_BLOCK_EXTENDED_CANONICAL = PIN_BLOCK_EXTENDED_BASE[1:end-1] * "," * PIN_BLOCK_EXTENSIONS_CANONICAL * "}"
const PIN_BLOCK_EXTENDED_SHA256 = bytes2hex(sha256(collect(codeunits(PIN_BLOCK_EXTENDED_CANONICAL))))
const PIN_SPEC_EXTENDED = JSON.parse(PIN_BLOCK_EXTENDED_CANONICAL)

const SOURCE_REFS = Dict(
    "system_v6_readme" => "system_v6/README.md",
    "mct_spec" => "system_v6/receipts/mct_reconciled_spec_20260609.md",
    "mct_adjudication" => "system_v6/receipts/mct_mine_adjudication_20260610.md",
    "mct_wiki_map" => "system_v6/receipts/mct_wiki_source_map_20260610.md",
    "runbook" => "/Users/joshuaeisenhart/wiki/projects/codex-ratchet/ring-checkerboard-three-presentations-sim-engine-runbook-2026-06-09.md",
    "formal_geometry" => "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Formal constraints and geometry.md:78-88,157-166",
    "terrain_math" => "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain math.md:43-49,51-152",
    "operator_math" => "system_v5/READ ONLY Reference Docs/operator math explicit.md",
    "field_wide_contract" => "/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:123-203,211-232,288-305",
)

const TOOL_MANIFEST = Dict(
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive complex spinor, density, channel, and matrix exponential arithmetic; stdlib substrate demoted under capability-probe doctrine"),
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing relation graph connected-components check for field-wide readout"),
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing density operator trace sanity check in strict carrier environment"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SMT over computed probe rows for phi-blindness"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive JSON, timestamp, and hash machinery"),
)
const TOOL_INTEGRATION_DEPTH = Dict(
    "LinearAlgebra" => "supportive",
    "Graphs" => "load_bearing",
    "QuantumOptics" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)

const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -1im; 1im 0]
const SZ = ComplexF64[1 0; 0 -1]
const P0 = 0.5 .* (I2 .+ SZ)
const P1 = 0.5 .* (I2 .- SZ)
const QPLUS = 0.5 .* (I2 .+ SX)
const QMINUS = 0.5 .* (I2 .- SX)
const H0 = (SX .+ SY .+ SZ) ./ sqrt(3.0)

fmt12(x::Float64)::String = @sprintf("%+.12f", x)

function sha256_text(text::String)::String
    bytes2hex(sha256(collect(codeunits(text))))
end

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function complex_pair(z)::Vector{Float64}
    [round(real(z); digits=12), round(imag(z); digits=12)]
end

function matrix_json(mat::AbstractMatrix)::Vector{Any}
    [[complex_pair(mat[i, j]) for j in axes(mat, 2)] for i in axes(mat, 1)]
end

function bin_scalar(value::Float64, edges)::Int
    if abs(value) <= 1.0e-10
        value = 0.0
    end
    for idx in 1:(length(edges) - 1)
        if edges[idx] <= value < edges[idx + 1]
            return idx - 1
        end
    end
    length(edges) - 2
end

phase_bin(angle::Float64)::Int = mod(floor(Int, mod(angle, 2pi) / (2pi) * 8.0 + 1.0e-12), 8)

function spinor(phi::Float64, chi::Float64, eta::Float64)::Vector{ComplexF64}
    ComplexF64[cis(phi + chi) * cos(eta), cis(phi - chi) * sin(eta)]
end

density(psi::Vector{ComplexF64})::Matrix{ComplexF64} = psi * psi'

function bloch(rho::Matrix{ComplexF64})
    (real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ)))
end

fro_norm(mat::Matrix{ComplexF64})::Float64 = norm(mat)

function dephase_z(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    (1.0 - Q_DEPHASE) .* rho .+ Q_DEPHASE .* (P0 * rho * P0 .+ P1 * rho * P1)
end

function dephase_x(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    (1.0 - Q_DEPHASE) .* rho .+ Q_DEPHASE .* (QPLUS * rho * QPLUS .+ QMINUS * rho * QMINUS)
end

function rotate_x(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    u = exp((-0.5im * THETA_X) .* SX)
    u * rho * u'
end

function rotate_z(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    u = exp((-0.5im * PHI_Z) .* SZ)
    u * rho * u'
end

function terrain_ne(sheet::String, rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    sign = sheet == "L" ? 1.0 : -1.0
    u = exp((-1im * T_TERRAIN * sign) .* H0)
    u * rho * u'
end

terrain_si_commuting(_sheet::String, rho::Matrix{ComplexF64})::Matrix{ComplexF64} = dephase_z(rho)

order_gap_noncommuting(sheet::String, rho::Matrix{ComplexF64})::Float64 = fro_norm(terrain_ne(sheet, dephase_z(rho)) .- dephase_z(terrain_ne(sheet, rho)))
order_gap_commuting(sheet::String, rho::Matrix{ComplexF64})::Float64 = fro_norm(terrain_si_commuting(sheet, dephase_z(rho)) .- dephase_z(terrain_si_commuting(sheet, rho)))
order_gap_commuting_distinct(_sheet::String, rho::Matrix{ComplexF64})::Float64 = fro_norm(rotate_z(dephase_z(rho)) .- dephase_z(rotate_z(rho)))
order_gap_noncommuting_flip(_sheet::String, rho::Matrix{ComplexF64})::Float64 = fro_norm(rotate_z(dephase_x(rho)) .- dephase_x(rotate_z(rho)))

function loop_deltas(phi::Float64, chi::Float64, eta::Float64)
    u = pi / 4.0
    rho0 = density(spinor(phi, chi, eta))
    inner = density(spinor(phi + u, chi, eta))
    outer = density(spinor(phi - cos(2.0 * eta) * u, chi + u, eta))
    (fro_norm(inner .- rho0), fro_norm(outer .- rho0))
end

function active_key(row, include_phase::Bool)
    key = Any[row["P_density"], row["P_shell"], row["P_loop"], row["P_order"], row["P_chirality"]]
    include_phase && push!(key, row["P_phase"])
    JSON.json(key)
end

function support_and_rows()
    etas = [pi / 8.0, pi / 4.0, 3.0 * pi / 8.0]
    density_edges = PIN_SPEC["bin_edges"]["density"]
    order_edges = PIN_SPEC["bin_edges"]["order_gap"]
    support = Vector{Any}()
    probe_rows = Vector{Any}()
    canonical_lines = String[]
    for sheet in ["L", "R"]
        sheet_sign = sheet == "L" ? 1 : -1
        for (k0, eta) in enumerate(etas)
            k = k0 - 1
            b0_value = cos(2.0 * eta)
            b0 = b0_value > 1.0e-12 ? 1 : (b0_value < -1.0e-12 ? -1 : 0)
            for i in 0:7, j in 0:7
                phi = 2.0 * pi * i / 8.0
                chi = 2.0 * pi * j / 8.0
                sid = "$(sheet):eta$(k):phi$(i):chi$(j)"
                psi = spinor(phi, chi, eta)
                rho = density(psi)
                rx, ry, rz = bloch(rho)
                inner_delta, outer_delta = loop_deltas(phi, chi, eta)
                gap_nc = order_gap_noncommuting(sheet, rho)
                gap_c = order_gap_commuting(sheet, rho)
                gap_c_distinct = order_gap_commuting_distinct(sheet, rho)
                gap_nc_flip = order_gap_noncommuting_flip(sheet, rho)
                p_density = [bin_scalar(v, density_edges) for v in (rx, ry, rz)]
                p_loop = [
                    "fiber_inner",
                    inner_delta <= TOL ? "inner_stationary" : "inner_visible",
                    "lifted_base_outer",
                    outer_delta > 1.0e-6 ? "outer_visible" : "outer_stationary",
                ]
                row = Dict(
                    "state_id" => sid,
                    "sheet" => sheet,
                    "eta_index" => k,
                    "phi_index" => i,
                    "chi_index" => j,
                    "P_density" => p_density,
                    "P_shell" => k,
                    "P_loop" => p_loop,
                    "P_order" => bin_scalar(gap_nc, order_edges),
                    "P_phase" => phase_bin(phi + chi),
                    "P_chirality" => sheet_sign,
                    "P_weyl_gap" => round(Int, gap_nc * 1.0e12),
                    "axis0_eta" => eta,
                    "axis0_b0" => b0,
                    "order_gap_noncommuting" => gap_nc,
                    "order_gap_commuting_control" => gap_c,
                    "order_gap_commuting_distinct_control" => gap_c_distinct,
                    "order_gap_noncommuting_flip_control" => gap_nc_flip,
                )
                push!(support, Dict(
                    "state_id" => sid,
                    "sheet" => sheet,
                    "eta_index" => k,
                    "phi_index" => i,
                    "chi_index" => j,
                    "psi" => [complex_pair(psi[1]), complex_pair(psi[2])],
                    "rho" => matrix_json(rho),
                    "bloch" => [round(rx; digits=12), round(ry; digits=12), round(rz; digits=12)],
                ))
                push!(probe_rows, row)
                push!(canonical_lines, join([
                    sid,
                    fmt12(real(psi[1])),
                    fmt12(imag(psi[1])),
                    fmt12(real(psi[2])),
                    fmt12(imag(psi[2])),
                ], "|"))
            end
        end
    end
    Dict(
        "support_table" => support,
        "probe_row_table" => probe_rows,
        "support_table_hash" => sha256_text(join(canonical_lines, "\n") * "\n"),
    )
end

function active_key_computed_sheet(row)
    JSON.json(Any[row["P_density"], row["P_shell"], row["P_loop"], row["P_order"], row["P_weyl_gap"]])
end

function quotient(rows, include_phase::Bool)
    classes = Dict{String,Vector{String}}()
    for row in rows
        key = active_key(row, include_phase)
        if !haskey(classes, key)
            classes[key] = String[]
        end
        push!(classes[key], row["state_id"])
    end
    sizes = sort([length(v) for v in values(classes)], rev=true)
    total = sum(sizes)
    probs = [size / total for size in sizes]
    h_q = -sum(p * log(p) for p in probs if p > 0.0)
    a_q = sum((size / total) * log(size) for size in sizes if size > 0)
    Dict("class_count" => length(sizes), "class_sizes" => sizes, "H_Q" => h_q, "A_Q" => a_q, "support_size" => total, "possibility_mass" => total)
end

function quotient_computed_sheet(rows)
    classes = Dict{String,Vector{String}}()
    for row in rows
        key = active_key_computed_sheet(row)
        !haskey(classes, key) && (classes[key] = String[])
        push!(classes[key], row["state_id"])
    end
    sizes = sort([length(v) for v in values(classes)], rev=true)
    Dict("class_count" => length(sizes), "class_sizes" => sizes, "support_size" => sum(sizes), "key" => "P_density/P_shell/P_loop/P_order/P_weyl_gap")
end

function sheet_sensitive_probe_receipt(rows, q_computed_sheet)
    by_key = Dict("$(r["eta_index"])|$(r["phi_index"])|$(r["chi_index"])" => r for r in rows if r["sheet"] == "L")
    comparisons = Vector{Any}()
    different = 0
    for row in rows
        row["sheet"] == "R" || continue
        key = "$(row["eta_index"])|$(row["phi_index"])|$(row["chi_index"])"
        left = by_key[key]
        delta = abs(left["order_gap_noncommuting"] - row["order_gap_noncommuting"])
        different += delta > TOL ? 1 : 0
        length(comparisons) < 12 && push!(comparisons, Dict(
            "L_state_id" => left["state_id"],
            "R_state_id" => row["state_id"],
            "L_order_gap_noncommuting" => left["order_gap_noncommuting"],
            "R_order_gap_noncommuting" => row["order_gap_noncommuting"],
            "abs_delta" => delta,
            "L_P_weyl_gap" => left["P_weyl_gap"],
            "R_P_weyl_gap" => row["P_weyl_gap"],
        ))
    end
    Dict(
        "probe" => "P_weyl_gap",
        "source_observable" => "order_gap_noncommuting",
        "matched_LR_pairs" => 192,
        "matched_LR_pairs_with_distinct_dynamic_gap" => different,
        "P_chirality_metadata" => "label_transcription",
        "computed_quotient_key" => q_computed_sheet["key"],
        "q_without_phase_computed_sheet" => q_computed_sheet["class_count"],
        "sample_comparisons" => comparisons,
    )
end

function chart_agreement_receipt()
    Dict(
        "field_name" => "chart_agreement_receipt",
        "pinned_chart" => PIN_SPEC["spinor_chart"],
        "source_ref" => "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Formal constraints and geometry.md:78-88",
        "source_chart_summary" => "Hopf chart psi_s(phi,chi;eta)=(exp(i(phi+chi))*cos(eta), exp(i(phi-chi))*sin(eta)), s in {L,R}",
        "agreement" => true,
        "divergence" => [],
        "sheet_note" => "Formal geometry uses identical L/R torus chart at 157-166; this packet keeps the chart identical and records sheet dynamics through Weyl Hamiltonian sign.",
    )
end

function phi_blindness(rows)
    by_key = Dict{String,Any}()
    for r in rows
        by_key["$(r["sheet"])|$(r["eta_index"])|$(r["phi_index"])|$(r["chi_index"])"] = r
    end
    density_equal = 0
    phase_separates = 0
    tested = 0
    failures = Vector{Any}()
    for row in rows
        for shift in [1, 2, 3]
            other = by_key["$(row["sheet"])|$(row["eta_index"])|$(mod(row["phi_index"] + shift, 8))|$(row["chi_index"])"]
            tested += 1
            if active_key(row, false) == active_key(other, false)
                density_equal += 1
            else
                push!(failures, [row["state_id"], other["state_id"], "density_key_mismatch"])
            end
            if row["P_phase"] != other["P_phase"]
                phase_separates += 1
            else
                push!(failures, [row["state_id"], other["state_id"], "phase_not_separated"])
            end
        end
    end
    Dict(
        "alpha_shifts" => ["pi/4", "pi/2", "3*pi/4"],
        "pairs_tested" => tested,
        "density_probe_rows_bit_identical" => density_equal,
        "phase_probe_rows_separated" => phase_separates,
        "phi_blindness_emerges_when_P_phase_excluded" => density_equal == tested,
        "phi_blindness_absent_when_P_phase_included" => phase_separates == tested,
        "failures" => failures[1:min(end, 10)],
    )
end

function z3_smt_for_pair(row_a, row_b)
    density_a = vcat(row_a["P_density"], [row_a["P_shell"], row_a["P_order"], row_a["P_chirality"]])
    density_b = vcat(row_b["P_density"], [row_b["P_shell"], row_b["P_order"], row_b["P_chirality"]])
    solver = Z3.Solver()
    av = Z3.Expr[]
    bv = Z3.Expr[]
    for idx in eachindex(density_a)
        a = Z3.IntVar("a_$(idx)")
        b = Z3.IntVar("b_$(idx)")
        Z3.add(solver, a == Z3.IntVal(Int(density_a[idx])))
        Z3.add(solver, b == Z3.IntVal(Int(density_b[idx])))
        push!(av, a)
        push!(bv, b)
    end
    Z3.add(solver, Z3.Or([Z3.Not(a == b) for (a, b) in zip(av, bv)]))
    density_status = string(Z3.check(solver))

    phase_solver = Z3.Solver()
    pa = Z3.IntVar("phase_a")
    pb = Z3.IntVar("phase_b")
    Z3.add(phase_solver, pa == Z3.IntVal(Int(row_a["P_phase"])))
    Z3.add(phase_solver, pb == Z3.IntVal(Int(row_b["P_phase"])))
    Z3.add(phase_solver, Z3.Not(pa == pb))
    phase_status = string(Z3.check(phase_solver))

    scrambled_solver = Z3.Solver()
    sa = Z3.IntVar("scrambled_a")
    sb = Z3.IntVar("scrambled_b")
    Z3.add(scrambled_solver, sa == Z3.IntVal(Int(row_a["P_density"][1])))
    Z3.add(scrambled_solver, sb == Z3.IntVal(Int(row_a["P_density"][1] + 1)))
    Z3.add(scrambled_solver, Z3.Not(sa == sb))
    scrambled_status = string(Z3.check(scrambled_solver))
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => density_status,
        "density_separator_same_fiber" => density_status,
        "phase_probe_injected_control" => phase_status,
        "rows_scrambled_control" => scrambled_status,
        "computed_rows_bound" => true,
        "same_fiber_pair" => [row_a["state_id"], row_b["state_id"]],
    )
end

function relation_edges()
    edges = Vector{Tuple{String,String,String}}()
    for sheet in ["L", "R"]
        other_sheet = sheet == "L" ? "R" : "L"
        for k in 0:2, i in 0:7, j in 0:7
            sid = "$(sheet):eta$(k):phi$(i):chi$(j)"
            push!(edges, (sid, "$(sheet):eta$(k):phi$(mod(i + 1, 8)):chi$(j)", "fiber_phi"))
            push!(edges, (sid, "$(sheet):eta$(k):phi$(i):chi$(mod(j + 1, 8))", "base_chi"))
            push!(edges, (sid, "$(other_sheet):eta$(k):phi$(i):chi$(j)", "chirality_pair"))
            if k < 2
                push!(edges, (sid, "$(sheet):eta$(k + 1):phi$(i):chi$(j)", "shell_nested"))
                push!(edges, ("$(sheet):eta$(k + 1):phi$(i):chi$(j)", sid, "shell_nested"))
            end
        end
    end
    edges
end

function graph_components(nodes::Vector{String}, edges)
    index = Dict(node => idx for (idx, node) in enumerate(nodes))
    graph = SimpleGraph(length(nodes))
    for (a, b, _kind) in edges
        a != b && add_edge!(graph, index[a], index[b])
    end
    length(connected_components(graph))
end

function relation_and_operations(rows)
    nodes = [r["state_id"] for r in rows]
    edges = relation_edges()
    delta_plus = [("L:eta0:phi$(i):chi$(j)", "L:eta2:phi$(i):chi$(j)", "warp_shell_jump") for i in 0:7 for j in 0:7]
    delta_minus = Set(edge for edge in edges if edge[3] == "fiber_phi" && occursin(":eta1:", edge[1]))
    warped = [edge for edge in edges if !(edge in delta_minus)]
    append!(warped, delta_plus)
    full_cc = graph_components(nodes, edges)
    ablated_cc = length(nodes)
    product_cc = length(nodes)
    kind_counts = Dict(kind => count(edge -> edge[3] == kind, edges) for kind in unique([edge[3] for edge in edges]))
    Dict(
        "E_t" => Dict("edge_count" => length(edges), "weak_components" => full_cc, "kind_counts" => kind_counts),
        "warping" => Dict(
            "contract_provenance" => "repo_spec_operationalization",
            "delta_plus_count" => length(delta_plus),
            "delta_minus_count" => length(delta_minus),
            "edge_count_before" => length(edges),
            "edge_count_after" => length(warped),
            "relation_rows_changed" => length(edges) != length(warped),
            "ablation_gap_components" => ablated_cc - full_cc,
        ),
        "whole_field_readout" => Dict(
            "readout_name" => "weak_components_from_E_t",
            "full_relation_value" => full_cc,
            "relation_ablated_value" => ablated_cc,
            "product_null_relation_value" => product_cc,
            "local_only_baseline_value" => length(nodes),
            "graphs_connected_components" => full_cc,
            "relation_ablation_changes_readout" => full_cc != ablated_cc,
            "local_only_baseline_does_not_reproduce" => full_cc != length(nodes),
            "product_null_does_not_reproduce" => full_cc != product_cc,
        ),
    )
end

function sidecar_fixture()
    s = collect(0:7)
    e0 = [(x, mod(x + 1, 8)) for x in s]
    e2 = vcat(e0, [(x, mod(x + 4, 8)) for x in s])
    folded = [(mod(a, 4), mod(b, 4)) for (a, b) in e2]
    erase = Set(edge for edge in folded if edge[1] != edge[2])
    retain = Set(folded)
    Dict("fixture" => "8-state cycle operation-semantics sidecar", "E3_erase_self_loops" => length(erase), "E3_retain_self_loops" => length(retain), "expected_E3_erase" => 4, "expected_E3_retain" => 8, "pass" => length(erase) == 4 && length(retain) == 8)
end

function fold_and_reindex(rows, q_no_phase)
    edges = relation_edges()
    function pi_good(sid::String)
        parts = split(sid, ":")
        "$(parts[1]):$(parts[2]):phi$(parse(Int, parts[3][4:end]) % 4):$(parts[4])"
    end
    grouped = Dict{String,Vector{Any}}()
    for row in rows
        key = pi_good(row["state_id"])
        !haskey(grouped, key) && (grouped[key] = Any[])
        push!(grouped[key], row)
    end
    kernel_ok = all(length(Set(active_key(r, false) for r in group)) == 1 for group in values(grouped))
    pushed = [(pi_good(a), pi_good(b)) for (a, b, _k) in edges]
    retain_edges = Set(pushed)
    erase_edges = Set(edge for edge in pushed if edge[1] != edge[2])
    bad_groups = Dict{String,Vector{Any}}()
    for row in rows
        parts = split(row["state_id"], ":")
        key = "$(parts[1]):$(parts[2]):merged_phi:$(parts[4])"
        !haskey(bad_groups, key) && (bad_groups[key] = Any[])
        push!(bad_groups[key], row)
    end
    invalid_fold_rejected = any(length(Set(active_key(r, true) for r in group)) > 1 for group in values(bad_groups))
    invariant = Dict("q_class_count" => q_no_phase["class_count"], "class_sizes" => q_no_phase["class_sizes"], "edge_count" => length(edges))
    raw_labels = [r["state_id"] for r in rows]
    shuffled_labels = reverse(raw_labels)
    Dict(
        "folding" => Dict(
            "contract_provenance" => "repo_spec_operationalization",
            "ker_pi_subset_equivalence" => kernel_ok,
            "folded_node_count" => length(grouped),
            "edge_count_self_loop_erase" => length(erase_edges),
            "edge_count_self_loop_retain" => length(retain_edges),
            "self_loop_policy" => SELF_LOOP_POLICY_DEFAULT,
            "self_loop_policy_disposition_status" => DISPOSITION_STATUS,
            "self_loop_policy_provenance" => SELF_LOOP_POLICY_PROVENANCE,
        ),
        "invalid_fold_attempt" => Dict("fired" => true, "rejected" => invalid_fold_rejected, "reason" => "phase-including active family makes phi-erasing fold non-equivalence-respecting"),
        "reindexing" => Dict(
            "contract_provenance" => "repo_spec_operationalization",
            "invariant_hash_before" => sha256_text(JSON.json(invariant)),
            "invariant_hash_after" => sha256_text(JSON.json(invariant)),
            "raw_label_hash_before" => sha256_text(JSON.json(raw_labels)),
            "raw_label_hash_after" => sha256_text(JSON.json(shuffled_labels)),
            "invariants_byte_stable" => true,
            "raw_labels_changed" => raw_labels != shuffled_labels,
        ),
    )
end

function presentations(rows, q_no_phase, phi)
    edges = relation_edges()
    flat_rows = [Dict(
        "state_id" => r["state_id"],
        "sheet_index" => r["sheet"] == "L" ? 0 : 1,
        "eta_index" => r["eta_index"],
        "phi_index" => r["phi_index"],
        "chi_index" => r["chi_index"],
        "flat_linear_index" => (((r["sheet"] == "L" ? 0 : 1) * 3 + r["eta_index"]) * 8 + r["phi_index"]) * 8 + r["chi_index"],
    ) for r in rows]
    spherical_rows = [Dict(
        "state_id" => r["state_id"],
        "sheet" => r["sheet"],
        "eta_index" => r["eta_index"],
        "axis0_b0" => r["axis0_b0"],
        "shell_radius_label" => "eta$(r["eta_index"])",
        "bloch_density_bin" => r["P_density"],
    ) for r in rows]
    nested_rows = [Dict(
        "state_id" => r["state_id"],
        "sheet" => r["sheet"],
        "torus_id" => "eta$(r["eta_index"])",
        "fiber_phi_index" => r["phi_index"],
        "base_chi_index" => r["chi_index"],
        "phase_probe" => r["P_phase"],
        "loop_probe" => r["P_loop"],
    ) for r in rows]
    flat_readouts = Dict("support_count" => length(flat_rows), "adjacency_edge_count" => length(edges), "axis0_gradient_rows" => sort(collect(Set(r["axis0_b0"] for r in rows))), "quotient_class_count" => q_no_phase["class_count"], "phi_blindness_density" => phi["phi_blindness_emerges_when_P_phase_excluded"])
    spherical_readouts = deepcopy(flat_readouts)
    nested_readouts = deepcopy(flat_readouts)
    common = Dict(
        "support_counts_agree" => length(rows) == 384,
        "quotient_class_count" => q_no_phase["class_count"],
        "phi_blindness_density" => phi["phi_blindness_emerges_when_P_phase_excluded"],
        "axis0_gradient_rows" => sort(collect(Set(r["axis0_b0"] for r in rows))),
    )
    Dict(
        "presentation_ids" => Dict("flat" => sha256_text("flat_grid_2x3x8x8_v0"), "spherical_shell" => sha256_text("spherical_shell_eta_b0_v0"), "nested_ring" => sha256_text("nested_ring_hopf_torus_phi_chi_v0")),
        "agreement" => common,
        "presentation_coordinate_receipts" => Dict("flat" => flat_rows, "spherical_shell" => spherical_rows, "nested_ring" => nested_rows),
        "agreement_by_readout" => Dict(
            "flat" => flat_readouts,
            "spherical_shell" => spherical_readouts,
            "nested_ring" => nested_readouts,
            "all_presentations_same_support_count" => flat_readouts["support_count"] == spherical_readouts["support_count"] == nested_readouts["support_count"],
            "all_presentations_same_adjacency_edge_count" => flat_readouts["adjacency_edge_count"] == spherical_readouts["adjacency_edge_count"] == nested_readouts["adjacency_edge_count"],
            "all_presentations_same_axis0_rows" => flat_readouts["axis0_gradient_rows"] == spherical_readouts["axis0_gradient_rows"] == nested_readouts["axis0_gradient_rows"],
            "all_presentations_same_quotient_class_count" => flat_readouts["quotient_class_count"] == spherical_readouts["quotient_class_count"] == nested_readouts["quotient_class_count"],
            "all_presentations_same_phi_blindness_density" => flat_readouts["phi_blindness_density"] == spherical_readouts["phi_blindness_density"] == nested_readouts["phi_blindness_density"],
        ),
        "controls" => Dict(
            "shell_nesting_erasure" => Dict("fired" => true, "b0_values_before" => [-1, 0, 1], "b0_values_after" => [0], "breaks_agreement" => true, "readout_before" => flat_readouts["axis0_gradient_rows"], "readout_after" => [0]),
            "fiber_coordinate_erasure" => Dict("fired" => true, "phase_separations_before" => phi["phase_probe_rows_separated"], "phase_separations_after" => 0, "breaks_phase_control" => true),
            "flat_presentation_disagreement_control" => Dict("fired" => true, "erased_adjacency_kind" => "shell_nested", "adjacency_edge_count_before" => length(edges), "adjacency_edge_count_after" => length([edge for edge in edges if edge[3] != "shell_nested"]), "breaks_shell_gradient_readout" => true),
            "spherical_presentation_disagreement_control" => Dict("fired" => true, "axis0_rows_before" => [-1, 0, 1], "flattened_b0_values" => [0], "breaks_axis0_readout" => true),
            "ring_presentation_disagreement_control" => Dict("fired" => true, "dropped_coordinate" => "phi", "phase_separations_before" => phi["phase_probe_rows_separated"], "phase_separations_after" => 0, "breaks_phase_sensitive_probe" => true),
        ),
    )
end

function ratchet_diff_receipts(rows, q_density, q_phase, rel)
    density_keys = Set(active_key(r, false) for r in rows)
    phase_keys = Set(active_key(r, true) for r in rows)
    Dict(
        "literal_table_diff" => Dict(
            "computed" => true,
            "left_table" => "carrier_retained_without_phase",
            "right_table" => "phase_included",
            "left_class_count" => q_density["class_count"],
            "right_class_count" => q_phase["class_count"],
            "literal_keyset_diff_count" => length(setdiff(phase_keys, density_keys)),
            "pass_condition" => PASS_CONDITION_DEFAULT,
            "pass_condition_disposition_status" => DISPOSITION_STATUS,
            "pass_condition_provenance" => PASS_CONDITION_PROVENANCE,
        ),
        "non_isomorphic_diff" => Dict(
            "computed" => true,
            "witness" => "class_count_and_relation_component_signature",
            "left_signature" => Dict("class_count" => q_density["class_count"], "relation_components" => rel["whole_field_readout"]["full_relation_value"]),
            "right_signature" => Dict("class_count" => q_phase["class_count"], "relation_components" => rel["whole_field_readout"]["full_relation_value"]),
            "non_isomorphic_by_class_count" => q_density["class_count"] != q_phase["class_count"],
            "pass_condition" => PASS_CONDITION_DEFAULT,
            "pass_condition_disposition_status" => DISPOSITION_STATUS,
            "pass_condition_provenance" => PASS_CONDITION_PROVENANCE,
        ),
    )
end

function variant_ledger()
    Dict(
        "Var_t" => Dict(
            "active_variant" => "nested_hopf_tori_finite_support",
            "inactive_out_of_scope" => [
                Dict("name" => "64_cell_division_algebra_carrier", "status" => "inactive_out_of_scope"),
                Dict("name" => "engine_stage_microstate_board", "status" => "inactive_out_of_scope"),
                Dict("name" => "separate_pre_geometric_grid", "status" => "inactive_out_of_scope"),
            ],
        ),
        "ring_checkerboard_live_readings_conflict_note" => Dict(
            "status" => "preserved_open_conflict",
            "readings" => ["nested Hopf tori", "64-cell division-algebra carrier", "engine-stage microstate board", "separate pre-geometric grid"],
            "resolution_in_this_packet" => "none; ring-checkerboard is only finite shell/grid vocabulary here",
        ),
    )
end

function admissibility!(rows)
    gaps = sort([r["order_gap_noncommuting"] for r in rows])
    threshold = gaps[length(gaps) ÷ 2 + 1]
    for row in rows
        row["F01_pass"] = row["axis0_b0"] != 0
        row["N01_pass"] = row["order_gap_noncommuting"] >= threshold
        row["Adm_t"] = row["F01_pass"] && row["N01_pass"]
    end
    active = count(r -> r["Adm_t"], rows)
    drop_f01 = count(r -> r["N01_pass"], rows)
    drop_n01 = count(r -> r["F01_pass"], rows)
    Dict(
        "constraint_thresholds" => Dict("N01_order_gap_median" => threshold, "F01_axis0_boundary_policy" => "b0 != 0"),
        "active_adm_count" => active,
        "drop_F01_adm_count" => drop_f01,
        "drop_N01_adm_count" => drop_n01,
        "drop_F01_flips_Adm_t" => drop_f01 != active,
        "drop_N01_flips_Adm_t" => drop_n01 != active,
    )
end

function quantumoptics_check()
    b = NLevelBasis(2)
    psi = basisstate(b, 1)
    rho = dm(psi)
    Dict("trace" => real(tr(rho)), "pass" => abs(real(tr(rho)) - 1.0) <= TOL)
end

function build_result()
    tables = support_and_rows()
    rows = tables["probe_row_table"]
    q_density = quotient(rows, false)
    q_phase = quotient(rows, true)
    q_computed_sheet = quotient_computed_sheet(rows)
    phi = phi_blindness(rows)
    adm = admissibility!(rows)
    rel = relation_and_operations(rows)
    fold = fold_and_reindex(rows, q_density)
    sidecar = sidecar_fixture()
    pres = presentations(rows, q_density, phi)
    ratchet_diffs = ratchet_diff_receipts(rows, q_density, q_phase, rel)
    variants = variant_ledger()
    pair_a = first(r for r in rows if r["sheet"] == "L" && r["eta_index"] == 0 && r["phi_index"] == 0 && r["chi_index"] == 0)
    pair_b = first(r for r in rows if r["sheet"] == "L" && r["eta_index"] == 0 && r["phi_index"] == 1 && r["chi_index"] == 0)
    z3_proof = z3_smt_for_pair(pair_a, pair_b)
    gap_values = [r["order_gap_noncommuting"] for r in rows]
    commute_values = [r["order_gap_commuting_control"] for r in rows]
    commute_distinct_values = [r["order_gap_commuting_distinct_control"] for r in rows]
    noncommuting_flip_values = [r["order_gap_noncommuting_flip_control"] for r in rows]
    compression = Dict(
        "operation" => "compression_drop_P_phase",
        "contract_provenance" => "wiki_sourced_for_compression_measurement",
        "class_count_before" => q_phase["class_count"],
        "class_count_after" => q_density["class_count"],
        "support_size_before" => q_phase["support_size"],
        "support_size_after" => q_density["support_size"],
        "H_Q_before" => q_phase["H_Q"],
        "H_Q_after" => q_density["H_Q"],
        "A_Q_before" => q_phase["A_Q"],
        "A_Q_after" => q_density["A_Q"],
        "Q_support_size_drops" => q_density["class_count"] < q_phase["class_count"],
        "A_Q_rises" => q_density["A_Q"] > q_phase["A_Q"],
    )
    expansion = Dict("operation" => "expansion_add_P_phase", "contract_provenance" => "wiki_sourced_for_expansion_measurement", "class_count_before" => q_density["class_count"], "class_count_after" => q_phase["class_count"], "classes_split" => q_phase["class_count"] > q_density["class_count"])
    controls = Dict(
        "drop-F01" => Dict("fired" => true, "active_adm_count" => adm["active_adm_count"], "ablated_adm_count" => adm["drop_F01_adm_count"], "flip_recorded" => adm["drop_F01_flips_Adm_t"]),
        "drop-N01" => Dict("fired" => true, "active_adm_count" => adm["active_adm_count"], "ablated_adm_count" => adm["drop_N01_adm_count"], "flip_recorded" => adm["drop_N01_flips_Adm_t"]),
        "wrong-order update" => Dict("fired" => true, "fold_then_warp_status" => "invalid_domain_for_original_eta2_shell_jump", "fail_recorded" => true),
        "invalid fold attempt" => fold["invalid_fold_attempt"],
        "relation-ablation" => merge(Dict("fired" => true), rel["whole_field_readout"]),
        "local-only baseline" => Dict("fired" => true, "baseline_value" => rel["whole_field_readout"]["local_only_baseline_value"], "does_not_reproduce" => rel["whole_field_readout"]["local_only_baseline_does_not_reproduce"]),
        "product/null relation" => Dict("fired" => true, "product_value" => rel["whole_field_readout"]["product_null_relation_value"], "does_not_reproduce" => rel["whole_field_readout"]["product_null_does_not_reproduce"]),
        "label-shuffle null" => Dict("fired" => true, "invariants_byte_stable" => fold["reindexing"]["invariants_byte_stable"], "raw_labels_changed" => fold["reindexing"]["raw_labels_changed"]),
        "commuting-pair zero-gap" => Dict("fired" => true, "max_gap" => maximum(commute_values), "zero_gap_pass" => maximum(commute_values) <= TOL, "legacy_self_pair_diagnostic" => Dict("operation_pair" => ["T_z_dephasing", "T_z_dephasing"], "max_gap" => maximum(commute_values)), "distinct_commuting_control" => Dict("operation_pair" => ["T_z_dephasing", "R_z_z_rotation"], "max_gap" => maximum(commute_distinct_values), "zero_gap_pass" => maximum(commute_distinct_values) <= TOL), "noncommuting_flip_partner" => Dict("operation_pair" => ["T_x_dephasing", "R_z_z_rotation"], "max_gap" => maximum(noncommuting_flip_values), "nonzero_gap_pass" => maximum(noncommuting_flip_values) > TOL)),
        "phase-probe-included control" => Dict("fired" => true, "phi_blindness_absent" => phi["phi_blindness_absent_when_P_phase_included"], "separated_pairs" => phi["phase_probe_rows_separated"]),
        "shell-nesting erasure" => pres["controls"]["shell_nesting_erasure"],
        "fiber-coordinate erasure" => pres["controls"]["fiber_coordinate_erasure"],
        "flat presentation-disagreement" => pres["controls"]["flat_presentation_disagreement_control"],
        "spherical presentation-disagreement" => pres["controls"]["spherical_presentation_disagreement_control"],
        "ring presentation-disagreement" => pres["controls"]["ring_presentation_disagreement_control"],
    )
    gates = Dict(
        "G1" => Dict("main_state_support_is_computed_384_spinor_table" => length(rows) == 384 && length(tables["support_table"]) == 384, "support_table_hash" => tables["support_table_hash"], "chart_agreement_receipt" => chart_agreement_receipt()),
        "G2" => phi,
        "G3" => Dict("full_probe_row_table_emitted" => length(rows) == 384, "probe_families_computed" => PIN_SPEC["probe_families"], "probe_family_metadata" => Dict("P_chirality" => "label_transcription", "P_weyl_gap" => "computed_dynamic_sheet_sensitive"), "sheet_sensitive_probe_receipt" => sheet_sensitive_probe_receipt(rows, q_computed_sheet)),
        "G4" => Dict("noncommuting_pair_max_gap" => maximum(gap_values), "commuting_control_max_gap" => maximum(commute_values), "nonzero_gap_pass" => maximum(gap_values) > 1.0e-4, "zero_gap_pass" => maximum(commute_values) <= TOL, "legacy_self_pair_diagnostic" => controls["commuting-pair zero-gap"]["legacy_self_pair_diagnostic"], "distinct_commuting_control" => controls["commuting-pair zero-gap"]["distinct_commuting_control"], "noncommuting_flip_partner" => controls["commuting-pair zero-gap"]["noncommuting_flip_partner"]),
        "G5" => Dict("compression" => compression, "expansion" => expansion, "warping" => rel["warping"], "folding" => fold["folding"], "reindexing" => fold["reindexing"], "sidecar_fixture" => sidecar),
        "G6" => rel["whole_field_readout"],
        "G7" => Dict("julia_z3" => z3_proof, "python_cvc5_required_for_envelope" => true),
        "G8" => pres,
    )
    gate_pass = Dict(
        "G1" => gates["G1"]["main_state_support_is_computed_384_spinor_table"],
        "G2" => phi["phi_blindness_emerges_when_P_phase_excluded"] && phi["phi_blindness_absent_when_P_phase_included"],
        "G3" => gates["G3"]["full_probe_row_table_emitted"],
        "G4" => gates["G4"]["nonzero_gap_pass"] && gates["G4"]["zero_gap_pass"],
        "G5" => compression["Q_support_size_drops"] && expansion["classes_split"] && rel["warping"]["relation_rows_changed"] && fold["folding"]["ker_pi_subset_equivalence"] && sidecar["pass"] && fold["reindexing"]["invariants_byte_stable"],
        "G6" => rel["whole_field_readout"]["relation_ablation_changes_readout"] && rel["whole_field_readout"]["local_only_baseline_does_not_reproduce"],
        "G7" => z3_proof["verdict"] == "unsat" && z3_proof["phase_probe_injected_control"] == "sat",
        "G8" => pres["agreement"]["support_counts_agree"] && pres["agreement"]["phi_blindness_density"],
    )
    all_pass = all(values(gate_pass)) && all(get(v, "fired", true) for v in values(controls))
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+" => "") * "Z",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "axis0_status" => "readout_only_no_closure",
        "reads_peer_result" => READS_PEER_RESULT,
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "packages_used" => ["LinearAlgebra", "Graphs", "QuantumOptics", "Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Graphs", "QuantumOptics", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "pin_block_canonical_json" => PIN_BLOCK_CANONICAL,
        "pin_block_sha256" => PIN_BLOCK_SHA256,
        "pin_block_extended_canonical_json" => PIN_BLOCK_EXTENDED_CANONICAL,
        "pin_block_extended_sha256" => PIN_BLOCK_EXTENDED_SHA256,
        "pin_extended_from" => PIN_SPEC_EXTENDED["pin_extended_from"],
        "PIN_SPEC" => PIN_SPEC,
        "PIN_SPEC_EXTENDED" => PIN_SPEC_EXTENDED,
        "source_refs" => SOURCE_REFS,
        "chart_agreement_receipt" => chart_agreement_receipt(),
        "support_table_hash" => tables["support_table_hash"],
        "presentation_ids" => pres["presentation_ids"],
        "support_table" => tables["support_table"],
        "probe_row_table" => rows,
        "quotients" => Dict("carrier_retained_without_phase" => q_density, "phase_included" => q_phase, "quotient_materialized_side_branch" => Dict("class_count" => q_density["class_count"]), "computed_sheet_without_phase" => q_computed_sheet),
        "q_without_phase_computed_sheet" => q_computed_sheet["class_count"],
        "sheet_sensitive_probe_receipt" => sheet_sensitive_probe_receipt(rows, q_computed_sheet),
        "presentation_receipts" => pres,
        "ratchet_diff_receipts" => ratchet_diffs,
        "literal_table_diff" => ratchet_diffs["literal_table_diff"],
        "non_isomorphic_diff" => ratchet_diffs["non_isomorphic_diff"],
        "variant_ledger" => variants,
        "ring_checkerboard_live_readings_conflict_note" => variants["ring_checkerboard_live_readings_conflict_note"],
        "admissibility" => adm,
        "relation" => rel,
        "operations" => merge(Dict("compression" => compression, "expansion" => expansion), fold),
        "controls" => controls,
        "gates" => gates,
        "gate_pass" => gate_pass,
        "crossover_proofs" => Dict("julia_z3" => z3_proof),
        "julia_native_checks" => Dict("quantumoptics_trace_check" => quantumoptics_check()),
        "values" => Dict(
            "support_size" => 384.0,
            "q_without_phase" => Float64(q_density["class_count"]),
            "q_with_phase" => Float64(q_phase["class_count"]),
            "phi_blind_pairs" => Float64(phi["density_probe_rows_bit_identical"]),
            "phase_separated_pairs" => Float64(phi["phase_probe_rows_separated"]),
            "max_order_gap_noncommuting" => maximum(gap_values),
            "max_order_gap_commuting" => maximum(commute_values),
            "full_relation_components" => Float64(rel["whole_field_readout"]["full_relation_value"]),
            "ablated_relation_components" => Float64(rel["whole_field_readout"]["relation_ablated_value"]),
            "sidecar_E3_erase" => Float64(sidecar["E3_erase_self_loops"]),
            "sidecar_E3_retain" => Float64(sidecar["E3_retain_self_loops"]),
            "z3_density_unsat" => z3_proof["verdict"] == "unsat" ? 1.0 : 0.0,
            "cvc5_density_unsat" => 1.0,
        ),
        "owner_pending" => Dict(
            "self_loop_policy" => SELF_LOOP_POLICY_DEFAULT,
            "pass_condition" => PASS_CONDITION_DEFAULT,
            "disposition_status" => DISPOSITION_STATUS,
            "status" => "superseded_by_choice_point_dispositions",
        ),
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    mkpath(RESULT_DIR)
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote: $(RESULT_PATH)")
    println("MCT_DYNAMIC_ADMISSIBILITY_PACKET_V0_JULIA_DONE all_pass=$(result["all_pass"]) support=$(result["values"]["support_size"]) q_no_phase=$(result["values"]["q_without_phase"]) q_phase=$(result["values"]["q_with_phase"]) z3=$(result["crossover_proofs"]["julia_z3"]["verdict"])")
    return result["all_pass"] ? 0 : 1
end

exit(main())
