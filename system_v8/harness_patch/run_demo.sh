#!/usr/bin/env bash
# End-to-end demo: ticket -> route seal -> admission seal -> flip battery -> Lev bridge.
# Writes ONLY inside ./results. Never writes into ~/lev-main.
set -u
cd "$(dirname "$0")"
PY="${SIM_PY:-/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3}"
R=results; mkdir -p "$R/fixtures"; : > "$R/events.jsonl"; rm -f "$R/run_ticket.json"
line() { printf '\n─── %s ───\n' "$1"; }

line "1. task_start: mint run ticket (nonce minted by broker, not the worker)"
"$PY" harness_gate.py mint --claim "engine loop order is load-bearing" \
  --ceiling "tool_lego_fit_probe" --tools "Bash,Write" --roots "$(cd ../.. && pwd)"

line "2. pre_tool_use: route seal"
for spec in "Write|$(cd ../.. && pwd)/system_v8/x.json" \
            "Write|$HOME/lev-main/plugins/x.ts" \
            "Write|$(cd ../.. && pwd)/../lev-main/core/y.ts" \
            "WebFetch|"; do
  t="${spec%%|*}"; p="${spec#*|}"
  out=$("$PY" harness_gate.py pre --tool "$t" --path "$p"); rc=$?
  printf '  %-9s %-52s -> %s (exit %d)\n' "$t" "${p:0:52}" \
    "$(echo "$out" | "$PY" -c 'import json,sys;print(json.load(sys.stdin)["verdict"])')" "$rc"
done

line "3. post_tool_use: admission seal vs hostile intake"
printf '{"classification":"probe","all_pass":false,"all_pass":true}' > "$R/fixtures/dupkey.json"
printf '{"classification":"probe","metric":NaN}'                     > "$R/fixtures/nan.json"
printf '{"classification":"probe","promotion_allowed":true}'         > "$R/fixtures/selfverdict.json"
printf '{"classification":"tool_lego_fit_probe","claim_ceiling":"probe only","dS":0.164}' > "$R/fixtures/clean.json"
for f in dupkey nan selfverdict clean absent; do
  out=$("$PY" harness_gate.py post --receipt "$R/fixtures/$f.json" 2>/dev/null); rc=$?
  v=$(echo "$out" | "$PY" -c 'import json,sys
try: print(json.load(sys.stdin)["verdict"])
except Exception: print("BLOCKED")' 2>/dev/null)
  printf '  %-12s -> %-24s (exit %d)\n' "$f" "$v" "$rc"
done

line "4. anti-theatre battery: z3 x JAX, zero LLM tokens"
"$PY" flip_harness.py > "$R/flip_stdout.json" 2>&1; rc=$?
"$PY" - <<'PY'
import json
d = json.load(open("results/flip_harness_v0.json"))
for r in d["results"]:
    t2 = r["test_2_perturb"]
    print(f'  {r["label"]:42s} flip_rate={t2["flip_rate"]:<5} '
          f'erase_flips={str(r["test_1_erase"]["passes"]):5s} -> {r["verdict"]}')
print(f'  battery_discriminates = {d["battery_discriminates"]}   '
      f'llm_tokens_spent = {d["llm_tokens_spent"]}')
PY

line "5. Lev bridge (read-only on lev-main): dispatch events + receipt"
if command -v lev >/dev/null 2>&1; then
  lev triggers dispatch "$(pwd)/$R/events.jsonl" --receipt "$(pwd)/$R/fixtures/clean.json" \
      --exec-dry-run --json 2>/dev/null \
    | "$PY" -c 'import json,sys
d=json.load(sys.stdin)
print("  schema  :", d["result"]["data"]["schema"])
print("  policy  :", d["policy"]["decision"])
print("  effect  :", d["side_effect"]["class"])
print("  status  :", d["result"]["status"])' 2>/dev/null || echo "  (lev dispatch returned non-JSON)"
else
  echo "  lev not on PATH — skipped, NOT passed"
fi

line "ceiling"
echo "  E2_SUPERVISED_EXECUTION. Admission control, NOT bypass prevention."
echo "  ~/lev-main untouched. promotion_allowed=false."
