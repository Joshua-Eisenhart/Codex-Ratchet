#!/usr/bin/env julia

using CliffordAlgebras
using Dates
using Enzyme
using JSON
using SHA

const CANON_PATH = abspath(ENV["CANON_PATH"])
const OUTPUT_PATH = abspath(ENV["OUTPUT_PATH"])
const JULIA_EXECUTABLE = ENV["CORRECTION_JULIA_EXECUTABLE"]
const JULIA_PROJECT = abspath(ENV["CORRECTION_JULIA_PROJECT"])

Base.active_project() == joinpath(JULIA_PROJECT, "Project.toml") ||
    error("active Julia project does not match the correction project")

include(CANON_PATH)
using .ExceptionalAlgebraCanon

sha256_file(path::AbstractString) = bytes2hex(sha256(read(path)))
timestamp() = Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ")

const TOLERANCE = 1.0e-12

function albert_probe()
    # Reproduce the candidate's invalid scalar comparison, then evaluate the
    # actual component norm and a synthetic nonzero residual control.
    x = primitive_idempotent(1)
    y = primitive_idempotent(2)
    residual = jordan_identity_residual(x, y)
    candidate_error = ""
    candidate_failure = false
    try
        residual < 1.0e-10
    catch error
        candidate_failure = true
        candidate_error = sprint(showerror, error)
    end
    corrected_error = sqrt(
        sum(abs2, residual.diag) +
        sum(ExceptionalAlgebraCanon.norm2(value) for value in residual.off)
    )
    synthetic_residual = Albert(
        (1.0e-6, 0.0, 0.0),
        residual.off,
    )
    synthetic_error = sqrt(
        sum(abs2, synthetic_residual.diag) +
        sum(ExceptionalAlgebraCanon.norm2(value) for value in synthetic_residual.off)
    )
    Dict{String,Any}(
        "candidate_failure_reproduced" => candidate_failure,
        "observed" => Dict(
            "component_norm" => corrected_error,
            "candidate_error" => candidate_error,
            "fixture_scope" => "diagonal primitive-idempotent fixture; synthetic control perturbs one diagonal component only",
            "synthetic_component_norm" => synthetic_error,
        ),
        "tolerance" => TOLERANCE,
        "corrected_pass" => corrected_error < TOLERANCE,
        "must_fail_control_fired" => !(synthetic_error < TOLERANCE),
    )
end

function clifford_probe()
    # Reproduce one(::CliffordAlgebra), then compare the rotor square against
    # the multiplicative identity of the multivector value.
    clifford = CliffordAlgebra(3)
    gp = clifford.e1 * clifford.e2
    candidate_error = ""
    candidate_failure = false
    try
        one(clifford)
    catch error
        candidate_failure = true
        candidate_error = sprint(showerror, error)
    end
    Dict{String,Any}(
        "candidate_failure_reproduced" => candidate_failure,
        "observed" => Dict(
            "gp_squared" => sprint(show, gp * gp),
            "one_gp" => sprint(show, one(gp)),
            "e1_squared" => sprint(show, clifford.e1 * clifford.e1),
            "candidate_error" => candidate_error,
        ),
        "tolerance" => nothing,
        "corrected_pass" => (gp * gp) == -one(gp),
        "must_fail_control_fired" => !((clifford.e1 * clifford.e1) == -one(gp)),
    )
end

function enzyme_probe()
    # Reproduce the imported child exactly: no --project, JULIA_PROJECT unset,
    # and JULIA_LOAD_PATH=@:@stdlib. Then execute the derivative in the
    # explicitly bound v1.12 project.
    candidate_code = "using Enzyme; f(x)=sin(x)^2; autodiff(Reverse,f,Active,Active(0.3))"
    candidate_command = Cmd([
        JULIA_EXECUTABLE,
        "--startup-file=no",
        "-e",
        candidate_code,
    ])
    candidate_process = addenv(
        candidate_command,
        "JULIA_PROJECT" => nothing,
        "JULIA_LOAD_PATH" => "@:@stdlib",
    )
    candidate_stderr = IOBuffer()
    process = run(
        pipeline(candidate_process, stdout=devnull, stderr=candidate_stderr);
        wait=false,
    )
    wait(process)
    candidate_exit_code = process.exitcode
    candidate_error = String(take!(candidate_stderr))
    candidate_failure = candidate_exit_code != 0
    f(x) = sin(x)^2
    gradient = autodiff(Reverse, f, Active, Active(0.3))[1][1]
    analytic = 2 * sin(0.3) * cos(0.3)
    corrected_error = abs(gradient - analytic)
    shifted_error = abs(gradient - (analytic + 1.0e-3))
    Dict{String,Any}(
        "candidate_failure_reproduced" => candidate_failure,
        "observed" => Dict(
            "gradient_error" => corrected_error,
            "shifted_target_error" => shifted_error,
            "candidate_command" => collect(candidate_command.exec),
            "candidate_julia_project" => nothing,
            "candidate_julia_load_path" => "@:@stdlib",
            "candidate_reproduction_scope" => "exact imported child environment: no --project and JULIA_PROJECT unset",
            "candidate_exit_code" => candidate_exit_code,
            "candidate_error" => candidate_error,
        ),
        "tolerance" => TOLERANCE,
        "corrected_pass" => corrected_error < TOLERANCE,
        "must_fail_control_fired" => !(shifted_error < TOLERANCE),
    )
end

checks = Dict{String,Any}(
    "albert_component_norm" => albert_probe(),
    "clifford_rotor_identity" => clifford_probe(),
    "enzyme_reverse_gradient" => enzyme_probe(),
)
all_pass = all(
    check["candidate_failure_reproduced"] === true &&
    check["corrected_pass"] === true &&
    check["must_fail_control_fired"] === true
    for check in values(checks)
)

project_toml = joinpath(JULIA_PROJECT, "Project.toml")
manifest_toml = joinpath(JULIA_PROJECT, "Manifest.toml")
program = abspath(PROGRAM_FILE)
command = [
    JULIA_EXECUTABLE,
    "--startup-file=no",
    "--project=$(JULIA_PROJECT)",
    program,
]
receipt = Dict{String,Any}(
    "schema" => "codex-ratchet.julia-correction-probes.v1",
    "created_at" => timestamp(),
    "command" => command,
    "runtime" => Dict(
        "julia_executable" => JULIA_EXECUTABLE,
        "julia_version" => string(VERSION),
        "active_project" => Base.active_project(),
        "enzyme_path" => string(pathof(Enzyme)),
        "enzyme_version" => string(Base.pkgversion(Enzyme)),
    ),
    "project" => Dict(
        "project_toml_path" => project_toml,
        "project_toml_sha256" => sha256_file(project_toml),
        "manifest_toml_path" => manifest_toml,
        "manifest_toml_sha256" => sha256_file(manifest_toml),
    ),
    "sources" => Dict(
        "correction_script" => Dict(
            "path" => program,
            "sha256" => sha256_file(program),
        ),
        "archive_canon" => Dict(
            "path" => CANON_PATH,
            "sha256" => sha256_file(CANON_PATH),
        ),
    ),
    "checks" => checks,
    "all_pass" => all_pass,
    "claim_ceiling" => "Machine-local Julia API/environment correction probes only; no scientific admission or portable/canonical environment claim.",
    "promotion_allowed" => false,
)

mkpath(dirname(OUTPUT_PATH))
open(OUTPUT_PATH, "w") do io
    JSON.print(io, receipt, 2)
    write(io, '\n')
end
println(JSON.json(Dict("all_pass" => all_pass, "output" => OUTPUT_PATH)))
exit(all_pass ? 0 : 1)
