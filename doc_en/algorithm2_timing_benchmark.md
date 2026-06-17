# Algorithm 2 Timing Benchmark — DoubleIntegrator 2D

Timing benchmark for Algorithm 2 (competitive ε-approximate simulation) on the DoubleIntegrator 2D system.

Builds fine and coarse IMDPs, runs the epsilon binary search, and reports detailed wall-clock timing.

IMDPs are cached to disk after the first build. Subsequent runs load the cache automatically — delete the `.pkl` file or use `--rebuild` to rebuild.

## Usage

```bash
# Fastest: 49-state coarse vs 441-state fine
python time_algorithm2.py --coarse_resolution coarse --fine_resolution fine

# Medium: 196-state coarse vs 1764-state fine
python time_algorithm2.py --coarse_resolution medium --fine_resolution fine_x2

# Rebuild from scratch (ignore cache)
python time_algorithm2.py --rebuild
```

> **Note:** Run directly inside the conda environment, not via `conda run`.

## Resolution Options

DoubleIntegrator 2D system supported resolutions (3 actions):

| Value | Grid | States |
|-------|------|--------|
| `coarse` | 7×7 | 49 |
| `medium` | 14×14 | 196 |
| `fine` | 21×21 | 441 |
| `medium_x2` | 28×28 | 784 |
| `fine_x2` | 42×42 | 1,764 |

## Command-Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--fine_resolution` | `fine` | Resolution for fine IMDP |
| `--coarse_resolution` | `coarse` | Resolution for coarse IMDP |
| `--eps_tol` | `1e-3` | Binary search tolerance |
| `--n_jobs` | `-1` | Parallel threads (-1 = all CPUs, 1 = sequential) |
| `--seed` | `42` | Random seed |
| `--rebuild` | — | Force rebuild IMDPs (ignore disk cache) |

## Output Example

```
=================================================================
Algorithm 2 Timing Benchmark — DoubleIntegrator 2D
  Coarse resolution: coarse
  Fine resolution:   fine
  Epsilon tolerance: 0.001
  Parallel threads:  -1
=================================================================

--- Phase 1: Building IMDPs ---
[Coarse] Creating model...
[Coarse] Model done (0.6s)
[Coarse] Partition: 49 states (2.9s)
[Coarse] Computing forward reachable sets...
[Coarse] Forward reachability done (0.3s)
[Coarse] Computing probability intervals (JAX may compile on first call)...
[Coarse] Probability intervals done (1.9s)
[Coarse] IMDP complete: 49 states, 6.2s total

[Fine] Creating model...
...

Phase 1 total: 15.3s (coarse=6.2s, fine=9.1s)
  Coarse: 49 states
  Fine:   441 states

--- Phase 2: Building f2c mapping ---
Phase 2: 0.1s  (441 mapped, labels consistent: True)

--- Phase 3: Epsilon Search (Algorithm 2) ---
  Coarse: 49 states, Fine: 441 states
  Search tolerance: 0.001
  Note: epsilon=1.0 is trivial (no LPs), epsilon=0.0 is the real work.

...

=================================================================
TIMING SUMMARY
=================================================================
  Phase 1+2 (IMDPs + f2c map):  built/cached
  Phase 3 (Epsilon search):        xxx.x sec
  ------------------------------------------
  Total wall time:                 xxx.x sec

  Epsilon minimum:  x.xxxxxx
  |R_final|:        xxx
  Binary search:    x evaluations
=================================================================
```

## Cache

IMDPs are cached under `.cache_imdps/` after the first build. Subsequent runs skip Phases 1–2 and load directly from cache. Delete the cache file or use `--rebuild` to force a fresh build.
