# Ouldouz's server runbook

## 1. Fix the revision and environment

Execute from the repository root. Keep a clean checkout for paper results. Record the Git commit, node name, usable CPU cores, memory, Python/NumPy/SciPy/JAX versions, process count and complete logs. The manuscript specifies AMD EPYC 7702 **64-core CPUs**, not 64 GPUs.

```bash
git fetch origin hscc2027-algorithm1
git switch hscc2027-algorithm1
git rev-parse HEAD
git status -sb
python hscc2027_handoff/run_experiments.py --suite status
python -m unittest tests.test_hscc2027 -q
```

If using a server work disk, add the **same** `--out-root /scratch/HSCC_2027_runs` to every experiment command. The default is the Git-ignored `hscc2027_handoff/runs/`. Add `--dry-run` to inspect the expanded solver command without executing it.

## 2. Run experiments one at a time

[EXPERIMENT_COMMANDS.md](EXPERIMENT_COMMANDS.md) gives a separate copyable command for every **case × semantics × algorithm** combination. [experiment_commands.csv](experiment_commands.csv) provides the same 60 commands for filtering or a job scheduler. Each command runs exactly one experiment. Start with 1D (5,10), then (5,15) and (7,21), which Weijie checked locally. Proceed to 1D (5,25), (10,20), (7,35), (20,40), (17,51), then the two 2D cases after checking resource usage.

For example, these are **three separate experiments** for cooperative 1D (5,10):

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_5_10 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_5_10 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_5_10 --semantics cooperative --jobs 1
```

`table1` is Algorithm 1 plus bisection at tolerance `1e-3`; `fixed` is Algorithm 2, which reads the **same case and semantics** Algorithm 1 relation; `joint` is Algorithm 3. Run Algorithm 1 before Algorithm 2. Algorithm 3 can run independently, but its cost can be high: it recomputes local errors after each relation-pair deletion. Start with the small cases.

## 3. Optional use of the 64-core node

The per-experiment commands are the primary workflow. To use more cores, launch independent commands in separate terminals or scheduler jobs, each with a distinct output directory. Alternatively, a grouped command can schedule a **small number of independent experiments**:

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_5_10 1D_5_15 --semantics both --jobs 2
```

This is only an optional scheduling shortcut; there is no requirement to run the whole table in one command. Start with two processes, measure total wall time and peak memory, then try four. Do not assume 64 concurrent jobs or 64-fold speedup. The wrapper sets OMP/OpenBLAS/MKL/NumExpr threads to one per process. The revised algorithms do not yet have validated intra-experiment process parallelism. Bisection probes and Algorithm 3 elimination rounds have sequential dependencies; the old thread-pool runner uses earlier definitions.

## 4. Inspect outputs and progress

Each experiment writes `runs/<case>/<semantics>/<stage>/run.log`, `result.json`, `history.json` and `relation.csv`; Algorithm 2 also writes `pair_errors.csv`. For example:

```bash
tail -f hscc2027_handoff/runs/1D_5_10/cooperative/table1/run.log
```

`runs/summary.csv` lists all present results across separate invocations. `runs/batch_manifest.json` records the environment and status of the latest invocation. Probe and iteration milestones are flushed immediately; longer LP batches emit a heartbeat about every 15 seconds.

## 5. Acceptance checks and debugging

1. Verify `result.json` has the intended Git commit, `git_dirty=false`, the correct M1/M2 state counts and semantics, and an initial pair present in `relation.csv`. The relation data-row count must equal `relation_size`. The wrapper checks these fields automatically.
2. Algorithm 1's feasible upper and infeasible lower bounds must be no more than `1e-3` apart. Review `history.json`. Algorithm 2's `epsilon_star` and Algorithm 3's `epsilon_min` should lie in the matching Algorithm 1 bracket. The wrapper cross-checks these when same-commit baseline output is available.
3. A failure should be investigated in the task's `run.log` and `batch_manifest.json`. A missing Algorithm 2 relation means the matching Algorithm 1 task has not completed in the same `--out-root`. Rerunning a command resumes completed clean-checkout work; use `--force` to recompute.
4. If results differ from [Weijie's local archive](local_results/README.md), first check commit, dependency versions, seed 42, model direction and state counts. For a cache concern, run the direct solver with `--no-action-cache` and compare brackets and relation CSVs. A complete vertex-enumeration support error must be reported rather than bypassed with an incomplete vertex set.
5. The older Table 1 is not the revised implementation's correctness standard. [EXPERIMENT_LOG.md](records/EXPERIMENT_LOG.md) gives the local dual-semantics baseline and explains differences.

Weijie should update Table 1 only after server checks. Any manuscript edits should be highlighted in color for Sadegh.
