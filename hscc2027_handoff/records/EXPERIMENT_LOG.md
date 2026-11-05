# Local experiment log and results (2026-11-05)

## Scope and provenance

Weijie ran the revised HSCC 2027 implementation locally before handing it to Ouldouz. The archived outputs are under [../local_results](../local_results/README.md): 27 directories containing original `result.json`, `history.json`, `relation.csv`, optional `pair_errors.csv`, and one diagnostic file. [snapshot_index.csv](../local_results/snapshot_index.csv) indexes every run, [reproduce_commands.csv](../local_results/reproduce_commands.csv) gives one equivalent command per run, and [file_manifest.json](../local_results/file_manifest.json) records SHA-256 hashes. The files are copied verbatim.

The principal baseline code was commit `8dc41cac8d2f7889e65253b124b10c9f26da3b52`; live progress and bounded bisection LP caching were added in `36b4dd77fad58e3e3904526a6c7f2acb83197919`. Local Python was 3.13.14 with NumPy 2.5.0, SciPy 1.18.0 and JAX 0.10.2. Solver: `scipy.optimize.linprog(method="highs")`. The runner fixes seed 42. Historical result files retain their original commit and `git_dirty` fields; some were created before commit, and later runs reported `git_dirty=true` because an unrelated untracked exploration script was present. The tracked algorithm files matched the named commit. These are validation data, **not final server Table 1 numbers**.

The original console streams from these historical runs were not saved. Their probe and elimination histories are preserved in `history.json`; future runs through the handoff entry point save a flushed `run.log` for each task.

Each pair below uses M1 as the smaller abstract partition and M2 as the larger concrete partition. Each model also has one absorbing state. Algorithm 1 searches with tolerance `1e-3`. `wall_time_s_total` measures relation/LP work and excludes benchmark model construction.

## Algorithm 1 bisection and Algorithm 2 fixed-relation checks

The Algorithm 2 input is the relation returned at Algorithm 1's feasible upper bound for the same case and semantics.

| M1/M2 partition states | Semantics | Algorithm 1 infeasible/feasible bracket | Relation pairs | LP calls | Solver seconds | Algorithm 2 exact error for that relation |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 5/10 | cooperative | [0.4990234375, 0.5] | 21 | 5,733 | 7.2 | 0.4997999966144562 |
| 5/10 | competitive | [0, 0.0009765625] | 35 | 7,809 | 9.4 | 0.00009999999747378752 |
| 5/15 | cooperative | [0.951171875, 0.9521484375] | 40 | 11,181 | 15.1 | 0.9521000009408453 |
| 5/15 | competitive | [0, 0.0009765625] | 52 | 39,029 | 49.3 | 0.00009999999747378752 |
| 7/21 | cooperative | [0.5078125, 0.5087890625] | 71 | 56,454 | 81.3 | 0.5083999931812286 |
| 7/21 | competitive | [0, 0.0009765625] | 76 | 209,544 | 360.5 | 0.0002000039821723476 |

All six Algorithm 2 values lie inside their matching bisection brackets. In every case, the `pair_errors.csv` row count equals the recorded relation size. The original output directories are named `validation_1d_<M1>_<M2>_<semantics>_bisect001` and `..._algorithm2`.

The older draft Table 1 lists competitive `0.000977` for these three examples, numerically the same rounded bisection upper bound. Its relation sizes are 10, 15 and 21, whereas the revised results have 35, 52 and 76 pairs. The prior implementation used the earlier model direction, quantifiers and relation initialization; numerical coincidence is not validation of the old table row. Runtime and LP counts across the two implementations are not directly comparable.

## Algorithm 3 joint search

| M1/M2 | Semantics | Exact global minimum error | Greatest relation size | Cross-check |
| --- | --- | ---: | ---: | --- |
| 5/10 | cooperative | 0.4997999966144562 | 21 | Inside Algorithm 1 bracket; same relation as its feasible upper bound |
| 5/10 | competitive | 0.00009999999747378752 | 35 | Inside bracket; same relation |
| 5/15 | cooperative | 0.9520000029733637 | 34 | Inside bracket; Algorithm 1 at this exact threshold returns exactly the same relation |
| 5/15 | competitive | 0.00009999999747378752 | 52 | Inside bracket; same relation as the feasible upper bound |

For 5/15 cooperative, Algorithm 2 evaluates the 40-pair bisection-upper relation at 0.9521000009408453. Algorithm 3 finds a different 34-pair relation at 0.9520000029733637. This is expected: Algorithm 2 keeps the supplied relation fixed, whereas Algorithm 3 searches across relations. Algorithm 3 has not yet been run locally on 7/21 or larger cases.

## Additional diagnostic and progress runs

At fixed epsilon 0.1 on 5/10, cooperative Algorithm 1 removes the initial pair and ends with one pair after 491 LP calls; competitive retains the initial pair and ends with 35 pairs after 646 LP calls. The cooperative initial-pair diagnostic identifies M1 action index 2; the three M2 candidate actions have worst errors approximately 0.9998, 0.9998 and 0.4998. Independently, the M1 action has a vertex with about 0.9998 mass on the goal label, while M2's best candidate can put at most 0.5 mass there, forcing at least 0.4998 mass outside any label-preserving relation.

The `validation_progress_smoke_*` directories record later logging checks. `validation_1d_5_10_*_bisect01` used a coarser tolerance, and `validation_1d_5_15_cooperative_exact_threshold` checked the Algorithm 3 threshold. These remain in the snapshot archive so the history is complete.

## Bounded-cache comparison

| Competitive case | Uncached LP calls | Cached LP calls | Uncached solver seconds | Cached solver seconds |
| --- | ---: | ---: | ---: | ---: |
| 5/10 | 7,809 | 1,519 | 9.39 | 1.88 |
| 7/21 | 209,544 | 38,574 | 360.45 | 56.55 |

For each case, cached and uncached outputs have identical brackets and relation CSVs. The cached output directories are `validation_cache_1d_5_10_competitive` and `validation_cache_1d_7_21_competitive`. These are local observations; do not assume the same speedup for other models or hardware.

## What remains

Ouldouz should reproduce small cases from a clean fixed commit, then run the remaining 1D and 2D Table 1 cases under both semantics. For each Algorithm 1 relation, run Algorithm 2; assess Algorithm 3 costs case by case. Record the exact code, environment, machine, concurrency, logs and output files. Weijie should update the paper only after server checks and mark any draft changes with color for Sadegh.
