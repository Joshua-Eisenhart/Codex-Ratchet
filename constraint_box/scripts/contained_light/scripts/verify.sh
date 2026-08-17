#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
if [ -z "${CB_PYTHON:-}" ]; then
  echo "REFUSE: set CB_PYTHON" >&2
  exit 2
fi
export PYTHONPATH="$ROOT/light/src"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
OUT="$ROOT/receipts"
mkdir -p "$OUT"

echo "== seed-check (stdlib python3) =="
python3 "$ROOT/scripts/seed_check.py" --root "$ROOT" --out "$OUT/SEED_CHECK.json"

echo "== seed =="
"$CB_PYTHON" -m constraintbox.contained_light --root "$ROOT" seed \
  --out "$OUT/seed.json"

echo "== collapsed order must refuse =="
set +e
"$CB_PYTHON" -m constraintbox.contained_light --root "$ROOT" seed \
  "$ROOT/light/fixtures/cr/manifold_time_first_seed_collapsed_v1.json" \
  --out "$OUT/seed_collapsed.json"
collapsed=$?
set -e
if [ "$collapsed" -eq 0 ]; then
  echo "collapsed seed unexpectedly passed" >&2
  exit 3
fi

echo "== feasibility =="
"$CB_PYTHON" -m constraintbox.contained_light --root "$ROOT" feasibility \
  --out "$OUT/feasibility.json"

echo "== quotient =="
"$CB_PYTHON" -m constraintbox.contained_light --root "$ROOT" quotient \
  --out "$OUT/quotient.json"

echo "== unbound quotient must hold =="
set +e
"$CB_PYTHON" -m constraintbox.contained_light --root "$ROOT" quotient \
  "$ROOT/light/fixtures/bound_observation/bound_unbound.json" \
  --out "$OUT/quotient_unbound.json"
unbound=$?
set -e
if [ "$unbound" -eq 0 ]; then
  echo "unbound quotient unexpectedly passed" >&2
  exit 4
fi

echo "== surface =="
"$CB_PYTHON" -m constraintbox.contained_light --root "$ROOT" surface \
  --out "$OUT/surface.json"

echo "== status =="
"$CB_PYTHON" -m constraintbox.contained_light --root "$ROOT" status \
  --out "$OUT/status.json"

echo "== tests =="
"$CB_PYTHON" -m pytest -q -p no:cacheprovider \
  "$ROOT/light/tests/test_manifold_foundation.py" \
  "$ROOT/light/tests/test_distinguishability.py" \
  "$ROOT/light/tests/test_mmm_load_gate.py" \
  "$ROOT/light/tests/test_contained_light.py" \
  "$ROOT/light/tests/test_bound_quotient.py"

echo "== python -I (expected fail) =="
set +e
"$CB_PYTHON" -I -c "import constraintbox.manifold_foundation"
iso=$?
set -e
echo "isolated_import_exit:$iso"
if [ "$iso" -eq 0 ]; then
  echo "contained wheel unexpectedly imported the overlay" >&2
  exit 5
fi

"$CB_PYTHON" "$ROOT/scripts/check_receipts.py" "$OUT"
