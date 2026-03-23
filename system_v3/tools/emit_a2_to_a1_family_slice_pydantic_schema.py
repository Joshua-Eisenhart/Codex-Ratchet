#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from a2_to_a1_family_slice_models import A2ToA1FamilySlice


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Emit the current Pydantic JSON schema for A2_TO_A1_FAMILY_SLICE_v1.")
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    out_json = Path(args.out_json)
    if not out_json.is_absolute():
        raise SystemExit("non_absolute_out_json")

    schema = A2ToA1FamilySlice.model_json_schema(by_alias=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "schema": "A2_TO_A1_FAMILY_SLICE_PYDANTIC_SCHEMA_EMIT_v1",
                "out_json": str(out_json),
                "title": schema.get("title", ""),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
