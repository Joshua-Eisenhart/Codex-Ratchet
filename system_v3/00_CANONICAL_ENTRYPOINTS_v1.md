# Canonical Entrypoints v1
Status: ACTIVE
Date: 2026-02-24

## Intent
Define the minimum canonical surfaces required to run, inspect, and save the system.

## Canonical Runtime Entrypoints
- Runner: `system_v3/runtime/bootpack_b_kernel_v1/a1_a0_b_sim_runner.py`
- ZIP validation: `system_v3/runtime/bootpack_b_kernel_v1/zip_protocol_v2_validator.py`
- ZIP writing: `system_v3/runtime/bootpack_b_kernel_v1/zip_protocol_v2_writer.py`
- Compiler: `system_v3/runtime/bootpack_b_kernel_v1/a0_compiler.py`

## Canonical State Surfaces
- Active runs root: `system_v3/runs/`
- Current run pointer: `system_v3/runs/_CURRENT_RUN.txt`
- Shared resume state: `system_v3/runs/_CURRENT_STATE/`
- Save export staging: `system_v3/runs/_save_exports/`
- A2 persistent brain: `system_v3/a2_state/`

## Canonical Specs Surface
- Working specs: `system_v3/specs/`
- Control-plane bundle work: `system_v3/control_plane_bundle_work/system_v3_control_plane/`

## Non-Canonical / Derived Surfaces
- `system_v3/a2_derived_indices_noncanonical/`
- `archive/` (retention only; never runtime source)

## Guard Scripts
- Sprawl guard: `system_v3/tools/sprawl_guard.py`
- Archive guard: `system_v3/tools/archive_guard.py`

## Save Profiles
- Builder: `system_v3/tools/build_save_profile_zip.py`
- Bootstrap save: includes `core_docs/` + `system_v3/` and excludes runs/archive artifacts.
- Debug save: bootstrap plus selected run IDs.
