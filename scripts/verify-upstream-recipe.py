#!/usr/bin/env python3
"""Verify Duckgres's amd64 control-plane image benchmark plan."""

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)

def main() -> int:
    try:
        command = tomllib.loads((ROOT / ".boringcache.toml").read_text())["adapters"]["docker"]["command"]
        require(command[:7] == ["docker", "buildx", "build", "--file", "upstream/Dockerfile", "--platform", "linux/amd64"], "Docker plan changed")
        for fragment in ("VERSION=build-__SOURCE_SHA__", "COMMIT=__SOURCE_SHA__", "BUILD_TAGS=kubernetes", "duckgres-benchmark:local"):
            require(fragment in command, f"Docker plan changed: {fragment}")
        activation = (ROOT / "scripts/activate-docker-plan.py").read_text()
        require('"--push"' in activation and "__SOURCE_SHA__" in activation, "Docker plan activation changed")
        upstream = (ROOT / "upstream/.github/workflows/container-image-controlplane-cd.yml").read_text()
        for fragment in ("- platform: linux/arm64", "- platform: linux/amd64", "file: Dockerfile", "platforms: ${{ matrix.platform }}", "VERSION=build-${{ github.sha }}", "COMMIT=${{ github.sha }}", "BUILD_TAGS=kubernetes", "push: true"):
            require(fragment in upstream, f"upstream control-plane job changed: {fragment}")
        action = (ROOT / ".github/actions/duckgres-docker-benchmark/action.yml").read_text()
        for fragment in ("VERSION=build-${{ steps.scope.outputs.source_sha }}", "COMMIT=${{ steps.scope.outputs.source_sha }}", "BUILD_TAGS=kubernetes"):
            require(action.count(fragment) == 1, f"Actions/cache projection changed: {fragment}")
        require(action.count("Activate the BoringCache Docker plan") == 1, "BoringCache publication projection changed")
    except (KeyError, OSError, RuntimeError, tomllib.TOMLDecodeError) as error:
        print(f"Duckgres recipe mismatch: {error}", file=sys.stderr)
        return 1
    print("Verified Duckgres control-plane amd64 plan.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
