# ratchet_stress_harness

Deterministic stress harness for ZIP-driven replay tests.

## Run
```bash
python3 tests/ratchet_stress_harness/harness_runner.py \
  --vectors-dir tests/ratchet_stress_harness/test_vectors \
  --out tests/ratchet_stress_harness/replay_logs/harness_report.json
```

## Vector format
Each `test_vectors/*.json` file:
```json
{
  "test_id": "STRING",
  "zip_sequence": ["/absolute/path/to/zip1.zip", "/absolute/path/to/zip2.zip"],
  "initial_state_hex": "",
  "compiler_version": "A0_COMPILER_v1",
  "expected": {
    "expected_final_state_hash": "OPTIONAL_HEX64",
    "expected_last_outcome": "OPTIONAL_OK_PARK_REJECT",
    "must_contain_tags": ["OPTIONAL_REJECT_TAG"]
  }
}
```
