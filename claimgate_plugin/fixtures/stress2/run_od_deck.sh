#!/bin/sh
# Measure every output_dependence stress case and print its EXACT exit code.
# Usage: sh claimgate_plugin/fixtures/stress2/run_od_deck.sh
INTERP=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
REPO=/Users/joshuaeisenhart/Codex-Ratchet
DECK="$REPO/claimgate_plugin/fixtures/stress2"
for c in x1_value_substitution x2_env_leak x3_probe_reconstructs_perturbation \
         x4_crash_refuting_pass_single x5_decoy_control \
         x6_honest_invariant_observable x7_honest_operator_ops; do
  out=$("$INTERP" "$REPO/claimgate_plugin/output_dependence.py" \
        "$DECK/$c/results/probe.json" \
        --json "$DECK/$c/results/od_report.json" 2>&1)
  rc=$?
  v=$(printf '%s' "$out" | sed -n 's/.*"verdict": "\([A-Z_]*\)".*/\1/p' | head -1)
  echo "$c MEASURED_EXIT=$rc verdict=$v"
done

# x8: honest engines_ran block, fabrications parked outside it. output_dependence
# takes EVERY numeric leaf of the receipt, so the extra numbers are UNBOUND, which
# blocks. This is the case julia_witness passes (y6).
out=$("$INTERP" "$REPO/claimgate_plugin/output_dependence.py" \
      "$DECK/x1_value_substitution/results/probe_out_of_denominator.json" \
      --leg "$DECK/x1_value_substitution/probe_jax.py" \
      --json "$DECK/x1_value_substitution/results/od_report_out_of_denominator.json" 2>&1)
rc=$?
v=$(printf '%s' "$out" | sed -n 's/.*"verdict": "\([A-Z_]*\)".*/\1/p' | head -1)
echo "x8_out_of_denominator MEASURED_EXIT=$rc verdict=$v"
