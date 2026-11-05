# Progress reporting and 64-core CPU usage

## Hardware statement

The manuscript says experiments were performed on cluster nodes equipped with **AMD EPYC 7702 64-core processors**. This describes CPU hardware, not 64 GPUs. It does not state that the earlier implementation used every core, and it does not imply 64-fold speedup.

## Improvements already in the committed baseline

The runner flushes fixed-point iterations, bisection probes, Algorithm 2 checks and Algorithm 3 elimination rounds to stdout. During a long LP batch, the default heartbeat interval is 15 seconds; `--progress-interval` adjusts it. The handoff wrapper sends each task's output to a dedicated `run.log` and gives a batch-level heartbeat.

Algorithm 1 bisection caches an action-pair LP worst error when the relation and fixed vertex side are identical across probes. The LP optimum does not depend on the tested epsilon. The cache holds at most 50,000 entries and is scoped to one bisection run; `--no-action-cache` disables it. Local competitive comparisons had identical brackets and relation CSVs:

| Case | LP calls uncached → cached | Solver seconds uncached → cached |
| --- | ---: | ---: |
| 1D (5,10) | 7,809 → 1,519 | 9.39 → 1.88 |
| 1D (7,21) | 209,544 → 38,574 | 360.45 → 56.55 |

Times are local relation/LP time, excluding model construction. They are measurements for these cases, not a universal speedup claim.

## Safe concurrency today

Each **separate case/semantics/algorithm command** is an independent process. The wrapper defaults to one job. Ouldouz can run separate commands in different terminals or optionally group a few independent jobs with `--jobs 2`, then try 4 after observing CPU and memory. It restricts OMP, OpenBLAS, MKL and NumExpr threads to one per process. The same case's Algorithm 2 depends on Algorithm 1's relation file, so that pair must be ordered.

Within one fixed-point iteration, state-pair checks read a frozen relation and are mathematically independent. Algorithm 2 local errors have the same property. These are candidates for a future **process-based** implementation and benchmark on the 64-core node. Bisection probes depend on the previous bracket; Algorithm 3 rounds depend on the previous deletion. Those outer steps remain sequential. The old thread-pool runner uses outdated semantics and is not an approved acceleration path for the revised table.

The current handoff does **not** implement intra-experiment CPU process parallelism. If introduced, compare exact error bounds, `relation.csv`, action quantifiers and LP counts with the serial baseline on 1D (5,10), (5,15), and (7,21). Record machine, process count, thread limits, peak memory and wall time. Large 2D cases may be constrained by complete vertex enumeration and memory, so test resource use before scaling concurrency.
