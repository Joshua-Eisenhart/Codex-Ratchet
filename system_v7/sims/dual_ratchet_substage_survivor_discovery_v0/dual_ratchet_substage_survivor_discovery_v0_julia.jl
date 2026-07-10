using Dates
using JSON3
using LinearAlgebra
using QuantumOptics
using Random
using SHA

const HERE = @__DIR__
const SPEC_PATH = joinpath(HERE, "spec.json")
const RESULT_PATH = joinpath(HERE, "results", "dual_ratchet_substage_survivor_discovery_v0_julia_results.json")
const SOURCE_PATH = abspath(@__FILE__)
const CARRIER_PROJECT = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml"
const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const PAULI = [SX, SY, SZ]
const G = 0.35
const KAP = 1.0
const FINGERPRINT_EPS = 1.0e-14
const STRICT_ENTROPY = 1.0e-8

struct AffineMap
    matrix::Matrix{Float64}
    offset::Vector{Float64}
end

struct Candidate
    candidate_id::String
    samples::Vector{AffineMap}
end

clean_real(value::Real) = abs(Float64(value)) < 1.0e-14 ? 0.0 : Float64(value)

function compact_result(value)
    if value isa AbstractDict
        return Dict(
            string(key) => compact_result(item)
            for (key, item) in value
            if string(key) != "fingerprint"
        )
    elseif value isa AbstractVector || value isa Tuple
        return [compact_result(item) for item in value]
    end
    value
end

function sha256_file(path::String)::String
    open(path, "r") do io
        bytes2hex(SHA.sha256(io))
    end
end

normalize_axis(axis) = Float64.(axis) / LinearAlgebra.norm(Float64.(axis))

function dephasing_map(axis, strength::Float64)
    direction = normalize_axis(axis)
    AffineMap((1.0 - strength) * Matrix{Float64}(I, 3, 3) + strength * (direction * direction'), zeros(3))
end

function rotation_map(axis, angle::Float64)
    x, y, z = normalize_axis(axis)
    cross = Float64[0 -z y; z 0 -x; -y x 0]
    matrix = Matrix{Float64}(I, 3, 3) + sin(angle) * cross + (1.0 - cos(angle)) * (cross * cross)
    AffineMap(matrix, zeros(3))
end

depolarizing_map(strength::Float64) = AffineMap((1.0 - strength) * Matrix{Float64}(I, 3, 3), zeros(3))

function amplitude_damping_map(strength::Float64, pole::Int)
    matrix = diagm([sqrt(1.0 - strength), sqrt(1.0 - strength), 1.0 - strength])
    AffineMap(matrix, [0.0, 0.0, pole * strength])
end

identity_map() = AffineMap(Matrix{Float64}(I, 3, 3), zeros(3))
transpose_map() = AffineMap(diagm([1.0, -1.0, 1.0]), zeros(3))

function build_candidates(spec; include_generic_axes::Bool, erase_rotation_sides::Bool=false)
    axes = [Float64.(axis) for axis in spec["main_axis_registry"]]
    registry = ["pauli_x", "pauli_y", "pauli_z"]
    if include_generic_axes
        append!(axes, [Float64.(axis) for axis in spec["generic_axis_challenge"]])
        append!(registry, ["generic_h0", "generic_123"])
    end
    candidates = Candidate[]
    truth = Dict{String,Any}()

    function add(samples::Vector{AffineMap}; family::String, axis_registry=nothing, main_registry::Bool=false, expected_operator=nothing)
        candidate_id = "candidate_" * lpad(string(length(candidates)), 3, '0')
        push!(candidates, Candidate(candidate_id, samples))
        truth[candidate_id] = Dict(
            "family" => family,
            "axis_registry" => axis_registry,
            "main_registry" => main_registry,
            "expected_operator" => expected_operator,
        )
    end

    strengths = Float64.(spec["candidate_family_samples"]["axis_dephasing_strengths"])
    angles = Float64.(spec["candidate_family_samples"]["axis_rotation_absolute_angles"])
    sides = erase_rotation_sides ? [1] : Int.(spec["candidate_family_samples"]["axis_rotation_sides"])
    for (axis, registry_name) in zip(axes, registry)
        dephasing_samples = [dephasing_map(axis, strength) for strength in strengths]
        dephasing_operator = startswith(registry_name, "pauli_") ? (registry_name in ["pauli_x", "pauli_y"] ? "Te" : "Ti") : nothing
        add(
            dephasing_samples;
            family="axis_dephasing_path",
            axis_registry=registry_name,
            main_registry=startswith(registry_name, "pauli_"),
            expected_operator=dephasing_operator,
        )
        rotation_samples = [rotation_map(axis, side * angle) for angle in angles for side in sides]
        rotation_operator = startswith(registry_name, "pauli_") ? (registry_name in ["pauli_x", "pauli_y"] ? "Fi" : "Fe") : nothing
        add(
            rotation_samples;
            family="axis_rotation_path",
            axis_registry=registry_name,
            main_registry=startswith(registry_name, "pauli_"),
            expected_operator=rotation_operator,
        )
    end
    add([identity_map(), identity_map(), identity_map()]; family="identity_null")
    add(
        [depolarizing_map(Float64(value)) for value in spec["candidate_family_samples"]["isotropic_depolarizing_strengths"]];
        family="isotropic_depolarizing_control",
    )
    add(
        [
            amplitude_damping_map(Float64(value), Int(pole))
            for value in spec["candidate_family_samples"]["amplitude_damping_strengths"]
            for pole in spec["candidate_family_samples"]["amplitude_damping_poles"]
        ];
        family="amplitude_damping_control",
        axis_registry="pauli_z",
    )
    add([transpose_map()]; family="transpose_non_cp_control")
    candidates, truth
end

function dop(lindblad::Matrix{ComplexF64}, rho::Matrix{ComplexF64})
    lindblad * rho * lindblad' - 0.5 * (lindblad' * lindblad * rho + rho * lindblad' * lindblad)
end

function terrain_generator(terrain::Int)
    epsilon, kind, pole = [
        (1, "damp", 1),
        (1, "depol", 0),
        (1, "damp", -1),
        (1, "proj", 0),
        (-1, "damp", -1),
        (-1, "depol", 0),
        (-1, "damp", 1),
        (-1, "proj", 0),
    ][terrain + 1]
    hamiltonian = epsilon * (SX + SY + SZ) / sqrt(3.0)
    sp = 0.5 * (SX + im * SY)
    sm = 0.5 * (SX - im * SY)
    function generator(rho::Matrix{ComplexF64})
        output = -im * G * (hamiltonian * rho - rho * hamiltonian)
        if kind == "damp"
            output += KAP * dop(pole > 0 ? sp : sm, rho)
        elseif kind == "depol"
            output += 0.5 * KAP * (dop(SX, rho) + dop(SY, rho))
        else
            output += KAP * dop(SZ, rho)
        end
        output
    end
    generator
end

function density_from_bloch(vector)
    value = Float64.(vector)
    0.5 * (I2 + value[1] * SX + value[2] * SY + value[3] * SZ)
end

bloch(rho) = Float64[real(tr(rho * sigma)) for sigma in PAULI]

function terrain_superoperator(terrain::Int)
    generator = terrain_generator(terrain)
    liouvillian = zeros(ComplexF64, 4, 4)
    for index in 1:4
        basis = zeros(ComplexF64, 2, 2)
        basis[index] = 1.0
        liouvillian[:, index] = vec(generator(basis))
    end
    exp(liouvillian)
end

function terrain_map(terrain::Int)
    flow = terrain_superoperator(terrain)
    apply(rho) = reshape(flow * vec(rho), 2, 2)
    offset = bloch(apply(density_from_bloch(zeros(3))))
    columns = Vector{Float64}[]
    for index in 1:3
        basis = zeros(3)
        basis[index] = 1.0
        push!(columns, bloch(apply(density_from_bloch(basis))) - offset)
    end
    AffineMap(hcat(columns...), offset)
end

terrain_maps() = [terrain_map(index) for index in 0:7]
fixed_point(channel::AffineMap) = (Matrix{Float64}(I, 3, 3) - channel.matrix) \ channel.offset

const AXIS_PERMUTATIONS = [
    (1, 2, 3),
    (1, 3, 2),
    (2, 1, 3),
    (2, 3, 1),
    (3, 1, 2),
    (3, 2, 1),
]

function signed_permutation_matrices()
    output = Matrix{Float64}[]
    for permutation in AXIS_PERMUTATIONS
        for sx in (-1.0, 1.0), sy in (-1.0, 1.0), sz in (-1.0, 1.0)
            matrix = zeros(3, 3)
            for (row, column) in enumerate(permutation)
                matrix[row, column] = (sx, sy, sz)[row]
            end
            push!(output, matrix)
        end
    end
    output
end

function discover_terrain_automorphisms(terrains::Vector{AffineMap}, tolerance::Float64)
    rows = Dict{String,Any}[]
    for matrix in signed_permutation_matrices()
        mapping = Int[]
        errors = Float64[]
        unused = Set(1:length(terrains))
        for terrain in terrains
            transformed_matrix = matrix * terrain.matrix * matrix'
            transformed_offset = matrix * terrain.offset
            costs = [norm(transformed_matrix - target.matrix) + norm(transformed_offset - target.offset) for target in terrains]
            index = first(sort(collect(unused); by=candidate -> costs[candidate]))
            push!(mapping, index)
            push!(errors, costs[index])
            delete!(unused, index)
        end
        if length(unique(mapping)) == length(terrains) && maximum(errors) <= tolerance
            push!(rows, Dict(
                "matrix" => matrix,
                "determinant" => round(Int, det(matrix)),
                "terrain_permutation_one_based" => mapping,
                "maximum_match_error" => maximum(errors),
            ))
        end
    end
    proper = [row for row in rows if row["determinant"] == 1]
    axis_orbits = Vector{Int}[]
    for axis_index in 1:3
        vector = Matrix{Float64}(I, 3, 3)[:, axis_index]
        orbit = sort(unique(argmax(abs.(row["matrix"] * vector)) for row in proper))
        push!(axis_orbits, [value - 1 for value in orbit])
    end
    Dict(
        "rows" => rows,
        "count" => length(rows),
        "proper_rotation_count" => length(proper),
        "axis_orbits_zero_based" => axis_orbits,
        "all_matches_within_tolerance" => all(row["maximum_match_error"] <= tolerance for row in rows),
    )
end

function symmetry_closed_probes(seed::Int, spec, automorphisms)
    rng = MersenneTwister(seed)
    base_count = Int(spec["probe_base_count"])
    radius_min = Float64(spec["probe_radius_min"])
    radius_max = Float64(spec["probe_radius_max"])
    seen = Dict{Tuple{Float64,Float64,Float64},Vector{Float64}}()
    for _ in 1:base_count
        vector = randn(rng, 3)
        vector /= norm(vector)
        vector *= radius_min + rand(rng) * (radius_max - radius_min)
        for row in automorphisms
            moved = row["matrix"] * vector
            key = Tuple(round.(moved; digits=13))
            seen[key] = moved
        end
    end
    [seen[key] for key in sort(collect(keys(seen)))]
end

apply_affine(channel::AffineMap, vector) = channel.matrix * vector + channel.offset

function apply_to_matrix(channel::AffineMap, value::Matrix{ComplexF64})
    trace_value = tr(value)
    coordinates = ComplexF64[tr(value * sigma) for sigma in PAULI]
    moved = channel.matrix * coordinates + channel.offset * trace_value
    0.5 * (trace_value * I2 + sum(moved[index] * PAULI[index] for index in 1:3))
end

function choi_matrix(channel::AffineMap)
    choi = zeros(ComplexF64, 4, 4)
    for row in 1:2, column in 1:2
        matrix_unit = zeros(ComplexF64, 2, 2)
        matrix_unit[row, column] = 1.0
        moved = apply_to_matrix(channel, matrix_unit)
        choi[(2row - 1):(2row), (2column - 1):(2column)] = moved
    end
    Hermitian((choi + choi') / 2)
end

function physical_summary(candidate::Candidate, tolerance::Float64)
    minimum_choi = minimum(minimum(real.(eigvals(choi_matrix(sample)))) for sample in candidate.samples)
    maximum_offset = maximum(norm(sample.offset) for sample in candidate.samples)
    Dict(
        "minimum_choi_eigenvalue" => minimum_choi,
        "all_samples_cp" => minimum_choi >= -tolerance,
        "maximum_unital_offset_norm" => maximum_offset,
        "all_samples_unital" => maximum_offset <= tolerance,
    )
end

function entropy_nats(vector, basis)
    rho = density_from_bloch(vector)
    operator = QuantumOptics.DenseOperator(basis, basis, rho)
    clean_real(real(QuantumOptics.entropy_vn(operator)))
end

function matrix_log_psd(rho::Matrix{ComplexF64})
    values, vectors = eigen(Hermitian((rho + rho') / 2))
    vectors * Diagonal(log.(clamp.(real.(values), 1.0e-12, 1.0))) * vectors'
end

function relative_entropy(left, right)
    rho = density_from_bloch(left)
    sigma = density_from_bloch(right)
    max(clean_real(real(tr(rho * (matrix_log_psd(rho) - matrix_log_psd(sigma))))), 0.0)
end

function normalized(vector::Vector{Float64})
    magnitude = norm(vector)
    magnitude <= FINGERPRINT_EPS ? zeros(length(vector)) : vector / magnitude
end

function geometry_fingerprint(candidate::Candidate, terrains::Vector{AffineMap}, probes)
    values = Float64[]
    for sample in candidate.samples, terrain in terrains, probe in probes
        terrain_after_operator = apply_affine(terrain, apply_affine(sample, probe))
        operator_after_terrain = apply_affine(sample, apply_affine(terrain, probe))
        push!(values, norm(terrain_after_operator - operator_after_terrain))
    end
    sort(values)
end

function entropy_fingerprint(candidate::Candidate, terrains::Vector{AffineMap}, probes, basis)
    direct = Float64[]
    values = Float64[]
    fixed_points = [fixed_point(terrain) for terrain in terrains]
    for sample in candidate.samples
        for probe in probes
            push!(direct, entropy_nats(apply_affine(sample, probe), basis) - entropy_nats(probe, basis))
        end
        for (terrain, fixed) in zip(terrains, fixed_points), probe in probes
            terrain_first = apply_affine(terrain, probe)
            terrain_after_operator = apply_affine(terrain, apply_affine(sample, probe))
            operator_after_terrain = apply_affine(sample, terrain_first)
            base_u = relative_entropy(terrain_first, fixed)
            first_u = relative_entropy(terrain_after_operator, fixed)
            second_u = relative_entropy(operator_after_terrain, fixed)
            push!(values, first_u - base_u)
            push!(values, abs(first_u - second_u))
        end
    end
    direct, sort(values)
end

function fixed_direction_dimension(matrix::Matrix{Float64}, tolerance::Float64)
    count(value -> value <= tolerance, svdvals(matrix - Matrix{Float64}(I, 3, 3)))
end

function fixed_direction_line(matrix::Matrix{Float64})
    decomposition = svd(matrix - Matrix{Float64}(I, 3, 3))
    count(value -> value <= 1.0e-8, decomposition.S) == 1 || return nothing
    normalize_axis(decomposition.V[:, end])
end

function geometry_lane(candidate::Candidate, terrains, probes, spec)
    tolerance = Float64(spec["density_tolerance"])
    physical = physical_summary(candidate, tolerance)
    identity_distances = [norm(sample.matrix - Matrix{Float64}(I, 3, 3)) + norm(sample.offset) for sample in candidate.samples]
    fixed_dimensions = [fixed_direction_dimension(sample.matrix, Float64(spec["identity_tolerance"])) for sample in candidate.samples]
    fixed_lines = [fixed_direction_line(sample.matrix) for sample in candidate.samples]
    isometry_residuals = [norm(sample.matrix' * sample.matrix - Matrix{Float64}(I, 3, 3)) for sample in candidate.samples]
    contractions = [minimum(svdvals(sample.matrix)) for sample in candidate.samples]
    nonidentity = maximum(identity_distances) > Float64(spec["identity_tolerance"])
    one_fixed_direction = !isempty(fixed_dimensions) && all(value == 1 for value in fixed_dimensions)
    family = if maximum(isometry_residuals) <= 1.0e-8
        "geometry_isometry_axis"
    elseif one_fixed_direction && minimum(contractions) < 1.0 - 1.0e-8
        "geometry_contraction_axis"
    else
        "geometry_other"
    end
    fingerprint = geometry_fingerprint(candidate, terrains, probes)
    admissible = Bool(
        physical["all_samples_cp"] &&
        physical["all_samples_unital"] &&
        nonidentity &&
        one_fixed_direction &&
        family in ["geometry_isometry_axis", "geometry_contraction_axis"] &&
        norm(fingerprint) > FINGERPRINT_EPS
    )
    reasons = String[]
    !physical["all_samples_cp"] && push!(reasons, "non_cp")
    !physical["all_samples_unital"] && push!(reasons, "nonunital")
    !nonidentity && push!(reasons, "identity")
    !one_fixed_direction && push!(reasons, "fixed_direction_dimension_not_one")
    family == "geometry_other" && push!(reasons, "no_axis_family")
    norm(fingerprint) <= FINGERPRINT_EPS && push!(reasons, "terrain_commutator_fingerprint_zero")
    line_index = findfirst(line -> line !== nothing, fixed_lines)
    fixed_line = line_index === nothing ? nothing : fixed_lines[line_index]
    Dict(
        "candidate_id" => candidate.candidate_id,
        "admissible" => admissible,
        "rejection_reasons" => reasons,
        "lane_family" => family,
        "fixed_direction_dimensions" => fixed_dimensions,
        "fixed_direction_line" => fixed_line,
        "fingerprint_norm" => norm(fingerprint),
        "fingerprint" => normalized(fingerprint),
        "physical" => physical,
    )
end

function entropy_lane(candidate::Candidate, terrains, probes, spec, basis)
    physical = physical_summary(candidate, Float64(spec["density_tolerance"]))
    direct, fingerprint = entropy_fingerprint(candidate, terrains, probes, basis)
    entropy_preserved = maximum(abs.(direct)) <= 1.0e-8
    mixing = minimum(direct) >= -1.0e-8 && maximum(direct) > STRICT_ENTROPY
    family = mixing ? "entropy_mixing" : (entropy_preserved ? "entropy_isospectral" : "entropy_mixed_direction")
    fingerprint_norm = norm(fingerprint)
    admissible = Bool(
        physical["all_samples_cp"] &&
        family in ["entropy_mixing", "entropy_isospectral"] &&
        fingerprint_norm > 1.0e-8
    )
    reasons = String[]
    !physical["all_samples_cp"] && push!(reasons, "non_cp")
    family == "entropy_mixed_direction" && push!(reasons, "von_neumann_entropy_not_one_direction_or_isospectral")
    fingerprint_norm <= 1.0e-8 && push!(reasons, "terrain_relative_entropy_response_zero")
    Dict(
        "candidate_id" => candidate.candidate_id,
        "admissible" => admissible,
        "rejection_reasons" => reasons,
        "lane_family" => family,
        "direct_entropy_delta_min" => minimum(direct),
        "direct_entropy_delta_max" => maximum(direct),
        "fingerprint_norm" => fingerprint_norm,
        "fingerprint" => normalized(fingerprint),
        "physical" => physical,
    )
end

function canonical_line(vector; digits::Int=10)
    value = normalize_axis(vector)
    pivot = findfirst(item -> abs(item) > 1.0e-10, value)
    pivot !== nothing && value[pivot] < 0.0 && (value = -value)
    Tuple(clean_real.(round.(value; digits=digits)))
end

function geometry_orbit_key(fixed_line, automorphisms)
    proper = [row for row in automorphisms if row["determinant"] == 1]
    Tuple(sort(unique(canonical_line(row["matrix"] * fixed_line) for row in proper)))
end

function geometry_components(rows, automorphisms)
    groups = Dict{Any,Vector{String}}()
    for row in rows
        line = row["fixed_direction_line"]
        key = line === nothing ? (row["lane_family"], "no_fixed_line", row["candidate_id"]) : (row["lane_family"], geometry_orbit_key(line, automorphisms))
        push!(get!(groups, key, String[]), row["candidate_id"])
    end
    sort([sort(members) for members in values(groups)]; by=members -> Tuple(members))
end

function connected_components(rows, threshold::Float64)
    by_id = Dict(row["candidate_id"] => row for row in rows)
    ids = sort(collect(keys(by_id)))
    adjacency = Dict(candidate_id => Set{String}() for candidate_id in ids)
    for left_index in eachindex(ids)
        left_id = ids[left_index]
        for right_id in ids[(left_index + 1):end]
            left = by_id[left_id]
            right = by_id[right_id]
            left["lane_family"] == right["lane_family"] || continue
            left_fp = Float64.(left["fingerprint"])
            right_fp = Float64.(right["fingerprint"])
            similar = if norm(left_fp) <= FINGERPRINT_EPS || norm(right_fp) <= FINGERPRINT_EPS
                norm(left_fp) <= FINGERPRINT_EPS && norm(right_fp) <= FINGERPRINT_EPS
            else
                dot(left_fp, right_fp) >= threshold
            end
            if similar
                push!(adjacency[left_id], right_id)
                push!(adjacency[right_id], left_id)
            end
        end
    end
    components = Vector{Vector{String}}()
    unseen = Set(ids)
    while !isempty(unseen)
        start = minimum(unseen)
        stack = [start]
        component = Set{String}()
        while !isempty(stack)
            current = pop!(stack)
            current in component && continue
            push!(component, current)
            append!(stack, sort(collect(setdiff(adjacency[current], component)); rev=true))
        end
        setdiff!(unseen, component)
        push!(components, sort(collect(component)))
    end
    sort(components; by=members -> Tuple(members))
end

partition_key(components) = Tuple(sort([Tuple(sort(component)) for component in components]))
restrict_rows(rows, ids) = [row for row in rows if row["candidate_id"] in ids]

function run_order(order::String, geometry_rows, entropy_rows)
    geometry_by_id = Dict(row["candidate_id"] => row for row in geometry_rows)
    entropy_by_id = Dict(row["candidate_id"] => row for row in entropy_rows)
    survivors = Set(keys(geometry_by_id))
    hell = Dict{String,Any}[]
    stages = order == "G_then_E" ? ["geometry", "entropy"] : ["entropy", "geometry"]
    for stage in stages
        lane = stage == "geometry" ? geometry_by_id : entropy_by_id
        rejected = String[]
        for candidate_id in sort(collect(survivors))
            if !lane[candidate_id]["admissible"]
                push!(rejected, candidate_id)
                push!(hell, Dict(
                    "candidate_id" => candidate_id,
                    "rejected_by" => stage,
                    "reasons" => lane[candidate_id]["rejection_reasons"],
                ))
            end
        end
        setdiff!(survivors, rejected)
    end
    Dict(
        "order" => order,
        "semantics" => "fixed_extensional_filter_only",
        "survivor_ids" => sort(collect(survivors)),
        "survivor_count" => length(survivors),
        "hell" => hell,
        "hell_count" => length(hell),
    )
end

function source_bridge(final_components, truth)
    representatives = Dict{String,String}()
    for (operator, family, axis) in [
        ("Ti", "axis_dephasing_path", "pauli_z"),
        ("Te", "axis_dephasing_path", "pauli_x"),
        ("Fi", "axis_rotation_path", "pauli_x"),
        ("Fe", "axis_rotation_path", "pauli_z"),
    ]
        matches = [candidate_id for (candidate_id, metadata) in truth if metadata["family"] == family && metadata["axis_registry"] == axis]
        length(matches) == 1 || error("source bridge could not identify $(operator)")
        representatives[operator] = only(matches)
    end
    class_for = Dict{String,Int}()
    for (class_index, component) in enumerate(final_components), candidate_id in component
        class_for[candidate_id] = class_index - 1
    end
    classes = Dict(operator => get(class_for, candidate_id, -1) for (operator, candidate_id) in representatives)
    y_shared = all(
        any(
            metadata["axis_registry"] == "pauli_y" && metadata["family"] == family && get(class_for, candidate_id, -2) == classes[operator]
            for (candidate_id, metadata) in truth
        )
        for (operator, family) in [("Te", "axis_dephasing_path"), ("Fi", "axis_rotation_path")]
    )
    Dict(
        "source_representatives" => representatives,
        "source_class_indices" => classes,
        "all_four_source_operators_covered" => all(value >= 0 for value in values(classes)),
        "all_four_source_operators_in_distinct_classes" => length(unique(values(classes))) == 4,
        "transverse_y_candidates_share_Te_Fi_classes" => y_shared,
        "representative_choice_emitted_by_ratchet" => false,
    )
end

function one_universe(spec, terrains; include_generic_axes::Bool, erase_rotation_sides::Bool=false, terrain_override=nothing)
    candidates, truth = build_candidates(spec; include_generic_axes=include_generic_axes, erase_rotation_sides=erase_rotation_sides)
    active_terrains = terrain_override === nothing ? terrains : terrain_override
    active_automorphisms = discover_terrain_automorphisms(active_terrains, Float64(spec["automorphism_match_tolerance"]))
    basis = QuantumOptics.SpinBasis(1 // 2)
    seed_runs = Dict{String,Any}[]
    for seed_value in spec["probe_seeds"]
        probes = symmetry_closed_probes(Int(seed_value), spec, active_automorphisms["rows"])
        geometry_rows = [geometry_lane(candidate, active_terrains, probes, spec) for candidate in candidates]
        entropy_rows = [entropy_lane(candidate, active_terrains, probes, spec, basis) for candidate in candidates]
        geometry_ids = Set(row["candidate_id"] for row in geometry_rows if row["admissible"])
        entropy_ids = Set(row["candidate_id"] for row in entropy_rows if row["admissible"])
        intersection = intersect(geometry_ids, entropy_ids)
        geometry_partition = geometry_components(restrict_rows(geometry_rows, intersection), active_automorphisms["rows"])
        entropy_partition = connected_components(restrict_rows(entropy_rows, intersection), Float64(spec["fingerprint_cosine_threshold"]))
        threshold_rows = Dict{String,Any}[]
        for threshold_value in spec["fingerprint_threshold_sweep"]
            g_partition = geometry_components(restrict_rows(geometry_rows, intersection), active_automorphisms["rows"])
            e_partition = connected_components(restrict_rows(entropy_rows, intersection), Float64(threshold_value))
            push!(threshold_rows, Dict(
                "threshold" => threshold_value,
                "geometry_class_count" => length(g_partition),
                "entropy_class_count" => length(e_partition),
                "partitions_agree" => partition_key(g_partition) == partition_key(e_partition),
            ))
        end
        orders = Dict(order => run_order(order, geometry_rows, entropy_rows) for order in ["G_then_E", "E_then_G"])
        push!(seed_runs, Dict(
            "seed" => seed_value,
            "probe_count" => length(probes),
            "geometry_rows" => geometry_rows,
            "entropy_rows" => entropy_rows,
            "geometry_survivor_ids" => sort(collect(geometry_ids)),
            "entropy_survivor_ids" => sort(collect(entropy_ids)),
            "intersection_survivor_ids" => sort(collect(intersection)),
            "intersection_survivor_count" => length(intersection),
            "geometry_partition" => geometry_partition,
            "entropy_partition" => entropy_partition,
            "geometry_class_count" => length(geometry_partition),
            "entropy_class_count" => length(entropy_partition),
            "partitions_agree" => partition_key(geometry_partition) == partition_key(entropy_partition),
            "threshold_sweep" => threshold_rows,
            "orders" => orders,
            "extensional_filter_survivors_agree" => orders["G_then_E"]["survivor_ids"] == orders["E_then_G"]["survivor_ids"],
            "rejection_attribution_differs_by_filter_order" => orders["G_then_E"]["hell"] != orders["E_then_G"]["hell"],
            "source_bridge" => include_generic_axes ? nothing : source_bridge(geometry_partition, truth),
        ))
    end
    reference_partition = partition_key(seed_runs[1]["geometry_partition"])
    enumeration_checks = Dict{String,Any}[]
    reference_rows = seed_runs[1]["geometry_rows"]
    reference_ids = Set(seed_runs[1]["intersection_survivor_ids"])
    for enumeration_seed in spec["candidate_enumeration_seeds"]
        shuffled = copy(restrict_rows(reference_rows, reference_ids))
        Random.shuffle!(MersenneTwister(Int(enumeration_seed)), shuffled)
        partition = geometry_components(shuffled, active_automorphisms["rows"])
        push!(enumeration_checks, Dict("seed" => enumeration_seed, "partition_stable" => partition_key(partition) == reference_partition))
    end
    Dict(
        "include_generic_axes" => include_generic_axes,
        "erase_rotation_sides" => erase_rotation_sides,
        "candidate_truth_posthoc" => truth,
        "terrain_automorphisms" => active_automorphisms,
        "seed_runs" => seed_runs,
        "all_seed_geometry_partitions_stable" => all(partition_key(row["geometry_partition"]) == reference_partition for row in seed_runs),
        "all_seed_entropy_partitions_match_geometry" => all(row["partitions_agree"] for row in seed_runs),
        "all_seed_extensional_filter_intersections_agree" => all(
            row["extensional_filter_survivors_agree"] for row in seed_runs
        ),
        "all_threshold_rows_stable" => all(
            item["geometry_class_count"] == seed_runs[1]["geometry_class_count"] &&
            item["entropy_class_count"] == seed_runs[1]["entropy_class_count"] &&
            item["partitions_agree"]
            for row in seed_runs for item in row["threshold_sweep"]
        ),
        "enumeration_checks" => enumeration_checks,
        "all_enumeration_partitions_stable" => all(row["partition_stable"] for row in enumeration_checks),
        "reference_class_count" => seed_runs[1]["geometry_class_count"],
        "reference_intersection_survivor_count" => seed_runs[1]["intersection_survivor_count"],
        "reference_partition" => seed_runs[1]["geometry_partition"],
    )
end

function main()
    spec = JSON3.read(read(SPEC_PATH, String), Dict{String,Any})
    terrains = terrain_maps()
    automorphisms = discover_terrain_automorphisms(terrains, Float64(spec["automorphism_match_tolerance"]))
    main_universe = one_universe(spec, terrains; include_generic_axes=false)
    generic_challenge = one_universe(spec, terrains; include_generic_axes=true)
    side_erasure = one_universe(spec, terrains; include_generic_axes=false, erase_rotation_sides=true)
    isotropic_terrains = [depolarizing_map(0.45) for _ in terrains]
    terrain_erasure = one_universe(spec, terrains; include_generic_axes=false, terrain_override=isotropic_terrains)
    main_seed = main_universe["seed_runs"][1]
    main_checks = Dict{String,Bool}(
        "strict_carrier_project" => normpath(String(Base.active_project())) == normpath(CARRIER_PROJECT),
        "strict_load_path" => get(ENV, "JULIA_LOAD_PATH", "") == "@:@stdlib" && Base.LOAD_PATH == ["@", "@stdlib"],
        "target_count_not_supplied_to_selectors" => spec["target_survivor_count_supplied_to_selectors"] == false,
        "terrain_automorphism_group_nontrivial" => automorphisms["count"] >= 4,
        "proper_terrain_symmetry_has_transverse_xy_and_axial_z_orbits" => automorphisms["axis_orbits_zero_based"] == [[0, 1], [0, 1], [2]],
        "geometry_and_entropy_intersection_has_four_classes_in_main_registry" => main_universe["reference_class_count"] == 4,
        "independent_lane_partitions_agree_on_main_registry" => main_universe["all_seed_entropy_partitions_match_geometry"],
        "fixed_extensional_filter_orders_share_survivor_intersection" => main_universe[
            "all_seed_extensional_filter_intersections_agree"
        ],
        "probe_seed_partitions_stable" => main_universe["all_seed_geometry_partitions_stable"],
        "candidate_enumeration_partitions_stable" => main_universe["all_enumeration_partitions_stable"],
        "threshold_sweep_partitions_stable" => main_universe["all_threshold_rows_stable"],
        "source_representatives_cover_four_distinct_classes" => main_seed["source_bridge"]["all_four_source_operators_in_distinct_classes"],
        "transverse_y_competitors_quotient_with_source_x_representatives" => main_seed["source_bridge"]["transverse_y_candidates_share_Te_Fi_classes"],
    )
    falsifier_checks = Dict{String,Bool}(
        "generic_axes_add_at_least_one_class" => generic_challenge["reference_class_count"] > 4,
        "generic_axis_challenge_blocks_foundational_four" => generic_challenge["reference_class_count"] != main_universe["reference_class_count"],
        "rotation_side_erasure_changes_entropy_convergence_or_class_count" => !side_erasure["all_seed_entropy_partitions_match_geometry"] || side_erasure["reference_class_count"] != 4,
        "terrain_isotropy_erasure_changes_class_count_or_survivors" => terrain_erasure["reference_class_count"] != 4 || terrain_erasure["reference_intersection_survivor_count"] != main_universe["reference_intersection_survivor_count"],
        "source_gauge_representative_not_emitted" => main_seed["source_bridge"]["representative_choice_emitted_by_ratchet"] == false,
    )
    conditional_four = all(values(main_checks))
    foundational_four = conditional_four && !falsifier_checks["generic_axis_challenge_blocks_foundational_four"]
    all_pass = conditional_four && all(values(falsifier_checks)) && !foundational_four
    result = Dict{String,Any}(
        "schema" => "codex_ratchet.dual_ratchet_substage_survivor_discovery_v0.julia_result.v1",
        "sim_id" => spec["sim_id"],
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "stage_movement_allowed" => false,
        "engine_mode" => spec["engine_mode"],
        "reads_peer_result" => false,
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "spec_sha256" => sha256_file(SPEC_PATH),
        "terrain_automorphisms" => automorphisms,
        "main_pauli_registry" => compact_result(main_universe),
        "generic_axis_challenge" => compact_result(generic_challenge),
        "rotation_side_erasure_control" => compact_result(side_erasure),
        "terrain_isotropy_erasure_control" => compact_result(terrain_erasure),
        "main_checks" => main_checks,
        "falsifier_checks" => falsifier_checks,
        "conditional_four_class_quotient_observed" => conditional_four,
        "foundational_four_substage_emergence_earned" => foundational_four,
        "history_dependent_dual_ratchet_tested" => false,
        "bidirectional_ratchet_earned" => false,
        "per_stage_four_substages_earned" => false,
        "filter_order_semantics" => "The two orders apply fixed extensional predicates, so their common survivor intersection is plumbing, not a noncommuting ratchet result.",
        "scientific_verdict" => conditional_four && !foundational_four ? "conditional_pauli_registry_four_class_operator_quotient_only" : "main_candidate_failed_or_unconditional_result_requires_audit",
        "all_pass" => all_pass,
        "accepted_status_label" => all_pass ? "passes local rerun" : "local candidate gate failed",
        "julia" => Dict(
            "ran" => true,
            "version" => string(VERSION),
            "active_project" => String(Base.active_project()),
            "load_path" => join(Base.LOAD_PATH, ":"),
            "packages_used" => ["QuantumOptics", "LinearAlgebra", "JSON3"],
            "aligned_packages_load_bearing" => ["QuantumOptics"],
            "reads_peer_result" => false,
        ),
        "tool_calls" => [
            Dict(
                "tool" => "QuantumOptics",
                "function" => "QuantumOptics.entropy_vn",
                "input_object" => "independently constructed density outputs for anonymous channel-family samples",
                "output_object" => "von Neumann entropy classification used by the entropy survivor gate",
                "positive_case" => "main entropy partition agrees with the exact geometry orbit quotient",
                "negative_control" => "rotation-side erasure breaks lane agreement",
                "boundary_case" => "identity has zero terrain-relative entropy response",
                "demotion_condition" => "lane, seed, order, threshold, or control failure",
                "gates" => ["conditional_four_class_quotient_observed", "all_pass"],
            ),
        ],
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict("used" => true, "reason" => "load-bearing density-state von Neumann entropy"),
            "LinearAlgebra" => Dict("used" => true, "reason" => "load-bearing independent finite carrier, Choi, affine map, and relative entropy implementation"),
            "JSON3" => Dict("used" => true, "reason" => "supportive spec and result serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("QuantumOptics" => "load_bearing", "LinearAlgebra" => "load_bearing", "JSON3" => "supportive"),
        "claim_ceiling" => spec["claim_ceiling"],
        "blocked_consumers" => [
            "unconditional four-substage emergence",
            "four history-dependent substages inside each of 16 stages",
            "source-gauge representative selection",
            "full R1-R6 ratchet admission",
            "canonical QIT engine admission",
            "Axis0, perception, objects, MMMs, ontologies, or Lev mesh mutation",
        ],
        "written_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
    )
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, result)
        write(io, "\n")
    end
    println(JSON3.write(Dict(
        "result_path" => RESULT_PATH,
        "automorphisms" => automorphisms["count"],
        "proper_axis_orbits" => automorphisms["axis_orbits_zero_based"],
        "main_classes" => main_universe["reference_class_count"],
        "generic_challenge_classes" => generic_challenge["reference_class_count"],
        "conditional_four" => conditional_four,
        "foundational_four" => foundational_four,
        "all_pass" => all_pass,
    )))
    all_pass || exit(1)
end

main()
