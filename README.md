# benchmark-duckgres

Isolated Duckgres benchmark runner for BoringCache vs GitHub Actions cache.

Stable BoringCache workflows install the verified CLI `v1.15.0` release;
canary dispatches must use an exact immutable CLI tag.

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

## Rolling Proof Series

The benchmark replays these three linear `main` commits oldest to newest.
Each commit has a successful upstream `Container Image CD` run, so this is
real image-building history rather than an arbitrary three-commit sample:

| Commit | Upstream proof |
| --- | --- |
| `95050973c56b7876488a209bfa7c328cec71fe83` | [run 30022289969](https://github.com/PostHog/duckgres/actions/runs/30022289969) |
| `d94730966803998856c3ef9fc66c2d1720d5a739` | [run 30048412994](https://github.com/PostHog/duckgres/actions/runs/30048412994) |
| `b9823d4336b244857185888952f4a3086cceda3a` | [run 30085493243](https://github.com/PostHog/duckgres/actions/runs/30085493243) |

## Measured Result

All rows below ran on GitHub-hosted `ubuntu-latest` runners and built the
unchanged upstream Dockerfile. Total time includes cache setup and the
measured Docker build.

| Revision | GHA | BoringCache | Saved | GHA export | BoringCache export |
| --- | ---: | ---: | ---: | ---: | ---: |
| [oldest](https://github.com/boringcache/benchmark-duckgres/actions/runs/30086951894) | 341s | 195s | 146s (43%) | 147.0s | 2.1s |
| [middle](https://github.com/boringcache/benchmark-duckgres/actions/runs/30087337296) | 318s | 210s | 108s (34%) | 123.2s | 1.8s |
| [newest](https://github.com/boringcache/benchmark-duckgres/actions/runs/30087850987) | 263s | 204s | 59s (22%) | 76.1s | 1.8s |

Across the three real commits, BoringCache averaged 203 seconds versus 307
seconds for GHA, a 34% reduction. GHA spent an average of 115 seconds exporting
cache after the build; BoringCache averaged 1.9 seconds.

The final [fresh comparison](https://github.com/boringcache/benchmark-duckgres/actions/runs/30088155935)
measured a 387-second GHA cold run versus 260 seconds with BoringCache. The
same-source warm reruns were effectively instant in both lanes: 3 seconds for
GHA and 4 seconds for BoringCache. The value is therefore the recurring
publish path on changed commits, not an exaggerated same-commit warm claim.

## Scenarios

- `cold`
- `warm1`

Fresh lane runs a no-prior-cache cold build plus one warm rerun on the same pinned source tree. Rolling lane records the upstream commit build as-is after each upstream sync against the prior rolling cache and skips `warm1`.

The two-entry matrix compares GitHub Actions cache with BoringCache managed
BuildKit. It does not call BoringCache inside Dockerfile `RUN` steps, and
upstream Dockerfile cache mounts stay native to BuildKit. Docker tool-cache
lanes are intentionally absent until Duckgres has a static supported adapter
for its in-Docker Go build cache shape.

## Output

Each workflow uploads machine-readable JSON and Markdown summaries. Those artifacts are intended to be ingested by the central `boringcache/benchmarks` publisher later.

## Token Model

This repo uses split BoringCache tokens as the standard CI shape:

- `BORINGCACHE_RESTORE_TOKEN` for read-only restore and proxy access
- `BORINGCACHE_SAVE_TOKEN` for trusted write paths
