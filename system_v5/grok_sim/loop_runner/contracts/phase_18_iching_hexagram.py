"""phase_18_iching_hexagram.py — 64 engine stages naturally map to 64 I-Ching hexagrams.

The architecture has 64 total stages (32 per engine × 2 engines). Each stage has these
natural binary attributes:
  - engine_id (A=0, B=1) — 1 bit
  - direction (fwd=0, rev=1) — 1 bit
  - loop (f=0, b=1) — 1 bit
  - sheet (L=0, R=1) — 1 bit
  - terrain (Ti=00, Te=01, Fi=10, Fe=11) — 2 bits

Total: 6 bits → exactly 64 unique combinations = the I-Ching's 64 hexagram space.

This is "I-Ching emergence": the 6-bit structure isn't IMPOSED on the architecture; it
FALLS OUT of the engine enumeration's own attributes. Each engine stage IS a hexagram
under this mapping.

Required API: `stage_to_hexagram(stage_index: int, engine: str = "A") -> dict`
  Input: stage 0..31, engine "A" or "B"
  Returns:
    {
      "hexagram_bits": list[6] of int (0/1),
      "hexagram_index": int 0..63,
      "trigram_lower": list[3] of int,    # bottom 3 bits
      "trigram_upper": list[3] of int,    # top 3 bits
      "engine": str,
      "stage_index": int,
    }
"""
import collections


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "stage_to_hexagram"):
        return {
            "pass": False,
            "failures": [{
                "check": "stage_to_hexagram_exists",
                "msg": "Required function `stage_to_hexagram(stage_index: int, engine: str) -> dict` is "
                       "not exported. The 64 engine stages (32 × 2 engines) naturally decompose into "
                       "6 binary attributes (engine, direction, loop, sheet, terrain×2), mapping to the "
                       "I-Ching's 64-hexagram space. Expose this mapping.",
            }],
            "metrics": metrics,
        }

    # Build all 64 hexagrams
    hexagrams = {}
    indices_seen = []
    for engine in ("A", "B"):
        for stage in range(32):
            try:
                r = candidate.stage_to_hexagram(stage, engine)
            except Exception as e:
                failures.append({
                    "check": f"stage_to_hexagram_call_{engine}_{stage}",
                    "msg": f"stage_to_hexagram({stage}, '{engine}') raised {type(e).__name__}: {str(e)[:200]}",
                })
                continue
            if not isinstance(r, dict):
                failures.append({"check": f"hexagram_returns_dict_{engine}_{stage}",
                                 "msg": f"returned {type(r).__name__}"})
                continue
            for k in ("hexagram_bits", "hexagram_index", "trigram_lower", "trigram_upper"):
                if k not in r:
                    failures.append({"check": f"hexagram_missing_{k}_{engine}_{stage}",
                                     "msg": f"missing `{k}`"})
                    break
            else:
                hexagrams[(engine, stage)] = r
                indices_seen.append(int(r["hexagram_index"]))

    if not hexagrams:
        return {"pass": False, "failures": failures, "metrics": metrics}

    metrics["hexagrams_returned"] = len(hexagrams)

    # Verify 6-bit structure: each hexagram_bits is a 6-long list of 0/1
    for (engine, stage), r in list(hexagrams.items())[:5]:
        bits = r["hexagram_bits"]
        if not isinstance(bits, (list, tuple)) or len(bits) != 6:
            failures.append({
                "check": f"hexagram_bits_shape_{engine}_{stage}",
                "msg": f"hexagram_bits = {bits}, expected list of length 6",
            })
        elif not all(b in (0, 1) for b in bits):
            failures.append({
                "check": f"hexagram_bits_binary_{engine}_{stage}",
                "msg": f"hexagram_bits = {bits}, must contain only 0 and 1",
            })
        else:
            # Verify bit decomposition equals hexagram_index (interpret bits as a binary number)
            recomputed_idx = sum(b * (1 << i) for i, b in enumerate(bits))
            if recomputed_idx != int(r["hexagram_index"]):
                # Maybe they encode big-endian — try the other way
                recomputed_idx_be = sum(b * (1 << (5 - i)) for i, b in enumerate(bits))
                if recomputed_idx_be != int(r["hexagram_index"]):
                    failures.append({
                        "check": f"hexagram_bits_index_consistent_{engine}_{stage}",
                        "msg": f"bits {bits} don't encode hexagram_index {r['hexagram_index']} "
                               f"in either endianness (LE={recomputed_idx}, BE={recomputed_idx_be})",
                    })

    # 64 unique indices, full coverage of [0, 64)
    unique_indices = set(indices_seen)
    metrics["unique_hexagram_count"] = len(unique_indices)
    if len(unique_indices) != 64:
        failures.append({
            "check": "hexagram_unique_count",
            "msg": f"got {len(unique_indices)} unique hexagram indices, expected 64. "
                   f"The 64 engine stages should map BIJECTIVELY to 64 hexagrams.",
        })

    if unique_indices and (max(unique_indices) > 63 or min(unique_indices) < 0):
        failures.append({
            "check": "hexagram_index_range",
            "msg": f"hexagram indices range [{min(unique_indices)}, {max(unique_indices)}], "
                   f"expected [0, 63]",
        })

    # Coverage: all 64 indices appear
    missing = set(range(64)) - unique_indices
    if missing:
        failures.append({
            "check": "hexagram_full_coverage",
            "msg": f"missing hexagram indices: {sorted(missing)[:5]}{'...' if len(missing) > 5 else ''}. "
                   f"Bijection requires all 64 hexagrams present.",
        })

    # Bit balance: each of 6 bit positions should have exactly 32 zeros and 32 ones
    # (each binary attribute splits 64 stages exactly in half)
    bit_sums = [0, 0, 0, 0, 0, 0]
    for (_, _), r in hexagrams.items():
        for i, b in enumerate(r["hexagram_bits"][:6]):
            bit_sums[i] += int(b)
    metrics["bit_position_sums"] = bit_sums
    for i, s in enumerate(bit_sums):
        if s != 32:
            failures.append({
                "check": f"hexagram_bit_balance_position_{i}",
                "msg": f"bit position {i} has sum {s} (count of 1s), expected 32 out of 64. "
                       f"Each binary attribute should split exactly in half.",
            })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "stage_to_hexagram returns same hexagram for all stages — fails unique_count",
            "stage_to_hexagram returns only odd indices — fails full coverage",
            "bit balance off (e.g., one bit is always 1) — fails bit_balance",
            "bits don't match hexagram_index — fails consistency check",
        ],
        "baseline_variants": [
            "trivial constant baseline: all hexagrams = 0 — fails unique count",
            "random hexagram baseline: probably non-bijective, fails coverage",
        ],
    }
