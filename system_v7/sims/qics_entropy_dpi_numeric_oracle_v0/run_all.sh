#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON=/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/qics-1.1.3-py311/bin/python
QICS_CHECKOUT=/Users/joshuaeisenhart/GitHub/qics

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$QICS_CHECKOUT"

"$PYTHON" -B "$HERE/validate_qics_entropy_dpi_numeric_oracle_v0.py" --self-test
"$PYTHON" -B "$HERE/qics_entropy_dpi_numeric_oracle_v0.py" --output "$HERE/result.json"
"$PYTHON" -B "$HERE/validate_qics_entropy_dpi_numeric_oracle_v0.py" "$HERE/result.json"
"$PYTHON" -B "$HERE/qics_entropy_dpi_numeric_oracle_v0.py" --output "$HERE/rerun_result.json"
"$PYTHON" -B "$HERE/validate_qics_entropy_dpi_numeric_oracle_v0.py" "$HERE/rerun_result.json" --compare "$HERE/result.json"

/usr/bin/shasum -a 256 "$HERE/result.json" "$HERE/rerun_result.json"
printf '%s\n' 'deterministic_rerun: PASS'
