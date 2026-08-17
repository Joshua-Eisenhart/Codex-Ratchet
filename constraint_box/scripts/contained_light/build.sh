#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
CB=$(CDPATH= cd -- "$HERE/../.." && pwd)
NAME=${NAME:-ConstraintBox_Contained_Light_2026-08-16}
STAGE=${STAGE:-/tmp/cb-contained-stage-$$}
DEST=${DEST:-/Users/joshuaeisenhart/Desktop/${NAME}.zip}

rm -rf "$STAGE"
ROOT="$STAGE/$NAME"
mkdir -p \
  "$ROOT/light/src/constraintbox" \
  "$ROOT/light/fixtures/cr" \
  "$ROOT/light/fixtures/distinguishability" \
  "$ROOT/light/fixtures/bound_observation" \
  "$ROOT/light/tests" \
  "$ROOT/light/mmm/packs" \
  "$ROOT/bin" \
  "$ROOT/scripts" \
  "$ROOT/receipts" \
  "$ROOT/STATE"

for mod in intake manifold_foundation constraints dualsolve distinguishability mmm_load_gate contained_light bound_quotient; do
  cp "$CB/src/constraintbox/${mod}.py" "$ROOT/light/src/constraintbox/${mod}.py"
done
cp "$HERE/slim_init.py" "$ROOT/light/src/constraintbox/__init__.py"

cp "$CB/fixtures/cr/manifold_time_first_seed_v1.json" "$ROOT/light/fixtures/cr/"
cp "$CB/fixtures/cr/manifold_time_first_seed_collapsed_v1.json" "$ROOT/light/fixtures/cr/"
cp "$CB/fixtures/distinguishability/"*.json "$ROOT/light/fixtures/distinguishability/"
cp "$CB/fixtures/bound_observation/"*.json "$ROOT/light/fixtures/bound_observation/"
cp "$CB/tests/test_manifold_foundation.py" "$ROOT/light/tests/"
cp "$CB/tests/test_distinguishability.py" "$ROOT/light/tests/"
cp "$CB/tests/test_mmm_load_gate.py" "$ROOT/light/tests/"
cp "$CB/tests/test_contained_light.py" "$ROOT/light/tests/"
cp "$CB/tests/test_bound_quotient.py" "$ROOT/light/tests/"
cp "$CB/mmm/packs/"*.md "$ROOT/light/mmm/packs/"

cp "$HERE/00_READ_THIS_FIRST.md" "$ROOT/00_READ_THIS_FIRST.md"
cp "$HERE/LIGHT_CONTRACT.md" "$ROOT/LIGHT_CONTRACT.md"
cp "$HERE/bin/cb" "$ROOT/bin/cb"
cp "$HERE/scripts/verify.sh" "$ROOT/scripts/verify.sh"
cp "$HERE/scripts/check_receipts.py" "$ROOT/scripts/check_receipts.py"
cp "$HERE/seed_check.py" "$ROOT/scripts/seed_check.py"
cp "$HERE/seed-check" "$ROOT/seed-check"
printf 'receipts are written here by bin/cb\n' > "$ROOT/receipts/README.txt"
chmod +x "$ROOT/bin/cb" "$ROOT/scripts/verify.sh" "$ROOT/seed-check"

git -C "$(dirname "$CB")" rev-parse HEAD > "$ROOT/STATE/GIT_HEAD.txt"
git -C "$(dirname "$CB")" rev-parse --abbrev-ref HEAD > "$ROOT/STATE/GIT_BRANCH.txt"
printf '%s\n' \
  "contained Light source overlay" \
  "not measured distinguishability" \
  "not Light-wheel admission" \
  "not Heavy" \
  > "$ROOT/STATE/CLAIM_CEILING.txt"

cat > "$ROOT/BUNDLE_METADATA.json" <<EOF
{
  "schema": "constraintbox.contained-light-bundle.v3",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source_head": "$(git -C "$(dirname "$CB")" rev-parse HEAD)",
  "bundle_kind": "contained_light_verbs",
  "verbs": ["seed-check", "seed", "feasibility", "surface", "quotient", "status", "verify"],
  "contained_light_wheel": false,
  "promotion_allowed": false,
  "lean_zip_considered": "/Users/joshuaeisenhart/Desktop/ConstraintBox_Lean_Clean_2026-08-16.zip",
  "claim_ceiling": "contained source overlay for seed-check + feasibility + bound quotient; solver-chosen obs are not measured distinguishability; not wheel admission; not Heavy"
}
EOF

(
  cd "$ROOT"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS
  find . -type f ! -name MANIFEST.txt ! -name SHA256SUMS | sort > MANIFEST.txt
)
rm -f "$DEST"
( cd "$STAGE" && zip -qry "$DEST" "$NAME" )
echo "DEST=$DEST"
ls -lh "$DEST"
echo "files=$(wc -l < "$ROOT/MANIFEST.txt" | tr -d ' ')"
