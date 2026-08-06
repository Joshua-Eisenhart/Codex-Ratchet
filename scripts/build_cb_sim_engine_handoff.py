#!/usr/bin/env python3
"""Build a curated CB + simulation-engine stress-test handoff ZIP.

This is deliberately a source/evidence pack, not a runtime installer.  It
copies the contained ConstraintBox source, the bounded engine surfaces used by
the fresh runs, and source-addressed receipts into a deterministic archive.
External runtimes, caches, credentials, owner-tree results, and the rest of the
dirty Codex-Ratchet checkout are excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("/private/tmp/CB_SIM_ENGINE_STRESS_HANDOFF_20260803_v1.zip")
EXCLUDED_PARTS = {
    ".git",
    ".hypothesis",
    ".pytest_cache",
    ".DS_Store",
    ".AppleDouble",
    "__pycache__",
    "build",
    "dist",
    "constraintbox.egg-info",
    "receipts",
    "results",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_RESULT_NAMES = {
    "py_battery_results.json",
    "jl_battery_results.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def include(path: Path, source_root: Path) -> bool:
    rel = path.relative_to(source_root)
    return (
        path.is_file()
        and not any(part in EXCLUDED_PARTS for part in rel.parts)
        and path.suffix not in EXCLUDED_SUFFIXES
        and path.name not in EXCLUDED_RESULT_NAMES
    )


def copy_file(stage: Path, source: Path, destination: str, missing: list[str]) -> None:
    if not source.is_file():
        missing.append(str(source))
        return
    target = stage / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_tree(
    stage: Path,
    source: Path,
    destination: str,
    missing: list[str],
    *,
    exclude_result_files: bool = False,
) -> None:
    if not source.is_dir():
        missing.append(str(source))
        return
    for path in sorted(source.rglob("*")):
        if include(path, source) and not (
            exclude_result_files and "result" in path.stem.lower()
        ):
            target = stage / destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def write_text(stage: Path, relative: str, text: str) -> None:
    target = stage / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.rstrip() + "\n", encoding="utf-8")


def source_copy(stage: Path, missing: list[str]) -> None:
    # The complete CB source closure is filtered using the same exclusions as
    # its contained-core builder, so the LLM receives the actual controller,
    # adapters, fixtures, tests, and docs without caches or owner receipts.
    copy_tree(stage, ROOT / "constraint_box", "source/constraint_box", missing)
    copy_tree(stage, ROOT / "system_v8" / "engine_estate", "source/system_v8/engine_estate", missing)
    copy_tree(stage, ROOT / "system_v8" / "manifold" / "prototypes", "source/system_v8/manifold/prototypes", missing)
    copy_tree(
        stage,
        ROOT / "system_v5" / "ops" / "tooling" / "stress_battery",
        "source/system_v5/ops/tooling/stress_battery",
        missing,
        exclude_result_files=True,
    )

    files = [
        ("AGENTS.md", "context/AGENTS.md"),
        ("CODEX.md", "context/CODEX.md"),
        ("system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md", "context/INTEGRATION_INVENTORY_AND_CAMPAIGN.md"),
        ("system_v8/manifold/results/source_packets.json", "source/system_v8/manifold/results/source_packets.json"),
        ("system_v5/julia_carrier/Project.toml", "source/system_v5/julia_carrier/Project.toml"),
        ("system_v5/julia_carrier/Manifest.toml", "source/system_v5/julia_carrier/Manifest.toml"),
        ("system_v5/julia_carrier/paired_extension_nominalist_julia.jl", "source/system_v5/julia_carrier/paired_extension_nominalist_julia.jl"),
        ("system_v5/ops/formal_scouts/paired_extension_nominalist_jax.py", "source/system_v5/ops/formal_scouts/paired_extension_nominalist_jax.py"),
        ("system_v5/ops/formal_scouts/paired_extension_nominalist_pytorch.py", "source/system_v5/ops/formal_scouts/paired_extension_nominalist_pytorch.py"),
        ("scripts/codex_engine_stack_shakedown.py", "source/scripts/codex_engine_stack_shakedown.py"),
        ("scripts/codex_runtime_env_doctor.py", "source/scripts/codex_runtime_env_doctor.py"),
        ("scripts/audit_runtime_mapping_references.py", "source/scripts/audit_runtime_mapping_references.py"),
        ("scripts/validate_three_engine_sim_result.py", "source/scripts/validate_three_engine_sim_result.py"),
        ("system_v4/probes/runtime_hygiene_audit.py", "source/system_v4/probes/runtime_hygiene_audit.py"),
    ]
    for src, dst in files:
        copy_file(stage, ROOT / src, dst, missing)

    authority_docs = [
        "ENFORCEMENT_AND_PROCESS_RULES.md",
        "LLM_CONTROLLER_CONTRACT.md",
        "LEGO_SIM_CONTRACT.md",
        "RUNTIME_LIBRARY_LOCATION_MAP_20260608.md",
        "SIM_STACK_FULL_TARGET_SETS_20260609.md",
    ]
    for name in authority_docs:
        copy_file(stage, ROOT / "system_v5" / "docs" / name, f"context/system_v5_docs/{name}", missing)


def evidence_copy(stage: Path, missing: list[str]) -> dict[str, str]:
    evidence = {
        "cb_ijk/controller_receipt.json": "/private/tmp/cb_ijk_exploratory_parent.OLiS4U/run/receipt.json",
        "cb_ijk/prototype/RUN_RECEIPT.json": "/private/tmp/cb_ijk_exploratory_parent.OLiS4U/run/prototype/RUN_RECEIPT.json",
        "cb_ijk/prototype/RESULT.md": "/private/tmp/cb_ijk_exploratory_parent.OLiS4U/run/prototype/RESULT.md",
        "cb_ijk/prototype/engine_field.svg": "/private/tmp/cb_ijk_exploratory_parent.OLiS4U/run/prototype/engine_field.svg",
        "cb_paired_extension/controller_receipt.json": "/private/tmp/cb_paired_extension_run_parent.C9QCM9/run/receipt.json",
        "engine_estate/jax/receipt.json": "/private/tmp/engine_estate_jax.STKw6S/results/receipt.json",
        "engine_estate/torch/receipt.json": "/private/tmp/engine_estate_torch.PwVQry/results/receipt.json",
        "engine_estate/julia/receipt.json": "/private/tmp/engine_estate_julia.Gz5Iub/results/receipt.json",
        "engine_estate/integration/receipt.json": "/private/tmp/engine_estate_integration2.EVffO7/integration/receipt.json",
        "engine_estate/integration/handoff_torch.json": "/private/tmp/engine_estate_integration2.EVffO7/integration/handoff_torch.json",
        "engine_estate/integration/handoff_jax.json": "/private/tmp/engine_estate_integration2.EVffO7/integration/handoff_jax.json",
        "engine_estate/integration/handoff_julia.json": "/private/tmp/engine_estate_integration2.EVffO7/integration/handoff_julia.json",
        "stress/python_battery/results.json": "/private/tmp/py_battery.L2LwtL/py_battery_results.json",
        "stress/python_battery/stdout.txt": "/private/tmp/py_battery.L2LwtL/stdout.txt",
        "stress/julia_battery/results.json": "/private/tmp/jl_battery3.stJz2V/jl_battery_results.json",
        "stress/julia_battery/stdout.txt": "/private/tmp/jl_battery3.stJz2V/stdout.txt",
        "stress/cb_targeted_tests/stdout.txt": "/private/tmp/cb_targeted_tests.fDwppI/stdout.txt",
        "stress/cb_full_tests/postfix_stdout.txt": "/private/tmp/cb_full_tests_postfix.p6yaIn/stdout.txt",
        "stress/engine_stack_shakedown/result.json": "/private/tmp/codex_stack_shakedown.Mu8nCy/result.json",
        "stress/runtime_hygiene/result.json": "/private/tmp/runtime_hygiene_audit.Dl161C/result.json",
    }
    for relative, raw in evidence.items():
        copy_file(stage, Path(raw), f"evidence/{relative}", missing)
    return evidence


def generated_docs(stage: Path, evidence: dict[str, str], missing: list[str]) -> None:
    readme = """# ConstraintBox + simulation-engine stress handoff

Generated 2026-08-03 from the Codex-Ratchet working tree. This is a curated
source/evidence packet for another LLM. It is not a wheel, installer, or claim
that the model/CR has been validated.

## Fresh bounded results

| Surface | Fresh result | Ceiling |
|---|---:|---|
| CB full suite after repair | 929 passed, 336 subtests | one deprecation warning; no failures |
| CB repair regression surface | 49 passed, 35 subtests | targeted confirmation before the full rerun |
| Python function battery | 30/30 PASS | tool-operation diagnostic |
| Julia function battery | 14/15 PASS | Enzyme blocked: not in selected carrier/default environment |
| JAX estate | 22/22 PASS | working-sim estate, not canonical/proof |
| PyTorch estate | 13/13 PASS | working-sim estate, not canonical/proof |
| Julia estate | 7/7 PASS | isolated Julia depot; direct global-depot doctor still hits EPERM |
| Torch -> JAX -> Julia handoff | 10/10 PASS | chained numerical/GKSL diagnostic |
| CB paired whole-extension slice | 4/4 PASS | external engines, controller recheck, promotion false |
| CB IJK prototype adapter | EXECUTED; authored checks true | telemetry only; not CB kernel, CR truth, or validation |
| runtime hygiene | PASS | no blocker/advisory in isolated output path |
| engine-stack shakedown | 30 pass, 1 expected doctor fail, 1 intentional skip | Julia global cache permissions; DLPack bridge skipped by policy |

The full CB rerun initially exposed three stale/test-hygiene regressions; the
repair set is included in `source/constraint_box/tests` and the final full
receipt is in `evidence/stress/cb_full_tests`. The Julia estate used
`JULIA_DEPOT_PATH` with a temporary writable depot plus
the user's package depot. That corrected the host-cache write problem without
installing or changing packages. The Julia receipt records a known
`Attractors.extract_attractors` API mismatch; the load-bearing bistable basin
mapper still passed.

## Integration boundary

ConstraintBox is the deterministic controller/gate and receipt authority. The
JAX, Julia, PyTorch, IJK, and paired-extension workloads remain external
simulation operations. CB invokes selected sources, captures runtime/source/
result hashes, rechecks declared observations, and keeps `promotion_allowed`
and CR/scientific claims false. LLMs are proposal/advisory inputs only; no
model provider is hard-coded into this source packet.

The package contains no Java/TLC/Apalache requirement and performs no package
installation. The Enzyme gap is intentionally visible rather than converted
into a pass.

## How to read the packet

1. Start with `handoff/TOOL_ENGINE_MATRIX.md` and `handoff/RUN_COMMANDS.md`.
2. Inspect the source under `source/constraint_box` and the bounded engine
   surfaces under `source/system_v8` and `source/system_v5`.
3. Treat every JSON under `evidence/` as source-addressed local evidence with
   its original host paths preserved inside the receipt; do not infer a
   canonical or scientific result from a passing check.
4. `MANIFEST.json` hashes every payload file in this archive (excluding the
   manifest itself).
"""
    write_text(stage, "handoff/HANDOFF_README.md", readme)

    matrix = """# Tool and integration matrix

Status meanings: `PASS` means the declared operation ran and its local check
passed; `INTEGRATED` means a tool is load-bearing in the bounded operation;
`SUPPORTIVE` means it cross-checks or gates; `AVAILABLE/BLOCKED` is not an
integration claim.

| Tool/surface | Level in this handoff | Fresh evidence | Boundary |
|---|---|---|---|
| ConstraintBox core/controller | INTEGRATED | repaired 49-test surface; CB source | deterministic gate, not LLM authority |
| ClaimGate / Mini-Lev flow | INTEGRATED in CB source | contained-core tests and fixtures | no live Lev runtime claim |
| IJK manifold prototype | CB telemetry adapter; external operation | `evidence/cb_ijk` | execution/telemetry only; external-not-CB-kernel |
| Paired JAX/Julia/PyTorch extension | CB source invocation + shared fixture + controller recheck | `evidence/cb_paired_extension` | 4 entries pass; not CR validation |
| JAX | INTEGRATED workhorse | 22/22 estate; 10/10 handoff; Python battery | CPU/x64 local run |
| Julia/QuantumOptics | INTEGRATED authoritative lane | 7/7 estate; 10/10 handoff | writable isolated depot required |
| PyTorch/PyG | INTEGRATED graph lane | 13/13 estate; 10/10 handoff | CPU local run; torch_ga remains float32-only |
| Julia attractors/ITensors/Grassmann/Clifford | SUPPORTIVE/load-bearing probes | Julia estate sections | Attractors extractor API mismatch remains known |
| Quimb/Cotengra | SUPPORTIVE JAX estate lane | JAX receipt | quimb path runs; cotengra own executor known broken |
| Dynamiqs, Diffrax, OTT, NetKet, Lineax, JAXOpt, e3nn-JAX, Jraph | FUNCTION-TESTED / SUPPORTIVE | Python battery + JAX estate | not automatically promoted to CR arrows |
| Z3, CVC5, SymPy, Maude | GATE/PROOF SUPPORT | Python battery; CB formal tests | solver agreement is not independent semantics |
| SINDy, GUDHI, Rustworkx, XGI, scikit-learn, mpmath | SUPPORTIVE tool probes | Python battery | diagnostic/cross-check only |
| DLPack Torch↔JAX | FUNCTION-TESTED | Python battery | Julia DLPack bridge intentionally skipped in shakedown |
| Enzyme | BLOCKED | Julia battery 14/15 | package absent from selected carrier/default environment; no install authorized |
| Java/TLC/Apalache | OUT OF SCOPE | none | not required or invoked by this package |

No row above licenses manifold, CR, physics, convergence, attractor theorem,
or release claims. The strongest current statement is that these bounded
operations can be executed and gated with receipts on this host.
"""
    write_text(stage, "handoff/TOOL_ENGINE_MATRIX.md", matrix)

    commands = """# Reproduction commands

Commands below use the canonical local runtimes used for the fresh receipts.
They are bounded diagnostics; use fresh output directories and do not write
owner-tree results.

```sh
cd <repo-root>
SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
CB_PY=/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3
JULIA=/opt/homebrew/bin/julia

PYTHONPATH=constraint_box/src $SIM_PY -m pytest -q \
  constraint_box/tests/test_attractor_basin_adapter.py \
  constraint_box/tests/test_cli_wiring.py \
  constraint_box/tests/test_contained_core_bundle.py

CODEX_PY_BATTERY_RESULT_PATH=/tmp/py-battery.json \
  $SIM_PY system_v5/ops/tooling/stress_battery/py_battery.py

ENGINE_ESTATE_RESULTS_DIR=/tmp/jax-results \
  $SIM_PY system_v8/engine_estate/jax_estate_test.py
ENGINE_ESTATE_RESULTS_DIR=/tmp/torch-results \
  $CB_PY system_v8/engine_estate/torch_estate_test.py

RUN=$(mktemp -d)
mkdir -p "$RUN/depot" "$RUN/results" "$RUN/mpl" "$RUN/numba"
JULIA_DEPOT_PATH="$RUN/depot:$HOME/.julia" JULIA_LOAD_PATH='@:@stdlib' \
ENGINE_ESTATE_RESULTS_DIR="$RUN/results" MPLCONFIGDIR="$RUN/mpl" \
NUMBA_CACHE_DIR="$RUN/numba" \
  $JULIA --startup-file=no --project=system_v5/julia_carrier \
  system_v8/engine_estate/julia_estate_test.jl

RUN=$(mktemp -d)
mkdir -p "$RUN/integration" "$RUN/depot" "$RUN/mpl" "$RUN/numba"
JULIA_DEPOT_PATH="$RUN/depot:$HOME/.julia" JULIA_LOAD_PATH='@:@stdlib' \
ENGINE_ESTATE_INTEGRATION_DIR="$RUN/integration" MPLCONFIGDIR="$RUN/mpl" \
NUMBA_CACHE_DIR="$RUN/numba" \
  $SIM_P system_v8/engine_estate/integration_handoff_test.py

PARENT=$(mktemp -d); RUN="$PARENT/run"
PYTHONPATH=constraint_box/src $CB_PY -m constraintbox.cli exploratory-ijk \
  --run-dir "$RUN" --cr-root "$PWD" \
  --output "$RUN/receipt.json"
```

The full Python battery and Julia battery receipts in `evidence/` are the
authoritative fresh run records for this handoff. The Julia battery's Enzyme
failure is expected under the selected environment until an explicitly
authorized package/environment change is made.
"""
    write_text(stage, "handoff/RUN_COMMANDS.md", commands)


def write_manifest(stage: Path, evidence: dict[str, str], missing: list[str]) -> None:
    files = []
    for path in sorted(stage.rglob("*")):
        if path.is_file():
            files.append({
                "path": str(path.relative_to(stage)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    manifest = {
        "schema": "cb.sim-engine-stress-handoff.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "package_role": "curated source and bounded local evidence handoff",
        "promotion_allowed": False,
        "cr_truth_claim": False,
        "scientific_proof_claim": False,
        "source_root": str(ROOT),
        "file_count": len(files),
        "manifest_excludes_itself": True,
        "files": files,
        "evidence_original_paths": evidence,
        "missing_evidence": missing,
        "no_install_performed": True,
    }
    write_text(stage, "MANIFEST.json", json.dumps(manifest, indent=2, sort_keys=True))


def build(output: Path) -> Path:
    output = output.expanduser().absolute()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")
    stage = output.parent / output.stem
    if stage.exists():
        raise SystemExit(f"refusing to overwrite existing staging directory: {stage}")
    stage.mkdir(parents=True)
    missing: list[str] = []
    source_copy(stage, missing)
    evidence = evidence_copy(stage, missing)
    generated_docs(stage, evidence, missing)
    write_manifest(stage, evidence, missing)

    top = output.stem
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                archive.write(path, f"{top}/{path.relative_to(stage)}")
    print(f"staging: {stage}")
    print(f"zip: {output}")
    print(f"sha256: {sha256(output)}")
    print(f"files: {len([p for p in stage.rglob('*') if p.is_file()])}")
    if missing:
        print("missing_evidence:")
        for item in missing:
            print(f"  {item}")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
