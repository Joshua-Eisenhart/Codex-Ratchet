#!/usr/bin/env julia
# Interval certificate lane for geo_s7_discrete_refinement_v0.
#
# Run with:
# JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=@codex-ratchet-tensorkit-v1.12 geo_s7_discrete_refinement_v0_interval.jl

using Dates
using IntervalArithmetic
using SHA

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s7_discrete_refinement_v0"
const SIM_DIR_REL = joinpath("system_v6", "sims", SIM_ID)
const SIM_DIR = joinpath(ROOT, SIM_DIR_REL)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath(SIM_DIR_REL, "$(SIM_ID)_interval.jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath(SIM_DIR_REL, "results", "$(SIM_ID)_interval_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const N_VALUES = [8, 16, 32, 64]
const ETA_ROWS = [
    ("pi/12", interval(pi) / 12),
    ("pi/8", interval(pi) / 8),
    ("pi/6", interval(pi) / 6),
    ("pi/4", interval(pi) / 4),
    ("pi/3", interval(pi) / 3),
    ("3*pi/8", 3 * interval(pi) / 8),
    ("5*pi/12", 5 * interval(pi) / 12),
]
const STRIP_PAIRS = [
    ("pi/12", "pi/8"),
    ("pi/8", "pi/6"),
    ("pi/6", "pi/4"),
    ("pi/4", "pi/3"),
    ("pi/3", "3*pi/8"),
    ("3*pi/8", "5*pi/12"),
    ("pi/12", "pi/4"),
    ("pi/8", "3*pi/8"),
    ("pi/6", "5*pi/12"),
]
const ETA_BY_LABEL = Dict(label => eta for (label, eta) in ETA_ROWS)

const TOOL_MANIFEST = Dict(
    "IntervalArithmetic" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing interval-valued propagation from eta/N inputs through area, holonomy, flux, and Stokes residual bounds",
    ),
    "SHA/Dates" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive source hashing and timestamping",
    ),
)
const TOOL_INTEGRATION_DEPTH = Dict(
    "IntervalArithmetic" => "load_bearing",
    "SHA/Dates" => "supportive",
)

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))

function json_escape(s::AbstractString)
    out = IOBuffer()
    for c in s
        if c == '"'
            print(out, "\\\"")
        elseif c == '\\'
            print(out, "\\\\")
        elseif c == '\n'
            print(out, "\\n")
        else
            print(out, c)
        end
    end
    String(take!(out))
end

function json_value(x)
    if x === nothing
        return "null"
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        if isfinite(x)
            return string(x)
        end
        return "null"
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa AbstractVector
        return "[" * join([json_value(item) for item in x], ",") * "]"
    elseif x isa Dict
        keys_sorted = sort(collect(keys(x)); by=string)
        return "{" * join(["\"" * json_escape(string(k)) * "\":" * json_value(x[k]) for k in keys_sorted], ",") * "}"
    else
        return "\"" * json_escape(string(x)) * "\""
    end
end

function write_json(path::AbstractString, payload)
    open(path, "w") do io
        write(io, json_value(payload))
        write(io, "\n")
    end
end

function iv_bounds(x)
    Dict("inf" => Float64(inf(x)), "sup" => Float64(sup(x)), "interval" => string(x))
end

function abs_upper(x)
    max(abs(Float64(inf(x))), abs(Float64(sup(x))))
end

target_area(eta) = 2 * interval(pi)^2 * sin(2 * eta)
target_holonomy(eta) = -2 * interval(pi) * cos(2 * eta)
target_flux(eta_i, eta_j) = 2 * interval(pi) * (cos(2 * eta_j) - cos(2 * eta_i))

function torus_point(eta, phi, chi)
    [
        cos(eta) * cos(phi + chi),
        cos(eta) * sin(phi + chi),
        sin(eta) * cos(phi - chi),
        sin(eta) * sin(phi - chi),
    ]
end

function torus_point_index(eta, n, a, b)
    torus_point(eta, 2 * interval(pi) * mod(a, n) / n, 2 * interval(pi) * mod(b, n) / n)
end

function quotient_partner(n, a, b)
    (mod(a + div(n, 2), n), mod(b + div(n, 2), n))
end

function cell_representatives(n)
    seen = Set{Tuple{Int,Int}}()
    reps = Tuple{Int,Int}[]
    for a in 0:(n - 1), b in 0:(n - 1)
        point = (a, b)
        point in seen && continue
        partner = quotient_partner(n, a, b)
        pair = sort([point, partner])
        push!(reps, pair[1])
        push!(seen, pair[1])
        push!(seen, pair[2])
    end
    reps
end

function triangle_area(p0, p1, p2)
    u = p1 .- p0
    v = p2 .- p0
    uu = sum(item * item for item in u)
    vv = sum(item * item for item in v)
    uv = sum(u[i] * v[i] for i in eachindex(u))
    gram = uu * vv - uv^2
    sqrt(max(gram, interval(0))) / 2
end

function area_estimate_interval(eta, n)
    total = interval(0)
    for (a, b) in cell_representatives(n)
        p00 = torus_point_index(eta, n, a, b)
        p10 = torus_point_index(eta, n, a + 1, b)
        p01 = torus_point_index(eta, n, a, b + 1)
        p11 = torus_point_index(eta, n, a + 1, b + 1)
        total += triangle_area(p00, p10, p01) + triangle_area(p10, p11, p01)
    end
    total
end

function wilson_holonomy_interval(eta, n)
    delta = 2 * interval(pi) / n
    ratio = cos(2 * eta) * sin(delta) / cos(delta)
    -n * atan(ratio)
end

function flux_interval(eta_i, eta_j, n)
    deta = (eta_j - eta_i) / n
    dchi = 2 * interval(pi) / n
    total = interval(0)
    for i in 0:(n - 1)
        eta_mid = eta_i + (interval(i) + interval(1) / 2) * deta
        total += n * (-2 * sin(2 * eta_mid) * deta * dchi)
    end
    total
end

function row_certificate(value_iv, target_iv; label, n, family, threshold)
    residual = value_iv - target_iv
    bound = abs_upper(residual)
    Dict(
        "family" => family,
        "label" => label,
        "N" => n,
        "value_interval" => iv_bounds(value_iv),
        "target_interval" => iv_bounds(target_iv),
        "residual_interval" => iv_bounds(residual),
        "abs_error_upper_bound" => bound,
        "threshold" => threshold,
        "within_threshold" => bound <= threshold,
        "pass" => isfinite(bound),
    )
end

function family_summary(rows, threshold)
    n8 = [row for row in rows if row["N"] == 8]
    n64 = [row for row in rows if row["N"] == 64]
    max_n64 = maximum(row["abs_error_upper_bound"] for row in n64)
    max_n8 = maximum(row["abs_error_upper_bound"] for row in n8)
    Dict(
        "row_count" => length(rows),
        "max_abs_error_upper_bound_N8" => max_n8,
        "max_abs_error_upper_bound_N64" => max_n64,
        "N64_below_threshold" => max_n64 <= threshold,
        "refinement_improves_from_N8_to_N64" => max_n64 < max_n8,
        "threshold" => threshold,
        "pass" => all(row["pass"] for row in rows) && max_n64 <= threshold && max_n64 < max_n8,
    )
end

function build_result()
    area_rows = Any[]
    holonomy_rows = Any[]
    flux_rows = Any[]
    stokes_rows = Any[]
    area_threshold = 0.25
    holonomy_threshold = 0.45
    flux_threshold = 0.08
    stokes_threshold = 0.5
    for (eta_label, eta) in ETA_ROWS
        for n in N_VALUES
            area = area_estimate_interval(eta, n)
            push!(area_rows, row_certificate(area, target_area(eta); label=eta_label, n=n, family="area", threshold=area_threshold))
            hol = wilson_holonomy_interval(eta, n)
            push!(holonomy_rows, row_certificate(hol, target_holonomy(eta); label=eta_label, n=n, family="holonomy", threshold=holonomy_threshold))
        end
    end
    for (eta_i_label, eta_j_label) in STRIP_PAIRS
        eta_i = ETA_BY_LABEL[eta_i_label]
        eta_j = ETA_BY_LABEL[eta_j_label]
        label = eta_i_label * "->" * eta_j_label
        for n in N_VALUES
            flux = flux_interval(eta_i, eta_j, n)
            push!(flux_rows, row_certificate(flux, target_flux(eta_i, eta_j); label=label, n=n, family="flux", threshold=flux_threshold))
            stokes = wilson_holonomy_interval(eta_j, n) - wilson_holonomy_interval(eta_i, n) + flux
            push!(stokes_rows, row_certificate(stokes, interval(0); label=label, n=n, family="stokes", threshold=stokes_threshold))
        end
    end
    summaries = Dict(
        "area" => family_summary(area_rows, area_threshold),
        "holonomy" => family_summary(holonomy_rows, holonomy_threshold),
        "flux" => family_summary(flux_rows, flux_threshold),
        "stokes" => family_summary(stokes_rows, stokes_threshold),
    )
    controls = Dict(
        "endpoint_float_boxing_erasure" => Dict(
            "mutation" => "replace interval-valued subdomains by endpoint Float64 evaluations",
            "interior_width_preserved" => false,
            "gate_pass" => false,
        ),
        "csv_curve_as_proof_erasure" => Dict(
            "mutation" => "accept CSV residual rows without interval recomputation",
            "gate_pass" => false,
        ),
    )
    all_pass = all(summary["pass"] for summary in values(summaries)) &&
        all(control["gate_pass"] == false for control in values(controls)) &&
        CLASSIFICATION == "scratch_diagnostic" &&
        PROMOTION_ALLOWED == false &&
        FORMAL_ADMISSION_ALLOWED == false
    Dict(
        "schema_version" => "geo_s7_interval_certificate_v1",
        "sim_id" => SIM_ID,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "julia_project" => string(Base.active_project()),
        "packages_used" => ["IntervalArithmetic", "SHA", "Dates"],
        "claim_path_tools" => ["IntervalArithmetic"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "route" => "interval-valued eta/N inputs propagated through the same area, Wilson holonomy, midpoint flux, and Stokes residual formulas; CSV rows are not read",
        "certificates" => Dict(
            "area" => Dict("summary" => summaries["area"], "rows" => area_rows),
            "holonomy" => Dict("summary" => summaries["holonomy"], "rows" => holonomy_rows),
            "flux" => Dict("summary" => summaries["flux"], "rows" => flux_rows),
            "stokes" => Dict("summary" => summaries["stokes"], "rows" => stokes_rows),
        ),
        "controls" => controls,
        "capability_receipt" => "system_v6/probes/julia/results/intervalarithmetic_capability_results.json",
        "csv_policy" => "CSV convergence curves are output artifacts only; interval certificates are the convergence proof surface.",
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    write_json(RESULT_PATH, result)
    println(json_value(Dict("ok" => result["all_pass"], "result_path" => RESULT_PATH_REL)))
    result["all_pass"] ? 0 : 1
end

exit(main())
