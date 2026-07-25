#!/bin/sh
# Measure every julia_witness stress case and print its EXACT exit code.
# Usage: sh claimgate_plugin/fixtures/stress2/run_julia_deck.sh
INTERP=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
REPO=/Users/joshuaeisenhart/Codex-Ratchet
W="$REPO/claimgate_plugin/julia_witness.py"
DECK="$REPO/claimgate_plugin/fixtures/stress2"

run() {   # run <label> <leg> <receipt>
  out=$("$INTERP" "$W" "$2" --receipt "$3" 2>&1)
  rc=$?
  echo "$1 MEASURED_EXIT=$rc :: $(printf '%s' "$out" | tr '\n' '|' | cut -c1-200)"
}

# --- honest pass path -------------------------------------------------------
run y2_honest_all_dependent      "$DECK/y2_honest_all_dependent/probe_julia.jl"   "$DECK/y2_honest_all_dependent/results/probe.json"
# --- honest, one observable mathematically independent of the only input -----
run y0_honest_trace_independent  "$DECK/y0_honest_input_contract/probe_julia.jl"  "$DECK/y0_honest_input_contract/results/probe.json"
# --- gaming attempts --------------------------------------------------------
run y1_input_laundered           "$DECK/y1_input_laundered_constant/probe_julia.jl" "$DECK/y1_input_laundered_constant/results/probe.json"
run y3_decorative_using_control  "$DECK/y3_decorative_using_control/probe_julia.jl" "$DECK/y3_decorative_using_control/results/probe.json"
run y4_token_dispatch_laundered  "$DECK/y4_token_dispatch_laundered/probe_julia.jl" "$DECK/y4_token_dispatch_laundered/results/probe.json"
run y10_predicted_perturbation   "$DECK/y10_predicted_perturbation/probe_julia.jl"  "$DECK/y10_predicted_perturbation/results/probe.json"
run y9_value_substitution        "$DECK/y2_honest_all_dependent/probe_julia.jl"    "$DECK/y2_honest_all_dependent/results/probe_value_substituted.json"
# --- receipt-side, against the HONEST leg -----------------------------------
run y5_dupkey_honest_leg         "$DECK/y2_honest_all_dependent/probe_julia.jl"   "$DECK/y2_honest_all_dependent/results/probe_dupkey.json"
run y6_out_of_denominator        "$DECK/y2_honest_all_dependent/probe_julia.jl"   "$DECK/y2_honest_all_dependent/results/probe_out_of_denominator.json"
# --- legacy honest leg, no input contract -----------------------------------
run y7_legacy_honest_no_contract "$REPO/claimgate_plugin/fixtures/bypass/j1_real_julia_leg/probe_julia.jl" "$REPO/claimgate_plugin/fixtures/bypass/j1_real_julia_leg/results/probe.json"

# --- y8: julia absent from PATH entirely. The interpreter is an absolute path,
# so stripping PATH removes only the engine.
out=$(env PATH=/nonexistent "$INTERP" "$W" \
      "$DECK/y2_honest_all_dependent/probe_julia.jl" \
      --receipt "$DECK/y2_honest_all_dependent/results/probe.json" 2>&1)
echo "y8_julia_absent MEASURED_EXIT=$? :: $(printf '%s' "$out" | tr '\n' '|' | cut -c1-200)"
