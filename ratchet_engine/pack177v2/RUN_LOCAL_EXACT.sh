#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

python3 -B source/source_balanced_completion_ratchet.py --self-test
python3 -B source/source_balanced_completion_ratchet.py --run
python3 -B source/source_balanced_completion_ratchet.py --validate
python3 -B source/compile_fuel_obligations.py --self-test
python3 -B source/compile_fuel_obligations.py --run
python3 -B source/compile_fuel_obligations.py --validate
python3 -B source/build_lev_context_graph.py
python3 -B solver/generate_cvc5_instances.py
