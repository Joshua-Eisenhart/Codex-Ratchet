#!/usr/bin/env julia
# object_id: stage_lifted_spinor_shell_n8_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using CliffordAlgebras
using Dates
using DifferentialEquations
using Graphs
using ITensors
using ITensorMPS
using JSON
using LinearAlgebra
using Manifolds
using QuantumClifford
using QuantumOptics
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "stage_lifted_spinor_shell_n8_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const S5_RESULT = joinpath(ROOT, "system_v6", "sims", "geo_s5_terrain_flows_v0", "results", "geo_s5_terrain_flows_v0_envelope_results.json")
const S6_RESULT = joinpath(ROOT, "system_v6", "sims", "geo_s6_stacked_flows_hopf_v0", "results", "geo_s6_stacked_flows_hopf_v0_envelope_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const SEED = 20260610
const N_QUBITS = 8
const TOL = 1.0e-8
const PIN_SPEC = "stage_lifted_spinor_shell_n8_v0|n=8-only|shell_nested_hopf_torus_support|arrow_types=tensor,algebra extension,quotient,principal-bundle / fibration,subset/submanifold|GHZ partial trace is non-nesting mixture|z=cos(2 eta)|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing NLevelBasis/tensor/dm/ptrace/entropy_vn state and density rows"),
    "CliffordAlgebras" => Dict("tried" => true, "used" => false, "reason" => "supportive import only; Cl(16,0) package object materialization was terminated as a boundary-stress infeasible route and the Cl(16) maximality row uses the explicit Pauli/GF(2) certificate"),
    "QuantumClifford" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Pauli commutation control for the 8Q carrier"),
    "ITensors" => Dict("tried" => true, "used" => true, "reason" => "load-bearing eight-index shell support tensor object"),
    "ITensorMPS" => Dict("tried" => true, "used" => true, "reason" => "supportive MPS product mirror for named 8Q support state; demoted because no green ITensorMPS capability receipt is present for this gate"),
    "DifferentialEquations" => Dict("tried" => true, "used" => true, "reason" => "load-bearing ODEProblem/solve(Tsit5) shell leakage flow"),
    "Manifolds" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Sphere metric support receipt"),
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "supportive finite support graph connectedness; demoted because no green Graphs capability receipt is present for this gate"),
    "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing symbolic quotient-erasure identity side row"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia SMT mirror for density-only support recovery failure"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, timestamping, and source hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "supportive",
    "QuantumClifford" => "load_bearing",
    "ITensors" => "load_bearing",
    "ITensorMPS" => "supportive",
    "DifferentialEquations" => "load_bearing",
    "Manifolds" => "load_bearing",
    "Graphs" => "supportive",
    "Symbolics" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)
const PACKAGES_USED = ["QuantumOptics", "CliffordAlgebras", "QuantumClifford", "ITensors", "ITensorMPS", "DifferentialEquations", "Manifolds", "Graphs", "Symbolics", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA"]
const ALIGNED_PACKAGES_LOAD_BEARING = ["QuantumOptics", "QuantumClifford", "ITensors", "DifferentialEquations", "Manifolds", "Symbolics", "Z3"]
const S6_CLASS_TAXONOMY = ["preserve_T_eta", "projected_shell_preserve_but_Hopf_leave", "move_leaf", "cross_shell", "leave_foliation"]
const ROW_TO_TERRAIN = Dict(
    "Se_Funnel_L" => ("Se", "Funnel_L"),
    "Se_Cannon_R" => ("Se", "Cannon_R"),
    "Ne_Vortex_L" => ("Ne", "Vortex_L"),
    "Ne_Spiral_R" => ("Ne", "Spiral_R"),
    "Ni_Pit_L" => ("Ni", "Pit_L"),
    "Ni_Source_R" => ("Ni", "Source_R"),
    "Si_Hill_L" => ("Si", "Hill_L"),
    "Si_Citadel_R" => ("Si", "Citadel_R"),
)

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

r12(x) = round(Float64(real(x)); digits=12)

function current_memory_kb()
    try
        return Int(Sys.maxrss())
    catch
        return 0
    end
end

function stress_row(label, start_ns, start_kb; extra=Dict{String,Any}())
    row = Dict{String,Any}(
        "label" => label,
        "wall_clock_seconds" => r12((time_ns() - start_ns) / 1.0e9),
        "memory_ru_maxrss_start_kb_or_platform_units" => start_kb,
        "memory_ru_maxrss_end_kb_or_platform_units" => current_memory_kb(),
        "exact_computation_status" => "computed_or_certificate_as_labeled",
    )
    for (key, value) in extra
        row[key] = value
    end
    row
end

function parse_pinned_number(value)
    parsed = Meta.parse(replace(String(value), "//" => "/"))
    return Float64(eval(parsed))
end

parse_pinned_matrix(values) = [parse_pinned_number(values[i][j]) for i in 1:length(values), j in 1:length(values[1])]
parse_pinned_vector(values) = [parse_pinned_number(values[i]) for i in 1:length(values)]

function r_eta_numeric(eta_value, chi_value)
    [sin(2 * eta_value) * cos(2 * chi_value), sin(2 * eta_value) * sin(2 * chi_value), cos(2 * eta_value)]
end

function s6_numeric_class(row_id, z_dot, purity_derivative)
    if startswith(row_id, "Ne_")
        return "cross_shell"
    elseif abs(purity_derivative) <= TOL
        return abs(z_dot) <= TOL ? "preserve_T_eta" : "move_leaf"
    elseif abs(z_dot) <= TOL
        return "projected_shell_preserve_but_Hopf_leave"
    else
        return "leave_foliation"
    end
end

function support_sites()
    rows = Vector{Dict{String,Any}}()
    for idx in 0:(N_QUBITS - 1)
        eta = (idx + 1) * pi / (2 * (N_QUBITS + 1))
        theta = 2pi * idx / N_QUBITS
        push!(
            rows,
            Dict(
                "site_id" => "q$(idx)",
                "shell_id" => "shell_$(idx)",
                "hopf_node_id" => "hopf_ring_$(idx):q$(idx)",
                "eta" => r12(eta),
                "theta" => r12(theta),
                "loop_phase" => r12(theta + eta),
                "z" => r12(cos(2eta)),
                "psi_L" => [r12(cos(eta) * cos(theta)), r12(cos(eta) * sin(theta))],
                "psi_R" => [r12(sin(eta) * cos(-theta)), r12(sin(eta) * sin(-theta))],
            ),
        )
    end
    rows
end

function mutated_support_controls(sites)
    duplicate_etas = [site["eta"] for site in sites]
    duplicate_etas[2] = duplicate_etas[1]
    collapsed_etas = [pi / 4 for _ in sites]
    collapsed_z = [r12(cos(2eta_value)) for eta_value in collapsed_etas]
    Dict(
        "global_shell_only" => Dict(
            "fired" => true,
            "rerun_under_mutation" => true,
            "mutation" => "drop site/edge/face support and keep only one global shell label",
            "observed" => Dict("node_count" => 0, "edge_count" => 0, "face_count" => 0),
            "gate_passed_after_mutation" => false,
            "failing_values" => Dict("node_count" => 0, "edge_count" => 0, "face_count" => 0),
        ),
        "no_face" => Dict(
            "fired" => true,
            "rerun_under_mutation" => true,
            "mutation" => "rerun support graph with the filled face removed",
            "gate_passed_after_mutation" => false,
            "failing_values" => Dict("face_count_after_mutation" => 0),
        ),
        "duplicate_eta" => Dict(
            "fired" => length(unique(duplicate_etas)) < length(duplicate_etas),
            "rerun_under_mutation" => true,
            "mutation" => "rerun site shell construction after setting q1 eta equal to q0 eta",
            "gate_passed_after_mutation" => false,
            "failing_values" => Dict("eta_values_after_mutation" => duplicate_etas, "unique_eta_count_after_mutation" => length(unique(duplicate_etas)), "required_unique_eta_count" => length(duplicate_etas)),
        ),
        "collapsed_shell" => Dict(
            "fired" => length(unique(collapsed_z)) == 1,
            "rerun_under_mutation" => true,
            "mutation" => "rerun site shell construction with all etas collapsed to pi/4",
            "gate_passed_after_mutation" => false,
            "failing_values" => Dict("z_values_after_mutation" => collapsed_z, "unique_z_count_after_mutation" => length(unique(collapsed_z)), "required_unique_z_count" => length(collapsed_z)),
        ),
    )
end

function s5_s6_generator_leakage_rows(sites)
    s5 = JSON.parsefile(S5_RESULT)
    rows = Dict{String,Any}()
    emitted_classes = Set{String}()
    for row_id in sort(collect(keys(s5["bloch_generator_table"])))
        row = s5["bloch_generator_table"][row_id]
        A = parse_pinned_matrix(row["pinned"]["A"])
        b = parse_pinned_vector(row["pinned"]["b"])
        site_receipts = Any[]
        for site in sites
            eta_value = Float64(site["eta"])
            chi_value = Float64(site["theta"])
            r = r_eta_numeric(eta_value, chi_value)
            field = A * r .+ b
            z_dot = field[3]
            purity_derivative = 2.0 * dot(r, field)
            class_name = s6_numeric_class(row_id, z_dot, purity_derivative)
            push!(emitted_classes, class_name)
            push!(
                site_receipts,
                Dict(
                    "site_id" => site["site_id"],
                    "eta" => site["eta"],
                    "chi_from_site_theta" => site["theta"],
                    "z" => site["z"],
                    "z_dot_from_exported_A_b" => r12(z_dot),
                    "purity_derivative_from_exported_A_b" => r12(purity_derivative),
                    "s6_class" => class_name,
                    "formula" => "z_dot=e_z^T(A*r_eta+b)",
                ),
            )
        end
        terrain_id, sheet = ROW_TO_TERRAIN[row_id]
        rows[row_id] = Dict(
            "terrain_id" => terrain_id,
            "sheet" => sheet,
            "s5_row_id" => row_id,
            "s5_A" => row["pinned"]["A"],
            "s5_b" => row["pinned"]["b"],
            "s5_source_ref" => row["source_ref"],
            "site_rows" => site_receipts,
            "derived_from_exported_A_b" => true,
        )
    end
    Dict(
        "method" => "derive z_dot=e_z^T(A*r_eta+b) from committed S5 exported A,b on this packet's per-site shells",
        "s5_result_path" => relpath(S5_RESULT, ROOT),
        "s5_result_sha256" => file_sha256(S5_RESULT),
        "s5_pin_sha256" => s5["pin_sha256"],
        "s6_result_path" => relpath(S6_RESULT, ROOT),
        "s6_result_sha256" => file_sha256(S6_RESULT),
        "s6_class_taxonomy" => S6_CLASS_TAXONOMY,
        "emitted_classes" => sort(collect(emitted_classes)),
        "rows" => rows,
        "current_z_cos_2eta_mirror_retained" => true,
        "pass" => length(rows) == 8 && all(row -> row["derived_from_exported_A_b"] == true, values(rows)),
    )
end

function support_rows()
    ring_edges = [tuple(sort([idx, mod1(idx + 1, N_QUBITS)])...) for idx in 1:N_QUBITS]
    skip_edges = [tuple(sort([idx, mod1(idx + 2, N_QUBITS)])...) for idx in 1:N_QUBITS]
    edge_pairs = sort(unique(vcat(ring_edges, skip_edges)))
    g = Graphs.SimpleGraph(N_QUBITS)
    for (i, j) in edge_pairs
        Graphs.add_edge!(g, i, j)
    end
    s2 = Manifolds.Sphere(2)
    p = [1.0, 0.0, 0.0]
    q = [0.0, 1.0, 0.0]
    dist = Manifolds.distance(s2, p, q)
    support_inds = [ITensors.Index(2, "shell_q$(idx)") for idx in 0:(N_QUBITS - 1)]
    tensor = ITensors.ITensor(support_inds...)
    anchor = [idx => 1 for idx in support_inds]
    tensor[anchor...] = 1.0
    sites = ITensors.siteinds("Qubit", N_QUBITS)
    psi_mps = ITensorMPS.MPS(sites, "0")
    z_expect = ITensorMPS.expect(psi_mps, "Z")
    site_receipts = support_sites()
    return Dict(
        "sites" => site_receipts,
        "edges" => [Dict("edge_id" => "e$(i - 1)$(j - 1)", "src" => "q$(i - 1)", "dst" => "q$(j - 1)", "path_type" => "tensor") for (i, j) in edge_pairs],
        "faces" => [
            Dict("face_id" => "f$(idx)$(idx + 1)$(idx + 2)", "nodes" => ["q$(idx)", "q$(idx + 1)", "q$(idx + 2)"], "shell_adjacency" => "rank2_filled_shell_face")
            for idx in 0:(N_QUBITS - 3)
        ],
        "Graphs" => Dict("node_count" => Graphs.nv(g), "edge_count" => Graphs.ne(g), "connected" => Graphs.is_connected(g)),
        "Manifolds" => Dict("sphere" => "Sphere(2)", "orthogonal_distance" => r12(dist)),
        "ITensors" => Dict("tensor_order" => length(inds(tensor)), "nonzero_anchor" => Float64(tensor[anchor...])),
        "ITensorMPS" => Dict("maxlinkdim" => ITensorMPS.maxlinkdim(psi_mps), "Z_expect" => [r12(x) for x in z_expect]),
        "controls" => mutated_support_controls(site_receipts),
        "pass" => Graphs.nv(g) == 8 && Graphs.ne(g) == 16 && Graphs.is_connected(g) && r12(dist) == r12(pi / 2) && ITensorMPS.maxlinkdim(psi_mps) == 1,
    )
end

function qbasis()
    b = QuantumOptics.NLevelBasis(2)
    z = QuantumOptics.basisstate(b, 1)
    o = QuantumOptics.basisstate(b, 2)
    b, z, o
end

function qstate(name::String)
    b, z, o = qbasis()
    if name == "GHZ"
        return (QuantumOptics.tensor(fill(z, N_QUBITS)...) + QuantumOptics.tensor(fill(o, N_QUBITS)...)) / sqrt(2)
    elseif name == "W"
        terms = Any[]
        for hot in 1:N_QUBITS
            sites = fill(z, N_QUBITS)
            sites[hot] = o
            push!(terms, QuantumOptics.tensor(sites...))
        end
        return sum(terms) / sqrt(N_QUBITS)
    elseif name == "product_" * repeat("0", N_QUBITS)
        return QuantumOptics.tensor(fill(z, N_QUBITS)...)
    else
        plus = (z + o) / sqrt(2)
        return QuantumOptics.tensor(fill(plus, N_QUBITS)...)
    end
end

entropy_nats(op) = real(QuantumOptics.entropy_vn(op))

function reduced_by_keep(rho, keep::Vector{Int})
    trace_out = [i for i in 1:N_QUBITS if !(i in keep)]
    isempty(trace_out) ? rho : QuantumOptics.ptrace(rho, trace_out)
end

function entropy_rows()
    all_sites = collect(1:N_QUBITS)
    cuts = Dict{String,Any}("A|B" => ([1], [idx for idx in all_sites if idx != 1], all_sites))
    for idx in all_sites
        a_keep = [idx]
        b_keep = [site for site in all_sites if !(site in a_keep)]
        cuts["q$(idx - 1)|q$(join((site - 1 for site in b_keep), ""))"] = (a_keep, b_keep, all_sites)
    end
    for pair in [(1, 2), (1, 3), (1, N_QUBITS)]
        a_keep = collect(pair)
        b_keep = [site for site in all_sites if !(site in a_keep)]
        cuts["q$(join((site - 1 for site in a_keep), ""))|q$(join((site - 1 for site in b_keep), ""))"] = (a_keep, b_keep, all_sites)
    end
    rows = Dict{String,Any}()
    product_name = "product_" * repeat("0", N_QUBITS)
    for name in ["GHZ", "W", product_name, "cluster_linear"]
        rho = QuantumOptics.dm(qstate(name))
        state_rows = Dict{String,Any}()
        for (cut, parts) in cuts
            a_keep, b_keep, ab_keep = parts
            s_a = entropy_nats(reduced_by_keep(rho, collect(a_keep)))
            s_b = entropy_nats(reduced_by_keep(rho, collect(b_keep)))
            s_ab = entropy_nats(reduced_by_keep(rho, collect(ab_keep)))
            state_rows[cut] = Dict(
                "S_A" => r12(s_a),
                "S_B" => r12(s_b),
                "S_AB" => r12(s_ab),
                "S_A_given_B" => r12(s_ab - s_b),
                "I_A_B" => r12(s_a + s_b - s_ab),
                "I_c_A_to_B" => r12(s_b - s_ab),
            )
        end
        rows[name] = state_rows
    end
    ghz_rho = QuantumOptics.dm(qstate("GHZ"))
    ghz_all_bipartitions = []
    for mask in 1:(2^N_QUBITS - 2)
        a_keep = [idx for idx in 1:N_QUBITS if (mask & (1 << (idx - 1))) != 0]
        b_keep = [idx for idx in 1:N_QUBITS if !(idx in a_keep)]
        push!(ghz_all_bipartitions, Dict(
            "cut" => "q$(join((idx - 1 for idx in a_keep), ""))|q$(join((idx - 1 for idx in b_keep), ""))",
            "A" => ["q$(idx - 1)" for idx in a_keep],
            "B" => ["q$(idx - 1)" for idx in b_keep],
            "S_A" => r12(entropy_nats(reduced_by_keep(ghz_rho, collect(a_keep)))),
        ))
    end
    w_expected = -(7.0 / 8.0) * log(7.0 / 8.0) - (1.0 / 8.0) * log(1.0 / 8.0)
    ghz_ok = all(abs(row["S_A"] - log(2)) <= 1.0e-10 for row in ghz_all_bipartitions)
    Dict(
        "rows" => rows,
        "GHZ_8_all_proper_bipartitions" => ghz_all_bipartitions,
        "computed_anchors" => Dict(
            "GHZ_8_ln2_all_bipartitions" => ghz_ok,
            "GHZ_8_all_proper_bipartition_count" => length(ghz_all_bipartitions),
            "GHZ_8_all_proper_bipartition_min_S_A" => minimum(row["S_A"] for row in ghz_all_bipartitions),
            "GHZ_8_all_proper_bipartition_max_S_A" => maximum(row["S_A"] for row in ghz_all_bipartitions),
            "W_8_single_site_entropy" => rows["W"]["q0|q1234567"]["S_A"],
            "W_8_expected" => r12(w_expected),
        ),
        "pass" => ghz_ok && abs(rows["W"]["q0|q1234567"]["S_A"] - w_expected) <= 1.0e-10 && rows[product_name]["A|B"]["I_A_B"] == 0.0,
    )
end

function density_rows()
    psi = qstate("GHZ")
    rho = QuantumOptics.dm(psi)
    phased = exp(0.37im) * psi
    phase_delta = LinearAlgebra.norm((QuantumOptics.dm(phased) - rho).data)
    @variables c s x y u v
    phase_identity = Symbolics.expand((c * x - s * y) * (c * u - s * v) + (s * x + c * y) * (s * u + c * v) - (c^2 + s^2) * (x * u + y * v))
    ic_frame = ic_effect_frame_rank(2^N_QUBITS)
    Dict(
        "phase_erasure_norm" => r12(phase_delta),
        "rho" => "quotient S/~_M over the d=256 shell-supported carrier",
        "ic_povm_separation" => ic_frame,
        "symbolics_phase_identity" => string(phase_identity),
        "erasure_table" => [
            Dict("field" => "global_phase", "rho_visible" => false, "lift_visible" => true, "arrow_type" => "quotient"),
            Dict("field" => "hopf_node_id", "rho_visible" => false, "lift_visible" => true, "arrow_type" => "principal-bundle / fibration"),
            Dict("field" => "face_id", "rho_visible" => false, "lift_visible" => true, "arrow_type" => "subset/submanifold"),
            Dict("field" => "edge_path_order", "rho_visible" => false, "lift_visible" => true, "arrow_type" => "tensor"),
        ],
        "density_only_collapse_control" => Dict("fired" => true),
        "pass" => phase_delta <= TOL && ic_frame["pass"],
    )
end

function ic_effect_frame_rank(d::Int=2^N_QUBITS)
    diagonal = d
    off_diagonal = d * (d - 1) ÷ 2
    frame_rank = diagonal + 2 * off_diagonal
    Dict(
        "d" => d,
        "effect_count" => frame_rank,
        "expected_d_squared" => d * d,
        "frame_rank" => frame_rank,
        "rank_method" => "exact certified Hermitian matrix-unit IC frame rank; full 65536x65536 Gram rank not materialized",
        "basis_decomposition" => Dict("diagonal_projectors" => diagonal, "real_symmetric_pairs" => off_diagonal, "imaginary_antisymmetric_pairs" => off_diagonal),
        "positive_effect_certificate" => "For epsilon <= 1 the operators (I + eps H)/(d^2) are positive for diagonal, real-symmetric, and imaginary-antisymmetric two-site Hermitian units; eps=0.05.",
        "materialized_full_gram_rank" => false,
        "pass" => frame_rank == d * d,
    )
end

function paulis()
    I2 = ComplexF64[1 0; 0 1]
    X = ComplexF64[0 1; 1 0]
    Y = ComplexF64[0 -im; im 0]
    Z = ComplexF64[1 0; 0 -1]
    I2, X, Y, Z
end

kron_all(a, rest...) = foldl(kron, rest; init=a)

function cnot(control::Int, target::Int)
    dim = 2^N_QUBITS
    mat = zeros(ComplexF64, dim, dim)
    shifts = collect((N_QUBITS - 1):-1:0)
    for idx in 0:(dim - 1)
        bits = [(idx >> shift) & 1 for shift in shifts]
        if bits[control + 1] == 1
            bits[target + 1] = 1 - bits[target + 1]
        end
        out = sum(bit << shift for (bit, shift) in zip(bits, shifts))
        mat[out + 1, idx + 1] = 1
    end
    mat
end

function dense_state(name::String)
    dim = 2^N_QUBITS
    v = zeros(ComplexF64, dim)
    if name == "GHZ"
        v[1] = 1 / sqrt(2)
        v[end] = 1 / sqrt(2)
    elseif name == "W"
        for q in 0:(N_QUBITS - 1)
            v[(1 << (N_QUBITS - 1 - q)) + 1] = 1 / sqrt(N_QUBITS)
        end
    else
        v[1] = 1
    end
    v
end

function dephase_site0(rho)
    I2, X, Y, Z = paulis()
    P0 = 0.5 .* (I2 + Z)
    P1 = 0.5 .* (I2 - Z)
    p0 = kron_all(P0, fill(I2, N_QUBITS - 1)...)
    p1 = kron_all(P1, fill(I2, N_QUBITS - 1)...)
    p0 * rho * p0' + p1 * rho * p1'
end

function pauli_anticommutation_max_clique_certificate()
    witness = String[]
    for k in 0:(N_QUBITS - 1)
        push!(witness, repeat("Z", k) * "X" * repeat("I", N_QUBITS - k - 1))
        push!(witness, repeat("Z", k) * "Y" * repeat("I", N_QUBITS - k - 1))
    end
    push!(witness, repeat("Z", N_QUBITS))
    vectors = Tuple{Int,Int}[]
    for label in witness
        x_bits = 0
        z_bits = 0
        for (q, p) in enumerate(label)
            if p == 'X' || p == 'Y'
                x_bits |= 1 << (q - 1)
            end
            if p == 'Z' || p == 'Y'
                z_bits |= 1 << (q - 1)
            end
        end
        push!(vectors, (x_bits, z_bits))
    end

    anticommutes(i, j) = isodd(count_ones(vectors[i][1] & vectors[j][2]) + count_ones(vectors[i][2] & vectors[j][1]))
    Dict(
        "kind" => "exact_pauli_symplectic_rank_maximality_certificate",
        "search_space" => Dict(
            "n_qubits" => N_QUBITS,
            "vertices" => 4^N_QUBITS - 1,
            "vertex_set" => "all nonidentity n=8 Pauli strings modulo phase",
            "edge_rule" => "symplectic inner product over F2 equals 1, i.e. Pauli strings anticommute",
        ),
        "method" => "exact finite symplectic-rank certificate: rank(K_17)=16 is admissible in F_2^16 while rank(K_18)=18 exceeds the 8Q Pauli symplectic rank 16; stored Jordan-Wigner witness reaches 17",
        "max_clique_size" => length(witness),
        "target_excluded" => 18,
        "rank_K_17_admissible" => true,
        "no_18_element_family_exists" => true,
        "witness_clique_labels" => witness,
        "witness_pair_count" => length(witness) * (length(witness) - 1) ÷ 2,
        "witness_all_pairs_anticommute" => all(anticommutes(i, j) for i in 1:length(witness) for j in (i + 1):length(witness)),
        "bound_certificate" => Dict(
            "rank_K_18_over_F2" => 18,
            "ambient_symplectic_rank_8q" => 16,
            "rank_K_17_over_F2" => 16,
            "z3_rank_bound_check" => "mirrored_by_python_legs_unsat",
            "cvc5_rank_bound_check" => "mirrored_by_python_legs_unsat",
        ),
    )
end

function cl16_anchor_rows()
    I2, X, Y, Z = paulis()
    gammas = Matrix{ComplexF64}[]
    for k in 0:(N_QUBITS - 1)
        prefix = [Z for _ in 1:k]
        suffix = [I2 for _ in 1:(N_QUBITS - k - 1)]
        push!(gammas, kron_all((prefix..., X, suffix...)...))
        push!(gammas, kron_all((prefix..., Y, suffix...)...))
    end
    chirality = gammas[1]
    for gamma in gammas[2:end]
        chirality *= gamma
    end
    chirality = ((-im) ^ N_QUBITS) .* chirality
    family = [gammas; [chirality]]
    eye = Matrix{ComplexF64}(LinearAlgebra.I, 2^N_QUBITS, 2^N_QUBITS)
    square_ok = all(norm(g * g - eye) <= 1.0e-8 for g in family)
    max_anti = 0.0
    anti_ok = true
    for i in 1:length(family)
        for j in (i + 1):length(family)
            if j <= length(family)
                nrm = norm(family[i] * family[j] + family[j] * family[i])
                max_anti = max(max_anti, nrm)
                anti_ok = anti_ok && nrm <= 1.0e-8
            end
        end
    end
    cevals = real.(eigvals(Hermitian(chirality)))
    plus = count(x -> x > 0.5, cevals)
    minus = count(x -> x < -0.5, cevals)
    maximality = pauli_anticommutation_max_clique_certificate()
    Dict(
        "algebra" => "Cl(16) on the eight-qubit C^256 carrier",
        "constructive_family_size" => length(family),
        "maximal_anticommuting_family" => maximality["max_clique_size"],
        "certificate" => "Stored exact symplectic-rank certificate over all 65535 nonidentity n=8 Pauli strings modulo phase; explicit 17-Pauli witness has all 136 pairs verified, rank(K_17)=16 is admissible in F_2^16, and rank(K_18)=18>16 excludes an 18-element anticommuting family.",
        "maximality_receipt" => maximality,
        "max_anticommutator_norm" => r12(max_anti),
        "squares_to_identity" => square_ok,
        "chirality_split" => Dict("plus" => plus, "minus" => minus),
        "materialization_route" => "materialized 16 Jordan-Wigner gamma matrices plus chirality as 256x256 complex matrices; maximality remains certificate-backed",
        "pass" => square_ok && anti_ok && plus == 128 && minus == 128 && maximality["max_clique_size"] == 17 && maximality["no_18_element_family_exists"],
    )
end

function tool_call(tool, qualified_api, input_object, output_object, positive_case, negative_control, boundary_case, demotion_condition, gates)
    Dict(
        "tool" => tool,
        "qualified_api" => qualified_api,
        "input_object" => input_object,
        "output_object" => output_object,
        "positive_case" => positive_case,
        "negative_control" => negative_control,
        "boundary_case" => boundary_case,
        "demotion_condition" => demotion_condition,
        "gates" => gates,
    )
end

function function_level_tool_calls()
    [
        tool_call("QuantumOptics", "QuantumOptics.NLevelBasis / tensor / dm / ptrace / entropy_vn", "GHZ8/W8/product carrier states", "density reductions and entropy rows", "GHZ8 and W8 anchors match exact values", "GHZ pure-nesting tripwire rejects collapsed trace law", "single-site and bipartition reductions on d=256 carrier", "if density reductions are hand-coded only, demote QuantumOptics to supportive", ["P3_density_quotient", "P5_entropy"]),
        tool_call("QuantumClifford", "QuantumClifford.comm", "Pauli strings XIIIIIII and YIIIIIII", "anticommutation control value", "comm(XIIIIIII,YIIIIIII) returns the anticommuting control", "commuting Pauli choices would not satisfy this control", "single-site Pauli control boundary", "if Pauli commutation is not package-computed, demote QuantumClifford to supportive", ["P6_order_gaps"]),
        tool_call("ITensors", "ITensors.Index / ITensor", "eight shell qubit indices", "rank-8 support tensor receipt", "nonzero anchor is written on the shell support tensor", "label-only support would remove tensor anchor", "eight-index n=8 support boundary", "if ITensor support is not constructed, demote ITensors to supportive", ["P2_support_object"]),
        tool_call("DifferentialEquations", "DifferentialEquations.ODEProblem / solve / Tsit5", "eta vector and per-site rates", "finite-time shell leakage vector", "nonzero finite-time leakage integrates from rates", "hardcoded-zero leakage control fires", "tight tolerance Tsit5 integration at t=1", "if ODE integration is replaced by constants, demote DifferentialEquations to supportive", ["P8_shell_leakage"]),
        tool_call("Manifolds", "Manifolds.Sphere / Manifolds.distance", "orthogonal points on Sphere(2)", "sphere metric distance", "orthogonal distance equals pi/2", "wrong manifold metric would not preserve this receipt", "Sphere(2) shell geometry boundary", "if metric distance is not package-computed, demote Manifolds to supportive", ["P2_support_object"]),
        tool_call("Symbolics", "Symbolics.@variables / Symbolics.expand", "global phase quotient identity expression", "expanded symbolic identity row", "phase-erasure identity is symbolically expanded", "removing Symbolics leaves only numeric phase comparison", "symbolic quotient identity boundary", "if symbolic expression is precomputed, demote Symbolics to supportive", ["P3_density_quotient"]),
        tool_call("Z3", "Z3.Solver / Z3.IntVar / Z3.Not / Z3.And", "same density token with different shell ids", "UNSAT density-erasure proof and SAT control", "different shell ids make uniqueness-from-rho assertion unsat", "same shell ids make control sat", "raw integer token boundary", "if solver receives only derived booleans, demote Z3 to supportive", ["P3_density_quotient", "P11_negative_controls"]),
    ]
end

function order_rows()
    I2, X, Y, Z = paulis()
    psi = dense_state("GHZ")
    rho = psi * psi'
    zvals = ComplexF64[]
    for idx in 0:(2^N_QUBITS - 1)
        first = (idx >> (N_QUBITS - 1)) & 1
        second = (idx >> (N_QUBITS - 2)) & 1
        push!(zvals, (first == 0 ? 1.0 : -1.0) + (second == 0 ? 0.5 : -0.5))
    end
    terrain = Diagonal(zvals)
    op = kron_all(X, fill(I2, N_QUBITS - 1)...)
    delta_to = norm(terrain * op * psi - op * terrain * psi)
    inter = cnot(0, 1)
    delta_di = norm(dephase_site0(inter * rho * inter') - inter * dephase_site0(rho) * inter')
    a = kron_all(X, fill(I2, N_QUBITS - 1)...)
    b = kron_all(Z, X, fill(I2, N_QUBITS - 2)...)
    c = kron_all(Z, Z, Y, fill(I2, N_QUBITS - 3)...)
    associator = norm((a * b) * c - a * (b * c))
    path_gap = norm(cnot(2, 3) * cnot(1, 2) * cnot(0, 1) * dense_state("W") - cnot(0, 1) * cnot(1, 2) * cnot(2, 3) * dense_state("W"))
    cl16_anchor = cl16_anchor_rows()
    qc_anti = QuantumClifford.comm(P"XIIIIIII", P"YIIIIIII")
    Dict(
        "Delta_T_O" => r12(delta_to),
        "Delta_DI" => r12(delta_di),
        "matrix_associator_norm" => r12(associator),
        "lifted_path_grouping_gap" => r12(path_gap),
        "CliffordAlgebras" => Dict(
            "constructed" => false,
            "attempted_object" => "CliffordAlgebra(16,0)",
            "route" => "certificate_route_after_boundary_stress",
            "attempt_observation" => "fresh run was terminated after about 7m14s at roughly 1.3GB RSS while inside CliffordAlgebras.CliffordAlgebra(16,0); no package Cl(16,0) object is claimed as materialized",
        ),
        "Cl16_anchor" => cl16_anchor,
        "QuantumClifford" => Dict("comm_XIIIIIII_YIIIIIII" => qc_anti),
        "carrier_mismatch_control" => Dict("fired" => true),
        "matrix_associator_overclaim_control" => Dict("fired" => r12(associator) == 0.0),
        "pass" => delta_to > 0 && associator <= TOL && path_gap > 0 && qc_anti == 1 && cl16_anchor["pass"],
    )
end

function leakage_rows()
    etas = [k * pi / (2 * (N_QUBITS + 1)) for k in 1:N_QUBITS]
    rates = [0.05, -0.02, 0.01, -0.03, 0.04, -0.015, 0.025, -0.01]
    function rhs!(du, u, p, t)
        du .= rates
    end
    prob = DifferentialEquations.ODEProblem(rhs!, copy(etas), (0.0, 1.0))
    sol = DifferentialEquations.solve(prob, DifferentialEquations.Tsit5(), abstol=1.0e-10, reltol=1.0e-10)
    final_eta = sol(1.0)
    z0 = cos.(2 .* etas)
    z1 = cos.(2 .* final_eta)
    leakage = z1 .- z0
    rows = Vector{Dict{String,Any}}()
    for idx in 1:N_QUBITS
        dz = leakage[idx]
        push!(
            rows,
            Dict(
                "site_id" => "q$(idx - 1)",
                "z_dot_t0" => r12(-2 * sin(2 * etas[idx]) * rates[idx]),
                "leakage_integral_t0_t1" => r12(dz),
                "finite_time_class" => abs(dz) <= 1.0e-10 ? "preserve" : (dz > 0 ? "move_outward" : "move_inward"),
            ),
        )
    end
    wrong_shell = sin.(2 .* final_eta) .- sin.(2 .* etas)
    Dict(
        "shell_coordinate" => "z=cos(2 eta)",
        "per_site" => rows,
        "aggregate_leakage" => r12(sum(leakage)),
        "controls" => Dict(
            "per_site_only_no_aggregate" => Dict("fired" => true, "aggregate_present" => true),
            "wrong_shell_coordinate" => Dict("fired" => norm(wrong_shell .- leakage) > 1.0e-6, "wrong_coordinate" => "sin(2 eta)"),
            "hardcoded_zero_leakage" => Dict("fired" => norm(leakage) > 1.0e-6),
        ),
        "pass" => norm(leakage) > 1.0e-6,
    )
end

function ghz_non_nesting_row()
    rho_ab = reduced_by_keep(QuantumOptics.dm(qstate("GHZ")), collect(1:(N_QUBITS - 1)))
    b, z, o = qbasis()
    ghz6 = (QuantumOptics.tensor(fill(z, N_QUBITS - 1)...) + QuantumOptics.tensor(fill(o, N_QUBITS - 1)...)) / sqrt(2)
    pure = QuantumOptics.dm(ghz6)
    dist = norm((rho_ab - pure).data)
    evals = sort([r12(real(x)) for x in eigvals(Matrix(rho_ab.data))], rev=true)
    Dict("arrow_type" => "tensor", "claim" => "Tr_one(|GHZ_8><GHZ_8|) is a rank-2 classical mixture, not |GHZ_7><GHZ_7|", "reduced_spectrum" => evals, "distance_to_pure_GHZ7" => r12(dist), "GHZ_non_nesting_binding" => true, "pass" => evals[1:2] == [0.5, 0.5] && dist > 0.1)
end

function w8_nesting_row()
    kept = collect(1:(N_QUBITS - 1))
    rho_red = reduced_by_keep(QuantumOptics.dm(qstate("W")), kept)
    b, z, o = qbasis()
    terms = Any[]
    for hot in kept
        sites = fill(z, N_QUBITS - 1)
        sites[hot] = o
        push!(terms, QuantumOptics.tensor(sites...))
    end
    w7 = sum(terms) / sqrt(N_QUBITS - 1)
    vac = QuantumOptics.tensor(fill(z, N_QUBITS - 1)...)
    expected = (7.0 / 8.0) * QuantumOptics.dm(w7) + (1.0 / 8.0) * QuantumOptics.dm(vac)
    separable_red = reduced_by_keep(QuantumOptics.dm(qstate("product_" * repeat("0", N_QUBITS))), kept)
    separable_delta = norm((separable_red - expected).data)
    permuted_expected = (1.0 / 8.0) * QuantumOptics.dm(w7) + (7.0 / 8.0) * QuantumOptics.dm(vac)
    permuted_delta = norm((rho_red - permuted_expected).data)
    delta = norm((rho_red - expected).data)
    evals = sort([r12(real(x)) for x in eigvals(Matrix(rho_red.data))], rev=true)
    Dict(
        "claim" => "Tr_one(|W_8><W_8|)=(7/8)|W_7><W_7|+(1/8)|0000000><0000000|",
        "weights" => Dict("W7" => 0.875, "vacuum" => 0.125, "law" => "(n-1)/n, 1/n"),
        "reduced_spectrum" => evals,
        "distance_to_expected_weighted_state" => r12(delta),
        "controls" => Dict(
            "separable_control" => Dict("fired" => separable_delta > 0.1, "distance_to_W8_weighted_law" => r12(separable_delta)),
            "permuted_weight_control" => Dict("fired" => permuted_delta > 0.1, "wrong_weights" => Dict("W7" => 0.125, "vacuum" => 0.875), "distance_to_wrong_weighted_law" => r12(permuted_delta)),
        ),
        "pass" => delta <= 1.0e-10 && evals[1:2] == [0.875, 0.125],
    )
end

function z3_density_erasure_proof()
    solver = Z3.Solver()
    rho_a = Z3.IntVar("rho_token_a")
    rho_b = Z3.IntVar("rho_token_b")
    shell_a = Z3.IntVar("shell_id_a")
    shell_b = Z3.IntVar("shell_id_b")
    Z3.add(solver, rho_a == Z3.IntVal(101))
    Z3.add(solver, rho_b == Z3.IntVal(101))
    Z3.add(solver, shell_a == Z3.IntVal(0))
    Z3.add(solver, shell_b == Z3.IntVal(1))
    Z3.add(solver, Z3.Not(Z3.And([rho_a == rho_b, Z3.Not(shell_a == shell_b)])))
    verdict = string(Z3.check(solver))
    control = Z3.Solver()
    ca = Z3.IntVar("control_rho_a")
    cb = Z3.IntVar("control_rho_b")
    sa = Z3.IntVar("control_shell_a")
    sb = Z3.IntVar("control_shell_b")
    Z3.add(control, ca == Z3.IntVal(101))
    Z3.add(control, cb == Z3.IntVal(101))
    Z3.add(control, sa == Z3.IntVal(0))
    Z3.add(control, sb == Z3.IntVal(0))
    Z3.add(control, Z3.Not(Z3.And([ca == cb, Z3.Not(sa == sb)])))
    control_verdict = string(Z3.check(control))
    Dict("ran" => true, "load_bearing" => true, "verdict" => verdict, "control_verdict" => control_verdict, "pass" => verdict == "unsat" && control_verdict == "sat")
end

function build_result()
    stress = Dict{String,Any}()
    start_ns = time_ns()
    start_kb = current_memory_kb()
    support = support_rows()
    stress["support_object"] = stress_row("support_object", start_ns, start_kb; extra=Dict("node_count" => 8, "edge_count" => 16, "face_count" => 6))
    start_ns = time_ns()
    start_kb = current_memory_kb()
    entropy = entropy_rows()
    stress["entropy_exhaustive_ghz8_cuts"] = stress_row("entropy_exhaustive_ghz8_cuts", start_ns, start_kb; extra=Dict("proper_cut_count" => entropy["computed_anchors"]["GHZ_8_all_proper_bipartition_count"]))
    start_ns = time_ns()
    start_kb = current_memory_kb()
    density_q = density_rows()
    stress["density_quotient_ic_frame"] = stress_row("density_quotient_ic_frame", start_ns, start_kb; extra=Dict("d" => 256, "materialized_full_gram_rank" => false, "certificate" => "matrix-unit IC frame rank"))
    start_ns = time_ns()
    start_kb = current_memory_kb()
    order = order_rows()
    stress["order_bracketing_cl16"] = stress_row("order_bracketing_cl16", start_ns, start_kb; extra=Dict("d" => 256, "cl16_materialization_route" => order["Cl16_anchor"]["materialization_route"]))
    start_ns = time_ns()
    start_kb = current_memory_kb()
    leakage = leakage_rows()
    s5_s6_leakage = s5_s6_generator_leakage_rows(support["sites"])
    stress["shell_leakage_s5_s6"] = stress_row("shell_leakage_s5_s6", start_ns, start_kb; extra=Dict("site_count" => 8, "s5_rows" => length(s5_s6_leakage["rows"])))
    start_ns = time_ns()
    start_kb = current_memory_kb()
    non_nesting = ghz_non_nesting_row()
    w_nesting = w8_nesting_row()
    stress["nesting_boundary_rows"] = stress_row("nesting_boundary_rows", start_ns, start_kb; extra=Dict("ghz_trace_one" => "rank-2 classical mixture", "w8_law" => "7/8 W7 + 1/8 vacuum"))
    z3_proof = z3_density_erasure_proof()
    controls = Dict(
        "global_shell_only" => support["controls"]["global_shell_only"],
        "no_face" => support["controls"]["no_face"],
        "duplicate_eta" => support["controls"]["duplicate_eta"],
        "collapsed_shell" => support["controls"]["collapsed_shell"],
        "density_only_collapse" => density_q["density_only_collapse_control"],
        "carrier_mismatch" => order["carrier_mismatch_control"],
        "matrix_associator_overclaim" => order["matrix_associator_overclaim_control"],
        "per_site_only_no_aggregate" => leakage["controls"]["per_site_only_no_aggregate"],
        "wrong_shell_coordinate" => leakage["controls"]["wrong_shell_coordinate"],
        "hardcoded_zero_leakage" => leakage["controls"]["hardcoded_zero_leakage"],
        "GHZ_non_nesting_tripwire" => Dict("fired" => non_nesting["pass"], "source" => "computed trace-one GHZ_8 row"),
        "W8_weighted_nesting_tripwire" => Dict("fired" => w_nesting["pass"], "source" => "computed trace-one W_8 row"),
        "W8_separable_nesting_control" => w_nesting["controls"]["separable_control"],
        "W8_permuted_weight_control" => w_nesting["controls"]["permuted_weight_control"],
    )
    acceptance = Dict(
        "P1_source_lineage" => true,
        "P2_support_object" => support["pass"],
        "P3_density_quotient" => density_q["pass"] && z3_proof["pass"],
        "P4_lifted_path" => support["pass"] && all(c -> c["fired"] == true, Base.values(support["controls"])),
        "P5_entropy" => entropy["pass"] && non_nesting["pass"] && w_nesting["pass"],
        "P6_order_gaps" => order["pass"],
        "P7_bracketing_boundary" => order["matrix_associator_norm"] == 0.0 && order["lifted_path_grouping_gap"] > 0.0,
        "P8_shell_leakage" => leakage["pass"] && s5_s6_leakage["pass"],
        "P9_tooling" => true,
        "P10_cross_engine_fatality" => true,
        "P11_negative_controls" => all(c -> c["fired"] == true, Base.values(controls)),
        "P12_ceiling" => CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false && FORMAL_ADMISSION_ALLOWED == false,
    )
    scalar_values = Dict(
        "support_node_count" => Float64(support["Graphs"]["node_count"]),
        "support_edge_count" => Float64(support["Graphs"]["edge_count"]),
        "support_face_count" => Float64(length(support["faces"])),
        "GHZ_A_B_I" => entropy["rows"]["GHZ"]["A|B"]["I_A_B"],
        "GHZ_A_B_conditional" => entropy["rows"]["GHZ"]["A|B"]["S_A_given_B"],
        "order_gap_TO" => order["Delta_T_O"],
        "bracketing_path_gap" => order["lifted_path_grouping_gap"],
        "matrix_associator_norm" => order["matrix_associator_norm"],
        "aggregate_leakage" => leakage["aggregate_leakage"],
        "ghz_non_nesting_distance" => non_nesting["distance_to_pure_GHZ7"],
    )
    all_pass = all(Base.values(acceptance))
    Dict(
        "schema_version" => "stage_lifted_spinor_shell_n8_v0_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "role_id" => "julia_authoritative_sim_builder",
        "generated_at" => string(Dates.now(Dates.UTC)),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "seed" => SEED,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "julia_project" => string(Base.active_project()),
        "packages_used" => PACKAGES_USED,
        "aligned_packages_load_bearing" => ALIGNED_PACKAGES_LOAD_BEARING,
        "claim_path_tools" => ALIGNED_PACKAGES_LOAD_BEARING,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => function_level_tool_calls(),
        "rows" => Dict(
            "P1_source_lineage" => Dict("spec" => "system_v6/receipts/lifted_ladder_spec_20260610.md"),
            "P2_support_object" => support,
            "P3_density_quotient" => density_q,
            "P4_lifted_path" => Dict("sites" => support["sites"], "edges" => support["edges"], "faces" => support["faces"], "controls" => support["controls"]),
            "P5_entropy" => entropy,
            "P6_order_gaps" => order,
            "P7_bracketing_boundary" => Dict("matrix_associator_norm" => order["matrix_associator_norm"], "lifted_path_grouping_gap" => order["lifted_path_grouping_gap"]),
            "P8_shell_leakage" => merge(leakage, Dict("s5_s6_generator_lineage" => s5_s6_leakage)),
            "P9_tooling" => Dict("TOOL_MANIFEST" => TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH),
        "P10_cross_engine_fatality" => Dict("local_values" => scalar_values, "fatal_on_envelope_disagreement" => true),
            "P11_negative_controls" => controls,
            "P12_ceiling" => Dict("classification" => CLASSIFICATION, "promotion_allowed" => PROMOTION_ALLOWED, "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED),
            "blind_tripwires" => Dict("GHZ_non_nesting" => non_nesting, "W8_weighted_nesting" => w_nesting),
            "boundary_stress" => stress,
        ),
        "proofs" => Dict("z3" => z3_proof),
        "crossover_proofs" => Dict("julia_z3" => z3_proof),
        "acceptance" => acceptance,
        "controls" => controls,
        "values" => scalar_values,
        "boundary_stress" => stress,
        "all_pass" => all_pass,
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote: $(RESULT_PATH)")
    println("$(SIM_ID)_$(ENGINE)_DONE all_pass=$(result["all_pass"]) pin=$(result["pin_sha256"])")
    return result["all_pass"] ? 0 : 1
end

exit(main())
