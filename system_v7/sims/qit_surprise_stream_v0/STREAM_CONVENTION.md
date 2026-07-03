# QIT Surprise Stream v0

Status: reference convention for feeding Codex Ratchet QIT surprise ticks to Lev.
Claim ceiling: transport convention only. This does not admit a QIT engine,
world model, bridge, Axis0 claim, or canonical sim result by itself.

## Tick Schema

Each stream segment is append-only JSONL. Each line is one canonical JSON object:

```json
{"tick":0,"t_iso":"2026-07-03T00:00:00Z","belief_bloch":[0.12,-0.08,0.96],"surprise_bits":0.0,"fe_gradient":0.0,"line_sha256":"...","stream_id":"qit_surprise_stream_v0.reference","schema":"cr.qit_surprise_tick.v1"}
```

Required fields:

- `schema`: exactly `cr.qit_surprise_tick.v1`.
- `stream_id`: stable stream identity for a run or producer.
- `tick`: zero-based non-negative integer, contiguous within a stream.
- `t_iso`: UTC ISO-8601 timestamp ending in `Z`.
- `belief_bloch`: three finite numbers `[x, y, z]`.
- `surprise_bits`: finite non-negative scalar. Non-finite readouts are invalid.
- `fe_gradient`: finite scalar free-energy-gradient readout.
- `line_sha256`: lowercase SHA-256 hex digest of the canonical JSON line with
  this field omitted.

Canonical line hashing uses `json.dumps(..., sort_keys=True, separators=(",", ":"))`
over the object without `line_sha256`, UTF-8 encoded. The emitted line itself is
the same canonical encoding after `line_sha256` is added, followed by `\n`.

## Segments

Segments rotate at 10,000 lines by default. Segment files live under:

```text
<stream_dir>/segments/segment_000000.jsonl
<stream_dir>/segments/segment_000001.jsonl
...
```

`segments_manifest.json` is updated after each fsynced tick and records:

- manifest schema: `cr.qit_surprise_segments_manifest.v1`;
- stream id and tick schema;
- segment line limit;
- next tick;
- for each segment: relative path, first tick, last tick, line count, and
  SHA-256 of the complete segment file bytes.

Segment files are append-only. Producers must not rewrite existing segment
bytes. A manifest rewrite is allowed because it is the reader discovery index,
not the event log.

## Durability

The reference emitter:

- opens segment files in append-binary mode;
- writes exactly one complete JSONL line per tick;
- flushes and `fsync`s the segment file after each line;
- refreshes `segments_manifest.json` with an atomic temp-file replace;
- `fsync`s the manifest file and containing directory after manifest updates.

## Reader Contract

Readers use either mode:

- Tail-follow the latest segment named in `segments_manifest.json`.
- Poll `segments_manifest.json`, verify each segment SHA-256, and then read any
  new complete lines.

Readers must fail closed on malformed JSON, non-contiguous ticks, duplicate
ticks, non-finite numeric fields, line-hash mismatch, segment-hash mismatch, or
manifest path traversal.

## Reference Emitter

`qit_surprise_stream_emitter.py` reimplements the minimal Lev bridge stream
shape without importing the Lev bundle. The loop emits a deterministic
Bloch-belief trajectory, a QIT-surprise scalar, and an FE-gradient scalar. It is
a transport fixture, not a scientific admission result.
