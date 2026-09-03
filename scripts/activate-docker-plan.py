#!/usr/bin/env python3
"""Resolve source and GitHub publication values in the committed Docker plan."""

import argparse
import json
import re
import tomllib
from pathlib import Path

PLAN = Path(__file__).resolve().parents[1] / ".boringcache.toml"


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise SystemExit(f"committed Duckgres plan no longer contains {old!r}")
    return source.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--push", choices=("true", "false"), required=True)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_sha):
        raise SystemExit("source SHA must be a full lowercase commit SHA")

    source = PLAN.read_text()
    source = replace_once(source, "VERSION=build-__SOURCE_SHA__", f"VERSION=build-{args.source_sha}")
    source = replace_once(source, "COMMIT=__SOURCE_SHA__", f"COMMIT={args.source_sha}")
    if args.push == "true":
        needle = '  "--tag", "duckgres-benchmark:local",\n  "upstream",'
        replacement = f'  "--tag", {json.dumps(args.image)},\n  "--push",\n  "upstream",'
        source = replace_once(source, needle, replacement)
    tomllib.loads(source)
    PLAN.write_text(source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
