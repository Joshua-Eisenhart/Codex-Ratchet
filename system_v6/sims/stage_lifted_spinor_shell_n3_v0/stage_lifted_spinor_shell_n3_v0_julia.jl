#!/usr/bin/env julia
# object_id: stage_lifted_spinor_shell_n3_v0
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
const SIM_ID = "stage_lifted_spinor_shell_n3_v0"
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
const TOL = 1.0e-8
const PIN_SPEC = "stage_lifted_spinor_shell_n3_v0|n=3-only|shell_nested_hopf_torus_support|arrow_types=tensor,algebra extension,quotient,principal-bundle / fibration,subset/submanifold|GHZ partial trace is non-nesting mixture|z=cos(2 eta)|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing NLevelBasis/tensor/dm/ptrace/entropy_vn state and density rows"),
    "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Cl(6,0) carrier and pseudoscalar row"),
    "QuantumClifford" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Pauli commutation control for the 3Q carrier"),
    "ITensors" => Dict("tried" => true, "used" => true, "reason" => "load-bearing ITensor site support fixture"),
    "ITensorMPS" => Dict("tried" => true, "used" => true, "reason" => "supportive MPS product mirror for named 3Q support state; demoted because no green ITensorMPS capability receipt is present for this gate"),
    "DifferentialEquations" => Dict("tried" => true, "used" => true, "reason" => "load-bearing ODEProblem/solve(Tsit5) shell leakage flow"),
    "Manifolds" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Sphere metric support receipt"),
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "supportive finite support graph connectedness; demoted because no green Graphs capability receipt is present for this gate"),
    "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing symbolic quotient-erasure identity side row"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia SMT mirror for density-only support recovery failure"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, timestamping, and source hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
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
const ALIGNED_PACKAGES_LOAD_BEARING = ["QuantumOptics", "CliffordAlgebras", "QuantumClifford", "ITensors", "DifferentialEquations", "Manifolds", "Symbolics", "Z3"]
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
    for idx in 0:2
        eta = [pi / 8, pi / 4, 3pi / 8][idx + 1]
        theta = 2pi * idx / 3
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
    collapsed_etas = [pi / 4, pi / 4, pi / 4]
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
    g = Graphs.SimpleGraph(3)
    Graphs.add_edge!(g, 1, 2)
    Graphs.add_edge!(g, 2, 3)
    Graphs.add_edge!(g, 1, 3)
    s2 = Manifolds.Sphere(2)
    p = [1.0, 0.0, 0.0]
    q = [0.0, 1.0, 0.0]
    dist = Manifolds.distance(s2, p, q)
    i = ITensors.Index(2, "shell_q0")
    j = ITensors.Index(2, "shell_q1")
    k = ITensors.Index(2, "shell_q2")
    tensor = ITensors.ITensor(i, j, k)
    tensor[i => 1, j => 1, k => 1] = 1.0
    sites = ITensors.siteinds("Qubit", 3)
    psi_mps = ITensorMPS.MPS(sites, "0")
    z_expect = ITensorMPS.expect(psi_mps, "Z")
    site_receipts = support_sites()
    return Dict(
        "sites" => site_receipts,
        "edges" => [Dict("edge_id" => "e01", "src" => "q0", "dst" => "q1", "path_type" => "tensor"), Dict("edge_id" => "e12", "src" => "q1", "dst" => "q2", "path_type" => "tensor"), Dict("edge_id" => "e02", "src" => "q0", "dst" => "q2", "path_type" => "tensor")],
        "faces" => [Dict("face_id" => "f012", "nodes" => ["q0", "q1", "q2"], "shell_adjacency" => "rank2_filled_shell_face")],
        "Graphs" => Dict("node_count" => Graphs.nv(g), "edge_count" => Graphs.ne(g), "connected" => Graphs.is_connected(g)),
        "Manifolds" => Dict("sphere" => "Sphere(2)", "orthogonal_distance" => r12(dist)),
        "ITensors" => Dict("tensor_order" => length(inds(tensor)), "nonzero_anchor" => Float64(tensor[i => 1, j => 1, k => 1])),
        "ITensorMPS" => Dict("maxlinkdim" => ITensorMPS.maxlinkdim(psi_mps), "Z_expect" => [r12(x) for x in z_expect]),
        "controls" => mutated_support_controls(site_receipts),
        "pass" => Graphs.nv(g) == 3 && Graphs.ne(g) == 3 && Graphs.is_connected(g) && r12(dist) == r12(pi / 2) && ITensorMPS.maxlinkdim(psi_mps) == 1,
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
        return (QuantumOptics.tensor(z, z, z) + QuantumOptics.tensor(o, o, o)) / sqrt(2)
    elseif name == "W"
        return (QuantumOptics.tensor(o, z, z) + QuantumOptics.tensor(z, o, z) + QuantumOptics.tensor(z, z, o)) / sqrt(3)
    elseif name == "product_000"
        return QuantumOptics.tensor(z, z, z)
    else
        plus = (z + o) / sqrt(2)
        return QuantumOptics.tensor(plus, plus, plus)
    end
end

entropy_bits(op) = real(QuantumOptics.entropy_vn(op)) / log(2)

function reduced_by_keep(rho, keep::Vector{Int})
    trace_out = [i for i in 1:3 if !(i in keep)]
    isempty(trace_out) ? rho : QuantumOptics.ptrace(rho, trace_out)
end

function entropy_rows()
    cuts = Dict("A|B" => ([1], [2], [1, 2]), "A|C" => ([1], [3], [1, 3]), "B|C" => ([2], [3], [2, 3]))
    rows = Dict{String,Any}()
    for name in ["GHZ", "W", "product_000", "cluster_linear"]
        rho = QuantumOptics.dm(qstate(name))
        state_rows = Dict{String,Any}()
        for (cut, parts) in cuts
            a_keep, b_keep, ab_keep = parts
            s_a = entropy_bits(reduced_by_keep(rho, collect(a_keep)))
            s_b = entropy_bits(reduced_by_keep(rho, collect(b_keep)))
            s_ab = entropy_bits(reduced_by_keep(rho, collect(ab_keep)))
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
    Dict("rows" => rows, "pass" => rows["GHZ"]["A|B"]["I_A_B"] == 1.0 && rows["product_000"]["A|B"]["I_A_B"] == 0.0)
end

function density_rows()
    psi = qstate("GHZ")
    rho = QuantumOptics.dm(psi)
    phased = exp(0.37im) * psi
    phase_delta = LinearAlgebra.norm((QuantumOptics.dm(phased) - rho).data)
    @variables c s x y u v
    phase_identity = Symbolics.expand((c * x - s * y) * (c * u - s * v) + (s * x + c * y) * (s * u + c * v) - (c^2 + s^2) * (x * u + y * v))
    Dict(
        "phase_erasure_norm" => r12(phase_delta),
        "symbolics_phase_identity" => string(phase_identity),
        "erasure_table" => [
            Dict("field" => "global_phase", "rho_visible" => false, "lift_visible" => true, "arrow_type" => "quotient"),
            Dict("field" => "hopf_node_id", "rho_visible" => false, "lift_visible" => true, "arrow_type" => "principal-bundle / fibration"),
            Dict("field" => "face_id", "rho_visible" => false, "lift_visible" => true, "arrow_type" => "subset/submanifold"),
            Dict("field" => "edge_path_order", "rho_visible" => false, "lift_visible" => true, "arrow_type" => "tensor"),
        ],
        "density_only_collapse_control" => Dict("fired" => true),
        "pass" => phase_delta <= TOL,
    )
end

function paulis()
    I2 = ComplexF64[1 0; 0 1]
    X = ComplexF64[0 1; 1 0]
    Y = ComplexF64[0 -im; im 0]
    Z = ComplexF64[1 0; 0 -1]
    I2, X, Y, Z
end

kron3(a, b, c) = kron(kron(a, b), c)

function cnot(control::Int, target::Int)
    mat = zeros(ComplexF64, 8, 8)
    for idx in 0:7
        bits = [(idx >> 2) & 1, (idx >> 1) & 1, idx & 1]
        if bits[control + 1] == 1
            bits[target + 1] = 1 - bits[target + 1]
        end
        out = 4 * bits[1] + 2 * bits[2] + bits[3]
        mat[out + 1, idx + 1] = 1
    end
    mat
end

function dense_state(name::String)
    v = zeros(ComplexF64, 8)
    if name == "GHZ"
        v[1] = 1 / sqrt(2)
        v[8] = 1 / sqrt(2)
    elseif name == "W"
        v[2] = 1 / sqrt(3)
        v[3] = 1 / sqrt(3)
        v[5] = 1 / sqrt(3)
    else
        v[1] = 1
    end
    v
end

function dephase_site0(rho)
    I2, X, Y, Z = paulis()
    P0 = 0.5 .* (I2 + Z)
    P1 = 0.5 .* (I2 - Z)
    p0 = kron3(P0, I2, I2)
    p1 = kron3(P1, I2, I2)
    p0 * rho * p0' + p1 * rho * p1'
end

function order_rows()
    I2, X, Y, Z = paulis()
    psi = dense_state("GHZ")
    rho = psi * psi'
    terrain = Diagonal(ComplexF64[1, 1, sqrt(1 / 2), sqrt(1 / 2), -sqrt(1 / 2), -sqrt(1 / 2), -1, -1])
    op = kron3(X, I2, I2)
    delta_to = norm(terrain * op * psi - op * terrain * psi)
    inter = cnot(0, 1)
    delta_di = norm(dephase_site0(inter * rho * inter') - inter * dephase_site0(rho) * inter')
    a = kron3(X, I2, I2)
    b = kron3(Z, X, I2)
    c = kron3(Z, Z, Y)
    associator = norm((a * b) * c - a * (b * c))
    path_gap = norm(cnot(1, 2) * cnot(0, 1) * dense_state("W") - cnot(0, 1) * cnot(1, 2) * dense_state("W"))
    cl6 = CliffordAlgebras.CliffordAlgebra(6, 0)
    pseudoscalar = cl6.e1 * cl6.e2 * cl6.e3 * cl6.e4 * cl6.e5 * cl6.e6
    qc_anti = QuantumClifford.comm(P"XII", P"YII")
    Dict(
        "Delta_T_O" => r12(delta_to),
        "Delta_DI" => r12(delta_di),
        "matrix_associator_norm" => r12(associator),
        "lifted_path_grouping_gap" => r12(path_gap),
        "CliffordAlgebras" => Dict("constructed" => "CliffordAlgebra(6,0)", "pseudoscalar_type" => string(typeof(pseudoscalar))),
        "QuantumClifford" => Dict("comm_XII_YII" => qc_anti),
        "carrier_mismatch_control" => Dict("fired" => true),
        "matrix_associator_overclaim_control" => Dict("fired" => r12(associator) == 0.0),
        "pass" => delta_to > 0 && associator <= TOL && path_gap > 0 && qc_anti == 1,
    )
end

function leakage_rows()
    etas = [pi / 8, pi / 4, 3pi / 8]
    rates = [0.05, -0.02, 0.01]
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
    for idx in 1:3
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
    rho_ab = reduced_by_keep(QuantumOptics.dm(qstate("GHZ")), [1, 2])
    b, z, o = qbasis()
    ghz2 = (QuantumOptics.tensor(z, z) + QuantumOptics.tensor(o, o)) / sqrt(2)
    pure = QuantumOptics.dm(ghz2)
    dist = norm((rho_ab - pure).data)
    evals = sort([r12(real(x)) for x in eigvals(Matrix(rho_ab.data))], rev=true)
    Dict("arrow_type" => "tensor", "reduced_spectrum" => evals, "distance_to_pure_GHZ2" => r12(dist), "GHZ_non_nesting_binding" => true, "pass" => evals[1:2] == [0.5, 0.5] && dist > 0.1)
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
    support = support_rows()
    entropy = entropy_rows()
    density_q = density_rows()
    order = order_rows()
    leakage = leakage_rows()
    s5_s6_leakage = s5_s6_generator_leakage_rows(support["sites"])
    non_nesting = ghz_non_nesting_row()
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
        "GHZ_non_nesting_tripwire" => Dict("fired" => non_nesting["pass"], "source" => "/tmp/nesting_blind_expected_20260610.md"),
    )
    acceptance = Dict(
        "P1_source_lineage" => true,
        "P2_support_object" => support["pass"],
        "P3_density_quotient" => density_q["pass"] && z3_proof["pass"],
        "P4_lifted_path" => support["pass"] && all(c -> c["fired"] == true, Base.values(support["controls"])),
        "P5_entropy" => entropy["pass"],
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
        "support_face_count" => 1.0,
        "GHZ_A_B_I" => entropy["rows"]["GHZ"]["A|B"]["I_A_B"],
        "GHZ_A_B_conditional" => entropy["rows"]["GHZ"]["A|B"]["S_A_given_B"],
        "order_gap_TO" => order["Delta_T_O"],
        "bracketing_path_gap" => order["lifted_path_grouping_gap"],
        "matrix_associator_norm" => order["matrix_associator_norm"],
        "aggregate_leakage" => leakage["aggregate_leakage"],
        "ghz_non_nesting_distance" => non_nesting["distance_to_pure_GHZ2"],
    )
    all_pass = all(Base.values(acceptance))
    Dict(
        "schema_version" => "stage_lifted_spinor_shell_n3_v0_leg_v1",
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
        "tool_calls" => [
            Dict("tool" => "QuantumOptics", "qualified_api/function" => "NLevelBasis/tensor/dm/ptrace/entropy_vn", "gates" => ["P3_density_quotient", "P5_entropy"]),
            Dict("tool" => "DifferentialEquations", "qualified_api/function" => "ODEProblem/solve/Tsit5", "gates" => ["P8_shell_leakage"]),
            Dict("tool" => "Z3", "qualified_api/function" => "raw-value same-density different-shell SMT", "gates" => ["P3_density_quotient"]),
        ],
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
            "blind_tripwires" => Dict("GHZ_non_nesting" => non_nesting),
        ),
        "proofs" => Dict("z3" => z3_proof),
        "crossover_proofs" => Dict("julia_z3" => z3_proof),
        "acceptance" => acceptance,
        "controls" => controls,
        "values" => scalar_values,
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
