#!/usr/bin/env julia
# Julia leg for the source-locked terrain generator sheet packet.

using LinearAlgebra
using Dates
using SHA
using JSON
using Z3
using QuantumOptics

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "terrain_generator_sheet_packet"
const OBJECT_ID = "$(SIM_ID)_julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-8
const SMT_SCALE = 10^9
const T_CHANNEL = 0.4
const EPS = 0.2
const SE_LAMBDA = 0.2
const GAMMA_NI = 0.5
const KAPPA_SI = 0.4
const OMEGA_SI = EPS
const ETA0 = pi / 8.0
const PHI0 = 0.3
const CHI0 = 0.2

const SOURCE_LINE_REFS = Dict(
    "terrain_math_sigma" => "system_v5/READ ONLY Reference Docs/terrain math.md:23-24",
    "terrain_math_loops" => "system_v5/READ ONLY Reference Docs/terrain math.md:30-33",
    "terrain_math_generators" => "system_v5/READ ONLY Reference Docs/terrain math.md:76-83",
    "terrain_math_projectors" => "system_v5/READ ONLY Reference Docs/terrain math.md:89-90",
    "terrain_math_placements" => "system_v5/READ ONLY Reference Docs/terrain math.md:122-150",
    "rosetta_lk_projectors" => "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:53-58",
    "rosetta_stage_channel" => "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:63-71",
    "rosetta_placements" => "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:151-183",
    "scaffold_terrain_section" => "system_v6/foundations/working_math_scaffold_20260609.md:77-101",
    "operator_state_matrix" => "system_v5/READ ONLY Reference Docs/operator math explicit.md:8-30",
)

const SOURCE_LOCK_LINE_RANGES = Dict(
    "terrain_math_generators_78_83" => ("system_v5/READ ONLY Reference Docs/terrain math.md", 78, 83),
    "terrain_math_placements_122_137" => ("system_v5/READ ONLY Reference Docs/terrain math.md", 122, 137),
    "rosetta_si_projectors_57_58" => ("system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md", 57, 58),
    "rosetta_stage_channel_71" => ("system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md", 71, 71),
    "rosetta_placements_151_183" => ("system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md", 151, 183),
)

const SOURCE_LOCK_EXPECTED_SHA256 = Dict(
    "terrain_math_generators_78_83" => "1c2041062a386ac505aa1d18f2fdc85a304a1f99515e5ad67c56b7a6aed9a1c8",
    "terrain_math_placements_122_137" => "0a890e6a0363eae5e96ac85793655d2222456ddba4d0380bdb36fbb0c8df3c53",
    "rosetta_si_projectors_57_58" => "fdb1447de960e2dabc406777b939018b7a15bfa135083be62a7145c248d75a83",
    "rosetta_stage_channel_71" => "85d126c9ffeea7ea2babe2a3764252a177530e974c20a81715b6514839799545",
    "rosetta_placements_151_183" => "251b15eb6f7623c5ccb9ddbd4757e111649801322a768c884379d3bf3c61365c",
)

const PIN_SPEC = Dict(
    "H_0" => "(sigma_x + sigma_y + sigma_z) / sqrt(3)",
    "H_L" => "+H_0",
    "H_R" => "-H_0",
    "eps_all" => EPS,
    "se_lambda" => Dict(
        "value" => SE_LAMBDA,
        "status" => "PINNED-CHOICE",
        "reason" => "source gives a Se dissipator family but no numeric lambda in the requested line refs",
    ),
    "gamma_Ni" => GAMMA_NI,
    "kappa_Si" => KAPPA_SI,
    "omega_Si" => Dict(
        "value" => OMEGA_SI,
        "status" => "PINNED-CHOICE",
        "reason" => "source leaves omega/K frame magnitude free; set equal to eps for this bounded packet",
    ),
    "Si_frames" => Dict("m_L" => "z-axis", "m_R" => "x-axis", "status" => "PINNED-CHOICE not source-forced"),
    "Phi" => "expm(0.4 * X)",
    "rho_0_rho_1" => Dict(
        "status" => "PINNED-FALLBACK",
        "reason" => "source_locked_operator_base_packet is not present in this checkout; states instantiate the operator packet density constraints",
    ),
)

const PAULI_EXPANSION_FAMILY_PIN_METADATA = Dict(
    "Se_Funnel_L" => Dict(
        "status" => "PINNED-CHOICE not source-forced",
        "reason" => "source fixes the Se dissipator family shape but not this finite Pauli coefficient set",
        "source_refs" => [
            "system_v5/READ ONLY Reference Docs/terrain math.md:76",
            "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:53",
        ],
    ),
    "Se_Cannon_R" => Dict(
        "status" => "PINNED-CHOICE not source-forced",
        "reason" => "source fixes the Se dissipator family shape but not this finite Pauli coefficient set",
        "source_refs" => [
            "system_v5/READ ONLY Reference Docs/terrain math.md:77",
            "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:54",
        ],
    ),
    "Ne_Vortex_L" => Dict(
        "status" => "PINNED-CHOICE not source-forced",
        "reason" => "pure Ne is source-forced; weak-dissipator Ne uses this exploratory coefficient set as a pinned variant",
        "source_refs" => [
            "system_v5/READ ONLY Reference Docs/terrain math.md:78",
            "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:55",
        ],
    ),
    "Ne_Spiral_R" => Dict(
        "status" => "PINNED-CHOICE not source-forced",
        "reason" => "pure Ne is source-forced; weak-dissipator Ne uses this exploratory coefficient set as a pinned variant",
        "source_refs" => [
            "system_v5/READ ONLY Reference Docs/terrain math.md:79",
            "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:56",
        ],
    ),
)

const AXIS0_DELTA_VECTOR_RAW = [0.90, -0.33, 0.30]
const AXIS0_DELTA_VECTOR = AXIS0_DELTA_VECTOR_RAW ./ norm(AXIS0_DELTA_VECTOR_RAW)
const AXIS0_DELTA_SCALE = 0.01
const AXIS0_TIMES = [0.0, 0.1, 0.2, T_CHANNEL]
const AXIS0_DOCTRINE_PATTERN = Dict("Ne" => "+", "Ni" => "+", "Se" => "-", "Si" => "-")
const PINNED_BIPARTITE_LAMBDA = 0.37
const PINNED_BIPARTITE_PHASE = 0.41

const TOOL_MANIFEST = Dict(
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive matrix exponential, eigenspectrum, SVD trace norm, and projector arithmetic; stdlib substrate demoted under capability-probe doctrine"),
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing carrier-project entropy cross-check for rho_0/rho_1 certificates"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Z3.jl in-solver equality check over bound Pit/Source generator entries"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, timestamping, and source hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "LinearAlgebra" => "supportive",
    "QuantumOptics" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)

const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -1im; 1im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SIGMA_MINUS = ComplexF64[0 0; 1 0]
const SIGMA_PLUS = ComplexF64[0 1; 0 0]
const H0 = (SX + SY + SZ) / sqrt(3.0)
const PZ_PLUS = 0.5 .* (I2 + SZ)
const PZ_MINUS = 0.5 .* (I2 - SZ)
const PX_PLUS = 0.5 .* (I2 + SX)
const PX_MINUS = 0.5 .* (I2 - SX)
const TERRAIN_KET0 = PZ_MINUS
const TERRAIN_KET1 = PZ_PLUS

const RHO_0 = ComplexF64[0.65 0.21 - 0.13im; 0.21 + 0.13im 0.35]
const RHO_1 = ComplexF64[0.42 -0.18 + 0.16im; -0.18 - 0.16im 0.58]
const SENSITIVE_RHO = ComplexF64[0.50 0.23 - 0.17im; 0.23 + 0.17im 0.50]

const SQRT_SE = sqrt(SE_LAMBDA)
const SE_FUNNEL_COEFFS = [
    Dict("I" => 0.0 + 0im, "sx" => SQRT_SE + 0im, "sy" => 0.0 + 0im, "sz" => 0.0 + 0im),
    Dict("I" => 0.0 + 0im, "sx" => 0.0 + 0im, "sy" => SQRT_SE + 0im, "sz" => 0.0 + 0im),
]
const SE_CANNON_COEFFS = [
    Dict("I" => 0.0 + 0im, "sx" => -SQRT_SE + 0im, "sy" => 0.0 + 0im, "sz" => 0.0 + 0im),
    Dict("I" => 0.0 + 0im, "sx" => 0.0 + 0im, "sy" => 1im * SQRT_SE, "sz" => 0.0 + 0im),
]
const NE_VORTEX_COEFFS = [
    Dict("I" => 0.0 + 0im, "sx" => 1.0 + 0im, "sy" => 0.0 + 0im, "sz" => 0.0 + 0im),
    Dict("I" => 0.0 + 0im, "sx" => 0.0 + 0im, "sy" => 0.0 + 0im, "sz" => 1.0 + 0im),
]
const NE_SPIRAL_COEFFS = [
    Dict("I" => 0.0 + 0im, "sx" => -1.0 + 0im, "sy" => 0.0 + 0im, "sz" => 0.0 + 0im),
    Dict("I" => 0.0 + 0im, "sx" => 0.0 + 0im, "sy" => 0.0 + 0im, "sz" => 1.0im),
]

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function sha256_line_range(relative_path::String, start_line::Int, end_line::Int)::String
    lines = readlines(joinpath(ROOT, relative_path), keep=true)
    payload = join(lines[start_line:end_line])
    bytes2hex(sha256(collect(codeunits(payload))))
end

function source_lock_freshness()
    rows = Dict{String,Any}()
    for (name, (relative_path, start_line, end_line)) in SOURCE_LOCK_LINE_RANGES
        current = sha256_line_range(relative_path, start_line, end_line)
        expected = SOURCE_LOCK_EXPECTED_SHA256[name]
        rows[name] = Dict(
            "path" => relative_path,
            "start_line" => start_line,
            "end_line" => end_line,
            "expected_sha256" => expected,
            "current_sha256" => current,
            "fresh" => current == expected,
            "stale_red" => current != expected,
        )
    end
    Dict(
        "lock_kind" => "exact_source_line_range_sha256",
        "rows" => rows,
        "all_fresh" => all(row["fresh"] for row in values(rows)),
        "stale_red" => any(row["stale_red"] for row in values(rows)),
    )
end

function matrix_json(mat::AbstractMatrix)
    return Dict("real" => real.(mat), "imag" => imag.(mat))
end

function jsonable(x)
    if x isa Dict
        return Dict(string(k) => jsonable(v) for (k, v) in x)
    elseif x isa Vector
        return [jsonable(v) for v in x]
    elseif x isa Tuple
        return [jsonable(v) for v in x]
    elseif x isa AbstractMatrix
        return matrix_json(x)
    elseif x isa Bool || x isa String || x === nothing
        return x
    elseif x isa Complex
        return Dict("real" => Float64(real(x)), "imag" => Float64(imag(x)))
    elseif x isa Real
        return Float64(x)
    else
        return string(x)
    end
end

hermitize(rho::Matrix{ComplexF64}) = 0.5 .* (rho + rho')

function density_valid(rho::Matrix{ComplexF64})
    eigs = eigvals(Hermitian(hermitize(rho)))
    trace_residual = abs(real(tr(rho)) - 1.0)
    min_eig = minimum(real.(eigs))
    Dict(
        "trace_residual" => trace_residual,
        "hermitian_residual" => maximum(abs.(rho .- rho')),
        "min_eigenvalue" => min_eig,
        "pass" => trace_residual <= TOL && min_eig >= -TOL,
    )
end

function entropy_vn(rho::Matrix{ComplexF64})::Float64
    vals = clamp.(real.(eigvals(Hermitian(hermitize(rho)))), 0.0, 1.0)
    total = 0.0
    for p in vals
        if p > 1.0e-14
            total -= p * log(p)
        end
    end
    total
end

purity(rho::Matrix{ComplexF64})::Float64 = real(tr(rho * rho))
trace_norm(mat::Matrix{ComplexF64})::Float64 = sum(svdvals(mat))
trace_distance(a::Matrix{ComplexF64}, b::Matrix{ComplexF64})::Float64 = 0.5 * trace_norm(a - b)
fro_norm(mat::Matrix{ComplexF64})::Float64 = norm(mat)

function bloch(rho::Matrix{ComplexF64})::Vector{Float64}
    [real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
end

function dissipator(op::Matrix{ComplexF64}, rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    od = op'
    odo = od * op
    op * rho * od - 0.5 .* (odo * rho + rho * odo)
end

function dephase_projectors(projectors::Vector{Matrix{ComplexF64}}, rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    out = zeros(ComplexF64, 2, 2)
    for p in projectors
        out .+= p * rho * p
    end
    out - rho
end

comm(h::Matrix{ComplexF64}, rho::Matrix{ComplexF64}) = h * rho - rho * h

function pauli_from_coeffs(coeffs::Dict)::Matrix{ComplexF64}
    coeffs["I"] .* I2 + coeffs["sx"] .* SX + coeffs["sy"] .* SY + coeffs["sz"] .* SZ
end

function dissipator_family(coeff_rows::Vector, rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    out = zeros(ComplexF64, 2, 2)
    for coeffs in coeff_rows
        out .+= dissipator(pauli_from_coeffs(coeffs), rho)
    end
    out
end

function generator_fn(
    terrain::String;
    ne_variant::String = "pure_hamiltonian",
    erased_weyl::Bool = false,
    commuting_si_frame::Bool = false,
    sigma_swap_source_side::Bool = false,
    sigma_only_swap::Bool = false,
)
    h_l = H0
    h_r = erased_weyl ? H0 : -H0
    if terrain == "Funnel"
        return rho -> dissipator_family(SE_FUNNEL_COEFFS, rho) - 1im * EPS .* comm(h_l, rho)
    elseif terrain == "Cannon"
        return rho -> dissipator_family(SE_CANNON_COEFFS, rho) - 1im * EPS .* comm(h_r, rho)
    elseif terrain == "Vortex"
        return rho -> begin
            base = -1im .* comm(h_l, rho)
            ne_variant == "weak_dissipator" ? base + EPS .* dissipator_family(NE_VORTEX_COEFFS, rho) : base
        end
    elseif terrain == "Spiral"
        return rho -> begin
            base = -1im .* comm(h_r, rho)
            ne_variant == "weak_dissipator" ? base + EPS .* dissipator_family(NE_SPIRAL_COEFFS, rho) : base
        end
    elseif terrain == "Pit"
        if sigma_swap_source_side
            jump = SIGMA_PLUS
            h = h_r
        elseif sigma_only_swap
            jump = SIGMA_PLUS
            h = h_l
        else
            jump = SIGMA_MINUS
            h = h_l
        end
        return rho -> GAMMA_NI .* dissipator(jump, rho) - 1im * EPS .* comm(h, rho)
    elseif terrain == "Source"
        return rho -> GAMMA_NI .* dissipator(SIGMA_PLUS, rho) - 1im * EPS .* comm(h_r, rho)
    elseif terrain == "Hill"
        return rho -> -1im .* comm(OMEGA_SI .* SZ, rho) + KAPPA_SI .* dephase_projectors([PZ_PLUS, PZ_MINUS], rho)
    elseif terrain == "Citadel"
        if commuting_si_frame
            return rho -> -1im .* comm(OMEGA_SI .* SZ, rho) + KAPPA_SI .* dephase_projectors([PZ_PLUS, PZ_MINUS], rho)
        end
        return rho -> -1im .* comm(OMEGA_SI .* SX, rho) + KAPPA_SI .* dephase_projectors([PX_PLUS, PX_MINUS], rho)
    end
    error("unknown terrain $terrain")
end

function basis_matrix(i::Int, j::Int)::Matrix{ComplexF64}
    mat = zeros(ComplexF64, 2, 2)
    mat[i, j] = 1.0 + 0im
    mat
end

function superoperator(gen)::Matrix{ComplexF64}
    cols = Vector{Vector{ComplexF64}}()
    for j in 1:2, i in 1:2
        push!(cols, vec(gen(basis_matrix(i, j))))
    end
    hcat(cols...)
end

channel_from_generator(gen) = exp(T_CHANNEL .* superoperator(gen))
channel_from_generator_at(gen, time_value::Float64) = exp(time_value .* superoperator(gen))

apply_channel_linear(channel::Matrix{ComplexF64}, mat::Matrix{ComplexF64})::Matrix{ComplexF64} = reshape(channel * vec(mat), 2, 2)

function apply_channel(channel::Matrix{ComplexF64}, rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    out = reshape(channel * vec(rho), 2, 2)
    out = hermitize(out)
    out ./ tr(out)
end

function unitality_column(channels::Dict{String,Matrix{ComplexF64}})
    rows = Dict{String,Any}()
    for (name, channel) in channels
        e_identity = apply_channel_linear(channel, I2)
        residual = fro_norm(e_identity - I2)
        rows[name] = Dict(
            "E_I" => e_identity,
            "E_I_minus_I_fro_norm" => residual,
            "unital_within_tolerance" => residual <= 1.0e-7,
            "expected_non_unital" => name in ["Pit", "Source"],
        )
    end
    ni_values = [rows[name]["E_I_minus_I_fro_norm"] for name in ["Pit", "Source"]]
    non_ni_values = [row["E_I_minus_I_fro_norm"] for (name, row) in rows if !(name in ["Pit", "Source"])]
    Dict(
        "definition" => "unital iff E(I)=I for the finite channel exp(tX)",
        "rows" => rows,
        "ni_pair_non_unital" => all(value -> value > 1.0e-4, ni_values),
        "non_ni_unital" => all(value -> value <= 1.0e-7, non_ni_values),
        "max_non_ni_E_I_minus_I_fro_norm" => maximum(non_ni_values),
        "min_ni_E_I_minus_I_fro_norm" => minimum(ni_values),
        "pass" => all(value -> value > 1.0e-4, ni_values) && all(value -> value <= 1.0e-7, non_ni_values),
    )
end

function pauli_coefficients(delta::Matrix{ComplexF64})::Vector{Float64}
    [real(tr(delta * SX)), real(tr(delta * SY)), real(tr(delta * SZ))]
end

function pauli_diversity_metrics(delta::Matrix{ComplexF64})
    coeffs = pauli_coefficients(delta)
    weights = coeffs .* coeffs
    weight_sum = sum(weights)
    if weight_sum <= 1.0e-14
        participation = 0.0
        entropy = 0.0
    else
        probs = weights ./ weight_sum
        participation = (sum(weights) * sum(weights)) / sum(weights .* weights)
        entropy = -sum(p > 1.0e-14 ? p * log(p) : 0.0 for p in probs)
    end
    Dict(
        "pauli_coefficients" => Dict("sx" => coeffs[1], "sy" => coeffs[2], "sz" => coeffs[3]),
        "pauli_weight_sum" => weight_sum,
        "pauli_participation_ratio" => participation,
        "observable_spread_entropy" => entropy,
        "trace_norm" => trace_norm(delta),
    )
end

function sign_label(value::Float64; tol::Float64 = 1.0e-8)::String
    value > tol && return "+"
    value < -tol && return "-"
    "0"
end

function axis0_generator_specs()
    [
        (name = "Vortex:pure_hamiltonian", terrain = "Vortex", kwargs = (ne_variant = "pure_hamiltonian",), family = "Ne", group = "Ne:pure_hamiltonian"),
        (name = "Spiral:pure_hamiltonian", terrain = "Spiral", kwargs = (ne_variant = "pure_hamiltonian",), family = "Ne", group = "Ne:pure_hamiltonian"),
        (name = "Vortex:weak_dissipator", terrain = "Vortex", kwargs = (ne_variant = "weak_dissipator",), family = "Ne", group = "Ne:weak_dissipator"),
        (name = "Spiral:weak_dissipator", terrain = "Spiral", kwargs = (ne_variant = "weak_dissipator",), family = "Ne", group = "Ne:weak_dissipator"),
        (name = "Pit", terrain = "Pit", kwargs = NamedTuple(), family = "Ni", group = "Ni"),
        (name = "Source", terrain = "Source", kwargs = NamedTuple(), family = "Ni", group = "Ni"),
        (name = "Funnel", terrain = "Funnel", kwargs = NamedTuple(), family = "Se", group = "Se"),
        (name = "Cannon", terrain = "Cannon", kwargs = NamedTuple(), family = "Se", group = "Se"),
        (name = "Hill", terrain = "Hill", kwargs = NamedTuple(), family = "Si", group = "Si"),
        (name = "Citadel", terrain = "Citadel", kwargs = NamedTuple(), family = "Si", group = "Si"),
    ]
end

function axis0_delta_rho()::Matrix{ComplexF64}
    AXIS0_DELTA_SCALE .* (AXIS0_DELTA_VECTOR[1] .* SX + AXIS0_DELTA_VECTOR[2] .* SY + AXIS0_DELTA_VECTOR[3] .* SZ)
end

function axis0_response()
    delta0 = axis0_delta_rho()
    initial = pauli_diversity_metrics(delta0)
    functionals = ["pauli_participation_ratio", "trace_norm", "observable_spread_entropy"]
    rows = Dict{String,Any}()
    for spec in axis0_generator_specs()
        gen = generator_fn(spec.terrain; spec.kwargs...)
        series = Vector{Dict{String,Any}}()
        for time_value in AXIS0_TIMES
            channel = channel_from_generator_at(gen, time_value)
            metrics = pauli_diversity_metrics(apply_channel_linear(channel, delta0))
            push!(series, merge(Dict("time" => time_value), metrics))
        end
        final = series[end]
        responses = Dict(functional => final[functional] - initial[functional] for functional in functionals)
        rows[spec.name] = Dict(
            "family" => spec.family,
            "group" => spec.group,
            "series" => series,
            "responses" => responses,
            "signs" => Dict(functional => sign_label(responses[functional]) for functional in functionals),
        )
    end

    aggregate_groups = Dict(
        "Ne:pure_hamiltonian" => ["Vortex:pure_hamiltonian", "Spiral:pure_hamiltonian"],
        "Ne:weak_dissipator" => ["Vortex:weak_dissipator", "Spiral:weak_dissipator"],
        "Ne" => ["Vortex:pure_hamiltonian", "Spiral:pure_hamiltonian", "Vortex:weak_dissipator", "Spiral:weak_dissipator"],
        "Ni" => ["Pit", "Source"],
        "Se" => ["Funnel", "Cannon"],
        "Si" => ["Hill", "Citadel"],
    )
    group_rows = Dict{String,Any}()
    for (group, names) in aggregate_groups
        responses = Dict(
            functional => sum(rows[name]["responses"][functional] for name in names) / length(names)
            for functional in functionals
        )
        group_rows[group] = Dict(
            "members" => names,
            "responses" => responses,
            "signs" => Dict(functional => sign_label(responses[functional]) for functional in functionals),
        )
    end
    sign_table = Dict(
        functional => Dict(group => group_rows[group]["signs"][functional] for group in ["Ne:pure_hamiltonian", "Ne:weak_dissipator", "Ni", "Se", "Si"])
        for functional in functionals
    )
    doctrine_sign_table = Dict(
        functional => Dict(family => group_rows[family]["signs"][functional] for family in ["Ne", "Ni", "Se", "Si"])
        for functional in functionals
    )
    doctrine_pattern_match = Dict(
        functional => doctrine_sign_table[functional] == AXIS0_DOCTRINE_PATTERN
        for functional in functionals
    )
    Dict(
        "spec_ref" => "system_v6/foundations/working_math_scaffold_20260609.md:270-276",
        "delta_rho" => Dict(
            "definition" => "0.01 * normalized(0.90*sigma_x - 0.33*sigma_y + 0.30*sigma_z)",
            "pin_status" => "PINNED-CHOICE not source-forced",
            "pauli_vector_normalized" => AXIS0_DELTA_VECTOR,
            "matrix" => delta0,
        ),
        "primary_functional" => "pauli_participation_ratio",
        "functional_definitions" => Dict(
            "pauli_participation_ratio" => "(sum_i c_i^2)^2 / sum_i c_i^4 for c_i=Tr(delta_rho(t) sigma_i)",
            "trace_norm" => "||delta_rho(t)||_1",
            "observable_spread_entropy" => "Shannon entropy of normalized c_i^2 over {sigma_x,sigma_y,sigma_z}",
        ),
        "initial_metrics" => initial,
        "rows" => rows,
        "groups" => group_rows,
        "sign_table" => sign_table,
        "doctrine_family_sign_table" => doctrine_sign_table,
        "doctrine_prediction" => AXIS0_DOCTRINE_PATTERN,
        "doctrine_pattern_match" => doctrine_pattern_match,
        "pass" => all(!isempty(row["series"]) for row in values(rows)),
    )
end

function choi_matrix(channel::Matrix{ComplexF64})::Matrix{ComplexF64}
    choi = zeros(ComplexF64, 4, 4)
    for i in 1:2, j in 1:2
        block = reshape(channel * vec(basis_matrix(i, j)), 2, 2)
        choi[(2i - 1):(2i), (2j - 1):(2j)] .= block
    end
    hermitize(choi)
end

function channel_certificate(channel::Matrix{ComplexF64})
    choi = choi_matrix(channel)
    eigs = eigvals(Hermitian(choi))
    tp_residual = 0.0
    for i in 1:2, j in 1:2
        expected = i == j ? 1.0 : 0.0
        got = real(tr(reshape(channel * vec(basis_matrix(i, j)), 2, 2)))
        tp_residual = max(tp_residual, abs(got - expected))
    end
    min_choi = minimum(real.(eigs))
    Dict(
        "choi_min_eigenvalue" => min_choi,
        "choi_trace" => real(tr(choi)),
        "tp_residual" => tp_residual,
        "choi_psd" => min_choi >= -1.0e-7,
        "tp" => tp_residual <= 1.0e-7,
        "pass" => min_choi >= -1.0e-7 && tp_residual <= 1.0e-7,
    )
end

function pinned_bipartite_state()::Matrix{ComplexF64}
    amp0 = sqrt(PINNED_BIPARTITE_LAMBDA)
    amp1 = sqrt(1.0 - PINNED_BIPARTITE_LAMBDA)
    phase = cis(PINNED_BIPARTITE_PHASE)
    psi = ComplexF64[amp0, 0.0, 0.0, phase * amp1]
    psi * psi'
end

function partial_trace_ancilla(rho_ab::Matrix{ComplexF64})::Matrix{ComplexF64}
    rho_b = zeros(ComplexF64, 2, 2)
    for b in 1:2, bp in 1:2
        value = 0.0 + 0.0im
        for a in 1:2
            value += rho_ab[2 * (a - 1) + b, 2 * (a - 1) + bp]
        end
        rho_b[b, bp] = value
    end
    rho_b
end

function apply_channel_to_system(channel::Matrix{ComplexF64}, rho_ab::Matrix{ComplexF64})::Matrix{ComplexF64}
    out = zeros(ComplexF64, 4, 4)
    for b in 1:2, bp in 1:2
        block = zeros(ComplexF64, 2, 2)
        for a in 1:2, ap in 1:2
            block[a, ap] = rho_ab[2 * (a - 1) + b, 2 * (ap - 1) + bp]
        end
        block_out = apply_channel_linear(channel, block)
        for a in 1:2, ap in 1:2
            out[2 * (a - 1) + b, 2 * (ap - 1) + bp] = block_out[a, ap]
        end
    end
    out = hermitize(out)
    out ./ tr(out)
end

conditional_entropy_a_given_b(rho_ab::Matrix{ComplexF64})::Float64 = entropy_vn(rho_ab) - entropy_vn(partial_trace_ancilla(rho_ab))

function generator_hamiltonian(name::String)::Matrix{ComplexF64}
    if name in ["Funnel", "Vortex:pure_hamiltonian", "Vortex:weak_dissipator", "Pit"]
        return H0
    elseif name in ["Cannon", "Spiral:pure_hamiltonian", "Spiral:weak_dissipator", "Source"]
        return -H0
    elseif name == "Hill"
        return OMEGA_SI .* SZ
    elseif name == "Citadel"
        return OMEGA_SI .* SX
    end
    error("unknown generator $name")
end

dissipative_component_present(name::String)::Bool = !(name in ["Vortex:pure_hamiltonian", "Spiral:pure_hamiltonian"])

function entropy_columns(channels::Dict{String,Matrix{ComplexF64}})
    rho_ab = pinned_bipartite_state()
    conditional_before = conditional_entropy_a_given_b(rho_ab)
    rows = Dict{String,Any}()
    for (name, channel) in channels
        hamiltonian = generator_hamiltonian(name)
        state_rows = Dict{String,Any}()
        for (state_name, rho) in Dict("rho_0" => RHO_0, "rho_1" => RHO_1)
            out = apply_channel(channel, rho)
            energy_before = real(tr(hamiltonian * rho))
            energy_after = real(tr(hamiltonian * out))
            state_rows[state_name] = Dict(
                "Delta_S_system_von_neumann" => entropy_vn(out) - entropy_vn(rho),
                "system_entropy_before" => entropy_vn(rho),
                "system_entropy_after" => entropy_vn(out),
                "bath_exchange_energy_delta_TrHrho" => energy_after - energy_before,
                "energy_before_TrHrho" => energy_before,
                "energy_after_TrHrho" => energy_after,
            )
        end
        out_ab = apply_channel_to_system(channel, rho_ab)
        conditional_after = conditional_entropy_a_given_b(out_ab)
        rows[name] = Dict(
            "dissipative_component_present" => dissipative_component_present(name),
            "hamiltonian_for_energy_bookkeeping" => hamiltonian,
            "system_entropy" => state_rows,
            "pinned_bipartite_extension" => Dict(
                "state" => "sqrt(lambda)|00> + exp(i phase)*sqrt(1-lambda)|11>",
                "lambda" => PINNED_BIPARTITE_LAMBDA,
                "phase" => PINNED_BIPARTITE_PHASE,
                "S_A_given_B_before" => conditional_before,
                "S_A_given_B_after" => conditional_after,
                "Delta_S_A_given_B" => conditional_after - conditional_before,
            ),
        )
    end
    Dict(
        "definition" => "Delta-S_system is von Neumann entropy after-before; bath exchange is Delta Tr[H rho]; Delta-S(A|B) applies E tensor I to a pinned partially entangled system-ancilla state.",
        "rows" => rows,
    )
end

function state_deltas(channel::Matrix{ComplexF64})
    rows = Dict{String,Any}()
    for (name, rho) in Dict("rho_0" => RHO_0, "rho_1" => RHO_1)
        out = apply_channel(channel, rho)
        rows[name] = Dict(
            "entropy_before" => entropy_vn(rho),
            "entropy_after" => entropy_vn(out),
            "entropy_delta" => entropy_vn(out) - entropy_vn(rho),
            "purity_before" => purity(rho),
            "purity_after" => purity(out),
            "purity_delta" => purity(out) - purity(rho),
            "trace_distance_from_input" => trace_distance(out, rho),
        )
    end
    rows
end

function projector_coherence(rho::Matrix{ComplexF64}, projectors::Vector{Matrix{ComplexF64}})::Float64
    total = 0.0
    for i in 1:2, j in 1:2
        i == j && continue
        total += fro_norm(projectors[i] * rho * projectors[j])
    end
    total
end

function spinor(phi::Float64, chi::Float64, eta::Float64)::Vector{ComplexF64}
    ComplexF64[cis(phi + chi) * cos(eta), cis(phi - chi) * sin(eta)]
end

function loop_spinor(loop::String, u::Float64; sheet::String)::Vector{ComplexF64}
    phi = PHI0
    chi = sheet == "L" ? CHI0 : -CHI0
    if loop == "inner"
        phi += u
    elseif loop == "outer"
        phi -= cos(2.0 * ETA0) * u
        chi += u
    else
        error("unknown loop $loop")
    end
    psi = spinor(phi, chi, ETA0)
    psi ./ norm(psi)
end

density(psi::Vector{ComplexF64}) = psi * psi'

const PLACEMENTS = [
    (1, "Se / Funnel / inner", "L", "Funnel", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:122"),
    (2, "Se / Funnel / outer", "L", "Funnel", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:123"),
    (3, "Ne / Vortex / inner", "L", "Vortex", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:124"),
    (4, "Ne / Vortex / outer", "L", "Vortex", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:125"),
    (5, "Ni / Pit / inner", "L", "Pit", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:126"),
    (6, "Ni / Pit / outer", "L", "Pit", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:127"),
    (7, "Si / Hill / inner", "L", "Hill", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:128"),
    (8, "Si / Hill / outer", "L", "Hill", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:129"),
    (9, "Se / Cannon / inner", "R", "Cannon", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:130"),
    (10, "Se / Cannon / outer", "R", "Cannon", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:131"),
    (11, "Ne / Spiral / inner", "R", "Spiral", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:132"),
    (12, "Ne / Spiral / outer", "R", "Spiral", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:133"),
    (13, "Ni / Source / inner", "R", "Source", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:134"),
    (14, "Ni / Source / outer", "R", "Source", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:135"),
    (15, "Si / Citadel / inner", "R", "Citadel", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:136"),
    (16, "Si / Citadel / outer", "R", "Citadel", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:137"),
]

function placement_table(channels::Dict{String,Matrix{ComplexF64}})
    rows = Vector{Dict{String,Any}}()
    sample_us = [0.0, pi / 2.0, pi, 3.0 * pi / 2.0, 2.0 * pi]
    for (idx, label, sheet, terrain, loop, line_ref) in PLACEMENTS
        rho_start = density(loop_spinor(loop, 0.0; sheet=sheet))
        loop_deltas = [trace_distance(density(loop_spinor(loop, u; sheet=sheet)), rho_start) for u in sample_us]
        key = terrain in ["Vortex", "Spiral"] ? "$(terrain):pure_hamiltonian" : terrain
        rho_end = apply_channel(channels[key], rho_start)
        row = Dict(
            "index" => idx,
            "label" => label,
            "sheet" => sheet,
            "terrain" => terrain,
            "loop" => loop,
            "source_line_ref" => line_ref,
            "placement" => "(X_$(terrain),$(loop == "inner" ? "gamma_in" : "gamma_out"))",
            "density_delta" => trace_distance(rho_end, rho_start),
            "loop_coordinate_density_delta_max" => maximum(loop_deltas),
            "loop_class" => loop == "inner" ? "fiber_density_stationary" : "base_density_visible",
        )
        if terrain in ["Vortex", "Spiral"]
            weak = channels["$(terrain):weak_dissipator"]
            row["density_delta_weak_dissipator"] = trace_distance(apply_channel(weak, rho_start), rho_start)
        end
        push!(rows, row)
    end
    rows
end

function scaled_superop_entries(matrix::Matrix{ComplexF64})
    [(Int(round(real(v) * SMT_SCALE)), Int(round(imag(v) * SMT_SCALE))) for v in vec(matrix)]
end

function z3_bind_entries!(solver, prefix::String, values)
    reals = Z3.Expr[]
    imags = Z3.Expr[]
    for (idx, (real_value, imag_value)) in enumerate(values)
        rv = Z3.IntVar("$(prefix)_re_$(idx)")
        iv = Z3.IntVar("$(prefix)_im_$(idx)")
        Z3.add(solver, rv == Z3.IntVal(real_value))
        Z3.add(solver, iv == Z3.IntVal(imag_value))
        push!(reals, rv)
        push!(imags, iv)
    end
    reals, imags
end

function z3_smt_suite(pit::Matrix{ComplexF64}, source::Matrix{ComplexF64}, swapped::Matrix{ComplexF64})
    pit_values = scaled_superop_entries(pit)
    source_values = scaled_superop_entries(source)
    swapped_values = scaled_superop_entries(swapped)
    forced = Z3.Solver()
    pit_re, pit_im = z3_bind_entries!(forced, "pit_jl", pit_values)
    source_re, source_im = z3_bind_entries!(forced, "source_jl", source_values)
    for (a, b) in zip(vcat(pit_re, pit_im), vcat(source_re, source_im))
        Z3.add(forced, a == b)
    end
    forced_status = string(Z3.check(forced))

    eq = Z3.Solver()
    sw_re, sw_im = z3_bind_entries!(eq, "swapped_jl", swapped_values)
    src_re, src_im = z3_bind_entries!(eq, "source_eq_jl", source_values)
    for (a, b) in zip(vcat(sw_re, sw_im), vcat(src_re, src_im))
        Z3.add(eq, a == b)
    end
    eq_status = string(Z3.check(eq))

    neq = Z3.Solver()
    sw2_re, sw2_im = z3_bind_entries!(neq, "swapped_neq_jl", swapped_values)
    src2_re, src2_im = z3_bind_entries!(neq, "source_neq_jl", source_values)
    terms = Z3.Expr[]
    for (a, b) in zip(vcat(sw2_re, sw2_im), vcat(src2_re, src2_im))
        push!(terms, Z3.Not(a == b))
    end
    Z3.add(neq, Z3.Or(terms))
    neq_status = string(Z3.check(neq))
    Dict(
        "solver" => "Z3.jl",
        "verdict" => forced_status,
        "claim" => "Pit and Source full generator entries are not equal under entry-binding SMT; forced equality is UNSAT.",
        "proof_kind" => "entry_binding_smt",
        "symbolic_derivation_in_solver" => false,
        "entry_binding_honesty_label" => "ENTRY-BINDING SMT: generator formulas are constructed outside the solver; the solver binds scaled generator entries and checks equality/inequality.",
        "sigma_swapped_pit_source_convention_equality" => eq_status,
        "sigma_swapped_pit_source_convention_inequality" => neq_status,
        "binds_generator_entries" => length(pit_values),
        "scale" => SMT_SCALE,
        "asserted_precomputed_boolean" => false,
        "pass" => forced_status == "unsat" && eq_status == "sat" && neq_status == "unsat",
    )
end

function quantumoptics_entropy_crosscheck()
    q = QuantumOptics.SpinBasis(1 // 2)
    op0 = QuantumOptics.DenseOperator(q, q, RHO_0)
    op1 = QuantumOptics.DenseOperator(q, q, RHO_1)
    e0 = Float64(real(QuantumOptics.entropy_vn(op0)))
    e1 = Float64(real(QuantumOptics.entropy_vn(op1)))
    Dict(
        "api" => "QuantumOptics.DenseOperator + QuantumOptics.entropy_vn",
        "rho_0_entropy" => e0,
        "rho_1_entropy" => e1,
        "rho_0_local_entropy" => entropy_vn(RHO_0),
        "rho_1_local_entropy" => entropy_vn(RHO_1),
        "pass" => abs(e0 - entropy_vn(RHO_0)) <= 1.0e-10 && abs(e1 - entropy_vn(RHO_1)) <= 1.0e-10,
    )
end

function build_result()
    mkpath(RESULT_DIR)
    channels = Dict(
        "Funnel" => channel_from_generator(generator_fn("Funnel")),
        "Cannon" => channel_from_generator(generator_fn("Cannon")),
        "Vortex:pure_hamiltonian" => channel_from_generator(generator_fn("Vortex"; ne_variant="pure_hamiltonian")),
        "Vortex:weak_dissipator" => channel_from_generator(generator_fn("Vortex"; ne_variant="weak_dissipator")),
        "Spiral:pure_hamiltonian" => channel_from_generator(generator_fn("Spiral"; ne_variant="pure_hamiltonian")),
        "Spiral:weak_dissipator" => channel_from_generator(generator_fn("Spiral"; ne_variant="weak_dissipator")),
        "Pit" => channel_from_generator(generator_fn("Pit")),
        "Source" => channel_from_generator(generator_fn("Source")),
        "Hill" => channel_from_generator(generator_fn("Hill")),
        "Citadel" => channel_from_generator(generator_fn("Citadel")),
    )
    erased_channels = Dict(
        "Cannon" => channel_from_generator(generator_fn("Cannon"; erased_weyl=true)),
        "Spiral:pure_hamiltonian" => channel_from_generator(generator_fn("Spiral"; ne_variant="pure_hamiltonian", erased_weyl=true)),
        "Spiral:weak_dissipator" => channel_from_generator(generator_fn("Spiral"; ne_variant="weak_dissipator", erased_weyl=true)),
        "Citadel:commuting_frame" => channel_from_generator(generator_fn("Citadel"; commuting_si_frame=true)),
        "Pit:sigma_only_swap" => channel_from_generator(generator_fn("Pit"; sigma_only_swap=true)),
        "Pit:sigma_swap_source_side" => channel_from_generator(generator_fn("Pit"; sigma_swap_source_side=true)),
    )

    certs = Dict(name => Dict("cptp" => channel_certificate(ch), "state_deltas" => state_deltas(ch)) for (name, ch) in channels)
    unitality = unitality_column(channels)
    for (name, row) in unitality["rows"]
        certs[name]["unitality"] = row
    end
    source_lock = source_lock_freshness()
    axis0 = axis0_response()
    entropy = entropy_columns(channels)
    pit_gen = generator_fn("Pit")
    source_gen = generator_fn("Source")
    pit_swapped_source_gen = generator_fn("Pit"; sigma_swap_source_side=true)
    z3_proof = z3_smt_suite(superoperator(pit_gen), superoperator(source_gen), superoperator(pit_swapped_source_gen))
    qo_check = quantumoptics_entropy_crosscheck()

    pit_drift_z = real(tr(pit_gen(SENSITIVE_RHO) * SZ))
    source_drift_z = real(tr(source_gen(SENSITIVE_RHO) * SZ))
    pit_sigma_only_drift_z = real(tr(generator_fn("Pit"; sigma_only_swap=true)(SENSITIVE_RHO) * SZ))
    hill_sensitive_before = projector_coherence(SENSITIVE_RHO, [PZ_PLUS, PZ_MINUS])
    hill_sensitive_after = projector_coherence(apply_channel(channels["Hill"], SENSITIVE_RHO), [PZ_PLUS, PZ_MINUS])
    citadel_sensitive_before = projector_coherence(SENSITIVE_RHO, [PX_PLUS, PX_MINUS])
    citadel_sensitive_after = projector_coherence(apply_channel(channels["Citadel"], SENSITIVE_RHO), [PX_PLUS, PX_MINUS])

    fixed_point_checks = Dict(
        "basis_label_policy" => Dict(
            "terrain_label_zero_projector_matrix" => TERRAIN_KET0,
            "terrain_label_one_projector_matrix" => TERRAIN_KET1,
            "note" => "Labels follow the locked sigma convention: D[sigma_-] fixes the second matrix-basis projector.",
        ),
        "Pit" => Dict(
            "source_jump" => "sigma_-",
            "dissipator_target" => "terrain |0><0|",
            "dissipator_target_residual" => fro_norm(GAMMA_NI .* dissipator(SIGMA_MINUS, TERRAIN_KET0)),
            "full_generator_target_residual" => fro_norm(pit_gen(TERRAIN_KET0)),
            "full_generator_hamiltonian_tilt_recorded" => fro_norm(pit_gen(TERRAIN_KET0)) > TOL,
            "sensitive_state_rz_drift" => pit_drift_z,
            "attractor_side_pass" => pit_drift_z < -1.0e-4,
        ),
        "Source" => Dict(
            "source_jump" => "sigma_+",
            "dissipator_target" => "terrain |1><1|",
            "dissipator_target_residual" => fro_norm(GAMMA_NI .* dissipator(SIGMA_PLUS, TERRAIN_KET1)),
            "full_generator_target_residual" => fro_norm(source_gen(TERRAIN_KET1)),
            "full_generator_hamiltonian_tilt_recorded" => fro_norm(source_gen(TERRAIN_KET1)) > TOL,
            "sensitive_state_rz_drift" => source_drift_z,
            "attractor_side_pass" => source_drift_z > 1.0e-4,
        ),
        "Hill" => Dict(
            "frame" => "z-axis",
            "commutator_K_P_plus_norm" => fro_norm((OMEGA_SI .* SZ) * PZ_PLUS - PZ_PLUS * (OMEGA_SI .* SZ)),
            "commutator_K_P_minus_norm" => fro_norm((OMEGA_SI .* SZ) * PZ_MINUS - PZ_MINUS * (OMEGA_SI .* SZ)),
            "pure_projector_control_delta" => trace_distance(apply_channel(channels["Hill"], PZ_PLUS), PZ_PLUS),
            "sensitive_coherence_before" => hill_sensitive_before,
            "sensitive_coherence_after" => hill_sensitive_after,
            "sensitive_state_control_pass" => hill_sensitive_after < hill_sensitive_before - 1.0e-4,
        ),
        "Citadel" => Dict(
            "frame" => "x-axis",
            "commutator_K_P_plus_norm" => fro_norm((OMEGA_SI .* SX) * PX_PLUS - PX_PLUS * (OMEGA_SI .* SX)),
            "commutator_K_P_minus_norm" => fro_norm((OMEGA_SI .* SX) * PX_MINUS - PX_MINUS * (OMEGA_SI .* SX)),
            "pure_projector_control_delta" => trace_distance(apply_channel(channels["Citadel"], PX_PLUS), PX_PLUS),
            "sensitive_coherence_before" => citadel_sensitive_before,
            "sensitive_coherence_after" => citadel_sensitive_after,
            "sensitive_state_control_pass" => citadel_sensitive_after < citadel_sensitive_before - 1.0e-4,
        ),
    )

    n0 = [1.0, 1.0, 1.0] ./ sqrt(3.0)
    rv0 = bloch(RHO_0)
    vort_pure = apply_channel(channels["Vortex:pure_hamiltonian"], RHO_0)
    spir_pure = apply_channel(channels["Spiral:pure_hamiltonian"], RHO_0)
    vort_weak = apply_channel(channels["Vortex:weak_dissipator"], RHO_0)
    spir_weak = apply_channel(channels["Spiral:weak_dissipator"], RHO_0)
    rotation_vortex_pure = dot(n0, cross(rv0, bloch(vort_pure)))
    rotation_spiral_pure = dot(n0, cross(rv0, bloch(spir_pure)))
    rotation_vortex_weak = dot(n0, cross(rv0, bloch(vort_weak)))
    rotation_spiral_weak = dot(n0, cross(rv0, bloch(spir_weak)))

    pair_separation = Dict(
        "Funnel_vs_Cannon" => Dict(
            "source_table_claim" => "opposite Weyl sign plus pinned coefficient-distinct dissipator family",
            "trace_distance_rho_0" => trace_distance(apply_channel(channels["Funnel"], RHO_0), apply_channel(channels["Cannon"], RHO_0)),
            "trace_distance_rho_1" => trace_distance(apply_channel(channels["Funnel"], RHO_1), apply_channel(channels["Cannon"], RHO_1)),
            "erased_weyl_trace_distance_rho_0" => trace_distance(apply_channel(channels["Funnel"], RHO_0), apply_channel(erased_channels["Cannon"], RHO_0)),
        ),
        "Vortex_vs_Spiral" => Dict(
            "pure_trace_distance_rho_0" => trace_distance(vort_pure, spir_pure),
            "weak_trace_distance_rho_0" => trace_distance(vort_weak, spir_weak),
            "vortex_rotation_direction_pure" => rotation_vortex_pure,
            "spiral_rotation_direction_pure" => rotation_spiral_pure,
            "vortex_rotation_direction_weak" => rotation_vortex_weak,
            "spiral_rotation_direction_weak" => rotation_spiral_weak,
            "erased_weyl_pure_trace_distance_rho_0" => trace_distance(vort_pure, apply_channel(erased_channels["Spiral:pure_hamiltonian"], RHO_0)),
            "erased_weyl_weak_trace_distance_rho_0" => trace_distance(vort_weak, apply_channel(erased_channels["Spiral:weak_dissipator"], RHO_0)),
        ),
        "Pit_vs_Source" => Dict(
            "pit_sensitive_rz_drift" => pit_drift_z,
            "source_sensitive_rz_drift" => source_drift_z,
            "opposite_sink_source_directions" => pit_drift_z < -1.0e-4 && source_drift_z > 1.0e-4,
            "finite_channel_trace_distance_rho_0" => trace_distance(apply_channel(channels["Pit"], RHO_0), apply_channel(channels["Source"], RHO_0)),
        ),
        "Hill_vs_Citadel" => Dict(
            "projector_overlap_matrix_z_vs_x" => [
                [real(tr(PZ_PLUS * PX_PLUS)), real(tr(PZ_PLUS * PX_MINUS))],
                [real(tr(PZ_MINUS * PX_PLUS)), real(tr(PZ_MINUS * PX_MINUS))],
            ],
            "post_channel_trace_distance_rho_0" => trace_distance(apply_channel(channels["Hill"], RHO_0), apply_channel(channels["Citadel"], RHO_0)),
            "commuting_frame_control_trace_distance_rho_0" => trace_distance(apply_channel(channels["Hill"], RHO_0), apply_channel(erased_channels["Citadel:commuting_frame"], RHO_0)),
            "distinct_strata_pass" => trace_distance(apply_channel(channels["Hill"], RHO_0), apply_channel(channels["Citadel"], RHO_0)) > 1.0e-4,
        ),
    )

    placements = placement_table(channels)
    negative_controls = Dict(
        "erased_weyl_sign_collapses_Funnel_Cannon" => pair_separation["Funnel_vs_Cannon"]["erased_weyl_trace_distance_rho_0"] <= 1.0e-7,
        "erased_weyl_sign_collapses_Vortex_Spiral_pure" => pair_separation["Vortex_vs_Spiral"]["erased_weyl_pure_trace_distance_rho_0"] <= 1.0e-7,
        "erased_weyl_sign_collapses_Vortex_Spiral_weak" => pair_separation["Vortex_vs_Spiral"]["erased_weyl_weak_trace_distance_rho_0"] <= 1.0e-7,
        "commuting_frame_Si_control_collapses_Hill_Citadel" => pair_separation["Hill_vs_Citadel"]["commuting_frame_control_trace_distance_rho_0"] <= 1.0e-7,
        "sigma_only_swap_gives_source_jump_direction" => pit_sigma_only_drift_z > 1.0e-4,
        "sigma_only_swap_full_generator_still_differs_due_H_sign" => trace_distance(apply_channel(erased_channels["Pit:sigma_only_swap"], RHO_0), apply_channel(channels["Source"], RHO_0)) > 1.0e-4,
        "sigma_swapped_pit_source_convention_equals_source" => trace_distance(apply_channel(erased_channels["Pit:sigma_swap_source_side"], RHO_0), apply_channel(channels["Source"], RHO_0)) <= 1.0e-7,
    )

    cptp_pass = all(cert["cptp"]["pass"] for cert in values(certs))
    fixed_pass = fixed_point_checks["Pit"]["attractor_side_pass"] &&
        fixed_point_checks["Source"]["attractor_side_pass"] &&
        fixed_point_checks["Hill"]["sensitive_state_control_pass"] &&
        fixed_point_checks["Citadel"]["sensitive_state_control_pass"] &&
        fixed_point_checks["Hill"]["commutator_K_P_plus_norm"] <= TOL &&
        fixed_point_checks["Citadel"]["commutator_K_P_plus_norm"] <= TOL
    pair_pass = pair_separation["Funnel_vs_Cannon"]["trace_distance_rho_0"] > 1.0e-4 &&
        pair_separation["Vortex_vs_Spiral"]["pure_trace_distance_rho_0"] > 1.0e-4 &&
        pair_separation["Vortex_vs_Spiral"]["weak_trace_distance_rho_0"] > 1.0e-4 &&
        pair_separation["Vortex_vs_Spiral"]["vortex_rotation_direction_pure"] * pair_separation["Vortex_vs_Spiral"]["spiral_rotation_direction_pure"] < 0.0 &&
        pair_separation["Pit_vs_Source"]["opposite_sink_source_directions"] &&
        pair_separation["Hill_vs_Citadel"]["distinct_strata_pass"]
    placement_pass = length(placements) == 16 &&
        count(row -> row["loop"] == "inner" && row["loop_coordinate_density_delta_max"] <= TOL, placements) == 8 &&
        count(row -> row["loop"] == "outer" && row["loop_coordinate_density_delta_max"] > 1.0e-4, placements) == 8
    negative_pass = all(values(negative_controls))
    smt_pass = z3_proof["pass"]
    state_pass = density_valid(RHO_0)["pass"] && density_valid(RHO_1)["pass"] && density_valid(SENSITIVE_RHO)["pass"]
    qo_pass = qo_check["pass"]
    source_lock_pass = source_lock["all_fresh"]
    unitality_pass = unitality["pass"]
    axis0_pass = axis0["pass"]
    all_pass = cptp_pass &&
        fixed_pass &&
        pair_pass &&
        placement_pass &&
        negative_pass &&
        smt_pass &&
        state_pass &&
        qo_pass &&
        source_lock_pass &&
        unitality_pass &&
        axis0_pass

    choi_min = minimum(cert["cptp"]["choi_min_eigenvalue"] for cert in values(certs))
    tp_max = maximum(cert["cptp"]["tp_residual"] for cert in values(certs))
    shared_scalars = Dict(
        "choi_min_eigenvalue_min" => choi_min,
        "tp_residual_max" => tp_max,
        "pair_funnel_cannon_trace_distance_rho_0" => pair_separation["Funnel_vs_Cannon"]["trace_distance_rho_0"],
        "pair_funnel_cannon_erased_trace_distance_rho_0" => pair_separation["Funnel_vs_Cannon"]["erased_weyl_trace_distance_rho_0"],
        "pair_vortex_spiral_pure_trace_distance_rho_0" => pair_separation["Vortex_vs_Spiral"]["pure_trace_distance_rho_0"],
        "pair_vortex_spiral_weak_trace_distance_rho_0" => pair_separation["Vortex_vs_Spiral"]["weak_trace_distance_rho_0"],
        "pair_vortex_spiral_erased_pure_trace_distance_rho_0" => pair_separation["Vortex_vs_Spiral"]["erased_weyl_pure_trace_distance_rho_0"],
        "pair_pit_rz_drift" => pit_drift_z,
        "pair_source_rz_drift" => source_drift_z,
        "pair_hill_citadel_post_channel_trace_distance_rho_0" => pair_separation["Hill_vs_Citadel"]["post_channel_trace_distance_rho_0"],
        "placement_count" => Float64(length(placements)),
        "fiber_stationary_count" => Float64(count(row -> row["loop"] == "inner" && row["loop_coordinate_density_delta_max"] <= TOL, placements)),
        "base_visible_count" => Float64(count(row -> row["loop"] == "outer" && row["loop_coordinate_density_delta_max"] > 1.0e-4, placements)),
        "smt_pit_source_forced_equal_unsat" => z3_proof["verdict"] == "unsat" ? 1.0 : 0.0,
        "smt_sigma_swapped_valid" => z3_proof["sigma_swapped_pit_source_convention_inequality"] == "unsat" ? 1.0 : 0.0,
        "source_lock_fresh" => source_lock_pass ? 1.0 : 0.0,
        "unitality_max_non_ni_E_I_minus_I_fro_norm" => unitality["max_non_ni_E_I_minus_I_fro_norm"],
        "unitality_min_ni_E_I_minus_I_fro_norm" => unitality["min_ni_E_I_minus_I_fro_norm"],
        "axis0_pr_sign_Ne" => axis0["doctrine_family_sign_table"]["pauli_participation_ratio"]["Ne"] == "+" ? 1.0 : -1.0,
        "axis0_pr_sign_Ni" => axis0["doctrine_family_sign_table"]["pauli_participation_ratio"]["Ni"] == "+" ? 1.0 : -1.0,
        "axis0_pr_sign_Se" => axis0["doctrine_family_sign_table"]["pauli_participation_ratio"]["Se"] == "+" ? 1.0 : -1.0,
        "axis0_pr_sign_Si" => axis0["doctrine_family_sign_table"]["pauli_participation_ratio"]["Si"] == "+" ? 1.0 : -1.0,
    )

    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => replace(string(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS")), "+00:00" => "Z"),
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "packages_used" => ["LinearAlgebra", "QuantumOptics", "Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "source_line_refs" => SOURCE_LINE_REFS,
        "source_lock_freshness" => source_lock,
        "pin_spec" => PIN_SPEC,
        "pauli_expansion_families" => Dict(
            "Se_Funnel_L" => SE_FUNNEL_COEFFS,
            "Se_Cannon_R" => SE_CANNON_COEFFS,
            "Ne_Vortex_L" => NE_VORTEX_COEFFS,
            "Ne_Spiral_R" => NE_SPIRAL_COEFFS,
            "family_note" => "Coefficient rows are distinct but phase/sign gauge-equivalent within each L/R pair so Weyl erasure can be a decisive control.",
        ),
        "pauli_expansion_family_pin_metadata" => PAULI_EXPANSION_FAMILY_PIN_METADATA,
        "states" => Dict(
            "rho_0" => RHO_0,
            "rho_1" => RHO_1,
            "sensitive_rho" => SENSITIVE_RHO,
            "rho_0_valid" => density_valid(RHO_0),
            "rho_1_valid" => density_valid(RHO_1),
            "sensitive_rho_valid" => density_valid(SENSITIVE_RHO),
        ),
        "terrain_certificates" => certs,
        "fixed_point_and_strata_checks" => fixed_point_checks,
        "unitality_column" => unitality,
        "axis0_response" => axis0,
        "entropy_columns" => entropy,
        "pair_separation_table" => pair_separation,
        "placements_16" => placements,
        "negative_controls" => negative_controls,
        "julia_native_checks" => Dict("quantumoptics_entropy_crosscheck" => qo_check),
        "smt" => Dict("julia_z3" => z3_proof),
        "sigma_swap_control_detail" => Dict(
            "pit_sigma_only_swap_sensitive_rz_drift" => pit_sigma_only_drift_z,
            "source_sensitive_rz_drift" => source_drift_z,
            "interpretation" => "sigma-only Pit swap matches the Source jump direction; full equality also requires the R-sheet Hamiltonian sign, which is checked separately.",
        ),
        "crossover_proofs" => Dict(
            "julia_z3" => merge(Dict("ran" => true, "load_bearing" => true, "verdict" => z3_proof["verdict"]), z3_proof),
        ),
        "shared_scalars" => shared_scalars,
        "controls" => Dict(
            "state_pass" => state_pass,
            "cptp_pass" => cptp_pass,
            "fixed_pass" => fixed_pass,
            "pair_pass" => pair_pass,
            "placement_pass" => placement_pass,
            "negative_pass" => negative_pass,
            "smt_pass" => smt_pass,
            "quantumoptics_pass" => qo_pass,
            "source_lock_pass" => source_lock_pass,
            "unitality_pass" => unitality_pass,
            "axis0_response_computed" => axis0_pass,
            "classification_ceiling_held" => CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false && FORMAL_ADMISSION_ALLOWED == false,
        ),
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, jsonable(result), 2)
        write(io, "\n")
    end
    println(JSON.json(Dict(
        "result_path" => RESULT_PATH,
        "all_pass" => result["all_pass"],
        "pair_funnel_cannon" => result["shared_scalars"]["pair_funnel_cannon_trace_distance_rho_0"],
        "placements" => result["shared_scalars"]["placement_count"],
        "julia_z3" => result["smt"]["julia_z3"]["verdict"],
    ), 2))
    return result["all_pass"] ? 0 : 1
end

exit(main())
