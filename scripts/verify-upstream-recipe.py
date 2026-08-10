#!/usr/bin/env python3
"""Verify Duckgres's amd64 control-plane image benchmark plan."""

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SCRIPT = "source_sha=$(git -C upstream rev-parse HEAD); exec docker buildx build --file upstream/Dockerfile --platform linux/amd64 --build-arg VERSION=build-${source_sha} --build-arg COMMIT=${source_sha} --build-arg BUILD_TAGS=kubernetes --tag duckgres-benchmark:local upstream"

def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)

def main() -> int:
    try:
        command = tomllib.loads((ROOT / ".boringcache.toml").read_text())["adapters"]["docker"]["command"]
        require(command == ["bash", "-euo", "pipefail", "-c", EXPECTED_SCRIPT], "Docker plan changed")
        upstream = (ROOT / "upstream/.github/workflows/container-image-controlplane-cd.yml").read_text()
        for fragment in ("- platform: linux/arm64", "- platform: linux/amd64", "file: Dockerfile", "platforms: ${{ matrix.platform }}", "VERSION=build-${{ github.sha }}", "COMMIT=${{ github.sha }}", "BUILD_TAGS=kubernetes", "push: true"):
            require(fragment in upstream, f"upstream control-plane job changed: {fragment}")
        action = (ROOT / ".github/actions/duckgres-docker-benchmark/action.yml").read_text()
        for fragment in ("VERSION=build-${{ steps.scope.outputs.source_sha }}", "COMMIT=${{ steps.scope.outputs.source_sha }}", "BUILD_TAGS=kubernetes"):
            require(action.count(fragment) == 3, f"provider projection changed: {fragment}")
    except (KeyError, OSError, RuntimeError, tomllib.TOMLDecodeError) as error:
        print(f"Duckgres recipe mismatch: {error}", file=sys.stderr)
        return 1
    print("Verified Duckgres control-plane amd64 plan.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
