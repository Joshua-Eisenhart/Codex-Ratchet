#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
DEEPTIME_PY=/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/deeptime-0.4.5-py313/bin/python

"$SIM_PY" "$HERE/build_contract_and_pydmd.py"
"$DEEPTIME_PY" "$HERE/run_deeptime_vamp.py"
"$SIM_PY" "$HERE/assemble_results.py"
"$SIM_PY" "$HERE/validate_stage_interior_spectral_kinetic_discriminator_v0.py"
