# ConstraintBox End-to-End Run Report: Schema Embedding Test

## Task
Run ConstraintBox end-to-end on the codex_luna route with schema embedding changes applied to agentrun.py.

## Exact Commands Executed

### 1. Box Run (First-Box Preflight)
```bash
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 << 'PYEOF'
import sys
sys.path.insert(0, '/Users/joshuaeisenhart/.config/superpowers/worktrees/Codex-Ratchet/v9-stack-consolidation-20260806/constraint_box/src')
from constraintbox import cli
sys.argv = ['constraintbox', 'box', 
    '--request', '/private/tmp/claude-501/.../test_request.json',
    '--run-dir', '/private/tmp/claude-501/.../box_run']
cli.main()
PYEOF
```

**Box Run Disposition:** `READY_FOR_UNTRUSTED_PROPOSAL`
**Box Run Reason:** `request_and_external_function_packet_passed`

### 2. Agent Run (Proposal Loop)
```bash
export CONSTRAINTBOX_PROPOSAL_PROVIDER=codex_luna
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 << 'PYEOF'
import sys, os
sys.path.insert(0, '.../constraint_box/src')
os.environ['CONSTRAINTBOX_PROPOSAL_PROVIDER'] = 'codex_luna'
from constraintbox import cli
sys.argv = ['constraintbox', 'run',
    '--box-run-dir', '/private/tmp/claude-501/.../box_run',
    '--run-dir', '/private/tmp/claude-501/.../agent_run']
cli.main()
PYEOF
```

**Agent Run Disposition:** `PARKED`
**Agent Run Reason:** `the bounded Mini-Lev proposal flow parked`

## Final Status Summary

| Metric | Value |
|--------|-------|
| codex CLI availability | YES - `/usr/local/bin/codex` (v0.147.0) |
| gpt-5.6-luna model validity | REGISTERED in route table (codex_luna route) |
| Box run completion | YES - READY_FOR_UNTRUSTED_PROPOSAL |
| Agent run execution | YES - executed, attempted to run luna |
| Attempts made | 1 of 2 maximum |
| Attempt 1 result | PARKED - PROVIDER_BOUNDARY_ERROR |
| Schema embedded in prompt | YES - confirmed in prompt.txt |
| Prompt template version | v2_schema_embedded - recorded in flow_binding |

## Schema Embedding Verification

### Evidence of Schema Embedding

1. **Prompt Contains Schema Block**
   - File: `/private/tmp/claude-501/.../agent_run/attempt-1/prompt.txt`
   - Contains: `[PROPOSAL OUTPUT SCHEMA sha256=36ad9944cf0f0d0bc19d4f679c368065d87df7589e39d97e6f7156066cde43e0]`
   - Full JSON schema follows, embedded directly in prompt text

2. **Flow Binding Records Schema SHA256**
   - File: `/private/tmp/claude-501/.../agent_run/proposal_flow_binding.json`
   - Field: `"proposal_schema_sha256": "36ad9944cf0f0d0bc19d4f679c368065d87df7589e39d97e6f7156066cde43e0"`
   - Field: `"prompt_template_version": "v2_schema_embedded"`

### Prompt Template Verification
The prompt text shows the new instruction:
```
Return only the JSON object matching the [PROPOSAL OUTPUT SCHEMA] block below.
```

Previously (without embedding): 
```
Return only the JSON object required by the supplied output schema.
```

## Per-Attempt Outcome

### Attempt 1: PARKED

**Disposition:** PARKED  
**Reason Codes:** ["PROVIDER_BOUNDARY_ERROR"]  
**Provider:** codex_luna (gpt-5.6-luna)

**Error Details**
- File: `/private/tmp/claude-501/.../agent_run/attempt-1/provider_boundary_error.json`
- Error: `"no provider-key location: set CONSTRAINTBOX_RUNTIME_DIR, CONSTRAINTBOX_PROVIDER_KEY_FILE, or CONSTRAINTBOX_PROVIDER_HMAC_KEY"`
- Exception Type: RuntimeError

**Root Cause:** Provider harness configuration missing. The provider interface attempted to initialize the notary/key system but no environment configuration was provided. This occurred AFTER the prompt was successfully built with the embedded schema.

**What Did NOT Fail:** Schema embedding, prompt construction, flow binding creation.

**What Failed:** Provider runtime initialization (credential/key setup), before luna was invoked.

## Receipt Paths

- **Box Run Receipt:** `/private/tmp/claude-501/-Users-joshuaeisenhart-Codex-Ratchet/b1e33759-f392-47e0-8f05-c6ce7250426c/scratchpad/box_run/box_receipt.json`
- **Agent Run Receipt:** `/private/tmp/claude-501/-Users-joshuaeisenhart-Codex-Ratchet/b1e33759-f392-47e0-8f05-c6ce7250426c/scratchpad/agent_run/run_receipt.json`
- **Flow Binding:** `/private/tmp/claude-501/-Users-joshuaeisenhart-Codex-Ratchet/b1e33759-f392-47e0-8f05-c6ce7250426c/scratchpad/agent_run/proposal_flow_binding.json`
- **Attempt 1 Prompt:** `/private/tmp/claude-501/-Users-joshuaeisenhart-Codex-Ratchet/b1e33759-f392-47e0-8f05-c6ce7250426c/scratchpad/agent_run/attempt-1/prompt.txt`
- **Attempt 1 Error:** `/private/tmp/claude-501/-Users-joshuaeisenhart-Codex-Ratchet/b1e33759-f392-47e0-8f05-c6ce7250426c/scratchpad/agent_run/attempt-1/provider_boundary_error.json`

## Honest Reading (Status Ladder)

**Status: `runs`**

The change under test (schema embedding in prompt) successfully executed. The prompt was built with the schema embedded, the flow binding was created with the schema SHA256 recorded, and the attempt directory shows the schema was present in the prompt file. However, luna itself did not execute because the provider harness failed at initialization due to missing key configuration. This is a legitimate outcome: the schema embedding mechanism works as designed, but the provider boundary was never reached.

The run is `runs` (executes without error), not `passes local rerun` (which would require luna to actually respond and pass the shape check), and not higher (which would require the proposal to survive the deterministic gates).
