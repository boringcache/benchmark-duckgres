# benchmark-duckgres

Isolated Duckgres benchmark runner for BoringCache vs GitHub Actions cache.

Duckgres is the first PostHog satellite benchmark because its current CD
topology makes the cache cost visible: the main, control-plane, and worker
workflows can run eight `type=gha,mode=max` exports for one commit. Public run
[`30048412994`](https://github.com/PostHog/duckgres/actions/runs/30048412994)
spent 215.2 seconds preparing
and sending the amd64 cache after the image had already been exported; the
parallel arm64 export took 123.5 seconds.

This is recurring rather than a one-off. In the 30 days ending 2026-07-24,
each of the main, control-plane, and worker container workflows recorded 173
runs, or about 5.8 source pushes per day. Their full matrices can produce
eight image builds per push: two main, two control-plane, and four worker
builds. That is up to 1,384 `mode=max` exports in the observed window. The
Actions cache API reported 12.69 GB across 180 active entries at inspection
time.

This repo exists separately from the central benchmarks publisher so Duckgres can have:

- a pinned upstream source commit
- isolated GitHub Actions cache usage
- one per-repo BoringCache workspace name: `boringcache/benchmark-duckgres`
- independent benchmark runs triggered by upstream sync commits and manual dispatches

## Source Model

- upstream app source lives in the pinned `upstream/` submodule
- workflows build the upstream Dockerfile with `upstream/` as the Docker context
- builds use the same `BUILD_TAGS=kubernetes` argument as Duckgres CD
- the initial comparison targets `linux/amd64`; architecture matrices belong in
  a follow-up only after the single-platform cache path is proven

Pinned upstream source:

- see committed `upstream/` submodule on `main`

## Scenarios

- `cold`
- `warm1`

Fresh lane runs a no-prior-cache cold build plus one warm rerun on the same pinned source tree. Rolling lane records the upstream commit build as-is after each upstream sync against the prior rolling cache and skips `warm1`.

BoringCache compares the explicit registry/OCI cache path and the managed
BuildKit backend path. It does not call BoringCache inside Dockerfile `RUN`
steps, and upstream Dockerfile cache mounts stay native to BuildKit. Docker
tool-cache lanes are intentionally absent until Duckgres has a static supported
adapter for its in-Docker Go build cache shape.

The ECR comparison is optional and stays skipped until the benchmark repo has
the existing Docker benchmark ECR variables. The required proof is GHA versus
BoringCache; ECR is useful context, not a prerequisite.

## Output

Each workflow uploads machine-readable JSON and Markdown summaries. Those artifacts are intended to be ingested by the central `boringcache/benchmarks` publisher later.

## Token Model

This repo uses split BoringCache tokens as the standard CI shape:

- `BORINGCACHE_RESTORE_TOKEN` for read-only restore and proxy access
- `BORINGCACHE_SAVE_TOKEN` for trusted write paths
- `BORINGCACHE_API_TOKEN` only where a single bearer variable is still required for compatibility
